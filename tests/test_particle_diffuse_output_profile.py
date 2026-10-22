"""Focused tests for the particle diffuse output store admission.

The authority's JavaScript lowers ``outRGBA = diffuseActive > 0.5 ? a : b;``
so that only the false arm stores into ``outRGBA``.
``particle_diffuse_output_profile`` admits exactly those statements of nine
particle agent programs. These tests check the census, that changed sources
and foreign keys fail closed, and that the emitter lowers each admitted store
with the false-arm-only form.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.particle_diffuse_output_profile import (
    PARTICLE_DIFFUSE_OUTPUT_KEYS, authenticate_particle_diffuse_outputs)

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus" / CORPUS_REVISION
STORES = {
    "points/attractor:agent": 2, "points/buddhabrot:agent": 2, "points/dla:agent": 3,
    "points/flock:agent": 1, "points/flow:agent": 1, "points/hydraulic:agent": 1,
    "points/lenia:agentField": 1, "points/physarum:agent": 1, "points/physical:agent": 1,
}


def _source(key: str) -> bytes:
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    entry = next(item for item in manifest["programs"] if item["program_key"] == key)
    return (CORPUS / entry["source"]).read_bytes()


def _analyzed(key: str, source: bytes | None = None):
    text = (_source(key) if source is None else source).decode("utf-8")
    return analyze_program(parse_program(text, key, {}), key)


class ParticleDiffuseOutputProfileTests(unittest.TestCase):
    def test_carrier_set_is_exactly_the_nine_agent_programs(self):
        self.assertEqual(frozenset(STORES), PARTICLE_DIFFUSE_OUTPUT_KEYS)

    def test_each_program_admits_exactly_its_diffuse_output_stores(self):
        for key, count in STORES.items():
            with self.subTest(key=key):
                proof = authenticate_particle_diffuse_outputs(
                    _analyzed(key), hashlib.sha256(_source(key)).hexdigest())
                self.assertEqual(count, len(proof.assignments))
                for assignment in proof.assignments:
                    self.assertEqual("=", assignment.operator)
                    self.assertEqual("outRGBA", assignment.children[0].symbol.name)
                    self.assertEqual("conditional", assignment.children[1].kind)

    def test_changed_source_fails_closed(self):
        key = "points/dla:agent"
        raw = _source(key) + b"\n"
        with self.assertRaises(ValueError):
            authenticate_particle_diffuse_outputs(_analyzed(key, raw), hashlib.sha256(raw).hexdigest())

    def test_foreign_program_key_is_refused(self):
        key = "points/dla:agent"
        program = dataclasses.replace(_analyzed(key), key="points/life:agent")
        with self.assertRaises(ValueError):
            authenticate_particle_diffuse_outputs(program, hashlib.sha256(_source(key)).hexdigest())

    def test_emitter_stores_only_the_false_arm(self):
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        key = "points/dla:agent"
        raw = _source(key)
        source = render_typed_cpp(
            _analyzed(key), key, hashlib.sha256(raw).hexdigest(), "dla_test", "bind_dla_test",
            hash_scalar_uint_xor_profile="hash-scalar-uint-xor-v1",
            hash_scalar_uint_rshift_profile="hash-scalar-uint-rshift-v1",
            dla_bit_ingress_profile="dla-bit-ingress-admission-v1")
        self.assertEqual(3, source.count("(void)(((state.diffuseActive > static_cast<float>(0.5))) ? "))
        self.assertEqual(3, source.count(" : (outRGBA = glsl::Vec4(base)));"))
        self.assertNotIn("outRGBA = glsl::Vec4(((state.diffuseActive", source)


if __name__ == "__main__":
    unittest.main()
