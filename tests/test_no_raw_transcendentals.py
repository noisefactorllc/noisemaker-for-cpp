"""Grep gate: no bare std:: transcendental call survives on a render path.

std::sin/cos/tan/asin/acos/atan/atan2/exp/expm1/log/log2/pow/hypot/tanh are
each measurably NOT bit-exact with V8's Math.* (see
docs/port-engineering/v8-math/v8-math-report.md). The one math layer that
IS -- noisemaker::fdlibm -- exists precisely to close that gap; every call
site was migrated to it in this pass. This test is the backstop: it fails
loudly if a bare std:: call to one of these functions reappears anywhere
under src/ or include/ (the compiled library) or in the typed-C++ emitter
templates that generate src/typed_generated/typed_slice.cpp, so a future
edit cannot silently reopen the hole one call site at a time.

Deliberately excluded (not a hole):
  - fdlibm.cpp / fdlibm_off.cpp: the math layer's OWN implementation, which
    legitimately calls std::pow as V8's live math::pow wrapper's fallback
    (see fdlibm.hpp's provenance comment -- that branch resolves to the
    same shared libm symbol V8 itself calls, so no port is needed there),
    and std::fabs/std::sqrt/std::isnan/std::isinf/std::signbit, which are
    exact on both sides and never at issue.
  - std::sqrt anywhere: IEEE-754 correctly-rounded, already agrees with
    V8's Math.sqrt (a bare machine op) exactly.
  - std::floor/ceil/round/trunc/fabs/fmod/scalbn/isnan/isinf/signbit: exact
    bitwise/hardware operations, not part of this port.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Functions that must route through noisemaker::fdlibm, never bare std::.
GATED = (
    "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
    "exp", "expm1", "log", "log2", "pow", "hypot", "tanh",
)
# std::name( with an optional leading "::" but not preceded by an identifier
# character (so this does not match e.g. `noisemaker::fdlibm::sin` premised
# tokens, and not a struct/member named similarly).
PATTERN = re.compile(
    r"(?<![\w:])std::(" + "|".join(GATED) + r")\s*\(",
)

# Files that legitimately contain std:: calls to these names (the math
# layer's own implementation) and are exempt from this gate.
EXEMPT_FILES = {
    ROOT / "src" / "fdlibm.cpp",
    ROOT / "src" / "fdlibm_off.cpp",
    # Header comments here document the std::pow fallback rationale (see
    # fdlibm.cpp) by name; not a code call site.
    ROOT / "include" / "noisemaker" / "fdlibm.hpp",
}

SEARCH_DIRS = (
    ROOT / "src",
    ROOT / "include",
)
EMITTER_FILES = (
    ROOT / "tools" / "glslcpp" / "emit_typed_cpp.py",
)


def _iter_cpp_files():
    for base in SEARCH_DIRS:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix in (".cpp", ".hpp", ".h", ".cc"):
                yield path


class NoRawTranscendentalsTest(unittest.TestCase):
    def test_no_bare_std_transcendental_in_compiled_library(self) -> None:
        offenders: dict[str, list[str]] = {}
        for path in _iter_cpp_files():
            if path in EXEMPT_FILES:
                continue
            text = path.read_text(encoding="utf-8")
            hits = []
            for lineno, line in enumerate(text.splitlines(), start=1):
                for match in PATTERN.finditer(line):
                    hits.append(f"{lineno}: std::{match.group(1)}(  -- {line.strip()}")
            if hits:
                offenders[str(path.relative_to(ROOT))] = hits
        self.assertEqual(
            offenders, {},
            "bare std:: transcendental call(s) found outside the math layer "
            "(route through noisemaker::fdlibm instead):\n" +
            "\n".join(f"{f}:\n  " + "\n  ".join(hits) for f, hits in offenders.items()))

    def test_no_bare_std_transcendental_in_typed_cpp_emitter(self) -> None:
        offenders: dict[str, list[str]] = {}
        for path in EMITTER_FILES:
            text = path.read_text(encoding="utf-8")
            hits = []
            for lineno, line in enumerate(text.splitlines(), start=1):
                # The emitter's source contains Python code AND embedded
                # C++ string literals; either shape of an emitted bare
                # std::<gated>( is equally a future-generated hole.
                for match in PATTERN.finditer(line):
                    hits.append(f"{lineno}: std::{match.group(1)}(  -- {line.strip()}")
            if hits:
                offenders[str(path.relative_to(ROOT))] = hits
        self.assertEqual(
            offenders, {},
            "bare std:: transcendental call(s) found in a typed-C++ emitter "
            "template (would generate a hole into src/typed_generated/"
            "typed_slice.cpp on the next --write):\n" +
            "\n".join(f"{f}:\n  " + "\n  ".join(hits) for f, hits in offenders.items()))


if __name__ == "__main__":
    unittest.main()
