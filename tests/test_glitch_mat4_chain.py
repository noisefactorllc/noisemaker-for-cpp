from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import pathlib
import re
import tempfile
import types
import unittest
from unittest import mock

from tools.glslcpp import (
    emit_typed_cpp,
    generate_glitch_native_oracle_include,
    generate_typed_slice,
)
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tests.historical_cross_lane import historical_cross_lane


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "classicNoisedeck/glitch:glitch"
PROFILE = "glitch-mat4-chain-v1"
RAW_SHA256 = "13d6350eb21cfb5a7c9f0d0a8fffe8e7495068ca2e082d1520ef14ca5b34c134"
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources/classicNoisedeck/glitch/glitch.glsl")
MODULE = "tools.glslcpp.frontend.glitch_mat4_chain_profile"


def _profile():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError("Glitch mat4 chain profile module is absent")
    return importlib.import_module(MODULE)


def _analyzed(raw: str | None = None, key: str = KEY):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(
        parse_program(raw, key, generate_typed_slice._defaults(ROOT, key)), key)


def _coarse_refreeze(profile, candidate):
    raw = candidate.raw_source.encode()
    normalized = candidate.source.encode()
    return {
        "_RAW_BYTES": len(raw),
        "_RAW_SHA256": hashlib.sha256(raw).hexdigest(),
        "_NORMALIZED_BYTES": len(normalized),
        "_NORMALIZED_BYTES_SHA256": hashlib.sha256(normalized).hexdigest(),
        "_NORMALIZED_IR_SHA256": profile._sha(candidate.source),
        "_RAW_IR_SHA256": profile._sha(candidate.raw_source),
        "_FUNCTIONS_SHA256": profile._sha(candidate.functions),
        "_DECLARATIONS_SHA256": profile._sha(candidate.declarations),
        "_WHOLE_SHA256": profile._whole(candidate),
        "_INTERFACE_SHA256": profile._interface(candidate),
    }


def _ordered_splat_tuple(profile, candidate):
    statement = candidate.functions[2].body[3]
    assignment = statement.expressions[0]
    target, constructor = assignment.children
    scalar = constructor.children[0]
    return (
        (3,), profile._span(statement), profile._sha(statement),
        profile._span(assignment), profile._sha(assignment),
        profile._span(target), profile._sha(target),
        profile._span(constructor), profile._sha(constructor),
        profile._span(scalar), profile._sha(scalar),
    )


def _replace_expression(program, target, replacement):
    def expression(value):
        if value is target:
            return replacement
        children = tuple(expression(child) for child in value.children)
        return value if all(new is old for new, old in zip(
            children, value.children)) else dataclasses.replace(
            value, children=children)

    def statement(value):
        expressions = tuple(expression(item) for item in value.expressions)
        children = tuple(statement(item) for item in value.children)
        if (all(new is old for new, old in zip(
                expressions, value.expressions))
                and all(new is old for new, old in zip(
                    children, value.children))):
            return value
        return dataclasses.replace(
            value, expressions=expressions, children=children)

    functions = tuple(dataclasses.replace(
        function, body=tuple(statement(item) for item in function.body))
        for function in program.functions)
    return dataclasses.replace(program, functions=functions)


