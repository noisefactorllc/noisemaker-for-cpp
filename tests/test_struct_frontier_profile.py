"""Focused tests for the five-program struct-declaration frontier admission.

The counted-for queue's remaining 3D render/synth families all stop at the
``unsupported struct declaration`` validator frontier.
``struct_frontier_profile`` freezes each carrier's complete struct plumbing
(declarations, fields, struct-return functions, struct-typed parameters,
struct locals, member sites, absent constructor/global sets) and admits it
proof-gated: admission is by object identity into the module's frozen
records only, the capability vocabulary does not move, and the emitter
keeps every struct type rejected (this leg advances the validator; the
emitter frontier is a later slice).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import unittest

MODULE = "tools.glslcpp.frontend.struct_frontier_profile"

ROOT = pathlib.Path(__file__).resolve().parents[1]

KEYS = (
    "classicNoisedeck/shapes3d:shapes3d",
    "render/render3d:render3d",
    "render/renderCubemap3d:renderCubemap3d",
    "render/renderLit3d:renderLit3d",
    "synth3d/flythrough3d:precompute",
)
PROFILES = {
    "classicNoisedeck/shapes3d:shapes3d": "struct-frontier-shapes3d-v1",
    "render/render3d:render3d": "struct-frontier-render3d-v1",
    "render/renderCubemap3d:renderCubemap3d": "struct-frontier-rendercube-v1",
    "render/renderLit3d:renderLit3d": "struct-frontier-renderlit-v1",
    "synth3d/flythrough3d:precompute": "struct-frontier-flythrough-v1",
}
CROSS_KEYS = frozenset({
    "render/render3d:render3d",
    "render/renderLit3d:renderLit3d",
    "synth3d/flythrough3d:precompute",
})
RENDER3D_KEY = "render/render3d:render3d"
SHAPES3D_KEY = "classicNoisedeck/shapes3d:shapes3d"

# (structs, locals, members, total_nodes) per carrier, measured this session.
CENSUS = {
    "classicNoisedeck/shapes3d:shapes3d": (2, 4, 29, 1146),
    "render/render3d:render3d": (2, 4, 29, 1204),
    "render/renderCubemap3d:renderCubemap3d": (2, 4, 29, 1165),
    "render/renderLit3d:renderLit3d": (1, 2, 18, 1006),
    "synth3d/flythrough3d:precompute": (1, 4, 15, 795),
}
CONSUMED = {
    "classicNoisedeck/shapes3d:shapes3d": 54,
    "render/render3d:render3d": 47,
    "render/renderCubemap3d:renderCubemap3d": 47,
    "render/renderLit3d:renderLit3d": 28,
    "synth3d/flythrough3d:precompute": 30,
}

FOREIGN_SOURCE = (
    "out vec4 fragColor;\n"
    "struct Foreign {\n"
    "    float a;\n"
    "};\n"
    "void main() {\n"
    "    Foreign f;\n"
    "    f.a = 1.0;\n"
    "    fragColor = vec4(f.a);\n"
    "}\n"
)


def _module():
    import importlib
    return importlib.import_module(MODULE)


def _corpus_root() -> pathlib.Path:
    from tools.glslcpp import check_corpus
    return ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION


def _pending() -> dict:
    return json.loads((_corpus_root() / "pending.json").read_text(
        encoding="utf-8"))


def _source_text(key: str) -> str:
    effect_id, program = key.split(":", 1)
    path = (_corpus_root() / "pending-sources" / effect_id / f"{program}.glsl")
    if not path.exists():
        path = (_corpus_root() / "sources" / effect_id / f"{program}.glsl")
    return path.read_text(encoding="utf-8")


def _defaults(key: str) -> dict:
    from tools.glslcpp import check_semantics
    pending = _pending()
    effect = pending["effects"][key.split(":", 1)[0]]
    return check_semantics._metadata_defaults(
        {"effects": {key.split(":", 1)[0]: effect}}, key)


def _effect(key: str) -> dict:
    return _pending()["effects"][key.split(":", 1)[0]]


def _analyzed(key: str, source: str | None = None):
    """The carrier's post-admission tree: exactly the tree the validator
    authenticates (loop-proof seed, cross admission, fixed proofs)."""
    from tools.glslcpp import generate_typed_slice
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.loop_proof import (
        SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
    from tools.glslcpp.frontend.semantic import analyze_program
    text = _source_text(key) if source is None else source
    source_hash = _source_hash(text)
    typed = analyze_program(
        parse_program(text, key, _defaults(key)), key,
        source_global_literal_int_profile=(
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
    if key in CROSS_KEYS:
        from tools.glslcpp.frontend.cross_builtin_profile import (
            CROSS_KEYS as _CROSS_PROFILE_KEYS,
            PROFILE as CROSS_BUILTIN_PROFILE, apply_cross_admission)
        assert key in _CROSS_PROFILE_KEYS
        typed = apply_cross_admission(typed, source_hash,
                                      CROSS_BUILTIN_PROFILE)
    typed = generate_typed_slice.attach_fixed_array_in_parameter_proof(typed)
    typed = generate_typed_slice.attach_fixed_affine_centers13_proof(typed)
    return typed


def _source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


class ModulePresenceTests(unittest.TestCase):
    def test_module_carries_exactly_the_five_carriers(self):
        module = _module()
        self.assertEqual(KEYS, module.KEYS)
        self.assertEqual(PROFILES, module.PROFILES)
        self.assertEqual(frozenset(KEYS), module.STRUCT_FRONTIER_KEYS)
        for key in KEYS:
            self.assertIn(key, module._LOCKS)
            self.assertEqual(
                frozenset({"defines", "program_key",
                           "struct_frontier_profile"}),
                module.allowed_row_fields(key))
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("test:foreign")


class FrozenFactTests(unittest.TestCase):
    def test_pinned_source_identity_matches_the_live_corpus(self):
        module = _module()
        for key in KEYS:
            raw = _source_text(key).encode("utf-8")
            lock = module._LOCKS[key]
            self.assertEqual(lock["raw_bytes"], len(raw), key)
            self.assertEqual(lock["raw_sha256"],
                             hashlib.sha256(raw).hexdigest(), key)

    def test_live_analysis_rederives_every_frozen_census(self):
        module = _module()
        for key in KEYS:
            with self.subTest(key=key):
                program = _analyzed(key)
                locals_out, members_out, constructors, total_nodes, \
                    total_assigns = module._derive_census(program)
                sorted_locals, sorted_members = module._sort_census(
                    locals_out, members_out)
                lock = module._LOCKS[key]
                self.assertEqual(module._derive_structs(program),
                                 lock["structs"])
                self.assertEqual(module._derive_return_functions(program),
                                 lock["return_functions"])
                self.assertEqual(module._derive_parameters(program),
                                 lock["parameters"])
                self.assertEqual(sorted_locals, lock["locals"])
                self.assertEqual(sorted_members, lock["members"])
                self.assertEqual(constructors, ())
                self.assertEqual((total_nodes, total_assigns),
                                 (lock["total_nodes"], lock["total_assigns"]))
                structs, locals_count, members_count, nodes = CENSUS[key]
                self.assertEqual((len(lock["structs"]), len(sorted_locals),
                                  len(sorted_members), total_nodes),
                                 (structs, locals_count, members_count, nodes))


class AdmissionGreenTests(unittest.TestCase):
    def test_every_carrier_authenticates_with_the_exact_profile(self):
        module = _module()
        for key in KEYS:
            with self.subTest(key=key):
                program = _analyzed(key)
                record = module.authenticate_struct_frontier(
                    program, _source_hash(_source_text(key)),
                    PROFILES[key])
                self.assertIsNotNone(record)
                self.assertEqual(len(record.structs), CENSUS[key][0])
                self.assertEqual(len(record.locals), CENSUS[key][1])
                self.assertEqual(len(record.members), CENSUS[key][2])
                self.assertEqual(len(record.consumed), CONSUMED[key])
                self.assertEqual(
                    len(record.consumed),
                    len({id(item) for item in record.consumed}))
                self.assertIs(
                    program, module.apply_struct_frontier(
                        program, _source_hash(_source_text(key)),
                        PROFILES[key]))

    def test_record_types_are_the_live_struct_types(self):
        module = _module()
        program = _analyzed(RENDER3D_KEY)
        record = module.authenticate_struct_frontier(
            program, _source_hash(_source_text(RENDER3D_KEY)),
            PROFILES[RENDER3D_KEY])
        self.assertEqual(record.structs, tuple(program.structs))
        self.assertEqual(
            record.struct_types,
            tuple(item.type for item in program.structs))

    def test_foreign_key_without_profile_returns_none(self):
        module = _module()
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        program = analyze_program(
            parse_program(FOREIGN_SOURCE, "test:foreign", {}), "test:foreign")
        self.assertIsNone(module.authenticate_struct_frontier(
            program, _source_hash(FOREIGN_SOURCE), None))

    def test_foreign_key_with_profile_is_a_hard_failure(self):
        module = _module()
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        program = analyze_program(
            parse_program(FOREIGN_SOURCE, "test:foreign", {}), "test:foreign")
        with self.assertRaises(ValueError) as raised:
            module.authenticate_struct_frontier(
                program, _source_hash(FOREIGN_SOURCE),
                PROFILES[RENDER3D_KEY])
        self.assertIn(
            "program key is not an admitted struct-frontier carrier",
            str(raised.exception))

    def test_wrong_profile_string_is_refused(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact profile carrier required"):
            module.authenticate_struct_frontier(
                _analyzed(RENDER3D_KEY),
                _source_hash(_source_text(RENDER3D_KEY)),
                "struct-frontier-render3d-v2")

    def test_wrong_caller_source_hash_is_refused(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_struct_frontier(
                _analyzed(RENDER3D_KEY), "0" * 64, PROFILES[RENDER3D_KEY])

    def test_tampered_source_is_refused_at_the_coarse_gate(self):
        module = _module()
        raw = _source_text(RENDER3D_KEY).replace(
            "result.dist = -1.0;", "result.dist = -2.0;")
        self.assertNotEqual(raw, _source_text(RENDER3D_KEY))
        with self.assertRaisesRegex(ValueError,
                                    "source digest mismatch|raw source drift|"
                                    "normalized source drift|fingerprint drift|"
                                    "census mismatch"):
            _analyzed(RENDER3D_KEY, raw)


class ValidatorIntegrationTests(unittest.TestCase):
    def test_validator_demands_the_exact_profile_carrier(self):
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.loop_proof import (
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        key = SHAPES3D_KEY
        program = _analyzed(key)
        with self.assertRaises(generate_typed_slice.GeneratorError) as ctx:
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=_source_hash(_source_text(key)),
                source_global_literal_int_profile=(
                    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
        self.assertEqual(
            f"{key}: exact struct frontier profile carrier required",
            str(ctx.exception))

    def test_render3d_validator_accepts_and_emitter_still_rejects(self):
        """The render3d family has no other validator blocker left, so the
        profile carries it through validation; the emitter -- deliberately
        untouched this leg -- still rejects the struct type."""
        from tools.glslcpp import emit_typed_cpp, generate_typed_slice
        from tools.glslcpp.frontend.cross_builtin_profile import (
            PROFILE as CROSS_BUILTIN_PROFILE)
        from tools.glslcpp.frontend.loop_proof import (
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        key = RENDER3D_KEY
        program = _analyzed(key)
        self.assertIsNone(generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=_source_hash(_source_text(key)),
            source_global_literal_int_profile=(
                SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
            cross_builtin_profile=CROSS_BUILTIN_PROFILE,
            struct_frontier_profile=PROFILES[key]))
        with self.assertRaisesRegex(emit_typed_cpp.TypedEmissionError,
                                    "unsupported typed type IsoHit"):
            emit_typed_cpp.render_typed_cpp(
                program, key, _source_hash(_source_text(key)),
                "typed_test", "bind_test",
                source_global_literal_int_profile=(
                    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
                cross_builtin_profile=CROSS_BUILTIN_PROFILE)

    def test_probe_advances_every_carrier_past_the_struct_gate(self):
        """The ratchet's own probe: every carrier's first blocker is no
        longer the struct declaration, and no other program regressed."""
        from tools.glslcpp import corpus_ratchet
        expected_frontiers = {
            SHAPES3D_KEY: ("typed.validator", "unsupported builtin round"),
            "render/renderCubemap3d:renderCubemap3d":
                ("typed.emitter", "unsupported typed type IsoHit"),
            RENDER3D_KEY: ("typed.emitter", "unsupported typed type IsoHit"),
            "render/renderLit3d:renderLit3d":
                ("typed.validator", "unsupported builtin any"),
            "synth3d/flythrough3d:precompute":
                ("typed.validator", "unsupported parameter direction out"),
        }
        for key in KEYS:
            with self.subTest(key=key):
                blocker = corpus_ratchet.probe_program(
                    key, _source_text(key).encode("utf-8"), _effect(key))
                self.assertIsNotNone(blocker)
                stage, diagnostic = expected_frontiers[key]
                self.assertEqual(stage, blocker["stage"])
                self.assertIn(diagnostic, blocker["diagnostic"])


class CorpusCensusTests(unittest.TestCase):
    def test_struct_declarations_belong_exactly_to_the_five_carriers(self):
        """Every pending program that declares a top-level struct is either
        an admitted carrier or is blocked earlier than the struct gate
        (palette3d's global declarations, renderLandscape3d's tan variant):
        none of them reaches the emitter past an unadmitted struct."""
        module = _module()
        declaring = set()
        for key in (item["program_key"] for item in _pending()["pending"]):
            try:
                source = _source_text(key)
            except FileNotFoundError:
                continue  # adapter-status programs carry no committed GLSL
            import re
            if re.search(r"^struct\s+\w+", source, re.MULTILINE):
                declaring.add(key)
        self.assertLessEqual(frozenset(KEYS), declaring)
        pending = {item["program_key"]: item for item in _pending()["pending"]}
        for key in declaring - frozenset(KEYS):
            self.assertNotEqual("typed.emitter", pending[key]["blocker"]["stage"],
                                key)
        for key in KEYS:
            self.assertIn(key, declaring)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
