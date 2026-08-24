from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import unittest

from tools.glslcpp import generate_typed_slice
from tools.glslcpp import check_corpus
from tools.glslcpp import emit_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import noise_frontend_profile as profile


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"


def analyzed():
    key = profile.KEY
    entry = next(item for item in json.loads(
        (CORPUS / "manifest.json").read_text())['programs']
        if item['program_key'] == key)
    raw = (CORPUS / entry['source']).read_text()
    return analyze_program(
        parse_program(raw, key, generate_typed_slice._defaults(ROOT, key)), key)


class ClassicNoiseFrontendTests(unittest.TestCase):
    def test_exact_source_contract_and_native_interface(self):
        program = analyzed()
        self.assertEqual(profile.RAW_SHA256,
                         hashlib.sha256(program.raw_source.encode()).hexdigest())
        proof = profile.authenticate_noise_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        self.assertEqual(profile.FIXED_DEFINES, proof.defines)
        self.assertEqual(tuple(name for name, _ in profile.SOURCE_UNIFORMS),
                         tuple(item.symbol.name for item in program.declarations
                               if item.symbol.storage == 'uniform'))
        self.assertEqual(profile.REACHABLE_FUNCTION_IDS,
                         tuple(item.signature.id for item in proof.reachable_functions))
        self.assertEqual(profile.DEAD_FUNCTION_IDS,
                         tuple(item.signature.id for item in proof.dead_functions))

    def test_projection_removes_dead_carriers_and_keeps_rotate_and_octaves_loop(self):
        projected = profile.apply_noise_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        self.assertEqual(profile.REACHABLE_FUNCTION_IDS,
                         tuple(item.signature.id for item in projected.functions))
        self.assertEqual(profile.PROJECTED_DECLARATION_NAMES,
                         tuple(item.symbol.name for item in projected.declarations))
        self.assertEqual((), tuple(item for item in projected.declarations
                                   if item.type.display() in {'mat3', 'mat4'}))
        self.assertTrue(any(item.name == 'rotate2D'
                            for item in projected.functions))
        self.assertEqual((1, 0), (projected.counted_loop_proof.loop_count,
                                  projected.counted_loop_proof.unproved_loop_count))
        loop = next(statement for function in projected.functions
                    for statement in function.body
                    if statement.kind == 'for')
        self.assertEqual((1, 8, '<=', '++', 8,
                          'runtime-metadata-uniform-direct-parameter'),
                         (loop.loop_proof.start_value, loop.loop_proof.bound_value,
                          loop.loop_proof.comparison, loop.loop_proof.update,
                          loop.loop_proof.trip_count, loop.loop_proof.bound_kind))

    def test_runtime_contract_is_immutable_and_exactly_octaves(self):
        program = analyzed()
        contract = profile.authenticate_noise_runtime(
            program, profile.RAW_SHA256, profile.PROFILE)
        self.assertEqual(('octaves', 1, 2, 8),
                         (contract.uniform_name, contract.minimum,
                          contract.default, contract.maximum))
        self.assertEqual('octaves', contract.seed.symbol.name)
        with self.assertRaises(ValueError):
            profile.authenticate_noise_runtime(
                dataclasses.replace(program, key='foreign:key'),
                profile.RAW_SHA256, profile.PROFILE)

    def test_projection_rejects_forged_stale_or_wrong_ordered_program(self):
        program = analyzed()
        cases = (
            (dataclasses.replace(program, raw_source=program.raw_source + '\n'),
             profile.RAW_SHA256, profile.PROFILE),
            (program, '0' * 64, profile.PROFILE),
            (program, profile.RAW_SHA256, 'wrong-profile'),
            (dataclasses.replace(program, functions=tuple(reversed(program.functions))),
             profile.RAW_SHA256, profile.PROFILE),
        )
        for candidate, source_hash, selected in cases:
            with self.subTest(selected=selected):
                with self.assertRaisesRegex(ValueError, profile.PROFILE):
                    profile.apply_noise_frontend(candidate, source_hash, selected)

    def test_projection_proof_rejects_truncated_or_missing_fields(self):
        projected = profile.apply_noise_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        proof = profile.authenticate_noise_projection(
            projected, profile.RAW_SHA256, profile.PROFILE)
        forged = (
            proof._replace(functions=()),
            proof._replace(functions=proof.functions[:-1]),
            proof._replace(declarations=()),
            proof._replace(declarations=proof.declarations[:-1]),
            proof._replace(counted_loop_summary=None),
        )
        for candidate in forged:
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(ValueError, profile.PROFILE):
                    profile.verify_noise_projection(projected, candidate)

    def test_frontend_proof_rejects_empty_ledgers(self):
        program = analyzed()
        proof = profile.authenticate_noise_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        for candidate in (proof._replace(matrix_globals=()),
                          proof._replace(consumed_objects=())):
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(ValueError, profile.PROFILE):
                    profile.verify_noise_frontend(program, candidate)

    def test_runtime_auth_rejects_unrelated_dead_function_rename(self):
        program = analyzed()
        dead = next(item for item in program.functions
                    if item.signature.id not in profile.REACHABLE_FUNCTION_IDS)
        renamed = dataclasses.replace(
            dead, signature=dataclasses.replace(
                dead.signature, name=dead.signature.name + '_forged'))
        mutated = dataclasses.replace(
            program, functions=tuple(renamed if item is dead else item
                                     for item in program.functions))
        with self.assertRaisesRegex(ValueError, profile.PROFILE):
            profile.authenticate_noise_runtime(
                mutated, profile.RAW_SHA256, profile.PROFILE)

    def test_validator_and_emitter_select_exact_projected_profile(self):
        projected = profile.apply_noise_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        generate_typed_slice.validate_capabilities(
            projected, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=profile.RAW_SHA256,
            noise_frontend_profile=profile.PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            projected, profile.KEY, profile.RAW_SHA256,
            noise_frontend_profile=profile.PROFILE)
        self.assertIn('octaves must be in [1,8]', rendered)
        self.assertEqual(24, rendered.count('bindings.get'))
        self.assertNotIn('COLOR_MODE', rendered)
        self.assertNotIn('LOOP_OFFSET', rendered)

    def test_validator_and_emitter_reject_missing_profile_carrier(self):
        projected = profile.apply_noise_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    'exact Classic Noise frontend profile carrier'):
            generate_typed_slice.validate_capabilities(
                projected, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=profile.RAW_SHA256)
        with self.assertRaisesRegex(emit_typed_cpp.TypedEmissionError,
                                    'exact Classic Noise frontend profile carrier'):
            emit_typed_cpp.render_typed_cpp(
                projected, profile.KEY, profile.RAW_SHA256)


if __name__ == '__main__':
    unittest.main()
