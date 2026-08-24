"""Normalization for pinned GLSL fixtures; this is not a general preprocessor."""

from __future__ import annotations


def normalize(source: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(source):
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            if end < 0:
                raise ValueError("unterminated block comment")
            result.extend("\n" for character in source[index:end + 2] if character == "\n")
            index = end + 2
            continue
        if source.startswith("//", index):
            end = source.find("\n", index + 2)
            if end < 0:
                break
            result.append("\n")
            index = end + 1
            continue
        result.append(source[index])
        index += 1
    kept: list[str] = []
    skip_gl_es = False
    for line in "".join(result).splitlines():
        stripped = line.strip()
        if stripped == "#ifdef GL_ES":
            skip_gl_es = True
            continue
        if stripped == "#endif" and skip_gl_es:
            skip_gl_es = False
            continue
        if skip_gl_es or stripped.startswith("#version") or stripped.startswith("precision "):
            continue
        kept.append(line)
    return "\n".join(kept) + "\n"
