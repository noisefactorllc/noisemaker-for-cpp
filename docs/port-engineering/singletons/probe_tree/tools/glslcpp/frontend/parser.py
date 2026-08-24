"""GLSL ES 3.00 recursive-descent parser -> clean AST.

AST nodes are dicts with a "k" (kind) field. Consumes tokens from lexer.tokenize
on already-preprocessed GLSL (no #directives, no structs beyond flat ones).
"""

from __future__ import annotations

from typing import ClassVar

from .lexer import tokenize


class Node(dict):
    """Parser-private mapping carrying a source range outside its keys."""

    __slots__ = ("start", "end")

    def __init__(self, values, start: int, end: int):
        super().__init__(values)
        self.start = start
        self.end = end

SCALAR = {"void", "bool", "int", "uint", "float"}
VEC = {f"{p}vec{n}" for p in ("", "i", "u", "b") for n in (2, 3, 4)}
MAT = {f"mat{n}" for n in (2, 3, 4)} | {f"mat{a}x{b}" for a in (2, 3, 4) for b in (2, 3, 4)}
SAMPLER = {"sampler2D", "sampler3D", "samplerCube", "sampler2DArray"}
TYPES = SCALAR | VEC | MAT | SAMPLER

QUALIFIERS = {
    "const",
    "uniform",
    "in",
    "out",
    "inout",
    "flat",
    "smooth",
    "noperspective",
    "centroid",
    "invariant",
    "highp",
    "mediump",
    "lowp",
    "precise",
}
CONTROL = {"if", "else", "for", "while", "do", "return", "break", "continue", "discard", "struct"}

