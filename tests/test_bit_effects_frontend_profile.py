from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
KEY = "classicNoisedeck/bitEffects:bitEffects"


def _load_program():
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    entry = next(item for item in manifest["programs"]
                 if item["program_key"] == KEY)
    raw = (CORPUS / entry["source"]).read_text()
    defines = generate_typed_slice._defaults(ROOT, KEY)
    return (entry["raw_sha256"],
            analyze_program(parse_program(raw, KEY, defines), KEY))


def _module():
    from tools.glslcpp.frontend import bit_effects_profile
    return bit_effects_profile


class BitEffectsFrontendProfileTests(unittest.TestCase):
    def test_profile_is_prepared_and_runtime_abi_is_explicit(self):
        module = _module()
        self.assertIsNotNone(importlib.util.find_spec(
            "tools.glslcpp.frontend.bit_effects_profile"))
        self.assertEqual(module.KEYS, ())
        self.assertEqual(module.PREPARED_KEYS, (KEY,))
        self.assertEqual(module.PROFILES, {KEY: module.PROFILE})
        self.assertEqual(module.RUNTIME_ABI, {
            "scalar_int_bitwise": (
                "glsl::detail::js_bitwise_and",
                "glsl::detail::js_bitwise_or",
                "glsl::detail::js_bitwise_xor",
            ),
            "float_bits_to_uint": "noisemaker::float_bits_to_uint",
            "uvec3_shift_right": "glsl::shift_right",
            "uvec3_bitwise_xor": "glsl::bitwise_xor",
            "compile_time_shift_left": "C++ constant expression",
            "canonical_overload_misdispatch":
                "four-argument maskValue helper with quiet-NaN final argument",
            "canonical_xi_to_int32":
                "whole NaN-bearing xi sum through JavaScript ToInt32",
        })

    def test_authentication_returns_exact_feature_census(self):
        module = _module()
        source_hash, program = _load_program()
        proof = module.authenticate_bit_effects_frontend(
            program, source_hash, module.PROFILE)
        self.assertEqual(proof.program_key, KEY)
        self.assertEqual(len(proof.scalar_int_bitwise_nodes), 13)
        self.assertEqual(len(proof.float_bits_to_uint_nodes), 2)
        self.assertEqual(len(proof.vector_uint_bitwise_nodes), 2)
        self.assertEqual(len(proof.scalar_uint_xor_nodes), 3)
        self.assertEqual(tuple(item.symbol.name for item in
                              proof.global_const_declarations),
                         ("BIT_COUNT", "mask"))
        self.assertEqual(len(proof.consumed_objects), 20)
        self.assertEqual(len({id(item) for item in proof.consumed_objects}), 20)
        self.assertEqual(proof.scalar_int_bitwise_operators,
                         ("<<", "&", "&", "&", "&", "&", "^", "|",
                          "&", "&", "^", "&", "&"))
        self.assertEqual(proof.float_bits_to_uint_spans,
                         ("95:21-95:39", "96:21-96:46"))
        self.assertEqual(proof.vector_uint_bitwise_spans,
                         ("50:7-50:20", "104:19-104:57"))
        self.assertEqual(proof.canonical_overload_misdispatch_call.kind, "call")
        self.assertEqual(proof.canonical_overload_misdispatch_call.callee,
                         "maskValue")
        self.assertEqual(
            proof.canonical_overload_misdispatch_call.signature_id, 101)
        self.assertEqual(
            module._span(proof.canonical_overload_misdispatch_call),
            "340:32-340:58")
        self.assertEqual(proof.canonical_xi_to_int32_node.kind, "binary")
        self.assertEqual(proof.canonical_xi_to_int32_node.operator, "+")
        self.assertEqual(
            module._span(proof.canonical_xi_to_int32_node), "90:14-90:54")

    def test_wrong_key_hash_profile_and_forged_site_fail_closed(self):
        module = _module()
        source_hash, program = _load_program()
        for candidate, digest, profile in (
                (program, source_hash, "wrong"),
                (dataclasses.replace(program, key="foreign:foreign"),
                 source_hash, module.PROFILE),
                (program, "0" * 64, module.PROFILE)):
            with self.assertRaises(ValueError):
                module.authenticate_bit_effects_frontend(
                    candidate, digest, profile)

        target = next(node for node in module._all_nodes(program)
                      if node.kind == "binary" and node.operator == "|")
        replacement = dataclasses.replace(target, operator="^")
        changed = module._replace_expression(program, target, replacement)
        with self.assertRaisesRegex(ValueError, "source|identity|cardinality|site"):
            module.authenticate_bit_effects_frontend(
                changed, source_hash, module.PROFILE)

        proof = module.authenticate_bit_effects_frontend(
            program, source_hash, module.PROFILE)
        changed_call = dataclasses.replace(
            proof.canonical_overload_misdispatch_call, signature_id=102)
        changed = module._replace_expression(
            program, proof.canonical_overload_misdispatch_call, changed_call)
        with self.assertRaisesRegex(ValueError, "source|identity|misdispatch"):
            module.authenticate_bit_effects_frontend(
                changed, source_hash, module.PROFILE)

        proof = module.authenticate_bit_effects_frontend(
            program, source_hash, module.PROFILE)
        changed_xi = dataclasses.replace(
            proof.canonical_xi_to_int32_node, operator="-")
        changed = module._replace_expression(
            program, proof.canonical_xi_to_int32_node, changed_xi)
        with self.assertRaisesRegex(ValueError, "source|identity|xi"):
            module.authenticate_bit_effects_frontend(
                changed, source_hash, module.PROFILE)

    def test_foreign_source_cannot_be_relocked_into_this_profile(self):
        module = _module()
        source_hash, program = _load_program()
        changed_raw = program.raw_source.replace("Bit-effects", "Other-effects", 1)
        changed = dataclasses.replace(program, raw_source=changed_raw,
                                      source=program.source.replace(
                                          "Bit-effects", "Other-effects", 1))
        with self.assertRaises(ValueError):
            module.authenticate_bit_effects_frontend(
                changed, hashlib.sha256(changed_raw.encode()).hexdigest(),
                module.PROFILE)

    def test_source_and_interface_contract_exposes_exact_resources(self):
        module = _module()
        source_hash, program = _load_program()
        proof = module.authenticate_bit_effects_frontend(
            program, source_hash, module.PROFILE)
        self.assertEqual(proof.resources, (
            ("time", "seed", "resolution", "tileOffset", "fullResolution",
             "n", "scale", "rotation", "speed", "tiles", "complexity",
             "hueRange", "hueRotation", "baseHueRange"),
            (), ("fragColor",), False, False))
        self.assertEqual(proof.defines, (
            ("COLOR_SCHEME", "int", "20"), ("FORMULA", "int", "0"),
            ("INTERP", "int", "0"), ("MASK_COLOR_SCHEME", "int", "1"),
            ("MASK_FORMULA", "int", "10"), ("MODE", "int", "1")))
        self.assertEqual(proof.declaration_count, 17)
        self.assertEqual(proof.function_count, 30)


if __name__ == "__main__":
    unittest.main()
