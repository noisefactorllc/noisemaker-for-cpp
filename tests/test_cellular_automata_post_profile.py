"""Exact integer post-increment admission for current Cellular Automata 3D."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import unittest

from tools.glslcpp import check_corpus, check_semantics, corpus_ratchet
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.cellular_automata_post_profile import (
    KEY, RAW_SHA256, authenticate_ca_posts)
from tools.glslcpp.frontend.semantic import analyze_program


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
    return analyze_program(parse_program(raw.decode("utf-8"), KEY, defaults), KEY)


class CellularAutomataPostProfileTests(unittest.TestCase):
    def test_age_source_preserves_cpu_seed_hash_rounding(self):
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp

        emitted = render_typed_cpp(_typed(), KEY, RAW_SHA256)
        self.assertIn('bindings.get<std::int32_t>("colorMode")', emitted)
        self.assertIn("packState(state, context, alive, age)", emitted)
        self.assertIn("packState(state, context, finalAlive, finalAge)", emitted)
        self.assertIn("const double cpuHashDot", emitted)
        self.assertIn("noisemaker::f32(cpuHashDot + cpuHashDot)", emitted)
        self.assertNotIn("float(state.seed)", emitted)

    def test_exact_sites_and_complete_pending_pipeline(self):
        posts = authenticate_ca_posts(_typed(), RAW_SHA256)
        self.assertEqual(len(posts), 10)
        self.assertEqual({item.operator for item in posts}, {"++"})
        raw, effect = _source_and_effect()
        self.assertIsNone(corpus_ratchet.probe_program(KEY, raw, effect))

    def test_wrong_source_and_ir_are_rejected(self):
        typed = _typed()
        with self.assertRaisesRegex(ValueError, "exact source"):
            authenticate_ca_posts(typed, "0" * 64)
        with self.assertRaisesRegex(ValueError, "exact source"):
            authenticate_ca_posts(dataclasses.replace(typed, key="other:program"),
                                  RAW_SHA256)
        with self.assertRaisesRegex(ValueError, "whole-program"):
            authenticate_ca_posts(
                dataclasses.replace(typed, functions=typed.functions[:-1]),
                RAW_SHA256)


if __name__ == "__main__":
    unittest.main()
