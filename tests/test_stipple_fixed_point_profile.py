"""Stipple's unsigned fixed-point kernel is admitted by exact node identity."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import unittest
from unittest import mock

from tools.glslcpp import check_corpus, corpus_ratchet, emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend import stipple_fixed_point_profile as profile
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = profile.KEY


def _source_and_effect() -> tuple[str, dict]:
    corpus = check_corpus._corpus_root(ROOT)
    manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    row = next(item for item in manifest["programs"] if item["program_key"] == KEY)
    raw = (corpus / row["source"]).read_bytes()
    metadata = json.loads((corpus / "metadata.json").read_text(encoding="utf-8"))
    return raw.decode("utf-8"), metadata["effects"][KEY.split(":", 1)[0]]


def _runtime_tree():
    """The typed slice tree: MODE as a runtime int, every branch present."""
    raw, _ = _source_and_effect()
    parsed = parse_program(
        generate_typed_slice.transform_generic_dynamic_source(raw, KEY), KEY,
        generate_typed_slice.GENERIC_DYNAMIC_DEFINE_TYPES[KEY])
    parsed["raw_source"] = raw
    typed = analyze_program(parsed, KEY)
    typed = generate_typed_slice.attach_fixed_array_in_parameter_proof(typed)
    return generate_typed_slice.attach_fixed_affine_centers13_proof(typed)


def _default_tree():
    """The corpus probe tree: the authority's default define, MODE=0."""
    raw, _ = _source_and_effect()
    typed = analyze_program(parse_program(raw, KEY, {"MODE": 0}), KEY)
    typed = generate_typed_slice.attach_fixed_array_in_parameter_proof(typed)
    return generate_typed_slice.attach_fixed_affine_centers13_proof(typed)


def _trees():
    return (("runtime", _runtime_tree()), ("default", _default_tree()))


def _replace_node(program, target, replacement):
    def expression(node):
        if node is target:
            return replacement
        return dataclasses.replace(
            node, children=tuple(expression(child) for child in node.children))

    def statement(node):
        return dataclasses.replace(
            node, expressions=tuple(expression(item) for item in node.expressions),
            children=tuple(statement(item) for item in node.children))

    return dataclasses.replace(program, functions=tuple(
        dataclasses.replace(function, body=tuple(statement(item) for item in function.body))
        for function in program.functions))


