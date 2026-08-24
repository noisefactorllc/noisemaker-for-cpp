"""Exact ownership and ABI proofs for the pinned nine-tap array programs.

Dict-keyed per program: `classicNoisedeck/refract:refract` (the historical
refract record, byte-identical in behavior),
`classicNoisedeck/cellRefract:cellRefract` (`cellrefract-convolve-v1`) and
`classicNoisedeck/kaleido:kaleido` (`kaleido-convolve-v1`).  All three
records share the `FixedArrayInParameterProof` shape the emitter and the
validator consume flat; every per-key value (hashes, censuses, symbol ids,
flags) is frozen per profile and re-derived, never transcribed.
"""

from __future__ import annotations

import dataclasses
import hashlib

from .span import SourceSpan, span_at
from .typed_ir import (
    FixedArrayInParameterProof,
    FixedArrayOwnedTableProof,
    FixedArrayParameterProof,
    PreprocessorDefine,
    RefractCompatibilitySiteProof,
    TypedExpression,
    TypedFunction,
    TypedProgram,
    TypedStatement,
)


CAPABILITY = "fixed-array-in-parameter-v1"
REFRACT_KEY = "classicNoisedeck/refract:refract"
SOURCE_PROFILE = "refract-fixed-array-in-parameter-v1"
RAW_SOURCE_SHA256 = "d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2"
NORMALIZED_SOURCE_SHA256 = "bff1818ad5db7e637a01d6f10476cebba8ac04d6ffdf467d02508fa23671757e"
CANONICAL_FACTORY_SHA256 = "b404a801dea1ba438da7bad20d7cae059d0aa7f25c76610221ca07546fdfe2f6"
INTERFACE_SHA256 = "36d7815ce5aa9efedf3144e199ae7b49dc5819c751475b815708424269033229"
TYPED_IR_SHA256 = "4c9e125cd4dda55f2688c362a5ab7e81acf1b08c9e284bc5c25e04da39020188"
WHOLE_PROGRAM_SHA256 = "93329ab73d54ff1eb3b8ec43da8570365d58de8caaa1a36252ef1ad30a709de2"

CELLREFRACT_KEY = "classicNoisedeck/cellRefract:cellRefract"
CELLREFRACT_SOURCE_PROFILE = "cellrefract-convolve-v1"
CELLREFRACT_RAW_SOURCE_SHA256 = "aa93167faa07ee22ff0be9c653b5602ac88b1b962e405548cafab43b9e867a70"
CELLREFRACT_NORMALIZED_SOURCE_SHA256 = "31cce61e01275d44d46556bfc13edeea4383dcfbcfde024fd7c54a624933bd3c"
CELLREFRACT_CANONICAL_FACTORY_SHA256 = "329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3"
CELLREFRACT_INTERFACE_SHA256 = "09c626e4a6923f856dac399e76972de809ccc8efeb3d49c59d5f69eb8ed17352"
CELLREFRACT_TYPED_IR_SHA256 = "e7e3fd532c4fcc8116655ca64d2b73e6c0905d221cc485014315d29b22b27a6b"
CELLREFRACT_WHOLE_PROGRAM_SHA256 = "144e3e4c035bf5af4102d3bfed99afabe2f403b8a6c2c2794802adb0ca51d40b"

KALEIDO_KEY = "classicNoisedeck/kaleido:kaleido"
KALEIDO_SOURCE_PROFILE = "kaleido-convolve-v1"
KALEIDO_RAW_SOURCE_SHA256 = "3a155a9bf64f9e700dd66a77c4195df113d9e85228bde56b1cf410944aaeb8b9"
KALEIDO_NORMALIZED_SOURCE_SHA256 = "d31299ee69dd0c41965209860ef60a4ad2abf762229cc340383dce2646c6cc1d"
KALEIDO_CANONICAL_FACTORY_SHA256 = "4ab626fda5e91e7f89b93c9d863cda497b85d79239183499785c03607cce19a3"
KALEIDO_INTERFACE_SHA256 = "666586f65044abc1a147a7c3007f376fde3833c275f5f25bce9b6027b7eaa717"
KALEIDO_TYPED_IR_SHA256 = "2ffb48e5f118844d675f9741ccbf7e831ce2f7cfe4609b24777ddb5fb67887ff"
KALEIDO_WHOLE_PROGRAM_SHA256 = "2590b36ad768dd1217743dac63486619562f0d3f2c90d9aa4cb06c0b2ca68e68"

EFFECTS_KEY = "classicNoisedeck/effects:effects"
EFFECTS_SOURCE_PROFILE = "effects-convolve-v1"
EFFECTS_RAW_SOURCE_SHA256 = "e3b742be53b6b1b0dd5e089a805ff02a931cd14643d0a0abe376bd8044e8ec6c"
EFFECTS_NORMALIZED_SOURCE_SHA256 = "cce2f30177586f4cdabab1e1741a99d1470f49db79c60dc20df9ddbcac9bdfda"
EFFECTS_CANONICAL_FACTORY_SHA256 = "ebf43ff45f4a3568854da02b41baf6b1a25efd2bc5bbf2d8cf78f0a11e3dd81a"
EFFECTS_INTERFACE_SHA256 = "feeb85a578bad5296e9c345401f7f1a6055da9aa6f5f476c346137f53cdeef52"
EFFECTS_TYPED_IR_SHA256 = "d06fd4218bd7513a5aecd343bc3bb9d83dfb6b8fba011626fd5bb80707d67579"
EFFECTS_WHOLE_PROGRAM_SHA256 = "b5176c5224f3c44442f2bb28f5e3917b937123430888aa649a8d86301b92d581"

_BINDINGS = (
    "inputTex:sampler2D", "resolution:vec2", "tileOffset:vec2",
    "fullResolution:vec2", "time:float", "mode:int", "amount:float",
    "direction:float", "blendMode:int", "mixAmt:float", "wrap:int",
)
_CALLER_PROFILES = (
    (39, "derivX", 57, "deriv_x",
     (0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0)),
    (40, "derivY", 60, "deriv_y",
     (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0)),
)
_COMPATIBILITY = {
    # mode: source id, equality constant, false builtin, predicate offsets,
    # false-arm offsets
    2: (34, 0.0, "max", (3004, 3023), (3036, 3086)),
    3: (34, 1.0, "min", (3148, 3167), (3180, 3219)),
    7: (34, 1.0, "min", (3542, 3561), (3574, 3622)),
    15: (33, 1.0, "min", (4544, 4563), (4576, 4624)),
}

_CELLREFRACT_DEFINES = (
    PreprocessorDefine("KERNEL", "int", "0"),
    PreprocessorDefine("SHAPE", "int", "1"),
)
_CELLREFRACT_BINDINGS = (
    "inputTex:sampler2D", "time:float", "seed:int", "resolution:vec2",
    "tileOffset:vec2", "fullResolution:vec2", "scale:float",
    "cellScale:float", "cellSmooth:float", "variation:float", "speed:float",
    "refractAmt:float", "direction:float", "wrap:int", "effectWidth:float",
)
# The five mutable global float[9] tables (17-21, Worker A's profile), the
# convolve parameter (23), convolve's vec2 offset table (101) and the eight
# caller tables -- the whole-program array census covers every one of them.
_CELLREFRACT_ARRAY_IDS = frozenset(
    {17, 18, 19, 20, 21, 23, 101, 107, 108, 131, 132, 152, 153, 162, 163})
_CELLREFRACT_CENSUS = (1, 9, 146, 137, 126, 3, 129, 8, 8)
# Unreachability frozen as a fact (the proof vouches grammar, not liveness):
# at KERNEL=0 the reachable set from main is exactly these seven functions.
_CELLREFRACT_REACHABLE = ("cells", "loadKernels", "main", "map", "pcg", "prng",
                          "smin")
_CELLREFRACT_PARAMETERS = (
    (22, "localUV", "vec2", "in"),
    (23, "kernel", "float[9]", "in"),
    (24, "divide", "bool", "in"),
)
_CELLREFRACT_LOOP_PROOF = (
    104, 0, 9, "<", "++", "literal", 9, 1, 1, 9, 30,
)
_SOBEL_X = (1.0, 0.0, -1.0, 2.0, 0.0, -2.0, 1.0, 0.0, -1.0)
_SOBEL_Y = (1.0, 2.0, 1.0, 0.0, 0.0, 0.0, -1.0, -2.0, -1.0)
# owner id, owner name, owner body count, symbol id, name, call statement
# index, literal values; ordered exactly as the whole-array call arguments.
_CELLREFRACT_CALLER_TABLES = (
    (67, "derivatives", 25, 107, "deriv_x", 21,
     (0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0)),
    (67, "derivatives", 25, 108, "deriv_y", 22,
     (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0)),
    (84, "sobel", 25, 162, "sobel_x", 21, _SOBEL_X),
    (84, "sobel", 25, 163, "sobel_y", 22, _SOBEL_Y),
    (81, "shadow", 29, 152, "sobel_x", 21, _SOBEL_X),
    (81, "shadow", 29, 153, "sobel_y", 22, _SOBEL_Y),
    (73, "outline", 26, 131, "sobel_x", 21, _SOBEL_X),
    (73, "outline", 26, 132, "sobel_y", 22, _SOBEL_Y),
)
_CELLREFRACT_OFFSET_COMPONENTS = (
    ("-x", "-y"), ("0", "-y"), ("x", "-y"),
    ("-x", "0"), ("0", "0"), ("x", "0"),
    ("-x", "y"), ("0", "y"), ("x", "y"),
)

