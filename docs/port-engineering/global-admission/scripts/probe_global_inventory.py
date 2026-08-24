"""Exhaustive inventory of every non-uniform/non-output top-level declaration
across the 25-program global-declaration family: storage class, type, and
initializer shape (literal / id-ref / arithmetic / array-literal / none).

Never writes to the real repo.
"""
from __future__ import annotations

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


def describe_initializer(value) -> str:
    if value is None:
        return "none"
    kind = value.kind
    if kind == "literal":
        return f"literal({value.literal})"
    if kind == "id":
        return "id-ref"
    if kind == "unary":
        return f"unary({value.operator})[{describe_initializer(value.children[0]) if value.children else '?'}]"
    if kind == "binary":
        return f"binary({value.operator})"
    if kind == "construct":
        return f"construct({value.constructor_type.display() if getattr(value, 'constructor_type', None) else '?'}, nargs={len(value.children)})"
    return kind


def main() -> int:
    results = []
    for key in TARGET_KEYS:
        entry = ENTRIES[key]
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen0._defaults(HERE, key)
        program = analyze_program(parse_program(raw, key, defines), key)
        decls = []
        for d in program.declarations:
            storage = d.symbol.storage
            if storage in {"uniform", "output"}:
                continue
            decls.append({
                "name": d.symbol.name,
                "storage": storage,
                "type": d.type.display(),
                "type_kind": d.type.kind,
                "initializer": describe_initializer(d.initializer),
                "loc": f"{d.span.start_line}:{d.span.start_column}",
            })
        results.append({"key": key, "declarations": decls})

    out = HERE.parent / "probe_global_inventory.json"
    out.write_text(json.dumps(results, indent=1, sort_keys=True))
    for r in results:
        print("===", r["key"], "===")
        for d in r["declarations"]:
            print(f"  {d['storage']:8s} {d['type']:10s} {d['name']:20s} init={d['initializer']} @ {d['loc']}")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
