#!/usr/bin/env python3
"""Generate the checked native Normalmap185 fixture from the canonical JS JSON.

This is the sole JSON-to-C++ materializer for `filter/normalMap:normalMap`. It
never renders anything: every expected word and byte originates in
`docs/port-engineering/normalmap-parity/normalmap-oracles.json`, which is
produced by the canonical JavaScript oracle generator. The materializer is
fail-closed and rejects missing or extra fields, duplicate case names,
malformed dimensions, counts, hex words or byte values, wrong digests, wrong or
missing sidecars, and truncated or extra arrays. `--self-test` proves each
rejection.

Nothing recorded as prose is trusted. Every observation the document reports --
control identity, binding inertness, the amendment 11 transpose equivalence, the
amendment 12 round invariance, the kernel-table narrowing impossibility, the
per-pixel re-evaluation equivalence, the amendment 15 pooled-table hazard, the
double accumulator, fragColor persistence, and per-case mutant discrimination --
is RE-DERIVED here from the stored arrays and digests, so a hand-edited verdict
with refreshed hashes cannot survive.

Every number the emitted include asserts is emitted FROM the document. Nothing
is transcribed out of the report markdown, because a transcribed literal
survives a regeneration and then reads as a native regression.
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
PACKAGE = ROOT / "docs/port-engineering/normalmap-parity"
OUTPUT = ROOT / "tests/oracles/normalmap_expected.inc"
TOOL = pathlib.Path(__file__).resolve()

SCHEMA = "noisemaker-for-cpp.normalmap185.pixel-parity.v1"
SCHEMA_VERSION = 1
PROGRAM_KEY = "filter/normalMap:normalMap"
EFFECT_KEY = "filter/normalMap"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
FACTORY_NAME = "canonicalFactory86"
FACTORY_SHA256 = "9b1348836825b6efe90109747ca5ef341651527077d8ad7dbbcbc7080369842a"
SOURCE_RELATIVE = (
    f"tools/glslcpp/corpus/{CORPUS_REVISION}"
    "/sources/filter/normalMap/normalMap.glsl")
SOURCE_BYTES = 4017
SOURCE_LINES = 155
SOURCE_SHA256 = (
    "384312e50972f75dbebd4080cd76d1c2554a439eb36746f2e351d63a03a271cb")
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

# The Python-side eligibility table, which `filter/normalMap:normalMap` must
# stay out of. Read from the LIVE `check_corpus` module, never transcribed:
# comparing one frozen copy against another frozen copy proves nothing, and
# would stay green if the key were ever added to the real table.
CORPUS_ADAPTER_SOURCE = "tools/glslcpp/check_corpus.py"
CORPUS_ADAPTER_CENSUS_EXPECTED = frozenset({
    "classicNoisedeck/fractal:fractal",
    "filter/historicPalette:historicPalette",
    "filter/palette:palette",
    "synth/julia:julia",
})

CPU_ROOT_PLACEHOLDER = "<immutable-cpu-snapshot-root>"
LIVE_CHECKOUT_PLACEHOLDER = "<live-noisemaker-for-cpu-checkout>"
# A checked-in gate must not carry a machine-specific path anywhere. `$HOME/...`
# and `<placeholder>` forms are fine; a rooted filesystem path is not.
ABSOLUTE_PATH = re.compile(r"(?:^/|/Users/|/home/|/private/|/var/|/tmp/|/opt/)")

WORD = re.compile(r"0x[0-9a-f]{8}")
HEX64 = re.compile(r"[0-9a-f]{64}")
OPAQUE_ALPHA_WORD = "0x3f800000"
OPAQUE_ALPHA_BYTE = 255

BINDING_NAMES = ("tileOffset", "fullResolution", "inputTex", "size", "motion")
BINDING_ABI = {
    "tileOffset": "Vec2", "fullResolution": "Vec2", "inputTex": "sampler2D",
    "size": "Vec4", "motion": "Vec4",
}
VEC_LANES = {"Vec2": 2, "Vec4": 4}

# (name, width, height, route, input_pattern, opaque_input)
EXPECTED_CASES = (
    ("normalmap-default-16x9", 16, 9, "production-binding-set", "ramp", True),
    ("normalmap-default-7x5", 7, 5, "production-binding-set", "ramp", True),
    ("normalmap-high-contrast-8x6", 8, 6, "production-binding-set",
     "contrast", True),
    ("normalmap-channelcount-2-8x6", 8, 6, "synthetic-size", "ramp", True),
    ("normalmap-channelcount-3-oklab-8x6", 8, 6, "synthetic-size", "ramp",
     True),
    ("normalmap-channelcount-4-clamped-8x6", 8, 6, "synthetic-size", "wide",
     True),
    ("normalmap-explicit-size-larger-8x6", 8, 6, "synthetic-size", "ramp",
     True),
    ("normalmap-flat-alpha-8x6", 8, 6, "production-binding-set", "flat",
     False),
)
CASE_NAMES = tuple(name for name, _, _, _, _, _ in EXPECTED_CASES)
ANCHOR_CASE = "normalmap-default-16x9"
FLAT_CASE = "normalmap-flat-alpha-8x6"

# The per-case, per-mutant discrimination ledger. A per-mutant summary is not
# sufficient: every cell is frozen and every cell is checked.
MUTANT_DISCRIMINATION = {
    "normalmap-sobel-x-y-swapped": {
        "normalmap-default-16x9": True,
        "normalmap-default-7x5": True,
        "normalmap-high-contrast-8x6": True,
        "normalmap-channelcount-2-8x6": True,
        "normalmap-channelcount-3-oklab-8x6": True,
        "normalmap-channelcount-4-clamped-8x6": True,
        "normalmap-explicit-size-larger-8x6": True,
        "normalmap-flat-alpha-8x6": False,
    },
    "normalmap-alpha-source-transposed": {
        "normalmap-default-16x9": False,
        "normalmap-default-7x5": False,
        "normalmap-high-contrast-8x6": False,
        "normalmap-channelcount-2-8x6": False,
        "normalmap-channelcount-3-oklab-8x6": False,
        "normalmap-channelcount-4-clamped-8x6": False,
        "normalmap-explicit-size-larger-8x6": False,
        "normalmap-flat-alpha-8x6": True,
    },
}
MUTANTS = tuple(MUTANT_DISCRIMINATION)

# (name, expectation)
CONTROLS = (
    ("external-pass-extreme", "identical"),
    ("motion-extreme", "identical"),
    ("tile-offset-extreme", "identical"),
    ("full-resolution-extreme", "identical"),
    ("size-w-extreme", "identical"),
    ("size-z-three", "differs"),
    ("size-xy-smaller", "differs"),
)
INERT_BINDINGS = ("motion", "fullResolution", "tileOffset")
LIVE_BINDINGS = ("inputTex", "size")
KERNEL_CENSUS_MUTANTS = (
    "normalmap-sobel-x-negated", "normalmap-sobel-x1-perturbed")
ARM_SWEEP_PATTERNS = ("ramp", "wide")
VALUE_MAP_ARMS = [0, 1, 2, 3, 4]
SOBEL_X_KERNEL = (0.5, 0.0, -0.5, 1.0, 0.0, -1.0, 0.5, 0.0, -0.5)
SOBEL_Y_KERNEL = (0.5, 1.0, 0.5, 0.0, 0.0, 0.0, -0.5, -1.0, -0.5)
SOBEL_OFFSETS = ((-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0),
                 (-1, 1), (0, 1), (1, 1))
ACCUMULATOR_WITNESSES = (
    "normalmap-channelcount-3-oklab-8x6",
    "normalmap-channelcount-4-clamped-8x6")
POOLED_PROBE_LANES = (111.0, 444.0, -11.0, -44.0)

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
    "corpus_revision", "upstream_revision", "defines",
    "preprocessor_define_count", "runtime_binding_names",
    "runtime_binding_abi", "oracle_authority", "const_global_table_contracts",
    "exactness_contract", "provenance", "comparer_self_tests",
    "coverage_axes", "render_cases", "control_group",
    "binding_inertness_census", "transpose_equivalence_proof",
    "kernel_table_mutant_census", "kernel_table_narrowing_axis",
    "as_u32_round_axis", "per_pixel_reevaluation_equivalence",
    "pooled_table_hazard", "accumulator_double_census",
    "value_map_arm_census",
    "fragcolor_persistence_witness", "mutation_ledger",
    "mutation_discrimination_contract", "claim_boundaries",
}
CASE_KEYS = {
    "name", "coverage", "route", "width", "height", "input_pattern",
    "opaque_input", "input_texture", "bindings", "external_pass",
    "output_expected", "canonical_repeat", "public_canonical",
}
SURFACE_KEYS = {
    "width", "height", "f32_words_le", "f32_sha256", "rgba8_bytes",
    "rgba8_sha256", "finite_lane_count", "nonfinite_lane_count",
    "distinct_alpha_f32_word_count", "alpha_f32_words_le",
    "distinct_alpha_rgba8_byte_count",
}
INPUT_KEYS = {
    "width", "height", "row_order", "f32_words_le", "f32_sha256",
    "every_lane_exactly_f32_representable",
}


class OracleError(RuntimeError):
    pass


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


@dataclasses.dataclass(frozen=True)
class Paths:
    package: pathlib.Path
    tool: pathlib.Path
    output: pathlib.Path

    @property
    def oracle(self) -> pathlib.Path:
        return self.package / "normalmap-oracles.json"

    @property
    def report(self) -> pathlib.Path:
        return self.package / "normalmap-oracle-report.md"

    @property
    def generator(self) -> pathlib.Path:
        return self.package / "normalmap_oracle_generator.mjs"


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


def require_keys(value: object, expected: set[str],
                 label: str) -> dict[str, Any]:
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


def require_count(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise OracleError(f"{label}: non-negative integer required")
    return value


def require_true(value: object, label: str) -> None:
    if value is not True:
        raise OracleError(f"{label}: must be recorded true")


def require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OracleError(f"{label}: non-empty prose required")
    return value


def packed_words(words: list[str]) -> bytes:
    return b"".join(struct.pack("<I", int(word, 16)) for word in words)


def word_to_float(word: str) -> float:
    return struct.unpack("<f", struct.pack("<I", int(word, 16)))[0]


def exactly_f32(value: float) -> bool:
    return struct.unpack("<f", struct.pack("<f", value))[0] == value


def validate_input_texture(record: object, width: int, height: int,
                           label: str) -> dict[str, Any]:
    texture = require_keys(record, INPUT_KEYS, label)
    require_dimension(texture.get("width"), width, f"{label}.width")
    require_dimension(texture.get("height"), height, f"{label}.height")
    words = require_word_array(texture.get("f32_words_le"),
                               width * height * 4, label)
    if sha256(packed_words(words)) != require_hex64(
            texture.get("f32_sha256"), f"{label}.f32_sha256"):
        raise OracleError(f"{label}: input texture Float32 digest mismatch")
    require_true(texture.get("every_lane_exactly_f32_representable"),
                 f"{label}.every_lane_exactly_f32_representable")
    for index, word in enumerate(words):
        value = word_to_float(word)
        if value != value or value in (float("inf"), float("-inf")):
            raise OracleError(
                f"{label}: non-finite input lane at {index}")
        if not exactly_f32(value):
            raise OracleError(
                f"{label}: input lane at {index} is not exactly "
                "f32-representable")
    require_text(texture.get("row_order"), f"{label}.row_order")
    return texture


def validate_surface(record: object, width: int, height: int, label: str,
                     opaque: bool | None = None) -> dict[str, Any]:
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
    if nonfinite != 0:
        raise OracleError(f"{label}: non-finite output lane recorded")
    alpha_words = sorted({words[index] for index in range(3, count, 4)})
    alpha_bytes = {rgba[index] for index in range(3, count, 4)}
    if alpha_words != sorted(surface.get("alpha_f32_words_le") or []):
        raise OracleError(f"{label}: alpha word census disagrees with the "
                          "stored lanes")
    if len(alpha_words) != surface.get("distinct_alpha_f32_word_count"):
        raise OracleError(f"{label}: distinct alpha word count disagrees")
    if len(alpha_bytes) != surface.get("distinct_alpha_rgba8_byte_count"):
        raise OracleError(f"{label}: distinct alpha byte count disagrees")
    if opaque is True:
        if alpha_words != [OPAQUE_ALPHA_WORD] or alpha_bytes != {
                OPAQUE_ALPHA_BYTE}:
            raise OracleError(
                f"{label}: an opaque case must carry a uniform "
                f"{OPAQUE_ALPHA_WORD}/{OPAQUE_ALPHA_BYTE} alpha lane")
    if opaque is False and len(alpha_words) < 2:
        raise OracleError(
            f"{label}: the varying-alpha case must carry more than one "
            "alpha word")
    return surface


def validate_bindings(record: object, label: str, input_digest: str,
                      width: int, height: int) -> dict[str, Any]:
    bindings = require_keys(record, set(BINDING_NAMES), label)
    for name in BINDING_NAMES:
        abi = BINDING_ABI[name]
        entry = bindings[name]
        if not isinstance(entry, dict) or entry.get("abi") != abi:
            raise OracleError(f"{label}.{name}: ABI drift")
        if abi == "sampler2D":
            require_dimension(entry.get("width"), width, f"{label}.{name}.width")
            require_dimension(entry.get("height"), height,
                              f"{label}.{name}.height")
            if entry.get("f32_sha256") != input_digest:
                raise OracleError(
                    f"{label}.{name}: sampler digest disagrees with the "
                    "stored input texture")
            if set(entry) != {"abi", "width", "height", "f32_sha256"}:
                raise OracleError(f"{label}.{name}: sampler field drift")
            continue
        lanes = VEC_LANES[abi]
        if set(entry) != {"abi", "f32_values", "f32_words_le"}:
            raise OracleError(f"{label}.{name}: vector field drift")
        words = require_word_array(entry.get("f32_words_le"), lanes,
                                   f"{label}.{name}")
        values = entry.get("f32_values")
        if not isinstance(values, list) or len(values) != lanes:
            raise OracleError(f"{label}.{name}: expected {lanes} lane values")
        for index, (word, value) in enumerate(zip(words, values)):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise OracleError(f"{label}.{name}: malformed lane {index}")
            decoded = word_to_float(word)
            if decoded != float(value):
                raise OracleError(
                    f"{label}.{name}: f32 word disagrees with its value at "
                    f"lane {index}")
    return bindings


def validate_external(record: object, label: str) -> dict[str, Any]:
    external = require_keys(record, {"time", "seed"}, label)
    for name in ("time", "seed"):
        entry = require_keys(external[name], {"f32_value", "f32_word_le"},
                             f"{label}.{name}")
        word = entry.get("f32_word_le")
        if not isinstance(word, str) or not WORD.fullmatch(word):
            raise OracleError(f"{label}.{name}: malformed Float32 word at 0")
        if word_to_float(word) != float(entry.get("f32_value")):
            raise OracleError(
                f"{label}.{name}: f32 word disagrees with its value")
    return external


def validate_identity(record: object, label: str) -> None:
    identity = require_keys(record, {
        "exact", "changed_lane_count", "changed_rgba8_byte_count",
        "expected_dimensions", "actual_dimensions"}, label)
    if (identity["exact"] is not True or identity["changed_lane_count"] != 0
            or identity["changed_rgba8_byte_count"] != 0
            or identity["expected_dimensions"] != identity["actual_dimensions"]):
        raise OracleError(f"{label}: route identity was not exact")


def validate_provenance(oracle: dict[str, Any], paths: Paths) -> None:
    provenance = oracle["provenance"]
    for name, target in (("generator", paths.generator),
                         ("native_include_generator", paths.tool)):
        entry = provenance.get(name)
        if not isinstance(entry, dict):
            raise OracleError(f"provenance.{name}: object required")
        if sha256(target.read_bytes()) != entry.get("sha256"):
            raise OracleError(
                f"provenance.{name}: recorded digest does not match the file")
        relative = entry.get("relative_path_from_noisemaker_for_cpp")
        if not isinstance(relative, str) or relative.startswith("/"):
            raise OracleError(f"provenance.{name}: relative path required")
    snapshot = provenance.get("cpu_snapshot")
    if not isinstance(snapshot, dict):
        raise OracleError("provenance.cpu_snapshot: object required")
    if (snapshot.get("argument") != CPU_ROOT_PLACEHOLDER
            or snapshot.get("live_checkout_rejected")
            != LIVE_CHECKOUT_PLACEHOLDER):
        raise OracleError(
            "provenance.cpu_snapshot: the snapshot and live-checkout paths "
            "must be recorded as stable placeholders")
    require_true(snapshot.get("immutable_snapshot"),
                 "provenance.cpu_snapshot.immutable_snapshot")
    require_true(snapshot.get("imports_confined_beneath_snapshot"),
                 "provenance.cpu_snapshot.imports_confined_beneath_snapshot")
    closure = snapshot.get("import_closure")
    if (not isinstance(closure, list) or not closure
            or len(closure) != snapshot.get("import_closure_file_count")):
        raise OracleError("provenance.cpu_snapshot: import closure census drift")
    for entry in closure:
        relative = entry.get("relative_path_from_noisemaker_for_cpu")
        if not isinstance(relative, str) or relative.startswith("/"):
            raise OracleError(
                "provenance.cpu_snapshot: import closure entry is not relative")
        require_hex64(entry.get("sha256"), "provenance.cpu_snapshot closure")
    pinned = snapshot.get("pinned_files")
    if not isinstance(pinned, dict) or set(pinned) != set(PINNED_CPU_FILES):
        raise OracleError("provenance.cpu_snapshot: pinned CPU file census drift")
    for name, (relative, digest) in PINNED_CPU_FILES.items():
        entry = pinned[name]
        if (entry.get("relative_path_from_noisemaker_for_cpu") != relative
                or entry.get("sha256") != digest):
            raise OracleError(f"pinned CPU file {name} mismatch")
    source = provenance.get("source")
    if (not isinstance(source, dict)
            or source.get("relative_path_from_noisemaker_for_cpp")
            != SOURCE_RELATIVE
            or source.get("bytes") != SOURCE_BYTES
            or source.get("lines") != SOURCE_LINES
            or source.get("sha256") != SOURCE_SHA256
            or source.get("preprocessor_defines") != []):
        raise OracleError("pinned GLSL source mismatch")
    on_disk = ROOT / SOURCE_RELATIVE
    if not on_disk.is_file() or sha256(on_disk.read_bytes()) != SOURCE_SHA256:
        raise OracleError("pinned GLSL source mismatch on disk")
    factory = provenance.get("canonical_factory")
    if (not isinstance(factory, dict) or factory.get("name") != FACTORY_NAME
            or factory.get("sha256") != FACTORY_SHA256):
        raise OracleError("canonical factory identity mismatch")
    require_true(provenance.get("public_factory_is_canonical_identity"),
                 "provenance.public_factory_is_canonical_identity")
    require_true(provenance.get("adapter_override_absent"),
                 "provenance.adapter_override_absent")
    routed = provenance.get("adapter_routed_keys")
    if not isinstance(routed, list) or PROGRAM_KEY in routed:
        raise OracleError(
            f"{PROGRAM_KEY} must be absent from the adapter table")
    corpus_keys = provenance.get("corpus_adapter_keys")
    if not isinstance(corpus_keys, list) or PROGRAM_KEY in corpus_keys:
        raise OracleError(
            f"{PROGRAM_KEY} must be absent from the adapter table")
    live_keys = live_corpus_adapter_keys()
    if set(corpus_keys) != live_keys:
        raise OracleError(
            "recorded corpus adapter keys disagree with the live "
            "check_corpus._ADAPTERS")
    if live_keys != CORPUS_ADAPTER_CENSUS_EXPECTED:
        raise OracleError(
            "the live check_corpus._ADAPTERS census changed; re-derive the "
            "eligibility claim before regenerating")
    adapter_source = provenance.get("corpus_adapter_source")
    if (not isinstance(adapter_source, dict)
            or adapter_source.get("relative_path_from_noisemaker_for_cpp")
            != CORPUS_ADAPTER_SOURCE
            or adapter_source.get("parsed_from_live_source") is not True):
        raise OracleError(
            "the adapter eligibility table must be read from the live source")
    metadata = provenance.get("metadata")
    if (not isinstance(metadata, dict) or metadata.get("id") != EFFECT_KEY
            or metadata.get("func") != "normalMap"
            or metadata.get("kind") != "filter"):
        raise OracleError("effect metadata drift")
    if metadata.get("params") != {}:
        raise OracleError(
            "filter/normalMap grew a param; `size` may no longer be the zero "
            "vec4 in production and the reachability claim must be re-derived")


def validate_table_contracts(oracle: dict[str, Any]) -> None:
    contracts = oracle["const_global_table_contracts"]
    expected = {"SOBEL_OFFSETS", "SOBEL_X_KERNEL", "SOBEL_Y_KERNEL",
                "transpose_identity"}
    if set(contracts) != expected:
        raise OracleError("const global table census drift")
    for name in ("SOBEL_X_KERNEL", "SOBEL_Y_KERNEL"):
        entry = contracts[name]
        if "Float32Array" in entry.get("javascript_declaration", ""):
            raise OracleError(f"{name}: numeric contract drift")
        if entry.get("native_element_type") != "double":
            raise OracleError(f"{name}: numeric contract drift")
        if "double" not in entry.get("numeric_contract", ""):
            raise OracleError(f"{name}: numeric contract drift")
        if entry.get("oracle_discriminable") is not False:
            raise OracleError(
                f"{name}: the double element type is NOT oracle-discriminable "
                "and must not be recorded as if it were")
        if entry.get("discriminating_mutant") is not None:
            raise OracleError(
                f"{name}: a discriminating mutant is recorded for a contract "
                "no pixel can distinguish")
    offsets = contracts["SOBEL_OFFSETS"]
    if offsets.get("native_element_type") != "glsl::IVec2":
        raise OracleError("SOBEL_OFFSETS: numeric contract drift")
    if offsets.get("oracle_discriminable") is not True:
        raise OracleError("SOBEL_OFFSETS: contract is recorded as not "
                          "discriminable")
    if "POOLED" not in offsets.get("element_materialization", ""):
        raise OracleError(
            "SOBEL_OFFSETS: the pooled element materialization is the "
            "operative fact and must be recorded")
    # Amendment 11's identity, re-derived rather than trusted.
    for row in range(3):
        for column in range(3):
            if SOBEL_X_KERNEL[3 * row + column] != SOBEL_Y_KERNEL[
                    3 * column + row]:
                raise OracleError(
                    "SOBEL_X_KERNEL is no longer the exact transpose of "
                    "SOBEL_Y_KERNEL")


def digest_of(record: dict[str, Any], label: str) -> tuple[str, str]:
    return (require_hex64(record.get("f32_sha256"), f"{label}.f32_sha256"),
            require_hex64(record.get("rgba8_sha256"), f"{label}.rgba8_sha256"))


def validate_mutant_rows(rows: object, expected_digests: dict[str, tuple[str, str]],
                         label: str) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) != len(CASE_NAMES):
        raise OracleError(f"{label}: mutant row census mismatch")
    seen: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise OracleError(f"{label}[{index}]: object required")
        name = row.get("case")
        if name != CASE_NAMES[index]:
            raise OracleError(f"{label}[{index}]: case identity mismatch")
        seen.append(name)
        f32_digest, rgba8_digest = digest_of(row, f"{label}[{index}]")
        expected_f32, expected_rgba8 = expected_digests[name]
        derived = (f32_digest != expected_f32) or (rgba8_digest != expected_rgba8)
        recorded = row.get("differs")
        if recorded is not derived:
            raise OracleError(
                f"{label}[{index}]: the row records differs={recorded} but its "
                f"mutant digests say otherwise")
        changed = require_count(row.get("changed_lane_count"),
                                f"{label}[{index}].changed_lane_count")
        if derived and changed == 0:
            raise OracleError(
                f"{label}[{index}]: a differing row records zero changed lanes")
        if not derived and changed != 0:
            raise OracleError(
                f"{label}[{index}]: an identical row records changed lanes")
        require_count(row.get("changed_rgba8_byte_count"),
                      f"{label}[{index}].changed_rgba8_byte_count")
    if len(set(seen)) != len(seen):
        raise OracleError(f"{label}: duplicate case row")
    return rows


def validate_mutant_identity(record: dict[str, Any], label: str) -> None:
    count = require_count(record.get("anchor_count"), f"{label}.anchor_count")
    if count < 1:
        raise OracleError(f"{label}: at least one anchor required")
    for field in ("anchor_sha256", "replacement_sha256"):
        digests = record.get(field)
        if not isinstance(digests, list) or len(digests) != count:
            raise OracleError(f"{label}.{field}: one digest per anchor required")
        for digest in digests:
            require_hex64(digest, f"{label}.{field}")
    occurrences = record.get("anchor_occurrences")
    if occurrences != [1] * count:
        raise OracleError(
            f"{label}: every mutation anchor must match exactly once")
    require_hex64(record.get("mutated_factory_sha256"),
                  f"{label}.mutated_factory_sha256")
    if record.get("mutated_factory_sha256") == FACTORY_SHA256:
        raise OracleError(f"{label}: the mutated factory equals the canonical one")


def validate_mutations(oracle: dict[str, Any],
                       expected_digests: dict[str, tuple[str, str]]) -> None:
    # Disjointness derived from the FROZEN table, so relaxing the table alone
    # cannot smuggle an overlap past the document-level check below.
    for left in range(len(MUTANTS)):
        for right in range(left + 1, len(MUTANTS)):
            overlap = {
                case for case, differs
                in MUTANT_DISCRIMINATION[MUTANTS[left]].items()
                if differs and MUTANT_DISCRIMINATION[MUTANTS[right]][case]}
            if overlap:
                raise OracleError(
                    f"{MUTANTS[left]} and {MUTANTS[right]} share witnesses "
                    f"({', '.join(sorted(overlap))}) in the frozen table")
    ledger = oracle["mutation_ledger"]
    if not isinstance(ledger, list) or len(ledger) != len(MUTANTS):
        raise OracleError("mutant census mismatch")
    witness_sets: dict[str, set[str]] = {}
    for index, mutant in enumerate(ledger):
        name = mutant.get("name")
        if name != MUTANTS[index]:
            raise OracleError(f"mutation_ledger[{index}]: mutant census mismatch")
        validate_mutant_identity(mutant, f"mutation_ledger[{index}]")
        require_text(mutant.get("target"), f"{name}.target")
        require_text(mutant.get("contract"), f"{name}.contract")
        rows = validate_mutant_rows(mutant.get("results"), expected_digests, name)
        frozen = MUTANT_DISCRIMINATION[name]
        for row in rows:
            case = row["case"]
            if row.get("expected_discriminates") is not frozen[case]:
                raise OracleError(
                    f"{name}/{case}: the row carries the wrong per-case "
                    "expectation")
            if row["differs"] is not frozen[case]:
                raise OracleError(
                    f"{name}/{case}: the frozen table says "
                    f"{frozen[case]} but the ledger records {row['differs']}")
        witnesses = [row["case"] for row in rows if row["differs"]]
        controls = [row["case"] for row in rows if not row["differs"]]
        if (mutant.get("witness_cases") != witnesses
                or mutant.get("control_cases") != controls):
            raise OracleError(f"{name}: witness/control partition drift")
        if not witnesses:
            raise OracleError(f"{name}: no case discriminates this mutant")
        witness_sets[name] = set(witnesses)
    for left in range(len(MUTANTS)):
        for right in range(left + 1, len(MUTANTS)):
            shared = witness_sets[MUTANTS[left]] & witness_sets[MUTANTS[right]]
            if shared:
                raise OracleError(
                    f"{MUTANTS[left]} and {MUTANTS[right]} share witnesses "
                    f"({', '.join(sorted(shared))}); a divergence would not be "
                    "attributable to one contract")
    contract = oracle["mutation_discrimination_contract"]
    if contract.get("per_case") is not True:
        raise OracleError("the per-case discrimination contract must be stated")
    requirement = contract.get("disjoint_witness_requirement")
    if not isinstance(requirement, str) or "DISJOINT" not in requirement:
        raise OracleError(
            "the disjoint witness requirement must be stated, not merely "
            "enforced")
    require_text(contract.get("disjointness_construction"),
                 "mutation_discrimination_contract.disjointness_construction")
    if contract.get("expected") != MUTANT_DISCRIMINATION:
        raise OracleError(
            "the recorded per-case expectation does not match the frozen table")
    sets = contract.get("witness_sets")
    if not isinstance(sets, dict) or set(sets) != set(MUTANTS):
        raise OracleError("witness set census drift")
    for name in MUTANTS:
        if set(sets[name].get("witness_cases", [])) != witness_sets[name]:
            raise OracleError(
                f"{name}: the recorded witness set disagrees with the frozen "
                "per-case table")
    excluded = contract.get("excluded_from_ledger")
    if not isinstance(excluded, dict) or len(excluded) < 5:
        raise OracleError(
            "every mutant considered and rejected must be recorded with its "
            "reason")


def validate_controls(oracle: dict[str, Any],
                      by_name: dict[str, Any]) -> dict[str, Any]:
    group = oracle["control_group"]
    if group.get("anchor") != ANCHOR_CASE:
        raise OracleError("control group anchor drift")
    anchor = by_name[ANCHOR_CASE]["output_expected"]
    baseline = group.get("baseline")
    if (not isinstance(baseline, dict)
            or baseline.get("f32_sha256") != anchor["f32_sha256"]
            or baseline.get("rgba8_sha256") != anchor["rgba8_sha256"]):
        raise OracleError("control baseline digests disagree with the anchor case")
    controls = group.get("controls")
    if not isinstance(controls, list) or len(controls) != len(CONTROLS):
        raise OracleError("control census mismatch")
    width = by_name[ANCHOR_CASE]["width"]
    height = by_name[ANCHOR_CASE]["height"]
    for index, (control, (name, expectation)) in enumerate(
            zip(controls, CONTROLS)):
        if control.get("name") != name:
            raise OracleError(f"control_group.controls[{index}]: census drift")
        if control.get("expectation") != expectation:
            raise OracleError(f"control {name}: frozen expectation drift")
        surface = validate_surface(
            control.get("output"), width, height,
            f"control_group.{name}.output")
        derived = "identical" if (
            surface["f32_words_le"] == anchor["f32_words_le"]
            and surface["rgba8_bytes"] == anchor["rgba8_bytes"]) else "differs"
        if control.get("observed") != derived:
            raise OracleError(
                f"control {name}: recorded observation "
                f"{control.get('observed')!r} disagrees with the stored arrays")
        if control.get("pass") is not (derived == expectation):
            raise OracleError(
                f"control {name}: pass ledger disagrees with observation")
        if control.get("pass") is not True:
            raise OracleError(f"control {name}: control did not pass")
        changed = require_count(control.get("changed_lane_count"),
                                f"control {name}.changed_lane_count")
        if (derived == "identical") != (changed == 0):
            raise OracleError(
                f"control {name}: changed lane count disagrees with the "
                "observation")
        validate_external(control.get("external_pass"),
                          f"control_group.{name}.external_pass")
        require_text(control.get("note"), f"control_group.{name}.note")
    return group


def validate_inertness(oracle: dict[str, Any],
                       by_name: dict[str, Any]) -> None:
    census = oracle["binding_inertness_census"]
    if census.get("probe_case") != ANCHOR_CASE:
        raise OracleError("inertness probe case drift")
    anchor_digest = by_name[ANCHOR_CASE]["output_expected"]["f32_sha256"]
    entries = census.get("inert")
    if not isinstance(entries, list) or len(entries) != len(INERT_BINDINGS):
        raise OracleError("inert binding census mismatch")
    for entry, name in zip(entries, INERT_BINDINGS):
        if entry.get("binding") != name or entry.get("abi") != BINDING_ABI[name]:
            raise OracleError(f"inert binding {name}: census drift")
        if entry.get("live") is not False:
            raise OracleError(f"inert binding {name}: recorded live")
        probes = entry.get("probes")
        if not isinstance(probes, list) or len(probes) < 3:
            raise OracleError(
                f"inert binding {name}: at least three probes required")
        for probe in probes:
            if probe.get("differs_from_baseline") is not False:
                raise OracleError(
                    f"inert binding {name}: a probe changed the output")
            if probe.get("f32_sha256") != anchor_digest:
                raise OracleError(
                    f"inert binding {name}: an inert probe's digest differs "
                    "from the anchor's; the inertness claim is unsupported")
            if require_count(probe.get("changed_lane_count"),
                             f"inert {name}.changed_lane_count") != 0:
                raise OracleError(
                    f"inert binding {name}: a probe recorded changed lanes")
            require_word_array(probe.get("f32_words_le"),
                               VEC_LANES[BINDING_ABI[name]], f"inert {name}")
    if tuple(census.get("live") or ()) != LIVE_BINDINGS:
        raise OracleError("live binding census mismatch")
    reasons = census.get("reason")
    if not isinstance(reasons, dict) or set(reasons) != set(BINDING_NAMES):
        raise OracleError("inertness reason census mismatch")


def validate_transpose(oracle: dict[str, Any],
                       expected_digests: dict[str, tuple[str, str]]) -> None:
    proof = oracle["transpose_equivalence_proof"]
    if proof.get("retracted_mutant") != "normalmap-offsets-transposed":
        raise OracleError("transpose proof identity drift")
    if proof.get("retained_mutant") != MUTANTS[0]:
        raise OracleError("transpose proof retained-mutant drift")
    validate_mutant_identity(proof, "transpose_equivalence_proof")
    swap = {row["case"]: row for row in
            oracle["mutation_ledger"][0]["results"]}
    rows = proof.get("rows")
    if not isinstance(rows, list) or len(rows) != len(CASE_NAMES):
        raise OracleError("transpose proof row census mismatch")
    non_vacuous = False
    for row, name in zip(rows, CASE_NAMES):
        if row.get("case") != name:
            raise OracleError("transpose proof case identity mismatch")
        if row.get("identical_to_sobel_x_y_swapped") is not True:
            raise OracleError(
                f"{name}: normalmap-offsets-transposed is recorded as NOT "
                "identical to the retained mutant")
        f32_digest, rgba8_digest = digest_of(row, f"transpose proof {name}")
        if (f32_digest, rgba8_digest) != (swap[name]["f32_sha256"],
                                          swap[name]["rgba8_sha256"]):
            raise OracleError(
                f"{name}: the transposed-offsets digests differ from the "
                "swapped-kernel digests, so amendment 11's bit-identity claim "
                "is unsupported by this document")
        if row.get("changed_lane_count_against_swap") != 0:
            raise OracleError(
                f"{name}: the transpose proof records changed lanes against "
                "the retained mutant")
        derived = (f32_digest, rgba8_digest) != expected_digests[name]
        if row.get("differs_from_canonical") is not derived:
            raise OracleError(
                f"{name}: differs_from_canonical disagrees with the digests")
        non_vacuous = non_vacuous or derived
    if proof.get("non_vacuous") is not True or not non_vacuous:
        raise OracleError(
            "the transpose-equivalence proof is vacuous: neither mutant "
            "differs from canonical anywhere")
    require_text(proof.get("algebra"), "transpose_equivalence_proof.algebra")
    require_text(proof.get("consequence"),
                 "transpose_equivalence_proof.consequence")


def validate_kernel_census(oracle: dict[str, Any],
                           expected_digests: dict[str, tuple[str, str]],
                           ledger_witnesses: set[str]) -> None:
    census = oracle["kernel_table_mutant_census"]
    if census.get("in_disjoint_ledger") is not False:
        raise OracleError("the kernel census must not claim ledger membership")
    mutants = census.get("mutants")
    if not isinstance(mutants, list) or len(mutants) != len(
            KERNEL_CENSUS_MUTANTS):
        raise OracleError("kernel census mutant count mismatch")
    relations: set[str] = set()
    for mutant, name in zip(mutants, KERNEL_CENSUS_MUTANTS):
        if mutant.get("name") != name:
            raise OracleError("kernel census mutant identity drift")
        validate_mutant_identity(mutant, f"kernel census {name}")
        rows = validate_mutant_rows(mutant.get("results"), expected_digests,
                                    f"kernel census {name}")
        witnesses = [row["case"] for row in rows if row["differs"]]
        if mutant.get("witness_cases") != witnesses:
            raise OracleError(f"kernel census {name}: witness partition drift")
        if not witnesses:
            raise OracleError(f"kernel census {name}: cannot diverge anywhere")
        contains = ledger_witnesses.issubset(set(witnesses))
        if mutant.get("contains_retained_ledger_witnesses") is not contains:
            raise OracleError(
                f"kernel census {name}: the containment claim disagrees with "
                "the stored rows")
        if not contains:
            raise OracleError(
                f"kernel census {name}: the recorded reason for keeping it out "
                "of the disjoint ledger no longer holds")
        # The relation is NOT strict for every candidate: `sobel-x-negated`
        # witnesses exactly the retained mutant's cases. Calling that a strict
        # superset would understate it, so the relation is re-derived here.
        relation = ("identical" if len(witnesses) == len(ledger_witnesses)
                    else "strict-superset")
        if mutant.get("witness_relation") != relation:
            raise OracleError(
                f"kernel census {name}: witness_relation is recorded as "
                f"{mutant.get('witness_relation')!r} but the stored rows make "
                f"it {relation!r}")
        relations.add(relation)
        require_text(mutant.get("note"), f"kernel census {name}.note")
    if "identical" not in relations:
        raise OracleError(
            "no kernel-census mutant is witness-identical to the retained "
            "ledger mutant; the recorded relations must be re-derived rather "
            "than carried forward")


def validate_invariant_axis(record: dict[str, Any], label: str,
                            expected_digests: dict[str, tuple[str, str]]) -> int:
    mutant = record.get("rendered_mutant")
    if not isinstance(mutant, dict):
        raise OracleError(f"{label}: rendered mutant record required")
    validate_mutant_identity(mutant, f"{label}.rendered_mutant")
    rows = validate_mutant_rows(mutant.get("rows"), expected_digests, label)
    total = sum(row["changed_lane_count"] for row in rows)
    if any(row["differs"] for row in rows) or total != 0:
        raise OracleError(
            f"{label}: the axis is recorded invariant but a case diverged")
    if record.get("rendered_divergences") != total:
        raise OracleError(
            f"{label}: the recorded divergence total disagrees with the rows")
    return total


def validate_round_axis(oracle: dict[str, Any],
                        expected_digests: dict[str, tuple[str, str]]) -> None:
    axis = oracle["as_u32_round_axis"]
    if axis.get("status") != "unsatisfiable-control-proven-invariant":
        raise OracleError("as_u32 round axis status drift")
    sites = axis.get("call_sites")
    if not isinstance(sites, list) or len(sites) != axis.get("call_site_count"):
        raise OracleError("as_u32 call-site census mismatch")
    if len(sites) != 3:
        raise OracleError(
            "as_u32 has three call sites, not one; amendment 12 rests on that")
    scan = axis.get("scalar_scan")
    if not isinstance(scan, dict):
        raise OracleError("as_u32 scalar scan required")
    samples = require_count(scan.get("samples"), "as_u32 scan samples")
    disagreements = require_count(scan.get("rounder_disagreements"),
                                  "as_u32 scan rounder_disagreements")
    divergences = require_count(scan.get("as_u32_divergences"),
                                "as_u32 scan as_u32_divergences")
    if samples < 1000 or disagreements == 0:
        raise OracleError(
            "the as_u32 scan is vacuous: it found no rounder disagreement")
    if divergences != 0:
        raise OracleError(
            "the as_u32 scan found a divergence; amendment 12's clamp argument "
            "no longer holds")
    validate_invariant_axis(axis, "as_u32_round_axis", expected_digests)
    claim = require_text(axis.get("claim"), "as_u32_round_axis.claim")
    if "NOTHING WHATSOEVER" not in claim:
        raise OracleError(
            "the round-contract claim boundary must say out loud that this "
            "package proves nothing about it")
    require_text(axis.get("why_empty"), "as_u32_round_axis.why_empty")


def validate_narrowing_axis(oracle: dict[str, Any],
                            expected_digests: dict[str, tuple[str, str]]) -> None:
    axis = oracle["kernel_table_narrowing_axis"]
    if axis.get("status") != "cannot-diverge-do-not-ship":
        raise OracleError("kernel narrowing axis status drift")
    elements = axis.get("elements")
    if (not isinstance(elements, dict)
            or [float(value) for value in elements.get("SOBEL_X_KERNEL", [])]
            != list(SOBEL_X_KERNEL)
            or [float(value) for value in elements.get("SOBEL_Y_KERNEL", [])]
            != list(SOBEL_Y_KERNEL)):
        raise OracleError("kernel element census drift")
    if axis.get("element_count") != len(SOBEL_X_KERNEL) + len(SOBEL_Y_KERNEL):
        raise OracleError("kernel element count drift")
    if axis.get("inexact_elements") != []:
        raise OracleError("an inexact kernel element is recorded")
    for value in list(SOBEL_X_KERNEL) + list(SOBEL_Y_KERNEL):
        if not exactly_f32(value):
            raise OracleError(
                "a kernel element is not exactly f32-representable; design "
                "section 9 must be revisited")
    require_true(axis.get("every_element_exactly_f32_representable"),
                 "kernel_table_narrowing_axis")
    validate_invariant_axis(axis, "kernel_table_narrowing_axis", expected_digests)
    claim = require_text(axis.get("claim"), "kernel_table_narrowing_axis.claim")
    if "STRUCTURALLY" not in claim:
        raise OracleError(
            "the kernel double contract must be recorded as proven "
            "structurally, not numerically")


def validate_reevaluation(oracle: dict[str, Any],
                          expected_digests: dict[str, tuple[str, str]]) -> None:
    record = oracle["per_pixel_reevaluation_equivalence"]
    if record.get("status") != "measured-equivalent":
        raise OracleError("per-pixel re-evaluation status drift")
    validate_invariant_axis(record, "per_pixel_reevaluation_equivalence",
                            expected_digests)
    reason = require_text(record.get("operative_reason"),
                          "per_pixel_reevaluation_equivalence.operative_reason")
    if "MATERIALIZATION" not in reason.upper():
        raise OracleError(
            "amendment 15 makes element materialization the operative reason "
            "for per-pixel equivalence; it must be recorded as such")


def validate_pooled_hazard(oracle: dict[str, Any]) -> None:
    hazard = oracle["pooled_table_hazard"]
    if hazard.get("status") != "hazard-reproduced":
        raise OracleError("pooled table hazard status drift")
    validate_mutant_identity(hazard.get("probe") or {},
                             "pooled_table_hazard.probe")
    words = hazard.get("observed_f32_words_le")
    lanes = hazard.get("observed_lanes")
    if (not isinstance(words, list) or not words or len(words) % 4 != 0
            or not isinstance(lanes, list) or len(lanes) != len(words)):
        raise OracleError("pooled table hazard lane census mismatch")
    require_word_array(words, len(words), "pooled_table_hazard")
    for index, (word, lane) in enumerate(zip(words, lanes)):
        if word_to_float(word) != float(lane):
            raise OracleError(
                f"pooled_table_hazard: lane {index} disagrees with its word")
    float_survived = all(
        float(lanes[index]) == POOLED_PROBE_LANES[index % 4]
        for index in range(len(lanes)) if index % 4 < 2)
    int_survived = all(
        float(lanes[index]) == POOLED_PROBE_LANES[index % 4]
        for index in range(len(lanes)) if index % 4 >= 2)
    if hazard.get("pooled_float_table_survived") is not float_survived:
        raise OracleError(
            "pooled_table_hazard: the float-table verdict disagrees with the "
            "published lanes")
    if hazard.get("pooled_int_table_survived") is not int_survived:
        raise OracleError(
            "pooled_table_hazard: the int-table verdict disagrees with the "
            "published lanes")
    if float_survived:
        raise OracleError(
            "a factory-scope PooledFloat32Array table survived the render; "
            "amendment 15's hazard argument no longer holds")
    if not int_survived:
        raise OracleError(
            "the factory-scope pooled ivec2 table did not survive the render")
    allowlist = hazard.get("element_type_allowlist")
    if not isinstance(allowlist, list) or any(
            entry.startswith("vec") for entry in allowlist):
        raise OracleError(
            "the element-type allowlist must exclude every float-vector type")
    claim = require_text(hazard.get("claim"), "pooled_table_hazard.claim")
    if "allowlist" not in claim:
        raise OracleError(
            "the float-vector claim boundary must require an allowlist")


def validate_accumulator(oracle: dict[str, Any],
                         expected_digests: dict[str, tuple[str, str]],
                         ledger_witnesses: set[str]) -> None:
    census = oracle["accumulator_double_census"]
    if census.get("in_disjoint_ledger") is not False:
        raise OracleError("the accumulator census must not claim ledger membership")
    mutant = census.get("rendered_mutant")
    validate_mutant_identity(mutant or {},
                             "accumulator_double_census.rendered_mutant")
    rows = validate_mutant_rows(mutant.get("rows"), expected_digests,
                                "accumulator_double_census")
    witnesses = [row["case"] for row in rows if row["differs"]]
    if census.get("witness_cases") != witnesses:
        raise OracleError("accumulator census witness partition drift")
    if tuple(witnesses) != ACCUMULATOR_WITNESSES:
        raise OracleError(
            "accumulator census witness set drift; the double-accumulation "
            "claim rests on exactly the oklab cases")
    if not set(witnesses).issubset(ledger_witnesses):
        raise OracleError(
            "the accumulator census records an overlap claim that no longer "
            "holds")
    require_text(census.get("overlaps"), "accumulator_double_census.overlaps")
    require_text(census.get("reason"), "accumulator_double_census.reason")


def validate_value_map_arms(oracle: dict[str, Any]) -> None:
    census = oracle["value_map_arm_census"]
    if census.get("arms") != VALUE_MAP_ARMS:
        raise OracleError("value_map arm sweep census drift")
    sweeps = census.get("sweeps")
    if not isinstance(sweeps, list) or [sweep.get("input_pattern")
                                        for sweep in sweeps] != list(
                                            ARM_SWEEP_PATTERNS):
        raise OracleError("value_map arm sweep pattern census drift")
    digests: dict[tuple[str, int], str] = {}
    for sweep in sweeps:
        rows = sweep.get("rows")
        if not isinstance(rows, list) or [row.get("size_z") for row in rows
                                          ] != list(VALUE_MAP_ARMS):
            raise OracleError("value_map arm row census drift")
        for row in rows:
            expected_count = 1 if row["size_z"] <= 1 else row["size_z"]
            if row.get("resolved_channel_count") != expected_count:
                raise OracleError(
                    "value_map arm row records the wrong resolved channel "
                    "count")
            digests[(sweep["input_pattern"], row["size_z"])] = require_hex64(
                row.get("f32_sha256"), "value_map arm row")
        classes = sweep.get("equivalence_classes")
        derived: dict[str, list[int]] = {}
        for row in rows:
            derived.setdefault(row["f32_sha256"], []).append(row["size_z"])
        if classes != list(derived.values()):
            raise OracleError(
                "value_map arm equivalence classes disagree with the stored "
                "digests")
    for pattern in ARM_SWEEP_PATTERNS:
        for arm in (1, 2):
            if digests[(pattern, arm)] != digests[(pattern, 0)]:
                raise OracleError(
                    f"value_map arm {arm} is no longer byte-identical to the "
                    f"<= 1 arm on {pattern}; the channelCount-2 case would "
                    "then be covering a second value map")
        if digests[(pattern, 3)] == digests[(pattern, 0)]:
            raise OracleError(
                f"value_map arm 3 collapsed onto the texel.x arms on {pattern}")
        # Arm 4 pre-clamps an argument oklab_l_component clamps again, so it
        # must agree with arm 3 even on the out-of-range input.
        if digests[(pattern, 4)] != digests[(pattern, 3)]:
            raise OracleError(
                f"value_map arms 3 and 4 differ on {pattern}; the recorded "
                "redundant-clamp reason no longer holds")
    if census.get("measured_behaviour_count") != 2:
        raise OracleError(
            "value_map_component has five source arms and exactly two measured "
            "behaviours; the census must say so")
    require_text(census.get("rule"), "value_map_arm_census.rule")
    require_text(census.get("redundant_clamp"),
                 "value_map_arm_census.redundant_clamp")


def validate_fragcolor(oracle: dict[str, Any]) -> dict[str, Any]:
    witness = oracle["fragcolor_persistence_witness"]
    if witness.get("status") != "quarantined-not-a-parity-case":
        raise OracleError("fragColor persistence status drift")
    width = require_count(witness.get("width"), "fragcolor witness width")
    height = require_count(witness.get("height"), "fragcolor witness height")
    if width <= 0 or height <= 0:
        raise OracleError("fragcolor witness geometry required")
    validate_input_texture(witness.get("input_texture"), width, height,
                           "fragcolor_persistence_witness.input_texture")
    surface = validate_surface(witness.get("output_expected"), width, height,
                               "fragcolor_persistence_witness.output_expected")
    require_word_array(witness.get("size_binding_f32_words_le"), 4,
                       "fragcolor_persistence_witness.size")
    reset = witness.get("reset_mutant")
    validate_mutant_identity(reset or {},
                             "fragcolor_persistence_witness.reset_mutant")
    if reset.get("f32_sha256") == surface["f32_sha256"]:
        raise OracleError(
            "resetting fragColor per pixel produced the same image; the "
            "persistence witness is vacuous")
    if require_count(reset.get("changed_lane_count"),
                     "fragcolor reset changed_lane_count") == 0:
        raise OracleError("the fragColor persistence witness is vacuous")
    coverage = witness.get("full_coverage_control")
    if (not isinstance(coverage, dict)
            or coverage.get("differs_from_early_return_render") is not True
            or coverage.get("f32_sha256") == surface["f32_sha256"]):
        raise OracleError(
            "the full-coverage control does not differ; no pixel took the "
            "early return")
    if witness.get("native_expressible") is not False:
        raise OracleError(
            "the fragColor persistence configuration is recorded as natively "
            "expressible; if that became true it must move into the parity "
            "cases rather than stay quarantined")
    require_text(witness.get("native_reason"),
                 "fragcolor_persistence_witness.native_reason")
    require_text(witness.get("reachability"),
                 "fragcolor_persistence_witness.reachability")
    require_text(witness.get("why_not_a_ledger_mutant"),
                 "fragcolor_persistence_witness.why_not_a_ledger_mutant")
    return witness


def validate_claims(oracle: dict[str, Any]) -> None:
    claims = oracle["claim_boundaries"]
    expected = {"kernel_double_type", "round_contract",
                "per_pixel_reevaluation", "float_vector_tables",
                "production_reachability", "fragcolor_persistence",
                "normalized_source"}
    if set(claims) != expected:
        raise OracleError("claim boundary census drift")
    for name, text in claims.items():
        require_text(text, f"claim_boundaries.{name}")
    if "no params" not in claims["production_reachability"]:
        raise OracleError(
            "the production reachability boundary must record that "
            "filter/normalMap declares no params")


def load(paths: Paths = LIVE) -> tuple[dict[str, Any], str]:
    verify_sidecar(paths.generator)
    report_payload = verify_sidecar(paths.report)
    payload = verify_sidecar(paths.oracle)
    # Whole-document guard, not only the fields that are known to hold paths: a
    # machine-specific absolute path anywhere in a byte-compared gate makes the
    # gate unrunnable off the machine that produced it. The REPORT is
    # sidecar-verified and byte-compared exactly like the JSON, so a path
    # leaked into it alone would reproduce the same defect; both are scanned.
    for label, document in (("oracle", payload), ("report", report_payload)):
        leaked = ABSOLUTE_PATH.search(document.decode("utf-8", "replace"))
        if leaked is not None:
            raise OracleError(
                f"Normalmap185 {label} records an absolute filesystem path "
                f"({leaked.group(0)!r}); the gate must be path-independent")
    try:
        oracle = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OracleError(f"invalid Normalmap185 JSON: {error}") from error
    require_keys(oracle, TOP_LEVEL_KEYS, "oracle")
    if (oracle["schema"], oracle["schema_version"], oracle["program_key"],
            oracle["effect_key"], oracle["runtime_key"],
            oracle["corpus_revision"]) != (
                SCHEMA, SCHEMA_VERSION, PROGRAM_KEY, EFFECT_KEY, PROGRAM_KEY,
                CORPUS_REVISION):
        raise OracleError("Normalmap185 schema/program identity mismatch")
    if oracle["defines"] != {} or oracle["preprocessor_define_count"] != 0:
        raise OracleError(
            "Normalmap185 define mismatch: this program has no preprocessor "
            "defines")
    if tuple(oracle["runtime_binding_names"]) != BINDING_NAMES:
        raise OracleError("Normalmap185 runtime binding census mismatch")
    if oracle["runtime_binding_abi"] != BINDING_ABI:
        raise OracleError("Normalmap185 runtime binding ABI mismatch")
    validate_provenance(oracle, paths)
    validate_table_contracts(oracle)
    self_tests = oracle.get("comparer_self_tests")
    if not isinstance(self_tests, dict) or any(
            self_tests.get(name) is not True for name in REQUIRED_SELF_TESTS):
        raise OracleError("Normalmap185 comparer self-test mismatch")
    cases = oracle.get("render_cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise OracleError("Normalmap185 fixture count mismatch")
    names: list[str] = []
    for index, (case, expected) in enumerate(zip(cases, EXPECTED_CASES)):
        name, width, height, route, pattern, opaque = expected
        entry = require_keys(case, CASE_KEYS, f"render_cases[{index}]")
        if entry["name"] in names:
            raise OracleError(f"render_cases[{index}]: duplicate case name "
                              f"{entry['name']}")
        names.append(entry["name"])
        if (entry["name"] != name or entry["route"] != route
                or entry["input_pattern"] != pattern
                or entry["opaque_input"] is not opaque):
            raise OracleError(f"render_cases[{index}]: case identity mismatch")
        require_dimension(entry["width"], width, f"{name}.width")
        require_dimension(entry["height"], height, f"{name}.height")
        if not isinstance(entry["coverage"], list) or not entry["coverage"]:
            raise OracleError(f"{name}: coverage labels required")
        texture = validate_input_texture(entry["input_texture"], width, height,
                                         f"{name}.input_texture")
        validate_bindings(entry["bindings"], f"{name}.bindings",
                          texture["f32_sha256"], width, height)
        validate_external(entry["external_pass"], f"{name}.external_pass")
        validate_surface(entry["output_expected"], width, height,
                         f"{name}.output_expected", opaque)
        size_lanes = [word_to_float(word) for word
                      in entry["bindings"]["size"]["f32_words_le"]]
        production = all(lane == 0.0 for lane in size_lanes)
        if production is not (route == "production-binding-set"):
            raise OracleError(
                f"{name}: the route label disagrees with the size binding")
        validate_identity(entry["canonical_repeat"], f"{name}.canonical_repeat")
        validate_identity(entry["public_canonical"], f"{name}.public_canonical")
    by_name = {case["name"]: case for case in cases}
    expected_digests = {
        case["name"]: (case["output_expected"]["f32_sha256"],
                       case["output_expected"]["rgba8_sha256"])
        for case in cases}
    validate_controls(oracle, by_name)
    validate_inertness(oracle, by_name)
    validate_mutations(oracle, expected_digests)
    ledger_witnesses = set(oracle["mutation_ledger"][0]["witness_cases"])
    validate_transpose(oracle, expected_digests)
    validate_kernel_census(oracle, expected_digests, ledger_witnesses)
    validate_round_axis(oracle, expected_digests)
    validate_narrowing_axis(oracle, expected_digests)
    validate_reevaluation(oracle, expected_digests)
    validate_pooled_hazard(oracle)
    validate_accumulator(oracle, expected_digests, ledger_witnesses)
    validate_value_map_arms(oracle)
    validate_fragcolor(oracle)
    validate_claims(oracle)
    return oracle, sha256(payload)


def array_lines(values: list[str] | list[int], suffix: str,
                width: int) -> list[str]:
    rendered = [f"{value}{suffix}" for value in values]
    return ["    " + ", ".join(rendered[index:index + width]) + ","
            for index in range(0, len(rendered), width)]


def word_list(values: list[str]) -> str:
    return ", ".join(f"{value}U" for value in values)


def double_literal(value: float) -> str:
    text = repr(float(value))
    return text if ("." in text or "e" in text or "inf" in text) else f"{text}.0"


def render(paths: Paths = LIVE) -> bytes:
    oracle, oracle_hash = load(paths)
    cases = oracle["render_cases"]
    fragcolor = oracle["fragcolor_persistence_witness"]
    hazard = oracle["pooled_table_hazard"]
    round_axis = oracle["as_u32_round_axis"]
    narrowing = oracle["kernel_table_narrowing_axis"]
    reevaluation = oracle["per_pixel_reevaluation_equivalence"]
    accumulator = oracle["accumulator_double_census"]
    transpose = oracle["transpose_equivalence_proof"]
    lines = [
        "// Generated from the checked canonical JavaScript Normalmap185 oracle.",
        "// Do not edit; C++ output never participates in these expected arrays.",
        "//",
        "// filter/normalMap carries three CONST file-scope tables. The two",
        "// float[9] kernels are plain JS Arrays -- doubles, never narrowed --",
        "// and that half is NOT oracle-discriminable: every element is exactly",
        "// representable in binary32. Compare kSobelXKernel/kSobelYKernel",
        "// against the emitted std::array<double, 9> instead of expecting a",
        "// pixel test to prove it. SOBEL_OFFSETS holds pooled Int32Arrays; see",
        "// kPooledFloatTableSurvived for why the element type is an allowlist.",
        "#pragma once", "", "namespace normalmap185_oracle {", "",
        f'inline constexpr std::string_view kOracleSha256 = "{oracle_hash}";',
        f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";',
        f'inline constexpr std::string_view kCorpusRevision = "{CORPUS_REVISION}";',
        f"inline constexpr std::size_t kCaseCount = {len(cases)}U;",
        f"inline constexpr std::size_t kBindingCount = {len(BINDING_NAMES)}U;",
        "inline constexpr std::size_t kPreprocessorDefineCount = "
        f"{oracle['preprocessor_define_count']}U;",
        "",
        f"inline constexpr std::array<std::string_view, {len(BINDING_NAMES)}> "
        "kBindingNames{{",
        "    " + ", ".join(f'"{name}"' for name in BINDING_NAMES) + ",",
        "}};", "",
        "// The const tables as the JavaScript declares them. `double` is the",
        "// contract, and it is proven structurally rather than by any pixel.",
        f"inline constexpr std::array<double, {len(SOBEL_X_KERNEL)}> "
        "kSobelXKernel{{",
        "    " + ", ".join(double_literal(value) for value in SOBEL_X_KERNEL) + ",",
        "}};",
        f"inline constexpr std::array<double, {len(SOBEL_Y_KERNEL)}> "
        "kSobelYKernel{{",
        "    " + ", ".join(double_literal(value) for value in SOBEL_Y_KERNEL) + ",",
        "}};",
        f"inline constexpr std::array<std::array<std::int32_t, 2>, "
        f"{len(SOBEL_OFFSETS)}> kSobelOffsets{{{{",
        "    " + ", ".join(f"std::array<std::int32_t, 2>{{{x}, {y}}}"
                           for x, y in SOBEL_OFFSETS) + ",",
        "}};", "",
    ]
    for index, case in enumerate(cases):
        texture = case["input_texture"]
        surface = case["output_expected"]
        lines.append(
            f"inline constexpr std::array<std::uint32_t, "
            f"{len(texture['f32_words_le'])}> kCase{index}InputWords{{{{")
        lines.extend(array_lines(texture["f32_words_le"], "U", 8))
        lines.extend(["}};", ""])
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
    lines.extend([
        "struct CaseView {",
        "  std::string_view name;",
        "  std::size_t width;",
        "  std::size_t height;",
        "  std::string_view route;",
        "  std::string_view input_pattern;",
        "  bool opaque_input;",
        "  std::span<const std::uint32_t> input_words;",
        "  std::span<const std::uint32_t> expected_words;",
        "  std::span<const std::uint8_t> expected_rgba8;",
        "  std::array<std::uint32_t, 2> tile_offset_words;",
        "  std::array<std::uint32_t, 2> full_resolution_words;",
        "  std::array<std::uint32_t, 4> size_words;",
        "  std::array<std::uint32_t, 4> motion_words;",
        "  std::uint32_t external_time_word;",
        "  std::uint32_t external_seed_word;",
        "  std::size_t distinct_alpha_word_count;",
        "};", "",
        "// The two ledger mutants must have disjoint witness sets: a case that",
        "// witnessed both could not attribute a divergence to one contract.",
        "struct MutantSetView {",
        "  std::string_view mutant;",
        "  std::span<const std::string_view> witness_cases;",
        "  std::span<const std::string_view> control_cases;",
        "};", "",
        "// One row per mutant per case: the frozen per-case discrimination",
        "// ledger. A per-mutant summary is deliberately not materialized.",
        "struct MutantWitnessView {",
        "  std::string_view mutant;",
        "  std::string_view oracle_case;",
        "  bool discriminates;",
        "  std::size_t changed_lane_count;",
        "};", "",
        "// Amendment 11: `normalmap-offsets-transposed` is bit-identical to",
        "// `normalmap-sobel-x-y-swapped` at every pixel, which is why only one",
        "// of design section 7's pair survives.",
        "struct TransposeRowView {",
        "  std::string_view oracle_case;",
        "  std::size_t lanes_against_retained_mutant;",
        "  std::size_t lanes_against_canonical;",
        "};", "",
        f"inline constexpr std::array<CaseView, {len(cases)}> kCases{{{{",
    ])
    for index, case in enumerate(cases):
        binding = case["bindings"]
        external = case["external_pass"]
        lines.append(
            f'  CaseView{{"{case["name"]}", {case["width"]}U, '
            f'{case["height"]}U, "{case["route"]}", '
            f'"{case["input_pattern"]}", '
            f'{str(case["opaque_input"]).lower()}, '
            f'kCase{index}InputWords, kCase{index}ExpectedWords, '
            f'kCase{index}ExpectedRgba8, '
            f'{{{word_list(binding["tileOffset"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["fullResolution"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["size"]["f32_words_le"])}}}, '
            f'{{{word_list(binding["motion"]["f32_words_le"])}}}, '
            f'{external["time"]["f32_word_le"]}U, '
            f'{external["seed"]["f32_word_le"]}U, '
            f'{case["output_expected"]["distinct_alpha_f32_word_count"]}U}},')
    ledger_rows = [(mutant["name"], result["case"], result["differs"],
                    result["changed_lane_count"])
                   for mutant in oracle["mutation_ledger"]
                   for result in mutant["results"]]
    lines.extend([
        "}};", "",
        f"inline constexpr std::array<MutantWitnessView, {len(ledger_rows)}> "
        "kMutantWitnesses{{",
    ])
    for mutant_name, case_name, differs, changed in ledger_rows:
        lines.append(f'  MutantWitnessView{{"{mutant_name}", "{case_name}", '
                     f'{str(differs).lower()}, {changed}U}},')
    lines.extend(["}};", ""])
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
    lines.extend(["}};", ""])
    lines.append(
        f"inline constexpr std::array<TransposeRowView, "
        f"{len(transpose['rows'])}> kTransposeEquivalence{{{{")
    for row in transpose["rows"]:
        lines.append(
            f'  TransposeRowView{{"{row["case"]}", '
            f'{row["changed_lane_count_against_swap"]}U, '
            f'{row["changed_lane_count_against_canonical"]}U}},')
    lines.extend(["}};", ""])
    accumulator_witnesses = accumulator["witness_cases"]
    lines.extend([
        "// Amendment 12: `as_u32` has three call sites and the round axis is",
        "// STRUCTURALLY unsatisfiable -- Math.round and round-half-away differ",
        "// only on negative half-integers and max(..., 0) collapses every one.",
        "// This oracle proves NOTHING about the round contract. The numbers",
        "// below are the invariance evidence, not a parity claim.",
        "inline constexpr std::size_t kAsU32CallSiteCount = "
        f"{round_axis['call_site_count']}U;",
        "inline constexpr std::size_t kAsU32ScanSamples = "
        f"{round_axis['scalar_scan']['samples']}U;",
        "inline constexpr std::size_t kAsU32RounderDisagreements = "
        f"{round_axis['scalar_scan']['rounder_disagreements']}U;",
        "inline constexpr std::size_t kAsU32Divergences = "
        f"{round_axis['scalar_scan']['as_u32_divergences']}U;",
        "inline constexpr std::size_t kRoundMutantChangedLanes = "
        f"{round_axis['rendered_divergences']}U;",
        "",
        "// Design section 9: an f32-narrowing mutant on the kernel tables",
        "// cannot diverge, so it is not shipped as a control.",
        "inline constexpr std::size_t kKernelElementCount = "
        f"{narrowing['element_count']}U;",
        "inline constexpr bool kKernelElementsExactlyF32Representable = "
        f"{str(narrowing['every_element_exactly_f32_representable']).lower()};",
        "inline constexpr std::size_t kKernelNarrowingChangedLanes = "
        f"{narrowing['rendered_divergences']}U;",
        "",
        "// Design 3.1 as amended by 15: re-evaluating all three tables per",
        "// pixel is MEASURED equivalent, which is what makes the emitter's",
        "// source_global_locals rewrite sound for this program.",
        "inline constexpr std::size_t kPerPixelReevaluationChangedLanes = "
        f"{reevaluation['rendered_divergences']}U;",
        "",
        "// Amendment 15, reproduced against the pinned runtime: a factory-scope",
        "// PooledFloat32Array table is clobbered by the first per-pixel scratch",
        "// allocation, while the pooled Int32Array table survives. Do NOT",
        "// extend the const-table mechanism to vec2[N]/vec3[N]/vec4[N].",
        "inline constexpr bool kPooledFloatTableSurvived = "
        f"{str(hazard['pooled_float_table_survived']).lower()};",
        "inline constexpr bool kPooledIntTableSurvived = "
        f"{str(hazard['pooled_int_table_survived']).lower()};",
        f"inline constexpr std::array<std::uint32_t, "
        f"{len(hazard['observed_f32_words_le'])}> kPooledProbeWords{{{{",
        "    " + word_list(hazard["observed_f32_words_le"]) + ",",
        "}};", "",
        "// Amendment 16: `dx += value * SOBEL_X_KERNEL[i]` accumulates in",
        "// double with no per-step F32. Unlike the element type, this half IS",
        "// discriminable, on exactly the cases whose value map leaves the",
        "// dyadic grid. It shares witnesses with the retained ledger mutant, so",
        "// it is evidence, not attribution.",
        f"inline constexpr std::array<std::string_view, "
        f"{len(accumulator_witnesses)}> kAccumulatorDoubleWitnesses{{{{",
        "    " + ", ".join(f'"{name}"' for name in accumulator_witnesses) + ",",
        "}};", "",
    ])
    lines.extend([
        "// fragColor is a factory-scope Float32Array that is NOT reset per",
        "// pixel, so a pixel taking main()'s early return writes the PREVIOUS",
        "// pixel's colour. src/pass_runner.cpp declares `glsl::Vec4 output;`",
        "// inside the per-pixel loop and the emitted pixel() assigns it only on",
        "// the path that reaches the end of main(), so the native side cannot",
        "// reproduce this array today. The configuration is UNREACHABLE through",
        "// the shipped binding set (filter/normalMap declares no params, so",
        "// `size` is the zero vec4). These arrays exist so the boundary is",
        "// visible and testable -- do not write a parity test against them",
        "// while kFragColorPersistenceNativelyExpressible is false.",
        "inline constexpr bool kFragColorPersistenceNativelyExpressible = "
        f"{str(fragcolor['native_expressible']).lower()};",
        f'inline constexpr std::string_view kFragColorPersistenceCase = '
        f'"{fragcolor["case"]}";',
        "inline constexpr std::size_t kFragColorPersistenceWidth = "
        f"{fragcolor['width']}U;",
        "inline constexpr std::size_t kFragColorPersistenceHeight = "
        f"{fragcolor['height']}U;",
        "inline constexpr std::array<std::uint32_t, 4> "
        "kFragColorPersistenceSizeWords{{",
        "    " + word_list(fragcolor["size_binding_f32_words_le"]) + ",",
        "}};",
        "inline constexpr std::size_t kFragColorPersistenceResetChangedLanes = "
        f"{fragcolor['reset_mutant']['changed_lane_count']}U;",
        f"inline constexpr std::array<std::uint32_t, "
        f"{len(fragcolor['input_texture']['f32_words_le'])}> "
        "kFragColorPersistenceInputWords{{",
    ])
    lines.extend(array_lines(fragcolor["input_texture"]["f32_words_le"], "U", 8))
    lines.extend(["}};", ""])
    lines.append(
        f"inline constexpr std::array<std::uint32_t, "
        f"{len(fragcolor['output_expected']['f32_words_le'])}> "
        "kFragColorPersistenceExpectedWords{{")
    lines.extend(array_lines(fragcolor["output_expected"]["f32_words_le"], "U", 8))
    lines.extend(["}};", ""])
    lines.append(
        f"inline constexpr std::array<std::uint8_t, "
        f"{len(fragcolor['output_expected']['rgba8_bytes'])}> "
        "kFragColorPersistenceExpectedRgba8{{")
    lines.extend(array_lines(fragcolor["output_expected"]["rgba8_bytes"], "U", 16))
    lines.extend(["}};", ""])
    lines.extend([
        f'inline constexpr std::uint32_t kOpaqueAlphaWord = {OPAQUE_ALPHA_WORD}U;',
        f"inline constexpr std::uint8_t kOpaqueAlphaByte = {OPAQUE_ALPHA_BYTE}U;",
        "",
        "}  // namespace normalmap185_oracle", "",
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
    for name in ("normalmap-oracles.json", "normalmap-oracle-report.md",
                 "normalmap_oracle_generator.mjs"):
        shutil.copy2(PACKAGE / name, package / name)
        shutil.copy2(PACKAGE / f"{name}.sha256", package / f"{name}.sha256")
    return Paths(package=package, tool=TOOL, output=destination / "out.inc")


def _rewrite(paths: Paths, oracle: dict[str, Any]) -> None:
    payload = f"{json.dumps(oracle, indent=2)}\n".encode("utf-8")
    paths.oracle.write_bytes(payload)
    paths.oracle.with_suffix(paths.oracle.suffix + ".sha256").write_text(
        sidecar_text(paths.oracle, payload), encoding="utf-8")


def _refresh_surface_digests(surface: dict[str, Any]) -> None:
    surface["f32_sha256"] = sha256(packed_words(surface["f32_words_le"]))
    surface["rgba8_sha256"] = sha256(bytes(surface["rgba8_bytes"]))


def _break_opaque_alpha_word(doc: dict[str, Any]) -> None:
    surface = doc["render_cases"][0]["output_expected"]
    surface["f32_words_le"][3] = "0x3f000000"
    surface["alpha_f32_words_le"] = sorted(
        {surface["f32_words_le"][index]
         for index in range(3, len(surface["f32_words_le"]), 4)})
    surface["distinct_alpha_f32_word_count"] = len(
        surface["alpha_f32_words_le"])
    _refresh_surface_digests(surface)


def _fabricate_control(doc: dict[str, Any]) -> None:
    control = doc["control_group"]["controls"][0]
    control["output"]["f32_words_le"][0] = "0x7f7fffff"
    _refresh_surface_digests(control["output"])


def _fabricate_inert_probe(doc: dict[str, Any]) -> None:
    doc["binding_inertness_census"]["inert"][0]["probes"][0]["f32_sha256"] = (
        "0" * 64)


def _forge_transpose_row(doc: dict[str, Any]) -> None:
    doc["transpose_equivalence_proof"]["rows"][0]["f32_sha256"] = "0" * 64


def _fabricate_mutant_digest(doc: dict[str, Any]) -> None:
    row = doc["mutation_ledger"][0]["results"][0]
    row["f32_sha256"] = doc["render_cases"][0]["output_expected"]["f32_sha256"]
    row["rgba8_sha256"] = doc["render_cases"][0]["output_expected"][
        "rgba8_sha256"]


def _collapse_round_scan(doc: dict[str, Any]) -> None:
    doc["as_u32_round_axis"]["scalar_scan"]["rounder_disagreements"] = 0


def _diverge_axis(section: str) -> Callable[[dict[str, Any]], None]:
    """Make an invariant axis internally consistent but no longer invariant."""

    def mutate(doc: dict[str, Any]) -> None:
        row = doc[section]["rendered_mutant"]["rows"][0]
        row["differs"] = True
        row["changed_lane_count"] = 4
        row["changed_rgba8_byte_count"] = 4
        row["f32_sha256"] = "3" * 64
        row["rgba8_sha256"] = "4" * 64
        doc[section]["rendered_divergences"] = 4

    return mutate


def _claim_pooled_float_survived(doc: dict[str, Any]) -> None:
    hazard = doc["pooled_table_hazard"]
    hazard["pooled_float_table_survived"] = True


def _truncate_pooled_probe(doc: dict[str, Any]) -> None:
    doc["pooled_table_hazard"]["observed_f32_words_le"].pop()


def _make_fragcolor_expressible(doc: dict[str, Any]) -> None:
    doc["fragcolor_persistence_witness"]["native_expressible"] = True


def _vacuous_fragcolor(doc: dict[str, Any]) -> None:
    witness = doc["fragcolor_persistence_witness"]
    witness["reset_mutant"]["f32_sha256"] = witness["output_expected"][
        "f32_sha256"]


def _overlap_ledger_witnesses(doc: dict[str, Any]) -> None:
    # Make the alpha mutant witness the anchor case too, keeping the document
    # internally consistent apart from the disjointness requirement.
    ledger = doc["mutation_ledger"][1]
    row = ledger["results"][0]
    row["differs"] = True
    row["expected_discriminates"] = True
    row["changed_lane_count"] = 4
    row["f32_sha256"] = "1" * 64
    row["rgba8_sha256"] = "2" * 64
    ledger["witness_cases"] = [
        result["case"] for result in ledger["results"] if result["differs"]]
    ledger["control_cases"] = [
        result["case"] for result in ledger["results"] if not result["differs"]]
    doc["mutation_discrimination_contract"]["expected"][
        "normalmap-alpha-source-transposed"][ANCHOR_CASE] = True
    doc["mutation_discrimination_contract"]["witness_sets"][
        "normalmap-alpha-source-transposed"]["witness_cases"] = ledger[
            "witness_cases"]


def _drop_kernel_containment_claim(doc: dict[str, Any]) -> None:
    doc["kernel_table_mutant_census"]["mutants"][0][
        "contains_retained_ledger_witnesses"] = False


def _overstate_kernel_relation(doc: dict[str, Any]) -> None:
    """Call the witness-identical mutant a strict superset."""
    for mutant in doc["kernel_table_mutant_census"]["mutants"]:
        if mutant["witness_relation"] == "identical":
            mutant["witness_relation"] = "strict-superset"
            return
    raise OracleError("no witness-identical kernel-census mutant to overstate")


def _split_value_map_arm_two(doc: dict[str, Any]) -> None:
    sweep = doc["value_map_arm_census"]["sweeps"][0]
    row = next(item for item in sweep["rows"] if item["size_z"] == 2)
    row["f32_sha256"] = "5" * 64
    derived: dict[str, list[int]] = {}
    for item in sweep["rows"]:
        derived.setdefault(item["f32_sha256"], []).append(item["size_z"])
    sweep["equivalence_classes"] = list(derived.values())


def _split_clamped_value_map_arms(doc: dict[str, Any]) -> None:
    sweep = next(item for item in doc["value_map_arm_census"]["sweeps"]
                 if item["input_pattern"] == "wide")
    four = next(item for item in sweep["rows"] if item["size_z"] == 4)
    four["f32_sha256"] = "6" * 64
    derived: dict[str, list[int]] = {}
    for item in sweep["rows"]:
        derived.setdefault(item["f32_sha256"], []).append(item["size_z"])
    sweep["equivalence_classes"] = list(derived.values())


def _flip_accumulator_witness(doc: dict[str, Any]) -> None:
    census = doc["accumulator_double_census"]
    census["witness_cases"] = [ANCHOR_CASE]


def self_test() -> int:
    base, _ = load(LIVE)
    scenarios: tuple[tuple[str, Callable[[dict[str, Any]], None], str], ...] = (
        ("missing-top-level-field",
         lambda doc: doc.pop("pooled_table_hazard"),
         "missing field(s) pooled_table_hazard"),
        ("extra-top-level-field",
         lambda doc: doc.__setitem__("bonus", 1), "unexpected field(s) bonus"),
        ("missing-case-field",
         lambda doc: doc["render_cases"][0].pop("input_texture"),
         "missing field(s) input_texture"),
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
        ("malformed-hex-word",
         lambda doc: doc["render_cases"][0]["output_expected"]["f32_words_le"]
         .__setitem__(0, "0xZZZZZZZZ"), "malformed Float32 word at 0"),
        ("malformed-byte-value",
         lambda doc: doc["render_cases"][0]["output_expected"]["rgba8_bytes"]
         .__setitem__(0, 256), "malformed RGBA8 byte at 0"),
        ("truncated-word-array",
         lambda doc: doc["render_cases"][0]["output_expected"]["f32_words_le"]
         .pop(), "Float32 words, found"),
        ("truncated-byte-array",
         lambda doc: doc["render_cases"][0]["output_expected"]["rgba8_bytes"]
         .pop(), "RGBA8 bytes, found"),
        ("truncated-input-texture",
         lambda doc: doc["render_cases"][0]["input_texture"]["f32_words_le"]
         .pop(), "Float32 words, found"),
        ("wrong-float-digest",
         lambda doc: doc["render_cases"][0]["output_expected"].__setitem__(
             "f32_sha256", "0" * 64), "Float32 digest mismatch"),
        ("wrong-input-digest",
         lambda doc: doc["render_cases"][0]["input_texture"].__setitem__(
             "f32_sha256", "0" * 64),
         "input texture Float32 digest mismatch"),
        ("sampler-digest-disagreement",
         lambda doc: doc["render_cases"][0]["bindings"]["inputTex"]
         .__setitem__("f32_sha256", "0" * 64),
         "sampler digest disagrees with the stored input texture"),
        ("binding-word-value-disagreement",
         lambda doc: doc["render_cases"][0]["bindings"]["size"].__setitem__(
             "f32_values", [1.0, 0.0, 0.0, 0.0]),
         "f32 word disagrees with its value"),
        ("route-label-drift",
         lambda doc: doc["render_cases"][0].__setitem__(
             "route", "synthetic-size"), "case identity mismatch"),
        ("opaque-alpha-drift", _break_opaque_alpha_word,
         "must carry a uniform"),
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
         lambda doc: doc["provenance"]["adapter_routed_keys"].append(
             PROGRAM_KEY), "must be absent from the adapter table"),
        ("wrong-pinned-cpu-digest",
         lambda doc: doc["provenance"]["cpu_snapshot"]["pinned_files"]
         ["glsl_runtime"].__setitem__("sha256", "0" * 64),
         "pinned CPU file glsl_runtime mismatch"),
        ("recorded-absolute-path",
         lambda doc: doc["provenance"]["cpu_snapshot"].__setitem__(
             "argument", "/private/tmp/normalmap-run/oracle/noisemaker-for-cpu"),
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
        ("effect-grew-a-param",
         lambda doc: doc["provenance"]["metadata"].__setitem__(
             "params", {"strength": {}}),
         "filter/normalMap grew a param"),
        ("wrong-source-digest",
         lambda doc: doc["provenance"]["source"].__setitem__(
             "sha256", "0" * 64), "pinned GLSL source mismatch"),
        ("define-drift",
         lambda doc: doc.__setitem__("preprocessor_define_count", 1),
         "define mismatch"),
        ("binding-census-drift",
         lambda doc: doc["runtime_binding_names"].append("palette"),
         "runtime binding census mismatch"),
        ("kernel-contract-drift",
         lambda doc: doc["const_global_table_contracts"]["SOBEL_X_KERNEL"]
         .__setitem__("native_element_type", "float"),
         "numeric contract drift"),
        ("kernel-contract-claimed-discriminable",
         lambda doc: doc["const_global_table_contracts"]["SOBEL_X_KERNEL"]
         .__setitem__("oracle_discriminable", True),
         "NOT oracle-discriminable"),
        ("offsets-pooling-unrecorded",
         lambda doc: doc["const_global_table_contracts"]["SOBEL_OFFSETS"]
         .__setitem__("element_materialization", "nine ivec2 objects"),
         "pooled element materialization is the operative fact"),
        ("fabricated-control", _fabricate_control,
         "disagrees with the stored arrays"),
        ("control-expectation-drift",
         lambda doc: doc["control_group"]["controls"][5].__setitem__(
             "expectation", "identical"), "frozen expectation drift"),
        ("baseline-digest-drift",
         lambda doc: doc["control_group"]["baseline"].__setitem__(
             "f32_sha256", "0" * 64),
         "digests disagree with the anchor case"),
        ("fabricated-inert-probe", _fabricate_inert_probe,
         "an inert probe's digest differs from the anchor's"),
        ("inert-binding-recorded-live",
         lambda doc: doc["binding_inertness_census"]["inert"][0].__setitem__(
             "live", True), "recorded live"),
        ("forged-transpose-row", _forge_transpose_row,
         "the transposed-offsets digests differ from the swapped-kernel "
         "digests"),
        ("transpose-not-identical",
         lambda doc: doc["transpose_equivalence_proof"]["rows"][0].__setitem__(
             "identical_to_sobel_x_y_swapped", False),
         "recorded as NOT identical to the retained mutant"),
        ("kernel-census-in-ledger",
         lambda doc: doc["kernel_table_mutant_census"].__setitem__(
             "in_disjoint_ledger", True),
         "must not claim ledger membership"),
        ("kernel-census-containment-claim-dropped",
         _drop_kernel_containment_claim,
         "the containment claim disagrees with the stored rows"),
        ("kernel-census-relation-overstated", _overstate_kernel_relation,
         "witness_relation is recorded as"),
        ("value-map-arm-two-split", _split_value_map_arm_two,
         "no longer byte-identical to the <= 1 arm"),
        ("value-map-clamped-arms-split", _split_clamped_value_map_arms,
         "the recorded redundant-clamp reason no longer holds"),
        ("value-map-behaviour-count-drift",
         lambda doc: doc["value_map_arm_census"].__setitem__(
             "measured_behaviour_count", 5),
         "exactly two measured behaviours"),
        ("value-map-arm-census-drift",
         lambda doc: doc["value_map_arm_census"]["sweeps"][0]["rows"].pop(),
         "value_map arm row census drift"),
        ("round-scan-vacuous", _collapse_round_scan,
         "the as_u32 scan is vacuous"),
        ("round-scan-divergence",
         lambda doc: doc["as_u32_round_axis"]["scalar_scan"].__setitem__(
             "as_u32_divergences", 1),
         "amendment 12's clamp argument no longer holds"),
        ("round-axis-diverged", _diverge_axis("as_u32_round_axis"),
         "recorded invariant but a case diverged"),
        ("round-claim-softened",
         lambda doc: doc["as_u32_round_axis"].__setitem__(
             "claim", "the round contract is partially covered"),
         "must say out loud that this package proves nothing about it"),
        ("as-u32-call-site-count",
         lambda doc: doc["as_u32_round_axis"]["call_sites"].pop(),
         "call-site census mismatch"),
        ("narrowing-axis-diverged",
         _diverge_axis("kernel_table_narrowing_axis"),
         "recorded invariant but a case diverged"),
        ("narrowing-claim-softened",
         lambda doc: doc["kernel_table_narrowing_axis"].__setitem__(
             "claim", "the double contract is proven by these renders"),
         "must be recorded as proven structurally"),
        ("reevaluation-diverged",
         _diverge_axis("per_pixel_reevaluation_equivalence"),
         "recorded invariant but a case diverged"),
        ("reevaluation-reason-drift",
         lambda doc: doc["per_pixel_reevaluation_equivalence"].__setitem__(
             "operative_reason", "the initializers are literals"),
         "element materialization the operative reason"),
        ("pooled-float-claimed-surviving", _claim_pooled_float_survived,
         "the float-table verdict disagrees with the published lanes"),
        ("pooled-probe-truncated", _truncate_pooled_probe,
         "lane census mismatch"),
        ("pooled-allowlist-admits-vec2",
         lambda doc: doc["pooled_table_hazard"]["element_type_allowlist"]
         .append("vec2"),
         "must exclude every float-vector type"),
        ("accumulator-in-ledger",
         lambda doc: doc["accumulator_double_census"].__setitem__(
             "in_disjoint_ledger", True),
         "must not claim ledger membership"),
        ("accumulator-witness-drift", _flip_accumulator_witness,
         "witness partition drift"),
        ("fragcolor-claimed-expressible", _make_fragcolor_expressible,
         "recorded as natively expressible"),
        ("fragcolor-vacuous", _vacuous_fragcolor,
         "produced the same image"),
        ("fragcolor-coverage-control-identical",
         lambda doc: doc["fragcolor_persistence_witness"]
         ["full_coverage_control"].__setitem__(
             "differs_from_early_return_render", False),
         "no pixel took the early return"),
        ("mutant-census-drift",
         lambda doc: doc["mutation_ledger"].pop(), "mutant census mismatch"),
        ("mutant-per-case-table-drift",
         lambda doc: doc["mutation_discrimination_contract"]["expected"]
         ["normalmap-alpha-source-transposed"].__setitem__(ANCHOR_CASE, True),
         "does not match the frozen table"),
        ("mutant-row-expectation-drift",
         lambda doc: doc["mutation_ledger"][0]["results"][7].__setitem__(
             "expected_discriminates", True),
         "carries the wrong per-case expectation"),
        ("fabricated-mutant-digest", _fabricate_mutant_digest,
         "but its mutant digests say otherwise"),
        ("mutant-partition-drift",
         lambda doc: doc["mutation_ledger"][0]["witness_cases"].append("bogus"),
         "witness/control partition drift"),
        ("mutant-anchor-matched-twice",
         lambda doc: doc["mutation_ledger"][0].__setitem__(
             "anchor_occurrences", [2]),
         "must match exactly once"),
        # The frozen per-case table is the first line of defence against an
        # overlap, so a document that fabricates one is rejected there before
        # the set-level disjointness check sees it. The set-level check guards
        # the other direction: a future edit to MUTANT_DISCRIMINATION itself.
        ("overlapping-ledger-witnesses", _overlap_ledger_witnesses,
         "carries the wrong per-case expectation"),
        ("disjoint-requirement-unstated",
         lambda doc: doc["mutation_discrimination_contract"].__setitem__(
             "disjoint_witness_requirement",
             "the sets happen not to overlap"),
         "must be stated, not merely enforced"),
        ("excluded-mutants-unrecorded",
         lambda doc: doc["mutation_discrimination_contract"].__setitem__(
             "excluded_from_ledger", {"one": "reason"}),
         "must be recorded with its reason"),
        ("claim-boundary-census-drift",
         lambda doc: doc["claim_boundaries"].pop("round_contract"),
         "claim boundary census drift"),
        ("reachability-claim-softened",
         lambda doc: doc["claim_boundaries"].__setitem__(
             "production_reachability", "the synthetic cases are fine"),
         "must record that filter/normalMap declares no params"),
        ("self-test-ledger-drift",
         lambda doc: doc["comparer_self_tests"].__setitem__(
             "signed_zero_rejected_with_equal_rgba8", False),
         "comparer self-test mismatch"),
    )
    passed = 0
    with tempfile.TemporaryDirectory(prefix="normalmap185-selftest-") as raw:
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
        leaked_report = _stage(root / "leaked-report")
        leaked = leaked_report.report.read_bytes() + (
            b"\nsnapshot: /Users/someone/platform/noisemaker-for-cpu\n")
        leaked_report.report.write_bytes(leaked)
        leaked_report.report.with_suffix(
            leaked_report.report.suffix + ".sha256").write_text(
                sidecar_text(leaked_report.report, leaked), encoding="utf-8")
        _expect_rejection(leaked_report,
                          "Normalmap185 report records an absolute filesystem "
                          "path", "absolute-path-in-report")
        passed += 1
        broken_json = _stage(root / "broken-json")
        payload = b"{ this is not json"
        broken_json.oracle.write_bytes(payload)
        broken_json.oracle.with_suffix(
            broken_json.oracle.suffix + ".sha256").write_text(
                sidecar_text(broken_json.oracle, payload), encoding="utf-8")
        _expect_rejection(broken_json, "invalid Normalmap185 JSON", "broken-json")
        passed += 1
    print("Normalmap185 native oracle materializer self-test ok "
          f"({passed} checks)")
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
                    "generated Normalmap185 native include is stale")
    except (OSError, OracleError) as error:
        print(f"glslcpp: {error}", file=sys.stderr)
        return 1
    oracle, _ = load(LIVE)
    words = sum(len(case["output_expected"]["f32_words_le"])
                for case in oracle["render_cases"])
    inputs = sum(len(case["input_texture"]["f32_words_le"])
                 for case in oracle["render_cases"])
    witnesses = {mutant["name"]: len(mutant["witness_cases"])
                 for mutant in oracle["mutation_ledger"]}
    print("Normalmap185 native oracle include ok "
          f"({len(EXPECTED_CASES)} cases, {inputs} input words, {words} "
          f"expected words, {words} bytes, {len(MUTANTS)} disjoint mutants, "
          "per-case witnesses "
          + ", ".join(f"{name}={count}" for name, count in witnesses.items())
          + ")")
    if oracle["fragcolor_persistence_witness"]["native_expressible"] is not True:
        print("glslcpp: NOTICE the fragColor cross-pixel persistence witness is "
              "quarantined: src/pass_runner.cpp declares `glsl::Vec4 output;` "
              "per pixel and the emitted pixel() leaves it unassigned on "
              "main()'s early return, so the native side cannot reproduce it. "
              "The configuration is unreachable through the shipped binding "
              "set; see fragcolor_persistence_witness", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
