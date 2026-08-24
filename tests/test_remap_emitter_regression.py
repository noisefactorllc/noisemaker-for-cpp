"""Independent fail-closed admission tests for the Remap typed emitter."""
from __future__ import annotations

import pathlib
import unittest

from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.remap_profile import (
    KEY, PROFILE, RAW_SHA256, authenticate_remap_frontend,
)
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources"
SOURCE = (CORPUS / "synth/remap/remap.glsl").read_text(encoding="utf-8")
DEFINES = {}


def typed_remap():
    parsed = parse_program(SOURCE, KEY, DEFINES)
    return analyze_program(parsed, KEY)


class RemapEmitterRegressionTests(unittest.TestCase):
    def proof(self, typed=None):
        typed = typed or typed_remap()
        return typed, authenticate_remap_frontend(typed, RAW_SHA256, PROFILE)

    def test_authenticated_remap_emits_owned_data_and_checked_indices(self):
        typed, proof = self.proof()
        output = render_typed_cpp(
            typed, KEY, RAW_SHA256, "remap_kernel", "bind_remap",
            remap_profile=PROFILE, remap_frontend_proof=proof)
        self.assertIn("RemapUniformData data_value", output)
        self.assertIn("RemapUniformData data;", output)
        self.assertIn("remap_data_index", output)
        self.assertIn("state.data.data[remap_data_index", output)
        self.assertIn("std::int64_t", output)
        self.assertNotIn("std::array<glsl::Vec4, 267> data", output)

    def test_missing_remap_profile_is_rejected(self):
        typed, proof = self.proof()
        with self.assertRaisesRegex(TypedEmissionError, "exact Remap profile"):
            render_typed_cpp(typed, KEY, RAW_SHA256, remap_frontend_proof=proof)

    def test_missing_remap_proof_is_rejected(self):
        typed = typed_remap()
        with self.assertRaisesRegex(TypedEmissionError, "exact Remap frontend proof"):
            render_typed_cpp(typed, KEY, RAW_SHA256, remap_profile=PROFILE)

    def test_foreign_and_stale_remap_proofs_are_rejected(self):
        typed, proof = self.proof()
        foreign = proof._replace(program_key="foreign:key")
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(typed, KEY, RAW_SHA256,
                             remap_profile=PROFILE,
                             remap_frontend_proof=foreign)
        stale = proof._replace(indexes=proof.indexes[:-1])
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(typed, KEY, RAW_SHA256,
                             remap_profile=PROFILE,
                             remap_frontend_proof=stale)


if __name__ == "__main__":
    unittest.main()
