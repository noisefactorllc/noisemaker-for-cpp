#!/usr/bin/env python3
"""Fail-closed JSON-to-C++ materializer for the prepared Fractal oracle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/fractal-parity"
ORACLE = PACKAGE / "fractal-oracles.json"
REPORT = PACKAGE / "fractal-oracle-report.md"
OUTPUT = ROOT / "tests/oracles/fractal_expected.inc"
SCHEMA = "noisemaker-for-cpp.fractal.pixel-parity.v1"
KEY = "classicNoisedeck/fractal:fractal"
SOURCE = "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/fractal/fractal.glsl"
SOURCE_SHA = "a73c8044185be58e3ae1b0f14b954dbaa7bb8852290b821dba44167fee5e037b"
FACTORY_SOURCE = "src/effects/adapters/fractal.js"
FACTORY_SHA = "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29"
EXPECTED_UPSTREAM = "117a236679d1db3ab8f0e278230ece277b57564c"
EXPECTED_AUTHORITY_PROVENANCE = "<external-authority-root>"
EXPECTED_CLOSURE_SHA256 = "b16cbd8716cab226271041751af6431bfe48fef1c0826bba89544a0f4bf525f5"
EXPECTED_ADVERSARIAL_WITNESS = {
    "case": "julia-near-escape-nonrepresentable",
    "pixel": [5, 1],
    "lane_index": 56,
    "global_coord_number": [8, -1],
    "normalized_coord_number": ["0.6153846153846154", "-0.07692307692307693"],
    "initial_state_number": ["0.20134615384615387", "-1.399807692307692"],
    "next_state_number": ["-1.9189213017751472", "-0.5636917899408284"],
    "escape_radius2": "4.000007396453121",
    "escape_margin": "0.000007396453121089053",
    "expected_f32_word": "0x3f75d177",
    "expected_rgba8_byte": 245,
}
HEX = re.compile(r"^0x[0-9a-f]{8}$")


class MaterializationError(RuntimeError):
    pass


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sidecar(path: Path) -> None:
    expected = f"{digest(path.read_bytes())}  {path.name}\n"
    if not path.is_file() or not Path(f"{path}.sha256").is_file() or Path(f"{path}.sha256").read_text() != expected:
        raise MaterializationError(f"missing or invalid sidecar: {path}")


def strict_json(path: Path):
    sidecar(path)
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise MaterializationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    try:
        return json.loads(path.read_text(), object_pairs_hook=pairs)
    except (OSError, json.JSONDecodeError) as exc:
        raise MaterializationError(f"invalid oracle JSON: {exc}") from exc


def words_digest(words: list[str]) -> str:
    try:
        raw = b"".join(struct.pack("<I", int(word, 16)) for word in words)
    except (TypeError, ValueError, struct.error) as exc:
        raise MaterializationError("invalid Float32 word") from exc
    return digest(raw)


def f32_word(value: str) -> str:
    try:
        return f"0x{struct.unpack('<I', struct.pack('<f', float(value)))[0]:08x}"
    except (TypeError, ValueError, struct.error) as exc:
        raise MaterializationError("invalid witness Number value") from exc


def f32_value(value: str) -> float:
    try:
        return struct.unpack("<f", struct.pack("<f", float(value)))[0]
    except (TypeError, ValueError, struct.error) as exc:
        raise MaterializationError("invalid witness Number value") from exc


def validate_adversarial_derivations(witness: dict) -> None:
    try:
        normalized = witness["normalized_coord_number"]
        initial = witness["initial_state_number"]
        next_state = witness["next_state_number"]
        values = [*normalized, *initial, *next_state]
        if any(not HEX.fullmatch(f32_word(value)) or f32_value(value) == float(value) for value in values):
            raise MaterializationError("witness Float32 derivation mismatch")
        next_x, next_y = (float(value) for value in next_state)
        radius2 = next_x * next_x + next_y * next_y
        margin = radius2 - 4.0
        if radius2 != float(witness["escape_radius2"]) or margin != float(witness["escape_margin"]):
            raise MaterializationError("witness radius derivation mismatch")
        if margin <= 0.0 or margin >= 0.00001:
            raise MaterializationError("witness escape margin is not near-escape")
    except (KeyError, TypeError, ValueError) as exc:
        raise MaterializationError("invalid adversarial witness Number values") from exc


def validate(doc: dict) -> None:
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or doc.get("schema_version") != 1:
        raise MaterializationError("schema identity mismatch")
    if doc.get("program_key") != KEY or doc.get("effect_key") != "classicNoisedeck/fractal":
        raise MaterializationError("program identity mismatch")
    if doc.get("upstream_revision") != EXPECTED_UPSTREAM:
        raise MaterializationError("upstream revision mismatch")
    factory = doc.get("factory", {})
    if factory.get("name") != "fractalFactory" or factory.get("text_sha256") != "0543dcdfa0c2cbe72f8a90f079100d1551ee754a11457da617c2254828d4e11f" or not factory.get("public_factory_is_canonical_identity") or not factory.get("adapter_own_key"):
        raise MaterializationError("factory identity mismatch")
    source = doc.get("provenance", {}).get("source", {})
    factory_source = doc.get("provenance", {}).get("factory_source", {})
    if source.get("relative_path") != SOURCE or source.get("sha256") != SOURCE_SHA or source.get("bytes") != 10067:
        raise MaterializationError("source provenance mismatch")
    if factory_source.get("relative_path") != FACTORY_SOURCE or factory_source.get("sha256") != FACTORY_SHA:
        raise MaterializationError("factory-source provenance mismatch")
    snap = doc.get("provenance", {}).get("cpu_snapshot", {})
    if not all(snap.get(k) is True for k in ("immutable_snapshot", "realpath_containment_checked", "live_checkout_rejected")):
        raise MaterializationError("snapshot safety flags missing")
    if snap.get("root_realpath") != EXPECTED_AUTHORITY_PROVENANCE or snap.get("import_closure_sha256") != EXPECTED_CLOSURE_SHA256:
        raise MaterializationError("pinned authority provenance/closure mismatch")
    closure = snap.get("import_closure")
    if not isinstance(closure, list) or len(closure) != 22 or digest(json.dumps(closure, separators=(",", ":")).encode()) != EXPECTED_CLOSURE_SHA256:
        raise MaterializationError("import closure digest mismatch")
    if doc.get("runtime_binding_names") != ["time", "resolution", "tileOffset", "fullResolution", "type", "symmetry", "offsetX", "offsetY", "centerX", "centerY", "zoomAmt", "speed", "rotation", "iterations", "mode", "colorMode", "paletteMode", "paletteOffset", "paletteAmp", "paletteFreq", "palettePhase", "cyclePalette", "rotatePalette", "repeatPalette", "hueRange", "levels", "bgColor", "bgAlpha", "cutoff"]:
        raise MaterializationError("runtime binding order mismatch")
    comparer = doc.get("comparer_self_tests", {})
    if not all(comparer.get(k) is True for k in ("same_dimensions_before_access", "first_mismatch_reported", "raw_words_and_rgba8_independent")) or not all(comparer.get("cases", {}).values()):
        raise MaterializationError("comparer self-test failure")
    cases = doc.get("render_cases")
    if not isinstance(cases, list) or len(cases) != 9 or len({c.get("name") for c in cases}) != 9:
        raise MaterializationError("render case census mismatch")
    for case in cases:
        width, height = case.get("width"), case.get("height")
        expected = case.get("expected", {})
        words, rgba = expected.get("f32_words_le"), expected.get("rgba8_bytes")
        if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
            raise MaterializationError("invalid case dimensions")
        if not isinstance(words, list) or len(words) != width * height * 4 or any(not isinstance(x, str) or not HEX.fullmatch(x) for x in words) or expected.get("f32_sha256") != words_digest(words):
            raise MaterializationError(f"invalid Float32 expectation: {case.get('name')}")
        if not isinstance(rgba, list) or len(rgba) != width * height * 4 or any(type(x) is not int or x < 0 or x > 255 for x in rgba) or expected.get("rgba8_sha256") != digest(bytes(rgba)):
            raise MaterializationError(f"invalid RGBA8 expectation: {case.get('name')}")
    witness = doc.get("adversarial_witness")
    if witness != EXPECTED_ADVERSARIAL_WITNESS:
        raise MaterializationError("adversarial witness contract mismatch")
    validate_adversarial_derivations(witness)
    witness_case = next((case for case in cases if case.get("name") == EXPECTED_ADVERSARIAL_WITNESS["case"]), None)
    if witness_case is None or witness_case["expected"]["f32_words_le"][56] != EXPECTED_ADVERSARIAL_WITNESS["expected_f32_word"] or witness_case["expected"]["rgba8_bytes"][56] != EXPECTED_ADVERSARIAL_WITNESS["expected_rgba8_byte"]:
        raise MaterializationError("adversarial witness output mismatch")
    mutations = doc.get("mutation_ledger")
    if not isinstance(mutations, list) or len(mutations) != 5 or doc.get("mutation_anchor_cardinality", {}).get("total") != 5:
        raise MaterializationError("mutation census mismatch")
    for mutation in mutations:
        if not mutation.get("independent") or not mutation.get("witness_cases") or not mutation.get("results"):
            raise MaterializationError("mutation witness contract missing")
        if any(result.get("changed_float32_lanes", 0) <= 0 or result.get("changed_rgba8_bytes", 0) <= 0 for result in mutation["results"]):
            raise MaterializationError(f"mutation has no pixel witness: {mutation.get('name')}")
    claim = doc.get("claim_boundaries", {})
    if claim.get("canonical_factory_only") is not True or claim.get("typed_slice_landing") is not False or claim.get("shared_emitter_modified") is not False or claim.get("first_blocker_span") != "julia:261:5-269:6":
        raise MaterializationError("claim boundary mismatch")


def render_include(doc: dict) -> bytes:
    lines = ["#pragma once", "#include <array>", "#include <cstdint>", "#include <string_view>", "", "namespace fractal_oracle {", f'inline constexpr std::string_view kSchema = "{SCHEMA}";', f'inline constexpr std::string_view kProgramKey = "{KEY}";', "struct CaseSummary { std::string_view name; std::uint32_t width; std::uint32_t height; std::string_view f32_sha256; std::string_view rgba8_sha256; };", ""]
    summaries = []
    for index, case in enumerate(doc["render_cases"]):
        words = ", ".join(case["expected"]["f32_words_le"])
        rgba = ", ".join(str(value) for value in case["expected"]["rgba8_bytes"])
        lines.append(f"inline constexpr std::array<std::uint32_t, {len(case['expected']['f32_words_le'])}> kCase{index}F32 = {{{words}}};")
        lines.append(f"inline constexpr std::array<std::uint8_t, {len(case['expected']['rgba8_bytes'])}> kCase{index}Rgba8 = {{{rgba}}};")
        summaries.append(f'  CaseSummary{{"{case["name"]}", {case["width"]}U, {case["height"]}U, "{case["expected"]["f32_sha256"]}", "{case["expected"]["rgba8_sha256"]}"}}')
    lines += ["", f"inline constexpr std::array<CaseSummary, {len(summaries)}> kCases = {{", ",\n".join(summaries), "};", "inline constexpr std::string_view kFrontendBlocker = \"counted-loop-proof:julia:261:5-269:6\";", "}  // namespace fractal_oracle", ""]
    return "\n".join(lines).encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", dest="self_test", action="store_true")
    args = parser.parse_args()
    if sum((args.write, args.check, args.self_test)) != 1:
        parser.error("choose exactly one of --write, --check, or --self-test")
    doc = strict_json(ORACLE)
    sidecar(REPORT)
    validate(doc)
    output = render_include(doc)
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(output)
        Path(f"{OUTPUT}.sha256").write_text(f"{digest(output)}  {OUTPUT.name}\n")
        print("fractal native oracle include written")
        return 0
    if args.self_test:
        for mutation in (lambda d: d.__setitem__("schema", "forged"), lambda d: d["render_cases"][0]["expected"]["f32_words_le"].__setitem__(0, "0x80000000"), lambda d: d["mutation_ledger"][0].__setitem__("independent", False)):
            candidate = json.loads(json.dumps(doc))
            mutation(candidate)
            try:
                validate(candidate)
            except MaterializationError:
                continue
            raise MaterializationError("self-test mutation accepted")
        print("strict schema, digest, comparer, and mutation self-tests verified")
        return 0
    if not OUTPUT.is_file() or Path(f"{OUTPUT}.sha256").read_text() != f"{digest(OUTPUT.read_bytes())}  {OUTPUT.name}\n" or OUTPUT.read_bytes() != output:
        raise MaterializationError("generated include drift")
    print("fractal native oracle include check passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MaterializationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
