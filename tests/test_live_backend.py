#!/usr/bin/env python3
"""Live backend unit tests with a fake HTTP layer (no real API key needed)."""
from __future__ import annotations
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status
    def read(self):
        return json.dumps(self._payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False

class TestLiveBackend(unittest.TestCase):
    def test_complete_text(self):
        payload = {
            "choices": [{"message": {"content": "pong"}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 12},
        }
        def fake_urlopen(req, timeout=120):
            return FakeResponse(payload)
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            with mock.patch("urllib.request.urlopen", fake_urlopen):
                from backends.openai_compat import OpenAICompatBackend
                from library.core import ModelConfig
                b = OpenAICompatBackend(api_key="test-key", cache=False)
                r = b.complete(ModelConfig(name="t"), "ping")
                self.assertEqual(r.text, "pong")
                self.assertTrue(r.final)
                self.assertGreaterEqual(r.confidence, 0.8)

    def test_complete_tools(self):
        payload = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "now", "arguments": "{}"},
                    }],
                },
                "finish_reason": "tool_calls",
            }],
            "usage": {"total_tokens": 20},
        }
        def fake_urlopen(req, timeout=120):
            return FakeResponse(payload)
        with mock.patch("urllib.request.urlopen", fake_urlopen):
            from backends.openai_compat import OpenAICompatBackend
            from library.core import ModelConfig, DecodeMode
            b = OpenAICompatBackend(api_key="test-key", cache=False)
            r = b.complete(ModelConfig(name="t", mode=DecodeMode.TOOLS, tools=["now"]), "what time is it")
            self.assertFalse(r.final)
            self.assertEqual(len(r.tool_calls), 1)
            self.assertEqual(r.tool_calls[0]["function"]["name"], "now")

    def test_probe_without_key(self):
        env = {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "LLM_API_KEY")}
        with mock.patch.dict(os.environ, env, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("LLM_API_KEY", None)
            from backends import probe_backend
            info = probe_backend()
            self.assertEqual(info["selected"], "mock")

    def test_get_backend_auto_mock(self):
        with mock.patch.dict(os.environ, {"LLM_BACKEND": "mock"}, clear=False):
            from backends import get_backend
            b = get_backend("mock")
            self.assertTrue(getattr(b, "mock", False) or b.__class__.__name__ == "LLMBackend")

if __name__ == "__main__":
    unittest.main()
