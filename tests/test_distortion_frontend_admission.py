from __future__ import annotations

import hashlib
import dataclasses
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.distortion_frontend_profile import (
    DERIVATIVE_SPANS, KEY, LOCAL_ARRAY_DECLARATIONS, PROFILE,
    SAMPLER_CALLS, authenticate_distortion_frontend,
)
from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (
    PROFILE as FOCUS_BLUR_PROFILE,
    FOCUS_BLUR_KEY,
    authenticate_focus_blur_borrowed_sampler_parameters,
)
from tools.glslcpp.frontend import fixed_nine_table_proof
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / (
    "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/"
    "sources/mixer/distortion/distortion.glsl"
)
FOCUS_BLUR_SOURCE = ROOT / (
    "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/"
    "sources/mixer/focusBlur/focusBlur.glsl"
)


def _replace_expression(value, target, replacement):
    if value is target:
        return replacement
    return dataclasses.replace(
        value,
        children=tuple(_replace_expression(child, target, replacement)
                       for child in value.children))


def _replace_statement(value, target, replacement):
    if value is target:
        return replacement
    return dataclasses.replace(
        value,
        expressions=tuple(_replace_expression(item, target, replacement)
                          for item in value.expressions),
        children=tuple(_replace_statement(child, target, replacement)
                       for child in value.children))


def _replace_program(program, target, replacement):
    functions = tuple(
        dataclasses.replace(
            function,
            body=tuple(_replace_statement(statement, target, replacement)
                       for statement in function.body))
        for function in program.functions)
    return dataclasses.replace(program, functions=functions)


def _walk_expression(value):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk(statement):
    for expression in statement.expressions:
        yield from _walk_expression(expression)
    for child in statement.children:
        yield from _walk(child)


