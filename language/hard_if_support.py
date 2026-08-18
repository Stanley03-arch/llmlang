"""Ensure HardIf parsing is available (foundation patch for pure if)."""
from __future__ import annotations

def ensure_hard_if():
    from language import ast_nodes
    if not hasattr(ast_nodes, "HardIf"):
        from dataclasses import dataclass, field
        @dataclass
        class HardIf(ast_nodes.Node):
            condition: object
            then_body: list
            else_body: list = field(default_factory=list)
        ast_nodes.HardIf = HardIf

    from language import parser as P
    if not hasattr(P.Parser, "hard_if"):
        def hard_if(self):
            from language.ast_nodes import HardIf
            self.tok.expect("IDENT", "if")
            cond = self.expr()
            then_body = self.block()
            else_body = []
            if self.tok.peek() and self.tok.peek()[1] == "else":
                self.tok.next()
                else_body = self.block()
            return HardIf(cond, then_body, else_body)
        P.Parser.hard_if = hard_if
        _orig = P.Parser.statement
        def statement(self):
            tok = self.tok.peek()
            if tok and tok[0] == "IDENT" and tok[1] == "if":
                nxt = self.tok.tokens[self.tok.pos + 1] if self.tok.pos + 1 < len(self.tok.tokens) else None
                if nxt and nxt[1] == "conf":
                    return self.soft_if()
                return self.hard_if()
            return _orig(self)
        P.Parser.statement = statement

ensure_hard_if()
