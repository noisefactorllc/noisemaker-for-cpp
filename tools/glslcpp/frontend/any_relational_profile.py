"""Exact ``any`` over lane-wise relational closures profile (heightmap3d, renderLit3d).

This module does not add a general boolean-vector, relational, or reduction
capability. It authenticates the two corpus programs whose four
``any(<relational>(<vector>, <vector>))`` trees may be lowered:

- ``synth3d/heightmap3d:precompute`` -- ``any(lessThan(ivec3, ivec3))`` and
  ``any(greaterThanEqual(ivec3, ivec3))`` (the density bounds check), plus
  ``all(greaterThanEqual(ivec2, ivec2))`` and ``all(lessThan(ivec2, ivec2))``
  (the terrain bounds check).
- ``render/renderLit3d:renderLit3d`` -- ``any(lessThan(vec3, vec3))`` and
  ``any(greaterThan(vec3, vec3))`` (the march volume-exit check).

The returned candidate-owned IR objects are consumed independently by the
validator and the emitter -- the same node-identity pattern used by Waves'
``any(notEqual(vec2, vec2))`` closure (``waves_any_notequal_profile.py``),
Extrude's ``all(lessThanEqual(vec2, vec2))`` closure, and the Attractor
agent's ``any(isnan(vec3))`` closure.

Each ``bvec2``/``bvec3`` intermediate produced by a relational is consumed
immediately by its exact parent reduction (``any`` or ``all``). It is never
declared, stored, returned, subscripted, aggregated, or otherwise escaped,
and this module proves that rather than assuming it.

Deliberately independent of, and composed with, the per-program loop-proof
and struct-frontier carriers: ``renderLit3d`` carries the frozen
``source-global-literal-int`` march bound and the ``IsoHit`` struct-frontier
record, both attached by key before this authentication runs, so its
function/whole digests are frozen on the seed-attached post-proof tree the
validator authenticates (``heightmap3d``'s digests are frozen on the
analyzer's own tree). Neither carrier's identity is changed here, and this
module fails closed if the optional proof fields it pins absent ever appear.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "any-relational-admission-v1"
HEIGHTMAP_KEY = "synth3d/heightmap3d:precompute"
RENDERLIT_KEY = "render/renderLit3d:renderLit3d"
ANY_RELATIONAL_KEYS = (HEIGHTMAP_KEY, RENDERLIT_KEY)

# Every census callee: an extra reduction or relational site anywhere in a
# key's program, beyond the exact nodes below, is a hard failure.
_CENSUS_CALLEES = frozenset({
    "any", "notEqual", "lessThan", "greaterThan", "greaterThanEqual",
    "lessThanEqual", "equal", "all"})


@dataclass(frozen=True, slots=True)
class AnyRelationalRecord:
    """Frozen per-key identity. Nothing outside these facts may be lowered."""

    key: str
    raw_bytes: int
    raw_sha256: str
    normalized_bytes: int
    normalized_sha256: str
    functions_sha256: str
    whole_sha256: str
    interface_sha256: str
    main_id: int
    main_span: str
    main_body_len: int
    function_count: int
    loop_proof: tuple[int, int, int, int, int, bool]
    resources: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], bool, bool]
    struct_names: tuple[str, ...]
    # (callee, path, span, result type, node sha, parent kind,
    #  child type tuple, child sha tuple), in source order.
    nodes: tuple[tuple, ...]
    # The exact ancestor chain (kinds, spans) of each ``any`` node.
    chains: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]


_HEIGHTMAP = AnyRelationalRecord(
    key=HEIGHTMAP_KEY,
    raw_bytes=3221,
    raw_sha256="5048bda8ed7006354d5b2492a65a8ac7064d7ab0c3c74bd5d9f989ff4c3ba29b",
    normalized_bytes=2280,
    normalized_sha256=(
        "089eabe88c9a71e1bf3cac8ed7612d57b6f9ee45f07187040e9f0ff2a722c5f4"),
    functions_sha256=(
        "d4cef966c334a79c21787609f2e917d76f0eded2b746f7117c0788fe8f697df6"),
    whole_sha256=(
        "88880bdd5d3a93f67c9956f018de48d3fd29ddb476bfee7d999d47f9887d3323"),
    interface_sha256=(
        "4e25e4690eab6192cd98624e2df56ffb0d6ccd04006227861e7009ac4d673ba7"),
    main_id=20,
    main_span="59:1-77:2",
    main_body_len=11,
    function_count=7,
    loop_proof=(0, 0, 0, 0, 0, True),
    resources=(
        ("heightTex", "tex", "volumeSize", "heightScale", "baseHeight",
         "aspect", "aspectInv"),
        ("heightTex", "tex"),
        ("fragColor", "geoOut"), True, False),
    struct_names=(),
    nodes=(
        ("any", (0, "e0", 0), "55:9-55:35", "bool",
         "a33b04b156bfe6f613f5543054429c7e26e93326787dad77db76610b1f4b83a9",
         "binary", ("bvec3",),
         ("334a578bd0b2fa229246816f47a5178e1a44b01beadcd15726478c09afac9f22",)),
        ("lessThan", (0, "e0", 0, 0), "55:13-55:34", "bvec3",
         "334a578bd0b2fa229246816f47a5178e1a44b01beadcd15726478c09afac9f22",
         "builtin", ("ivec3", "ivec3"),
         ("869c5d40aa1e2b6e9a114a7071b6ac2096a7f80b755ca23f670ab196fdc84b83",
          "dbdb2ca6e268a5248ffaeb54aefb476867cd4619011306283e083afd0f3a7d25")),
        ("any", (0, "e0", 1), "55:39-55:82", "bool",
         "f622d30ea612a31f10e47aabc3f691484aa96455034b3c56870f2187186f4296",
         "binary", ("bvec3",),
         ("e4febce98fcc8ac8fcb5fb8fb91c4677995d67ae53e0fcd4a36ebeb0a25f8448",)),
        ("greaterThanEqual", (0, "e0", 1, 0), "55:43-55:81", "bvec3",
         "e4febce98fcc8ac8fcb5fb8fb91c4677995d67ae53e0fcd4a36ebeb0a25f8448",
         "builtin", ("ivec3", "ivec3"),
         ("715cbce64478b7c976c34c3fc677fbd83ee8a65e5de4784d72283420f6b21214",
          "76c675a54d33deadb4ecc375dac8b57ea2a8ba02a93e25fdd4f3bb4804e83bd5")),
        ("all", (1, "e0", 0), "39:12-39:50", "bool",
         "0f0bfd3d87a4243c3c00d2f28b7df753e016286b049f4131cb0a4d0f16313fb0",
         "binary", ("bvec2",),
         ("3e54db6d11c1c1354f3dfa82ed57eee3841e8f9fa5bffdf6c647465674b21e68",)),
        ("greaterThanEqual", (1, "e0", 0, 0), "39:16-39:49", "bvec2",
         "3e54db6d11c1c1354f3dfa82ed57eee3841e8f9fa5bffdf6c647465674b21e68",
         "builtin", ("ivec2", "ivec2"),
         ("7024bd4b14dee1b03b861224749027b3c495fb119dbfa646716bd16d861238bf",
          "296311a9508b65add7bf3799f60de9c725253a9af741302edb5abd24d3d9a535")),
        ("all", (1, "e0", 1), "39:54-39:89", "bool",
         "707d1c240b9d777c0274506edc5a04f37f16e296b98c5b707966850572835ca9",
         "binary", ("bvec2",),
         ("7b2de3be52f4f7497701d098e22600683f919c6b017dc1cbdc724fcdd3b4eb9a",)),
        ("lessThan", (1, "e0", 1, 0), "39:58-39:88", "bvec2",
         "7b2de3be52f4f7497701d098e22600683f919c6b017dc1cbdc724fcdd3b4eb9a",
         "builtin", ("ivec2", "ivec2"),
         ("04bc61380279fe7d994a05ca4dce1ed377bebd7661f5f3405ba59deae791bbf1",
          "c7f834a5cc40a68562926c19a622844d90d3529434b138628c124427ecfadd69")),
    ),
    chains=(
        (("if",), ("55:5-55:95",)),
        (("if",), ("55:5-55:95",)),
        (("return",), ("39:5-39:90",)),
        (("return",), ("39:5-39:90",)),
    ),
)

_RENDERLIT = AnyRelationalRecord(
    key=RENDERLIT_KEY,
    raw_bytes=12406,
    raw_sha256=(
        "ea309e7e9c4bcb13fd96bf05f0e587bfd25557b7184872b32aabc160df49b627"),
    normalized_bytes=9486,
    normalized_sha256=(
        "436cdf22da60272b948b145b0dabc113d65bc1b9006659517e07dcd80ba48b62"),
    functions_sha256=(
        "d6c4f6bbf5a4cd19ca2006fd1b997fde798c280a51039246be9e1c423cc41e38"),
    whole_sha256=(
        "2688f3be3bed47ff1facee122dd2e7da11501f21044bda9206c847efaf077ac0"),
    interface_sha256=(
        "e3f61fcd73cd0441cf76d4a119f618bd6fad0515ec6b588d074ccc2751e87b86"),
    main_id=65,
    main_span="323:1-393:2",
    main_body_len=27,
    function_count=12,
    loop_proof=(2, 0, 2, 2048, 2304, True),
    resources=(
        ("resolution", "tileOffset", "fullResolution", "time", "threshold",
         "invert", "volumeSize", "shape", "orbitSpeed", "cameraPosition",
         "bgColor", "bgAlpha", "volumeCache", "lightDirection", "diffuseColor",
         "diffuseIntensity", "specularColor", "specularIntensity", "shininess",
         "ambientColor", "rimIntensity", "rimPower"),
        ("volumeCache",),
        ("fragColor", "geoOut"), True, False),
    struct_names=("IsoHit",),
    nodes=(
        ("any", (13, "s1", "s3", "s0", "s0", "e0", 0), "236:17-236:45", "bool",
         "23c5f1bbe68dcf11aeadfe3e8d220be37fc4c1949fa8f001b4393caed88e843f",
         "binary", ("bvec3",),
         ("df58ee20f1b4f544deef847bdbee398b6257b79fe5ceeaf5c345e58e9fcc8113",)),
        ("lessThan", (13, "s1", "s3", "s0", "s0", "e0", 0, 0), "236:21-236:44",
         "bvec3",
         "df58ee20f1b4f544deef847bdbee398b6257b79fe5ceeaf5c345e58e9fcc8113",
         "builtin", ("vec3", "vec3"),
         ("503075593dc8c323d9a8bd1505f431070eb40730c67b094c5a7de5dc199cb720",
          "d1fb4f48d71c3fc559b43cf470a6b121aa6699d7654dc34102a2d30f2f4bd415")),
        ("any", (13, "s1", "s3", "s0", "s0", "e0", 1), "236:49-236:79", "bool",
         "31e61bb38f041a3f42ed3b84a8f9591eeec4399a4813c835eb12a5aa5e242066",
         "binary", ("bvec3",),
         ("60a239b3be4eb154d6dd10ef53f7c00921457843d3d1a400744ed98ef69d43c3",)),
        ("greaterThan", (13, "s1", "s3", "s0", "s0", "e0", 1, 0),
         "236:53-236:78", "bvec3",
         "60a239b3be4eb154d6dd10ef53f7c00921457843d3d1a400744ed98ef69d43c3",
         "builtin", ("vec3", "vec3"),
         ("9c1d047ceee2e4cd125c54634a22aab8c8d1aebb3a6195128cc902a1a7806894",
          "3b4efd2a4d420f0535442efd5426d1cf983c5fccc8c734483d61f2fa4f86859e")),
    ),
    chains=(
        (("for", "block", "if", "block", "if"),
         ("227:5-274:6", "227:41-274:6", "234:9-244:10", "234:25-239:10",
          "236:13-238:14")),
        (("for", "block", "if", "block", "if"),
         ("227:5-274:6", "227:41-274:6", "234:9-244:10", "234:25-239:10",
          "236:13-238:14")),
    ),
)

_RECORDS: dict[str, AnyRelationalRecord] = {
    HEIGHTMAP_KEY: _HEIGHTMAP, RENDERLIT_KEY: _RENDERLIT}

# Self-integrity: the frozen record reprs must survive any accidental edit.
_RECORD_SHA256 = {
    HEIGHTMAP_KEY: "e62afdfb18fcd82f902170dfcd2dddddf5d73f37c361e34d8f030c80e536a01e",
    RENDERLIT_KEY: "2653509f034c4e3116b885b73764b2d681d4ec6dcdbc17d59198f0e2909cb6f5",
}

_ANY_SIGNATURE_ID = -4
_ALL_SIGNATURE_ID = -3
_REDUCTION_CALLEES = frozenset({"any", "all"})
_RELATIONAL_SIGNATURE_IDS = {
    "lessThan": -23, "greaterThan": -50, "greaterThanEqual": -20,
    "lessThanEqual": -24, "notEqual": -32, "equal": -22}

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class AnyRelationalProof:
    key: str
    reductions: tuple[TypedExpression, ...]
    relationals: tuple[TypedExpression, ...]
    chains: tuple[tuple[TypedStatement, ...], ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [self.key, *self.reductions, *self.relationals]
        for chain in self.chains:
            values.extend(chain)
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = (
    "PROFILE", "HEIGHTMAP_KEY", "RENDERLIT_KEY", "ANY_RELATIONAL_KEYS",
    "AnyRelationalProof",
    "authenticate_any_relational_admission",
    "apply_any_relational_admission",
    "is_authenticated_reduction_node", "is_authenticated_relational_node")


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


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _record_sha(record: AnyRelationalRecord) -> str:
    return _sha((record.key, record.raw_bytes, record.raw_sha256,
                 record.normalized_bytes, record.normalized_sha256,
                 record.functions_sha256, record.whole_sha256,
                 record.interface_sha256, record.main_id, record.main_span,
                 record.main_body_len, record.function_count, record.loop_proof,
                 record.resources, record.struct_names, record.nodes,
                 record.chains))


def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, epath in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, epath, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def authenticate_any_relational_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> AnyRelationalProof:
    """Authenticate a frozen record and return only candidate-owned objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    record = _RECORDS.get(program.key)
    if record is None:
        raise _fail(f"no frozen record for {program.key}")
    if _record_sha(record) != _RECORD_SHA256[record.key]:
        raise _fail("internal frozen record mismatch")
    if source_hash != record.raw_sha256:
        raise _fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if (len(raw) != record.raw_bytes
            or hashlib.sha256(raw).hexdigest() != record.raw_sha256
            or len(normalized) != record.normalized_bytes
            or hashlib.sha256(normalized).hexdigest() != record.normalized_sha256
            or defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != record.functions_sha256
            or _whole(program) != record.whole_sha256
            or _interface(program) != record.interface_sha256):
        raise _fail("source, define, function, whole-program, or interface mismatch")

    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    actual_structs = tuple(item.name for item in program.structs)
    if actual_structs != record.struct_names or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    proof = program.counted_loop_proof
    if (proof is None or
            (proof.loop_count, proof.unproved_loop_count,
             proof.max_effective_depth, proof.max_lexical_product,
             proof.entrypoint_charge, proof.call_graph_acyclic)
            != record.loop_proof):
        raise _fail("loop or call graph profile mismatch")

    if ((program.resources.uniforms, program.resources.samplers,
         program.resources.outputs, program.resources.uses_texture,
         program.resources.uses_derivatives) != record.resources):
        raise _fail("resource or binding signature mismatch")

    if len(program.functions) != record.function_count:
        raise _fail("function cardinality mismatch")
    main = next((item for item in program.functions
                 if item.id == record.main_id), None)
    if (main is None or main.name != "main"
            or main.return_type.display() != "void"
            or len(main.parameters) != 0
            or len(main.body) != record.main_body_len
            or _span(main) != record.main_span):
        raise _fail("main identity mismatch")

    # Census the WHOLE program: an extra reduction or relational site anywhere
    # else, or any bvec-typed value that is not exactly one of the pinned
    # relational results, is a hard failure, not an unnoticed extra.
    located: list[tuple[str, tuple[object, ...], TypedExpression,
                        TypedExpression | None, tuple[TypedStatement, ...]]] = []
    bvec_nodes: list[TypedExpression] = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                display = None if item.type is None else item.type.display()
                if display is not None and display.startswith("bvec"):
                    bvec_nodes.append(item)
                if item.kind == "builtin" and item.callee in _CENSUS_CALLEES:
                    located.append((item.callee, path, item, parent, chain))

    if len(located) != len(record.nodes):
        raise _fail(f"closure site cardinality mismatch: {len(located)}")

    actual = tuple(
        (callee, path, _span(item),
         "" if item.type is None else item.type.display(), _sha(item),
         "None" if parent is None else parent.kind,
         tuple("" if child.type is None else child.type.display()
               for child in item.children),
         tuple(_sha(child) for child in item.children))
        for callee, path, item, parent, _ in located)
    if actual != record.nodes:
        raise _fail("closure node identity mismatch")

    expected_signature_ids = (
        _ANY_SIGNATURE_ID if node[0] == "any"
        else _ALL_SIGNATURE_ID if node[0] == "all"
        else _RELATIONAL_SIGNATURE_IDS[node[0]] for node in record.nodes)
    for (callee, _, item, _, _), expected_signature in zip(
            located, expected_signature_ids):
        if item.signature_id != expected_signature:
            raise _fail("closure node signature mismatch")

    reductions = tuple(item for callee, _, item, _, _ in located
                       if callee in _REDUCTION_CALLEES)
    relationals = tuple(item for callee, _, item, _, _ in located
                        if callee not in _REDUCTION_CALLEES)
    if len(reductions) * 2 != len(located) or len(relationals) != len(located) // 2:
        raise _fail("closure shape mismatch")
    # Each relational is consumed immediately, by identity, by exactly one
    # pinned `any`; and the pinned bvec3 census is exactly the relationals.
    for node_row, any_node in zip(record.nodes[0::2], reductions):
        child_sha = node_row[7][0]
        child = any_node.children[0]
        if (len(any_node.children) != 1
                or _sha(child) != child_sha
                or any(any_node.children[i] is child
                       for i in range(1, len(any_node.children)))):
            raise _fail("reduction does not immediately consume its relational")
        expected_child = next(item for item in relationals if _sha(item) == child_sha)
        if child is not expected_child:
            raise _fail("reduction does not consume its exact relational")
    if len(bvec_nodes) != len(relationals) or any(
            not any(bvec is item for item in relationals)
            for bvec in bvec_nodes):
        raise _fail("bvec3 value escapes its immediate reduction")

    # Each `any` node's single ancestor statement chain is the pinned one.
    chains: list[tuple[TypedStatement, ...]] = []
    for (callee, _, _, _, chain), expected_row in zip(
            (row for row in located if row[0] in _REDUCTION_CALLEES),
            record.chains):
        if (tuple(item.kind for item in chain) != expected_row[0]
                or tuple(_span(item) for item in chain) != expected_row[1]):
            raise _fail("closure ancestry mismatch")
        chains.append(chain)

    result = AnyRelationalProof(record.key, reductions, relationals,
                                tuple(chains))
    expected_consumed = (1 + len(reductions) + len(relationals)
                         + len({id(item) for chain in chains for item in chain}))
    if len(result.consumed_objects) != expected_consumed:
        raise _fail(
            f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def apply_any_relational_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_any_relational_admission(program, source_hash, profile)
    return program


def is_authenticated_reduction_node(
        proof: AnyRelationalProof, node: TypedExpression) -> bool:
    """True only for the exact authenticated ``any`` objects."""
    return any(node is item for item in proof.reductions)


def is_authenticated_relational_node(
        proof: AnyRelationalProof, node: TypedExpression) -> bool:
    """True only for the exact authenticated relational objects."""
    return any(node is item for item in proof.relationals)
