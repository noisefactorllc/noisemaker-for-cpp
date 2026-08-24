from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import julia_frontend_profile as profile
from tools.glslcpp.frontend import out_inout_admission_profile as out_profile
from tools.glslcpp.frontend import struct_declaration_profile as struct_profile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources/synth/julia/julia.glsl")


def analyzed(raw: str | None = None, key: str = profile.KEY):
    text = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(
        parse_program(text, key, generate_typed_slice._defaults(ROOT, key)), key)


class JuliaFrontendAdmissionTests(unittest.TestCase):
    def test_landed_registry_and_exact_row_contract(self):
        self.assertEqual((profile.KEY,), profile.KEYS)
        self.assertEqual((), profile.PREPARED_KEYS)
        self.assertEqual({profile.KEY: profile.PROFILE}, profile.PROFILES)
        self.assertEqual({}, profile.PREPARED_PROFILES)
        self.assertEqual(
            frozenset({"defines", "program_key", "julia_frontend_profile",
                       "struct_declaration_profile",
                       "out_inout_admission_profile"}),
            profile.ALLOWED_ROW_FIELDS[profile.KEY])
        self.assertEqual(
            (("struct_declaration_profile", "struct-declaration-julia-v1"),
             ("out_inout_admission_profile", "out-inout-admission-julia-v1")),
            profile.REQUIRED_COMPANION_PROFILES[profile.KEY])
        self.assertEqual(21, len(profile.SOURCE_UNIFORMS))
        self.assertEqual(("fragColor", "vec4", "Vec4", "output"),
                         profile.OUTPUT_ABI)
        self.assertEqual(
            profile.ALLOWED_ROW_FIELDS[profile.KEY],
            struct_profile.allowed_row_fields(profile.KEY))
        self.assertEqual(
            profile.ALLOWED_ROW_FIELDS[profile.KEY],
            out_profile.allowed_row_fields(profile.KEY))

    def test_julia_specific_loop_policy_is_authenticated_without_global_raise(self):
        self.assertEqual(1000, profile.JULIA_MAX_TRIP_COUNT)
        self.assertEqual(profile.COUNTED_LOOP_SUMMARY,
                         profile.JULIA_COUNTED_LOOP_SUMMARY)
        from tools.glslcpp.frontend import loop_proof
        self.assertEqual(512, loop_proof.COUNTED_FOR_V1_MAX_TRIP_COUNT)

    def test_authentication_returns_struct_out_and_loop_shape(self):
        program = analyzed()
        proof = profile.authenticate_julia_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(),
            profile.PROFILE)
        self.assertEqual(profile.STRUCT_NAME, proof.struct_name)
        self.assertEqual(profile.STRUCT_FIELD_NAMES, proof.struct_fields)
        self.assertEqual(profile.OUT_PARAMETERS, proof.out_parameters)
        self.assertEqual(profile.LOOPS, proof.loops)
        self.assertEqual(profile.STRUCT_MEMBER_COUNT, len(proof.struct_members))
        self.assertEqual(profile.EXPECTED_EXPR_KINDS,
                         dict(proof.expression_counts))
        self.assertEqual(profile.EXPECTED_OPERATORS,
                         dict(proof.operator_counts))
        self.assertEqual(len(proof.consumed_objects),
                         len({id(item) for item in proof.consumed_objects}))
        self.assertIs(program, profile.apply_julia_frontend(
            program, profile.RAW_SHA256, profile.PROFILE))

    def test_wrong_identity_profile_or_source_fails_closed(self):
        program = analyzed()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        for candidate, candidate_hash, selected in (
                (program, "0" * 64, profile.PROFILE),
                (program, source_hash, "wrong-profile"),
                (dataclasses.replace(program, key="foreign:key"),
                 source_hash, profile.PROFILE)):
            with self.assertRaisesRegex(ValueError, profile.PROFILE):
                profile.authenticate_julia_frontend(
                    candidate, candidate_hash, selected)

    def test_source_mutation_is_rejected_even_when_reparsed(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "const float TAU = 6.28318530718",
            "const float TAU = 6.28318530719", 1)
        with self.assertRaisesRegex(ValueError, "source, function, whole-program, or interface"):
            profile.authenticate_julia_frontend(
                analyzed(raw), profile.RAW_SHA256, profile.PROFILE)

    def test_struct_companion_authenticates_mixed_precision_result(self):
        program = analyzed()
        record = struct_profile.authenticate_struct_declaration(
            program, profile.RAW_SHA256, struct_profile.JULIA_PROFILE)
        self.assertEqual(profile.STRUCT_FIELD_NAMES, record.fields)
        self.assertEqual(1, record.constructor_count)
        self.assertEqual(24, record.member_count)
        contract = struct_profile.materialization_contract(profile.KEY)
        self.assertEqual("custom-double-backed-mixed-precision", contract.native_kind)
        self.assertEqual(("zMag2", "dzMag2", "stripeSum", "stripeCount",
                          "stripeLast"), contract.f32_narrowed_fields)
        self.assertEqual(
            ("iter", "zMag2", "dzMag2", "stripeSum", "stripeCount",
             "stripeLast"), contract.normal_f32_narrowed_fields)
        self.assertIn("iter = F32(iteration + 1)", contract.normal_iteration_store)
        self.assertEqual(("iter", "trapMin"), contract.number_double_fields)
        self.assertEqual("convergence iteration remains Number double",
                         contract.convergence_iteration)

    def test_iteration_mutation_is_rejected_as_a_mixed_precision_boundary(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "i += 1.0;", "i += 2.0;", 1)
        with self.assertRaisesRegex(ValueError, "normal iteration f32 store"):
            struct_profile.authenticate_struct_declaration(
                analyzed(raw), profile.RAW_SHA256, struct_profile.JULIA_PROFILE)

    def test_out_companion_authenticates_four_exact_reference_outputs(self):
        program = analyzed()
        record = out_profile.authenticate_out_inout_admission(
            program, profile.RAW_SHA256, out_profile.JULIA_PROFILE)
        self.assertEqual(profile.OUT_PARAMETERS, record.parameters)
        self.assertEqual(4, record.store_count)
        self.assertEqual(6, record.call_count)
        contract = out_profile.direction_contract(profile.KEY)
        self.assertEqual("reference", contract.native_abi)
        self.assertEqual(("df64_split.hi", "float&"), contract.parameter_abis[0])
        self.assertEqual(("transformCoords.reDF", "glsl::Vec2&"),
                         contract.parameter_abis[2])
        self.assertEqual(6, len(record.call_arguments))
        self.assertEqual(
            ("df64_mul", "df64_split", 86, "113:5-113:30"),
            record.call_arguments[0].identity)
        self.assertEqual(
            ((0, "swizzle", None, "float", "113:16-113:19", "in"),
             (1, "id", 105, "float", "113:21-113:24", "out"),
             (2, "id", 106, "float", "113:26-113:29", "out")),
            record.call_arguments[0].arguments)
        self.assertEqual(
            (("df64_mul", "df64_split", 86, "113:5-113:30"),
             ("df64_mul", "df64_split", 86, "114:5-114:30"),
             ("df64_mul_f", "df64_split", 86, "123:5-123:30"),
             ("df64_mul_f", "df64_split", 86, "124:5-124:28"),
             ("iterateSmooth", "transformCoords", 99, "290:5-290:47"),
             ("main", "transformCoords", 99, "353:9-353:64")),
            tuple(call.identity for call in record.call_arguments))
        self.assertEqual(
            (((0, "swizzle", None, "float", "113:16-113:19", "in"),
              (1, "id", 105, "float", "113:21-113:24", "out"),
              (2, "id", 106, "float", "113:26-113:29", "out")),
             ((0, "swizzle", None, "float", "114:16-114:19", "in"),
              (1, "id", 107, "float", "114:21-114:24", "out"),
              (2, "id", 108, "float", "114:26-114:29", "out")),
             ((0, "swizzle", None, "float", "123:16-123:19", "in"),
              (1, "id", 111, "float", "123:21-123:24", "out"),
              (2, "id", 112, "float", "123:26-123:29", "out")),
             ((0, "id", 46, "float", "124:16-124:17", "in"),
              (1, "id", 113, "float", "124:19-124:22", "out"),
              (2, "id", 114, "float", "124:24-124:27", "out")),
             ((0, "id", 72, "vec2", "290:21-290:30", "in"),
              (1, "id", 75, "float", "290:32-290:34", "in"),
              (2, "id", 118, "vec2", "290:36-290:40", "out"),
              (3, "id", 119, "vec2", "290:42-290:46", "out")),
             ((0, "id", 152, "vec2", "353:25-353:36", "in"),
              (1, "id", 154, "float", "353:38-353:51", "in"),
              (2, "id", 157, "vec2", "353:53-353:57", "out"),
              (3, "id", 158, "vec2", "353:59-353:63", "out"))),
            tuple(tuple((argument.ordinal, argument.kind, argument.symbol_id,
                         argument.glsl_type, argument.span, argument.direction)
                        for argument in call.arguments)
                  for call in record.call_arguments))
        self.assertEqual((3, 3, 3, 3, 4, 4),
                         tuple(len(call.arguments)
                               for call in record.call_arguments))
        for call in record.call_arguments:
            self.assertEqual(tuple(range(len(call.arguments))),
                             tuple(argument.ordinal for argument in call.arguments))
            self.assertEqual(
                tuple("out" if ordinal >= len(call.arguments) - 2 else "in"
                      for ordinal in range(len(call.arguments))),
                tuple(argument.direction for argument in call.arguments))

    def test_out_companion_rejects_argument_order_mutation(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "df64_split(a.x, ahi, alo)",
            "df64_split(a.x, alo, ahi)", 1)
        with self.assertRaisesRegex(ValueError, "argument order"):
            out_profile.authenticate_out_inout_admission(
                analyzed(raw), profile.RAW_SHA256, out_profile.JULIA_PROFILE)

    def test_companion_mutations_are_rejected_by_their_exact_locks(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "const float TAU = 6.28318530718",
            "const float TAU = 6.28318530719", 1)
        mutated = analyzed(raw)
        with self.assertRaises(ValueError):
            struct_profile.authenticate_struct_declaration(
                mutated, profile.RAW_SHA256, struct_profile.JULIA_PROFILE)
        with self.assertRaises(ValueError):
            out_profile.authenticate_out_inout_admission(
                mutated, profile.RAW_SHA256, out_profile.JULIA_PROFILE)

    def test_typed_slice_has_one_sorted_julia_row_with_empty_defines(self):
        data = __import__("json").loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text())
        rows = data["programs"]
        row = next(item for item in rows if item["program_key"] == profile.KEY)
        self.assertEqual({}, row["defines"])
        self.assertEqual(
            ["synth/gradient:gradient", profile.KEY, "synth/mandala:mandala"],
            [item["program_key"] for item in rows[192:195]])


if __name__ == "__main__":
    unittest.main()
