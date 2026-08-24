#!/usr/bin/env python3
"""Independent typed-frontend census for Edge's exact bvec3 closure.

This is an oracle asset, not production admission code.  It reparses the
pinned corpus source, freezes every bvec3 value and every read of those values,
and preserves both the historical pre-admission diagnostic widening and the
live exact-profile admission evidence.  Neither check edits modules on disk.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp.frontend.typed_ir import (  # noqa: E402
    TypedExpression,
    TypedProgram,
    TypedStatement,
)


REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
KEY = "filter/edge:edge"
SOURCE = (ROOT / "tools/glslcpp/corpus" / REVISION
          / "sources/filter/edge/edge.glsl")
PROFILE = "edge-bvec3-contour-v1"
RAW_SHA256 = "841f9f547d06aace8444953f401009abd02758f9dff271097b2799424c1db5d0"
NORMALIZED_SHA256 = "af95979c51c8135c5be956a4c5666897e7f622975c71e6ec63c1b4c1171d6324"
FUNCTIONS_SHA256 = "e69b0c3401068641c9e9f724c37515a3c3055217d06be7326a9a1621a9462c85"
WHOLE_SHA256 = "01849635b4a01ff1d14991c68c93804bff954c94c4fb18d53b7a5782cf19bc79"
INTERFACE_SHA256 = "97e91a090b9892f5e26aefe00ebf95e2448e32ef2825f4b54fd2357425798052"

# Captured before Edge admission at live typed slice 175.  This is frozen
# historical evidence.  --live-frontier observes the current gate later.
CAPTURED_PRE_ADMISSION_FRONTIER = {
    "typed_slice_programs": 175,
    "corpus_programs": 212,
    "remaining_programs": 37,
    "validator_first_error": (
        "filter/edge:edge:73:11: unsupported typed type bvec3"),
    "emitter_first_error": (
        "filter/edge:edge:73:38: unsupported builtin greaterThanEqual"),
    "diagnostic_bypass": {
        "method": (
            "temporarily admit bvec3 and the lessThan and greaterThanEqual "
            "builtins globally in process; retain the exact typed tree"),
        "validator": "pass",
        "emitter": "pass",
        "rendered_cpp_bytes": 14639,
        "rendered_cpp_sha256": (
            "fc9d8b6c220f5677136881ed304df6cb907f439e014864bdbd86b680fb938a23"),
    },
}

# The current exact-profile admission is intentionally separate from the
# immutable historical diagnostic above.  --live-frontier must reproduce this
# complete record from the current validator and emitter.
EXPECTED_CURRENT_PROFILE_FRONTIER = {
    "validator_first_error": (
        "filter/edge:edge: exact Edge bvec3 contour profile carrier required"),
    "emitter_first_error": (
        "filter/edge:edge:1:1: exact Edge bvec3 contour profile carrier required"),
    "profile_admission": {
        "method": (
            "supply edge-bvec3-contour-v1 to both independent authorities; "
            "retain the exact typed tree and lower the authenticated center "
            "self-splat as three ordered lane stores"),
        "validator": "pass",
        "emitter": "pass",
        "rendered_cpp_bytes": 14774,
        "rendered_cpp_sha256": (
            "8855be067925a5eafad622f8bb6541be2e58671adb78a740c0c3275838a0ddab"),
    },
}

# Every expression whose result type is bvec3, in traversal order.
# (path, span, kind, callee, node sha, parent kind, child types, child shas)
EXPECTED_BVEC_NODES = (
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

EXPECTED_SWIZZLES = (
    ((6, "e0", 0, 0, 0), "76:9-76:23", "r", 40),
    ((6, "e0", 0, 1, 0), "79:9-79:23", "g", 40),
    ((6, "e0", 0, 2, 0), "82:9-82:23", "b", 40),
    ((7, "e0", 0, 0), "86:17-86:27", "r", 41),
    ((7, "e0", 1, 0), "86:41-86:51", "g", 41),
    ((7, "e0", 2, 0), "86:65-86:75", "b", 41),
)

EXPECTED_CENTER_SPLAT = (
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


def sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def whole(program: TypedProgram) -> str:
    return sha((program.key, program.source, program.raw_source,
                program.declarations, program.functions, program.resources,
                program.body_status, program.local_type_names, program.structs,
                program.uniform_blocks, program.interface_symbols,
                program.builtin_symbols, program.counted_loop_proof,
                program.preprocessor_defines))


def interface(program: TypedProgram) -> str:
    return sha((program.declarations, program.resources,
                program.local_type_names, program.structs,
                program.uniform_blocks, program.interface_symbols,
                program.builtin_symbols, program.preprocessor_defines))


def walk_expression(value: TypedExpression,
                    parent: TypedExpression | None = None,
                    path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from walk_expression(child, value, (*path, index))


def walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                   ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, expression_path in walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, expression_path, chain
    for index, child in enumerate(value.children):
        yield from walk_statement(child, (*path, f"s{index}"), chain)


def parse(raw: str, key: str = KEY) -> TypedProgram:
    return analyze_program(parse_program(raw, key, gen._defaults(ROOT, key)), key)


def located(program: TypedProgram):
    host = next(item for item in program.functions if item.name == "contourConv")
    values = []
    for statement_index, statement in enumerate(host.body):
        for item, parent, path, chain in walk_statement(
                statement, (statement_index,)):
            values.append((item, parent, path, chain))
    return host, values


def bvec_nodes(program: TypedProgram):
    host, values = located(program)
    return host, [item for item in values
                  if item[0].type is not None
                  and item[0].type.display() == "bvec3"]


def bvec_swizzles(program: TypedProgram):
    host, values = located(program)
    return host, [item for item in values
                  if item[0].kind == "swizzle"
                  and item[0].children
                  and item[0].children[0].type is not None
                  and item[0].children[0].type.display() == "bvec3"]


def center_splats(program: TypedProgram):
    main = next(item for item in program.functions if item.name == "main")
    records = []
    for statement_index, statement in enumerate(main.body):
        for item, _, path, chain in walk_statement(statement,
                                                    (statement_index,)):
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
            records.append((item, target, constructor, dot, path, chain))
    return main, records


def center_splat_tuple(record: tuple[Any, ...]) -> tuple[object, ...]:
    item, target, constructor, dot, path, chain = record
    return (
        path,
        tuple((ancestor.kind, span(ancestor), sha(ancestor))
              for ancestor in chain),
        span(item), sha(item), sha(target), sha(constructor), sha(dot),
        tuple(sha(child) for child in dot.children),
        (target.symbol_id, target.symbol.name,
         dot.children[0].symbol_id, dot.children[0].symbol.name,
         dot.children[1].symbol_id, dot.children[1].symbol.name),
    )


def bvec_tuple(record: tuple[Any, ...]) -> tuple[object, ...]:
    item, parent, path, _ = record
    return (path, span(item), item.kind, item.callee, sha(item),
            None if parent is None else parent.kind,
            tuple(child.type.display() for child in item.children),
            tuple(sha(child) for child in item.children))


def swizzle_tuple(record: tuple[Any, ...]) -> tuple[object, ...]:
    item, _, path, _ = record
    base = item.children[0]
    return (path, span(item), item.member, base.symbol_id)


def call_graph(program: TypedProgram) -> dict[str, tuple[str, ...]]:
    names = {function.id: function.name for function in program.functions}
    result: dict[str, tuple[str, ...]] = {}
    for function in program.functions:
        called: set[str] = set()
        for statement_index, statement in enumerate(function.body):
            for item, _, _, _ in walk_statement(statement, (statement_index,)):
                if item.kind == "call":
                    called.add(names[item.signature_id])
        result[function.name] = tuple(sorted(called))
    return result


def reaches(graph: dict[str, tuple[str, ...]], source: str,
            target: str) -> bool:
    pending = [source]
    visited: set[str] = set()
    while pending:
        name = pending.pop()
        if name == target:
            return True
        if name in visited:
            continue
        visited.add(name)
        pending.extend(graph.get(name, ()))
    return False


def identity_accepts(program: TypedProgram, *, key: str, raw_hash: str,
                     profile: str) -> bool:
    host, nodes = bvec_nodes(program)
    _, swizzles = bvec_swizzles(program)
    main, splats = center_splats(program)
    proof = program.counted_loop_proof
    return all((
        profile == PROFILE,
        key == KEY,
        raw_hash == RAW_SHA256,
        len(program.raw_source.encode()) == 6530,
        hashlib.sha256(program.raw_source.encode()).hexdigest() == RAW_SHA256,
        len(program.source.encode()) == 5869,
        hashlib.sha256(program.source.encode()).hexdigest() == NORMALIZED_SHA256,
        sha(program.functions) == FUNCTIONS_SHA256,
        whole(program) == WHOLE_SHA256,
        interface(program) == INTERFACE_SHA256,
        program.body_status == "analyzed",
        program.preprocessor_defines == (),
        program.structs == (),
        program.uniform_blocks == (),
        len(program.functions) == 4,
        (main.id, main.name, main.return_type.display(), len(main.parameters))
        == (30, "main", "void", 0),
        (host.id, host.name, host.return_type.display(), len(host.parameters),
         len(host.body), span(host))
        == (28, "contourConv", "vec3", 6, 8, "56:1-87:2"),
        proof is not None,
        proof is not None and
        (proof.loop_count, proof.unproved_loop_count,
         proof.max_effective_depth, proof.max_lexical_product,
         proof.entrypoint_charge, proof.call_graph_acyclic)
        == (2, 0, 2, 49, 56, True),
        tuple(bvec_tuple(item) for item in nodes) == EXPECTED_BVEC_NODES,
        tuple(swizzle_tuple(item) for item in swizzles) == EXPECTED_SWIZZLES,
        tuple(center_splat_tuple(item) for item in splats)
        == (EXPECTED_CENTER_SPLAT,),
        sum(1 for item in nodes if item[0].kind == "declaration") == 2,
        sum(1 for item in nodes if item[0].kind == "builtin") == 2,
        sum(1 for item in nodes if item[0].kind == "construct") == 1,
        sum(1 for item in nodes if item[0].kind == "conditional") == 1,
        sum(1 for item in nodes if item[0].kind == "id") == 6,
    ))


def first_error(action) -> str:
    try:
        action()
    except Exception as error:  # noqa: BLE001 - frozen authority text
        return str(error).strip().splitlines()[0]
    return "pass"


def live_frontier(program: TypedProgram) -> dict[str, Any]:
    validator = first_error(lambda: gen.validate_capabilities(
        program, gen.APPROVED_CAPABILITIES, source_hash=RAW_SHA256))
    emitter = first_error(lambda: emit.render_typed_cpp(
        program, KEY, RAW_SHA256, "edge_probe", "bind_edge_probe"))

    rendered: list[str] = []
    bypass_validator = first_error(lambda: gen.validate_capabilities(
        program, gen.APPROVED_CAPABILITIES, source_hash=RAW_SHA256,
        edge_bvec3_contour_profile=PROFILE))
    bypass_emitter = first_error(lambda: rendered.append(
        emit.render_typed_cpp(
            program, KEY, RAW_SHA256, "edge_probe", "bind_edge_probe",
            edge_bvec3_contour_profile=PROFILE)))

    return {
        "validator_first_error": validator,
        "emitter_first_error": emitter,
        "profile_admission": {
            "method": EXPECTED_CURRENT_PROFILE_FRONTIER[
                "profile_admission"]["method"],
            "validator": bypass_validator,
            "emitter": bypass_emitter,
            "rendered_cpp_bytes": (len(rendered[0].encode())
                                   if rendered else None),
            "rendered_cpp_sha256": (hashlib.sha256(
                rendered[0].encode()).hexdigest() if rendered else None),
        },
    }


def mutation_record(name: str, raw: str, anchor: str,
                    replacement: str) -> dict[str, Any]:
    if raw.count(anchor) != 1:
        raise RuntimeError(f"{name}: mutation anchor count is {raw.count(anchor)}")
    mutated_raw = raw.replace(anchor, replacement)
    candidate = parse(mutated_raw)
    return {
        "name": name,
        "mutated_raw_sha256": hashlib.sha256(mutated_raw.encode()).hexdigest(),
        "bvec3_nodes": len(bvec_nodes(candidate)[1]),
        "bvec3_swizzles": len(bvec_swizzles(candidate)[1]),
        "independent_identity_accepts": identity_accepts(
            candidate, key=KEY,
            raw_hash=hashlib.sha256(mutated_raw.encode()).hexdigest(),
            profile=PROFILE),
    }


def build() -> dict[str, Any]:
    raw = SOURCE.read_text()
    program = parse(raw)
    host, nodes = bvec_nodes(program)
    _, swizzles = bvec_swizzles(program)
    main_host, splats = center_splats(program)
    graph = call_graph(program)
    if not identity_accepts(program, key=KEY, raw_hash=RAW_SHA256,
                            profile=PROFILE):
        raise RuntimeError("frozen Edge identity no longer authenticates")
    if not reaches(graph, "main", "contourConv"):
        raise RuntimeError("Edge contour closure is unreachable from main")

    mutations = [
        mutation_record("upper-relational-changed", raw,
                        "greaterThanEqual(centerRGB, vec3(lvl))",
                        "lessThanEqual(centerRGB, vec3(lvl))"),
        mutation_record("lower-relational-changed", raw,
                        "lessThan(centerRGB, vec3(lvl))",
                        "greaterThanEqual(centerRGB, vec3(lvl))"),
        mutation_record("red-lane-source-swapped", raw,
                        "centerOnSide.r &&", "centerOnSide.g &&"),
        mutation_record("crossing-lane-order-swapped", raw,
                        "centerOnSide.g && (upperSide",
                        "centerOnSide.b && (upperSide"),
        mutation_record("extra-bvec3-storage", raw,
                        "bvec3 crossing = bvec3(",
                        ("bvec3 extra = greaterThanEqual(centerRGB, vec3(lvl));\n"
                         "    bvec3 crossing = bvec3(")),
        mutation_record("center-splat-dot-route-reversed", raw,
                        "centerSample = vec3(dot(centerSample, LUMA));",
                        "centerSample = vec3(dot(LUMA, centerSample));"),
        mutation_record("extra-center-self-splat", raw,
                        "centerSample = vec3(dot(centerSample, LUMA));",
                        ("centerSample = vec3(dot(centerSample, LUMA));\n"
                         "        centerSample = vec3(dot(centerSample, LUMA));")),
    ]
    if any(item["independent_identity_accepts"] for item in mutations):
        raise RuntimeError("Edge frontend mutation escaped identity")

    current = live_frontier(program)
    if current != EXPECTED_CURRENT_PROFILE_FRONTIER:
        raise RuntimeError("Edge current exact-profile frontier drift")

    proof = program.counted_loop_proof
    return {
        "schema": "noisemaker-for-cpp.edge.bvec3-frontend-proof.v1",
        "program_key": KEY,
        "proposed_profile": PROFILE,
        "corpus_revision": REVISION,
        "identity": {
            "raw_bytes": len(raw.encode()),
            "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "normalized_bytes": len(program.source.encode()),
            "normalized_sha256": hashlib.sha256(
                program.source.encode()).hexdigest(),
            "functions_sha256": sha(program.functions),
            "whole_program_sha256": whole(program),
            "interface_sha256": interface(program),
            "function_count": len(program.functions),
            "defines": [],
            "body_status": program.body_status,
            "loop_proof": [
                proof.loop_count, proof.unproved_loop_count,
                proof.max_effective_depth, proof.max_lexical_product,
                proof.entrypoint_charge, proof.call_graph_acyclic,
            ],
            "resources": {
                "uniforms": list(program.resources.uniforms),
                "samplers": list(program.resources.samplers),
                "outputs": list(program.resources.outputs),
                "uses_texture": program.resources.uses_texture,
                "uses_derivatives": program.resources.uses_derivatives,
            },
        },
        "host": {
            "id": host.id,
            "name": host.name,
            "span": span(host),
            "return_type": host.return_type.display(),
            "parameter_count": len(host.parameters),
            "body_statement_count": len(host.body),
            "call_graph": {name: list(targets)
                           for name, targets in sorted(graph.items())},
            "main_reaches_host": reaches(graph, "main", "contourConv"),
        },
        "bvec3_nodes": [
            {
                "path_in_host": list(path),
                "span": span(item),
                "kind": item.kind,
                "callee": item.callee,
                "node_sha256": sha(item),
                "parent_kind": None if parent is None else parent.kind,
                "parent_span": None if parent is None else span(parent),
                "child_types": [child.type.display()
                                for child in item.children],
                "child_sha256": [sha(child) for child in item.children],
                "statement_chain": [
                    {"kind": ancestor.kind, "span": span(ancestor)}
                    for ancestor in chain
                ],
                "symbol": ({"id": item.symbol.id,
                            "name": item.symbol.name}
                           if item.symbol is not None else None),
            }
            for item, parent, path, chain in nodes
        ],
        "bvec3_swizzles": [
            {
                "path_in_host": list(path),
                "span": span(item),
                "lanes": item.member,
                "base_symbol_id": item.children[0].symbol_id,
                "base_symbol_name": item.children[0].symbol.name,
                "node_sha256": sha(item),
            }
            for item, _, path, _ in swizzles
        ],
        "center_splat": {
            "host_id": main_host.id,
            "path_in_main": list(splats[0][4]),
            "statement_chain": [
                {"kind": item.kind, "span": span(item),
                 "node_sha256": sha(item)}
                for item in splats[0][5]
            ],
            "assignment_span": span(splats[0][0]),
            "assignment_sha256": sha(splats[0][0]),
            "target_sha256": sha(splats[0][1]),
            "constructor_sha256": sha(splats[0][2]),
            "dot_sha256": sha(splats[0][3]),
            "dot_child_sha256": [sha(item)
                                  for item in splats[0][3].children],
            "symbol_route": [
                splats[0][1].symbol_id,
                splats[0][3].children[0].symbol_id,
                splats[0][3].children[1].symbol_id,
            ],
            "canonical_js_materialization": (
                "three ordered Float32 lane stores; each later dot reads "
                "the previously mutated centerSample"),
            "ordinary_whole_vec_assignment_rejected": True,
        },
        "captured_pre_admission_frontier": {
            "snapshot_kind": "captured-pre-admission-live175",
            "durability": (
                "frozen evidence; use --live-frontier after admission"),
            **CAPTURED_PRE_ADMISSION_FRONTIER,
        },
        "current_profile_frontier": {
            "snapshot_kind": "live-exact-profile-edge179",
            "durability": "recomputed and checked against the current tree",
            **current,
        },
        "profile_boundary": {
            "existing_extrude_profile_reusable_as_identity": False,
            "reason": (
                "Extrude authenticates two immediate bvec2 relational-to-"
                "reduction closures. Edge stores bvec3 values in two locals, "
                "selects between two relational results, constructs another "
                "bvec3, and reads six lanes."),
            "required": (
                "parallel exact Edge profile authenticating all 12 bvec3 "
                "typed nodes, six lane reads, their two declarations, exact "
                "host/reachability, key/hash/interface, and no other bvec "
                "value anywhere in the program"),
            "runtime_types": "glsl::BVec3 already exists",
            "runtime_helpers_required": [
                "greaterThanEqual(vec3, vec3/FloatExpr<3>) -> BVec3",
                "lessThan(vec3, vec3/FloatExpr<3>) -> BVec3",
            ],
            "global_type_vocabulary_must_change": False,
            "global_builtin_vocabulary_must_change": False,
            "global_helper_width_must_change": False,
        },
        "contract_negatives": [
            {"name": "wrong-profile", "accepted": identity_accepts(
                program, key=KEY, raw_hash=RAW_SHA256, profile="wrong")},
            {"name": "wrong-key", "accepted": identity_accepts(
                program, key="foreign:edge", raw_hash=RAW_SHA256,
                profile=PROFILE)},
            {"name": "wrong-caller-hash", "accepted": identity_accepts(
                program, key=KEY, raw_hash="0" * 64, profile=PROFILE)},
            *mutations,
        ],
    }


def main() -> int:
    data = build()
    if "--live-frontier" in sys.argv:
        print(json.dumps(live_frontier(parse(SOURCE.read_text())),
                         indent=2, sort_keys=True))
        return 0
    if "--check" in sys.argv:
        print("Edge frontend proof ok "
              f"({len(data['bvec3_nodes'])} exact bvec3 nodes, "
              f"{len(data['bvec3_swizzles'])} exact lane reads; "
              "authenticated center self-splat; validator/emitter pass)")
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
