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

_RAW_BYTES = 4936
_RAW_SHA256 = "5ec5c8c92dc026ca123c37cb735386c4bca9df0e2b2ebbd9831d3fbc32ac127e"
_NORMALIZED_BYTES = 4037
_NORMALIZED_SHA256 = "d6b8f3bdd40429533066d5a36851310e4fd2f12c4d5fbbfeef9e722e2b03c0aa"
_FUNCTIONS_SHA256 = "b48ff25068d3a828af049eb2877b9a7b78dba0fe01b064815fb2cd21aa108ec2"
_WHOLE_SHA256 = "01dbb7768fad041b71cd7f21da1edc1214fac2c0498af2b3ebf5ce6d2ee85c74"
_INTERFACE_SHA256 = "743337eb60a5726ea3f547181b79d65013ebd67850e3484f367fd73b1cebda61"

_MAIN_ID = 31
_DEFINES: tuple[tuple[str, str, str], ...] = ()
_LOOP_PROOF = (0, 0, 0, 0, 0, True)

# Exactly the two authenticated nodes, in source order. Each row is
# (callee, path, span, result type, node sha, parent kind, child type tuple,
#  child sha tuple). Nothing outside this tuple may be lowered.
_NODES = (
    ("any", (12, "e0", 0), "177:9-177:27", "bool",
     "bfa026ec85fcf4b20dcd6e72688dd1f9b99e0b849c6551f2bb163904d9f1b007",
     "binary", ("bvec3",),
     ("0b5f83c77dbd222b8359bb35ff78b14d6e873b1558aeed99c25736a95163ffa3",)),
    ("isnan", (12, "e0", 0, 0), "177:13-177:26", "bvec3",
     "0b5f83c77dbd222b8359bb35ff78b14d6e873b1558aeed99c25736a95163ffa3",
     "builtin", ("vec3",),
     ("4f6e28f38aa6b15d449e4ea25d95fb3d948333e5324a8533a1b10c17e1c7cecb",)),
)

_ANY_SIGNATURE_ID = -4
_ISNAN_SIGNATURE_ID = -54

# The closure lives at one statement: an `if` condition (divergence check
# `if (any(isnan(newPos)) || length(newPos) > 1000.0)`).
_ANCESTOR_KINDS = (("if",),)
_ANCESTOR_SPANS = (
    ("177:5-183:6",),
)

_PROFILE_SHA256 = "281ce06976160c9923bee389e61ab4ba3f2075d773d90bc983c4ffef03a910c8"
_FROZEN_PROFILE_TUPLE_REPR = """('attractor-isnan-any-admission-v1', 'points/attractor:agent', '5ec5c8c92dc026ca123c37cb735386c4bca9df0e2b2ebbd9831d3fbc32ac127e', (), 'glsl-f32', 'b48ff25068d3a828af049eb2877b9a7b78dba0fe01b064815fb2cd21aa108ec2', '01dbb7768fad041b71cd7f21da1edc1214fac2c0498af2b3ebf5ce6d2ee85c74', '743337eb60a5726ea3f547181b79d65013ebd67850e3484f367fd73b1cebda61', 31, (0, 0, 0, 0, 0, True), (('any', (12, 'e0', 0), '177:9-177:27', 'bool', 'bfa026ec85fcf4b20dcd6e72688dd1f9b99e0b849c6551f2bb163904d9f1b007', 'binary', ('bvec3',), ('0b5f83c77dbd222b8359bb35ff78b14d6e873b1558aeed99c25736a95163ffa3',)), ('isnan', (12, 'e0', 0, 0), '177:13-177:26', 'bvec3', '0b5f83c77dbd222b8359bb35ff78b14d6e873b1558aeed99c25736a95163ffa3', 'builtin', ('vec3',), ('4f6e28f38aa6b15d449e4ea25d95fb3d948333e5324a8533a1b10c17e1c7cecb',))), (('177:5-183:6',),))"""

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
                 "xyzTex", "velTex", "rgbaTex"),
                ("xyzTex", "velTex", "rgbaTex"),
                ("outXYZ", "outVel", "outRGBA"), True, False)):
        raise _fail("resource or binding signature mismatch")

    if len(program.functions) != 11:
        raise _fail("function cardinality mismatch")
    main = next((item for item in program.functions if item.id == _MAIN_ID), None)
    if (main is None
            or (main.name, main.return_type.display(), len(main.parameters),
                len(main.body), _span(main))
            != ("main", "void", 0, 16, "132:1-188:2")):
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
