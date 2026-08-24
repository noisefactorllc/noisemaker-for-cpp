"""Re-run the census's 3-layer relaxed-admission probe against the LIVE tree
(copied read-only under docs/port-engineering/global-admission/live_probe/),
not the frozen 2026-08-12 snapshot, to confirm the published
relaxed_global_probe.json / relaxed2_mat3_probe.json / relaxed3_mat3_probe.json
tables still hold now that typed count is 154 (was 131 at census time).

Layer 1: admit any global declaration that fails 'unsupported global
  declaration' (generate_typed_slice_relaxed1.py).
Layer 2: layer 1 + admit mat3 as a typed type in reject_type()
  (generate_typed_slice_relaxed2.py).
Layer 3: layer 2 + also bypass the unconditional matrix-kind global rejection
  for mat3 specifically (generate_typed_slice_relaxed3.py).

Never writes to the real repo; only reads/imports the rsync'd copy under this
directory.
"""
from __future__ import annotations

import importlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen0  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = HERE / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

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

MAT3_KEYS = [
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


def run_layer(module_name: str, keys: list[str]) -> list[dict]:
    gen = importlib.import_module(module_name)
    results = []
    for key in keys:
        entry = ENTRIES[key]
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen0._defaults(HERE, key)
        program = analyze_program(parse_program(raw, key, defines), key)
        row = {"key": key}
        try:
            gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES,
                                       source_hash=entry["raw_sha256"])
            row["blocker"] = "VALIDATOR-PASS"
        except gen.GeneratorError as error:
            row["blocker"] = first_line(error)
        results.append(row)
    return results


def main() -> int:
    layer1 = run_layer("tools.glslcpp.generate_typed_slice_relaxed1", TARGET_KEYS)
    layer2 = run_layer("tools.glslcpp.generate_typed_slice_relaxed2", MAT3_KEYS)
    layer3 = run_layer("tools.glslcpp.generate_typed_slice_relaxed3", MAT3_KEYS)

    out = {
        "layer1_all25_next_blocker": layer1,
        "layer2_mat3_after_type_admission": layer2,
        "layer3_mat3_after_type_and_global_admission": layer3,
    }
    outpath = HERE.parent / "probe_layers123.json"
    outpath.write_text(json.dumps(out, indent=1, sort_keys=True))

    print("=== LAYER 1 (all 25) ===")
    for r in layer1:
        print(r["key"], "->", r["blocker"])
    print("=== LAYER 2 (7 mat3) ===")
    for r in layer2:
        print(r["key"], "->", r["blocker"])
    print("=== LAYER 3 (7 mat3) ===")
    for r in layer3:
        print(r["key"], "->", r["blocker"])
    print("wrote", outpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
