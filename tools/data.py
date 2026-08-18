"""Data & productivity tools: CSV, tables, notes, TODOs, analytics."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import os
import csv
import json
from datetime import datetime, timezone

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(PROJECT)

def _safe(path: str) -> str:
    if not path:
        raise ValueError("empty path")
    abs_path = os.path.abspath(os.path.join(PROJECT, path) if not os.path.isabs(path) else path)
    return abs_path

def read_csv(path: str, max_rows: int = 100) -> Dict[str, Any]:
    p = _safe(path)
    if not os.path.isfile(p):
        return {"ok": False, "error": f"not found: {path}"}
    with open(p, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = []
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows.append(dict(row))
        fieldnames = list(reader.fieldnames or [])
    return {"ok": True, "path": path, "columns": fieldnames, "rows": rows, "count": len(rows)}

def write_csv(path: str, rows: Union[List[Dict], str], fieldnames: Optional[List[str]] = None) -> Dict[str, Any]:
    if isinstance(rows, str):
        rows = json.loads(rows)
    p = _safe(path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    if not rows:
        return {"ok": False, "error": "no rows"}
    if not fieldnames:
        fieldnames = list(rows[0].keys())
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})
    return {"ok": True, "path": path, "rows": len(rows), "columns": fieldnames}

def summarize_numbers(values: Union[List[float], str], label: str = "data") -> Dict[str, Any]:
    if isinstance(values, str):
        values = json.loads(values)
    nums = [float(v) for v in values]
    if not nums:
        return {"ok": False, "error": "empty"}
    s = sorted(nums)
    n = len(s)
    mean = sum(s) / n
    mid = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"ok": True, "label": label, "count": n, "min": s[0], "max": s[-1], "sum": sum(s), "mean": mean, "median": mid}

def todo_list(action: str = "list", item: str = "", path: str = "examples/TODOS.json") -> Dict[str, Any]:
    p = _safe(path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"items": []}
    items = data.get("items") or []
    action = (action or "list").lower()
    if action == "add" and item:
        items.append({"text": item, "done": False, "at": datetime.now(timezone.utc).isoformat()})
    elif action == "done" and item:
        for it in items:
            if it.get("text") == item or item in str(it.get("text")):
                it["done"] = True
                break
    elif action == "clear":
        items = [it for it in items if not it.get("done")]
    data["items"] = items
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return {"ok": True, "action": action, "items": items, "path": path}

def write_note(title: str, body: str, path: str = None) -> Dict[str, Any]:
    safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title).strip().replace(" ", "_")
    path = path or f"examples/notes/{safe_title}.md"
    p = _safe(path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    content = f"# {title}\n\n{body}\n"
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return {"ok": True, "path": path, "bytes": len(content.encode())}

def table_to_markdown(rows: Union[List[Dict], str], title: str = "Table") -> Dict[str, Any]:
    if isinstance(rows, str):
        rows = json.loads(rows)
    if not rows:
        return {"ok": False, "error": "no rows"}
    cols = list(rows[0].keys())
    lines = [f"## {title}", "", "| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    md = "\n".join(lines) + "\n"
    return {"ok": True, "markdown": md, "rows": len(rows)}

DATA_TOOLS: Dict[str, Dict[str, Any]] = {
    "read_csv": {"name": "read_csv", "description": "Read a CSV file into rows.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "max_rows": {"type": "integer"}}, "required": ["path"]}, "function": read_csv},
    "write_csv": {"name": "write_csv", "description": "Write rows to CSV.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "rows": {}, "fieldnames": {"type": "array", "items": {"type": "string"}}}, "required": ["path", "rows"]}, "function": write_csv},
    "summarize_numbers": {"name": "summarize_numbers", "description": "Min/max/mean/median/sum.", "parameters": {"type": "object", "properties": {"values": {}, "label": {"type": "string"}}, "required": ["values"]}, "function": summarize_numbers},
    "todo_list": {"name": "todo_list", "description": "Manage todos.", "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "item": {"type": "string"}, "path": {"type": "string"}}, "required": []}, "function": todo_list},
    "write_note": {"name": "write_note", "description": "Write a markdown note.", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "body": {"type": "string"}, "path": {"type": "string"}}, "required": ["title", "body"]}, "function": write_note},
    "table_to_markdown": {"name": "table_to_markdown", "description": "Convert list of objects to markdown table.", "parameters": {"type": "object", "properties": {"rows": {}, "title": {"type": "string"}}, "required": ["rows"]}, "function": table_to_markdown},
}
