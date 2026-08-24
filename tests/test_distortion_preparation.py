from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.frontend import distortion_frontend_profile as profile
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/mixer/distortion/distortion.glsl"


def analyzed(raw: str | None = None, key: str = profile.KEY):
    text = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(parse_program(text, key, {}), key)


def replace_expression(value, target, replacement):
    if value is target:
        return replacement
    return dataclasses.replace(
        value, children=tuple(replace_expression(child, target, replacement)
                              for child in value.children))


def replace_statement(statement, target, replacement):
    return dataclasses.replace(
        statement,
        expressions=tuple(replace_expression(item, target, replacement)
                          for item in statement.expressions),
        children=tuple(replace_statement(child, target, replacement)
                        for child in statement.children))


class DistortionPreparedFrontendTests(unittest.TestCase):
    def test_prepared_registry_and_frontier_contract(self):
        self.assertEqual((), profile.KEYS)
        self.assertEqual((profile.KEY,), profile.PREPARED_KEYS)
        self.assertEqual({profile.KEY: profile.PROFILE}, profile.PROFILES)
        self.assertEqual({profile.KEY: profile.PROFILE}, profile.PREPARED_PROFILES)
        self.assertEqual(
            frozenset({"defines", "program_key", "distortion_frontend_profile"}),
            profile.ALLOWED_ROW_FIELDS[profile.KEY])
        self.assertEqual((), profile.REQUIRED_COMPANION_PROFILES[profile.KEY])
        self.assertEqual(7, sum(len(names) for _, names, _ in profile.SAMPLER_PARAMETER_FUNCTIONS))
        self.assertEqual(6, len(profile.DERIVATIVE_SPANS))
        self.assertEqual(3, len(profile.LOCAL_ARRAY_DECLARATIONS))
        self.assertEqual(
            ("inputTex", "sampler2D", "const Surface&", "tex", "sampler2D", "const Surface&"),
            profile.SAMPLER_RUNTIME_ABI)

    def test_authentication_returns_source_bound_disjoint_live_proof(self):
        program = analyzed()
        proof = profile.authenticate_distortion_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(), profile.PROFILE)
        self.assertEqual(profile.KEY, proof.program_key)
        self.assertEqual(7, len(proof.sampler_parameter_nodes))
        self.assertEqual(6, len(proof.derivative_nodes))
        self.assertEqual(30, len(proof.indexed_nodes))
        self.assertEqual(3, len(proof.local_array_declarations))
        self.assertEqual(len(proof.consumed_objects), len({id(x) for x in proof.consumed_objects}))
        self.assertIs(program, profile.apply_distortion_frontend(
            program, profile.RAW_SHA256, profile.PROFILE))

    def test_exact_frontier_blockers_are_exposed(self):
        program = analyzed()
        proof = program.counted_loop_proof
        self.assertEqual(profile.LOOP_PROOF, (proof.loop_count, proof.unproved_loop_count,
                                              proof.max_effective_depth, proof.max_lexical_product,
                                              proof.entrypoint_charge, proof.call_graph_acyclic))
        self.assertEqual(("calculateNormal", ("mapTex",), "26:1-72:2"),
                         profile.SAMPLER_PARAMETER_FUNCTIONS[-1])
        self.assertEqual(("sobel_x", "float[9]", "31:11-31:21"),
                         profile.LOCAL_ARRAY_DECLARATIONS[0])

    def test_wrong_identity_or_source_fails_closed(self):
        program = analyzed()
        for candidate, source_hash, selected in (
                (program, "0" * 64, profile.PROFILE),
                (program, profile.RAW_SHA256, "wrong-profile"),
                (dataclasses.replace(program, key="foreign:key"), profile.RAW_SHA256, profile.PROFILE)):
            with self.assertRaisesRegex(ValueError, profile.PROFILE):
                profile.authenticate_distortion_frontend(candidate, source_hash, selected)

    def test_derivative_mutation_is_rejected_even_when_candidate_is_rebuilt(self):
        program = analyzed()
        target = next(item for item in profile._expressions(program)
                      if item.kind == "builtin" and item.callee == "dFdx")
        changed_node = dataclasses.replace(target, callee="dFdy")
        changed = dataclasses.replace(
            program,
            functions=tuple(dataclasses.replace(
                function,
                body=tuple(replace_statement(statement, target, changed_node)
                           for statement in function.body))
                for function in program.functions))
        with self.assertRaisesRegex(ValueError, "lock mismatch|derivative|source"):
            profile.authenticate_distortion_frontend(changed, profile.RAW_SHA256, profile.PROFILE)


if __name__ == "__main__":
    unittest.main()
