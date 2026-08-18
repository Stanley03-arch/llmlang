#!/usr/bin/env python3
"""Tests for central ToolExecutor."""

from __future__ import annotations
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from library.tool_executor import ToolExecutor, execute_tool_calls
from library.core import model, run_agent


class TestToolExecutor(unittest.TestCase):
    def test_execute_calculator(self):
        ex = ToolExecutor()
        r = ex.execute_one({
            "id": "c1",
            "type": "function",
            "function": {"name": "calculator", "arguments": '{"expression": "2+3*4"}'},
        })
        self.assertTrue(r.ok)
        self.assertEqual(r.result["result"], 14)

    def test_missing_required(self):
        ex = ToolExecutor()
        r = ex.execute_one({
            "id": "c2",
            "function": {"name": "count_letter", "arguments": '{"text": "hello"}'},
        })
        self.assertFalse(r.ok)
        self.assertIn("Missing required", r.error)

    def test_unknown_tool(self):
        ex = ToolExecutor()
        r = ex.execute_one({"id": "c3", "function": {"name": "no_such_tool", "arguments": "{}"}})
        self.assertFalse(r.ok)
        self.assertIn("Unknown tool", r.error)

    def test_allowed_tools_gate(self):
        ex = ToolExecutor(allowed_tools=["calculator"])
        r = ex.execute_one({
            "id": "c4",
            "function": {"name": "now", "arguments": "{}"},
        })
        self.assertFalse(r.ok)
        self.assertIn("not allowed", r.error)

    def test_parallel_batch(self):
        calls = [
            {"id": "a", "function": {"name": "calculator", "arguments": '{"expression": "1+1"}'}},
            {"id": "b", "function": {"name": "word_length", "arguments": '{"text": "abcd"}'}},
        ]
        results = execute_tool_calls(calls, parallel=True)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.ok for r in results))

    def test_message_format(self):
        ex = ToolExecutor()
        calls = [{"id": "t1", "type": "function", "function": {"name": "now", "arguments": "{}"}}]
        msgs, results = ex.execute_and_format("calling now", calls)
        self.assertEqual(msgs[0]["role"], "assistant")
        self.assertEqual(msgs[1]["role"], "tool")

    def test_agent_loop_executes_tools(self):
        @model(name="calc_agent", tools=["calculator"], mode="tools")
        def agent(prompt=None, messages=None):
            return prompt
        r = run_agent(agent, "Calculate 10 + 5", max_turns=3)
        self.assertTrue(len(r.steps) >= 1)
        self.assertIsInstance(r.final_answer, str)


if __name__ == "__main__":
    unittest.main()
