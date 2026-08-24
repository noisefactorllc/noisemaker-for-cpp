"""Exact identity profile for Smooth Edge's sole source ``const vec3``."""

from __future__ import annotations

import hashlib
import struct

from .typed_ir import TypedDeclaration, TypedExpression, TypedProgram, TypedStatement


PROFILE = "smooth-edge-luma-weights-v1"
SMOOTH_EDGE_KEY = "filter/smooth:smoothEdge"

_RAW_BYTES = 1554
_RAW_SHA256 = "b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265"
_NORMALIZED_BYTES = 1235
_NORMALIZED_SHA256 = "42f61c507d633c07415bc816b6ba61f8a862642429943be1c0c1208c97b90f7c"
_FUNCTIONS_SHA256 = "8a7f2ac058a23e438f31787c55d235235271429fb79fc1d085c4dd1ba08cd4fc"
_WHOLE_SHA256 = "5586658ce1f621887647e5fb77990606e8637b7d759d2c9f1096f26b7385cd89"
_INTERFACE_SHA256 = "9149a7b19b47edea7179f8460443ee67c4a314bcb3ed2a83b7a68d91550f4930"
_DECLARATION_SHA256 = "be8644a44ad3d2710e4dfaa87045257a5bd7c0e7e0a363c12893ea77c3d2ee27"
_INITIALIZER_SHA256 = "57ee749ccff2d5029ccbd10b7ce01320fdeb694bf2d02d5835a0e6ccd5836104"
_READ_SHA256 = "df251d3d8461278afd63b36f1f3cef0d48777196908b8571a11d65dc54b83880"
_PARENT_SHA256 = "0f4d0fe02d9ee23557db69dfaca7ffa5c2542295d385c0d075f5b7e374fa43ae"
_RGB_SHA256 = "0c947970257b7042745712013dccbc9cbe816a36827840e4e403bd36c3e06ef3"
_PROFILE_SHA256 = "fbb3808e4392e3b3fa56a48965a36a47ce1a438626c9acdc6d33613fd3f57b80"
_LUMINANCE_SHA256 = "454e07a023decf6855ebb1b00e4e34013a0926b9b2ce43c08d6dd257f4538b8a"
_MAIN_SHA256 = "91808a5a46522dc3c72f54733faea98e29621f9ac305a88ef5c7e5c2709e16aa"
_READ_PATH = (0, "e0", 0, 1)
_LANES = (
    ("0.299", 0.299, "12:32-12:37",
     "06162ef141f3a4066bbb35d0ec773002c341ec99f3c3b19a024bf381d5486c27",
     0x3E991687),
    ("0.587", 0.587, "12:39-12:44",
     "6f17e5a19288943b912be887ac5b4390afbab72c3e2c6786d78d64dd068f285f",
     0x3F1645A2),
    ("0.114", 0.114, "12:46-12:51",
     "8af04ca08c0c38d7ad1fb93f89ce44698bbb43bd43ca80060a723dd089806e41",
     0x3DE978D5),
)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

