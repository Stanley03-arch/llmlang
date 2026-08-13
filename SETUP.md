# Setup

This repository hosts **LlmLang** — a programming language whose runtime is an LLM + tools.

## Quick start (when full source is present)

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang
python -m llm_lang --version
python -m llm_lang --demo
python -m llm_lang --eval
```

## Live models

```bash
export OPENAI_API_KEY=sk-...
python -m llm_lang --live
```

## Layout

- `language/` — parser, AST, interpreter
- `library/` — models, agents, tool executor, memory, pipelines
- `backends/` — mock + OpenAI-compatible
- `tools/` — ~60 tools
- `patterns/` — coding agent and strategies
- `examples/` — demos
- `tests/` — unit + capability eval

Version: 1.3.1  |  License: MIT
