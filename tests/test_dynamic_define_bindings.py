"""Runtime defines must retain a source in the graph binding ABI."""

import json
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.dsl import generate_backend_compatibility as generator

ROOT = Path(__file__).resolve().parents[1]


class DynamicDefineBindingTests(unittest.TestCase):
    def test_noise3d_number_seed_carrier_requires_exact_source_and_route(self):
        metadata = json.loads((ROOT / f"tools/glslcpp/corpus/{CORPUS_REVISION}/metadata.json").read_text())
        key = "synth3d/noise3d:precompute"
        effect = metadata["effects"]["synth3d/noise3d"]
        pass_item = next(item for item in effect["passes"] if item["program"] == "precompute")
        record = {"program_key": key,
                  "source_sha256": "60ce97d188bf78bc84176c063943f29c25371e4325f13cedbb4eec889c905727",
                  "typed_abi": {"uniforms": [{"name": "seed", "type": "int"}], "samplers": []}}
        result, uniforms, _ = generator._binding_abi(effect, pass_item, record)
        self.assertEqual(result["unresolved"], [])
        self.assertEqual(uniforms, [{"name": "seed", "type": "int", "cpp_type": "double",
                                    "source": "effect_parameter", "source_name": "seed"}])
        with self.assertRaises(generator.CompatibilityError):
            generator._binding_abi(effect, pass_item,
                                   {**record, "source_sha256": "0" * 64})
        self.assertEqual(generator._cpp_type("int", "seed", "effect_parameter",
                                             "synth3d/shape3d:precompute"), "std::int32_t")

    def test_new_runtime_defines_have_parameter_binding_sources(self):
        metadata = json.loads((ROOT / f"tools/glslcpp/corpus/{CORPUS_REVISION}/metadata.json").read_text())
        cases = {
            "classicNoisedeck/cellRefract:cellRefract": ["KERNEL", "SHAPE"],
            "classicNoisedeck/kaleido:kaleido": ["DIRECTION", "KERNEL", "LOOP_OFFSET", "METRIC"],
            "classicNoisedeck/effects:effects": ["EFFECT", "FLIP"],
            "classicNoisedeck/noise:noise": ['COLOR_MODE', 'LOOP_OFFSET', 'METRIC', 'NOISE_TYPE', 'REFRACT_MODE'],
            "classicNoisedeck/moodscape:moodscape": ["COLOR_MODE", "NOISE_TYPE"],
            "filter/emboss:emboss": ["STYLE"],
            "filter/extrude:extrude": ["DEPTH_SOURCE", "EXTRUDE_TYPE"],
            "filter/texture:texture": ["MODE"],
            "filter/lowPoly:lowPoly": ["LP_BORDER", "LP_LIGHT"],
            "filter/strokes:stkSmear": ["MODE"],
            "classicNoisedeck/caustic:caustic": ["NOISE_TYPE"],
            "synth/perlin:perlin": ["DIMENSIONS"],
            "synth/shape:shape": ["LOOP_A_OFFSET", "LOOP_B_OFFSET"],
            "classicNoisedeck/shapes:shapes": ["LOOP_A_OFFSET", "LOOP_B_OFFSET"],
            "filter/halftone:halftone": ["PATTERN"],
            "classicNoisedeck/shapes3d:shapes3d": ["BLEND_MODE", "SHAPE_A", "SHAPE_B"],
            "filter3d/flow3d:agent": ["BEHAVIOR"],
            "render/render3d:render3d": ["FILTERING", "INVERT"],
            "render/renderCubemap3d:renderCubemap3d": ["FILTERING", "INVERT"],
            "render/renderLandscape3d:landscape": ["FILTERING", "VIEW_MODE"],
            "synth3d/noise3d:precompute": ["COLOR_MODE"],
        }
        for key, names in cases.items():
            with self.subTest(key=key):
                effect = metadata["effects"][key.split(":")[0]]
                pass_item = next(p for p in effect["passes"] if p["program"] == key.split(":")[1])
                for name in names:
                    self.assertTrue(any(p.get("define") == name for p in effect["params"].values()))
                row = {"program_key": key, "typed_abi": {
                    "uniforms": [{"name": name, "type": "int"} for name in names],
                    "samplers": []}}
                result, uniforms, _ = generator._binding_abi(effect, pass_item, row)
                self.assertEqual(result["unresolved"], [])
                self.assertEqual([u["source"] for u in uniforms], ["pass_derived"] * len(names))
                self.assertEqual([u["source_name"] for u in uniforms], ["typed_compile_define"] * len(names))
