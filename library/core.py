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
import os
import re


@dataclass
class ModelConfig:
    name: str
    system: str = "You are a helpful assistant."
    temperature: float = 0.2
    mode: str = "free"  # free | json | tools
    tools: List[str] = field(default_factory=list)
    max_tokens: int = 1024


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
    data: Any = None  # parsed JSON when mode=json

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
        }

    def json(self) -> Any:
        if self.data is not None:
            return self.data
        try:
            return json.loads(self.text)
        except Exception:
            return None


def conf(x: Any) -> float:
    """Extract confidence from a CallResult or treat as 1.0 for plain values."""
    if isinstance(x, CallResult):
        return float(x.confidence)
    if isinstance(x, (int, float)):
        return float(x)
    return 1.0


class Memory:
    """Simple multi-turn conversation memory."""

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
        # keep system + last max_turns*2 messages
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


class LLMBackend:
    """Simple mock backend used when no API key is present."""

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
        key = self._key(config, prompt, messages)
        if self.cache and key in self._cache:
            return self._cache[key]

        t0 = time.time()
        lower = prompt.lower()
        data = None

        if config.mode == "json":
            # structured mock responses
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
            # multi-turn awareness
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
        if self.cache:
            self._cache[key] = result
        return result

    def _key(self, config: ModelConfig, prompt: str, messages) -> str:
        raw = f"{config.name}|{config.mode}|{config.system}|{prompt}|{json.dumps(messages or [], sort_keys=True, default=str)}"
        return hashlib.sha1(raw.encode()).hexdigest()

    def health(self) -> Dict:
        return {"ok": True, "backend": "mock"}


# Global backend holder
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
    )


def run_with_retry(
    call_fn: Callable[[], CallResult],
    min_conf: float = 0.7,
    max_attempts: int = 3,
) -> CallResult:
    """Retry a model call until confidence >= min_conf or attempts exhausted."""
    last = None
    for _ in range(max_attempts):
        last = call_fn()
        if conf(last) >= min_conf:
            return last
    return last


def soft_if(value: Any, threshold: float = 0.7) -> bool:
    """True when conf(value) > threshold."""
    return conf(value) > threshold
