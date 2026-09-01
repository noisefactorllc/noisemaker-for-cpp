"""Parser for the intentionally small, fail-closed Task-5 GLSL subset."""

from __future__ import annotations

from .lexer import Token, lex
from .preprocess import normalize
from .ir_types import Expr, Program, Statement, Uniform


class GeneratorError(ValueError):
    pass


_TYPE_NAMES = {"float", "int", "vec2", "vec3", "vec4", "ivec2", "sampler2D"}
_SUPPORTED_CALLS = {"vec2", "vec4", "texture", "textureSize", "min"}


class _Parser:
    def __init__(self, tokens: list[Token], key: str) -> None:
        self.tokens = tokens
        self.key = key
        self.index = 0

    def error(self, token: Token | None, message: str) -> GeneratorError:
        if token is None:
            return GeneratorError(f"{self.key}:EOF: {message}")
        return GeneratorError(f"{self.key}:{token.line}:{token.column}: {message}")

    def peek(self, value: str | None = None) -> Token | None:
        token = self.tokens[self.index] if self.index < len(self.tokens) else None
        if value is not None and (token is None or token.value != value):
            return None
        return token

    def take(self, value: str | None = None) -> Token:
        token = self.peek()
        if token is None:
            raise self.error(token, f"expected {value or 'token'}")
        if value is not None and token.value != value:
            raise self.error(token, f"expected {value}")
        self.index += 1
        return token

    def parse(self) -> Program:
        uniforms: list[Uniform] = []
        statements: tuple[Statement, ...] | None = None
        while self.peek() is not None:
            if self.peek("uniform"):
                self.take("uniform")
                type_name = self.take().value
                if type_name not in _TYPE_NAMES:
                    raise self.error(self.tokens[self.index - 1], "unsupported uniform type")
                uniforms.append(Uniform(type_name, self.take().value))
                self.take(";")
            elif self.peek("out"):
                self.take("out")
                self.take("vec4")
                self.take()
                self.take(";")
            elif self.peek("void"):
                self.take("void")
                self.take("main")
                self.take("(")
                self.take(")")
                if statements is not None:
                    raise self.error(self.peek(), "multiple main functions")
                statements = self.parse_block()
            else:
                raise self.error(self.peek(), "unsupported top-level declaration")
        if statements is None:
            raise GeneratorError(f"{self.key}:EOF: missing main function")
        return Program(self.key, tuple(uniforms), statements)

    def parse_block(self) -> tuple[Statement, ...]:
        self.take("{")
        statements: list[Statement] = []
        while not self.peek("}"):
            if self.peek() is None:
                raise self.error(None, "unterminated block")
            statements.append(self.parse_statement())
        self.take("}")
        return tuple(statements)

    def parse_statement(self) -> Statement:
        if self.peek("if"):
            self.take("if")
            self.take("(")
            condition = self.parse_expression()
            self.take(")")
            then_body = self.parse_block()
            else_body: tuple[Statement, ...] = ()
            if self.peek("else"):
                self.take("else")
                else_body = self.parse_block()
            return Statement("if", target=condition, then_body=then_body, else_body=else_body)
        token = self.peek()
        if token is not None and token.value in _TYPE_NAMES - {"sampler2D"}:
            type_name = self.take().value
            name = self.take().value
            self.take("=")
            value = self.parse_expression()
            self.take(";")
            return Statement("declaration", type_name=type_name,
                             target=Expr("name", name, line=token.line, column=token.column), value=value)
        target = self.parse_postfix()
        self.take("=")
        value = self.parse_expression()
        self.take(";")
        return Statement("assignment", target=target, value=value)

    def parse_expression(self, minimum_precedence: int = 0) -> Expr:
        left = self.parse_unary()
        precedence = {"==": 1, "+": 2, "-": 2, "*": 3, "/": 3}
        while (token := self.peek()) is not None and token.value in precedence and precedence[token.value] >= minimum_precedence:
            operator = self.take()
            right = self.parse_expression(precedence[operator.value] + 1)
            left = Expr("binary", operator.value, (left, right), operator.line, operator.column)
        return left

    def parse_unary(self) -> Expr:
        token = self.peek()
        if token is not None and token.value == "-":
            self.take("-")
            return Expr("unary", "-", (self.parse_unary(),), token.line, token.column)
        return self.parse_postfix()

    def parse_postfix(self) -> Expr:
        token = self.take()
        if token.value[0].isdigit() or token.value.startswith("."):
            expression = Expr("literal", token.value, line=token.line, column=token.column)
        else:
            expression = Expr("name", token.value, line=token.line, column=token.column)
        if self.peek("("):
            self.take("(")
            arguments: list[Expr] = []
            if not self.peek(")"):
                while True:
                    arguments.append(self.parse_expression())
                    if not self.peek(","):
                        break
                    self.take(",")
            self.take(")")
            if expression.value not in _SUPPORTED_CALLS:
                raise self.error(token, f"unsupported call {expression.value}")
            expression = Expr("call", expression.value, tuple(arguments), token.line, token.column)
        while self.peek("."):
            self.take(".")
            member = self.take()
            expression = Expr("member", member.value, (expression,), member.line, member.column)
        return expression


def parse_program(source: str, key: str) -> Program:
    try:
        normalized = normalize(source)
    except ValueError as error:
        raise GeneratorError(f"{key}: preprocess: {error}") from error
    try:
        return _Parser(lex(normalized), key).parse()
    except GeneratorError:
        raise
    except ValueError as error:
        raise GeneratorError(f"{key}: lexer: {error}") from error
