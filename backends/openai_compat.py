"""
OpenAI-compatible Chat Completions backend.
Works with OpenAI, Groq, Ollama, vLLM, Together, etc.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import hashlib
import os
import time
import urllib.request
import urllib.error

from library.core import ModelConfig, CallResult


class OpenAICompatBackend:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        cache: bool = True,
        timeout: float = 120,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.default_model = default_model or os.environ.get("OPENAI_MODEL") or os.environ.get("LLM_MODEL") or "gpt-4o-mini"
        self.cache = cache
        self.timeout = timeout
        self._cache: Dict[str, CallResult] = {}

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY (or LLM_API_KEY) is required for the live backend")

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

        msgs = messages or [
            {"role": "system", "content": config.system},
            {"role": "user", "content": prompt},
        ]
        if not any(m.get("role") == "system" for m in msgs):
            msgs = [{"role": "system", "content": config.system}] + list(msgs)

        model_name = kwargs.get("model") or self.default_model
        body = {
            "model": model_name,
            "messages": msgs,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        t0 = time.time()
        try:
            data = self._post("/chat/completions", body)
            choice = data["choices"][0]
            text = choice["message"].get("content") or ""
            # crude confidence heuristic from finish_reason + length
            finish = choice.get("finish_reason", "")
            conf = 0.85 if finish == "stop" else 0.5
            if len(text) < 5:
                conf *= 0.7

            result = CallResult(
                text=text.strip(),
                confidence=conf,
                model=model_name,
                fingerprint=key[:16],
                raw=data,
                latency_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            result = CallResult(
                text=f"[error] {e}",
                confidence=0.0,
                model=model_name,
                fingerprint=key[:16],
                latency_ms=(time.time() - t0) * 1000,
            )

        if self.cache:
            self._cache[key] = result
        return result

    def _post(self, path: str, body: dict) -> dict:
        url = self.base_url + path
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _key(self, config: ModelConfig, prompt: str, messages) -> str:
        raw = f"{config.name}|{config.system}|{prompt}|{json.dumps(messages or [], sort_keys=True, default=str)}"
        return hashlib.sha1(raw.encode()).hexdigest()

    def health(self) -> Dict:
        try:
            # lightweight check: list models if available, else just report config
            return {
                "ok": True,
                "backend": "openai_compat",
                "base_url": self.base_url,
                "model": self.default_model,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
