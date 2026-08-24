#!/usr/bin/env python3
"""Read-only source/IR proof for the Shape Mixer182 JavaScript oracle.

This probe is evidence, not admission code.  It reparses the pinned GLSL with
``LOOP_OFFSET=10`` and fails closed if any whole-program, interface, resource,
call-graph, geometric-builtin, wide-mod, bit-ingress, or dynamic-index identity
drifts.  It never writes repository files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.scalar_uint_xor_profile import (  # noqa: E402
    PROFILE as SCALAR_XOR_PROFILE,
    authenticate_scalar_uint_xor,
)
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp.frontend.typed_ir import (  # noqa: E402
    TypedExpression,
    TypedProgram,
    TypedStatement,
)


REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
KEY = "classicNoisedeck/shapeMixer:shapeMixer"
SOURCE = (ROOT / "tools/glslcpp/corpus" / REVISION
          / "sources/classicNoisedeck/shapeMixer/shapeMixer.glsl")
RAW_BYTES = 21718
RAW_SHA256 = "704157151a2aa7e0192bd5b3483d5f1a5532a15a6e3f6a3ee0ba93ce70f8a9e4"
NORMALIZED_BYTES = 17664
NORMALIZED_SHA256 = "afb1be09867bbbb02f63c115b84ef4fd813d72defc71e2cc7d8891db9113b1b8"
FUNCTIONS_SHA256 = "ccf3834882fdd6ff45744377d38bd0b729f3e39d6d58c41c14a43095d6c99bcd"
DECLARATIONS_SHA256 = "cdbe1347d245c1feb13b2eacce960131ec035882a086c40b9af3ff43d2f8664a"
WHOLE_SHA256 = "57ad82d28eb34f2ea014122b03d2333099123d7b51dfe91629035ef5f41634f9"
INTERFACE_SHA256 = "45782fb4605e8e140b66a4e6b462408f79488968895dc6e735d66f5de748a21d"
FUNCTION_INVENTORY_SHA256 = "fd267bcb5cb3035f9a2174bfd29de118a6dca4d990f1d9eea65d432296a05f81"
BINDING_INVENTORY_SHA256 = "f7700f10ec7dd723ce09e8657e30d0e6aa5ce3a0e34b79cfe1d5bdbb4e3e5730"
CALL_GRAPH_SHA256 = "7dbff9a0b49d4282938dd7c6b8c5aedae5dbc520e05e48d0a96e0ad7d3c2f601"
REACHABLE = (99, 100, 101, 102, 103, 104, 106, 107, 108, 109, 110,
             111, 112, 113, 114, 115, 116, 118, 119, 120, 121, 122,
             123, 124, 125, 126, 127, 128, 130, 131, 132, 133, 134,
             135, 136)
UNREACHABLE = (105, 117, 129)
RESOURCE_NAMES = (
    "inputTex", "tex", "resolution", "tileOffset", "fullResolution",
    "time", "seed", "blendMode", "loopScale", "paletteMode",
    "paletteOffset", "paletteAmp", "paletteFreq", "palettePhase",
    "animate", "cyclePalette", "rotatePalette", "repeatPalette",
    "levels", "wrap",
)
RESOURCE_TYPES = (
    "sampler2D", "sampler2D", "vec2", "vec2", "vec2", "float", "int",
    "int", "float", "int", "vec3", "vec3", "vec3", "vec3", "int",
    "int", "float", "float", "float", "bool",
)
GEOMETRIC_LOCKS = (
    (99, "blend", "reflect", "float", "672:17-672:49",
     "6c44e7a12325dc21c075e5e06b08aee23db609835b9e903fb9eb490c5fe9969e",
     ("float", "float"), "assign", "672:9-672:49",
     "7eda259a9e49fcb064fffe21a8c238b2a32302b699953bb20361508292ce639f"),
    (99, "blend", "refract", "float", "675:17-675:48",
     "243e10285acd7fc24f0d3d2496c593d390c23bcfdc33b5c4e97aec43dc80fa03",
     ("float", "float", "float"), "assign", "675:9-675:48",
     "0ac43ced9b9ccca9338181fa2203b8ee956e3fc4a6cf456c0f60cf335ec3e823"),
    (100, "blend", "reflect", "vec3", "625:17-625:49",
     "e7773612b7e390575ae32f1a215ed0bd4f23deeaa668798f9867ae09984a548d",
     ("vec3", "vec3"), "assign", "625:9-625:49",
     "077422fb0acd71397427a91c310f7414e87c1ed1e1ef1ba58b7e21da08a92b4b"),
    (100, "blend", "refract", "vec3", "628:17-628:48",
     "9719b815cd3a11bde7a013648ffc9c40681b818c2bc85ee22e224719f1eadbe7",
     ("vec3", "vec3", "float"), "assign", "628:9-628:48",
     "12774d36a5c9baf9c2cbe95158999b0cda9fc57d8f416400c0934f7bf03fdb92"),
)
WIDE_MOD_LOCK = (
    100, "blend", "mod", "vec3", "619:17-619:45",
    "adbd6c013236568bbd6bf6b0d9300b02219959ec3bbadef1f5931a36612565e8",
    ("vec3", "vec3"), "assign", "619:9-619:45",
    "f65d5394d1b8da4181737b0f616d8fa776c91ae4ad95955c157354443c654e00",
)
BIT_INGRESS_LOCK = (
    130, "randomFromLatticeWithOffset", "floatBitsToUint", "uint",
    "411:21-411:46",
    "7af407db873fb245128e37a9607f63e96bd7e045949a7c2a0248935d6680c599",
    ("float",), "declaration", "411:10-411:46",
    "c79dfe491df8e5b426b701baa461aa0cfb756367e46e411c052d7e663acacb5c",
)
INDEX_LOCKS = (
    ("116:13-116:22", "528b09c525aada465b6c495d8baba229f4505f035bf289dfcc3a633a1df1fe65", 26, "linear", 152, "i", "binary"),
    ("117:13-117:20", "4f71a469a541118309586ab52d77595abbaf41ec0bce41bbf6e7df5c207a1b38", 151, "srgb", 152, "i", "assign"),
    ("117:23-117:32", "f83cbc13499fb9ef2b1342876974d5a9d4e506809d79b5b333ee0982249eb86f", 26, "linear", 152, "i", "binary"),
    ("119:13-119:20", "cc5ebbdb32112bacf7f25ff10b7a8b4fde6d7e574b0e69e319f58d41a1e16e32", 151, "srgb", 152, "i", "assign"),
    ("119:35-119:44", "b845e12b17619d5c93857882f43fb929a365ad00aad60ac1e36907845e3df7f8", 26, "linear", 152, "i", "builtin"),
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


def walk_statement(value: TypedStatement, path: tuple[object, ...] = ()):
    for index, expression in enumerate(value.expressions):
        yield from walk_expression(expression, None, (*path, f"e{index}"))
    for index, child in enumerate(value.children):
        yield from walk_statement(child, (*path, f"s{index}"))


def all_nodes(program: TypedProgram):
    calls: dict[int, list[int]] = {
        function.signature.id: [] for function in program.functions}
    records = []
    for function in program.functions:
        for statement_index, statement in enumerate(function.body):
            for node, parent, path in walk_statement(statement,
                                                     (statement_index,)):
                records.append((function, node, parent, path))
                if (node.kind == "call" and node.signature_id in calls
                        and node.signature_id not in calls[function.signature.id]):
                    calls[function.signature.id].append(node.signature_id)
    return records, calls


def node_lock(record: tuple[Any, ...]) -> tuple[object, ...]:
    function, node, parent, _ = record
    return (
        function.signature.id, function.name, node.callee,
        node.type.display(), span(node), sha(node),
        tuple(child.type.display() for child in node.children),
        None if parent is None else parent.kind,
        None if parent is None else span(parent),
        None if parent is None else sha(parent),
    )


def build() -> dict[str, object]:
    raw = SOURCE.read_bytes()
    if len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256:
        raise RuntimeError("pinned Shape Mixer GLSL source drift")
    parsed = parse_program(raw.decode("utf-8"), KEY, {"LOOP_OFFSET": 10})
    normalized = parsed["source"].encode("utf-8")
    if (len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256):
        raise RuntimeError("pinned LOOP_OFFSET=10 normalized source drift")
    program = analyze_program(parsed, KEY)
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    inventory = tuple(
        (item.signature.id, item.name, item.return_type.display(),
         len(item.parameters), len(item.body), span(item))
        for item in program.functions)
    bindings = tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable)
        for item in program.declarations)
    resources = program.resources
    resource_tuple = (resources.uniforms, resources.samplers,
                      resources.outputs, resources.uses_texture,
                      resources.uses_derivatives)
    loop = program.counted_loop_proof
    loop_tuple = (loop.loop_count, loop.unproved_loop_count,
                  loop.max_effective_depth, loop.max_lexical_product,
                  loop.entrypoint_charge, loop.call_graph_acyclic)
    if (defines != (("LOOP_OFFSET", "int", "10"),)
            or program.body_status != "analyzed"
            or len(program.declarations) != 25
            or len(program.functions) != 38
            or sha(program.functions) != FUNCTIONS_SHA256
            or sha(program.declarations) != DECLARATIONS_SHA256
            or whole(program) != WHOLE_SHA256
            or interface(program) != INTERFACE_SHA256
            or sha(inventory) != FUNCTION_INVENTORY_SHA256
            or sha(bindings) != BINDING_INVENTORY_SHA256
            or resource_tuple != (RESOURCE_NAMES, ("inputTex", "tex"),
                                  ("fragColor",), True, False)
            or loop_tuple != (1, 0, 1, 3, 3, True)
            or program.structs or program.uniform_blocks):
        raise RuntimeError("Shape Mixer whole-program or interface drift")

    declaration_types = {item.symbol.name: item.type.display()
                         for item in program.declarations}
    if tuple(declaration_types[name] for name in RESOURCE_NAMES) != RESOURCE_TYPES:
        raise RuntimeError("Shape Mixer binding type/order drift")
    globals_ = tuple((item.symbol.id, item.symbol.name, item.type.display(),
                      item.symbol.storage, item.symbol.writable, span(item),
                      sha(item), sha(item.initializer))
                     for item in program.declarations
                     if item.type.display() == "mat3")
    if tuple(item[1] for item in globals_) != ("fwdA", "fwdB", "invB", "invA"):
        raise RuntimeError("Shape Mixer const mat3 global drift")
    if any(item[2:5] != ("mat3", "const", False) for item in globals_):
        raise RuntimeError("Shape Mixer const mat3 qualifier drift")

    records, calls = all_nodes(program)
    geometric = [item for item in records
                 if item[1].kind == "builtin"
                 and item[1].callee in ("reflect", "refract")]
    if tuple(node_lock(item) for item in geometric) != GEOMETRIC_LOCKS:
        raise RuntimeError("Shape Mixer geometric builtin identity drift")
    mods = [item for item in records
            if item[1].kind == "builtin" and item[1].callee == "mod"]
    wide_mod = [item for item in mods
                if item[1].type.display() == "vec3"]
    if len(mods) != 6 or len(wide_mod) != 1 or node_lock(wide_mod[0]) != WIDE_MOD_LOCK:
        raise RuntimeError("Shape Mixer mod census or wide-mod identity drift")
    ingress = [item for item in records if item[1].kind == "builtin"
               and item[1].callee == "floatBitsToUint"]
    if len(ingress) != 1 or node_lock(ingress[0]) != BIT_INGRESS_LOCK:
        raise RuntimeError("Shape Mixer floatBitsToUint identity drift")
    indexes = [item for item in records if item[1].kind == "index"]
    index_locks = tuple((span(node), sha(node), node.children[0].symbol_id,
                         node.children[0].symbol.name,
                         node.children[1].symbol_id,
                         node.children[1].symbol.name,
                         parent.kind)
                        for function, node, parent, _ in indexes
                        if function.signature.id == 109)
    if len(indexes) != 5 or index_locks != INDEX_LOCKS:
        raise RuntimeError("Shape Mixer dynamic vec3 index identity drift")

    call_graph = tuple((function.signature.id,
                        tuple(calls[function.signature.id]))
                       for function in program.functions)
    reachable: set[int] = set()
    pending = [112]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(calls[current])
    if (sha(call_graph) != CALL_GRAPH_SHA256
            or tuple(sorted(reachable)) != REACHABLE
            or tuple(sorted(set(calls) - reachable)) != UNREACHABLE):
        raise RuntimeError("Shape Mixer call graph or reachability drift")

    xor_nodes = authenticate_scalar_uint_xor(
        program, RAW_SHA256, SCALAR_XOR_PROFILE)
    source = normalized.decode("utf-8")
    anchors = {
        "linear_to_srgb_loop": source.count("for (int i = 0; i < 3; ++i)"),
        "factor_inversions": source.count("factor = 1.0 - factor;"),
        "vector_half_factor": source.count("blendMode, blendy * 0.5"),
        "input_texture_sample": source.count("texture(inputTex"),
        "second_texture_sample": source.count("texture(tex"),
        "alpha_max": source.count("color.a = max(color1.a, color2.a);"),
        "bit_ingress": source.count("floatBitsToUint(seedFrac)"),
    }
    if anchors != {
            "linear_to_srgb_loop": 1, "factor_inversions": 2,
            "vector_half_factor": 1, "input_texture_sample": 1,
            "second_texture_sample": 1, "alpha_max": 1,
            "bit_ingress": 1}:
        raise RuntimeError(f"Shape Mixer source anchor drift: {anchors}")
    mode_counts = {str(mode): source.count(f"mode == {mode}")
                   for mode in range(10)}
    if any(value != 2 for value in mode_counts.values()):
        raise RuntimeError(f"Shape Mixer mode ladder drift: {mode_counts}")

    return {
        "schema": "noisemaker-for-cpp.shape-mixer.frontend-probe.v1",
        "program_key": KEY,
        "corpus_revision": REVISION,
        "raw_source": {"bytes": len(raw), "sha256": RAW_SHA256},
        "normalized_source": {
            "define": {"LOOP_OFFSET": 10},
            "bytes": len(normalized), "sha256": NORMALIZED_SHA256},
        "program_fingerprints": {
            "functions_sha256": FUNCTIONS_SHA256,
            "declarations_sha256": DECLARATIONS_SHA256,
            "whole_program_sha256": WHOLE_SHA256,
            "interface_sha256": INTERFACE_SHA256,
            "function_inventory_sha256": FUNCTION_INVENTORY_SHA256,
            "binding_inventory_sha256": BINDING_INVENTORY_SHA256,
            "call_graph_sha256": CALL_GRAPH_SHA256,
        },
        "counts": {"declarations": 25, "functions": 38,
                   "mod_calls": 6, "dynamic_indexes": 5,
                   "scalar_uint_xor_nodes": len(xor_nodes)},
        "resources": {"names": list(RESOURCE_NAMES),
                      "types": list(RESOURCE_TYPES),
                      "samplers": ["inputTex", "tex"],
                      "outputs": ["fragColor"],
                      "uses_texture": True, "uses_derivatives": False},
        "loop_proof": list(loop_tuple),
        "reachable_function_ids": list(REACHABLE),
        "unreachable_function_ids": list(UNREACHABLE),
        "const_mat3_globals": [
            {"symbol_id": item[0], "name": item[1], "span": item[5],
             "declaration_sha256": item[6], "initializer_sha256": item[7]}
            for item in globals_],
        "geometric_nodes": [
            {"owner_id": item[0], "owner": item[1], "callee": item[2],
             "result_type": item[3], "span": item[4], "node_sha256": item[5],
             "argument_types": list(item[6]), "parent_kind": item[7],
             "parent_span": item[8], "parent_sha256": item[9]}
            for item in GEOMETRIC_LOCKS],
        "wide_mod_node": {"owner_id": WIDE_MOD_LOCK[0],
                          "span": WIDE_MOD_LOCK[4],
                          "node_sha256": WIDE_MOD_LOCK[5]},
        "bit_ingress_node": {"owner_id": BIT_INGRESS_LOCK[0],
                             "span": BIT_INGRESS_LOCK[4],
                             "node_sha256": BIT_INGRESS_LOCK[5]},
        "dynamic_index_nodes": [
            {"span": item[0], "node_sha256": item[1],
             "base_symbol_id": item[2], "base": item[3],
             "induction_symbol_id": item[4], "induction": item[5],
             "parent_kind": item[6]}
            for item in INDEX_LOCKS],
        "source_anchor_census": anchors,
        "mode_ladder_census": mode_counts,
        "scalar_uint_xor_companion": SCALAR_XOR_PROFILE,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args(argv)
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
