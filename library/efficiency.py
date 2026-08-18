"""Token efficiency and multi-task speed utilities for LlmLang."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
import time

from library.tool_executor import ToolExecutor

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "cache")


class SharedCache:
    def __init__(self, namespace: str = "llm"):
        self.namespace = namespace
        self._mem: Dict[str, Any] = {}
        self.hits = 0
        self.misses = 0
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _key(self, tool: str, arguments: Dict[str, Any]) -> str:
        raw = json.dumps({"tool": tool, "args": arguments}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def get(self, tool: str, arguments: Dict[str, Any]):
        k = self._key(tool, arguments)
        if k in self._mem:
            self.hits += 1
            return self._mem[k]
        path = os.path.join(CACHE_DIR, f"{self.namespace}_{k}.json")
        if os.path.isfile(path):
            try:
                data = json.load(open(path))
                self._mem[k] = data
                self.hits += 1
                return data
            except Exception:
                pass
        self.misses += 1
        return None

    def set(self, tool: str, arguments: Dict[str, Any], value: Any):
        k = self._key(tool, arguments)
        self._mem[k] = value
        path = os.path.join(CACHE_DIR, f"{self.namespace}_{k}.json")
        try:
            json.dump(value, open(path, "w"), default=str)
        except Exception:
            pass

    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        return {"hits": self.hits, "misses": self.misses, "hit_rate": (self.hits / total) if total else 0.0,
                "entries": len(self._mem), "persist": True, "namespace": self.namespace}

_shared = SharedCache()

def get_shared_cache() -> SharedCache:
    return _shared


@dataclass
class TaskResult:
    name: str
    ok: bool
    output: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    cached: bool = False


@dataclass
class ParallelReport:
    ok: bool
    results: List[TaskResult] = field(default_factory=list)
    wall_ms: float = 0.0
    serial_ms: float = 0.0
    speedup: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "wall_ms": self.wall_ms, "serial_ms": self.serial_ms, "speedup": self.speedup,
                "results": [{"name": r.name, "ok": r.ok, "cached": r.cached, "latency_ms": r.latency_ms} for r in self.results]}


def run_tasks_parallel(tasks: List[Dict[str, Any]], max_workers: int = 4, use_cache: bool = True) -> ParallelReport:
    executor = ToolExecutor(timeout_s=60)
    cache = get_shared_cache()
    t0 = time.time()
    results: List[TaskResult] = [None] * len(tasks)  # type: ignore

    def run_one(i: int, task: Dict[str, Any]) -> TaskResult:
        name = task.get("name") or f"t{i}"
        tool = task.get("tool") or ""
        args = task.get("arguments") or {}
        t1 = time.time()
        if use_cache:
            hit = cache.get(tool, args)
            if hit is not None:
                return TaskResult(name=name, ok=True, output=hit, latency_ms=(time.time()-t1)*1000, cached=True)
        tr = executor.execute_one({"id": name, "function": {"name": tool, "arguments": json.dumps(args)}})
        if tr.ok and use_cache:
            cache.set(tool, args, tr.result)
        return TaskResult(name=name, ok=tr.ok, output=tr.result if tr.ok else None, error=tr.error,
                          latency_ms=(time.time()-t1)*1000, cached=False)

    with ThreadPoolExecutor(max_workers=min(max_workers, max(1, len(tasks)))) as pool:
        futs = {pool.submit(run_one, i, t): i for i, t in enumerate(tasks)}
        for fut in as_completed(futs):
            i = futs[fut]
            results[i] = fut.result()
    wall = (time.time() - t0) * 1000
    serial = sum(r.latency_ms for r in results if r)
    speedup = (serial / wall) if wall > 0 else 1.0
    ok = all(r.ok for r in results if r)
    return ParallelReport(ok=ok, results=[r for r in results if r], wall_ms=wall, serial_ms=serial, speedup=speedup)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)

def compact_messages(messages: List[Dict[str, Any]], max_tokens: int = 2000):
    original = sum(estimate_tokens(str(m.get("content", ""))) for m in messages)
    if original <= max_tokens:
        return messages, {"original_tokens": original, "compacted_tokens": original}
    system = [m for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]
    kept = system + rest[-max(1, max_tokens // 100):]
    compacted = sum(estimate_tokens(str(m.get("content", ""))) for m in kept)
    return kept, {"original_tokens": original, "compacted_tokens": compacted}

def tool_schema_tokens(tool_names: List[str]) -> Dict[str, Any]:
    from tools.builtin import TOOL_REGISTRY
    full = sum(estimate_tokens(json.dumps(TOOL_REGISTRY[n].get("parameters", {}))) for n in tool_names if n in TOOL_REGISTRY)
    slim = sum(estimate_tokens(n + str(TOOL_REGISTRY[n].get("description", "")[:80])) for n in tool_names if n in TOOL_REGISTRY)
    return {"full_est_tokens": full, "slim_est_tokens": slim}

_PREFETCH_RULES = [
    (["search", "find", "where", "locate"], "search_code", lambda p: {"query": p[:80], "path": "."}),
    (["stats", "overview", "how many"], "project_stats", lambda p: {"path": "."}),
    (["rag", "retrieve", "relevant"], "codebase_rag", lambda p: {"query": p[:80], "top_k": 3}),
    (["time", "clock", "now"], "now", lambda p: {}),
]

def speculative_prefetch(prompt: str, max_tools: int = 3, use_cache: bool = True) -> Dict[str, Any]:
    pl = (prompt or "").lower()
    tasks = []
    seen = set()
    for keywords, tool, argfn in _PREFETCH_RULES:
        if any(k in pl for k in keywords) and tool not in seen:
            seen.add(tool)
            tasks.append({"name": f"prefetch_{tool}", "kind": "tool", "tool": tool, "arguments": argfn(prompt)})
        if len(tasks) >= max_tools:
            break
    if not tasks:
        tasks = [{"name": "prefetch_stats", "kind": "tool", "tool": "project_stats", "arguments": {"path": "."}}]
    report = run_tasks_parallel(tasks, max_workers=max_tools, use_cache=use_cache)
    return {"prompt_preview": (prompt or "")[:100], "prefetched": [t["name"] for t in tasks], "report": report.to_dict()}

def fast_ai_agent(task: str) -> Dict[str, Any]:
    t0 = time.time()
    pref = speculative_prefetch(task, max_tools=3, use_cache=True)
    elapsed = (time.time() - t0) * 1000
    return {"task": task, "elapsed_ms": elapsed, "prefetch": pref["prefetched"], "cache": get_shared_cache().stats(),
            "summary": f"fast_ai completed in {elapsed:.0f}ms with prefetch={pref['prefetched']}"}

def ai_speed_benchmark() -> Dict[str, Any]:
    toolspecs = [
        {"name": "search", "kind": "tool", "tool": "search_code", "arguments": {"query": "CallResult"}},
        {"name": "stats", "kind": "tool", "tool": "project_stats", "arguments": {"path": "."}},
        {"name": "calc", "kind": "tool", "tool": "calculator", "arguments": {"expression": "1+1"}},
    ]
    ex = ToolExecutor(timeout_s=60)
    t0 = time.time()
    for t in toolspecs:
        ex.execute_one({"id": t["name"], "function": {"name": t["tool"], "arguments": json.dumps(t["arguments"])}})
    serial_ms = (time.time() - t0) * 1000
    cold = run_tasks_parallel(toolspecs, max_workers=3, use_cache=True)
    warm = run_tasks_parallel(toolspecs, max_workers=3, use_cache=True)
    return {"serial_ms": serial_ms, "parallel_cold_ms": cold.wall_ms, "parallel_warm_ms": warm.wall_ms,
            "parallel_speedup_vs_serial": (serial_ms / cold.wall_ms) if cold.wall_ms else None,
            "cache_speedup_vs_serial": (serial_ms / warm.wall_ms) if warm.wall_ms else None,
            "cache_stats": get_shared_cache().stats()}
