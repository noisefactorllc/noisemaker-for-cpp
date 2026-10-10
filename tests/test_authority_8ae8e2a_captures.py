"""Current-authority captures for the programs 8ae8e2a / 5976b7a6 changed.

The sweep feeds solid inputs, which cannot see where a kernel samples; these
cases use asymmetric textures with white and all-zero pixels and a nonzero
tile offset, so both vector-equality arms, coalesce's refracted UVs and the
tiled displacement paths are all observable. tests/test_typed_slice.cpp
renders the same cases through the public factory route and requires these
bytes exactly; this module keeps that table, the case file and the capture in
lockstep and reproduces the capture from an authenticated CPU checkout.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import struct
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/authority_8ae8e2a"
NATIVE = ROOT / "tests/test_typed_slice.cpp"
BEGIN = "// AUTHORITY_8AE8E2A_CASES_BEGIN\n"
END = "// AUTHORITY_8AE8E2A_CASES_END\n"
KINDS = {"int": "'i'", "float": "'f'", "bool": "'b'", "vec3": "'3'"}


def _f32_word(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def native_table(cases: list[dict], results: list[dict]) -> str:
    """The exact C++ table the native test carries between the markers."""
    if [case["name"] for case in cases] != [row["name"] for row in results]:
        raise AssertionError("capture order does not match the cases")
    lines = [BEGIN, "constexpr std::array<Authority8ae8e2aCase, %d> kAuthority8ae8e2aCases{{\n" % len(cases)]
    for case, row in zip(cases, results):
        lines.append(
            f'    {{"{case["name"]}", "{case["key"]}", {case["width"]}U, {case["height"]}U, '
            f'0x{_f32_word(case["time"]):08x}U, {case["seed"]}, {case["frame"]}U, '
            f'{{{case["tileOffset"][0]:.1f}f, {case["tileOffset"][1]:.1f}f}}, '
            f'{{{case["fullResolution"][0]:.1f}f, {case["fullResolution"][1]:.1f}f}},\n'
            f'     "{row["float32_sha256"]}",\n'
            f'     "{row["rgba8_sha256"]}"}},\n')
    lines.append("}};\n")
    uniforms = []
    textures = []
    for index, case in enumerate(cases):
        for name, (kind, value) in case["uniforms"].items():
            if kind == "vec3":
                words = [_f32_word(item) for item in value]
            elif kind == "float":
                words = [_f32_word(value), 0, 0]
            elif kind == "bool":
                words = [1 if value else 0, 0, 0]
            else:
                words = [value & 0xFFFFFFFF, 0, 0]
            uniforms.append(f'    {{{index}U, "{name}", {KINDS[kind]}, '
                            f'{{0x{words[0]:08x}U, 0x{words[1]:08x}U, 0x{words[2]:08x}U}}}},\n')
        for name, spec in case["textures"].items():
            textures.append(f'    {{{index}U, "{name}", {spec["width"]}U, {spec["height"]}U, {spec["tag"]}U}},\n')
    lines.append("constexpr std::array<Authority8ae8e2aUniform, %d> kAuthority8ae8e2aUniforms{{\n" % len(uniforms))
    lines.extend(uniforms)
    lines.append("}};\n")
    lines.append("constexpr std::array<Authority8ae8e2aTexture, %d> kAuthority8ae8e2aTextures{{\n" % len(textures))
    lines.extend(textures)
    lines.append("}};\n")
    lines.append(END)
    return "".join(lines)


def _load():
    cases = json.loads((FIXTURE / "cases.json").read_text(encoding="utf-8"))
    expected = json.loads((FIXTURE / "expected.json").read_text(encoding="utf-8"))
    return cases, expected


class Authority8ae8e2aCaptureTests(unittest.TestCase):
    def test_capture_provenance_and_coverage(self):
        for name, digest in {
                "cases.json": "0ff8b1e3a2892b3330ecefa3d5101ee74a6c13131efee5c7baf0ccf18a425bb3",
                "expected.json": "d8b339daee1addfa3c7957c4686330f85bee909483c5cac64f53ccfdfd4799e3"}.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), digest, name)
        cases, expected = _load()
        self.assertEqual("8ae8e2ae97812952db49246a87b04d7e5a480494", expected["cpu_revision"])
        self.assertEqual(6, len(expected["source_hashes"]))
        self.assertEqual(
            {"classicNoisedeck/coalesce:coalesce", "classicNoisedeck/refract:refract",
             "classicNoisedeck/lensDistortion:lensDistortion", "classicNoisedeck/colorLab:colorLab",
             "mixer/cellSplit:cellSplit", "filter/degauss:degauss",
             "classicNoisedeck/effects:effects", "filter/scale:scale"},
            {case["key"] for case in cases})
        self.assertEqual(len(cases), len({row["float32_sha256"] for row in expected["results"]}))

    def test_native_table_is_the_capture(self):
        cases, expected = _load()
        source = NATIVE.read_text(encoding="utf-8")
        start = source.index(BEGIN)
        end = source.index(END, start) + len(END)
        self.assertEqual(native_table(cases, expected["results"]), source[start:end])

    def test_capture_reproduces_from_authenticated_cpu(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce the 8ae8e2a capture")
        # This fixture pins the historical 8ae8e2a authority byte-for-byte (its
        # reference.mjs authenticates that revision). Its native-table and
        # provenance assertions above always run; the live reproduce leg needs
        # that exact revision present -- a later pinned authority is a
        # different CPU and fails the fixture's own hash gate, so skip when
        # the configured root is not the 8ae8e2a revision.
        pinned = "f4f3c23286da0d72032a6156ed1bd641b93a39d54a6e1812079280d2d3243e70"
        canonical = pathlib.Path(configured) / "src/effects/generated/canonical-kernels.js"
        digest = hashlib.sha256(canonical.read_bytes()).hexdigest()
        if digest != pinned:
            self.skipTest(f"the 8ae8e2a capture needs that CPU revision, not {digest[:12]}")
        result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), configured,
                                 str(FIXTURE / "cases.json")], capture_output=True, check=True)
        self.assertEqual(result.stdout, (FIXTURE / "expected.json").read_bytes())

    def test_reference_authenticates_cpu_before_import(self):
        with tempfile.TemporaryDirectory(prefix="authority-8ae8e2a-forged-") as raw:
            root = pathlib.Path(raw)
            source = root / "src/effects/generated/canonical-kernels.js"
            source.parent.mkdir(parents=True)
            source.write_text("throw new Error('untrusted module executed');\n")
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), str(root),
                                     str(FIXTURE / "cases.json")], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CPU source hash mismatch", result.stderr)
            self.assertNotIn("Error: untrusted module executed", result.stderr)


if __name__ == "__main__":
    unittest.main()
