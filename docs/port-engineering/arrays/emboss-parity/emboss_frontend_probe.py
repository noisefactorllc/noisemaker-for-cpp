#!/usr/bin/env python3
"""Independent source-authentication probe for Emboss181 oracle assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402


REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
KEY = "filter/emboss:emboss"
SOURCE = (ROOT / "tools/glslcpp/corpus" / REVISION
          / "sources/filter/emboss/emboss.glsl")
RAW_BYTES = 5160
RAW_SHA256 = "872eff00bdfe411a0dceb66e8b203b5ea1c03015e3eea041d821966354713191"
NORMALIZED_BYTES = 4052
NORMALIZED_SHA256 = "8f6426db42dac9e25c2051a858616efa79350d4236f5a3f49f7e5a4a5f9a3e3c"


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def require_unique(source: str, anchor: str, label: str) -> None:
    count = source.count(anchor)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source anchor, found {count}")


def build() -> dict[str, object]:
    raw = SOURCE.read_bytes()
    if len(raw) != RAW_BYTES or digest(raw) != RAW_SHA256:
        raise RuntimeError("pinned Emboss GLSL source drift")
    text = raw.decode("utf-8")
    parsed = parse_program(text, KEY, {"STYLE": 0})
    normalized = parsed["source"].encode("utf-8")
    if (len(normalized) != NORMALIZED_BYTES
            or digest(normalized) != NORMALIZED_SHA256):
        raise RuntimeError("pinned STYLE=0 normalized source drift")
    typed = analyze_program(parsed, KEY)
    define_tuple = tuple((item.name, item.kind, item.canonical_value)
                         for item in typed.preprocessor_defines)
    if define_tuple != (("STYLE", "int", "0"),):
        raise RuntimeError("Emboss define contract drift")

    anchors = {
        "default_kernel": "kernel[0] = -2.0;",
        "default_offsets": "offsets[0] = vec2(-texelSize.x, -texelSize.y);",
        "general_offsets": "baseOffsetsPx[0] = vec2(-1.0, -1.0);",
        "full_frame": ("all(equal(tileOffset, vec2(0.0))) && "
                       "all(equal(fullResolution, resolution))"),
        "default_dispatch": "angle == 135.0 && height == 1.0",
        "final_clamp_alpha": "vec4(clamp(result, 0.0, 1.0), origColor.a)",
    }
    # The two helpers intentionally repeat the kernel anchor.
    if text.count(anchors["default_kernel"]) != 2:
        raise RuntimeError("Emboss kernel table census drift")
    for label in ("default_offsets", "general_offsets", "full_frame",
                  "default_dispatch", "final_clamp_alpha"):
        require_unique(text, anchors[label], label)

    functions = tuple(function.name for function in typed.functions)
    resources = typed.resources.uniforms
    if functions != ("colorDefaultEmboss", "colorGeneralEmboss", "grayEmboss",
                     "main", "sampleGlobal"):
        raise RuntimeError(f"Emboss function census drift: {functions}")
    if resources != ("tileOffset", "fullResolution", "inputTex", "amount",
                     "angle", "height", "colorAmount", "renderScale"):
        raise RuntimeError(f"Emboss resource ABI drift: {resources}")

    return {
        "schema": "noisemaker-for-cpp.emboss.frontend-probe.v1",
        "program_key": KEY,
        "corpus_revision": REVISION,
        "raw_source": {"bytes": len(raw), "sha256": digest(raw)},
        "style0_normalized_source": {
            "bytes": len(normalized), "sha256": digest(normalized)},
        "define_contract": [list(item) for item in define_tuple],
        "function_order": list(functions),
        "resource_order": list(resources),
        "table_census": {
            "float_9_declarations": text.count("float kernel[9];"),
            "vec2_9_declarations": (text.count("vec2 offsets[9];")
                                    + text.count("vec2 baseOffsetsPx[9];")),
            "kernel_literal_stores": sum(text.count(f"kernel[{i}] =")
                                         for i in range(9)),
            "default_offset_literal_stores": sum(
                text.count(f"offsets[{i}] =") for i in range(9)),
            "general_offset_literal_stores": sum(
                text.count(f"baseOffsetsPx[{i}] =") for i in range(9)),
            "nine_trip_loops": text.count("for (int i = 0; i < 9; i++)"),
        },
        "bvec2_closure": {
            "equal_vec2_calls": text.count("equal("),
            "all_bvec2_calls": text.count("all("),
            "full_frame_anchor_unique": True,
        },
        "source_hash_authentication_rejects_any_exact_mutation": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    result = build()
    expected_tables = {
        "float_9_declarations": 2,
        "vec2_9_declarations": 2,
        "kernel_literal_stores": 18,
        "default_offset_literal_stores": 9,
        "general_offset_literal_stores": 9,
        "nine_trip_loops": 2,
    }
    if result["table_census"] != expected_tables:
        raise RuntimeError(f"Emboss table census drift: {result['table_census']}")
    if result["bvec2_closure"]["equal_vec2_calls"] != 2:
        raise RuntimeError("Emboss equal census drift")
    if result["bvec2_closure"]["all_bvec2_calls"] != 2:
        raise RuntimeError("Emboss all census drift")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
