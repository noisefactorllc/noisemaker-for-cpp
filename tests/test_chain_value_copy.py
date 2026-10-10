"""CPU26d numerical and authentication checks for copied chain locals."""
from __future__ import annotations

import dataclasses
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

from tools.glslcpp import check_corpus, emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.loop_proof import SOURCE_GLOBAL_LITERAL_INT_KEYS, SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
from tools.glslcpp.frontend.chain_value_copy_profile import CONTRACTS, authenticate_chain_value_copies
from tests.gate import full_run_only

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/chain_value_copy"


def packed_input(case):
    values = [((x * 17 + y * 29 + c * 43 + 7) % 251) / 250 if c < 3 else 1
              for y in range(case["height"]) for x in range(case["width"]) for c in range(4)]
    return struct.pack(f"<{len(values)}f", *values)


def program(key):
    effect, name = key.split(":")
    raw = (ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION /
           "sources" / effect / (name + ".glsl")).read_text()
    return analyze_program(parse_program(raw, key, {}), key,
                           source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
                           if key in SOURCE_GLOBAL_LITERAL_INT_KEYS else None)


def emitted_kernel(key):
    typed = program(key)
    row = next(row for row in generate_typed_slice.load_slice(ROOT)["programs"]
               if row["program_key"] == key)
    name = key.split(":")[1]
    return emit_typed_cpp.render_typed_cpp(
        typed, key, CONTRACTS[key][0], namespace="copy_" + name,
        factory="bind_" + name + "_copy_probe",
        source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
        if key in SOURCE_GLOBAL_LITERAL_INT_KEYS else None,
        **{name: value for name, value in row.items() if name.endswith("_profile")})


@full_run_only
class ChainValueCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="chain-copy-native-")
        cls.addClassCleanup(cls.temporary.cleanup)
        root = pathlib.Path(cls.temporary.name)
        compiler = shutil.which("clang++") or shutil.which("c++")
        if compiler is None:
            raise AssertionError("a C++20 compiler is required for chain copy verification")
        cls.binaries = {}
        for current in (False, True):
            with mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_VALUE_COPIES", current):
                (root / "chain_copy_emitted.inc").write_text("\n".join(emitted_kernel(key) for key in CONTRACTS))
            binary = root / ("current" if current else "historical")
            result = subprocess.run([
                compiler, "-std=c++20", "-O1", "-ffp-contract=off", "-I", str(ROOT / "include"),
                "-I", str(root), str(FIXTURE / "probe.cpp"),
                *(str(ROOT / "src" / (name + ".cpp")) for name in
                  ("surface", "numeric", "sampler", "glsl_runtime", "kernel", "fdlibm", "fdlibm_off")),
                "-o", str(binary)], capture_output=True, text=True)
            if result.returncode:
                raise AssertionError(result.stderr)
            cls.binaries[current] = binary

    def test_current_copies_match_cpu_and_old_aliases_are_discriminated(self):
        cases = json.loads((FIXTURE / "cases.json").read_text())
        captures = json.loads((FIXTURE / "expected.json").read_text())["results"]
        discriminated = set()
        self.assertEqual([case["name"] for case in cases], [row["name"] for row in captures])
        for case, expected in zip(cases, captures, strict=True):
            with self.subTest(case=case["name"]):
                uniforms = case["uniforms"]
                args = [case["width"], case["height"], case["key"].split(":")[1],
                        uniforms.get("strength", 0), uniforms.get("sharpness", .1),
                        uniforms.get("threshold", 0), uniforms.get("pivot", 0)]
                split = case["width"] * case["height"] * 16
                for current, binary in self.binaries.items():
                    result = subprocess.run([str(binary), *map(str, args)], input=packed_input(case),
                                            capture_output=True, check=True)
                    self.assertEqual(len(result.stdout), split + split // 4)
                    hashes = [hashlib.sha256(result.stdout[:split]).hexdigest(),
                              hashlib.sha256(result.stdout[split:]).hexdigest()]
                    expected_hashes = [expected["float32_sha256"], expected["rgba8_sha256"]]
                    if current:
                        self.assertEqual(hashes, expected_hashes)
                    elif hashes != expected_hashes:
                        discriminated.add(case["key"])
        self.assertEqual(discriminated, set(CONTRACTS))

    def test_capture_provenance_and_live_reproduction(self):
        for name, digest in {
            "cases.json": "609b4825df1db6ad466798e5f4f54cbf7cc4af454cb158d11b9a2ec7f182a141",
            "expected.json": "cf855852d9efcccb667c234b1f0f2080c4e2246336892a5b09d8ff675d85e270",
        }.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), digest)
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce chain captures")
        cases = json.loads((FIXTURE / "cases.json").read_text())
        with tempfile.TemporaryDirectory(prefix="chain-copy-inputs-") as raw:
            inputs = pathlib.Path(raw) / "inputs.json"
            inputs.write_text(json.dumps([{**case, "inputFloat32": packed_input(case).hex()} for case in cases]))
            result = subprocess.run(["node", str(FIXTURE / "reference.mjs"), configured, str(inputs)],
                                    capture_output=True, check=True)
        self.assertEqual(result.stdout, (FIXTURE / "expected.json").read_bytes())

    def test_exact_source_and_ir_forgery_fail_closed(self):
        for key, contract in CONTRACTS.items():
            typed = program(key)
            copies = authenticate_chain_value_copies(typed, contract[0])
            self.assertEqual(len(copies), 1)
            self.assertEqual(copies[0].symbol.name, contract[2])
            for forged in (dataclasses.replace(typed, key="foreign:key"),
                           dataclasses.replace(typed, raw_source=typed.raw_source + "\n"),
                           dataclasses.replace(typed, functions=tuple(reversed(typed.functions)))):
                with self.assertRaisesRegex(ValueError, "source or typed program"):
                    authenticate_chain_value_copies(forged, contract[0])
            with self.assertRaisesRegex(ValueError, "source or typed program"):
                authenticate_chain_value_copies(typed, "0" * 64)

    def test_current_and_historical_emission_are_explicitly_separate(self):
        for key, contract in CONTRACTS.items():
            with mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_VALUE_COPIES", False):
                historical = emitted_kernel(key)
            current = emitted_kernel(key)
            declaration = contract[3].replace("vec", "glsl::Vec")
            self.assertIn(declaration + "& " + contract[2] + " = " + contract[5], historical)
            self.assertNotIn(declaration + "& " + contract[2] + " = " + contract[5], current)
            self.assertIn(declaration + " " + contract[2] + " = " + contract[5], current)

    def test_emitter_rejects_skipped_authenticated_copy_lowering(self):
        original = emit_typed_cpp._Emitter._collect_pooled_vector_aliases

        def force_alias(emitter, statement):
            original(emitter, statement)
            for declaration in emitter.authorized_vector_value_copies:
                emitter.alias_declaration_symbol_ids.add(declaration.symbol_id)

        for key in CONTRACTS:
            with mock.patch.object(emit_typed_cpp._Emitter, "_collect_pooled_vector_aliases", force_alias):
                with self.assertRaisesRegex(ValueError, "authenticated vector value-copy emission mismatch"):
                    emitted_kernel(key)


