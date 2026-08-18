"""Memory tools exposed to agents."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.memory import memory_add, memory_get, memory_search, memory_list, memory_clear

MEMORY_TOOLS: Dict[str, Dict[str, Any]] = {
    "memory_add": {
        "name": "memory_add",
        "description": "Store a note/fact in agent memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "key": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "namespace": {"type": "string"},
            },
            "required": ["text"],
        },
        "function": lambda text, key=None, tags=None, namespace="default": memory_add(text, key, tags, namespace),
    },
    "memory_search": {
        "name": "memory_search",
        "description": "Search agent memory by keywords.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "namespace": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
        "function": lambda query, namespace="default", limit=5: memory_search(query, namespace, limit),
    },
    "memory_get": {
        "name": "memory_get",
        "description": "Get memory item by key.",
        "parameters": {
            "type": "object",
            "properties": {"key": {"type": "string"}, "namespace": {"type": "string"}},
            "required": ["key"],
        },
        "function": lambda key, namespace="default": memory_get(key, namespace),
    },
    "memory_list": {
        "name": "memory_list",
        "description": "List recent memory items.",
        "parameters": {
            "type": "object",
            "properties": {"namespace": {"type": "string"}, "limit": {"type": "integer"}},
            "required": [],
        },
        "function": lambda namespace="default", limit=20: memory_list(namespace, limit),
    },
}
