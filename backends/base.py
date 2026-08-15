"""
Backend protocol and shared helpers.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol
import json
import hashlib

from library.core import ModelConfig, CallResult


class Backend(Protocol):
    def complete(
        self,
        config: ModelConfig,
        prompt: str,
        messages: Optional[List[Dict]] = None,
        **kwargs,
    ) -> CallResult: ...


def fingerprint(config: ModelConfig, prompt: str, messages: List[Dict]) -> str:
    key = config.name + "|" + prompt + "|" + json.dumps(messages or [], sort_keys=True, default=str)
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def messages_from_prompt(config: ModelConfig, prompt: str, messages: Optional[List[Dict]]) -> List[Dict]:
    if messages:
        if not any(m.get("role") == "system" for m in messages):
            return [{"role": "system", "content": config.system}] + list(messages)
        return list(messages)
    return [
        {"role": "system", "content": config.system},
        {"role": "user", "content": prompt},
    ]
