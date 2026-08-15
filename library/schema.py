"""
Lightweight JSON schema validation for LlmLang structured outputs.

Supports a practical subset:
  type, properties, required, items, enum, minimum, maximum,
  minLength, maxLength, additionalProperties
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


def validate(data: Any, schema: Dict[str, Any], path: str = "$") -> Tuple[bool, List[str]]:
    """Validate data against schema. Returns (ok, list_of_errors)."""
    errors: List[str] = []
    _check(data, schema, path, errors)
    return (len(errors) == 0, errors)


def _check(data: Any, schema: Dict[str, Any], path: str, errors: List[str]) -> None:
    if not isinstance(schema, dict):
        errors.append(f"{path}: schema must be an object")
        return

    t = schema.get("type")
    if t:
        ok = _type_ok(data, t)
        if not ok:
            errors.append(f"{path}: expected type {t}, got {type(data).__name__}")
            return

    if "enum" in schema:
        if data not in schema["enum"]:
            errors.append(f"{path}: value not in enum {schema['enum']}")

    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"{path}: {data} < minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"{path}: {data} > maximum {schema['maximum']}")

    if isinstance(data, str):
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength")
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errors.append(f"{path}: string longer than maxLength")

    if isinstance(data, list) and "items" in schema:
        item_schema = schema["items"]
        for i, item in enumerate(data):
            _check(item, item_schema, f"{path}[{i}]", errors)

    if isinstance(data, dict) and "properties" in schema:
        props = schema["properties"] or {}
        required = schema.get("required") or []
        for key in required:
            if key not in data:
                errors.append(f"{path}: missing required property '{key}'")
        for key, val in data.items():
            if key in props:
                _check(val, props[key], f"{path}.{key}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property '{key}'")


def _type_ok(data: Any, t: Any) -> bool:
    if isinstance(t, list):
        return any(_type_ok(data, x) for x in t)
    mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "null": type(None),
    }
    py = mapping.get(t)
    if py is None:
        return True
    if t == "number":
        return isinstance(data, (int, float)) and not isinstance(data, bool)
    if t == "integer":
        return isinstance(data, int) and not isinstance(data, bool)
    return isinstance(data, py)


# Common ready-made schemas
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning": {"type": "string"},
    },
    "required": ["answer", "confidence"],
    "additionalProperties": True,
}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "action": {"type": "string"},
                },
                "required": ["id", "action"],
            },
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["goal", "steps"],
    "additionalProperties": True,
}

CRITIQUE_SCHEMA = {
    "type": "object",
    "properties": {
        "critique": {"type": "string"},
        "score": {"type": "number", "minimum": 0, "maximum": 1},
        "issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["critique", "score"],
    "additionalProperties": True,
}

NAMED_SCHEMAS = {
    "answer": ANSWER_SCHEMA,
    "plan": PLAN_SCHEMA,
    "critique": CRITIQUE_SCHEMA,
}


def resolve_schema(spec: Any) -> Optional[Dict[str, Any]]:
    """Accept a dict schema or a named string ('answer'|'plan'|'critique')."""
    if spec is None:
        return None
    if isinstance(spec, str):
        return NAMED_SCHEMAS.get(spec.lower())
    if isinstance(spec, dict):
        return spec
    return None
