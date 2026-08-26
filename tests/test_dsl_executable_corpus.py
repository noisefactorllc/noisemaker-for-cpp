"""Tests for the authenticated, canonical executable DSL corpus."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/dsl/generate_executable_corpus.mjs"
FIXTURE = ROOT / "tests/fixtures/dsl/executable-corpus.json"
ORACLE = ROOT / "tests/oracles/dsl_executable_corpus.sha256"


class ExecutableCorpusTest(unittest.TestCase):
    def node(self) -> str:
        value = shutil.which("node")
        if value is None:
            self.skipTest("node is required for executable corpus generation")
        return value

    def authority(self) -> pathlib.Path:
        # No default: the immutable CPU authority lives outside the repository
        # and its location is machine-specific, so it must arrive by env.
        path = pathlib.Path(os.environ.get("NOISEMAKER_CPU_ROOT", ""))
        if not path.is_absolute() or not path.is_dir():
            self.skipTest("NOISEMAKER_CPU_ROOT must identify the immutable CPU authority")
        return path

    def run_generator(self, output: pathlib.Path, authority: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.node(), str(GENERATOR), "--cpu-root", str(authority or self.authority()), "--output", str(output)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_checked_manifest_has_dynamic_counts_and_required_provenance(self) -> None:
        manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "noisemaker-cpp.dsl-executable-corpus.v1")
        self.assertEqual(manifest["manifestSha256"], ORACLE.read_text(encoding="utf-8").strip())
        records = manifest["records"]
        self.assertEqual(manifest["counts"]["admitted"], sum(r["recordKind"] == "admitted" for r in records))
        self.assertEqual(manifest["counts"]["excluded"], sum(r["recordKind"] == "excluded" for r in records))
        self.assertEqual(len({r["id"] for r in records}), len(records))
        self.assertGreater(manifest["counts"]["admitted"], 0)
        self.assertGreater(manifest["counts"]["excluded"], 0)
        self.assertTrue(any(r["effectId"] == "filter/blur" and r["recordKind"] == "admitted" for r in records))
        text = next(r for r in records if r["effectId"] == "filter/text")
        self.assertEqual(text["recordKind"], "excluded")
        self.assertEqual(text["firstFailure"]["code"], "source_incompatible")
        for record in records:
            self.assertEqual(record["sourceSha256"], hashlib.sha256(record["source"].encode()).hexdigest())
            self.assertEqual(record["options"]["width"], 17)
            self.assertEqual(record["options"]["height"], 11)
            self.assertIn("coverage", record)
            self.assertIn("provenance", record)
            if record["recordKind"] == "admitted":
                self.assertIn("plan", record)
            else:
                self.assertTrue(record["allReasons"])

    def test_generation_is_deterministic_and_does_not_rewrite_fixture(self) -> None:
        fixture_before = FIXTURE.read_bytes()
        oracle_before = ORACLE.read_bytes()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-corpus-", dir="/private/tmp") as directory:
            first = pathlib.Path(directory) / "first.json"
            second = pathlib.Path(directory) / "second.json"
            for output in (first, second):
                result = self.run_generator(output)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            generated = json.loads(first.read_text(encoding="utf-8"))
            checked = json.loads(FIXTURE.read_text(encoding="utf-8"))
            # Nothing is discarded before comparing: a pinned fixture the
            # generator cannot reproduce byte-for-byte is not a pin. Provenance
            # drift used to hide here.
            self.assertEqual(generated, checked)
            # And the recorded provenance has to describe this tree, not an
            # earlier one, so a typed-slice regeneration that forgets the
            # corpus is loud instead of silent.
            live_manifest = hashlib.sha256(
                (ROOT / "src/typed_generated/typed_manifest.json").read_bytes()).hexdigest()
            self.assertEqual(checked["provenance"]["typedManifestSha256"], live_manifest)
            for record in checked["records"]:
                self.assertEqual(record["provenance"]["typedManifestSha256"], live_manifest)
        self.assertEqual(FIXTURE.read_bytes(), fixture_before)
        self.assertEqual(ORACLE.read_bytes(), oracle_before)

    def test_generator_fails_closed_for_forged_authority_before_import(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-corpus-forge-", dir="/private/tmp") as directory:
            forged = pathlib.Path(directory) / "cpu"
            shutil.copytree(self.authority(), forged, symlinks=True)
            marker = forged / "imported-marker"
            renderer = forged / "src/runtime/renderer.js"
            renderer.write_text(f"import fs from 'node:fs'; fs.writeFileSync({json.dumps(str(marker))}, 'imported');\n")
            result = self.run_generator(pathlib.Path(directory) / "output.json", forged)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(marker.exists())
            self.assertTrue("behavioral" in result.stderr or "sha256" in result.stderr or "symlink" in result.stderr)


if __name__ == "__main__":
    unittest.main()
