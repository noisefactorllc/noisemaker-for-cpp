"""Exact C++/JavaScript lexer stream comparison.

The CPU root is deliberately an explicit input. This test never imports the
live repository checkout and never permits the oracle to rewrite fixtures.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/dsl/frontend-cases.json"
EXPECTED = ROOT / "tests/oracles/dsl_frontend_expected.txt"
ORACLE_JS = ROOT / "tools/dsl/js_frontend_oracle.mjs"
DEFAULT_CPP = pathlib.Path(os.environ.get("NOISEMAKER_DSL_CPP_ORACLE", ""))


class DslFrontendOracleTest(unittest.TestCase):
    def test_checked_stream_matches_authoritative_node_oracle_and_cpp(self) -> None:
        cpu_root_value = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not cpu_root_value:
            self.fail("NOISEMAKER_CPU_ROOT must explicitly identify the frozen CPU authority")
        cpu_root = pathlib.Path(cpu_root_value)
        self.assertTrue(cpu_root.is_absolute(), "NOISEMAKER_CPU_ROOT must be absolute")
        self.assertTrue((cpu_root / "src/dsl/tokenize.js").is_file())
        node = shutil_which("node")
        self.assertIsNotNone(node, "node is required for the authority oracle")
        cpp = DEFAULT_CPP
        if not cpp:
            candidates = [
                pathlib.Path("/private/tmp/noisemaker-cpp-task3-build/noisemaker-dsl-frontend-oracle"),
                pathlib.Path("/private/tmp/noisemaker-cpp-dsl-build/noisemaker-dsl-frontend-oracle"),
            ]
            cpp = next((candidate for candidate in candidates if candidate.is_file()), pathlib.Path())
        self.assertTrue(cpp.is_file(), "set NOISEMAKER_DSL_CPP_ORACLE to the built C++ oracle")

        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-oracle-") as temporary:
            generated = pathlib.Path(temporary) / "expected.txt"
            subprocess.run(
                [node, str(ORACLE_JS), "--cpu-root", str(cpu_root), "--fixtures", str(FIXTURES), "--output", str(generated)],
                check=True,
                text=True,
            )
            self.assertEqual(generated.read_text(encoding="utf-8"), EXPECTED.read_text(encoding="utf-8"))
            fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
            cpp_records = []
            for fixture in fixtures:
                result = subprocess.run(
                    [str(cpp), "--name", fixture["name"], "--source", fixture["source"], "--source-name", fixture.get("sourceName", fixture["name"])],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                cpp_records.append(result.stdout)
            self.assertEqual("".join(cpp_records), EXPECTED.read_text(encoding="utf-8"))


def shutil_which(command: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = pathlib.Path(directory) / command
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


if __name__ == "__main__":
    unittest.main()
