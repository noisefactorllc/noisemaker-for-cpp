"""Exact identity profile admitting ``inout vec3`` parameters for
``filter/watercolor:wcSimplify``'s ``sort2`` compare-exchange helper.

``wcSimplify`` implements the Devillard ``opt_med9`` 3x3 median network (the
same 19-op compare-exchange sequence ``filter/median``'s ``medianPass.glsl``
uses) via a single helper:

```glsl
void sort2(inout vec3 a, inout vec3 b) {
    vec3 lo = min(a, b);
    vec3 hi = max(a, b);
    a = lo;
    b = hi;
}
```

called 19 times from ``main()``, always with two plain local ``vec3``
variables as arguments (``sort2(p1, p2);`` etc). Parameter direction ``out``/
``inout`` has zero admission path anywhere in the generator today (unlike
``round``/``reflect``/the derivative trio, which are each admitted for
specific programs by node identity) -- this module follows that exact same
zero-vocabulary-growth, node-identity pattern. ``inout`` never joins
``APPROVED_CAPABILITIES`` (the frozen 44-entry vocabulary is untouched); only
these two specific parameters of this one function, in this one program, are
ever admitted.

Semantic analysis (``body_semantic.py:325``) already requires every argument
bound to an ``out``/``inout`` parameter to be an lvalue before the typed IR
even reaches this module, so every one of the 19 call sites' arguments is
already guaranteed to be an lvalue by construction. What this module adds is
the narrower guarantee the emitter actually needs: each argument is a bare
``id`` naming a *local* variable (never a member/swizzle/index target,
global, or parameter), which is exactly the shape that lowers soundly to a
plain C++ reference parameter (``glsl::Vec3&``) bound to the caller's local.

C++'s value-type ``glsl::Vec3`` makes reference-parameter mutation exactly
equivalent to GLSL's copy-in/copy-out ``inout`` semantics here: every call
site passes a *distinct* plain local (never the same expression twice, never
a parameter), so there is no possibility of the C++ reference binding
observing a copy-in/copy-out divergence that GLSL's semantics would produce
for aliased arguments.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .typed_ir import TypedExpression, TypedFunction, TypedProgram


PROFILE = "inout-vec3-swap-v1"
WATERCOLOR_KEY = "filter/watercolor:wcSimplify"

_RAW_BYTES = 2233
_RAW_SHA256 = "81e668d554920b70353a2cccaaa414f1ad4eebd83bd1d7100ca05f44a11f8b5c"
_NORMALIZED_BYTES = 1433
_NORMALIZED_SHA256 = "883c8412fc9ba83b6e01132a8b5d348956f4ce75f9e4ab9ae342d9782aff3c5c"
_FUNCTIONS_SHA256 = "f1a9e7fa0c90c11b0ecdee2ecbabf7cb90796f5e07233ea9bd85b92a9a7c885a"
_WHOLE_SHA256 = "9f43ebbc6042db7d30f336106215ce8842140f27ca3c46061f9394de216af2fb"
_INTERFACE_SHA256 = "12b0afcf3e6495444935f28b81ff083c9730b0d0cd8b6b66d46a927d577cf97d"

_SORT2_NAME = "sort2"
_SORT2_SIGNATURE_ID = 8
_SORT2_PARAM_IDS = (5, 6)
_SORT2_BODY_SHA256 = "0dd91bd5ecc98992202816e418de69512efe7150d70d4a7f2098979168e0842a"

# (host_function_name, host_signature_id, start_line, start_column, end_line,
#  end_column, (arg0_symbol_id, arg1_symbol_id), node_sha256) for all 19 real
# call sites, computed directly from the live tree -- never hand-derived.
_CALL_SITES = (
    ("main", 7, 37, 5, 37, 18, (23, 24), "229de33fb9b579ff1b96f0a050123a07aa764a2394bd3b568875f0d92b9c0a8b"),
    ("main", 7, 37, 20, 37, 33, (26, 27), "e8413d8aa6d20079c72c6932d103fa8bb0c1faa34700af0c14fdc29ed26654f7"),
    ("main", 7, 37, 35, 37, 48, (29, 30), "f1c1fde2437ee4e7166601a67f1f7cf9e6efebd5b778c7858170639091843066"),
    ("main", 7, 38, 5, 38, 18, (22, 23), "da39c7479b799c503fc8cac9da831159d379285aeac9415582aad9ec1774e4fb"),
    ("main", 7, 38, 20, 38, 33, (25, 26), "bb4fac524bf77e605fa750dd91c4e42431cad84f17aec0e2b04d69bba3d9de89"),
    ("main", 7, 38, 35, 38, 48, (28, 29), "a94cf10cab4a218ff2d2ca189c3f28769ad5eea2df3aa386d67b030e7faa1319"),
    ("main", 7, 39, 5, 39, 18, (23, 24), "859721ebf035bedb0fd218fd824a82632e4bcbcf124ab470ace03bee4469e343"),
    ("main", 7, 39, 20, 39, 33, (26, 27), "1af11d10c999d573bce5bfe7896b4f6f4349f4c139dc5c1d5011e7d50b9132f9"),
    ("main", 7, 39, 35, 39, 48, (29, 30), "08567a2a9bde08cd79fb2abc4e22b1e381e5e82c67a205a838c2fe1b6cbb5e30"),
    ("main", 7, 40, 5, 40, 18, (22, 25), "15ab2cba1d55b2f30298186d79508f748104e23e6310d688f71e948e19785f4d"),
    ("main", 7, 40, 20, 40, 33, (27, 30), "6750a459e8f8df19cc24c24b1353f58deab40a536581e4391cfd9eedbae7eb99"),
    ("main", 7, 40, 35, 40, 48, (26, 29), "da8e05933f8694bc61e4f325b6c2a8e8dcc6130de3bec301bc3b8adbd4ca5eee"),
    ("main", 7, 41, 5, 41, 18, (25, 28), "617807aa1817ac61c3fb6e6afbe2291dcb071efbef1c28f20211d3905c71fe4d"),
    ("main", 7, 41, 20, 41, 33, (23, 26), "02e686919800c0d18715920d96f4bdfb70dbb4954883bf0bf476ae8d09d81a4d"),
    ("main", 7, 41, 35, 41, 48, (24, 27), "a2e5d95a93204850980a980be623276d19e62c4d0b6f6cc819f79b6f4901387e"),
    ("main", 7, 42, 5, 42, 18, (26, 29), "02731c8cb4f8d3c4120272d648e47a6e0d1c1bbb31b7f2107e703ec2f3eaeb70"),
    ("main", 7, 42, 20, 42, 33, (26, 24), "efade36ac4934eda201766ddcf48dff75095c2176c9509cb3bc4f90d9bd011e2"),
    ("main", 7, 42, 35, 42, 48, (28, 26), "1e0c4228bfee8548edb6a9d57e3da5be292e5c4d981741394f23e283b2385074"),
    ("main", 7, 43, 5, 43, 18, (26, 24), "4d6b55fb93a61c9f67afd3dc125f2c9c21b02b9e970f97bc8b8e833963185271"),
)

__all__ = ("PROFILE", "WATERCOLOR_KEY", "InoutVec3SwapProof",
           "authenticate_inout_vec3_swap_admission",
           "apply_inout_vec3_swap_admission")


@dataclass(frozen=True, slots=True)
class InoutVec3SwapProof:
    function: TypedFunction
    parameters: tuple[object, ...]
    calls: tuple[TypedExpression, ...]


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


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


def _walk_statement(statement, results: list) -> None:
    for expression in statement.expressions:
        _walk_expression(expression, results)
    for child in statement.children:
        _walk_statement(child, results)


def _walk_expression(value: TypedExpression, results: list) -> None:
    results.append(value)
    for child in value.children:
        _walk_expression(child, results)


def authenticate_inout_vec3_swap_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> InoutVec3SwapProof:
    """Authenticate and return the exact frozen ``sort2``/call-site identity."""
    if program.key != WATERCOLOR_KEY:
        raise _fail("selected key is not Watercolor wcSimplify")
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if source_hash != _RAW_SHA256:
        raise _fail("exact caller source digest required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole_fingerprint(program) != _WHOLE_SHA256
            or _interface_fingerprint(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")

    sort2 = next((fn for fn in program.functions if fn.name == _SORT2_NAME), None)
    if (sort2 is None or sort2.signature.id != _SORT2_SIGNATURE_ID
            or sort2.return_type.display() != "void"
            or tuple(p.id for p in sort2.parameters) != _SORT2_PARAM_IDS
            or len(sort2.parameters) != 2
            or any(p.type.display() != "vec3" for p in sort2.parameters)
            or any(p.direction != "inout" for p in sort2.parameters)
            or any(not p.writable for p in sort2.parameters)
            or _sha(sort2.body) != _SORT2_BODY_SHA256):
        raise _fail("sort2 function identity mismatch")

    census: list[tuple[str, int, TypedExpression]] = []
    for function in program.functions:
        results: list[TypedExpression] = []
        for statement in function.body:
            _walk_statement(statement, results)
        for node in results:
            if node.kind == "call" and node.signature_id == sort2.signature.id:
                census.append((function.name, function.signature.id, node))

    if len(census) != len(_CALL_SITES):
        raise _fail("sort2 call-site cardinality mismatch")

    calls: list[TypedExpression] = []
    remaining = list(_CALL_SITES)
    for function_name, function_id, node in census:
        span = node.span
        arg_ids = tuple(child.symbol_id for child in node.children)
        fingerprint = (function_name, function_id, span.start_line, span.start_column,
                      span.end_line, span.end_column, arg_ids, _sha(node))
        if fingerprint not in remaining:
            raise _fail("sort2 call-site node profile mismatch")
        remaining.remove(fingerprint)
        if (len(node.children) != 2
                or any(child.kind != "id" for child in node.children)
                or any(child.category != "lvalue" for child in node.children)
                or any(getattr(child.symbol, "storage", None) != "local"
                       for child in node.children)
                or any(child.type.display() != "vec3" for child in node.children)
                or node.children[0].symbol_id == node.children[1].symbol_id):
            raise _fail("sort2 call-site argument shape mismatch")
        calls.append(node)
    if remaining:
        raise _fail("sort2 call-site node profile mismatch")

    return InoutVec3SwapProof(
        function=sort2, parameters=tuple(sort2.parameters), calls=tuple(calls))


def apply_inout_vec3_swap_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate this frozen identity profile without changing the tree."""
    authenticate_inout_vec3_swap_admission(program, source_hash, profile)
    return program
