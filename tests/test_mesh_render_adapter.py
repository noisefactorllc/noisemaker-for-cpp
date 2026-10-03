"""Independent CPU26d captures for the full-pass triangle adapter."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/mesh_render"


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
    return " ".join(map(str, values))


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
        expected = json.loads((FIXTURE / "expected.json").read_text())["results"]
        self.assertEqual([case["name"] for case in cases], [row["name"] for row in expected])
        self.assertEqual(len(cases), 23)
        for case, row in zip(cases, expected, strict=True):
            with self.subTest(case=case["name"]):
                result = subprocess.run([str(self.probe)], input=probe_input(case),
                                        text=True, capture_output=True, check=True)
                count, words, rgba8 = result.stdout.splitlines()
                self.assertEqual(int(count), row["pixels"])
                self.assertEqual(list(map(int, words.split())), row["words"])
                self.assertEqual(list(map(int, rgba8.split())), row["rgba8"])


class MeshRenderAuthorityTests(unittest.TestCase):
    def test_capture_has_immutable_cpu_provenance(self):
        expected = json.loads((FIXTURE / "expected.json").read_text())
        self.assertEqual(expected["cpu_revision"], "26d6f42be38da7172f602373e844f85a8155356f")
        self.assertEqual(expected["source_hashes"], {
            "src/effects/cpu/mesh-render.js": "4fa90cc2681e51dce259e79bf807fb352868cc5e31823a313c818b7c1deeb051",
            "src/runtime/surface.js": "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
        })
        for name, digest in FIXTURE_HASHES.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), digest)

    def test_capture_reproduces_from_authenticated_current_cpu(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce the CPU capture")
        result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), configured,
                                 str(FIXTURE / "cases.json")],
                                check=True, capture_output=True, text=True)
        self.assertEqual(result.stdout.encode(), (FIXTURE / "expected.json").read_bytes())

    def test_reference_rejects_modified_cpu_before_import(self):
        with tempfile.TemporaryDirectory(prefix="mesh-render-forgery-") as raw:
            root = pathlib.Path(raw)
            source = root / "src/effects/cpu/mesh-render.js"
            source.parent.mkdir(parents=True)
            source.write_text("throw new Error('untrusted module executed');\n")
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), str(root),
                                     str(FIXTURE / "cases.json")], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CPU source hash mismatch: src/effects/cpu/mesh-render.js", result.stderr)
            self.assertNotIn("Error: untrusted module executed", result.stderr)


FIXTURE_HASHES = {
    "cases.json": "161358e3d0bfb3bcb2798d05ff5c2c681982d369441726256d265458b8c65830",
    "expected.json": "01a96fd648596c5d3de2b2a9afd6a7e9ce95ef1da241c6a29e865e1b3804b854",
}
