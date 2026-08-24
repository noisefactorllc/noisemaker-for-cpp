from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest import mock


REPOSITORY = Path(__file__).resolve().parents[1]


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _load_program(key: str):
    from tools.glslcpp import check_corpus, generate_typed_slice
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic import analyze_program

    corpus = check_corpus._corpus_root(REPOSITORY)
    manifest = json.loads((corpus / "manifest.json").read_text())
    entry = next(item for item in manifest["programs"]
                 if item["program_key"] == key)
    raw = (corpus / entry["source"]).read_text()
    defines = generate_typed_slice._defaults(REPOSITORY, key)
    program = analyze_program(parse_program(raw, key, defines), key)
    if key == "synth/noise:noise":
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, apply_runtime_loop_bound)
        program = apply_runtime_loop_bound(program, entry["raw_sha256"],
                                           PROFILE)
    return entry["raw_sha256"], program


def _walk_expression(value):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _replace_expression(value, target, replacement):
    if value is target:
        return replacement
    return dataclasses.replace(
        value, children=tuple(_replace_expression(child, target, replacement)
                              for child in value.children))


def _replace_statement(value, target, replacement):
    return dataclasses.replace(
        value,
        expressions=tuple(_replace_expression(item, target, replacement)
                          for item in value.expressions),
        children=tuple(_replace_statement(item, target, replacement)
                       for item in value.children))


def _replace_in_program(program, target, replacement):
    return dataclasses.replace(
        program,
        functions=tuple(dataclasses.replace(
            function,
            body=tuple(_replace_statement(item, target, replacement)
                       for item in function.body))
            for function in program.functions))


