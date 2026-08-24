"""Exact one-node float-bit ingress profile for `classicNoisedeck/shapes`.

Shapes reaches `floatBitsToUint` exactly once, in the lattice hash helper:

```glsl
float seedFrac = 0.0;                         // normalized 101, raw 115
...
uint fracBits = floatBitsToUint(seedFrac);    // normalized 119, raw 133
uvec3 jitter = uvec3(
    (fracBits * 374761393u) ^ 0x9E3779B9u,    // normalized 122
    (fracBits * 668265263u) ^ 0x7F4A7C15u,    // normalized 123
    (fracBits * 2246822519u) ^ 0x94D049B4u    // normalized 124
);
```

This module does **not** add `floatBitsToUint` to the global builtin or
capability vocabulary. `floatBitsToUint` is already special-cased in the
builtin-name skip-list next to `round`/`tanh`/`ceil`/`all`+`lessThanEqual`,
and the frozen 44-entry `APPROVED_CAPABILITIES` tuple is untouched: the
caller must admit this node by object identity and skip `used.add(...)`.

It is deliberately kept separate from `scalar_uint_xor_profile.py`, which
already owns the complete Shapes source/interface/function/loop/reachability
lock and the three scalar XOR sites. Each mechanism keeps one responsibility
and its own traversal accounting; this module *reuses* the scalar-XOR
authenticator's returned candidate objects to bind the downstream ancestry
rather than re-deriving or duplicating that proof.

What is authenticated, beyond the coarse program identity:

* the exact `randomFromLatticeWithOffset` owner and its reachability from
  `main` in the conservative call graph;
* the declaration statement and `uint fracBits` declaration parent that owns
  the call, by span, node hash, symbol identity, and object identity;
* the scalar `float -> uint` signature -- one operand, `float` in, `uint`
  out, `rvalue`, no vector overload and no inverse conversion;
* the `seedFrac` local's source declaration and its **positive** `+0.0`
  literal initializer, read off the real sign bit rather than a `== 0.0`
  comparison, so `float seedFrac = -0.0;` fails here and not on a coarse
  hash;
* complete whole-program reference censuses for `seedFrac` and `fracBits`,
  so a moved call, a different operand, or an extra consumer is rejected;
* a complete whole-program census of exactly one `floatBitsToUint` node; and
* downstream ancestry: each of the three scalar XOR nodes the scalar-XOR
  authenticator returns must consume the declared `fracBits` symbol through
  its own frozen `uint * uint` product.

Claim boundary: with the default `LOOP_A_OFFSET=40`/`LOOP_B_OFFSET=30`
defines the owner is conservative call-graph reachable but the hash branch is
not taken by a normal full render. This closure authenticates structure and
emission, not render execution; the runtime bit-pattern tests and these
mutation barriers carry the semantic proof.
"""

from __future__ import annotations

import hashlib
import math

from .scalar_uint_xor_profile import (
    PROFILE as SCALAR_UINT_XOR_PROFILE, authenticate_scalar_uint_xor)
from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "shapes-float-bits-ingress-v1"
SHAPES_KEY = "classicNoisedeck/shapes:shapes"
SHAPES_FLOAT_BITS_INGRESS_KEYS = frozenset({SHAPES_KEY})

_RAW_BYTES = 21289
_RAW_SHA256 = "60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0"
_NORMALIZED_BYTES = 18713
_NORMALIZED_SHA256 = (
    "347d19f46adb59129ec2f5eb58910b1ea981be9ec03788a068ff6e884bb848e6")
_FUNCTIONS_SHA256 = (
    "dfd7220ab36ed03702afbc5e69e7e3a7346c60d488d9b3a2087d31214219943a")
_WHOLE_SHA256 = (
    "e072ec89fef6122ed3d581ea5efb6cec953d9b7492294ca9d8b0f011af5411f0")
_INTERFACE_SHA256 = (
    "e27ca4581c14991de7a17e296353b1993e8f9c6e5a4ec48b170dde8f8d1b1b6c")

_DEFINES = (("LOOP_A_OFFSET", "int", "40"), ("LOOP_B_OFFSET", "int", "30"))
_DECLARATION_COUNT = 23
_FUNCTION_COUNT = 36
_RESOURCES = (
    ("time", "seed", "wrap", "resolution", "tileOffset", "fullResolution",
     "loopAScale", "loopBScale", "speedA", "speedB", "paletteMode",
     "paletteOffset", "paletteAmp", "paletteFreq", "palettePhase",
     "cyclePalette", "rotatePalette", "repeatPalette"),
    (), ("fragColor",), False, False)
