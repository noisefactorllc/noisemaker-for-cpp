"""Exact authority pass-define contract for depthKeys."""

import copy
import json
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import check_semantics, corpus_ratchet, generate_typed_slice
from tools.dsl import generate_backend_compatibility as backend


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / f"tools/glslcpp/corpus/{CORPUS_REVISION}"
KEY = "render/pointsBillboardRender:depthKeys"


def source_and_effect():
    pending = json.loads((CORPUS / "pending.json").read_text())
    row = next((item for item in pending["pending"] if item["program_key"] == KEY), None)
    if row is None:
        manifest = json.loads((CORPUS / "manifest.json").read_text())
        row = next(item for item in manifest["programs"] if item["program_key"] == KEY)
    effect = json.loads((CORPUS / "metadata.json").read_text())["effects"]["render/pointsBillboardRender"]
    return (CORPUS / row["source"]).read_bytes(), effect


class DepthKeysPassDefinesTests(unittest.TestCase):
    def test_exact_two_passes_are_admitted(self):
        raw, effect = source_and_effect()
        self.assertEqual(corpus_ratchet.depth_keys_pass_defines(effect), {"VIEW_MODE": 1})
        self.assertIsNone(corpus_ratchet.probe_program(KEY, raw, effect))
        self.assertEqual(check_semantics._program_defaults(
            {"effects": {"render/pointsBillboardRender": effect}}, KEY),
            {"VIEW_MODE": 1})
        self.assertEqual(generate_typed_slice._defaults(ROOT, KEY),
                         {"VIEW_MODE": 1})

    def test_changed_pass_define_is_rejected(self):
        raw, effect = source_and_effect()
        for mutation in ({"VIEW_MODE": 1}, {"VIEW_MODE": 3}, {"VIEW_MODE": 2, "OTHER": 1}, {}):
            wrong = copy.deepcopy(effect)
            matches = [item for item in wrong["passes"] if item["program"] == "depthKeys"]
            matches[1]["defines"] = mutation
            with self.subTest(mutation=mutation):
                result = corpus_ratchet.probe_program(KEY, raw, wrong)
                self.assertEqual(result["stage"], "corpus.pass_binding")
                with self.assertRaises(ValueError):
                    check_semantics._program_defaults(
                        {"effects": {"render/pointsBillboardRender": wrong}}, KEY)

    def test_backend_binding_and_authority_projection_are_key_scoped(self):
        _, effect = source_and_effect()
        passes = [item for item in effect["passes"] if item["program"] == "depthKeys"]
        self.assertEqual(backend._authority_pass(passes[0])["defines"], {"VIEW_MODE": 1})
        self.assertEqual(backend._authority_pass(passes[1])["defines"], {"VIEW_MODE": 2})
        typed = {"program_key": KEY, "typed_abi": {"uniforms": [
            {"name": "VIEW_MODE", "type": "int"}], "samplers": []}}
        _, uniforms, _ = backend._binding_abi(effect, passes[0], typed)
        self.assertEqual((uniforms[0]["source"], uniforms[0]["source_name"]),
                         ("pass_derived", "typed_pass_define"))
        typed["program_key"] = "foreign:program"
        resolved, uniforms, _ = backend._binding_abi(effect, passes[0], typed)
        self.assertEqual(resolved["unresolved"], [])
        self.assertEqual((uniforms[0]["source"], uniforms[0]["source_name"]),
                         ("pass_derived", "typed_compile_define"))
        typed["typed_abi"]["uniforms"][0]["name"] = "UNCLASSIFIED_VIEW_MODE"
        unresolved, _, _ = backend._binding_abi(effect, passes[0], typed)
        self.assertEqual(unresolved["unresolved"][0]["reason"], "unclassified binding")


if __name__ == "__main__":
    unittest.main()
