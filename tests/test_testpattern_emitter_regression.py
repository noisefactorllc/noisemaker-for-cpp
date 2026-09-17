from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import unittest

from tools.glslcpp import emit_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import testpattern_profile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/glslcpp/corpus/0ed489ec46842bffba33ee2ec65a218b6dda51f5"
          / "sources/synth/testPattern/testPattern.glsl")
KEY = testpattern_profile.KEY


def _program(raw: str | None = None, key: str = KEY):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(parse_program(raw, key, {}), key)


def _render(program, profile: str | None = testpattern_profile.PROFILE):
    source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
    proof = None
    if profile == testpattern_profile.PROFILE:
        try:
            proof = testpattern_profile.authenticate_testpattern_frontend(
                program, source_hash, profile)
        except ValueError:
            # Preserve the emitter's fail-closed diagnostic for forged or
            # stale trees instead of making the test helper the gate.
            proof = None
    return emit_typed_cpp.render_typed_cpp(
        program, KEY, source_hash, testpattern_profile=profile,
        testpattern_frontend_proof=proof)


class TestPatternEmitterRegressionTests(unittest.TestCase):
    def test_authenticated_arrays_preserve_payload_types_and_constness(self):
        rendered = _render(_program())
        self.assertIn(
            "const std::array<std::int32_t, 10> GLYPH = "
            "std::array<std::int32_t, 10>{{std::int32_t(31599), "
            "std::int32_t(9362), std::int32_t(29671), std::int32_t(29391), "
            "std::int32_t(23497), std::int32_t(31183), std::int32_t(31215), "
            "std::int32_t(29257), std::int32_t(31727), "
            "std::int32_t(31695)}};",
            rendered,
        )
        # `digits` is `double`, not `std::int32_t`: the authority's own DSL
        # compiler never resolves `temp /= 10` (inside this same function's
        # digit-extraction loop) to `int`, so canonical-kernels.js emits
        # plain, untyped `temp /= 10;` -- real JS division, not
        # `$rt.intDivide`. `digits[]` and the digit read back out of it can
        # therefore carry a fractional JS Number forward exactly like the
        # authority does; see the field comment on
        # `emitted_testpattern_digit_extraction_declarations` in
        # emit_typed_cpp.py.
        self.assertIn(
            "[[maybe_unused]] std::array<double, 3> digits{};",
            rendered,
        )
        self.assertIn(
            "[[maybe_unused]] std::array<glsl::Vec3, 8> colors = "
            "std::array<glsl::Vec3, 8>{{",
            rendered,
        )
        self.assertNotIn("std::array<int,", rendered)
        self.assertNotIn("std::array<float,", rendered)
        self.assertNotIn("std::vector", rendered)

    def test_digit_extraction_stays_an_untyped_js_number(self):
        """Root-cause regression for the grid-boundary divergence.

        canonical-kernels.js's `renderNumber` extracts digits with
        `digits[i] = temp % 10; temp /= 10;` where `temp` is a GLSL `int`
        the authority's own compiler (src/csl/codegen.js:67,124,131) never
        resolves to `int` at this one compound-assign site -- so it emits
        plain, untyped `temp /= 10;`: real (non-truncating) JS division,
        not `$rt.intDivide`. A previously-emitted `std::int32_t temp`
        truncated that remainder away every iteration, so a two-or-more
        digit cell number that should fail to render (e.g. 11, whose
        `GLYPH[1.1]` is a JS `undefined`, and every bitwise op on
        `undefined` coerces to zero) instead rendered its second digit for
        real -- measured divergent at exactly the two grid-boundary pixels
        the frozen `kMeasuredParityExclusions` reason names.
        """
        rendered = _render(_program())
        self.assertIn("[[maybe_unused]] double temp = number;", rendered)
        self.assertIn(
            "digits[static_cast<std::size_t>(i)] = "
            "std::fmod(static_cast<double>(temp), "
            "static_cast<double>(std::int32_t(10)));",
            rendered,
        )
        # Plain double division: `temp / std::int32_t(10)` with `temp`
        # `double` promotes the int literal, no truncating helper involved.
        self.assertIn("temp = (temp / std::int32_t(10));", rendered)
        self.assertNotIn("glsl::integer_mod(temp,", rendered)
        # The digit read back out of `digits[]` is `double`, and the one
        # call site that reads it (`sampleGlyph`) is guarded so a
        # fractional digit can only ever take the `false` branch --
        # `sampleGlyph` itself stays untouched (still `std::int32_t digit`).
        self.assertIn(
            "[[maybe_unused]] double digit = digits[static_cast<std::size_t>"
            "(((numDigits - std::int32_t(1)) - d))];",
            rendered,
        )
        self.assertIn(
            "return ((std::trunc(digit) == (digit)) ? "
            "sampleGlyph(state, context, static_cast<std::int32_t>(digit), "
            "gx, gy) : false);",
            rendered,
        )
        self.assertIn(
            "bool sampleGlyph([[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] std::int32_t digit, "
            "[[maybe_unused]] std::int32_t x, [[maybe_unused]] std::int32_t y) "
            "noexcept {",
            rendered,
        )

    def test_all_four_authenticated_indexes_are_range_casts(self):
        rendered = _render(_program())
        index_lines = tuple(
            line.strip() for line in rendered.splitlines()
            if "static_cast<std::size_t>(" in line
        )
        self.assertEqual(len(index_lines), 4)
        self.assertEqual(sum("GLYPH[static_cast<std::size_t>(digit)]" in line
                             for line in index_lines), 1)
        self.assertEqual(sum("colors[static_cast<std::size_t>(bar)]" in line
                             for line in index_lines), 1)
        self.assertEqual(sum("digits[static_cast<std::size_t>(i)]" in line
                             for line in index_lines), 1)
        self.assertEqual(sum(
            "digits[static_cast<std::size_t>(((numDigits - std::int32_t(1)) - d))]"
            in line for line in index_lines), 1)

    def test_bitwise_sites_use_signed_javascript_helpers_only(self):
        rendered = _render(_program())
        self.assertEqual(rendered.count("glsl::detail::js_shift_right("), 1)
        self.assertEqual(rendered.count("glsl::detail::js_bitwise_and("), 1)
        self.assertNotIn("GLYPH[static_cast<std::size_t>(digit)] >>", rendered)
        self.assertNotIn("& std::int32_t(1)", rendered)
        self.assertIn(
            "js_bitwise_and(glsl::detail::js_shift_right(GLYPH[",
            rendered,
        )

    def test_vector_round_is_narrowed_per_lane_before_vec2_materialization(self):
        rendered = _render(_program())
        self.assertIn(
            "glsl::Vec2(noisemaker::f32(glsl::round(glsl::swizzle<0>(scaled))), "
            "noisemaker::f32(glsl::round(glsl::swizzle<1>(scaled))))",
            rendered,
        )
        self.assertNotIn("glsl::round(scaled)", rendered)
        self.assertEqual(rendered.count("noisemaker::f32(glsl::round("), 2)

    def test_dynamic_loop_carrier_is_consumed_without_fixed_bound_widening(self):
        rendered = _render(_program())
        self.assertIn(
            "for ([[maybe_unused]] std::int32_t d = std::int32_t(0); "
            "(d < numDigits); ++d)",
            rendered,
        )
        self.assertIn(
            "for ([[maybe_unused]] std::int32_t i = std::int32_t(0); "
            "(i < std::int32_t(3)); ++i)",
            rendered,
        )
        self.assertEqual(rendered.count("(d < numDigits)"), 1)
        self.assertNotIn("(d < std::int32_t(3))", rendered)

    def test_missing_wrong_foreign_and_stale_profile_carriers_fail_closed(self):
        program = _program()
        for profile in (None, "wrong-testpattern-profile"):
            with self.subTest(profile=profile):
                with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                    _render(program, profile)

        foreign = _program(key="synth/foreign:foreign")
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                foreign, "synth/foreign:foreign",
                hashlib.sha256(foreign.raw_source.encode()).hexdigest(),
                testpattern_profile=testpattern_profile.PROFILE)

        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, "0" * 64,
                testpattern_profile=testpattern_profile.PROFILE)

    def test_source_and_typed_tree_mutations_are_rejected_by_identity_fingerprint(self):
        program = _program()
        changed_source = dataclasses.replace(
            program, source=program.source + "\n// forged\n")
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            _render(changed_source)

        changed_tree = dataclasses.replace(program, functions=program.functions[:-1])
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            _render(changed_tree)

    def test_profile_is_not_a_generic_array_or_operator_admission(self):
        module = testpattern_profile
        self.assertEqual(module.KEYS, ())
        self.assertEqual(module.REQUIRED_COMPANION_PROFILES[KEY], ())
        self.assertEqual(module.GRID_SIZE_RANGE, (0, 16))
        self.assertEqual(module.PATTERN_RANGE, (0, 6))

        # The only typed array forms admitted by this source-bound carrier are
        # the three proof records.  This assertion intentionally names the
        # exact native forms instead of blessing a generic array vocabulary.
        proof = module.authenticate_testpattern_frontend(
            _program(), module.RAW_SHA256, module.PROFILE)
        self.assertEqual(
            (proof.global_array.type_name,
             proof.local_arrays),
            ("int[10]", ("digits", "colors")),
        )
        self.assertEqual(
            tuple(item.array_name for item in proof.dynamic_indexes),
            ("GLYPH", "digits", "colors"),
        )
        self.assertEqual(proof.digit_store_index.array_name, "digits")


if __name__ == "__main__":
    unittest.main()
