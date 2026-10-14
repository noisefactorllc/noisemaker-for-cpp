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
    material_layer_conversions: tuple[TypedExpression, ...]
    signed_gradient_shift: tuple[TypedExpression, ...]
    vector_scalar_conversions: tuple[TypedExpression, ...]
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
    if tuple((d.name, d.kind, d.canonical_value)
             for d in program.preprocessor_defines) == _DYNAMIC_DEFINES:
        return _authenticate_dynamic_texture(program, source_hash)
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
                         inverse_sqrt_nodes[0], hash_conversions[0], (), (), (), consumed)


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


# Runtime MODE is a separate exact-source/tree admission. MODE=3 retains its
# original frozen proof and all of its old rejection checks.
_DYNAMIC_DEFINES = (('MODE', 'str', 'int'),)
_DYNAMIC_IDENTITY = (12758,
 '8f0106bd69d6d872c464af065fa201f1fc5d963dadfa8f0cce651002b538249d',
 'b9ea50c50b8f9ac835d33c924102d85fb6d4aed233eca0607dfa207ca737b77e',
 '5087c67362be8b6bacbbcba08f80ae6d515f102bb7031ef444366aa53db7d068',
 '656c5a7adc7be649df963df7d9cee6afd014c37944051bd0262ceda664108670',
 ((1, 'MODE', 'int', 'uniform', False, '1:1-1:18'),
  (2, 'inputTex', 'sampler2D', 'uniform', False, '17:1-17:28'),
  (3, 'time', 'float', 'uniform', False, '18:1-18:20'),
  (4, 'alpha', 'float', 'uniform', False, '19:1-19:21'),
  (5, 'scale', 'float', 'uniform', False, '20:1-20:21'),
  (6, 'intensity', 'float', 'uniform', False, '21:1-21:25'),
  (7, 'contrast', 'float', 'uniform', False, '22:1-22:24'),
  (8, 'mono', 'bool', 'uniform', False, '23:1-23:19'),
  (9, 'tileOffset', 'vec2', 'uniform', False, '24:1-24:25'),
  (10, 'fullResolution', 'vec2', 'uniform', False, '25:1-25:29'),
  (11, 'fragColor', 'vec4', 'output', True, '27:1-27:16'),
  (12, 'PI', 'float', 'const', False, '29:1-29:32'),
  (13, 'INV_UINT32_MAX', 'float', 'const', False, '30:1-30:49'),
  (14, 'Z_LOOP', 'int', 'const', False, '31:1-31:22'),
  (15, 'SHADE_GAIN', 'float', 'const', False, '32:1-32:30')),
 ((78, 'clamp01', 'float', ((16, 'value', 'float', 'parameter', True, 'in'),), '34:1-36:2'),
  (79, 'fade', 'float', ((18, 't', 'float', 'parameter', True, 'in'),), '43:1-45:2'),
  (80,
   'fast_hash',
   'float',
   ((22, 'p', 'ivec3', 'parameter', True, 'in'), (23, 'salt', 'uint', 'parameter', True, 'in')),
   '68:1-77:2'),
  (81,
   'freq_for_shape',
   'vec2',
   ((19, 'base_freq', 'float', 'parameter', True, 'in'), (20, 'dims', 'vec2', 'parameter', True, 'in')),
   '47:1-57:2'),
  (82, 'hash_uint', 'uint', ((21, 'x', 'uint', 'parameter', True, 'in'),), '59:1-66:2'),
  (83,
   'height_canvas',
   'float',
   ((34, 'uv', 'vec2', 'parameter', True, 'in'),
    (35, 'base_freq', 'vec2', 'parameter', True, 'in'),
    (36, 'motion', 'float', 'parameter', True, 'in')),
   '154:1-163:2'),
  (84,
   'height_crosshatch',
   'float',
   ((39, 'uv', 'vec2', 'parameter', True, 'in'), (40, 'base_freq', 'vec2', 'parameter', True, 'in')),
   '174:1-179:2'),
  (85,
   'height_field',
   'float',
   ((41, 'uv', 'vec2', 'parameter', True, 'in'),
    (42, 'base_freq', 'vec2', 'parameter', True, 'in'),
    (43, 'motion', 'float', 'parameter', True, 'in')),
   '183:1-195:2'),
  (86,
   'height_halftone',
   'float',
   ((37, 'uv', 'vec2', 'parameter', True, 'in'), (38, 'base_freq', 'vec2', 'parameter', True, 'in')),
   '166:1-171:2'),
  (87,
   'height_paper',
   'float',
   ((28, 'uv', 'vec2', 'parameter', True, 'in'),
    (29, 'base_freq', 'vec2', 'parameter', True, 'in'),
    (30, 'motion', 'float', 'parameter', True, 'in')),
   '115:1-132:2'),
  (88,
   'height_stucco',
   'float',
   ((31, 'uv', 'vec2', 'parameter', True, 'in'),
    (32, 'base_freq', 'vec2', 'parameter', True, 'in'),
    (33, 'motion', 'float', 'parameter', True, 'in')),
   '135:1-151:2'),
  (89, 'main', 'void', (), '322:1-384:2'),
  (90,
   'material_directional',
   'float',
   ((62, 'globalPixel', 'vec2', 'parameter', True, 'in'),
    (63, 'motion', 'float', 'parameter', True, 'in'),
    (64, 'salt', 'uint', 'parameter', True, 'in'),
    (65, 'size', 'float', 'parameter', True, 'in')),
   '248:1-257:2'),
  (91,
   'material_edge_mask',
   'float',
   ((70, 'uv', 'vec2', 'parameter', True, 'in'), (71, 'pixelStep', 'vec2', 'parameter', True, 'in')),
   '276:1-282:2'),
  (92, 'material_fade', 'vec2', ((50, 't', 'vec2', 'parameter', True, 'in'),), '211:1-213:2'),
  (93,
   'material_gradient',
   'vec2',
   ((47, 'p', 'ivec2', 'parameter', True, 'in'),
    (48, 'salt', 'uint', 'parameter', True, 'in'),
    (49, 'layer', 'uint', 'parameter', True, 'in')),
   '205:1-209:2'),
  (94,
   'material_gradient_layer',
   'float',
   ((51, 'p', 'vec2', 'parameter', True, 'in'),
    (52, 'salt', 'uint', 'parameter', True, 'in'),
    (53, 'layer', 'uint', 'parameter', True, 'in')),
   '215:1-224:2'),
  (95,
   'material_hash',
   'uint',
   ((44, 'p', 'ivec2', 'parameter', True, 'in'),
    (45, 'salt', 'uint', 'parameter', True, 'in'),
    (46, 'layer', 'uint', 'parameter', True, 'in')),
   '197:1-203:2'),
  (96,
   'material_noise',
   'float',
   ((54, 'globalPixel', 'vec2', 'parameter', True, 'in'),
    (55, 'cellSize', 'vec2', 'parameter', True, 'in'),
    (56, 'motion', 'float', 'parameter', True, 'in'),
    (57, 'salt', 'uint', 'parameter', True, 'in')),
   '226:1-235:2'),
  (97,
   'material_soft',
   'float',
   ((58, 'globalPixel', 'vec2', 'parameter', True, 'in'),
    (59, 'motion', 'float', 'parameter', True, 'in'),
    (60, 'salt', 'uint', 'parameter', True, 'in'),
    (61, 'size', 'float', 'parameter', True, 'in')),
   '237:1-246:2'),
  (98,
   'material_sprinkles',
   'float',
   ((66, 'globalPixel', 'vec2', 'parameter', True, 'in'),
    (67, 'motion', 'float', 'parameter', True, 'in'),
    (68, 'salt', 'uint', 'parameter', True, 'in'),
    (69, 'size', 'float', 'parameter', True, 'in')),
   '259:1-274:2'),
  (99,
   'material_value',
   'float',
   ((72, 'globalPixel', 'vec2', 'parameter', True, 'in'),
    (73, 'dims', 'vec2', 'parameter', True, 'in'),
    (74, 'uv', 'vec2', 'parameter', True, 'in'),
    (75, 'motion', 'float', 'parameter', True, 'in'),
    (76, 'salt', 'uint', 'parameter', True, 'in')),
   '284:1-312:2'),
  (100, 's_curve01', 'float', ((17, 'value', 'float', 'parameter', True, 'in'),), '38:1-41:2'),
  (101, 'shape_material', 'float', ((77, 'raw', 'float', 'parameter', True, 'in'),), '314:1-320:2'),
  (102,
   'value_noise',
   'float',
   ((24, 'uv', 'vec2', 'parameter', True, 'in'),
    (25, 'freq', 'vec2', 'parameter', True, 'in'),
    (26, 'motion', 'float', 'parameter', True, 'in'),
    (27, 'salt', 'uint', 'parameter', True, 'in')),
   '79:1-112:2')),
 (('MODE',
   'inputTex',
   'time',
   'alpha',
   'scale',
   'intensity',
   'contrast',
   'mono',
   'tileOffset',
   'fullResolution'),
  ('inputTex',),
  ('fragColor',),
  True,
  False),
 (('MODE', 'str', 'int'),),
 (104, 'v_texCoord', 'vec2', 'varying', False, '1:1-385:1'),
 (('assign', 32),
  ('binary', 223),
  ('builtin', 86),
  ('call', 78),
  ('conditional', 3),
  ('construct', 82),
  ('declaration', 128),
  ('id', 501),
  ('literal', 247),
  ('post', 4),
  ('swizzle', 57),
  ('unary', 3)),
 (('!', 1),
  ('%', 4),
  ('&', 1),
  ('*', 88),
  ('*=', 6),
  ('+', 52),
  ('++', 4),
  ('+=', 4),
  ('-', 30),
  ('/', 12),
  ('<', 4),
  ('<=', 3),
  ('=', 14),
  ('==', 15),
  ('>', 4),
  ('>=', 1),
  ('>>', 4),
  ('^', 7),
  ('^=', 8)))
