"""Compute the exact frozen identity fields for the as_u32-round-admission-v1
profile, for a given program key. Read-only: never writes under tools/src/
include/tests. Run against the LIVE (already globally-widened) tree.
"""
from __future__ import annotations
import hashlib, json, pathlib, sys

ROOT = pathlib.Path('.')
sys.path.insert(0, str(ROOT))
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}


def sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def span(value) -> str:
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


def whole(program) -> str:
    return sha((program.key, program.source, program.raw_source,
                program.declarations, program.functions, program.resources,
                program.body_status, program.local_type_names, program.structs,
                program.uniform_blocks, program.interface_symbols,
                program.builtin_symbols, program.counted_loop_proof,
                program.preprocessor_defines))


def interface(program) -> str:
    return sha((program.declarations, program.resources,
                program.local_type_names, program.structs,
                program.uniform_blocks, program.interface_symbols,
                program.builtin_symbols, program.preprocessor_defines))


def compute(key: str) -> dict:
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    parsed = parse_program(raw, key, defines)
    program = analyze_program(parsed, key)

    as_u32 = next(f for f in program.functions if f.name == "as_u32")
    assert len(as_u32.body) == 1
    ret_stmt = as_u32.body[0]
    assert ret_stmt.kind == "return", ret_stmt.kind
    uint_construct = ret_stmt.expressions[0]
    assert uint_construct.kind == "construct" and uint_construct.type.display() == "uint"
    max_call = uint_construct.children[0]
    assert max_call.kind == "builtin" and max_call.callee == "max"
    round_call = max_call.children[0]
    assert round_call.kind == "builtin" and round_call.callee == "round"

    functions_sorted = tuple(sorted(program.functions, key=lambda item: item.id))
    function_inventory = tuple(
        (item.id, item.name, item.return_type.display(), len(item.parameters),
         len(item.body), span(item)) for item in functions_sorted)

    bindings = tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable)
        for item in program.declarations)
    resources = program.resources

    profile = {
        "raw_bytes": len(program.raw_source.encode("utf-8")),
        "raw_sha256": hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest(),
        "normalized_bytes": len(program.source.encode("utf-8")),
        "normalized_sha256": hashlib.sha256(program.source.encode("utf-8")).hexdigest(),
        "functions_sha256": sha(program.functions),
        "whole_program_sha256": whole(program),
        "interface_sha256": interface(program),
        "as_u32_id": as_u32.id,
        "as_u32_span": span(as_u32),
        "function_inventory": function_inventory,
        "return_stmt_span": span(ret_stmt),
        "return_stmt_sha256": sha(ret_stmt),
        "uint_construct_span": span(uint_construct),
        "uint_construct_sha256": sha(uint_construct),
        "max_call_span": span(max_call),
        "max_call_sha256": sha(max_call),
        "max_sibling_sha256": sha(max_call.children[1]),
        "round_span": span(round_call),
        "round_sha256": sha(round_call),
        "round_argument_sha256": sha(round_call.children[0]),
        "round_signature_id": round_call.signature_id,
        "bindings": bindings,
        "resources": ((resources.uniforms, resources.samplers, resources.outputs,
                        resources.uses_texture, resources.uses_derivatives)),
        "structs_empty": program.structs == (),
        "uniform_blocks_empty": program.uniform_blocks == (),
        "defines": tuple((item.name, item.kind, item.canonical_value)
                          for item in program.preprocessor_defines),
    }
    return profile


if __name__ == "__main__":
    out = {}
    for key in ["filter/grain:grain", "filter/snow:snow", "filter/fxaa:fxaa"]:
        out[key] = compute(key)
    print(json.dumps(out, indent=2, default=str))
