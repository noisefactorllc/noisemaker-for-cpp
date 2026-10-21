"""The Physical agent must not require a sampler absent from its CPU pass."""
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

    def test_exact_program_omits_only_unread_sampler(self):
        self.assertEqual(omitted_physical_samplers(self.typed), frozenset({"inputTex"}))
        abi = generator._typed_abi(self.typed)
        self.assertEqual(abi["samplers"], ["xyzTex", "velTex", "rgbaTex"])
        self.assertNotIn("inputTex", {u["name"] for u in abi["uniforms"]})

    def test_current_emitter_does_not_request_the_unused_texture(self):
        source = render_typed_cpp(self.typed, KEY,
            "a144cacbadeca15a78a83dac987bfd25164bd7904a2e9f0ea22e8b1bf22e3614",
            "physical_test", "bind_physical_test",
            hash_scalar_uint_xor_profile="hash-scalar-uint-xor-v1",
            hash_scalar_uint_rshift_profile="hash-scalar-uint-rshift-v1")
        self.assertNotIn('bindings.texture("inputTex")', source)
        self.assertNotIn('bindings.texture_or_black("inputTex")', source)
        self.assertIn('bindings.texture("xyzTex")', source)
        self.assertNotIn('bindings.texture_or_black("xyzTex")', source)
        for name in ("velTex", "rgbaTex"):
            self.assertIn(f'bindings.texture_or_black("{name}")', source)
            self.assertNotIn(f'bindings.texture("{name}")', source)

    def test_other_program_does_not_receive_the_omission(self):
        self.assertEqual(omitted_physical_samplers(dataclasses.replace(self.typed, key="foreign:agent")), frozenset())

    def test_changed_source_is_rejected(self):
        with self.assertRaises(ValueError):
            omitted_physical_samplers(dataclasses.replace(self.typed, raw_source=self.typed.raw_source + "\n"))

    def test_new_typed_reference_is_rejected(self):
        target = next(d.symbol for d in self.typed.declarations if d.symbol.name == "inputTex")
        function = self.typed.functions[-1]
        statement = function.body[0]
        expression = statement.expressions[0]
        reference = dataclasses.replace(expression, kind="id", type=target.type,
                                        symbol=target, symbol_id=target.id, children=())
        changed_statement = dataclasses.replace(statement, expressions=(reference,))
        changed_function = dataclasses.replace(function, body=(changed_statement, *function.body[1:]))
        with self.assertRaises(ValueError):
            omitted_physical_samplers(dataclasses.replace(self.typed, functions=(*self.typed.functions[:-1], changed_function)))


if __name__ == "__main__":
    unittest.main()
