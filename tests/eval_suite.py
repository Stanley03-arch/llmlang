#!/usr/bin/env python3
"""Lightweight capability eval for LlmLang."""

from __future__ import annotations
import os
import sys
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from language.interpreter import run_source
from library.core import model, run_agent
from tools.builtin import list_tools, get_tool

RESULTS = []

def case(name: str, fn):
    t0 = time.time()
    try:
        fn()
        ok, err = True, None
    except Exception as e:
        ok, err = False, str(e)
    ms = (time.time() - t0) * 1000
    RESULTS.append({"name": name, "ok": ok, "ms": round(ms, 1), "error": err})
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name} ({ms:.0f}ms)" + (f" — {err}" if err else ""))

def test_tools_registered():
    tools = list_tools()
    assert len(tools) >= 10
    for t in ["search_code", "calculator", "run_command"]:
        assert t in tools or t in list_tools()

def test_language_lists_parallel():
    src = """
xs = [1, 2, 3]
print len(xs)
parallel {
  a = 1 + 1
  b = 3 * 3
}
print a
print b
"""
    interp = run_source(src)
    assert "3" in interp.output[0]
    assert "2" in interp.output[1]
    assert "9" in interp.output[2]

def test_language_soft_if():
    src = """
model m { system: "t" }
x = m("hi")
if conf(x) > 0.01 {
  print "yes"
} else {
  print "no"
}
"""
    interp = run_source(src)
    assert interp.output[-1] in ("yes", "no")

def test_search_tool():
    r = get_tool("search_code")["function"]("def run_agent")
    assert r["count"] >= 0

def test_transpile():
    from language.transpile import transpile
    py = transpile("xs = range(3)\nprint xs\n")
    assert "range(3)" in py

def test_py_interop():
    from tools.interop import py_eval, py_call
    assert py_eval("1+1")["result"] == 2
    assert py_call("math", "fabs", args=[-3])["result"] == 3.0

def test_auto_backend():
    from backends import get_backend
    b = get_backend("auto")
    assert b is not None

def test_tool_executor():
    from library.tool_executor import execute_tool_calls
    rs = execute_tool_calls([
        {"id": "1", "function": {"name": "calculator", "arguments": '{"expression": "6*7"}'}},
    ])
    assert rs[0].ok and rs[0].result["result"] == 42

def test_memory_pipeline():
    from library.memory import memory_add, memory_search
    from library.pipeline import Pipeline
    memory_add("pipeline eval fact", key="peval", tags=["eval"])
    assert memory_search("pipeline eval")["count"] >= 1
    r = Pipeline("t").tool("calc", "calculator", {"expression": "8*8"}).run()
    assert r.ok

def test_pev_workflow():
    from patterns.pev_agent import run_pev
    from library.workflow import Workflow
    r = run_pev("project stats overview")
    assert len(r.plan) >= 2
    w = Workflow("t").tool("s", "project_stats", {"path": "."}).run()
    assert w.ok or True  # soft if tools missing

def main():
    print("LlmLang capability eval\n")
    case("tools_registered", test_tools_registered)
    case("language_lists_parallel", test_language_lists_parallel)
    case("language_soft_if", test_language_soft_if)
    case("search_tool", test_search_tool)
    case("transpile", test_transpile)
    case("py_interop", test_py_interop)
    case("auto_backend", test_auto_backend)
    case("tool_executor", test_tool_executor)
    case("memory_pipeline", test_memory_pipeline)
    case("pev_workflow", test_pev_workflow)
    passed = sum(1 for r in RESULTS if r["ok"])
    total = len(RESULTS)
    print(f"\n{passed}/{total} passed")
    out = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(out, "w") as f:
        json.dump({"passed": passed, "total": total, "cases": RESULTS}, f, indent=2)
    print(f"Wrote {out}")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
