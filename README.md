# LlmLang

**A programming language whose runtime is an LLM + tools.**

Version **0.2.0** — confidence control flow, tools, try/catch, parallel calls, collections.

> The computational model is *a large language model plus tools*, not a von Neumann machine with an LLM bolted on.

## Quick start

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang

python -m llm_lang --version
python -m llm_lang --demo
python -m llm_lang --eval
python -m llm_lang --tools

python -m llm_lang --run examples/hello.ll
python -m llm_lang --run examples/tools.ll
python -m llm_lang --run examples/agent_loop.ll
python -m llm_lang --run examples/parallel.ll
```

## Live models

```bash
export OPENAI_API_KEY=sk-...
python -m llm_lang --live
python -m llm_lang --run examples/hello.ll --backend openai
```

## Language features (v0.2)

| Feature | Example |
|---------|---------|
| Model decls | `model m { system: "..." temperature: 0.2 }` |
| Model calls | `r = m("prompt")` |
| Confidence CF | `if conf(r) > 0.8 { ... }` |
| Tools | `calc("2+2")`, `http_get(url)`, `now()`, … |
| try/catch | `try { ... } catch err { ... }` |
| parallel | `parallel { a = m1("x") b = m2("y") }` |
| Functions | `def f(x) { return x * 2 }` |
| Lists/dicts | `xs[0]`, `person["name"]`, `range(5)` |
| Ternary | `x > 0 ? "pos" : "neg"` |
| Import | `import "stdlib/prelude.ll"` |
| fmt / env | `fmt("hi {}", name)`, `env("HOME")` |

## Built-in tools

`calc`, `now`, `json_parse`, `json_stringify`, `http_get`, `read_file`, `write_file`, `list_dir`, `env`, `sleep`, `regex_search`, `upper`, `lower`, `len`

List them anytime: `python -m llm_lang --tools`

## Layout

```
llm_lang/       package + CLI
language/       parser, AST, interpreter
library/        CallResult, ModelConfig
backends/       mock + OpenAI-compatible
tools/          tool registry
examples/       .ll demos
stdlib/         growing standard library
```

## Docs

- [LANGUAGE.md](LANGUAGE.md) — syntax
- [VISION.md](VISION.md) — philosophy
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [LIVE.md](LIVE.md) — providers
- [ERRORS.md](ERRORS.md)

## License

MIT
