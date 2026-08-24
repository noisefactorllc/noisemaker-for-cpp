from __future__ import annotations

import hashlib
import pathlib
from dataclasses import replace
import unittest

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.loop_proof import (
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
    SOURCE_GLOBAL_LITERAL_INT_KEYS,
    _SOURCE_GLOBAL_LITERAL_INT_PROFILES,
    attach_counted_loop_proofs,
    summarize_counted_loop_proofs)
from tools.glslcpp.frontend import mandelbrot_sequential_dz_assignment_profile as module


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "synth/mandelbrot:mandelbrot"
PROFILE = "mandelbrot-sequential-dz-assignment-v1"
SOURCE = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6" / "sources/synth/mandelbrot/mandelbrot.glsl"
RAW_SHA256 = "0587dbc29f2dc8c186d7c47ebe6182e89dfe0387fc29a23826cac15499fba615"


def _analyzed(raw: str | None = None, key: str = KEY):
    text = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(
        parse_program(text, key, generate_typed_slice._defaults(ROOT, key)), key)


def _seeded():
    program = _analyzed()
    seed = next(item for item in program.declarations
                if item.symbol.name == "MAX_ITER")
    functions = attach_counted_loop_proofs(
        program.functions, KEY,
        source_global_bounds=((seed.symbol.id, 500,
                               "source-global-const-literal", seed.symbol),))
    return replace(program, functions=functions,
                   counted_loop_proof=summarize_counted_loop_proofs(functions))


class MandelbrotSequentialDzAssignmentTests(unittest.TestCase):
    def test_authenticates_only_the_exact_dz_assignment(self):
        proof = module.authenticate_mandelbrot_sequential_dz_assignment(
            _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(KEY, proof.candidate.key)
        self.assertEqual("mandelbrot_df64", proof.function.name)
        self.assertEqual("dz", proof.destination.symbol.name)
        self.assertEqual((0, 1), proof.source_lanes)
        self.assertEqual((0, 1), proof.destination_lanes)
        self.assertEqual(4, proof.source_reads)
        candidate = _analyzed()
        self.assertIs(candidate, module.apply_mandelbrot_sequential_dz_assignment(
            candidate, RAW_SHA256, PROFILE))

    def test_wrong_key_and_profile_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "exact profile carrier required"):
            module.authenticate_mandelbrot_sequential_dz_assignment(
                _analyzed(), RAW_SHA256, "cross-lane-assignment-v1")
        with self.assertRaisesRegex(ValueError, "exact source and key identity"):
            module.authenticate_mandelbrot_sequential_dz_assignment(
                _analyzed(key="foreign/mandelbrot:mandelbrot"), RAW_SHA256, PROFILE)

    def test_forged_destination_is_rejected(self):
        program = _analyzed()
        function = next(item for item in program.functions
                        if item.name == "mandelbrot_df64")
        def statements(items):
            for item in items:
                yield item
                yield from statements(item.children)
        statement = next(item for item in statements(function.body)
                         if any(expression.kind == "assign"
                                and expression.span.start_line == 234
                                for expression in item.expressions))
        assignment = statement.expressions[0]
        target, rhs = assignment.children
        original_symbol_id = target.symbol_id
        object.__setattr__(target, "symbol_id", 167)
        with self.assertRaisesRegex(ValueError, "destination identity mismatch"):
            module.authenticate_mandelbrot_sequential_dz_assignment(
                program, RAW_SHA256, PROFILE)
        object.__setattr__(target, "symbol_id", original_symbol_id)

    def test_source_hash_is_bound_to_the_canonical_source(self):
        raw = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(RAW_SHA256, hashlib.sha256(raw.encode()).hexdigest())
        with self.assertRaisesRegex(ValueError, "exact source and key identity"):
            module.authenticate_mandelbrot_sequential_dz_assignment(
                _analyzed(), "0" * 64, PROFILE)

    def test_profile_has_no_generic_gradient_alias(self):
        self.assertNotEqual(module.PROFILE, "cross-lane-assignment-v1")
        self.assertEqual(KEY, module.KEY)

    def test_generator_requires_and_consumes_all_three_mandelbrot_carriers(self):
        program = _seeded()
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=RAW_SHA256,
            source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
            log_admission_profile="log-admission-mandelbrot-v1",
            out_inout_admission_profile="out-inout-admission-mandelbrot-v1",
            mandelbrot_sequential_dz_assignment_profile=PROFILE)
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "exact Mandelbrot sequential-dz profile carrier required"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256,
                source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
                log_admission_profile="log-admission-mandelbrot-v1",
                out_inout_admission_profile="out-inout-admission-mandelbrot-v1")

    def test_max_iter_seed_is_registered_once_and_matches_log_owner(self):
        from tools.glslcpp.frontend import log_admission_profile
        self.assertIn(KEY, SOURCE_GLOBAL_LITERAL_INT_KEYS)
        self.assertEqual(
            log_admission_profile.counted_for_seed_contract(KEY)._asdict(),
            _SOURCE_GLOBAL_LITERAL_INT_PROFILES[KEY])


if __name__ == "__main__":
    unittest.main()
