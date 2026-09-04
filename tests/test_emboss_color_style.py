from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tests.historical_cross_lane import historical_cross_lane


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "filter/emboss:emboss"
PROFILE = "emboss-color-style-v1"
RAW_SHA256 = "872eff00bdfe411a0dceb66e8b203b5ea1c03015e3eea041d821966354713191"
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources/filter/emboss/emboss.glsl")
MODULE = "tools.glslcpp.frontend.emboss_color_style_profile"


def _profile():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError("Emboss color-style profile module is absent")
    return importlib.import_module(MODULE)


def _analyzed(raw: str | None = None, key: str = KEY,
              defines: dict[str, object] | None = None):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    runtime_defines = {"STYLE": 0} if defines is None else defines
    return analyze_program(parse_program(raw, key, runtime_defines), key)


def _coarse_refreeze(profile, candidate):
    raw = candidate.raw_source.encode()
    normalized = candidate.source.encode()
    return {
        "_RAW_BYTES": len(raw),
        "_RAW_SHA256": hashlib.sha256(raw).hexdigest(),
        "_RAW_IR_SHA256": profile._sha(candidate.raw_source),
        "_NORMALIZED_BYTES": len(normalized),
        "_NORMALIZED_SHA256": hashlib.sha256(normalized).hexdigest(),
        "_NORMALIZED_IR_SHA256": profile._sha(candidate.source),
        "_FUNCTIONS_SHA256": profile._sha(candidate.functions),
        "_DECLARATIONS_SHA256": profile._sha(candidate.declarations),
        "_WHOLE_SHA256": profile._whole(candidate),
        "_INTERFACE_SHA256": profile._interface(candidate),
    }


def _replace_expression(program, target, replacement):
    replacements = 0

    def expression(value):
        nonlocal replacements
        if value is target:
            replacements += 1
            return replacement
        children = tuple(expression(child) for child in value.children)
        return (value if children == value.children else
                dataclasses.replace(value, children=children))

    def statement(value):
        expressions = tuple(expression(item) for item in value.expressions)
        children = tuple(statement(item) for item in value.children)
        return (value if (expressions == value.expressions
                          and children == value.children) else
                dataclasses.replace(value, expressions=expressions,
                                    children=children))

    functions = tuple(dataclasses.replace(
        function, body=tuple(statement(item) for item in function.body))
        for function in program.functions)
    if replacements != 1:
        raise AssertionError(
            f"expected one expression identity replacement, got {replacements}")
    return dataclasses.replace(program, functions=functions)


def _replace_statement(program, target, replacement):
    replacements = 0

    def statement(value):
        nonlocal replacements
        if value is target:
            replacements += 1
            return replacement
        children = tuple(statement(item) for item in value.children)
        return (value if children == value.children else
                dataclasses.replace(value, children=children))

    functions = tuple(dataclasses.replace(
        function, body=tuple(statement(item) for item in function.body))
        for function in program.functions)
    if replacements != 1:
        raise AssertionError(
            f"expected one statement identity replacement, got {replacements}")
    return dataclasses.replace(program, functions=functions)


def _replace_function_body(program, function_id, body):
    replacements = 0
    functions = []
    for function in program.functions:
        if function.id == function_id:
            replacements += 1
            function = dataclasses.replace(function, body=tuple(body))
        functions.append(function)
    if replacements != 1:
        raise AssertionError(
            f"expected one function identity replacement, got {replacements}")
    return dataclasses.replace(program, functions=tuple(functions))


