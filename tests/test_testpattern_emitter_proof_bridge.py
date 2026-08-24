from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import unittest

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program, testpattern_profile
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources/synth/testPattern/testPattern.glsl")
KEY = testpattern_profile.KEY


def _program(raw: str | None = None):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(parse_program(raw, KEY, {}), KEY)


def _proof(program):
    source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
    return source_hash, testpattern_profile.authenticate_testpattern_frontend(
        program, source_hash, testpattern_profile.PROFILE)


class TestPatternEmitterProofBridge(unittest.TestCase):
    def test_render_consumes_the_authenticated_live_proof(self):
        program = _program()
        source_hash, proof = _proof(program)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash,
            testpattern_profile=testpattern_profile.PROFILE,
            testpattern_frontend_proof=proof)
        self.assertIn("std::array<std::int32_t, 10> GLYPH", rendered)
        self.assertEqual(rendered.count("static_cast<std::size_t>("), 4)

    def test_authenticated_controls_are_fetched_once_and_guarded(self):
        program = _program()
        source_hash, proof = _proof(program)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash,
            testpattern_profile=testpattern_profile.PROFILE,
            testpattern_frontend_proof=proof)
        self.assertEqual(
            rendered.count('bindings.get<std::int32_t>("gridSize")'), 1)
        self.assertEqual(
            rendered.count('bindings.get<std::int32_t>("pattern")'), 1)
        self.assertIn("gridSize < 0 || gridSize > 16", rendered)
        self.assertIn("pattern < 0 || pattern > 6", rendered)
        self.assertIn("KernelBindingError", rendered)

    def test_missing_or_mismatched_proof_is_fail_closed(self):
        program = _program()
        source_hash, proof = _proof(program)
        cases = (
            {},
            {"testpattern_frontend_proof": proof._replace(program_key="foreign")},
            {"testpattern_frontend_proof": proof._replace(round_node=program.functions[0])},
            {"testpattern_frontend_proof": proof._replace(dynamic_indexes=(None,))},
        )
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                    emit_typed_cpp.render_typed_cpp(
                        program, KEY, source_hash,
                        testpattern_profile=testpattern_profile.PROFILE,
                        **kwargs)

    def test_stale_proof_and_profile_pairings_are_rejected(self):
        program = _program()
        source_hash, proof = _proof(program)
        changed = dataclasses.replace(program, source=program.source + "\n// stale\n")
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                changed, KEY, source_hash,
                testpattern_profile=testpattern_profile.PROFILE,
                testpattern_frontend_proof=proof)
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, source_hash,
                testpattern_frontend_proof=proof)


if __name__ == "__main__":
    unittest.main()
