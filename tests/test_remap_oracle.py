from __future__ import annotations

import json
import importlib.util
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "docs/port-engineering/remap-parity/remap_oracle_generator.mjs"
CPU = pathlib.Path(os.environ["NOISEMAKER_CPU_ROOT"]) if os.environ.get("NOISEMAKER_CPU_ROOT") else None
LIVE = pathlib.Path(os.environ["NOISEMAKER_FOR_CPU"]) if os.environ.get("NOISEMAKER_FOR_CPU") else None
TMP_ROOTS = (pathlib.Path(os.sep) / "tmp", pathlib.Path(os.sep) / "private" / "tmp")


class RemapOracleTests(unittest.TestCase):
    def node(self, *args, env=None):
        if LIVE is None:
            raise unittest.SkipTest("NOISEMAKER_FOR_CPU is not configured")
        merged = os.environ.copy()
        merged["NOISEMAKER_FOR_CPU"] = str(LIVE)
        if env:
            merged.update(env)
        return subprocess.run(
            ["node", str(GENERATOR), *args], cwd=ROOT, env=merged,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )

    def test_authority_generator_and_materializer(self):
        if CPU is None or LIVE is None or not CPU.is_dir() or not LIVE.is_dir():
            self.skipTest("authority fixture is not available")
        checked = self.node("--check", "--cpu-root", str(CPU))
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertIn("10 cases, 7 mutations", checked.stdout)
        materializer = subprocess.run(
            ["python3", "-B", "tools/glslcpp/generate_remap_native_oracle_include.py", "--check"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(0, materializer.returncode, materializer.stderr)

    def test_unset_authority_fails_closed(self):
        if CPU is None or not CPU.is_dir():
            self.skipTest("NOISEMAKER_CPU_ROOT is not configured")
        env = os.environ.copy()
        env.pop("NOISEMAKER_FOR_CPU", None)
        env.pop("NOISEMAKER_CPU_ROOT", None)
        result = subprocess.run(
            ["node", str(GENERATOR), "--check", "--cpu-root", str(CPU)],
            cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("live checkout", result.stderr)

    def test_tmp_and_private_tmp_authority_leaf_symlinks_rejected(self):
        if CPU is None or LIVE is None or not CPU.is_dir() or not LIVE.is_dir():
            self.skipTest("authority fixture is not available")
        for base in TMP_ROOTS:
            if not base.is_dir():
                self.skipTest(f"temporary root is unavailable: {base}")
            with tempfile.TemporaryDirectory(prefix="remap-authority-", dir=str(base)) as td:
                alias = pathlib.Path(td) / "alias"
                alias.symlink_to(CPU, target_is_directory=True)
                result = self.node("--check", "--cpu-root", str(alias))
                self.assertNotEqual(0, result.returncode)
                self.assertIn("non-symlink", result.stderr)

    def test_document_has_exact_source_and_runtime_contract(self):
        document = json.loads((ROOT / "docs/port-engineering/remap-parity/remap-oracles.json").read_text())
        self.assertEqual("synth/remap:remap", document["program_key"])
        self.assertEqual(22, len(document["provenance"]["cpu_snapshot"]["import_closure"]))
        self.assertEqual(10, len(document["render_cases"]))
        self.assertEqual(7, len(document["mutation_ledger"]))
        self.assertTrue(all(item["witness_cases"] for item in document["mutation_ledger"]))
        self.assertTrue(all(any(r["changed_float32_lanes"] and r["changed_rgba8_bytes"] for r in item["results"]) for item in document["mutation_ledger"]))
        active_zone_indices = {i for case in document["render_cases"] for i, zone in enumerate(case["controls"]["zones"]) if zone["active"]}
        self.assertTrue(set(range(8)).issubset(active_zone_indices))
        self.assertTrue(any(any(zone["active"] and zone["count"] < 3 for zone in case["controls"]["zones"]) for case in document["render_cases"]))

    def test_materializer_duplicate_key_and_matching_sidecar_forgery_rejected(self):
        materializer = ROOT / "tools/glslcpp/generate_remap_native_oracle_include.py"
        duplicate = '{"schema":1,"schema":2}'
        self.assertEqual(json.loads(duplicate, object_pairs_hook=lambda pairs: pairs), [("schema", 1), ("schema", 2)])
        result = subprocess.run(["python3", "-B", str(materializer), "--self-test"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("64 matching-sidecar forgery probes", result.stdout)

    def test_materializer_rejects_matching_sidecar_include_forgery(self):
        materializer_path = ROOT / "tools/glslcpp/generate_remap_native_oracle_include.py"
        spec = importlib.util.spec_from_file_location("remap_materializer", materializer_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        document = module.validate(module.checked_payload(module.ORACLE))
        expected = module.emit(document).encode()
        with tempfile.TemporaryDirectory(prefix="remap-include-forgery-test-") as td:
            forged = pathlib.Path(td) / "remap_expected.inc"
            forged_bytes = expected + b"\n// recomputed sidecar forge\n"
            forged.write_bytes(forged_bytes)
            forged.with_name(forged.name + ".sha256").write_text(module.sidecar(forged, forged_bytes))
            with self.assertRaises(module.OracleError):
                module.checked_target(document, forged)

    def test_generator_self_test_rejects_nonliteral_import_forms(self):
        if CPU is None or LIVE is None or not CPU.is_dir() or not LIVE.is_dir():
            self.skipTest("authority fixture is not available")
        checked = self.node("--self-test", "--cpu-root", str(CPU))
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertIn("imports", checked.stdout)

    def test_native_include_exposes_controls_alpha_and_witnesses(self):
        source = r'''#include "tests/oracles/remap_expected.inc"
int main() {
  const auto& c = remap_oracle::kCases[0];
  (void)c.controls.bg_color;
  (void)c.controls.bg_alpha;
  (void)c.controls.smooth_edge;
  (void)c.controls.zone_count;
  (void)c.controls.tile_offset;
  (void)c.controls.full_resolution;
  (void)c.controls.zones;
  (void)c.output_alpha_float_words;
  (void)c.output_alpha_rgba8_bytes;
  const auto& result = remap_oracle::kMutation0Results[0];
  (void)result.float32_witness.index;
  (void)result.float32_witness.expected;
  (void)result.rgba8_witness.actual;
  (void)remap_oracle::kMutations[0].witness_cases;
  return 0;
}
'''
        completed = subprocess.run(["c++", "-std=c++20", "-I", str(ROOT), "-x", "c++", "-fsyntax-only", "-"], input=source, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
