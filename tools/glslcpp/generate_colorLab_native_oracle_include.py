#!/usr/bin/env python3
"""Fail-closed materializer for the frozen ColorLab pixel oracle."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/color-lab-parity"
ORACLE = PACKAGE / "colorLab-oracles.json"
REPORT = PACKAGE / "colorLab-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/colorLab_expected.inc"
KEY = "classicNoisedeck/colorLab:colorLab"
SCHEMA = "noisemaker-for-cpp.colorLab.pixel-parity.v1"


class MaterializationError(ValueError):
    pass


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sidecar(path: Path, payload: bytes) -> str:
    return f"{_sha(payload)}  {path.name}\n"


def _read_checked(path: Path) -> bytes:
    if not path.is_file() or not path.with_name(path.name + ".sha256").is_file():
        raise MaterializationError(f"missing artifact or sidecar: {path}")
    payload = path.read_bytes()
    if path.with_name(path.name + ".sha256").read_text() != _sidecar(path, payload):
        raise MaterializationError(f"sidecar drift: {path}")
    return payload


def _exact(value, expected, label: str):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise MaterializationError(f"{label}: schema drift")


def _hex_word(value, label: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-f]{8}", value):
        raise MaterializationError(f"{label}: malformed Float32 word")
    return int(value, 16)


def _words(value, expected: int, label: str) -> list[int]:
    if not isinstance(value, list) or len(value) != expected:
        raise MaterializationError(f"{label}: exact Float32 cardinality required")
    return [_hex_word(item, f"{label}[{index}]") for index, item in enumerate(value)]


def _bytes(value, expected: int, label: str) -> list[int]:
    if not isinstance(value, list) or len(value) != expected or any(
            isinstance(item, bool) or not isinstance(item, int) or not 0 <= item <= 255
            for item in value):
        raise MaterializationError(f"{label}: exact RGBA8 cardinality/range required")
    return list(value)


def _check_digest(value: str, label: str):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise MaterializationError(f"{label}: malformed SHA-256")


def _check_surface(surface, size: int, label: str):
    _exact(surface, {"f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"}, label)
    words = _words(surface["f32_words_le"], size, f"{label}.f32_words_le")
    rgba = _bytes(surface["rgba8_bytes"], size, f"{label}.rgba8_bytes")
    _check_digest(surface["f32_sha256"], f"{label}.f32_sha256")
    _check_digest(surface["rgba8_sha256"], f"{label}.rgba8_sha256")
    if surface["f32_sha256"] != _sha(b"".join(word.to_bytes(4, "little") for word in words)):
        raise MaterializationError(f"{label}: Float32 digest mismatch")
    if surface["rgba8_sha256"] != _sha(bytes(rgba)):
        raise MaterializationError(f"{label}: RGBA8 digest mismatch")


def validate(document: dict) -> dict:
    if not isinstance(document, dict):
        raise MaterializationError("oracle root must be an object")
    _exact(document, {"schema", "program_key", "provenance", "factory", "runtime_binding_names",
                      "runtime_binding_abi", "source_uniform_abi", "render_cases",
                      "comparer_self_tests", "mutation_ledger", "claim_boundaries"}, "oracle")
    if document["schema"] != SCHEMA or document["program_key"] != KEY:
        raise MaterializationError("schema/program identity drift")
    provenance = document["provenance"]
    _exact(provenance, {"authority_node", "upstream_revision", "source", "factory", "cpu_snapshot"}, "provenance")
    source = provenance["source"]
    _exact(source, {"relative_path", "bytes", "sha256"}, "provenance.source")
    if not isinstance(source["relative_path"], str) or source["relative_path"].startswith(("/", "\\")) or ".." in Path(source["relative_path"]).parts:
        raise MaterializationError("absolute or escaping source path")
    _check_digest(source["sha256"], "provenance.source.sha256")
    snapshot = provenance["cpu_snapshot"]
    _exact(snapshot, {"import_closure", "closure_cardinality", "immutable_snapshot", "live_checkout_rejected", "realpath_containment_checked", "symlink_escape_rejected"}, "provenance.cpu_snapshot")
    if snapshot["closure_cardinality"] != len(snapshot["import_closure"]) or not all(snapshot[key] is True for key in ("immutable_snapshot", "live_checkout_rejected", "realpath_containment_checked", "symlink_escape_rejected")):
        raise MaterializationError("frozen import-closure provenance drift")
    for index, entry in enumerate(snapshot["import_closure"]):
        _exact(entry, {"relative_path", "sha256"}, f"import_closure[{index}]")
        if not isinstance(entry["relative_path"], str) or entry["relative_path"].startswith(("/", "\\")) or ".." in Path(entry["relative_path"]).parts:
            raise MaterializationError("import closure path escapes authority")
        _check_digest(entry["sha256"], f"import_closure[{index}].sha256")
    factory = document["factory"]
    _exact(factory, {"name", "text_bytes", "text_sha256", "adapter_own_key", "public_factory_is_direct_identity"}, "factory")
    _check_digest(factory["text_sha256"], "factory.text_sha256")
    if factory["adapter_own_key"] is not False or factory["public_factory_is_direct_identity"] is not True:
        raise MaterializationError("factory identity claim drift")
    names = document["runtime_binding_names"]
    if not isinstance(names, list) or names != list(document["runtime_binding_abi"]):
        raise MaterializationError("runtime binding ABI drift")
    if not isinstance(document["runtime_binding_abi"], dict) or set(names) != set(document["runtime_binding_abi"]):
        raise MaterializationError("runtime binding ABI schema drift")
    if not isinstance(document["source_uniform_abi"], dict) or set(names) != set(document["source_uniform_abi"]):
        raise MaterializationError("source uniform ABI schema drift")
    comparer = document["comparer_self_tests"]
    expected_comparer = {"good_equal", "dimensions_mismatch", "short_lane_count", "rgba8_mismatch", "signed_zero", "nan_payload"}
    if not isinstance(comparer, dict) or set(comparer) != expected_comparer or not all(value is True for value in comparer.values()):
        raise MaterializationError("strict comparer self-tests missing or false")
    cases = document["render_cases"]
    if not isinstance(cases, list) or len(cases) < 8:
        raise MaterializationError("ColorLab render case cardinality drift")
    for index, case in enumerate(cases):
        label = f"render_cases[{index}]"
        required = {"name", "width", "height", "controls", "tile", "binding_words", "input", "expected", "input_immutable_exact_bits", "input_lifetime_stable", "repeat_output_object_distinct", "repeat_output_data_distinct", "public_direct_exact"}
        _exact(case, required, label)
        if not isinstance(case["name"], str) or not isinstance(case["width"], int) or not isinstance(case["height"], int) or case["width"] <= 0 or case["height"] <= 0:
            raise MaterializationError(f"{label}: dimensions required")
        size = case["width"] * case["height"] * 4
        _check_surface(case["input"], size, f"{label}.input")
        _check_surface(case["expected"], size, f"{label}.expected")
        if not all(case[key] is True for key in ("input_immutable_exact_bits", "input_lifetime_stable", "repeat_output_object_distinct", "repeat_output_data_distinct", "public_direct_exact")):
            raise MaterializationError(f"{label}: lifetime/identity claim drift")
        if not isinstance(case["controls"], dict) or not isinstance(case["tile"], dict):
            raise MaterializationError(f"{label}: controls/tiles required")
        if set(case["binding_words"]) != {"inputTex", "tileOffset", "fullResolution"}:
            raise MaterializationError(f"{label}: binding-word schema drift")
        if case["binding_words"]["inputTex"] != case["input"]["f32_words_le"]:
            raise MaterializationError(f"{label}: input binding replay drift")
    ledger = document["mutation_ledger"]
    if not isinstance(ledger, list) or len(ledger) < 10:
        raise MaterializationError("mutation ledger cardinality drift")
    for index, mutation in enumerate(ledger):
        _exact(mutation, {"name", "source_anchor", "replacement", "anchor_sha256", "replacement_sha256", "mutated_factory_sha256", "required_witnesses", "required_witness_results", "independent"}, f"mutation_ledger[{index}]")
        for field in ("anchor_sha256", "replacement_sha256", "mutated_factory_sha256"):
            _check_digest(mutation[field], f"mutation_ledger[{index}].{field}")
        if mutation["independent"] is not True or not mutation["required_witnesses"]:
            raise MaterializationError(f"mutation_ledger[{index}]: witness contract drift")
        for result in mutation["required_witness_results"]:
            _exact(result, {"case", "mismatched_lanes", "mismatched_bytes", "first_mismatch", "first_rgba8_mismatch"}, f"mutation_ledger[{index}].result")
            if result["mismatched_lanes"] <= 0 or result["mismatched_bytes"] <= 0:
                raise MaterializationError(f"mutation_ledger[{index}]: non-diverging witness")
    return document


def _q(value: str) -> str:
    return json.dumps(value, separators=(",", ":"))


def render_include(document: dict) -> bytes:
    lines = ["// Generated by generate_colorLab_native_oracle_include.py; exact frozen JSON authority.", "#pragma once", "#include <array>", "#include <cstdint>", "#include <span>", "#include <string_view>", "namespace noisemaker_color_lab_oracle {"]
    lines.append("struct Case { std::string_view name; std::uint32_t width, height; std::span<const std::uint32_t> input_f32, expected_f32; std::span<const std::uint8_t> input_rgba8, expected_rgba8; std::string_view input_f32_sha256, expected_f32_sha256, expected_rgba8_sha256; bool input_immutable_exact_bits, input_lifetime_stable, repeat_output_object_distinct, repeat_output_data_distinct, public_direct_exact; };")
    lines.append("struct MutationResult { std::string_view case_name; std::uint32_t mismatched_lanes, mismatched_bytes; };")
    lines.append("struct Mutation { std::string_view name, source_anchor, replacement, mutated_factory_sha256; std::span<const MutationResult> results; };")
    lines.append(f"inline constexpr std::string_view kSchema = {_q(document['schema'])};")
    lines.append(f"inline constexpr std::string_view kProgramKey = {_q(document['program_key'])};")
    lines.append(f"inline constexpr std::string_view kFactorySha256 = {_q(document['factory']['text_sha256'])};")
    for index, case in enumerate(document["render_cases"]):
        inp = [_hex_word(word, "include") for word in case["input"]["f32_words_le"]]
        out = [_hex_word(word, "include") for word in case["expected"]["f32_words_le"]]
        rgba_in = case["input"]["rgba8_bytes"]; rgba_out = case["expected"]["rgba8_bytes"]
        lines.append(f"inline constexpr std::array<std::uint32_t, {len(inp)}> kInputF32{index} = {{{', '.join(f'0x{word:08x}u' for word in inp)}}};")
        lines.append(f"inline constexpr std::array<std::uint32_t, {len(out)}> kExpectedF32{index} = {{{', '.join(f'0x{word:08x}u' for word in out)}}};")
        lines.append(f"inline constexpr std::array<std::uint8_t, {len(rgba_in)}> kInputRgba8{index} = {{{', '.join(str(value) for value in rgba_in)}}};")
        lines.append(f"inline constexpr std::array<std::uint8_t, {len(rgba_out)}> kExpectedRgba8{index} = {{{', '.join(str(value) for value in rgba_out)}}};")
    lines.append("inline constexpr std::array<Case, %d> kCases = {{" % len(document["render_cases"]))
    for index, case in enumerate(document["render_cases"]):
        lines.append(f"  {{{_q(case['name'])}, {case['width']}u, {case['height']}u, kInputF32{index}, kExpectedF32{index}, kInputRgba8{index}, kExpectedRgba8{index}, {_q(case['input']['f32_sha256'])}, {_q(case['expected']['f32_sha256'])}, {_q(case['expected']['rgba8_sha256'])}, true, true, true, true, true}},")
    lines.append("}};")
    for index, mutation in enumerate(document["mutation_ledger"]):
        results = mutation["required_witness_results"]
        lines.append(f"inline constexpr std::array<MutationResult, {len(results)}> kMutationResults{index} = {{{{")
        for result in results:
            lines.append(f"  {{{_q(result['case'])}, {result['mismatched_lanes']}u, {result['mismatched_bytes']}u}},")
        lines.append("}};")
    lines.append("inline constexpr std::array<Mutation, %d> kMutations = {{" % len(document["mutation_ledger"]))
    for index, mutation in enumerate(document["mutation_ledger"]):
        lines.append(f"  {{{_q(mutation['name'])}, {_q(mutation['source_anchor'])}, {_q(mutation['replacement'])}, {_q(mutation['mutated_factory_sha256'])}, kMutationResults{index}}},")
    lines.append("}};\n}")
    return ("\n".join(lines) + "\n").encode()


def main() -> int:
    mode = next((item for item in sys.argv[1:] if item in {"--write", "--check", "--self-test"}), None)
    if mode is None or sys.argv.count(mode) != 1:
        raise MaterializationError("choose exactly one of --write, --check, or --self-test")
    document = validate(json.loads(_read_checked(ORACLE).decode()))
    expected = render_include(document)
    if mode == "--write":
        INCLUDE.parent.mkdir(parents=True, exist_ok=True)
        INCLUDE.write_bytes(expected)
        INCLUDE.with_name(INCLUDE.name + ".sha256").write_text(_sidecar(INCLUDE, expected))
        print(f"{len(document['render_cases'])} cases, {len(document['mutation_ledger'])} mutations materialized")
    else:
        actual = _read_checked(INCLUDE)
        if actual != expected:
            raise MaterializationError("native include drift")
        if mode == "--self-test":
            probes = []
            forged = copy.deepcopy(document); forged["schema"] = "foreign"; probes.append((forged, "schema mutation rejected"))
            forged = copy.deepcopy(document); forged["render_cases"][0]["expected"]["f32_words_le"][0] = "0x00000000"; probes.append((forged, "Float32 digest mutation rejected"))
            forged = copy.deepcopy(document); forged["render_cases"][0]["binding_words"]["inputTex"][0] = "0x00000000"; probes.append((forged, "input binding replay mutation rejected"))
            for candidate, message in probes:
                try: validate(candidate)
                except MaterializationError: print(message)
                else: raise MaterializationError(f"{message}: accepted")
            print("strict comparer self-tests verified")
            print("dimension validation precedes storage access")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MaterializationError as error:
        print(f"ColorLab materialization failed: {error}", file=sys.stderr)
        raise SystemExit(1)
