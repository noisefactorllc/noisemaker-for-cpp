#!/usr/bin/env python3
"""Read-only regeneration check for the scalar-uint-XOR profile cluster.

This evidence probe reparses all six pinned corpus carriers, independently
recomputes the scalar-XOR and ``float(uint)`` censuses, and then asks the
production profile to authenticate the freshly built object graph.  It never
writes source, profile constants, or generated C++.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.glslcpp import check_corpus, generate_typed_slice  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.scalar_uint_xor_profile import (  # noqa: E402
    PROFILE,
    SCALAR_UINT_XOR_KEYS,
    _UINT_TO_FLOAT_CENSUS_LOCKS,
    authenticate_scalar_uint_to_float_narrowing_skips,
    authenticate_scalar_uint_xor,
)
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402


def walk_expression(value):
    yield value
    for child in value.children:
        yield from walk_expression(child)


def walk_statement(value):
    for expression in value.expressions:
        yield from walk_expression(expression)
    for child in value.children:
        yield from walk_statement(child)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()

    corpus = check_corpus._corpus_root(ROOT)
    manifest = json.loads((corpus / "manifest.json").read_text())
    entries = {item["program_key"]: item for item in manifest["programs"]}
    report = []
    total_xors = 0
    total_casts = 0
    for key in sorted(SCALAR_UINT_XOR_KEYS):
        entry = entries[key]
        raw_bytes = (corpus / entry["source"]).read_bytes()
        raw_hash = hashlib.sha256(raw_bytes).hexdigest()
        if raw_hash != entry["raw_sha256"]:
            raise RuntimeError(f"{key}: corpus manifest hash drift")
        raw = raw_bytes.decode()
        program = analyze_program(
            parse_program(raw, key, generate_typed_slice._defaults(ROOT, key)),
            key)
        xors = tuple(
            value for function in program.functions for statement in function.body
            for value in walk_statement(statement)
            if value.kind == "binary" and value.operator == "^"
            and value.type.display() == "uint"
            and len(value.children) == 2
            and all(child.type.display() == "uint"
                    for child in value.children))
        casts = tuple(
            value for function in program.functions for statement in function.body
            for value in walk_statement(statement)
            if value.kind == "construct"
            and value.constructor_type is not None
            and value.constructor_type.display() == "float"
            and len(value.children) == 1
            and value.children[0].type.display() == "uint")
        authenticated_xors = authenticate_scalar_uint_xor(
            program, raw_hash, PROFILE)
        selected_casts = authenticate_scalar_uint_to_float_narrowing_skips(
            program, raw_hash, PROFILE)
        if xors != authenticated_xors:
            raise RuntimeError(f"{key}: authenticated XOR objects drift")
        if len(casts) != len(_UINT_TO_FLOAT_CENSUS_LOCKS[key]):
            raise RuntimeError(f"{key}: float(uint) census drift")
        total_xors += len(xors)
        total_casts += len(casts)
        report.append({
            "program_key": key,
            "scalar_uint_xors": len(xors),
            "float_uint_census": len(casts),
            "selected_narrowing_skips": len(selected_casts),
        })
    if total_xors != 18 or total_casts != 32:
        raise RuntimeError(
            f"cluster cardinality drift: XOR={total_xors}, casts={total_casts}")
    if sum(item["selected_narrowing_skips"] for item in report) != 1:
        raise RuntimeError("narrowing-skip selection drift")
    print(json.dumps({
        "profile": PROFILE,
        "programs": report,
        "totals": {
            "scalar_uint_xors": total_xors,
            "float_uint_census": total_casts,
            "selected_narrowing_skips": 1,
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
