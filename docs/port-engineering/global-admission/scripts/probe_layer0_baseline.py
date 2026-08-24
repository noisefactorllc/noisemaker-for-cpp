"""Layer-0 baseline: run the REAL, unmodified live validator (as vendored
into this read-only copy of tools/glslcpp under docs/port-engineering/) over
the 25-program global-declaration family, to confirm each program's current
terminal blocker is exactly 'unsupported global declaration' before any
relaxation is applied.

This operates on a plain rsync copy of the live tools/glslcpp tree (made by
the calling agent under docs/port-engineering/global-admission/live_probe/),
NOT on the real tools/ directory, and NEVER writes to the real repo.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = HERE / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}
SLICE = json.loads((HERE / "tools/glslcpp/typed_slice.json").read_text())
TYPED = {row["program_key"] for row in SLICE["programs"]}

# The 25-program global-declaration family taken from
# docs/port-engineering/census/relaxed_global_probe.json (task-supplied
# authoritative list), re-verified independently below.
TARGET_KEYS = [
    "classicNoisedeck/bitEffects:bitEffects",
    "classicNoisedeck/cellNoise:cellNoise",
    "classicNoisedeck/cellRefract:cellRefract",
    "classicNoisedeck/colorLab:colorLab",
    "classicNoisedeck/kaleido:kaleido",
    "classicNoisedeck/moodscape:moodscape",
    "classicNoisedeck/shapeMixer:shapeMixer",
    "classicNoisedeck/shapes:shapes",
    "filter/adjust:adjust",
    "filter/colorspace:colorspace",
    "filter/edge:edge",
    "filter/emboss:emboss",
    "filter/fxaa:fxaa",
    "filter/glyphMap:glyphMap",
    "filter/grain:grain",
    "filter/historicPalette:historicPalette",
    "filter/normalMap:normalMap",
    "filter/osd:osd",
    "filter/palette:palette",
    "filter/scanlineError:scanlineError",
    "filter/snow:snow",
    "filter/spookyTicker:spookyTicker",
    "filter/texture:texture",
    "filter/wobble:wobble",
    "synth/shape:shape",
]


def first_line(error) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def main() -> int:
    assert len(ENTRIES) == 212, len(ENTRIES)
    assert len(TARGET_KEYS) == 25, len(TARGET_KEYS)
    missing_from_corpus = [key for key in TARGET_KEYS if key not in ENTRIES]
    assert not missing_from_corpus, missing_from_corpus
    already_typed = [key for key in TARGET_KEYS if key in TYPED]
    assert not already_typed, already_typed

    results = []
    for key in TARGET_KEYS:
        entry = ENTRIES[key]
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen._defaults(HERE, key)
        program = analyze_program(parse_program(raw, key, defines), key)
        row = {"key": key}
        try:
            gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES,
                                       source_hash=entry["raw_sha256"])
            row["baseline_blocker"] = "VALIDATOR-PASS"
        except gen.GeneratorError as error:
            row["baseline_blocker"] = first_line(error)
        results.append(row)

    out = HERE.parent / "probe_layer0_baseline.json"
    out.write_text(json.dumps(results, indent=1, sort_keys=True))
    for r in results:
        print(r["key"], "->", r["baseline_blocker"])
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
