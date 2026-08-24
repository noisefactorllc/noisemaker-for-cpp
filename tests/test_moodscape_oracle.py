from __future__ import annotations

import copy
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
PACKAGE = ROOT / "docs/port-engineering/moodscape-parity"
GENERATOR = PACKAGE / "moodscape_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_moodscape_native_oracle_include.py"
ORACLE = PACKAGE / "moodscape-oracles.json"
REPORT = PACKAGE / "moodscape-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/moodscape_expected.inc"
AUTHORITY = Path("/private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu")
LIVE = Path("/Users/aayars/platform/noisemaker-for-cpu")
SOURCE = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/moodscape/moodscape.glsl"


def materializer_module():
    spec = importlib.util.spec_from_file_location("moodscape_materializer", MATERIALIZER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_generator(*args, cpu_root=AUTHORITY, live=LIVE):
    env = os.environ.copy()
    if live is None:
        env.pop("NOISEMAKER_FOR_CPU", None)
    else:
        env["NOISEMAKER_FOR_CPU"] = str(live)
    return subprocess.run(
        ["node", str(GENERATOR), *args, "--cpu-root", str(cpu_root)],
        cwd=ROOT, env=env, text=True, capture_output=True,
    )


class MoodscapeOracleTests(unittest.TestCase):
    def test_package_and_sidecars_pin_strict_contract(self):
        for path in (GENERATOR, ORACLE, REPORT, MATERIALIZER, INCLUDE):
            self.assertTrue(path.is_file(), path)
            sidecar = Path(f"{path}.sha256")
            self.assertEqual(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n",
                sidecar.read_text(),
            )
        document = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.moodscape.pixel-parity.v1", document["schema"])
        self.assertEqual("classicNoisedeck/moodscape:moodscape", document["program_key"])
        self.assertEqual(["NOISE_TYPE", "COLOR_MODE", "time", "seed", "wrap", "resolution",
                          "tileOffset", "fullResolution", "noiseScale", "refractAmt", "speed",
                          "hueRotation", "hueRange", "intensity", "ridges"],
                         document["runtime_binding_names"])
        self.assertEqual({"NOISE_TYPE": "int32", "COLOR_MODE": "int32", "time": "float",
                          "seed": "int32", "wrap": "bool", "resolution": "Vec2",
                          "tileOffset": "Vec2", "fullResolution": "Vec2", "noiseScale": "float",
                          "refractAmt": "float", "speed": "float", "hueRotation": "float",
                          "hueRange": "float", "intensity": "float", "ridges": "bool"},
                         document["runtime_binding_abi"])
        self.assertEqual({"time": "float", "seed": "int", "wrap": "bool", "resolution": "vec2",
                          "tileOffset": "vec2", "fullResolution": "vec2", "noiseScale": "float",
                          "refractAmt": "float", "speed": "float", "hueRotation": "float",
                          "hueRange": "float", "intensity": "float", "ridges": "bool"},
                         document["source_uniform_abi"])
        self.assertEqual(22, document["authority"]["closure_cardinality"])
        self.assertEqual(22, len(document["authority"]["import_closure"]))
        self.assertEqual(6, len(document["render_cases"]))
        self.assertEqual(5, len(document["mutation_ledger"]))
        self.assertEqual("canonicalFactory11", document["factory"]["name"])
        self.assertEqual("70db1168604045e22ac0c74f4b58a96d5e4ed2c6e107ec2fe3b2beab08ca479d",
                         document["factory"]["text_sha256"])
        self.assertEqual(19559, document["provenance"]["source"]["bytes"])
        self.assertEqual("a2580a36096208dd7a63965d2b277be9356f29a8d3af634d1736df9142db1a44",
                         document["provenance"]["source"]["sha256"])

    def test_every_case_records_exact_repeat_storage_and_controls(self):
        document = json.loads(ORACLE.read_text())
        for case in document["render_cases"]:
            size = case["width"] * case["height"] * 4
            expected = case["expected"]
            self.assertEqual(size, len(expected["f32_words_le"]))
            self.assertEqual(size, len(expected["rgba8_bytes"]))
            self.assertEqual(size * 4, case["f32_byte_count"])
            self.assertEqual(size, case["rgba8_byte_count"])
            self.assertTrue(case["repeat"]["exact"])
            self.assertTrue(case["storage"]["distinct_surface_objects"])
            self.assertTrue(case["storage"]["distinct_f32_backing_stores"])
            self.assertTrue(case["controls_snapshot"]["unchanged"])
            self.assertEqual(expected["f32_sha256"], hashlib.sha256(
                b"".join(int(word, 16).to_bytes(4, "little") for word in expected["f32_words_le"])
            ).hexdigest())
            self.assertEqual(expected["rgba8_sha256"], hashlib.sha256(bytes(expected["rgba8_bytes"])).hexdigest())

    def test_generator_check_self_test_and_authority_negative_paths(self):
        if not AUTHORITY.is_dir() or not LIVE.is_dir():
            self.skipTest("frozen CPU authority or live CPU checkout unavailable")
        for mode in ("--check", "--self-test"):
            result = run_generator(mode)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        unset = run_generator("--check", live=None)
        self.assertNotEqual(0, unset.returncode)
        self.assertIn("live noisemaker-for-cpu checkout does not exist", unset.stderr)
        missing = run_generator("--check", live=ROOT / "missing-live-noisemaker")
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("live noisemaker-for-cpu checkout does not exist", missing.stderr)
        wrong = run_generator("--check", live=ROOT)
        self.assertNotEqual(0, wrong.returncode)
        self.assertIn("not a noisemaker-for-cpu checkout", wrong.stderr)
        same = run_generator("--check", live=AUTHORITY)
        self.assertNotEqual(0, same.returncode)
        self.assertIn("immutable snapshot", same.stderr)
        with tempfile.TemporaryDirectory(prefix="moodscape-live-") as raw:
            link = Path(raw) / "live"
            link.symlink_to(LIVE, target_is_directory=True)
            linked = run_generator("--check", live=link)
        self.assertNotEqual(0, linked.returncode)
        self.assertIn("must not be a symlink", linked.stderr)
        under_cpp = run_generator("--check", cpu_root=ROOT)
        self.assertNotEqual(0, under_cpp.returncode)
        self.assertIn("authority", under_cpp.stderr)

    def test_generator_rejects_extra_nonliteral_bare_escape_and_symlink_closure(self):
        if not AUTHORITY.is_dir() or not LIVE.is_dir():
            self.skipTest("frozen CPU authority or live CPU checkout unavailable")
        with tempfile.TemporaryDirectory(prefix="moodscape-authority-") as raw:
            base = Path(raw)

            def run(mutator, label):
                clone = base / label
                shutil.copytree(AUTHORITY, clone)
                mutator(clone)
                return run_generator("--check", cpu_root=clone)

            extra = run(lambda clone: ((clone / "src/csl/runtime.js").write_text(
                (clone / "src/csl/runtime.js").read_text() + "\nimport './literal-extra.js'\n")), "extra")
            self.assertNotEqual(0, extra.returncode)
            self.assertIn("import closure", extra.stderr)
            def absolute(clone):
                target = clone / "absolute-extra.js"
                target.write_text("export const absolute = 1\n")
                runtime = clone / "src/csl/runtime.js"
                runtime.write_text(runtime.read_text() + f"\nimport '{target}'\n")
            absolute_result = run(absolute, "absolute")
            self.assertNotEqual(0, absolute_result.returncode)
            self.assertIn("absolute module specifier", absolute_result.stderr)
            dynamic = run(lambda clone: ((clone / "src/csl/runtime.js").write_text(
                (clone / "src/csl/runtime.js").read_text() + "\nvoid import(dynamicSpecifier)\n")), "dynamic")
            self.assertNotEqual(0, dynamic.returncode)
            self.assertIn("nonliteral dynamic import", dynamic.stderr)
            bare = run(lambda clone: ((clone / "src/csl/runtime.js").write_text(
                (clone / "src/csl/runtime.js").read_text() + "\nimport 'fs'\n")), "bare")
            self.assertNotEqual(0, bare.returncode)
            self.assertIn("bare module specifier", bare.stderr)
            escaped_file = base / "escaped.js"
            escaped_file.write_text("export const escaped = 1\n")
            escaped = run(lambda clone: ((clone / "src/csl/runtime.js").write_text(
                (clone / "src/csl/runtime.js").read_text() + "\nimport '../../../escaped.js'\n")), "escaped")
            self.assertNotEqual(0, escaped.returncode)
            self.assertIn("import escaped", escaped.stderr)
            outside = base / "outside.js"
            outside.write_text("export const outside = 1\n")
            def symlink(clone):
                runtime = clone / "src/csl/runtime.js"
                runtime.unlink()
                runtime.symlink_to(outside)
            linked = run(symlink, "symlink")
            self.assertNotEqual(0, linked.returncode)
            self.assertIn("must not be a symlink", linked.stderr)

    def test_materializer_rejects_forged_document_and_recomputes_source_and_sidecars(self):
        module = materializer_module()
        baseline = json.loads(ORACLE.read_text())
        for mutate in (
            lambda d: d.__setitem__("schema", "forged"),
            lambda d: d.__setitem__("extra", True),
            lambda d: d["factory"].__setitem__("text_sha256", "0" * 64),
            lambda d: d["factory"].__setitem__("adapter_own_key", True),
            lambda d: d["authority"]["import_closure"].pop(),
            lambda d: d["authority"]["import_closure"][0].__setitem__("relative_path", "../escape.js"),
            lambda d: d["runtime_binding_names"].__setitem__(0, "forged"),
            lambda d: d["source_uniform_abi"].__setitem__("time", "int"),
            lambda d: d["render_cases"][0]["expected"]["f32_words_le"].__setitem__(0, "0x00000000"),
            lambda d: d["render_cases"][0]["expected"].__setitem__("f32_sha256", "0" * 64),
            lambda d: d["render_cases"][0]["repeat"].__setitem__("exact", False),
            lambda d: d["render_cases"][0]["storage"].__setitem__("distinct_surface_objects", False),
            lambda d: d["render_cases"][0]["controls_snapshot"].__setitem__("unchanged", False),
            lambda d: d["mutation_ledger"][0].__setitem__("independent", False),
            lambda d: d["comparer_self_tests"].__setitem__("control_mutation_rejected", False),
            lambda d: d["mutation_ledger"][0].__setitem__("extra", True),
            lambda d: d["mutation_ledger"][0].__setitem__("witnesses", d["mutation_ledger"][0]["witnesses"][:-1]),
            lambda d: d["mutation_ledger"][0].__setitem__("witnesses", [d["mutation_ledger"][0]["witnesses"][0]] * len(d["mutation_ledger"][0]["witnesses"])),
            lambda d: d["mutation_ledger"].__setitem__(1, {**d["mutation_ledger"][1], "name": d["mutation_ledger"][0]["name"]}),
            lambda d: d["mutation_ledger"][0]["results"].__setitem__(1, dict(d["mutation_ledger"][0]["results"][0])),
            lambda d: d["mutation_ledger"][0].pop("witnesses"),
        ):
            document = copy.deepcopy(baseline)
            mutate(document)
            with self.assertRaises(module.OracleError):
                module.validate(document)
        with tempfile.TemporaryDirectory(prefix="moodscape-source-") as raw:
            fake_root = Path(raw)
            target = fake_root / module.SOURCE
            target.parent.mkdir(parents=True)
            target.write_bytes(SOURCE.read_bytes() + b"\n")
            with self.assertRaises(module.OracleError):
                module.validate_source_file(fake_root)

    def test_materializer_modes_and_cxx20_include_smoke_compile(self):
        for args in (("--self-test",), ("--check",)):
            result = subprocess.run(
                [sys.executable, "-B", str(MATERIALIZER), *args], cwd=ROOT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="moodscape-oracle-cxx-") as raw:
            unit = Path(raw) / "smoke.cpp"
            unit.write_text(
                '#include "tests/oracles/moodscape_expected.inc"\n'
                "int main() {\n"
                "  static_assert(noisemaker_moodscape_oracle::kCases.size() == 6);\n"
                "  static_assert(noisemaker_moodscape_oracle::kRuntimeBindings.size() == 15);\n"
                "  static_assert(noisemaker_moodscape_oracle::kImportClosureCardinality == 22);\n"
                "  static_assert(noisemaker_moodscape_oracle::kMutations.size() == 5);\n"
                "  return 0;\n}\n"
            )
            result = subprocess.run(
                [compiler, "-std=c++20", "-I", str(ROOT), "-fsyntax-only", str(unit)],
                cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
