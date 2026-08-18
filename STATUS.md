# Upload status (LlmLang foundations)

Repo: https://github.com/Stanley03-arch/llmlang

## On GitHub

- Core language: parser, interpreter, AST (HardIf), transpile
- Bytecode VM + LANGUAGE_SPEC + FOUNDATION
- Weft-style: dense IR, static check, builder, typed ports, durable
- Tools, patterns, backends, efficiency, CLI flags

## Local may still be ahead on

- Full `__main__.py` wiring for every flag
- Full `parser.py` inlined hard_if (patch module covers GitHub)

## Verify

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang
PYTHONPATH=. python language/bytecode.py  # or
PYTHONPATH=. python -c "from language.bytecode import run_bytecode; print(run_bytecode('print 1+2*3').to_dict())"
```
