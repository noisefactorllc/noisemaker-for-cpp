from __future__ import annotations

import hashlib
import copy
import json
import os
import pathlib
import subprocess
import unittest

from tools.dsl import generate_backend_compatibility as generator


ROOT = pathlib.Path(__file__).resolve().parents[1]
CPU_ROOT = pathlib.Path(os.environ.get("NOISEMAKER_CPU_ROOT", ""))
SHADER_GIT = pathlib.Path(os.environ.get("NOISEMAKER_SHADER_GIT", ""))
MANIFEST = ROOT / "src/effects/generated/backend_compatibility.json"


class BackendCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not CPU_ROOT.is_dir() or not SHADER_GIT.is_dir():
            raise unittest.SkipTest("set NOISEMAKER_CPU_ROOT and NOISEMAKER_SHADER_GIT for authority tests")
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
        first = generator.generate(cpu_root=CPU_ROOT, shader_git=SHADER_GIT)
        second = generator.generate(cpu_root=CPU_ROOT, shader_git=SHADER_GIT)
        first_bytes = json.dumps(first, indent=2, sort_keys=True).encode() + b"\n"
        second_bytes = json.dumps(second, indent=2, sort_keys=True).encode() + b"\n"
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first_bytes, MANIFEST.read_bytes())
        generator.check(cpu_root=CPU_ROOT, shader_git=SHADER_GIT, repository=ROOT)
        first = hashlib.sha256(first_bytes).hexdigest()
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
            generator.validate_document(
                forged,
                expected_source_hashes={
                    row["program_key"]: row["new_raw_sha256"]
                    for row in self.document["canonical_programs"]
                } | {self.document["scatter"]["program_key"]: self.document["scatter"]["new_raw_sha256"]},
            )

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
            lambda document: document["canonical_programs"][0].update(new_raw_sha256="0" * 64))

    def test_draw_mode_and_dimensionality_fail_closed(self) -> None:
        self._assert_fails_closed(lambda document: document["canonical_programs"][0].update(draw_mode="points"))
        self._assert_fails_closed(lambda document: document["canonical_programs"][0].update(dimensionality="volume"))

    def test_unknown_status_reason_and_reference_key_fail_closed(self) -> None:
        self._assert_fails_closed(lambda document: document["canonical_programs"][0].update(status="maybe"))
        self._assert_fails_closed(lambda document: document["reference_passes"][0]["reasons"].append("not-structured"))
        self._assert_fails_closed(lambda document: document["reference_passes"][0].update(program_key="forged:key"))

    def test_output_names_routes_and_scatter_hash_fail_closed(self) -> None:
        self._assert_fails_closed(lambda document: document["canonical_programs"][0]["outputs"][0].update(physical_name="forged"))
        self._assert_fails_closed(lambda document: document["canonical_programs"][0]["outputs"][0].update(logical_route="forged"))
        self._assert_fails_closed(lambda document: document["scatter"].update(new_raw_sha256="forged"))

    def test_typed_manifest_requires_complete_authenticated_rows(self) -> None:
        corpus_root = generator.check_corpus._corpus_root(ROOT)
        entries = generator.check_corpus._validate_manifest(
            generator.check_corpus._load_json(corpus_root / "manifest.json", "manifest"))
        corpus_keys = {item["program_key"] for item in entries}
        typed_path = ROOT / "src/typed_generated/typed_manifest.json"
        typed = json.loads(typed_path.read_text(encoding="utf-8"))
        typed["programs"].pop()
        with self.assertRaises(generator.CompatibilityError):
            generator._typed_manifest(ROOT, typed, corpus_keys)
        typed = json.loads(typed_path.read_text(encoding="utf-8"))
        typed["programs"].append(copy.deepcopy(typed["programs"][0]))
        with self.assertRaises(generator.CompatibilityError):
            generator._typed_manifest(ROOT, typed, corpus_keys)

    def test_shader_repository_is_not_mutated(self) -> None:
        before = subprocess.run(["git", "-C", str(SHADER_GIT), "status", "--porcelain"],
                                check=True, text=True, capture_output=True).stdout
        generator._authority(CPU_ROOT, SHADER_GIT)
        after = subprocess.run(["git", "-C", str(SHADER_GIT), "status", "--porcelain"],
                               check=True, text=True, capture_output=True).stdout
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
