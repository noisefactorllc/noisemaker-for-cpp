"""Prepared, source-locked frontend admission for ``filter/osd``.

This is deliberately a prepared lane.  It does not register a typed-slice
row or change the shared validator/emitter.  OSD's source is analyzable, but
integration still needs an exact global ``int[80]`` materialization and the
second-order bitwise carrier (``^``, ``>>``, and ``&``).
"""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import NamedTuple

from .typed_ir import TypedExpression, TypedProgram


KEY = "filter/osd:osd"
PROFILE = "osd-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}
OSD_FRONTEND_KEYS = frozenset(PREPARED_PROFILES)
ALLOWED_ROW_FIELDS = {
    KEY: frozenset({"defines", "program_key", "osd_frontend_profile"}),
}
REQUIRED_COMPANION_PROFILES = {KEY: ()}

RAW_BYTES = 6164
RAW_SHA256 = "c45adaf30ecef6fb7f83a4f3995e671df0caaa47bfeceba8bb9bfe2c07427443"
NORMALIZED_BYTES = 4915
NORMALIZED_SHA256 = "407bcdae0bd1fbf888c9d6fed4ffb966960fd41be003874a6a0123fd1f9159f0"
FUNCTIONS_SHA256 = "4908190e102178eed6ab485fe90ba0bcf92419b679284719d0981a2a78c0694f"
WHOLE_SHA256 = "42e9156e230c71c53819680f819ebc0358517b994c8f3cf5af540cee60e10906"
INTERFACE_SHA256 = "4af28ccb2f9620ee0c4b710ac65b2f856b1ffdb7bd820d1c73dce9604c86883c"

# This is the source interface, not a guessed UI interface.  In particular,
# seed is a GLSL float even though the effect metadata exposes it as an int.
SOURCE_UNIFORMS = (
    ("inputTex", "sampler2D"), ("resolution", "vec2"),
    ("tileOffset", "vec2"), ("fullResolution", "vec2"),
    ("renderScale", "float"), ("alpha", "float"),
    ("seed", "float"), ("speed", "float"), ("time", "float"),
    ("corner", "int"),
)
RUNTIME_UNIFORM_ABI = (
    ("resolution", "Vec2"), ("tileOffset", "Vec2"),
    ("fullResolution", "Vec2"), ("renderScale", "float"),
    ("alpha", "float"), ("seed", "float"), ("speed", "float"),
    ("time", "float"), ("corner", "int32"),
)
SAMPLER_RUNTIME_ABI = ("inputTex", "sampler2D", "const Surface&")
TEXTURE_SIZE_CONTRACT = ("textureSize", "ivec2", 0)
TEXEL_FETCH_CONTRACT = ("texelFetch", "vec4", 0, "bottom-left")

# These are integration requirements, not an assertion that the current
# emitter already provides them.
GLOBAL_ARRAY_NATIVE_REQUIREMENT = (
    "int[80]", "std::array<std::int32_t, 80>")