_KALEIDO_DEFINES = (
    PreprocessorDefine("DIRECTION", "int", "2"),
    PreprocessorDefine("KERNEL", "int", "0"),
    PreprocessorDefine("LOOP_OFFSET", "int", "10"),
    PreprocessorDefine("METRIC", "int", "0"),
)
_KALEIDO_BINDINGS = (
    "inputTex:sampler2D", "resolution:vec2", "tileOffset:vec2",
    "fullResolution:vec2", "time:float", "wrap:bool", "seed:int",
    "speed:float", "loopScale:float", "kaleido:float", "effectWidth:float",
)
# The five mutable global float[9] tables (13-17, the array module's record),
# the convolve parameter (82), convolve's vec2 offset table (243) and the
# eight caller tables -- the whole-program array census covers every one of
# them.  kaleido's nine-number census is byte-identical to cellRefract's.
_KALEIDO_ARRAY_IDS = frozenset(
    {13, 14, 15, 16, 17, 82, 243, 249, 250, 274, 275, 332, 333, 362, 363})
_KALEIDO_CENSUS = (1, 9, 146, 137, 126, 3, 129, 8, 8)
# Unreachability frozen as a fact (the proof vouches grammar, not liveness):
# at KERNEL=0 the structural reachable set from main is these 30 functions
# (kaleido-design §1 -- the LOOP_OFFSET constant guards keep the never-taken
# interpolation arms structurally reachable, so the set is larger than
# cellRefract's seven).
_KALEIDO_REACHABLE = (
    "bicubicValue", "blendBicubic", "blendLinearOrCosine", "catmullRom3",
    "catmullRom3x3Value", "catmullRom4", "catmullRom4x4Value", "circles",
    "constant", "diamonds", "getMetric", "kaleidoscope", "loadKernels",
    "main", "map", "mod289_2", "mod289_3", "offset", "pcg",
    "periodicFunction", "permute3", "positiveModulo", "quadratic3",
    "quadratic3x3Value", "randomFromLatticeWithOffset", "rings", "shape",
    "simplexValue", "sineNoise", "value",
)
_KALEIDO_PARAMETERS = (
    (81, "uv", "vec2", "in"),
    (82, "kernel", "float[9]", "in"),
    (83, "divide", "bool", "in"),
)
_KALEIDO_LOOP_PROOF = (
    246, 0, 9, "<", "++", "literal", 9, 1, 1, 9, 0,
)
# convolve's `vec2 offset[9]` table: symbol 243, declared at body[1], nine
# component stores at body[2..10], its `step` base is symbol 242, one
# induction-indexed read (induction 246) inside the loop at body[13].
_KALEIDO_OFFSET_SYMBOL_ID = 243
_KALEIDO_OFFSET_STEPS_ID = 242
# The 8 caller tables; owner id, owner name, owner body count, symbol id,
# name, call statement index, literal values -- the same shape and the same
# numeric payloads as cellRefract's family.  `shadow`'s tables sit at
# statements 0 and 10, not 1 and 11 like the other three (and like all four
# of cellRefract's) -- the declaration-searching table helper handles this;
# a frozen-index helper would not (kaleido-design §1).
_KALEIDO_CALLER_TABLES = (
    (120, "derivatives", 25, 249, "deriv_x", 21,
     (0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0)),
    (120, "derivatives", 25, 250, "deriv_y", 22,
     (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0)),
    (150, "sobel", 25, 362, "sobel_x", 21, _SOBEL_X),
    (150, "sobel", 25, 363, "sobel_y", 22, _SOBEL_Y),
    (132, "outline", 26, 274, "sobel_x", 21, _SOBEL_X),
    (132, "outline", 26, 275, "sobel_y", 22, _SOBEL_Y),
    (146, "shadow", 29, 332, "sobel_x", 21, _SOBEL_X),
    (146, "shadow", 29, 333, "sobel_y", 22, _SOBEL_Y),
)

_EFFECTS_DEFINES = (
    PreprocessorDefine("EFFECT", "int", "0"),
    PreprocessorDefine("FLIP", "int", "0"),
)
_EFFECTS_BINDINGS = (
    "inputTex:sampler2D", "resolution:vec2", "tileOffset:vec2",
    "fullResolution:vec2", "renderScale:float", "time:float",
    "effectAmt:float", "scaleAmt:float", "rotation:float", "offsetX:float",
    "offsetY:float", "intensity:float", "saturation:float",
)
# The SEVEN mutable global float[9] tables (15-21, the array module's
# effects record), the convolve parameter (42), convolve's vec2 offset table
# (151) and the eight caller tables -- the whole-program array census covers
# every one of them.  effects' census is the family's first SEVEN-array /
# 63-store shape: 144 literal stores (63 + 72 + 9) over 17 array ids, frozen
# per key and never shared with the two landed convolve keys.
_EFFECTS_ARRAY_IDS = frozenset(
    {15, 16, 17, 18, 19, 20, 21, 42, 151, 157, 158, 179, 180, 202, 203,
     210, 211})
_EFFECTS_CENSUS = (1, 9, 164, 155, 144, 3, 147, 8, 8)
# Unreachability frozen as a fact (the proof vouches grammar, not liveness):
# at EFFECT=0 the reachable set from main is exactly these eight functions
# (effects-design §1 -- the runtime-live pixel path).
_EFFECTS_REACHABLE = ("brightnessContrast", "loadKernels", "main", "map",
                      "offsets", "periodicFunction", "rotate2D", "saturate")
_EFFECTS_PARAMETERS = (
    (41, "uv", "vec2", "in"),
    (42, "kernel", "float[9]", "in"),
    (43, "divide", "bool", "in"),
)
_EFFECTS_LOOP_PROOF = (
    154, 0, 9, "<", "++", "literal", 9, 1, 1, 9, 0,
)
# convolve's `vec2 offset[9]` table: symbol 151, declared at body[1], nine
# component stores at body[2..10], its `step` base is symbol 150, one
# induction-indexed read (induction 154) inside the loop at body[13].
_EFFECTS_OFFSET_SYMBOL_ID = 151
_EFFECTS_OFFSET_STEPS_ID = 150
# The 8 caller tables; owner id, owner name, owner body count, symbol id,
# name, call statement index, literal values -- the same family payloads.
# `shadow`'s tables sit at statements 0 and 10, the kaleido quirk the
# declaration-searching helper absorbs (effects-design §1/§12).
_EFFECTS_CALLER_TABLES = (
    (71, "derivatives", 25, 157, "deriv_x", 21,
     (0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0)),
    (71, "derivatives", 25, 158, "deriv_y", 22,
     (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0)),
    (90, "sobel", 25, 210, "sobel_x", 21, _SOBEL_X),
    (90, "sobel", 25, 211, "sobel_y", 22, _SOBEL_Y),
    (79, "outline", 26, 179, "sobel_x", 21, _SOBEL_X),
    (79, "outline", 26, 180, "sobel_y", 22, _SOBEL_Y),
    (89, "shadow", 29, 202, "sobel_x", 21, _SOBEL_X),
    (89, "shadow", 29, 203, "sobel_y", 22, _SOBEL_Y),
)


@dataclasses.dataclass(frozen=True)
class _Profile:
    """Per-key frozen identity and whole-program census expectations."""

    source_profile: str
    raw_source_sha256: str
    normalized_source_sha256: str
    canonical_factory_sha256: str
    interface_sha256: str
    typed_ir_sha256: str
    whole_program_sha256: str
    preprocessor_defines: tuple[PreprocessorDefine, ...]
    binding_signature: tuple[str, ...]
    array_ids: frozenset[int]
    census: tuple[int, ...]


