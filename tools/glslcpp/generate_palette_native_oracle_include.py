#!/usr/bin/env python3
"""Validate and materialize the authenticated Palette oracle as C++20 metadata."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/palette-parity"
ORACLE = PACKAGE / "palette-oracles.json"
REPORT = PACKAGE / "palette-oracle-report.md"
GENERATOR = PACKAGE / "palette_oracle_generator.mjs"
INCLUDE = ROOT / "tests/oracles/palette_expected.inc"


class MaterializationError(ValueError):
    pass


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sidecar(path: Path) -> None:
    sidecar = Path(f"{path}.sha256")
    if not path.is_file() or not sidecar.is_file():
        raise MaterializationError(f"missing sidecar: {path}")
    expected = f"{_sha(path.read_bytes())}  {path.name}\n"
    if sidecar.read_text() != expected:
        raise MaterializationError(f"sidecar drift: {path}")


def _reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MaterializationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(payload: bytes):
    try:
        return json.loads(payload.decode("utf-8"), object_pairs_hook=_reject_duplicates,
                          parse_constant=lambda value: (_ for _ in ()).throw(MaterializationError(value)))
    except MaterializationError:
        raise
    except Exception as exc:
        raise MaterializationError(f"invalid JSON: {exc}") from exc


def _reject_paths(value, label="oracle"):
    if isinstance(value, str):
        if value.startswith("/") or re.search(r"(?:^|[\\/])(Users|private|tmp|home)[\\/]", value):
            raise MaterializationError(f"{label}: absolute path")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_paths(item, f"{label}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_paths(item, f"{label}.{key}")


def _hex_words(words, label):
    if not isinstance(words, list) or not all(isinstance(item, str) and re.fullmatch(r"0x[0-9a-f]{8}", item) for item in words):
        raise MaterializationError(f"{label}: invalid Float32 words")
    return b"".join(int(item, 16).to_bytes(4, "little") for item in words)


def _hex_digest(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise MaterializationError(f"{label}: invalid SHA-256")


def _f32_word(value):
    return f"0x{struct.unpack('<I', struct.pack('<f', float(value)))[0]:08x}"


def _validate_hash(value, expected, label):
    _hex_digest(value, label)
    if value != expected:
        raise MaterializationError(f"{label}: hash mismatch")


def validate(document: dict) -> dict:
    if not isinstance(document, dict):
        raise MaterializationError("oracle root must be an object")
    if document.get("schema") != "noisemaker-for-cpp.palette.pixel-parity.v1":
        raise MaterializationError("schema mismatch")
    if document.get("program_key") != "filter/palette:palette":
        raise MaterializationError("program key mismatch")
    provenance = document.get("provenance")
    factory = document.get("factory")
    if not isinstance(provenance, dict) or not isinstance(factory, dict):
        raise MaterializationError("provenance/factory contract missing")
    source = provenance.get("source")
    snapshot = provenance.get("cpu_snapshot")
    if source != {"relative_path": "src/effects/adapters/palette.js", "bytes": 5283,
                  "sha256": "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452"}:
        raise MaterializationError("source provenance mismatch")
    if factory != {"name": "paletteFactory", "text_bytes": 1408,
                   "text_sha256": "547bb6741b27cc12d6ed488cd1bbe12284ab3b916cdaefe1c747a63125523040",
                   "adapter_own_key": True, "public_factory_is_direct_identity": True}:
        raise MaterializationError("factory identity mismatch")
    if not isinstance(snapshot, dict) or snapshot.get("closure_cardinality") != 22 \
            or snapshot.get("immutable_snapshot") is not True \
            or snapshot.get("live_checkout_rejected") is not True \
            or snapshot.get("realpath_containment_checked") is not True \
            or len(snapshot.get("import_closure", [])) != 22:
        raise MaterializationError("CPU import closure contract mismatch")
    for item in snapshot["import_closure"]:
        if set(item) != {"relative_path", "sha256"} or Path(item["relative_path"]).is_absolute():
            raise MaterializationError("import closure path drift")
        _hex_digest(item["sha256"], "import closure")
    _reject_paths(document)
    names = document.get("runtime_binding_names")
    if names != ["inputTex", "tileOffset", "fullResolution", "paletteIndex", "rotation", "offset", "repeat", "alpha", "time"]:
        raise MaterializationError("runtime binding names mismatch")
    abi = document.get("runtime_binding_abi")
    if abi != {"inputTex": "sampler2D", "tileOffset": "Vec2", "fullResolution": "Vec2", "paletteIndex": "int32", "rotation": "int32", "offset": "number", "repeat": "number", "alpha": "number", "time": "number"}:
        raise MaterializationError("runtime binding ABI mismatch")
    source_abi = document.get("source_uniform_abi")
    if source_abi != {"inputTex": "sampler2D", "tileOffset": "vec2", "fullResolution": "vec2", "paletteIndex": "int", "rotation": "int", "offset": "float", "repeat": "float", "alpha": "float", "time": "float"}:
        raise MaterializationError("source uniform ABI mismatch")
    comparer = document.get("comparer_self_tests")
    if not isinstance(comparer, dict) or set(comparer) != {"good_equal", "dimensions_mismatch", "short_lane_count", "rgba8_mismatch", "signed_zero", "nan_payload"} or not all(comparer.values()):
        raise MaterializationError("strict comparer self-tests mismatch")
    cases = document.get("render_cases")
    if not isinstance(cases, list) or len(cases) < 8:
        raise MaterializationError("Palette render case cardinality mismatch")
    case_names = set()
    binding_names = {"inputTex", "tileOffset", "fullResolution", "paletteIndex", "rotation", "offset", "repeat", "alpha", "time"}
    value_binding_names = binding_names - {"inputTex"}
    for case in cases:
        if set(case) != {"name", "width", "height", "bindings", "binding_words", "input", "expected", "input_immutable_exact_bits", "input_lifetime_stable", "repeat_output_object_distinct", "repeat_output_data_distinct"}:
            raise MaterializationError("Palette render case schema drift")
        if case["name"] in case_names or not isinstance(case["width"], int) or isinstance(case["width"], bool) or not isinstance(case["height"], int) or isinstance(case["height"], bool) or case["width"] <= 0 or case["height"] <= 0:
            raise MaterializationError("Palette render case identity drift")
        if not isinstance(case["bindings"], dict) or set(case["bindings"]) != value_binding_names:
            raise MaterializationError("Palette binding value schema drift")
        case_names.add(case["name"])
        size = case["width"] * case["height"] * 4
        inp, out = case["input"], case["expected"]
        if set(inp) != {"f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"} or set(out) != {"f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"}:
            raise MaterializationError("Palette input/output schema drift")
        if len(inp.get("f32_words_le", [])) != size or len(out.get("f32_words_le", [])) != size or len(out.get("rgba8_bytes", [])) != size:
            raise MaterializationError("Palette render case cardinality drift")
        for obj, suffix in ((inp, "input"), (out, "expected")):
            packed = _hex_words(obj["f32_words_le"], f"{case['name']} {suffix}")
            if obj["f32_sha256"] != _sha(packed):
                raise MaterializationError("Palette Float32 hash mismatch")
        if out["rgba8_sha256"] != _sha(bytes(out["rgba8_bytes"])) or not all(isinstance(item, int) and 0 <= item <= 255 for item in out["rgba8_bytes"]):
            raise MaterializationError("Palette RGBA8 hash mismatch")
        if not all(isinstance(item, int) and not isinstance(item, bool) for item in out["rgba8_bytes"]):
            raise MaterializationError("Palette RGBA8 type drift")
        binding_words = case["binding_words"]
        if not isinstance(binding_words, dict) or set(binding_words) != binding_names:
            raise MaterializationError("Palette binding words cardinality drift")
        for name in ("tileOffset", "fullResolution"):
            item = binding_words[name]
            if set(item) != {"values", "f32_words_le"} or not isinstance(item["values"], list) or len(item["values"]) != 2 or len(item["f32_words_le"]) != 2:
                raise MaterializationError(f"Palette {name} raw binding schema drift")
            _hex_words(item["f32_words_le"], f"{case['name']} {name}")
            if item["values"] != case["bindings"][name] or any(word != _f32_word(value) for word, value in zip(item["f32_words_le"], item["values"])):
                raise MaterializationError(f"Palette {name} binding value drift")
        item = binding_words["inputTex"]
        if set(item) != {"width", "height", "f32_words_le", "f32_sha256"} or item["width"] != case["width"] or item["height"] != case["height"] or item["f32_words_le"] != inp["f32_words_le"] or item["f32_sha256"] != inp["f32_sha256"]:
            raise MaterializationError("Palette inputTex binding replay drift")
        for name in ("paletteIndex", "rotation"):
            item = binding_words[name]
            if set(item) != {"value", "int32", "f32_words_le"} or not isinstance(item["value"], int) or isinstance(item["value"], bool) or item["value"] != case["bindings"][name] or item["int32"] != item["value"] or len(item["f32_words_le"]) != 1:
                raise MaterializationError(f"Palette {name} binding ABI drift")
            _hex_words(item["f32_words_le"], f"{case['name']} {name}")
            if item["f32_words_le"][0] != _f32_word(item["value"]):
                raise MaterializationError(f"Palette {name} raw word drift")
        for name in ("offset", "repeat", "alpha", "time"):
            item = binding_words[name]
            if set(item) != {"value", "f32_words_le"} or not isinstance(item["value"], (int, float)) or isinstance(item["value"], bool) or item["value"] != case["bindings"][name] or len(item["f32_words_le"]) != 1:
                raise MaterializationError(f"Palette {name} binding ABI drift")
            _hex_words(item["f32_words_le"], f"{case['name']} {name}")
            if item["f32_words_le"][0] != _f32_word(item["value"]):
                raise MaterializationError(f"Palette {name} raw word drift")
        if not all(case[field] is True for field in ("input_immutable_exact_bits", "input_lifetime_stable", "repeat_output_object_distinct", "repeat_output_data_distinct")):
            raise MaterializationError("Palette lifetime/immutability contract mismatch")
    mutations = document.get("mutation_ledger")
    if not isinstance(mutations, list) or len(mutations) < 12:
        raise MaterializationError("Palette mutation ledger cardinality mismatch")
    mutation_names = set()
    for mutation in mutations:
        required = {"name", "source_anchor", "replacement", "anchor_sha256", "replacement_sha256", "mutated_factory_sha256", "required_witnesses", "required_witness_results", "independent"}
        if set(mutation) != required or mutation["name"] in mutation_names or mutation["independent"] is not True:
            raise MaterializationError("Palette mutation ledger schema drift")
        mutation_names.add(mutation["name"])
        _validate_hash(mutation["anchor_sha256"], _sha(mutation["source_anchor"].encode()), "mutation anchor")
        _validate_hash(mutation["replacement_sha256"], _sha(mutation["replacement"].encode()), "mutation replacement")
        _hex_digest(mutation["mutated_factory_sha256"], "mutated factory")
        if not mutation["required_witnesses"] or len(mutation["required_witness_results"]) != len(mutation["required_witnesses"]):
            raise MaterializationError("Palette mutation witness cardinality mismatch")
        for result in mutation["required_witness_results"]:
            if result["case"] not in case_names or result["mismatched_lanes"] <= 0 or result["mismatched_bytes"] <= 0:
                raise MaterializationError("Palette mutation witness is not divergent")
    return document


def _cpp_string(value: str) -> str:
    return json.dumps(value)


def materialize(document: dict) -> bytes:
    cases = document["render_cases"]
    mutations = document["mutation_ledger"]
    lines = ["#pragma once", "#include <array>", "#include <cstddef>", "#include <cstdint>", "#include <span>", "#include <string_view>", "", "namespace noisemaker_palette_oracle {", "", f"inline constexpr std::string_view kSchema = \"noisemaker-for-cpp.palette.pixel-parity.v1\";", "inline constexpr std::string_view kProgramKey = \"filter/palette:palette\";", f"inline constexpr std::string_view kOracleSha256 = {_cpp_string(_sha(ORACLE.read_bytes()))};", f"inline constexpr std::string_view kFactoryTextSha256 = {_cpp_string(document['factory']['text_sha256'])};", "struct BindingWords { std::array<std::uint32_t, 2> tile_offset; std::array<std::uint32_t, 2> full_resolution; std::int32_t palette_index; std::int32_t rotation; std::uint32_t offset; std::uint32_t repeat; std::uint32_t alpha; std::uint32_t time; std::size_t input_width; std::size_t input_height; };", ""]
    for index, case in enumerate(cases):
        input_words = ", ".join(f"{int(word, 16)}U" for word in case["input"]["f32_words_le"])
        output_words = ", ".join(f"{int(word, 16)}U" for word in case["expected"]["f32_words_le"])
        rgba8 = ", ".join(f"{value}U" for value in case["expected"]["rgba8_bytes"])
        binding = case["binding_words"]
        tile = ", ".join(f"{int(word, 16)}U" for word in binding["tileOffset"]["f32_words_le"])
        full = ", ".join(f"{int(word, 16)}U" for word in binding["fullResolution"]["f32_words_le"])
        raw = lambda name: f"{int(binding[name]['f32_words_le'][0], 16)}U"
        lines.extend([
            f"inline constexpr std::array<std::uint32_t, {len(case['input']['f32_words_le'])}> kInput{index}{{{{{input_words}}}}};",
            f"inline constexpr std::array<std::uint32_t, {len(case['expected']['f32_words_le'])}> kCase{index}Words{{{{{output_words}}}}};",
            f"inline constexpr std::array<std::uint8_t, {len(case['expected']['rgba8_bytes'])}> kCase{index}Rgba8{{{{{rgba8}}}}};",
            f"inline constexpr BindingWords kBindingWords{index}{{std::array<std::uint32_t, 2>{{{{{tile}}}}}, std::array<std::uint32_t, 2>{{{{{full}}}}}, {int(binding['paletteIndex']['int32'])}, {int(binding['rotation']['int32'])}, {raw('offset')}, {raw('repeat')}, {raw('alpha')}, {raw('time')}, {binding['inputTex']['width']}U, {binding['inputTex']['height']}U}};",
        ])
    lines.extend(["struct CaseView { std::string_view name; std::size_t width; std::size_t height; std::size_t palette_index; std::span<const std::uint32_t> input_f32_words; std::span<const std::uint32_t> f32_words; std::span<const std::uint8_t> rgba8_bytes; BindingWords binding_words; std::string_view input_lifetime; bool input_immutable_exact_bits; bool input_lifetime_stable; bool repeat_output_object_distinct; bool repeat_output_data_distinct; };", f"inline constexpr std::array<CaseView, {len(cases)}> kCases{{{{"])
    for index, case in enumerate(cases):
        lines.append(f"  CaseView{{{_cpp_string(case['name'])}, {case['width']}U, {case['height']}U, {case['bindings']['paletteIndex']}U, kInput{index}, kCase{index}Words, kCase{index}Rgba8, kBindingWords{index}, \"caller-owned-independent-surface\", true, {str(case['input_lifetime_stable']).lower()}, {str(case['repeat_output_object_distinct']).lower()}, {str(case['repeat_output_data_distinct']).lower()}}},")
    lines.extend(["}};", "struct BindingView { std::string_view name; std::string_view abi; };", f"inline constexpr std::array<BindingView, {len(document['runtime_binding_names'])}> kBindings{{{{"])
    for name in document["runtime_binding_names"]:
        lines.append(f"  BindingView{{{_cpp_string(name)}, {_cpp_string(document['runtime_binding_abi'][name])}}},")
    lines.append("}};")
    lines.append("struct MutationView { std::string_view name; std::string_view source_anchor; std::string_view replacement; std::size_t witness_count; };")
    lines.append(f"inline constexpr std::array<MutationView, {len(mutations)}> kMutations{{{{")
    for mutation in mutations:
        lines.append(f"  MutationView{{{_cpp_string(mutation['name'])}, {_cpp_string(mutation['source_anchor'])}, {_cpp_string(mutation['replacement'])}, {len(mutation['required_witnesses'])}U}},")
    lines.append("}};")
    lines.append("inline constexpr std::array<std::string_view, 6> kComparerSelfTests{{\"good_equal\", \"dimensions_mismatch\", \"short_lane_count\", \"rgba8_mismatch\", \"signed_zero\", \"nan_payload\"}};")
    lines.append("}\n")
    return "\n".join(lines).encode("utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in {"--check", "--write", "--self-test"}:
        raise MaterializationError("choose exactly one of --check, --write, or --self-test")
    for path in (GENERATOR, ORACLE, REPORT):
        _sidecar(path)
    document = validate(strict_json(ORACLE.read_bytes()))
    payload = materialize(document)
    if argv[0] == "--write":
        INCLUDE.parent.mkdir(parents=True, exist_ok=True)
        INCLUDE.write_bytes(payload)
        Path(f"{INCLUDE}.sha256").write_text(f"{_sha(payload)}  {INCLUDE.name}\n")
        materializer = Path(__file__)
        Path(f"{materializer}.sha256").write_text(
            f"{_sha(materializer.read_bytes())}  {materializer.name}\n"
        )
        print(f"{len(document['render_cases'])} cases, {len(document['mutation_ledger'])} mutations materialized")
        return 0
    _sidecar(INCLUDE)
    if INCLUDE.read_bytes() != payload:
        raise MaterializationError("Palette native include drift")
    if argv[0] == "--self-test":
        probes = []
        forged = json.loads(json.dumps(document)); forged["render_cases"][0]["expected"]["f32_words_le"][0] = "0x80000000"; probes.append(("output words", forged))
        forged = json.loads(json.dumps(document)); forged["render_cases"][0]["input"]["f32_words_le"][0] = "0x00000000"; probes.append(("input words", forged))
        forged = json.loads(json.dumps(document)); forged["render_cases"][1]["binding_words"]["offset"]["f32_words_le"][0] = "0x00000000"; probes.append(("binding words", forged))
        forged = json.loads(json.dumps(document)); del forged["render_cases"][0]["binding_words"]["time"]; probes.append(("binding cardinality", forged))
        for label, candidate in probes:
            try:
                validate(candidate)
            except MaterializationError:
                continue
            raise MaterializationError(f"forged {label} accepted")
        print(f"strict replayable oracle forgery probes verified ({len(probes)})")
    else:
        print(f"{len(document['render_cases'])} cases, {len(document['mutation_ledger'])} mutations checked")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except MaterializationError as exc:
        print(f"palette materializer: {exc}", file=sys.stderr)
        raise SystemExit(1)
