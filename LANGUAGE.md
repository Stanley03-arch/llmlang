# LlmLang Language Reference

LlmLang is a domain-specific language for programs whose runtime is an LLM + tools.

## Models

```ll
model name {
  system: "role instructions"
  temperature: 0.2
  mode: "free" | "json" | "tools"
}
result = name("your prompt here")
if conf(result) > 0.85 {
  print "accepted"
}
```

## Features (v0.1)

- Model declarations
- Model calls that return a first-class `CallResult`
- `conf(x)` for confidence-based control flow
- `if` / `else`, `while`, `for … in`
- User-defined `def` functions + `return`
- `print`, `assert`
- Literals, lists, arithmetic, comparison, `and` / `or` / `not`
- Comments with `#`

## Coming soon

- `parallel { … }`
- Richer tool calling
- Structured JSON mode
- Import / modules
- Better error messages and diagnostics

See VISION.md and ARCHITECTURE.md for design.
