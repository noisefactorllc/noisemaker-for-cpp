"""For the 'unsupported global declaration' cluster, dump every top-level
declaration's storage/type/initializer-shape directly from the typed AST
(never from raw source text + reported line, which the corpus's own
preprocessor-driven renumbering makes unreliable -- see the triage doc's
moodscape note). Read-only, writes only under this directory.
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp.frontend.semantic_types import FLOAT  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = [
    "classicNoisedeck/bitEffects:bitEffects",
    "classicNoisedeck/cellRefract:cellRefract",
    "classicNoisedeck/effects:effects",
    "classicNoisedeck/kaleido:kaleido",
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
    "filter/smooth:smoothBlend",
    "filter/snow:snow",
    "filter/spookyTicker:spookyTicker",
    "filter/texture:texture",
    "filter/wobble:wobble",
    "synth/shape:shape",
]


def summarize_initializer(value) -> str:
    if value is None:
        return "<none>"
    kind = value.kind
    if kind == "literal":
        return f"literal({value.literal_value!r})"
    if kind == "id":
        return f"id(sym={value.symbol_id})"
    if kind == "call":
        return f"call({value.callee})"
    if kind == "construct":
        return f"construct({value.type.display()}, nargs={len(value.children)})"
    return f"{kind}(nchildren={len(value.children)})"


def main() -> int:
    for key in KEYS:
        entry = ENTRIES[key]
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen._defaults(REPO, key)
        parsed = parse_program(raw, key, defines)
        program = analyze_program(parsed, key)
        print(f"=== {key} ===")
        for declaration in program.declarations:
            storage = declaration.symbol.storage
            type_display = declaration.type.display()
            name = declaration.symbol.name
            init_summary = summarize_initializer(declaration.initializer)
            flag = ""
            if storage in {"uniform", "output"}:
                flag = "(exempt: uniform/output)"
            elif storage == "const" and type_display == "float" and declaration.initializer is not None:
                flag = "(likely already admitted: const float)"
            elif storage == "const" and type_display == "int":
                flag = "(needs source-global-literal-int profile)"
            elif storage == "const" and type_display == "mat3":
                flag = "(likely already admitted: const mat3 literal)"
            else:
                flag = "*** BLOCKED SHAPE ***"
            print(f"  {name:20s} storage={storage:10s} type={type_display:10s} init={init_summary:30s} {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