class GlitchMat4ChainProfileTests(unittest.TestCase):
    def test_native_oracle_include_has_complete_std_array_terminators(self):
        rendered = generate_glitch_native_oracle_include.render().decode(
            "utf-8")
        self.assertEqual(
            1, rendered.count(
                "inline constexpr std::array<CaseView, 8> kCases{{"))
        self.assertTrue(rendered.endswith(
            "\n}};\n\n}  // namespace glitch_native_oracle\n"))

    def test_current_program_requires_exact_profile_at_both_boundaries(self):
        program = _analyzed()
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"classicNoisedeck/glitch:glitch:.*exact Glitch mat4 chain profile carrier required"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        with self.assertRaisesRegex(
                emit_typed_cpp.TypedEmissionError,
                r"classicNoisedeck/glitch:glitch:.*exact Glitch mat4 chain profile carrier required"):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, RAW_SHA256, "glitch_probe", "bind_glitch_probe")

    def test_exact_profile_returns_candidate_owned_complete_closure(self):
        profile = _profile()
        program = _analyzed()
        proof = profile.authenticate_glitch_mat4_chain(
            program, RAW_SHA256, PROFILE)
        self.assertIs(proof._candidate, program)
        self.assertIs(profile.apply_glitch_mat4_chain(
            program, RAW_SHA256, PROFILE), program)
        self.assertEqual((4, 3, 2, 4, 1, 14), (
            len(proof.declarations), len(proof.constructors),
            len(proof.matrix_products), len(proof.matrix_ids),
            len(proof.vector_products), len(proof.consumed_objects)))
        self.assertEqual(
            ("76:10-76:114", "76:14-76:114", "77:10-77:86",
             "77:14-77:86", "78:10-78:86", "78:14-78:86",
             "79:10-79:23", "79:14-79:23", "79:14-79:19",
             "79:14-79:15", "79:18-79:19", "79:22-79:23",
             "84:16-84:22", "84:21-84:22"),
            tuple(profile._span(item) for item in proof.consumed_objects))

        independent = profile.authenticate_glitch_mat4_chain(
            _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(
            tuple(profile._span(item) for item in proof.consumed_objects),
            tuple(profile._span(item) for item in independent.consumed_objects))
        self.assertTrue(all(
            left is not right for left, right in zip(
                proof.consumed_objects, independent.consumed_objects)))

    def test_exact_profile_admits_validator_and_emits_column_major_left_chain(self):
        program = _analyzed()
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=RAW_SHA256, glitch_mat4_chain_profile=PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256, "glitch_probe", "bind_glitch_probe",
            glitch_mat4_chain_profile=PROFILE)
        self.assertEqual(3, rendered.count("glsl::Mat4("))
        matrix_constructor_lines = tuple(
            line for line in rendered.splitlines()
            if "glsl::Mat4 Q = glsl::Mat4(" in line
            or "glsl::Mat4 S = glsl::Mat4(" in line
            or "glsl::Mat4 T = glsl::Mat4(" in line)
        self.assertEqual(3, len(matrix_constructor_lines))
        self.assertEqual(12, sum(
            line.count("glsl::Vec4(") for line in matrix_constructor_lines))
        self.assertIn("glsl::Mat4 A = ((T * Q) * S);", rendered)
        self.assertIn("glsl::dot((tv * A), uv)", rendered)
        self.assertNotIn("mat4", generate_typed_slice.APPROVED_TYPES)
        self.assertNotIn("mat4", emit_typed_cpp._TYPES)

    def test_exact_profile_preserves_canonical_ordered_freq_splat(self):
        profile = _profile()
        proof = profile.authenticate_glitch_mat4_chain(
            _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual("137:5-137:79", profile._span(
            proof.ordered_freq_splat_assignment))
        self.assertEqual("*=", proof.ordered_freq_splat_assignment.operator)
        self.assertEqual(
            (proof.ordered_freq_splat_target,
             proof.ordered_freq_splat_constructor),
            proof.ordered_freq_splat_assignment.children)

        rendered = emit_typed_cpp.render_typed_cpp(
            proof._candidate, KEY, RAW_SHA256,
            "glitch_probe", "bind_glitch_probe",
            glitch_mat4_chain_profile=PROFILE)
        ordered = (
            "glsl::set_swizzle<0>(freq, (glsl::swizzle<0>(freq) * "
            "periodicFunction(",
            "glsl::set_swizzle<1>(freq, (glsl::swizzle<1>(freq) * "
            "periodicFunction(",
        )
        positions = tuple(rendered.find(line) for line in ordered)
        self.assertTrue(all(position >= 0 for position in positions), rendered)
        self.assertLess(*positions)
        self.assertNotIn(
            "freq = glsl::Vec2((freq * glsl::FloatExpr<2>(periodicFunction(",
            rendered)

    def test_profile_rejects_carrier_identity_and_reviewed_source_mutations(self):
        profile = _profile()
        program = _analyzed()
        candidates = (
            (program, RAW_SHA256, None),
            (program, RAW_SHA256, "wrong"),
            (program, "0" * 64, PROFILE),
            (dataclasses.replace(program, key="classicNoisedeck/other:other"),
             RAW_SHA256, PROFILE),
            (dataclasses.replace(program, functions=program.functions[:-1]),
             RAW_SHA256, PROFILE),
        )
        for candidate, source_hash, carrier in candidates:
            with self.subTest(candidate=(candidate.key, source_hash, carrier)), \
                    self.assertRaises(ValueError):
                profile.authenticate_glitch_mat4_chain(
                    candidate, source_hash, carrier)

        raw = SOURCE.read_text(encoding="utf-8")
        mutations = (
            ("association", "mat4 A = T * Q * S;",
             "mat4 A = T * (Q * S);"),
            ("inner-order", "mat4 A = T * Q * S;",
             "mat4 A = Q * T * S;"),
            ("basis-coefficient", "-3., 3., -2., -1.",
             "-3., 3., -2., -0.5"),
            ("extra-matrix", "mat4 A = T * Q * S;",
             "mat4 extra = mat4(1.0);\n    mat4 A = (T * Q) * S;"),
            ("vector-orientation", "dot(tv * A, uv)",
             "dot(A * tv, uv)"),
            ("return-route", "return dot(tv * A, uv);",
             "return dot(uv, tv * A);"),
            ("ordered-splat-broadcast", "freq *= vec2(periodicFunction(",
             "freq = freq * vec2(periodicFunction("),
        )
        for name, anchor, replacement in mutations:
            self.assertEqual(1, raw.count(anchor), name)
            changed = raw.replace(anchor, replacement)
            with self.subTest(name=name), self.assertRaises(ValueError):
                profile.authenticate_glitch_mat4_chain(
                    _analyzed(changed), hashlib.sha256(changed.encode()).hexdigest(),
                    PROFILE)

    def test_refrozen_coarse_identity_still_rejects_topology_and_splat_mutations(self):
        profile = _profile()
        raw = SOURCE.read_text(encoding="utf-8")
        mutations = (
            ("association", "mat4 A = T * Q * S;",
             "mat4 A = T * (Q * S);", "matrix node closure"),
            ("inner-order", "mat4 A = T * Q * S;",
             "mat4 A = Q * T * S;", "matrix node closure"),
            ("constructor-order", "mat4 Q = mat4(f11, f21,",
             "mat4 Q = mat4(f21, f11,", "matrix node closure"),
            ("constructor-removed",
             "mat4 Q = mat4(f11, f21, f11x, f21x, f12, f22, f12x, f22x, f11y, f21y, f11xy, f21xy, f12y, f22y, f12xy, f22xy);",
             "mat4 Q = mat4(1.0);", "matrix node closure"),
            ("constructor-duplicated", "mat4 A = T * Q * S;",
             "mat4 duplicateConstructor = mat4(1.0);\n    "
             "mat4 A = T * Q * S;",
             "matrix node closure|ordered frequency splat"),
            ("product-removed", "mat4 A = T * Q * S;",
             "mat4 A = T;", "matrix node closure"),
            ("product-duplicated", "mat4 A = T * Q * S;",
             "mat4 duplicateProduct = T * Q;\n    "
             "mat4 A = T * Q * S;",
             "matrix node closure|ordered frequency splat"),
            ("extra-mat4-id-and-declaration", "mat4 A = T * Q * S;",
             "mat4 extraId = Q;\n    mat4 A = T * Q * S;",
             "matrix node closure|ordered frequency splat"),
            ("vector-orientation", "dot(tv * A, uv)",
             "dot(A * tv, uv)", "matrix node closure|route"),
            ("ordered-splat-assignment", "freq *= vec2(periodicFunction(",
             "freq = freq * vec2(periodicFunction(",
             "ordered frequency splat"),
            ("ordered-splat-extra", "freq *= vec2(periodicFunction(",
             "freq *= vec2(periodicFunction(0.0));\n    "
             "freq *= vec2(periodicFunction(", "ordered frequency splat"),
        )
        for name, anchor, replacement, message in mutations:
            self.assertEqual(1, raw.count(anchor), name)
            changed = raw.replace(anchor, replacement)
            candidate = _analyzed(changed)
            replacements = _coarse_refreeze(profile, candidate)
            if not name.startswith("ordered-splat"):
                replacements["_ORDERED_FREQ_SPLAT"] = _ordered_splat_tuple(
                    profile, candidate)
            with self.subTest(name=name), mock.patch.multiple(
                    profile, **replacements):
                profile_hash = profile._sha(profile._profile_tuple())
                with mock.patch.object(profile, "_PROFILE_SHA256", profile_hash), \
                        self.assertRaisesRegex(ValueError, message):
                    profile.authenticate_glitch_mat4_chain(
                        candidate, replacements["_RAW_SHA256"], PROFILE)

    def test_refrozen_matrix_closure_rejects_complete_typed_tree_mutation_set(self):
        profile = _profile()
        exact_program = _analyzed()
        exact = profile.authenticate_glitch_mat4_chain(
            exact_program, RAW_SHA256, PROFILE)
        q, _, _, a = exact.declarations
        outer, inner = exact.matrix_products
        t_id = exact.matrix_ids[0]
        vec4_type = exact.vector_products[0].type
        bicubic = exact_program.functions[0]
        q_statement = bicubic.body[22]
        a_statement = bicubic.body[25]
        duplicate_constructor_statement = dataclasses.replace(
            q_statement, kind="return", expressions=(exact.constructors[0],))
        duplicate_product_statement = dataclasses.replace(
            a_statement, kind="return", expressions=(inner,))
        extra_id_statement = dataclasses.replace(
            a_statement, kind="return", expressions=(exact.matrix_ids[1],))

        def with_bicubic_body(body):
            return dataclasses.replace(
                exact_program,
                functions=(dataclasses.replace(bicubic, body=body),
                           *exact_program.functions[1:]))

        mutations = {
            "forged-outer-parent": _replace_expression(
                exact_program, outer,
                dataclasses.replace(outer, children=(inner, t_id))),
            "retyped-matrix-id": _replace_expression(
                exact_program, t_id, dataclasses.replace(t_id, type=vec4_type)),
            "retyped-matrix-product": _replace_expression(
                exact_program, inner, dataclasses.replace(inner, type=vec4_type)),
            "initializer-removed": _replace_expression(
                exact_program, q, dataclasses.replace(q, children=())),
            "product-removed": _replace_expression(
                exact_program, a, dataclasses.replace(a, children=(exact.matrix_ids[2],))),
            "constructor-duplicated": with_bicubic_body((
                *bicubic.body[:23], duplicate_constructor_statement,
                *bicubic.body[23:])),
            "product-duplicated": with_bicubic_body((
                *bicubic.body[:26], duplicate_product_statement,
                *bicubic.body[26:])),
            "extra-mat4-id": with_bicubic_body((
                *bicubic.body[:26], extra_id_statement,
                *bicubic.body[26:])),
            "extra-mat4-declaration": with_bicubic_body((
                *bicubic.body[:23], q_statement, *bicubic.body[23:])),
        }
        for name, candidate in mutations.items():
            replacements = _coarse_refreeze(profile, candidate)
            with self.subTest(name=name), mock.patch.multiple(
                    profile, **replacements):
                profile_hash = profile._sha(profile._profile_tuple())
                with mock.patch.object(profile, "_PROFILE_SHA256", profile_hash), \
                        self.assertRaisesRegex(ValueError, "matrix node closure"):
                    profile.authenticate_glitch_mat4_chain(
                        candidate, replacements["_RAW_SHA256"], PROFILE)

    def test_validator_and_emitter_ledgers_reject_suppressed_doubled_and_early_initializer(self):
        profile = _profile()
        program = _analyzed()
        exact = profile.authenticate_glitch_mat4_chain(
            program, RAW_SHA256, PROFILE)
        bicubic = program.functions[0]
        declaration_statement = bicubic.body[22]
        early_initializer = dataclasses.replace(
            declaration_statement, kind="return",
            expressions=(exact.constructors[0],))
        bodies = {
            "suppressed-declaration": (
                *bicubic.body[:22], *bicubic.body[23:]),
            "doubled-declaration": (
                *bicubic.body[:22], declaration_statement,
                declaration_statement, *bicubic.body[23:]),
            "initializer-before-declaration": (
                *bicubic.body[:22], early_initializer,
                *bicubic.body[22:]),
        }
        for name, body in bodies.items():
            functions = (dataclasses.replace(bicubic, body=body),
                         *program.functions[1:])
            candidate = dataclasses.replace(program, functions=functions)
            proof = dataclasses.replace(exact, _candidate=candidate)
            with self.subTest(name=name, authority="validator"), \
                    mock.patch.object(
                        generate_typed_slice,
                        "authenticate_glitch_mat4_chain",
                        return_value=proof), \
                    self.assertRaisesRegex(
                        generate_typed_slice.GeneratorError,
                        "Glitch matrix (object visited twice|traversal)"):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    glitch_mat4_chain_profile=PROFILE)
            with self.subTest(name=name, authority="emitter"), mock.patch(
                    "tools.glslcpp.emit_typed_cpp."
                    "authenticate_glitch_mat4_chain",
                    return_value=proof), self.assertRaisesRegex(
                        emit_typed_cpp.TypedEmissionError,
                        "Glitch matrix (object emitted twice|emission)"):
                emit_typed_cpp.render_typed_cpp(
                    candidate, KEY, RAW_SHA256, "glitch_probe",
                    "bind_glitch_probe", glitch_mat4_chain_profile=PROFILE)

    def test_both_authorities_reject_forged_traversal_and_parent_proofs(self):
        profile = _profile()
        program = _analyzed()
        exact = profile.authenticate_glitch_mat4_chain(
            program, RAW_SHA256, PROFILE)
        cross = profile.authenticate_glitch_mat4_chain(
            _analyzed(), RAW_SHA256, PROFILE)

        def proof_with(consumed):
            return types.SimpleNamespace(
                _candidate=program,
                host=exact.host,
                declarations=exact.declarations,
                constructors=exact.constructors,
                matrix_products=exact.matrix_products,
                matrix_ids=exact.matrix_ids,
                vector_products=exact.vector_products,
                dot=exact.dot,
                return_statement=exact.return_statement,
                ordered_freq_splat_assignment=(
                    exact.ordered_freq_splat_assignment),
                ordered_freq_splat_target=exact.ordered_freq_splat_target,
                ordered_freq_splat_constructor=(
                    exact.ordered_freq_splat_constructor),
                consumed_objects=consumed,
            )

        consumed = exact.consumed_objects
        forged = {
            "cross-candidate": cross,
            "deep-copy-declaration": dataclasses.replace(
                exact,
                declarations=(copy.deepcopy(exact.declarations[0]),
                              *exact.declarations[1:])),
            "cloned-inner-parent": dataclasses.replace(
                exact,
                matrix_products=(exact.matrix_products[0],
                                 copy.deepcopy(exact.matrix_products[1]))),
            "declaration-after-initializer": proof_with(
                (consumed[1], consumed[0], *consumed[2:])),
            "missing": proof_with(consumed[:-1]),
            "duplicate": proof_with((*consumed[:-1], consumed[-2])),
            "out-of-order": proof_with(
                (*consumed[:8], consumed[9], consumed[8], *consumed[10:])),
            "wrong-product-parent": dataclasses.replace(
                exact, matrix_products=(exact.matrix_products[1],
                                        exact.matrix_products[0])),
            "wrong-return-parent": dataclasses.replace(
                exact, dot=exact.vector_products[0]),
            "wrong-splat-target": dataclasses.replace(
                exact, ordered_freq_splat_target=exact.matrix_ids[0]),
        }
        for name, proof in forged.items():
            with self.subTest(name=name, authority="validator"), \
                    mock.patch.object(
                        generate_typed_slice,
                        "authenticate_glitch_mat4_chain",
                        return_value=proof), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    glitch_mat4_chain_profile=PROFILE)
            with self.subTest(name=name, authority="emitter"), mock.patch(
                    "tools.glslcpp.emit_typed_cpp."
                    "authenticate_glitch_mat4_chain",
                    return_value=proof), self.assertRaises(
                        emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, RAW_SHA256, "glitch_probe",
                    "bind_glitch_probe", glitch_mat4_chain_profile=PROFILE)

    def test_slice_schema_accepts_only_one_exact_noncolliding_glitch_carrier(self):
        exact = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text(
            encoding="utf-8"))
        row = next(item for item in exact["programs"]
                   if item["program_key"] == KEY)
        self.assertEqual({
            "defines": {},
            "glitch_mat4_chain_profile": PROFILE,
            "program_key": KEY,
        }, row)
        mutations = {}
        wrong = copy.deepcopy(exact)
        next(item for item in wrong["programs"] if item["program_key"] == KEY)[
            "glitch_mat4_chain_profile"] = "wrong"
        mutations["wrong"] = wrong
        missing = copy.deepcopy(exact)
        del next(item for item in missing["programs"]
                 if item["program_key"] == KEY)["glitch_mat4_chain_profile"]
        mutations["missing"] = missing
        extra = copy.deepcopy(exact)
        next(item for item in extra["programs"] if item["program_key"] == KEY)[
            "extra"] = True
        mutations["extra-field"] = extra
        duplicate = copy.deepcopy(exact)
        duplicate["programs"].append(copy.deepcopy(row))
        duplicate["programs"].sort(key=lambda item: item["program_key"])
        mutations["duplicate"] = duplicate
        foreign = copy.deepcopy(exact)
        next(item for item in foreign["programs"]
             if item["program_key"] == "synth/gradient:gradient")[
                 "glitch_mat4_chain_profile"] = PROFILE
        mutations["foreign"] = foreign
        collision = copy.deepcopy(exact)
        next(item for item in collision["programs"]
             if item["program_key"] == KEY)[
                 "edge_bvec3_contour_profile"] = "edge-bvec3-contour-v1"
        mutations["carrier-collision"] = collision
        for name, candidate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                repository = pathlib.Path(temp)
                target = repository / "tools/glslcpp/typed_slice.json"
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.load_slice(repository)

    def test_glitch_is_exact_delta_over_edge179_and_frozen_glyph178(self):
        # MILESTONE reconstruction of the Glitch-180/Edge-179/Glyph-178 chain:
        # later rows are excluded below, and cellRefract joins the exclusion
        # set so the frozen reconstruction stays exactly as-is. Grime is the
        # established exception: it was already present when these artifact
        # pins were recorded, so subtracting it would change the projection.
        edge_key = "filter/edge:edge"
        live180_spec = copy.deepcopy(generate_typed_slice.load_slice(ROOT))
        with historical_cross_lane(live180_spec):
            live180_spec["programs"] = [
                item for item in live180_spec["programs"]
                if item["program_key"] not in {
                    "filter/dither:dither", "synth/julia:julia",
                    "classicNoisedeck/moodscape:moodscape",
                    "filter/emboss:emboss",
                    "classicNoisedeck/shapeMixer:shapeMixer",
                    "classicNoisedeck/shapes:shapes",
                    "synth/shape:shape",
                    "filter/normalMap:normalMap",
                    "classicNoisedeck/cellRefract:cellRefract",
                    "mixer/distortion:distortion",
                    "classicNoisedeck/kaleido:kaleido",
                    "classicNoisedeck/effects:effects",
                    "filter/wobble:wobble",
                    "filter/parallax:parallax",
                    "filter/lightLeak:lightLeak",
                    "synth/newton:newton",
                    "synth/noise:noise",
                    "synth/mandelbrot:mandelbrot",
                    "synth/remap:remap",
                    "synth/testPattern:testPattern",
                    "classicNoisedeck/bitEffects:bitEffects",
                    "classicNoisedeck/colorLab:colorLab",
                    "classicNoisedeck/noise:noise",
                    "classicNoisedeck/fractal:fractal",
                    "filter/historicPalette:historicPalette",
                    "filter/median:median", "filter/osd:osd",
                    "filter/palette:palette", "filter/spookyTicker:spookyTicker",
                    "filter/texture:texture",
                }]
            edge179_spec = copy.deepcopy(live180_spec)
            edge179_spec["programs"] = [
                item for item in edge179_spec["programs"]
                if item["program_key"] != KEY]
            glyph178_spec = copy.deepcopy(edge179_spec)
            glyph178_spec["programs"] = [
                item for item in glyph178_spec["programs"]
                if item["program_key"] != edge_key]

            def outputs(spec):
                with mock.patch.object(generate_typed_slice, "load_slice",
                                       return_value=spec):
                    rendered = generate_typed_slice.generate_outputs(ROOT)
                rendered["include/noisemaker/generated/catalog.hpp"] = (
                    generate_typed_slice.render_catalog_header(spec))
                return rendered

            states = (
                ("live180", live180_spec, outputs(live180_spec)),
                ("edge179", edge179_spec, outputs(edge179_spec)),
                ("glyph178", glyph178_spec, outputs(glyph178_spec)),
            )
        expected_hashes = {
            "live180": {
                "src/typed_generated/typed_slice.cpp": "fcfdb407f7b29e579ae7a49b248769b0ca5bd7b6211579e198ddbeee56a1f462",
                "src/typed_generated/typed_manifest.json": "2a7dcfa5ac9db8a10dbd09cb21855c88a1620fba35062eeffc2c23aef89addf8",
                "include/noisemaker/generated/catalog.hpp": "105647d33091bb328be1ac98e21252c5a349de4e12b955f79f256d53a2b58716",
            },
            "edge179": {
                "src/typed_generated/typed_slice.cpp": "8c11cba4eceaada760977b597465bf714ffa0b72a7c20ba848de774652863431",
                "src/typed_generated/typed_manifest.json": "5c5bc85b96b8f1ccc94377b8705fa5082d3d1eb7d0cf2044f5e6b2e9d6ce4662",
                "include/noisemaker/generated/catalog.hpp": "14af2c62f92c6f025fdfd23f0e3eec95ca25ef7618314051d832d087d0a3fb7d",
            },
            "glyph178": {
                "src/typed_generated/typed_slice.cpp": "13911a23e95d6f3a6e18e74043bc8afa3dd3a852854dff884290edc78d881bce",
                "src/typed_generated/typed_manifest.json": "28426b635570f1fe6d87396ca72244187cc514568fc19d409a158c34663c1a6c",
                "include/noisemaker/generated/catalog.hpp": "5b29f9b683ae0d365c9ede4e6011ebcc854904b6447c6bf6aca3a60acdc7cbcb",
            },
        }
        for label, _, rendered in states:
            for path, digest in expected_hashes[label].items():
                with self.subTest(state=label, artifact=path):
                    self.assertEqual(digest,
                                     hashlib.sha256(rendered[path]).hexdigest())

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

        live_blocks, edge_blocks, glyph_blocks = tuple(
            blocks(rendered["src/typed_generated/typed_slice.cpp"])
            for _, _, rendered in states)
        self.assertEqual((181, 180, 179),
                         tuple(map(len, (live_blocks, edge_blocks, glyph_blocks))))
        self.assertEqual({KEY}, set(live_blocks) - set(edge_blocks))
        self.assertEqual({edge_key}, set(edge_blocks) - set(glyph_blocks))
        ordinal = re.compile(r"typed_[0-9]+")
        for newer, older, label in (
                (live_blocks, edge_blocks, "live180-to-edge179"),
                (edge_blocks, glyph_blocks, "edge179-to-glyph178")):
            for key, block in older.items():
                with self.subTest(boundary=label, retained_program=key):
                    self.assertEqual(
                        ordinal.sub("typed_SENTINEL", block),
                        ordinal.sub("typed_SENTINEL", newer[key]))

        live_keys, edge_keys, glyph_keys = tuple(
            tuple(item["program_key"] for item in spec["programs"])
            for _, spec, _ in states)
        self.assertEqual({KEY}, set(live_keys) - set(edge_keys))
        self.assertEqual({edge_key}, set(edge_keys) - set(glyph_keys))
        self.assertEqual(
            "d62d138498858962e8b7869042848ee87e3b4fe9c6b042dfdc5ccd577d7d8de9",
            hashlib.sha256(("\n".join(glyph_keys) + "\n").encode()).hexdigest())

    def test_slice_row_is_exact_and_preserves_global_vocabularies(self):
        spec = generate_typed_slice.load_slice(ROOT)
        row = next(item for item in spec["programs"]
                   if item["program_key"] == KEY)
        self.assertEqual({
            "defines": {},
            "glitch_mat4_chain_profile": PROFILE,
            "program_key": KEY,
        }, row)
        # Live-state pin: the current sorted slice has 211 programs. The
        # authenticated key-list hash below covers every later landing and
        # ordinal shift; Glitch's own sorted position remains unchanged.
        self.assertEqual(211, len(spec["programs"]))
        self.assertEqual(
            "29a148b26cfe4f550ac82325810655eb0e5ffad2c3a4e5241e42600bac9f76c1",
            hashlib.sha256(("\n".join(
                item["program_key"] for item in spec["programs"]) + "\n").encode()).hexdigest())
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(17, len(generate_typed_slice.APPROVED_TYPES))
        self.assertNotIn("mat4", generate_typed_slice.APPROVED_TYPES)


if __name__ == "__main__":
    unittest.main()
