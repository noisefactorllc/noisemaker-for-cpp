"""Authenticate frozen and current Shape sources without crossing identities."""
from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source
from tools.glslcpp.frontend.mutable_global_frame_profile import authenticate_mutable_global_frame
from tools.glslcpp.frontend.scalar_uint_xor_profile import (
    authenticate_scalar_uint_xor, authenticate_scalar_uint_to_float_narrowing_skips)
from tools.glslcpp.frontend.shape_positive_modulo_profile import authenticate_shape_positive_modulo

ROOT = Path(__file__).resolve().parents[1]
KEY = 'synth/shape:shape'
REVISIONS = ('d0ed94ae19cca7328bc7d6b28902712a0838e1a9',
             '67d6e44c750e4f9bebb34f88645b934e3b933a84')

class SyncShapeProfilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = []
        for revision in REVISIONS:
            raw = (ROOT / 'tools/glslcpp/corpus' / revision / 'sources/synth/shape/shape.glsl').read_text()
            for dynamic in (False, True):
                defines = dict(LOOP_A_OFFSET='int' if dynamic else 40,
                               LOOP_B_OFFSET='int' if dynamic else 30)
                parsed = parse_program(transform_source(raw, KEY), KEY, defines)
                parsed['raw_source'] = raw
                cls.cases.append((revision, dynamic, hashlib.sha256(raw.encode()).hexdigest(),
                                  analyze_program(parsed, KEY)))

    def test_both_source_revisions_default_and_runtime(self):
        for revision, dynamic, sha, program in self.cases:
            with self.subTest(revision=revision, dynamic=dynamic):
                self.assertEqual(2, len(authenticate_mutable_global_frame(program, sha, 'mutable-global-frame-shape-v1')))
                self.assertEqual(3, len(authenticate_scalar_uint_xor(program, sha, 'scalar-uint-xor-v1')))
                self.assertEqual((), authenticate_scalar_uint_to_float_narrowing_skips(program, sha, 'scalar-uint-xor-v1'))
                result = authenticate_shape_positive_modulo(program, sha)
                self.assertEqual('positiveModulo' if dynamic else None, result.name if result else None)

    def test_source_tree_defines_and_foreign_carrier_rejected(self):
        for revision, dynamic, sha, program in self.cases:
            for label, mutant, claimed in (
                ('hash', program, '0' * 64),
                ('raw', replace(program, raw_source=program.raw_source+'\n'), sha),
                ('tree', replace(program, functions=program.functions[:-1]), sha),
                ('defines', replace(program, preprocessor_defines=()), sha),
                ('foreign', replace(program, fixed_nine_table_proof=object()), sha),
            ):
                for authenticate, carrier in ((authenticate_mutable_global_frame, 'mutable-global-frame-shape-v1'),
                                               (authenticate_scalar_uint_xor, 'scalar-uint-xor-v1')):
                    with self.subTest(revision=revision, dynamic=dynamic, label=label, profile=carrier):
                        with self.assertRaises(ValueError): authenticate(mutant, claimed, carrier)
            other_sha = next(h for r, _, h, _ in self.cases if r != revision)
            with self.subTest(revision=revision, dynamic=dynamic), self.assertRaises(ValueError):
                authenticate_scalar_uint_xor(program, other_sha, 'scalar-uint-xor-v1')
            if dynamic:
                for mutant, claimed in ((program, other_sha),
                        (replace(program, raw_source=program.raw_source+'\n'),sha),
                        (replace(program, functions=program.functions[:-1]),sha)):
                    with self.subTest(revision=revision, modulo=True), self.assertRaises(ValueError):
                        authenticate_shape_positive_modulo(mutant, claimed)
