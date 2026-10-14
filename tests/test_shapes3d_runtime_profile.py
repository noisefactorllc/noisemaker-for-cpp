"""Exact source-bound Shapes3D dynamic define admission regressions."""
import dataclasses
import hashlib
import json
import unittest
from pathlib import Path

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.loop_proof import SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
from tools.glslcpp.frontend.shapes3d_runtime_profile import KEY, RAW, authenticate
from tools.glslcpp.frontend.shapes3d_round_profile import authenticate_shapes3d_rounds
from tools.glslcpp.frontend.struct_frontier_profile import apply_struct_frontier, SHAPES3D_PROFILE

CORPUS=Path(__file__).resolve().parents[1]/'tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d'
ENTRY=next(x for x in json.loads((CORPUS/'manifest.json').read_text())['programs'] if x['program_key']==KEY)
SOURCE=(CORPUS/ENTRY['source']).read_text()

class Shapes3dRuntimeProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parsed=parse_program(transform_source(SOURCE,KEY),KEY,{'BLEND_MODE':'int','SHAPE_A':'int','SHAPE_B':'int'})
        parsed['raw_source']=SOURCE
        cls.dynamic=analyze_program(parsed,KEY,source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
    def test_dynamic_exact(self):
        structs,indices,rounds=authenticate(self.dynamic,RAW)
        self.assertEqual((2,5,2),(len(structs.structs),len(indices),len(rounds)))
    def test_default_proofs_stay_locked(self):
        parsed=parse_program(SOURCE,KEY,{'BLEND_MODE':10,'SHAPE_A':30,'SHAPE_B':10})
        default=analyze_program(parsed,KEY,source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        self.assertEqual(2,len(authenticate_shapes3d_rounds(default,RAW)))
        self.assertEqual(2,len(apply_struct_frontier(default,RAW,SHAPES3D_PROFILE).structs))
    def test_rejects_raw_source_forgery(self):
        forged=dataclasses.replace(self.dynamic,raw_source=self.dynamic.raw_source+' ')
        with self.assertRaises(ValueError):authenticate(forged,RAW)
    def test_rejects_typed_tree_forgery(self):
        first=dataclasses.replace(self.dynamic.functions[0],signature=dataclasses.replace(self.dynamic.functions[0].signature,name='forged_name'))
        forged=dataclasses.replace(self.dynamic,functions=(first,)+self.dynamic.functions[1:])
        with self.assertRaises(ValueError):authenticate(forged,RAW)
    def test_rejects_compile_define_forgery(self):
        define=dataclasses.replace(self.dynamic.preprocessor_defines[0],canonical_value='11')
        forged=dataclasses.replace(self.dynamic,preprocessor_defines=(define,)+self.dynamic.preprocessor_defines[1:])
        with self.assertRaises(ValueError):authenticate(forged,RAW)

if __name__=='__main__':unittest.main()
