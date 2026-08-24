#!/usr/bin/env python3
"""Independent current-frontier and identity census for Scanline Error.

This script is an oracle asset, not production admission code.  It reparses the
pinned corpus source, records the exact three ``floatBitsToUint`` nodes, and
proves that replacing only those unsupported builtins with an already-admitted
builtin exposes no later validator or emitter gate.
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
KEY = "filter/scanlineError:scanlineError"
SOURCE = (ROOT / "tools/glslcpp/corpus" / REVISION
          / "sources/filter/scanlineError/scanlineError.glsl")
RAW_SHA256 = "66556b29659b479edd397f8e0c87c176cafa7560c426eab8211b6939a08f2198"
NORMALIZED_SHA256 = "a3f9b6dc4c76e09f3379ff8b3dfea4e909b77b2084edb5fd6d6eb5146dd72a63"
FUNCTIONS_SHA256 = "ed2047b18516f88701c44b45742561860b8dc62a56f463231c00823bd470cb0b"
WHOLE_SHA256 = "9585ed49e2fe4c258ed23feb5b349421126101451b7264e9d65a44bf1027ef7a"
INTERFACE_SHA256 = "c2e8b81ea371988159e842ddc32177268989b10776abbd2375d43b0182f2f35e"
PROFILE = "scanline-error-float-bits-ingress-v1"

# Frozen evidence captured by this script against live typed slice 174 before
# production admission.  It is deliberately data, not a forever-current test:
# once the new exact profile exists, calling validation without its carrier
# must fail at a different (profile-required) gate.  ``--live-frontier`` is the
# explicit diagnostic mode for observing that transition without rewriting the
# oracle JSON or making its ordinary ``--check`` self-invalidating.
CAPTURED_PRE_ADMISSION_FRONTIER = {
    "typed_slice_programs": 174,
    "corpus_programs": 212,
    "remaining_programs": 38,
    "validator_first_error": (
        "filter/scanlineError:scanlineError:234:24: "
        "unsupported builtin floatBitsToUint"),
    "emitter_first_error": (
        "filter/scanlineError:scanlineError:234:24: "
        "unsupported builtin floatBitsToUint"),
    "diagnostic_bypass": {
        "method": (
            "replace exactly the three floatBitsToUint callees with "
            "already-admitted abs in memory; retain typed nodes and all "
            "other source structure"),
        "validator": "pass",
        "emitter": "pass",
        "rendered_cpp_bytes": 37672,
        "rendered_cpp_sha256": (
            "6fdd47fc25a045239adc348dad0075d6513974e96ea4f93f726112bca7f51db5"),
    },
}

EXPECTED_NODES = (
    ((0, "e0", 0, 0), "234:24-234:44", "uint",
     "2402bf7aad304a4e6424e97c2617afa0554cd1cb2be13fa598b7064e42557ec6",
     "construct", ("float",),
     ("694c599fbc13e63691cb6db314cc05974ac044ca161fe2514441052e672735f5",)),
    ((0, "e0", 0, 1), "234:46-234:66", "uint",
     "d82ebb35ac2a24139851ec2bde1a92c8c6df4e0a7ba67acd6b2e53705e806436",
     "construct", ("float",),
     ("14eda8b6339c0ff91896b354074403e16175bb9876ef18ef8dbac65c4dc915eb",)),
    ((0, "e0", 0, 2), "234:68-234:88", "uint",
     "5ec80d658b993e6eca6ce0478da6d2ff2dd877b7d49178ce1231094d851a9552",
     "construct", ("float",),
     ("6bbdea87cfdfed567bbbb023d3a4d59e476c5b85698679b462eb76e219f8cdea",)),
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


def walk_statement(value: TypedStatement,
                   path: tuple[object, ...] = (),
                   ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        yield from ((item, parent, epath, chain)
                    for item, parent, epath in walk_expression(
                        expression, None, (*path, f"e{index}")))
    for index, child in enumerate(value.children):
        yield from walk_statement(child, (*path, f"s{index}"), chain)


def parse(raw: str, key: str = KEY) -> TypedProgram:
    return analyze_program(parse_program(raw, key, gen._defaults(ROOT, key)), key)


def sites(program: TypedProgram):
    found = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in walk_statement(statement, (index,)):
                if item.kind == "builtin" and item.callee == "floatBitsToUint":
                    found.append((function, item, parent, path, chain))
    return found


def call_graph(program: TypedProgram) -> dict[str, tuple[str, ...]]:
    names = {function.id: function.name for function in program.functions}
    result: dict[str, tuple[str, ...]] = {}
    for function in program.functions:
        called: set[str] = set()
        for statement_index, statement in enumerate(function.body):
            for item, _, _, _ in walk_statement(statement, (statement_index,)):
                if item.kind == "call":
                    if item.signature_id not in names:
                        raise RuntimeError(
                            f"unknown call target {item.signature_id} in {function.name}")
                    called.add(names[item.signature_id])
        result[function.name] = tuple(sorted(called))
    return result


def reaches(graph: dict[str, tuple[str, ...]], source: str,
            target: str) -> bool:
    pending = [source]
    visited: set[str] = set()
    while pending:
        item = pending.pop()
        if item == target:
            return True
        if item in visited:
            continue
        visited.add(item)
        pending.extend(graph.get(item, ()))
    return False


def node_tuple(item: tuple[Any, ...]) -> tuple[object, ...]:
    _, expression, parent, path, _ = item
    return (path, span(expression), expression.type.display(), sha(expression),
            "" if parent is None else parent.kind,
            tuple(child.type.display() for child in expression.children),
            tuple(sha(child) for child in expression.children))


def replace_ingress_with_abs(program: TypedProgram) -> TypedProgram:
    """Diagnostic-only replacement used to expose the downstream gate."""
    def expression(value: TypedExpression) -> TypedExpression:
        result = dataclasses.replace(
            value, children=tuple(expression(child) for child in value.children))
        if result.kind == "builtin" and result.callee == "floatBitsToUint":
            result = dataclasses.replace(result, callee="abs")
        return result

    def statement(value: TypedStatement) -> TypedStatement:
        return dataclasses.replace(
            value,
            expressions=tuple(expression(item) for item in value.expressions),
            children=tuple(statement(item) for item in value.children))

    return dataclasses.replace(
        program,
        functions=tuple(dataclasses.replace(
            function, body=tuple(statement(item) for item in function.body))
                        for function in program.functions))


def first_error(action) -> str:
    try:
        action()
    except Exception as error:  # noqa: BLE001 - evidence captures authority text
        return str(error).strip().splitlines()[0]
    return "pass"


def live_frontier(program: TypedProgram) -> dict:
    validator = first_error(lambda: gen.validate_capabilities(
        program, gen.APPROVED_CAPABILITIES, source_hash=RAW_SHA256))
    emitter = first_error(lambda: emit.render_typed_cpp(
        program, KEY, RAW_SHA256, "scanline_error_probe",
        "bind_scanline_error_probe"))
    bypass = replace_ingress_with_abs(program)
    bypass_validator = first_error(lambda: gen.validate_capabilities(
        bypass, gen.APPROVED_CAPABILITIES, source_hash=RAW_SHA256))
    rendered: list[str] = []
    bypass_emitter = first_error(lambda: rendered.append(emit.render_typed_cpp(
        bypass, KEY, RAW_SHA256, "scanline_error_probe",
        "bind_scanline_error_probe")))
    return {
        "validator_first_error": validator,
        "emitter_first_error": emitter,
        "diagnostic_bypass": {
            "method": CAPTURED_PRE_ADMISSION_FRONTIER["diagnostic_bypass"]["method"],
            "validator": bypass_validator,
            "emitter": bypass_emitter,
            "rendered_cpp_bytes": len(rendered[0].encode()) if rendered else None,
            "rendered_cpp_sha256": hashlib.sha256(
                rendered[0].encode()).hexdigest() if rendered else None,
        },
    }


def identity_accepts(program: TypedProgram, *, key: str, raw_hash: str,
                     profile: str) -> bool:
    """Independent frozen predicate defining the required future profile."""
    located = sites(program)
    host = next((item for item in program.functions if item.id == 69), None)
    proof = program.counted_loop_proof
    return all((
        profile == PROFILE,
        key == KEY,
        raw_hash == RAW_SHA256,
        len(program.raw_source.encode("utf-8")) == 13302,
        hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest() == RAW_SHA256,
        len(program.source.encode("utf-8")) == 12383,
        hashlib.sha256(program.source.encode("utf-8")).hexdigest() == NORMALIZED_SHA256,
        sha(program.functions) == FUNCTIONS_SHA256,
        whole(program) == WHOLE_SHA256,
        interface(program) == INTERFACE_SHA256,
        program.body_status == "analyzed",
        program.preprocessor_defines == (),
        program.structs == (),
        program.uniform_blocks == (),
        len(program.functions) == 19,
        host is not None,
        host is not None and (host.name, host.return_type.display(),
                              len(host.parameters), len(host.body), span(host))
        == ("hashNoise", "float", 1, 2, "233:1-236:2"),
        proof is not None,
        proof is not None and
        (proof.loop_count, proof.unproved_loop_count,
         proof.max_effective_depth, proof.max_lexical_product,
         proof.entrypoint_charge, proof.call_graph_acyclic)
        == (0, 0, 0, 0, 0, True),
        tuple(node_tuple(item) for item in located) == EXPECTED_NODES,
        all(function.id == 69 for function, *_ in located),
        all(tuple((ancestor.kind, span(ancestor)) for ancestor in chain)
            == (("decl", "234:5-234:90"),)
            for *_, chain in located),
        len({id(parent) for _, _, parent, _, _ in located}) == 1,
    ))


def mutation_record(name: str, raw: str, anchor: str, replacement: str) -> dict:
    if raw.count(anchor) != 1:
        raise RuntimeError(f"{name}: mutation anchor count is {raw.count(anchor)}")
    mutated_raw = raw.replace(anchor, replacement)
    candidate = parse(mutated_raw)
    return {
        "name": name,
        "mutated_raw_sha256": hashlib.sha256(mutated_raw.encode()).hexdigest(),
        "float_bits_sites": len(sites(candidate)),
        "independent_identity_accepts": identity_accepts(
            candidate, key=KEY,
            raw_hash=hashlib.sha256(mutated_raw.encode()).hexdigest(),
            profile=PROFILE),
    }


def build() -> dict:
    raw = SOURCE.read_text()
    program = parse(raw)
    located = sites(program)
    graph = call_graph(program)
    if not identity_accepts(program, key=KEY, raw_hash=RAW_SHA256, profile=PROFILE):
        raise RuntimeError("frozen Scanline Error identity no longer authenticates")
    if (not reaches(graph, "main", "hashNoise")
            or not reaches(graph, "vhs_gradValue", "hashNoise")
            or not reaches(graph, "vhs_scanNoise", "hashNoise")):
        raise RuntimeError("float-bit ingress host is not reachable on both VHS paths")

    mutations = [
        mutation_record("lane-x-numeric-conversion", raw,
                        "floatBitsToUint(p.x)", "uint(p.x)"),
        mutation_record("lane-y-source-swapped", raw,
                        "floatBitsToUint(p.y)", "floatBitsToUint(p.x)"),
        mutation_record("extra-ingress-site", raw,
                        "uvec3 seed = uvec3(",
                        "uint extraBits = floatBitsToUint(p.x);\n    uvec3 seed = uvec3("),
    ]
    for record in mutations:
        if record["independent_identity_accepts"]:
            raise RuntimeError(f"mutation escaped identity: {record['name']}")

    parent = located[0][2]
    return {
        "schema": "noisemaker-for-cpp.scanline-error.frontend-proof.v1",
        "program_key": KEY,
        "proposed_profile": PROFILE,
        "corpus_revision": REVISION,
        "identity": {
            "raw_bytes": len(raw.encode()),
            "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "normalized_bytes": len(program.source.encode()),
            "normalized_sha256": hashlib.sha256(program.source.encode()).hexdigest(),
            "functions_sha256": sha(program.functions),
            "whole_program_sha256": whole(program),
            "interface_sha256": interface(program),
            "function_count": len(program.functions),
            "defines": [],
            "body_status": program.body_status,
            "loop_proof": [
                program.counted_loop_proof.loop_count,
                program.counted_loop_proof.unproved_loop_count,
                program.counted_loop_proof.max_effective_depth,
                program.counted_loop_proof.max_lexical_product,
                program.counted_loop_proof.entrypoint_charge,
                program.counted_loop_proof.call_graph_acyclic,
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
            "id": 69,
            "name": located[0][0].name,
            "span": span(located[0][0]),
            "return_type": located[0][0].return_type.display(),
            "parameter_count": len(located[0][0].parameters),
            "body_statement_count": len(located[0][0].body),
            "reachable_chain_from_main": [
                "main", "vhs_gradValue/vhs_scanNoise", "vhs_computeNoise",
                "valueNoise", "hashNoise",
            ],
            "call_graph": {name: list(targets)
                           for name, targets in sorted(graph.items())},
            "main_reaches_host": reaches(graph, "main", "hashNoise"),
            "both_vhs_helpers_reach_host": (
                reaches(graph, "vhs_gradValue", "hashNoise")
                and reaches(graph, "vhs_scanNoise", "hashNoise")),
        },
        "nodes": [
            {
                "path_in_host": list(path),
                "span": span(item),
                "result_type": item.type.display(),
                "node_sha256": sha(item),
                "parent_kind": parent.kind if parent is not None else None,
                "parent_span": span(parent) if parent is not None else None,
                "child_types": [child.type.display() for child in item.children],
                "child_sha256": [sha(child) for child in item.children],
                "statement_chain": [
                    {"kind": ancestor.kind, "span": span(ancestor)}
                    for ancestor in chain
                ],
            }
            for _, item, parent, path, chain in located
        ],
        "shared_parent": {
            "kind": parent.kind,
            "span": span(parent),
            "sha256": sha(parent),
            "all_three_share_object_identity": all(
                candidate[2] is parent for candidate in located),
        },
        "current_frontier": {
            "snapshot_kind": "captured-pre-admission-live174",
            "durability": (
                "frozen evidence; use --live-frontier to observe later "
                "production admission without changing this oracle"),
            **CAPTURED_PRE_ADMISSION_FRONTIER,
        },
        "profile_boundary": {
            "caustic_profile_reusable_as_identity": False,
            "reason": "Caustic freezes another key/hash, NOISE_TYPE=10, one ingress, and three scalar uint XOR nodes.",
            "required": "parallel exact Scanline Error profile authenticating these three ingress objects; validator and emitter re-authenticate independently",
            "runtime_lowering_reusable": "noisemaker::float_bits_to_uint(expression)",
            "global_builtin_vocabulary_must_change": False,
            "scalar_xor_profile_required": False,
        },
        "contract_negatives": [
            {"name": "wrong-profile", "accepted": identity_accepts(
                program, key=KEY, raw_hash=RAW_SHA256, profile="wrong")},
            {"name": "wrong-key", "accepted": identity_accepts(
                program, key="foreign:scanlineError", raw_hash=RAW_SHA256,
                profile=PROFILE)},
            {"name": "wrong-caller-hash", "accepted": identity_accepts(
                program, key=KEY, raw_hash="0" * 64, profile=PROFILE)},
            *mutations,
        ],
    }


def main() -> int:
    data = build()
    if "--live-frontier" in sys.argv:
        raw = SOURCE.read_text()
        print(json.dumps(live_frontier(parse(raw)), indent=2, sort_keys=True))
        return 0
    if "--check" in sys.argv:
        print("Scanline Error frontend proof ok "
              f"({len(data['nodes'])} exact ingress nodes; frozen live174 "
              "validator/emitter downstream evidence intact)")
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
