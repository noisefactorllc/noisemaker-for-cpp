import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import out_inout_admission_profile as out_profile
from tools.glslcpp.frontend import struct_declaration_profile as struct_profile


KEY = "synth/newton:newton"


class NewtonGeneratorLandingTests(unittest.TestCase):
    def test_newton_is_landed_as_an_exact_mutual_companion_row(self):
        self.assertEqual(("synth/julia:julia", KEY), struct_profile.KEYS)
        self.assertEqual(
            ("synth/julia:julia", "synth/mandelbrot:mandelbrot", KEY),
            out_profile.KEYS[1:])
        self.assertEqual("struct-declaration-newton-v1",
                         struct_profile.PROFILES[KEY])
        self.assertEqual("out-inout-admission-newton-v1",
                         out_profile.PROFILES[KEY])

        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        row = next(item for item in spec["programs"]
                   if item["program_key"] == KEY)
        self.assertEqual(
            {"defines": {}, "program_key": KEY,
             "struct_declaration_profile": "struct-declaration-newton-v1",
             "out_inout_admission_profile": "out-inout-admission-newton-v1"},
            row)
        self.assertEqual(211, len(spec["programs"]))
        self.assertEqual(199, spec["programs"].index(row))


if __name__ == "__main__":
    unittest.main()
