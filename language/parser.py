"""
Simple recursive-descent parser for LlmLang.

Supports:
  model name { system: "..." temperature: 0.2 mode: "free" }
  result = model("prompt")
  if conf(x) > 0.8 { ... } else { ... }
  print ..., assert, while, for, def, return, basic expressions
"""

from __future__ import annotations
from typing import List, Optional, Any
import re

from .ast import (
    Program, ModelDecl, Assign, Call, Print, If, While, For,
    Binary, Unary, Literal, Name, Conf, Assert, Return,
    FunctionDef, Block, Node,
)


class ParseError(Exception):
    def __init__(self, message: str, line: int = 0, col: int = 0):
        super().__init__(f"Parse error at {line}:{col}: {message}")
        self.line = line
        self.col = col


class Token:
    def __init__(self, type_: str, value: Any, line: int, col: int):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r})"


KEYWORDS = {
    "model", "if", "else", "while", "for", "in", "def", "return",
    "print", "assert", "true", "false", "null", "and", "or", "not",
    "conf",
}


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line = 1
    col = 1
    n = len(source)

    def peek(k=0):
        return source[i + k] if i + k < n else ""

    def advance():
        nonlocal i, line, col
        ch = source[i]
        i += 1
        if ch == "\n":
            line += 1
            col = 1
        else:
            col += 1
        return ch

    while i < n:
        ch = peek()
        start_line, start_col = line, col

        # whitespace
        if ch.isspace():
            advance()
            continue

        # comments
        if ch == "#":
            while i < n and peek() != "\n":
                advance()
            continue

        # strings
        if ch in ("'\""):
            quote = advance()
            buf = []
            while i < n and peek() != quote:
                if peek() == "\\":
                    advance()
                    esc = advance()
                    buf.append({"n": "\n", "t": "\t", "\\": "\\", quote: quote}.get(esc, esc))
                else:
                    buf.append(advance())
            if i >= n:
                raise ParseError("Unterminated string", start_line, start_col)
            advance()  # closing quote
            tokens.append(Token("STRING", "".join(buf), start_line, start_col))
            continue

        # numbers
        if ch.isdigit() or (ch == "." and peek(1).isdigit()):
            num = []
            while i < n and (peek().isdigit() or peek() == "."):
                num.append(advance())
            text = "".join(num)
            value = float(text) if "." in text else int(text)
            tokens.append(Token("NUMBER", value, start_line, start_col))
            continue

        # identifiers / keywords
        if ch.isalpha() or ch == "_":
            ident = []
            while i < n and (peek().isalnum() or peek() == "_"):
                ident.append(advance())
            text = "".join(ident)
            if text in KEYWORDS:
                tokens.append(Token(text.upper(), text, start_line, start_col))
            else:
                tokens.append(Token("IDENT", text, start_line, start_col))
            continue

        # two-char operators
        two = peek() + peek(1)
        if two in ("==", "!=", "<=", ">=", "&&", "||"):
            advance()
            advance()
            tokens.append(Token("OP", two, start_line, start_col))
            continue

        # single-char
        if ch in "+-*/%<>=!(){}[],.:":
            advance()
            if ch in "(){}[],.:":
                tokens.append(Token(ch, ch, start_line, start_col))
            else:
                tokens.append(Token("OP", ch, start_line, start_col))
            continue

        raise ParseError(f"Unexpected character {ch!r}", start_line, start_col)

    tokens.append(Token("EOF", None, line, col))
    return tokens


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, k=0) -> Token:
        idx = self.pos + k
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        tok = self.current()
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def expect(self, type_: str, value=None) -> Token:
        tok = self.current()
        if tok.type != type_ and (value is None or tok.value != value):
            raise ParseError(
                f"Expected {type_}{(' ' + repr(value)) if value else ''}, got {tok.type} {tok.value!r}",
                tok.line, tok.col,
            )
        return self.advance()

    def match(self, type_: str, value=None) -> bool:
        tok = self.current()
        if tok.type == type_ and (value is None or tok.value == value):
            self.advance()
            return True
        return False

    def parse(self) -> Program:
        stmts = []
        while self.current().type != "EOF":
            stmts.append(self.statement())
        return Program(stmts)

    def statement(self) -> Node:
        tok = self.current()

        if tok.type == "MODEL":
            return self.model_decl()
        if tok.type == "IF":
            return self.if_stmt()
        if tok.type == "WHILE":
            return self.while_stmt()
        if tok.type == "FOR":
            return self.for_stmt()
        if tok.type == "DEF":
            return self.function_def()
        if tok.type == "RETURN":
            return self.return_stmt()
        if tok.type == "PRINT":
            return self.print_stmt()
        if tok.type == "ASSERT":
            return self.assert_stmt()

        # assignment or expression statement
        if tok.type == "IDENT" and self.peek(1).type == "OP" and self.peek(1).value == "=":
            return self.assignment()

        # bare expression (rarely useful, but allow)
        expr = self.expression()
        return expr

    def model_decl(self) -> ModelDecl:
        self.expect("MODEL")
        name = self.expect("IDENT").value
        self.expect("{")
        fields = {}
        while not self.match("}"):
            key = self.expect("IDENT").value
            self.expect(":")
            val = self.expression()
            # evaluate simple literals now for convenience
            if isinstance(val, Literal):
                fields[key] = val.value
            else:
                fields[key] = val  # keep as AST for later
            # optional comma or newline already handled by tokenizer
        return ModelDecl(name=name, fields=fields)

    def assignment(self) -> Assign:
        name = self.expect("IDENT").value
        self.expect("OP", "=")
        value = self.expression()
        return Assign(name=name, value=value)

    def if_stmt(self) -> If:
        self.expect("IF")
        cond = self.expression()
        self.expect("{")
        then_body = self.block_body()
        else_body = []
        if self.match("ELSE"):
            self.expect("{")
            else_body = self.block_body()
        return If(condition=cond, then_body=then_body, else_body=else_body)

    def while_stmt(self) -> While:
        self.expect("WHILE")
        cond = self.expression()
        self.expect("{")
        body = self.block_body()
        return While(condition=cond, body=body)

    def for_stmt(self) -> For:
        self.expect("FOR")
        var = self.expect("IDENT").value
        self.expect("IN")
        iterable = self.expression()
        self.expect("{")
        body = self.block_body()
        return For(var=var, iterable=iterable, body=body)

    def function_def(self) -> FunctionDef:
        self.expect("DEF")
        name = self.expect("IDENT").value
        self.expect("(")
        params = []
        if not self.match(")"):
            while True:
                params.append(self.expect("IDENT").value)
                if self.match(")"):
                    break
                self.expect(",")
        self.expect("{")
        body = self.block_body()
        return FunctionDef(name=name, params=params, body=body)

    def return_stmt(self) -> Return:
        self.expect("RETURN")
        if self.current().type in ("}", "EOF") or self.current().type in KEYWORDS:
            return Return(value=None)
        return Return(value=self.expression())

    def print_stmt(self) -> Print:
        self.expect("PRINT")
        args = [self.expression()]
        while self.match(","):
            args.append(self.expression())
        return Print(args=args)

    def assert_stmt(self) -> Assert:
        self.expect("ASSERT")
        cond = self.expression()
        msg = None
        if self.match(","):
            msg = self.expression()
        return Assert(condition=cond, message=msg)

    def block_body(self) -> List[Node]:
        stmts = []
        while not self.match("}"):
            if self.current().type == "EOF":
                raise ParseError("Unclosed block", self.current().line, self.current().col)
            stmts.append(self.statement())
        return stmts

    # ---- expressions (precedence climbing style) ----

    def expression(self) -> Node:
        return self.or_expr()

    def or_expr(self) -> Node:
        left = self.and_expr()
        while self.current().type == "OR" or (self.current().type == "OP" and self.current().value == "||"):
            self.advance()
            right = self.and_expr()
            left = Binary(op="or", left=left, right=right)
        return left

    def and_expr(self) -> Node:
        left = self.equality()
        while self.current().type == "AND" or (self.current().type == "OP" and self.current().value == "&&"):
            self.advance()
            right = self.equality()
            left = Binary(op="and", left=left, right=right)
        return left

    def equality(self) -> Node:
        left = self.comparison()
        while self.current().type == "OP" and self.current().value in ("==", "!="):
            op = self.advance().value
            right = self.comparison()
            left = Binary(op=op, left=left, right=right)
        return left

    def comparison(self) -> Node:
        left = self.term()
        while self.current().type == "OP" and self.current().value in ("<", ">", "<=", ">="):
            op = self.advance().value
            right = self.term()
            left = Binary(op=op, left=left, right=right)
        return left

    def term(self) -> Node:
        left = self.factor()
        while self.current().type == "OP" and self.current().value in ("+", "-"):
            op = self.advance().value
            right = self.factor()
            left = Binary(op=op, left=left, right=right)
        return left

    def factor(self) -> Node:
        left = self.unary()
        while self.current().type == "OP" and self.current().value in ("*", "/", "%"):
            op = self.advance().value
            right = self.unary()
            left = Binary(op=op, left=left, right=right)
        return left

    def unary(self) -> Node:
        if self.current().type == "NOT" or (self.current().type == "OP" and self.current().value == "-"):
            op = self.advance().value
            if op == "not":
                op = "not"
            return Unary(op=op, operand=self.unary())
        return self.primary()

    def primary(self) -> Node:
        tok = self.current()

        if tok.type == "NUMBER":
            self.advance()
            return Literal(tok.value)
        if tok.type == "STRING":
            self.advance()
            return Literal(tok.value)
        if tok.type == "TRUE":
            self.advance()
            return Literal(True)
        if tok.type == "FALSE":
            self.advance()
            return Literal(False)
        if tok.type == "NULL":
            self.advance()
            return Literal(None)

        if tok.type == "CONF":
            self.advance()
            self.expect("(")
            expr = self.expression()
            self.expect(")")
            return Conf(expr=expr)

        if tok.type == "IDENT":
            name = self.advance().value
            # function / model call
            if self.match("("):
                args = []
                if not self.match(")"):
                    while True:
                        args.append(self.expression())
                        if self.match(")"):
                            break
                        self.expect(",")
                return Call(callee=name, args=args)
            return Name(id=name)

        if self.match("("):
            expr = self.expression()
            self.expect(")")
            return expr

        if self.match("["):
            items = []
            if not self.match("]"):
                while True:
                    items.append(self.expression())
                    if self.match("]"):
                        break
                    self.expect(",")
            # represent list as a special Call for simplicity
            return Call(callee="__list__", args=items)

        raise ParseError(f"Unexpected token {tok.type} {tok.value!r}", tok.line, tok.col)


def parse(source: str) -> Program:
    tokens = tokenize(source)
    return Parser(tokens).parse()
