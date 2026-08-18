#!/usr/bin/env python3
"""Demo: memory + pipelines + plugins capacity layer."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.memory import memory_add, memory_search, memory_list
from library.pipeline import Pipeline
from tools.plugins import register_tool
from tools.builtin import list_tools

def main():
    print("=== Memory ===")
    memory_add("LlmLang uses confidence-based control flow", key="fact1", tags=["lang"])
    print(memory_search("confidence"))
    print("items:", memory_list(limit=5))

    print("\n=== Plugin ===")
    register_tool("double", lambda x=0: {"ok": True, "result": int(x) * 2}, description="Double a number")
    print("tools count", len(list_tools()))

    print("\n=== Pipeline ===")
    p = (
        Pipeline("capacity")
        .tool("stats", "project_stats", {"path": "."})
        .tool("calc", "calculator", {"expression": "6*7"})
    )
    r = p.run()
    print("pipeline ok=", r.ok)
    for s in r.steps:
        print(f"  {s.name}: ok={s.ok}")

if __name__ == "__main__":
    main()
