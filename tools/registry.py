"""
Tool registry for LlmLang.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str = ""

    def __str__(self):
        if self.ok:
            return str(self.data) if self.data is not None else "ok"
        return f"[tool error] {self.error}"

    def __bool__(self):
        return self.ok


ToolFn = Callable[..., ToolResult]
TOOLS: Dict[str, ToolFn] = {}


def tool(name: str = None):
    def decorator(fn: ToolFn):
        key = name or fn.__name__
        TOOLS[key] = fn
        return fn
    return decorator


def get_tool(name: str) -> Optional[ToolFn]:
    return TOOLS.get(name)


def list_tools() -> List[str]:
    return sorted(TOOLS.keys())


def call_tool(name: str, *args, **kwargs) -> ToolResult:
    fn = TOOLS.get(name)
    if not fn:
        return ToolResult(ok=False, error=f"unknown tool: {name}")
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("calc")
def tool_calc(expression: str) -> ToolResult:
    expr = str(expression).strip()
    if not re.fullmatch(r"[0-9+\-*/().%\s]+", expr):
        return ToolResult(ok=False, error="only basic arithmetic allowed")
    try:
        value = eval(expr, {"__builtins__": {}}, {})
        return ToolResult(ok=True, data=value)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("now")
def tool_now(fmt: str = "%Y-%m-%d %H:%M:%S") -> ToolResult:
    try:
        s = datetime.now(timezone.utc).strftime(str(fmt))
        return ToolResult(ok=True, data=s)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("json_parse")
def tool_json_parse(text: str) -> ToolResult:
    try:
        return ToolResult(ok=True, data=json.loads(str(text)))
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("json_stringify")
def tool_json_stringify(obj: Any, indent: int = 2) -> ToolResult:
    try:
        return ToolResult(ok=True, data=json.dumps(obj, indent=int(indent), default=str))
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("http_get")
def tool_http_get(url: str, timeout: float = 15) -> ToolResult:
    try:
        req = Request(str(url), headers={"User-Agent": "LlmLang/0.3"})
        with urlopen(req, timeout=float(timeout)) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return ToolResult(ok=True, data={"status": resp.status, "body": body[:50000]})
    except (URLError, HTTPError, Exception) as e:
        return ToolResult(ok=False, error=str(e))


@tool("read_file")
def tool_read_file(path: str) -> ToolResult:
    try:
        with open(str(path), "r", encoding="utf-8") as f:
            return ToolResult(ok=True, data=f.read())
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("write_file")
def tool_write_file(path: str, content: str) -> ToolResult:
    try:
        with open(str(path), "w", encoding="utf-8") as f:
            f.write(str(content))
        return ToolResult(ok=True, data={"path": path, "bytes": len(str(content))})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("append_file")
def tool_append_file(path: str, content: str) -> ToolResult:
    try:
        with open(str(path), "a", encoding="utf-8") as f:
            f.write(str(content))
        return ToolResult(ok=True, data={"path": path})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("list_dir")
def tool_list_dir(path: str = ".") -> ToolResult:
    try:
        return ToolResult(ok=True, data=os.listdir(str(path)))
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("env")
def tool_env(name: str, default: str = "") -> ToolResult:
    return ToolResult(ok=True, data=os.environ.get(str(name), str(default)))


@tool("sleep")
def tool_sleep(seconds: float = 1) -> ToolResult:
    time.sleep(float(seconds))
    return ToolResult(ok=True, data=True)


@tool("regex_search")
def tool_regex_search(pattern: str, text: str) -> ToolResult:
    try:
        m = re.search(str(pattern), str(text))
        if not m:
            return ToolResult(ok=True, data=None)
        return ToolResult(ok=True, data={"match": m.group(0), "groups": list(m.groups())})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("upper")
def tool_upper(text: str) -> ToolResult:
    return ToolResult(ok=True, data=str(text).upper())


@tool("lower")
def tool_lower(text: str) -> ToolResult:
    return ToolResult(ok=True, data=str(text).lower())


@tool("split")
def tool_split(text: str, sep: str = " ") -> ToolResult:
    return ToolResult(ok=True, data=str(text).split(str(sep)))


@tool("join")
def tool_join(items: Any, sep: str = " ") -> ToolResult:
    try:
        return ToolResult(ok=True, data=str(sep).join(str(x) for x in items))
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool("contains")
def tool_contains(haystack: str, needle: str) -> ToolResult:
    return ToolResult(ok=True, data=str(needle) in str(haystack))


@tool("starts_with")
def tool_starts_with(text: str, prefix: str) -> ToolResult:
    return ToolResult(ok=True, data=str(text).startswith(str(prefix)))


@tool("strip")
def tool_strip(text: str) -> ToolResult:
    return ToolResult(ok=True, data=str(text).strip())


@tool("replace")
def tool_replace(text: str, old: str, new: str) -> ToolResult:
    return ToolResult(ok=True, data=str(text).replace(str(old), str(new)))
