"""Authenticate Grade LUT's original-color copy under its existing source lock."""

from __future__ import annotations

from .grade_index_expression_profile import authenticate_grade_index_expression
from .typed_ir import TypedExpression, TypedProgram


KEY = "filter/grade:lut"


def authenticate_grade_value_copy(
        program: TypedProgram, source_hash: str | None,
        index_profile: str | None) -> TypedExpression:
    if program.key != KEY:
        raise ValueError("Grade value copy requires the exact LUT program")
    # This existing proof authenticates raw and normalized source, the complete
    # typed tree, interface, defines and every dynamic index site independently.
    authenticate_grade_index_expression(program, source_hash, index_profile)
    declarations = [node for function in program.functions if function.name == "main"
                    for statement in function.body for node in statement.expressions
                    if node.kind == "declaration" and node.symbol_id == 127]
    if len(declarations) != 1:
        raise ValueError("Grade value copy declaration census differs")
    node = declarations[0]
    if (node.symbol is None or node.symbol.name != "graded"
            or node.symbol.storage != "local" or node.type.display() != "vec3"
            or len(node.children) != 1):
        raise ValueError("Grade value copy declaration differs")
    source = node.children[0]
    if (source.kind != "id" or source.symbol_id != 126 or source.symbol is None
            or source.symbol.name != "rgb" or source.symbol.storage != "local"
            or source.type.display() != "vec3"):
        raise ValueError("Grade value copy source differs")
    return node
