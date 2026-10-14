"""Exact-source out-parameter admission for Flythrough3D."""

import dataclasses
import hashlib
import json
from pathlib import Path
import unittest

from tools.glslcpp import corpus_ratchet
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.out_inout_admission_profile import (
    authenticate_out_inout_admission, authenticate_flythrough_value_copies)
from tools.glslcpp.frontend.fractal3d_log_profile import authenticate_fractal3d_log_admission
from tools.glslcpp.frontend.loop_proof import SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d"
KEY = "synth3d/flythrough3d:precompute"
PROFILE = "out-inout-admission-flythrough3d-v1"
LOG_PROFILE = "fractal3d-log-flythrough3d-v1"


def source_and_effect():
    pending = json.loads((CORPUS / "pending.json").read_text())
    row = next((item for item in pending["pending"] if item["program_key"] == KEY), None)
    if row is not None:
        effect = pending["effects"]["synth3d/flythrough3d"]
    else:
        manifest = json.loads((CORPUS / "manifest.json").read_text())
        row = next(item for item in manifest["programs"] if item["program_key"] == KEY)
        effect = json.loads((CORPUS / "metadata.json").read_text())["effects"]["synth3d/flythrough3d"]
    return (CORPUS / row["source"]).read_bytes(), effect


class FlythroughOutProfileTests(unittest.TestCase):
    def test_fractal_vector_locals_copy_their_parameters(self):
        raw, _ = source_and_effect()
        typed = analyze_program(parse_program(raw.decode(), KEY, {}), KEY,
                                source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        digest = hashlib.sha256(raw).hexdigest()
        copies = authenticate_flythrough_value_copies(typed, digest)
        self.assertEqual(tuple((item.symbol.name, item.span.start_line,
                                item.children[0].symbol.name) for item in copies),
                         (("z", 227, "pos"), ("z", 180, "pos")))
        with self.assertRaises(ValueError):
            authenticate_flythrough_value_copies(
                dataclasses.replace(typed, functions=()), digest)

    def test_exact_source_accepts_three_out_parameters_and_one_call(self):
        raw, effect = source_and_effect()
        typed = analyze_program(parse_program(raw.decode(), KEY, {}), KEY,
                                source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        parameters, calls = authenticate_out_inout_admission(
            typed, hashlib.sha256(raw).hexdigest(), PROFILE)
        self.assertEqual(tuple(parameter.name for parameter in parameters), ("pos", "dir", "up"))
        self.assertEqual(tuple(call.callee for call in calls), ("getCameraState",))
        self.assertIsNone(corpus_ratchet.probe_program(KEY, raw, effect))

    def test_source_tree_and_direction_cannot_change(self):
        raw, _ = source_and_effect()
        typed = analyze_program(parse_program(raw.decode(), KEY, {}), KEY,
                                source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        digest = hashlib.sha256(raw).hexdigest()
        owner_index = next(index for index, function in enumerate(typed.functions)
                           if function.name == "getCameraState")
        owner = typed.functions[owner_index]
        wrong_parameters = list(owner.parameters)
        wrong_parameters[2] = dataclasses.replace(wrong_parameters[2], direction="in")
        wrong_functions = list(typed.functions)
        wrong_functions[owner_index] = dataclasses.replace(
            owner, signature=dataclasses.replace(
                owner.signature, parameters=tuple(wrong_parameters)))
        main_index = next(index for index, function in enumerate(typed.functions)
                          if function.name == "main")
        main = typed.functions[main_index]
        wrong_body = list(main.body)
        call_statement = wrong_body[9]
        call = call_statement.expressions[0]
        wrong_call = dataclasses.replace(call, children=(call.children[0], call.children[2],
                                                         call.children[1], call.children[3]))
        wrong_body[9] = dataclasses.replace(call_statement, expressions=(wrong_call,))
        wrong_call_functions = list(typed.functions)
        wrong_call_functions[main_index] = dataclasses.replace(main, body=tuple(wrong_body))
        self.assertEqual(authenticate_out_inout_admission(
            dataclasses.replace(typed, key="foreign:flythrough"), digest, None), ())
        for candidate, source_hash in (
            (typed, "0" * 64),
            (dataclasses.replace(typed, raw_source=typed.raw_source + "\n"), digest),
            (dataclasses.replace(typed, functions=()), digest),
            (dataclasses.replace(typed, functions=tuple(wrong_functions)), digest),
            (dataclasses.replace(typed, functions=tuple(wrong_call_functions)), digest),
            (dataclasses.replace(typed, preprocessor_defines=(("UNAUTHORIZED", 1),)), digest),
        ):
            with self.subTest(source_hash=source_hash):
                with self.assertRaises(ValueError):
                    authenticate_out_inout_admission(candidate, source_hash, PROFILE)

    def test_one_exact_scalar_log_site_is_required(self):
        raw, _ = source_and_effect()
        typed = analyze_program(parse_program(raw.decode(), KEY, {}), KEY,
                                source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        digest = hashlib.sha256(raw).hexdigest()
        proof = authenticate_fractal3d_log_admission(typed, digest, LOG_PROFILE)
        self.assertEqual(tuple((site.owner_name, site.span) for site in proof.sites),
                         (("mandelbulb", "211:25-211:31"),))
        with self.assertRaises(ValueError):
            authenticate_fractal3d_log_admission(
                dataclasses.replace(typed, functions=()), digest, LOG_PROFILE)
