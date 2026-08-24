#!/usr/bin/env python3
"""Generate the checked native Cellrefract186 fixture from the canonical JS JSON.

This is the sole JSON-to-C++ materializer for
`classicNoisedeck/cellRefract:cellRefract` (typed row 186). It never renders
anything: every expected word and byte originates in
`docs/port-engineering/cellrefract-parity/cellrefract186-oracles.json`, which is
produced by the canonical JavaScript oracle generator. The materializer is
fail-closed and rejects missing or extra fields, duplicate case names,
malformed dimensions, counts, hex words or byte values, wrong digests, wrong or
missing sidecars, and truncated or extra arrays. `--self-test` proves each
rejection.

Nothing recorded as prose is trusted. Every observation the document reports --
kernel-zero invariance, the measured tile-translation non-identity with its
d-field and localUV probe witnesses, binding inertness and liveness, the phase
integrality rule, and per-case mutant discrimination -- is RE-DERIVED here from
the stored arrays and digests, so a hand-edited verdict with refreshed hashes
cannot survive.
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
PACKAGE = ROOT / "docs/port-engineering/cellrefract-parity"
OUTPUT = ROOT / "tests/oracles/cellrefract186_expected.inc"
TOOL = pathlib.Path(__file__).resolve()

SCHEMA = "noisemaker-for-cpp.cellrefract186.pixel-parity.v1"
SCHEMA_VERSION = 1
PROGRAM_KEY = "classicNoisedeck/cellRefract:cellRefract"
EFFECT_KEY = "classicNoisedeck/cellRefract"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
DEFINES = {"KERNEL": 0, "SHAPE": 1}
FACTORY_NAME = "canonicalFactory3"
FACTORY_SHA256 = "329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3"
SOURCE_RELATIVE = (
    f"tools/glslcpp/corpus/{CORPUS_REVISION}"
    "/sources/classicNoisedeck/cellRefract/cellRefract.glsl")
SOURCE_BYTES = 13719
SOURCE_SHA256 = "aa93167faa07ee22ff0be9c653b5602ac88b1b962e405548cafab43b9e867a70"
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

# The Python-side eligibility table, which this program must stay out of.
# Read from the LIVE `check_corpus` module, never transcribed: comparing one
# frozen copy against another frozen copy proves nothing, and would stay green
# if `classicNoisedeck/cellRefract` were ever added to the real table.
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
    "inputTex", "time", "seed", "resolution", "tileOffset", "fullResolution",
    "scale", "cellScale", "cellSmooth", "variation", "speed", "refractAmt",
    "direction", "wrap", "effectWidth",
)
BINDING_ABI = {
    "inputTex": "sampler2D", "time": "number", "seed": "int32",
    "resolution": "Vec2", "tileOffset": "Vec2", "fullResolution": "Vec2",
    "scale": "number", "cellScale": "number", "cellSmooth": "number",
    "variation": "number", "speed": "number", "refractAmt": "number",
    "direction": "number", "wrap": "int32", "effectWidth": "number",
}
VEC_LANES = {"Vec2": 2}
LIVE_BINDINGS = (
    "inputTex", "time", "seed", "tileOffset", "fullResolution", "scale",
    "cellScale", "cellSmooth", "variation", "speed", "refractAmt",
    "direction", "wrap",
)
INERT_BINDINGS = ("resolution", "effectWidth")

TABLE_NAMES = ("emboss", "sharpen", "blur", "edge", "edge2")
KERNEL_TABLES = {
    "emboss": [-2, -1, 0, -1, 1, 1, 0, 1, 2],
    "sharpen": [-1, 0, -1, 0, 5, 0, -1, 0, -1],
    "blur": [1, 2, 1, 2, 4, 2, 1, 2, 1],
    "edge": [-1, -1, -1, -1, 8, -1, -1, -1, -1],
    "edge2": [-1, 0, -1, 0, 4, 0, -1, 0, -1],
}
TABLE_OCCURRENCES = {"emboss": 11, "sharpen": 11, "blur": 11, "edge": 10, "edge2": 12}
WRITER_CONTRACT = (
    "loadKernels, called once per pixel from main, re-writing all nine "
    "elements before any possible read")
# `mutantIdentity` in the generator: lists for anchors/replacements, a single
# digest for the mutated factory text.
MUTANT_IDENTITY_KEYS = {
    "anchor_count", "anchor_sha256", "replacement_sha256",
    "anchor_occurrences", "mutated_factory_sha256",
}

# (name, width, height, route)
EXPECTED_CASES = (
    ("cells-wrap-mirror", 16, 9, "full"),
    ("cells-wrap-repeat", 16, 9, "full"),
    ("cells-extreme-variation", 12, 12, "full"),
    ("tile-crop-translation", 4, 6, "tile"),
)
CASE_NAMES = tuple(name for name, _, _, _ in EXPECTED_CASES)
ANCHOR_CASE = "cells-wrap-mirror"
TILE_CASE = "tile-crop-translation"

CROP_RECT = {"crop_x": 4, "crop_y": 2, "tile_width": 4, "tile_height": 6,
             "full_width": 11, "full_height": 9}

# The per-case, per-mutant discrimination ledger. A per-mutant summary is not
# sufficient, so every cell is frozen and every cell is checked.
MUTANT_DISCRIMINATION = {
    "smin-h-quadratic-dropped": {
        "cells-wrap-mirror": True,
        "cells-wrap-repeat": True,
        "cells-extreme-variation": False,
        "tile-crop-translation": True,
    },
    "prng-pcg-constant-perturbed": {
        "cells-wrap-mirror": True,
        "cells-wrap-repeat": True,
        "cells-extreme-variation": True,
        "tile-crop-translation": True,
    },
    "aspect-ratio-inverted": {
        "cells-wrap-mirror": True,
        "cells-wrap-repeat": True,
        "cells-extreme-variation": False,
        "tile-crop-translation": True,
    },
    "wrap-arm-swapped": {
        "cells-wrap-mirror": True,
        "cells-wrap-repeat": True,
        "cells-extreme-variation": True,
        "tile-crop-translation": False,
    },
}
MUTANTS = tuple(MUTANT_DISCRIMINATION)

# (name, expectation). `kernel-binding-unbound` is the kernel-zero-invariance
# axis: an absent KERNEL binding must render bit-identically to KERNEL = 0.
CONTROLS = (
    ("external-pass-extreme", "identical"),
    ("kernel-binding-unbound", "identical"),
    ("bound-time-live", "differs"),
    ("effect-width-extreme", "identical"),
)
KERNEL_PROBE_LABELS = ("unbound", "0", "1-with-effectwidth-4",
                       "4-with-effectwidth-4", "7-with-effectwidth-4")
PHASE_PROBE_EXPECTATIONS = (("cells-wrap-mirror", "identical"),
                            ("cells-wrap-mirror", "differs"),
                            ("cells-wrap-repeat", "differs"))
SPEED_CLASSES = ((0, 2, 4), (1, 3, 5))

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
    "defines_are_runtime_bindings_in_the_javascript", "oracle_authority",
    "mutable_global_contracts", "exactness_contract", "provenance",
    "comparer_self_tests", "coverage_axes", "render_cases", "tile_translation",
    "control_group", "kernel_liveness_census", "binding_inertness_census",
    "binding_liveness_census", "time_speed_phase_census", "speed_class_census",
    "mutation_ledger", "nonreaching_control_mutant", "write_only_tables_axis",
    "prng_near_ulp_invariance", "mutation_discrimination_contract",
    "claim_boundaries",
}
CASE_KEYS = {
    "name", "coverage", "route", "width", "height", "input_texture",
    "bindings", "external_pass", "output_expected", "canonical_repeat",
    "public_canonical",
}
SURFACE_KEYS = {
    "width", "height", "f32_words_le", "f32_sha256", "rgba8_bytes",
    "rgba8_sha256", "finite_lane_count", "nonfinite_lane_count",
    "alpha_f32_word", "alpha_rgba8_byte",
}
INPUT_KEYS = {
    "width", "height", "row_order", "f32_words_le", "f32_sha256",
    "every_lane_exactly_f32_representable",
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
        return self.package / "cellrefract186-oracles.json"

    @property
    def report(self) -> pathlib.Path:
        return self.package / "cellrefract-oracle-report.md"

    @property
    def generator(self) -> pathlib.Path:
        return self.package / "cellrefract186_oracle_generator.mjs"


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


def require_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise OracleError(f"{label}: integer required")
    return value


def packed_words(words: list[str]) -> bytes:
    return b"".join(struct.pack("<I", int(word, 16)) for word in words)


def word_value(word: str) -> float:
    return struct.unpack("<f", struct.pack("<I", int(word, 16)))[0]


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


def validate_input(record: object, label: str) -> dict[str, Any]:
    entry = require_keys(record, INPUT_KEYS, label)
    width = require_int(entry.get("width"), f"{label}.width")
    height = require_int(entry.get("height"), f"{label}.height")
    if width <= 0 or height <= 0:
        raise OracleError(f"{label}: malformed dimension")
    count = width * height * 4
    words = require_word_array(entry.get("f32_words_le"), count, label)
    if sha256(packed_words(words)) != require_hex64(entry.get("f32_sha256"),
                                                    f"{label}.f32_sha256"):
        raise OracleError(f"{label}: Float32 digest mismatch")
    if entry.get("every_lane_exactly_f32_representable") is not True:
        raise OracleError(f"{label}: the f32-exactness contract must be stated")
    for index in range(3, count, 4):
        if words[index] != ALPHA_WORD:
            raise OracleError(
                f"{label}: input alpha word at lane {index} is {words[index]}")
    return entry


def validate_bindings(record: object, label: str) -> dict[str, Any]:
    bindings = require_keys(record, set(BINDING_NAMES), label)
    if tuple(bindings) != BINDING_NAMES:
        raise OracleError(f"{label}: binding order drift")
    for name in BINDING_NAMES:
        abi = BINDING_ABI[name]
        item = bindings[name]
        field = f"{label}.{name}"
        if abi == "sampler2D":
            entry = require_keys(item, {"abi", "width", "height", "f32_sha256"},
                                 field)
            for dimension in ("width", "height"):
                if (not isinstance(entry[dimension], int)
                        or isinstance(entry[dimension], bool)
                        or entry[dimension] <= 0):
                    raise OracleError(f"{field}: malformed {dimension}")
            require_hex64(entry["f32_sha256"], f"{field}.f32_sha256")
        elif abi == "int32":
            entry = require_keys(item, {"abi", "value"}, field)
            value = entry["value"]
            if (not isinstance(value, int) or isinstance(value, bool)
                    or not -2147483648 <= value <= 2147483647):
                raise OracleError(f"{field}: int32 value required")
        elif abi == "number":
            entry = require_keys(item, {"abi", "f32_value", "f32_word_le"},
                                 field)
            if not isinstance(entry["f32_value"], (int, float)) or isinstance(
                    entry["f32_value"], bool):
                raise OracleError(f"{field}: numeric value required")
            require_word_array([entry["f32_word_le"]], 1, field)
            if word_value(entry["f32_word_le"]) != entry["f32_value"]:
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
                if word_value(word) != values[lane]:
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
            "provenance: this program must be absent from the adapter table")
    if not isinstance(corpus_routed, list) or PROGRAM_KEY in corpus_routed:
        raise OracleError(
            "provenance: this program must be absent from the adapter table")
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
        "relative_path_from_noisemaker_for_cpp", "bytes", "sha256",
        "preprocessor_defines"},
        "provenance.source")
    if (source["relative_path_from_noisemaker_for_cpp"] != SOURCE_RELATIVE
            or source["bytes"] != SOURCE_BYTES
            or source["sha256"] != SOURCE_SHA256):
        raise OracleError("provenance: pinned GLSL source mismatch")
    if source["preprocessor_defines"] != ["KERNEL", "SHAPE"]:
        raise OracleError("provenance: preprocessor define census mismatch")
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
    metadata = require_keys(provenance["metadata"], {
        "id", "func", "kind", "pass", "define_params", "textures",
        "external_texture"}, "provenance.metadata")
    if (metadata["id"] != EFFECT_KEY or metadata["func"] != "cellRefract"
            or metadata["kind"] != "filter"
            or metadata["textures"] != {} or metadata["external_texture"] is not None):
        raise OracleError("provenance.metadata: effect metadata drift")
    if metadata["define_params"]["shape"]["default"] != DEFINES["SHAPE"] \
            or metadata["define_params"]["kernel"]["default"] != DEFINES["KERNEL"]:
        raise OracleError("provenance.metadata: define parameter defaults drift")


def validate_tables(oracle: dict[str, Any], by_name: dict[str, Any]) -> None:
    contracts = require_keys(oracle.get("mutable_global_contracts"),
                             set(TABLE_NAMES), "mutable_global_contracts")
    for name in TABLE_NAMES:
        entry = require_keys(contracts[name], {
            "javascript_declaration", "glsl_type", "element_materialization",
            "numeric_contract", "native_element_type", "writer", "elements",
            "identifier_occurrences", "reads", "oracle_discriminable",
            "why_not_discriminable"},
            f"mutable_global_contracts.{name}")
        if entry["javascript_declaration"] != f"var {name} = [0, 0, 0, 0, 0, 0, 0, 0, 0];":
            raise OracleError(
                f"mutable_global_contracts.{name}: declaration drift")
        if "NOT a Float32Array" not in entry["element_materialization"]:
            raise OracleError(
                f"mutable_global_contracts.{name}: element materialization must "
                "be a plain Array, never a Float32Array")
        if "NEVER narrowed" not in entry["numeric_contract"] \
                or entry["native_element_type"] != "double":
            raise OracleError(
                f"mutable_global_contracts.{name}: the double contract must be "
                "stated and paired with the native double type")
        if entry["writer"] != WRITER_CONTRACT:
            raise OracleError(
                f"mutable_global_contracts.{name}: writer contract drift")
        if entry["elements"] != KERNEL_TABLES[name]:
            raise OracleError(
                f"mutable_global_contracts.{name}: element census drift")
        if entry["identifier_occurrences"] != TABLE_OCCURRENCES[name]:
            raise OracleError(
                f"mutable_global_contracts.{name}: identifier occurrence drift")
        if entry["oracle_discriminable"] is not False:
            raise OracleError(
                f"mutable_global_contracts.{name}: the tables are write-only "
                "and must never be recorded discriminable")
        if "write_only_tables_axis" not in entry["why_not_discriminable"]:
            raise OracleError(
                f"mutable_global_contracts.{name}: the reason must name the "
                "write_only_tables_axis")
    axis = require_keys(oracle.get("write_only_tables_axis"), {
        "status", "design_reference", "element_count", "elements",
        "identifier_occurrence_census", "occurrence_rule", "rendered_mutant",
        "rendered_divergences", "claim"}, "write_only_tables_axis")
    if axis["status"] != "cannot-diverge-do-not-ship" \
            or axis["element_count"] != 45 or axis["elements"] != KERNEL_TABLES \
            or axis["identifier_occurrence_census"] != TABLE_OCCURRENCES:
        raise OracleError("write_only_tables_axis: census drift")
    rows = require_keys(axis["rendered_mutant"], {"name", "rows"} | MUTANT_IDENTITY_KEYS,
                        "write_only_tables_axis.rendered_mutant")["rows"]
    validate_invariant_rows(rows, "write_only_tables_axis.rendered_mutant",
                            by_name)
    if axis["rendered_divergences"] != 0:
        raise OracleError("write_only_tables_axis: a table mutant diverged")


def validate_invariant_rows(rows: object, label: str,
                            by_name: dict[str, Any] | None = None) -> None:
    if not isinstance(rows, list) or tuple(
            item.get("case") for item in rows) != CASE_NAMES:
        raise OracleError(f"{label}: row census mismatch")
    for row in rows:
        name = row["case"]
        entry = require_keys(row, {
            "case", "differs", "changed_lane_count",
            "changed_rgba8_byte_count", "f32_sha256", "rgba8_sha256",
            "first_mismatch"}, f"{label}.{name}")
        if entry["differs"] is not False or entry["changed_lane_count"] != 0 \
                or entry["changed_rgba8_byte_count"] != 0 \
                or entry["first_mismatch"] is not None:
            raise OracleError(f"{label}.{name}: the row must be invariant")
        for field in ("f32_sha256", "rgba8_sha256"):
            require_hex64(entry[field], f"{label}.{name}.{field}")
        if by_name is not None:
            canonical = by_name[name]["output_expected"]
            if (entry["f32_sha256"] != canonical["f32_sha256"]
                    or entry["rgba8_sha256"] != canonical["rgba8_sha256"]):
                raise OracleError(
                    f"{label}.{name}: an invariant row must carry the canonical "
                    "case's own digests")


def validate_translation(oracle: dict[str, Any],
                         by_name: dict[str, Any]) -> dict[str, Any]:
    record = require_keys(oracle.get("tile_translation"), {
        "case", "rect", "tile_offset_rule", "tile_offset_f32_words_le",
        "full_route_expected", "design_expectation", "measured",
        "word_mismatches", "byte_mismatches", "is_exact_crop",
        "first_mismatch", "why", "d_field_alignment_witness",
        "local_uv_translation_witness", "raw_crop_y_trap", "consequence"},
        "tile_translation")
    rect = require_keys(record["rect"], set(CROP_RECT), "tile_translation.rect")
    for key, value in rect.items():
        if value != CROP_RECT[key] or not isinstance(value, int) \
                or isinstance(value, bool) or value < 0:
            raise OracleError(f"tile_translation.rect: malformed {key}")
    if record["case"] != TILE_CASE:
        raise OracleError("tile_translation: unexpected case")
    tile = by_name[TILE_CASE]
    if (tile["width"] != rect["tile_width"]
            or tile["height"] != rect["tile_height"]):
        raise OracleError("tile_translation: tile dimensions disagree with case")
    if (rect["crop_x"] + rect["tile_width"] > rect["full_width"]
            or rect["crop_y"] + rect["tile_height"] > rect["full_height"]):
        raise OracleError("tile_translation: crop rectangle escapes the full surface")
    expected_offset = (float(rect["crop_x"]),
                       float(rect["full_height"] - rect["crop_y"]
                             - rect["tile_height"]))
    actual_offset = tuple(
        word_value(word) for word in require_word_array(
            tile["bindings"]["tileOffset"]["f32_words_le"], 2,
            "tile_translation.tileOffset"))
    if actual_offset != expected_offset:
        raise OracleError(
            "tile_translation: tileOffset is not "
            "(crop_x, full_height - crop_y - tile_height)")
    if require_word_array(record["tile_offset_f32_words_le"], 2,
                          "tile_translation.tile_offset_f32_words_le") != \
            tile["bindings"]["tileOffset"]["f32_words_le"]:
        raise OracleError("tile_translation: recorded tileOffset words disagree")
    full = validate_surface(record["full_route_expected"], rect["full_width"],
                            rect["full_height"], "tile_translation.full_route")
    if record["is_exact_crop"] is not False:
        raise OracleError(
            "tile_translation: the measured non-identity must be recorded as "
            "is_exact_crop false; a crop identity may not be asserted for this "
            "program")
    # Re-derived from the stored arrays, never from the recorded counts.
    tile_words = tile["output_expected"]["f32_words_le"]
    tile_bytes = tile["output_expected"]["rgba8_bytes"]
    full_words = full["f32_words_le"]
    full_bytes = full["rgba8_bytes"]
    word_mismatches = 0
    byte_mismatches = 0
    for ty in range(rect["tile_height"]):
        for tx in range(rect["tile_width"]):
            for channel in range(4):
                tile_index = ((ty * rect["tile_width"]) + tx) * 4 + channel
                full_index = (((rect["crop_y"] + ty) * rect["full_width"])
                              + (rect["crop_x"] + tx)) * 4 + channel
                if tile_words[tile_index] != full_words[full_index]:
                    word_mismatches += 1
                if tile_bytes[tile_index] != full_bytes[full_index]:
                    byte_mismatches += 1
    if word_mismatches != record["word_mismatches"] \
            or byte_mismatches != record["byte_mismatches"]:
        raise OracleError(
            "tile_translation: the recorded mismatch counts disagree with the "
            "stored arrays")
    if word_mismatches == 0:
        raise OracleError(
            "tile_translation: the tile IS an exact crop; the non-identity "
            "record is wrong")
    total = rect["tile_width"] * rect["tile_height"] * 4
    if word_mismatches == total:
        raise OracleError(
            "tile_translation: the routes share no lane; they are unrelated")
    first = require_keys(record["first_mismatch"], {
        "top_down_xy", "channel", "tile_word", "full_word"},
        "tile_translation.first_mismatch")
    if first["channel"] not in ("r", "g", "b", "a"):
        raise OracleError("tile_translation.first_mismatch: malformed channel")
    trap = require_keys(record["raw_crop_y_trap"], {
        "tile_offset_f32_words_le", "differs_from_correct_tile",
        "changed_lane_count", "first_mismatch"}, "tile_translation.raw_crop_y_trap")
    if trap["differs_from_correct_tile"] is not True \
            or not isinstance(trap["changed_lane_count"], int) \
            or trap["changed_lane_count"] < 1:
        raise OracleError("tile_translation: raw crop_y trap is vacuous")
    if rect["crop_y"] == rect["full_height"] - rect["crop_y"] - rect["tile_height"]:
        raise OracleError(
            "tile_translation: the raw crop_y trap is indistinguishable from "
            "the correct offset for this rectangle")

    # The d-field probe: the cells field must be an EXACT crop.
    dwitness = require_keys(record["d_field_alignment_witness"], {
        "classification", "probe", "rule", "exact_word_mismatches",
        "full_route_d_words_le", "full_route_d_sha256", "tile_d_words_le",
        "tile_d_sha256"}, "tile_translation.d_field_alignment_witness")
    require_keys(dwitness["probe"], {"name"} | MUTANT_IDENTITY_KEYS,
                 "tile_translation.d_field_alignment_witness.probe")
    if "NOT a parity array" not in dwitness["classification"]:
        raise OracleError(
            "tile_translation.d_field_alignment_witness: the probe must be "
            "labelled as not a parity array")
    tile_d = require_word_array(dwitness["tile_d_words_le"], total,
                                "tile_translation.d_field_alignment_witness.tile_d")
    full_d = require_word_array(dwitness["full_route_d_words_le"],
                                rect["full_width"] * rect["full_height"] * 4,
                                "tile_translation.d_field_alignment_witness.full_d")
    if sha256(packed_words(tile_d)) != require_hex64(
            dwitness["tile_d_sha256"],
            "tile_translation.d_field_alignment_witness.tile_d_sha256"):
        raise OracleError(
            "tile_translation.d_field_alignment_witness: tile d digest mismatch")
    if sha256(packed_words(full_d)) != require_hex64(
            dwitness["full_route_d_sha256"],
            "tile_translation.d_field_alignment_witness.full_route_d_sha256"):
        raise OracleError(
            "tile_translation.d_field_alignment_witness: full d digest mismatch")
    d_mismatches = 0
    for ty in range(rect["tile_height"]):
        for tx in range(rect["tile_width"]):
            for channel in range(4):
                tile_index = ((ty * rect["tile_width"]) + tx) * 4 + channel
                full_index = (((rect["crop_y"] + ty) * rect["full_width"])
                              + (rect["crop_x"] + tx)) * 4 + channel
                if tile_d[tile_index] != full_d[full_index]:
                    d_mismatches += 1
    if d_mismatches != dwitness["exact_word_mismatches"] or d_mismatches != 0:
        raise OracleError(
            "tile_translation.d_field_alignment_witness: the cells field is "
            "not an exact crop of the full route")

    # The localUV probe: no compared lane may be equal.
    uwitness = require_keys(record["local_uv_translation_witness"], {
        "classification", "probe", "rule", "compared_lane_count",
        "equal_lane_count", "full_route_uv_words_le", "full_route_uv_sha256",
        "tile_uv_words_le", "tile_uv_sha256"},
        "tile_translation.local_uv_translation_witness")
    require_keys(uwitness["probe"], {"name"} | MUTANT_IDENTITY_KEYS,
                 "tile_translation.local_uv_translation_witness.probe")
    if "NOT a parity array" not in uwitness["classification"]:
        raise OracleError(
            "tile_translation.local_uv_translation_witness: the probe must be "
            "labelled as not a parity array")
    tile_uv = require_word_array(uwitness["tile_uv_words_le"], total,
                                 "tile_translation.local_uv_translation_witness.tile_uv")
    full_uv = require_word_array(uwitness["full_route_uv_words_le"],
                                 rect["full_width"] * rect["full_height"] * 4,
                                 "tile_translation.local_uv_translation_witness.full_uv")
    if sha256(packed_words(tile_uv)) != require_hex64(
            uwitness["tile_uv_sha256"],
            "tile_translation.local_uv_translation_witness.tile_uv_sha256"):
        raise OracleError(
            "tile_translation.local_uv_translation_witness: tile uv digest mismatch")
    if sha256(packed_words(full_uv)) != require_hex64(
            uwitness["full_route_uv_sha256"],
            "tile_translation.local_uv_translation_witness.full_route_uv_sha256"):
        raise OracleError(
            "tile_translation.local_uv_translation_witness: full uv digest mismatch")
    compared = 0
    equal = 0
    for ty in range(rect["tile_height"]):
        for tx in range(rect["tile_width"]):
            for channel in range(2):
                tile_index = ((ty * rect["tile_width"]) + tx) * 4 + channel
                full_index = (((rect["crop_y"] + ty) * rect["full_width"])
                              + (rect["crop_x"] + tx)) * 4 + channel
                compared += 1
                if tile_uv[tile_index] == full_uv[full_index]:
                    equal += 1
    if compared != uwitness["compared_lane_count"] \
            or equal != uwitness["equal_lane_count"] or equal != 0:
        raise OracleError(
            "tile_translation.local_uv_translation_witness: the translation "
            "account disagrees with the stored probe arrays")
    return record


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
        # The anchor's own geometry, never the record's self-reported
        # dimensions: a self-consistent control of another shape is not a
        # one-axis variant of the anchor.
        surface = validate_surface(entry["output"], anchor_case["width"],
                                   anchor_case["height"], f"{label}.output")
        identical = (surface["f32_words_le"] == anchor_surface["f32_words_le"]
                     and surface["rgba8_bytes"] == anchor_surface["rgba8_bytes"])
        derived.append("identical" if identical else "differs")
    if controls[0]["observed"] != "identical":
        raise OracleError(
            "control_group: external runPass time/seed changed the output")
    if controls[1]["observed"] != "identical":
        raise OracleError(
            "control_group: the kernel-binding-unbound axis is not invariant")
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


def validate_kernel_census(oracle: dict[str, Any],
                           by_name: dict[str, Any]) -> None:
    census = require_keys(oracle.get("kernel_liveness_census"), {
        "probe_case", "rule", "probes"}, "kernel_liveness_census")
    if census["probe_case"] != ANCHOR_CASE:
        raise OracleError("kernel_liveness_census: unexpected probe case")
    probes = census["probes"]
    if not isinstance(probes, list) or tuple(
            probe.get("kernel") for probe in probes) != KERNEL_PROBE_LABELS:
        raise OracleError("kernel_liveness_census: probe census mismatch")
    anchor_digest = by_name[ANCHOR_CASE]["output_expected"]["f32_sha256"]
    for index, probe in enumerate(probes):
        entry = require_keys(probe, {
            "kernel", "differs_from_baseline", "changed_lane_count",
            "f32_sha256"}, f"kernel_liveness_census.{KERNEL_PROBE_LABELS[index]}")
        digest_matches = entry["f32_sha256"] == anchor_digest
        if entry["differs_from_baseline"] is digest_matches:
            raise OracleError(
                f"kernel_liveness_census.{entry['kernel']}: the verdict "
                "disagrees with the recorded digest")
        if entry["differs_from_baseline"] is not (entry["changed_lane_count"] > 0):
            raise OracleError(
                f"kernel_liveness_census.{entry['kernel']}: changed lane count "
                "disagrees with the verdict")
    closed = probes[:2]
    live = probes[2:]
    if any(probe["differs_from_baseline"] for probe in closed):
        raise OracleError(
            "kernel_liveness_census: the unbound/0 probes are not invariant")
    if closed[0]["f32_sha256"] != closed[1]["f32_sha256"]:
        raise OracleError(
            "kernel_liveness_census: unbound KERNEL and KERNEL 0 rendered "
            "different images; the invariance axis failed")
    if not all(probe["differs_from_baseline"] for probe in live):
        raise OracleError(
            "kernel_liveness_census: a KERNEL != 0 probe is invariant; the "
            "census is vacuous")


def validate_binding_censuses(oracle: dict[str, Any],
                              by_name: dict[str, Any]) -> None:
    anchor_digest = by_name[ANCHOR_CASE]["output_expected"]["f32_sha256"]
    inert = require_keys(oracle.get("binding_inertness_census"), {
        "probe_case", "rule", "inert", "live", "reason"},
        "binding_inertness_census")
    if inert["probe_case"] != ANCHOR_CASE:
        raise OracleError("binding_inertness_census: unexpected probe case")
    if tuple(entry.get("binding") for entry in inert["inert"]) != INERT_BINDINGS:
        raise OracleError("binding_inertness_census: inert census mismatch")
    for entry in inert["inert"]:
        label = f"binding_inertness_census.{entry['binding']}"
        item = require_keys(entry, {
            "binding", "abi", "probes", "live"}, label)
        if item["abi"] != BINDING_ABI[item["binding"]]:
            raise OracleError(f"{label}: ABI drift")
        if item["live"] is True:
            raise OracleError(f"{label}: recorded inert but live")
        probes = item["probes"]
        if not isinstance(probes, list) or len(probes) < 2:
            raise OracleError(f"{label}: probe census mismatch")
        for probe in probes:
            row = require_keys(probe, {
                "value", "differs_from_baseline", "changed_lane_count",
                "f32_sha256"}, f"{label}.probe")
            if row["differs_from_baseline"] is True \
                    or row["f32_sha256"] != anchor_digest:
                raise OracleError(
                    f"{label}: an inert probe must be invariant and carry the "
                    "anchor digest")
    if sorted(inert["live"]) != sorted(LIVE_BINDINGS):
        raise OracleError("binding_inertness_census: live census mismatch")
    for name in (*INERT_BINDINGS, *LIVE_BINDINGS):
        if name not in inert["reason"]:
            raise OracleError(f"binding_inertness_census.reason: {name} missing")

    liveness = require_keys(oracle.get("binding_liveness_census"), {
        "probe_case", "rule", "probes"}, "binding_liveness_census")
    if liveness["probe_case"] != ANCHOR_CASE:
        raise OracleError("binding_liveness_census: unexpected probe case")
    probes = liveness["probes"]
    if not isinstance(probes, list) or tuple(
            probe.get("binding") for probe in probes) != LIVE_BINDINGS:
        raise OracleError("binding_liveness_census: probe census mismatch")
    for probe in probes:
        label = f"binding_liveness_census.{probe['binding']}"
        row = require_keys(probe, {
            "binding", "differs_from_baseline", "changed_lane_count",
            "f32_sha256"}, label)
        if row["differs_from_baseline"] is not True:
            raise OracleError(f"{label}: recorded live but invariant")
        if row["f32_sha256"] == anchor_digest:
            raise OracleError(
                f"{label}: a live probe carries the anchor digest")
        if row["changed_lane_count"] < 1:
            raise OracleError(f"{label}: changed lane count disagrees")


def validate_phase_censuses(oracle: dict[str, Any],
                            by_name: dict[str, Any]) -> None:
    census = require_keys(oracle.get("time_speed_phase_census"), {
        "rule", "per_case_phase", "probes"}, "time_speed_phase_census")
    phases = census["per_case_phase"]
    if not isinstance(phases, list) or tuple(
            row.get("case") for row in phases) != CASE_NAMES:
        raise OracleError("time_speed_phase_census: per-case census mismatch")
    integral_seen = False
    nonintegral_seen = False
    for row in phases:
        entry = require_keys(row, {
            "case", "time", "floor_speed", "phase", "phase_is_integral"},
            f"time_speed_phase_census.{row.get('case')}")
        case = by_name[entry["case"]]
        time_value = case["bindings"]["time"]["f32_value"]
        speed_value = case["bindings"]["speed"]["f32_value"]
        if entry["time"] != time_value:
            raise OracleError(f"time_speed_phase_census.{entry['case']}: time drift")
        if entry["floor_speed"] != float(int(speed_value)):
            raise OracleError(
                f"time_speed_phase_census.{entry['case']}: floor(speed) drift")
        if entry["phase"] != time_value * int(speed_value):
            raise OracleError(
                f"time_speed_phase_census.{entry['case']}: phase drift")
        if entry["phase_is_integral"] is not float(entry["phase"]).is_integer():
            raise OracleError(
                f"time_speed_phase_census.{entry['case']}: integrality drift")
        integral_seen = integral_seen or entry["phase_is_integral"]
        nonintegral_seen = nonintegral_seen or not entry["phase_is_integral"]
    if not integral_seen or not nonintegral_seen:
        raise OracleError(
            "time_speed_phase_census: both the integral and non-integral "
            "witnesses are required")
    probes = census["probes"]
    if not isinstance(probes, list) or len(probes) != len(PHASE_PROBE_EXPECTATIONS):
        raise OracleError("time_speed_phase_census: probe census mismatch")
    for probe, (case_name, expectation) in zip(probes, PHASE_PROBE_EXPECTATIONS):
        entry = require_keys(probe, {
            "case", "overrides", "note", "observed", "changed_lane_count",
            "f32_sha256"}, f"time_speed_phase_census.probe.{case_name}")
        if entry["case"] != case_name or entry["observed"] != expectation:
            raise OracleError(
                f"time_speed_phase_census.probe: {case_name} must be "
                f"{expectation}")
        digest = by_name[case_name]["output_expected"]["f32_sha256"]
        digest_matches = entry["f32_sha256"] == digest
        if (entry["observed"] == "identical") is not digest_matches:
            raise OracleError(
                "time_speed_phase_census.probe: the observation disagrees with "
                "the recorded digest")
        if (entry["changed_lane_count"] == 0) is not (entry["observed"] == "identical"):
            raise OracleError(
                "time_speed_phase_census.probe: changed lane count disagrees")

    speed = require_keys(oracle.get("speed_class_census"), {
        "probe_case", "rule", "probes", "distinct_digest_count",
        "equivalence_classes"}, "speed_class_census")
    if speed["probe_case"] != ANCHOR_CASE:
        raise OracleError("speed_class_census: unexpected probe case")
    probes = speed["probes"]
    if not isinstance(probes, list) or len(probes) != 6:
        raise OracleError("speed_class_census: probe census mismatch")
    digests: dict[str, list[int]] = {}
    for probe in probes:
        entry = require_keys(probe, {"speed", "f32_sha256"},
                             "speed_class_census.probes")
        if not isinstance(entry["speed"], int) or isinstance(entry["speed"], bool):
            raise OracleError("speed_class_census: malformed speed")
        require_hex64(entry["f32_sha256"], "speed_class_census.probes")
        digests.setdefault(entry["f32_sha256"], []).append(entry["speed"])
    if [entry["speed"] for entry in probes] != [0, 1, 2, 3, 4, 5]:
        raise OracleError("speed_class_census: the 0..5 sweep is required")
    if speed["distinct_digest_count"] != len(digests) or len(digests) != 2:
        raise OracleError("speed_class_census: distinct digest count drift")
    classes = tuple(tuple(sorted(values)) for values in digests.values())
    if sorted(classes) != sorted(SPEED_CLASSES):
        raise OracleError(
            "speed_class_census: the equivalence classes are not the recorded "
            "even/odd triples")
    if sorted(tuple(sorted(cls)) for cls in speed["equivalence_classes"]) != sorted(SPEED_CLASSES):
        raise OracleError("speed_class_census: recorded classes disagree")


def validate_nonreaching_and_near_ulp(oracle: dict[str, Any],
                                      by_name: dict[str, Any]) -> None:
    nonreaching = require_keys(oracle.get("nonreaching_control_mutant"), {
        "status", "design_reference", "rendered_mutant", "rendered_divergences",
        "claim"}, "nonreaching_control_mutant")
    if nonreaching["status"] != "proven-invariant-everywhere":
        raise OracleError("nonreaching_control_mutant: status drift")
    rows = require_keys(nonreaching["rendered_mutant"], {"name", "rows"} | MUTANT_IDENTITY_KEYS,
                        "nonreaching_control_mutant.rendered_mutant")["rows"]
    validate_invariant_rows(rows, "nonreaching_control_mutant.rendered_mutant",
                            by_name)
    if nonreaching["rendered_divergences"] != 0:
        raise OracleError(
            "nonreaching_control_mutant: the KERNEL != 0 branch control diverged")

    near_ulp = require_keys(oracle.get("prng_near_ulp_invariance"), {
        "status", "rendered_mutant", "rendered_divergences", "reason"},
        "prng_near_ulp_invariance")
    if near_ulp["status"] != "measured-invariant":
        raise OracleError("prng_near_ulp_invariance: status drift")
    rows = require_keys(near_ulp["rendered_mutant"], {"name", "rows"} | MUTANT_IDENTITY_KEYS,
                        "prng_near_ulp_invariance.rendered_mutant")["rows"]
    validate_invariant_rows(rows, "prng_near_ulp_invariance.rendered_mutant",
                            by_name)
    if near_ulp["rendered_divergences"] != 0:
        raise OracleError("prng_near_ulp_invariance: the near-ULP mutant diverged")


def validate_mutations(oracle: dict[str, Any],
                       by_name: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = oracle.get("mutation_ledger")
    if not isinstance(ledger, list) or tuple(
            item.get("name") for item in ledger) != MUTANTS:
        raise OracleError("mutation_ledger: mutant census mismatch")
    contract = require_keys(oracle.get("mutation_discrimination_contract"), {
        "per_case", "rule", "witness_overlap_disclosure", "witness_sets",
        "expected", "excluded_from_ledger"},
        "mutation_discrimination_contract")
    if contract["per_case"] is not True:
        raise OracleError(
            "mutation_discrimination_contract: discrimination must be per case")
    if contract["expected"] != MUTANT_DISCRIMINATION:
        raise OracleError(
            "mutation_discrimination_contract: the per-case discrimination "
            "ledger does not match the frozen table")
    # The overlap must be DISCLOSED, not hidden: unlike the two-contract
    # packages, these mutants pin different reachable functions and their
    # witness sets overlap by construction.
    if "overlap" not in contract["witness_overlap_disclosure"].lower():
        raise OracleError(
            "mutation_discrimination_contract: the witness overlap must be "
            "disclosed, not silently asserted disjoint")
    excluded = require_keys(contract["excluded_from_ledger"], {
        "kernel4-arm-emboss-to-sharpen", "kernel-table-emboss0-perturbed",
        "prng-divisor-ulp-perturbed"},
        "mutation_discrimination_contract.excluded_from_ledger")
    for name, reason in excluded.items():
        if not isinstance(reason, str) or not reason:
            raise OracleError(f"mutation_discrimination_contract: {name} "
                              "exclusion reason required")
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
        expected_keys = {
            "name", "target", "contract", "reaching", "classification",
            "witness_cases", "control_cases", "results"} | MUTANT_IDENTITY_KEYS
        if isinstance(mutant, dict) and "note" in mutant:
            expected_keys = expected_keys | {"note"}
        entry = require_keys(mutant, expected_keys, label)
        if any(occurrence != 1 for occurrence in entry["anchor_occurrences"]) \
                or entry["anchor_count"] != len(entry["anchor_occurrences"]) \
                or entry["anchor_count"] < 1:
            raise OracleError(f"{label}: anchor census drift")
        for field in ("anchor_sha256", "replacement_sha256"):
            if not isinstance(entry[field], list) \
                    or len(entry[field]) != entry["anchor_count"]:
                raise OracleError(f"{label}.{field}: anchor list census drift")
            for digest in entry[field]:
                require_hex64(digest, f"{label}.{field}")
        require_hex64(entry["mutated_factory_sha256"],
                      f"{label}.mutated_factory_sha256")
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
            "Cellrefract186 oracle records an absolute filesystem path "
            f"({leaked.group(0)!r}); the gate must be path-independent")
    try:
        oracle = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OracleError(f"invalid Cellrefract186 JSON: {error}") from error
    require_keys(oracle, TOP_LEVEL_KEYS, "oracle")
    if (oracle["schema"], oracle["schema_version"], oracle["program_key"],
            oracle["effect_key"], oracle["runtime_key"],
            oracle["corpus_revision"]) != (
                SCHEMA, SCHEMA_VERSION, PROGRAM_KEY, EFFECT_KEY, PROGRAM_KEY,
                CORPUS_REVISION):
        raise OracleError("Cellrefract186 schema/program identity mismatch")
    if oracle["defines"] != DEFINES:
        raise OracleError("Cellrefract186 define mismatch")
    if tuple(oracle["runtime_binding_names"]) != BINDING_NAMES:
        raise OracleError("Cellrefract186 runtime binding census mismatch")
    if oracle["runtime_binding_abi"] != BINDING_ABI:
        raise OracleError("Cellrefract186 runtime binding ABI mismatch")
    if oracle["compile_time_defines_are_not_bindings"] is not True:
        raise OracleError("Cellrefract186 compile-time define contract mismatch")
    if not isinstance(oracle["defines_are_runtime_bindings_in_the_javascript"], str) \
            or "KERNEL" not in oracle["defines_are_runtime_bindings_in_the_javascript"]:
        raise OracleError(
            "Cellrefract186: the runtime-binding status of the defines must be "
            "stated")
    validate_provenance(oracle, paths)
    self_tests = oracle.get("comparer_self_tests")
    if not isinstance(self_tests, dict) or any(
            self_tests.get(name) is not True for name in REQUIRED_SELF_TESTS):
        raise OracleError("Cellrefract186 comparer self-test mismatch")
    cases = oracle.get("render_cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise OracleError("Cellrefract186 fixture count mismatch")
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
        validate_input(entry["input_texture"], f"{name}.input_texture")
        if route == "full" and (entry["input_texture"]["width"] != width
                                or entry["input_texture"]["height"] != height):
            raise OracleError(
                f"{name}: a full-route case must consume a same-sized input")
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
        if entry["bindings"]["inputTex"]["f32_sha256"] != \
                entry["input_texture"]["f32_sha256"]:
            raise OracleError(
                f"{name}: the inputTex binding digest disagrees with the stored "
                "input texture")
        if (entry["bindings"]["inputTex"]["width"] != entry["input_texture"]["width"]
                or entry["bindings"]["inputTex"]["height"] != entry["input_texture"]["height"]):
            raise OracleError(
                f"{name}: the inputTex binding dimensions disagree with the "
                "stored input texture")
        validate_identity(entry["canonical_repeat"], f"{name}.canonical_repeat")
        validate_identity(entry["public_canonical"], f"{name}.public_canonical")
    by_name = {case["name"]: case for case in cases}
    validate_tables(oracle, by_name)
    coverage = oracle.get("coverage_axes")
    if not isinstance(coverage, dict) or not coverage:
        raise OracleError("Cellrefract186: coverage axes required")
    for axis, buckets in coverage.items():
        for bucket, bucket_names in buckets.items():
            if not isinstance(bucket_names, list) or not bucket_names:
                raise OracleError(f"coverage axis {axis} bucket {bucket} has no witness")
            for name in bucket_names:
                if name not in by_name:
                    raise OracleError(f"coverage axis {axis} names unknown case {name}")
    validate_translation(oracle, by_name)
    validate_controls(oracle, by_name)
    validate_kernel_census(oracle, by_name)
    validate_binding_censuses(oracle, by_name)
    validate_phase_censuses(oracle, by_name)
    validate_nonreaching_and_near_ulp(oracle, by_name)
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
    translation = oracle["tile_translation"]
    lines = [
        "// Generated from the checked canonical JavaScript Cellrefract186",
        "// oracle. Do not edit; C++ output never participates in these",
        "// expected arrays.",
        "//",
        "// classicNoisedeck/cellRefract declares five mutable uninitialized",
        "// float[9] tables written once per pixel by loadKernels and never",
        "// read at the frozen KERNEL = 0. Their double element contract is",
        "// structural; see the oracle's write_only_tables_axis. The ledger",
        "// mutants below pin the reachable path instead.",
        "#pragma once", "", "namespace cellrefract186_oracle {", "",
        f'inline constexpr std::string_view kOracleSha256 = "{oracle_hash}";',
        f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";',
        f'inline constexpr std::string_view kCorpusRevision = "{CORPUS_REVISION}";',
        f"inline constexpr std::int32_t kKernelDefine = {DEFINES['KERNEL']};",
        f"inline constexpr std::int32_t kShapeDefine = {DEFINES['SHAPE']};",
        f"inline constexpr std::size_t kCaseCount = {len(cases)}U;",
        f"inline constexpr std::size_t kBindingCount = {len(BINDING_NAMES)}U;",
        "",
        f"inline constexpr std::array<std::string_view, {len(BINDING_NAMES)}> "
        "kBindingNames{{",
        "    " + ", ".join(f'"{name}"' for name in BINDING_NAMES) + ",",
        "}};", "",
    ]
    for index, case in enumerate(cases):
        # The input texture travels with the case (normalMap precedent): the
        # native test binds it as inputTex verbatim, and a pattern name would
        # be a second chance to disagree with the authority.
        texture = case["input_texture"]
        lines.append(
            f"inline constexpr std::array<std::uint32_t, "
            f"{len(texture['f32_words_le'])}> kCase{index}InputWords{{{{")
        lines.extend(array_lines(texture["f32_words_le"], "U", 8))
        lines.extend(["}};", ""])
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
    full = translation["full_route_expected"]
    lines.append(
        f"inline constexpr std::array<std::uint32_t, "
        f"{len(full['f32_words_le'])}> kTranslationFullExpectedWords{{{{")
    lines.extend(array_lines(full["f32_words_le"], "U", 8))
    lines.extend(["}};", ""])
    lines.append(
        f"inline constexpr std::array<std::uint8_t, "
        f"{len(full['rgba8_bytes'])}> kTranslationFullExpectedRgba8{{{{")
    lines.extend(array_lines(full["rgba8_bytes"], "U", 16))
    lines.extend(["}};", ""])
    lines.extend([
        "struct CaseView {",
        "  std::string_view name;",
        "  std::size_t width;",
        "  std::size_t height;",
        "  std::string_view route;",
        "  std::size_t input_width;",
        "  std::size_t input_height;",
        "  std::string_view input_f32_sha256;",
        "  std::span<const std::uint32_t> input_words;",
        "  std::span<const std::uint32_t> expected_words;",
        "  std::span<const std::uint8_t> expected_rgba8;",
        "  std::uint32_t time_word;",
        "  std::int32_t seed;",
        "  std::int32_t wrap;",
        "  std::array<std::uint32_t, 2> resolution_words;",
        "  std::array<std::uint32_t, 2> tile_offset_words;",
        "  std::array<std::uint32_t, 2> full_resolution_words;",
        "  std::uint32_t scale_word;",
        "  std::uint32_t cell_scale_word;",
        "  std::uint32_t cell_smooth_word;",
        "  std::uint32_t variation_word;",
        "  std::uint32_t speed_word;",
        "  std::uint32_t refract_amt_word;",
        "  std::uint32_t direction_word;",
        "  std::uint32_t effect_width_word;",
        "  std::uint32_t external_time_word;",
        "  std::uint32_t external_seed_word;",
        "};", "",
        "// The Shapes crop contract does NOT hold for this program: the tile",
        "// output is a measured non-crop of the full route (the counts below),",
        "// because localUV subtracts tileOffset again before sampling. The",
        "// full-route arrays above are a parity surface in their own right;",
        "// never compare the tile against a crop of them.",
        "struct TranslationProofView {",
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
        "  std::size_t measured_word_mismatches;",
        "  std::size_t measured_byte_mismatches;",
        "  std::size_t raw_crop_y_trap_changed_lanes;",
        "};", "",
        "struct MutantSetView {",
        "  std::string_view mutant;",
        "  std::span<const std::string_view> witness_cases;",
        "  std::span<const std::string_view> control_cases;",
        "};", "",
        "// One row per mutant per case: the frozen per-case discrimination",
        "// ledger. A per-mutant summary is deliberately not materialized.",
        "struct MutantWitnessView {",
        "  std::string_view mutant;",
        "  std::string_view case_name;",
        "  bool discriminates;",
        "};", "",
        "struct ControlView {",
        "  std::string_view name;",
        "  std::string_view expectation;",
        "  std::string_view observed;",
        "};", "",
        f"inline constexpr std::array<CaseView, {len(cases)}> kCases{{{{",
    ])
    for index, case in enumerate(cases):
        binding = case["bindings"]
        external = case["external_pass"]
        input_texture = case["input_texture"]
        parts = [
            f'CaseView{{"{case["name"]}", {case["width"]}U, {case["height"]}U, '
            f'"{case["route"]}", {input_texture["width"]}U, {input_texture["height"]}U, '
            f'"{binding["inputTex"]["f32_sha256"]}", kCase{index}InputWords, '
            f'kCase{index}ExpectedWords, '
            f'kCase{index}ExpectedRgba8, '
            f'{binding["time"]["f32_word_le"]}U, {binding["seed"]["value"]}, '
            f'{binding["wrap"]["value"]}, '
            f'{{{word_list(binding["resolution"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["tileOffset"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["fullResolution"]["f32_words_le"])}}},',
        ]
        scalar_line = ", ".join(
            f'{binding[name]["f32_word_le"]}U' for name in
            ("scale", "cellScale", "cellSmooth", "variation", "speed",
             "refractAmt", "direction", "effectWidth"))
        parts.append(f"    {scalar_line}, "
                     f'{external["time"]["f32_word_le"]}U, '
                     f'{external["seed"]["f32_word_le"]}U}},')
        lines.append("  " + " ".join(parts))
    rect = translation["rect"]
    ledger_rows = [(mutant["name"], result["case"], result["differs"])
                   for mutant in oracle["mutation_ledger"]
                   for result in mutant["results"]]
    control_rows = [(control["name"], control["expectation"], control["observed"])
                    for control in oracle["control_group"]["controls"]]
    lines.extend([
        "}};", "",
        "inline constexpr TranslationProofView kTranslationProof{",
        f'    "{translation["case"]}", {rect["crop_x"]}U, {rect["crop_y"]}U, '
        f'{rect["tile_width"]}U, {rect["tile_height"]}U, '
        f'{rect["full_width"]}U, {rect["full_height"]}U,',
        f'    {{{word_list(translation["tile_offset_f32_words_le"])}}}, '
        "kTranslationFullExpectedWords, kTranslationFullExpectedRgba8,",
        f'    {translation["word_mismatches"]}U, '
        f'{translation["byte_mismatches"]}U, '
        f'{translation["raw_crop_y_trap"]["changed_lane_count"]}U}};', "",
        f"inline constexpr std::array<MutantWitnessView, {len(ledger_rows)}> "
        "kMutantWitnesses{{",
    ])
    for mutant_name, case_name, differs in ledger_rows:
        lines.append(f'  MutantWitnessView{{"{mutant_name}", "{case_name}", '
                     f'{str(differs).lower()}}},')
    lines.extend(["}};", ""])
    for index, mutant in enumerate(oracle["mutation_ledger"]):
        for kind, names_ in (("Witness", mutant["witness_cases"]),
                             ("Control", mutant["control_cases"])):
            lines.append(
                f"inline constexpr std::array<std::string_view, {len(names_)}> "
                f"kMutant{index}{kind}Cases"
                + ("{{" if names_ else "{};"))
            if names_:
                lines.append("    " + ", ".join(f'"{name}"' for name in names_) + ",")
                lines.extend(["}};", ""])
            else:
                # A zero-length std::array has no elements to list, and a bare
                # comma would not compile: `prng-pcg-constant-perturbed` has no
                # control cases, so this arm is exercised by the real data.
                lines.append("")
    lines.append(
        f"inline constexpr std::array<MutantSetView, "
        f"{len(oracle['mutation_ledger'])}> kMutantSets{{{{")
    for index, mutant in enumerate(oracle["mutation_ledger"]):
        lines.append(f'  MutantSetView{{"{mutant["name"]}", '
                     f'kMutant{index}WitnessCases, kMutant{index}ControlCases}},')
    lines.extend([
        "}};", "",
        f"inline constexpr std::array<ControlView, {len(control_rows)}> "
        "kControls{{",
    ])
    for name, expectation, observed in control_rows:
        lines.append(f'  ControlView{{"{name}", "{expectation}", "{observed}"}},')
    lines.extend([
        "}};", "",
        f'inline constexpr std::uint32_t kAlphaWord = {ALPHA_WORD}U;',
        f"inline constexpr std::uint8_t kAlphaByte = {ALPHA_BYTE}U;", "",
        "}  // namespace cellrefract186_oracle", "",
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
    for name in ("cellrefract186-oracles.json", "cellrefract-oracle-report.md",
                 "cellrefract186_oracle_generator.mjs"):
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


def _bind_raw_crop_y(doc: dict[str, Any]) -> None:
    """Bind raw top-down `crop_y` into tileOffset.y, self-consistently."""
    rect = doc["tile_translation"]["rect"]
    offset = (float(rect["crop_x"]), float(rect["crop_y"]))
    words = [f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"
             for value in offset]
    tile = next(case for case in doc["render_cases"] if case["name"] == TILE_CASE)
    tile["bindings"]["tileOffset"]["f32_words_le"] = words
    tile["bindings"]["tileOffset"]["f32_values"] = list(offset)
    doc["tile_translation"]["tile_offset_f32_words_le"] = words


def _forge_translation_counts(doc: dict[str, Any]) -> None:
    """Claim fewer mismatches than the stored arrays show."""
    doc["tile_translation"]["word_mismatches"] = 3
    doc["tile_translation"]["byte_mismatches"] = 3


def _forge_d_field(doc: dict[str, Any]) -> None:
    """Rewrite one stored tile d word and refresh the digest."""
    witness = doc["tile_translation"]["d_field_alignment_witness"]
    witness["tile_d_words_le"][0] = "0x7f7fffff"
    witness["tile_d_sha256"] = sha256(packed_words(witness["tile_d_words_le"]))


def _forge_local_uv(doc: dict[str, Any]) -> None:
    """Claim three equal lanes; the stored arrays show none."""
    doc["tile_translation"]["local_uv_translation_witness"]["equal_lane_count"] = 3


def _fabricate_control(doc: dict[str, Any]) -> None:
    """Swap a lane of the `identical` kernel control for a foreign value."""
    surface = doc["control_group"]["controls"][1]["output"]
    surface["f32_words_le"][0] = "0x7f7fffff"
    surface["rgba8_bytes"][0] = 7
    _refresh_surface_digests(surface)


def _fabricate_kernel_probe(doc: dict[str, Any]) -> None:
    """Claim the unbound-KERNEL probe differs."""
    doc["kernel_liveness_census"]["probes"][0]["differs_from_baseline"] = True
    doc["kernel_liveness_census"]["probes"][0]["changed_lane_count"] = 12


def _fabricate_inert_probe(doc: dict[str, Any]) -> None:
    """Claim an inert resolution probe differs while carrying the anchor digest."""
    doc["binding_inertness_census"]["inert"][0]["probes"][0][
        "differs_from_baseline"] = True


def _fabricate_live_probe(doc: dict[str, Any]) -> None:
    """Give a live probe the anchor digest while claiming it differs."""
    anchor = next(case for case in doc["render_cases"]
                  if case["name"] == ANCHOR_CASE)["output_expected"]["f32_sha256"]
    doc["binding_liveness_census"]["probes"][0]["f32_sha256"] = anchor


def _fabricate_phase(doc: dict[str, Any]) -> None:
    """Flip the anchor's phase integrality."""
    doc["time_speed_phase_census"]["per_case_phase"][0][
        "phase_is_integral"] = False


