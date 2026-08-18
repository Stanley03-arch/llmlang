#!/usr/bin/env python3
"""Demo multi-domain power tasks."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.efficiency import run_tasks_parallel, fast_ai_agent
from tools.rag import codebase_rag
from tools.programmer import search_code, diff_stats

def main():
    print("=== parallel tasks ===")
    report = run_tasks_parallel([
        {"name": "stats", "kind": "tool", "tool": "project_stats", "arguments": {"path": "."}},
        {"name": "calc", "kind": "tool", "tool": "calculator", "arguments": {"expression": "12*12"}},
        {"name": "rag", "kind": "tool", "tool": "codebase_rag", "arguments": {"query": "CallResult", "top_k": 2}},
    ], max_workers=3)
    print(f"ok={report.ok} speedup={report.speedup:.2f}x wall={report.wall_ms:.0f}ms")

    print("\n=== fast_ai_agent ===")
    r = fast_ai_agent("Search for ToolExecutor and get project stats")
    print(r["summary"])

    print("\n=== rag ===")
    hits = codebase_rag("Interpreter", top_k=2)
    print("hits", hits.get("count"))

if __name__ == "__main__":
    main()
