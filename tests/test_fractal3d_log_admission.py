"""Focused tests for ``synth3d/fractal3d:precompute``'s log admission.

The program is the ``parameter-uniform-argument-bound`` counted-for carrier
(``loop_proof``'s frozen ``synth3d/fractal3d:precompute`` entry) whose two
distance estimators finish with ``float dist = 0.5 * log(r) * r / dr;`` --
the first authentic non-counted frontier (``93:24: unsupported builtin log``)
after the parameter-bound seed landed. ``log`` is analyzer-known
(``body_semantic``'s ``unary_float`` overload) and the JS authority routes it
through ``Math.log`` (``glsl-runtime.js:341``: ``log: unary(Math.log)``), but
the shared validator vocabulary and emitter arms do not carry it generically:
exactly the Mandelbrot log-admission shape. ``fractal3d_log_profile`` freezes
the two sites by node identity and both authorities consume them; the
capability vocabulary does not move.
"""

from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import unittest

from tools.glslcpp import check_corpus, generate_typed_slice
from tools.glslcpp import emit_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.loop_proof import (
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
from tools.glslcpp.frontend.semantic import analyze_program

MODULE = "tools.glslcpp.frontend.fractal3d_log_profile"

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / f"tools/glslcpp/corpus/{check_corpus.REVISION}"
KEY = "synth3d/fractal3d:precompute"
PROFILE = "fractal3d-log-admission-v1"
SOURCE_PATH = "synth3d/fractal3d/precompute.glsl"
RAW_SHA256 = "8ab3dfe63e16d4406deee719c1f822d405c712bae21bd1348ae5b75b79a14d41"
NORMALIZED_SHA256 = (
    "bfc4b9e886fa4dc5d642abfd6457c643a47287f2095ccac0f99759ad5ff1d5a6")
LOG_SPANS = ("93:24-93:30", "55:24-55:30")
LOG_OWNERS = ("juliaBulb", "mandelbulb")
COUNTED_LOOP_SUMMARY = (4, 0, 1, 20, 80, True)
LEDGER = 6

FOREIGN_SOURCE = (
    "uniform float time;\n"
    "out vec4 fragColor;\n"
    "void main() {\n"
    "    fragColor = vec4(log(time), 0.0, 0.0, 1.0);\n"
    "}\n"
)


def _module():
    import importlib
    return importlib.import_module(MODULE)


def _source_text() -> str:
    """The pinned program source, resolved from either corpus side."""
    for parent in ("sources", "pending-sources"):
        path = CORPUS / parent / SOURCE_PATH
        if path.exists():
            return path.read_text(encoding="utf-8")
    raise AssertionError(f"{SOURCE_PATH} is absent from the corpus")


def _analyzed():
    return analyze_program(
        parse_program(_source_text(), KEY, {}), KEY,
        source_global_literal_int_profile=(
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))


def _foreign():
    return analyze_program(
        parse_program(FOREIGN_SOURCE, "test:foreign", {}), "test:foreign")


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ModulePresenceTests(unittest.TestCase):
    def test_module_imports(self):
        module = _module()
        self.assertEqual(KEY, module.KEY)
        self.assertEqual(PROFILE, module.PROFILE)
        self.assertEqual(frozenset({KEY}), module.FRACTAL3D_LOG_KEYS)


class FrozenFactTests(unittest.TestCase):
    def test_pinned_source_bytes_and_hash(self):
        module = _module()
        raw = _source_text().encode("utf-8")
        self.assertEqual(module.RAW_BYTES, len(raw))
        self.assertEqual(RAW_SHA256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(RAW_SHA256, module.RAW_SHA256)

    def test_live_analysis_matches_frozen_identity(self):
        module = _module()
        program = _analyzed()
        normalized = program.source.encode("utf-8")
        self.assertEqual(module.NORMALIZED_BYTES, len(normalized))
        self.assertEqual(NORMALIZED_SHA256,
                         hashlib.sha256(normalized).hexdigest())
        summary = program.counted_loop_proof
        self.assertEqual(COUNTED_LOOP_SUMMARY,
                         (summary.loop_count, summary.unproved_loop_count,
                          summary.max_effective_depth,
                          summary.max_lexical_product,
                          summary.entrypoint_charge,
                          summary.call_graph_acyclic))
        self.assertEqual(
            (module.INTERFACE_SHA256, module.FUNCTIONS_SHA256,
             module.WHOLE_SHA256),
            (module._interface(program),
             module._sha(module.clear_counted_loop_proofs(program.functions)),
             module._whole_cleared(program)))


class AdmissionGreenTests(unittest.TestCase):
    def test_proof_names_both_sites_in_program_order(self):
        module = _module()
        program = _analyzed()
        proof = module.authenticate_fractal3d_log_admission(
            program, RAW_SHA256, PROFILE)
        self.assertEqual(2, len(proof.sites))
        self.assertEqual(LOG_OWNERS,
                         tuple(site.owner_name for site in proof.sites))
        self.assertEqual(LOG_SPANS, tuple(site.span for site in proof.sites))
        self.assertEqual(LEDGER, len(proof.consumed_objects))
        self.assertEqual(LEDGER, len({id(item) for item in
                                      proof.consumed_objects}))

    def test_apply_is_the_identity(self):
        module = _module()
        program = _analyzed()
        self.assertIs(program, module.apply_fractal3d_log_admission(
            program, RAW_SHA256, PROFILE))

    def test_foreign_key_without_profile_returns_none(self):
        module = _module()
        self.assertIsNone(module.authenticate_fractal3d_log_admission(
            _foreign(), _hash(FOREIGN_SOURCE), None))

    def test_foreign_key_with_profile_is_a_hard_failure(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_fractal3d_log_admission(
                _foreign(), _hash(FOREIGN_SOURCE), PROFILE)
        self.assertIn(
            f"{PROFILE}: program key is not an admitted fractal3d log "
            f"admission carrier; {KEY} 93:24 and 55:24 are the sole admitted "
            "log sites",
            str(raised.exception))

    def test_wrong_profile_string_is_refused(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact profile carrier required"):
            module.authenticate_fractal3d_log_admission(
                _analyzed(), RAW_SHA256, "fractal3d-log-admission-v2")

    def test_wrong_caller_source_hash_is_refused(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_fractal3d_log_admission(
                _analyzed(), "0" * 64, PROFILE)

    def test_tampered_source_is_refused_at_the_coarse_gate(self):
        module = _module()
        raw = _source_text().replace("0.5 * log(r) * r / dr;",
                                     "0.55 * log(r) * r / dr;")
        program = analyze_program(parse_program(raw, KEY, {}), KEY)
        with self.assertRaisesRegex(ValueError, "lock mismatch"):
            module.authenticate_fractal3d_log_admission(
                program, RAW_SHA256, PROFILE)

    def test_allowed_row_fields_reject_foreign_keys(self):
        module = _module()
        self.assertEqual(
            frozenset({"defines", "fractal3d_log_profile", "program_key"}),
            module.allowed_row_fields(KEY))
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("test:foreign")


class AuthorityIntegrationTests(unittest.TestCase):
    def test_validator_demands_the_exact_profile_carrier(self):
        program = _analyzed()
        with self.assertRaises(generate_typed_slice.GeneratorError) as raised:
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256,
                source_global_literal_int_profile=(
                    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
        self.assertEqual(
            f"{KEY}: exact fractal3d log admission profile carrier required",
            str(raised.exception))

    def test_validator_and_emitter_accept_the_admitted_program(self):
        program = _analyzed()
        self.assertIsNone(generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=RAW_SHA256,
            source_global_literal_int_profile=(
                SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
            fractal3d_log_profile=PROFILE))
        emitted = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256, "typed_test", "bind_test",
            source_global_literal_int_profile=(
                SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
            fractal3d_log_profile=PROFILE)
        self.assertEqual(2, emitted.count("glsl::log("))

    def test_emitter_without_the_profile_still_rejects_the_log_sites(self):
        program = _analyzed()
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=RAW_SHA256,
            source_global_literal_int_profile=(
                SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
            fractal3d_log_profile=PROFILE)
        with self.assertRaisesRegex(
                emit_typed_cpp.TypedEmissionError,
                "exact fractal3d log admission profile carrier required"):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, RAW_SHA256, "typed_test", "bind_test",
                source_global_literal_int_profile=(
                    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))


class CorpusCensusTests(unittest.TestCase):
    def test_fractal3d_is_an_authenticatable_single_key_census(self):
        """Source-level census: the pinned corpus carries several pending
        `log(` callers (flythrough3d, noise3d, shapes3d among them), so the
        authenticatable set must stay frozen at exactly this one key."""
        module = _module()
        carriers = set()
        for parent in ("sources", "pending-sources"):
            for path in (CORPUS / parent).rglob("*.glsl"):
                if "log(" in path.read_text(encoding="utf-8"):
                    relative = path.relative_to(CORPUS / parent).with_suffix(
                        "").as_posix()
                    namespace_effect, program = relative.rsplit("/", 1)
                    carriers.add(f"{namespace_effect}:{program}")
        self.assertIn(KEY, carriers)
        self.assertEqual(frozenset({KEY}), module.FRACTAL3D_LOG_KEYS)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