class ScalarUintXorProfileTests(unittest.TestCase):
    def test_profile_module_exists(self) -> None:
        self.assertIsNotNone(
            importlib.util.find_spec(
                "tools.glslcpp.frontend.scalar_uint_xor_profile"))

    def test_profile_exposes_authentication_contract(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as profile

        self.assertEqual("scalar-uint-xor-v1", profile.PROFILE)
        self.assertTrue(callable(profile.authenticate_scalar_uint_xor))
        self.assertTrue(callable(
            profile.authenticate_scalar_uint_to_float_narrowing_skips))
        self.assertTrue(callable(profile.apply_scalar_uint_xor))
        self.assertEqual(7, len(profile.SCALAR_UINT_XOR_KEYS))

    def test_exact_uint_to_float_census_selects_only_grain_observable_site(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as profile

        selected = {}
        self.assertLessEqual(set(profile._UINT_TO_FLOAT_CENSUS_LOCKS),
                             set(profile.SCALAR_UINT_XOR_KEYS))
        self.assertNotIn("synth/noise:noise",
                         profile._UINT_TO_FLOAT_CENSUS_LOCKS)
        for key in sorted(profile._UINT_TO_FLOAT_CENSUS_LOCKS):
            source_hash, program = _load_program(key)
            sites = profile.authenticate_scalar_uint_to_float_narrowing_skips(
                program, source_hash, profile.PROFILE)
            selected[key] = sites
        self.assertEqual(
            {"filter/grain:grain": 1},
            {key: len(sites) for key, sites in selected.items() if sites})

        source_hash, first = _load_program("filter/grain:grain")
        _, second = _load_program("filter/grain:grain")
        first_site, = profile.authenticate_scalar_uint_to_float_narrowing_skips(
            first, source_hash, profile.PROFILE)
        second_site, = profile.authenticate_scalar_uint_to_float_narrowing_skips(
            second, source_hash, profile.PROFILE)
        self.assertEqual(first_site, second_site)
        self.assertIsNot(first_site, second_site)
        self.assertEqual("construct", first_site.kind)
        self.assertEqual("float", first_site.constructor_type.display())
        self.assertEqual("uint", first_site.children[0].type.display())
        self.assertEqual("swizzle", first_site.children[0].kind)

        with self.assertRaises(ValueError):
            profile.authenticate_scalar_uint_to_float_narrowing_skips(
                first, source_hash, None)
        with self.assertRaises(ValueError):
            profile.authenticate_scalar_uint_to_float_narrowing_skips(
                _replace_in_program(
                    first, first_site,
                    dataclasses.replace(first_site, category="lvalue")),
                source_hash, profile.PROFILE)

    def test_uint_to_float_site_mutation_survives_coarse_hash_bypass(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as profile

        source_hash, program = _load_program("filter/grain:grain")
        site, = profile.authenticate_scalar_uint_to_float_narrowing_skips(
            program, source_hash, profile.PROFILE)
        mutated = _replace_in_program(
            program, site, dataclasses.replace(site, category="lvalue"))
        record = dict(profile._PROFILES[program.key])
        owner = next(function for function in mutated.functions
                     if function.signature.id == 60)
        record["functions_sha256"] = profile._sha(mutated.functions)
        record["whole_program_sha256"] = (
            profile._whole_program_fingerprint(mutated))
        record["owner"] = (*record["owner"][:6], profile._sha(owner),
                           record["owner"][7])
        with mock.patch.dict(profile._PROFILES, {program.key: record}):
            with self.assertRaisesRegex(
                    ValueError, "uint-to-float census site mismatch"):
                profile.authenticate_scalar_uint_to_float_narrowing_skips(
                    mutated, source_hash, profile.PROFILE)

    def test_all_seven_exact_carriers_authenticate_three_owned_lanes(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, SCALAR_UINT_XOR_KEYS, apply_scalar_uint_xor,
            authenticate_scalar_uint_xor)

        total = 0
        for key in sorted(SCALAR_UINT_XOR_KEYS):
            with self.subTest(key=key):
                source_hash, program = _load_program(key)
                sites = authenticate_scalar_uint_xor(
                    program, source_hash, PROFILE)
                self.assertEqual(3, len(sites))
                total += len(sites)
                self.assertIs(
                    program,
                    apply_scalar_uint_xor(program, source_hash, PROFILE))
                self.assertEqual(
                    ["uint", "uint", "uint"],
                    [site.type.display() for site in sites])
                self.assertEqual(
                    [("binary", "^", "rvalue", ["uint", "uint"])] * 3,
                    [(site.kind, site.operator, site.category,
                      [child.type.display() for child in site.children])
                     for site in sites])

                owner_sites = []
                for function in program.functions:
                    for statement in function.body:
                        for value in _walk_statement(statement):
                            if any(value is site for site in sites):
                                owner_sites.append((function, value))
                self.assertEqual(3, len(owner_sites))
                self.assertEqual(1, len({id(owner) for owner, _ in owner_sites}))
        self.assertEqual(21, total)

    def test_profile_token_key_and_source_hash_boundaries_are_closed(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, SCALAR_UINT_XOR_KEYS, authenticate_scalar_uint_xor)

        for key in sorted(SCALAR_UINT_XOR_KEYS):
            source_hash, program = _load_program(key)
            for bad_hash, bad_profile in (
                    (source_hash, None), (source_hash, "wrong"),
                    ("0" * 64, PROFILE)):
                with self.subTest(key=key, source_hash=bad_hash,
                                  profile=bad_profile), self.assertRaises(ValueError):
                    authenticate_scalar_uint_xor(
                        program, bad_hash, bad_profile)
            with self.subTest(key=key, mutation="foreign-key"), self.assertRaises(ValueError):
                authenticate_scalar_uint_xor(
                    dataclasses.replace(program, key="foreign:key"),
                    source_hash, PROFILE)

        source_hash, ordinary = _load_program("filter/bc:bc")
        self.assertEqual((), authenticate_scalar_uint_xor(
            ordinary, source_hash, None))
        with self.assertRaises(ValueError):
            authenticate_scalar_uint_xor(ordinary, source_hash, PROFILE)

    def test_authentication_returns_objects_from_each_supplied_tree(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, authenticate_scalar_uint_xor)

        for key in ("filter/grain:grain",
                    "classicNoisedeck/bitEffects:bitEffects"):
            source_hash, first = _load_program(key)
            _, second = _load_program(key)
            first_sites = authenticate_scalar_uint_xor(first, source_hash, PROFILE)
            second_sites = authenticate_scalar_uint_xor(second, source_hash, PROFILE)
            self.assertEqual(first_sites, second_sites)
            self.assertTrue(all(a is not b
                                for a, b in zip(first_sites, second_sites)))

    def test_each_carrier_rejects_missing_duplicate_reordered_and_retyped_sites(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, SCALAR_UINT_XOR_KEYS, authenticate_scalar_uint_xor)
        from tools.glslcpp.frontend.semantic_types import INT

        for key in sorted(SCALAR_UINT_XOR_KEYS):
            source_hash, program = _load_program(key)
            sites = authenticate_scalar_uint_xor(program, source_hash, PROFILE)
            parent = next(
                value for function in program.functions for statement in function.body
                for value in _walk_statement(statement)
                if len(value.children) == 3
                and all(value.children[index] is sites[index]
                        for index in range(3)))
            mutations = {
                "missing": _replace_in_program(
                    program, sites[0], sites[0].children[0]),
                "duplicate": _replace_in_program(
                    program, sites[1], sites[0]),
                "reordered": _replace_in_program(
                    program, parent, dataclasses.replace(
                        parent, children=(sites[1], sites[0], sites[2]))),
                "operator": _replace_in_program(
                    program, sites[0], dataclasses.replace(sites[0], operator="|")),
                "category": _replace_in_program(
                    program, sites[0], dataclasses.replace(sites[0], category="lvalue")),
                "result-type": _replace_in_program(
                    program, sites[0], dataclasses.replace(sites[0], type=INT)),
                "left-type": _replace_in_program(
                    program, sites[0], dataclasses.replace(
                        sites[0], children=(dataclasses.replace(
                            sites[0].children[0], type=INT), sites[0].children[1]))),
            }
            for label, mutated in mutations.items():
                with self.subTest(key=key, mutation=label), self.assertRaises(ValueError):
                    authenticate_scalar_uint_xor(mutated, source_hash, PROFILE)

    def test_biteffects_signed_and_vector_xors_are_not_authorized(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, authenticate_scalar_uint_xor)

        source_hash, program = _load_program(
            "classicNoisedeck/bitEffects:bitEffects")
        authorized = authenticate_scalar_uint_xor(program, source_hash, PROFILE)
        all_xors = [
            value for function in program.functions for statement in function.body
            for value in _walk_statement(statement)
            if value.kind == "binary" and value.operator == "^"]
        self.assertEqual(3, len(authorized))
        self.assertTrue(any(value.type.display() == "int" for value in all_xors))
        self.assertTrue(any(value.type.display() == "uvec3" for value in all_xors))
        self.assertTrue(all(any(value is site for value in all_xors)
                            for site in authorized))
        self.assertTrue(all(site.type.display() == "uint" for site in authorized))

    def test_node_mutation_survives_coarse_hash_bypass_and_is_still_rejected(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as profile

        source_hash, program = _load_program("filter/grain:grain")
        first, _, _ = profile.authenticate_scalar_uint_xor(
            program, source_hash, profile.PROFILE)
        mutated = _replace_in_program(
            program, first, dataclasses.replace(first, category="lvalue"))

        # Re-freeze all enclosing/coarse digests to the forged tree. The exact
        # site digest/category check must remain an independent barrier.
        record = dict(profile._PROFILES[program.key])
        owner = next(function for function in mutated.functions
                     if function.name == record["owner"][1])
        parent = next(
            value for statement in owner.body for value in _walk_statement(statement)
            if _span(value) == record["parent"][0])
        record["functions_sha256"] = profile._sha(mutated.functions)
        record["whole_program_sha256"] = profile._whole_program_fingerprint(mutated)
        record["owner"] = (*record["owner"][:6], profile._sha(owner),
                           record["owner"][7])
        record["parent"] = (record["parent"][0], profile._sha(parent))
        record["scalar_census_sha256"] = profile._scalar_census_fingerprint(
            mutated, parent)
        with mock.patch.dict(profile._PROFILES, {program.key: record}):
            with self.assertRaisesRegex(ValueError, "scalar XOR site mismatch"):
                profile.authenticate_scalar_uint_xor(
                    mutated, source_hash, profile.PROFILE)

    def test_grain_validator_and_emitter_require_both_composed_profiles(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import (
            TypedEmissionError, render_typed_cpp)
        from tools.glslcpp.frontend.as_u32_round_profile import (
            PROFILE as ROUND_PROFILE)
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE as XOR_PROFILE)

        source_hash, program = _load_program("filter/grain:grain")
        kwargs = {
            "source_hash": source_hash,
            "as_u32_round_profile": ROUND_PROFILE,
            "scalar_uint_xor_profile": XOR_PROFILE,
        }
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES, **kwargs)
        emitted = render_typed_cpp(program, program.key, source_hash,
                                   as_u32_round_profile=ROUND_PROFILE,
                                   scalar_uint_xor_profile=XOR_PROFILE)
        self.assertIn("BoundKernel bind_typed", emitted)

        for missing in ("as_u32_round_profile", "scalar_uint_xor_profile"):
            bad = dict(kwargs)
            bad.pop(missing)
            with self.subTest(validator_missing=missing), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES, **bad)
            emitter_bad = dict(bad)
            emitter_bad.pop("source_hash")
            with self.subTest(emitter_missing=missing), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(program, program.key, source_hash,
                                 **emitter_bad)

    def test_validator_and_emitter_reject_equal_nodes_from_a_foreign_tree(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import (
            TypedEmissionError, render_typed_cpp)
        from tools.glslcpp.frontend.as_u32_round_profile import (
            PROFILE as ROUND_PROFILE)
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE as XOR_PROFILE, authenticate_scalar_uint_xor)

        source_hash, first = _load_program("filter/grain:grain")
        _, second = _load_program("filter/grain:grain")
        foreign = authenticate_scalar_uint_xor(second, source_hash, XOR_PROFILE)
        with mock.patch.object(
                generate_typed_slice, "authenticate_scalar_uint_xor",
                return_value=foreign):
            with self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    first, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    as_u32_round_profile=ROUND_PROFILE,
                    scalar_uint_xor_profile=XOR_PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp.authenticate_scalar_uint_xor",
                return_value=foreign):
            with self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    first, first.key, source_hash,
                    as_u32_round_profile=ROUND_PROFILE,
                    scalar_uint_xor_profile=XOR_PROFILE)

    def test_slice_schema_has_exact_shape_and_grain_carriers_and_no_vocabulary_growth(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.scalar_uint_xor_profile import PROFILE

        spec = generate_typed_slice.load_slice(REPOSITORY)
        rows = [item for item in spec["programs"]
                if "scalar_uint_xor_profile" in item]
        self.assertEqual([
            # kaleido (187) sorts ahead of Shape Mixer and carries this
            # carrier as a REQUIRED companion to its mutable-global-array
            # record; the XOR module's absent-set carve admits the
            # auto-attached fixed-array proof for this key only.
            {
                "program_key": "classicNoisedeck/kaleido:kaleido",
                "defines": {"DIRECTION": 2, "KERNEL": 0,
                            "LOOP_OFFSET": 10, "METRIC": 0},
                "mutable_global_array_profile":
                    "mutable-global-nine-array-kaleido-v1",
                "scalar_uint_xor_profile": PROFILE,
            },
            {
                "program_key": "classicNoisedeck/shapeMixer:shapeMixer",
                "defines": {"LOOP_OFFSET": 10},
                "scalar_uint_xor_profile": PROFILE,
                "shape_mixer_builtin_profile":
                    "shape-mixer-builtin-closure-v1",
            },
            # Shapes183 reuses this carrier verbatim rather than adding a
            # second XOR implementation, and sorts between Shape Mixer and
            # Grain. It is the only member carrying three further profiles.
            {
                "program_key": "classicNoisedeck/shapes:shapes",
                "defines": {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30},
                "linear_srgb_lane_index_profile":
                    "linear-srgb-shapes-lane-index-v1",
                "scalar_uint_xor_profile": PROFILE,
                "shapes_float_bits_ingress_profile":
                    "shapes-float-bits-ingress-v1",
                "shapes_rvalue_assign_profile": "shapes-rvalue-assign-v1",
            },
            {
                "program_key": "filter/grain:grain",
                "defines": {},
                "as_u32_round_profile": "as-u32-round-admission-v1",
                "scalar_uint_xor_profile": PROFILE,
            },
            {
                "program_key": "synth/noise:noise",
                "defines": {"LOOP_OFFSET": 300, "NOISE_TYPE": 10},
                "mutable_global_frame_profile":
                    "mutable-global-frame-noise-v1",
                "runtime_define_profile": "runtime-defines-noise-v1",
                "runtime_loop_bound_profile": "runtime-loop-bound-v1",
                "scalar_uint_xor_profile": PROFILE,
            },
            # `synth/shape:shape` reuses this carrier verbatim as well, sorts
            # last of the four, and pairs it with the mutable-global frame
            # closure -- a different program from Shapes above, with a
            # numerically identical define pair.
            {
                "program_key": "synth/shape:shape",
                "defines": {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30},
                "mutable_global_frame_profile":
                    "mutable-global-frame-shape-v1",
                "scalar_uint_xor_profile": PROFILE,
            },
        ], rows)
        keys = [item["program_key"] for item in spec["programs"]]
        # Live-state pin, not a milestone: later landings leave Grain at
        # ordinal 58, while the current sorted slice has 211 programs. The
        # authenticated key-list hash below covers every landing and shift.
        self.assertEqual(211, len(keys))
        self.assertEqual(59, keys.index("filter/grain:grain"))
        self.assertEqual(
            "29a148b26cfe4f550ac82325810655eb0e5ffad2c3a4e5241e42600bac9f76c1",
            hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest())
        self.assertNotIn("scalar-uint-xor", spec["capabilities"])
        self.assertNotIn("scalar-uint-xor",
                         generate_typed_slice.APPROVED_CAPABILITIES)

    def test_generated_grain_uses_three_direct_xors_and_preserves_vector_xor(self) -> None:
        generated = (REPOSITORY / "src/typed_generated/typed_slice.cpp").read_text()
        begin = generated.index("// Typed IR program: filter/grain:grain")
        next_marker = generated.index("// Typed IR program:", begin + 1)
        block = generated[begin:next_marker]
        first = block.index("random_from_cell_3d(")
        second = block.index("random_from_cell_3d(", first + 1)
        owner = block[second:block.index("\n}\n", second)]
        self.assertEqual(3, owner.count(" ^ "))
        self.assertEqual(0, owner.count("glsl::bitwise_xor("))
        self.assertEqual(1, block.count("glsl::bitwise_xor("))
        self.assertIn(
            "static_cast<double>(static_cast<double>("
            "glsl::swizzle<0>(noise))) * ", owner)
        self.assertNotIn("float(glsl::swizzle<0>(noise))", owner)
        self.assertNotRegex(owner, r"bitwise_xor\([^\n]*std::uint32_t")
        self.assertNotIn("scalar_uint_xor", generated)

    def test_grain_is_exact_single_program_delta_from_174(self) -> None:
        import copy
        from tools.glslcpp import generate_typed_slice

        # Reconstruct the exact Grain-175 milestone before comparing it with
        # StatsFinal-174; Gabor, Scanline Error, Glyph Map, and Shapes are
        # subsequent additive programs.
        #
        # This is a MILESTONE reconstruction, not a live-state pin: Shapes
        # joins the exclusion set so the 175/174 counts below stay exactly as
        # frozen. Bumping those counts instead would have silently redefined
        # which milestone this test measures. cellRefract joins the exclusion
        # set the same way, so the frozen 175/174 counts stay exactly as-is.
        spec = copy.deepcopy(generate_typed_slice.load_slice(REPOSITORY))
        spec["programs"] = [
            item for item in spec["programs"]
            if item["program_key"] not in {
                "filter/dither:dither", "synth/julia:julia",
                "classicNoisedeck/moodscape:moodscape",
                "filter/emboss:emboss", "synth/gabor:gabor",
                "filter/scanlineError:scanlineError",
                "filter/glyphMap:glyphMap", "filter/edge:edge",
                "mixer/distortion:distortion",
                "classicNoisedeck/glitch:glitch",
                "classicNoisedeck/shapeMixer:shapeMixer",
                "classicNoisedeck/shapes:shapes",
                "synth/shape:shape", "filter/normalMap:normalMap",
                "classicNoisedeck/cellRefract:cellRefract",
                "classicNoisedeck/kaleido:kaleido",
                "classicNoisedeck/effects:effects",
                "filter/wobble:wobble",
                "filter/parallax:parallax",
                "filter/lightLeak:lightLeak",
                "synth/newton:newton",
                "synth/mandelbrot:mandelbrot",
                "synth/remap:remap", "synth/testPattern:testPattern",
                "classicNoisedeck/bitEffects:bitEffects",
                "classicNoisedeck/colorLab:colorLab",
                "classicNoisedeck/noise:noise",
                "classicNoisedeck/fractal:fractal",
                "filter/historicPalette:historicPalette", "filter/median:median",
                "filter/osd:osd", "filter/palette:palette",
                "filter/spookyTicker:spookyTicker", "filter/texture:texture"}]
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=spec):
            current = generate_typed_slice.generate_outputs(REPOSITORY)
        prior_spec = copy.deepcopy(spec)
        prior_spec["programs"] = [
            item for item in prior_spec["programs"]
            if item["program_key"] != "filter/grain:grain"]
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=prior_spec):
            prior = generate_typed_slice.generate_outputs(REPOSITORY)

        marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")
        def blocks(payload: bytes):
            source = payload.decode()
            starts = list(marker.finditer(source))
            catalog = source.index(
                "\nnamespace {\nconstexpr std::array<KernelFactory")
            return {
                match.group(1): source[
                    match.start():(starts[index + 1].start()
                                   if index + 1 < len(starts) else catalog)]
                for index, match in enumerate(starts)
            }

        current_blocks = blocks(current[
            "src/typed_generated/typed_slice.cpp"])
        prior_blocks = blocks(prior["src/typed_generated/typed_slice.cpp"])
        self.assertEqual((177, 176),
                         (len(current_blocks), len(prior_blocks)))
        self.assertEqual({"filter/grain:grain"},
                         set(current_blocks) - set(prior_blocks))
        ordinal = re.compile(r"typed_[0-9]+")
        for key, block in prior_blocks.items():
            with self.subTest(existing_program=key):
                self.assertEqual(
                    ordinal.sub("typed_SENTINEL", block),
                    ordinal.sub("typed_SENTINEL", current_blocks[key]))

        manifest = json.loads(current[
            "src/typed_generated/typed_manifest.json"])
        row = next(item for item in manifest["programs"]
                   if item["program_key"] == "filter/grain:grain")
        self.assertEqual("scalar-uint-xor-v1",
                         row["scalar_uint_xor_profile"])
        self.assertEqual("as-u32-round-admission-v1",
                         row["as_u32_round_profile"])


