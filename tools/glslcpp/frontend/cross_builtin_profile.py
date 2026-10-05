"""Proof profile for authenticated ``cross`` builtin carriers.

Authenticates the exact cross(vec3, vec3) -> vec3 builtin call sites for the
three pending programs whose first blocker is the missing builtin:
- render/render3d:render3d        (2 sites, camera basis vectors)
- render/renderLit3d:renderLit3d  (2 sites, camera basis vectors)
- synth3d/flythrough3d:precompute (7 sites, path wobble basis vectors)

Lowering is ``glsl::cross(left, right)`` in
``include/noisemaker/glsl_runtime.hpp``: JS Number (double) products and
subtraction with exactly one float32 rounding per output lane, matching
``src/csl/glsl-runtime.js``'s ``cross`` in the pinned CPU authority.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "cross-builtin-admission-v1"

RENDER_3D_KEY = "render/render3d:render3d"
RENDER_LIT_3D_KEY = "render/renderLit3d:renderLit3d"
FLYTHROUGH_3D_PRECOMPUTE_KEY = "synth3d/flythrough3d:precompute"

CROSS_KEYS = frozenset({
    RENDER_3D_KEY,
    RENDER_LIT_3D_KEY,
    FLYTHROUGH_3D_PRECOMPUTE_KEY,
})

_PROFILES = {
    RENDER_3D_KEY: {
        "raw_bytes": 14169,
        "raw_sha256": "5ff6fc621924c7c53425c2f18202e549ace6a4ff8a96f9e908ad26bba6e0c7e2",
        "norm_bytes": 10945,
        "norm_sha256": "0fde47a6fd4d39a0cd085a5af72e87de5f3fdf2456c24c2c11667318866dcffb",
        # Re-locked to the seed-attached post-proof tree: this key is also a
        # source-global-literal-int-v1 carrier (MAX_STEPS=256 march bound),
        # and the attached counted-loop proofs change the functions and
        # whole-program identity authenticated below. Pre-re-lock values were
        # functions 166c56ce… / whole a72dd52f… (the pre-proof tree); the
        # interface identity is unchanged (it never folds in the proofs).
        "functions_sha256": "f6bbb586902c4a17f95866f17f1696059021943a1af07e404d398833942d0d84",
        "whole_sha256": "00dfc79804df55b1d20d681fc67ad5da40e6f5effa37c38f26a212063221a744",
        "interface_sha256": "33bbe0c8346497495b7d0bab56b40840854e27a6e56ec14e876000d716e101e6",
        "cross_count": 2,
    },
    RENDER_LIT_3D_KEY: {
        "raw_bytes": 12143,
        "raw_sha256": "77460fb4a9e53f7776d7a3d73cb3fcc1840dce577c6f0989354eeb540011529f",
        "norm_bytes": 9504,
        "norm_sha256": "cc72ea7149272c38ff05fb6842a4f7f720ea05c4065b2e6900edb7f1885ec980",
        # Re-locked to the seed-attached post-proof tree (see the render3d
        # note above). Pre-re-lock: functions 53177f75… / whole 45ddfc7d….
        "functions_sha256": "82752b9a047ff5613dbf7073aad1a4358ed83b46cb93b406aa5b4f78c9cdb11c",
        "whole_sha256": "a7553f3dcf3c0ff6bf74e8d55bb6976c8c70dff4bda014fb3cdd59db50b4450c",
        "interface_sha256": "ec6d329d5512d28f68ce1ea7b2bd102a7ef1985fe5e72d8ed6cf3c11b918ca49",
        "cross_count": 2,
    },
    FLYTHROUGH_3D_PRECOMPUTE_KEY: {
        "raw_bytes": 11404,
        "raw_sha256": "e4288dfc3384f76e63eda968ad4ce3219a9b96989d8e6ff38755dbcf44f788f3",
        "norm_bytes": 7766,
        "norm_sha256": "b8ae9dac1d40943d7bd023fbd6bc26494c686fe62fecd2e26551367ea82eaa58",
        # Re-locked to the seed-attached post-proof tree (2026-10-05 leg):
        # this key is also a parameter-uniform counted-for carrier (`int
        # maxIter` march bounds, see loop_proof.py's flythrough3d entry), and
        # the attached counted-loop proofs change the functions and
        # whole-program identity authenticated below. Pre-re-lock values were
        # functions 6f3edced834a17851390e18356b9a4b6a5fb72edde48d69b50f95b859
        # 4b0e93a / whole 250d2cb9a66ad470c67489ba4e5af1f9036b9e21d5b0f8be391
        # 74df601e29258 (the pre-proof tree) — exactly the loop-proof entry's
        # pre digests; the interface identity is unchanged (it never folds in
        # the proofs).
        "functions_sha256": "7de221d4edf58a01ab203317ccca1cda66915a846e55798d1e12f161482d4375",
        "whole_sha256": "0408c95a2a47cc03302de544b4f68cf50b6b607d2e77291d0c53c3f906424717",
        "interface_sha256": "45e03760bdc51c6217d746b5fb329fe8c67e9f2b5301fb88660c79db93f32c8a",
        "cross_count": 7,
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


def authenticate_cross_sites(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate every ``cross`` builtin site and return the exact AST nodes."""
    if profile != PROFILE:
        raise ValueError(f"{PROFILE}: exact profile carrier required")
    if program.key not in CROSS_KEYS:
        raise ValueError(f"{PROFILE}: program key {program.key} not in {CROSS_KEYS}")
    expected = _PROFILES[program.key]
    if source_hash != expected["raw_sha256"]:
        raise ValueError(f"{PROFILE}: {program.key} caller source hash mismatch")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["norm_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["norm_sha256"]
            or program.body_status != "analyzed"
            or _sha(program.functions) != expected["functions_sha256"]
            or _whole(program) != expected["whole_sha256"]
            or _interface(program) != expected["interface_sha256"]):
        raise ValueError(
            f"{PROFILE}: {program.key} source, function, whole-program, or interface mismatch")

    crosses: list[TypedExpression] = []
    for fn in program.functions:
        for stmt in fn.body:
            for expr in _walk_statement(stmt):
                if (getattr(expr, "kind", None) == "builtin"
                        and getattr(expr, "callee", None) == "cross"):
                    if (expr.type.display() != "vec3"
                            or len(expr.children) != 2
                            or tuple(child.type.display()
                                     for child in expr.children) != ("vec3", "vec3")):
                        raise ValueError(
                            f"{PROFILE}: {program.key} malformed cross site")
                    crosses.append(expr)

    if len(crosses) != expected["cross_count"]:
        raise ValueError(
            f"{PROFILE}: {program.key} expected {expected['cross_count']} cross sites, "
            f"found {len(crosses)}")

    return tuple(crosses)


def apply_cross_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Validate profile and return program untouched (identity carrier)."""
    authenticate_cross_sites(program, source_hash, profile)
    return program
