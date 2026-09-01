"""Exactly one translation unit may opt out of the sanitizers.

`src/effects/generated/effect_catalog.cpp` is excluded under sanitizer
builds because instrumenting its single 7,967-line initializer measured 58x
(1739s against 30s), which is why the sanitizer CI job never once completed.
That carve-out is defensible only while it stays this narrow: a second
`-fno-sanitize=all` would pass every other gate in this repository silently,
and the code it silenced would look instrumented in every report.

This test pins the list. Adding a file to it is a deliberate act that has to
edit this test too, with a reason.
"""

from __future__ import annotations

import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CMAKE = ROOT / "CMakeLists.txt"

# Every source permitted to disable sanitizer instrumentation, and why.
PERMITTED_CARVE_OUTS = {
    "src/effects/generated/effect_catalog.cpp":
        "one 7,967-line generated initializer; 58x under ASan+UBSan",
}


class SanitizerCarveOutTests(unittest.TestCase):
    def test_only_the_documented_sources_disable_sanitizers(self) -> None:
        text = CMAKE.read_text(encoding="utf-8")
        # Every set_property/set_source_files_properties block that disables
        # sanitizing, paired with the sources named in the same statement.
        carved: set[str] = set()
        for statement in re.findall(r"set_(?:property|source_files_properties)\((.*?)\)\s*$",
                                    text, re.S | re.M):
            if "-fno-sanitize" not in statement:
                continue
            carved.update(re.findall(r"[\w./-]+\.(?:cpp|cc|cxx|c)\b", statement))
        self.assertEqual(
            set(PERMITTED_CARVE_OUTS), carved,
            "the set of sanitizer-exempt sources changed; if that is "
            "intended, add the file to PERMITTED_CARVE_OUTS with the "
            "measurement that justifies it")

    def test_the_carve_out_is_guarded_so_ordinary_builds_are_unaffected(self) -> None:
        text = CMAKE.read_text(encoding="utf-8")
        self.assertIn('if(CMAKE_CXX_FLAGS MATCHES "-fsanitize")', text)
        # A bare -fno-sanitize=all outside the guard would silence the file in
        # every build, including the ones nobody thinks are sanitized.
        guarded = re.search(
            r'if\(CMAKE_CXX_FLAGS MATCHES "-fsanitize"\)(.*?)endif\(\)', text, re.S)
        self.assertIsNotNone(guarded)
        self.assertEqual(
            text.count("-fno-sanitize"), guarded.group(1).count("-fno-sanitize"),
            "every -fno-sanitize must sit inside the sanitizer guard")

    def test_the_carved_out_source_exists(self) -> None:
        for relative in PERMITTED_CARVE_OUTS:
            self.assertTrue(
                (ROOT / relative).is_file(),
                f"{relative} is pinned as sanitizer-exempt but does not exist")


if __name__ == "__main__":
    unittest.main()
