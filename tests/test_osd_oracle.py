from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/osd-parity"
GENERATOR = PACKAGE / "osd_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_osd_native_oracle_include.py"
ORACLE = PACKAGE / "osd-oracles.json"
REPORT = PACKAGE / "osd-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/osd_expected.inc"


def _authority() -> Path:
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not value:
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT is unset")
    path = Path(value)
    if not path.is_dir():
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT is not a directory")
    return path


class OsdOracleTests(unittest.TestCase):
    def _node(self, *args):
        authority = _authority()
        env = os.environ.copy()
        return subprocess.run(
            ["node", str(GENERATOR), *args, "--cpu-root", str(authority)],
            cwd=ROOT, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def test_generator_check_and_materializer_contract(self):
        checked = self._node("--check")
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertIn("7 cases, 6 behavioral mutations", checked.stdout)
        materialized = subprocess.run(
            [sys.executable, "-B", str(MATERIALIZER), "--check"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False)
        self.assertEqual(0, materialized.returncode, materialized.stderr)

    def test_self_tests_cover_identity_input_and_strict_comparer(self):
        checked = self._node("--self-test")
        self.assertEqual(0, checked.returncode, checked.stderr)
        for marker in (
                "modified import dependency rejected",
                "missing import-closure entry rejected",
                "factory mutation witness",
                "public/direct/repeat identity",
                "strict comparer self-tests"):
            self.assertIn(marker, checked.stdout)
        materialized = subprocess.run(
            [sys.executable, "-B", str(MATERIALIZER), "--self-test"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False)
        self.assertEqual(0, materialized.returncode, materialized.stderr)
        self.assertIn("matching-sidecar forgery probes", materialized.stdout)

    def test_document_freezes_small_matrix_and_witnesses(self):
        _authority()
        document = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.osd.pixel-parity.v1",
                         document["schema"])
        self.assertEqual("filter/osd:osd", document["program_key"])
        self.assertEqual("canonicalFactory94", document["factory"]["name"])
        self.assertEqual(7, len(document["render_cases"]))
        self.assertEqual(6, len(document["behavioral_mutation_ledger"]))
        self.assertEqual({
            "inputTex", "resolution", "tileOffset", "fullResolution",
            "renderScale", "alpha", "seed", "speed", "time", "corner",
        }, set(document["source_uniform_abi"]))
        self.assertEqual({
            "good_equal", "dimensions_mismatch", "short_lane_count",
            "long_lane_count", "rgba8_mismatch", "signed_zero_rejected",
            "nan_payload_rejected",
        }, set(document["comparer_self_tests"]))
        self.assertTrue(all(document["comparer_self_tests"].values()))
        for case in document["render_cases"]:
            self.assertTrue(case["input_immutable_exact_bits"])
            self.assertTrue(case["input_lifetime_stable"])
            self.assertEqual(case["width"] * case["height"] * 4,
                             len(case["output_f32_words_le"]))
            self.assertEqual(len(case["output_f32_words_le"]),
                             len(case["output_rgba8_bytes"]))
        for mutation in document["behavioral_mutation_ledger"]:
            self.assertTrue(mutation["required_witnesses"])
            self.assertTrue(all(
                result["mismatched_lanes"] > 0
                and result["mismatched_bytes"] > 0
                for result in mutation["required_witness_results"]))

    def test_sidecars_and_include_are_self_consistent(self):
        for path in (GENERATOR, MATERIALIZER, ORACLE, REPORT, INCLUDE):
            self.assertTrue(path.is_file(), path)
            sidecar = path.with_name(path.name + ".sha256")
            self.assertTrue(sidecar.is_file(), sidecar)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(f"{digest}  {path.name}\n", sidecar.read_text())
        text = INCLUDE.read_text()
        for marker in (
                "namespace noisemaker_osd_oracle", "kCases", "kMutations",
                "kMutationWitnesses", "output_f32_words", "output_rgba8_bytes",
                "kComparerSelfTests", "input_immutable_exact_bits",
                "input_lifetime_stable"):
            self.assertIn(marker, text)
        source = (Path(__file__).read_text())
        self.assertNotRegex(source, r"/(?:private|Users|tmp)/")

    def test_include_compiles_with_cxx20(self):
        source = """
#include <cstdint>
#include <cstddef>
#include <array>
#include "tests/oracles/osd_expected.inc"
int main() {
  static_assert(noisemaker_osd_oracle::kCases.size() == 7);
  static_assert(noisemaker_osd_oracle::kMutations.size() == 6);
  (void)noisemaker_osd_oracle::kCases[0].output_f32_words;
  (void)noisemaker_osd_oracle::kCases[0].output_rgba8_bytes;
  (void)noisemaker_osd_oracle::kMutationWitnesses[0].required_results;
}
"""
        with tempfile.TemporaryDirectory(prefix="osd-oracle-cxx-") as raw:
            unit = Path(raw) / "smoke.cpp"
            unit.write_text(source)
            result = subprocess.run(
                ["c++", "-std=c++20", "-I", str(ROOT), "-fsyntax-only",
                 str(unit)], cwd=ROOT, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
