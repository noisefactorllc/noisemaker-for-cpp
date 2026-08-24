"""Exact proof for the two pinned, fixed-size 3x3 convolution tables."""

from __future__ import annotations

import hashlib

from .typed_ir import (FixedNineArrayProof, FixedNineLocalTableProof,
                       TypedExpression, TypedFunction, TypedProgram)


CAPABILITY = "fixed-nine-local-literal-init-counted-read-v1"
SHARPEN_KEY = "filter/sharpen:sharpen"
SOBEL_KEY = "filter/sobel:sobel"
SOURCE_LOCKS = {
    SHARPEN_KEY: (
        "c9a9b196e61a2904b37ad89c7fc46bee1b40b6bba81293dde3d7cd37527773e7",
        "1a252d3d5efca1c657dcde87953b12c081c586da01d885e24d3b50395ec5abb0",
    ),
    SOBEL_KEY: (
        "ef459738b931929a65422df36f852da4e7cbe4e90387690bea747a34a2e52f84",
        "d8aad0d49bd0b1badd5231b46bb7bd5a35f9eddadd466afd4ac9f1a0fc0cbf0c",
    ),
}

_PROFILES = {
    SHARPEN_KEY: (("kernel", "float", 6), ("offsets", "vec2", 16)),
    SOBEL_KEY: (("sobel_x", "float", 6), ("sobel_y", "float", 16),
                ("offsets", "vec2", 26)),
}
_LOOP_INDEX = {SHARPEN_KEY: 27, SOBEL_KEY: 38}
_BODY_COUNT = {SHARPEN_KEY: 29, SOBEL_KEY: 43}
_PAYLOAD = {SHARPEN_KEY: 144, SOBEL_KEY: 216}
_LOOP_READS = {SHARPEN_KEY: ("offsets", "kernel"),
               SOBEL_KEY: ("offsets", "sobel_x", "sobel_y")}
_TYPED_IR_LOCKS = {
    SHARPEN_KEY: "743c607006eb06012c0d4a748afc59e65f9f50314467b1b918e73c745f0928d6",
    SOBEL_KEY: "156a1f9c80868de41a72e6ada9dab841fb89aa4653cd7314179006ed90b201e5",
}
_WHOLE_PROGRAM_LOCKS = {
    SHARPEN_KEY: "cd6f2490b0a9b01c997a4e7b1890505932e8d2f0ae84a28a93c649326c12be9c",
    SOBEL_KEY: "0e391482a7d3d3b6b8877bb8fa56dde92f381d86eed95d9c9d36056b710dadb1",
}


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _fingerprint(functions: tuple[TypedFunction, ...]) -> str:
    return hashlib.sha256(repr(functions).encode("utf-8")).hexdigest()


def _whole_program_fingerprint(program: TypedProgram) -> str:
    """Hash every immutable semantic input except the proof being rebuilt."""
    profile = (
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    )
    return hashlib.sha256(repr(profile).encode("utf-8")).hexdigest()


def source_provenance_error(program, source_hash: str | None) -> str | None:
    """Independently authenticate retained raw/normalized source and defines."""
    locks = SOURCE_LOCKS.get(program.key)
    if locks is None:
        return None
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    if (program.preprocessor_defines or raw_hash != locks[0]
            or normalized_hash != locks[1] or source_hash != locks[0]):
        return "source provenance mismatch for fixed-nine local tables"
    return None


