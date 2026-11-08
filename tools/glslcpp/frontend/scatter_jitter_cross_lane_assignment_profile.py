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

RAW_BYTES = 5665
RAW_SHA256 = "bf22d2fba241ce0ce0c05bd96c11ebb515e8ed458cf03e050aa5d1493dcf53e6"
NORMALIZED_BYTES = 2500
NORMALIZED_SHA256 = "b34c492f0486c9551f914b5bb38331db601ea99eb4cffe265d1a87b156870257"
FUNCTIONS_SHA256 = "971379d8a4b2f71f69e268bfb7458b40996826a4ea4d9427bf466d6f23a2704a"
WHOLE_SHA256 = "c01899902f19f8841cc078156fdeb69155e472e599ddcc4fcf5b92e52f770ac0"
INTERFACE_SHA256 = "6f2019aca55e3d73220f28398bcb92afdd1685d7f0df30299284fa58a75b84f0"

FUNCTION_ID = 13
FUNCTION_NAME = "main"
TARGET_SYMBOL_ID = 33
TARGET_NAME = "offset"
PERP_SYMBOL_ID = 36
PERP_NAME = "perp"
ASSIGNMENT_SPAN = "83:13-83:46"
ASSIGNMENT_SHA256 = "04dcd4021b8468984bdfd4869d8afe881706a75fcaec218fe0a461e7f6d4df2d"
TARGET_SHA256 = "f24b8e7a58297dcee913503263bcbf578c2138998f5b91e0cbd7e9f5e8568f25"
RHS_SHA256 = "5d75c166b06364a2f068f2eb0cc48f4119303c48757f2d7cf3500560ebda9757"
DOT_SHA256 = "4707b71dbc9f83e9c5630c4a103aabcc8e49e45ec48badab6e9c058351715d3b"
PERP_SHA256 = "105182b548e549576a2da043d9fb46997cc0e5c5f95a54bc025bac4a2103d3bb"


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