_DYNAMIC_SITES = ((('323:23-323:52', 'bdcbca9ee3f5b1bb2dbb7585491f5b3d36f88afb7e47ed6f37142760c59962f0', 'vec4', 'inputTex'),
  ('277:19-277:65', 'd6cdb5be239fa67d86af95fb85a9706f598e482c72335f488b19cadc9564c6ec', 'vec4', 'inputTex'),
  ('278:19-278:65', 'eaf1cea7abd0b163c9d930156f48c7e676800b3b0efd3ecdc02c835558202964', 'vec4', 'inputTex'),
  ('279:19-279:65', 'c88a28c9391416046e5da6eac8dc8e55ab42f953a3741adce924112d5b507475', 'vec4', 'inputTex'),
  ('280:19-280:65', '02106657ed9c7e0d9394f899739de2447c775a87a082ec350f2f0574fc80d67d', 'vec4', 'inputTex')),
 (('324:22-324:46',
   '41ff7c157e2d5649846ede6095fa351ab0eb3ac1b7aeedf6619eebf802cbbc9c',
   'ivec2',
   'inputTex',
   0),),
 (('^', 'uint', '69:14-69:32', 'ef18770a28c84d905cfe9223359575b490d27e6948a38e87d4da4def63ee88b0'),
  ('>>', 'uint', '60:10-60:18', '70a89d589dc96d7bd74bdf48295a8c10e291f75f51d8734226fe05b87b44054d'),
  ('>>', 'uint', '62:10-62:18', 'fc4bb3f3b10596ba99c2675e824a7b33177ca67a5bd2b227a3146009fadd5ca2'),
  ('>>', 'uint', '64:10-64:18', '6d666eaab93022d461cf6161996bc5b46038a233606a9014ab3b26262b612086'),
  ('^', 'uint', '255:24-255:42', 'bd13e62c6f4e424c814855fbcefd28d44d97b22d839c8ce0161a3eae242c0711'),
  ('&', 'uint', '207:32-207:43', '867e973f3930b590c04daa1231f1f625542559d99a37099a0a31bc2eccdf9c34'),
  ('>>', 'uint', '207:52-207:60', '9e7f9fd5afa1f683923ff6d5b75d2f4b6f880683fca8f34923f7378ed2050a0e'),
  ('^', 'uint', '198:14-198:42', '4dec4458825c1066b905ef548b4cccccc949e9195fe53e283ee630d311ae1851'),
  ('^', 'uint', '244:24-244:42', '8420d846c0427aa3906aee86888cc7d39fb0be9753a1a76192409a5870d8c7db'),
  ('^', 'uint', '268:50-268:68', 'b747fffbd97c0c88c5daee466958b82ef916335659c629d5da897e677062ce69'),
  ('^', 'uint', '292:76-292:94', '09774c1bf4c0540b7887dbfe7300d8eeddfa16142674edb5e28945afee7f9514'),
  ('^', 'uint', '293:76-293:94', '0a1de70a47557f5260131003eb2a7e353e24278c4929917cd6431fc5a5e9f95a')),
 (('^=',
   'uint',
   '70:5-70:33',
   'adad6b6c447991ae67c5fb403381778b521d69829cbf99ecc688677d62d8a597',
   ('uint', 'uint')),
  ('^=',
   'uint',
   '72:5-72:33',
   '6beb04ce533f68bf5a5a654ba2ea1f10d6a6c421906e9685a700d0280d66c2fd',
   ('uint', 'uint')),
  ('^=',
   'uint',
   '74:5-74:33',
   '90b4b88407906578950b4a2b0ef8cda46bef82a83aedf377bbbf8028109133ca',
   ('uint', 'uint')),
  ('^=',
   'uint',
   '60:5-60:18',
   'e5ad8dc8e1604071fc9746d9512519ab7bf3c36db241fe9795efb878e269d326',
   ('uint', 'uint')),
  ('^=',
   'uint',
   '62:5-62:18',
   '73fc12d6b51867a2a5d285bdb50331e6d02234ca616498dea0d0664ecc7511a4',
   ('uint', 'uint')),
  ('^=',
   'uint',
   '64:5-64:18',
   '080004a74975bf2071118d746b678b07240a9213cf580053e135d12ffe21a915',
   ('uint', 'uint')),
  ('^=',
   'uint',
   '199:5-199:33',
   '78e4f0925948e9cd4fb24be5ca25063deb00e212acf231922510b46b39d9cd14',
   ('uint', 'uint')),
  ('^=',
   'uint',
   '201:5-201:33',
   '9dca54193ac545d1486f106d9140c0b7bfcef57541e83a7a5950341d3736bd57',
   ('uint', 'uint'))),
 (('float',
   '208:23-208:74',
   'c35a647ac750543b97b372b5d87faf6462fb4ec47370e66933645f1a4c548f7d',
   ('float',)),),
 (('float', '76:12-76:20', '56728366c71e82aa47c836c718ad4341aec1691d6a4dddd96974c2843bea3608', ('uint',)),))