class DistortionFrontendAdmissionTests(unittest.TestCase):
    @staticmethod
    def exact_program():
        raw = SOURCE.read_text(encoding="utf-8")
        return (raw, analyze_program(parse_program(raw, KEY, {}), KEY))

    def exact_proof(self):
        raw, program = self.exact_program()
        return raw, program, authenticate_distortion_frontend(
            program, hashlib.sha256(raw.encode()).hexdigest(), PROFILE)

    def test_proof_carries_all_lowering_ledgers(self) -> None:
        raw, program, proof = self.exact_proof()

        self.assertEqual(7, len(proof.sampler_parameter_nodes))
        self.assertEqual(8, len(proof.sampler_calls))
        self.assertEqual(14, len(proof.sampler_actual_nodes))
        self.assertEqual(6, len(proof.derivative_nodes))
        self.assertEqual(30, len(proof.indexed_nodes))
        self.assertEqual(3, len(proof.local_array_declarations))
        self.assertEqual(1, len(proof.array_loops))
        self.assertEqual((78, 79, 80), tuple(
            item.symbol_id for item in proof.local_array_declarations))
        self.assertEqual(LOCAL_ARRAY_DECLARATIONS, tuple(
            (item.symbol.name, item.type.display(),
             f"{item.span.start_line}:{item.span.start_column}-"
             f"{item.span.end_line}:{item.span.end_column}")
            for item in proof.local_array_declarations))
        self.assertEqual(27, len(proof.array_stores))
        self.assertEqual(3, len(proof.array_reads))
        self.assertEqual(30, len({id(item) for item in proof.indexed_nodes}))
        self.assertEqual(SAMPLER_CALLS, tuple(
            (function.name, call.callee,
             f"{call.span.start_line}:{call.span.start_column}-"
             f"{call.span.end_line}:{call.span.end_column}")
            for function in program.functions
            for statement in function.body
            for call in _walk(statement)
            if call.kind == "call"
            and any(child.type.display() == "sampler2D" for child in call.children)))
        self.assertEqual(DERIVATIVE_SPANS, tuple(
            (node.callee,
             f"{node.span.start_line}:{node.span.start_column}-"
             f"{node.span.end_line}:{node.span.end_column}")
            for node in proof.derivative_nodes))
        loop = proof.array_loops[0]
        self.assertEqual((0, 9, "<", "++", 9), (
            loop.loop_proof.start_value, loop.loop_proof.bound_value,
            loop.loop_proof.comparison, loop.loop_proof.update,
            loop.loop_proof.trip_count))
        self.assertEqual(32, proof.reflect_function_id)
        self.assertEqual(-36, proof.reflect_signature_id)
        self.assertEqual("143:26-143:51", proof.reflect_span)

    def test_sampler_caller_and_span_mutations_fail_closed(self) -> None:
        raw, program, proof = self.exact_proof()
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        for original, changed in (
                (proof.sampler_calls[0],
                 dataclasses.replace(proof.sampler_calls[0], callee="applyRefraction")),
                (proof.sampler_calls[0], dataclasses.replace(
                    proof.sampler_calls[0],
                    span=dataclasses.replace(proof.sampler_calls[0].span,
                                              start_column=20)))):
            with self.subTest(original=original, changed=changed):
                with self.assertRaisesRegex(ValueError, PROFILE):
                    authenticate_distortion_frontend(
                        _replace_program(program, original, changed),
                        source_hash, PROFILE)

    def test_array_ids_indexes_loop_reflect_and_derivatives_fail_closed(self) -> None:
        raw, program, proof = self.exact_proof()
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        declaration = proof.local_array_declarations[0]
        index = proof.indexed_nodes[0]
        loop = proof.array_loops[0]
        reflect = proof.reflect_node
        derivative = proof.derivative_nodes[0]
        mutations = (
            (declaration, dataclasses.replace(declaration, symbol_id=79)),
            (index, dataclasses.replace(
                index, children=(index.children[0], dataclasses.replace(
                    index.children[1], literal_value=8, literal="8")))),
            (loop, dataclasses.replace(
                loop, loop_proof=dataclasses.replace(loop.loop_proof,
                                                      bound_value=8))),
            (reflect, dataclasses.replace(reflect, signature_id=-35)),
            (derivative, dataclasses.replace(derivative, callee="dFdy")),
        )
        for original, changed in mutations:
            with self.subTest(kind=original.kind):
                with self.assertRaisesRegex(ValueError, PROFILE):
                    authenticate_distortion_frontend(
                        _replace_program(program, original, changed),
                        source_hash, PROFILE)

    def test_generator_derivative_ledger_rejects_truncation_and_duplicates(self) -> None:
        raw, program, proof = self.exact_proof()
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        forged_ledgers = (
            proof.derivative_nodes[:-1],
            (proof.derivative_nodes[0], proof.derivative_nodes[2],
             proof.derivative_nodes[1], *proof.derivative_nodes[3:]),
            (proof.derivative_nodes[0], proof.derivative_nodes[0],
             *proof.derivative_nodes[2:]),
        )
        for derivatives in forged_ledgers:
            with self.subTest(derivatives=derivatives):
                forged = proof._replace(derivative_nodes=derivatives)
                with patch.object(generate_typed_slice,
                                  "authenticate_distortion_frontend",
                                  return_value=forged):
                    with self.assertRaises(generate_typed_slice.GeneratorError):
                        generate_typed_slice.validate_capabilities(
                            program, generate_typed_slice.APPROVED_CAPABILITIES,
                            source_hash=source_hash,
                            distortion_frontend_profile=PROFILE)

    def test_fixed_nine_rejects_wrong_pinned_distortion_array_id(self) -> None:
        raw, program, proof = self.exact_proof()
        declaration = proof.local_array_declarations[0]
        mutated = _replace_program(
            program, declaration, dataclasses.replace(declaration, symbol_id=79))
        # Move the candidate locks to this deliberately mutated IR so the
        # assertion reaches the explicit Distortion-only symbol-ID pin rather
        # than stopping at the preceding whole-function locks.
        with patch.dict(
                fixed_nine_table_proof._TYPED_IR_LOCKS,
                {KEY: fixed_nine_table_proof._fingerprint(mutated.functions)}), \
             patch.dict(
                 fixed_nine_table_proof._WHOLE_PROGRAM_LOCKS,
                 {KEY: fixed_nine_table_proof._whole_program_fingerprint(mutated)}):
            self.assertIsNone(
                fixed_nine_table_proof.prove_fixed_nine_local_tables(mutated))

    def test_focus_blur_retains_exact_two_borrowed_sampler_sites(self) -> None:
        raw = FOCUS_BLUR_SOURCE.read_text(encoding="utf-8")
        program = analyze_program(parse_program(raw, FOCUS_BLUR_KEY, {}),
                                  FOCUS_BLUR_KEY)
        proof = authenticate_focus_blur_borrowed_sampler_parameters(
            program, hashlib.sha256(raw.encode()).hexdigest(), FOCUS_BLUR_PROFILE)
        self.assertEqual((57, 59), tuple(item.span.start_line for item in proof.calls))
        self.assertEqual((14, 14, 13, 13), tuple(
            item.symbol_id for item in proof.sampler_uses))
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            focus_blur_borrowed_sampler_profile=FOCUS_BLUR_PROFILE)
        emitted = render_typed_cpp(
            program, FOCUS_BLUR_KEY, source_hash,
            focus_blur_borrowed_sampler_profile=FOCUS_BLUR_PROFILE)
        self.assertEqual(2, emitted.count("const Surface& sceneTex"))
        self.assertEqual(2, emitted.count("const Surface& depthTex"))


if __name__ == "__main__":
    unittest.main()
