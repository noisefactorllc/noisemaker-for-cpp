"""Source-locked Number-arithmetic repair for Sacred Geometry's Star path."""

from __future__ import annotations

import dataclasses
import hashlib

from .semantic_types import FLOAT
from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


TRANSFORM = "sacred-star-number-division-v1"
SACRED_KEY = "synth/sacredGeometry:sacredGeometry"
RAW_SOURCE_BYTES = 9710
RAW_SOURCE_SHA256 = "24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de"
NORMALIZED_SOURCE_SHA256 = "6b3c4e8492a69969f3d6f78689cfd19de846656fd0c6d5c8dfd5a758427c61d3"
INTERFACE_SHA256 = "de898c81d54e1aa67052f551b953dca47e46b8b8aca66ca179408948b9ec8770"
PRE_FUNCTION_SHA256 = "261327d6c1700f71cef056020358ba1ea4dd56c1e8d1017f545df805a4f9b1d8"
PRE_WHOLE_PROGRAM_SHA256 = "2dda5c4f3931965da85ac54fca2b6e4748cb2cb1ca61b03316f750c2f6754388"
POST_FUNCTION_SHA256 = "fdaf48f945303bfe83c56ee0e2e75ae62d418904c02fc2bc6621fc0da907f7b2"
POST_WHOLE_PROGRAM_SHA256 = "de499dea91a59d8fc5ec4591be30a9b4350bb6a9e0317259aa97e8d3e3586ee0"


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def whole_program_fingerprint(program: TypedProgram) -> str:
    """Hash the frozen semantic tree while intentionally excluding proof carriers."""
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _fail(message: str) -> ValueError:
    return ValueError(f"{TRANSFORM}: {message}")


def _proofs_empty(program: TypedProgram) -> bool:
    return all(getattr(program, name, None) is None for name in (
        "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
        "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
    ))


def _source_ok(program: TypedProgram) -> bool:
    return (
        program.key == SACRED_KEY
        and not program.preprocessor_defines
        and len(program.raw_source.encode("utf-8")) == RAW_SOURCE_BYTES
        and hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
            == RAW_SOURCE_SHA256
        and hashlib.sha256(program.source.encode("utf-8")).hexdigest()
            == NORMALIZED_SOURCE_SHA256
        and interface_fingerprint(program) == INTERFACE_SHA256
    )


def _is_span(value: TypedExpression, line: int, start: int, end: int) -> bool:
    return (value.span.start_line, value.span.start_column,
            value.span.end_line, value.span.end_column) == (line, start, line, end)


def _rewrite_expression(value: TypedExpression,
                        counts: dict[str, int]) -> TypedExpression:
    children = tuple(_rewrite_expression(child, counts) for child in value.children)
    result = dataclasses.replace(value, children=children)
    if (value.kind == "binary" and value.operator == "/"
            and value.type.display() == "int" and _is_span(value, 260, 29, 39)):
        left, right = value.children
        if (left.kind != "binary" or left.operator != "+"
                or right.kind != "id" or right.symbol_id != 37):
            raise _fail("division structure mismatch")
        counts["division"] += 1
        result = dataclasses.replace(result, type=FLOAT)
    elif (value.kind == "binary" and value.operator == "*"
          and value.type.display() == "int" and _is_span(value, 260, 29, 44)):
        if (len(value.children) != 2 or value.children[0].kind != "binary"
                or value.children[0].operator != "/"
                or value.children[1].kind != "id"
                or value.children[1].symbol_id != 37):
            raise _fail("multiplication structure mismatch")
        counts["multiplication"] += 1
        result = dataclasses.replace(result, type=FLOAT)
    elif (value.kind == "binary" and value.operator == "-"
          and value.type.display() == "int" and _is_span(value, 260, 18, 44)):
        if len(value.children) != 2 or value.children[0].operator != "+":
            raise _fail("subtraction structure mismatch")
        counts["subtraction"] += 1
        result = dataclasses.replace(result, type=FLOAT)
    elif (value.kind == "declaration" and value.symbol_id == 107
          and value.type.display() == "int" and _is_span(value, 260, 13, 44)):
        if (value.symbol is None or value.symbol.name != "j"
                or value.symbol.storage != "local" or not value.symbol.writable
                or len(value.children) != 1):
            raise _fail("j declaration mismatch")
        counts["declaration"] += 1
        result = dataclasses.replace(
            result, type=FLOAT, symbol=dataclasses.replace(value.symbol, type=FLOAT))
    elif (value.kind == "id" and value.symbol_id == 107
          and value.type.display() == "int" and _is_span(value, 262, 30, 31)):
        if value.symbol is None or value.symbol.name != "j":
            raise _fail("j consumption mismatch")
        counts["consumption"] += 1
        result = dataclasses.replace(
            result, type=FLOAT, symbol=dataclasses.replace(value.symbol, type=FLOAT))
    return result


def _rewrite_statement(value: TypedStatement,
                       counts: dict[str, int]) -> TypedStatement:
    return dataclasses.replace(
        value,
        expressions=tuple(_rewrite_expression(item, counts)
                          for item in value.expressions),
        children=tuple(_rewrite_statement(item, counts) for item in value.children),
    )


def apply_sacred_star_number_division(program: TypedProgram) -> TypedProgram:
    """Change exactly the five authenticated Star-number nodes to typed float."""
    if not _proofs_empty(program):
        raise _fail("pre-transform proof carrier is not empty")
    if (not _source_ok(program) or _sha(program.functions) != PRE_FUNCTION_SHA256
            or whole_program_fingerprint(program) != PRE_WHOLE_PROGRAM_SHA256):
        raise _fail("source, key, interface, or pre-transform tree mismatch")
    matches = [function for function in program.functions
               if function.signature.id == 46 and function.name == "starPolygonMask"
               and function.body]
    if len(matches) != 1 or len(matches[0].body) != 7:
        raise _fail("starPolygonMask identity/body mismatch")
    star = matches[0]
    if (star.return_type.display() != "float"
            or tuple((item.id, item.name, item.type.display())
                     for item in star.parameters) != ((36, "p", "vec2"), (37, "n", "int"))):
        raise _fail("starPolygonMask signature mismatch")
    counts = {name: 0 for name in (
        "division", "multiplication", "subtraction", "declaration", "consumption")}
    rewritten = dataclasses.replace(
        star, body=tuple(_rewrite_statement(item, counts) for item in star.body))
    if counts != {name: 1 for name in counts}:
        raise _fail(f"expected one exact five-node site, got {counts}")
    transformed = dataclasses.replace(
        program, functions=tuple(rewritten if function is star else function
                                 for function in program.functions))
    if (_sha(transformed.functions) != POST_FUNCTION_SHA256
            or whole_program_fingerprint(transformed) != POST_WHOLE_PROGRAM_SHA256):
        raise _fail("post-transform tree mismatch")
    return transformed


def authenticate_sacred_star_number_division(
        program: TypedProgram, source_hash: str | None) -> None:
    """Authenticate an already transformed Sacred tree without mutating it."""
    if (source_hash != RAW_SOURCE_SHA256 or not _source_ok(program)
            or _sha(program.functions) != POST_FUNCTION_SHA256
            or whole_program_fingerprint(program) != POST_WHOLE_PROGRAM_SHA256):
        raise _fail("source, interface, or post-transform tree mismatch")
