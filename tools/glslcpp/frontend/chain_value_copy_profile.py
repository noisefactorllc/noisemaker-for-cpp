"""Authenticate CPU26d's copied locals in FXAA and Parallax."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram

CONTRACTS = {
    "filter/fxaa:fxaa": (
        "088449aa1fd5855489d3ce0c6ed2986b9b128fa93ace5817dbeafeff92a7bdf0",
        "ef6488fe42615c7e1ed8c9b61931228908fccd6f65776d8b885fa529edf5bca7",
        "result_texel", "vec4", 60, "center_texel", 38,
    ),
    "filter/parallax:parallax": (
        "5ce5dce2ec8e8d7ebd3024c6a5bd5dcb068d0cf322bfd105c4fb3546e1b97642",
        "30e996fec218dfd0c92f0f706d1cde5b0da84b25421fedf6d9f08479421d8a16",
        "prevUV", "vec2", 35, "rayUV", 30,
    ),
}
KEYS = frozenset(CONTRACTS)


def authenticate_chain_value_copies(program: TypedProgram,
                                    source_hash: str) -> tuple[TypedExpression, ...]:
    # CPU26d canonical-kernels.js copies these Float32Arrays. CPU61aa shared
    # them; historical reconstruction must not activate this current profile.
    whole = (program.key, program.source, program.raw_source,
             program.declarations, program.functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.counted_loop_proof,
             program.preprocessor_defines)
    contract = CONTRACTS.get(program.key)
    if (contract is None or source_hash != contract[0]
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != contract[0]
            or hashlib.sha256(repr(whole).encode()).hexdigest() != contract[1]):
        raise ValueError("chain-value-copy: source or typed program mismatch")

    def declarations(statement):
        yield from statement.expressions
        for child in statement.children:
            yield from declarations(child)

    _, _, name, type_name, symbol_id, source_name, source_id = contract
    copies = tuple(node for function in program.functions if function.name == "main"
                   for statement in function.body for node in declarations(statement)
                   if node.kind == "declaration" and node.symbol is not None
                   and node.symbol.name == name)
    if (len(copies) != 1 or copies[0].type.display() != type_name
            or copies[0].symbol_id != symbol_id or len(copies[0].children) != 1
            or copies[0].children[0].kind != "id"
            or copies[0].children[0].symbol_id != source_id
            or copies[0].children[0].symbol is None
            or copies[0].children[0].symbol.name != source_name):
        raise ValueError("chain-value-copy: declaration identity mismatch")
    return copies
