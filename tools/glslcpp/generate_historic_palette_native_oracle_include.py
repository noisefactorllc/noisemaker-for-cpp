#!/usr/bin/env python3
"""Fail-closed materializer for the Historic Palette pixel oracle."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import struct

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/historic-palette-parity"
ORACLE = PACKAGE / "historic-palette-oracles.json"
TARGET = ROOT / "tests/oracles/historic_palette_expected.inc"
SCHEMA = "noisemaker-for-cpp.historic-palette.pixel-parity.v1"
KEY = "filter/historicPalette:historicPalette"
HEX_WORD = re.compile(r"^0x[0-9a-f]{8}$")
HEX_HASH = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_BINDINGS = ["tileOffset", "fullResolution", "inputTex", "paletteIndex", "smoothness", "rotation", "offset", "repeat", "alpha", "time"]

class MaterializationError(ValueError):
    pass

def _sha_bytes(values: list[str]) -> str:
    return hashlib.sha256(b"".join(int(x, 16).to_bytes(4, "little") for x in values)).hexdigest()

def _sha_bytes8(values: list[int]) -> str:
    return hashlib.sha256(bytes(values)).hexdigest()

def _f32_word(value: object) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', float(value)))[0]:08x}"

def _binding_word(value: object, label: str) -> str:
    if not isinstance(value, str) or not HEX_WORD.fullmatch(value):
        raise MaterializationError(f"{label}: raw Float32 word required")
    return value

def _reject_absolute(value: object, label: str = "document") -> None:
    if isinstance(value, str):
        if value.startswith(("/", "\\\\")) or re.search(r"(?:^|[\\/])(Users|private|tmp|home)[\\/]", value):
            raise MaterializationError(f"{label}: absolute-looking string")
    elif isinstance(value, list):
        for i, item in enumerate(value): _reject_absolute(item, f"{label}[{i}]")
    elif isinstance(value, dict):
        for key, item in value.items(): _reject_absolute(item, f"{label}.{key}")

def _exact(value: object, fields: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != fields: raise MaterializationError(f"{label}: exact fields required")

def validate(document: dict) -> dict:
    _reject_absolute(document)
    _exact(document, {"schema", "schema_version", "program_key", "effect_key", "runtime_key", "corpus_revision", "upstream_revision", "factory", "runtime_binding_names", "runtime_binding_abi", "canonical_binding_contract", "exactness_contract", "comparer_self_tests", "provenance", "render_cases", "source_mutation_contract", "mutation_anchor_cardinality", "mutation_ledger", "control_group", "claim_boundaries"}, "document")
    if document["schema"] != SCHEMA or document["schema_version"] != 1 or document["program_key"] != KEY or document["effect_key"] != "filter/historicPalette" or document["runtime_key"] != KEY: raise MaterializationError("identity drift")
    if document["factory"].get("name") != "historicPaletteFactory" or not document["factory"].get("public_factory_is_canonical_identity") or not document["factory"].get("adapter_own_key") or not HEX_HASH.fullmatch(document["factory"].get("text_sha256", "")): raise MaterializationError("factory identity drift")
    if document["runtime_binding_names"] != EXPECTED_BINDINGS or document["canonical_binding_contract"]["names"] != EXPECTED_BINDINGS: raise MaterializationError("binding names drift")
    if document["exactness_contract"].get("tolerance") != "none" or document["exactness_contract"].get("comparison") != "dimensions, counts, every uint32 word, every RGBA8 byte": raise MaterializationError("exactness contract drift")
    comparer = document["comparer_self_tests"]
    if set(comparer) != {"dimensions_before_access", "first_mismatch_reported", "raw_words_and_rgba8_independent", "cases"} or not all(comparer.get(name) is True for name in ("dimensions_before_access", "first_mismatch_reported", "raw_words_and_rgba8_independent")): raise MaterializationError("comparer contract drift")
    if set(comparer.get("cases", {})) != {"good", "dimensions", "short", "long", "rgba8_count", "rgba8_mismatch", "signed_zero", "nan_payload"} or not all(value is True for value in comparer["cases"].values()): raise MaterializationError("comparer self-test drift")
    closure = document["provenance"]["cpu_snapshot"].get("import_closure", [])
    if document["provenance"]["cpu_snapshot"].get("immutable_snapshot") is not True or document["provenance"]["cpu_snapshot"].get("live_checkout_rejected") is not True or document["provenance"]["cpu_snapshot"].get("closure_cardinality") != len(closure) or not closure: raise MaterializationError("immutable closure contract drift")
    if any(set(row) != {"relative_path", "sha256"} or not isinstance(row["relative_path"], str) or row["relative_path"].startswith("../") or "/../" in row["relative_path"] or not HEX_HASH.fullmatch(row["sha256"]) for row in closure): raise MaterializationError("closure hash drift")
    if [row["relative_path"] for row in closure] != sorted({row["relative_path"] for row in closure}) or len({row["relative_path"] for row in closure}) != len(closure): raise MaterializationError("closure ordering/cardinality drift")
    source = document["provenance"]["source"]
    if source != {"relative_path": "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/historicPalette/historicPalette.glsl", "sha256": "cc0feb09e2f90505766a0b8b0d61ca0cf83a1121ec7b104eea5ff806c9ce0c33"}: raise MaterializationError("source provenance drift")
    cases = document["render_cases"]
    if len(cases) != 21 or [case.get("name") for case in cases] != [f"palette-{i}" for i in range(21)]: raise MaterializationError("case cardinality/order drift")
    case_fields = {"name", "width", "height", "time", "paletteIndex", "smoothness", "rotation", "offset", "repeat", "alpha", "tileX", "tileY", "salt", "input", "input_f32_words_le", "input_f32_sha256", "expected", "input_immutable_exact_bits", "input_lifetime", "input_surface_not_released", "bindings", "binding_words", "repeat_identity", "repeat_output_object_distinct", "repeat_output_data_distinct", "public_direct_identity", "independent_output_storage"}
    binding_fields = {"tileOffset", "fullResolution", "inputTex", "paletteIndex", "smoothness", "rotation", "offset", "repeat", "alpha", "time"}
    for index, case in enumerate(cases):
        if set(case) != case_fields: raise MaterializationError(f"case {index}: exact schema required")
        expected = case.get("width", 0) * case.get("height", 0) * 4
        if case.get("paletteIndex") != index or expected <= 0: raise MaterializationError(f"case {index}: identity/dimensions drift")
        for field in ("input", "expected"):
            payload = case.get(field, {})
            if len(payload.get("f32_words_le", [])) != expected or any(not isinstance(x, str) or not HEX_WORD.fullmatch(x) for x in payload.get("f32_words_le", [])) or payload.get("f32_sha256") != _sha_bytes(payload["f32_words_le"]): raise MaterializationError(f"case {index}: {field} Float32 drift")
        if case["input_f32_words_le"] != case["input"]["f32_words_le"] or case["input_f32_sha256"] != case["input"]["f32_sha256"]: raise MaterializationError(f"case {index}: native input replay drift")
        if case["input_immutable_exact_bits"] is not True or case["input_lifetime"] != "caller-owned-independent-surface" or case["input_surface_not_released"] is not True: raise MaterializationError(f"case {index}: input lifetime contract drift")
        output = case["expected"]
        if len(output.get("rgba8_bytes", [])) != expected or any(not isinstance(x, int) or isinstance(x, bool) or x < 0 or x > 255 for x in output["rgba8_bytes"]) or output.get("rgba8_sha256") != _sha_bytes8(output["rgba8_bytes"]): raise MaterializationError(f"case {index}: RGBA8 drift")
        if case.get("independent_output_storage") is not True or case.get("repeat_identity") is not True or case.get("repeat_output_object_distinct") is not True or case.get("repeat_output_data_distinct") is not True or case.get("public_direct_identity") is not True: raise MaterializationError(f"case {index}: storage contract drift")
        binding_words = case.get("binding_words")
        if not isinstance(binding_words, dict) or set(binding_words) != binding_fields: raise MaterializationError(f"case {index}: binding cardinality drift")
        if case["bindings"].get("binding_words") != binding_words: raise MaterializationError(f"case {index}: binding alias drift")
        for name in ("tileOffset", "fullResolution"):
            item = binding_words[name]
            _exact(item, {"values", "f32_words_le"}, f"case {index}: {name}")
            if len(item["f32_words_le"]) != 2 or any(not isinstance(word, str) or not HEX_WORD.fullmatch(word) for word in item["f32_words_le"]): raise MaterializationError(f"case {index}: {name} words drift")
            if any(word != _f32_word(value) for word, value in zip(item["f32_words_le"], item["values"])): raise MaterializationError(f"case {index}: {name} value/word drift")
        if binding_words["tileOffset"]["values"] != [case["tileX"], case["tileY"]] or binding_words["fullResolution"]["values"] != [case["width"], case["height"]]: raise MaterializationError(f"case {index}: binding value drift")
        item = binding_words["inputTex"]
        _exact(item, {"width", "height", "f32_words_le", "f32_sha256"}, f"case {index}: inputTex")
        if item["width"] != case["width"] or item["height"] != case["height"] or item["f32_words_le"] != case["input_f32_words_le"] or item["f32_sha256"] != case["input_f32_sha256"]: raise MaterializationError(f"case {index}: inputTex replay drift")
        for name in ("paletteIndex", "rotation"):
            item = binding_words[name]
            _exact(item, {"value", "int32", "f32_words_le"}, f"case {index}: {name}")
            if item["value"] != case[name] or item["int32"] != int(item["value"]) or len(item["f32_words_le"]) != 1 or item["f32_words_le"][0] != _f32_word(item["value"]): raise MaterializationError(f"case {index}: {name} raw word drift")
        for name in ("smoothness", "offset", "repeat", "alpha", "time"):
            item = binding_words[name]
            _exact(item, {"value", "f32_words_le"}, f"case {index}: {name}")
            if item["value"] != case[name] or len(item["f32_words_le"]) != 1 or item["f32_words_le"][0] != _f32_word(item["value"]): raise MaterializationError(f"case {index}: {name} raw word drift")
    ledger = document["mutation_ledger"]
    if len(ledger) != document["mutation_anchor_cardinality"].get("total") or len(ledger) < 6: raise MaterializationError("mutation ledger cardinality drift")
    for row in ledger:
        if not row.get("independent") or row.get("structural_only") or not row.get("required_witnesses") or row.get("anchor_occurrence_count") != 1: raise MaterializationError("mutation witness contract drift")
        for field in ("source_sha256", "canonical_factory_text_sha256", "source_anchor_sha256", "replacement_sha256", "mutated_factory_text_sha256"):
            if not HEX_HASH.fullmatch(row.get(field, "")): raise MaterializationError(f"mutation hash drift: {field}")
    return document

def _render(document: dict) -> str:
    cases = document["render_cases"]
    out = ["// Generated from the authenticated Historic Palette JSON oracle.\n#pragma once\n#include <array>\n#include <cstddef>\n#include <cstdint>\n#include <span>\n#include <string_view>\n\nnamespace historic_palette_oracle {\n", f'inline constexpr std::string_view kProgramKey = "{KEY}";\n', f'inline constexpr std::string_view kOracleSha256 = "{hashlib.sha256(ORACLE.read_bytes()).hexdigest()}";\n', f'inline constexpr std::string_view kFactoryTextSha256 = "{document["factory"]["text_sha256"]}";\n', "struct BindingWords { std::array<std::uint32_t, 2> tile_offset; std::array<std::uint32_t, 2> full_resolution; std::int32_t palette_index; std::int32_t rotation; std::uint32_t smoothness; std::uint32_t offset; std::uint32_t repeat; std::uint32_t alpha; std::uint32_t time; std::size_t input_width; std::size_t input_height; };\n"]
    for i, case in enumerate(cases):
        input_words = ", ".join(f"{int(x, 16)}U" for x in case["input_f32_words_le"])
        words = ", ".join(f"{int(x, 16)}U" for x in case["expected"]["f32_words_le"])
        rgba = ", ".join(f"{x}U" for x in case["expected"]["rgba8_bytes"])
        binding = case["binding_words"]
        tile = ", ".join(f"{int(x, 16)}U" for x in binding["tileOffset"]["f32_words_le"])
        full = ", ".join(f"{int(x, 16)}U" for x in binding["fullResolution"]["f32_words_le"])
        raw = lambda name: f"{int(binding[name]['f32_words_le'][0], 16)}U"
        out += [f"inline constexpr std::array<std::uint32_t, {len(case['input_f32_words_le'])}> kInput{i}{{{input_words}}};\n", f"inline constexpr std::array<std::uint32_t, {len(case['expected']['f32_words_le'])}> kCase{i}Words{{{words}}};\n", f"inline constexpr std::array<std::uint8_t, {len(case['expected']['rgba8_bytes'])}> kCase{i}Rgba8{{{rgba}}};\n", f"inline constexpr BindingWords kBindingWords{i}{{std::array<std::uint32_t, 2>{{{tile}}}, std::array<std::uint32_t, 2>{{{full}}}, {int(binding['paletteIndex']['int32'])}, {int(binding['rotation']['int32'])}, {raw('smoothness')}, {raw('offset')}, {raw('repeat')}, {raw('alpha')}, {raw('time')}, {binding['inputTex']['width']}U, {binding['inputTex']['height']}U}};\n"]
    out += ["struct CaseView { std::string_view name; std::size_t width; std::size_t height; std::size_t palette_index; std::span<const std::uint32_t> input_f32_words; std::span<const std::uint32_t> f32_words; std::span<const std::uint8_t> rgba8_bytes; BindingWords binding_words; std::string_view input_lifetime; bool input_immutable_exact_bits; bool input_surface_not_released; bool input_storage_independent; };\n", "inline constexpr std::array<CaseView, 21> kCases{\n"]
    for i, case in enumerate(cases): out.append(f'  CaseView{{"{case["name"]}", {case["width"]}U, {case["height"]}U, {case["paletteIndex"]}U, kInput{i}, kCase{i}Words, kCase{i}Rgba8, kBindingWords{i}, "{case["input_lifetime"]}", {str(case["input_immutable_exact_bits"]).lower()}, {str(case["input_surface_not_released"]).lower()}, {str(case["independent_output_storage"]).lower()}}},\n')
    out += ["};\nstruct MutationView { std::string_view name; std::size_t witness_count; std::size_t anchor_occurrence_count; };\n", f"inline constexpr std::array<MutationView, {len(document['mutation_ledger'])}> kMutations{{\n"]
    for row in document["mutation_ledger"]: out.append(f'  MutationView{{"{row["name"]}", {len(row["required_witnesses"])}U, {row["anchor_occurrence_count"]}U}},\n')
    out += ["};\n}\n"]
    return "".join(out)

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true"); parser.add_argument("--self-test", action="store_true"); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    if sum((args.check, args.self_test, args.write)) != 1: parser.error("choose exactly one of --check, --self-test, or --write")
    document = validate(json.loads(ORACLE.read_text(encoding="utf-8"))); rendered = _render(document)
    if args.self_test:
        print(f"historic palette materializer self-test: {len(document['mutation_ledger'])}/{len(document['mutation_ledger'])} pass"); return 0
    if args.write:
        TARGET.write_text(rendered, encoding="utf-8"); (TARGET.with_name(TARGET.name + ".sha256")).write_text(f"{hashlib.sha256(rendered.encode()).hexdigest()}  {TARGET.name}\n", encoding="utf-8"); print(f"historic palette include written ({len(rendered)} bytes)"); return 0
    if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != rendered: raise MaterializationError("historic palette include drift")
    sidecar = TARGET.with_name(TARGET.name + ".sha256"); expected = f"{hashlib.sha256(rendered.encode()).hexdigest()}  {TARGET.name}\n"; 
    if not sidecar.exists() or sidecar.read_text(encoding="utf-8") != expected: raise MaterializationError("historic palette include sidecar drift")
    print("historic palette materializer: ok"); return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except MaterializationError as error: raise SystemExit(str(error))
