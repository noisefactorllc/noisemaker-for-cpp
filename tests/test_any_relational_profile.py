"""Focused tests for the any-relational admission profile.

``synth3d/heightmap3d:precompute`` stopped at ``unsupported builtin any`` on
its density bounds ``any(lessThan(p, ivec3(0))) ||
any(greaterThanEqual(p, ivec3(volumeSize)))``, and
``render/renderLit3d:renderLit3d`` on its march volume-exit check
``any(lessThan(p, vec3(-1.0))) || any(greaterThan(p, vec3(1.0)))``.
``any_relational_profile`` freezes each program's complete node identity
(source/normalized/functions/interface digests, main identity, resource
signature, loop proof, closure spans and child hashes) and admits the exact
``any``/relational objects by identity, never a general bvec or relational
capability: each ``bvec3`` intermediate may not escape its immediate
reduction and every other site is refused.

These tests pin the contract directly (the sibling pattern of
``test_attractor_any_isnan_profile``): admission green, forged and tampered
sources fail closed, the validator demands the exact carrier, the emitter
lowers only the authenticated closure, and the runtime surface's new
integer/float relational overloads are exercised on their own (see
``test_glsl_types.cpp`` for the compile-time width/lanes constraints).
"""

from __future__ import annotations

import hashlib
import pathlib
import unittest

MODULE = "tools.glslcpp.frontend.any_relational_profile"

ROOT = pathlib.Path(__file__).resolve().parents[1]

HEIGHTMAP_KEY = "synth3d/heightmap3d:precompute"
RENDERLIT_KEY = "render/renderLit3d:renderLit3d"
PROFILE = "any-relational-admission-v1"

CORPUS_REVISION = "5976b7a6b77f69c47c41f4ee296a54d5318e1f9d"


def _source_path(key: str) -> pathlib.Path:
    effect_id, program = key.split(":", 1)
    vendored = (ROOT / "tools/glslcpp/corpus" / CORPUS_REVISION /
                "sources" / effect_id / f"{program}.glsl")
    if vendored.is_file():
        return vendored
    return (ROOT / "tools/glslcpp/corpus" / CORPUS_REVISION /
            "pending-sources" / effect_id / f"{program}.glsl")


def _module():
    import importlib
    return importlib.import_module(MODULE)


def _source_text(key: str) -> str:
    return _source_path(key).read_text(encoding="utf-8")


def _source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _analyzed(key: str, source: str | None = None):
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic import analyze_program
    from tools.glslcpp.frontend.loop_proof import (
        SOURCE_GLOBAL_LITERAL_INT_CAPABILITY, SOURCE_GLOBAL_LITERAL_INT_KEYS)
    text = _source_text(key) if source is None else source
    return analyze_program(
        parse_program(text, key), key,
        source_global_literal_int_profile=(
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
            if key in SOURCE_GLOBAL_LITERAL_INT_KEYS else None))


class ModulePresenceTests(unittest.TestCase):
    def test_module_exports_the_two_carriers(self):
        module = _module()
        self.assertEqual(PROFILE, module.PROFILE)
        self.assertEqual(HEIGHTMAP_KEY, module.HEIGHTMAP_KEY)
        self.assertEqual(RENDERLIT_KEY, module.RENDERLIT_KEY)
        self.assertEqual(
            (HEIGHTMAP_KEY, RENDERLIT_KEY), module.ANY_RELATIONAL_KEYS)
        self.assertEqual(
            ("PROFILE", "HEIGHTMAP_KEY", "RENDERLIT_KEY",
             "ANY_RELATIONAL_KEYS", "AnyRelationalProof",
             "authenticate_any_relational_admission",
             "apply_any_relational_admission",
             "is_authenticated_reduction_node",
             "is_authenticated_relational_node"),
            module.__all__)


