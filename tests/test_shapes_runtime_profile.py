import dataclasses
import hashlib
import json
import pathlib
import unittest

from tools.glslcpp import generate_typed_slice as generator
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import (
    scalar_uint_xor_profile as xor,
    shapes_float_bits_ingress_profile as ingress,
    shapes_rvalue_assign_profile as rvalue,
    linear_srgb_lane_index_profile as lane,
)


_LOCAL_REPO = pathlib.Path(__file__).resolve().parents[1]
REPO = _LOCAL_REPO if (_LOCAL_REPO / 'tools/glslcpp/corpus').exists() else pathlib.Path.cwd()
KEY = 'classicNoisedeck/shapes:shapes'
ROOT = REPO / 'tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d'
MANIFEST = json.loads((ROOT / 'manifest.json').read_text())
ENTRY = next(item for item in MANIFEST['programs'] if item['program_key'] == KEY)
RAW = (ROOT / ENTRY['source']).read_text()
SHA = hashlib.sha256(RAW.encode()).hexdigest()
PROFILES = dict(
    scalar_uint_xor_profile=xor.PROFILE,
    shapes_float_bits_ingress_profile=ingress.PROFILE,
    shapes_rvalue_assign_profile=rvalue.PROFILE,
    linear_srgb_lane_index_profile=lane.PROFILES[KEY],
)


def program(dynamic):
    if dynamic:
        parsed = parse_program(transform_source(RAW, KEY), KEY,
                               {'LOOP_A_OFFSET': 'int', 'LOOP_B_OFFSET': 'int'})
    else:
        parsed = parse_program(RAW, KEY,
                               {'LOOP_A_OFFSET': 40, 'LOOP_B_OFFSET': 30})
    parsed['raw_source'] = RAW
    return analyze_program(parsed, KEY)


class ShapesRuntimeProfileTests(unittest.TestCase):
    def test_exact_default_and_dynamic_proofs(self):
        for dynamic in (False, True):
            with self.subTest(dynamic=dynamic):
                p = program(dynamic)
                self.assertEqual(3, len(xor.authenticate_scalar_uint_xor(p, SHA, xor.PROFILE)))
                self.assertEqual(1, len(ingress.authenticate_shapes_float_bits_ingress(
                    p, SHA, ingress.PROFILE)))
                self.assertEqual(1, len(rvalue.authenticate_shapes_rvalue_assign(
                    p, SHA, rvalue.PROFILE)))
                self.assertEqual(5, len(lane.authenticate_linear_srgb_lane_index(
                    p, SHA, lane.PROFILES[KEY])))
                generator.validate_capabilities(
                    p, generator.APPROVED_CAPABILITIES, source_hash=SHA, **PROFILES)
                emitted = render_typed_cpp(p, KEY, SHA, **PROFILES)
                self.assertIn('bind_typed', emitted)

    def test_runtime_forgeries_rejected(self):
        p = program(True)
        frozen = program(False)
        changed_function = dataclasses.replace(
            p.functions[0], signature=dataclasses.replace(
                p.functions[0].signature, name='forged'))
        variants = {
            'raw': dataclasses.replace(p, raw_source=p.raw_source + '\n'),
            'normalized': dataclasses.replace(p, source=p.source + '\n'),
            'function': dataclasses.replace(p, functions=(changed_function, *p.functions[1:])),
            'defines': dataclasses.replace(p, preprocessor_defines=frozen.preprocessor_defines),
        }
        for name, altered in variants.items():
            with self.subTest(forgery=name), self.assertRaises((ValueError, generator.GeneratorError)):
                generator.validate_capabilities(
                    altered, generator.APPROVED_CAPABILITIES, source_hash=SHA, **PROFILES)
        with self.assertRaises((ValueError, generator.GeneratorError)):
            generator.validate_capabilities(
                p, generator.APPROVED_CAPABILITIES,
                source_hash='0' * 64, **PROFILES)


if __name__ == '__main__':
    unittest.main()
