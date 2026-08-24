"""Authenticated frontend admission for ``synth/julia:julia``.

This source-bound profile records the exact struct, aggregate
member, ``out``-parameter, and counted-loop shape needed by the eventual
typed C++ row, without changing the shared validator or emitter. Julia is
kept separate from the ``classicNoisedeck/fractal`` effect: the latter has a
Julia-named helper, but it is a different program and is not this adapter's
canonical identity.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedProgram

KEY = "synth/julia:julia"
PROFILE = "julia-frontend-admission-v1"
KEYS: tuple[str, ...] = (KEY,)
PREPARED_KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_PROFILES: dict[str, str] = {}
ALLOWED_ROW_FIELDS = {
    KEY: frozenset({"defines", "program_key", "julia_frontend_profile",
                    "struct_declaration_profile", "out_inout_admission_profile"}),
}
PREPARED_ROW_FIELDS = dict(ALLOWED_ROW_FIELDS)
REQUIRED_COMPANION_PROFILES = {
    KEY: (("struct_declaration_profile", "struct-declaration-julia-v1"),
          ("out_inout_admission_profile", "out-inout-admission-julia-v1")),
}

RAW_BYTES = 12407
RAW_SHA256 = "825e175c22fea086ad2860e16bcf0a79d797574a9dfad937a23baaadaffdeef0"
NORMALIZED_BYTES = 9423
NORMALIZED_SHA256 = "ea70d41e7eef508a0fcfb816b13132e771d2d09f706d8f6eec9668cfe593078c"
FUNCTIONS_SHA256 = "bb6661ce644aae958656581c001a25f0e50acf3746dfe93f7d9a8c4a90cb062d"
WHOLE_SHA256 = "de353a3d7bf4c6373749cdc67e5f8d41abc034157332200c68b3d7d4fef5e91b"
INTERFACE_SHA256 = "9ffe9f511b2a6d6d3e07ad2b8e8462f6a1de10048159d0233f5a7b82624d3532"

SOURCE_UNIFORMS = (
    ("resolution", "vec2"), ("tileOffset", "vec2"),
    ("fullResolution", "vec2"), ("time", "float"),
    ("cReal", "float"), ("cImag", "float"), ("poi", "int"),
    ("outputMode", "int"), ("centerX", "float"), ("centerY", "float"),
    ("rotation", "float"), ("iterations", "int"),
    ("stripeFreq", "float"), ("trapShape", "int"),
    ("lightAngle", "float"), ("cPath", "int"), ("cSpeed", "float"),
    ("cRadius", "float"), ("invert", "bool"), ("zoomSpeed", "float"),
    ("zoomDepth", "float"),
)
RUNTIME_UNIFORM_ABI = tuple(
    (name, {"float": "number", "int": "int32", "bool": "bool",
            "vec2": "Vec2"}[kind]) for name, kind in SOURCE_UNIFORMS)
OUTPUT_ABI = ("fragColor", "vec4", "Vec4", "output")
FUNCTION_NAMES = (
    "cmul", "df64_add", "df64_from", "df64_mul", "df64_mul_f",
    "df64_split", "df64_sub", "getAnimatedC", "getPOI", "iterateSmooth",
    "juliaIterate", "main", "outputDistanceEstimation", "outputNormalMap",
    "outputOrbitTrap", "outputSmoothIteration", "outputStripeAverage",
    "resolveC", "transformCoords",
)
FUNCTION_IDS = (
    (81, "cmul", "vec2"), (82, "df64_add", "vec2"),
    (83, "df64_from", "vec2"), (84, "df64_mul", "vec2"),
    (85, "df64_mul_f", "vec2"), (86, "df64_split", "void"),
    (87, "df64_sub", "vec2"), (88, "getAnimatedC", "vec2"),
    (89, "getPOI", "vec2"), (90, "iterateSmooth", "float"),
    (91, "juliaIterate", "JuliaResult"), (92, "main", "void"),
    (93, "outputDistanceEstimation", "float"),
    (94, "outputNormalMap", "float"), (95, "outputOrbitTrap", "float"),
    (96, "outputSmoothIteration", "float"),
    (97, "outputStripeAverage", "float"), (98, "resolveC", "vec2"),
    (99, "transformCoords", "void"),
)
EXPECTED_EXPR_KINDS = {
    "id": 380, "binary": 160, "literal": 139, "declaration": 80,
    "swizzle": 63, "builtin": 50, "call": 47, "construct": 41,
    "assign": 41, "member": 24, "unary": 14, "post": 3,
    "conditional": 1,
}
EXPECTED_OPERATORS = {
    "*": 56, "-": 38, "=": 35, "+": 25, "==": 21, "/": 15,
    ">=": 7, ">": 7, "+=": 6, "<": 5, "++": 3,
}
STRUCT_NAME = "JuliaResult"
STRUCT_FIELD_NAMES = ("iter", "zMag2", "dzMag2", "stripeSum",
                      "stripeCount", "stripeLast", "trapMin")
STRUCT_DECLARATION_SPAN = "161:1-169:3"
STRUCT_MEMBER_COUNT = 24
OUT_PARAMETERS = (
    ("df64_split", "hi", "float", "out", "104:26-104:38"),
    ("df64_split", "lo", "float", "out", "104:40-104:52"),
    ("transformCoords", "reDF", "vec2", "out", "145:22-145:35"),
    ("transformCoords", "imDF", "vec2", "out", "145:37-145:50"),
)
LOOPS = (
    ("iterateSmooth", "297:5-310:6", 1000),
    ("juliaIterate", "187:5-236:6", 1000),
)
COUNTED_LOOP_SUMMARY = (2, 0, 1, 1000, 3000, True)
JULIA_MAX_TRIP_COUNT = 1000
JULIA_COUNTED_LOOP_SUMMARY = COUNTED_LOOP_SUMMARY


@dataclass(frozen=True, slots=True)
class JuliaFrontendProof:
    program: TypedProgram
    uniforms: tuple[tuple[str, str], ...]
    functions: tuple[tuple[int, str, str], ...]
    struct_name: str
    struct_fields: tuple[str, ...]
    struct_members: tuple[TypedExpression, ...]
    out_parameters: tuple[tuple[str, str, str, str, str], ...]
    loops: tuple[tuple[str, str, int], ...]
    expression_counts: tuple[tuple[str, int], ...]
    operator_counts: tuple[tuple[str, int], ...]
    consumed_objects: tuple[object, ...]
    julia_loop_proof: "JuliaLoopProof"


@dataclass(frozen=True, slots=True)
class JuliaLoopProof:
    """Authenticated 1000-trip proof local to the Julia adapter."""

    loops: tuple[tuple[str, str, int], ...]
    loop_count: int
    unproved_loop_count: int
    entrypoint_charge: int
    max_trip_count: int
    call_graph_acyclic: bool


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources, program.local_type_names,
                 program.structs, program.uniform_blocks,
                 program.interface_symbols, program.builtin_symbols,
                 program.preprocessor_defines))


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _expressions(program: TypedProgram) -> tuple[TypedExpression, ...]:
    values: list[TypedExpression] = []
    for declaration in program.declarations:
        if declaration.initializer is not None:
            values.extend(_walk_expression(declaration.initializer))
    for function in program.functions:
        for statement in function.body:
            values.extend(_walk_statement(statement))
    return tuple(values)


def _statements(value):
    yield value
    for child in value.children:
        yield from _statements(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_julia_frontend(program: TypedProgram, source_hash: str | None,
                                profile: str | None) -> JuliaFrontendProof:
    if program.key != KEY or profile != PROFILE:
        raise _fail("exact key/profile required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (source_hash != RAW_SHA256 or len(raw) != RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or _sha(program.functions) != FUNCTIONS_SHA256
            or _whole(program) != WHOLE_SHA256
            or _interface(program) != INTERFACE_SHA256):
        raise _fail("source, function, whole-program, or interface lock mismatch")
    uniforms = tuple((item.symbol.name, item.type.display())
                     for item in program.declarations
                     if item.symbol.storage == "uniform")
    if uniforms != SOURCE_UNIFORMS:
        raise _fail("uniform interface census mismatch")
    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives)
            != (tuple(name for name, _ in SOURCE_UNIFORMS), (),
                ("fragColor",), False, False)):
        raise _fail("resource interface census mismatch")
    function_identity = tuple((item.id, item.name, item.return_type.display())
                              for item in program.functions)
    if function_identity != FUNCTION_IDS:
        raise _fail("function identity census mismatch")
    values = _expressions(program)
    if dict(Counter(item.kind for item in values)) != EXPECTED_EXPR_KINDS:
        raise _fail("expression-kind census mismatch")
    if dict(Counter(item.operator for item in values if item.operator)) != EXPECTED_OPERATORS:
        raise _fail("operator census mismatch")
    if len(program.structs) != 1 or program.structs[0].name != STRUCT_NAME:
        raise _fail("struct declaration identity mismatch")
    struct = program.structs[0]
    if _span(struct) != STRUCT_DECLARATION_SPAN or tuple(
            field.name for field in struct.fields) != STRUCT_FIELD_NAMES:
        raise _fail("struct field census mismatch")
    members = tuple(item for item in values if item.kind == "member")
    if len(members) != STRUCT_MEMBER_COUNT or any(
            item.children[0].type.display() != STRUCT_NAME for item in members):
        raise _fail("struct member census mismatch")
    out_parameters = tuple(
        (function.name, parameter.name, parameter.type.display(),
         parameter.direction, _span(parameter))
        for function in program.functions for parameter in function.parameters
        if parameter.direction != "in")
    if out_parameters != OUT_PARAMETERS:
        raise _fail("out-parameter identity census mismatch")
    loops = []
    for function in program.functions:
        for root in function.body:
            for statement in _statements(root):
                if statement.kind == "for":
                    proof = statement.loop_proof
                    loops.append((function.name, _span(statement),
                                  proof.bound_value if proof is not None else -1))
    if tuple(loops) != LOOPS:
        raise _fail("counted-loop identity census mismatch")
    summary = program.counted_loop_proof
    actual_summary = (summary.loop_count, summary.unproved_loop_count,
                      summary.max_effective_depth, summary.max_lexical_product,
                      summary.entrypoint_charge, summary.call_graph_acyclic)
    if actual_summary != COUNTED_LOOP_SUMMARY:
        raise _fail("counted-loop safety summary mismatch")
    consumed = tuple(program.declarations) + tuple(program.functions) + values
    if len({id(item) for item in consumed}) != len(consumed):
        raise _fail("consumed-object ledger is not identity-disjoint")
    julia_loop_proof = JuliaLoopProof(
        tuple(loops), summary.loop_count, summary.unproved_loop_count,
        summary.entrypoint_charge, summary.max_lexical_product,
        summary.call_graph_acyclic)
    return JuliaFrontendProof(
        program, uniforms, function_identity, STRUCT_NAME, STRUCT_FIELD_NAMES,
        members, out_parameters, tuple(loops),
        tuple(sorted(Counter(item.kind for item in values).items())),
        tuple(sorted(Counter(item.operator for item in values if item.operator).items())),
        consumed, julia_loop_proof)


def apply_julia_frontend(program: TypedProgram, source_hash: str | None,
                         profile: str | None) -> TypedProgram:
    authenticate_julia_frontend(program, source_hash, profile)
    return program


__all__ = (
    "KEY", "PROFILE", "KEYS", "PREPARED_KEYS", "PROFILES",
    "PREPARED_PROFILES", "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS",
    "REQUIRED_COMPANION_PROFILES", "SOURCE_UNIFORMS", "RUNTIME_UNIFORM_ABI",
    "OUTPUT_ABI", "FUNCTION_NAMES", "FUNCTION_IDS", "STRUCT_NAME",
    "STRUCT_FIELD_NAMES", "OUT_PARAMETERS", "LOOPS", "COUNTED_LOOP_SUMMARY",
    "JULIA_MAX_TRIP_COUNT", "JULIA_COUNTED_LOOP_SUMMARY",
    "JuliaFrontendProof", "JuliaLoopProof", "authenticate_julia_frontend",
    "apply_julia_frontend",
)
