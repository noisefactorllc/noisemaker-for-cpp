#!/usr/bin/env python3
"""Recompute the invariant counted-loop proof for synth/gabor:gabor.

This probe intentionally does not assert whether Gabor is already admitted by
the live slice. Admission changes during the port; the source-derived proof
must not. It writes nothing and never imports a generated C++ artifact.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
CPP_ROOT = HERE.parents[3]
sys.path.insert(0, str(CPP_ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.loop_proof import (  # noqa: E402
    attach_counted_loop_proofs,
    summarize_counted_loop_proofs,
)
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402


PROGRAM_KEY = "synth/gabor:gabor"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
SOURCE_SHA256 = "91665da2d584d6d88b38e8ba314dfc0b546dd49d29aa161f5d66aecf6bf67bf5"


def span(value: object) -> str:
    item = getattr(value, "span")
    return (
        f"{item.start_line}:{item.start_column}-"
        f"{item.end_line}:{item.end_column}"
    )


def walk(statements):
    for statement in statements:
        yield statement
        yield from walk(statement.children)


def build() -> dict:
    corpus = CPP_ROOT / "tools/glslcpp/corpus" / CORPUS_REVISION
    manifest = json.loads((corpus / "manifest.json").read_text())
    entry = next(
        row for row in manifest["programs"] if row["program_key"] == PROGRAM_KEY
    )
    source_path = corpus / entry["source"]
    source_bytes = source_path.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    if source_hash != SOURCE_SHA256 or entry["raw_sha256"] != SOURCE_SHA256:
        raise AssertionError("Gabor source/manifest hash drift")

    defines = gen._defaults(CPP_ROOT, PROGRAM_KEY)
    if defines != {}:
        raise AssertionError(f"Gabor define-map drift: {defines!r}")
    typed = analyze_program(
        parse_program(source_bytes.decode(), PROGRAM_KEY, defines), PROGRAM_KEY
    )
    functions = attach_counted_loop_proofs(typed.functions, PROGRAM_KEY)
    summary = summarize_counted_loop_proofs(functions)

    loops = []
    for function in functions:
        for statement in walk(function.body):
            proof = statement.loop_proof
            if statement.kind not in {"for", "while", "dowhile"}:
                continue
            if proof is None:
                raise AssertionError(f"unproved Gabor loop at {span(statement)}")
            loops.append(
                {
                    "owner": function.name,
                    "span": span(statement),
                    **dataclasses.asdict(proof),
                }
            )

    result = {
        "program_key": PROGRAM_KEY,
        "corpus_revision": CORPUS_REVISION,
        "source_sha256": source_hash,
        "authorized_defines": defines,
        "summary": dataclasses.asdict(summary),
        "loops": loops,
        "derived": {
            "helper_nested_charge": 3 + (3 * 3) + (3 * 3 * 8),
            "main_entrypoint_charge": 5 + 5 * (3 + (3 * 3) + (3 * 3 * 8)),
            "below_historical_4096_product_cap": summary.max_lexical_product < 4096,
            "below_historical_4096_charge_cap": summary.entrypoint_charge < 4096,
            "only_depth_exceeds_three": (
                summary.unproved_loop_count == 0
                and summary.call_graph_acyclic
                and summary.max_effective_depth == 4
                and summary.max_lexical_product < 4096
                and summary.entrypoint_charge < 4096
            ),
        },
    }
    expected_summary = {
        "loop_count": 4,
        "unproved_loop_count": 0,
        "max_effective_depth": 4,
        "max_lexical_product": 72,
        "entrypoint_charge": 425,
        "call_graph_acyclic": True,
    }
    expected_loop_core = [
        ("gaborNoise", "49:5-79:6", 3, 1, 2, 72, 425),
        ("gaborNoise", "50:9-78:10", 3, 2, 3, 72, 425),
        ("gaborNoise", "54:13-77:14", 8, 3, 4, 72, 425),
        ("main", "104:5-113:6", 5, 1, 1, 5, 425),
    ]
    actual_loop_core = [
        (
            item["owner"], item["span"], item["trip_count"],
            item["lexical_depth"], item["effective_depth"],
            item["lexical_product"], item["entrypoint_charge"],
        )
        for item in loops
    ]
    if result["summary"] != expected_summary:
        raise AssertionError(f"Gabor aggregate proof drift: {result['summary']!r}")
    if actual_loop_core != expected_loop_core:
        raise AssertionError(f"Gabor loop tuple drift: {actual_loop_core!r}")
    if result["derived"] != {
        "helper_nested_charge": 84,
        "main_entrypoint_charge": 425,
        "below_historical_4096_product_cap": True,
        "below_historical_4096_charge_cap": True,
        "only_depth_exceeds_three": True,
    }:
        raise AssertionError(f"Gabor charge derivation drift: {result['derived']!r}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build()
    if args.json or not args.check:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "Gabor loop proof ok "
            f"({result['summary']['loop_count']} loops, "
            f"depth {result['summary']['max_effective_depth']}, "
            f"product {result['summary']['max_lexical_product']}, "
            f"charge {result['summary']['entrypoint_charge']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
