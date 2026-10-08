"""Exact frontend admission for Mandelbrot's sequential ``dz`` lane update.

The JavaScript authority stores the two lanes of ``dz`` in source order.  The
second lane therefore observes the first lane's updated value.  This is an
identity-bound carrier for Mandelbrot only; Gradient's whole-vector carrier
must not be widened to cover this distinct source and authority contract.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


KEY = "synth/mandelbrot:mandelbrot"
PROFILE = "mandelbrot-sequential-dz-assignment-v1"
SOURCE_PATH = "synth/mandelbrot/mandelbrot.glsl"
RAW_BYTES = 14931
RAW_SHA256 = "6e6f740356f7ced1cbd40b3a991dd0ef654e39ecaeec8c52e091a08f68e3b3bd"
NORMALIZED_BYTES = 10416
NORMALIZED_SHA256 = "4a28158eff2b0f94d9568c6a06aa61a924e51b4901cb59698a8a4498dd782986"
FUNCTION_ID = 111
FUNCTION_NAME = "mandelbrot_df64"
DESTINATION_SYMBOL_ID = 169
DESTINATION_NAME = "dz"
ASSIGNMENT_SPAN = "235:9-238:10"
ASSIGNMENT_SHA256 = "f6301c8dda9b84a07312efe2581554bfb90b97f33a322496425b88f78a6ffb4b"
CONSTRUCTOR_SHA256 = "d73021dd4b3f95c8ad4e5bfb10d7a84b8d9d556b7f8373bc19fbd2d901c18abb"
DESTINATION_SHA256 = "c66fb46b2e7274d6b5711cd43ff2ac9968938a42502d8c0cd2809a6891f3695a"
@dataclass(frozen=True, slots=True)
class MandelbrotSequentialDzAssignmentProof:
    candidate: TypedProgram
    function: TypedFunction
    statement: TypedStatement
    assignment: TypedExpression
    destination: TypedExpression
    constructor: TypedExpression
    source_lanes: tuple[int, int]
    destination_lanes: tuple[int, int]
    source_reads: int


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


def _walk(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_mandelbrot_sequential_dz_assignment(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> MandelbrotSequentialDzAssignmentProof:
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != KEY or source_hash != RAW_SHA256:
        raise _fail("exact source and key identity required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256):
        raise _fail("source bytes or normalized source identity mismatch")
    functions = tuple(item for item in program.functions
                      if item.id == FUNCTION_ID and item.name == FUNCTION_NAME)
    if len(functions) != 1:
        raise _fail("mandelbrot_df64 ownership mismatch")
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
        raise _fail("exact dz assignment cardinality required")
    statement, assignment = matches[0]
    if (statement.kind != "expr" or len(statement.expressions) != 1
            or assignment.operator != "=" or assignment.type.display() != "vec2"
            or len(assignment.children) != 2):
        raise _fail("sequential dz assignment shape mismatch")
    destination, constructor = assignment.children
    if (destination.kind != "id" or destination.symbol_id != DESTINATION_SYMBOL_ID
            or destination.symbol.name != DESTINATION_NAME
            or destination.type.display() != "vec2"
            or destination.category != "lvalue"
            or _sha(destination) != DESTINATION_SHA256):
        raise _fail("destination identity mismatch")
    if (constructor.kind != "construct"
            or constructor.constructor_type.display() != "vec2"
            or constructor.type.display() != "vec2"
            or len(constructor.children) != 2
            or _sha(constructor) != CONSTRUCTOR_SHA256
            or _sha(assignment) != ASSIGNMENT_SHA256):
        raise _fail("sequential dz constructor identity mismatch")
    reads = tuple(item for item in _walk(constructor)
                  if item.kind == "swizzle" and item.children
                  and item.children[0].kind == "id"
                  and item.children[0].symbol_id == DESTINATION_SYMBOL_ID)
    if len(reads) != 4:
        raise _fail("sequential dz source read cardinality mismatch")
    if tuple(item.member for item in reads) != ("x", "y", "y", "x"):
        raise _fail("sequential dz source lane order mismatch")
    # The four source read nodes are deliberately authenticated by ownership,
    # member order, and the enclosing constructor/assignment hashes.  Do not
    # turn this into a generic vector-assignment admission.
    return MandelbrotSequentialDzAssignmentProof(
        program, function, statement, assignment, destination, constructor,
        (0, 1), (0, 1), len(reads))


def apply_mandelbrot_sequential_dz_assignment(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    authenticate_mandelbrot_sequential_dz_assignment(program, source_hash, profile)
    return program


__all__ = (
    "KEY", "PROFILE", "SOURCE_PATH", "RAW_BYTES", "RAW_SHA256",
    "NORMALIZED_BYTES", "NORMALIZED_SHA256",
    "MandelbrotSequentialDzAssignmentProof",
    "authenticate_mandelbrot_sequential_dz_assignment",
    "apply_mandelbrot_sequential_dz_assignment",
)
