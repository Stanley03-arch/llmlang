"""Abstract Syntax Tree nodes for LlmLang."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional, Union


@dataclass
class Node:
    pass


@dataclass
class Program(Node):
    statements: List[Node]


@dataclass
class ModelDecl(Node):
    name: str
    fields: dict  # system, temperature, mode, tools, ...


@dataclass
class Assign(Node):
    name: str
    value: Node


@dataclass
class Call(Node):
    callee: str          # model name or function
    args: List[Node]
    kwargs: dict = field(default_factory=dict)


@dataclass
class Print(Node):
    args: List[Node]


@dataclass
class If(Node):
    condition: Node
    then_body: List[Node]
    else_body: List[Node] = field(default_factory=list)


@dataclass
class While(Node):
    condition: Node
    body: List[Node]


@dataclass
class For(Node):
    var: str
    iterable: Node
    body: List[Node]


@dataclass
class Binary(Node):
    op: str
    left: Node
    right: Node


@dataclass
class Unary(Node):
    op: str
    operand: Node


@dataclass
class Literal(Node):
    value: Any


@dataclass
class Name(Node):
    id: str


@dataclass
class Conf(Node):
    expr: Node


@dataclass
class Assert(Node):
    condition: Node
    message: Optional[Node] = None


@dataclass
class Return(Node):
    value: Optional[Node] = None


@dataclass
class FunctionDef(Node):
    name: str
    params: List[str]
    body: List[Node]


@dataclass
class Block(Node):
    statements: List[Node]
