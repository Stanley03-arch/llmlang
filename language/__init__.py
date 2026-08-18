"""LlmLang language package: parser, AST, interpreter, bytecode VM."""

try:
    from language import hard_if_support  # noqa: F401 — register pure if
except Exception:
    pass
