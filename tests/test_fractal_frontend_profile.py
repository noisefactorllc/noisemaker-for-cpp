from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import unittest

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.loop_proof import summarize_counted_loop_proofs
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import fractal_frontend_profile as profile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/fractal/fractal.glsl"
METADATA = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/metadata.json"


def analyzed(raw: str | None = None, key: str = profile.KEY):
    text = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(parse_program(text, key, {}), key)


def metadata_effect():
    return json.loads(METADATA.read_text(encoding="utf-8"))["effects"][
        "classicNoisedeck/fractal"]


class FractalPreparedFrontendTests(unittest.TestCase):
    def test_prepared_registry_and_runtime_contract(self):
        self.assertEqual((), profile.KEYS)
        self.assertEqual((profile.KEY,), profile.PREPARED_KEYS)
        self.assertEqual({profile.KEY: profile.PROFILE}, profile.PROFILES)
        self.assertEqual({profile.KEY: profile.PROFILE}, profile.PREPARED_PROFILES)
        self.assertEqual(
            frozenset({"defines", "program_key", "fractal_frontend_profile"}),
            profile.ALLOWED_ROW_FIELDS[profile.KEY])
        self.assertEqual((), profile.REQUIRED_COMPANION_PROFILES[profile.KEY])
        self.assertEqual("fragColor", profile.OUTPUT_ABI[0])
        self.assertEqual("Vec4", profile.OUTPUT_ABI[2])
        self.assertEqual(29, len(profile.SOURCE_UNIFORMS))
        self.assertEqual(("fwdA", "fwdB", "invB", "invA"), profile.MATRIX_CONSTANTS)

    def test_authentication_returns_exact_shape_and_explicit_loop_blocker(self):
        program = analyzed()
        proof = profile.authenticate_fractal_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(),
            profile.PROFILE)
        self.assertEqual(profile.FUNCTION_NAMES, proof.functions)
        self.assertEqual(profile.LOOP_SPANS, proof.loops)
        self.assertEqual(profile.UNPROVED_LOOP_SPANS, proof.unproved_loops)
        self.assertEqual(profile.FRONTEND_BLOCKER, proof.blocker)
        self.assertEqual("iterations", proof.iterations_contract.uniform_name)
        self.assertEqual(1, proof.iterations_contract.minimum)
        self.assertEqual(50, proof.iterations_contract.default)
        self.assertEqual(50, proof.iterations_contract.maximum)
        applied = profile.apply_fractal_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        self.assertIsNot(program, applied)
        self.assertEqual(0, applied.counted_loop_proof.unproved_loop_count)

    def test_authenticates_exact_background_alpha_product_and_literal(self):
        proof = profile.authenticate_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        self.assertEqual(profile.ALPHA_BRANCH_SPAN,
                         f"{proof.alpha_branch.span.start_line}:"
                         f"{proof.alpha_branch.span.start_column}-"
                         f"{proof.alpha_branch.span.end_line}:"
                         f"{proof.alpha_branch.span.end_column}")
        self.assertEqual(profile.ALPHA_PRODUCT_SPAN,
                         f"{proof.alpha_product.span.start_line}:"
                         f"{proof.alpha_product.span.start_column}-"
                         f"{proof.alpha_product.span.end_line}:"
                         f"{proof.alpha_product.span.end_column}")
        self.assertEqual(profile.ALPHA_LITERAL_SPAN,
                         f"{proof.alpha_literal.span.start_line}:"
                         f"{proof.alpha_literal.span.start_column}-"
                         f"{proof.alpha_literal.span.end_line}:"
                         f"{proof.alpha_literal.span.end_column}")
        self.assertEqual("*", proof.alpha_product.operator)
        self.assertEqual(profile.ALPHA_BG_SYMBOL_ID,
                         proof.alpha_product.children[0].symbol_id)
        self.assertEqual(profile.ALPHA_BG_SYMBOL_NAME,
                         proof.alpha_product.children[0].symbol.name)
        self.assertEqual(profile.ALPHA_LITERAL_SPELLING,
                         proof.alpha_literal.literal)
        self.assertEqual(profile.ALPHA_LITERAL_VALUE,
                         proof.alpha_literal.literal_value)
        expressions = profile._expressions(proof.program)
        self.assertEqual(
            1, sum(item is proof.alpha_product for item in expressions))
        self.assertEqual(
            1, sum(item is proof.alpha_literal for item in expressions))

    def test_authenticates_exact_number_hsv_path(self):
        proof = profile.authenticate_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        self.assertEqual("hsv2rgb", proof.hsv_function.name)
        self.assertEqual(60, proof.hsv_function.signature.id)
        self.assertEqual(("hsv", 40, "vec3"),
                         (proof.hsv_parameter.name, proof.hsv_parameter.id,
                          proof.hsv_parameter.type.display()))
        self.assertEqual(
            ("174:17-174:31", "369:21-369:47"),
            tuple(f"{item.span.start_line}:{item.span.start_column}-"
                  f"{item.span.end_line}:{item.span.end_column}"
                  for item in proof.hsv_calls))
        self.assertEqual("368:9-368:31",
                         f"{proof.hue_scale_assignment.span.start_line}:"
                         f"{proof.hue_scale_assignment.span.start_column}-"
                         f"{proof.hue_scale_assignment.span.end_line}:"
                         f"{proof.hue_scale_assignment.span.end_column}")
        self.assertEqual("*=", proof.hue_scale_assignment.operator)
        self.assertIs(proof.hue_scale_product,
                      proof.hue_scale_assignment.children[1])
        self.assertEqual("hueRange",
                         proof.hue_scale_product.children[0].symbol.name)
        self.assertIs(proof.hue_scale_literal,
                      proof.hue_scale_product.children[1])
        self.assertEqual("0.01", proof.hue_scale_literal.literal)
        self.assertEqual("353:5-353:17",
                         f"{proof.distance_fract_assignment.span.start_line}:"
                         f"{proof.distance_fract_assignment.span.start_column}-"
                         f"{proof.distance_fract_assignment.span.end_line}:"
                         f"{proof.distance_fract_assignment.span.end_column}")
        self.assertIs(proof.distance_fract_builtin,
                      proof.distance_fract_assignment.children[1])
        self.assertEqual("fract", proof.distance_fract_builtin.callee)
        self.assertEqual(-18, proof.distance_fract_builtin.signature_id)
        self.assertEqual("352:5-352:49",
                         f"{proof.distance_map_assignment.span.start_line}:"
                         f"{proof.distance_map_assignment.span.start_column}-"
                         f"{proof.distance_map_assignment.span.end_line}:"
                         f"{proof.distance_map_assignment.span.end_column}")
        self.assertEqual("+", proof.distance_map_sum.operator)
        self.assertEqual("repeatPalette",
                         proof.distance_repeat_product.children[1].symbol.name)
        self.assertEqual("rotatePalette",
                         proof.distance_rotate_product.children[0].symbol.name)
        self.assertEqual("0.01", proof.distance_rotate_literal.literal)
        self.assertEqual(("pal", 70, "vec3"),
                         (proof.palette_function.name,
                          proof.palette_function.signature.id,
                          proof.palette_function.return_type.display()))
        self.assertEqual(("t", 49, "float"),
                         (proof.palette_parameter.name,
                          proof.palette_parameter.id,
                          proof.palette_parameter.type.display()))
        self.assertEqual("365:21-365:27",
                         f"{proof.palette_call.span.start_line}:"
                         f"{proof.palette_call.span.start_column}-"
                         f"{proof.palette_call.span.end_line}:"
                         f"{proof.palette_call.span.end_column}")
        self.assertEqual(("newton", 67, "float"),
                         (proof.newton_function.name,
                          proof.newton_function.signature.id,
                          proof.newton_function.return_type.display()))
        self.assertEqual(("st", 54, "vec2"),
                         (proof.newton_parameter.name,
                          proof.newton_parameter.id,
                          proof.newton_parameter.type.display()))
        self.assertEqual(profile.NEWTON_BODY_SPANS,
                         tuple(f"{item.span.start_line}:"
                               f"{item.span.start_column}-"
                               f"{item.span.end_line}:"
                               f"{item.span.end_column}"
                               for item in proof.newton_function.body))
        self.assertEqual("336:13-336:23",
                         f"{proof.newton_call.span.start_line}:"
                         f"{proof.newton_call.span.start_column}-"
                         f"{proof.newton_call.span.end_line}:"
                         f"{proof.newton_call.span.end_column}")

    def test_authenticates_exact_julia_mandelbrot_number_paths(self):
        proof = profile.authenticate_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        self.assertEqual(("julia", 61, "float"), (
            proof.julia_function.name, proof.julia_function.signature.id,
            proof.julia_function.return_type.display()))
        self.assertEqual(("st", 55, "vec2", "in"), (
            proof.julia_parameter.name, proof.julia_parameter.id,
            proof.julia_parameter.type.display(), proof.julia_parameter.direction))
        self.assertEqual(profile.JULIA_BODY_SPANS, tuple(
            f"{item.span.start_line}:{item.span.start_column}-"
            f"{item.span.end_line}:{item.span.end_column}"
            for item in proof.julia_function.body))
        self.assertEqual(("334:13-334:22", 61, 102, "st"), (
            f"{proof.julia_call.span.start_line}:{proof.julia_call.span.start_column}-"
            f"{proof.julia_call.span.end_line}:{proof.julia_call.span.end_column}",
            proof.julia_call.signature_id,
            proof.julia_call.children[0].symbol_id,
            proof.julia_call.children[0].symbol.name))
        self.assertEqual(("mandelbrot", 65, "float"), (
            proof.mandelbrot_function.name,
            proof.mandelbrot_function.signature.id,
            proof.mandelbrot_function.return_type.display()))
        self.assertEqual(("st", 56, "vec2", "in"), (
            proof.mandelbrot_parameter.name, proof.mandelbrot_parameter.id,
            proof.mandelbrot_parameter.type.display(),
            proof.mandelbrot_parameter.direction))
        self.assertEqual(profile.MANDELBROT_BODY_SPANS, tuple(
            f"{item.span.start_line}:{item.span.start_column}-"
            f"{item.span.end_line}:{item.span.end_column}"
            for item in proof.mandelbrot_function.body))
        self.assertEqual(("338:13-338:27", 65, 102, "st"), (
            f"{proof.mandelbrot_call.span.start_line}:"
            f"{proof.mandelbrot_call.span.start_column}-"
            f"{proof.mandelbrot_call.span.end_line}:"
            f"{proof.mandelbrot_call.span.end_column}",
            proof.mandelbrot_call.signature_id,
            proof.mandelbrot_call.children[0].symbol_id,
            proof.mandelbrot_call.children[0].symbol.name))
        self.assertEqual(profile.MATRIX_CONSTRUCTOR_SPAN,
                         f"{proof.matrix_constructor.span.start_line}:"
                         f"{proof.matrix_constructor.span.start_column}-"
                         f"{proof.matrix_constructor.span.end_line}:"
                         f"{proof.matrix_constructor.span.end_column}")

    def test_carries_exact_number_anchor_nodes_and_actual_mode_return_span(self):
        proof = profile.authenticate_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        self.assertEqual(profile.JULIA_NUMBER_ANCHOR_SPANS,
                         tuple(profile._span(item)
                               for item in proof.julia_number_anchors))
        self.assertEqual(profile.MANDELBROT_NUMBER_ANCHOR_SPANS,
                         tuple(profile._span(item)
                               for item in proof.mandelbrot_number_anchors))
        self.assertEqual("277:9-277:48", profile.JULIA_MODE_ZERO_RETURN_SPAN)
        self.assertEqual("277:9-277:48",
                         profile._span(proof.julia_number_anchors[-2]))

    def test_emitter_consumes_exact_number_anchor_census(self):
        from unittest import mock

        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        proof = profile.authenticate_fractal_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        for field in ("julia_number_anchors", "mandelbrot_number_anchors"):
            anchors = getattr(proof, field)
            forged = dataclasses.replace(proof, **{field: anchors[:-1]})
            with self.subTest(field=field):
                with mock.patch.object(
                        emit_typed_cpp, "authenticate_fractal_frontend",
                        return_value=forged):
                    with self.assertRaisesRegex(
                            emit_typed_cpp.TypedEmissionError,
                            "anchor identity mismatch"):
                        emit_typed_cpp.render_typed_cpp(
                            program, profile.KEY, profile.RAW_SHA256,
                            fractal_frontend_profile=profile.PROFILE)

    def test_emitter_rejects_each_mutated_number_anchor(self):
        from unittest import mock

        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        proof = profile.authenticate_fractal_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        for field in ("julia_number_anchors", "mandelbrot_number_anchors"):
            anchors = getattr(proof, field)
            for index in range(len(anchors)):
                mutated = list(anchors)
                mutated[index] = anchors[(index + 1) % len(anchors)]
                forged = dataclasses.replace(
                    proof, **{field: tuple(mutated)})
                with self.subTest(field=field, index=index):
                    with mock.patch.object(
                            emit_typed_cpp, "authenticate_fractal_frontend",
                            return_value=forged):
                        with self.assertRaisesRegex(
                                emit_typed_cpp.TypedEmissionError,
                                "anchor identity mismatch"):
                            emit_typed_cpp.render_typed_cpp(
                                program, profile.KEY, profile.RAW_SHA256,
                                fractal_frontend_profile=profile.PROFILE)

    def test_emits_scalar_julia_mandelbrot_number_paths(self):
        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, profile.KEY, profile.RAW_SHA256,
            fractal_frontend_profile=profile.PROFILE)
        for name in ("julia", "mandelbrot"):
            start = rendered.rfind(
                f"double {name}(", 0, rendered.index("void pixel"))
            end = rendered.index("\n}\n", start)
            body = rendered[start:end]
            self.assertIn(
                f"double {name}([[maybe_unused]] const State& state, "
                "[[maybe_unused]] const glsl::PixelContext& context, "
                "[[maybe_unused]] double input_x, "
                "[[maybe_unused]] double input_y) noexcept {", body)
            self.assertNotIn("glsl::Vec2 z", body)
            self.assertNotIn("glsl::dot", body)
            self.assertNotIn("glsl::length(z)", body)
            self.assertIn("const auto hypot_number", body)
            self.assertIn("noisemaker::fdlibm::sin", body)
        self.assertIn(
            "julia(state, context, (static_cast<double>(context.frag_coord[0]) + "
            "static_cast<double>(state.tileOffset[0])) / "
            "static_cast<double>(state.fullResolution[1]),",
            rendered)
        self.assertIn(
            "mandelbrot(state, context, "
            "(static_cast<double>(context.frag_coord[0]) + "
            "static_cast<double>(state.tileOffset[0])) / "
            "static_cast<double>(state.fullResolution[1]),",
            rendered)
        self.assertIn("iteration = index;", rendered)
        self.assertIn("const double next_x =", rendered)
        self.assertIn("const double next_y =", rendered)
        self.assertNotIn("julia(state, context, globalCoord", rendered)
        self.assertNotIn("mandelbrot(state, context, globalCoord", rendered)

    def test_emits_pinned_number_setup_order(self):
        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, profile.KEY, profile.RAW_SHA256,
            fractal_frontend_profile=profile.PROFILE)

        def helper(name):
            start = rendered.rfind(
                f"double {name}(", 0, rendered.index("void pixel"))
            end = rendered.index("\n}\n", start)
            return rendered[start:end]

        julia = helper("julia")
        self.assertLess(julia.index("const double zoom"),
                        julia.index("const double speedy"))
        self.assertLess(julia.index("const double speedy ="),
                        julia.index("const double speed ="))
        self.assertLess(julia.index("const double speed ="),
                        julia.index("const double cx"))
        self.assertLess(julia.index("const double cx"),
                        julia.index("const double cy"))
        self.assertLess(julia.index("const double cy"),
                        julia.index("const double angle"))

        mandelbrot = helper("mandelbrot")
        self.assertLess(mandelbrot.index("const double zoom"),
                        mandelbrot.index("const double speedy"))
        self.assertLess(mandelbrot.index("const double speedy ="),
                        mandelbrot.index("const double speed ="))
        self.assertLess(mandelbrot.index("const double speed ="),
                        mandelbrot.index("const double angle"))

    def test_fractal_helper_identity_mutations_are_rejected(self):
        raw = SOURCE.read_text(encoding="utf-8")
        for original, replacement in (
                ("map(zoomAmt, 0.0, 100.0, 2.0, 0.5)",
                 "map(zoomAmt, 0.0, 100.0, 2.0, 0.6)"),
                ("zoom * st - vec2(centerX + 50.0, centerY) * 0.01",
                 "zoom * st - vec2(centerX + 51.0, centerY) * 0.01")):
            mutated = raw.replace(original, replacement, 1)
            self.assertNotEqual(raw, mutated)
            with self.assertRaisesRegex(ValueError, profile.PROFILE):
                profile.authenticate_fractal_frontend(
                    analyzed(mutated), profile.RAW_SHA256, profile.PROFILE)

    def test_background_alpha_source_mutation_is_rejected(self):
        raw = SOURCE.read_text(encoding="utf-8")
        mutated = raw.replace(
            "vec4(bgColor, bgAlpha * 0.01)",
            "vec4(bgColor, bgAlpha * 0.02)", 1)
        self.assertNotEqual(raw, mutated)
        with self.assertRaisesRegex(ValueError, profile.PROFILE):
            profile.authenticate_fractal_frontend(
                analyzed(mutated), profile.RAW_SHA256, profile.PROFILE)

    def test_wrong_identity_or_source_fails_closed(self):
        program = analyzed()
        for candidate, source_hash, selected in (
                (program, "0" * 64, profile.PROFILE),
                (program, profile.RAW_SHA256, "wrong-profile"),
                (dataclasses.replace(program, key="foreign:key"),
                 profile.RAW_SHA256, profile.PROFILE)):
            with self.assertRaisesRegex(ValueError, profile.PROFILE):
                profile.authenticate_fractal_frontend(candidate, source_hash, selected)

    def test_source_mutation_is_rejected_even_when_reparsed(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "#define TAU 6.28318530718", "#define TAU 6.28318530719", 1)
        changed = analyzed(raw)
        with self.assertRaisesRegex(ValueError, "source, function, whole-program, or interface"):
            profile.authenticate_fractal_frontend(changed, profile.RAW_SHA256, profile.PROFILE)

    def test_forged_iterations_metadata_is_rejected(self):
        effect = metadata_effect()
        profile.authenticate_fractal_metadata(effect)
        for field, value in (("type", "float"), ("min", 0),
                             ("default", 49), ("max", 51),
                             ("uniform", "iterationCount")):
            forged = json.loads(json.dumps(effect))
            forged["params"]["iterations"][field] = value
            with self.assertRaisesRegex(ValueError, "metadata contract mismatch"):
                profile.authenticate_fractal_metadata(forged)

    def test_forged_mode_metadata_is_rejected(self):
        effect = metadata_effect()
        profile.authenticate_fractal_metadata(effect)
        for field, value in (
                ("choices", {"iter": 0, "z": 2}),
                ("default", 1), ("type", "float"), ("uniform", "fractalMode"),
                ("ui", {"control": "slider", "label": "mode"})):
            forged = json.loads(json.dumps(effect))
            forged["params"]["mode"][field] = value
            with self.assertRaisesRegex(ValueError, "metadata contract mismatch"):
                profile.authenticate_fractal_metadata(forged)

    def test_first_frontend_blocker_is_exact_julia_iteration_loop(self):
        self.assertEqual(("julia", "261:5-269:6"), profile.UNPROVED_LOOP_SPANS[0])
        self.assertIn("julia 261:5-269:6", profile.FRONTEND_BLOCKER)

    def test_apply_attaches_exact_three_fractal_iteration_proofs(self):
        proofed = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        self.assertIsNot(proofed, analyzed())
        loops = []
        for function in proofed.functions:
            def walk(statement):
                if statement.kind == "for":
                    loops.append((function.name, statement.span, statement.loop_proof))
                for child in statement.children:
                    walk(child)
            for statement in function.body:
                walk(statement)
        self.assertEqual(
            [("julia", 100), ("linearToSrgb", 3),
             ("mandelbrot", 50), ("newton", 50)],
            [(name, proof.trip_count) for name, _span, proof in loops])
        self.assertEqual(4, proofed.counted_loop_proof.loop_count)
        self.assertEqual(0, proofed.counted_loop_proof.unproved_loop_count)
        self.assertEqual(
            proofed.counted_loop_proof,
            summarize_counted_loop_proofs(proofed.functions))

    def test_generator_and_emitter_accept_only_authenticated_fractal_carrier(self):
        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=profile.RAW_SHA256,
            fractal_frontend_profile=profile.PROFILE,
            fractal_metadata_effect=metadata_effect())
        rendered = emit_typed_cpp.render_typed_cpp(
            program, profile.KEY, profile.RAW_SHA256,
            fractal_frontend_profile=profile.PROFILE)
        self.assertIn("namespace typed_kernel", rendered)
        self.assertIn(
            'const auto iterations = bindings.get<std::int32_t>("iterations");',
            rendered)
        self.assertIn("if (iterations < 1 || iterations > 50)", rendered)
        self.assertIn(
            'classicNoisedeck/fractal:fractal iterations must be in [1,50]',
            rendered)

    def test_emitter_uses_assignment_form_and_source_bound_terminal_fallbacks(self):
        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, profile.KEY, profile.RAW_SHA256,
            fractal_frontend_profile=profile.PROFILE)
        self.assertNotIn("double i = i =", rendered)
        self.assertIn(
            "for (; iteration < state.iterations; ++iteration)",
            rendered)
        self.assertIn("mode must be one of the authenticated choices [0,1]", rendered)
        for function in ("julia", "mandelbrot", "newton"):
            start = rendered.rfind(f"double {function}(", 0,
                                   rendered.index("void pixel"))
            end = rendered.index("\n}\n", start)
            body = rendered[start:end]
            self.assertIn(
                "// Fractal mode contract [0,1]; unreachable terminal fallback.",
                body)
            self.assertTrue(body.endswith("  return 0.0;"))

    def test_emitter_preserves_number_for_only_authenticated_alpha_literal(self):
        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, profile.KEY, profile.RAW_SHA256,
            fractal_frontend_profile=profile.PROFILE)
        expected = ("static_cast<double>(state.bgAlpha) * "
                    "static_cast<double>(0.01)")
        self.assertEqual(1, rendered.count(expected))
        self.assertNotIn(
            "static_cast<double>(state.bgAlpha) * "
            "static_cast<double>(static_cast<float>(0.01))", rendered)
        checkpoint = struct.unpack("<I", struct.pack("<f", 73.0 * 0.01))[0]
        self.assertEqual(0x3F3AE148, checkpoint)

    def test_emitter_preserves_adapter_number_hsv_path(self):
        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, profile.KEY, profile.RAW_SHA256,
            fractal_frontend_profile=profile.PROFILE)
        self.assertIn(
            "glsl::FloatExpr<3> hsv) noexcept {", rendered)
        self.assertIn(
            "double h = (hsv[0] - std::floor(hsv[0]));", rendered)
        self.assertIn(
            "double h6 = (h * 6.0);", rendered)
        self.assertIn(
            "double hue_mod = (h6 - (2.0 * std::floor(h6 / 2.0)));",
            rendered)
        self.assertIn(
            "d = ((static_cast<double>(d) * "
            "static_cast<double>(state.hueRange)) * "
            "static_cast<double>(0.01));", rendered)
        self.assertIn(
            "d = (static_cast<double>(d) - "
            "std::floor(static_cast<double>(d)));", rendered)
        self.assertIn(
            "d = ((static_cast<double>(d) * "
            "static_cast<double>(state.repeatPalette)) + "
            "(static_cast<double>(state.rotatePalette) * "
            "static_cast<double>(0.01)));", rendered)
        self.assertIn(
            "if (state.paletteMode == std::int32_t(1)) {", rendered)
        self.assertIn(
            "if (state.paletteMode == std::int32_t(2)) {", rendered)
        self.assertIn(
            "const double a = ("
            "static_cast<double>(adapter_color[1]) * -0.509 + 0.276);",
            rendered)
        self.assertIn(
            "const double b = ("
            "static_cast<double>(adapter_color[2]) * -0.509 + 0.198);",
            rendered)
        self.assertNotIn("const double a = noisemaker::f32(", rendered)
        self.assertNotIn("const double b = noisemaker::f32(", rendered)
        self.assertIn(
            "double newton([[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] double input_x, "
            "[[maybe_unused]] double input_y) noexcept {",
            rendered)
        self.assertIn(
            "newton(state, context, "
            "(static_cast<double>(context.frag_coord[0]) + "
            "static_cast<double>(state.tileOffset[0])) / "
            "static_cast<double>(state.fullResolution[1]), "
            "(static_cast<double>(context.frag_coord[1]) + "
            "static_cast<double>(state.tileOffset[1])) / "
            "static_cast<double>(state.fullResolution[1]))",
            rendered)
        self.assertIn("const auto hypot_number =", rendered)
        self.assertIn(
            "return std::sqrt(scaled_x * scaled_x + "
            "scaled_y * scaled_y) * maximum;",
            rendered)
        self.assertNotIn("std::hypot(", rendered)
        self.assertEqual(
            3, rendered.count("noisemaker::fdlibm::cos(6.28318 *"))
        self.assertIn(
            "return adapter_color;", rendered)
        self.assertIn(
            "1.055 * std::pow(value, 1.0 / 2.4) - 0.055;", rendered)
        self.assertNotIn(
            "d = (static_cast<double>(d) * static_cast<double>((static_cast<double>(state.hueRange) * "
            "static_cast<double>(static_cast<float>(0.01)))));", rendered)
        expected = (16.0 / 19.0) * 83.0 * 0.01
        red = 6.0 * expected - 4.0
        checkpoint = struct.unpack("<I", struct.pack("<f", red))[0]
        self.assertEqual(0x3E465527, checkpoint)

    def test_fractal_render_is_strict_cpp_syntax_clean(self):
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, profile.KEY, profile.RAW_SHA256,
            fractal_frontend_profile=profile.PROFILE)
        source = "\n".join((
            '#include "noisemaker/kernel.hpp"',
            '#include "noisemaker/numeric.hpp"',
            '#include "noisemaker/pass_runner.hpp"',
            '#include "noisemaker/sampler.hpp"',
            "#include <array>", "#include <cmath>", "#include <cstdint>",
            "#include <memory>", "#include <stdexcept>",
            "namespace noisemaker::generated {", rendered,
            "}", ""))
        result = subprocess.run(
            [compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror",
             "-I", str(ROOT / "include"), "-x", "c++", "-fsyntax-only", "-"],
            input=source, text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_generator_rejects_forged_iterations_metadata(self):
        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        forged = metadata_effect()
        forged["params"]["iterations"]["max"] = 51
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "metadata contract mismatch"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=profile.RAW_SHA256,
                fractal_frontend_profile=profile.PROFILE,
                fractal_metadata_effect=forged)

    def test_missing_or_wrong_profile_carrier_still_fails_closed(self):
        program = profile.apply_fractal_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "exact Fractal frontend profile carrier required"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=profile.RAW_SHA256,
                fractal_metadata_effect=metadata_effect())
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "Fractal frontend profile metadata mismatch"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=profile.RAW_SHA256,
                fractal_frontend_profile="wrong-profile",
                fractal_metadata_effect=metadata_effect())
        with self.assertRaisesRegex(
                emit_typed_cpp.TypedEmissionError,
                "exact Fractal frontend profile carrier required"):
            emit_typed_cpp.render_typed_cpp(
                program, profile.KEY, profile.RAW_SHA256)
        with self.assertRaisesRegex(
                emit_typed_cpp.TypedEmissionError,
                "Fractal frontend profile metadata mismatch"):
            emit_typed_cpp.render_typed_cpp(
                program, profile.KEY, profile.RAW_SHA256,
                fractal_frontend_profile="wrong-profile")


if __name__ == "__main__":
    unittest.main()
