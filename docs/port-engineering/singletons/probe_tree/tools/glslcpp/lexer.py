"""Small location-preserving lexer for the Task-5 GLSL subset."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    value: str
    line: int
    column: int


class LexError(ValueError):
    pass


def lex(source: str) -> list[Token]:
    tokens: list[Token] = []
    index = 0
    line = 1
    column = 1
    two_character = {"=="}
    while index < len(source):
        character = source[index]
        if character in " \t\r":
            index += 1
            column += 1
            continue
        if character == "\n":
            index += 1
            line += 1
            column = 1
            continue
        if character.isalpha() or character == "_":
            start = index
            start_column = column
            while index < len(source) and (source[index].isalnum() or source[index] == "_"):
                index += 1
                column += 1
            tokens.append(Token(source[start:index], line, start_column))
            continue
        if character.isdigit() or (character == "." and index + 1 < len(source) and source[index + 1].isdigit()):
            start = index
            start_column = column
            while index < len(source) and (source[index].isdigit() or source[index] in ".eE+-"):
                if source[index] in "+-" and index > start and source[index - 1] not in "eE":
                    break
                index += 1
                column += 1
            tokens.append(Token(source[start:index], line, start_column))
            continue
        pair = source[index:index + 2]
        if pair in two_character:
            tokens.append(Token(pair, line, column))
            index += 2
            column += 2
            continue
        if character in "(){};,=+-*/.":
            tokens.append(Token(character, line, column))
            index += 1
            column += 1
            continue
        raise LexError(f"{line}:{column}: unsupported character {character!r}")
    return tokens
