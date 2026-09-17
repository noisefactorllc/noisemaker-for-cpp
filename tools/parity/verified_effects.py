"""Derive export-kit/verified-effects.json from parity sweep results.

An effect is verified only when every one of its single-effect sweep cases, in every sweep given,
was byte-exact on RGBA8 and float32, or was refused by both the authority and this port. Any
divergent, timed-out, or C++-only refused case disqualifies it, and so does having no byte-exact
case at all. export-kit/generate-compat.mjs lists only verified effects.

usage: python3 tools/parity/verified_effects.py --sweep <out-dir> [--sweep <out-dir> ...] [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "export-kit/verified-effects.json"
SCHEMA = "noisemaker-cpp.verified-effects.v1"
ACCEPTED = {"byte_exact", "both_refused"}


def verified(sweeps: list[Path]) -> dict:
    classes: dict[str, set[str]] = {}
    runs = []
    for sweep in sweeps:
        document = json.loads((sweep / "results.json").read_text(encoding="utf-8"))
        rows = [json.loads(line) for line in (sweep / "results.jsonl").read_text(encoding="utf-8").splitlines() if line]
        meta = document["meta"]
        runs.append({"seed": meta["seed"], "variants": meta["variants"], "cases": len(rows)})
        for row in rows:
            if row["kind"] == "chain":
                continue
            classes.setdefault(row["effect_id"], set()).add(row["classification"])
    effects = sorted(effect for effect, seen in classes.items() if seen <= ACCEPTED and "byte_exact" in seen)
    return {"schema": SCHEMA, "sweeps": runs, "swept_effects": len(classes), "effects": effects}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", action="append", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    output = json.dumps(verified(arguments.sweep), indent=2) + "\n"
    if arguments.check:
        if TARGET.read_text(encoding="utf-8") != output:
            print("verified_effects: export-kit/verified-effects.json does not match these sweeps", file=sys.stderr)
            return 1
    else:
        TARGET.write_text(output, encoding="utf-8")
    print(f"verified_effects: {len(json.loads(output)['effects'])} verified effects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
