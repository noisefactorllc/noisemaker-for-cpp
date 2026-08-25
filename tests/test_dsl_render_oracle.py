"""Authenticated JavaScript render oracle and strict raw RGBA8 comparer.

The tests intentionally use an external CPU root and an external scratch
directory.  The oracle is never allowed to update the checked-in expected
arrays.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parents[1]
ORACLE = ROOT / "tools/dsl/js_render_oracle.mjs"
FIXTURE = ROOT / "tests/fixtures/dsl/blur.dsl"
NONCONSTANT_FIXTURE = ROOT / "tests/fixtures/dsl/blur-nonconstant.dsl"
INCLUDE = ROOT / "tests/oracles/dsl_blur_rgba8.inc"
METADATA = ROOT / "tests/oracles/dsl_blur_rgba8.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class Rgba8Comparison:
    width: int
    height: int
    expected_length: int
    candidate_length: int
    expected_sha256: str
    candidate_sha256: str
    mismatch_count: int
    first_mismatch: dict[str, int | str] | None
    max_delta: int
    ok: bool

    def format(self) -> str:
        lines = [
            f"dimensions={self.width}x{self.height}",
            f"expected length={self.expected_length} candidate length={self.candidate_length}",
            f"expected sha256={self.expected_sha256}",
            f"candidate sha256={self.candidate_sha256}",
            f"mismatch byte count={self.mismatch_count}",
            f"max channel delta={self.max_delta}",
        ]
        if self.expected_length != self.width * self.height * 4 or self.candidate_length != self.width * self.height * 4:
            lines.insert(0, "dimension/length mismatch")
        if self.first_mismatch is not None:
            mismatch = self.first_mismatch
            lines.append(
                "first mismatch: byte offset {offset}, x={x}, y={y}, channel={channel}, "
                "expected={expected}, actual={actual}".format(**mismatch)
            )
        return "\n".join(lines)


def compare_rgba8(width: int, height: int, expected_bytes: bytes, candidate_bytes: bytes) -> Rgba8Comparison:
    """Compare top-down RGBA8 bytes, returning only bounded diagnostics."""
    expected = bytes(expected_bytes)
    candidate = bytes(candidate_bytes)
    expected_hash = sha256_bytes(expected)
    candidate_hash = sha256_bytes(candidate)
    expected_length = len(expected)
    candidate_length = len(candidate)
    required_length = width * height * 4
    if expected_length != required_length or candidate_length != required_length:
        return Rgba8Comparison(width, height, expected_length, candidate_length, expected_hash, candidate_hash, 0, None, 0, False)
    mismatch_count = 0
    max_delta = 0
    first = None
    channels = "RGBA"
    for offset, (wanted, actual) in enumerate(zip(expected, candidate)):
        delta = abs(wanted - actual)
        if delta > max_delta:
            max_delta = delta
        if wanted != actual:
            mismatch_count += 1
            if first is None:
                pixel, channel_offset = divmod(offset, 4)
                first = {
                    "offset": offset,
                    "x": pixel % width,
                    "y": pixel // width,
                    "channel": channels[channel_offset],
                    "expected": wanted,
                    "actual": actual,
                }
    return Rgba8Comparison(width, height, expected_length, candidate_length, expected_hash, candidate_hash, mismatch_count, first, max_delta, mismatch_count == 0 and max_delta == 0 and expected_hash == candidate_hash)


def node() -> str:
    value = shutil.which("node")
    if value is None:
        raise AssertionError("node is required for the authenticated render oracle")
    return value


def run_oracle(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    command = [node(), str(ORACLE), *args]
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=check)


class DslRenderOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cpu_root = pathlib.Path(os.environ.get("NOISEMAKER_CPU_ROOT", ""))

    def require_authority(self) -> pathlib.Path:
        if not self.cpu_root or not self.cpu_root.is_absolute():
            self.skipTest("NOISEMAKER_CPU_ROOT must identify the immutable CPU authority")
        if not self.cpu_root.is_dir():
            self.skipTest(f"CPU authority is unavailable: {self.cpu_root}")
        return self.cpu_root

    def test_fixtures_and_metadata_are_source_bound(self) -> None:
        self.assertEqual(
            sha256_bytes(FIXTURE.read_bytes()),
            "c3a9da6bc816effcaf750a386d1024c4d309cc000ef7cf9c9315843a4cb3df2c",
        )
        self.assertEqual(
            sha256_bytes(NONCONSTANT_FIXTURE.read_bytes()),
            "6190f788d4d5f23895ff57f5234ac11fc3790c6b80912d91d08635fb99b42d80",
        )
        metadata = json.loads(METADATA.read_text(encoding="utf-8"))
        self.assertEqual(metadata["schema"], "noisemaker-for-cpp.dsl-render-oracle.v1")
        self.assertEqual(len(metadata["cases"]), 4)
        self.assertEqual(
            {case["sha256"] for case in metadata["cases"]},
            {
                "488342e4dc1f8a338a094df4466f5d2fa21db347578fef67efcb1714cc694f92",
                "9b645146126a59aa3beba16e108932567283173a5641036927385b8d2337d7af",
                "e5f2f4135e339cd40919565acc2d3d7cb4493c54d7ca0c59dfd681bd42cb7ffb",
                "f8dbfe36fee9b3bb464681c1e4878c12daef9b0e7c7bdcb202a511489229d445",
            },
        )

    def test_strict_comparer_reports_bounded_first_mismatch(self) -> None:
        result = compare_rgba8(2, 1, bytes([1, 2, 3, 4, 5, 6, 7, 8]), bytes([1, 2, 0, 4, 5, 9, 7, 8]))
        self.assertFalse(result.ok)
        self.assertEqual(result.mismatch_count, 2)
        self.assertEqual(result.first_mismatch, {"offset": 2, "x": 0, "y": 0, "channel": "B", "expected": 3, "actual": 0})
        self.assertEqual(result.max_delta, 3)
        self.assertEqual(result.expected_sha256, sha256_bytes(bytes([1, 2, 3, 4, 5, 6, 7, 8])))
        self.assertIn("byte offset 2", result.format())

    def test_strict_comparer_rejects_dimension_and_length_mismatch_before_bytes(self) -> None:
        dimensions = compare_rgba8(2, 2, bytes(16), bytes(4))
        self.assertFalse(dimensions.ok)
        self.assertIn("dimension/length mismatch", dimensions.format())
        self.assertEqual(dimensions.mismatch_count, 0)
        length = compare_rgba8(2, 1, bytes(8), bytes(7))
        self.assertFalse(length.ok)
        self.assertIn("dimension/length mismatch", length.format())

    def test_check_regenerates_twice_without_rewriting_expected(self) -> None:
        authority = self.require_authority()
        before_include = INCLUDE.read_bytes()
        before_metadata = METADATA.read_bytes()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-render-oracle-", dir="/private/tmp") as temporary:
            for _ in range(2):
                result = run_oracle(
                    "--cpu-root", str(authority),
                    "--fixture", str(FIXTURE),
                    "--nonconstant-fixture", str(NONCONSTANT_FIXTURE),
                    "--check", str(INCLUDE),
                    "--metadata", str(METADATA),
                    "--scratch", str(pathlib.Path(temporary) / f"run-{_}"),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(INCLUDE.read_bytes(), before_include)
        self.assertEqual(METADATA.read_bytes(), before_metadata)

    def test_oracle_rejects_update_and_never_mutates_expected(self) -> None:
        before = INCLUDE.read_bytes()
        result = run_oracle("--update", "--cpu-root", str(self.cpu_root), "--fixture", str(FIXTURE))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--update is unsupported", result.stderr)
        self.assertEqual(INCLUDE.read_bytes(), before)

    def test_oracle_rejects_forged_or_symlinked_authority_before_import(self) -> None:
        authority = self.require_authority()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-render-forge-", dir="/private/tmp") as temporary:
            root = pathlib.Path(temporary) / "cpu"
            shutil.copytree(authority, root, symlinks=True)
            marker = root / "imported-marker"
            renderer = root / "src/runtime/renderer.js"
            renderer.write_text(f"import fs from 'node:fs'; fs.writeFileSync({json.dumps(str(marker))}, 'imported');\n", encoding="utf-8")
            result = run_oracle("--cpu-root", str(root), "--fixture", str(FIXTURE), "--scratch", str(pathlib.Path(temporary) / "forged-scratch"))
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue("sha256" in result.stderr or "behavioral lock" in result.stderr)
            self.assertFalse(marker.exists())
            link = pathlib.Path(temporary) / "cpu-link"
            link.symlink_to(authority, target_is_directory=True)
            result = run_oracle("--cpu-root", str(link), "--fixture", str(FIXTURE), "--scratch", str(pathlib.Path(temporary) / "symlink-scratch"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)

    def test_oracle_rejects_mutated_fixture_and_expected_bytes(self) -> None:
        authority = self.require_authority()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-render-mutate-", dir="/private/tmp") as temporary:
            scratch = pathlib.Path(temporary)
            forged_fixture = scratch / "blur.dsl"
            forged_fixture.write_bytes(FIXTURE.read_bytes() + b" ")
            result = run_oracle("--cpu-root", str(authority), "--fixture", str(forged_fixture), "--scratch", str(scratch / "forged-scratch"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source sha256", result.stderr)
            forged_include = scratch / "dsl_blur_rgba8.inc"
            forged_include.write_bytes(INCLUDE.read_bytes().replace(b"488342e4", b"00000000", 1))
            result = run_oracle(
                "--cpu-root", str(authority), "--fixture", str(FIXTURE),
                "--nonconstant-fixture", str(NONCONSTANT_FIXTURE),
                "--check", str(forged_include), "--metadata", str(METADATA),
                "--scratch", str(scratch / "check"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("checked expected", result.stderr)

    def test_oracle_rejects_symlinked_scratch_directory_targeting_repository(self) -> None:
        authority = self.require_authority()
        sentinel = METADATA.read_bytes()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-render-scratch-link-", dir="/private/tmp") as temporary:
            link = pathlib.Path(temporary) / "scratch-link"
            link.symlink_to(ROOT / "tests/oracles", target_is_directory=True)
            result = run_oracle(
                "--cpu-root", str(authority), "--fixture", str(FIXTURE),
                "--nonconstant-fixture", str(NONCONSTANT_FIXTURE), "--scratch", str(link),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)
        self.assertEqual(METADATA.read_bytes(), sentinel)

    def test_oracle_rejects_symlinked_output_file_before_write(self) -> None:
        authority = self.require_authority()
        sentinel = METADATA.read_bytes()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-render-output-link-", dir="/private/tmp") as temporary:
            output = pathlib.Path(temporary) / "output-link.json"
            output.symlink_to(METADATA)
            result = run_oracle(
                "--cpu-root", str(authority), "--fixture", str(FIXTURE),
                "--nonconstant-fixture", str(NONCONSTANT_FIXTURE), "--output", str(output),
                "--scratch", str(pathlib.Path(temporary) / "scratch"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)
        self.assertEqual(METADATA.read_bytes(), sentinel)

    def test_oracle_rejects_symlinked_output_parent_before_write(self) -> None:
        authority = self.require_authority()
        sentinel = METADATA.read_bytes()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-render-parent-link-", dir="/private/tmp") as temporary:
            parent = pathlib.Path(temporary) / "parent-link"
            parent.symlink_to(ROOT / "tests/oracles", target_is_directory=True)
            result = run_oracle(
                "--cpu-root", str(authority), "--fixture", str(FIXTURE),
                "--nonconstant-fixture", str(NONCONSTANT_FIXTURE),
                "--output", str(parent / "forged.json"),
                "--scratch", str(pathlib.Path(temporary) / "scratch"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)
        self.assertEqual(METADATA.read_bytes(), sentinel)

    def test_oracle_accepts_real_external_output_and_scratch(self) -> None:
        authority = self.require_authority()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-render-real-output-", dir="/private/tmp") as temporary:
            root = pathlib.Path(temporary)
            output = root / "output.json"
            result = run_oracle(
                "--cpu-root", str(authority), "--fixture", str(FIXTURE),
                "--nonconstant-fixture", str(NONCONSTANT_FIXTURE), "--output", str(output),
                "--scratch", str(root / "scratch"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["schema"], "noisemaker-for-cpp.dsl-render-oracle.v1")


if __name__ == "__main__":
    unittest.main()
