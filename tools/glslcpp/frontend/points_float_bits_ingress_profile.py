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
        "raw_bytes": 11303,
        "raw_sha256": "3be70196fe1ffee473c7352e5a13d600f507a1bb6f6005622d1c1d03f8b6c156",
        "norm_bytes": 9625,
        "norm_sha256": "64fba0ca7fa41e701271dd0a713a3427a265f7b599bac510d6eceadea14af792",
        "functions_sha256": "03293a8f9c0ef0a0b627253fe6762f0bd3a62d56c48ed9040bb8913608abee2d",
        "whole_sha256": "59099a0064e8e9af2ebf7477febcb2e1e22fa8272d77222018ec52abfcbbff70",
        "interface_sha256": "25653fe91b5d3024f18a0e791a41dadf848caa7d5644b8b859c581923f4455cb",
        "float_bits_count": 1,
    },
    PHYSARUM_AGENT_KEY: {
        "raw_bytes": 6510,
        "raw_sha256": "a9b21cee808cf70e7d29d05f27bdf9bd598ef1f5ac8dae492e6541cf21456e2f",
        "norm_bytes": 5059,
        "norm_sha256": "1d643cf97a028845eb22904b69a761b1002b715df5d92203a68e54137df89290",
        "functions_sha256": "435c2a35ed63fb4f0e4beca71b295e3f00f11c7e62a823927aac4cdeaf602a52",
        "whole_sha256": "4a898e86b6cea2445a247aee4d53b29b7306563996975462dc084945fa0ca878",
        "interface_sha256": "c760682209b67b28f5a5a76e80fd8913dcd7b0a98995ac314c64987bad6276b0",
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
