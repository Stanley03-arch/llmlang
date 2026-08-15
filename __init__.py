"""
LlmLang top-level convenience imports.
Prefer: from llm_lang import ...  or  python -m llm_lang
"""
from llm_lang import (
    __version__,
    CallResult,
    ModelConfig,
    model,
    conf,
    parse,
    ParseError,
    Interpreter,
    run_source,
)

__all__ = [
    "__version__",
    "CallResult",
    "ModelConfig",
    "model",
    "conf",
    "parse",
    "ParseError",
    "Interpreter",
    "run_source",
]
