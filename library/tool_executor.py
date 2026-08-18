"""Central tool execution engine for LlmLang."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.builtin import TOOL_REGISTRY, get_tool, list_tools


@dataclass
class ToolCallRequest:
    id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    raw_arguments: str = ""


@dataclass
class ToolCallResult:
    id: str
    name: str
    ok: bool
    result: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    arguments: Dict[str, Any] = field(default_factory=dict)

    def to_message_content(self) -> str:
        if self.ok:
            payload = self.result
        else:
            payload = {"ok": False, "error": self.error, "tool": self.name}
        try:
            return json.dumps(payload, default=str)
        except TypeError:
            return json.dumps({"ok": self.ok, "repr": repr(payload)})

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "ok": self.ok, "result": self.result if self.ok else None,
                "error": self.error, "latency_ms": self.latency_ms, "arguments": self.arguments}


class ToolExecutor:
    def __init__(self, allowed_tools: Optional[List[str]] = None, timeout_s: float = 60.0,
                 parallel: bool = True, max_workers: int = 4, strict_args: bool = False,
                 retries: int = 0, retry_delay_s: float = 0.15):
        self.allowed_tools = set(allowed_tools) if allowed_tools else None
        self.timeout_s = timeout_s
        self.parallel = parallel
        self.max_workers = max_workers
        self.strict_args = strict_args
        self.retries = retries
        self.retry_delay_s = retry_delay_s
        self.history: List[ToolCallResult] = []

    def parse_call(self, tc: Dict[str, Any]) -> ToolCallRequest:
        fn = tc.get("function") or {}
        name = fn.get("name") or tc.get("name") or ""
        raw = fn.get("arguments", tc.get("arguments", {}))
        if isinstance(raw, dict):
            args, raw_s = raw, json.dumps(raw)
        elif isinstance(raw, str):
            raw_s = raw
            try:
                parsed = json.loads(raw) if raw.strip() else {}
                args = parsed if isinstance(parsed, dict) else {"value": parsed}
            except json.JSONDecodeError:
                args = {}
        else:
            args, raw_s = {}, "{}"
        call_id = tc.get("id") or f"call_{name}_{int(time.time()*1000)}"
        return ToolCallRequest(id=call_id, name=name, arguments=args, raw_arguments=raw_s)

    def validate_args(self, name: str, args: Dict[str, Any]) -> Optional[str]:
        if name not in TOOL_REGISTRY:
            return f"Unknown tool: {name}. Known: {list_tools()[:12]}..."
        if self.allowed_tools is not None and name not in self.allowed_tools:
            return f"Tool '{name}' not allowed for this agent. Allowed: {sorted(self.allowed_tools)}"
        schema = TOOL_REGISTRY[name].get("parameters") or {}
        required = schema.get("required") or []
        missing = [k for k in required if k not in args]
        if missing:
            return f"Missing required arguments for {name}: {missing}"
        return None

    def execute_one(self, tc: Union[Dict[str, Any], ToolCallRequest]) -> ToolCallResult:
        req = tc if isinstance(tc, ToolCallRequest) else self.parse_call(tc)
        t0 = time.time()
        err = self.validate_args(req.name, req.arguments)
        if err:
            result = ToolCallResult(id=req.id, name=req.name, ok=False, error=err,
                                   latency_ms=(time.time()-t0)*1000, arguments=req.arguments)
            self.history.append(result)
            return result
        last_err = None
        out = None
        try:
            tool = get_tool(req.name)
            fn = tool["function"]
            attempts = 0
            while attempts <= self.retries:
                attempts += 1
                try:
                    with ThreadPoolExecutor(max_workers=1) as pool:
                        fut = pool.submit(fn, **req.arguments)
                        out = fut.result(timeout=self.timeout_s)
                    last_err = None
                    break
                except FuturesTimeout:
                    last_err = f"Tool '{req.name}' timed out after {self.timeout_s}s"
                    if attempts <= self.retries:
                        time.sleep(self.retry_delay_s)
                except TypeError as e:
                    last_err = f"TypeError calling {req.name}: {e}"
                    break
                except Exception as e:
                    last_err = f"{type(e).__name__}: {e}"
                    if attempts <= self.retries:
                        time.sleep(self.retry_delay_s)
            if last_err and out is None:
                result = ToolCallResult(id=req.id, name=req.name, ok=False, error=last_err,
                                       latency_ms=(time.time()-t0)*1000, arguments=req.arguments)
                self.history.append(result)
                return result
            result = ToolCallResult(id=req.id, name=req.name, ok=True, result=out,
                                   latency_ms=(time.time()-t0)*1000, arguments=req.arguments)
        except Exception as e:
            result = ToolCallResult(id=req.id, name=req.name, ok=False, error=f"{type(e).__name__}: {e}",
                                   latency_ms=(time.time()-t0)*1000, arguments=req.arguments)
        self.history.append(result)
        return result

    def execute_all(self, tool_calls: List[Dict[str, Any]]) -> List[ToolCallResult]:
        if not tool_calls:
            return []
        requests = [self.parse_call(tc) for tc in tool_calls]
        if not self.parallel or len(requests) == 1:
            return [self.execute_one(r) for r in requests]
        results: List[Optional[ToolCallResult]] = [None] * len(requests)
        def run_idx(i: int, req: ToolCallRequest):
            results[i] = self.execute_one(req)
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(requests))) as pool:
            futs = [pool.submit(run_idx, i, r) for i, r in enumerate(requests)]
            for f in futs:
                f.result()
        return [r for r in results if r is not None]

    def to_assistant_message(self, text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"role": "assistant", "content": text or "", "tool_calls": tool_calls}

    def to_tool_messages(self, results: List[ToolCallResult]) -> List[Dict[str, Any]]:
        return [{"role": "tool", "tool_call_id": r.id, "content": r.to_message_content()} for r in results]

    def execute_and_format(self, text: str, tool_calls: List[Dict[str, Any]]):
        results = self.execute_all(tool_calls)
        messages = [self.to_assistant_message(text, tool_calls)] + self.to_tool_messages(results)
        return messages, results


default_executor = ToolExecutor()

def execute_tool_calls(tool_calls: List[Dict[str, Any]], allowed_tools: Optional[List[str]] = None,
                       timeout_s: float = 60.0, parallel: bool = True) -> List[ToolCallResult]:
    ex = ToolExecutor(allowed_tools=allowed_tools, timeout_s=timeout_s, parallel=parallel)
    return ex.execute_all(tool_calls)
