"""Builder (Tangle-inspired) — NL → dense IR / .ll with static check."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
import re

from library.dense_ir import (
    expand_to_ll, run_dense, density_report,
    PYTHON_AGENT_GLUE, LL_EQUIVALENT, DENSE_EQUIVALENT,
)
from library.static_check import check_source


@dataclass
class BuildResult:
    ok: bool
    intent: str
    dense: str = ""
    ll_source: str = ""
    check: Optional[Dict[str, Any]] = None
    run: Optional[Dict[str, Any]] = None
    density: Optional[Dict[str, Any]] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "intent": self.intent, "dense": self.dense, "ll_source": self.ll_source,
                "check": self.check, "run": self.run, "density": self.density, "notes": self.notes}


def _heuristic_dense(intent: str) -> str:
    t = intent.lower()
    steps = []
    if any(k in t for k in ("search", "find", "where", "locate")):
        q = intent
        for p in ("search for", "find", "locate"):
            if p in t:
                q = intent[t.index(p) + len(p):].strip(" :")
                break
        q = re.sub(r"[^\w\s.]", "", q)[:60].strip() or "def"
        steps.append(f"T search_code query={q.replace(' ', '_')}")
    if any(k in t for k in ("stats", "size", "overview", "how big", "project")):
        steps.append("T project_stats path=.")
    if any(k in t for k in ("test", "pytest")):
        steps.append("T run_pytest path=tests")
    if any(k in t for k in ("time", "now", "clock")):
        steps.append("T now")
    if any(k in t for k in ("website", "site")):
        steps.append("T scaffold_website name=built title=Built")
    if not steps:
        steps.append("T project_stats path=.")
        steps.append("T search_code query=" + re.sub(r"\s+", "_", intent)[:40])
    if any(k in t for k in ("summarize", "explain", "report")):
        steps.append('L "summarize tool results for the user"')
    return " | ".join(steps)


def build_from_intent(intent: str, run: bool = True, agent: Optional[Callable] = None) -> BuildResult:
    notes = []
    dense = _heuristic_dense(intent)
    notes.append(f"dense plan: {dense}")
    ll_source = expand_to_ll(dense)
    check_dict = check_source(ll_source).to_dict() if ll_source.strip() else None
    run_result = run_dense(dense) if run else None
    dens = density_report(PYTHON_AGENT_GLUE, LL_EQUIVALENT, dense)
    notes.append(f"token density vs Python: dense≈{dens.get('dense_vs_python')}x smaller")
    ok = True if run_result is None else bool(run_result.get("ok"))
    return BuildResult(ok=ok, intent=intent, dense=dense, ll_source=ll_source, check=check_dict, run=run_result, density=dens, notes=notes)


def compare_to_python() -> Dict[str, Any]:
    return {
        "python_sample": PYTHON_AGENT_GLUE.strip()[:400] + "...",
        "ll_sample": LL_EQUIVALENT.strip(),
        "dense_sample": DENSE_EQUIVALENT,
        "report": density_report(PYTHON_AGENT_GLUE, LL_EQUIVALENT, DENSE_EQUIVALENT),
        "claim": (
            "Weft-style win: dense IR and short .ll express the same agent workflow "
            "in a fraction of the tokens of Python OpenAI tool-loop glue. "
            "Static check catches unknown tools before runtime."
        ),
    }
