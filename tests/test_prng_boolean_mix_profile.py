"""Source-bound admission for CPU PRNG boolean-mix sign folds."""

from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import prng_boolean_mix_select_profile as profile
from tools.glslcpp.frontend.noise_runtime_define_profile import transform_source
from tools.glslcpp.frontend.runtime_loop_bound_profile import apply_runtime_loop_bound


ROOT = Path(__file__).resolve().parents[1]


class PrngBooleanMixProfileTests(unittest.TestCase):
    def variants(self):
        for name, variants in (
                ('perlin', ({'DIMENSIONS': 2}, {'DIMENSIONS': 'int'})),
                ('noise', ({'LOOP_OFFSET': 300, 'NOISE_TYPE': 10},
                           {'NOISE_TYPE': 'int', 'LOOP_OFFSET': 'int'}))):
            key = f'synth/{name}:{name}'
            raw = (ROOT / f'tools/glslcpp/corpus/{REVISION}/sources/synth/{name}/{name}.glsl').read_text()
            for defines in variants:
                source = transform_source(raw, key) if name == 'noise' and defines['NOISE_TYPE'] == 'int' else raw
                parsed = parse_program(source, key, defines)
                parsed["raw_source"] = raw
                program = analyze_program(parsed, key)
                digest = hashlib.sha256(raw.encode()).hexdigest()
                if name == "noise" and defines["NOISE_TYPE"] == "int":
                    program = apply_runtime_loop_bound(program, digest, "runtime-loop-bound-v1")
                yield program, digest

    def test_default_and_runtime_nodes_are_owned(self):
        for program, digest in self.variants():
            with self.subTest(key=program.key, defines=program.preprocessor_defines):
                proof = profile.authenticate(program, digest, profile.PROFILE)
                self.assertEqual(len(proof.mix_nodes), 1)
                self.assertIs(proof.mix_nodes[0].children[2], proof.relationals[0])

    def test_wrong_source_define_tree_or_carrier_is_rejected(self):
        for program, digest in self.variants():
            for mutant in (replace(program, key='foreign:prng'),
                           replace(program, raw_source=program.raw_source + '\n'),
                           replace(program, source=program.source + '\n'),
                           replace(program, functions=program.functions[:-1]),
                           replace(program, preprocessor_defines=()),
                           replace(program, fixed_nine_table_proof=object())):
                with self.subTest(key=program.key), self.assertRaises(ValueError):
                    profile.authenticate(mutant, digest, profile.PROFILE)
            for source_hash, carrier in (('0' * 64, profile.PROFILE),
                                         (digest, None), (digest, 'wrong')):
                with self.assertRaises(ValueError):
                    profile.authenticate(program, source_hash, carrier)

    def test_changed_comparator_arms_and_duplicate_sites_are_rejected(self):
        for program, digest in self.variants():
            proof = profile.authenticate(program, digest, profile.PROFILE)
            mix = proof.mix_nodes[0]
            rel = proof.relationals[0]
            mutants = (
                replace(mix, children=(mix.children[1], mix.children[0], rel)),
                replace(mix, children=(*mix.children[:2], replace(rel, callee="lessThan"))),
                replace(mix, children=(*mix.children[:2], replace(rel, children=tuple(reversed(rel.children))))),
            )
            def substitute(node, target):
                if node is mix:
                    return target
                return replace(node, children=tuple(substitute(child, target) for child in node.children))
            for mutant in mutants:
                functions = tuple(replace(function, body=tuple(
                    replace(statement, expressions=tuple(substitute(expr, mutant)
                        for expr in statement.expressions))
                    for statement in function.body)) for function in program.functions)
                with self.assertRaises(ValueError):
                    profile.authenticate(replace(program, functions=functions), digest, profile.PROFILE)
            function = next(function for function in program.functions
                            if any(mix is node for statement in function.body
                                   for expr in statement.expressions for node in profile._walk(expr)))
            duplicate = replace(program, functions=program.functions + (function,))
            with self.assertRaises(ValueError):
                profile.authenticate(duplicate, digest, profile.PROFILE)

    def test_source_closures_preserve_historical_and_current_proofs(self):
        from tools.glslcpp.frontend import caustic_word_hash_profile as caustic
        from tools.glslcpp.frontend import linear_srgb_lane_index_profile as linear
        for revision in ('32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3', REVISION):
            for effect, name, defines, authenticate, carrier, expected in (
                    ('classicNoisedeck/caustic', 'caustic', {'NOISE_TYPE': 10},
                     caustic.authenticate_caustic_word_hash, caustic.PROFILE, 9),
                    ('classicNoisedeck/caustic', 'caustic', {'NOISE_TYPE': 'int'},
                     caustic.authenticate_caustic_word_hash, caustic.PROFILE, 9),
                    ('classicNoisedeck/cellNoise', 'cellNoise', {},
                     linear.authenticate_linear_srgb_lane_index, 'linear-srgb-cellnoise-lane-index-v1', 5)):
                raw = (ROOT / f'tools/glslcpp/corpus/{revision}/sources/{effect}/{name}.glsl').read_text()
                key = f'{effect}:{name}'
                program = analyze_program(parse_program(raw, key, defines), key)
                digest = hashlib.sha256(raw.encode()).hexdigest()
                proof = authenticate(program, digest, carrier)
                self.assertEqual(len(proof.consumed_objects if hasattr(proof, 'consumed_objects') else proof), expected)
                for mutant in (replace(program, raw_source=raw + '\n'),
                               replace(program, functions=program.functions[::-1]),
                               replace(program, fixed_nine_table_proof=object())):
                    with self.assertRaises(ValueError):
                        authenticate(mutant, digest, carrier)

    def test_moodscape_runtime_projection_is_source_bound(self):
        from tools.glslcpp.frontend import moodscape_dynamic_profile as moodscape
        for revision in ('32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3', REVISION):
            raw = (ROOT / f'tools/glslcpp/corpus/{revision}/sources/classicNoisedeck/moodscape/moodscape.glsl').read_text()
            program = analyze_program(parse_program(raw, moodscape.KEY,
                {'COLOR_MODE': 'int', 'NOISE_TYPE': 'int'}), moodscape.KEY)
            digest = hashlib.sha256(raw.encode()).hexdigest()
            projected, sites = moodscape.apply(program, digest, moodscape.PROFILE)
            self.assertEqual(tuple(f.id for f in projected.functions), moodscape.REACHABLE_IDS)
            self.assertEqual(len(sites.scalar_xors), 3)
            for mutant in (replace(program, raw_source=raw + '\n'),
                           replace(program, functions=program.functions[::-1]),
                           replace(program, preprocessor_defines=())):
                with self.assertRaises(ValueError):
                    moodscape.apply(mutant, digest, moodscape.PROFILE)
            with self.assertRaises(ValueError):
                moodscape.authenticate_projection(replace(projected, functions=projected.functions[:-1]), digest, moodscape.PROFILE)

    def test_classic_noise_runtime_projection_is_source_bound(self):
        from tools.glslcpp.frontend import noise_frontend_profile as noise
        from tools.glslcpp.frontend.dynamic_define_hoist import transform_source as hoist
        for revision in ('32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3', REVISION):
            raw = (ROOT / f'tools/glslcpp/corpus/{revision}/sources/classicNoisedeck/noise/noise.glsl').read_text()
            parsed = parse_program(hoist(raw, noise.KEY), noise.KEY,
                {name: 'int' for name, _, _ in noise._DYNAMIC_DEFINES})
            parsed['raw_source'] = raw
            program = analyze_program(parsed, noise.KEY)
            digest = hashlib.sha256(raw.encode()).hexdigest()
            projected = noise.apply_noise_frontend(program, digest, noise.PROFILE)
            self.assertEqual(tuple(f.signature.id for f in projected.functions), noise._DYNAMIC_REACHABLE_IDS)
            for mutant in (replace(program, raw_source=raw + '\n'),
                           replace(program, functions=program.functions[::-1]),
                           replace(program, preprocessor_defines=())):
                with self.assertRaises(ValueError):
                    noise.apply_noise_frontend(mutant, digest, noise.PROFILE)
            with self.assertRaises(ValueError):
                noise.authenticate_noise_projection(replace(projected, functions=projected.functions[:-1]), digest, noise.PROFILE)

    def test_every_admitted_current_source_variant_owns_its_mix(self):
        from tools.glslcpp.frontend import moodscape_dynamic_profile as moodscape
        from tools.glslcpp.frontend import noise_frontend_profile as classic_noise
        from tools.glslcpp.frontend.dynamic_define_hoist import transform_source as hoist
        from tools.glslcpp.frontend.noise_runtime_define_profile import DYNAMIC_DEFINES
        for key, canonical in profile._VARIANTS:
            effect, name = key.split(':')
            raw = (ROOT / f'tools/glslcpp/corpus/{REVISION}/sources/{effect}/{name}.glsl').read_text()
            defines = {name: int(value) if kind == 'int' else value for name, kind, value in canonical}
            source = raw
            if key == 'synth/noise:noise' and defines.get('NOISE_TYPE') == 'int':
                defines = DYNAMIC_DEFINES
                source = transform_source(raw, key)
            elif key == classic_noise.KEY:
                source = hoist(raw, key)
            parsed = parse_program(source, key, defines)
            parsed['raw_source'] = raw
            program = analyze_program(parsed, key)
            digest = hashlib.sha256(raw.encode()).hexdigest()
            if key == 'synth/noise:noise' and defines.get('NOISE_TYPE') == 'int':
                program = apply_runtime_loop_bound(program, digest, 'runtime-loop-bound-v1')
            elif key == moodscape.KEY:
                program = moodscape.apply(program, digest, moodscape.PROFILE)[0]
            elif key == classic_noise.KEY:
                program = classic_noise.apply_noise_frontend(program, digest, classic_noise.PROFILE)
            with self.subTest(key=key, defines=defines):
                proof = profile.authenticate(program, digest, profile.PROFILE)
                self.assertEqual(len(proof.mix_nodes), 1)
                self.assertIs(proof.mix_nodes[0].children[2], proof.relationals[0])
                with self.assertRaises(ValueError):
                    profile.authenticate(replace(program, functions=program.functions[::-1]), digest, profile.PROFILE)

    def test_corpus_probe_selects_the_companion_only_for_exact_source(self):
        import json
        from unittest import mock
        from tools.glslcpp import corpus_ratchet, generate_typed_slice
        key = 'classicNoisedeck/noise3d:noise3d'
        corpus = ROOT / f'tools/glslcpp/corpus/{REVISION}'
        raw = (corpus / 'sources/classicNoisedeck/noise3d/noise3d.glsl').read_bytes()
        effect = json.loads((corpus / 'metadata.json').read_text())['effects'][key.split(':')[0]]
        validator = generate_typed_slice.validate_capabilities
        for candidate, expected in ((raw, profile.PROFILE), (raw + b'\n', None)):
            with mock.patch.object(generate_typed_slice, 'validate_capabilities', wraps=validator) as validate:
                result = corpus_ratchet.probe_program(key, candidate, effect)
            self.assertEqual(validate.call_count, 1)
            self.assertEqual(validate.call_args.kwargs['prng_boolean_mix_select_profile'], expected)
            if expected:
                self.assertIsNone(result)
            else:
                self.assertIsNotNone(result)
                self.assertEqual(result['stage'], 'typed.validator')

    def test_noise3d_omits_only_prng_sites_in_authenticated_dead_functions(self):
        from tools.glslcpp import emit_typed_cpp, generate_typed_slice
        key = 'classicNoisedeck/noise3d:noise3d'
        raw = (ROOT / f'tools/glslcpp/corpus/{REVISION}/sources/classicNoisedeck/noise3d/noise3d.glsl').read_text()
        digest = hashlib.sha256(raw.encode()).hexdigest()
        for value, omitted in ((12, 2), ('int', 0)):
            program = analyze_program(parse_program(raw, key, {'NOISE_TYPE': value}), key)
            proof = profile.authenticate(program, digest, profile.PROFILE)
            self.assertEqual(len(proof.mix_nodes), 1)
            self.assertEqual(len(proof.relationals), 1)
            self.assertEqual(len(proof.omitted_nodes), omitted)
            self.assertEqual(len(proof.live_mix_nodes), 1 - omitted // 2)
            self.assertEqual(len(proof.live_relationals), 1 - omitted // 2)
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=digest, prng_boolean_mix_select_profile=profile.PROFILE)
            emit_typed_cpp.render_typed_cpp(
                program, key, digest, prng_boolean_mix_select_profile=profile.PROFILE)
            prng = next(function for function in program.functions if function.name == 'prng')
            changed = replace(program, functions=tuple(
                replace(function, body=()) if function is prng else function
                for function in program.functions))
            with self.assertRaisesRegex(ValueError, 'typed-tree fingerprint'):
                profile.authenticate(changed, digest, profile.PROFILE)