def prove_fixed_nine_local_tables(program: TypedProgram) -> FixedNineLocalTableProof | None:
    """Return a proof only when the pinned table program has its exact typed shape."""
    key = program.key
    functions = program.functions
    defines = program.preprocessor_defines
    if key not in _PROFILES or defines:
        return None
    fingerprint = _fingerprint(functions)
    if fingerprint != _TYPED_IR_LOCKS[key]:
        return None
    whole_program_fingerprint = _whole_program_fingerprint(program)
    if whole_program_fingerprint != _WHOLE_PROGRAM_LOCKS[key]:
        return None
    mains = [function for function in functions if function.name == "main" and function.body]
    if len(mains) != 1:
        return None
    main = mains[0]
    if len(main.body) != _BODY_COUNT[key]:
        return None
    arrays: list[FixedNineArrayProof] = []
    array_ids: dict[int, str] = {}
    for role, element, declaration_index in _PROFILES[key]:
        declaration_statement = main.body[declaration_index]
        if (declaration_statement.kind != "decl"
                or len(declaration_statement.expressions) != 1):
            return None
        declaration = declaration_statement.expressions[0]
        if (declaration.kind != "declaration" or declaration.symbol is None
                or declaration.symbol_id is None or declaration.children
                or declaration.symbol.name != role
                or declaration.type.display() != f"{element}[9]"):
            return None
        store_statements = main.body[declaration_index + 1:declaration_index + 10]
        indices: list[int] = []
        store_spans = []
        store_index_spans = []
        for statement in store_statements:
            if statement.kind != "expr" or len(statement.expressions) != 1:
                return None
            assignment = statement.expressions[0]
            if assignment.kind != "assign" or assignment.operator != "=" or len(assignment.children) != 2:
                return None
            target = assignment.children[0]
            if (target.kind != "index" or len(target.children) != 2
                    or target.children[0].kind != "id"
                    or target.children[0].symbol_id != declaration.symbol_id
                    or target.children[1].kind != "literal"
                    or not isinstance(target.children[1].literal_value, int)):
                return None
            indices.append(target.children[1].literal_value)
            store_spans.append(statement.span)
            store_index_spans.append(target.span)
        if tuple(indices) != tuple(range(9)):
            return None
        array_ids[declaration.symbol_id] = role
        arrays.append(FixedNineArrayProof(
            role, declaration.symbol_id, declaration.symbol.name,
            declaration.type.display(), element, 9,
            "double" if element == "float" else "glsl::Vec2",
            declaration_index, declaration.span,
            tuple(range(declaration_index + 1, declaration_index + 10)),
            tuple(store_spans), tuple(store_index_spans), tuple(indices), (), 1))

    loop_index = _LOOP_INDEX[key]
    loop = main.body[loop_index]
    if (loop.kind != "for" or loop.loop_proof is None
            or loop.loop_proof.start_value != 0 or loop.loop_proof.bound_value != 9
            or loop.loop_proof.comparison != "<" or loop.loop_proof.update != "++"
            or loop.loop_proof.trip_count != 9 or len(loop.children) != 2
            or loop.children[1].kind != "block"):
        return None
    loop_body = loop.children[1]
    expected_loop_body_count = 2 if key == SHARPEN_KEY else 3
    if len(loop_body.children) != expected_loop_body_count:
        return None
    reads: dict[str, list] = {role: [] for role in _LOOP_READS[key]}
    all_references = 0
    for statement in main.body:
        for expression in statement.expressions:
            for node in _walk_expression(expression):
                if node.kind == "id" and node.symbol_id in array_ids:
                    all_references += 1
    for statement in loop_body.children:
        for expression in statement.expressions:
            for node in _walk_expression(expression):
                if (node.kind == "index" and len(node.children) == 2
                        and node.children[0].symbol_id in array_ids
                        and node.children[1].kind == "id"
                        and node.children[1].symbol_id == loop.loop_proof.induction_symbol_id):
                    reads[array_ids[node.children[0].symbol_id]].append(node.span)
    if tuple(role for role in _LOOP_READS[key] if len(reads[role]) == 1) != _LOOP_READS[key]:
        return None
    arrays = [FixedNineArrayProof(
        item.role, item.symbol_id, item.symbol_name, item.array_type,
        item.element_type, item.extent, item.native_element_type,
        item.declaration_statement_index, item.declaration_span,
        item.literal_store_statement_indices, item.literal_store_spans,
        item.literal_store_index_spans, item.literal_store_indices,
        tuple(reads[item.role]), 1)
        for item in arrays]
    first = min(item.declaration_statement_index for item in arrays)
    last = max(item.literal_store_statement_indices[-1] for item in arrays)
    return FixedNineLocalTableProof(
        CAPABILITY, "sharpen-3x3-v1" if key == SHARPEN_KEY else "sobel-3x3-v1",
        main.signature.id, len(main.body), defines, tuple(arrays), first, last,
        loop_index, loop.span, loop.loop_proof.induction_symbol_id, 0, 9, 9, 0, 9,
        expected_loop_body_count, "one-induction-indexed-read-per-table-v1",
        all_references, True, True, True, _PAYLOAD[key], fingerprint,
        whole_program_fingerprint)
