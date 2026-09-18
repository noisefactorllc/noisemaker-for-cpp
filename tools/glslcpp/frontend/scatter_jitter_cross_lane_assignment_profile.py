"""Exact frontend admission for scatterJitter's cross-lane assignment.

The JavaScript authority lowers ``offset = dot(offset, perp) * perp;`` to:
  (offset[0] = (dot(offset, perp)) * perp[0], offset[1] = (dot(offset, perp)) * perp[1], offset)
where the second assignment lane reads the destination's mutated first lane.
This profile admits this exact assignment by complete identity and AST proof.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


KEY = "filter/scatter:scatterJitter"
PROFILE = "scatter-jitter-cross-lane-assignment-v1"
SOURCE_PATH = "filter/scatter/scatterJitter.glsl"

RAW_BYTES = 4475
RAW_SHA256 = "e68ff4dc90236e866895d4720d58e81b9151a67d9cc62b43085efbf634fa4e71"
NORMALIZED_BYTES = 2075
NORMALIZED_SHA256 = "049ea5ea34f480892b08bc4adf8e0fc0fbdad000527eeadf7ca57acdf435ed66"
FUNCTIONS_SHA256 = "2d23a7494caa9647aa0c4d8b7f8f314a41bd6fa8175c231879a389935d1f5a51"
WHOLE_SHA256 = "bf8655739e63c1278b5e1f0a1e965a5e0fc93b8f47103363417ca522b3ad14b8"
INTERFACE_SHA256 = "aa0168d5f03b4cc9ce327f7487f92c77e19477ec03a7a727a0bc8e009fb1ec24"

FUNCTION_ID = 14
FUNCTION_NAME = "main"
TARGET_SYMBOL_ID = 30
TARGET_NAME = "offset"
PERP_SYMBOL_ID = 33
PERP_NAME = "perp"
ASSIGNMENT_SPAN = "65:13-65:46"
ASSIGNMENT_SHA256 = "99804a8cd74c70e4f9a1e9f651dd626c2afc22c81eb34d552e6990c48169c5fa"
TARGET_SHA256 = "a0063134e725aef04f0a99a7bf307ce07b6a4848298b5f9d0280688ac5176c17"
RHS_SHA256 = "d43af88081e18a68dbf513557c09444a51d11dadf8e608452a90fe3fbb20c781"
DOT_SHA256 = "ca807f41b3cc30354294a11cfcc68e9b5283bfe8c5089501139543d8ccdce30b"
PERP_SHA256 = "8d349fbee0166d61f9f91ce48c4aff8f60ed04ba9dad8288b2f278efdac61e45"


@dataclass(frozen=True, slots=True)
class ScatterJitterCrossLaneAssignmentProof:
    program: TypedProgram
    function: TypedFunction
    statement: TypedStatement
    assignment: TypedExpression
    target: TypedExpression
    dot_expr: TypedExpression
    perp_expr: TypedExpression


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


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


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_scatter_jitter_cross_lane_assignment(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> ScatterJitterCrossLaneAssignmentProof:
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != KEY or source_hash != RAW_SHA256:
        raise _fail("exact source and key identity required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or _sha(program.functions) != FUNCTIONS_SHA256
            or _whole(program) != WHOLE_SHA256
            or _interface(program) != INTERFACE_SHA256):
        raise _fail("source bytes, normalized source, or interface identity mismatch")
    functions = tuple(item for item in program.functions
                      if item.id == FUNCTION_ID and item.name == FUNCTION_NAME)
    if len(functions) != 1:
        raise _fail("main host identity mismatch")
    function = functions[0]
    matches: list[tuple[TypedStatement, TypedExpression]] = []

    def visit(statement: TypedStatement) -> None:
        for expression in statement.expressions:
            if expression.kind == "assign" and _span(expression) == ASSIGNMENT_SPAN:
                matches.append((statement, expression))
        for child in statement.children:
            visit(child)

    for statement in function.body:
        visit(statement)
    if len(matches) != 1:
        raise _fail("exact scatter jitter cross-lane assignment cardinality required")
    statement, assignment = matches[0]
    if (assignment.operator != "=" or assignment.type.display() != "vec2"
            or len(assignment.children) != 2
            or _sha(assignment) != ASSIGNMENT_SHA256):
        raise _fail("scatter jitter cross-lane assignment shape mismatch")
    target, rhs = assignment.children
    if (target.kind != "id" or target.symbol_id != TARGET_SYMBOL_ID
            or target.symbol.name != TARGET_NAME
            or target.type.display() != "vec2"
            or target.category != "lvalue"
            or _sha(target) != TARGET_SHA256):
        raise _fail("target identity mismatch")
    if (rhs.kind != "binary" or rhs.operator != "*"
            or rhs.type.display() != "vec2"
            or len(rhs.children) != 2
            or _sha(rhs) != RHS_SHA256):
        raise _fail("rhs identity mismatch")
    dot_expr, perp_expr = rhs.children
    if (dot_expr.kind != "builtin" or dot_expr.callee != "dot"
            or len(dot_expr.children) != 2
            or _sha(dot_expr) != DOT_SHA256):
        raise _fail("dot expression identity mismatch")
    if (perp_expr.kind != "id" or perp_expr.symbol_id != PERP_SYMBOL_ID
            or perp_expr.symbol.name != PERP_NAME
            or perp_expr.type.display() != "vec2"
            or _sha(perp_expr) != PERP_SHA256):
        raise _fail("perp expression identity mismatch")
    return ScatterJitterCrossLaneAssignmentProof(
        program, function, statement, assignment, target, dot_expr, perp_expr)


def apply_scatter_jitter_cross_lane_assignment(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    authenticate_scatter_jitter_cross_lane_assignment(program, source_hash, profile)
    return program


__all__ = (
    "KEY", "PROFILE", "SOURCE_PATH", "RAW_BYTES", "RAW_SHA256",
    "NORMALIZED_BYTES", "NORMALIZED_SHA256",
    "ScatterJitterCrossLaneAssignmentProof",
    "authenticate_scatter_jitter_cross_lane_assignment",
    "apply_scatter_jitter_cross_lane_assignment",
)