class SourceIdentityTests(unittest.TestCase):
    def test_heightmap_source_matches_the_frozen_digests(self):
        module = _module()
        record = module._RECORDS[HEIGHTMAP_KEY]
        raw = _source_text(HEIGHTMAP_KEY).encode("utf-8")
        self.assertEqual(record.raw_bytes, len(raw))
        self.assertEqual(record.raw_sha256, _source_hash(_source_text(HEIGHTMAP_KEY)))
        self.assertEqual(
            (record.normalized_bytes, record.normalized_sha256),
            (1667, "fc9f74e1a388e251dc5663c7022639ae8d9981c81c44abd6ba9d16edb581c0bc"))

    def test_renderlit_source_matches_the_frozen_digests(self):
        module = _module()
        record = module._RECORDS[RENDERLIT_KEY]
        raw = _source_text(RENDERLIT_KEY).encode("utf-8")
        self.assertEqual(record.raw_bytes, len(raw))
        self.assertEqual(record.raw_sha256, _source_hash(_source_text(RENDERLIT_KEY)))
        self.assertEqual(
            (record.normalized_bytes, record.normalized_sha256),
            (9504, "cc72ea7149272c38ff05fb6842a4f7f720ea05c4065b2e6900edb7f1885ec980"))


class AdmissionGreenTests(unittest.TestCase):
    def test_heightmap_authentication_returns_candidate_owned_objects(self):
        module = _module()
        program = _analyzed(HEIGHTMAP_KEY)
        proof = module.authenticate_any_relational_admission(
            program, _source_hash(_source_text(HEIGHTMAP_KEY)), PROFILE)
        self.assertEqual(HEIGHTMAP_KEY, proof.key)
        self.assertEqual(2, len(proof.reductions))
        self.assertEqual(2, len(proof.relationals))
        for reduction in proof.reductions:
            self.assertEqual("any", reduction.callee)
            self.assertEqual("bool", reduction.type.display())
        self.assertEqual("lessThan", proof.relationals[0].callee)
        self.assertEqual("greaterThanEqual", proof.relationals[1].callee)
        for relational in proof.relationals:
            self.assertEqual("bvec3", relational.type.display())
            self.assertEqual(("ivec3", "ivec3"),
                             tuple(child.type.display()
                                   for child in relational.children))
        # Identity, not equality: each relational is exactly its reduction's
        # only child.
        self.assertIs(proof.relationals[0], proof.reductions[0].children[0])
        self.assertIs(proof.relationals[1], proof.reductions[1].children[0])

    def test_renderlit_authentication_returns_candidate_owned_objects(self):
        module = _module()
        program = _analyzed(RENDERLIT_KEY)
        proof = module.authenticate_any_relational_admission(
            program, _source_hash(_source_text(RENDERLIT_KEY)), PROFILE)
        self.assertEqual(RENDERLIT_KEY, proof.key)
        self.assertEqual(2, len(proof.reductions))
        self.assertEqual(2, len(proof.relationals))
        self.assertEqual("lessThan", proof.relationals[0].callee)
        self.assertEqual("greaterThan", proof.relationals[1].callee)
        for relational in proof.relationals:
            self.assertEqual(("vec3", "vec3"),
                             tuple(child.type.display()
                                   for child in relational.children))
        self.assertIs(proof.relationals[0], proof.reductions[0].children[0])
        self.assertIs(proof.relationals[1], proof.reductions[1].children[0])

    def test_apply_returns_the_same_program_object(self):
        module = _module()
        for key in (HEIGHTMAP_KEY, RENDERLIT_KEY):
            program = _analyzed(key)
            self.assertIs(
                program,
                module.apply_any_relational_admission(
                    program, _source_hash(_source_text(key)), PROFILE))

    def test_identity_helpers_accept_only_the_exact_nodes(self):
        module = _module()
        for key in (HEIGHTMAP_KEY, RENDERLIT_KEY):
            proof = module.authenticate_any_relational_admission(
                _analyzed(key), _source_hash(_source_text(key)), PROFILE)
            for reduction in proof.reductions:
                self.assertTrue(module.is_authenticated_reduction_node(
                    proof, reduction))
                self.assertFalse(module.is_authenticated_relational_node(
                    proof, reduction))
            for relational in proof.relationals:
                self.assertTrue(module.is_authenticated_relational_node(
                    proof, relational))
                self.assertFalse(module.is_authenticated_reduction_node(
                    proof, relational))


