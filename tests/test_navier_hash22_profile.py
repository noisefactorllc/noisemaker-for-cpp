"""Exact CPU9f3 Navier-Stokes hash22 lane-order regression."""

from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION
from tools.glslcpp import emit_typed_cpp
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine
from tools.glslcpp.frontend.navier_hash22_sequential_profile import (
    KEY, authenticate_navier_hash22)

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / f"tools/glslcpp/corpus/{REVISION}/sources/synth/navierStokes/nsSplat.glsl"


class NavierHash22ProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SOURCE.read_text(encoding="utf-8")
        self.sha = hashlib.sha256(self.source.encode()).hexdigest()
        self.program = analyze_program(parse_program(self.source, KEY, {}), KEY)

    def test_exact_source_emits_two_ordered_lane_stores(self) -> None:
        proof = authenticate_navier_hash22(self.program, self.sha)
        self.assertIsNotNone(proof)
        # Authority 5e93c23c stored lane 0 before it read lane 1.
        with emit_typed_cpp.authority_before_7f47340():
            emitted = render_typed_cpp(self.program, KEY, self.sha, "pixel",
                                       "bind_synth_navierStokes_nsSplat")
        first = "glsl::set_swizzle<0>(p, glsl::dot(p,"
        second = "glsl::set_swizzle<1>(p, glsl::dot(p,"
        self.assertEqual(emitted.count(first), 1)
        self.assertEqual(emitted.count(second), 1)
        self.assertLess(emitted.index(first), emitted.index(second))
        self.assertNotIn("p = glsl::Vec2(glsl::FloatExpr<2>(glsl::dot(p,", emitted)
        # Authority 7f47340 (vector-writes.js) reads both lanes, then stores them.
        current = render_typed_cpp(self.program, KEY, self.sha, "pixel",
                                   "bind_synth_navierStokes_nsSplat")
        reads = ("const double cpu_vector_write_0 = static_cast<double>(glsl::dot(p,",
                 "const double cpu_vector_write_1 = static_cast<double>(glsl::dot(p,")
        stores = ("glsl::set_swizzle<0>(p, cpu_vector_write_0);",
                  "glsl::set_swizzle<1>(p, cpu_vector_write_1);")
        for text in reads + stores:
            self.assertEqual(current.count(text), 1)
        self.assertLess(current.index(reads[1]), current.index(stores[0]))
        self.assertLess(current.index(stores[0]), current.index(stores[1]))
        self.assertNotIn(first, current)

    def test_wrong_caller_hash_and_raw_bytes_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "source identity"):
            authenticate_navier_hash22(self.program, "0" * 64)
        forged = replace(self.program, raw_source=self.program.raw_source + " ")
        with self.assertRaisesRegex(ValueError, "source identity"):
            authenticate_navier_hash22(forged, self.sha)

    def test_source_mutation_fails(self) -> None:
        source = self.source.replace("127.1", "127.2", 1)
        candidate = analyze_program(parse_program(source, KEY, {}), KEY)
        with self.assertRaisesRegex(ValueError, "source identity"):
            authenticate_navier_hash22(candidate, hashlib.sha256(source.encode()).hexdigest())

    def test_define_interface_and_other_function_forgery_fail(self) -> None:
        forged_defines = replace(self.program, preprocessor_defines=(
            PreprocessorDefine("FORGED", "int", "1"),))
        with self.assertRaisesRegex(ValueError, "defines must be empty"):
            authenticate_navier_hash22(forged_defines, self.sha)
        forged_resources = replace(self.program, resources=replace(
            self.program.resources, outputs=("other",)))
        with self.assertRaisesRegex(ValueError, "complete typed program identity"):
            authenticate_navier_hash22(forged_resources, self.sha)
        other_function = next(item for item in self.program.functions if item.name == "hash11")
        forged_function = replace(other_function, body=(
            replace(other_function.body[0], kind="discard"), *other_function.body[1:]))
        forged_functions = replace(self.program, functions=tuple(
            forged_function if item is other_function else item
            for item in self.program.functions))
        with self.assertRaisesRegex(ValueError, "complete typed program identity"):
            authenticate_navier_hash22(forged_functions, self.sha)

    def test_target_body_forgery_fails(self) -> None:
        function = next(item for item in self.program.functions if item.name == "hash22")
        statement = function.body[0]
        assignment = statement.expressions[0]
        forged = replace(assignment, operator="+=")
        forged_statement = replace(statement, expressions=(forged,))
        forged_function = replace(function, body=(forged_statement, *function.body[1:]))
        candidate = replace(self.program, functions=tuple(
            forged_function if item is function else item
            for item in self.program.functions))
        with self.assertRaisesRegex(ValueError, "complete typed program identity"):
            authenticate_navier_hash22(candidate, self.sha)


if __name__ == "__main__":
    unittest.main()
