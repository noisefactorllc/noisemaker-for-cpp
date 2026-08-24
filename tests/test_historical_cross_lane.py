"""Tests for the explicit legacy Gradient reconstruction gate."""

from __future__ import annotations

import copy
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from tools.glslcpp import generate_typed_slice, regen_cache

from tests.historical_cross_lane import (
    CROSS_LANE_KEY,
    CROSS_LANE_PROFILE,
    historical_cross_lane,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]


class HistoricalCrossLaneTests(unittest.TestCase):
    def _spec(self) -> dict[str, object]:
        return copy.deepcopy(generate_typed_slice.load_slice(ROOT))

    def _gradient_row(self, spec: dict[str, object]) -> dict[str, object]:
        rows = [row for row in spec["programs"]
                if row.get("program_key") == CROSS_LANE_KEY]
        self.assertEqual(1, len(rows))
        return rows[0]

    def test_legacy_projection_emits_exact_generic_assignment_and_no_carrier(self) -> None:
        spec = self._spec()
        with historical_cross_lane(spec):
            self.assertNotIn(
                "cross_lane_assignment_profile", self._gradient_row(spec))
            with mock.patch.object(generate_typed_slice, "load_slice",
                                   return_value=spec):
                outputs = generate_typed_slice.generate_outputs(ROOT)

        cpp = outputs["src/typed_generated/typed_slice.cpp"].decode()
        gradient = cpp[cpp.index("// Typed IR program: synth/gradient:gradient"):]
        self.assertIn(
            "rotatedCentered = glsl::Vec2((glsl::Mat2(glsl::Vec2(c, (-s)), "
            "glsl::Vec2(s, c)) * centered));",
            gradient)
        self.assertNotIn("set_swizzle<0>(rotatedCentered", gradient)
        manifest = json.loads(
            outputs["src/typed_generated/typed_manifest.json"])
        row = next(item for item in manifest["programs"]
                   if item["program_key"] == CROSS_LANE_KEY)
        self.assertNotIn("cross_lane_assignment_profile", row)

    def test_carrier_is_restored_after_success_and_exception(self) -> None:
        spec = self._spec()
        row = self._gradient_row(spec)
        self.assertEqual(CROSS_LANE_PROFILE,
                         row["cross_lane_assignment_profile"])
        with historical_cross_lane(spec):
            self.assertNotIn("cross_lane_assignment_profile", row)
        self.assertEqual(CROSS_LANE_PROFILE,
                         row["cross_lane_assignment_profile"])
        with self.assertRaisesRegex(RuntimeError, "sentinel failure"):
            with historical_cross_lane(spec):
                raise RuntimeError("sentinel failure")
        self.assertEqual(CROSS_LANE_PROFILE,
                         row["cross_lane_assignment_profile"])

    def test_missing_wrong_and_duplicate_gradient_carriers_fail_closed(self) -> None:
        missing = self._spec()
        del self._gradient_row(missing)["cross_lane_assignment_profile"]
        with self.assertRaisesRegex(ValueError, "exact carrier"):
            with historical_cross_lane(missing):
                pass

        wrong = self._spec()
        self._gradient_row(wrong)["cross_lane_assignment_profile"] = "wrong"
        with self.assertRaisesRegex(ValueError, "exact carrier"):
            with historical_cross_lane(wrong):
                pass

        duplicate = self._spec()
        duplicate["programs"].append(copy.deepcopy(self._gradient_row(duplicate)))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            with historical_cross_lane(duplicate):
                pass

    def test_regen_cache_detects_patched_collaborators_and_bypasses_io(self) -> None:
        spec = self._spec()
        temp_root = os.environ.get("TMPDIR")
        if not temp_root or not pathlib.Path(temp_root).is_dir():
            temp_root = tempfile.gettempdir()
        with tempfile.TemporaryDirectory(
                prefix="historical-cross-lane-cache-",
                dir=temp_root) as cache:
            old = os.environ.get(regen_cache._ENV_VAR)
            os.environ[regen_cache._ENV_VAR] = cache
            try:
                with historical_cross_lane(spec):
                    self.assertTrue(
                        regen_cache._collaborators_are_patched(
                            generate_typed_slice))
                    with mock.patch.object(generate_typed_slice, "load_slice",
                                           return_value=spec):
                        generate_typed_slice.generate_outputs(ROOT)
                self.assertEqual([], list(pathlib.Path(cache).rglob("index.json")))
            finally:
                if old is None:
                    os.environ.pop(regen_cache._ENV_VAR, None)
                else:
                    os.environ[regen_cache._ENV_VAR] = old


if __name__ == "__main__":
    unittest.main()
