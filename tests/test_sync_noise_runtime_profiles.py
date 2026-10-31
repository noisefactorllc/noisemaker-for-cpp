"""Historical and current source identity for runtime synth/noise."""
from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import noise_runtime_define_profile as profile
from tools.glslcpp.frontend.runtime_loop_bound_profile import apply_runtime_loop_bound
from tools.glslcpp import emit_typed_cpp, generate_typed_slice

ROOT = Path(__file__).resolve().parents[1] / 'tools/glslcpp/corpus'
REVISIONS = ('32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3',
             'd0ed94ae19cca7328bc7d6b28902712a0838e1a9')


def candidate(revision):
    source = (ROOT / revision / 'sources/synth/noise/noise.glsl').read_text()
    parsed = parse_program(profile.transform_source(source), profile.KEY, profile.DYNAMIC_DEFINES)
    parsed['raw_source'] = source
    return analyze_program(parsed, profile.KEY), hashlib.sha256(source.encode()).hexdigest()


class SyncNoiseRuntimeProfilesTests(unittest.TestCase):
    def test_both_sources_authenticate_runtime_frame_and_scalar_xor(self):
        for revision in REVISIONS:
            with self.subTest(revision=revision):
                before, digest = candidate(revision)
                after = apply_runtime_loop_bound(before, digest, 'runtime-loop-bound-v1')
                self.assertEqual(len(profile.authenticate_frame(after, digest, 'mutable-global-frame-noise-v1')), 1)
                self.assertEqual(len(profile.authenticate_scalar_xor(after, digest, 'scalar-uint-xor-v1')), 3)
                self.assertEqual(len(profile.authenticate_noise_ingress(after, digest, 'scalar-uint-xor-v1')), 1)
                self.assertEqual(profile.dynamic_frame_contract(after).struct_name, 'Frame')

    def test_current_candidate_reaches_validator_and_emitter_with_required_companion(self):
        before, digest = candidate(REVISIONS[1])
        after = apply_runtime_loop_bound(before, digest, 'runtime-loop-bound-v1')
        kwargs = dict(runtime_loop_bound_profile='runtime-loop-bound-v1',
                      scalar_uint_xor_profile='scalar-uint-xor-v1',
                      mutable_global_frame_profile='mutable-global-frame-noise-v1',
                      prng_boolean_mix_select_profile='prng-boolean-mix-select-v1')
        generate_typed_slice.validate_capabilities(after, generate_typed_slice.APPROVED_CAPABILITIES,
                                                  source_hash=digest, **kwargs)
        emitted = emit_typed_cpp.render_typed_cpp(after, profile.KEY, digest, **kwargs)
        self.assertIn('bindings.get<std::int32_t>("NOISE_TYPE")', emitted)
        self.assertIn('bindings.get<std::int32_t>("LOOP_OFFSET")', emitted)
        self.assertIn('glsl::mix(', emitted)

    def test_cross_source_hash_and_tree_mutations_fail_at_identity_guard(self):
        current, digest = candidate(REVISIONS[1])
        _, historical_digest = candidate(REVISIONS[0])
        with self.assertRaisesRegex(ValueError, 'source or interface'):
            profile.authenticate_source(current, historical_digest)
        with self.assertRaisesRegex(ValueError, 'source or interface'):
            profile.transform_source(current.raw_source.replace('base = map', 'base = 1.0 + map', 1))
        after = apply_runtime_loop_bound(current, digest, 'runtime-loop-bound-v1')
        with self.assertRaisesRegex(ValueError, 'typed tree fingerprint'):
            profile.authenticate_scalar_xor(replace(after, functions=tuple(reversed(after.functions))),
                                            digest, 'scalar-uint-xor-v1')
        with self.assertRaisesRegex(ValueError, 'source or interface'):
            profile.authenticate_frame(replace(after, source=after.source + '\n'), digest,
                                       'mutable-global-frame-noise-v1')
