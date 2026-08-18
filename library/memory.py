"""Lightweight persistent memory for agents (keyword search, no vector DB)."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import json
import time
import hashlib
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "memory")

def _path(namespace: str = "default") -> str:
    os.makedirs(ROOT, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in namespace)
    return os.path.join(ROOT, f"{safe}.json")

def _load(namespace: str) -> Dict[str, Any]:
    p = _path(namespace)
    if not os.path.isfile(p):
        return {"namespace": namespace, "items": []}
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def _save(namespace: str, data: Dict[str, Any]) -> None:
    with open(_path(namespace), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

def memory_add(text: str, key: str = None, tags: Optional[List[str]] = None, namespace: str = "default", meta: Optional[Dict] = None) -> Dict[str, Any]:
    data = _load(namespace)
    item_id = key or hashlib.sha1(f"{time.time()}:{text[:40]}".encode()).hexdigest()[:12]
    item = {"id": item_id, "text": text, "tags": tags or [], "meta": meta or {}, "created": datetime.now(timezone.utc).isoformat()}
    items = [i for i in data["items"] if i.get("id") != item_id]
    items.append(item)
    data["items"] = items
    _save(namespace, data)
    return {"ok": True, "id": item_id, "namespace": namespace}

def memory_get(key: str, namespace: str = "default") -> Dict[str, Any]:
    for i in _load(namespace)["items"]:
        if i.get("id") == key:
            return {"ok": True, "item": i}
    return {"ok": False, "error": f"not found: {key}"}

def memory_search(query: str, namespace: str = "default", limit: int = 5) -> Dict[str, Any]:
    q = query.lower().split()
    scored = []
    for item in _load(namespace)["items"]:
        blob = ((item.get("text") or "") + " " + " ".join(item.get("tags") or [])).lower()
        score = sum(1 for t in q if t in blob)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: -x[0])
    hits = [item for _, item in scored[:limit]]
    return {"ok": True, "query": query, "count": len(hits), "items": hits}

def memory_list(namespace: str = "default", limit: int = 20) -> Dict[str, Any]:
    data = _load(namespace)
    return {"ok": True, "namespace": namespace, "count": len(data["items"]), "items": data["items"][-limit:]}

def memory_clear(namespace: str = "default") -> Dict[str, Any]:
    _save(namespace, {"namespace": namespace, "items": []})
    return {"ok": True, "namespace": namespace, "cleared": True}