PROFILES: dict[str, _Profile] = {
    REFRACT_KEY: _Profile(
        source_profile=SOURCE_PROFILE,
        raw_source_sha256=RAW_SOURCE_SHA256,
        normalized_source_sha256=NORMALIZED_SOURCE_SHA256,
        canonical_factory_sha256=CANONICAL_FACTORY_SHA256,
        interface_sha256=INTERFACE_SHA256,
        typed_ir_sha256=TYPED_IR_SHA256,
        whole_program_sha256=WHOLE_PROGRAM_SHA256,
        preprocessor_defines=(),
        binding_signature=_BINDINGS,
        array_ids=frozenset({19, 51, 57, 60}),
        census=(1, 3, 35, 32, 27, 3, 30, 2, 2),
    ),
    CELLREFRACT_KEY: _Profile(
        source_profile=CELLREFRACT_SOURCE_PROFILE,
        raw_source_sha256=CELLREFRACT_RAW_SOURCE_SHA256,
        normalized_source_sha256=CELLREFRACT_NORMALIZED_SOURCE_SHA256,
        canonical_factory_sha256=CELLREFRACT_CANONICAL_FACTORY_SHA256,
        interface_sha256=CELLREFRACT_INTERFACE_SHA256,
        typed_ir_sha256=CELLREFRACT_TYPED_IR_SHA256,
        whole_program_sha256=CELLREFRACT_WHOLE_PROGRAM_SHA256,
        preprocessor_defines=_CELLREFRACT_DEFINES,
        binding_signature=_CELLREFRACT_BINDINGS,
        array_ids=_CELLREFRACT_ARRAY_IDS,
        census=_CELLREFRACT_CENSUS,
    ),
    KALEIDO_KEY: _Profile(
        source_profile=KALEIDO_SOURCE_PROFILE,
        raw_source_sha256=KALEIDO_RAW_SOURCE_SHA256,
        normalized_source_sha256=KALEIDO_NORMALIZED_SOURCE_SHA256,
        canonical_factory_sha256=KALEIDO_CANONICAL_FACTORY_SHA256,
        interface_sha256=KALEIDO_INTERFACE_SHA256,
        typed_ir_sha256=KALEIDO_TYPED_IR_SHA256,
        whole_program_sha256=KALEIDO_WHOLE_PROGRAM_SHA256,
        preprocessor_defines=_KALEIDO_DEFINES,
        binding_signature=_KALEIDO_BINDINGS,
        array_ids=_KALEIDO_ARRAY_IDS,
        census=_KALEIDO_CENSUS,
    ),
    EFFECTS_KEY: _Profile(
        source_profile=EFFECTS_SOURCE_PROFILE,
        raw_source_sha256=EFFECTS_RAW_SOURCE_SHA256,
        normalized_source_sha256=EFFECTS_NORMALIZED_SOURCE_SHA256,
        canonical_factory_sha256=EFFECTS_CANONICAL_FACTORY_SHA256,
        interface_sha256=EFFECTS_INTERFACE_SHA256,
        typed_ir_sha256=EFFECTS_TYPED_IR_SHA256,
        whole_program_sha256=EFFECTS_WHOLE_PROGRAM_SHA256,
        preprocessor_defines=_EFFECTS_DEFINES,
        binding_signature=_EFFECTS_BINDINGS,
        array_ids=_EFFECTS_ARRAY_IDS,
        census=_EFFECTS_CENSUS,
    ),
}
KEYS = tuple(PROFILES)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _whole_program_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
        program.fixed_nine_table_proof,
        program.fixed_grid_counter_store_proof,
    ))


def source_provenance_error(program: TypedProgram,
                            source_hash: str | None) -> str | None:
    profile = PROFILES.get(program.key)
    if profile is None:
        return None
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    if (program.preprocessor_defines != profile.preprocessor_defines
            or raw_hash != profile.raw_source_sha256
            or normalized_hash != profile.normalized_source_sha256
            or source_hash != profile.raw_source_sha256):
        return "source provenance mismatch for fixed-array input parameter"
    return None


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


def _all_expressions(program: TypedProgram) -> tuple[TypedExpression, ...]:
    values: list[TypedExpression] = []
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if isinstance(value, TypedExpression):
                    values.append(value)
    return tuple(values)


def _definition(program: TypedProgram, signature_id: int, name: str,
                body_count: int) -> TypedFunction | None:
    matches = [function for function in program.functions
               if function.signature.id == signature_id and function.name == name
               and function.body]
    if len(matches) != 1 or len(matches[0].body) != body_count:
        return None
    return matches[0]


def _declaration(statement: TypedStatement, symbol_id: int, name: str,
                 type_name: str) -> TypedExpression | None:
    if (statement.kind != "decl" or len(statement.expressions) != 1
            or statement.children):
        return None
    value = statement.expressions[0]
    if (value.kind != "declaration" or value.symbol is None
            or value.symbol_id != symbol_id or value.symbol.id != symbol_id
            or value.symbol.name != name or value.type.display() != type_name
            or value.symbol.type != value.type or value.symbol.storage != "local"
            or not value.symbol.writable):
        return None
    return value


def _literal_int(value: TypedExpression, expected: int) -> bool:
    return (value.kind == "literal" and value.type.display() == "int"
            and value.literal_value == expected and value.literal == str(expected))


def _number(value: TypedExpression) -> float | None:
    if (value.kind == "literal" and value.type.display() == "float"
            and isinstance(value.literal_value, float)):
        return value.literal_value
    if (value.kind == "unary" and value.operator == "-"
            and len(value.children) == 1):
        child = value.children[0]
        if (child.kind == "literal" and child.type.display() == "float"
                and isinstance(child.literal_value, float)):
            return -child.literal_value
    return None


def _literal_store(statement: TypedStatement, symbol_id: int,
                   index: int) -> tuple[TypedExpression, TypedExpression] | None:
    if (statement.kind != "expr" or len(statement.expressions) != 1
            or statement.children):
        return None
    assignment = statement.expressions[0]
    if (assignment.kind != "assign" or assignment.operator != "="
            or len(assignment.children) != 2):
        return None
    target, value = assignment.children
    if (target.kind != "index" or len(target.children) != 2
            or target.children[0].kind != "id"
            or target.children[0].symbol_id != symbol_id
            or not _literal_int(target.children[1], index)):
        return None
    return target, value


def _caller_table(function: TypedFunction, symbol_id: int, name: str,
                  expected_values: tuple[float, ...]) -> tuple[
                      FixedArrayOwnedTableProof, TypedExpression] | None:
    declaration = _declaration(function.body[1], symbol_id, name, "float[9]")
    if declaration is None or declaration.children:
        return None
    store_spans: list[SourceSpan] = []
    index_spans: list[SourceSpan] = []
    values: list[float] = []
    for index, statement in enumerate(function.body[2:11]):
        store = _literal_store(statement, symbol_id, index)
        if store is None:
            return None
        target, rhs = store
        number = _number(rhs)
        if number is None:
            return None
        store_spans.append(statement.span)
        index_spans.append(target.span)
        values.append(number)
    if tuple(values) != expected_values:
        return None
    call_declaration = _declaration(
        function.body[11], 58 if function.id == 39 else 61,
        "s1" if function.id == 39 else "s2", "vec3")
    if call_declaration is None or len(call_declaration.children) != 1:
        return None
    call = call_declaration.children[0]
    if (call.kind != "call" or call.signature_id != 38
            or call.callee != "convolve" or len(call.children) != 3
            or call.children[1].kind != "id"
            or call.children[1].symbol_id != symbol_id):
        return None
    return (FixedArrayOwnedTableProof(
        role=name, owner_signature_id=function.id, symbol_id=symbol_id,
        symbol_name=name, array_type="float[9]", element_type="float",
        extent=9, native_alias="Kernel9", declaration_statement_index=1,
        declaration_span=declaration.span,
        literal_store_statement_indices=tuple(range(2, 11)),
        literal_store_spans=tuple(store_spans),
        literal_index_spans=tuple(index_spans),
        literal_indices=tuple(range(9)), number_values=tuple(values),
        induction_read_spans=(),
    ), call)


def _offset_component(value: TypedExpression, steps_id: int) -> str | None:
    if (value.kind == "literal" and value.type.display() == "float"
            and value.literal_value == 0.0):
        return "0"
    sign = ""
    inner = value
    if value.kind == "unary" and value.operator == "-" and len(value.children) == 1:
        sign = "-"
        inner = value.children[0]
    if (inner.kind != "swizzle" or inner.member not in ("x", "y")
            or len(inner.children) != 1 or inner.children[0].kind != "id"
            or inner.children[0].symbol_id != steps_id):
        return None
    return sign + inner.member


def _offset_table(function: TypedFunction, induction_id: int) -> FixedArrayOwnedTableProof | None:
    declaration = _declaration(function.body[2], 51, "offset", "vec2[9]")
    if declaration is None or declaration.children:
        return None
    expected = (
        ("-x", "-y"), ("0", "-y"), ("x", "-y"),
        ("-x", "0"), ("0", "0"), ("x", "0"),
        ("-x", "y"), ("0", "y"), ("x", "y"),
    )
    store_spans: list[SourceSpan] = []
    index_spans: list[SourceSpan] = []
    for index, statement in enumerate(function.body[3:12]):
        store = _literal_store(statement, 51, index)
        if store is None:
            return None
        target, rhs = store
        if (rhs.kind != "construct" or rhs.type.display() != "vec2"
                or rhs.constructor_type is None
                or rhs.constructor_type.display() != "vec2"
                or len(rhs.children) != 2
                or tuple(_offset_component(item, 50) for item in rhs.children)
                != expected[index]):
            return None
        store_spans.append(statement.span)
        index_spans.append(target.span)
    reads = tuple(value.span for statement in function.body
                  for value in _walk_statement(statement)
                  if isinstance(value, TypedExpression)
                  and value.kind == "index" and len(value.children) == 2
                  and value.children[0].kind == "id"
                  and value.children[0].symbol_id == 51
                  and value.children[1].kind == "id"
                  and value.children[1].symbol_id == induction_id)
    if len(reads) != 1:
        return None
    return FixedArrayOwnedTableProof(
        role="offset", owner_signature_id=function.id, symbol_id=51,
        symbol_name="offset", array_type="vec2[9]", element_type="vec2",
        extent=9, native_alias="Offsets9", declaration_statement_index=2,
        declaration_span=declaration.span,
        literal_store_statement_indices=tuple(range(3, 12)),
        literal_store_spans=tuple(store_spans),
        literal_index_spans=tuple(index_spans),
        literal_indices=tuple(range(9)), number_values=None,
        induction_read_spans=reads,
    )


