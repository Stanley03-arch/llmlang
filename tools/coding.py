"""Coding tools: generate modules/tests, patch, search, pytest, tree."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import os
import re
import subprocess

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _safe(path: str) -> str:
    return os.path.abspath(os.path.join(PROJECT, path) if not os.path.isabs(path) else path)

def generate_module(path: str, module_doc: str = "", functions: Optional[List[Dict]] = None) -> Dict[str, Any]:
    functions = functions or []
    lines = [f'"""{module_doc}"""\n' if module_doc else ""]
    for fn in functions:
        name = fn.get("name", "func")
        args = fn.get("args", "")
        body = fn.get("body", "pass")
        doc = fn.get("docstring", "")
        lines.append(f"def {name}({args}):")
        if doc:
            lines.append(f'    """{doc}"""')
        for bl in str(body).splitlines() or ["pass"]:
            lines.append(f"    {bl}")
        lines.append("")
    text = "\n".join(lines)
    p = _safe(path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return {"ok": True, "path": path, "bytes": len(text)}

def generate_tests(module_path: str, test_path: str = None, functions: Optional[List[str]] = None) -> Dict[str, Any]:
    test_path = test_path or module_path.replace(".py", "_test.py")
    mod = os.path.splitext(os.path.basename(module_path))[0]
    functions = functions or ["main"]
    lines = ["import unittest", f"import {mod}", "", "class TestMod(unittest.TestCase):"]
    for fn in functions:
        lines.append(f"    def test_{fn}(self):")
        lines.append(f"        self.assertTrue(hasattr({mod}, '{fn}'))")
        lines.append("")
    lines += ['if __name__ == "__main__":', "    unittest.main()", ""]
    text = "\n".join(lines)
    p = _safe(test_path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w") as f:
        f.write(text)
    return {"ok": True, "path": test_path}

def apply_patch(path: str, old: str, new: str) -> Dict[str, Any]:
    p = _safe(path)
    if not os.path.isfile(p):
        return {"ok": False, "error": f"not found: {path}"}
    text = open(p, encoding="utf-8").read()
    if old not in text:
        return {"ok": False, "error": "old text not found"}
    open(p, "w", encoding="utf-8").write(text.replace(old, new, 1))
    return {"ok": True, "path": path, "replacements": 1}

def apply_unified_diff(path: str, diff: str) -> Dict[str, Any]:
    """Minimal unified-diff applier for single-file +/- lines."""
    p = _safe(path)
    if not os.path.isfile(p):
        return {"ok": False, "error": f"not found: {path}"}
    text = open(p, encoding="utf-8").read()
    olds, news = [], []
    for line in diff.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            olds.append(line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            news.append(line[1:])
    if olds:
        chunk = "\n".join(olds)
        if chunk in text:
            text = text.replace(chunk, "\n".join(news), 1)
            open(p, "w", encoding="utf-8").write(text)
            return {"ok": True, "path": path}
    return {"ok": False, "error": "could not apply diff"}

def multi_file_replace(replacements: List[Dict[str, str]]) -> Dict[str, Any]:
    results = []
    for item in replacements:
        r = apply_patch(item["path"], item["old"], item["new"])
        results.append(r)
    return {"ok": all(r.get("ok") for r in results), "results": results}

def run_pytest(path: str = "tests", timeout: int = 60) -> Dict[str, Any]:
    p = _safe(path)
    try:
        proc = subprocess.run(["python", "-m", "pytest", p, "-q"], cwd=PROJECT, capture_output=True, text=True, timeout=timeout)
        return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout[-3000:], "stderr": proc.stderr[-1500:]}
    except FileNotFoundError:
        # fallback: run unittest discovery
        proc = subprocess.run(["python", "-m", "unittest", "discover", "-s", path, "-q"], cwd=PROJECT, capture_output=True, text=True, timeout=timeout)
        return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout[-3000:], "stderr": proc.stderr[-1500:]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def project_tree(path: str = ".", max_depth: int = 3) -> Dict[str, Any]:
    base = _safe(path)
    lines = []
    def walk(cur, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(cur))
        except OSError:
            return
        for name in entries:
            if name in ("__pycache__", ".git", ".pytest_cache", "websites", "sessions", "cache"):
                continue
            full = os.path.join(cur, name)
            rel = os.path.relpath(full, base)
            lines.append(("  " * depth) + name + ("/" if os.path.isdir(full) else ""))
            if os.path.isdir(full):
                walk(full, depth + 1)
    walk(base, 0)
    return {"ok": True, "path": path, "tree": "\n".join(lines[:200])}

def list_symbols(path: str) -> Dict[str, Any]:
    p = _safe(path)
    if not os.path.isfile(p):
        return {"ok": False, "error": "not found"}
    text = open(p, encoding="utf-8", errors="replace").read()
    funcs = re.findall(r"^def\s+(\w+)", text, re.M)
    classes = re.findall(r"^class\s+(\w+)", text, re.M)
    return {"ok": True, "path": path, "functions": funcs, "classes": classes}

def search_and_read(query: str, path: str = ".", max_files: int = 3) -> Dict[str, Any]:
    from tools.programmer import search_code, read_file
    s = search_code(query, path=path)
    matches = s.get("matches") or []
    files = []
    seen = set()
    for m in matches:
        fp = m.split(":", 1)[0] if ":" in m else m
        if fp in seen:
            continue
        seen.add(fp)
        files.append(read_file(fp, max_lines=80))
        if len(files) >= max_files:
            break
    return {"ok": True, "match_count": s.get("count", 0), "files": files}

CODING_TOOLS: Dict[str, Dict[str, Any]] = {
    "generate_module": {"name": "generate_module", "description": "Generate a Python module.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "module_doc": {"type": "string"}, "functions": {}}, "required": ["path"]}, "function": generate_module},
    "generate_tests": {"name": "generate_tests", "description": "Generate unittest file.", "parameters": {"type": "object", "properties": {"module_path": {"type": "string"}, "test_path": {"type": "string"}, "functions": {}}, "required": ["module_path"]}, "function": generate_tests},
    "apply_patch": {"name": "apply_patch", "description": "Replace exact text in a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}, "function": apply_patch},
    "apply_unified_diff": {"name": "apply_unified_diff", "description": "Apply a simple unified diff.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "diff": {"type": "string"}}, "required": ["path", "diff"]}, "function": apply_unified_diff},
    "multi_file_replace": {"name": "multi_file_replace", "description": "Replace text across files.", "parameters": {"type": "object", "properties": {"replacements": {}}, "required": ["replacements"]}, "function": multi_file_replace},
    "run_pytest": {"name": "run_pytest", "description": "Run pytest or unittest.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "timeout": {"type": "integer"}}, "required": []}, "function": run_pytest},
    "project_tree": {"name": "project_tree", "description": "Print a directory tree.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "max_depth": {"type": "integer"}}, "required": []}, "function": project_tree},
    "list_symbols": {"name": "list_symbols", "description": "List functions/classes in a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, "function": list_symbols},
    "search_and_read": {"name": "search_and_read", "description": "Search then read matching files.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "path": {"type": "string"}, "max_files": {"type": "integer"}}, "required": ["query"]}, "function": search_and_read},
}
