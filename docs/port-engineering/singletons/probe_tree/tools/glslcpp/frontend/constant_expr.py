"""Strict, side-effect-free GLSL ES signed-int constant-expression evaluator."""

from __future__ import annotations

from collections.abc import Callable


def _i32(value: int) -> int:
    return ((value + 0x80000000) & 0xffffffff) - 0x80000000


def evaluate_int_constant(node: object, lookup: Callable[[str], int | None]) -> int | None:
    """Evaluate the permitted integer-constant subset or return ``None``.

    The caller supplies lexical constant lookup.  Unsuffixed hexadecimal words
    are GLSL ``int`` bit patterns; unsigned, float, bool, nonconstant and
    malformed operations never become integer constant expressions.
    """
    if not isinstance(node, dict): return None
    kind = node.get("k")
    if kind == "num":
        raw = node.get("value", "")
        if not isinstance(raw, str) or raw.endswith(("u", "U")) or any(char in raw.lower() for char in (".", "e")):
            return None
        try:
            value = int(raw, 0)
        except ValueError:
            return None
        if raw.lower().startswith("0x"):
            return _i32(value) if 0 <= value <= 0xffffffff else None
        return value if -0x80000000 <= value <= 0x7fffffff else None
    if kind == "id": return lookup(node.get("name", ""))
    if kind == "unary" and node.get("op") in {"+", "-", "~"}:
        value = evaluate_int_constant(node.get("x"), lookup)
        if value is None: return None
        return _i32({"+": value, "-": -value, "~": ~value}[node["op"]])
    if kind != "binary": return None
    left, right = evaluate_int_constant(node.get("l"), lookup), evaluate_int_constant(node.get("r"), lookup)
    if left is None or right is None: return None
    operation = node.get("op")
    if operation in {"/", "%"} and right == 0: return None
    if operation in {"<<", ">>"} and not 0 <= right < 32: return None
    quotient = (abs(left) // abs(right)) * (-1 if (left < 0) != (right < 0) else 1) if operation in {"/", "%"} else 0
    if operation == "+": return _i32(left + right)
    if operation == "-": return _i32(left - right)
    if operation == "*": return _i32(left * right)
    if operation == "/": return _i32(quotient)
    if operation == "%": return _i32(left - quotient * right)
    if operation == "<<": return _i32(left << right)
    if operation == ">>": return _i32(left >> right)
    if operation == "&": return _i32(left & right)
    if operation == "|": return _i32(left | right)
    if operation == "^": return _i32(left ^ right)
    return None
