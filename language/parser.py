"""
Recursive-descent parser for LlmLang v0.2.

Supports models, conf control-flow, try/catch, parallel, import,
functions, tools, indexing, ternary, and basic expressions.
"""

from __future__ import annotations
from typing import List, Optional, Any

from .ast import (
    Program, ModelDecl, Assign, IndexAssign, Call, Print, If, While, For,
    TryCatch, Parallel, Binary, Unary, Literal, Name, Index, Conf, Assert,
    Return, FunctionDef, Import, Ternary, Block, Node,
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
    "conf", "try", "catch", "parallel", "import",
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

        if ch.isspace():
            advance()
            continue

        if ch == "#":
            while i < n and peek() != "\n":
                advance()
            continue

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
            advance()
            tokens.append(Token("STRING", "".join(buf), start_line, start_col))
            continue

        if ch.isdigit() or (ch == "." and peek(1).isdigit()):
            num = []
            while i < n and (peek().isdigit() or peek() == "."):
                num.append(advance())
            text = "".join(num)
            value = float(text) if "." in text else int(text)
            tokens.append(Token("NUMBER", value, start_line, start_col))
            continue

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

        # ternary ?
        if ch == "?":
            advance()
            tokens.append(Token("?", "?", start_line, start_col))
            continue

        two = peek() + peek(1)
        if two in ("==", "!=", "<=", ">=", "&&", "||"):
            advance()
            advance()
            tokens.append(Token("OP", two, start_line, start_col))
            continue

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
        if tok.type == "TRY":
            return self.try_stmt()
        if tok.type == "PARALLEL":
            return self.parallel_stmt()
        if tok.type == "IMPORT":
            return self.import_stmt()
        if tok.type == "DEF":
            return self.function_def()
        if tok.type == "RETURN":
            return self.return_stmt()
        if tok.type == "PRINT":
            return self.print_stmt()
        if tok.type == "ASSERT":
            return self.assert_stmt()

        # index assign: xs[0] = 1
        if tok.type == "IDENT" and self.peek(1).type == "[":
            # look ahead for ] = 
            saved = self.pos
            try:
                target = self.postfix_primary()
                if self.current().type == "OP" and self.current().value == "=":
                    self.advance()
                    value = self.expression()
                    if isinstance(target, Index):
                        return IndexAssign(target=target.target, index=target.index, value=value)
            except ParseError:
                pass
            self.pos = saved

        if tok.type == "IDENT" and self.peek(1).type == "OP" and self.peek(1).value == "=":
            return self.assignment()

        return self.expression()

    def model_decl(self) -> ModelDecl:
        self.expect("MODEL")
        name = self.expect("IDENT").value
        self.expect("{")
        fields = {}
        while not self.match("}"):
            key = self.expect("IDENT").value
            self.expect(":")
            val = self.expression()
            if isinstance(val, Literal):
                fields[key] = val.value
            elif isinstance(val, Call) and val.callee == "__list__":
                # tools: ["a" "b"] style — evaluate list of literals if possible
                items = []
                for a in val.args:
                    items.append(a.value if isinstance(a, Literal) else a)
                fields[key] = items
            else:
                fields[key] = val
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

    def try_stmt(self) -> TryCatch:
        self.expect("TRY")
        self.expect("{")
        try_body = self.block_body()
        catch_var = None
        catch_body = []
        if self.match("CATCH"):
            if self.current().type == "IDENT":
                catch_var = self.advance().value
            self.expect("{")
            catch_body = self.block_body()
        return TryCatch(try_body=try_body, catch_var=catch_var, catch_body=catch_body)

    def parallel_stmt(self) -> Parallel:
        self.expect("PARALLEL")
        self.expect("{")
        body = self.block_body()
        return Parallel(body=body)

    def import_stmt(self) -> Import:
        self.expect("IMPORT")
        path = self.expect("STRING").value
        return Import(path=path)

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
        if self.current().type in ("}", "EOF") or (
            self.current().type in {k.upper() for k in KEYWORDS} and self.current().type not in ("TRUE", "FALSE", "NULL", "CONF")
        ):
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

    # ---- expressions ----

    def expression(self) -> Node:
        return self.ternary()

    def ternary(self) -> Node:
        cond = self.or_expr()
        if self.match("?"):
            then_e = self.expression()
            self.expect(":")
            else_e = self.expression()
            return Ternary(condition=cond, then_expr=then_e, else_expr=else_e)
        return cond

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
        return self.postfix_primary()

    def postfix_primary(self) -> Node:
        node = self.primary()
        while True:
            if self.match("["):
                idx = self.expression()
                self.expect("]")
                node = Index(target=node, index=idx)
            else:
                break
        return node

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
            return Call(callee="__list__", args=items)

        if self.match("{"):
            # simple dict: { "k": v, ... }  or empty {}
            pairs = []
            if not self.match("}"):
                while True:
                    key = self.expression()
                    self.expect(":")
                    val = self.expression()
                    pairs.append((key, val))
                    if self.match("}"):
                        break
                    self.expect(",")
            # encode as special call
            flat = []
            for k, v in pairs:
                flat.extend([k, v])
            return Call(callee="__dict__", args=flat)

        raise ParseError(f"Unexpected token {tok.type} {tok.value!r}", tok.line, tok.col)


def parse(source: str) -> Program:
    tokens = tokenize(source)
    return Parser(tokens).parse()
