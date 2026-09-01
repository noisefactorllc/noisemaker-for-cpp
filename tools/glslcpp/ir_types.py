"""Immutable parsed subset used by the deterministic C++ emitter.

Not named types.py. Every tool in this directory is also run as a
script, which puts this directory at the head of sys.path, so a module
named after a standard-library module hides the real one from the
interpreter itself -- including from the imports CPython performs while
loading argparse. tests/test_tool_script_module_hygiene.py holds the
invariant.
"""

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
