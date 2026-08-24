from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = os.environ.get("NOISEMAKER_CPU_ROOT")
LIVE = os.environ.get("NOISEMAKER_FOR_CPU")
SHAPE = ROOT / "docs/port-engineering/shape-mixer-parity/shape_mixer_parity_oracle_generator.mjs"
SPOOKY = ROOT / "docs/port-engineering/spooky-ticker-parity/spooky_ticker_oracle_generator.mjs"


class PublicationRootShapeSpookyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUTHORITY or not LIVE:
            raise unittest.SkipTest("NOISEMAKER_CPU_ROOT and NOISEMAKER_FOR_CPU are required")
        cls.authority = Path(AUTHORITY)
        cls.live = Path(LIVE)
        if not cls.authority.is_dir() or not cls.live.is_dir():
            raise unittest.SkipTest("configured publication roots are unavailable")

    def run_generator(self, generator: Path, mode: str, *, live: str | None = LIVE,
                      extra: tuple[str, ...] = ()):
        env = os.environ.copy()
        if live is None:
            env.pop("NOISEMAKER_FOR_CPU", None)
        else:
            env["NOISEMAKER_FOR_CPU"] = live
        return subprocess.run(
            ["node", str(generator), mode, "--cpu-root", str(self.authority), *extra],
            cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def test_shape_mixer_requires_strict_external_authority_and_live_roots(self):
        self.assertEqual(0, self.run_generator(SHAPE, "--check").returncode)
        for live in (None, str(self.authority), str(self.authority / "missing-live")):
            with self.subTest(live=live):
                self.assertNotEqual(0, self.run_generator(SHAPE, "--check", live=live).returncode)
        with tempfile.TemporaryDirectory(prefix="shape-mixer-roots-") as raw:
            link = Path(raw) / "live-link"
            link.symlink_to(self.live, target_is_directory=True)
            self.assertNotEqual(0, self.run_generator(SHAPE, "--check", live=str(link)).returncode)

    def test_shape_mixer_rejects_unknown_and_duplicate_options(self):
        self.assertNotEqual(0, self.run_generator(SHAPE, "--check", extra=("--check",)).returncode)
        self.assertNotEqual(0, self.run_generator(SHAPE, "--check", extra=("--unknown",)).returncode)

    def test_spooky_ticker_requires_strict_external_authority_and_live_roots(self):
        self.assertEqual(0, self.run_generator(SPOOKY, "--check").returncode)
        self.assertEqual(0, self.run_generator(SPOOKY, "--self-test").returncode)
        for live in (None, str(self.authority), str(self.authority / "missing-live")):
            with self.subTest(live=live):
                self.assertNotEqual(0, self.run_generator(SPOOKY, "--check", live=live).returncode)
        with tempfile.TemporaryDirectory(prefix="spooky-ticker-roots-") as raw:
            link = Path(raw) / "live-link"
            link.symlink_to(self.live, target_is_directory=True)
            self.assertNotEqual(0, self.run_generator(SPOOKY, "--check", live=str(link)).returncode)

    def test_spooky_ticker_rejects_unknown_and_duplicate_options(self):
        self.assertNotEqual(0, self.run_generator(SPOOKY, "--check", extra=("--check",)).returncode)
        self.assertNotEqual(0, self.run_generator(SPOOKY, "--check", extra=("--unknown",)).returncode)


if __name__ == "__main__":
    unittest.main()
