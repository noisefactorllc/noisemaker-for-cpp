"""Second-order probe for the derivatives family: if dFdx/dFdy/fwidth were
admitted as ordinary builtins (the same monkeypatch technique
future-precompute/analyze_candidates.py uses -- add to
gen.APPROVED_CAPABILITIES / gen._BUILTINS / emit._BUILTIN_NAMES, run, restore
in finally), what's the NEXT blocker for each of the 15 keys?

IMPORTANT CAVEAT this probe cannot resolve: admitting the *name* dFdx/dFdy/
fwidth into the builtin allowlist only proves the validator/emitter's type
checking and C++ text generation would accept a call syntactically. It does
NOT prove the C++ runtime actually HAS a working dFdx/dFdy/fwidth free
function with correct screen-space-derivative semantics -- that requires new
runtime infrastructure (see the JS reference's record/replay 2x2-quad
strategy at noisemaker-for-cpu/src/csl/glsl-runtime.js:448-546), which the
typed-slice generator/emitter alone cannot provide. This probe answers "is
the REST of each program otherwise portable", not "is derivative emission a
solved problem".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = [
    "filter/bulge:bulge",
    "filter/celShading:celShadingColor",
    "filter/halftone:halftone",
    "filter/lens:lens",
    "filter/lensWarp:lensWarp",
    "filter/octaveWarp:octaveWarp",
    "filter/pinch:pinch",
    "filter/polar:polar",
    "filter/pondRipples:pondRipples",
    "filter/spiral:spiral",
    "filter/stamp:stThreshold",
    "filter/step:step",
    "filter/stipple:stipple",
    "filter/tunnel:tunnel",
    "filter/warp:warp",
]

DERIVATIVE_BUILTINS = ("dFdx", "dFdy", "fwidth")


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, typed


def first(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else f"{type(error).__name__}"


def probe(key: str) -> dict:
    entry, typed = load(key)
    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_names = dict(emit._BUILTIN_NAMES)
    try:
        gen.APPROVED_CAPABILITIES = (*old_caps, *DERIVATIVE_BUILTINS)
        gen._BUILTINS = frozenset((*old_builtins, *DERIVATIVE_BUILTINS))
        emit._BUILTIN_NAMES.update({name: name for name in DERIVATIVE_BUILTINS})
        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES,
                                       source_hash=entry["raw_sha256"])
            validator = "pass"
        except Exception as error:  # noqa: BLE001
            validator = first(error)
        try:
            emit.render_typed_cpp(typed, key, entry["raw_sha256"],
                                   "deriv_probe", "bind_deriv_probe")
            emitter = "pass"
        except Exception as error:  # noqa: BLE001
            emitter = first(error)
    finally:
        gen.APPROVED_CAPABILITIES = old_caps
        gen._BUILTINS = old_builtins
        emit._BUILTIN_NAMES.clear()
        emit._BUILTIN_NAMES.update(old_names)
    return {"key": key, "validator_next": validator, "emitter_next": emitter}


def main() -> int:
    rows = [probe(key) for key in KEYS]
    tag_counts: dict[str, int] = {}
    for row in rows:
        tag_counts[row["emitter_next"]] = tag_counts.get(row["emitter_next"], 0) + 1
    out = {
        "family": "dFdx / dFdy / fwidth -- second order (builtin-name admission only)",
        "caveat": ("Admitting the NAME does not imply the C++ runtime has real "
                   "derivative semantics; see docstring."),
        "rows": rows,
        "emitter_next_distribution": tag_counts,
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
