"""Dense IR — token-cheap representation for AI builders (Weft-inspired)."""

from __future__ import annotations
from typing import Any, Dict, List, Union
import json

from library.tool_executor import ToolExecutor


def parse_dense_line(line: str) -> List[Dict[str, Any]]:
    parts = [p.strip() for p in line.split("|") if p.strip()]
    steps = []
    for i, part in enumerate(parts):
        if part.startswith("T ") or part.startswith("t "):
            rest = part[2:].strip()
            bits = rest.split()
            tool = bits[0]
            args: Dict[str, Any] = {}
            for b in bits[1:]:
                if "=" in b:
                    k, v = b.split("=", 1)
                    args[k] = v.strip('"')
            steps.append({"op": "tool", "name": f"s{i}_{tool}", "tool": tool, "args": args})
        elif part.startswith("L ") or part.startswith("l "):
            prompt = part[2:].strip().strip('"')
            steps.append({"op": "llm", "name": f"llm{i}", "prompt": prompt, "tools": []})
        elif part.startswith("M ") or part.startswith("m "):
            steps.append({"op": "llm", "name": f"m{i}", "prompt": part[2:].strip(), "tools": []})
        else:
            steps.append({"op": "tool", "name": f"s{i}", "tool": part.split()[0], "args": {}})
    return steps


def expand_to_ll(ir: Union[Dict[str, Any], List[Dict[str, Any]], str]) -> str:
    if isinstance(ir, str):
        if ir.strip().startswith("{"):
            ir = json.loads(ir)
        else:
            ir = {"pipeline": parse_dense_line(ir)}
    if isinstance(ir, list):
        pipeline = ir
    else:
        pipeline = ir.get("pipeline") or ir.get("steps") or []
    lines = ["# Generated from dense IR", ""]
    for step in pipeline:
        op = step.get("op") or step.get("kind")
        name = step.get("name") or "step"
        if op == "tool":
            tool = step.get("tool") or "project_stats"
            args = step.get("args") or step.get("arguments") or {}
            lines.append(f"# tool {name}: {tool} {json.dumps(args)}")
            lines.append("# use run via pipeline host")
        elif op == "llm":
            prompt = step.get("prompt") or ""
            tools = step.get("tools") or []
            tool_s = " ".join(f'"{t}"' for t in tools)
            lines.append(f"model {name} {{")
            lines.append('  system: "You are a careful agent."')
            lines.append('  mode: "tools"')
            if tools:
                lines.append(f"  tools: {{{tool_s}}}")
            lines.append("}")
            lines.append(f'{name}_out = {name}("{prompt}")')
            lines.append(f"print {name}_out")
            lines.append("")
    return "\n".join(lines) + "\n"


def run_dense(ir: Union[Dict[str, Any], List, str], max_workers: int = 4) -> Dict[str, Any]:
    if isinstance(ir, str):
        if ir.strip().startswith("{"):
            ir = json.loads(ir)
        else:
            ir = {"pipeline": parse_dense_line(ir)}
    if isinstance(ir, list):
        steps = ir
    else:
        steps = ir.get("pipeline") or ir.get("steps") or []
    ex = ToolExecutor(timeout_s=60)
    results = []
    ctx: Dict[str, Any] = {}
    for step in steps:
        op = step.get("op") or step.get("kind")
        name = step.get("name") or f"step{len(results)}"
        if op == "tool":
            tool = step.get("tool")
            args = step.get("args") or step.get("arguments") or {}
            resolved = {}
            for k, v in args.items():
                if isinstance(v, str) and v.startswith("$") and v[1:] in ctx:
                    resolved[k] = ctx[v[1:]]
                else:
                    resolved[k] = v
            tr = ex.execute_one({"id": name, "function": {"name": tool, "arguments": json.dumps(resolved)}})
            entry = {"name": name, "op": "tool", "ok": tr.ok, "result": tr.result if tr.ok else None, "error": tr.error}
            results.append(entry)
            if tr.ok:
                ctx[name] = tr.result
            else:
                return {"ok": False, "results": results, "context_keys": list(ctx.keys())}
        elif op == "llm":
            results.append({"name": name, "op": "llm", "ok": True, "pending": True,
                            "prompt": step.get("prompt"), "tools": step.get("tools") or [],
                            "note": "LLM step — run via agent host"})
        else:
            results.append({"name": name, "op": op, "ok": False, "error": f"unknown op {op}"})
            return {"ok": False, "results": results, "context_keys": list(ctx.keys())}
    return {"ok": True, "results": results, "context_keys": list(ctx.keys())}


def density_report(python_src: str, ll_src: str = "", dense: str = "") -> Dict[str, Any]:
    def toks(s: str) -> int:
        return max(1, len(s) // 4)
    py_t = toks(python_src)
    out: Dict[str, Any] = {"python_tokens_est": py_t, "python_chars": len(python_src)}
    if ll_src:
        ll_t = toks(ll_src)
        out["ll_tokens_est"] = ll_t
        out["ll_vs_python"] = round(py_t / ll_t, 2) if ll_t else None
    if dense:
        d_t = toks(dense)
        out["dense_tokens_est"] = d_t
        out["dense_vs_python"] = round(py_t / d_t, 2) if d_t else None
    return out


PYTHON_AGENT_GLUE = '''
import os, json
from openai import OpenAI
client = OpenAI()
tools = [{"type": "function", "function": {"name": "search_code", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
 {"type": "function", "function": {"name": "project_stats", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}]}]
messages = [{"role": "user", "content": "Find CallResult and summarize project size"}]
for _ in range(5):
    r = client.chat.completions.create(model="gpt-4o", messages=messages, tools=tools)
    msg = r.choices[0].message
    messages.append(msg)
    if not msg.tool_calls:
        break
    for tc in msg.tool_calls:
        pass
print(messages[-1])
'''

LL_EQUIVALENT = '''
model agent {
  mode: "tools"
  tools: {"search_code" "project_stats"}
}
out = agent("Find CallResult and summarize project size")
print out
'''

DENSE_EQUIVALENT = 'T search_code query=CallResult | T project_stats path=. | L "summarize findings"'