class StippleFixedPointProfileTests(unittest.TestCase):
    def test_both_trees_authenticate_with_exact_censuses(self) -> None:
        self.assertEqual(profile.RAW_SHA256, hashlib.sha256(
            _source_and_effect()[0].encode("utf-8")).hexdigest())
        for variant, typed in _trees():
            with self.subTest(variant=variant):
                proof = profile.authenticate_stipple_fixed_point(
                    typed, profile.RAW_SHA256, profile.PROFILE)
                self.assertEqual(variant, proof.variant)
                self.assertEqual("uint[5]", proof.table_declaration.type.display())
                self.assertEqual(
                    profile.TABLE_VALUES,
                    tuple(item.literal_value for item in proof.table_constructor.children))
                self.assertIs(proof.table_index.children[0], proof.table_reference)
                self.assertEqual({"runtime": 14, "default": 10}[variant],
                                 len(proof.scalar_uint_rshifts))
                self.assertEqual("ivec2", proof.signed_vector_rshift.type.display())
                self.assertEqual(["uvec2", "uint", "uvec2"],
                                 [item.type.display() for item in proof.left_shifts])
                self.assertEqual(["--", "--", "++", "++"],
                                 [item.operator for item in proof.uint_steps])
                self.assertEqual(2, len(proof.truncated_divisions))
                self.assertEqual(("uvec3", "+"), (proof.f32_blend.type.display(),
                                                  proof.f32_blend.operator))
                self.assertIs(typed, profile.apply_stipple_fixed_point(
                    typed, profile.RAW_SHA256, profile.PROFILE))

    def test_mutations_fail_closed(self) -> None:
        for variant, typed in _trees():
            proof = profile.authenticate_stipple_fixed_point(
                typed, profile.RAW_SHA256, profile.PROFILE)
            mutants = (
                dataclasses.replace(typed, key="filter/other:other"),
                dataclasses.replace(typed, raw_source=typed.raw_source + "\n"),
                dataclasses.replace(typed, source=typed.source + "\n"),
                dataclasses.replace(typed, functions=typed.functions[:-1]),
                dataclasses.replace(typed, functions=typed.functions[::-1]),
                dataclasses.replace(typed, preprocessor_defines=()),
                dataclasses.replace(typed, body_status="mutated"),
                _replace_node(typed, proof.f32_blend,
                              dataclasses.replace(proof.f32_blend, operator="-")),
                _replace_node(typed, proof.left_shifts[1],
                              dataclasses.replace(proof.left_shifts[1], operator=">>")),
            )
            for index, mutant in enumerate(mutants):
                with self.subTest(variant=variant, mutant=index), self.assertRaises(ValueError):
                    profile.authenticate_stipple_fixed_point(
                        mutant, profile.RAW_SHA256, profile.PROFILE)
            for source_hash, carrier in (("0" * 64, profile.PROFILE),
                                         (profile.RAW_SHA256, None),
                                         (profile.RAW_SHA256, "stipple-fixed-point-v0")):
                with self.subTest(variant=variant, carrier=carrier), self.assertRaises(ValueError):
                    profile.authenticate_stipple_fixed_point(typed, source_hash, carrier)

    def test_corpus_probe_selects_the_carrier_and_passes(self) -> None:
        raw, effect = _source_and_effect()
        validator = generate_typed_slice.validate_capabilities
        for candidate, passes in ((raw.encode("utf-8"), True),
                                  (raw.encode("utf-8") + b"\n", False)):
            with mock.patch.object(generate_typed_slice, "validate_capabilities",
                                   wraps=validator) as validate:
                result = corpus_ratchet.probe_program(KEY, candidate, effect)
            self.assertEqual(1, validate.call_count)
            self.assertEqual(profile.PROFILE,
                             validate.call_args.kwargs["stipple_fixed_point_profile"])
            if passes:
                self.assertIsNone(result)
            else:
                self.assertEqual("typed.validator", result["stage"])
                self.assertIn(profile.PROFILE, result["diagnostic"])

    def test_validator_requires_and_scopes_the_carrier(self) -> None:
        for variant, typed in _trees():
            with self.subTest(variant=variant):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=profile.RAW_SHA256,
                    stipple_fixed_point_profile=profile.PROFILE)
                with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                            "exact Stipple fixed-point profile carrier required"):
                    generate_typed_slice.validate_capabilities(
                        typed, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=profile.RAW_SHA256)
                with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                            "profile metadata mismatch"):
                    generate_typed_slice.validate_capabilities(
                        typed, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=profile.RAW_SHA256,
                        stipple_fixed_point_profile=profile.PROFILE,
                        derivative_admission_profile="derivative-admission-v1")

    def test_emitter_lowers_the_authority_semantics(self) -> None:
        for variant, typed in _trees():
            with self.subTest(variant=variant):
                cpp = emit_typed_cpp.render_typed_cpp(
                    typed, KEY, profile.RAW_SHA256, "typed_probe",
                    "bind_filter_stipple_stipple",
                    stipple_fixed_point_profile=profile.PROFILE)
                # The function-local table and its one counted read.
                self.assertIn(
                    "const std::array<std::uint32_t, 5> M{std::uint32_t(65536), "
                    "std::uint32_t(32284), std::uint32_t(15903), std::uint32_t(7834), "
                    "std::uint32_t(3859)};", cpp)
                self.assertIn("M[static_cast<std::size_t>(k)]", cpp)
                # The blend lanes round to float32 before `>> 12`.
                self.assertIn(
                    "glsl::shift_right(([&]() { const glsl::UVec3 lanes = "
                    "((paper * (std::uint32_t(4096) - inside)) + (ink * inside)); "
                    "return glsl::UVec3(static_cast<std::uint32_t>(noisemaker::f32("
                    "static_cast<double>(lanes[0]))), ", cpp)
                # Both scalar uint quotients are truncated, so `t` stays uint.
                self.assertIn("std::int32_t aa = glsl::detail::glsl_int_cast(std::trunc(", cpp)
                self.assertIn("std::uint32_t t = ((d <= (radius - aa)) ? std::uint32_t(0) : "
                              "((d >= (radius + aa)) ? std::uint32_t(4096) : std::trunc(", cpp)
                # Logical shifts with JavaScript's five-bit count mask.
                self.assertIn("(std::uint32_t(16) & 31U)", cpp)
                self.assertIn("return glsl::UVec2(lanes[0] << (counts[0] & 31U), "
                              "lanes[1] << (counts[1] & 31U)); }())", cpp)
                self.assertIn("return glsl::IVec2(lanes[0] >> count, lanes[1] >> count); }())",
                              cpp)
                self.assertEqual(4, cpp.count("(r--);") + cpp.count("(r++);"))
                with self.assertRaisesRegex(emit_typed_cpp.TypedEmissionError,
                                            "exact Stipple fixed-point profile carrier required"):
                    emit_typed_cpp.render_typed_cpp(
                        typed, KEY, profile.RAW_SHA256, "typed_probe",
                        "bind_filter_stipple_stipple")

    def test_typed_slice_row_carries_the_profile(self) -> None:
        rows = [item for item in generate_typed_slice.load_slice(ROOT)["programs"]
                if item["program_key"] == KEY]
        self.assertEqual([{
            "defines": {"MODE": 0},
            "program_key": KEY,
            "runtime_define_profile": generate_typed_slice.GENERIC_RUNTIME_DEFINE_PROFILE,
            "stipple_fixed_point_profile": profile.PROFILE,
        }], rows)


if __name__ == "__main__":
    unittest.main()
