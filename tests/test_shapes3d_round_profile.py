"""Exact Shapes3d round, lane-index, and struct emission witnesses."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import unittest

from tools.glslcpp import check_corpus, check_semantics, corpus_ratchet
from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.loop_proof import SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.shapes3d_round_profile import (
    KEY, RAW_SHA256, authenticate_shapes3d_linear_indices,
    authenticate_shapes3d_rounds)
from tools.glslcpp.frontend.struct_frontier_profile import PROFILES


ROOT = pathlib.Path(__file__).resolve().parents[1]


def _source_and_effect():
    corpus = check_corpus._corpus_root(ROOT)
    pending = json.loads((corpus / "pending.json").read_text(encoding="utf-8"))
    if any(item["program_key"] == KEY for item in pending["pending"]):
        row = next(item for item in pending["pending"]
                   if item["program_key"] == KEY)
        effect = pending["effects"][KEY.split(":", 1)[0]]
    else:
        manifest = json.loads((corpus / "manifest.json").read_text(
            encoding="utf-8"))
        row = next(item for item in manifest["programs"]
                   if item["program_key"] == KEY)
        metadata = json.loads((corpus / "metadata.json").read_text(
            encoding="utf-8"))
        effect = metadata["effects"][KEY.split(":", 1)[0]]
    raw = (corpus / row["source"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RAW_SHA256
    return raw, effect


def _typed():
    raw, effect = _source_and_effect()
    defaults = check_semantics._metadata_defaults(
        {"effects": {KEY.split(":", 1)[0]: effect}}, KEY)
    return analyze_program(
        parse_program(raw.decode("utf-8"), KEY, defaults), KEY,
        source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)


class Shapes3dRoundProfileTests(unittest.TestCase):
    def test_exact_nodes_and_complete_pipeline(self):
        typed = _typed()
        self.assertEqual(len(authenticate_shapes3d_rounds(typed, RAW_SHA256)), 2)
        self.assertEqual(len(authenticate_shapes3d_linear_indices(
            typed, RAW_SHA256)), 5)
        raw, effect = _source_and_effect()
        self.assertIsNone(corpus_ratchet.probe_program(KEY, raw, effect))

    def test_emitter_keeps_exact_structs_and_lane_lowering(self):
        output = render_typed_cpp(
            _typed(), KEY, RAW_SHA256, "typed_probe", "bind_shapes3d",
            source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
            struct_frontier_profile=PROFILES[KEY])
        self.assertIn("struct TransformData final", output)
        self.assertIn("struct ShapeParams final", output)
        self.assertIn("glsl::round(glsl::swizzle<0>", output)
        self.assertIn("[i]", output)

    def test_wrong_source_key_and_program_identity_fail_closed(self):
        typed = _typed()
        with self.assertRaisesRegex(ValueError, "exact source"):
            authenticate_shapes3d_rounds(typed, "0" * 64)
        with self.assertRaisesRegex(ValueError, "exact source"):
            authenticate_shapes3d_linear_indices(
                dataclasses.replace(typed, key="other:program"), RAW_SHA256)
        with self.assertRaisesRegex(ValueError, "whole-program"):
            authenticate_shapes3d_linear_indices(
                dataclasses.replace(typed, functions=typed.functions[:-1]),
                RAW_SHA256)


if __name__ == "__main__":
    unittest.main()
