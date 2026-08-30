from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/distortion-parity"
GENERATOR = PACKAGE / "distortion_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_distortion_native_oracle_include.py"
ORACLE = PACKAGE / "distortion-oracles.json"
REPORT = PACKAGE / "distortion-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/distortion_expected.inc"
# No defaults: the frozen CPU authority and the live checkout live outside
# the repository at machine-specific locations, so they must arrive by env.
AUTHORITY = Path(os.environ.get("NOISEMAKER_CPU_ROOT") or "/nonexistent")


def live_cpu_checkout() -> Path:
    candidate = Path(os.environ.get("NOISEMAKER_FOR_CPU") or "/nonexistent")
    if not candidate.is_dir():
        raise unittest.SkipTest(f"live noisemaker-for-cpu unavailable: {candidate}")
    return candidate


def materializer_module():
    spec = importlib.util.spec_from_file_location("distortion_materializer", MATERIALIZER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DistortionOracleTests(unittest.TestCase):
    def test_package_and_sidecars(self):
        for path in (GENERATOR, ORACLE, REPORT, INCLUDE):
            self.assertTrue(path.is_file(), path)
            sidecar = Path(f"{path}.sha256")
            self.assertEqual(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n", sidecar.read_text())
        document = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.distortion.pixel-parity.v1", document["schema"])
        self.assertEqual("mixer/distortion:distortion", document["program_key"])
        self.assertEqual(6, len(document["render_cases"]))
        self.assertEqual(3, len(document["mutation_ledger"]))
        snapshot = document["provenance"]["cpu_snapshot"]
        self.assertEqual(22, snapshot["closure_cardinality"])
        self.assertEqual(22, len(snapshot["import_closure"]))
        self.assertEqual(sorted(item["relative_path"] for item in snapshot["import_closure"]),
                         [item["relative_path"] for item in snapshot["import_closure"]])
        self.assertTrue(snapshot["realpath_containment_checked"])
        self.assertTrue(snapshot["live_checkout_rejected"])
        self.assertTrue(all(item["independent"] for item in document["mutation_ledger"]))
        self.assertTrue(all(result["changed_float32_lanes"] and result["changed_rgba8_bytes"]
                            for item in document["mutation_ledger"] for result in item["results"]))

    def test_materializer_self_test_and_check(self):
        for args in (("--self-test",), ("--check",)):
            result = subprocess.run(
                [sys.executable, str(MATERIALIZER), *args], cwd=ROOT,
                env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
                text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_canonical_generator_check_and_self_test(self):
        cpu_root = AUTHORITY
        if not cpu_root.is_dir():
            self.skipTest(f"frozen CPU oracle unavailable: {cpu_root}")
        live_cpu = live_cpu_checkout()
        for mode in ("--check", "--self-test"):
            result = subprocess.run(
                ["node", str(GENERATOR), mode, "--cpu-root", str(cpu_root)],
                cwd=ROOT, env={**os.environ, "NOISEMAKER_FOR_CPU": str(live_cpu)},
                text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_generator_requires_existing_nonsymlink_separate_live_checkout(self):
        if not AUTHORITY.is_dir():
            self.skipTest(f"frozen CPU oracle unavailable: {AUTHORITY}")
        base_env = os.environ.copy()
        base_env.pop("NOISEMAKER_FOR_CPU", None)
        unset = subprocess.run(
            ["node", str(GENERATOR), "--check", "--cpu-root", str(AUTHORITY)],
            cwd=ROOT, env=base_env, text=True, capture_output=True)
        self.assertNotEqual(0, unset.returncode)
        self.assertIn("live noisemaker-for-cpu checkout does not exist", unset.stderr)

        missing = subprocess.run(
            ["node", str(GENERATOR), "--check", "--cpu-root", str(AUTHORITY)],
            cwd=ROOT, env={**base_env, "NOISEMAKER_FOR_CPU": str(ROOT / "missing-live-cpu")},
            text=True, capture_output=True)
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("live noisemaker-for-cpu checkout does not exist", missing.stderr)

        wrong = subprocess.run(
            ["node", str(GENERATOR), "--check", "--cpu-root", str(AUTHORITY)],
            cwd=ROOT, env={**base_env, "NOISEMAKER_FOR_CPU": str(ROOT)},
            text=True, capture_output=True)
        self.assertNotEqual(0, wrong.returncode)
        self.assertIn("is not a noisemaker-for-cpu checkout", wrong.stderr)

        same = subprocess.run(
            ["node", str(GENERATOR), "--check", "--cpu-root", str(AUTHORITY)],
            cwd=ROOT, env={**base_env, "NOISEMAKER_FOR_CPU": str(AUTHORITY)},
            text=True, capture_output=True)
        self.assertNotEqual(0, same.returncode)
        self.assertIn("immutable snapshot", same.stderr)

        with tempfile.TemporaryDirectory(prefix="distortion-live-symlink-") as directory:
            link = Path(directory) / "live"
            link.symlink_to(live_cpu_checkout(), target_is_directory=True)
            linked = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(AUTHORITY)],
                cwd=ROOT, env={**base_env, "NOISEMAKER_FOR_CPU": str(link)},
                text=True, capture_output=True)
        self.assertNotEqual(0, linked.returncode)
        self.assertIn("NOISEMAKER_FOR_CPU must not be a symlink", linked.stderr)

    def test_generator_rejects_closure_extra_and_nonliteral_dynamic_import(self):
        cpu_root = AUTHORITY
        if not cpu_root.is_dir():
            self.skipTest(f"frozen CPU oracle unavailable: {cpu_root}")
        with tempfile.TemporaryDirectory(prefix="distortion-authority-closure-") as directory:
            clone = Path(directory) / "cpu"
            shutil.copytree(cpu_root, clone)
            runtime = clone / "src/csl/runtime.js"
            runtime.write_text(runtime.read_text() + "\nimport './literal-extra.js'\n")
            (clone / "src/csl/literal-extra.js").write_text("export const extra = 1\n")
            env = {**os.environ, "NOISEMAKER_FOR_CPU": str(live_cpu_checkout())}
            result = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(clone)],
                cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("import closure", result.stderr)
            runtime.write_text(runtime.read_text() + "\nvoid import(dynamicSpecifier)\n")
            result = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(clone)],
                cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("nonliteral dynamic import", result.stderr)

    def test_generator_rejects_bare_escape_and_symlink_imports(self):
        cpu_root = AUTHORITY
        if not cpu_root.is_dir():
            self.skipTest(f"frozen CPU oracle unavailable: {cpu_root}")
        with tempfile.TemporaryDirectory(prefix="distortion-authority-paths-") as directory:
            base = Path(directory)
            env = {**os.environ, "NOISEMAKER_FOR_CPU": str(live_cpu_checkout())}

            def run(mutator):
                clone = base / f"cpu-{len(list(base.glob('cpu-*')))}"
                shutil.copytree(cpu_root, clone)
                mutator(clone)
                return subprocess.run(
                    ["node", str(GENERATOR), "--check", "--cpu-root", str(clone)],
                    cwd=ROOT, env=env, text=True, capture_output=True)

            bare = run(lambda clone: (clone / "src/csl/runtime.js").write_text(
                (clone / "src/csl/runtime.js").read_text() + "\nimport 'fs'\n"))
            self.assertNotEqual(0, bare.returncode)
            self.assertIn("bare module specifier", bare.stderr)

            escaped_file = base / "escaped.js"
            escaped_file.write_text("export const escaped = 1\n")
            escaped = run(lambda clone: (clone / "src/csl/runtime.js").write_text(
                (clone / "src/csl/runtime.js").read_text() + "\nimport '../../../escaped.js'\n"))
            self.assertNotEqual(0, escaped.returncode)
            self.assertIn("import escaped", escaped.stderr)

            symlink_target = base / "outside-runtime.js"
            symlink_target.write_text("export const outside = 1\n")
            def symlink(clone):
                runtime = clone / "src/csl/runtime.js"
                runtime.unlink()
                runtime.symlink_to(symlink_target)
            linked = run(symlink)
            self.assertNotEqual(0, linked.returncode)
            self.assertIn("escaped immutable snapshot", linked.stderr)

    def test_materializer_rejects_forged_mutation(self):
        module = materializer_module()
        document = json.loads(ORACLE.read_text())
        document["mutation_ledger"][0]["independent"] = False
        with self.assertRaises(module.OracleError):
            module.validate(document)

    def test_materializer_rejects_forged_authority_closure(self):
        module = materializer_module()
        baseline = json.loads(ORACLE.read_text())
        for mutate in (
                lambda document: document["provenance"]["cpu_snapshot"]["import_closure"].pop(),
                lambda document: document["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__(
                    "relative_path", "../escaped.js"),
                lambda document: document["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__(
                    "sha256", "0" * 64),
                lambda document: document["provenance"]["cpu_snapshot"].__setitem__(
                    "closure_cardinality", 21),
        ):
            document = json.loads(json.dumps(baseline))
            mutate(document)
            with self.assertRaises(module.OracleError):
                module.validate(document)

    def test_materializer_rejects_forged_mutation_provenance_and_counts(self):
        module = materializer_module()
        for mutate in (
                lambda document: document["mutation_ledger"][0].__setitem__(
                    "mutated_factory_sha256", "0" * 64),
                lambda document: document["mutation_ledger"][0]["results"][0].__setitem__(
                    "changed_float32_lanes", 191),
                lambda document: document["mutation_ledger"][1]["results"][0].__setitem__(
                    "changed_rgba8_bytes", 999999),
        ):
            document = json.loads(ORACLE.read_text())
            mutate(document)
            with self.assertRaises(module.OracleError):
                module.validate(document)

    def test_materializer_rejects_non_object_and_forged_claim_boundaries(self):
        module = materializer_module()
        with self.assertRaises(module.OracleError):
            module.validate(None)

        for mutate in (
                lambda document: document["claim_boundaries"].__setitem__(
                    "first_blocker", "forged"),
                lambda document: document["claim_boundaries"]["additional_blockers"].__setitem__(
                    0, "forged"),
        ):
            document = json.loads(ORACLE.read_text())
            mutate(document)
            with self.assertRaises(module.OracleError):
                module.validate(document)

    def test_materializer_rejects_forged_controls_and_provenance(self):
        module = materializer_module()
        document = json.loads(ORACLE.read_text())
        document["render_cases"][0]["intensity"] = True
        with self.assertRaises(module.OracleError):
            module.validate(document)

    def test_materializer_rejects_local_glsl_source_byte_drift(self):
        module = materializer_module()
        with tempfile.TemporaryDirectory(prefix="distortion-source-drift-") as directory:
            fake_root = Path(directory)
            source = fake_root / module.SOURCE
            source.parent.mkdir(parents=True)
            source.write_bytes((ROOT / module.SOURCE).read_bytes() + b"\n")
            with self.assertRaisesRegex(module.OracleError, "source bytes drift"):
                module.validate_source_file(fake_root)

        document = json.loads(ORACLE.read_text())
        document["render_cases"][0]["tileOffset"] = [0]
        with self.assertRaises(module.OracleError):
            module.validate(document)

        document = json.loads(ORACLE.read_text())
        document["provenance"]["source"]["sha256"] = "0" * 64
        with self.assertRaises(module.OracleError):
            module.validate(document)

    def test_materializer_rejects_forged_immutability_and_texture_abi(self):
        module = materializer_module()
        for mutate in (
                lambda document: document["render_cases"][0].__setitem__("input_immutable", False),
                lambda document: document["runtime_binding_abi"].__setitem__("inputTex", "number"),
                lambda document: document["source_uniform_abi"].__setitem__("tex", "float"),
                lambda document: document["runtime_binding_names"].__setitem__(0, "tex"),
        ):
            document = json.loads(ORACLE.read_text())
            mutate(document)
            with self.assertRaises(module.OracleError):
                module.validate(document)

    def test_canonical_texture_abi_is_authenticated_in_order(self):
        module = materializer_module()
        document = json.loads(ORACLE.read_text())
        self.assertEqual(
            ["inputTex", "tex", "resolution", "tileOffset", "fullResolution",
             "mode", "mapSource", "intensity", "wrap", "smoothing", "aberration",
             "antialias"],
            document["runtime_binding_names"])
        self.assertEqual("Surface", document["runtime_binding_abi"]["inputTex"])
        self.assertEqual("Surface", document["runtime_binding_abi"]["tex"])
        self.assertEqual("sampler2D", document["source_uniform_abi"]["inputTex"])
        self.assertEqual("sampler2D", document["source_uniform_abi"]["tex"])

    def test_include_exposes_authenticated_controls_and_metadata(self):
        text = INCLUDE.read_text()
        self.assertIn("struct CaseControls", text)
        self.assertIn("kOracleJsonSha256", text)
        self.assertIn(hashlib.sha256(ORACLE.read_bytes()).hexdigest(), text)
        self.assertIn("kFactorySha256", text)
        self.assertIn("kRuntimeBindings", text)
        self.assertIn("kMutations", text)
        self.assertIn("kImportClosure", text)
        self.assertIn("kImportClosureCardinality = 22U", text)
        self.assertIn("kCase0Controls", text)

    def test_include_compiles_as_cxx20(self):
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="distortion-oracle-") as directory:
            unit = Path(directory) / "smoke.cpp"
            unit.write_text(
                '#include "tests/oracles/distortion_expected.inc"\n'
                "int main() {\n"
                "  static_assert(distortion_oracle::kCases.size() == 6);\n"
                "  static_assert(distortion_oracle::kCase0F32.size() == 8 * 6 * 4);\n"
                "  static_assert(distortion_oracle::kCase0Rgba8.size() == 8 * 6 * 4);\n"
                "  static_assert(distortion_oracle::kCase0Controls.intensity.bits == 0x42820000U);\n"
                "  static_assert(distortion_oracle::kRuntimeBindings.size() == 12);\n"
                "  static_assert(distortion_oracle::kImportClosureCardinality == 22);\n"
                "  static_assert(distortion_oracle::kImportClosure.size() == 22);\n"
                "  static_assert(distortion_oracle::kMutations.size() == 3);\n"
                "  return distortion_oracle::kCases[0].width == 8U ? 0 : 1;\n"
                "}\n")
            result = subprocess.run(
                [compiler, "-std=c++20", "-I", str(ROOT), "-fsyntax-only", str(unit)],
                cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
