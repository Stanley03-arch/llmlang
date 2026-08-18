# Power without only relying on Python

## Layers

| Layer | Runtime | Beats Python at? |
|-------|---------|------------------|
| Token / agent surface | Source density | **Yes** vs agent glue |
| Pure logic | **Go VM** (`runtime/llvm.go`) | Independence; speed still catching CPython |
| Full agents | Python + tools | Parallel tools, cache, PEV |

## Non-Python path

```bash
python __main__.py --native examples/vm_pure.ll
python __main__.py --tokens
```

`.ll` → bytecode JSON → **Go VM** (Python only compiles).

## Token efficiency

Compact agents are ~10× fewer tokens than OpenAI tool-loop Python.

## Honest CPU speed

Go VM works and is correct; optimized CPython loops can still be faster until we add typed stacks / direct codegen. Independence first; speed next.
