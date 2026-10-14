from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import loop_proof

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d/sources'


def dynamic_program(key, relative, defines):
    raw = (CORPUS / relative).read_text()
    source = transform_source(raw, key) if any(isinstance(value, str)
                                                for value in defines.values()) else raw
    parsed = parse_program(source, key, defines)
    return replace(analyze_program(parsed, key), raw_source=raw)


class RuntimeProfilePatchTests(unittest.TestCase):
    def test_lowpoly_accepts_exact_dynamic_tree_and_returns_exact_nodes(self):
        from tools.glslcpp.frontend.lowpoly_runtime_profile import (
            PROFILE, authenticate_lowpoly_runtime)
        key = 'filter/lowPoly:lowPoly'
        program = dynamic_program(key, 'filter/lowPoly/lowPoly.glsl',
                                  {'LP_BORDER': 'int', 'LP_LIGHT': 'int'})
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        proof = authenticate_lowpoly_runtime(program, source_hash, PROFILE)
        self.assertEqual((1, 1, 1),
                         (len(proof.reductions), len(proof.relationals),
                          len(proof.derivatives)))
        self.assertEqual(('any', 'notEqual', 'fwidth'),
                         (proof.reductions[0].callee, proof.relationals[0].callee,
                          proof.derivatives[0].callee))
        self.assertIs(proof.nodes[0], proof.derivatives[0])

    def test_lowpoly_rejects_wrong_source_and_forged_tree(self):
        from tools.glslcpp.frontend.lowpoly_runtime_profile import (
            PROFILE, authenticate_lowpoly_runtime)
        key = 'filter/lowPoly:lowPoly'
        program = dynamic_program(key, 'filter/lowPoly/lowPoly.glsl',
                                  {'LP_BORDER': 'int', 'LP_LIGHT': 'int'})
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        with self.assertRaises(ValueError):
            authenticate_lowpoly_runtime(program, '0' * 64, PROFILE)
        with self.assertRaises(ValueError):
            authenticate_lowpoly_runtime(replace(program, functions=program.functions[:-1]),
                                         source_hash, PROFILE)
        with self.assertRaises(ValueError):
            authenticate_lowpoly_runtime(program, source_hash, 'foreign-profile')

    def test_strokes_dynamic_source_global_proof_preserves_default_proof(self):
        key = 'filter/strokes:stkSmear'
        default = dynamic_program(key, 'filter/strokes/stkSmear.glsl', {'MODE': 0})
        dynamic = dynamic_program(key, 'filter/strokes/stkSmear.glsl', {'MODE': 'int'})
        for program in (default, dynamic):
            attached, summary = loop_proof.rebuild_authenticated_counted_loop_proofs(
                program, loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
            proved = replace(program, functions=attached, counted_loop_proof=summary)
            loop_proof.validate_source_global_literal_int_program(
                proved, loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        self.assertEqual((3, 0, 24, 72),
                         (summary.loop_count, summary.unproved_loop_count,
                          summary.max_lexical_product, summary.entrypoint_charge))

    def test_production_runtime_validation_and_emission(self):
        from tools.glslcpp import generate_typed_slice as generator, emit_typed_cpp as emitter
        for key, path, defines in (
            ('filter/lowPoly:lowPoly', 'filter/lowPoly/lowPoly.glsl',
             {'LP_BORDER': 'int', 'LP_LIGHT': 'int'}),
            ('filter/strokes:stkSmear', 'filter/strokes/stkSmear.glsl', {'MODE': 'int'})):
            program = dynamic_program(key, path, defines)
            digest = hashlib.sha256(program.raw_source.encode()).hexdigest()
            options = {}
            if key == 'filter/strokes:stkSmear':
                functions, summary = loop_proof.rebuild_authenticated_counted_loop_proofs(
                    program, loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
                program = replace(program, functions=functions, counted_loop_proof=summary)
                options['source_global_literal_int_profile'] = loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
            generator.validate_capabilities(program, generator.APPROVED_CAPABILITIES,
                                            source_hash=digest, **options)
            emitted = emitter.render_typed_cpp(program, key, digest, 'test_runtime',
                                               'bind_test_runtime', **options)
            self.assertIn('glsl::degrees(' if options else 'glsl::BVec2(', emitted)
            with self.assertRaises(ValueError):
                generator.validate_capabilities(replace(program, raw_source=program.raw_source + '\n'),
                                                generator.APPROVED_CAPABILITIES,
                                                source_hash=digest, **options)

    def test_strokes_dynamic_source_global_proof_rejects_forgery(self):
        key = 'filter/strokes:stkSmear'
        program = dynamic_program(key, 'filter/strokes/stkSmear.glsl', {'MODE': 'int'})
        changed = replace(program, raw_source=program.raw_source.replace(
            'const int MAX_TAPS = 24;', 'const int MAX_TAPS = 25;'))
        with self.assertRaises(ValueError):
            loop_proof.rebuild_authenticated_counted_loop_proofs(
                changed, loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        changed_tree = replace(program, functions=program.functions[:-1])
        with self.assertRaises(ValueError):
            loop_proof.rebuild_authenticated_counted_loop_proofs(
                changed_tree, loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)


if __name__ == '__main__':
    unittest.main()
