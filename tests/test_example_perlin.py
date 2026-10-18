"""The documented library example, `examples/perlin.cpp`, runs and draws.

The README promises that `./build/noisemaker-cpu-example-perlin` writes
`perlin.png`. A kernel that gains a uniform the example does not bind makes
the example throw `KernelBindingError` and write nothing, so this test runs the
built example in an empty directory and checks the file it leaves there.

The example is built externally (CTest's `noisemaker-cpu-example-perlin-build`
fixture), so it arrives by env:

    NOISEMAKER_EXAMPLE_PERLIN   built noisemaker-cpu-example-perlin binary
"""

from __future__ import annotations

import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools.benchmark.corpus_lane import resolve_driver


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
WIDTH = 256
HEIGHT = 256


def _paeth(left: int, up: int, up_left: int) -> int:
    estimate = left + up - up_left
    distance_left, distance_up, distance_up_left = (
        abs(estimate - left), abs(estimate - up), abs(estimate - up_left))
    if distance_left <= distance_up and distance_left <= distance_up_left:
        return left
    return up if distance_up <= distance_up_left else up_left


def decode_rgba8_png(png: bytes) -> tuple[int, int, list[bytes]]:
    """Decodes an 8-bit RGBA, non-interlaced PNG into its pixel rows."""
    if png[:8] != PNG_MAGIC:
        raise AssertionError("not a PNG file")
    offset, header, idat = 8, None, bytearray()
    while offset < len(png):
        (length,) = struct.unpack(">I", png[offset:offset + 4])
        kind = png[offset + 4:offset + 8]
        body = png[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if header is None:
        raise AssertionError("PNG has no IHDR chunk")
    width, height, depth, color_type, _compression, _filter, interlace = header
    if (depth, color_type, interlace) != (8, 6, 0):
        raise AssertionError(f"expected non-interlaced 8-bit RGBA, got IHDR {header}")
    stride = width * 4
    raw = zlib.decompress(bytes(idat))
    if len(raw) != height * (stride + 1):
        raise AssertionError("PNG scanline data has the wrong length")
    rows: list[bytes] = []
    previous = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for x in range(stride):
            left = line[x - 4] if x >= 4 else 0
            up = previous[x]
            up_left = previous[x - 4] if x >= 4 else 0
            if kind == 1:
                line[x] = (line[x] + left) & 0xFF
            elif kind == 2:
                line[x] = (line[x] + up) & 0xFF
            elif kind == 3:
                line[x] = (line[x] + ((left + up) >> 1)) & 0xFF
            elif kind == 4:
                line[x] = (line[x] + _paeth(left, up, up_left)) & 0xFF
            elif kind != 0:
                raise AssertionError(f"unknown PNG filter type {kind}")
        rows.append(bytes(line))
        previous = line
    return width, height, rows


class ExamplePerlinTests(unittest.TestCase):
    def setUp(self) -> None:
        self.example = resolve_driver("NOISEMAKER_EXAMPLE_PERLIN", "noisemaker-cpu-example-perlin build")

    def test_the_example_exits_zero_and_writes_a_256_square_picture(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-example-perlin-") as directory:
            work = pathlib.Path(directory)
            result = subprocess.run(
                [str(self.example)], cwd=str(work), text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("wrote perlin.png", result.stdout)
            output = work / "perlin.png"
            self.assertTrue(output.is_file(), "the example wrote no perlin.png")
            width, height, rows = decode_rgba8_png(output.read_bytes())
        self.assertEqual((WIDTH, HEIGHT), (width, height))
        pixels = {row[x:x + 4] for row in rows for x in range(0, len(row), 4)}
        self.assertGreater(len(pixels), 1, "perlin.png holds a single flat color")


if __name__ == "__main__":
    unittest.main()
