from __future__ import annotations

import dataclasses
import copy
import json
from unittest import mock
from pathlib import Path
import unittest

from tools.glslcpp import check_corpus, generate_typed_slice
from tools.glslcpp import emit_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import moodscape_frontend_profile as profile
from tools.glslcpp.frontend.typed_ir import TypedStatement


ROOT = Path(__file__).resolve().parents[1]
KEY = profile.KEY


def analyzed():
    corpus = check_corpus._corpus_root(ROOT)
    manifest = json.loads((corpus / "manifest.json").read_text())
    entry = next(item for item in manifest["programs"] if item["program_key"] == KEY)
    raw = (corpus / entry["source"]).read_text()
    return analyze_program(parse_program(raw, KEY, generate_typed_slice._defaults(ROOT, KEY)), KEY)


class MoodscapePreparedFrontendTests(unittest.TestCase):
    def _row_like_generation_inputs(self, profile_name=profile.PROFILE):
        slice_spec = copy.deepcopy(generate_typed_slice.load_slice(ROOT))
        slice_spec["programs"] = [{
            "defines": {"COLOR_MODE": 2, "NOISE_TYPE": 10},
            "program_key": KEY,
            "moodscape_frontend_profile": profile_name,
        }]
        corpus = check_corpus._corpus_root(ROOT)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == KEY)
        return slice_spec, entry

    def _generate_row_like_outputs(self, slice_spec, entry):
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=slice_spec), \
                mock.patch.object(check_corpus, "validate_corpus"), \
                mock.patch.object(
                    generate_typed_slice.check_semantics, "semantic_report",
                    return_value={"body_success": 212}), \
                mock.patch.object(generate_typed_slice, "_source_entries",
                                  return_value=[entry]):
            return generate_typed_slice.generate_outputs(ROOT)

    def test_prepared_registry_and_runtime_contract(self):
        self.assertEqual((), profile.KEYS)
        self.assertEqual((KEY,), profile.PREPARED_KEYS)
        self.assertEqual({KEY: profile.PROFILE}, profile.PROFILES)
        self.assertEqual((("COLOR_MODE", "int", "2"), ("NOISE_TYPE", "int", "10")), profile.DEFINES)
        self.assertEqual(
            (("time", "float"), ("seed", "int"), ("wrap", "bool"),
             ("resolution", "vec2"), ("tileOffset", "vec2"),
             ("fullResolution", "vec2"), ("noiseScale", "float"),
             ("refractAmt", "float"), ("speed", "float"),
             ("hueRotation", "float"), ("hueRange", "float"),
             ("intensity", "float"), ("ridges", "bool")),
            profile.SOURCE_UNIFORMS)
        self.assertEqual(
            (("time", "float"), ("seed", "int32"), ("wrap", "bool"),
             ("resolution", "Vec2"), ("tileOffset", "Vec2"),
             ("fullResolution", "Vec2"), ("noiseScale", "float"),
             ("refractAmt", "float"), ("speed", "float"),
             ("hueRotation", "float"), ("hueRange", "float"),
             ("intensity", "float"), ("ridges", "bool")),
            profile.RUNTIME_UNIFORM_ABI)
        self.assertEqual(("fragColor", "vec4", "Vec4", "output"), profile.OUTPUT_ABI)
        self.assertEqual(frozenset({"defines", "program_key", "moodscape_frontend_profile"}), profile.ALLOWED_ROW_FIELDS[KEY])

    def test_authentication_proves_live_and_dead_closures(self):
        program = analyzed()
        proof = profile.authenticate_moodscape_frontend(program, profile.RAW_SHA256, profile.PROFILE)
        self.assertEqual((85, 90, 93, 94, 95, 96, 99, 100, 106, 107),
                         tuple(item.id for item in proof.reachable_functions))
        self.assertEqual((83, 84, 86, 87, 88, 89, 91, 92, 97, 98, 101, 102, 103, 104, 105),
                         tuple(item.id for item in proof.dead_functions))
        self.assertEqual(("fwdA", "fwdB", "invB", "invA"), tuple(item.symbol.name for item in proof.matrix_globals))
        self.assertEqual(profile.FLOAT_BITS_SPAN, f"{proof.float_bits_node.span.start_line}:{proof.float_bits_node.span.start_column}-{proof.float_bits_node.span.end_line}:{proof.float_bits_node.span.end_column}")
        self.assertEqual(len(proof.consumed_objects), len({id(item) for item in proof.consumed_objects}))
        self.assertTrue(any(type(item) is TypedStatement
                            for item in proof.consumed_objects))
        self.assertIs(profile.authenticate_moodscape_frontend(
            program, profile.RAW_SHA256, profile.PROFILE).program, program)
        self.assertIs(profile.verify_moodscape_frontend(program, proof), proof)

    def test_source_and_identity_mutations_fail_closed(self):
        program = analyzed()
        for candidate, source_hash, selected in (
                (program, "0" * 64, profile.PROFILE),
                (program, profile.RAW_SHA256, "wrong-profile"),
                (dataclasses.replace(program, key="foreign:key"), profile.RAW_SHA256, profile.PROFILE),
        ):
            with self.assertRaisesRegex(ValueError, profile.PROFILE):
                profile.authenticate_moodscape_frontend(candidate, source_hash, selected)

    def test_dead_float_bits_site_is_identity_bound(self):
        program = analyzed()
        proof = profile.authenticate_moodscape_frontend(program, profile.RAW_SHA256, profile.PROFILE)
        mutated_node = dataclasses.replace(proof.float_bits_node, callee="uintBitsToFloat")
        changed = profile.replace_expression(program, proof.float_bits_node, mutated_node)
        with self.assertRaisesRegex(ValueError, "lock mismatch|dead-site"):
            profile.authenticate_moodscape_frontend(changed, profile.RAW_SHA256, profile.PROFILE)

    def test_apply_projects_only_authenticated_dead_closure(self):
        program = analyzed()
        projected = profile.apply_moodscape_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        self.assertIsNot(projected, program)
        self.assertIs(projected.raw_source, program.raw_source)
        self.assertIs(projected.source, program.source)
        self.assertEqual((85, 90, 93, 94, 95, 96, 99, 100, 106, 107),
                         tuple(item.id for item in projected.functions))
        self.assertEqual(
            ("time", "seed", "wrap", "resolution", "tileOffset",
             "fullResolution", "noiseScale", "refractAmt", "speed",
             "hueRotation", "hueRange", "intensity", "ridges", "fragColor"),
            tuple(item.symbol.name for item in projected.declarations))
        self.assertEqual((), tuple(item for item in projected.declarations
                                   if item.type.display() == "mat3"))
        proof = profile.authenticate_moodscape_projection(
            projected, profile.RAW_SHA256, profile.PROFILE)
        self.assertIs(
            profile.verify_moodscape_projection(projected, proof), proof)
        self.assertEqual((85, 90, 93, 94, 95, 96, 99, 100, 106, 107),
                         tuple(item.id for item in proof.functions))
        self.assertEqual(profile.PROJECTED_FUNCTIONS_SHA256, proof.functions_sha256)

    def test_validator_and_emitter_require_independent_projected_profile(self):
        source_hash = profile.RAW_SHA256
        projected = profile.apply_moodscape_frontend(
            analyzed(), source_hash, profile.PROFILE)
        generate_typed_slice.validate_capabilities(
            projected, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            moodscape_frontend_profile=profile.PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            projected, KEY, source_hash,
            moodscape_frontend_profile=profile.PROFILE)
        self.assertIn("// Source SHA-256: " + source_hash, rendered)
        self.assertNotIn("fwdA", rendered)
        self.assertNotIn("floatBitsToUint", rendered)
        self.assertIn(
            'std::make_shared<typed_kernel::State>(bindings.get_number("time"), '
            'bindings.get<std::int32_t>("seed"), bindings.get<bool>("wrap"), '
            'bindings.get<glsl::Vec2>("resolution"), '
            'bindings.get<glsl::Vec2>("tileOffset"), '
            'bindings.get<glsl::Vec2>("fullResolution"), '
            'bindings.get_number("noiseScale"), bindings.get_number("refractAmt"), '
            'bindings.get_number("speed"), bindings.get_number("hueRotation"), '
            'bindings.get_number("hueRange"), bindings.get_number("intensity"), '
            'bindings.get<bool>("ridges"))', rendered)

    def test_frontend_verifier_rejects_forged_or_truncated_proof_ledger(self):
        program = analyzed()
        proof = profile.authenticate_moodscape_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        statement_index = next(
            index for index, item in enumerate(proof.consumed_objects)
            if type(item) is TypedStatement)
        forged_statement_ledger = list(proof.consumed_objects)
        forged_statement_ledger[statement_index] = copy.deepcopy(
            forged_statement_ledger[statement_index])
        forged = (
            proof._replace(consumed_objects=()),
            proof._replace(consumed_objects=proof.consumed_objects[:-1]),
            proof._replace(consumed_objects=tuple(reversed(proof.consumed_objects))),
            proof._replace(consumed_objects=(copy.deepcopy(proof.consumed_objects[0]),) + proof.consumed_objects[1:]),
            proof._replace(consumed_objects=tuple(forged_statement_ledger)),
            proof._replace(functions=()),
            proof._replace(functions=proof.functions[:-1]),
            proof._replace(functions=tuple(reversed(proof.functions))),
            proof._replace(functions=(copy.deepcopy(proof.functions[0]),) + proof.functions[1:]),
            proof._replace(expression_nodes=()),
            proof._replace(expression_nodes=proof.expression_nodes[:-1]),
            proof._replace(expression_nodes=tuple(reversed(proof.expression_nodes))),
            proof._replace(program_key="forged:key"),
            proof._replace(profile="forged-profile"),
            proof._replace(source_hash="0" * 64),
            proof._replace(normalized_source_hash="0" * 64),
            proof._replace(source_uniforms=()),
            proof._replace(runtime_uniform_abi=()),
        )
        for candidate in forged:
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(ValueError, profile.PROFILE):
                    profile.verify_moodscape_frontend(program, candidate)

    def test_projection_verifier_rejects_forged_or_truncated_proof_ledger(self):
        projected = profile.apply_moodscape_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        proof = profile.authenticate_moodscape_projection(
            projected, profile.RAW_SHA256, profile.PROFILE)
        statement_index = next(
            index for index, item in enumerate(proof.consumed_objects)
            if type(item) is TypedStatement)
        forged_statement_ledger = list(proof.consumed_objects)
        forged_statement_ledger[statement_index] = copy.deepcopy(
            forged_statement_ledger[statement_index])
        forged = (
            proof._replace(consumed_objects=()),
            proof._replace(consumed_objects=proof.consumed_objects[:-1]),
            proof._replace(consumed_objects=tuple(reversed(proof.consumed_objects))),
            proof._replace(consumed_objects=(copy.deepcopy(proof.consumed_objects[0]),) + proof.consumed_objects[1:]),
            proof._replace(consumed_objects=tuple(forged_statement_ledger)),
            proof._replace(functions=()),
            proof._replace(functions=proof.functions[:-1]),
            proof._replace(functions=tuple(reversed(proof.functions))),
            proof._replace(functions=(copy.deepcopy(proof.functions[0]),) + proof.functions[1:]),
            proof._replace(declarations=()),
            proof._replace(declarations=proof.declarations[:-1]),
            proof._replace(declarations=tuple(reversed(proof.declarations))),
            proof._replace(declarations=(copy.deepcopy(proof.declarations[0]),) + proof.declarations[1:]),
            proof._replace(program_key="forged:key"),
            proof._replace(profile="forged-profile"),
            proof._replace(source_hash="0" * 64),
            proof._replace(normalized_source_hash="0" * 64),
            proof._replace(source_uniforms=()),
            proof._replace(runtime_uniform_abi=()),
        )
        for candidate in forged:
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(ValueError, profile.PROFILE):
                    profile.verify_moodscape_projection(projected, candidate)

    def test_projected_source_or_reachability_mutation_fails_closed(self):
        projected = profile.apply_moodscape_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        changed = dataclasses.replace(
            projected, functions=tuple(reversed(projected.functions)))
        with self.assertRaisesRegex(ValueError, "projection|function"):
            profile.authenticate_moodscape_projection(
                changed, profile.RAW_SHA256, profile.PROFILE)

    def test_validator_and_emitter_reject_unprofiled_moodscape(self):
        projected = profile.apply_moodscape_frontend(
            analyzed(), profile.RAW_SHA256, profile.PROFILE)
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "exact Moodscape frontend profile carrier required"):
            generate_typed_slice.validate_capabilities(
                projected, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=profile.RAW_SHA256)
        with self.assertRaisesRegex(ValueError, "exact Moodscape frontend profile carrier required"):
            emit_typed_cpp.render_typed_cpp(
                projected, KEY, profile.RAW_SHA256)

    def test_row_like_slice_load_apply_and_generate_is_single_moodscape_delta(self):
        slice_spec, entry = self._row_like_generation_inputs()
        outputs = self._generate_row_like_outputs(slice_spec, entry)
        manifest = json.loads(
            outputs["src/typed_generated/typed_manifest.json"].decode("utf-8"))
        cpp = outputs["src/typed_generated/typed_slice.cpp"].decode("utf-8")
        self.assertEqual(1, len(manifest["programs"]))
        self.assertEqual(KEY, manifest["programs"][0]["program_key"])
        self.assertEqual(profile.PROFILE,
                         manifest["programs"][0]["moodscape_frontend_profile"])
        self.assertEqual(1, cpp.count("// Typed IR program: " + KEY))
        # Re-derived 2026-08-25: the DSL/Task-7 emitter writes a second table,
        # `kCanonicalRoutes`, into the same translation unit as `kCatalog`, so
        # every program key is now quoted TWICE and the bare `== 1` this
        # replaces can no longer hold. Asserting the count PER SECTION rather
        # than a bare `== 2` keeps the isolation proof and sharpens it: exactly
        # one catalog row, exactly one canonical route, and the key quoted
        # nowhere in the emitted program body. The three slices partition the
        # whole file, so this also pins the total. See
        # task-7-typed-generator-census-repair.md.
        quoted = '"' + KEY + '"'
        catalog_at = cpp.index("constexpr std::array<KernelFactory")
        routes_at = cpp.index("constexpr std::array<FactoryRoute")
        self.assertLess(catalog_at, routes_at)
        self.assertEqual(
            (0, 1, 1),
            (cpp[:catalog_at].count(quoted),
             cpp[catalog_at:routes_at].count(quoted),
             cpp[routes_at:].count(quoted)))
        self.assertIn("typed_0::State", cpp)
        self.assertIn("bindings.get<std::int32_t>(\"seed\")", cpp)

    def test_row_like_slice_rejects_missing_or_wrong_moodscape_profile(self):
        for selected in (None, "wrong-moodscape-profile"):
            with self.subTest(selected=selected):
                slice_spec, entry = self._row_like_generation_inputs(selected)
                if selected is None:
                    slice_spec["programs"][0].pop("moodscape_frontend_profile")
                with self.assertRaisesRegex(
                        generate_typed_slice.GeneratorError,
                        "exact Moodscape frontend profile carrier required|metadata mismatch"):
                    self._generate_row_like_outputs(slice_spec, entry)


if __name__ == "__main__":
    unittest.main()
