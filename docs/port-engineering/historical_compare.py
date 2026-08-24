"""Reporting-only equality helpers for historical reconstruction tests.

The historical tests intentionally keep frozen expectations.  When a
projection is stale, a normal ``assertEqual`` stops at its first artifact and
can hide the rest of the debt.  This module compares without changing either
operand and reports every mismatch in one pass.  It deliberately does not
patch ``unittest`` or raise ``AssertionError``; callers that use
``assertRaises(AssertionError)`` therefore retain their original semantics.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class Mismatch:
    """One path-qualified difference between two values."""

    path: tuple[object, ...]
    expected: object
    actual: object

    def format(self) -> str:
        location = "".join(
            f"[{part!r}]" if isinstance(part, int) else f".{part}"
            for part in self.path
        ).lstrip(".") or "<root>"
        return f"{location}: expected {self.expected!r}, got {self.actual!r}"


class ComparisonError(Exception):
    """Raised only by the opt-in asserting wrapper, never by ``compare``."""

    def __init__(self, mismatches: Sequence[Mismatch]) -> None:
        self.mismatches = tuple(mismatches)
        super().__init__(format_mismatches(self.mismatches))


def compare(expected: Any, actual: Any, *, path: tuple[object, ...] = ()) -> tuple[Mismatch, ...]:
    """Return all differences, preserving inputs and never raising assertions."""

    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        mismatches: list[Mismatch] = []
        keys = sorted(set(expected) | set(actual), key=repr)
        for key in keys:
            child = path + (key,)
            if key not in expected:
                mismatches.append(Mismatch(child, "<missing>", actual[key]))
            elif key not in actual:
                mismatches.append(Mismatch(child, expected[key], "<missing>"))
            else:
                mismatches.extend(compare(expected[key], actual[key], path=child))
        return tuple(mismatches)

    if (isinstance(expected, Sequence) and not isinstance(expected, (str, bytes))
            and isinstance(actual, Sequence)
            and not isinstance(actual, (str, bytes))):
        mismatches = []
        for index in range(max(len(expected), len(actual))):
            child = path + (index,)
            if index >= len(expected):
                mismatches.append(Mismatch(child, "<missing>", actual[index]))
            elif index >= len(actual):
                mismatches.append(Mismatch(child, expected[index], "<missing>"))
            else:
                mismatches.extend(compare(expected[index], actual[index], path=child))
        return tuple(mismatches)

    return () if expected == actual else (Mismatch(path, expected, actual),)


def compare_artifacts(expected: Mapping[str, bytes], actual: Mapping[str, bytes]) -> tuple[Mismatch, ...]:
    """Compare artifact bytes by size and SHA-256, reporting every mismatch."""

    def summary(value: bytes) -> dict[str, object]:
        return {"size": len(value), "sha256": sha256(value).hexdigest()}

    return compare(
        {name: summary(payload) for name, payload in expected.items()},
        {name: summary(payload) for name, payload in actual.items()},
    )


def compare_artifact_pins(
        expected: Mapping[str, tuple[int, str]],
        actual: Mapping[str, bytes],
) -> tuple[Mismatch, ...]:
    """Compare frozen ``(size, sha256)`` pins with rendered artifact bytes."""

    actual_summary = {
        name: {"size": len(payload), "sha256": sha256(payload).hexdigest()}
        for name, payload in actual.items()
    }
    expected_summary = {
        name: {"size": size, "sha256": digest}
        for name, (size, digest) in expected.items()
    }
    return compare(expected_summary, actual_summary)


def format_mismatches(mismatches: Sequence[Mismatch]) -> str:
    """Render a stable multi-line diagnostic suitable for a test failure."""

    if not mismatches:
        return "no mismatches"
    return "\n".join(item.format() for item in mismatches)


def assert_matches(expected: Any, actual: Any) -> None:
    """Opt-in assertion helper using a distinct exception type."""

    mismatches = compare(expected, actual)
    if mismatches:
        raise ComparisonError(mismatches)


__all__ = [
    "ComparisonError",
    "Mismatch",
    "assert_matches",
    "compare",
    "compare_artifacts",
    "compare_artifact_pins",
    "format_mismatches",
]
