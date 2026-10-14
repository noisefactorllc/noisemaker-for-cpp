"""Exact dynamic Shapes float-bit ingress proof.

The existing structural checker runs against separately measured
runtime-define source and typed-tree locks.
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

_RAW_BYTES = 21292
_RAW_SHA256 = "28775b3e960c9051a320d48c7974792fbef33eaab80e5ca9aed5af43e8645d5e"
_NORMALIZED_BYTES = 18957
_NORMALIZED_SHA256 = 'da0d599c7b7192aab59e2d9e5d3031fe541b3bcaf0efd86c3aa3e39e3888ae70'
_FUNCTIONS_SHA256 = '22b94ef7f5fee7075a1463762717191748f52fa057f4001eebefbb301240a079'
_WHOLE_SHA256 = 'e831c40ff9a3b6529d8c9bc1b1edabcc9a7a722967514478a1a7d121565e8449'
_INTERFACE_SHA256 = '4dcc23b4c0fc79321c8da7385bdacfb12876cc4b66c22e8cf22db08fb4342121'

_DEFINES = (('LOOP_A_OFFSET', 'str', 'int'), ('LOOP_B_OFFSET', 'str', 'int'))
_DECLARATION_COUNT = 25
_FUNCTION_COUNT = 36
_RESOURCES = (('LOOP_A_OFFSET', 'LOOP_B_OFFSET', 'time', 'seed', 'wrap', 'resolution', 'tileOffset', 'fullResolution', 'loopAScale', 'loopBScale', 'speedA', 'speedB', 'paletteMode', 'paletteOffset', 'paletteAmp', 'paletteFreq', 'palettePhase', 'cyclePalette', 'rotatePalette', 'repeatPalette'), (), ('fragColor',), False, False)
_LOOP_PROOF = (1, 0, 1, 3, 3, True)

_OWNER = (142, 'randomFromLatticeWithOffset', 'vec3', ((35, 'st', 'vec2', 'in'), (36, 'freq', 'float', 'in'), (37, 'offset', 'ivec2', 'in')), 19, '96:1-137:2')

# Ingress: callee, expression path, span, result type, node hash, category.
_INGRESS = ('floatBitsToUint', (13, 'e0', 0), '121:21-121:46', 'uint', 'd07937bf73b620329a65b9ba0089f2efcc1f6cbd96465abf3f8514e6040f6952', 'rvalue')
# Operand: kind, span, type, category, symbol id/name/storage/writable, hash.
_INGRESS_OPERAND = ('id', '121:37-121:45', 'float', 'lvalue', 296, 'seedFrac', 'local', True, 'd73d9d9d692b18ffbd9688056cffb07184b14941546904ff88e6001b2507f900')
# Declaration parent: kind, span, type, symbol id/name/storage/writable, hash.
_PARENT = ('declaration', '121:10-121:46', 'uint', 304, 'fracBits', 'local', True, '279e85a94489bb632a860e9a7794b1abd5a3cdc9a1d1adc432b9dfaf71d76a51')
_OWNER_STATEMENT_INDEX = 13
_STATEMENT_CHAIN = (('decl', '121:5-121:47'),)

# `float seedFrac = 0.0;` -- statement index, declaration span/hash, and the
# exact positive-zero literal initializer.
_SEED_FRAC_STATEMENT_INDEX = 5
_SEED_FRAC_DECLARATION = ('declaration', '103:11-103:25', 'float', 296, 'seedFrac', 'local', True, '7085b3dcfe45fe0da35d772c2081e2e500f33067307258c5d2d8cef0ed93f0b9')
_SEED_FRAC_INITIALIZER = ('literal', '103:22-103:25', 'float', 'rvalue', '0.0', '8e4af0190cf0d93b73077338a75f1465d0b7675920ae542e77ac77a3cf0bc910')
_SEED_FRAC_REFERENCES = (('declaration', '103:11-103:25', '7085b3dcfe45fe0da35d772c2081e2e500f33067307258c5d2d8cef0ed93f0b9'), ('id', '105:32-105:40', 'acbf4e1a3901bf2b23a47d59e2a856f1f9d9fe8d9fc4bd35cdbfc31296ac4e29'), ('id', '121:37-121:45', 'd73d9d9d692b18ffbd9688056cffb07184b14941546904ff88e6001b2507f900'))

# Downstream ancestry, one row per scalar XOR lane: the XOR span, its `uint *
# uint` product child (operator/span/hash), and the `fracBits` consumer id
# (span/hash) that product reads.
_XOR_ANCESTRY = (('124:10-124:46', '*', '124:10-124:31', 'ceffef4faf6caab3b0619c446f710341e59021891b86c8e9f02511caeb23a8ef', '124:10-124:18', '98915c2c853e3a8abac3829c7b15afc6c17a1647c448ad0a5fff33be88e58a96'), ('125:10-125:46', '*', '125:10-125:31', 'ef6fdac0a523b8178fbd26c1f293ca88e1c061fcf03942ac625963cf58097f88', '125:10-125:18', 'bd7373e021cc8012ab42f0cde4a1d113561f2f5b1f8c941b091aef511c6acd33'), ('126:10-126:47', '*', '126:10-126:32', '5601df8956f5b4c1270d06baa26ee0ac583e4b13a4db97ca7f17d8caf5da62c5', '126:10-126:18', '895129e23276908a3c2b75cd38f6c281f6f8a580c3d5d3bb49190e850bc103f8'))
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
