"""Exact current-source Cell3D hash3 conversion nodes."""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from .typed_ir import TypedExpression, TypedProgram


KEY = "synth3d/cell3d:precompute"
RAW_SHA256 = "83ef13ab1e5997c76e64280d11e0bdb0eaedd6f41a504d2b1e79761cd1dd1755"
NORMALIZED_SHA256 = "f74d023c96692085939e6f474e93f55f73b17a342dcf900099a81fc1007e6b7b"
WHOLE_SHA256 = "685bb4a1f098313184a5e240c811284a4cf37e889ef4e68b24969d1948028427"


class Cell3dHash3Proof(NamedTuple):
    seed_cast: TypedExpression
    q_constructor: TypedExpression


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def authenticate_cell3d_hash3(
        program: TypedProgram, source_hash: str | None) -> Cell3dHash3Proof:
    if (program.key != KEY or source_hash != RAW_SHA256
            or len(program.raw_source.encode("utf-8")) != 5081
            or hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
            != RAW_SHA256
            or len(program.source.encode("utf-8")) != 3703
            or hashlib.sha256(program.source.encode("utf-8")).hexdigest()
            != NORMALIZED_SHA256
            or _sha((program.key, program.source, program.raw_source,
                     program.declarations, program.functions, program.resources,
                     program.body_status, program.local_type_names,
                     program.structs, program.uniform_blocks,
                     program.interface_symbols, program.builtin_symbols,
                     program.preprocessor_defines)) != WHOLE_SHA256):
        raise ValueError("Cell3D hash3 source or typed identity mismatch")
    owners = [function for function in program.functions
              if function.id == 15 and function.name == "hash3"]
    if len(owners) != 1 or len(owners[0].body) != 4:
        raise ValueError("Cell3D hash3 owner mismatch")
    owner = owners[0]
    try:
        seed_cast = owner.body[0].expressions[0].children[1].children[1].children[0]
        q_constructor = owner.body[1].expressions[0].children[0]
        q_offset = q_constructor.children[0]
        scaled = q_offset.children[0].children[0]
    except (IndexError, AttributeError):
        raise ValueError("Cell3D hash3 node mismatch") from None
    if (seed_cast.kind != "construct" or seed_cast.type.display() != "float"
            or seed_cast.span.start_line != 34 or len(seed_cast.children) != 1
            or seed_cast.children[0].kind != "id"
            or seed_cast.children[0].symbol_id != 4
            or seed_cast.children[0].symbol is None
            or seed_cast.children[0].symbol.name != "seed"
            or q_constructor.kind != "construct"
            or q_constructor.type.display() != "uvec3"
            or q_constructor.span.start_line != 35
            or q_offset.kind != "binary" or q_offset.operator != "+"
            or scaled.kind != "binary" or scaled.operator != "*"
            or scaled.type.display() != "vec3"
            or scaled.children[0].kind != "id"
            or scaled.children[0].symbol_id != 12
            or scaled.children[1].kind != "literal"
            or scaled.children[1].literal_value != 1000.0):
        raise ValueError("Cell3D hash3 conversion identity mismatch")
    return Cell3dHash3Proof(seed_cast, q_constructor)
