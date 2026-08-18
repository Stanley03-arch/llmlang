"""
Built-in tools that both the library and the language can use.
All tools are pure Python so the mock backend can actually execute them.
"""

from __future__ import annotations
from typing import Any, Dict, List, Callable
import re
import math
import importlib


def count_letter(text: str, letter: str) -> Dict[str, Any]:
    if not letter or len(letter) != 1:
        return {"error": "letter must be a single character"}
    count = text.lower().count(letter.lower())
    return {"text": text, "letter": letter, "count": count}


def calculator(expression: str) -> Dict[str, Any]:
    allowed = re.sub(r"[^0-9+\-*/().\s]", "", expression)
    try:
        result = eval(allowed, {"__builtins__": {}}, {})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


def word_length(text: str) -> Dict[str, Any]:
    return {"text": text, "length": len(text), "words": len(text.split())}


TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "count_letter": {
        "name": "count_letter",
        "description": "Count occurrences of a letter in a string (case-insensitive).",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "letter": {"type": "string", "minLength": 1, "maxLength": 1},
            },
            "required": ["text", "letter"],
        },
        "function": count_letter,
    },
    "calculator": {
        "name": "calculator",
        "description": "Evaluate a simple arithmetic expression (+ - * /).",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
        "function": calculator,
    },
    "word_length": {
        "name": "word_length",
        "description": "Return character and word count of a string.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        "function": word_length,
    },
}

try:
    from tools.programmer import PROGRAMMER_TOOLS
    TOOL_REGISTRY.update(PROGRAMMER_TOOLS)
except ImportError:
    pass
try:
    from tools.web import WEB_TOOLS
    TOOL_REGISTRY.update(WEB_TOOLS)
except ImportError:
    pass
try:
    from tools.extra import EXTRA_TOOLS
    TOOL_REGISTRY.update(EXTRA_TOOLS)
except ImportError:
    pass
try:
    from tools.coding import CODING_TOOLS
    TOOL_REGISTRY.update(CODING_TOOLS)
except ImportError:
    pass
try:
    from tools.data import DATA_TOOLS
    TOOL_REGISTRY.update(DATA_TOOLS)
except ImportError:
    pass
try:
    from tools.api_scaffold import API_TOOLS
    TOOL_REGISTRY.update(API_TOOLS)
except ImportError:
    pass
try:
    from tools.util_tools import UTIL_TOOLS
    TOOL_REGISTRY.update(UTIL_TOOLS)
except ImportError:
    pass
try:
    from tools.interop import INTEROP_TOOLS
    TOOL_REGISTRY.update(INTEROP_TOOLS)
except ImportError:
    pass
try:
    from tools.github_tools import GITHUB_TOOLS
    TOOL_REGISTRY.update(GITHUB_TOOLS)
except ImportError:
    pass

def _merge(mod_name: str, attr: str):
    try:
        mod = importlib.import_module(mod_name)
        TOOL_REGISTRY.update(getattr(mod, attr))
    except Exception:
        pass

_merge("tools.memory_tools", "MEMORY_TOOLS")
_merge("tools.plugins", "PLUGIN_TOOLS")
_merge("tools.rag", "RAG_TOOLS")

def get_tool(name: str) -> Dict[str, Any]:
    if name not in TOOL_REGISTRY:
        raise KeyError(f"Unknown tool: {name}")
    return TOOL_REGISTRY[name]

def list_tools() -> List[str]:
    return list(TOOL_REGISTRY.keys())
