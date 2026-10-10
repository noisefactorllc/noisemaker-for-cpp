"""CPU26d OSD regression for truncated glyph cell indexing."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest import mock

from tests import corpus_census
from tools.glslcpp import emit_typed_cpp

from tools.glslcpp import check_corpus
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tests.gate import full_run_only

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/osd_current"
KEY = "filter/osd:osd"
PARAMETERS = ("alpha", "seed", "speed", "corner")


def packed_input(case):
    width, height = case["width"], case["height"]
    if case["image"] == "solid":
        values = [.2, 2 / 3, 7 / 15, 1] * (width * height)
    else:
        values = [((x * 17 + y * 29 + c * 43 + 7) % 251) / 250 if c < 3 else 1
                  for y in range(height) for x in range(width) for c in range(4)]
    return struct.pack(f"<{len(values)}f", *values)


def reference_inputs(cases):
    return [{**case, "inputFloat32": packed_input(case).hex()} for case in cases]


def emitted_kernel():
    source = (ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION /
              "sources/filter/osd/osd.glsl").read_text()
    digest = hashlib.sha256(source.encode()).hexdigest()
    program = analyze_program(parse_program(source, KEY, {}), KEY)
    return render_typed_cpp(program, KEY, digest, osd_frontend_profile="osd-frontend-admission-v1",
                            factory="bind_osd_numerical_probe")


@full_run_only
class OsdCurrentKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="osd-current-kernel-")
        cls.addClassCleanup(cls.temporary.cleanup)
        temporary = pathlib.Path(cls.temporary.name)
        (temporary / "osd_emitted.inc").write_text(emitted_kernel())
        cls.binary = temporary / "probe"
        compiler = shutil.which("clang++") or shutil.which("c++")
        if compiler is None:
            raise AssertionError("a C++20 compiler is required for OsdCurrent kernel verification")
        result = subprocess.run([
            compiler, "-std=c++20", "-O1", "-ffp-contract=off", "-I", str(ROOT / "include"),
            "-I", str(temporary), str(FIXTURE / "probe.cpp"),
            *(str(ROOT / "src" / f"{name}.cpp") for name in
              ("surface", "numeric", "sampler", "glsl_runtime", "kernel", "fdlibm", "fdlibm_off")),
            "-o", str(cls.binary),
        ], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def test_glyph_cell_boundaries_match_cpu(self):
        cases = json.loads((FIXTURE / "cases.json").read_text())
        captures = json.loads((FIXTURE / "expected.json").read_text())["results"]
        self.assertEqual(len(cases), 38)
        self.assertEqual([case["name"] for case in cases], [row["name"] for row in captures])
        for case, row in zip(cases, captures, strict=True):
            with self.subTest(case=case["name"]):
                args = [case["width"], case["height"], case["time"],
                        *(case["uniforms"][name] for name in PARAMETERS)]
                result = subprocess.run([str(self.binary), *map(str, args)], input=packed_input(case),
                                        capture_output=True, check=True)
                word_bytes = case["width"] * case["height"] * 16
                rgba_bytes = case["width"] * case["height"] * 4
                self.assertEqual(len(result.stdout), word_bytes + rgba_bytes)
                self.assertEqual(hashlib.sha256(result.stdout[:word_bytes]).hexdigest(), row["float32_sha256"])
                self.assertEqual(hashlib.sha256(result.stdout[word_bytes:]).hexdigest(), row["rgba8_sha256"])


class OsdCurrentReferenceTests(unittest.TestCase):
    def test_capture_provenance_and_coverage(self):
        for name, digest in {'cases.json': '0a507681df91bbd819a5126bc88c55739ecb17642e3dc81b0849388a32fb9f4b', 'expected.json': 'ef2c7cff76818ada54115890381e6fd65691dba04bd8331bcdb6f2b9bf624d99'}.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), digest)
        expected = json.loads((FIXTURE / "expected.json").read_text())
        self.assertEqual(expected["cpu_revision"], "5b686a45b5c56329adf0c63cbcf572eb6f23fad1")
        self.assertEqual(len(expected["source_hashes"]), 5)
        cases = json.loads((FIXTURE / "cases.json").read_text())
        self.assertEqual(len(cases), 38)
        self.assertEqual({c["uniforms"]["corner"] for c in cases}, {0, 1, 2, 3})
        self.assertEqual({c["image"] for c in cases}, {"solid", "asymmetric"})

    def test_captures_reproduce_from_authenticated_cpu(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce the OsdCurrent capture")
        cases = json.loads((FIXTURE / "cases.json").read_text())
        with tempfile.TemporaryDirectory(prefix="osd-current-reference-inputs-") as raw:
            inputs = pathlib.Path(raw) / "inputs.json"
            inputs.write_text(json.dumps(reference_inputs(cases)))
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), configured, str(inputs)],
                                    capture_output=True, check=True)
        self.assertEqual(result.stdout, (FIXTURE / "expected.json").read_bytes())

    def test_reference_authenticates_cpu_before_import(self):
        with tempfile.TemporaryDirectory(prefix="osd-current-forged-authority-") as raw:
            root = pathlib.Path(raw)
            source = root / "src/effects/generated/canonical-kernels.js"
            source.parent.mkdir(parents=True)
            source.write_text("throw new Error('untrusted module executed');\n")
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), str(root),
                                     str(FIXTURE / "cases.json")], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CPU source hash mismatch", result.stderr)
            self.assertNotIn("Error: untrusted module executed", result.stderr)


class OsdHistoricalKernelTests(unittest.TestCase):
    def test_frozen_kernel_reconstructs_with_explicit_historical_division(self):
        path = ROOT / "tests/fixtures/historical/osd_kernel.cpp"
        fixture = path.read_bytes()
        begin = fixture.index(b"// Typed IR program: filter/osd:osd\n")
        block = fixture[begin:fixture.index(b"// End frozen OSD block\n")]
        self.assertEqual(hashlib.sha256(block).hexdigest(),
                         "8c0efabd8c85bec68d7d6ed09b481b9efb8b1dd285c8d53ebd7072b65b20cb9a")
        entry = next(row for row in corpus_census.historical_document("manifest.json")["programs"]
                     if row["program_key"] == KEY)
        source = (corpus_census.HISTORICAL_CORPUS / entry["source"]).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), entry["raw_sha256"])
        program = analyze_program(parse_program(source.decode(), KEY, {}), KEY)
        with mock.patch.object(emit_typed_cpp, "OSD_GLYPH_INDEX_TRUNCATES", False):
            rendered = render_typed_cpp(program, KEY, entry["raw_sha256"], "typed_93",
                                       "bind_filter_osd_osd", osd_frontend_profile="osd-frontend-admission-v1")
        self.assertEqual(block, (rendered + "\n").encode())
        self.assertTrue(emit_typed_cpp.OSD_GLYPH_INDEX_TRUNCATES)
        cmake = (ROOT / "CMakeLists.txt").read_text()
        filename = "tests/fixtures/historical/osd_kernel.cpp"
        self.assertEqual(cmake.count(filename), 1)
        self.assertIn(filename, cmake.split("add_executable(noisemaker-cpu-tests\n", 1)[1].split("\n)", 1)[0])