def _collapse_speed(doc: dict[str, Any]) -> None:
    """Give one odd-class probe a foreign digest, creating a third class."""
    doc["speed_class_census"]["probes"][1]["f32_sha256"] = "e" * 64


def _fabricate_mutant_digest(doc: dict[str, Any]) -> None:
    """Give a witness row the canonical case's own digests."""
    ledger = doc["mutation_ledger"][0]
    row = next(item for item in ledger["results"]
               if item["case"] == ANCHOR_CASE)
    canonical = next(case for case in doc["render_cases"]
                     if case["name"] == ANCHOR_CASE)["output_expected"]
    row["f32_sha256"] = canonical["f32_sha256"]
    row["rgba8_sha256"] = canonical["rgba8_sha256"]


def _forge_nonreaching(doc: dict[str, Any]) -> None:
    row = doc["nonreaching_control_mutant"]["rendered_mutant"]["rows"][0]
    row["differs"] = True
    row["changed_lane_count"] = 5


def _forge_table_axis(doc: dict[str, Any]) -> None:
    row = doc["write_only_tables_axis"]["rendered_mutant"]["rows"][0]
    row["differs"] = True
    row["changed_lane_count"] = 5


def _forge_near_ulp(doc: dict[str, Any]) -> None:
    row = doc["prng_near_ulp_invariance"]["rendered_mutant"]["rows"][0]
    row["differs"] = True
    row["changed_lane_count"] = 5


