from __future__ import annotations

import importlib
import pathlib
import unittest
import dataclasses
import copy

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "filter/historicPalette:historicPalette"
SOURCE = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/historicPalette/historicPalette.glsl"
RAW_SHA256 = "cc0feb09e2f90505766a0b8b0d61ca0cf83a1121ec7b104eea5ff806c9ce0c33"
PROFILE = "historic-palette-frontend-admission-v1"

def _profile():
    return importlib.import_module("tools.glslcpp.frontend.historic_palette_profile")

def _program():
    raw = SOURCE.read_bytes().decode("utf-8")
    return analyze_program(parse_program(raw, KEY, generate_typed_slice._defaults(ROOT, KEY)), KEY)

class HistoricPaletteProfileTests(unittest.TestCase):
    def test_authenticates_exact_struct_table_and_interface(self):
        module = _profile()
        program = _program()
        result = module.authenticate_historic_palette(program, RAW_SHA256, PROFILE)
        self.assertIsInstance(result, module.HistoricPaletteProof)
        self.assertIs(result.struct, program.structs[0])
        self.assertIs(result.palettes_declaration, next(d for d in program.declarations if d.symbol.name == "PALETTES"))
        self.assertEqual(len(result.palette_entries), 21)
        self.assertEqual(len(result.vec3_constructors), 105)
        self.assertEqual(len(result.palette_literals), 315)
        self.assertEqual(len(result.palette_index_reads), 1)
        self.assertEqual(len(result.consumed_nodes), 464)
        self.assertEqual(len({id(node) for node in result.consumed_nodes}), len(result.consumed_nodes))
        self.assertEqual(module.verify_historic_palette_proof(program, result), result)

    def test_proof_rejects_replaced_consumed_node(self):
        module = _profile()
        program = _program()
        proof = module.authenticate_historic_palette(program, RAW_SHA256, PROFILE)
        replaced = list(proof.palette_literals)
        replaced[0] = copy.deepcopy(replaced[0])
        forged = dataclasses.replace(proof, palette_literals=tuple(replaced))
        with self.assertRaises(ValueError):
            module.verify_historic_palette_proof(program, forged)

    def test_profile_rejects_source_or_interface_drift(self):
        module = _profile()
        with self.assertRaises(ValueError):
            module.authenticate_historic_palette(_program(), "0" * 64, PROFILE)
        mutated = _program()
        mutated = dataclasses.replace(mutated, raw_source=mutated.raw_source + "\n")
        with self.assertRaises(ValueError):
            module.authenticate_historic_palette(mutated, RAW_SHA256, PROFILE)

    def test_profile_lock_is_exact_and_not_generic(self):
        module = _profile()
        self.assertEqual(module.KEYS, (KEY,))
        self.assertEqual(module.PROFILE, PROFILE)
        self.assertEqual(module.EXPECTED_STRUCT_FIELDS, ("color1", "color2", "color3", "color4", "color5"))

if __name__ == "__main__":
    unittest.main()
