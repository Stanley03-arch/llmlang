"""Route pure programs to Go codegen (faster than CPython on tight loops)."""
from __future__ import annotations
from typing import Any, Dict
from language.parser import parse
from language.ast_nodes import ModelDecl, SoftIf, Parallel, TryCatch

def is_pure(source: str) -> bool:
    try:
        prog = parse(source)
    except Exception:
        return False
    for stmt in prog.statements:
        if isinstance(stmt, (ModelDecl, SoftIf, Parallel, TryCatch)):
            return False
    if "model " in source or "conf(" in source or "py(" in source:
        return False
    return True

def run_always_fast(source: str) -> Dict[str, Any]:
    if is_pure(source):
        try:
            from runtime.run_native import run_codegen_build
            r = run_codegen_build(source)
            r["path"] = "go_codegen"
            return r
        except Exception as e:
            from language.fast_path import run_fast
            fr = run_fast(source)
            return {**fr.to_dict(), "path": "python_transpile", "go_error": str(e)}
    from language.interpreter import run_source
    out = run_source(source)
    return {"ok": True, "path": "interpreter", "result": str(out)[:500]}
