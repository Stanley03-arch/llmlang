"""Transpile a subset of LlmLang to readable Python."""

from __future__ import annotations
from .parser import parse
from .ast_nodes import *


def transpile(source: str) -> str:
    prog = parse(source)
    lines = ["# Transpiled from LlmLang", "from __future__ import annotations", ""]
    for stmt in prog.statements:
        lines.extend(_stmt(stmt))
    return "\n".join(lines) + "\n"


def _stmt(node) -> list:
    if isinstance(node, Assign):
        return [f"{node.name} = {_expr(node.value)}"]
    if isinstance(node, AssignIndex):
        return [f"{_expr(node.target)} = {_expr(node.value)}"]
    if isinstance(node, Print):
        return [f"print({_expr(node.value)})"]
    if isinstance(node, Assert):
        msg = repr(node.message or "assertion failed")
        return [f"assert {_expr(node.condition)}, {msg}"]
    if isinstance(node, FuncDef):
        params = ", ".join(node.params)
        body = []
        for s in node.body:
            for line in _stmt(s):
                body.append("    " + line)
        if not body:
            body = ["    pass"]
        return [f"def {node.name}({params}):"] + body + [""]
    if isinstance(node, ForLoop):
        out = [f"for {node.var} in {_expr(node.iterable)}:"]
        for s in node.body:
            for line in _stmt(s):
                out.append("    " + line)
        return out
    if isinstance(node, Return):
        return [f"return {_expr(node.value)}"]
    if isinstance(node, ModelDecl):
        return [f"# model {node.name} (runtime LLM)"]
    if isinstance(node, Import):
        return [f"# import {node.path!r}"]
    return [f"# unsupported: {type(node).__name__}"]


def _expr(node) -> str:
    if isinstance(node, Literal):
        return repr(node.value)
    if isinstance(node, Var):
        return node.name
    if isinstance(node, ListLiteral):
        return "[" + ", ".join(_expr(e) for e in node.elements) + "]"
    if isinstance(node, DictLiteral):
        pairs = ", ".join(f"{_expr(k)}: {_expr(v)}" for k, v in node.pairs)
        return "{" + pairs + "}"
    if isinstance(node, BinaryOp):
        return f"({_expr(node.left)} {node.op} {_expr(node.right)})"
    if isinstance(node, UnaryOp):
        if node.op in ("len", "str", "int", "bool"):
            return f"{node.op}({_expr(node.operand)})"
        if node.op == "conf":
            return f"confidence({_expr(node.operand)})"
        if node.op == "-":
            return f"-{_expr(node.operand)}"
        return f"{node.op}({_expr(node.operand)})"
    if isinstance(node, Index):
        return f"{_expr(node.target)}[{_expr(node.index)}]"
    if isinstance(node, ModelCall) and node.model == "range":
        return f"range({_expr(node.prompt)})"
    if isinstance(node, ModelCall):
        return f'{node.model}({_expr(node.prompt)})  # LLM call'
    if isinstance(node, FuncCall):
        args = ", ".join(_expr(a) for a in node.args)
        return f"{node.name}({args})"
    return "None"
