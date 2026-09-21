"""Frozen adapter oracles must reject forgeries with recomputed sidecars."""

import copy
import hashlib
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from tools.glslcpp import generate_median_all_radii_native_oracle_include as median
from tools.glslcpp import generate_snow_native_oracle_include as snow


class AdapterOracleMaterializerTests(unittest.TestCase):
    def load_candidate(self, module, document):
        with tempfile.TemporaryDirectory() as directory:
            oracle = pathlib.Path(directory) / module.ORACLE.name
            payload = (json.dumps(document, indent=2) + "\n").encode()
            oracle.write_bytes(payload)
            oracle.with_name(oracle.name + ".sha256").write_text(
                hashlib.sha256(payload).hexdigest() + "  " + oracle.name + "\n")
            with patch.object(module, "ORACLE", oracle):
                return module._load_oracle()

    def test_committed_authority_keeps_identical_native_include(self):
        for module in (snow, median):
            with self.subTest(module=module.__name__):
                self.assertEqual(module.render(module._load_oracle()),
                                 module.TARGET.read_bytes())

    def test_matching_sidecar_cannot_replace_source_identity(self):
        for module in (snow, median):
            for field, value in (("sourceSha256", "0" * 64),
                                 ("sourceBytes", 0),
                                 ("sourceRelativePath", "unrelated.js")):
                with self.subTest(module=module.__name__, field=field):
                    document = json.loads(module.ORACLE.read_bytes())
                    document[field] = value
                    with self.assertRaisesRegex(SystemExit, "source identity"):
                        self.load_candidate(module, document)

    def test_matching_sidecar_cannot_remove_duplicate_or_replace_cases(self):
        for module in (snow, median):
            original = json.loads(module.ORACLE.read_bytes())
            for change in ("empty", "missing", "duplicate", "renamed", "reordered"):
                with self.subTest(module=module.__name__, change=change):
                    document = copy.deepcopy(original)
                    cases = document["cases"]
                    if change == "empty":
                        cases.clear()
                    elif change == "missing":
                        cases.pop()
                    elif change == "duplicate":
                        cases[-1] = copy.deepcopy(cases[0])
                    elif change == "renamed":
                        cases[0]["name"] = "unverified-case"
                    else:
                        cases.reverse()
                    with self.assertRaisesRegex(SystemExit, "case census"):
                        self.load_candidate(module, document)

    def test_exactness_flags_require_true_booleans(self):
        for module in (snow, median):
            for field in ("exactFloat32", "exactRgba8", "toleranceNone"):
                with self.subTest(module=module.__name__, field=field):
                    document = json.loads(module.ORACLE.read_bytes())
                    document[field] = "false"
                    with self.assertRaisesRegex(SystemExit, "zero-tolerance"):
                        self.load_candidate(module, document)

    def test_matching_sidecar_cannot_rebaseline_pixels_or_controls(self):
        for module in (snow, median):
            for change in ("pixel", "control"):
                with self.subTest(module=module.__name__, change=change):
                    document = json.loads(module.ORACLE.read_bytes())
                    case = document["cases"][0]
                    if change == "pixel":
                        case["outputRgba8"][0] ^= 1
                    else:
                        name = next(iter(case["controls"]))
                        case["controls"][name] += 1
                    with self.assertRaisesRegex(SystemExit, "frozen authority payload"):
                        self.load_candidate(module, document)


if __name__ == "__main__":
    unittest.main()
