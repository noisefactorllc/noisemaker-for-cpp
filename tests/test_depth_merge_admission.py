"""Sampler precision and bounded merge-search loop regressions."""

import json
from pathlib import Path
import unittest

from tools.glslcpp import corpus_ratchet
from tools.glslcpp.frontend import FrontendError, parse_program
from tools.glslcpp.frontend.semantic import analyze_program


CORPUS = Path(__file__).resolve().parents[1] / "tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d"
KEY = "render/pointsBillboardRender:depthMerge"


def source_and_effect():
    metadata = json.loads((CORPUS / "metadata.json").read_text())["effects"]
    for filename, rows in (("pending.json", "pending"), ("manifest.json", "programs")):
        data = json.loads((CORPUS / filename).read_text())
        row = next((item for item in data[rows] if item["program_key"] == KEY), None)
        if row is not None:
            effects = {**metadata, **data.get("effects", {})}
            return (CORPUS / row["source"]).read_bytes(), effects[KEY.split(":")[0]]
    raise AssertionError("Missing depth merge source")


class DepthMergeAdmissionTests(unittest.TestCase):
    def test_current_depth_merge_pass_completes_the_existing_probe(self):
        raw, effect = source_and_effect()
        self.assertIsNone(corpus_ratchet.probe_program(KEY, raw, effect))

    def test_sampler_precision_keeps_invalid_type_and_qualifier_errors(self):
        parse_program("precision highp sampler2D; void main() {}", "test:precision", {})
        for declaration in ("precision highp vec4;", "precision unknown sampler2D;", "precision highp unknown;"):
            with self.subTest(declaration=declaration):
                with self.assertRaisesRegex(FrontendError, "invalid precision declaration"):
                    parse_program(declaration + " void main() {}", "test:precision", {})

    def test_short_circuit_guard_only_reduces_the_proved_bound(self):
        def program(condition):
            raw = """out vec4 fragColor;
uniform int unbounded;
bool sideEffect() { return true; }
void main() {
  int low = 0; int high = 9;
  for (int step = 0; CONDITION; step++) { low = low + 1; }
  fragColor = vec4(float(low));
}""".replace("CONDITION", condition)
            return analyze_program(parse_program(raw, "test:guard", {}), "test:guard")
        accepted = program("step < 22 && low < high")
        self.assertEqual(accepted.counted_loop_proof.loop_count, 1)
        self.assertEqual(accepted.counted_loop_proof.unproved_loop_count, 0)
        self.assertEqual(accepted.counted_loop_proof.max_lexical_product, 22)
        for condition in ("step < 22 || low < high", "step < unbounded && low < high",
                          "step < 22 && sideEffect()", "step < 22 && ++low < high",
                          "step < 22 && (step = 0) < high"):
            with self.subTest(condition=condition):
                self.assertEqual(program(condition).counted_loop_proof.unproved_loop_count, 1)
