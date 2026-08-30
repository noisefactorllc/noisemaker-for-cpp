"""Task 35's exact JavaScript-Number compatibility boundary."""

from __future__ import annotations

import dataclasses
import copy
import hashlib
import json
import pathlib
import re
import unittest
from unittest import mock

from tools.glslcpp import check_corpus, generate_typed_slice
from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.generate_kernels import GeneratorError
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.bitwise_scalar_int_ops_profile import (
    PROFILE,
    apply_bitwise_scalar_int_ops,
    authenticate_bitwise_scalar_int_ops,
)
from tools.glslcpp.frontend.semantic import analyze_program
from tests.historical_cross_lane import historical_cross_lane
from tools.glslcpp.frontend.semantic_types import FLOAT, INT


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
KEY = "synth/bitwise:bitwise"
RAW_SHA256 = "1beb9d4b4fff3466587b9c942af3b1a46c0f35a1bf41874c7461c18dcf2f923f"


def _analyzed():
    root = check_corpus._corpus_root(REPOSITORY)
    manifest = json.loads((root / "manifest.json").read_text())
    entry = next(item for item in manifest["programs"]
                 if item["program_key"] == KEY)
    raw = (root / entry["source"]).read_text()
    return analyze_program(parse_program(raw, KEY, {}), KEY)


def _rewrite_expression(program, predicate, replacement):
    def expression(value):
        children = tuple(expression(child) for child in value.children)
        value = dataclasses.replace(value, children=children)
        return replacement(value) if predicate(value) else value

    def statement(value):
        return dataclasses.replace(
            value,
            expressions=tuple(expression(item) for item in value.expressions),
            children=tuple(statement(item) for item in value.children),
        )

    return dataclasses.replace(
        program,
        functions=tuple(dataclasses.replace(
            function,
            body=tuple(statement(item) for item in function.body))
            for function in program.functions),
    )


def _expression_key(value):
    span = value.span
    return (value.kind, span.start_line, span.start_column,
            span.end_line, span.end_column, value.operator, value.symbol_id)


def _rewrite_symbol_storage(program, symbol_id):
    proof = authenticate_bitwise_scalar_int_ops(
        program, RAW_SHA256, PROFILE)
    old_symbol = next(symbol for symbol in proof.number_symbols
                      if symbol.id == symbol_id)
    new_symbol = dataclasses.replace(old_symbol, storage="mutated-storage")

    def expression(value):
        children = tuple(expression(child) for child in value.children)
        return dataclasses.replace(
            value, children=children,
            symbol=(new_symbol if value.symbol is old_symbol else value.symbol))

    def statement(value):
        return dataclasses.replace(
            value,
            expressions=tuple(expression(item) for item in value.expressions),
            children=tuple(statement(item) for item in value.children),
        )

    functions = []
    for function in program.functions:
        signature = dataclasses.replace(
            function.signature,
            parameters=tuple(new_symbol if parameter is old_symbol else parameter
                             for parameter in function.parameters))
        functions.append(dataclasses.replace(
            function, signature=signature,
            body=tuple(statement(item) for item in function.body)))
    return dataclasses.replace(program, functions=tuple(functions))


