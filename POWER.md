# Power: token efficiency + native speed

## Beats Python where it counts

### 1. Pure numeric loops (CPU)

```bash
python __main__.py --beat --n 500000
```

Measured on this stack (sum 0..n-1):

| n | Hand Python | Go codegen (run) | Winner |
|---|-------------|------------------|--------|
| 300k | ~12.5 ms | **~1.7 ms** | **Go ~7×** |
| 1M | ~42 ms | **~2.2 ms** | **Go ~19×** |

Pipeline: `.ll` → **Go source** → `go build` → native binary.

### 2. AI agent tokens

```bash
python __main__.py --tokens
```

Compact / short `.ll` ≪ Python OpenAI tool-loop glue.

### 3. Independence

Pure programs do not need CPython at **runtime** (Go executes).

## Commands

```bash
python __main__.py --beat
python __main__.py --native          # Go codegen path
python __main__.py --speed           # Python transpile path
python __main__.py --tokens
```

## Limits

- Native codegen: pure numeric/control subset (while, if, arithmetic).
- Models, tools, soft-if: still Python interpreter path.
- Build time is separate; **run** time is what beats CPython.
