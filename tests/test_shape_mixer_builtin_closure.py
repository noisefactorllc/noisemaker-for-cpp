from __future__ import annotations

import dataclasses
import hashlib
import importlib
import importlib.util
import copy
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "classicNoisedeck/shapeMixer:shapeMixer"
PROFILE = "shape-mixer-builtin-closure-v1"
SCALAR_XOR_PROFILE = "scalar-uint-xor-v1"
RAW_SHA256 = "704157151a2aa7e0192bd5b3483d5f1a5532a15a6e3f6a3ee0ba93ce70f8a9e4"
SOURCE = (
    ROOT
    / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
    / "sources/classicNoisedeck/shapeMixer/shapeMixer.glsl"
)
MODULE = "tools.glslcpp.frontend.shape_mixer_builtin_profile"


def _profile():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError("Shape Mixer builtin-closure profile module is absent")
    return importlib.import_module(MODULE)


def _analyzed(*, key: str = KEY, defines: dict[str, object] | None = None):
    raw = SOURCE.read_text(encoding="utf-8")
    runtime_defines = {"LOOP_OFFSET": 10} if defines is None else defines
    return analyze_program(parse_program(raw, key, runtime_defines), key)


def _authenticate_with_refrozen_coarse_locks(profile, original, mutated):
    """Exercise fine-grained locks after all coarse tree locks are re-frozen."""
    companion = profile.authenticate_scalar_uint_xor(
        original, RAW_SHA256, SCALAR_XOR_PROFILE)
    role_hashes = dict(profile._FUNCTION_ROLE_HASHES)
    mutated_main = next(item for item in mutated.functions
                        if item.name == "main")
    role_hashes[112] = profile._sha(mutated_main)
    inventory = tuple(
        (item.signature.id, item.name, item.return_type.display(),
         len(item.parameters), len(item.body), profile._span(item))
        for item in mutated.functions)
    names = {item.id: item.name for item in mutated.functions}
    calls = {item.id: [] for item in mutated.functions}
    for function, item, _, _, _ in profile._located(mutated):
        if item.kind == "call" and item.signature_id in names:
            calls[function.id].append(item.signature_id)
    call_graph = tuple((item.id, tuple(calls[item.id]))
                       for item in mutated.functions)
    with mock.patch.multiple(
            profile,
            _FUNCTIONS_SHA256=profile._sha(mutated.functions),
            _WHOLE_SHA256=profile._whole(mutated),
            _FUNCTION_INVENTORY_SHA256=profile._sha(inventory),
            _CALL_GRAPH_SHA256=profile._sha(call_graph),
            _FUNCTION_ROLE_HASHES=role_hashes):
        with mock.patch.object(
                profile, "_PROFILE_SHA256",
                profile._sha(profile._profile_tuple())), mock.patch.object(
                    profile, "authenticate_scalar_uint_xor",
                    return_value=companion):
            return profile.authenticate_shape_mixer_builtin_closure(
                mutated, RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE)


