"""Autonomous multi-step coding agent: explore → locate → edit → test → report."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
import os
import re
import sys
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.coding import project_tree, apply_patch, run_pytest
from tools.programmer import search_code, read_file, write_file


class CodingAgentResult:
    def __init__(self):
        self.steps: List[Dict[str, Any]] = []
        self.files_changed: List[str] = []
        self.tests_ok: Optional[bool] = None
        self.final: str = ""
        self.ok: bool = False

    def add(self, name: str, detail: Any):
        self.steps.append({"step": name, "detail": detail})

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "final": self.final, "files_changed": self.files_changed,
                "tests_ok": self.tests_ok, "steps": self.steps}


def _plant_bug_task() -> Dict[str, Any]:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ws = os.path.join(root, "examples", "agent_workspace")
    os.makedirs(ws, exist_ok=True)
    mod = os.path.join(ws, "broken_math.py")
    test = os.path.join(ws, "test_broken_math.py")
    with open(mod, "w") as f:
        f.write('def add(a, b):\n    return a - b  # BUG\n\ndef multiply(a, b):\n    return a * b\n')
    with open(test, "w") as f:
        f.write('''import unittest, importlib.util, os
def _load():
    path = os.path.join(os.path.dirname(__file__), "broken_math.py")
    spec = importlib.util.spec_from_file_location("broken_math", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
class TestBroken(unittest.TestCase):
    def test_add(self):
        self.assertEqual(_load().add(2, 3), 5)
    def test_multiply(self):
        self.assertEqual(_load().multiply(3, 4), 12)
if __name__ == "__main__":
    unittest.main()
''')
    return {"module": mod, "test": test}


def run_coding_agent(task: str = "fix the failing add function", workspace: str = "examples/agent_workspace", setup_demo: bool = True) -> CodingAgentResult:
    result = CodingAgentResult()
    t0 = time.time()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if setup_demo:
        planted = _plant_bug_task()
        result.add("setup", planted)
        mod_path = planted["module"]
        test_path = planted["test"]
    else:
        mod_path = os.path.join(root, workspace, "broken_math.py")
        test_path = os.path.join(root, workspace, "test_broken_math.py")

    tree = project_tree(os.path.join(root, workspace) if setup_demo else ".", max_depth=2)
    result.add("explore", {"tree_ok": tree.get("ok"), "path": tree.get("path")})

    search = search_code("def add", path=workspace if setup_demo else ".", glob="*.py")
    result.add("search", {"count": search.get("count"), "sample": (search.get("matches") or [])[:3]})

    proc = subprocess.run(["python", test_path], capture_output=True, text=True)
    result.add("test_before", {"exit": proc.returncode, "stderr_tail": (proc.stderr or proc.stdout or "")[-400:]})

    try:
        content = open(mod_path).read()
    except OSError:
        content = ""
    if "return a - b" in content:
        # prefer tools.coding.apply_patch if available with relative path
        rel = os.path.relpath(mod_path, root)
        try:
            patch = apply_patch(rel, "return a - b  # BUG", "return a + b")
        except Exception:
            patch = {"ok": False}
        if not patch.get("ok"):
            content2 = content.replace("return a - b  # BUG", "return a + b").replace("return a - b", "return a + b")
            open(mod_path, "w").write(content2)
            patch = {"ok": True, "path": rel}
        result.add("patch", patch)
        if patch.get("ok"):
            result.files_changed.append(rel)
    else:
        result.add("patch", {"ok": False, "error": f"no automatic fix for task: {task}"})

    proc2 = subprocess.run(["python", test_path], capture_output=True, text=True)
    result.tests_ok = proc2.returncode == 0
    result.add("test_after", {"exit": proc2.returncode, "ok": result.tests_ok})
    elapsed = round(time.time() - t0, 2)
    result.ok = bool(result.tests_ok and result.files_changed)
    result.final = f"Coding agent finished in {elapsed}s. changed={result.files_changed} tests_ok={result.tests_ok} steps={len(result.steps)}"
    result.add("report", result.final)
    return result


def run_live_coding_agent(agent: Callable, task: str, max_turns: int = 8):
    from library.core import run_agent
    prompt = (
        f"You are an autonomous coding agent. Task: {task}\n"
        "Use tools to explore, read, patch, and test. Finish when tests pass."
    )
    return run_agent(agent, prompt, max_turns=max_turns)
