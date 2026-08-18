"""Lightweight durable step log — resume workflows after restart."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
import json
import os
import time
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "durable")

def _ensure():
    os.makedirs(ROOT, exist_ok=True)


@dataclass
class DurableRun:
    run_id: str
    path: str
    completed: Set[str] = field(default_factory=set)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def log(self, event: Dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("ts", datetime.now(timezone.utc).isoformat())
        self.events.append(event)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
        if event.get("type") == "step_done" and event.get("ok"):
            self.completed.add(event.get("step", ""))

    def is_done(self, step: str) -> bool:
        return step in self.completed


def start_run(run_id: Optional[str] = None) -> DurableRun:
    _ensure()
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(ROOT, f"{run_id}.jsonl")
    completed: Set[str] = set()
    events: List[Dict[str, Any]] = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                ev = json.loads(line)
                events.append(ev)
                if ev.get("type") == "step_done" and ev.get("ok"):
                    completed.add(ev.get("step", ""))
    else:
        with open(path, "w", encoding="utf-8") as f:
            meta = {"type": "meta", "run_id": run_id, "started": datetime.now(timezone.utc).isoformat()}
            f.write(json.dumps(meta) + "\n")
            events.append(meta)
    return DurableRun(run_id=run_id, path=path, completed=completed, events=events)


def run_dense_durable(dense: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    from library.dense_ir import parse_dense_line
    from library.tool_executor import ToolExecutor
    run = start_run(run_id)
    steps = parse_dense_line(dense)
    ex = ToolExecutor(timeout_s=60)
    results = []
    ctx: Dict[str, Any] = {}
    run.log({"type": "plan", "dense": dense, "steps": [s.get("name") for s in steps]})
    for step in steps:
        name = step.get("name") or "step"
        if run.is_done(name):
            results.append({"name": name, "skipped": True, "reason": "already completed"})
            continue
        op = step.get("op")
        if op == "tool":
            tool = step.get("tool")
            args = step.get("args") or {}
            t0 = time.time()
            tr = ex.execute_one({"id": name, "function": {"name": tool, "arguments": json.dumps(args)}})
            entry = {"name": name, "op": "tool", "ok": tr.ok, "result": tr.result if tr.ok else None,
                     "error": tr.error, "latency_ms": (time.time() - t0) * 1000}
            results.append(entry)
            run.log({"type": "step_done", "step": name, "ok": tr.ok, "error": tr.error})
            if tr.ok:
                ctx[name] = tr.result
            else:
                run.log({"type": "failed", "step": name})
                return {"ok": False, "run_id": run.run_id, "path": run.path, "results": results, "resumable": True}
        elif op == "llm":
            results.append({"name": name, "op": "llm", "pending": True, "prompt": step.get("prompt")})
            run.log({"type": "step_done", "step": name, "ok": True, "pending_llm": True})
        else:
            run.log({"type": "step_done", "step": name, "ok": False, "error": f"unknown op {op}"})
            return {"ok": False, "run_id": run.run_id, "results": results}
    run.log({"type": "complete", "ok": True})
    return {"ok": True, "run_id": run.run_id, "path": run.path, "results": results, "context_keys": list(ctx.keys())}


def list_runs() -> List[str]:
    _ensure()
    return sorted(os.path.join(ROOT, n) for n in os.listdir(ROOT) if n.endswith(".jsonl"))
