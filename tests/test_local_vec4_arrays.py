"""Exact-source admission for initialized local history and smoothing arrays."""

import dataclasses
import hashlib
import json
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import corpus_ratchet
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / f"tools/glslcpp/corpus/{CORPUS_REVISION}"
KEYS = ("filter/temporalAberration:temporalAberration", "synth/navierStokes:nsSmooth")


def source_and_effect(key):
    for filename, rows in (("pending.json", "pending"), ("manifest.json", "programs")):
        data = json.loads((CORPUS / filename).read_text())
        row = next((item for item in data[rows] if item["program_key"] == key), None)
        if row is not None:
            effects = json.loads((CORPUS / "metadata.json").read_text())["effects"]
            if filename == "pending.json":
                effects = {**effects, **data["effects"]}
            return (CORPUS / row["source"]).read_bytes(), effects[key.split(":")[0]]
    raise AssertionError(f"Missing source: {key}")


class LocalVec4ArrayTests(unittest.TestCase):
    def test_full_pipeline_accepts_both_exact_sources(self):
        for key in KEYS:
            with self.subTest(key=key):
                raw, effect = source_and_effect(key)
                self.assertIsNone(corpus_ratchet.probe_program(key, raw, effect))

    def test_source_tree_and_compile_configuration_are_bound(self):
        from tools.glslcpp.frontend.local_vec4_array_profile import authenticate_local_vec4_arrays
        for key in KEYS:
            raw, _ = source_and_effect(key)
            typed = analyze_program(parse_program(raw.decode(), key, {}), key)
            digest = hashlib.sha256(raw).hexdigest()
            proof = authenticate_local_vec4_arrays(typed, digest)
            self.assertEqual(len(proof.declarations), 1 if key == KEYS[0] else 4)
            self.assertIsNone(authenticate_local_vec4_arrays(dataclasses.replace(typed, key="foreign:array"), digest))
            for candidate, source_hash in (
                (typed, "0" * 64),
                (dataclasses.replace(typed, raw_source=typed.raw_source + "\n"), digest),
                (dataclasses.replace(typed, functions=()), digest),
                (dataclasses.replace(typed, declarations=()), digest),
                (dataclasses.replace(typed, preprocessor_defines=(("UNAUTHORIZED", 1),)), digest),
            ):
                with self.subTest(key=key, candidate=candidate.key, source_hash=source_hash):
                    with self.assertRaisesRegex(ValueError, "local vec4 array"):
                        authenticate_local_vec4_arrays(candidate, source_hash)
