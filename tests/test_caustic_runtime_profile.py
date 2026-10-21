from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.caustic_word_hash_profile import (
    PROFILE, CAUSTIC_KEY, authenticate_caustic_word_hash)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / f'tools/glslcpp/corpus/{CORPUS_REVISION}'
          / 'sources/classicNoisedeck/caustic/caustic.glsl')


def program(defines):
    raw = SOURCE.read_text()
    return analyze_program(parse_program(raw, CAUSTIC_KEY, defines), CAUSTIC_KEY)


class CausticRuntimeProfileTests(unittest.TestCase):
    def test_exact_default_and_dynamic_proofs(self):
        for defines in ({'NOISE_TYPE': 10}, {'NOISE_TYPE': 'int'}):
            with self.subTest(defines=defines):
                candidate = program(defines)
                digest = hashlib.sha256(candidate.raw_source.encode()).hexdigest()
                proof = authenticate_caustic_word_hash(candidate, digest, PROFILE)
                self.assertEqual(3, len(proof.word_xors))
                self.assertEqual('floatBitsToUint', proof.ingress.callee)
                self.assertEqual('randomFromLatticeWithOffset', proof.host.name)

    def test_dynamic_proof_rejects_wrong_source_tree_and_carrier(self):
        candidate = program({'NOISE_TYPE': 'int'})
        digest = hashlib.sha256(candidate.raw_source.encode()).hexdigest()
        variants = ((candidate, '0' * 64, PROFILE),
                    (replace(candidate, functions=candidate.functions[:-1]), digest, PROFILE),
                    (replace(candidate, source=candidate.source + '\n'), digest, PROFILE),
                    (candidate, digest, 'foreign-profile'))
        for entry in variants:
            with self.subTest(entry=entry[1:]):
                with self.assertRaises(ValueError):
                    authenticate_caustic_word_hash(*entry)


if __name__ == '__main__':
    unittest.main()