BITWISE_REQUIREMENT = ("^", ">>", "&")

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)
_EXPECTED_RESOURCE = (
    tuple(item[0] for item in SOURCE_UNIFORMS), ("inputTex",), ("fragColor",),
    True, False,
)
_EXPECTED_COUNTED_LOOP = (0, 0, 0, 0, 0, True)
_EXPECTED_EXPR_KINDS = {
    "id": 167, "literal": 142, "binary": 101, "declaration": 46,
    "construct": 23, "swizzle": 16, "assign": 15, "builtin": 14,
    "call": 6, "conditional": 1, "index": 1,
}
_EXPECTED_OPERATORS = {
    "*": 20, "-": 19, "=": 15, "+": 13, "<": 11, "||": 6,
    ">=": 6, "/": 5, "^": 4, "&&": 4, ">>": 4, "==": 3,
    "&": 2, "%": 2, ">": 1, "<=": 1,
}
_EXPECTED_BUILTINS = (
    ("max", "int", "77:18-77:62"),
    ("textureSize", "ivec2", "84:21-84:45"),
    ("max", "int", "87:17-87:39"),
    ("max", "int", "88:18-88:40"),
    ("texelFetch", "vec4", "92:18-92:48"),
    ("clamp", "float", "94:25-94:47"),
    ("max", "int", "97:24-97:51"),
    ("max", "float", "106:27-106:41"),
    ("floor", "float", "164:33-164:64"),
    ("max", "float", "164:46-164:63"),
    ("clamp", "vec3", "176:26-176:51"),
    ("max", "vec3", "182:22-182:53"),
    ("mix", "vec3", "183:20-183:57"),
    ("clamp", "vec3", "184:22-184:46"),
)
_EXPECTED_CALLS = (
    ("pcg", "59:12-59:52"), ("pcg", "63:12-63:62"),
    ("hash2", "63:16-63:27"), ("hash2", "109:31-109:52"),
    ("hash3", "165:31-165:81"), ("sample_glyph", "168:20-168:72"),
)
_EXPECTED_BITWISE = (
    ("^", "uint", "59:16-59:51", ("uint", "uint")),
    ("^", "uint", "63:16-63:61", ("uint", "uint")),
    ("&", "int", "98:56-98:89", ("int", "int")),
    ("^", "uint", "54:19-54:58", ("uint", "uint")),
    (">>", "uint", "54:19-54:49", ("uint", "uint")),
    (">>", "uint", "54:30-54:42", ("uint", "uint")),
    ("^", "uint", "55:13-55:32", ("uint", "uint")),
    (">>", "uint", "55:13-55:24", ("uint", "uint")),
    ("&", "int", "72:19-72:39", ("int", "int")),
    (">>", "int", "72:19-72:34", ("int", "int")),
)
_GLYPHS = (
    "0x3C", "0x42", "0x42", "0x42", "0x42", "0x42", "0x3C", "0x00",
    "0x18", "0x08", "0x08", "0x08", "0x1C", "0x1C", "0x1C", "0x00",
    "0x1C", "0x04", "0x04", "0x1C", "0x10", "0x10", "0x1C", "0x00",
    "0x1C", "0x04", "0x04", "0x1C", "0x06", "0x06", "0x1E", "0x00",
    "0x60", "0x60", "0x60", "0x60", "0x66", "0x7E", "0x06", "0x00",
    "0x3C", "0x20", "0x20", "0x3C", "0x04", "0x04", "0x3C", "0x00",
    "0x78", "0x48", "0x40", "0x40", "0x7E", "0x42", "0x7E", "0x00",
    "0x3C", "0x24", "0x04", "0x0C", "0x08", "0x08", "0x08", "0x00",
    "0x3C", "0x24", "0x24", "0x7E", "0x66", "0x66", "0x7E", "0x00",
    "0x3E", "0x22", "0x22", "0x3E", "0x06", "0x06", "0x06", "0x00",
)


class ArrayRecord(NamedTuple):
    name: str
    symbol_id: int
    type_name: str
    element_type: str
    extent: int
    storage: str
    writable: bool
    span: str
    initializer_sha256: str


class FrontendProof(NamedTuple):
    program_key: str
    global_array: ArrayRecord
    sampler_builtins: tuple[str, ...]
    bitwise_nodes: tuple[TypedExpression, ...]
    pcg_function: object
    pcg_bitwise_nodes: tuple[TypedExpression, ...]
    hash_modulo_nodes: tuple[TypedExpression, ...]
    consumed_objects: tuple[object, ...]


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
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _expressions(program: TypedProgram) -> tuple[TypedExpression, ...]:
    values = []
    for declaration in program.declarations:
        if declaration.initializer is not None:
            values.extend(_walk_expression(declaration.initializer))
    for function in program.functions:
        for statement in function.body:
            values.extend(_walk_statement(statement))
    return tuple(values)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _decl_lock(program: TypedProgram):
    return tuple((
        item.symbol.id, item.symbol.name, item.type.display(),
        item.symbol.storage, item.symbol.writable, _span(item),
    ) for item in program.declarations)


def _function_expressions(function):
    values = []
    for statement in function.body:
        values.extend(_walk_statement(statement))
    return tuple(values)


