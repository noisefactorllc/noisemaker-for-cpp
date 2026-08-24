"""Exact float-bit-ingress and scalar word-XOR closure profile for Caustic.

This module does not add a general bit-reinterpretation or scalar bitwise
capability.  It authenticates the one corpus program whose lattice hash may
reinterpret a float's bits and mix three scalar ``uint`` words, and returns the
candidate-owned IR objects consumed independently by the validator and the
emitter.

Unlike Perlin's scalar XOR closure (Task 27), Caustic's XORs are live,
reachable, rendered code: their results reach ``fragColor``.  Native fixtures
must therefore prove real values, not merely that the program compiles.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "caustic-float-bits-scalar-word-hash-v1"
CAUSTIC_KEY = "classicNoisedeck/caustic:caustic"

_RAW_BYTES = 15645
_RAW_SHA256 = "161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d"
_NORMALIZED_BYTES = 7999
_NORMALIZED_SHA256 = "b4a45216e62c5facade77e64925075e736ee3ed0eb7b1798bc777ba1bb714b83"
_FUNCTIONS_SHA256 = "43a0063cf16ebea820084302df1d6c59594485b559267597ad30ac3cddc659a3"
_WHOLE_SHA256 = "b0ffb30caee0d301f54d42892a6e70619fd4cf1e4c19d5fc3f399b3bfc598624"
_INTERFACE_SHA256 = "094c31b573c08cfdf9e3c76e766c4b4ca96a2df12d6a1629f18b141624464b50"

_HOST_ID = 94
_HOST_NAME = "randomFromLatticeWithOffset"
_HOST_SPAN = "164:1-208:2"
_DEFINES = (("NOISE_TYPE", "int", "10"),)
_LOOP_PROOF = (0, 0, 0, 0, 0, True)

# Exactly the four authenticated nodes, in source order. Each row is
# (kind, path, span, result type, node sha, parent kind, child type tuple,
#  child sha tuple). Nothing outside this tuple may be lowered.
#
# The `uvec3 ^ uvec3` at 200:19 is deliberately ABSENT: it is already admitted
# by the pre-existing `uint-vector-bitwise` capability and is not part of this
# closure.
_NODES = (
    ("floatBitsToUint", (13, "e0", 0), "192:21-192:46", "uint",
     "e6b86baf243b38741b4870acfe990ce3b353f18948d38773cc853ab11ce3b6a4",
     "declaration", ("float",),
     ("4c2cc94f5d6f93142124122d1f36a2aa7560bdc88512eb7f27370783eb78dbac",)),
    ("^", (14, "e0", 0, 0), "195:10-195:46", "uint",
     "0ec45e30c890d1177375332f93564f8d12d8bd47805393740503edd290617445",
     "construct", ("uint", "uint"),
     ("2562f15164ab5b9481bb798dc74b9994417976020d5e6e9183421ecead9479a1",
      "4d5400d40220fb6418ef8c6d27997a72862ff40174c4487d8bcdfba8deefacb8")),
    ("^", (14, "e0", 0, 1), "196:10-196:46", "uint",
     "7f98e820b388d74eb98c8296f798d778d63d6bdb8d67e68f9bfae73f74e56e4e",
     "construct", ("uint", "uint"),
     ("b5d7903129b6eb87c8dc28a936ac1d7449031b684a895995a33f608f061bdfc8",
      "b30427f6ce552c15b34104bca4aa23b865ad0939898eb45d4ec5cdcb1545dfff")),
    ("^", (14, "e0", 0, 2), "197:10-197:47", "uint",
     "791b232712de5fe1a3babde2e00799603fbb523421973f9b20888f12e978b8ee",
     "construct", ("uint", "uint"),
     ("6d5b73a65a867110b99a54ab4fd21669eeffbbffe871830809a6cc374f9df688",
      "53bcacbea819782a268357731c1eb75d12b5019586f84dc7d33e163aef6ebcd6")),
)

_ANCESTOR_KINDS = ("decl",)
_INGRESS_ANCESTOR_SPAN = ("192:5-192:47",)
_XOR_ANCESTOR_SPAN = ("194:5-198:7",)

_PROFILE_SHA256 = "f97e506b0bd1a5b009e56809e33cfb1015e541a658dd4eff72388419f6244c80"
_FROZEN_PROFILE_TUPLE_REPR = """('caustic-float-bits-scalar-word-hash-v1', 'classicNoisedeck/caustic:caustic', '161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d', (('NOISE_TYPE', 'int', '10'),), 'glsl-f32', '43a0063cf16ebea820084302df1d6c59594485b559267597ad30ac3cddc659a3', 'b0ffb30caee0d301f54d42892a6e70619fd4cf1e4c19d5fc3f399b3bfc598624', '094c31b573c08cfdf9e3c76e766c4b4ca96a2df12d6a1629f18b141624464b50', 94, (0, 0, 0, 0, 0, True), (('floatBitsToUint', (13, 'e0', 0), '192:21-192:46', 'uint', 'e6b86baf243b38741b4870acfe990ce3b353f18948d38773cc853ab11ce3b6a4', 'declaration', ('float',), ('4c2cc94f5d6f93142124122d1f36a2aa7560bdc88512eb7f27370783eb78dbac',)), ('^', (14, 'e0', 0, 0), '195:10-195:46', 'uint', '0ec45e30c890d1177375332f93564f8d12d8bd47805393740503edd290617445', 'construct', ('uint', 'uint'), ('2562f15164ab5b9481bb798dc74b9994417976020d5e6e9183421ecead9479a1', '4d5400d40220fb6418ef8c6d27997a72862ff40174c4487d8bcdfba8deefacb8')), ('^', (14, 'e0', 0, 1), '196:10-196:46', 'uint', '7f98e820b388d74eb98c8296f798d778d63d6bdb8d67e68f9bfae73f74e56e4e', 'construct', ('uint', 'uint'), ('b5d7903129b6eb87c8dc28a936ac1d7449031b684a895995a33f608f061bdfc8', 'b30427f6ce552c15b34104bca4aa23b865ad0939898eb45d4ec5cdcb1545dfff')), ('^', (14, 'e0', 0, 2), '197:10-197:47', 'uint', '791b232712de5fe1a3babde2e00799603fbb523421973f9b20888f12e978b8ee', 'construct', ('uint', 'uint'), ('6d5b73a65a867110b99a54ab4fd21669eeffbbffe871830809a6cc374f9df688', '53bcacbea819782a268357731c1eb75d12b5019586f84dc7d33e163aef6ebcd6'))))"""

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class CausticWordHashProof:
    host: TypedFunction
    ingress: TypedExpression
    word_xors: tuple[TypedExpression, TypedExpression, TypedExpression]
    parents: tuple[TypedExpression, ...]
    statement_parent_chains: tuple[tuple[TypedStatement, ...], ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [self.host, self.ingress, *self.word_xors,
                                *self.parents]
        for chain in self.statement_parent_chains:
            values.extend(chain)
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = ("PROFILE", "CAUSTIC_KEY", "CausticWordHashProof",
           "authenticate_caustic_word_hash", "apply_caustic_word_hash")


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


def _is_closure_node(item: TypedExpression) -> bool:
    if item.kind == "builtin" and item.callee == "floatBitsToUint":
        return True
    return (item.kind == "binary" and item.operator == "^"
            and item.type is not None and item.type.display() == "uint")


def authenticate_caustic_word_hash(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> CausticWordHashProof:
    """Authenticate Caustic and return only candidate-owned exact objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != CAUSTIC_KEY or source_hash != _RAW_SHA256:
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
            != (("time", "seed", "wrap", "resolution", "tileOffset",
                 "fullResolution", "noiseScale", "speed", "hueRotation",
                 "hueRange", "intensity"),
                (), ("fragColor",), False, False)):
        raise _fail("resource or binding signature mismatch")

    if len(program.functions) != 22:
        raise _fail("function cardinality mismatch")
    host = next((item for item in program.functions if item.id == _HOST_ID), None)
    if (host is None
            or (host.name, host.return_type.display(), len(host.parameters),
                len(host.body), _span(host))
            != (_HOST_NAME, "vec3", 5, 19, _HOST_SPAN)):
        raise _fail("host function identity mismatch")

    # Census the WHOLE program, so an additional ingress or scalar word XOR
    # anywhere else is a hard failure rather than an unnoticed extra.
    located: list[tuple[str, tuple[object, ...], TypedExpression,
                        TypedExpression | None, tuple[TypedStatement, ...]]] = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                if _is_closure_node(item):
                    if function.id != _HOST_ID:
                        raise _fail("closure site outside the host function")
                    kind = ("floatBitsToUint" if item.kind == "builtin"
                            else "^")
                    located.append((kind, path, item, parent, chain))

    if len(located) != len(_NODES):
        raise _fail(f"closure site cardinality mismatch: {len(located)}")

    actual = tuple(
        (kind, path, _span(item),
         "" if item.type is None else item.type.display(), _sha(item),
         "" if parent is None else parent.kind,
         tuple("" if child.type is None else child.type.display()
               for child in item.children),
         tuple(_sha(child) for child in item.children))
        for kind, path, item, parent, _ in located)
    if actual != _NODES:
        raise _fail("closure node identity mismatch")

    ingress = tuple(item for kind, _, item, _, _ in located
                    if kind == "floatBitsToUint")
    word_xors = tuple(item for kind, _, item, _, _ in located if kind == "^")
    if len(ingress) != 1 or len(word_xors) != 3:
        raise _fail("ingress or word XOR cardinality mismatch")

    if len(ingress[0].children) != 1:
        raise _fail("ingress arity mismatch")
    for node in word_xors:
        if len(node.children) != 2:
            raise _fail("word XOR arity mismatch")
        if any(child.type is None or child.type.display() != "uint"
               for child in node.children):
            raise _fail("word XOR operand is not an exact scalar uint")

    parents = tuple(parent for _, _, _, parent, _ in located)
    if any(parent is None for parent in parents):
        raise _fail("closure parent mismatch")

    chains = tuple(chain for _, _, _, _, chain in located)
    if tuple(tuple(item.kind for item in chain)
             for chain in chains) != (_ANCESTOR_KINDS,) * 4:
        raise _fail("closure ancestry kind mismatch")
    spans = tuple(tuple(_span(item) for item in chain) for chain in chains)
    if (spans[0] != _INGRESS_ANCESTOR_SPAN
            or any(span != _XOR_ANCESTOR_SPAN for span in spans[1:])):
        raise _fail("closure ancestry span mismatch")

    result = CausticWordHashProof(host, ingress[0], word_xors, parents,
                                  (chains[0], chains[1]))
    # host, ingress, three word XORs, two unique parents (the ingress
    # declaration and the single uvec3 `construct` shared by all three XORs),
    # and two unique statements (one `decl` per closure).
    if len(result.consumed_objects) != 9:
        raise _fail(
            f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def apply_caustic_word_hash(program: TypedProgram, source_hash: str | None,
                            profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_caustic_word_hash(program, source_hash, profile)
    return program
