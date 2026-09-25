"""Proof profile for authenticated post-increment expressions in points effects.

Authenticates exact scalar int post-increment expression statements across points programs:
- points/flock:agent (separationCount++, alignmentCount++, cohesionCount++)
- points/life:agent (neighborCount++)

All candidate expressions operate on a single int lvalue identifier and evaluate to int.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "points-post-admission-v1"

FLOCK_AGENT_KEY = "points/flock:agent"
LIFE_AGENT_KEY = "points/life:agent"

POINTS_POST_KEYS = frozenset({
    FLOCK_AGENT_KEY,
    LIFE_AGENT_KEY,
})

_PROFILES = {
    FLOCK_AGENT_KEY: {
        "raw_bytes": 9726,
        "raw_sha256": "4c664f7443b1085a37896730b5077ed6399ce345a7b5a25101a7a91e00b18363",
        "norm_bytes": 8417,
        "norm_sha256": "0a527a329e196188e6d52ad0e112242446826927e6cf31e1c0abb2bead19fd73",
        "functions_sha256": "67075b3c5276a803fbfe201aafaefdc48a2a276dce18baa539759e03537366b0",
        "whole_sha256": "603b09344b7356dc77c4f4cf426e43eb8cfea815a7f81dd8d291b37371956ac3",
        "interface_sha256": "dc2b8f83d606730c7cc366cc2320707f073f2f4e9e3eaa48bea747f83a6465b3",
        "post_count": 3,
    },
    LIFE_AGENT_KEY: {
        "raw_bytes": 9544,
        "raw_sha256": "78513907f1480250cef2e603e91a012aa4972c2e9e4bd66fc5aefa089a9a4775",
        "norm_bytes": 7560,
        "norm_sha256": "7b68cb1352d33295ea3d044de858c4a3c96a76b82c34450d700ba0ccd2758ba8",
        "functions_sha256": "08322fc7d7cfd4ab169f3280bf6bb73c64630f63c6285e3700d8e12daffc1715",
        "whole_sha256": "ade942f1bc599e45bc607ab2a92116368324c28e4d4818c7c73b9cad826d86ba",
        "interface_sha256": "d0d7e70f8758f7b7a924fefb72d36022ea212bc47446eb29b29c02e69e4c470a",
        "post_count": 1,
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


def authenticate_points_post(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate and return the exact post-increment expression nodes."""
    if program.key not in POINTS_POST_KEYS:
        if profile is not None:
            raise _fail("program key is not an admitted points post carrier")
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


def apply_points_post_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Validate profile and return program untouched (identity carrier)."""
    authenticate_points_post(program, source_hash, profile)
    return program