def self_test() -> int:
    base, _ = load(LIVE)
    scenarios: tuple[tuple[str, Callable[[dict[str, Any]], None], str], ...] = (
        ("missing-top-level-field",
         lambda doc: doc.pop("tile_translation"), "missing field(s) tile_translation"),
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
         lambda doc: doc["render_cases"][0]["bindings"]["speed"].__setitem__(
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
        ("wrong-source-digest",
         lambda doc: doc["provenance"]["source"].__setitem__("sha256", "0" * 64),
         "pinned GLSL source mismatch"),
        ("define-drift",
         lambda doc: doc["defines"].__setitem__("KERNEL", 1),
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
        ("non-int32-wrap",
         lambda doc: doc["render_cases"][0]["bindings"]["wrap"].__setitem__(
             "value", "mirror"), "int32 value required"),
        ("table-declaration-drift",
         lambda doc: doc["mutable_global_contracts"]["emboss"].__setitem__(
             "javascript_declaration", "var emboss = new Float32Array(9);"),
         "declaration drift"),
        ("table-float32-materialization",
         lambda doc: doc["mutable_global_contracts"]["emboss"].__setitem__(
             "element_materialization", "a Float32Array of f32 lanes"),
         "plain Array, never a Float32Array"),
        ("table-recorded-discriminable",
         lambda doc: doc["mutable_global_contracts"]["blur"].__setitem__(
             "oracle_discriminable", True),
         "must never be recorded discriminable"),
        ("table-element-drift",
         lambda doc: doc["mutable_global_contracts"]["edge"].__setitem__(
             "elements", [-1, -1, -1, -1, 9, -1, -1, -1, -1]),
         "element census drift"),
        ("table-axis-forged-divergence", _forge_table_axis,
         "the row must be invariant"),
        ("alpha-word-drift", _break_alpha_word, "alpha Float32 word at lane 3"),
        ("alpha-byte-drift", _break_alpha_byte, "alpha RGBA8 byte at lane 3"),
        ("tile-offset-drift", _bind_raw_crop_y, "tileOffset is not"),
        ("tile-full-route-digest",
         lambda doc: doc["tile_translation"]["full_route_expected"]
         ["f32_words_le"].__setitem__(0, "0x00000000"),
         "Float32 digest mismatch"),
        ("tile-claims-exact-crop",
         lambda doc: doc["tile_translation"].__setitem__("is_exact_crop", True),
         "may not be asserted"),
        ("tile-mismatch-counts-forged", _forge_translation_counts,
         "recorded mismatch counts disagree"),
        ("tile-d-field-forged", _forge_d_field,
         "not an exact crop of the full route"),
        ("tile-local-uv-forged", _forge_local_uv,
         "translation account disagrees"),
        ("tile-vacuous-trap",
         lambda doc: doc["tile_translation"]["raw_crop_y_trap"].__setitem__(
             "changed_lane_count", 0), "raw crop_y trap is vacuous"),
        ("external-control-drift",
         lambda doc: doc["control_group"]["controls"][0].__setitem__(
             "observed", "differs"),
         "pass ledger disagrees with observation"),
        ("kernel-control-drift",
         lambda doc: (
             doc["control_group"]["controls"][1].__setitem__("observed", "differs"),
             doc["control_group"]["controls"][1].__setitem__("pass", False)),
         "control did not pass"),
        ("baseline-digest-drift",
         lambda doc: doc["control_group"]["baseline"].__setitem__(
             "f32_sha256", "0" * 64),
         "digests disagree with the anchor case"),
        ("fabricated-kernel-control", _fabricate_control,
         "recorded observation 'identical' disagrees with the stored arrays"),
        ("kernel-probe-fabricated", _fabricate_kernel_probe,
         "verdict disagrees with the recorded digest"),
        ("kernel-unbound-differs",
         lambda doc: (
             doc["kernel_liveness_census"]["probes"][0].__setitem__(
                 "f32_sha256", "f" * 64),
             doc["kernel_liveness_census"]["probes"][0].__setitem__(
                 "differs_from_baseline", True),
             doc["kernel_liveness_census"]["probes"][0].__setitem__(
                 "changed_lane_count", 3)),
         "the unbound/0 probes are not invariant"),
        ("inert-probe-fabricated", _fabricate_inert_probe,
         "carry the anchor digest"),
        ("live-probe-fabricated", _fabricate_live_probe,
         "a live probe carries the anchor digest"),
        ("phase-integrality-fabricated", _fabricate_phase, "integrality drift"),
        ("phase-probe-observation-drift",
         lambda doc: doc["time_speed_phase_census"]["probes"][0].__setitem__(
             "observed", "differs"),
         "must be identical"),
        ("collapsed-speed-census", _collapse_speed,
         "distinct digest count drift"),
        ("mutant-census-drift",
         lambda doc: doc["mutation_ledger"].pop(), "mutant census mismatch"),
        ("mutant-per-case-table-drift",
         lambda doc: doc["mutation_discrimination_contract"]["expected"]
         ["aspect-ratio-inverted"].__setitem__("cells-extreme-variation", True),
         "does not match the frozen table"),
        ("mutant-row-expectation-drift",
         lambda doc: doc["mutation_ledger"][0]["results"][2].__setitem__(
             "expected_discriminates", True),
         "carries the wrong per-case expectation"),
        ("mutant-witness-non-discriminating",
         lambda doc: doc["mutation_ledger"][0]["results"][0].__setitem__(
             "differs", False), "but the ledger records False"),
        ("mutant-control-changed",
         lambda doc: doc["mutation_ledger"][3]["results"][3].__setitem__(
             "differs", True), "but the ledger records True"),
        ("fabricated-mutant-digest", _fabricate_mutant_digest,
         "but its mutant digests say otherwise"),
        ("mutant-partition-drift",
         lambda doc: doc["mutation_ledger"][0]["witness_cases"].append("bogus"),
         "witness/control partition drift"),
        ("witness-sets-drift",
         lambda doc: doc["mutation_discrimination_contract"]["witness_sets"]
         ["wrap-arm-swapped"].__setitem__(
             "witness_cases", ["cells-wrap-mirror"]),
         "disagrees with the frozen per-case table"),
        ("overlap-undisclosed",
         lambda doc: doc["mutation_discrimination_contract"].__setitem__(
             "witness_overlap_disclosure", "the sets are disjoint"),
         "witness overlap must be disclosed"),
        ("nonreaching-forged", _forge_nonreaching,
         "the row must be invariant"),
        ("near-ulp-forged", _forge_near_ulp,
         "the row must be invariant"),
        ("excluded-ledger-entry-dropped",
         lambda doc: doc["mutation_discrimination_contract"]
         ["excluded_from_ledger"].pop("kernel4-arm-emboss-to-sharpen"),
         "missing field(s) kernel4-arm-emboss-to-sharpen"),
        ("input-texture-digest-drift",
         lambda doc: doc["render_cases"][0]["input_texture"].__setitem__(
             "f32_sha256", "0" * 64), "Float32 digest mismatch"),
        ("inputtex-binding-disagreement",
         lambda doc: doc["render_cases"][0]["bindings"]["inputTex"].__setitem__(
             "f32_sha256", "0" * 64),
         "inputTex binding digest disagrees"),
        ("coverage-names-unknown-case",
         lambda doc: doc["coverage_axes"]["route"]["full"].append("bogus"),
         "names unknown case bogus"),
        ("self-test-ledger-drift",
         lambda doc: doc["comparer_self_tests"].__setitem__(
             "signed_zero_rejected_with_equal_rgba8", False),
         "comparer self-test mismatch"),
    )
    passed = 0
    with tempfile.TemporaryDirectory(prefix="cellrefract186-selftest-") as raw:
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
        _expect_rejection(broken_json, "invalid Cellrefract186 JSON", "broken-json")
        passed += 1
    print(f"Cellrefract186 native oracle materializer self-test ok ({passed} checks)")
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
                    "generated Cellrefract186 native include is stale")
    except (OSError, OracleError) as error:
        print(f"glslcpp: {error}", file=sys.stderr)
        return 1
    oracle, _ = load(LIVE)
    words = sum(len(case["output_expected"]["f32_words_le"])
                for case in oracle["render_cases"])
    witnesses = {mutant["name"]: len(mutant["witness_cases"])
                 for mutant in oracle["mutation_ledger"]}
    translation = oracle["tile_translation"]
    print(f"Cellrefract186 native oracle include ok "
          f"({len(EXPECTED_CASES)} cases, {words} case words, "
          f"{len(translation['full_route_expected']['f32_words_le'])} full-route words, "
          f"{len(MUTANTS)} mutants, per-case witnesses "
          + ", ".join(f"{name}={count}" for name, count in witnesses.items())
          + f", tile non-crop {translation['word_mismatches']}/"
          f"{translation['rect']['tile_width'] * translation['rect']['tile_height'] * 4} words)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
