from __future__ import annotations

from tests.historical_cpu import current_cpu_root, current_run, historical_cpu_root, historical_run
from tests.simulated_links import simulate_symlink

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_AUTHORITY = historical_cpu_root()
CURRENT_AUTHORITY = current_cpu_root()
LIVE = os.environ.get("NOISEMAKER_FOR_CPU")
SHAPE = ROOT / "docs/port-engineering/shape-mixer-parity/shape_mixer_parity_oracle_generator.mjs"
SPOOKY = ROOT / "docs/port-engineering/spooky-ticker-parity/spooky_ticker_oracle_generator.mjs"


class PublicationRootShapeSpookyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HISTORICAL_AUTHORITY or not CURRENT_AUTHORITY or not LIVE:
            raise unittest.SkipTest("historical and current CPU authorities and NOISEMAKER_FOR_CPU are required")
        cls.historical_authority = Path(HISTORICAL_AUTHORITY)
        cls.current_authority = Path(CURRENT_AUTHORITY)
        cls.live = Path(LIVE)
        if not cls.historical_authority.is_dir() or not cls.current_authority.is_dir() or not cls.live.is_dir():
            raise unittest.SkipTest("configured publication roots are unavailable")

    def authority_for(self, generator: Path) -> Path:
        return self.current_authority if generator == SHAPE else self.historical_authority

    def run_generator(self, generator: Path, mode: str, *, live: str | None = LIVE,
                      extra: tuple[str, ...] = ()):
        env = os.environ.copy()
        if live is None:
            env.pop("NOISEMAKER_FOR_CPU", None)
        else:
            env["NOISEMAKER_FOR_CPU"] = live
        runner = current_run if generator == SHAPE else historical_run
        return runner(
            ["node", str(generator), mode, "--cpu-root", str(self.authority_for(generator)), *extra],
            cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def test_shape_mixer_requires_strict_external_authority_and_live_roots(self):
        self.assertEqual(0, self.run_generator(SHAPE, "--check").returncode)
        for live in (None, str(self.current_authority), str(self.current_authority / "missing-live")):
            with self.subTest(live=live):
                self.assertNotEqual(0, self.run_generator(SHAPE, "--check", live=live).returncode)
        with tempfile.TemporaryDirectory(prefix="shape-mixer-roots-") as raw:
            link = Path(raw) / "live-link"
            simulate_symlink(link, self.live, target_is_directory=True)
            self.assertNotEqual(0, self.run_generator(SHAPE, "--check", live=str(link)).returncode)

    def test_shape_mixer_rejects_unknown_and_duplicate_options(self):
        self.assertNotEqual(0, self.run_generator(SHAPE, "--check", extra=("--check",)).returncode)
        self.assertNotEqual(0, self.run_generator(SHAPE, "--check", extra=("--unknown",)).returncode)

    def test_spooky_ticker_requires_strict_external_authority_and_live_roots(self):
        self.assertEqual(0, self.run_generator(SPOOKY, "--check").returncode)
        self.assertEqual(0, self.run_generator(SPOOKY, "--self-test").returncode)
        for live in (None, str(self.historical_authority), str(self.historical_authority / "missing-live")):
            with self.subTest(live=live):
                self.assertNotEqual(0, self.run_generator(SPOOKY, "--check", live=live).returncode)
        with tempfile.TemporaryDirectory(prefix="spooky-ticker-roots-") as raw:
            link = Path(raw) / "live-link"
            simulate_symlink(link, self.live, target_is_directory=True)
            self.assertNotEqual(0, self.run_generator(SPOOKY, "--check", live=str(link)).returncode)

    def test_spooky_ticker_rejects_unknown_and_duplicate_options(self):
        self.assertNotEqual(0, self.run_generator(SPOOKY, "--check", extra=("--check",)).returncode)
        self.assertNotEqual(0, self.run_generator(SPOOKY, "--check", extra=("--unknown",)).returncode)


if __name__ == "__main__":
    unittest.main()
