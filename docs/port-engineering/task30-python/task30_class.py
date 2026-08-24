

class Task30ExtrudeBvec2RelationalReductionTests(unittest.TestCase):
    @staticmethod
    def exact_program():
        import hashlib
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            EXTRUDE_KEY)
        from tools.glslcpp.frontend.semantic import analyze_program

        source = (REPOSITORY / "tools/glslcpp/corpus/"
                  "a024dc3a960cc44af454abc7aebce50456c194e6/"
                  "sources/filter/extrude/extrude.glsl").read_text()
        return (source, hashlib.sha256(source.encode()).hexdigest(),
                analyze_program(parse_program(
                    source, EXTRUDE_KEY, {"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0}),
                    EXTRUDE_KEY))

    def test_task30_exact_profile_authenticates_frozen_closure_and_narrow_abi_emission(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            PROFILE, apply_extrude_bvec2_relational_reduction,
            authenticate_extrude_bvec2_relational_reduction)

        _, source_hash, exact = self.exact_program()
        proof = authenticate_extrude_bvec2_relational_reduction(
            exact, source_hash, PROFILE)
        main = exact.functions[5]
        self.assertIs(main, proof.main)
        self.assertEqual(36, main.id)
        self.assertEqual((2, 2), (len(proof.reductions), len(proof.relationals)))
        self.assertEqual(("bool", "bool"),
                         tuple(item.type.display() for item in proof.reductions))
        self.assertEqual(("bvec2", "bvec2"),
                         tuple(item.type.display() for item in proof.relationals))
        self.assertEqual(("all", "all"),
                         tuple(item.callee for item in proof.reductions))
        self.assertEqual(("lessThanEqual", "lessThanEqual"),
                         tuple(item.callee for item in proof.relationals))

        def span(value):
            return (f"{value.span.start_line}:{value.span.start_column}-"
                    f"{value.span.end_line}:{value.span.end_column}")

        self.assertEqual(("159:23-159:72", "160:37-160:81"),
                         tuple(span(item) for item in proof.reductions))
        self.assertEqual(("159:27-159:71", "160:41-160:80"),
                         tuple(span(item) for item in proof.relationals))
        for reduction, relational in zip(proof.reductions, proof.relationals):
            self.assertEqual(1, len(reduction.children))
            self.assertIs(relational, reduction.children[0])
            self.assertEqual(2, len(relational.children))
        self.assertEqual(("declaration", "binary"),
                         tuple(item.kind for item in proof.reduction_parents))
        self.assertEqual((3, 3), tuple(map(len, proof.statement_parent_chains)))
        for chain in proof.statement_parent_chains:
            self.assertEqual(("for", "block", "decl"),
                             tuple(item.kind for item in chain))
        self.assertEqual(11, len(proof.consumed_objects))
        self.assertEqual(11, len({id(item) for item in proof.consumed_objects}))
        self.assertIs(exact, apply_extrude_bvec2_relational_reduction(
            exact, source_hash, PROFILE))

        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(exact, exact.key, source_hash)
        generate_typed_slice.validate_capabilities(
            exact, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)
        emitted = render_typed_cpp(
            exact, exact.key, source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)

        # Narrow-ABI lowering: exactly the two authenticated
        # all(lessThanEqual(...)) nests, nothing wider (no `any`, no
        # strict-relational, no named bvec2 intermediate).
        self.assertEqual(2, emitted.count("glsl::all("))
        self.assertEqual(2, emitted.count("glsl::lessThanEqual("))
        self.assertEqual(2, emitted.count("glsl::all(glsl::lessThanEqual("))
        self.assertEqual(0, emitted.count("glsl::any("))
        self.assertEqual(0, emitted.count("glsl::lessThan("))
        self.assertEqual(0, emitted.count("glsl::greaterThan("))
        self.assertEqual(0, emitted.count("glsl::greaterThanEqual("))
        self.assertEqual(0, emitted.count("glsl::BVec2"))
        self.assertIn(
            "bool topHit = glsl::all(glsl::lessThanEqual(glsl::abs("
            "(P - faceCenter)), faceHalf));", emitted)
        self.assertIn(
            "bool sideHit = ((!topHit) && glsl::all(glsl::lessThanEqual("
            "glsl::abs((P - cellC)), halfCell)));", emitted)
        self.assertIn("namespace typed_25 {", emitted)

        # Independent reconstruction: a distinct-object, structurally equal
        # tree still authenticates on its own authority, sharing no object
        # identity with the original candidate's proof.
        def reconstruct(value):
            if dataclasses.is_dataclass(value):
                return dataclasses.replace(value, **{
                    field.name: reconstruct(getattr(value, field.name))
                    for field in dataclasses.fields(value)})
            if isinstance(value, tuple):
                return tuple(reconstruct(item) for item in value)
            return value

        rebuilt = reconstruct(exact)
        self.assertEqual(exact, rebuilt)
        self.assertIsNot(exact, rebuilt)
        rebuilt_proof = authenticate_extrude_bvec2_relational_reduction(
            rebuilt, source_hash, PROFILE)
        self.assertEqual(len(proof.consumed_objects), len(rebuilt_proof.consumed_objects))
        self.assertTrue(all(not any(old is own for old in proof.consumed_objects)
                            for own in rebuilt_proof.consumed_objects))
        generate_typed_slice.validate_capabilities(
            rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)
        render_typed_cpp(
            rebuilt, rebuilt.key, source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)

        # Neither authority trusts a forged/stale proof: even if the
        # authenticate function is mocked to hand back a proof built from a
        # DIFFERENT (the original, not `rebuilt`) tree, the surrounding
        # pipeline independently re-derives node identity by walking the
        # actual candidate, and rejects the mismatch.
        with mock.patch.object(
                generate_typed_slice,
                "authenticate_extrude_bvec2_relational_reduction",
                return_value=proof), self.assertRaises(
                    generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                extrude_bvec2_relational_reduction_profile=PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp."
                "authenticate_extrude_bvec2_relational_reduction",
                return_value=proof), self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                rebuilt, rebuilt.key, source_hash,
                extrude_bvec2_relational_reduction_profile=PROFILE)

    def test_task30_exhaustive_single_axis_structural_mutations_reject_at_all_three_authorities(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            PROFILE, authenticate_extrude_bvec2_relational_reduction)
        from tools.glslcpp.frontend.semantic_types import FLOAT, vector
        from tools.glslcpp.frontend.typed_ir import PreprocessorDefine

        _, source_hash, exact = self.exact_program()

        def at(value, path):
            for part in path:
                value = value[part] if isinstance(part, int) else getattr(value, part)
            return value

        def replaced(value, path, replacement):
            if len(path) == 1:
                part = path[0]
                if isinstance(part, int):
                    items = list(value); items[part] = replacement
                    return tuple(items)
                return dataclasses.replace(value, **{part: replacement})
            part = path[0]
            child = value[part] if isinstance(part, int) else getattr(value, part)
            updated = replaced(child, path[1:], replacement)
            if isinstance(part, int):
                items = list(value); items[part] = updated
                return tuple(items)
            return dataclasses.replace(value, **{part: updated})

        main_index = 5
        main = exact.functions[main_index]
        self.assertEqual(36, main.id)
        top_all_path = ("functions", main_index, "body", 12, "children", 1,
                        "children", 8, "expressions", 0, "children", 0)
        top_rel_path = top_all_path + ("children", 0)
        side_all_path = ("functions", main_index, "body", 12, "children", 1,
                         "children", 9, "expressions", 0, "children", 0,
                         "children", 1)
        side_rel_path = side_all_path + ("children", 0)
        top_rel = at(exact, top_rel_path)

        axes = {
            "program-key": (("key",), "filter/extrude:foreign"),
            "normalized-source": (("source",), exact.source + " "),
            "raw-source": (("raw_source",), exact.raw_source + " "),
            "body-status": (("body_status",), "task30-mutated"),
            "define-name": (("preprocessor_defines",),
                            (PreprocessorDefine("TASK30", "int", "1"),
                             PreprocessorDefine("EXTRUDE_TYPE", "int", "0"))),
            "define-order": (("preprocessor_defines",),
                             tuple(reversed(exact.preprocessor_defines))),
            "struct-presence": (("structs",), (object(),)),
            "uniform-block-presence": (("uniform_blocks",), (object(),)),
            "loop-count": (("counted_loop_proof", "loop_count"), 4),
            "loop-depth": (("counted_loop_proof", "max_effective_depth"), 4),
            "loop-product": (("counted_loop_proof", "max_lexical_product"), 10),
            "loop-charge": (("counted_loop_proof", "entrypoint_charge"), 91),
            "call-graph-cycle": (("counted_loop_proof", "call_graph_acyclic"), False),
            "resource-uniform-order": (("resources", "uniforms"),
                                       tuple(reversed(exact.resources.uniforms))),
            "resource-uniform-count": (("resources", "uniforms"),
                                       exact.resources.uniforms[:-1]),
            "resource-sampler-count": (("resources", "samplers"), ()),
            "resource-output": (("resources", "outputs", 0), "otherColor"),
            "resource-texture": (("resources", "uses_texture"), False),
            "resource-derivative": (("resources", "uses_derivatives"), True),
            "function-count": (("functions",), exact.functions[:-1]),
            "function-order": (("functions",), tuple(reversed(exact.functions))),
            "main-id": (("functions", main_index, "signature", "id"), 999),
            "main-return": (("functions", main_index, "signature", "return_type"), FLOAT),
            "main-body-count": (("functions", main_index, "body"), main.body[:-1]),
            "main-span": (("functions", main_index, "span", "start_line"), 128),
            "for-kind": (("functions", main_index, "body", 12, "kind"), "block"),
            "for-span": (("functions", main_index, "body", 12, "span", "start_line"), 144),
            "block-kind": (("functions", main_index, "body", 12, "children", 1, "kind"), "decl"),
            "block-span": (("functions", main_index, "body", 12, "children", 1,
                           "span", "start_line"), 144),
            "decl8-span": (("functions", main_index, "body", 12, "children", 1,
                          "children", 8, "span", "start_line"), 144),
            "decl9-span": (("functions", main_index, "body", 12, "children", 1,
                          "children", 9, "span", "start_line"), 144),
            "decl8-kind": (("functions", main_index, "body", 12, "children", 1,
                          "children", 8, "kind"), "block"),
            "top-all-span": (top_all_path + ("span", "start_column"), 24),
            "top-all-callee": (top_all_path + ("callee",), "any"),
            "top-all-type": (top_all_path + ("type",), FLOAT),
            "top-all-children-order": (top_all_path + ("children",), (top_rel, top_rel)),
            "top-rel-span": (top_rel_path + ("span", "start_column"), 28),
            "top-rel-type": (top_rel_path + ("type",), vector("bool", 3)),
            "top-rel-callee": (top_rel_path + ("callee",), "lessThan"),
            "top-rel-children-order": (top_rel_path + ("children",),
                                       tuple(reversed(top_rel.children))),
            "top-rel-children-count": (top_rel_path + ("children",), top_rel.children[:1]),
            "side-all-span": (side_all_path + ("span", "start_column"), 38),
            "side-all-callee": (side_all_path + ("callee",), "any"),
            "side-all-type": (side_all_path + ("type",), FLOAT),
            "side-rel-span": (side_rel_path + ("span", "start_column"), 42),
            "side-rel-type": (side_rel_path + ("type",), vector("bool", 3)),
            "side-rel-callee": (side_rel_path + ("callee",), "lessThan"),
        }
        candidates = {name: replaced(exact, path, value)
                      for name, (path, value) in axes.items()}
        self.assertEqual(len(axes), len(candidates))
        self.assertEqual(47, len(candidates))
        self.assertEqual(
            "2919cf0225ab23a5e10247e9625c74fb40fb158a8ab910aad577b17bbfd35a0d",
            hashlib.sha256(("\n".join(sorted(candidates)) + "\n").encode()).hexdigest())

        for name, candidate in candidates.items():
            # Each candidate must assert its own structural precondition —
            # that it genuinely changed the program — before rejection is
            # meaningful; a no-op mutation would prove nothing.
            self.assertNotEqual(exact, candidate, name)
            with self.subTest(axis=name, layer="profile"), self.assertRaises(ValueError):
                authenticate_extrude_bvec2_relational_reduction(
                    candidate, source_hash, PROFILE)
            with self.subTest(axis=name, layer="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    extrude_bvec2_relational_reduction_profile=PROFILE)
            with self.subTest(axis=name, layer="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, source_hash,
                    extrude_bvec2_relational_reduction_profile=PROFILE)

    def test_task30_validator_and_emitter_authenticate_independently_without_trusting_each_other(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            EXTRUDE_KEY, PROFILE)

        _, source_hash, exact = self.exact_program()
        foreign = dataclasses.replace(exact, key="filter/extrude:foreignvariant")

        # The emitter fails closed on its own authority: no profile, a wrong
        # profile string, and a foreign (differently-keyed) program carrying
        # the identical closure — none of these ever invoke the validator.
        with self.assertRaisesRegex(TypedEmissionError, r"exact .* carrier required"):
            render_typed_cpp(exact, exact.key, source_hash)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                exact, exact.key, source_hash,
                extrude_bvec2_relational_reduction_profile="wrong")
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                foreign, foreign.key, source_hash,
                extrude_bvec2_relational_reduction_profile=PROFILE)
        # The deepest-reachable rejection on the foreign program, with no
        # carrier at all, is exactly the live-verified builtin-level message —
        # the emitter walks into the closure and rejects the first offending
        # node, never having consulted the validator.
        with self.assertRaisesRegex(
                TypedEmissionError,
                r"filter/extrude:foreignvariant:159:27: unsupported builtin lessThanEqual"):
            render_typed_cpp(foreign, foreign.key, source_hash)

        # The validator fails closed on its own authority, symmetrically,
        # without ever invoking the emitter.
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError, r"exact .* carrier required"):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                extrude_bvec2_relational_reduction_profile="wrong")
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                extrude_bvec2_relational_reduction_profile=PROFILE)
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"filter/extrude:foreignvariant:159:23: unsupported builtin all"):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)

        # Widening the validator's generic type vocabulary alone does not
        # rescue an unauthenticated candidate: bvec2/all/lessThanEqual
        # admission is identity-scoped to the four authenticated nodes, not a
        # table a wider program could opt into. Snapshot and restore under
        # try/finally so no other test observes the widened state.
        snapshot = tuple(generate_typed_slice.APPROVED_TYPES)
        try:
            with mock.patch.object(
                    generate_typed_slice, "APPROVED_TYPES",
                    (*generate_typed_slice.APPROVED_TYPES, "bvec2")):
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=source_hash)
        finally:
            self.assertEqual(snapshot, generate_typed_slice.APPROVED_TYPES)

    def test_task30_capability_and_type_vocabulary_are_identity_scoped_not_widened(self) -> None:
        from tools.glslcpp import emit_typed_cpp, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import PROFILE

        # bvec2 is never a globally-approved type, and all/lessThanEqual are
        # never globally-approved builtins or capability names — exactly like
        # `round` before it (Task 24).
        self.assertNotIn("bvec2", generate_typed_slice.APPROVED_TYPES)
        self.assertNotIn("all", generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("lessThanEqual", generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("all", emit_typed_cpp._BUILTIN_NAMES)
        self.assertNotIn("lessThanEqual", emit_typed_cpp._BUILTIN_NAMES)
        self.assertNotIn("bvec2", emit_typed_cpp._TYPES)

        # The capability vocabulary is still exactly the 44 entries frozen
        # before this task; the two-node relational/reduction closure never
        # widened it.
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        spec = generate_typed_slice.load_slice(REPOSITORY)
        self.assertEqual(44, len(spec["capabilities"]))
        self.assertEqual(tuple(spec["capabilities"]),
                         generate_typed_slice.APPROVED_CAPABILITIES)

        # Behavioral proof, not just a static list check: validate_capabilities
        # raises "missing capabilities" if ANYTHING reaches its internal
        # bookkeeping (`used`) that is absent from the declared 44-entry
        # vocabulary — see generate_typed_slice.py's `missing = used -
        # set(capabilities)` gate. `all`/`lessThanEqual` are deliberately
        # skipped from `used.add`, exactly like `round`
        # (`if value.callee not in {"round", "all", "lessThanEqual"}:
        # used.add(value.callee)`). Since this call succeeds against the
        # UNMODIFIED 44-entry tuple that itself excludes `all`/`lessThanEqual`,
        # it is direct evidence that neither builtin ever entered `used` —
        # had they, this call would have raised "missing capabilities all,
        # lessThanEqual".
        _, source_hash, exact = self.exact_program()
        generate_typed_slice.validate_capabilities(
            exact, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)
        render_typed_cpp(
            exact, exact.key, source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)

    def test_task30_history_coexistence_and_live_schema_matches_130_program_state(self) -> None:
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            EXTRUDE_KEY, PROFILE)

        spec = generate_typed_slice.load_slice(REPOSITORY)
        typed = tuple(item["program_key"] for item in spec["programs"])
        public = tuple(sorted((*typed, "filter/invert:inv", "synth/solid:solid")))
        corpus = json.loads((check_corpus._corpus_root(REPOSITORY) /
                             "manifest.json").read_text())
        unported = tuple(sorted(
            {item["program_key"] for item in corpus["programs"]} - set(public)))
        self.assertEqual((130, 132, 80, 212),
                         (len(typed), len(public), len(unported),
                          len(corpus["programs"])))
        self.assertEqual(
            "d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904",
            hashlib.sha256(("\n".join(typed) + "\n").encode()).hexdigest())
        self.assertEqual(
            "4fe573b21a782a784b7fcacacaa276a03a395a1b8c92e83149971b8a19831056",
            hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest())
        self.assertEqual(25, typed.index(EXTRUDE_KEY))
        self.assertEqual(("filter/directionalBlur:directionalBlur", EXTRUDE_KEY,
                          "filter/fibers:fibersBlend"), typed[24:27])
        self.assertEqual([{
            "defines": {"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0},
            "extrude_bvec2_relational_reduction_profile": PROFILE,
            "program_key": EXTRUDE_KEY,
        }], [item for item in spec["programs"]
             if "extrude_bvec2_relational_reduction_profile" in item])

        manifest = json.loads(generate_typed_slice.generate_outputs(REPOSITORY)[
            "src/typed_generated/typed_manifest.json"])
        extrude_row = next(item for item in manifest["programs"]
                           if item["program_key"] == EXTRUDE_KEY)
        self.assertEqual(PROFILE,
                         extrude_row["extrude_bvec2_relational_reduction_profile"])
        self.assertEqual({"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0},
                         extrude_row["defines"])

        # Coexistence: this identity profile carries no relationship to any
        # earlier task's profile/capability, so declaring both at once is a
        # metadata-mismatch at every prior task's carrier — proving a fresh
        # APPROVED_CAPABILITIES/APPROVED_TYPES tuple import-cycle collision
        # never occurs.
        _, source_hash, exact = self.exact_program()
        coexistence = {
            "compatibility_transform": generate_typed_slice.CRT_COMPATIBILITY_TRANSFORM,
            "custom_comparer_profile": generate_typed_slice.LENS_CUSTOM_COMPARER_PROFILE,
            "source_global_literal_int_profile":
                generate_typed_slice.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
            "gather_sorted_round_profile": generate_typed_slice.GATHER_SORTED_ROUND_PROFILE,
            "literal_vec3_lane_index_profile":
                generate_typed_slice.LITERAL_VEC3_LANE_INDEX_PROFILE,
            "smooth_edge_luma_weights_profile":
                generate_typed_slice.SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE,
            "perlin_scalar_uint_xor_profile":
                generate_typed_slice.PERLIN_SCALAR_UINT_XOR_PROFILE,
            "rotate_mat2_return_profile": generate_typed_slice.ROTATE_MAT2_RETURN_PROFILE,
            "focus_blur_borrowed_sampler_profile":
                generate_typed_slice.FOCUS_BLUR_BORROWED_SAMPLER_PROFILE,
        }
        self.assertEqual(9, len(coexistence))
        for name, value in coexistence.items():
            kwargs = {name: value,
                     "extrude_bvec2_relational_reduction_profile": PROFILE}
            with self.subTest(layer="validator", coexistence=name), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    exact, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash, **kwargs)
            with self.subTest(layer="emitter", coexistence=name), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(exact, exact.key, source_hash, **kwargs)

        # Module import + a fresh APPROVED_CAPABILITIES/APPROVED_TYPES tuple
        # check: importing the profile module standalone must not mutate
        # either module-level tuple, and both must still equal the frozen
        # 44/16-entry vocabularies after import.
        from tools.glslcpp.frontend import extrude_bvec2_relational_reduction_profile as profile_module
        self.assertEqual(PROFILE, profile_module.PROFILE)
        self.assertEqual(EXTRUDE_KEY, profile_module.EXTRUDE_KEY)
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(16, len(generate_typed_slice.APPROVED_TYPES))

    def test_task30_removing_only_extrude_regenerates_task29_outputs_byte_for_byte(self) -> None:
        import copy
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            EXTRUDE_KEY)

        spec = generate_typed_slice.load_slice(REPOSITORY)
        task29_spec = copy.deepcopy(spec)
        task29_spec["programs"] = [item for item in task29_spec["programs"]
                                   if item["program_key"] != EXTRUDE_KEY]
        task29_keys = tuple(item["program_key"] for item in task29_spec["programs"])
        self.assertEqual(129, len(task29_keys))
        self.assertEqual(
            "c2561c5937ba5f11f5d2e86d729ff90b617aff738cb4de53dbf3cd8b76dbbff9",
            hashlib.sha256(("\n".join(task29_keys) + "\n").encode()).hexdigest())

        # load_slice hard-pins the live 130-program count/hash, so the Task29
        # reconstruction must go through the mocked loader, exactly as the
        # Task29 test reconstructs Task28.
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=task29_spec):
            task29 = generate_typed_slice.generate_outputs(REPOSITORY)
        task29["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(task29_spec))
        expected_task29 = {
            "src/typed_generated/typed_slice.cpp":
                "358847db37675afd7f173341c66f71527af04c8ac817efddcc7d4b7cf31551aa",
            "src/typed_generated/typed_manifest.json":
                "01bfe3c139e8352ad04ac87ed5817715166dff371e983361f8cbb7fefe650351",
            "include/noisemaker/generated/catalog.hpp":
                "2d32511c858a5caeedb7c4fe1b2d985191e639a9e4ed1d98ca9219a60b668304",
        }
        for path, expected in expected_task29.items():
            self.assertEqual(expected, hashlib.sha256(task29[path]).hexdigest(), path)

        marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")
        def blocks(payload):
            source = payload.decode()
            starts = list(marker.finditer(source))
            catalog = source.index(
                "\nnamespace {\nconstexpr std::array<KernelFactory")
            return {match.group(1): source[
                match.start():(starts[index + 1].start()
                               if index + 1 < len(starts) else catalog)]
                for index, match in enumerate(starts)}

        task29_blocks = blocks(task29["src/typed_generated/typed_slice.cpp"])
        self.assertEqual(129, len(task29_blocks))
        self.assertNotIn(EXTRUDE_KEY, task29_blocks)

    def test_task30_native_executable_tables_are_exact_frozen_transcription_and_tamper_sensitive(self) -> None:
        import hashlib

        oracle_path = REPOSITORY / "tests/oracles/task-30-oracles.json"
        self.assertTrue(oracle_path.is_file(), "Task 30 frozen oracle JSON is required")
        oracle_bytes = oracle_path.read_bytes()
        self.assertEqual(
            "bf8c4c165846eb116d2afb4f78b7c1de78f70f104ac714e09395ceffbe51c758",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)

        kernels_path = REPOSITORY / "tests/test_generated_kernels.cpp"
        cpp = kernels_path.read_text()
        for marker in ("// TASK30_NATIVE_ORACLE_TABLE_BEGIN",
                       "// TASK30_NATIVE_ORACLE_TABLE_END",
                       "// TASK30_DIRECT_ABI_HARNESS_BEGIN",
                       "// TASK30_DIRECT_ABI_SWITCH_BEGIN",
                       "// TASK30_DIRECT_ABI_SWITCH_END",
                       "// TASK30_DIRECT_ABI_HARNESS_END"):
            self.assertIn(marker, cpp,
                         "native Task30 fixtures/tables are pending in "
                         "tests/test_generated_kernels.cpp")
        parsed = _task30_parse_executable_tables(cpp)

        # Only the 3 direct define-map {EXTRUDE_TYPE:0, DEPTH_SOURCE:0} cases
        # are authorized for the native port (see the brief and the comment
        # immediately preceding kTask30NativeCases); the other 3 oracle cases
        # use a different define map and are excluded here on purpose.
        authorized_cases = [item for item in oracle["cases"]
                            if item["defines"] == {"EXTRUDE_TYPE": 0, "DEPTH_SOURCE": 0}]
        self.assertEqual(3, len(authorized_cases))
        self.assertEqual(6, len(oracle["cases"]))
        expected_cases = []
        for item in authorized_cases:
            output = item["output"]
            probes = []
            for probe in output["probes"][:5]:
                probes.extend(probe["at_top_down_xy"])
                probes.extend(int(bits, 16) for bits in probe["f32_bits_le"])
            expected_cases.append([
                item["name"], item["dimensions"]["width"], item["dimensions"]["height"],
                item["phase"], float(item["uniforms"]["size"]),
                float(item["uniforms"]["depth"]), item["uniforms"]["solidFront"],
                item["input"]["f32_sha256"], output["f32_sha256"], output["rgba8_sha256"],
                probes, output["finite_lanes"], output["nonfinite_lanes"],
            ])
        self.assertEqual(expected_cases, parsed["cases"])

        # The 7 direct_relational_cases rows, transcribed verbatim.
        direct = oracle["direct_relational_cases"]
        self.assertEqual(7, len(direct))
        expected_rows = [[
            [int(bits, 16) for bits in item["left_bits"]],
            [int(bits, 16) for bits in item["right_bits"]],
            item["less_than_equal_lanes"], item["all_result"], item["any_result"],
            item["strict_less_lanes"],
        ] for item in direct]
        self.assertEqual(expected_rows, parsed["relational_rows"])

        # Independently recomputed public-factory mutation divergence counts
        # (out of the oracle's full 6 cases per mutation, across both
        # authorized and sensitivity-only define maps), cross-checked against
        # the brief's claimed 3/6, 2/6, 4/6, 2/6.
        mutations = {item["id"]: item for item in oracle["public_factory_mutations"]}
        self.assertEqual(
            {"top-lane-any", "side-lane-any", "top-strict-less",
             "side-strict-less"},
            set(mutations))
        divergence = {mutation_id: sum(
            1 for row in item["case_results"] if not row["same_f32_bytes"])
            for mutation_id, item in mutations.items()}
        self.assertEqual({
            "top-lane-any": 3, "side-lane-any": 2,
            "top-strict-less": 4, "side-strict-less": 2,
        }, divergence)

        # Mode enum / dispatch table: five structurally distinct native modes
        # (never a disguised shared code path, unlike 3 of Task 26's 11).
        enum_names = ["exact_inclusive_all", "inclusive_any", "strict_exclusive_all",
                     "strict_exclusive_any", "mirrored_inclusive_all"]
        self.assertEqual([[name, ordinal] for ordinal, name in enumerate(enum_names)],
                         parsed["mode_enum"])
        self.assertEqual(enum_names, parsed["dispatch"])
        self.assertEqual([
            "exact-inclusive-le-all-reduction", "inclusive-le-any-reduction",
            "strict-exclusive-lt-all-reduction", "strict-exclusive-lt-any-reduction",
            "mirrored-inclusive-ge-all-reduction"], parsed["names"])
        self.assertEqual(5, len(parsed["arms"]))
        self.assertEqual(5, len(set(body for _, body in parsed["arms"])))
        arms = dict(parsed["arms"])
        self.assertIn("noisemaker::glsl::lessThanEqual<2>", arms["exact_inclusive_all"])
        self.assertIn("noisemaker::glsl::all<2>", arms["exact_inclusive_all"])
        self.assertNotIn("noisemaker::glsl::all<2>", arms["inclusive_any"])
        self.assertIn("any=any||le[lane]", arms["inclusive_any"])
        self.assertIn("lx<rx", arms["strict_exclusive_all"])
        self.assertIn("all_true=all_true&&lane[l]", arms["strict_exclusive_all"])
        self.assertIn("lx<rx", arms["strict_exclusive_any"])
        self.assertIn("any=any||lane[l]", arms["strict_exclusive_any"])
        self.assertIn("rx<=lx", arms["mirrored_inclusive_all"])
        self.assertNotIn("lessThanEqual", arms["mirrored_inclusive_all"])
        self.assertIn("invalidTask30relationalmode", parsed["guard"])
        self.assertEqual(10, len(parsed["signature_fields"]))

        # Token-level tamper sensitivity over the whole authenticated region:
        # every single-token mutation that still parses must change the
        # parsed structure. Catches source tampering, not just JSON tampering.
        begin = cpp.index("// TASK30_NATIVE_ORACLE_TABLE_BEGIN")
        end = cpp.index("// TASK30_DIRECT_ABI_HARNESS_END") + len(
            "// TASK30_DIRECT_ABI_HARNESS_END")
        region = cpp[begin:end]
        tokens = list(re.finditer(
            r'"[^"\n]*"|::|==|!=|<=|>=|&&|\|\||'
            r'\b(?:0x[0-9a-fA-F]+|[0-9]+(?:\.[0-9]+)?f?)(?:U)?\b|'
            r'\b[A-Za-z_][A-Za-z0-9_]*\b|[{}()\[\],;:+\-*/=<>]',
            region))
        self.assertGreater(len(tokens), 3000)
        baseline = parsed
        for ordinal, token in enumerate(tokens):
            old = token.group(0)
            if old.startswith('"'):
                new = old[:-1] + 'X"'
            elif re.match(r"[A-Za-z_]", old):
                new = old + "X"
            elif re.match(r"(?:0x|[0-9])", old):
                new = "7" if old != "7" else "8"
            else:
                new = "@"
            tampered_region = region[:token.start()] + new + region[token.end():]
            tampered = cpp[:begin] + tampered_region + cpp[end:]
            try:
                changed = _task30_parse_executable_tables(tampered)
            except (AssertionError, SyntaxError, ValueError):
                continue
            self.assertNotEqual(baseline, changed,
                                f"Task30 executable token {ordinal}: {old}")
        self.assertEqual(
            "bf8c4c165846eb116d2afb4f78b7c1de78f70f104ac714e09395ceffbe51c758",
            hashlib.sha256(oracle_bytes).hexdigest())
