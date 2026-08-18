"""Static checks for LlmLang — Weft-style if it checks, architecture is sound."""

from __future__ import annotations
from typing import Any, Dict, List, Set
from dataclasses import dataclass, field

from language.parser import parse, ParseError
from language.ast_nodes import (
    Program, Assign, AssignIndex, ModelDecl, ModelCall, SoftIf, FuncDef, FuncCall,
    Parallel, ForLoop, WhileLoop, Print, Assert, TryCatch, Var, BinaryOp, UnaryOp,
    ListLiteral, DictLiteral, Index, Ternary, Return, Import,
)


@dataclass
class CheckIssue:
    severity: str
    code: str
    message: str
    node: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"severity": self.severity, "code": self.code, "message": self.message, "node": self.node}


@dataclass
class CheckResult:
    ok: bool
    issues: List[CheckIssue] = field(default_factory=list)
    tools_referenced: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "issues": [i.to_dict() for i in self.issues],
            "tools_referenced": self.tools_referenced,
            "models": self.models,
            "errors": sum(1 for i in self.issues if i.severity == "error"),
            "warnings": sum(1 for i in self.issues if i.severity == "warning"),
        }


def _known_tools() -> Set[str]:
    try:
        from tools.builtin import list_tools
        return set(list_tools())
    except Exception:
        return set()


def check_source(source: str) -> CheckResult:
    try:
        prog = parse(source)
    except ParseError as e:
        return CheckResult(ok=False, issues=[CheckIssue("error", "parse", str(e))])
    except Exception as e:
        return CheckResult(ok=False, issues=[CheckIssue("error", "parse", f"{type(e).__name__}: {e}")])
    return check_program(prog)


def check_program(prog: Program) -> CheckResult:
    issues: List[CheckIssue] = []
    tools_ref: Set[str] = set()
    models: Set[str] = set()
    known = _known_tools()
    defined: Set[str] = {"True", "False", "None", "range", "len", "str", "int", "bool", "conf", "py", "fmt", "env"}

    def walk_expr(node, env: Set[str]):
        if node is None:
            return
        t = type(node).__name__
        if isinstance(node, Var):
            if node.name not in env and node.name not in models:
                issues.append(CheckIssue("warning", "undef_var", f"possibly undefined variable '{node.name}'", t))
        elif isinstance(node, BinaryOp):
            walk_expr(node.left, env); walk_expr(node.right, env)
        elif isinstance(node, UnaryOp):
            walk_expr(node.operand, env)
        elif isinstance(node, Index):
            walk_expr(node.target, env); walk_expr(node.index, env)
        elif isinstance(node, ListLiteral):
            for e in node.elements:
                walk_expr(e, env)
        elif isinstance(node, DictLiteral):
            for k, v in node.pairs:
                walk_expr(k, env); walk_expr(v, env)
        elif isinstance(node, ModelCall):
            walk_expr(node.prompt, env)
        elif isinstance(node, FuncCall):
            if node.name not in env and node.name not in models:
                issues.append(CheckIssue("warning", "undef_fn", f"possibly undefined function '{node.name}'", t))
            for a in node.args:
                walk_expr(a, env)
        elif isinstance(node, Ternary):
            walk_expr(node.condition, env); walk_expr(node.then_value, env); walk_expr(node.else_value, env)

    def walk_stmts(stmts, env: Set[str]):
        local = set(env)
        for stmt in stmts:
            t = type(stmt).__name__
            if isinstance(stmt, ModelDecl):
                models.add(stmt.name); local.add(stmt.name)
                for tool in stmt.tools or []:
                    tools_ref.add(tool)
                    if known and tool not in known:
                        issues.append(CheckIssue("error", "unknown_tool", f"model '{stmt.name}' references unknown tool '{tool}'", t))
            elif isinstance(stmt, Assign):
                walk_expr(stmt.value, local); local.add(stmt.name)
            elif isinstance(stmt, AssignIndex):
                walk_expr(stmt.target, local); walk_expr(stmt.value, local)
            elif isinstance(stmt, FuncDef):
                local.add(stmt.name)
                walk_stmts(stmt.body, set(local) | set(stmt.params))
            elif isinstance(stmt, SoftIf):
                if stmt.condition_var not in local and stmt.condition_var not in models:
                    issues.append(CheckIssue("warning", "softif_var", f"soft-if var '{stmt.condition_var}' may be undefined", t))
                walk_stmts(stmt.then_body, local); walk_stmts(stmt.else_body, local)
            elif isinstance(stmt, Parallel):
                if not stmt.statements:
                    issues.append(CheckIssue("error", "empty_parallel", "parallel block has no statements", t))
                walk_stmts(stmt.statements, local)
            elif isinstance(stmt, ForLoop):
                walk_expr(stmt.iterable, local)
                walk_stmts(stmt.body, set(local) | {stmt.var})
            elif isinstance(stmt, WhileLoop):
                walk_expr(stmt.condition, local); walk_stmts(stmt.body, local)
            elif isinstance(stmt, TryCatch):
                walk_stmts(stmt.try_body, local)
                catch_env = set(local)
                if stmt.catch_var:
                    catch_env.add(stmt.catch_var)
                walk_stmts(stmt.catch_body, catch_env)
            elif isinstance(stmt, Print):
                walk_expr(stmt.value, local)
            elif isinstance(stmt, Assert):
                walk_expr(stmt.condition, local)
            elif isinstance(stmt, Return):
                walk_expr(stmt.value, local)
        return local

    walk_stmts(prog.statements, defined)
    errors = [i for i in issues if i.severity == "error"]
    return CheckResult(ok=len(errors) == 0, issues=issues, tools_referenced=sorted(tools_ref), models=sorted(models))


def check_or_raise(source: str) -> CheckResult:
    r = check_source(source)
    if not r.ok:
        msgs = "; ".join(f"[{i.code}] {i.message}" for i in r.issues if i.severity == "error")
        raise ValueError(f"LlmLang static check failed: {msgs}")
    return r
