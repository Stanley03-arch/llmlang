"""Patterns for building websites and other deliverables."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.core import run_agent, CallResult

WEB_TOOL_NAMES = [
    "scaffold_website", "write_page", "write_asset", "serve_site", "list_sites",
    "read_file", "write_file", "list_dir", "run_command",
]

def build_website(agent: Callable, name: str, title: str, brief: str = "", serve: bool = False) -> CallResult:
    prompt = f"Build a static website named '{name}' with title '{title}'. Use scaffold_website. "
    if brief:
        prompt += f"Design notes: {brief}. "
    prompt += "After scaffolding, confirm the files created."
    if serve:
        prompt += f" Then serve_site for '{name}'."
    return _run(agent, prompt)

def add_page(agent: Callable, site: str, page: str, title: str, content_brief: str) -> CallResult:
    prompt = (
        f"Add a page to site '{site}'. Use write_page with page='{page}', title='{title}'. "
        f"Body should cover: {content_brief}. Use simple semantic HTML inside body_html."
    )
    return _run(agent, prompt)

def preview_site(agent: Callable, site: str, port: int = 8765) -> CallResult:
    prompt = f"Serve the site '{site}' on port {port} using serve_site and report the URL."
    return _run(agent, prompt)

def _run(agent: Callable, prompt: str) -> CallResult:
    result = run_agent(agent, prompt, max_turns=5)
    return CallResult(text=result.final_answer, confidence=result.confidence, final=True)