def _compatibility_sites(program: TypedProgram,
                         blend: TypedFunction) -> tuple[RefractCompatibilitySiteProof, ...] | None:
    statement = blend.body[3]
    sites: list[RefractCompatibilitySiteProof] = []
    modes: list[int] = []
    while True:
        if (statement.kind != "if" or len(statement.expressions) != 1
                or not statement.children):
            return None
        guard = statement.expressions[0]
        if (guard.kind != "binary" or guard.operator != "=="
                or len(guard.children) != 2):
            return None
        literals = [item for item in guard.children
                    if item.kind == "literal" and isinstance(item.literal_value, int)]
        ids = [item for item in guard.children
               if item.kind == "id" and item.symbol_id == 9]
        if len(literals) != 1 or len(ids) != 1:
            return None
        mode = literals[0].literal_value
        modes.append(mode)
        if mode in _COMPATIBILITY:
            block = statement.children[0]
            if (block.kind != "block" or len(block.children) != 1
                    or block.children[0].kind != "expr"
                    or len(block.children[0].expressions) != 1):
                return None
            assignment = block.children[0].expressions[0]
            if (assignment.kind != "assign" or assignment.operator != "="
                    or len(assignment.children) != 2
                    or assignment.children[0].kind != "id"
                    or assignment.children[0].symbol_id != 47
                    or assignment.children[1].kind != "id"
                    or assignment.children[1].symbol_id != 47):
                return None
            source_id, constant, builtin, condition_offsets, false_offsets = _COMPATIBILITY[mode]
            sites.append(RefractCompatibilitySiteProof(
                blend_mode=mode, guard_span=guard.span,
                assignment_statement_span=block.children[0].span,
                assignment_span=assignment.span, target_symbol_id=47,
                source_symbol_id=source_id, equality_constant=constant,
                false_builtin=builtin,
                original_condition_span=span_at(
                    REFRACT_KEY, program.source, *condition_offsets),
                original_false_span=span_at(
                    REFRACT_KEY, program.source, *false_offsets),
                transformed_rhs_span=assignment.children[1].span,
            ))
        if len(statement.children) == 1:
            break
        if len(statement.children) != 2 or statement.children[1].kind != "if":
            return None
        statement = statement.children[1]
    if tuple(modes) != (0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18):
        return None
    return tuple(sites) if tuple(item.blend_mode for item in sites) == (2, 3, 7, 15) else None


def _mode_one(main: TypedFunction) -> tuple[SourceSpan, tuple[SourceSpan, ...]] | None:
    outer = main.body[8]
    if (outer.kind != "if" or len(outer.children) != 2
            or outer.children[1].kind != "if"):
        return None
    mode_one = outer.children[1]
    guard = mode_one.expressions[0] if len(mode_one.expressions) == 1 else None
    if (guard is None or guard.kind != "binary" or guard.operator != "=="
            or len(guard.children) != 2
            or not any(item.kind == "id" and item.symbol_id == 6 for item in guard.children)
            or not any(_literal_int(item, 1) for item in guard.children)
            or len(mode_one.children) != 1 or mode_one.children[0].kind != "block"
            or len(mode_one.children[0].children) != 2):
        return None
    calls: list[TypedExpression] = []
    for statement, signature_id, name in zip(
            mode_one.children[0].children, (39, 40), ("derivX", "derivY")):
        matches = [value for value in _walk_statement(statement)
                   if isinstance(value, TypedExpression)
                   and value.kind == "call" and value.signature_id == signature_id
                   and value.callee == name]
        if (len(matches) != 1 or len(matches[0].children) != 3
                or matches[0].children[2].kind != "literal"
                or matches[0].children[2].literal_value is not False):
            return None
        calls.append(matches[0])
    return mode_one.span, tuple(item.span for item in calls)


def _array_census(program: TypedProgram, array_ids: frozenset[int],
                  induction_symbol_id: int,
                  direct_calls: tuple[TypedExpression, ...]):
    expressions = _all_expressions(program)
    array_parameters = tuple(
        item for function in program.functions for item in function.parameters
        if item.type.kind == "array")
    array_declarations = tuple(
        item for item in expressions
        if item.kind == "declaration" and item.type.kind == "array")
    array_expressions = tuple(item for item in expressions if item.type.kind == "array")
    array_identifiers = tuple(
        item for item in expressions if item.kind == "id"
        and item.type.kind == "array")
    indexes = tuple(item for item in expressions if item.kind == "index")
    literal_stores = tuple(
        item for item in expressions
        if item.kind == "assign" and item.operator == "=" and item.children
        and item.children[0].kind == "index"
        and len(item.children[0].children) == 2
        and item.children[0].children[0].kind == "id"
        and item.children[0].children[0].symbol_id in array_ids
        and item.children[0].children[1].kind == "literal")
    induction_reads = tuple(
        item for item in indexes if len(item.children) == 2
        and item.children[0].kind == "id"
        and item.children[0].symbol_id in array_ids
        and item.children[1].kind == "id"
        and item.children[1].symbol_id == induction_symbol_id)
    whole_arguments = tuple(item.children[1] for item in direct_calls)
    array_calls = tuple(
        item for item in expressions if item.kind == "call"
        and any(child.type.kind == "array" for child in item.children))
    return (array_parameters, array_declarations, array_expressions,
            array_identifiers, literal_stores, induction_reads, indexes,
            whole_arguments, array_calls)


