"""Direct LlmLang → Go source codegen for pure numeric/control subset."""

from __future__ import annotations
from typing import List, Set
from language.parser import parse
from language.ast_nodes import *


class CodegenError(Exception):
    pass


def codegen_go(source: str, package: str = "main") -> str:
    prog = parse(source)
    names: Set[str] = set()
    _collect_names(prog, names)
    body: List[str] = []
    for stmt in prog.statements:
        body.extend(_stmt(stmt, 1))
    lines = [
        f"package {package}", "",
        "import (", '\t"fmt"', '\t"encoding/json"', '\t"time"', ")", "",
        "func main() {",
        "\tt0 := time.Now()",
        "\tvar output []string",
    ]
    for n in sorted(names):
        lines.append(f"\tvar {n} float64")
    lines.append("")
    lines.extend(body)
    lines += [
        "\tres := map[string]interface{}{",
        '\t\t"ok": true,',
        '\t\t"output": output,',
        '\t\t"ms": float64(time.Since(t0).Microseconds()) / 1000.0,',
        "\t}",
        '\tb, _ := json.MarshalIndent(res, "", "  ")',
        "\tfmt.Println(string(b))",
        "}", "",
    ]
    return "\n".join(lines)


def _collect_names(prog, names: Set[str]):
    for stmt in prog.statements:
        _collect_stmt(stmt, names)


def _collect_stmt(node, names: Set[str]):
    if isinstance(node, Assign):
        names.add(node.name)
        _collect_expr(node.value, names)
    elif isinstance(node, Print):
        _collect_expr(node.value, names)
    elif isinstance(node, HardIf):
        _collect_expr(node.condition, names)
        for s in node.then_body + node.else_body:
            _collect_stmt(s, names)
    elif isinstance(node, WhileLoop):
        _collect_expr(node.condition, names)
        for s in node.body:
            _collect_stmt(s, names)
    elif isinstance(node, (SoftIf, ModelDecl)):
        raise CodegenError("not in native codegen")


def _collect_expr(node, names: Set[str]):
    if isinstance(node, Var):
        names.add(node.name)
    elif isinstance(node, BinaryOp):
        _collect_expr(node.left, names)
        _collect_expr(node.right, names)
    elif isinstance(node, UnaryOp):
        _collect_expr(node.operand, names)


def _stmt(node, ind: int) -> List[str]:
    p = "\t" * ind
    if isinstance(node, Assign):
        return [f"{p}{node.name} = {_expr(node.value)}"]
    if isinstance(node, Print):
        return [
            f"{p}{{",
            f"{p}\tv := {_expr(node.value)}",
            f"{p}\tif v == float64(int64(v)) {{",
            f"{p}\t\toutput = append(output, fmt.Sprintf(\"%d\", int64(v)))",
            f"{p}\t}} else {{",
            f"{p}\t\toutput = append(output, fmt.Sprint(v))",
            f"{p}\t}}",
            f"{p}}}",
        ]
    if isinstance(node, WhileLoop):
        out = [f"{p}for {_expr(node.condition)} {{"]
        for s in node.body:
            out.extend(_stmt(s, ind + 1))
        out.append(f"{p}}}")
        return out
    if isinstance(node, HardIf):
        out = [f"{p}if {_expr(node.condition)} {{"]
        for s in node.then_body:
            out.extend(_stmt(s, ind + 1))
        if node.else_body:
            out.append(f"{p}}} else {{")
            for s in node.else_body:
                out.extend(_stmt(s, ind + 1))
        out.append(f"{p}}}")
        return out
    raise CodegenError(f"unsupported {type(node).__name__}")


def _expr(node) -> str:
    if isinstance(node, Literal):
        v = node.value
        if isinstance(v, bool):
            return "1.0" if v else "0.0"
        if v is None:
            return "0.0"
        if isinstance(v, str):
            raise CodegenError("strings: use VM path")
        return f"{float(v)}"
    if isinstance(node, Var):
        return node.name
    if isinstance(node, BinaryOp):
        l, r = _expr(node.left), _expr(node.right)
        op = node.op
        if op in ("+", "-", "*", "/"):
            return f"({l} {op} {r})"
        if op == "%":
            return f"float64(int64({l}) % int64({r}))"
        if op == "==":
            return f"({l} == {r})"
        if op == "!=":
            return f"({l} != {r})"
        if op == "<":
            return f"({l} < {r})"
        if op == "<=":
            return f"({l} <= {r})"
        if op == ">":
            return f"({l} > {r})"
        if op == ">=":
            return f"({l} >= {r})"
        if op == "and":
            return f"(({l} != 0) && ({r} != 0))"
        if op == "or":
            return f"(({l} != 0) || ({r} != 0))"
        raise CodegenError(f"op {op}")
    if isinstance(node, UnaryOp):
        if node.op in ("-", "neg"):
            return f"(-{_expr(node.operand)})"
        if node.op in ("not", "!"):
            return f"(({_expr(node.operand)} == 0))"
        raise CodegenError(f"unary {node.op}")
    raise CodegenError(f"expr {type(node).__name__}")
