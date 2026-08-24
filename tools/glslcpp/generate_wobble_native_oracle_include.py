#!/usr/bin/env python3
"""Generate the checked native Wobble fixture from the canonical JS JSON.

This is the sole JSON-to-C++ materializer for `filter/wobble:wobble` (typed
row 189, the first varying-admission program). It never renders anything:
every expected word and byte originates in
`docs/port-engineering/varying-parity/wobble-oracles.json`, which is produced
by the canonical JavaScript oracle generator against an immutable
`noisemaker-for-cpu` snapshot. The materializer is fail-closed and rejects
missing or extra fields, duplicate case names, malformed dimensions, counts,
hex words or byte values, wrong digests, wrong or missing sidecars, and
truncated or extra arrays. `--self-test` proves each rejection.

Nothing recorded as prose is trusted. Every observation the document reports
-- the measured tile-translation non-identity on BOTH arms with its
sampleCoord probe witnesses, per-case mutant discrimination, the control
group, the binding liveness / range-zero / defaults / wrap-arm censuses, and
the alpha contract -- is RE-DERIVED here from the stored arrays and digests,
so a hand-edited verdict with refreshed hashes cannot survive.
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
PACKAGE = ROOT / "docs/port-engineering/varying-parity"
OUTPUT = ROOT / "tests/oracles/wobble_expected.inc"
TOOL = pathlib.Path(__file__).resolve()

SCHEMA = "noisemaker-for-cpp.wobble189.pixel-parity.v1"
SCHEMA_VERSION = 1
PROGRAM_KEY = "filter/wobble:wobble"
EFFECT_KEY = "filter/wobble"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
UPSTREAM_REVISION = "117a236679d1db3ab8f0e278230ece277b57564c"
DEFINES: dict[str, int] = {}
FACTORY_NAME = "canonicalFactory178"
FACTORY_SHA256 = "e09f2ef4c49b33b06febfac20d4eeea3563270f6edab6cb1f6761f2dd20759d4"
CROSS_VALIDATION_FACTORY_KEY = "classicNoisedeck/cellRefract:cellRefract"
CROSS_VALIDATION_FACTORY_SHA256 = (
    "329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3")
SOURCE_RELATIVE = (
    f"tools/glslcpp/corpus/{CORPUS_REVISION}"
    "/sources/filter/wobble/wobble.glsl")
SOURCE_BYTES = 3105
SOURCE_SHA256 = "1bdd1e3bed9111743dfeb7e3418e14c42aa8d93ed4636167a99d17cb143a38cc"
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
# if `filter/wobble` were ever added to the real table.
CORPUS_ADAPTER_SOURCE = "tools/glslcpp/check_corpus.py"
CORPUS_ADAPTER_CENSUS_EXPECTED = frozenset({
    "classicNoisedeck/fractal:fractal",
    "filter/historicPalette:historicPalette",
    "filter/palette:palette",
    "synth/julia:julia",
})
CANONICAL_ADAPTER_KEYS = (
    "classicNoisedeck/bitEffects:bitEffects",
    "classicNoisedeck/fractal:fractal",
    "filter/crt:crt",
    "filter/historicPalette:historicPalette",
    "filter/median:median",
    "filter/palette:palette",
    "filter/pixelSort:luminance",
    "filter/reindex:nmReindexApply",
    "filter/reindex:nmReindexStats",
    "filter/snow:snow",
    "synth/julia:julia",
)


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

BINDING_NAMES = ("inputTex", "time", "speed", "range", "wrap")
BINDING_ABI = {
    "inputTex": "sampler2D", "time": "number", "speed": "number",
    "range": "number", "wrap": "number",
}
LIVE_BINDINGS = ("inputTex", "time", "speed", "range", "wrap")

# The varying materialization contract, frozen as the exact shipped strings.
VARYING_NAME = "v_texCoord"
VARYING_GLSL_DECLARATION = "in vec2 v_texCoord;"
VARYING_JS_SLOT = "var v_texCoord = new Float32Array([0, 0]);"
VARYING_JS_COPY = 'v_texCoord.set($runtime.varyings["v_texCoord"])'
VARYING_READ_EXPRESSION = "v_texCoord[0] + offset[0], v_texCoord[1] + offset[1]"
VARYING_OCCURRENCES = 5
VARYING_RUNTIME_SLOT = "v_texCoord: new Float32Array(2),"
VARYING_RUNTIME_ALIASES = (
    "this.varyings.v_texCoord[0] = uv[0]",
    "this.varyings.v_texCoord[1] = uv[1]",
)
VARYING_PASS_RUNNER_UV = (
    "uv[0] = fx * inverseWidth",
    "uv[1] = fy * inverseHeight",
)
MUTANT_IDENTITY_KEYS = {
    "anchor_count", "anchor_sha256", "replacement_sha256",
    "anchor_occurrences", "mutated_factory_sha256",
}

# (name, width, height, route)
EXPECTED_CASES = (
    ("range-zero-passthrough", 16, 9, "full"),
    ("live-mirror-max-range", 16, 9, "full"),
    ("live-repeat-portrait", 9, 16, "full"),
    ("tile-crop-translation", 5, 6, "tile"),
)
CASE_NAMES = tuple(name for name, _, _, _ in EXPECTED_CASES)
ANCHOR_CASE = "live-mirror-max-range"
TILE_CASE = "tile-crop-translation"
ZERO_CASE = "range-zero-passthrough"

CROP_RECT = {"crop_x": 3, "crop_y": 2, "tile_width": 5, "tile_height": 6,
             "full_width": 11, "full_height": 9}

# The per-case, per-mutant discrimination ledger. A per-mutant summary is not
# sufficient, so every cell is frozen and every cell is checked.
MUTANT_DISCRIMINATION = {
    "varying-lane-swapped": {
        "range-zero-passthrough": True,
        "live-mirror-max-range": True,
        "live-repeat-portrait": True,
        "tile-crop-translation": True,
    },
    "varying-y-unflipped": {
        "range-zero-passthrough": True,
        "live-mirror-max-range": True,
        "live-repeat-portrait": True,
        "tile-crop-translation": True,
    },
    "offset-sign-flipped": {
        "range-zero-passthrough": False,
        "live-mirror-max-range": True,
        "live-repeat-portrait": True,
        "tile-crop-translation": True,
    },
    "wrap-arm-swapped": {
        "range-zero-passthrough": False,
        "live-mirror-max-range": True,
        "live-repeat-portrait": True,
        "tile-crop-translation": False,
    },
    "speed-fold-phase-shifted": {
        "range-zero-passthrough": False,
        "live-mirror-max-range": True,
        "live-repeat-portrait": True,
        "tile-crop-translation": True,
    },
    "hash31-pcg-divisor-halved": {
        "range-zero-passthrough": False,
        "live-mirror-max-range": True,
        "live-repeat-portrait": True,
        "tile-crop-translation": True,
    },
}
MUTANTS = tuple(MUTANT_DISCRIMINATION)

# (name, expectation)
CONTROLS = (
    ("external-pass-extreme", "identical"),
    ("wrap-binding-unbound", "identical"),
    ("wrap-binding-fractional-0.5", "identical"),
    ("wrap-binding-fractional-1.5", "differs"),
    ("bound-time-live", "differs"),
)

# Frozen wrap-arm census structure: per case, the lane-crossing booleans and
# whether each alternate arm (wrap + 1) % 3 then (wrap + 2) % 3 differs.
WRAP_CROSSING_EXPECTED = {
    "range-zero-passthrough": ((False, False), (False, False)),
    "live-mirror-max-range": ((True, False), (True, False)),
    "live-repeat-portrait": ((False, True), (True, True)),
    "tile-crop-translation": ((False, True), (True, True)),
}

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
    "runtime_binding_abi", "wrap_binding_narrowing", "oracle_authority",
    "varying_materialization", "exactness_contract", "provenance",
    "comparer_self_tests", "coverage_axes", "render_cases", "tile_translation",
    "control_group", "binding_liveness_census", "range_zero_inertness_census",
    "defaults_inertness_census", "wrap_arm_census", "mutation_ledger",
    "mutation_discrimination_contract", "uv_subtexel_invariance",
    "dead_code_census", "claim_boundaries",
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
TRANSLATION_KEYS = {
    "case", "rect", "design_expectation", "measured", "live_clamp_arm",
    "range_zero_arm", "full_route_expected", "why",
    "live_clamp_samplecoord_witness", "range_zero_samplecoord_witness",
    "consequence",
}
ARM_KEYS = {"tile_bindings", "word_mismatches", "byte_mismatches",
            "is_exact_crop", "first_mismatch"}
WITNESS_KEYS = {
    "classification", "probe", "rule", "compared_pairs_per_lane",
    "equal_x_lanes", "equal_y_lanes", "tile_words_le", "tile_sha256",
    "full_route_words_le", "full_route_sha256",
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
        return self.package / "wobble-oracles.json"

    @property
    def report(self) -> pathlib.Path:
        return self.package / "wobble-oracle-report.md"

    @property
    def generator(self) -> pathlib.Path:
        return self.package / "wobble_oracle_generator.mjs"


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
        else:
            if item.get("unbound") is True:
                entry = require_keys(item, {"abi", "unbound", "resolved_toint32_mode"},
                                     field)
                if name != "wrap" or entry["resolved_toint32_mode"] != 0:
                    raise OracleError(
                        f"{field}: only the wrap binding may be recorded "
                        "unbound, and it must resolve to mirror (0)")
                if entry["abi"] != abi:
                    raise OracleError(f"{field}: ABI drift {entry['abi']!r}")
                continue
            entry = require_keys(item, {"abi", "f32_value", "f32_word_le"}
                                 | ({"toint32_mode"} if name == "wrap" else set()),
                                 field)
            if not isinstance(entry["f32_value"], (int, float)) or isinstance(
                    entry["f32_value"], bool):
                raise OracleError(f"{field}: numeric value required")
            require_word_array([entry["f32_word_le"]], 1, field)
            if word_value(entry["f32_word_le"]) != entry["f32_value"]:
                raise OracleError(f"{field}: f32 word disagrees with its value")
            if name == "wrap":
                mode = entry.get("toint32_mode")
                if (not isinstance(mode, int) or isinstance(mode, bool)
                        or not 0 <= mode <= 2
                        or mode != int(entry["f32_value"])):
                    raise OracleError(
                        f"{field}: toint32 mode drift; wrap must narrow by "
                        "truncation to mirror 0 / repeat 1 / clamp 2")
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


def validate_varying(oracle: dict[str, Any]) -> None:
    entry = require_keys(oracle.get("varying_materialization"), {
        "glsl_declaration", "glsl_declaration_site", "javascript_slot_declaration",
        "javascript_slot_kind", "per_pixel_copy", "runtime_alias",
        "numeric_contract", "read_expression", "identifier_occurrences",
        "runtime_slot_line", "runtime_alias_lines", "pass_runner_uv_lines",
        "bound_by", "discriminators", "discriminator_case"},
        "varying_materialization")
    if entry["glsl_declaration"] != VARYING_GLSL_DECLARATION:
        raise OracleError("varying_materialization: GLSL declaration drift")
    if entry["javascript_slot_declaration"] != VARYING_JS_SLOT:
        raise OracleError("varying_materialization: slot declaration drift")
    if "NOT pooled" not in entry["javascript_slot_kind"]:
        raise OracleError(
            "varying_materialization: the slot must be recorded as not pooled")
    if entry["per_pixel_copy"] != VARYING_JS_COPY:
        raise OracleError("varying_materialization: per-pixel copy drift")
    if entry["read_expression"] != VARYING_READ_EXPRESSION:
        raise OracleError("varying_materialization: read expression drift")
    if entry["identifier_occurrences"] != VARYING_OCCURRENCES:
        raise OracleError("varying_materialization: identifier census drift")
    if entry["runtime_slot_line"] != VARYING_RUNTIME_SLOT:
        raise OracleError("varying_materialization: runtime slot line drift")
    if tuple(entry["runtime_alias_lines"]) != VARYING_RUNTIME_ALIASES:
        raise OracleError("varying_materialization: runtime alias lines drift")
    if tuple(entry["pass_runner_uv_lines"]) != VARYING_PASS_RUNNER_UV:
        raise OracleError("varying_materialization: pass-runner uv lines drift")
    if "context.uv" not in entry["runtime_alias"] \
            or "no vertex stage" not in entry["runtime_alias"]:
        raise OracleError(
            "varying_materialization: the runtime alias contract must name "
            "context.uv and the absence of a vertex stage")
    if tuple(entry["discriminators"]) != ("varying-lane-swapped",
                                          "varying-y-unflipped"):
        raise OracleError("varying_materialization: discriminator census drift")
    if entry["discriminator_case"] != ZERO_CASE:
        raise OracleError("varying_materialization: discriminator case drift")
    if "implicit" not in entry["bound_by"]:
        raise OracleError(
            "varying_materialization: the varying must be recorded as bound "
            "implicitly through the pass runner")


def validate_provenance(oracle: dict[str, Any], paths: Paths) -> None:
    provenance = require_keys(oracle.get("provenance"), {
        "node_version", "generator", "native_include_generator", "cpu_snapshot",
        "source", "canonical_factory", "factory_text_method_cross_validation",
        "public_factory_is_canonical_identity", "adapter_override_absent",
        "adapter_routed_keys", "corpus_adapter_keys", "corpus_adapter_source",
        "metadata"},
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
    if sorted(routed) != sorted(CANONICAL_ADAPTER_KEYS):
        raise OracleError("provenance: canonical adapter table census drift")
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
    cross = require_keys(provenance["factory_text_method_cross_validation"], {
        "factory", "sha256", "claim"},
        "provenance.factory_text_method_cross_validation")
    if (cross["factory"] != CROSS_VALIDATION_FACTORY_KEY
            or cross["sha256"] != CROSS_VALIDATION_FACTORY_SHA256):
        raise OracleError(
            "provenance: the toString cross-validation record drifted")
    source = require_keys(provenance["source"], {
        "relative_path_from_noisemaker_for_cpp", "bytes", "sha256",
        "preprocessor_defines"},
        "provenance.source")
    if (source["relative_path_from_noisemaker_for_cpp"] != SOURCE_RELATIVE
            or source["bytes"] != SOURCE_BYTES
            or source["sha256"] != SOURCE_SHA256):
        raise OracleError("provenance: pinned GLSL source mismatch")
    if source["preprocessor_defines"] != []:
        raise OracleError(
            "provenance: wobble has no preprocessor defines; an empty census "
            "is required")
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
        "id", "func", "kind", "pass", "params", "textures",
        "external_texture"}, "provenance.metadata")
    if (metadata["id"] != EFFECT_KEY or metadata["func"] != "wobble"
            or metadata["kind"] != "filter"
            or metadata["textures"] != {} or metadata["external_texture"] is not None):
        raise OracleError("provenance.metadata: effect metadata drift")
    params = metadata["params"]
    if (params["speed"]["default"] != 5 or params["range"]["default"] != 0.5
            or params["wrap"]["default"] != 0
            or params["wrap"]["choices"] != {"mirror": 0, "repeat": 1, "clamp": 2}):
        raise OracleError("provenance.metadata: default parameter drift")
    if metadata["pass"]["program"] != "wobble" \
            or metadata["pass"]["inputs"] != {"inputTex": "inputTex"}:
        raise OracleError("provenance.metadata: pass interface drift")


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


def _crop_lanewise(rect: dict[str, int], tile_words: list[str],
                   full_words: list[str], tile_bytes: list[int],
                   full_bytes: list[int]) -> tuple[int, int, dict[str, Any] | None]:
    word_mismatches = 0
    byte_mismatches = 0
    first: dict[str, Any] | None = None
    channels = ("r", "g", "b", "a")
    for ty in range(rect["tile_height"]):
        for tx in range(rect["tile_width"]):
            for channel in range(4):
                tile_index = ((ty * rect["tile_width"]) + tx) * 4 + channel
                full_index = (((rect["crop_y"] + ty) * rect["full_width"])
                              + (rect["crop_x"] + tx)) * 4 + channel
                if tile_words[tile_index] != full_words[full_index]:
                    word_mismatches += 1
                    if first is None:
                        first = {"top_down_xy": [tx, ty], "channel": channels[channel],
                                 "tile_word": tile_words[tile_index],
                                 "full_word": full_words[full_index]}
                if tile_bytes[tile_index] != full_bytes[full_index]:
                    byte_mismatches += 1
    return word_mismatches, byte_mismatches, first


def _validate_arm(record: dict[str, Any], tile: dict[str, Any],
                  full: dict[str, Any], rect: dict[str, int], label: str,
                  extra: set[str] | None = None) -> None:
    arm = require_keys(record, ARM_KEYS | (extra or set()), label)
    if not isinstance(arm["tile_bindings"], str) or not arm["tile_bindings"]:
        raise OracleError(f"{label}: tile binding description required")
    if arm["is_exact_crop"] is not False:
        raise OracleError(
            f"{label}: the measured non-identity must be recorded as "
            "is_exact_crop false; no crop identity may be asserted for this "
            "program on any arm")
    # Re-derived from the stored arrays, never from the recorded counts.
    word_mismatches, byte_mismatches, first = _crop_lanewise(
        rect, tile["f32_words_le"], full["f32_words_le"],
        tile["rgba8_bytes"], full["rgba8_bytes"])
    if word_mismatches != arm["word_mismatches"] \
            or byte_mismatches != arm["byte_mismatches"]:
        raise OracleError(
            f"{label}: the recorded mismatch counts disagree with the "
            "stored arrays")
    total = rect["tile_width"] * rect["tile_height"] * 4
    if word_mismatches == 0:
        raise OracleError(f"{label}: the tile IS an exact crop; the record is wrong")
    if word_mismatches == total:
        raise OracleError(f"{label}: the routes share no lane; they are unrelated")
    recorded_first = require_keys(arm["first_mismatch"], {
        "top_down_xy", "channel", "tile_word", "full_word"},
        f"{label}.first_mismatch")
    if recorded_first["channel"] not in ("r", "g", "b", "a"):
        raise OracleError(f"{label}.first_mismatch: malformed channel")
    if first is None or recorded_first != first:
        raise OracleError(
            f"{label}: the recorded first mismatch disagrees with the arrays")


def _validate_witness(record: object, rect: dict[str, int], label: str) -> None:
    witness = require_keys(record, WITNESS_KEYS, label)
    require_keys(witness["probe"], {"name"} | MUTANT_IDENTITY_KEYS,
                 f"{label}.probe")
    if "NOT a parity array" not in witness["classification"]:
        raise OracleError(f"{label}: the probe must be labelled as not a parity array")
    compared = rect["tile_width"] * rect["tile_height"]
    if witness["compared_pairs_per_lane"] != compared:
        raise OracleError(f"{label}: compared-pair census mismatch")
    tile_words = require_word_array(
        witness["tile_words_le"], compared * 4, f"{label}.tile_words_le")
    full_words = require_word_array(
        witness["full_route_words_le"],
        rect["full_width"] * rect["full_height"] * 4,
        f"{label}.full_route_words_le")
    if sha256(packed_words(tile_words)) != require_hex64(
            witness["tile_sha256"], f"{label}.tile_sha256"):
        raise OracleError(f"{label}: tile sampleCoord digest mismatch")
    if sha256(packed_words(full_words)) != require_hex64(
            witness["full_route_sha256"], f"{label}.full_route_sha256"):
        raise OracleError(f"{label}: full-route sampleCoord digest mismatch")
    equal_x = 0
    equal_y = 0
    for ty in range(rect["tile_height"]):
        for tx in range(rect["tile_width"]):
            tile_index = ((ty * rect["tile_width"]) + tx) * 4
            full_index = (((rect["crop_y"] + ty) * rect["full_width"])
                          + (rect["crop_x"] + tx)) * 4
            if tile_words[tile_index] == full_words[full_index]:
                equal_x += 1
            if tile_words[tile_index + 1] == full_words[full_index + 1]:
                equal_y += 1
    if equal_x != witness["equal_x_lanes"] or equal_y != witness["equal_y_lanes"]:
        raise OracleError(
            f"{label}: the sampleCoord probe account disagrees with the "
            "stored arrays")
    if equal_x + equal_y == compared * 2:
        raise OracleError(
            f"{label}: every probed lane coincides; the non-identity mechanism "
            "must be re-derived")


def validate_translation(oracle: dict[str, Any],
                         by_name: dict[str, Any]) -> dict[str, Any]:
    record = require_keys(oracle.get("tile_translation"), TRANSLATION_KEYS,
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
    if (tile["input_texture"]["width"] != rect["full_width"]
            or tile["input_texture"]["height"] != rect["full_height"]):
        raise OracleError(
            "tile_translation: the tile case must consume the full-size input")
    if (rect["crop_x"] + rect["tile_width"] > rect["full_width"]
            or rect["crop_y"] + rect["tile_height"] > rect["full_height"]):
        raise OracleError("tile_translation: crop rectangle escapes the full surface")
    full = validate_surface(record["full_route_expected"], rect["full_width"],
                            rect["full_height"], "tile_translation.full_route")
    # The live-clamp arm: the stored tile parity case versus the full route.
    _validate_arm(record["live_clamp_arm"], tile["output_expected"], full, rect,
                  "tile_translation.live_clamp_arm")
    # The range-zero arm: both surfaces stored in the record.
    zero = record["range_zero_arm"]
    zero_extra = {"full_route_expected", "tile_expected"}
    if set(zero) != ARM_KEYS | zero_extra:
        raise OracleError(
            "tile_translation.range_zero_arm: field census mismatch")
    zero_tile = validate_surface(zero["tile_expected"], rect["tile_width"],
                                 rect["tile_height"],
                                 "tile_translation.range_zero_arm.tile_expected")
    zero_full = validate_surface(zero["full_route_expected"], rect["full_width"],
                                 rect["full_height"],
                                 "tile_translation.range_zero_arm.full_route_expected")
    _validate_arm(zero, zero_tile, zero_full, rect,
                  "tile_translation.range_zero_arm", extra=zero_extra)
    if (zero_tile["f32_sha256"] == tile["output_expected"]["f32_sha256"]
            or zero_full["f32_sha256"] == full["f32_sha256"]):
        raise OracleError(
            "tile_translation.range_zero_arm: the probe arm must use its own "
            "bindings, not re-store the live arm's surfaces")
    _validate_witness(record["live_clamp_samplecoord_witness"], rect,
                      "tile_translation.live_clamp_samplecoord_witness")
    _validate_witness(record["range_zero_samplecoord_witness"], rect,
                      "tile_translation.range_zero_samplecoord_witness")
    for field in ("design_expectation", "measured", "why", "consequence"):
        if not isinstance(record[field], str) or not record[field]:
            raise OracleError(f"tile_translation.{field}: prose required")
    if "tileOffset" not in record["why"] or "fullResolution" not in record["why"]:
        raise OracleError(
            "tile_translation.why: the absence of tileOffset/fullResolution "
            "bindings must be stated as the mechanism")
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
    if controls[1]["observed"] != "identical" or controls[2]["observed"] != "identical":
        raise OracleError(
            "control_group: the wrap ToInt32-narrowing axis is not invariant")
    return group


def _digest_verdict(row: dict[str, Any], label: str, anchor_digest: str,
                    expect_live: bool, what: str) -> None:
    require_keys(row, {
        "differs_from_baseline", "changed_lane_count", "f32_sha256",
        "binding"}, label)
    digest_matches = row["f32_sha256"] == anchor_digest
    if row["differs_from_baseline"] is digest_matches:
        raise OracleError(
            f"{label}: the verdict disagrees with the recorded digest")
    if row["differs_from_baseline"] is not (row["changed_lane_count"] > 0):
        raise OracleError(
            f"{label}: changed lane count disagrees with the verdict")
    if row["differs_from_baseline"] is not expect_live:
        raise OracleError(f"{label}: {what}")


def validate_binding_censuses(oracle: dict[str, Any],
                              by_name: dict[str, Any]) -> None:
    anchor_digest = by_name[ANCHOR_CASE]["output_expected"]["f32_sha256"]
    liveness = require_keys(oracle.get("binding_liveness_census"), {
        "probe_case", "rule", "probes"}, "binding_liveness_census")
    if liveness["probe_case"] != ANCHOR_CASE:
        raise OracleError("binding_liveness_census: unexpected probe case")
    probes = liveness["probes"]
    if not isinstance(probes, list) or tuple(
            probe.get("binding") for probe in probes) != LIVE_BINDINGS:
        raise OracleError("binding_liveness_census: probe census mismatch")
    for probe in probes:
        _digest_verdict(probe, f"binding_liveness_census.{probe['binding']}",
                        anchor_digest, True,
                        "recorded live but invariant; the census is vacuous")

    zero_digest = by_name[ZERO_CASE]["output_expected"]["f32_sha256"]
    zero = require_keys(oracle.get("range_zero_inertness_census"), {
        "probe_case", "rule", "inert", "range_discriminator"},
        "range_zero_inertness_census")
    if zero["probe_case"] != ZERO_CASE:
        raise OracleError("range_zero_inertness_census: unexpected probe case")
    if tuple(entry.get("binding") for entry in zero["inert"]) != ("time", "speed", "wrap"):
        raise OracleError("range_zero_inertness_census: inert census mismatch")
    for entry in zero["inert"]:
        _digest_verdict(entry, f"range_zero_inertness_census.{entry['binding']}",
                        zero_digest, False,
                        "recorded inert on the range-zero case but a probe "
                        "changed the output")
    _digest_verdict(zero["range_discriminator"],
                    "range_zero_inertness_census.range_discriminator",
                    zero_digest, True,
                    "range does not wake the warp path; the discriminator "
                    "premise is wrong")

    defaults = require_keys(oracle.get("defaults_inertness_census"), {
        "probe_case", "rule", "offset_f32_words_le",
        "baseline_f32_sha256", "baseline_rgba8_sha256", "probes"},
        "defaults_inertness_census")
    for field in ("baseline_f32_sha256", "baseline_rgba8_sha256"):
        require_hex64(defaults[field], f"defaults_inertness_census.{field}")
    require_word_array(defaults["offset_f32_words_le"], 3,
                       "defaults_inertness_census.offset_f32_words_le")
    entries = defaults["probes"]
    if not isinstance(entries, list) or tuple(
            entry.get("binding") for entry in entries) != ("time", "speed", "range", "wrap"):
        raise OracleError("defaults_inertness_census: probe census mismatch")
    for entry in entries:
        label = f"defaults_inertness_census.{entry['binding']}"
        item = require_keys(entry, {"binding", "probes"}, label)
        if not isinstance(item["probes"], list) or len(item["probes"]) != 2:
            raise OracleError(f"{label}: two probes per binding are required")
        for probe in item["probes"]:
            row = require_keys(probe, {
                "override", "differs_from_baseline", "changed_lane_count",
                "f32_sha256"}, f"{label}.probe")
            if row["differs_from_baseline"] is not False:
                raise OracleError(
                    f"{label}: at the shipped defaults the census is wrong; a "
                    "probe moved the output")
            if row["f32_sha256"] != defaults["baseline_f32_sha256"]:
                raise OracleError(
                    f"{label}: an inert defaults probe must carry the defaults "
                    "baseline digest")
            if row["changed_lane_count"] != 0:
                raise OracleError(f"{label}: changed lane count disagrees")


def validate_wrap_census(oracle: dict[str, Any],
                         by_name: dict[str, Any]) -> None:
    census = require_keys(oracle.get("wrap_arm_census"), {"rule", "rows"},
                          "wrap_arm_census")
    rows = census["rows"]
    if not isinstance(rows, list) or tuple(
            row.get("case") for row in rows) != CASE_NAMES:
        raise OracleError("wrap_arm_census: row census mismatch")
    for row in rows:
        name = row["case"]
        label = f"wrap_arm_census.{name}"
        entry = require_keys(row, {
            "case", "wrap_binding", "arm", "offset_f32_words_le",
            "half_texel_margins", "lane_crosses_boundary", "any_crossing",
            "alternates"}, label)
        case = by_name[name]
        width = case["width"]
        height = case["height"]
        wrap = case["bindings"]["wrap"]["toint32_mode"]
        if entry["wrap_binding"] != wrap:
            raise OracleError(f"{label}: wrap binding disagrees with the case")
        expected_arm = {0: "mirror", 1: "repeat", 2: "clamp"}[wrap]
        if entry["arm"] != expected_arm:
            raise OracleError(f"{label}: arm name drift")
        offsets = require_word_array(entry["offset_f32_words_le"], 2,
                                     f"{label}.offset_f32_words_le")
        margins = entry["half_texel_margins"]
        if (not isinstance(margins, list) or len(margins) != 2
                or margins != [0.5 / width, 0.5 / height]):
            raise OracleError(f"{label}: half-texel margin arithmetic drift")
        # The crossing flags are re-derived from the stored offset words.
        crossing = [abs(word_value(word)) > margin
                    for word, margin in zip(offsets, margins)]
        if entry["lane_crosses_boundary"] != crossing:
            raise OracleError(
                f"{label}: the lane-crossing census disagrees with the stored "
                "offset words and margins")
        if entry["any_crossing"] is not (crossing[0] or crossing[1]):
            raise OracleError(f"{label}: any_crossing disagrees with the lanes")
        alternates = entry["alternates"]
        if not isinstance(alternates, list) or len(alternates) != 2:
            raise OracleError(f"{label}: two alternates are required")
        expected_crossing, expected_differs = WRAP_CROSSING_EXPECTED[name]
        if crossing != list(expected_crossing):
            raise OracleError(
                f"{label}: crossing structure drift; re-freeze from measurement")
        case_digest = case["output_expected"]["f32_sha256"]
        for index, alternate in enumerate(alternates):
            alt = require_keys(alternate, {
                "wrap_binding", "arm", "differs_from_case",
                "changed_lane_count", "f32_sha256"}, f"{label}.alternate[{index}]")
            expected_wrap = (wrap + index + 1) % 3
            if alt["wrap_binding"] != expected_wrap:
                raise OracleError(f"{label}.alternate[{index}]: wrap order drift")
            if alt["arm"] != {0: "mirror", 1: "repeat", 2: "clamp"}[expected_wrap]:
                raise OracleError(f"{label}.alternate[{index}]: arm name drift")
            digest_matches = alt["f32_sha256"] == case_digest
            if alt["differs_from_case"] is digest_matches:
                raise OracleError(
                    f"{label}.alternate[{index}]: the verdict disagrees with "
                    "the recorded digest")
            if alt["differs_from_case"] is not (alt["changed_lane_count"] > 0):
                raise OracleError(
                    f"{label}.alternate[{index}]: changed lane count disagrees")
            if alt["differs_from_case"] is not expected_differs[index]:
                raise OracleError(
                    f"{label}.alternate[{index}]: wrap-switch structure drift; "
                    "re-freeze from measurement")


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
    # The overlap must be DISCLOSED, not hidden: the mutants pin overlapping
    # regions of one program and their witness sets overlap by construction.
    if "overlap" not in contract["witness_overlap_disclosure"].lower():
        raise OracleError(
            "mutation_discrimination_contract: the witness overlap must be "
            "disclosed, not silently asserted disjoint")
    excluded = require_keys(contract["excluded_from_ledger"], {
        "uv-subtexel-perturbed"},
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
                    f"{label}: non-discriminating case {row['case']} changed")
            (witnesses if expected else controls).append(row["case"])
        if entry["witness_cases"] != witnesses or entry["control_cases"] != controls:
            raise OracleError(f"{label}: witness/control partition drift")
        if not witnesses:
            raise OracleError(f"{label}: no case witnesses this mutant")
    # The two varying mutants are the only ones that may move the pure
    # pass-through case -- the discriminator structure itself is frozen.
    zero_witnesses = [name for name in MUTANTS
                      if MUTANT_DISCRIMINATION[name][ZERO_CASE]]
    if zero_witnesses != ["varying-lane-swapped", "varying-y-unflipped"]:
        raise OracleError(
            "mutation_ledger: on the pure pass-through case ONLY the two "
            "varying mutants may witness; the discriminator structure drifted")
    return ledger


def validate_extras(oracle: dict[str, Any], by_name: dict[str, Any]) -> None:
    near_ulp = require_keys(oracle.get("uv_subtexel_invariance"), {
        "status", "rendered_mutant", "rendered_divergences", "reason"},
        "uv_subtexel_invariance")
    if near_ulp["status"] != "measured-invariant":
        raise OracleError("uv_subtexel_invariance: status drift")
    rows = require_keys(near_ulp["rendered_mutant"],
                        {"name", "rows"} | MUTANT_IDENTITY_KEYS,
                        "uv_subtexel_invariance.rendered_mutant")["rows"]
    validate_invariant_rows(rows, "uv_subtexel_invariance.rendered_mutant",
                            by_name)
    if near_ulp["rendered_divergences"] != 0:
        raise OracleError("uv_subtexel_invariance: the sub-texel mutant diverged")

    dead = require_keys(oracle.get("dead_code_census"), {
        "status", "design_reference", "claim"}, "dead_code_census")
    if dead["status"] != "no-dead-code-exists":
        raise OracleError("dead_code_census: status drift")
    if "algebraic" not in dead["claim"]:
        raise OracleError(
            "dead_code_census: the range-zero control rows must be recorded "
            "as algebraic cancellations, never as skip/strip agreements")


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
            "Wobble oracle records an absolute filesystem path "
            f"({leaked.group(0)!r}); the gate must be path-independent")
    try:
        oracle = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OracleError(f"invalid Wobble JSON: {error}") from error
    require_keys(oracle, TOP_LEVEL_KEYS, "oracle")
    if (oracle["schema"], oracle["schema_version"], oracle["program_key"],
            oracle["effect_key"], oracle["runtime_key"],
            oracle["corpus_revision"], oracle["upstream_revision"]) != (
                SCHEMA, SCHEMA_VERSION, PROGRAM_KEY, EFFECT_KEY, PROGRAM_KEY,
                CORPUS_REVISION, UPSTREAM_REVISION):
        raise OracleError("Wobble schema/program identity mismatch")
    if oracle["defines"] != DEFINES:
        raise OracleError("Wobble define mismatch: wobble has no defines")
    if tuple(oracle["runtime_binding_names"]) != BINDING_NAMES:
        raise OracleError("Wobble runtime binding census mismatch")
    if oracle["runtime_binding_abi"] != BINDING_ABI:
        raise OracleError("Wobble runtime binding ABI mismatch")
    if not isinstance(oracle["wrap_binding_narrowing"], str) \
            or "ToInt32" not in oracle["wrap_binding_narrowing"]:
        raise OracleError(
            "Wobble: the wrap ToInt32 narrowing contract must be stated")
    validate_provenance(oracle, paths)
    validate_varying(oracle)
    self_tests = oracle.get("comparer_self_tests")
    if not isinstance(self_tests, dict) or any(
            self_tests.get(name) is not True for name in REQUIRED_SELF_TESTS):
        raise OracleError("Wobble comparer self-test mismatch")
    cases = oracle.get("render_cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise OracleError("Wobble fixture count mismatch")
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
        wrap_mode = entry["bindings"]["wrap"]["toint32_mode"]
        if {0: "mirror", 1: "repeat", 2: "clamp"}.get(wrap_mode) is None:
            raise OracleError(f"{name}: unknown wrap mode {wrap_mode!r}")
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
    coverage = oracle.get("coverage_axes")
    if not isinstance(coverage, dict) or not coverage:
        raise OracleError("Wobble: coverage axes required")
    for axis, buckets in coverage.items():
        for bucket, bucket_names in buckets.items():
            if not isinstance(bucket_names, list) or not bucket_names:
                raise OracleError(f"coverage axis {axis} bucket {bucket} has no witness")
            for name in bucket_names:
                if name not in by_name:
                    raise OracleError(f"coverage axis {axis} names unknown case {name}")
    validate_translation(oracle, by_name)
    validate_controls(oracle, by_name)
    validate_binding_censuses(oracle, by_name)
    validate_wrap_census(oracle, by_name)
    validate_mutations(oracle, by_name)
    validate_extras(oracle, by_name)
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
        "// Generated from the checked canonical JavaScript Wobble oracle.",
        "// Do not edit; C++ output never participates in these expected",
        "// arrays.",
        "//",
        "// filter/wobble:wobble is the first varying-admission program: the",
        "// parity target is the materialization of `in vec2 v_texCoord;`,",
        "// which the JavaScript equates with context.uv (the pixel center's",
        "// destination-local coordinate; no vertex stage, no interpolation,",
        "// no varying binding -- bound implicitly by the pass runner). The",
        "// range = 0 case is the pure pass-through discriminator; only the",
        "// two varying mutants move a lane on it. The tile route is a",
        "// measured NON-crop of the full route on both arms: wobble has no",
        "// tileOffset/fullResolution bindings and v_texCoord is",
        "// destination-local. Never assert a crop identity here.",
        "#pragma once", "", "namespace wobble189_oracle {", "",
        f'inline constexpr std::string_view kOracleSha256 = "{oracle_hash}";',
        f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";',
        f'inline constexpr std::string_view kCorpusRevision = "{CORPUS_REVISION}";',
        f"inline constexpr std::size_t kCaseCount = {len(cases)}U;",
        f"inline constexpr std::size_t kBindingCount = {len(BINDING_NAMES)}U;",
        "",
        f"inline constexpr std::array<std::string_view, {len(BINDING_NAMES)}> "
        "kBindingNames{{",
        "    " + ", ".join(f'"{name}"' for name in BINDING_NAMES) + ",",
        "}};", "",
    ]
    for index, case in enumerate(cases):
        # The input texture travels with the case (normalMap/cellrefract
        # precedent): the native test binds it as inputTex verbatim, and a
        # pattern name would be a second chance to disagree with the authority.
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
    for label, surface in (
            ("TranslationFull", translation["full_route_expected"]),
            ("RangeZeroTile", translation["range_zero_arm"]["tile_expected"]),
            ("RangeZeroFull", translation["range_zero_arm"]["full_route_expected"])):
        lines.append(
            f"inline constexpr std::array<std::uint32_t, "
            f"{len(surface['f32_words_le'])}> k{label}ExpectedWords{{{{")
        lines.extend(array_lines(surface["f32_words_le"], "U", 8))
        lines.extend(["}};", ""])
        lines.append(
            f"inline constexpr std::array<std::uint8_t, "
            f"{len(surface['rgba8_bytes'])}> k{label}ExpectedRgba8{{{{")
        lines.extend(array_lines(surface["rgba8_bytes"], "U", 16))
        lines.extend(["}};", ""])
    lines.extend([
        "struct CaseView {",
        "  std::string_view name;",
        "  std::size_t width;",
        "  std::size_t height;",
        "  std::string_view route;",
        "  std::string_view wrap_arm;",
        "  std::int32_t wrap_mode;",
        "  std::size_t input_width;",
        "  std::size_t input_height;",
        "  std::string_view input_f32_sha256;",
        "  std::span<const std::uint32_t> input_words;",
        "  std::span<const std::uint32_t> expected_words;",
        "  std::span<const std::uint8_t> expected_rgba8;",
        "  std::uint32_t time_word;",
        "  std::uint32_t speed_word;",
        "  std::uint32_t range_word;",
        "  std::uint32_t wrap_word;",
        "  std::uint32_t external_time_word;",
        "  std::uint32_t external_seed_word;",
        "};", "",
        "// The tile route is a measured non-crop on BOTH arms (the counts",
        "// below); wobble has no tileOffset/fullResolution bindings and",
        "// v_texCoord is destination-local. The full-route and range-zero",
        "// surfaces above are parity surfaces in their own right; never",
        "// compare the tile against a crop of any of them.",
        "struct TranslationProofView {",
        "  std::string_view tile_case;",
        "  std::size_t crop_x;",
        "  std::size_t crop_y;",
        "  std::size_t tile_width;",
        "  std::size_t tile_height;",
        "  std::size_t full_width;",
        "  std::size_t full_height;",
        "  std::size_t live_clamp_word_mismatches;",
        "  std::size_t live_clamp_byte_mismatches;",
        "  std::size_t range_zero_word_mismatches;",
        "  std::size_t range_zero_byte_mismatches;",
        "  std::size_t live_probe_equal_x_lanes;",
        "  std::size_t live_probe_equal_y_lanes;",
        "  std::size_t zero_probe_equal_x_lanes;",
        "  std::size_t zero_probe_equal_y_lanes;",
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
        wrap_mode = binding["wrap"]["toint32_mode"]
        wrap_arm = {0: "mirror", 1: "repeat", 2: "clamp"}[wrap_mode]
        lines.append(
            f'  CaseView{{"{case["name"]}", {case["width"]}U, {case["height"]}U, '
            f'"{case["route"]}", "{wrap_arm}", {wrap_mode}, '
            f'{input_texture["width"]}U, {input_texture["height"]}U, '
            f'"{binding["inputTex"]["f32_sha256"]}", kCase{index}InputWords, '
            f'kCase{index}ExpectedWords, kCase{index}ExpectedRgba8, '
            f'{binding["time"]["f32_word_le"]}U, {binding["speed"]["f32_word_le"]}U, '
            f'{binding["range"]["f32_word_le"]}U, {binding["wrap"]["f32_word_le"]}U, '
            f'{external["time"]["f32_word_le"]}U, {external["seed"]["f32_word_le"]}U}},')
    rect = translation["rect"]
    live_arm = translation["live_clamp_arm"]
    zero_arm = translation["range_zero_arm"]
    live_witness = translation["live_clamp_samplecoord_witness"]
    zero_witness = translation["range_zero_samplecoord_witness"]
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
        f'    {live_arm["word_mismatches"]}U, {live_arm["byte_mismatches"]}U, '
        f'{zero_arm["word_mismatches"]}U, {zero_arm["byte_mismatches"]}U,',
        f'    {live_witness["equal_x_lanes"]}U, {live_witness["equal_y_lanes"]}U, '
        f'{zero_witness["equal_x_lanes"]}U, {zero_witness["equal_y_lanes"]}U}};', "",
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
                # comma would not compile; this arm is exercised by the real
                # data whenever a mutant has no control cases.
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
        "}  // namespace wobble189_oracle", "",
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
    for name in ("wobble-oracles.json", "wobble-oracle-report.md",
                 "wobble_oracle_generator.mjs"):
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


def _forge_arm_counts(doc: dict[str, Any], arm: str) -> None:
    doc["tile_translation"][arm]["word_mismatches"] = 3
    doc["tile_translation"][arm]["byte_mismatches"] = 3


def _forge_probe_digest(doc: dict[str, Any]) -> None:
    witness = doc["tile_translation"]["live_clamp_samplecoord_witness"]
    witness["tile_words_le"][0] = "0x7f7fffff"


def _forge_probe_equal(doc: dict[str, Any]) -> None:
    witness = doc["tile_translation"]["range_zero_samplecoord_witness"]
    witness["equal_x_lanes"] = 0
    witness["equal_y_lanes"] = 0


def _fabricate_control(doc: dict[str, Any]) -> None:
    """Swap a lane of the `identical` unbound-wrap control for a foreign value."""
    surface = doc["control_group"]["controls"][1]["output"]
    surface["f32_words_le"][0] = "0x7f7fffff"
    surface["rgba8_bytes"][0] = 7
    _refresh_surface_digests(surface)


def _fabricate_live_probe(doc: dict[str, Any]) -> None:
    doc["binding_liveness_census"]["probes"][0]["differs_from_baseline"] = False


def _fabricate_zero_inert(doc: dict[str, Any]) -> None:
    doc["range_zero_inertness_census"]["inert"][0]["differs_from_baseline"] = True
    doc["range_zero_inertness_census"]["inert"][0]["changed_lane_count"] = 12


def _fabricate_range_discriminator(doc: dict[str, Any]) -> None:
    doc["range_zero_inertness_census"]["range_discriminator"][
        "differs_from_baseline"] = False
    doc["range_zero_inertness_census"]["range_discriminator"][
        "changed_lane_count"] = 0


def _fabricate_defaults_probe(doc: dict[str, Any]) -> None:
    doc["defaults_inertness_census"]["probes"][0]["probes"][0][
        "differs_from_baseline"] = True
    doc["defaults_inertness_census"]["probes"][0]["probes"][0][
        "changed_lane_count"] = 5


def _fabricate_wrap_crossing(doc: dict[str, Any]) -> None:
    doc["wrap_arm_census"]["rows"][1]["lane_crosses_boundary"] = [False, True]


def _fabricate_wrap_verdict(doc: dict[str, Any]) -> None:
    doc["wrap_arm_census"]["rows"][1]["alternates"][1][
        "differs_from_case"] = True
    doc["wrap_arm_census"]["rows"][1]["alternates"][1]["changed_lane_count"] = 4


def _fabricate_mutant_digest(doc: dict[str, Any]) -> None:
    ledger = doc["mutation_ledger"][0]
    row = next(item for item in ledger["results"]
               if item["case"] == ANCHOR_CASE)
    canonical = next(case for case in doc["render_cases"]
                     if case["name"] == ANCHOR_CASE)["output_expected"]
    row["f32_sha256"] = canonical["f32_sha256"]
    row["rgba8_sha256"] = canonical["rgba8_sha256"]


def _forge_near_ulp(doc: dict[str, Any]) -> None:
    row = doc["uv_subtexel_invariance"]["rendered_mutant"]["rows"][0]
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
         lambda doc: doc["render_cases"][0]["bindings"]["speed"]
         .__setitem__("f32_word_le", "0x1"),
         "malformed Float32 word at 0"),
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
        ("factory-name-drift",
         lambda doc: doc["provenance"]["canonical_factory"].__setitem__(
             "name", "canonicalFactory177"), "canonical factory identity mismatch"),
        ("cross-validation-drift",
         lambda doc: doc["provenance"]["factory_text_method_cross_validation"]
         .__setitem__("sha256", "0" * 64),
         "toString cross-validation record drifted"),
        ("adapter-routed-key",
         lambda doc: doc["provenance"]["adapter_routed_keys"].append(PROGRAM_KEY),
         "must be absent from the adapter table"),
        ("canonical-adapter-census-drift",
         lambda doc: doc["provenance"]["adapter_routed_keys"].append(
             "filter/bogus:bogus"),
         "canonical adapter table census drift"),
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
        ("preprocessor-define-drift",
         lambda doc: doc["provenance"]["source"].__setitem__(
             "preprocessor_defines", ["MODE"]),
         "no preprocessor defines"),
        ("binding-census-drift",
         lambda doc: doc["runtime_binding_names"].append("palette"),
         "runtime binding census mismatch"),
        ("binding-abi-drift",
         lambda doc: doc["render_cases"][0]["bindings"]["time"].__setitem__(
             "abi", "int32"), "ABI drift"),
        ("wrap-mode-drift",
         lambda doc: doc["render_cases"][0]["bindings"]["wrap"].__setitem__(
             "toint32_mode", 1), "toint32 mode drift"),
        ("binding-order-drift",
         lambda doc: doc["render_cases"][0]["bindings"].__setitem__(
             "time", doc["render_cases"][0]["bindings"].pop("time")),
         "binding order drift"),
        ("defines-drift",
         lambda doc: doc.__setitem__("defines", {"KERNEL": 1}),
         "Wobble define mismatch"),
        ("schema-drift",
         lambda doc: doc.__setitem__("schema_version", 2),
         "schema/program identity mismatch"),
        ("varying-glsl-declaration-drift",
         lambda doc: doc["varying_materialization"].__setitem__(
             "glsl_declaration", "in vec2 vUv;"),
         "GLSL declaration drift"),
        ("varying-slot-declaration-drift",
         lambda doc: doc["varying_materialization"].__setitem__(
             "javascript_slot_declaration",
             "var v_texCoord = new Float32Array(2);"),
         "slot declaration drift"),
        ("varying-copy-drift",
         lambda doc: doc["varying_materialization"].__setitem__(
             "per_pixel_copy", "v_texCoord.set(context.uv)"),
         "per-pixel copy drift"),
        ("varying-pooled-claim",
         lambda doc: doc["varying_materialization"].__setitem__(
             "javascript_slot_kind", "a pooled array"),
         "must be recorded as not pooled"),
        ("varying-occurrence-drift",
         lambda doc: doc["varying_materialization"].__setitem__(
             "identifier_occurrences", 6), "identifier census drift"),
        ("varying-alias-line-drift",
         lambda doc: doc["varying_materialization"].__setitem__(
             "runtime_alias_lines",
             ["this.varyings.v_texCoord[0] = fragCoord[0]",
              "this.varyings.v_texCoord[1] = fragCoord[1]"]),
         "runtime alias lines drift"),
        ("varying-read-expression-drift",
         lambda doc: doc["varying_materialization"].__setitem__(
             "read_expression", "v_texCoord"), "read expression drift"),
        ("varying-bound-by-drift",
         lambda doc: doc["varying_materialization"].__setitem__(
             "bound_by", "an explicit binding"),
             "recorded as bound implicitly"),
        ("alpha-word-drift", _break_alpha_word, "alpha Float32 word at lane 3"),
        ("alpha-byte-drift", _break_alpha_byte, "alpha RGBA8 byte at lane 3"),
        ("tile-live-arm-claims-exact-crop",
         lambda doc: doc["tile_translation"]["live_clamp_arm"].__setitem__(
             "is_exact_crop", True), "no crop identity may be asserted"),
        ("tile-zero-arm-claims-exact-crop",
         lambda doc: doc["tile_translation"]["range_zero_arm"].__setitem__(
             "is_exact_crop", True), "no crop identity may be asserted"),
        ("tile-live-arm-counts-forged",
         lambda doc: _forge_arm_counts(doc, "live_clamp_arm"),
         "recorded mismatch counts disagree"),
        ("tile-zero-arm-counts-forged",
         lambda doc: _forge_arm_counts(doc, "range_zero_arm"),
         "recorded mismatch counts disagree"),
        ("tile-probe-digest-forged", _forge_probe_digest,
         "sampleCoord digest mismatch"),
        ("tile-probe-equal-forged", _forge_probe_equal,
         "sampleCoord probe account disagrees"),
        ("tile-zero-arm-restores-live-surfaces",
         lambda doc: doc["tile_translation"]["range_zero_arm"].__setitem__(
             "tile_expected", doc["render_cases"][3]["output_expected"]),
         "recorded mismatch counts disagree"),
        ("tile-why-mechanism-dropped",
         lambda doc: doc["tile_translation"].__setitem__(
             "why", "the tile is smaller"),
             "absence of tileOffset/fullResolution"),
        ("external-control-drift",
         lambda doc: doc["control_group"]["controls"][0].__setitem__(
             "observed", "differs"),
         "pass ledger disagrees with observation"),
        ("unbound-wrap-control-drift",
         lambda doc: (
             doc["control_group"]["controls"][1].__setitem__("observed", "differs"),
             doc["control_group"]["controls"][1].__setitem__("pass", False)),
         "control did not pass"),
        ("baseline-digest-drift",
         lambda doc: doc["control_group"]["baseline"].__setitem__(
             "f32_sha256", "0" * 64),
         "digests disagree with the anchor case"),
        ("fabricated-unbound-wrap-control", _fabricate_control,
         "recorded observation 'identical' disagrees with the stored arrays"),
        ("liveness-probe-fabricated", _fabricate_live_probe,
         "the verdict disagrees with the recorded digest"),
        ("zero-inert-fabricated", _fabricate_zero_inert,
         "the verdict disagrees with the recorded digest"),
        ("range-discriminator-fabricated", _fabricate_range_discriminator,
         "the verdict disagrees with the recorded digest"),
        ("defaults-probe-fabricated", _fabricate_defaults_probe,
         "at the shipped defaults the census is wrong"),
        ("defaults-baseline-drift",
         lambda doc: doc["defaults_inertness_census"].__setitem__(
             "baseline_f32_sha256", "0" * 64),
         "an inert defaults probe must carry the defaults baseline digest"),
        ("wrap-crossing-fabricated", _fabricate_wrap_crossing,
         "lane-crossing census disagrees"),
        ("wrap-verdict-fabricated", _fabricate_wrap_verdict,
         "the verdict disagrees with the recorded digest"),
        ("wrap-margin-arithmetic-drift",
         lambda doc: doc["wrap_arm_census"]["rows"][0]["half_texel_margins"]
         .__setitem__(0, 0.5),
         "half-texel margin arithmetic drift"),
        ("mutant-census-drift",
         lambda doc: doc["mutation_ledger"].pop(), "mutant census mismatch"),
        ("mutant-per-case-table-drift",
         lambda doc: doc["mutation_discrimination_contract"]["expected"]
         ["wrap-arm-swapped"].__setitem__("tile-crop-translation", True),
         "does not match the frozen table"),
        ("mutant-row-expectation-drift",
         lambda doc: doc["mutation_ledger"][2]["results"][0].__setitem__(
             "expected_discriminates", True),
         "carries the wrong per-case expectation"),
        ("mutant-witness-non-discriminating",
         lambda doc: doc["mutation_ledger"][2]["results"][1].__setitem__(
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
             "witness_cases", ["live-mirror-max-range"]),
         "disagrees with the frozen per-case table"),
        ("overlap-undisclosed",
         lambda doc: doc["mutation_discrimination_contract"].__setitem__(
             "witness_overlap_disclosure", "the sets are disjoint"),
         "witness overlap must be disclosed"),
        ("zero-case-discriminator-structure-drift",
         lambda doc: doc["mutation_discrimination_contract"]["expected"]
         ["offset-sign-flipped"].__setitem__("range-zero-passthrough", True),
         "does not match the frozen table"),
        ("near-ulp-forged", _forge_near_ulp,
         "the row must be invariant"),
        ("dead-code-status-drift",
         lambda doc: doc["dead_code_census"].__setitem__(
             "status", "nonreaching-control-present"),
         "dead_code_census: status drift"),
        ("dead-code-claim-drift",
         lambda doc: doc["dead_code_census"].__setitem__(
             "claim", "the branch is skipped at the frozen define"),
         "recorded as algebraic cancellations"),
        ("excluded-ledger-entry-dropped",
         lambda doc: doc["mutation_discrimination_contract"]
         ["excluded_from_ledger"].pop("uv-subtexel-perturbed"),
         "missing field(s) uv-subtexel-perturbed"),
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
        ("wrap-narrowing-note-dropped",
         lambda doc: doc.__setitem__("wrap_binding_narrowing", "wrap is a float"),
         "wrap ToInt32 narrowing contract must be stated"),
    )
    passed = 0
    with tempfile.TemporaryDirectory(prefix="wobble189-selftest-") as raw:
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
        _expect_rejection(broken_json, "invalid Wobble JSON", "broken-json")
        passed += 1
    print(f"Wobble native oracle materializer self-test ok ({passed} checks)")
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
                    "generated Wobble native include is stale")
    except (OSError, OracleError) as error:
        print(f"glslcpp: {error}", file=sys.stderr)
        return 1
    oracle, _ = load(LIVE)
    words = sum(len(case["output_expected"]["f32_words_le"])
                for case in oracle["render_cases"])
    witnesses = {mutant["name"]: len(mutant["witness_cases"])
                 for mutant in oracle["mutation_ledger"]}
    translation = oracle["tile_translation"]
    print(f"Wobble native oracle include ok "
          f"({len(EXPECTED_CASES)} cases, {words} case words, "
          f"{len(translation['full_route_expected']['f32_words_le'])} full-route words, "
          f"{len(MUTANTS)} mutants, per-case witnesses "
          + ", ".join(f"{name}={count}" for name, count in witnesses.items())
          + f", tile non-crop clamp {translation['live_clamp_arm']['word_mismatches']}"
          f"/{translation['range_zero_arm']['word_mismatches']} of "
          f"{translation['rect']['tile_width'] * translation['rect']['tile_height'] * 4} words)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
