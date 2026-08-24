"""Exact source-authenticated color-style closure for Emboss.

This profile admits only the four candidate-owned local 3x3 tables, the two
width-two equality/reduction pairs, and the two reachable texture-coordinate
numerator materialization boundaries in the reviewed STYLE=0 Emboss program.
It does not widen fixed arrays, bvecs, ``equal``, ``all``, or vector
materialization globally.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "emboss-color-style-v1"
EMBOSS_KEY = "filter/emboss:emboss"

_RAW_BYTES = 5160
_RAW_SHA256 = "872eff00bdfe411a0dceb66e8b203b5ea1c03015e3eea041d821966354713191"
_RAW_IR_SHA256 = "4fbe96840dafd37c6a7cf20181bafb2971b81373e206ade774c9a97c548f8d81"
_NORMALIZED_BYTES = 4052
_NORMALIZED_SHA256 = "8f6426db42dac9e25c2051a858616efa79350d4236f5a3f49f7e5a4a5f9a3e3c"
_NORMALIZED_IR_SHA256 = "4498bb25a45447ebdc6a14de763413ebb4e7ba7994388e0b9689c38e9d894030"
_FUNCTIONS_SHA256 = "768fb9d8c4b9e4e8f7a121f406a62aa513cd43507bae07fc41ee038982b2e142"
_DECLARATIONS_SHA256 = "12d3ee6d8e3eba290659ca00f179a75005955f22bdc48c389051638169cc58c4"
_WHOLE_SHA256 = "0e2a4a76ca1ccc9ef6d0f313a32d0eacbd28a8953db46f1842362cc6233a2424"
_INTERFACE_SHA256 = "89fb8a9509822b219d22c4acc6714669598b33a6c09d39c69da18f74f9f24e0b"
_DEFINES = (("STYLE", "int", "0"),)
_RESOURCES = (
    ("tileOffset", "fullResolution", "inputTex", "amount", "angle",
     "height", "colorAmount", "renderScale"),
    ("inputTex",), ("fragColor",), True, False,
)
_LOOP_PROOF = (2, 0, 1, 9, 9, True)
_FUNCTIONS = (
    (18, "colorDefaultEmboss", "vec3",
     ((12, "uv", "vec2"), (13, "texelSize", "vec2")), 23, "26:1-53:2"),
    (19, "colorGeneralEmboss", "vec3",
     ((14, "uv", "vec2"), (15, "texelSize", "vec2")), 26, "55:1-84:2"),
    (20, "grayEmboss", "vec3",
     ((16, "uv", "vec2"), (17, "centerRGB", "vec3")), 12, "86:1-102:2"),
    (21, "main", "void", (), 10, "104:1-124:2"),
    (22, "sampleGlobal", "vec3", ((11, "globalUV", "vec2"),),
     2, "21:1-24:2"),
)
_CALL_GRAPH = {
    "colorDefaultEmboss": (),
    "colorGeneralEmboss": (),
    "grayEmboss": ("sampleGlobal",),
    "main": ("colorDefaultEmboss", "colorGeneralEmboss"),
    "sampleGlobal": (),
}
_REACHABLE_FROM_MAIN = ("colorDefaultEmboss", "colorGeneralEmboss", "main")
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

# owner id/name, body count, symbol id/name/type/native type, declaration index,
# declaration span/hash, declaration-statement hash, literal-store spans,
# store/rhs/target tuple hashes, loop index/span/hash/body hash/induction/body
# count, dynamic-read span/hash/path, and native payload bytes.
_TABLES = (
    (18, "colorDefaultEmboss", 23, 24, "kernel", "float[9]", "double",
     0, "27:11-27:20",
     "36d7270d3e2c24d0749c3f618f514cd429bc1ca432cbc77f2a23a198bd203f13",
     "8df2a671e4995cd7971086bcce344507f3659dd3194fb188e67796652d69fefb",
     ("28:5-28:22", "28:23-28:40", "28:41-28:57",
      "29:5-29:22", "29:23-29:39", "29:41-29:57",
      "30:5-30:21", "30:23-30:39", "30:41-30:57"),
     "85469a39d8583e78a0c001b52889c01d82c6771c53377d07e8d4e0bdfc795718",
     "f29d4a3e675722e477515f48eadd423dc3334be087dc56a93137af92c3b2c1fc",
     "0baae101a5d7308789914259fc2b76bd54a834d5cda2a9783b466594f0efb722",
     21, "47:5-50:6",
     "696af98af800653a6219eb84cc8cbf904732b21e42e0e52224f177f224a518ec",
     "8e4d5e06057dae59fb82c7c70521a0d77b1efcdc612317b9d7333f725518d61b",
     27, 2, "49:29-49:38",
     "a35d02bbb424a016e4b605e111a7fc2af34173a063319a84a6d2ad70690fd0ab",
     (21, "s1", "s1", "e0", 1, 1), 72),
    (18, "colorDefaultEmboss", 23, 25, "offsets", "vec2[9]", "glsl::Vec2",
     10, "35:10-35:20",
     "8abffea0a836092e75912ca5666bd7ec625fa683bb0dd0a1c90839e3db3e9fe0",
     "7f2de7e931ca1c07bc2fc985c17811e6788089b329f4897b0e6e6cadbe89add1",
     ("36:5-36:51", "37:5-37:42", "38:5-38:50",
      "39:5-39:42", "40:5-40:33", "41:5-41:41",
      "42:5-42:50", "43:5-43:41", "44:5-44:49"),
     "c3d2dcd540603accf06e39f23d33d450c10af0d77ea03ae540e36daf548526cd",
     "3cca56422a8bef09794e94bdd45f1b9424f4a7c9ef0e172e17137f487a0d08db",
     "4307f82c9b2f45fee46f5d1ed152d4ad4d3046ce247515061d309b5438bc6602",
     21, "47:5-50:6",
     "696af98af800653a6219eb84cc8cbf904732b21e42e0e52224f177f224a518ec",
     "8e4d5e06057dae59fb82c7c70521a0d77b1efcdc612317b9d7333f725518d61b",
     27, 2, "48:51-48:61",
     "6c84c37ef42ce6cb6189fa20f74597f5434fed7f22e7482f1ac23c342465bdd6",
     (21, "s1", "s0", "e0", 0, 0, 1, 0, 0, 0, 1, 0, 0), 72),
    (19, "colorGeneralEmboss", 26, 29, "kernel", "float[9]", "double",
     0, "56:11-56:20",
     "39ab180903f5c420a122c1e217f75e14d4d8b78b2b38c80b59f27447ed7efce3",
     "c82b56eccb00af27db4a730bcfb97c16adf08f83fed0ec9dd5b62af76a9ca71f",
     ("57:5-57:22", "57:23-57:40", "57:41-57:57",
      "58:5-58:22", "58:23-58:39", "58:41-58:57",
      "59:5-59:21", "59:23-59:39", "59:41-59:57"),
     "355b75b91f1b1b56c307d8f55c993b635d6835cadb257ca97d3791b3c3141d26",
     "12db4ca4db6191f212696c53eb59c9e29ff1679c62dc16943d19c8acb63fdb93",
     "d21a6acb030bd9e46bb7ee877eaaaf585591f1d20f362420d78e67a1f851f97c",
     24, "76:5-82:6",
     "13dff71b37d56e87aae7c5facf5cc980e1a7c34807c4850c02c76b3f647e26c1",
     "6f3824cc9bdb22ab462e1beacbbd4b8590891b3f54f25b2b404a5faf39c6eedf",
     35, 5, "81:29-81:38",
     "6054d46937a056bdeae3188b88016c71dfdb82a5d9fc193fb483e1c3b9ca2fe6",
     (24, "s1", "s4", "e0", 1, 1), 72),
    (19, "colorGeneralEmboss", 26, 30, "baseOffsetsPx", "vec2[9]",
     "glsl::Vec2", 10, "61:10-61:26",
     "26b2ece9e27252d66d6761f36ade78ebb129a317df1fa5d1f9c0f348c2cef0d5",
     "a8d3033bf071b678385afdfa9f0fc4b89ee0e0fbe1b79a7c4ee0741b6517885d",
     ("62:5-62:41", "63:5-63:41", "64:5-64:41",
      "65:5-65:41", "66:5-66:41", "67:5-67:41",
      "68:5-68:41", "69:5-69:41", "70:5-70:41"),
     "f88dc7368573637686f34fb127726045b17aa0bf4f29112971327942c56b59bd",
     "3ba42359608d84d548ecdaba04cf67b15f6b8e05e0f4d77da876e2196331d184",
     "910d5dbde3e809319eb360231a757208a9cda36e550984d5fc10ddaad5b0e980",
     24, "76:5-82:6",
     "13dff71b37d56e87aae7c5facf5cc980e1a7c34807c4850c02c76b3f647e26c1",
     "6f3824cc9bdb22ab462e1beacbbd4b8590891b3f54f25b2b404a5faf39c6eedf",
     35, 5, "77:23-77:39",
     "538c31222c20ca80d35a00c111df5b32c34a9618a944273f7fd24355dbbcbd97",
     (24, "s1", "s0", "e0", 0), 72),
)

# path, span, kind, type, callee/signature, parent kind/callee/operator,
# complete node hash, ordered child type/hash tuples.
_BOOLEAN_NODES = (
    ((5, "e0", 0, 0), "110:22-110:55", "builtin", "bool", "all", -3,
     ("binary", None, "&&"),
     "3d0be7b17c21dc8b8ad704bf1649dacb471ff9350087c747bc2588910bcbf7d9",
     (("bvec2", "6d300948b3d0de554a6b6949ddf03bc685d8b1b53cf297cd0471946e944bc87a"),)),
    ((5, "e0", 0, 0, 0), "110:26-110:54", "builtin", "bvec2", "equal", -14,
     ("builtin", "all", None),
     "6d300948b3d0de554a6b6949ddf03bc685d8b1b53cf297cd0471946e944bc87a",
     (("vec2", "1fb3b23a98d82992b001bc3317c41976da7c6df91f82181c9dd97c9490bdb3a4"),
      ("vec2", "6ebdb48c22d6f6384fea9b0ed50f87eae3c20bec31a197cf3910626462afe8e7"))),
    ((5, "e0", 0, 1), "110:59-110:97", "builtin", "bool", "all", -3,
     ("binary", None, "&&"),
     "cb92ee8ec6bf5ed63eed5353cf2402a33c4d75a95704e14eea1e8f4b0cc2bf6f",
     (("bvec2", "f5b9acc275131d3561563646e7fe465e71b5dde892af03504c73d13c60e5abee"),)),
    ((5, "e0", 0, 1, 0), "110:63-110:96", "builtin", "bvec2", "equal", -14,
     ("builtin", "all", None),
     "f5b9acc275131d3561563646e7fe465e71b5dde892af03504c73d13c60e5abee",
     (("vec2", "3a38863a37a642748a0f00791f435edaf7a743c272dc45b254e28a0e004bfd09"),
      ("vec2", "45d4e5d44c63148d2556399185ca5b02a32f57ba1e30c986ba5c7ae1833bd1d0"))),
)
_MAIN_ROUTE = (
    (5, "110:5-110:98",
     "b2f634ea389535079c71acf50e4a98919d4f7c8dca00d641ea1dc4322e825a2e"),
    (6, "114:5-114:72",
     "8c1733c3df85a98b84f1f9ecd5447406ba654469bb65d7c2e4197108696f43b9"),
    (8, "117:5-121:6",
     "5e3d40784bcda8b337be4499c14eebbbe0ec961aa77f5192573a6e453d5a3e05"),
    (9, "123:5-123:60",
     "44d2b6667ecd073a45ce368409954fb6a26a221cfaefeb896d634bc792f04c6c"),
)
_LUMA = (
    "57875634dad16eaba6458505baa639f2305117a51cf11de79dcb1054a501869b",
    ((20, (3, "e0", 0, 1), "92:59-92:63",
      "baf788e70eb3b6dafeffc7725880573b69de069457fb2ad7e25cfa6d299cb4b0"),
     (20, (4, "e0", 0, 1), "93:59-93:63",
      "1a4162817a5532a65896b2764fefa07ff32fe572836abc2fbbf9f5550ce44b2e"),
     (20, (8, "e0", 0, 1), "98:39-98:43",
      "521ac083e151546cf68be0b73f2a9caac43d6891f87c9796c105a0ef7053cea7")),
)

# owner id/name, texture path/span/hash, division path/span/hash, numerator
# span/hash, and divisor span/hash. The generated JavaScript materializes each
# numerator as a Float32Array-backed vec2 before dividing by textureSize.
_TEXTURE_COORDINATE_MATERIALIZATIONS = (
    (18, "colorDefaultEmboss",
     (21, "s1", "s0", "e0", 0, 0), "48:26-48:150",
     "f3ce35fb231157b9ca62f010d3d7d09edcecca4b161153f7713b424557a0bfc1",
     (21, "s1", "s0", "e0", 0, 0, 1), "48:46-48:149",
     "22dce34574b9cdfe01698544e7fda5c6437fe1268088cd3320185dc344d405b2",
     "48:46-48:115",
     "ad823505842d002a37dfff8cf6e7cdec72c506587205ecb7d255acfaad8bd6a8",
     "48:119-48:149",
     "e915dc40cae7d24052209fa49957d3c3cb7553393a82a25a41cec35891066afc"),
    (19, "colorGeneralEmboss",
     (24, "s1", "s3", "e0", 0, 0), "80:26-80:125",
     "2d78f3235be6b0be4196401e787924f48901af84cf9a1ec3fab77fbc05dbf115",
     (24, "s1", "s3", "e0", 0, 0, 1), "80:46-80:124",
     "23e4e31571c59dcacb622bfa5a6006b197900871b96bc0ce799ce5868e9d1346",
     "80:46-80:90",
     "ef74b96f682be5d79cafe9d0ea9c7fd222001ab7fa557f0359212f3b33bbb057",
     "80:94-80:124",
     "f5a7c7db170e1bc073de73d7a8c63a9ca5a45bb8784302c2800d0e9bf01b0cda"),
)

_PROFILE_SHA256 = "cea6ab0b8421b4136956dc62ad7a7e608369e694ab345058e2b610345f6e26a8"


@dataclass(frozen=True, slots=True)
class EmbossTableProof:
    _candidate: TypedProgram
    owner: TypedFunction
    symbol_id: int
    symbol_name: str
    array_type: str
    native_element_type: str
    declaration_statement_index: int
    declaration_statement: TypedStatement
    declaration: TypedExpression
    literal_store_statement_indices: tuple[int, ...]
    literal_store_statements: tuple[TypedStatement, ...]
    literal_stores: tuple[TypedExpression, ...]
    loop_statement_index: int
    loop_statement: TypedStatement
    loop_body: TypedStatement
    induction_symbol_id: int
    dynamic_read: TypedExpression
    payload_bytes: int

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        return (self.owner, self.declaration_statement, self.declaration,
                *self.literal_store_statements, *self.literal_stores,
                self.loop_statement, self.loop_body, self.dynamic_read)

    @property
    def declaration_span(self):
        return self.declaration.span

    @property
    def literal_store_indices(self) -> tuple[int, ...]:
        return tuple(range(9))

    @property
    def literal_store_index_spans(self) -> tuple[object, ...]:
        return tuple(store.children[0].span for store in self.literal_stores)

    @property
    def read_spans(self) -> tuple[object, ...]:
        return (self.dynamic_read.span,)


@dataclass(frozen=True, slots=True)
class EmbossColorStyleProof:
    _candidate: TypedProgram
    tables: tuple[EmbossTableProof, ...]
    equalities: tuple[TypedExpression, ...]
    reductions: tuple[TypedExpression, ...]
    full_frame_declaration: TypedExpression
    full_frame_conjunction: TypedExpression
    color_texel_declaration: TypedExpression
    color_texel_conditional: TypedExpression
    texture_coordinate_divisions: tuple[TypedExpression, ...]
    texture_coordinate_numerators: tuple[TypedExpression, ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = []
        for table in self.tables:
            values.extend(table.consumed_objects)
        values.extend((self.full_frame_declaration, self.full_frame_conjunction,
                       *self.reductions, *self.equalities,
                       self.color_texel_declaration, self.color_texel_conditional,
                       *self.texture_coordinate_divisions,
                       *self.texture_coordinate_numerators))
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = (
    "PROFILE", "EMBOSS_KEY", "EmbossTableProof", "EmbossColorStyleProof",
    "authenticate_emboss_color_style", "apply_emboss_color_style",
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _profile_tuple() -> tuple[object, ...]:
    return (PROFILE, EMBOSS_KEY, _RAW_BYTES, _RAW_SHA256, _RAW_IR_SHA256,
            _NORMALIZED_BYTES, _NORMALIZED_SHA256, _NORMALIZED_IR_SHA256,
            _FUNCTIONS_SHA256, _DECLARATIONS_SHA256, _WHOLE_SHA256,
            _INTERFACE_SHA256, _DEFINES, _RESOURCES, _LOOP_PROOF, _FUNCTIONS,
            tuple(sorted(_CALL_GRAPH.items())), _REACHABLE_FROM_MAIN,
            _TABLES, _BOOLEAN_NODES, _MAIN_ROUTE, _LUMA,
            _TEXTURE_COORDINATE_MATERIALIZATIONS)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression,
                     parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement,
                    path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, expression_path in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, expression_path, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _reachable(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    pending = ["main"]
    visited: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        pending.extend(graph.get(name, ()))
    return tuple(sorted(visited))


def authenticate_emboss_color_style(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> EmbossColorStyleProof:
    """Authenticate Emboss and return only objects owned by ``program``."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != EMBOSS_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if (len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or _sha(program.raw_source) != _RAW_IR_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or _sha(program.source) != _NORMALIZED_IR_SHA256
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _sha(program.declarations) != _DECLARATIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256
            or defines != _DEFINES
            or program.body_status != "analyzed"):
        raise _fail("source, define, function, program, or interface mismatch")
    if (program.structs != () or program.uniform_blocks != ()
            or any(getattr(program, field, None) is not None
                   for field in _OPTIONAL_PROOF_FIELDS)):
        raise _fail("unrelated structural or proof carrier is present")

    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != _RESOURCES):
        raise _fail("resource signature mismatch")
    loop = program.counted_loop_proof
    if (loop is None or
            (loop.loop_count, loop.unproved_loop_count,
             loop.max_effective_depth, loop.max_lexical_product,
             loop.entrypoint_charge, loop.call_graph_acyclic) != _LOOP_PROOF):
        raise _fail("loop-program proof mismatch")

    actual_functions = tuple(
        (item.id, item.name, item.return_type.display(),
         tuple((parameter.id, parameter.name, parameter.type.display())
               for parameter in item.parameters),
         len(item.body), _span(item))
        for item in program.functions)
    if actual_functions != _FUNCTIONS:
        raise _fail("function census mismatch")

    located: list[tuple[TypedFunction, TypedExpression,
                       TypedExpression | None, tuple[object, ...],
                       tuple[TypedStatement, ...]]] = []
    graph: dict[str, tuple[str, ...]] = {}
    names = {item.id: item.name for item in program.functions}
    for function in program.functions:
        function_nodes = []
        for index, statement in enumerate(function.body):
            function_nodes.extend(_walk_statement(statement, (index,)))
        located.extend((function, *record) for record in function_nodes)
        graph[function.name] = tuple(sorted({
            names[item.signature_id] for item, _, _, _ in function_nodes
            if item.kind == "call" and item.signature_id in names
        }))
    if graph != _CALL_GRAPH or _reachable(graph) != _REACHABLE_FROM_MAIN:
        raise _fail("call graph or STYLE=0 reachability mismatch")

    if (len(program.declarations) != 10
            or program.declarations[-1].symbol.id != 10
            or program.declarations[-1].symbol.name != "LUMA"
            or program.declarations[-1].symbol.storage != "const"
            or program.declarations[-1].type.display() != "vec3"
            or _span(program.declarations[-1]) != "19:1-19:48"
            or _sha(program.declarations[-1]) != _LUMA[0]):
        raise _fail("global LUMA declaration mismatch")
    luma_records = tuple(
        (function.id, path, _span(item), _sha(item))
        for function, item, _, path, _ in located
        if item.kind == "id" and item.symbol_id == 10)
    if luma_records != _LUMA[1]:
        raise _fail("global LUMA read topology mismatch")

    by_id = {item.id: item for item in program.functions}
    tables: list[EmbossTableProof] = []
    for expected in _TABLES:
        (owner_id, owner_name, body_count, symbol_id, symbol_name, array_type,
         native_type, declaration_index, declaration_span, declaration_hash,
         declaration_statement_hash, store_spans, stores_hash, rhs_hash,
         targets_hash, loop_index, loop_span, loop_hash, loop_body_hash,
         induction_id, loop_body_count, read_span, read_hash, read_path,
         payload_bytes) = expected
        owner = by_id.get(owner_id)
        if (owner is None or owner.name != owner_name
                or len(owner.body) != body_count):
            raise _fail("table owner mismatch")
        declaration_statement = owner.body[declaration_index]
        if (declaration_statement.kind != "decl"
                or len(declaration_statement.expressions) != 1
                or declaration_statement.children
                or _sha(declaration_statement) != declaration_statement_hash):
            raise _fail("table declaration statement mismatch")
        declaration = declaration_statement.expressions[0]
        if (declaration.kind != "declaration" or declaration.children
                or declaration.symbol is None
                or declaration.symbol_id != symbol_id
                or declaration.symbol.name != symbol_name
                or declaration.type.display() != array_type
                or _span(declaration) != declaration_span
                or _sha(declaration) != declaration_hash):
            raise _fail("table declaration mismatch")

        store_indices = tuple(range(declaration_index + 1,
                                    declaration_index + 10))
        store_statements = tuple(owner.body[index] for index in store_indices)
        if (tuple(_span(item) for item in store_statements) != store_spans
                or any(item.kind != "expr" or len(item.expressions) != 1
                       or item.children for item in store_statements)):
            raise _fail("table literal-store statement mismatch")
        stores = tuple(item.expressions[0] for item in store_statements)
        targets = tuple(item.children[0] for item in stores
                        if len(item.children) == 2)
        rhs = tuple(item.children[1] for item in stores
                    if len(item.children) == 2)
        if (len(targets) != 9 or len(rhs) != 9
                or _sha(stores) != stores_hash or _sha(rhs) != rhs_hash
                or _sha(targets) != targets_hash
                or any(item.kind != "assign" or item.operator != "="
                       for item in stores)
                or any(target.kind != "index" or len(target.children) != 2
                       or target.children[0].kind != "id"
                       or target.children[0].symbol_id != symbol_id
                       or target.children[1].kind != "literal"
                       for target in targets)
                or tuple(target.children[1].literal_value
                         for target in targets) != tuple(range(9))):
            raise _fail("table literal-store payload, order, or target mismatch")

        loop_statement = owner.body[loop_index]
        if (loop_statement.kind != "for" or loop_statement.loop_proof is None
                or _span(loop_statement) != loop_span
                or _sha(loop_statement) != loop_hash
                or len(loop_statement.children) != 2
                or loop_statement.children[1].kind != "block"):
            raise _fail("table loop statement mismatch")
        loop_proof = loop_statement.loop_proof
        loop_body = loop_statement.children[1]
        if ((loop_proof.induction_symbol_id, loop_proof.start_value,
             loop_proof.bound_value, loop_proof.comparison,
             loop_proof.update, loop_proof.trip_count)
                != (induction_id, 0, 9, "<", "++", 9)
                or len(loop_body.children) != loop_body_count
                or _sha(loop_body) != loop_body_hash):
            raise _fail("table loop induction, bound, or body mismatch")

        refs = [(function, item, parent, path, chain)
                for function, item, parent, path, chain in located
                if item.kind == "id" and item.symbol_id == symbol_id]
        dynamic_reads = []
        for function, item, parent, path, chain in located:
            if (item.kind != "index" or len(item.children) != 2
                    or item.children[0].kind != "id"
                    or item.children[0].symbol_id != symbol_id
                    or item.children[1].kind != "id"
                    or item.children[1].symbol_id != induction_id):
                continue
            dynamic_reads.append((function, item, parent, path, chain))
        if (len(refs) != 10 or len(dynamic_reads) != 1
                or any(function is not owner for function, *_ in refs)):
            raise _fail("table reference count, ownership, alias, or escape mismatch")
        function, dynamic_read, _, actual_path, chain = dynamic_reads[0]
        if (function is not owner or actual_path != read_path
                or _span(dynamic_read) != read_span
                or _sha(dynamic_read) != read_hash
                or loop_statement not in chain or loop_body not in chain
                or dynamic_read.children[0] is not refs[-1][1]
                or any(target.children[0] is not ref[1]
                       for target, ref in zip(targets, refs[:9]))):
            raise _fail("table dynamic-read identity or owner-loop route mismatch")

        tables.append(EmbossTableProof(
            program, owner, symbol_id, symbol_name, array_type, native_type,
            declaration_index, declaration_statement, declaration,
            store_indices, store_statements, stores, loop_index, loop_statement,
            loop_body, induction_id, dynamic_read, payload_bytes))

    if sum(item.payload_bytes for item in tables) != 288:
        raise _fail("table payload mismatch")

    materialization_records = []
    texture_coordinate_divisions = []
    texture_coordinate_numerators = []
    for expected in _TEXTURE_COORDINATE_MATERIALIZATIONS:
        (owner_id, owner_name, texture_path, texture_span, texture_hash,
         division_path, division_span, division_hash, numerator_span,
         numerator_hash, divisor_span, divisor_hash) = expected
        matches = [
            (function, item, parent, path)
            for function, item, parent, path, _ in located
            if function.id == owner_id and path == texture_path]
        if len(matches) != 1:
            raise _fail("texture-coordinate owner or path mismatch")
        owner, texture, _, actual_texture_path = matches[0]
        if (owner.name != owner_name or owner.name not in _REACHABLE_FROM_MAIN
                or texture.kind != "builtin" or texture.callee != "texture"
                or texture.type.display() != "vec4"
                or len(texture.children) != 2
                or texture.children[0].kind != "id"
                or texture.children[0].symbol_id != 3
                or _span(texture) != texture_span
                or _sha(texture) != texture_hash):
            raise _fail("reachable texture-coordinate call mismatch")
        division = texture.children[1]
        if (division.kind != "binary" or division.operator != "/"
                or division.type.display() != "vec2"
                or len(division.children) != 2
                or _span(division) != division_span
                or _sha(division) != division_hash):
            raise _fail("texture-coordinate division mismatch")
        division_matches = [
            (function, item, parent, path)
            for function, item, parent, path, _ in located
            if item is division]
        if (division_matches != [(owner, division, texture, division_path)]
                or division_path != (*actual_texture_path, 1)):
            raise _fail("texture-coordinate division parent identity mismatch")
        numerator, divisor = division.children
        if (numerator.kind != "binary" or numerator.operator != "-"
                or numerator.type.display() != "vec2"
                or _span(numerator) != numerator_span
                or _sha(numerator) != numerator_hash
                or divisor.kind != "construct"
                or divisor.type.display() != "vec2"
                or _span(divisor) != divisor_span
                or _sha(divisor) != divisor_hash):
            raise _fail("texture-coordinate numerator or divisor mismatch")
        materialization_records.append((
            owner.id, owner.name, actual_texture_path, _span(texture),
            _sha(texture), division_path, _span(division), _sha(division),
            _span(numerator), _sha(numerator), _span(divisor), _sha(divisor)))
        texture_coordinate_divisions.append(division)
        texture_coordinate_numerators.append(numerator)
    if tuple(materialization_records) != _TEXTURE_COORDINATE_MATERIALIZATIONS:
        raise _fail("texture-coordinate materialization census mismatch")
    reachable_color_textures = tuple(
        item for function, item, _, _, _ in located
        if function.name in {"colorDefaultEmboss", "colorGeneralEmboss"}
        and item.kind == "builtin" and item.callee == "texture")
    if tuple(item.children[1] for item in reachable_color_textures) != tuple(
            texture_coordinate_divisions):
        raise _fail("texture-coordinate materialization cardinality mismatch")

    main = by_id[21]
    if tuple((index, _span(main.body[index]), _sha(main.body[index]))
             for index, _, _ in _MAIN_ROUTE) != _MAIN_ROUTE:
        raise _fail("main dispatch, branch, clamp, or alpha route mismatch")
    full_frame_statement = main.body[5]
    color_texel_statement = main.body[6]
    if (len(full_frame_statement.expressions) != 1
            or len(color_texel_statement.expressions) != 1):
        raise _fail("fullFrame declaration topology mismatch")
    full_frame_declaration = full_frame_statement.expressions[0]
    color_texel_declaration = color_texel_statement.expressions[0]
    if (full_frame_declaration.kind != "declaration"
            or full_frame_declaration.symbol_id != 56
            or full_frame_declaration.symbol is None
            or full_frame_declaration.symbol.name != "fullFrame"
            or len(full_frame_declaration.children) != 1
            or color_texel_declaration.kind != "declaration"
            or color_texel_declaration.symbol_id != 57
            or color_texel_declaration.symbol is None
            or color_texel_declaration.symbol.name != "colorTexelSize"
            or len(color_texel_declaration.children) != 1):
        raise _fail("fullFrame or colorTexelSize declaration mismatch")
    conjunction = full_frame_declaration.children[0]
    conditional = color_texel_declaration.children[0]
    if (conjunction.kind != "binary" or conjunction.operator != "&&"
            or conjunction.type.display() != "bool"
            or len(conjunction.children) != 2
            or conditional.kind != "conditional"
            or conditional.type.display() != "vec2"
            or len(conditional.children) != 3
            or conditional.children[0].kind != "id"
            or conditional.children[0].symbol_id != 56):
        raise _fail("fullFrame conjunction or sole consumer mismatch")

    boolean_records = []
    boolean_objects = []
    for function, item, parent, path, _ in located:
        display = item.type.display()
        if display.startswith("bvec") or (
                item.kind == "builtin" and item.callee in {"equal", "all"}):
            boolean_records.append((
                path, _span(item), item.kind, display, item.callee,
                item.signature_id,
                None if parent is None else
                (parent.kind, parent.callee, parent.operator),
                _sha(item),
                tuple((child.type.display(), _sha(child))
                      for child in item.children),
            ))
            boolean_objects.append(item)
    if tuple(boolean_records) != _BOOLEAN_NODES:
        raise _fail("equal/all bvec2 closure mismatch")
    reduction0, equality0, reduction1, equality1 = boolean_objects
    reductions = (reduction0, reduction1)
    equalities = (equality0, equality1)
    if (conjunction.children != reductions
            or any(reduction.children != (equality,)
                   for equality, reduction in zip(equalities, reductions))
            or tuple((child.symbol_id if child.kind == "id" else None)
                     for equality in equalities for child in equality.children)
            != (1, None, 2, 52)):
        raise _fail("equal/all parent identity or operand route mismatch")

    full_frame_reads = [item for _, item, _, _, _ in located
                        if item.kind == "id" and item.symbol_id == 56]
    if full_frame_reads != [conditional.children[0]]:
        raise _fail("fullFrame use count or consumer identity mismatch")

    proof = EmbossColorStyleProof(
        program, tuple(tables), equalities, reductions,
        full_frame_declaration, conjunction,
        color_texel_declaration, conditional,
        tuple(texture_coordinate_divisions),
        tuple(texture_coordinate_numerators))
    if (len(proof.tables) != 4 or len(proof.equalities) != 2
            or len(proof.reductions) != 2
            or len(proof.texture_coordinate_divisions) != 2
            or len(proof.texture_coordinate_numerators) != 2
            or any(division.children[0] is not numerator
                   for division, numerator in zip(
                       proof.texture_coordinate_divisions,
                       proof.texture_coordinate_numerators))
            or len({id(item) for item in proof.consumed_objects})
            != len(proof.consumed_objects)):
        raise _fail("candidate ownership or consumed-object uniqueness mismatch")
    return proof


def apply_emboss_color_style(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    authenticate_emboss_color_style(program, source_hash, profile)
    return program
