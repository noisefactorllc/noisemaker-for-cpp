from __future__ import annotations

import hashlib
import json
import pathlib
import unittest

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import testpattern_profile


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = testpattern_profile.KEY


class TestPatternGeneratorIntegrationTests(unittest.TestCase):
    def test_typed_slice_admits_exact_testpattern_row_after_noise(self):
        spec = generate_typed_slice.load_slice(ROOT)
        rows = [item for item in spec["programs"] if item["program_key"] == KEY]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], {
            "defines": {},
            "program_key": KEY,
            "testpattern_profile": testpattern_profile.PROFILE,
        })
        keys = [item["program_key"] for item in spec["programs"]]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(keys.index(KEY), 208)
        self.assertEqual(len(keys), 209)

    def test_generator_authenticates_testpattern_bindings_and_loop_proof(self):
        source_path = (ROOT / "tools/glslcpp/corpus"
                       / generate_typed_slice.check_corpus.REVISION
                       / "sources/synth/testPattern/testPattern.glsl")
        source = source_path.read_text(encoding="utf-8")
        parsed = parse_program(source, KEY, {})
        typed = analyze_program(parsed, KEY)
        source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
        proof = testpattern_profile.authenticate_testpattern_frontend(
            typed, source_hash, testpattern_profile.PROFILE)
        contract = testpattern_profile.preflight_testpattern_bindings(typed)
        self.assertEqual(contract.names, testpattern_profile.BINDING_NAMES)
        self.assertEqual(contract.grid_size_range, (0, 16))
        self.assertEqual(contract.pattern_range, (0, 6))
        self.assertEqual(proof.dynamic_loop_bound_range, (1, 3))
        self.assertEqual(proof.binding_preflight, contract)

    def _typed_and_proof(self):
        source_path = (ROOT / "tools/glslcpp/corpus"
                       / generate_typed_slice.check_corpus.REVISION
                       / "sources/synth/testPattern/testPattern.glsl")
        source = source_path.read_text(encoding="utf-8")
        typed = analyze_program(parse_program(source, KEY, {}), KEY)
        source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
        proof = testpattern_profile.authenticate_testpattern_frontend(
            typed, source_hash, testpattern_profile.PROFILE)
        return typed, source_hash, proof

    def test_generator_consumes_authenticated_testpattern_proof(self):
        typed, source_hash, proof = self._typed_and_proof()
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, testpattern_frontend_proof=proof)

    def test_generator_rejects_missing_testpattern_array_consumption(self):
        typed, source_hash, proof = self._typed_and_proof()
        glyph = next(item for item in proof.consumed_objects
                     if getattr(getattr(item, "symbol", None), "id", None)
                     == proof.global_array.symbol_id)
        forged = proof._replace(
            consumed_objects=tuple(item for item in proof.consumed_objects
                                   if item is not glyph))
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "unsupported typed type int\\[10\\]"):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash, testpattern_frontend_proof=forged)

    def test_generated_manifest_has_testpattern_runtime_contract(self):
        manifest_path = ROOT / "src/typed_generated/typed_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = [item for item in manifest["programs"] if item["program_key"] == KEY]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["define_contract"], "none")
        self.assertEqual(rows[0]["testpattern_profile"],
                         testpattern_profile.PROFILE)


if __name__ == "__main__":
    unittest.main()
