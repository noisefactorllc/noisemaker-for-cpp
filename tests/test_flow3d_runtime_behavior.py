"""Flow3D behavior must stay dynamic only in the pass that reads it."""

import dataclasses
import hashlib
import json
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import corpus_ratchet, generate_typed_slice as generator
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import hash_scalar_uint_xor_profile as xor
from tools.glslcpp.frontend import hash_scalar_uint_rshift_profile as shift

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / f"tools/glslcpp/corpus/{CORPUS_REVISION}"
KEY = "filter3d/flow3d:agent"


class Flow3DRuntimeBehaviorTests(unittest.TestCase):
    def test_agent_proofs_keep_default_and_dynamic_trees(self):
        raw = (CORPUS / "sources/filter3d/flow3d/agent.glsl").read_text()
        digest = hashlib.sha256(raw.encode()).hexdigest()
        for define in (1, "int"):
            typed = analyze_program(parse_program(raw, KEY, {"BEHAVIOR": define}), KEY)
            self.assertEqual(len(xor.authenticate_hash_scalar_uint_xor(typed, digest, xor.PROFILE)), 2)
            self.assertEqual(len(shift.authenticate_hash_scalar_uint_rshift(typed, digest, shift.PROFILE)), 3)
            for candidate in (dataclasses.replace(typed, functions=()),
                              dataclasses.replace(typed, raw_source=raw + "\n"),
                              dataclasses.replace(typed, preprocessor_defines=())):
                for authenticate, profile in (
                    (xor.authenticate_hash_scalar_uint_xor, xor.PROFILE),
                    (shift.authenticate_hash_scalar_uint_rshift, shift.PROFILE)):
                    with self.assertRaisesRegex(ValueError, "mismatch"):
                        authenticate(candidate, digest, profile)

    def test_full_agent_admission_uses_runtime_behavior(self):
        self.assertEqual(generator.GENERIC_DYNAMIC_DEFINE_TYPES[KEY], {"BEHAVIOR": "int"})
        raw = (CORPUS / "sources/filter3d/flow3d/agent.glsl").read_bytes()
        effect = json.loads((CORPUS / "metadata.json").read_text())["effects"]["filter3d/flow3d"]
        self.assertIsNone(corpus_ratchet.probe_program(KEY, raw, effect))

    def test_non_agent_passes_do_not_bake_an_absent_define(self):
        for name in ("blend", "copy", "diffuse"):
            raw = (CORPUS / f"sources/filter3d/flow3d/{name}.glsl").read_text()
            self.assertEqual(generator.default_define_contract(raw, {"BEHAVIOR": 1}), "none")
            self.assertEqual(generator.default_define_contract(raw + "\n#if BEHAVIOR == 1\n#endif\n",
                                                              {"BEHAVIOR": 1}), "default-only")
        # Any source occurrence conservatively retains the compiled contract.
        self.assertEqual(generator.default_define_contract("// MODE\nvoid main() {}", {"MODE": 0}), "default-only")
        self.assertEqual(generator.default_define_contract("float MODE2;", {"MODE": 0}), "none")
