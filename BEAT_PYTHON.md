# How LlmLang beats Python (Weft-style)

**Not** faster CPU loops than CPython.  
**Yes** faster *AI system construction* than naive Python agent glue.

## Levers (same family as Weft)

1. **Dense IR** — `T search_code query=X | T project_stats | L "summarize"`
2. **Short .ll** — model + tools in ~6 lines vs ~50–90 lines of OpenAI tool-loop Python
3. **Static check** — unknown tools / architecture issues before runtime
4. **Builder** — intent → dense → check → run tools without hand-written plumbing

## Measured density (estimate)

| Form | Est. tokens |
|------|-------------|
| Python OpenAI tool-loop glue | ~200 |
| LlmLang `.ll` agent | ~35 (**~6× smaller**) |
| Dense IR one-liner | ~20 (**~10× smaller**) |

## Commands

```bash
python __main__.py --build "Search for CallResult and get project stats"
python __main__.py --build --compare
python __main__.py --check examples/hello.ll
python examples/beat_python_demo.py
```

## Roadmap toward Weft-class

- [x] Dense IR + runner
- [x] Static tool/var checks
- [x] Builder heuristic
- [ ] Typed ports between steps
- [ ] Graph view
- [ ] Durable execution
- [ ] Rust compiler core (optional)