_LOOP_PROOF = (1, 0, 1, 3, 3, True)

_OWNER = (140, "randomFromLatticeWithOffset", "vec3",
          ((33, "st", "vec2", "in"), (34, "freq", "float", "in"),
           (35, "offset", "ivec2", "in")), 19, "94:1-135:2")

# Ingress: callee, expression path, span, result type, node hash, category.
_INGRESS = ("floatBitsToUint", (13, "e0", 0), "119:21-119:46", "uint",
            "15914c32a39e162b0da842b6b42d782d0579f9f46a41dec40713124adee3c451",
            "rvalue")
# Operand: kind, span, type, category, symbol id/name/storage/writable, hash.
_INGRESS_OPERAND = (
    "id", "119:37-119:45", "float", "lvalue", 294, "seedFrac", "local", True,
    "cfaf041fb7024c191ea005a26943a1fad37cce9be653075a9034ba75b57f7228")
# Declaration parent: kind, span, type, symbol id/name/storage/writable, hash.
_PARENT = (
    "declaration", "119:10-119:46", "uint", 302, "fracBits", "local", True,
    "f5dc751b49a4281ccc18b326e8ff16cd206283c1f3aa20b32090399748c3da8c")
_OWNER_STATEMENT_INDEX = 13
_STATEMENT_CHAIN = (("decl", "119:5-119:47"),)

# `float seedFrac = 0.0;` -- statement index, declaration span/hash, and the
# exact positive-zero literal initializer.
_SEED_FRAC_STATEMENT_INDEX = 5
_SEED_FRAC_DECLARATION = (
    "declaration", "101:11-101:25", "float", 294, "seedFrac", "local", True,
    "2dd8848610bf8c99a0bac30863f3b14a982a4fe4a419d8c6d0df400dc1b744c4")
_SEED_FRAC_INITIALIZER = (
    "literal", "101:22-101:25", "float", "rvalue", "0.0",
    "7ac93ffa79e6559ed02955eb8af1ed152b59b2e640af1d5ee97a372ba68b6579")
_SEED_FRAC_REFERENCES = (
    ("declaration", "101:11-101:25",
     "2dd8848610bf8c99a0bac30863f3b14a982a4fe4a419d8c6d0df400dc1b744c4"),
    ("id", "103:32-103:40",
     "5dfce39d07ccbcf59fd72b00bdf62858627fe35223709732607635bfe3ca168b"),
    ("id", "119:37-119:45",
     "cfaf041fb7024c191ea005a26943a1fad37cce9be653075a9034ba75b57f7228"),
)

# Downstream ancestry, one row per scalar XOR lane: the XOR span, its `uint *
# uint` product child (operator/span/hash), and the `fracBits` consumer id
# (span/hash) that product reads.
_XOR_ANCESTRY = (
    ("122:10-122:46", "*", "122:10-122:31",
     "ef28ea123ca50ffe49405acff9abf5cffac98f0a5d8923f29000890f49d97832",
     "122:10-122:18",
     "7b3742cadf4314863f83e469941df27106245be4ac7be3105f64ad2064c8f7b9"),
    ("123:10-123:46", "*", "123:10-123:31",
     "ae853fe2a64b5a16675079f5b3b3a395f14e63522f70ae0da2b782e2683b7966",
     "123:10-123:18",
     "f3cda3445b9b4937773f53db8d081b9a2ace15fcc2dd7fe396f6c99cfe380b08"),
    ("124:10-124:47", "*", "124:10-124:32",
     "fff586effb00f9673514ef6c140bfe774f69cf2c8b68bf4f917d02612e3e832b",
     "124:10-124:18",
     "337f3d6c8226bba9a378c3fee9e8ded84c25f311e16c0d777377a0709e036a85"),
)
_FRAC_BITS_REFERENCES = 4

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

# Owner, ingress, ingress operand, declaration parent, declaration statement,
# the `seedFrac` source declaration, and the three scalar XOR nodes: nine
# distinct objects, each visited and consumed exactly once.
_CONSUMED_LEDGER = 9

