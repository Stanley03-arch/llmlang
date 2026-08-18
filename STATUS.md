# Upload status

This GitHub tree is **growing** but may still be incomplete versus the full local build (v1.6.0).

## On GitHub now

- Docs (README, VISION, LANGUAGE, ERRORS, LIVE, …)
- Package structure: language/, library/, tools/, backends/, stdlib/, schemas/
- language/ast_nodes.py, transpile.py
- tools/builtin.py, programmer.py, plugins.py, util_tools.py, rag.py
- backends/__init__.py, base.py

## Still primarily local (may be missing on GitHub)

- language/parser.py, interpreter.py
- library/core.py, efficiency.py, tool_executor.py, workflow.py, …
- Most remaining tools/, patterns/, tests/

## Full source

Use the complete zip from the build environment:

`llmlang-src.zip`

```bash
git clone https://github.com/Stanley03-arch/llmlang.git
cd llmlang
unzip -o /path/to/llmlang-src.zip
cp -a llm_lang/* .
rm -rf llm_lang
git add -A && git commit -m "Sync full LlmLang 1.6.0" && git push
```
