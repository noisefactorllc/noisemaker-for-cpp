"""Read-only census of every corpus program absent from the typed slice.

For each remaining key this records the first validator gate and the first
emitter gate under the *current* accepted pipeline. No repository or Git state
is changed. Output is JSON on stdout.
"""

from __future__ import annotations

import json
import pathlib
import sys
import traceback

ROOT = pathlib.Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

SLICE = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text())
TYPED = {row["program_key"] for row in SLICE["programs"]}


def first_line(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else f"{type(error).__name__}"


def census_one(key: str) -> dict:
    entry = ENTRIES[key]
    row = {
        "key": key,
        "raw_bytes": entry["raw_bytes"],
        "raw_sha256": entry["raw_sha256"],
        "parse": None,
        "validator": None,
        "emitter": None,
        "builtins": None,
    }
    try:
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen._defaults(ROOT, key)
        program = analyze_program(parse_program(raw, key, defines), key)
        row["parse"] = "pass"
    except Exception as error:  # noqa: BLE001
        row["parse"] = first_line(error)
        row["parse_type"] = type(error).__name__
        return row

    try:
        used = sorted({
            name
            for function in program.functions
            for name in getattr(function, "builtins", ()) or ()
        })
        row["builtins"] = used
    except Exception:  # noqa: BLE001
        pass

    try:
        gen.validate_capabilities(
            program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"]
        )
        row["validator"] = "pass"
    except Exception as error:  # noqa: BLE001
        row["validator"] = first_line(error)
        row["validator_type"] = type(error).__name__

    try:
        emit.render_typed_cpp(
            program, key, entry["raw_sha256"], "census_probe", "bind_census_probe"
        )
        row["emitter"] = "pass"
    except Exception as error:  # noqa: BLE001
        row["emitter"] = first_line(error)
        row["emitter_type"] = type(error).__name__
    return row


def main() -> int:
    remaining = [key for key in sorted(ENTRIES) if key not in TYPED]
    rows = []
    for key in remaining:
        try:
            rows.append(census_one(key))
        except Exception:  # noqa: BLE001
            rows.append({"key": key, "crash": traceback.format_exc().splitlines()[-1]})
    print(json.dumps({
        "revision": REVISION,
        "corpus_total": len(ENTRIES),
        "typed_total": len(TYPED),
        "remaining_total": len(remaining),
        "rows": rows,
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
