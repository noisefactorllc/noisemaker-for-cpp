from __future__ import annotations

import hashlib
import copy
import importlib.util
import json
import os
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/historic-palette-parity"
ORACLE = PACKAGE / "historic-palette-oracles.json"
GENERATOR = PACKAGE / "historic_palette_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_historic_palette_native_oracle_include.py"
INCLUDE = ROOT / "tests/oracles/historic_palette_expected.inc"
class HistoricPaletteOracleTests(unittest.TestCase):
    def _authority(self):
        raw = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not raw:
            self.skipTest("NOISEMAKER_CPU_ROOT is required for the frozen JS authority")
        authority = pathlib.Path(raw).resolve()
        self.assertTrue(authority.is_dir(), f"NOISEMAKER_CPU_ROOT is not a directory: {authority}")
        return authority

    def _materializer_module(self):
        spec = importlib.util.spec_from_file_location("historic_palette_materializer", MATERIALIZER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_no_task_run_specific_authority_path(self):
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        forbidden = "noisemaker-" + "cpp-continuation"
        self.assertNotIn(forbidden, source)

    def test_package_is_exact_and_covers_all_branches(self):
        doc = json.loads(ORACLE.read_text())
        self.assertEqual(doc["schema"], "noisemaker-for-cpp.historic-palette.pixel-parity.v1")
        self.assertEqual(doc["program_key"], "filter/historicPalette:historicPalette")
        self.assertEqual(doc["runtime_key"], doc["program_key"])
        self.assertTrue(doc["factory"]["adapter_own_key"])
        self.assertEqual(doc["provenance"]["cpu_snapshot"]["closure_cardinality"], 22)
        self.assertEqual(len(doc["provenance"]["cpu_snapshot"]["import_closure"]), 22)
        self.assertEqual(doc["runtime_binding_names"], ["tileOffset", "fullResolution", "inputTex", "paletteIndex", "smoothness", "rotation", "offset", "repeat", "alpha", "time"])
        self.assertEqual(len(doc["render_cases"]), 21)
        self.assertEqual(sorted({case["bindings"]["paletteIndex"] for case in doc["render_cases"]}), list(range(21)))
        self.assertEqual({case["bindings"]["rotation"] for case in doc["render_cases"]}, {-1, 0, 1})
        self.assertIn(0, {case["bindings"]["smoothness"] for case in doc["render_cases"]})
        self.assertTrue(any(case["bindings"]["smoothness"] > 0 for case in doc["render_cases"]))
        self.assertEqual(doc["exactness_contract"]["tolerance"], "none")
        self.assertTrue(doc["comparer_self_tests"]["raw_words_and_rgba8_independent"])
        self.assertGreaterEqual(doc["mutation_anchor_cardinality"]["total"], 6)
        self.assertTrue(all(row["required_witnesses"] for row in doc["mutation_ledger"]))
        self.assertTrue(all("input_f32_words_le" in case and "binding_words" in case for case in doc["render_cases"]))
        self.assertTrue(all(len(case["input_f32_words_le"]) == case["width"] * case["height"] * 4 for case in doc["render_cases"]))
        self.assertEqual(set(doc["render_cases"][0]["binding_words"]), {"tileOffset", "fullResolution", "paletteIndex", "smoothness", "rotation", "offset", "repeat", "alpha", "time", "inputTex"})
        self.assertTrue(all("f32_words_le" in value or "int32" in value or "width" in value for value in doc["render_cases"][0]["binding_words"].values()))
        self.assertGreater(len({tuple(case["bindings"]["tileOffset"]) for case in doc["render_cases"]}), 1)
        self.assertGreater(len({tuple(case["bindings"]["fullResolution"]) for case in doc["render_cases"]}), 1)
        for name in ("smoothness", "rotation", "offset", "repeat", "alpha", "time"):
            self.assertGreater(len({case["bindings"][name] for case in doc["render_cases"]}), 1, name)

    def test_generator_check_self_test_and_materializer(self):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        authority = self._authority()
        check = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(authority)], cwd=ROOT, text=True, capture_output=True, env=env)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn("historic palette oracle: ok", check.stdout)
        self_test = subprocess.run(["node", str(GENERATOR), "--self-test", "--cpu-root", str(authority)], cwd=ROOT, text=True, capture_output=True, env=env)
        self.assertEqual(self_test.returncode, 0, self_test.stdout + self_test.stderr)
        materializer = subprocess.run(["python3", "-B", str(MATERIALIZER), "--check"], cwd=ROOT, text=True, capture_output=True, env=env)
        self.assertEqual(materializer.returncode, 0, materializer.stdout + materializer.stderr)
        self.assertIn("historic palette materializer: ok", materializer.stdout)

    def test_generator_self_test_rejects_symlink_escape(self):
        authority = self._authority()
        result = subprocess.run(
            ["node", str(GENERATOR), "--self-test", "--cpu-root", str(authority)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("symlink confinement", result.stdout)

    def test_materializer_include_is_hash_bound_and_cxx20_parseable(self):
        sidecar = INCLUDE.with_name(INCLUDE.name + ".sha256")
        expected = f"{hashlib.sha256(INCLUDE.read_bytes()).hexdigest()}  {INCLUDE.name}\n"
        self.assertEqual(sidecar.read_text(), expected)
        compiler = subprocess.run(["c++", "-std=c++20", "-I", str(ROOT), "-x", "c++", "-fsyntax-only", "-"], input=f'#include "tests/oracles/{INCLUDE.name}"\nint main() {{ using namespace historic_palette_oracle; static_assert(kCases.size() == 21U); return 0; }}\n', cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(compiler.returncode, 0, compiler.stdout + compiler.stderr)
        self.assertIn("kInput", INCLUDE.read_text())
        self.assertIn("kBindingWords", INCLUDE.read_text())
        smoke = '#include "tests/oracles/historic_palette_expected.inc"\nint main() { using namespace historic_palette_oracle; static_assert(kCases[0].input_f32_words.size() == 80U); static_assert(kCases[0].binding_words.palette_index == 0); static_assert(kCases[1].binding_words.rotation == 0); static_assert(kCases[0].binding_words.input_width == 5U); static_assert(kCases[0].input_immutable_exact_bits); static_assert(kCases[0].input_surface_not_released); static_assert(kCases[0].input_storage_independent); return 0; }\n'
        smoke_result = subprocess.run(["c++", "-std=c++20", "-I", str(ROOT), "-x", "c++", "-fsyntax-only", "-"], input=smoke, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(smoke_result.returncode, 0, smoke_result.stdout + smoke_result.stderr)

    def test_materializer_rejects_input_and_binding_sabotage(self):
        module = self._materializer_module()
        document = json.loads(ORACLE.read_text())
        for mutate in (
            lambda bad: bad["render_cases"][0]["input_f32_words_le"].__setitem__(0, "0x00000000"),
            lambda bad: bad["render_cases"][1]["binding_words"]["smoothness"]["f32_words_le"].__setitem__(0, "0x00000000"),
            lambda bad: bad["render_cases"][0]["binding_words"].pop("time"),
        ):
            forged = copy.deepcopy(document)
            mutate(forged)
            with self.assertRaises(module.MaterializationError):
                module.validate(forged)

if __name__ == "__main__":
    unittest.main()
