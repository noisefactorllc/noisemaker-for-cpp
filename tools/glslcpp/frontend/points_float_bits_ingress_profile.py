"""Proof profile for authenticated floatBitsToUint ingress in points effects.

Authenticates exact floatBitsToUint expression sites across points programs:
- render/pointsEmit:init (uniform time bit reinterpretation for seed mixing)
- points/flock:agent (hashFloat bit reinterpretation helper)
- points/physarum:agent (hashFloat bit reinterpretation helper)

All candidate expressions operate on a single float operand and return a uint.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "points-float-bits-ingress-v1"

POINTS_EMIT_INIT_KEY = "render/pointsEmit:init"
FLOCK_AGENT_KEY = "points/flock:agent"
PHYSARUM_AGENT_KEY = "points/physarum:agent"

POINTS_FLOAT_BITS_INGRESS_KEYS = frozenset({
    POINTS_EMIT_INIT_KEY,
    FLOCK_AGENT_KEY,
    PHYSARUM_AGENT_KEY,
})

_PROFILES = {
    POINTS_EMIT_INIT_KEY: {
        "raw_bytes": 5236,
        "raw_sha256": "cd266c795b298b372f077e6aeb6f862c75a0970999fba2f87c4462b322592402",
        "norm_bytes": 3527,
        "norm_sha256": "0d6c62fe326d9ec1e8f7ebbfe90ae7338c8bbe7f75b07d13a3007a81002f80dc",
        "functions_sha256": "35e45f77abdb760c64d089a39992f89f269feea0f0987899636d44bc2b0a9ded",
        "whole_sha256": "42b04762d700eb0b0c8c30627e317f0d2795886a7a80a32113f464608aa5e041",
        "interface_sha256": "4c788a40ea67029aafa7a4f2ecddfe820308b1da11f23f8278bf506e97806da4",
        "float_bits_count": 1,
    },
    FLOCK_AGENT_KEY: {
        "raw_bytes": 9726,
        "raw_sha256": "4c664f7443b1085a37896730b5077ed6399ce345a7b5a25101a7a91e00b18363",
        "norm_bytes": 8417,
        "norm_sha256": "0a527a329e196188e6d52ad0e112242446826927e6cf31e1c0abb2bead19fd73",
        "functions_sha256": "67075b3c5276a803fbfe201aafaefdc48a2a276dce18baa539759e03537366b0",
        "whole_sha256": "603b09344b7356dc77c4f4cf426e43eb8cfea815a7f81dd8d291b37371956ac3",
        "interface_sha256": "dc2b8f83d606730c7cc366cc2320707f073f2f4e9e3eaa48bea747f83a6465b3",
        "float_bits_count": 1,
    },
    PHYSARUM_AGENT_KEY: {
        "raw_bytes": 4817,
        "raw_sha256": "d39a5afa26f97da83f61099e712b40d7a901978ce5b2a0070c2d87eef0c03c44",
        "norm_bytes": 3677,
        "norm_sha256": "e4ee3bac5c2066c3c554459b71e0593c6df980b93c60929e85c7962674b601aa",
        "functions_sha256": "f50cfcd2a5bbd96fe3afb495aeff4ce0e31870035da51d5a4bd62f0b77f30e34",
        "whole_sha256": "32d8e51315238189755e5e60df01f40c96f4057a44b95e9c60b93d70db2a1d2c",
        "interface_sha256": "9c75d74e7798cf5017f69ff010e2ab213425c51c5282514e6e1275cfa1eb94ba",
        "float_bits_count": 1,
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


def _walk_expression(value: TypedExpression):
    yield value
    for child in getattr(value, "children", ()):
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in getattr(value, "expressions", ()):
        yield from _walk_expression(expression)
    for child in getattr(value, "children", ()):
        yield from _walk_statement(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_points_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate and return the exact floatBitsToUint expression nodes."""
    if program.key not in POINTS_FLOAT_BITS_INGRESS_KEYS:
        if profile is not None:
            raise _fail("program key is not an admitted points float-bit ingress carrier")
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
                if (getattr(expr, "kind", None) == "builtin"
                        and getattr(expr, "callee", None) == "floatBitsToUint"):
                    if expr.type is None or expr.type.display() != "uint":
                        raise _fail("floatBitsToUint result type must be uint")
                    if (len(expr.children) != 1
                            or expr.children[0].type is None
                            or expr.children[0].type.display() != "float"):
                        raise _fail("floatBitsToUint operand must be a single float")
                    located.append(expr)

    if len(located) != expected["float_bits_count"]:
        raise _fail(
            f"floatBitsToUint count mismatch: expected {expected['float_bits_count']}, "
            f"found {len(located)}")

    return tuple(located)


def apply_points_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the points float-bit ingress carrier profile without changing the tree."""
    authenticate_points_float_bits_ingress(program, source_hash, profile)
    return program


__all__ = (
    "PROFILE",
    "POINTS_EMIT_INIT_KEY",
    "FLOCK_AGENT_KEY",
    "PHYSARUM_AGENT_KEY",
    "POINTS_FLOAT_BITS_INGRESS_KEYS",
    "authenticate_points_float_bits_ingress",
    "apply_points_float_bits_ingress",
)
