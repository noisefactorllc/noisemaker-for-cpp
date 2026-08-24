"""Exact identity profile for Perlin's two unreachable scalar uint XORs."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "perlin-scalar-uint-xor-v1"
PERLIN_KEY = "synth/perlin:perlin"

_RAW_BYTES = 10882
_RAW_SHA256 = "9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318"
_NORMALIZED_BYTES = 4875
_NORMALIZED_SHA256 = "88cb30dfb53c75f2d1bf51e9f9b865dca48ffb528e6ff2f77dec224dab309f64"
_FUNCTIONS_SHA256 = "3dbb088e9f6a0ae35d25a3ae197008f62bc7932f3a31697f2ce3fdb05c3e1abc"
_WHOLE_SHA256 = "a47c9ae9ef983c68c6c867296aaa33401841e5a089dddf9842630c6453e775bc"
_INTERFACE_SHA256 = "b8ff41d2d2259908c8efa422227f27b89469110330908e8eb34410319e878066"
_HASH3_SHA256 = "3c3253eaa535ee944476a6c5d60bcb8e66212482d3e4b5af44db96d0e1dfcc50"
_OUTER_SHA256 = "31049e8d38c4a6d26d051659ccd435fb7715906fb861440b7904429f3514495c"
_INNER_SHA256 = "f51b3a1264df7050a8528a5094da6d16c464978d1cb5c8b680461c9173d195cc"
_CONSTRUCTOR_SHA256 = "98f5cc12b9b7d44fefc28337f7d4a2d605eb455d2b36f39f3e80296114e57e2b"
_OPERANDS = (
    ("x", "73:18-73:21", "7a2954d83ebe2be4dfd2ca31558438ff5423668aa4bb593b349b489b7fc92023"),
    ("y", "73:24-73:27", "d15d2568d9165294874cd3c76406e368a48b31c6834d2949d91f7ac4845a81cc"),
    ("z", "73:30-73:33", "5387f564b5e3d096fd99fe10781613d0adab40bc86ebb50a00b79725118f7f08"),
)
_PROFILE_SHA256 = "bc712abd28da325cb3f3d162a6b542b9c28a7491564c44a90a6b090af39c0cbf"
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

__all__ = (
    "PROFILE", "PERLIN_KEY", "authenticate_perlin_scalar_uint_xor",
    "apply_perlin_scalar_uint_xor",
)


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


def _profile_tuple() -> tuple[object, ...]:
    return (
        PROFILE, PERLIN_KEY, _RAW_SHA256, {"DIMENSIONS": 2},
        (49, "hash3", (10, "e0", 0, 0, 0), "73:18-73:33",
         _OUTER_SHA256, _CONSTRUCTOR_SHA256, 0),
        (49, "hash3", (10, "e0", 0, 0, 0, 0), "73:18-73:27",
         _INNER_SHA256, _OUTER_SHA256, 0),
        _FUNCTIONS_SHA256, _WHOLE_SHA256, _INTERFACE_SHA256,
        (45, 46, 48, 50, 51, 52, 53, 54, 55, 56), (47, 49, 57),
    )


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _all_expressions(program: TypedProgram):
    for function in program.functions:
        for statement in function.body:
            yield function.signature.id, statement, from_expression(statement)


def from_expression(statement: TypedStatement):
    for expression in _walk_statement(statement):
        yield expression


def authenticate_perlin_scalar_uint_xor(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, TypedExpression]:
    """Authenticate and return the exact outer and inner scalar XOR objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != PERLIN_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or tuple((item.name, item.kind, item.canonical_value)
                     for item in program.preprocessor_defines)
            != (("DIMENSIONS", "int", "2"),)
            or program.body_status != "analyzed"
            or len(program.declarations) != 17
            or len(program.functions) != 13
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole_fingerprint(program) != _WHOLE_SHA256
            or _interface_fingerprint(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    proof = program.counted_loop_proof
    if (proof is None or (proof.loop_count, proof.unproved_loop_count,
                          proof.max_effective_depth, proof.max_lexical_product,
                          proof.entrypoint_charge, proof.call_graph_acyclic)
            != (2, 0, 1, 8, 28, True)):
        raise _fail("loop proof mismatch")

    hash3 = program.functions[4]
    if ((hash3.signature.id, hash3.name, len(hash3.parameters), len(hash3.body),
         _sha(hash3)) != (49, "hash3", 1, 11, _HASH3_SHA256)
            or (hash3.parameters[0].id, hash3.parameters[0].name,
                hash3.parameters[0].type.display(), hash3.parameters[0].direction)
            != (20, "p", "vec3", "in")):
        raise _fail("hash3 signature or body mismatch")
    returned = hash3.body[10]
    if returned.kind != "return" or len(returned.expressions) != 1:
        raise _fail("hash3 return mismatch")
    division = returned.expressions[0]
    constructor = division.children[0]
    outer = constructor.children[0]
    inner = outer.children[0]
    if (division.kind != "binary" or division.operator != "/"
            or division.type.display() != "float"
            or constructor.kind != "construct"
            or constructor.constructor_type is None
            or constructor.constructor_type.display() != "float"
            or _span(constructor) != "73:12-73:34"
            or _sha(constructor) != _CONSTRUCTOR_SHA256
            or len(constructor.children) != 1):
        raise _fail("float-constructor parent mismatch")
    for value, span, digest in (
            (outer, "73:18-73:33", _OUTER_SHA256),
            (inner, "73:18-73:27", _INNER_SHA256)):
        if (value.kind != "binary" or value.operator != "^"
                or value.type.display() != "uint" or value.category != "rvalue"
                or len(value.children) != 2
                or any(child.type.display() != "uint" for child in value.children)
                or _span(value) != span or _sha(value) != digest):
            raise _fail("scalar XOR site mismatch")
    operands = (inner.children[0], inner.children[1], outer.children[1])
    for operand, (member, span, digest) in zip(operands, _OPERANDS):
        if (operand.kind != "swizzle" or operand.member != member
                or operand.type.display() != "uint" or len(operand.children) != 1
                or operand.children[0].symbol_id != 81
                or _span(operand) != span or _sha(operand) != digest):
            raise _fail("scalar XOR operand identity mismatch")

    scalar_xors: list[TypedExpression] = []
    calls: dict[int, list[int]] = {item.signature.id: [] for item in program.functions}
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if (value.kind == "binary" and value.operator == "^"
                        and value.type.display() == "uint"):
                    scalar_xors.append(value)
                if value.kind == "call" and value.signature_id is not None:
                    calls[function.signature.id].append(value.signature_id)
    if scalar_xors != [outer, inner]:
        raise _fail("scalar XOR cardinality or order mismatch")
    reachable: set[int] = set()
    pending = [50]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(calls[current])
    if (tuple(sorted(reachable)) != (45, 46, 48, 50, 51, 52, 53, 54, 55, 56)
            or tuple(sorted(set(calls) - reachable)) != (47, 49, 57)
            or calls[47].count(49) != 3
            or any(49 in calls[item] for item in reachable)):
        raise _fail("call graph or reachability mismatch")
    return outer, inner


def apply_perlin_scalar_uint_xor(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate this frozen identity profile without changing the tree."""
    authenticate_perlin_scalar_uint_xor(program, source_hash, profile)
    return program
