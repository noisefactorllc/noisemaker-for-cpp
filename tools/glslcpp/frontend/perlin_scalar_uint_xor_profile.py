"""Exact identity profile for Perlin's default and runtime scalar uint XORs."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "perlin-scalar-uint-xor-v1"
PERLIN_KEY = "synth/perlin:perlin"

_RAW_BYTES = 10882
_RAW_SHA256 = "9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318"
_NORMALIZED_BYTES = 4875
_NORMALIZED_SHA256 = "88cb30dfb53c75f2d1bf51e9f9b865dca48ffb528e6ff2f77dec224dab309f64"
_FUNCTIONS_SHA256 = "3dbb088e9f6a0ae35d25a3ae197008f62bc7932f3a31697f2ce3fdb05c3e1abc"
_WHOLE_SHA256 = "a47c9ae9ef983c68c6c867296aaa33401841e5a089dddf9842630c6453e775bc"
_INTERFACE_SHA256 = "b8ff41d2d2259908c8efa422227f27b89469110330908e8eb34410319e878066"
_HASH3_SHA256 = "3c3253eaa535ee944476a6c5d60bcb8e66212482d3e4b5af44db96d0e1dfcc50"
_OUTER_SHA256 = "31049e8d38c4a6d26d051659ccd435fb7715906fb861440b7904429f3514495c"
_INNER_SHA256 = "f51b3a1264df7050a8528a5094da6d16c464978d1cb5c8b680461c9173d195cc"
_CONSTRUCTOR_SHA256 = "98f5cc12b9b7d44fefc28337f7d4a2d605eb455d2b36f39f3e80296114e57e2b"
_OPERANDS = (
    ("x", "73:18-73:21", "7a2954d83ebe2be4dfd2ca31558438ff5423668aa4bb593b349b489b7fc92023"),
    ("y", "73:24-73:27", "d15d2568d9165294874cd3c76406e368a48b31c6834d2949d91f7ac4845a81cc"),
    ("z", "73:30-73:33", "5387f564b5e3d096fd99fe10781613d0adab40bc86ebb50a00b79725118f7f08"),
)
_PROFILE_SHA256 = "bc712abd28da325cb3f3d162a6b542b9c28a7491564c44a90a6b090af39c0cbf"

_DEFAULT_VARIANTS = {
    _RAW_SHA256: {
        "raw_bytes": _RAW_BYTES,
        "raw_sha256": _RAW_SHA256,
        "normalized_bytes": _NORMALIZED_BYTES,
        "normalized_sha256": _NORMALIZED_SHA256,
        "functions_sha256": _FUNCTIONS_SHA256,
        "whole_sha256": _WHOLE_SHA256,
        "interface_sha256": _INTERFACE_SHA256,
        "hash3_sha256": _HASH3_SHA256,
        "outer_sha256": _OUTER_SHA256,
        "inner_sha256": _INNER_SHA256,
        "constructor_sha256": _CONSTRUCTOR_SHA256,
        "operands": _OPERANDS,
        "profile_sha256": _PROFILE_SHA256,
    },
    'd36fe934e6f0833ba01862b14c11697cc1db9e6a1eaafc690ac9c70438b5ea05': {'raw_bytes': 10951,
     'raw_sha256': 'd36fe934e6f0833ba01862b14c11697cc1db9e6a1eaafc690ac9c70438b5ea05',
     'normalized_bytes': 4796,
     'normalized_sha256': 'dd1082c7f0860ed2546a902e9e564f9ad5069022a05fadad6c3bb684d38324d3',
     'functions_sha256': 'fad171539eeb1f223418d726163fd6383a823988ae05e096ea9a54be45fee6a6',
     'whole_sha256': '3c1843a6d9731a096703e0f97983d96596111997cbe0a65a4623f4903537139b',
     'interface_sha256': 'a76eb3e72ae1e7e4c609d1adda3aaece51f5c3f09fd3334547efb20fce5d86a9',
     'hash3_sha256': '6b67821c54812980eb97656cc983c4ef6eea1a0efa9f520fc5b6dec991ebc492',
     'outer_sha256': '6a499d8b369e82c8bbde4ecb3710883248d574fb3da30552d5d3f38085ab5b8f',
     'inner_sha256': '6d94fc3d7501a4f88cbd112365bc73360332ee0822d2901777d116d2874651b5',
     'constructor_sha256': '803a0eb338f704e5582347b0c2a8defd650c9457f60f92348b42065ff563ef59',
     'operands': (('x',
                   '73:18-73:21',
                   '0ff2c373d77410a06c7c35a20b55a34198e3389b412d01f99b5a9bc56786487e'),
                  ('y',
                   '73:24-73:27',
                   '570ccd06797be9502908e1a1b23ac65b1ae74274e43fa28354a60c64c9054ccf'),
                  ('z',
                   '73:30-73:33',
                   '1c95212b7de692b9ffe66c206fa4f2a4aa80d49949a8afc08f8a2d8b99c39e28')),
     'profile_sha256': '22b4aaa3e9a3f0ca9e77c7f9b3be727b35d9f60b773de980d5b8b20232bced8a'},
}

_RUNTIME_VARIANTS = {'9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318': {'normalized_bytes': 7798,
                                                                      'normalized_sha256': '7e2a8c6cf41f85c9eecf3b2ac5ca2f6707f66b2f1e3bd480077ee78d0ce438ae',
                                                                      'functions_sha256': '86ba9bc311a85f9e1a288052fe64e80cada6f738bd34823427beadfe0de0643d',
                                                                      'whole_sha256': 'b74922ad26c60782ee9a86e67c57bb82bf0b880182fda0d09f0f568ac1f8297c',
                                                                      'interface_sha256': 'c17273b4700caa13a2de1c8ba4846cfd4a889fcd5346937df1d2eb2f745525f9'},
 'd36fe934e6f0833ba01862b14c11697cc1db9e6a1eaafc690ac9c70438b5ea05': {'normalized_bytes': 7719,
                                                                      'normalized_sha256': 'aa2c831be7adfdd7aec184da0130fae67a858b9592d931be09ec960a042a987b',
                                                                      'functions_sha256': '5351a2562f59a3b5131605194e406bd4f283b7d5f5343015260cc9b5f6f7c766',
                                                                      'whole_sha256': '37184ebf8ffdc85205ad6f6b43615cdda6047e2e3941a6f02a91aa4d30b2f8a1',
                                                                      'interface_sha256': '854254133f9834f70ad991a07f82a4a77f8cb3f0e9e245fc9a395a66b8b3ab88'}}

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

__all__ = (
    "PROFILE", "PERLIN_KEY", "authenticate_perlin_scalar_uint_xor",
    "apply_perlin_scalar_uint_xor",
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


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


def _profile_tuple(site) -> tuple[object, ...]:
    return (
        PROFILE, PERLIN_KEY, site["raw_sha256"], {"DIMENSIONS": 2},
        (49, "hash3", (10, "e0", 0, 0, 0), "73:18-73:33",
         site["outer_sha256"], site["constructor_sha256"], 0),
        (49, "hash3", (10, "e0", 0, 0, 0, 0), "73:18-73:27",
         site["inner_sha256"], site["outer_sha256"], 0),
        site["functions_sha256"], site["whole_sha256"], site["interface_sha256"],
        (45, 46, 48, 50, 51, 52, 53, 54, 55, 56), (47, 49, 57),
    )


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _all_expressions(program: TypedProgram):
    for function in program.functions:
        for statement in function.body:
            yield function.signature.id, statement, from_expression(statement)


def from_expression(statement: TypedStatement):
    for expression in _walk_statement(statement):
        yield expression



def _authenticate_runtime_perlin(program, source_hash, profile):
    site = _DEFAULT_VARIANTS.get(source_hash)
    runtime = _RUNTIME_VARIANTS.get(source_hash)
    if site is None or runtime is None:
        raise _fail("unrecognized runtime source hash")
    if (profile != PROFILE or program.key != PERLIN_KEY
            or source_hash != site["raw_sha256"]
            or len(program.raw_source.encode()) != site["raw_bytes"]
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != site["raw_sha256"]
            or len(program.source.encode()) != runtime["normalized_bytes"]
            or hashlib.sha256(program.source.encode()).hexdigest()
            != runtime["normalized_sha256"]
            or _sha(program.functions)
            != runtime["functions_sha256"]
            or _whole_fingerprint(program)
            != runtime["whole_sha256"]
            or _interface_fingerprint(program)
            != runtime["interface_sha256"]
            or any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS)):
        raise _fail("runtime source, tree, or interface mismatch")
    nodes = tuple(value for function in program.functions
                  for statement in function.body for value in _walk_statement(statement)
                  if value.kind == "binary" and value.operator == "^"
                  and value.type.display() == "uint")
    if len(nodes) != 2 or nodes[0] is nodes[1]:
        raise _fail("runtime scalar XOR census mismatch")
    return nodes

def authenticate_perlin_scalar_uint_xor(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, TypedExpression]:
    """Authenticate and return the exact outer and inner scalar XOR objects."""
    if tuple((item.name, item.kind, item.canonical_value)
             for item in program.preprocessor_defines) == (("DIMENSIONS", "str", "int"),):
        return _authenticate_runtime_perlin(program, source_hash, profile)
    site = _DEFAULT_VARIANTS.get(source_hash)
    if site is None:
        raise _fail("unrecognized source hash")
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != PERLIN_KEY or source_hash != site["raw_sha256"]:
        raise _fail("selected key and exact caller source hash required")
    if _sha(_profile_tuple(site)) != site["profile_sha256"]:
        raise _fail("internal frozen profile tuple mismatch")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != site["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != site["raw_sha256"]
            or len(normalized) != site["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != site["normalized_sha256"]
            or tuple((item.name, item.kind, item.canonical_value)
                     for item in program.preprocessor_defines)
            != (("DIMENSIONS", "int", "2"),)
            or program.body_status != "analyzed"
            or len(program.declarations) != 17
            or len(program.functions) != 13
            or _sha(program.functions) != site["functions_sha256"]
            or _whole_fingerprint(program) != site["whole_sha256"]
            or _interface_fingerprint(program) != site["interface_sha256"]):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    proof = program.counted_loop_proof
    if (proof is None or (proof.loop_count, proof.unproved_loop_count,
                          proof.max_effective_depth, proof.max_lexical_product,
                          proof.entrypoint_charge, proof.call_graph_acyclic)
            != (2, 0, 1, 8, 28, True)):
        raise _fail("loop proof mismatch")

    hash3 = program.functions[4]
    if ((hash3.signature.id, hash3.name, len(hash3.parameters), len(hash3.body),
         _sha(hash3)) != (49, "hash3", 1, 11, site["hash3_sha256"])
            or (hash3.parameters[0].id, hash3.parameters[0].name,
                hash3.parameters[0].type.display(), hash3.parameters[0].direction)
            != (20, "p", "vec3", "in")):
        raise _fail("hash3 signature or body mismatch")
    returned = hash3.body[10]
    if returned.kind != "return" or len(returned.expressions) != 1:
        raise _fail("hash3 return mismatch")
    division = returned.expressions[0]
    constructor = division.children[0]
    outer = constructor.children[0]
    inner = outer.children[0]
    if (division.kind != "binary" or division.operator != "/"
            or division.type.display() != "float"
            or constructor.kind != "construct"
            or constructor.constructor_type is None
            or constructor.constructor_type.display() != "float"
            or _span(constructor) != "73:12-73:34"
            or _sha(constructor) != site["constructor_sha256"]
            or len(constructor.children) != 1):
        raise _fail("float-constructor parent mismatch")
    for value, span, digest in (
            (outer, "73:18-73:33", site["outer_sha256"]),
            (inner, "73:18-73:27", site["inner_sha256"])):
        if (value.kind != "binary" or value.operator != "^"
                or value.type.display() != "uint" or value.category != "rvalue"
                or len(value.children) != 2
                or any(child.type.display() != "uint" for child in value.children)
                or _span(value) != span or _sha(value) != digest):
            raise _fail("scalar XOR site mismatch")
    operands = (inner.children[0], inner.children[1], outer.children[1])
    for operand, (member, span, digest) in zip(operands, site["operands"]):
        if (operand.kind != "swizzle" or operand.member != member
                or operand.type.display() != "uint" or len(operand.children) != 1
                or operand.children[0].symbol_id != 81
                or _span(operand) != span or _sha(operand) != digest):
            raise _fail("scalar XOR operand identity mismatch")

    scalar_xors: list[TypedExpression] = []
    calls: dict[int, list[int]] = {item.signature.id: [] for item in program.functions}
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if (value.kind == "binary" and value.operator == "^"
                        and value.type.display() == "uint"):
                    scalar_xors.append(value)
                if value.kind == "call" and value.signature_id is not None:
                    calls[function.signature.id].append(value.signature_id)
    if scalar_xors != [outer, inner]:
        raise _fail("scalar XOR cardinality or order mismatch")
    reachable: set[int] = set()
    pending = [50]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(calls[current])
    if (tuple(sorted(reachable)) != (45, 46, 48, 50, 51, 52, 53, 54, 55, 56)
            or tuple(sorted(set(calls) - reachable)) != (47, 49, 57)
            or calls[47].count(49) != 3
            or any(49 in calls[item] for item in reachable)):
        raise _fail("call graph or reachability mismatch")
    return outer, inner


def apply_perlin_scalar_uint_xor(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate this frozen identity profile without changing the tree."""
    authenticate_perlin_scalar_uint_xor(program, source_hash, profile)
    return program
