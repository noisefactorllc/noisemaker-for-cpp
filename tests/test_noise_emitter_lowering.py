from __future__ import annotations

import pathlib
import unittest

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.mutable_global_frame_profile import NOISE_PROFILE
from tools.glslcpp.frontend.runtime_loop_bound_profile import (
    PROFILE as RUNTIME_PROFILE,
    apply_runtime_loop_bound,
)
from tools.glslcpp.frontend.scalar_uint_xor_profile import (
    PROFILE as SCALAR_XOR_PROFILE,
    authenticate_noise_float_bits_ingress,
    authenticate_scalar_uint_xor,
)
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "synth/noise:noise"
SOURCE = ROOT / (
    "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/"
    "sources/synth/noise/noise.glsl"
)
SOURCE_HASH = "410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274"


def _program():
    raw = SOURCE.read_text(encoding="utf-8")
    program = analyze_program(
        parse_program(raw, KEY, generate_typed_slice._defaults(ROOT, KEY)),
        KEY,
    )
    program = apply_runtime_loop_bound(program, SOURCE_HASH, RUNTIME_PROFILE)
    authenticate_scalar_uint_xor(program, SOURCE_HASH, SCALAR_XOR_PROFILE)
    return program


class NoiseEmitterLoweringTests(unittest.TestCase):
    def test_emits_authenticated_noise_carriers_and_number_float_uint_sites(self):
        program = _program()
        xor_sites = authenticate_scalar_uint_xor(
            program, SOURCE_HASH, SCALAR_XOR_PROFILE)
        self.assertEqual(3, len(xor_sites))
        self.assertEqual({97, 98, 99},
                         {site.span.start_line for site in xor_sites})
        self.assertTrue(all(site.span.program_key == KEY for site in xor_sites))
        ingress = authenticate_noise_float_bits_ingress(
            program, SOURCE_HASH, SCALAR_XOR_PROFILE)
        self.assertEqual(1, len(ingress))
        rendered = emit_typed_cpp.render_typed_cpp(
            program,
            KEY,
            SOURCE_HASH,
            runtime_loop_bound_profile=RUNTIME_PROFILE,
            scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
            mutable_global_frame_profile=NOISE_PROFILE,
        )
        self.assertIn("struct Frame final", rendered)
        self.assertIn("glsl::Vec2 globalCoord{}", rendered)
        self.assertIn("const Frame& frame", rendered)
        self.assertIn("std::uint32_t fracBits", rendered)
        self.assertIn("noisemaker::float_bits_to_uint", rendered)
        # All three authenticated scalar float(uint) constructors retain the
        # canonical f32 boundary; the surrounding scalar expression is then
        # promoted to the emitter's Number-compatible double local.
        self.assertEqual(1, rendered.count("float(glsl::swizzle<0>(prngState))"))
        self.assertEqual(1, rendered.count("float(std::uint32_t(4294967295))"))
        self.assertEqual(1, rendered.count(
            "float(std::uint32_t(std::int32_t(-1)))"))
        self.assertIn("octaves must be in [1,8]", rendered)

    def test_noise_carriers_reject_foreign_or_missing_profiles(self):
        program = _program()
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                program,
                KEY,
                SOURCE_HASH,
                runtime_loop_bound_profile=RUNTIME_PROFILE,
                scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                mutable_global_frame_profile="mutable-global-frame-shape-v1",
            )
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                program,
                KEY,
                SOURCE_HASH,
                runtime_loop_bound_profile=RUNTIME_PROFILE,
                scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
            )


if __name__ == "__main__":
    unittest.main()
