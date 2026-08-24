from __future__ import annotations

import hashlib
import pathlib
import unittest
import dataclasses
import copy
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import dither_frontend_profile as dither
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = dither.KEY
SOURCE = ROOT / (
    "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/"
    "sources/filter/dither/dither.glsl"
)


def _program():
    source = SOURCE.read_text(encoding="utf-8")
    return analyze_program(parse_program(source, KEY, generate_typed_slice._defaults(ROOT, KEY)), KEY)


class DitherEmitterLoweringTests(unittest.TestCase):
    def test_emits_authenticated_dither_lane_and_runtime_abi(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        rendered = emit_typed_cpp.render_typed_cpp(
            _program(), KEY, source_hash,
            dither_frontend_profile=dither.PROFILE)
        self.assertIn("std::array<glsl::Vec3, 18> errRow", rendered)
        self.assertIn("glsl::detail::js_to_int32", rendered)
        self.assertIn("sample_nearest_bottom_left", rendered)
        self.assertIn("texel_fetch_bottom_left", rendered)
        self.assertIn("bindings.get<glsl::Vec2>(\"tileOffset\")", rendered)
        self.assertIn("bindings.get<std::int32_t>(\"ditherType\")", rendered)
        self.assertIn("bindings.get_number(\"threshold\")", rendered)
        self.assertIn("ditherWithPalette", rendered)
        self.assertIn("F49", rendered)

    def test_dither_requires_exact_profile_carrier(self):
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                _program(), KEY,
                hashlib.sha256(SOURCE.read_bytes()).hexdigest())

    def test_source_exact_f32_pattern_carriers_and_diffusion_slot_selection(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        rendered = emit_typed_cpp.render_typed_cpp(
            _program(), KEY, source_hash,
            dither_frontend_profile=dither.PROFILE)
        self.assertIn("const glsl::Vec2 p =", rendered)
        self.assertIn("glsl::smoothstep(0.5, 0.0", rendered)
        self.assertIn("const glsl::Vec2 hashCoord", rendered)
        self.assertIn("std::floor(static_cast<double>(scaledCoord[0]))", rendered)
        self.assertIn("if (local[0] == 1)", rendered)
        self.assertNotIn("incomingIndex = 12 + local[0]", rendered)

    def test_foreign_proof_carriers_fail_closed(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        for kwargs in (
            {"testpattern_frontend_proof": object()},
            {"remap_frontend_proof": object()},
            {"testpattern_frontend_proof": object(), "remap_frontend_proof": object()},
        ):
            with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    _program(), KEY, source_hash,
                    dither_frontend_profile=dither.PROFILE, **kwargs)

    def test_forged_live_proof_is_rejected_before_emission(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        program = _program()
        real = dither.authenticate_dither_frontend(
            program, source_hash, dither.PROFILE)
        forged = dataclasses.replace(
            real,
            conversion_records=tuple(object() for _ in range(30)),
            pcg_order_records=(), f32_materialization_records=(),
            parameter_copy_records=(), loop_records=(), array_records=(),
            index_records=(), bitwise_records=())
        with mock.patch.object(emit_typed_cpp, "authenticate_dither_frontend", return_value=forged):
            with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, source_hash,
                    dither_frontend_profile=dither.PROFILE)

    def test_pcg_source_record_mapping_is_explicit_and_ordered(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        rendered = emit_typed_cpp.render_typed_cpp(
            _program(), KEY, source_hash,
            dither_frontend_profile=dither.PROFILE)
        self.assertIn("P01 source=pcg:151", rendered)
        self.assertIn("P05 source=pcg:155", rendered)
        self.assertLess(rendered.index("P01 source=pcg:151"),
                        rendered.index("P08 source=pcg:158"))

    def test_emission_consumer_rejects_deleted_or_reordered_pcg_operation(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        program = _program()
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash, dither_frontend_profile=dither.PROFILE)
        proof = emit_typed_cpp.authenticate_dither_frontend(
            program, source_hash, dither.PROFILE)
        deleted = rendered.replace(
            "// P03 source=pcg:153\n  v[1] += dither_imul(v[2], v[0]);\n", "", 1)
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp._finalize_dither_emission(proof, program, deleted)
        p02 = "// P02 source=pcg:152\n  v[0] += dither_imul(v[1], v[2]);\n"
        p03 = "  // P03 source=pcg:153\n  v[1] += dither_imul(v[2], v[0]);\n"
        reordered = rendered.replace("  " + p02 + p03, p03 + "  " + p02, 1)
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp._finalize_dither_emission(proof, program, reordered)
        duplicated = rendered.replace(p02, p02 + p02, 1)
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp._finalize_dither_emission(proof, program, duplicated)

    def test_emission_consumer_rejects_deleted_or_reordered_conversion(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        program = _program()
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash, dither_frontend_profile=dither.PROFILE)
        proof = emit_typed_cpp.authenticate_dither_frontend(
            program, source_hash, dither.PROFILE)
        c01 = "const std::int32_t x = dither_i32"
        c02 = "const std::int32_t y = dither_i32"
        deleted = rendered.replace(c01, "", 1)
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp._finalize_dither_emission(proof, program, deleted)
        reordered = rendered.replace(c01, "__C01__", 1).replace(
            c02, c01, 1).replace("__C01__", c02, 1)
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp._finalize_dither_emission(proof, program, reordered)

    def test_emission_consumer_rejects_shallow_copied_proof_carrier(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        program = _program()
        real = dither.authenticate_dither_frontend(
            program, source_hash, dither.PROFILE)
        shallow = copy.copy(real)
        with mock.patch.object(emit_typed_cpp, "authenticate_dither_frontend",
                               return_value=shallow):
            with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, source_hash,
                    dither_frontend_profile=dither.PROFILE)

    def test_emission_consumer_rejects_non_pcg_body_mutations(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        program = _program()
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash, dither_frontend_profile=dither.PROFILE)
        proof = emit_typed_cpp.authenticate_dither_frontend(
            program, source_hash, dither.PROFILE)
        mutations = (
            rendered.replace(
                "const glsl::Vec2 c(noisemaker::f32(std::floor(static_cast<double>(p[0])) + 0.5), noisemaker::f32(std::floor(static_cast<double>(p[1])) + 0.5)); (void)c;",
                "", 1),
            rendered.replace(
                "errRow[static_cast<std::size_t>(i)] = glsl::Vec3(noisemaker::f32(static_cast<double>(seed[0]) * stepScale), noisemaker::f32(static_cast<double>(seed[1]) * stepScale), noisemaker::f32(static_cast<double>(seed[2]) * stepScale));",
                "", 1),
            rendered.replace(
                "  output = glsl::Vec4(mixed[0], mixed[1], mixed[2], color4[3]);  // F48; F49 writeColor f32 return\n",
                "  output = glsl::Vec4(mixed[0], mixed[1], mixed[2], color4[3]);  // F48; F49 writeColor f32 return\n" * 2,
                1),
        )
        for mutated in mutations:
            with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp._finalize_dither_emission(proof, program, mutated)

    def test_emission_consumer_rejects_deleted_pcg_scalar_expansions(self):
        source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        program = _program()
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, source_hash, dither_frontend_profile=dither.PROFILE)
        proof = emit_typed_cpp.authenticate_dither_frontend(
            program, source_hash, dither.PROFILE)
        mutations = (
            rendered.replace(
                "  v[1] = dither_imul(v[1], 1664525U) + 1013904223U;\n", "", 1),
            rendered.replace(
                "  v[2] ^= v[2] >> 16U;\n", "", 1),
        )
        for mutated in mutations:
            with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp._finalize_dither_emission(proof, program, mutated)


if __name__ == "__main__":
    unittest.main()
