from __future__ import annotations
import json, pathlib, sys

SNAPSHOT_TS = "20260812T225121Z"
REPO = pathlib.Path(f"docs/port-engineering/census/snapshot/{SNAPSHOT_TS}/repo")
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice_relaxed_varying as genr  # noqa: E402
from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = ["filter/grime:grime", "filter/spookyTicker:spookyTicker",
        "filter/texture:texture", "filter/wobble:wobble", "filter/wormhole:deposit"]


def first_line(error) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def main():
    for key in KEYS:
        entry = ENTRIES[key]
        raw = (CORPUS / entry["source"]).read_text()
        defines = genr._defaults(REPO, key)
        program = analyze_program(parse_program(raw, key, defines), key)
        try:
            genr.validate_capabilities(program, genr.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
            status = "VALIDATOR-PASS"
            try:
                emit.render_typed_cpp(program, key, entry["raw_sha256"], "probev", "bind_probev")
                status += " / emitter pass"
            except Exception as error:  # noqa: BLE001
                status += f" / emitter FAIL: {first_line(error)}"
        except genr.GeneratorError as error:
            status = first_line(error)
        print(key, "->", status)


if __name__ == "__main__":
    main()
