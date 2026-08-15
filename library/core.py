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
        }


def conf(x: Any) -> float:
    """Extract confidence from a CallResult or treat as 1.0 for plain values."""
    if isinstance(x, CallResult):
        return float(x.confidence)
    if isinstance(x, (int, float)):
        return float(x)
    return 1.0


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
        # Very simple deterministic mock responses
        lower = prompt.lower()
        if "2 + 2" in lower or "2+2" in lower:
            text = "4"
            conf_val = 0.95
        elif "hello" in lower:
            text = "hello"
            conf_val = 0.9
        elif "what is llmlang" in lower:
            text = "LlmLang is a programming language whose runtime is an LLM plus tools."
            conf_val = 0.85
        else:
            text = f"[mock] Processed: {prompt[:120]}"
            conf_val = 0.6

        result = CallResult(
            text=text,
            confidence=conf_val,
            model=config.name or "mock",
            fingerprint=key[:16],
            latency_ms=(time.time() - t0) * 1000,
        )
        if self.cache:
            self._cache[key] = result
        return result

    def _key(self, config: ModelConfig, prompt: str, messages) -> str:
        raw = f"{config.name}|{config.system}|{prompt}|{json.dumps(messages or [], sort_keys=True, default=str)}"
        return hashlib.sha1(raw.encode()).hexdigest()

    def health(self) -> Dict:
        return {"ok": True, "backend": "mock"}


# Global backend holder (set by interpreter / CLI)
_current_backend: Optional[Any] = None


def backend(b=None):
    global _current_backend
    if b is not None:
        _current_backend = b
    return _current_backend


def model(name: str, **kwargs) -> ModelConfig:
    """Create a ModelConfig (also used from Python side)."""
    return ModelConfig(
        name=name,
        system=kwargs.get("system", "You are a helpful assistant."),
        temperature=float(kwargs.get("temperature", 0.2)),
        mode=kwargs.get("mode", "free"),
        tools=list(kwargs.get("tools", [])),
        max_tokens=int(kwargs.get("max_tokens", 1024)),
    )
