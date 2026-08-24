"""Exact three-node float-bit ingress profile for Scanline Error.

This module does not add ``floatBitsToUint`` to the global builtin or
capability vocabulary.  It authenticates the frozen Scanline Error program
and returns only the candidate-owned typed-IR objects which the validator and
emitter must consume independently.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "scanline-error-float-bits-ingress-v1"
SCANLINE_ERROR_KEY = "filter/scanlineError:scanlineError"

_RAW_BYTES = 13302
_RAW_SHA256 = "66556b29659b479edd397f8e0c87c176cafa7560c426eab8211b6939a08f2198"
_NORMALIZED_BYTES = 12383
_NORMALIZED_SHA256 = "a3f9b6dc4c76e09f3379ff8b3dfea4e909b77b2084edb5fd6d6eb5146dd72a63"
_FUNCTIONS_SHA256 = "ed2047b18516f88701c44b45742561860b8dc62a56f463231c00823bd470cb0b"
_WHOLE_SHA256 = "9585ed49e2fe4c258ed23feb5b349421126101451b7264e9d65a44bf1027ef7a"
_INTERFACE_SHA256 = "c2e8b81ea371988159e842ddc32177268989b10776abbd2375d43b0182f2f35e"

_HOST_ID = 69
_HOST_NAME = "hashNoise"
_HOST_SPAN = "233:1-236:2"
_LOOP_PROOF = (0, 0, 0, 0, 0, True)
_NODES = (
    ("floatBitsToUint", (0, "e0", 0, 0), "234:24-234:44", "uint",
     "2402bf7aad304a4e6424e97c2617afa0554cd1cb2be13fa598b7064e42557ec6",
     "construct", ("float",),
     ("694c599fbc13e63691cb6db314cc05974ac044ca161fe2514441052e672735f5",)),
    ("floatBitsToUint", (0, "e0", 0, 1), "234:46-234:66", "uint",
     "d82ebb35ac2a24139851ec2bde1a92c8c6df4e0a7ba67acd6b2e53705e806436",
     "construct", ("float",),
     ("14eda8b6339c0ff91896b354074403e16175bb9876ef18ef8dbac65c4dc915eb",)),
    ("floatBitsToUint", (0, "e0", 0, 2), "234:68-234:88", "uint",
     "5ec80d658b993e6eca6ce0478da6d2ff2dd877b7d49178ce1231094d851a9552",
     "construct", ("float",),
     ("6bbdea87cfdfed567bbbb023d3a4d59e476c5b85698679b462eb76e219f8cdea",)),
)
_PARENT = (
    "construct", "234:18-234:89",
    "c7b80c2d12ff68b1c6d72ea84fcfc94cbc796f66c434d3b659bc16e1116a340a",
)
_STATEMENT_CHAIN = (("decl", "234:5-234:90"),)
_PROFILE_SHA256 = "713e5af0f0a2e8d55e872f5c15920474523d511118176ecfc801a7dd31e84773"
_FROZEN_PROFILE_TUPLE_REPR = """('scanline-error-float-bits-ingress-v1', 'filter/scanlineError:scanlineError', '66556b29659b479edd397f8e0c87c176cafa7560c426eab8211b6939a08f2198', (), 'glsl-f32', 'ed2047b18516f88701c44b45742561860b8dc62a56f463231c00823bd470cb0b', '9585ed49e2fe4c258ed23feb5b349421126101451b7264e9d65a44bf1027ef7a', 'c2e8b81ea371988159e842ddc32177268989b10776abbd2375d43b0182f2f35e', 69, (0, 0, 0, 0, 0, True), (('floatBitsToUint', (0, 'e0', 0, 0), '234:24-234:44', 'uint', '2402bf7aad304a4e6424e97c2617afa0554cd1cb2be13fa598b7064e42557ec6', 'construct', ('float',), ('694c599fbc13e63691cb6db314cc05974ac044ca161fe2514441052e672735f5',)), ('floatBitsToUint', (0, 'e0', 0, 1), '234:46-234:66', 'uint', 'd82ebb35ac2a24139851ec2bde1a92c8c6df4e0a7ba67acd6b2e53705e806436', 'construct', ('float',), ('14eda8b6339c0ff91896b354074403e16175bb9876ef18ef8dbac65c4dc915eb',)), ('floatBitsToUint', (0, 'e0', 0, 2), '234:68-234:88', 'uint', '5ec80d658b993e6eca6ce0478da6d2ff2dd877b7d49178ce1231094d851a9552', 'construct', ('float',), ('6bbdea87cfdfed567bbbb023d3a4d59e476c5b85698679b462eb76e219f8cdea',))), ('construct', '234:18-234:89', 'c7b80c2d12ff68b1c6d72ea84fcfc94cbc796f66c434d3b659bc16e1116a340a'), (('decl', '234:5-234:90'),))"""

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class ScanlineErrorFloatBitsIngressProof:
    host: TypedFunction
    ingresses: tuple[TypedExpression, TypedExpression, TypedExpression]
    parent: TypedExpression
    statement: TypedStatement

    @property
    def parents(self) -> tuple[TypedExpression, TypedExpression, TypedExpression]:
        return (self.parent, self.parent, self.parent)

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        return (self.host, *self.ingresses, self.parent, self.statement)


__all__ = (
    "PROFILE", "SCANLINE_ERROR_KEY", "ScanlineErrorFloatBitsIngressProof",
    "authenticate_scanline_error_float_bits_ingress",
    "apply_scanline_error_float_bits_ingress",
)


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


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _profile_tuple() -> tuple[object, ...]:
    value = ast.literal_eval(_FROZEN_PROFILE_TUPLE_REPR)
    if not isinstance(value, tuple):
        raise _fail("internal frozen profile tuple is not a tuple")
    return value


def _walk_expression(value: TypedExpression,
                     parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        yield from ((item, parent, expression_path, chain)
                    for item, parent, expression_path in _walk_expression(
                        expression, None, (*path, f"e{index}")))
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _host_is_reachable(program: TypedProgram, host_id: int) -> bool:
    calls: dict[int, set[int]] = {function.id: set()
                                  for function in program.functions}
    for function in program.functions:
        for statement_index, statement in enumerate(function.body):
            for item, _, _, _ in _walk_statement(statement, (statement_index,)):
                if item.kind == "call" and item.signature_id is not None:
                    calls[function.id].add(item.signature_id)
    main = next((function.id for function in program.functions
                 if function.name == "main"), None)
    pending = [] if main is None else [main]
    visited: set[int] = set()
    while pending:
        current = pending.pop()
        if current == host_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(calls.get(current, ()))
    return False


def authenticate_scanline_error_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> ScanlineErrorFloatBitsIngressProof:
    """Authenticate Scanline Error and return candidate-owned ingress nodes."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != SCANLINE_ERROR_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256):
        raise _fail("source, function, whole-program, or interface mismatch")
    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    loop_proof = program.counted_loop_proof
    if (loop_proof is None or
            (loop_proof.loop_count, loop_proof.unproved_loop_count,
             loop_proof.max_effective_depth, loop_proof.max_lexical_product,
             loop_proof.entrypoint_charge, loop_proof.call_graph_acyclic)
            != _LOOP_PROOF):
        raise _fail("loop or call graph profile mismatch")
    if ((program.resources.uniforms, program.resources.samplers,
         program.resources.outputs, program.resources.uses_texture,
         program.resources.uses_derivatives)
            != (("inputTex", "tileOffset", "fullResolution", "speed",
                 "timeOffset", "distortion", "noise", "mode", "time",
                 "renderScale"), ("inputTex",), ("fragColor",), True, False)):
        raise _fail("resource or binding signature mismatch")
    if len(program.functions) != 19:
        raise _fail("function cardinality mismatch")
    host = next((item for item in program.functions if item.id == _HOST_ID), None)
    if (host is None or
            (host.name, host.return_type.display(), len(host.parameters),
             len(host.body), _span(host))
            != (_HOST_NAME, "float", 1, 2, _HOST_SPAN)):
        raise _fail("host function identity mismatch")
    if not _host_is_reachable(program, _HOST_ID):
        raise _fail("ingress host is not reachable from main")

    located: list[tuple[tuple[object, ...], TypedExpression,
                        TypedExpression | None, tuple[TypedStatement, ...]]] = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                if item.kind == "builtin" and item.callee == "floatBitsToUint":
                    if function is not host:
                        raise _fail("float-bit ingress outside the host function")
                    located.append((path, item, parent, chain))
    if len(located) != 3:
        raise _fail(f"ingress cardinality mismatch: {len(located)}")

    actual = tuple(
        ("floatBitsToUint", path, _span(item),
         "" if item.type is None else item.type.display(), _sha(item),
         "" if parent is None else parent.kind,
         tuple("" if child.type is None else child.type.display()
               for child in item.children),
         tuple(_sha(child) for child in item.children))
        for path, item, parent, _ in located)
    if actual != _NODES:
        raise _fail("ingress node identity mismatch")

    ingresses = tuple(item for _, item, _, _ in located)
    if any(len(item.children) != 1 for item in ingresses):
        raise _fail("ingress arity mismatch")
    parents = tuple(parent for _, _, parent, _ in located)
    if (parents[0] is None or any(parent is not parents[0]
                                  for parent in parents[1:])):
        raise _fail("shared ingress parent identity mismatch")
    parent = parents[0]
    if (parent.kind, _span(parent), _sha(parent)) != _PARENT:
        raise _fail("shared ingress parent structure mismatch")

    chains = tuple(chain for _, _, _, chain in located)
    if any(chain != chains[0] for chain in chains[1:]):
        raise _fail("shared ingress statement identity mismatch")
    if tuple((item.kind, _span(item)) for item in chains[0]) != _STATEMENT_CHAIN:
        raise _fail("ingress statement ancestry mismatch")
    statement = chains[0][0]

    result = ScanlineErrorFloatBitsIngressProof(
        host, (ingresses[0], ingresses[1], ingresses[2]), parent, statement)
    if len(result.consumed_objects) != 6:
        raise _fail(
            f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def apply_scanline_error_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_scanline_error_float_bits_ingress(program, source_hash, profile)
    return program