class ScalarUintXorFixedArrayCompanionCarveTests(unittest.TestCase):
    """The absent-set carve, per key (kaleido-design §4.4.2).

    `kaleido` is the first program that carries BOTH this carrier and the
    generator's auto-attached `fixed_array_in_parameter_proof`
    (`kaleido-convolve-v1`, row 187), so the module's frozen "every optional
    proof absent" set would reject the authentic row at validation. The
    carve is PER KEY: kaleido alone stops checking that one field; the other
    six carriers keep the full absent set, and the remaining sibling-proof
    fields stay checked for kaleido too. Exactness of kaleido's attached
    proof is NOT this module's concern -- the fixed-array arms at both
    authorities own that equality lock (the Amendment 13.2 family split).
    """

    KEY = "classicNoisedeck/kaleido:kaleido"
    PROFILE = "scalar-uint-xor-v1"
    CARVE_KEYS = frozenset({KEY})

    @staticmethod
    def _foreign_proof():
        """A non-None fixed-array proof object, borrowed from the
        cellRefract program (it auto-attaches at its corpus defaults with no
        compatibility transform) -- its identity is irrelevant here, only
        its presence."""
        from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
            attach_fixed_array_in_parameter_proof)

        _, program = _load_program("classicNoisedeck/cellRefract:cellRefract")
        proof = attach_fixed_array_in_parameter_proof(
            program).fixed_array_in_parameter_proof
        assert proof is not None
        return proof

    def test_the_module_names_exactly_one_carved_key(self):
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        self.assertEqual(
            self.CARVE_KEYS, module._FIXED_ARRAY_PROOF_COMPANION_KEYS)
        # The frozen absent-set vocabulary itself is unchanged: the carve
        # selects from it per key rather than shrinking it.
        self.assertEqual(
            ("fixed_nine_table_proof", "fixed_grid_counter_store_proof",
             "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof"),
            module._OPTIONAL_PROOF_FIELDS)

    def test_kaleido_authenticates_with_the_fixed_array_proof_attached(self):
        import dataclasses
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            authenticate_scalar_uint_xor)

        source_hash, program = _load_program(self.KEY)
        proof = self._foreign_proof()
        self.assertIsNotNone(proof)
        carrying = dataclasses.replace(
            program, fixed_array_in_parameter_proof=proof)
        # CLEAN: the carved field no longer fails the absent-set check, and
        # no fingerprint in this module covers the proof field, so the
        # authentic program plus a companion proof authenticates exactly.
        nodes = authenticate_scalar_uint_xor(carrying, source_hash,
                                             self.PROFILE)
        self.assertEqual(3, len(nodes))

    def test_every_other_sibling_proof_still_absent_for_kaleido(self):
        import dataclasses
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            authenticate_scalar_uint_xor)

        source_hash, program = _load_program(self.KEY)
        for field in ("fixed_nine_table_proof",
                      "fixed_grid_counter_store_proof",
                      "fixed_affine_centers13_proof"):
            with self.subTest(field=field):
                carrying = dataclasses.replace(
                    program, fixed_array_in_parameter_proof=None,
                    **{field: self._foreign_proof()})
                with self.assertRaisesRegex(
                        ValueError,
                        "unrelated proof carrier is not absent"):
                    authenticate_scalar_uint_xor(carrying, source_hash,
                                                 self.PROFILE)

    def test_the_other_six_keys_keep_the_stricter_absent_set(self):
        import dataclasses
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            authenticate_scalar_uint_xor)

        others = tuple(sorted(set(module.SCALAR_UINT_XOR_KEYS)
                              - self.CARVE_KEYS))
        self.assertEqual(6, len(others))
        proof = self._foreign_proof()
        for key in others:
            with self.subTest(key=key):
                source_hash, program = _load_program(key)
                carrying = dataclasses.replace(
                    program, fixed_array_in_parameter_proof=proof)
                with self.assertRaisesRegex(
                        ValueError,
                        "unrelated proof carrier is not absent"):
                    authenticate_scalar_uint_xor(carrying, source_hash,
                                                 self.PROFILE)


if __name__ == "__main__":
    unittest.main()
