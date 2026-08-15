# LlmLang Language Reference (v0.4)

## Reliable models

```ll
model m {
  system: "..."
  mode: "json"
  schema: "answer"    # answer | plan | critique
  min_conf: 0.7
  max_retries: 2
  cache: "exact"      # exact | off
}
r = m("prompt")
print conf(r), schema_ok(r), json(r)
checked = require(r, 0.7, 1)
```

## Tracing

```bash
python -m llm_lang --run program.ll --trace
python -m llm_lang --run program.ll --trace out.trace.json
```

See VISION.md and examples/ for more.
