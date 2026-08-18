"""Tools that map to real programmer work."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT = ROOT

def _safe_path(path: str) -> str:
    if not path:
        raise ValueError("empty path")
    abs_path = os.path.abspath(os.path.join(PROJECT, path) if not os.path.isabs(path) else path)
    if not abs_path.startswith(os.path.dirname(ROOT)) and not abs_path.startswith(ROOT):
        # allow project tree
        pass
    return abs_path

def read_file(path: str, max_lines: int = 200) -> Dict[str, Any]:
    p = _safe_path(path)
    if not os.path.isfile(p):
        return {"error": f"not a file: {path}"}
    with open(p, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    total = len(lines)
    content = "".join(lines[:max_lines])
    return {"path": path, "lines": total, "truncated": total > max_lines, "content": content}

def write_file(path: str, content: str) -> Dict[str, Any]:
    p = _safe_path(path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return {"path": path, "bytes": len(content.encode("utf-8")), "ok": True}

def list_dir(path: str = ".", max_entries: int = 100) -> Dict[str, Any]:
    p = _safe_path(path)
    if not os.path.isdir(p):
        return {"error": f"not a directory: {path}"}
    entries = sorted(os.listdir(p))[:max_entries]
    out = []
    for name in entries:
        full = os.path.join(p, name)
        out.append({"name": name, "type": "dir" if os.path.isdir(full) else "file",
                    "size": os.path.getsize(full) if os.path.isfile(full) else None})
    return {"path": path, "entries": out}

def search_code(query: str, path: str = ".", glob: str = "*.py") -> Dict[str, Any]:
    p = _safe_path(path)
    try:
        cmd = ["grep", "-R", "-n", "-I", "--include", glob, query, p]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()][:50]
        return {"query": query, "matches": lines, "count": len(lines)}
    except Exception as e:
        return {"query": query, "error": str(e), "matches": []}

def run_command(command: str, timeout: int = 30) -> Dict[str, Any]:
    banned = ["rm -rf /", "mkfs", "dd if=", ":(){", "shutdown", "reboot"]
    low = command.lower()
    for b in banned:
        if b in low:
            return {"error": f"command blocked: contains '{b}'"}
    try:
        proc = subprocess.run(command, shell=True, cwd=PROJECT, capture_output=True, text=True, timeout=timeout)
        return {"command": command, "exit_code": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-2000:]}
    except subprocess.TimeoutExpired:
        return {"command": command, "error": "timeout"}
    except Exception as e:
        return {"command": command, "error": str(e)}

def run_python(code: str, timeout: int = 15) -> Dict[str, Any]:
    try:
        proc = subprocess.run(["python", "-c", code], cwd=PROJECT, capture_output=True, text=True, timeout=timeout)
        return {"exit_code": proc.returncode, "stdout": proc.stdout[-3000:], "stderr": proc.stderr[-1500:]}
    except Exception as e:
        return {"error": str(e)}

def diff_stats(path: str = ".") -> Dict[str, Any]:
    p = _safe_path(path)
    py_files = 0
    total_lines = 0
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
        for f in files:
            if f.endswith(".py"):
                py_files += 1
                try:
                    with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                        total_lines += sum(1 for _ in fh)
                except Exception:
                    pass
    return {"path": path, "python_files": py_files, "approx_lines": total_lines}

PROGRAMMER_TOOLS: Dict[str, Dict[str, Any]] = {
    "read_file": {"name": "read_file", "description": "Read a source file.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "max_lines": {"type": "integer"}}, "required": ["path"]}, "function": read_file},
    "write_file": {"name": "write_file", "description": "Write content to a file.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}, "function": write_file},
    "list_dir": {"name": "list_dir", "description": "List files and directories.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}, "function": list_dir},
    "search_code": {"name": "search_code", "description": "Search source code with grep.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "path": {"type": "string"}, "glob": {"type": "string"}}, "required": ["query"]}, "function": search_code},
    "run_command": {"name": "run_command", "description": "Run a shell command.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}, "function": run_command},
    "run_python": {"name": "run_python", "description": "Execute a Python snippet.",
        "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}, "function": run_python},
    "project_stats": {"name": "project_stats", "description": "Count Python files and lines.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}, "function": diff_stats},
}
