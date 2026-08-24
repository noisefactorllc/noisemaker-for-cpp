"""Fail-closed, dependency-free frontend for the pinned GLSL corpus."""

from __future__ import annotations

import re
import math

from .lexer import tokenize
from .parser import parse
from .preprocess import normalize
from .ast_spans import strip_and_spans
from .typed_ir import PreprocessorDefine


def _canonical_defines(runtime_defines: dict | None) -> tuple[PreprocessorDefine, ...]:
    records: list[PreprocessorDefine] = []
    items = tuple((runtime_defines or {}).items())
    if any(not isinstance(name, str) for name, _ in items):
        raise ValueError("preprocessor define names must be strings")
    for name, value in sorted(items):
        if isinstance(value, bool):
            kind, canonical = "bool", "true" if value else "false"
        elif isinstance(value, int):
            kind, canonical = "int", str(value)
        elif isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("preprocessor float defines must be finite")
            kind, canonical = "float", value.hex()
        elif isinstance(value, str):
            kind, canonical = "str", value
        else:
            raise ValueError("unsupported preprocessor define value")
        records.append(PreprocessorDefine(name, kind, canonical))
    return tuple(records)


class FrontendError(ValueError):
    """A deterministic frontend diagnostic tied to a corpus program."""

    def __init__(self, program_key: str, line: int, column: int, message: str) -> None:
        self.program_key = program_key
        self.line = line
        self.column = column
        self.message = message
        super().__init__(f"{program_key}:{line}:{column}: {message}")


def parse_program(source: str, program_key: str, runtime_defines: dict | None = None) -> dict:
    """Normalize and structurally parse one complete GLSL program.

    This is deliberately a syntax frontier only.  Semantic/type validation is a
    later stage, but every token must be consumed by the adapted sibling parser.
    """
    try:
        canonical_defines = _canonical_defines(runtime_defines)
        normalized = normalize(source, runtime_defines)
        tokens = tokenize(normalized["source"])
        parsed_ast = parse(tokens)
        ast, spans = strip_and_spans(parsed_ast, program_key, normalized["source"])
    except (SyntaxError, ValueError, KeyError, IndexError) as error:
        source_line = getattr(error, "line", None)
        if source_line is not None:
            line = source_line
            column = getattr(error, "column", 1)
        elif (match := re.search(r"at token (\d+)", str(error))):
            token_index = int(match.group(1))
            token = tokens[token_index] if "tokens" in locals() and token_index < len(tokens) else None
            position = token.pos if token is not None else 0
        else:
            character = re.search(r" at (\d+)$", str(error))
            position = int(character.group(1)) if character else 0
        if source_line is None:
            before = normalized["source"][:position] if "normalized" in locals() else ""
            line = before.count("\n") + 1
            column = position - before.rfind("\n")
        message = "unconsumed or malformed token" if isinstance(error, IndexError) else str(error)
        raise FrontendError(program_key, line, column, message) from error
    # Keep the legacy mapping interface while preserving the normalized input
    # from which semantic locations are calculated.  The parsed AST remains an
    # ordinary, caller-owned syntax tree and is never mutated by analysis.
    return {"k": "program", "ast": ast, "outputs": tuple(normalized["outputs"]),
            "varyings": tuple(normalized["varyings"]), "source": normalized["source"],
            "program_key": program_key,
            "raw_source": source,
            "preprocessor_defines": canonical_defines,
            "varying_types": dict(normalized["varying_types"]),
            "spans": spans}
