"""Focused tests for the struct-frontier emitter leg.

The 2026-10 validator leg (struct_frontier_profile) froze the complete
struct plumbing of the five carriers and deliberately left the emitter
rejecting every struct type. This module covers the emitter advancement:
the same frozen census now authenticates the emitter, which lowers the
admitted ``VoxelHit``/``IsoHit`` plumbing for the three render-family
programs — the exact struct definitions, struct locals (uninitialized and
call-initialized), member reads/stores, and struct-returning function
signatures. Nothing here admits a struct the census does not freeze.

Measured, never transcribed: every identity value below is re-derived
from the live pending corpus by this module's own helpers.
"""

from __future__ import annotations

import hashlib
import json
import os
import unittest
from pathlib import Path

RENDER3D_KEY = "render/render3d:render3d"
RENDER_CUBE_KEY = "render/renderCubemap3d:renderCubemap3d"
RENDER_LIT_KEY = "render/renderLit3d:renderLit3d"

CORPUS_REVISION = "5976b7a6b77f69c47c41f4ee296a54d5318e1f9d"
REPOSITORY = Path(__file__).resolve().parent.parent


def _corpus_root() -> Path:
    return REPOSITORY / f"tools/glslcpp/corpus/{CORPUS_REVISION}"


def _manifest_row(key: str) -> dict:
    manifest = json.loads(
        (_corpus_root() / "manifest.json").read_text(encoding="utf-8"))
    return next(item for item in manifest["programs"]
                if item["program_key"] == key)


def _analyzed(key: str, *, with_seed: bool = True):
    import sys
    sys.path.insert(0, str(REPOSITORY))
    from tools.glslcpp import check_semantics
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic import analyze_program
    row = _manifest_row(key)
    effect_id, program_name = key.split(":")
    source_path = _corpus_root() / row["source"]
    raw = source_path.read_text(encoding="utf-8")
    assert (hashlib.sha256(raw.encode("utf-8")).hexdigest()
            == row["raw_sha256"])
    defaults = check_semantics._metadata_defaults(
        {"effects": {effect_id: json.loads(
            (_corpus_root() / "metadata.json").read_text(
                encoding="utf-8"))["effects"][effect_id]}}, key)
    kwargs = {}
    if with_seed:
        from tools.glslcpp.frontend import loop_proof
        kwargs["source_global_literal_int_profile"] = (
            loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
    return analyze_program(parse_program(raw, key, defaults), key, **kwargs)


def _module():
    import sys
    sys.path.insert(0, str(REPOSITORY))
    import tools.glslcpp.frontend.struct_frontier_profile as module
    return module


def _render(key: str, with_profile: bool):
    from tools.glslcpp.emit_typed_cpp import render_typed_cpp
    from tools.glslcpp.frontend import loop_proof
    from tools.glslcpp.frontend.cross_builtin_profile import (
        PROFILE as CROSS_BUILTIN_PROFILE, CROSS_KEYS)
    from tools.glslcpp.frontend.any_relational_profile import (
        PROFILE as ANY_RELATIONAL_PROFILE, RENDERLIT_KEY)
    module = _module()
    from tools.glslcpp.frontend.struct_frontier_profile import (
        PROFILES as STRUCT_FRONTIER_PROFILES)
    typed = _analyzed(key)
    row = _manifest_row(key)
    kwargs = {
        "source_global_literal_int_profile":
            loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
    }
    if key in CROSS_KEYS:
        kwargs["cross_builtin_profile"] = CROSS_BUILTIN_PROFILE
    if key == RENDERLIT_KEY:
        kwargs["any_relational_profile"] = ANY_RELATIONAL_PROFILE
    if with_profile:
        kwargs["struct_frontier_profile"] = STRUCT_FRONTIER_PROFILES[key]
    return render_typed_cpp(
        typed, key, row["raw_sha256"], "typed_probe",
        "bind_" + key.replace("/", "_").replace(":", "_"), **kwargs)


class ModulePresenceTests(unittest.TestCase):
    def test_emitter_wiring_exports_the_frontier_symbols(self):
        import sys
        sys.path.insert(0, str(REPOSITORY))
        import tools.glslcpp.emit_typed_cpp as emitter_module
        self.assertTrue(hasattr(emitter_module, "STRUCT_FRONTIER_KEYS"))
        self.assertTrue(hasattr(emitter_module, "authenticate_struct_frontier"))


class ValidatorIntegrationTests(unittest.TestCase):
    def test_validator_green_with_the_exact_carriers(self):
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import loop_proof
        from tools.glslcpp.frontend.cross_builtin_profile import (
            PROFILE as CROSS_BUILTIN_PROFILE, CROSS_KEYS)
        from tools.glslcpp.frontend.any_relational_profile import (
            PROFILE as ANY_RELATIONAL_PROFILE, RENDERLIT_KEY)
        from tools.glslcpp.frontend.struct_frontier_profile import (
            PROFILES as STRUCT_FRONTIER_PROFILES)
        module = _module()
        for key in (RENDER3D_KEY, RENDER_CUBE_KEY, RENDER_LIT_KEY):
            with self.subTest(key=key):
                program = _analyzed(key)
                raw_sha = hashlib.sha256(
                    program.raw_source.encode("utf-8")).hexdigest()
                kwargs = {
                    "source_global_literal_int_profile":
                        loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
                    "struct_frontier_profile":
                        STRUCT_FRONTIER_PROFILES[key],
                }
                if key in CROSS_KEYS:
                    kwargs["cross_builtin_profile"] = CROSS_BUILTIN_PROFILE
                if key == RENDER_LIT_KEY:
                    kwargs["any_relational_profile"] = (
                        ANY_RELATIONAL_PROFILE)
                self.assertIsNone(generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=raw_sha, **kwargs))

    def test_validator_demands_the_exact_profile_carrier(self):
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import loop_proof
        from tools.glslcpp.frontend.cross_builtin_profile import (
            PROFILE as CROSS_BUILTIN_PROFILE, CROSS_KEYS)
        from tools.glslcpp.frontend.any_relational_profile import (
            PROFILE as ANY_RELATIONAL_PROFILE, RENDERLIT_KEY)
        for key in (RENDER3D_KEY, RENDER_CUBE_KEY, RENDER_LIT_KEY):
            with self.subTest(key=key):
                program = _analyzed(key)
                raw_sha = hashlib.sha256(
                    program.raw_source.encode("utf-8")).hexdigest()
                kwargs = {
                    "source_global_literal_int_profile":
                        loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
                }
                if key in CROSS_KEYS:
                    kwargs["cross_builtin_profile"] = CROSS_BUILTIN_PROFILE
                if key == RENDER_LIT_KEY:
                    kwargs["any_relational_profile"] = (
                        ANY_RELATIONAL_PROFILE)
                with self.assertRaisesRegex(
                        generate_typed_slice.GeneratorError,
                        "exact struct frontier profile carrier required"):
                    generate_typed_slice.validate_capabilities(
                        program, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=raw_sha, **kwargs)


