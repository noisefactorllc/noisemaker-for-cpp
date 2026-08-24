"""Exact identity profile for Lighting's one ``reflect(vec3,vec3)`` call.

`filter/lighting:lighting` calls the GLSL builtin ``reflect`` exactly once,
inside ``applyReflection``, to compute a reflection vector for its chromatic-
aberration pass:

```glsl
vec3 reflectionVec = reflect(incident, normal);
```

`reflect` has zero admission path anywhere in the generator today (unlike
`round`/`tanh`/`floatBitsToUint`/`all`+`lessThanEqual`/the derivative trio,
which are each admitted for specific programs by node identity). This module
follows that exact same zero-vocabulary-growth, node-identity pattern:
`reflect` never joins `_BUILTINS` and never enters the frozen 44-entry
`APPROVED_CAPABILITIES` vocabulary. `glsl::reflect` already exists, generic
over `Vec<N,float>`, in `include/noisemaker/glsl_runtime.hpp` and implements
exactly `I - 2*dot(N,I)*N` with no defensive internal normalize -- verified
against the reference JS by `docs/port-engineering/builtins/oracle/` (the
`reflect-sign-flip` and `reflect-defensive-normalize` mutations both diverge
on a non-unit-N discriminating case), so no runtime change is needed here.

Lighting also carries a `fixed_nine_table_proof` (its Sobel-shaped normal-map
convolution, admitted by extending `fixed_nine_table_proof.py` to a non-
`main` host function) -- that proof is a REQUIRED companion for this program,
not an unrelated carrier to reject, unlike the fully-independent proof
families this module still requires absent.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "lighting-reflect-admission-v1"
LIGHTING_KEY = "filter/lighting:lighting"

_RAW_BYTES = 6049
_RAW_SHA256 = "a0601f7012f385c14c1bdb9f462e5dcb303fe05cfbb4645484d5d1bd629e1a4f"
_NORMALIZED_BYTES = 4997
_NORMALIZED_SHA256 = "c35208b3f864c1a3a75e0aa1f500fab3391c3bef31c6e80da153f04e02b6f343"
_FUNCTIONS_SHA256 = "e5a7a72859a571065a6d6a5660ec6cf2181ce0f4256f1edc028da3cfb47f9240"
_WHOLE_SHA256 = "a24152ae1a234052831e0ab0761aa1b5389ed6aa9a3ea59b5ae1a09216c6220b"
_INTERFACE_SHA256 = "ee35749b616ce087ae1b837c9f5da32f1e27b795904edc8ed19249451551fc2d"

_HOST_ID = 27
_HOST_NAME = "applyReflection"
_NODE_SPAN = "93:26-93:51"
_NODE_SHA256 = "dfc12a08d944a54e06e6a7fd9b6eed922ca56f568254f3d4228ac3e14dcc924a"
_PARENT_SPAN = "93:10-93:51"
_PARENT_SHA256 = "89f8d53ab810bb4713b975a9ddd9b44254b65986ec8eab7f81ac00d5c03f6f0a"

_UNRELATED_PROOF_FIELDS = (
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

__all__ = ("PROFILE", "LIGHTING_KEY", "authenticate_reflect_admission",
           "apply_reflect_admission")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_statement(statement: TypedStatement, results: list) -> None:
    for expression in statement.expressions:
        _walk_expression(expression, results)
    for child in statement.children:
        _walk_statement(child, results)


def _walk_expression(value: TypedExpression, results: list) -> None:
    results.append(value)
    for child in value.children:
        _walk_expression(child, results)


def authenticate_reflect_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedExpression:
    """Authenticate and return the exact frozen ``reflect`` call node."""
    if program.key != LIGHTING_KEY:
        raise _fail("selected key is not Lighting")
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if source_hash != _RAW_SHA256:
        raise _fail("exact caller source digest required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole_fingerprint(program) != _WHOLE_SHA256
            or _interface_fingerprint(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if program.fixed_nine_table_proof is None:
        raise _fail("required companion fixed-nine table proof is absent")
    if any(getattr(program, field) is not None for field in _UNRELATED_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    proof = program.counted_loop_proof
    if proof is None or not proof.call_graph_acyclic:
        raise _fail("loop or call graph profile mismatch")

    census: list[tuple[TypedExpression, int, str]] = []
    for function in program.functions:
        results: list[TypedExpression] = []
        for statement in function.body:
            _walk_statement(statement, results)
        for node in results:
            if node.kind == "builtin" and node.callee == "reflect":
                census.append((node, function.id, function.name))

    if len(census) != 1:
        raise _fail("reflect call-site cardinality mismatch")
    node, function_id, function_name = census[0]
    if (function_id != _HOST_ID or function_name != _HOST_NAME
            or _span(node) != _NODE_SPAN or _sha(node) != _NODE_SHA256
            or node.type.display() != "vec3" or node.category != "rvalue"
            or len(node.children) != 2
            or any(child.type.display() != "vec3" for child in node.children)):
        raise _fail("reflect call-site node profile mismatch")

    # Confirm the exact enclosing declaration, tying the node to the one
    # frozen source site rather than merely its structural shape.
    found_parent = False
    for function in program.functions:
        results = []
        for statement in function.body:
            _walk_statement(statement, results)
        for candidate in results:
            if candidate.kind == "declaration" and candidate.children:
                if candidate.children[0] is node:
                    if (_span(candidate) != _PARENT_SPAN
                            or _sha(candidate) != _PARENT_SHA256):
                        raise _fail("reflect call-site parent mismatch")
                    found_parent = True
    if not found_parent:
        raise _fail("reflect call-site parent not found")

    return node


def apply_reflect_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate this frozen identity profile without changing the tree."""
    authenticate_reflect_admission(program, source_hash, profile)
    return program
