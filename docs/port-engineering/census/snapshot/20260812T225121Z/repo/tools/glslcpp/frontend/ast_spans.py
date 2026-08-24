"""Convert parser-private ranged nodes into the legacy plain mapping AST."""

from __future__ import annotations

from .parser import Node
from .span import SourceSpan, span_at


def strip_and_spans(ast: Node, program_key: str, source: str) -> tuple[dict, tuple[tuple[tuple[object, ...], SourceSpan], ...]]:
    """Erase parser-private attributes while retaining one exact span per map."""
    records: list[tuple[tuple[object, ...], SourceSpan]] = []

    def convert(value: object, path: tuple[object, ...]):
        if isinstance(value, Node):
            records.append((path, span_at(program_key, source, value.start, value.end)))
            return {name: convert(child, path + (name,)) for name, child in value.items()}
        if isinstance(value, list):
            return [convert(child, path + (index,)) for index, child in enumerate(value)]
        if isinstance(value, tuple):
            return tuple(convert(child, path + (index,)) for index, child in enumerate(value))
        return value

    plain = convert(ast, ())
    return plain, tuple(records)
