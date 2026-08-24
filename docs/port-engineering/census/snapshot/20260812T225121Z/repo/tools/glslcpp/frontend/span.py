"""Immutable normalized-source locations used by the semantic frontier."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceSpan:
    program_key: str
    start: int
    end: int
    start_line: int
    start_column: int
    end_line: int
    end_column: int


def span_at(program_key: str, source: str, start: int = 0, end: int | None = None) -> SourceSpan:
    """Return a normalized-source span, clamped to the supplied source."""
    end = len(source) if end is None else max(start, min(end, len(source)))
    start = max(0, min(start, len(source)))
    before_start, before_end = source[:start], source[:end]
    return SourceSpan(
        program_key, start, end,
        before_start.count("\n") + 1, start - before_start.rfind("\n"),
        before_end.count("\n") + 1, end - before_end.rfind("\n"),
    )
