"""Immutable parsed subset used by the deterministic C++ emitter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Expr:
    kind: str
    value: str | None = None
    children: tuple["Expr", ...] = ()
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class Statement:
    kind: str
    type_name: str | None = None
    target: Expr | None = None
    value: Expr | None = None
    then_body: tuple["Statement", ...] = ()
    else_body: tuple["Statement", ...] = ()


@dataclass(frozen=True)
class Uniform:
    type_name: str
    name: str


@dataclass(frozen=True)
class Program:
    key: str
    uniforms: tuple[Uniform, ...]
    statements: tuple[Statement, ...]
