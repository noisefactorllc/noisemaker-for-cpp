"""Authenticate Feedback's single local HSV hue lane read/write."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "filter/feedback:feedback"
RAW_SHA256 = '047cbf124875f9d146c41c24f58081e19fb78b7d8c5cf4887e4255ea5bb43ca3'
RAW_BYTES = 12346
NORMALIZED_SHA256 = '4321055e525b9c7073552a29549b8b8d80dcba0b3d68e20702513e458194d403'
NORMALIZED_BYTES = 10330
FUNCTIONS_SHA256 = 'd918c2b1ae48bcf9bdafd19338cfa0c0ddbf7ee9c25a0a1c260824f13d4836f5'
WHOLE_SHA256 = '8d49dc4074386964408001d4708087a6548f93e99489c98e4a8e9d9a7ba7e17c'
INTERFACE_SHA256 = '098b518737980638801a1cd6f4de758f2f02e8b7428417aecb03455325143ac9'
SITES = (
    (372, 5, '8a036d47a0d88a73ec1675218bc7250aecf2bab425fe130a67cb300ba54dbcb1'),
    (372, 20, '99411d54abba37091a83eefcee66804416b5efbed12b4bea5a52405250dacbe6'),
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
                  if function.id == 54 and function.name == "main"), None)
    if owner is None or len(owner.body) <= 6:
        raise ValueError("feedback-hue-index: exact main required")
    declaration = owner.body[4]
    assignment = owner.body[6]
    if (declaration.kind != "decl" or len(declaration.expressions) != 1
            or declaration.expressions[0].kind != "declaration"
            or declaration.expressions[0].symbol_id != 113
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
                or node.children[0].symbol_id != 113
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
                       if value.symbol_id == 113)
    if len(references) != 4 or {id(value) for value in references} != {
            id(declaration.expressions[0]), id(left.children[0]),
            id(right.children[0]),
            id(owner.body[7].expressions[0].children[1].children[0])}:
        raise ValueError("feedback-hue-index: HSV reference census drift")
    return indexes
