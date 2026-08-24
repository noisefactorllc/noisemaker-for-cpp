from __future__ import annotations
import json, pathlib, sys

SNAPSHOT_TS = "20260812T225121Z"
REPO = pathlib.Path(f"docs/port-engineering/census/snapshot/{SNAPSHOT_TS}/repo")
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice_relaxed3 as genr  # noqa: E402
from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = [
    "classicNoisedeck/cellNoise:cellNoise",
    "classicNoisedeck/colorLab:colorLab",
    "classicNoisedeck/moodscape:moodscape",
    "classicNoisedeck/shapeMixer:shapeMixer",
    "classicNoisedeck/shapes:shapes",
    "filter/adjust:adjust",
    "filter/colorspace:colorspace",
]


def first_line(error) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def main() -> int:
    results = []
    for key in KEYS:
        entry = ENTRIES[key]
        raw = (CORPUS / entry["source"]).read_text()
        defines = genr._defaults(REPO, key)
        program = analyze_program(parse_program(raw, key, defines), key)
        row = {"key": key}
        try:
            genr.validate_capabilities(program, genr.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
            row["after_mat3_full_admission"] = "VALIDATOR-PASS"
            try:
                emit.render_typed_cpp(program, key, entry["raw_sha256"], "probe2", "bind_probe2")
                row["emitter"] = "pass"
            except Exception as error:  # noqa: BLE001
                row["emitter"] = first_line(error)
        except genr.GeneratorError as error:
            row["after_mat3_full_admission"] = first_line(error)
        results.append(row)
    out = pathlib.Path("docs/port-engineering/census/relaxed3_mat3_probe.json")
    out.write_text(json.dumps(results, indent=1, sort_keys=True))
    for r in results:
        print(r["key"], "->", r.get("after_mat3_full_admission"), "| emit:", r.get("emitter"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
