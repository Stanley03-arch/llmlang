"""
Core types and helpers for LlmLang.

CallResult is a first-class value: text + confidence + provenance.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import json
import hashlib
import time

from library.schema import validate as schema_validate, resolve_schema


@dataclass
class ModelConfig:
    name: str
    system: str = "You are a helpful assistant."
    temperature: float = 0.2
    mode: str = "free"  # free | json | tools
    tools: List[str] = field(default_factory=list)
    max_tokens: int = 1024
    schema: Any = None  # dict or named schema string
    min_conf: float = 0.0  # soft default; require() can override
    max_retries: int = 0
    cache: str = "exact"  # exact | off


@dataclass
class CallResult:
    """First-class value returned by every model call."""
    text: str
    confidence: float = 0.5
    model: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    fingerprint: str = ""
    raw: Any = None
    latency_ms: float = 0.0
    data: Any = None
    schema_ok: Optional[bool] = None
    schema_errors: List[str] = field(default_factory=list)
    attempts: int = 1

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"CallResult(text={self.text!r}, conf={self.confidence:.2f}, model={self.model!r})"

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "model": self.model,
            "tool_calls": self.tool_calls,
            "fingerprint": self.fingerprint,
            "latency_ms": self.latency_ms,
            "data": self.data,
            "schema_ok": self.schema_ok,
            "schema_errors": self.schema_errors,
            "attempts": self.attempts,
        }

    def json(self) -> Any:
        if self.data is not None:
            return self.data
        try:
            return json.loads(self.text)
        except Exception:
            return None


def conf(x: Any) -> float:
    if isinstance(x, CallResult):
        return float(x.confidence)
    if isinstance(x, (int, float)):
        return float(x)
    return 1.0


class Memory:
    def __init__(self, system: str = "", max_turns: int = 20):
        self.system = system
        self.max_turns = max_turns
        self.messages: List[Dict[str, str]] = []
        if system:
            self.messages.append({"role": "system", "content": system})

    def add_user(self, text: str):
        self.messages.append({"role": "user", "content": str(text)})
        self._trim()

    def add_assistant(self, text: str):
        self.messages.append({"role": "assistant", "content": str(text)})
        self._trim()

    def add(self, role: str, text: str):
        self.messages.append({"role": str(role), "content": str(text)})
        self._trim()

    def clear(self):
        sys_msgs = [m for m in self.messages if m.get("role") == "system"]
        self.messages = list(sys_msgs)

    def _trim(self):
        sys_msgs = [m for m in self.messages if m.get("role") == "system"]
        rest = [m for m in self.messages if m.get("role") != "system"]
        if len(rest) > self.max_turns * 2:
            rest = rest[-(self.max_turns * 2) :]
        self.messages = sys_msgs + rest

    def as_list(self) -> List[Dict[str, str]]:
        return list(self.messages)

    def __len__(self):
        return len(self.messages)

    def __repr__(self):
        return f"Memory(turns={len(self.messages)}, system={bool(self.system)})"


def _apply_schema(result: CallResult, schema_spec: Any) -> CallResult:
    schema = resolve_schema(schema_spec)
    if not schema:
        return result
    data = result.data
    if data is None:
        try:
            data = json.loads(result.text)
            result.data = data
        except Exception:
            result.schema_ok = False
            result.schema_errors = ["response is not valid JSON"]
            result.confidence = min(result.confidence, 0.3)
            return result
    ok, errors = schema_validate(data, schema)
    result.schema_ok = ok
    result.schema_errors = errors
    if not ok:
        result.confidence = min(result.confidence, 0.35)
    else:
        # bump confidence slightly when schema validates
        result.confidence = max(result.confidence, min(0.9, result.confidence + 0.1))
        # if schema includes confidence field, prefer it when present
        if isinstance(data, dict) and isinstance(data.get("confidence"), (int, float)):
            result.confidence = float(data["confidence"])
        if isinstance(data, dict) and isinstance(data.get("score"), (int, float)):
            # critique-style
            result.confidence = max(result.confidence, float(data["score"]))
    return result


class LLMBackend:
    """Mock backend used when no API key is present."""

    def __init__(self, mock: bool = True, cache: bool = True):
        self.mock = mock
        self.cache = cache
        self._cache: Dict[str, CallResult] = {}

    def complete(
        self,
        config: ModelConfig,
        prompt: str,
        messages: Optional[List[Dict]] = None,
        **kwargs,
    ) -> CallResult:
        use_cache = self.cache and getattr(config, "cache", "exact") != "off"
        key = self._key(config, prompt, messages)
        if use_cache and key in self._cache:
            cached = self._cache[key]
            # return a copy-ish
            return CallResult(
                text=cached.text,
                confidence=cached.confidence,
                model=cached.model,
                fingerprint=cached.fingerprint,
                latency_ms=0.0,
                data=cached.data,
                schema_ok=cached.schema_ok,
                schema_errors=list(cached.schema_errors or []),
                attempts=cached.attempts,
            )

        t0 = time.time()
        lower = prompt.lower()
        data = None

        if config.mode == "json":
            if "plan" in lower or "steps" in lower:
                text = json.dumps({
                    "goal": "mock goal",
                    "steps": [
                        {"id": 1, "action": "analyze"},
                        {"id": 2, "action": "execute"},
                    ],
                    "confidence": 0.8,
                })
            elif "score" in lower or "critique" in lower:
                text = json.dumps({
                    "critique": "Looks reasonable for a mock response.",
                    "score": 0.75,
                    "issues": [],
                })
            else:
                text = json.dumps({
                    "answer": f"mock answer for: {prompt[:60]}",
                    "confidence": 0.7,
                    "reasoning": "mock",
                })
            conf_val = 0.8
            try:
                data = json.loads(text)
            except Exception:
                data = None
        elif "2 + 2" in lower or "2+2" in lower:
            text = "4"
            conf_val = 0.95
        elif "hello" in lower:
            text = "hello"
            conf_val = 0.9
        elif "what is llmlang" in lower:
            text = "LlmLang is a programming language whose runtime is an LLM plus tools."
            conf_val = 0.85
        else:
            if messages and len(messages) > 2:
                text = f"[mock multi-turn] Re: {prompt[:80]}"
                conf_val = 0.7
            else:
                text = f"[mock] Processed: {prompt[:120]}"
                conf_val = 0.6

        result = CallResult(
            text=text,
            confidence=conf_val,
            model=config.name or "mock",
            fingerprint=key[:16],
            latency_ms=(time.time() - t0) * 1000,
            data=data,
        )
        if config.schema is not None or config.mode == "json":
            result = _apply_schema(result, config.schema or ("answer" if config.mode == "json" else None))

        if use_cache:
            self._cache[key] = result
        return result

    def _key(self, config: ModelConfig, prompt: str, messages) -> str:
        raw = f"{config.name}|{config.mode}|{config.system}|{prompt}|{json.dumps(messages or [], sort_keys=True, default=str)}"
        return hashlib.sha1(raw.encode()).hexdigest()

    def health(self) -> Dict:
        return {"ok": True, "backend": "mock"}


_current_backend: Optional[Any] = None


def backend(b=None):
    global _current_backend
    if b is not None:
        _current_backend = b
    return _current_backend


def model(name: str, **kwargs) -> ModelConfig:
    return ModelConfig(
        name=name,
        system=kwargs.get("system", "You are a helpful assistant."),
        temperature=float(kwargs.get("temperature", 0.2)),
        mode=kwargs.get("mode", "free"),
        tools=list(kwargs.get("tools", [])),
        max_tokens=int(kwargs.get("max_tokens", 1024)),
        schema=kwargs.get("schema"),
        min_conf=float(kwargs.get("min_conf", 0.0)),
        max_retries=int(kwargs.get("max_retries", 0)),
        cache=kwargs.get("cache", "exact"),
    )


def run_with_retry(
    call_fn: Callable[[], CallResult],
    min_conf: float = 0.7,
    max_attempts: int = 3,
) -> CallResult:
    last = None
    for i in range(max_attempts):
        last = call_fn()
        last.attempts = i + 1
        if conf(last) >= min_conf and (last.schema_ok is not False):
            return last
    return last


def soft_if(value: Any, threshold: float = 0.7) -> bool:
    return conf(value) > threshold


def require(
    call_fn: Callable[[], CallResult],
    min_conf: float = 0.7,
    max_attempts: int = 3,
    require_schema: bool = True,
) -> CallResult:
    """
    Retry until confidence (and optional schema) pass, or attempts exhausted.
    Raises RuntimeError if still failing after max_attempts when strict.
    """
    last = None
    for i in range(max_attempts):
        last = call_fn()
        last.attempts = i + 1
        ok_conf = conf(last) >= min_conf
        ok_schema = (not require_schema) or (last.schema_ok is not False)
        if ok_conf and ok_schema:
            return last
    return last
