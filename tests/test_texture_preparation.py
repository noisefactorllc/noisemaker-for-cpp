from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import texture_frontend_profile as profile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/texture/texture.glsl"


def analyzed(raw: str | None = None, key: str = profile.KEY):
    text = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(parse_program(text, key, {"MODE": 3}), key)


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


class TexturePreparedFrontendTests(unittest.TestCase):
    def test_prepared_registry_and_exact_runtime_contract(self):
        self.assertEqual((), profile.KEYS)
        self.assertEqual((profile.KEY,), profile.PREPARED_KEYS)
        self.assertEqual({profile.KEY: profile.PROFILE}, profile.PROFILES)
        self.assertEqual({profile.KEY: profile.PROFILE}, profile.PREPARED_PROFILES)
        self.assertEqual(
            frozenset({"defines", "program_key", "texture_frontend_profile"}),
            profile.ALLOWED_ROW_FIELDS[profile.KEY])
        self.assertEqual((), profile.REQUIRED_COMPANION_PROFILES[profile.KEY])
        self.assertEqual(("inputTex", "sampler2D", "const Surface&"),
                         profile.SAMPLER_RUNTIME_ABI)
        self.assertEqual(("v_texCoord", "vec2", "context.uv", "read-only"),
                         profile.VARYING_RUNTIME_ABI)
        self.assertEqual(("Z_LOOP", "const int", 2, "loop-free modulo divisor"),
                         profile.GLOBAL_INT_REQUIREMENT)

    def test_authentication_returns_source_bound_disjoint_live_proof(self):
        program = analyzed()
        proof = profile.authenticate_texture_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(),
            profile.PROFILE)
        self.assertEqual(("v_texCoord", "vec2", 103, "1:1-326:1"), proof.varying)
        self.assertEqual(("texture", "textureSize"), proof.sampler_builtins)
        self.assertEqual(10, len(proof.bitwise_nodes))
        self.assertEqual(len(proof.consumed_objects),
                         len({id(item) for item in proof.consumed_objects}))
        self.assertIs(program, profile.apply_texture_frontend(
            program, profile.RAW_SHA256, profile.PROFILE))

    def test_wrong_identity_or_source_fails_closed(self):
        program = analyzed()
        for candidate, source_hash, selected in (
                (program, "0" * 64, profile.PROFILE),
                (program, profile.RAW_SHA256, "wrong-profile"),
                (dataclasses.replace(program, key="foreign:key"),
                 profile.RAW_SHA256, profile.PROFILE)):
            with self.assertRaisesRegex(ValueError, profile.PROFILE):
                profile.authenticate_texture_frontend(candidate, source_hash, selected)

    def test_bitwise_mutation_is_rejected_even_when_candidate_is_rebuilt(self):
        program = analyzed()
        target = next(item for item in profile._expressions(program)
                      if item.kind == "binary" and item.operator == "^")
        mutated = dataclasses.replace(target, operator="|")
        changed = dataclasses.replace(
            program,
            functions=tuple(dataclasses.replace(
                function,
                body=tuple(replace_statement(statement, target, mutated)
                           for statement in function.body))
                for function in program.functions))
        with self.assertRaisesRegex(ValueError, "lock mismatch|bitwise"):
            profile.authenticate_texture_frontend(
                changed, profile.RAW_SHA256, profile.PROFILE)

    def test_sampler_and_varying_contracts_are_live_not_documentary(self):
        program = analyzed()
        varying = program.interface_symbols[0]
        changed = dataclasses.replace(
            program, interface_symbols=(dataclasses.replace(varying, name="forged"),))
        with self.assertRaises(ValueError):
            profile.authenticate_texture_frontend(
                changed, profile.RAW_SHA256, profile.PROFILE)


if __name__ == "__main__":
    unittest.main()
