"""Small utility tools."""
from __future__ import annotations
from typing import Any, Dict
import uuid
import base64
import hashlib
import json

def make_uuid() -> Dict[str, Any]:
    return {"ok": True, "uuid": str(uuid.uuid4())}

def hash_text(text: str, algo: str = "sha256") -> Dict[str, Any]:
    h = hashlib.new(algo if algo in hashlib.algorithms_available else "sha256")
    h.update(text.encode("utf-8", errors="replace"))
    return {"ok": True, "algo": algo, "hex": h.hexdigest()}

def b64_encode(text: str) -> Dict[str, Any]:
    return {"ok": True, "b64": base64.b64encode(text.encode()).decode()}

def b64_decode(text: str) -> Dict[str, Any]:
    try:
        return {"ok": True, "text": base64.b64decode(text.encode()).decode("utf-8", errors="replace")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def json_get(path: str, data: Any) -> Dict[str, Any]:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return {"ok": False, "error": "invalid json"}
    cur = data
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            i = int(part)
            cur = cur[i] if i < len(cur) else None
        else:
            return {"ok": False, "error": f"cannot traverse {part}"}
    return {"ok": True, "path": path, "value": cur}

UTIL_TOOLS = {
    "make_uuid": {"name": "make_uuid", "description": "Generate a UUID4.", "parameters": {"type": "object", "properties": {}, "required": []}, "function": make_uuid},
    "hash_text": {"name": "hash_text", "description": "Hash text.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "algo": {"type": "string"}}, "required": ["text"]}, "function": hash_text},
    "b64_encode": {"name": "b64_encode", "description": "Base64-encode text.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, "function": b64_encode},
    "b64_decode": {"name": "b64_decode", "description": "Base64-decode text.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, "function": b64_decode},
    "json_get": {"name": "json_get", "description": "Get nested value by path a.b.0.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "data": {}}, "required": ["path", "data"]}, "function": json_get},
}