class EmbossColorStyleProfileTests(unittest.TestCase):
    def _assert_post_refreeze_rejected(self, profile, candidate, name):
        replacements = _coarse_refreeze(profile, candidate)
        with self.subTest(name=name), mock.patch.multiple(
                profile, **replacements):
            profile_hash = profile._sha(profile._profile_tuple())
            with mock.patch.object(profile, "_PROFILE_SHA256", profile_hash):
                with self.assertRaises(ValueError):
                    profile.authenticate_emboss_color_style(
                        candidate, replacements["_RAW_SHA256"], PROFILE)
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=replacements["_RAW_SHA256"],
                        emboss_color_style_profile=PROFILE)
                with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                    emit_typed_cpp.render_typed_cpp(
                        candidate, KEY, replacements["_RAW_SHA256"],
                        "emboss_negative", "bind_emboss_negative",
                        emboss_color_style_profile=PROFILE)

    def test_current_frontier_is_local_float_nine_before_profile_admission(self):
        frontier_key = "filter/emboss-frontier:emboss"
        program = _analyzed(key=frontier_key)
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"filter/emboss-frontier:emboss:27:11: unsupported typed type float\[9\]"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        with self.assertRaisesRegex(
                emit_typed_cpp.TypedEmissionError,
                r"filter/emboss-frontier:emboss:27:11: unsupported fixed-nine array declaration"):
            emit_typed_cpp.render_typed_cpp(
                program, frontier_key, RAW_SHA256,
                "emboss_probe", "bind_emboss_probe")

    def test_exact_profile_returns_candidate_owned_tables_and_boolean_closure(self):
        profile = _profile()
        program = _analyzed()
        proof = profile.authenticate_emboss_color_style(
            program, RAW_SHA256, PROFILE)

        self.assertIs(proof._candidate, program)
        self.assertIs(profile.apply_emboss_color_style(
            program, RAW_SHA256, PROFILE), program)
        self.assertEqual(
            ("kernel", "offsets", "kernel", "baseOffsetsPx"),
            tuple(table.symbol_name for table in proof.tables))
        self.assertEqual((24, 25, 29, 30),
                         tuple(table.symbol_id for table in proof.tables))
        self.assertEqual((18, 18, 19, 19),
                         tuple(table.owner.id for table in proof.tables))
        self.assertEqual((0, 10, 0, 10),
                         tuple(table.declaration_statement_index
                               for table in proof.tables))
        self.assertEqual((21, 21, 24, 24),
                         tuple(table.loop_statement_index
                               for table in proof.tables))
        self.assertEqual((27, 27, 35, 35),
                         tuple(table.induction_symbol_id
                               for table in proof.tables))
        self.assertEqual(("49:29-49:38", "48:51-48:61",
                          "81:29-81:38", "77:23-77:39"),
                         tuple(profile._span(table.dynamic_read)
                               for table in proof.tables))
        self.assertEqual((9, 9, 9, 9),
                         tuple(len(table.literal_stores)
                               for table in proof.tables))
        self.assertEqual((0, 1, 2, 3, 4, 5, 6, 7, 8),
                         tuple(store.children[0].children[1].literal_value
                               for store in proof.tables[0].literal_stores))
        self.assertEqual(("110:26-110:54", "110:63-110:96"),
                         tuple(profile._span(item)
                               for item in proof.equalities))
        self.assertEqual(("110:22-110:55", "110:59-110:97"),
                         tuple(profile._span(item)
                               for item in proof.reductions))
        for equality, reduction in zip(proof.equalities, proof.reductions):
            self.assertIs(reduction.children[0], equality)
        self.assertIs(proof.full_frame_conjunction.children[0],
                      proof.reductions[0])
        self.assertIs(proof.full_frame_conjunction.children[1],
                      proof.reductions[1])

    def test_profile_rejects_wrong_carrier_key_source_and_define_contract(self):
        profile = _profile()
        program = _analyzed()
        candidates = (
            (program, RAW_SHA256, None),
            (program, RAW_SHA256, "wrong"),
            (program, "0" * 64, PROFILE),
            (dataclasses.replace(program, key="filter/other:other"),
             RAW_SHA256, PROFILE),
            (_analyzed(defines={}), RAW_SHA256, PROFILE),
            (_analyzed(defines={"STYLE": 1}), RAW_SHA256, PROFILE),
            (_analyzed(defines={"STYLE": 0, "EXTRA": 1}), RAW_SHA256, PROFILE),
        )
        for candidate, source_hash, carrier in candidates:
            with self.subTest(candidate=(candidate.key, source_hash, carrier)), \
                    self.assertRaises(ValueError):
                profile.authenticate_emboss_color_style(
                    candidate, source_hash, carrier)

    def test_exact_profile_admits_validator(self):
        program = _analyzed()
        self.assertIn("emboss_color_style_profile",
                      inspect.signature(
                          generate_typed_slice.validate_capabilities).parameters)
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=RAW_SHA256,
            emboss_color_style_profile=PROFILE)

    def test_exact_profile_admits_emitter_with_only_scoped_new_shapes(self):
        program = _analyzed()
        self.assertIn("emboss_color_style_profile",
                      inspect.signature(
                          emit_typed_cpp.render_typed_cpp).parameters)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256, "emboss_probe", "bind_emboss_probe",
            emboss_color_style_profile=PROFILE)
        self.assertEqual(2, rendered.count("std::array<double, 9> kernel"))
        self.assertEqual(1, rendered.count("std::array<glsl::Vec2, 9> offsets"))
        self.assertEqual(1, rendered.count(
            "std::array<glsl::Vec2, 9> baseOffsetsPx"))
        self.assertEqual(2, rendered.count("glsl::equal("))
        self.assertEqual(2, rendered.count("glsl::all("))
        self.assertNotIn("std::vector", rendered)
        self.assertNotIn("std::map", rendered)

    def test_exact_profile_materializes_two_reachable_texture_numerators(self):
        profile = _profile()
        program = _analyzed()
        proof = profile.authenticate_emboss_color_style(
            program, RAW_SHA256, PROFILE)
        self.assertEqual(
            ("48:46-48:115", "80:46-80:90"),
            tuple(profile._span(item)
                  for item in proof.texture_coordinate_numerators))
        self.assertEqual(
            ("48:46-48:149", "80:46-80:124"),
            tuple(profile._span(item)
                  for item in proof.texture_coordinate_divisions))
        for numerator, division in zip(
                proof.texture_coordinate_numerators,
                proof.texture_coordinate_divisions):
            self.assertIs(division.children[0], numerator)

        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256, "emboss_probe", "bind_emboss_probe",
            emboss_color_style_profile=PROFILE)
        texture_lines = [line for line in rendered.splitlines()
                         if "texSample =" in line and "sample_texture" in line]
        self.assertEqual(2, len(texture_lines))
        for line in texture_lines:
            self.assertIn("/ glsl::Vec2(texture_size", line)
            self.assertIn("glsl::Vec2((", line)
            numerator_start = line.index("glsl::Vec2((")
            divide = line.index(" / glsl::Vec2(texture_size")
            self.assertLess(numerator_start, divide)

    def test_coarse_source_locks_reject_behavioral_table_and_boolean_mutations(self):
        profile = _profile()
        raw = SOURCE.read_text(encoding="utf-8")
        mutations = (
            ("default-kernel", "kernel[0] = -2.0;", "kernel[0] = -1.0;", 2),
            ("default-offset", "offsets[0] = vec2(-texelSize.x, -texelSize.y);",
             "offsets[0] = vec2(texelSize.x, -texelSize.y);", 1),
            ("general-kernel",
             "vec3 colorGeneralEmboss(vec2 uv, vec2 texelSize) {\n"
             "    float kernel[9];\n"
             "    kernel[0] = -2.0;",
             "vec3 colorGeneralEmboss(vec2 uv, vec2 texelSize) {\n"
             "    float kernel[9];\n"
             "    kernel[0] = -1.0;", 1),
            ("general-offset", "baseOffsetsPx[0] = vec2(-1.0, -1.0);",
             "baseOffsetsPx[0] = vec2(1.0, -1.0);", 1),
            ("resolution-equality", "equal(fullResolution, resolution)",
             "notEqual(fullResolution, resolution)", 1),
            ("conjunction", ")) && all(equal(fullResolution",
             ")) || all(equal(fullResolution", 1),
        )
        for name, anchor, replacement, expected_count in mutations:
            self.assertEqual(expected_count, raw.count(anchor), name)
            changed = raw.replace(anchor, replacement, 1)
            candidate = _analyzed(changed)
            with self.subTest(name=name), self.assertRaises(ValueError):
                profile.authenticate_emboss_color_style(
                    candidate, hashlib.sha256(changed.encode()).hexdigest(),
                    PROFILE)

    def test_detailed_profile_rejects_complete_matrix_after_coarse_refreeze(self):
        profile = _profile()
        raw = SOURCE.read_text(encoding="utf-8")
        source_mutations = (
            ("duplicate-default-index",
             "vec3 colorDefaultEmboss(vec2 uv, vec2 texelSize) {\n"
             "    float kernel[9];\n"
             "    kernel[0] = -2.0; kernel[1] = -1.0;",
             "vec3 colorDefaultEmboss(vec2 uv, vec2 texelSize) {\n"
             "    float kernel[9];\n"
             "    kernel[0] = -2.0; kernel[0] = -1.0;"),
            ("general-read-not-induction",
             "conv += texSample * kernel[i];\n    }\n    return conv;\n}\n\nvec3 grayEmboss",
             "conv += texSample * kernel[0];\n    }\n    return conv;\n}\n\nvec3 grayEmboss"),
            ("resolution-operand-order",
             "equal(fullResolution, resolution)",
             "equal(resolution, fullResolution)"),
            ("fullframe-consumer-invert",
             "fullFrame ? texelSize :", "!fullFrame ? texelSize :"),
            ("extra-default-reference",
             "offsets[8] = vec2(texelSize.x, texelSize.y);\n\n"
             "    vec3 conv = vec3(0.0);\n"
             "    for (int i = 0; i < 9; i++) {",
             "offsets[8] = vec2(texelSize.x, texelSize.y);\n\n"
             "    vec3 conv = vec3(kernel[0]);\n"
             "    for (int i = 0; i < 9; i++) {"),
            ("source-level-extra-numerator-materialization",
             "((uv + offsets[i] * amount * renderScale) * fullResolution "
             "- tileOffset) / vec2(textureSize(inputTex, 0))",
             "vec2((uv + offsets[i] * amount * renderScale) * "
             "fullResolution - tileOffset) / "
             "vec2(textureSize(inputTex, 0))"),
            # The four oracle rows that are intentionally structural-only.
            ("structural-tile-equal-to-notequal",
             "all(equal(tileOffset, vec2(0.0)))",
             "all(notEqual(tileOffset, vec2(0.0)))"),
            ("structural-tile-all-to-any",
             "all(equal(tileOffset, vec2(0.0)))",
             "any(equal(tileOffset, vec2(0.0)))"),
            ("structural-true-arm-use-canvas-size",
             "fullFrame ? texelSize : 1.0 / fullResolution",
             "fullFrame ? 1.0 / fullResolution : 1.0 / fullResolution"),
            ("structural-fullframe-force-false",
             "bool fullFrame = all(equal(tileOffset, vec2(0.0))) && "
             "all(equal(fullResolution, resolution));",
             "bool fullFrame = false;"),
            ("pre-initialization-read",
             "vec3 colorDefaultEmboss(vec2 uv, vec2 texelSize) {\n"
             "    float kernel[9];\n"
             "    kernel[0] = -2.0;",
             "vec3 colorDefaultEmboss(vec2 uv, vec2 texelSize) {\n"
             "    float kernel[9];\n"
             "    float preRead = kernel[0];\n"
             "    kernel[0] = -2.0;"),
            ("post-initialization-write",
             "conv += texSample * kernel[i];\n"
             "    }\n"
             "    // COLOR_DEFAULT_EXACT_END",
             "conv += texSample * kernel[i];\n"
             "    }\n"
             "    kernel[0] = 0.0;\n"
             "    // COLOR_DEFAULT_EXACT_END"),
            ("array-copy-alias",
             "    offsets[8] = vec2(texelSize.x, texelSize.y);\n\n"
             "    vec3 conv = vec3(0.0);\n"
             "    for (int i = 0; i < 9; i++) {",
             "    offsets[8] = vec2(texelSize.x, texelSize.y);\n\n"
             "    float copiedKernel[9];\n"
             "    copiedKernel = kernel;\n"
             "    vec3 conv = vec3(0.0);\n"
             "    for (int i = 0; i < 9; i++) {"),
            ("extra-bvec-storage",
             "bool fullFrame = all(equal(tileOffset, vec2(0.0)))",
             "bvec2 spareBvec = equal(tileOffset, vec2(0.0));\n"
             "    bool fullFrame = all(equal(tileOffset, vec2(0.0)))"),
            ("bvec-index",
             "bool fullFrame = all(equal(tileOffset, vec2(0.0)))",
             "bool spareLane = equal(tileOffset, vec2(0.0)).x;\n"
             "    bool fullFrame = all(equal(tileOffset, vec2(0.0)))"),
            ("bvec-escape",
             "void main() {",
             "bool consumeBvec(bvec2 value) { return all(value); }\n\n"
             "void main() {"),
            ("ternary-arm-order",
             "fullFrame ? texelSize : 1.0 / fullResolution",
             "fullFrame ? 1.0 / fullResolution : texelSize"),
            ("extra-fullframe-consumer",
             "vec2 colorTexelSize = fullFrame ? texelSize : "
             "1.0 / fullResolution;",
             "vec2 colorTexelSize = fullFrame ? texelSize : "
             "1.0 / fullResolution;\n"
             "    bool copiedFullFrame = fullFrame;"),
            ("resource-census",
             "uniform float renderScale;",
             "uniform float renderScale;\nuniform float spareUniform;"),
            ("interface-census",
             "out vec4 fragColor;",
             "out vec4 fragColor;\nout vec4 spareOutput;"),
            ("function-census",
             "vec3 sampleGlobal(vec2 globalUV) {",
             "float spareFunction() { return 0.0; }\n\n"
             "vec3 sampleGlobal(vec2 globalUV) {"),
            ("global-payload",
             "const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);",
             "const vec3 LUMA = vec3(0.2127, 0.7152, 0.0722);"),
            ("call-graph",
             "result = colorDefaultEmboss(uv, colorTexelSize);",
             "result = grayEmboss(uv, origColor.rgb);"),
        )
        for name, anchor, replacement in source_mutations:
            self.assertEqual(1, raw.count(anchor), name)
            changed = raw.replace(anchor, replacement)
            candidate = _analyzed(changed)
            self._assert_post_refreeze_rejected(profile, candidate, name)

        program = _analyzed()
        proof = profile.authenticate_emboss_color_style(
            program, RAW_SHA256, PROFILE)
        ir_mutations = []

        # Each of the four owned declarations gets independent extent, element,
        # and initializer attacks. These are forged analyzed candidates, so the
        # detailed profile—not the source digest—must reject them.
        for index, table in enumerate(proof.tables):
            other = proof.tables[1 if index % 2 == 0 else 0]
            ir_mutations.extend((
                (f"table-{index}-declaration-extent",
                 _replace_expression(
                     program, table.declaration,
                     dataclasses.replace(
                         table.declaration,
                         type=dataclasses.replace(
                             table.declaration.type, size=10)))),
                (f"table-{index}-declaration-element",
                 _replace_expression(
                     program, table.declaration,
                     dataclasses.replace(
                         table.declaration,
                         type=dataclasses.replace(
                             table.declaration.type,
                             element=other.declaration.type.element)))),
                (f"table-{index}-declaration-initializer",
                 _replace_expression(
                     program, table.declaration,
                     dataclasses.replace(
                         table.declaration,
                         children=(table.literal_stores[0].children[1],)))),
            ))

            first = table.literal_stores[0]
            second = table.literal_stores[1]
            literal_index = first.children[0].children[1]
            ir_mutations.extend((
                (f"table-{index}-store-index",
                 _replace_expression(
                     program, literal_index,
                     dataclasses.replace(literal_index, literal="8",
                                         literal_value=8))),
                (f"table-{index}-store-payload",
                 _replace_expression(
                     program, first,
                     dataclasses.replace(
                         first, children=(first.children[0],
                                          second.children[1])))),
            ))
            owner_body = list(table.owner.body)
            first_index, second_index = table.literal_store_statement_indices[:2]
            reordered = owner_body.copy()
            reordered[first_index], reordered[second_index] = (
                reordered[second_index], reordered[first_index])
            missing = owner_body.copy()
            del missing[first_index]
            extra = owner_body.copy()
            extra.insert(first_index, owner_body[first_index])
            ir_mutations.extend((
                (f"table-{index}-store-order",
                 _replace_function_body(program, table.owner.id, reordered)),
                (f"table-{index}-store-count-missing",
                 _replace_function_body(program, table.owner.id, missing)),
                (f"table-{index}-store-count-extra",
                 _replace_function_body(program, table.owner.id, extra)),
            ))

            other_induction = proof.tables[2 if index < 2 else 0].induction_symbol_id
            read_index = table.dynamic_read.children[1]
            ir_mutations.append((
                f"table-{index}-cross-owner-induction-read",
                _replace_expression(
                    program, read_index,
                    dataclasses.replace(read_index,
                                        symbol_id=other_induction))))

        for loop_table in (proof.tables[0], proof.tables[2]):
            loop = loop_table.loop_statement
            loop_proof = loop.loop_proof
            self.assertIsNotNone(loop_proof)
            ir_mutations.extend((
                (f"loop-{loop_table.owner.id}-bound",
                 _replace_statement(
                     program, loop,
                     dataclasses.replace(
                         loop, loop_proof=dataclasses.replace(
                             loop_proof, bound_value=8, trip_count=8)))),
                (f"loop-{loop_table.owner.id}-update",
                 _replace_statement(
                     program, loop,
                     dataclasses.replace(
                         loop, loop_proof=dataclasses.replace(
                             loop_proof, update="--")))),
                (f"loop-{loop_table.owner.id}-induction",
                 _replace_statement(
                     program, loop,
                     dataclasses.replace(
                         loop, loop_proof=dataclasses.replace(
                             loop_proof, induction_symbol_id=999)))),
                (f"loop-{loop_table.owner.id}-body",
                 _replace_statement(
                     program, loop_table.loop_body,
                     dataclasses.replace(
                         loop_table.loop_body,
                         children=loop_table.loop_body.children[:-1]))),
            ))

        equality0, equality1 = proof.equalities
        reduction0, reduction1 = proof.reductions
        ir_mutations.extend((
            ("equality-signature",
             _replace_expression(
                 program, equality0,
                 dataclasses.replace(equality0, signature_id=-999))),
            ("equality-span-path",
             _replace_expression(
                 program, equality0,
                 dataclasses.replace(equality0, span=equality1.span))),
            ("equality-operand-order",
             _replace_expression(
                 program, equality0,
                 dataclasses.replace(
                     equality0, children=tuple(reversed(equality0.children))))),
            ("reduction-signature",
             _replace_expression(
                 program, reduction0,
                 dataclasses.replace(reduction0, signature_id=-999))),
            ("reduction-parent-child",
             _replace_expression(
                 program, reduction0,
                 dataclasses.replace(reduction0, children=(equality1,)))),
            ("conjunction-order",
             _replace_expression(
                 program, proof.full_frame_conjunction,
                 dataclasses.replace(
                     proof.full_frame_conjunction,
                     children=(reduction1, reduction0)))),
            ("conditional-branch-order",
             _replace_expression(
                 program, proof.color_texel_conditional,
                 dataclasses.replace(
                     proof.color_texel_conditional,
                     children=(proof.color_texel_conditional.children[0],
                               proof.color_texel_conditional.children[2],
                               proof.color_texel_conditional.children[1])))),
        ))

        for name, candidate in ir_mutations:
            self._assert_post_refreeze_rejected(profile, candidate, name)

    def test_validator_and_emitter_reauthenticate_candidate_owned_proof(self):
        profile = _profile()
        program = _analyzed()
        separate = _analyzed()
        exact = profile.authenticate_emboss_color_style(
            program, RAW_SHA256, PROFILE)
        cross = profile.authenticate_emboss_color_style(
            separate, RAW_SHA256, PROFILE)
        copied_equality = copy.deepcopy(exact.equalities[0])
        forged = dataclasses.replace(
            exact, equalities=(copied_equality, exact.equalities[1]))
        forged_numerator = dataclasses.replace(
            exact,
            texture_coordinate_numerators=(
                copy.deepcopy(exact.texture_coordinate_numerators[0]),
                exact.texture_coordinate_numerators[1]))
        missing_materialization = dataclasses.replace(
            exact,
            texture_coordinate_divisions=(
                exact.texture_coordinate_divisions[0],))
        duplicate_materialization = dataclasses.replace(
            exact,
            texture_coordinate_divisions=(
                exact.texture_coordinate_divisions[0],
                exact.texture_coordinate_divisions[0]))
        table0 = exact.tables[0]
        forged_declaration_table = dataclasses.replace(
            table0, declaration=copy.deepcopy(table0.declaration))
        forged_store_table = dataclasses.replace(
            table0,
            literal_stores=(copy.deepcopy(table0.literal_stores[0]),
                            *table0.literal_stores[1:]))
        forged_read_table = dataclasses.replace(
            table0, dynamic_read=copy.deepcopy(table0.dynamic_read))
        forged_loop_table = dataclasses.replace(
            table0, loop_statement=copy.deepcopy(table0.loop_statement))
        shallow_declaration_statement_table = dataclasses.replace(
            table0,
            declaration_statement=dataclasses.replace(
                table0.declaration_statement))
        shallow_store_statements = list(table0.literal_store_statements)
        shallow_store_statements[0] = dataclasses.replace(
            shallow_store_statements[0])
        shallow_store_statement_table = dataclasses.replace(
            table0, literal_store_statements=tuple(shallow_store_statements))
        shallow_loop_body = dataclasses.replace(table0.loop_body)
        shallow_loop_children = list(table0.loop_statement.children)
        shallow_loop_children[1] = shallow_loop_body
        shallow_loop_table = dataclasses.replace(
            table0,
            loop_statement=dataclasses.replace(
                table0.loop_statement,
                children=tuple(shallow_loop_children)),
            loop_body=shallow_loop_body)
        shallow_fullframe_conjunction = dataclasses.replace(
            exact.full_frame_conjunction)
        shallow_fullframe_declaration = dataclasses.replace(
            exact.full_frame_declaration,
            children=(shallow_fullframe_conjunction,))
        shallow_fullframe_chain = dataclasses.replace(
            exact,
            full_frame_declaration=shallow_fullframe_declaration,
            full_frame_conjunction=shallow_fullframe_conjunction)
        shallow_color_conditional = dataclasses.replace(
            exact.color_texel_conditional)
        shallow_color_declaration = dataclasses.replace(
            exact.color_texel_declaration,
            children=(shallow_color_conditional,))
        shallow_color_chain = dataclasses.replace(
            exact,
            color_texel_declaration=shallow_color_declaration,
            color_texel_conditional=shallow_color_conditional)
        for name, proof in (
                ("cross-candidate", cross),
                ("forged-parent", forged),
                ("forged-materialization-numerator", forged_numerator),
                ("missing-materialization", missing_materialization),
                ("duplicate-materialization", duplicate_materialization),
                ("forged-table-declaration", dataclasses.replace(
                    exact, tables=(forged_declaration_table,
                                   *exact.tables[1:]))),
                ("forged-table-store", dataclasses.replace(
                    exact, tables=(forged_store_table, *exact.tables[1:]))),
                ("forged-table-read", dataclasses.replace(
                    exact, tables=(forged_read_table, *exact.tables[1:]))),
                ("forged-table-loop", dataclasses.replace(
                    exact, tables=(forged_loop_table, *exact.tables[1:]))),
                ("shallow-table-declaration-statement", dataclasses.replace(
                    exact, tables=(shallow_declaration_statement_table,
                                   *exact.tables[1:]))),
                ("shallow-table-store-statement", dataclasses.replace(
                    exact, tables=(shallow_store_statement_table,
                                   *exact.tables[1:]))),
                ("shallow-table-loop-body-chain", dataclasses.replace(
                    exact, tables=(shallow_loop_table, *exact.tables[1:]))),
                ("shallow-fullframe-parent-chain", shallow_fullframe_chain),
                ("shallow-color-parent-chain", shallow_color_chain)):
            for authority, function, keyword in (
                    ("validator", generate_typed_slice.validate_capabilities,
                     {"declared": generate_typed_slice.APPROVED_CAPABILITIES}),
                    ("emitter", emit_typed_cpp.render_typed_cpp,
                     {"program_key": KEY, "source_hash": RAW_SHA256,
                      "namespace": "emboss_probe", "factory": "bind_probe"})):
                with self.subTest(name=name, authority=authority), \
                        mock.patch.object(
                            generate_typed_slice if authority == "validator"
                            else emit_typed_cpp,
                            "authenticate_emboss_color_style",
                            return_value=proof):
                    with self.assertRaises(
                            (generate_typed_slice.GeneratorError,
                             emit_typed_cpp.TypedEmissionError)) as caught:
                        if authority == "validator":
                            function(
                                program, keyword["declared"],
                                source_hash=RAW_SHA256,
                                emboss_color_style_profile=PROFILE)
                        else:
                            function(
                                program, keyword["program_key"],
                                keyword["source_hash"], keyword["namespace"],
                                keyword["factory"],
                                emboss_color_style_profile=PROFILE)
                    if name.startswith("shallow-"):
                        self.assertIn(
                            "candidate ownership, table, or boolean parent "
                            "mismatch", str(caught.exception))

    def test_oracle_check_uses_explicit_immutable_snapshot(self):
        package = ROOT / "docs/port-engineering/arrays/emboss-parity"
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest(
                "authority-dependent Emboss oracle skipped: "
                "NOISEMAKER_CPU_ROOT is unset")
        authority_root = pathlib.Path(configured)
        if not authority_root.is_dir():
            self.skipTest(
                "authority-dependent Emboss oracle skipped: "
                f"NOISEMAKER_CPU_ROOT is missing: {authority_root}")
        command = ("node", str(
            package / "emboss_parity_oracle_generator.mjs"), "--check",
                   "--cpu-root", str(authority_root))
        expected = "17 renders, 29 behavioral mutations, 4 structural-only"
        with tempfile.TemporaryDirectory(
                prefix="noisemaker-emboss181-checks-",
                dir=os.environ.get("TMPDIR", tempfile.gettempdir())) as temp:
            environment = os.environ.copy()
            environment.update({
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPYCACHEPREFIX": str(pathlib.Path(temp) / "pycache"),
                "TMPDIR": temp,
                "XDG_CACHE_HOME": str(pathlib.Path(temp) / "cache"),
            })
            completed = subprocess.run(
                command, cwd=ROOT, env=environment, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                check=False)
            self.assertEqual(
                0, completed.returncode,
                "oracle check failed:\nstdout:\n"
                f"{completed.stdout}\nstderr:\n{completed.stderr}")
            self.assertIn(expected, completed.stdout)

    def _require_live_checkout(self) -> pathlib.Path:
        """The generator resolves the live checkout before it validates
        --cpu-root, so every guard that drives it needs the live checkout to
        exist. Name the resource instead of erroring on its absence."""
        configured = os.environ.get("NOISEMAKER_FOR_CPU")
        if not configured:
            self.skipTest(
                "live-checkout-dependent Emboss guard skipped: "
                "NOISEMAKER_FOR_CPU is unset")
        live = pathlib.Path(configured)
        # Unset means the machine has no live checkout: skip. Set-but-wrong is
        # a misconfiguration and stays fatal, which is the contract the
        # handoff publishes for every NOISEMAKER_* root.
        self.assertTrue(
            live.is_dir(),
            f"NOISEMAKER_FOR_CPU is set but is not a directory: {live}")
        return live

    def test_oracle_check_rejects_a_cpu_root_inside_cpp_repository(self):
        live = self._require_live_checkout()
        package = ROOT / "docs/port-engineering/arrays/emboss-parity"
        completed = subprocess.run(
            ("node", str(package / "emboss_parity_oracle_generator.mjs"),
             "--check", "--cpu-root", str(ROOT)),
            cwd=ROOT, env={**os.environ, "NOISEMAKER_FOR_CPU": str(live)},
            text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(0, completed.returncode)
        self.assertIn(
            "--cpu-root must not live inside the C++ repository",
            completed.stderr)

    def _run_oracle_guard_test(self, *arguments, env_overrides=None):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured or not pathlib.Path(configured).is_dir():
            self.skipTest("NOISEMAKER_CPU_ROOT snapshot is unavailable")
        package = ROOT / "docs/port-engineering/arrays/emboss-parity"
        environment = os.environ.copy()
        environment.update(env_overrides or {})
        return subprocess.run(
            ("node", str(package / "emboss_parity_oracle_generator.mjs"),
             *arguments, "--cpu-root", configured),
            cwd=ROOT, env=environment, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def test_oracle_rejects_duplicate_mode_flags(self):
        completed = self._run_oracle_guard_test("--check", "--write")
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("choose exactly one of --write or --check", completed.stderr)

    def test_oracle_rejects_missing_live_checkout_guard(self):
        completed = self._run_oracle_guard_test(
            "--check", env_overrides={
                "NOISEMAKER_FOR_CPU": str(ROOT / "missing-noisemaker-for-cpu"),
            })
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("live noisemaker-for-cpu checkout does not exist",
                      completed.stderr)

    def test_oracle_realpaths_symlinked_cpp_root_containment(self):
        live = self._require_live_checkout()
        package = ROOT / "docs/port-engineering/arrays/emboss-parity"
        with tempfile.TemporaryDirectory(
                prefix="noisemaker-emboss181-symlink-",
                dir=os.environ.get("TMPDIR", tempfile.gettempdir())) as temp:
            symlinked_cpp_root = pathlib.Path(temp) / "cpp-root"
            symlinked_cpp_root.symlink_to(ROOT, target_is_directory=True)
            completed = subprocess.run(
                ("node", str(package / "emboss_parity_oracle_generator.mjs"),
                 "--check", "--cpu-root", str(symlinked_cpp_root)),
                cwd=ROOT,
                env={**os.environ, "NOISEMAKER_FOR_CPU": str(live)},
                text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(0, completed.returncode)
        self.assertIn(
            "--cpu-root must not live inside the C++ repository",
            completed.stderr)

    def test_oracle_rejects_unpinned_transitive_dependency_mutation(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured or not pathlib.Path(configured).is_dir():
            self.skipTest("NOISEMAKER_CPU_ROOT snapshot is unavailable")
        with tempfile.TemporaryDirectory(
                prefix="noisemaker-emboss181-transitive-",
                dir=os.environ.get("TMPDIR", tempfile.gettempdir())) as temp:
            mutated = pathlib.Path(temp) / "cpu"
            shutil.copytree(configured, mutated)
            runtime = mutated / "src/csl/runtime.js"
            runtime.write_text(runtime.read_text(encoding="utf-8")
                               + "\nexport const unpinnedMutation = 1\n",
                               encoding="utf-8")
            completed = subprocess.run(
                ("node", str(ROOT /
                 "docs/port-engineering/arrays/emboss-parity/"
                 "emboss_parity_oracle_generator.mjs"), "--check",
                 "--cpu-root", str(mutated)),
                cwd=ROOT, env=os.environ.copy(), text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("CPU import closure mismatch", completed.stderr)

    def test_oracle_rejects_nonliteral_dynamic_import(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured or not pathlib.Path(configured).is_dir():
            self.skipTest("NOISEMAKER_CPU_ROOT snapshot is unavailable")
        with tempfile.TemporaryDirectory(
                prefix="noisemaker-emboss181-dynamic-import-",
                dir=os.environ.get("TMPDIR", tempfile.gettempdir())) as temp:
            mutated = pathlib.Path(temp) / "cpu"
            shutil.copytree(configured, mutated)
            runtime = mutated / "src/csl/runtime.js"
            runtime.write_text(runtime.read_text(encoding="utf-8")
                               + "\nvoid import(runtimeSpecifier)\n",
                               encoding="utf-8")
            completed = subprocess.run(
                ("node", str(ROOT /
                 "docs/port-engineering/arrays/emboss-parity/"
                 "emboss_parity_oracle_generator.mjs"), "--check",
                 "--cpu-root", str(mutated)),
                cwd=ROOT, env=os.environ.copy(), text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("nonliteral dynamic import", completed.stderr)

    def test_oracle_report_commands_require_explicit_cpu_root(self):
        package = ROOT / "docs/port-engineering/arrays/emboss-parity"
        report = (package / "emboss-parity-oracle-report.md").read_text(
            encoding="utf-8")
        for mode in ("--write", "--check"):
            self.assertIn(
                f"emboss_parity_oracle_generator.mjs {mode} "
                '--cpu-root "$NOISEMAKER_CPU_ROOT"', report)

    def test_include_and_frontend_probe_no_write_checks(self):
        package = ROOT / "docs/port-engineering/arrays/emboss-parity"
        commands = (
            ("include", (sys.executable, str(
                package / "generate_emboss_native_oracle_include.py"),
                         "--check"),
             "17 cases, 2784 words, 2784 bytes"),
            ("frontend", (sys.executable, str(
                package / "emboss_frontend_probe.py"), "--check"),
             '"program_key": "filter/emboss:emboss"'),
        )
        with tempfile.TemporaryDirectory(
                prefix="noisemaker-emboss181-checks-",
                dir=os.environ.get("TMPDIR", tempfile.gettempdir())) as temp:
            environment = os.environ.copy()
            environment.update({
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPYCACHEPREFIX": str(pathlib.Path(temp) / "pycache"),
                "TMPDIR": temp,
                "XDG_CACHE_HOME": str(pathlib.Path(temp) / "cache"),
            })
            for name, command, expected in commands:
                with self.subTest(name=name):
                    completed = subprocess.run(
                        command, cwd=ROOT, env=environment, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        check=False)
                    self.assertEqual(
                        0, completed.returncode,
                        f"{name} check failed:\nstdout:\n{completed.stdout}"
                        f"\nstderr:\n{completed.stderr}")
                    self.assertIn(expected, completed.stdout)

    def test_slice_row_is_exact_and_preserves_frozen_vocabularies(self):
        spec = generate_typed_slice.load_slice(ROOT)
        rows = [item for item in spec["programs"]
                if item["program_key"] == KEY]
        self.assertEqual([{
            "defines": {"STYLE": 0},
            "emboss_color_style_profile": PROFILE,
            "program_key": KEY,
        }], rows)
        # Live-state pin: the current sorted slice has 211 programs. The
        # authenticated key-list hash below covers all later landings and
        # ordinal shifts; Emboss's own row/index remains unchanged. The
        # frozen vocabularies below stay at 44/17.
        self.assertEqual(211, len(spec["programs"]))
        self.assertEqual(
            "29a148b26cfe4f550ac82325810655eb0e5ffad2c3a4e5241e42600bac9f76c1",
            hashlib.sha256(("\n".join(
                item["program_key"] for item in spec["programs"])
                + "\n").encode()).hexdigest())
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(17, len(generate_typed_slice.APPROVED_TYPES))
        self.assertNotIn("bvec2", generate_typed_slice.APPROVED_TYPES)
        self.assertNotIn("float[9]", generate_typed_slice.APPROVED_TYPES)

    def test_slice_schema_accepts_only_one_exact_noncolliding_emboss_carrier(self):
        exact = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text(
            encoding="utf-8"))
        row = next(item for item in exact["programs"]
                   if item["program_key"] == KEY)
        self.assertEqual({
            "defines": {"STYLE": 0},
            "emboss_color_style_profile": PROFILE,
            "program_key": KEY,
        }, row)

        mutations = {}
        wrong = copy.deepcopy(exact)
        next(item for item in wrong["programs"] if item["program_key"] == KEY)[
            "emboss_color_style_profile"] = "wrong"
        mutations["wrong"] = wrong
        missing = copy.deepcopy(exact)
        del next(item for item in missing["programs"]
                 if item["program_key"] == KEY)["emboss_color_style_profile"]
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
                 "emboss_color_style_profile"] = PROFILE
        mutations["foreign"] = foreign
        collision = copy.deepcopy(exact)
        next(item for item in collision["programs"]
             if item["program_key"] == KEY)[
                 "glitch_mat4_chain_profile"] = "glitch-mat4-chain-v1"
        mutations["carrier-collision"] = collision
        no_defines = copy.deepcopy(exact)
        next(item for item in no_defines["programs"]
             if item["program_key"] == KEY)["defines"] = {}
        mutations["missing-style"] = no_defines
        style_one = copy.deepcopy(exact)
        next(item for item in style_one["programs"]
             if item["program_key"] == KEY)["defines"] = {"STYLE": 1}
        mutations["style-one"] = style_one
        extra_define = copy.deepcopy(exact)
        next(item for item in extra_define["programs"]
             if item["program_key"] == KEY)["defines"] = {
                 "STYLE": 0, "EXTRA": 1}
        mutations["extra-define"] = extra_define

        for name, candidate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                repository = pathlib.Path(temp)
                target = repository / "tools/glslcpp/typed_slice.json"
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.load_slice(repository)

    def test_generator_registers_exact_emboss_program_and_manifest_carrier(self):
        outputs = generate_typed_slice.generate_outputs(ROOT)
        source = outputs["src/typed_generated/typed_slice.cpp"].decode()
        manifest = __import__("json").loads(
            outputs["src/typed_generated/typed_manifest.json"])
        self.assertEqual(1, source.count(
            "// Typed IR program: filter/emboss:emboss\n"))
        self.assertEqual(1, source.count(
            "Kernel bind_filter_emboss_emboss("))
        rows = [item for item in manifest["programs"]
                if item["program_key"] == KEY]
        self.assertEqual(1, len(rows))
        self.assertEqual(PROFILE, rows[0]["emboss_color_style_profile"])
        self.assertEqual({"STYLE": 0}, rows[0]["defines"])
        catalog = generate_typed_slice.render_catalog_header(
            generate_typed_slice.load_slice(ROOT)).decode()
        self.assertEqual(1, catalog.count(
            "Kernel bind_filter_emboss_emboss("))

    def test_shape182_is_exact_delta_over_emboss181_glitch180_edge179_and_glyph178(self):
        shape_key = "classicNoisedeck/shapeMixer:shapeMixer"
        glitch_key = "classicNoisedeck/glitch:glitch"
        edge_key = "filter/edge:edge"
        # Every hash and count in this test is a frozen MILESTONE, not a live
        # pin: the chain measures the 182 -> 178 deltas. Shapes183 and
        # `synth/shape:shape` (184) both landed after all five states, so both
        # are removed here to rebuild the 182 milestone. Bumping the frozen
        # hashes to the live state instead would have destroyed what this test
        # measures -- and the frozen hashes are the authority when they
        # disagree with a count. `filter/normalMap:normalMap` (185) and
        # `classicNoisedeck/cellRefract:cellRefract` (186) and
        # `mixer/distortion:distortion` (176) also landed after all five
        # states and join the exclusion set, so the frozen hashes and the
        # 182/181/180/179/178 counts stay exactly as-is.
        live182_spec = copy.deepcopy(generate_typed_slice.load_slice(ROOT))
        with historical_cross_lane(live182_spec):
            historical182_spec = copy.deepcopy(live182_spec)
            historical182_spec["programs"] = [
                item for item in historical182_spec["programs"]
                if item["program_key"] not in {"filter/dither:dither",
                                               "synth/julia:julia",
                                               "classicNoisedeck/moodscape:moodscape",
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
                    "synth/remap:remap", "synth/testPattern:testPattern",
                    "classicNoisedeck/bitEffects:bitEffects",
                                               "classicNoisedeck/colorLab:colorLab",
                                               "classicNoisedeck/noise:noise",
                    "classicNoisedeck/fractal:fractal",
                    "filter/historicPalette:historicPalette", "filter/median:median",
                    "filter/osd:osd", "filter/palette:palette",
                    "filter/spookyTicker:spookyTicker", "filter/texture:texture"}]
            emboss181_spec = copy.deepcopy(historical182_spec)
            emboss181_spec["programs"] = [
                item for item in emboss181_spec["programs"]
                if item["program_key"] != shape_key]
            glitch180_spec = copy.deepcopy(emboss181_spec)
            glitch180_spec["programs"] = [
                item for item in glitch180_spec["programs"]
                if item["program_key"] != KEY]
            edge179_spec = copy.deepcopy(glitch180_spec)
            edge179_spec["programs"] = [
                item for item in edge179_spec["programs"]
                if item["program_key"] != glitch_key]
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
                ("live182", historical182_spec, outputs(historical182_spec)),
                ("emboss181", emboss181_spec, outputs(emboss181_spec)),
                ("glitch180", glitch180_spec, outputs(glitch180_spec)),
                ("edge179", edge179_spec, outputs(edge179_spec)),
                ("glyph178", glyph178_spec, outputs(glyph178_spec)),
            )
        expected_spec_hashes = {
            "live182": "c54c2ca281bbcb6db25b0b5afa45a86c50a6491adf848b384b4b21ed9011826d",
            "emboss181": "bbfd7b261ae94fd9616ec9a50352fe20f759201e517655cb89dc83b0f4cac3ae",
            "glitch180": "ccabcd9f07d62d515c19fd6280743416710cf5ae0a4f56dd9d06451682ffbb4b",
            "edge179": "ec7888e36ad1828a185b80c77ea3915b1cd3fb77a79c6587cf75a94f6490e76f",
            "glyph178": "9c9a47f7ca42097888d9dc4e6869297fa713b9bba47842bf03736ada0ea64347",
        }
        # Re-frozen 2026-08-25 because the DSL/Task-7 emitter now writes
        # FactoryRoute/define metadata into the emitted artifacts. The projection
        # is unchanged (its frozen COUNTS still match), so this measures the same
        # milestone under the new emitter. Derived from a measured regeneration of
        # this test's own projection; see
        # task-7-typed-generator-census-repair.md.
        expected_artifact_hashes = {
            "live182": {
                "src/typed_generated/typed_slice.cpp": "3f108d58d2e06369cf785bd6871592bb554302df7ff1bd3f65bd4545987ce2d0",
                "src/typed_generated/typed_manifest.json": "a64ecabd3f102b49063eaa8aa6cf9a3f4d36f0bc823c75bbff11528ad12f07c3",
                "include/noisemaker/generated/catalog.hpp": "c167d502824e6ee052d404f403c524e75c49ee8d153aed5b7ef18a3bb7d66dc6",
            },
            "emboss181": {
                "src/typed_generated/typed_slice.cpp": "a7225d35d813f7781663287a5f6b335a8d2e052d470f5314860146ce844a3a00",
                "src/typed_generated/typed_manifest.json": "88b2ea6b7e541ef877e439aa7b32191116c47911da1d9ec83c806b6be489c43e",
                "include/noisemaker/generated/catalog.hpp": "afa8e867e782e540a323113549c3b5e6d6f1a7c2abd504846661999359ff4673",
            },
            "glitch180": {
                "src/typed_generated/typed_slice.cpp": "b003b93a26ed7504c39fd052c75811af70b50d96be6ee44ae49fec7a795b9954",
                "src/typed_generated/typed_manifest.json": "721ce86527490b038f4378c7878e135382ba992497d9829015b4f1ace7c316d9",
                "include/noisemaker/generated/catalog.hpp": "dedfbfa3f14fe7e0267a5ccac9a6d385717a64cded35d0374cf7e4320142c1f2",
            },
            "edge179": {
                "src/typed_generated/typed_slice.cpp": "67c70a8a66792d57844d50a8409757891264a951e6b56d06ba41bded78ff7e3f",
                "src/typed_generated/typed_manifest.json": "0225c98b4ad08ff9a3c5036ec49de0464cec13649d369ce92c4de556d765d8a0",
                "include/noisemaker/generated/catalog.hpp": "b493116184614b37edc2416ebb9c16822bab9032aaadc28e60650020f33b8f42",
            },
            "glyph178": {
                "src/typed_generated/typed_slice.cpp": "05c57f4e5c38c4fd6e1afae4ed1e222237d76b2e51cb65ff8d0478d21db9f3be",
                "src/typed_generated/typed_manifest.json": "0da0d1d4f140048f4c3d729c5b4159cbd7d08c8f62cb59a6601f613ab071c26a",
                "include/noisemaker/generated/catalog.hpp": "a9e99e5bc57bb06d2e0307b8255fc39a2fb769b7e9aff808e18b2bd4de1b4f53",
            },
        }
        for label, spec, rendered in states:
            canonical = (json.dumps(spec, indent=2, sort_keys=True)
                         + "\n").encode()
            self.assertEqual(expected_spec_hashes[label],
                             hashlib.sha256(canonical).hexdigest())
            for path, digest in expected_artifact_hashes[label].items():
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

        rendered_states = [rendered for _, _, rendered in states]
        block_states = [blocks(rendered[
            "src/typed_generated/typed_slice.cpp"])
                        for rendered in rendered_states]
        self.assertEqual((183, 182, 181, 180, 179),
                         tuple(len(item) for item in block_states))
        expected_deltas = (shape_key, KEY, glitch_key, edge_key)
        ordinal = re.compile(r"typed_[0-9]+")
        for newer, older, delta in zip(
                block_states, block_states[1:], expected_deltas):
            self.assertEqual({delta}, set(newer) - set(older))
            for key, block in older.items():
                with self.subTest(delta=delta, retained_program=key):
                    self.assertEqual(
                        ordinal.sub("typed_SENTINEL", block),
                        ordinal.sub("typed_SENTINEL", newer[key]))

        manifests = [json.loads(rendered[
            "src/typed_generated/typed_manifest.json"])
                     for rendered in rendered_states]
        def semantic_rows(manifest):
            # The whole-translation-unit digest is carried TWICE per row since
            # the DSL/Task-7 route work: `output_sha256`, and again as
            # `factory_route.source_sha256` for any route whose `source` IS the
            # generated unit. It is a property of the slice, not of the row, so
            # it differs between any two projections and says nothing about
            # whether a row was perturbed. This drops the second copy on the
            # same grounds the first was always dropped. Keyed on the route's
            # own `source`, so a `custom_adapter` route naming a different file
            # keeps its real digest and stays compared, as does every other
            # field of `factory_route`. See
            # task-7-typed-generator-census-repair.md.
            def semantic_row(item):
                row = {key: value for key, value in item.items()
                       if key != "output_sha256"}
                route = row.get("factory_route")
                if (isinstance(route, dict)
                        and route.get("source")
                        == "src/typed_generated/typed_slice.cpp"):
                    row["factory_route"] = {
                        key: value for key, value in route.items()
                        if key != "source_sha256"}
                return row

            return {item["program_key"]: semantic_row(item)
                    for item in manifest["programs"]}

        for newer, older, delta in zip(
                manifests, manifests[1:], expected_deltas):
            newer_rows = semantic_rows(newer)
            older_rows = semantic_rows(older)
            self.assertEqual({delta}, set(newer_rows) - set(older_rows))
            self.assertEqual(older_rows,
                             {key: newer_rows[key] for key in older_rows})

        catalog_entries = [set(re.findall(
            r"Kernel (bind_[A-Za-z0-9_]+)\(",
            rendered["include/noisemaker/generated/catalog.hpp"].decode()))
                           for rendered in rendered_states]
        for newer, older in zip(catalog_entries, catalog_entries[1:]):
            self.assertEqual(1, len(newer - older))
            self.assertFalse(older - newer)


if __name__ == "__main__":
    unittest.main()