def _prove_refract(program: TypedProgram,
                   profile: _Profile) -> FixedArrayInParameterProof | None:
    """Return a proof only for the exact transformed, pinned Refract program."""
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    typed_hash = _sha(program.functions)
    interface_hash = _interface_fingerprint(program)
    whole_hash = _whole_program_fingerprint(program)
    if (program.preprocessor_defines != profile.preprocessor_defines
            or raw_hash != profile.raw_source_sha256
            or normalized_hash != profile.normalized_source_sha256
            or typed_hash != profile.typed_ir_sha256
            or interface_hash != profile.interface_sha256
            or whole_hash != profile.whole_program_sha256
            or program.fixed_nine_table_proof is not None
            or program.fixed_grid_counter_store_proof is not None
            or program.body_status != "analyzed"
            or program.structs or program.uniform_blocks
            or program.resources.uniforms != tuple(item.split(":", 1)[0]
                                                   for item in profile.binding_signature)
            or program.resources.samplers != ("inputTex",)
            or program.resources.outputs != ("fragColor",)
            or not program.resources.uses_texture
            or program.resources.uses_derivatives):
        return None
    binding_signature = tuple(
        f"{item.symbol.name}:{item.type.display()}"
        for item in program.declarations if item.symbol.storage == "uniform")
    if binding_signature != profile.binding_signature:
        return None

    blend = _definition(program, 35, "blend", 6)
    convolve = _definition(program, 38, "convolve", 17)
    deriv_x = _definition(program, 39, "derivX", 13)
    deriv_y = _definition(program, 40, "derivY", 13)
    main = _definition(program, 42, "main", 14)
    if None in (blend, convolve, deriv_x, deriv_y, main):
        return None
    assert blend is not None and convolve is not None
    assert deriv_x is not None and deriv_y is not None and main is not None

    compatibility = _compatibility_sites(program, blend)
    if compatibility is None:
        return None
    if (convolve.return_type.display() != "vec3"
            or tuple((item.id, item.name, item.type.display(), item.direction)
                     for item in convolve.parameters)
            != ((18, "uv", "vec2", "in"),
                (19, "kernel", "float[9]", "in"),
                (20, "divide", "bool", "in"))):
        return None
    loop = convolve.body[14]
    if (loop.kind != "for" or loop.loop_proof is None
            or len(loop.expressions) != 2 or len(loop.children) != 2
            or loop.children[1].kind != "block"
            or len(loop.children[1].children) != 3):
        return None
    loop_proof = loop.loop_proof
    if ((loop_proof.induction_symbol_id, loop_proof.start_value,
         loop_proof.bound_value, loop_proof.comparison, loop_proof.update,
         loop_proof.trip_count, loop_proof.lexical_depth,
         loop_proof.effective_depth, loop_proof.lexical_product,
         loop_proof.entrypoint_charge)
            != (54, 0, 9, "<", "++", 9, 1, 1, 9, 18)):
        return None
    offset = _offset_table(convolve, 54)
    if offset is None:
        return None

    caller_results = tuple(
        _caller_table(function, symbol_id, name, values)
        for function, (_, _, symbol_id, name, values) in zip(
            (deriv_x, deriv_y), _CALLER_PROFILES))
    if any(item is None for item in caller_results):
        return None
    callers = tuple(item[0] for item in caller_results if item is not None)
    direct_calls = tuple(item[1] for item in caller_results if item is not None)

    parameter_reads = tuple(
        value.span for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "index"
        and len(value.children) == 2 and value.children[0].kind == "id"
        and value.children[0].symbol_id == 19
        and value.children[1].kind == "id"
        and value.children[1].symbol_id == 54)
    if len(parameter_reads) != 2:
        return None
    parameter = FixedArrayParameterProof(
        owner_signature_id=38, parameter_ordinal=1, symbol_id=19,
        symbol_name="kernel", array_type="float[9]", element_type="float",
        extent=9, direction="in", native_abi="const Kernel9&",
        induction_read_spans=parameter_reads, reads_per_iteration=2,
        direct_call_spans=tuple(item.span for item in direct_calls),
        direct_argument_spans=tuple(item.children[1].span for item in direct_calls),
    )
    mode = _mode_one(main)
    if mode is None:
        return None

    (array_parameters, array_declarations, array_expressions,
     array_identifiers, literal_stores, induction_reads, indexes,
     whole_arguments, array_calls) = _array_census(
        program, profile.array_ids, 54, direct_calls)
    if ((len(array_parameters), len(array_declarations), len(array_expressions),
         len(array_identifiers), len(literal_stores), len(induction_reads),
         len(indexes), len(whole_arguments), len(array_calls))
            != profile.census
            or {item.symbol_id for item in array_expressions
                if item.symbol_id is not None} != profile.array_ids
            or {item.symbol_id for item in array_identifiers} != profile.array_ids):
        return None

    return FixedArrayInParameterProof(
        proof_kind=CAPABILITY, source_profile=profile.source_profile,
        raw_source_sha256=raw_hash, normalized_source_sha256=normalized_hash,
        canonical_factory_sha256=profile.canonical_factory_sha256,
        define_contract=program.preprocessor_defines,
        binding_signature=binding_signature,
        compatibility_sites=compatibility,
        kernel_alias="Kernel9", offsets_alias="Offsets9",
        caller_tables=callers, parameter=parameter, offset_table=offset,
        convolve_loop_span=loop.span, induction_symbol_id=54,
        loop_trip_count=9, lexical_product=9, entrypoint_charge=18,
        main_signature_id=42, mode_one_span=mode[0],
        main_derivative_call_spans=mode[1],
        array_parameter_count=1, array_declaration_count=3,
        array_typed_expression_count=35,
        array_identifier_reference_count=32, literal_store_count=27,
        induction_read_count=3, index_expression_count=30,
        whole_array_argument_count=2, array_call_count=2,
        no_alias_copy_escape_return_or_post_call_use=True,
        complete_initialization_dominates_reads=True,
        caller_tables_never_simultaneously_live=True,
        parameter_read_only_and_synchronous=True,
        mode_zero_array_free=True, raw_simultaneous_payload_bytes=144,
        interface_sha256=interface_hash, typed_ir_sha256=typed_hash,
        whole_program_sha256=whole_hash,
    )


def _cellrefract_caller_table(
        program: TypedProgram, function: TypedFunction, symbol_id: int,
        name: str, call_index: int,
        expected_values: tuple[float, ...],
        convolve_signature_id: int = 66) -> tuple[
            FixedArrayOwnedTableProof, TypedExpression] | None:
    declaration = None
    for statement in function.body:
        candidate = _declaration(statement, symbol_id, name, "float[9]")
        if candidate is not None and not candidate.children:
            declaration = candidate
            declaration_index = function.body.index(statement)
    if declaration is None:
        return None
    store_spans: list[SourceSpan] = []
    index_spans: list[SourceSpan] = []
    values: list[float] = []
    for offset, statement in enumerate(
            function.body[declaration_index + 1:declaration_index + 10]):
        store = _literal_store(statement, symbol_id, offset)
        if store is None:
            return None
        target, rhs = store
        number = _number(rhs)
        if number is None:
            return None
        store_spans.append(statement.span)
        index_spans.append(target.span)
        values.append(number)
    if tuple(values) != expected_values:
        return None
    if (call_index <= declaration_index + 9
            or call_index >= len(function.body)):
        return None
    statement = function.body[call_index]
    if (statement.kind != "decl" or len(statement.expressions) != 1
            or statement.children):
        return None
    call_declaration = statement.expressions[0]
    if (call_declaration.kind != "declaration"
            or call_declaration.type.display() != "vec3"
            or len(call_declaration.children) != 1):
        return None
    call = call_declaration.children[0]
    if (call.kind != "call" or call.signature_id != convolve_signature_id
            or call.callee != "convolve" or len(call.children) != 3
            or call.children[0].kind != "id"
            or call.children[0].type.display() != "vec2"
            or call.children[1].kind != "id"
            or call.children[1].symbol_id != symbol_id
            or call.children[1].symbol is not declaration.symbol
            or call.children[2].type.display() != "bool"):
        return None
    # Read-only, completely initialized before its single whole-array use:
    # the table's identifier references are exactly its nine store bases and
    # its one call argument -- no pre-initialization read, no post-call use,
    # no alias copy, and no second passing call anywhere in the program.
    references = tuple(
        value for walked in function.body for value in _walk_statement(walked)
        if isinstance(value, TypedExpression) and value.kind == "id"
        and value.symbol_id == symbol_id)
    if len(references) != 10:
        return None
    passing_calls = tuple(
        value for other in program.functions for walked in other.body
        for value in _walk_statement(walked)
        if isinstance(value, TypedExpression) and value.kind == "call"
        and value.callee == "convolve" and len(value.children) == 3
        and value.children[1].kind == "id"
        and value.children[1].symbol_id == symbol_id)
    if len(passing_calls) != 1 or passing_calls[0] is not call:
        return None
    return (FixedArrayOwnedTableProof(
        role=name, owner_signature_id=function.id, symbol_id=symbol_id,
        symbol_name=name, array_type="float[9]", element_type="float",
        extent=9, native_alias="Kernel9",
        declaration_statement_index=declaration_index,
        declaration_span=declaration.span,
        literal_store_statement_indices=tuple(
            range(declaration_index + 1, declaration_index + 10)),
        literal_store_spans=tuple(store_spans),
        literal_index_spans=tuple(index_spans),
        literal_indices=tuple(range(9)), number_values=tuple(values),
        induction_read_spans=(),
    ), call)


def _cellrefract_offset_table(
        convolve: TypedFunction, owner_signature_id: int = 66,
        symbol_id: int = 101, steps_id: int = 100,
        induction_id: int = 104) -> FixedArrayOwnedTableProof | None:
    declaration = _declaration(convolve.body[1], symbol_id, "offset",
                               "vec2[9]")
    if declaration is None or declaration.children:
        return None
    store_spans: list[SourceSpan] = []
    index_spans: list[SourceSpan] = []
    for index, statement in enumerate(convolve.body[2:11]):
        store = _literal_store(statement, symbol_id, index)
        if store is None:
            return None
        target, rhs = store
        if (rhs.kind != "construct" or rhs.type.display() != "vec2"
                or rhs.constructor_type is None
                or rhs.constructor_type.display() != "vec2"
                or len(rhs.children) != 2
                or tuple(_offset_component(item, steps_id)
                         for item in rhs.children)
                != _CELLREFRACT_OFFSET_COMPONENTS[index]):
            return None
        store_spans.append(statement.span)
        index_spans.append(target.span)
    reads = tuple(value.span for statement in convolve.body
                  for value in _walk_statement(statement)
                  if isinstance(value, TypedExpression)
                  and value.kind == "index" and len(value.children) == 2
                  and value.children[0].kind == "id"
                  and value.children[0].symbol_id == symbol_id
                  and value.children[1].kind == "id"
                  and value.children[1].symbol_id == induction_id)
    if len(reads) != 1:
        return None
    references = tuple(
        value for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "id"
        and value.symbol_id == symbol_id)
    if len(references) != 10:
        return None
    return FixedArrayOwnedTableProof(
        role="offset", owner_signature_id=owner_signature_id,
        symbol_id=symbol_id,
        symbol_name="offset", array_type="vec2[9]", element_type="vec2",
        extent=9, native_alias="Offsets9", declaration_statement_index=1,
        declaration_span=declaration.span,
        literal_store_statement_indices=tuple(range(2, 11)),
        literal_store_spans=tuple(store_spans),
        literal_index_spans=tuple(index_spans),
        literal_indices=tuple(range(9)), number_values=None,
        induction_read_spans=reads,
    )


