#!/usr/bin/env python3
"""Materialize the checked Kaleido187 canonical oracle include.

The JSON is the only source of expected pixels.  This materializer is strict:
schema, provenance, sidecars, dimensions, counts, words, bytes, duplicate
keys, and every nested field are checked before any C++ is emitted.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import sys
from typing import Any


REPOSITORY = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = REPOSITORY / "docs/port-engineering/kaleido-parity"
ORACLE = PACKAGE / "kaleido187-oracles.json"
GENERATOR = PACKAGE / "kaleido187_oracle_generator.mjs"
REPORT = PACKAGE / "kaleido187-oracle-report.md"
TOOL = pathlib.Path(__file__).resolve()
TARGET = REPOSITORY / "tests/oracles/kaleido187_expected.inc"
SCHEMA = "noisemaker-for-cpp.kaleido187.pixel-parity.v1"
PROGRAM_KEY = "classicNoisedeck/kaleido:kaleido"
EFFECT_KEY = "classicNoisedeck/kaleido"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
FACTORY_TEXT_SHA256 = "4ab626fda5e91e7f89b93c9d863cda497b85d79239183499785c03607cce19a3"
SOURCE_SHA256 = "3a155a9bf64f9e700dd66a77c4195df113d9e85228bde56b1cf410944aaeb8b9"
ORACLE_AUTHORITY = "unmodified public canonicalFactory9 from the immutable noisemaker-for-cpu snapshot through bindCanonicalKernel/GlslCpuRuntime/runPass; no C++ output participates"
PINNED_CPU_FILES = {
    "canonical_kernels": ("src/effects/generated/canonical-kernels.js", "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe"),
    "public_catalog": ("src/effects/catalog.js", "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4"),
    "glsl_kernel": ("src/csl/glsl-kernel.js", "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa"),
    "glsl_runtime": ("src/csl/glsl-runtime.js", "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072"),
    "pass_runner": ("src/runtime/pass-runner.js", "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa"),
    "surface": ("src/runtime/surface.js", "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59"),
}
EXPECTED_IMPORT_CLOSURE = {
    "src/csl/glsl-kernel.js": "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa",
    "src/csl/glsl-runtime.js": "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072",
    "src/csl/runtime.js": "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee",
    "src/effects/adapters/bit-effects.js": "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7",
    "src/effects/adapters/crt.js": "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc",
    "src/effects/adapters/f32-color.js": "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046",
    "src/effects/adapters/fractal.js": "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29",
    "src/effects/adapters/index.js": "40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267",
    "src/effects/adapters/julia.js": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
    "src/effects/adapters/median.js": "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583",
    "src/effects/adapters/palette.js": "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452",
    "src/effects/adapters/snow.js": "202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366",
    "src/effects/catalog.js": "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4",
    "src/effects/definition.js": "fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02",
    "src/effects/generated/canonical-adapter-data.js": "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab",
    "src/effects/generated/canonical-kernels.js": "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe",
    "src/effects/generated/kernels.js": "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01",
    "src/effects/generated/upstream-snapshot.js": "e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090",
    "src/effects/registry.js": "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618",
    "src/runtime/pass-runner.js": "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa",
    "src/runtime/sampler.js": "1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328",
    "src/runtime/surface.js": "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
}
TABLE_NAMES = ("emboss", "sharpen", "blur", "edge", "edge2")
TABLE_VALUES = {
    "emboss": [-2, -1, 0, -1, 1, 1, 0, 1, 2],
    "sharpen": [-1, 0, -1, 0, 5, 0, -1, 0, -1],
    "blur": [1, 2, 1, 2, 4, 2, 1, 2, 1],
    "edge": [-1, -1, -1, -1, 8, -1, -1, -1, -1],
    "edge2": [-1, 0, -1, 0, 4, 0, -1, 0, -1],
}
TABLE_OCCURRENCES = {"emboss": 11, "sharpen": 11, "blur": 11, "edge": 10, "edge2": 12}
BINDING_NAMES = ["inputTex", "resolution", "tileOffset", "fullResolution", "time", "wrap", "seed", "speed", "loopScale", "kaleido", "effectWidth"]
RUNTIME_BINDING_ABI = {"inputTex": "sampler2D", "resolution": "Vec2", "tileOffset": "Vec2", "fullResolution": "Vec2", "time": "number", "wrap": "bool", "seed": "int32", "speed": "number", "loopScale": "number", "kaleido": "number", "effectWidth": "number"}
SOURCE_UNIFORM_ABI = {"inputTex": "sampler2D", "resolution": "vec2", "tileOffset": "vec2", "fullResolution": "vec2", "time": "float", "wrap": "bool", "seed": "int", "speed": "float", "loopScale": "float", "kaleido": "float", "effectWidth": "float"}
CANONICAL_RETURNED_CATEGORIES = {"inputTex": "Surface", "resolution": "Float32Array[2]", "tileOffset": "Float32Array[2]", "fullResolution": "Float32Array[2]", "time": "number", "wrap": "boolean", "seed": "number", "speed": "number", "loopScale": "number", "kaleido": "number", "effectWidth": "number"}
EXPECTED_MUTANT_NAMES = ("kaleido-sides-plus-one", "wrap-arm-inverted", "time-sign-flipped", "speed-sign-flipped")
EXPECTED_MUTATION_COUNTS = {
    "kaleido-sides-plus-one": ((26, 26), (9, 9), (30, 30), (0, 0)),
    "wrap-arm-inverted": ((0, 0), (33, 33), (0, 0), (48, 48)),
    "time-sign-flipped": ((30, 30), (36, 36), (0, 0), (0, 0)),
    "speed-sign-flipped": ((0, 0), (0, 0), (42, 42), (36, 36)),
}
EXPECTED_CASE_NAMES = ("sides-three-mirror", "sides-seven-mirror", "wrap-floor-repeat", "time-speed-live")
WORD = re.compile(r"^0x[0-9a-f]{8}$")


class OracleError(RuntimeError):
    pass


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sidecar_text(path: pathlib.Path, payload: bytes) -> str:
    return f"{digest(payload)}  {path.name}\n"


def verify_sidecar(path: pathlib.Path) -> bytes:
    if not path.is_file() or not path.with_name(path.name + ".sha256").is_file():
        raise OracleError(f"missing checked asset or sidecar: {path.name}")
    payload = path.read_bytes()
    if path.with_name(path.name + ".sha256").read_text() != sidecar_text(path, payload):
        raise OracleError(f"checksum sidecar drift: {path.name}")
    return payload


def pairs(pairs_: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs_:
        if key in out:
            raise OracleError(f"duplicate JSON field: {key}")
        out[key] = value
    return out


def require_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OracleError(f"{label}: expected object")
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise OracleError(f"{label}: missing field(s): {sorted(missing)}")
    if extra:
        raise OracleError(f"{label}: extra field(s): {sorted(extra)}")
    return value


def reject_absolute(value: Any, label: str = "document") -> None:
    if isinstance(value, str):
        if re.match(r"^(?:[A-Za-z]:[\\/]|\\\\|/)", value) or re.search(r"(?:^|[\\/])(?:Users|private|tmp|home)[\\/]", value):
            raise OracleError(f"{label}: absolute-looking string")
    elif isinstance(value, list):
        for index, entry in enumerate(value):
            reject_absolute(entry, f"{label}[{index}]")
    elif isinstance(value, dict):
        for key, entry in value.items():
            reject_absolute(entry, f"{label}.{key}")


def require_word_array(value: Any, count: int, label: str) -> list[str]:
    if not isinstance(value, list) or len(value) != count:
        raise OracleError(f"{label}: expected exactly {count} words")
    if any(not isinstance(word, str) or not WORD.fullmatch(word) for word in value):
        raise OracleError(f"{label}: malformed float32 word")
    return value


def require_byte_array(value: Any, count: int, label: str) -> list[int]:
    if not isinstance(value, list) or len(value) != count:
        raise OracleError(f"{label}: expected exactly {count} bytes")
    if any(not isinstance(byte, int) or isinstance(byte, bool) or not 0 <= byte <= 255 for byte in value):
        raise OracleError(f"{label}: malformed RGBA8 byte")
    return value


def require_int(value: Any, label: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise OracleError(f"{label}: expected integer")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise OracleError(f"{label}: integer out of range")
    return value


def require_uint32(value: Any, label: str) -> int:
    return require_int(value, label, minimum=0, maximum=0xFFFFFFFF)


def require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise OracleError(f"{label}: malformed SHA-256")
    return value


def validate_document(doc: Any) -> dict[str, Any]:
    reject_absolute(doc)
    top = require_keys(doc, {
        "schema", "schema_version", "program_key", "effect_key", "runtime_key", "corpus_revision", "upstream_revision", "defines",
        "runtime_binding_names", "runtime_binding_abi", "compile_time_defines_are_not_bindings", "defines_are_runtime_bindings_in_javascript",
        "factory", "oracle_authority", "mutable_global_contracts", "exactness_contract", "provenance", "canonical_binding_contract", "native_expected_rejection", "abi_rejection_contract",
        "comparer_self_tests", "coverage_axes", "render_cases", "control_group", "kernel_liveness_census", "mutation_ledger",
        "write_only_tables_axis", "xor_sites_axis", "binding_liveness_census", "claim_boundaries",
    }, "document")
    if top["schema"] != SCHEMA or require_int(top["schema_version"], "schema_version") != 1:
        raise OracleError("Kaleido187 schema mismatch")
    if top["program_key"] != PROGRAM_KEY or top["runtime_key"] != PROGRAM_KEY or top["effect_key"] != EFFECT_KEY:
        raise OracleError("Kaleido187 program identity mismatch")
    if top["oracle_authority"] != ORACLE_AUTHORITY:
        raise OracleError("Kaleido187 oracle authority drift")
    if top["corpus_revision"] != CORPUS_REVISION or top["upstream_revision"] != "117a236679d1db3ab8f0e278230ece277b57564c":
        raise OracleError("Kaleido187 provenance revision mismatch")
    defines = require_keys(top["defines"], {"DIRECTION", "KERNEL", "LOOP_OFFSET", "METRIC"}, "defines")
    if any(require_int(defines[name], f"defines.{name}") != expected for name, expected in {"DIRECTION": 2, "KERNEL": 0, "LOOP_OFFSET": 10, "METRIC": 0}.items()):
        raise OracleError("Kaleido187 define mismatch")
    if top["runtime_binding_names"] != ["inputTex", "resolution", "tileOffset", "fullResolution", "time", "wrap", "seed", "speed", "loopScale", "kaleido", "effectWidth"] or top["compile_time_defines_are_not_bindings"] is not True or top["defines_are_runtime_bindings_in_javascript"] != "KERNEL is runtime-bound at zero for parity; omitted KERNEL is an explicit identity control. The typed port has no KERNEL binding.":
        raise OracleError("Kaleido187 binding census mismatch")
    if top["runtime_binding_abi"] != {"inputTex": "sampler2D", "resolution": "Vec2", "tileOffset": "Vec2", "fullResolution": "Vec2", "time": "number", "wrap": "bool", "seed": "int32", "speed": "number", "loopScale": "number", "kaleido": "number", "effectWidth": "number"}:
        raise OracleError("Kaleido187 binding ABI mismatch")
    factory = require_keys(top["factory"], {"name", "text_sha256", "public_factory_is_canonical_identity"}, "factory")
    if factory["name"] != "canonicalFactory9" or factory["text_sha256"] != FACTORY_TEXT_SHA256 or factory["public_factory_is_canonical_identity"] is not True:
        raise OracleError("Kaleido187 factory identity mismatch")
    exact = require_keys(top["exactness_contract"], {"float32", "rgba8", "tolerance", "comparison_order", "coordinates", "alpha"}, "exactness_contract")
    if exact != {
        "float32": "complete raw little-endian uint32 lane arrays; signed zero and NaN payloads significant",
        "rgba8": "complete independently captured canonical Surface.toRgba8 byte arrays",
        "tolerance": "none",
        "comparison_order": "dimensions, counts, every float32 word, every independent RGBA8 byte",
        "coordinates": "top-down Surface storage order",
        "alpha": "sampled alpha is exactly 1.0 in every input and output",
    }:
        raise OracleError("Kaleido187 exactness contract drift")
    abi = require_keys(top["abi_rejection_contract"], {"contract_type", "required_bindings", "source_interface", "status"}, "abi_rejection_contract")
    if abi != {
        "contract_type": "native expected-rejection preflight table",
        "required_bindings": BINDING_NAMES,
        "source_interface": "pinned Kaleido GLSL uniform declarations plus canonical createCanonicalBindings return surface",
        "status": "pending_shared_native_integration",
    }:
        raise OracleError("Kaleido187 native ABI contract drift")
    canonical = require_keys(top["canonical_binding_contract"], {"source_uniform_types", "returned_binding_keys", "returned_binding_categories", "acceptance_probe"}, "canonical_binding_contract")
    acceptance = require_keys(canonical["acceptance_probe"], {"inputTex_number_accepted", "wrap_number_accepted", "seed_fractional_number_accepted"}, "canonical_binding_contract.acceptance_probe")
    if canonical["source_uniform_types"] != SOURCE_UNIFORM_ABI or canonical["returned_binding_keys"] != BINDING_NAMES or canonical["returned_binding_categories"] != CANONICAL_RETURNED_CATEGORIES or acceptance != {"inputTex_number_accepted": True, "wrap_number_accepted": True, "seed_fractional_number_accepted": True}:
        raise OracleError("Kaleido187 canonical binding contract drift")
    native_rows = top["native_expected_rejection"]
    expected_native_variants = {
        "inputTex": ("sampler2D", "number", "1"), "resolution": ("vec2", "number", "1"), "tileOffset": ("vec2", "number", "1"), "fullResolution": ("vec2", "number", "1"),
        "time": ("float", "vec2", "[0, 0]"), "wrap": ("bool", "number", "1"), "seed": ("int", "number", "0.5"), "speed": ("float", "vec2", "[0, 0]"),
        "loopScale": ("float", "vec2", "[0, 0]"), "kaleido": ("float", "vec2", "[0, 0]"), "effectWidth": ("float", "vec2", "[0, 0]"),
    }
    if not isinstance(native_rows, list) or len(native_rows) != len(BINDING_NAMES):
        raise OracleError("Kaleido187 native ABI table row count drift")
    for index, binding_name in enumerate(BINDING_NAMES):
        row = require_keys(native_rows[index], {"binding_name", "authenticated_expected_abi_category", "native_wrong_variant", "native_wrong_value", "missing_case", "status"}, f"native_expected_rejection[{index}]")
        source_type, wrong_variant, wrong_value = expected_native_variants[binding_name]
        if row != {"binding_name": binding_name, "authenticated_expected_abi_category": source_type, "native_wrong_variant": wrong_variant, "native_wrong_value": wrong_value, "missing_case": f"missing {binding_name}", "status": "pending_shared_native_integration"}:
            raise OracleError(f"Kaleido187 native ABI row drift: {binding_name}")
    provenance = require_keys(top["provenance"], {"node_version", "generator", "native_include_generator", "cpu_snapshot", "source", "canonical_factory", "adapter_override_absent", "adapter_routed_keys", "corpus_adapter_keys", "corpus_adapter_source", "pinned_cpu_files"}, "provenance")
    if provenance["node_version"] != "v24.7.0" or provenance["corpus_adapter_source"] != "tools/glslcpp/check_corpus.py":
        raise OracleError("Kaleido187 authority runtime provenance drift")
    canonical_factory = require_keys(provenance["canonical_factory"], {"name", "text_sha256", "public_factory_is_canonical_identity"}, "provenance.canonical_factory")
    if canonical_factory != {"name": "canonicalFactory9", "text_sha256": FACTORY_TEXT_SHA256, "public_factory_is_canonical_identity": True}:
        raise OracleError("Kaleido187 canonical factory provenance drift")
    generator = require_keys(provenance["generator"], {"relative_path", "sha256"}, "provenance.generator")
    if generator["relative_path"] != "docs/port-engineering/kaleido-parity/kaleido187_oracle_generator.mjs" or generator["sha256"] != digest(GENERATOR.read_bytes()):
        raise OracleError("Kaleido187 generator provenance drift")
    native_generator = require_keys(provenance["native_include_generator"], {"relative_path", "sha256"}, "provenance.native_include_generator")
    if native_generator["relative_path"] != "tools/glslcpp/generate_kaleido_native_oracle_include.py" or native_generator["sha256"] != digest(TOOL.read_bytes()):
        raise OracleError("Kaleido187 materializer provenance drift")
    source = require_keys(provenance["source"], {"relative_path_from_noisemaker_for_cpp", "bytes", "sha256"}, "provenance.source")
    if source["bytes"] != 27567 or source["sha256"] != SOURCE_SHA256 or source["relative_path_from_noisemaker_for_cpp"] != "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/kaleido/kaleido.glsl":
        raise OracleError("Kaleido187 source provenance drift")
    snapshot = require_keys(provenance["cpu_snapshot"], {"argument", "immutable_snapshot", "live_checkout_rejected", "containment_checked", "import_closure"}, "provenance.cpu_snapshot")
    if snapshot["argument"] != "<immutable-cpu-snapshot-root>" or snapshot["immutable_snapshot"] is not True or snapshot["live_checkout_rejected"] is not True or snapshot["containment_checked"] is not True:
        raise OracleError("Kaleido187 snapshot lock drift")
    if not isinstance(snapshot["import_closure"], list) or len(snapshot["import_closure"]) != len(EXPECTED_IMPORT_CLOSURE):
        raise OracleError("Kaleido187 import closure missing")
    closure: dict[str, str] = {}
    for index, entry in enumerate(snapshot["import_closure"]):
        item = require_keys(entry, {"relative_path", "sha256"}, f"provenance.cpu_snapshot.import_closure[{index}]")
        require_sha(item["sha256"], f"import closure {index}")
        if not isinstance(item["relative_path"], str) or pathlib.PurePath(item["relative_path"]).is_absolute() or item["relative_path"] in closure:
            raise OracleError("Kaleido187 import closure has absolute path")
        closure[item["relative_path"]] = item["sha256"]
    if closure != EXPECTED_IMPORT_CLOSURE:
        raise OracleError("Kaleido187 import closure provenance mismatch")
    if provenance["adapter_override_absent"] is not True or PROGRAM_KEY in provenance["adapter_routed_keys"] or PROGRAM_KEY in provenance["corpus_adapter_keys"]:
        raise OracleError("Kaleido187 adapter routing drift")
    if provenance["adapter_routed_keys"] != [
        "classicNoisedeck/bitEffects:bitEffects", "classicNoisedeck/fractal:fractal", "filter/crt:crt",
        "filter/historicPalette:historicPalette", "filter/median:median", "filter/palette:palette",
        "filter/pixelSort:luminance", "filter/reindex:nmReindexApply", "filter/reindex:nmReindexStats",
        "filter/snow:snow", "synth/julia:julia",
    ] or provenance["corpus_adapter_keys"] != [
        "classicNoisedeck/fractal:fractal", "filter/historicPalette:historicPalette", "filter/palette:palette", "synth/julia:julia",
    ]:
        raise OracleError("Kaleido187 adapter census drift")
    pinned = provenance["pinned_cpu_files"]
    if not isinstance(pinned, dict) or set(pinned) != set(PINNED_CPU_FILES):
        raise OracleError("Kaleido187 pinned CPU-file census drift")
    for name, (relative, expected) in PINNED_CPU_FILES.items():
        item = require_keys(pinned[name], {"relative_path", "sha256"}, f"provenance.pinned_cpu_files.{name}")
        if item["relative_path"] != relative or item["sha256"] != expected:
            raise OracleError(f"Kaleido187 pinned CPU-file drift: {name}")
    coverage_axes = require_keys(top["coverage_axes"], {"kaleido_sides", "wrap", "time", "speed", "loopScale", "input_pattern", "route"}, "coverage_axes")
    if coverage_axes != {
        "kaleido_sides": [3, 5, 7, 9],
        "wrap": [False, True],
        "time": [0.25, 0.75, 1.5, 2],
        "speed": [10, 35, -25, 60],
        "loopScale": [1, 3, 8, 20],
        "input_pattern": "dyadic RGBA gradient",
        "route": "full only; tile-crop identity intentionally unclaimed",
    } or any(type(item) is not bool for item in coverage_axes["wrap"]):
        raise OracleError("Kaleido187 coverage axis drift")
    controls = require_keys(top["control_group"], {"repeatability", "input_immutability", "independent_output_storage", "public_direct_identity"}, "control_group")
    repeatability = require_keys(controls["repeatability"], {"case", "identical_float32", "identical_rgba8"}, "control_group.repeatability")
    immutability = require_keys(controls["input_immutability"], {"case", "unchanged"}, "control_group.input_immutability")
    independence = require_keys(controls["independent_output_storage"], {"case", "distinct_data_objects"}, "control_group.independent_output_storage")
    if controls["public_direct_identity"] is not True or repeatability["case"] != "sides-seven-mirror" or repeatability["identical_float32"] is not True or repeatability["identical_rgba8"] is not True or immutability["case"] != "sides-seven-mirror" or immutability["unchanged"] is not True or independence["case"] != "wrap-floor-repeat" or independence["distinct_data_objects"] is not True:
        raise OracleError("Kaleido187 control-group drift")
    liveness = require_keys(top["kernel_liveness_census"], {"probe_case", "omitted_vs_zero", "nonzero_kernel_with_effect_width", "zero_lanes_changed", "live_probe_changed_lanes"}, "kernel_liveness_census")
    if liveness != {"probe_case": "sides-three-mirror", "omitted_vs_zero": "identical", "nonzero_kernel_with_effect_width": "differs", "zero_lanes_changed": 0, "live_probe_changed_lanes": 60}:
        raise OracleError("Kaleido187 kernel liveness drift")
    claims = require_keys(top["claim_boundaries"], {"tables", "kernel", "tile_crop", "absolute_paths", "tolerance"}, "claim_boundaries")
    if claims != {
        "tables": "structural only",
        "kernel": "KERNEL=0 is the frozen corpus define; nonzero probe proves the JS channel exists but is not a parity case",
        "tile_crop": "no crop identity claim",
        "absolute_paths": "all provenance paths are stable repository-relative placeholders",
        "tolerance": "none",
    }:
        raise OracleError("Kaleido187 claim-boundary drift")
    comparer = require_keys(top["comparer_self_tests"], {"exact_words_and_bytes", "dimensions_before_access", "equal_rgba8_does_not_hide_word_mismatch", "signed_zero_and_nan_payloads_significant", "truncated_and_extra_arrays_rejected"}, "comparer_self_tests")
    if comparer != {"exact_words_and_bytes": True, "dimensions_before_access": True, "equal_rgba8_does_not_hide_word_mismatch": True, "signed_zero_and_nan_payloads_significant": True, "truncated_and_extra_arrays_rejected": True}:
        raise OracleError("Kaleido187 comparer self-test contract drift")
    xor_sites = require_keys(top["xor_sites_axis"], {"status", "loop_offset", "sites", "pixel_case"}, "xor_sites_axis")
    if xor_sites != {"status": "runtime-dead control", "loop_offset": 10, "sites": ["158:10", "159:10", "160:10"], "pixel_case": "not budgeted; structural carrier only"}:
        raise OracleError("Kaleido187 XOR-site semantic drift")
    binding_liveness = require_keys(top["binding_liveness_census"], {"live", "required_but_unread_or_zero", "abi"}, "binding_liveness_census")
    if binding_liveness != {"live": ["inputTex", "time", "wrap", "seed", "speed", "loopScale", "kaleido"], "required_but_unread_or_zero": ["resolution", "tileOffset", "fullResolution", "effectWidth"], "abi": RUNTIME_BINDING_ABI}:
        raise OracleError("Kaleido187 binding-liveness semantic drift")
    contracts = top["mutable_global_contracts"]
    if not isinstance(contracts, dict) or set(contracts) != set(TABLE_NAMES):
        raise OracleError("Kaleido187 mutable table census mismatch")
    for name in TABLE_NAMES:
        contract = require_keys(contracts[name], {"javascript_declaration", "glsl_type", "element_materialization", "numeric_contract", "native_element_type", "writer", "elements", "identifier_occurrence_census", "reads", "oracle_discriminable", "why_not_discriminable"}, f"mutable_global_contracts.{name}")
        expected_contract = {
            "javascript_declaration": f"var {name} = [0, 0, 0, 0, 0, 0, 0, 0, 0];",
            "glsl_type": "float[9], mutable, uninitialized",
            "element_materialization": "plain JS Array of Numbers, not Float32Array",
            "numeric_contract": "double, never narrowed to f32",
            "native_element_type": "double",
            "writer": "loadKernels called once per pixel from main and rewrites all nine elements",
            "elements": TABLE_VALUES[name],
            "identifier_occurrence_census": TABLE_OCCURRENCES[name],
            "reads": "none at accepted KERNEL=0 defines",
            "oracle_discriminable": False,
            "why_not_discriminable": "write-only at frozen defines; pixels are controls, not structural-carrier evidence",
        }
        if contract != expected_contract:
            raise OracleError(f"mutable_global_contracts.{name}: semantic drift")
    cases = top["render_cases"]
    if not isinstance(cases, list) or len(cases) < 3:
        raise OracleError("Kaleido187 carries too few render cases")
    case_names: list[str] = []
    for index, case in enumerate(cases):
        case = require_keys(case, {"name", "width", "height", "input", "expected", "bindings", "alpha_f32_word", "alpha_rgba8_byte"}, f"render_cases[{index}]")
        if case["name"] in case_names:
            raise OracleError("duplicate render case name")
        case_names.append(case["name"])
        if isinstance(case["width"], bool) or isinstance(case["height"], bool) or not isinstance(case["width"], int) or not isinstance(case["height"], int) or case["width"] <= 0 or case["height"] <= 0:
            raise OracleError(f"render_cases[{index}]: malformed dimensions")
        count = case["width"] * case["height"] * 4
        inp = require_keys(case["input"], {"width", "height", "f32_words_le", "f32_sha256"}, f"render_cases[{index}].input")
        if inp["width"] != case["width"] or inp["height"] != case["height"]:
            raise OracleError(f"render_cases[{index}].input: dimensions drift")
        words = require_word_array(inp["f32_words_le"], count, f"render_cases[{index}].input.f32_words_le")
        if require_sha(inp["f32_sha256"], "input digest") != digest(b"".join(int(word, 16).to_bytes(4, "little") for word in words)):
            raise OracleError(f"render_cases[{index}].input: digest mismatch")
        expected = require_keys(case["expected"], {"f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"}, f"render_cases[{index}].expected")
        expected_words = require_word_array(expected["f32_words_le"], count, f"render_cases[{index}].expected.f32_words_le")
        expected_bytes = require_byte_array(expected["rgba8_bytes"], count, f"render_cases[{index}].expected.rgba8_bytes")
        if require_sha(expected["f32_sha256"], "expected digest") != digest(b"".join(int(word, 16).to_bytes(4, "little") for word in expected_words)):
            raise OracleError(f"render_cases[{index}].expected: word digest mismatch")
        if require_sha(expected["rgba8_sha256"], "expected bytes digest") != digest(bytes(expected_bytes)):
            raise OracleError(f"render_cases[{index}].expected: byte digest mismatch")
        if any(expected_words[offset + 3] != "0x3f800000" or expected_bytes[offset + 3] != 255 for offset in range(0, count, 4)):
            raise OracleError(f"render_cases[{index}]: alpha mismatch")
        bindings = require_keys(case["bindings"], {"time", "seed", "speed", "loopScale", "kaleido", "effectWidth", "wrap"}, f"render_cases[{index}].bindings")
        for key in ("time", "speed", "loopScale", "kaleido", "effectWidth"):
            if not isinstance(bindings[key], str) or not WORD.fullmatch(bindings[key]):
                raise OracleError(f"render_cases[{index}].bindings.{key}: malformed word")
        if isinstance(bindings["seed"], bool) or not isinstance(bindings["seed"], int) or not -2147483648 <= bindings["seed"] <= 2147483647 or not isinstance(bindings["wrap"], bool):
            raise OracleError(f"render_cases[{index}].bindings: ABI type drift")
        if case["alpha_f32_word"] != "0x3f800000" or isinstance(case["alpha_rgba8_byte"], bool) or not isinstance(case["alpha_rgba8_byte"], int) or case["alpha_rgba8_byte"] != 255:
            raise OracleError(f"render_cases[{index}]: alpha contract drift")
    if repeatability["case"] not in case_names or immutability["case"] not in case_names or independence["case"] not in case_names or liveness["probe_case"] not in case_names:
        raise OracleError("Kaleido187 control references unknown case")
    require_uint32(liveness["zero_lanes_changed"], "kernel_liveness_census.zero_lanes_changed")
    require_uint32(liveness["live_probe_changed_lanes"], "kernel_liveness_census.live_probe_changed_lanes")
    ledger = top["mutation_ledger"]
    if not isinstance(ledger, list) or len(ledger) != len(EXPECTED_MUTANT_NAMES):
        raise OracleError("Kaleido187 mutation ledger set drift")
    if tuple(case_names) != EXPECTED_CASE_NAMES:
        raise OracleError("Kaleido187 render case order drift")
    for index, expected_name in enumerate(EXPECTED_MUTANT_NAMES):
        row = require_keys(ledger[index], {"name", "rows", "budgeted_as"}, f"mutation_ledger[{index}]")
        if row["name"] != expected_name or row["budgeted_as"] != "pixel witness" or not isinstance(row["rows"], list) or len(row["rows"]) != len(EXPECTED_CASE_NAMES):
            raise OracleError(f"mutation_ledger[{index}]: exact mutant set drift")
        expected_counts = EXPECTED_MUTATION_COUNTS[expected_name]
        witness_count = 0
        for row_index, item in enumerate(row["rows"]):
            item = require_keys(item, {"case", "differs", "changed_float32_lanes", "changed_rgba8_bytes"}, f"mutation_ledger[{index}].rows[{row_index}]")
            if item["case"] != EXPECTED_CASE_NAMES[row_index] or not isinstance(item["differs"], bool):
                raise OracleError(f"mutation_ledger[{index}]: case row order drift")
            lanes = require_uint32(item["changed_float32_lanes"], f"mutation_ledger[{index}].rows[{row_index}].changed_float32_lanes")
            bytes_changed = require_uint32(item["changed_rgba8_bytes"], f"mutation_ledger[{index}].rows[{row_index}].changed_rgba8_bytes")
            if (lanes, bytes_changed) != expected_counts[row_index] or item["differs"] is not (lanes > 0 or bytes_changed > 0):
                raise OracleError(f"mutation_ledger[{index}].rows[{row_index}]: frozen witness drift")
            case_data = cases[row_index]
            case_count = case_data["width"] * case_data["height"] * 4
            if lanes > case_count or bytes_changed > case_count:
                raise OracleError(f"mutation_ledger[{index}].rows[{row_index}]: witness count exceeds case")
            witness_count += int(item["differs"])
        if witness_count == 0:
            raise OracleError(f"mutation_ledger[{index}]: empty witness set")
    write_only = require_keys(top["write_only_tables_axis"], {"status", "element_count", "table_names", "oracle_discriminable", "rendered_mutant", "rendered_divergences", "claim"}, "write_only_tables_axis")
    divergences = require_keys(write_only["rendered_divergences"], {"float32_lanes", "rgba8_bytes"}, "write_only_tables_axis.rendered_divergences")
    if require_uint32(write_only["element_count"], "write_only_tables_axis.element_count") != 45 or write_only["table_names"] != list(TABLE_NAMES) or write_only["oracle_discriminable"] is not False or write_only["status"] != "measured structural control" or write_only["rendered_mutant"] != "table constants changed at accepted KERNEL=0 defines" or divergences != {"float32_lanes": 0, "rgba8_bytes": 0} or write_only["claim"] != "table values are write-only at accepted defines; pixel controls cannot carry the array ABI proof":
        raise OracleError("Kaleido187 write-only axis drift")
    return top


def load_oracle() -> tuple[dict[str, Any], str]:
    verify_sidecar(GENERATOR)
    verify_sidecar(REPORT)
    payload = verify_sidecar(ORACLE)
    try:
        document = json.loads(payload, object_pairs_hook=pairs)
    except (json.JSONDecodeError, OracleError) as error:
        raise OracleError(f"invalid Kaleido187 JSON: {error}") from error
    return validate_document(document), digest(payload)


def word_rows(words: list[str], per_row: int = 8) -> str:
    return "\n".join("    " + " ".join(f"{word}U," for word in words[start:start + per_row]) for start in range(0, len(words), per_row))


def byte_rows(values: list[int], per_row: int = 16) -> str:
    return "\n".join("    " + " ".join(f"{value}U," for value in values[start:start + per_row]) for start in range(0, len(values), per_row))


def render(doc: dict[str, Any], oracle_sha: str) -> str:
    out: list[str] = []
    add = out.append
    add("// Generated from the checked canonical JavaScript Kaleido187 oracle.")
    add("// C++ output never participates in these expected arrays.")
    add("#pragma once\n")
    add("namespace kaleido187_oracle {\n")
    add(f'inline constexpr std::string_view kOracleSha256 = "{oracle_sha}";')
    add(f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";')
    add(f'inline constexpr std::string_view kCorpusRevision = "{CORPUS_REVISION}";')
    add(f'inline constexpr std::string_view kFactoryTextSha256 = "{FACTORY_TEXT_SHA256}";\n')
    for index, case in enumerate(doc["render_cases"]):
        for label, values in (("Input", case["input"]["f32_words_le"]), ("Expected", case["expected"]["f32_words_le"])):
            add(f"inline constexpr std::array<std::uint32_t, {len(values)}> kCase{index}{label}Words{{{{")
            add(word_rows(values)); add("}};\n")
        values = case["expected"]["rgba8_bytes"]
        add(f"inline constexpr std::array<std::uint8_t, {len(values)}> kCase{index}ExpectedRgba8{{{{")
        add(byte_rows(values)); add("}};\n")
    add("struct CaseView {")
    add("  std::string_view name; std::size_t width; std::size_t height;")
    add("  std::string_view input_f32_sha256; std::string_view expected_f32_sha256; std::string_view expected_rgba8_sha256;")
    add("  std::span<const std::uint32_t> input_words; std::span<const std::uint32_t> expected_words; std::span<const std::uint8_t> expected_rgba8;")
    add("  std::uint32_t time_word; std::int32_t seed; std::uint32_t speed_word; std::uint32_t loop_scale_word; std::uint32_t kaleido_word; std::uint32_t effect_width_word; bool wrap;")
    add("};\n")
    add(f"inline constexpr std::array<CaseView, {len(doc['render_cases'])}> kCases{{{{")
    for index, case in enumerate(doc["render_cases"]):
        bindings = case["bindings"]
        add(f'  CaseView{{"{case["name"]}", {case["width"]}U, {case["height"]}U, "{case["input"]["f32_sha256"]}", "{case["expected"]["f32_sha256"]}", "{case["expected"]["rgba8_sha256"]}", kCase{index}InputWords, kCase{index}ExpectedWords, kCase{index}ExpectedRgba8, {int(bindings["time"], 16)}U, {bindings["seed"]}, {int(bindings["speed"], 16)}U, {int(bindings["loopScale"], 16)}U, {int(bindings["kaleido"], 16)}U, {int(bindings["effectWidth"], 16)}U, {str(bindings["wrap"]).lower()}}},')
    add("}};\n")
    add("struct MutantWitnessView { std::string_view mutant; std::string_view case_name; bool differs; std::size_t changed_float32_lanes; std::size_t changed_rgba8_bytes; };\n")
    witness_rows = [(entry["name"], row) for entry in doc["mutation_ledger"] for row in entry["rows"]]
    add(f"inline constexpr std::array<MutantWitnessView, {len(witness_rows)}> kMutantWitnesses{{{{")
    for mutant, row in witness_rows:
        add(f'  MutantWitnessView{{"{mutant}", "{row["case"]}", {str(row["differs"]).lower()}, {row["changed_float32_lanes"]}U, {row["changed_rgba8_bytes"]}U}},')
    add("}};\n")
    add("struct ControlView { std::string_view name; bool identical; };\n")
    add("inline constexpr std::array<ControlView, 4> kControls{{")
    add('  ControlView{"repeatability", true}, ControlView{"input-immutability", true},')
    add('  ControlView{"independent-output-storage", true}, ControlView{"KERNEL-omitted-vs-zero", true},')
    add("}};\n")
    add("enum class NativeExpectedAbiCategory { Sampler2D, Vec2, Float, Bool, Int32 };\n")
    add("struct NativeExpectedRejectionView { std::string_view binding_name; NativeExpectedAbiCategory expected_category; std::string_view wrong_variant; std::string_view wrong_value; std::string_view missing_case; std::string_view status; };\n")
    category_enums = {"sampler2D": "Sampler2D", "vec2": "Vec2", "float": "Float", "bool": "Bool", "int": "Int32"}
    add(f"inline constexpr std::array<NativeExpectedRejectionView, {len(doc['native_expected_rejection'])}> kNativeExpectedRejections{{{{")
    for row in doc["native_expected_rejection"]:
        add(f'  NativeExpectedRejectionView{{"{row["binding_name"]}", NativeExpectedAbiCategory::{category_enums[row["authenticated_expected_abi_category"]]}, "{row["native_wrong_variant"]}", "{row["native_wrong_value"]}", "{row["missing_case"]}", "{row["status"]}"}},')
    add("}};\n")
    add("inline constexpr std::size_t kKernelLiveProbeChangedLanes = " + str(doc["kernel_liveness_census"]["live_probe_changed_lanes"]) + "U;")
    add("inline constexpr std::uint32_t kAlphaWord = 0x3f800000U;\ninline constexpr std::uint8_t kAlphaByte = 255U;\n")
    add("}  // namespace kaleido187_oracle\n")
    return "\n".join(out)


def self_test() -> int:
    checks: list[tuple[str, bool]] = []
    try:
        doc, oracle_sha = load_oracle()
        checks.append(("schema and provenance load", True))
        checks.append(("rendered include has namespace", "namespace kaleido187_oracle" in render(doc, oracle_sha)))
        checks.append(("all render cases have exact counts", all(len(c["expected"]["f32_words_le"]) == c["width"] * c["height"] * 4 for c in doc["render_cases"])))
        checks.append(("table axis is non-discriminable", doc["write_only_tables_axis"]["oracle_discriminable"] is False))
        checks.append(("alpha contract is exact", all(c["alpha_f32_word"] == "0x3f800000" and c["alpha_rgba8_byte"] == 255 for c in doc["render_cases"])))
        checks.append(("mutation rows cover each case", all(len(e["rows"]) == len(doc["render_cases"]) for e in doc["mutation_ledger"])))
        broken = copy.deepcopy(doc); broken["render_cases"][0]["expected"]["f32_words_le"].pop()
        try: validate_document(broken); checks.append(("truncated arrays rejected", False))
        except OracleError: checks.append(("truncated arrays rejected", True))
        broken = copy.deepcopy(doc); broken["write_only_tables_axis"]["oracle_discriminable"] = True
        try: validate_document(broken); checks.append(("table mutant claim rejected", False))
        except OracleError: checks.append(("table mutant claim rejected", True))
        broken = copy.deepcopy(doc); broken["provenance"]["cpu_snapshot"]["argument"] = "/private/foreign"
        try: validate_document(broken); checks.append(("absolute provenance rejected", False))
        except OracleError: checks.append(("absolute provenance rejected", True))
        semantic_mutations = [
            ("effect_key", lambda value: value.__setitem__("effect_key", EFFECT_KEY + "-drift")),
            ("oracle_authority", lambda value: value.__setitem__("oracle_authority", ORACLE_AUTHORITY + "-drift")),
            ("abi_rejection_contract", lambda value: value["abi_rejection_contract"].__setitem__("executed_harness", "declarative-only")),
            ("coverage_axes", lambda value: value["coverage_axes"].pop("route")),
            ("control_group", lambda value: value["control_group"].__setitem__("public_direct_identity", False)),
            ("kernel_liveness_census", lambda value: value["kernel_liveness_census"].__setitem__("nonzero_kernel_with_effect_width", "identical")),
            ("claim_boundaries", lambda value: value["claim_boundaries"].__setitem__("tolerance", "epsilon")),
            ("generator provenance", lambda value: value["provenance"]["generator"].__setitem__("sha256", "0" * 64)),
            ("native materializer provenance", lambda value: value["provenance"]["native_include_generator"].__setitem__("sha256", "0" * 64)),
            ("exactness contract", lambda value: value["exactness_contract"].__setitem__("tolerance", "epsilon")),
        ]
        semantic_results = []
        for label, mutate in semantic_mutations:
            broken = copy.deepcopy(doc); mutate(broken)
            try: validate_document(broken); semantic_results.append(False)
            except OracleError: semantic_results.append(True)
        checks.append(("semantic mandatory fields rejected", all(semantic_results)))
        broken = copy.deepcopy(doc); broken["render_cases"][0]["width"] = True
        try: validate_document(broken); checks.append(("bool-as-int rejected", False))
        except OracleError: checks.append(("bool-as-int rejected", True))
        type_mutations = [
            ("zero dimension", lambda value: value["render_cases"][0].__setitem__("height", 0)),
            ("seed above int32", lambda value: value["render_cases"][0]["bindings"].__setitem__("seed", 2147483648)),
            ("seed below int32", lambda value: value["render_cases"][0]["bindings"].__setitem__("seed", -2147483649)),
            ("uint32 above range", lambda value: value["kernel_liveness_census"].__setitem__("live_probe_changed_lanes", 0x100000000)),
            ("invalid emitted word", lambda value: value["render_cases"][0]["bindings"].__setitem__("time", "0x100000000")),
            ("schema bool", lambda value: value.__setitem__("schema_version", True)),
            ("define bool", lambda value: value["defines"].__setitem__("KERNEL", False)),
            ("wrap integer", lambda value: value["coverage_axes"].__setitem__("wrap", [0, 1])),
        ]
        type_results = []
        for label, mutate in type_mutations:
            broken = copy.deepcopy(doc); mutate(broken)
            try: validate_document(broken); type_results.append(False)
            except OracleError: type_results.append(True)
        checks.append(("ABI numeric boundaries rejected", all(type_results)))
        broken = copy.deepcopy(doc); broken["provenance"]["cpu_snapshot"]["import_closure"].pop()
        try: validate_document(broken); checks.append(("missing import-closure entry rejected", False))
        except OracleError: checks.append(("missing import-closure entry rejected", True))
        broken = copy.deepcopy(doc); broken["provenance"]["cpu_snapshot"]["import_closure"].append({"relative_path": "src/runtime/foreign.js", "sha256": "0" * 64})
        try: validate_document(broken); checks.append(("extra import-closure entry rejected", False))
        except OracleError: checks.append(("extra import-closure entry rejected", True))
        broken = copy.deepcopy(doc); broken["provenance"]["cpu_snapshot"]["import_closure"][0]["sha256"] = "0" * 64
        try: validate_document(broken); checks.append(("modified closure dependency rejected", False))
        except OracleError: checks.append(("modified closure dependency rejected", True))
        broken = copy.deepcopy(doc); broken["mutation_ledger"][0]["rows"][0]["changed_float32_lanes"] = -1
        try: validate_document(broken); checks.append(("mutation count sabotage rejected", False))
        except OracleError: checks.append(("mutation count sabotage rejected", True))
        mutation_mutations = [
            lambda value: (value["mutation_ledger"][0]["rows"][0].__setitem__("differs", False), value["mutation_ledger"][0]["rows"][0].__setitem__("changed_float32_lanes", 1)),
            lambda value: (value["mutation_ledger"][0]["rows"][0].__setitem__("differs", True), value["mutation_ledger"][0]["rows"][0].__setitem__("changed_float32_lanes", 0), value["mutation_ledger"][0]["rows"][0].__setitem__("changed_rgba8_bytes", 0)),
            lambda value: [row.__setitem__("differs", False) or row.__setitem__("changed_float32_lanes", 0) or row.__setitem__("changed_rgba8_bytes", 0) for row in value["mutation_ledger"][0]["rows"]],
        ]
        mutation_results = []
        for mutate in mutation_mutations:
            broken = copy.deepcopy(doc); mutate(broken)
            try: validate_document(broken); mutation_results.append(False)
            except OracleError: mutation_results.append(True)
        checks.append(("mutation witness invariants rejected", all(mutation_results)))
        native_mutations = [
            lambda value: value["native_expected_rejection"].pop(),
            lambda value: value["native_expected_rejection"][0].__setitem__("binding_name", "renamed"),
            lambda value: value["native_expected_rejection"][0].__setitem__("authenticated_expected_abi_category", "float"),
            lambda value: value["native_expected_rejection"].reverse(),
            lambda value: value["native_expected_rejection"].insert(0, copy.deepcopy(value["native_expected_rejection"][0])),
            lambda value: value["native_expected_rejection"].append(copy.deepcopy(value["native_expected_rejection"][-1])),
            lambda value: value["native_expected_rejection"][0].__setitem__("native_wrong_variant", "bool"),
            lambda value: value["native_expected_rejection"][0].__setitem__("status", "executed"),
        ]
        native_results = []
        for mutate in native_mutations:
            broken = copy.deepcopy(doc); mutate(broken)
            try: validate_document(broken); native_results.append(False)
            except OracleError: native_results.append(True)
        checks.append(("native ABI table sabotage rejected", all(native_results)))
        semantic_carrier_mutations = [
            lambda value: value["comparer_self_tests"].__setitem__("exact_words_and_bytes", False),
            lambda value: value["xor_sites_axis"].__setitem__("loop_offset", 9),
            lambda value: value["binding_liveness_census"].__setitem__("live", []),
            lambda value: value["mutable_global_contracts"]["emboss"].__setitem__("elements", [99] * 9),
            lambda value: value["mutable_global_contracts"]["emboss"].__setitem__("writer", "changed"),
        ]
        carrier_results = []
        for mutate in semantic_carrier_mutations:
            broken = copy.deepcopy(doc); mutate(broken)
            try: validate_document(broken); carrier_results.append(False)
            except OracleError: carrier_results.append(True)
        checks.append(("semantic carrier sabotage rejected", all(carrier_results)))
        mutation_exact_mutations = [
            lambda value: value["mutation_ledger"][0].__setitem__("name", "renamed"),
            lambda value: value.__setitem__("mutation_ledger", [value["mutation_ledger"][0]]),
            lambda value: value["mutation_ledger"].reverse(),
            lambda value: value["mutation_ledger"][0]["rows"].reverse(),
        ]
        mutation_exact_results = []
        for mutate in mutation_exact_mutations:
            broken = copy.deepcopy(doc); mutate(broken)
            try: validate_document(broken); mutation_exact_results.append(False)
            except OracleError: mutation_exact_results.append(True)
        checks.append(("mutation ledger exactness rejected", all(mutation_exact_results)))
    except OracleError as error:
        print(f"self-test setup failed: {error}", file=sys.stderr)
        return 1
    failed = [label for label, ok in checks if not ok]
    for label, ok in checks: print(f"  [{'ok' if ok else 'FAIL'}] {label}")
    print(f"{len(checks) - len(failed)}/{len(checks)} self-test checks passed")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test: return self_test()
    doc, oracle_sha = load_oracle()
    rendered = render(doc, oracle_sha).encode()
    if args.write:
        TARGET.write_bytes(rendered)
        TARGET.with_name(TARGET.name + ".sha256").write_text(sidecar_text(TARGET, rendered))
        TOOL.with_name(TOOL.name + ".sha256").write_text(sidecar_text(TOOL, TOOL.read_bytes()))
        print(f"kaleido187 native oracle include written ({len(rendered)} bytes, {digest(rendered)})")
        return 0
    actual = verify_sidecar(TARGET)
    if actual != rendered: raise OracleError("kaleido187_expected.inc drift")
    verify_sidecar(TOOL)
    print("kaleido187 native oracle include: ok")
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except OracleError as error:
        print(f"generate_kaleido_native_oracle_include: {error}", file=sys.stderr)
        raise SystemExit(1)
