"""Downstream-blocker probe: using a RELAXED copy of validate_capabilities
that provisionally admits every global declaration presently rejected by
'unsupported global declaration' (any const non-float global: mat3/vec2/vec3/
int/uint/array: and any non-const, non-uniform/output global), rerun the
validator on the keys that hit that exact blocker in the real run, to find
each program's NEXT blocker (or confirm PASS, meaning this is genuinely their
only remaining blocker).

This does NOT claim the relaxation is a real, single admissible mechanism --
mat3 admission, vec3 admission, int/uint admission, array admission, and
mutable-global admission are almost certainly separate bespoke mechanisms.
It only answers "what's behind gate 2036-2037", which is otherwise invisible
without either modifying the real generator (forbidden) or this scratch-only
patched copy (frozen snapshot, never touches the real repos).

Read-only w.r.t. the real repos. Operates entirely inside the frozen
snapshot directory created earlier by run_census.py.
"""
from __future__ import annotations

import json
import pathlib
import sys

SNAPSHOT_TS = "20260812T225121Z"
REPO = pathlib.Path(f"docs/port-engineering/census/snapshot/{SNAPSHOT_TS}/repo")
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice_relaxed as genr  # noqa: E402
from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}


def first_line(error) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def main() -> int:
    raw_census = json.loads(pathlib.Path("docs/port-engineering/census/raw_census.json").read_text())
    keys = [r["key"] for r in raw_census["rows"]
            if isinstance(r.get("validator"), str) and r["validator"].endswith("unsupported global declaration")]
    results = []
    for key in keys:
        entry = ENTRIES[key]
        raw = (CORPUS / entry["source"]).read_text()
        defines = genr._defaults(REPO, key)
        program = analyze_program(parse_program(raw, key, defines), key)
        row = {"key": key}
        try:
            genr.validate_capabilities(program, genr.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
            row["next_after_relaxed_global_admission"] = "VALIDATOR-PASS"
            try:
                emit.render_typed_cpp(program, key, entry["raw_sha256"], "probe", "bind_probe")
                row["emitter_after_relaxed"] = "pass"
            except Exception as error:  # noqa: BLE001
                row["emitter_after_relaxed"] = first_line(error)
        except genr.GeneratorError as error:
            row["next_after_relaxed_global_admission"] = first_line(error)
        results.append(row)

    out = pathlib.Path("docs/port-engineering/census/relaxed_global_probe.json")
    out.write_text(json.dumps(results, indent=1, sort_keys=True))
    for r in results:
        print(r["key"], "->", r.get("next_after_relaxed_global_admission"), "| emit:", r.get("emitter_after_relaxed"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
