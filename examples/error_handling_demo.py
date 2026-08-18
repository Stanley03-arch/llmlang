#!/usr/bin/env python3
"""Error handling demos: language try/catch + tool executor soft failures."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from language.interpreter import run_source
from library.tool_executor import ToolExecutor
from library.pipeline import Pipeline

def main():
    print("=== language try/catch ===")
    ll = os.path.join(os.path.dirname(__file__), "error_handling.ll")
    if os.path.isfile(ll):
        run_source(open(ll).read(), mock=True)
    else:
        run_source('''
try {
  assert 1 == 2, "demo"
} catch err {
  print fmt("caught: {}", err)
}
print "ok"
''', mock=True)

    print("\n=== tool executor soft fail ===")
    ex = ToolExecutor(allowed_tools=["calculator"])
    r = ex.execute_one({"id": "1", "function": {"name": "now", "arguments": "{}"}})
    print("ok=", r.ok, "error=", r.error)

    r2 = ex.execute_one({"id": "2", "function": {"name": "calculator", "arguments": '{"expression": "2+2"}'}})
    print("calc ok=", r2.ok, "result=", r2.result)

    print("\n=== pipeline stop on fail ===")
    p = Pipeline("err").tool("bad", "no_such_tool", {}).tool("never", "calculator", {"expression": "1"})
    pr = p.run()
    print("pipeline ok=", pr.ok, "steps=", len(pr.steps))

if __name__ == "__main__":
    main()
