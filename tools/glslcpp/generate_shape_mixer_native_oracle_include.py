#!/usr/bin/env python3
"""Generate the checked native Shape Mixer182 fixture from canonical JS JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import struct
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/shape-mixer-parity"
ORACLE = PACKAGE / "shape-mixer-parity-oracles.json"
OUTPUT = ROOT / "tests/oracles/shape_mixer182_expected.inc"
PROGRAM_KEY = "classicNoisedeck/shapeMixer:shapeMixer"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
SCHEMA = "noisemaker-for-cpp.shape-mixer182.pixel-parity.v1"
WORD = re.compile(r"0x[0-9a-f]{8}")
HEX64 = re.compile(r"[0-9a-f]{64}")
EXPECTED_CASES = tuple(
    (f"mode-{mode}-{kind}", 7 if kind == "scalar" else 8,
     5 if kind == "scalar" else 6)
    for mode in range(10) for kind in ("scalar", "vector")
) + (
    ("palette-hsv", 9, 5),
    ("palette-oklab-lanes", 5, 9),
    ("palette-rgb-extremes", 9, 5),
    ("animate-minus", 9, 5), ("animate-zero", 9, 5),
    ("animate-plus", 9, 5), ("cycle-minus", 9, 5),
    ("cycle-zero", 9, 5), ("cycle-plus", 9, 5),
    ("levels-one-scalar", 9, 5),
    ("levels-fractional-vector", 9, 5),
    ("loopscale-min", 9, 5), ("loopscale-max", 9, 5),
    ("dead-random-neg-nowrap", 9, 5),
    ("dead-random-neg-wrap", 9, 5),
    ("dead-random-max-nowrap", 9, 5),
    ("dead-random-max-wrap", 9, 5),
    ("tiled-fractional-ratio", 6, 4),
    ("sampler-edge-y", 9, 7),
    ("alpha-three-way", 3, 1),
    ("external-context-base", 9, 5),
    ("external-context-extreme", 9, 5),
)
IDENTITY_GROUPS = (
    ("dead-random-neg-nowrap", "dead-random-neg-wrap",
     "dead-random-max-nowrap", "dead-random-max-wrap"),
    ("external-context-base", "external-context-extreme"),
)
BEHAVIORAL_MUTATIONS = (
    "vector-reflect-scale-sign",
    "vector-reflect-subtract-to-add",
    "vector-reflect-reversed-output-operands",
    "vector-reflect-defensive-normal-normalization",
    "vector-reflect-omit-product-f32",
    "scalar-reflect-mathematical-dot",
    "scalar-reflect-factor-association",
    "vector-refract-wrong-k-formula",
    "vector-refract-omit-left-f32",
    "vector-refract-omit-right-f32",
    "scalar-refract-mathematical-dot",
    "scalar-refract-eta-association",
    "scalar-refract-omit-left-f32",
    "scalar-refract-omit-right-f32",
    "scalar-refract-omit-final-f32",
    "wide-mod-reversed-operands",
    "wide-mod-unmaterialized-divisor",
    "index-linear-condition-fixed-lane",
    "index-srgb-low-write-fixed-lane",
    "index-linear-low-read-fixed-lane",
    "index-srgb-high-write-fixed-lane",
    "index-linear-high-read-fixed-lane",
    "linear-to-srgb-loop-bound-two",
    "linear-to-srgb-branch-inverted",
    "oklab-fwdB-transpose",
    "oklab-fwdA-row-column",
    "oklab-remove-fwdA-intermediate-f32",
) + tuple(
    f"mode-{mode}-{kind}-dispatch"
    for mode in range(10) for kind in ("vector", "scalar")
) + (
    "vector-factor-inversion-removed",
    "scalar-factor-inversion-removed",
    "scalar-vector-overload-swapped",
    "palette-mode-four-branch-inverted",
    "blendy-half-removed",
    "blendy-half-after-factor-inversion",
    "scalar-posterize-order",
    "scalar-posterize-level-one-special-case",
    "vector-posterize-order",
    "cycle-palette-sign-reversed",
    "animate-sign-reversed",
    "input-textures-swapped",
    "second-texture-substituted-with-first",
    "input-texture-size-substituted",
    "second-texture-size-substituted",
    "input-filter-forced-nearest",
    "second-filter-forced-nearest",
    "input-y-convention-inverted",
    "second-y-convention-inverted",
    "alpha-forced-one",
    "alpha-only-input-a",
    "alpha-only-input-b",
    "tile-offset-omitted",
    "full-resolution-replaced-by-local",
    "local-resolution-replaced-by-full",
    "loop-offset-ten-changed",
    "rotate-palette-omitted",
    "repeat-palette-omitted",
    "palette-vector-component-order",
)
BEHAVIORAL_WITNESSES = {
    "vector-reflect-scale-sign": ("mode-7-vector",),
    "vector-reflect-subtract-to-add": ("mode-7-vector",),
    "vector-reflect-reversed-output-operands": ("mode-7-vector",),
    "vector-reflect-defensive-normal-normalization": ("mode-7-vector",),
    "vector-reflect-omit-product-f32": ("mode-7-vector",),
    "scalar-reflect-mathematical-dot": ("mode-7-scalar",),
    "scalar-reflect-factor-association": ("mode-7-scalar",),
    "vector-refract-wrong-k-formula": (
        "mode-8-vector", "animate-minus", "animate-plus"),
    "vector-refract-omit-left-f32": ("mode-8-vector",),
    "vector-refract-omit-right-f32": ("mode-8-vector",),
    "scalar-refract-mathematical-dot": ("mode-8-scalar",),
    "scalar-refract-eta-association": ("mode-8-scalar",),
    "scalar-refract-omit-left-f32": ("mode-8-scalar",),
    "scalar-refract-omit-right-f32": ("mode-8-scalar",),
    "scalar-refract-omit-final-f32": ("mode-8-scalar",),
    "wide-mod-reversed-operands": ("mode-5-vector",),
    "wide-mod-unmaterialized-divisor": ("mode-5-vector",),
    "index-linear-condition-fixed-lane": ("palette-oklab-lanes",),
    "index-srgb-low-write-fixed-lane": ("palette-oklab-lanes",),
    "index-linear-low-read-fixed-lane": ("palette-oklab-lanes",),
    "index-srgb-high-write-fixed-lane": ("palette-oklab-lanes",),
    "index-linear-high-read-fixed-lane": ("palette-oklab-lanes",),
    "linear-to-srgb-loop-bound-two": ("palette-oklab-lanes",),
    "linear-to-srgb-branch-inverted": ("palette-oklab-lanes",),
    "oklab-fwdB-transpose": ("palette-oklab-lanes",),
    "oklab-fwdA-row-column": ("palette-oklab-lanes",),
    "oklab-remove-fwdA-intermediate-f32": ("palette-oklab-lanes",),
    **{f"mode-{mode}-{kind}-dispatch": (f"mode-{mode}-{kind}",)
       for mode in range(10) for kind in ("vector", "scalar")},
    "vector-factor-inversion-removed": (
        "mode-4-vector", "mode-7-vector", "mode-8-vector"),
    "scalar-factor-inversion-removed": ("mode-4-scalar", "mode-8-scalar"),
    "scalar-vector-overload-swapped": (
        "mode-5-scalar", "mode-7-scalar", "mode-8-scalar"),
    "palette-mode-four-branch-inverted": ("mode-4-scalar", "mode-4-vector"),
    "blendy-half-removed": ("mode-5-vector", "mode-7-vector", "mode-8-vector"),
    "blendy-half-after-factor-inversion": (
        "mode-5-vector", "mode-7-vector", "mode-8-vector"),
    "scalar-posterize-order": ("levels-one-scalar",),
    "scalar-posterize-level-one-special-case": ("levels-one-scalar",),
    "vector-posterize-order": ("levels-fractional-vector",),
    "cycle-palette-sign-reversed": ("cycle-plus",),
    "animate-sign-reversed": ("animate-minus",),
    "input-textures-swapped": (
        "mode-0-vector", "tiled-fractional-ratio", "sampler-edge-y"),
    "second-texture-substituted-with-first": (
        "mode-0-vector", "tiled-fractional-ratio", "sampler-edge-y"),
    "input-texture-size-substituted": (
        "tiled-fractional-ratio", "sampler-edge-y"),
    "second-texture-size-substituted": (
        "tiled-fractional-ratio", "sampler-edge-y"),
    "input-filter-forced-nearest": ("mode-1-scalar", "mode-3-vector"),
    "second-filter-forced-nearest": ("mode-3-vector", "sampler-edge-y"),
    "input-y-convention-inverted": ("sampler-edge-y",),
    "second-y-convention-inverted": ("sampler-edge-y",),
    "alpha-forced-one": ("alpha-three-way",),
    "alpha-only-input-a": ("alpha-three-way",),
    "alpha-only-input-b": ("alpha-three-way",),
    "tile-offset-omitted": ("tiled-fractional-ratio",),
    "full-resolution-replaced-by-local": ("tiled-fractional-ratio",),
    "local-resolution-replaced-by-full": ("tiled-fractional-ratio",),
    "loop-offset-ten-changed": (
        "loopscale-min", "loopscale-max", "tiled-fractional-ratio"),
    "rotate-palette-omitted": (
        "palette-rgb-extremes", "palette-hsv", "palette-oklab-lanes"),
    "repeat-palette-omitted": (
        "palette-rgb-extremes", "palette-hsv", "palette-oklab-lanes"),
    "palette-vector-component-order": (
        "palette-rgb-extremes", "palette-hsv", "palette-oklab-lanes"),
}
DIRECT_HELPER_MUTATIONS = (
    "published-vector-reflect-old-one-narrow",
    "published-vector-refract-old-one-narrow",
    "scalar-reflect-negative-zero-positive-normal",
    "scalar-reflect-negative-zero-negative-normal",
    "scalar-reflect-finite",
    "scalar-refract-negative-zero-eta-zero",
    "scalar-refract-negative-zero-negative-normal-eta-one",
    "scalar-refract-finite",
    "vector-refract-negative-k-positive-zero",
    "vector-refract-exact-zero-k",
    "vector-refract-signed-zero",
    "vector-refract-non-unit-normal",
    "vector-refract-nan-staging",
    "wide-mod-direct-0", "wide-mod-direct-1", "wide-mod-direct-2",
    "wide-mod-direct-3", "wide-mod-direct-4",
    "scalar-reflect-nan", "scalar-refract-nan",
)
STRUCTURAL_MUTATIONS = (
    "vector-reflect-dot-child-order",
    "vector-refract-dot-child-order",
    "float-bits-to-uint-positive-zero-numeric-conversion",
    "scalar-uint-xor-lane-0", "scalar-uint-xor-lane-1",
    "scalar-uint-xor-lane-2", "scalar-uint-xor-uvec3-parent",
)
NON_PIXEL_BARRIERS = (
    "fmod_negative_operand_semantics", "loop_bound_four",
    "inverse_oklab_matrices", "vector_final_narrowing_only",
)
DIRECT_HELPER_LEDGER_SHA256 = (
    "e497093f0921a55b0d25fa3b6e48e2b9823e85259991105f0576c30845e2c5ab")
NON_PIXEL_BARRIERS_SHA256 = (
    "44a9fcea1ffe35f16fac11abd6716952ae80feb8932338653a000fb93a49ea6d")


class OracleError(RuntimeError):
    pass


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_sha256(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False).encode("utf-8"))


def sidecar_text(target: pathlib.Path, payload: bytes) -> str:
    return f"{sha256(payload)}  {target.name}\n"


def verify_sidecar(target: pathlib.Path) -> bytes:
    sidecar = target.with_suffix(target.suffix + ".sha256")
    if not target.is_file() or not sidecar.is_file():
        raise OracleError(f"missing checked asset or sidecar: {target}")
    payload = target.read_bytes()
    if sidecar.read_text(encoding="utf-8") != sidecar_text(target, payload):
        raise OracleError(f"checksum sidecar drift: {target}")
    return payload


def require_word_array(value: object, count: int, label: str) -> list[str]:
    if (not isinstance(value, list) or len(value) != count
            or not all(isinstance(item, str) and WORD.fullmatch(item)
                       for item in value)):
        raise OracleError(f"{label}: incomplete Float32 word array")
    return value


def require_byte_array(value: object, count: int, label: str) -> list[int]:
    if (not isinstance(value, list) or len(value) != count
            or not all(isinstance(item, int) and not isinstance(item, bool)
                       and 0 <= item <= 255 for item in value)):
        raise OracleError(f"{label}: incomplete RGBA8 byte array")
    return value


def validate_surface(record: object, width: int, height: int, label: str,
                     *, expected: bool) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise OracleError(f"{label}: surface record missing")
    if (record.get("width"), record.get("height")) != (width, height):
        raise OracleError(f"{label}: dimensions mismatch")
    count = width * height * 4
    raw_words = require_word_array(record.get("f32_words_le"), count, label)
    rgba = require_byte_array(record.get("rgba8_bytes"), count, label)
    word_bytes = b"".join(struct.pack("<I", int(word, 16))
                          for word in raw_words)
    if sha256(word_bytes) != record.get("f32_sha256"):
        raise OracleError(f"{label}: Float32 digest mismatch")
    if sha256(bytes(rgba)) != record.get("rgba8_sha256"):
        raise OracleError(f"{label}: RGBA8 digest mismatch")
    if (record.get("finite_lane_count") != count
            or record.get("nonfinite_lane_count") != 0):
        raise OracleError(f"{label}: finite census mismatch")
    if not isinstance(record.get("probes"), list) or len(record["probes"]) < 5:
        raise OracleError(f"{label}: probe census mismatch")
    if not expected:
        if (record.get("pre_sha256") != record.get("post_sha256")
                or record.get("immutable_exact_bits") is not True):
            raise OracleError(f"{label}: input immutability mismatch")
        if record.get("filter") not in ("nearest", "linear"):
            raise OracleError(f"{label}: sampler filter mismatch")
    return record


def validate_f32_binding(value: object, width: int, label: str) -> list[str]:
    if not isinstance(value, dict):
        raise OracleError(f"{label}: missing f32 binding record")
    key = "f32_word_le" if width == 1 else "f32_words_le"
    words_value = [value.get(key)] if width == 1 else value.get(key)
    return require_word_array(words_value, width, label)


def validate_route_input_provenance(case: dict[str, Any], label: str) -> None:
    routes = case.get("input_route_provenance")
    expected_routes = ("canonical", "canonical_repeat", "public_catalog")
    if not isinstance(routes, dict) or tuple(routes) != expected_routes:
        raise OracleError(f"{label}: route input provenance schema mismatch")
    canonical_hashes = {
        "inputTex": case["inputTex"]["pre_sha256"],
        "tex": case["tex"]["pre_sha256"],
    }
    expected_route_keys = {"inputs_disjoint_backing", "inputTex", "tex"}
    expected_input_keys = {
        "pre_f32_sha256", "post_f32_sha256", "immutable_exact_bits"}
    for route_name, route in routes.items():
        if (not isinstance(route, dict) or set(route) != expected_route_keys
                or route.get("inputs_disjoint_backing") is not True):
            raise OracleError(f"{label}.{route_name}: route schema mismatch")
        for input_name in ("inputTex", "tex"):
            item = route.get(input_name)
            if (not isinstance(item, dict) or set(item) != expected_input_keys
                    or item.get("immutable_exact_bits") is not True):
                raise OracleError(
                    f"{label}.{route_name}.{input_name}: provenance schema mismatch")
            before = item.get("pre_f32_sha256")
            after = item.get("post_f32_sha256")
            if (not isinstance(before, str) or not HEX64.fullmatch(before)
                    or before != after
                    or before != canonical_hashes[input_name]):
                raise OracleError(
                    f"{label}.{route_name}.{input_name}: provenance hash mismatch")


def load() -> tuple[dict[str, Any], str]:
    for asset in (
            PACKAGE / "shape_mixer_parity_oracle_generator.mjs",
            PACKAGE / "shape_mixer_frontend_probe.py",
            PACKAGE / "shape-mixer-parity-oracle-report.md"):
        verify_sidecar(asset)
    payload = verify_sidecar(ORACLE)
    try:
        oracle = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OracleError(f"invalid Shape Mixer JSON: {error}") from error
    if (oracle.get("schema"), oracle.get("program_key"),
            oracle.get("corpus_revision"), oracle.get("define")) != (
                SCHEMA, PROGRAM_KEY, CORPUS_REVISION, {"LOOP_OFFSET": 10}):
        raise OracleError("Shape Mixer schema/program/define mismatch")
    provenance = oracle.get("provenance", {})
    if (provenance.get("authority_commit") !=
            "4834b0144ee0524588144a482cca0067b15f68ec"
            or provenance.get("authority_checkout_clean") is not True
            or provenance.get("node_version") != "v24.7.0"
            or provenance.get("public_factory_is_canonical_identity") is not True
            or provenance.get("adapter_override_absent") is not True):
        raise OracleError("Shape Mixer authority provenance mismatch")
    factory = provenance.get("canonical_factory", {})
    if factory != {
            "name": "canonicalFactory15", "bytes": 26033,
            "sha256": "063bb7cf252349866766abd1c781bb41d32af2d9b71bb02461f34ed8404c8124",
            "source_slice_bytes": 26035,
            "source_slice_sha256": "5c870c15339e431a0972742008caae2f7859836995e508892cd823d98e32c985"}:
        raise OracleError("Shape Mixer canonical factory provenance mismatch")
    source = provenance.get("source", {})
    if (source.get("bytes"), source.get("sha256"),
            source.get("normalized_loop_offset_10_bytes"),
            source.get("normalized_loop_offset_10_sha256")) != (
                21718,
                "704157151a2aa7e0192bd5b3483d5f1a5532a15a6e3f6a3ee0ba93ce70f8a9e4",
                17664,
                "afb1be09867bbbb02f63c115b84ef4fd813d72defc71e2cc7d8891db9113b1b8"):
        raise OracleError("Shape Mixer source provenance mismatch")
    self_tests = oracle.get("comparer_self_tests", {})
    required_self_tests = (
        "equal_area_different_shape_rejected_before_access",
        "signed_zero_rejected_with_equal_rgba8",
        "distinct_quiet_nan_payload_rejected_with_equal_rgba8",
        "final_float32_alpha_lane_reported",
        "independent_final_rgba8_byte_reported",
        "expected_lane_and_byte_count_short_and_long_rejected_before_iteration",
    )
    if any(self_tests.get(name) is not True for name in required_self_tests):
        raise OracleError("Shape Mixer comparer self-test mismatch")
    cases = oracle.get("render_cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise OracleError("Shape Mixer fixture count mismatch")
    for index, (case, expected_case) in enumerate(zip(cases, EXPECTED_CASES)):
        if not isinstance(case, dict):
            raise OracleError(f"Shape Mixer case {index} is not an object")
        name, width, height = expected_case
        if (case.get("name"), case.get("width"), case.get("height")) != expected_case:
            raise OracleError(f"Shape Mixer case {index} identity/shape mismatch")
        for input_name in ("inputTex", "tex"):
            input_record = case.get(input_name, {})
            validate_surface(input_record, input_record.get("width"),
                             input_record.get("height"),
                             f"{name}.{input_name}", expected=False)
        validate_surface(case.get("output_expected"), width, height,
                         f"{name}.output", expected=True)
        bindings = case.get("bindings", {})
        if (bindings.get("LOOP_OFFSET") != 10
                or not isinstance(bindings.get("seed"), int)
                or not isinstance(bindings.get("blendMode"), int)
                or not isinstance(bindings.get("paletteMode"), int)
                or not isinstance(bindings.get("animate"), int)
                or not isinstance(bindings.get("cyclePalette"), int)
                or not isinstance(bindings.get("wrap"), bool)):
            raise OracleError(f"{name}: scalar binding schema mismatch")
        for field in ("time", "loopScale", "rotatePalette",
                      "repeatPalette", "levels"):
            validate_f32_binding(bindings.get(field), 1, f"{name}.{field}")
        for field in ("paletteOffset", "paletteAmp", "paletteFreq",
                      "palettePhase"):
            validate_f32_binding(bindings.get(field), 3, f"{name}.{field}")
        validate_f32_binding(case.get("tile_offset"), 2,
                             f"{name}.tile_offset")
        validate_f32_binding(case.get("full_resolution"), 2,
                             f"{name}.full_resolution")
        for route in ("canonical_repeat", "public_canonical"):
            if case.get(route, {}).get("exact") is not True:
                raise OracleError(f"{name}: {route} mismatch")
        validate_route_input_provenance(case, name)
    if oracle.get("identity_groups") != [list(item) for item in IDENTITY_GROUPS]:
        raise OracleError("Shape Mixer identity-group mismatch")
    by_name = {case["name"]: case for case in cases}
    for group in IDENTITY_GROUPS:
        reference = by_name[group[0]]["output_expected"]
        for name in group[1:]:
            candidate = by_name[name]["output_expected"]
            if (candidate["f32_words_le"] != reference["f32_words_le"]
                    or candidate["rgba8_bytes"] != reference["rgba8_bytes"]):
                raise OracleError(f"Shape Mixer identity differs: {group[0]}/{name}")
    behavioral = oracle.get("behavioral_mutation_ledger")
    if (not isinstance(behavioral, list)
            or tuple(item.get("name") for item in behavioral)
            != BEHAVIORAL_MUTATIONS):
        raise OracleError("Shape Mixer behavioral mutation ledger mismatch")
    for item in behavioral:
        witnesses = item.get("required_witnesses")
        results = item.get("required_witness_results")
        expected_witnesses = BEHAVIORAL_WITNESSES[item["name"]]
        if (tuple(witnesses or ()) != expected_witnesses
                or not isinstance(results, list) or len(results) != len(witnesses)
                or tuple(result.get("case") for result in results)
                != expected_witnesses
                or any(result.get("changed_lane_count", 0) < 1
                       or not isinstance(result.get("first_mismatch"), dict)
                       for result in results)):
            raise OracleError(f"{item.get('name')}: incomplete mutation proof")
        for field in ("anchor_sha256", "replacement_sha256",
                      "mutated_factory_sha256"):
            if not isinstance(item.get(field), str) or not HEX64.fullmatch(item[field]):
                raise OracleError(f"{item.get('name')}: invalid {field}")
    direct = oracle.get("direct_helper_mutation_ledger")
    if (not isinstance(direct, list)
            or tuple(item.get("name") for item in direct)
            != DIRECT_HELPER_MUTATIONS
            or canonical_json_sha256(direct) != DIRECT_HELPER_LEDGER_SHA256):
        raise OracleError("Shape Mixer direct-helper ledger mismatch")
    structural = oracle.get("structural_only_mutation_ledger")
    if (not isinstance(structural, list)
            or tuple(item.get("name") for item in structural)
            != STRUCTURAL_MUTATIONS):
        raise OracleError("Shape Mixer structural-only ledger mismatch")
    runtime_rows = structural[:2]
    expected_runtime = (
        ("vector-reflect-dot-child-order", 102,
         "4c662c611eb3791504489059e1bfaf333d04eeeed1936f4107e1fead1e09fb5f",
         "2bb7127394627068b074ac2a20dcd2b2da7c621859d0d6c7fdf4b779c683b70c",
         "68cf768bc28afb39e022db7eea7d9806ea05137232e734239dc597029dbdcb71"),
        ("vector-refract-dot-child-order", 378,
         "9b4ef5725fe268e68a4122b69a575941d0413d50e6266ae062f969f20327753b",
         "e5881f966c801880cb99af96997b5e6a130b71fa6cb7caea9a036d8e2490072e",
         "330051671e8280b6e6fa577ee42f5d47fd8cbe77eeaf24b3361061a8d10b6c86"),
    )
    for row, (name, owner_bytes, owner_hash, mutant_hash,
              mutated_runtime_hash) in zip(
            runtime_rows, expected_runtime):
        if (row.get("name") != name
                or row.get("source_layer") !=
                "pinned noisemaker-for-cpu GLSL runtime owner slice"
                or row.get("runtime_relative_path") != "src/csl/glsl-runtime.js"
                or row.get("runtime_sha256") !=
                "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072"
                or row.get("owner_bytes") != owner_bytes
                or row.get("owner_sha256") != owner_hash
                or row.get("anchor_occurrences_in_owner") != 1
                or row.get("mutated_owner_sha256") != mutant_hash
                or row.get("mutated_runtime_sha256")
                != mutated_runtime_hash):
            raise OracleError(f"{name}: runtime structural proof mismatch")
    barriers = oracle.get("admitted_non_pixel_barriers")
    if (not isinstance(barriers, dict) or tuple(barriers) != NON_PIXEL_BARRIERS
            or canonical_json_sha256(barriers) != NON_PIXEL_BARRIERS_SHA256):
        raise OracleError("Shape Mixer non-pixel barrier schema mismatch")
    return oracle, sha256(payload)


def array_lines(values: list[str] | list[int], suffix: str,
                width: int) -> list[str]:
    rendered = [f"{value}{suffix}" for value in values]
    return ["    " + ", ".join(rendered[index:index + width]) + ","
            for index in range(0, len(rendered), width)]


def render() -> bytes:
    oracle, oracle_hash = load()
    cases = oracle["render_cases"]
    lines = [
        "// Generated from the checked canonical JavaScript Shape Mixer182 oracle.",
        "// Do not edit; C++ output never participates in these expected arrays.",
        "#pragma once", "", "namespace shape_mixer182_oracle {", "",
        f'inline constexpr std::string_view kOracleSha256 = "{oracle_hash}";',
        f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";',
        f'inline constexpr std::string_view kCorpusRevision = "{CORPUS_REVISION}";',
        f"inline constexpr std::size_t kCaseCount = {len(cases)}U;", "",
    ]
    for index, case in enumerate(cases):
        for suffix, record in (("InputA", case["inputTex"]),
                               ("InputB", case["tex"]),
                               ("Output", case["output_expected"])):
            raw_words = record["f32_words_le"]
            lines.append(f"inline constexpr std::array<std::uint32_t, {len(raw_words)}> kCase{index}{suffix}Words{{{{")
            lines.extend(array_lines(raw_words, "U", 8))
            lines.extend(["}};", ""])
        rgba = case["output_expected"]["rgba8_bytes"]
        lines.append(f"inline constexpr std::array<std::uint8_t, {len(rgba)}> kCase{index}OutputRgba8{{{{")
        lines.extend(array_lines(rgba, "U", 16))
        lines.extend(["}};", ""])
    lines.extend([
        "struct SurfaceView {", "  std::size_t width;", "  std::size_t height;",
        "  std::string_view filter;", "  std::span<const std::uint32_t> words;", "};", "",
        "struct CaseView {", "  std::string_view name;", "  std::size_t width;",
        "  std::size_t height;", "  SurfaceView input_a;", "  SurfaceView input_b;",
        "  std::span<const std::uint32_t> expected_words;",
        "  std::span<const std::uint8_t> expected_rgba8;",
        "  std::int32_t blend_mode;", "  std::int32_t palette_mode;",
        "  std::int32_t seed;", "  std::int32_t animate;",
        "  std::int32_t cycle_palette;", "  bool wrap;",
        "  std::array<std::uint32_t, 5> scalar_f32_words;",
        "  std::array<std::uint32_t, 12> palette_f32_words;",
        "  std::array<std::uint32_t, 2> tile_offset_words;",
        "  std::array<std::uint32_t, 2> full_resolution_words;",
        "  double external_time;", "  std::uint64_t external_seed;", "};", "",
        f"inline constexpr std::array<CaseView, {len(cases)}> kCases{{{{",
    ])
    for index, case in enumerate(cases):
        binding = case["bindings"]
        scalar = [binding[name]["f32_word_le"] for name in
                  ("time", "loopScale", "rotatePalette", "repeatPalette", "levels")]
        palette = sum((binding[name]["f32_words_le"] for name in
                       ("paletteOffset", "paletteAmp", "paletteFreq", "palettePhase")), [])
        tile = case["tile_offset"]["f32_words_le"]
        full = case["full_resolution"]["f32_words_le"]
        a = case["inputTex"]
        b = case["tex"]
        context = case["external_context"]
        lines.append(
            f'  CaseView{{"{case["name"]}", {case["width"]}U, {case["height"]}U, '
            f'SurfaceView{{{a["width"]}U, {a["height"]}U, "{a["filter"]}", kCase{index}InputAWords}}, '
            f'SurfaceView{{{b["width"]}U, {b["height"]}U, "{b["filter"]}", kCase{index}InputBWords}}, '
            f'kCase{index}OutputWords, kCase{index}OutputRgba8, '
            f'{binding["blendMode"]}, {binding["paletteMode"]}, {binding["seed"]}, '
            f'{binding["animate"]}, {binding["cyclePalette"]}, '
            f'{str(binding["wrap"]).lower()}, '
            f'{{{", ".join(word + "U" for word in scalar)}}}, '
            f'{{{", ".join(word + "U" for word in palette)}}}, '
            f'{{{", ".join(word + "U" for word in tile)}}}, '
            f'{{{", ".join(word + "U" for word in full)}}}, '
            f'{context["time"]!r}, {context["seed"]}ULL}},')
    lines.extend(["}};", "", "}  // namespace shape_mixer182_oracle", ""])
    return "\n".join(lines).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        verify_sidecar(pathlib.Path(__file__))
        expected = render()
        if args.write:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(expected)
            OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(
                sidecar_text(OUTPUT, expected), encoding="utf-8")
        else:
            payload = verify_sidecar(OUTPUT)
            if payload != expected:
                raise OracleError("generated Shape Mixer182 native include is stale")
    except (OSError, OracleError) as error:
        print(f"glslcpp: {error}", file=sys.stderr)
        return 1
    oracle, _ = load()
    total = sum(len(case["output_expected"]["f32_words_le"])
                for case in oracle["render_cases"])
    print(f"Shape Mixer182 native oracle include ok "
          f"({len(EXPECTED_CASES)} cases, {total} words, {total} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
