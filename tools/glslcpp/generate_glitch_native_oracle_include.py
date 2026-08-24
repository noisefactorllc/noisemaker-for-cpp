"""Generate the exact native Glitch parity fixture from the reviewed JSON oracle."""

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
ORACLE = (ROOT / "docs/port-engineering/matrix/glitch-parity"
          / "glitch-parity-oracles.json")
SIDECAR = ORACLE.with_suffix(ORACLE.suffix + ".sha256")
OUTPUT = ROOT / "tests/oracles/glitch-parity-native.inc"
ORACLE_SHA256 = "535dda6aff731f41974b0f37277949a7d18a2c311c0795ac846a1497acc22e55"
PROGRAM_KEY = "classicNoisedeck/glitch:glitch"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
EXPECTED_CASES = (
    ("matrix-masked-control", 9, 7),
    ("scanlines-max-seed-one", 11, 9),
    ("scanlines-mid-seed-thirty-seven", 13, 10),
    ("scanlines-min-nonzero", 17, 6),
    ("aspect-negative-lens-vignette", 7, 12),
    ("snow-upper-midpoint", 8, 8),
    ("snow-saturated-tiled", 6, 5),
    ("fractional-full-resolution-tile", 5, 9),
)
HEX64 = re.compile(r"[0-9a-f]{64}")
WORD = re.compile(r"0x[0-9a-f]{8}")


