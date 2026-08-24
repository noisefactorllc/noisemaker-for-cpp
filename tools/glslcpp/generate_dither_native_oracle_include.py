"""Materialize the authenticated dither JSON oracle as a C++20 include."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
ORACLE = ROOT / "docs/port-engineering/dither-parity/dither-oracles.json"
OUT = ROOT / "tests/oracles/dither_expected.inc"
KEY = "filter/dither:dither"
BASELINE_NAMES = (
    "bayer2-input", "bayer8-tiled", "dot-input", "line-input", "crosshatch-input",
    "noise-input", "fallback-type", "error-diffusion-input", "error-diffusion-input-tiled",
)
ADVERSARIAL_NAMES = ("error-diffusion-negative-tile", "levels-2-boundary", "levels-16-boundary")
CASE_NAMES = BASELINE_NAMES + ADVERSARIAL_NAMES
MUTATION_NAMES = ("fallback-default", "quantize-levels", "error-diffusion-route")
EXPECTED_BINDINGS = {
    "bayer2-input": (4, 3, 0, 0, 4, 0, 1, 1, 1, 0, (0, 0), (4, 3)),
    "bayer8-tiled": (7, 5, 2, 0, 5, .13, 2, 1, .85, .2, (3, 2), (24, 20)),
    "dot-input": (6, 4, 3, 0, 4, -.2, 2, 1.25, 1, .4, (2, 1), (18, 14)),
    "line-input": (5, 6, 4, 0, 4, .2, 3, .75, .6, .75, (4, 3), (20, 24)),
    "crosshatch-input": (6, 5, 5, 0, 4, 0, 1, 1, 1, .1, (1, 4), (12, 10)),
    "noise-input": (7, 4, 6, 0, 4, -.1, 2, 1, .9, 1.1, (5, 2), (28, 16)),
    "fallback-type": (3, 3, 99, 0, 4, 0, 1, 1, 1, 0, (0, 0), (3, 3)),
    "error-diffusion-input": (5, 5, 7, 0, 4, 0, 1, 1, 1, .33, (0, 0), (5, 5)),
    "error-diffusion-input-tiled": (6, 4, 7, 0, 4, .1, 2, 1, .8, -.2, (2, 1), (18, 12)),
    "error-diffusion-negative-tile": (6, 4, 7, 0, 4, .1, 2, 1, .8, -.2, (-9, 2), (18, 12)),
    "levels-2-boundary": (4, 3, 0, 0, 2, 0, 1, 1, 1, 0, (0, 0), (4, 3)),
    "levels-16-boundary": (4, 3, 0, 0, 16, 0, 1, 1, 1, 0, (0, 0), (4, 3)),
}
EXPECTED_MUTATIONS = {
    "fallback-default": (("fallback-type", 6, 4),),
    "quantize-levels": (("bayer2-input", 30, 26),),
    "error-diffusion-route": (("error-diffusion-input", 25, 22), ("error-diffusion-input-tiled", 13, 13)),
}
EXPECTED_MUTATION_WITNESSES = {
    "fallback-default": (("fallback-type", 6, 4, 6, "0x3eaaaaab", "0x00000000", 6, 85, 0),),
    "quantize-levels": (("bayer2-input", 30, 26, 0, "0xbeaaaaab", "0xbe800000", 4, 255, 191),),
    "error-diffusion-route": (
        ("error-diffusion-input", 25, 22, 5, "0x3f2aaaab", "0x3f800000", 5, 170, 255),
        ("error-diffusion-input-tiled", 13, 13, 2, "0x3f317e4b", "0x3f75c28f", 2, 177, 245),
    ),
}
EXPECTED_BLOCKER = {
    "route": "palette != PALETTE_INPUT",
    "error": "ditherWithPalette(...).reduce is not a function",
    "source_anchor": "ditherWithPalette(...).reduce((res,el,i)=>(res[i] = el, res), result)",
    "reproducible": True,
}
EXPECTED_POLICY = {"f32_words_exact", "rgba8_bytes_exact", "dimensions_before_data", "signed_zero_exact", "input_bits_exact", "public_direct_exact", "repeat_identity_exact"}
CORPUS_SOURCE = "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/dither/dither.glsl"
CORPUS_SOURCE_SHA256 = "a966f1746213c8206c5cb57a88cafd8033eb8f8cb08b207209eb31479a11abdb"
EXPECTED_UPSTREAM_REVISION = "117a236679d1db3ab8f0e278230ece277b57564c"
EXPECTED_SOURCE = {"relative_path": "src/effects/generated/canonical-kernels.js", "bytes": 1713290, "sha256": "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe"}
EXPECTED_FACTORY = {"name": "canonicalFactory48", "text_bytes": 22898, "text_sha256": "28a1c56b63d345eaa3c3e803b19397a546730020d456ed2c29eb39aec3a5c820", "public_factory_name": "canonicalFactory48", "public_factory_is_canonical_identity": True}
EXPECTED_CLOSURE = (
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
)
EXPECTED_CLOSURE_SHA256 = "b16cbd8716cab226271041751af6431bfe48fef1c0826bba89544a0f4bf525f5"
EXPECTED_MUTATION_IDENTITIES = {
    "fallback-default": {"anchor_sha256": "8e35a9b15829e194b90777d8f38e5709ec2e1f8cfa875d4294496fade9f67683", "replacement_sha256": "8fb42fd196d8a5e5bff6ba3a7a1dd24a87fe4dfb2b0f07a75146dc5bdcd1251b", "mutated_factory_sha256": "85c2335ba2395a5d80f05fff460de3ddf5779b39524a927ee506618c36e0f611"},
    "quantize-levels": {"anchor_sha256": "4af10b05bcf97c256bedc908d8fc491d9a7d53b3bd16508493a436d742f602ac", "replacement_sha256": "aa8311a86e4e743a9c84375b905a6c66581039145887910832a63625c2ef4b34", "mutated_factory_sha256": "c48b59a286a1178abe723287b9ea9869600425609971827b37bb4b2d5b6ea007"},
    "error-diffusion-route": {"anchor_sha256": "4d67d8c234a20ad7a01c31093fd192a8a78821d5414d115bbc1dfbb209586e3f", "replacement_sha256": "a379b9b2de4ff3d9bbc89b6f64472ac79af6d39b89ae7604f2cf529752d32788", "mutated_factory_sha256": "3937d5b5265b810304261dae07e087890cec8fcf755da6a17d82146aa0432be3"},
}
EXPECTED_TRACE_POINTS = (
    ((0, 0), (-8.5, 2.5), (-5, 1), (-4, 0)),
    ((1, 0), (-7.5, 2.5), (-4, 1), (-4, 0)),
    ((5, 0), (-3.5, 2.5), (-2, 1), (0, 0)),
)
EXPECTED_CLAMP_WITNESS = {"fragment": [0, 0], "block_origin": [-4, 0], "loop_offset": [-4, -4], "cell": [-8, -4], "global": [-15, -7], "raw_local": [-6, -9], "clamped_local": [0, 0], "visited": True}
EXPECTED_LEVEL_EVIDENCE = {
    "levels-2-boundary": {"levels": 2, "zero": [0, 1, 4, 6, 13, 14, 17, 18, 21, 22, 28, 30, 32, 34, 36, 37, 41], "one": [2, 5, 8, 10, 12, 20, 24, 25, 38, 40, 44, 45, 46]},
    "levels-16-boundary": {"levels": 16, "zero": [2, 5, 33], "one": [8, 25]},
}


class MaterializationError(ValueError):
    pass


def _word_bytes(values: list[str]) -> bytes:
    return b"".join(struct.pack("<I", int(value, 16)) for value in values)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _assert_finite_words(values: list[str], label: str) -> None:
    if any(((int(value, 16) >> 23) & 0xFF) == 0xFF for value in values):
        raise MaterializationError(f"{label}: non-finite f32 lane")


def _assert_binding(case: dict, expected: tuple) -> None:
    (width, height, dither_type, palette, levels, threshold, matrix_scale,
     render_scale, mix_amount, time, tile, full) = expected
    actual = (case.get("width"), case.get("height"), case.get("ditherType"),
              case.get("palette"), case.get("levels"), case.get("threshold"),
              case.get("matrixScale"), case.get("renderScale"), case.get("mixAmount"),
              case.get("time"), tuple(case.get("tileOffset", ())), tuple(case.get("fullResolution", ())))
    if actual != (width, height, dither_type, palette, levels, threshold, matrix_scale,
                  render_scale, mix_amount, time, tile, full):
        raise MaterializationError(f"{case.get('name')}: binding drift")


def validate(document: dict) -> None:
    if document.get("schema") != "noisemaker-for-cpp.dither.pixel-parity.v1":
        raise MaterializationError("oracle schema mismatch")
    if document.get("program_key") != KEY:
        raise MaterializationError("program key mismatch")
    cases = document.get("render_cases")
    if not isinstance(cases, list) or tuple(case.get("name") for case in cases) != CASE_NAMES:
        raise MaterializationError("exact twelve-case order mismatch")
    if len({case.get("name") for case in cases}) != 12 or any(case.get("palette") != 0 for case in cases):
        raise MaterializationError("duplicate or non-input palette case")
    for case in cases:
        if case["name"] in EXPECTED_BINDINGS:
            _assert_binding(case, EXPECTED_BINDINGS[case["name"]])
        width, height = case.get("width"), case.get("height")
        if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
            raise MaterializationError("invalid dimensions")
        count = width * height * 4
        for label in ("input", "expected", "public_expected"):
            record = case.get(label)
            if not isinstance(record, dict) or len(record.get("f32_words_le", ())) != count:
                raise MaterializationError(f"{case.get('name')}: {label} lane cardinality")
            if len(record.get("rgba8_bytes", ())) != count:
                raise MaterializationError(f"{case.get('name')}: {label} RGBA8 cardinality")
            _assert_finite_words(record["f32_words_le"], f"{case.get('name')}: {label}")
            if _sha(_word_bytes(record["f32_words_le"])) != record.get("f32_sha256"):
                raise MaterializationError(f"{case.get('name')}: {label} f32 hash")
            if _sha(bytes(record["rgba8_bytes"])) != record.get("rgba8_sha256"):
                raise MaterializationError(f"{case.get('name')}: {label} RGBA8 hash")
        if not case.get("input_immutable_exact_bits") or not case.get("public_direct_exact"):
            raise MaterializationError(f"{case.get('name')}: parity claims are not authenticated")
        repeat = case.get("repeat", {})
        if set(repeat) != {"exact", "output_object_distinct", "output_data_distinct"} or not all(repeat.values()):
            raise MaterializationError(f"{case.get('name')}: repeat contract")
        if case.get("name") in EXPECTED_LEVEL_EVIDENCE:
            expected = EXPECTED_LEVEL_EVIDENCE[case["name"]]
            evidence = case.get("level_evidence", {})
            if (evidence.get("levels") != expected["levels"]
                    or evidence.get("rgb_endpoint_lanes") != {"zero": expected["zero"], "one": expected["one"]}
                    or evidence.get("highest_level_word") != "0x3f800000"
                    or evidence.get("highest_level_rgb_lanes") != expected["one"]):
                raise MaterializationError(f"{case['name']}: level endpoint evidence")
    traces = [case.get("signed_trace") for case in cases if case.get("signed_trace") is not None]
    if len(traces) != 1 or traces[0].get("source", {}).get("relative_path") != CORPUS_SOURCE:
        raise MaterializationError("signed trace cardinality/source")
    trace = traces[0]
    if (trace.get("source") != {"relative_path": CORPUS_SOURCE, "raw_sha256": CORPUS_SOURCE_SHA256, "block_span": "508-566", "fetch_span": "500-506"}
            or trace.get("signed_division") != "truncate_toward_zero"
            or trace.get("fs_block") != 4 or trace.get("cell_size") != 2):
        raise MaterializationError("signed trace source identity")
    if not trace.get("negative_global_coordinate") or not trace.get("negative_block_origin"):
        raise MaterializationError("signed trace lacks negative witness")
    actual_points = tuple((tuple(point.get("fragment", ())), tuple(point.get("global", ())), tuple(point.get("cell", ())), tuple(point.get("block_origin", ()))) for point in trace.get("points", ()))
    if actual_points != EXPECTED_TRACE_POINTS:
        raise MaterializationError("signed trace point identity")
    witness = trace.get("clamp_witness", {})
    if (any(witness.get(key) != value for key, value in EXPECTED_CLAMP_WITNESS.items())
            or not witness.get("clamped") or witness.get("raw_local") == witness.get("clamped_local")
            or not witness.get("visited")):
        raise MaterializationError("signed trace lacks clamp witness")
    policy = document.get("comparer_policy")
    if not isinstance(policy, dict) or set(policy) != EXPECTED_POLICY or not all(policy.values()):
        raise MaterializationError("comparer policy mismatch")
    if not isinstance(document.get("comparer_self_tests"), dict) or not all(document["comparer_self_tests"].values()):
        raise MaterializationError("comparer self-tests incomplete")
    provenance = document.get("provenance", {})
    if provenance.get("upstream_revision") != EXPECTED_UPSTREAM_REVISION:
        raise MaterializationError("upstream revision identity mismatch")
    source = provenance.get("corpus_source", {})
    if source.get("relative_path") != CORPUS_SOURCE or source.get("raw_sha256") != CORPUS_SOURCE_SHA256:
        raise MaterializationError("corpus source identity mismatch")
    if provenance.get("source") != EXPECTED_SOURCE:
        raise MaterializationError("canonical source identity mismatch")
    factory = provenance.get("factory", {})
    if any(factory.get(key) != value for key, value in EXPECTED_FACTORY.items()):
        raise MaterializationError("canonical factory identity mismatch")
    snapshot = provenance.get("cpu_snapshot", {})
    closure = snapshot.get("import_closure")
    if (not isinstance(closure, list) or tuple((item.get("relative_path"), item.get("sha256")) for item in closure) != EXPECTED_CLOSURE
            or any(Path(item.get("relative_path", "")).is_absolute() for item in closure)
            or any(".." in Path(item.get("relative_path", "")).parts for item in closure)
            or len({item.get("relative_path") for item in closure}) != 22
            or _sha(json.dumps(closure, separators=(",", ":")).encode()) != EXPECTED_CLOSURE_SHA256
            or snapshot.get("closure_sha256") != EXPECTED_CLOSURE_SHA256
            or snapshot.get("immutable_snapshot") is not True
            or snapshot.get("live_checkout_rejected") is not True
            or snapshot.get("realpath_containment_checked") is not True
            or snapshot.get("symlink_escape_rejected") is not True):
        raise MaterializationError("portable authority closure mismatch")
    mutations = document.get("mutation_ledger")
    if not isinstance(mutations, list) or tuple(item.get("name") for item in mutations) != MUTATION_NAMES:
        raise MaterializationError("exact mutation ledger order mismatch")
    for mutation in mutations:
        expected = EXPECTED_MUTATIONS[mutation["name"]]
        actual = tuple((item.get("case"), item.get("mismatched_lanes"), item.get("mismatched_bytes"))
                       for item in mutation.get("required_witness_results", ()))
        if actual != expected or tuple(mutation.get("required_witnesses", ())) != tuple(item[0] for item in expected):
            raise MaterializationError(f"{mutation['name']}: witness drift")
        witness_actual = tuple(
            (item.get("case"), item.get("mismatched_lanes"), item.get("mismatched_bytes"),
             item.get("first_mismatch", {}).get("lane_index"),
             item.get("first_mismatch", {}).get("reference"),
             item.get("first_mismatch", {}).get("candidate"),
             item.get("first_rgba8_mismatch", {}).get("byte_index"),
             item.get("first_rgba8_mismatch", {}).get("reference"),
             item.get("first_rgba8_mismatch", {}).get("candidate"))
            for item in mutation.get("required_witness_results", ()))
        if witness_actual != EXPECTED_MUTATION_WITNESSES[mutation["name"]]:
            raise MaterializationError(f"{mutation['name']}: first witness drift")
        if hashlib.sha256(mutation.get("source_anchor", "").encode()).hexdigest() != mutation.get("anchor_sha256"):
            raise MaterializationError(f"{mutation['name']}: anchor hash")
        if hashlib.sha256(mutation.get("replacement", "").encode()).hexdigest() != mutation.get("replacement_sha256"):
            raise MaterializationError(f"{mutation['name']}: replacement hash")
        if len(mutation.get("mutated_factory_sha256", "")) != 64 or not mutation.get("independent"):
            raise MaterializationError(f"{mutation['name']}: mutation identity")
        expected_identity = EXPECTED_MUTATION_IDENTITIES[mutation["name"]]
        if any(mutation.get(key) != value for key, value in expected_identity.items()):
            raise MaterializationError(f"{mutation['name']}: pinned mutation identity")
    blocker = document.get("negative_authority")
    if not isinstance(blocker, dict) or any(blocker.get(key) != value for key, value in EXPECTED_BLOCKER.items()):
        raise MaterializationError("negative authority blocker identity")
    for route in ("direct", "public"):
        if blocker.get(route, {}).get("throws") is not True or blocker[route].get("message") != EXPECTED_BLOCKER["error"]:
            raise MaterializationError("negative authority blocker execution")
    upstream = document.get("upstream_runtime_blockers")
    if not isinstance(upstream, list) or len(upstream) != 1 or any(upstream[0].get(key) != value for key, value in EXPECTED_BLOCKER.items()):
        raise MaterializationError("upstream blocker metadata")


def words(values: list[str]) -> str:
    return ", ".join(f"{value}u" for value in values)


def bytes_(values: list[int]) -> str:
    return ", ".join(str(value) for value in values)


def _cpp_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _cpp_float(value: float) -> str:
    number = float(value)
    if not math.isfinite(number):
        raise MaterializationError("non-finite float")
    text = repr(number)
    if "e" not in text and "E" not in text and "." not in text:
        text += ".0"
    return f"{text}f"


def _cpp_float_array(values) -> str:
    return "{" + ", ".join(_cpp_float(value) for value in values) + "}"


def _cpp_int_array(values) -> str:
    return "{" + ", ".join(f"{int(value)}" for value in values) + "}"


def materialize(document: dict) -> str:
    validate(document)
    lines = [
        "// Authenticated dither oracle; generated by generate_dither_native_oracle_include.py.",
        "#pragma once", "#include <array>", "#include <cstdint>", "#include <span>", "#include <string_view>",
        "namespace noisemaker_dither_oracle {",
        "struct Case { std::string_view name; std::uint32_t width, height, dither_type, palette, levels; float threshold, matrix_scale, render_scale, mix_amount, time; std::array<float, 2> tile_offset, full_resolution; std::uint32_t phase; std::span<const std::uint32_t> input_f32, expected_f32, public_f32; std::span<const std::uint8_t> input_rgba8, expected_rgba8, public_rgba8; };",
        "struct MutationResult { std::string_view case_name, reference_f32_word, candidate_f32_word; std::uint32_t mismatched_lanes, mismatched_bytes, first_f32_index, first_rgba8_index, reference_rgba8_byte, candidate_rgba8_byte; };",
        "struct Mutation { std::string_view name, anchor_sha256, replacement_sha256, mutated_factory_sha256; std::span<const MutationResult> results; };",
        "struct TracePoint { std::array<std::int32_t, 2> fragment; std::array<float, 2> global; std::array<std::int32_t, 2> cell, block_origin; };",
        "struct SignedTrace { std::string_view case_name, method, source_path, source_sha256, source_block_span, source_fetch_span, signed_division; std::int32_t fs_block; float cell_size; bool negative_global_coordinate, negative_block_origin; std::span<const TracePoint> points; std::array<std::int32_t, 2> clamp_fragment, clamp_block_origin, clamp_loop_offset, clamp_cell, clamp_raw_local, clamp_clamped; std::array<float, 2> clamp_global; bool clamp_witness, clamp_visited; };",
        "struct LevelEvidence { std::string_view case_name, highest_level_word; std::uint32_t levels; std::span<const std::uint32_t> zero_lanes, one_lanes, highest_level_rgb_lanes; };",
        "struct AuthorityBlocker { std::string_view route, error, source_anchor, case_name, direct_message, public_message; std::uint32_t palette; bool reproducible, direct_throws, public_throws; };",
        "struct ClosureEntry { std::string_view relative_path, sha256; };",
        "struct ComparerPolicy { bool f32_words_exact, rgba8_bytes_exact, dimensions_before_data, signed_zero_exact, input_bits_exact, public_direct_exact, repeat_identity_exact; };",
        "struct ComparerSelfTests { bool good_equal, dimensions_mismatch, short_lane_count, rgba8_mismatch, signed_zero; };",
    ]
    lines += [
        f"inline constexpr std::string_view kSchema = {_cpp_string(document['schema'])};",
        f"inline constexpr std::string_view kProgramKey = {_cpp_string(document['program_key'])};",
        f"inline constexpr std::string_view kAuthorityNode = {_cpp_string(document['provenance']['authority_node'])};",
        f"inline constexpr std::string_view kUpstreamRevision = {_cpp_string(document['provenance']['upstream_revision'])};",
        f"inline constexpr std::string_view kSourceRelativePath = {_cpp_string(document['provenance']['source']['relative_path'])};",
        f"inline constexpr std::string_view kSourceSha256 = {_cpp_string(document['provenance']['source']['sha256'])};",
        f"inline constexpr std::string_view kFactoryName = {_cpp_string(document['provenance']['factory']['name'])};",
        f"inline constexpr std::string_view kFactoryTextSha256 = {_cpp_string(document['provenance']['factory']['text_sha256'])};",
        f"inline constexpr std::string_view kPublicFactoryName = {_cpp_string(document['provenance']['factory']['public_factory_name'])};",
        f"inline constexpr bool kPublicFactoryIsCanonicalIdentity = {'true' if document['provenance']['factory']['public_factory_is_canonical_identity'] else 'false'};",
        f"inline constexpr std::string_view kCorpusSourceRelativePath = {_cpp_string(document['provenance']['corpus_source']['relative_path'])};",
        f"inline constexpr std::string_view kCorpusSourceSha256 = {_cpp_string(document['provenance']['corpus_source']['raw_sha256'])};",
        f"inline constexpr std::string_view kClosureSha256 = {_cpp_string(document['provenance']['cpu_snapshot']['closure_sha256'])};",
        f"inline constexpr bool kImmutableSnapshot = {'true' if document['provenance']['cpu_snapshot']['immutable_snapshot'] else 'false'};",
        f"inline constexpr bool kLiveCheckoutRejected = {'true' if document['provenance']['cpu_snapshot']['live_checkout_rejected'] else 'false'};",
        f"inline constexpr bool kRealpathContainmentChecked = {'true' if document['provenance']['cpu_snapshot']['realpath_containment_checked'] else 'false'};",
        f"inline constexpr bool kSymlinkEscapeRejected = {'true' if document['provenance']['cpu_snapshot']['symlink_escape_rejected'] else 'false'};",
        f"inline constexpr std::uint32_t kBaselineCaseCount = 9u;",
        f"inline constexpr std::uint32_t kAdversarialCaseCount = 3u;",
        "",
    ]
    case_names = []
    for index, case in enumerate(document["render_cases"]):
        suffix = str(index)
        case_names.append(case["name"])
        for label, key in (("input", "Input"), ("expected", "Expected"), ("public_expected", "Public")):
            record = case[label]
            lines.append(f"inline constexpr std::array<std::uint32_t, {len(record['f32_words_le'])}> k{key}F32{suffix} = {{{words(record['f32_words_le'])}}};")
            lines.append(f"inline constexpr std::array<std::uint8_t, {len(record['rgba8_bytes'])}> k{key}Rgba8{suffix} = {{{bytes_(record['rgba8_bytes'])}}};")
    lines.append(f"inline constexpr std::array<Case, {len(document['render_cases'])}> kCases = {{")
    for index, case in enumerate(document["render_cases"]):
        lines.append(f"  Case{{{_cpp_string(case['name'])}, {case['width']}u, {case['height']}u, {case['ditherType']}u, {case['palette']}u, {case['levels']}u, {_cpp_float(case['threshold'])}, {_cpp_float(case['matrixScale'])}, {_cpp_float(case['renderScale'])}, {_cpp_float(case['mixAmount'])}, {_cpp_float(case['time'])}, {_cpp_float_array(case['tileOffset'])}, {_cpp_float_array(case['fullResolution'])}, {case['phase']}u, kInputF32{index}, kExpectedF32{index}, kPublicF32{index}, kInputRgba8{index}, kExpectedRgba8{index}, kPublicRgba8{index}}},")
    lines.append("};")
    level_cases = [case for case in document["render_cases"] if case.get("level_evidence") is not None]
    for index, case in enumerate(level_cases):
        evidence = case["level_evidence"]
        zero = evidence["rgb_endpoint_lanes"]["zero"]
        one = evidence["rgb_endpoint_lanes"]["one"]
        lines.append(f"inline constexpr std::array<std::uint32_t, {len(zero)}> kLevelZeroLanes{index} = {{{bytes_(zero)}}};")
        lines.append(f"inline constexpr std::array<std::uint32_t, {len(one)}> kLevelOneLanes{index} = {{{bytes_(one)}}};")
        lines.append(f"inline constexpr std::array<std::uint32_t, {len(evidence['highest_level_rgb_lanes'])}> kLevelHighestLanes{index} = {{{bytes_(evidence['highest_level_rgb_lanes'])}}};")
    lines.append(f"inline constexpr std::array<LevelEvidence, {len(level_cases)}> kLevelEvidence = {{")
    for index, case in enumerate(level_cases):
        evidence = case["level_evidence"]
        lines.append(f"  LevelEvidence{{{_cpp_string(case['name'])}, {_cpp_string(evidence['highest_level_word'])}, {evidence['levels']}u, kLevelZeroLanes{index}, kLevelOneLanes{index}, kLevelHighestLanes{index}}},")
    lines.append("};")
    trace_cases = [(case, case["signed_trace"]) for case in document["render_cases"] if case.get("signed_trace") is not None]
    for index, (case, trace) in enumerate(trace_cases):
        lines.append(f"inline constexpr std::array<TracePoint, {len(trace['points'])}> kSignedTracePoints{index} = {{")
        for point in trace["points"]:
            lines.append(f"  TracePoint{{{_cpp_int_array(point['fragment'])}, {_cpp_float_array(point['global'])}, {_cpp_int_array(point['cell'])}, {_cpp_int_array(point['block_origin'])}}},")
        lines.append("};")
    lines.append(f"inline constexpr std::array<SignedTrace, {len(trace_cases)}> kSignedTraces = {{")
    for index, (case, trace) in enumerate(trace_cases):
        witness = trace["clamp_witness"]
        lines.append(f"  SignedTrace{{{_cpp_string(case['name'])}, {_cpp_string(trace['method'])}, {_cpp_string(trace['source']['relative_path'])}, {_cpp_string(trace['source']['raw_sha256'])}, {_cpp_string(trace['source']['block_span'])}, {_cpp_string(trace['source']['fetch_span'])}, {_cpp_string(trace['signed_division'])}, {trace['fs_block']}, {_cpp_float(trace['cell_size'])}, {'true' if trace['negative_global_coordinate'] else 'false'}, {'true' if trace['negative_block_origin'] else 'false'}, kSignedTracePoints{index}, {_cpp_int_array(witness['fragment'])}, {_cpp_int_array(witness['block_origin'])}, {_cpp_int_array(witness['loop_offset'])}, {_cpp_int_array(witness['cell'])}, {_cpp_int_array(witness['raw_local'])}, {_cpp_int_array(witness['clamped_local'])}, {_cpp_float_array(witness['global'])}, {'true' if witness['clamped'] else 'false'}, {'true' if witness['visited'] else 'false'}}},")
    lines.append("};")
    blocker = document["negative_authority"]
    lines.append(f"inline constexpr AuthorityBlocker kAuthorityBlocker{{{_cpp_string(blocker['route'])}, {_cpp_string(blocker['error'])}, {_cpp_string(blocker['source_anchor'])}, {_cpp_string(blocker['case_name'])}, {_cpp_string(blocker['direct']['message'])}, {_cpp_string(blocker['public']['message'])}, {blocker['palette']}u, {'true' if blocker['reproducible'] else 'false'}, {'true' if blocker['direct']['throws'] else 'false'}, {'true' if blocker['public']['throws'] else 'false'}}};")
    closure = document["provenance"]["cpu_snapshot"]["import_closure"]
    lines.append(f"inline constexpr std::array<ClosureEntry, {len(closure)}> kCpuClosure = {{")
    for entry in closure:
        lines.append(f"  ClosureEntry{{{_cpp_string(entry['relative_path'])}, {_cpp_string(entry['sha256'])}}},")
    lines.append("};")
    policy = document["comparer_policy"]
    lines.append(f"inline constexpr ComparerPolicy kComparerPolicy{{{', '.join('true' if policy[key] else 'false' for key in ('f32_words_exact', 'rgba8_bytes_exact', 'dimensions_before_data', 'signed_zero_exact', 'input_bits_exact', 'public_direct_exact', 'repeat_identity_exact'))}}};")
    self_tests = document["comparer_self_tests"]
    lines.append(f"inline constexpr ComparerSelfTests kComparerSelfTests{{{', '.join('true' if self_tests[key] else 'false' for key in ('good_equal', 'dimensions_mismatch', 'short_lane_count', 'rgba8_mismatch', 'signed_zero'))}}};")
    mutation_names = []
    for index, mutation in enumerate(document["mutation_ledger"]):
        mutation_names.append(mutation["name"])
        lines.append(f"inline constexpr std::array<MutationResult, {len(mutation['required_witness_results'])}> kMutationResults{index} = {{")
        for result in mutation["required_witness_results"]:
            first_f32 = result["first_mismatch"]
            first_rgba8 = result["first_rgba8_mismatch"]
            lines.append(f"  MutationResult{{\"{result['case']}\", {_cpp_string(first_f32['reference'])}, {_cpp_string(first_f32['candidate'])}, {result['mismatched_lanes']}u, {result['mismatched_bytes']}u, {first_f32['lane_index']}u, {first_rgba8['byte_index']}u, {first_rgba8['reference']}u, {first_rgba8['candidate']}u}},")
        lines.append("};")
    lines.append(f"inline constexpr std::array<Mutation, {len(mutation_names)}> kMutations = {{")
    for index, name in enumerate(mutation_names):
        mutation = document["mutation_ledger"][index]
        lines.append(f"  Mutation{{\"{name}\", {_cpp_string(mutation['anchor_sha256'])}, {_cpp_string(mutation['replacement_sha256'])}, {_cpp_string(mutation['mutated_factory_sha256'])}, kMutationResults{index}}},")
    lines += ["};", "}", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    document = json.loads(ORACLE.read_text(encoding="utf-8"))
    content = materialize(document)
    if args.check or args.self_test:
        if not OUT.is_file() or OUT.read_text(encoding="utf-8") != content:
            raise SystemExit("dither native oracle include drift")
        digest = hashlib.sha256(content.encode()).hexdigest()
        sidecar = OUT.with_name(OUT.name + ".sha256")
        if not sidecar.is_file() or sidecar.read_text(encoding="utf-8") != f"{digest}  {OUT.name}\n":
            raise SystemExit("dither native oracle include sidecar drift")
        if args.self_test:
            print("dither oracle validation and include materialization verified")
        else:
            print("dither native oracle include check passed")
        return 0
    OUT.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(content.encode()).hexdigest()
    OUT.with_name(OUT.name + ".sha256").write_text(f"{digest}  {OUT.name}\n", encoding="utf-8")
    print(f"{len(document['render_cases'])} cases, {len(document['mutation_ledger'])} mutations written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
