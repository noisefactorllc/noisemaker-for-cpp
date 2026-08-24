#!/usr/bin/env python3
"""Generate the checked native Shape184 fixture from the canonical JS JSON.

This is the sole JSON-to-C++ materializer for `synth/shape:shape`. It never
renders anything: every expected word and byte originates in
`docs/port-engineering/shape-parity/shape-oracles.json`, which is produced by
the canonical JavaScript oracle generator. The materializer is fail-closed and
rejects missing or extra fields, duplicate case names, malformed dimensions,
counts, hex words or byte values, wrong digests, wrong or missing sidecars, and
truncated or extra arrays. `--self-test` proves each rejection.

Nothing recorded as prose is trusted. Every observation the document reports --
control identity, crop translation, seed and wrap liveness, and per-case mutant
discrimination -- is RE-DERIVED here from the stored arrays and digests, so a
hand-edited verdict with refreshed hashes cannot survive.
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
PACKAGE = ROOT / "docs/port-engineering/shape-parity"
OUTPUT = ROOT / "tests/oracles/shape_expected.inc"
TOOL = pathlib.Path(__file__).resolve()

SCHEMA = "noisemaker-for-cpp.shape184.pixel-parity.v1"
SCHEMA_VERSION = 1
PROGRAM_KEY = "synth/shape:shape"
EFFECT_KEY = "synth/shape"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
DEFINES = {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30}
FACTORY_NAME = "canonicalFactory274"
FACTORY_SHA256 = "870d97a811e5720f827f5616057483a43b27224240ac95c04a8084dd257a6125"
SOURCE_RELATIVE = (
    f"tools/glslcpp/corpus/{CORPUS_REVISION}"
    "/sources/synth/shape/shape.glsl")
SOURCE_BYTES = 15986
SOURCE_SHA256 = "d917d2027c873f05bc4183277a2b1dffe158c13cfd1281461580a31e0cd7d67f"
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

# The Python-side eligibility table, which `synth/shape:shape` must stay out of.
# Read from the LIVE `check_corpus` module, never transcribed: comparing one
# frozen copy against another frozen copy proves nothing, and would stay green
# if `synth/shape:shape` were ever added to the real table.
CORPUS_ADAPTER_SOURCE = "tools/glslcpp/check_corpus.py"
CORPUS_ADAPTER_CENSUS_EXPECTED = frozenset({
    "classicNoisedeck/fractal:fractal",
    "filter/historicPalette:historicPalette",
    "filter/palette:palette",
    "synth/julia:julia",
})


def live_corpus_adapter_keys() -> frozenset[str]:
    """Return `check_corpus._ADAPTERS` as the live module defines it."""
    directory = str(TOOL.parent)
    if directory not in sys.path:
        sys.path.insert(0, directory)
    try:
        import check_corpus  # noqa: PLC0415  (deliberately late and local)
    except ImportError as error:  # pragma: no cover - a missing sibling is fatal
        raise OracleError(
            f"cannot read {CORPUS_ADAPTER_SOURCE}: {error}") from error
    adapters = getattr(check_corpus, "_ADAPTERS", None)
    if not isinstance(adapters, frozenset) or not adapters:
        raise OracleError(
            f"{CORPUS_ADAPTER_SOURCE}: _ADAPTERS is not a non-empty frozenset")
    return adapters

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
    "loopAScale", "loopBScale", "speedA", "speedB",
)
BINDING_ABI = {
    "time": "number", "seed": "int32", "wrap": "bool", "resolution": "Vec2",
    "tileOffset": "Vec2", "fullResolution": "Vec2", "loopAScale": "number",
    "loopBScale": "number", "speedA": "number", "speedB": "number",
}
VEC_LANES = {"Vec2": 2}

# (name, width, height, route)
EXPECTED_CASES = (
    ("shape-landscape-16x9", 16, 9, "full"),
    ("shape-crop-1280x720", 40, 24, "tile"),
    ("shape-square-12", 12, 12, "full"),
    ("shape-portrait-9x16", 9, 16, "full"),
    ("shape-zero-speeds", 16, 9, "full"),
    ("shape-wrap-live-37-61", 4, 6, "tile"),
    ("shape-negative-speeds", 16, 9, "full"),
    ("shape-extreme-tile-offset", 16, 12, "tile"),
)
CASE_NAMES = tuple(name for name, _, _, _ in EXPECTED_CASES)
ANCHOR_CASE = "shape-landscape-16x9"
CROP_CASE = "shape-wrap-live-37-61"
GLOBALCOORD_CASE = "shape-extreme-tile-offset"

# The per-case, per-mutant discrimination ledger. A per-mutant summary is not
# sufficient: two cases with the same aspect ratio can differ in whether they
# discriminate, so every cell is frozen and every cell is checked.
MUTANT_DISCRIMINATION = {
    "shape-aspect-f32-narrowed": {
        "shape-landscape-16x9": True,
        "shape-crop-1280x720": True,
        "shape-square-12": False,
        "shape-portrait-9x16": False,
        "shape-zero-speeds": False,
        "shape-wrap-live-37-61": True,
        "shape-negative-speeds": True,
        "shape-extreme-tile-offset": False,
    },
    "shape-globalcoord-unnarrowed": {
        "shape-landscape-16x9": False,
        "shape-crop-1280x720": False,
        "shape-square-12": False,
        "shape-portrait-9x16": False,
        "shape-zero-speeds": False,
        "shape-wrap-live-37-61": False,
        "shape-negative-speeds": False,
        "shape-extreme-tile-offset": True,
    },
}
MUTANTS = tuple(MUTANT_DISCRIMINATION)

# (name, expectation). `bound-seed-123` and `bound-wrap-true` are recorded as
# proven INVARIANT, per shape-design.md section 4.2; they are not waived tests.
CONTROLS = (
    ("external-pass-extreme", "identical"),
    ("bound-time-ten", "differs"),
    ("bound-seed-123", "identical"),
    ("bound-wrap-true", "identical"),
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
    "oracle_authority", "mutable_global_contracts", "exactness_contract",
    "provenance", "comparer_self_tests", "coverage_axes", "render_cases",
    "crop_identity", "control_group", "seed_liveness_census",
    "wrap_liveness_census", "speed_sign_census", "globalcoord_witness_census",
    "globalcoord_native_binding_witness", "mutation_ledger",
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
        return self.package / "shape-oracles.json"

    @property
    def report(self) -> pathlib.Path:
        return self.package / "shape-oracle-report.md"

    @property
    def generator(self) -> pathlib.Path:
        return self.package / "shape_oracle_generator.mjs"


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


def packed_words(words: list[str]) -> bytes:
    return b"".join(struct.pack("<I", int(word, 16)) for word in words)


def validate_surface(record: object, width: int, height: int,
                     label: str) -> dict[str, Any]:
    surface = require_keys(record, SURFACE_KEYS, label)
    require_dimension(surface.get("width"), width, f"{label}.width")
    require_dimension(surface.get("height"), height, f"{label}.height")
    count = width * height * 4
    words = require_word_array(surface.get("f32_words_le"), count, label)
    rgba = require_byte_array(surface.get("rgba8_bytes"), count, label)
    if sha256(packed_words(words)) != require_hex64(surface.get("f32_sha256"),
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
            if struct.unpack("<f", struct.pack(
                    "<I", int(entry["f32_word_le"], 16)))[0] != entry["f32_value"]:
                raise OracleError(f"{field}: f32 word disagrees with its value")
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
            for lane, word in enumerate(entry["f32_words_le"]):
                if struct.unpack("<f", struct.pack(
                        "<I", int(word, 16)))[0] != values[lane]:
                    raise OracleError(
                        f"{field}: f32 word at lane {lane} disagrees with its value")
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
        "adapter_override_absent", "adapter_routed_keys", "corpus_adapter_keys",
        "corpus_adapter_source", "metadata"},
        "provenance")
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
    routed = provenance["adapter_routed_keys"]
    corpus_routed = provenance["corpus_adapter_keys"]
    if not isinstance(routed, list) or PROGRAM_KEY in routed:
        raise OracleError(
            "provenance: synth/shape:shape must be absent from the adapter table")
    if not isinstance(corpus_routed, list) or PROGRAM_KEY in corpus_routed:
        raise OracleError(
            "provenance: synth/shape:shape must be absent from the adapter table")
    # The authority is the live module, not this file and not the document.
    live_adapters = live_corpus_adapter_keys()
    if PROGRAM_KEY in live_adapters:
        raise OracleError(
            f"provenance: {PROGRAM_KEY} is present in the live "
            "check_corpus._ADAPTERS eligibility table")
    if live_adapters != CORPUS_ADAPTER_CENSUS_EXPECTED:
        raise OracleError(
            "provenance: live check_corpus._ADAPTERS census drift: "
            f"{sorted(live_adapters)}")
    if set(corpus_routed) != live_adapters:
        raise OracleError(
            "provenance: recorded corpus_adapter_keys disagree with the live "
            "check_corpus._ADAPTERS")
    adapter_source = require_keys(provenance["corpus_adapter_source"], {
        "relative_path_from_noisemaker_for_cpp", "parsed_from_live_source"},
        "provenance.corpus_adapter_source")
    if (adapter_source["relative_path_from_noisemaker_for_cpp"] != CORPUS_ADAPTER_SOURCE
            or adapter_source["parsed_from_live_source"] is not True):
        raise OracleError(
            "provenance.corpus_adapter_source: the eligibility table must be "
            "read from the live source")
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
    for label, value in (("argument", snapshot["argument"]),
                         ("live_checkout_rejected",
                          snapshot["live_checkout_rejected"]),
                         ("live_checkout_resolution",
                          snapshot["live_checkout_resolution"])):
        if not isinstance(value, str) or ABSOLUTE_PATH.search(value):
            raise OracleError(
                f"provenance.cpu_snapshot.{label}: absolute path recorded")
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


def validate_globals(oracle: dict[str, Any]) -> None:
    contracts = require_keys(oracle.get("mutable_global_contracts"), {
        "aspectRatio", "globalCoord", "shadowed_binding"},
        "mutable_global_contracts")
    for name, mutant, marker in (
            ("aspectRatio", "shape-aspect-f32-narrowed", "double"),
            ("globalCoord", "shape-globalcoord-unnarrowed", "f32")):
        entry = require_keys(contracts[name], {
            "javascript_declaration", "numeric_contract", "write_expression",
            "mutant", "oracle_discriminable"},
            f"mutable_global_contracts.{name}")
        if entry["mutant"] != mutant:
            raise OracleError(
                f"mutable_global_contracts.{name}: mutant identity mismatch")
        if entry["oracle_discriminable"] is not True:
            raise OracleError(
                f"mutable_global_contracts.{name}: contract is recorded as "
                "not discriminable")
        if marker not in entry["numeric_contract"]:
            raise OracleError(
                f"mutable_global_contracts.{name}: numeric contract drift")
    # The two globals must NOT share a contract; that is the whole point of the
    # program. A document that gives them the same one is rejected.
    if (contracts["aspectRatio"]["numeric_contract"]
            == contracts["globalCoord"]["numeric_contract"]):
        raise OracleError(
            "mutable_global_contracts: aspectRatio and globalCoord must carry "
            "different numeric contracts")


def validate_crop(oracle: dict[str, Any],
                  by_name: dict[str, Any]) -> dict[str, Any]:
    crop = require_keys(oracle.get("crop_identity"), {
        "case", "rect", "tile_offset_rule", "tile_offset_f32_words_le",
        "held_identical_bindings", "full_route_expected",
        "exact_word_mismatches", "exact_byte_mismatches", "exact",
        "raw_crop_y_trap", "production_shaped_case"}, "crop_identity")
    rect = require_keys(crop["rect"], {
        "crop_x", "crop_y", "tile_width", "tile_height", "full_width",
        "full_height"}, "crop_identity.rect")
    for key, value in rect.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise OracleError(f"crop_identity.rect: malformed {key}")
    if crop["case"] != CROP_CASE:
        raise OracleError("crop_identity: unexpected case")
    tile = by_name[CROP_CASE]
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
    # Re-derived from the stored arrays, never from the recorded counts.
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
    if rect["crop_y"] == rect["full_height"] - rect["crop_y"] - rect["tile_height"]:
        raise OracleError(
            "crop_identity: the raw crop_y trap is indistinguishable from the "
            "correct offset for this rectangle")
    validate_production_crop(crop, by_name)
    return crop


def validate_production_crop(crop: dict[str, Any],
                             by_name: dict[str, Any]) -> None:
    """Re-derive the production-scale crop from its stored 40x24 window.

    `st = globalCoord / fullResolution[1]` is two orders of magnitude larger
    here than in the 11x9 proof, so a translation defect that only appears at
    large fullResolution is caught only by this case. The whole 1280x720 route
    is not storable, but the window is, and it is compared lane by lane against
    the tile the case actually rendered.
    """
    label = "crop_identity.production_shaped_case"
    production = require_keys(crop["production_shaped_case"], {
        "case", "rect", "tile_offset_rule", "tile_offset_f32_words_le",
        "full_route_stored", "full_route_crop_window_stored",
        "full_route_dimensions", "full_route_f32_sha256",
        "full_route_rgba8_sha256", "full_route_crop_window",
        "exact_word_mismatches", "exact_byte_mismatches", "exact",
        "raw_crop_y_trap", "note"}, label)
    if production["case"] != "shape-crop-1280x720":
        raise OracleError(f"{label}: unexpected case")
    if production["full_route_stored"] is not False \
            or production["full_route_crop_window_stored"] is not True:
        raise OracleError(
            f"{label}: the crop window must be stored and the full route must "
            "not be")
    prod_rect = require_keys(production["rect"], {
        "crop_x", "crop_y", "tile_width", "tile_height", "full_width",
        "full_height"}, f"{label}.rect")
    for key, value in prod_rect.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise OracleError(f"{label}.rect: malformed {key}")
    if (prod_rect["crop_x"] + prod_rect["tile_width"] > prod_rect["full_width"]
            or prod_rect["crop_y"] + prod_rect["tile_height"]
            > prod_rect["full_height"]):
        raise OracleError(f"{label}: crop rectangle escapes the full surface")
    if production["full_route_dimensions"] != [prod_rect["full_width"],
                                               prod_rect["full_height"]]:
        raise OracleError(f"{label}: full route dimensions disagree with the rect")
    for field in ("full_route_f32_sha256", "full_route_rgba8_sha256"):
        require_hex64(production[field], f"{label}.{field}")
    prod_case = by_name[production["case"]]
    if (prod_case["width"] != prod_rect["tile_width"]
            or prod_case["height"] != prod_rect["tile_height"]):
        raise OracleError(f"{label}: tile dimensions disagree with the case")
    prod_expected = (float(prod_rect["crop_x"]),
                     float(prod_rect["full_height"] - prod_rect["crop_y"]
                           - prod_rect["tile_height"]))
    prod_actual = tuple(
        struct.unpack("<f", struct.pack("<I", int(word, 16)))[0]
        for word in prod_case["bindings"]["tileOffset"]["f32_words_le"])
    if prod_actual != prod_expected:
        raise OracleError(
            f"{label}: tileOffset is not "
            "(crop_x, full_height - crop_y - tile_height)")
    if require_word_array(production["tile_offset_f32_words_le"], 2,
                          f"{label}.tile_offset_f32_words_le") != \
            prod_case["bindings"]["tileOffset"]["f32_words_le"]:
        raise OracleError(f"{label}: recorded tileOffset words disagree")
    window = require_keys(production["full_route_crop_window"], {
        "width", "height", "source_origin_xy", "source_full_width",
        "f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256",
        "alpha_f32_word", "alpha_rgba8_byte"}, f"{label}.full_route_crop_window")
    require_dimension(window["width"], prod_rect["tile_width"],
                      f"{label}.full_route_crop_window.width")
    require_dimension(window["height"], prod_rect["tile_height"],
                      f"{label}.full_route_crop_window.height")
    if window["source_origin_xy"] != [prod_rect["crop_x"], prod_rect["crop_y"]] \
            or window["source_full_width"] != prod_rect["full_width"]:
        raise OracleError(
            f"{label}.full_route_crop_window: the window does not name the "
            "crop it was cut from")
    count = prod_rect["tile_width"] * prod_rect["tile_height"] * 4
    window_words = require_word_array(window["f32_words_le"], count,
                                      f"{label}.full_route_crop_window")
    window_bytes = require_byte_array(window["rgba8_bytes"], count,
                                      f"{label}.full_route_crop_window")
    if sha256(packed_words(window_words)) != require_hex64(
            window["f32_sha256"], f"{label}.full_route_crop_window.f32_sha256"):
        raise OracleError(
            f"{label}.full_route_crop_window: Float32 digest mismatch")
    if sha256(bytes(window_bytes)) != require_hex64(
            window["rgba8_sha256"],
            f"{label}.full_route_crop_window.rgba8_sha256"):
        raise OracleError(
            f"{label}.full_route_crop_window: RGBA8 digest mismatch")
    if (window["alpha_f32_word"] != ALPHA_WORD
            or window["alpha_rgba8_byte"] != ALPHA_BYTE):
        raise OracleError(f"{label}.full_route_crop_window: alpha contract mismatch")
    for index in range(3, count, 4):
        if window_words[index] != ALPHA_WORD or window_bytes[index] != ALPHA_BYTE:
            raise OracleError(
                f"{label}.full_route_crop_window: alpha drift at lane {index}")
    if (production["exact"] is not True
            or production["exact_word_mismatches"] != 0
            or production["exact_byte_mismatches"] != 0):
        raise OracleError(f"{label}: tile is not an exact top-down crop")
    # The re-derivation itself: the stored window, cut from a 1280x720 render,
    # must equal the tile the case rendered through the tile route.
    tile_words = prod_case["output_expected"]["f32_words_le"]
    tile_bytes = prod_case["output_expected"]["rgba8_bytes"]
    for index in range(count):
        if tile_words[index] != window_words[index]:
            raise OracleError(
                f"{label}: stored tile word differs from the production-scale "
                f"top-down crop at lane {index}")
        if tile_bytes[index] != window_bytes[index]:
            raise OracleError(
                f"{label}: stored tile byte differs from the production-scale "
                f"top-down crop at lane {index}")
    trap = require_keys(production["raw_crop_y_trap"], {
        "tile_offset_f32_words_le", "differs_from_correct_tile",
        "changed_lane_count", "first_mismatch"}, f"{label}.raw_crop_y_trap")
    if trap["differs_from_correct_tile"] is not True \
            or trap["changed_lane_count"] < 1:
        raise OracleError(f"{label}: raw crop_y trap is vacuous")


def validate_controls(oracle: dict[str, Any],
                      by_name: dict[str, Any]) -> dict[str, Any]:
    group = require_keys(oracle.get("control_group"), {
        "anchor", "baseline", "controls"}, "control_group")
    if group["anchor"] != ANCHOR_CASE:
        raise OracleError("control_group: unexpected anchor")
    baseline = require_keys(group["baseline"], {
        "external_pass", "f32_sha256", "rgba8_sha256"}, "control_group.baseline")
    anchor_case = by_name.get(group["anchor"])
    if not isinstance(anchor_case, dict):
        raise OracleError("control_group: anchor case is absent")
    anchor_surface = anchor_case["output_expected"]
    if (baseline["f32_sha256"] != anchor_surface["f32_sha256"]
            or baseline["rgba8_sha256"] != anchor_surface["rgba8_sha256"]):
        raise OracleError(
            "control_group.baseline: digests disagree with the anchor case")
    controls = group["controls"]
    if not isinstance(controls, list) or len(controls) != len(CONTROLS):
        raise OracleError("control_group: control census mismatch")
    # Do not trust the stored `observed` string: the baseline arrays are in the
    # same document, so every control's relation to the anchor is re-derived
    # from the arrays themselves. A hand-edited control with refreshed digests
    # must not survive.
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
        if entry["pass"] is not True:
            raise OracleError(f"{label}: control did not pass")
        validate_bindings(entry["bindings"], f"{label}.bindings")
        validate_external(entry["external_pass"], f"{label}.external_pass")
        output = entry["output"]
        if not isinstance(output, dict):
            raise OracleError(f"{label}: output record required")
        # The anchor's own geometry, never the record's self-reported
        # dimensions: a self-consistent control of another shape -- including a
        # transpose with an identical lane count -- is not a one-axis variant
        # of the anchor.
        surface = validate_surface(output, anchor_case["width"],
                                   anchor_case["height"], f"{label}.output")
        identical = (surface["f32_words_le"] == anchor_surface["f32_words_le"]
                     and surface["rgba8_bytes"] == anchor_surface["rgba8_bytes"])
        derived.append("identical" if identical else "differs")
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
        expected_zero = observation == "identical"
        if (control["changed_lane_count"] == 0) is not expected_zero:
            raise OracleError(
                f"control_group.{name}: changed lane count disagrees with the arrays")
    return group


def validate_seed_census(oracle: dict[str, Any], group: dict[str, Any],
                         by_name: dict[str, Any]) -> None:
    census = require_keys(oracle.get("seed_liveness_census"), {
        "probe_case", "probes", "bound_seed_changes_output", "consumers",
        "reason", "design_agreement"}, "seed_liveness_census")
    if census["probe_case"] != ANCHOR_CASE:
        raise OracleError("seed_liveness_census: unexpected probe case")
    anchor_digest = by_name[ANCHOR_CASE]["output_expected"]["f32_sha256"]
    probes = census["probes"]
    if not isinstance(probes, list) or len(probes) < 2:
        raise OracleError("seed_liveness_census: probe census mismatch")
    if not isinstance(census["consumers"], list) or not census["consumers"]:
        raise OracleError("seed_liveness_census: consumer inventory required")
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
        # Re-derived: an invariant probe must carry the anchor's own digest.
        digest_matches = entry["f32_sha256"] == anchor_digest
        if entry["differs_from_baseline"] is digest_matches:
            raise OracleError(
                f"seed_liveness_census: probe seed {entry['seed']} reports "
                f"differs_from_baseline={entry['differs_from_baseline']} but "
                "its digest says otherwise")
    observed = any(probe["differs_from_baseline"] for probe in probes)
    if census["bound_seed_changes_output"] is not observed:
        raise OracleError(
            "seed_liveness_census: summary disagrees with the probe ledger")
    if observed:
        raise OracleError(
            "seed_liveness_census: bound seed is recorded as invariant at "
            "defines 40/30 but a probe differs")
    seed_control = next(control for control in group["controls"]
                        if control["name"] == "bound-seed-123")
    if (seed_control["observed"] == "differs") is not observed:
        raise OracleError(
            "seed_liveness_census: bound-seed control disagrees with the census")


def validate_wrap_census(oracle: dict[str, Any],
                         by_name: dict[str, Any]) -> None:
    census = require_keys(oracle.get("wrap_liveness_census"), {
        "probes", "rule", "invariant_witness", "live_witness"},
        "wrap_liveness_census")
    if census["invariant_witness"] != ANCHOR_CASE or census["live_witness"] != CROP_CASE:
        raise OracleError("wrap_liveness_census: witness identity mismatch")
    probes = census["probes"]
    if not isinstance(probes, list) or len(probes) != 2:
        raise OracleError("wrap_liveness_census: probe census mismatch")
    for probe in probes:
        entry = require_keys(probe, {
            "case", "bound_wrap", "loop_a_scale", "loop_b_scale", "lf_a", "lf_b",
            "lf_a_is_integral", "lf_b_is_integral", "flip_differs",
            "changed_lane_count", "f32_sha256"}, "wrap_liveness_census.probes")
        case = by_name.get(entry["case"])
        if case is None:
            raise OracleError(
                f"wrap_liveness_census: unknown case {entry['case']}")
        if entry["bound_wrap"] is not case["bindings"]["wrap"]["value"]:
            raise OracleError(
                f"wrap_liveness_census: {entry['case']} bound wrap disagrees "
                "with the case binding")
        for field, scale in (("lf_a", entry["loop_a_scale"]),
                             ("lf_b", entry["loop_b_scale"])):
            expected = 6 + (1 - 6) * (scale - 1) / (100 - 1)
            if entry[field] != expected:
                raise OracleError(
                    f"wrap_liveness_census: {entry['case']} {field} is not "
                    "map(loopScale, 1, 100, 6, 1)")
        if entry["lf_a_is_integral"] is not float(entry["lf_a"]).is_integer() \
                or entry["lf_b_is_integral"] is not float(entry["lf_b"]).is_integer():
            raise OracleError(
                f"wrap_liveness_census: {entry['case']} integrality drift")
        # Re-derived: an invariant flip must carry the case's own digest.
        digest_matches = entry["f32_sha256"] == case["output_expected"]["f32_sha256"]
        if entry["flip_differs"] is digest_matches:
            raise OracleError(
                f"wrap_liveness_census: {entry['case']} reports "
                f"flip_differs={entry['flip_differs']} but its digest says otherwise")
        if entry["flip_differs"] and entry["changed_lane_count"] < 1:
            raise OracleError(
                f"wrap_liveness_census: {entry['case']} changed lane count "
                "disagrees with the flip")
    invariant = next(p for p in probes if p["case"] == ANCHOR_CASE)
    live = next(p for p in probes if p["case"] == CROP_CASE)
    if not (invariant["lf_a_is_integral"] and invariant["lf_b_is_integral"]) \
            or invariant["flip_differs"]:
        raise OracleError("wrap_liveness_census: the invariant witness is not invariant")
    if (live["lf_a_is_integral"] or live["lf_b_is_integral"]) or not live["flip_differs"]:
        raise OracleError("wrap_liveness_census: the live witness is not live")


def validate_speed_census(oracle: dict[str, Any],
                          by_name: dict[str, Any]) -> None:
    census = require_keys(oracle.get("speed_sign_census"), {
        "probe_case", "probes", "distinct_digest_count", "rule"},
        "speed_sign_census")
    if census["probe_case"] != ANCHOR_CASE:
        raise OracleError("speed_sign_census: unexpected probe case")
    probes = census["probes"]
    if not isinstance(probes, list) or len(probes) != 9:
        raise OracleError("speed_sign_census: probe census mismatch")
    anchor = by_name[ANCHOR_CASE]
    anchor_speed_a = anchor["bindings"]["speedA"]["f32_value"]
    anchor_speed_b = anchor["bindings"]["speedB"]["f32_value"]
    signs = set()
    digests = set()
    for probe in probes:
        entry = require_keys(probe, {"speedA", "speedB", "f32_sha256"},
                             "speed_sign_census.probes")
        for field in ("speedA", "speedB"):
            if not isinstance(entry[field], (int, float)) or isinstance(
                    entry[field], bool):
                raise OracleError(f"speed_sign_census: malformed {field}")
        key = (entry["speedA"], entry["speedB"])
        if key in signs:
            raise OracleError("speed_sign_census: duplicate speed combination")
        signs.add(key)
        digests.add(require_hex64(entry["f32_sha256"], "speed_sign_census.probes"))
        # Re-derived: the combination that matches the anchor must reproduce it.
        if key == (anchor_speed_a, anchor_speed_b) and \
                entry["f32_sha256"] != anchor["output_expected"]["f32_sha256"]:
            raise OracleError(
                "speed_sign_census: the anchor's own speed combination does not "
                "reproduce the anchor output")
    expected_signs = {(a, b) for a in (-50, 0, 50) for b in (-50, 0, 50)}
    if signs != expected_signs:
        raise OracleError("speed_sign_census: sign/zero matrix is incomplete")
    if census["distinct_digest_count"] != len(digests):
        raise OracleError("speed_sign_census: distinct digest count disagrees")
    if len(digests) != len(probes):
        raise OracleError(
            "speed_sign_census: two speed sign/zero combinations collapsed")


def validate_globalcoord(oracle: dict[str, Any],
                         by_name: dict[str, Any]) -> dict[str, Any]:
    census = require_keys(oracle.get("globalcoord_witness_census"), {
        "probe_geometry", "probes", "rule"}, "globalcoord_witness_census")
    geometry = require_keys(census["probe_geometry"], {
        "width", "height", "full_resolution"},
        "globalcoord_witness_census.probe_geometry")
    if geometry["width"] <= 0 or geometry["height"] <= 0:
        raise OracleError("globalcoord_witness_census: malformed probe geometry")
    probes = census["probes"]
    if not isinstance(probes, list) or len(probes) < 3:
        raise OracleError("globalcoord_witness_census: probe census mismatch")
    seen = set()
    discriminating = 0
    for probe in probes:
        entry = require_keys(probe, {
            "tile_offset", "tile_offset_f32_words_le", "discriminates",
            "changed_lane_count"}, "globalcoord_witness_census.probes")
        offset = entry["tile_offset"]
        if not isinstance(offset, list) or len(offset) != 2:
            raise OracleError("globalcoord_witness_census: malformed tile offset")
        key = tuple(offset)
        if key in seen:
            raise OracleError("globalcoord_witness_census: duplicate tile offset")
        seen.add(key)
        require_word_array(entry["tile_offset_f32_words_le"], 2,
                           "globalcoord_witness_census.probes")
        if entry["discriminates"] is not (entry["changed_lane_count"] > 0):
            raise OracleError(
                "globalcoord_witness_census: verdict disagrees with the lane count")
        if entry["discriminates"]:
            discriminating += 1
    if discriminating == 0:
        raise OracleError(
            "globalcoord_witness_census: no tile offset discriminates the contract")
    if probes[0]["tile_offset"] != [0, 0] or probes[0]["discriminates"]:
        raise OracleError(
            "globalcoord_witness_census: the zero-offset control is missing or "
            "discriminates")

    witness = require_keys(oracle.get("globalcoord_native_binding_witness"), {
        "case", "width", "height", "tile_offset_f32_words_le",
        "probe_anchor_sha256", "probe_replacement_sha256",
        "probe_factory_sha256", "classification", "lane_order", "f32_words_le",
        "f32_sha256", "native_expression", "purpose"},
        "globalcoord_native_binding_witness")
    if witness["case"] != GLOBALCOORD_CASE:
        raise OracleError("globalcoord_native_binding_witness: unexpected case")
    case = by_name[GLOBALCOORD_CASE]
    require_dimension(witness["width"], case["width"],
                      "globalcoord_native_binding_witness.width")
    require_dimension(witness["height"], case["height"],
                      "globalcoord_native_binding_witness.height")
    lanes = require_word_array(witness["f32_words_le"],
                               case["width"] * case["height"] * 2,
                               "globalcoord_native_binding_witness")
    if sha256(packed_words(lanes)) != require_hex64(
            witness["f32_sha256"], "globalcoord_native_binding_witness.f32_sha256"):
        raise OracleError(
            "globalcoord_native_binding_witness: Float32 digest mismatch")
    if witness["tile_offset_f32_words_le"] != \
            case["bindings"]["tileOffset"]["f32_words_le"]:
        raise OracleError(
            "globalcoord_native_binding_witness: tileOffset words disagree with "
            "the case binding")
    for field in ("probe_anchor_sha256", "probe_replacement_sha256",
                  "probe_factory_sha256"):
        require_hex64(witness[field], f"globalcoord_native_binding_witness.{field}")
    if "NOT a parity array" not in witness["classification"]:
        raise OracleError(
            "globalcoord_native_binding_witness: the probe must be labelled as "
            "not a parity array")
    return witness


def validate_mutations(oracle: dict[str, Any],
                       by_name: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = oracle.get("mutation_ledger")
    if not isinstance(ledger, list) or tuple(
            item.get("name") for item in ledger) != MUTANTS:
        raise OracleError("mutation_ledger: mutant census mismatch")
    contract = require_keys(oracle.get("mutation_discrimination_contract"), {
        "per_case", "rule", "disjoint_witness_requirement", "witness_sets",
        "expected"}, "mutation_discrimination_contract")
    if contract["per_case"] is not True:
        raise OracleError(
            "mutation_discrimination_contract: discrimination must be per case")
    if contract["expected"] != MUTANT_DISCRIMINATION:
        raise OracleError(
            "mutation_discrimination_contract: the per-case discrimination "
            "ledger does not match the frozen table")
    if "DISJOINT" not in contract["disjoint_witness_requirement"]:
        raise OracleError(
            "mutation_discrimination_contract: the disjoint-witness requirement "
            "must be stated, not merely enforced")
    witness_sets = require_keys(contract["witness_sets"], set(MUTANTS),
                                "mutation_discrimination_contract.witness_sets")
    for name in MUTANTS:
        entry = require_keys(witness_sets[name], {
            "witness_cases", "control_cases"},
            f"mutation_discrimination_contract.witness_sets.{name}")
        table = MUTANT_DISCRIMINATION[name]
        if entry["witness_cases"] != [case for case in CASE_NAMES if table[case]] \
                or entry["control_cases"] != [case for case in CASE_NAMES
                                              if not table[case]]:
            raise OracleError(
                f"mutation_discrimination_contract.witness_sets.{name}: "
                "disagrees with the frozen per-case table")
    for mutant in ledger:
        label = f"mutation_ledger.{mutant.get('name')}"
        entry = require_keys(mutant, {
            "name", "target", "contract", "reaching", "classification",
            "anchor_sha256", "replacement_sha256", "mutated_factory_sha256",
            "anchor_occurrences", "witness_cases", "control_cases", "results"},
            label)
        if entry["anchor_occurrences"] != 1:
            raise OracleError(f"{label}: anchor is not unique")
        for field in ("anchor_sha256", "replacement_sha256",
                      "mutated_factory_sha256"):
            require_hex64(entry[field], f"{label}.{field}")
        table = MUTANT_DISCRIMINATION[entry["name"]]
        results = entry["results"]
        if not isinstance(results, list) or tuple(
                item.get("case") for item in results) != CASE_NAMES:
            raise OracleError(f"{label}: result census mismatch")
        witnesses: list[str] = []
        controls: list[str] = []
        for result in results:
            row = require_keys(result, {
                "case", "expected_discriminates", "differs",
                "changed_lane_count", "changed_rgba8_byte_count", "f32_sha256",
                "rgba8_sha256", "first_mismatch"},
                f"{label}.{result.get('case')}")
            expected = table[row["case"]]
            if row["expected_discriminates"] is not expected:
                raise OracleError(
                    f"{label}: {row['case']} carries the wrong per-case "
                    "expectation")
            if row["differs"] is not expected:
                raise OracleError(
                    f"{label}: case {row['case']} expected "
                    f"discriminates={expected} but the ledger records "
                    f"{row['differs']}")
            require_hex64(row["f32_sha256"], f"{label}.{row['case']}.f32_sha256")
            require_hex64(row["rgba8_sha256"], f"{label}.{row['case']}.rgba8_sha256")
            # Re-derived from the case's own stored digests: a non-discriminating
            # mutant render is byte-identical to the canonical one, and a
            # discriminating render is not.
            canonical = by_name[row["case"]]["output_expected"]
            digest_matches = (row["f32_sha256"] == canonical["f32_sha256"]
                              and row["rgba8_sha256"] == canonical["rgba8_sha256"])
            if row["differs"] is digest_matches:
                raise OracleError(
                    f"{label}: case {row['case']} records "
                    f"differs={row['differs']} but its mutant digests say "
                    "otherwise")
            if expected and (row["changed_lane_count"] < 1
                             or row["first_mismatch"] is None):
                raise OracleError(
                    f"{label}: witness case {row['case']} did not discriminate")
            if not expected and (row["changed_lane_count"] != 0
                                 or row["changed_rgba8_byte_count"] != 0
                                 or row["first_mismatch"] is not None):
                raise OracleError(
                    f"{label}: non-reaching control {row['case']} changed")
            (witnesses if expected else controls).append(row["case"])
        if entry["witness_cases"] != witnesses or entry["control_cases"] != controls:
            raise OracleError(f"{label}: witness/control partition drift")
        if not witnesses:
            raise OracleError(f"{label}: no case witnesses this mutant")
    # Each of the two numeric contracts must own at least one case that the
    # other does not, or the pair proves one contract twice.
    aspect = set(MUTANT_DISCRIMINATION["shape-aspect-f32-narrowed"])
    aspect_witnesses = {name for name in aspect
                        if MUTANT_DISCRIMINATION["shape-aspect-f32-narrowed"][name]}
    global_witnesses = {name for name in aspect
                        if MUTANT_DISCRIMINATION["shape-globalcoord-unnarrowed"][name]}
    if not aspect_witnesses or not global_witnesses:
        raise OracleError("mutation_ledger: a numeric contract has no witness")
    if aspect_witnesses & global_witnesses:
        raise OracleError(
            "mutation_ledger: the two contracts must not share a witness case; "
            "a shared case cannot attribute a divergence to one of them")
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
            "Shape184 oracle records an absolute filesystem path "
            f"({leaked.group(0)!r}); the gate must be path-independent")
    try:
        oracle = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OracleError(f"invalid Shape184 JSON: {error}") from error
    require_keys(oracle, TOP_LEVEL_KEYS, "oracle")
    if (oracle["schema"], oracle["schema_version"], oracle["program_key"],
            oracle["effect_key"], oracle["runtime_key"],
            oracle["corpus_revision"]) != (
                SCHEMA, SCHEMA_VERSION, PROGRAM_KEY, EFFECT_KEY, PROGRAM_KEY,
                CORPUS_REVISION):
        raise OracleError("Shape184 schema/program identity mismatch")
    if oracle["defines"] != DEFINES:
        raise OracleError("Shape184 define mismatch")
    if tuple(oracle["runtime_binding_names"]) != BINDING_NAMES:
        raise OracleError("Shape184 runtime binding census mismatch")
    if oracle["runtime_binding_abi"] != BINDING_ABI:
        raise OracleError("Shape184 runtime binding ABI mismatch")
    if oracle["compile_time_defines_are_not_bindings"] is not True:
        raise OracleError("Shape184 compile-time define contract mismatch")
    validate_provenance(oracle, paths)
    validate_globals(oracle)
    self_tests = oracle.get("comparer_self_tests")
    if not isinstance(self_tests, dict) or any(
            self_tests.get(name) is not True for name in REQUIRED_SELF_TESTS):
        raise OracleError("Shape184 comparer self-test mismatch")
    cases = oracle.get("render_cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise OracleError("Shape184 fixture count mismatch")
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
        tile_offset = tuple(entry["bindings"]["tileOffset"]["f32_values"])
        if (route == "full") is not (tile_offset == (0.0, 0.0)):
            raise OracleError(f"{name}: route label disagrees with tileOffset")
        validate_identity(entry["canonical_repeat"], f"{name}.canonical_repeat")
        validate_identity(entry["public_canonical"], f"{name}.public_canonical")
    by_name = {case["name"]: case for case in cases}
    validate_crop(oracle, by_name)
    group = validate_controls(oracle, by_name)
    validate_seed_census(oracle, group, by_name)
    validate_wrap_census(oracle, by_name)
    validate_speed_census(oracle, by_name)
    validate_globalcoord(oracle, by_name)
    validate_mutations(oracle, by_name)
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
    witness = oracle["globalcoord_native_binding_witness"]
    lines = [
        "// Generated from the checked canonical JavaScript Shape184 oracle.",
        "// Do not edit; C++ output never participates in these expected arrays.",
        "//",
        "// synth/shape carries two mutable file-scope globals with different",
        "// numeric contracts: `aspectRatio` is a double and is never narrowed to",
        "// f32, while `globalCoord` is a Float32Array whose every lane store",
        "// narrows. Both are witnessed here; see kMutantWitnesses.",
        "#pragma once", "", "namespace shape184_oracle {", "",
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
    production = crop["production_shaped_case"]
    window = production["full_route_crop_window"]
    lines.extend([
        "// The 40x24 window cut out of a full 1280x720 render. The full route is",
        "// not storable; the window is, and it is the production-scale proof of",
        "// the top-down crop translation, where st = globalCoord /",
        "// fullResolution[1] is two orders of magnitude larger than in the 11x9",
        "// proof above.",
    ])
    lines.append(
        f"inline constexpr std::array<std::uint32_t, "
        f"{len(window['f32_words_le'])}> kProductionCropWindowWords{{{{")
    lines.extend(array_lines(window["f32_words_le"], "U", 8))
    lines.extend(["}};", ""])
    lines.append(
        f"inline constexpr std::array<std::uint8_t, "
        f"{len(window['rgba8_bytes'])}> kProductionCropWindowRgba8{{{{")
    lines.extend(array_lines(window["rgba8_bytes"], "U", 16))
    lines.extend(["}};", ""])
    lines.extend([
        "// globalCoord.x / globalCoord.y per pixel, top-down, for the",
        "// shape-extreme-tile-offset case. Produced by an instrumented probe",
        "// factory, NOT by a parity render: it exists so the f32-lane contract",
        "// on globalCoord has a native witness through the real binding ABI.",
    ])
    lines.append(
        f"inline constexpr std::array<std::uint32_t, "
        f"{len(witness['f32_words_le'])}> kGlobalCoordWitnessWords{{{{")
    lines.extend(array_lines(witness["f32_words_le"], "U", 8))
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
        "// The production-scale crop proof. `window_expected_*` is the 40x24",
        "// window cut from a full 1280x720 render -- NOT a full route -- so it",
        "// is index-aligned with the tile array and compared lane for lane.",
        "struct ProductionCropProofView {",
        "  std::string_view tile_case;",
        "  std::size_t crop_x;",
        "  std::size_t crop_y;",
        "  std::size_t tile_width;",
        "  std::size_t tile_height;",
        "  std::size_t full_width;",
        "  std::size_t full_height;",
        "  std::array<std::uint32_t, 2> tile_offset_words;",
        "  std::span<const std::uint32_t> window_expected_words;",
        "  std::span<const std::uint8_t> window_expected_rgba8;",
        "};", "",
        "// The two contracts must have disjoint witness sets: a case that",
        "// witnessed both could not attribute a divergence to one of them.",
        "struct MutantSetView {",
        "  std::string_view mutant;",
        "  std::span<const std::string_view> witness_cases;",
        "  std::span<const std::string_view> control_cases;",
        "};", "",
        "struct GlobalCoordWitnessView {",
        "  std::string_view tile_case;",
        "  std::size_t width;",
        "  std::size_t height;",
        "  std::array<std::uint32_t, 2> tile_offset_words;",
        "  std::span<const std::uint32_t> expected_lane_words;",
        "};", "",
        "// One row per mutant per case: the frozen per-case discrimination",
        "// ledger. A per-mutant summary is deliberately not materialized.",
        "struct MutantWitnessView {",
        "  std::string_view mutant;",
        "  std::string_view tile_case;",
        "  bool discriminates;",
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
            f'{external["time"]["f32_word_le"]}U, '
            f'{external["seed"]["f32_word_le"]}U}},')
    rect = crop["rect"]
    ledger_rows = [(mutant["name"], result["case"], result["differs"])
                   for mutant in oracle["mutation_ledger"]
                   for result in mutant["results"]]
    lines.extend([
        "}};", "",
        "inline constexpr CropProofView kCropProof{",
        f'    "{crop["case"]}", {rect["crop_x"]}U, {rect["crop_y"]}U, '
        f'{rect["tile_width"]}U, {rect["tile_height"]}U, '
        f'{rect["full_width"]}U, {rect["full_height"]}U,',
        f'    {{{word_list(crop["tile_offset_f32_words_le"])}}}, '
        "kCropFullExpectedWords, kCropFullExpectedRgba8,",
        "};", "",
        "inline constexpr ProductionCropProofView kProductionCropProof{",
        f'    "{production["case"]}", {production["rect"]["crop_x"]}U, '
        f'{production["rect"]["crop_y"]}U, {production["rect"]["tile_width"]}U, '
        f'{production["rect"]["tile_height"]}U, '
        f'{production["rect"]["full_width"]}U, '
        f'{production["rect"]["full_height"]}U,',
        f'    {{{word_list(production["tile_offset_f32_words_le"])}}}, '
        "kProductionCropWindowWords, kProductionCropWindowRgba8,",
        "};", "",
        "inline constexpr GlobalCoordWitnessView kGlobalCoordWitness{",
        f'    "{witness["case"]}", {witness["width"]}U, {witness["height"]}U,',
        f'    {{{word_list(witness["tile_offset_f32_words_le"])}}}, '
        "kGlobalCoordWitnessWords,",
        "};", "",
        f"inline constexpr std::array<MutantWitnessView, {len(ledger_rows)}> "
        "kMutantWitnesses{{",
    ])
    for mutant_name, case_name, differs in ledger_rows:
        lines.append(f'  MutantWitnessView{{"{mutant_name}", "{case_name}", '
                     f'{str(differs).lower()}}},')
    lines.append("}};")
    lines.append("")
    for index, mutant in enumerate(oracle["mutation_ledger"]):
        for kind, names in (("Witness", mutant["witness_cases"]),
                            ("Control", mutant["control_cases"])):
            lines.append(
                f"inline constexpr std::array<std::string_view, {len(names)}> "
                f"kMutant{index}{kind}Cases{{{{")
            lines.append("    " + ", ".join(f'"{name}"' for name in names) + ",")
            lines.extend(["}};", ""])
    lines.append(
        f"inline constexpr std::array<MutantSetView, "
        f"{len(oracle['mutation_ledger'])}> kMutantSets{{{{")
    for index, mutant in enumerate(oracle["mutation_ledger"]):
        lines.append(f'  MutantSetView{{"{mutant["name"]}", '
                     f'kMutant{index}WitnessCases, kMutant{index}ControlCases}},')
    lines.extend([
        "}};", "",
        f'inline constexpr std::uint32_t kAlphaWord = {ALPHA_WORD}U;',
        f"inline constexpr std::uint8_t kAlphaByte = {ALPHA_BYTE}U;", "",
        "}  // namespace shape184_oracle", "",
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
    for name in ("shape-oracles.json", "shape-oracle-report.md",
                 "shape_oracle_generator.mjs"):
        shutil.copy2(PACKAGE / name, package / name)
        shutil.copy2(PACKAGE / f"{name}.sha256", package / f"{name}.sha256")
    return Paths(package=package, tool=TOOL, output=destination / "out.inc")


def _rewrite(paths: Paths, oracle: dict[str, Any]) -> None:
    payload = (json.dumps(oracle, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    paths.oracle.write_bytes(payload)
    paths.oracle.with_suffix(paths.oracle.suffix + ".sha256").write_text(
        sidecar_text(paths.oracle, payload), encoding="utf-8")


def _refresh_surface_digests(surface: dict[str, Any]) -> None:
    surface["f32_sha256"] = sha256(packed_words(surface["f32_words_le"]))
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
    tile = next(case for case in doc["render_cases"] if case["name"] == CROP_CASE)
    tile["bindings"]["tileOffset"]["f32_words_le"] = shifted
    tile["bindings"]["tileOffset"]["f32_values"] = [
        float(rect["crop_x"]),
        float(rect["full_height"] - rect["crop_y"] - rect["tile_height"])]


def _bind_raw_crop_y(doc: dict[str, Any]) -> None:
    """Bind raw top-down `crop_y` into tileOffset.y, self-consistently.

    Words and values are kept in agreement, so the earlier word/value check
    cannot fire; only the crop translation rule can reject it.
    """
    rect = doc["crop_identity"]["rect"]
    offset = (float(rect["crop_x"]), float(rect["crop_y"]))
    words = [f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"
             for value in offset]
    tile = next(case for case in doc["render_cases"] if case["name"] == CROP_CASE)
    tile["bindings"]["tileOffset"]["f32_words_le"] = words
    tile["bindings"]["tileOffset"]["f32_values"] = list(offset)
    doc["crop_identity"]["tile_offset_f32_words_le"] = words


def _forge_production_window(doc: dict[str, Any]) -> None:
    """Rewrite one window lane and refresh its digest.

    The window stays internally consistent, so only comparing it against the
    tile the case actually rendered can reject it. This is the production-scale
    analogue of `_shift_crop_row`.
    """
    window = doc["crop_identity"]["production_shaped_case"]["full_route_crop_window"]
    window["f32_words_le"][0] = "0x7f7fffff"
    window["rgba8_bytes"][0] = 7
    window["f32_sha256"] = sha256(packed_words(window["f32_words_le"]))
    window["rgba8_sha256"] = sha256(bytes(window["rgba8_bytes"]))


def _fabricate_control(doc: dict[str, Any]) -> None:
    """Swap a lane of the `identical` external control for a foreign value.

    Both digests are refreshed and `observed` is left saying "identical", so
    only the independent re-derivation against the anchor case's own baseline
    arrays can reject it.
    """
    surface = doc["control_group"]["controls"][0]["output"]
    surface["f32_words_le"][0] = "0x7f7fffff"
    surface["rgba8_bytes"][0] = 7
    _refresh_surface_digests(surface)


def _transpose_control_geometry(doc: dict[str, Any]) -> None:
    """Reshape the external control from 16x9 to 9x16.

    The lane count, both digests, and the alpha stride are all unchanged, so
    only comparing against the anchor case's own width/height can reject it.
    """
    surface = doc["control_group"]["controls"][0]["output"]
    surface["width"], surface["height"] = surface["height"], surface["width"]


def _fabricate_seed_probe(doc: dict[str, Any]) -> None:
    """Claim a seed probe is invariant while giving it a foreign digest."""
    doc["seed_liveness_census"]["probes"][2]["f32_sha256"] = "b" * 64


def _fabricate_wrap_probe(doc: dict[str, Any]) -> None:
    """Claim the wrap flip on the live witness is identical."""
    probe = next(item for item in doc["wrap_liveness_census"]["probes"]
                 if item["case"] == CROP_CASE)
    probe["flip_differs"] = False
    probe["changed_lane_count"] = 0


def _fabricate_mutant_digest(doc: dict[str, Any]) -> None:
    """Give a witness row the canonical case's own digests.

    Every verdict field still agrees with the frozen per-case table, so the
    row's claim to have discriminated can only be refuted by re-deriving it
    from the digests it carries.
    """
    ledger = doc["mutation_ledger"][0]
    row = next(item for item in ledger["results"]
               if item["case"] == ANCHOR_CASE)
    canonical = next(case for case in doc["render_cases"]
                     if case["name"] == ANCHOR_CASE)["output_expected"]
    row["f32_sha256"] = canonical["f32_sha256"]
    row["rgba8_sha256"] = canonical["rgba8_sha256"]


def _collapse_speed_census(doc: dict[str, Any]) -> None:
    probes = doc["speed_sign_census"]["probes"]
    probes[1]["f32_sha256"] = probes[2]["f32_sha256"]


def _truncate_globalcoord_witness(doc: dict[str, Any]) -> None:
    witness = doc["globalcoord_native_binding_witness"]
    witness["f32_words_le"].pop()
    witness["f32_sha256"] = sha256(packed_words(witness["f32_words_le"]))


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
         lambda doc: doc["render_cases"][0]["bindings"]["tileOffset"]
         .__setitem__("f32_words_le", ["0x00000000", "0x1"]),
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
        ("binding-word-value-disagreement",
         lambda doc: doc["render_cases"][0]["bindings"]["speedA"].__setitem__(
             "f32_word_le", "0x00000000"),
         "f32 word disagrees with its value"),
        ("route-label-drift",
         lambda doc: doc["render_cases"][0].__setitem__("route", "tile"),
         "case identity mismatch"),
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
        ("adapter-routed-key",
         lambda doc: doc["provenance"]["adapter_routed_keys"].append(PROGRAM_KEY),
         "must be absent from the adapter table"),
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
        ("corpus-adapter-keys-drift",
         lambda doc: doc["provenance"]["corpus_adapter_keys"].append(
             "filter/bogus:bogus"),
         "disagree with the live check_corpus._ADAPTERS"),
        ("corpus-adapter-source-not-live",
         lambda doc: doc["provenance"]["corpus_adapter_source"].__setitem__(
             "parsed_from_live_source", False),
         "must be read from the live source"),
        ("production-crop-window-mismatch",
         lambda doc: doc["crop_identity"]["production_shaped_case"]
         ["full_route_crop_window"]["f32_words_le"].__setitem__(0, "0x00000000"),
         "Float32 digest mismatch"),
        ("production-crop-window-forged", _forge_production_window,
         "stored tile word differs from the production-scale top-down crop"),
        ("production-crop-window-not-stored",
         lambda doc: doc["crop_identity"]["production_shaped_case"].__setitem__(
             "full_route_crop_window_stored", False),
         "the crop window must be stored"),
        ("production-crop-vacuous-trap",
         lambda doc: doc["crop_identity"]["production_shaped_case"]
         ["raw_crop_y_trap"].__setitem__("changed_lane_count", 0),
         "raw crop_y trap is vacuous"),
        ("disjoint-requirement-unstated",
         lambda doc: doc["mutation_discrimination_contract"].__setitem__(
             "disjoint_witness_requirement", "the sets happen not to overlap"),
         "must be stated, not merely enforced"),
        ("witness-sets-drift",
         lambda doc: doc["mutation_discrimination_contract"]["witness_sets"]
         ["shape-globalcoord-unnarrowed"].__setitem__(
             "witness_cases", ["shape-landscape-16x9"]),
         "disagrees with the frozen per-case table"),
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
        ("global-contract-marker-drift",
         lambda doc: doc["mutable_global_contracts"]["globalCoord"].__setitem__(
             "numeric_contract", "plain double lanes"),
         "numeric contract drift"),
        ("merged-global-contracts",
         lambda doc: doc["mutable_global_contracts"]["globalCoord"].__setitem__(
             "numeric_contract",
             doc["mutable_global_contracts"]["aspectRatio"]["numeric_contract"]),
         "must carry different numeric contracts"),
        ("global-contract-not-discriminable",
         lambda doc: doc["mutable_global_contracts"]["aspectRatio"].__setitem__(
             "oracle_discriminable", False),
         "contract is recorded as not discriminable"),
        ("alpha-word-drift", _break_alpha_word, "alpha Float32 word at lane 3"),
        ("alpha-byte-drift", _break_alpha_byte, "alpha RGBA8 byte at lane 3"),
        ("crop-offset-drift", _bind_raw_crop_y, "tileOffset is not"),
        ("crop-full-route-digest",
         lambda doc: doc["crop_identity"]["full_route_expected"]["f32_words_le"]
         .__setitem__(0, "0x00000000"), "Float32 digest mismatch"),
        ("crop-row-shift", _shift_crop_row,
         "stored tile word differs from the top-down crop"),
        ("crop-vacuous-trap",
         lambda doc: doc["crop_identity"]["raw_crop_y_trap"].__setitem__(
             "changed_lane_count", 0), "raw crop_y trap is vacuous"),
        ("production-crop-claims-stored-full-route",
         lambda doc: doc["crop_identity"]["production_shaped_case"].__setitem__(
             "full_route_stored", True),
         "the full route must not be"),
        ("external-control-drift",
         lambda doc: doc["control_group"]["controls"][0].__setitem__(
             "observed", "differs"),
         "pass ledger disagrees with observation"),
        ("bound-time-control-drift",
         lambda doc: (
             doc["control_group"]["controls"][1].__setitem__("observed", "identical"),
             doc["control_group"]["controls"][1].__setitem__("pass", False)),
         "control did not pass"),
        ("baseline-digest-drift",
         lambda doc: doc["control_group"]["baseline"].__setitem__(
             "f32_sha256", "0" * 64),
         "digests disagree with the anchor case"),
        ("fabricated-control", _fabricate_control,
         "recorded observation 'identical' disagrees with the stored arrays"),
        ("wrong-geometry-control", _transpose_control_geometry,
         "control_group.external-pass-extreme.output.width: "
         "malformed dimension 9"),
        ("seed-census-disagreement",
         lambda doc: doc["seed_liveness_census"].__setitem__(
             "bound_seed_changes_output", True),
         "summary disagrees with the probe ledger"),
        ("fabricated-seed-probe", _fabricate_seed_probe,
         "its digest says otherwise"),
        ("fabricated-wrap-probe", _fabricate_wrap_probe,
         "its digest says otherwise"),
        ("wrap-lf-drift",
         lambda doc: doc["wrap_liveness_census"]["probes"][0].__setitem__(
             "lf_a", 3.5), "is not map(loopScale, 1, 100, 6, 1)"),
        ("collapsed-speed-census", _collapse_speed_census,
         "distinct digest count disagrees"),
        ("truncated-globalcoord-witness", _truncate_globalcoord_witness,
         "Float32 words, found"),
        ("globalcoord-census-zero-offset-discriminates",
         lambda doc: (
             doc["globalcoord_witness_census"]["probes"][0].__setitem__(
                 "discriminates", True),
             doc["globalcoord_witness_census"]["probes"][0].__setitem__(
                 "changed_lane_count", 1)),
         "the zero-offset control is missing or discriminates"),
        ("mutant-census-drift",
         lambda doc: doc["mutation_ledger"].pop(), "mutant census mismatch"),
        ("mutant-per-case-table-drift",
         lambda doc: doc["mutation_discrimination_contract"]["expected"]
         ["shape-globalcoord-unnarrowed"].__setitem__(
             "shape-landscape-16x9", True),
         "does not match the frozen table"),
        ("mutant-row-expectation-drift",
         lambda doc: doc["mutation_ledger"][0]["results"][2].__setitem__(
             "expected_discriminates", True),
         "carries the wrong per-case expectation"),
        ("mutant-witness-non-discriminating",
         lambda doc: doc["mutation_ledger"][0]["results"][0].__setitem__(
             "differs", False), "but the ledger records False"),
        ("mutant-control-changed",
         lambda doc: doc["mutation_ledger"][1]["results"][0].__setitem__(
             "differs", True), "but the ledger records True"),
        ("fabricated-mutant-digest", _fabricate_mutant_digest,
         "but its mutant digests say otherwise"),
        ("mutant-partition-drift",
         lambda doc: doc["mutation_ledger"][0]["witness_cases"].append("bogus"),
         "witness/control partition drift"),
        ("self-test-ledger-drift",
         lambda doc: doc["comparer_self_tests"].__setitem__(
             "signed_zero_rejected_with_equal_rgba8", False),
         "comparer self-test mismatch"),
    )
    passed = 0
    with tempfile.TemporaryDirectory(prefix="shape184-selftest-") as raw:
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
        _expect_rejection(broken_json, "invalid Shape184 JSON", "broken-json")
        passed += 1
    print(f"Shape184 native oracle materializer self-test ok ({passed} checks)")
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
                    "generated Shape184 native include is stale")
    except (OSError, OracleError) as error:
        print(f"glslcpp: {error}", file=sys.stderr)
        return 1
    oracle, _ = load(LIVE)
    words = sum(len(case["output_expected"]["f32_words_le"])
                for case in oracle["render_cases"])
    witnesses = {mutant["name"]: len(mutant["witness_cases"])
                 for mutant in oracle["mutation_ledger"]}
    print(f"Shape184 native oracle include ok "
          f"({len(EXPECTED_CASES)} cases, {words} words, {words} bytes, "
          f"{len(MUTANTS)} mutants, per-case witnesses "
          + ", ".join(f"{name}={count}" for name, count in witnesses.items())
          + ")")
    for control in oracle["control_group"]["controls"]:
        if control["pass"] is not True:
            print(f"glslcpp: NOTICE control {control['name']} expected "
                  f"{control['expectation']} but the shipped JavaScript is "
                  f"{control['observed']}; see seed_liveness_census",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
