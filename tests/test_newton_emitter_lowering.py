from __future__ import annotations

import dataclasses
import pathlib
import unittest

from tools.glslcpp import generate_typed_slice
from tools.glslcpp import emit_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "synth/newton:newton"
STRUCT_PROFILE = "struct-declaration-newton-v1"
OUT_PROFILE = "out-inout-admission-newton-v1"
SOURCE = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/newton/newton.glsl"
SOURCE_HASH = "603090e299ccb08fd4db4bf54a2aa6668ed81be971a84a8b679c7f560e5c27ac"


def _program():
    source = SOURCE.read_text(encoding="utf-8")
    defaults = generate_typed_slice._defaults(ROOT, KEY)
    return analyze_program(parse_program(source, KEY, defaults), KEY)


class NewtonEmitterLoweringTests(unittest.TestCase):
    def test_emits_authenticated_struct_array_out_and_log_lanes(self):
        rendered = emit_typed_cpp.render_typed_cpp(
            _program(), KEY, SOURCE_HASH,
            struct_declaration_profile=STRUCT_PROFILE,
            out_inout_admission_profile=OUT_PROFILE)
        self.assertIn("struct POIData final", rendered)
        self.assertIn("glsl::Vec4 center;", rendered)
        self.assertIn("double deg;", rendered)
        self.assertIn("double maxZoom;", rendered)
        self.assertEqual(7, rendered.count("return POIData{"))
        self.assertIn("std::array<glsl::Vec2, 8> roots{};", rendered)
        self.assertIn("glsl::Vec2& rr", rendered)
        self.assertIn("glsl::Vec2& ri", rendered)
        self.assertEqual(2, rendered.count("std::log("))
        self.assertEqual(1, rendered.count("std::log2("))
        self.assertIn("7.771800092370995e-09", rendered)

    def test_struct_and_root_mutations_fail_closed(self):
        program = _program()
        struct = program.structs[0]
        forged_struct = dataclasses.replace(struct, name="ForeignPOIData")
        forged = dataclasses.replace(program, structs=(forged_struct,))
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                forged, KEY, SOURCE_HASH,
                struct_declaration_profile=STRUCT_PROFILE,
                out_inout_admission_profile=OUT_PROFILE)


if __name__ == "__main__":
    unittest.main()
