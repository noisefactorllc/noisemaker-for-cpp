from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "filter/median:median"
PACKAGE = ROOT / "docs/port-engineering/median-parity"
GENERATOR = PACKAGE / "median_oracle_generator.mjs"
ORACLE = PACKAGE / "median-oracles.json"
REPORT = PACKAGE / "median-oracle-report.md"
MATERIALIZER = ROOT / "tools/glslcpp/generate_median_native_oracle_include.py"
INCLUDE = ROOT / "tests/oracles/median_expected.inc"


def authority() -> pathlib.Path:
    configured = __import__("os").environ.get("NOISEMAKER_CPU_ROOT")
    if not configured:
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT unavailable")
    value = pathlib.Path(configured)
    if not value.is_dir():
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT unavailable")
    return value


class MedianFrontendPreparationTests(unittest.TestCase):
    def test_profile_is_prepared_and_identity_disjoint_for_all_radii(self):
        from tools.glslcpp.frontend import median_frontend_profile as profile
        for radius in profile.RADIUS_DEFINES:
            source_hash, program = profile.load_live_program(ROOT, radius)
            proof = profile.authenticate_median_frontend(program, source_hash, profile.PROFILE, radius)
            self.assertEqual(KEY, proof.program_key)
            self.assertEqual(profile.SOURCE_UNIFORMS, proof.source_uniforms)
            self.assertEqual(radius, proof.radius)
            self.assertEqual(len(proof.consumed_nodes), len({id(item) for item in proof.consumed_nodes}))
            self.assertIs(profile.verify_median_frontend(program, proof), proof)

    def test_profile_rejects_foreign_expression_and_radius(self):
        from tools.glslcpp.frontend import median_frontend_profile as profile
        source_hash, program = profile.load_live_program(ROOT, 2)
        proof = profile.authenticate_median_frontend(program, source_hash, profile.PROFILE, 2)
        with self.assertRaisesRegex(ValueError, "identity|closure"):
            profile.verify_median_frontend(program, proof._replace(expression_nodes=tuple(reversed(proof.expression_nodes))))
        target = next(item for item in proof.expression_nodes if item.kind == "binary" and item.operator == "<")
        mutated = profile.replace_expression(program, target, profile.dataclasses.replace(target, operator=">"))
        with self.assertRaisesRegex(ValueError, "fingerprint|census"):
            profile.authenticate_median_frontend(mutated, source_hash, profile.PROFILE, 2)
        with self.assertRaises(ValueError):
            profile.load_live_program(ROOT, 4)

    def test_prepared_registry_and_exact_emitter_blocker_are_explicit(self):
        from tools.glslcpp.frontend import median_frontend_profile as profile
        self.assertEqual((), profile.KEYS)
        self.assertEqual((KEY,), profile.PREPARED_KEYS)
        self.assertEqual(("inputTex", "sampler2D", "const Surface&"), profile.SAMPLER_RUNTIME_ABI)
        self.assertEqual("47:5: unsupported counted-for program proof", profile.CURRENT_EMITTER_BLOCKER)


class MedianOraclePreparationTests(unittest.TestCase):
    def test_oracle_package_has_strict_surfaces_closure_and_mutation_witnesses(self):
        for path in (GENERATOR, ORACLE, REPORT, MATERIALIZER, INCLUDE):
            self.assertTrue(path.is_file(), path)
            self.assertEqual(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n", pathlib.Path(f"{path}.sha256").read_text())
        document = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.median.pixel-parity.v1", document["schema"])
        self.assertEqual(KEY, document["program_key"])
        self.assertGreaterEqual(len(document["render_cases"]), 9)
        self.assertGreaterEqual(len(document["mutation_ledger"]), 4)
        self.assertTrue(all(document["comparer_self_tests"].values()))
        self.assertTrue(all(document["provenance"]["cpu_snapshot"][name] for name in ("realpath_containment_checked", "symlink_escape_rejected")))
        for case in document["render_cases"]:
            count = case["width"] * case["height"] * 4
            for label in ("input", "expected", "public_expected"):
                self.assertEqual(count, len(case[label]["f32_words_le"]))
                self.assertEqual(count, len(case[label]["rgba8_bytes"]))
            self.assertTrue(case["input_immutable_exact_bits"])
            self.assertTrue(case["public_direct_exact"])
            self.assertTrue(all(case["repeat"].values()))
        for mutation in document["mutation_ledger"]:
            self.assertTrue(mutation["required_witnesses"])
            self.assertTrue(all(result["mismatched_lanes"] > 0 and result["mismatched_bytes"] > 0 for result in mutation["required_witness_results"]))

    def test_standalone_generators_and_materializer_are_green(self):
        root = authority()
        for command in (("node", str(GENERATOR), "--check", "--cpu-root", str(root)), ("node", str(GENERATOR), "--self-test", "--cpu-root", str(root)), (sys.executable, "-B", str(MATERIALIZER), "--self-test"), (sys.executable, "-B", str(MATERIALIZER), "--check")):
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_materializer_rejects_dimension_and_digest_mutations(self):
        spec = __import__("importlib.util").util.spec_from_file_location("median_materializer", MATERIALIZER)
        module = __import__("importlib.util").util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
        document = json.loads(ORACLE.read_text())
        forged = copy.deepcopy(document); forged["render_cases"][0]["width"] += 1
        with self.assertRaises(module.MaterializationError): module.validate(forged)
        forged = copy.deepcopy(document); forged["render_cases"][0]["expected"]["f32_words_le"][0] = "0x00000000"
        with self.assertRaises(module.MaterializationError): module.validate(forged)

    def test_include_is_cxx20_wall_wextra_werror_smoke(self):
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None: self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="median-oracle-cxx-") as raw:
            unit = pathlib.Path(raw) / "smoke.cpp"
            unit.write_text('#include "tests/oracles/median_expected.inc"\nint main() { using namespace noisemaker_median_oracle; static_assert(kCases.size() >= 9U); static_assert(kMutations.size() >= 4U); return 0; }\n')
            result = subprocess.run((compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT), "-fsyntax-only", str(unit)), cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__": unittest.main()
