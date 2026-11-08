"""Source-bound profile for stipple's const uint[5] fbm octave table.

Authenticates the exact single const array declaration the integer-hash
stipple introduces: ``const uint M[5]`` inside ``fbm``, initialized with a
five-literal constructor, read exactly once per counted-loop iteration by
the induction symbol.  The generator's type rejection admits only the
array declaration, constructor, reference, and index nodes this proof
consumes.
"""

from __future__ import annotations

import dataclasses
import hashlib

from .typed_ir import (TypedExpression, TypedFunction, TypedProgram,
                       TypedStatement)


PROFILE = "stipple-fbm-const-array-v1"

STIPPLE_KEY = "filter/stipple:stipple"

RAW_BYTES = 10823
RAW_SHA256 = "84755c2b6b2bf86a9c0b73a1faceda9b9bbb5fbf7d7a0570e91e2caf979f52a6"
NORMALIZED_BYTES = 4821
NORMALIZED_SHA256 = "8dfaabf22a11f15e61c0abe50ced8036dc5acecc02a21b5bb5286266128f0eaa"
FUNCTIONS_SHA256 = "4daea2de58e00e9f8525a82ec36b0214cc556c07adfff07f73fd8418536359bd"
WHOLE_SHA256 = "789bff0aaa4d54537f2e9f42420d59d14f00376162ae1a4d841e42b9718b6bae"
INTERFACE_SHA256 = "7c261199c004c39a6f6b58a0d9c1e53391beda34743b66369db7933b9bee9d7f"

FBM_FUNCTION_ID = 27
FBM_BODY_COUNT = 4
DECL_SYMBOL_ID = 38
DECL_NAME = "M"
DECL_SPAN = "69:16-69:68"
CONSTRUCTOR_TYPE = "uint[5]"
CONSTRUCTOR_LITERALS = (65536, 32284, 15903, 7834, 3859)
LOOP_INDEX = 2
LOOP_PROOF = (40, 0, 5, "<", "++", 5, 12, 1, 5, 12)
INDEX_SPAN = "72:32-72:36"
DECLARATION_INITIALIZER_SHA256 = (
    "ac91aceff912731109b6002d1e469beec65f233c74e0be386c37b48faadb41bd")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = value.span
    return (f"{span.start_line}:{span.start_column}"
            f"-{span.end_line}:{span.end_column}")


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


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


@dataclasses.dataclass(frozen=True)
class StippleFbmConstArrayProof:
    declaration: object
    constructor: object
    reference: object
    index_nodes: tuple


def _authenticate(program: TypedProgram, source_hash: str | None,
                  profile: str | None) -> StippleFbmConstArrayProof:
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

    fbms = [function for function in program.functions
            if function.signature.id == FBM_FUNCTION_ID
            and function.name == "fbm"]
    if len(fbms) != 1 or len(fbms[0].body) != FBM_BODY_COUNT:
        raise _fail("fbm function identity mismatch")
    fbm = fbms[0]
    declaration_statement = fbm.body[0]
    if declaration_statement.kind != "decl" or len(
            declaration_statement.expressions) != 1:
        raise _fail("fbm const array declaration shape mismatch")
    declaration = declaration_statement.expressions[0]
    if (declaration.kind != "declaration" or declaration.symbol is None
            or declaration.symbol_id != DECL_SYMBOL_ID
            or declaration.symbol.name != DECL_NAME
            or declaration.type.display() != "uint[5]"
            or _span(declaration) != DECL_SPAN
            or len(declaration.children) != 1
            or declaration.children[0].kind != "construct"
            or declaration.children[0].constructor_type.display()
            != CONSTRUCTOR_TYPE
            or len(declaration.children[0].children) != 5
            or any(child.kind != "literal"
                   or child.type.display() != "uint"
                   for child in declaration.children[0].children)):
        raise _fail("fbm const uint[5] declaration identity mismatch")
    constructor = declaration.children[0]
    if tuple(child.literal_value for child in constructor.children) != (
            CONSTRUCTOR_LITERALS):
        raise _fail("fbm const uint[5] literal payload mismatch")
    if _sha(constructor) != DECLARATION_INITIALIZER_SHA256:
        raise _fail("fbm const uint[5] constructor identity mismatch")

    loop = fbm.body[LOOP_INDEX]
    proof = loop.loop_proof
    if proof is None:
        raise _fail("fbm octave loop is not a counted-for proof")
    actual = (proof.induction_symbol_id, proof.start_value,
              proof.bound_value, proof.comparison, proof.update,
              proof.trip_count, proof.entrypoint_charge,
              proof.effective_depth, proof.lexical_product,
              proof.entrypoint_charge)
    if actual != LOOP_PROOF or len(loop.children) != 2:
        raise _fail("fbm octave loop bound mismatch")

    references = [
        value for function in program.functions for statement in function.body
        for value in _walk_statement(statement)
        if value.kind == "id" and value.symbol_id == DECL_SYMBOL_ID]
    if len(references) != 1:
        raise _fail("fbm const array reference census mismatch")
    reference = references[0]
    indexes = [
        value for function in program.functions for statement in function.body
        for value in _walk_statement(statement)
        if value.kind == "index" and value.children[0].symbol_id
        == DECL_SYMBOL_ID]
    if len(indexes) != 1:
        raise _fail("fbm const array index census mismatch")
    index_node = indexes[0]
    if (_span(index_node) != INDEX_SPAN
            or index_node.children[1].kind != "id"
            or index_node.children[1].symbol_id
            != proof.induction_symbol_id):
        raise _fail("fbm const array index site identity mismatch")
    return StippleFbmConstArrayProof(
        declaration, constructor, reference, (index_node,))


def authenticate_stipple_fbm_const_array(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> StippleFbmConstArrayProof:
    return _authenticate(program, source_hash, profile)


def apply_stipple_fbm_const_array(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    _authenticate(program, source_hash, profile)
    return program


__all__ = (
    "PROFILE", "STIPPLE_KEY", "RAW_BYTES", "RAW_SHA256", "NORMALIZED_BYTES",
    "NORMALIZED_SHA256", "FUNCTIONS_SHA256", "WHOLE_SHA256",
    "INTERFACE_SHA256", "StippleFbmConstArrayProof",
    "authenticate_stipple_fbm_const_array", "apply_stipple_fbm_const_array",
)
