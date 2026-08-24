from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


PACKAGE = ROOT / "docs/port-engineering/classic-noise-parity"
GENERATOR = PACKAGE / "classic_noise_oracle_generator.mjs"
ORACLE = PACKAGE / "classic-noise-oracles.json"
REPORT = PACKAGE / "classic-noise-oracle-report.md"
MATERIALIZER = ROOT / "tools/glslcpp/generate_classic_noise_native_oracle_include.py"
INCLUDE = ROOT / "tests/oracles/classic_noise_expected.inc"
AUTHORITY = Path("/private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu")
LIVE = Path("/Users/aayars/platform/noisemaker-for-cpu")


def checked(path):
    payload = path.read_bytes()
    assert Path(f"{path}.sha256").read_text() == f"{hashlib.sha256(payload).hexdigest()}  {path.name}\n"
    return payload


def materializer_module():
    spec = importlib.util.spec_from_file_location("classic_noise_materializer", MATERIALIZER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_classic_noise_oracle_package_exists():
    package = ROOT / "docs/port-engineering/classic-noise-parity"
    for path in (GENERATOR, ORACLE, REPORT, MATERIALIZER, INCLUDE):
        assert path.is_file()
        checked(path)


def test_schema_abi_cases_and_dead_binding_invariance():
    document = json.loads(ORACLE.read_text())
    assert document["schema"] == "noisemaker-for-cpp.classic-noise.pixel-parity.v1"
    assert document["program_key"] == "classicNoisedeck/noise:noise"
    assert document["defines"] == {"NOISE_TYPE": 10, "REFRACT_MODE": 2, "LOOP_OFFSET": 300, "METRIC": 0, "COLOR_MODE": 6}
    assert len(document["runtime_binding_names"]) == 29
    assert len(document["render_cases"]) == 8
    assert len(document["mutation_ledger"]) == 5
    assert document["render_cases"][-2]["expected"] == document["render_cases"][-1]["expected"]
    for case in document["render_cases"]:
        count = case["width"] * case["height"] * 4
        assert len(case["expected"]["f32_words_le"]) == count
        assert len(case["expected"]["rgba8_bytes"]) == count
        assert case["repeat"]["exact"] and case["storage"]["distinct_f32_backing_stores"]
        assert case["controls_snapshot"]["unchanged"]
    for mutation in document["mutation_ledger"]:
        assert mutation["independent"] and mutation["anchor_cardinality"] == 1
        rows = {row["case"]: row for row in mutation["results"]}
        assert all(rows[name]["changed_float32_lanes"] > 0 and rows[name]["changed_rgba8_bytes"] > 0 for name in mutation["witnesses"])


class ClassicNoiseOracleTests(unittest.TestCase):
    def test_generator_check_and_self_test(self):
        if not AUTHORITY.is_dir() or not LIVE.is_dir():
            self.skipTest("immutable or live CPU authority unavailable")
        env = {**os.environ, "NOISEMAKER_FOR_CPU": str(LIVE)}
        for mode in ("--check", "--self-test"):
            result = subprocess.run(["node", str(GENERATOR), mode, "--cpu-root", str(AUTHORITY)], cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_generator_rejects_unset_wrong_and_same_authority(self):
        if not AUTHORITY.is_dir():
            self.skipTest("immutable CPU authority unavailable")
        base = os.environ.copy()
        base.pop("NOISEMAKER_FOR_CPU", None)
        unset = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(AUTHORITY)], cwd=ROOT, env=base, text=True, capture_output=True)
        self.assertNotEqual(0, unset.returncode)
        wrong = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(AUTHORITY)], cwd=ROOT, env={**base, "NOISEMAKER_FOR_CPU": str(ROOT)}, text=True, capture_output=True)
        self.assertNotEqual(0, wrong.returncode)
        same = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(AUTHORITY)], cwd=ROOT, env={**base, "NOISEMAKER_FOR_CPU": str(AUTHORITY)}, text=True, capture_output=True)
        self.assertNotEqual(0, same.returncode)

    def test_materializer_check_and_self_test(self):
        for mode in ("--check", "--self-test"):
            result = subprocess.run([sys.executable, "-B", str(MATERIALIZER), mode], cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_materializer_rejects_forged_identity_payload_and_mutation(self):
        module = materializer_module()
        with self.assertRaises(module.OracleError):
            module.strict_json(b'{"duplicate":1,"duplicate":2}')
        baseline = json.loads(ORACLE.read_text())
        for mutate in (
            lambda d: d.__setitem__("schema", "forged"),
            lambda d: d["factory"].__setitem__("text_sha256", "0" * 64),
            lambda d: d["comparer_self_tests"].__setitem__("forged", True),
            lambda d: d["defines"].__setitem__("COLOR_MODE", 2),
            lambda d: d["runtime_binding_names"].__setitem__(0, "forged"),
            lambda d: d["render_cases"][0]["expected"]["f32_words_le"].__setitem__(0, "0x00000000"),
            lambda d: d["render_cases"].pop(),
            lambda d: d["mutation_ledger"][0].__setitem__("independent", False),
            lambda d: d["authority"]["import_closure"].pop(),
        ):
            candidate = copy.deepcopy(baseline)
            mutate(candidate)
            with self.assertRaises(module.OracleError):
                module.validate(candidate)

    def test_generated_include_compiles_and_reports_cardinalities(self):
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="classic-noise-oracle-cxx-") as raw:
            unit = Path(raw) / "smoke.cpp"
            unit.write_text('#include "tests/oracles/classic_noise_expected.inc"\n#include <cassert>\nint main() { assert(noisemaker_classic_noise_oracle::kCases.size() == 8); assert(noisemaker_classic_noise_oracle::kRuntimeBindings.size() == 29); assert(noisemaker_classic_noise_oracle::kMutations.size() == 5); return 0; }\n')
            result = subprocess.run([compiler, "-std=c++20", "-I", str(ROOT), str(unit), "-o", str(Path(raw) / "smoke")], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            run = subprocess.run([str(Path(raw) / "smoke")], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, run.returncode, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
