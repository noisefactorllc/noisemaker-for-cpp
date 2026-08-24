from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/spooky-ticker-parity"
GENERATOR = PACKAGE / "spooky_ticker_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_spooky_ticker_native_oracle_include.py"
ORACLE = PACKAGE / "spooky-ticker-oracles.json"
REPORT = PACKAGE / "spooky-ticker-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/spooky_ticker_expected.inc"

def cpu_root():
    raw = __import__("os").environ.get("NOISEMAKER_CPU_ROOT")
    if not raw: raise unittest.SkipTest("NOISEMAKER_CPU_ROOT is unset")
    path = Path(raw)
    if not path.is_dir(): raise unittest.SkipTest("NOISEMAKER_CPU_ROOT is not a directory")
    return path

class SpookyTickerOracleTests(unittest.TestCase):
    def node(self, mode):
        return subprocess.run(["node", str(GENERATOR), mode, "--cpu-root", str(cpu_root())], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def test_generator_and_materializer_contracts(self):
        result = self.node("--check"); self.assertEqual(0, result.returncode, result.stderr); self.assertIn("7 cases, 10 behavioral mutations", result.stdout)
        result = subprocess.run([sys.executable, "-B", str(MATERIALIZER), "--check"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE); self.assertEqual(0, result.returncode, result.stderr)
    def test_generator_self_tests_witness_closure_and_mutants(self):
        result = self.node("--self-test"); self.assertEqual(0, result.returncode, result.stderr)
        for marker in ("modified import dependency rejected", "symlink import-closure escape rejected", "missing import-closure entry rejected", "public/direct/repeat identity verified", "factory mutation witness: hash-xor-carrier"):
            self.assertIn(marker, result.stdout)
        result = subprocess.run([sys.executable, "-B", str(MATERIALIZER), "--self-test"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE); self.assertEqual(0, result.returncode, result.stderr)
    def test_document_freezes_exact_outputs_inputs_and_semantic_axes(self):
        document = json.loads(ORACLE.read_text()); self.assertEqual("noisemaker-for-cpp.spooky-ticker.pixel-parity.v1", document["schema"]); self.assertEqual("filter/spookyTicker:spookyTicker", document["program_key"])
        self.assertEqual("canonicalFactory147", document["factory"]["name"]); self.assertEqual(7, len(document["render_cases"])); self.assertEqual(10, len(document["behavioral_mutation_ledger"]))
        self.assertEqual({"inputTex","renderScale","time","speed","alpha","rows","seed"}, set(document["source_uniform_abi"]))
        self.assertTrue(all(document["comparer_self_tests"].values()))
        for case in document["render_cases"]:
            count = case["width"] * case["height"] * 4
            self.assertEqual(count, len(case["output_f32_words_le"])); self.assertEqual(count, len(case["output_rgba8_bytes"])); self.assertTrue(case["distinct_storage"])
            self.assertTrue(case["input_immutable_exact_bits"] and case["input_lifetime_stable"] and case["public_direct_repeat_exact"])
        for mutation in document["behavioral_mutation_ledger"]:
            self.assertTrue(mutation["required_witnesses"]); self.assertTrue(all(x["mismatched_lanes"] > 0 and x["mismatched_bytes"] > 0 for x in mutation["required_witness_results"]))
    def test_sidecars_include_and_cxx_smoke_are_self_consistent(self):
        for path in (GENERATOR, MATERIALIZER, ORACLE, REPORT, INCLUDE):
            self.assertTrue(path.is_file(), path); self.assertEqual(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n", path.with_name(path.name+".sha256").read_text())
        text=INCLUDE.read_text();
        for marker in ("namespace noisemaker_spooky_ticker_oracle","kCases","kMutations","kMutationWitnesses","ControlRecord","input_f32_words","input_rgba8_bytes","output_f32_words","output_rgba8_bytes","tile_offset_words","full_resolution_words","kComparerSelfTests","distinct_storage"):
            self.assertIn(marker,text)
        source=Path(__file__).read_text(); self.assertNotRegex(source,r"/(?:private|Users|tmp)/")
        with tempfile.TemporaryDirectory(prefix="spooky-ticker-cxx-") as raw:
            unit=Path(raw)/"smoke.cpp"; unit.write_text('#include <array>\n#include <cstdint>\n#include <cstddef>\n#include "tests/oracles/spooky_ticker_expected.inc"\nint main(){static_assert(noisemaker_spooky_ticker_oracle::kCases.size()==7); static_assert(noisemaker_spooky_ticker_oracle::kMutations.size()==10); static_assert(noisemaker_spooky_ticker_oracle::kComparerSelfTests.hostile_dimension_guard); (void)noisemaker_spooky_ticker_oracle::kCases[0].controls.render_scale_word; (void)noisemaker_spooky_ticker_oracle::kCases[0].controls.tile_offset_words; (void)noisemaker_spooky_ticker_oracle::kCases[0].input_f32_words; (void)noisemaker_spooky_ticker_oracle::kCases[0].output_f32_words; (void)noisemaker_spooky_ticker_oracle::kMutationWitnesses[0].required_results;}\n')
            result=subprocess.run(["c++","-std=c++20","-I",str(ROOT),"-fsyntax-only",str(unit)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE); self.assertEqual(0,result.returncode,result.stderr)

if __name__ == "__main__": unittest.main()
