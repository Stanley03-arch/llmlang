# Upload status (LlmLang 1.6.0)

## On GitHub

- Docs: README, VISION, LANGUAGE, ERRORS, LIVE, SETUP, STATUS, Makefile, LICENSE
- language/: __init__, ast_nodes, transpile
- library/: __init__, memory, session, tool_executor, workflow
- tools/: builtin, programmer, plugins, util_tools, rag, data
- backends/: __init__, base
- tests/: test_language, test_tool_executor
- stdlib/, schemas/

## Still primarily local (use zip for full sync)

- language/parser.py, interpreter.py
- library/core.py, efficiency.py, pipeline.py
- backends/openai_compat.py
- tools/coding.py, web.py, extra.py, interop, github_tools, api_scaffold, memory_tools
- patterns/* (most)
- tests/eval_suite.py, test_live_backend.py
- __main__.py and most examples/

## Full source zip

`llmlang-src.zip` from the build environment — unpack over clone and `git push` for a complete tree.

Repo: https://github.com/Stanley03-arch/llmlang
