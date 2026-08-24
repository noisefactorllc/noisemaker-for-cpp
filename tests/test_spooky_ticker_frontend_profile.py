from __future__ import annotations
import dataclasses
import copy
import json
import sys
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
KEY = "filter/spookyTicker:spookyTicker"

def load_program():
    from tools.glslcpp import check_corpus, generate_typed_slice
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic import analyze_program
    corpus = check_corpus._corpus_root(ROOT)
    manifest = json.loads((corpus / "manifest.json").read_text())
    entry = next(x for x in manifest["programs"] if x["program_key"] == KEY)
    raw = (corpus / entry["source"]).read_text()
    program = analyze_program(parse_program(raw, KEY, generate_typed_slice._defaults(ROOT, KEY)), KEY)
    return entry["raw_sha256"], program

class SpookyTickerFrontendProfileTests(unittest.TestCase):
    def test_prepared_profile_authenticates_exact_varying_array_and_bitwise_closure(self):
        from tools.glslcpp.frontend import spooky_ticker_frontend_profile as profile
        source_hash, program = load_program()
        proof = profile.authenticate_spooky_ticker_frontend(program, source_hash, profile.PROFILE)
        self.assertEqual(("v_texCoord", "vec2", "context.uv"), (proof.varying_symbol.name, proof.varying_symbol.type.display(), profile.VARYING_RUNTIME_ABI[2]))
        self.assertEqual(("GLYPHS", "int[80]", 80), (proof.global_array.name, proof.global_array.type_name, proof.global_array.extent))
        self.assertEqual(3, len(proof.varying_reads))
        self.assertEqual(11, len(proof.bitwise_nodes))
        self.assertEqual((14, 16, 17, 20),
                         tuple(item.id for item in proof.number_parameters))
        self.assertEqual((51, 52, 57, 58, 59, 43, 44, 49),
                         tuple(item.symbol_id
                               for item in proof.number_declarations))
        self.assertEqual(5, len(proof.number_divisions))
        self.assertEqual(2, len(proof.number_umul_nodes))
        self.assertEqual(1, len(proof.number_remainder_nodes))
        self.assertEqual(("main", "hash_mix", "sample_glyph", "ticker_row_mask"), tuple(item.name for item in proof.closure_functions))
        self.assertIs(proof.closure_functions[0], next(item for item in program.functions if item.name == "main"))
        self.assertIs(proof.varying_reads[0].node, next(item for item in profile._expressions(program) if item.kind == "id" and item.symbol_id == 30))
        self.assertIs(profile.verify_spooky_ticker_frontend(program, proof), proof)

    def test_foreign_program_and_reordered_function_proofs_fail_closed(self):
        from tools.glslcpp.frontend import spooky_ticker_frontend_profile as profile
        source_hash, program = load_program()
        proof = profile.authenticate_spooky_ticker_frontend(program, source_hash, profile.PROFILE)
        foreign = copy.deepcopy(program)
        with self.assertRaisesRegex(ValueError, "closure function identity"):
            profile.verify_spooky_ticker_frontend(program, proof._replace(closure_functions=tuple(foreign.functions[i] for i in (1, 0, 2, 3))))
        with self.assertRaisesRegex(ValueError, "closure function identity"):
            profile.verify_spooky_ticker_frontend(program, proof._replace(closure_functions=foreign.functions))

    def test_candidate_owned_identity_and_operator_mutations_fail_closed(self):
        from tools.glslcpp.frontend import spooky_ticker_frontend_profile as profile
        source_hash, program = load_program()
        proof = profile.authenticate_spooky_ticker_frontend(program, source_hash, profile.PROFILE)
        target = proof.bitwise_nodes[0]
        mutated = dataclasses.replace(target, operator="|")
        def replace(value):
            if value is target: return mutated
            return dataclasses.replace(value, children=tuple(replace(child) for child in value.children))
        mutated_program = dataclasses.replace(program, functions=tuple(dataclasses.replace(fn, body=tuple(dataclasses.replace(stmt, expressions=tuple(replace(x) for x in stmt.expressions), children=stmt.children) for stmt in fn.body)) for fn in program.functions))
        operators = dict(profile._EXPECTED_OPERATORS)
        operators["^"] -= 1
        operators["|"] = 1
        with mock.patch.object(profile, "FUNCTIONS_SHA256", profile._sha(mutated_program.functions)), \
                mock.patch.object(profile, "WHOLE_SHA256", profile._whole(mutated_program)), \
                mock.patch.object(profile, "_EXPECTED_OPERATORS", operators):
            with self.assertRaisesRegex(ValueError, "bitwise"):
                profile.authenticate_spooky_ticker_frontend(mutated_program, source_hash, profile.PROFILE)

    def test_number_lowering_proof_rejects_foreign_equal_nodes(self):
        from tools.glslcpp.frontend import spooky_ticker_frontend_profile as profile
        source_hash, program = load_program()
        proof = profile.authenticate_spooky_ticker_frontend(
            program, source_hash, profile.PROFILE)
        for field, message in (
                ("number_parameters", "Number parameter identity"),
                ("number_declarations", "Number declaration identity"),
                ("number_divisions", "Number division identity"),
                ("number_umul_nodes", "Number umul identity"),
                ("number_remainder_nodes", "Number remainder identity")):
            values = getattr(proof, field)
            replacement = (copy.deepcopy(values[0]), *values[1:])
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, message):
                profile.verify_spooky_ticker_frontend(
                    program, proof._replace(**{field: replacement}))

    def test_runtime_abi_is_explicit_and_prepared_only(self):
        from tools.glslcpp.frontend import spooky_ticker_frontend_profile as profile
        self.assertEqual((), profile.KEYS)
        self.assertEqual((KEY,), profile.PREPARED_KEYS)
        self.assertEqual(("inputTex", "sampler2D", "const Surface&"), profile.SAMPLER_RUNTIME_ABI)
        self.assertEqual(("int[80]", "std::array<std::int32_t, 80>"), profile.GLOBAL_ARRAY_NATIVE_REQUIREMENT)
        self.assertEqual(("^", ">>", "&"), profile.BITWISE_REQUIREMENT)

if __name__ == "__main__": unittest.main()
