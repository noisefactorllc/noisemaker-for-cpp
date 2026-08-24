"""Extract the exact frozen constants the Extrude profile must lock."""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
KEY = "synth/curl:curl"
ENTRY = {r["program_key"]: r
         for r in json.loads((CORPUS / "manifest.json").read_text())["programs"]}[KEY]


def sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def span(value: object) -> str:
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


def whole(p) -> str:
    return sha((p.key, p.source, p.raw_source, p.declarations, p.functions,
                p.resources, p.body_status, p.local_type_names, p.structs,
                p.uniform_blocks, p.interface_symbols, p.builtin_symbols,
                p.counted_loop_proof, p.preprocessor_defines))


def interface(p) -> str:
    return sha((p.declarations, p.resources, p.local_type_names, p.structs,
                p.uniform_blocks, p.interface_symbols, p.builtin_symbols,
                p.preprocessor_defines))


def walk_expr(value, parent=None, path=()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from walk_expr(child, value, (*path, index))


def walk_stmt(value, path=(), ancestors=()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, epath in walk_expr(expression, None, (*path, f"e{index}")):
            yield item, parent, epath, chain
    for index, child in enumerate(value.children):
        yield from walk_stmt(child, (*path, f"s{index}"), chain)


raw = (CORPUS / ENTRY["source"]).read_text()
defines = gen._defaults(ROOT, KEY)
program = analyze_program(parse_program(raw, KEY, defines), KEY)

raw_b = program.raw_source.encode()
norm_b = program.source.encode()

print("=== identity ===")
print("defines            :", defines)
print("preprocessor_defines:", program.preprocessor_defines)
print("raw bytes/sha      :", len(raw_b), hashlib.sha256(raw_b).hexdigest())
print("norm bytes/sha     :", len(norm_b), hashlib.sha256(norm_b).hexdigest())
print("functions sha      :", sha(program.functions))
print("whole sha          :", whole(program))
print("interface sha      :", interface(program))
print("body_status        :", program.body_status)
print("function count     :", len(program.functions))
print("structs/blocks     :", program.structs, program.uniform_blocks)

proof = program.counted_loop_proof
print("loop proof         :", (proof.loop_count, proof.unproved_loop_count,
                               proof.max_effective_depth, proof.max_lexical_product,
                               proof.entrypoint_charge, proof.call_graph_acyclic))

r = program.resources
print("resources          :", (r.uniforms, r.samplers, r.outputs,
                               r.uses_texture, r.uses_derivatives))

optional = ("fixed_nine_table_proof", "fixed_grid_counter_store_proof",
            "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof")
print("optional carriers  :", {f: getattr(program, f, None) is not None for f in optional})

print()
print("=== functions ===")
for f in program.functions:
    print(f"  id={f.id:3d} {f.name:24s} ret={f.return_type.display():8s} "
          f"params={len(f.parameters)} body={len(f.body)} span={span(f)}")

print()
print("=== tanh/mod sites ===")
for f in program.functions:
    for statement in f.body:
        for item, parent, epath, chain in walk_stmt(statement):
            if item.kind == "builtin" and item.callee in ("tanh","mod"):
                print(f"  fn={f.id} callee={item.callee:14s} span={span(item)} "
                      f"type={item.type.display():6s} children={len(item.children)} "
                      f"sha={sha(item)}")
                print(f"      parent={None if parent is None else parent.kind} "
                      f"childtypes={[c.type.display() for c in item.children]}")

print()
print("=== scalar XOR sites ===")
for f in program.functions:
    for statement in f.body:
        for item, parent, epath, chain in walk_stmt(statement):

            if False:
                print(f"  fn={f.id} op=^ type={item.type.display()} span={span(item)} "
                      f"childtypes={[c.type.display() for c in item.children]} sha={sha(item)}")
