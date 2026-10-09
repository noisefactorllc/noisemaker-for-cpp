"""Focused tests for the attractor ``any(isnan(vec3))`` admission profile.

``points/attractor:agent`` stopped at ``no exact overload for any/isnan`` on
its divergence check ``if (any(isnan(newPos)) || length(newPos) > 1000.0)``.
``attractor_any_isnan_profile`` freezes that one closure's complete node
identity (source/normalized/functions/interface digests, main identity,
resource signature, loop proof, closure spans and child hashes) and admits
the exact ``any``/``isnan`` objects by identity, never a general bvec or
NaN capability: the ``bvec3`` intermediate may not escape its immediate
reduction and every other site is refused.

These tests pin the contract directly (the sibling pattern of
``test_struct_frontier_profile``): admission green, forged and tampered
sources fail closed, the validator demands the exact carrier, the emitter
lowers only the authenticated closure, and the runtime surface
``isnan(Vec3)``/``any(BVec3)`` is exercised on its own (see
``test_glsl_types.cpp`` for the compile-time width/lanes constraints).
"""

from __future__ import annotations

import hashlib
import pathlib
import unittest

MODULE = "tools.glslcpp.frontend.attractor_any_isnan_profile"

ROOT = pathlib.Path(__file__).resolve().parents[1]

KEY = "points/attractor:agent"
PROFILE = "attractor-isnan-any-admission-v1"

CORPUS_REVISION = "5976b7a6b77f69c47c41f4ee296a54d5318e1f9d"
SOURCE_PATH = (ROOT / "tools/glslcpp/corpus" / CORPUS_REVISION /
               "sources/points/attractor/agent.glsl")


def _module():
    import importlib
    return importlib.import_module(MODULE)


def _source_text() -> str:
    return SOURCE_PATH.read_text(encoding="utf-8")


def _source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _analyzed(source: str | None = None):
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic import analyze_program
    text = _source_text() if source is None else source
    return analyze_program(
        parse_program(text, KEY), KEY)


class ModulePresenceTests(unittest.TestCase):
    def test_module_exports_the_single_carrier(self):
        module = _module()
        self.assertEqual(PROFILE, module.PROFILE)
        self.assertEqual(KEY, module.ATTRACTOR_KEY)
        self.assertEqual(
            ("PROFILE", "ATTRACTOR_KEY", "AttractorAnyIsnanProof",
             "authenticate_attractor_any_isnan_admission",
             "apply_attractor_any_isnan_admission",
             "is_authenticated_reduction_node",
             "is_authenticated_test_node"),
            module.__all__)


class SourceIdentityTests(unittest.TestCase):
    def test_vendored_source_matches_the_frozen_digests(self):
        module = _module()
        raw = _source_text().encode("utf-8")
        self.assertEqual(module._RAW_BYTES, len(raw))
        self.assertEqual(module._RAW_SHA256, _source_hash(_source_text()))
        self.assertEqual(
            (module._NORMALIZED_BYTES, module._NORMALIZED_SHA256),
            (4037, "d6b8f3bdd40429533066d5a36851310e4fd2f12c4d5fbbfeef9e722e2b03c0aa"))


class AdmissionGreenTests(unittest.TestCase):
    def test_authentication_returns_candidate_owned_objects(self):
        module = _module()
        program = _analyzed()
        proof = module.authenticate_attractor_any_isnan_admission(
            program, _source_hash(_source_text()), PROFILE)
        self.assertEqual(31, proof.main.id)
        self.assertEqual("any", proof.reduction.callee)
        self.assertEqual("isnan", proof.test.callee)
        self.assertEqual("bool", proof.reduction.type.display())
        self.assertEqual("bvec3", proof.test.type.display())
        # main, the reduction, the test, and the single enclosing if.
        self.assertEqual(4, len(proof.consumed_objects))
        # Identity, not equality: the proof's test object is exactly the
        # reduction's only child inside the program tree.
        self.assertIs(proof.test, proof.reduction.children[0])

    def test_apply_returns_the_same_program_object(self):
        module = _module()
        program = _analyzed()
        self.assertIs(
            program,
            module.apply_attractor_any_isnan_admission(
                program, _source_hash(_source_text()), PROFILE))

    def test_identity_helpers_accept_only_the_exact_nodes(self):
        module = _module()
        proof = module.authenticate_attractor_any_isnan_admission(
            _analyzed(), _source_hash(_source_text()), PROFILE)
        self.assertTrue(module.is_authenticated_reduction_node(
            proof, proof.reduction))
        self.assertFalse(module.is_authenticated_reduction_node(
            proof, proof.test))
        self.assertTrue(module.is_authenticated_test_node(proof, proof.test))
        self.assertFalse(module.is_authenticated_test_node(
            proof, proof.reduction))


