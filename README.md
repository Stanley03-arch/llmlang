# LlmLang

**A programming language whose runtime is an LLM + tools.**

Version **1.6.0** — confidence-based control flow, tool agents, parallel multi-task, AI-speed prefetch/cache.

## Quick start

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang
python -m llm_lang --version
python -m llm_lang --demo
python -m llm_lang --eval
python -m llm_lang --ai-speed
python -m llm_lang --pev "Search for CallResult"
```

## Live models

```bash
export OPENAI_API_KEY=sk-...
python -m llm_lang --live
```

## Docs

- LANGUAGE.md — syntax
- ARCHITECTURE.md — design
- LIVE.md — providers
- ERRORS.md — error handling
- VISION.md — philosophy

## Layout

```
language/   parser, AST, interpreter
library/    agents, tools executor, memory, workflows, efficiency
backends/   mock + OpenAI-compatible
tools/      ~57 tools
patterns/   coding agent, PEV, strategies
examples/   demos
tests/      unit + capability eval
```

License: MIT
