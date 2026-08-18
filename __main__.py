#!/usr/bin/env python3
"""LlmLang — programming language whose runtime is an LLM + tools.

Usage:
  python -m llm_lang --demo | --test | --eval | --tools | --version
  python -m llm_lang --agent | --live | --pev [task] | --workflow
  python -m llm_lang --fast | --ai-speed | --sessions | --web
  python -m llm_lang <file.ll>
"""

from __future__ import annotations
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
PARENT = os.path.dirname(ROOT)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

def cmd_demo():
    from language.interpreter import run_source
    for name in ("mega_showcase.ll", "ultimate_showcase.ll", "hello.ll"):
        path = os.path.join(ROOT, "examples", name)
        if os.path.isfile(path):
            print(f"Running: {path}\n")
            run_source(open(path).read())
            return
    run_source('print "LlmLang demo"\nmodel m { system: "brief" }\nx = m("hi")\nprint conf(x)\n')

def cmd_test():
    import runpy
    os.chdir(ROOT)
    runpy.run_path(os.path.join(ROOT, "tests", "test_language.py"), run_name="__main__")

def cmd_eval():
    import runpy
    os.chdir(ROOT)
    runpy.run_path(os.path.join(ROOT, "tests", "eval_suite.py"), run_name="__main__")

def cmd_web():
    from tools.web import scaffold_website, list_sites, serve_site
    r = scaffold_website(name="llm_home", title="LlmLang", pages=["index", "about", "docs"])
    print(r)
    print("Sites:", list_sites())
    print(serve_site("llm_home", port=8765))

def cmd_tools():
    from tools.builtin import list_tools, TOOL_REGISTRY
    print(f"{len(list_tools())} tools:\n")
    for name in list_tools():
        desc = TOOL_REGISTRY[name].get("description", "")
        print(f"  {name:24} {desc[:70]}")

def cmd_version():
    ver = "1.6.0"
    try:
        for line in open(os.path.join(ROOT, "__init__.py")):
            if line.startswith("__version__"):
                ver = line.split("=")[1].strip().strip("\"'")
                break
    except Exception:
        pass
    print(f"LlmLang {ver}")
    print("A programming language whose runtime is an LLM + tools.")

def cmd_agent():
    from patterns.coding_agent import run_coding_agent
    from library.session import new_session, log_event
    session = new_session("coding_agent")
    result = run_coding_agent(setup_demo=True)
    log_event(session, {"type": "coding_agent", **result.to_dict()})
    print(result.final)
    print("ok=", result.ok, "tests_ok=", result.tests_ok)

def cmd_sessions():
    from library.session import list_sessions
    for s in list_sessions():
        print(s)

def cmd_live():
    from backends import probe_backend, get_backend
    info = probe_backend()
    for k, v in info.items():
        print(f"  {k}: {v}")
    if info.get("selected") == "openai" and info.get("has_api_key"):
        try:
            from library.core import ModelConfig
            r = get_backend("openai").complete(ModelConfig(name="probe", temperature=0), "Reply with exactly: pong")
            print(f"  text={r.text!r} conf={r.confidence}")
        except Exception as e:
            print(f"  completion error: {e}")

def cmd_pev(task: str = None):
    from patterns.pev_agent import run_pev
    r = run_pev(task or "Search for CallResult and get project stats")
    print(r.final)
    print("ok=", r.ok, "plan=", len(r.plan))

def cmd_workflow():
    from library.workflow import Workflow
    w = Workflow("demo").tool("stats", "project_stats", {"path": "."}).tool("calc", "calculator", {"expression": "7*6"}, depends_on=["stats"])
    r = w.run()
    print(r.to_dict())

def cmd_fast():
    from library.efficiency import run_tasks_parallel
    r = run_tasks_parallel([
        {"name": "c", "kind": "tool", "tool": "calculator", "arguments": {"expression": "1+1"}},
        {"name": "w", "kind": "tool", "tool": "word_length", "arguments": {"text": "abcd"}},
    ])
    print(f"ok={r.ok} speedup={r.speedup:.2f}x wall_ms={r.wall_ms:.0f}")

def cmd_ai_speed():
    from library.efficiency import ai_speed_benchmark, fast_ai_agent
    b = ai_speed_benchmark()
    print("serial_ms", b.get("serial_ms"))
    print("parallel_cold_ms", b.get("parallel_cold_ms"))
    print("parallel_warm_ms", b.get("parallel_warm_ms"))
    print(fast_ai_agent("get project stats")["summary"])

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return
    cmd = args[0]
    if cmd == "--demo": cmd_demo()
    elif cmd == "--test": cmd_test()
    elif cmd == "--eval": cmd_eval()
    elif cmd == "--web": cmd_web()
    elif cmd == "--tools": cmd_tools()
    elif cmd in ("--version", "-V"): cmd_version()
    elif cmd == "--agent": cmd_agent()
    elif cmd == "--sessions": cmd_sessions()
    elif cmd == "--live": cmd_live()
    elif cmd == "--pev": cmd_pev(" ".join(args[1:]) if len(args) > 1 else None)
    elif cmd == "--workflow": cmd_workflow()
    elif cmd == "--fast": cmd_fast()
    elif cmd == "--ai-speed": cmd_ai_speed()
    elif cmd == "--backend":
        if len(args) < 2:
            print("Usage: --backend mock|openai|auto"); sys.exit(1)
        os.environ["LLM_BACKEND"] = args[1]; cmd_live()
    else:
        path = cmd if os.path.exists(cmd) else os.path.join(ROOT, cmd)
        if not os.path.exists(path):
            print(f"File not found: {cmd}"); sys.exit(1)
        from language.interpreter import run_source
        print(f"=== {path} ===\n")
        run_source(open(path).read())

if __name__ == "__main__":
    main()
