from __future__ import annotations

import copy
import dataclasses
import hashlib
import os
import pathlib
import unittest
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.glyph_map_nonnegative_int_shift_profile import (
    PROFILE, authenticate_glyph_map_nonnegative_int_shift,
    authenticated_glyph_map_tile_sites,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE_ROOT = pathlib.Path(os.environ.get("NOISEMAKER_CPP_ROOT", ROOT))
KEY = "filter/glyphMap:glyphMap"
OLD = ROOT / "tools/glslcpp/corpus/a1a3fa2a84223dfc1f5ec2c7a54a6f4269139c15/sources/filter/glyphMap/glyphMap.glsl"
NEW = ROOT / "tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d/sources/filter/glyphMap/glyphMap.glsl"


def analyzed(path: pathlib.Path):
    raw = path.read_text(encoding="utf-8")
    return analyze_program(parse_program(raw, KEY, generate_typed_slice._defaults(LIVE_ROOT, KEY)), KEY)


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GlyphMapOriginTileTests(unittest.TestCase):
    def test_exact_old_and_new_source_admission(self):
        old = analyzed(OLD)
        new = analyzed(NEW)
        old_proof = authenticate_glyph_map_nonnegative_int_shift(old, digest(OLD), PROFILE)
        new_proof = authenticate_glyph_map_nonnegative_int_shift(new, digest(NEW), PROFILE)
        self.assertEqual((), old_proof.tile_sites)
        self.assertEqual(2, len(new_proof.tile_sites))
        self.assertIs(new_proof.tile_any.children[0], new_proof.tile_not_equal)
        self.assertEqual((3, 24), tuple(child.symbol_id for child in new_proof.tile_not_equal.children))
        for program, source_hash, count in ((old, digest(OLD), 0), (new, digest(NEW), 1)):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                glyph_map_nonnegative_int_shift_profile=PROFILE,
            )
            rendered = emit_typed_cpp.render_typed_cpp(
                program, KEY, source_hash, "glyph_probe", "bind_glyph_probe",
                glyph_map_nonnegative_int_shift_profile=PROFILE,
            )
            self.assertEqual(count, rendered.count("glsl::any(glsl::notEqual(state.fullResolution, resolution))"))
            self.assertEqual(1, rendered.count("glsl::detail::js_shift_right("))
            self.assertEqual(1, rendered.count("glsl::detail::js_bitwise_and("))

    def test_forged_origin_tile_proof_sites_fail_both_consumers(self):
        program = analyzed(NEW)
        source_hash = digest(NEW)
        proof = authenticate_glyph_map_nonnegative_int_shift(program, source_hash, PROFILE)
        for label, forged in (
            ("omitted", dataclasses.replace(proof, tile_any=None, tile_not_equal=None)),
            ("swapped", dataclasses.replace(
                proof, tile_any=proof.tile_not_equal,
                tile_not_equal=proof.tile_any)),
            ("copied", dataclasses.replace(
                proof, tile_any=copy.deepcopy(proof.tile_any))),
        ):
            with self.subTest(label=label, consumer="validator"), \
                 mock.patch.object(generate_typed_slice,
                                   "authenticate_glyph_map_nonnegative_int_shift",
                                   return_value=forged), \
                 self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    glyph_map_nonnegative_int_shift_profile=PROFILE,
                )
            with self.subTest(label=label, consumer="emitter"), \
                 mock.patch.object(emit_typed_cpp,
                                   "authenticate_glyph_map_nonnegative_int_shift",
                                   return_value=forged), \
                 self.assertRaises(emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, source_hash, "glyph_probe", "bind_glyph_probe",
                    glyph_map_nonnegative_int_shift_profile=PROFILE,
                )

    def test_frozen_historical_profile_without_tile_field_remains_valid(self):
        from tests.historical_authority import _glyph_profile
        frozen = _glyph_profile()
        historical_source = (LIVE_ROOT / "tools/glslcpp/corpus/0ed489ec46842bffba33ee2ec65a218b6dda51f5"
                             / "sources/filter/glyphMap/glyphMap.glsl")
        program = analyzed(historical_source)
        source_hash = "853c3c15f300cf56ba3c11d5613cb91bfcb14b8b2f1be6bb5193e71397fdcea1"
        proof = frozen.authenticate_glyph_map_nonnegative_int_shift(
            program, source_hash, PROFILE)
        self.assertFalse(hasattr(proof, "tile_sites"))
        self.assertEqual((), authenticated_glyph_map_tile_sites(proof, program, source_hash))
        with mock.patch.object(generate_typed_slice, "authenticate_glyph_map_nonnegative_int_shift",
                               frozen.authenticate_glyph_map_nonnegative_int_shift), \
             mock.patch.object(emit_typed_cpp, "authenticate_glyph_map_nonnegative_int_shift",
                               frozen.authenticate_glyph_map_nonnegative_int_shift):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                glyph_map_nonnegative_int_shift_profile=PROFILE,
            )
            rendered = emit_typed_cpp.render_typed_cpp(
                program, KEY, source_hash, "glyph_historical", "bind_glyph_historical",
                glyph_map_nonnegative_int_shift_profile=PROFILE,
            )
            self.assertNotIn("glsl::any(glsl::notEqual(", rendered)
        with self.assertRaises(ValueError):
            authenticated_glyph_map_tile_sites(proof, analyzed(NEW), digest(NEW))

    def test_origin_source_and_tree_forgeries_rejected(self):
        program = analyzed(NEW)
        source_hash = digest(NEW)
        cases = (
            (program, "0" * 64),
            (dataclasses.replace(program, key="filter/foreign:foreign"), source_hash),
            (dataclasses.replace(program, functions=program.functions[:-1]), source_hash),
            (dataclasses.replace(program, raw_source=program.raw_source.replace(
                "any(notEqual(fullResolution, resolution))", "length(tileOffset) > 0")), source_hash),
            (dataclasses.replace(program, source=program.source.replace(
                "any(notEqual(fullResolution, resolution))", "any(notEqual(resolution, fullResolution))")), source_hash),
        )
        for candidate, caller_hash in cases:
            with self.subTest(candidate=candidate.key, hash=caller_hash), self.assertRaises(ValueError):
                authenticate_glyph_map_nonnegative_int_shift(candidate, caller_hash, PROFILE)
        with self.assertRaises(ValueError):
            authenticate_glyph_map_nonnegative_int_shift(program, source_hash, None)
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
            )
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, source_hash, "glyph_probe", "bind_glyph_probe",
            )
