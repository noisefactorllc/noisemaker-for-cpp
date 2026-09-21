"""Behavioral dimension validation through the real corpus driver CLI."""

from __future__ import annotations

import hashlib
import pathlib
import struct
import subprocess
import tempfile
import unittest

from tools.benchmark.corpus_lane import resolve_driver


class CaseDriverDimensionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = resolve_driver("NOISEMAKER_DSL_CPU_CASE", "noisemaker-dsl-cpu-case")
        temporary = tempfile.TemporaryDirectory(prefix="case-driver-dimensions-")
        self.addCleanup(temporary.cleanup)
        self.work = pathlib.Path(temporary.name)
        self.source = self.work / "case.dsl"
        self.source.write_text(
            "search synth\nmedia(scaleAmt: 100, imageSize: [2, 2]).write(o0)\nrender(o0)\n",
            encoding="utf-8",
        )
        self.digest = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def invoke(self, texture: str, width: str = "2", height: str = "2",
               frame: str = "0") -> subprocess.CompletedProcess:
        return subprocess.run([
            str(self.driver), "--source-file", str(self.source),
            "--source-sha256", self.digest,
            "--width", width, "--height", height, "--time", "0", "--frame", frame, "--seed", "1",
            "--external-texture", texture,
            "--rgba8-output", str(self.work / "out.rgba8"),
            "--metadata-output", str(self.work / "out.json"),
        ], text=True, capture_output=True, timeout=20)

    def test_invalid_external_dimensions_exit_usage_without_undefined_conversion(self) -> None:
        upper_bound = str(1 << (struct.calcsize("P") * 8))
        for invalid in ("nan", "inf", "-inf", "0", "-1", "1.5", upper_bound):
            for axis in (0, 1):
                dimensions = ["1", "1"]
                dimensions[axis] = invalid
                with self.subTest(value=invalid, axis=axis):
                    result = self.invoke(f"imageTex={dimensions[0]}x{dimensions[1]}:ff0000ff")
                    self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                    self.assertIn("must be a positive integer", result.stderr)
                    self.assertNotIn("runtime error:", result.stderr)

    def test_invalid_render_dimensions_exit_usage_before_integer_conversion(self) -> None:
        upper_bound = str(1 << (struct.calcsize("P") * 8))
        for invalid in ("nan", "inf", "-inf", "0", "-1", "1.5", upper_bound):
            for axis in (0, 1):
                dimensions = ["2", "2"]
                dimensions[axis] = invalid
                with self.subTest(value=invalid, axis=axis):
                    result = self.invoke("imageTex=1x1:ff0000ff", *dimensions)
                    self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                    self.assertIn("must be a positive integer", result.stderr)
                    self.assertNotIn("runtime error:", result.stderr)

    def test_external_byte_count_overflow_exits_usage_before_surface_allocation(self) -> None:
        # This dimension is representable, but multiplying it by four wraps
        # size_t to zero. Empty bytes must not slip through that wrapped check.
        overflowing = str(1 << (struct.calcsize("P") * 8 - 2))
        for width, height in ((overflowing, "1"), ("1", overflowing)):
            with self.subTest(width=width, height=height):
                result = self.invoke(f"imageTex={width}x{height}:")
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertIn("dimensions", result.stderr)

    def test_invalid_frame_exits_usage_before_integer_conversion(self) -> None:
        for invalid in ("nan", "inf", "-inf", "-1", "1.5", str(1 << 32)):
            with self.subTest(value=invalid):
                result = self.invoke("imageTex=1x1:ff0000ff", frame=invalid)
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertIn("must be a nonnegative integer", result.stderr)
                self.assertNotIn("runtime error:", result.stderr)

    def test_zero_and_maximum_uint32_frame_are_accepted(self) -> None:
        for frame in ("0", str((1 << 32) - 1)):
            with self.subTest(frame=frame):
                result = self.invoke("imageTex=1x1:ff0000ff", frame=frame)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(bytes.fromhex("ff0000ff" * 4), (self.work / "out.rgba8").read_bytes())

    def test_one_and_two_pixel_texture_dimensions_render_the_supplied_color(self) -> None:
        for size in (1, 2):
            with self.subTest(size=size):
                result = self.invoke(f"imageTex={size}x{size}:" + "ff0000ff" * (size * size))
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(bytes.fromhex("ff0000ff" * 4), (self.work / "out.rgba8").read_bytes())


if __name__ == "__main__":
    unittest.main()
