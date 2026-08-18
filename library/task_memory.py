"""Task memory — paths, prefs, failures (local JSON)."""
from __future__ import annotations
from typing import Any, Dict, List
import json, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM_PATH = os.path.join(ROOT, "examples", "task_memory.json")

def _now():
    return datetime.now(timezone.utc).isoformat()

def load() -> Dict[str, Any]:
    if not os.path.isfile(MEM_PATH):
        return {"project_root": ROOT, "last_paths": [], "prefs": {"use_go_tools": True, "use_cache": True, "max_patch_files": 5}, "failures": [], "history": []}
    try:
        return json.load(open(MEM_PATH, encoding="utf-8"))
    except Exception:
        return {"project_root": ROOT, "last_paths": [], "prefs": {}, "failures": [], "history": []}

def save(data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(MEM_PATH), exist_ok=True)
    data["updated"] = _now()
    json.dump(data, open(MEM_PATH, "w", encoding="utf-8"), indent=2, default=str)

def remember_path(path: str) -> None:
    data = load()
    paths = data.setdefault("last_paths", [])
    path = os.path.abspath(path)
    if path in paths: paths.remove(path)
    paths.insert(0, path)
    data["last_paths"] = paths[:20]
    save(data)

def remember_failure(task: str, step: str, error: str) -> None:
    data = load()
    fails = data.setdefault("failures", [])
    fails.insert(0, {"task": task, "step": step, "error": error, "ts": _now()})
    data["failures"] = fails[:50]
    save(data)

def remember_success(task: str, summary: str, files: List[str]) -> None:
    data = load()
    hist = data.setdefault("history", [])
    hist.insert(0, {"task": task, "summary": summary, "files": files, "ts": _now()})
    data["history"] = hist[:50]
    for f in files:
        remember_path(f)
    save(data)

def prefs() -> Dict[str, Any]:
    return load().get("prefs") or {}

def set_pref(key: str, value: Any) -> Dict[str, Any]:
    data = load()
    data.setdefault("prefs", {})[key] = value
    save(data)
    return data["prefs"]
