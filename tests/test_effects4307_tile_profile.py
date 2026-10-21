"""Exact current Effects tile budget and source admission tests."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import unittest
from pathlib import Path

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
    attach_fixed_array_in_parameter_proof, source_provenance_error)
from tools.glslcpp.frontend.dynamic_kernel9_profile import prove
from tools.glslcpp.frontend.mutable_global_array_profile import (
    EFFECTS_PROFILE, authenticate_mutable_global_array)
from tools.glslcpp.frontend.effects_zoomblur_local_array_profile import (
    authenticate_zoomblur_local_array)
from tools.glslcpp.emit_typed_cpp import render_typed_cpp

ROOT = Path(__file__).resolve().parents[1]
KEY = 'classicNoisedeck/effects:effects'
CORPUS = ROOT / f'tools/glslcpp/corpus/{CORPUS_REVISION}'
SOURCE = CORPUS / 'sources/classicNoisedeck/effects/effects.glsl'
SHA = 'b4f4279698ce60bd3c0c45f8339a4869cd6c2f0714f219ee6b2e997328057316'


def candidate(raw: str):
    parsed = parse_program(transform_source(raw, KEY), KEY,
                           {'EFFECT': 'int', 'FLIP': 'int'})
    parsed['raw_source'] = raw
    return analyze_program(parsed, KEY)


class Effects4307TileProfileTests(unittest.TestCase):
    def test_exact_current_source_proofs_and_emission(self):
        raw = SOURCE.read_text()
        self.assertEqual(SHA, hashlib.sha256(raw.encode()).hexdigest())
        program = candidate(raw)
        self.assertIsNone(source_provenance_error(program, SHA))
        self.assertIsNotNone(prove(program))
        self.assertEqual(7, len(authenticate_mutable_global_array(
            program, SHA, EFFECTS_PROFILE)))
        self.assertIsNotNone(authenticate_zoomblur_local_array(program, SHA))
        attached = attach_fixed_array_in_parameter_proof(program)
        row = next(item for item in json.loads(
            (ROOT / 'tools/glslcpp/typed_slice.json').read_text())['programs']
            if item['program_key'] == KEY)
        rendered = render_typed_cpp(
            attached, KEY, SHA,
            mutable_global_array_profile=row['mutable_global_array_profile'],
            glitch_mat4_chain_profile=row['glitch_mat4_chain_profile'],
            ceil_admission_profile=row['ceil_admission_profile'])
        self.assertEqual(1, rendered.count(
            'tapBudget = (glsl::FloatExpr<2>(static_cast<float>(256.0)) * '
            'state.invFullResolution);'))
        self.assertEqual(1, rendered.count(
            'tapB = glsl::Vec2(glsl::component_min(glsl::component_max('
            'tapB, (-tapBudget)), tapBudget));'))
        self.assertIn('(((st + tapB) * state.fullResolution) - state.tileOffset)',
                      rendered)

    def test_forged_source_caller_and_tree_are_rejected(self):
        raw = SOURCE.read_text()
        program = candidate(raw)
        self.assertIsNotNone(source_provenance_error(program, '0' * 64))
        mutated_source = raw.replace('vec2(256.0) * invFullResolution',
                                     'vec2(257.0) * invFullResolution', 1)
        self.assertNotEqual(mutated_source, raw)
        altered = candidate(mutated_source)
        self.assertIsNotNone(source_provenance_error(
            altered, hashlib.sha256(mutated_source.encode()).hexdigest()))
        zoom = next(f for f in program.functions if f.name == 'zoomBlur')
        loop = zoom.body[5]
        block = loop.children[1]
        branch = block.children[7]
        condition = dataclasses.replace(branch.expressions[0], operator='&&')
        forged_branch = dataclasses.replace(branch, expressions=(condition,))
        forged_block = dataclasses.replace(
            block, children=block.children[:7] + (forged_branch,) + block.children[8:])
        forged_loop = dataclasses.replace(
            loop, children=(loop.children[0], forged_block))
        forged_zoom = dataclasses.replace(
            zoom, body=zoom.body[:5] + (forged_loop,) + zoom.body[6:])
        forged = dataclasses.replace(program, functions=tuple(
            forged_zoom if f is zoom else f for f in program.functions))
        self.assertIsNone(prove(forged))
        with self.assertRaises(ValueError):
            authenticate_mutable_global_array(forged, SHA, EFFECTS_PROFILE)


if __name__ == '__main__':
    unittest.main()
