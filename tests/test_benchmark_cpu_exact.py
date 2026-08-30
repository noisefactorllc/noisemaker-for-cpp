"""Strict byte comparer and JS CPU corpus runner contract."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from tools.benchmark.exact_compare import compare_rgba8, format_diagnostics


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/benchmark/run_cpu_case.mjs"
FIXTURE = ROOT / "tests/fixtures/dsl/executable-corpus.json"


class ExactCpuBenchmarkTest(unittest.TestCase):
    def test_comparer_reports_first_coordinate_channel_and_hashes(self) -> None:
        result = compare_rgba8(2, 1, bytes([1, 2, 3, 4, 5, 6, 7, 8]), bytes([1, 2, 0, 4, 5, 9, 7, 8]))
        self.assertFalse(result["ok"])
        self.assertEqual(result["mismatchCount"], 2)
        self.assertEqual(result["maxDelta"], 3)
        self.assertEqual(result["firstMismatch"], {"offset": 2, "x": 0, "y": 0, "channel": "B", "expected": 3, "actual": 0})
        self.assertEqual(result["expectedSha256"], hashlib.sha256(bytes([1, 2, 3, 4, 5, 6, 7, 8])).hexdigest())
        self.assertIn("x=0 y=0 channel=B", format_diagnostics(result))

    def test_comparer_rejects_dimensions_and_lengths_before_byte_comparison(self) -> None:
        result = compare_rgba8(2, 2, bytes(16), bytes(4))
        self.assertFalse(result["ok"])
        self.assertEqual(result["mismatchCount"], 0)
        self.assertIsNone(result["firstMismatch"])

    def test_runner_is_a_dedicated_raw_rgba8_authority_driver(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("toRgba8", source)
        self.assertIn("seedSurfaces", source)
        self.assertIn("importCpu", source)
        self.assertIn("top-down", source)
        self.assertNotIn("toDataURL", source)

    def test_js_cpu_runner_is_reproducible_for_the_blur_case(self) -> None:
        node = shutil.which("node")
        # No default: the immutable CPU authority lives outside the repository
        # and its location is machine-specific, so it must arrive by env.
        authority = pathlib.Path(os.environ.get("NOISEMAKER_CPU_ROOT", ""))
        if node is None or not authority.is_absolute() or not authority.is_dir():
            self.skipTest("node and NOISEMAKER_CPU_ROOT (the immutable CPU authority) are required")
        case = next(record for record in json.loads(FIXTURE.read_text(encoding="utf-8"))["records"] if record["effectId"] == "filter/blur")
        # Default temp root only: a pinned macOS-specific root errors on Linux.
        with tempfile.TemporaryDirectory(prefix="noisemaker-cpu-case-") as directory:
            root = pathlib.Path(directory)
            case_path = root / "case.json"
            case_path.write_text(json.dumps(case), encoding="utf-8")
            outputs = []
            for index in (1, 2):
                raw = root / f"run-{index}.rgba8"
                metadata = root / f"run-{index}.json"
                result = subprocess.run([node, str(RUNNER), "--cpu-root", str(authority), "--case", str(case_path), "--rgba8-output", str(raw), "--metadata-output", str(metadata)], cwd=ROOT, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs.append((raw.read_bytes(), json.loads(metadata.read_text(encoding="utf-8"))))
            self.assertEqual(outputs[0][0], outputs[1][0])
            self.assertEqual(outputs[0][1], outputs[1][1])
            self.assertEqual(outputs[0][1]["format"], "rgba8")
            self.assertEqual(outputs[0][1]["orientation"], "top-down")


if __name__ == "__main__":
    unittest.main()
