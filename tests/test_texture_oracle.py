from __future__ import annotations

import copy
import hashlib
import os
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/texture-parity"
GENERATOR = PACKAGE / "texture_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_texture_native_oracle_include.py"
ORACLE = PACKAGE / "texture-oracles.json"
REPORT = PACKAGE / "texture-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/texture_expected.inc"


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authority() -> pathlib.Path:
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not value or not pathlib.Path(value).is_dir():
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT unavailable")
    return pathlib.Path(value)


class TextureOracleTests(unittest.TestCase):
    def test_package_sidecars_and_contract(self):
        for path in (GENERATOR, MATERIALIZER, ORACLE, REPORT, INCLUDE):
            self.assertTrue(path.is_file(), path)
            self.assertEqual(f"{sha(path)}  {path.name}\n",
                             path.with_name(path.name + ".sha256").read_text())
        document = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.texture.pixel-parity.v1", document["schema"])
        self.assertEqual("filter/texture:texture", document["program_key"])
        self.assertEqual(8, len(document["render_cases"]))
        self.assertEqual(4, len(document["mutation_ledger"]))
        self.assertTrue(all(document["comparer_self_tests"].values()))
        self.assertEqual("int32", document["runtime_binding_abi"]["MODE"])
        for case in document["render_cases"]:
            size = case["width"] * case["height"] * 4
            self.assertEqual(size, len(case["expected"]["f32_words_le"]))
            self.assertEqual(size, len(case["expected"]["rgba8_bytes"]))
            self.assertTrue(case["input_immutable_exact_bits"])
            self.assertTrue(case["public_direct_exact"])
            self.assertTrue(all(case["repeat"].values()))
        for mutation in document["mutation_ledger"]:
            self.assertTrue(mutation["independent"])
            self.assertTrue(mutation["required_witnesses"])
            self.assertTrue(all(result["mismatched_lanes"] > 0 and result["mismatched_bytes"] > 0
                                for result in mutation["required_witness_results"]))

    def test_generator_and_materializer_strict_modes(self):
        root = authority()
        for command in (
                ["node", str(GENERATOR), "--check", "--cpu-root", str(root)],
                ["node", str(GENERATOR), "--self-test", "--cpu-root", str(root)],
                [sys.executable, "-B", str(MATERIALIZER), "--self-test"],
                [sys.executable, "-B", str(MATERIALIZER), "--check"]):
            result = subprocess.run(command, cwd=ROOT, text=True,
                                    capture_output=True, env={**__import__("os").environ,
                                                              "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_materializer_rejects_digest_and_witness_forgery(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("texture_materializer", MATERIALIZER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        baseline = json.loads(ORACLE.read_text())
        forged = copy.deepcopy(baseline)
        forged["render_cases"][0]["expected"]["f32_words_le"][0] = "0x00000000"
        with self.assertRaises(module.MaterializationError):
            module.validate(forged)
        forged = copy.deepcopy(baseline)
        forged["mutation_ledger"][0]["required_witness_results"][0]["mismatched_lanes"] = 0
        with self.assertRaises(module.MaterializationError):
            module.validate(forged)

    def test_include_compiles_as_cxx20(self):
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="texture-oracle-cxx-") as raw:
            unit = pathlib.Path(raw) / "smoke.cpp"
            unit.write_text('#include "tests/oracles/texture_expected.inc"\n'
                            'int main() { using namespace noisemaker_texture_oracle; '
                            'static_assert(kCases.size() == 8U); '
                            'static_assert(kMutations.size() == 4U); return 0; }\n')
            result = subprocess.run([compiler, "-std=c++20", "-I", str(ROOT),
                                     "-fsyntax-only", str(unit)], cwd=ROOT,
                                    text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