class FailClosedTests(unittest.TestCase):
    def test_missing_profile_is_refused(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact profile carrier required"):
            module.authenticate_attractor_any_isnan_admission(
                _analyzed(), _source_hash(_source_text()), None)

    def test_wrong_profile_string_is_refused(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact profile carrier required"):
            module.authenticate_attractor_any_isnan_admission(
                _analyzed(), _source_hash(_source_text()),
                "attractor-isnan-any-admission-v2")

    def test_foreign_key_with_profile_is_refused(self):
        module = _module()
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        foreign = (
            "out vec4 fragColor;\n"
            "void main() {\n"
            "    fragColor = vec4(1.0);\n"
            "}\n")
        program = analyze_program(parse_program(foreign, "test:foreign"),
                                  "test:foreign")
        with self.assertRaisesRegex(ValueError,
                                    "selected key and exact caller source "
                                    "hash required"):
            module.authenticate_attractor_any_isnan_admission(
                program, _source_hash(foreign), PROFILE)

    def test_wrong_caller_source_hash_is_refused(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "selected key and exact caller source "
                                    "hash required"):
            module.authenticate_attractor_any_isnan_admission(
                _analyzed(), "0" * 64, PROFILE)

    def test_forged_normalized_identical_source_is_refused(self):
        """Whitespace hidden inside a comment leaves the normalized text
        untouched but must still fail closed on the raw digest."""
        module = _module()
        raw = _source_text()
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
        with self.assertRaisesRegex(ValueError,
                                    "selected key and exact caller source "
                                    "hash required"):
            module.authenticate_attractor_any_isnan_admission(
                _analyzed(forged), _source_hash(forged), PROFILE)

    def test_tampered_source_is_refused(self):
        module = _module()
        raw = _source_text()
        tampered = raw.replace("newPos", "newpos2")
        self.assertNotEqual(tampered, raw)
        with self.assertRaisesRegex(ValueError,
                                    "selected key and exact caller source "
                                    "hash required"):
            module.authenticate_attractor_any_isnan_admission(
                _analyzed(tampered), _source_hash(tampered), PROFILE)


class ValidatorIntegrationTests(unittest.TestCase):
    def test_validator_demands_the_exact_profile_carrier(self):
        from tools.glslcpp import generate_typed_slice
        program = _analyzed()
        with self.assertRaises(generate_typed_slice.GeneratorError) as ctx:
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=_source_hash(_source_text()))
        self.assertEqual(
            f"{KEY}: exact Attractor any/isnan admission profile carrier "
            "required",
            str(ctx.exception))

    def test_profile_alone_is_not_sufficient(self):
        """The closure profile admits any/isnan only; the agent's separate
        hash_uint closure still needs its own hash carriers."""
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.attractor_any_isnan_profile import (
            PROFILE as ATTRACTOR_PROFILE)
        program = _analyzed()
        with self.assertRaises(generate_typed_slice.GeneratorError) as ctx:
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=_source_hash(_source_text()),
                attractor_any_isnan_profile=ATTRACTOR_PROFILE)
        self.assertIn("unsupported binary operator ^", str(ctx.exception))

    def test_validator_accepts_with_the_exact_carriers(self):
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.attractor_any_isnan_profile import (
            PROFILE as ATTRACTOR_PROFILE)
        from tools.glslcpp.frontend.hash_scalar_uint_xor_profile import (
            PROFILE as XOR_PROFILE)
        from tools.glslcpp.frontend.hash_scalar_uint_rshift_profile import (
            PROFILE as RSHIFT_PROFILE)
        program = _analyzed()
        self.assertIsNone(generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=_source_hash(_source_text()),
            hash_scalar_uint_xor_profile=XOR_PROFILE,
            hash_scalar_uint_rshift_profile=RSHIFT_PROFILE,
            attractor_any_isnan_profile=ATTRACTOR_PROFILE))


class EmitterLoweringTests(unittest.TestCase):
    def _emitted(self, with_profile: bool):
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend.attractor_any_isnan_profile import (
            PROFILE as ATTRACTOR_PROFILE)
        from tools.glslcpp.frontend.hash_scalar_uint_xor_profile import (
            PROFILE as XOR_PROFILE)
        from tools.glslcpp.frontend.hash_scalar_uint_rshift_profile import (
            PROFILE as RSHIFT_PROFILE)
        kwargs = {
            "hash_scalar_uint_xor_profile": XOR_PROFILE,
            "hash_scalar_uint_rshift_profile": RSHIFT_PROFILE,
        }
        if with_profile:
            kwargs["attractor_any_isnan_profile"] = ATTRACTOR_PROFILE
        return render_typed_cpp(
            _analyzed(), KEY, _source_hash(_source_text()),
            "typed_test", "bind_test", **kwargs)

    def test_emitter_requires_the_profile_carrier(self):
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError
        with self.assertRaisesRegex(TypedEmissionError,
                                    "exact Attractor any/isnan admission "
                                    "profile carrier required"):
            self._emitted(with_profile=False)

    def test_emitter_lowers_the_authenticated_closure(self):
        out = self._emitted(with_profile=True)
        marker = "glsl::any(glsl::isnan(newPos))"
        self.assertIn(marker, out)
        # The closure is exactly the divergence check's first operand.
        self.assertIn(
            f"if ({marker} || (glsl::length(newPos) > "
            "static_cast<float>(1000.0)))", out)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
