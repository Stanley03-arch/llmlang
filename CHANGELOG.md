# Changelog

## 0.2.0 — 2026-08-15

- Tool system with 14 built-ins (calc, http_get, files, json, …)
- `try { } catch err { }`
- `parallel { }` concurrent model calls
- Lists, dicts, indexing, index assignment
- Ternary `cond ? a : b`
- `fmt`, `range`, `env`, `type`, `keys`, `values`
- `import "path.ll"`
- New examples: tools, try_catch, parallel, agent_loop, collections
- CLI `--tools`

## 0.1.0 — 2026-08-15

- Initial runnable implementation
- Parser + AST + interpreter
- CallResult + confidence control flow
- Mock + OpenAI-compatible backends
- CLI and basic examples
