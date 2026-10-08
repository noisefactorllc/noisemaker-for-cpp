"""CPU26d Reverb regression for isolated original, current and accumulation vectors."""
from __future__ import annotations

import hashlib
import dataclasses
import json
import os
import pathlib
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest import mock

from tools.glslcpp import check_corpus
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.reverb_value_copy_profile import (
    RAW_SHA256, authenticate_reverb_value_copies)
from tools.glslcpp import emit_typed_cpp
from tests.gate import full_run_only

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/reverb"
KEY = "filter/reverb:reverb"
PARAMETERS = ("iterations", "ridges", "alpha", "wrap")


def packed_input(case):
    width, height = case["width"], case["height"]
    values = [((x * 17 + y * 29 + c * 43 + 7) % 251) / 250 if c < 3 else 1
              for y in range(height) for x in range(width) for c in range(4)]
    return struct.pack(f"<{len(values)}f", *values)


def reference_inputs(cases):
    return [{**case, "inputFloat32": packed_input(case).hex()} for case in cases]


def emitted_kernel():
    source = (ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION /
              "sources/filter/reverb/reverb.glsl").read_text()
    digest = hashlib.sha256(source.encode()).hexdigest()
    program = analyze_program(parse_program(source, KEY, {}), KEY)
    return render_typed_cpp(program, KEY, digest,
                            factory="bind_reverb_numerical_probe")


@full_run_only
class ReverbKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="reverb-kernel-")
        cls.addClassCleanup(cls.temporary.cleanup)
        temporary = pathlib.Path(cls.temporary.name)
        (temporary / "reverb_emitted.inc").write_text(emitted_kernel())
        cls.binary = temporary / "probe"
        compiler = shutil.which("clang++") or shutil.which("c++")
        if compiler is None:
            raise AssertionError("a C++20 compiler is required for Reverb kernel verification")
        result = subprocess.run([
            compiler, "-std=c++20", "-O1", "-ffp-contract=off", "-I", str(ROOT / "include"),
            "-I", str(temporary), str(FIXTURE / "probe.cpp"),
            *(str(ROOT / "src" / f"{name}.cpp") for name in
              ("surface", "numeric", "sampler", "glsl_runtime", "kernel", "fdlibm", "fdlibm_off")),
            "-o", str(cls.binary),
        ], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def test_original_color_isolated_from_ridges_and_accumulation_matches_cpu(self):
        cases = json.loads((FIXTURE / "cases.json").read_text())
        captures = json.loads((FIXTURE / "expected.json").read_text())["results"]
        self.assertEqual(len(cases), 18)
        self.assertEqual([case["name"] for case in cases], [row["name"] for row in captures])
        for case, row in zip(cases, captures, strict=True):
            with self.subTest(case=case["name"]):
                args = [case["width"], case["height"], case["time"],
                        *(int(case["uniforms"][name]) if name == "ridges" else case["uniforms"][name] for name in PARAMETERS)]
                result = subprocess.run([str(self.binary), *map(str, args)], input=packed_input(case),
                                        capture_output=True, check=True)
                word_bytes = case["width"] * case["height"] * 16
                rgba_bytes = case["width"] * case["height"] * 4
                self.assertEqual(len(result.stdout), word_bytes + rgba_bytes)
                self.assertEqual(hashlib.sha256(result.stdout[:word_bytes]).hexdigest(), row["float32_sha256"])
                self.assertEqual(hashlib.sha256(result.stdout[word_bytes:]).hexdigest(), row["rgba8_sha256"])


class ReverbReferenceTests(unittest.TestCase):
    def test_capture_provenance_and_coverage(self):
        for name, digest in {
                "cases.json": "86ab3d3fe7e8a63ce56e3deec9faf1d928850ec32c94c82ab9dd6ab90d9dd530",
                "expected.json": "8198aa3d41fb888748db72e203e7897cc793b175a52c3337f8a64a33e3338882"}.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), digest)
        expected = json.loads((FIXTURE / "expected.json").read_text())
        self.assertEqual(expected["cpu_revision"], "26d6f42be38da7172f602373e844f85a8155356f")
        self.assertEqual(len(expected["source_hashes"]), 5)
        cases = json.loads((FIXTURE / "cases.json").read_text())
        self.assertEqual({c["uniforms"]["iterations"] for c in cases}, {1, 3, 8})
        self.assertEqual({c["uniforms"]["alpha"] for c in cases}, {0, .37, 1})
        self.assertEqual({c["uniforms"]["ridges"] for c in cases}, {False, True})
        self.assertEqual({c["uniforms"]["wrap"] for c in cases}, {0, 1, 2})

    def test_captures_reproduce_from_authenticated_cpu(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce the Reverb capture")
        cases = json.loads((FIXTURE / "cases.json").read_text())
        with tempfile.TemporaryDirectory(prefix="reverb-reference-inputs-") as raw:
            inputs = pathlib.Path(raw) / "inputs.json"
            inputs.write_text(json.dumps(reference_inputs(cases)))
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), configured, str(inputs)],
                                    capture_output=True, check=True)
        self.assertEqual(result.stdout, (FIXTURE / "expected.json").read_bytes())

    def test_reference_authenticates_cpu_before_import(self):
        with tempfile.TemporaryDirectory(prefix="reverb-forged-authority-") as raw:
            root = pathlib.Path(raw)
            source = root / "src/effects/generated/canonical-kernels.js"
            source.parent.mkdir(parents=True)
            source.write_text("throw new Error('untrusted module executed');\n")
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), str(root),
                                     str(FIXTURE / "cases.json")], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CPU source hash mismatch", result.stderr)
            self.assertNotIn("Error: untrusted module executed", result.stderr)


