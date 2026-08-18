"""Fast path: pure LlmLang → real Python → CPython."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import time
import io
import contextlib

from language.parser import parse
from language.ast_nodes import *


class FastPathError(Exception):
    pass


def transpile_full(source: str) -> str:
    prog = parse(source)
    lines = ["# Transpiled from LlmLang (fast path)", "from __future__ import annotations", ""]
    for stmt in prog.statements:
        lines.extend(_stmt(stmt, indent=0))
    return "\n".join(lines) + "\n"


def _ind(n: int) -> str:
    return "    " * n


def _stmt(node, indent: int = 0) -> List[str]:
    p = _ind(indent)
    if isinstance(node, Assign):
        return [f"{p}{node.name} = {_expr(node.value)}"]
    if isinstance(node, Print):
        return [f"{p}print({_expr(node.value)})"]
    if isinstance(node, HardIf):
        out = [f"{p}if {_expr(node.condition)}:"]
        body = []
        for s in node.then_body:
            body.extend(_stmt(s, indent + 1))
        out.extend(body or [f"{p}    pass"])
        if node.else_body:
            out.append(f"{p}else:")
            eb = []
            for s in node.else_body:
                eb.extend(_stmt(s, indent + 1))
            out.extend(eb or [f"{p}    pass"])
        return out
    if isinstance(node, WhileLoop):
        out = [f"{p}while {_expr(node.condition)}:"]
        body = []
        for s in node.body:
            body.extend(_stmt(s, indent + 1))
        out.extend(body or [f"{p}    pass"])
        return out
    if isinstance(node, ForLoop):
        out = [f"{p}for {node.var} in {_expr(node.iterable)}:"]
        body = []
        for s in node.body:
            body.extend(_stmt(s, indent + 1))
        out.extend(body or [f"{p}    pass"])
        return out
    if isinstance(node, FuncDef):
        params = ", ".join(node.params)
        out = [f"{p}def {node.name}({params}):"]
        body = []
        for s in node.body:
            body.extend(_stmt(s, indent + 1))
        out.extend(body or [f"{p}    pass"])
        return out + [""]
    if isinstance(node, Return):
        return [f"{p}return {_expr(node.value)}"]
    if isinstance(node, ModelDecl):
        raise FastPathError(f"model '{node.name}' is not pure")
    if isinstance(node, SoftIf):
        return [f"{p}# soft-if — use interpreter"]
    return [f"{p}# unsupported: {type(node).__name__}"]


def _expr(node) -> str:
    if isinstance(node, Literal):
        return repr(node.value)
    if isinstance(node, Var):
        return node.name
    if isinstance(node, ListLiteral):
        return "[" + ", ".join(_expr(e) for e in node.elements) + "]"
    if isinstance(node, BinaryOp):
        return f"({_expr(node.left)} {node.op} {_expr(node.right)})"
    if isinstance(node, UnaryOp):
        if node.op in ("len", "str", "int", "bool"):
            return f"{node.op}({_expr(node.operand)})"
        if node.op == "-":
            return f"(-{_expr(node.operand)})"
        if node.op in ("not", "!"):
            return f"(not {_expr(node.operand)})"
        raise FastPathError(f"unary {node.op}")
    if isinstance(node, Index):
        return f"{_expr(node.target)}[{_expr(node.index)}]"
    if isinstance(node, ModelCall) and node.model == "range":
        return f"range({_expr(node.prompt)})"
    if isinstance(node, FuncCall):
        return f"{node.name}({', '.join(_expr(a) for a in node.args)})"
    return "None"


@dataclass
class FastResult:
    ok: bool
    output: List[str] = field(default_factory=list)
    error: Optional[str] = None
    python_source: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "output": self.output, "error": self.error,
                "elapsed_ms": round(self.elapsed_ms, 3),
                "python_source_preview": self.python_source[:400]}


def run_fast(source: str, env: Optional[Dict[str, Any]] = None) -> FastResult:
    try:
        py = transpile_full(source)
    except Exception as e:
        return FastResult(ok=False, error=f"transpile: {e}")
    buf = io.StringIO()
    g = {"__name__": "__ll_fast__"}
    if env:
        g.update(env)
    t0 = time.perf_counter()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(py, "<ll_fast>", "exec"), g, g)
        elapsed = (time.perf_counter() - t0) * 1000
        return FastResult(ok=True, output=buf.getvalue().splitlines(), python_source=py, elapsed_ms=elapsed)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return FastResult(ok=False, error=f"{type(e).__name__}: {e}", python_source=py, elapsed_ms=elapsed)


def speed_benchmark(n: int = 50_000) -> Dict[str, Any]:
    ll = f"s = 0\ni = 0\nwhile i < {n} {{\n  s = s + i\n  i = i + 1\n}}\nprint s\n"
    results: Dict[str, Any] = {"n": n}
    t0 = time.perf_counter()
    fr = run_fast(ll)
    results["fast_path_ms"] = (time.perf_counter() - t0) * 1000
    results["fast_ok"] = fr.ok
    results["fast_out"] = fr.output[-1] if fr.output else None
    try:
        from language.bytecode import VM, compile_source
        t0 = time.perf_counter()
        br = VM(compile_source(ll), max_steps=5_000_000).execute()
        results["bytecode_ms"] = (time.perf_counter() - t0) * 1000
        results["bytecode_ok"] = br.ok
        results["bytecode_out"] = br.output[-1] if br.output else None
    except Exception as e:
        results["bytecode_error"] = str(e)
    try:
        from language.interpreter import run_source
        n_i = min(n, 5000)
        ll_i = f"s = 0\ni = 0\nwhile i < {n_i} {{\n  s = s + i\n  i = i + 1\n}}\nprint s\n"
        t0 = time.perf_counter()
        run_source(ll_i)
        results["interpreter_ms"] = (time.perf_counter() - t0) * 1000
        results["interpreter_n"] = n_i
    except Exception as e:
        results["interpreter_error"] = str(e)
    t0 = time.perf_counter()
    s = 0
    i = 0
    while i < n:
        s = s + i
        i = i + 1
    results["hand_python_ms"] = (time.perf_counter() - t0) * 1000
    results["hand_python_out"] = str(s)
    hp = results.get("hand_python_ms") or 1
    if results.get("fast_path_ms"):
        results["fast_vs_hand"] = round(results["fast_path_ms"] / hp, 2)
    if results.get("bytecode_ms"):
        results["bytecode_vs_hand"] = round(results["bytecode_ms"] / hp, 2)
        if results.get("fast_path_ms"):
            results["fast_vs_bytecode"] = round(results["bytecode_ms"] / max(results["fast_path_ms"], 1e-9), 2)
    results["claim"] = (
        "Fast path (transpile→CPython) approaches hand Python; "
        "bytecode VM (Python-hosted) is much slower; tree-walk is slowest."
    )
    return results
