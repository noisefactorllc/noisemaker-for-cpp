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
RENDER_DYNAMIC_PROFILE = "cross-builtin-render3d-dynamic-v1"

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
        "raw_bytes": 14393,
        "raw_sha256": "138d3e0daa247100fe3553b2699bce3f302e77fce25d9d4fb507868d31a84a30",
        "norm_bytes": 10963,
        "norm_sha256": "a211ec112f89ccea8cabeee2bd7f45a896b9c54812b49ff4a6091e9629aa3f53",
        # Re-locked to the seed-attached post-proof tree: this key is also a
        # source-global-literal-int-v1 carrier (MAX_STEPS=256 march bound),
        # and the attached counted-loop proofs change the functions and
        # whole-program identity authenticated below. Pre-re-lock values were
        # functions 166c56ce… / whole a72dd52f… (the pre-proof tree); the
        # interface identity is unchanged (it never folds in the proofs).
        "functions_sha256": "f658d31e5a1ba348713e862f9016ece193419831f58da04b035a4c7bb0faba37",
        "whole_sha256": "8de2584a45895b30fec34b527112c52c3b0688f041c299a42bdeac879e493838",
        "interface_sha256": "4f1eb4b5aea7ad075a5756dfa748d88f83705993085f1446c427d9d4e09cb3fe",
        "cross_count": 2,
    },
    RENDER_LIT_3D_KEY: {
        "raw_bytes": 12406,
        "raw_sha256": "ea309e7e9c4bcb13fd96bf05f0e587bfd25557b7184872b32aabc160df49b627",
        "norm_bytes": 9486,
        "norm_sha256": "436cdf22da60272b948b145b0dabc113d65bc1b9006659517e07dcd80ba48b62",
        # Re-locked to the seed-attached post-proof tree (see the render3d
        # note above). Pre-re-lock: functions 53177f75… / whole 45ddfc7d….
        "functions_sha256": "d6c4f6bbf5a4cd19ca2006fd1b997fde798c280a51039246be9e1c423cc41e38",
        "whole_sha256": "2688f3be3bed47ff1facee122dd2e7da11501f21044bda9206c847efaf077ac0",
        "interface_sha256": "e3f61fcd73cd0441cf76d4a119f618bd6fad0515ec6b588d074ccc2751e87b86",
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

_RENDER_DYNAMIC_PROFILE = {
    "raw_bytes": 14393,
    "raw_sha256": "138d3e0daa247100fe3553b2699bce3f302e77fce25d9d4fb507868d31a84a30",
    "norm_bytes": 11017,
    "norm_sha256": "001cda0e746f30bfd3c0d407ebc5b057cbbca5f7d359cae71bec196e37292b57",
    "functions_sha256": "5dcdd99853125e9f83aab78cd0fb2bfbeef19488832897e0d5d9f7bb0d735af9",
    "whole_sha256": "1bc8d1107edcc33329aac2d5ff524f9ddc26a1e98fd1eb3486bfb438caff5a86",
    "interface_sha256": "7a3699a10686d022f30a5b40aac40f164b022bc7203508f875949f8f5c87cf31",
    "cross_count": 2,
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
    dynamic_render = program.key == RENDER_3D_KEY and profile == RENDER_DYNAMIC_PROFILE
    if profile != PROFILE and not dynamic_render:
        raise ValueError(f"{PROFILE}: exact profile carrier required")
    if program.key not in CROSS_KEYS:
        raise ValueError(f"{PROFILE}: program key {program.key} not in {CROSS_KEYS}")
    expected = _RENDER_DYNAMIC_PROFILE if dynamic_render else _PROFILES[program.key]
    if source_hash != expected["raw_sha256"]:
        raise ValueError(f"{PROFILE}: {program.key} caller source hash mismatch")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if dynamic_render and tuple((item.name, item.kind, item.canonical_value)
                                for item in program.preprocessor_defines) != (
                                    ("FILTERING", "str", "int"),
                                    ("INVERT", "str", "bool")):
        raise ValueError(f"{RENDER_DYNAMIC_PROFILE}: runtime define identity mismatch")
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