class HistoricalParallaxTests(unittest.TestCase):
    def test_frozen_kernel_reconstructs_with_explicit_historical_aliases(self):
        from tests import corpus_census
        key = "filter/parallax:parallax"
        fixture = (ROOT / "tests/fixtures/historical/parallax_kernel.cpp").read_bytes()
        block = fixture[fixture.index(b"// Typed IR program: filter/parallax:parallax\n"):
                        fixture.index(b"// End frozen Parallax block\n")]
        self.assertEqual(hashlib.sha256(block).hexdigest(),
                         "c09dd3fbd9685caa9836add2b30addb9cbb4253b259a3f6bc575b8f1ec3d7b15")
        entry = next(row for row in corpus_census.historical_document("manifest.json")["programs"]
                     if row["program_key"] == key)
        source = (corpus_census.HISTORICAL_CORPUS / entry["source"]).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), entry["raw_sha256"])
        typed = analyze_program(parse_program(source.decode(), key, {}), key,
                                source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        with mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_VALUE_COPIES", False):
            rendered = emit_typed_cpp.render_typed_cpp(
                typed, key, entry["raw_sha256"], "typed_98", "bind_filter_parallax_parallax",
                source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
                texture_lod_admission_profile="texture-lod-admission-parallax-v1")
        self.assertEqual(block, (rendered + "\n").encode())
        self.assertTrue(emit_typed_cpp.CURRENT_AUTHORITY_VALUE_COPIES)
        cmake = (ROOT / "CMakeLists.txt").read_text()
        filename = "tests/fixtures/historical/parallax_kernel.cpp"
        self.assertEqual(cmake.count(filename), 1)
        self.assertIn(filename, cmake.split("add_executable(noisemaker-cpu-tests\n", 1)[1].split("\n)", 1)[0])
