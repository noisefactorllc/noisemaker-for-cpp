#!/usr/bin/env python3
"""Fail-closed materializer for the Effects188 canonical oracle."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import pathlib
import re
import struct
import subprocess
import tempfile
from typing import Any, Callable

ROOT = pathlib.Path(__file__).resolve().parents[2]
PARITY = ROOT / "docs/port-engineering/effects-parity"
ORACLE = PARITY / "effects188-oracles.json"
REPORT = PARITY / "effects188-oracle-report.md"
GENERATOR = PARITY / "effects188_oracle_generator.mjs"
TARGET = ROOT / "tests/oracles/effects188_expected.inc"
SCHEMA = "noisemaker-for-cpp.effects188.pixel-parity.v1"
PROGRAM = "classicNoisedeck/effects:effects"
CORPUS = "a024dc3a960cc44af454abc7aebce50456c194e6"
SOURCE_RELATIVE = f"tools/glslcpp/corpus/{CORPUS}/sources/classicNoisedeck/effects/effects.glsl"
SOURCE_SHA = "e3b742be53b6b1b0dd5e089a805ff02a931cd14643d0a0abe376bd8044e8ec6c"
CASE_INPUT_DIMS = {
    "rotation-scale": (7, 5),
    "offset-arms": (6, 6),
    "intensity-negative": (6, 4),
    "intensity-positive": (6, 4),
    "time-witness": (8, 5),
    "tile-route": (9, 8),
}
CASE_SPECS = [
    {
        "name": "rotation-scale", "coverage": "rotate2D mat2", "route": "full",
        "width": 7, "height": 5, "input_width": 7, "input_height": 5,
        "t": 2, "seed": 1, "tileOffset": [0, 0], "fullResolution": [7, 5],
        "uniforms": {"renderScale": 1, "time": 0, "effectAmt": 1, "scaleAmt": 75, "rotation": 45, "offsetX": 0, "offsetY": 0, "intensity": 0, "saturation": 0},
        "input_f32_sha256": "862274e98a2b319fba1cb18ecaba26f5a521ae8cc537557c4ed24fd0182cbd96",
        "output_f32_sha256": "862274e98a2b319fba1cb18ecaba26f5a521ae8cc537557c4ed24fd0182cbd96",
        "output_rgba8_sha256": "c3af6f45935649272b891b2caf5a5b33d2a097525493153fefa3da16135ecca9",
    },
    {
        "name": "offset-arms", "coverage": "offset maps", "route": "full",
        "width": 6, "height": 6, "input_width": 6, "input_height": 6,
        "t": 3, "seed": 1, "tileOffset": [0, 0], "fullResolution": [6, 6],
        "uniforms": {"renderScale": 1, "time": 0, "effectAmt": 1, "scaleAmt": 100, "rotation": 0, "offsetX": 40, "offsetY": -30, "intensity": 0, "saturation": 0},
        "input_f32_sha256": "94f49cbd8f40354e97f072e69e31bafaec69637ad14d66b41ad7f26851d7dd33",
        "output_f32_sha256": "94f49cbd8f40354e97f072e69e31bafaec69637ad14d66b41ad7f26851d7dd33",
        "output_rgba8_sha256": "aca69166b3954e8cab142b6579a324ed1b091f1e21f2dc6ef3594e0b163488b1",
    },
    {
        "name": "intensity-negative", "coverage": "negative brightness/saturation", "route": "full",
        "width": 6, "height": 4, "input_width": 6, "input_height": 4,
        "t": 5, "seed": 1, "tileOffset": [0, 0], "fullResolution": [6, 4],
        "uniforms": {"renderScale": 1, "time": 0, "effectAmt": 1, "scaleAmt": 100, "rotation": 0, "offsetX": 0, "offsetY": 0, "intensity": -60, "saturation": -40},
        "input_f32_sha256": "b8101b77176fd2670bca1cf43bdd40b106afaf57c6f0cfb9b0a88321c7d9e02f",
        "output_f32_sha256": "6a0366778c576976faf4fc0d1c5f3d6b80381e9c61ff7180c8aaa89abd199a27",
        "output_rgba8_sha256": "9789faf79dfe48018008585565ccb9f57469cad54beec380230a3c6b0a58e66e",
    },
    {
        "name": "intensity-positive", "coverage": "positive brightness/saturation", "route": "full",
        "width": 6, "height": 4, "input_width": 6, "input_height": 4,
        "t": 4, "seed": 1, "tileOffset": [0, 0], "fullResolution": [6, 4],
        "uniforms": {"renderScale": 1, "time": 0, "effectAmt": 1, "scaleAmt": 100, "rotation": 0, "offsetX": 0, "offsetY": 0, "intensity": 60, "saturation": 40},
        "input_f32_sha256": "c26ac5b7a5999f3d3734ee4954e5bd2b7ff07efcc9b0c073cd7256c2ba8a04b7",
        "output_f32_sha256": "65582f26cbde8bb94d6e31b9bbde73dda7052c7bd623b3e39d8c4abade85f830",
        "output_rgba8_sha256": "af685b97b640303b183315a52e539620061fd481b350b0d46e4354ff070cb365",
    },
    {
        "name": "time-witness", "coverage": "periodic offsets", "route": "full",
        "width": 8, "height": 5, "input_width": 8, "input_height": 5,
        "t": 6, "seed": 1, "tileOffset": [0, 0], "fullResolution": [8, 5],
        "uniforms": {"renderScale": 1, "time": 1.25, "effectAmt": 1, "scaleAmt": 100, "rotation": 0, "offsetX": 0, "offsetY": 0, "intensity": 0, "saturation": 0},
        "input_f32_sha256": "870702f3af9f9c14e323efdacf518a254675c7605f00d36d7495c3f3b0cd9bd5",
        "output_f32_sha256": "870702f3af9f9c14e323efdacf518a254675c7605f00d36d7495c3f3b0cd9bd5",
        "output_rgba8_sha256": "b3a429c1e8cb0d3e5db3b7138954ad4021f941e8cd4fc7a627b096eaef23633e",
    },
    {
        "name": "tile-route", "coverage": "tile route", "route": "tile",
        "width": 4, "height": 3, "input_width": 9, "input_height": 8,
        "t": 7, "seed": 1, "tileOffset": [2, 3], "fullResolution": [9, 8],
        "uniforms": {"renderScale": 1, "time": 0, "effectAmt": 1, "scaleAmt": 100, "rotation": 0, "offsetX": 0, "offsetY": 0, "intensity": 0, "saturation": 0},
        "input_f32_sha256": "7c9a1000d930d53bc77027780a67532d9ac8a51f9f7095b86a0638395bbd01e3",
        "output_f32_sha256": "9bc1da6319c76186eef414f73419ef37926488bc774ce54798d63fd5281d22b4",
        "output_rgba8_sha256": "fc670cbc687fef34e417b8340513f3e9908aade7a739975fa8aa89781434bea7",
    },
]
NATIVE_PREFLIGHT = [
    {"binding": "inputTex", "abi": "sampler2D", "expected_category": "Sampler2D", "wrong_category": "Number", "wrong_value": {"category": "Number", "number": 1, "vec2": [0, 0]}, "missing_strategy": "omit texture/uniform binding", "wrong_strategy": "set_uniform_same_name_and_omit_texture", "missing_status": "pending_shared_native_integration", "wrong_status": "pending_shared_native_integration"},
]

FACTORY_TEXT_SHA = "ebf43ff45f4a3568854da02b41baf6b1a25efd2bc5bbf2d8cf78f0a11e3dd81a"
FACTORY_SLICE_SHA = "a029e3a32e400d3d9fb0cd9c7e9914f4fd2132ddd848c0a7210f690ed21f3970"
BINDINGS = [
    "inputTex", "resolution", "tileOffset", "fullResolution", "renderScale",
    "time", "effectAmt", "scaleAmt", "rotation", "offsetX", "offsetY",
    "intensity", "saturation",
]
BINDING_ABI = {
    "inputTex": "sampler2D",
    "resolution": "Vec2",
    "tileOffset": "Vec2",
    "fullResolution": "Vec2",
    "renderScale": "number",
    "time": "number",
    "effectAmt": "number",
    "scaleAmt": "number",
    "rotation": "number",
    "offsetX": "number",
    "offsetY": "number",
    "intensity": "number",
    "saturation": "number",
}
NATIVE_PREFLIGHT.extend({"binding": name, "abi": BINDING_ABI[name], "expected_category": "Vec2" if BINDING_ABI[name] == "Vec2" else "Number", "wrong_category": "Number" if BINDING_ABI[name] == "Vec2" else "Vec2", "wrong_value": {"category": "Number", "number": 1, "vec2": [0, 0]} if BINDING_ABI[name] == "Vec2" else {"category": "Vec2", "number": 0, "vec2": [1, 1]}, "missing_strategy": "omit texture/uniform binding", "wrong_strategy": "set_uniform_same_name", "missing_status": "pending_shared_native_integration", "wrong_status": "pending_shared_native_integration"} for name in BINDINGS[1:])
TABLE_NAMES = ["emboss", "sharpen", "blur", "edge", "edge2", "edge3", "sharpenBlur"]
TABLE_VALUES = {
    "emboss": [-2, -1, 0, -1, 1, 1, 0, 1, 2],
    "sharpen": [-1, 0, -1, 0, 5, 0, -1, 0, -1],
    "blur": [1, 2, 1, 2, 4, 2, 1, 2, 1],
    "edge": [-1, -1, -1, -1, 8, -1, -1, -1, -1],
    "edge2": [-1, 0, -1, 0, 4, 0, -1, 0, -1],
    "edge3": [-0.875, -0.75, -0.875, -0.75, 5, -0.75, -0.875, -0.75, -0.875],
    "sharpenBlur": [-2, 2, -2, 2, 1, 2, -2, 2, -2],
}
PINNED_FILES = {
    "canonical_kernels": [
        "src/effects/generated/canonical-kernels.js",
        "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe",
    ],
    "public_catalog": [
        "src/effects/catalog.js",
        "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4",
    ],
    "glsl_kernel": [
        "src/csl/glsl-kernel.js",
        "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa",
    ],
    "glsl_runtime": [
        "src/csl/glsl-runtime.js",
        "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072",
    ],
    "pass_runner": [
        "src/runtime/pass-runner.js",
        "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa",
    ],
    "surface": [
        "src/runtime/surface.js",
        "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
    ],
}
CLOSURE = {
    "src/csl/glsl-kernel.js": "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa",
    "src/csl/glsl-runtime.js": "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072",
    "src/csl/runtime.js": "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee",
    "src/effects/adapters/bit-effects.js": "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7",
    "src/effects/adapters/crt.js": "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc",
    "src/effects/adapters/f32-color.js": "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046",
    "src/effects/adapters/fractal.js": "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29",
    "src/effects/adapters/index.js": "40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267",
    "src/effects/adapters/julia.js": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
    "src/effects/adapters/median.js": "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583",
    "src/effects/adapters/palette.js": "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452",
    "src/effects/adapters/snow.js": "202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366",
    "src/effects/catalog.js": "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4",
    "src/effects/definition.js": "fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02",
    "src/effects/generated/canonical-adapter-data.js": "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab",
    "src/effects/generated/canonical-kernels.js": "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe",
    "src/effects/generated/kernels.js": "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01",
    "src/effects/generated/upstream-snapshot.js": "e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090",
    "src/effects/registry.js": "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618",
    "src/runtime/pass-runner.js": "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa",
    "src/runtime/sampler.js": "1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328",
    "src/runtime/surface.js": "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
}
EXPECTED_MUTANTS = {
    "ceil-dropped": "measured-invariant",
    "rotate-angle-map-perturbed": "measured-invariant",
    "brightness-coefficient-perturbed": "output-live",
    "saturation-map-perturbed": "output-live",
    "aspect-ratio-inverted": "measured-invariant",
}
EXPECTED_CLAIMS = {
    "tables": "Seven tables write-only at frozen defines; exact stores are structural.",
    "mat4": "Bicubic mat4 unreachable; native closure structural.",
    "defines": "Nonzero EFFECT/FLIP require separate oracle.",
    "crop": "No crop identity asserted.",
}
HEX = re.compile(r"^0x[0-9a-f]{8}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
ABSOLUTE = re.compile(r"^(?:/|\\|[A-Za-z]:[\\/]|file://|~/|\$HOME(?:[\\/]|$))", re.IGNORECASE)


class MaterializationError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact(obj: Any, keys: set[str], label: str) -> None:
    if not isinstance(obj, dict) or set(obj) != keys:
        raise MaterializationError(f"{label}: exact fields required")


def sha_value(value: Any, label: str) -> None:
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise MaterializationError(f"{label}: malformed sha256")


def integer(value: Any, label: str, positive: bool = False) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or (positive and value <= 0):
        raise MaterializationError(f"{label}: integer contract drift")
    return value


def finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise MaterializationError(f"{label}: finite number required")
    return float(value)


def sidecar_path(path: pathlib.Path) -> pathlib.Path:
    return path.with_name(path.name + ".sha256")


def verify_sidecar(path: pathlib.Path) -> None:
    if not path.is_file():
        raise MaterializationError(f"missing source/artifact: {path}")
    side = sidecar_path(path)
    if not side.is_file():
        raise MaterializationError(f"missing checksum sidecar: {side}")
    fields = side.read_text(encoding="utf-8").split()
    if len(fields) != 2 or fields[1] != path.name or not SHA.fullmatch(fields[0]):
        raise MaterializationError(f"malformed checksum sidecar: {path}")
    if fields[0] != digest(path.read_bytes()):
        raise MaterializationError(f"checksum sidecar drift: {path}")


def verify_sidecars() -> None:
    for path in (ORACLE, REPORT, GENERATOR, pathlib.Path(__file__).resolve(), TARGET):
        verify_sidecar(path)


def scan_absolute(value: Any, label: str) -> None:
    if isinstance(value, str):
        if ABSOLUTE.search(value):
            raise MaterializationError(f"absolute-looking string in {label}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan_absolute(item, f"{label}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            scan_absolute(item, f"{label}.{key}")


def unpack_word(value: Any, label: str) -> int:
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise MaterializationError(f"{label}: malformed f32 word")
    return int(value[2:], 16)


def validate_words(values: Any, count: int, label: str) -> list[int]:
    if not isinstance(values, list) or len(values) != count:
        raise MaterializationError(f"{label}: word count drift")
    return [unpack_word(value, f"{label}[{index}]") for index, value in enumerate(values)]


def words_digest(words: list[int]) -> str:
    return digest(b"".join(struct.pack("<I", word) for word in words))


def validate_bytes(values: Any, count: int, label: str) -> list[int]:
    if not isinstance(values, list) or len(values) != count:
        raise MaterializationError(f"{label}: byte count drift")
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 255 for value in values):
        raise MaterializationError(f"{label}: malformed byte")
    return values


def f32_word(value: Any, label: str) -> int:
    number = finite_number(value, label)
    try:
        return struct.unpack("<I", struct.pack("<f", number))[0]
    except struct.error as exc:
        raise MaterializationError(f"{label}: not representable as f32") from exc


def validate_vec2(binding: Any, label: str) -> None:
    exact(binding, {"abi", "f32_values", "f32_words_le"}, label)
    if binding["abi"] != "Vec2":
        raise MaterializationError(f"{label}: ABI drift")
    values = binding["f32_values"]
    words = validate_words(binding["f32_words_le"], 2, f"{label}.f32_words_le")
    if not isinstance(values, list) or len(values) != 2:
        raise MaterializationError(f"{label}: Vec2 value count drift")
    for index, value in enumerate(values):
        if f32_word(value, f"{label}.f32_values[{index}]") != words[index]:
            raise MaterializationError(f"{label}: value/word drift")


def validate_scalar(binding: Any, label: str) -> None:
    exact(binding, {"abi", "f32_value", "f32_word_le"}, label)
    if binding["abi"] != "number" or f32_word(binding["f32_value"], f"{label}.f32_value") != unpack_word(binding["f32_word_le"], f"{label}.f32_word_le"):
        raise MaterializationError(f"{label}: scalar ABI/value drift")


def validate_input_texture(obj: Any, label: str, width: int, height: int) -> tuple[list[int], str]:
    exact(obj, {"width", "height", "f32_words_le", "f32_sha256", "row_order"}, label)
    if integer(obj["width"], f"{label}.width", True) != width or integer(obj["height"], f"{label}.height", True) != height:
        raise MaterializationError(f"{label}: dimensions drift")
    if obj["row_order"] != "top-down storage; GLSL texture origin bottom-left":
        raise MaterializationError(f"{label}: row order drift")
    sha_value(obj["f32_sha256"], f"{label}.f32_sha256")
    words = validate_words(obj["f32_words_le"], width * height * 4, f"{label}.f32_words_le")
    if words_digest(words) != obj["f32_sha256"]:
        raise MaterializationError(f"{label}: digest drift")
    return words, obj["f32_sha256"]


def validate_output(obj: Any, label: str, width: int, height: int) -> None:
    exact(obj, {"width", "height", "f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256", "finite_lane_count", "nonfinite_lane_count", "alpha_f32_word", "alpha_rgba8_byte"}, label)
    if integer(obj["width"], f"{label}.width", True) != width or integer(obj["height"], f"{label}.height", True) != height:
        raise MaterializationError(f"{label}: dimensions drift")
    count = width * height * 4
    sha_value(obj["f32_sha256"], f"{label}.f32_sha256")
    words = validate_words(obj["f32_words_le"], count, f"{label}.f32_words_le")
    if words_digest(words) != obj["f32_sha256"]:
        raise MaterializationError(f"{label}: f32 digest drift")
    if any(not math.isfinite(struct.unpack("<f", struct.pack("<I", word))[0]) for word in words):
        raise MaterializationError(f"{label}: nonfinite word")
    sha_value(obj["rgba8_sha256"], f"{label}.rgba8_sha256")
    rgba = validate_bytes(obj["rgba8_bytes"], count, f"{label}.rgba8_bytes")
    if digest(bytes(rgba)) != obj["rgba8_sha256"]:
        raise MaterializationError(f"{label}: RGBA8 digest drift")
    if obj["finite_lane_count"] != count or obj["nonfinite_lane_count"] != 0 or obj["alpha_f32_word"] != "0x3f800000" or obj["alpha_rgba8_byte"] != 255:
        raise MaterializationError(f"{label}: alpha/finite contract drift")
    for index in range(3, count, 4):
        if words[index] != 0x3F800000 or rgba[index] != 255:
            raise MaterializationError(f"{label}: alpha lane drift")


def validate_binding(binding: Any, name: str, case: dict[str, Any], spec: dict[str, Any], input_words: list[int], input_sha: str) -> None:
    label = f"case {case['name']} binding {name}"
    abi = BINDING_ABI[name]
    if not isinstance(binding, dict) or binding.get("abi") != abi:
        raise MaterializationError(f"{label}: ABI drift")
    if abi == "sampler2D":
        exact(binding, {"abi", "width", "height", "f32_sha256"}, label)
        if integer(binding["width"], f"{label}.width", True) != spec["input_width"] or integer(binding["height"], f"{label}.height", True) != spec["input_height"]:
            raise MaterializationError(f"{label}: sampler dimensions drift")
        if binding["f32_sha256"] != input_sha or binding["f32_sha256"] != spec["input_f32_sha256"] or len(input_words) != binding["width"] * binding["height"] * 4:
            raise MaterializationError(f"{label}: sampler digest drift")
    elif abi == "Vec2":
        validate_vec2(binding, label)
        expected = {
            "resolution": [spec["width"], spec["height"]],
            "tileOffset": spec["tileOffset"],
            "fullResolution": spec["fullResolution"],
        }[name]
        if binding["f32_values"] != expected:
            raise MaterializationError(f"{label}: semantic Vec2 drift")
    else:
        validate_scalar(binding, label)
        if binding["f32_value"] != spec["uniforms"][name]:
            raise MaterializationError(f"{label}: semantic scalar drift")


def validate_native_preflight(data: dict[str, Any]) -> None:
    rows = data["native_binding_preflight"]
    if not isinstance(rows, list) or rows != NATIVE_PREFLIGHT:
        raise MaterializationError("native binding preflight drift")
    if len(rows) != len(BINDINGS) or [row["binding"] for row in rows] != BINDINGS:
        raise MaterializationError("native binding preflight census drift")
    for row in rows:
        exact(row, {"binding", "abi", "expected_category", "wrong_category", "wrong_value", "missing_strategy", "wrong_strategy", "missing_status", "wrong_status"}, f"native preflight {row.get('binding')}")
        expected_category = "Sampler2D" if row["binding"] == "inputTex" else "Vec2" if BINDING_ABI[row["binding"]] == "Vec2" else "Number"
        expected_wrong = "Number" if row["binding"] == "inputTex" or BINDING_ABI[row["binding"]] == "Vec2" else "Vec2"
        expected_value = {"category": "Number", "number": 1, "vec2": [0, 0]} if expected_wrong == "Number" else {"category": "Vec2", "number": 0, "vec2": [1, 1]}
        if row["expected_category"] != expected_category or row["wrong_category"] != expected_wrong or row["wrong_value"] != expected_value or row["missing_status"] != "pending_shared_native_integration" or row["wrong_status"] != "pending_shared_native_integration":
            raise MaterializationError("native preflight status/category/value drift")


def validate_matrix(data: dict[str, Any], cases: list[dict[str, Any]]) -> None:
    matrix = data["abi_rejection_matrix"]
    exact(matrix, {"harness", "case", "rows"}, "abi_rejection_matrix")
    if matrix["harness"] != "generator ABI preflight" or matrix["case"] != cases[0]["name"]:
        raise MaterializationError("ABI harness identity drift")
    rows = matrix["rows"]
    if not isinstance(rows, list) or [row.get("binding") for row in rows] != BINDINGS:
        raise MaterializationError("ABI rejection census drift")
    for row, name in zip(rows, BINDINGS):
        exact(row, {"binding", "omit", "wrong_variant"}, f"ABI row {name}")
        for key, category in (("omit", "missing"), ("wrong_variant", BINDING_ABI[name])):
            result = row[key]
            exact(result, {"accepted", "error_name", "binding", "category"}, f"ABI row {name}.{key}")
            if result != {"accepted": False, "error_name": "KernelBindingError", "binding": name, "category": category}:
                raise MaterializationError(f"ABI rejection behavior drift for {name}.{key}")


def validate_mutant_rows(rows: Any, case_names: list[str], label: str) -> list[str]:
    if not isinstance(rows, list) or [row.get("case") for row in rows] != case_names:
        raise MaterializationError(f"{label}: case census drift")
    differs: list[str] = []
    for row in rows:
        exact(row, {"case", "differs", "changed_lane_count", "changed_rgba8_byte_count", "first_mismatch"}, f"{label} {row.get('case')}")
        if not isinstance(row["differs"], bool) or integer(row["changed_lane_count"], "changed_lane_count") < 0 or integer(row["changed_rgba8_byte_count"], "changed_rgba8_byte_count") < 0:
            raise MaterializationError(f"{label}: changed-count drift")
        mismatch = row["first_mismatch"]
        if row["differs"]:
            differs.append(row["case"])
            if row["changed_lane_count"] <= 0 or not isinstance(mismatch, dict):
                raise MaterializationError(f"{label}: missing witness")
            exact(mismatch, {"index", "channel", "expected", "actual"}, f"{label} first_mismatch")
            integer(mismatch["index"], f"{label} mismatch index")
            if mismatch["channel"] not in {"r", "g", "b", "a"}:
                raise MaterializationError(f"{label}: mismatch channel drift")
            unpack_word(mismatch["expected"], f"{label} expected word")
            unpack_word(mismatch["actual"], f"{label} actual word")
        elif mismatch is not None or row["changed_lane_count"] != 0 or row["changed_rgba8_byte_count"] != 0:
            raise MaterializationError(f"{label}: invariant row drift")
    return differs


def validate_payload(data: Any) -> dict[str, Any]:
    required = {"schema", "program_key", "corpus_revision", "defines", "source", "canonical_factory", "authority", "generator_provenance", "table_contract", "comparer_self_tests", "binding_names", "binding_abi", "abi_rejection_matrix", "native_binding_preflight", "case_specs", "render_cases", "mutation_ledger", "write_only_table_control", "unreachable_mat4_control", "claim_boundaries", "output_storage_control"}
    exact(data, required, "oracle")
    scan_absolute(data, "oracle")
    if data["schema"] != SCHEMA or data["program_key"] != PROGRAM or data["corpus_revision"] != CORPUS or data["defines"] != {"EFFECT": 0, "FLIP": 0} or data["binding_names"] != BINDINGS or data["binding_abi"] != BINDING_ABI:
        raise MaterializationError("schema/program/defines/binding census drift")
    exact(data["source"], {"relative_path", "bytes", "sha256"}, "source")
    if data["source"]["relative_path"] != SOURCE_RELATIVE or data["source"]["bytes"] != 21087 or data["source"]["sha256"] != SOURCE_SHA:
        raise MaterializationError("GLSL source identity drift")
    sha_value(data["source"]["sha256"], "source.sha256")
    source_path = ROOT / SOURCE_RELATIVE
    source_bytes = source_path.read_bytes()
    if len(source_bytes) != data["source"]["bytes"] or digest(source_bytes) != data["source"]["sha256"]:
        raise MaterializationError("GLSL source bytes drift")
    exact(data["canonical_factory"], {"name", "text_sha256", "source_slice_sha256"}, "canonical_factory")
    if data["canonical_factory"]["name"] != "canonicalFactory7" or data["canonical_factory"]["text_sha256"] != FACTORY_TEXT_SHA or data["canonical_factory"]["source_slice_sha256"] != FACTORY_SLICE_SHA:
        raise MaterializationError("canonical factory identity drift")
    sha_value(data["canonical_factory"]["text_sha256"], "canonical_factory.text_sha256")
    sha_value(data["canonical_factory"]["source_slice_sha256"], "canonical_factory.source_slice_sha256")
    exact(data["generator_provenance"], {"relative_path", "sha256"}, "generator_provenance")
    if data["generator_provenance"]["relative_path"] != "docs/port-engineering/effects-parity/effects188_oracle_generator.mjs" or data["generator_provenance"]["sha256"] != digest(GENERATOR.read_bytes()):
        raise MaterializationError("generator provenance drift")
    authority = data["authority"]
    exact(authority, {"node", "oracle", "pinned_files", "cpu_root", "live_checkout", "canonical_public_identity", "adapter_override_absent", "import_closure"}, "authority")
    if authority["node"] != "v24.7.0" or authority["oracle"] != "unmodified public canonical factory from immutable snapshot" or authority["cpu_root"] != "<immutable-cpu-snapshot-root>" or authority["live_checkout"] != "<live-noisemaker-for-cpu-checkout>" or authority["canonical_public_identity"] is not True or authority["adapter_override_absent"] is not True or authority["pinned_files"] != PINNED_FILES:
        raise MaterializationError("complete authority identity drift")
    closure = authority["import_closure"]
    if not isinstance(closure, list) or len(closure) != len(CLOSURE) or [item.get("relative_path") for item in closure] != sorted(CLOSURE):
        raise MaterializationError("transitive closure path drift")
    for item, relative in zip(closure, sorted(CLOSURE)):
        exact(item, {"relative_path", "sha256"}, f"closure {relative}")
        if item["relative_path"] != relative or item["sha256"] != CLOSURE[relative] or relative.startswith("/") or ".." in pathlib.PurePosixPath(relative).parts:
            raise MaterializationError("transitive closure digest drift")
    table = data["table_contract"]
    exact(table, {"names", "values", "element_count", "reads_at_defines", "write_only_at_defines"}, "table_contract")
    if table["names"] != TABLE_NAMES or table["values"] != TABLE_VALUES or table["element_count"] != 63 or table["reads_at_defines"] != [] or table["write_only_at_defines"] is not True or sum(len(values) for values in table["values"].values()) != 63:
        raise MaterializationError("table contract drift")
    for name in TABLE_NAMES:
        if not isinstance(table["values"][name], list) or len(table["values"][name]) != 9:
            raise MaterializationError("table dimensions drift")
        for value in table["values"][name]:
            finite_number(value, f"table {name}")
    comparer = data["comparer_self_tests"]
    exact(comparer, {"red", "green"}, "comparer_self_tests")
    exact(comparer["red"], {"old_numeric_equality_accepted_signed_zero"}, "comparer_self_tests.red")
    exact(comparer["green"], {"exact_word_comparer_rejected_signed_zero", "changed_lane_count"}, "comparer_self_tests.green")
    if comparer["red"]["old_numeric_equality_accepted_signed_zero"] is not True or comparer["green"]["exact_word_comparer_rejected_signed_zero"] is not True or comparer["green"]["changed_lane_count"] != 1:
        raise MaterializationError("comparer behavioral TDD evidence drift")
    validate_native_preflight(data)
    specs = data["case_specs"]
    if specs != CASE_SPECS:
        raise MaterializationError("frozen case specifications drift")
    cases = data["render_cases"]
    if not isinstance(cases, list) or len(cases) != len(CASE_SPECS) or len({case.get("name") for case in cases}) != len(CASE_SPECS):
        raise MaterializationError("case census drift")
    case_names: list[str] = []
    dimensions: set[tuple[int, int]] = set()
    routes: set[str] = set()
    for index, (case, spec) in enumerate(zip(cases, CASE_SPECS)):
        exact(case, {"name", "coverage", "route", "width", "height", "input_texture", "bindings", "output_expected", "canonical_repeat", "public_canonical"}, f"case {index}")
        if not isinstance(case["name"], str) or not case["name"] or not isinstance(case["coverage"], str) or not case["coverage"] or case["route"] not in {"full", "tile"}:
            raise MaterializationError(f"case {index}: identity drift")
        if case["name"] != spec["name"] or case["coverage"] != spec["coverage"] or case["route"] != spec["route"]:
            raise MaterializationError(f"case {index}: frozen identity drift")
        width = integer(case["width"], f"case {index}.width", True)
        height = integer(case["height"], f"case {index}.height", True)
        if (width, height) != (spec["width"], spec["height"]):
            raise MaterializationError(f"case {index}: frozen dimensions drift")
        expected_input_width, expected_input_height = spec["input_width"], spec["input_height"]
        dimensions.add((width, height)); routes.add(case["route"]); case_names.append(case["name"])
        input_words, input_sha = validate_input_texture(case["input_texture"], f"case {index}.input_texture", expected_input_width, expected_input_height)
        if case["input_texture"]["width"] != expected_input_width or case["input_texture"]["height"] != expected_input_height:
            raise MaterializationError(f"case {index}: input dimensions drift")
        if case["route"] == "full" and (case["input_texture"]["width"] != width or case["input_texture"]["height"] != height):
            raise MaterializationError(f"case {index}: full route dimensions drift")
        validate_output(case["output_expected"], f"case {index}.output_expected", width, height)
        if case["input_texture"]["f32_sha256"] != spec["input_f32_sha256"] or case["output_expected"]["f32_sha256"] != spec["output_f32_sha256"] or case["output_expected"]["rgba8_sha256"] != spec["output_rgba8_sha256"]:
            raise MaterializationError(f"case {index}: frozen digest drift")
        exact(case["canonical_repeat"], {"exact"}, f"case {index}.canonical_repeat")
        exact(case["public_canonical"], {"exact"}, f"case {index}.public_canonical")
        if case["canonical_repeat"]["exact"] is not True or case["public_canonical"]["exact"] is not True:
            raise MaterializationError(f"case {index}: canonical identity drift")
        bindings = case["bindings"]
        if not isinstance(bindings, dict) or set(bindings) != set(BINDINGS):
            raise MaterializationError(f"case {index}: binding fields drift")
        for name in BINDINGS:
            validate_binding(bindings[name], name, case, spec, input_words, input_sha)
    if len(dimensions) < 3 or routes != {"full", "tile"}:
        raise MaterializationError("degenerate case matrix")
    validate_matrix(data, cases)
    ledger = data["mutation_ledger"]
    if not isinstance(ledger, list) or len(ledger) != len(EXPECTED_MUTANTS) or [item.get("name") for item in ledger] != list(EXPECTED_MUTANTS):
        raise MaterializationError("mutation ledger census drift")
    for item in ledger:
        exact(item, {"name", "classification", "results", "witness_cases", "control_cases"}, f"mutant {item.get('name')}")
        if item["classification"] != EXPECTED_MUTANTS[item["name"]]:
            raise MaterializationError(f"mutant {item['name']}: classification drift")
        differs = validate_mutant_rows(item["results"], case_names, f"mutant {item['name']}.results")
        if item["witness_cases"] != differs or item["control_cases"] != [name for name in case_names if name not in differs]:
            raise MaterializationError(f"mutant {item['name']}: witness/control drift")
        if item["classification"] == "output-live" and not differs:
            raise MaterializationError(f"mutant {item['name']}: output-live mutant has no witness")
        if item["classification"] == "measured-invariant" and differs:
            raise MaterializationError(f"mutant {item['name']}: invariant mutant diverged")
    for key, expected_name in (("write_only_table_control", "table-content-perturbed"), ("unreachable_mat4_control", "bicubic-mat4-dead-mutated")):
        control = data[key]
        exact(control, {"mutant", "rows", "changed_lanes"}, key)
        if control["mutant"] != expected_name or control["changed_lanes"] != 0 or validate_mutant_rows(control["rows"], case_names, f"{key}.rows"):
            raise MaterializationError(f"{key}: invariant control drift")
    exact(data["claim_boundaries"], set(EXPECTED_CLAIMS), "claim_boundaries")
    if data["claim_boundaries"] != EXPECTED_CLAIMS:
        raise MaterializationError("claim boundaries drift")
    storage = data["output_storage_control"]
    exact(storage, {"distinct_buffers", "cases"}, "output_storage_control")
    if storage["distinct_buffers"] is not True or not isinstance(storage["cases"], list) or [row.get("case") for row in storage["cases"]] != case_names:
        raise MaterializationError("output storage census drift")
    for row in storage["cases"]:
        exact(row, {"case", "independent"}, "output_storage_control case")
        if row["independent"] is not True:
            raise MaterializationError("output storage independence drift")
    return data


def load_oracle() -> dict[str, Any]:
    verify_sidecars()
    try:
        data = json.loads(ORACLE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MaterializationError("invalid oracle JSON") from exc
    return validate_payload(data)


def word_rows(values: list[str], per: int = 8) -> str:
    return "\n".join("    " + " ".join(value + "U," for value in values[index:index + per]) for index in range(0, len(values), per))


def byte_rows(values: list[int], per: int = 16) -> str:
    return "\n".join("    " + " ".join(str(value) + "U," for value in values[index:index + per]) for index in range(0, len(values), per))


def cpp_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def cpp_float(value: Any) -> str:
    number = finite_number(value, "C++ Float32 literal")
    if number == 0.0:
        return "0.0f"
    if number.is_integer():
        return f"{int(number)}.0f"
    return f"{number!r}f"


def cpp_word(value: str) -> str:
    unpack_word(value, "C++ word literal")
    return value + "U"


def cpp_category(value: str) -> str:
    if value not in {"Sampler2D", "Vec2", "Number"}:
        raise MaterializationError(f"unknown native binding category: {value}")
    return "NativeBindingCategory::" + value


def render(data: dict[str, Any]) -> str:
    cases = data["render_cases"]
    out = [
        "", "// Generated from the checked Effects188 canonical JavaScript oracle.",
        "// C++ output never participates in these arrays.", "#pragma once", "",
        "namespace effects188_oracle {", "",
        f'inline constexpr std::string_view kOracleSchema = "{data["schema"]}";',
        f'inline constexpr std::string_view kProgramKey = "{PROGRAM}";',
        f"inline constexpr std::size_t kCaseCount = {len(cases)}U;", "",
    ]
    for index, case in enumerate(cases):
        for label, obj in (("Input", case["input_texture"]), ("Expected", case["output_expected"])):
            words = obj["f32_words_le"]
            out += [f"inline constexpr std::array<std::uint32_t, {len(words)}> kCase{index}{label}Words{{{{", word_rows(words), "}};", ""]
        rgba = case["output_expected"]["rgba8_bytes"]
        out += [f"inline constexpr std::array<std::uint8_t, {len(rgba)}> kCase{index}ExpectedRgba8{{{{", byte_rows(rgba), "}};", ""]
    out += [
        "struct CaseView { std::string_view name; std::string_view route; std::size_t width; std::size_t height; std::span<const std::uint32_t> input_words; std::span<const std::uint32_t> expected_words; std::span<const std::uint8_t> expected_rgba8; };",
        f"inline constexpr std::array<CaseView, {len(cases)}> kCases{{{{",
    ]
    for index, case in enumerate(cases):
        out.append(f'  CaseView{{"{case["name"]}", "{case["route"]}", {case["width"]}U, {case["height"]}U, kCase{index}InputWords, kCase{index}ExpectedWords, kCase{index}ExpectedRgba8}},')
    out += [
        "}};", "",
        "enum class NativeBindingCategory { Sampler2D, Vec2, Number };",
        "struct NativeWrongValue { NativeBindingCategory category; float number; std::array<float, 2> vec2; };",
        "struct BindingPreflightView { std::string_view binding; NativeBindingCategory expected_category; NativeBindingCategory wrong_category; NativeWrongValue wrong_value; std::string_view missing_strategy; std::string_view wrong_strategy; std::string_view missing_status; std::string_view wrong_status; };",
        'inline constexpr std::string_view kNativeKernelBindingErrorExecution = "pending_shared_native_integration";',
        f"inline constexpr std::array<BindingPreflightView, {len(data['native_binding_preflight'])}> kBindingPreflight{{{{",
    ]
    for row in data["native_binding_preflight"]:
        value = row["wrong_value"]
        wrong_value = "NativeWrongValue{" + ", ".join((cpp_category(value["category"]), cpp_float(value["number"]), "{" + ", ".join(cpp_float(item) for item in value["vec2"]) + "}")) + "}"
        out.append("  BindingPreflightView{" + ", ".join((cpp_string(row["binding"]), cpp_category(row["expected_category"]), cpp_category(row["wrong_category"]), wrong_value, cpp_string(row["missing_strategy"]), cpp_string(row["wrong_strategy"]), cpp_string(row["missing_status"]), cpp_string(row["wrong_status"]))) + "},")
    out += [
        "}};",
        "constexpr bool native_wrong_value_supported(const BindingPreflightView& row) {",
        "  switch (row.wrong_category) {",
        "    case NativeBindingCategory::Number: return row.wrong_value.category == NativeBindingCategory::Number && row.wrong_value.number == 1.0f;",
        "    case NativeBindingCategory::Vec2: return row.wrong_value.category == NativeBindingCategory::Vec2 && row.wrong_value.vec2[0] == 1.0f && row.wrong_value.vec2[1] == 1.0f;",
        "    case NativeBindingCategory::Sampler2D: return false;",
        "  }",
        "  return false;",
        "}",
        "constexpr bool native_binding_preflight_complete() {",
        "  for (const auto& row : kBindingPreflight) if (!native_wrong_value_supported(row)) return false;",
        "  return true;",
        "}",
        f"static_assert(kBindingPreflight.size() == {len(data['native_binding_preflight'])}U);",
        "static_assert(native_binding_preflight_complete());",
        "",
        "struct NativeSamplerBindingView { std::size_t width; std::size_t height; std::string_view f32_sha256; std::span<const std::uint32_t> words; };",
        "struct NativeVec2BindingView { std::array<float, 2> values; std::array<std::uint32_t, 2> words; };",
        "struct NativeScalarBindingView { float value; std::uint32_t word; };",
        "struct NativeCaseBindingView { std::string_view name; NativeSamplerBindingView inputTex; NativeVec2BindingView resolution; NativeVec2BindingView tileOffset; NativeVec2BindingView fullResolution; NativeScalarBindingView renderScale; NativeScalarBindingView time; NativeScalarBindingView effectAmt; NativeScalarBindingView scaleAmt; NativeScalarBindingView rotation; NativeScalarBindingView offsetX; NativeScalarBindingView offsetY; NativeScalarBindingView intensity; NativeScalarBindingView saturation; };",
        f"inline constexpr std::array<NativeCaseBindingView, {len(cases)}> kCaseBindings{{{{",
    ]
    for index, case in enumerate(cases):
        bindings = case["bindings"]
        sampler = bindings["inputTex"]
        sampler_expr = "NativeSamplerBindingView{" + ", ".join((f"{sampler['width']}U", f"{sampler['height']}U", cpp_string(sampler["f32_sha256"]), f"kCase{index}InputWords")) + "}"
        vec_exprs = []
        for name in ("resolution", "tileOffset", "fullResolution"):
            binding = bindings[name]
            vec_exprs.append("NativeVec2BindingView{{" + ", ".join(cpp_float(value) for value in binding["f32_values"]) + "}, {" + ", ".join(cpp_word(word) for word in binding["f32_words_le"]) + "}}")
        scalar_exprs = []
        for name in BINDINGS[4:]:
            binding = bindings[name]
            scalar_exprs.append("NativeScalarBindingView{" + cpp_float(binding["f32_value"]) + ", " + cpp_word(binding["f32_word_le"]) + "}")
        fields = [cpp_string(case["name"]), sampler_expr, *vec_exprs, *scalar_exprs]
        out.append("  NativeCaseBindingView{" + ", ".join(fields) + "},")
    out += [
        "}};",
        f"static_assert(kCaseBindings.size() == {len(cases)}U);",
        "static_assert(kCaseBindings.size() == kCaseCount);",
        "",
        "struct MutantWitnessView { std::string_view mutant; std::string_view case_name; bool witnesses; std::size_t changed_lane_count; };",
        f"inline constexpr std::array<MutantWitnessView, {sum(len(item['results']) for item in data['mutation_ledger'])}> kMutantWitnesses{{{{",
    ]
    for mutant in data["mutation_ledger"]:
        for row in mutant["results"]:
            out.append(f'  MutantWitnessView{{"{mutant["name"]}", "{row["case"]}", {str(row["differs"]).lower()}, {row["changed_lane_count"]}U}},')
    out += ["}};", "", "}  // namespace effects188_oracle", ""]
    return "\n".join(out)


def run_native_cpp_self_test() -> None:
    source = r'''
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>
#include <type_traits>
#include "tests/oracles/effects188_expected.inc"
using namespace effects188_oracle;
constexpr bool map_wrong(const BindingPreflightView& row) {
  switch (row.wrong_category) {
    case NativeBindingCategory::Number:
      return row.wrong_value.category == NativeBindingCategory::Number && row.wrong_value.number == 1.0f;
    case NativeBindingCategory::Vec2:
      return row.wrong_value.category == NativeBindingCategory::Vec2 && row.wrong_value.vec2[0] == 1.0f && row.wrong_value.vec2[1] == 1.0f;
    case NativeBindingCategory::Sampler2D:
      return false;
  }
  return false;
}
consteval bool exhaustive() {
  static_assert(std::is_enum_v<decltype(kBindingPreflight[0].expected_category)>);
  static_assert(std::is_enum_v<decltype(kBindingPreflight[0].wrong_category)>);
  if (kBindingPreflight.size() != 13U || kCaseBindings.size() != 6U) return false;
  constexpr std::array<NativeBindingCategory, 13> expected{
      NativeBindingCategory::Sampler2D, NativeBindingCategory::Vec2, NativeBindingCategory::Vec2,
      NativeBindingCategory::Vec2, NativeBindingCategory::Number, NativeBindingCategory::Number,
      NativeBindingCategory::Number, NativeBindingCategory::Number, NativeBindingCategory::Number,
      NativeBindingCategory::Number, NativeBindingCategory::Number, NativeBindingCategory::Number,
      NativeBindingCategory::Number};
  for (std::size_t i = 0; i < expected.size(); ++i)
    if (kBindingPreflight[i].expected_category != expected[i] || !map_wrong(kBindingPreflight[i])) return false;
  if (kCaseBindings[0].resolution.values[0] != 7.0f || kCaseBindings[0].resolution.words[0] != 0x40e00000U) return false;
  if (kCaseBindings[5].inputTex.width != 9U || kCaseBindings[5].inputTex.height != 8U) return false;
  if (kCaseBindings[5].tileOffset.values[0] != 2.0f || kCaseBindings[5].fullResolution.values[1] != 8.0f) return false;
  return true;
}
static_assert(exhaustive());
int main() {}
'''
    result = subprocess.run(
        [os.environ.get("CXX", "c++"), "-std=c++20", f"-I{ROOT}", "-fsyntax-only", "-x", "c++", "-"],
        cwd=ROOT,
        input=source,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise MaterializationError("external C++20 preflight/case static assertions failed: " + result.stderr[-2000:])


def expect_reject(label: str, mutate: Callable[[dict[str, Any]], None], baseline: dict[str, Any]) -> None:
    candidate = copy.deepcopy(baseline)
    mutate(candidate)
    try:
        validate_payload(candidate)
    except MaterializationError:
        return
    raise MaterializationError(f"self-test sabotage accepted: {label}")


def self_test() -> None:
    baseline = load_oracle()
    tests: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("schema", lambda d: d.__setitem__("schema", "wrong")),
        ("source bytes", lambda d: d["source"].__setitem__("bytes", 1)),
        ("factory bytes", lambda d: d["canonical_factory"].__setitem__("text_sha256", "0" * 64)),
        ("authority closure missing", lambda d: d["authority"].__setitem__("import_closure", d["authority"]["import_closure"][:-1])),
        ("authority closure escaped", lambda d: d["authority"]["import_closure"][0].__setitem__("relative_path", "../escaped.js")),
        ("binding ABI", lambda d: d["binding_abi"].__setitem__("time", "Vec2")),
        ("native preflight category", lambda d: d["native_binding_preflight"][0].__setitem__("expected_category", "Vec2")),
        ("native preflight status", lambda d: d["native_binding_preflight"][0].__setitem__("wrong_status", "accepted")),
        ("native preflight strategy", lambda d: d["native_binding_preflight"][0].__setitem__("wrong_strategy", "set_uniform_wrong_name")),
        ("binding extra field", lambda d: d["render_cases"][0]["bindings"]["time"].__setitem__("extra", 1)),
        ("sampler dimensions", lambda d: d["render_cases"][0]["bindings"]["inputTex"].__setitem__("width", 99)),
        ("sampler digest", lambda d: d["render_cases"][0]["bindings"]["inputTex"].__setitem__("f32_sha256", "0" * 64)),
        ("resolution semantic value and words", lambda d: d["render_cases"][0]["bindings"]["resolution"].update({"f32_values": [99, 98], "f32_words_le": ["0x42c60000", "0x42c40000"]})),
        ("scalar semantic value and word", lambda d: d["render_cases"][0]["bindings"]["time"].update({"f32_value": 42.0, "f32_word_le": "0x42280000"})),
        ("tile offset semantic", lambda d: d["render_cases"][5]["bindings"]["tileOffset"].update({"f32_values": [0, 0], "f32_words_le": ["0x00000000", "0x00000000"]})),
        ("full resolution semantic", lambda d: d["render_cases"][5]["bindings"]["fullResolution"].update({"f32_values": [4, 3], "f32_words_le": ["0x40800000", "0x40400000"]})),
        ("case route mismatch", lambda d: d["case_specs"][5].__setitem__("route", "full")),
        ("case rename", lambda d: d["case_specs"][0].__setitem__("name", "renamed")),
        ("case reorder", lambda d: d["case_specs"].reverse()),
        ("case duplicate", lambda d: d["render_cases"][1].__setitem__("name", d["render_cases"][0]["name"])),
        ("case extra", lambda d: d["case_specs"].append(copy.deepcopy(d["case_specs"][-1]))),
        ("comparer", lambda d: d["comparer_self_tests"]["green"].__setitem__("changed_lane_count", 0)),
        ("claims", lambda d: d["claim_boundaries"].__setitem__("crop", "changed")),
        ("mutation ledger empty", lambda d: d.__setitem__("mutation_ledger", [])),
        ("mutation witness", lambda d: d["mutation_ledger"][2].__setitem__("witness_cases", [])),
        ("output words", lambda d: d["render_cases"][0]["output_expected"]["f32_words_le"].__setitem__(0, "0x00000000")),
        ("input truncation", lambda d: d["render_cases"][0]["input_texture"]["f32_words_le"].pop()),
        ("output extra words", lambda d: d["render_cases"][0]["output_expected"]["f32_words_le"].append("0x00000000")),
        ("RGBA8 truncation", lambda d: d["render_cases"][0]["output_expected"]["rgba8_bytes"].pop()),
        ("RGBA8 bytes", lambda d: d["render_cases"][0]["output_expected"]["rgba8_bytes"].__setitem__(0, 256)),
        ("provenance", lambda d: d["generator_provenance"].__setitem__("sha256", "0" * 64)),
        ("storage", lambda d: d["output_storage_control"]["cases"][0].__setitem__("independent", False)),
    ]
    for label, mutate in tests:
        expect_reject(label, mutate, baseline)
    for label, value in ((
        ("POSIX", "/tmp/escaped"),
        ("POSIX etc", "/etc/passwd"),
        ("POSIX double slash", "//host/share"),
        ("POSIX usr", "/usr/local/x"),
        ("Windows", "C:\\escaped"),
        ("file URI", "file:///tmp/escaped"),
        ("UNC", "\\\\server\\share"),
        ("home", "~/escaped"),
        ("HOME variable", "$HOME/escaped"),
    )):
        expect_reject(f"absolute {label}", lambda d, value=value: d["claim_boundaries"].__setitem__("crop", value), baseline)
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
        probe = pathlib.Path(directory) / "probe"
        probe.write_bytes(b"probe")
        sidecar_path(probe).write_text("bad sidecar\n", encoding="utf-8")
        try:
            verify_sidecar(probe)
        except MaterializationError:
            tests.append(("sidecar sabotage", lambda d: None))
        else:
            raise MaterializationError("self-test sabotage accepted: sidecar")
    run_native_cpp_self_test()
    tests.append(("external C++20 enum/case static assertions", lambda d: None))
    print(f"Effects188 materializer self-test: {len(tests)}/{len(tests)} pass")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if sum((args.write, args.check, args.self_test)) != 1:
        parser.error("choose exactly one of --write, --check, or --self-test")
    if args.self_test:
        self_test()
        return
    data = load_oracle()
    rendered = render(data)
    if args.write:
        TARGET.write_text(rendered, encoding="utf-8")
        sidecar_path(TARGET).write_text(digest(rendered.encode()) + "  " + TARGET.name + "\n", encoding="utf-8")
        print(f"Effects188 include written: {TARGET}")
        return
    if TARGET.read_text(encoding="utf-8") != rendered:
        raise MaterializationError("effects188_expected.inc drift")
    if digest(TARGET.read_bytes()) != sidecar_path(TARGET).read_text(encoding="utf-8").split()[0]:
        raise MaterializationError("effects188_expected.inc sidecar drift")
    print("Effects188 include checked")


if __name__ == "__main__":
    try:
        main()
    except MaterializationError as exc:
        raise SystemExit(f"materialization rejected: {exc}")
