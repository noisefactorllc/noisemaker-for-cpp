"""Probe whether a candidate program's ONLY blocker is a single, literal,
non-loop-bounding const-int global -- i.e. whether it is a clean
source-global-literal-int-v1 fingerprint reuse (same mechanism already
shipped for bloom/directionalBlur/spinBlur/strokes/vaseline/wind/
nmReindexStats/nmReindexReduce), computed from the REAL authentication
functions (never hand-computed hashes), then temporarily registered
in-process (never written to the live tree) to see the ACTUAL next blocker
via the real validate_capabilities()/render_typed_cpp().

Read-only w.r.t. the live tree: all patching happens on already-imported
module objects in this process only.
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend import loop_proof  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}


def build_profile(program, integer_name: str) -> dict:
    key = program.key
    pre_functions = loop_proof.attach_counted_loop_proofs(program.functions, key)

    integer_decl = next(
        item for item in program.declarations
        if item.symbol.storage not in {"uniform", "output"}
        and item.symbol.name == integer_name)
    integer_id = integer_decl.symbol.id
    integer_literal = integer_decl.initializer.literal
    integer_value = integer_decl.initializer.literal_value
    assert integer_decl.initializer.kind == "literal"
    assert integer_decl.type.display() == "int"

    reads = []
    for function in pre_functions:
        for statement in function.body:
            for expression in loop_proof._walk_statement_expressions(statement):
                if expression.kind == "id" and expression.symbol_id == integer_id:
                    span = expression.span
                    reads.append((function.name, function.signature.id,
                                  span.start_line, span.start_column,
                                  span.end_line, span.end_column))
    seed = ((integer_id, integer_value, "source-global-const-literal", integer_decl.symbol),)

    source_globals = tuple(item for item in program.declarations
                           if item.symbol.storage not in {"uniform", "output"})
    actual_globals = tuple((item.symbol.name, item.symbol.id, item.type.display(),
                            item.initializer.literal if item.initializer is not None else None)
                           for item in source_globals)
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)

    pre_summary = loop_proof.summarize_counted_loop_proofs(pre_functions)
    attached = loop_proof.attach_counted_loop_proofs(pre_functions, key, source_global_bounds=seed)
    post_summary = loop_proof.summarize_counted_loop_proofs(attached)

    profile = {
        "raw": loop_proof._text_sha(program.raw_source),
        "source": loop_proof._text_sha(program.source),
        "defines": defines,
        "integer": (integer_name, integer_id, integer_literal, integer_value),
        "globals": actual_globals,
        "reads": tuple(reads),
        "pre_functions": loop_proof._sha(pre_functions),
        "post_functions": loop_proof._sha(attached),
        "pre_whole": loop_proof._sha(loop_proof._whole_program_identity(program, pre_functions, pre_summary)),
        "post_whole": loop_proof._sha(loop_proof._whole_program_identity(program, attached, post_summary)),
        "interface": loop_proof._sha(loop_proof._interface_identity(program)),
    }
    return profile


def probe(key: str, integer_name: str) -> None:
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(REPO, key)
    parsed = parse_program(raw, key, defines)
    program = analyze_program(parsed, key)

    profile = build_profile(program, integer_name)
    print(f"=== {key} candidate profile ===")
    print(json.dumps({k: (v if not isinstance(v, tuple) else list(v)) for k, v in profile.items()},
                      default=str, indent=2))

    # Patch in-process only.
    loop_proof._SOURCE_GLOBAL_LITERAL_INT_PROFILES[key] = profile
    new_keys = frozenset(loop_proof._SOURCE_GLOBAL_LITERAL_INT_PROFILES)
    loop_proof.SOURCE_GLOBAL_LITERAL_INT_KEYS = new_keys
    gen.SOURCE_GLOBAL_LITERAL_INT_KEYS = new_keys
    emit.SOURCE_GLOBAL_LITERAL_INT_KEYS = new_keys

    try:
        gen.validate_capabilities(
            program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"],
            source_global_literal_int_profile=loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
        )
        print("VALIDATOR: pass")
    except Exception as error:  # noqa: BLE001
        print(f"VALIDATOR: FAIL: {error}")
        return

    try:
        rendered = emit.render_typed_cpp(
            program, key, entry["raw_sha256"], "probe_single_int", "bind_probe_single_int",
            source_global_literal_int_profile=loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
        )
        print(f"EMITTER: pass ({len(rendered)} bytes)")
    except Exception as error:  # noqa: BLE001
        print(f"EMITTER: FAIL: {error}")


if __name__ == "__main__":
    key = sys.argv[1]
    integer_name = sys.argv[2]
    probe(key, integer_name)
