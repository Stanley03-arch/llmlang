"""Token efficiency — denser than Python for AI agents."""
from __future__ import annotations
from typing import Any, Dict, List

COMPACT_HEADER = "@ll1"

def compact_agent(goal: str, tools: List[str], parallel: bool = True) -> str:
    t = ",".join(tools)
    lines = [COMPACT_HEADER, f"@tools {t}", f"> {goal.strip()}"]
    if parallel and len(tools) > 1:
        lines.append(f"! parallel {','.join(tools[:4])}")
    return "\n".join(lines) + "\n"

def expand_compact(src: str) -> Dict[str, Any]:
    tools, goal, parallel = [], "", []
    for line in src.splitlines():
        line = line.strip()
        if line.startswith("@tools "):
            tools = [x.strip() for x in line[7:].split(",") if x.strip()]
        elif line.startswith(">"):
            goal = line[1:].strip()
        elif line.startswith("! parallel "):
            parallel = [x.strip() for x in line[11:].split(",") if x.strip()]
    return {"goal": goal, "tools": tools, "parallel": parallel or tools}

def token_report(python_agent: str, compact: str, ll: str = "") -> Dict[str, Any]:
    def toks(s: str) -> int:
        return max(1, len(s) // 4)
    out = {
        "python_tokens_est": toks(python_agent),
        "compact_tokens_est": toks(compact),
        "compact_vs_python": round(toks(python_agent) / max(toks(compact), 1), 2),
        "note": "Token efficiency beats Python agent glue; not CPU FLOPs.",
    }
    if ll:
        out["ll_tokens_est"] = toks(ll)
        out["ll_vs_python"] = round(toks(python_agent) / max(toks(ll), 1), 2)
    return out

PYTHON_GLUE = '''
from openai import OpenAI
client = OpenAI()
tools = [{"type":"function","function":{"name":"search_code","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}}]
messages = [{"role":"user","content":"Find CallResult"}]
for _ in range(8):
    r = client.chat.completions.create(model="gpt-4o", messages=messages, tools=tools)
    m = r.choices[0].message
    messages.append(m)
    if not m.tool_calls: break
'''
