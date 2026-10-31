"""Exact-source admission across the PRNG boolean-mix sync."""
from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import corrupt_value_copy_profile as corrupt
from tools.glslcpp.frontend import derivative_admission_profile as derivative
from tools.glslcpp.frontend import cross_lane_assignment_profile as gradient

ROOT = Path(__file__).resolve().parents[1] / 'tools/glslcpp/corpus'
REVISIONS = ('32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3',
             'd0ed94ae19cca7328bc7d6b28902712a0838e1a9')
AUTHENTICATORS = {
    corrupt.KEY: (corrupt.authenticate_corrupt_value_copy, corrupt.PROFILE),
    'filter/lensWarp:lensWarp': (derivative.authenticate_derivative_admission, derivative.PROFILE),
    'filter/warp:warp': (derivative.authenticate_derivative_admission, derivative.PROFILE),
    gradient.CROSS_LANE_KEY: (gradient.authenticate_cross_lane_assignment, gradient.PROFILE),
}


def program(revision, key):
    raw = (ROOT / revision / 'sources' / (key.replace(':', '/') + '.glsl')).read_text()
    return analyze_program(parse_program(raw, key, {}), key), hashlib.sha256(raw.encode()).hexdigest()


class SyncCorruptDerivativeGradientProfilesTests(unittest.TestCase):
    def test_historical_and_current_proofs_preserve_semantics_and_node_identity(self):
        for revision in REVISIONS:
            for key, (authenticate, profile) in AUTHENTICATORS.items():
                with self.subTest(revision=revision, key=key):
                    candidate, digest = program(revision, key)
                    proof = authenticate(candidate, digest, profile)
                    if key == corrupt.KEY:
                        self.assertEqual((proof.symbol.name, proof.children[0].symbol.name), ('sampleUv', 'uv'))
                        self.assertTrue(any(proof is e for f in candidate.functions for s in f.body for e in s.expressions))
                    elif key == gradient.CROSS_LANE_KEY:
                        self.assertIs(proof._candidate, candidate)
                        self.assertEqual((proof.source_lanes, proof.destination_lanes), ((0, 1), (0, 1)))
                        self.assertEqual(proof.rhs_source.symbol.name, 'centered')
                        self.assertEqual(tuple(c.kind for c in proof.matrix.children), ('id', 'unary', 'id', 'id'))
                    else:
                        self.assertEqual(tuple(n.callee for n in proof.nodes), ('dFdx', 'dFdy'))
                        self.assertTrue(all(any(owner is f for f in candidate.functions) for owner in proof.owners))
                        self.assertTrue(all(n.children[0].symbol.name == 'uv' for n in proof.nodes))

    def test_sync_changes_only_prng_selection_and_preserves_proof_structure(self):
        old_selection = "\n".join(
            f"    p.{lane} = p.{lane} >= 0.0 ? p.{lane} * 2.0 : -p.{lane} * 2.0 + 1.0;"
            for lane in "xyz")
        new_selection = (
            "    // Select per component, like the WGSL select(): a software rasterizer\n"
            "    // builds each float ternary as a branch, and loops of them build for minutes.\n"
            "    p = mix(-p * 2.0 + 1.0, p * 2.0, greaterThanEqual(p, vec3(0.0)));"
        )

        def shape(node):
            return (node.kind, node.type.display(), node.category, node.operator,
                    node.callee, node.symbol_id, node.member,
                    tuple(shape(child) for child in node.children))

        for key, (authenticate, profile) in AUTHENTICATORS.items():
            old, old_digest = program(REVISIONS[0], key)
            current, digest = program(REVISIONS[1], key)
            with self.subTest(key=key):
                self.assertEqual(old.raw_source.count(old_selection), 1)
                self.assertEqual(old.raw_source.replace(old_selection, new_selection), current.raw_source)
                old_proof = authenticate(old, old_digest, profile)
                proof = authenticate(current, digest, profile)
                if key == corrupt.KEY:
                    self.assertEqual(shape(old_proof), shape(proof))
                elif key == gradient.CROSS_LANE_KEY:
                    for field in ('alias_declaration', 'assignment', 'target', 'target_source', 'rhs_source', 'matrix'):
                        self.assertEqual(shape(getattr(old_proof, field)), shape(getattr(proof, field)))
                else:
                    self.assertEqual(tuple(shape(n) for n in old_proof.nodes), tuple(shape(n) for n in proof.nodes))
                    self.assertEqual(tuple(tuple(s.kind for s in chain) for chain in old_proof.statement_parent_chains),
                                     tuple(tuple(s.kind for s in chain) for chain in proof.statement_parent_chains))

    def test_source_tree_and_carrier_forgery_fail_closed(self):
        for key, (authenticate, profile) in AUTHENTICATORS.items():
            candidate, digest = program(REVISIONS[1], key)
            _, old_digest = program(REVISIONS[0], key)
            mutants = (
                replace(candidate, raw_source=candidate.raw_source + '\n'),
                replace(candidate, source=candidate.source + '\n'),
                replace(candidate, functions=candidate.functions[:-1]),
                replace(candidate, resources=replace(candidate.resources, outputs=())),
                replace(candidate, key='forged:key'),
            )
            for mutant in mutants:
                with self.subTest(key=key), self.assertRaises(ValueError):
                    authenticate(mutant, digest, profile)
            for bad_digest, bad_profile in ((old_digest, profile), (digest, 'forged')):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    authenticate(candidate, bad_digest, bad_profile)
