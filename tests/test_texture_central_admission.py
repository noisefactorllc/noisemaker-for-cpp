from __future__ import annotations

import hashlib
import dataclasses
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tests import corpus_census
from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.generate_kernels import GeneratorError
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source
from tools.glslcpp.frontend.texture_frontend_profile import (
    KEY, PROFILE)


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / f"tools/glslcpp/corpus/{CORPUS_REVISION}"
          / "sources/filter/texture/texture.glsl")


def typed():
    source = SOURCE.read_text(encoding="utf-8")
    return analyze_program(parse_program(source, KEY, {"MODE": 3}), KEY)


class TextureCentralAdmissionTests(unittest.TestCase):
    def test_row_is_landed_and_profile_is_source_bound(self):
        spec = generate_typed_slice.load_slice(ROOT)
        self.assertEqual(corpus_census.typed_count(), len(spec["programs"]))
        row = next(item for item in spec["programs"]
                   if item["program_key"] == KEY)
        self.assertEqual(
            {"defines": {"MODE": 3}, "program_key": KEY,
             "texture_frontend_profile": PROFILE,
             "runtime_define_profile": "runtime-defines-generic-v1"}, row)

    def test_validator_admits_authenticated_texture_integer_closure(self):
        program = typed()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, texture_frontend_profile=PROFILE)

    def test_emitter_lowers_authenticated_texture_integer_closure(self):
        program = typed()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        rendered = render_typed_cpp(program, KEY, source_hash,
                                    texture_frontend_profile=PROFILE)
        self.assertIn("glsl::inversesqrt", rendered)
        self.assertGreaterEqual(rendered.count(" ^ "), 10)
        self.assertIn(
            "return (static_cast<double>(static_cast<double>(h)) * "
            "static_cast<double>(INV_UINT32_MAX));",
            rendered,
        )
        self.assertNotIn("static_cast<double>(float(h))", rendered)
        self.assertNotIn(
            "glsl::Vec2((glsl::Vec2((glsl::FloatExpr<2>(",
            rendered,
        )

    def test_profile_authenticates_texture_hash_number_conversion(self):
        program = typed()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        proof = __import__(
            "tools.glslcpp.frontend.texture_frontend_profile",
            fromlist=["authenticate_texture_frontend"],
        ).authenticate_texture_frontend(program, source_hash, PROFILE)

        def span(node):
            value = node.span
            return (f"{value.start_line}:{value.start_column}-"
                    f"{value.end_line}:{value.end_column}")

        self.assertEqual(
            ("construct", "float", "75:12-75:20", ("uint",)),
            (proof.number_preserving_hash_conversion.kind,
             proof.number_preserving_hash_conversion.type.display(),
             span(proof.number_preserving_hash_conversion),
             tuple(child.type.display()
                   for child in proof.number_preserving_hash_conversion.children)),
        )


    def test_runtime_material_compatibility_is_source_bound(self):
        from tools.glslcpp.frontend.texture_frontend_profile import authenticate_texture_frontend
        raw = SOURCE.read_text(encoding="utf-8")
        parsed = parse_program(transform_source(raw, KEY), KEY, {"MODE": "int"})
        parsed["raw_source"] = raw
        program = analyze_program(parsed, KEY)
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        proof = authenticate_texture_frontend(program, source_hash, PROFILE)
        self.assertEqual(2, len(proof.material_layer_conversions))
        self.assertEqual(1, len(proof.signed_gradient_shift))
        self.assertEqual(2, len(proof.vector_scalar_conversions))
        rendered = render_typed_cpp(program, KEY, source_hash,
                                    texture_frontend_profile=PROFILE)
        self.assertEqual(2, rendered.count("std::uint32_t{0}"))
        self.assertIn("float(glsl::detail::js_shift_right(h, 16))", rendered)
        self.assertIn("glsl::IVec3(0, 0, 0)", rendered)
        self.assertIn("glsl::IVec3(0, 1, 0)", rendered)
        with self.assertRaisesRegex(ValueError, "source|structural|identity"):
            authenticate_texture_frontend(dataclasses.replace(
                program, raw_source=raw + " "), source_hash, PROFILE)
        with self.assertRaisesRegex(ValueError, "source|structural|identity"):
            authenticate_texture_frontend(dataclasses.replace(
                program, functions=program.functions[:-1]), source_hash, PROFILE)

if __name__ == "__main__":
    unittest.main()
