from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
KEY = "classicNoisedeck/colorLab:colorLab"
PACKAGE = ROOT / "docs/port-engineering/color-lab-parity"
GENERATOR = PACKAGE / "color_lab_oracle_generator.mjs"
ORACLE = PACKAGE / "colorLab-oracles.json"
REPORT = PACKAGE / "colorLab-oracle-report.md"
MATERIALIZER = ROOT / "tools/glslcpp/generate_colorLab_native_oracle_include.py"
INCLUDE = ROOT / "tests/oracles/colorLab_expected.inc"


def _authority() -> pathlib.Path:
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not value or not pathlib.Path(value).is_dir():
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT unavailable")
    return pathlib.Path(value)


class ColorLabFrontendPreparationTests(unittest.TestCase):
    def test_profile_is_landed_with_identity_disjoint_live_closure(self):
        from tools.glslcpp.frontend import color_lab_frontend_profile as profile
        source_hash, program = profile.load_live_program(ROOT)
        proof = profile.authenticate_color_lab_frontend(
            program, source_hash, profile.PROFILE)
        self.assertEqual(KEY, proof.program_key)
        self.assertEqual(profile.KEYS, (KEY,))
        self.assertEqual(profile.PREPARED_KEYS, ())
        self.assertEqual(profile.SOURCE_UNIFORMS, proof.source_uniforms)
        self.assertEqual(profile.RUNTIME_UNIFORM_ABI, proof.runtime_uniform_abi)
        self.assertEqual(profile.FUNCTION_NAMES, tuple(f.name for f in proof.functions))
        self.assertGreater(len(proof.consumed_nodes), 100)
        self.assertEqual(len(proof.consumed_nodes), len({id(x) for x in proof.consumed_nodes}))
        self.assertIs(profile.verify_color_lab_frontend(program, proof), proof)

    def test_profile_rejects_foreign_function_and_operator_mutations(self):
        from tools.glslcpp.frontend import color_lab_frontend_profile as profile
        source_hash, program = profile.load_live_program(ROOT)
        proof = profile.authenticate_color_lab_frontend(
            program, source_hash, profile.PROFILE)
        with self.assertRaisesRegex(ValueError, "function identity"):
            profile.verify_color_lab_frontend(
                program, proof._replace(functions=tuple(reversed(proof.functions))))
        target = next(node for node in proof.operator_nodes if node.operator == "*")
        mutated = profile.replace_expression(program, target,
                                              profile.dataclasses.replace(target, operator="+"))
        with self.assertRaisesRegex(ValueError, "fingerprint|operator|source"):
            profile.authenticate_color_lab_frontend(mutated, source_hash, profile.PROFILE)

    def test_runtime_index_and_abi_requirements_are_narrow_and_landed(self):
        from tools.glslcpp.frontend import color_lab_frontend_profile as profile
        self.assertEqual((KEY,), profile.KEYS)
        self.assertEqual((), profile.PREPARED_KEYS)
        self.assertEqual(("inputTex", "sampler2D", "const Surface&"), profile.SAMPLER_RUNTIME_ABI)
        self.assertEqual(("gl_FragCoord", "tileOffset", "fullResolution", "textureSize"), profile.INDEX_RUNTIME_REQUIREMENTS)
        self.assertIn(("paletteMode", "int32"), profile.RUNTIME_UNIFORM_ABI)


class ColorLabOraclePreparationTests(unittest.TestCase):
    def test_package_contract_has_controls_tiles_mutants_and_provenance(self):
        for path in (GENERATOR, ORACLE, REPORT, MATERIALIZER, INCLUDE):
            self.assertTrue(path.is_file(), path)
            sidecar = pathlib.Path(f"{path}.sha256")
            self.assertEqual(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n",
                sidecar.read_text(),
            )
        document = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.colorLab.pixel-parity.v1", document["schema"])
        self.assertEqual(KEY, document["program_key"])
        self.assertGreaterEqual(len(document["render_cases"]), 8)
        self.assertGreaterEqual(len(document["mutation_ledger"]), 10)
        self.assertTrue(all(document["comparer_self_tests"].values()))
        self.assertTrue(document["provenance"]["cpu_snapshot"]["realpath_containment_checked"])
        self.assertTrue(document["provenance"]["cpu_snapshot"]["symlink_escape_rejected"])
        for case in document["render_cases"]:
            size = case["width"] * case["height"] * 4
            self.assertEqual(size, len(case["expected"]["f32_words_le"]))
            self.assertEqual(size, len(case["expected"]["rgba8_bytes"]))
            self.assertTrue(case["input_immutable_exact_bits"])
            self.assertTrue(case["repeat_output_object_distinct"])
            self.assertTrue(case["repeat_output_data_distinct"])
        for mutation in document["mutation_ledger"]:
            self.assertTrue(mutation["required_witnesses"])
            self.assertTrue(all(row["mismatched_lanes"] > 0 and row["mismatched_bytes"] > 0
                                for row in mutation["required_witness_results"]))

    def test_generator_and_materializer_checks_are_standalone(self):
        authority = _authority()
        commands = (
            ["node", str(GENERATOR), "--check", "--cpu-root", str(authority)],
            ["node", str(GENERATOR), "--self-test", "--cpu-root", str(authority)],
            [sys.executable, "-B", str(MATERIALIZER), "--self-test"],
            [sys.executable, "-B", str(MATERIALIZER), "--check"],
        )
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_materializer_rejects_schema_and_digest_mutations(self):
        spec = importlib.util.spec_from_file_location("color_lab_materializer", MATERIALIZER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        document = json.loads(ORACLE.read_text())
        forged = copy.deepcopy(document)
        forged["render_cases"][0]["expected"]["f32_words_le"][0] = "0x00000000"
        with self.assertRaises(module.MaterializationError):
            module.validate(forged)

    def test_include_is_cxx20_smoke_compilable(self):
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="colorlab-oracle-cxx-") as raw:
            unit = pathlib.Path(raw) / "smoke.cpp"
            unit.write_text(
                '#include "tests/oracles/colorLab_expected.inc"\n'
                'int main() { using namespace noisemaker_color_lab_oracle; '
                'static_assert(kCases.size() >= 8U); '
                'static_assert(kCases[0].input_f32.size() == 48U); '
                'static_assert(kMutations.size() >= 10U); return 0; }\n')
            result = subprocess.run(
                [compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror",
                 "-I", str(ROOT), "-fsyntax-only", str(unit)],
                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