_ASSIGN = {"=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="}


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0
        self.struct_types = set()

    def node(self, start: int, values: dict) -> Node:
        """Build a private AST node with exact token-derived character bounds."""
        end_token = self.toks[max(0, self.i - 1)]
        return Node(values, start, end_token.pos + len(end_token.value))

    @staticmethod
    def start_of(value, fallback: int) -> int:
        return value.start if isinstance(value, Node) else fallback

    # ---- cursor ----
    def peek(self, k=0):
        return self.toks[self.i + k]

    def at(self, value):
        t = self.toks[self.i]
        return t.value == value

    def at_type(self):
        t = self.toks[self.i]
        return t.kind == "id" and (t.value in TYPES or t.value in self.struct_types)

    def next(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect(self, value):
        t = self.toks[self.i]
        if t.value != value:
            raise SyntaxError(f"expected {value!r} got {t.value!r} at token {self.i}")
        self.i += 1
        return t

    def eat(self, value):
        if self.toks[self.i].value == value:
            self.i += 1
            return True
        return False

    # ---- top level ----
    def parse_program(self):
        start = self.peek().pos
        decls = []
        while not self.at("<eof>"):
            d = self.external_decl()
            if d is not None:
                decls.append(d)
        return self.node(start, {"k": "program", "decls": decls})

    def external_decl(self):
        start = self.peek().pos
        if self.at("precision"):
            self.next()
            qualifier = self.next().value
            base_type = self.next().value
            if qualifier not in {"highp", "mediump", "lowp"} or base_type not in {"int", "float"}:
                raise SyntaxError(f"invalid precision declaration at token {self.i - 1}")
            self.expect(";")
            return None
        if self.at("struct"):
            return self.struct_decl()
        # skip layout(...) qualifier prefixes
        quals = self.qualifiers()
        # interface (uniform) block: `uniform Name { members } [inst];`
        if "uniform" in quals and self.peek().kind == "id" and self.peek(1).value == "{":
            node = self.uniform_block(); node.start = start; return node
        typ = self.type_spec()
        # function or variable?
        name = self.next().value
        if self.at("("):
            node = self.function_rest(typ, name, quals); node.start = start; return node
        node = self.var_decl_rest(typ, name, quals, top=True); node.start = start; return node

    def uniform_block(self):
        start = self.peek().pos
        block_name = self.next().value
        self.expect("{")
        members = []
        while not self.at("}"):
            self.qualifiers()
            member_start = self.peek().pos
            mtype = self.type_spec()
            mname = self.next().value
            arr = None
            if self.eat("["):
                arr = self.expr()
                self.expect("]")
            members.append(self.node(member_start, {"type": mtype, "name": mname, "array": arr}))
            self.expect(";")
        self.expect("}")
        inst = None
        if self.peek().kind == "id":
            inst = self.next().value
        self.expect(";")
        return self.node(start, {"k": "ubo", "name": block_name, "members": members, "inst": inst})

    def qualifiers(self):
        q = []
        while True:
            t = self.peek()
            if t.value == "layout":
                self.next()
                self.expect("(")
                depth = 1
                while depth:
                    v = self.next().value
                    if v == "(":
                        depth += 1
                    elif v == ")":
                        depth -= 1
                continue
            if t.kind == "id" and t.value in QUALIFIERS:
                q.append(self.next().value)
                continue
            break
        return q

    def type_spec(self):
        t = self.next()
        return t.value

    def struct_decl(self):
        start = self.peek().pos
        self.expect("struct")
        name = self.next().value
        self.struct_types.add(name)
        self.expect("{")
        fields = []
        while not self.at("}"):
            self.qualifiers()
            field_start = self.peek().pos
            ftype = self.type_spec()
            fname = self.next().value
            arr = None
            if self.eat("["):
                arr = self.expr()
                self.expect("]")
            fields.append(self.node(field_start, {"type": ftype, "name": fname, "array": arr}))
            self.expect(";")
        self.expect("}")
        # optional instance name: `struct S {...} inst;`
        inst = None
        if self.peek().kind == "id":
            inst = self.next().value
        self.expect(";")
        return self.node(start, {"k": "struct", "name": name, "fields": fields, "inst": inst})

    def function_rest(self, ret, name, quals):
        start = self.toks[self.i - 2].pos
        self.expect("(")
        params = []
        if not self.at(")"):
            while True:
                parameter_start = self.peek().pos
                pquals = self.qualifiers()
                if self.at("void") and self.peek(1).value == ")":
                    self.next()
                    break
                ptype = self.type_spec()
                pname = self.next().value if self.peek().kind == "id" else None
                array = None
                if self.eat("["):
                    array = self.expr()
                    self.expect("]")
                params.append(self.node(parameter_start, {"type": ptype, "name": pname, "quals": pquals, "array": array}))
                if not self.eat(","):
                    break
        self.expect(")")
        if self.eat(";"):  # prototype
            return self.node(start, {"k": "proto", "ret": ret, "name": name, "params": params})
        body = self.block()
        return self.node(start, {"k": "func", "ret": ret, "name": name, "params": params, "body": body})

    def var_decl_rest(self, typ, name, quals, top=False):
        start = self.toks[self.i - 2].pos
        declarator_start = self.toks[self.i - 1].pos
        declarators = []
        while True:
            arr = None
            if self.eat("["):
                arr = True if self.at("]") else self.expr()
                self.expect("]")
            init = None
            if self.eat("="):
                init = self.assign_expr()
            declarators.append(self.node(declarator_start, {"name": name, "array": arr, "init": init}))
            if not self.eat(","):
                break
            next_name = self.next()
            name = next_name.value
            declarator_start = next_name.pos
        self.expect(";")
        return self.node(start, {"k": "decl", "type": typ, "quals": quals, "declarators": declarators, "top": top})

    # ---- statements ----
    def block(self):
        self.expect("{")
        stmts = []
        while not self.at("}"):
            stmts.append(self.statement())
        self.expect("}")
        return stmts

    def statement(self):
        t = self.peek()
        if t.value == "{":
            start = t.pos
            return self.node(start, {"k": "block", "body": self.block()})
        if t.value == "if":
            return self.if_stmt()
        if t.value == "for":
            return self.for_stmt()
        if t.value == "while":
            start = t.pos
            self.next()
            self.expect("(")
            cond = self.expr()
            self.expect(")")
            return self.node(start, {"k": "while", "cond": cond, "body": self.statement()})
        if t.value == "do":
            start = t.pos
            self.next()
            body = self.statement()
            self.expect("while")
            self.expect("(")
            cond = self.expr()
            self.expect(")")
            self.expect(";")
            return self.node(start, {"k": "dowhile", "cond": cond, "body": body})
        if t.value == "return":
            start = t.pos
            self.next()
            val = None if self.at(";") else self.expr()
            self.expect(";")
            return self.node(start, {"k": "return", "value": val})
        if t.value == "break":
            start = t.pos
            self.next()
            self.expect(";")
            return self.node(start, {"k": "break"})
        if t.value == "continue":
            start = t.pos
            self.next()
            self.expect(";")
            return self.node(start, {"k": "continue"})
        if t.value == "discard":
            start = t.pos
            self.next()
            self.expect(";")
            return self.node(start, {"k": "discard"})
        # declaration vs expression: [const] TYPE ident ...
        if self.at_decl_start():
            quals = self.qualifiers()
            typ = self.type_spec()
            name = self.next().value
            return self.var_decl_rest(typ, name, quals)
        start = t.pos
        e = self.expr()
        self.expect(";")
        return self.node(start, {"k": "expr", "expr": e})

    def at_decl_start(self):
        t = self.peek()
        if t.kind != "id":
            return False
        if t.value in QUALIFIERS:
            return True
        if t.value in TYPES or t.value in self.struct_types:
            # a type keyword followed by an ident (decl) or by `(` (constructor expr)
            return self.peek(1).kind == "id"
        return False

    def if_stmt(self):
        start = self.next().pos
        self.expect("(")
        cond = self.expr()
        self.expect(")")
        then = self.statement()
        els = None
        if self.eat("else"):
            els = self.statement()
        return self.node(start, {"k": "if", "cond": cond, "then": then, "els": els})

    def for_stmt(self):
        start = self.next().pos
        self.expect("(")
        if self.eat(";"):
            init = None
        elif self.at_decl_start():
            quals = self.qualifiers()
            typ = self.type_spec()
            name = self.next().value
            init = self.var_decl_rest(typ, name, quals)
        else:
            expr_start = self.peek().pos
            init = self.node(expr_start, {"k": "expr", "expr": self.expr()})
            self.expect(";")
        cond = None if self.at(";") else self.expr()
        self.expect(";")
        update = None if self.at(")") else self.expr()
        self.expect(")")
        body = self.statement()
        return self.node(start, {"k": "for", "init": init, "cond": cond, "update": update, "body": body})

    # ---- expressions (precedence climbing) ----
    def expr(self):
        e = self.assign_expr()
        while self.at(","):  # comma operator: keep last
            self.next()
            e = self.assign_expr()
        return e

    def assign_expr(self):
        left = self.conditional()
        if self.peek().value in _ASSIGN:
            op = self.next().value
            right = self.assign_expr()
            return self.node(self.start_of(left, self.peek().pos), {"k": "assign", "op": op, "target": left, "value": right})
        return left

    def conditional(self):
        c = self.binary(0)
        if self.eat("?"):
            a = self.expr()
            self.expect(":")
            b = self.assign_expr()
            return self.node(self.start_of(c, self.peek().pos), {"k": "cond", "c": c, "a": a, "b": b})
        return c

    _BIN: ClassVar = [
        {"||"},
        {"&&"},
        {"|"},
        {"^"},
        {"&"},
        {"==", "!="},
        {"<", ">", "<=", ">="},
        {"<<", ">>"},
        {"+", "-"},
        {"*", "/", "%"},
    ]

    def binary(self, level):
        if level >= len(self._BIN):
            return self.unary()
        left = self.binary(level + 1)
        while self.peek().value in self._BIN[level]:
            op = self.next().value
            right = self.binary(level + 1)
            left = self.node(self.start_of(left, self.peek().pos), {"k": "binary", "op": op, "l": left, "r": right})
        return left

    def unary(self):
        t = self.peek()
        if t.value in ("+", "-", "!", "~", "++", "--"):
            self.next()
            return self.node(t.pos, {"k": "unary", "op": t.value, "x": self.unary()})
        return self.postfix()

    def postfix(self):
        e = self.primary()
        while True:
            t = self.peek()
            if t.value == ".":
                self.next()
                field = self.next().value
                if self.at("(") and field == "length":  # arr.length() -> array size
                    self.expect("(")
                    self.expect(")")
                    e = self.node(self.start_of(e, t.pos), {"k": "call", "name": "__array_length", "args": [e]})
                else:
                    e = self.node(self.start_of(e, t.pos), {"k": "member", "obj": e, "field": field})
            elif t.value == "[":
                self.next()
                idx = self.expr()
                self.expect("]")
                e = self.node(self.start_of(e, t.pos), {"k": "index", "obj": e, "idx": idx})
            elif t.value == "(":
                e = self.call_rest(e)
            elif t.value in ("++", "--"):
                self.next()
                e = self.node(self.start_of(e, t.pos), {"k": "post", "op": t.value, "x": e})
            else:
                break
        return e

    def call_rest(self, callee):
        start = self.start_of(callee, self.peek().pos)
        self.expect("(")
        args = []
        if not self.at(")"):
            while True:
                args.append(self.assign_expr())
                if not self.eat(","):
                    break
        self.expect(")")
        name = callee["name"] if callee.get("k") == "id" else callee.get("type")
        return self.node(start, {"k": "call", "name": name, "args": args})

    def primary(self):
        t = self.peek()
        if t.value == "(":
            self.next()
            e = self.expr()
            self.expect(")")
            return e
        if t.kind == "num":
            self.next()
            return self.node(t.pos, {"k": "num", "value": t.value})
        if t.value in ("true", "false"):
            self.next()
            return self.node(t.pos, {"k": "bool", "value": t.value == "true"})
        if t.kind == "id":
            # constructor: TYPE(...) or TYPE[N](...)
            if (t.value in TYPES or t.value in self.struct_types) and self.peek(1).value in ("(", "["):
                self.next()
                arr = None
                if self.eat("["):
                    arr = True if self.at("]") else self.expr()
                    self.expect("]")
                self.expect("(")
                args = []
                if not self.at(")"):
                    while True:
                        args.append(self.assign_expr())
                        if not self.eat(","):
                            break
                self.expect(")")
                return self.node(t.pos, {"k": "construct", "type": t.value, "array": arr, "args": args})
            self.next()
            return self.node(t.pos, {"k": "id", "name": t.value})
        raise SyntaxError(f"unexpected token {t.value!r} at {self.i}")


def parse(source_or_tokens):
    tokens = tokenize(source_or_tokens) if isinstance(source_or_tokens, str) else source_or_tokens
    return Parser(tokens).parse_program()
