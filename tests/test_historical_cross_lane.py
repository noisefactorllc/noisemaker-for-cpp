"""Tests for the explicit legacy Gradient reconstruction gate."""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice, regen_cache
from tools.glslcpp import check_corpus
from tests import corpus_census
from tests.historical_authority import historical_authority
from tools.glslcpp.frontend import (
    moodscape_frontend_profile, noise_frontend_profile, parse_program,
    texture_frontend_profile)
from tools.glslcpp.frontend.semantic import analyze_program
from tests.gate import full_run_only

from tests.historical_cross_lane import (
    CROSS_LANE_KEY,
    CROSS_LANE_PROFILE,
    historical_cross_lane,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]


class HistoricalCrossLaneTests(unittest.TestCase):
    def _spec(self) -> dict[str, object]:
        return corpus_census.without_expansion(generate_typed_slice.load_slice(ROOT))

    def _gradient_row(self, spec: dict[str, object]) -> dict[str, object]:
        rows = [row for row in spec["programs"]
                if row.get("program_key") == CROSS_LANE_KEY]
        self.assertEqual(1, len(rows))
        return rows[0]

    @full_run_only
    def test_legacy_projection_emits_exact_generic_assignment_and_no_carrier(self) -> None:
        spec = self._spec()
        with historical_cross_lane(spec):
            self.assertNotIn(
                "cross_lane_assignment_profile", self._gradient_row(spec))
            with mock.patch.object(generate_typed_slice, "load_slice",
                                   return_value=spec):
                outputs = generate_typed_slice.generate_outputs(ROOT)

        cpp = outputs["src/typed_generated/typed_slice.cpp"].decode()
        gradient = cpp[cpp.index("// Typed IR program: synth/gradient:gradient"):]
        self.assertIn(
            "rotatedCentered = glsl::Vec2((glsl::Mat2(glsl::Vec2(c, (-s)), "
            "glsl::Vec2(s, c)) * centered));",
            gradient)
        self.assertNotIn("set_swizzle<0>(rotatedCentered", gradient)
        manifest = json.loads(
            outputs["src/typed_generated/typed_manifest.json"])
        row = next(item for item in manifest["programs"]
                   if item["program_key"] == CROSS_LANE_KEY)
        self.assertNotIn("cross_lane_assignment_profile", row)

    def test_carrier_is_restored_after_success_and_exception(self) -> None:
        spec = self._spec()
        row = self._gradient_row(spec)
        self.assertEqual(CROSS_LANE_PROFILE,
                         row["cross_lane_assignment_profile"])
        with historical_cross_lane(spec):
            self.assertNotIn("cross_lane_assignment_profile", row)
        self.assertEqual(CROSS_LANE_PROFILE,
                         row["cross_lane_assignment_profile"])
        with self.assertRaisesRegex(RuntimeError, "sentinel failure"):
            with historical_cross_lane(spec):
                raise RuntimeError("sentinel failure")
        self.assertEqual(CROSS_LANE_PROFILE,
                         row["cross_lane_assignment_profile"])

    def test_missing_wrong_and_duplicate_gradient_carriers_fail_closed(self) -> None:
        missing = self._spec()
        del self._gradient_row(missing)["cross_lane_assignment_profile"]
        with self.assertRaisesRegex(ValueError, "exact carrier"):
            with historical_cross_lane(missing):
                pass

        wrong = self._spec()
        self._gradient_row(wrong)["cross_lane_assignment_profile"] = "wrong"
        with self.assertRaisesRegex(ValueError, "exact carrier"):
            with historical_cross_lane(wrong):
                pass

        duplicate = self._spec()
        duplicate["programs"].append(copy.deepcopy(self._gradient_row(duplicate)))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            with historical_cross_lane(duplicate):
                pass

    def test_live_census_and_historical_membership_are_separate(self) -> None:
        live = generate_typed_slice.load_slice(ROOT)
        historical = corpus_census.without_expansion(live)
        self.assertEqual(corpus_census.typed_keys(),
                         [row['program_key'] for row in live['programs']])
        self.assertEqual(corpus_census.HISTORICAL_REVISION, historical['revision'])
        keys = [row['program_key'] for row in historical['programs']]
        self.assertEqual(corpus_census.PRE_EXPANSION_TYPED_KEY_SHA256,
                         hashlib.sha256(('\n'.join(keys) + '\n').encode()).hexdigest())
        for key in ('filter/bc:bc', 'filter/colorspace:colorspace', 'filter/hs:hs'):
            self.assertIn(key, keys)
            self.assertNotIn(key, corpus_census.typed_keys())
        for key in ('render/meshLoader:preview', 'render/meshRender:clear', 'synth/roll:copy'):
            self.assertIn(key, corpus_census.typed_keys())
            self.assertNotIn(key, keys)
        damaged = copy.deepcopy(live)
        damaged['programs'] = [row for row in damaged['programs']
                               if row['program_key'] != CROSS_LANE_KEY]
        with self.assertRaisesRegex(AssertionError, 'projection drift'):
            corpus_census.without_expansion(damaged)
        foreign = copy.deepcopy(live)
        foreign['programs'].append({'program_key': 'foreign:key', 'defines': {}})
        with self.assertRaisesRegex(AssertionError, 'unknown authority keys'):
            corpus_census.without_expansion(foreign)

    def test_historical_authority_restores_live_context_after_exception(self) -> None:
        revision = check_corpus.REVISION
        root = check_corpus._corpus_root(ROOT)
        noise_hash = noise_frontend_profile.RAW_SHA256
        authenticate = generate_typed_slice.authenticate_glitch_mat4_chain
        with self.assertRaisesRegex(RuntimeError, 'sentinel failure'):
            with historical_authority(self._spec()):
                self.assertEqual(corpus_census.HISTORICAL_CORPUS, check_corpus._corpus_root(ROOT))
                self.assertNotEqual(noise_hash, noise_frontend_profile.RAW_SHA256)
                self.assertIsNot(authenticate, generate_typed_slice.authenticate_glitch_mat4_chain)
                raise RuntimeError('sentinel failure')
        self.assertEqual(revision, check_corpus.REVISION)
        self.assertEqual(root, check_corpus._corpus_root(ROOT))
        self.assertEqual(noise_hash, noise_frontend_profile.RAW_SHA256)
        self.assertIs(authenticate, generate_typed_slice.authenticate_glitch_mat4_chain)
        with self.assertRaisesRegex(ValueError, 'explicit historical slice'):
            with historical_authority(generate_typed_slice.load_slice(ROOT)):
                pass

    def test_historical_profiles_authenticate_old_sources_and_reject_forgery(self) -> None:
        with historical_authority(self._spec()):
            for key, profile, authenticate in (
                    ('classicNoisedeck/glitch:glitch', 'glitch-mat4-chain-v1',
                     generate_typed_slice.authenticate_glitch_mat4_chain),
                    (noise_frontend_profile.KEY, noise_frontend_profile.PROFILE,
                     noise_frontend_profile.authenticate_noise_frontend)):
                effect, filename = key.split(':')
                raw = (check_corpus._corpus_root(ROOT) / 'sources' / effect / (filename + '.glsl')).read_text()
                program = analyze_program(parse_program(
                    raw, key, generate_typed_slice._defaults(ROOT, key)), key)
                source_hash = hashlib.sha256(raw.encode()).hexdigest()
                authenticate(program, source_hash, profile)
                with self.assertRaises(ValueError):
                    authenticate(dataclasses.replace(program, raw_source=raw + '\n'),
                                 source_hash, profile)

    def test_classic_noise_current_and_historical_single_program_projection(self) -> None:
        key = noise_frontend_profile.KEY
        live = generate_typed_slice.load_slice(ROOT)
        current = next(row for row in live['programs'] if row['program_key'] == key)
        self.assertEqual('runtime-defines-generic-v1', current['runtime_define_profile'])
        damaged = copy.deepcopy(live)
        next(row for row in damaged['programs'] if row['program_key'] == key).pop(
            'runtime_define_profile')
        with self.assertRaisesRegex(AssertionError, 'runtime carrier census drift'):
            corpus_census.without_expansion(damaged)
        source_path = 'sources/classicNoisedeck/noise/noise.glsl'
        raw = (check_corpus._corpus_root(ROOT) / source_path).read_text()
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        self.assertEqual(noise_frontend_profile.RAW_SHA256, source_hash)
        transformed = generate_typed_slice.transform_generic_dynamic_source(raw, key)
        parsed = parse_program(
            transformed, key, generate_typed_slice.GENERIC_DYNAMIC_DEFINE_TYPES[key])
        parsed['raw_source'] = raw
        current_program = analyze_program(parsed, key)
        current_projected = noise_frontend_profile.apply_noise_frontend(
            current_program, source_hash, current['noise_frontend_profile'])
        noise_frontend_profile.authenticate_noise_projection(
            current_projected, source_hash, current['noise_frontend_profile'])

        historical = corpus_census.without_expansion(live)
        frozen = next(row for row in historical['programs'] if row['program_key'] == key)
        self.assertNotIn('runtime_define_profile', frozen)
        with historical_authority(historical):
            entry = next(row for row in corpus_census.historical_document('manifest.json')['programs']
                         if row['program_key'] == key)
            self.assertEqual(source_path, entry['source'])
            raw = (check_corpus._corpus_root(ROOT) / entry['source']).read_text()
            source_hash = hashlib.sha256(raw.encode()).hexdigest()
            self.assertEqual(entry['raw_sha256'], source_hash)
            frozen_program = analyze_program(parse_program(raw, key, frozen['defines']), key)
            frozen_projected = noise_frontend_profile.apply_noise_frontend(
                frozen_program, source_hash, frozen['noise_frontend_profile'])
            noise_frontend_profile.authenticate_noise_projection(
                frozen_projected, source_hash, frozen['noise_frontend_profile'])

    def test_moodscape_and_texture_restore_frozen_single_program_contracts(self) -> None:
        live = generate_typed_slice.load_slice(ROOT)
        historical = corpus_census.without_expansion(live)
        cases = (
            (moodscape_frontend_profile.KEY, 'moodscape_frontend_profile',
             'moodscape-runtime-frontend-v1', moodscape_frontend_profile.PROFILE),
            (texture_frontend_profile.KEY, 'texture_frontend_profile',
             texture_frontend_profile.PROFILE, texture_frontend_profile.PROFILE),
        )
        for key, field, current_profile, frozen_profile in cases:
            with self.subTest(key=key):
                current = next(row for row in live['programs'] if row['program_key'] == key)
                frozen = next(row for row in historical['programs'] if row['program_key'] == key)
                self.assertEqual('runtime-defines-generic-v1', current['runtime_define_profile'])
                self.assertEqual(current_profile, current[field])
                self.assertNotIn('runtime_define_profile', frozen)
                self.assertEqual(frozen_profile, frozen[field])
                damaged = copy.deepcopy(live)
                next(row for row in damaged['programs'] if row['program_key'] == key).pop(
                    'runtime_define_profile')
                with self.assertRaisesRegex(AssertionError, 'runtime carrier census drift'):
                    corpus_census.without_expansion(damaged)
                if key == moodscape_frontend_profile.KEY:
                    damaged = copy.deepcopy(live)
                    next(row for row in damaged['programs'] if row['program_key'] == key)[
                        field] = 'wrong-profile'
                    with self.assertRaisesRegex(AssertionError,
                                                'Moodscape frontend carrier identity drift'):
                        corpus_census.without_expansion(damaged)
                with historical_authority(historical):
                    entry = next(row for row in corpus_census.historical_document(
                        'manifest.json')['programs'] if row['program_key'] == key)
                    raw = (check_corpus._corpus_root(ROOT) / entry['source']).read_text()
                    source_hash = hashlib.sha256(raw.encode()).hexdigest()
                    self.assertEqual(entry['raw_sha256'], source_hash)
                    program = analyze_program(parse_program(raw, key, frozen['defines']), key)
                    self.assertEqual(entry['normalized_sha256'],
                                     hashlib.sha256(program.source.encode()).hexdigest())
                    if key == moodscape_frontend_profile.KEY:
                        projected = moodscape_frontend_profile.apply_moodscape_frontend(
                            program, source_hash, frozen[field])
                        moodscape_frontend_profile.authenticate_moodscape_projection(
                            projected, source_hash, frozen[field])
                    else:
                        texture_frontend_profile.apply_texture_frontend(
                            program, source_hash, frozen[field])

    def test_historical_effects_retains_authenticated_zoomblur_helper(self) -> None:
        from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
            attach_fixed_array_in_parameter_proof)

        spec = self._spec()
        key = "classicNoisedeck/effects:effects"
        row = next(item for item in spec["programs"] if item["program_key"] == key)
        original = emit_typed_cpp.authenticated_effects_emission_omission
        with historical_authority(spec):
            entry = next(item for item in corpus_census.historical_document(
                "manifest.json")["programs"] if item["program_key"] == key)
            raw = (check_corpus._corpus_root(ROOT) / entry["source"]).read_text()
            source_hash = hashlib.sha256(raw.encode()).hexdigest()
            self.assertEqual(entry["raw_sha256"], source_hash)
            program = attach_fixed_array_in_parameter_proof(analyze_program(
                parse_program(raw, key, row["defines"]), key))
            profiles = {name: value for name, value in row.items()
                        if name.endswith("_profile")}
            body = emit_typed_cpp.render_typed_cpp(program, key, source_hash, **profiles)
            self.assertEqual(2, body.count("glsl::Vec3 zoomBlur("))
            with self.assertRaises(ValueError):
                emit_typed_cpp.authenticated_effects_emission_omission(
                    program, "0" * 64, row["mutable_global_array_profile"])
        self.assertIs(original, emit_typed_cpp.authenticated_effects_emission_omission)

    def test_historical_documents_and_verifier_reject_byte_drift(self) -> None:
        original = pathlib.Path.read_bytes

        def changed(path):
            raw = original(path)
            return raw + b'\n' if path.name == 'glitch_mat4_chain_profile.py' else raw

        with mock.patch.object(pathlib.Path, 'read_bytes', changed):
            with self.assertRaisesRegex(AssertionError, 'verifier source drift'):
                with historical_authority(self._spec()):
                    pass
        with mock.patch.object(pathlib.Path, 'read_bytes', return_value=b'{}'):
            with self.assertRaisesRegex(AssertionError, 'authority document drift'):
                corpus_census.historical_document('manifest.json')

    def test_historical_compatibility_preserves_original_identity_and_abi_checks(self) -> None:
        with historical_authority(self._spec()):
            rows = generate_typed_slice._compatibility_canonical_rows(ROOT)
            key = 'classicNoisedeck/glitch:glitch'
            raw_hash = '13d6350eb21cfb5a7c9f0d0a8fffe8e7495068ca2e082d1520ef14ca5b34c134'
            self.assertEqual(raw_hash, rows[key]['old_raw_sha256'])
            manifest = [{'program_key': key, 'source_sha256': raw_hash}]
            self.assertEqual({key: rows[key]['new_raw_sha256']},
                             generate_typed_slice._compatibility_source_hashes(ROOT, manifest))
            self.assertTrue(rows[key]['uniforms'])
            manifest[0]['source_sha256'] = '0' * 64
            with self.assertRaisesRegex(generate_typed_slice.GeneratorError, 'source identity mismatch'):
                generate_typed_slice._compatibility_source_hashes(ROOT, manifest)

    def test_historical_dictionary_extent_preserves_original_abi_digests(self) -> None:
        # Frozen from a15c4b6816a3cb4a1811a03429e4fbf84530c722, after reading
        # the original compatibility JSON. Dictionary-valued dimensions are
        # stringified by the ABI grammar, so their insertion order matters.
        with historical_authority(self._spec()):
            row = generate_typed_slice._compatibility_canonical_rows(ROOT)[
                'filter3d/flow3d:blend']
            self.assertEqual({
                'sampler_abi_sha256': '22ec34b7a1254fb28c9b3ad106bbb35341a384780b52e23bdb38cb58121e3af3',
                'uniform_abi_sha256': '7018fec1b16b60a298029ad0d129a2a4b075246436e8ffb87d5253a91334d54b',
                'output_abi_sha256': '4098fa3b3ee3a2471a85a8b43ee05ab248d03e4ad6bc9281862148587100a4b8',
                'output_extent_sha256': '3f260f4582b2ce78f85fdee3254c24d98de564e3f5b2e7645ab227a58d322b50',
                'compile_define_abi_sha256': '02fd423231499554cc6d031543c9bbd11752fc1fe72135d4c112f0bd3da43b7e',
            }, generate_typed_slice._binding_abi_sections(
                row, generate_typed_slice._custom_adapter_defines(row)))

    @full_run_only
    def test_regen_cache_detects_patched_collaborators_and_bypasses_io(self) -> None:
        spec = self._spec()
        temp_root = os.environ.get("TMPDIR")
        if not temp_root or not pathlib.Path(temp_root).is_dir():
            temp_root = tempfile.gettempdir()
        with tempfile.TemporaryDirectory(
                prefix="historical-cross-lane-cache-",
                dir=temp_root) as cache:
            old = os.environ.get(regen_cache._ENV_VAR)
            os.environ[regen_cache._ENV_VAR] = cache
            try:
                with historical_cross_lane(spec):
                    self.assertTrue(
                        regen_cache._collaborators_are_patched(
                            generate_typed_slice))
                    with mock.patch.object(generate_typed_slice, "load_slice",
                                           return_value=spec):
                        generate_typed_slice.generate_outputs(ROOT)
                self.assertEqual([], list(pathlib.Path(cache).rglob("index.json")))
            finally:
                if old is None:
                    os.environ.pop(regen_cache._ENV_VAR, None)
                else:
                    os.environ[regen_cache._ENV_VAR] = old


if __name__ == "__main__":
    unittest.main()
