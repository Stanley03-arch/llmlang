"""Plan → Execute → Verify agent."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.core import model, run_agent, CallResult
from library.tool_executor import ToolExecutor


@dataclass
class PEVResult:
    ok: bool
    plan: List[Dict[str, Any]] = field(default_factory=list)
    executions: List[Dict[str, Any]] = field(default_factory=list)
    verifications: List[Dict[str, Any]] = field(default_factory=list)
    final: str = ""
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "plan": self.plan, "executions": self.executions,
                "verifications": self.verifications, "final": self.final, "latency_ms": self.latency_ms}


def _heuristic_plan(task: str) -> List[Dict[str, Any]]:
    t = task.lower()
    steps = [{"id": "orient", "action": "project_stats", "args": {"path": "."}, "goal": "understand project"}]
    if any(k in t for k in ("search", "find", "where", "locate")):
        q = task
        for prefix in ("search for", "find", "locate"):
            if prefix in t:
                q = task[t.index(prefix) + len(prefix):].strip(" :")
                break
        steps.append({"id": "search", "action": "search_code", "args": {"query": q[:80]}, "goal": "locate code"})
    if any(k in t for k in ("test", "pytest", "verify")):
        steps.append({"id": "test", "action": "run_pytest", "args": {}, "goal": "run tests"})
    if any(k in t for k in ("fix", "bug", "broken", "patch")):
        steps.append({"id": "search_bug", "action": "search_code", "args": {"query": "BUG"}, "goal": "find bug markers"})
        steps.append({"id": "test", "action": "run_pytest", "args": {}, "goal": "confirm"})
    if any(k in t for k in ("stats", "overview", "summary")):
        steps.append({"id": "tree", "action": "project_tree", "args": {"path": ".", "max_depth": 2}, "goal": "tree"})
    if len(steps) == 1:
        steps.append({"id": "search", "action": "search_code", "args": {"query": task[:60]}, "goal": "explore"})
    steps.append({"id": "remember", "action": "memory_add", "args": {"text": f"PEV task: {task}", "tags": ["pev"]}, "goal": "log"})
    return steps


def _execute_step(step: Dict[str, Any], executor: ToolExecutor) -> Dict[str, Any]:
    tool = step.get("action")
    args = step.get("args") or {}
    tr = executor.execute_one({"id": step.get("id", tool), "function": {"name": tool, "arguments": json.dumps(args)}})
    return {"id": step.get("id"), "action": tool, "ok": tr.ok, "result": tr.result if tr.ok else None, "error": tr.error, "latency_ms": tr.latency_ms}


def _verify_step(step: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
    if not execution.get("ok"):
        return {"id": step.get("id"), "ok": False, "reason": execution.get("error") or "execution failed"}
    action = step.get("action")
    result = execution.get("result") or {}
    if action == "search_code":
        return {"id": step.get("id"), "ok": result.get("count", 0) >= 0, "reason": f"matches={result.get('count', 0)}"}
    if action == "run_pytest":
        ok = result.get("ok", result.get("returncode", 1) == 0)
        return {"id": step.get("id"), "ok": bool(ok), "reason": "tests" if ok else "tests failed"}
    if action == "project_stats":
        return {"id": step.get("id"), "ok": "python_files" in result or "ok" in result, "reason": "stats"}
    if action == "memory_add":
        return {"id": step.get("id"), "ok": result.get("ok", False), "reason": "memory"}
    return {"id": step.get("id"), "ok": True, "reason": "default pass"}


def run_pev(task: str, max_replans: int = 1) -> PEVResult:
    t0 = time.time()
    executor = ToolExecutor(timeout_s=60, retries=1)
    plan = _heuristic_plan(task)
    executions, verifications = [], []
    for step in plan:
        ex = _execute_step(step, executor)
        executions.append(ex)
        verifications.append(_verify_step(step, ex))
    failed = [v for v in verifications if not v.get("ok")]
    if failed and max_replans > 0:
        for v in failed:
            step = next((s for s in plan if s.get("id") == v["id"]), None)
            if step and step.get("action") == "search_code":
                step = dict(step)
                step["args"] = dict(step.get("args") or {})
                step["args"]["query"] = (step["args"].get("query") or "def")[:40]
                ex = _execute_step(step, executor)
                executions.append({**ex, "replan": True})
                verifications.append({**_verify_step(step, ex), "replan": True})
    oks = [v.get("ok") for v in verifications]
    ok = sum(1 for x in oks if x) >= max(1, len(oks) // 2)
    final = f"PEV done for: {task!r}. plan_steps={len(plan)} exec={len(executions)} ok_ratio={sum(1 for x in oks if x)}/{len(oks)}"
    return PEVResult(ok=ok, plan=plan, executions=executions, verifications=verifications, final=final, latency_ms=(time.time()-t0)*1000)


def run_pev_with_model(agent: Callable, task: str, max_turns: int = 6):
    prompt = f"PLAN-EXECUTE-VERIFY for task: {task}\n1) Outline 3-6 steps\n2) Execute with tools\n3) Verify and report"
    return run_agent(agent, prompt, max_turns=max_turns)
