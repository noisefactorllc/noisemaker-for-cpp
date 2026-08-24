"""Task 32, task 2: classify the first failing global declaration for all 30
programs blocked by `unsupported global declaration`
(generate_typed_slice.py:1926: `storage != "const" or declaration.type !=
FLOAT or declaration.initializer is None`).

For each program: storage class, type kind (scalar/vector/matrix/array/
struct), and initializer shape (literal / constructor / arithmetic
expression / swizzle / other). Resolves the two previously-inconclusive keys
(bitEffects, scanlineError) by reading their actual declaration objects
(name, span, initializer.kind) directly from the real frontend output --
not regex, not guessing from raw source line numbers (the corpus source has
`#ifdef`/preprocessor lines that shift the *normalized* source's line
numbers away from the raw file's).

Read-only: only parse_program + analyze_program are used (the real
frontend), no monkeypatching, no writes to the target repo.
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

# All 30 keys in the "unsupported global declaration" family (27 const-typed
# + 3 non-const-global), per roadmap/remaining-capability-roadmap.md section
# 2 and roadmap/probe_globals.py's KEYS list, re-verified below by running
# the real unpatched validator against every key and confirming the exact
# "unsupported global declaration" message.
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
    return entry, raw, defines, typed


def span_str(value) -> str:
    s = value.span
    return f"{s.start_line}:{s.start_column}"


def initializer_shape(value) -> str:
    if value is None:
        return "none"
    if value.kind == "literal":
        return "literal"
    if value.kind == "construct":
        return "constructor"
    if value.kind in {"binary", "unary"}:
        return f"arithmetic expression ({value.kind} {getattr(value, 'operator', '?')})"
    if value.kind == "swizzle":
        return "swizzle"
    if value.kind == "id":
        return "identifier reference"
    return f"other ({value.kind})"


def admitted_by_current_rule(declaration) -> bool:
    return (declaration.symbol.storage == "const"
            and declaration.type == FLOAT
            and declaration.initializer is not None)


def classify_first_failing(typed):
    """Walk typed.declarations in order, skipping uniform/output, and return
    the first one that fails today's exact admission predicate
    (generate_typed_slice.py:1926)."""
    for d in typed.declarations:
        if d.symbol.storage in {"uniform", "output"}:
            continue
        if admitted_by_current_rule(d):
            continue
        return d
    return None


def main() -> int:
    # Sanity: confirm every key in KEYS really is in this family today, via
    # the REAL unpatched validator (not the replica predicate), and that the
    # message is exactly "unsupported global declaration".
    sanity = []
    for key in KEYS:
        entry, raw, defines, typed = load(key)
        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES,
                                      source_hash=entry["raw_sha256"])
            sanity.append((key, "UNEXPECTED PASS"))
        except Exception as error:  # noqa: BLE001
            msg = str(error).splitlines()[0]
            sanity.append((key, msg))
            assert "unsupported global declaration" in msg, (key, msg)

    rows = []
    for key in KEYS:
        entry, raw, defines, typed = load(key)
        assert key not in SOURCE_GLOBAL_LITERAL_INT_KEYS
        first = classify_first_failing(typed)
        assert first is not None, f"{key}: no failing declaration found (should be impossible)"

        storage = first.symbol.storage
        type_kind = first.type.kind
        if type_kind == "scalar":
            type_detail = first.type.display()
        elif type_kind == "vector":
            type_detail = first.type.display()
        elif type_kind == "matrix":
            type_detail = first.type.display()
        elif type_kind == "array":
            type_detail = f"{first.type.element.display()}[{first.type.size}]"
        elif type_kind == "struct":
            type_detail = first.type.name or "struct"
        else:
            type_detail = first.type.display()

        rows.append({
            "key": key,
            "declaration_name": first.symbol.name,
            "span": span_str(first),
            "storage": storage,
            "type_kind": type_kind,
            "type_detail": type_detail,
            "has_initializer": first.initializer is not None,
            "initializer_shape": initializer_shape(first.initializer),
        })

    # Distribution table: (storage-bucket, type_kind) counts.
    def bucket(row):
        if row["storage"] != "const":
            return f"non-const global ({row['storage']})"
        if row["type_kind"] == "scalar" and row["type_detail"] == "float":
            return "const float scalar (should not occur -- would already be admitted)"
        if row["type_kind"] == "scalar":
            return f"const non-float scalar ({row['type_detail']})"
        if row["type_kind"] == "vector":
            return "const vector"
        if row["type_kind"] == "matrix":
            return "const matrix"
        if row["type_kind"] == "array":
            return "const array"
        if row["type_kind"] == "struct":
            return "const struct"
        return f"const other ({row['type_kind']})"

    distribution: dict[str, int] = {}
    for row in rows:
        b = bucket(row)
        row["bucket"] = b
        distribution[b] = distribution.get(b, 0) + 1

    initializer_shape_distribution: dict[str, int] = {}
    for row in rows:
        s = row["initializer_shape"]
        initializer_shape_distribution[s] = initializer_shape_distribution.get(s, 0) + 1

    payload = {
        "schema": "noisemaker-for-cpp.task32.global-declaration-distribution.v1",
        "corpus_revision": REVISION,
        "member_count": len(KEYS),
        "sanity_all_fail_with_family_message": sanity,
        "rows": rows,
        "storage_type_bucket_distribution": distribution,
        "initializer_shape_distribution": initializer_shape_distribution,
        "resolved_bitEffects": next(r for r in rows if "bitEffects" in r["key"]),
        "resolved_scanlineError": next(r for r in rows if "scanlineError" in r["key"]),
    }
    out = Path(__file__).with_name("global-distribution-output.json")
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
