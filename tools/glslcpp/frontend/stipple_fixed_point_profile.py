"""Exact node-identity admission profile for ``filter/stipple:stipple``'s
unsigned fixed-point kernel (``stipple-fixed-point-v1``).

The pinned Stipple source computes every hash, noise value, distance and blend
in unsigned integer fixed point. Its typed tree carries constructs that the
frozen capability vocabulary does not admit for any other program:

- fbm's function-local ``const uint M[5] = uint[5](...)`` table and its
  ``M[k]`` read in the counted ``k`` loop;
- scalar ``uint >> uint`` shifts (hash16, lum16, smooth12, vnoise, fbm, the
  dot radius, the reticulation amplitude, the mezzoStrokes grain);
- the ``ivec2 >> int`` shift of the pointillize seed texel;
- the left shifts: ``uvec2 << uvec2`` (vnoise's and pointillize's 12-bit
  fractions) and ``uint << uint`` (the dot-edge ramp);
- isqrt's ``r--``/``r++`` steps on a uint local.

This module admits exactly those nodes, by object identity, after it has
locked the raw and normalized source bytes, the function bodies, the whole
program and its interface. Nothing here widens a shared capability, type or
operator vocabulary, and no other program can carry the profile.

It also returns the nodes whose CPU authority evaluation the emitter must
reproduce instead of the GLSL uint lowering, as canonicalFactory149 compiles
them:

- pointillize's ink/paper blend ``paper * (4096u - inside) + ink * inside``.
  The kernel materializes the uvec3 sum in a ``PooledFloat32Array`` before
  ``vec3.rshift``, so every lane is rounded to float32 before its ``>> 12``;
- pointillize's scalar uint divisions, ``2097152u / c256`` and the dot edge
  ramp's ``(...) << 12u) / uint(2 * aa)``. The kernel truncates both (``|0``
  and ``Math.trunc``), so neither is a fractional Number.

Two typed trees carry the profile. The typed slice parses MODE as a
runtime-int define (``runtime-defines-generic-v1``), so every MODE branch is
in its tree. The corpus probe parses the authority's default define, MODE=0,
so only the pointillize branch remains in ``main``. Both trees are locked.
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "filter/stipple:stipple"
PROFILE = "stipple-fixed-point-v1"

RAW_BYTES = 10823
RAW_SHA256 = "84755c2b6b2bf86a9c0b73a1faceda9b9bbb5fbf7d7a0570e91e2caf979f52a6"

TABLE_NAME = "M"
TABLE_TYPE = "uint[5]"
TABLE_VALUES = (65536, 32284, 15903, 7834, 3859)

# Per-tree locks. "runtime": MODE as a runtime int (typed slice);
# "default": MODE=0 baked (corpus probe).
_LOCKS = {
    "runtime": {
        "defines": (("MODE", "str", "int"),),
        "norm_bytes": 4821,
        "norm_sha256": "8dfaabf22a11f15e61c0abe50ced8036dc5acecc02a21b5bb5286266128f0eaa",
        "functions_sha256": "4daea2de58e00e9f8525a82ec36b0214cc556c07adfff07f73fd8418536359bd",
        "whole_sha256": "789bff0aaa4d54537f2e9f42420d59d14f00376162ae1a4d841e42b9718b6bae",
        "interface_sha256": "7c261199c004c39a6f6b58a0d9c1e53391beda34743b66369db7933b9bee9d7f",
        "scalar_uint_rshifts": 14,
    },
    "default": {
        "defines": (("MODE", "int", "0"),),
        "norm_bytes": 3930,
        "norm_sha256": "7fed33c85686d96f9419f9cb7163859713ad1d7733b6369af0e9f77f3bbef58e",
        "functions_sha256": "da8f05c8ca222ab0969b61dce8d56dd06fa768eb8a4c8539fcd438e8bfb32802",
        "whole_sha256": "ac1db4c7bb393863957b4c8ee04ae23ab422ecc2a9d938a93ac249f172bf812e",
        "interface_sha256": "a020dff4bb0abc7b58c1677fa246d283ab426e7db93d704c89d86dc339e54bcd",
        "scalar_uint_rshifts": 10,
    },
}

FUNCTION_NAMES = ("fbm", "hash16", "inkStep", "isqrt", "lum16", "main",
                  "pcg3d", "smooth12", "unorm16", "vnoise")


class StippleProof(NamedTuple):
    program: TypedProgram
    variant: str
    table_declaration: TypedExpression
    table_constructor: TypedExpression
    table_reference: TypedExpression
    table_index: TypedExpression
    scalar_uint_rshifts: tuple[TypedExpression, ...]
    signed_vector_rshift: TypedExpression
    left_shifts: tuple[TypedExpression, ...]
    uint_steps: tuple[TypedExpression, ...]
    truncated_divisions: tuple[TypedExpression, ...]
    f32_blend: TypedExpression

    @property
    def array_type_nodes(self) -> tuple[TypedExpression, ...]:
        """The two ``uint[5]``-typed nodes the type gate meets; the index
        read consumes the third, ``table_reference``."""
        return (self.table_declaration, self.table_constructor)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _function_nodes(program: TypedProgram, name: str) -> tuple[TypedExpression, ...]:
    function = next(item for item in program.functions if item.name == name)
    return tuple(node for statement in function.body
                 for node in _walk_statement(statement))


def _signature(node: TypedExpression) -> tuple[str, ...]:
    return (node.type.display(),
            *(child.type.display() for child in node.children))


def _variant(program: TypedProgram) -> str:
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    for name, lock in _LOCKS.items():
        if defines == lock["defines"]:
            return name
    raise ValueError(f"{PROFILE}: MODE define drift {defines!r}")


def authenticate_stipple_fixed_point(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> StippleProof:
    """Authenticate the pinned Stipple tree and return its admitted nodes."""
    if profile != PROFILE:
        raise ValueError(f"{PROFILE}: exact profile carrier required")
    if program.key != KEY:
        raise ValueError(f"{PROFILE}: program key {program.key} is not {KEY}")
    if source_hash != RAW_SHA256:
        raise ValueError(f"{PROFILE}: caller source hash mismatch")
    variant = _variant(program)
    lock = _LOCKS[variant]
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != lock["norm_bytes"]
            or hashlib.sha256(normalized).hexdigest() != lock["norm_sha256"]
            or program.body_status != "analyzed"
            or _sha(program.functions) != lock["functions_sha256"]
            or _whole(program) != lock["whole_sha256"]
            or _interface(program) != lock["interface_sha256"]):
        raise ValueError(
            f"{PROFILE}: source, function, whole-program, or interface mismatch")
    if tuple(item.name for item in program.functions) != FUNCTION_NAMES:
        raise ValueError(f"{PROFILE}: function identity drift")

    nodes = tuple(node for function in program.functions
                  for statement in function.body
                  for node in _walk_statement(statement))
    arrays = tuple(node for node in nodes if node.type.kind == "array")
    fbm = _function_nodes(program, "fbm")
    declarations = tuple(node for node in arrays if node.kind == "declaration")
    constructors = tuple(node for node in arrays if node.kind == "construct")
    references = tuple(node for node in arrays if node.kind == "id")
    indexes = tuple(node for node in nodes if node.kind == "index")
    if (len(arrays) != 3 or len(declarations) != 1 or len(constructors) != 1
            or len(references) != 1 or len(indexes) != 1):
        raise ValueError(f"{PROFILE}: fixed table census drift")
    declaration, constructor = declarations[0], constructors[0]
    reference, index = references[0], indexes[0]
    if (declaration.type.display() != TABLE_TYPE
            or declaration.symbol is None
            or declaration.symbol.name != TABLE_NAME
            or declaration.symbol.storage != "const"
            or declaration.symbol.writable
            or declaration.children != (constructor,)
            or constructor.type.display() != TABLE_TYPE
            or len(constructor.children) != len(TABLE_VALUES)
            or any(child.kind != "literal" or child.type.display() != "uint"
                   or child.literal_value != value
                   for child, value in zip(constructor.children, TABLE_VALUES))
            or reference.type.display() != TABLE_TYPE
            or reference.symbol_id != declaration.symbol_id
            or index.type.display() != "uint"
            or index.children[0] is not reference
            or len(index.children) != 2
            or index.children[1].kind != "id"
            or index.children[1].type.display() != "int"
            or index.children[1].symbol.name != "k"
            or not all(any(node is item for item in fbm)
                       for node in (declaration, constructor, reference, index))):
        raise ValueError(f"{PROFILE}: fixed table identity drift")

    rshifts = tuple(node for node in nodes
                    if node.kind == "binary" and node.operator == ">>")
    scalar = tuple(node for node in rshifts
                   if _signature(node) == ("uint", "uint", "uint"))
    signed = tuple(node for node in rshifts
                   if _signature(node) == ("ivec2", "ivec2", "int"))
    vector = tuple(node for node in rshifts
                   if _signature(node) in {("uvec2", "uvec2", "uvec2"),
                                            ("uvec3", "uvec3", "uvec3")})
    if (len(scalar) != lock["scalar_uint_rshifts"] or len(signed) != 1
            or len(scalar) + len(signed) + len(vector) != len(rshifts)
            or any(node.category != "rvalue" for node in (*scalar, *signed))):
        raise ValueError(f"{PROFILE}: right shift census drift")

    lshifts = tuple(node for node in nodes
                    if node.kind == "binary" and node.operator == "<<")
    if (tuple(_signature(node) for node in lshifts)
            != (("uvec2", "uvec2", "uvec2"), ("uint", "uint", "uint"),
                ("uvec2", "uvec2", "uvec2"))
            or any(node.category != "rvalue" for node in lshifts)):
        raise ValueError(f"{PROFILE}: left shift census drift")

    isqrt = _function_nodes(program, "isqrt")
    steps = tuple(node for node in nodes
                  if node.kind in {"post", "unary"}
                  and node.operator in {"++", "--"}
                  and node.type.display() != "int")
    if (tuple(node.operator for node in steps) != ("--", "--", "++", "++")
            or any(node.kind != "post" or node.type.display() != "uint"
                   or len(node.children) != 1
                   or node.children[0].kind != "id"
                   or node.children[0].symbol.name != "r"
                   or not any(node is item for item in isqrt)
                   for node in steps)):
        raise ValueError(f"{PROFILE}: uint step census drift")

    main = _function_nodes(program, "main")
    divisions = tuple(node for node in nodes
                      if node.kind == "binary" and node.operator == "/"
                      and node.type.display() in {"int", "uint"})
    if (tuple(_signature(node) for node in divisions)
            != (("uint", "uint", "uint"), ("uint", "uint", "uint"))
            or not all(any(node is item for item in main) for node in divisions)
            or divisions[0].children[0].kind != "literal"
            or divisions[0].children[0].literal_value != 2097152
            or divisions[1].children[0].kind != "binary"
            or divisions[1].children[0].operator != "<<"):
        raise ValueError(f"{PROFILE}: scalar uint division census drift")

    blends = tuple(node for node in main
                   if node.kind == "binary" and node.operator == "+"
                   and _signature(node) == ("uvec3", "uvec3", "uvec3"))
    if len(blends) != 1:
        raise ValueError(f"{PROFILE}: pointillize blend census drift")
    blend = blends[0]
    left, right = blend.children
    if (left.kind != "binary" or left.operator != "*"
            or right.kind != "binary" or right.operator != "*"
            or _signature(left) != ("uvec3", "uvec3", "uint")
            or _signature(right) != ("uvec3", "uvec3", "uint")
            or left.children[0].kind != "id"
            or left.children[0].symbol.name != "paper"
            or right.children[0].kind != "id"
            or right.children[0].symbol.name != "ink"
            or right.children[1].kind != "id"
            or right.children[1].symbol.name != "inside"):
        raise ValueError(f"{PROFILE}: pointillize blend identity drift")

    return StippleProof(program, variant, declaration, constructor, reference,
                        index, scalar, signed[0], lshifts, steps, divisions,
                        blend)


def apply_stipple_fixed_point(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Validate the profile and return the program unchanged (identity carrier)."""
    authenticate_stipple_fixed_point(program, source_hash, profile)
    return program