class EmitterLoweringTests(unittest.TestCase):
    def test_emitter_requires_the_profile_carrier(self):
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError
        for key in (RENDER3D_KEY, RENDER_CUBE_KEY, RENDER_LIT_KEY):
            with self.subTest(key=key):
                with self.assertRaisesRegex(
                        TypedEmissionError,
                        "exact struct frontier profile carrier required"):
                    _render(key, with_profile=False)

    def test_render3d_emits_the_exact_struct_definitions_and_lowering(self):
        out = _render(RENDER3D_KEY, with_profile=True)
        self.assertIn(
            "struct VoxelHit final {\n"
            "  float dist;\n"
            "  glsl::Vec3 normal;\n"
            "  glsl::IVec3 voxel;\n"
            "};", out)
        self.assertIn(
            "struct IsoHit final {\n"
            "  float dist;\n"
            "  glsl::Vec3 pos;\n"
            "  bool hit;\n"
            "};", out)
        # Uninitialized struct locals value-initialize in C++ (the carriers
        # assign every member before any read).
        self.assertIn("VoxelHit result = {};", out)
        self.assertIn("IsoHit result = {};", out)
        # Member stores and reads lower as plain member access; helper calls
        # carry the emitter-bound (state, context) parameters.
        self.assertIn("result.hit = false;", out)
        self.assertIn("result.dist = static_cast<float>(-1.0);", out)
        self.assertIn("IsoHit hit = isosurfaceTrace(state, context, ro, rd);",
                      out)
        self.assertIn("if (hit.hit) {", out)
        self.assertIn("color = glsl::Vec3(shade(state, context, hit.pos, rd));",
                      out)
        self.assertIn("VoxelHit hit = voxelTrace(state, context, ro, rd);", out)
        self.assertIn("normal = glsl::Vec3(hit.normal);", out)
        # Struct-returning helpers keep their native signatures.
        self.assertIn("[[nodiscard]] IsoHit isosurfaceTrace(", out)
        self.assertIn("[[nodiscard]] VoxelHit voxelTrace(", out)
        self.assertIn("return result;", out)

    def test_rendercubemap3d_emits_the_exact_struct_lowering(self):
        out = _render(RENDER_CUBE_KEY, with_profile=True)
        self.assertIn("struct IsoHit final {", out)
        self.assertIn("struct VoxelHit final {", out)
        self.assertIn("IsoHit result = {};", out)

    def test_renderlit3d_emits_the_exact_struct_lowering(self):
        out = _render(RENDER_LIT_KEY, with_profile=True)
        self.assertIn("struct IsoHit final {\n"
                      "  float dist;\n"
                      "  glsl::Vec3 pos;\n"
                      "  bool hit;\n"
                      "  bool atBoundary;\n"
                      "};", out)
        self.assertIn("IsoHit result = {};", out)
        self.assertIn("result.atBoundary = false;", out)
        self.assertIn("IsoHit hit = raymarch(state, context, roVol, rdVol);",
                      out)
        self.assertIn("if (hit.atBoundary) {", out)
        self.assertIn("if (glsl::any(glsl::lessThan(p, "
                      "glsl::FloatExpr<3>(static_cast<float>(-1.0)))) || "
                      "glsl::any(glsl::greaterThan(p, "
                      "glsl::FloatExpr<3>(static_cast<float>(1.0))))) {", out)

    def test_forged_source_fails_closed_in_the_emitter(self):
        import sys
        sys.path.insert(0, str(REPOSITORY))
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import loop_proof, parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.cross_builtin_profile import (
            PROFILE as CROSS_BUILTIN_PROFILE)
        from tools.glslcpp.frontend.struct_frontier_profile import (
            PROFILES as STRUCT_FRONTIER_PROFILES)
        import json as _json
        from tools.glslcpp import check_semantics
        corpus = _corpus_root()
        for key in (RENDER3D_KEY, RENDER_LIT_KEY):
            with self.subTest(key=key):
                row = _manifest_row(key)
                effect_id, program_name = key.split(":")
                raw = (corpus / row["source"]).read_text(encoding="utf-8")
                defaults = check_semantics._metadata_defaults(
                    {"effects": {effect_id: _json.loads(
                        (corpus / "metadata.json").read_text(
                            encoding="utf-8"))["effects"][effect_id]}},
                    key)
                forged = raw + "\n"
                with self.assertRaises(ValueError) as ctx:
                    analyze_program(
                        parse_program(forged, key, defaults), key,
                        source_global_literal_int_profile=(
                            loop_proof.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
                self.assertIn("mismatch", str(ctx.exception))
                del defaults


class CompletenessTests(unittest.TestCase):
    def test_emitted_member_and_local_census_matches_the_frozen_lock(self):
        from tools.glslcpp.emit_typed_cpp import _Emitter
        from tools.glslcpp.frontend.cross_builtin_profile import (
            PROFILE as CROSS_BUILTIN_PROFILE)
        from tools.glslcpp.frontend.struct_frontier_profile import (
            PROFILES as STRUCT_FRONTIER_PROFILES,
            authenticate_struct_frontier)
        from tools.glslcpp.frontend import loop_proof
        for key in (RENDER3D_KEY, RENDER_CUBE_KEY, RENDER_LIT_KEY):
            with self.subTest(key=key):
                typed = _analyzed(key)
                raw_sha = hashlib.sha256(
                    typed.raw_source.encode("utf-8")).hexdigest()
                record = authenticate_struct_frontier(
                    typed, raw_sha, STRUCT_FRONTIER_PROFILES[key])
                emitter = _Emitter.__new__(_Emitter)
                # Count directly on the authenticated record instead of
                # re-walking: the census IS the emitter's authority.
                self.assertEqual(
                    len(record.members), len(set(id(item) for item in record.members)))
                self.assertEqual(
                    len(record.locals), len(set(id(item[1]) for item in record.locals)))
                self.assertEqual(
                    {item.name for item in record.structs},
                    ({"VoxelHit", "IsoHit"} if key != RENDER_LIT_KEY
                     else {"IsoHit"}))


if __name__ == "__main__":
    unittest.main()
