#!/usr/bin/env python3
"""Fail-closed JSON-to-C++ materializer for the prepared Distortion oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/distortion-parity"
ORACLE = PACKAGE / "distortion-oracles.json"
REPORT = PACKAGE / "distortion-oracle-report.md"
OUTPUT = ROOT / "tests/oracles/distortion_expected.inc"
SCHEMA = "noisemaker-for-cpp.distortion.pixel-parity.v1"
KEY = "mixer/distortion:distortion"
SOURCE = "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/mixer/distortion/distortion.glsl"
SOURCE_SHA = "569fbab57b57baad275a60facfd70b913afe76d69a724b682e821883d40dcae8"
FACTORY_SHA = "4f962484b211546300a659acde664df1d9430ceff7108d0877c13cf47d5a3fa5"
HEX = re.compile(r"^0x[0-9a-f]{8}$")
EXPECTED_CLOSURE = [
    ("src/csl/glsl-kernel.js", "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa"),
    ("src/csl/glsl-runtime.js", "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072"),
    ("src/csl/runtime.js", "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee"),
    ("src/effects/adapters/bit-effects.js", "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7"),
    ("src/effects/adapters/crt.js", "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc"),
    ("src/effects/adapters/f32-color.js", "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046"),
    ("src/effects/adapters/fractal.js", "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29"),
    ("src/effects/adapters/index.js", "40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267"),
    ("src/effects/adapters/julia.js", "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5"),
    ("src/effects/adapters/median.js", "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583"),
    ("src/effects/adapters/palette.js", "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452"),
    ("src/effects/adapters/snow.js", "202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366"),
    ("src/effects/catalog.js", "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4"),
    ("src/effects/definition.js", "fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02"),
    ("src/effects/generated/canonical-adapter-data.js", "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab"),
    ("src/effects/generated/canonical-kernels.js", "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe"),
    ("src/effects/generated/kernels.js", "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01"),
    ("src/effects/generated/upstream-snapshot.js", "e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090"),
    ("src/effects/registry.js", "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618"),
    ("src/runtime/pass-runner.js", "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa"),
    ("src/runtime/sampler.js", "1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328"),
    ("src/runtime/surface.js", "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59"),
]
EXPECTED_BINDING_NAMES = ["inputTex", "tex", "resolution", "tileOffset", "fullResolution", "mode", "mapSource", "intensity", "wrap", "smoothing", "aberration", "antialias"]
EXPECTED_RUNTIME_ABI = {"inputTex": "Surface", "tex": "Surface", "resolution": "Vec2", "tileOffset": "Vec2", "fullResolution": "Vec2", "mode": "int32", "mapSource": "int32", "intensity": "number", "wrap": "int32", "smoothing": "number", "aberration": "number", "antialias": "bool"}
EXPECTED_SOURCE_ABI = {"inputTex": "sampler2D", "tex": "sampler2D", "resolution": "vec2", "tileOffset": "vec2", "fullResolution": "vec2", "mode": "int", "mapSource": "int", "intensity": "float", "wrap": "int", "smoothing": "float", "aberration": "float", "antialias": "bool"}
EXPECTED_CASE_CONTROLS = [
    ("displacement-mirror-map-a", 8, 6, 1, 2, 0, 0, 0, 65, 1, 0, False, [0, 0], [8, 6]),
    ("displacement-repeat-map-b-aa", 7, 5, 3, 4, 0, 1, 1, 90, 4, 0, True, [2, 1], [13, 9]),
    ("refraction-clamp-map-a", 9, 6, 5, 6, 1, 0, 2, 75, 12, 0, False, [0, 0], [9, 6]),
    ("refraction-mirror-map-b-aa", 6, 8, 7, 8, 1, 1, 0, 35, 3, 0, True, [-1, 3], [12, 15]),
    ("reflection-repeat-chromatic", 8, 7, 9, 10, 2, 0, 1, 100, 9, 22, False, [1, -2], [14, 11]),
    ("reflection-clamp-chromatic-aa", 7, 6, 11, 12, 2, 1, 2, 48, 20, 7, True, [0, 0], [7, 6]),
]
EXPECTED_MUTATIONS = [
    (
        "mode-displacement-to-reflection", "if (mode == 0)", "if (mode == 2)",
        "34abfffa3ee7924b70b6cb00b67226a2d09370cb614058fd08fd8d4d7380d034",
        "e27fe9f9218ec1e0d5e2580ed2e94e260adbbe023161a1ed69f791c1aa292c55",
        "c0f79ade9162082dfbc103ee5e025c7c28e85428b8155727c3a98055f3f1a231",
        ("displacement-mirror-map-a", "displacement-repeat-map-b-aa"),
        (("displacement-mirror-map-a", 192, 192, False),
         ("displacement-repeat-map-b-aa", 140, 140, False)),
    ),
    (
        "wrap-repeat-to-clamp", "wrap == 1", "wrap == 2",
        "7ba5f64201e29b6b8bb71150afc79e5227c47135bccf40a0a79ea8fb7b7d2b6c",
        "7377363c5e4ccd9bc5982735782603e3e317ca62dcfbaa9b763b62fd8a4cf372",
        "30d53a97335b36d25582131b2212f263864af1001d26785a0d7a41f71159146c",
        ("displacement-repeat-map-b-aa", "reflection-repeat-chromatic"),
        (("displacement-repeat-map-b-aa", 108, 105, False),
         ("reflection-repeat-chromatic", 47, 47, False)),
    ),
    (
        "displacement-strength-half",
        "offset[0] = (cos(len * 6.2831854820251465)) * (intensity * 0.0010000000474974513);",
        "offset[0] = (cos(len * 6.2831854820251465)) * (intensity * 0.0005000000237487257);",
        "a33418f58436c73968e5590fe973e541cf1fe461031d1ecc6f4e5a69e37cc9be",
        "8ccbb8066b0b4cbd79f4e01ff2d2b6cb7d9fee3b169b3df7857f44db59ece97a",
        "6fccb470a39a70fb74bf29e52744e5738b3eaed6cb5efd53e0251cfe70ac2535",
        ("displacement-mirror-map-a", "displacement-repeat-map-b-aa"),
        (("displacement-mirror-map-a", 28, 28, False),
         ("displacement-repeat-map-b-aa", 127, 126, False)),
    ),
]
EXPECTED_CLAIM_BOUNDARIES = {
    "canonical_factory_only": True,
    "typed_slice_landing": False,
    "shared_emitter_modified": False,
    "first_blocker": "sampler-parameter:calculateNormal:26:1-72:2",
    "additional_blockers": [
        "derivative-abi:6 call sites",
        "mutable-local-arrays:3 declarations / 30 indexed expressions",
    ],
}
TOP_LEVEL_FIELDS = {"schema", "schema_version", "program_key", "effect_key", "corpus_revision", "upstream_revision", "factory", "runtime_binding_names", "runtime_binding_abi", "source_uniform_abi", "provenance", "comparer_self_tests", "render_cases", "mutation_anchor_cardinality", "mutation_ledger", "claim_boundaries"}


class OracleError(RuntimeError):
    pass


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def check_sidecar(path: Path) -> None:
    sidecar = Path(f"{path}.sha256")
    expected = f"{digest(path.read_bytes())}  {path.name}\n"
    if not path.is_file() or not sidecar.is_file() or sidecar.read_text() != expected:
        raise OracleError(f"missing or stale sidecar: {path}")


def load_json() -> dict:
    check_sidecar(ORACLE)
    try:
        return json.loads(ORACLE.read_text(), object_pairs_hook=lambda pairs: _pairs(pairs))
    except (OSError, json.JSONDecodeError) as exc:
        raise OracleError(f"invalid oracle JSON: {exc}") from exc


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise OracleError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def words_digest(words: list[str]) -> str:
    try:
        return digest(b"".join(struct.pack("<I", int(word, 16)) for word in words))
    except (TypeError, ValueError, struct.error) as exc:
        raise OracleError("invalid Float32 word") from exc


def f32_word(value: object, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise OracleError(f"{label}: expected finite JSON number")
    try:
        return f"0x{struct.unpack('<I', struct.pack('<f', float(value)))[0]:08x}"
    except (OverflowError, struct.error) as exc:
        raise OracleError(f"{label}: outside Float32 range") from exc


def validate_source_file(root: Path = ROOT) -> bytes:
    source_path = root / SOURCE
    try:
        payload = source_path.read_bytes()
    except OSError as exc:
        raise OracleError(f"local GLSL source bytes drift: {source_path}") from exc
    if len(payload) != 8117 or digest(payload) != SOURCE_SHA:
        raise OracleError("local GLSL source bytes drift")
    return payload


def _exact_case(case: dict, expected: tuple) -> None:
    (name, width, height, phase_a, phase_b, mode, map_source, wrap, intensity,
     smoothing, aberration, antialias, tile_offset, full_resolution) = expected
    required = {"name", "width", "height", "phaseA", "phaseB", "mode", "mapSource", "wrap", "intensity", "smoothing", "aberration", "antialias", "tileOffset", "fullResolution", "repeat_exact", "input_immutable", "expected"}
    if set(case) != required:
        raise OracleError(f"case {case.get('name')}: control fields mismatch")
    if tuple(case[key] for key in ("name", "width", "height", "phaseA", "phaseB", "mode", "mapSource", "wrap", "intensity", "smoothing", "aberration", "antialias", "tileOffset", "fullResolution")) != (name, width, height, phase_a, phase_b, mode, map_source, wrap, intensity, smoothing, aberration, antialias, tile_offset, full_resolution):
        raise OracleError(f"case {name}: source-bound controls mismatch")
    for key in ("width", "height", "phaseA", "phaseB", "mode", "mapSource", "wrap", "intensity", "smoothing", "aberration"):
        if type(case[key]) is not int:
            raise OracleError(f"case {name}: {key} must be an integer")
    if width <= 0 or height <= 0 or phase_a < 0 or phase_b < 0 or mode not in (0, 1, 2) or map_source not in (0, 1) or wrap not in (0, 1, 2) or intensity < 0 or smoothing < 0 or aberration < 0:
        raise OracleError(f"case {name}: control range")
    if type(antialias) is not bool or type(case["repeat_exact"]) is not bool or type(case["input_immutable"]) is not bool or not case["repeat_exact"] or not case["input_immutable"]:
        raise OracleError(f"case {name}: runtime control flags")
    for key, values in (("tileOffset", tile_offset), ("fullResolution", full_resolution)):
        if type(values) is not list or len(values) != 2:
            raise OracleError(f"case {name}: {key} must be a two-element array")
        for index, value in enumerate(values):
            f32_word(value, f"case {name} {key}[{index}]")
    if full_resolution[0] <= 0 or full_resolution[1] <= 0:
        raise OracleError(f"case {name}: fullResolution range")
    expected = case["expected"]
    if not isinstance(expected, dict) or set(expected) != {"f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"}:
        raise OracleError(f"case {name}: expected payload fields mismatch")


def validate(doc: dict) -> None:
    if not isinstance(doc, dict):
        raise OracleError("document must be an object")
    if doc.get("schema") != SCHEMA or doc.get("schema_version") != 1 or doc.get("program_key") != KEY:
        raise OracleError("schema or program identity mismatch")
    if set(doc) != TOP_LEVEL_FIELDS:
        raise OracleError("document fields mismatch")
    if doc.get("effect_key") != "mixer/distortion" or doc.get("corpus_revision") != "a024dc3a960cc44af454abc7aebce50456c194e6" or doc.get("upstream_revision") != "117a236679d1db3ab8f0e278230ece277b57564c":
        raise OracleError("revision provenance mismatch")
    if doc.get("runtime_binding_names") != EXPECTED_BINDING_NAMES or doc.get("runtime_binding_abi") != EXPECTED_RUNTIME_ABI or doc.get("source_uniform_abi") != EXPECTED_SOURCE_ABI:
        raise OracleError("runtime/source binding ABI mismatch")
    factory = doc.get("factory", {})
    if not isinstance(factory, dict) or set(factory) != {"name", "text_sha256", "public_factory_is_canonical_identity", "adapter_own_key"} or factory.get("name") != "canonicalFactory194" or factory.get("text_sha256") != FACTORY_SHA or factory.get("public_factory_is_canonical_identity") is not True or factory.get("adapter_own_key") is not False:
        raise OracleError("canonical factory provenance mismatch")
    provenance = doc.get("provenance", {})
    if not isinstance(provenance, dict) or set(provenance) != {"source", "cpu_snapshot"}:
        raise OracleError("provenance fields mismatch")
    source = provenance.get("source", {})
    if not isinstance(source, dict) or set(source) != {"relative_path", "bytes", "sha256"} or source.get("relative_path") != SOURCE or type(source.get("bytes")) is not int or source.get("bytes") != 8117 or source.get("sha256") != SOURCE_SHA:
        raise OracleError("source provenance mismatch")
    validate_source_file()
    snapshot = provenance.get("cpu_snapshot", {})
    expected_closure = [{"relative_path": relative, "sha256": sha256} for relative, sha256 in EXPECTED_CLOSURE]
    if (not isinstance(snapshot, dict)
            or set(snapshot) != {"immutable_snapshot", "realpath_containment_checked", "live_checkout_rejected", "import_closure", "closure_cardinality"}
            or not all(snapshot.get(key) is True for key in ("immutable_snapshot", "realpath_containment_checked", "live_checkout_rejected"))
            or snapshot.get("closure_cardinality") != len(expected_closure)
            or snapshot.get("import_closure") != expected_closure):
        raise OracleError("snapshot safety flags missing")
    comparer = doc.get("comparer_self_tests", {})
    if not isinstance(comparer, dict) or set(comparer) != {"good", "dimensions_before_access", "f32_count", "rgba8_count", "signed_zero", "nan_payload", "rgba_mismatch", "input_mutation_rejected"} or not all(comparer.get(key) is True for key in ("good", "dimensions_before_access", "f32_count", "rgba8_count", "signed_zero", "nan_payload", "rgba_mismatch", "input_mutation_rejected")):
        raise OracleError("comparer self-test failure")
    cases = doc.get("render_cases")
    if not isinstance(cases, list) or len(cases) != 6 or any(not isinstance(case, dict) for case in cases) or len({case.get("name") for case in cases}) != 6:
        raise OracleError("render case census mismatch")
    for case, frozen in zip(cases, EXPECTED_CASE_CONTROLS):
        _exact_case(case, frozen)
        words = case.get("expected", {}).get("f32_words_le")
        rgba = case.get("expected", {}).get("rgba8_bytes")
        width, height = case.get("width"), case.get("height")
        if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
            raise OracleError("invalid case dimensions")
        if not isinstance(words, list) or len(words) != width * height * 4 or any(not isinstance(word, str) or not HEX.fullmatch(word) for word in words):
            raise OracleError(f"invalid Float32 words: {case.get('name')}")
        if case["expected"].get("f32_sha256") != words_digest(words):
            raise OracleError(f"Float32 digest mismatch: {case.get('name')}")
        if not isinstance(rgba, list) or len(rgba) != width * height * 4 or any(type(value) is not int or not 0 <= value <= 255 for value in rgba):
            raise OracleError(f"invalid RGBA8 bytes: {case.get('name')}")
        if case["expected"].get("rgba8_sha256") != digest(bytes(rgba)):
            raise OracleError(f"RGBA8 digest mismatch: {case.get('name')}")
    mutations = doc.get("mutation_ledger")
    if not isinstance(mutations, list) or len(mutations) != 3 or any(not isinstance(item, dict) for item in mutations) or not isinstance(doc.get("mutation_anchor_cardinality"), dict) or doc.get("mutation_anchor_cardinality", {}).get("total") != 3:
        raise OracleError("mutation census mismatch")
    if doc.get("mutation_anchor_cardinality") != {"total": 3, "anchors": {item["name"]: 1 for item in mutations}}:
        raise OracleError("mutation anchor cardinality mismatch")
    for mutation, frozen in zip(mutations, EXPECTED_MUTATIONS):
        required_mutation = {"name", "anchor", "anchor_sha256", "replacement", "replacement_sha256", "mutated_factory_sha256", "independent", "results", "witnesses"}
        if set(mutation) != required_mutation or mutation.get("independent") is not True or not isinstance(mutation.get("results"), list) or not isinstance(mutation.get("witnesses"), list):
            raise OracleError(f"mutation witness missing: {mutation.get('name')}")
        if len(mutation["results"]) != 2 or any(not isinstance(result, dict) for result in mutation["results"]):
            raise OracleError(f"mutation result malformed: {mutation.get('name')}")
        if any(set(result) != {"case", "exact", "changed_float32_lanes", "changed_rgba8_bytes"} or type(result["exact"]) is not bool or type(result["changed_float32_lanes"]) is not int or type(result["changed_rgba8_bytes"]) is not int for result in mutation["results"]):
            raise OracleError(f"mutation result malformed: {mutation.get('name')}")
        signature = (
            mutation["name"], mutation["anchor"], mutation["replacement"],
            mutation["anchor_sha256"], mutation["replacement_sha256"],
            mutation["mutated_factory_sha256"], tuple(mutation["witnesses"]),
            tuple((result["case"], result["changed_float32_lanes"],
                   result["changed_rgba8_bytes"], result["exact"])
                  for result in mutation["results"]),
        )
        if signature != frozen:
            raise OracleError(f"mutation authority pin mismatch: {mutation.get('name')}")
        if digest(mutation["anchor"].encode()) != mutation["anchor_sha256"] or digest(mutation["replacement"].encode()) != mutation["replacement_sha256"] or not re.fullmatch(r"[0-9a-f]{64}", mutation["anchor_sha256"]) or not re.fullmatch(r"[0-9a-f]{64}", mutation["replacement_sha256"]) or not re.fullmatch(r"[0-9a-f]{64}", mutation["mutated_factory_sha256"]):
            raise OracleError(f"mutation provenance mismatch: {mutation.get('name')}")
        if not isinstance(mutation["witnesses"], list) or len(mutation["witnesses"]) != 2 or any(not isinstance(item, str) for item in mutation["witnesses"]):
            raise OracleError(f"mutation witnesses malformed: {mutation.get('name')}")
        if [result.get("case") for result in mutation["results"]] != mutation["witnesses"]:
            raise OracleError(f"mutation witness order mismatch: {mutation.get('name')}")
        if any(type(result.get("changed_float32_lanes")) is not int or type(result.get("changed_rgba8_bytes")) is not int or result["changed_float32_lanes"] <= 0 or result["changed_rgba8_bytes"] <= 0 for result in mutation["results"]):
            raise OracleError(f"mutation has no pixel witness: {mutation.get('name')}")
    claim = doc.get("claim_boundaries", {})
    if not isinstance(claim, dict) or claim != EXPECTED_CLAIM_BOUNDARIES or claim.get("canonical_factory_only") is not True or claim.get("typed_slice_landing") is not False or claim.get("shared_emitter_modified") is not False:
        raise OracleError("claim boundary mismatch")


def render(doc: dict, oracle_sha256: str | None = None) -> bytes:
    oracle_sha256 = oracle_sha256 or digest(ORACLE.read_bytes())
    lines = ["#pragma once", "#include <array>", "#include <cstdint>", "#include <string_view>", "", "namespace distortion_oracle {"]
    lines += [f'inline constexpr std::string_view kSchema = "{SCHEMA}";', f'inline constexpr std::string_view kProgramKey = "{KEY}";', f'inline constexpr std::string_view kOracleJsonSha256 = "{oracle_sha256}";', 'inline constexpr std::string_view kOracleSha256 = kOracleJsonSha256;', f'inline constexpr std::string_view kFactoryTextSha256 = "{FACTORY_SHA}";', 'inline constexpr std::string_view kFactorySha256 = kFactoryTextSha256;', f'inline constexpr std::string_view kSourceSha256 = "{SOURCE_SHA}";', 'inline constexpr std::uint32_t kSourceBytes = 8117U;', f'inline constexpr std::string_view kSourceRelativePath = "{SOURCE}";', "struct ImportClosureEntry { std::string_view relativePath; std::string_view sha256; };", f"inline constexpr std::uint32_t kImportClosureCardinality = {len(EXPECTED_CLOSURE)}U;", f"inline constexpr std::array<ImportClosureEntry, {len(EXPECTED_CLOSURE)}> kImportClosure = {{"]
    lines.extend(f'  ImportClosureEntry{{"{relative}", "{sha256}"}},' for relative, sha256 in EXPECTED_CLOSURE)
    lines += ["};", "struct Float32Word { std::uint32_t bits; };", "struct Vec2Float32 { Float32Word x; Float32Word y; };", "struct CaseControls { std::uint32_t phaseA; std::uint32_t phaseB; std::int32_t mode; std::int32_t mapSource; std::int32_t wrap; Float32Word intensity; Float32Word smoothing; Float32Word aberration; bool antialias; Vec2Float32 tileOffset; Vec2Float32 fullResolution; };", "struct RuntimeBinding { std::string_view name; std::string_view runtimeAbi; std::string_view sourceAbi; };", ""]
    lines.append(f"inline constexpr std::array<RuntimeBinding, {len(EXPECTED_BINDING_NAMES)}> kRuntimeBindings = {{")
    for name in EXPECTED_BINDING_NAMES:
        lines.append(f'  RuntimeBinding{{"{name}", "{EXPECTED_RUNTIME_ABI[name]}", "{EXPECTED_SOURCE_ABI[name]}"}},')
    lines += ["};", "struct CaseSummary { std::string_view name; std::uint32_t width; std::uint32_t height; std::string_view f32_sha256; std::string_view rgba8_sha256; CaseControls controls; bool repeat_exact; bool input_immutable; };", ""]
    summaries = []
    for index, case in enumerate(doc["render_cases"]):
        expected = case["expected"]
        controls = [case["phaseA"], case["phaseB"], case["mode"], case["mapSource"], case["wrap"]]
        float_words = [f32_word(case["intensity"], "intensity"), f32_word(case["smoothing"], "smoothing"), f32_word(case["aberration"], "aberration")]
        tile_words = [f32_word(value, "tileOffset") for value in case["tileOffset"]]
        full_words = [f32_word(value, "fullResolution") for value in case["fullResolution"]]
        lines.append(f'inline constexpr CaseControls kCase{index}Controls{{{controls[0]}U, {controls[1]}U, {controls[2]}, {controls[3]}, {controls[4]}, Float32Word{{{float_words[0]}}}, Float32Word{{{float_words[1]}}}, Float32Word{{{float_words[2]}}}, {str(case["antialias"]).lower()}, Vec2Float32{{Float32Word{{{tile_words[0]}}}, Float32Word{{{tile_words[1]}}}}}, Vec2Float32{{Float32Word{{{full_words[0]}}}, Float32Word{{{full_words[1]}}}}}}};')
        lines.append(f"inline constexpr std::array<std::uint32_t, {len(expected['f32_words_le'])}> kCase{index}F32 = {{{', '.join(expected['f32_words_le'])}}};")
        lines.append(f"inline constexpr std::array<std::uint8_t, {len(expected['rgba8_bytes'])}> kCase{index}Rgba8 = {{{', '.join(str(x) for x in expected['rgba8_bytes'])}}};")
        summaries.append(f'  CaseSummary{{"{case["name"]}", {case["width"]}U, {case["height"]}U, "{expected["f32_sha256"]}", "{expected["rgba8_sha256"]}", kCase{index}Controls, {str(case["repeat_exact"]).lower()}, {str(case["input_immutable"]).lower()}}}')
    lines += ["", f"inline constexpr std::array<CaseSummary, {len(summaries)}> kCases = {{", ",\n".join(summaries), "};"]
    mutation_rows = []
    lines += ["", "struct MutationResult { std::string_view caseName; std::uint32_t changedFloat32Lanes; std::uint32_t changedRgba8Bytes; bool exact; };", "struct MutationSummary { std::string_view name; std::string_view anchor; std::string_view replacement; std::string_view anchorSha256; std::string_view replacementSha256; std::string_view mutatedFactorySha256; std::array<std::string_view, 2> witnessCases; std::array<MutationResult, 2> results; };", ""]
    for mutation in doc["mutation_ledger"]:
        results = ", ".join(f'MutationResult{{"{row["case"]}", {row["changed_float32_lanes"]}U, {row["changed_rgba8_bytes"]}U, false}}' for row in mutation["results"])
        witnesses = ", ".join(f'"{value}"' for value in mutation["witnesses"])
        mutation_rows.append(f'  MutationSummary{{"{mutation["name"]}", "{mutation["anchor"]}", "{mutation["replacement"]}", "{mutation["anchor_sha256"]}", "{mutation["replacement_sha256"]}", "{mutation["mutated_factory_sha256"]}", {{{witnesses}}}, {{{results}}}}}')
    lines += [f"inline constexpr std::array<MutationSummary, {len(mutation_rows)}> kMutations = {{", ",\n".join(mutation_rows), "};", 'inline constexpr std::string_view kFrontendBlocker = "sampler-parameter:calculateNormal:26:1-72:2";', "}  // namespace distortion_oracle", ""]
    return "\n".join(lines).encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if sum((args.write, args.check, args.self_test)) != 1:
        parser.error("choose exactly one of --write, --check, or --self-test")
    check_sidecar(REPORT)
    document = load_json()
    validate(document)
    output = render(document)
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(output)
        Path(f"{OUTPUT}.sha256").write_text(f"{digest(output)}  {OUTPUT.name}\n")
        print("distortion native oracle include written")
    elif args.self_test:
        checks = []
        for label, mutate in (
                ("mutation", lambda d: d["mutation_ledger"][0].__setitem__("independent", False)),
                ("closure", lambda d: d["provenance"]["cpu_snapshot"]["import_closure"].pop()),
                ("closure-path", lambda d: d["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__("relative_path", "../escaped.js")),
                ("comparer", lambda d: d["comparer_self_tests"].__setitem__("rgba_mismatch", False)),
        ):
            forged = json.loads(json.dumps(document))
            mutate(forged)
            try:
                validate(forged)
            except OracleError:
                checks.append((label, True))
            else:
                checks.append((label, False))
        for label, ok in checks:
            print(f"  [{'ok' if ok else 'FAIL'}] {label} forge rejected")
        if not all(ok for _, ok in checks):
            raise OracleError("distortion self-test accepted a forged document")
        print(f"strict schema, provenance, comparer, and mutation self-tests verified ({len(checks)}/{len(checks)})")
    else:
        check_sidecar(OUTPUT)
        if OUTPUT.read_bytes() != output:
            raise OracleError("generated include drift")
        print("distortion native oracle include check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
