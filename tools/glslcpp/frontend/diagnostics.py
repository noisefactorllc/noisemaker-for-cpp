"""Stable semantic diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

from .span import SourceSpan


@dataclass(frozen=True, slots=True)
class SemanticDiagnostic:
    code: str
    span: SourceSpan
    message: str

    def __str__(self) -> str:
        return f"{self.span.program_key}:{self.span.start_line}:{self.span.start_column}: {self.code}: {self.message}"


class SemanticError(ValueError):
    def __init__(self, diagnostics: tuple[SemanticDiagnostic, ...] | list[SemanticDiagnostic]):
        self.diagnostics = tuple(sorted(diagnostics, key=lambda item: (item.span.program_key, item.span.start, item.code, item.message)))
        super().__init__("\n".join(map(str, self.diagnostics)))
