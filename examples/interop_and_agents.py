#!/usr/bin/env python3
"""Demo: Python interop + export_agent."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.interop import py_eval, py_call
from patterns.advanced import export_agent, DEEP_CODING_TOOLS
from library.core import run_agent

def main():
    print("=== py_eval ===")
    print(py_eval("2 + 2"))
    print(py_eval("sum(range(10))"))

    print("\n=== py_call ===")
    print(py_call("math", "sqrt", args=[16]))

    print("\n=== export_agent ===")
    agent = export_agent("demo", tools=["calculator", "project_stats"], system="Be brief.")
    r = run_agent(agent, "What is 3*9? Use calculator.", max_turns=3)
    print("final:", r.final_answer)

if __name__ == "__main__":
    main()
