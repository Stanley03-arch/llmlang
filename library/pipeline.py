"""Pipeline runner — ordered multi-step tool/agent workflows with retries."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
import time
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.tool_executor import ToolExecutor


@dataclass
class StepResult:
    name: str
    ok: bool
    output: Any = None
    error: Optional[str] = None
    attempts: int = 1
    latency_ms: float = 0.0


@dataclass
class PipelineResult:
    ok: bool
    steps: List[StepResult] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "steps": [{"name": s.name, "ok": s.ok, "output": s.output, "error": s.error,
                       "attempts": s.attempts, "latency_ms": s.latency_ms} for s in self.steps],
            "context": self.context,
        }


class Pipeline:
    def __init__(self, name: str = "pipeline", retries: int = 0):
        self.name = name
        self.retries = retries
        self._steps: List[Dict[str, Any]] = []
        self.executor = ToolExecutor(timeout_s=60, retries=0)

    def tool(self, name: str, tool_name: str, arguments: Dict[str, Any] = None) -> "Pipeline":
        self._steps.append({"kind": "tool", "name": name, "tool": tool_name, "arguments": arguments or {}})
        return self

    def fn(self, name: str, func: Callable[[Dict[str, Any]], Any]) -> "Pipeline":
        self._steps.append({"kind": "fn", "name": name, "func": func})
        return self

    def run(self, context: Dict[str, Any] = None) -> PipelineResult:
        ctx = dict(context or {})
        results: List[StepResult] = []
        overall = True
        for step in self._steps:
            t0 = time.time()
            attempts = 0
            last_err = None
            out = None
            ok = False
            while attempts <= self.retries:
                attempts += 1
                try:
                    if step["kind"] == "tool":
                        tr = self.executor.execute_one({
                            "id": step["name"],
                            "function": {"name": step["tool"], "arguments": json.dumps(step["arguments"])},
                        })
                        if not tr.ok:
                            last_err = tr.error
                            continue
                        out = tr.result
                    else:
                        out = step["func"](ctx)
                    ok = True
                    last_err = None
                    break
                except Exception as e:
                    last_err = str(e)
            sr = StepResult(name=step["name"], ok=ok, output=out, error=last_err,
                            attempts=attempts, latency_ms=(time.time()-t0)*1000)
            results.append(sr)
            if ok:
                ctx[step["name"]] = out
            else:
                overall = False
                break
        return PipelineResult(ok=overall, steps=results, context=ctx)
