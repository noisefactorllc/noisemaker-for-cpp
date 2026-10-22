"""The Physical agent requires exactly the samplers its CPU pass binds."""
from __future__ import annotations

import dataclasses
import pathlib
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import generate_typed_slice as generator
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.physical_unused_sampler import omitted_physical_samplers
from tools.glslcpp.emit_typed_cpp import render_typed_cpp

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "points/physical:agent"
SOURCE = ROOT / f"tools/glslcpp/corpus/{CORPUS_REVISION}/sources/points/physical/agent.glsl"


class PhysicalUnusedSamplerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.typed = analyze_program(parse_program(SOURCE.read_text(), KEY, {}), KEY)

    def test_exact_program_omits_no_sampler(self):
        # The CPU pass binds inputTex, and spawnColor() reads it.
        self.assertEqual(omitted_physical_samplers(self.typed), frozenset())
        abi = generator._typed_abi(self.typed)
        self.assertEqual(abi["samplers"], ["inputTex", "xyzTex", "velTex", "rgbaTex", "diffuseTex", "baseColorTex"])
        self.assertIn("inputTex", {u["name"] for u in abi["uniforms"]})

    def test_current_emitter_requests_the_bound_input_texture(self):
        source = render_typed_cpp(self.typed, KEY,
            "06f3afef8efeaba67f1babf129ee107b06e860ec8458e270ce404fc770b46615",
            "physical_test", "bind_physical_test",
            hash_scalar_uint_xor_profile="hash-scalar-uint-xor-v1",
            hash_scalar_uint_rshift_profile="hash-scalar-uint-rshift-v1")
        # textureSize() reads the metadata of xyzTex, diffuseTex and inputTex.
        for name in ("xyzTex", "diffuseTex", "inputTex"):
            self.assertIn(f'bindings.texture("{name}")', source)
            self.assertNotIn(f'bindings.texture_or_black("{name}")', source)
        for name in ("velTex", "rgbaTex", "baseColorTex"):
            self.assertIn(f'bindings.texture_or_black("{name}")', source)
            self.assertNotIn(f'bindings.texture("{name}")', source)

    def test_other_program_does_not_receive_the_omission(self):
        self.assertEqual(omitted_physical_samplers(dataclasses.replace(self.typed, key="foreign:agent")), frozenset())

    def test_changed_source_is_rejected(self):
        with self.assertRaises(ValueError):
            omitted_physical_samplers(dataclasses.replace(self.typed, raw_source=self.typed.raw_source + "\n"))

    def test_removed_typed_reference_is_rejected(self):
        spawn = next(f for f in self.typed.functions if f.name == "spawnColor")
        changed = dataclasses.replace(spawn, body=())
        functions = tuple(changed if f is spawn else f for f in self.typed.functions)
        with self.assertRaises(ValueError):
            omitted_physical_samplers(dataclasses.replace(self.typed, functions=functions))


if __name__ == "__main__":
    unittest.main()
