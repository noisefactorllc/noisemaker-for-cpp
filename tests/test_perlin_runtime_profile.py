"""Authenticate Perlin runtime dimensions and its CPU integer conversion."""
from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import perlin_scalar_uint_xor_profile as profile
from tools.glslcpp.frontend.prng_boolean_mix_select_profile import PROFILE as PRNG_PROFILE

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / f'tools/glslcpp/corpus/{CORPUS_REVISION}/sources/synth/perlin/perlin.glsl'


class PerlinRuntimeProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SOURCE.read_text()
        cls.sha = hashlib.sha256(cls.raw.encode()).hexdigest()
        cls.program = analyze_program(parse_program(cls.raw, profile.PERLIN_KEY,
                                                   {'DIMENSIONS': 'int'}), profile.PERLIN_KEY)

    def test_default_and_runtime_proofs(self):
        default = analyze_program(parse_program(self.raw, profile.PERLIN_KEY,
                                                {'DIMENSIONS': 2}), profile.PERLIN_KEY)
        for program in (default, self.program):
            self.assertEqual(len(profile.authenticate_perlin_scalar_uint_xor(
                program, self.sha, profile.PROFILE)), 2)

    def test_runtime_proof_rejects_forgery(self):
        for mutant in (replace(self.program, key='foreign:perlin'),
                       replace(self.program, raw_source=self.raw + '\n'),
                       replace(self.program, source=self.program.source + '\n'),
                       replace(self.program, functions=self.program.functions[:-1]),
                       replace(self.program, preprocessor_defines=()),
                       replace(self.program, fixed_nine_table_proof=object())):
            with self.subTest(mutant=mutant.key), self.assertRaises(ValueError):
                profile.authenticate_perlin_scalar_uint_xor(mutant, self.sha, profile.PROFILE)
        with self.assertRaises(ValueError):
            profile.authenticate_perlin_scalar_uint_xor(self.program, '0' * 64, profile.PROFILE)

    def test_production_emission_stores_float_vector_before_integer_conversion(self):
        generate_typed_slice.validate_capabilities(
            self.program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=self.sha, perlin_scalar_uint_xor_profile=profile.PROFILE,
            prng_boolean_mix_select_profile=PRNG_PROFILE)
        emitted = emit_typed_cpp.render_typed_cpp(
            self.program, profile.PERLIN_KEY, self.sha, 'perlin_test', 'bind_perlin_test',
            perlin_scalar_uint_xor_profile=profile.PROFILE,
            prng_boolean_mix_select_profile=PRNG_PROFILE)
        self.assertIn('glsl::IVec3(glsl::Vec3((p * static_cast<float>(1000.0))))', emitted)
        self.assertIn("glsl::Vec3(glsl::greaterThanEqual(", emitted)
        self.assertIn("glsl::Vec3 p, [[maybe_unused]] glsl::Vec3 k) noexcept", emitted)
        self.assertIn("static_cast<double>(k[0]) + static_cast<double>(noisemaker::f32", emitted)

    def test_historical_default_and_runtime_proofs_remain_authenticated(self):
        raw = (ROOT / 'tools/glslcpp/corpus/32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3/sources/synth/perlin/perlin.glsl').read_text()
        digest = hashlib.sha256(raw.encode()).hexdigest()
        for dimensions in (2, 'int'):
            program = analyze_program(parse_program(raw, profile.PERLIN_KEY,
                                                     {'DIMENSIONS': dimensions}), profile.PERLIN_KEY)
            self.assertEqual(len(profile.authenticate_perlin_scalar_uint_xor(
                program, digest, profile.PROFILE)), 2)
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=digest, perlin_scalar_uint_xor_profile=profile.PROFILE)
            if dimensions == "int":
                emitted = emit_typed_cpp.render_typed_cpp(
                    program, profile.PERLIN_KEY, digest,
                    perlin_scalar_uint_xor_profile=profile.PROFILE)
                self.assertIn("glsl::Vec3 p, [[maybe_unused]] glsl::Vec3 k) noexcept", emitted)
                self.assertIn("static_cast<double>(k[0]) + static_cast<double>(noisemaker::f32", emitted)
