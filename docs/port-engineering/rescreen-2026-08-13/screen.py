"""Read-only re-screen of every currently-unported program against the LIVE
tools/glslcpp tree (not a frozen snapshot -- the live census is what's on
disk right now). Mirrors the pattern in docs/port-engineering/census/
run_census.py: parse -> analyze -> validate_capabilities(APPROVED_CAPABILITIES
only, no profiles) -> render_typed_cpp, recording the first blocker at each
stage. Read-only: writes only under docs/port-engineering/rescreen-2026-08-13/.
Never runs git.
"""
from __future__ import annotations

import json
import pathlib
import sys
import traceback

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}
assert len(ENTRIES) == 212, f"expected 212 corpus programs, got {len(ENTRIES)}"

SLICE = json.loads((REPO / "tools/glslcpp/typed_slice.json").read_text())
TYPED = {row["program_key"] for row in SLICE["programs"]}


def first_line(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def screen_one(key: str) -> dict:
    entry = ENTRIES[key]
    row = {"key": key, "parse": None, "validator": None, "emitter": None}
    try:
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen._defaults(REPO, key)
    except Exception as error:  # noqa: BLE001
        row["parse"] = f"DEFAULTS-ERROR: {first_line(error)}"
        return row
    try:
        parsed = parse_program(raw, key, defines)
        program = analyze_program(parsed, key)
        row["parse"] = "pass"
    except Exception as error:  # noqa: BLE001
        row["parse"] = first_line(error)
        return row
    try:
        gen.validate_capabilities(
            program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"]
        )
        row["validator"] = "pass"
    except Exception as error:  # noqa: BLE001
        row["validator"] = first_line(error)
    try:
        emit.render_typed_cpp(
            program, key, entry["raw_sha256"], "rescreen_probe", "bind_rescreen_probe"
        )
        row["emitter"] = "pass"
    except Exception as error:  # noqa: BLE001
        row["emitter"] = first_line(error)
    return row


def main() -> int:
    all_keys = sorted(ENTRIES)
    remaining = sorted(k for k in all_keys if k not in TYPED)
    print(f"typed_now={len(TYPED)} remaining={len(remaining)}")
    rows = []
    for key in remaining:
        try:
            row = screen_one(key)
        except Exception:  # noqa: BLE001
            row = {"key": key, "crash": traceback.format_exc()}
        rows.append(row)
        blocker = row.get("validator") or row.get("parse")
        print(f"{key:45s} validator={row.get('validator')!r} emitter={row.get('emitter')!r}")
    out = {"typed_now": len(TYPED), "remaining": len(remaining), "rows": rows}
    out_path = pathlib.Path(__file__).resolve().parent / "screen_out.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