class ShapeMixerBuiltinClosureTests(unittest.TestCase):
    def test_live_slice_has_one_exact_shape_mixer_row_at_ordinal_fourteen(self):
        spec = generate_typed_slice.load_slice(ROOT)
        rows = spec["programs"]
        keys = [row["program_key"] for row in rows]

        # Live-state pin. Shapes183 inserted at ordinal 8 and
        # `synth/shape:shape` at ordinal 181 and
        # `filter/normalMap:normalMap` at ordinal 66, all after Shape Mixer, so
        # Shape Mixer's own ordinal 7 and row were untouched and only the slice
        # size and key SHA moved. cellRefract (186) is the first landing to
        # sort AHEAD of Shape Mixer -- ordinal 2, between cellNoise and
        # coalesce -- so Shape Mixer moves from ordinal 7 to 8 and Shapes from
        # 8 to 9; the row itself is unchanged. kaleido (row 187, ordinal 6)
        # lands after coalesce and before Shape Mixer's neighbors' peers, so
        # kaleido sorts between coalesce and Shape Mixer, so Shape Mixer
        # moves from ordinal 8 to 9 and Shapes from 9 to 10; the row itself
        # is unchanged and the slice grows to 187 keys. effects (row 188,
        # ordinal 5) sorts ahead of Shape Mixer too, moving it to 10 and
        # Shapes to 11; the row itself is unchanged and the slice grows to
        # 188 keys. wobble (row 189) sorts BEHIND Shapes, so both ordinals
        # and both rows are unchanged and only the slice grows to 189 keys.
        # Later admitted rows grow the live slice to 211. Shape Mixer remains
        # at its exact sorted position, with Shapes immediately following it.
        self.assertEqual(211, len(rows))
        self.assertEqual(211, len(set(keys)))
        self.assertEqual(KEY, keys[15])
        self.assertEqual("classicNoisedeck/shapes:shapes", keys[16])
        self.assertEqual(
            {
                "defines": {"LOOP_OFFSET": 10},
                "program_key": KEY,
                "scalar_uint_xor_profile": SCALAR_XOR_PROFILE,
                "shape_mixer_builtin_profile": PROFILE,
            },
            rows[15],
        )
        self.assertEqual(
            "29a148b26cfe4f550ac82325810655eb0e5ffad2c3a4e5241e42600bac9f76c1",
            hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest(),
        )
        self.assertEqual(44, len(spec["capabilities"]))
        self.assertEqual(17, len(spec["types"]))
        self.assertEqual(17, len(spec["binary_operators"]))
        self.assertEqual(6, len(spec["assignment_operators"]))

    def test_exact_profile_returns_candidate_owned_complete_closure(self):
        profile = _profile()
        program = _analyzed()
        proof = profile.authenticate_shape_mixer_builtin_closure(
            program, RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE)

        self.assertIs(proof._candidate, program)
        self.assertIs(
            profile.apply_shape_mixer_builtin_closure(
                program, RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE),
            program,
        )
        self.assertEqual(
            ("672:17-672:49", "625:17-625:49"),
            tuple(profile._span(item) for item in proof.reflect_nodes),
        )
        self.assertEqual(
            ("675:17-675:48", "628:17-628:48"),
            tuple(profile._span(item) for item in proof.refract_nodes),
        )
        self.assertEqual("619:17-619:45", profile._span(proof.wide_mod_node))
        self.assertEqual("411:21-411:46", profile._span(proof.bit_ingress))
        self.assertEqual(
            (
                "116:13-116:22",
                "117:13-117:20",
                "117:23-117:32",
                "119:13-119:20",
                "119:35-119:44",
            ),
            tuple(profile._span(item) for item in proof.dynamic_indexes),
        )
        self.assertEqual(11, len(proof.exceptional_nodes))
        self.assertEqual(11, len({id(item) for item in proof.exceptional_nodes}))
        self.assertEqual(3, len(proof.companion_scalar_uint_xors))

    def test_exact_profile_authenticates_twenty_owned_blend_mode_guards(self):
        profile = _profile()
        program = _analyzed()
        proof = profile.authenticate_shape_mixer_builtin_closure(
            program, RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE)

        guards = getattr(proof, "blend_mode_guards", None)
        self.assertIsNotNone(guards)
        assert guards is not None
        self.assertEqual(20, len(guards))
        self.assertEqual(20, len({id(item) for item in guards}))
        owners = tuple(
            next(item for item in program.functions if item.id == owner_id)
            for owner_id in (99, 100))
        for owner_index, owner in enumerate(owners):
            mode = next(item for item in owner.parameters
                        if item.name == "mode")
            current = owner.body[2]
            owner_guards = guards[owner_index * 10:(owner_index + 1) * 10]
            for expected_mode, guard in enumerate(owner_guards):
                with self.subTest(owner=owner.id, mode=expected_mode):
                    self.assertEqual("if", current.kind)
                    self.assertEqual(1, len(current.expressions))
                    self.assertIs(guard, current.expressions[0])
                    self.assertEqual("binary", guard.kind)
                    self.assertEqual("==", guard.operator)
                    self.assertEqual("bool", guard.type.display())
                    self.assertEqual(2, len(guard.children))
                    left, right = guard.children
                    self.assertEqual("id", left.kind)
                    self.assertIs(left.symbol, mode)
                    self.assertEqual("int", left.type.display())
                    self.assertEqual("literal", right.kind)
                    self.assertEqual("int", right.type.display())
                    self.assertEqual(expected_mode, right.literal_value)
                    self.assertEqual(2, len(current.children))
                    current = current.children[1]
            self.assertEqual("block", current.kind)

    def test_authenticated_blend_ladders_emit_one_balanced_tree_per_overload(self):
        source = emit_typed_cpp.render_typed_cpp(
            _analyzed(), KEY, RAW_SHA256,
            "shape_mixer_balanced", "bind_shape_mixer_balanced",
            scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
            shape_mixer_builtin_profile=PROFILE,
        )

        self.assertEqual(2, source.count(
            "if ((mode < std::int32_t(0)) || "
            "(mode > std::int32_t(9))) {"))
        self.assertEqual(2, source.count(
            "else if (mode < std::int32_t(5)) {"))
        self.assertEqual(2, source.count(
            "if (mode < std::int32_t(2)) {"))
        self.assertEqual(2, source.count(
            "else if (mode < std::int32_t(8)) {"))
        for mode in (0, 2, 3, 5, 6, 8):
            self.assertEqual(
                2, source.count(f"mode == std::int32_t({mode})"))
        for mode in (1, 4, 7, 9):
            self.assertNotIn(f"mode == std::int32_t({mode})", source)
        self.assertNotIn("shape_mixer_mode_is", source)
        self.assertNotIn("volatile", source)

    def test_profile_rejects_wrong_carriers_key_source_and_define(self):
        profile = _profile()
        program = _analyzed()
        cases = (
            (program, RAW_SHA256, None, SCALAR_XOR_PROFILE),
            (program, RAW_SHA256, "wrong", SCALAR_XOR_PROFILE),
            (program, RAW_SHA256, PROFILE, None),
            (program, RAW_SHA256, PROFILE, "wrong"),
            (program, "0" * 64, PROFILE, SCALAR_XOR_PROFILE),
            (dataclasses.replace(program, key="filter/other:other"),
             RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE),
            (_analyzed(defines={"LOOP_OFFSET": 9}),
             RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE),
        )
        for candidate, source_hash, carrier, scalar_carrier in cases:
            with self.subTest(key=candidate.key, carrier=carrier,
                              scalar_carrier=scalar_carrier):
                with self.assertRaises(ValueError):
                    profile.authenticate_shape_mixer_builtin_closure(
                        candidate, source_hash, carrier, scalar_carrier)

    def test_validator_and_emitter_both_require_the_exact_profile(self):
        program = _analyzed()
        generate_typed_slice.validate_capabilities(
            program,
            generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=RAW_SHA256,
            scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
            shape_mixer_builtin_profile=PROFILE,
        )
        with self.assertRaisesRegex(
                emit_typed_cpp.TypedEmissionError,
                r"classicNoisedeck/shapeMixer:shapeMixer:1:1: "
                r"exact Shape Mixer builtin profile carrier required"):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, RAW_SHA256,
                "shape_mixer_validator_only", "bind_shape_mixer_validator_only",
                scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
            )

    def test_emitter_routes_only_authenticated_shape_mixer_sites(self):
        program = _analyzed()
        source = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256,
            "shape_mixer_emitted", "bind_shape_mixer_emitted",
            scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
            shape_mixer_builtin_profile=PROFILE,
        )
        self.assertEqual(1, source.count("shape_mixer_reflect_scalar("))
        self.assertEqual(1, source.count("shape_mixer_refract_scalar("))
        self.assertEqual(1, source.count("shape_mixer_mod_vec3("))
        self.assertEqual(1, source.count("glsl::reflect("))
        self.assertEqual(1, source.count("glsl::refract("))
        self.assertEqual(1, source.count("noisemaker::float_bits_to_uint("))

    def test_validator_and_emitter_independently_reauthenticate_owned_proofs(self):
        profile = _profile()
        first = _analyzed()
        second = _analyzed()
        foreign = profile.authenticate_shape_mixer_builtin_closure(
            second, RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE)

        with mock.patch.object(
                generate_typed_slice,
                "authenticate_shape_mixer_builtin_closure",
                wraps=profile.authenticate_shape_mixer_builtin_closure) as auth:
            generate_typed_slice.validate_capabilities(
                first,
                generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256,
                scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                shape_mixer_builtin_profile=PROFILE,
            )
            self.assertEqual(1, auth.call_count)
        with mock.patch.object(
                emit_typed_cpp,
                "authenticate_shape_mixer_builtin_closure",
                wraps=profile.authenticate_shape_mixer_builtin_closure) as auth:
            emit_typed_cpp.render_typed_cpp(
                first, KEY, RAW_SHA256,
                scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                shape_mixer_builtin_profile=PROFILE,
            )
            self.assertEqual(1, auth.call_count)

        for boundary, owner in (
                (generate_typed_slice, "validator"),
                (emit_typed_cpp, "emitter")):
            with self.subTest(boundary=owner), mock.patch.object(
                    boundary,
                    "authenticate_shape_mixer_builtin_closure",
                    return_value=foreign), self.assertRaises(
                        (generate_typed_slice.GeneratorError
                         if owner == "validator"
                         else emit_typed_cpp.TypedEmissionError)):
                if owner == "validator":
                    boundary.validate_capabilities(
                        first,
                        generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=RAW_SHA256,
                        scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                        shape_mixer_builtin_profile=PROFILE,
                    )
                else:
                    boundary.render_typed_cpp(
                        first, KEY, RAW_SHA256,
                        scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                        shape_mixer_builtin_profile=PROFILE,
                    )

    def test_validator_and_emitter_reject_same_candidate_role_forgery(self):
        profile = _profile()
        program = _analyzed()
        genuine = profile.authenticate_shape_mixer_builtin_closure(
            program, RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE)
        other_owned_statement = next(
            item for function in program.functions if function.name == "main"
            for item in function.body)
        forgeries = {
            "deep-copy": copy.deepcopy(genuine),
            "reflect-order": dataclasses.replace(
                genuine, reflect_nodes=genuine.reflect_nodes[::-1]),
            "refract-order": dataclasses.replace(
                genuine, refract_nodes=genuine.refract_nodes[::-1]),
            "wide-mod-role": dataclasses.replace(
                genuine, wide_mod_node=genuine.exceptional_nodes[0]),
            "dynamic-index-order": dataclasses.replace(
                genuine, dynamic_indexes=genuine.dynamic_indexes[::-1]),
            "bit-ingress-role": dataclasses.replace(
                genuine, bit_ingress=genuine.exceptional_nodes[0]),
            "exceptional-order": dataclasses.replace(
                genuine, exceptional_nodes=genuine.exceptional_nodes[::-1]),
            "exceptional-duplicate": dataclasses.replace(
                genuine,
                exceptional_nodes=(genuine.exceptional_nodes[0],
                                   *genuine.exceptional_nodes[:-1])),
            "exceptional-suppressed": dataclasses.replace(
                genuine,
                exceptional_nodes=genuine.exceptional_nodes[:-1]),
            "exceptional-extra": dataclasses.replace(
                genuine,
                exceptional_nodes=(*genuine.exceptional_nodes,
                                   genuine.exceptional_nodes[0])),
            "parent-order": dataclasses.replace(
                genuine,
                exceptional_parents=genuine.exceptional_parents[::-1]),
            "loop-ancestry": dataclasses.replace(
                genuine, linear_srgb_loop=other_owned_statement),
            "companion-order": dataclasses.replace(
                genuine,
                companion_scalar_uint_xors=(
                    genuine.companion_scalar_uint_xors[::-1])),
        }

        second = _analyzed()
        foreign = profile.authenticate_shape_mixer_builtin_closure(
            second, RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE)
        guards = genuine.blend_mode_guards
        guard_forgeries = {
            "guard-foreign": dataclasses.replace(
                genuine, blend_mode_guards=foreign.blend_mode_guards),
            "guard-deep-copy": dataclasses.replace(
                genuine, blend_mode_guards=copy.deepcopy(guards)),
            "guard-reorder": dataclasses.replace(
                genuine, blend_mode_guards=guards[::-1]),
            "guard-duplicate": dataclasses.replace(
                genuine, blend_mode_guards=(guards[0], *guards[:-1])),
            "guard-suppressed": dataclasses.replace(
                genuine, blend_mode_guards=guards[:-1]),
            "guard-extra": dataclasses.replace(
                genuine, blend_mode_guards=(*guards, guards[0])),
            "guard-overload-order": dataclasses.replace(
                genuine, blend_mode_guards=(*guards[10:], *guards[:10])),
            "guard-cross-overload-swap": dataclasses.replace(
                genuine,
                blend_mode_guards=(guards[10], *guards[1:10], guards[0],
                                   *guards[11:])),
        }
        forgeries.update(guard_forgeries)

        for name, forged in forgeries.items():
            for boundary, error in (
                    (generate_typed_slice,
                     generate_typed_slice.GeneratorError),
                    (emit_typed_cpp, emit_typed_cpp.TypedEmissionError)):
                with self.subTest(name=name, boundary=boundary.__name__), \
                        mock.patch.object(
                            boundary,
                            "authenticate_shape_mixer_builtin_closure",
                            return_value=forged), self.assertRaises(error):
                    if boundary is generate_typed_slice:
                        boundary.validate_capabilities(
                            program,
                            generate_typed_slice.APPROVED_CAPABILITIES,
                            source_hash=RAW_SHA256,
                            scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                            shape_mixer_builtin_profile=PROFILE,
                        )
                    else:
                        boundary.render_typed_cpp(
                            program, KEY, RAW_SHA256,
                            scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                            shape_mixer_builtin_profile=PROFILE,
                        )

    def test_guard_consumers_reject_forgeries_even_when_matcher_is_bypassed(self):
        profile = _profile()
        program = _analyzed()
        genuine = profile.authenticate_shape_mixer_builtin_closure(
            program, RAW_SHA256, PROFILE, SCALAR_XOR_PROFILE)
        guards = genuine.blend_mode_guards
        forged_sequences = {
            "suppressed": guards[:-1],
            "duplicate": (guards[0], *guards[:-1]),
            "extra": (*guards, guards[0]),
            "reordered": guards[::-1],
            "cross-overload": (*guards[10:], *guards[:10]),
        }
        for name, sequence in forged_sequences.items():
            forged = dataclasses.replace(
                genuine, blend_mode_guards=sequence)
            for boundary, error in (
                    (generate_typed_slice,
                     generate_typed_slice.GeneratorError),
                    (emit_typed_cpp, emit_typed_cpp.TypedEmissionError)):
                with self.subTest(name=name, boundary=boundary.__name__), \
                        mock.patch.object(
                            boundary,
                            "authenticate_shape_mixer_builtin_closure",
                            return_value=forged), mock.patch.object(
                                boundary,
                                "_shape_mixer_proof_matches_candidate",
                                return_value=True), self.assertRaises(error):
                    if boundary is generate_typed_slice:
                        boundary.validate_capabilities(
                            program,
                            generate_typed_slice.APPROVED_CAPABILITIES,
                            source_hash=RAW_SHA256,
                            scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                            shape_mixer_builtin_profile=PROFILE,
                        )
                    else:
                        boundary.render_typed_cpp(
                            program, KEY, RAW_SHA256,
                            scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                            shape_mixer_builtin_profile=PROFILE,
                        )

    def test_balanced_body_consumer_rejects_forged_candidate_records(self):
        records_builder = getattr(
            emit_typed_cpp, "_shape_mixer_ladder_records", None)
        self.assertIsNotNone(records_builder)
        assert records_builder is not None
        program = _analyzed()
        records = records_builder(program)
        self.assertEqual(2, len(records))
        for root, guards, bodies in records:
            self.assertEqual(10, len(guards))
            self.assertEqual(11, len(bodies))
            self.assertEqual(11, len({id(item) for item in bodies}))
            self.assertIs(root.expressions[0], guards[0])

        scalar_root, scalar_guards, scalar_bodies = records[0]
        vector_root, vector_guards, vector_bodies = records[1]
        forgeries = {
            "body-suppressed": (
                (scalar_root, scalar_guards, scalar_bodies[:-1]),
                records[1]),
            "body-duplicate": (
                (scalar_root, scalar_guards,
                 (scalar_bodies[0], *scalar_bodies[:-1])),
                records[1]),
            "body-extra": (
                (scalar_root, scalar_guards,
                 (*scalar_bodies, scalar_bodies[0])),
                records[1]),
            "body-reordered": (
                (scalar_root, scalar_guards, scalar_bodies[::-1]),
                records[1]),
            "body-substituted": (
                (scalar_root, scalar_guards,
                 (vector_bodies[0], *scalar_bodies[1:])),
                records[1]),
            "root-substituted": (
                (vector_root, scalar_guards, scalar_bodies),
                records[1]),
        }
        for name, forged_records in forgeries.items():
            with self.subTest(name=name), mock.patch.object(
                    emit_typed_cpp,
                    "_shape_mixer_proof_matches_candidate",
                    return_value=True), mock.patch.object(
                        emit_typed_cpp, "_shape_mixer_ladder_records",
                        return_value=forged_records), self.assertRaises(
                            emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, RAW_SHA256,
                    scalar_uint_xor_profile=SCALAR_XOR_PROFILE,
                    shape_mixer_builtin_profile=PROFILE,
                )

    def test_profile_rejects_blend_reparenting_and_palette_branch_bypasses(self):
        profile = _profile()
        program = _analyzed()
        main = next(item for item in program.functions if item.name == "main")
        palette_branch = main.body[16]
        self.assertEqual("if", palette_branch.kind)
        self.assertEqual("726:5-748:6", profile._span(palette_branch))

        vector_blend_statement = palette_branch.children[0].children[0]
        shortened_true = dataclasses.replace(
            palette_branch.children[0],
            children=palette_branch.children[0].children[1:])
        shortened_branch = dataclasses.replace(
            palette_branch,
            children=(shortened_true, palette_branch.children[1]))
        vector_top_level_main = dataclasses.replace(
            main,
            body=(*main.body[:16], vector_blend_statement,
                  shortened_branch, *main.body[17:]))

        scalar_blend_statement = main.body[14]
        expanded_true = dataclasses.replace(
            palette_branch.children[0],
            children=(scalar_blend_statement,
                      *palette_branch.children[0].children))
        scalar_nested_branch = dataclasses.replace(
            palette_branch,
            children=(expanded_true, palette_branch.children[1]))
        scalar_nested_main = dataclasses.replace(
            main,
            body=(*main.body[:14], main.body[15], scalar_nested_branch,
                  *main.body[17:]))

        swapped_branch = dataclasses.replace(
            palette_branch, children=palette_branch.children[::-1])
        swapped_branch_main = dataclasses.replace(
            main,
            body=(*main.body[:16], swapped_branch, *main.body[17:]))

        for name, mutated_main in {
                "vector-top-level": vector_top_level_main,
                "scalar-inside-palette": scalar_nested_main,
                "palette-true-false-swap": swapped_branch_main,
        }.items():
            mutated = dataclasses.replace(
                program,
                functions=tuple(mutated_main if item is main else item
                                for item in program.functions))
            with self.subTest(name=name), self.assertRaisesRegex(
                    ValueError, "scalar/vector blend.*ancestry"):
                _authenticate_with_refrozen_coarse_locks(
                    profile, program, mutated)

    def test_slice_schema_rejects_shape_carrier_mutations_and_collisions(self):
        exact = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        row = next(item for item in exact["programs"]
                   if item["program_key"] == KEY)
        mutations = {}

        wrong = copy.deepcopy(exact)
        next(item for item in wrong["programs"]
             if item["program_key"] == KEY)[
                 "shape_mixer_builtin_profile"] = "wrong"
        mutations["wrong-profile"] = wrong
        missing = copy.deepcopy(exact)
        del next(item for item in missing["programs"]
                 if item["program_key"] == KEY)[
                     "shape_mixer_builtin_profile"]
        mutations["missing-profile"] = missing
        missing_companion = copy.deepcopy(exact)
        del next(item for item in missing_companion["programs"]
                 if item["program_key"] == KEY)["scalar_uint_xor_profile"]
        mutations["missing-companion"] = missing_companion
        collision = copy.deepcopy(exact)
        next(item for item in collision["programs"]
             if item["program_key"] == KEY)[
                 "emboss_color_style_profile"] = "emboss-color-style-v1"
        mutations["carrier-collision"] = collision
        foreign = copy.deepcopy(exact)
        next(item for item in foreign["programs"]
             if item["program_key"] == "filter/bc:bc")[
                 "shape_mixer_builtin_profile"] = PROFILE
        mutations["foreign-key"] = foreign
        duplicate = copy.deepcopy(exact)
        duplicate["programs"].append(copy.deepcopy(row))
        duplicate["programs"].sort(key=lambda item: item["program_key"])
        mutations["duplicate-row"] = duplicate

        for name, candidate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                repository = pathlib.Path(temp)
                target = repository / "tools/glslcpp/typed_slice.json"
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.load_slice(repository)

    def test_generated_outputs_register_exact_shape_program_once(self):
        outputs = generate_typed_slice.generate_outputs(ROOT)
        source = outputs["src/typed_generated/typed_slice.cpp"].decode()
        manifest = json.loads(
            outputs["src/typed_generated/typed_manifest.json"])
        catalog = generate_typed_slice.render_catalog_header(
            generate_typed_slice.load_slice(ROOT)).decode()
        marker = f"// Typed IR program: {KEY}\n"
        begin = source.index(marker)
        end = source.index("// Typed IR program:", begin + len(marker))
        block = source[begin:end]

        self.assertEqual(1, source.count(marker))
        self.assertEqual(1, block.count(
            "bind_classicNoisedeck_shapeMixer_shapeMixer"))
        self.assertEqual(1, catalog.count(
            "bind_classicNoisedeck_shapeMixer_shapeMixer"))
        rows = [item for item in manifest["programs"]
                if item["program_key"] == KEY]
        self.assertEqual(1, len(rows))
        # Live-state pin: 211 typed programs and 213 public catalog
        # declarations because two legacy entries are dual-registered.
        self.assertEqual(211, len(manifest["programs"]))
        self.assertEqual(213, catalog.count("[[nodiscard]] BoundKernel bind_"))
        self.assertEqual(SCALAR_XOR_PROFILE,
                         rows[0]["scalar_uint_xor_profile"])
        self.assertEqual(PROFILE, rows[0]["shape_mixer_builtin_profile"])


if __name__ == "__main__":
    unittest.main()
