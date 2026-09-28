"""Proof profile for the authenticated DLA agent bit-ingress closure.

Authenticates the exact bit-reinterpretation builtin call sites for the one
pending program whose first blocker is the missing ``uintBitsToFloat``
overload:

- points/dla:agent -- three ``uintBitsToFloat(uint) -> float`` sites
  (45:12, 48:12, 104:12) plus the two ``floatBitsToUint(float) -> uint``
  sites (43:17, 103:48) of the same float-seed bit-cast closure.

``floatBitsToUint`` alone would only swap the first diagnostic for its
inverse, so the closure is admitted as one unit: both directions lower to
the existing exact bit-cast helpers ``noisemaker::float_bits_to_uint`` /
``noisemaker::uint_bits_to_float`` in ``include/noisemaker/numeric.hpp``,
which are ``std::bit_cast`` transcriptions of the pinned CPU authority's
``src/csl/glsl-runtime.js`` ``floatBitsToUint``/``uintBitsToFloat``
(Float32Array/Uint32Array view ping-pong over the same four bytes).

Admission is by object identity of the exact call sites, keyed by the
program's raw/normalized source SHA-256 and whole-IR digests, and is
fail-closed: forged, extra, or missing sites abort. No global capability
gate is opened; the frozen vocabulary is unchanged.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "dla-bit-ingress-admission-v1"

DLA_AGENT_KEY = "points/dla:agent"

DLA_KEYS = frozenset({DLA_AGENT_KEY})

_PIN = {
    "raw_bytes": 5928,
    "raw_sha256": "5f11d2d5096ac4f54b243a2e9de1d7526960be76c460314f8ec7142c21c9995a",
    "norm_bytes": 4464,
    "norm_sha256": "10230df7fdf7fe5a02b8a62f410d28e2606a12d175741c25ec1f746e3ed35b8e",
    "functions_sha256": "bf3bc64bed802a11e5676f0c4310a39a604f68edd20c3aa73eee83e4b7fecdfd",
    "whole_sha256": "d56645842caf80c89c5a4b89feaaf2ce03c4fe52e2ec5dfc7e6c31bd82ed6b97",
    "interface_sha256": "28db1449b3e1ae28184383f5649b1cca9dd5aab5ecc40467ccafb03863cc55a9",
}

# Exactly the five authenticated call sites, in program-walk order (main's
# statement list precedes rand's; each list is in source order). Each row is
# (callee, span, result type, node sha, parent kind, parent operator,
#  child type tuple, child sha tuple, ancestor-chain kind/span tuple).
# Nothing outside this tuple may be lowered.
_NODES = (
    ("floatBitsToUint", "103:48-103:69", "uint",
     "7f4184a9b9ec3ab6533cec9af8b555ae49f199ad7fd80dcfd2f9a0934bfa026a",
     "binary", "+", ("float",),
     ("2cd011953f78ae49bebc5b673ad1b4a2560f4d43c3b1a0fec7dc3789a3c99600",),
     (("decl", "103:5-103:71"),)),
    ("uintBitsToFloat", "104:12-104:68", "float",
     "652e2a449d171e9ba6f25b8810c6e653fbbd5b77c9d2a76c24a68c2165826c61",
     "binary", "-", ("uint",),
     ("e040f65668deae4562552773e2e94714706a6c15f2aa1afc314fa6f84b9494fc",),
     (("expr", "104:5-104:75"),)),
    ("floatBitsToUint", "43:17-43:38", "uint",
     "01e23c7c726114f007af2a45cee993e16c42d18de206161e09feb8014d4593c7",
     "declaration", None, ("float",),
     ("89a067f227c6988e38335011bfd5e63c876ea7646f26608f3275e5615cb28d48",),
     (("decl", "43:5-43:39"),)),
    ("uintBitsToFloat", "45:12-45:47", "float",
     "c1b516cce7026744b603184b1431f1ed25b5bae5e6abde51fdd2ea754c8bd5f3",
     "binary", "-", ("uint",),
     ("4f37cc3f609fea56baae3e38e68a5cd22afef8600d4531334844bb38124e1105",),
     (("expr", "45:5-45:54"),)),
    ("uintBitsToFloat", "48:12-48:63", "float",
     "ee1b2dec3648b0f5e41276c4471d7f51662e23ebb3b969f044ac279794a643f7",
     "binary", "-", ("uint",),
     ("c538c1466bd7ed81c63a4d5ed54597949fb2aeebdcca2e5b41dba8ce1aca15ab",),
     (("expr", "48:5-48:70"),)),
)


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


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _walk_expression(value: TypedExpression):
    yield value
    for child in getattr(value, "children", ()):
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item in _walk_expression(expression):
            yield item, (*path, f"e{index}"), chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def authenticate_dla_bit_ingress_sites(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate every DLA bit-ingress site and return the exact AST nodes."""
    if profile != PROFILE:
        raise ValueError(f"{PROFILE}: exact profile carrier required")
    if program.key not in DLA_KEYS:
        raise ValueError(f"{PROFILE}: program key {program.key} not in {DLA_KEYS}")
    if source_hash != _PIN["raw_sha256"]:
        raise ValueError(f"{PROFILE}: {program.key} caller source hash mismatch")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if (len(raw) != _PIN["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != _PIN["raw_sha256"]
            or len(normalized) != _PIN["norm_bytes"]
            or hashlib.sha256(normalized).hexdigest() != _PIN["norm_sha256"]
            or defines != ()
            or program.body_status != "analyzed"
            or program.structs != () or program.uniform_blocks != ()
            or _sha(program.functions) != _PIN["functions_sha256"]
            or _whole(program) != _PIN["whole_sha256"]
            or _interface(program) != _PIN["interface_sha256"]):
        raise ValueError(
            f"{PROFILE}: {program.key} source, function, whole-program, "
            "or interface mismatch")

    if any(getattr(program, field, None) is not None
           for field in ("fixed_nine_table_proof", "fixed_grid_counter_store_proof",
                         "fixed_array_in_parameter_proof",
                         "fixed_affine_centers13_proof")):
        raise ValueError(f"{PROFILE}: {program.key} unrelated proof carrier is not absent")

    proof = program.counted_loop_proof
    if (proof is None
            or (proof.loop_count, proof.unproved_loop_count,
                proof.max_effective_depth, proof.max_lexical_product,
                proof.entrypoint_charge, proof.call_graph_acyclic)
            != (0, 0, 0, 0, 0, True)):
        raise ValueError(f"{PROFILE}: {program.key} loop or call graph profile mismatch")

    if (program.resources.uniforms, program.resources.samplers,
            program.resources.outputs, program.resources.uses_texture,
            program.resources.uses_derivatives) != (
            ("resolution", "time", "frame", "stride", "inputWeight",
             "attrition", "stateSize", "resetState", "xyzTex", "velTex",
             "rgbaTex", "gridTex", "inputTex"),
            ("xyzTex", "velTex", "rgbaTex", "gridTex", "inputTex"),
            ("outXYZ", "outVel", "outRGBA"), True, False):
        raise ValueError(f"{PROFILE}: {program.key} resource or binding signature mismatch")

    function_ids = tuple(item.id for item in program.functions)
    if function_ids != (25, 26, 27, 28, 29, 30, 31, 32):
        raise ValueError(f"{PROFILE}: {program.key} function cardinality mismatch")

    # Census the WHOLE program: any bit-ingress site outside the frozen table
    # (or any of the two callees shaped differently) is a hard failure.
    located: list[tuple[TypedExpression, tuple[object, ...],
                        tuple[TypedStatement, ...]]] = []
    for item, path, chain, (parent_kind, parent_operator) in _with_parents(program):
        if item.kind == "builtin" and item.callee in (
                "floatBitsToUint", "uintBitsToFloat"):
            if (item.type.display() != ("uint" if item.callee == "floatBitsToUint"
                                        else "float")
                    or len(item.children) != 1
                    or item.children[0].type.display() != (
                        "float" if item.callee == "floatBitsToUint" else "uint")):
                raise ValueError(f"{PROFILE}: {program.key} malformed bit-ingress site")
            located.append((item, path, chain))

    if len(located) != len(_NODES):
        raise ValueError(
            f"{PROFILE}: {program.key} expected {len(_NODES)} bit-ingress sites, "
            f"found {len(located)}")

    actual = tuple(
        (item.callee, _span(item), item.type.display(), _sha(item), parent_kind,
         parent_operator, tuple(child.type.display() for child in item.children),
         tuple(_sha(child) for child in item.children),
         tuple((statement.kind, _span(statement)) for statement in chain))
        for item, _, chain, (parent_kind, parent_operator) in _with_parents(program)
        if item.kind == "builtin" and item.callee in (
            "floatBitsToUint", "uintBitsToFloat"))
    if actual != _NODES:
        raise ValueError(f"{PROFILE}: {program.key} closure node identity mismatch")

    return tuple(item for item, _, _ in located)


def _with_parents(program: TypedProgram):
    """Yield (node, path, chain, parent kind, parent operator) in walk order."""

    def walk_expression(value: TypedExpression, parent: TypedExpression | None,
                        path: tuple[object, ...]):
        yield value, parent, path
        for index, child in enumerate(value.children):
            yield from walk_expression(child, value, (*path, index))

    def walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                       ancestors: tuple[TypedStatement, ...] = ()):
        chain = (*ancestors, value)
        for index, expression in enumerate(value.expressions):
            for item, parent, epath in walk_expression(expression, None,
                                                       (*path, f"e{index}")):
                yield item, epath, chain, (
                    None if parent is None else parent.kind,
                    None if parent is None else getattr(parent, "operator", None))
        for index, child in enumerate(value.children):
            yield from walk_statement(child, (*path, f"s{index}"), chain)

    for function in program.functions:
        for index, statement in enumerate(function.body):
            yield from walk_statement(statement, (index,))


def apply_dla_bit_ingress_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Validate profile and return program untouched (identity carrier)."""
    authenticate_dla_bit_ingress_sites(program, source_hash, profile)
    return program
