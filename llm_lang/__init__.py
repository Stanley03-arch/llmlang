"""
LlmLang — a programming language whose runtime is an LLM + tools.
"""

__version__ = "0.1.0"

from library.core import (
    CallResult,
    ModelConfig,
    LLMBackend,
    model,
    conf,
    backend,
)
from language.parser import parse, ParseError
from language.interpreter import Interpreter, run_source

__all__ = [
    "__version__",
    "CallResult",
    "ModelConfig",
    "LLMBackend",
    "model",
    "conf",
    "backend",
    "parse",
    "ParseError",
    "Interpreter",
    "run_source",
]
