# LlmLang

**A programming language whose runtime is an LLM + tools.**

Version **0.4.0** — schema validation, confidence retries, execution traces.

> Built to outperform agent *frameworks* on clarity, cost, and reliability — not to replace C or Python for general compute.

## Quick start

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang

python -m llm_lang --version
python -m llm_lang --demo
python -m llm_lang --run examples/schema_mode.ll --trace
python -m llm_lang --run examples/traced_agent.ll --trace agent.trace.json
```

## What makes v0.4 different

### Schema-validated JSON mode
```ll
model extractor {
  mode: "json"
  schema: "answer"   # or "plan" | "critique"
  min_conf: 0.6
  max_retries: 2
}
r = extractor("Capital of Kenya?")
print schema_ok(r), json(r)
```

### Confidence as a runtime contract
```ll
model careful {
  min_conf: 0.7
  max_retries: 3
}
r = careful("...")
checked = require(r, 0.7, 1)
```

### Execution traces
```bash
python -m llm_lang --run examples/traced_agent.ll --trace
# writes examples/traced_agent.ll.trace.json
```
Every model/tool call is logged with inputs, outputs, confidence, latency.

## Feature map

| Area | Features |
|------|----------|
| Models | free / json mode, schema, min_conf, max_retries, cache |
| Control | if/else, while, for, break/continue, parallel, try/catch |
| Confidence | conf(x), soft_if, require |
| Agents | memory, chat, plan, critic |
| Tools | 20+ builtins (calc, http, files, strings, json, …) |
| Observability | Trace, --trace, summary |

## License

MIT
