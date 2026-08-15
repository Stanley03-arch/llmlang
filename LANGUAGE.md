# LlmLang Language Reference

LlmLang is a domain-specific language for programs whose runtime is an LLM + tools.

## Models

```ll
model name {
  system: "role instructions"
  temperature: 0.2
  mode: "free" | "json" | "tools"
  tools: {"tool_a" "tool_b"}
}
result = m("your prompt here")
if conf(result) > 0.85 {
  print "accepted"
}
```

## Features

Functions, lists, dicts, range, index assign, for/while, parallel, import, assert, and/or/in, ternary, fmt/env, try/catch.

See VISION.md and ARCHITECTURE.md for design.
