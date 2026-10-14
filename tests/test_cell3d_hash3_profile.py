from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import unittest

from tools.glslcpp import emit_typed_cpp
from tools.glslcpp.check_corpus import REVISION
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.cell3d_hash3_profile import (
    KEY, RAW_SHA256, authenticate_cell3d_hash3)
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine


SOURCE = (pathlib.Path(__file__).resolve().parents[1]
          / "tools/glslcpp/corpus" / REVISION
          / "sources/synth3d/cell3d/precompute.glsl")


def _program():
    raw = SOURCE.read_text(encoding="utf-8")
    return raw, analyze_program(parse_program(raw, KEY, {}), KEY)


class Cell3dHash3Tests(unittest.TestCase):
    def test_exact_nodes_and_emission(self):
        raw, program = _program()
        self.assertEqual(RAW_SHA256, hashlib.sha256(raw.encode()).hexdigest())
        proof = authenticate_cell3d_hash3(program, RAW_SHA256)
        self.assertEqual((34, 35), (proof.seed_cast.span.start_line,
                                    proof.q_constructor.span.start_line))
        emitted = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256, "cell3d_test", "bind_cell3d_test")
        self.assertIn("double seed;", emitted)
        self.assertIn('bindings.get_number("seed")', emitted)
        self.assertIn("glsl::detail::js_to_int32(scaled[0])", emitted)
        self.assertIn("glsl::Vec3((p * static_cast<float>(1000.0)))", emitted)
        self.assertNotIn("float(state.seed)", emitted)

    def test_caller_source_and_define_forgery(self):
        _, program = _program()
        for forged, caller_hash in (
                (program, "0" * 64),
                (dataclasses.replace(program, raw_source=program.raw_source + "\n"),
                 RAW_SHA256),
                (dataclasses.replace(program, preprocessor_defines=(
                    PreprocessorDefine("FAKE", "int", "1"),)), RAW_SHA256)):
            with self.subTest(caller_hash=caller_hash,
                              defines=forged.preprocessor_defines):
                with self.assertRaisesRegex(ValueError, "identity mismatch"):
                    authenticate_cell3d_hash3(forged, caller_hash)

    def test_typed_tree_forgery(self):
        _, program = _program()
        functions = list(program.functions)
        index = next(i for i, item in enumerate(functions)
                     if item.name == "hash3")
        owner = functions[index]
        body = list(owner.body)
        q = body[1].expressions[0]
        body[1] = dataclasses.replace(body[1], expressions=(
            dataclasses.replace(q, symbol_id=0),))
        functions[index] = dataclasses.replace(owner, body=tuple(body))
        forged = dataclasses.replace(program, functions=tuple(functions))
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            authenticate_cell3d_hash3(forged, RAW_SHA256)


if __name__ == "__main__":
    unittest.main()
