"""
OpenAI-compatible Chat Completions backend with JSON mode + schema validation.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import hashlib
import os
import time
import urllib.request

from library.core import ModelConfig, CallResult, _apply_schema


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
        use_cache = self.cache and getattr(config, "cache", "exact") != "off"
        key = self._key(config, prompt, messages)
        if use_cache and key in self._cache:
            c = self._cache[key]
            return CallResult(
                text=c.text, confidence=c.confidence, model=c.model,
                fingerprint=c.fingerprint, latency_ms=0.0, data=c.data,
                schema_ok=c.schema_ok, schema_errors=list(c.schema_errors or []),
            )

        msgs = messages or [
            {"role": "system", "content": config.system},
            {"role": "user", "content": prompt},
        ]
        if not any(m.get("role") == "system" for m in msgs):
            msgs = [{"role": "system", "content": config.system}] + list(msgs)

        model_name = kwargs.get("model") or self.default_model
        body: Dict[str, Any] = {
            "model": model_name,
            "messages": msgs,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        if config.mode == "json" or config.schema is not None:
            body["response_format"] = {"type": "json_object"}
            if msgs and msgs[0].get("role") == "system":
                if "json" not in msgs[0]["content"].lower():
                    msgs[0] = {
                        "role": "system",
                        "content": msgs[0]["content"] + "\nAlways respond with valid JSON.",
                    }
                    body["messages"] = msgs

        t0 = time.time()
        data_parsed = None
        try:
            data = self._post("/chat/completions", body)
            choice = data["choices"][0]
            text = choice["message"].get("content") or ""
            finish = choice.get("finish_reason", "")
            conf = 0.85 if finish == "stop" else 0.5
            if len(text) < 5:
                conf *= 0.7

            if config.mode == "json" or config.schema is not None:
                try:
                    data_parsed = json.loads(text)
                    conf = max(conf, 0.75)
                except Exception:
                    conf = min(conf, 0.4)

            result = CallResult(
                text=text.strip(),
                confidence=conf,
                model=model_name,
                fingerprint=key[:16],
                raw=data,
                latency_ms=(time.time() - t0) * 1000,
                data=data_parsed,
            )
            if config.schema is not None:
                result = _apply_schema(result, config.schema)
            elif config.mode == "json":
                result = _apply_schema(result, "answer")
        except Exception as e:
            result = CallResult(
                text=f"[error] {e}",
                confidence=0.0,
                model=model_name,
                fingerprint=key[:16],
                latency_ms=(time.time() - t0) * 1000,
            )

        if use_cache and result.confidence > 0:
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
        raw = f"{config.name}|{config.mode}|{config.system}|{prompt}|{json.dumps(messages or [], sort_keys=True, default=str)}"
        return hashlib.sha1(raw.encode()).hexdigest()

    def health(self) -> Dict:
        return {
            "ok": True,
            "backend": "openai_compat",
            "base_url": self.base_url,
            "model": self.default_model,
        }