def _cellrefract_reachable_names(
        program: TypedProgram,
        main_signature_id: int = 71) -> tuple[str, ...]:
    defined = {function.signature.id for function in program.functions
               if function.body}
    edges: dict[int, set[int]] = {}
    for function in program.functions:
        if not function.body:
            continue
        edges[function.signature.id] = {
            value.signature_id for statement in function.body
            for value in _walk_statement(statement)
            if isinstance(value, TypedExpression) and value.kind == "call"
            and value.signature_id in defined}
    reached: set[int] = set()
    pending = [main_signature_id]
    while pending:
        signature_id = pending.pop()
        if signature_id in reached:
            continue
        reached.add(signature_id)
        pending.extend(edges.get(signature_id, ()))
    return tuple(sorted(
        next(function.name for function in program.functions
             if function.signature.id == signature_id)
        for signature_id in reached))


def _prove_cellrefract(program: TypedProgram,
                       profile: _Profile) -> FixedArrayInParameterProof | None:
    """Return a proof only for the exact pinned, KERNEL=0 cellRefract program."""
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    typed_hash = _sha(program.functions)
    interface_hash = _interface_fingerprint(program)
    whole_hash = _whole_program_fingerprint(program)
    if (program.preprocessor_defines != profile.preprocessor_defines
            or raw_hash != profile.raw_source_sha256
            or normalized_hash != profile.normalized_source_sha256
            or typed_hash != profile.typed_ir_sha256
            or interface_hash != profile.interface_sha256
            or whole_hash != profile.whole_program_sha256
            or program.fixed_nine_table_proof is not None
            or program.fixed_grid_counter_store_proof is not None
            or program.body_status != "analyzed"
            or program.structs or program.uniform_blocks
            or program.resources.uniforms != tuple(item.split(":", 1)[0]
                                                   for item in profile.binding_signature)
            or program.resources.samplers != ("inputTex",)
            or program.resources.outputs != ("fragColor",)
            or not program.resources.uses_texture
            or program.resources.uses_derivatives):
        return None
    binding_signature = tuple(
        f"{item.symbol.name}:{item.type.display()}"
        for item in program.declarations if item.symbol.storage == "uniform")
    if binding_signature != profile.binding_signature:
        return None

    convolve = _definition(program, 66, "convolve", 16)
    main = _definition(program, 71, "main", 16)
    collapsed = _definition(program, 65, "convolutionKernel", 1)
    if None in (convolve, main, collapsed):
        return None
    assert convolve is not None and main is not None and collapsed is not None
    if (convolve.return_type.display() != "vec3"
            or tuple((item.id, item.name, item.type.display(), item.direction)
                     for item in convolve.parameters)
            != _CELLREFRACT_PARAMETERS):
        return None
    loop = convolve.body[13]
    if (loop.kind != "for" or loop.loop_proof is None
            or len(loop.expressions) != 2 or len(loop.children) != 2
            or loop.children[1].kind != "block"
            or len(loop.children[1].children) != 3):
        return None
    loop_proof = loop.loop_proof
    if ((loop_proof.induction_symbol_id, loop_proof.start_value,
         loop_proof.bound_value, loop_proof.comparison, loop_proof.update,
         loop_proof.bound_kind, loop_proof.trip_count,
         loop_proof.lexical_depth, loop_proof.effective_depth,
         loop_proof.lexical_product, loop_proof.entrypoint_charge)
            != _CELLREFRACT_LOOP_PROOF):
        return None
    # Bind the induction/trip contract to the statements the proof summarizes:
    # `int i = 0;`, `i < 9;` and `i++` with the frozen induction symbol.
    initializer, condition, update = (loop.children[0], *loop.expressions)
    if (initializer.kind != "decl" or len(initializer.expressions) != 1
            or initializer.children
            or initializer.expressions[0].kind != "declaration"
            or initializer.expressions[0].symbol_id != 104
            or len(initializer.expressions[0].children) != 1
            or not _literal_int(initializer.expressions[0].children[0], 0)
            or condition.kind != "binary" or condition.operator != "<"
            or len(condition.children) != 2
            or condition.children[0].kind != "id"
            or condition.children[0].symbol_id != 104
            or not _literal_int(condition.children[1], 9)
            or update.kind != "post" or update.operator != "++"
            or len(update.children) != 1
            or update.children[0].kind != "id"
            or update.children[0].symbol_id != 104):
        return None

    offset = _cellrefract_offset_table(convolve)
    if offset is None:
        return None

    caller_results = []
    for (owner_id, owner_name, body_count, symbol_id, name, call_index,
         values) in _CELLREFRACT_CALLER_TABLES:
        owner = _definition(program, owner_id, owner_name, body_count)
        if owner is None:
            return None
        table = _cellrefract_caller_table(
            program, owner, symbol_id, name, call_index, values)
        if table is None:
            return None
        caller_results.append(table)
    callers = tuple(item[0] for item in caller_results)
    direct_calls = tuple(item[1] for item in caller_results)

    parameter_reads = tuple(
        value.span for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "index"
        and len(value.children) == 2 and value.children[0].kind == "id"
        and value.children[0].symbol_id == 23
        and value.children[1].kind == "id"
        and value.children[1].symbol_id == 104)
    if len(parameter_reads) != 2:
        return None
    kernel_references = tuple(
        value for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "id"
        and value.symbol_id == 23)
    if len(kernel_references) != 2:
        return None
    parameter = FixedArrayParameterProof(
        owner_signature_id=66, parameter_ordinal=1, symbol_id=23,
        symbol_name="kernel", array_type="float[9]", element_type="float",
        extent=9, direction="in", native_abi="const Kernel9&",
        induction_read_spans=parameter_reads, reads_per_iteration=2,
        direct_call_spans=tuple(item.span for item in direct_calls),
        direct_argument_spans=tuple(item.children[1].span for item in direct_calls),
    )

    # Unreachability recorded as a frozen fact: the proof vouches grammar,
    # not liveness.  The KERNEL=0 collapse witness is convolutionKernel's
    # single `return color;` statement, and main invokes no array caller.
    witness = collapsed.body[0]
    if (witness.kind != "return" or len(witness.expressions) != 1
            or witness.children
            or witness.expressions[0].kind != "id"
            or witness.expressions[0].symbol_id != 44
            or witness.expressions[0].symbol is None
            or witness.expressions[0].symbol.name != "color"):
        return None
    if _cellrefract_reachable_names(program) != _CELLREFRACT_REACHABLE:
        return None

    (array_parameters, array_declarations, array_expressions,
     array_identifiers, literal_stores, induction_reads, indexes,
     whole_arguments, array_calls) = _array_census(
        program, profile.array_ids, 104, direct_calls)
    if ((len(array_parameters), len(array_declarations), len(array_expressions),
         len(array_identifiers), len(literal_stores), len(induction_reads),
         len(indexes), len(whole_arguments), len(array_calls))
            != profile.census
            or {item.symbol_id for item in array_expressions
                if item.symbol_id is not None} != profile.array_ids
            or {item.symbol_id for item in array_identifiers} != profile.array_ids):
        return None

    return FixedArrayInParameterProof(
        proof_kind=CAPABILITY, source_profile=profile.source_profile,
        raw_source_sha256=raw_hash, normalized_source_sha256=normalized_hash,
        canonical_factory_sha256=profile.canonical_factory_sha256,
        define_contract=program.preprocessor_defines,
        binding_signature=binding_signature,
        compatibility_sites=(),
        kernel_alias="Kernel9", offsets_alias="Offsets9",
        caller_tables=callers, parameter=parameter, offset_table=offset,
        convolve_loop_span=loop.span, induction_symbol_id=104,
        loop_trip_count=9, lexical_product=9, entrypoint_charge=30,
        main_signature_id=71, mode_one_span=witness.span,
        main_derivative_call_spans=(),
        array_parameter_count=len(array_parameters),
        array_declaration_count=len(array_declarations),
        array_typed_expression_count=len(array_expressions),
        array_identifier_reference_count=len(array_identifiers),
        literal_store_count=len(literal_stores),
        induction_read_count=len(induction_reads),
        index_expression_count=len(indexes),
        whole_array_argument_count=len(whole_arguments),
        array_call_count=len(array_calls),
        no_alias_copy_escape_return_or_post_call_use=True,
        complete_initialization_dominates_reads=True,
        # Derived, not transcribed: within every caller the second table is
        # fully initialized before the first table's consuming convolve call
        # (derivatives lines 199-201 precede 203), so the pairs DO coexist.
        caller_tables_never_simultaneously_live=False,
        parameter_read_only_and_synchronous=True,
        # No mode dispatch exists here; the reachable pixel path writes the
        # five globals through loadKernels every pixel.
        mode_zero_array_free=False, raw_simultaneous_payload_bytes=144,
        interface_sha256=interface_hash, typed_ir_sha256=typed_hash,
        whole_program_sha256=whole_hash,
    )