__all__ = (
    "PROFILE",
    "SMOOTH_EDGE_KEY",
    "authenticate_smooth_edge_luma_weights",
    "apply_smooth_edge_luma_weights",
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_fingerprint(program: TypedProgram) -> str:
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


def _profile_tuple() -> tuple[object, ...]:
    return (
        PROFILE,
        SMOOTH_EDGE_KEY,
        _RAW_SHA256,
        {},
        (7, "LUMA_WEIGHTS", "const", "vec3", "12:1-12:53",
         _DECLARATION_SHA256, _INITIALIZER_SHA256,
         tuple((lexeme, value, span, digest)
               for lexeme, value, span, digest, _ in _LANES)),
        (9, "luminance", _READ_PATH, "15:21-15:33", _READ_SHA256,
         _PARENT_SHA256, 1),
        _FUNCTIONS_SHA256,
        _WHOLE_SHA256,
        _INTERFACE_SHA256,
    )


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _read_at(function: object) -> tuple[TypedExpression, TypedExpression]:
    statement = function.body[_READ_PATH[0]]
    parent = statement.expressions[int(_READ_PATH[1][1:])]
    if _READ_PATH[2] != 0:
        raise _fail("invalid frozen expression-root marker")
    read = parent.children[_READ_PATH[3]]
    return parent, read


def authenticate_smooth_edge_luma_weights(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedDeclaration, TypedExpression]:
    """Authenticate and return only the exact Smooth declaration/read pair."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != SMOOTH_EDGE_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole_fingerprint(program) != _WHOLE_SHA256
            or _interface_fingerprint(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    proof = program.counted_loop_proof
    if (proof is None or proof.loop_count != 0 or proof.unproved_loop_count != 0
            or proof.max_effective_depth != 0
            or proof.max_lexical_product != 0
            or proof.entrypoint_charge != 0
            or not proof.call_graph_acyclic):
        raise _fail("loop or call graph profile mismatch")

    if len(program.declarations) != 7:
        raise _fail("declaration cardinality mismatch")
    declaration = program.declarations[6]
    symbol = declaration.symbol
    initializer = declaration.initializer
    if (symbol.id != 7 or symbol.name != "LUMA_WEIGHTS"
            or symbol.storage != "const" or symbol.writable
            or symbol.direction != "in" or symbol.type.display() != "vec3"
            or declaration.type.display() != "vec3"
            or _span(declaration) != "12:1-12:53"
            or _sha(declaration) != _DECLARATION_SHA256
            or initializer is None or initializer.kind != "construct"
            or initializer.type.display() != "vec3"
            or initializer.constructor_type is None
            or initializer.constructor_type.display() != "vec3"
            or initializer.category != "rvalue"
            or _span(initializer) != "12:27-12:52"
            or _sha(initializer) != _INITIALIZER_SHA256
            or len(initializer.children) != 3):
        raise _fail("declaration or initializer profile mismatch")
    for lane, expected in zip(initializer.children, _LANES):
        lexeme, value, span, digest, bits = expected
        lane_bits = struct.unpack("<I", struct.pack("<f", lane.literal_value))[0]
        if (lane.kind != "literal" or lane.type.display() != "float"
                or lane.category != "rvalue" or lane.literal != lexeme
                or lane.literal_value != value or _span(lane) != span
                or _sha(lane) != digest or lane_bits != bits):
            raise _fail("literal lane profile mismatch")

    if (len(program.functions) != 2
            or (program.functions[0].id, program.functions[0].name,
                len(program.functions[0].parameters),
                len(program.functions[0].body), _sha(program.functions[0]))
            != (9, "luminance", 1, 1, _LUMINANCE_SHA256)
            or (program.functions[1].id, program.functions[1].name,
                len(program.functions[1].parameters),
                len(program.functions[1].body), _sha(program.functions[1]))
            != (10, "main", 0, 13, _MAIN_SHA256)):
        raise _fail("function profile mismatch")
    parameter = program.functions[0].parameters[0]
    if (parameter.id, parameter.name, parameter.type.display(),
            parameter.storage, parameter.direction) != (
            8, "rgb", "vec3", "parameter", "in"):
        raise _fail("luminance parameter profile mismatch")

    parent, read = _read_at(program.functions[0])
    if (read.kind != "id" or read.symbol_id != 7
            or read.symbol is not symbol or read.type.display() != "vec3"
            or read.category != "readonly lvalue"
            or _span(read) != "15:21-15:33" or _sha(read) != _READ_SHA256
            or parent.kind != "builtin" or parent.callee != "dot"
            or parent.signature_id != -13 or parent.type.display() != "float"
            or parent.category != "rvalue" or len(parent.children) != 2
            or parent.children[1] is not read
            or _span(parent) != "15:12-15:34" or _sha(parent) != _PARENT_SHA256
            or _sha(parent.children[0]) != _RGB_SHA256):
        raise _fail("resolved read or dot parent profile mismatch")
    reads: list[tuple[int, TypedExpression]] = []
    luminance_calls = 0
    texel_fetches = 0
    texture_sizes = 0
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if value.kind == "id" and value.symbol_id == 7:
                    reads.append((function.id, value))
                if value.kind == "call" and value.signature_id == 9:
                    luminance_calls += 1
                if value.kind == "builtin" and value.callee == "texelFetch":
                    texel_fetches += 1
                if value.kind == "builtin" and value.callee == "textureSize":
                    texture_sizes += 1
    if reads != [(9, read)]:
        raise _fail("resolved read cardinality or ownership mismatch")
    if (luminance_calls, texel_fetches, texture_sizes) != (5, 6, 1):
        raise _fail("call or resource site census mismatch")
    return declaration, read


def apply_smooth_edge_luma_weights(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_smooth_edge_luma_weights(program, source_hash, profile)
    return program
