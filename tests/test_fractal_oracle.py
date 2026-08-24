from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/fractal-parity"
GENERATOR = PACKAGE / "fractal_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_fractal_native_oracle_include.py"
ORACLE = PACKAGE / "fractal-oracles.json"
REPORT = PACKAGE / "fractal-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/fractal_expected.inc"
EXPECTED_UPSTREAM = "117a236679d1db3ab8f0e278230ece277b57564c"
EXPECTED_AUTHORITY_PROVENANCE = "<external-authority-root>"
EXPECTED_CLOSURE_SHA256 = "b16cbd8716cab226271041751af6431bfe48fef1c0826bba89544a0f4bf525f5"


def f32_word(value: str) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', float(value)))[0]:08x}"


def f32_value(value: str) -> float:
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def module():
    spec = importlib.util.spec_from_file_location("fractal_materializer", MATERIALIZER)
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


class FractalOracleTests(unittest.TestCase):
    def test_package_and_sidecars(self):
        for path in (GENERATOR, ORACLE, REPORT, INCLUDE):
            self.assertTrue(path.is_file(), path)
            sidecar = Path(f"{path}.sha256")
            self.assertEqual(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n",
                sidecar.read_text())
        doc = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.fractal.pixel-parity.v1", doc["schema"])
        self.assertEqual("classicNoisedeck/fractal:fractal", doc["program_key"])
        self.assertEqual(9, len(doc["render_cases"]))
        self.assertEqual(5, len(doc["mutation_ledger"]))
        self.assertEqual(EXPECTED_UPSTREAM, doc["upstream_revision"])
        snapshot = doc["provenance"]["cpu_snapshot"]
        self.assertEqual(EXPECTED_AUTHORITY_PROVENANCE, snapshot["root_realpath"])
        self.assertEqual(EXPECTED_CLOSURE_SHA256, snapshot["import_closure_sha256"])
        self.assertEqual(22, len(snapshot["import_closure"]))
        self.assertEqual("julia:261:5-269:6", doc["claim_boundaries"]["first_blocker_span"])
        cases = {case["name"]: case for case in doc["render_cases"]}
        self.assertEqual(0, cases["julia-distance-mode1"]["bindings"]["type"])
        self.assertEqual(1, cases["julia-distance-mode1"]["bindings"]["mode"])
        self.assertEqual(2, cases["mandelbrot-distance-mode1"]["bindings"]["type"])
        self.assertEqual(1, cases["mandelbrot-distance-mode1"]["bindings"]["mode"])
        adversarial = cases["julia-near-escape-nonrepresentable"]
        self.assertEqual(1, adversarial["bindings"]["mode"])
        self.assertEqual([3, -2], adversarial["bindings"]["tileOffset"])
        self.assertEqual([17, 13], adversarial["bindings"]["fullResolution"])
        self.assertEqual(-25, adversarial["bindings"]["centerX"])
        self.assertEqual(67, adversarial["bindings"]["centerY"])
        self.assertEqual([5, 1], doc["adversarial_witness"]["pixel"])
        self.assertEqual(56, doc["adversarial_witness"]["lane_index"])
        self.assertEqual([8, -1], doc["adversarial_witness"]["global_coord_number"])
        witness = doc["adversarial_witness"]
        recorded_numbers = [*witness["normalized_coord_number"],
                            *witness["initial_state_number"],
                            *witness["next_state_number"]]
        self.assertTrue(all(word.startswith("0x") and len(word) == 10
                            for word in [f32_word(value) for value in recorded_numbers]))
        self.assertTrue(all(f32_value(value) != float(value)
                            for value in recorded_numbers))
        next_state = [float(value) for value in witness["next_state_number"]]
        radius2 = next_state[0] * next_state[0] + next_state[1] * next_state[1]
        self.assertEqual(float(witness["escape_radius2"]), radius2)
        self.assertEqual(float(witness["escape_margin"]), radius2 - 4.0)
        self.assertEqual("0x3f75d177", doc["adversarial_witness"]["expected_f32_word"])
        self.assertEqual(245, doc["adversarial_witness"]["expected_rgba8_byte"])
        self.assertNotEqual(adversarial["bindings"]["fullResolution"][0] / adversarial["bindings"]["fullResolution"][1],
                            round(adversarial["bindings"]["fullResolution"][0] / adversarial["bindings"]["fullResolution"][1]))
        self.assertTrue(all(m["independent"] for m in doc["mutation_ledger"]))
        self.assertTrue(all(r["changed_float32_lanes"] and r["changed_rgba8_bytes"]
                            for m in doc["mutation_ledger"] for r in m["results"]))

    def test_materializer_self_test_and_check(self):
        for args in (("--self-test",), ("--check",)):
            result = subprocess.run(
                [sys.executable, str(MATERIALIZER), *args], cwd=ROOT,
                env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
                text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_materializer_rejects_forged_mutation(self):
        loaded = module()
        doc = json.loads(ORACLE.read_text())
        mutations = [
            lambda candidate: candidate["mutation_ledger"][0].__setitem__("independent", False),
            lambda candidate: candidate.__setitem__("upstream_revision", "forged"),
            lambda candidate: candidate["provenance"]["cpu_snapshot"].__setitem__("root_realpath", "/tmp/forged"),
            lambda candidate: candidate["provenance"]["cpu_snapshot"].__setitem__("import_closure_sha256", "0" * 64),
            lambda candidate: candidate["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__("sha256", "0" * 64),
            lambda candidate: candidate["adversarial_witness"].__setitem__("escape_margin", "0"),
        ]
        for mutate in mutations:
            candidate = json.loads(json.dumps(doc))
            mutate(candidate)
            with self.assertRaises(loaded.MaterializationError):
                loaded.validate(candidate)

    def test_generator_accepts_identical_copy_and_rejects_mutated_copy(self):
        source_root = os.environ.get("NOISEMAKER_CPU_AUTHORITY_ROOT")
        if not source_root:
            self.skipTest("NOISEMAKER_CPU_AUTHORITY_ROOT is required for authority-copy test")
        with tempfile.TemporaryDirectory(prefix="fractal-authority-", dir="/private/tmp") as directory:
            clone = Path(directory) / "cpu"
            shutil.copytree(source_root, clone)
            accepted = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(clone)],
                cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
            self.assertIn("fractal oracle check passed", accepted.stdout)
            target = clone / "src/effects/generated/upstream-snapshot.js"
            target.write_text(target.read_text() + "\n// forged closure mutation\n")
            result = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(clone)],
                cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("authority import closure mismatch", result.stderr)

    def test_include_compiles_as_cxx20(self):
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="fractal-oracle-") as directory:
            unit = Path(directory) / "smoke.cpp"
            unit.write_text(
                '#include "tests/oracles/fractal_expected.inc"\n'
                "int main() {\n"
                "  static_assert(fractal_oracle::kCases.size() == 9);\n"
                "  static_assert(fractal_oracle::kCase0F32.size() == 192);\n"
                "  static_assert(fractal_oracle::kCase0Rgba8.size() == 192);\n"
                "  static_assert(fractal_oracle::kCase8F32.size() == 180);\n"
                "  static_assert(fractal_oracle::kCase8Rgba8.size() == 180);\n"
                "  static_assert(fractal_oracle::kCase8F32[56] == 0x3f75d177U);\n"
                "  static_assert(fractal_oracle::kCase8Rgba8[56] == 245U);\n"
                "  return fractal_oracle::kCases[8].width == 9U ? 0 : 1;\n"
                "}\n")
            result = subprocess.run(
                [compiler, "-std=c++20", "-I", str(ROOT), "-fsyntax-only", str(unit)],
                cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