def _prove_kaleido(program: TypedProgram,
                   profile: _Profile) -> FixedArrayInParameterProof | None:
    """Return a proof only for the exact pinned, KERNEL=0 kaleido program.

    Structurally the cellRefract convolve family under a symbol-id shift
    (globals 13-17, parameter 82, offset table 243, induction 246): the same
    nine-number census tuple, the same caller-table payloads, the same
    KERNEL=0 collapse witness.  The two measured differences frozen here are
    the four-define contract (DIRECTION/KERNEL/LOOP_OFFSET/METRIC) and the
    30-function structural reachable set, whose constant-guard arms
    `LOOP_OFFSET=10` keeps alive (kaleido-design §1) -- plus `shadow`'s
    caller tables at statements 0/10, which the declaration-searching helper
    absorbs.
    """
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    typed_hash = _sha(program.functions)
    interface_hash = _interface_fingerprint(program)
    whole_hash = _whole_program_fingerprint(program)
    if (program.preprocessor_defines != profile.preprocessor_defines
            or raw_hash != profile.raw_source_sha256
            or normalized_hash != profile.normalized_source_sha256
            or typed_hash != profile.typed_ir_sha256
            or interface_hash != profile.interface_sha256
            or whole_hash != profile.whole_program_sha256
            or program.fixed_nine_table_proof is not None
            or program.fixed_grid_counter_store_proof is not None
            or program.body_status != "analyzed"
            or program.structs or program.uniform_blocks
            or program.resources.uniforms != tuple(item.split(":", 1)[0]
                                                   for item in profile.binding_signature)
            or program.resources.samplers != ("inputTex",)
            or program.resources.outputs != ("fragColor",)
            or not program.resources.uses_texture
            or program.resources.uses_derivatives):
        return None
    binding_signature = tuple(
        f"{item.symbol.name}:{item.type.display()}"
        for item in program.declarations if item.symbol.storage == "uniform")
    if binding_signature != profile.binding_signature:
        return None

    convolve = _definition(program, 119, "convolve", 16)
    main = _definition(program, 127, "main", 11)
    collapsed = _definition(program, 118, "convolutionKernel", 1)
    if None in (convolve, main, collapsed):
        return None
    assert convolve is not None and main is not None and collapsed is not None
    if (convolve.return_type.display() != "vec3"
            or tuple((item.id, item.name, item.type.display(), item.direction)
                     for item in convolve.parameters)
            != _KALEIDO_PARAMETERS):
        return None
    loop = convolve.body[13]
    if (loop.kind != "for" or loop.loop_proof is None
            or len(loop.expressions) != 2 or len(loop.children) != 2
            or loop.children[1].kind != "block"
            or len(loop.children[1].children) != 3):
        return None
    loop_proof = loop.loop_proof
    if ((loop_proof.induction_symbol_id, loop_proof.start_value,
         loop_proof.bound_value, loop_proof.comparison, loop_proof.update,
         loop_proof.bound_kind, loop_proof.trip_count,
         loop_proof.lexical_depth, loop_proof.effective_depth,
         loop_proof.lexical_product, loop_proof.entrypoint_charge)
            != _KALEIDO_LOOP_PROOF):
        return None
    # Bind the induction/trip contract to the statements the proof summarizes:
    # `int i = 0;`, `i < 9;` and `i++` with the frozen induction symbol.
    initializer, condition, update = (loop.children[0], *loop.expressions)
    if (initializer.kind != "decl" or len(initializer.expressions) != 1
            or initializer.children
            or initializer.expressions[0].kind != "declaration"
            or initializer.expressions[0].symbol_id != 246
            or len(initializer.expressions[0].children) != 1
            or not _literal_int(initializer.expressions[0].children[0], 0)
            or condition.kind != "binary" or condition.operator != "<"
            or len(condition.children) != 2
            or condition.children[0].kind != "id"
            or condition.children[0].symbol_id != 246
            or not _literal_int(condition.children[1], 9)
            or update.kind != "post" or update.operator != "++"
            or len(update.children) != 1
            or update.children[0].kind != "id"
            or update.children[0].symbol_id != 246):
        return None

    offset = _cellrefract_offset_table(
        convolve, owner_signature_id=119, symbol_id=_KALEIDO_OFFSET_SYMBOL_ID,
        steps_id=_KALEIDO_OFFSET_STEPS_ID, induction_id=246)
    if offset is None:
        return None

    caller_results = []
    for (owner_id, owner_name, body_count, symbol_id, name, call_index,
         values) in _KALEIDO_CALLER_TABLES:
        owner = _definition(program, owner_id, owner_name, body_count)
        if owner is None:
            return None
        table = _cellrefract_caller_table(
            program, owner, symbol_id, name, call_index, values,
            convolve_signature_id=119)
        if table is None:
            return None
        caller_results.append(table)
    callers = tuple(item[0] for item in caller_results)
    direct_calls = tuple(item[1] for item in caller_results)

    parameter_reads = tuple(
        value.span for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "index"
        and len(value.children) == 2 and value.children[0].kind == "id"
        and value.children[0].symbol_id == 82
        and value.children[1].kind == "id"
        and value.children[1].symbol_id == 246)
    if len(parameter_reads) != 2:
        return None
    kernel_references = tuple(
        value for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "id"
        and value.symbol_id == 82)
    if len(kernel_references) != 2:
        return None
    parameter = FixedArrayParameterProof(
        owner_signature_id=119, parameter_ordinal=1, symbol_id=82,
        symbol_name="kernel", array_type="float[9]", element_type="float",
        extent=9, direction="in", native_abi="const Kernel9&",
        induction_read_spans=parameter_reads, reads_per_iteration=2,
        direct_call_spans=tuple(item.span for item in direct_calls),
        direct_argument_spans=tuple(item.children[1].span for item in direct_calls),
    )

    # Unreachability recorded as a frozen fact: the proof vouches grammar,
    # not liveness.  The KERNEL=0 collapse witness is convolutionKernel's
    # single `return color;` statement, and main invokes no array caller.
    witness = collapsed.body[0]
    if (witness.kind != "return" or len(witness.expressions) != 1
            or witness.children
            or witness.expressions[0].kind != "id"
            or witness.expressions[0].symbol_id != 94
            or witness.expressions[0].symbol is None
            or witness.expressions[0].symbol.name != "color"):
        return None
    if _cellrefract_reachable_names(program, main_signature_id=127) \
            != _KALEIDO_REACHABLE:
        return None

    (array_parameters, array_declarations, array_expressions,
     array_identifiers, literal_stores, induction_reads, indexes,
     whole_arguments, array_calls) = _array_census(
        program, profile.array_ids, 246, direct_calls)
    if ((len(array_parameters), len(array_declarations), len(array_expressions),
         len(array_identifiers), len(literal_stores), len(induction_reads),
         len(indexes), len(whole_arguments), len(array_calls))
            != profile.census
            or {item.symbol_id for item in array_expressions
                if item.symbol_id is not None} != profile.array_ids
            or {item.symbol_id for item in array_identifiers} != profile.array_ids):
        return None

    return FixedArrayInParameterProof(
        proof_kind=CAPABILITY, source_profile=profile.source_profile,
        raw_source_sha256=raw_hash, normalized_source_sha256=normalized_hash,
        canonical_factory_sha256=profile.canonical_factory_sha256,
        define_contract=program.preprocessor_defines,
        binding_signature=binding_signature,
        compatibility_sites=(),
        kernel_alias="Kernel9", offsets_alias="Offsets9",
        caller_tables=callers, parameter=parameter, offset_table=offset,
        convolve_loop_span=loop.span, induction_symbol_id=246,
        loop_trip_count=9, lexical_product=9, entrypoint_charge=0,
        main_signature_id=127, mode_one_span=witness.span,
        main_derivative_call_spans=(),
        array_parameter_count=len(array_parameters),
        array_declaration_count=len(array_declarations),
        array_typed_expression_count=len(array_expressions),
        array_identifier_reference_count=len(array_identifiers),
        literal_store_count=len(literal_stores),
        induction_read_count=len(induction_reads),
        index_expression_count=len(indexes),
        whole_array_argument_count=len(whole_arguments),
        array_call_count=len(array_calls),
        no_alias_copy_escape_return_or_post_call_use=True,
        complete_initialization_dominates_reads=True,
        # Derived, not transcribed: within every caller the second table is
        # fully initialized before the first table's consuming convolve
        # call, exactly the cellRefract shape -- the pairs DO coexist.
        caller_tables_never_simultaneously_live=False,
        parameter_read_only_and_synchronous=True,
        # No mode dispatch exists here; the reachable pixel path writes the
        # five globals through loadKernels every pixel.
        mode_zero_array_free=False, raw_simultaneous_payload_bytes=144,
        interface_sha256=interface_hash, typed_ir_sha256=typed_hash,
        whole_program_sha256=whole_hash,
    )


