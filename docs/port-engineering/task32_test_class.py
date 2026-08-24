

class Task32GradeClusterTests(unittest.TestCase):
    """`filter/grade:*` -- six programs, two capability shapes, per the
    frozen Task 32 brief (§1/§2/§8): five identity-scoped `LUMA_WEIGHTS`
    global carve-outs (never widened past the exact frozen declaration) and
    one id-indexed-lane-read/write proof track admitted purely by node
    identity, never by adding a 45th `used.add(...)` token.
    """

    LUMA_KEYS = (
        "filter/grade:creative", "filter/grade:hslSecondary",
        "filter/grade:primary", "filter/grade:vignette", "filter/grade:wheels",
    )
    ALL_KEYS = (
        "filter/grade:creative", "filter/grade:hslSecondary", "filter/grade:lut",
        "filter/grade:primary", "filter/grade:vignette", "filter/grade:wheels",
    )
    SOURCE_FILES = {
        "filter/grade:creative": "creative.glsl",
        "filter/grade:hslSecondary": "hslSecondary.glsl",
        "filter/grade:lut": "lut.glsl",
        "filter/grade:primary": "primary.glsl",
        "filter/grade:vignette": "vignette.glsl",
        "filter/grade:wheels": "wheels.glsl",
    }

    @staticmethod
    def exact_program(key):
        import hashlib
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = (REPOSITORY / "tools/glslcpp/corpus/"
                  "a024dc3a960cc44af454abc7aebce50456c194e6/"
                  f"sources/filter/grade/"
                  f"{Task32GradeClusterTests.SOURCE_FILES[key]}").read_text()
        return (source, hashlib.sha256(source.encode()).hexdigest(),
                analyze_program(parse_program(source, key, {}), key))

    def test_task32_authenticates_frozen_luma_weights_for_five_programs(self) -> None:
        from tools.glslcpp.frontend.grade_luma_weights_profile import (
            PROFILES, authenticate_grade_luma_weights)

        expected_reads = {
            "filter/grade:primary": 4, "filter/grade:hslSecondary": 0,
            "filter/grade:wheels": 2, "filter/grade:vignette": 1,
            "filter/grade:creative": 3,
        }
        for key in self.LUMA_KEYS:
            with self.subTest(key=key):
                _, source_hash, typed = self.exact_program(key)
                declaration = authenticate_grade_luma_weights(
                    typed, source_hash, PROFILES[key])
                self.assertEqual("LUMA_WEIGHTS", declaration.symbol.name)
                self.assertEqual("const", declaration.symbol.storage)
                self.assertFalse(declaration.symbol.writable)
                self.assertEqual("vec3", declaration.type.display())
                self.assertEqual(3, len(declaration.initializer.children))
                lanes = tuple(child.literal for child in declaration.initializer.children)
                self.assertEqual(("0.2126", "0.7152", "0.0722"), lanes)
                reads = [value for function in typed.functions
                         for statement in function.body
                         for value in self._walk_statement(statement)
                         if value.kind == "id"
                         and value.symbol_id == declaration.symbol.id]
                self.assertEqual(expected_reads[key], len(reads), key)
                for value in reads:
                    self.assertIs(value.symbol, declaration.symbol)
                    self.assertEqual("readonly lvalue", value.category)

    @staticmethod
    def _walk_expression(value):
        yield value
        for child in value.children:
            yield from Task32GradeClusterTests._walk_expression(child)

    @staticmethod
    def _walk_statement(statement):
        for expression in statement.expressions:
            yield from Task32GradeClusterTests._walk_expression(expression)
        for child in statement.children:
            yield from Task32GradeClusterTests._walk_statement(child)

    def test_task32_hslsecondary_luma_weights_is_structurally_validated_only(self) -> None:
        """Disclosure: `hslSecondary`'s LUMA_WEIGHTS type-checks (admission
        completeness for otherwise-dead source) but is never read anywhere
        in the program -- confirmed by full census, not sampling. No oracle
        mutation can discriminate it (per the frozen brief §5/§8); a future
        maintainer should not go hunting for a render-based test that cannot
        exist for this specific declaration.
        """
        from tools.glslcpp.frontend.grade_luma_weights_profile import (
            PROFILES, authenticate_grade_luma_weights)

        key = "filter/grade:hslSecondary"
        _, source_hash, typed = self.exact_program(key)
        declaration = authenticate_grade_luma_weights(typed, source_hash, PROFILES[key])
        reads = [value for function in typed.functions
                 for statement in function.body
                 for value in self._walk_statement(statement)
                 if value.kind == "id" and value.symbol_id == declaration.symbol.id]
        self.assertEqual(0, len(reads))

    def test_task32_authenticates_frozen_index_expression_sites_for_six_programs(self) -> None:
        from tools.glslcpp.frontend.grade_index_expression_profile import (
            PROFILES, authenticate_grade_index_expression)

        expected_counts = {
            "filter/grade:primary": 10, "filter/grade:hslSecondary": 14,
            "filter/grade:wheels": 10, "filter/grade:vignette": 10,
            "filter/grade:creative": 10, "filter/grade:lut": 20,
        }
        for key in self.ALL_KEYS:
            with self.subTest(key=key):
                _, source_hash, typed = self.exact_program(key)
                sites = authenticate_grade_index_expression(
                    typed, source_hash, PROFILES[key])
                self.assertEqual(expected_counts[key], len(sites), key)
                for site in sites:
                    self.assertEqual("index", site.kind)
                    self.assertEqual("float", site.type.display())
                    self.assertEqual("lvalue", site.category)
                    self.assertEqual(2, len(site.children))
                    base, index = site.children
                    self.assertEqual("id", base.kind)
                    self.assertEqual("vec3", base.type.display())
                    self.assertIn(base.symbol.storage, ("local", "parameter"))
                    self.assertTrue(base.symbol.writable)
                    self.assertEqual("id", index.kind)
                    self.assertEqual("int", index.type.display())
                    self.assertEqual("local", index.symbol.storage)

    def test_task32_rejects_wrong_profile_hash_and_foreign_key_for_both_tracks(self) -> None:
        from tools.glslcpp.frontend.grade_luma_weights_profile import (
            PROFILES as LUMA_PROFILES, authenticate_grade_luma_weights)
        from tools.glslcpp.frontend.grade_index_expression_profile import (
            PROFILES as INDEX_PROFILES, authenticate_grade_index_expression)

        _, source_hash, typed = self.exact_program("filter/grade:primary")
        with self.assertRaises(ValueError):
            authenticate_grade_luma_weights(typed, source_hash, "wrong-profile")
        with self.assertRaises(ValueError):
            authenticate_grade_luma_weights(
                typed, "0" * 64, LUMA_PROFILES["filter/grade:primary"])
        with self.assertRaises(ValueError):
            authenticate_grade_luma_weights(
                typed, source_hash, LUMA_PROFILES["filter/grade:wheels"])
        with self.assertRaises(ValueError):
            authenticate_grade_index_expression(typed, source_hash, "wrong-profile")
        with self.assertRaises(ValueError):
            authenticate_grade_index_expression(
                typed, source_hash, INDEX_PROFILES["filter/grade:lut"])

        # lut has no LUMA_WEIGHTS declaration at all -- confirm the luma
        # profile rejects it outright rather than silently no-op admitting.
        _, lut_hash, lut_typed = self.exact_program("filter/grade:lut")
        with self.assertRaises(ValueError):
            authenticate_grade_luma_weights(
                lut_typed, lut_hash, LUMA_PROFILES["filter/grade:primary"])

    def test_task32_capability_vocabulary_stays_frozen_at_forty_four_entries(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend.grade_luma_weights_profile import (
            PROFILES as LUMA_PROFILES)
        from tools.glslcpp.frontend.grade_index_expression_profile import (
            PROFILES as INDEX_PROFILES)

        before = tuple(generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertEqual(44, len(before))
        for key in self.ALL_KEYS:
            with self.subTest(key=key):
                _, source_hash, typed = self.exact_program(key)
                kwargs = {"grade_index_expression_profile": INDEX_PROFILES[key]}
                if key in self.LUMA_KEYS:
                    kwargs["grade_luma_weights_profile"] = LUMA_PROFILES[key]
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash, **kwargs)
                render_typed_cpp(typed, key, source_hash, **kwargs)
        self.assertEqual(before, tuple(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))

    def test_task32_validator_and_emitter_require_both_profiles_where_expected(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.grade_luma_weights_profile import (
            PROFILES as LUMA_PROFILES)
        from tools.glslcpp.frontend.grade_index_expression_profile import (
            PROFILES as INDEX_PROFILES)

        key = "filter/grade:primary"
        _, source_hash, typed = self.exact_program(key)
        # LUMA_WEIGHTS present but not admitted -> unsupported global.
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                grade_index_expression_profile=INDEX_PROFILES[key])
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(typed, key, source_hash,
                             grade_index_expression_profile=INDEX_PROFILES[key])
        # Global admitted but index sites not -> unsupported expression index.
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                grade_luma_weights_profile=LUMA_PROFILES[key])
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(typed, key, source_hash,
                             grade_luma_weights_profile=LUMA_PROFILES[key])

        # lut has no luma track at all; supplying one for it is foreign.
        _, lut_hash, lut_typed = self.exact_program("filter/grade:lut")
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                lut_typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=lut_hash,
                grade_luma_weights_profile=LUMA_PROFILES["filter/grade:primary"],
                grade_index_expression_profile=INDEX_PROFILES["filter/grade:lut"])

    def test_task32_emitted_primary_shows_narrow_global_and_index_lowering(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend.grade_luma_weights_profile import (
            PROFILES as LUMA_PROFILES)
        from tools.glslcpp.frontend.grade_index_expression_profile import (
            PROFILES as INDEX_PROFILES)

        key = "filter/grade:primary"
        _, source_hash, typed = self.exact_program(key)
        emitted = render_typed_cpp(
            typed, key, source_hash,
            grade_luma_weights_profile=LUMA_PROFILES[key],
            grade_index_expression_profile=INDEX_PROFILES[key])
        self.assertIn(
            "const glsl::Vec3 LUMA_WEIGHTS = glsl::FloatExpr<3>("
            "static_cast<float>(0.2126), static_cast<float>(0.7152), "
            "static_cast<float>(0.0722));", emitted)
        self.assertEqual(1, emitted.count("LUMA_WEIGHTS ="))
        self.assertIn("linear[i]", emitted)
        self.assertIn("srgb[i]", emitted)
        # No matrix/array runtime symbol is introduced by this capability.
        self.assertNotIn("proved_array", emitted)

    def test_task32_index_expression_node_level_logic_rejects_past_the_coarse_hash_gate(
            self) -> None:
        """The single-axis rejection above is absorbed by the coarse
        "source, define, function, whole-program, or interface mismatch"
        gate for every mutation, because any tree edit perturbs the
        whole-program hash. Here that coarse gate is deliberately re-frozen
        to match the mutated tree, so the module's *novel* logic --
        node-identity/base-identity comparison against the frozen per-site
        table -- is what has to fire.

        Non-vacuity is then proven by sabotage: the frozen expectation for
        the mutated site is temporarily corrupted to match the forged base
        name (deleting the discriminating power of that one field without
        touching any code), the SAME real `authenticate_grade_index_
        expression` call is re-run and shown to now wrongly ACCEPT the
        tampered tree, and finally the frozen table is restored and the
        same call is shown to correctly REJECT again -- confirming the
        rejection above was caused by that specific check, not by
        something else.
        """
        import dataclasses
        from tools.glslcpp.frontend import grade_index_expression_profile as profile

        key = "filter/grade:primary"
        _, source_hash, baseline = self.exact_program(key)
        baseline_functions_sha = profile._sha(baseline.functions)

        _, _, candidate = self.exact_program(key)
        target_function = next(f for f in candidate.functions if f.name == "srgbToLinear")
        found: list = []

        def walk_expr(value):
            if value.kind == "index":
                found.append(value)
            for child in value.children:
                walk_expr(child)

        def walk_statement(statement):
            for expression in statement.expressions:
                walk_expr(expression)
            for child in statement.children:
                walk_statement(child)

        for statement in target_function.body:
            walk_statement(statement)
        self.assertTrue(found)
        site = found[0]
        base = site.children[0]
        forged_name = "forgedSrgbBase"
        object.__setattr__(
            base, "symbol", dataclasses.replace(base.symbol, name=forged_name))

        # The mutation must genuinely change the tree, or the case is
        # vacuous regardless of what the profile then reports.
        self.assertNotEqual(baseline_functions_sha, profile._sha(candidate.functions))

        lock = profile._LOCKS[key]
        original = dict(lock)
        try:
            lock["functions_sha256"] = profile._sha(candidate.functions)
            lock["whole_sha256"] = profile._whole_fingerprint(candidate)
            lock["interface_sha256"] = profile._interface_fingerprint(candidate)

            with self.assertRaises(ValueError) as context:
                profile.authenticate_grade_index_expression(
                    candidate, source_hash, lock["profile"])
            message = str(context.exception)
            self.assertIn("index site base profile mismatch", message)
            self.assertNotIn(
                "source, define, function, whole-program, or interface mismatch",
                message)

            # --- Sabotage: corrupt the frozen expectation to match the
            # forgery, deleting this one check's discriminating power.
            sites = list(lock["sites"])
            mutated_site = sites[0]
            self.assertEqual("28:13-28:20", mutated_site[2])
            sites[0] = mutated_site[:6] + (forged_name,) + mutated_site[7:]
            lock["sites"] = tuple(sites)
            sabotaged = profile.authenticate_grade_index_expression(
                candidate, source_hash, lock["profile"])
            self.assertEqual(10, len(sabotaged))
        finally:
            lock.clear()
            lock.update(original)

        # Restored: the same real call rejects the same tampered tree again.
        lock2 = profile._LOCKS[key]
        with mock.patch.dict(lock2, {
                "functions_sha256": profile._sha(candidate.functions),
                "whole_sha256": profile._whole_fingerprint(candidate),
                "interface_sha256": profile._interface_fingerprint(candidate)}):
            with self.assertRaises(ValueError) as context:
                profile.authenticate_grade_index_expression(
                    candidate, source_hash, lock2["profile"])
            self.assertIn("index site base profile mismatch", str(context.exception))

        # The patched lock must be restored, or later tests inherit a
        # profile that authenticates the wrong tree.
        self.assertEqual(original, profile._LOCKS[key])
        _, _, restored = self.exact_program(key)
        sites = profile.authenticate_grade_index_expression(
            restored, source_hash, profile.PROFILES[key])
        self.assertEqual(10, len(sites))

    def test_task32_luma_weights_node_level_logic_rejects_past_the_coarse_hash_gate(
            self) -> None:
        """Sibling of the index-track coarse-gate-bypass test above, for the
        global-admission track: swap the BT.709 lane literal for BT.601
        (the exact bug the profile must catch, per the vendored oracle's
        `*-luma-weights-bt601-swap` mutation), re-freeze the coarse gate to
        match, and confirm rejection is by a specific literal-lane message,
        proven non-vacuous by sabotage.
        """
        import dataclasses
        from tools.glslcpp.frontend import grade_luma_weights_profile as profile

        key = "filter/grade:primary"
        _, source_hash, baseline = self.exact_program(key)
        baseline_functions_sha = profile._sha(baseline.functions)

        _, _, candidate = self.exact_program(key)
        declaration = next(d for d in candidate.declarations
                           if d.symbol.name == "LUMA_WEIGHTS")
        first_lane = declaration.initializer.children[0]
        object.__setattr__(first_lane, "literal", "0.299")
        object.__setattr__(first_lane, "literal_value", 0.299)

        self.assertNotEqual(baseline_functions_sha, profile._sha(candidate.functions))

        lock = profile._LOCKS[key]
        original = dict(lock)
        try:
            lock["whole_sha256"] = profile._whole_fingerprint(candidate)
            lock["interface_sha256"] = profile._interface_fingerprint(candidate)
            lock["functions_sha256"] = profile._sha(candidate.functions)
            with self.assertRaises(ValueError) as context:
                profile.authenticate_grade_luma_weights(
                    candidate, source_hash, lock["profile"])
            message = str(context.exception)
            self.assertIn("literal lane profile mismatch", message)
            self.assertNotIn(
                "source, define, function, whole-program, or interface mismatch",
                message)

            # Sabotage: corrupt the frozen lane expectation to match the
            # forged BT.601 literal, deleting this check's power.
            lanes = list(lock["lanes"])
            lanes[0] = ("0.299", 0.299, lanes[0][2], lanes[0][3])
            lock["lanes"] = tuple(lanes)
            declaration2 = profile.authenticate_grade_luma_weights(
                candidate, source_hash, lock["profile"])
            self.assertIsNotNone(declaration2)
        finally:
            lock.clear()
            lock.update(original)

        # Restored: the same real call rejects the same tampered tree again,
        # re-freezing the coarse gate exactly as before.
        lock2 = profile._LOCKS[key]
        with mock.patch.dict(lock2, {
                "whole_sha256": profile._whole_fingerprint(candidate),
                "interface_sha256": profile._interface_fingerprint(candidate),
                "functions_sha256": profile._sha(candidate.functions)}):
            with self.assertRaises(ValueError) as context:
                profile.authenticate_grade_luma_weights(
                    candidate, source_hash, lock2["profile"])
            self.assertIn("literal lane profile mismatch", str(context.exception))

        self.assertEqual(original, profile._LOCKS[key])
        _, _, restored = self.exact_program(key)
        declaration = profile.authenticate_grade_luma_weights(
            restored, source_hash, profile.PROFILES[key])
        self.assertEqual("LUMA_WEIGHTS", declaration.symbol.name)

    def test_task32_ordinal_blast_radius_removing_six_grade_keys_reconstructs_task31(
            self) -> None:
        """Removing all six grade keys from the live typed list must
        regenerate the frozen Task 31 (131-count) outputs byte-for-byte --
        the direct proof that grade's insertion is purely additive and that
        the shared index-admission machinery change didn't perturb any
        other program's emission.
        """
        import copy
        import hashlib
        from tools.glslcpp import generate_typed_slice

        spec = generate_typed_slice.load_slice(REPOSITORY)
        typed = tuple(item["program_key"] for item in spec["programs"])
        self.assertEqual(137, len(typed))

        task31_spec = copy.deepcopy(spec)
        task31_spec["programs"] = [
            item for item in task31_spec["programs"]
            if item["program_key"] not in {
                "filter/grade:creative", "filter/grade:hslSecondary",
                "filter/grade:lut", "filter/grade:primary",
                "filter/grade:vignette", "filter/grade:wheels"}]
        task31_keys = tuple(item["program_key"] for item in task31_spec["programs"])
        self.assertEqual(131, len(task31_keys))
        self.assertEqual(
            "ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2",
            hashlib.sha256(("\n".join(task31_keys) + "\n").encode()).hexdigest())

        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=task31_spec):
            task31 = generate_typed_slice.generate_outputs(REPOSITORY)
        task31["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(task31_spec))

        manifest = json.loads(
            task31["src/typed_generated/typed_manifest.json"].decode())
        self.assertEqual(131, len(manifest["programs"]))
        expected_task31 = {
            "src/typed_generated/typed_slice.cpp":
                "8de4f3843b8183fba5231f795eae3f8e7f95f9d981327a82dc61b194c90fde89",
            "src/typed_generated/typed_manifest.json":
                "26518f224f60cb89c591e230c42dd035d9445a3350e624af3ff6e2a76821c329",
            "include/noisemaker/generated/catalog.hpp":
                "b45c8cd8ad281c38ab49a575a9ef0879dd7ac2b1f4be222e8ca9cbc3e5676ec9",
        }
        for path, expected in expected_task31.items():
            self.assertEqual(expected, hashlib.sha256(task31[path]).hexdigest(), path)

        current = generate_typed_slice.generate_outputs(REPOSITORY)
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

        current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
        task31_blocks = blocks(task31["src/typed_generated/typed_slice.cpp"])
        self.assertEqual((137, 131), (len(current_blocks), len(task31_blocks)))
        self.assertEqual({
            "filter/grade:creative", "filter/grade:hslSecondary",
            "filter/grade:lut", "filter/grade:primary",
            "filter/grade:vignette", "filter/grade:wheels"},
            set(current_blocks) - set(task31_blocks))
        ordinal = re.compile(r"typed_[0-9]+")
        for key, block in task31_blocks.items():
            with self.subTest(historical_task31_block=key):
                self.assertEqual(
                    ordinal.sub("typed_SENTINEL", block),
                    ordinal.sub("typed_SENTINEL", current_blocks[key]))

    def test_task32_no_history_collision_and_fresh_capability_and_type_tuples(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.grade_luma_weights_profile import (
            PROFILES as LUMA_PROFILES, KEYS as LUMA_KEYS)
        from tools.glslcpp.frontend.grade_index_expression_profile import (
            PROFILES as INDEX_PROFILES, KEYS as INDEX_KEYS)

        self.assertEqual(self.LUMA_KEYS, LUMA_KEYS)
        self.assertEqual(self.ALL_KEYS, INDEX_KEYS)
        # No grade profile string collides with any prior task's profile
        # name, and none of grade's own ten strings collide with each other.
        all_names = tuple(LUMA_PROFILES.values()) + tuple(INDEX_PROFILES.values())
        self.assertEqual(10, len(set(all_names)))
        other_profiles = {
            generate_typed_slice.SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE,
            generate_typed_slice.LITERAL_VEC3_LANE_INDEX_PROFILE,
            generate_typed_slice.PERLIN_SCALAR_UINT_XOR_PROFILE,
            generate_typed_slice.ROTATE_MAT2_RETURN_PROFILE,
            generate_typed_slice.FOCUS_BLUR_BORROWED_SAMPLER_PROFILE,
            generate_typed_slice.EXTRUDE_BVEC2_RELATIONAL_REDUCTION_PROFILE,
            generate_typed_slice.CAUSTIC_WORD_HASH_PROFILE,
            generate_typed_slice.CURL_VECTOR_MATH_PROFILE,
            generate_typed_slice.GATHER_SORTED_ROUND_PROFILE,
        }
        self.assertEqual(set(), set(all_names) & other_profiles)
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(16, len(generate_typed_slice.APPROVED_TYPES))
