# Power vs Python — honest map

| Workload | Faster than Python? | How |
|----------|---------------------|-----|
| Pure numeric loops | **Yes** | Go codegen (`--beat`) |
| Local tools (search, stats, files) | **Competitive / can be** | Go `lltools` daemon (`--go-tools`) |
| LLM API calls | **No language can be** | Bound by network + model |
| Full agent loop | **Often fewer tokens** | Dense IR; tools in Go |

## Why LLM is not "faster in Go"

The model API takes hundreds of ms to seconds. Switching the HTTP client from Python to Go does not beat that. Same keys, same models, same latency.

What we *did* move off Python:

1. **Pure compute** → Go native binary  
2. **Local tools** → Go daemon (parallel, no CPython in the tool body)  
3. **Agent source density** → fewer tokens than Python glue  

## Commands

```bash
python __main__.py --beat --n 500000   # pure loops beat CPython
python __main__.py --go-tools          # local tools via Go
python __main__.py --go-tools --daemon # ensure daemon up
```

## Bottom line

- **Everything that is local pure work:** can beat Python.  
- **Everything that waits on an LLM API:** cannot beat the API, in any language.
