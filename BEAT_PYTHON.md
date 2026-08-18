# How LlmLang beats Python (Weft-style)

**Not** faster CPU loops than CPython.  
**Yes** faster *AI system construction* than naive Python agent glue.

## Levers

1. **Dense IR** — `T search_code query=X | T project_stats | L "summarize"`
2. **Short .ll** — model + tools in ~6 lines vs ~50–90 lines of Python tool-loop glue
3. **Static check** — unknown tools before runtime
4. **Builder** — intent → dense → check → run
5. **Typed ports** — step I/O types + cycle detection
6. **Graph view** — Mermaid from dense pipelines
7. **Durable runs** — JSONL journal, skip completed steps on resume

## Density (estimate)

| Form | Est. tokens |
|------|-------------|
| Python OpenAI tool-loop glue | ~200 |
| LlmLang `.ll` agent | ~35 (~6×) |
| Dense IR one-liner | ~20 (~10×) |

## Commands

```bash
python __main__.py --build --compare
python __main__.py --build "Search for CallResult and get project stats"
python __main__.py --check examples/hello.ll
python __main__.py --graph --demo
python __main__.py --graph "project stats and search CallResult"
python __main__.py --durable "what time is it"
python __main__.py --durable --list
python examples/beat_python_demo.py
python examples/typed_graph_demo.py
```

## Roadmap

- [x] Dense IR + runner
- [x] Static tool/var checks
- [x] Builder heuristic
- [x] Typed ports between steps
- [x] Graph view (Mermaid)
- [x] Durable step journal
- [ ] Full dual code/graph editor
- [ ] Restate-class durable engine
- [ ] Rust compiler core (optional)