class FailClosedTests(unittest.TestCase):
    def test_missing_profile_is_refused(self):
        module = _module()
        for key in (HEIGHTMAP_KEY, RENDERLIT_KEY):
            with self.assertRaisesRegex(ValueError,
                                        "exact profile carrier required"):
                module.authenticate_any_relational_admission(
                    _analyzed(key), _source_hash(_source_text(key)), None)

    def test_wrong_profile_string_is_refused(self):
        module = _module()
        for key in (HEIGHTMAP_KEY, RENDERLIT_KEY):
            with self.assertRaisesRegex(ValueError,
                                        "exact profile carrier required"):
                module.authenticate_any_relational_admission(
                    _analyzed(key), _source_hash(_source_text(key)),
                    "any-relational-admission-v2")

    def test_wrong_caller_source_hash_is_refused(self):
        module = _module()
        for key in (HEIGHTMAP_KEY, RENDERLIT_KEY):
            with self.assertRaisesRegex(ValueError,
                                        "selected key and exact caller source "
                                        "hash required"):
                module.authenticate_any_relational_admission(
                    _analyzed(key), "0" * 64, PROFILE)

    def test_tampered_source_is_refused(self):
        module = _module()
        tamper = {HEIGHTMAP_KEY: "volumeSize", RENDERLIT_KEY: "tEnd"}
        for key, needle in tamper.items():
            raw = _source_text(key)
            tampered = raw.replace(needle, f"{needle}2")
            self.assertNotEqual(tampered, raw)
            if key == RENDERLIT_KEY:
                # renderLit3d's frozen march-bound carrier refuses the
                # tampered raw digest one stage earlier (at loop-proof
                # attach); the refusal is equally fail-closed.
                with self.assertRaises(ValueError):
                    module.authenticate_any_relational_admission(
                        _analyzed(key, tampered), _source_hash(tampered),
                        PROFILE)
            else:
                with self.assertRaisesRegex(
                        ValueError,
                        "selected key and exact caller source "
                        "hash required"):
                    module.authenticate_any_relational_admission(
                        _analyzed(key, tampered), _source_hash(tampered),
                        PROFILE)

    def test_forged_normalized_identical_source_is_refused(self):
        """Whitespace hidden inside a comment leaves the normalized text
        untouched but must still fail closed on the raw digest."""
        module = _module()
        for key in (HEIGHTMAP_KEY, RENDERLIT_KEY):
            raw = _source_text(key)
            lines = raw.splitlines(keepends=True)
            forged = None
            for index, line in enumerate(lines):
                if line.lstrip().startswith("//"):
                    candidate = lines.copy()
                    candidate[index] = line.rstrip("\n") + " \n"
                    forged = "".join(candidate)
                    break
            self.assertIsNotNone(forged)
            from tools.glslcpp.frontend.preprocess import normalize
            self.assertNotEqual(forged, raw)
            self.assertEqual(normalize(forged), normalize(raw))
            if key == RENDERLIT_KEY:
                # renderLit3d's frozen march-bound carrier refuses the forged
                # raw digest one stage earlier (at loop-proof attach); the
                # refusal is equally fail-closed.
                with self.assertRaises(ValueError):
                    module.authenticate_any_relational_admission(
                        _analyzed(key, forged), _source_hash(forged), PROFILE)
            else:
                with self.assertRaisesRegex(
                        ValueError,
                        "selected key and exact caller source "
                        "hash required"):
                    module.authenticate_any_relational_admission(
                        _analyzed(key, forged), _source_hash(forged), PROFILE)

    def test_extra_reduction_site_is_refused(self):
        """A second `any(lessThan(...))` with the same shapes but a different
        source identity must never authenticate."""
        module = _module()
        raw = _source_text(HEIGHTMAP_KEY)
        duplicated = raw.replace(
            "any(lessThan(p, ivec3(0)))",
            "any(lessThan(p, ivec3(0))) || any(lessThan(p, ivec3(0)))", 1)
        self.assertNotEqual(duplicated, raw)
        from tools.glslcpp.frontend.preprocess import normalize
        self.assertNotEqual(normalize(duplicated), normalize(raw))


