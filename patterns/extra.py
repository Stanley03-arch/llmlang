"""Patterns for packages, reports, HTTP, git."""

from __future__ import annotations
from typing import Callable
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.core import run_agent, CallResult

EXTRA_TOOL_NAMES = [
    "http_get", "read_json", "write_json", "append_file", "git_status",
    "markdown_report", "now", "scaffold_python_package", "replace_in_file",
    "read_file", "write_file", "list_dir", "run_command",
]

def create_package(agent: Callable, name: str, description: str = "") -> CallResult:
    prompt = f"Create a Python package named '{name}'. Use scaffold_python_package. Description: {description or name}."
    return _run(agent, prompt)

def write_report(agent: Callable, title: str, topic: str, path: str = "examples/GENERATED_REPORT.md") -> CallResult:
    prompt = f"Write a markdown report titled '{title}' about: {topic}. Use markdown_report and save to '{path}'."
    return _run(agent, prompt)

def fetch_url(agent: Callable, url: str) -> CallResult:
    prompt = f"Fetch this URL with http_get and summarize the response: {url}"
    return _run(agent, prompt)

def repo_status(agent: Callable) -> CallResult:
    prompt = "Use git_status and project_stats to summarize the repository state."
    return _run(agent, prompt)

def _run(agent: Callable, prompt: str) -> CallResult:
    result = run_agent(agent, prompt, max_turns=5)
    return CallResult(text=result.final_answer, confidence=result.confidence, final=True)
