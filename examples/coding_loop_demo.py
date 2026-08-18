#!/usr/bin/env python3
"""Demo coding loop: generate → test → patch pattern (offline mock)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.core import model, run_agent
from patterns.coding import generate_test_fix, implement_and_test
from patterns.coding_agent import run_coding_agent

def main():
    print("=== coding agent ===")
    r = run_coding_agent(setup_demo=True)
    print("ok=", r.ok, "tests_ok=", getattr(r, "tests_ok", None))
    print(str(r.final)[:300] if r.final else "")

    print("\n=== implement_and_test pattern (agent prompt only offline) ===")
    @model(name="coder", tools=["generate_module", "generate_tests", "run_pytest", "project_stats"], mode="tools")
    def coder(prompt=None, messages=None):
        return prompt
    result = implement_and_test(coder, "examples/gen_hello.py", "a hello() function that returns Hello")
    print(result.text[:400] if result.text else result)

if __name__ == "__main__":
    main()
