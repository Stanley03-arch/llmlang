"""
LlmLang interpreter v0.2.

Executes the AST. Model calls go through the configured LLM backend.
Tools are registered and callable like functions.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from .ast import (
    Program, ModelDecl, Assign, IndexAssign, Call, Print, If, While, For,
    TryCatch, Parallel, Binary, Unary, Literal, Name, Index, Conf, Assert,
    Return, FunctionDef, Import, Ternary, Node,
)
from library.core import CallResult, ModelConfig, conf as conf_fn, LLMBackend, backend as set_backend
from tools.registry import call_tool, list_tools, ToolResult, TOOLS


class RuntimeError_(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


def _fmt(template: str, *args) -> str:
    try:
        return str(template).format(*args)
    except Exception:
        # fallback: simple {} replacement left-to-right
        out = str(template)
        for a in args:
            out = out.replace("{}", str(a), 1)
        return out


def _range(*args):
    return list(range(*args))


def _type_name(x):
    if isinstance(x, CallResult):
        return "CallResult"
    if isinstance(x, ToolResult):
        return "ToolResult"
    if isinstance(x, bool):
        return "bool"
    if isinstance(x, int):
        return "int"
    if isinstance(x, float):
        return "float"
    if isinstance(x, str):
        return "str"
    if isinstance(x, list):
        return "list"
    if isinstance(x, dict):
        return "dict"
    return type(x).__name__


class Interpreter:
    def __init__(self, backend=None, base_dir: str = None):
        self.globals: Dict[str, Any] = {}
        self.models: Dict[str, ModelConfig] = {}
        self.functions: Dict[str, FunctionDef] = {}
        self.backend = backend or LLMBackend(mock=True)
        self.base_dir = base_dir or os.getcwd()
        set_backend(self.backend)

        # builtins
        self.globals["len"] = len
        self.globals["str"] = str
        self.globals["int"] = int
        self.globals["float"] = float
        self.globals["bool"] = bool
        self.globals["print"] = print
        self.globals["fmt"] = _fmt
        self.globals["range"] = _range
        self.globals["type"] = _type_name
        self.globals["keys"] = lambda d: list(d.keys()) if isinstance(d, dict) else []
        self.globals["values"] = lambda d: list(d.values()) if isinstance(d, dict) else []
        self.globals["env"] = lambda name, default="": os.environ.get(str(name), str(default))
        self.globals["tools"] = list_tools

        # register tools as callables that return ToolResult
        for name in TOOLS:
            self.globals[name] = self._make_tool_callable(name)

    def _make_tool_callable(self, name: str):
        def wrapper(*args):
            # unwrap CallResult args
            clean = []
            for a in args:
                if isinstance(a, CallResult):
                    clean.append(a.text)
                elif isinstance(a, ToolResult):
                    clean.append(a.data if a.ok else a.error)
                else:
                    clean.append(a)
            return call_tool(name, *clean)
        wrapper.__name__ = name
        return wrapper

    def run(self, program: Program) -> Any:
        last = None
        for stmt in program.statements:
            last = self.exec(stmt)
        return last

    def exec(self, node: Node) -> Any:
        if isinstance(node, ModelDecl):
            tools_field = node.fields.get("tools", [])
            if not isinstance(tools_field, list):
                tools_field = []
            cfg = ModelConfig(
                name=node.name,
                system=str(node.fields.get("system", "You are a helpful assistant.")),
                temperature=float(node.fields.get("temperature", 0.2)),
                mode=str(node.fields.get("mode", "free")),
                tools=[str(t) for t in tools_field],
                max_tokens=int(node.fields.get("max_tokens", 1024)) if not isinstance(node.fields.get("max_tokens"), Node) else 1024,
            )
            self.models[node.name] = cfg
            self.globals[node.name] = cfg
            return cfg

        if isinstance(node, Assign):
            value = self.eval(node.value)
            self.globals[node.name] = value
            return value

        if isinstance(node, IndexAssign):
            target = self.eval(node.target)
            index = self.eval(node.index)
            value = self.eval(node.value)
            if isinstance(target, list):
                target[int(index)] = value
            elif isinstance(target, dict):
                target[index] = value
            else:
                raise RuntimeError_(f"Cannot index-assign into {type(target).__name__}")
            return value

        if isinstance(node, Print):
            vals = [self.eval(a) for a in node.args]
            out = []
            for v in vals:
                if isinstance(v, CallResult):
                    out.append(v.text)
                elif isinstance(v, ToolResult):
                    out.append(str(v))
                else:
                    out.append(v)
            print(*out)
            return None

        if isinstance(node, If):
            cond = self.eval(node.condition)
            if self.truthy(cond):
                return self.exec_block(node.then_body)
            return self.exec_block(node.else_body)

        if isinstance(node, While):
            last = None
            n = 0
            while self.truthy(self.eval(node.condition)):
                last = self.exec_block(node.body)
                n += 1
                if n > 100000:
                    raise RuntimeError_("while loop exceeded 100000 iterations")
            return last

        if isinstance(node, For):
            iterable = self.eval(node.iterable)
            last = None
            for item in iterable:
                self.globals[node.var] = item
                last = self.exec_block(node.body)
            return last

        if isinstance(node, TryCatch):
            try:
                return self.exec_block(node.try_body)
            except Exception as e:
                if node.catch_var:
                    self.globals[node.catch_var] = str(e)
                return self.exec_block(node.catch_body)

        if isinstance(node, Parallel):
            # Run independent assignments / calls concurrently when possible.
            # Simple strategy: evaluate expression-statements & assigns in a thread pool.
            results = []
            call_nodes = []
            other = []
            for s in node.body:
                if isinstance(s, Assign) and isinstance(s.value, Call):
                    call_nodes.append(s)
                else:
                    other.append(s)

            # sequential non-calls first (defs etc.)
            for s in other:
                results.append(self.exec(s))

            if call_nodes:
                def run_one(assign: Assign):
                    val = self.eval(assign.value)
                    return assign.name, val

                with ThreadPoolExecutor(max_workers=min(8, len(call_nodes))) as pool:
                    futs = [pool.submit(run_one, a) for a in call_nodes]
                    for fut in as_completed(futs):
                        name, val = fut.result()
                        self.globals[name] = val
                        results.append(val)
            return results[-1] if results else None

        if isinstance(node, Import):
            path = node.path
            if not os.path.isabs(path):
                path = os.path.join(self.base_dir, path)
            if not os.path.isfile(path):
                raise RuntimeError_(f"import not found: {node.path}")
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
            from .parser import parse
            prog = parse(src)
            return self.run(prog)

        if isinstance(node, FunctionDef):
            self.functions[node.name] = node
            self.globals[node.name] = node
            return node

        if isinstance(node, Return):
            value = self.eval(node.value) if node.value is not None else None
            raise ReturnSignal(value)

        if isinstance(node, Assert):
            cond = self.eval(node.condition)
            if not self.truthy(cond):
                msg = self.eval(node.message) if node.message else "assertion failed"
                raise RuntimeError_(str(msg))
            return None

        return self.eval(node)

    def exec_block(self, stmts: List[Node]) -> Any:
        last = None
        for s in stmts:
            last = self.exec(s)
        return last

    def eval(self, node: Node) -> Any:
        if node is None:
            return None
        if isinstance(node, Literal):
            return node.value
        if isinstance(node, Name):
            if node.id in self.globals:
                return self.globals[node.id]
            if node.id in self.models:
                return self.models[node.id]
            raise RuntimeError_(f"Undefined name: {node.id}")

        if isinstance(node, Index):
            target = self.eval(node.target)
            index = self.eval(node.index)
            try:
                if isinstance(target, (list, str)):
                    return target[int(index)]
                if isinstance(target, dict):
                    return target[index]
                if isinstance(target, CallResult):
                    return target.text[int(index)]
                raise RuntimeError_(f"Cannot index {type(target).__name__}")
            except (IndexError, KeyError, TypeError) as e:
                raise RuntimeError_(f"Index error: {e}")

        if isinstance(node, Conf):
            return conf_fn(self.eval(node.expr))

        if isinstance(node, Ternary):
            if self.truthy(self.eval(node.condition)):
                return self.eval(node.then_expr)
            return self.eval(node.else_expr)

        if isinstance(node, Unary):
            val = self.eval(node.operand)
            if node.op == "-":
                return -val
            if node.op == "not":
                return not self.truthy(val)
            raise RuntimeError_(f"Unknown unary op {node.op}")

        if isinstance(node, Binary):
            left = self.eval(node.left)
            if node.op == "and":
                return left if not self.truthy(left) else self.eval(node.right)
            if node.op == "or":
                return left if self.truthy(left) else self.eval(node.right)

            right = self.eval(node.right)
            l = left.text if isinstance(left, CallResult) else (left.data if isinstance(left, ToolResult) and left.ok else left)
            r = right.text if isinstance(right, CallResult) else (right.data if isinstance(right, ToolResult) and right.ok else right)

            ops = {
                "+": lambda a, b: a + b,
                "-": lambda a, b: a - b,
                "*": lambda a, b: a * b,
                "/": lambda a, b: a / b,
                "%": lambda a, b: a % b,
                "==": lambda a, b: a == b,
                "!=": lambda a, b: a != b,
                "<": lambda a, b: a < b,
                ">": lambda a, b: a > b,
                "<=": lambda a, b: a <= b,
                ">=": lambda a, b: a >= b,
            }
            if node.op not in ops:
                raise RuntimeError_(f"Unknown operator {node.op}")
            try:
                return ops[node.op](l, r)
            except Exception as e:
                raise RuntimeError_(f"Binary op {node.op} failed: {e}")

        if isinstance(node, Call):
            return self.call(node)

        raise RuntimeError_(f"Cannot evaluate node type {type(node).__name__}")

    def call(self, node: Call) -> Any:
        name = node.callee

        if name == "__list__":
            return [self.eval(a) for a in node.args]

        if name == "__dict__":
            args = [self.eval(a) for a in node.args]
            d = {}
            for i in range(0, len(args), 2):
                if i + 1 < len(args):
                    d[args[i]] = args[i + 1]
            return d

        if name in self.functions:
            fn = self.functions[name]
            if len(node.args) != len(fn.params):
                raise RuntimeError_(f"{name} expects {len(fn.params)} args, got {len(node.args)}")
            saved = {p: self.globals.get(p) for p in fn.params}
            for p, a in zip(fn.params, node.args):
                self.globals[p] = self.eval(a)
            try:
                self.exec_block(fn.body)
                result = None
            except ReturnSignal as rs:
                result = rs.value
            finally:
                for p, old in saved.items():
                    if old is None and p in self.globals:
                        del self.globals[p]
                    elif old is not None:
                        self.globals[p] = old
            return result

        if name in self.models:
            cfg = self.models[name]
            if not node.args:
                raise RuntimeError_(f"Model {name} requires a prompt argument")
            prompt = self.eval(node.args[0])
            if isinstance(prompt, CallResult):
                prompt = prompt.text
            elif isinstance(prompt, ToolResult):
                prompt = str(prompt.data if prompt.ok else prompt.error)
            prompt = str(prompt)
            return self.backend.complete(cfg, prompt)

        if name in TOOLS:
            args = [self.eval(a) for a in node.args]
            clean = []
            for a in args:
                if isinstance(a, CallResult):
                    clean.append(a.text)
                elif isinstance(a, ToolResult):
                    clean.append(a.data if a.ok else a.error)
                else:
                    clean.append(a)
            return call_tool(name, *clean)

        if name in self.globals and callable(self.globals[name]):
            args = [self.eval(a) for a in node.args]
            return self.globals[name](*args)

        raise RuntimeError_(f"Unknown callable: {name}")

    def truthy(self, value: Any) -> bool:
        if isinstance(value, CallResult):
            return bool(value.text)
        if isinstance(value, ToolResult):
            return value.ok
        return bool(value)


def run_source(source: str, backend_name: str = "mock", base_dir: str = None) -> Any:
    from backends import get_backend
    from .parser import parse

    backend = get_backend(backend_name)
    program = parse(source)
    interp = Interpreter(backend=backend, base_dir=base_dir or os.getcwd())
    return interp.run(program)
