"""Workflow engine — DAG of steps with dependencies and parallel waves."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.tool_executor import ToolExecutor


@dataclass
class StepSpec:
    name: str
    kind: str
    tool: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    func: Optional[Callable] = None
    depends_on: List[str] = field(default_factory=list)
    verify: Optional[Callable[[Any, Dict], bool]] = None


@dataclass
class StepOutcome:
    name: str
    ok: bool
    output: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0


@dataclass
class WorkflowResult:
    ok: bool
    outcomes: Dict[str, StepOutcome] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    order: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "order": self.order,
            "outcomes": {k: {"name": v.name, "ok": v.ok, "output": v.output, "error": v.error, "latency_ms": v.latency_ms} for k, v in self.outcomes.items()},
            "context_keys": list(self.context.keys()),
        }


class Workflow:
    def __init__(self, name: str = "workflow", max_workers: int = 4):
        self.name = name
        self.max_workers = max_workers
        self._steps: Dict[str, StepSpec] = {}
        self.executor = ToolExecutor(timeout_s=90, parallel=False)

    def tool(self, name: str, tool_name: str, arguments: Dict[str, Any] = None, depends_on: List[str] = None, verify: Callable = None) -> "Workflow":
        self._steps[name] = StepSpec(name=name, kind="tool", tool=tool_name, arguments=arguments or {}, depends_on=depends_on or [], verify=verify)
        return self

    def fn(self, name: str, func: Callable[[Dict[str, Any]], Any], depends_on: List[str] = None, verify: Callable = None) -> "Workflow":
        self._steps[name] = StepSpec(name=name, kind="fn", func=func, depends_on=depends_on or [], verify=verify)
        return self

    def _ready(self, done: Set[str]) -> List[str]:
        return [name for name, spec in self._steps.items() if name not in done and all(d in done for d in spec.depends_on)]

    def _run_one(self, spec: StepSpec, ctx: Dict[str, Any]) -> StepOutcome:
        t0 = time.time()
        try:
            if spec.kind == "tool":
                args = {}
                for k, v in spec.arguments.items():
                    if isinstance(v, str) and v.startswith("$") and v[1:] in ctx:
                        args[k] = ctx[v[1:]]
                    else:
                        args[k] = v
                tr = self.executor.execute_one({"id": spec.name, "function": {"name": spec.tool, "arguments": json.dumps(args)}})
                if not tr.ok:
                    return StepOutcome(spec.name, False, error=tr.error, latency_ms=(time.time()-t0)*1000)
                out = tr.result
            else:
                out = spec.func(ctx)
            if spec.verify and not spec.verify(out, ctx):
                return StepOutcome(spec.name, False, output=out, error="verify failed", latency_ms=(time.time()-t0)*1000)
            return StepOutcome(spec.name, True, output=out, latency_ms=(time.time()-t0)*1000)
        except Exception as e:
            return StepOutcome(spec.name, False, error=str(e), latency_ms=(time.time()-t0)*1000)

    def run(self, context: Dict[str, Any] = None) -> WorkflowResult:
        ctx = dict(context or {})
        done: Set[str] = set()
        outcomes: Dict[str, StepOutcome] = {}
        order: List[str] = []
        overall = True
        while len(done) < len(self._steps):
            ready = self._ready(done)
            if not ready:
                for n in self._steps:
                    if n not in done:
                        outcomes[n] = StepOutcome(n, False, error="unmet dependencies or cycle")
                overall = False
                break
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(ready))) as pool:
                futs = {pool.submit(self._run_one, self._steps[n], ctx): n for n in ready}
                for fut in as_completed(futs):
                    name = futs[fut]
                    outcome = fut.result()
                    outcomes[name] = outcome
                    order.append(name)
                    done.add(name)
                    if outcome.ok:
                        ctx[name] = outcome.output
                    else:
                        overall = False
            if not overall:
                break
        return WorkflowResult(ok=overall, outcomes=outcomes, context=ctx, order=order)
