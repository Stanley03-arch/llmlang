# LlmLang

**A programming language whose runtime is an LLM + tools.**

Version **0.1.0** — confidence-based control flow, model declarations, first-class `CallResult`.

> The computational model is *a large language model plus tools*, not a von Neumann machine with an LLM bolted on.

## Quick start

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang

# works with zero API keys (uses deterministic mock backend)
python -m llm_lang --version
python -m llm_lang --demo
python -m llm_lang --eval

# run example programs
python -m llm_lang --run examples/hello.ll
python -m llm_lang --run examples/math.ll
python -m llm_lang --run examples/functions.ll
```

## Live models

Any OpenAI-compatible endpoint works (OpenAI, Groq, Ollama, vLLM, …):

```bash
export OPENAI_API_KEY=sk-...
# optional:
# export OPENAI_MODEL=gpt-4o-mini
# export OPENAI_BASE_URL=https://api.openai.com/v1

python -m llm_lang --live
python -m llm_lang --run examples/hello.ll --backend openai
```

## Language sketch

```ll
model helper {
  system: "You are a helpful assistant. Be concise."
  temperature: 0.2
  mode: "free"
}

result = helper("What is 2 + 2?")
print result
print conf(result)

if conf(result) > 0.85 {
  print "accepted"
} else {
  print "low confidence — reconsider"
}
```

### Core ideas

- A `CallResult` is a first-class value: **text + confidence + provenance**.
- `if conf(x) > θ` is real control flow.
- Models are declared, not scattered as magic strings.
- Designed so a multi-step tool-using agent can be expressed more clearly than typical framework soup.

## Layout

```
llm_lang/          package + CLI
language/          parser, AST, interpreter
library/           CallResult, ModelConfig, core helpers
backends/          mock + OpenAI-compatible
examples/          .ll demos
stdlib/            prelude (growing)
```

## Docs

- [LANGUAGE.md](LANGUAGE.md) — syntax notes
- [VISION.md](VISION.md) — design philosophy
- [ARCHITECTURE.md](ARCHITECTURE.md) — hosted DSL overview
- [LIVE.md](LIVE.md) — providers
- [ERRORS.md](ERRORS.md) — error model

## Status

This is an early but **runnable** implementation of the vision. The mock backend lets you develop and test language features without any API key. Live calls work against any OpenAI-compatible Chat Completions API.

Next directions: richer tool system, `parallel {}`, structured JSON mode, better error messages, more stdlib.

## License

MIT
