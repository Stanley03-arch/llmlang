#!/usr/bin/env python3
"""Minimal but meaningful tests for LlmLang."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from language.parser import parse, ParseError
from language.interpreter import run_source, Interpreter
from library.core import LLMBackend, CallResult


def test_lists_and_arith():
    src = """
    xs = [1, 2, 3, 4]
    print len(xs)
    print xs[0] + xs[3]
    """
    interp = run_source(src)
    assert "4" in interp.output[0]
    assert "5" in interp.output[1]
    print("OK test_lists_and_arith")


def test_function():
    src = """
    def double(x) {
      return x * 2
    }
    print double(21)
    """
    interp = run_source(src)
    assert "42" in interp.output[0]
    print("OK test_function")


def test_parallel():
    src = """
    parallel {
      a = 10 + 1
      b = 20 + 2
    }
    print a
    print b
    """
    interp = run_source(src)
    assert "11" in interp.output[0]
    assert "22" in interp.output[1]
    print("OK test_parallel")


def test_model_and_conf():
    src = """
    model m {
      system: "test"
      temperature: 0.1
    }
    x = m("hello")
    print conf(x)
    """
    interp = run_source(src)
    val = float(interp.output[0])
    assert 0.0 <= val <= 1.0
    print("OK test_model_and_conf")


def test_soft_if():
    src = """
    model m { system: "t" }
    x = m("hi")
    if conf(x) > 0.1 {
      print "high"
    } else {
      print "low"
    }
    """
    interp = run_source(src)
    assert interp.output[-1] in ("high", "low")
    print("OK test_soft_if")


def test_parse_error_message():
    try:
        parse("model {")
        assert False, "should have raised"
    except ParseError as e:
        assert "Expected" in str(e)
        print("OK test_parse_error_message")


def test_cache():
    backend = LLMBackend(mock=True, cache=True)
    from library.core import ModelConfig, DecodeMode
    cfg = ModelConfig(name="t", mode=DecodeMode.FREE)
    r1 = backend.complete(cfg, "same prompt every time")
    r2 = backend.complete(cfg, "same prompt every time")
    assert r1.fingerprint == r2.fingerprint
    assert r2.latency_ms == 0.0
    stats = backend.cache_stats()
    assert stats["entries"] >= 1
    print("OK test_cache")


def test_structured():
    src = """
    model m {
      system: "json only"
      mode: "json"
      schema: "answer"
    }
    x = m("hi")
    print x
    """
    interp = run_source(src)
    import json
    data = json.loads(interp.output[0].split("  (conf=")[0])
    assert "answer" in data
    assert "confidence" in data
    print("OK test_structured")


def test_effects():
    from library.core import ModelConfig, DecodeMode, Effect, EffectSet, effects_of_config, check_effects
    cfg = ModelConfig(name="a", mode=DecodeMode.TOOLS, tools=["calculator"])
    es = effects_of_config(cfg)
    assert Effect.TOOLS in es.effects
    assert Effect.MODEL in es.effects
    try:
        check_effects(cfg, EffectSet())
        assert False
    except PermissionError:
        pass
    print("OK test_effects")


if __name__ == "__main__":
    test_lists_and_arith()
    test_function()
    test_parallel()
    test_model_and_conf()
    test_soft_if()
    test_parse_error_message()
    test_cache()
    test_structured()
    test_effects()
    print("\nAll tests passed.")
