from __future__ import annotations

import dataclasses
import pathlib
import unittest

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.loop_proof import (
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
    attach_counted_loop_proofs, summarize_counted_loop_proofs)
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "synth/mandelbrot:mandelbrot"
LOG_PROFILE = "log-admission-mandelbrot-v1"
OUT_PROFILE = "out-inout-admission-mandelbrot-v1"
CROSS_LANE_PROFILE = "mandelbrot-sequential-dz-assignment-v1"
SOURCE = ROOT / (
    "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/"
    "sources/synth/mandelbrot/mandelbrot.glsl"
)
SOURCE_HASH = "0587dbc29f2dc8c186d7c47ebe6182e89dfe0387fc29a23826cac15499fba615"


def _program():
    source = SOURCE.read_text(encoding="utf-8")
    defaults = generate_typed_slice._defaults(ROOT, KEY)
    program = analyze_program(parse_program(source, KEY, defaults), KEY)
    max_iter = next(item for item in program.declarations
                    if item.symbol.name == "MAX_ITER")
    functions = attach_counted_loop_proofs(
        program.functions, KEY,
        source_global_bounds=((max_iter.symbol.id, 500,
                               "source-global-const-literal", max_iter.symbol),))
    return dataclasses.replace(
        program, functions=functions,
        counted_loop_proof=summarize_counted_loop_proofs(functions))


class MandelbrotEmitterLoweringTests(unittest.TestCase):
    def test_emits_authenticated_out_calls_logs_and_sequential_dz_lanes(self):
        rendered = emit_typed_cpp.render_typed_cpp(
            _program(), KEY, SOURCE_HASH,
            source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
            log_admission_profile=LOG_PROFILE,
            out_inout_admission_profile=OUT_PROFILE,
            mandelbrot_sequential_dz_assignment_profile=CROSS_LANE_PROFILE)

        # Ten exact out parameters are references; the five bare calls are
        # the only void-call expression statements admitted for this key.
        # All four scalar out values stay JS Numbers through the helper's
        # __out__ stash and output-mode arithmetic.
        self.assertEqual(0, rendered.count("float&"))
        self.assertEqual(8, rendered.count("double&"))
        # Count the authenticated out parameters by name; the shared texture
        # helper also has a const Vec2 reference and must not enter this ABI
        # census.
        self.assertEqual(2, rendered.count("glsl::Vec2& cX_df"))
        self.assertEqual(2, rendered.count("glsl::Vec2& cY_df"))
        self.assertIn("double& smoothIter", rendered)
        self.assertIn("double& rawIter", rendered)
        self.assertIn("double& stripeAcc", rendered)
        self.assertIn("double& trapMin", rendered)
        self.assertEqual(1, rendered.count("getPOI(state, context"))
        self.assertEqual(2, rendered.count("transformCoords_df64(state, context"))
        self.assertEqual(2, rendered.count("mandelbrot_df64(state, context"))
        self.assertIn("glsl::set_swizzle<0>(dz", rendered)
        self.assertIn("glsl::set_swizzle<1>(dz", rendered)
        self.assertNotIn("dz = glsl::Vec2", rendered)
        self.assertEqual(3, rendered.count("std::log("))

    def test_mandelbrot_lowering_requires_all_three_authenticated_profiles(self):
        program = _program()
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, SOURCE_HASH,
                source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
                log_admission_profile=LOG_PROFILE,
                out_inout_admission_profile=OUT_PROFILE)


if __name__ == "__main__":
    unittest.main()
