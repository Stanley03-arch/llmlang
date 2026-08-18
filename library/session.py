"""Session persistence for agent runs — JSONL history under examples/sessions/."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import json
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "sessions")

def _ensure():
    os.makedirs(ROOT, exist_ok=True)

def new_session(name: str = None) -> str:
    _ensure()
    name = name or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(ROOT, f"{name}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "meta", "name": name, "started": datetime.now(timezone.utc).isoformat()}) + "\n")
    return path

def log_event(session_path: str, event: Dict[str, Any]) -> None:
    event = dict(event)
    event.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with open(session_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")

def load_session(session_path: str) -> List[Dict[str, Any]]:
    events = []
    with open(session_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events

def list_sessions() -> List[str]:
    _ensure()
    return sorted(os.path.join(ROOT, n) for n in os.listdir(ROOT) if n.endswith(".jsonl"))
