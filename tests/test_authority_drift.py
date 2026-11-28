"""Exercise the drift check against a CPU checkout with a known payload."""

import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.dsl import check_authority_drift


CORPUS = "f" * 40
DIGEST = "82d16680eeb8ebba6c99ef0b3a224158bd4ffd75cbe459a64187771b7ce9aeeb"


class AuthorityDriftTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.cpu_root = self.root / "cpu"
        for name, contents in {
            "package.json": '{"type":"module"}\n',
            "package-lock.json": '{"lockfileVersion":3}\n',
            "scripts/upstream/source-lock.js": f"export const PINNED_UPSTREAM_REVISION = '{CORPUS}'\n",
            "src/effects/catalog.js": "export const effectId = 'synth/solid'\n",
        }.items():
            file = self.cpu_root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(contents, encoding="utf-8")

        self.git("init", "--quiet", "--initial-branch=main")
        self.git("add", "--", ".")
        self.git("commit", "--quiet", "-m", "CPU authority fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()

        self.authority = self.root / "corpus_authority.mjs"
        self.authority.write_text(
            f"export const EXPECTED = {{ behavioralLockSha256: '{DIGEST}', upstreamRevision: '{CORPUS}' }}\n",
            encoding="utf-8",
        )

    def git(self, *args):
        return subprocess.check_output(
            [
                "git", "-c", "user.name=Test Fixture", "-c", "user.email=fixture@example.com",
                "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args,
            ],
            cwd=self.cpu_root,
            stderr=subprocess.STDOUT,
            text=True,
        )

    def check(self, *args):
        diagnostics = io.StringIO()
        with (
            patch.object(check_authority_drift, "AUTHORITY_MODULE", self.authority),
            contextlib.redirect_stdout(diagnostics),
            contextlib.redirect_stderr(diagnostics),
        ):
            try:
                status = check_authority_drift.main(["--cpu-root", str(self.cpu_root), *args])
            except SystemExit as error:
                if isinstance(error.code, str):
                    print(error.code, file=diagnostics)
                    status = 1
                else:
                    status = error.code
        return status, diagnostics.getvalue()

    def assert_rejected(self, diagnostic, *, revision=None, corpus=CORPUS):
        status, output = self.check("--pinned", revision or self.revision, corpus)
        self.assertEqual(status, 1, output)
        self.assertIn(diagnostic, output)

    def test_matching_checkout_and_payload_pass(self):
        status, output = self.check("--pinned", self.revision, CORPUS)
        self.assertEqual(status, 0, output)

    def test_matching_bytes_under_the_wrong_commit_are_rejected(self):
        self.assert_rejected("CPU revision", revision="1" * 40)

    def test_matching_commit_with_changed_payload_is_rejected(self):
        (self.cpu_root / "src/effects/catalog.js").write_text("export const effectId = 'synth/gradient'\n")
        self.assert_rejected("behavioralLockSha256")

    def test_expected_corpus_must_match_the_source_lock(self):
        self.assert_rejected("corpus revision", corpus="2" * 40)

    def test_missing_cpu_payload_is_rejected(self):
        (self.cpu_root / "package-lock.json").unlink()
        self.assert_rejected("missing CPU authority file")

    def test_archive_without_a_git_checkout_is_rejected_in_pinned_mode(self):
        (self.cpu_root / ".git").rename(self.root / "detached-git-metadata")
        self.assert_rejected("CPU checkout")

    def test_existing_live_comparison_accepts_an_archive(self):
        (self.cpu_root / ".git").rename(self.root / "detached-git-metadata")
        status, output = self.check()
        self.assertEqual(status, 0, output)
