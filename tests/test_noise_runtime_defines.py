from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import unittest
from unittest import mock

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.noise_runtime_define_profile import (
    DYNAMIC_DEFINES,
    KEY as NOISE_KEY,
    LOOP_OFFSET_CHOICES,
    NOISE_TYPE_CHOICES,
    PROFILE,
    authenticate_scalar_xor,
    transform_source,
)
from tools.glslcpp.frontend.runtime_loop_bound_profile import apply_runtime_loop_bound


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = next((ROOT / "tools" / "glslcpp" / "corpus").glob("*/"))
SOURCE = (CORPUS / "sources/synth/noise/noise.glsl").read_text()
KEY = NOISE_KEY


def _dynamic_program(*, raw_source: str = SOURCE,
                     transformed_source: str | None = None):
    parsed = parse_program(
        transformed_source or transform_source(SOURCE, KEY),
        KEY,
        DYNAMIC_DEFINES)
    parsed["raw_source"] = raw_source
    return analyze_program(parsed, KEY)


def _load_mutated_slice(mutator) -> None:
    document = json.loads(
        (ROOT / "tools/glslcpp/typed_slice.json").read_text())
    mutator(document)
    slice_path = (ROOT / "tools/glslcpp/typed_slice.json").resolve()
    original_read_text = pathlib.Path.read_text

    def read_text(path, *args, **kwargs):
        if path.resolve() == slice_path:
            return json.dumps(document)
        return original_read_text(path, *args, **kwargs)

    with mock.patch.object(pathlib.Path, "read_text", new=read_text):
        generate_typed_slice.load_slice(ROOT)


class NoiseRuntimeDefineTests(unittest.TestCase):
    def test_noise_row_rejects_wrong_runtime_define_profile(self) -> None:
        def mutate(document) -> None:
            row = next(item for item in document["programs"]
                       if item["program_key"] == KEY)
            row["runtime_define_profile"] = "runtime-defines-noise-v2"

        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "exact runtime-define profile"):
            _load_mutated_slice(mutate)

    def test_noise_row_rejects_missing_runtime_define_profile(self) -> None:
        def mutate(document) -> None:
            row = next(item for item in document["programs"]
                       if item["program_key"] == KEY)
            del row["runtime_define_profile"]

        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "exact runtime-define profile"):
            _load_mutated_slice(mutate)

    def test_runtime_define_profile_is_rejected_on_foreign_row(self) -> None:
        def mutate(document) -> None:
            row = next(item for item in document["programs"]
                       if item["program_key"] != KEY)
            row["runtime_define_profile"] = PROFILE

        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "runtime-define profile on foreign key"):
            _load_mutated_slice(mutate)

    def test_transform_is_source_bound_and_preserves_line_count(self) -> None:
        transformed = transform_source(SOURCE, KEY)
        self.assertEqual(len(SOURCE.splitlines()), len(transformed.splitlines()))
        self.assertIn("vec2 lf = vec2(1.0); float base = 0.0;", transformed)
        self.assertNotIn("float base = map", transformed)
        self.assertEqual(
            "410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274",
            hashlib.sha256(SOURCE.encode()).hexdigest())

    def test_dynamic_noise_program_analyzes_with_define_bindings(self) -> None:
        transformed = transform_source(SOURCE, KEY)
        parsed = parse_program(transformed, KEY, DYNAMIC_DEFINES)
        parsed["raw_source"] = SOURCE
        program = analyze_program(parsed, KEY)
        self.assertEqual(
            ("NOISE_TYPE", "LOOP_OFFSET", "time", "seed", "resolution",
             "tileOffset", "fullResolution", "scaleX", "scaleY", "octaves",
             "ridges", "loopScale", "speed", "colorMode", "wrap"),
            program.resources.uniforms)
        self.assertEqual(
            (("LOOP_OFFSET", "str", "int"), ("NOISE_TYPE", "str", "int")),
            tuple((item.name, item.kind, item.canonical_value)
                  for item in program.preprocessor_defines))

    def test_dynamic_path_rejects_transformed_source_drift(self) -> None:
        drifted = transform_source(SOURCE, KEY).replace(
            "float base = 0.0", "float base = 1.0", 1)
        program = _dynamic_program(transformed_source=drifted)
        with self.assertRaisesRegex(ValueError, "source or interface"):
            apply_runtime_loop_bound(
                program, hashlib.sha256(SOURCE.encode()).hexdigest(),
                "runtime-loop-bound-v1")

    def test_dynamic_path_rejects_raw_source_mismatch(self) -> None:
        program = _dynamic_program(raw_source=SOURCE + " ")
        with self.assertRaisesRegex(ValueError, "source or interface"):
            apply_runtime_loop_bound(
                program, hashlib.sha256(SOURCE.encode()).hexdigest(),
                "runtime-loop-bound-v1")

    def test_dynamic_path_rejects_post_runtime_typed_tree_mutation(self) -> None:
        source_hash = hashlib.sha256(SOURCE.encode()).hexdigest()
        program = apply_runtime_loop_bound(
            _dynamic_program(), source_hash, "runtime-loop-bound-v1")
        mutated = dataclasses.replace(
            program, functions=tuple(reversed(program.functions)))
        with self.assertRaisesRegex(ValueError, "typed tree fingerprint"):
            authenticate_scalar_xor(
                mutated, source_hash, "scalar-uint-xor-v1")

    def test_metadata_domains_are_exactly_authoritative_choices(self) -> None:
        metadata = json.loads((CORPUS / "metadata.json").read_text())
        params = metadata["effects"]["synth/noise"]["params"]
        self.assertEqual(
            frozenset(value for value in params["type"]["choices"].values()
                      if value is not None),
            NOISE_TYPE_CHOICES)
        self.assertEqual(
            frozenset(value for value in params["loopOffset"]["choices"].values()
                      if value is not None),
            LOOP_OFFSET_CHOICES)

    def test_emitter_binds_both_defines_as_unrestricted_int32_uniforms(self) -> None:
        transformed = transform_source(SOURCE, KEY)
        parsed = parse_program(transformed, KEY, DYNAMIC_DEFINES)
        parsed["raw_source"] = SOURCE
        program = analyze_program(parsed, KEY)
        source_hash = hashlib.sha256(SOURCE.encode()).hexdigest()
        program = apply_runtime_loop_bound(
            program, source_hash, "runtime-loop-bound-v1")
        rendered = render_typed_cpp(
            program, KEY, source_hash,
            runtime_loop_bound_profile="runtime-loop-bound-v1",
            scalar_uint_xor_profile="scalar-uint-xor-v1",
            mutable_global_frame_profile="mutable-global-frame-noise-v1")
        self.assertIn('bindings.get<std::int32_t>("NOISE_TYPE")', rendered)
        self.assertIn('bindings.get<std::int32_t>("LOOP_OFFSET")', rendered)
        self.assertIn('bindings.get<std::int32_t>("seed")', rendered)
        self.assertNotIn("must be one of", rendered)


if __name__ == "__main__":
    unittest.main()