class OracleError(RuntimeError):
    pass


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load() -> dict[str, Any]:
    payload = ORACLE.read_bytes()
    if _sha256(payload) != ORACLE_SHA256:
        raise OracleError("Glitch oracle JSON digest mismatch")
    sidecar = SIDECAR.read_text(encoding="utf-8").strip()
    if sidecar != f"{ORACLE_SHA256}  {ORACLE.name}":
        raise OracleError("Glitch oracle sidecar mismatch")
    try:
        oracle = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OracleError(f"invalid Glitch oracle JSON: {error}") from error
    if oracle.get("schema") != 1:
        raise OracleError("unsupported Glitch oracle schema")
    if oracle.get("program_key") != PROGRAM_KEY:
        raise OracleError("Glitch oracle program key mismatch")
    if oracle.get("corpus_revision") != CORPUS_REVISION:
        raise OracleError("Glitch oracle corpus revision mismatch")
    cases = oracle.get("render_cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise OracleError("Glitch oracle must contain exactly eight render cases")
    total_words = 0
    total_bytes = 0
    for index, (case, expected) in enumerate(zip(cases, EXPECTED_CASES)):
        name, width, height = expected
        if not isinstance(case, dict):
            raise OracleError(f"Glitch case {index} is not an object")
        if (case.get("name"), case.get("width"), case.get("height")) != expected:
            raise OracleError(f"Glitch case {index} identity/dimensions mismatch")
        for field in ("phase", "seed"):
            if not isinstance(case.get(field), int) or isinstance(case.get(field), bool):
                raise OracleError(f"{name}: {field} must be an integer")
        if not isinstance(case.get("aspectLens"), bool):
            raise OracleError(f"{name}: aspectLens must be boolean")
        for field in ("time", "xChonk", "yChonk", "glitchiness",
                      "scanlinesAmt", "snowAmt", "vignetteAmt",
                      "aberration", "distortion"):
            value = case.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise OracleError(f"{name}: {field} must be numeric")
        for field in ("effective_tile_offset", "effective_full_resolution"):
            value = case.get(field)
            if (not isinstance(value, list) or len(value) != 2
                    or not all(isinstance(item, (int, float))
                               and not isinstance(item, bool) for item in value)):
                raise OracleError(f"{name}: {field} must contain two numbers")
        words = case.get("output_f32_bits_le")
        rgba = case.get("output_rgba8")
        count = width * height * 4
        if (not isinstance(words, list) or len(words) != count
                or not all(isinstance(word, str) and WORD.fullmatch(word)
                           for word in words)):
            raise OracleError(f"{name}: Float32 oracle array mismatch")
        if (not isinstance(rgba, list) or len(rgba) != count
                or not all(isinstance(byte, int) and not isinstance(byte, bool)
                           and 0 <= byte <= 255 for byte in rgba)):
            raise OracleError(f"{name}: RGBA8 oracle array mismatch")
        f32_hash = case.get("output_f32_sha256")
        rgba_hash = case.get("output_rgba8_sha256")
        if not isinstance(f32_hash, str) or not HEX64.fullmatch(f32_hash):
            raise OracleError(f"{name}: invalid Float32 digest")
        if not isinstance(rgba_hash, str) or not HEX64.fullmatch(rgba_hash):
            raise OracleError(f"{name}: invalid RGBA8 digest")
        word_bytes = b"".join(struct.pack("<I", int(word, 16)) for word in words)
        if _sha256(word_bytes) != f32_hash:
            raise OracleError(f"{name}: Float32 digest does not match raw words")
        if _sha256(bytes(rgba)) != rgba_hash:
            raise OracleError(f"{name}: RGBA8 digest does not match raw bytes")
        total_words += len(words)
        total_bytes += len(rgba)
    if (total_words, total_bytes) != (2468, 2468):
        raise OracleError("Glitch oracle aggregate array census mismatch")
    return oracle


def _cpp_number(value: int | float) -> str:
    if isinstance(value, int):
        return f"{value}.0"
    text = repr(value)
    return text if any(marker in text for marker in ".eE") else text + ".0"


def _array_lines(values: list[str] | list[int], suffix: str,
                 width: int = 8) -> list[str]:
    rendered = [f"{value}{suffix}" for value in values]
    return ["    " + ", ".join(rendered[index:index + width]) + ","
            for index in range(0, len(rendered), width)]


def render() -> bytes:
    oracle = _load()
    lines = [
        "// Generated by tools/glslcpp/generate_glitch_native_oracle_include.py.",
        "// Do not edit by hand; every raw word and byte comes from the reviewed JS oracle.",
        "#pragma once",
        "",
        "namespace glitch_native_oracle {",
        "",
        f'inline constexpr std::string_view kOracleSha256 = "{ORACLE_SHA256}";',
        f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";',
        f'inline constexpr std::string_view kCorpusRevision = "{CORPUS_REVISION}";',
        "inline constexpr std::size_t kTotalFloatWords = 2468U;",
        "inline constexpr std::size_t kTotalRgbaBytes = 2468U;",
        "",
    ]
    cases = oracle["render_cases"]
    for index, case in enumerate(cases):
        words = case["output_f32_bits_le"]
        rgba = case["output_rgba8"]
        lines.append(
            f"inline constexpr std::array<std::uint32_t, {len(words)}> kCase{index}FloatWords{{{{")
        lines.extend(_array_lines(words, "U"))
        lines.extend(["}};", ""])
        lines.append(
            f"inline constexpr std::array<std::uint8_t, {len(rgba)}> kCase{index}RgbaBytes{{{{")
        lines.extend(_array_lines(rgba, "U", width=16))
        lines.extend(["}};", ""])
    lines.extend([
        "struct CaseView {",
        "  std::string_view name;",
        "  std::size_t width;",
        "  std::size_t height;",
        "  std::uint32_t phase;",
        "  double time;",
        "  std::int32_t seed;",
        "  bool aspect_lens;",
        "  double x_chonk;",
        "  double y_chonk;",
        "  double glitchiness;",
        "  double scanlines_amount;",
        "  double snow_amount;",
        "  double vignette_amount;",
        "  double aberration;",
        "  double distortion;",
        "  std::array<double, 2> tile_offset;",
        "  std::array<double, 2> full_resolution;",
        "  std::span<const std::uint32_t> float_words;",
        "  std::span<const std::uint8_t> rgba_bytes;",
        "  std::string_view float_sha256;",
        "  std::string_view rgba_sha256;",
        "};",
        "",
        "inline constexpr std::array<CaseView, 8> kCases{{",
    ])
    for index, case in enumerate(cases):
        tile = case["effective_tile_offset"]
        full = case["effective_full_resolution"]
        lines.append(
            "  CaseView{" +
            f'"{case["name"]}", {case["width"]}U, {case["height"]}U, '
            f'{case["phase"]}U, {_cpp_number(case["time"])}, '
            f'std::int32_t{{{case["seed"]}}}, '
            f'{str(case["aspectLens"]).lower()}, '
            f'{_cpp_number(case["xChonk"])}, {_cpp_number(case["yChonk"])}, '
            f'{_cpp_number(case["glitchiness"])}, '
            f'{_cpp_number(case["scanlinesAmt"])}, '
            f'{_cpp_number(case["snowAmt"])}, '
            f'{_cpp_number(case["vignetteAmt"])}, '
            f'{_cpp_number(case["aberration"])}, '
            f'{_cpp_number(case["distortion"])}, '
            f'{{{_cpp_number(tile[0])}, {_cpp_number(tile[1])}}}, '
            f'{{{_cpp_number(full[0])}, {_cpp_number(full[1])}}}, '
            f'kCase{index}FloatWords, kCase{index}RgbaBytes, '
            f'"{case["output_f32_sha256"]}", '
            f'"{case["output_rgba8_sha256"]}"' + "},")
    lines.extend(["}};", "", "}  // namespace glitch_native_oracle", ""])
    return "\n".join(lines).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        expected = render()
        if arguments.write:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(expected)
        elif not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            raise OracleError("generated Glitch native oracle include is stale")
    except (OSError, OracleError) as error:
        print(f"glslcpp: {error}", file=sys.stderr)
        return 1
    print("Glitch native oracle include ok (8 cases, 2468 words, 2468 bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
