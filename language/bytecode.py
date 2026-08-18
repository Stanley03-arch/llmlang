"""LlmLang bytecode + compiler + VM (pure subset, v0.1)."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import IntEnum, auto
import operator

from language.parser import parse
from language.ast_nodes import (
    Program, Assign, Print, SoftIf, HardIf, WhileLoop, Literal, Var, BinaryOp, UnaryOp,
    ListLiteral, Index, ForLoop, FuncDef, Return, Assert, ModelDecl, Parallel, TryCatch, Import,
)


class Op(IntEnum):
    LOAD_CONST = auto()
    LOAD_NAME = auto()
    STORE_NAME = auto()
    BINARY_ADD = auto()
    BINARY_SUB = auto()
    BINARY_MUL = auto()
    BINARY_DIV = auto()
    BINARY_MOD = auto()
    BINARY_EQ = auto()
    BINARY_NE = auto()
    BINARY_LT = auto()
    BINARY_LE = auto()
    BINARY_GT = auto()
    BINARY_GE = auto()
    BINARY_AND = auto()
    BINARY_OR = auto()
    UNARY_NEG = auto()
    UNARY_NOT = auto()
    UNARY_LEN = auto()
    BUILD_LIST = auto()
    GET_ITEM = auto()
    JUMP = auto()
    JUMP_IF_FALSE = auto()
    PRINT = auto()
    POP = auto()
    RETURN = auto()


BIN_OPS = {
    "+": Op.BINARY_ADD, "-": Op.BINARY_SUB, "*": Op.BINARY_MUL, "/": Op.BINARY_DIV, "%": Op.BINARY_MOD,
    "==": Op.BINARY_EQ, "!=": Op.BINARY_NE, "<": Op.BINARY_LT, "<=": Op.BINARY_LE,
    ">": Op.BINARY_GT, ">=": Op.BINARY_GE, "and": Op.BINARY_AND, "or": Op.BINARY_OR,
}


@dataclass
class CodeObject:
    names: List[str] = field(default_factory=list)
    consts: List[Any] = field(default_factory=list)
    code: List[Tuple] = field(default_factory=list)

    def dis(self) -> str:
        lines = []
        for i, instr in enumerate(self.code):
            op, arg = instr[0], instr[1] if len(instr) > 1 else None
            extra = ""
            if op == Op.LOAD_CONST and arg is not None:
                extra = f"  # {self.consts[arg]!r}"
            elif op in (Op.LOAD_NAME, Op.STORE_NAME) and arg is not None:
                extra = f"  # {self.names[arg]}"
            elif op in (Op.JUMP, Op.JUMP_IF_FALSE) and arg is not None:
                extra = f"  # -> {arg}"
            lines.append(f"{i:4d} {op.name:<16} {arg if arg is not None else ''}{extra}")
        return "\n".join(lines)


class CompilerError(Exception):
    pass


class Compiler:
    def __init__(self):
        self.names: List[str] = []
        self.consts: List[Any] = []
        self.code: List[Tuple] = []
        self.name_index: Dict[str, int] = {}
        self.const_index: Dict[str, int] = {}

    def _name(self, n: str) -> int:
        if n not in self.name_index:
            self.name_index[n] = len(self.names)
            self.names.append(n)
        return self.name_index[n]

    def _const(self, v: Any) -> int:
        key = repr(v)
        if key not in self.const_index:
            self.const_index[key] = len(self.consts)
            self.consts.append(v)
        return self.const_index[key]

    def emit(self, op: Op, arg: Any = None):
        self.code.append((op, arg))

    def compile_program(self, prog: Program) -> CodeObject:
        for stmt in prog.statements:
            self.compile_stmt(stmt)
        self.emit(Op.LOAD_CONST, self._const(None))
        self.emit(Op.RETURN)
        return CodeObject(names=self.names, consts=self.consts, code=self.code)

    def compile_stmt(self, node):
        if isinstance(node, Assign):
            self.compile_expr(node.value)
            self.emit(Op.STORE_NAME, self._name(node.name))
        elif isinstance(node, Print):
            self.compile_expr(node.value)
            self.emit(Op.PRINT)
        elif isinstance(node, SoftIf):
            raise CompilerError("soft-if not in pure VM; use if expr { }")
        elif isinstance(node, HardIf):
            self.compile_expr(node.condition)
            jif = len(self.code)
            self.emit(Op.JUMP_IF_FALSE, None)
            for s in node.then_body:
                self.compile_stmt(s)
            if node.else_body:
                jend = len(self.code)
                self.emit(Op.JUMP, None)
                self.code[jif] = (Op.JUMP_IF_FALSE, len(self.code))
                for s in node.else_body:
                    self.compile_stmt(s)
                self.code[jend] = (Op.JUMP, len(self.code))
            else:
                self.code[jif] = (Op.JUMP_IF_FALSE, len(self.code))
        elif isinstance(node, WhileLoop):
            loop_start = len(self.code)
            self.compile_expr(node.condition)
            jif = len(self.code)
            self.emit(Op.JUMP_IF_FALSE, None)
            for s in node.body:
                self.compile_stmt(s)
            self.emit(Op.JUMP, loop_start)
            self.code[jif] = (Op.JUMP_IF_FALSE, len(self.code))
        elif isinstance(node, Assert):
            self.compile_expr(node.condition)
            self.emit(Op.POP)
        elif isinstance(node, (FuncDef, ForLoop)):
            raise CompilerError(f"{type(node).__name__} not in VM v0.1")
        elif isinstance(node, Return):
            self.compile_expr(node.value)
            self.emit(Op.RETURN)
        else:
            raise CompilerError(f"unsupported statement: {type(node).__name__}")

    def compile_expr(self, node):
        if isinstance(node, Literal):
            self.emit(Op.LOAD_CONST, self._const(node.value))
        elif isinstance(node, Var):
            self.emit(Op.LOAD_NAME, self._name(node.name))
        elif isinstance(node, BinaryOp):
            if node.op not in BIN_OPS:
                raise CompilerError(f"unsupported op {node.op}")
            self.compile_expr(node.left)
            self.compile_expr(node.right)
            self.emit(BIN_OPS[node.op])
        elif isinstance(node, UnaryOp):
            self.compile_expr(node.operand)
            if node.op in ("-", "neg"):
                self.emit(Op.UNARY_NEG)
            elif node.op in ("not", "!"):
                self.emit(Op.UNARY_NOT)
            elif node.op == "len":
                self.emit(Op.UNARY_LEN)
            else:
                raise CompilerError(f"unsupported unary {node.op}")
        elif isinstance(node, ListLiteral):
            for e in node.elements:
                self.compile_expr(e)
            self.emit(Op.BUILD_LIST, len(node.elements))
        elif isinstance(node, Index):
            self.compile_expr(node.target)
            self.compile_expr(node.index)
            self.emit(Op.GET_ITEM)
        else:
            raise CompilerError(f"unsupported expr: {type(node).__name__}")


OPS_IMPL = {
    Op.BINARY_ADD: operator.add, Op.BINARY_SUB: operator.sub, Op.BINARY_MUL: operator.mul,
    Op.BINARY_DIV: operator.truediv, Op.BINARY_MOD: operator.mod,
    Op.BINARY_EQ: operator.eq, Op.BINARY_NE: operator.ne, Op.BINARY_LT: operator.lt,
    Op.BINARY_LE: operator.le, Op.BINARY_GT: operator.gt, Op.BINARY_GE: operator.ge,
}


@dataclass
class VMResult:
    ok: bool
    value: Any = None
    output: List[str] = field(default_factory=list)
    error: Optional[str] = None
    steps: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "value": self.value, "output": self.output, "error": self.error, "steps": self.steps}


class VM:
    def __init__(self, code: CodeObject, max_steps: int = 100_000):
        self.code = code
        self.max_steps = max_steps

    def execute(self, env: Optional[Dict[str, Any]] = None) -> VMResult:
        stack: List[Any] = []
        names = list(self.code.names)
        locals_map: Dict[str, Any] = dict(env or {})
        output: List[str] = []
        ip = 0
        steps = 0
        instructions = self.code.code
        try:
            while ip < len(instructions):
                steps += 1
                if steps > self.max_steps:
                    return VMResult(ok=False, error="max steps exceeded", output=output, steps=steps)
                op, arg = instructions[ip][0], instructions[ip][1]
                ip += 1
                if op == Op.LOAD_CONST:
                    stack.append(self.code.consts[arg])
                elif op == Op.LOAD_NAME:
                    n = names[arg]
                    if n not in locals_map:
                        return VMResult(ok=False, error=f"undefined name '{n}'", output=output, steps=steps)
                    stack.append(locals_map[n])
                elif op == Op.STORE_NAME:
                    locals_map[names[arg]] = stack.pop()
                elif op in OPS_IMPL:
                    b, a = stack.pop(), stack.pop()
                    stack.append(OPS_IMPL[op](a, b))
                elif op == Op.BINARY_AND:
                    b, a = stack.pop(), stack.pop()
                    stack.append(bool(a) and bool(b))
                elif op == Op.BINARY_OR:
                    b, a = stack.pop(), stack.pop()
                    stack.append(bool(a) or bool(b))
                elif op == Op.UNARY_NEG:
                    stack.append(-stack.pop())
                elif op == Op.UNARY_NOT:
                    stack.append(not stack.pop())
                elif op == Op.UNARY_LEN:
                    stack.append(len(stack.pop()))
                elif op == Op.BUILD_LIST:
                    n = arg or 0
                    items = [stack.pop() for _ in range(n)]
                    items.reverse()
                    stack.append(items)
                elif op == Op.GET_ITEM:
                    idx, xs = stack.pop(), stack.pop()
                    stack.append(xs[idx])
                elif op == Op.JUMP:
                    ip = arg
                elif op == Op.JUMP_IF_FALSE:
                    if not stack.pop():
                        ip = arg
                elif op == Op.PRINT:
                    output.append(str(stack.pop()))
                elif op == Op.POP:
                    if stack:
                        stack.pop()
                elif op == Op.RETURN:
                    val = stack.pop() if stack else None
                    return VMResult(ok=True, value=val, output=output, steps=steps)
                else:
                    return VMResult(ok=False, error=f"unknown opcode {op}", output=output, steps=steps)
            return VMResult(ok=True, value=stack[-1] if stack else None, output=output, steps=steps)
        except Exception as e:
            return VMResult(ok=False, error=f"{type(e).__name__}: {e}", output=output, steps=steps)


def compile_source(source: str) -> CodeObject:
    prog = parse(source)
    for stmt in prog.statements:
        if isinstance(stmt, (ModelDecl, Parallel, TryCatch, Import)):
            raise CompilerError(f"{type(stmt).__name__} not allowed in pure VM programs")
    return Compiler().compile_program(prog)


def run_bytecode(source: str, env: Optional[Dict[str, Any]] = None) -> VMResult:
    try:
        code = compile_source(source)
    except Exception as e:
        return VMResult(ok=False, error=str(e))
    return VM(code).execute(env)


def disassemble(source: str) -> str:
    return compile_source(source).dis()
