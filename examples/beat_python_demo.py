#!/usr/bin/env python3
"""Demo: beat Python (Weft-style) — density + static check + dense IR."""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from patterns.builder import build_from_intent, compare_to_python
from library.static_check import check_source

def main():
    print("=== Token density ===")
    print(json.dumps(compare_to_python()["report"], indent=2))
    print(compare_to_python()["claim"])
    print("\n=== Static check ===")
    good = 'model agent { mode: "tools" tools: {"calculator"} }\nx = agent("hi")\n'
    bad = 'model agent { mode: "tools" tools: {"not_a_real_tool_xyz"} }\n'
    print("good", check_source(good).to_dict())
    print("bad", check_source(bad).to_dict())
    print("\n=== Builder ===")
    for intent in ["Search for CallResult and get project stats", "what time is it"]:
        r = build_from_intent(intent, run=True)
        print(intent, "->", r.dense, "ok=", r.ok)

if __name__ == "__main__":
    main()
