"""Exact runtime Kernel9 proof for the three convolution programs."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import unittest
from pathlib import Path

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
    PROFILES, attach_fixed_array_in_parameter_proof,
    prove_fixed_array_in_parameter, source_provenance_error)
from tools.glslcpp.frontend.dynamic_kernel9_profile import (
    LOCKS, authenticate_kaleido_offset_terminal,
    authenticate_effects_subpixel_value_copy)
from tools.glslcpp import generate_typed_slice as generator
from tools.glslcpp.emit_typed_cpp import render_typed_cpp, TypedEmissionError
from tools.glslcpp.generate_kernels import GeneratorError

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d"
HISTORICAL_EFFECTS_CORPUS = (
    ROOT / "tools/glslcpp/corpus/a1a3fa2a84223dfc1f5ec2c7a54a6f4269139c15")


class DynamicKernel9ProfileTests(unittest.TestCase):
    @staticmethod
    def candidate(key: str, dynamic: bool, *, current_default: bool = False):
        corpus = (HISTORICAL_EFFECTS_CORPUS
                  if key == "classicNoisedeck/effects:effects"
                  and not dynamic and not current_default else CORPUS)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == key)
        raw = (corpus / entry["source"]).read_text()
        if dynamic:
            defines = {name: "int" for name, _, _ in LOCKS[key]["defines"]}
            parsed = parse_program(transform_source(raw, key), key, defines)
            parsed["raw_source"] = raw
        else:
            defines = {item.name: int(item.canonical_value)
                       for item in PROFILES[key].preprocessor_defines}
            parsed = parse_program(raw, key, defines)
        return raw, analyze_program(parsed, key)

    def test_live_call_abi_and_default_proofs(self):
        for key, row in LOCKS.items():
            with self.subTest(key=key):
                raw, dynamic = self.candidate(key, True)
                proof = attach_fixed_array_in_parameter_proof(
                    dynamic).fixed_array_in_parameter_proof
                self.assertIsNotNone(proof)
                self.assertEqual("Kernel9", proof.kernel_alias)
                self.assertEqual(row["census"][-1], proof.array_call_count)
                self.assertEqual(len(row["global_calls"])
                                 + len(row["local_calls"]),
                                 len(proof.parameter.direct_argument_spans))
                self.assertIsNone(source_provenance_error(
                    dynamic, hashlib.sha256(raw.encode()).hexdigest()))
                _, default = self.candidate(key, False)
                old = prove_fixed_array_in_parameter(default)
                self.assertIsNotNone(old)
                self.assertEqual(PROFILES[key].source_profile,
                                 old.source_profile)
                self.assertEqual(8, old.array_call_count)
                if key == "classicNoisedeck/effects:effects":
                    _, current_frozen = self.candidate(
                        key, False, current_default=True)
                    self.assertIsNone(
                        prove_fixed_array_in_parameter(current_frozen))

    def test_kaleido_unmatched_offset_has_source_bound_nan_terminal(self):
        key = "classicNoisedeck/kaleido:kaleido"
        raw, dynamic = self.candidate(key, True)
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        offset = authenticate_kaleido_offset_terminal(dynamic, source_hash)
        self.assertEqual(135, offset.id)
        program = attach_fixed_array_in_parameter_proof(dynamic)
        rows = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text())["programs"]
        row = next(item for item in rows if item["program_key"] == key)
        carriers = ("mutable_global_array_profile", "scalar_uint_xor_profile",
                    "glitch_mat4_chain_profile", "ceil_admission_profile")
        kwargs = {name: row[name] for name in carriers if name in row}
        emitted = render_typed_cpp(program, key, source_hash, **kwargs)
        offset_body = emitted.split("[[nodiscard]] double offset(", 2)[-1].split(
            "[[nodiscard]] glsl::Vec3 outline(", 1)[0]
        self.assertEqual(1, offset_body.count(
            "return std::numeric_limits<double>::quiet_NaN();"))
        _, frozen = self.candidate(key, False)
        self.assertIsNotNone(prove_fixed_array_in_parameter(frozen))
        with self.assertRaises(ValueError):
            authenticate_kaleido_offset_terminal(dynamic, "0" * 64)
        with self.assertRaises(ValueError):
            authenticate_kaleido_offset_terminal(
                dataclasses.replace(dynamic, preprocessor_defines=()),
                source_hash)
        forged_offset = dataclasses.replace(offset, body=())
        forged = dataclasses.replace(dynamic, functions=tuple(
            forged_offset if function is offset else function
            for function in dynamic.functions))
        with self.assertRaises(ValueError):
            authenticate_kaleido_offset_terminal(forged, source_hash)

    def test_effects_subpixel_uses_exact_source_bound_value_copy(self):
        key = "classicNoisedeck/effects:effects"
        raw, dynamic = self.candidate(key, True)
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        copy = authenticate_effects_subpixel_value_copy(dynamic, source_hash)
        self.assertEqual(234, copy.symbol_id)
        program = attach_fixed_array_in_parameter_proof(dynamic)
        rows = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text())["programs"]
        row = next(item for item in rows if item["program_key"] == key)
        carriers = ("mutable_global_array_profile", "scalar_uint_xor_profile",
                    "glitch_mat4_chain_profile", "ceil_admission_profile")
        kwargs = {name: row[name] for name in carriers if name in row}
        emitted = render_typed_cpp(program, key, source_hash, **kwargs)
        self.assertIn("[[maybe_unused]] glsl::Vec3 color = orig;", emitted)
        self.assertNotIn("[[maybe_unused]] glsl::Vec3& color = orig;", emitted)
        _, frozen = self.candidate(key, False)
        self.assertIsNotNone(prove_fixed_array_in_parameter(frozen))
        with self.assertRaises(ValueError):
            authenticate_effects_subpixel_value_copy(dynamic, "0" * 64)
        with self.assertRaises(ValueError):
            authenticate_effects_subpixel_value_copy(
                dataclasses.replace(dynamic, preprocessor_defines=()),
                source_hash)
        subpixel = next(function for function in dynamic.functions
                        if function.name == "subpixel")
        forged = dataclasses.replace(dynamic, functions=tuple(
            dataclasses.replace(subpixel, body=()) if function is subpixel
            else function for function in dynamic.functions))
        with self.assertRaises(ValueError):
            authenticate_effects_subpixel_value_copy(forged, source_hash)

    def test_source_tree_and_define_forgery_rejected(self):
        for key in LOCKS:
            with self.subTest(key=key):
                raw, program = self.candidate(key, True)
                self.assertIsNone(prove_fixed_array_in_parameter(
                    dataclasses.replace(program, raw_source=raw + "\n")))
                self.assertIsNone(prove_fixed_array_in_parameter(
                    dataclasses.replace(program,
                                        preprocessor_defines=())))
                dispatch = next(function for function in program.functions
                                if function.name in
                                ("convolutionEffect", "convolutionKernel")
                                and function.body)
                forged = dataclasses.replace(dispatch, body=())
                mutated = dataclasses.replace(program, functions=tuple(
                    forged if function is dispatch else function
                    for function in program.functions))
                self.assertIsNone(prove_fixed_array_in_parameter(mutated))
                self.assertIsNotNone(source_provenance_error(
                    program, "0" * 64))

    def test_production_carriers_and_emission_reject_forgery(self):
        rows = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text())[
            "programs"]
        carriers = ("mutable_global_array_profile", "scalar_uint_xor_profile",
                    "glitch_mat4_chain_profile", "ceil_admission_profile")
        for key in LOCKS:
            with self.subTest(key=key):
                raw, candidate = self.candidate(key, True)
                program = attach_fixed_array_in_parameter_proof(candidate)
                source_hash = hashlib.sha256(raw.encode()).hexdigest()
                row = next(item for item in rows if item["program_key"] == key)
                kwargs = {name: row[name] for name in carriers if name in row}
                generator.validate_capabilities(
                    program, generator.APPROVED_CAPABILITIES,
                    source_hash=source_hash, **kwargs)
                emitted = render_typed_cpp(program, key, source_hash, **kwargs)
                self.assertIn("void pixel(", emitted)
                if key == "classicNoisedeck/effects:effects":
                    self.assertIn("glsl::dot(glsl::Vec4(glsl::dot(tv, A[0])", emitted)
                    self.assertIn("convolutionEffect(state, context, frame", emitted)
                for name in kwargs:
                    with self.subTest(carrier=name):
                        missing = {field: value for field, value in kwargs.items()
                                   if field != name}
                        with self.assertRaises(GeneratorError):
                            generator.validate_capabilities(
                                program, generator.APPROVED_CAPABILITIES,
                                source_hash=source_hash, **missing)
                        with self.assertRaises(GeneratorError):
                            generator.validate_capabilities(
                                program, generator.APPROVED_CAPABILITIES,
                                source_hash=source_hash,
                                **{**kwargs, name: "forged-profile"})
                with self.assertRaises(GeneratorError):
                    generator.validate_capabilities(
                        program, generator.APPROVED_CAPABILITIES,
                        source_hash="0" * 64, **kwargs)
                with self.assertRaises(TypedEmissionError):
                    render_typed_cpp(program, key, "0" * 64, **kwargs)
                forged = dataclasses.replace(program, functions=program.functions[:-1])
                with self.assertRaises(GeneratorError):
                    generator.validate_capabilities(
                        forged, generator.APPROVED_CAPABILITIES,
                        source_hash=source_hash, **kwargs)


if __name__ == "__main__":
    unittest.main()
