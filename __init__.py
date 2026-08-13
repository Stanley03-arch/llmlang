"""
LlmLang — a programming language (and companion library) for LLMs.
"""

__version__ = "1.3.1"

import os, sys
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from library.core import (
    model,
    critic,
    plan,
    soft_if,
    run_with_retry,
    run_agent,
    CallResult,
    LLMBackend,
    backend,
)
from language.interpreter import run_source, Interpreter
from language.parser import parse, ParseError

__all__ = [
    "model",
    "critic",
    "plan",
    "soft_if",
    "run_with_retry",
    "run_agent",
    "CallResult",
    "LLMBackend",
    "backend",
    "run_source",
    "Interpreter",
    "parse",
    "ParseError",
]
