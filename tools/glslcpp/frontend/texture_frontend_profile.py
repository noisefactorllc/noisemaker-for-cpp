"""Source-bound frontend admission for ``filter/texture``.

The row-206 typed slice now carries this exact Texture admission.  It proves
the typed program shape and keeps the integration scope bound to the pinned
source: varying and integer hash operators, const ``Z_LOOP``, sampler ABI,
and their validator/emitter admissions.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import NamedTuple

from .typed_ir import TypedExpression, TypedProgram


KEY = "filter/texture:texture"
PROFILE = "texture-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}
TEXTURE_FRONTEND_KEYS = frozenset(PREPARED_PROFILES)
ALLOWED_ROW_FIELDS = {
    KEY: frozenset({"defines", "program_key", "texture_frontend_profile"}),
}
REQUIRED_COMPANION_PROFILES = {KEY: ()}

RAW_BYTES = 14344
RAW_SHA256 = "8e95251ef9a7789b1de4e51718ab3bebd9fc6d20db8acd0969191e288ec7454c"
NORMALIZED_BYTES = 10411
NORMALIZED_SHA256 = "0bc3450da3fd8a9fa6834a750689d085b4c427c9ed2a8906f610ca3855bc5ff9"
FUNCTIONS_SHA256 = "cb050bb74a7ba8ab5bb4754cfbd86e4dcbd8f6f91037c013d10fef143c6aa590"
WHOLE_SHA256 = "be332c46aea5fbce4613e9be631b1585930045767abecd24f035d20427f2df21"
INTERFACE_SHA256 = "5678a319d26e55b2035ee9b6df7f64eee996ee9bf4a9e58d05a50e3eda6bbe62"

SOURCE_UNIFORMS = (
    ("inputTex", "sampler2D"), ("time", "float"),
    ("alpha", "float"), ("scale", "float"), ("intensity", "float"),
    ("contrast", "float"), ("mono", "bool"), ("tileOffset", "vec2"),
    ("fullResolution", "vec2"),
)
RUNTIME_UNIFORM_ABI = (
    ("time", "float"), ("alpha", "float"), ("scale", "float"),
    ("intensity", "float"), ("contrast", "float"), ("mono", "bool"),
    ("tileOffset", "Vec2"), ("fullResolution", "Vec2"),
)
SAMPLER_RUNTIME_ABI = ("inputTex", "sampler2D", "const Surface&")
VARYING_RUNTIME_ABI = ("v_texCoord", "vec2", "context.uv", "read-only")
TEXTURE_SIZE_CONTRACT = ("textureSize", "ivec2", 0, "inputTex")
TEXTURE_SAMPLE_CONTRACT = ("texture", "vec4", "inputTex", "bottom-left", "linear")
MODE_DEFINE_CONTRACT = ("MODE", "int", "3", "compile-time-specialization")
GLOBAL_INT_REQUIREMENT = ("Z_LOOP", "const int", 2, "loop-free modulo divisor")
BITWISE_REQUIREMENT = ("uint", ("^", "^=", ">>", "&"), "uint32-wrap")
INVERSE_SQRT_REQUIREMENT = ("inversesqrt", "float", "gradient normalization")
NUMBER_PRESERVING_HASH_CONVERSION_CONTRACT = (
    "fast_hash", "construct", "float", "75:12-75:20", ("uint",),
)

_DECLARATIONS = (
    (1, "inputTex", "sampler2D", "uniform", False, "16:1-16:28"),
    (2, "time", "float", "uniform", False, "17:1-17:20"),
    (3, "alpha", "float", "uniform", False, "18:1-18:21"),
    (4, "scale", "float", "uniform", False, "19:1-19:21"),
    (5, "intensity", "float", "uniform", False, "20:1-20:25"),
    (6, "contrast", "float", "uniform", False, "21:1-21:24"),
    (7, "mono", "bool", "uniform", False, "22:1-22:19"),
    (8, "tileOffset", "vec2", "uniform", False, "23:1-23:25"),
    (9, "fullResolution", "vec2", "uniform", False, "24:1-24:29"),
    (10, "fragColor", "vec4", "output", True, "26:1-26:16"),
    (11, "PI", "float", "const", False, "28:1-28:32"),
    (12, "INV_UINT32_MAX", "float", "const", False, "29:1-29:49"),
    (13, "Z_LOOP", "int", "const", False, "30:1-30:22"),
    (14, "SHADE_GAIN", "float", "const", False, "31:1-31:30"),
)
_FUNCTIONS = (
    (77, "clamp01", "float", ((15, "value", "float", "parameter", True, "in"),), "33:1-35:2"),
    (78, "fade", "float", ((17, "t", "float", "parameter", True, "in"),), "42:1-44:2"),
    (79, "fast_hash", "float", ((21, "p", "ivec3", "parameter", True, "in"), (22, "salt", "uint", "parameter", True, "in")), "67:1-76:2"),
    (80, "freq_for_shape", "vec2", ((18, "base_freq", "float", "parameter", True, "in"), (19, "dims", "vec2", "parameter", True, "in")), "46:1-56:2"),
    (81, "hash_uint", "uint", ((20, "x", "uint", "parameter", True, "in"),), "58:1-65:2"),
    (82, "height_canvas", "float", ((33, "uv", "vec2", "parameter", True, "in"), (34, "base_freq", "vec2", "parameter", True, "in"), (35, "motion", "float", "parameter", True, "in")), "153:1-162:2"),
    (83, "height_crosshatch", "float", ((38, "uv", "vec2", "parameter", True, "in"), (39, "base_freq", "vec2", "parameter", True, "in")), "173:1-178:2"),
    (84, "height_field", "float", ((40, "uv", "vec2", "parameter", True, "in"), (41, "base_freq", "vec2", "parameter", True, "in"), (42, "motion", "float", "parameter", True, "in")), "182:1-184:2"),
    (85, "height_halftone", "float", ((36, "uv", "vec2", "parameter", True, "in"), (37, "base_freq", "vec2", "parameter", True, "in")), "165:1-170:2"),
    (86, "height_paper", "float", ((27, "uv", "vec2", "parameter", True, "in"), (28, "base_freq", "vec2", "parameter", True, "in"), (29, "motion", "float", "parameter", True, "in")), "114:1-131:2"),
    (87, "height_stucco", "float", ((30, "uv", "vec2", "parameter", True, "in"), (31, "base_freq", "vec2", "parameter", True, "in"), (32, "motion", "float", "parameter", True, "in")), "134:1-150:2"),
    (88, "main", "void", (), "286:1-325:2"),
    (89, "material_directional", "float", ((61, "globalPixel", "vec2", "parameter", True, "in"), (62, "motion", "float", "parameter", True, "in"), (63, "salt", "uint", "parameter", True, "in"), (64, "size", "float", "parameter", True, "in")), "237:1-246:2"),
    (90, "material_edge_mask", "float", ((69, "uv", "vec2", "parameter", True, "in"), (70, "pixelStep", "vec2", "parameter", True, "in")), "265:1-271:2"),
    (91, "material_fade", "vec2", ((49, "t", "vec2", "parameter", True, "in"),), "200:1-202:2"),
    (92, "material_gradient", "vec2", ((46, "p", "ivec2", "parameter", True, "in"), (47, "salt", "uint", "parameter", True, "in"), (48, "layer", "uint", "parameter", True, "in")), "194:1-198:2"),
    (93, "material_gradient_layer", "float", ((50, "p", "vec2", "parameter", True, "in"), (51, "salt", "uint", "parameter", True, "in"), (52, "layer", "uint", "parameter", True, "in")), "204:1-213:2"),
    (94, "material_hash", "uint", ((43, "p", "ivec2", "parameter", True, "in"), (44, "salt", "uint", "parameter", True, "in"), (45, "layer", "uint", "parameter", True, "in")), "186:1-192:2"),
    (95, "material_noise", "float", ((53, "globalPixel", "vec2", "parameter", True, "in"), (54, "cellSize", "vec2", "parameter", True, "in"), (55, "motion", "float", "parameter", True, "in"), (56, "salt", "uint", "parameter", True, "in")), "215:1-224:2"),
    (96, "material_soft", "float", ((57, "globalPixel", "vec2", "parameter", True, "in"), (58, "motion", "float", "parameter", True, "in"), (59, "salt", "uint", "parameter", True, "in"), (60, "size", "float", "parameter", True, "in")), "226:1-235:2"),
    (97, "material_sprinkles", "float", ((65, "globalPixel", "vec2", "parameter", True, "in"), (66, "motion", "float", "parameter", True, "in"), (67, "salt", "uint", "parameter", True, "in"), (68, "size", "float", "parameter", True, "in")), "248:1-263:2"),
    (98, "material_value", "float", ((71, "globalPixel", "vec2", "parameter", True, "in"), (72, "dims", "vec2", "parameter", True, "in"), (73, "uv", "vec2", "parameter", True, "in"), (74, "motion", "float", "parameter", True, "in"), (75, "salt", "uint", "parameter", True, "in")), "273:1-276:2"),
    (99, "s_curve01", "float", ((16, "value", "float", "parameter", True, "in"),), "37:1-40:2"),
    (100, "shape_material", "float", ((76, "raw", "float", "parameter", True, "in"),), "278:1-284:2"),
    (101, "value_noise", "float", ((23, "uv", "vec2", "parameter", True, "in"), (24, "freq", "vec2", "parameter", True, "in"), (25, "motion", "float", "parameter", True, "in"), (26, "salt", "uint", "parameter", True, "in")), "78:1-111:2"),
)
_EXPECTED_EXPR_KINDS = {"id": 391, "literal": 203, "binary": 186, "declaration": 118, "builtin": 79, "construct": 72, "call": 54, "swizzle": 50, "assign": 25, "post": 4, "conditional": 2, "unary": 2}
_EXPECTED_OPERATORS = {"*": 76, "+": 47, "-": 30, "/": 11, "^=": 8, "=": 7, "*=": 6, "^": 5, "<": 4, ">>": 4, "++": 4, "+=": 4, "%": 4, ">": 3, "<=": 3, "&": 1}


class FrontendProof(NamedTuple):
    program_key: str
    varying: tuple[str, str, int, str]
    sampler_builtins: tuple[str, ...]
    bitwise_nodes: tuple[TypedExpression, ...]
    bitwise_assignments: tuple[TypedExpression, ...]
    inverse_sqrt: TypedExpression
    number_preserving_hash_conversion: TypedExpression
    consumed_objects: tuple[object, ...]


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source, program.declarations,
                 program.functions, program.resources, program.body_status,
                 program.local_type_names, program.structs, program.uniform_blocks,
                 program.interface_symbols, program.builtin_symbols,
                 program.counted_loop_proof, program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources, program.local_type_names,
                 program.structs, program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _expressions(program: TypedProgram):
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


def authenticate_texture_frontend(program: TypedProgram, source_hash: str | None,
                                   profile: str | None) -> FrontendProof:
    if program.key != KEY:
        raise _fail("selected key is not filter/texture:texture")
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
    if tuple((d.symbol.id, d.symbol.name, d.type.display(), d.symbol.storage,
              d.symbol.writable, _span(d)) for d in program.declarations) != _DECLARATIONS:
        raise _fail("declaration interface census mismatch")
    if tuple((f.signature.id, f.name, f.return_type.display(),
              tuple((p.id, p.name, p.type.display(), p.storage, p.writable,
                     p.direction) for p in f.parameters), _span(f))
             for f in program.functions) != _FUNCTIONS:
        raise _fail("function identity census mismatch")
    if (program.resources.uniforms, program.resources.samplers,
            program.resources.outputs, program.resources.uses_texture,
            program.resources.uses_derivatives) != (
                tuple(x[0] for x in SOURCE_UNIFORMS), ("inputTex",),
                ("fragColor",), True, False):
        raise _fail("resource or sampler interface mismatch")
    if tuple((d.name, d.kind, d.canonical_value)
             for d in program.preprocessor_defines) != (MODE_DEFINE_CONTRACT[:3],):
        raise _fail("MODE define contract mismatch")
    if len(program.interface_symbols) != 1:
        raise _fail("varying interface census mismatch")
    varying = program.interface_symbols[0]
    if (varying.name, varying.type.display(), varying.storage, varying.writable) != (
            "v_texCoord", "vec2", "varying", False):
        raise _fail("v_texCoord varying contract mismatch")

    expressions = _expressions(program)
    if Counter(item.kind for item in expressions) != Counter(_EXPECTED_EXPR_KINDS):
        raise _fail("expression-kind cardinality mismatch")
    if Counter(item.operator for item in expressions if item.operator is not None) != Counter(_EXPECTED_OPERATORS):
        raise _fail("operator cardinality mismatch")
    texture_nodes = tuple(item for item in expressions
                          if item.kind == "builtin" and item.callee == "texture")
    size_nodes = tuple(item for item in expressions
                       if item.kind == "builtin" and item.callee == "textureSize")
    if len(texture_nodes) != 5 or len(size_nodes) != 1:
        raise _fail("sampler builtin cardinality mismatch")
    if any(node.children[0].symbol.name != "inputTex" for node in (*texture_nodes, *size_nodes)):
        raise _fail("sampler binding identity mismatch")
    if size_nodes[0].children[1].literal_value != 0:
        raise _fail("textureSize lod contract mismatch")
    bitwise_nodes = tuple(item for item in expressions
                          if item.kind == "binary" and item.operator in BITWISE_REQUIREMENT[1])
    bitwise_assignments = tuple(item for item in expressions
                                if item.kind == "assign"
                                and item.operator == "^=")
    inverse_sqrt_nodes = tuple(item for item in expressions
                               if item.kind == "builtin"
                               and item.callee == "inversesqrt")
    if tuple((node.operator, node.type.display(), _span(node)) for node in bitwise_nodes) != (
            ("^", "uint", "68:14-68:32"), (">>", "uint", "59:10-59:18"),
            (">>", "uint", "61:10-61:18"), (">>", "uint", "63:10-63:18"),
            ("^", "uint", "244:24-244:42"), ("&", "uint", "196:32-196:43"),
            (">>", "uint", "196:52-196:60"), ("^", "uint", "187:14-187:42"),
            ("^", "uint", "233:24-233:42"), ("^", "uint", "257:50-257:68")):
        raise _fail("bitwise identity census mismatch")
    if tuple((node.operator, node.type.display(), _span(node))
             for node in bitwise_assignments) != (
                 ("^=", "uint", "69:5-69:33"),
                 ("^=", "uint", "71:5-71:33"),
                 ("^=", "uint", "73:5-73:33"),
                 ("^=", "uint", "59:5-59:18"),
                 ("^=", "uint", "61:5-61:18"),
                 ("^=", "uint", "63:5-63:18"),
                 ("^=", "uint", "188:5-188:33"),
                 ("^=", "uint", "190:5-190:33")):
        raise _fail("bitwise assignment identity census mismatch")
    if any(node.children[0].type.display() != "uint"
           or node.children[1].type.display() != "uint"
           for node in bitwise_assignments):
        raise _fail("bitwise assignment type contract mismatch")
    if (len(inverse_sqrt_nodes) != 1
            or inverse_sqrt_nodes[0].type.display() != "float"
            or len(inverse_sqrt_nodes[0].children) != 1
            or inverse_sqrt_nodes[0].children[0].type.display() != "float"
            or _span(inverse_sqrt_nodes[0]) != "197:23-197:74"):
            raise _fail("inverse-square-root identity census mismatch")
    fast_hash = next(function for function in program.functions
                     if function.name == "fast_hash")
    fast_hash_expressions = tuple(
        item for statement in fast_hash.body for item in _walk_statement(statement))
    hash_conversions = tuple(
        item for item in fast_hash_expressions
        if item.kind == "construct"
        and item.type.display() == "float"
        and len(item.children) == 1
        and item.children[0].type.display() == "uint")
    if (len(hash_conversions) != 1
            or (fast_hash.name, hash_conversions[0].kind,
                hash_conversions[0].type.display(), _span(hash_conversions[0]),
                tuple(child.type.display()
                      for child in hash_conversions[0].children))
            != NUMBER_PRESERVING_HASH_CONVERSION_CONTRACT):
        raise _fail("hash Number-preserving conversion identity census mismatch")
    consumed = (varying, *texture_nodes, *size_nodes, *bitwise_nodes,
                *bitwise_assignments, inverse_sqrt_nodes[0],
                hash_conversions[0])
    if len({id(item) for item in consumed}) != len(consumed):
        raise _fail("object-identity ledger is not disjoint")
    return FrontendProof(KEY, (varying.name, varying.type.display(), varying.id,
                               _span(varying)), ("texture", "textureSize"),
                         bitwise_nodes, bitwise_assignments,
                         inverse_sqrt_nodes[0], hash_conversions[0], consumed)


def apply_texture_frontend(program: TypedProgram, source_hash: str | None,
                           profile: str | None) -> TypedProgram:
    authenticate_texture_frontend(program, source_hash, profile)
    return program


__all__ = ("KEY", "PROFILE", "KEYS", "PROFILES", "PREPARED_KEYS",
           "PREPARED_PROFILES", "TEXTURE_FRONTEND_KEYS", "ALLOWED_ROW_FIELDS",
           "REQUIRED_COMPANION_PROFILES", "SOURCE_UNIFORMS", "RUNTIME_UNIFORM_ABI",
           "SAMPLER_RUNTIME_ABI", "VARYING_RUNTIME_ABI", "TEXTURE_SIZE_CONTRACT",
           "TEXTURE_SAMPLE_CONTRACT", "MODE_DEFINE_CONTRACT", "GLOBAL_INT_REQUIREMENT",
           "BITWISE_REQUIREMENT", "INVERSE_SQRT_REQUIREMENT", "FrontendProof",
           "NUMBER_PRESERVING_HASH_CONVERSION_CONTRACT",
           "authenticate_texture_frontend", "apply_texture_frontend")
