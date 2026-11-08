"""Source-bound profile for stipple's integer shift carriers and isqrt posts.

Authenticates the exact shift sites the integer-hash stipple introduces:
two ``uvec2 << uvec2`` sites, one ``uint << uint`` site, one signed
``ivec2 >> int`` site, and the four ``uint`` post increment/decrement
statements inside the integer ``isqrt`` helper.  The scalar uint right
shifts belong to the hash-scalar-uint-rshift carrier, not this module.
"""

from __future__ import annotations

import hashlib
import dataclasses

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "stipple-integer-shift-v1"

STIPPLE_KEY = "filter/stipple:stipple"
STIPPLE_PROFILE = PROFILE

RAW_BYTES = 10823
RAW_SHA256 = "84755c2b6b2bf86a9c0b73a1faceda9b9bbb5fbf7d7a0570e91e2caf979f52a6"
NORMALIZED_BYTES = 4821
NORMALIZED_SHA256 = "8dfaabf22a11f15e61c0abe50ced8036dc5acecc02a21b5bb5286266128f0eaa"
FUNCTIONS_SHA256 = "4daea2de58e00e9f8525a82ec36b0214cc556c07adfff07f73fd8418536359bd"
WHOLE_SHA256 = "789bff0aaa4d54537f2e9f42420d59d14f00376162ae1a4d841e42b9718b6bae"
INTERFACE_SHA256 = "7c261199c004c39a6f6b58a0d9c1e53391beda34743b66369db7933b9bee9d7f"


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = value.span
    return f"{span.start_line}:{span.start_column}-{span.end_line}:{span.end_column}"


def _whole(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _walk_expression(value: TypedExpression):
    yield value
    for child in getattr(value, "children", ()):
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in getattr(value, "expressions", ()):
        yield from _walk_expression(expression)
    for child in getattr(value, "children", ()):
        yield from _walk_statement(child)


def _program_nodes(program: TypedProgram):
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                yield function, statement, value


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


@dataclasses.dataclass(frozen=True)
class StippleIntegerShiftProof:
    vector_lefts: tuple
    scalar_lefts: tuple
    signed_rights: tuple
    sites: tuple
    isqrt_posts: tuple


def _authenticate(program: TypedProgram, source_hash: str | None,
                  profile: str | None) -> StippleIntegerShiftProof:
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != STIPPLE_KEY:
        raise _fail("profile on foreign key")
    if source_hash != RAW_SHA256:
        raise _fail("exact caller source hash required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or program.body_status != "analyzed"
            or _sha(program.functions) != FUNCTIONS_SHA256
            or _whole(program) != WHOLE_SHA256
            or _interface(program) != INTERFACE_SHA256):
        raise _fail("raw, normalized, function, whole, or interface fingerprint mismatch")

    vector_lefts: list[TypedExpression] = []
    scalar_lefts: list[TypedExpression] = []
    signed_rights: list[TypedExpression] = []
    posts: list[TypedExpression] = []
    for function, _statement, value in _program_nodes(program):
        if value.kind == "binary" and value.operator == "<<":
            left = value.children[0].type.display()
            if left == "uvec2":
                vector_lefts.append(value)
            elif left == "uint":
                scalar_lefts.append(value)
            else:
                raise _fail("unexpected left-shift operand type")
        elif value.kind == "binary" and value.operator == ">>":
            if (value.children[0].type.display() == "ivec2"
                    and value.children[1].type.display() == "int"):
                signed_rights.append(value)
        elif value.kind == "post" and value.type.display() == "uint":
            posts.append(value)

    if len(vector_lefts) != 2 or len(scalar_lefts) != 1:
        raise _fail("left-shift site census mismatch")
    if len(signed_rights) != 1:
        raise _fail("signed right-shift site census mismatch")
    isqrt = [function for function in program.functions
             if function.name == "isqrt"]
    if len(isqrt) != 1:
        raise _fail("isqrt helper identity mismatch")
    expected_posts = [value for value in posts
                      if getattr(value.children[0], "symbol_id", None)
                      in _isqrt_local_ids(isqrt[0])]
    if tuple((value.operator, _span(value)) for value in expected_posts) != (
            ("--", "81:20-81:23"), ("--", "82:20-82:23"),
            ("++", "83:35-83:38"), ("++", "84:35-84:38")):
        raise _fail("isqrt uint post census mismatch")
    return StippleIntegerShiftProof(
        tuple(vector_lefts), tuple(scalar_lefts), tuple(signed_rights),
        tuple(vector_lefts) + tuple(scalar_lefts) + tuple(signed_rights),
        tuple(expected_posts))


def _isqrt_local_ids(function) -> set[int]:
    ids = set()
    for statement in function.body:
        for expression in _walk_statement(statement):
            if expression.kind == "id" and expression.symbol_id is not None:
                ids.add(expression.symbol_id)
    return ids


def authenticate_stipple_integer_shift(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> StippleIntegerShiftProof:
    return _authenticate(program, source_hash, profile)


def authenticate_stipple_isqrt_posts(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple:
    return _authenticate(program, source_hash, profile).isqrt_posts


def apply_stipple_integer_shift(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    _authenticate(program, source_hash, profile)
    return program


__all__ = (
    "PROFILE", "STIPPLE_KEY", "STIPPLE_PROFILE", "RAW_BYTES", "RAW_SHA256",
    "NORMALIZED_BYTES", "NORMALIZED_SHA256", "FUNCTIONS_SHA256",
    "WHOLE_SHA256", "INTERFACE_SHA256", "StippleIntegerShiftProof",
    "authenticate_stipple_integer_shift", "authenticate_stipple_isqrt_posts",
    "apply_stipple_integer_shift",
)
