"""Exact Landscape volume-atlas and typed lowering regression tests."""

import dataclasses
import hashlib
import json
from pathlib import Path
import unittest

from tools.glslcpp import corpus_ratchet
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.landscape_volume_profile import (
    KEY, RAW_SHA256, authenticate, axis_indexes, borrowed_samplers,
    perspective_call, relational_nodes, tangent_node)
from tools.glslcpp.frontend.runtime_loop_bound_profile import apply_runtime_loop_bound
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.struct_frontier_profile import (
    LANDSCAPE_PROFILE, authenticate_struct_frontier)


CORPUS = (Path(__file__).resolve().parents[1]
          / "tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d")


def source_and_effect():
    pending = json.loads((CORPUS / "pending.json").read_text())
    row = next((item for item in pending["pending"] if item["program_key"] == KEY), None)
    if row is not None:
        effect = pending["effects"]["render/renderLandscape3d"]
    else:
        manifest = json.loads((CORPUS / "manifest.json").read_text())
        row = next(item for item in manifest["programs"] if item["program_key"] == KEY)
        effect = json.loads((CORPUS / "metadata.json").read_text())["effects"]["render/renderLandscape3d"]
    return (CORPUS / row["source"]).read_bytes(), effect


def typed_program(raw):
    typed = analyze_program(parse_program(
        raw.decode(), KEY, {"FILTERING": "int", "VIEW_MODE": "int"}), KEY)
    return apply_runtime_loop_bound(typed, RAW_SHA256, "runtime-loop-bound-v1")


class LandscapeVolumeProfileTests(unittest.TestCase):
    def test_exact_landscape_probe_and_proof_census(self):
        raw, effect = source_and_effect()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), RAW_SHA256)
        typed = typed_program(raw)
        contract = authenticate(typed, RAW_SHA256)
        self.assertEqual((contract.seed.maximum, contract.uniform_maximum), (256, 256))
        self.assertEqual((typed.counted_loop_proof.loop_count,
                          typed.counted_loop_proof.unproved_loop_count,
                          typed.counted_loop_proof.entrypoint_charge), (6, 0, 9990))
        structs = authenticate_struct_frontier(typed, RAW_SHA256, LANDSCAPE_PROFILE)
        self.assertEqual((len(structs.structs), len(structs.locals),
                          len(structs.members), len(structs.constructors)), (2, 4, 12, 5))
        relations = relational_nodes(typed, RAW_SHA256)
        self.assertEqual((len(relations.reductions), len(relations.relationals),
                          len(relations.declarations), len(relations.swizzles)), (3, 5, 2, 4))
        self.assertEqual((len(axis_indexes(typed, RAW_SHA256)),
                          len(borrowed_samplers(typed, RAW_SHA256).parameters),
                          len(borrowed_samplers(typed, RAW_SHA256).uses)), (19, 3, 10))
        self.assertEqual(tangent_node(typed, RAW_SHA256).callee, "tan")
        self.assertEqual(perspective_call(typed, RAW_SHA256).callee, "renderPerspective")
        self.assertIsNone(corpus_ratchet.probe_program(KEY, raw, effect))

    def test_source_tree_variant_and_metadata_mutations_fail_closed(self):
        raw, effect = source_and_effect()
        typed = typed_program(raw)
        for candidate, source_hash in (
            (typed, "0" * 64),
            (dataclasses.replace(typed, key="foreign:landscape"), RAW_SHA256),
            (dataclasses.replace(typed, functions=()), RAW_SHA256),
            (dataclasses.replace(typed, raw_source=typed.raw_source + "\n"), RAW_SHA256),
        ):
            with self.subTest(candidate=candidate.key, source_hash=source_hash):
                with self.assertRaises(ValueError):
                    authenticate(candidate, source_hash)
        altered = json.loads(json.dumps(effect))
        altered["params"]["volumeSize"]["default"] = 512
        result = corpus_ratchet.probe_program(KEY, raw, altered)
        self.assertIsNotNone(result)
        self.assertEqual(result["stage"], "corpus.parameter_uniform")
        mutated = raw.replace(b"volumeSize * 4", b"volumeSize * 5")
        self.assertNotEqual(mutated, raw)
        changed = analyze_program(parse_program(
            mutated.decode(), KEY, {"FILTERING": "int", "VIEW_MODE": "int"}), KEY)
        with self.assertRaises(ValueError):
            authenticate(changed, hashlib.sha256(mutated).hexdigest())


if __name__ == "__main__":
    unittest.main()