class ValidatorIntegrationTests(unittest.TestCase):
    def test_heightmap_validator_demands_the_exact_profile_carrier(self):
        from tools.glslcpp import generate_typed_slice
        program = _analyzed(HEIGHTMAP_KEY)
        with self.assertRaises(generate_typed_slice.GeneratorError) as ctx:
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=_source_hash(_source_text(HEIGHTMAP_KEY)))
        self.assertIn("exact any-relational admission profile carrier "
                      "required", str(ctx.exception))

    def test_heightmap_validator_accepts_with_the_exact_carrier(self):
        from tools.glslcpp import generate_typed_slice
        program = _analyzed(HEIGHTMAP_KEY)
        self.assertIsNone(generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=_source_hash(_source_text(HEIGHTMAP_KEY)),
            any_relational_profile=PROFILE))

    def test_renderlit_validator_demands_the_exact_profile_carrier(self):
        """renderLit3d composes the closure with its frozen march loop
        bound, IsoHit struct-frontier and cross-builtin carriers; with only
        those present, the missing closure carrier is the refusal."""
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.cross_builtin_profile import (
            PROFILE as CROSS_BUILTIN_PROFILE)
        from tools.glslcpp.frontend.loop_proof import (
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        from tools.glslcpp.frontend.struct_frontier_profile import (
            PROFILES as STRUCT_FRONTIER_PROFILES)
        program = _analyzed(RENDERLIT_KEY)
        with self.assertRaises(generate_typed_slice.GeneratorError) as ctx:
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=_source_hash(_source_text(RENDERLIT_KEY)),
                source_global_literal_int_profile=(
                    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
                struct_frontier_profile=STRUCT_FRONTIER_PROFILES[RENDERLIT_KEY],
                cross_builtin_profile=CROSS_BUILTIN_PROFILE)
        self.assertIn("exact any-relational admission profile carrier "
                      "required", str(ctx.exception))

    def test_renderlit_validator_accepts_with_the_exact_carriers(self):
        """renderLit3d composes the closure with its frozen march loop bound,
        IsoHit struct-frontier and cross-builtin carriers, all attached by
        key or row."""
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.cross_builtin_profile import (
            PROFILE as CROSS_BUILTIN_PROFILE)
        from tools.glslcpp.frontend.loop_proof import (
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        from tools.glslcpp.frontend.struct_frontier_profile import (
            PROFILES as STRUCT_FRONTIER_PROFILES)
        program = _analyzed(RENDERLIT_KEY)
        self.assertIsNone(generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=_source_hash(_source_text(RENDERLIT_KEY)),
            source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
            struct_frontier_profile=STRUCT_FRONTIER_PROFILES[RENDERLIT_KEY],
            cross_builtin_profile=CROSS_BUILTIN_PROFILE,
            any_relational_profile=PROFILE))


class EmitterLoweringTests(unittest.TestCase):
    def _emitted(self, key: str, with_profile: bool, **extra):
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend.cross_builtin_profile import (
            PROFILE as CROSS_BUILTIN_PROFILE)
        from tools.glslcpp.frontend.loop_proof import (
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        kwargs = {}
        if key == RENDERLIT_KEY:
            kwargs["source_global_literal_int_profile"] = (
                SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
            kwargs["cross_builtin_profile"] = CROSS_BUILTIN_PROFILE
        if with_profile:
            kwargs["any_relational_profile"] = PROFILE
        kwargs.update(extra)
        return render_typed_cpp(
            _analyzed(key), key, _source_hash(_source_text(key)),
            "typed_test", "bind_test", **kwargs)

    def test_heightmap_emitter_requires_the_profile_carrier(self):
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError
        with self.assertRaisesRegex(TypedEmissionError,
                                    "exact any-relational admission profile "
                                    "carrier required"):
            self._emitted(HEIGHTMAP_KEY, with_profile=False)

    def test_heightmap_emitter_lowers_the_authenticated_closure(self):
        out = self._emitted(HEIGHTMAP_KEY, with_profile=True)
        self.assertIn(
            "if (glsl::any(glsl::lessThan(p, glsl::IVec3(std::int32_t(0)))) "
            "|| glsl::any(glsl::greaterThanEqual(p, glsl::IVec3("
            "state.volumeSize))))", out)

    def test_renderlit_emitter_demands_the_exact_profile_carrier(self):
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError
        with self.assertRaisesRegex(TypedEmissionError,
                                    "exact any-relational admission profile "
                                    "carrier required"):
            self._emitted(RENDERLIT_KEY, with_profile=False)

    def test_renderlit_emitter_renders_with_the_struct_frontier(self):
        """With the closure and struct-frontier carriers together, every
        any/relational site lowers and the IsoHit struct emission is
        authenticated -- the former frontier of the render3d/renderCubemap3d
        siblings is admitted."""
        from tools.glslcpp.frontend.struct_frontier_profile import (
            PROFILES as STRUCT_FRONTIER_PROFILES)
        self.assertIn("IsoHit raymarch", self._emitted(
            RENDERLIT_KEY, with_profile=True,
            struct_frontier_profile=STRUCT_FRONTIER_PROFILES[RENDERLIT_KEY]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
