"""Focused tests for the particle base-color ``round``/``all(lessThanEqual)`` admission.

Seven particle agent programs compare an agent's color with its spawn color in
``baseColor``. ``particle_base_color_profile`` admits exactly the two
``round(vec4)`` sites, the ``lessThanEqual(vec4, vec4)`` relational and its
``all(bvec4)`` reduction of each program, by object identity. These tests
check that admission, that changed sources and foreign keys fail closed, that
the validator and emitter accept only the authenticated closure, and that the
emitter lowers each round lane with Math.round semantics and f32 narrowing.
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
from tools.glslcpp.frontend.particle_base_color_profile import (
    PARTICLE_BASE_COLOR_KEYS, authenticate_particle_base_color)

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus" / CORPUS_REVISION
KEYS = ("points/dla:agent", "points/flock:agent", "points/flow:agent",
        "points/hydraulic:agent", "points/lenia:agentField",
        "points/physarum:agent", "points/physical:agent")


def _source(key: str) -> bytes:
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    entry = next(item for item in manifest["programs"] if item["program_key"] == key)
    return (CORPUS / entry["source"]).read_bytes()


def _analyzed(key: str, source: bytes | None = None):
    text = (_source(key) if source is None else source).decode("utf-8")
    return analyze_program(parse_program(text, key, {}), key)


class ParticleBaseColorProfileTests(unittest.TestCase):
    def test_carrier_set_is_exactly_the_seven_agent_programs(self):
        self.assertEqual(frozenset(KEYS), PARTICLE_BASE_COLOR_KEYS)

    def test_each_program_admits_exactly_its_four_closure_nodes(self):
        for key in KEYS:
            with self.subTest(key=key):
                raw = _source(key)
                program = _analyzed(key)
                proof = authenticate_particle_base_color(
                    program, hashlib.sha256(raw).hexdigest())
                self.assertEqual("baseColor", proof.function.name)
                self.assertEqual(["round", "round"], [item.callee for item in proof.rounds])
                self.assertEqual(["vec4", "vec4"], [item.type.display() for item in proof.rounds])
                self.assertEqual("lessThanEqual", proof.relational.callee)
                self.assertEqual("bvec4", proof.relational.type.display())
                self.assertEqual("all", proof.reduction.callee)
                self.assertIs(proof.relational, proof.reduction.children[0])
                self.assertEqual(4, len({id(item) for item in proof.nodes}))

    def test_changed_source_fails_closed(self):
        key = "points/flock:agent"
        raw = _source(key) + b"\n"
        with self.assertRaises(ValueError):
            authenticate_particle_base_color(_analyzed(key, raw), hashlib.sha256(raw).hexdigest())

    def test_caller_source_hash_is_required(self):
        key = "points/flock:agent"
        with self.assertRaises(ValueError):
            authenticate_particle_base_color(_analyzed(key), "0" * 64)

    def test_foreign_program_key_is_refused(self):
        key = "points/flock:agent"
        program = dataclasses.replace(_analyzed(key), key="points/attractor:agent")
        with self.assertRaises(ValueError):
            authenticate_particle_base_color(program, hashlib.sha256(_source(key)).hexdigest())

    def test_emitter_lowers_each_round_lane_and_the_bvec4_reduction(self):
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        key = "points/flock:agent"
        raw = _source(key)
        source = render_typed_cpp(
            _analyzed(key), key, hashlib.sha256(raw).hexdigest(), "flock_test", "bind_flock_test",
            hash_scalar_uint_xor_profile="hash-scalar-uint-xor-v1",
            hash_scalar_uint_rshift_profile="hash-scalar-uint-rshift-v1",
            vec_scalar_modulo_profile="vec-scalar-modulo-v1",
            points_float_bits_ingress_profile="points-float-bits-ingress-v1",
            points_post_profile="points-post-admission-v1")
        lanes = ", ".join(f"noisemaker::f32(glsl::round(lanes[{index}]))" for index in range(4))
        self.assertEqual(2, source.count("return glsl::Vec4(" + lanes + ");"))
        self.assertEqual(1, source.count(
            "return glsl::BVec4(lhs[0] <= rhs[0], lhs[1] <= rhs[1], lhs[2] <= rhs[2], lhs[3] <= rhs[3]);"))
        self.assertEqual(1, source.count("return lanes[0] && lanes[1] && lanes[2] && lanes[3];"))


if __name__ == "__main__":
    unittest.main()
