"""Source-bound acceptance for the upstream PRNG sign-fold sync."""
from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import gabor_effective_depth_profile as gabor
from tools.glslcpp.frontend import noise3d_dead_globals as noise

ROOT = Path(__file__).resolve().parents[1] / 'tools/glslcpp/corpus'
REVISIONS = ('32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3',
             'd0ed94ae19cca7328bc7d6b28902712a0838e1a9')


def program(revision, key, defines):
    raw = (ROOT / revision / 'sources' / (key.replace(':', '/') + '.glsl')).read_text()
    return analyze_program(parse_program(raw, key, defines), key), hashlib.sha256(raw.encode()).hexdigest()


class SyncSourceProfilesTests(unittest.TestCase):
    def test_gabor_old_and_current_preserve_candidate_owned_loops(self):
        for revision in REVISIONS:
            with self.subTest(revision=revision):
                candidate, digest = program(revision, gabor.GABOR_KEY, {})
                proof = gabor.authenticate_gabor_effective_depth(candidate, digest, gabor.PROFILE)
                self.assertIs(proof.program_proof, candidate.counted_loop_proof)
                self.assertEqual(len(proof.loops), 4)
                self.assertIs(gabor.validate_gabor_effective_depth_contract(proof), proof)
                with self.assertRaises(ValueError):
                    gabor.validate_gabor_effective_depth_contract(replace(proof, loops=proof.loops[:-1]))

    def test_noise_old_and_current_default_and_runtime(self):
        for revision in REVISIONS:
            for define in (12, 'int'):
                with self.subTest(revision=revision, define=define):
                    candidate, digest = program(revision, noise.KEY, {'NOISE_TYPE': define})
                    proof = noise.authenticate_noise3d_dead_globals(candidate, digest)
                    self.assertEqual(tuple(x.symbol.name for x in proof.globals), ('myt', 'mys'))
                    self.assertEqual(len(proof.rounds), 2 if define == 'int' else 0)
                    self.assertEqual(len(proof.cellular_distances), 9 if define == 'int' else 0)

    def test_mutated_current_trees_and_cross_source_hashes_are_rejected(self):
        for key, defines, authenticate in (
            (gabor.GABOR_KEY, {}, lambda p, h: gabor.authenticate_gabor_effective_depth(p, h, gabor.PROFILE)),
            (noise.KEY, {'NOISE_TYPE': 12}, noise.authenticate_noise3d_dead_globals),
            (noise.KEY, {'NOISE_TYPE': 'int'}, noise.authenticate_noise3d_dead_globals),
        ):
            current, digest = program(REVISIONS[1], key, defines)
            _, old_digest = program(REVISIONS[0], key, defines)
            for mutant in (replace(current, raw_source=current.raw_source + '\n'),
                           replace(current, source=current.source + '\n'),
                           replace(current, functions=current.functions[:-1]),
                           replace(current, counted_loop_proof=replace(current.counted_loop_proof, entrypoint_charge=0))):
                with self.subTest(key=key, defines=defines), self.assertRaises(ValueError):
                    authenticate(mutant, digest)
            with self.assertRaises(ValueError):
                authenticate(current, old_digest)
            with self.assertRaises(ValueError):
                authenticate(current, '0' * 64)
