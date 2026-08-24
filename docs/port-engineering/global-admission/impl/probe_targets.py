"""READ-ONLY probe over the live tree for the mat3 + linear/srgb lane-index
slice: filter/adjust, filter/colorspace, classicNoisedeck/cellNoise,
classicNoisedeck/colorLab. Gathers exact spans/hashes needed to build the
frozen lock tables for the new linear_srgb_lane_index_v1 profile and the
mat3 global-declaration admission. Never writes under tools/src/include/tests.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

CORPUS_ROOT = ROOT / "tools/glslcpp/corpus"
REVISION = sorted(p.name for p in CORPUS_ROOT.iterdir() if p.is_dir())[-1]
CORPUS = CORPUS_ROOT / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = [
    "filter/adjust:adjust",
    "filter/colorspace:colorspace",
    "classicNoisedeck/cellNoise:cellNoise",
    "classicNoisedeck/colorLab:colorLab",
]


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


def walk_expr(value, parent=None, child_index=None):
    yield value, parent, child_index
    for i, child in enumerate(value.children):
        yield from walk_expr(child, value, i)


def walk_stmt(value):
    for i, e in enumerate(value.expressions):
        yield from walk_expr(e, value, i)
    for c in value.children:
        yield from walk_stmt(c)


def load(key):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    parsed = parse_program(raw, key, defines)
    typed = analyze_program(parsed, key)
    return entry, raw, defines, typed


def call_graph_reachable(program):
    funcs_by_id = {f.id: f for f in program.functions}
    main_id = next((f.id for f in program.functions if f.name == "main"), None)
    if main_id is None:
        return set()
    seen = {main_id}
    frontier = [main_id]
    while frontier:
        fid = frontier.pop()
        fn = funcs_by_id.get(fid)
        if fn is None:
            continue
        for stmt in fn.body:
            for value, _parent, _idx in walk_stmt(stmt):
                if value.kind == "call" and value.signature_id is not None:
                    target = value.signature_id
                    if target not in seen and target in funcs_by_id:
                        seen.add(target)
                        frontier.append(target)
    return seen


def function_tuple(program):
    return tuple((f.id, f.name, len(f.body), sha(f)) for f in program.functions)


def declaration_report(program):
    out = []
    for decl in program.declarations:
        storage = decl.symbol.storage
        if storage in {"uniform", "output"}:
            continue
        out.append({
            "symbol_id": decl.symbol.id, "name": decl.symbol.name,
            "storage": storage, "type": decl.type.display(),
            "span": span(decl), "sha256": sha(decl),
            "initializer_kind": decl.initializer.kind if decl.initializer else None,
            "initializer_children": (
                [c.kind for c in decl.initializer.children] if decl.initializer else []),
            "initializer_child_literal_values": (
                [getattr(c, "literal_value", None) for c in decl.initializer.children]
                if decl.initializer else []),
        })
    return out


def index_node_report(program, reachable):
    out = []
    for fn in program.functions:
        for stmt in fn.body:
            for value, parent, child_index in walk_stmt(stmt):
                if value.kind not in ("index", "swizzle"):
                    continue
                base = value.children[0]
                out.append({
                    "kind": value.kind,
                    "owning_function_id": fn.id, "owning_function_name": fn.name,
                    "owning_function_reachable": fn.id in reachable,
                    "span": span(value), "sha256": sha(value),
                    "type": value.type.display(), "category": value.category,
                    "base_kind": base.kind, "base_symbol_id": getattr(base, "symbol_id", None),
                    "base_name": getattr(base.symbol, "name", None) if getattr(base, "symbol", None) else None,
                    "base_type": base.type.display(),
                    "index_or_member": (
                        getattr(value.children[1], "symbol_id", None) if value.kind == "index"
                        and value.children[1].kind == "id" else
                        getattr(value.children[1], "literal_value", None) if value.kind == "index"
                        else getattr(value, "member", None)),
                    "parent_kind": parent.kind if parent is not None else None,
                    "parent_operator": getattr(parent, "operator", None) if parent is not None else None,
                    "parent_span": span(parent) if parent is not None else None,
                    "child_index_in_parent": child_index,
                })
    return out


def find_function(program, name):
    matches = [f for f in program.functions if f.name == name]
    return matches[0] if matches else None


def loop_report(fn):
    out = []
    for i, stmt in enumerate(fn.body):
        if stmt.kind == "for":
            proof = stmt.loop_proof
            out.append({
                "body_index": i, "span": span(stmt),
                "proof": None if proof is None else {
                    "start_value": proof.start_value, "bound_value": proof.bound_value,
                    "comparison": proof.comparison, "update": proof.update,
                    "trip_count": proof.trip_count,
                    "induction_symbol_id": proof.induction_symbol_id,
                },
            })
    return out


def main():
    out = {}
    for key in KEYS:
        entry, raw, defines, typed = load(key)
        raw_bytes = raw.encode("utf-8")
        norm_bytes = typed.source.encode("utf-8")
        reachable = call_graph_reachable(typed)
        proof = typed.counted_loop_proof
        entry_out = {
            "manifest_entry": entry, "defines": defines,
            "raw_bytes": len(raw_bytes), "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "normalized_bytes": len(norm_bytes), "normalized_sha256": hashlib.sha256(norm_bytes).hexdigest(),
            "function_count": len(typed.functions),
            "function_tuple_sha256": sha(function_tuple(typed)),
            "whole_sha256": whole(typed), "interface_sha256": interface(typed),
            "loop_proof": None if proof is None else {
                "loop_count": proof.loop_count, "unproved_loop_count": proof.unproved_loop_count,
                "max_effective_depth": proof.max_effective_depth,
                "max_lexical_product": proof.max_lexical_product,
                "entrypoint_charge": proof.entrypoint_charge,
                "call_graph_acyclic": proof.call_graph_acyclic,
            },
            "reachable_function_ids": sorted(reachable),
            "reachable_function_names": sorted(f.name for f in typed.functions if f.id in reachable),
            "declarations": declaration_report(typed),
            "index_nodes": index_node_report(typed, reachable),
            "functions": [
                {"id": f.id, "name": f.name, "body_len": len(f.body),
                 "loops": loop_report(f)}
                for f in typed.functions
            ],
        }
        out[key] = entry_out
        print(f"=== {key} ===", file=sys.stderr)
        print(f"  raw {entry_out['raw_bytes']}B sha256={entry_out['raw_sha256']}", file=sys.stderr)
        print(f"  functions: {[(f['id'], f['name'], f['body_len']) for f in entry_out['functions']]}", file=sys.stderr)
        for d in entry_out["declarations"]:
            print(f"  decl {d['name']}: type={d['type']} storage={d['storage']} initializer={d['initializer_kind']}", file=sys.stderr)
        for n in entry_out["index_nodes"]:
            print(f"  {n['kind']} {n['span']} fn={n['owning_function_name']} base={n['base_name']}:{n['base_type']} idx/member={n['index_or_member']} parent={n['parent_kind']}/{n['parent_operator']}", file=sys.stderr)

    Path("docs/port-engineering/global-admission/impl/probe_targets_output.json").write_text(
        json.dumps(out, indent=1, default=str))
    print("wrote probe_targets_output.json", file=sys.stderr)


if __name__ == "__main__":
    main()
