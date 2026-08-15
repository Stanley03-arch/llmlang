# Changelog

## 0.4.0 — 2026-08-16

- Schema validation for JSON mode (`schema: "answer"|"plan"|"critique"`)
- Model-level `min_conf` + `max_retries` with automatic re-calls
- `require(result, min_conf, attempts)` and `schema_ok(result)`
- Execution `Trace` for every model/tool call
- CLI `--trace [path]` writes JSON audit log
- Examples: require_retry, schema_mode, traced_agent

## 0.3.0 — 2026-08-15

- JSON mode, memory/chat, plan/critic, break/continue

## 0.2.0 — 2026-08-15

- Tools, try/catch, parallel, collections

## 0.1.0 — 2026-08-15

- Initial runnable implementation
