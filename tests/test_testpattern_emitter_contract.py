from __future__ import annotations

import hashlib
import pathlib
import unittest

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp import emit_typed_cpp


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
KEY = "synth/testPattern:testPattern"
SOURCE = CORPUS / "sources/synth/testPattern/testPattern.glsl"


def _program():
    raw = SOURCE.read_text(encoding="utf-8")
    defines = generate_typed_slice._defaults(ROOT, KEY)
    return analyze_program(parse_program(raw, KEY, defines), KEY)


class TestPatternEmitterLoweringTests(unittest.TestCase):
    def test_profile_emits_only_authenticated_arrays_indexes_and_round(self):
        from tools.glslcpp.frontend import testpattern_profile

        program = _program()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        proof = testpattern_profile.authenticate_testpattern_frontend(
            program, source_hash, testpattern_profile.PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash,
            testpattern_profile=testpattern_profile.PROFILE,
            testpattern_frontend_proof=proof)

        self.assertIn(
            "const std::array<std::int32_t, 10> GLYPH = "
            "std::array<std::int32_t, 10>{{",
            rendered)
        self.assertIn(
            "std::array<std::int32_t, 3> digits{};", rendered)
        self.assertIn(
            "std::array<glsl::Vec3, 8> colors = "
            "std::array<glsl::Vec3, 8>{{", rendered)
        self.assertEqual(rendered.count("static_cast<std::size_t>("), 4)
        self.assertIn("glsl::detail::js_shift_right(", rendered)
        self.assertIn("glsl::detail::js_bitwise_and(", rendered)
        self.assertIn(
            "glsl::Vec2(noisemaker::f32(glsl::round(glsl::swizzle<0>(",
            rendered)
        self.assertIn(
            "noisemaker::f32(glsl::round(glsl::swizzle<1>(", rendered)

    def test_profile_is_required_for_testpattern_and_rejects_missing_carrier(self):
        program = _program()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(program, KEY, source_hash)


if __name__ == "__main__":
    unittest.main()
