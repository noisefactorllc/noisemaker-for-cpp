"""Exact default and dynamic Synth Shape source-admission checks."""

from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source
from tools.glslcpp.frontend.mutable_global_frame_profile import (
    authenticate_mutable_global_frame, frame_contract)
from tools.glslcpp.frontend.shape_positive_modulo_profile import (
    authenticate_shape_positive_modulo)
from tools.glslcpp.frontend.scalar_uint_xor_profile import (
    authenticate_scalar_uint_to_float_narrowing_skips,
    authenticate_scalar_uint_xor)
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = Path(__file__).resolve().parents[1]
KEY = "synth/shape:shape"
SOURCE = (ROOT / "tools/glslcpp/corpus/"
          "6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d/"
          "sources/synth/shape/shape.glsl")
FRAME = "mutable-global-frame-shape-v1"
XOR = "scalar-uint-xor-v1"


class ShapeRuntimeProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SOURCE.read_text()
        cls.sha = hashlib.sha256(cls.raw.encode()).hexdigest()
        cls.programs = {}
        for name, defines in (
                ("default", {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30}),
                ("dynamic", {"LOOP_A_OFFSET": "int", "LOOP_B_OFFSET": "int"})):
            parsed = parse_program(transform_source(cls.raw, KEY), KEY, defines)
            parsed["raw_source"] = cls.raw
            cls.programs[name] = analyze_program(parsed, KEY)

    def test_default_profile_is_preserved(self):
        program = self.programs["default"]
        self.assertEqual((14, 15), tuple(field.symbol_id
                         for field in frame_contract(program).fields))
        self.assertEqual(2, len(authenticate_mutable_global_frame(program, self.sha, FRAME)))
        self.assertEqual(3, len(authenticate_scalar_uint_xor(program, self.sha, XOR)))
        self.assertEqual(0, len(authenticate_scalar_uint_to_float_narrowing_skips(
            program, self.sha, XOR)))

    def test_dynamic_profile_and_production_emission(self):
        program = self.programs["dynamic"]
        self.assertEqual((16, 17), tuple(field.symbol_id
                         for field in frame_contract(program).fields))
        self.assertEqual(2, len(authenticate_mutable_global_frame(program, self.sha, FRAME)))
        self.assertEqual(3, len(authenticate_scalar_uint_xor(program, self.sha, XOR)))
        self.assertEqual(0, len(authenticate_scalar_uint_to_float_narrowing_skips(
            program, self.sha, XOR)))
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES, source_hash=self.sha,
            scalar_uint_xor_profile=XOR, mutable_global_frame_profile=FRAME)
        emitted = emit_typed_cpp.render_typed_cpp(
            program, KEY, self.sha, "shape_runtime_test", "bind_shape_runtime_test",
            scalar_uint_xor_profile=XOR, mutable_global_frame_profile=FRAME)
        self.assertIn("struct Frame", emitted)
        self.assertIn("bind_shape_runtime_test", emitted)
        self.assertIn(
            "double result = static_cast<double>(a) - "
            "(static_cast<double>(a) / static_cast<double>(b))", emitted)
        self.assertNotIn("std::int32_t result = (a - ((a / b) * b));", emitted)

    def test_positive_modulo_source_and_tree_forgery_rejected(self):
        program = self.programs["dynamic"]
        self.assertEqual("positiveModulo",
                         authenticate_shape_positive_modulo(program, self.sha).name)
        self.assertIsNone(authenticate_shape_positive_modulo(
            self.programs["default"], self.sha))
        for label, mutant, source_hash in (
                ("raw", replace(program, raw_source=self.raw + "\n"), self.sha),
                ("source", replace(program, source=program.source + "\n"), self.sha),
                ("functions", replace(program, functions=program.functions[:-1]),
                 self.sha),
                ("hash", program, "0" * 64)):
            with self.subTest(label=label), self.assertRaises(ValueError):
                authenticate_shape_positive_modulo(mutant, source_hash)

    def test_exact_runtime_row_and_negative_candidates(self):
        row = next(item for item in generate_typed_slice.load_slice(ROOT)["programs"]
                   if item["program_key"] == KEY)
        self.assertEqual("runtime-defines-generic-v1", row["runtime_define_profile"])
        program = self.programs["dynamic"]
        mutants = (
            replace(program, key="synth/foreign:shape"),
            replace(program, raw_source=self.raw + "\n"),
            replace(program, source=program.source + "\n"),
            replace(program, functions=program.functions[:-1]),
            replace(program, preprocessor_defines=()),
            replace(program, fixed_nine_table_proof=object()),
        )
        for mutant in mutants:
            with self.subTest(mutant=mutant.key):
                with self.assertRaises(ValueError):
                    authenticate_mutable_global_frame(mutant, self.sha, FRAME)
                with self.assertRaises(ValueError):
                    authenticate_scalar_uint_xor(mutant, self.sha, XOR)
        for authenticate, profile in (
                (authenticate_mutable_global_frame, FRAME),
                (authenticate_scalar_uint_xor, XOR)):
            with self.assertRaises(ValueError):
                authenticate(program, "0" * 64, profile)
            with self.assertRaises(ValueError):
                authenticate(program, self.sha, "foreign-profile")


if __name__ == "__main__":
    unittest.main()
