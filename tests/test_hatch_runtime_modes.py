"""Hatch must use the caller's MODE instead of a baked default."""

import hashlib
import json
from pathlib import Path
import unittest
from dataclasses import replace
from unittest import mock

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import corpus_ratchet, generate_typed_slice
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / f"tools/glslcpp/corpus/{CORPUS_REVISION}"
KEY = "filter/hatch:hatch"


class HatchRuntimeModeTests(unittest.TestCase):
    def test_runtime_profile_and_full_admission(self):
        self.assertEqual(generate_typed_slice.GENERIC_DYNAMIC_DEFINE_TYPES[KEY], {"MODE": "int"})
        spec = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text())
        row = next(item for item in spec["programs"] if item["program_key"] == KEY)
        self.assertEqual(row["runtime_define_profile"], generate_typed_slice.GENERIC_RUNTIME_DEFINE_PROFILE)
        raw = (CORPUS / "sources/filter/hatch/hatch.glsl").read_bytes()
        effect = json.loads((CORPUS / "metadata.json").read_text())["effects"]["filter/hatch"]
        self.assertIsNone(corpus_ratchet.probe_program(KEY, raw, effect))

    def test_emission_keeps_all_six_mode_paths(self):
        raw = (CORPUS / "sources/filter/hatch/hatch.glsl").read_text()
        typed = analyze_program(parse_program(raw, KEY, {"MODE": "int"}), KEY)
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=hashlib.sha256(raw.encode()).hexdigest())
        code = render_typed_cpp(typed, KEY, hashlib.sha256(raw.encode()).hexdigest(),
                                "test_hatch", "bind_test_hatch")
        self.assertIn('bindings.get<std::int32_t>("MODE")', code)
        for mode in range(5):
            self.assertIn(f"state.MODE == std::int32_t({mode})", code)
        self.assertIn("lumGradient(state, context, uv)", code)

    def test_degrees_proof_rejects_forged_source_and_tree(self):
        from tools.glslcpp.frontend.hatch_degrees_profile import authenticate, RAW_SHA256
        raw = (CORPUS / "sources/filter/hatch/hatch.glsl").read_text()
        typed = analyze_program(parse_program(raw, KEY, {"MODE": "int"}), KEY)
        self.assertEqual(len(authenticate(typed, RAW_SHA256)), 1)
        for mutant in (replace(typed, key="foreign:hatch"),
                       replace(typed, raw_source=typed.raw_source + "\n"),
                       replace(typed, functions=typed.functions[:-1]),
                       replace(typed, preprocessor_defines=())):
            with self.assertRaises(ValueError):
                authenticate(mutant, RAW_SHA256)
        with self.assertRaises(ValueError):
            authenticate(typed, "0" * 64)

    def test_stroke_field_multiplier_materializes_reciprocal_once(self):
        from tools.glslcpp.frontend.hatch_degrees_profile import (
            authenticate_hatch_multiplier, RAW_SHA256)
        raw = (CORPUS / "sources/filter/hatch/hatch.glsl").read_text()
        typed = analyze_program(parse_program(raw, KEY, {"MODE": "int"}), KEY)
        multiplier = authenticate_hatch_multiplier(typed, RAW_SHA256)
        self.assertEqual((multiplier.kind, multiplier.type.display()), ("construct", "vec2"))
        code = render_typed_cpp(typed, KEY, RAW_SHA256,
                                "test_hatch", "bind_test_hatch")
        expected = ("glsl::Vec2(glsl::FloatExpr<2>("
                    "(static_cast<double>(static_cast<float>(1.0)) / "
                    "static_cast<double>(stretchAmt)), static_cast<float>(0.9)))")
        self.assertEqual(code.count(expected), 1)
        self.assertIn("rotate2D(state, context, gc, angleDeg)", code)

        function = next(item for item in typed.functions if item.name == "strokeField")
        statement = function.body[0]
        declaration = statement.expressions[0]
        product = declaration.children[0]
        forged_multiplier = replace(
            multiplier, children=(multiplier.children[0],
                                  replace(multiplier.children[1], literal_value=0.8)))
        forged_product = replace(product, children=(product.children[0], forged_multiplier))
        forged_declaration = replace(declaration, children=(forged_product,))
        forged_statement = replace(statement, expressions=(forged_declaration,))
        forged_function = replace(function, body=(forged_statement, *function.body[1:]))
        forged_functions = tuple(forged_function if item is function else item
                                 for item in typed.functions)

        for mutant in (replace(typed, raw_source=typed.raw_source + "\n"),
                       replace(typed, source=typed.source + "\n"),
                       replace(typed, functions=forged_functions),
                       replace(typed, functions=typed.functions[:-1]),
                       replace(typed, preprocessor_defines=()),
                       replace(typed, key="foreign:hatch")):
            with self.assertRaises(ValueError):
                authenticate_hatch_multiplier(mutant, RAW_SHA256)
        with self.assertRaises(ValueError):
            authenticate_hatch_multiplier(typed, "0" * 64)
        for mutant in (replace(typed, raw_source=typed.raw_source + "\n"),
                       replace(typed, functions=forged_functions)):
            with self.assertRaises(ValueError):
                render_typed_cpp(mutant, KEY, RAW_SHA256,
                                 "forged_hatch", "bind_forged_hatch")

    def test_frozen_default_keeps_original_multiplier_emission(self):
        raw = (ROOT / "tools/glslcpp/corpus/0ed489ec46842bffba33ee2ec65a218b6dda51f5"
               / "sources/filter/hatch/hatch.glsl").read_text()
        typed = analyze_program(parse_program(raw, KEY, {"MODE": "0"}), KEY)
        from tools.glslcpp.frontend import hatch_degrees_profile
        # The frozen default has its own complete typed-tree identity.
        with mock.patch.object(hatch_degrees_profile, "WHOLE_SHA256",
                               "eb95b58dbfe1cc5c430c6368ab9f6b44d3fc0f4314c9118b4da630323000ee42"):
            code = render_typed_cpp(typed, KEY, hashlib.sha256(raw.encode()).hexdigest(),
                                    "historical_hatch", "bind_historical_hatch")
        self.assertIn("glsl::FloatExpr<2>((static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(stretchAmt))", code)
        self.assertNotIn("glsl::Vec2(glsl::FloatExpr<2>((static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(stretchAmt))", code)
