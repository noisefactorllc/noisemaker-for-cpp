"""Regression tests for the Remap typed-emitter custom_adapter short-circuit.

synth/remap:remap is corpus-status ``adapter``: typed generation cannot be
bit-exact against the authority for this program (see
tools/glslcpp/frontend/remap_profile.py's module docstring), so
``emit_typed_cpp.render_typed_cpp`` special-cases ``REMAP_KEY`` before ever
constructing an emitter -- it always returns a fixed "custom_adapter route"
comment naming the hand-written ``noisemaker::effects::bind_remap`` (see
src/effects/remap.cpp), never a typed kernel body, regardless of what
``remap_profile``/``remap_frontend_proof`` (or any other capability
argument) is supplied. These tests pin that short-circuit: it fires with no
profile carrier at all, and it is not bypassable by supplying a real,
forged, or foreign one -- there is no longer anything for a caller to admit
or fail closed on for this key's typed body, by design.
"""
from __future__ import annotations

import pathlib
import unittest

from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.remap_profile import (
    KEY, PROFILE, RAW_SHA256, authenticate_remap_frontend,
)
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
# remap_profile.py's RAW_SHA256/authenticate_remap_frontend are pinned to the
# OLD 267-slot remap.glsl (corpus a024dc3a...), kept as a historical record
# and deliberately never run against the live 0ed489ec... source (see that
# module's docstring). This test authenticates that same frozen record, so
# it reads the OLD corpus, matching test_remap_frontend_profile.py.
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources"
SOURCE = (CORPUS / "synth/remap/remap.glsl").read_text(encoding="utf-8")
DEFINES = {}

EXPECTED_STUB = (
    f"// Typed IR program: {KEY}\n"
    f"// Source SHA-256: {RAW_SHA256}\n"
    "// custom_adapter route: no typed kernel body generated;\n"
    "// see noisemaker::effects::bind_remap (src/effects/remap.cpp).\n"
)


def typed_remap():
    parsed = parse_program(SOURCE, KEY, DEFINES)
    return analyze_program(parsed, KEY)


class RemapEmitterRegressionTests(unittest.TestCase):
    def proof(self, typed=None):
        typed = typed or typed_remap()
        return typed, authenticate_remap_frontend(typed, RAW_SHA256, PROFILE)

    def test_remap_key_always_renders_the_custom_adapter_stub_with_no_profile(self):
        typed = typed_remap()
        output = render_typed_cpp(typed, KEY, RAW_SHA256)
        self.assertEqual(EXPECTED_STUB, output)
        self.assertNotIn("RemapUniformData", output)
        self.assertNotIn("struct State", output)
        self.assertNotIn("bind_synth_remap_remap", output)

    def test_remap_key_ignores_a_real_authenticated_profile_and_proof(self):
        typed, proof = self.proof()
        output = render_typed_cpp(
            typed, KEY, RAW_SHA256, "remap_kernel", "bind_remap",
            remap_profile=PROFILE, remap_frontend_proof=proof)
        self.assertEqual(EXPECTED_STUB, output)

    def test_remap_key_ignores_a_proof_with_no_profile_carrier(self):
        typed, proof = self.proof()
        output = render_typed_cpp(typed, KEY, RAW_SHA256, remap_frontend_proof=proof)
        self.assertEqual(EXPECTED_STUB, output)

    def test_remap_key_ignores_foreign_and_stale_proofs(self):
        typed, proof = self.proof()
        foreign = proof._replace(program_key="foreign:key")
        self.assertEqual(
            EXPECTED_STUB,
            render_typed_cpp(typed, KEY, RAW_SHA256, remap_profile=PROFILE,
                             remap_frontend_proof=foreign))
        stale = proof._replace(indexes=proof.indexes[:-1])
        self.assertEqual(
            EXPECTED_STUB,
            render_typed_cpp(typed, KEY, RAW_SHA256, remap_profile=PROFILE,
                             remap_frontend_proof=stale))

    def test_remap_key_ignores_a_wrong_profile_string(self):
        typed = typed_remap()
        self.assertEqual(
            EXPECTED_STUB,
            render_typed_cpp(typed, KEY, RAW_SHA256,
                             remap_profile="foreign-profile-token"))


if __name__ == "__main__":
    unittest.main()
