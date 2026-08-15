# Setup

This repository hosts **LlmLang** — a programming language whose runtime is an LLM + tools.

## Quick start

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang
python -m llm_lang --version
python -m llm_lang --demo
python -m llm_lang --eval
python -m llm_lang --run examples/hello.ll
```

## Live models

```bash
export OPENAI_API_KEY=sk-...
python -m llm_lang --live
```

## Layout

- `llm_lang/` — package + CLI entrypoint
- `language/` — parser, AST, interpreter
- `library/` — CallResult, ModelConfig, core helpers
- `backends/` — mock + OpenAI-compatible
- `examples/` — demos
- `stdlib/` — growing standard library

Version: 0.1.0  |  License: MIT
