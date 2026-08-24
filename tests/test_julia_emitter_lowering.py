"""Focused TDD coverage for the standalone Julia typed emitter lane."""

from __future__ import annotations

import hashlib
import pathlib
import unittest
from dataclasses import replace
from unittest import mock


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (REPOSITORY / "tools/glslcpp/corpus"
          / "a024dc3a960cc44af454abc7aebce50456c194e6")
KEY = "synth/julia:julia"
RAW_SHA256 = "825e175c22fea086ad2860e16bcf0a79d797574a9dfad937a23baaadaffdeef0"


class JuliaEmitterLoweringTests(unittest.TestCase):
    def _canonical(self):
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        raw = (CORPUS / "sources/synth/julia/julia.glsl").read_text()
        parsed = parse_program(raw, KEY, {})
        return analyze_program(parsed, KEY), hashlib.sha256(
            raw.encode("utf-8")).hexdigest()

    def test_authenticated_julia_emission_has_adapter_lowering(self):
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp

        program, source_hash = self._canonical()
        self.assertEqual(RAW_SHA256, source_hash)
        emitted = render_typed_cpp(
            program, KEY, source_hash,
            namespace="typed_julia_test",
            factory="bind_synth_julia_julia",
            julia_frontend_profile="julia-frontend-admission-v1",
            struct_declaration_profile="struct-declaration-julia-v1",
            out_inout_admission_profile="out-inout-admission-julia-v1",
        )
        for expected in (
                "JuliaResultNative",
                "JuliaNumberVec2",
                "julia_f32",
                "julia_number_min",
                "julia_number_max",
                "if (a == b && a == 0.0)",
                "if (std::signbit(a) == std::signbit(b)) return a",
                "min(maxIterations, 1000)",
                "nextDerivativeX",
                "float& hi",
                "float& lo",
                "glsl::Vec2& reDF",
                "glsl::Vec2& imDF",
                "double fragX, double fragY",
                "const JuliaNumberVec2 c = resolveC(state)",
                "const double globalX = static_cast<double>(context.frag_coord[0])",
                "iterateSmooth(state, fragX + 1.0, fragY",
                "iterateSmooth(state, fragX, fragY + 1.0",
                "std::hypot(nx, ny, nz)",
                "std::hypot(lx, ly, lz)",
                "double slowX = static_cast<double>(reHigh)",
                "double slowY = static_cast<double>(imHigh)",
                "const float stripeHalf = julia_f32(",
                "stripeLast = julia_f32(static_cast<double>(stripeHalf) + 0.5)",
                "noisemaker::fdlibm::sin",
                "noisemaker::fdlibm::cos",
                "bind_synth_julia_julia",
                "typed_julia_test::pixel"):
            self.assertIn(expected, emitted)
        self.assertNotIn("std::sin(", emitted)
        self.assertNotIn("std::cos(", emitted)
        self.assertNotIn("std::fmin(", emitted)
        self.assertNotIn("std::fmax(", emitted)
        self.assertIn(
            'noisemaker::f32(bindings.get_number("time"))', emitted)
        self.assertIn(
            'noisemaker::f32(bindings.get_number("cSpeed"))', emitted)
        self.assertNotIn("runtime_loop_radius", emitted)

    def test_julia_requires_all_three_authenticated_profiles(self):
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp

        program, source_hash = self._canonical()
        with self.assertRaisesRegex(TypedEmissionError,
                                     "Julia profile metadata mismatch"):
            render_typed_cpp(
                program, KEY, source_hash,
                julia_frontend_profile="julia-frontend-admission-v1",
                struct_declaration_profile="struct-declaration-julia-v1",
            )

    def test_julia_emission_keeps_exact_function_and_binding_surface(self):
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp

        program, source_hash = self._canonical()
        emitted = render_typed_cpp(
            program, KEY, source_hash,
            julia_frontend_profile="julia-frontend-admission-v1",
            struct_declaration_profile="struct-declaration-julia-v1",
            out_inout_admission_profile="out-inout-admission-julia-v1",
        )
        for name in (
                "cmul", "df64_add", "df64_from", "df64_mul", "df64_mul_f",
                "df64_split", "df64_sub", "getAnimatedC", "getPOI",
                "iterateSmooth", "juliaIterate", "main",
                "outputDistanceEstimation", "outputNormalMap",
                "outputOrbitTrap", "outputSmoothIteration",
                "outputStripeAverage", "resolveC", "transformCoords"):
            self.assertIn(name, emitted)
        for binding in (
                "bindings.get<glsl::Vec2>(\"resolution\")",
                "bindings.get<std::int32_t>(\"iterations\")",
                "bindings.get<bool>(\"invert\")",
                "bindings.get_number(\"zoomDepth\")"):
            self.assertIn(binding, emitted)
        self.assertNotIn("512", emitted)

    def _render_with_frontend_proof(self, proof):
        from tools.glslcpp import emit_typed_cpp

        program, source_hash = self._canonical()
        with mock.patch.object(emit_typed_cpp,
                               "authenticate_julia_frontend",
                               return_value=proof):
            return emit_typed_cpp.render_typed_cpp(
                program, KEY, source_hash,
                julia_frontend_profile="julia-frontend-admission-v1",
                struct_declaration_profile="struct-declaration-julia-v1",
                out_inout_admission_profile="out-inout-admission-julia-v1",
            )

    def test_julia_rejects_mutated_frontend_proof_ledgers(self):
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError
        from tools.glslcpp.frontend.julia_frontend_profile import (
            PROFILE, authenticate_julia_frontend)

        program, source_hash = self._canonical()
        proof = authenticate_julia_frontend(program, source_hash, PROFILE)
        mutations = {
            "function": replace(proof, functions=proof.functions[:-1]),
            "member": replace(proof, struct_members=proof.struct_members[:-1]),
            "loop": replace(proof, loops=proof.loops[:-1]),
            "binding": replace(proof, uniforms=proof.uniforms[:-1]),
            "duplicate-function": replace(
                proof, functions=proof.functions[:-1] + (proof.functions[-2],)),
            "duplicate-member": replace(
                proof, struct_members=proof.struct_members[:-1]
                + (proof.struct_members[-2],)),
            "duplicate-loop": replace(
                proof, loops=proof.loops[:-1] + (proof.loops[-2],)),
            "duplicate-binding": replace(
                proof, uniforms=proof.uniforms[:-1] + (proof.uniforms[-2],)),
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label), self.assertRaisesRegex(
                    TypedEmissionError, "cardinality|identity|proof"):
                self._render_with_frontend_proof(mutated)

    def test_julia_rejects_mutated_out_call_cardinality_and_order(self):
        from tools.glslcpp import emit_typed_cpp
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError
        from tools.glslcpp.frontend.out_inout_admission_profile import (
            JULIA_PROFILE, authenticate_out_inout_admission)

        program, source_hash = self._canonical()
        record = authenticate_out_inout_admission(
            program, source_hash, JULIA_PROFILE)
        short = record._replace(call_arguments=record.call_arguments[:-1])
        calls = list(record.call_arguments)
        calls[0] = calls[0]._replace(
            arguments=tuple(reversed(calls[0].arguments)))
        swapped = record._replace(call_arguments=tuple(calls))
        for label, mutated in (("cardinality", short), ("order", swapped)):
            with self.subTest(label=label), mock.patch.object(
                    emit_typed_cpp, "authenticate_out_inout_admission",
                    return_value=mutated), self.assertRaisesRegex(
                    TypedEmissionError,
                    "out (call|argument)|cardinality|identity"):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, source_hash,
                    julia_frontend_profile="julia-frontend-admission-v1",
                    struct_declaration_profile="struct-declaration-julia-v1",
                    out_inout_admission_profile="out-inout-admission-julia-v1",
                )

    def test_julia_rejects_wrong_hash_profile_and_foreign_policy_carrier(self):
        from tools.glslcpp import emit_typed_cpp
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError

        program, source_hash = self._canonical()
        cases = (
            ("hash", dict(julia_frontend_profile="julia-frontend-admission-v1",
                           struct_declaration_profile="struct-declaration-julia-v1",
                           out_inout_admission_profile="out-inout-admission-julia-v1"),
             source_hash[:-1] + ("1" if source_hash[-1] != "1" else "0")),
            ("profile", dict(julia_frontend_profile="wrong-profile",
                              struct_declaration_profile="struct-declaration-julia-v1",
                              out_inout_admission_profile="out-inout-admission-julia-v1"),
             source_hash),
            ("foreign-carrier", dict(julia_frontend_profile="julia-frontend-admission-v1",
                                      struct_declaration_profile="struct-declaration-julia-v1",
                                      out_inout_admission_profile="out-inout-admission-julia-v1",
                                      median_frontend_profile="median-frontend-admission-v1"),
             source_hash),
        )
        for label, kwargs, caller_hash in cases:
            with self.subTest(label=label), self.assertRaisesRegex(
                    TypedEmissionError, "Julia profile|source|profile"):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, caller_hash, **kwargs)

    def test_julia_rejects_profile_on_foreign_key(self):
        from tools.glslcpp import emit_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        raw = (CORPUS / "sources/synth/julia/julia.glsl").read_text()
        foreign_key = "foreign/julia:julia"
        program = analyze_program(parse_program(raw, foreign_key, {}), foreign_key)
        with self.assertRaisesRegex(emit_typed_cpp.TypedEmissionError,
                                     "foreign key"):
            emit_typed_cpp.render_typed_cpp(
                program, foreign_key, RAW_SHA256,
                julia_frontend_profile="julia-frontend-admission-v1",
                struct_declaration_profile="struct-declaration-julia-v1",
                out_inout_admission_profile="out-inout-admission-julia-v1",
            )

    def test_julia_body_consumer_plan_mutations_fail_closed(self):
        from tools.glslcpp import emit_typed_cpp

        self.assertTrue(
            hasattr(emit_typed_cpp, "JULIA_BODY_CONSUMER_PLAN"),
            "Julia lowering must expose its fail-closed body-consumer plan",
        )
        canonical = emit_typed_cpp.JULIA_BODY_CONSUMER_PLAN

        missing = dict(canonical)
        missing["functions"] = canonical["functions"][:-1]

        duplicate = dict(canonical)
        duplicate["members"] = (
            canonical["members"][:-1] + (canonical["members"][-2],))

        reordered = dict(canonical)
        reordered_calls = list(canonical["out_calls"])
        reordered_calls[0], reordered_calls[1] = (
            reordered_calls[1], reordered_calls[0])
        reordered["out_calls"] = tuple(reordered_calls)

        synthetic = dict(canonical)
        synthetic_bindings = list(canonical["bindings"])
        synthetic_bindings[0] = (0, "synthetic binding marker")
        synthetic["bindings"] = tuple(synthetic_bindings)

        program, source_hash = self._canonical()
        for label, plan in (
                ("missing", missing), ("duplicate", duplicate),
                ("reordered", reordered), ("synthetic", synthetic)):
            with self.subTest(label=label), mock.patch.object(
                    emit_typed_cpp, "JULIA_BODY_CONSUMER_PLAN", plan), \
                    self.assertRaisesRegex(
                        emit_typed_cpp.TypedEmissionError,
                        "Julia emission consumption"):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, source_hash,
                    julia_frontend_profile="julia-frontend-admission-v1",
                    struct_declaration_profile="struct-declaration-julia-v1",
                    out_inout_admission_profile="out-inout-admission-julia-v1",
                )

    def test_julia_body_omission_duplicate_and_reorder_fail_consumption(self):
        from tools.glslcpp import emit_typed_cpp

        function_marker = "[[nodiscard]] glsl::Vec2 cmul("
        first_binding = 'bindings.get<glsl::Vec2>("resolution")'
        second_binding = 'bindings.get<glsl::Vec2>("tileOffset")'

        def omit(body):
            return body.replace(function_marker, "", 1)

        def duplicate(body):
            return body.replace(first_binding,
                                first_binding + "\n" + first_binding, 1)

        def reorder(body):
            placeholder = "__JULIA_BINDING_REORDER_PLACEHOLDER__"
            return body.replace(first_binding, placeholder, 1).replace(
                second_binding, first_binding, 1).replace(
                    placeholder, second_binding, 1)

        original = emit_typed_cpp._Emitter._consume_julia_body
        program, source_hash = self._canonical()
        for label, transform in (("omission", omit), ("duplicate", duplicate),
                                 ("reorder", reorder)):
            def consume_mutated(emitter, body, proof, transform=transform):
                return original(emitter, transform(body), proof)

            with self.subTest(label=label), mock.patch.object(
                    emit_typed_cpp._Emitter, "_consume_julia_body",
                    consume_mutated), self.assertRaisesRegex(
                        emit_typed_cpp.TypedEmissionError,
                        "Julia emission consumption"):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, source_hash,
                    julia_frontend_profile="julia-frontend-admission-v1",
                    struct_declaration_profile="struct-declaration-julia-v1",
                    out_inout_admission_profile="out-inout-admission-julia-v1",
                )


if __name__ == "__main__":
    unittest.main()
