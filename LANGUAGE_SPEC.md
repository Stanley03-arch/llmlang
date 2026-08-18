# LlmLang Language Specification (v0.1 foundation)

ABC-layer contract: small, orthogonal, implementable.
AI features (models, tools, confidence) are **effects** on a deterministic core.

## Design goals

1. Readable by humans and models
2. Deterministic pure core (no hidden LLM in arithmetic/control)
3. Effects are marked (model, tools, py, IO)
4. Compile-checkable
5. Two paths: tree-walk interpreter (full) + **bytecode VM** (pure subset)

## Values

Number, String, Bool, Null, List, Dict, Closure, ModelRef, EffectResult

## Pure VM subset (v0.1)

- Literals, names, `+ - * / % == != < <= > >= and or`, unary `- not len`
- Lists + index read
- `assign`, `print`, `if expr { } else { }`, `while expr { }`

**Not in VM v0.1:** model, tools, parallel, py, conf soft-if, dicts, functions, for, try

## Bytecode (stack machine)

LOAD_CONST, LOAD_NAME, STORE_NAME, BINARY_*, UNARY_*, BUILD_LIST, GET_ITEM,
JUMP, JUMP_IF_FALSE, PRINT, POP, RETURN

## Pipeline

```
source → parse → AST → [static_check] → compile_bytecode → VM.execute
# or AST → tree-walk interpreter (full language)
```

## Versioning

- 0.1 — spec + pure VM slice
- 0.2 — functions + locals in VM
- 0.3 — dicts + for-in
- 1.0 — effects formalized; shared value model
