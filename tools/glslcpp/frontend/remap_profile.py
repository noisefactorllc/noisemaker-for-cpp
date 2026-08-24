"""Hash-bound frontend admission for ``synth/remap:remap``.

Remap is deliberately kept out of the generic array and uniform-block
machinery.  This profile authenticates one fixed std140 block, its four exact
index nodes, the three bounded source loops, and the complete sampler/binding
surface.  The returned proof contains candidate-owned objects for the future
generator/emitter lane; no global capability is widened here.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import NamedTuple

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "synth/remap:remap"
REMAP_KEY = KEY
PROFILE = "remap-std140-frontend-v1"
REMAP_PROFILE = PROFILE
KEYS = (KEY,)
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = KEYS
PREPARED_PROFILES = PROFILES
REQUIRED_COMPANION_PROFILES = {KEY: ()}
ALLOWED_ROW_FIELDS = {
    KEY: frozenset({"defines", "program_key", "remap_profile"}),
}

BINDING_NAMES = (
    "data", "tileOffset", "fullResolution", "zone0_tex", "zone1_tex",
    "zone2_tex", "zone3_tex", "zone4_tex", "zone5_tex", "zone6_tex",
    "zone7_tex",
)
SOURCE_BINDING_ABI = (
    ("data", "vec4[267]"), ("tileOffset", "vec2"),
    ("fullResolution", "vec2"),
    *((f"zone{i}_tex", "sampler2D") for i in range(8)),
)
RUNTIME_BINDING_ABI = (
    ("data", "std140 vec4[267]"), ("tileOffset", "Vec2"),
    ("fullResolution", "Vec2"),
    *((f"zone{i}_tex", "sampler2D") for i in range(8)),
)
SOURCE_UNIFORM_ABI = SOURCE_BINDING_ABI
RUNTIME_UNIFORM_ABI = RUNTIME_BINDING_ABI

RAW_BYTES = 5117
RAW_SHA256 = "e70bb491b2838bc2e5632a458fb2aeb5488d772d734b6e4caf7958afa9737e7f"
NORMALIZED_BYTES = 3447
NORMALIZED_SHA256 = "50b5db4643f9095cfd24831f9c8d9e94dc942aa20c5d7a6e398658e521e7f37e"
FUNCTIONS_SHA256 = "6a822484a221a99b8f61086ba662f075e899b37fb00d19cafc9db0a600c618db"
WHOLE_SHA256 = "fefd573fd895f4cebfea46667ae5df28642a9bdda913a824a392f3851d83bd98"
INTERFACE_SHA256 = "c81005045a65d4c2dfdc203177a96cd2b865d9e874dc4c9548b1e065eb60753c"
DEFINES = ()

# These are fixed source constants, retained explicitly even though the source
# and normalized fingerprints already bind them.  The generator may use them
# when lowering data[] accesses without rediscovering preprocessor state.
SOURCE_CONSTANTS = (
    ("MAX_ZONES", 8), ("MAX_VERTS_PER_ZONE", 64), ("MAX_PAIRS", 32),
    ("HEADER_SLOT", 0), ("CONTROLS_SLOT", 1), ("ZONE_META_SLOT", 2),
    ("ZONE_VERTS_SLOT", 10),
)
_CONSTANT_LINES = (
    "#define MAX_ZONES 8", "#define MAX_VERTS_PER_ZONE 64",
    "#define MAX_PAIRS 32", "#define HEADER_SLOT 0",
    "#define CONTROLS_SLOT 1", "#define ZONE_META_SLOT 2",
    "#define ZONE_VERTS_SLOT 10",
)


class BindingPreflight(NamedTuple):
    names: tuple[str, ...]
    source_abi: tuple[tuple[str, str], ...]
    runtime_abi: tuple[tuple[str, str], ...]
    resources: tuple


class IndexRecord(NamedTuple):
    function_id: int
    function_name: str
    span: str
    node_sha256: str
    base_symbol_id: int
    base_name: str
    base_type: str
    index_type: str
    index_shape: str
    index_operator: str | None
    index_literal: int | None
    parent_kind: str | None
    child_types: tuple[str, ...]
    node: TypedExpression


class LoopRecord(NamedTuple):
    function_id: int
    function_name: str
    span: str
    induction_symbol_id: int
    start: int
    bound: int
    comparison: str
    update: str
    trip_count: int
    effective_depth: int
    proof: object


class FrontendProof(NamedTuple):
    program_key: str
    uniform_block: object
    data_field: object
    indexes: tuple[IndexRecord, ...]
    loops: tuple[LoopRecord, ...]
    binding_preflight: BindingPreflight
    source_constants: tuple[tuple[str, int], ...]
    consumed_objects: tuple[object, ...]

    @property
    def dynamic_indexes(self) -> tuple[IndexRecord, ...]:
        return tuple(item for item in self.indexes if item.index_shape == "binary")


_FUNCTIONS = (
    (29, "distToZoneEdge", "float", 2, 6, "80:1-96:2"),
    (30, "getVert", "vec2", 2, 2, "34:1-37:2"),
    (31, "getZoneActive", "int", 1, 1, "43:1-45:2"),
    (32, "getZoneAlpha", "float", 1, 1, "47:1-49:2"),
    (33, "getZoneCount", "int", 1, 1, "39:1-41:2"),
    (34, "getZoneMeta", "vec4", 1, 1, "26:1-28:2"),
    (35, "getZonePack", "vec4", 2, 1, "30:1-32:2"),
    (36, "main", "void", 0, 13, "98:1-137:2"),
    (37, "pointInZone", "bool", 2, 6, "62:1-78:2"),
    (38, "sampleZone", "vec4", 2, 8, "51:1-60:2"),
)
_LOOP_PROOF = (3, 0, 2, 64, 1032, True)
_LOOPS = (
    (29, "distToZoneEdge", "85:5-94:6", 43, 0, 64, "<", "++", 64, 2),
    (36, "main", "120:5-134:6", 61, 0, 8, "<", "++", 8, 1),
    (37, "pointInZone", "67:5-76:6", 70, 0, 64, "<", "++", 64, 2),
)

# (function, span, node hash, index shape, operator, literal, parent kind,
#  child type tuple).  The base is always the one authenticated data symbol.
_INDEX_LOCKS = (
    (34, "getZoneMeta", "27:12-27:23",
     "4c1fd6e9288b944ed561be0ebeda9434e0b1284f518a792d81425c3699bf57ff",
     "binary", "+", None, None, ("vec4[267]", "int")),
    (35, "getZonePack", "31:12-31:45",
     "bb96149062a6af94d34be9745cabeb10c83bebf99932aaa7cc880e07d1b0e745",
     "binary", "+", None, None, ("vec4[267]", "int")),
    (36, "main", "112:19-112:26",
     "a62d7a3d4ec8a1e0643594d93edad2c7c9c1b3ac3770dca1cd045ce0e8d5497b",
     "literal", None, 0, "declaration", ("vec4[267]", "int")),
    (36, "main", "113:21-113:28",
     "0fce5c7d81c8bcb77c7f3a1d69ed0b02a4f2ccfc8f74b2b4c644fd1c12cd1bca",
     "literal", None, 1, "declaration", ("vec4[267]", "int")),
)

_BINDING_PREFLIGHT = BindingPreflight(
    BINDING_NAMES, SOURCE_BINDING_ABI, RUNTIME_BINDING_ABI,
    (BINDING_NAMES, tuple(f"zone{i}_tex" for i in range(8)), ("fragColor",),
     True, False),
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = value.span
    return f"{span.start_line}:{span.start_column}-{span.end_line}:{span.end_column}"


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources, program.local_type_names,
                 program.structs, program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression,
                     parent: TypedExpression | None = None):
    yield value, parent
    for child in value.children:
        yield from _walk_expression(child, value)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def preflight_remap_bindings(program: TypedProgram,
                             bindings: Mapping[str, object] | None = None
                             ) -> BindingPreflight:
    if program.key != KEY:
        raise _fail("binding or resource key mismatch")
    if len(program.declarations) != 11 + 1:
        raise _fail("binding declaration cardinality mismatch")
    actual = tuple((item.symbol.name, item.type.display(), item.symbol.storage,
                    item.symbol.writable) for item in program.declarations)
    expected = (("data", "vec4[267]", "uniform", False),
                ("tileOffset", "vec2", "uniform", False),
                ("fullResolution", "vec2", "uniform", False),
                *((f"zone{i}_tex", "sampler2D", "uniform", False)
                  for i in range(8)),
                ("fragColor", "vec4", "output", True))
    if actual != expected:
        raise _fail("binding declaration ABI mismatch")
    resources = program.resources
    actual_resources = (resources.uniforms, resources.samplers,
                        resources.outputs, resources.uses_texture,
                        resources.uses_derivatives)
    if actual_resources != _BINDING_PREFLIGHT.resources:
        raise _fail("binding or resource profile mismatch")
    if bindings is not None:
        if not isinstance(bindings, Mapping) or tuple(bindings) != BINDING_NAMES:
            raise _fail("binding or resource names mismatch")
    return _BINDING_PREFLIGHT


def authenticate_remap_frontend(program: TypedProgram, source_hash: str | None,
                                profile: str | None) -> FrontendProof:
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != KEY or source_hash != RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or any(line.encode("utf-8") not in raw for line in _CONSTANT_LINES)
            or tuple((item.name, item.kind, item.canonical_value)
                     for item in program.preprocessor_defines) != DEFINES
            or program.body_status != "analyzed"
            or _sha(program.functions) != FUNCTIONS_SHA256
            or _whole(program) != WHOLE_SHA256
            or _interface(program) != INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field, None) is not None for field in (
            "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
            "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof")):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.interface_symbols != ():
        raise _fail("unrelated struct or interface carrier is present")
    if len(program.uniform_blocks) != 1:
        raise _fail("uniform block cardinality mismatch")
    block = program.uniform_blocks[0]
    if (block.block_name, block.instance_name, len(block.fields),
            _span(block)) != ("RemapUniforms", None, 1, "5:1-7:3"):
        raise _fail("RemapUniforms block identity mismatch")
    field = block.fields[0]
    if (field.name, field.type.display(), field.id, _span(field)) != (
            "data", "vec4[267]", 2, "6:5-6:19"):
        raise _fail("RemapUniforms data field identity mismatch")
    if ((program.counted_loop_proof is None) or
            (program.counted_loop_proof.loop_count,
             program.counted_loop_proof.unproved_loop_count,
             program.counted_loop_proof.max_effective_depth,
             program.counted_loop_proof.max_lexical_product,
             program.counted_loop_proof.entrypoint_charge,
             program.counted_loop_proof.call_graph_acyclic) != _LOOP_PROOF):
        raise _fail("loop or call graph profile mismatch")
    preflight = preflight_remap_bindings(program)
    inventory = tuple((item.id, item.name, item.return_type.display(),
                       len(item.parameters), len(item.body), _span(item))
                      for item in sorted(program.functions, key=lambda x: x.id))
    if inventory != _FUNCTIONS:
        raise _fail("function inventory mismatch")
    loops: list[LoopRecord] = []
    for function in program.functions:
        def visit(statement: TypedStatement) -> None:
            if statement.loop_proof is not None:
                proof = statement.loop_proof
                loops.append(LoopRecord(
                    function.id, function.name, _span(statement),
                    proof.induction_symbol_id, proof.start_value,
                    proof.bound_value, proof.comparison, proof.update,
                    proof.trip_count, proof.effective_depth, proof))
            for child in statement.children:
                visit(child)
        for statement in function.body:
            visit(statement)
    if tuple((item.function_id, item.function_name, item.span,
              item.induction_symbol_id, item.start, item.bound,
              item.comparison, item.update, item.trip_count,
              item.effective_depth) for item in loops) != _LOOPS:
        raise _fail("fixed loop census mismatch")
    located: list[IndexRecord] = []
    for function in program.functions:
        for statement in function.body:
            for item, parent in _walk_statement(statement):
                if item.kind != "index":
                    continue
                if len(item.children) != 2:
                    raise _fail("index arity mismatch")
                base, index = item.children
                if (base.kind != "id" or base.symbol_id != 1
                        or base.type.display() != "vec4[267]"
                        or base.symbol is None or base.symbol.name != "data"):
                    raise _fail("index base is not authenticated data")
                shape = "binary" if index.kind == "binary" else "literal" if index.kind == "literal" else index.kind
                located.append(IndexRecord(
                    function.id, function.name, _span(item), _sha(item),
                    base.symbol_id, base.symbol.name, base.type.display(),
                    index.type.display(), shape, index.operator,
                    index.literal_value if isinstance(index.literal_value, int) else None,
                    parent.kind if parent is not None else None,
                    tuple(child.type.display() for child in item.children), item))
    if len(located) != len(_INDEX_LOCKS):
        raise _fail("index census cardinality mismatch")
    actual = tuple((item.function_id, item.function_name, item.span,
                    item.node_sha256, item.index_shape,
                    item.index_operator, item.index_literal,
                    item.parent_kind, item.child_types) for item in located)
    expected = tuple((row[0], row[1], row[2], row[3], row[4], row[5],
                      row[6], row[7], row[8]) for row in _INDEX_LOCKS)
    if actual != expected:
        raise _fail("index node identity or shape mismatch")
    consumed: list[object] = [block, field, *(item.node for item in located),
                              *(item.proof for item in loops)]
    unique: list[object] = []
    for item in consumed:
        if not any(item is prior for prior in unique):
            unique.append(item)
    if len(unique) != 9 or len(consumed) != 9:
        raise _fail("consumed object cardinality mismatch")
    return FrontendProof(KEY, block, field, tuple(located), tuple(loops),
                         preflight, SOURCE_CONSTANTS, tuple(unique))


__all__ = (
    "KEY", "REMAP_KEY", "PROFILE", "REMAP_PROFILE", "KEYS", "PROFILES",
    "PREPARED_KEYS", "PREPARED_PROFILES", "REQUIRED_COMPANION_PROFILES",
    "ALLOWED_ROW_FIELDS", "BINDING_NAMES", "SOURCE_BINDING_ABI",
    "RUNTIME_BINDING_ABI", "SOURCE_UNIFORM_ABI", "RUNTIME_UNIFORM_ABI",
    "SOURCE_CONSTANTS", "RAW_BYTES", "RAW_SHA256", "NORMALIZED_BYTES",
    "NORMALIZED_SHA256", "FUNCTIONS_SHA256", "WHOLE_SHA256",
    "INTERFACE_SHA256", "BindingPreflight", "IndexRecord", "LoopRecord",
    "FrontendProof", "preflight_remap_bindings", "authenticate_remap_frontend",
)
