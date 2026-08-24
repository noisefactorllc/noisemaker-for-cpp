"""Second-order probe for the 'unsupported global declaration' family.

Read-only: parses+analyzes each program via the real frontend (parse_program +
analyze_program), then replicates the exact admission logic at
tools/glslcpp/generate_typed_slice.py lines 1752-1770 to classify every
top-level (non uniform/output) declaration in each of the 30 affected
programs. This tells us, per program, which declarations are the *actual*
blocker (first one hit, matching the real validator's raise point) and what
the *other* declarations in the same program look like (so we know whether
admitting "const float scalar" alone would still leave residual blockers).

No monkeypatching needed here since we are not probing hypothetical capability
admission (that's a fixed classification rule, not a capability flag) -- we
are literally re-running the documented admission predicate against the AST.
Does not import generate_typed_slice's validate_capabilities and does not
call it in a way that mutates any module state. Nothing in the target repo is
written.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp.frontend.semantic_types import FLOAT  # noqa: E402
from tools.glslcpp.frontend.loop_proof import SOURCE_GLOBAL_LITERAL_INT_KEYS  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = [
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
    "filter/grade:creative",
    "filter/grade:hslSecondary",
    "filter/grade:primary",
    "filter/grade:vignette",
    "filter/grade:wheels",
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


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, typed


def classify(declaration) -> dict:
    symbol = declaration.symbol
    kind = declaration.type.kind
    if kind == "array":
        shape = f"array[{declaration.type.size}] of {declaration.type.element.display()}"
    elif kind == "matrix":
        shape = f"matrix {declaration.type.display()}"
    elif kind == "vector":
        shape = f"vector {declaration.type.display()}"
    else:
        shape = declaration.type.display()
    is_const_float_scalar = (
        symbol.storage == "const"
        and declaration.type == FLOAT
        and declaration.initializer is not None
    )
    return {
        "name": symbol.name,
        "storage": symbol.storage,
        "shape": shape,
        "type_kind": kind,
        "has_initializer": declaration.initializer is not None,
        "admitted_by_current_rule": is_const_float_scalar,
    }


def admission_tag(row: dict) -> str:
    """Bucket a single declaration by *why* it fails the current rule."""
    if row["admitted_by_current_rule"]:
        return "admitted (const float scalar)"
    if row["storage"] == "const" and row["type_kind"] == "array":
        return "const array"
    if row["storage"] == "const" and row["type_kind"] == "vector":
        return "const vector"
    if row["storage"] == "const" and row["type_kind"] == "matrix":
        return "const matrix"
    if row["storage"] == "const" and row["type_kind"] == "scalar" and row["shape"] != "float":
        return f"const non-float scalar ({row['shape']})"
    if row["storage"] == "const" and row["type_kind"] == "scalar" and not row["has_initializer"]:
        return "const float scalar, no initializer"
    if row["storage"] != "const":
        return f"non-const global ({row['storage']})"
    return "other"


def main() -> int:
    results = []
    for key in KEYS:
        entry, typed = load(key)
        assert key not in SOURCE_GLOBAL_LITERAL_INT_KEYS, key
        source_decls = [d for d in typed.declarations
                        if d.symbol.storage not in {"uniform", "output"}]
        rows = [classify(d) for d in source_decls]
        for row in rows:
            row["tag"] = admission_tag(row)
        first_blocker = next((row for row in rows if not row["admitted_by_current_rule"]), None)
        results.append({
            "key": key,
            "source_global_count": len(rows),
            "declarations": rows,
            "first_blocking_declaration": first_blocker,
            "first_blocker_tag": first_blocker["tag"] if first_blocker else None,
        })

    tag_counts: dict[str, int] = {}
    for r in results:
        tag = r["first_blocker_tag"]
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    out = {
        "family": "unsupported global declaration",
        "member_count": len(KEYS),
        "first_blocker_tag_distribution": tag_counts,
        "rows": results,
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
