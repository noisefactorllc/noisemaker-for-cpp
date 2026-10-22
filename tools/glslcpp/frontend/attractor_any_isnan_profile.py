"""Exact ``any(isnan(vec3))`` closure profile for the Attractor agent.

This module does not add a general boolean-vector, NaN-test, or reduction
capability. It authenticates the one corpus program whose single
``any(isnan(newPos))`` tree may be lowered, and returns the candidate-owned
IR objects consumed independently by the validator and the emitter -- the
same node-identity pattern used by Waves' ``any(notEqual(vec2, vec2))``
closure (``waves_any_notequal_profile.py``) and Extrude's
``all(lessThanEqual(vec2, vec2))`` closure.

The ``bvec3`` intermediate produced by ``isnan`` is consumed immediately by
its exact parent ``any``. It is never declared, stored, returned,
subscripted, aggregated, or otherwise escaped, and this module proves that
rather than assuming it.

Deliberately independent of, and not mutually exclusive with, the
per-program loop/ingress profiles -- the Attractor agent carries none of
those today, and this module fails closed if one appears (the optional
proof-carrier absence check below).
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "attractor-isnan-any-admission-v1"
ATTRACTOR_KEY = "points/attractor:agent"

_RAW_BYTES = 6045
_RAW_SHA256 = "cfe98602348063ab7cb3aa0c642f70de000c2352a40368e8fc9eddcf47447e82"
_NORMALIZED_BYTES = 4962
_NORMALIZED_SHA256 = "40a92be211e8fdf13632733980068dc859f0537d5a6ea41e6f23a880a6da2b82"
_FUNCTIONS_SHA256 = "0fa03645f358ef1548d70d161d1de8a3537c9515b3ccc6192a03315c6687792b"
_WHOLE_SHA256 = "fdf7bfecf50c8e0bd9203bea3ade19426ff315b3d4468711a9891a90eb1f3477"
_INTERFACE_SHA256 = "67f852eea1830480136dcda6881990f5a10a467ba3a9d94f765515a2d9b0118d"

_MAIN_ID = 41
_DEFINES: tuple[tuple[str, str, str], ...] = ()
_LOOP_PROOF = (0, 0, 0, 0, 0, True)

# Exactly the two authenticated nodes, in source order. Each row is
# (callee, path, span, result type, node sha, parent kind, child type tuple,
#  child sha tuple). Nothing outside this tuple may be lowered.
_NODES = (
    ("any", (12, "e0", 0), "202:9-202:27", "bool",
     "156d140628c05eb0d6ba53d599cd9a8a14c0c2c5273f7ee61968d0da9fb0713d",
     "binary", ("bvec3",),
     ("078af5f75e50d01801324a9bc2cf2d8e3c88f8bf88289d69f9381551b04cbe71",)),
    ("isnan", (12, "e0", 0, 0), "202:13-202:26", "bvec3",
     "078af5f75e50d01801324a9bc2cf2d8e3c88f8bf88289d69f9381551b04cbe71",
     "builtin", ("vec3",),
     ("e98545f21687785126abc55c510e43a8a0e1f19f2e1e38b454c96a6a83eb3ce0",)),
)

_ANY_SIGNATURE_ID = -4
_ISNAN_SIGNATURE_ID = -54

# The closure lives at one statement: an `if` condition (divergence check
# `if (any(isnan(newPos)) || length(newPos) > 1000.0)`).
_ANCESTOR_KINDS = (("if",),)
_ANCESTOR_SPANS = (
    ("202:5-208:6",),
)

_PROFILE_SHA256 = "bc440ad2496401ba1cf81438f960836020885e1ddccdd71dbbd92ab218265bac"
_FROZEN_PROFILE_TUPLE_REPR = """('attractor-isnan-any-admission-v1', 'points/attractor:agent', 'cfe98602348063ab7cb3aa0c642f70de000c2352a40368e8fc9eddcf47447e82', (), 'glsl-f32', '0fa03645f358ef1548d70d161d1de8a3537c9515b3ccc6192a03315c6687792b', 'fdf7bfecf50c8e0bd9203bea3ade19426ff315b3d4468711a9891a90eb1f3477', '67f852eea1830480136dcda6881990f5a10a467ba3a9d94f765515a2d9b0118d', 41, (0, 0, 0, 0, 0, True), (('any', (12, 'e0', 0), '202:9-202:27', 'bool', '156d140628c05eb0d6ba53d599cd9a8a14c0c2c5273f7ee61968d0da9fb0713d', 'binary', ('bvec3',), ('078af5f75e50d01801324a9bc2cf2d8e3c88f8bf88289d69f9381551b04cbe71',)), ('isnan', (12, 'e0', 0, 0), '202:13-202:26', 'bvec3', '078af5f75e50d01801324a9bc2cf2d8e3c88f8bf88289d69f9381551b04cbe71', 'builtin', ('vec3',), ('e98545f21687785126abc55c510e43a8a0e1f19f2e1e38b454c96a6a83eb3ce0',))), (('202:5-208:6',),))"""

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class AttractorAnyIsnanProof:
    main: TypedFunction
    reduction: TypedExpression
    test: TypedExpression
    statement_chain: tuple[TypedStatement, ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [self.main, self.reduction, self.test,
                                *self.statement_chain]
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = ("PROFILE", "ATTRACTOR_KEY", "AttractorAnyIsnanProof",
           "authenticate_attractor_any_isnan_admission",
           "apply_attractor_any_isnan_admission",
           "is_authenticated_reduction_node", "is_authenticated_test_node")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


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


def _profile_tuple() -> tuple[object, ...]:
    value = ast.literal_eval(_FROZEN_PROFILE_TUPLE_REPR)
    if not isinstance(value, tuple):
        raise _fail("internal frozen profile tuple is not a tuple")
    return value


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, epath in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, epath, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def authenticate_attractor_any_isnan_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> AttractorAnyIsnanProof:
    """Authenticate the Attractor agent and return only candidate-owned objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != ATTRACTOR_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if (len(raw) != _RAW_BYTES or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or defines != _DEFINES
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")

    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    proof = program.counted_loop_proof
    if (proof is None or
            (proof.loop_count, proof.unproved_loop_count,
             proof.max_effective_depth, proof.max_lexical_product,
             proof.entrypoint_charge, proof.call_graph_acyclic) != _LOOP_PROOF):
        raise _fail("loop or call graph profile mismatch")

    if ((program.resources.uniforms, program.resources.samplers,
         program.resources.outputs, program.resources.uses_texture,
         program.resources.uses_derivatives)
            != (("time", "resolution", "seed", "attractor", "speed",
                 "xyzTex", "velTex", "rgbaTex", "diffuseTex", "diffuseActive",
                 "baseColorTex"),
                ("xyzTex", "velTex", "rgbaTex", "diffuseTex", "baseColorTex"),
                ("outXYZ", "outVel", "outRGBA", "outBaseColor"), True, False)):
        raise _fail("resource or binding signature mismatch")

    if len(program.functions) != 14:
        raise _fail("function cardinality mismatch")
    main = next((item for item in program.functions if item.id == _MAIN_ID), None)
    if (main is None
            or (main.name, main.return_type.display(), len(main.parameters),
                len(main.body), _span(main))
            != ("main", "void", 0, 18, "155:1-215:2")):
        raise _fail("main identity mismatch")

    # Census the WHOLE program: an extra any/isnan site anywhere else, or
    # any bvec-typed value that is not the single isnan result, is a hard
    # failure, not an unnoticed extra.
    located: list[tuple[str, tuple[object, ...], TypedExpression,
                        TypedExpression | None, tuple[TypedStatement, ...]]] = []
    bvec_nodes: list[TypedExpression] = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                display = None if item.type is None else item.type.display()
                if display is not None and display.startswith("bvec"):
                    bvec_nodes.append(item)
                if item.kind == "builtin" and item.callee in ("any", "isnan"):
                    if function.id != _MAIN_ID:
                        raise _fail("closure site outside main")
                    located.append((item.callee, path, item, parent, chain))

    if len(located) != len(_NODES):
        raise _fail(f"closure site cardinality mismatch: {len(located)}")

    actual = tuple(
        (callee, path, _span(item),
         "" if item.type is None else item.type.display(), _sha(item),
         "None" if parent is None else parent.kind,
         tuple("" if child.type is None else child.type.display()
               for child in item.children),
         tuple(_sha(child) for child in item.children))
        for callee, path, item, parent, _ in located)
    if actual != _NODES:
        raise _fail("closure node identity mismatch")

    for callee, path, item, parent, chain in located:
        expected_signature = (_ANY_SIGNATURE_ID if callee == "any"
                              else _ISNAN_SIGNATURE_ID)
        if item.signature_id != expected_signature:
            raise _fail("closure node signature mismatch")

    test = next(item for callee, _, item, _, _ in located if callee == "isnan")
    reduction = next(item for callee, _, item, _, _ in located if callee == "any")
    if len(bvec_nodes) != 1 or bvec_nodes[0] is not test:
        raise _fail("bvec3 value escapes its immediate reduction")

    # The reduction consumes exactly one child, and that child is exactly the
    # isnan object (identity, not equality).
    if (len(reduction.children) != 1
            or reduction.children[0] is not test):
        raise _fail("reduction does not immediately consume its test")
    if len(test.children) != 1:
        raise _fail("isnan arity mismatch")
    if (test.children[0].type is None
            or test.children[0].type.display() != "vec3"):
        raise _fail("isnan operand type mismatch")

    # The reduction's parent is the exact binary `||` of the divergence
    # check, and its single ancestor statement is the pinned `if`.
    chain = next(chain for callee, _, _, _, chain in located if callee == "any")
    chain_kinds = tuple(item.kind for item in chain)
    chain_spans = tuple(_span(item) for item in chain)
    if chain_kinds != _ANCESTOR_KINDS[0] or chain_spans != _ANCESTOR_SPANS[0]:
        raise _fail("closure ancestry mismatch")

    result = AttractorAnyIsnanProof(main, reduction, test, chain)
    # main, the reduction, the test, and the single enclosing if statement.
    if len(result.consumed_objects) != 4:
        raise _fail(
            f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def apply_attractor_any_isnan_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_attractor_any_isnan_admission(program, source_hash, profile)
    return program


def is_authenticated_reduction_node(
        proof: AttractorAnyIsnanProof, node: TypedExpression) -> bool:
    """True only for the exact authenticated ``any`` object."""
    return node is proof.reduction


def is_authenticated_test_node(
        proof: AttractorAnyIsnanProof, node: TypedExpression) -> bool:
    """True only for the exact authenticated ``isnan`` object."""
    return node is proof.test
