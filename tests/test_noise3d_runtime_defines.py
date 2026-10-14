import dataclasses
import hashlib
import json
from pathlib import Path
import unittest


class Noise3dRuntimeDefinesTest(unittest.TestCase):
    def test_runtime_define_table_and_loop_contract_are_scoped(self) -> None:
        from tools.glslcpp.generate_typed_slice import GENERIC_DYNAMIC_DEFINE_TYPES
        from tools.glslcpp.frontend.runtime_loop_bound_profile import RUNTIME_LOOP_BOUND_KEYS

        key = "synth3d/noise3d:precompute"
        self.assertEqual(
            {"COLOR_MODE": "int", "OCTAVES": "int", "RIDGES": "bool"},
            GENERIC_DYNAMIC_DEFINE_TYPES[key],
        )
        self.assertIn(key, RUNTIME_LOOP_BOUND_KEYS)

    def test_exact_source_metadata_proof_and_emitted_guards(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE as LOOP, apply_runtime_loop_bound,
            authenticate_runtime_loop_bound, validate_noise3d_metadata,
        )
        from tools.glslcpp.frontend.hash_scalar_uint_xor_profile import (
            PROFILE as XOR, authenticate_hash_scalar_uint_xor,
        )
        from tools.glslcpp.generate_typed_slice import (
            APPROVED_CAPABILITIES, validate_capabilities,
        )
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp

        key = "synth3d/noise3d:precompute"
        root = Path("tools/glslcpp/corpus/5976b7a6b77f69c47c41f4ee296a54d5318e1f9d")
        raw = (root / "sources/synth3d/noise3d/precompute.glsl").read_text()
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        metadata = json.loads((root / "metadata.json").read_text())
        effect = metadata["effects"]["synth3d/noise3d"]
        validate_noise3d_metadata(effect)
        changed = json.loads(json.dumps(effect))
        changed["params"]["octaves"]["max"] = 7
        with self.assertRaises(ValueError):
            validate_noise3d_metadata(changed)

        ast = parse_program(raw, key, {"COLOR_MODE": "int", "OCTAVES": "int",
                                       "RIDGES": "bool"})
        ast["raw_source"] = raw
        typed = analyze_program(ast, key)
        with self.assertRaises(ValueError):
            authenticate_runtime_loop_bound(typed, "0" * 64, LOOP)
        proofed = apply_runtime_loop_bound(typed, source_hash, LOOP)
        self.assertEqual(6, proofed.counted_loop_proof.max_lexical_product)
        self.assertEqual(3, len(authenticate_hash_scalar_uint_xor(proofed, source_hash, XOR)))
        validate_capabilities(proofed, APPROVED_CAPABILITIES,
                              source_hash=source_hash,
                              runtime_loop_bound_profile=LOOP,
                              hash_scalar_uint_xor_profile=XOR)
        cpp = render_typed_cpp(
            proofed, key, source_hash, "pixel", "bind_synth3d_noise3d_precompute",
            runtime_loop_bound_profile=LOOP, hash_scalar_uint_xor_profile=XOR)
        self.assertIn("OCTAVES < 1 || OCTAVES > 6", cpp)
        self.assertIn("COLOR_MODE < 0 || COLOR_MODE > 1", cpp)
        self.assertIn("glsl::detail::js_to_int32(static_cast<double>(scaled[lane]))", cpp)
        self.assertIn("double seed_value", cpp)
        self.assertIn('bindings.get_number("seed")', cpp)

        alien = dataclasses.replace(proofed, key="foreign/effect:precompute")
        with self.assertRaises(ValueError):
            authenticate_hash_scalar_uint_xor(alien, source_hash, XOR)


if __name__ == "__main__":
    unittest.main()
