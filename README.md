# LlmLang

**A programming language whose runtime is an LLM + tools.**

Version **0.3.0** — JSON mode, multi-turn memory, plan/critic agents, break/continue, 20+ tools.

> The computational model is *a large language model plus tools*, not a von Neumann machine with an LLM bolted on.

## Quick start

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang

python -m llm_lang --version
python -m llm_lang --demo
python -m llm_lang --tools

python -m llm_lang --run examples/memory.ll
python -m llm_lang --run examples/json_mode.ll
python -m llm_lang --run examples/plan_critic.ll
python -m llm_lang --run examples/agent_loop.ll
```

## Live models

```bash
export OPENAI_API_KEY=sk-...
python -m llm_lang --live
```

## Highlights (v0.3)

| Feature | Example |
|---------|---------|
| JSON mode | `model m { mode: "json" }` then `json(result)` |
| Memory / chat | `mem = memory("...")` / `chat("m", "hi", mem)` |
| plan / critic | `plan("m", goal)` / `critic("m", text)` |
| break / continue | inside `for` / `while` |
| Tools | `calc`, `http_get`, `split`, `join`, `replace`, … |
| Confidence CF | `if conf(r) > 0.8 { ... }` |
| parallel | concurrent model calls |
| try/catch | recoverable errors |

## Built-in tools

`calc`, `now`, `json_parse`, `json_stringify`, `http_get`, `read_file`, `write_file`, `append_file`, `list_dir`, `env`, `sleep`, `regex_search`, `upper`, `lower`, `split`, `join`, `contains`, `starts_with`, `strip`, `replace`, `len`

## License

MIT
