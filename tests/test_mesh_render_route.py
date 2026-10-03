"""Authenticated admission of the mesh whole-pass adapter."""

import json
import copy
import pathlib
import unittest

from tools.glslcpp import check_corpus, corpus_ratchet
from tools.dsl import mesh_render_contract

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "render/meshRender:render"


class MeshRenderRouteTests(unittest.TestCase):
    def test_exact_mesh_source_uses_whole_pass_admission(self):
        root = check_corpus._corpus_root(ROOT)
        source = root / "sources/render/meshRender/render.frag"
        if not source.exists():
            source = root / "pending-sources/render/meshRender/render.frag"
        effect = json.loads((root / "metadata.json").read_text())["effects"]["render/meshRender"]
        self.assertIsNone(corpus_ratchet.probe_program(KEY, source.read_bytes(), effect))

    def test_source_and_effect_forgery_stay_closed(self):
        root = check_corpus._corpus_root(ROOT)
        source = root / "sources/render/meshRender/render.frag"
        effect = json.loads((root / "metadata.json").read_text())["effects"]["render/meshRender"]
        changed = corpus_ratchet.probe_program(KEY, source.read_bytes() + b"\n", effect)
        self.assertEqual(changed["stage"], "whole_pass.source")
        effect["passes"][1]["count"] = "resolution"
        changed = corpus_ratchet.probe_program(KEY, source.read_bytes(), effect)
        self.assertEqual(changed["stage"], "whole_pass.source")

    def test_route_and_ordered_abi_forgery_stay_closed(self):
        row = mesh_render_contract.compatibility_row(ROOT)
        mutations = [
            lambda value: value["factory"]["route"].__setitem__("kind", "typed_emitter"),
            lambda value: value["whole_pass_contract"].__setitem__("cpu_adapter_sha256", "0" * 64),
            lambda value: value["whole_pass_contract"].__setitem__("vertex_sha256", "0" * 64),
            lambda value: value["whole_pass_contract"].__setitem__("definition_sha256", "0" * 64),
            lambda value: value["uniforms"].reverse(),
            lambda value: value["uniforms"][0].__setitem__("cpp_type", "glsl::Vec3"),
            lambda value: value["samplers"][1].__setitem__("resource", "global_mesh0_positions"),
            lambda value: value["output_abi"]["extent"].__setitem__("format", "rgba32f"),
        ]
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                forged = copy.deepcopy(row)
                mutation(forged)
                self.assertNotEqual(forged, row)
                with self.assertRaisesRegex(ValueError, "whole-pass.*drift"):
                    mesh_render_contract.validate_row(forged, ROOT)

    def test_generated_descriptor_is_exact_and_has_no_fragment_binder(self):
        expected = mesh_render_contract.render_header(ROOT)
        self.assertEqual((ROOT / mesh_render_contract.HEADER).read_bytes(), expected)
        self.assertIn(b'"whole_pass"', expected)
        self.assertIn(b", nullptr};", expected)
        from tools.glslcpp import generate_typed_slice
        from tests import corpus_census
        self.assertNotIn(KEY, generate_typed_slice.typed_corpus_keys())
        self.assertNotIn(KEY, corpus_census.typed_keys())


if __name__ == "__main__":
    unittest.main()
