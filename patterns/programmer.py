"""High-level patterns that map to real programmer workflows."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.core import run_agent, CallResult

PROGRAMMER_TOOL_NAMES = [
    "read_file", "write_file", "list_dir", "search_code",
    "run_command", "run_python", "project_stats",
]

def explore_project(agent: Callable, question: str = "Give me an overview of this project") -> CallResult:
    prompt = f"{question}\nUse project_stats and list_dir. If useful, search_code for key entry points."
    return _run(agent, prompt)

def find_definition(agent: Callable, symbol: str) -> CallResult:
    prompt = (
        f"Find the definition of `{symbol}`. "
        f"Use search_code with query '{symbol}' or 'def {symbol}' / 'class {symbol}'. "
        "Then read_file the most relevant hit and summarize the definition."
    )
    return _run(agent, prompt)

def run_tests(agent: Callable, test_cmd: str = "python tests/test_language.py") -> CallResult:
    prompt = f"Run the tests using run_command with: {test_cmd}\nSummarize which tests passed or failed."
    return _run(agent, prompt)

def explain_file(agent: Callable, path: str) -> CallResult:
    prompt = f"Read {path} with read_file and explain what it does, key functions, and dependencies."
    return _run(agent, prompt)

def implement_snippet(agent: Callable, path: str, description: str) -> CallResult:
    prompt = f"Write a Python file at {path} that: {description}. Use write_file."
    return _run(agent, prompt)

def fix_from_error(agent: Callable, path: str, error: str) -> CallResult:
    prompt = (
        f"File {path} has this error:\n{error}\n"
        "Read the file, diagnose, and write a fixed version with write_file."
    )
    return _run(agent, prompt)

def _run(agent: Callable, prompt: str) -> CallResult:
    result = run_agent(agent, prompt, max_turns=5)
    return CallResult(text=result.final_answer, confidence=result.confidence, final=True)