_DYNAMIC_RECORD_SHA256 = 'ddd14b4a74f292eb9739c59cc65c85e09360732167c37441185ef42247fdf997'
_DYNAMIC_SIGNED_GRADIENT_SHIFT = ('207:52-207:60', '9e7f9fd5afa1f683923ff6d5b75d2f4b6f880683fca8f34923f7378ed2050a0e')
_DYNAMIC_VECTOR_SCALAR_CONVERSIONS = (
    ('267:34-267:48', 'f9482982fd28eef2f4f73b660cfb7540b68ac70ecdee167efd334115aabbd909', 0),
    ('268:34-268:48', '75b857e44eeaf137c9ffa7c13f6f497f47414eb7f43c3ae8156e8b154a14eb50', 1),
)
_DYNAMIC_MATERIAL_LAYER_CONVERSIONS = (
    ('231:49-231:57', '1c2f8353d23468d0a3427184ef9b37055d34cc664f4cf27afecd7d2bd2970d5e', 'z0'),
    ('232:49-232:57', '8f03a3cb6ae07b63d33af7771c9eafabd4c131314e239e9a948dab135d0d77ad', 'z1'),
)


def _authenticate_dynamic_texture(program: TypedProgram, source_hash: str | None) -> FrontendProof:
    if (_sha((_DYNAMIC_IDENTITY, _DYNAMIC_SITES)) != _DYNAMIC_RECORD_SHA256
            or source_hash != RAW_SHA256 or len(program.raw_source.encode('utf-8')) != RAW_BYTES
            or hashlib.sha256(program.raw_source.encode('utf-8')).hexdigest() != RAW_SHA256
            or program.body_status != 'analyzed' or program.structs or program.uniform_blocks):
        raise _fail('runtime MODE record, raw source, or structural identity mismatch')
    expr = _expressions(program)
    if len(program.interface_symbols) != 1:
        raise _fail('runtime varying census mismatch')
    varying = program.interface_symbols[0]
    identity = (len(program.source.encode('utf-8')),
                hashlib.sha256(program.source.encode('utf-8')).hexdigest(),
                _sha(program.functions), _whole(program), _interface(program),
                tuple((d.symbol.id,d.symbol.name,d.type.display(),d.symbol.storage,
                       d.symbol.writable,_span(d)) for d in program.declarations),
                tuple((f.signature.id,f.name,f.return_type.display(),
                       tuple((q.id,q.name,q.type.display(),q.storage,q.writable,q.direction)
                             for q in f.parameters),_span(f)) for f in program.functions),
                (program.resources.uniforms,program.resources.samplers,program.resources.outputs,
                 program.resources.uses_texture,program.resources.uses_derivatives),
                tuple((d.name,d.kind,d.canonical_value) for d in program.preprocessor_defines),
                (varying.id,varying.name,varying.type.display(),varying.storage,
                 varying.writable,_span(varying)),
                tuple(sorted(Counter(x.kind for x in expr).items())),
                tuple(sorted(Counter(x.operator for x in expr if x.operator is not None).items())))
    if identity != _DYNAMIC_IDENTITY:
        raise _fail('runtime normalized source, function, whole tree, interface, or census mismatch')
    texture=tuple(x for x in expr if x.kind=='builtin' and x.callee=='texture')
    size=tuple(x for x in expr if x.kind=='builtin' and x.callee=='textureSize')
    bit=tuple(x for x in expr if x.kind=='binary' and x.operator in BITWISE_REQUIREMENT[1])
    assign=tuple(x for x in expr if x.kind=='assign' and x.operator=='^=')
    inv=tuple(x for x in expr if x.kind=='builtin' and x.callee=='inversesqrt')
    fast=next((x for x in program.functions if x.name=='fast_hash'),None)
    if fast is None:
        raise _fail('runtime hash function absent')
    conversions=tuple(x for st in fast.body for x in _walk_statement(st)
                      if x.kind=='construct' and x.type.display()=='float'
                      and len(x.children)==1 and x.children[0].type.display()=='uint')
    noise=next((x for x in program.functions if x.name=='material_noise'),None)
    if noise is None:
        raise _fail('runtime material noise function absent')
    layers=tuple(x for st in noise.body for x in _walk_statement(st)
                 if x.kind=='construct' and x.type.display()=='uint')
    if (tuple((_span(x),_sha(x),x.children[0].symbol.name if len(x.children)==1
               and x.children[0].symbol is not None else None) for x in layers)
            != _DYNAMIC_MATERIAL_LAYER_CONVERSIONS
            or any(len(x.children)!=1 or x.children[0].type.display()!='int'
                   for x in layers)):
        raise _fail('runtime material noise layer conversion mismatch')
    sites=(tuple((_span(x),_sha(x),x.type.display(),
                  x.children[0].symbol.name if x.children else None) for x in texture),
           tuple((_span(x),_sha(x),x.type.display(),
                  x.children[0].symbol.name if x.children else None,
                  x.children[1].literal_value if len(x.children)>1 else None) for x in size),
           tuple((x.operator,x.type.display(),_span(x),_sha(x)) for x in bit),
           tuple((x.operator,x.type.display(),_span(x),_sha(x),
                  tuple(c.type.display() for c in x.children)) for x in assign),
           tuple((x.type.display(),_span(x),_sha(x),
                  tuple(c.type.display() for c in x.children)) for x in inv),
           tuple((x.type.display(),_span(x),_sha(x),
                  tuple(c.type.display() for c in x.children)) for x in conversions))
    if (sites != _DYNAMIC_SITES or len(texture)!=5 or len(size)!=1 or len(inv)!=1
            or len(conversions)!=1 or len(bit)!=12 or len(assign)!=8):
        raise _fail('runtime sampler, bitwise, inverse sqrt, or hash conversion mismatch')
    if (any(x.children[0].symbol.name!='inputTex' for x in (*texture,*size))
            or size[0].children[1].literal_value!=0
            or any(x.children[0].type.display()!='uint' or
                   x.children[1].type.display()!='uint' for x in assign)):
        raise _fail('runtime sampler or uint operand route mismatch')
    gradient=next((f for f in program.functions if f.name=='material_gradient'),None)
    sprinkles=next((f for f in program.functions if f.name=='material_sprinkles'),None)
    if gradient is None or sprinkles is None:
        raise _fail('runtime Texture material functions absent')
    shifts=tuple(x for st in gradient.body for x in _walk_statement(st)
                 if x.kind=='binary' and x.operator=='>>')
    if (len(shifts)!=1 or (_span(shifts[0]),_sha(shifts[0]))
            != _DYNAMIC_SIGNED_GRADIENT_SHIFT
            or shifts[0].type.display()!='uint'
            or len(shifts[0].children)!=2
            or shifts[0].children[0].symbol is None
            or shifts[0].children[0].symbol.name!='h'
            or shifts[0].children[1].literal_value!=16):
        raise _fail('runtime Texture signed gradient shift mismatch')
    vectors=tuple(x for st in sprinkles.body for x in _walk_statement(st)
                  if x.kind=='construct' and x.type.display()=='ivec3')
    if (tuple((_span(x),_sha(x),x.children[1].literal_value
               if len(x.children)==2 else None) for x in vectors)
            != _DYNAMIC_VECTOR_SCALAR_CONVERSIONS
            or any(x.children[0].symbol is None
                   or x.children[0].symbol.name!='cell'
                   or x.children[0].type.display()!='ivec2'
                   or x.children[1].type.display()!='int' for x in vectors)):
        raise _fail('runtime Texture vector-scalar constructor mismatch')
    if not any(shifts[0] is node for node in bit):
        raise _fail('runtime signed shift is absent from bitwise ledger')
    consumed=(varying,*texture,*size,*bit,*assign,inv[0],conversions[0],
              *layers,*vectors)
    if len({id(x) for x in consumed})!=len(consumed):
        raise _fail('runtime candidate object identity collision')
    return FrontendProof(KEY,(varying.name,varying.type.display(),varying.id,_span(varying)),
                         ('texture','textureSize'),bit,assign,inv[0],conversions[0],layers,shifts,vectors,consumed)
