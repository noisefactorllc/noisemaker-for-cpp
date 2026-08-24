from __future__ import annotations

import hashlib
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.generate_kernels import GeneratorError

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources"
KEY = "filter/median:median"
PROFILE = "median-frontend-admission-v1"


def _typed(radius: int = 2):
    source = (CORPUS / "filter/median/median.glsl").read_text()
    return analyze_program(parse_program(source, KEY, {"RADIUS": radius}), KEY)


class MedianGeneratorEmitterTests(unittest.TestCase):
    def test_row_is_exactly_landed_as_204(self):
        spec = generate_typed_slice.load_slice(ROOT)
        self.assertEqual(211, len(spec["programs"]))
        row = next(item for item in spec["programs"] if item["program_key"] == KEY)
        self.assertEqual({"defines": {"RADIUS": 2}, "program_key": KEY,
                          "median_frontend_profile": PROFILE}, row)

    def test_validate_requires_exact_profile_and_source_bound_proof(self):
        typed = _typed()
        source_hash = hashlib.sha256(typed.raw_source.encode()).hexdigest()
        kwargs = {"median_frontend_profile": PROFILE}
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, **kwargs)
        with self.assertRaises(GeneratorError):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaises(GeneratorError):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                median_frontend_profile="foreign-profile")

    def test_emitter_requires_profile_and_emits_authenticated_radius_state(self):
        typed = _typed()
        source_hash = hashlib.sha256(typed.raw_source.encode()).hexdigest()
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(typed, KEY, source_hash)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(typed, KEY, source_hash,
                             median_frontend_profile="foreign-profile")
        emitted = render_typed_cpp(
            typed, KEY, source_hash, median_frontend_profile=PROFILE)
        self.assertIn("std::int32_t RADIUS", emitted)
        self.assertIn("state.median_radius", emitted)
        self.assertIn("RADIUS", emitted)
        self.assertIn("texelFetch", emitted)
        self.assertEqual(
            2, emitted.count("glsl::pack_half2x16(glsl::Vec2("))
        self.assertEqual(2, emitted.count("glsl::unpack_half2x16("))


if __name__ == "__main__":
    unittest.main()
