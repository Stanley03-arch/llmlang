"""
LlmLang — a programming language whose runtime is an LLM + tools.
"""

__version__ = "0.3.0"

from library.core import (
    CallResult,
    ModelConfig,
    Memory,
    LLMBackend,
    model,
    conf,
    backend,
    run_with_retry,
    soft_if,
)
from library.agents import chat, plan, critic, run_agent
from language.parser import parse, ParseError
from language.interpreter import Interpreter, run_source
from tools.registry import ToolResult, list_tools, call_tool

__all__ = [
    "__version__",
    "CallResult",
    "ModelConfig",
    "Memory",
    "LLMBackend",
    "model",
    "conf",
    "backend",
    "run_with_retry",
    "soft_if",
    "chat",
    "plan",
    "critic",
    "run_agent",
    "parse",
    "ParseError",
    "Interpreter",
    "run_source",
    "ToolResult",
    "list_tools",
    "call_tool",
]
