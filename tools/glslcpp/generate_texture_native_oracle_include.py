#!/usr/bin/env python3
"""Fail-closed materializer for the frozen Texture pixel oracle."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/texture-parity"
ORACLE = PACKAGE / "texture-oracles.json"
INCLUDE = ROOT / "tests/oracles/texture_expected.inc"
SCHEMA = "noisemaker-for-cpp.texture.pixel-parity.v1"
KEY = "filter/texture:texture"


class MaterializationError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked(path: Path) -> bytes:
    side = path.with_name(path.name + ".sha256")
    if not path.is_file() or not side.is_file():
        raise MaterializationError(f"missing artifact or sidecar: {path}")
    data = path.read_bytes()
    if side.read_text() != f"{digest(data)}  {path.name}\n":
        raise MaterializationError(f"sidecar drift: {path}")
    return data


def words(value, size: int, label: str) -> list[int]:
    if not isinstance(value, list) or len(value) != size:
        raise MaterializationError(f"{label}: exact Float32 cardinality required")
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or re.fullmatch(r"0x[0-9a-f]{8}", item) is None:
            raise MaterializationError(f"{label}[{index}]: malformed Float32 word")
        result.append(int(item, 16))
    return result


def bytes8(value, size: int, label: str) -> list[int]:
    if (not isinstance(value, list) or len(value) != size or
            any(type(item) is not int or not 0 <= item <= 255 for item in value)):
        raise MaterializationError(f"{label}: exact RGBA8 cardinality/range required")
    return list(value)


def surface(value, size: int, label: str) -> None:
    if not isinstance(value, dict) or set(value) != {"f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"}:
        raise MaterializationError(f"{label}: surface schema drift")
    ws = words(value["f32_words_le"], size, f"{label}.f32_words_le")
    rb = bytes8(value["rgba8_bytes"], size, f"{label}.rgba8_bytes")
    if value["f32_sha256"] != digest(b"".join(x.to_bytes(4, "little") for x in ws)):
        raise MaterializationError(f"{label}: Float32 digest drift")
    if value["rgba8_sha256"] != digest(bytes(rb)):
        raise MaterializationError(f"{label}: RGBA8 digest drift")


def validate(document: dict) -> dict:
    required = {"schema", "program_key", "provenance", "runtime_binding_abi", "render_cases", "comparer_self_tests", "mutation_ledger", "claim_boundaries"}
    if not isinstance(document, dict) or set(document) != required:
        raise MaterializationError("oracle schema drift")
    if document["schema"] != SCHEMA or document["program_key"] != KEY:
        raise MaterializationError("schema/program identity drift")
    provenance = document["provenance"]
    if not isinstance(provenance, dict) or set(provenance) != {"authority_node", "upstream_revision", "source", "factory", "cpu_snapshot"}:
        raise MaterializationError("provenance schema drift")
    source = provenance["source"]
    if not isinstance(source, dict) or set(source) != {"relative_path", "bytes", "sha256"} or source["relative_path"].startswith("/") or ".." in Path(source["relative_path"]).parts:
        raise MaterializationError("source provenance drift")
    factory = provenance["factory"]
    if not isinstance(factory, dict) or factory.get("public_factory_is_canonical_identity") is not True or not re.fullmatch(r"[0-9a-f]{64}", factory.get("text_sha256", "")):
        raise MaterializationError("factory identity drift")
    snapshot = provenance["cpu_snapshot"]
    if not isinstance(snapshot, dict) or snapshot.get("closure_cardinality") != len(snapshot.get("import_closure", [])) or not all(snapshot.get(k) is True for k in ("immutable_snapshot", "live_checkout_rejected", "realpath_containment_checked", "symlink_escape_rejected")):
        raise MaterializationError("immutable closure provenance drift")
    for entry in snapshot["import_closure"]:
        if not isinstance(entry, dict) or set(entry) != {"relative_path", "sha256"} or entry["relative_path"].startswith("/") or ".." in Path(entry["relative_path"]).parts or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise MaterializationError("import closure entry drift")
    abi = document["runtime_binding_abi"]
    if set(abi) != {"inputTex", "time", "alpha", "scale", "intensity", "contrast", "mono", "tileOffset", "fullResolution", "MODE"} or abi["MODE"] != "int32":
        raise MaterializationError("runtime binding ABI drift")
    comparer = document["comparer_self_tests"]
    if set(comparer) != {"good_equal", "dimensions_mismatch", "short_lane_count", "rgba8_mismatch", "signed_zero", "nan_payload"} or not all(comparer.values()):
        raise MaterializationError("strict comparer self-tests missing")
    cases = document["render_cases"]
    if not isinstance(cases, list) or len(cases) < 8:
        raise MaterializationError("Texture case cardinality drift")
    for index, case in enumerate(cases):
        if not isinstance(case, dict) or not isinstance(case.get("width"), int) or not isinstance(case.get("height"), int) or case["width"] <= 0 or case["height"] <= 0:
            raise MaterializationError(f"case {index}: dimensions drift")
        size = case["width"] * case["height"] * 4
        for label in ("input", "expected", "public_expected"):
            surface(case.get(label), size, f"case {index}.{label}")
        if not all(case.get(k) is True for k in ("input_immutable_exact_bits", "public_direct_exact")):
            raise MaterializationError(f"case {index}: identity/lifetime drift")
        repeat = case.get("repeat", {})
        if not all(repeat.get(k) is True for k in ("exact", "output_object_distinct", "output_data_distinct")):
            raise MaterializationError(f"case {index}: repeat contract drift")
    ledger = document["mutation_ledger"]
    if not isinstance(ledger, list) or len(ledger) < 4:
        raise MaterializationError("mutation ledger cardinality drift")
    for index, mutation in enumerate(ledger):
        if not mutation.get("independent") or not mutation.get("required_witnesses"):
            raise MaterializationError(f"mutation {index}: witness contract drift")
        for result in mutation.get("required_witness_results", []):
            if result.get("mismatched_lanes", 0) <= 0 or result.get("mismatched_bytes", 0) <= 0:
                raise MaterializationError(f"mutation {index}: non-diverging witness")
    return document


def render(document: dict) -> bytes:
    lines = ["// Authenticated Texture oracle; generated by generate_texture_native_oracle_include.py.", "#pragma once", "#include <array>", "#include <cstdint>", "#include <span>", "#include <string_view>", "namespace noisemaker_texture_oracle {", "struct Case { std::string_view name; std::uint32_t width, height; std::span<const std::uint32_t> input_f32, expected_f32, public_f32; std::span<const std::uint8_t> input_rgba8, expected_rgba8, public_rgba8; };", "struct MutationResult { std::string_view case_name; std::uint32_t mismatched_lanes, mismatched_bytes; };", "struct Mutation { std::string_view name, source_anchor, replacement; std::span<const MutationResult> results; };"]
    for index, case in enumerate(document["render_cases"]):
        for label, prefix in (("input", "Input"), ("expected", "Expected"), ("public_expected", "Public")):
            ws = [int(x, 16) for x in case[label]["f32_words_le"]]
            rb = case[label]["rgba8_bytes"]
            lines.append(f"inline constexpr std::array<std::uint32_t, {len(ws)}> k{prefix}F32{index} = {{{', '.join(f'0x{x:08x}u' for x in ws)}}};")
            lines.append(f"inline constexpr std::array<std::uint8_t, {len(rb)}> k{prefix}Rgba8{index} = {{{', '.join(map(str, rb))}}};")
    lines.append(f"inline constexpr std::array<Case, {len(document['render_cases'])}> kCases = {{")
    for index, case in enumerate(document["render_cases"]):
        lines.append(f"  Case{{{json.dumps(case['name'])}, {case['width']}u, {case['height']}u, kInputF32{index}, kExpectedF32{index}, kPublicF32{index}, kInputRgba8{index}, kExpectedRgba8{index}, kPublicRgba8{index}}},")
    lines.append("};")
    for index, mutation in enumerate(document["mutation_ledger"]):
        lines.append(f"inline constexpr std::array<MutationResult, {len(mutation['required_witness_results'])}> kMutationResults{index} = {{")
        for result in mutation["required_witness_results"]:
            lines.append(f"  MutationResult{{{json.dumps(result['case'])}, {result['mismatched_lanes']}u, {result['mismatched_bytes']}u}},")
        lines.append("};")
    lines.append(f"inline constexpr std::array<Mutation, {len(document['mutation_ledger'])}> kMutations = {{")
    for index, mutation in enumerate(document["mutation_ledger"]):
        lines.append(f"  Mutation{{{json.dumps(mutation['name'])}, {json.dumps(mutation['source_anchor'])}, {json.dumps(mutation['replacement'])}, kMutationResults{index}}},")
    lines += ["};", "}", ""]
    return "\n".join(lines).encode()


def main() -> None:
    mode = next((item for item in sys.argv[1:] if item in {"--write", "--check", "--self-test"}), None)
    if mode is None or sys.argv.count(mode) != 1:
        raise MaterializationError("choose exactly one mode")
    document = validate(json.loads(checked(ORACLE)))
    expected = render(document)
    if mode == "--write":
        INCLUDE.parent.mkdir(parents=True, exist_ok=True)
        INCLUDE.write_bytes(expected)
        INCLUDE.with_name(INCLUDE.name + ".sha256").write_text(f"{digest(expected)}  {INCLUDE.name}\n")
        print(f"{len(document['render_cases'])} cases, {len(document['mutation_ledger'])} mutations materialized")
        return
    if checked(INCLUDE) != expected:
        raise MaterializationError("native include drift")
    if mode == "--self-test":
        forged = copy.deepcopy(document)
        forged["render_cases"][0]["expected"]["f32_words_le"][0] = "0x00000000"
        try:
            validate(forged)
        except MaterializationError:
            print("schema, digest, dimensions, and mutation witness checks verified")
        else:
            raise MaterializationError("forged oracle accepted")
    else:
        print("texture native oracle include check passed")


if __name__ == "__main__":
    try:
        main()
    except MaterializationError as error:
        print(f"Texture materialization failed: {error}", file=sys.stderr)
        raise SystemExit(1)
