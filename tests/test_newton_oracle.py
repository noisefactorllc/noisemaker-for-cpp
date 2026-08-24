from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/newton-parity"
GENERATOR = PACKAGE / "newton_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_newton_native_oracle_include.py"
ORACLE = PACKAGE / "newton-oracles.json"
REPORT = PACKAGE / "newton-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/newton_expected.inc"


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _authority() -> pathlib.Path:
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not value or not pathlib.Path(value).is_dir():
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT unavailable; authority test skipped")
    return pathlib.Path(value)


class NewtonOracleTests(unittest.TestCase):
    def _node(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(env or {})
        return subprocess.run(["node", str(GENERATOR), *args], cwd=ROOT, env=environment,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=False)

    def test_package_contract_and_sidecars(self) -> None:
        for path in (GENERATOR, MATERIALIZER, ORACLE, REPORT, INCLUDE):
            self.assertTrue(path.is_file(), path)
            sidecar = pathlib.Path(f"{path}.sha256")
            self.assertEqual(f"{_sha256(path)}  {path.name}\n", sidecar.read_text())
        document = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.newton.pixel-parity.v1", document["schema"])
        self.assertEqual("synth/newton:newton", document["program_key"])
        self.assertEqual("canonicalFactory264", document["factory"]["name"])
        self.assertTrue(document["factory"]["public_factory_is_canonical_identity"])
        self.assertFalse(document["factory"]["adapter_own_key"])
        self.assertEqual(22, len(document["provenance"]["cpu_snapshot"]["import_closure"]))
        self.assertEqual(22, document["provenance"]["cpu_snapshot"]["closure_cardinality"])
        self.assertTrue(document["provenance"]["cpu_snapshot"]["live_checkout_rejected"])
        self.assertTrue(document["provenance"]["cpu_snapshot"]["realpath_containment_checked"])
        self.assertNotRegex(ORACLE.read_text() + REPORT.read_text(),
                            r"(?:/Users/|/private/|/tmp/|/home/)")

    def test_binding_case_and_control_contract(self) -> None:
        document = json.loads(ORACLE.read_text())
        names = document["runtime_binding_names"]
        self.assertEqual(22, len(names))
        self.assertEqual(names, list(document["runtime_binding_abi"]))
        self.assertEqual(names, document["canonical_binding_contract"]["names"])
        cases = document["render_cases"]
        self.assertGreaterEqual(len(cases), 8)
        for case in cases:
            n = case["width"] * case["height"] * 4
            self.assertEqual(n, len(case["input"]["f32_words_le"]))
            self.assertEqual(n, len(case["expected"]["f32_words_le"]))
            self.assertEqual(n, len(case["expected"]["rgba8_bytes"]))
            self.assertTrue(case["input_immutable_exact_bits"])
            self.assertTrue(case["repeat_output_object_distinct"])
            self.assertTrue(case["repeat_output_data_distinct"])
            self.assertEqual(case["bindings"]["resolution"], [case["width"], case["height"]])
            self.assertEqual(case["bindings"]["fullResolution"], [case["width"], case["height"]])
            self.assertEqual(case["expected"]["f32_sha256"], hashlib.sha256(
                b"".join(int(x, 16).to_bytes(4, "little") for x in case["expected"]["f32_words_le"])
            ).hexdigest())
        comparer = document["comparer_self_tests"]
        self.assertTrue(all(comparer["cases"].values()))
        self.assertTrue(comparer["dimensions_before_access"])
        self.assertTrue(comparer["first_mismatch_reported"])
        self.assertTrue(comparer["raw_words_and_rgba8_independent"])
        self.assertIn("signed_zero", comparer["cases"])
        self.assertIn("nan_payload", comparer["cases"])

    def test_mutation_ledger_is_executed_and_complete(self) -> None:
        document = json.loads(ORACLE.read_text())
        ledger = document["mutation_ledger"]
        self.assertGreaterEqual(len(ledger), 12)
        self.assertEqual(document["mutation_anchor_cardinality"]["total"], len(ledger))
        groups = document["mutation_anchor_cardinality"]["by_group"]
        self.assertIn("struct-declaration", groups)
        self.assertIn("out-materialization", groups)
        self.assertIn("control-axis", groups)
        names = {row["name"] for row in ledger}
        self.assertIn("cross-lane-assignment", names)
        self.assertIn("struct-POIData-declaration", names)
        self.assertGreaterEqual(len(names), 12)
        for row in ledger:
            self.assertTrue(row["independent"])
            self.assertGreater(row["anchor_occurrence_count"], 0)
            self.assertRegex(row["source_anchor_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(row["replacement_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(row["mutated_factory_text_sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(row["required_witnesses"] or row["structural_only"])
            if not row["structural_only"]:
                self.assertEqual(row["required_witnesses"],
                                 [x["case"] for x in row["required_witness_results"]])
                self.assertTrue(all(x["mismatched_lanes"] > 0 for x in row["required_witness_results"]))
        structural = next(row for row in ledger if row["name"] == "struct-POIData-declaration")
        self.assertFalse(structural["structural_only"])
        self.assertTrue(structural["structural_probe"])
        self.assertEqual(structural["source_anchor"], structural["source_probe_anchor"])
        self.assertEqual(structural["replacement"], structural["source_probe_replacement"])
        self.assertTrue(structural["factory_anchor"])
        self.assertTrue(structural["factory_replacement"])

    def test_generator_check_self_test_and_materializer(self) -> None:
        authority = _authority()
        checked = self._node("--check", "--cpu-root", str(authority))
        self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
        self.assertIn("newton oracle: ok", checked.stdout)
        self_test = self._node("--self-test", "--cpu-root", str(authority))
        self.assertEqual(0, self_test.returncode, self_test.stdout + self_test.stderr)
        materializer_self_test = subprocess.run(["python3", "-B", str(MATERIALIZER), "--self-test"],
            cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(0, materializer_self_test.returncode,
                         materializer_self_test.stdout + materializer_self_test.stderr)
        materializer_check = subprocess.run(["python3", "-B", str(MATERIALIZER), "--check"],
            cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(0, materializer_check.returncode,
                         materializer_check.stdout + materializer_check.stderr)

    def test_materializer_rejects_forty_semantic_forges(self) -> None:
        module: dict[str, object] = {"__file__": str(MATERIALIZER)}
        exec(compile(MATERIALIZER.read_text(), str(MATERIALIZER), "exec"), module)
        validate = module["validate"]
        error = module["MaterializationError"]
        baseline = json.loads(ORACLE.read_text())
        mutations: list[tuple[str, object]] = []
        for index in range(8):
            mutations.append((f"case-name-{index}", index))
        mutations += [
            ("schema", lambda d: d.__setitem__("schema", "forged")),
            ("program", lambda d: d.__setitem__("program_key", "filter/newton:newton")),
            ("factory-name", lambda d: d["factory"].__setitem__("name", "canonicalFactory0")),
            ("factory-hash", lambda d: d["factory"].__setitem__("text_sha256", "0" * 64)),
            ("factory-public", lambda d: d["factory"].__setitem__("public_factory_is_canonical_identity", False)),
            ("adapter", lambda d: d["factory"].__setitem__("adapter_own_key", True)),
            ("bindings-reverse", lambda d: d["runtime_binding_names"].reverse()),
            ("binding-abi", lambda d: d["runtime_binding_abi"].__setitem__("degree", "Vec2")),
            ("exactness", lambda d: d["exactness_contract"].__setitem__("tolerance", "1e-5")),
            ("comparer", lambda d: d["comparer_self_tests"]["cases"].__setitem__("signed_zero", False)),
            ("comparer-derived-dimensions", lambda d: d["comparer_self_tests"].__setitem__("dimensions_before_access", False)),
            ("source-path", lambda d: d["provenance"]["source"].__setitem__("relative_path", "/tmp/source.glsl")),
            ("source-hash", lambda d: d["provenance"]["source"].__setitem__("sha256", "0" * 64)),
            ("closure-drop", lambda d: d["provenance"]["cpu_snapshot"]["import_closure"].pop()),
            ("closure-hash", lambda d: d["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__("sha256", "0" * 64)),
            ("closure-path", lambda d: d["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__("relative_path", "/escape.js")),
            ("closure-flag", lambda d: d["provenance"]["cpu_snapshot"].__setitem__("immutable_snapshot", False)),
            ("case-width", lambda d: d["render_cases"][0].__setitem__("width", 99)),
            ("case-control", lambda d: d["render_cases"][0]["bindings"].__setitem__("degree", 9.0)),
            ("case-input-word", lambda d: d["render_cases"][0]["input"]["f32_words_le"].__setitem__(0, "0x80000000")),
            ("case-input-hash", lambda d: d["render_cases"][0]["input"].__setitem__("f32_sha256", "0" * 64)),
            ("case-output-word", lambda d: d["render_cases"][0]["expected"]["f32_words_le"].__setitem__(0, "0x80000000")),
            ("case-output-hash", lambda d: d["render_cases"][0]["expected"].__setitem__("f32_sha256", "0" * 64)),
            ("case-rgba-byte", lambda d: d["render_cases"][0]["expected"]["rgba8_bytes"].__setitem__(0, 1)),
            ("case-rgba-hash", lambda d: d["render_cases"][0]["expected"].__setitem__("rgba8_sha256", "0" * 64)),
            ("immutability", lambda d: d["render_cases"][0].__setitem__("input_immutable_exact_bits", False)),
            ("control-repeat", lambda d: d["control_group"]["repeatability"].__setitem__("identical_float32", False)),
            ("control-storage", lambda d: d["control_group"]["independent_output_storage"].__setitem__("distinct_data_objects", False)),
            ("repeat-object", lambda d: d["render_cases"][0].__setitem__("repeat_output_object_distinct", False)),
            ("repeat-data", lambda d: d["render_cases"][0].__setitem__("repeat_output_data_distinct", False)),
            ("profile-status", lambda d: d["cross_lane_assignment_profile"].__setitem__("status", "unverified")),
            ("profile-anchor", lambda d: d["cross_lane_assignment_profile"].__setitem__("anchor", "forged")),
            ("mutation-name", lambda d: d["mutation_ledger"][0].__setitem__("name", "forged")),
            ("mutation-group", lambda d: d["mutation_ledger"][0].__setitem__("group", "uniform")),
            ("mutation-anchor", lambda d: d["mutation_ledger"][0].__setitem__("source_anchor", "forged")),
            ("mutation-anchor-hash", lambda d: d["mutation_ledger"][0].__setitem__("source_anchor_sha256", "0" * 64)),
            ("mutation-replacement", lambda d: d["mutation_ledger"][0].__setitem__("replacement", "forged")),
            ("mutation-replacement-hash", lambda d: d["mutation_ledger"][0].__setitem__("replacement_sha256", "0" * 64)),
            ("mutation-factory-hash", lambda d: d["mutation_ledger"][0].__setitem__("mutated_factory_text_sha256", "0" * 64)),
            ("mutation-independent", lambda d: d["mutation_ledger"][0].__setitem__("independent", False)),
            ("mutation-witness", lambda d: d["mutation_ledger"][0].__setitem__("required_witnesses", [])),
            ("mutation-result", lambda d: d["mutation_ledger"][0]["required_witness_results"][0].__setitem__("mismatched_lanes", 0)),
            ("mutation-result-case", lambda d: d["mutation_ledger"][0]["required_witness_results"][0].__setitem__("case", "forged")),
            ("mutation-structural", lambda d: d["mutation_ledger"][0].__setitem__("structural_only", True)),
            ("structural-probe", lambda d: d["mutation_ledger"][-1].__setitem__("structural_probe", False)),
            ("structural-factory-anchor", lambda d: d["mutation_ledger"][-1].__setitem__("factory_anchor", "forged")),
            ("claim-authority", lambda d: d["claim_boundaries"].__setitem__("authority", "local implementation")),
            ("claim-absolute", lambda d: d["claim_boundaries"].__setitem__("foreign", "/tmp/escape")),
        ]
        self.assertGreaterEqual(len(mutations), 40)
        for label, mutate in mutations:
            forged = copy.deepcopy(baseline)
            if label.startswith("case-name"):
                forged["render_cases"][mutate]["name"] += "-forged"
            else:
                mutate(forged)
            with self.assertRaises(error, msg=label):
                validate(forged)

    def test_paths_closure_and_live_checkout_fail_closed(self) -> None:
        authority = _authority()
        with tempfile.TemporaryDirectory(prefix="newton-oracle-paths-") as raw:
            base = pathlib.Path(raw)
            link = base / "cpp-link"
            link.symlink_to(ROOT, target_is_directory=True)
            escaped = self._node("--check", "--cpu-root", str(link))
            self.assertNotEqual(0, escaped.returncode)
            self.assertIn("C++ repository", escaped.stderr)
            live = self._node("--check", "--cpu-root", str(authority),
                              env={"NOISEMAKER_FOR_CPU": str(authority)})
            self.assertNotEqual(0, live.returncode)
            self.assertRegex(live.stderr, r"live checkout|immutable snapshot")
            clone = base / "cpu"
            shutil.copytree(authority, clone)
            runtime = clone / "src/csl/runtime.js"
            runtime.write_text(runtime.read_text() + "\nimport './literal-extra.js'\n")
            (clone / "src/csl/literal-extra.js").write_text("export const extra = 1\n")
            extra = self._node("--check", "--cpu-root", str(clone))
            self.assertNotEqual(0, extra.returncode)
            self.assertIn("import closure", extra.stderr)
            runtime.write_text(runtime.read_text() + "\nvoid import(dynamicSpecifier)\n")
            nonliteral = self._node("--check", "--cpu-root", str(clone))
            self.assertNotEqual(0, nonliteral.returncode)
            self.assertIn("nonliteral dynamic import", nonliteral.stderr)

    def test_cli_requires_exact_mode_and_explicit_snapshot(self) -> None:
        authority = _authority()
        missing = self._node("--check")
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("--cpu-root", missing.stderr)
        duplicate = self._node("--check", "--write", "--cpu-root", str(authority))
        self.assertNotEqual(0, duplicate.returncode)
        self.assertIn("choose exactly one", duplicate.stderr)

    def test_cxx20_include_smoke(self) -> None:
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="newton-include-") as raw:
            unit = pathlib.Path(raw) / "smoke.cpp"
            unit.write_text(
                '#include "tests/oracles/newton_expected.inc"\n'
                'int main() { using namespace newton_oracle; '
                'static_assert(kBindingNames.size() == 22U); '
                'static_assert(kCases.size() >= 8U); '
                'static_assert(kMutations.size() >= 12U); return 0; }\n')
            result = subprocess.run([compiler, "-std=c++20", "-I", str(ROOT),
                                     "-fsyntax-only", str(unit)], cwd=ROOT,
                                    text=True, capture_output=True, check=False)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
