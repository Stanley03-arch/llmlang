# LlmLang foundations (Python/ABC path)

## Built this phase

| Artifact | Role |
|----------|------|
| `LANGUAGE_SPEC.md` | Formal core vs effects |
| `language/bytecode.py` | Stack VM + compiler (pure subset) |
| `language/ast_nodes.py` | Includes `HardIf` |
| `language/hard_if_support.py` | Parser patch: `if expr { }` vs `if conf(x) > n` |
| `examples/vm_pure.ll` | Pure program for the VM |

## Run

```bash
python __main__.py --vm
python __main__.py --vm examples/vm_pure.ll
python __main__.py --vm --dis examples/vm_pure.ll
```

## Two runtimes

1. **Bytecode VM** — pure arithmetic, lists, while, hard if  
2. **Tree-walk interpreter** — full language (models, tools, soft-if, parallel)

## Next foundation steps

- VM 0.2: functions + call frames
- Dicts + for-in on VM
- Effect checker (`pure` programs cannot call models)
- Shared value model between VM and interpreter
