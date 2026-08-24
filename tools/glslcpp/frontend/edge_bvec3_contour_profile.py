"""Exact stored-bvec3 contour closure admission for Edge.

This profile authenticates one complete candidate-owned Edge program.  It does
not add ``bvec3`` or either relational builtin to the global typed vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "edge-bvec3-contour-v1"
EDGE_KEY = "filter/edge:edge"

_RAW_BYTES = 6530
_RAW_SHA256 = "841f9f547d06aace8444953f401009abd02758f9dff271097b2799424c1db5d0"
_NORMALIZED_BYTES = 5869
_NORMALIZED_SHA256 = "af95979c51c8135c5be956a4c5666897e7f622975c71e6ec63c1b4c1171d6324"
_FUNCTIONS_SHA256 = "e69b0c3401068641c9e9f724c37515a3c3055217d06be7326a9a1621a9462c85"
_WHOLE_SHA256 = "01849635b4a01ff1d14991c68c93804bff954c94c4fb18d53b7a5782cf19bc79"
_INTERFACE_SHA256 = "97e91a090b9892f5e26aefe00ebf95e2448e32ef2825f4b54fd2357425798052"
_HOST_ID = 28
_LOOP_PROOF = (2, 0, 2, 49, 56, True)
_RESOURCES = (
    ("inputTex", "kernel", "size", "renderScale", "blend", "invert",
     "channel", "threshold", "amount", "mixAmt", "level", "contourSide"),
    ("inputTex",), ("fragColor",), True, False,
)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

# Frozen verbatim from edge_frontend_probe.py.  Each bvec row is
# (path, span, kind, callee, node hash, parent kind, child types, child hashes).
_BVEC_NODES = (
    ((5, "e0"), "73:11-74:69", "declaration", None,
     "bb9c357313a708b8eba5107228d4a3dcaed90df1a5a8d2f2834e960e458d7ad2",
     None, ("bvec3",),
     ("b5e678e2e157a8038119a17d1f5fba5213b9db135d9eea12e5e381d0ac031b65",)),
    ((5, "e0", 0), "73:26-74:69", "conditional", None,
     "b5e678e2e157a8038119a17d1f5fba5213b9db135d9eea12e5e381d0ac031b65",
     "declaration", ("bool", "bvec3", "bvec3"),
     ("54358e0d18a52dab0c0d3f95ea29a7dbb8b80112b5321746f424c66d273d04d5",
      "6d1c96296c83bba0eb883161fb9a30cb65f07105a2ea20c71ef697ff2f9489ba",
      "2d68139d5652efff5ccc143e7573e7c96054538718927f4c4dcd5cb8eeb3f6bb")),
    ((5, "e0", 0, 1), "73:38-73:76", "builtin", "greaterThanEqual",
     "6d1c96296c83bba0eb883161fb9a30cb65f07105a2ea20c71ef697ff2f9489ba",
     "conditional", ("vec3", "vec3"),
     ("8b279822a0e2ae40c1418d0feacb1000bfc2e465b175725bcb580ac401a0a247",
      "a8a3687c9cfc3c3a7151e3d481b19ac07a466a5445c4ec1c0e229733f8873ea2")),
    ((5, "e0", 0, 2), "74:39-74:69", "builtin", "lessThan",
     "2d68139d5652efff5ccc143e7573e7c96054538718927f4c4dcd5cb8eeb3f6bb",
     "conditional", ("vec3", "vec3"),
     ("617c8f28eeeadd6a277ad154afc61c2b48d9ef52d1628754494d8ee348707cd1",
      "a7bb5f4ca018892478b8fab3ed8a8dfc99bc4e1acee2ae40868ea95e97e4ddd3")),
    ((6, "e0"), "75:11-85:6", "declaration", None,
     "64a9132653f16dbb431da5ea299d6f799d82f07064274dd75032a888e8a07a32",
     None, ("bvec3",),
     ("c9a30d0b0818c32aa7d365e47f2dd106489d7b1f46ff402de4badd2baef2d564",)),
    ((6, "e0", 0), "75:22-85:6", "construct", None,
     "c9a30d0b0818c32aa7d365e47f2dd106489d7b1f46ff402de4badd2baef2d564",
     "declaration", ("bool", "bool", "bool"),
     ("e1d4dc290acfaf799cf1de23e062f88b0381f9ae059033c06d80649fe358d5f7",
      "f5af3237d63066c8df74a599383d3eb32c1657905e8f9120c106bd44102beb08",
      "603d32768fbad932f77dc6e19909d110ef5fc104303c150e2862438b0932c7eb")),
    ((6, "e0", 0, 0, 0, 0), "76:9-76:21", "id", None,
     "0574ff006c093fe254fc26014ed5dc9173451c2bc10fd461f6eb1d17b87d149a",
     "swizzle", (), ()),
    ((6, "e0", 0, 1, 0, 0), "79:9-79:21", "id", None,
     "1ee29e94206bff4325d9bc81b3187eae3c552231c77940b1a18dd157685c3975",
     "swizzle", (), ()),
    ((6, "e0", 0, 2, 0, 0), "82:9-82:21", "id", None,
     "441939758b59557ea132f8e71cbf24163bd921725a807ab4a32196b8788feb15",
     "swizzle", (), ()),
    ((7, "e0", 0, 0, 0), "86:17-86:25", "id", None,
     "2d2032c1afa9eae073797679063a4c531ae4a69e9647523c59ca63b349951953",
     "swizzle", (), ()),
    ((7, "e0", 1, 0, 0), "86:41-86:49", "id", None,
     "8ce39a42ade97dcd0d978f58cbce5ee2d757e3f6daf122e6d2d564160c99e936",
     "swizzle", (), ()),
    ((7, "e0", 2, 0, 0), "86:65-86:73", "id", None,
     "6f58d7d633057e66adf03597a04572cde11880d3b17e761e87023bd03a8abdb7",
     "swizzle", (), ()),
)

# (path, span, lane, exact base symbol id)
_SWIZZLES = (
    ((6, "e0", 0, 0, 0), "76:9-76:23", "r", 40),
    ((6, "e0", 0, 1, 0), "79:9-79:23", "g", 40),
    ((6, "e0", 0, 2, 0), "82:9-82:23", "b", 40),
    ((7, "e0", 0, 0), "86:17-86:27", "r", 41),
    ((7, "e0", 1, 0), "86:41-86:51", "g", 41),
    ((7, "e0", 2, 0), "86:65-86:75", "b", 41),
)

# Canonical JavaScript evaluates this one self-referential vec3 splat as three
# sequential lane stores.  This tuple freezes the only typed assignment that
# may receive that program-scoped lowering:
# (path, statement span/hash, assignment span/hash, target/constructor/dot
# hashes, dot child hashes, and exact symbol route).
_CENTER_SPLAT = (
    (11, "s1", "s2", "s0", "s0", "e0"),
    (("if", "106:5-138:6",
      "a141ccc4ddd23d0a1e1a609a4d23b4a64961c583563271b43ea9f9b483f45d1b"),
     ("block", "109:12-138:6",
      "cd9765a3acf9745f33de7e1a36e25cc5612b5dee71bf10bdbe10ffa71f2e6f55"),
     ("if", "134:9-136:10",
      "da77d67af3e3a1815d8789edd2e936b2e31ce4cf1e0012ca843fd4c48fc7b2e9"),
     ("block", "134:22-136:10",
      "25967c4015e36abfc6afc9a84c12fbdce9e074017904af71760effd9fa06cc2a"),
     ("expr", "135:13-135:58",
      "45169d69452a16b6b723b2a32e0aba7d1442693d7ac4fe469bb7238dd3e31fb3")),
    "135:13-135:57",
    "2559b7d881b9aaf4f425d0ab9df528e000fa3279a58a31ff839e4a5aaaf51064",
    "c87f659956f8254f53e9669db05ccffa8a63bf02d43f71db6a9b9525d3590901",
    "f3119318b20de2b75cc849d336128adf9d045561aa5431ff48fc7c7e2a920456",
    "a291f38f99ee87c7e0b3e4ce7ca9123b3f40d217e670b529d964707c2e495123",
    ("ab14c14d43cf7e56dc9db3d88b99545e8a1381020446233a14d52d8cbdcca643",
     "80d0610f07f6e1c4e705dbaeb98a9e588bdd79aa32f97c1b112c642417880662"),
    (59, "centerSample", 59, "centerSample", 14, "LUMA"),
)

_PROFILE_SHA256 = "463f0e29b92ef2822381cadb3cb4bacc968a648c43a87623e0c0e6eb727172f3"


@dataclass(frozen=True, slots=True)
class EdgeBvec3ContourProof:
    _candidate: TypedProgram
    host: TypedFunction
    bvec_nodes: tuple[TypedExpression, ...]
    relationals: tuple[TypedExpression, ...]
    declarations: tuple[TypedExpression, ...]
    constructor: TypedExpression
    id_reads: tuple[TypedExpression, ...]
    swizzles: tuple[TypedExpression, ...]
    statement_parent_chains: tuple[tuple[TypedStatement, ...], ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [self.host, *self.bvec_nodes, *self.swizzles]
        for chain in self.statement_parent_chains:
            values.extend(chain)
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


@dataclass(frozen=True, slots=True)
class EdgeCenterSplatProof:
    _candidate: TypedProgram
    host: TypedFunction
    statement: TypedStatement
    statement_parent_chain: tuple[TypedStatement, ...]
    assignment: TypedExpression
    target: TypedExpression
    constructor: TypedExpression
    dot: TypedExpression
    dot_target: TypedExpression
    luma: TypedExpression

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        return (self.host, *self.statement_parent_chain, self.assignment,
                self.target, self.constructor, self.dot, self.dot_target,
                self.luma)


__all__ = (
    "PROFILE", "EDGE_KEY", "EdgeBvec3ContourProof", "EdgeCenterSplatProof",
    "authenticate_edge_bvec3_contour", "authenticate_edge_center_splat",
    "apply_edge_bvec3_contour",
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
    return (PROFILE, EDGE_KEY, _RAW_SHA256, (), "glsl-f32",
            _FUNCTIONS_SHA256, _WHOLE_SHA256, _INTERFACE_SHA256, _HOST_ID,
            _LOOP_PROOF, _BVEC_NODES, _SWIZZLES, _CENTER_SPLAT)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression,
                     parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, expression_path in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, expression_path, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def authenticate_edge_bvec3_contour(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> EdgeBvec3ContourProof:
    """Authenticate Edge and return only objects owned by ``program``."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != EDGE_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256):
        raise _fail("source, function, whole-program, or interface mismatch")
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
        raise _fail("loop proof mismatch")

    host = next((item for item in program.functions
                 if item.id == _HOST_ID), None)
    if (len(program.functions) != 4 or host is None
            or (host.name, host.return_type.display(),
                tuple((item.id, item.name, item.type.display())
                      for item in host.parameters),
                len(host.body), _span(host))
            != ("contourConv", "vec3",
                ((21, "fragCoord", "vec2"), (22, "texelSize", "vec2"),
                 (23, "centerRGB", "vec3"), (24, "lvl", "float"),
                 (25, "useLuma", "bool"), (26, "upperSide", "bool")),
                8, "56:1-87:2")):
        raise _fail("host function mismatch")

    names = {item.id: item.name for item in program.functions}
    graph: dict[str, tuple[str, ...]] = {}
    all_located = []
    for function in program.functions:
        located = []
        for index, statement in enumerate(function.body):
            located.extend(_walk_statement(statement, (index,)))
        all_located.extend((function, *record) for record in located)
        graph[function.name] = tuple(sorted({
            names[item.signature_id] for item, _, _, _ in located
            if item.kind == "call"
        }))
    if graph != {"applyBlend": (), "contourConv": (), "getWeight": (),
                 "main": ("applyBlend", "contourConv", "getWeight")}:
        raise _fail("call graph or render reachability mismatch")

    bvec_records = []
    relational_records = []
    stored_id_records = []
    swizzle_records = []
    for function, item, parent, path, chain in all_located:
        display = None if item.type is None else item.type.display()
        if display is not None and display.startswith("bvec"):
            bvec_records.append((function, item, parent, path, chain))
        if item.kind == "builtin" and item.callee in {
                "greaterThanEqual", "lessThan"}:
            relational_records.append((function, item, parent, path, chain))
        if item.kind == "id" and item.symbol_id in {40, 41}:
            stored_id_records.append((function, item, parent, path, chain))
        if (item.kind == "swizzle" and item.children
                and item.children[0].type is not None
                and item.children[0].type.display().startswith("bvec")):
            swizzle_records.append((function, item, parent, path, chain))

    if any(record[0] is not host for record in (
            *bvec_records, *relational_records, *stored_id_records,
            *swizzle_records)):
        raise _fail("authenticated closure escaped its host")
    actual_nodes = tuple(
        (path, _span(item), item.kind, item.callee, _sha(item),
         None if parent is None else parent.kind,
         tuple(child.type.display() for child in item.children),
         tuple(_sha(child) for child in item.children))
        for _, item, parent, path, _ in bvec_records)
    if actual_nodes != _BVEC_NODES:
        raise _fail("bvec3 node closure mismatch")
    actual_swizzles = tuple(
        (path, _span(item), item.member, item.children[0].symbol_id)
        for _, item, _, path, _ in swizzle_records)
    if actual_swizzles != _SWIZZLES:
        raise _fail("stored bvec3 lane route mismatch")

    bvec_nodes = tuple(record[1] for record in bvec_records)
    relationals = tuple(record[1] for record in relational_records)
    declarations = tuple(item for item in bvec_nodes
                         if item.kind == "declaration")
    constructors = tuple(item for item in bvec_nodes
                         if item.kind == "construct")
    id_reads = tuple(record[1] for record in stored_id_records)
    swizzles = tuple(record[1] for record in swizzle_records)
    if (relationals != (bvec_nodes[2], bvec_nodes[3])
            or len(declarations) != 2
            or tuple((item.symbol_id, item.symbol.name)
                     for item in declarations)
            != ((40, "centerOnSide"), (41, "crossing"))
            or len(constructors) != 1
            or constructors[0] is not declarations[1].children[0]
            or id_reads != (*bvec_nodes[6:9], *bvec_nodes[9:12])
            or len(swizzles) != 6
            or any(swizzle.children[0] is not read
                   for swizzle, read in zip(swizzles, id_reads))):
        raise _fail("declaration, relational, constructor, or read identity mismatch")

    chains = tuple(record[4] for record in bvec_records) + tuple(
        record[4] for record in swizzle_records)
    if (tuple(tuple((item.kind, _span(item)) for item in chain)
            for chain in chains)
            != ((("decl", "73:5-74:70"),),) * 4
               + ((("decl", "75:5-85:7"),),) * 5
               + ((("return", "86:5-86:89"),),) * 3
               + ((("decl", "75:5-85:7"),),) * 3
               + ((("return", "86:5-86:89"),),) * 3):
        raise _fail("statement ancestry mismatch")

    result = EdgeBvec3ContourProof(
        program, host, bvec_nodes, relationals, declarations,
        constructors[0], id_reads, swizzles, chains)
    if len(result.consumed_objects) != 22:
        raise _fail(
            f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def authenticate_edge_center_splat(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> EdgeCenterSplatProof:
    """Authenticate Edge's sole canonical lane-sequential self-splat."""
    authenticate_edge_bvec3_contour(program, source_hash, profile)
    main = next((item for item in program.functions
                 if item.name == "main"), None)
    if (main is None or main.id != 30 or main.return_type.display() != "void"
            or main.parameters != ()):
        raise _fail("center-splat host mismatch")

    records = []
    for statement_index, statement in enumerate(main.body):
        for item, _, path, chain in _walk_statement(
                statement, (statement_index,)):
            if (item.kind != "assign" or item.operator != "="
                    or len(item.children) != 2):
                continue
            target, constructor = item.children
            if (target.kind != "id" or target.type.display() != "vec3"
                    or constructor.kind != "construct"
                    or constructor.type.display() != "vec3"
                    or len(constructor.children) != 1):
                continue
            dot = constructor.children[0]
            if (dot.kind != "builtin" or dot.callee != "dot"
                    or dot.type.display() != "float" or len(dot.children) != 2
                    or dot.children[0].kind != "id"
                    or dot.children[0].symbol_id != target.symbol_id):
                continue
            statement_value = chain[-1]
            route = (
                target.symbol_id, target.symbol.name,
                dot.children[0].symbol_id, dot.children[0].symbol.name,
                dot.children[1].symbol_id, dot.children[1].symbol.name,
            )
            frozen = (
                path, tuple((ancestor.kind, _span(ancestor), _sha(ancestor))
                            for ancestor in chain),
                _span(item), _sha(item), _sha(target), _sha(constructor),
                _sha(dot), tuple(_sha(child) for child in dot.children), route,
            )
            records.append((frozen, statement_value, chain, item, target,
                            constructor, dot, dot.children[0], dot.children[1]))
    if tuple(record[0] for record in records) != (_CENTER_SPLAT,):
        raise _fail("canonical center-splat closure mismatch")
    (_, statement, chain, assignment, target, constructor, dot, dot_target,
     luma) = records[0]
    result = EdgeCenterSplatProof(
        program, main, statement, chain, assignment, target, constructor,
        dot, dot_target, luma)
    if (statement is not chain[-1]
            or len(result.consumed_objects) != 12
            or len({id(item) for item in result.consumed_objects}) != 12):
        raise _fail("center-splat ownership or cardinality mismatch")
    return result


def apply_edge_bvec3_contour(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    authenticate_edge_bvec3_contour(program, source_hash, profile)
    return program
