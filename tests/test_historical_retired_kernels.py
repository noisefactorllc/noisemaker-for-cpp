"""Authenticate the retired kernels used only by historical native assertions."""

from __future__ import annotations

import hashlib
import json
import pathlib
import unittest

from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.generate_typed_slice import apply_compatibility_transform
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tests import corpus_census


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/historical/retired_kernels.cpp"
# Byte-exact block digests extracted from a15c4b6816a3cb4a1811a03429e4fbf84530c722:
# src/typed_generated/typed_slice.cpp (whole-file SHA-256
# 3f7c1644dc966f4f401e523ca0ea830d1ddc2e4372263e8710120930f2176b4c).
BLOCKS = (
    ("filter/bc:bc", 19, "77d9846d7e18e88e151a2ee1da5c959082246fc10f205778c3c57e383a3bf41a"),
    ("filter/corrupt:corrupt", 41, "779c56a55d21fe301ee3cddc0585eb7ff049df818c03cbe455d4519b15f46dc1"),
    ("filter/hs:hs", 71, "a9052db7ee9a12971cd26a6aca9e09b5fa17b9691cd71e5b5acfe3bf25141c37"),
)


class HistoricalRetiredKernelTests(unittest.TestCase):
    def test_original_blocks_match_frozen_hashes_and_immutable_shader_regeneration(self):
        fixture = FIXTURE.read_bytes()
        manifest = corpus_census.historical_document("manifest.json")
        by_key = {row["program_key"]: row for row in manifest["programs"]}
        for key, ordinal, expected_hash in BLOCKS:
            with self.subTest(key=key):
                begin = ("// Typed IR program: " + key + "\n").encode()
                end = ("// End frozen block: " + key + "\n").encode()
                self.assertEqual(1, fixture.count(begin))
                self.assertEqual(1, fixture.count(end))
                block = fixture[fixture.index(begin):fixture.index(end)]
                self.assertEqual(expected_hash, hashlib.sha256(block).hexdigest())
                entry = by_key[key]
                raw = (corpus_census.HISTORICAL_CORPUS / entry["source"]).read_bytes()
                self.assertEqual(entry["raw_sha256"], hashlib.sha256(raw).hexdigest())
                program = analyze_program(parse_program(raw.decode(), key, {}), key)
                transform = "corrupt-sample-uv-alias-v1" if key == "filter/corrupt:corrupt" else None
                if transform:
                    program = apply_compatibility_transform(program, transform)
                regenerated = render_typed_cpp(
                    program, key, entry["raw_sha256"], f"typed_{ordinal}",
                    "bind_" + key.replace("/", "_").replace(":", "_"),
                    compatibility_transform=transform)
                # The original combined translation unit separates emitted blocks
                # by one additional newline; preserve that byte as well.
                self.assertEqual(block, (regenerated + "\n").encode())

    def test_retired_factories_are_only_compiled_into_the_test_target(self):
        cmake = (ROOT / "CMakeLists.txt").read_text()
        fixture_source = "tests/fixtures/historical/retired_kernels.cpp"
        self.assertEqual(1, cmake.count(fixture_source))
        test_target = cmake.split("add_executable(noisemaker-cpu-tests\n", 1)[1].split("\n)", 1)[0]
        self.assertIn(fixture_source, test_target)
        header = (ROOT / "include/noisemaker/generated/catalog.hpp").read_text()
        live = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text())
        live_keys = {row["program_key"] for row in live["programs"]}
        for key in ("filter/bc:bc", "filter/colorspace:colorspace", "filter/hs:hs"):
            with self.subTest(key=key):
                self.assertNotIn(key, live_keys)
                self.assertNotIn("bind_" + key.replace("/", "_").replace(":", "_"), header)


if __name__ == "__main__":
    unittest.main()
