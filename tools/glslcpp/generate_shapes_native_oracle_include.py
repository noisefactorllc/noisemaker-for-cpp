#!/usr/bin/env python3
"""Generate the checked native Shapes183 fixture from the canonical JS JSON.

This is the sole JSON-to-C++ materializer for `classicNoisedeck/shapes:shapes`.
It never renders anything: every expected word and byte originates in
`docs/port-engineering/shapes-parity/shapes183-oracles.json`, which is produced
by the canonical JavaScript oracle generator. The materializer is fail-closed
and rejects missing or extra fields, duplicate case names, malformed
dimensions, counts, hex words or byte values, wrong digests, wrong or missing
sidecars, and truncated or extra arrays. `--self-test` proves each rejection.
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import json
import pathlib
import re
import shutil
import struct
import sys
import tempfile
from typing import Any, Callable


ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/shapes-parity"
OUTPUT = ROOT / "tests/oracles/shapes183_expected.inc"
TOOL = pathlib.Path(__file__).resolve()

SCHEMA = "noisemaker-for-cpp.shapes183.pixel-parity.v1"
SCHEMA_VERSION = 1
PROGRAM_KEY = "classicNoisedeck/shapes:shapes"
EFFECT_KEY = "classicNoisedeck/shapes"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
DEFINES = {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30}
FACTORY_NAME = "canonicalFactory16"
FACTORY_SHA256 = "a4e1aeaf8cbc3d748517369e054b7ec4a2fd5f70962cbafef61d5e473527c2c3"
SOURCE_RELATIVE = (
    f"tools/glslcpp/corpus/{CORPUS_REVISION}"
    "/sources/classicNoisedeck/shapes/shapes.glsl")
SOURCE_BYTES = 21289
SOURCE_SHA256 = "60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0"
PINNED_CPU_FILES = {
    "canonical_kernels": (
        "src/effects/generated/canonical-kernels.js",
        "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe"),
    "public_catalog": (
        "src/effects/catalog.js",
        "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4"),
    "glsl_kernel": (
        "src/csl/glsl-kernel.js",
        "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa"),
    "glsl_runtime": (
        "src/csl/glsl-runtime.js",
        "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072"),
    "pass_runner": (
        "src/runtime/pass-runner.js",
        "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa"),
    "surface": (
        "src/runtime/surface.js",
        "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59"),
}

CPU_ROOT_PLACEHOLDER = "<immutable-cpu-snapshot-root>"
LIVE_CHECKOUT_PLACEHOLDER = "<live-noisemaker-for-cpu-checkout>"
# A checked-in gate must not carry a machine-specific path anywhere. `$HOME/...`
# and `<placeholder>` forms are fine; a rooted filesystem path is not.
ABSOLUTE_PATH = re.compile(r"(?:^/|/Users/|/home/|/private/|/var/|/tmp/)")

WORD = re.compile(r"0x[0-9a-f]{8}")
HEX64 = re.compile(r"[0-9a-f]{64}")
ALPHA_WORD = "0x3f800000"
ALPHA_BYTE = 255

BINDING_NAMES = (
    "time", "seed", "wrap", "resolution", "tileOffset", "fullResolution",
    "loopAScale", "loopBScale", "speedA", "speedB", "paletteMode",
    "paletteOffset", "paletteAmp", "paletteFreq", "palettePhase",
    "cyclePalette", "rotatePalette", "repeatPalette",
)
BINDING_ABI = {
    "time": "number", "seed": "int32", "wrap": "bool", "resolution": "Vec2",
    "tileOffset": "Vec2", "fullResolution": "Vec2", "loopAScale": "number",
    "loopBScale": "number", "speedA": "number", "speedB": "number",
    "paletteMode": "int32", "paletteOffset": "Vec3", "paletteAmp": "Vec3",
    "paletteFreq": "Vec3", "palettePhase": "Vec3", "cyclePalette": "int32",
    "rotatePalette": "number", "repeatPalette": "number",
}
VEC_LANES = {"Vec2": 2, "Vec3": 3}

# (name, width, height, route)
EXPECTED_CASES = (
    ("oklab-palette-a", 9, 5, "full"),
    ("oklab-palette-tiled", 4, 6, "tile"),
    ("oklab-palette-extreme", 6, 6, "full"),
    ("oklab-palette-negative-speed", 5, 9, "full"),
    ("diagnostic-palette-hsv", 8, 3, "full"),
    ("diagnostic-palette-rgb", 4, 4, "full"),
)
REACHING_CASES = (
    "oklab-palette-a", "oklab-palette-tiled", "oklab-palette-extreme",
    "oklab-palette-negative-speed",
)
NON_REACHING_CASES = ("diagnostic-palette-hsv", "diagnostic-palette-rgb")
MUTANTS = ("shapes-fwdB-column-swap", "shapes-cube-unnarrowed")
CONTROLS = (
    ("external-pass-extreme", "identical"),
    ("bound-time-ten", "differs"),
    ("bound-seed-123", "differs"),
)
REQUIRED_SELF_TESTS = (
    "equal_area_different_shape_rejected_before_access",
    "signed_zero_rejected_with_equal_rgba8",
    "distinct_quiet_nan_payload_rejected_with_equal_rgba8",
    "final_float32_alpha_lane_reported",
    "independent_final_rgba8_byte_reported",
    "expected_lane_and_byte_count_short_and_long_rejected_before_iteration",
)

TOP_LEVEL_KEYS = {
    "schema", "schema_version", "program_key", "effect_key", "runtime_key",
    "corpus_revision", "upstream_revision", "defines", "runtime_binding_names",
    "runtime_binding_abi", "compile_time_defines_are_not_bindings",
    "oracle_authority", "exactness_contract", "provenance",
    "comparer_self_tests", "coverage_axes", "render_cases", "crop_identity",
    "control_group", "seed_liveness_census", "mutation_ledger",
    "mutation_discrimination_contract", "claim_boundaries",
}
CASE_KEYS = {
    "name", "coverage", "route", "width", "height", "bindings",
    "external_pass", "output_expected", "canonical_repeat", "public_canonical",
}
SURFACE_KEYS = {
    "width", "height", "f32_words_le", "f32_sha256", "rgba8_bytes",
    "rgba8_sha256", "finite_lane_count", "nonfinite_lane_count",
    "alpha_f32_word", "alpha_rgba8_byte",
}


class OracleError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class Paths:
    package: pathlib.Path
    tool: pathlib.Path
    output: pathlib.Path

    @property
    def oracle(self) -> pathlib.Path:
        return self.package / "shapes183-oracles.json"

    @property
    def report(self) -> pathlib.Path:
        return self.package / "shapes183-oracle-report.md"

    @property
    def generator(self) -> pathlib.Path:
        return self.package / "shapes183_oracle_generator.mjs"


LIVE = Paths(package=PACKAGE, tool=TOOL, output=OUTPUT)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sidecar_text(target: pathlib.Path, payload: bytes) -> str:
    return f"{sha256(payload)}  {target.name}\n"


def verify_sidecar(target: pathlib.Path) -> bytes:
    sidecar = target.with_suffix(target.suffix + ".sha256")
    if not target.is_file() or not sidecar.is_file():
        raise OracleError(f"missing checked asset or sidecar: {target.name}")
    payload = target.read_bytes()
    if sidecar.read_text(encoding="utf-8") != sidecar_text(target, payload):
        raise OracleError(f"checksum sidecar drift: {target.name}")
    return payload


def require_keys(value: object, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OracleError(f"{label}: object required")
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise OracleError(f"{label}: missing field(s) {', '.join(missing)}")
    if extra:
        raise OracleError(f"{label}: unexpected field(s) {', '.join(extra)}")
    return value


def require_word_array(value: object, count: int, label: str) -> list[str]:
    if not isinstance(value, list):
        raise OracleError(f"{label}: Float32 word array required")
    if len(value) != count:
        raise OracleError(
            f"{label}: expected {count} Float32 words, found {len(value)}")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not WORD.fullmatch(item):
            raise OracleError(f"{label}: malformed Float32 word at {index}")
    return value


def require_byte_array(value: object, count: int, label: str) -> list[int]:
    if not isinstance(value, list):
        raise OracleError(f"{label}: RGBA8 byte array required")
    if len(value) != count:
        raise OracleError(
            f"{label}: expected {count} RGBA8 bytes, found {len(value)}")
    for index, item in enumerate(value):
        if (not isinstance(item, int) or isinstance(item, bool)
                or not 0 <= item <= 255):
            raise OracleError(f"{label}: malformed RGBA8 byte at {index}")
    return value


def require_dimension(value: object, expected: int, label: str) -> int:
    if (not isinstance(value, int) or isinstance(value, bool)
            or value != expected or value <= 0):
        raise OracleError(f"{label}: malformed dimension {value!r}")
    return value


def require_hex64(value: object, label: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise OracleError(f"{label}: malformed SHA-256 digest")
    return value


def validate_surface(record: object, width: int, height: int,
                     label: str) -> dict[str, Any]:
    surface = require_keys(record, SURFACE_KEYS, label)
    require_dimension(surface.get("width"), width, f"{label}.width")
    require_dimension(surface.get("height"), height, f"{label}.height")
    count = width * height * 4
    words = require_word_array(surface.get("f32_words_le"), count, label)
    rgba = require_byte_array(surface.get("rgba8_bytes"), count, label)
    packed = b"".join(struct.pack("<I", int(word, 16)) for word in words)
    if sha256(packed) != require_hex64(surface.get("f32_sha256"),
                                       f"{label}.f32_sha256"):
        raise OracleError(f"{label}: Float32 digest mismatch")
    if sha256(bytes(rgba)) != require_hex64(surface.get("rgba8_sha256"),
                                            f"{label}.rgba8_sha256"):
        raise OracleError(f"{label}: RGBA8 digest mismatch")
    finite = surface.get("finite_lane_count")
    nonfinite = surface.get("nonfinite_lane_count")
    if (not isinstance(finite, int) or isinstance(finite, bool)
            or not isinstance(nonfinite, int) or isinstance(nonfinite, bool)
            or finite + nonfinite != count or finite < 0 or nonfinite < 0):
        raise OracleError(f"{label}: finite census mismatch")
    if (surface.get("alpha_f32_word") != ALPHA_WORD
            or surface.get("alpha_rgba8_byte") != ALPHA_BYTE):
        raise OracleError(f"{label}: alpha contract mismatch")
    for index in range(3, count, 4):
        if words[index] != ALPHA_WORD:
            raise OracleError(
                f"{label}: alpha Float32 word at lane {index} is {words[index]}")
        if rgba[index] != ALPHA_BYTE:
            raise OracleError(
                f"{label}: alpha RGBA8 byte at lane {index} is {rgba[index]}")
    return surface


def validate_bindings(record: object, label: str) -> dict[str, Any]:
    bindings = require_keys(record, set(BINDING_NAMES), label)
    if tuple(bindings) != BINDING_NAMES:
        raise OracleError(f"{label}: binding order drift")
    for name in BINDING_NAMES:
        abi = BINDING_ABI[name]
        item = bindings[name]
        field = f"{label}.{name}"
        if abi == "int32":
            entry = require_keys(item, {"abi", "value"}, field)
            value = entry["value"]
            if (not isinstance(value, int) or isinstance(value, bool)
                    or not -2147483648 <= value <= 2147483647):
                raise OracleError(f"{field}: int32 value required")
        elif abi == "bool":
            entry = require_keys(item, {"abi", "value"}, field)
            if not isinstance(entry["value"], bool):
                raise OracleError(f"{field}: bool value required")
        elif abi == "number":
            entry = require_keys(item, {"abi", "f32_value", "f32_word_le"},
                                 field)
            if not isinstance(entry["f32_value"], (int, float)) or isinstance(
                    entry["f32_value"], bool):
                raise OracleError(f"{field}: numeric value required")
            require_word_array([entry["f32_word_le"]], 1, field)
        else:
            entry = require_keys(item, {"abi", "f32_values", "f32_words_le"},
                                 field)
            lanes = VEC_LANES[abi]
            values = entry["f32_values"]
            if (not isinstance(values, list) or len(values) != lanes
                    or any(not isinstance(item, (int, float))
                           or isinstance(item, bool) for item in values)):
                raise OracleError(f"{field}: {abi} lane values required")
            require_word_array(entry["f32_words_le"], lanes, field)
        if entry["abi"] != abi:
            raise OracleError(f"{field}: ABI drift {entry['abi']!r}")
    return bindings


def validate_external(record: object, label: str) -> dict[str, Any]:
    external = require_keys(record, {"time", "seed"}, label)
    for name in ("time", "seed"):
        entry = require_keys(external[name], {"f32_value", "f32_word_le"},
                             f"{label}.{name}")
        require_word_array([entry["f32_word_le"]], 1, f"{label}.{name}")
    return external


def validate_identity(record: object, label: str) -> None:
    entry = require_keys(record, {
        "exact", "changed_lane_count", "changed_rgba8_byte_count",
        "expected_dimensions", "actual_dimensions"}, label)
    if entry["exact"] is not True or entry["changed_lane_count"] != 0 \
            or entry["changed_rgba8_byte_count"] != 0:
        raise OracleError(f"{label}: route is not exact")
    if entry["expected_dimensions"] != entry["actual_dimensions"]:
        raise OracleError(f"{label}: route dimension mismatch")


def validate_provenance(oracle: dict[str, Any], paths: Paths) -> None:
    provenance = require_keys(oracle.get("provenance"), {
        "node_version", "generator", "native_include_generator", "cpu_snapshot",
        "source", "canonical_factory", "public_factory_is_canonical_identity",
        "adapter_override_absent", "metadata"}, "provenance")
    for field, target in (("generator", paths.generator),
                          ("native_include_generator", paths.tool)):
        entry = require_keys(provenance[field], {
            "relative_path_from_noisemaker_for_cpp", "sha256"},
            f"provenance.{field}")
        if entry["sha256"] != sha256(target.read_bytes()):
            raise OracleError(
                f"provenance.{field}: recorded digest does not match "
                f"{target.name}")
    if provenance["public_factory_is_canonical_identity"] is not True:
        raise OracleError("provenance: public factory is not canonical identity")
    if provenance["adapter_override_absent"] is not True:
        raise OracleError("provenance: adapter override was not excluded")
    factory = require_keys(provenance["canonical_factory"], {
        "name", "bytes", "sha256", "source_slice_bytes",
        "source_slice_sha256"}, "provenance.canonical_factory")
    if factory["name"] != FACTORY_NAME or factory["sha256"] != FACTORY_SHA256:
        raise OracleError("provenance: canonical factory identity mismatch")
    source = require_keys(provenance["source"], {
        "relative_path_from_noisemaker_for_cpp", "bytes", "sha256"},
        "provenance.source")
    if (source["relative_path_from_noisemaker_for_cpp"] != SOURCE_RELATIVE
            or source["bytes"] != SOURCE_BYTES
            or source["sha256"] != SOURCE_SHA256):
        raise OracleError("provenance: pinned GLSL source mismatch")
    snapshot = require_keys(provenance["cpu_snapshot"], {
        "argument", "immutable_snapshot", "live_checkout_rejected",
        "live_checkout_resolution", "imports_confined_beneath_snapshot",
        "import_closure_file_count", "import_closure", "pinned_files"},
        "provenance.cpu_snapshot")
    if (snapshot["immutable_snapshot"] is not True
            or snapshot["imports_confined_beneath_snapshot"] is not True):
        raise OracleError("provenance: snapshot confinement not proven")
    # No absolute path may be recorded: `--check` byte-compares this document, so
    # a literal path would bind the gate to one directory on one machine, and
    # would leak a home directory into the repository.
    if (snapshot["argument"] != CPU_ROOT_PLACEHOLDER
            or snapshot["live_checkout_rejected"] != LIVE_CHECKOUT_PLACEHOLDER):
        raise OracleError(
            "provenance.cpu_snapshot: paths must be recorded as stable "
            "placeholders, never as literal filesystem paths")
    closure = snapshot["import_closure"]
    if (not isinstance(closure, list) or not closure
            or snapshot["import_closure_file_count"] != len(closure)):
        raise OracleError("provenance: import closure census mismatch")
    for entry in closure:
        item = require_keys(entry, {
            "relative_path_from_noisemaker_for_cpu", "sha256"},
            "provenance.cpu_snapshot.import_closure")
        require_hex64(item["sha256"], "provenance.cpu_snapshot.import_closure")
    pinned = require_keys(snapshot["pinned_files"], set(PINNED_CPU_FILES),
                          "provenance.cpu_snapshot.pinned_files")
    for name, (relative, digest) in PINNED_CPU_FILES.items():
        item = require_keys(pinned[name], {
            "relative_path_from_noisemaker_for_cpu", "sha256"},
            f"provenance.cpu_snapshot.pinned_files.{name}")
        if (item["relative_path_from_noisemaker_for_cpu"] != relative
                or item["sha256"] != digest):
            raise OracleError(f"provenance: pinned CPU file {name} mismatch")


def validate_crop(oracle: dict[str, Any],
                  by_name: dict[str, Any]) -> dict[str, Any]:
    crop = require_keys(oracle.get("crop_identity"), {
        "case", "rect", "tile_offset_rule", "tile_offset_f32_words_le",
        "held_identical_bindings", "full_route_expected",
        "exact_word_mismatches", "exact_byte_mismatches", "exact",
        "raw_crop_y_trap"}, "crop_identity")
    rect = require_keys(crop["rect"], {
        "crop_x", "crop_y", "tile_width", "tile_height", "full_width",
        "full_height"}, "crop_identity.rect")
    for key, value in rect.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise OracleError(f"crop_identity.rect: malformed {key}")
    if crop["case"] != "oklab-palette-tiled":
        raise OracleError("crop_identity: unexpected case")
    tile = by_name["oklab-palette-tiled"]
    if (tile["width"] != rect["tile_width"]
            or tile["height"] != rect["tile_height"]):
        raise OracleError("crop_identity: tile dimensions disagree with case")
    if (rect["crop_x"] + rect["tile_width"] > rect["full_width"]
            or rect["crop_y"] + rect["tile_height"] > rect["full_height"]):
        raise OracleError("crop_identity: crop rectangle escapes the full surface")
    expected_offset = (float(rect["crop_x"]),
                       float(rect["full_height"] - rect["crop_y"]
                             - rect["tile_height"]))
    actual_offset = tuple(
        struct.unpack("<f", struct.pack("<I", int(word, 16)))[0]
        for word in require_word_array(tile["bindings"]["tileOffset"]["f32_words_le"],
                                       2, "crop_identity.tileOffset"))
    if actual_offset != expected_offset:
        raise OracleError(
            "crop_identity: tileOffset is not "
            "(crop_x, full_height - crop_y - tile_height)")
    if require_word_array(crop["tile_offset_f32_words_le"], 2,
                          "crop_identity.tile_offset_f32_words_le") != \
            tile["bindings"]["tileOffset"]["f32_words_le"]:
        raise OracleError("crop_identity: recorded tileOffset words disagree")
    full = validate_surface(crop["full_route_expected"], rect["full_width"],
                            rect["full_height"], "crop_identity.full_route")
    if (crop["exact"] is not True or crop["exact_word_mismatches"] != 0
            or crop["exact_byte_mismatches"] != 0):
        raise OracleError("crop_identity: tile is not an exact top-down crop")
    tile_words = tile["output_expected"]["f32_words_le"]
    tile_bytes = tile["output_expected"]["rgba8_bytes"]
    full_words = full["f32_words_le"]
    full_bytes = full["rgba8_bytes"]
    for ty in range(rect["tile_height"]):
        for tx in range(rect["tile_width"]):
            for channel in range(4):
                tile_index = ((ty * rect["tile_width"]) + tx) * 4 + channel
                full_index = (((rect["crop_y"] + ty) * rect["full_width"])
                              + (rect["crop_x"] + tx)) * 4 + channel
                if tile_words[tile_index] != full_words[full_index]:
                    raise OracleError(
                        "crop_identity: stored tile word differs from the "
                        f"top-down crop at lane {tile_index}")
                if tile_bytes[tile_index] != full_bytes[full_index]:
                    raise OracleError(
                        "crop_identity: stored tile byte differs from the "
                        f"top-down crop at lane {tile_index}")
    trap = require_keys(crop["raw_crop_y_trap"], {
        "tile_offset_f32_words_le", "differs_from_correct_tile",
        "changed_lane_count", "first_mismatch"}, "crop_identity.raw_crop_y_trap")
    if trap["differs_from_correct_tile"] is not True or trap["changed_lane_count"] < 1:
        raise OracleError("crop_identity: raw crop_y trap is vacuous")
    return crop


def validate_controls(oracle: dict[str, Any],
                      by_name: dict[str, Any]) -> dict[str, Any]:
    group = require_keys(oracle.get("control_group"), {
        "anchor", "baseline", "controls"}, "control_group")
    if group["anchor"] != "oklab-palette-a":
        raise OracleError("control_group: unexpected anchor")
    require_keys(group["baseline"], {"external_pass", "f32_sha256",
                                     "rgba8_sha256"}, "control_group.baseline")
    anchor_case = by_name.get(group["anchor"])
    if not isinstance(anchor_case, dict):
        raise OracleError("control_group: anchor case is absent")
    anchor_surface = anchor_case["output_expected"]
    controls = group["controls"]
    if not isinstance(controls, list) or len(controls) != len(CONTROLS):
        raise OracleError("control_group: control census mismatch")
    # Do not trust the stored `observed` string: the baseline arrays are in the
    # same document, so every control's relation to the anchor is re-derived
    # from the arrays themselves. Same reasoning as the crop re-derivation
    # above -- a hand-edited control with refreshed digests must not survive.
    derived: list[str] = []
    for control, (name, expectation) in zip(controls, CONTROLS):
        label = f"control_group.{name}"
        entry = require_keys(control, {
            "name", "axis", "expectation", "observed", "pass",
            "changed_lane_count", "changed_rgba8_byte_count", "first_mismatch",
            "external_pass", "bindings", "output", "note"}, label)
        if entry["name"] != name or entry["expectation"] != expectation:
            raise OracleError(f"{label}: control identity mismatch")
        if entry["observed"] not in ("identical", "differs"):
            raise OracleError(f"{label}: malformed observation")
        if entry["pass"] is not (entry["observed"] == entry["expectation"]):
            raise OracleError(f"{label}: pass ledger disagrees with observation")
        validate_bindings(entry["bindings"], f"{label}.bindings")
        validate_external(entry["external_pass"], f"{label}.external_pass")
        output = entry["output"]
        if not isinstance(output, dict):
            raise OracleError(f"{label}: output record required")
        # The anchor's own geometry, never the record's self-reported
        # dimensions: a self-consistent control of another shape -- including
        # a transpose with an identical lane count -- is not a one-axis
        # variant of the anchor.
        surface = validate_surface(output, anchor_case["width"],
                                   anchor_case["height"], f"{label}.output")
        derived.append(
            "identical"
            if (surface["f32_words_le"] == anchor_surface["f32_words_le"]
                and surface["rgba8_bytes"] == anchor_surface["rgba8_bytes"])
            else "differs")
    if controls[0]["observed"] != "identical":
        raise OracleError(
            "control_group: external runPass time/seed changed the output")
    if controls[1]["observed"] != "differs":
        raise OracleError("control_group: bound time did not change the output")
    for control, (name, _), observation in zip(controls, CONTROLS, derived):
        if control["observed"] != observation:
            raise OracleError(
                f"control_group.{name}: recorded observation "
                f"{control['observed']!r} disagrees with the stored arrays, "
                f"which are {observation} to the {group['anchor']} baseline")
    return group


def validate_seed_census(oracle: dict[str, Any],
                         group: dict[str, Any]) -> None:
    census = require_keys(oracle.get("seed_liveness_census"), {
        "probe_case", "probes", "bound_seed_changes_output", "reason",
        "design_expectation", "disagreement"}, "seed_liveness_census")
    probes = census["probes"]
    if not isinstance(probes, list) or len(probes) < 2:
        raise OracleError("seed_liveness_census: probe census mismatch")
    seen = set()
    for probe in probes:
        entry = require_keys(probe, {
            "seed", "f32_sha256", "differs_from_baseline",
            "changed_lane_count"}, "seed_liveness_census.probes")
        if (not isinstance(entry["seed"], int) or isinstance(entry["seed"], bool)
                or not -2147483648 <= entry["seed"] <= 2147483647):
            raise OracleError("seed_liveness_census: malformed probe seed")
        if entry["seed"] in seen:
            raise OracleError("seed_liveness_census: duplicate probe seed")
        seen.add(entry["seed"])
        require_hex64(entry["f32_sha256"], "seed_liveness_census.probes")
    observed = any(probe["differs_from_baseline"] for probe in probes)
    if census["bound_seed_changes_output"] is not observed:
        raise OracleError(
            "seed_liveness_census: summary disagrees with the probe ledger")
    seed_control = group["controls"][2]
    if (seed_control["observed"] == "differs") is not observed:
        raise OracleError(
            "seed_liveness_census: bound-seed control disagrees with the census")


def validate_mutations(oracle: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = oracle.get("mutation_ledger")
    if not isinstance(ledger, list) or tuple(
            item.get("name") for item in ledger) != MUTANTS:
        raise OracleError("mutation_ledger: mutant census mismatch")
    contract = require_keys(oracle.get("mutation_discrimination_contract"), {
        "reaching_cases", "non_reaching_cases", "rule"},
        "mutation_discrimination_contract")
    if (tuple(contract["reaching_cases"]) != REACHING_CASES
            or tuple(contract["non_reaching_cases"]) != NON_REACHING_CASES):
        raise OracleError("mutation_discrimination_contract: case split drift")
    for mutant in ledger:
        label = f"mutation_ledger.{mutant.get('name')}"
        entry = require_keys(mutant, {
            "name", "target", "reaching", "classification", "anchor_sha256",
            "replacement_sha256", "mutated_factory_sha256", "anchor_occurrences",
            "results"}, label)
        if entry["anchor_occurrences"] != 1:
            raise OracleError(f"{label}: anchor is not unique")
        for field in ("anchor_sha256", "replacement_sha256",
                      "mutated_factory_sha256"):
            require_hex64(entry[field], f"{label}.{field}")
        results = entry["results"]
        if not isinstance(results, list) or tuple(
                item.get("case") for item in results) != tuple(
                    name for name, _, _, _ in EXPECTED_CASES):
            raise OracleError(f"{label}: result census mismatch")
        for result in results:
            row = require_keys(result, {
                "case", "reaching", "differs", "changed_lane_count",
                "changed_rgba8_byte_count", "f32_sha256", "rgba8_sha256",
                "first_mismatch"}, f"{label}.{result.get('case')}")
            reaching = row["case"] in REACHING_CASES
            if row["reaching"] is not reaching:
                raise OracleError(f"{label}: reachability drift for {row['case']}")
            if reaching and (row["differs"] is not True
                             or row["changed_lane_count"] < 1):
                raise OracleError(
                    f"{label}: reaching case {row['case']} did not discriminate")
            if not reaching and (row["differs"] is not False
                                 or row["changed_lane_count"] != 0):
                raise OracleError(
                    f"{label}: non-reaching control {row['case']} changed")
    return ledger


def load(paths: Paths = LIVE) -> tuple[dict[str, Any], str]:
    verify_sidecar(paths.generator)
    verify_sidecar(paths.report)
    payload = verify_sidecar(paths.oracle)
    # Whole-document guard, not only the fields that are known to hold paths: a
    # machine-specific absolute path anywhere in a byte-compared gate makes the
    # gate unrunnable off the machine that produced it.
    leaked = ABSOLUTE_PATH.search(payload.decode("utf-8", "replace"))
    if leaked is not None:
        raise OracleError(
            "Shapes183 oracle records an absolute filesystem path "
            f"({leaked.group(0)!r}); the gate must be path-independent")
    try:
        oracle = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OracleError(f"invalid Shapes183 JSON: {error}") from error
    require_keys(oracle, TOP_LEVEL_KEYS, "oracle")
    if (oracle["schema"], oracle["schema_version"], oracle["program_key"],
            oracle["effect_key"], oracle["runtime_key"],
            oracle["corpus_revision"]) != (
                SCHEMA, SCHEMA_VERSION, PROGRAM_KEY, EFFECT_KEY, PROGRAM_KEY,
                CORPUS_REVISION):
        raise OracleError("Shapes183 schema/program identity mismatch")
    if oracle["defines"] != DEFINES:
        raise OracleError("Shapes183 define mismatch")
    if tuple(oracle["runtime_binding_names"]) != BINDING_NAMES:
        raise OracleError("Shapes183 runtime binding census mismatch")
    if oracle["runtime_binding_abi"] != BINDING_ABI:
        raise OracleError("Shapes183 runtime binding ABI mismatch")
    if oracle["compile_time_defines_are_not_bindings"] is not True:
        raise OracleError("Shapes183 compile-time define contract mismatch")
    validate_provenance(oracle, paths)
    self_tests = oracle.get("comparer_self_tests")
    if not isinstance(self_tests, dict) or any(
            self_tests.get(name) is not True for name in REQUIRED_SELF_TESTS):
        raise OracleError("Shapes183 comparer self-test mismatch")
    cases = oracle.get("render_cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise OracleError("Shapes183 fixture count mismatch")
    names: list[str] = []
    for index, (case, expected) in enumerate(zip(cases, EXPECTED_CASES)):
        name, width, height, route = expected
        entry = require_keys(case, CASE_KEYS, f"render_cases[{index}]")
        if entry["name"] in names:
            raise OracleError(f"render_cases[{index}]: duplicate case name "
                              f"{entry['name']}")
        names.append(entry["name"])
        if entry["name"] != name or entry["route"] != route:
            raise OracleError(f"render_cases[{index}]: case identity mismatch")
        require_dimension(entry["width"], width, f"{name}.width")
        require_dimension(entry["height"], height, f"{name}.height")
        if not isinstance(entry["coverage"], list) or not entry["coverage"]:
            raise OracleError(f"{name}: coverage labels required")
        validate_bindings(entry["bindings"], f"{name}.bindings")
        validate_external(entry["external_pass"], f"{name}.external_pass")
        validate_surface(entry["output_expected"], width, height,
                         f"{name}.output_expected")
        resolution = tuple(entry["bindings"]["resolution"]["f32_values"])
        if resolution != (float(width), float(height)):
            raise OracleError(f"{name}: resolution binding disagrees with dimensions")
        validate_identity(entry["canonical_repeat"], f"{name}.canonical_repeat")
        validate_identity(entry["public_canonical"], f"{name}.public_canonical")
    by_name = {case["name"]: case for case in cases}
    validate_crop(oracle, by_name)
    group = validate_controls(oracle, by_name)
    validate_seed_census(oracle, group)
    validate_mutations(oracle)
    return oracle, sha256(payload)


def array_lines(values: list[str] | list[int], suffix: str,
                width: int) -> list[str]:
    rendered = [f"{value}{suffix}" for value in values]
    return ["    " + ", ".join(rendered[index:index + width]) + ","
            for index in range(0, len(rendered), width)]


def word_list(values: list[str]) -> str:
    return ", ".join(f"{value}U" for value in values)


def render(paths: Paths = LIVE) -> bytes:
    oracle, oracle_hash = load(paths)
    cases = oracle["render_cases"]
    crop = oracle["crop_identity"]
    lines = [
        "// Generated from the checked canonical JavaScript Shapes183 oracle.",
        "// Do not edit; C++ output never participates in these expected arrays.",
        "#pragma once", "", "namespace shapes183_oracle {", "",
        f'inline constexpr std::string_view kOracleSha256 = "{oracle_hash}";',
        f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";',
        f'inline constexpr std::string_view kCorpusRevision = "{CORPUS_REVISION}";',
        f"inline constexpr std::int32_t kLoopAOffset = {DEFINES['LOOP_A_OFFSET']};",
        f"inline constexpr std::int32_t kLoopBOffset = {DEFINES['LOOP_B_OFFSET']};",
        f"inline constexpr std::size_t kCaseCount = {len(cases)}U;",
        f"inline constexpr std::size_t kBindingCount = {len(BINDING_NAMES)}U;",
        "",
        f"inline constexpr std::array<std::string_view, {len(BINDING_NAMES)}> "
        "kBindingNames{{",
        "    " + ", ".join(f'"{name}"' for name in BINDING_NAMES) + ",",
        "}};", "",
    ]
    for index, case in enumerate(cases):
        surface = case["output_expected"]
        lines.append(
            f"inline constexpr std::array<std::uint32_t, "
            f"{len(surface['f32_words_le'])}> kCase{index}ExpectedWords{{{{")
        lines.extend(array_lines(surface["f32_words_le"], "U", 8))
        lines.extend(["}};", ""])
        lines.append(
            f"inline constexpr std::array<std::uint8_t, "
            f"{len(surface['rgba8_bytes'])}> kCase{index}ExpectedRgba8{{{{")
        lines.extend(array_lines(surface["rgba8_bytes"], "U", 16))
        lines.extend(["}};", ""])
    full = crop["full_route_expected"]
    lines.append(
        f"inline constexpr std::array<std::uint32_t, "
        f"{len(full['f32_words_le'])}> kCropFullExpectedWords{{{{")
    lines.extend(array_lines(full["f32_words_le"], "U", 8))
    lines.extend(["}};", ""])
    lines.append(
        f"inline constexpr std::array<std::uint8_t, "
        f"{len(full['rgba8_bytes'])}> kCropFullExpectedRgba8{{{{")
    lines.extend(array_lines(full["rgba8_bytes"], "U", 16))
    lines.extend(["}};", ""])
    lines.extend([
        "struct CaseView {",
        "  std::string_view name;",
        "  std::size_t width;",
        "  std::size_t height;",
        "  std::string_view route;",
        "  std::span<const std::uint32_t> expected_words;",
        "  std::span<const std::uint8_t> expected_rgba8;",
        "  std::uint32_t time_word;",
        "  std::int32_t seed;",
        "  bool wrap;",
        "  std::array<std::uint32_t, 2> resolution_words;",
        "  std::array<std::uint32_t, 2> tile_offset_words;",
        "  std::array<std::uint32_t, 2> full_resolution_words;",
        "  std::uint32_t loop_a_scale_word;",
        "  std::uint32_t loop_b_scale_word;",
        "  std::uint32_t speed_a_word;",
        "  std::uint32_t speed_b_word;",
        "  std::int32_t palette_mode;",
        "  std::array<std::uint32_t, 3> palette_offset_words;",
        "  std::array<std::uint32_t, 3> palette_amp_words;",
        "  std::array<std::uint32_t, 3> palette_freq_words;",
        "  std::array<std::uint32_t, 3> palette_phase_words;",
        "  std::int32_t cycle_palette;",
        "  std::uint32_t rotate_palette_word;",
        "  std::uint32_t repeat_palette_word;",
        "  std::uint32_t external_time_word;",
        "  std::uint32_t external_seed_word;",
        "};", "",
        "struct CropProofView {",
        "  std::string_view tile_case;",
        "  std::size_t crop_x;",
        "  std::size_t crop_y;",
        "  std::size_t tile_width;",
        "  std::size_t tile_height;",
        "  std::size_t full_width;",
        "  std::size_t full_height;",
        "  std::array<std::uint32_t, 2> tile_offset_words;",
        "  std::span<const std::uint32_t> full_expected_words;",
        "  std::span<const std::uint8_t> full_expected_rgba8;",
        "};", "",
        f"inline constexpr std::array<CaseView, {len(cases)}> kCases{{{{",
    ])
    for index, case in enumerate(cases):
        binding = case["bindings"]
        external = case["external_pass"]
        lines.append(
            f'  CaseView{{"{case["name"]}", {case["width"]}U, {case["height"]}U, '
            f'"{case["route"]}", kCase{index}ExpectedWords, '
            f'kCase{index}ExpectedRgba8, '
            f'{binding["time"]["f32_word_le"]}U, {binding["seed"]["value"]}, '
            f'{str(binding["wrap"]["value"]).lower()}, '
            f'{{{word_list(binding["resolution"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["tileOffset"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["fullResolution"]["f32_words_le"])}}}, '
            f'{binding["loopAScale"]["f32_word_le"]}U, '
            f'{binding["loopBScale"]["f32_word_le"]}U, '
            f'{binding["speedA"]["f32_word_le"]}U, '
            f'{binding["speedB"]["f32_word_le"]}U, '
            f'{binding["paletteMode"]["value"]}, '
            f'{{{word_list(binding["paletteOffset"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["paletteAmp"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["paletteFreq"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["palettePhase"]["f32_words_le"])}}}, '
            f'{binding["cyclePalette"]["value"]}, '
            f'{binding["rotatePalette"]["f32_word_le"]}U, '
            f'{binding["repeatPalette"]["f32_word_le"]}U, '
            f'{external["time"]["f32_word_le"]}U, '
            f'{external["seed"]["f32_word_le"]}U}},')
    rect = crop["rect"]
    lines.extend([
        "}};", "",
        "inline constexpr CropProofView kCropProof{",
        f'    "{crop["case"]}", {rect["crop_x"]}U, {rect["crop_y"]}U, '
        f'{rect["tile_width"]}U, {rect["tile_height"]}U, '
        f'{rect["full_width"]}U, {rect["full_height"]}U,',
        f'    {{{word_list(crop["tile_offset_f32_words_le"])}}}, '
        "kCropFullExpectedWords, kCropFullExpectedRgba8,",
        "};", "",
        f'inline constexpr std::uint32_t kAlphaWord = {ALPHA_WORD}U;',
        f"inline constexpr std::uint8_t kAlphaByte = {ALPHA_BYTE}U;", "",
        "}  // namespace shapes183_oracle", "",
    ])
    return "\n".join(lines).encode("utf-8")


# ---------------------------------------------------------------------------
# Negative self-tests
# ---------------------------------------------------------------------------


def _expect_rejection(paths: Paths, fragment: str, label: str) -> None:
    try:
        load(paths)
    except OracleError as error:
        if fragment not in str(error):
            raise OracleError(
                f"self-test {label}: rejected with the wrong message: {error}"
            ) from error
        return
    raise OracleError(f"self-test {label}: mutation was accepted")


def _stage(destination: pathlib.Path) -> Paths:
    package = destination / "package"
    package.mkdir(parents=True)
    for name in ("shapes183-oracles.json", "shapes183-oracle-report.md",
                 "shapes183_oracle_generator.mjs"):
        shutil.copy2(PACKAGE / name, package / name)
        shutil.copy2(PACKAGE / f"{name}.sha256", package / f"{name}.sha256")
    return Paths(package=package, tool=TOOL, output=destination / "out.inc")


def _rewrite(paths: Paths, oracle: dict[str, Any]) -> None:
    payload = (json.dumps(oracle, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    paths.oracle.write_bytes(payload)
    paths.oracle.with_suffix(paths.oracle.suffix + ".sha256").write_text(
        sidecar_text(paths.oracle, payload), encoding="utf-8")


def _refresh_surface_digests(surface: dict[str, Any]) -> None:
    packed = b"".join(struct.pack("<I", int(word, 16))
                      for word in surface["f32_words_le"])
    surface["f32_sha256"] = sha256(packed)
    surface["rgba8_sha256"] = sha256(bytes(surface["rgba8_bytes"]))


def _break_alpha_word(doc: dict[str, Any]) -> None:
    surface = doc["render_cases"][0]["output_expected"]
    surface["f32_words_le"][3] = "0x3f000000"
    _refresh_surface_digests(surface)


def _break_alpha_byte(doc: dict[str, Any]) -> None:
    surface = doc["render_cases"][0]["output_expected"]
    surface["rgba8_bytes"][3] = 254
    _refresh_surface_digests(surface)


def _shift_crop_row(doc: dict[str, Any]) -> None:
    """Move the crop up one row, keeping the tileOffset rule satisfied.

    The offset rule still holds, so only the independent re-derivation of the
    tile from the stored full-route array can catch this.
    """
    rect = doc["crop_identity"]["rect"]
    rect["crop_y"] -= 1
    shifted = [f"0x{struct.unpack('<I', struct.pack('<f', float(value)))[0]:08x}"
               for value in (rect["crop_x"],
                             rect["full_height"] - rect["crop_y"]
                             - rect["tile_height"])]
    doc["crop_identity"]["tile_offset_f32_words_le"] = shifted
    doc["render_cases"][1]["bindings"]["tileOffset"]["f32_words_le"] = shifted
    doc["render_cases"][1]["bindings"]["tileOffset"]["f32_values"] = [
        float(rect["crop_x"]),
        float(rect["full_height"] - rect["crop_y"] - rect["tile_height"])]


def _fabricate_control(doc: dict[str, Any]) -> None:
    """Swap a lane of the `identical` external control for a foreign value.

    Both digests are refreshed and `observed` is left saying "identical", so
    only the independent re-derivation against the anchor case's own baseline
    arrays can reject it.
    """
    control = doc["control_group"]["controls"][0]
    surface = control["output"]
    surface["f32_words_le"][0] = "0x7f7fffff"
    surface["rgba8_bytes"][0] = 7
    _refresh_surface_digests(surface)


def _transpose_control_geometry(doc: dict[str, Any]) -> None:
    """Reshape the external control from 9x5 to 5x9.

    The lane count, both digests, and the alpha stride are all unchanged, so
    only comparing against the anchor case's own width/height can reject it.
    """
    surface = doc["control_group"]["controls"][0]["output"]
    surface["width"], surface["height"] = surface["height"], surface["width"]


def self_test() -> int:
    base, _ = load(LIVE)
    scenarios: tuple[tuple[str, Callable[[dict[str, Any]], None], str], ...] = (
        ("missing-top-level-field",
         lambda doc: doc.pop("crop_identity"), "missing field(s) crop_identity"),
        ("extra-top-level-field",
         lambda doc: doc.__setitem__("bonus", 1), "unexpected field(s) bonus"),
        ("missing-case-field",
         lambda doc: doc["render_cases"][0].pop("external_pass"),
         "missing field(s) external_pass"),
        ("extra-case-field",
         lambda doc: doc["render_cases"][0].__setitem__("bonus", 1),
         "unexpected field(s) bonus"),
        ("duplicate-case-name",
         lambda doc: doc["render_cases"][1].__setitem__(
             "name", doc["render_cases"][0]["name"]),
         "duplicate case name"),
        ("malformed-dimension",
         lambda doc: doc["render_cases"][0].__setitem__("width", 0),
         "malformed dimension"),
        ("malformed-surface-dimension",
         lambda doc: doc["render_cases"][0]["output_expected"].__setitem__(
             "height", 4), "malformed dimension"),
        ("malformed-hex-word",
         lambda doc: doc["render_cases"][0]["output_expected"]["f32_words_le"]
         .__setitem__(0, "0xZZZZZZZZ"), "malformed Float32 word at 0"),
        ("malformed-binding-word",
         lambda doc: doc["render_cases"][0]["bindings"]["paletteAmp"]
         .__setitem__("f32_words_le", ["0x00000000", "0x1", "0x00000000"]),
         "malformed Float32 word at 1"),
        ("malformed-byte-value",
         lambda doc: doc["render_cases"][0]["output_expected"]["rgba8_bytes"]
         .__setitem__(0, 256), "malformed RGBA8 byte at 0"),
        ("truncated-word-array",
         lambda doc: doc["render_cases"][0]["output_expected"]["f32_words_le"]
         .pop(), "Float32 words, found"),
        ("extra-word-array-entry",
         lambda doc: doc["render_cases"][0]["output_expected"]["f32_words_le"]
         .append("0x00000000"), "Float32 words, found"),
        ("truncated-byte-array",
         lambda doc: doc["render_cases"][0]["output_expected"]["rgba8_bytes"]
         .pop(), "RGBA8 bytes, found"),
        ("extra-byte-array-entry",
         lambda doc: doc["render_cases"][0]["output_expected"]["rgba8_bytes"]
         .append(0), "RGBA8 bytes, found"),
        ("wrong-float-digest",
         lambda doc: doc["render_cases"][0]["output_expected"].__setitem__(
             "f32_sha256", "0" * 64), "Float32 digest mismatch"),
        ("wrong-byte-digest",
         lambda doc: doc["render_cases"][0]["output_expected"].__setitem__(
             "rgba8_sha256", "0" * 64), "RGBA8 digest mismatch"),
        ("malformed-digest",
         lambda doc: doc["render_cases"][0]["output_expected"].__setitem__(
             "f32_sha256", "nope"), "malformed SHA-256 digest"),
        ("wrong-generator-digest",
         lambda doc: doc["provenance"]["generator"].__setitem__(
             "sha256", "0" * 64),
         "provenance.generator: recorded digest does not match"),
        ("wrong-materializer-digest",
         lambda doc: doc["provenance"]["native_include_generator"].__setitem__(
             "sha256", "0" * 64),
         "provenance.native_include_generator: recorded digest does not match"),
        ("wrong-factory-digest",
         lambda doc: doc["provenance"]["canonical_factory"].__setitem__(
             "sha256", "0" * 64), "canonical factory identity mismatch"),
        ("wrong-pinned-cpu-digest",
         lambda doc: doc["provenance"]["cpu_snapshot"]["pinned_files"]
         ["glsl_runtime"].__setitem__("sha256", "0" * 64),
         "pinned CPU file glsl_runtime mismatch"),
        ("recorded-absolute-path",
         lambda doc: doc["provenance"]["cpu_snapshot"].__setitem__(
             "argument", "/private/tmp/noisemaker-run/oracle/noisemaker-for-cpu"),
         "records an absolute filesystem path"),
        ("placeholder-drift",
         lambda doc: doc["provenance"]["cpu_snapshot"].__setitem__(
             "live_checkout_rejected", "the live checkout"),
         "must be recorded as stable placeholders"),
        ("wrong-source-digest",
         lambda doc: doc["provenance"]["source"].__setitem__("sha256", "0" * 64),
         "pinned GLSL source mismatch"),
        ("define-drift",
         lambda doc: doc["defines"].__setitem__("LOOP_A_OFFSET", 50),
         "define mismatch"),
        ("binding-census-drift",
         lambda doc: doc["runtime_binding_names"].append("palette"),
         "runtime binding census mismatch"),
        ("binding-abi-drift",
         lambda doc: doc["render_cases"][0]["bindings"]["seed"].__setitem__(
             "abi", "number"), "ABI drift"),
        ("non-int32-seed",
         lambda doc: doc["render_cases"][0]["bindings"]["seed"].__setitem__(
             "value", 2147483648), "int32 value required"),
        ("alpha-word-drift", _break_alpha_word, "alpha Float32 word at lane 3"),
        ("alpha-byte-drift", _break_alpha_byte, "alpha RGBA8 byte at lane 3"),
        ("crop-offset-drift",
         lambda doc: doc["render_cases"][1]["bindings"]["tileOffset"]
         .__setitem__("f32_words_le", ["0x40800000", "0x40000000"]),
         "tileOffset is not"),
        ("crop-full-route-digest",
         lambda doc: doc["crop_identity"]["full_route_expected"]["f32_words_le"]
         .__setitem__(0, "0x00000000"), "Float32 digest mismatch"),
        ("crop-row-shift", _shift_crop_row,
         "stored tile word differs from the top-down crop"),
        ("crop-vacuous-trap",
         lambda doc: doc["crop_identity"]["raw_crop_y_trap"].__setitem__(
             "changed_lane_count", 0), "raw crop_y trap is vacuous"),
        ("external-control-drift",
         lambda doc: doc["control_group"]["controls"][0].__setitem__(
             "observed", "differs"),
         "pass ledger disagrees with observation"),
        ("bound-time-control-drift",
         lambda doc: (
             doc["control_group"]["controls"][1].__setitem__("observed", "identical"),
             doc["control_group"]["controls"][1].__setitem__("pass", False)),
         "bound time did not change the output"),
        ("fabricated-control", _fabricate_control,
         "recorded observation 'identical' disagrees with the stored arrays"),
        ("wrong-geometry-control", _transpose_control_geometry,
         "control_group.external-pass-extreme.output.width: "
         "malformed dimension 5"),
        ("seed-census-disagreement",
         lambda doc: doc["seed_liveness_census"].__setitem__(
             "bound_seed_changes_output", True),
         "summary disagrees with the probe ledger"),
        ("mutant-census-drift",
         lambda doc: doc["mutation_ledger"].pop(), "mutant census mismatch"),
        ("mutant-non-discriminating",
         lambda doc: doc["mutation_ledger"][0]["results"][0].__setitem__(
             "differs", False), "did not discriminate"),
        ("mutant-control-changed",
         lambda doc: doc["mutation_ledger"][0]["results"][4].__setitem__(
             "differs", True), "non-reaching control"),
        ("self-test-ledger-drift",
         lambda doc: doc["comparer_self_tests"].__setitem__(
             "signed_zero_rejected_with_equal_rgba8", False),
         "comparer self-test mismatch"),
    )
    passed = 0
    with tempfile.TemporaryDirectory(prefix="shapes183-selftest-") as raw:
        root = pathlib.Path(raw)
        clean = _stage(root / "clean")
        load(clean)
        passed += 1
        for index, (label, mutate, fragment) in enumerate(scenarios):
            paths = _stage(root / f"case-{index:02d}")
            document = copy.deepcopy(base)
            mutate(document)
            _rewrite(paths, document)
            _expect_rejection(paths, fragment, label)
            passed += 1
        # Sidecar failures are file-level, not document-level.
        stale = _stage(root / "stale-sidecar")
        stale.oracle.write_bytes(stale.oracle.read_bytes() + b"\n")
        _expect_rejection(stale, "checksum sidecar drift", "stale-json-sidecar")
        passed += 1
        missing = _stage(root / "missing-sidecar")
        missing.oracle.with_suffix(missing.oracle.suffix + ".sha256").unlink()
        _expect_rejection(missing, "missing checked asset or sidecar",
                          "missing-json-sidecar")
        passed += 1
        generator_drift = _stage(root / "generator-sidecar")
        generator_drift.generator.write_bytes(
            generator_drift.generator.read_bytes() + b"\n")
        _expect_rejection(generator_drift, "checksum sidecar drift",
                          "stale-generator-sidecar")
        passed += 1
        report_drift = _stage(root / "report-sidecar")
        report_drift.report.write_bytes(report_drift.report.read_bytes() + b"\n")
        _expect_rejection(report_drift, "checksum sidecar drift",
                          "stale-report-sidecar")
        passed += 1
        broken_json = _stage(root / "broken-json")
        payload = b"{ this is not json"
        broken_json.oracle.write_bytes(payload)
        broken_json.oracle.with_suffix(
            broken_json.oracle.suffix + ".sha256").write_text(
                sidecar_text(broken_json.oracle, payload), encoding="utf-8")
        _expect_rejection(broken_json, "invalid Shapes183 JSON", "broken-json")
        passed += 1
    print(f"Shapes183 native oracle materializer self-test ok ({passed} checks)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    try:
        verify_sidecar(TOOL)
        if args.self_test:
            return self_test()
        expected = render(LIVE)
        if args.write:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(expected)
            OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(
                sidecar_text(OUTPUT, expected), encoding="utf-8")
        else:
            payload = verify_sidecar(OUTPUT)
            if payload != expected:
                raise OracleError(
                    "generated Shapes183 native include is stale")
    except (OSError, OracleError) as error:
        print(f"glslcpp: {error}", file=sys.stderr)
        return 1
    oracle, _ = load(LIVE)
    words = sum(len(case["output_expected"]["f32_words_le"])
                for case in oracle["render_cases"])
    print(f"Shapes183 native oracle include ok "
          f"({len(EXPECTED_CASES)} cases, {words} words, {words} bytes, "
          f"{len(MUTANTS)} mutants)")
    for control in oracle["control_group"]["controls"]:
        if control["pass"] is not True:
            print(f"glslcpp: NOTICE control {control['name']} expected "
                  f"{control['expectation']} but the shipped JavaScript is "
                  f"{control['observed']}; see seed_liveness_census",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
