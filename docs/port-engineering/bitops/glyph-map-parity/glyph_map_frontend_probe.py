#!/usr/bin/env python3
"""Frozen typed-frontend proof for ``filter/glyphMap:glyphMap``.

This is an oracle asset, not admission code.  It authenticates the one scalar
``int >> int`` node, its immediate scalar ``int & 1`` parent, the sole source
``const int`` and its three reads, plus the exact return/materialization route.
The diagnostic bypass replaces only the two unsupported scalar bit operators
in memory to expose the downstream frontend boundary.
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
KEY = "filter/glyphMap:glyphMap"
PROFILE = "glyph-map-nonnegative-int-shift-v1"
SOURCE = (ROOT / "tools/glslcpp/corpus" / REVISION
          / "sources/filter/glyphMap/glyphMap.glsl")
RAW_SHA256 = "853c3c15f300cf56ba3c11d5613cb91bfcb14b8b2f1be6bb5193e71397fdcea1"
NORMALIZED_SHA256 = "03e74590b109c90a3c31ad003e62e9448a503a15afe68c18ec4a9de8d1bc2c8f"
FUNCTIONS_SHA256 = "96ad0a2ebb84546c658d4526dcd62b31768f7f8abb2157760beaa2d61f1feb73"
WHOLE_SHA256 = "837cf0f8548c8e39960c3aa0cc55f92d2aab0bf4aae1e878c0857679322b8d69"
INTERFACE_SHA256 = "de5f9e502fa19dfd21b54cf8256f9d12f6d4989d826f7fe99a3d7427b9a568f7"

CAPTURED_PRE_ADMISSION_FRONTIER = {
    "typed_slice_programs": 174,
    "validator_first_error": (
        "filter/glyphMap:glyphMap:287:16: unsupported binary operator &"),
    "emitter_first_error": (
        "filter/glyphMap:glyphMap:287:16: unsupported binary operator &"),
    "after_mask_bypass_validator": (
        "filter/glyphMap:glyphMap:287:16: unsupported binary operator >>"),
    "after_mask_bypass_emitter": (
        "filter/glyphMap:glyphMap:287:16: unsupported binary operator >>"),
    "diagnostic_bypass": {
        "method": (
            "replace only the exact scalar int & and scalar int >> nodes with "
            "ordinary int + in memory; retain every operand, parent, symbol, "
            "statement, function, interface, and source identity"),
        "validator": "pass",
        "emitter": "pass",
        "rendered_cpp_bytes": 17616,
        "rendered_cpp_sha256": (
            "ad46bd52432aef3e6921cd6dd7328830f03824af7ca2f4749995aaea10b17cab"),
    },
}


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


def all_nodes(program: TypedProgram):
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in walk_statement(statement, (index,)):
                yield function, item, parent, path, chain


def scalar_sites(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "binary"
            and item[1].operator in {"&", ">>"}
            and item[1].type.display() == "int"]


def global_reads(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "id"
            and getattr(item[1].symbol, "id", None) == 11]


def return_conversion(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "construct"
            and item[1].type.display() == "float"
            and len(item[1].children) == 1
            and item[1].children[0].kind == "id"
            and getattr(item[1].children[0].symbol, "name", None) == "bit"]


def row_assignments(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "assign"
            and item[1].operator == "="
            and len(item[1].children) == 2
            and getattr(item[1].children[0].symbol, "id", None) == 20]


def gx_clamps(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "builtin"
            and item[1].callee == "clamp"
            and len(item[1].children) == 3
            and getattr(item[1].children[0].symbol, "id", None) == 31]


def glyph_calls(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "call" and item[1].signature_id == 15]


def call_graph(program: TypedProgram) -> dict[str, tuple[str, ...]]:
    names = {function.id: function.name for function in program.functions}
    result: dict[str, tuple[str, ...]] = {}
    for function in program.functions:
        called: set[str] = set()
        for host, item, _, _, _ in all_nodes(program):
            if host is function and item.kind == "call":
                called.add(names[item.signature_id])
        result[function.name] = tuple(sorted(called))
    return result


def reaches(graph: dict[str, tuple[str, ...]], source: str, target: str) -> bool:
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


def first_error(action) -> str:
    try:
        action()
    except Exception as error:  # noqa: BLE001 - evidence freezes authority text
        return str(error).strip().splitlines()[0]
    return "pass"


def replace_scalar_ops(program: TypedProgram, operators: set[str]) -> TypedProgram:
    """Diagnostic-only bypass preserving node shape except the operator."""
    def expression(value: TypedExpression) -> TypedExpression:
        result = dataclasses.replace(
            value, children=tuple(expression(child) for child in value.children))
        if (result.kind == "binary" and result.operator in operators
                and result.type.display() == "int"):
            result = dataclasses.replace(result, operator="+")
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


def validate_and_emit(program: TypedProgram) -> tuple[str, str, str | None]:
    validator = first_error(lambda: gen.validate_capabilities(
        program, gen.APPROVED_CAPABILITIES, source_hash=RAW_SHA256))
    rendered: list[str] = []
    emitter = first_error(lambda: rendered.append(emit.render_typed_cpp(
        program, KEY, RAW_SHA256, "glyph_map_probe",
        "bind_glyph_map_probe")))
    return (validator, emitter,
            hashlib.sha256(rendered[0].encode()).hexdigest()
            if rendered else None)


def live_frontier(program: TypedProgram) -> dict[str, Any]:
    initial = validate_and_emit(program)
    mask = validate_and_emit(replace_scalar_ops(program, {"&"}))
    both_program = replace_scalar_ops(program, {"&", ">>"})
    both = validate_and_emit(both_program)
    rendered: list[str] = []
    if both[1] == "pass":
        rendered.append(emit.render_typed_cpp(
            both_program, KEY, RAW_SHA256, "glyph_map_probe",
            "bind_glyph_map_probe"))
    return {
        "typed_slice_programs_at_probe_time": len(gen.load_slice(ROOT)["programs"]),
        "validator_first_error": initial[0],
        "emitter_first_error": initial[1],
        "after_mask_bypass_validator": mask[0],
        "after_mask_bypass_emitter": mask[1],
        "diagnostic_bypass": {
            "method": CAPTURED_PRE_ADMISSION_FRONTIER["diagnostic_bypass"]["method"],
            "validator": both[0],
            "emitter": both[1],
            "rendered_cpp_bytes": len(rendered[0].encode()) if rendered else None,
            "rendered_cpp_sha256": both[2],
        },
    }


def identity_accepts(program: TypedProgram, *, key: str, raw_hash: str,
                     profile: str) -> bool:
    sites = scalar_sites(program)
    reads = global_reads(program)
    conversions = return_conversion(program)
    assignments = row_assignments(program)
    clamps = gx_clamps(program)
    calls = glyph_calls(program)
    host = next((item for item in program.functions if item.id == 15), None)
    declaration = next((item for item in program.declarations
                        if item.symbol.id == 11), None)
    proof = program.counted_loop_proof
    if (len(sites) != 2 or len(reads) != 3 or len(conversions) != 1
            or len(assignments) != 40 or len(clamps) != 1 or len(calls) != 1):
        return False
    mask = next((item for item in sites if item[1].operator == "&"), None)
    shift = next((item for item in sites if item[1].operator == ">>"), None)
    if mask is None or shift is None:
        return False
    return all((
        profile == PROFILE,
        key == KEY,
        raw_hash == RAW_SHA256,
        len(program.raw_source.encode()) == 7838,
        hashlib.sha256(program.raw_source.encode()).hexdigest() == RAW_SHA256,
        len(program.source.encode()) == 4939,
        hashlib.sha256(program.source.encode()).hexdigest() == NORMALIZED_SHA256,
        sha(program.functions) == FUNCTIONS_SHA256,
        whole(program) == WHOLE_SHA256,
        interface(program) == INTERFACE_SHA256,
        program.body_status == "analyzed",
        program.preprocessor_defines == (),
        program.structs == (),
        program.uniform_blocks == (),
        len(program.functions) == 4,
        host is not None,
        host is not None and (host.name, host.return_type.display(),
                              len(host.parameters), len(host.body), span(host))
        == ("glyphPixel", "float", 3, 4, "190:1-289:2"),
        declaration is not None,
        declaration is not None and
        (declaration.symbol.name, declaration.symbol.storage,
         declaration.type.display(), span(declaration), sha(declaration))
        == ("GLYPH_COUNT", "const", "int", "186:1-186:28",
            "f7b49cfb78c1c72d280c1120a7040e68031899ff4b5a57710ae38e8646704386"),
        declaration is not None and declaration.initializer.kind == "literal",
        declaration is not None and declaration.initializer.literal_value == 16,
        proof is not None,
        proof is not None and
        (proof.loop_count, proof.unproved_loop_count,
         proof.max_effective_depth, proof.max_lexical_product,
         proof.entrypoint_charge, proof.call_graph_acyclic)
        == (0, 0, 0, 0, 0, True),
        mask[0].id == shift[0].id == 15,
        span(mask[1]) == "287:16-287:35",
        sha(mask[1]) == "13b7e8039e75aa419da56f7ef88177d338c517f59c50bde9497165b098fdbb33",
        mask[1].children[0] is shift[1],
        mask[1].children[1].kind == "literal",
        mask[1].children[1].literal_value == 1,
        span(shift[1]) == "287:16-287:30",
        sha(shift[1]) == "532c26faeec29026185a9557f1173553d28752a77964835374dd94a4a476831b",
        shift[1].children[0].kind == "id",
        getattr(shift[1].children[0].symbol, "name", None) == "row",
        shift[1].children[1].kind == "binary",
        shift[1].children[1].operator == "-",
        sha(shift[1].children[1]) == "e0e9f7b40384f96ff80bcb109c300ebfb004584ef90d328194f0c4804a6e2882",
        sha(tuple(item[1] for item in assignments))
        == "05f32dbdd73f16e5a283dfde9535ac3469923bb9d6c6422a1f884f151b486455",
        tuple(sorted({item[1].children[1].literal_value
                      for item in assignments}))
        == (4, 9, 10, 11, 14, 16, 17, 19, 21, 22, 23, 25, 26, 27, 31),
        span(clamps[0][1]) == "309:10-309:25",
        sha(clamps[0][1]) == "d702374ee3b6f495c76840d0ed5858954b19fade833fa56c44acbfeb2c4dd81c",
        tuple(child.literal_value for child in clamps[0][1].children[1:])
        == (0, 4),
        span(calls[0][1]) == "331:22-331:50",
        sha(calls[0][1]) == "b9b6b899ee459bfca7d0eb1fc1ab9a621d5ad134d0624aa987b5b65dc274d6d1",
        tuple(getattr(child.symbol, "id", None)
              for child in calls[0][1].children) == (37, 31, 32),
        span(conversions[0][1]) == "288:12-288:22",
        sha(conversions[0][1]) == "9a729fd6e0b5e130b90ed981a2d5c1e0b9f9f7346cefec23f51640c0075e987a",
        tuple(span(item[1]) for item in reads)
        == ("319:43-319:54", "320:35-320:46", "325:52-325:63"),
    ))


def mutation_record(name: str, raw: str, anchor: str, replacement: str) -> dict:
    if raw.count(anchor) != 1:
        raise RuntimeError(f"{name}: mutation anchor count is {raw.count(anchor)}")
    mutated_raw = raw.replace(anchor, replacement)
    candidate = parse(mutated_raw)
    return {
        "name": name,
        "mutated_raw_sha256": hashlib.sha256(mutated_raw.encode()).hexdigest(),
        "scalar_sites": len(scalar_sites(candidate)),
        "global_reads": len(global_reads(candidate)),
        "independent_identity_accepts": identity_accepts(
            candidate, key=KEY,
            raw_hash=hashlib.sha256(mutated_raw.encode()).hexdigest(),
            profile=PROFILE),
    }


def build() -> dict[str, Any]:
    raw = SOURCE.read_text()
    program = parse(raw)
    graph = call_graph(program)
    if not identity_accepts(program, key=KEY, raw_hash=RAW_SHA256,
                            profile=PROFILE):
        raise RuntimeError("frozen Glyph Map identity no longer authenticates")
    if not reaches(graph, "main", "glyphPixel"):
        raise RuntimeError("glyphPixel is not reachable from main")

    mutations = [
        mutation_record("global-count-value", raw,
                        "const int GLYPH_COUNT = 16;",
                        "const int GLYPH_COUNT = 15;"),
        mutation_record("second-source-global-int", raw,
                        "const int GLYPH_COUNT = 16;",
                        "const int GLYPH_COUNT = 16;\nconst int EXTRA_COUNT = 1;"),
        mutation_record("nonempty-define-map", raw,
                        "#ifdef GL_ES",
                        "#define GLYPH_ORACLE_DRIFT 1\n#ifdef GL_ES"),
        mutation_record("mask-changed", raw,
                        "(row >> (4 - x)) & 1",
                        "(row >> (4 - x)) & 3"),
        mutation_record("shift-count-source", raw,
                        "row >> (4 - x)", "row >> x"),
        mutation_record("extra-scalar-shift", raw,
                        "int row = 0;", "int row = 0; int extra = row >> 1;"),
        mutation_record("return-route", raw,
                        "return float(bit);", "return float(bit + 1);"),
    ]
    if any(record["independent_identity_accepts"] for record in mutations):
        raise RuntimeError("a frontend mutation escaped Glyph Map identity")

    sites = scalar_sites(program)
    mask = next(item for item in sites if item[1].operator == "&")
    shift = next(item for item in sites if item[1].operator == ">>")
    reads = global_reads(program)
    declaration = next(item for item in program.declarations
                       if item.symbol.id == 11)
    assignments = row_assignments(program)
    clamp_node = gx_clamps(program)[0]
    call_node = glyph_calls(program)[0]
    conversion = return_conversion(program)[0]
    return {
        "schema": "noisemaker-for-cpp.glyph-map.frontend-proof.v1",
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
            "id": 15,
            "name": mask[0].name,
            "span": span(mask[0]),
            "return_type": mask[0].return_type.display(),
            "parameter_ids": [item.id for item in mask[0].parameters],
            "parameter_names": [item.name for item in mask[0].parameters],
            "parameter_types": [item.type.display() for item in mask[0].parameters],
            "call_graph": {name: list(targets)
                           for name, targets in sorted(graph.items())},
            "main_reaches_host": reaches(graph, "main", "glyphPixel"),
        },
        "global_constant": {
            "symbol_id": declaration.symbol.id,
            "name": declaration.symbol.name,
            "type": declaration.type.display(),
            "storage": declaration.symbol.storage,
            "span": span(declaration),
            "sha256": sha(declaration),
            "initializer_value": declaration.initializer.literal_value,
            "initializer_sha256": sha(declaration.initializer),
            "read_count": len(reads),
            "reads": [{"span": span(item), "node_sha256": sha(item),
                       "host": function.name, "path": list(path)}
                      for function, item, _, path, _ in reads],
        },
        "nodes": [
            {
                "role": role,
                "path_in_host": list(item[3]),
                "span": span(item[1]),
                "operator": item[1].operator,
                "result_type": item[1].type.display(),
                "node_sha256": sha(item[1]),
                "parent_kind": item[2].kind if item[2] is not None else None,
                "parent_operator": item[2].operator if item[2] is not None else None,
                "parent_span": span(item[2]) if item[2] is not None else None,
                "parent_sha256": sha(item[2]) if item[2] is not None else None,
                "child_kinds": [child.kind for child in item[1].children],
                "child_types": [child.type.display() for child in item[1].children],
                "child_sha256": [sha(child) for child in item[1].children],
                "statement_chain": [{"kind": ancestor.kind,
                                     "span": span(ancestor)}
                                    for ancestor in item[4]],
            }
            for role, item in (("mask-parent", mask), ("signed-shift", shift))
        ],
        "range_proof": {
            "row": "local row initializes to 0; all 40 later writes are authenticated literal assignments in 4..31",
            "row_assignment_count": len(assignments),
            "row_assignment_values": sorted({item[1].children[1].literal_value
                                             for item in assignments}),
            "row_assignments_sha256": sha(tuple(item[1] for item in assignments)),
            "x": "sole call passes gx; sole gx clamp is clamp(gx, 0, 4)",
            "gx_clamp": {
                "span": span(clamp_node[1]),
                "node_sha256": sha(clamp_node[1]),
                "parent_span": span(clamp_node[2]),
                "parent_sha256": sha(clamp_node[2]),
                "child_symbol_and_literals": [
                    getattr(clamp_node[1].children[0].symbol, "name", None),
                    clamp_node[1].children[1].literal_value,
                    clamp_node[1].children[2].literal_value,
                ],
            },
            "sole_glyph_call": {
                "span": span(call_node[1]),
                "node_sha256": sha(call_node[1]),
                "signature_id": call_node[1].signature_id,
                "argument_symbol_ids": [getattr(child.symbol, "id", None)
                                        for child in call_node[1].children],
                "argument_names": [getattr(child.symbol, "name", None)
                                   for child in call_node[1].children],
                "parent_span": span(call_node[2]),
                "parent_sha256": sha(call_node[2]),
            },
            "shift_count": "4 - x is 0..4",
            "mask": "literal 1",
            "shift_result": "immediate left child of the sole & node; no storage or escape",
            "materialization": {
                "description": "mask result initializes local int bit, then the sole float(bit) construct is returned",
                "return_construct_span": span(conversion[1]),
                "return_construct_sha256": sha(conversion[1]),
                "bit_symbol_id": conversion[1].children[0].symbol.id,
                "bit_read_sha256": sha(conversion[1].children[0]),
            },
        },
        "current_frontier": {
            "snapshot_kind": "captured-pre-admission-live174",
            "durability": (
                "frozen evidence; --live-frontier observes later admission "
                "without changing this oracle"),
            **CAPTURED_PRE_ADMISSION_FRONTIER,
        },
        "profile_boundary": {
            "required": (
                "parallel exact Glyph Map profile authenticating source global, "
                "shift, mask parent, range provenance, and return route by object identity"),
            "general_signed_shift_admitted": False,
            "general_scalar_int_mask_admitted": False,
            "capability_vocabulary_must_change": False,
            "cpp_lowering": (
                "std::int32_t arithmetic is safe only because the authenticated "
                "left operand is nonnegative and count is 0..4"),
        },
        "contract_negatives": [
            {"name": "wrong-profile", "accepted": identity_accepts(
                program, key=KEY, raw_hash=RAW_SHA256, profile="wrong")},
            {"name": "wrong-key", "accepted": identity_accepts(
                program, key="foreign:glyphMap", raw_hash=RAW_SHA256,
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
    elif "--check" in sys.argv:
        print("Glyph Map frontend proof ok "
              "(exact global + shift + mask + return identities authenticated)")
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