class ReverbCopyProfileTests(unittest.TestCase):
    def program(self):
        source = (ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION /
                  "sources/filter/reverb/reverb.glsl").read_text()
        return analyze_program(parse_program(source, KEY, {}), KEY)

    def test_exact_two_copies_and_source_ir_forgery_rejection(self):
        program = self.program()
        nodes = authenticate_reverb_value_copies(program, RAW_SHA256)
        self.assertEqual([n.symbol.name for n in nodes], ["current", "accum"])
        candidates = [dataclasses.replace(program, raw_source=program.raw_source + "\n"),
                      dataclasses.replace(program, key="foreign:key"),
                      dataclasses.replace(program, functions=tuple(reversed(program.functions))),
                      dataclasses.replace(program, counted_loop_proof=None)]
        for candidate in candidates:
            with self.subTest(key=candidate.key), self.assertRaisesRegex(ValueError, "source or typed program"):
                authenticate_reverb_value_copies(candidate, RAW_SHA256)
        with self.assertRaisesRegex(ValueError, "source or typed program"):
            authenticate_reverb_value_copies(program, "0" * 64)

    def test_historical_kernel_preserves_original_bytes_and_alias_semantics(self):
        fixture = (ROOT / "tests/fixtures/historical/reverb_kernel.cpp").read_bytes()
        begin = b"// Typed IR program: filter/reverb:reverb\n"
        end = b"// End frozen block: filter/reverb:reverb\n"
        block = fixture[fixture.index(begin):fixture.index(end)]
        # Exact block from a15c4b6816a3cb4a1811a03429e4fbf84530c722;
        # historical whole-TU SHA256 3f7c1644dc966f4f401e523ca0ea830d1ddc2e4372263e8710120930f2176b4c.
        self.assertEqual(hashlib.sha256(block).hexdigest(),
                         "16dc34f337bd054d056e19e165561c3df9cb811c2387b9454acb954ccb497d77")
        with mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_VALUE_COPIES", False):
            regenerated = render_typed_cpp(self.program(), KEY, RAW_SHA256,
                                          "typed_125", "bind_filter_reverb_reverb")
        self.assertEqual(block, (regenerated + "\n").encode())

    def test_copy_emission_census_rejects_a_missing_declaration(self):
        original = emit_typed_cpp._Emitter._collect_pooled_vector_aliases

        def force_alias(emitter, statement):
            original(emitter, statement)
            for node in emitter.authorized_vector_value_copies:
                emitter.alias_declaration_symbol_ids.add(node.symbol_id)

        with mock.patch.object(emit_typed_cpp._Emitter, "_collect_pooled_vector_aliases", force_alias):
            with self.assertRaisesRegex(ValueError, "vector value-copy emission mismatch"):
                emitted_kernel()
