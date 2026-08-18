"""Lightweight codebase RAG: chunk files, keyword score, return snippets."""

from __future__ import annotations
from typing import Any, Dict, List
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _iter_files(path: str, glob_ext: str = ".py") -> List[str]:
    base = path if os.path.isabs(path) else os.path.join(ROOT, path)
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git", ".pytest_cache", "websites", "sessions")]
        for fn in filenames:
            if fn.endswith(glob_ext) or (glob_ext == "*" and not fn.startswith(".")):
                out.append(os.path.join(dirpath, fn))
    return out

def _chunk_file(path: str, chunk_lines: int = 40) -> List[Dict[str, Any]]:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []
    chunks = []
    for i in range(0, len(lines), chunk_lines):
        block = lines[i : i + chunk_lines]
        text = "".join(block)
        rel = os.path.relpath(path, ROOT)
        chunks.append({"path": rel, "start_line": i + 1, "end_line": i + len(block), "text": text})
    return chunks

def codebase_rag(query: str, path: str = ".", top_k: int = 5, chunk_lines: int = 40, glob_ext: str = ".py") -> Dict[str, Any]:
    terms = [t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query) if len(t) > 1] or [query.lower()]
    scored = []
    for fp in _iter_files(path, glob_ext=glob_ext):
        for ch in _chunk_file(fp, chunk_lines=chunk_lines):
            blob = ch["text"].lower()
            score = sum(blob.count(t) for t in terms) + sum(2 for t in terms if t in ch["path"].lower())
            if score > 0:
                scored.append((score, ch))
    scored.sort(key=lambda x: -x[0])
    hits = [{"score": s, "path": c["path"], "start_line": c["start_line"], "end_line": c["end_line"], "preview": c["text"][:500]} for s, c in scored[:top_k]]
    return {"ok": True, "query": query, "count": len(hits), "hits": hits, "terms": terms}

RAG_TOOLS = {
    "codebase_rag": {
        "name": "codebase_rag",
        "description": "Retrieve relevant code chunks for a query (keyword RAG).",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "path": {"type": "string"}, "top_k": {"type": "integer"}, "chunk_lines": {"type": "integer"}, "glob_ext": {"type": "string"}}, "required": ["query"]},
        "function": codebase_rag,
    },
}
