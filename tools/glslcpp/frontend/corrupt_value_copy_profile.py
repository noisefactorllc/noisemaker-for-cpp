"""Authenticate CPU26d's value copy of Corrupt's sampling coordinate."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram

KEY = "filter/corrupt:corrupt"
PROFILE = "corrupt-sample-uv-copy-v2"
RAW_SHA256 = "b81642d2e63294f9f51656eb2441cdaf479c495c5e4acb0d3a4907a13b070d02"
WHOLE_SHA256 = "967c9e0b769163cf4c768d2f38274009297a1474762237c489277a3352ca5472"


def authenticate_corrupt_value_copy(program: TypedProgram, source_hash: str,
                                   profile: str) -> TypedExpression:
    # CPU26d canonicalFactory40 copies the Float32Array at sampleUv's
    # declaration. CPU61aa instead shared uv; the old transform stays available
    # only to explicit historical reconstruction.
    whole = (program.key, program.source, program.raw_source,
             program.declarations, program.functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.counted_loop_proof,
             program.preprocessor_defines)
    if (program.key != KEY or profile != PROFILE or source_hash != RAW_SHA256
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != RAW_SHA256
            or hashlib.sha256(repr(whole).encode()).hexdigest() != WHOLE_SHA256):
        raise ValueError("corrupt-value-copy: source or typed program mismatch")
    copies = tuple(node for function in program.functions if function.name == "main"
                   for statement in function.body for node in statement.expressions
                   if node.kind == "declaration" and node.symbol is not None
                   and node.symbol.name == "sampleUv")
    if (len(copies) != 1 or copies[0].type.display() != "vec2"
            or copies[0].symbol_id != 90 or len(copies[0].children) != 1
            or copies[0].children[0].kind != "id"
            or copies[0].children[0].symbol_id != 78
            or copies[0].children[0].symbol.name != "uv"):
        raise ValueError("corrupt-value-copy: declaration identity mismatch")
    return copies[0]