def _function_lock(program: TypedProgram):
    return tuple((
        function.id, function.name, function.return_type.display(),
        tuple((item.id, item.name, item.type.display(), item.storage,
               item.writable, item.direction) for item in function.parameters),
        _span(function),
    ) for function in program.functions)


def _bitwise_lock(nodes):
    return tuple((
        item.operator, item.type.display(), _span(item),
        tuple(child.type.display() for child in item.children),
    ) for item in nodes)


def authenticate_osd_frontend(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> FrontendProof:
    """Authenticate the complete OSD frontend shape and return live nodes."""
    if program.key != KEY:
        raise _fail("selected key is not filter/osd:osd")
    if profile != PROFILE:
        raise _fail("exact prepared profile required")
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
    if program.preprocessor_defines or program.body_status != "analyzed":
        raise _fail("preprocessor or body status mismatch")
    if any(getattr(program, field) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is present")
    proof = program.counted_loop_proof
    if proof is None or (
            proof.loop_count, proof.unproved_loop_count,
            proof.max_effective_depth, proof.max_lexical_product,
            proof.entrypoint_charge, proof.call_graph_acyclic) != _EXPECTED_COUNTED_LOOP:
        raise _fail("counted-loop proof mismatch")

    resource = (
        program.resources.uniforms, program.resources.samplers,
        program.resources.outputs, program.resources.uses_texture,
        program.resources.uses_derivatives,
    )
    if resource != _EXPECTED_RESOURCE:
        raise _fail("resource or sampler interface mismatch")
    if _decl_lock(program) != (
        (1, "inputTex", "sampler2D", "uniform", False, "9:1-9:28"),
        (2, "resolution", "vec2", "uniform", False, "10:1-10:25"),
        (3, "tileOffset", "vec2", "uniform", False, "11:1-11:25"),
        (4, "fullResolution", "vec2", "uniform", False, "12:1-12:29"),
        (5, "renderScale", "float", "uniform", False, "13:1-13:27"),
        (6, "alpha", "float", "uniform", False, "14:1-14:21"),
        (7, "seed", "float", "uniform", False, "15:1-15:20"),
        (8, "speed", "float", "uniform", False, "16:1-16:21"),
        (9, "time", "float", "uniform", False, "17:1-17:20"),
        (10, "corner", "int", "uniform", False, "18:1-18:20"),
        (11, "fragColor", "vec4", "output", True, "20:1-20:41"),
        (12, "GLYPHS", "int[80]", "const", False, "24:1-45:3"),
        (13, "GLYPH_W", "int", "const", False, "47:1-47:23"),
        (14, "GLYPH_H", "int", "const", False, "48:1-48:23"),
        (15, "BASE_SCALE", "int", "const", False, "49:1-49:26"),
        (16, "BASE_PADDING", "int", "const", False, "50:1-50:29"),
    ):
        raise _fail("declaration interface census mismatch")

    expressions = _expressions(program)
    if Counter(item.kind for item in expressions) != Counter(_EXPECTED_EXPR_KINDS):
        raise _fail("expression-kind cardinality mismatch")
    if Counter(item.operator for item in expressions if item.operator is not None) != Counter(_EXPECTED_OPERATORS):
        raise _fail("operator cardinality mismatch")
    builtins = tuple((item.callee, item.type.display(), _span(item))
                     for item in expressions if item.kind == "builtin")
    if builtins != _EXPECTED_BUILTINS:
        raise _fail("builtin census mismatch")
    calls = tuple((item.callee, _span(item))
                  for item in expressions if item.kind == "call")
    if calls != _EXPECTED_CALLS:
        raise _fail("call census mismatch")

    array = next((item for item in program.declarations
                  if item.symbol.name == "GLYPHS"), None)
    if array is None or array.initializer is None:
        raise _fail("GLYPHS declaration or initializer missing")
    if (array.initializer.kind != "construct"
            or array.initializer.type.display() != "int[80]"
            or len(array.initializer.children) != 80
            or tuple(item.literal for item in array.initializer.children) != _GLYPHS
            or any(item.kind != "literal" or item.type.display() != "int"
                   for item in array.initializer.children)):
        raise _fail("GLYPHS literal payload mismatch")

    indexes = tuple(item for item in expressions if item.kind == "index")
    if len(indexes) != 1:
        raise _fail("global-array index cardinality mismatch")
    index = indexes[0]
    if (_span(index), index.type.display(), index.children[0].symbol_id,
            index.children[0].symbol.name, index.children[1].kind,
            index.children[1].type.display()) != (
                "71:15-71:37", "int", 12, "GLYPHS", "binary", "int"):
        raise _fail("global-array index shape mismatch")

    bitwise = tuple(item for item in expressions
                    if item.kind == "binary" and item.operator in BITWISE_REQUIREMENT)
    if _bitwise_lock(bitwise) != _EXPECTED_BITWISE:
        raise _fail("bitwise census mismatch")
    sampler = tuple(item for item in expressions
                    if item.kind == "builtin"
                    and item.callee in ("textureSize", "texelFetch"))
    if tuple(item.callee for item in sampler) != ("textureSize", "texelFetch"):
        raise _fail("sampler builtin cardinality mismatch")
    texture_size, texel_fetch = sampler
    if (texture_size.children[0].symbol.name,
            texture_size.children[0].type.display(),
            texture_size.children[1].literal_value) != ("inputTex", "sampler2D", 0):
        raise _fail("textureSize sampler contract mismatch")
    if (texel_fetch.children[0].symbol.name,
            texel_fetch.children[0].type.display(),
            texel_fetch.children[1].symbol.name,
            texel_fetch.children[1].type.display(),
            texel_fetch.children[2].literal_value) != (
                "inputTex", "sampler2D", "coord", "ivec2", 0):
        raise _fail("texelFetch sampler contract mismatch")

    pcg_function = next((item for item in program.functions
                         if item.name == "pcg"), None)
    if (pcg_function is None or pcg_function.return_type.display() != "uint"
            or tuple(item.name for item in program.functions)
            != ("hash2", "hash3", "main", "pcg", "sample_glyph")):
        raise _fail("pcg function identity mismatch")
    pcg_expressions = _function_expressions(pcg_function)
    pcg_bitwise = tuple(item for item in pcg_expressions
                        if item.kind == "binary"
                        and item.operator in BITWISE_REQUIREMENT)
    hash_modulos = tuple(item for item in expressions
                         if item.kind == "binary" and item.operator == "%")
    if len(pcg_bitwise) != 5 or len(hash_modulos) != 2:
        raise _fail("pcg Number/ToInt32 node census mismatch")

    consumed = (array, array.initializer, index, texture_size, texel_fetch,
                *bitwise)
    if len(consumed) != 15 or len({id(item) for item in consumed}) != 15:
        raise _fail("object-identity ledger is not disjoint")
    for item in consumed:
        occurrences = sum(value is item for value in expressions)
        if item is array:
            occurrences = sum(value is array for value in program.declarations)
        if occurrences != 1:
            raise _fail("object-identity ledger cardinality mismatch")

    return FrontendProof(
        KEY,
        ArrayRecord("GLYPHS", array.symbol.id, array.type.display(), "int", 80,
                    array.symbol.storage, array.symbol.writable, _span(array),
                    _sha(array.initializer)),
        ("textureSize", "texelFetch"), bitwise, pcg_function, pcg_bitwise,
        hash_modulos, consumed)


def apply_osd_frontend(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate OSD and retain the exact typed tree (prepared identity)."""
    authenticate_osd_frontend(program, source_hash, profile)
    return program


__all__ = (
    "KEY", "PROFILE", "KEYS", "PROFILES", "PREPARED_KEYS",
    "PREPARED_PROFILES", "OSD_FRONTEND_KEYS", "ALLOWED_ROW_FIELDS",
    "REQUIRED_COMPANION_PROFILES", "SOURCE_UNIFORMS", "RUNTIME_UNIFORM_ABI",
    "SAMPLER_RUNTIME_ABI", "TEXTURE_SIZE_CONTRACT", "TEXEL_FETCH_CONTRACT",
    "GLOBAL_ARRAY_NATIVE_REQUIREMENT", "BITWISE_REQUIREMENT", "ArrayRecord",
    "FrontendProof", "authenticate_osd_frontend", "apply_osd_frontend",
)
