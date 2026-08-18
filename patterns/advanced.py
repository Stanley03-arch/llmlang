"""Advanced coding + interop patterns."""

from __future__ import annotations
from typing import Any, Callable, Dict, List
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.core import run_agent, CallResult, model

DEEP_CODING_TOOLS = [
    "search_code", "search_and_read", "read_file", "read_many",
    "apply_patch", "apply_unified_diff", "multi_file_replace", "multi_file_search_replace",
    "generate_module", "generate_tests", "run_pytest", "project_tree", "list_symbols",
    "py_eval", "py_call", "github_search_code", "github_status",
]

def multi_file_refactor(agent: Callable, instruction: str, scope: str = ".") -> CallResult:
    prompt = (
        f"MULTI-FILE REFACTOR in {scope}.\nInstruction: {instruction}\n"
        "1) search_and_read to find relevant files\n2) read_file key targets\n"
        "3) apply_patch or multi_file_replace\n4) run_pytest if tests exist\nReport files changed and test status."
    )
    result = run_agent(agent, prompt, max_turns=8)
    return CallResult(text=result.final_answer, confidence=result.confidence, final=True)

def github_explore(agent: Callable, query: str) -> CallResult:
    prompt = f"Use github_status then github_search_code or github_search_repos for: {query}. Summarize findings."
    result = run_agent(agent, prompt, max_turns=4)
    return CallResult(text=result.final_answer, confidence=result.confidence, final=True)

def export_agent(name: str, tools: List[str], system: str = "You are a careful agent.", mode: str = "tools"):
    @model(name=name, system=system, tools=tools, mode=mode, temperature=0.1)
    def agent_fn(prompt=None, messages=None):
        return prompt
    agent_fn._llmlang_export = True
    agent_fn._llmlang_tools = tools
    return agent_fn
