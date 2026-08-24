"""Task 31 read-only identity probe for classicNoisedeck/caustic:caustic.

Independently re-derives the target identity table using the exact
`_whole`/`_interface` field order copied verbatim from
tools/glslcpp/frontend/extrude_bvec2_relational_reduction_profile.py, so the
hashes are directly comparable to Task 30's brief and the Task 31 precompute
report. Read-only: never writes under ..
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp import check_corpus, check_semantics  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

KEY = "classicNoisedeck/caustic:caustic"


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return f"{span.start_line}:{span.start_column}-{span.end_line}:{span.end_column}"


def _whole(program) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def main() -> int:
    root = check_corpus._corpus_root(REPO)
    manifest = check_corpus._load_json(root / "manifest.json", "manifest")
    entries = {item["program_key"]: item
               for item in check_corpus._validate_manifest(manifest)}
    entry = entries[KEY]
    source_path = root / entry["source"]
    raw_source = source_path.read_text(encoding="utf-8")
    raw_bytes = raw_source.encode("utf-8")
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    assert raw_sha256 == entry["raw_sha256"], "pinned source hash mismatch"

    metadata = check_corpus._load_json(root / "metadata.json", "metadata")
    defines = check_semantics._metadata_defaults(metadata, KEY)

    parsed = parse_program(raw_source, KEY, defines)
    typed = analyze_program(parsed, KEY)

    normalized_bytes = typed.source.encode("utf-8")

    result = {
        "key": KEY,
        "raw_bytes": len(raw_bytes),
        "raw_sha256": raw_sha256,
        "normalized_bytes": len(normalized_bytes),
        "normalized_sha256": hashlib.sha256(normalized_bytes).hexdigest(),
        "defines": {item.name: item.canonical_value for item in typed.preprocessor_defines},
        "define_kinds": {item.name: item.kind for item in typed.preprocessor_defines},
        "function_count": len(typed.functions),
        "functions_sha256": _sha(typed.functions),
        "whole_sha256": _whole(typed),
        "interface_sha256": _interface(typed),
        "body_status": typed.body_status,
        "structs": typed.structs,
        "uniform_blocks": typed.uniform_blocks,
        "loop_proof": None if typed.counted_loop_proof is None else (
            typed.counted_loop_proof.loop_count,
            typed.counted_loop_proof.unproved_loop_count,
            typed.counted_loop_proof.max_effective_depth,
            typed.counted_loop_proof.max_lexical_product,
            typed.counted_loop_proof.entrypoint_charge,
            typed.counted_loop_proof.call_graph_acyclic,
        ),
        "resources": {
            "uniforms": list(typed.resources.uniforms),
            "samplers": list(typed.resources.samplers),
            "outputs": list(typed.resources.outputs),
            "uses_texture": typed.resources.uses_texture,
            "uses_derivatives": typed.resources.uses_derivatives,
        },
        "function_ids_names": [(f.id, f.name, len(f.parameters), len(f.body), _span(f))
                                for f in typed.functions],
    }

    out = pathlib.Path("docs/port-engineering/task31-identity-output.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
