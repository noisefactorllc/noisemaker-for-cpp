"""Task 31 read-only frontier scan.

For every corpus program key NOT currently in the 130-typed slice, parse +
analyze it against the live pipeline and record the validator's first
blocker message (or PASS). Used to (a) confirm nothing besides the two
already-known manual public keys passes both authorities unassisted today,
and (b) rank remaining candidates by rough gate-chain size for comparison
against Caustic.

Read-only: never writes under ..
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp import check_corpus, check_semantics  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402


def main() -> int:
    root = check_corpus._corpus_root(REPO)
    manifest = check_corpus._load_json(root / "manifest.json", "manifest")
    entries = {item["program_key"]: item
               for item in check_corpus._validate_manifest(manifest)}

    slice_spec = gen.load_slice(REPO)
    typed_keys = {item["program_key"] for item in slice_spec["programs"]}
    assert len(typed_keys) == 130, f"expected 130 typed keys, got {len(typed_keys)}"

    metadata = check_corpus._load_json(root / "metadata.json", "metadata")

    remaining = sorted(set(entries) - typed_keys)
    results = []
    for key in remaining:
        entry = entries[key]
        source = (root / entry["source"]).read_text(encoding="utf-8")
        try:
            defines = check_semantics._metadata_defaults(metadata, key)
            parsed = parse_program(source, key, defines)
            typed = analyze_program(parsed, key)
        except Exception as error:  # noqa: BLE001
            results.append({"key": key, "stage": "parse/analyze",
                             "error": f"{type(error).__name__}: {error}"})
            continue
        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES)
            results.append({"key": key, "stage": "validate", "error": "PASS"})
        except gen.GeneratorError as error:
            results.append({"key": key, "stage": "validate",
                             "error": str(error)})

    passing = [r for r in results if r["error"] == "PASS"]
    out = pathlib.Path("docs/port-engineering/task31-frontier-scan-output.json")
    out.write_text(json.dumps({
        "typed_count": len(typed_keys),
        "remaining_count": len(remaining),
        "passing_keys": [r["key"] for r in passing],
        "all_results": results,
    }, indent=2, sort_keys=True) + "\n")

    print("typed_count:", len(typed_keys))
    print("remaining_count:", len(remaining))
    print("passing (validator PASS) keys:", [r["key"] for r in passing])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
