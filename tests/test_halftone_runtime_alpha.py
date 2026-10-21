import dataclasses
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import render_typed_cpp, TypedEmissionError
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.derivative_admission_profile import (
    authenticate_derivative_admission)
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source
from tools.glslcpp.frontend.semantic import analyze_program


KEY = "filter/halftone:halftone"
SOURCE = (Path(__file__).resolve().parents[1] /
          f"tools/glslcpp/corpus/{CORPUS_REVISION}/"
          "sources/filter/halftone/halftone.glsl")
HASH = "063ddb13f5fffc6f957d4be0a60b0408ff706d6111fd4e3ba52582f7507c7ad7"


def dynamic_program():
    raw = SOURCE.read_text()
    parsed = parse_program(transform_source(raw, KEY), KEY,
                           {"MODE": "int", "PATTERN": "int"})
    parsed["raw_source"] = raw
    return analyze_program(parsed, KEY)


class HalftoneRuntimeAlphaTests(unittest.TestCase):
    def test_runtime_derivative_proof_accepts_only_exact_tree(self):
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), HASH)
        self.assertEqual(generate_typed_slice.GENERIC_DYNAMIC_DEFINE_TYPES[KEY],
                         {"MODE": "int", "PATTERN": "int"})
        program = dynamic_program()
        proof = authenticate_derivative_admission(program, HASH,
                                                   "derivative-admission-v1")
        self.assertEqual(tuple(node.callee for node in proof.nodes),
                         ("fwidth", "fwidth"))
        for candidate, digest in ((program, "0" * 64),
                                  (dataclasses.replace(program, functions=()), HASH),
                                  (dataclasses.replace(program,
                                                       raw_source=program.raw_source + "\n"), HASH)):
            with self.subTest(digest=digest):
                with self.assertRaises(ValueError):
                    authenticate_derivative_admission(
                        candidate, digest, "derivative-admission-v1")

    def test_exact_mono_output_keeps_optional_color_alpha(self):
        program = dynamic_program()
        cpp = render_typed_cpp(program, KEY, HASH,
                               "typed_halftone_test", "bind_halftone_test",
                               derivative_admission_profile="derivative-admission-v1")
        self.assertEqual(cpp.count("__cpuColorHasAlpha_inkColor"), 1)
        self.assertEqual(cpp.count("__cpuColorAlpha_paperColor"), 1)
        self.assertIn("if (state.inkColorHasAlpha)", cpp)
        self.assertIn("if (state.paperColorHasAlpha)", cpp)
        self.assertIn("cpuAlpha = std::numeric_limits<float>::quiet_NaN()", cpp)
        self.assertIn("glsl::Vec3(state.inkColor), glsl::Vec3(state.paperColor)), cpuAlpha)", cpp)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(dataclasses.replace(program, raw_source=program.raw_source + "\n"),
                             KEY, HASH, derivative_admission_profile="derivative-admission-v1")

    def test_frozen_default_program_still_emits(self):
        raw = SOURCE.read_text()
        program = analyze_program(parse_program(raw, KEY, {"MODE": 0, "PATTERN": 0}), KEY)
        cpp = render_typed_cpp(program, KEY, HASH,
                               "typed_halftone_default", "bind_halftone_default",
                               derivative_admission_profile="derivative-admission-v1")
        self.assertNotIn("__cpuColorHasAlpha_inkColor", cpp)
        self.assertIn("bind_halftone_default", cpp)


if __name__ == "__main__":
    unittest.main()