class Task35BitwiseNumberProfileTests(unittest.TestCase):
    def test_exact_profile_transforms_all_number_and_conversion_regions(self):
        self.assertEqual("bitwise-scalar-int-ops-v2", PROFILE)
        original = _analyzed()
        transformed = apply_bitwise_scalar_int_ops(
            original, RAW_SHA256, PROFILE)
        self.assertIsNot(original, transformed)

        proof = authenticate_bitwise_scalar_int_ops(
            transformed, RAW_SHA256, PROFILE)
        self.assertEqual(10, len(proof.bitwise_nodes))
        self.assertEqual(10, len(proof.arithmetic_nodes))
        self.assertEqual(4, len(proof.int_constructors))
        self.assertEqual(5, len(proof.number_symbols))
        self.assertEqual(44, len(proof.number_expressions))
        self.assertEqual(11, len(proof.number_assignments))
        self.assertEqual(2, len(proof.narrowing_skip_nodes))
        self.assertEqual(3, len(proof.float_identity_nodes))
        self.assertEqual(2, len(proof.float_boundary_nodes))
        self.assertEqual(
            ((19, "a"), (20, "b"), (27, "r"), (38, "x"), (39, "y")),
            tuple((symbol.id, symbol.name) for symbol in proof.number_symbols),
        )
        self.assertTrue(all(symbol.type.display() == "float"
                            for symbol in proof.number_symbols))
        self.assertTrue(all(node.type.display() == "float"
                            for node in proof.number_expressions))
        self.assertTrue(all(node.type.display() == "float"
                            for node in proof.number_assignments))
        self.assertTrue(all(node.type.display() == "float"
                            for node in proof.arithmetic_nodes))
        self.assertTrue(all(node.type.display() == "int"
                            for node in proof.bitwise_nodes))
        self.assertTrue(all(node.type.display() == "int"
                            for node in proof.int_constructors))

    def test_pre_and_post_tree_mutations_fail_closed(self):
        original = _analyzed()
        pre_mutations = {
            "arithmetic": _rewrite_expression(
                original,
                lambda value: (value.kind == "binary" and value.operator == "*"
                               and value.span.start_line == 69),
                lambda value: dataclasses.replace(value, operator="+")),
            "bitwise": _rewrite_expression(
                original,
                lambda value: (value.kind == "binary" and value.operator == "^"
                               and value.span.start_line == 34),
                lambda value: dataclasses.replace(value, operator="|")),
            "constructor": _rewrite_expression(
                original,
                lambda value: (value.kind == "construct"
                               and value.span.start_line == 64),
                lambda value: dataclasses.replace(
                    value, type=FLOAT, constructor_type=FLOAT)),
        }
        for line, start, end, label in (
                (43, 12, 20, "float-identity-r"),
                (43, 23, 31, "float-identity-m"),
                (86, 26, 37, "float-identity-mask"),
                (61, 39, 57, "float-boundary-speed"),
                (86, 40, 55, "float-boundary-mask-plus-one")):
            pre_mutations[label] = _rewrite_expression(
                original,
                lambda value, line=line, start=start, end=end: (
                    value.kind == "construct"
                    and value.span.start_line == line
                    and value.span.start_column == start
                    and value.span.end_column == end),
                lambda value: dataclasses.replace(
                    value, type=INT, constructor_type=INT))
        for name, candidate in pre_mutations.items():
            with self.subTest(pre=name), self.assertRaises(ValueError):
                apply_bitwise_scalar_int_ops(candidate, RAW_SHA256, PROFILE)
        with self.assertRaises(ValueError):
            apply_bitwise_scalar_int_ops(original, "0" * 64, PROFILE)
        with self.assertRaises(ValueError):
            apply_bitwise_scalar_int_ops(
                original, RAW_SHA256, "bitwise-scalar-int-ops-v1")
        with self.assertRaises(ValueError):
            apply_bitwise_scalar_int_ops(
                dataclasses.replace(original, key="synth/other:other"),
                RAW_SHA256, PROFILE)

        transformed = apply_bitwise_scalar_int_ops(
            original, RAW_SHA256, PROFILE)
        proof = authenticate_bitwise_scalar_int_ops(
            transformed, RAW_SHA256, PROFILE)
        post_mutations = []

        def mutate_nodes(label, nodes, replacement):
            for index, target in enumerate(nodes):
                key = _expression_key(target)
                post_mutations.append((
                    f"{label}-{index}",
                    _rewrite_expression(
                        transformed,
                        lambda value, key=key: _expression_key(value) == key,
                        replacement)))

        mutate_nodes(
            "arithmetic", proof.arithmetic_nodes,
            lambda value: dataclasses.replace(value, type=INT))
        mutate_nodes(
            "bitwise", proof.bitwise_nodes,
            lambda value: dataclasses.replace(
                value, operator=("!" if value.kind == "unary" else ">>")))
        mutate_nodes(
            "int-constructor", proof.int_constructors,
            lambda value: dataclasses.replace(
                value, type=FLOAT, constructor_type=FLOAT))
        mutate_nodes(
            "assignment", proof.number_assignments,
            lambda value: dataclasses.replace(value, type=INT))
        mutate_nodes(
            "float-identity", proof.float_identity_nodes,
            lambda value: dataclasses.replace(
                value, type=INT, constructor_type=INT))
        mutate_nodes(
            "float-boundary", proof.float_boundary_nodes,
            lambda value: dataclasses.replace(
                value, type=INT, constructor_type=INT))
        for symbol in proof.number_symbols:
            post_mutations.append((
                f"number-symbol-{symbol.id}",
                _rewrite_symbol_storage(transformed, symbol.id)))

        self.assertEqual(45, len(post_mutations))
        for name, candidate in post_mutations:
            with self.subTest(post=name):
                with self.assertRaises(ValueError):
                    authenticate_bitwise_scalar_int_ops(
                        candidate, RAW_SHA256, PROFILE)
                with self.assertRaises(GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=RAW_SHA256,
                        bitwise_scalar_int_ops_profile=PROFILE)
                with self.assertRaises(TypedEmissionError):
                    render_typed_cpp(
                        candidate, KEY, RAW_SHA256,
                        bitwise_scalar_int_ops_profile=PROFILE)

    def test_emitter_uses_only_exact_javascript_boundaries(self):
        transformed = apply_bitwise_scalar_int_ops(
            _analyzed(), RAW_SHA256, PROFILE)
        emitted = render_typed_cpp(
            transformed, KEY, RAW_SHA256,
            bitwise_scalar_int_ops_profile=PROFILE)
        self.assertEqual(4, emitted.count("glsl::detail::js_to_int32("))
        self.assertEqual(4, emitted.count("glsl::detail::js_bitwise_xor("))
        self.assertEqual(3, emitted.count("glsl::detail::js_bitwise_and("))
        self.assertEqual(1, emitted.count("glsl::detail::js_bitwise_or("))
        self.assertEqual(2, emitted.count("glsl::detail::js_bitwise_not("))
        for expected in ("static_cast<double>(r)", "static_cast<double>(m)",
                         "static_cast<double>(state.mask)"):
            self.assertIn(expected, emitted)
        self.assertIn("[[maybe_unused]] double a", emitted)
        self.assertIn("[[maybe_unused]] double b", emitted)
        self.assertIn("[[maybe_unused]] std::int32_t op", emitted)
        self.assertIn("[[maybe_unused]] std::int32_t m", emitted)
        self.assertIn("double r = std::int32_t(0);", emitted)
        self.assertIn("double x =", emitted)
        self.assertIn("double y =", emitted)
        self.assertIn(
            "float(glsl::detail::js_to_int32((-state.speed)))", emitted)
        self.assertIn(
            "float((static_cast<double>(state.mask) + "
            "static_cast<double>(std::int32_t(1))))", emitted)
        self.assertNotIn("state.seed * std::int32_t(3)", emitted)

    def test_current_and_task35_absent_generation_are_exact_and_isolated(self):
        live_outputs = generate_typed_slice.generate_outputs(REPOSITORY)
        committed = (REPOSITORY / "src/typed_generated/typed_slice.cpp").read_text()
        self.assertEqual(
            committed,
            live_outputs["src/typed_generated/typed_slice.cpp"].decode())

        # Preserve the exact Task 35/Grain-175 historical boundary even after
        # Gabor, Scanline Error, and Glyph Map land as later additive programs.
        # cellRefract joins the exclusion set so the frozen 175/174 boundary
        # stays exactly as-is.
        historical = copy.deepcopy(generate_typed_slice.load_slice(REPOSITORY))
        historical["programs"] = [
            item for item in historical["programs"]
            if item["program_key"] not in {
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
                "classicNoisedeck/fractal:fractal",
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
                "filter/historicPalette:historicPalette", "filter/median:median",
                "filter/osd:osd", "filter/palette:palette",
                # Removal-set insertion 2026-08-25: `filter/dither:dither` and
                                # `synth/julia:julia` landed AFTER this milestone and were absent from
                                # the projection, so it was measuring a slice two rows too large.
                                # Adding the landed keys is the correct repair -- the frozen counts
                                # below are unchanged, which is the proof this is the right one. The
                                # set now equals the next milestone's exclusions plus its own row.
                                # See task-7-typed-generator-census-repair.md.
                "filter/dither:dither",
                "synth/julia:julia",
                "filter/spookyTicker:spookyTicker", "filter/texture:texture"}]
        self.assertEqual(176, len(historical["programs"]))
        self.assertNotIn(
            "classicNoisedeck/shapeMixer:shapeMixer",
            {item["program_key"] for item in historical["programs"]})
        with historical_cross_lane(historical):
            with mock.patch.object(generate_typed_slice, "load_slice",
                                   return_value=historical):
                outputs = generate_typed_slice.generate_outputs(REPOSITORY)
        generated = outputs["src/typed_generated/typed_slice.cpp"].decode()

        def blocks(source):
            markers = list(re.finditer(r"(?m)^// Typed IR program: (.+)$", source))
            return {
                match.group(1): source[match.start():
                                       markers[index + 1].start()
                                       if index + 1 < len(markers) else len(source)]
                for index, match in enumerate(markers)
            }

        current = blocks(generated)
        self.assertEqual(
            "54be6f2f09324a7cd1d41078112651d82153a2eb762937d371fdc1fce1f26710",
            hashlib.sha256(current[KEY].encode()).hexdigest())
        # Re-frozen 2026-08-25 because the DSL/Task-7 emitter now writes
        # FactoryRoute/define metadata into the emitted artifacts. The projection
        # above is corrected first (the frozen COUNTS match again), so this
        # measures the same milestone under the new emitter. Derived from a
        # measured regeneration of this test's own projection; see
        # task-7-typed-generator-census-repair.md.
        self.assertEqual(
            "98f8cd34c330efdb71c6a9ed552b3418ced2adaca5224b4415f63d75ecfd1f2d",
            hashlib.sha256("".join(
                block for key, block in current.items() if key != KEY
            ).encode()).hexdigest())

        with historical_cross_lane(historical):
            without_task35_spec = copy.deepcopy(historical)
            without_task35_spec["programs"] = [
                item for item in without_task35_spec["programs"]
                if item["program_key"] != KEY]
            self.assertEqual(175, len(without_task35_spec["programs"]))
            self.assertNotIn(
                KEY,
                {item["program_key"] for item in without_task35_spec["programs"]})
            with mock.patch.object(generate_typed_slice, "load_slice",
                                   return_value=without_task35_spec):
                without_task35 = generate_typed_slice.generate_outputs(REPOSITORY)
        self.assertNotIn(
            "// Typed IR program: synth/bitwise:bitwise",
            without_task35["src/typed_generated/typed_slice.cpp"].decode())
        # Re-frozen 2026-08-25 because the DSL/Task-7 emitter now writes
        # FactoryRoute/define metadata into the emitted artifacts. The projection
        # above is corrected first (its frozen COUNTS match again), so this still
        # measures the same milestone. Derived from a measured regeneration of
        # this test's own projection; see
        # task-7-typed-generator-census-repair.md.
        self.assertEqual(
            "815611bf2ee69cfddd455a988172f211b5a13daea0593390ca049f8ecdf21777",
            hashlib.sha256(without_task35[
                "src/typed_generated/typed_slice.cpp"]).hexdigest())
        self.assertEqual(
            "570fb941955de6e5a5214c36b2a86055e13ef6120d8ef88a489ece0c5050459f",
            hashlib.sha256(without_task35[
                "src/typed_generated/typed_manifest.json"]).hexdigest())


if __name__ == "__main__":
    unittest.main()
