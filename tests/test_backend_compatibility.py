from __future__ import annotations

import hashlib
import copy
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

from tools.dsl import generate_backend_compatibility as generator


ROOT = pathlib.Path(__file__).resolve().parents[1]
CPU_ROOT = pathlib.Path("/private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu")
SHADER_GIT = pathlib.Path("/Users/aayars/platform/noisemaker")
MANIFEST = ROOT / "src/effects/generated/backend_compatibility.json"


class BackendCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = generator.generate(cpu_root=CPU_ROOT, shader_git=SHADER_GIT)

    def test_authority_and_backend_census_are_authenticated(self) -> None:
        document = self.document
        self.assertEqual(213, document["counts"]["fragment_rows"])
        self.assertEqual(211, document["counts"]["unique_fragment_keys"])
        self.assertEqual(
            ["filter/invert:inv", "synth/solid:solid"],
            document["counts"]["duplicate_fragment_keys"],
        )
        self.assertEqual("filter/wormhole:deposit", document["scatter"]["program_key"])
        self.assertEqual("117a236679d1db3ab8f0e278230ece277b57564c", document["authority"]["upstream_revision"])
        self.assertEqual("a7a997dfdc807697adba008729dcdfdfcfbaf53c", document["authority"]["upstream_tree"])
        self.assertEqual("66f4e9337810ca839dddaba047dadc0c15e903e0f662f189ee6d08ff84fb62c4", document["authority"]["source_lock_sha256"])
        self.assertEqual(205, document["counts"]["raw_exact"])
        self.assertEqual(6, document["counts"]["semantic_exact"])
        self.assertEqual(["filter/text:text"], document["counts"]["incompatible_keys"])

    def test_manifest_is_deterministic_and_checkable(self) -> None:
        expected = json.dumps(self.document, indent=2, sort_keys=True).encode() + b"\n"
        self.assertEqual(expected, MANIFEST.read_bytes())
        generator.check(cpu_root=CPU_ROOT, shader_git=SHADER_GIT, repository=ROOT)
        first = hashlib.sha256(expected).hexdigest()
        second = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
        self.assertEqual(first, second)

    def test_cli_requires_both_authority_paths(self) -> None:
        result = subprocess.run(
            ["python3", "-B", "tools/dsl/generate_backend_compatibility.py", "--check"],
            cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True, capture_output=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("--cpu-root", result.stderr)
        self.assertIn("--shader-git", result.stderr)

    def _assert_fails_closed(self, mutate) -> None:
        forged = copy.deepcopy(self.document)
        mutate(forged)
        with self.assertRaises(generator.CompatibilityError):
            generator.validate_document(forged)

    def test_forged_duplicate_program_fails_closed(self) -> None:
        self._assert_fails_closed(
            lambda document: document["canonical_programs"].append(
                copy.deepcopy(document["canonical_programs"][0])))

    def test_missing_scatter_registration_fails_closed(self) -> None:
        self._assert_fails_closed(lambda document: document["scatter"].update(status="missing"))

    def test_unclassified_binding_fails_closed(self) -> None:
        def remove_source(document):
            document["canonical_programs"][0]["uniforms"][0]["source"] = None
        self._assert_fails_closed(remove_source)

    def test_output_mismatch_fails_closed(self) -> None:
        def change_cardinality(document):
            document["canonical_programs"][0]["output_abi"]["cardinality"] += 1
        self._assert_fails_closed(change_cardinality)

    def test_source_drift_fails_closed(self) -> None:
        self._assert_fails_closed(
            lambda document: document["canonical_programs"][0].update(new_raw_sha256="source-drift"))


if __name__ == "__main__":
    unittest.main()
