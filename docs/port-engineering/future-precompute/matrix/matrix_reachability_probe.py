"""Reachability + discriminability groundwork probe for the 9 matrix-blocked
noisemaker-for-cpp programs identified by roadmap2/full-chain-frontier-map.md
Section 5/6 ("Matrix arithmetic beyond mat2 * vec2", 9 programs).

READ-ONLY. Never writes under noisemaker-for-cpp or noisemaker-for-cpu.
Reuses gate_chain_engine.load() (pure parse + semantic analysis, no
validator/emitter gating) and the same call-graph-from-main technique as
roadmap2/reachability_probe.py, applied here to the 9 matrix programs (which
never reach PASS, so they are absent from roadmap2/reachability-output.json).

No monkeypatching happens in this script -- reachability is a property of the
parsed AST, independent of whether the typed-slice validator/emitter accept
the program. Nothing is mutated, so there is nothing to restore; this file
still records that fact explicitly per program (monkeypatch_used: false).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, "docs/port-engineering/roadmap2")

import gate_chain_engine as gce  # noqa: E402

MATRIX_KEYS = [
    "classicNoisedeck/cellNoise:cellNoise",
    "classicNoisedeck/colorLab:colorLab",
    "classicNoisedeck/effects:effects",
    "classicNoisedeck/glitch:glitch",
    "classicNoisedeck/moodscape:moodscape",
    "classicNoisedeck/noise:noise",
    "classicNoisedeck/shapes:shapes",
    "filter/adjust:adjust",
    "filter/colorspace:colorspace",
]


def expression_nodes(value, path=()):
    yield path, value
    for index, child in enumerate(value.children):
        yield from expression_nodes(child, (*path, index))


def statement_nodes(value, path=()):
    for index, expression in enumerate(value.expressions):
        yield from expression_nodes(expression, (*path, f"e{index}"))
    for index, child in enumerate(value.children):
        yield from statement_nodes(child, (*path, f"s{index}"))


def function_nodes(function):
    for index, statement in enumerate(function.body):
        yield from statement_nodes(statement, (index,))


def reachable_signature_ids(typed):
    definitions = {f.signature.id: f for f in typed.functions if f.body}
    main = next((f for f in typed.functions if f.name == "main"), None)
    if main is None:
        return set(), definitions
    reachable = {main.signature.id}
    pending = [main.signature.id]
    while pending:
        sid = pending.pop()
        function = definitions.get(sid)
        if function is None:
            continue
        for _, value in function_nodes(function):
            if (value.kind == "call" and value.signature_id in definitions
                    and value.signature_id not in reachable):
                reachable.add(value.signature_id)
                pending.append(value.signature_id)
    return reachable, definitions


def span_text(value) -> str:
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


def analyze(key: str) -> dict:
    entry, raw, defines, typed = gce.load(key)
    reachable, definitions = reachable_signature_ids(typed)

    matrix_construct_sites = []
    matrix_binary_sites = []
    matrix_global_decls = []

    for function in typed.functions:
        owner_reachable = function.signature.id in reachable
        for path, value in function_nodes(function):
            if value.kind == "construct" and value.type.kind == "matrix":
                matrix_construct_sites.append({
                    "owner": function.name,
                    "owner_signature_id": function.signature.id,
                    "owner_reachable": owner_reachable,
                    "matrix_type": value.type.display(),
                    "child_count": len(value.children),
                    "span": span_text(value),
                })
            if (value.kind == "binary" and value.operator == "*"
                    and any(c.type.kind == "matrix" for c in value.children)):
                left, right = value.children
                matrix_binary_sites.append({
                    "owner": function.name,
                    "owner_signature_id": function.signature.id,
                    "owner_reachable": owner_reachable,
                    "left_type": left.type.display(),
                    "right_type": right.type.display(),
                    "result_type": value.type.display(),
                    "left_kind": left.kind, "right_kind": right.kind,
                    "left_is_matrix": left.type.kind == "matrix",
                    "right_is_matrix": right.type.kind == "matrix",
                    "span": span_text(value),
                })

    for d in typed.declarations:
        if d.type.kind == "matrix":
            refs = []
            for function in typed.functions:
                owner_reachable = function.signature.id in reachable
                for _, value in function_nodes(function):
                    if value.kind == "id" and value.symbol_id == d.symbol.id:
                        refs.append({"owner": function.name,
                                     "owner_reachable": owner_reachable,
                                     "span": span_text(value)})
            matrix_global_decls.append({
                "name": d.symbol.name, "storage": d.symbol.storage,
                "type": d.type.display(),
                "reference_count": len(refs),
                "any_reference_reachable": any(r["owner_reachable"] for r in refs),
                "references": refs,
            })

    dead_functions = [f.name for f in typed.functions
                       if f.body and f.signature.id not in reachable]

    return {
        "key": key,
        "source_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "defines": defines,
        "main_present": any(f.name == "main" for f in typed.functions),
        "reachable_function_count": len(reachable),
        "total_function_count": sum(1 for f in typed.functions if f.body),
        "dead_functions": dead_functions,
        "matrix_construct_sites": matrix_construct_sites,
        "matrix_binary_sites": matrix_binary_sites,
        "matrix_global_decls": matrix_global_decls,
        "any_matrix_construct_reachable": any(
            s["owner_reachable"] for s in matrix_construct_sites),
        "any_matrix_binary_reachable": any(
            s["owner_reachable"] for s in matrix_binary_sites),
        "matrix_matrix_multiply_present": any(
            s["left_is_matrix"] and s["right_is_matrix"]
            for s in matrix_binary_sites),
    }


if __name__ == "__main__":
    out = {}
    for key in MATRIX_KEYS:
        out[key] = analyze(key)
    payload = {
        "schema": "noisemaker-for-cpp.future-precompute.matrix.reachability.v1",
        "corpus_revision": gce.REVISION,
        "read_only": True,
        "monkeypatch_used": False,
        "keys": MATRIX_KEYS,
        "rows": out,
    }
    dest = Path("docs/port-engineering/future-precompute/matrix/matrix-reachability-output.json")
    dest.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(dest)
