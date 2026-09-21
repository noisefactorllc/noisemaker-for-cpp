"""Raw-bit behavioral regressions for the Node/V8 differential comparator."""

from __future__ import annotations

import json
import pathlib
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPARATOR = ROOT / "docs/port-engineering/v8-math/compare.mjs"


@unittest.skipUnless(shutil.which("node"), "node is required for the real comparator")
class V8MathCompareTests(unittest.TestCase):
    def compare(self, pairs: list[tuple[int, int]]) -> dict:
        with tempfile.TemporaryDirectory(prefix="v8-math-compare-") as directory:
            work = pathlib.Path(directory)
            inputs, v8, cpp = (work / name for name in ("inputs.bin", "v8.bin", "cpp.bin"))
            inputs.write_bytes(b"\0" * (8 * len(pairs)))
            v8.write_bytes(b"".join(struct.pack("<Q", left) for left, _ in pairs))
            cpp.write_bytes(b"".join(struct.pack("<Q", right) for _, right in pairs))
            result = subprocess.run(
                [shutil.which("node"), str(COMPARATOR), "synthetic", str(inputs),
                 str(v8), str(cpp), "1"],
                text=True, capture_output=True, timeout=20,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            return json.loads(result.stdout)

    def test_opposite_sign_ordinal_collision_is_divergent(self) -> None:
        # -1 and +3.9999999999999996 previously mapped to the same ordinal.
        negative, positive = 0xBFF0000000000000, 0x400FFFFFFFFFFFFF
        report = self.compare([(negative, positive), (positive, negative)])
        self.assertEqual(2, report["compared"])
        self.assertEqual(0, report["exact"])
        self.assertEqual(2, report["divergent"])
        self.assertEqual(str(1 << 63), report["max_ulp"])

    def test_signed_zeros_are_distinct_adjacent_values(self) -> None:
        report = self.compare([(0x8000000000000000, 0), (0, 0x8000000000000000)])
        self.assertEqual(2, report["divergent"])
        self.assertEqual("1", report["max_ulp"])

    def test_adjacent_values_on_each_side_are_one_ulp_apart(self) -> None:
        report = self.compare([
            (0xBFF0000000000000, 0xBFF0000000000001),
            (0x3FF0000000000000, 0x3FF0000000000001),
        ])
        self.assertEqual(2, report["divergent"])
        self.assertEqual("1", report["max_ulp"])

    def test_identical_finite_infinite_and_signed_zero_values_are_exact(self) -> None:
        values = [0xFFF0000000000000, 0xBFF0000000000000, 0x8000000000000000,
                  0, 0x3FF0000000000000, 0x7FF0000000000000]
        report = self.compare([(value, value) for value in values])
        self.assertEqual(len(values), report["exact"])
        self.assertEqual(0, report["divergent"])

    def test_both_nan_preserves_existing_payload_independent_policy(self) -> None:
        report = self.compare([
            (0x7FF8000000000000, 0xFFF8000000000001),
            (0x7FF0000000000001, 0x7FF8000000000000),
        ])
        self.assertEqual(2, report["exact"])
        self.assertEqual(0, report["divergent"])

    def test_only_one_nan_is_always_divergent(self) -> None:
        report = self.compare([
            (0x7FF8000000000000, 0x7FF0000000000000),
            (0x3FF0000000000000, 0xFFF8000000000001),
        ])
        self.assertEqual(0, report["exact"])
        self.assertEqual(2, report["divergent"])


if __name__ == "__main__":
    unittest.main()
