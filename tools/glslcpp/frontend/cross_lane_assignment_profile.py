"""Exact admission for Gradient's cross-lane whole-vector assignment.

The canonical JavaScript lowers ``rotatedCentered = mat2(...) * centered``
to two stores.  ``rotatedCentered`` is the pooled-array alias created by the
preceding declaration, so the second matrix lane reads ``centered[0]`` after
the first store has overwritten it.  This profile deliberately admits one
assignment by complete identity and dependency closure; it is not a generic
vector-assignment rule.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "cross-lane-assignment-v1"
CROSS_LANE_KEY = "synth/gradient:gradient"

_RAW_BYTES = 5439
_RAW_SHA256 = "308537be8f376750a2239be89a07e558e54ee1661a0ea360c6a3e48b8c6e7a75"
_NORMALIZED_BYTES = 4657
_NORMALIZED_SHA256 = "d6fdcc592f2990132ee2b28e0e2138c9465d2046b8d819e7bc1053bcf7499a1c"
_FUNCTIONS_SHA256 = "345937918e081f25978ccaef2a8dad30f58cc6b206767d0443acad486db76e80"
_WHOLE_SHA256 = "9c7d42cb9842b4142ef8f3fb2a02792988e88f1aeea6a3df099f3306178491d1"
_INTERFACE_SHA256 = "bc8f3c588099ccd7cb4e1b68c0656dfe8802f6df7ec1f97bdbb81b66271539e0"
_MAIN_ID = 29
_TARGET_SYMBOL_ID = 50
_SOURCE_SYMBOL_ID = 49
_MATRIX_C_SYMBOL_ID = 51
_MATRIX_S_SYMBOL_ID = 52
_ASSIGNMENT_SPAN = "124:5-124:51"
_ASSIGNMENT_SHA256 = "42ef1c4b53e2c0c696ec15fc0ea4e6b0d080e4cdcf4dcc92196a8a62619fd922"
_TARGET_SHA256 = "89d051f3af74f44d7b6fbbae4fcaf04e70f09468fc7b8b443b6b1ba1095a6062"
_RHS_SHA256 = "d0e2cf9ab49127996d913f904895db9968474c6f3df7ec1d747af3e34c17ab6a"
_MATRIX_SHA256 = "fd22b834ef5c125d7d2465adf7eb16d21ef58866ad3b276ed0b145eb869bb319"
_MATRIX_CHILD_SHA256 = (
    "bfa4a2b09460a7cd8dbe8f3b8727d27141cf63f6e8aa100c81b5b5a2890eaf6f",
    "7262813c8f76749cd0e810ba97780dc9d4ac7df6f69808d56002934fb2dc96f0",
    "b9d6b49eda2e042db4c949603a9980b1fc32b68bfb9307d27ace46aa6a270385",
    "68b66c604f595d66f822a4c591cef9856d2c8b8b9d090d6fda80acaa2df55879",
)
_SOURCE_SHA256 = "315914a10bc8a3bdc1464d892d4708fece4db131cf61e7e8d3c2dc729e815e3d"
_ALIAS_DECL_SPAN = "121:5-121:37"


@dataclass(frozen=True, slots=True)
class CrossLaneAssignmentProof:
    _candidate: TypedProgram
    host: TypedFunction
    statement: TypedStatement
    assignment: TypedExpression
    target: TypedExpression
    target_source: TypedExpression
    rhs_source: TypedExpression
    matrix: TypedExpression
    source_lanes: tuple[int, int]
    destination_lanes: tuple[int, int]


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


def _walk(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_cross_lane_assignment(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> CrossLaneAssignmentProof:
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != CROSS_LANE_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256
            or program.body_status != "analyzed"):
        raise _fail("source, function, whole-program, or interface identity mismatch")
    hosts = tuple(item for item in program.functions
                  if item.id == _MAIN_ID and item.name == "main")
    if len(hosts) != 1:
        raise _fail("main host identity mismatch")
    host = hosts[0]
    alias_declarations = []
    assignments = []
    for item in host.body:
        for expression in item.expressions:
            if expression.kind == "declaration" and expression.symbol_id == _TARGET_SYMBOL_ID:
                alias_declarations.append((item, expression))
            if (expression.kind == "assign" and expression.children
                    and _span(expression) == _ASSIGNMENT_SPAN):
                assignments.append((item, expression))
    if len(alias_declarations) != 1:
        raise _fail("exact pooled alias declaration required")
    alias_statement, alias = alias_declarations[0]
    if (alias.type.display() != "vec2" or len(alias.children) != 1
            or alias.children[0].kind != "id"
            or alias.children[0].symbol_id != _SOURCE_SYMBOL_ID
            or _span(alias_statement) != _ALIAS_DECL_SPAN):
        raise _fail("forged alias dependency")
    if len(assignments) != 1:
        raise _fail("exact whole-vector assignment cardinality required")
    statement, assignment = assignments[0]
    if (_span(assignment) != _ASSIGNMENT_SPAN
            or statement.kind != "expr"
            or assignment.kind != "assign" or assignment.operator != "="
            or assignment.type.display() != "vec2" or len(assignment.children) != 2):
        raise _fail("whole-vector assignment shape mismatch")
    target, rhs = assignment.children
    if (target.kind != "id" or target.symbol_id != _TARGET_SYMBOL_ID
            or target.type.display() != "vec2" or target.category != "lvalue"
            or _sha(target) != _TARGET_SHA256):
        raise _fail("wrong destination or destination type")
    if (rhs.kind != "binary" or rhs.operator != "*"
            or rhs.type.display() != "vec2" or len(rhs.children) != 2):
        raise _fail("whole-vector RHS shape mismatch")
    matrix, rhs_source = rhs.children
    if (matrix.kind != "construct" or matrix.type.display() != "mat2"
            or matrix.constructor_type.display() != "mat2"
            or len(matrix.children) != 4):
        raise _fail("matrix constructor mismatch")
    expected = (("id", _MATRIX_C_SYMBOL_ID, None),
                ("unary", None, "-"), ("id", _MATRIX_S_SYMBOL_ID, None),
                ("id", _MATRIX_C_SYMBOL_ID, None))
    for child, expected_kind in zip(matrix.children, expected):
        if child.kind != expected_kind[0]:
            raise _fail("reordered or forged matrix lane route")
    if (matrix.children[0].symbol_id != _MATRIX_C_SYMBOL_ID
            or matrix.children[1].operator != "-"
            or len(matrix.children[1].children) != 1
            or matrix.children[1].children[0].symbol_id != _MATRIX_S_SYMBOL_ID
            or matrix.children[2].symbol_id != _MATRIX_S_SYMBOL_ID
            or matrix.children[3].symbol_id != _MATRIX_C_SYMBOL_ID):
        raise _fail("matrix lane dependency mismatch")
    if (rhs_source.kind != "id" or rhs_source.type.display() != "vec2"
            or rhs_source.symbol_id != _SOURCE_SYMBOL_ID
            or rhs_source.member is not None
            or _sha(rhs_source) != _SOURCE_SHA256):
        raise _fail("missing or forged cross-lane source")
    source_reads = tuple(value for value in _walk(rhs)
                         if value.kind == "id" and value.symbol_id == _SOURCE_SYMBOL_ID)
    if len(source_reads) != 1 or source_reads != (rhs_source,):
        raise _fail("missing or extra source-lane reads")
    for child, lock in zip(matrix.children, _MATRIX_CHILD_SHA256):
        if _sha(child) != lock:
            raise _fail("reordered or forged matrix lane route")
    if _sha(matrix) != _MATRIX_SHA256:
        raise _fail("matrix constructor identity mismatch")
    if _sha(rhs) != _RHS_SHA256:
        raise _fail("whole-vector RHS identity mismatch")
    if _sha(assignment) != _ASSIGNMENT_SHA256:
        raise _fail("whole-vector assignment identity mismatch")
    return CrossLaneAssignmentProof(
        program, host, statement, assignment, target, alias.children[0],
        rhs_source, matrix, (0, 1), (0, 1))


def apply_cross_lane_assignment(program: TypedProgram, source_hash: str | None,
                                profile: str | None) -> TypedProgram:
    authenticate_cross_lane_assignment(program, source_hash, profile)
    return program


__all__ = ("PROFILE", "CROSS_LANE_KEY", "CrossLaneAssignmentProof",
           "authenticate_cross_lane_assignment", "apply_cross_lane_assignment")
