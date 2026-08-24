"""READ-ONLY probe for Task 32 (filter/grade cluster) design brief.

Re-derives, independently, for all six filter/grade:* programs:
- raw/normalized bytes + SHA-256
- exact defines (from metadata.json, via gen._defaults)
- function count / tuple SHA-256, whole-program SHA-256, interface SHA-256
  (using the same _whole/_interface fingerprint shape as
  frontend/curl_vector_math_profile.py and smooth_edge_luma_weights_profile.py)
- loop proof
- global declarations needing admission: storage/type/initializer shape,
  span, SHA-256, and whether each is ever read anywhere in the program
  (dead-declaration check)
- every bracket-index ("index" kind) AST node: span, base symbol, index kind
  (literal/id), lvalue/rvalue context, type, SHA-256, parent kind
- call-graph reachability from main() via `call` node signature_id

Never writes under noisemaker-for-cpp or noisemaker-for-cpp-for-cpu. Imports
only, no monkeypatching in this script (a separate script handles the
gate-chain restoration probes).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp import check_corpus  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = [
    "filter/grade:primary",
    "filter/grade:hslSecondary",
    "filter/grade:wheels",
    "filter/grade:vignette",
    "filter/grade:creative",
    "filter/grade:lut",
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


def walk_expr(value, parent=None):
    yield value, parent
    for child in value.children:
        yield from walk_expr(child, value)


def walk_stmt(value):
    for e in value.expressions:
        yield from walk_expr(e, None)
    for c in value.children:
        yield from walk_stmt(c)


def load(key):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    parsed = parse_program(raw, key, defines)
    typed = analyze_program(parsed, key)
    return entry, raw, defines, typed


def call_graph_reachable(program) -> set[int]:
    """BFS from `main` over `call` node signature_id -> function id."""
    funcs_by_id = {f.id: f for f in program.functions}
    main_id = None
    for f in program.functions:
        if f.name == "main":
            main_id = f.id
            break
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
            for value, _parent in walk_stmt(stmt):
                if value.kind == "call" and value.signature_id is not None:
                    target = value.signature_id
                    if target not in seen and target in funcs_by_id:
                        seen.add(target)
                        frontier.append(target)
    return seen


def declaration_report(program, reachable_ids):
    report = []
    for decl in program.declarations:
        storage = decl.symbol.storage
        if storage in {"uniform", "output"}:
            continue
        # Already-admitted generic shape: const float, literal/id/unary/binary
        # initializer over admitted const floats (see generate_typed_slice.py
        # global_initializer(), lines ~1929-1951).
        already_admitted_generic = (
            storage == "const" and decl.type.display() == "float"
            and decl.initializer is not None
            and decl.initializer.kind == "literal")
        # Census every read of this symbol anywhere in the program.
        reads = []
        for fn in program.functions:
            for stmt in fn.body:
                for value, parent in walk_stmt(stmt):
                    if value.kind == "id" and value.symbol_id == decl.symbol.id:
                        reads.append((fn.id, fn.name, span(value)))
        reachable_reads = [r for r in reads if r[0] in reachable_ids]
        report.append({
            "symbol_id": decl.symbol.id,
            "name": decl.symbol.name,
            "storage": storage,
            "type": decl.type.display(),
            "span": span(decl),
            "declaration_sha256": sha(decl),
            "initializer_kind": decl.initializer.kind if decl.initializer else None,
            "initializer_span": span(decl.initializer) if decl.initializer else None,
            "initializer_sha256": sha(decl.initializer) if decl.initializer else None,
            "initializer_children_kinds": (
                [c.kind for c in decl.initializer.children]
                if decl.initializer else []),
            "already_admitted_by_existing_generic_mechanism": already_admitted_generic,
            "total_read_count": len(reads),
            "reads": reads,
            "reachable_read_count": len(reachable_reads),
            "dead_declaration": len(reads) == 0,
        })
    return report


def index_node_report(program, reachable_ids):
    report = []
    for fn in program.functions:
        for stmt in fn.body:
            for value, parent in walk_stmt(stmt):
                if value.kind != "index":
                    continue
                base, index = value.children
                report.append({
                    "owning_function_id": fn.id,
                    "owning_function_name": fn.name,
                    "owning_function_reachable": fn.id in reachable_ids,
                    "span": span(value),
                    "sha256": sha(value),
                    "type": value.type.display(),
                    "category": value.category,
                    "base_kind": base.kind,
                    "base_symbol_id": base.symbol_id,
                    "base_type": base.type.display(),
                    "index_kind": index.kind,
                    "index_symbol_id": getattr(index, "symbol_id", None),
                    "index_literal_value": getattr(index, "literal_value", None),
                    "parent_kind": parent.kind if parent is not None else None,
                    "parent_operator": getattr(parent, "operator", None) if parent is not None else None,
                    "parent_span": span(parent) if parent is not None else None,
                })
    return report


def function_tuple(program):
    return tuple((f.id, f.name, len(f.body), sha(f)) for f in program.functions)


def main():
    out = {}
    for key in KEYS:
        entry, raw, defines, typed = load(key)
        raw_bytes = raw.encode("utf-8")
        norm_bytes = typed.source.encode("utf-8")
        reachable = call_graph_reachable(typed)
        reachable_names = sorted(f.name for f in typed.functions if f.id in reachable)
        unreachable_names = sorted(f.name for f in typed.functions if f.id not in reachable)
        proof = typed.counted_loop_proof
        entry_out = {
            "manifest_entry": entry,
            "defines": defines,
            "raw_bytes": len(raw_bytes),
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "normalized_bytes": len(norm_bytes),
            "normalized_sha256": hashlib.sha256(norm_bytes).hexdigest(),
            "function_count": len(typed.functions),
            "function_tuple_sha256": sha(function_tuple(typed)),
            "whole_sha256": whole(typed),
            "interface_sha256": interface(typed),
            "loop_proof": None if proof is None else {
                "loop_count": proof.loop_count,
                "unproved_loop_count": proof.unproved_loop_count,
                "max_effective_depth": proof.max_effective_depth,
                "max_lexical_product": proof.max_lexical_product,
                "entrypoint_charge": proof.entrypoint_charge,
                "call_graph_acyclic": proof.call_graph_acyclic,
            },
            "reachable_function_count": len(reachable),
            "reachable_functions": reachable_names,
            "unreachable_functions": unreachable_names,
            "declarations": declaration_report(typed, reachable),
            "index_nodes": index_node_report(typed, reachable),
        }
        out[key] = entry_out
        print(f"=== {key} ===", file=sys.stderr)
        print(f"  raw {entry_out['raw_bytes']}B sha256={entry_out['raw_sha256'][:16]}...", file=sys.stderr)
        print(f"  functions={entry_out['function_count']} reachable={len(reachable)} unreachable={unreachable_names}", file=sys.stderr)
        print(f"  declarations needing admission: {[d['name'] for d in entry_out['declarations'] if not d['already_admitted_by_existing_generic_mechanism']]}", file=sys.stderr)
        for d in entry_out["declarations"]:
            if not d["already_admitted_by_existing_generic_mechanism"]:
                print(f"    {d['name']}: type={d['type']} dead={d['dead_declaration']} reads={d['total_read_count']} reachable_reads={d['reachable_read_count']}", file=sys.stderr)
        print(f"  index nodes: {len(entry_out['index_nodes'])}", file=sys.stderr)
        for n in entry_out["index_nodes"]:
            print(f"    {n['span']} fn={n['owning_function_name']} base={n['base_type']}[{n['index_kind']}] parent={n['parent_kind']}/{n['parent_operator']} reachable={n['owning_function_reachable']}", file=sys.stderr)

    Path("docs/port-engineering/task32b_grade_identity_output.json").write_text(
        json.dumps(out, indent=2, default=str))
    print("wrote task32b_grade_identity_output.json", file=sys.stderr)


if __name__ == "__main__":
    main()
