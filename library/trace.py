"""
Execution traces for LlmLang.

Records every model call and tool call so runs are auditable and replayable.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import json
import time
import os


@dataclass
class TraceEvent:
    kind: str  # model | tool | require | info
    name: str
    input: Any = None
    output: Any = None
    confidence: Optional[float] = None
    latency_ms: float = 0.0
    ok: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # ensure JSON-serializable
        for k in ("input", "output"):
            try:
                json.dumps(d[k], default=str)
            except Exception:
                d[k] = str(d[k])
        return d


class Trace:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.events: List[TraceEvent] = []
        self.started_at = time.time()

    def record(self, kind: str, name: str, **kwargs) -> TraceEvent:
        ev = TraceEvent(kind=kind, name=name, **kwargs)
        if self.enabled:
            self.events.append(ev)
        return ev

    def model_call(self, name: str, prompt: str, result: Any, **meta):
        conf = getattr(result, "confidence", None)
        text = getattr(result, "text", str(result))
        lat = getattr(result, "latency_ms", 0.0)
        return self.record(
            "model",
            name,
            input=prompt[:2000] if isinstance(prompt, str) else prompt,
            output=text[:2000] if isinstance(text, str) else text,
            confidence=conf,
            latency_ms=lat or 0.0,
            ok=True,
            meta=meta,
        )

    def tool_call(self, name: str, args: Any, result: Any, **meta):
        ok = bool(getattr(result, "ok", True))
        data = getattr(result, "data", result)
        err = getattr(result, "error", "")
        return self.record(
            "tool",
            name,
            input=args,
            output=data if ok else err,
            ok=ok,
            meta=meta,
        )

    def require(self, name: str, conf_val: float, threshold: float, attempts: int, ok: bool):
        return self.record(
            "require",
            name,
            input={"threshold": threshold, "attempts": attempts},
            output={"confidence": conf_val},
            confidence=conf_val,
            ok=ok,
        )

    def info(self, message: str, **meta):
        return self.record("info", message, meta=meta)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "started_at": self.started_at,
            "duration_ms": (time.time() - self.started_at) * 1000,
            "events": [e.to_dict() for e in self.events],
            "summary": self.summary(),
        }

    def summary(self) -> Dict[str, Any]:
        models = [e for e in self.events if e.kind == "model"]
        tools = [e for e in self.events if e.kind == "tool"]
        return {
            "model_calls": len(models),
            "tool_calls": len(tools),
            "failed_tools": sum(1 for e in tools if not e.ok),
            "avg_model_conf": (
                sum(e.confidence or 0 for e in models) / len(models) if models else None
            ),
            "total_model_latency_ms": sum(e.latency_ms for e in models),
        }

    def save(self, path: str) -> str:
        data = self.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def __len__(self):
        return len(self.events)

    def __repr__(self):
        s = self.summary()
        return f"Trace(models={s['model_calls']}, tools={s['tool_calls']})"


# process-wide optional active trace (set by interpreter/CLI)
_active_trace: Optional[Trace] = None


def get_trace() -> Optional[Trace]:
    return _active_trace


def set_trace(t: Optional[Trace]):
    global _active_trace
    _active_trace = t
    return _active_trace