def _prove_effects(program: TypedProgram,
                   profile: _Profile) -> FixedArrayInParameterProof | None:
    """Return a proof only for the exact pinned, EFFECT=0 effects program.

    Structurally the cellRefract/kaleido convolve family under its own
    symbol ids (SEVEN globals 15-21, parameter 42, offset table 151,
    induction 154): the same caller-table payloads, the same EFFECT=0
    collapse witness (`convolutionEffect` reduced to `return color;`, which
    is what makes all seven globals write-only), the same shadow-at-0/10
    quirk.  The measured differences frozen here are the two-define contract
    (EFFECT/FLIP), the eight-function reachable set, and the family's first
    SEVEN-array whole-program census (144 literal stores over 17 array ids
    -- never shared with a sibling key).
    """
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    typed_hash = _sha(program.functions)
    interface_hash = _interface_fingerprint(program)
    whole_hash = _whole_program_fingerprint(program)
    if (program.preprocessor_defines != profile.preprocessor_defines
            or raw_hash != profile.raw_source_sha256
            or normalized_hash != profile.normalized_source_sha256
            or typed_hash != profile.typed_ir_sha256
            or interface_hash != profile.interface_sha256
            or whole_hash != profile.whole_program_sha256
            or program.fixed_nine_table_proof is not None
            or program.fixed_grid_counter_store_proof is not None
            or program.body_status != "analyzed"
            or program.structs or program.uniform_blocks
            or program.resources.uniforms != tuple(item.split(":", 1)[0]
                                                   for item in profile.binding_signature)
            or program.resources.samplers != ("inputTex",)
            or program.resources.outputs != ("fragColor",)
            or not program.resources.uses_texture
            or program.resources.uses_derivatives):
        return None
    binding_signature = tuple(
        f"{item.symbol.name}:{item.type.display()}"
        for item in program.declarations if item.symbol.storage == "uniform")
    if binding_signature != profile.binding_signature:
        return None

    convolve = _definition(program, 70, "convolve", 16)
    main = _definition(program, 76, "main", 23)
    collapsed = _definition(program, 69, "convolutionEffect", 1)
    if None in (convolve, main, collapsed):
        return None
    assert convolve is not None and main is not None and collapsed is not None
    if (convolve.return_type.display() != "vec3"
            or tuple((item.id, item.name, item.type.display(), item.direction)
                     for item in convolve.parameters)
            != _EFFECTS_PARAMETERS):
        return None
    loop = convolve.body[13]
    if (loop.kind != "for" or loop.loop_proof is None
            or len(loop.expressions) != 2 or len(loop.children) != 2
            or loop.children[1].kind != "block"
            or len(loop.children[1].children) != 3):
        return None
    loop_proof = loop.loop_proof
    if ((loop_proof.induction_symbol_id, loop_proof.start_value,
         loop_proof.bound_value, loop_proof.comparison, loop_proof.update,
         loop_proof.bound_kind, loop_proof.trip_count,
         loop_proof.lexical_depth, loop_proof.effective_depth,
         loop_proof.lexical_product, loop_proof.entrypoint_charge)
            != _EFFECTS_LOOP_PROOF):
        return None
    # Bind the induction/trip contract to the statements the proof summarizes:
    # `int i = 0;`, `i < 9;` and `i++` with the frozen induction symbol.
    initializer, condition, update = (loop.children[0], *loop.expressions)
    if (initializer.kind != "decl" or len(initializer.expressions) != 1
            or initializer.children
            or initializer.expressions[0].kind != "declaration"
            or initializer.expressions[0].symbol_id != 154
            or len(initializer.expressions[0].children) != 1
            or not _literal_int(initializer.expressions[0].children[0], 0)
            or condition.kind != "binary" or condition.operator != "<"
            or len(condition.children) != 2
            or condition.children[0].kind != "id"
            or condition.children[0].symbol_id != 154
            or not _literal_int(condition.children[1], 9)
            or update.kind != "post" or update.operator != "++"
            or len(update.children) != 1
            or update.children[0].kind != "id"
            or update.children[0].symbol_id != 154):
        return None

    offset = _cellrefract_offset_table(
        convolve, owner_signature_id=70, symbol_id=_EFFECTS_OFFSET_SYMBOL_ID,
        steps_id=_EFFECTS_OFFSET_STEPS_ID, induction_id=154)
    if offset is None:
        return None

    caller_results = []
    for (owner_id, owner_name, body_count, symbol_id, name, call_index,
         values) in _EFFECTS_CALLER_TABLES:
        owner = _definition(program, owner_id, owner_name, body_count)
        if owner is None:
            return None
        table = _cellrefract_caller_table(
            program, owner, symbol_id, name, call_index, values,
            convolve_signature_id=70)
        if table is None:
            return None
        caller_results.append(table)
    callers = tuple(item[0] for item in caller_results)
    direct_calls = tuple(item[1] for item in caller_results)

    parameter_reads = tuple(
        value.span for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "index"
        and len(value.children) == 2 and value.children[0].kind == "id"
        and value.children[0].symbol_id == 42
        and value.children[1].kind == "id"
        and value.children[1].symbol_id == 154)
    if len(parameter_reads) != 2:
        return None
    kernel_references = tuple(
        value for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "id"
        and value.symbol_id == 42)
    if len(kernel_references) != 2:
        return None
    parameter = FixedArrayParameterProof(
        owner_signature_id=70, parameter_ordinal=1, symbol_id=42,
        symbol_name="kernel", array_type="float[9]", element_type="float",
        extent=9, direction="in", native_abi="const Kernel9&",
        induction_read_spans=parameter_reads, reads_per_iteration=2,
        direct_call_spans=tuple(item.span for item in direct_calls),
        direct_argument_spans=tuple(item.children[1].span for item in direct_calls),
    )

    # Unreachability recorded as a frozen fact: the proof vouches grammar,
    # not liveness.  The EFFECT=0 collapse witness is convolutionEffect's
    # single `return color;` statement, and main invokes no array caller.
    witness = collapsed.body[0]
    if (witness.kind != "return" or len(witness.expressions) != 1
            or witness.children
            or witness.expressions[0].kind != "id"
            or witness.expressions[0].symbol_id != 53
            or witness.expressions[0].symbol is None
            or witness.expressions[0].symbol.name != "color"):
        return None
    if _cellrefract_reachable_names(program, main_signature_id=76) \
            != _EFFECTS_REACHABLE:
        return None

    (array_parameters, array_declarations, array_expressions,
     array_identifiers, literal_stores, induction_reads, indexes,
     whole_arguments, array_calls) = _array_census(
        program, profile.array_ids, 154, direct_calls)
    if ((len(array_parameters), len(array_declarations), len(array_expressions),
         len(array_identifiers), len(literal_stores), len(induction_reads),
         len(indexes), len(whole_arguments), len(array_calls))
            != profile.census
            or {item.symbol_id for item in array_expressions
                if item.symbol_id is not None} != profile.array_ids
            or {item.symbol_id for item in array_identifiers} != profile.array_ids):
        return None

    return FixedArrayInParameterProof(
        proof_kind=CAPABILITY, source_profile=profile.source_profile,
        raw_source_sha256=raw_hash, normalized_source_sha256=normalized_hash,
        canonical_factory_sha256=profile.canonical_factory_sha256,
        define_contract=program.preprocessor_defines,
        binding_signature=binding_signature,
        compatibility_sites=(),
        kernel_alias="Kernel9", offsets_alias="Offsets9",
        caller_tables=callers, parameter=parameter, offset_table=offset,
        convolve_loop_span=loop.span, induction_symbol_id=154,
        loop_trip_count=9, lexical_product=9, entrypoint_charge=0,
        main_signature_id=76, mode_one_span=witness.span,
        main_derivative_call_spans=(),
        array_parameter_count=len(array_parameters),
        array_declaration_count=len(array_declarations),
        array_typed_expression_count=len(array_expressions),
        array_identifier_reference_count=len(array_identifiers),
        literal_store_count=len(literal_stores),
        induction_read_count=len(induction_reads),
        index_expression_count=len(indexes),
        whole_array_argument_count=len(whole_arguments),
        array_call_count=len(array_calls),
        no_alias_copy_escape_return_or_post_call_use=True,
        complete_initialization_dominates_reads=True,
        # Derived, not transcribed: within every caller the second table is
        # fully initialized before the first table's consuming convolve
        # call, exactly the family shape -- the pairs DO coexist.
        caller_tables_never_simultaneously_live=False,
        parameter_read_only_and_synchronous=True,
        # No mode dispatch exists here; the reachable pixel path writes the
        # seven globals through loadKernels every pixel.
        mode_zero_array_free=False, raw_simultaneous_payload_bytes=144,
        interface_sha256=interface_hash, typed_ir_sha256=typed_hash,
        whole_program_sha256=whole_hash,
    )


def prove_fixed_array_in_parameter(
        program: TypedProgram) -> FixedArrayInParameterProof | None:
    """Return a proof only for an exact transformed, pinned program."""
    profile = PROFILES.get(program.key)
    if profile is None:
        return None
    if program.key == REFRACT_KEY:
        return _prove_refract(program, profile)
    if program.key == CELLREFRACT_KEY:
        return _prove_cellrefract(program, profile)
    if program.key == KALEIDO_KEY:
        return _prove_kaleido(program, profile)
    return _prove_effects(program, profile)


def attach_fixed_array_in_parameter_proof(program: TypedProgram) -> TypedProgram:
    base = dataclasses.replace(program, fixed_array_in_parameter_proof=None)
    return dataclasses.replace(
        base, fixed_array_in_parameter_proof=prove_fixed_array_in_parameter(base))
