#!/usr/bin/env python3
"""Materialize the authenticated filter/osd oracle as a C++20 include.

The JSON oracle is the authority.  This file deliberately validates its
semantic locks before emitting anything, and writes a matching hash sidecar
for the generated include.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/osd-parity"
ORACLE = PACKAGE / "osd-oracles.json"
INCLUDE = ROOT / "tests/oracles/osd_expected.inc"
SCHEMA = "noisemaker-for-cpp.osd.pixel-parity.v1"
PROGRAM = "filter/osd:osd"
FACTORY = "canonicalFactory94"
SOURCE_SHA = "c45adaf30ecef6fb7f83a4f3995e671df0caaa47bfeceba8bb9bfe2c07427443"
FACTORY_SHA = "9920f7a4d629d468a2d9ac8cbe319d28d385bd9561c06bb0772e5ce6204f528b"


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sidecar(path: Path, payload: bytes) -> str:
    return f"{digest(payload)}  {path.name}\n"


def load_json(path: Path) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    payload = path.read_bytes()
    document = json.loads(payload.decode("utf-8"), object_pairs_hook=pairs)
    if not isinstance(document, dict):
        raise ValueError("oracle root must be an object")
    return document


def reject_paths(value, label="oracle"):
    if isinstance(value, str):
        if value.startswith("/") or any(token in value for token in ("/private/", "/Users/", "/tmp/", "\\private\\", "\\Users\\")):
            raise ValueError(f"{label}: absolute path serialized")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_paths(item, f"{label}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            reject_paths(item, f"{label}.{key}")


def verify_sidecar(path: Path) -> bytes:
    payload = path.read_bytes()
    expected = sidecar(path, payload)
    if path.with_name(path.name + ".sha256").read_text() != expected:
        raise ValueError(f"sidecar drift: {path}")
    return payload


def hex_words(values, label):
    if not isinstance(values, list) or not values:
        raise ValueError(f"{label}: expected non-empty word list")
    words = []
    for index, value in enumerate(values):
        if not isinstance(value, str) or len(value) != 10 or not value.startswith("0x"):
            raise ValueError(f"{label}[{index}]: non-canonical u32 word")
        try:
            parsed = int(value, 16)
        except ValueError as error:
            raise ValueError(f"{label}[{index}]: invalid u32 word") from error
        if parsed > 0xFFFFFFFF:
            raise ValueError(f"{label}[{index}]: u32 overflow")
        words.append(parsed)
    return words


def bytes_values(values, label):
    if not isinstance(values, list):
        raise ValueError(f"{label}: expected byte list")
    if any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 255 for value in values):
        raise ValueError(f"{label}: invalid byte")
    return values


def validate(document):
    reject_paths(document)
    if document.get("schema") != SCHEMA or document.get("program_key") != PROGRAM:
        raise ValueError("OSD oracle schema/program lock mismatch")
    provenance = document.get("provenance", {})
    factory = document.get("factory", {})
    if provenance.get("source_sha256") != SOURCE_SHA or factory.get("text_sha256") != FACTORY_SHA:
        raise ValueError("OSD source/factory lock mismatch")
    if factory.get("name") != FACTORY or not factory.get("public_direct_identity") or factory.get("adapter_override"):
        raise ValueError("OSD factory identity lock mismatch")
    cases = document.get("render_cases")
    mutations = document.get("behavioral_mutation_ledger")
    if not isinstance(cases, list) or len(cases) != 7 or not isinstance(mutations, list) or len(mutations) != 6:
        raise ValueError("OSD case/mutation cardinality mismatch")
    seen = set()
    for case in cases:
        name = case.get("name")
        if not isinstance(name, str) or name in seen:
            raise ValueError("duplicate or invalid OSD case name")
        seen.add(name)
        width, height = case.get("width"), case.get("height")
        if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
            raise ValueError(f"{name}: invalid dimensions")
        expected = width * height * 4
        words = hex_words(case.get("output_f32_words_le"), f"{name}.output_f32_words_le")
        rgba = bytes_values(case.get("output_rgba8_bytes"), f"{name}.output_rgba8_bytes")
        if len(words) != expected or len(rgba) != expected:
            raise ValueError(f"{name}: output cardinality mismatch")
        packed = b"".join(struct.pack("<I", word) for word in words)
        if digest(packed) != case.get("output_f32_sha256") or digest(bytes(rgba)) != case.get("output_rgba8_sha256"):
            raise ValueError(f"{name}: output hash mismatch")
        if case.get("input_immutable_exact_bits") is not True or case.get("input_lifetime_stable") is not True or case.get("public_direct_repeat_exact") is not True:
            raise ValueError(f"{name}: missing identity/input guarantees")
    for mutation in mutations:
        if not mutation.get("name") or not mutation.get("anchor_text") or not mutation.get("replacement_text"):
            raise ValueError("incomplete mutation lock")
        if digest(mutation["anchor_text"].encode()) != mutation.get("anchor_sha256") or digest(mutation["replacement_text"].encode()) != mutation.get("replacement_sha256"):
            raise ValueError(f"{mutation['name']}: mutation text hash mismatch")
        witnesses = mutation.get("required_witness_results")
        if not isinstance(witnesses, list) or not witnesses:
            raise ValueError(f"{mutation['name']}: missing witness")
        if any(item.get("mismatched_lanes", 0) <= 0 or item.get("mismatched_bytes", 0) <= 0 for item in witnesses):
            raise ValueError(f"{mutation['name']}: inert witness")
    comparer = document.get("comparer_self_tests")
    if not isinstance(comparer, dict) or set(comparer) != {"good_equal", "dimensions_mismatch", "short_lane_count", "long_lane_count", "rgba8_mismatch", "signed_zero_rejected", "nan_payload_rejected"} or not all(comparer.values()):
        raise ValueError("strict comparer self-test lock mismatch")
    return cases, mutations


def cpp_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def emit(document, cases, mutations) -> str:
    out = ["// Authenticated filter/osd oracle; generated by generate_osd_native_oracle_include.py.", "#include <array>", "#include <cstddef>", "#include <cstdint>", "#include <span>", "#include <string_view>", "", "namespace noisemaker_osd_oracle {", "", "struct CaseRecord { std::string_view name; std::size_t width; std::size_t height; std::span<const std::uint32_t> output_f32_words; std::span<const std::uint8_t> output_rgba8_bytes; bool input_immutable_exact_bits; bool input_lifetime_stable; };", "struct MutationResult { std::string_view case_name; std::size_t mismatched_lanes; std::size_t mismatched_bytes; };", "struct MutationRecord { std::string_view name; std::string_view anchor_text; std::string_view replacement_text; std::span<const MutationResult> required_results; };", "struct ComparerSelfTests { bool good_equal; bool dimensions_mismatch; bool short_lane_count; bool long_lane_count; bool rgba8_mismatch; bool signed_zero_rejected; bool nan_payload_rejected; };", ""]
    for index, case in enumerate(cases):
        words = ", ".join(f"0x{int(word, 16):08x}u" for word in case["output_f32_words_le"])
        rgba = ", ".join(f"{value}u" for value in case["output_rgba8_bytes"])
        out.append(f"inline constexpr std::array<std::uint32_t, {len(case['output_f32_words_le'])}> output_f32_words_{index}{{{{{words}}}}};")
        out.append(f"inline constexpr std::array<std::uint8_t, {len(case['output_rgba8_bytes'])}> output_rgba8_bytes_{index}{{{{{rgba}}}}};")
    out.append("")
    for index, mutation in enumerate(mutations):
        results = ", ".join(f"{{{cpp_string(item['case'])}, {item['mismatched_lanes']}u, {item['mismatched_bytes']}u}}" for item in mutation["required_witness_results"])
        out.append(f"inline constexpr std::array<MutationResult, {len(mutation['required_witness_results'])}> mutation_results_{index}{{{{{results}}}}};")
    out.append("")
    case_records = ",\n  ".join(f"{{{cpp_string(case['name'])}, {case['width']}u, {case['height']}u, output_f32_words_{i}, output_rgba8_bytes_{i}, true, true}}" for i, case in enumerate(cases))
    out.append(f"inline constexpr std::array<CaseRecord, {len(cases)}> kCases{{{{\n  {case_records}\n}}}};")
    mutation_records = ",\n  ".join(f"{{{cpp_string(mutation['name'])}, {cpp_string(mutation['anchor_text'])}, {cpp_string(mutation['replacement_text'])}, mutation_results_{i}}}" for i, mutation in enumerate(mutations))
    out.append(f"inline constexpr std::array<MutationRecord, {len(mutations)}> kMutations{{{{\n  {mutation_records}\n}}}};")
    out.append("inline constexpr auto kMutationWitnesses = kMutations;")
    comparer = document["comparer_self_tests"]
    out.append("inline constexpr ComparerSelfTests kComparerSelfTests{" + ", ".join("true" if comparer[key] else "false" for key in ("good_equal", "dimensions_mismatch", "short_lane_count", "long_lane_count", "rgba8_mismatch", "signed_zero_rejected", "nan_payload_rejected")) + "};")
    out.extend(["", "} // namespace noisemaker_osd_oracle", ""])
    return "\n".join(out)


def main(argv):
    if len(argv) != 1 or argv[0] not in {"--write", "--check", "--self-test"}:
        raise SystemExit("usage: generate_osd_native_oracle_include.py --write|--check|--self-test")
    mode = argv[0]
    verify_sidecar(ORACLE)
    document = load_json(ORACLE)
    cases, mutations = validate(document)
    generated = emit(document, cases, mutations).encode()
    if mode == "--write":
        INCLUDE.parent.mkdir(parents=True, exist_ok=True)
        INCLUDE.write_bytes(generated)
        INCLUDE.with_name(INCLUDE.name + ".sha256").write_text(sidecar(INCLUDE, generated))
        script = Path(__file__).resolve()
        script.with_name(script.name + ".sha256").write_text(sidecar(script, script.read_bytes()))
        print("OSD native oracle include written")
    else:
        if verify_sidecar(INCLUDE) != generated:
            raise ValueError("OSD native oracle include drift")
        if mode == "--check":
            print("OSD native oracle include checked")
        else:
            with tempfile.TemporaryDirectory(prefix="osd-materializer-") as raw:
                forged = Path(raw) / ORACLE.name
                forged.write_text(json.dumps({**document, "schema": "forged"}))
                forged.with_name(forged.name + ".sha256").write_text(sidecar(forged, forged.read_bytes()))
                try:
                    validate(load_json(forged))
                except ValueError:
                    pass
                else:
                    raise ValueError("matching-sidecar semantic forgery accepted")
            print("matching-sidecar forgery probes rejected")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
