"""CPU26d Corrupt regression for copied rather than aliased sample UVs."""
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

from tools.glslcpp import check_corpus, generate_typed_slice
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.corrupt_value_copy_profile import (
    PROFILE, RAW_SHA256, authenticate_corrupt_value_copy)
from tools.glslcpp import emit_typed_cpp
from tests import corpus_census
from tests.gate import full_run_only

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/corrupt"
KEY = "filter/corrupt:corrupt"
PARAMETERS = ("intensity", "bandHeight", "sort", "shift", "channelShift", "melt", "scatter", "bits", "speed", "seed")


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
              "sources/filter/corrupt/corrupt.glsl").read_text()
    digest = hashlib.sha256(source.encode()).hexdigest()
    program = analyze_program(parse_program(source, KEY, {}), KEY)
    spec = generate_typed_slice.load_slice(ROOT)
    transform = spec["compatibility_transforms"].get(KEY)
    if transform:
        program = generate_typed_slice.apply_compatibility_transform(program, transform)
    return render_typed_cpp(program, KEY, digest, compatibility_transform=transform,
                            factory="bind_corrupt_numerical_probe")


@full_run_only
class CorruptKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="corrupt-kernel-")
        cls.addClassCleanup(cls.temporary.cleanup)
        temporary = pathlib.Path(cls.temporary.name)
        (temporary / "corrupt_emitted.inc").write_text(emitted_kernel())
        cls.binary = temporary / "probe"
        compiler = shutil.which("clang++") or shutil.which("c++")
        if compiler is None:
            raise AssertionError("a C++20 compiler is required for Corrupt kernel verification")
        result = subprocess.run([
            compiler, "-std=c++20", "-O1", "-ffp-contract=off", "-I", str(ROOT / "include"),
            "-I", str(temporary), str(FIXTURE / "probe.cpp"),
            *(str(ROOT / "src" / f"{name}.cpp") for name in
              ("surface", "numeric", "sampler", "glsl_runtime", "kernel", "fdlibm", "fdlibm_off")),
            "-o", str(cls.binary),
        ], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def test_displaced_sampling_and_original_xor_coordinates_match_cpu(self):
        cases = json.loads((FIXTURE / "cases.json").read_text())
        captures = json.loads((FIXTURE / "expected.json").read_text())["results"]
        self.assertEqual(len(cases), 18)
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


class CorruptReferenceTests(unittest.TestCase):
    def test_capture_provenance_and_coverage(self):
        for name, digest in {
                "cases.json": "3a8fe2538d58395696245eec7425b5491e3e6ca2135ea85240b7f7c3ee762e53",
                "expected.json": "4dade199a535207d7d623f6351f719d0f020d9202a45c106c096cd46bca1f14e"}.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), digest)
        expected = json.loads((FIXTURE / "expected.json").read_text())
        self.assertEqual(expected["cpu_revision"], "5b686a45b5c56329adf0c63cbcf572eb6f23fad1")
        self.assertEqual(len(expected["source_hashes"]), 5)
        cases = json.loads((FIXTURE / "cases.json").read_text())
        self.assertEqual({c["name"].split("-")[0] for c in cases},
                         {"v1", "v2", "v3", "v6", "v7", "v9", "v13", "v17", "v18"})
        self.assertEqual({c["image"] for c in cases}, {"solid", "asymmetric"})

    def test_captures_reproduce_from_authenticated_cpu(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce the Corrupt capture")
        cases = json.loads((FIXTURE / "cases.json").read_text())
        with tempfile.TemporaryDirectory(prefix="corrupt-reference-inputs-") as raw:
            inputs = pathlib.Path(raw) / "inputs.json"
            inputs.write_text(json.dumps(reference_inputs(cases)))
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), configured, str(inputs)],
                                    capture_output=True, check=True)
        self.assertEqual(result.stdout, (FIXTURE / "expected.json").read_bytes())

    def test_reference_authenticates_cpu_before_import(self):
        with tempfile.TemporaryDirectory(prefix="corrupt-forged-authority-") as raw:
            root = pathlib.Path(raw)
            source = root / "src/effects/generated/canonical-kernels.js"
            source.parent.mkdir(parents=True)
            source.write_text("throw new Error('untrusted module executed');\n")
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), str(root),
                                     str(FIXTURE / "cases.json")], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CPU source hash mismatch", result.stderr)
            self.assertNotIn("Error: untrusted module executed", result.stderr)


class CorruptCopyProfileTests(unittest.TestCase):
    def program(self):
        source = (ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION /
                  "sources/filter/corrupt/corrupt.glsl").read_text()
        return analyze_program(parse_program(source, KEY, {}), KEY)

    def test_live_copy_and_historical_alias_are_explicit_and_separate(self):
        current = generate_typed_slice.load_slice(ROOT)
        self.assertEqual(current["compatibility_transforms"][KEY], PROFILE)
        historical = corpus_census.without_expansion(current)
        self.assertEqual(historical["compatibility_transforms"][KEY], "corrupt-sample-uv-alias-v1")
        node = authenticate_corrupt_value_copy(self.program(), RAW_SHA256, PROFILE)
        self.assertEqual(node.symbol.name, "sampleUv")
        self.assertEqual(node.children[0].symbol.name, "uv")

    def test_source_ir_key_and_profile_forgery_fail_closed(self):
        program = self.program()
        candidates = [dataclasses.replace(program, raw_source=program.raw_source + "\n"),
                      dataclasses.replace(program, key="foreign:key"),
                      dataclasses.replace(program, functions=tuple(reversed(program.functions))),
                      generate_typed_slice.apply_compatibility_transform(program, "corrupt-sample-uv-alias-v1")]
        for candidate in candidates:
            with self.subTest(candidate=candidate.key), self.assertRaisesRegex(ValueError, "source or typed program"):
                authenticate_corrupt_value_copy(candidate, RAW_SHA256, PROFILE)
            with self.assertRaisesRegex(ValueError, "source or typed program"):
                render_typed_cpp(candidate, candidate.key, RAW_SHA256, compatibility_transform=PROFILE)
        for digest, profile in (("0" * 64, PROFILE), (RAW_SHA256, "unknown")):
            with self.assertRaisesRegex(ValueError, "source or typed program"):
                authenticate_corrupt_value_copy(program, digest, profile)

    def test_emitter_rejects_a_skipped_copy_lowering(self):
        original = emit_typed_cpp._Emitter._collect_pooled_vector_aliases

        def force_alias(emitter, statement):
            original(emitter, statement)
            for node in emitter.authorized_vector_value_copies:
                emitter.alias_declaration_symbol_ids.add(node.symbol_id)

        with mock.patch.object(emit_typed_cpp._Emitter, "_collect_pooled_vector_aliases", force_alias):
            with self.assertRaisesRegex(ValueError, "vector value-copy emission mismatch"):
                emitted_kernel()
