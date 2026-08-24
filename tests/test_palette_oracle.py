from __future__ import annotations

import hashlib
import json
import os
import pathlib
import copy
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/palette-parity"
GENERATOR = PACKAGE / "palette_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_palette_native_oracle_include.py"
ORACLE = PACKAGE / "palette-oracles.json"
REPORT = PACKAGE / "palette-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/palette_expected.inc"


def _authority() -> pathlib.Path:
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not value or not pathlib.Path(value).is_dir():
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT unavailable")
    return pathlib.Path(value)


class PaletteOracleTests(unittest.TestCase):
    def test_package_contract_and_sidecars(self):
        for path in (GENERATOR, MATERIALIZER, ORACLE, REPORT, INCLUDE):
            self.assertTrue(path.is_file(), path)
            sidecar = pathlib.Path(f"{path}.sha256")
            self.assertEqual(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n",
                             sidecar.read_text())
        document = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.palette.pixel-parity.v1", document["schema"])
        self.assertEqual("filter/palette:palette", document["program_key"])
        self.assertEqual("paletteFactory", document["factory"]["name"])
        self.assertTrue(document["factory"]["adapter_own_key"])
        self.assertTrue(document["factory"]["public_factory_is_direct_identity"])
        self.assertEqual(22, len(document["provenance"]["cpu_snapshot"]["import_closure"]))
        self.assertGreaterEqual(len(document["render_cases"]), 8)
        self.assertGreaterEqual(len(document["mutation_ledger"]), 12)
        self.assertTrue(all(document["comparer_self_tests"].values()))
        self.assertIn("signed_zero", document["comparer_self_tests"])
        self.assertIn("nan_payload", document["comparer_self_tests"])
        self.assertEqual(
            {"inputTex", "tileOffset", "fullResolution", "paletteIndex", "rotation", "offset", "repeat", "alpha", "time"},
            set(document["runtime_binding_names"]),
        )
        for case in document["render_cases"]:
            size = case["width"] * case["height"] * 4
            self.assertEqual(size, len(case["expected"]["f32_words_le"]))
            self.assertEqual(size, len(case["expected"]["rgba8_bytes"]))
            self.assertEqual(size, len(case["input"]["f32_words_le"]))
            self.assertEqual(
                {"inputTex", "tileOffset", "fullResolution", "paletteIndex", "rotation", "offset", "repeat", "alpha", "time"},
                set(case["binding_words"]),
            )
            self.assertEqual(case["binding_words"]["inputTex"]["f32_words_le"], case["input"]["f32_words_le"])
            for name in ("offset", "repeat", "alpha", "time"):
                self.assertEqual(1, len(case["binding_words"][name]["f32_words_le"]))
            for name in ("paletteIndex", "rotation"):
                self.assertEqual(1, len(case["binding_words"][name]["f32_words_le"]))
            self.assertTrue(case["input_immutable_exact_bits"])
            self.assertTrue(case["repeat_output_object_distinct"])
            self.assertTrue(case["repeat_output_data_distinct"])
        for mutation in document["mutation_ledger"]:
            self.assertTrue(mutation["required_witnesses"])
            self.assertTrue(all(result["mismatched_lanes"] > 0 and result["mismatched_bytes"] > 0
                                for result in mutation["required_witness_results"]))

    def test_generator_and_materializer(self):
        authority = _authority()
        for command in (
            ["node", str(GENERATOR), "--check", "--cpu-root", str(authority)],
            ["node", str(GENERATOR), "--self-test", "--cpu-root", str(authority)],
            [sys.executable, "-B", str(MATERIALIZER), "--self-test"],
            [sys.executable, "-B", str(MATERIALIZER), "--check"],
        ):
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_comparer_checks_dimensions_before_storage_access(self):
        authority = _authority()
        result = subprocess.run(
            ["node", str(GENERATOR), "--self-test", "--cpu-root", str(authority)],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("dimension validation precedes storage access", result.stdout)

    def test_include_compiles_as_cxx20(self):
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="palette-oracle-cxx-") as raw:
            unit = pathlib.Path(raw) / "smoke.cpp"
            unit.write_text('#include "tests/oracles/palette_expected.inc"\n'
                            'int main() { using namespace noisemaker_palette_oracle; '
                            'static_assert(kCases.size() >= 8U); '
                            'static_assert(kCases[0].input_f32_words.size() == 48U); '
                            'static_assert(kCases[0].binding_words.palette_index == 0); '
                            'static_assert(kCases[0].binding_words.input_width == 4U); '
                            'static_assert(kCases[0].input_immutable_exact_bits); '
                            'static_assert(kMutations.size() >= 12U); return 0; }\n')
            result = subprocess.run([compiler, "-std=c++20", "-I", str(ROOT),
                                     "-fsyntax-only", str(unit)], cwd=ROOT,
                                    text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_materializer_rejects_replay_input_binding_and_cardinality_sabotage(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("palette_materializer", MATERIALIZER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        document = json.loads(ORACLE.read_text())
        probes = []
        forged = copy.deepcopy(document); forged["render_cases"][0]["input"]["f32_words_le"][0] = "0x00000000"; probes.append(forged)
        forged = copy.deepcopy(document); forged["render_cases"][1]["binding_words"]["offset"]["f32_words_le"][0] = "0x00000000"; probes.append(forged)
        forged = copy.deepcopy(document); forged["render_cases"][0]["binding_words"].pop("time"); probes.append(forged)
        forged = copy.deepcopy(document); forged["render_cases"][0]["binding_words"]["inputTex"]["width"] = 1; probes.append(forged)
        for candidate in probes:
            with self.assertRaises(module.MaterializationError):
                module.validate(candidate)


if __name__ == "__main__":
    unittest.main()
