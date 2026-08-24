#!/usr/bin/env python3
"""Generate the checked native Emboss181 fixture from canonical JS JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import struct
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "docs/port-engineering/arrays/emboss-parity"
ORACLE = PACKAGE / "emboss-parity-oracles.json"
OUTPUT = ROOT / "tests/oracles/emboss181_expected.inc"
PROGRAM_KEY = "filter/emboss:emboss"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
EXPECTED_CASES = (
    ("full-frame-default-nonsquare", 9, 6),
    ("general-angle-only", 9, 6),
    ("general-height-only", 9, 6),
    ("general-rotation-extreme", 5, 5),
    ("default-fractional-scale", 8, 5),
    ("general-fractional-scale", 2, 2),
    ("fullresolution-x-mismatch-only", 7, 5),
    ("fullresolution-both-mismatch", 7, 5),
    ("tile-x-offset-only", 7, 5),
    ("both-frame-terms-false", 7, 5),
    ("clamp-and-alpha", 7, 5),
    ("coloramount-control-low", 8, 6),
    ("coloramount-control-high", 8, 6),
    ("external-context-base", 8, 6),
    ("external-context-extreme", 8, 6),
    ("default-asymmetric-impulse", 5, 7),
    ("general-asymmetric-impulse", 9, 7),
)
BEHAVIORAL_MUTATIONS = (
    "dispatch-force-general", "dispatch-force-default",
    "dispatch-drop-angle-half", "dispatch-drop-height-half",
    "dispatch-and-to-or", "default-kernel-0-minus-one",
    "general-kernel-0-minus-one", "default-loop-eight",
    "general-loop-eight", "default-offset-0-flip-x",
    "general-base-offset-0-flip-x", "general-rotation-y-sign",
    "rotatedpx-no-f32-array", "offsetuv-no-f32-array",
    "default-omit-amount", "general-omit-amount",
    "default-omit-render-scale", "general-omit-render-scale",
    "resolution-equal-to-notequal", "resolution-all-to-any",
    "fullframe-and-to-or", "true-arm-swizzle",
    "false-arm-use-local-size", "fullframe-force-true",
    "sample-numerator-use-local-size", "sample-denominator-use-full-size",
    "remove-final-clamp", "alpha-force-one", "style-zero-to-one",
)
STRUCTURAL_MUTATIONS = (
    "tile-equal-to-notequal", "tile-all-to-any",
    "true-arm-use-canvas-size", "fullframe-force-false",
)
WORD = re.compile(r"0x[0-9a-f]{8}")
HEX64 = re.compile(r"[0-9a-f]{64}")


class OracleError(RuntimeError):
    pass


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sidecar_text(target: pathlib.Path, payload: bytes) -> str:
    return f"{sha256(payload)}  {target.name}\n"


def verify_sidecar(target: pathlib.Path) -> bytes:
    if not target.is_file() or not target.with_suffix(
            target.suffix + ".sha256").is_file():
        raise OracleError(f"missing checked asset or sidecar: {target}")
    payload = target.read_bytes()
    actual = target.with_suffix(target.suffix + ".sha256").read_text(
        encoding="utf-8")
    if actual != sidecar_text(target, payload):
        raise OracleError(f"checksum sidecar drift: {target}")
    return payload


def require_number(value: object, label: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OracleError(f"{label} must be numeric")
    return value


def load() -> tuple[dict[str, Any], str]:
    for package_asset in (
            PACKAGE / "emboss_parity_oracle_generator.mjs",
            PACKAGE / "emboss_frontend_probe.py",
            PACKAGE / "emboss-parity-oracle-report.md"):
        verify_sidecar(package_asset)
    payload = verify_sidecar(ORACLE)
    try:
        oracle = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OracleError(f"invalid Emboss JSON: {error}") from error
    if oracle.get("schema") != "noisemaker-for-cpp.emboss181.pixel-parity.v1":
        raise OracleError("Emboss schema mismatch")
    if oracle.get("program_key") != PROGRAM_KEY:
        raise OracleError("Emboss program key mismatch")
    if oracle.get("corpus_revision") != CORPUS_REVISION:
        raise OracleError("Emboss corpus revision mismatch")
    provenance = oracle.get("provenance", {})
    if (provenance.get("authority_commit")
            != "4834b0144ee0524588144a482cca0067b15f68ec"
            or provenance.get("authority_checkout_clean") is not True
            or provenance.get("node_version") != "v24.7.0"
            or provenance.get("canonical_factory") != {
                "name": "canonicalFactory50", "bytes": 8336,
                "sha256": "72f7faa20dfbbf43cab7762c484d13d43e7f3b3102d0a5a70494ab0ab19fa79f"}
            or provenance.get("public_factory_is_canonical_identity") is not True
            or provenance.get("adapter_override_absent") is not True
            or provenance.get("style_define") != {
                "exact": 0, "gray_style_excluded_from_native_authority": 1}):
        raise OracleError("Emboss authority provenance mismatch")
    source = provenance.get("source", {})
    if (source.get("bytes"), source.get("sha256"),
            source.get("style0_normalized_bytes"),
            source.get("style0_normalized_sha256")) != (
                5160,
                "872eff00bdfe411a0dceb66e8b203b5ea1c03015e3eea041d821966354713191",
                4052,
                "8f6426db42dac9e25c2051a858616efa79350d4236f5a3f49f7e5a4a5f9a3e3c"):
        raise OracleError("Emboss source provenance mismatch")
    self_tests = oracle.get("comparer_self_tests", {})
    for field in (
            "equal_length_different_shape_rejected",
            "signed_zero_rejected_with_equal_rgba8",
            "distinct_quiet_nan_payload_rejected_with_equal_rgba8",
            "final_lane_mismatch_rejected",
            "independently_supplied_byte_only_mismatch_rejected"):
        if self_tests.get(field) is not True:
            raise OracleError(f"Emboss comparer self-test missing: {field}")
    cases = oracle.get("render_cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise OracleError("Emboss fixture count mismatch")
    for index, (case, expected) in enumerate(zip(cases, EXPECTED_CASES)):
        if not isinstance(case, dict):
            raise OracleError(f"Emboss case {index} is not an object")
        if (case.get("name"), case.get("width"), case.get("height")) != expected:
            raise OracleError(f"Emboss case {index} identity/shape mismatch")
        name, width, height = expected
        count = width * height * 4
        words = case.get("output_f32_words_le")
        rgba = case.get("output_rgba8_bytes")
        if (not isinstance(words, list) or len(words) != count
                or not all(isinstance(word, str) and WORD.fullmatch(word)
                           for word in words)):
            raise OracleError(f"{name}: incomplete Float32 word array")
        if (not isinstance(rgba, list) or len(rgba) != count
                or not all(isinstance(byte, int) and not isinstance(byte, bool)
                           and 0 <= byte <= 255 for byte in rgba)):
            raise OracleError(f"{name}: incomplete RGBA8 byte array")
        word_bytes = b"".join(struct.pack("<I", int(word, 16))
                              for word in words)
        if sha256(word_bytes) != case.get("output_f32_sha256"):
            raise OracleError(f"{name}: Float32 digest mismatch")
        if sha256(bytes(rgba)) != case.get("output_rgba8_sha256"):
            raise OracleError(f"{name}: RGBA8 digest mismatch")
        if case.get("finite_lane_count") != count or case.get(
                "nonfinite_lane_count") != 0:
            raise OracleError(f"{name}: finite census mismatch")
        if len(case.get("input_probes", [])) < 5 or len(
                case.get("output_probes", [])) < 5:
            raise OracleError(f"{name}: probe census mismatch")
        if case.get("input_immutable_exact_bits") is not True:
            raise OracleError(f"{name}: missing input immutability proof")
        if case.get("input_filter") not in ("nearest", "linear"):
            raise OracleError(f"{name}: invalid input filter")
        for route in ("repeat_identity", "public_catalog_vs_direct_canonical"):
            comparison = case.get(route, {})
            if (comparison.get("float32", {}).get("exact_f32_bits") is not True
                    or comparison.get("rgba8", {}).get(
                        "exact_rgba8_bytes") is not True):
                raise OracleError(f"{name}: {route} is not exact")
        controls = case.get("controls", {})
        if controls.get("style") != 0:
            raise OracleError(f"{name}: non-STYLE0 authority")
        for field in ("amount", "angle", "height", "color_amount",
                      "render_scale", "time"):
            require_number(controls.get(field), f"{name}.{field}")
        for field in ("frame", "external_seed"):
            if (not isinstance(controls.get(field), int)
                    or isinstance(controls.get(field), bool)):
                raise OracleError(f"{name}.{field} must be integer")
        for field in ("tile_offset", "full_resolution"):
            vector = controls.get(field)
            if (not isinstance(vector, list) or len(vector) != 2
                    or any(isinstance(item, bool)
                           or not isinstance(item, (int, float))
                           for item in vector)):
                raise OracleError(f"{name}.{field} must be vec2")
    behavior = oracle.get("behavioral_mutation_ledger")
    if (not isinstance(behavior, list)
            or tuple(item.get("name") for item in behavior)
            != BEHAVIORAL_MUTATIONS):
        raise OracleError("Emboss behavioral mutation ledger mismatch")
    for item in behavior:
        if (not item.get("required_witnesses")
                or item.get("changed_lane_count_at_first_required_witness", 0) < 1
                or not isinstance(item.get(
                    "first_mismatch_at_first_required_witness"), dict)
                or len(item.get("required_witness_results", []))
                != len(item["required_witnesses"])
                or any(result.get("changed_lane_count", 0) < 1
                       or not isinstance(result.get("first_mismatch"), dict)
                       for result in item["required_witness_results"])):
            raise OracleError(f"{item.get('name')}: incomplete mutation proof")
    structural = oracle.get("structural_only_mutation_ledger")
    if (not isinstance(structural, list)
            or tuple(item.get("name") for item in structural)
            != STRUCTURAL_MUTATIONS):
        raise OracleError("Emboss structural-only ledger mismatch")
    if oracle.get("identity_pairs") != [
        ["coloramount-control-low", "coloramount-control-high"],
        ["external-context-base", "external-context-extreme"],
    ]:
        raise OracleError("Emboss identity-pair contract mismatch")
    by_name = {case["name"]: case for case in cases}
    for left_name, right_name in oracle["identity_pairs"]:
        left = by_name[left_name]
        right = by_name[right_name]
        if (left["output_f32_words_le"] != right["output_f32_words_le"]
                or left["output_rgba8_bytes"]
                != right["output_rgba8_bytes"]):
            raise OracleError(
                f"Emboss declared identity pair differs: {left_name}/{right_name}")
    return oracle, sha256(payload)


def cpp_number(value: int | float) -> str:
    if isinstance(value, int):
        return f"{value}.0"
    text = repr(value)
    return text if any(marker in text for marker in ".eE") else text + ".0"


def array_lines(values: list[str] | list[int], suffix: str,
                width: int) -> list[str]:
    rendered = [f"{value}{suffix}" for value in values]
    return ["    " + ", ".join(rendered[index:index + width]) + ","
            for index in range(0, len(rendered), width)]


def render() -> bytes:
    oracle, oracle_hash = load()
    cases = oracle["render_cases"]
    total_words = sum(len(case["output_f32_words_le"]) for case in cases)
    total_bytes = sum(len(case["output_rgba8_bytes"]) for case in cases)
    lines = [
        "// Generated from the checked canonical JavaScript Emboss181 oracle.",
        "// Do not edit; C++ output never participates in these expected arrays.",
        "#pragma once", "", "namespace emboss181_oracle {", "",
        f'inline constexpr std::string_view kOracleSha256 = "{oracle_hash}";',
        f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";',
        f'inline constexpr std::string_view kCorpusRevision = "{CORPUS_REVISION}";',
        f"inline constexpr std::size_t kTotalFloatWords = {total_words}U;",
        f"inline constexpr std::size_t kTotalRgbaBytes = {total_bytes}U;", "",
    ]
    for index, case in enumerate(cases):
        words = case["output_f32_words_le"]
        rgba = case["output_rgba8_bytes"]
        lines.append(f"inline constexpr std::array<std::uint32_t, {len(words)}> kCase{index}FloatWords{{{{")
        lines.extend(array_lines(words, "U", 8))
        lines.extend(["}};", ""])
        lines.append(f"inline constexpr std::array<std::uint8_t, {len(rgba)}> kCase{index}RgbaBytes{{{{")
        lines.extend(array_lines(rgba, "U", 16))
        lines.extend(["}};", ""])
    lines.extend([
        "struct CaseView {",
        "  std::string_view name;",
        "  std::size_t width;",
        "  std::size_t height;",
        "  std::string_view input_kind;",
        "  std::string_view input_filter;",
        "  std::uint32_t input_phase;",
        "  double amount;",
        "  double angle;",
        "  double height_amount;",
        "  double color_amount;",
        "  double render_scale;",
        "  double time;",
        "  std::uint32_t frame;",
        "  std::uint32_t external_seed;",
        "  std::array<double, 2> tile_offset;",
        "  std::array<double, 2> full_resolution;",
        "  std::span<const std::uint32_t> f32_words;",
        "  std::span<const std::uint8_t> rgba8_bytes;",
        "  std::string_view input_f32_sha256;",
        "  std::string_view output_f32_sha256;",
        "  std::string_view output_rgba8_sha256;",
        "};", "",
        f"inline constexpr std::array<CaseView, {len(cases)}> kCases{{{{",
    ])
    for index, case in enumerate(cases):
        controls = case["controls"]
        tile = controls["tile_offset"]
        full = controls["full_resolution"]
        lines.append(
            "  CaseView{" +
            f'"{case["name"]}", {case["width"]}U, {case["height"]}U, '
            f'"{case["input_kind"]}", "{case["input_filter"]}", '
            f'{case["input_phase"]}U, '
            f'{cpp_number(controls["amount"])}, '
            f'{cpp_number(controls["angle"])}, '
            f'{cpp_number(controls["height"])}, '
            f'{cpp_number(controls["color_amount"])}, '
            f'{cpp_number(controls["render_scale"])}, '
            f'{cpp_number(controls["time"])}, '
            f'{controls["frame"]}U, {controls["external_seed"]}U, '
            f'{{{cpp_number(tile[0])}, {cpp_number(tile[1])}}}, '
            f'{{{cpp_number(full[0])}, {cpp_number(full[1])}}}, '
            f'kCase{index}FloatWords, kCase{index}RgbaBytes, '
            f'"{case["input_f32_sha256_before"]}", '
            f'"{case["output_f32_sha256"]}", '
            f'"{case["output_rgba8_sha256"]}"' + "},")
    lines.extend(["}};", "", "}  // namespace emboss181_oracle", ""])
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
                raise OracleError("generated Emboss181 native include is stale")
    except (OSError, OracleError) as error:
        print(f"glslcpp: {error}", file=sys.stderr)
        return 1
    oracle, _ = load()
    total = sum(len(case["output_f32_words_le"])
                for case in oracle["render_cases"])
    print(f"Emboss181 native oracle include ok "
          f"({len(EXPECTED_CASES)} cases, {total} words, {total} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
