from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import loop_proof


REPOSITORY = Path(".")
CORPUS = REPOSITORY / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
ORACLES = json.loads(Path("docs/port-engineering/task-23-oracles.json").read_text())
EXPECTED = {item["key"]: item for item in ORACLES["programs"]}


def digest(value: object) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


def function_hash(program) -> str:
    return digest(program.functions)


def whole_hash(program) -> str:
    return digest((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def interface_hash(program) -> str:
    return digest((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def expressions(value):
    for item in value.expressions:
        yield from expression(item)
    for child in value.children:
        yield from expressions(child)


def expression(value):
    yield value
    for child in value.children:
        yield from expression(child)


def statements(functions):
    def walk(value):
        yield value
        for child in value.children:
            yield from walk(child)
    for function in functions:
        for value in function.body:
            yield from walk(value)


def projected_functions(program, declaration):
    original = loop_proof._annotate_sequence
    seed = {
        declaration.symbol.id: (
            declaration.initializer.literal_value,
            "source-global-const-literal",
            declaration.symbol,
        )
    }

    def seeded(values, key, depth, ancestor_product, bounded):
        if depth == 0 and ancestor_product == 1 and not bounded:
            bounded = seed
        return original(values, key, depth, ancestor_product, bounded)

    loop_proof._annotate_sequence = seeded
    try:
        return loop_proof.attach_counted_loop_proofs(program.functions, program.key)
    finally:
        loop_proof._annotate_sequence = original


def verify_program(record):
    key = record["key"]
    raw = (CORPUS / record["source"]).read_text()
    parsed = parse_program(raw, key, dict(record["defines"]))
    pre = analyze_program(parsed, key)
    integer_globals = [
        item for item in pre.declarations
        if item.symbol.storage == "const" and item.type.display() == "int"
    ]
    assert len(integer_globals) == 1
    declaration = integer_globals[0]
    assert declaration.symbol.name == record["source_global_literal_int"]["symbol"]
    assert declaration.symbol.id == record["source_global_literal_int"]["symbol_id"]
    assert declaration.initializer.kind == "literal"
    assert declaration.initializer.literal_value == record["source_global_literal_int"]["value"]
    assert declaration.initializer.literal == str(record["source_global_literal_int"]["value"])
    assert not declaration.symbol.writable

    post_functions = projected_functions(pre, declaration)
    post = dataclasses.replace(
        pre,
        functions=post_functions,
        counted_loop_proof=loop_proof.summarize_counted_loop_proofs(post_functions),
    )

    actual = {
        "raw_bytes": len(raw.encode()),
        "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "normalized_sha256": hashlib.sha256(parsed["source"].encode()).hexdigest(),
        "pre_function_tuple_sha256": function_hash(pre),
        "post_function_tuple_sha256": function_hash(post),
        "pre_whole_program_sha256": whole_hash(pre),
        "post_whole_program_sha256": whole_hash(post),
        "interface_sha256_pre_and_post": interface_hash(pre),
    }
    for name, value in actual.items():
        expected_name = {
            "raw_bytes": "raw_source_bytes",
            "raw_sha256": "raw_source_sha256",
            "normalized_sha256": "normalized_source_sha256",
        }.get(name, name)
        assert value == record[expected_name], (key, name, value, record[expected_name])
    assert interface_hash(post) == actual["interface_sha256_pre_and_post"]
    assert (pre.counted_loop_proof.loop_count + pre.counted_loop_proof.unproved_loop_count
            == record["counted_loop_proof"]["count"])
    proof = post.counted_loop_proof
    expected_proof = record["counted_loop_proof"]
    assert proof.loop_count == expected_proof["count"]
    assert proof.unproved_loop_count == 0
    assert proof.max_effective_depth == expected_proof["max_depth"]
    assert proof.max_lexical_product == expected_proof["max_product"]
    assert proof.entrypoint_charge == expected_proof["entry_charge"]
    assert proof.call_graph_acyclic
    loop_rows = [item.loop_proof for item in statements(post.functions) if item.kind == "for"]
    assert [item.trip_count for item in loop_rows] == expected_proof["trip_caps"]
    assert all(item.bound_kind == "source-global-const-literal" for item in loop_rows if item.bound_value == declaration.initializer.literal_value)

    all_expressions = [item for function in pre.functions for statement in function.body for item in expressions(statement)]
    definitions = {function.signature.id: function for function in pre.functions if function.body}
    main = next(function for function in definitions.values() if function.name == "main")
    reachable = {main.signature.id}
    pending = [main.signature.id]
    while pending:
        owner = definitions[pending.pop()]
        for statement in owner.body:
            for item in expressions(statement):
                if (item.kind == "call" and item.signature_id in definitions
                        and item.signature_id not in reachable):
                    reachable.add(item.signature_id)
                    pending.append(item.signature_id)
    reachable_expressions = [
        item for signature_id in reachable for statement in definitions[signature_id].body
        for item in expressions(statement)
    ]
    reads = [item for item in all_expressions if item.kind == "id" and item.symbol_id == declaration.symbol.id]
    owners = []
    for function in pre.functions:
        if any(item.kind == "id" and item.symbol_id == declaration.symbol.id
               for statement in function.body for item in expressions(statement)):
            owners.append(function.name)
    assert reads
    texture_sites = sum(item.kind == "builtin" and item.callee in {"texture", "textureLod", "texelFetch"}
                        for item in reachable_expressions)
    static_expected = record["resource_fetch_bounds"].get(
        "static_texture_sites",
        record["resource_fetch_bounds"].get("static_texture_sites_in_resolved_MODE_0"),
    )
    assert texture_sites == static_expected, (key, texture_sites, static_expected)
    assert len(pre.resources.samplers) == 1 and len(pre.resources.outputs) == 1
    assert pre.resources.uses_texture and not pre.resources.uses_derivatives
    sampler_ordinals = {name: index + 1 for index, name in enumerate(pre.resources.samplers)}
    derived_bindings = []
    for item in pre.declarations:
        if item.symbol.storage == "uniform":
            suffix = f"/S{sampler_ordinals[item.symbol.name]}" if item.symbol.name in sampler_ordinals else ""
            derived_bindings.append(f"{item.symbol.name}:{item.type.display()}@{item.symbol.id}{suffix}")
        elif item.symbol.id == declaration.symbol.id:
            derived_bindings.append(f"{item.symbol.name}:const {item.type.display()}@{item.symbol.id}")
    outputs = [item for item in pre.declarations if item.symbol.storage == "output"]
    assert derived_bindings == record["binding_signature"], (key, derived_bindings, record["binding_signature"])
    assert len(outputs) == 1
    derived_output = f"{outputs[0].symbol.name}:{outputs[0].type.display()}@{outputs[0].symbol.id}"
    assert derived_output == record["output_signature"]
    non_interface = [
        item for item in pre.declarations
        if item.symbol.storage not in {"uniform", "output"}
    ]
    return {
        "key": key,
        **actual,
        "pre_proof": dataclasses.asdict(pre.counted_loop_proof),
        "post_proof": dataclasses.asdict(post.counted_loop_proof),
        "loop_rows": [dataclasses.asdict(item) for item in loop_rows],
        "resources": dataclasses.asdict(pre.resources),
        "binding_signature": derived_bindings,
        "output_signature": derived_output,
        "global_read_count": len(reads),
        "global_read_functions": owners,
        "non_interface_globals": [
            [item.symbol.name, item.type.display(), item.symbol.storage,
             item.initializer.literal if item.initializer else None]
            for item in non_interface
        ],
        "static_texture_sites": texture_sites,
    }


results = [verify_program(record) for record in ORACLES["programs"]]

slice_data = json.loads((REPOSITORY / "tools/glslcpp/typed_slice.json").read_text())
baseline = [item["program_key"] for item in slice_data["programs"]]
new_keys = [item["key"] for item in ORACLES["programs"]]
typed = sorted([*baseline, *new_keys])
public = sorted([*typed, "filter/invert:inv", "synth/solid:solid"])
manifest = json.loads((CORPUS / "manifest.json").read_text())
corpus_keys = sorted(item["program_key"] for item in manifest["programs"])
remaining = sorted(set(corpus_keys) - set(public))
assert len(baseline) == 116
assert len(typed) == 122 and len(public) == 124 and len(remaining) == 88 and len(corpus_keys) == 212
typed_hash = hashlib.sha256(("\n".join(typed) + "\n").encode()).hexdigest()
public_hash = hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest()
assert typed_hash == "9db3013a6b0f78d0b95fcb6713c54ace95e82d1545e796e7a380add23c009f0b"
assert public_hash == "2b84fff4d6f35aec1ac6bcc35188d9893e3194c90b9c428775a7308ce1f6281a"
expected_positions = {
    "filter/bloom:ntapGather": 7,
    "filter/directionalBlur:directionalBlur": 23,
    "filter/spinBlur:spinBlur": 77,
    "filter/strokes:stkSmear": 82,
    "filter/vaseline:upsample": 92,
    "filter/wind:wind": 96,
}
positions = {}
for key, position in expected_positions.items():
    assert typed[position] == key
    positions[key] = {"position": position, "previous": typed[position - 1], "next": typed[position + 1]}
assert "filter/reindex:nmReindexStats" in remaining

print(json.dumps({
    "programs": results,
    "publication": {
        "counts": {"baseline_typed": len(baseline), "typed": len(typed), "public": len(public),
                   "remaining": len(remaining), "corpus": len(corpus_keys)},
        "typed_sha256": typed_hash,
        "public_sha256": public_hash,
        "positions": positions,
        "reindex_excluded": "filter/reindex:nmReindexStats" in remaining,
    },
}, indent=2))
