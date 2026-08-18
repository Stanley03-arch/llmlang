# Speed: our current way

## Strategy

Do **not** claim to beat CPython at being CPython.

Make pure `.ll` **fast enough** by transpiling to real Python and executing under CPython.

| Path | Role |
|------|------|
| `run_fast` / `--speed` | pure `.ll` → Python source → `exec` |
| Bytecode VM | educational / portable intermediate |
| Tree-walk interpreter | full language (models, tools) |

## Benchmark (sum 0..n-1, n=30000, typical)

| Engine | Relative |
|--------|----------|
| Hand Python | 1× |
| **Fast path** | ~3× (includes transpile) |
| Bytecode VM | ~25–90× slower than hand |
| Interpreter | slowest (use smaller n) |

Fast path is **~8–30× faster than our Python-hosted bytecode** on this loop.

## Commands

```bash
python __main__.py --speed
python __main__.py --speed --n 50000
python __main__.py --speed examples/vm_pure.ll
python __main__.py --speed --transpile examples/vm_pure.ll
```

## AI workloads

Token density + parallel tools + cache still dominate agent wall-clock — see BEAT_PYTHON.md.
