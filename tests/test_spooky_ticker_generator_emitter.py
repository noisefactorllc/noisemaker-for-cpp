from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.spooky_ticker_frontend_profile import (
    KEY, PROFILE, authenticate_spooky_ticker_frontend)


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"


def _program():
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    entry = next(item for item in manifest["programs"]
                 if item["program_key"] == KEY)
    source = (CORPUS / entry["source"]).read_text()
    program = analyze_program(
        parse_program(source, KEY, generate_typed_slice._defaults(ROOT, KEY)),
        KEY)
    return entry["raw_sha256"], program


class SpookyTickerGeneratorEmitterTests(unittest.TestCase):
    def test_slice_admits_exact_spooky_ticker_row(self):
        spec = generate_typed_slice.load_slice(ROOT)
        rows = [item for item in spec["programs"] if item["program_key"] == KEY]
        self.assertEqual(rows, [{
            "defines": {},
            "program_key": KEY,
            "spooky_ticker_frontend_profile": PROFILE,
        }])
        self.assertEqual(len(spec["programs"]), 211)
        self.assertEqual([item["program_key"] for item in spec["programs"]],
                         sorted(item["program_key"]
                                for item in spec["programs"]))

    def test_generator_and_emitter_consume_authenticated_spooky_nodes(self):
        source_hash, program = _program()
        proof = authenticate_spooky_ticker_frontend(
            program, source_hash, PROFILE)
        self.assertEqual((proof.global_array.name, proof.global_array.extent),
                         ("GLYPHS", 80))
        self.assertEqual(len(proof.bitwise_nodes), 11)
        self.assertEqual(len(proof.varying_reads), 3)
        self.assertEqual(len(proof.number_parameters), 4)
        self.assertEqual(len(proof.number_declarations), 8)
        self.assertEqual(len(proof.number_divisions), 5)
        self.assertEqual(len(proof.number_umul_nodes), 2)
        self.assertEqual(len(proof.number_remainder_nodes), 1)
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            spooky_ticker_frontend_profile=PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash,
            spooky_ticker_frontend_profile=PROFILE)
        self.assertIn("std::array<std::int32_t, 80>", rendered)
        self.assertIn("glsl::detail::js_shift_right", rendered)
        self.assertIn("glsl::detail::js_bitwise_and", rendered)
        self.assertIn("context.uv", rendered)
        self.assertIn("texture_size", rendered)
        self.assertIn("sample_texture", rendered)
        self.assertEqual(2, rendered.count("glsl::detail::js_umul("))
        self.assertEqual(
            1,
            rendered.count(
                "glsl::detail::js_array_int32_read_for_bitwise("),
        )
        self.assertEqual(1, rendered.count("std::fmod("))
        self.assertEqual(2, rendered.count("[[nodiscard]] double hash_mix("))
        self.assertIn(
            "std::int32_t digit, [[maybe_unused]] double localX, "
            "[[maybe_unused]] double localY",
            rendered,
        )
        self.assertIn(
            "std::int32_t pixelX, [[maybe_unused]] double pixelY",
            rendered,
        )
        for name in ("rowIdx", "localY", "shadowLocalY", "gx", "gy",
                     "cellX", "localX", "h"):
            self.assertIn(f"[[maybe_unused]] double {name} =", rendered)

    def test_generator_rejects_missing_spooky_ticker_profile(self):
        source_hash, program = _program()
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "exact SpookyTicker frontend profile carrier required"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)


if __name__ == "__main__":
    unittest.main()
