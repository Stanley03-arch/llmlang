"""
Backend factory for LlmLang.

  from backends import get_backend, probe_backend
  backend = get_backend("auto")     # live if key else mock
  backend = get_backend("openai")
  backend = get_backend("mock")
"""

from __future__ import annotations
from typing import Any, Dict
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_backend(name: str = None, **kwargs) -> Any:
    name = (name or os.environ.get("LLM_BACKEND") or "auto").lower()

    if name == "auto":
        if os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY"):
            name = "openai"
        else:
            name = "mock"

    if name == "mock":
        from library.core import LLMBackend
        return LLMBackend(mock=True, cache=kwargs.get("cache", True))

    if name in ("openai", "openai_compat", "live"):
        from backends.openai_compat import OpenAICompatBackend
        return OpenAICompatBackend(
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"),
            default_model=kwargs.get("model") or kwargs.get("default_model"),
            cache=kwargs.get("cache", True),
            timeout=kwargs.get("timeout", 120),
            strict_schema=kwargs.get("strict_schema", False),
        )

    raise ValueError(f"Unknown backend: {name}. Use mock|openai|auto.")


def probe_backend() -> Dict[str, Any]:
    """Report which backend would be selected and optional health."""
    has_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY"))
    requested = (os.environ.get("LLM_BACKEND") or "auto").lower()
    selected = "openai" if (requested in ("openai", "live", "openai_compat") or (requested == "auto" and has_key)) else "mock"
    if requested == "mock":
        selected = "mock"
    info = {
        "requested": requested,
        "selected": selected,
        "has_api_key": has_key,
        "base_url": os.environ.get("OPENAI_BASE_URL") or os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1",
        "model": os.environ.get("OPENAI_MODEL") or os.environ.get("LLM_MODEL") or "gpt-4o-mini",
    }
    if selected == "openai" and has_key:
        try:
            b = get_backend("openai")
            info["health"] = b.health()
        except Exception as e:
            info["health"] = {"ok": False, "error": str(e)}
    return info