__all__ = (
    "PROFILE", "SHAPES_KEY", "SHAPES_FLOAT_BITS_INGRESS_KEYS",
    "authenticate_shapes_float_bits_ingress",
    "apply_shapes_float_bits_ingress",
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


def _check_ledger(entries: list, expected: int, label: str) -> None:
    """Require ``entries`` to hold exactly ``expected`` distinct objects."""
    identities = [id(item) for item in entries]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _fail(f"{label} visitation ledger mismatch")


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


def _owner_is_reachable(program: TypedProgram, owner_id: int) -> bool:
    calls: dict[int, set[int]] = {function.id: set()
                                  for function in program.functions}
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, _, _, _ in _walk_statement(statement, (index,)):
                if item.kind == "call" and item.signature_id is not None:
                    calls[function.id].add(item.signature_id)
    main = next((function.id for function in program.functions
                 if function.name == "main"), None)
    pending = [] if main is None else [main]
    visited: set[int] = set()
    while pending:
        current = pending.pop()
        if current == owner_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(calls.get(current, ()))
    return False


def _symbol_reference(value: TypedExpression) -> tuple[str, str, str]:
    return (value.kind, _span(value), _sha(value))


def authenticate_shapes_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return the one exact ``floatBitsToUint`` node from the supplied tree.

    Returns an empty tuple when ``program.key`` is not the carrier, so callers
    can treat the result as a membership set unconditionally; supplying a
    profile for a non-carrier key is a hard failure.
    """
    if program.key not in SHAPES_FLOAT_BITS_INGRESS_KEYS:
        if profile is not None:
            raise _fail("program key is not an admitted Shapes float-bit "
                        "ingress carrier")
        return ()
    if profile != PROFILE:
        raise _fail("exact profile carrier required")

    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if defines != _DEFINES:
        raise _fail("exact preprocessor define lock mismatch")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (source_hash != _RAW_SHA256
            or len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface "
                    "mismatch")
    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    loop_proof = program.counted_loop_proof
    if (loop_proof is None
            or (loop_proof.loop_count, loop_proof.unproved_loop_count,
                loop_proof.max_effective_depth, loop_proof.max_lexical_product,
                loop_proof.entrypoint_charge, loop_proof.call_graph_acyclic)
            != _LOOP_PROOF):
        raise _fail("loop or call graph profile mismatch")

    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != _RESOURCES
            or len(program.declarations) != _DECLARATION_COUNT):
        raise _fail("resource or binding signature mismatch")
    if len(program.functions) != _FUNCTION_COUNT:
        raise _fail("function cardinality mismatch")

    (owner_id, owner_name, owner_return, owner_parameters, owner_body_length,
     owner_span) = _OWNER
    owners = [item for item in program.functions if item.id == owner_id]
    if len(owners) != 1:
        raise _fail("ingress owner identity mismatch")
    owner = owners[0]
    if ((owner.name, owner.return_type.display(),
         tuple((item.id, item.name, item.type.display(), item.direction)
               for item in owner.parameters),
         len(owner.body), _span(owner))
            != (owner_name, owner_return, owner_parameters, owner_body_length,
                owner_span)):
        raise _fail("ingress owner identity mismatch")
    if not _owner_is_reachable(program, owner_id):
        raise _fail("ingress owner is not reachable from main")

    located: list[tuple[tuple[object, ...], TypedExpression,
                        TypedExpression | None,
                        tuple[TypedStatement, ...]]] = []
    seed_frac_references: list[TypedExpression] = []
    frac_bits_references: list[TypedExpression] = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                if item.symbol_id == _INGRESS_OPERAND[4]:
                    seed_frac_references.append(item)
                if item.symbol_id == _PARENT[3]:
                    frac_bits_references.append(item)
                if item.kind == "builtin" and item.callee == "floatBitsToUint":
                    if function is not owner:
                        raise _fail("float-bit ingress outside the owner "
                                    "function")
                    located.append((path, item, parent, chain))
    if len(located) != 1:
        raise _fail(f"ingress cardinality mismatch: {len(located)}")

    # The positive-zero initializer lock is evaluated before the ingress node
    # hashes so the focused `float seedFrac = 0.0;` -> `-0.0` mutant fails
    # *here* -- the operand's `Symbol` carries the declaration span, so a
    # coarser ordering would let the node hash absorb the sign change.
    seed_frac_statement = owner.body[_SEED_FRAC_STATEMENT_INDEX]
    if (seed_frac_statement.kind != "decl"
            or len(seed_frac_statement.expressions) != 1):
        raise _fail("seedFrac positive-zero initializer mismatch")
    seed_frac = seed_frac_statement.expressions[0]
    if ((seed_frac.kind, _span(seed_frac),
         "" if seed_frac.type is None else seed_frac.type.display(),
         seed_frac.symbol_id,
         None if seed_frac.symbol is None else seed_frac.symbol.name,
         None if seed_frac.symbol is None else seed_frac.symbol.storage,
         None if seed_frac.symbol is None else seed_frac.symbol.writable,
         _sha(seed_frac)) != _SEED_FRAC_DECLARATION
            or len(seed_frac.children) != 1):
        raise _fail("seedFrac positive-zero initializer mismatch")
    initializer = seed_frac.children[0]
    if ((initializer.kind, _span(initializer),
         "" if initializer.type is None else initializer.type.display(),
         initializer.category, initializer.literal, _sha(initializer))
            != _SEED_FRAC_INITIALIZER
            or initializer.children != ()
            or not isinstance(initializer.literal_value, float)
            or initializer.literal_value != 0.0
            or math.copysign(1.0, initializer.literal_value) != 1.0):
        raise _fail("seedFrac positive-zero initializer mismatch")

    path, ingress, parent, chain = located[0]
    if ((ingress.callee, _span(ingress),
         "" if ingress.type is None else ingress.type.display(),
         _sha(ingress), ingress.category)
            != (_INGRESS[0], _INGRESS[2], _INGRESS[3], _INGRESS[4], _INGRESS[5])
            or len(ingress.children) != 1):
        raise _fail("ingress node identity mismatch")
    operand = ingress.children[0]
    if ((operand.kind, _span(operand),
         "" if operand.type is None else operand.type.display(),
         operand.category, operand.symbol_id,
         None if operand.symbol is None else operand.symbol.name,
         None if operand.symbol is None else operand.symbol.storage,
         None if operand.symbol is None else operand.symbol.writable,
         _sha(operand)) != _INGRESS_OPERAND):
        raise _fail("ingress node identity mismatch")

    if (parent is None
            or (parent.kind, _span(parent),
                "" if parent.type is None else parent.type.display(),
                parent.symbol_id,
                None if parent.symbol is None else parent.symbol.name,
                None if parent.symbol is None else parent.symbol.storage,
                None if parent.symbol is None else parent.symbol.writable,
                _sha(parent)) != _PARENT
            or len(parent.children) != 1
            or parent.children[0] is not ingress):
        raise _fail("ingress declaration parent mismatch")

    if (path != _INGRESS[1]
            or tuple((item.kind, _span(item)) for item in chain)
            != _STATEMENT_CHAIN
            or len(chain) != 1
            or owner.body[_OWNER_STATEMENT_INDEX] is not chain[0]):
        raise _fail("ingress statement ancestry mismatch")
    statement = chain[0]

    if (tuple(_symbol_reference(item) for item in seed_frac_references)
            != _SEED_FRAC_REFERENCES
            or seed_frac_references[0] is not seed_frac
            or seed_frac_references[-1] is not operand):
        raise _fail("seedFrac reference census mismatch")

    xors = authenticate_scalar_uint_xor(program, source_hash,
                                        SCALAR_UINT_XOR_PROFILE)
    owned_frac_bits = {id(item) for item in frac_bits_references}
    if len(xors) != len(_XOR_ANCESTRY):
        raise _fail("downstream scalar XOR ancestry mismatch")
    consumers: list[TypedExpression] = []
    for node, record in zip(xors, _XOR_ANCESTRY):
        (xor_span, product_operator, product_span, product_sha,
         consumer_span, consumer_sha) = record
        if (_span(node) != xor_span or len(node.children) != 2):
            raise _fail("downstream scalar XOR ancestry mismatch")
        product = node.children[0]
        if (product.kind != "binary" or product.operator != product_operator
                or _span(product) != product_span
                or _sha(product) != product_sha
                or len(product.children) != 2):
            raise _fail("downstream scalar XOR ancestry mismatch")
        consumer = product.children[0]
        if (consumer.kind != "id" or consumer.symbol_id != parent.symbol_id
                or consumer.symbol is None
                or consumer.symbol.id != parent.symbol_id
                or consumer.type is None
                or consumer.type.display() != "uint"
                or _span(consumer) != consumer_span
                or _sha(consumer) != consumer_sha
                or id(consumer) not in owned_frac_bits):
            raise _fail("downstream scalar XOR ancestry mismatch")
        consumers.append(consumer)
    if (len(frac_bits_references) != _FRAC_BITS_REFERENCES
            or {id(item) for item in frac_bits_references}
            != {id(parent), *(id(item) for item in consumers)}):
        raise _fail("fracBits reference census mismatch")

    _check_ledger([owner, ingress, operand, parent, statement, seed_frac,
                   *xors], _CONSUMED_LEDGER, "ingress")
    return (ingress,)


def apply_shapes_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_shapes_float_bits_ingress(program, source_hash, profile)
    return program
