"""Current Feedback hue lane admission stays bound to its two exact sites."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import unittest

from tools.glslcpp import check_corpus, check_semantics, corpus_ratchet
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.feedback_hue_index_profile import (
    KEY, RAW_SHA256, authenticate_feedback_hue_indices)
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]


def _source_and_effect():
    corpus = check_corpus._corpus_root(ROOT)
    pending = json.loads((corpus / "pending.json").read_text(encoding="utf-8"))
    if any(item["program_key"] == KEY for item in pending["pending"]):
        row = next(item for item in pending["pending"]
                   if item["program_key"] == KEY)
        effect = pending["effects"].get(KEY.split(":", 1)[0])
    else:
        manifest = json.loads((corpus / "manifest.json").read_text(
            encoding="utf-8"))
        row = next(item for item in manifest["programs"]
                   if item["program_key"] == KEY)
        effect = None
    if effect is None:
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


class FeedbackHueIndexProfileTests(unittest.TestCase):
    def test_exact_hue_lane_and_complete_pipeline(self):
        sites = authenticate_feedback_hue_indices(_typed(), RAW_SHA256)
        self.assertEqual(len(sites), 2)
        self.assertEqual([site.children[1].literal_value for site in sites], [0, 0])
        raw, effect = _source_and_effect()
        self.assertIsNone(corpus_ratchet.probe_program(KEY, raw, effect))

    def test_mutations_fail_closed(self):
        typed = _typed()
        with self.assertRaisesRegex(ValueError, "exact source"):
            authenticate_feedback_hue_indices(typed, "0" * 64)
        with self.assertRaisesRegex(ValueError, "exact source"):
            authenticate_feedback_hue_indices(
                dataclasses.replace(typed, key="other:program"), RAW_SHA256)
        with self.assertRaisesRegex(ValueError, "whole-program"):
            authenticate_feedback_hue_indices(
                dataclasses.replace(typed, functions=typed.functions[:-1]), RAW_SHA256)


if __name__ == "__main__":
    unittest.main()
