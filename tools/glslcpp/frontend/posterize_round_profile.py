"""Closed identity profile for Posterize's one standalone ``round`` site.

Unlike Gather Sorted's ``round``, which is immediately wrapped by an ``int``
constructor and lowered as a single fused round-to-int operation, Posterize's
``round(levels_raw)`` is consumed directly as a ``float`` by
``max(round(levels_raw), MIN_LEVELS)``. The reference JS materializes GLSL
``round()`` as ``Math.round`` -- round-half-toward-positive-infinity, neither
the GLSL spec's round-half-to-even nor ``std::round``'s round-half-away-from-
zero -- and narrows the scalar result to f32 immediately on return
(``glsl-runtime.js`` ``#unary``: ``F32(operation(value))``), before the
surrounding ``max`` ever sees it. ``levels_raw`` is always non-negative here
(``max(levels, 0.0)``), so the well-known ``Math.round(-0.5) == -0`` versus
``floor(x + 0.5) == +0`` divergence never arises in this program's domain,
but the round site itself must still be reached only by exact node identity,
the same zero-vocabulary-growth pattern as every other admitted builtin in
this generator.

This profile is deliberately independent of, and not mutually exclusive
with, ``derivative-admission-v1`` -- Posterize also carries one ``fwidth``
call, admitted separately by that profile. Grade's LUMA-weights/index-
expression pair is the precedent for two profiles legitimately coexisting on
one program key.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "posterize-round-admission-v1"
POSTERIZE_KEY = "filter/posterize:posterize"

RAW_SOURCE_BYTES = 2630
RAW_SOURCE_SHA256 = "460910a8d1103eca5cc0b4df82f39fd91fbc447b9a815250ae7d34dfab8ee5b2"
NORMALIZED_SOURCE_BYTES = 2471
NORMALIZED_SOURCE_SHA256 = "4781d189690f57de2b57aebaaa946eba004b1c57272f32a18d1f0ce06ce44393"
FUNCTIONS_SHA256 = "7bdcf13444da35b93bcae7c4758f92d46c26f0316f1ec4308bd1bc6e1c93e977"
WHOLE_PROGRAM_SHA256 = "74adeb96fe8c6d4a916b0b54b29ce0f9ca2dbce7f7609f3582dcf51d82f4b6e8"
INTERFACE_SHA256 = "e53cc14ee2e987c2682722edd2870f0b617f1c28cae66e56e47aebe82548b81d"

_MAIN_ID = 20
_MAIN_SPAN = "54:1-96:2"
_FUNCTION_INVENTORY = (
    (17, "clamp_01", "float", 1, 1, "16:1-18:2"),
    (18, "linear_to_srgb_component", "float", 1, 2, "27:1-32:2"),
    (19, "linear_to_srgb_rgb", "vec3", 1, 1, "42:1-48:2"),
    (20, "main", "void", 0, 19, "54:1-96:2"),
    (21, "pow_vec3", "vec3", 2, 1, "50:1-52:2"),
    (22, "srgb_to_linear_component", "float", 1, 2, "20:1-25:2"),
    (23, "srgb_to_linear_rgb", "vec3", 1, 1, "34:1-40:2"),
)

STATEMENT_SHA256 = "a6f146726b03e4e0179a9052e198d8fe91bba4c28826dd40dfc9e7e50f6447b0"
_STATEMENT_SPAN = "60:5-60:65"
_STATEMENT_INDEX = 4

_DECL_SYMBOL_ID = 29
_DECL_SYMBOL_NAME = "levels_quantized"

_PARENT_SPAN = "60:30-60:64"
PARENT_SHA256 = "e9f9e3b934689555dd37a2923f64f3605ed96cd4f62c9ba5d489bec544d72872"
_SIBLING_SHA256 = "24740e468fa49b3be171d661e34d915d024e57b5180c52e9030278b488b4aea6"

_NODE_SPAN = "60:34-60:51"
ROUND_SHA256 = "20cd4f7a79809fe02ea5990311c12696d5f70e0affabd9a6320fb122bf3abdd5"
ARGUMENT_SHA256 = "ad903a68ec36e1f6b6a519ebb4e4bbcacd99ddf777a0fbf243c13efc98e5ce9a"
_NODE_SIGNATURE_ID = -38

_RESOURCES = (
    ("tileOffset", "fullResolution", "inputTex", "levels", "gamma", "antialias"),
    ("inputTex",), ("fragColor",), True, True,
)
_BINDINGS = (
    (1, "tileOffset", "vec2", "uniform", False),
    (2, "fullResolution", "vec2", "uniform", False),
    (3, "inputTex", "sampler2D", "uniform", False),
    (4, "levels", "float", "uniform", False),
    (5, "gamma", "float", "uniform", False),
    (6, "antialias", "bool", "uniform", False),
    (7, "fragColor", "vec4", "output", True),
    (8, "MIN_LEVELS", "float", "const", False),
    (9, "MIN_GAMMA", "float", "const", False),
)

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

__all__ = ("PROFILE", "POSTERIZE_KEY",
           "authenticate_posterize_round_admission",
           "apply_posterize_round_admission")


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


def authenticate_posterize_round_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedExpression:
    """Return the exact authenticated ``round`` node after full authentication."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (program.key != POSTERIZE_KEY or source_hash != RAW_SOURCE_SHA256
            or len(raw) != RAW_SOURCE_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SOURCE_SHA256
            or len(normalized) != NORMALIZED_SOURCE_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SOURCE_SHA256
            or program.preprocessor_defines or program.body_status != "analyzed"):
        raise _fail("source, key, define, or body profile mismatch")
    if (_sha(program.functions) != FUNCTIONS_SHA256
            or _whole_program_fingerprint(program) != WHOLE_PROGRAM_SHA256
            or _interface_fingerprint(program) != INTERFACE_SHA256):
        raise _fail("function, whole-program, or interface profile mismatch")
    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    functions_sorted = tuple(sorted(program.functions, key=lambda item: item.id))
    if tuple((item.id, item.name, item.return_type.display(), len(item.parameters),
              len(item.body), _span(item)) for item in functions_sorted) != _FUNCTION_INVENTORY:
        raise _fail("function inventory mismatch")
    main = next((item for item in functions_sorted if item.id == _MAIN_ID), None)
    if main is None or main.name != "main" or _span(main) != _MAIN_SPAN:
        raise _fail("main identity mismatch")

    statement = main.body[_STATEMENT_INDEX]
    if (statement.kind != "decl" or len(statement.expressions) != 1
            or _span(statement) != _STATEMENT_SPAN
            or _sha(statement) != STATEMENT_SHA256):
        raise _fail("declaration statement profile mismatch")
    declaration = statement.expressions[0]
    if (declaration.kind != "declaration"
            or declaration.symbol_id != _DECL_SYMBOL_ID
            or declaration.symbol is None
            or declaration.symbol.name != _DECL_SYMBOL_NAME
            or declaration.symbol.storage != "local"
            or not declaration.symbol.writable
            or declaration.type.display() != "float"
            or len(declaration.children) != 1):
        raise _fail("levels_quantized declaration profile mismatch")
    parent = declaration.children[0]
    if (parent.kind != "builtin" or parent.callee != "max"
            or parent.type.display() != "float" or parent.category != "rvalue"
            or len(parent.children) != 2 or _span(parent) != _PARENT_SPAN
            or _sha(parent) != PARENT_SHA256
            or _sha(parent.children[1]) != _SIBLING_SHA256):
        raise _fail("round-consuming max parent profile mismatch")
    round_value = parent.children[0]
    if (round_value.kind != "builtin" or round_value.callee != "round"
            or round_value.signature_id != _NODE_SIGNATURE_ID
            or round_value.type.display() != "float"
            or round_value.category != "rvalue"
            or len(round_value.children) != 1
            or round_value.children[0].type.display() != "float"
            or _span(round_value) != _NODE_SPAN
            or _sha(round_value) != ROUND_SHA256
            or _sha(round_value.children[0]) != ARGUMENT_SHA256):
        raise _fail("round site or argument profile mismatch")

    # Census the WHOLE program: an extra round site anywhere else is a hard
    # failure, not an unnoticed extra.
    all_rounds: list[TypedExpression] = []
    for function in functions_sorted:
        for item in function.body:
            for value in _walk_statement(item):
                if (isinstance(value, TypedExpression) and value.kind == "builtin"
                        and value.callee == "round"):
                    all_rounds.append(value)
    if len(all_rounds) != 1 or all_rounds[0] is not round_value:
        raise _fail("expected exactly one owned round site")

    bindings = tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable)
        for item in program.declarations)
    if bindings != _BINDINGS:
        raise _fail("binding profile mismatch")
    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != _RESOURCES):
        raise _fail("resource profile mismatch")

    return round_value


def apply_posterize_round_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate and return the same immutable program object."""
    authenticate_posterize_round_admission(program, source_hash, profile)
    return program
