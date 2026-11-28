"""Independent current-CPU captures for the full-pass triangle adapter."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from tests.gate import full_run_only

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/mesh_render"

CAPTURE_FILES = {
    ("darwin", "arm64"): "expected.json",
    ("linux", "aarch64"): "expected.json",
    ("linux", "x86_64"): "expected_linux_x86_64_node26.json",
}


def capture_path():
    profile = (sys.platform, platform.machine().lower())
    if profile not in CAPTURE_FILES:
        raise AssertionError(f"unsupported Mesh Node 26 capture profile: {profile}")
    return FIXTURE / CAPTURE_FILES[profile]


def probe_input(case):
    values = [case["width"], case["height"], case["tex_width"], case["tex_height"],
              *case["clear"], len(case["positions"]), *case["positions"],
              len(case["normals"]), *case["normals"]]
    scalars = {k: v for k, v in case["uniforms"].items() if not isinstance(v, list)}
    vectors = {k: v for k, v in case["uniforms"].items() if isinstance(v, list)}
    values.append(len(scalars))
    for name, value in scalars.items():
        values.extend((name, value))
    values.append(len(vectors))
    for name, value in vectors.items():
        values.extend((name, *value))
    full_resolution = case["bindings"].get("fullResolution")
    values.extend((int(full_resolution is not None), *(full_resolution or [])))
    count = case.get("pass", {"count": "input"}).get("count")
    count_value = ('"' + count.replace('\\', '\\\\').replace('"', '\\"') + '"'
                   if isinstance(count, str) else count if count is not None else "-")
    values.extend(("number" if isinstance(count, (int, float)) else "string" if count is not None else "absent",
                   count_value,
                   case.get("pass", {}).get("countUniform", "-")))
    inputs = case.get("inputs", {"meshPositions": {"width": case["tex_width"], "height": case["tex_height"]}})
    extent = inputs.get("meshPositions", inputs.get("inputTex"))
    values.extend((int(extent is not None), *((extent["width"], extent["height"]) if extent else ())))
    return " ".join(map(str, values))


def count_cases():
    basic = json.loads((FIXTURE / "cases.json").read_text())[0]
    # The first triangle is culled. The second produces the existing basic
    # capture, so both outcomes have independently captured words and bytes.
    small = {"width": 3, "height": 1}
    large = {"width": 3, "height": 2}
    rows = [
        ("literal-six", 6, None, {}, True),
        ("literal-fraction", 5.99, None, {}, False),
        ("literal-zero", 0, None, {}, False),
        ("uniform-overrides-literal", 3, "six", {}, True),
        ("uniform-overrides-extent", "screen", "two", {"meshPositions": large}, False),
        ("zero-uniform-falls-back", 6, "zero", {}, True),
        ("missing-uniform-falls-back", 6, "missing", {}, True),
        ("vector-uniform-falls-back", 6, "meshColor", {}, True),
        ("mesh-positions-extent", "input", None, {"meshPositions": large, "inputTex": small}, True),
        ("positions-precede-input", "input", None, {"meshPositions": small, "inputTex": large}, False),
        ("screen-uses-input-extent", "screen", None, {"inputTex": large}, True),
        ("auto-uses-input-extent", "auto", None, {"inputTex": large}, True),
        ("extent-absent", "input", None, {}, False),
        ("no-count", None, None, {"meshPositions": large}, False),
        ("oversized-count", 1e12, None, {}, True),
    ]
    for name, count, uniform, inputs, draws in rows:
        draw_pass = {} if count is None else {"count": count}
        if uniform is not None:
            draw_pass["countUniform"] = uniform
        yield {**basic, "name": name, "positions": [0] * 12 + basic["positions"],
               "normals": basic["normals"] * 2, "pass": draw_pass, "inputs": inputs,
               "uniforms": {**basic["uniforms"], "six": 6, "two": 2, "zero": 0}}, draws
    for literal, draws in [("+3", True), (" 3 ", True), ("\ufeff3\u00a0", True),
                           ("0x3", True), ("0b11", True), ("0o3", True),
                           ("+.3e1", True), ("1e9999", True), ("Infinity", True),
                           ("1e-9999", False), ("+0x3", False), ("0x3p0", False),
                           ("0b12", False), ("inf", False), ("  ", False), ("3px", False)]:
        yield {**basic, "name": f"count-string-{literal!r}", "pass": {"count": literal}}, draws


@full_run_only
class MeshRenderAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="mesh-render-adapter-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.probe = pathlib.Path(cls.temporary.name) / "probe"
        compiler = shutil.which("clang++") or shutil.which("c++")
        if compiler is None:
            raise AssertionError("a C++20 compiler is required for mesh adapter verification")
        subprocess.run([
            compiler, "-std=c++20", "-O1", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror",
            "-I", str(ROOT / "include"), str(FIXTURE / "probe.cpp"),
            *(str(ROOT / name) for name in (
                "src/effects/mesh_render.cpp", "src/numeric.cpp", "src/surface.cpp",
                "src/glsl_runtime.cpp", "src/fdlibm.cpp", "src/fdlibm_off.cpp")),
            "-o", str(cls.probe),
        ], check=True, capture_output=True, text=True)

    def test_exact_cpu_words_bytes_and_covered_counts(self):
        cases = json.loads((FIXTURE / "cases.json").read_text())
        expected = json.loads(capture_path().read_text())["results"]
        self.assertEqual([case["name"] for case in cases], [row["name"] for row in expected])
        self.assertEqual(len(cases), 23)
        basic, clear = expected[0], next(row for row in expected if row["name"] == "all-invalid-alpha")
        for case, row in [*zip(cases, expected, strict=True),
                          *((case, basic if draws else clear) for case, draws in count_cases())]:
            with self.subTest(case=case["name"]):
                result = subprocess.run([str(self.probe)], input=probe_input(case),
                                        text=True, capture_output=True, check=True)
                count, words, rgba8 = result.stdout.splitlines()
                self.assertEqual(int(count), row["pixels"])
                self.assertEqual(list(map(int, words.split())), row["words"])
                self.assertEqual(list(map(int, rgba8.split())), row["rgba8"])


class MeshRenderAuthorityTests(unittest.TestCase):
    def test_count_controls_match_current_cpu(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce the CPU capture")
        cases = list(count_cases())
        expected = json.loads(capture_path().read_text())["results"]
        basic, clear = expected[0], next(row for row in expected if row["name"] == "all-invalid-alpha")
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory, "count-cases.json")
            path.write_text(json.dumps([case for case, _ in cases]))
            output = subprocess.check_output(["node", str(FIXTURE / "reference.mjs"), configured, str(path)])
        for (case, draws), row in zip(cases, json.loads(output)["results"], strict=True):
            with self.subTest(case=case["name"]):
                self.assertEqual(row, {**(basic if draws else clear), "name": case["name"]})

    def test_capture_profile_is_explicit(self):
        for system, machine, filename in (
                ("darwin", "arm64", "expected.json"),
                ("linux", "aarch64", "expected.json"),
                ("linux", "x86_64", "expected_linux_x86_64_node26.json")):
            with mock.patch.object(sys, "platform", system), mock.patch.object(
                    platform, "machine", return_value=machine):
                self.assertEqual(capture_path().name, filename)
        with mock.patch.object(sys, "platform", "win32"):
            with self.assertRaisesRegex(AssertionError, "unsupported Mesh Node 26 capture profile"):
                capture_path()

    def test_capture_has_immutable_cpu_provenance(self):
        expected = json.loads(capture_path().read_text())
        self.assertEqual(expected["cpu_revision"], "e6f401303906445929ef14cca78a1507fbf38c4e")
        self.assertEqual(expected["source_hashes"], {
            "src/effects/cpu/mesh-render.js": "832a804f357173542daa4bd66f57fc4a0ae7c8388f0c5fdae7fe5408368a95c8",
            "src/runtime/external-input.js": "705f8f27b29e6ddc2334eb1e9af6ad57004063d848ea3bee9356626218c12757",
            "src/runtime/surface.js": "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
        })
        for name, digest in FIXTURE_HASHES.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), digest)

    def test_node26_captures_differ_only_at_invalid_pow_nan(self):
        arm = json.loads((FIXTURE / "expected.json").read_text())
        x86 = json.loads((FIXTURE / "expected_linux_x86_64_node26.json").read_text())
        self.assertEqual(arm["cpu_revision"], x86["cpu_revision"])
        self.assertEqual(arm["source_hashes"], x86["source_hashes"])
        self.assertEqual(len(arm["results"]), 23)
        self.assertEqual([row["name"] for row in arm["results"]],
                         [row["name"] for row in x86["results"]])
        for arm_row, x86_row in zip(arm["results"], x86["results"], strict=True):
            self.assertEqual(arm_row["pixels"], x86_row["pixels"])
            self.assertEqual(arm_row["rgba8"], x86_row["rgba8"])
            if arm_row["name"] != "negative-color-nan":
                self.assertEqual(arm_row["words"], x86_row["words"])
                continue
            differences = [(left, right) for left, right in
                           zip(arm_row["words"], x86_row["words"], strict=True)
                           if left != right]
            self.assertEqual(differences, [(0x7FC00000, 0xFFC00000)] * 15)

    def test_capture_reproduces_from_authenticated_current_cpu(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce the CPU capture")
        version = subprocess.run(["node", "--version"], check=True, capture_output=True,
                                 text=True).stdout.strip()
        self.assertTrue(version.startswith("v26."),
                        f"Mesh capture requires Node 26; received {version}")
        result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), configured,
                                 str(FIXTURE / "cases.json")],
                                check=True, capture_output=True, text=True)
        self.assertEqual(result.stdout.encode(), capture_path().read_bytes())

    def test_reference_rejects_modified_cpu_before_import(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        paths = ["src/effects/cpu/mesh-render.js"]
        if configured:
            paths.append("src/runtime/external-input.js")
        for path in paths:
            with self.subTest(path=path), tempfile.TemporaryDirectory(
                    prefix="mesh-render-forgery-") as raw:
                root = pathlib.Path(raw)
                if path == "src/runtime/external-input.js":
                    adapter = root / paths[0]
                    adapter.parent.mkdir(parents=True)
                    adapter.write_bytes((pathlib.Path(configured) / paths[0]).read_bytes())
                source = root / path
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text("throw new Error('untrusted module executed');\n")
                result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), str(root),
                                         str(FIXTURE / "cases.json")], text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"CPU source hash mismatch: {path}", result.stderr)
                self.assertNotIn("Error: untrusted module executed", result.stderr)


FIXTURE_HASHES = {
    "cases.json": "161358e3d0bfb3bcb2798d05ff5c2c681982d369441726256d265458b8c65830",
    "expected.json": "608efc215d3e8542fcf5522ff5ab432acea66cb1cbd407023f22bda92410d778",
    "expected_linux_x86_64_node26.json": "58e0ac433ded736dbf476d67bc4246fc9645dc774ea8bbec3872fc307f478e83",
}
