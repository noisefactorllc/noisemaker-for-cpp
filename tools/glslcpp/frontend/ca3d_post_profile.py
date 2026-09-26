"""Proof profile for authenticated post-increment expressions in synth3d effects.

Authenticates the exact scalar int post-increment expression statements in
`synth3d/cellularAutomata3d:simulate` (the seven `count++` sites in
`countMooreNeighbors` and `countVonNeumannNeighbors`).

All candidate expressions operate on a single int lvalue identifier and
evaluate to int. For-loop induction increments (`dz++`, `dy++`, `dx++`) are
authorized by the counted-for loop-proof machinery and are deliberately NOT
part of this profile's census.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "ca3d-post-admission-v1"

CA3D_SIMULATE_KEY = "synth3d/cellularAutomata3d:simulate"

CA3D_POST_KEYS = frozenset({
    CA3D_SIMULATE_KEY,
})

_PROFILES = {
    CA3D_SIMULATE_KEY: {
        "raw_bytes": 8843,
        "raw_sha256": "e29a5b033304463b8610c86823f46c16751270a3cbaa37f1204df968c6c5394a",
        "norm_bytes": 6584,
        "norm_sha256": "c4f0d809ea5e0e86ce47653cccac606490dd363733fb7c187e6b3698b2346f7b",
        "functions_sha256": "1b621c0f0d629f778954826f22601e2391d72f41a1aea83cac78a846e1a67674",
        "whole_sha256": "e99f386c062d5e5dd5e93efc8248913c77707e9da4bd7395f54981839b28e1ff",
        "interface_sha256": "7a402a8665f25b7ac55f9663eedc8a452784c477215093af13340b26f957a3e2",
        "post_count": 7,
    },
}


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


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


def _walk_statement(statement: TypedStatement):
    if statement.kind == "expr":
        for expression in statement.expressions:
            if getattr(expression, "kind", None) == "post":
                yield expression
    for child in statement.children:
        yield from _walk_statement(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_ca3d_post(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate and return the exact post-increment expression nodes."""
    if program.key not in CA3D_POST_KEYS:
        if profile is not None:
            raise _fail("program key is not an admitted cellularAutomata3d post carrier")
        return ()
    if profile != PROFILE:
        raise _fail("exact profile carrier required")

    expected = _PROFILES[program.key]
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")

    if (source_hash != expected["raw_sha256"]
            or len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]):
        raise _fail("source hash mismatch")
    if (len(normalized) != expected["norm_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["norm_sha256"]):
        raise _fail("normalized source hash mismatch")
    if program.body_status != "analyzed":
        raise _fail("program body status is not analyzed")
    if _sha(program.functions) != expected["functions_sha256"]:
        raise _fail("functions hash mismatch")
    if _whole(program) != expected["whole_sha256"]:
        raise _fail("whole-program hash mismatch")
    if _interface(program) != expected["interface_sha256"]:
        raise _fail("interface hash mismatch")

    located: list[TypedExpression] = []
    for function in program.functions:
        for statement in function.body:
            for expr in _walk_statement(statement):
                if (getattr(expr, "kind", None) == "post"
                        and getattr(expr, "operator", None) in {"++", "--"}):
                    if expr.type is None or expr.type.display() != "int":
                        raise _fail("post expression result type must be int")
                    if (len(expr.children) != 1
                            or getattr(expr.children[0], "kind", None) != "id"
                            or expr.children[0].type is None
                            or expr.children[0].type.display() != "int"):
                        raise _fail("post expression operand must be a scalar int identifier")
                    located.append(expr)

    if len(located) != expected["post_count"]:
        raise _fail(
            f"expected {expected['post_count']} post expression sites, found {len(located)}")

    return tuple(located)


def apply_ca3d_post_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Validate profile and return program untouched (identity carrier)."""
    authenticate_ca3d_post(program, source_hash, profile)
    return program
