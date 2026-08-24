from __future__ import annotations

import dataclasses
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock


REPOSITORY = Path(__file__).resolve().parents[1]
KEY = "filter/osd:osd"


def _load_program():
    from tools.glslcpp import check_corpus, generate_typed_slice
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic import analyze_program

    corpus = check_corpus._corpus_root(REPOSITORY)
    manifest = json.loads((corpus / "manifest.json").read_text())
    entry = next(item for item in manifest["programs"]
                 if item["program_key"] == KEY)
    raw = (corpus / entry["source"]).read_text()
    program = analyze_program(
        parse_program(raw, KEY, generate_typed_slice._defaults(REPOSITORY, KEY)),
        KEY)
    return entry["raw_sha256"], program


class OsdFrontendProfileTests(unittest.TestCase):
    def test_profile_module_exists_and_is_prepared_only(self):
        self.assertIsNotNone(
            importlib.util.find_spec("tools.glslcpp.frontend.osd_frontend_profile"))
        from tools.glslcpp.frontend import osd_frontend_profile as profile

        self.assertEqual(KEY, profile.KEY)
        self.assertEqual("osd-frontend-admission-v1", profile.PROFILE)
        self.assertEqual((), profile.KEYS)
        self.assertEqual((KEY,), profile.PREPARED_KEYS)
        self.assertEqual({KEY: profile.PROFILE}, profile.PREPARED_PROFILES)

    def test_exact_source_interface_and_sampler_contract_authenticates(self):
        from tools.glslcpp.frontend import osd_frontend_profile as profile

        source_hash, program = _load_program()
        proof = profile.authenticate_osd_frontend(
            program, source_hash, profile.PROFILE)
        self.assertEqual(KEY, proof.program_key)
        self.assertEqual(("GLYPHS", "int[80]", 80),
                         (proof.global_array.name, proof.global_array.type_name,
                          proof.global_array.extent))
        self.assertEqual(("textureSize", "texelFetch"), proof.sampler_builtins)
        self.assertEqual(10, len(proof.bitwise_nodes))
        self.assertEqual("pcg", proof.pcg_function.name)
        self.assertEqual(5, len(proof.pcg_bitwise_nodes))
        self.assertEqual(("%", "%"),
                         tuple(node.operator for node in proof.hash_modulo_nodes))
        self.assertEqual(15, len(proof.consumed_objects))
        self.assertEqual(15, len({id(item) for item in proof.consumed_objects}))

    def test_exact_bitwise_and_array_cardinality_rejects_ast_mutation(self):
        from tools.glslcpp.frontend import osd_frontend_profile as profile

        source_hash, program = _load_program()
        proof = profile.authenticate_osd_frontend(
            program, source_hash, profile.PROFILE)
        target = proof.bitwise_nodes[0]
        mutated = dataclasses.replace(target, operator="|")

        def replace(value):
            if value is target:
                return mutated
            return dataclasses.replace(value, children=tuple(
                replace(child) for child in value.children))

        mutated_program = dataclasses.replace(
            program,
            functions=tuple(dataclasses.replace(
                function,
                body=tuple(dataclasses.replace(
                    statement,
                    expressions=tuple(replace(item)
                                      for item in statement.expressions),
                    children=statement.children)
                    for statement in function.body))
                for function in program.functions))
        expected_operators = dict(profile._EXPECTED_OPERATORS)
        expected_operators["^"] -= 1
        expected_operators["|"] = 1
        with mock.patch.object(
                profile, "FUNCTIONS_SHA256", profile._sha(mutated_program.functions)), \
                mock.patch.object(profile, "WHOLE_SHA256",
                                   profile._whole(mutated_program)), \
                mock.patch.object(profile, "_EXPECTED_OPERATORS",
                                   expected_operators):
            with self.assertRaisesRegex(ValueError, "bitwise census"):
                profile.authenticate_osd_frontend(
                    mutated_program, source_hash, profile.PROFILE)

    def test_fail_closed_key_hash_and_apply_identity(self):
        from tools.glslcpp.frontend import osd_frontend_profile as profile

        source_hash, program = _load_program()
        with self.assertRaises(ValueError):
            profile.authenticate_osd_frontend(program, "0" * 64,
                                               profile.PROFILE)
        with self.assertRaises(ValueError):
            profile.authenticate_osd_frontend(
                dataclasses.replace(program, key="foreign:key"),
                source_hash, profile.PROFILE)
        self.assertIs(program, profile.apply_osd_frontend(
            program, source_hash, profile.PROFILE))

    def test_runtime_requirements_are_explicitly_bounded(self):
        from tools.glslcpp.frontend import osd_frontend_profile as profile

        self.assertEqual(("inputTex", "sampler2D", "const Surface&"),
                         profile.SAMPLER_RUNTIME_ABI)
        self.assertEqual(("textureSize", "ivec2", 0),
                         profile.TEXTURE_SIZE_CONTRACT)
        self.assertEqual(("texelFetch", "vec4", 0, "bottom-left"),
                         profile.TEXEL_FETCH_CONTRACT)
        self.assertEqual(("int[80]", "std::array<std::int32_t, 80>"),
                         profile.GLOBAL_ARRAY_NATIVE_REQUIREMENT)
        self.assertEqual(("^", ">>", "&"), profile.BITWISE_REQUIREMENT)


if __name__ == "__main__":
    unittest.main()
