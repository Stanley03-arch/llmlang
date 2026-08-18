"""Coding agent v2 — plan → search → patch → test."""
from __future__ import annotations
from typing import Any, Dict, List
from dataclasses import dataclass, field
import json, os, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class AgentStep:
    name: str
    ok: bool
    detail: Any = None
    ms: float = 0.0
    def to_dict(self):
        return {"name": self.name, "ok": self.ok, "detail": self.detail, "ms": round(self.ms, 2)}

@dataclass
class CodingResult:
    ok: bool
    task: str
    steps: List[AgentStep] = field(default_factory=list)
    summary: str = ""
    files_touched: List[str] = field(default_factory=list)
    def to_dict(self):
        return {"ok": self.ok, "task": self.task, "summary": self.summary,
                "files_touched": self.files_touched, "steps": [s.to_dict() for s in self.steps]}

def _tools_go(batch):
    try:
        from library.go_tools import run_tools_go
        return run_tools_go(batch, parallel=True)
    except Exception as e:
        return {"ok": False, "error": str(e), "results": []}

def _tools_py(name, args):
    try:
        from library.tool_executor import ToolExecutor
        ex = ToolExecutor(timeout_s=60)
        tr = ex.execute_one({"id": name, "function": {"name": name, "arguments": json.dumps(args)}})
        return {"ok": tr.ok, "result": tr.result, "error": tr.error}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _search(query):
    py = _tools_py("search_code", {"query": query, "path": os.path.join(ROOT, "language")})
    if py.get("ok") and py.get("result"):
        return py["result"]
    g = _tools_go([{"name": "search_code", "args": {"path": os.path.join(ROOT, "language"), "query": query}}])
    if g.get("ok") and g.get("results") and g["results"][0].get("ok"):
        return g["results"][0].get("result") or {}
    return {}

def _stats():
    g = _tools_go([{"name": "project_stats", "args": {"path": os.path.join(ROOT, "language")}}])
    if g.get("ok") and g.get("results") and g["results"][0].get("ok"):
        return g["results"][0].get("result") or {}
    return _tools_py("project_stats", {"path": os.path.join(ROOT, "language")}).get("result") or {}

def _run_tests():
    return _tools_py("run_pytest", {"path": os.path.join(ROOT, "tests")})

def _plan(task):
    t = task.lower()
    steps = ["stats", "search"]
    if any(k in t for k in ("test", "pytest", "fix")): steps.append("test")
    if any(k in t for k in ("website", "site", "fullstack", "web")): steps.append("scaffold_web")
    if any(k in t for k in ("refactor", "patch", "edit", "fix", "add")): steps.append("patch")
    if "test" not in steps: steps.append("test")
    return steps

def _extract_symbol(task):
    m = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b", task)
    stop = {"the", "and", "for", "find", "fix", "add", "with", "from", "this", "that", "code", "file"}
    cands = [x for x in m if x.lower() not in stop]
    return cands[-1] if cands else "def"

def run_coding_agent_v2(task: str, apply_patch: bool = False) -> CodingResult:
    t0 = time.perf_counter()
    steps_out, files = [], []
    plan = _plan(task)
    t1 = time.perf_counter()
    steps_out.append(AgentStep("stats", True, _stats(), (time.perf_counter()-t1)*1000))
    t1 = time.perf_counter()
    sym = _extract_symbol(task)
    found = _search(sym)
    steps_out.append(AgentStep("search", True, {"query": sym, "result": found}, (time.perf_counter()-t1)*1000))
    if "scaffold_web" in plan:
        t1 = time.perf_counter()
        try:
            from tools.fullstack import scaffold_fullstack
            name = re.sub(r"[^a-z0-9_]+", "_", task.lower())[:24] or "agent_site"
            r = scaffold_fullstack(name=name, title=task[:40])
            files.extend(r.get("files") or [])
            steps_out.append(AgentStep("scaffold_web", bool(r.get("ok")), r, (time.perf_counter()-t1)*1000))
        except Exception as e:
            steps_out.append(AgentStep("scaffold_web", False, str(e), (time.perf_counter()-t1)*1000))
    if "patch" in plan:
        t1 = time.perf_counter()
        note_path = os.path.join(ROOT, "examples", "agent_patches", f"patch_{int(time.time())}.md")
        os.makedirs(os.path.dirname(note_path), exist_ok=True)
        matches = (found or {}).get("matches") or []
        body = [f"# Agent patch plan: {task}", f"Symbol: `{sym}`", f"Matches: {len(matches)}", ""]
        for m in matches[:10]:
            body.append(f"- {m.get('file')}")
        open(note_path, "w").write("\n".join(body)+"\n")
        files.append(os.path.relpath(note_path, ROOT))
        steps_out.append(AgentStep("patch", True, {"path": note_path}, (time.perf_counter()-t1)*1000))
    t1 = time.perf_counter()
    test_r = _run_tests()
    steps_out.append(AgentStep("test", bool(test_r.get("ok")), test_r, (time.perf_counter()-t1)*1000))
    core_ok = all(s.ok for s in steps_out if s.name in ("stats", "search"))
    summary = f"Coding agent v2: plan={plan}, symbol={sym}, files={len(files)}, steps={len(steps_out)}, total_ms={round((time.perf_counter()-t0)*1000,1)}"
    return CodingResult(ok=core_ok, task=task, steps=steps_out, summary=summary, files_touched=files)
