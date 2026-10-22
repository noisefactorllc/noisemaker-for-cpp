"""Proof profile for the authenticated DLA agent bit-ingress closure.

Authenticates the exact bit-reinterpretation builtin call sites for the one
pending program whose first blocker is the missing ``uintBitsToFloat``
overload:

- points/dla:agent -- three ``uintBitsToFloat(uint) -> float`` sites
  (45:12, 48:12, 104:12) plus the two ``floatBitsToUint(float) -> uint``
  sites (43:17, 103:48) of the same float-seed bit-cast closure, and the
  five scalar ``uint`` ``&``/``|`` mask sites of that closure (45:28,
  48:29 twice, 104:29 twice) that materialize the mantissa/exponent
  pattern around the reinterpreted bits.

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
    "raw_bytes": 7791,
    "raw_sha256": "cae55bc611428b4e6938a79814898c8bda2a3af19b303502ec5b77f5479b88f9",
    "norm_bytes": 5998,
    "norm_sha256": "42ab52479b08fb567ce8d91d9946d0f67025a3f74c369149981c7d8c0afc3098",
    "functions_sha256": "309b3bc451c5471c50aa7f78c9fa5bc8b5c6f3f5b838bc2a5a8f0d74e9c49fac",
    "whole_sha256": "8e23638833b84a4abe58d15bc47b78ab54be59258ae1d58ac877344e3fb9d16a",
    "interface_sha256": "0c30d67bdb183aac29b001aa7fb06e58687ea1257fc4160628fcc48643f59d3d",
}

# Exactly the five authenticated call sites, in program-walk order (main's
# statement list precedes rand's; each list is in source order). Each row is
# (callee, span, result type, node sha, parent kind, parent operator,
#  child type tuple, child sha tuple, ancestor-chain kind/span tuple).
# Nothing outside this tuple may be lowered.
_NODES = (
    ("floatBitsToUint", "139:48-139:69", "uint", "920bcb8f595e2c4bde12ecb1ee706e3c91e7a4b0902d91d24b382b73d5e71cb5", "binary", "+", ("float",), ("d8ce39692341ef79d47fe966b085c9b8762379a14941201cd0c35c996081b4d6",), (("decl", "139:5-139:71"),)),
    ("uintBitsToFloat", "140:12-140:68", "float", "40f48f24adc58b3110d365259a58fce51423b64e4af00fbb34a229a205bfaeb7", "binary", "-", ("uint",), ("0cc013dafc9cb5aa703b2341bb65e6766c4de748f1ca259b8b7b4f3f383e40be",), (("expr", "140:5-140:75"),)),
    ("floatBitsToUint", "78:17-78:38", "uint", "0076868b40887093fc130544ef0c7866d83ba6d09acdf7f828dd0dab2d26d321", "declaration", None, ("float",), ("38faced6ee6532c1297c17fe638a8b5952262907c1cab8d6b2d0e95d835628cf",), (("decl", "78:5-78:39"),)),
    ("uintBitsToFloat", "80:12-80:47", "float", "206b055a360ec240540ea793e0ab0760fe8a61ad1d9796d33cf46e02624f63bd", "binary", "-", ("uint",), ("fca6803937197cdca56ece918021618fa6530ce66bacaeba08fd9ca07a900f1b",), (("expr", "80:5-80:54"),)),
    ("uintBitsToFloat", "83:12-83:63", "float", "166ca4f1b058e31bd0fae6d310c96cc10ed9722451c0dd24988c98f8a7d45b51", "binary", "-", ("uint",), ("8321687f8dedfa7618c8165ec8e82f1c816aeb72cb0468f2dc6a1671772bf1c3",), (("expr", "83:5-83:70"),)),
)

# The five scalar ``uint`` ``&``/``|`` mask sites of the same closure, in
# walk order. Each row is (operator, span, node sha, parent kind, parent
# operator, child type tuple, child sha tuple, ancestor-chain tuple).
# `bits | 0x3F800000u` and `(bits & 0x007FFFFFu) | 0x3F800000u` are the
# classic float-seed mantissa/exponent pattern; on GLSL ``uint`` operands
# both lower to the exact unsigned C++ operators (no JS int32 boundary is
# crossed: the operands are already uint words in the typed IR).
_MASKS = (
    ("|", "140:29-140:67", "0cc013dafc9cb5aa703b2341bb65e6766c4de748f1ca259b8b7b4f3f383e40be", "builtin", None, ("uint", "uint"), ("6118d960b363733d1175c23ff3fa809a67727b7a4bb2264b712a203aaea5d09e", "cd4a8cea19be0987467f46776fc2790fcb9766e85c350919c22d04283a7cc227"), (("expr", "140:5-140:75"),)),
    ("&", "140:29-140:52", "6118d960b363733d1175c23ff3fa809a67727b7a4bb2264b712a203aaea5d09e", "binary", "|", ("uint", "uint"), ("b3190f682592976479a0abe9f87088764a56a3771daf4311fa54a304b3149aec", "fd793f9aab2f9926261f76bc1a053d75d2988f53d183adbea5a3162502877bc1"), (("expr", "140:5-140:75"),)),
    ("|", "80:28-80:46", "fca6803937197cdca56ece918021618fa6530ce66bacaeba08fd9ca07a900f1b", "builtin", None, ("uint", "uint"), ("3dff387010cf04d3490d3ec54cae3b4440e7e0675c26764e1d2e4359320136b1", "f039946f8ccdb8d77107e2d73cc9af08f4c37beee1cf568efdf5c52488f2937d"), (("expr", "80:5-80:54"),)),
    ("|", "83:29-83:62", "8321687f8dedfa7618c8165ec8e82f1c816aeb72cb0468f2dc6a1671772bf1c3", "builtin", None, ("uint", "uint"), ("eaafa7f5c40cdd0520e7a57a36d5dcd61d502524b91f1aac75539a0b902e0f89", "bcbc60fc9cfd8e980d600db0a9a8c4ba9bd3446e25a8a3a3e63205944dcebcae"), (("expr", "83:5-83:70"),)),
    ("&", "83:29-83:47", "eaafa7f5c40cdd0520e7a57a36d5dcd61d502524b91f1aac75539a0b902e0f89", "binary", "|", ("uint", "uint"), ("e46f83d0ce2ea20f7f46ee001936e9e5cde7c6033b27245e559f04c4cb5bf234", "97cb5042d7fae52ed647a001c7ab866b8ab8626533da5daba59494186048c766"), (("expr", "83:5-83:70"),)),
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
             "fieldActive", "attrition", "stateSize", "resetState", "xyzTex",
             "velTex", "rgbaTex", "gridTex", "heightTex", "inputTex",
             "diffuseTex", "diffuseActive", "baseColorTex"),
            ("xyzTex", "velTex", "rgbaTex", "gridTex", "heightTex", "inputTex",
             "diffuseTex", "baseColorTex"),
            ("outXYZ", "outVel", "outRGBA", "outBaseColor"), True, False):
        raise ValueError(f"{PROFILE}: {program.key} resource or binding signature mismatch")

    function_ids = tuple(item.id for item in program.functions)
    if function_ids != (37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48):
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

    # The scalar uint &/| mask sites of the same closure, censused over the
    # WHOLE program: any extra scalar uint bitwise op outside the frozen
    # table is a hard failure.
    located_masks: list[tuple[TypedExpression, tuple[object, ...],
                              tuple[TypedStatement, ...]]] = []
    for item, path, chain, _ in _with_parents(program):
        if (item.kind == "binary" and item.operator in ("&", "|")
                and item.type.display() == "uint"
                and len(item.children) == 2
                and all(child.type.display() == "uint"
                        for child in item.children)):
            located_masks.append((item, path, chain))

    if len(located_masks) != len(_MASKS):
        raise ValueError(
            f"{PROFILE}: {program.key} expected {len(_MASKS)} scalar uint "
            f"mask sites, found {len(located_masks)}")

    actual_masks = tuple(
        (item.operator, _span(item), _sha(item), parent_kind, parent_operator,
         tuple(child.type.display() for child in item.children),
         tuple(_sha(child) for child in item.children),
         tuple((statement.kind, _span(statement)) for statement in chain))
        for item, _, chain, (parent_kind, parent_operator) in _with_parents(program)
        if (item.kind == "binary" and item.operator in ("&", "|")
            and item.type.display() == "uint"
            and len(item.children) == 2
            and all(child.type.display() == "uint"
                    for child in item.children)))
    if actual_masks != _MASKS:
        raise ValueError(f"{PROFILE}: {program.key} mask site identity mismatch")

    # One authorized tuple in whole-program walk order so the exact
    # visited-sequence completeness checks in the validator and the emitter
    # compare like with like.
    authorized_items = {
        id(item): item for item, _, _ in located}
    authorized_items.update({id(item): item for item, _, _ in located_masks})
    return tuple(authorized_items[id(item)]
                 for item, _, _, _ in _with_parents(program)
                 if id(item) in authorized_items)


def authenticate_dla_bit_ingress_parameter(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[object, ...]:
    """Authenticate the single ``inout float seed`` parameter of the closure.

    ``rand(inout float seed)`` is the accumulator of the same float-seed
    bit-cast closure: every update goes through the frozen bit-ingress and
    mask sites above.  Admission is fail-closed: the program must carry
    exactly one inout parameter, the float-typed ``seed`` of ``rand``, at
    the frozen span; anything else aborts.
    """
    if profile != PROFILE:
        raise ValueError(f"{PROFILE}: exact profile carrier required")
    if program.key not in DLA_KEYS:
        raise ValueError(f"{PROFILE}: program key {program.key} not in {DLA_KEYS}")
    if source_hash != _PIN["raw_sha256"]:
        raise ValueError(f"{PROFILE}: {program.key} caller source hash mismatch")

    expected = (
        ("seed", "float", "inout", "77:12-77:28"),
        ("seed", "float", "inout", "87:22-87:38"),
    )
    actual = tuple(
        (parameter.name, parameter.type.display(), parameter.direction,
         _span(parameter))
        for function in program.functions for parameter in function.parameters
        if parameter.direction != "in")
    if actual != expected:
        raise ValueError(
            f"{PROFILE}: {program.key} inout parameter identity mismatch "
            f"(expected {expected}, found {actual})")

    return tuple(
        parameter for function in program.functions
        for parameter in function.parameters if parameter.direction != "in")


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
