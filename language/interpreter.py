"""
LlmLang interpreter.

Executes the AST. Model calls go through the configured LLM backend.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import sys

from .ast import (
    Program, ModelDecl, Assign, Call, Print, If, While, For,
    Binary, Unary, Literal, Name, Conf, Assert, Return,
    FunctionDef, Node,
)
from library.core import CallResult, ModelConfig, conf as conf_fn, LLMBackend, backend as set_backend


class RuntimeError_(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class Interpreter:
    def __init__(self, backend=None):
        self.globals: Dict[str, Any] = {}
        self.models: Dict[str, ModelConfig] = {}
        self.functions: Dict[str, FunctionDef] = {}
        self.backend = backend or LLMBackend(mock=True)
        set_backend(self.backend)

        # builtins
        self.globals["len"] = len
        self.globals["str"] = str
        self.globals["int"] = int
        self.globals["float"] = float
        self.globals["print"] = print

    def run(self, program: Program) -> Any:
        last = None
        for stmt in program.statements:
            last = self.exec(stmt)
        return last

    def exec(self, node: Node) -> Any:
        if isinstance(node, ModelDecl):
            cfg = ModelConfig(
                name=node.name,
                system=str(node.fields.get("system", "You are a helpful assistant.")),
                temperature=float(node.fields.get("temperature", 0.2)),
                mode=str(node.fields.get("mode", "free")),
                tools=list(node.fields.get("tools", [])) if isinstance(node.fields.get("tools"), list) else [],
            )
            self.models[node.name] = cfg
            self.globals[node.name] = cfg  # also bind as callable later
            return cfg

        if isinstance(node, Assign):
            value = self.eval(node.value)
            self.globals[node.name] = value
            return value

        if isinstance(node, Print):
            vals = [self.eval(a) for a in node.args]
            # unwrap CallResult for nicer printing
            out = []
            for v in vals:
                if isinstance(v, CallResult):
                    out.append(v.text)
                else:
                    out.append(v)
            print(*out)
            return None

        if isinstance(node, If):
            cond = self.eval(node.condition)
            if self.truthy(cond):
                return self.exec_block(node.then_body)
            else:
                return self.exec_block(node.else_body)

        if isinstance(node, While):
            last = None
            while self.truthy(self.eval(node.condition)):
                last = self.exec_block(node.body)
            return last

        if isinstance(node, For):
            iterable = self.eval(node.iterable)
            last = None
            for item in iterable:
                self.globals[node.var] = item
                last = self.exec_block(node.body)
            return last

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

        # expression statement
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

        if isinstance(node, Conf):
            val = self.eval(node.expr)
            return conf_fn(val)

        if isinstance(node, Unary):
            val = self.eval(node.operand)
            if node.op == "-":
                return -val
            if node.op == "not":
                return not self.truthy(val)
            raise RuntimeError_(f"Unknown unary op {node.op}")

        if isinstance(node, Binary):
            left = self.eval(node.left)
            # short-circuit
            if node.op == "and":
                return left if not self.truthy(left) else self.eval(node.right)
            if node.op == "or":
                return left if self.truthy(left) else self.eval(node.right)

            right = self.eval(node.right)
            # unwrap CallResult for arithmetic / comparison where sensible
            l = left.text if isinstance(left, CallResult) else left
            r = right.text if isinstance(right, CallResult) else right

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

        # special list constructor
        if name == "__list__":
            return [self.eval(a) for a in node.args]

        # user-defined function
        if name in self.functions:
            fn = self.functions[name]
            if len(node.args) != len(fn.params):
                raise RuntimeError_(f"{name} expects {len(fn.params)} args, got {len(node.args)}")
            # simple local scope via save/restore
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

        # model call
        if name in self.models:
            cfg = self.models[name]
            if not node.args:
                raise RuntimeError_(f"Model {name} requires a prompt argument")
            prompt = self.eval(node.args[0])
            if isinstance(prompt, CallResult):
                prompt = prompt.text
            prompt = str(prompt)
            return self.backend.complete(cfg, prompt)

        # python callable in globals
        if name in self.globals and callable(self.globals[name]):
            args = [self.eval(a) for a in node.args]
            return self.globals[name](*args)

        raise RuntimeError_(f"Unknown callable: {name}")

    def truthy(self, value: Any) -> bool:
        if isinstance(value, CallResult):
            return bool(value.text)
        return bool(value)


def run_source(source: str, backend_name: str = "mock") -> Any:
    from backends import get_backend
    from .parser import parse

    backend = get_backend(backend_name)
    program = parse(source)
    interp = Interpreter(backend=backend)
    return interp.run(program)
