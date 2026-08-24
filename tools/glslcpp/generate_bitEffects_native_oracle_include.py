#!/usr/bin/env python3
"""Fail-closed BitEffects oracle materializer; intentionally independent of shared generators."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import struct
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/bit-effects-parity"
ORACLE = PACKAGE / "bitEffects-oracles.json"
REPORT = PACKAGE / "bitEffects-oracle-report.md"
GENERATOR = PACKAGE / "bitEffects_oracle_generator.mjs"
TARGET = ROOT / "tests/oracles/bitEffects_expected.inc"
SCHEMA = "noisemaker-for-cpp.bitEffects.pixel-parity.v1"
PROGRAM = "classicNoisedeck/bitEffects:bitEffects"
SHA = re.compile(r"^[0-9a-f]{64}$")
HEX = re.compile(r"^0x[0-9a-f]{8}$")
CASE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class MaterializationError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sidecar(path: pathlib.Path) -> pathlib.Path:
    return path.with_name(path.name + ".sha256")


def verify_sidecar(path: pathlib.Path) -> None:
    if not path.is_file() or not sidecar(path).is_file():
        raise MaterializationError(f"missing artifact or sidecar: {path}")
    fields = sidecar(path).read_text(encoding="utf-8").split()
    if len(fields) != 2 or fields[1] != path.name or not SHA.fullmatch(fields[0]) or fields[0] != digest(path.read_bytes()):
        raise MaterializationError(f"sidecar drift: {path}")


def word(value: Any, label: str) -> int:
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise MaterializationError(f"{label}: malformed Float32 word")
    return int(value[2:], 16)


def words(values: Any, count: int, label: str) -> list[int]:
    if not isinstance(values, list) or len(values) != count:
        raise MaterializationError(f"{label}: exact word cardinality required")
    return [word(item, f"{label}[{i}]") for i, item in enumerate(values)]


def rgba(values: Any, count: int, label: str) -> list[int]:
    if not isinstance(values, list) or len(values) != count or any(type(x) is not int or not 0 <= x <= 255 for x in values):
        raise MaterializationError(f"{label}: exact RGBA8 cardinality/range required")
    return values


def float_word(value: Any, label: str) -> int:
    if type(value) in (int, float):
        return struct.unpack("<I", struct.pack("<f", float(value)))[0]
    special = {
        "-0": 0x80000000,
        "NaN": 0x7FC00000,
        "Infinity": 0x7F800000,
        "-Infinity": 0xFF800000,
    }
    if isinstance(value, str) and value in special:
        return special[value]
    raise MaterializationError(f"{label}: malformed Float32 binding")


def load(document: dict[str, Any] | None = None) -> dict[str, Any]:
    if document is None:
        if not ORACLE.is_file():
            raise MaterializationError("oracle JSON is missing")
        document = json.loads(ORACLE.read_text(encoding="utf-8"))
    if document.get("schema") != SCHEMA or document.get("program_key") != PROGRAM:
        raise MaterializationError("schema/program identity drift")
    source = document.get("source")
    factory = document.get("factory")
    if not isinstance(source, dict) or not SHA.fullmatch(source.get("raw_sha256", "")) or not SHA.fullmatch(source.get("normalized_sha256", "")):
        raise MaterializationError("authenticated source hashes required")
    if not isinstance(factory, dict) or factory.get("name") != "canonicalFactory0" or not SHA.fullmatch(factory.get("text_sha256", "")) or not SHA.fullmatch(factory.get("source_slice_sha256", "")):
        raise MaterializationError("authenticated factory hashes required")
    census = document.get("feature_census")
    expected = {"scalar_int_bitwise_nodes": 13, "float_bits_to_uint_sites": 2, "uvec3_bitwise_sites": 2, "scalar_uint_xor_sites": 3, "global_mask_initializer": True}
    if not isinstance(census, dict) or any(census.get(k) != v for k, v in expected.items()):
        raise MaterializationError("feature census drift")
    if document.get("strict_comparer_self_tests", {}).get("status") != "passed":
        raise MaterializationError("strict comparer self-test missing")
    cases = document.get("render_cases")
    if not isinstance(cases, list) or len(cases) < 20:
        raise MaterializationError("render case cardinality drift")
    frozen_defines = {
        "COLOR_SCHEME": 20,
        "FORMULA": 0,
        "INTERP": 0,
        "MASK_COLOR_SCHEME": 1,
        "MASK_FORMULA": 10,
        "MODE": 1,
    }
    if document.get("native_typed_defines") != frozen_defines:
        raise MaterializationError("native typed define tuple drift")
    native_count = 0
    for index, case in enumerate(cases):
        if (not isinstance(case, dict)
                or not isinstance(case.get("name"), str)
                or not CASE_NAME.fullmatch(case["name"])):
            raise MaterializationError(f"case {index}: malformed identity")
        width, height = case.get("width"), case.get("height")
        if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
            raise MaterializationError(f"case {index}: dimensions required")
        out = case.get("output_expected")
        pub = case.get("public_output_expected")
        count = width * height * 4
        if not isinstance(out, dict) or not isinstance(pub, dict):
            raise MaterializationError(f"case {index}: direct/public outputs required")
        words(out.get("f32_words_le"), count, f"case {index} direct words")
        rgba(out.get("rgba8_bytes"), count, f"case {index} direct bytes")
        words(pub.get("f32_words_le"), count, f"case {index} public words")
        rgba(pub.get("rgba8_bytes"), count, f"case {index} public bytes")
        if case.get("canonical_repeat", {}).get("exact") is not True or case.get("distinct_output_storage") is not True:
            raise MaterializationError(f"case {index}: identity/lifetime ledger drift")
        bindings = case.get("bindings")
        uniforms = bindings.get("uniforms") if isinstance(bindings, dict) else None
        numeric_uniforms = (
            "n", "scale", "rotation", "speed", "tiles", "complexity",
            "hueRange", "hueRotation", "baseHueRange")
        if (not isinstance(uniforms, dict)
                or any(type(bindings.get(name)) is not int
                       or type(uniforms.get(name)) is not int
                       for name in frozen_defines)
                or any(bindings.get(name) != uniforms.get(name)
                       for name in frozen_defines)
                or not isinstance(bindings.get("tileOffset"), list)
                or len(bindings["tileOffset"]) != 2
                or not isinstance(bindings.get("fullResolution"), list)
                or len(bindings["fullResolution"]) != 2):
            raise MaterializationError(f"case {index}: binding record drift")
        float_word(bindings.get("time"), f"case {index} time")
        float_word(bindings.get("seed"), f"case {index} seed")
        for lane, value in enumerate(bindings["tileOffset"]):
            float_word(value, f"case {index} tileOffset[{lane}]")
        for lane, value in enumerate(bindings["fullResolution"]):
            float_word(value, f"case {index} fullResolution[{lane}]")
        for name in numeric_uniforms:
            float_word(uniforms.get(name), f"case {index} {name}")
        if case.get("native_direct_compatible") is True:
            if not isinstance(bindings, dict) or any(
                    bindings.get(name) != value
                    for name, value in frozen_defines.items()):
                raise MaterializationError(
                    f"case {index}: native direct define tuple drift")
            native_count += 1
    if native_count < 4:
        raise MaterializationError("native direct case cardinality drift")
    mutations = document.get("source_mutation_ledger")
    if not isinstance(mutations, list) or len(mutations) < 3 or any(not row.get("witness_case") for row in mutations):
        raise MaterializationError("mutation ledger exactness drift")
    return document


def render(document: dict[str, Any]) -> str:
    chunks: list[str] = [
        "// Authenticated BitEffects oracle; generated by generate_bitEffects_native_oracle_include.py.\n",
        "#pragma once\n",
        "namespace bitEffects_oracle {\n",
        "struct Case { std::string_view name; bool native_direct_compatible; std::size_t width; std::size_t height; std::int32_t mode; std::int32_t formula; std::int32_t color_scheme; std::int32_t interp; std::int32_t mask_formula; std::int32_t mask_color_scheme; std::uint32_t time_word; std::uint32_t seed_word; std::array<std::uint32_t, 2> tile_offset_words; std::array<std::uint32_t, 2> full_resolution_words; std::array<std::uint32_t, 9> numeric_uniform_words; std::span<const std::uint32_t> direct_words; std::span<const std::uint8_t> direct_rgba8; std::span<const std::uint32_t> public_words; std::span<const std::uint8_t> public_rgba8; };\n"]
    rows = []
    native_indices = []
    for index, case in enumerate(document["render_cases"]):
        direct = case["output_expected"]
        public = case["public_output_expected"]
        dw = [word(x, "direct") for x in direct["f32_words_le"]]
        pw = [word(x, "public") for x in public["f32_words_le"]]
        db, pb = direct["rgba8_bytes"], public["rgba8_bytes"]
        chunks.extend([f"inline constexpr std::array<std::uint32_t, {len(dw)}> kDirectWords{index} = {{", ", ".join(f"0x{x:08x}u" for x in dw), "};\n", f"inline constexpr std::array<std::uint8_t, {len(db)}> kDirectRgba8{index} = {{", ", ".join(str(x) for x in db), "};\n", f"inline constexpr std::array<std::uint32_t, {len(pw)}> kPublicWords{index} = {{", ", ".join(f"0x{x:08x}u" for x in pw), "};\n", f"inline constexpr std::array<std::uint8_t, {len(pb)}> kPublicRgba8{index} = {{", ", ".join(str(x) for x in pb), "};\n"])
        compatible = case.get("native_direct_compatible") is True
        if compatible:
            native_indices.append(index)
        bindings = case["bindings"]
        uniforms = bindings["uniforms"]
        numeric_names = (
            "n", "scale", "rotation", "speed", "tiles", "complexity",
            "hueRange", "hueRotation", "baseHueRange")
        numeric_words = ", ".join(
            f"0x{float_word(uniforms[name], name):08x}u"
            for name in numeric_names)
        tile_words = ", ".join(
            f"0x{float_word(value, 'tileOffset'):08x}u"
            for value in bindings["tileOffset"])
        full_words = ", ".join(
            f"0x{float_word(value, 'fullResolution'):08x}u"
            for value in bindings["fullResolution"])
        rows.append(
            f'  Case{{std::string_view({json.dumps(case["name"])}), '
            f'{str(compatible).lower()}, {case["width"]}, {case["height"]}, '
            f'{bindings["MODE"]}, {bindings["FORMULA"]}, '
            f'{bindings["COLOR_SCHEME"]}, {bindings["INTERP"]}, '
            f'{bindings["MASK_FORMULA"]}, {bindings["MASK_COLOR_SCHEME"]}, '
            f'0x{float_word(bindings["time"], "time"):08x}u, '
            f'0x{float_word(bindings["seed"], "seed"):08x}u, '
            f'{{{tile_words}}}, {{{full_words}}}, {{{numeric_words}}}, '
            f'kDirectWords{index}, kDirectRgba8{index}, '
            f'kPublicWords{index}, kPublicRgba8{index}}}')
    chunks.extend([
        f"inline constexpr std::array<Case, {len(rows)}> kCases = {{\n",
        ",\n".join(rows), "\n};\n",
        f"inline constexpr std::array<std::size_t, {len(native_indices)}> kNativeDirectCases = {{",
        ", ".join(str(index) for index in native_indices), "};\n",
        'inline constexpr std::int32_t kMode = 1;\n',
        'inline constexpr std::int32_t kFormula = 0;\n',
        'inline constexpr std::int32_t kColorScheme = 20;\n',
        'inline constexpr std::int32_t kInterp = 0;\n',
        'inline constexpr std::int32_t kMaskFormula = 10;\n',
        'inline constexpr std::int32_t kMaskColorScheme = 1;\n',
        f'inline constexpr std::string_view kProgramKey = {json.dumps(PROGRAM)};\n',
        "}\n"])
    return "".join(chunks)


def self_test() -> None:
    document = load()
    bad = copy.deepcopy(document)
    bad["feature_census"]["scalar_int_bitwise_nodes"] = 12
    try:
        load(bad)
    except MaterializationError:
        print("feature census sabotage rejected")
    bad = copy.deepcopy(document)
    bad["source_mutation_ledger"][0]["witness_case"] = ""
    try:
        load(bad)
    except MaterializationError:
        print("mutation ledger exactness rejected")
    bad = copy.deepcopy(document)
    bad["render_cases"][0]["name"] = 'bad\"); static_assert(false); //'
    try:
        load(bad)
    except MaterializationError:
        print("unsafe case name rejected")
    bad = copy.deepcopy(document)
    bad["render_cases"][0]["bindings"]["MODE"] = True
    try:
        load(bad)
    except MaterializationError:
        print("non-integer define rejected")
    print("strict identity/lifetime and mutation ledger self-tests passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    if sum((options.write, options.check, options.self_test)) != 1:
        parser.error("choose exactly one of --write, --check, --self-test")
    if options.self_test:
        self_test()
        return
    document = load()
    if options.write:
        payload = render(document).encode("utf-8")
        TARGET.write_bytes(payload)
        sidecar(TARGET).write_text(f"{digest(payload)}  {TARGET.name}\n", encoding="utf-8")
        print(f"wrote {TARGET}")
        return
    for path in (ORACLE, REPORT, GENERATOR, pathlib.Path(__file__).resolve(), TARGET):
        verify_sidecar(path)
    if render(document) != TARGET.read_text(encoding="utf-8"):
        raise MaterializationError("native include drift")
    print("BitEffects native include checked")


if __name__ == "__main__":
    main()
