"""CPU26d direct-kernel captures for Roll's admitted bounded loop."""

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

from tools.glslcpp import check_corpus
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.runtime_loop_bound_profile import PROFILE, apply_runtime_loop_bound
from tools.glslcpp.frontend.ceil_admission_profile import PROFILE as CEIL_PROFILE
from tests.gate import full_run_only

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/roll"
KEY = "synth/roll:roll"


def packed_inputs(case):
    """Top-down RGBA32F feedback plus a top-down MIDI texture, packed little-endian."""
    width, height = case["width"], case["height"]
    feedback = [((x * 17 + y * 29 + channel * 43 + 7) % 251) / 250.0
                for y in range(height) for x in range(width) for channel in range(4)]
    grid = [0.0] * (128 * 16 * 4)
    for channel in range(16):
        for key in range(128):
            active = case["grid"] == "bright" or (
                case["grid"] == "sparse" and key == 36 + (channel * 7) % 49)
            index = ((15 - channel) * 128 + key) * 4
            grid[index] = ((key * 11 + channel * 3) % 128 + 1) / 128.0 if active else 0
            grid[index + 1] = 1.0 if active else 0
    return struct.pack(f"<{len(feedback)}f", *feedback), struct.pack("<8192f", *grid)


def reference_inputs(cases):
    result = []
    for case in cases:
        feedback, grid = packed_inputs(case)
        result.append({**case, "feedbackFloat32": feedback.hex(), "gridFloat32": grid.hex()})
    return result


def emitted_kernel():
    corpus = ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION
    relative = "synth/roll/roll.glsl"
    source = next(p for section in ("sources", "pending-sources")
                  if (p := corpus / section / relative).is_file()).read_text()
    digest = hashlib.sha256(source.encode()).hexdigest()
    program = analyze_program(parse_program(source, KEY, {}), KEY)
    applied = apply_runtime_loop_bound(program, digest, PROFILE)
    return render_typed_cpp(applied, KEY, digest, runtime_loop_bound_profile=PROFILE,
                            ceil_admission_profile=CEIL_PROFILE,
                            factory="bind_roll_numerical_probe")


@full_run_only
class RollKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="roll-kernel-")
        cls.addClassCleanup(cls.temporary.cleanup)
        temporary = pathlib.Path(cls.temporary.name)
        (temporary / "roll_emitted.inc").write_text(emitted_kernel())
        cls.binary = temporary / "probe"
        compiler = shutil.which("clang++") or shutil.which("c++")
        if compiler is None:
            raise AssertionError("a C++20 compiler is required for Roll kernel verification")
        result = subprocess.run([
            compiler, "-std=c++20", "-O1", "-ffp-contract=off", "-I", str(ROOT / "include"),
            "-I", str(temporary), str(FIXTURE / "probe.cpp"),
            *(str(ROOT / "src" / f"{name}.cpp") for name in
              ("surface", "numeric", "sampler", "glsl_runtime", "kernel")),
            "-o", str(cls.binary),
        ], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def test_every_float32_word_and_rgba8_byte_matches_cpu(self):
        cases = json.loads((FIXTURE / "cases.json").read_text())
        captures = json.loads((FIXTURE / "expected.json").read_text())["results"]
        self.assertEqual(len(cases), 27)
        self.assertEqual([case["name"] for case in cases], [row["name"] for row in captures])
        for case, row in zip(cases, captures, strict=True):
            with self.subTest(case=case["name"]):
                feedback, grid = packed_inputs(case)
                args = [case["width"], case["height"], case["delta_time"], case["gain"],
                        case["speed"], *case["color"], case["filter"]]
                result = subprocess.run([str(self.binary), *map(str, args)], input=feedback + grid,
                                        capture_output=True, check=True)
                word_bytes = case["width"] * case["height"] * 16
                rgba_bytes = case["width"] * case["height"] * 4
                self.assertEqual(len(result.stdout), word_bytes + rgba_bytes)
                self.assertEqual((row["float32_bytes"], row["rgba8_bytes"]), (word_bytes, rgba_bytes))
                self.assertEqual(hashlib.sha256(result.stdout[:word_bytes]).hexdigest(), row["float32_sha256"])
                self.assertEqual(hashlib.sha256(result.stdout[word_bytes:]).hexdigest(), row["rgba8_sha256"])


class RollReferenceTests(unittest.TestCase):
    def test_capture_provenance_and_coverage(self):
        for name, digest in FIXTURE_HASHES.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), digest)
        expected = json.loads((FIXTURE / "expected.json").read_text())
        self.assertEqual(expected["cpu_revision"], "26d6f42be38da7172f602373e844f85a8155356f")
        self.assertEqual(len(expected["source_hashes"]), 5)
        cases = json.loads((FIXTURE / "cases.json").read_text())
        self.assertEqual({(c["width"], c["height"]) for c in cases}, {(1, 1), (17, 11), (64, 256)})
        self.assertEqual({c["grid"] for c in cases}, {"zero", "sparse", "bright"})
        self.assertEqual({c["delta_time"] for c in cases}, {0, .016, .2})
        self.assertEqual({c["gain"] for c in cases}, {.1, 1.37, 5})
        self.assertEqual({c["speed"] for c in cases}, {.5, 1.23, 5})
        self.assertEqual({c["filter"] for c in cases}, {"nearest", "linear"})
        for delta in (.016, .2):
            self.assertEqual({c["speed"] for c in cases if c["delta_time"] == delta}, {.5, 1.23, 5})
        self.assertEqual({(c["gain"], c["speed"]) for c in cases},
                         {(gain, speed) for gain in (.1, 1.37, 5) for speed in (.5, 1.23, 5)})

    def test_captures_reproduce_from_authenticated_current_cpu(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce the Roll capture")
        cases = json.loads((FIXTURE / "cases.json").read_text())
        with tempfile.TemporaryDirectory(prefix="roll-reference-inputs-") as raw:
            inputs = pathlib.Path(raw) / "inputs.json"
            inputs.write_text(json.dumps(reference_inputs(cases)))
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), configured, str(inputs)],
                                    capture_output=True, check=True)
        self.assertEqual(result.stdout, (FIXTURE / "expected.json").read_bytes())

    def test_reference_authenticates_cpu_before_import(self):
        with tempfile.TemporaryDirectory(prefix="roll-forged-authority-") as raw:
            root = pathlib.Path(raw)
            source = root / "src/effects/generated/canonical-kernels.js"
            source.parent.mkdir(parents=True)
            source.write_text("throw new Error('untrusted module executed');\n")
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), str(root),
                                     str(FIXTURE / "cases.json")], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CPU source hash mismatch", result.stderr)
            self.assertNotIn("Error: untrusted module executed", result.stderr)


FIXTURE_HASHES = {
    "cases.json": "7b4763eb3e72116ead1f7251dbe9c756918888bd92fb1197bf3fa455f5171c9c",
    "expected.json": "3499253e221300c0891fcaa4f795c1f5561aaa6153a7202a6d9c743f4e5ff1af",
}
