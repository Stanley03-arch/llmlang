"""
LlmLang — a programming language whose runtime is an LLM + tools.
"""

__version__ = "0.2.0"

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
from tools.registry import ToolResult, list_tools, call_tool

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
    "ToolResult",
    "list_tools",
    "call_tool",
]
