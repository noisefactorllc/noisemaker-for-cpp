from __future__ import annotations

import json
import hashlib
import os
import pathlib
import shutil
import struct
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/counted-for-parity/lightleak192-oracle"
GENERATOR = PACKAGE / "lightleak192_oracle_generator.mjs"
CPU_ROOT = (pathlib.Path(os.environ["NOISEMAKER_CPU_ROOT"])
            if os.environ.get("NOISEMAKER_CPU_ROOT") else None)
WORKER = pathlib.Path(os.environ.get("LIGHTLEAK192_TEST_TMP", tempfile.gettempdir()))


class LightLeak192OracleTests(unittest.TestCase):
    def _authority(self) -> pathlib.Path:
        if CPU_ROOT is None or not CPU_ROOT.is_dir():
            self.skipTest("set NOISEMAKER_CPU_ROOT to an immutable CPU snapshot")
        return CPU_ROOT

    def _node(self, *args, cpu_root: pathlib.Path | None = CPU_ROOT,
              env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(env or {})
        return subprocess.run(
            ("node", str(GENERATOR), *args, "--cpu-root", str(cpu_root)),
            cwd=ROOT, env=environment, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def test_checked_generator_and_include(self):
        self._authority()
        checked = self._node("--check")
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertIn("11 cases, 11 behavioral mutations, 2 structural-only",
                      checked.stdout)
        materializer = subprocess.run(
            ("python3", "-B", "tools/glslcpp/generate_lightleak192_native_oracle_include.py", "--check"),
            cwd=ROOT, env=os.environ.copy(), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(0, materializer.returncode, materializer.stderr)

    def test_materializer_self_test(self):
        completed = subprocess.run(
            ("python3", "-B", "tools/glslcpp/generate_lightleak192_native_oracle_include.py", "--self-test"),
            cwd=ROOT, env=os.environ.copy(), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("11 cases", completed.stdout)
        self.assertIn("73 matching-sidecar forgery probes", completed.stdout)

    def test_fixture_contract_and_binding_tables(self):
        oracle = json.loads((PACKAGE / "lightleak192-oracles.json").read_text())
        self.assertEqual("noisemaker-for-cpp.lightleak192.pixel-parity.v1",
                         oracle["schema"])
        self.assertEqual("filter/lightLeak:lightLeak", oracle["program_key"])
        self.assertEqual(22, len(oracle["provenance"]["import_closure"]))
        self.assertEqual(11, len(oracle["render_cases"]))
        self.assertEqual({
            "schema", "source_function", "source_function_sha256",
            "coordinate_order", "component_order", "formulas",
        }, set(oracle["input_fixture"]))
        self.assertEqual(
            "noisemaker-for-cpp.lightleak192.input-texture.v1",
            oracle["input_fixture"]["schema"])
        self.assertEqual("inputSurface", oracle["input_fixture"]["source_function"])
        self.assertRegex(oracle["input_fixture"]["source_function_sha256"],
                         r"^[0-9a-f]{64}$")
        self.assertEqual("x-fastest row-major",
                         oracle["input_fixture"]["coordinate_order"])
        self.assertEqual(["r", "g", "b", "a"],
                         oracle["input_fixture"]["component_order"])
        expected_abi = {
            "inputTex": "sampler2D", "resolution": "Vec2",
            "tileOffset": "Vec2", "fullResolution": "Vec2",
            "alpha": "number", "color": "Vec3", "speed": "number",
            "seed": "int32", "time": "number",
        }
        for case in oracle["render_cases"]:
            self.assertEqual(expected_abi, case["binding_abi"])
            input_texture = case["input_texture"]
            self.assertIsInstance(input_texture["phase"], int)
            self.assertEqual({"phase", "f32_words_le", "f32_sha256",
                              "rgba8_bytes", "rgba8_sha256"},
                             set(input_texture))
            self.assertEqual(case["width"] * case["height"] * 4,
                             len(input_texture["f32_words_le"]))
            self.assertEqual(len(input_texture["f32_words_le"]),
                             len(input_texture["rgba8_bytes"]))
            input_bytes = b"".join(
                struct.pack("<I", int(word, 16))
                for word in input_texture["f32_words_le"])
            self.assertEqual(input_texture["f32_sha256"],
                             hashlib.sha256(input_bytes).hexdigest())
            self.assertEqual(input_texture["rgba8_sha256"], hashlib.sha256(
                bytes(input_texture["rgba8_bytes"])).hexdigest())
            self.assertEqual(case["width"] * case["height"] * 4,
                             len(case["output_f32_words_le"]))
            self.assertEqual(len(case["output_f32_words_le"]),
                             len(case["output_rgba8_bytes"]))
            self.assertTrue(case["input_immutable_exact_bits"])
        self.assertEqual({
            "good_equal", "dimensions_mismatch", "short_lane_count",
            "long_lane_count", "rgba8_mismatch", "rgba8_byte_count",
            "signed_zero_rejected",
            "nan_payload_rejected",
        }, set(oracle["comparer_self_tests"]))
        self.assertTrue(all(oracle["comparer_self_tests"].values()))
        names = {item["name"] for item in oracle["behavioral_mutation_ledger"]}
        self.assertTrue({
            "out-cell-color-materialization", "out-cell-dist-materialization",
            "base-bare-call-site", "warp-bare-call-site",
            "source-global-POINT_COUNT", "loop-bound-POINT_COUNT",
        } <= names)
        self.assertEqual(names, set(oracle["mutation_contract"]["behavioral_names"]))
        for item in oracle["behavioral_mutation_ledger"]:
            self.assertEqual(item["required_witnesses"],
                             oracle["mutation_contract"]["witnesses"][item["name"]])
            self.assertEqual(item["required_witnesses"],
                             [result["case"] for result in item["required_witness_results"]])
            self.assertTrue(all(result["mismatched_lanes"] > 0
                                for result in item["required_witness_results"]))

    def test_no_absolute_paths_and_report_commands_are_stable(self):
        payload = (PACKAGE / "lightleak192-oracles.json").read_text()
        self.assertNotRegex(payload, r"(?:/Users/|/private/|/tmp/|/home/)")
        report = (PACKAGE / "lightleak192-oracle-report.md").read_text()
        self.assertIn('--cpu-root "$NOISEMAKER_CPU_ROOT"', report)
        self.assertIn("source-bound input-texture phase", report)
        self.assertIn("never infer phase from case order", report)

    def test_typed_include_contract_and_cxx20_smoke(self):
        include = (ROOT / "tests/oracles/lightleak192_expected.inc").read_text()
        self.assertNotIn("kCaseControls", include)
        for marker in ("struct BindingView", "kBindingAbi", "struct CaseView",
                        "struct SourceBindingView", "kSourceBindingAbi",
                        "kCases", "kInputFixtureSchema",
                        "kInputFixtureSourceFunctionSha256",
                        "kInputFixtureFormulas", "input_phase", "input_float_words",
                        "kCase0InputFloatWords", "output_alpha_f32_words",
                        "output_alpha_rgba8_bytes", "struct MutationDivergentRowView",
                        "struct MutationResultView", "struct MutationView", "kMutations",
                        "source_anchor", "replacement", "mechanism",
                        "required_witnesses", "divergent_rows", "required_results",
                        "struct MutationWitnessView", "kMutationWitnesses",
                        "kStructuralMutations"):
            self.assertIn(marker, include)
        oracle = json.loads((PACKAGE / "lightleak192-oracles.json").read_text())
        mutations = oracle["behavioral_mutation_ledger"]
        self.assertEqual(11, len(mutations))
        self.assertNotEqual(mutations[0]["mutated_factory_sha256"],
                            next(item for item in mutations
                                 if item["name"] == "color-control-axis")["mutated_factory_sha256"])
        for item in mutations:
            self.assertTrue(item["source_anchor_text"])
            self.assertTrue(item["replacement_text"])
            self.assertRegex(item["source_anchor_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(item["replacement_sha256"], r"^[0-9a-f]{64}$")
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="lightleak192-include-") as temp:
            unit = pathlib.Path(temp) / "typed_smoke.cpp"
            unit.write_text(
                '#include "tests/oracles/lightleak192_expected.inc"\n'
                'int main() {\n'
                '  using namespace lightleak192_oracle;\n'
                '  static_assert(kBindingAbi.size() == 9U);\n'
                '  static_assert(kSourceBindingAbi.size() == 9U);\n'
                '  static_assert(kCases.size() == 11U);\n'
                '  static_assert(kCases[0].input_phase == 1U);\n'
                '  static_assert(kCases[10].input_phase == 11U);\n'
                '  static_assert(kCases[1].output_alpha_f32_words.size() == 35U);\n'
                '  static_assert(kCases[1].output_alpha_rgba8_bytes.size() == 35U);\n'
                '  static_assert(kInputFixtureSchema.size() > 0U);\n'
                '  static_assert(kInputFixtureFormulas.size() == 4U);\n'
                '  static_assert(kMutations.size() == 11U);\n'
                '  static_assert(kMutations[0].source_anchor.size() > 0U);\n'
                '  static_assert(kMutations[0].replacement.size() > 0U);\n'
                '  static_assert(kMutations[0].mechanism.size() > 0U);\n'
                '  static_assert(kMutations[0].required_witnesses.size() == 1U);\n'
                '  static_assert(kMutations[0].divergent_rows.size() == 10U);\n'
                '  static_assert(kMutations[0].required_results.size() == 1U);\n'
                '  static_assert(kMutations[0].required_results[0].top_down_xy[0] == 0U);\n'
                '  static_assert(kMutationWitnesses.size() == 11U);\n'
                '  static_assert(kStructuralMutations.size() == 2U);\n'
                '  for (const auto& binding : kBindingAbi) {\n'
                '    if (binding.name.empty() || binding.runtime_abi.empty() || binding.source_abi.empty()) return 1;\n'
                '  }\n'
                '  for (const auto& binding : kSourceBindingAbi) {\n'
                '    if (binding.name.empty() || binding.source_abi.empty()) return 1;\n'
                '  }\n'
                '  for (const auto& item : kCases) {\n'
                '    if (item.name.empty() || item.width == 0U || item.height == 0U || item.input_phase == 0U ||\n'
                '        item.input_f32_sha256.empty() || item.input_rgba8_sha256.empty() ||\n'
                '        item.input_float_words.empty() || item.input_rgba8_bytes.empty() ||\n'
                '        item.f32_sha256.empty() || item.rgba8_sha256.empty() ||\n'
                '        item.float_words.empty() || item.rgba8_bytes.empty() ||\n'
                '        item.alpha.word == 0U && item.alpha.value != 0.0f ||\n'
                '        item.color.values.size() != 3U || item.color.words.size() != 3U ||\n'
                '        item.speed.word == 0U && item.speed.value != 0.0f ||\n'
                '        item.time.word == 0U && item.time.value != 0.0f ||\n'
                '        item.seed == 0 && item.seed != 0 ||\n'
                '        item.resolution.values.size() != 2U || item.resolution.words.size() != 2U ||\n'
                '        item.tileOffset.values.size() != 2U || item.tileOffset.words.size() != 2U ||\n'
                '        item.fullResolution.values.size() != 2U || item.fullResolution.words.size() != 2U ||\n'
                '        item.output_alpha_f32_words.empty() || item.output_alpha_rgba8_bytes.empty()) return 1;\n'
                '  }\n'
                '  for (const auto& mutation : kMutations) {\n'
                '    if (mutation.name.empty() || mutation.group.empty() || mutation.mechanism.empty() ||\n'
                '        mutation.source_anchor.empty() || mutation.replacement.empty() ||\n'
                '        mutation.source_anchor_sha256.empty() || mutation.replacement_sha256.empty() ||\n'
                '        mutation.mutated_factory_sha256.empty() || mutation.anchor_count == 0U ||\n'
                '        mutation.required_witnesses.empty() || mutation.divergent_rows.empty() ||\n'
                '        mutation.required_results.empty()) return 1;\n'
                '    for (const auto& required : mutation.required_witnesses) {\n'
                '      if (required.empty()) return 1;\n'
                '    }\n'
                '    for (const auto& row : mutation.divergent_rows) {\n'
                '      if (row.case_name.empty() || (row.required_witness && row.case_name.empty())) return 1;\n'
                '    }\n'
                '    for (const auto& result : mutation.required_results) {\n'
                '      if (result.case_name.empty() || result.mismatched_lanes == 0U ||\n'
                '          result.lane_index >= result.mismatched_lanes ||\n'
                '          result.top_down_xy[0] > 100000U || result.top_down_xy[1] > 100000U ||\n'
                '          result.channel.empty() || result.reference_bits_le == result.candidate_bits_le) return 1;\n'
                '    }\n'
                '  }\n'
                '  for (const auto& witness : kMutationWitnesses) {\n'
                '    if (witness.mutation.empty() || witness.case_name.empty() ||\n'
                '        witness.mismatched_lanes == 0U || witness.channel.empty() ||\n'
                '        witness.lane_index >= witness.mismatched_lanes ||\n'
                '        witness.top_down_xy[0] > 100000U || witness.top_down_xy[1] > 100000U ||\n'
                '        witness.reference_bits_le == witness.candidate_bits_le) return 1;\n'
                '  }\n'
                '  for (const auto& structural : kStructuralMutations) {\n'
                '    if (structural.name.empty() || structural.pixel_expectation.empty()) return 1;\n'
                '  }\n'
                '  return kBindingAbi[0].abi == BindingAbi::Sampler2D && '
                'kBindingAbi[0].runtime_abi == "sampler2D" && '
                'kSourceBindingAbi[0].source_abi == "sampler2D" && '
                'kCases[1].resolution.values[0] == 7.0f ? 0 : 1;\n}\n')
            result = subprocess.run(
                [compiler, "-std=c++20", "-I", str(ROOT), "-fsyntax-only", str(unit)],
                cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_duplicate_mode_and_missing_live_root_fail_closed(self):
        self._authority()
        duplicate = self._node("--check", "--write")
        self.assertNotEqual(0, duplicate.returncode)
        self.assertIn("choose exactly one", duplicate.stderr)
        missing = self._node(
            "--check",
            env={"NOISEMAKER_FOR_CPU": str(WORKER / "missing-live-cpu")})
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("live noisemaker-for-cpu checkout does not exist",
                      missing.stderr)

    def test_symlinked_cpp_root_is_rejected_after_realpath(self):
        with tempfile.TemporaryDirectory(
                prefix="lightleak192-symlink-") as temp:
            link = pathlib.Path(temp) / "cpp-root"
            link.symlink_to(ROOT, target_is_directory=True)
            completed = self._node("--check", cpu_root=link)
        self.assertNotEqual(0, completed.returncode)
        self.assertTrue(
            "must not be a symlink" in completed.stderr or
            "must not live inside the C++ repository" in completed.stderr,
            completed.stderr)

    def test_snapshot_leaf_symlink_is_rejected_in_default_and_private_tmp(self):
        authority = self._authority()
        for temp_dir in (None, pathlib.Path("/private/tmp")):
            with tempfile.TemporaryDirectory(
                    prefix="lightleak192-snapshot-leaf-",
                    dir=str(temp_dir) if temp_dir else None) as temp:
                link = pathlib.Path(temp) / "snapshot-leaf"
                link.symlink_to(authority, target_is_directory=True)
                completed = self._node("--check", cpu_root=link)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("--cpu-root must not be a symlink",
                          completed.stderr)

    def test_live_leaf_symlink_is_rejected_in_default_and_private_tmp(self):
        authority = self._authority()
        live = pathlib.Path(os.environ["NOISEMAKER_FOR_CPU"])
        self.assertTrue(live.is_dir())
        for temp_dir in (None, pathlib.Path("/private/tmp")):
            with tempfile.TemporaryDirectory(
                    prefix="lightleak192-live-leaf-",
                    dir=str(temp_dir) if temp_dir else None) as temp:
                link = pathlib.Path(temp) / "live-leaf"
                link.symlink_to(live, target_is_directory=True)
                completed = self._node(
                    "--check", cpu_root=authority,
                    env={"NOISEMAKER_FOR_CPU": str(link)})
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("NOISEMAKER_FOR_CPU must not be a symlink",
                          completed.stderr)

    def test_tmp_parent_alias_is_accepted(self):
        authority = self._authority()
        private_tmp = pathlib.Path("/private/tmp")
        tmp_alias = pathlib.Path("/tmp")
        if not private_tmp.is_dir() or tmp_alias.resolve() != private_tmp:
            self.skipTest("/tmp is not the /private/tmp parent alias")
        try:
            alias = tmp_alias / authority.relative_to(private_tmp)
        except ValueError:
            self.skipTest("authority snapshot is not under /private/tmp")
        self.assertTrue(alias.is_dir())
        for cpu_root in (authority, alias):
            completed = self._node("--check", cpu_root=cpu_root)
            self.assertEqual(0, completed.returncode, completed.stderr)

    def test_transitive_mutation_and_dynamic_import_are_rejected(self):
        self._authority()
        with tempfile.TemporaryDirectory(
                prefix="lightleak192-mutant-") as temp:
            clone = pathlib.Path(temp) / "cpu"
            shutil.copytree(CPU_ROOT, clone)
            runtime = clone / "src/csl/runtime.js"
            runtime.write_text(runtime.read_text() + "\nexport const mutation = 1\n")
            mutated = self._node("--check", cpu_root=clone)
            self.assertNotEqual(0, mutated.returncode)
            self.assertIn("CPU import closure mismatch", mutated.stderr)

            literal = clone / "src/csl/literal-dynamic.js"
            literal.write_text("export const literalDynamic = 1\n")
            dynamic = clone / "src/csl/runtime.js"
            dynamic.write_text(dynamic.read_text() + "\nvoid import('./literal-dynamic.js')\n")
            traversed = self._node("--check", cpu_root=clone)
            self.assertNotEqual(0, traversed.returncode)
            self.assertIn("CPU import closure mismatch: expected 22, found 23",
                          traversed.stderr)
            dynamic.write_text(dynamic.read_text() + "\nvoid import(runtimeSpecifier)\n")
            rejected = self._node("--check", cpu_root=clone)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("nonliteral dynamic import", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
