from __future__ import annotations

import dataclasses
import copy
import hashlib
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          "/sources/filter/palette/palette.glsl")
KEY = "filter/palette:palette"
PROFILE = "palette-frontend-admission-v1"

sys.path.insert(0, str(ROOT))


def _program():
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic import analyze_program

    raw = SOURCE.read_text(encoding="utf-8")
    return analyze_program(parse_program(raw, KEY, {}), KEY)


class PaletteFrontendProfileTests(unittest.TestCase):
    def test_profile_registry_is_palette_only_and_fail_closed(self):
        from tools.glslcpp.frontend import palette_frontend_profile as profile

        self.assertEqual(KEY, profile.KEY)
        self.assertEqual(PROFILE, profile.PROFILE)
        self.assertEqual((KEY,), profile.KEYS)
        self.assertEqual((), profile.PREPARED_KEYS)
        self.assertEqual({KEY: PROFILE}, profile.PROFILES)
        self.assertEqual(
            {"defines", "program_key", "palette_frontend_profile"},
            set(profile.ALLOWED_ROW_FIELDS[KEY]),
        )
        self.assertTrue(SOURCE.is_relative_to(ROOT))

    def test_exact_interface_struct_and_const_array_closure(self):
        from tools.glslcpp.frontend import palette_frontend_profile as profile

        program = _program()
        proof = profile.authenticate_palette_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(), PROFILE
        )
        self.assertEqual(KEY, proof.program_key)
        self.assertEqual(PROFILE, proof.profile)
        self.assertEqual(
            ("tileOffset", "fullResolution", "inputTex", "paletteIndex",
             "rotation", "offset", "repeat", "alpha", "time"),
            proof.uniform_names,
        )
        self.assertEqual(("PaletteEntry", 4, 55),
                         (proof.struct_name, proof.struct_field_count,
                          proof.palette_count))
        self.assertEqual(("amp", "freq", "offset", "phase"), proof.field_names)
        self.assertEqual(276, proof.const_array_construct_count)
        self.assertEqual(1, proof.palette_index_count)
        self.assertIsNotNone(proof.palettes_declaration)
        self.assertEqual(program.declarations[14], proof.palettes_declaration)
        self.assertIs(proof.program, program)
        self.assertIs(proof.struct, program.structs[0])
        self.assertIs(proof.palette_count_declaration, program.declarations[13])
        self.assertEqual(55, len(proof.palette_entries))
        self.assertEqual(55, len(proof.palette_entry_constructors))
        self.assertEqual(220, len(proof.vec4_constructors))
        self.assertEqual(880, len(proof.palette_literals))
        self.assertEqual(1, len(proof.palette_index_reads))
        self.assertEqual(1, len(proof.exceptional_nodes))
        self.assertEqual(1180, len(proof.consumed_nodes))
        self.assertEqual("glsl::FloatExpr<4>", proof.table_native_type)
        self.assertIs(proof.tau_initializer, proof.tau_declaration.initializer)
        self.assertIs(proof.cosine_vector_sites[0],
                      proof.cosine_clamp_site.children[0])
        self.assertIs(proof.cosine_vector_sites[1],
                      proof.cosine_vector_sites[0].children[1])
        self.assertEqual(len(proof.consumed_nodes), len({id(node) for node in proof.consumed_nodes}))
        self.assertIs(profile.verify_palette_frontend_proof(program, proof), proof)
        self.assertIs(program, profile.apply_palette_frontend(program, proof.source_hash, PROFILE))

    def test_source_interface_and_ast_mutations_are_rejected(self):
        from tools.glslcpp.frontend import palette_frontend_profile as profile

        program = _program()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "source provenance"):
            profile.authenticate_palette_frontend(program, "0" * 64, PROFILE)
        with self.assertRaisesRegex(ValueError, "program key"):
            profile.authenticate_palette_frontend(
                dataclasses.replace(program, key="filter/foreign:palette"), source_hash, PROFILE
            )
        with self.assertRaisesRegex(ValueError, "AST fingerprint"):
            forged = dataclasses.replace(
                program, structs=(dataclasses.replace(program.structs[0], name="ForeignEntry"),)
            )
            profile.authenticate_palette_frontend(forged, source_hash, PROFILE)

    def test_live_proof_rejects_replaced_or_reordered_consumed_nodes(self):
        from tools.glslcpp.frontend import palette_frontend_profile as profile

        program = _program()
        proof = profile.authenticate_palette_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(), PROFILE
        )
        copied = list(proof.palette_literals)
        copied[0] = copy.deepcopy(copied[0])
        with self.assertRaisesRegex(ValueError, "palette_literals identity"):
            profile.verify_palette_frontend_proof(
                program, dataclasses.replace(proof, palette_literals=tuple(copied))
            )
        with self.assertRaisesRegex(ValueError, "tau_declaration identity"):
            profile.verify_palette_frontend_proof(
                program, dataclasses.replace(
                    proof, tau_declaration=copy.deepcopy(proof.tau_declaration)))
        with self.assertRaisesRegex(ValueError, "cosine_site identity"):
            profile.verify_palette_frontend_proof(
                program, dataclasses.replace(
                    proof, cosine_site=copy.deepcopy(proof.cosine_site)))
        reordered = proof.consumed_nodes[1:] + proof.consumed_nodes[:1]
        with self.assertRaisesRegex(ValueError, "ledger identity"):
            profile.verify_palette_frontend_proof(
                program, dataclasses.replace(proof, consumed_nodes=reordered)
            )

    def test_live_proof_rejects_replaced_program_and_exceptional_form(self):
        from tools.glslcpp.frontend import palette_frontend_profile as profile

        program = _program()
        proof = profile.authenticate_palette_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(), PROFILE
        )
        with self.assertRaisesRegex(ValueError, "selected live program"):
            profile.verify_palette_frontend_proof(copy.deepcopy(program), proof)
        forged = dataclasses.replace(
            proof, exceptional_nodes=(copy.deepcopy(proof.exceptional_nodes[0]),)
        )
        with self.assertRaisesRegex(ValueError, "exceptional_nodes identity"):
            profile.verify_palette_frontend_proof(program, forged)


if __name__ == "__main__":
    unittest.main()
