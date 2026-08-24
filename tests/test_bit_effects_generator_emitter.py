from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.bit_effects_profile import KEY, PROFILE


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


class BitEffectsGeneratorEmitterTests(unittest.TestCase):
    def test_slice_has_one_canonical_prepared_bit_effects_carrier(self):
        spec = generate_typed_slice.load_slice(ROOT)
        rows = [item for item in spec["programs"] if item["program_key"] == KEY]
        self.assertEqual(spec["programs"][0]["program_key"], KEY)
        self.assertEqual(len(spec["programs"]), 211)
        self.assertEqual(rows, [{
            "defines": {
                "COLOR_SCHEME": 20,
                "FORMULA": 0,
                "INTERP": 0,
                "MASK_COLOR_SCHEME": 1,
                "MASK_FORMULA": 10,
                "MODE": 1,
            },
            "bit_effects_frontend_profile": PROFILE,
            "program_key": KEY,
        }])
        keys = [item["program_key"] for item in spec["programs"]]
        self.assertEqual(keys, sorted(keys))

    def test_generator_and_emitter_consume_the_exact_bit_effects_proof(self):
        source_hash, program = _program()
        from tools.glslcpp.frontend.bit_effects_profile import (
            authenticate_bit_effects_frontend)
        proof = authenticate_bit_effects_frontend(program, source_hash, PROFILE)
        self.assertEqual(
            (len(proof.scalar_int_bitwise_nodes),
             len(proof.float_bits_to_uint_nodes),
             len(proof.vector_uint_bitwise_nodes),
             len(proof.scalar_uint_xor_nodes)),
            (13, 2, 2, 3))
        self.assertEqual(len(proof.consumed_objects), 20)
        self.assertEqual(len({id(item) for item in proof.consumed_objects}), 20)
        mask = proof.global_const_declarations[1].initializer
        self.assertEqual(mask.operator, "-")
        self.assertIs(mask.children[0], proof.scalar_int_bitwise_nodes[0])
        self.assertEqual(mask.children[0].operator, "<<")
        self.assertEqual(mask.children[1].literal_value, 1)
        emitter = emit_typed_cpp._Emitter(
            program, source_hash, bit_effects_frontend_profile=PROFILE)
        self.assertEqual(
            emitter.source_global_dependencies[
                proof.global_const_declarations[1].symbol.id],
            (proof.global_const_declarations[0].symbol.id,))
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            bit_effects_frontend_profile=PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash,
            bit_effects_frontend_profile=PROFILE)
        self.assertIn("js_bitwise_and", rendered)
        self.assertIn("js_bitwise_or", rendered)
        self.assertIn("js_bitwise_xor", rendered)
        self.assertIn("float_bits_to_uint", rendered)
        self.assertIn("glsl::shift_right", rendered)
        self.assertIn("glsl::bitwise_xor", rendered)
        self.assertIn("const std::int32_t BIT_COUNT = 8;", rendered)
        self.assertIn("const std::int32_t mask =", rendered)
        self.assertIn(
            "maskValue(state, context, st, static_cast<float>(1.0), "
            "static_cast<float>(-100.0), "
            "std::numeric_limits<double>::quiet_NaN())",
            rendered)
        self.assertIn(
            "glsl::detail::js_to_int32("
            "static_cast<double>(glsl::swizzle<0>(base)) + "
            "static_cast<double>(seedInt) + glsl::floor(xCombined))",
            rendered)

    def test_cpp_operator_keywords_are_mangled_by_signature_identity(self):
        source_hash, program = _program()
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash,
            bit_effects_frontend_profile=PROFILE)
        for source_name in ("and", "or", "xor"):
            self.assertNotIn(f" {source_name}(", rendered)
        for emitted_name in (
                "and_glsl_87", "and_glsl_88",
                "or_glsl_106", "or_glsl_107",
                "xor_glsl_115", "xor_glsl_116"):
            self.assertIn(f" {emitted_name}(", rendered)

    def test_bit_effects_carrier_rejects_generic_bitwise_collision(self):
        source_hash, program = _program()
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                bit_effects_frontend_profile=PROFILE,
                bitwise_scalar_int_ops_profile="bitwise-scalar-int-ops-v2")


if __name__ == "__main__":
    unittest.main()
