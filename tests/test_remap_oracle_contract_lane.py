"""Independent contract checks for the authenticated Remap native oracle."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MATERIALIZER = ROOT / "tools/glslcpp/generate_remap_native_oracle_include.py"
ORACLE = ROOT / "docs/port-engineering/remap-parity/remap-oracles.json"


def load_materializer():
    spec = importlib.util.spec_from_file_location("remap_materializer_contract_lane", MATERIALIZER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RemapOracleContractLaneTests(unittest.TestCase):
    def test_materializer_check_and_self_test_are_green(self):
        for mode in ("--check", "--self-test"):
            result = subprocess.run(
                ["python3", "-B", str(MATERIALIZER), mode],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("JSON forgeries rejected", result.stdout)
        self.assertIn("matching-sidecar include forge rejected", result.stdout)

    def test_binding_abi_and_case_dimensions_are_exact(self):
        document = json.loads(ORACLE.read_text())
        self.assertEqual(document["schema"], "noisemaker-for-cpp.remap.pixel-parity.v2")
        self.assertEqual(document["program_key"], "synth/remap:remap")
        # The adapter's real binding surface: semantic uniforms remapFactory
        # reads directly, never the packed std140 array (that fed only the
        # retired typed-generated kernel, and there is no longer one ABI
        # string to describe -- hence no runtime_binding_abi/
        # source_uniform_abi/canonical_binding_contract fields at all).
        module = load_materializer()
        self.assertEqual(document["runtime_binding_names"], module.expected_binding_names())
        self.assertEqual(len(document["runtime_binding_names"]), 303)
        self.assertNotIn("runtime_binding_abi", document)
        self.assertNotIn("source_uniform_abi", document)
        self.assertNotIn("canonical_binding_contract", document)
        self.assertEqual(len(document["render_cases"]), 14)
        self.assertEqual(len(document["mutation_ledger"]), 7)
        for case in document["render_cases"]:
            pixels = case["width"] * case["height"]
            self.assertEqual(len(case["input"]["f32_words_le"]), pixels * 4)
            self.assertEqual(len(case["expected"]["f32_words_le"]), pixels * 4)
            self.assertEqual(len(case["expected"]["rgba8_bytes"]), pixels * 4)
            self.assertEqual(len(case["expected"]["f32_words_le"]), len(case["expected"]["rgba8_bytes"]))
            self.assertLessEqual(len(case["controls"]["zones"]), 8)
            self.assertLessEqual(len(case["controls"]["zones"]), case["controls"]["zone_count"])
        self.assertTrue(all(m["witness_cases"] for m in document["mutation_ledger"]))

    def test_provenance_and_mutation_anchors_are_source_bound(self):
        module = load_materializer()
        document = module.validate(module.checked_payload(module.ORACLE))
        self.assertEqual(len(document["provenance"]["cpu_snapshot"]["import_closure"]), 23)
        self.assertTrue(document["provenance"]["cpu_snapshot"]["immutable_snapshot"])
        self.assertTrue(document["provenance"]["cpu_snapshot"]["realpath_containment_checked"])
        self.assertTrue(document["provenance"]["cpu_snapshot"]["live_checkout_rejected"])
        self.assertEqual(document["source_mutation_contract"]["execution"],
                         "independent exact source anchor replacements of the whole adapter module, re-imported as a fresh module and rendered through bindCanonicalKernel/runPass")
        self.assertEqual(document["mutation_anchor_cardinality"]["total"], 7)
        self.assertIn("zone-bounds-reject", document["mutation_anchor_cardinality"]["anchors"])
        for mutation in document["mutation_ledger"]:
            self.assertEqual(mutation["anchor_occurrence_count"], 1)
            self.assertNotEqual(mutation["anchor"], mutation["replacement"])
            self.assertTrue(mutation["witness_cases"])
            self.assertTrue(all(row["case"] in mutation["witness_cases"] or
                                row["case"] in mutation["control_cases"]
                                for row in mutation["results"]))

    def test_matching_sidecar_does_not_authorize_include_forge(self):
        module = load_materializer()
        document = module.validate(module.checked_payload(module.ORACLE))
        expected = module.emit(document).encode()
        with tempfile.TemporaryDirectory(prefix="remap-contract-forge-") as directory:
            target = pathlib.Path(directory) / "remap_expected.inc"
            forged = expected + b"\n// forged after materialization\n"
            target.write_bytes(forged)
            target.with_name(target.name + ".sha256").write_text(module.sidecar(target, forged))
            with self.assertRaises(module.OracleError):
                module.checked_target(document, target)


if __name__ == "__main__":
    unittest.main()
