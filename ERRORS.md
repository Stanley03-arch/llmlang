# Error handling in LlmLang

## Layers

| Layer | Mechanism | Example |
|-------|-----------|---------|
| **Parse** | `ParseError` | Unclosed `{`, bad model decl |
| **Runtime** | `RuntimeError_` | Undefined var, bad index |
| **Assert** | fails to exception | `assert x == 1, "msg"` |
| **try/catch** | recover in-language | `try { ... } catch err { ... }` |
| **Confidence** | soft branch (not exception) | `if conf(a) > 0.8` |
| **Tools** | `ToolCallResult.ok=False` | Missing args, unknown tool |
| **Pipeline** | stop on first failed step | `Pipeline(...).run()` |
| **Live backend** | `CallResult` with conf=0 | HTTP 401/timeout text |

## Language: try/catch

```ll
try {
  assert 1 == 2, "nope"
  print xs[99]
} catch err {
  print fmt("handled: {}", err)
}
```

See examples/error_handling.ll and examples/error_handling_demo.py
