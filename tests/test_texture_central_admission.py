from __future__ import annotations

import hashlib
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.generate_kernels import GeneratorError
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.texture_frontend_profile import (
    KEY, PROFILE)


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources/filter/texture/texture.glsl")


def typed():
    source = SOURCE.read_text(encoding="utf-8")
    return analyze_program(parse_program(source, KEY, {"MODE": 3}), KEY)


class TextureCentralAdmissionTests(unittest.TestCase):
    def test_row_is_landed_and_profile_is_source_bound(self):
        spec = generate_typed_slice.load_slice(ROOT)
        self.assertEqual(211, len(spec["programs"]))
        row = next(item for item in spec["programs"]
                   if item["program_key"] == KEY)
        self.assertEqual(
            {"defines": {"MODE": 3}, "program_key": KEY,
             "texture_frontend_profile": PROFILE}, row)

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


if __name__ == "__main__":
    unittest.main()
