"""Additional capabilities: HTTP, JSON, git, markdown, Python package scaffold, time."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(PROJECT)

def _safe(path: str) -> str:
    if not path:
        raise ValueError("empty path")
    return os.path.abspath(os.path.join(PROJECT, path) if not os.path.isabs(path) else path)

def http_get(url: str, timeout: int = 15) -> Dict[str, Any]:
    if not url.startswith(("http://", "https://")):
        return {"error": "url must start with http:// or https://"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LlmLang/1.6"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(50_000).decode("utf-8", errors="replace")
            return {"url": url, "status": resp.status, "content_type": resp.headers.get("Content-Type", ""),
                    "body": body[:8000], "truncated": len(body) >= 8000}
    except Exception as e:
        return {"url": url, "error": str(e)}

def read_json(path: str) -> Dict[str, Any]:
    p = _safe(path)
    if not os.path.isfile(p):
        return {"error": f"not found: {path}"}
    with open(p, encoding="utf-8") as f:
        return {"path": path, "data": json.load(f), "ok": True}

def write_json(path: str, data: Any, indent: int = 2) -> Dict[str, Any]:
    p = _safe(path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            data = {"text": data}
    text = json.dumps(data, indent=indent, ensure_ascii=False) + "\n"
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return {"path": path, "bytes": len(text.encode()), "ok": True}

def append_file(path: str, content: str) -> Dict[str, Any]:
    p = _safe(path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(content)
    return {"path": path, "appended": len(content), "ok": True}

def git_status(path: str = ".") -> Dict[str, Any]:
    p = _safe(path)
    try:
        def run(args):
            return subprocess.run(args, cwd=p, capture_output=True, text=True, timeout=10)
        if run(["git", "rev-parse", "--is-inside-work-tree"]).returncode != 0:
            return {"path": path, "git": False, "message": "not a git repository"}
        status = run(["git", "status", "--short"]).stdout
        branch = run(["git", "branch", "--show-current"]).stdout.strip()
        log = run(["git", "log", "-3", "--oneline"]).stdout.strip()
        return {"path": path, "git": True, "branch": branch, "status": status.strip() or "(clean)",
                "recent": log.splitlines() if log else [], "ok": True}
    except Exception as e:
        return {"path": path, "error": str(e)}

def markdown_report(title: str, sections: Any, path: str = None) -> Dict[str, Any]:
    lines = [f"# {title}", ""]
    if isinstance(sections, str):
        lines.append(sections)
    elif isinstance(sections, list):
        for sec in sections:
            if isinstance(sec, dict):
                lines.append(f"## {sec.get('heading', 'Section')}")
                lines.append("")
                lines.append(str(sec.get("body", "")))
                lines.append("")
            else:
                lines.append(str(sec))
                lines.append("")
    else:
        lines.append(str(sections))
    text = "\n".join(lines).rstrip() + "\n"
    result: Dict[str, Any] = {"title": title, "markdown": text, "ok": True}
    if path:
        p = _safe(path)
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        result["path"] = path
        result["bytes"] = len(text.encode())
    return result

def now(fmt: str = "iso") -> Dict[str, Any]:
    dt = datetime.now(timezone.utc)
    if fmt == "unix":
        return {"utc": dt.timestamp(), "iso": dt.isoformat()}
    return {"iso": dt.isoformat(), "unix": int(dt.timestamp())}

def scaffold_python_package(name: str = "mypackage", description: str = "A small Python package") -> Dict[str, Any]:
    safe_name = re.sub(r"[^a-z0-9_]", "_", name.lower())
    root = _safe(os.path.join("examples", "packages", safe_name))
    pkg = os.path.join(root, safe_name)
    os.makedirs(pkg, exist_ok=True)
    files = {
        os.path.join(root, "pyproject.toml"): f"[project]\nname = \"{safe_name}\"\nversion = \"0.1.0\"\ndescription = \"{description}\"\nrequires-python = \">=3.10\"\n",
        os.path.join(root, "README.md"): f"# {safe_name}\n\n{description}\n",
        os.path.join(pkg, "__init__.py"): f'__version__ = "0.1.0"\ndef hello(name: str = "world") -> str:\n    return f"Hello, {{name}}! from {safe_name}"\n',
        os.path.join(pkg, "cli.py"): f"def main():\n    from {safe_name} import hello\n    print(hello())\nif __name__ == \"__main__\":\n    main()\n",
        os.path.join(root, "tests", "test_basic.py"): f"from {safe_name} import hello\ndef test_hello():\n    assert \"Hello\" in hello()\n",
    }
    os.makedirs(os.path.join(root, "tests"), exist_ok=True)
    written = []
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(os.path.relpath(path, PROJECT))
    return {"name": safe_name, "dir": os.path.relpath(root, PROJECT), "files": written, "ok": True}

def replace_in_file(path: str, old: str, new: str, count: int = 0) -> Dict[str, Any]:
    p = _safe(path)
    if not os.path.isfile(p):
        return {"error": f"not found: {path}"}
    with open(p, encoding="utf-8") as f:
        text = f.read()
    if count == 0:
        updated, n = text.replace(old, new), text.count(old)
    else:
        updated = text.replace(old, new, count)
        n = min(count, text.count(old))
    with open(p, "w", encoding="utf-8") as f:
        f.write(updated)
    return {"path": path, "replacements": n, "ok": True}

EXTRA_TOOLS: Dict[str, Dict[str, Any]] = {
    "http_get": {"name": "http_get", "description": "HTTP GET a URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "timeout": {"type": "integer"}}, "required": ["url"]}, "function": http_get},
    "read_json": {"name": "read_json", "description": "Read and parse a JSON file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, "function": read_json},
    "write_json": {"name": "write_json", "description": "Write a JSON file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "data": {}, "indent": {"type": "integer"}}, "required": ["path", "data"]}, "function": write_json},
    "append_file": {"name": "append_file", "description": "Append text to a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}, "function": append_file},
    "git_status": {"name": "git_status", "description": "Git status, branch, recent commits.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}, "function": git_status},
    "markdown_report": {"name": "markdown_report", "description": "Build a markdown report.", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "sections": {}, "path": {"type": "string"}}, "required": ["title", "sections"]}, "function": markdown_report},
    "now": {"name": "now", "description": "Current UTC time.", "parameters": {"type": "object", "properties": {"fmt": {"type": "string"}}, "required": []}, "function": now},
    "scaffold_python_package": {"name": "scaffold_python_package", "description": "Create a minimal Python package.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}}, "required": ["name"]}, "function": scaffold_python_package},
    "replace_in_file": {"name": "replace_in_file", "description": "Replace text in a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}, "count": {"type": "integer"}}, "required": ["path", "old", "new"]}, "function": replace_in_file},
}
