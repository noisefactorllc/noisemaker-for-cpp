"""Exact runtime define admission for Emboss and Extrude."""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
import unittest
from unittest import mock

from tools.glslcpp import check_corpus
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import emboss_color_style_profile as emboss
from tools.glslcpp.frontend import extrude_bvec2_relational_reduction_profile as extrude


CORPUS = (Path(check_corpus.__file__).resolve().parents[2] / "tools/glslcpp/corpus"
          / check_corpus.REVISION / "sources")
CASES = (
    (emboss, emboss.EMBOSS_KEY, CORPUS / "filter/emboss/emboss.glsl",
     {"STYLE": 0}, {"STYLE": "int"}, emboss.authenticate_emboss_color_style),
    (extrude, extrude.EXTRUDE_KEY, CORPUS / "filter/extrude/extrude.glsl",
     {"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0},
     {"DEPTH_SOURCE": "int", "EXTRUDE_TYPE": "int"},
     extrude.authenticate_extrude_bvec2_relational_reduction),
)


class DynamicEmbossExtrudeProfiles(unittest.TestCase):
    def test_default_and_runtime_records_return_candidate_owned_nodes(self):
        for module, key, source, default, dynamic, authenticate in CASES:
            raw = source.read_text(encoding="utf-8")
            source_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            for label, defines in (("default", default), ("runtime", dynamic)):
                with self.subTest(key=key, mode=label):
                    parsed = parse_program(raw, key, defines)
                    parsed["raw_source"] = raw
                    candidate = analyze_program(parsed, key)
                    proof = authenticate(candidate, source_hash, module.PROFILE)
                    self.assertTrue(proof.consumed_objects)
                    self.assertEqual(len({id(obj) for obj in proof.consumed_objects}),
                                     len(proof.consumed_objects))
                    if module is emboss:
                        self.assertTrue(all(table._candidate is candidate
                                            for table in proof.tables))
                        self.assertTrue(all(table.owner in candidate.functions
                                            for table in proof.tables))
                        self.assertEqual(len(proof.tables), 4)
                        self.assertEqual(len(proof.equalities), 2)
                    else:
                        self.assertTrue(any(proof.main is item
                                            for item in candidate.functions))
                        self.assertEqual(len(proof.reductions), 2)
                        self.assertEqual(len(proof.relationals), 2)

    def test_forged_runtime_source_tree_and_carriers_reject(self):
        for module, key, source, _, defines, authenticate in CASES:
            raw = source.read_text(encoding="utf-8")
            source_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            parsed = parse_program(raw, key, defines)
            parsed["raw_source"] = raw
            candidate = analyze_program(parsed, key)
            mutations = (
                ("key", dataclasses.replace(candidate, key="forged:key"),
                 source_hash, module.PROFILE),
                ("raw", dataclasses.replace(candidate, raw_source=raw + "\n"),
                 source_hash, module.PROFILE),
                ("typed source", dataclasses.replace(candidate,
                     source=candidate.source + "\n"), source_hash, module.PROFILE),
                ("tree", dataclasses.replace(candidate,
                     functions=candidate.functions[:-1]), source_hash, module.PROFILE),
                ("caller hash", candidate, "0" * 64, module.PROFILE),
                ("profile", candidate, source_hash, None),
            )
            with self.subTest(key=key, mutation="internal record"):
                with mock.patch.object(module, "_DYNAMIC_IDENTITY", ()):
                    with self.assertRaises(ValueError):
                        authenticate(candidate, source_hash, module.PROFILE)
            for label, variant, variant_hash, profile in mutations:
                with self.subTest(key=key, mutation=label):
                    with self.assertRaises(ValueError):
                        authenticate(variant, variant_hash, profile)


if __name__ == "__main__":
    unittest.main()
