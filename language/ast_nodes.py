"""
Abstract Syntax Tree nodes for LlmLang.
Now includes: functions, lists, indexing, parallel blocks, for-loops.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Union


@dataclass
class Node:
    pass


@dataclass
class Program(Node):
    statements: List[Node]


@dataclass
class ModelDecl(Node):
    name: str
    system: str = "You are a careful assistant."
    temperature: float = 0.2
    mode: str = "free"
    tools: List[str] = field(default_factory=list)
    schema_name: Optional[str] = None


@dataclass
class Assign(Node):
    name: str
    value: Node


@dataclass
class ModelCall(Node):
    model: str
    prompt: Node
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CriticCall(Node):
    model: str
    target: str
    question: Optional[str] = None


@dataclass
class SoftIf(Node):
    condition_var: str
    threshold: float
    then_body: List[Node]
    else_body: List[Node] = field(default_factory=list)


@dataclass
class Return(Node):
    value: Node


@dataclass
class Literal(Node):
    value: Any


@dataclass
class Var(Node):
    name: str


@dataclass
class BinaryOp(Node):
    op: str
    left: Node
    right: Node


@dataclass
class Print(Node):
    value: Node


@dataclass
class ListLiteral(Node):
    elements: List[Node]


@dataclass
class Index(Node):
    target: Node
    index: Node


@dataclass
class AssignIndex(Node):
    target: Index
    value: Node


@dataclass
class FuncDef(Node):
    name: str
    params: List[str]
    body: List[Node]


@dataclass
class FuncCall(Node):
    name: str
    args: List[Node]


@dataclass
class Parallel(Node):
    statements: List[Node]


@dataclass
class ForLoop(Node):
    var: str
    iterable: Node
    body: List[Node]


@dataclass
class UnaryOp(Node):
    op: str
    operand: Node


@dataclass
class DictLiteral(Node):
    pairs: List[tuple]


@dataclass
class WhileLoop(Node):
    condition: Node
    body: List[Node]


@dataclass
class Import(Node):
    path: str


@dataclass
class SoftElif(Node):
    pass


@dataclass
class Assert(Node):
    condition: Node
    message: Optional[str] = None


@dataclass
class Break(Node):
    pass


@dataclass
class Continue(Node):
    pass


@dataclass
class Ternary(Node):
    condition: Node
    then_value: Node
    else_value: Node


@dataclass
class TryCatch(Node):
    try_body: List[Node]
    catch_var: Optional[str]
    catch_body: List[Node]
