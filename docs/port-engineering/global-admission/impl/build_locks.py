"""Compute the exact frozen lock table for linear_srgb_lane_index_v1,
Slice A only: filter/adjust, filter/colorspace, classicNoisedeck/cellNoise.
Mirrors grade_index_expression_profile.py's _LOCKS shape exactly. Read-only.
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
]
PROFILE_NAMES = {
    "filter/adjust:adjust": "linear-srgb-adjust-lane-index-v1",
    "filter/colorspace:colorspace": "linear-srgb-colorspace-lane-index-v1",
    "classicNoisedeck/cellNoise:cellNoise": "linear-srgb-cellnoise-lane-index-v1",
}


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


def walk_stmt(value, results):
    for i, e in enumerate(value.expressions):
        walk_expr(e, value, i, results)
    for c in value.children:
        walk_stmt(c, results)


def walk_expr(value, parent, child_index, results):
    results.append((value, parent, child_index))
    for i, child in enumerate(value.children):
        walk_expr(child, value, i, results)


def load(key):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    parsed = parse_program(raw, key, defines)
    typed = analyze_program(parsed, key)
    return entry, raw, defines, typed


def main():
    out = {}
    for key in KEYS:
        entry, raw, defines, typed = load(key)
        assert defines == {}, (key, defines)
        raw_bytes = raw.encode("utf-8")
        norm_bytes = typed.source.encode("utf-8")

        census = []
        for function in typed.functions:
            results = []
            for statement in function.body:
                walk_stmt(statement, results)
            for node, parent, child_index in results:
                if node.kind == "index":
                    census.append((node, parent, child_index, function.id, function.name))

        sites = []
        for node, parent, child_index, function_id, function_name in census:
            role = ("write" if parent is not None and parent.kind == "assign"
                    and parent.operator == "=" and child_index == 0 else "read")
            base, index = node.children
            sites.append((
                function_id, function_name, span(node), sha(node), role,
                base.symbol_id, base.symbol.name, base.symbol.storage,
                index.symbol_id, index.symbol.name,
            ))

        entry_out = {
            "profile": PROFILE_NAMES[key],
            "raw_bytes": len(raw_bytes),
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "normalized_bytes": len(norm_bytes),
            "normalized_sha256": hashlib.sha256(norm_bytes).hexdigest(),
            "whole_sha256": whole(typed),
            "interface_sha256": interface(typed),
            "functions_sha256": sha(typed.functions),
            "sites": sites,
        }
        out[key] = entry_out
        print(f"=== {key}: {len(sites)} sites ===", file=sys.stderr)

    Path("docs/port-engineering/global-admission/impl/locks_output.json").write_text(
        json.dumps(out, indent=1, default=str))
    print("wrote locks_output.json", file=sys.stderr)


if __name__ == "__main__":
    main()
