"""Exact Texture MODE frontend admission and frozen default proof."""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
import unittest
from unittest import mock

from tools.glslcpp import check_corpus
from tools.glslcpp.frontend import dynamic_define_hoist, parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import texture_frontend_profile as profile

SOURCE = (Path(check_corpus.__file__).resolve().parents[2]
          / "tools/glslcpp/corpus" / check_corpus.REVISION
          / "sources/filter/texture/texture.glsl")


def candidate(raw: str, runtime: bool):
    source = (dynamic_define_hoist.transform_source(raw, profile.KEY)
              if runtime else raw)
    parsed = parse_program(source, profile.KEY,
                           {"MODE": "int" if runtime else 3})
    parsed["raw_source"] = raw
    return analyze_program(parsed, profile.KEY)


class TextureRuntimeModeProfileTests(unittest.TestCase):
    def test_frozen_default_and_runtime_candidate(self):
        raw = SOURCE.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        for runtime in (False, True):
            with self.subTest(runtime=runtime):
                program = candidate(raw, runtime)
                proof = profile.authenticate_texture_frontend(
                    program, source_hash, profile.PROFILE)
                self.assertEqual(profile.KEY, proof.program_key)
                self.assertEqual(5, len(proof.consumed_objects[1:6]))
                self.assertEqual(12 if runtime else 10, len(proof.bitwise_nodes))
                self.assertEqual(len(proof.consumed_objects),
                                 len({id(x) for x in proof.consumed_objects}))
                self.assertTrue(any(proof.inverse_sqrt is x
                                    for x in profile._expressions(program)))

    def test_runtime_forged_source_tree_and_profile_reject(self):
        raw = SOURCE.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        program = candidate(raw, True)
        mutations = (
            ("raw", dataclasses.replace(program, raw_source=raw + "\n"),
             source_hash, profile.PROFILE),
            ("normalized", dataclasses.replace(program,
             source=program.source + "\n"), source_hash, profile.PROFILE),
            ("tree", dataclasses.replace(program,
             functions=program.functions[:-1]), source_hash, profile.PROFILE),
            ("source hash", program, "0" * 64, profile.PROFILE),
            ("profile", program, source_hash, None),
            ("key", dataclasses.replace(program, key="forged:key"),
             source_hash, profile.PROFILE),
        )
        for label, altered, digest, name in mutations:
            with self.subTest(mutation=label):
                with self.assertRaises(ValueError):
                    profile.authenticate_texture_frontend(altered, digest, name)
        with mock.patch.object(profile, "_DYNAMIC_IDENTITY", ()):
            with self.assertRaises(ValueError):
                profile.authenticate_texture_frontend(
                    program, source_hash, profile.PROFILE)


if __name__ == "__main__":
    unittest.main()
