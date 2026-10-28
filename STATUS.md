# Status — LlmLang

Repo: https://github.com/Stanley03-arch/llmlang

## On GitHub

- Core language: parser, interpreter, AST, transpile
- Bytecode VM + LANGUAGE_SPEC + FOUNDATION docs
- Schema-validated JSON mode, confidence contracts, execution traces
- Tools, patterns, backends, efficiency helpers, CLI flags

## Quick verify

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang

PYTHONPATH=. python -m llm_lang --version
PYTHONPATH=. python -m llm_lang --demo
PYTHONPATH=. python -c "from language.bytecode import run_bytecode; print(run_bytecode('print 1+2*3').to_dict())"
```

## Current focus

- Keep schema + confidence + trace path solid
- Improve docs and examples for new contributors
- Optional: expand hard-if / full CLI flag coverage
