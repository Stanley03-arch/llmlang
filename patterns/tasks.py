"""Broader task patterns beyond pure coding / web."""

from __future__ import annotations
from typing import Any, Callable, Dict, List
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.core import run_agent, CallResult

def generate_readme(agent: Callable, project_summary: str, path: str = "GENERATED_README.md") -> CallResult:
    prompt = (
        f"Write a clear README for this project:\n{project_summary}\n\n"
        f"Save it with write_file to path '{path}'. Include title, features, quick start."
    )
    return _run(agent, prompt)

def data_report(agent: Callable, question: str) -> CallResult:
    prompt = f"Answer this analytically, using calculator or run_python if helpful:\n{question}"
    return _run(agent, prompt)

def todo_plan(agent: Callable, goal: str) -> CallResult:
    prompt = (
        f"Break this goal into a concrete checklist of 5-8 tasks:\n{goal}\n"
        "Be specific and ordered."
    )
    return _run(agent, prompt)

def _run(agent: Callable, prompt: str) -> CallResult:
    result = run_agent(agent, prompt, max_turns=5)
    return CallResult(text=result.final_answer, confidence=result.confidence, final=True)
