"""Closed identity profile for Gather Sorted's one round-to-int site."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "gather-sorted-round-to-int-v1"
GATHER_SORTED_KEY = "filter/pixelSort:gatherSorted"
RAW_SOURCE_BYTES = 1896
RAW_SOURCE_SHA256 = "a45eb039bae3e7b0a5f804de68c441092b6b7826b594c4aa5221c22a6c7b1386"
NORMALIZED_SOURCE_BYTES = 1185
NORMALIZED_SOURCE_SHA256 = "28e7ad80ef7db266559deb4b822f52251ab899af61feb9f915e32c0ecce079a9"
MAIN_SHA256 = "89ca9cc42483c88f4351e39338079ab5f742300493815982dff04ece432fba7e"
FUNCTIONS_SHA256 = "6378f26aa15c43dda1ceba1d098d5b7f7fd76174618bbc5428e6659622cf8218"
WHOLE_PROGRAM_SHA256 = "23120c79e838032a4ac54abeac0929d1dc2c7c89c895b083b68e6188b6f36fe3"
INTERFACE_SHA256 = "f18371bad7d92151cd361663a4b56266fffa2228b7b6379ad16518d9af8a8ed6"
ROUND_SHA256 = "a5f412a1949fdfae93b759bf1c01a22afb44f9a48e71710f2c54cdcdf312c625"
ARGUMENT_SHA256 = "a3797427a6fd439f07e4b1a5d33f7f13edcff528e71bee77a80489ae1697761d"
PARENT_SHA256 = "b16eb98c5a1cef7a40f78c65448f5f127c5feaa7cfa64dfdda0e167283aaba3c"
STATEMENT_SHA256 = "3c98243330c489b4216d526ba594bac28177a8c3c1f1eb3799528ddbad358ea5"
LOOP_PROOF_SHA256 = "c9df47f651e3ee7232826b3bf13ac40e29889e3d69a2d7a2f6dedecba5c579d4"
PROGRAM_PROOF_SHA256 = "dd9dc4392ed9350b896854ad13cee5a242281bbe2b791f19b28cd2bd361251ca"
PROFILE_SHA256 = "a100420798a4964c67ec4b2e98a09c62e5ca5b3b0d7f2fe1eb7a8ff8180e43fa"


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_program_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    yield value
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_gather_sorted_round_to_int(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, TypedExpression]:
    """Return the exact (int parent, round child) after full authentication."""
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if (program.key != GATHER_SORTED_KEY or source_hash != RAW_SOURCE_SHA256
            or len(raw) != RAW_SOURCE_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SOURCE_SHA256
            or len(normalized) != NORMALIZED_SOURCE_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SOURCE_SHA256
            or program.preprocessor_defines or program.body_status != "analyzed"):
        raise _fail("source, key, define, or body profile mismatch")
    if (len(program.functions) != 1 or program.functions[0].name != "main"
            or program.functions[0].id != 5
            or len(program.functions[0].body) != 15
            or _sha(program.functions[0]) != MAIN_SHA256
            or _sha(program.functions) != FUNCTIONS_SHA256
            or _whole_program_fingerprint(program) != WHOLE_PROGRAM_SHA256
            or _interface_fingerprint(program) != INTERFACE_SHA256):
        raise _fail("function, whole-program, or interface profile mismatch")

    function = program.functions[0]
    statement = function.body[6]
    if (statement.kind != "decl" or len(statement.expressions) != 1
            or _span(statement) != "24:5-24:68"
            or _sha(statement) != STATEMENT_SHA256):
        raise _fail("declaration statement profile mismatch")
    declaration = statement.expressions[0]
    if (declaration.kind != "declaration" or declaration.symbol_id != 13
            or declaration.symbol is None
            or declaration.symbol.name != "brightestX"
            or declaration.symbol.storage != "local"
            or not declaration.symbol.writable
            or declaration.type.display() != "int"
            or len(declaration.children) != 1):
        raise _fail("brightestX declaration profile mismatch")
    parent = declaration.children[0]
    if (parent.kind != "construct" or parent.constructor_type is None
            or parent.constructor_type.display() != "int"
            or parent.type.display() != "int" or parent.category != "rvalue"
            or len(parent.children) != 1 or _span(parent) != "24:22-24:67"
            or _sha(parent) != PARENT_SHA256):
        raise _fail("round-to-int parent profile mismatch")
    round_value = parent.children[0]
    if (round_value.kind != "builtin" or round_value.callee != "round"
            or round_value.signature_id != -38
            or round_value.type.display() != "float"
            or round_value.category != "rvalue"
            or len(round_value.children) != 1
            or round_value.children[0].type.display() != "float"
            or _span(round_value) != "24:26-24:66"
            or _sha(round_value) != ROUND_SHA256
            or _sha(round_value.children[0]) != ARGUMENT_SHA256):
        raise _fail("round site or argument profile mismatch")

    all_rounds = []
    all_loops = []
    for item in function.body:
        for value in _walk_statement(item):
            if isinstance(value, TypedExpression) and value.kind == "builtin" and value.callee == "round":
                all_rounds.append(value)
            if isinstance(value, TypedStatement) and value.kind == "for":
                all_loops.append(value)
    if len(all_rounds) != 1 or all_rounds[0] is not round_value:
        raise _fail("expected exactly one owned round site")
    if (len(all_loops) != 1 or _span(all_loops[0]) != "38:5-48:6"
            or _sha(all_loops[0].loop_proof) != LOOP_PROOF_SHA256
            or _sha(program.counted_loop_proof) != PROGRAM_PROOF_SHA256):
        raise _fail("counted-loop proof profile mismatch")

    bindings = tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable)
        for item in program.declarations)
    if bindings != (
            (1, "preparedTex", "sampler2D", "uniform", False),
            (2, "rankTex", "sampler2D", "uniform", False),
            (3, "brightestTex", "sampler2D", "uniform", False),
            (4, "fragColor", "vec4", "output", True)):
        raise _fail("binding profile mismatch")
    resources = program.resources
    if (resources.uniforms != ("preparedTex", "rankTex", "brightestTex")
            or resources.samplers != resources.uniforms
            or resources.outputs != ("fragColor",)
            or not resources.uses_texture or resources.uses_derivatives):
        raise _fail("resource profile mismatch")

    profile_tuple = (
        PROFILE, GATHER_SORTED_KEY, RAW_SOURCE_SHA256, {},
        ("main", (0, 6, "e0", 0, 0), "24:26-24:66", -38,
         ROUND_SHA256),
        ("int-parent", (0, 6, "e0", 0), "24:22-24:67",
         PARENT_SHA256),
        ("decl-statement", (0, 6), "24:5-24:68", STATEMENT_SHA256),
        FUNCTIONS_SHA256, WHOLE_PROGRAM_SHA256, INTERFACE_SHA256,
    )
    if _sha(profile_tuple) != PROFILE_SHA256:
        raise _fail("internal profile tuple mismatch")
    return parent, round_value


def apply_gather_sorted_round_to_int(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate and return the same immutable program object."""
    authenticate_gather_sorted_round_to_int(program, source_hash, profile)
    return program
