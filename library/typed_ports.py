"""Typed ports between workflow steps — Weft-inspired structural checks."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class Port:
    name: str
    typ: str = "any"

    def compatible_with(self, other: "Port") -> bool:
        if self.typ == "any" or other.typ == "any":
            return True
        return self.typ == other.typ


@dataclass
class TypedStep:
    name: str
    kind: str
    tool: Optional[str] = None
    inputs: List[Port] = field(default_factory=list)
    outputs: List[Port] = field(default_factory=list)
    args: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "kind": self.kind, "tool": self.tool,
            "inputs": [{"name": p.name, "type": p.typ} for p in self.inputs],
            "outputs": [{"name": p.name, "type": p.typ} for p in self.outputs],
            "args": self.args, "depends_on": self.depends_on,
        }


@dataclass
class PortCheckIssue:
    severity: str
    code: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {"severity": self.severity, "code": self.code, "message": self.message}


@dataclass
class TypedGraph:
    steps: Dict[str, TypedStep] = field(default_factory=dict)

    def add(self, step: TypedStep) -> "TypedGraph":
        self.steps[step.name] = step
        return self

    def edge(self, src: str, dst: str) -> "TypedGraph":
        if src not in self.steps[dst].depends_on:
            self.steps[dst].depends_on.append(src)
        return self

    def check(self) -> Dict[str, Any]:
        issues: List[PortCheckIssue] = []
        for name, step in self.steps.items():
            for d in step.depends_on:
                if d not in self.steps:
                    issues.append(PortCheckIssue("error", "missing_dep", f"step '{name}' depends on unknown '{d}'"))
        if self._has_cycle():
            issues.append(PortCheckIssue("error", "cycle", "dependency cycle detected"))
        for name, step in self.steps.items():
            for d in step.depends_on:
                if d not in self.steps:
                    continue
                upstream = self.steps[d]
                if not step.inputs:
                    continue
                if not upstream.outputs:
                    issues.append(PortCheckIssue("warning", "no_outputs", f"'{name}' depends on '{d}' with no outputs"))
                    continue
                if len(step.inputs) == 1 and len(upstream.outputs) == 1:
                    if not step.inputs[0].compatible_with(upstream.outputs[0]):
                        issues.append(PortCheckIssue("error", "type_mismatch",
                            f"'{d}' -> '{name}' type mismatch"))
                else:
                    up_map = {p.name: p for p in upstream.outputs}
                    for inp in step.inputs:
                        if inp.name in up_map and not inp.compatible_with(up_map[inp.name]):
                            issues.append(PortCheckIssue("error", "type_mismatch", f"port '{inp.name}' mismatch"))
        errors = [i for i in issues if i.severity == "error"]
        return {"ok": len(errors) == 0, "issues": [i.to_dict() for i in issues],
                "errors": len(errors), "warnings": sum(1 for i in issues if i.severity == "warning"),
                "steps": list(self.steps.keys())}

    def _has_cycle(self) -> bool:
        visiting, visited = set(), set()
        def dfs(n):
            if n in visiting: return True
            if n in visited: return False
            visiting.add(n)
            step = self.steps.get(n)
            if step:
                for d in step.depends_on:
                    if dfs(d): return True
            visiting.discard(n)
            visited.add(n)
            return False
        return any(dfs(n) for n in self.steps)

    def to_mermaid(self) -> str:
        lines = ["flowchart TD"]
        for name, step in self.steps.items():
            label = step.tool or step.kind
            outs = ",".join(f"{p.name}:{p.typ}" for p in step.outputs) or "—"
            lines.append(f'  {name}["{name}\\n{label}\\n→ {outs}"]')
        for name, step in self.steps.items():
            for d in step.depends_on:
                lines.append(f"  {d} --> {name}")
        return "\n".join(lines) + "\n"

    def to_dict(self) -> Dict[str, Any]:
        return {"steps": {k: v.to_dict() for k, v in self.steps.items()}, "check": self.check(), "mermaid": self.to_mermaid()}


def graph_from_dense(dense: str) -> TypedGraph:
    from library.dense_ir import parse_dense_line
    steps = parse_dense_line(dense)
    g = TypedGraph()
    prev = None
    tool_out = {
        "search_code": Port("matches", "object"), "project_stats": Port("stats", "object"),
        "calculator": Port("result", "number"), "word_length": Port("length", "number"),
        "now": Port("time", "object"), "codebase_rag": Port("hits", "object"),
        "run_pytest": Port("report", "object"), "scaffold_website": Port("site", "object"),
    }
    for i, s in enumerate(steps):
        name = s.get("name") or f"s{i}"
        op = s.get("op")
        if op == "tool":
            tool = s.get("tool") or "project_stats"
            out = tool_out.get(tool, Port("result", "any"))
            ts = TypedStep(name=name, kind="tool", tool=tool,
                           inputs=[Port("ctx", "any")] if prev else [],
                           outputs=[out], args=s.get("args") or {},
                           depends_on=[prev] if prev else [])
        else:
            ts = TypedStep(name=name, kind="llm",
                           inputs=[Port("context", "any")] if prev else [],
                           outputs=[Port("text", "string")],
                           args={"prompt": s.get("prompt")},
                           depends_on=[prev] if prev else [])
        g.add(ts)
        prev = name
    return g


def demo_typed_graph() -> Dict[str, Any]:
    g = TypedGraph()
    g.add(TypedStep("stats", "tool", tool="project_stats", outputs=[Port("stats", "object")]))
    g.add(TypedStep("search", "tool", tool="search_code", inputs=[Port("stats", "object")],
                    outputs=[Port("matches", "object")], args={"query": "CallResult"}, depends_on=["stats"]))
    g.add(TypedStep("summarize", "llm", inputs=[Port("matches", "object")],
                    outputs=[Port("text", "string")], depends_on=["search"]))
    return g.to_dict()
