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
        "raw_bytes": 11303,
        "raw_sha256": "3be70196fe1ffee473c7352e5a13d600f507a1bb6f6005622d1c1d03f8b6c156",
        "norm_bytes": 9625,
        "norm_sha256": "64fba0ca7fa41e701271dd0a713a3427a265f7b599bac510d6eceadea14af792",
        "functions_sha256": "03293a8f9c0ef0a0b627253fe6762f0bd3a62d56c48ed9040bb8913608abee2d",
        "whole_sha256": "59099a0064e8e9af2ebf7477febcb2e1e22fa8272d77222018ec52abfcbbff70",
        "interface_sha256": "25653fe91b5d3024f18a0e791a41dadf848caa7d5644b8b859c581923f4455cb",
        "post_count": 3,
    },
    LIFE_AGENT_KEY: {
        "raw_bytes": 9685,
        "raw_sha256": "60421e21ac31334ab7fa23c20d8dedd97a8285580ea85a110b5a347a44adca1e",
        "norm_bytes": 7701,
        "norm_sha256": "105f5af7c0f541bb3721eefc8c1cce7767b2b8d4dac054f18ec9caf00dc79726",
        "functions_sha256": "dd18a9aacf3cef52499030a4f31546d7adccf8e9ff3be3aeac43929ff1884eb7",
        "whole_sha256": "843592ce9021b2022c3db62ade6c91e1f54b506c45f4e48e4a0ece53a7b3a168",
        "interface_sha256": "1633b00a44698f13f38a1e4956553c1634c65821bc7feeb8bb4d1271d293a25e",
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
