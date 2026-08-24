from __future__ import annotations

import collections
import dataclasses
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(".")
CPU = Path("../noisemaker-for-cpu")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import emit_typed_cpp as emit
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {item["program_key"]: item for item in MANIFEST["programs"]}
SPEC = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text())
KEY = "mixer/focusBlur:focusBlur"
PROFILE = "focus-blur-borrowed-sampler-parameters-v1"
MANUAL = ("filter/invert:inv", "synth/solid:solid")


def digest(value: object) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def list_sha256(values: list[str]) -> str:
    return hashlib.sha256(("\n".join(values) + "\n").encode()).hexdigest()


def span(value: object) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


def whole(program: object) -> str:
    return digest((program.key, program.source, program.raw_source,
                   program.declarations, program.functions, program.resources,
                   program.body_status, program.local_type_names, program.structs,
                   program.uniform_blocks, program.interface_symbols,
                   program.builtin_symbols, program.counted_loop_proof,
                   program.preprocessor_defines))


def interface(program: object) -> str:
    return digest((program.declarations, program.resources,
                   program.local_type_names, program.structs,
                   program.uniform_blocks, program.interface_symbols,
                   program.builtin_symbols, program.preprocessor_defines))


def expression_nodes(value: object, path: tuple[object, ...],
                     ancestors: tuple[tuple[tuple[object, ...], object, int | None], ...] = (),
                     child_index: int | None = None):
    yield path, value, ancestors, child_index
    for ordinal, child in enumerate(value.children):
        yield from expression_nodes(
            child, (*path, ordinal), (*ancestors, (path, value, child_index)), ordinal)


def statement_nodes(
        value: object, path: tuple[object, ...],
        ancestors: tuple[tuple[tuple[object, ...], object, int | None], ...] = (),
        child_index: int | None = None):
    statement_chain = (*ancestors, (path, value, child_index))
    for ordinal, expression in enumerate(value.expressions):
        for expression_path, node, expression_chain, expression_child_index in \
                expression_nodes(expression, (*path, f"e{ordinal}", 0)):
            yield (expression_path, node, expression_chain,
                   expression_child_index, statement_chain)
    for ordinal, child in enumerate(value.children):
        yield from statement_nodes(
            child, (*path, f"s{ordinal}"), statement_chain, ordinal)


def nodes(function: object):
    for ordinal, statement in enumerate(function.body):
        yield from statement_nodes(statement, (ordinal,))


def expression_chain_record(chain):
    return [{
        "path": path, "kind": value.kind, "span": span(value),
        "sha256": digest(value), "child_index_from_parent": child_index,
    } for path, value, child_index in chain]


def statement_chain_record(chain):
    return [{
        "path": path, "kind": value.kind, "span": span(value),
        "sha256": digest(value), "child_index_from_parent": child_index,
        "statement_count": len(value.children),
        "expression_count": len(value.expressions),
    } for path, value, child_index in chain]


