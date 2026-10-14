"""Authenticate Perlin runtime dimensions and its CPU integer conversion."""
from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import perlin_scalar_uint_xor_profile as profile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d/sources/synth/perlin/perlin.glsl'


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
            source_hash=self.sha, perlin_scalar_uint_xor_profile=profile.PROFILE)
        emitted = emit_typed_cpp.render_typed_cpp(
            self.program, profile.PERLIN_KEY, self.sha, 'perlin_test', 'bind_perlin_test',
            perlin_scalar_uint_xor_profile=profile.PROFILE)
        self.assertIn('glsl::IVec3(glsl::Vec3((p * static_cast<float>(1000.0))))', emitted)
