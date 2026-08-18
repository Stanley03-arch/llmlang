"""Dynamic tool plugins — register callables at runtime."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional

def _registry():
    from tools.builtin import TOOL_REGISTRY
    return TOOL_REGISTRY

def register_tool(name: str, fn: Callable, description: str = "", parameters: Optional[Dict[str, Any]] = None, overwrite: bool = False) -> Dict[str, Any]:
    reg = _registry()
    if name in reg and not overwrite:
        return {"ok": False, "error": f"tool exists: {name}"}
    reg[name] = {
        "name": name,
        "description": description or f"Plugin tool {name}",
        "parameters": parameters or {"type": "object", "properties": {"input": {"type": "string"}}, "required": []},
        "function": fn,
    }
    return {"ok": True, "name": name, "total_tools": len(reg)}

def unregister_tool(name: str) -> Dict[str, Any]:
    reg = _registry()
    if name not in reg:
        return {"ok": False, "error": "not found"}
    del reg[name]
    return {"ok": True, "name": name, "total_tools": len(reg)}

def list_plugin_tools() -> Dict[str, Any]:
    from tools.builtin import list_tools
    tools = list_tools()
    return {"ok": True, "tools": tools, "count": len(tools)}

PLUGIN_TOOLS: Dict[str, Dict[str, Any]] = {
    "list_all_tools": {
        "name": "list_all_tools",
        "description": "List all registered tool names.",
        "parameters": {"type": "object", "properties": {}, "required": []},
        "function": lambda **kwargs: list_plugin_tools(),
    },
}
