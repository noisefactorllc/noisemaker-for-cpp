"""Authenticate Feedback's single local HSV hue lane read/write."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "filter/feedback:feedback"
RAW_SHA256 = "d0048fb91c30eafbb4532b2f02ed416e3dff61b14ce5861ce3565db81a743ca2"
RAW_BYTES = 10931
NORMALIZED_SHA256 = "005bfd2ef62b54c3fc25c84b00e849e69ceb4f60a8dec9151c80adf024cae7ff"
NORMALIZED_BYTES = 9712
FUNCTIONS_SHA256 = "c513473aaf247612529ac3ff413bfaaf9b9db39f4ccab48e2fe8a4d9a2d23cb0"
WHOLE_SHA256 = "a4fab30e15ee657fd07db30a4a8b72cc42d0bba5508e9068e118cf918df6f09c"
INTERFACE_SHA256 = "e34402ada45a1b7701180153d2ea82b305452cb9f98a9f1f40bdc2a0e3b6e977"
SITES = (
    (339, 5, "7bb66e788204f426192ae0c29f9792c8b1045abbd6e8159d90e86b653bc44874"),
    (339, 18, "fc77182b3092027b5d33a0ff528abe22aa8581210bb6f4e2d039c0630a77443f"),
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _expressions(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _expressions(child)


def _statements(value: TypedStatement):
    for expression in value.expressions:
        yield from _expressions(expression)
    for child in value.children:
        yield from _statements(child)


def authenticate_feedback_hue_indices(
        program: TypedProgram, source_hash: str | None) -> tuple[TypedExpression, ...]:
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (program.key != KEY or source_hash != RAW_SHA256
            or len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or program.preprocessor_defines != () or program.body_status != "analyzed"):
        raise ValueError("feedback-hue-index: exact source and compile configuration required")
    whole = (program.key, program.source, program.raw_source,
             program.declarations, program.functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.counted_loop_proof,
             program.preprocessor_defines)
    interface = (program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines)
    if (_sha(program.functions) != FUNCTIONS_SHA256 or _sha(whole) != WHOLE_SHA256
            or _sha(interface) != INTERFACE_SHA256):
        raise ValueError("feedback-hue-index: function, whole-program, or interface drift")
    owner = next((function for function in program.functions
                  if function.id == 47 and function.name == "main"), None)
    if owner is None or len(owner.body) <= 6:
        raise ValueError("feedback-hue-index: exact main required")
    declaration = owner.body[4]
    assignment = owner.body[5]
    if (declaration.kind != "decl" or len(declaration.expressions) != 1
            or declaration.expressions[0].kind != "declaration"
            or declaration.expressions[0].symbol_id != 101
            or len(declaration.expressions[0].children) != 1
            or declaration.expressions[0].children[0].kind != "call"
            or assignment.kind != "expr" or len(assignment.expressions) != 1
            or assignment.expressions[0].kind != "assign"
            or assignment.expressions[0].operator != "="):
        raise ValueError("feedback-hue-index: initialized HSV assignment required")
    indexes = tuple(value for function in program.functions
                    for statement in function.body for value in _statements(statement)
                    if value.kind == "index")
    if len(indexes) != 2:
        raise ValueError("feedback-hue-index: exact two index sites required")
    left, right = indexes
    for node, (line, column, digest) in zip(indexes, SITES):
        if (node.span.start_line != line or node.span.start_column != column
                or node.type.display() != "float" or len(node.children) != 2
                or node.children[0].kind != "id"
                or node.children[0].symbol_id != 101
                or node.children[0].type.display() != "vec3"
                or node.children[1].kind != "literal"
                or node.children[1].literal_value != 0
                or _sha(node) != digest):
            raise ValueError("feedback-hue-index: exact lane site drift")
    expression = assignment.expressions[0]
    if (expression.children[0] is not left
            or not any(value is right for value in _expressions(expression.children[1]))):
        raise ValueError("feedback-hue-index: hue read/write path drift")
    references = tuple(value for function in program.functions
                       for statement in function.body for value in _statements(statement)
                       if value.symbol_id == 101)
    if len(references) != 4 or {id(value) for value in references} != {
            id(declaration.expressions[0]), id(left.children[0]),
            id(right.children[0]),
            id(owner.body[6].expressions[0].children[1].children[0])}:
        raise ValueError("feedback-hue-index: HSV reference census drift")
    return indexes
