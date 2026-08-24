"""Strict A/L publication-root contracts for the Parallax and Glitch oracles."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = Path("/private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu")
LIVE = Path("/Users/aayars/platform/noisemaker-for-cpu")
PARALLAX = ROOT / "docs/port-engineering/counted-for-parity/parallax190_oracle_generator.mjs"
GLITCH = ROOT / "docs/port-engineering/matrix/glitch-parity/glitch_parity_oracle_generator.mjs"


def run(generator, *args, env=None):
    child_env = os.environ.copy()
    child_env.pop("NOISEMAKER_FOR_CPU", None)
    if env:
        child_env.update(env)
    return subprocess.run(
        ["node", str(generator), *args],
        cwd=ROOT,
        env=child_env,
        text=True,
        capture_output=True,
    )


class PublicationRootContractTests(unittest.TestCase):
    def test_both_generators_accept_only_explicit_a_and_l(self):
        for generator in (PARALLAX, GLITCH):
            result = run(
                generator,
                "--check",
                "--cpu-root",
                str(AUTHORITY),
                env={"NOISEMAKER_FOR_CPU": str(LIVE)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_live_root_is_not_ignored(self):
        for generator in (PARALLAX, GLITCH):
            result = run(generator, "--check", "--cpu-root", str(AUTHORITY))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NOISEMAKER_FOR_CPU", result.stderr)

    def test_invalid_same_and_symlink_live_roots_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            cases = [
                ("missing", temporary_root / "missing-live"),
                ("same", AUTHORITY),
            ]
            symlink = temporary_root / "live-link"
            symlink.symlink_to(LIVE, target_is_directory=True)
            cases.append(("symlink", symlink))
            for generator in (PARALLAX, GLITCH):
                for label, live in cases:
                    result = run(
                        generator,
                        "--check",
                        "--cpu-root",
                        str(AUTHORITY),
                        env={"NOISEMAKER_FOR_CPU": str(live)},
                    )
                    self.assertNotEqual(result.returncode, 0, f"{generator} accepted {label}")

    def test_authority_symlink_and_cpp_containment_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            symlink = Path(temporary) / "authority-link"
            symlink.symlink_to(AUTHORITY, target_is_directory=True)
            for generator in (PARALLAX, GLITCH):
                linked = run(
                    generator,
                    "--check",
                    "--cpu-root",
                    str(symlink),
                    env={"NOISEMAKER_FOR_CPU": str(LIVE)},
                )
                self.assertNotEqual(linked.returncode, 0)
                cpp = run(
                    generator,
                    "--check",
                    "--cpu-root",
                    str(ROOT),
                    env={"NOISEMAKER_FOR_CPU": str(LIVE)},
                )
                self.assertNotEqual(cpp.returncode, 0)
                live_cpp = run(
                    generator,
                    "--check",
                    "--cpu-root",
                    str(AUTHORITY),
                    env={"NOISEMAKER_FOR_CPU": str(ROOT)},
                )
                self.assertNotEqual(live_cpp.returncode, 0)

    def test_modes_and_options_are_strict(self):
        for generator in (PARALLAX, GLITCH):
            base = ("--cpu-root", str(AUTHORITY))
            for args in (
                ("--self-test", *base),
                ("--check", "--write", *base),
                ("--check", "--check", *base),
                ("--check", *base, "--cpu-root", str(AUTHORITY)),
                ("--check", *base, "--unknown"),
            ):
                result = run(generator, *args, env={"NOISEMAKER_FOR_CPU": str(LIVE)})
                self.assertNotEqual(result.returncode, 0, (generator, args))

    def test_generated_documents_use_stable_root_placeholders(self):
        artifacts = (
            ROOT / "docs/port-engineering/counted-for-parity/parallax190-oracles.json",
            ROOT / "docs/port-engineering/counted-for-parity/parallax190-oracle-report.md",
            ROOT / "docs/port-engineering/matrix/glitch-parity/glitch-parity-oracles.json",
            ROOT / "docs/port-engineering/matrix/glitch-parity/glitch-parity-oracle-report.md",
        )
        for artifact in artifacts:
            text = artifact.read_text()
            self.assertNotIn(str(AUTHORITY), text)
            self.assertNotIn(str(LIVE), text)
            self.assertNotIn("platform/noisemaker-for-cpu", text)
            self.assertIn("<immutable-cpu-snapshot-root>", text)

    def test_generators_have_no_sibling_or_static_cpu_import(self):
        for generator in (PARALLAX, GLITCH):
            source = generator.read_text()
            self.assertNotIn("platformRoot", source)
            self.assertNotIn("noisemaker-for-cpu/src", source)
            self.assertNotIn("path.resolve(cppRoot, '..', 'noisemaker-for-cpu')", source)


if __name__ == "__main__":
    unittest.main()
