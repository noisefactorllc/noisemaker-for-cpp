"""Authenticate Reverb's two CPU26d vector value copies."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram

KEY = "filter/reverb:reverb"
RAW_SHA256 = "4dde4b901aded65365d0d46145a7d50dcd2b8d279e32c3d1e7bf02cfc7f78bcb"
WHOLE_SHA256 = "0313ed0a8b864a4b008b058ce7584c207f7df3edc0e1cb96b07bd9864d937878"


def authenticate_reverb_value_copies(program: TypedProgram,
                                    source_hash: str) -> tuple[TypedExpression, ...]:
    whole = (program.key, program.source, program.raw_source,
             program.declarations, program.functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.counted_loop_proof,
             program.preprocessor_defines)
    if (program.key != KEY or source_hash != RAW_SHA256
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != RAW_SHA256
            or hashlib.sha256(repr(whole).encode()).hexdigest() != WHOLE_SHA256):
        raise ValueError("reverb-value-copy: source or typed program mismatch")
    nodes = tuple(node for function in program.functions if function.name == "main"
                  for statement in function.body for node in statement.expressions
                  if node.kind == "declaration" and node.symbol is not None
                  and node.symbol.name in {"current", "accum"})
    if len(nodes) != 2:
        raise ValueError("reverb-value-copy: exact two-declaration census required")
    for node, name, target_id, source_name, source_id in zip(
            nodes, ("current", "accum"), (21, 22), ("original", "current"), (20, 21)):
        if (node.symbol.name != name or node.symbol_id != target_id
                or node.type.display() != "vec4" or len(node.children) != 1
                or node.children[0].kind != "id"
                or node.children[0].symbol_id != source_id
                or node.children[0].symbol.name != source_name):
            raise ValueError("reverb-value-copy: declaration identity mismatch")
    return nodes
