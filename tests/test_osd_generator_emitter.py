from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.osd_frontend_profile import (
    KEY, PROFILE, authenticate_osd_frontend)
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"


def _program():
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    entry = next(item for item in manifest["programs"]
                 if item["program_key"] == KEY)
    source = (CORPUS / entry["source"]).read_text()
    program = analyze_program(
        parse_program(source, KEY, generate_typed_slice._defaults(ROOT, KEY)), KEY)
    return entry["raw_sha256"], program


class OsdGeneratorEmitterTests(unittest.TestCase):
    def test_slice_admits_exact_osd_row(self):
        spec = generate_typed_slice.load_slice(ROOT)
        rows = [item for item in spec["programs"] if item["program_key"] == KEY]
        self.assertEqual(rows, [{
            "defines": {}, "osd_frontend_profile": PROFILE, "program_key": KEY,
        }])
        self.assertEqual(len(spec["programs"]), 211)
        self.assertEqual([item["program_key"] for item in spec["programs"]],
                         sorted(item["program_key"] for item in spec["programs"]))

    def test_generator_and_emitter_consume_authenticated_osd_nodes(self):
        source_hash, program = _program()
        proof = authenticate_osd_frontend(program, source_hash, PROFILE)
        self.assertEqual((proof.global_array.name, proof.global_array.extent),
                         ("GLYPHS", 80))
        self.assertEqual(len(proof.bitwise_nodes), 10)
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, osd_frontend_profile=PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash, osd_frontend_profile=PROFILE)
        self.assertIn("std::array<std::int32_t, 80>", rendered)
        self.assertIn("glsl::detail::js_shift_right", rendered)
        self.assertIn("glsl::detail::js_bitwise_and", rendered)
        self.assertIn("double state_glsl_74 =", rendered)
        self.assertIn("static_cast<double>(std::uint32_t(v_in) * std::uint32_t(747796405))", rendered)
        self.assertIn("glsl::detail::js_to_int32(static_cast<double>(hash2", rendered)
        self.assertIn("glsl::detail::js_to_int32(static_cast<double>(digit_hash", rendered)
        self.assertIn(" ^ ", rendered)
        self.assertIn("texture_size", rendered)
        self.assertIn("texel_fetch", rendered)

    def test_osd_pcg_keeps_frozen_js_signed_right_shift_semantics(self):
        source_hash, program = _program()
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash, osd_frontend_profile=PROFILE)
        self.assertIn(
            "glsl::detail::js_shift_right(state_glsl_74, std::uint32_t(28))",
            rendered)
        self.assertIn(
            "glsl::detail::js_shift_right(state_glsl_74, "
            "static_cast<double>(pcg_shift) + static_cast<double>("
            "std::uint32_t(4)))",
            rendered)
        self.assertNotIn(
            "glsl::detail::js_logical_shift_right(state_glsl_74",
            rendered)

    def test_osd_glyph_cell_math_preserves_frozen_js_number_division(self):
        source_hash, program = _program()
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash, osd_frontend_profile=PROFILE)
        self.assertIn(
            "double glyph_idx = (static_cast<double>(lx) / "
            "static_cast<double>(cell_stride));",
            rendered)
        self.assertIn(
            "double within_glyph_x = (lx - (glyph_idx * cell_stride));",
            rendered)

    def test_osd_sample_glyph_preserves_frozen_js_number_index_boundary(self):
        source_hash, program = _program()
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash, osd_frontend_profile=PROFILE)
        self.assertIn(
            "double sample_glyph([[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] std::int32_t digit, [[maybe_unused]] double localX, "
            "[[maybe_unused]] double localY, [[maybe_unused]] std::int32_t iScale)",
            rendered)
        self.assertIn(
            "double gx = (static_cast<double>(localX) / "
            "static_cast<double>(iScale));",
            rendered)
        self.assertIn(
            "double gy = (static_cast<double>(localY) / "
            "static_cast<double>(iScale));",
            rendered)
        self.assertIn(
            "glsl::detail::js_array_int32_read_for_bitwise(",
            rendered)

    def test_generator_rejects_missing_osd_profile(self):
        source_hash, program = _program()
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "exact OSD frontend profile carrier required"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)


if __name__ == "__main__":
    unittest.main()