def typed(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    return analyze_program(parse_program(raw, key, defines), key), entry, raw, defines


def binding_signature(program: object) -> list[str]:
    sampler_bindings = {name: ordinal + 1
                        for ordinal, name in enumerate(program.resources.samplers)}
    result = []
    for declaration in program.declarations:
        symbol = declaration.symbol
        if symbol.storage == "uniform":
            suffix = (f"/S{sampler_bindings[symbol.name]}"
                      if symbol.name in sampler_bindings else "")
            result.append(f"{symbol.name}:{declaration.type.display()}@{symbol.id}{suffix}")
        elif symbol.storage == "output":
            result.append(f"{symbol.name}:{declaration.type.display()}@{symbol.id}/out")
    return result


def public_identity() -> dict[str, object]:
    script = f"""
import crypto from 'node:crypto';
import fs from 'node:fs';
import {{ canonicalAdapterFactories, canonicalKernelFactories, kernelFactories }} from '{CPU}/src/effects/catalog.js';
const h = v => crypto.createHash('sha256').update(v).digest('hex');
const key = '{KEY}'; const c = canonicalKernelFactories[key];
console.log(JSON.stringify({{
  canonical_kernels_sha256: h(fs.readFileSync('{CPU}/src/effects/generated/canonical-kernels.js')),
  public_catalog_sha256: h(fs.readFileSync('{CPU}/src/effects/catalog.js')),
  adapter_index_sha256: h(fs.readFileSync('{CPU}/src/effects/adapters/index.js')),
  canonical_factory_name: c.name,
  canonical_factory_to_string_sha256: h(c.toString()),
  public_is_canonical_identity: kernelFactories.get(key) === c,
  adapter_absent: canonicalAdapterFactories[key] === undefined,
}}));
"""
    output = subprocess.run(
        ["node", "--input-type=module", "-e", script], check=True,
        capture_output=True, text=True).stdout
    return json.loads(output)


typed_keys = [item["program_key"] for item in SPEC["programs"]]
public_keys = sorted((*typed_keys, *MANUAL))
projected_typed = sorted((*typed_keys, KEY))
projected_public = sorted((*projected_typed, *MANUAL))
corpus_keys = [item["program_key"] for item in MANIFEST["programs"]]
remaining = [key for key in corpus_keys if key not in set(typed_keys)]

candidate_rows = []
validator_histogram: collections.Counter[str] = collections.Counter()
emitter_passes = []
for candidate_key in remaining:
    try:
        candidate, candidate_entry, _, _ = typed(candidate_key)
    except Exception as error:
        candidate_rows.append({"key": candidate_key, "stage": "analyzer",
                               "error": str(error)})
        validator_histogram[f"analyzer: {error}"] += 1
        continue
    try:
        gen.validate_capabilities(candidate, tuple(gen.APPROVED_CAPABILITIES),
                                  source_hash=candidate_entry["raw_sha256"])
        validator = "pass"
    except Exception as error:
        validator = str(error)
    try:
        emit.render_typed_cpp(candidate, candidate_key,
                              candidate_entry["raw_sha256"],
                              "task29_probe", "bind_task29_probe")
        emitter = "pass"
        emitter_passes.append(candidate_key)
    except Exception as error:
        emitter = str(error)
    category = validator.split(": ", 1)[-1]
    validator_histogram[category] += 1
    if validator == "pass" or emitter == "pass" or candidate_key == KEY:
        candidate_rows.append({"key": candidate_key, "validator": validator,
                               "emitter": emitter})

program, entry, raw, defines = typed(KEY)
functions = {function.name: function for function in program.functions}
helper = functions["applyFocusBlur"]
main = functions["main"]
helper_nodes = list(nodes(helper))
main_nodes = list(nodes(main))
calls = [(path, value, expression_chain, child_index, statement_chain)
         for path, value, expression_chain, child_index, statement_chain in main_nodes
         if value.kind == "call" and value.signature_id == helper.signature.id]
sampler_parameter_ids = tuple(parameter.id for parameter in helper.parameters
                              if parameter.type.display() == "sampler2D")
sampler_parameter_uses = []
for path_value, value, expression_chain, child_index, statement_chain in helper_nodes:
    if value.kind == "id" and value.symbol_id in sampler_parameter_ids:
        parent = expression_chain[-1][1]
        sampler_parameter_uses.append({
            "path": path_value, "span": span(value), "sha256": digest(value),
            "symbol_id": value.symbol_id, "parent_kind": parent.kind,
            "parent_signature_id": parent.signature_id,
            "parent_child_index": child_index,
            "parent_sha256": digest(parent),
        })

texture_sites = []
texture_size_sites = []
for function in program.functions:
    for path_value, value, expression_chain, child_index, statement_chain in nodes(function):
        if value.kind == "builtin" and value.signature_id == -46:
            texture_sites.append({"owner_id": function.signature.id,
                                  "owner": function.name, "path": path_value,
                                  "span": span(value), "sha256": digest(value),
                                  "sampler_symbol_id": value.children[0].symbol_id})
        if value.kind == "builtin" and value.signature_id == -48:
            texture_size_sites.append({"owner_id": function.signature.id,
                                       "owner": function.name, "path": path_value,
                                       "span": span(value), "sha256": digest(value),
                                       "sampler_symbol_id": value.children[0].symbol_id})

call_records = []
conditional_objects = []
for path_value, value, expression_chain, child_index, statement_chain in calls:
    enclosing_if_positions = [ordinal for ordinal, (_, statement, _) in
                              enumerate(statement_chain)
                              if statement.kind == "if"]
    if len(enclosing_if_positions) != 1:
        raise AssertionError("each Focus helper call must have exactly one enclosing if")
    if_position = enclosing_if_positions[0]
    if if_position + 1 >= len(statement_chain):
        raise AssertionError("Focus helper call must belong to an if branch")
    conditional_path, conditional, _ = statement_chain[if_position]
    branch_path, branch, branch_ordinal = statement_chain[if_position + 1]
    if branch_ordinal not in (0, 1) or branch is not conditional.children[branch_ordinal]:
        raise AssertionError("Focus helper call branch ownership is not direct/authentic")
    if len(conditional.expressions) != 1 or len(conditional.children) != 2:
        raise AssertionError("Focus conditional shape drift")
    predicate = conditional.expressions[0]
    predicate_path = (*conditional_path, "e0", 0)
    parent = expression_chain[-1][1]
    conditional_objects.append(conditional)
    call_records.append({
        "path": path_value, "span": span(value), "sha256": digest(value),
        "signature_id": value.signature_id,
        "argument_symbol_ids": [child.symbol_id for child in value.children],
        "argument_types": [child.type.display() for child in value.children],
        "argument_hashes": [digest(child) for child in value.children],
        "parent_kind": parent.kind, "parent_sha256": digest(parent),
        "parent_child_index": child_index,
        "expression_parent_chain": expression_chain_record(expression_chain),
        "statement_parent_chain": statement_chain_record(statement_chain),
        "enclosing_if_path": conditional_path,
        "enclosing_if_kind": conditional.kind,
        "enclosing_if_span": span(conditional),
        "enclosing_if_sha256": digest(conditional),
        "predicate_path": predicate_path, "predicate_kind": predicate.kind,
        "predicate_operator": predicate.operator, "predicate_type": predicate.type.display(),
        "predicate_span": span(predicate), "predicate_sha256": digest(predicate),
        "predicate_child_symbol_ids": [child.symbol_id for child in predicate.children],
        "predicate_child_kinds": [child.kind for child in predicate.children],
        "predicate_child_types": [child.type.display() for child in predicate.children],
        "predicate_child_literals": [child.literal_value for child in predicate.children],
        "predicate_child_hashes": [digest(child) for child in predicate.children],
        "branch_ordinal": branch_ordinal,
        "branch_slot": "then" if branch_ordinal == 0 else "else",
        "branch_path": branch_path,
        "branch_kind": branch.kind, "branch_span": span(branch),
        "branch_sha256": digest(branch),
        "branch_statement_count": len(branch.children),
        "branch_expression_count": len(branch.expressions),
    })

if len(calls) != 2 or len({id(value) for value in conditional_objects}) != 1:
    raise AssertionError("Focus calls must share one exact conditional object")
conditional = conditional_objects[0]
predicate = conditional.expressions[0]
branches = conditional.children
branch_call_counts = [sum(record["branch_ordinal"] == ordinal
                          for record in call_records) for ordinal in range(2)]
if branch_call_counts != [1, 1] or {record["branch_ordinal"] for record in call_records} != {0, 1}:
    raise AssertionError("Focus conditional must own one helper call per branch")
if any(record["enclosing_if_sha256"] != digest(conditional)
       for record in call_records):
    raise AssertionError("Focus helper call escaped authenticated conditional")
call_records.sort(key=lambda record: record["branch_ordinal"])

profile_tuple = (
    PROFILE, KEY, entry["raw_sha256"], (), "glsl-f32",
    digest(program.functions), whole(program), interface(program),
    (helper.signature.id, helper.name, digest(helper.signature), digest(helper),
     span(helper), len(helper.body),
     tuple((parameter.id, parameter.name, parameter.type.display(),
            parameter.direction, span(parameter), digest(parameter))
           for parameter in helper.parameters)),
    tuple((record["path"], record["span"], record["sha256"],
           record["symbol_id"], record["parent_kind"],
           record["parent_signature_id"], record["parent_child_index"],
           record["parent_sha256"])
          for record in sampler_parameter_uses),
    tuple((record["path"], record["span"], record["sha256"],
           record["signature_id"], tuple(record["argument_symbol_ids"]),
           tuple(record["argument_types"]), tuple(record["argument_hashes"]),
           record["parent_kind"], record["parent_child_index"],
           record["parent_sha256"],
           tuple((tuple(frame["path"]), frame["kind"], frame["span"],
                  frame["sha256"], frame["child_index_from_parent"])
                 for frame in record["expression_parent_chain"]),
           tuple((tuple(frame["path"]), frame["kind"], frame["span"],
                  frame["sha256"], frame["child_index_from_parent"],
                  frame["statement_count"], frame["expression_count"])
                 for frame in record["statement_parent_chain"]),
           tuple(record["enclosing_if_path"]),
           record["enclosing_if_kind"], record["enclosing_if_span"],
           record["enclosing_if_sha256"], tuple(record["predicate_path"]),
           record["predicate_kind"], record["predicate_operator"],
           record["predicate_type"], record["predicate_span"],
           record["predicate_sha256"],
           tuple(record["predicate_child_symbol_ids"]),
           tuple(record["predicate_child_kinds"]),
           tuple(record["predicate_child_types"]),
           tuple(record["predicate_child_literals"]),
           tuple(record["predicate_child_hashes"]), record["branch_ordinal"],
           record["branch_slot"],
           tuple(record["branch_path"]), record["branch_kind"],
           record["branch_span"], record["branch_sha256"],
           record["branch_statement_count"], record["branch_expression_count"])
          for record in call_records),
    tuple((record["owner_id"], record["path"], record["span"],
           record["sha256"], record["sampler_symbol_id"])
          for record in texture_sites),
    tuple((record["owner_id"], record["path"], record["span"],
           record["sha256"], record["sampler_symbol_id"])
          for record in texture_size_sites),
    dataclasses.asdict(program.counted_loop_proof),
)

result = {
    "schema": "noisemaker-for-cpp.task-29-recompute.v1",
    "corpus_revision": REVISION,
    "baseline": {
        "corpus_count": len(corpus_keys), "typed_count": len(typed_keys),
        "public_count": len(public_keys),
        "publicly_unported_count": len(set(corpus_keys) - set(public_keys)),
        "typed_ordered_sha256": list_sha256(typed_keys),
        "public_ordered_sha256": list_sha256(public_keys),
        "typed_order_is_sorted": typed_keys == sorted(typed_keys),
    },
    "projected": {
        "typed_count": len(projected_typed),
        "public_count": len(projected_public),
        "publicly_unported_count": len(set(corpus_keys) - set(projected_public)),
        "typed_ordered_sha256": list_sha256(projected_typed),
        "public_ordered_sha256": list_sha256(projected_public),
        "typed_zero_based_position": projected_typed.index(KEY),
        "typed_neighbors": projected_typed[
            projected_typed.index(KEY) - 1:projected_typed.index(KEY) + 2],
    },
    "remaining_frontier": {
        "absent_from_typed_count_including_two_manual_programs": len(remaining),
        "publicly_unported_count": len(set(corpus_keys) - set(public_keys)),
        "emitter_passes": emitter_passes,
        "validator_first_blocker_histogram":
            dict(sorted(validator_histogram.items())),
        "distinguishing_rows": candidate_rows,
    },
    "focus_blur": {
        "key": KEY, "source": entry["source"],
        "raw_bytes": len(raw.encode()),
        "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "normalized_bytes": len(program.source.encode()),
        "normalized_sha256": hashlib.sha256(program.source.encode()).hexdigest(),
        "defines": defines, "numeric_contract": "glsl-f32",
        "function_count": len(program.functions),
        "function_tuple_sha256": digest(program.functions),
        "whole_program_sha256": whole(program),
        "interface_sha256": interface(program),
        "binding_signature": binding_signature(program),
        "resources": dataclasses.asdict(program.resources),
        "loop_proof": dataclasses.asdict(program.counted_loop_proof),
        "functions": [{
            "id": function.signature.id, "name": function.name,
            "return_type": function.return_type.display(),
            "signature_sha256": digest(function.signature),
            "body_statements": len(function.body),
            "body_sha256": digest(function), "span": span(function),
            "parameters": [[parameter.id, parameter.name,
                            parameter.type.display(), parameter.direction,
                            span(parameter), digest(parameter)]
                           for parameter in function.parameters],
        } for function in program.functions],
        "helper": {
            "id": helper.signature.id, "name": helper.name,
            "signature_sha256": digest(helper.signature),
            "body_sha256": digest(helper), "span": span(helper),
            "body_statements": len(helper.body),
            "sampler_parameter_ids": sampler_parameter_ids,
            "sampler_parameter_uses": sampler_parameter_uses,
            "sampler_parameter_assignments": 0,
            "sampler_parameter_returns": 0,
            "sampler_parameter_aggregate_uses": 0,
        },
        "calls": call_records,
        "conditional_call_proof": {
            "if_path": call_records[0]["enclosing_if_path"],
            "if_kind": conditional.kind,
            "if_span": span(conditional),
            "if_sha256": digest(conditional),
            "predicate_path": call_records[0]["predicate_path"],
            "predicate_kind": predicate.kind,
            "predicate_type": predicate.type.display(),
            "predicate_span": span(predicate),
            "predicate_sha256": digest(predicate),
            "predicate_operator": predicate.operator,
            "predicate_child_symbol_ids": [child.symbol_id for child in predicate.children],
            "predicate_child_kinds": [child.kind for child in predicate.children],
            "predicate_child_types": [child.type.display() for child in predicate.children],
            "predicate_child_literals": [child.literal_value for child in predicate.children],
            "predicate_child_hashes": [digest(child) for child in predicate.children],
            "branches": [{
                "ordinal": ordinal,
                "slot": "then" if ordinal == 0 else "else",
                "path": call_records[ordinal]["branch_path"],
                "kind": branch.kind,
                "span": span(branch),
                "sha256": digest(branch),
                "statement_count": len(branch.children),
                "expression_count": len(branch.expressions),
                "owned_helper_call_sha256": call_records[ordinal]["sha256"],
                "helper_call_count": branch_call_counts[ordinal],
            } for ordinal, branch in enumerate(branches)],
            "branch_count": len(branches),
            "calls_per_branch": branch_call_counts,
            "all_helper_calls_owned_by_conditional": len(calls) == sum(branch_call_counts),
            "dynamic_calls_per_pixel": min(branch_call_counts),
            "dynamic_calls_per_pixel_max": max(branch_call_counts),
            "exactly_one_dynamic_call": branch_call_counts == [1, 1],
            "mutually_exclusive": conditional.kind == "if" and len(branches) == 2,
            "mutation_controls": {
                "predicate_change": "reject predicate object/hash/operator/children",
                "predicate_reconstruction": "reject forged old predicate object; authenticate candidate-owned object",
                "branch_swap": "reject slot/path/call ownership and argument-order mismatch",
                "call_move_outside": "reject absent enclosing-if ancestry",
                "call_copy_same_branch": "reject branch call cardinality [2,1] or [1,2]",
                "call_copy_both_executed": "reject any path with dynamic call min/max other than 1/1",
                "call_swap_between_branches": "reject branch-owned call hash/order tuple",
            },
        },
        "texture_sites": texture_sites,
        "texture_size_sites": texture_size_sites,
        "static_texture_site_count": len(texture_sites),
        "static_texture_size_site_count": len(texture_size_sites),
        "dynamic_texture_reads_max_path": 67,
        "read_derivation": "1 depth + 64 scene loop + 2 alpha",
        "profile_tuple_sha256": digest(profile_tuple),
        "profile_tuple_repr": repr(profile_tuple),
        "validator": next(row["validator"] for row in candidate_rows
                          if row["key"] == KEY),
        "emitter": next(row["emitter"] for row in candidate_rows
                        if row["key"] == KEY),
        "public_identity": public_identity(),
    },
    "accepted_task28_file_hashes": {
        path: file_sha256(ROOT / path) for path in (
            "tools/glslcpp/frontend/rotate_mat2_return_profile.py",
            "tools/glslcpp/frontend/perlin_scalar_uint_xor_profile.py",
            "tools/glslcpp/generate_typed_slice.py",
            "tools/glslcpp/emit_typed_cpp.py",
            "tools/glslcpp/typed_slice.json",
            "tests/test_typed_generator.py",
            "tests/test_generated_kernels.cpp",
            "tests/test_typed_slice.cpp",
            "src/typed_generated/typed_slice.cpp",
            "src/typed_generated/typed_manifest.json",
            "include/noisemaker/generated/catalog.hpp",
            "include/noisemaker/glsl_types.hpp",
            "CMakeLists.txt",
        )
    },
}

payload = json.dumps(result, indent=2) + "\n"
if "--write" in sys.argv:
    Path("docs/port-engineering/task-29-recomputed.json").write_text(payload)
elif "--check" in sys.argv:
    expected = Path("docs/port-engineering/task-29-recomputed.json")
    if expected.read_text() != payload:
        raise SystemExit("Task29 recomputation drift")
    print("Task29 recomputation ok")
else:
    print(payload, end="")
