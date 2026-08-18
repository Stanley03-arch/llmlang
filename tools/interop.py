"""Python interop: evaluate Python, call callables, import modules."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import importlib
import json
import math
import os
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

def py_eval(code: str, mode: str = "eval") -> Dict[str, Any]:
    safe_builtins = {
        "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
        "range": range, "list": list, "dict": dict, "str": str, "int": int,
        "float": float, "bool": bool, "round": round, "sorted": sorted,
        "enumerate": enumerate, "zip": zip, "print": print, "isinstance": isinstance,
        "True": True, "False": False, "None": None,
    }
    env = {"__builtins__": safe_builtins, "math": math, "json": json}
    try:
        if mode == "exec":
            exec(code, env, env)
            out = {k: v for k, v in env.items() if not k.startswith("_") and k not in ("math", "json")}
            serializable = {}
            for k, v in out.items():
                try:
                    json.dumps(v)
                    serializable[k] = v
                except TypeError:
                    serializable[k] = repr(v)
            return {"ok": True, "mode": "exec", "locals": serializable}
        result = eval(code, env, env)
        try:
            json.dumps(result)
            val = result
        except TypeError:
            val = repr(result)
        return {"ok": True, "mode": "eval", "result": val}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}

def py_call(module: str, func: str, args: Optional[List[Any]] = None, kwargs: Optional[Dict] = None) -> Dict[str, Any]:
    args = args or []
    kwargs = kwargs or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = [args]
    if isinstance(kwargs, str):
        kwargs = json.loads(kwargs)
    try:
        mod = importlib.import_module(module)
        fn = getattr(mod, func)
        result = fn(*args, **kwargs)
        try:
            json.dumps(result)
            val = result
        except TypeError:
            val = repr(result)
        return {"ok": True, "module": module, "func": func, "result": val}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}

def py_import(module: str, names: Optional[List[str]] = None) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(module)
        if names:
            attrs = {n: repr(getattr(mod, n)) for n in names}
            return {"ok": True, "module": module, "attrs": attrs}
        public = [n for n in dir(mod) if not n.startswith("_")]
        return {"ok": True, "module": module, "public": public[:80], "count": len(public)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}

INTEROP_TOOLS: Dict[str, Dict[str, Any]] = {
    "py_eval": {"name": "py_eval", "description": "Evaluate Python expression or exec code.",
        "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "mode": {"type": "string"}}, "required": ["code"]}, "function": py_eval},
    "py_call": {"name": "py_call", "description": "Call module.func(*args, **kwargs).",
        "parameters": {"type": "object", "properties": {"module": {"type": "string"}, "func": {"type": "string"}, "args": {}, "kwargs": {}}, "required": ["module", "func"]}, "function": py_call},
    "py_import": {"name": "py_import", "description": "Import a Python module and list attributes.",
        "parameters": {"type": "object", "properties": {"module": {"type": "string"}, "names": {"type": "array", "items": {"type": "string"}}}, "required": ["module"]}, "function": py_import},
}
