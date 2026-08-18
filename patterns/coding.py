"""High-power coding agent patterns."""

from __future__ import annotations
from typing import Callable, List, Optional
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.core import run_agent, CallResult

CODING_TOOL_NAMES = [
    "apply_unified_diff", "read_many", "search_and_read",
    "read_file", "write_file", "apply_patch", "search_code", "list_symbols",
    "generate_module", "generate_tests", "run_pytest", "run_command", "run_python",
    "project_tree", "project_stats", "list_dir",
]

def implement_and_test(agent: Callable, module_path: str, description: str, test_path: str = None) -> CallResult:
    test_path = test_path or module_path.replace(".py", "_test.py")
    prompt = (
        f"Implement the following as a Python module at {module_path}: {description}. "
        f"Use generate_module. Then generate_tests at {test_path}. Then run_pytest or run_command to verify."
    )
    return _run(agent, prompt)

def inspect_codebase(agent: Callable, focus: str = "") -> CallResult:
    prompt = "Use project_tree and project_stats to orient. " + (f"Then search_code for '{focus}'. " if focus else "") + "Summarize structure."
    return _run(agent, prompt)

def patch_file(agent: Callable, path: str, instruction: str) -> CallResult:
    prompt = f"Read {path} with read_file, then apply_patch to implement: {instruction}. Use exact old/new text from the file."
    return _run(agent, prompt)

def generate_test_fix(agent, module_path: str, spec: str, max_rounds: int = 3) -> CallResult:
    prompt = (
        f"CODING LOOP for {module_path}:\nSpec: {spec}\n"
        f"1) generate_module at {module_path}\n2) generate_tests\n3) run_pytest\n"
        f"If tests fail, apply_patch to fix, then re-run. Max {max_rounds} fix rounds."
    )
    return _run(agent, prompt)

def _run(agent: Callable, prompt: str) -> CallResult:
    result = run_agent(agent, prompt, max_turns=6)
    return CallResult(text=result.final_answer, confidence=result.confidence, final=True)
