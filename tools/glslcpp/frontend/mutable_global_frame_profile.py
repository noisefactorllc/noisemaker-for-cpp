"""Exact identity profiles for **mutable, uninitialised, file-scope globals**.

`synth/shape:shape` is the first carrier, and the first program of this
mechanism. It declares two of them, one line apart::

    31|float aspectRatio;
    32|vec2 globalCoord;

The validator's "unsupported global declaration" names only normalized `31:1`.
That is the first rejecting site, not the bill of materials: **both** must be
admitted, and a `vec2` therefore has to be admissible on day one alongside a
`float`.

This module follows the **per-key-profile-name, shared-module** shape of
`linear_srgb_lane_index_profile.py` rather than the single-name shape of
`scalar_uint_xor_profile.py`. That is deliberate: `synth/noise:noise` carries
the identical reduced form (`vec2 globalCoord`) behind a counted-for first
blocker and will want `mutable-global-frame-noise-v1` from this module with no
edit to Shape's row, and the array-form programs (`cellRefract`, `effects`,
`kaleido`) will want their own names again on top of three further mechanisms.

**No vocabulary growth.** Nothing here touches `APPROVED_CAPABILITIES` (44) or
`APPROVED_TYPES` (17). `float` and `vec2` are already approved types -- it is
the *storage class*, not the type, that is being admitted -- so the caller must
skip `used.add(...)` entirely for a declaration admitted through this module,
symmetric with the `grade_valid` / `literal_vec3_lane_index_profile` /
`shapes_rvalue_assign_profile` precedents.

The crux: a state proof, not a syntax check
-------------------------------------------

Admitting a mutable global is safe only if every read is dominated by a write.
That is proved here as a structural predicate over the typed IR, re-derived
from a fresh parse:

* the **write census is exactly two** -- `globalCoord` at `459:5-459:47` and
  `aspectRatio` at `461:5-461:54`, both owned by `main`, both plain `=`, no
  compound assignment, no `++`/`--`, no partial write through a swizzle,
  member or index, and no write in any of the other 27 functions;
* both writes are **unconditional top-level statements of `main`**, at
  `main.body[1]` and `main.body[3]`, each the sole expression of its `expr`
  statement and nested inside nothing;
* **no `call` node occurs anywhere in `main.body[0..3]`**, so no helper -- and
  therefore no helper read -- can execute before both writes complete; the
  first call in `main` is at statement index 4;
* the **read census is exactly seven**, one of them in `main` itself at
  statement index 2, which follows the `globalCoord` write at index 1; the
  other six are in `circles`, `diamonds` (twice), `offset`, `rings` and
  `shape`, all reachable only through `offset(...)` at later statements.

Together those four make write-before-read hold on every reachable path, which
is what lets the emitted carrier be a `pixel`-scope object passed to helpers by
`const` reference -- and `const`-ness is then a compiler-level enforcement of
the single-writer lock rather than a comment.

Two globals, two different numeric contracts
--------------------------------------------

The parity target is the transpiler's materialization, not GLSL semantics.
`canonicalFactory274` declares them one line apart with materially different
contracts::

    var aspectRatio = 0;                          // plain Number -- a DOUBLE
    var globalCoord = new Float32Array([0, 0]);   // f32 lanes

and writes them as::

    (globalCoord[0] = gl_FragCoord[0] + tileOffset[0],
     globalCoord[1] = gl_FragCoord[1] + tileOffset[1], globalCoord);
    aspectRatio = fullResolution[0] / fullResolution[1];

`aspectRatio` is **never narrowed to f32** -- `fullResolution[0] /
fullResolution[1]` divides two exact-f32 doubles in double precision and stores
the double. A port that types this field `float` because GLSL says `float`
diverges, and the divergence is oracle-discriminable at any aspect ratio that
is not exactly f32-representable. `globalCoord` is the opposite: a
`Float32Array` mutated lane by lane, so every lane write narrows to f32,
discriminable only at extreme tile offsets.

`_LOCAL_TYPE_CONTRACT` therefore maps `float` to `double` and `vec2` to
`glsl::Vec2`, matching the emitter's existing `local_type()` convention -- and
each global's contract is a **separately deletable lock**, so a profile that
quietly treats the two uniformly cannot pass. Both are also value-initialised
to exactly the JS factory-scope initial values (`0` and `[0, 0]`), so the
"carry-over between pixels is unobservable" argument never has to be relied on
for the first pixel: in the reference these are factory-scope `var`s that
`$runtime.beginPixel` does **not** reset.

Census discipline
-----------------

Per the standing trap, modules that advertise a "whole-program" census while
walking only `function.body` leave global declaration initializers in a
coarse-hash-only blind spot. For this mechanism the initializers *are* the
subject matter, so every walker here descends `program.declarations` as well:
the initializer census records the two `const float` initializers node by node,
the reference census sees a read planted in one of them, and the node census
counts the whole program. `shapes_rvalue_assign_profile.py` -- which already
walks global initializers -- is the structural template, not the ingress
modules that inherit the gap.
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from .typed_ir import (TypedDeclaration, TypedExpression, TypedFunction,
                       TypedProgram, TypedStatement)


SHAPE_KEY = "synth/shape:shape"
SHAPE_PROFILE = "mutable-global-frame-shape-v1"
NOISE_KEY = "synth/noise:noise"
NOISE_PROFILE = "mutable-global-frame-noise-v1"

KEYS = (SHAPE_KEY, NOISE_KEY)
PROFILES = {SHAPE_KEY: SHAPE_PROFILE, NOISE_KEY: NOISE_PROFILE}
MUTABLE_GLOBAL_FRAME_KEYS = frozenset(PROFILES)

# Wiring data for the validator/emitter companion-exactness matrix. Shape
# additionally requires the already-frozen scalar-XOR carrier.
REQUIRED_COMPANION_PROFILES = {
    SHAPE_KEY: (("scalar_uint_xor_profile", "scalar-uint-xor-v1"),),
    NOISE_KEY: (
        ("runtime_loop_bound_profile", "runtime-loop-bound-v1"),
        ("scalar_uint_xor_profile", "scalar-uint-xor-v1"),
    ),
}

# The complete allowed field set for the slice row -- an ALLOWLIST, not a
# denylist. `generate_typed_slice`'s allowed-field arm compares
# `set(item) != expected`, so an allowlist is exhaustive by construction:
# "every other profile absent" follows from set equality and cannot go stale
# as new profile fields are added elsewhere in the tree. A denylist naming a
# handful of sibling profiles would silently admit the twenty-odd it does not
# name, which is precisely the guard §7.2 row 20 asks for.
ALLOWED_ROW_FIELDS = {
    SHAPE_KEY: frozenset({
        "defines",
        "program_key",
        "scalar_uint_xor_profile",
        "mutable_global_frame_profile",
    }),
    NOISE_KEY: frozenset({
        "defines",
        "program_key",
        "runtime_loop_bound_profile",
        "scalar_uint_xor_profile",
        "mutable_global_frame_profile",
    }),
}

# The emitter's own convention, asserted here rather than inherited silently so
# a future change to `emit_typed_cpp.local_type()` turns something red.
_LOCAL_TYPE_CONTRACT = {"float": "double", "vec2": "glsl::Vec2"}

_FRAME_STRUCT_NAME = "Frame"
_FRAME_INSTANCE_NAME = "frame"
_FRAME_PARAMETER_QUALIFIER = "const Frame&"
_FRAME_PARAMETER = "const Frame& frame"
_FRAME_PARAMETER_ORDINAL = 2
_FRAME_INSTANCE_SCOPE = "pixel"
_FRAME_WRITER = "main"

# Every IR shape that mutates a writable lvalue. `post` is a distinct kind from
# `unary`, not an operator variant of it -- see `_no_indirect_write_holds`.
_MUTATION_KINDS = ("assign", "unary", "post")
_INCREMENT_OPERATORS = ("++", "--")

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

# Two declarations, two symbols, `main`, two assignment nodes, two write
# targets, and the seven reads: sixteen distinct objects, each consumed once.
_CONSUMED_LEDGER = 16

__all__ = (
    "KEYS", "PROFILES", "MUTABLE_GLOBAL_FRAME_KEYS", "SHAPE_KEY",
    "SHAPE_PROFILE", "REQUIRED_COMPANION_PROFILES", "ALLOWED_ROW_FIELDS",
    "allowed_row_fields", "FrameField", "FrameContract", "frame_contract",
    "authenticate_mutable_global_frame", "apply_mutable_global_frame",
    "NOISE_KEY", "NOISE_PROFILE", "PREPARED_LOCKS",
    "PREPARED_MUTABLE_GLOBAL_FRAME_KEYS", "prepared_frame_contract",
    "authenticate_prepared_mutable_global_frame",
    "apply_prepared_mutable_global_frame",
)


class FrameField(NamedTuple):
    """One admitted global's complete numeric contract.

    `native_type` is the emitted C++ field type; `narrowing` records whether
    the shipped JavaScript narrows on every store. The two fields of
    `synth/shape` disagree on every single one of these, which is the whole
    point of recording them per declaration.
    """

    symbol_id: int
    name: str
    glsl_type: str
    native_type: str
    lane_count: int
    narrowing: str
    js_initializer: str
    js_number_kind: str


class FrameContract(NamedTuple):
    """The frozen emission shape the two authorities must both honour."""

    struct_name: str
    instance_name: str
    instance_scope: str
    value_initialized: bool
    helper_parameter: str
    helper_parameter_qualifier: str
    helper_parameter_ordinal: int
    writer_function: str
    fields: tuple[FrameField, ...]


class _Admitted(NamedTuple):
    """One admitted declaration's identity, position, and contract."""

    ordinal: int
    symbol_id: int
    name: str
    glsl_type: str
    storage: str
    writable: bool
    declaration_span: str
    symbol_span: str
    declaration_sha256: str
    symbol_sha256: str
    field: FrameField


class _WriteRecord(NamedTuple):
    symbol_id: int
    name: str
    owner_id: int
    owner_name: str
    operator: str
    assign_span: str
    assign_type: str
    assign_sha256: str
    target_span: str
    target_sha256: str
    statement_index: int
    statement_kind: str
    statement_span: str


class _ReadRecord(NamedTuple):
    symbol_id: int
    name: str
    owner_id: int
    owner_name: str
    span: str
    node_type: str
    node_sha256: str
    parent: tuple[str, str | None, str | None, str]
    statement_index: int
    path: tuple[object, ...]
    chain: tuple[tuple[str, str], ...]


class _WriteSite(NamedTuple):
    record: _WriteRecord
    node: TypedExpression
    target: TypedExpression
    chain: tuple[TypedStatement, ...]

    @property
    def symbol_id(self) -> int:
        return self.record.symbol_id

    @property
    def owner_id(self) -> int:
        return self.record.owner_id

    @property
    def owner_name(self) -> str:
        return self.record.owner_name

    @property
    def operator(self) -> str:
        return self.record.operator

    @property
    def assign_span(self) -> str:
        return self.record.assign_span

    @property
    def statement_index(self) -> int:
        return self.record.statement_index


class _ReadSite(NamedTuple):
    record: _ReadRecord
    node: TypedExpression
    chain: tuple[TypedStatement, ...]

    @property
    def symbol_id(self) -> int:
        return self.record.symbol_id

    @property
    def owner_id(self) -> int:
        return self.record.owner_id

    @property
    def owner_name(self) -> str:
        return self.record.owner_name

    @property
    def span(self) -> str:
        return self.record.span

    @property
    def statement_index(self) -> int:
        return self.record.statement_index


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
    return ValueError(f"{SHAPE_PROFILE}: {message}")


def _check_ledger(entries: list, expected: int, label: str) -> None:
    """Require ``entries`` to hold exactly ``expected`` distinct objects."""
    identities = [id(item) for item in entries]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _fail(f"{label} visitation ledger mismatch")


# --- walkers ----------------------------------------------------------------
#
# Every walker here descends `program.declarations` as well as
# `program.functions`. A "whole-program" census that only walks `function.body`
# leaves global declaration initializers in a coarse-hash-only blind spot, and
# for this mechanism the globals are the subject matter.

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
        yield from ((item, parent, item_path, chain, index)
                    for item, parent, item_path in _walk_expression(
                        expression, None, (*path, f"e{index}")))
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _program_nodes(program: TypedProgram):
    """Every expression node in the program, global initializers included."""
    for declaration in program.declarations:
        if declaration.initializer is None:
            continue
        for item, parent, path in _walk_expression(declaration.initializer):
            yield None, declaration, item, parent, path, ()
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain, _ in _walk_statement(
                    statement, (index,)):
                yield function, None, item, parent, path, chain


def _statement_node_kinds(statement: TypedStatement, index: int) -> tuple:
    return tuple(item.kind
                 for item, _, _, _, _ in _walk_statement(statement, (index,)))


def _call_statement_indices(function: TypedFunction) -> tuple[int, ...]:
    found = set()
    for index, statement in enumerate(function.body):
        for item, _, path, _, _ in _walk_statement(statement, (index,)):
            if item.kind == "call":
                found.add(path[0])
    return tuple(sorted(found))


def _node_census(program: TypedProgram) -> tuple[int, int]:
    total = 0
    assigns = 0
    for _, _, item, _, _, _ in _program_nodes(program):
        total += 1
        if item.kind == "assign":
            assigns += 1
    return total, assigns


def _declaration_inventory(program: TypedProgram) -> tuple:
    """All declarations, order-insensitive. Order is the adjacency lock's."""
    return tuple(sorted(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable,
         item.initializer is not None, _span(item))
        for item in program.declarations))


def _initializer_census(program: TypedProgram) -> tuple:
    return tuple(sorted(
        (item.symbol.id, item.symbol.name,
         tuple((node.kind, _span(node), node.literal, repr(node.literal_value),
                node.type.display())
               for node, _, _ in _walk_expression(item.initializer)))
        for item in program.declarations if item.initializer is not None))


def _call_graph(program: TypedProgram) -> tuple:
    edges = set()
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, _, _, _, _ in _walk_statement(statement, (index,)):
                if item.kind == "call":
                    edges.add((function.id, function.name, item.signature_id,
                               item.callee))
    return tuple(sorted(edges))


def _reachability(program: TypedProgram) -> tuple[tuple[int, ...],
                                                  tuple[int, ...]]:
    adjacency: dict[int, set[int]] = {}
    for caller, _, callee, _ in _call_graph(program):
        adjacency.setdefault(caller, set()).add(callee)
    entry = [item.id for item in program.functions if item.name == "main"]
    seen: set[int] = set()
    stack = list(entry)
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(adjacency.get(current, ()))
    identifiers = {item.id for item in program.functions}
    return (tuple(sorted(seen & identifiers)),
            tuple(sorted(identifiers - seen)))


def _base_symbol(node: TypedExpression) -> TypedExpression:
    current = node
    while current.kind in ("swizzle", "member", "index") and current.children:
        current = current.children[0]
    return current


def _parent_record(parent: object) -> tuple[str, str | None, str | None, str]:
    return (getattr(parent, "kind", ""), getattr(parent, "operator", None),
            getattr(parent, "callee", None), _span(parent))


def _reference_census(program: TypedProgram, symbols: dict[int, str]
                      ) -> tuple[list[_WriteSite], list[_ReadSite]]:
    """Classify every reference to an admitted global as a write or a read.

    A reference is a **write** only when it is the whole left-hand side of an
    assignment -- ``globalCoord = ...``. A reference reached through a swizzle,
    member or index target (``globalCoord.x = ...``) is classified as a read
    here on purpose, and `_no_indirect_write_holds` is the lock that refuses
    it: silently treating a partial write as a write would let a second writer
    in through the classifier.
    """
    writes: list[_WriteSite] = []
    reads: list[_ReadSite] = []
    for function, declaration, node, parent, path, chain in _program_nodes(
            program):
        if node.symbol_id not in symbols:
            continue
        owner_id = -1 if function is None else function.id
        owner_name = ("<global-initializer>" if function is None
                      else function.name)
        statement_index = -1 if not path else path[0]
        if (parent is not None and parent.kind == "assign"
                and parent.children and parent.children[0] is node):
            statement = chain[-1] if chain else None
            writes.append(_WriteSite(
                _WriteRecord(
                    node.symbol_id, symbols[node.symbol_id], owner_id,
                    owner_name, parent.operator, _span(parent),
                    parent.type.display(), _sha(parent), _span(node),
                    _sha(node), statement_index,
                    "" if statement is None else statement.kind,
                    "" if statement is None else _span(statement)),
                parent, node, chain))
            continue
        reads.append(_ReadSite(
            _ReadRecord(
                node.symbol_id, symbols[node.symbol_id], owner_id, owner_name,
                _span(node), node.type.display(), _sha(node),
                None if parent is None else _parent_record(parent),
                statement_index, path,
                tuple((item.kind, _span(item)) for item in chain)),
            node, chain))
    return writes, reads


# --- individually deletable locks -------------------------------------------
#
# Each predicate below is exactly one lock with exactly one message. A test
# proves a lock load-bearing by re-executing this module into a scratch
# namespace, replacing one of these functions with an always-true stand-in, and
# showing that the lock's message disappears. Keep them small, single-purpose
# and side-effect free.
#
# Ordering matters. `Symbol` embeds its declaration span, so every value-level
# lock (storage, mutability, initialiser-absence, both numeric contracts) is
# evaluated AHEAD of the node-hash identity lock that would otherwise absorb it
# and make it vacuous.

def _caller_source_hash_holds(source_hash: str | None, lock: dict) -> bool:
    """The caller's own view of the source agrees with the frozen record."""
    return source_hash == lock["raw_sha256"]


def _defines_hold(program: TypedProgram, lock: dict) -> bool:
    """Exactly `LOOP_A_OFFSET=40`, `LOOP_B_OFFSET=30`, in that order."""
    return tuple((item.name, item.kind, item.canonical_value)
                 for item in program.preprocessor_defines) == lock["defines"]


def _raw_source_holds(program: TypedProgram, lock: dict) -> bool:
    raw = program.raw_source.encode("utf-8")
    return (len(raw) == lock["raw_bytes"]
            and hashlib.sha256(raw).hexdigest() == lock["raw_sha256"])


def _normalized_source_holds(program: TypedProgram, lock: dict) -> bool:
    normalized = program.source.encode("utf-8")
    return (program.body_status == "analyzed"
            and len(normalized) == lock["normalized_bytes"]
            and hashlib.sha256(normalized).hexdigest()
            == lock["normalized_sha256"])


def _functions_fingerprint_holds(program: TypedProgram, lock: dict) -> bool:
    return _sha(program.functions) == lock["functions_sha256"]


def _whole_program_fingerprint_holds(program: TypedProgram,
                                     lock: dict) -> bool:
    return _whole(program) == lock["whole_sha256"]


def _interface_fingerprint_holds(program: TypedProgram, lock: dict) -> bool:
    return _interface(program) == lock["interface_sha256"]


def _function_cardinality_holds(program: TypedProgram, lock: dict) -> bool:
    return len(program.functions) == lock["function_count"]


def _resources_hold(program: TypedProgram, lock: dict) -> bool:
    """Ten uniforms, no sampler, one output, no texture, no derivatives.

    `resolution` is declared and never read anywhere in the program. It stays
    a required ABI binding; this lock is what stops it being "cleaned up".
    """
    resources = program.resources
    return ((resources.uniforms, resources.samplers, resources.outputs,
             resources.uses_texture, resources.uses_derivatives)
            == lock["resources"])


def _call_graph_holds(program: TypedProgram, lock: dict) -> bool:
    """The exact call-graph edge set, its digest, and full reachability.

    Deliberately does **not** count call *nodes*: the dominance lock owns where
    calls appear in `main`, and folding a node count in here would let this
    lock fire first and hide it.
    """
    edges = _call_graph(program)
    reachable, unreachable = _reachability(program)
    proof = program.counted_loop_proof
    if proof is None:
        return False
    return (len(edges) == lock["call_edge_count"]
            and _sha(edges) == lock["call_graph_sha256"]
            and reachable == lock["reachable"]
            and unreachable == lock["unreachable"]
            and (proof.loop_count, proof.unproved_loop_count,
                 proof.max_effective_depth, proof.max_lexical_product,
                 proof.entrypoint_charge, proof.call_graph_acyclic)
            == lock["counted_loop_proof"])


def _ordinal_adjacency_holds(program: TypedProgram, ordinals: tuple[int, ...],
                             lock: dict) -> bool:
    """The pair sits at declarations[13] and [14], right after `const float TAU`."""
    if ordinals != tuple(item.ordinal for item in lock["admitted"]):
        return False
    index, symbol_id = lock["preceding"]
    if index >= len(program.declarations):
        return False
    preceding = program.declarations[index]
    return (preceding.symbol.id == symbol_id
            and preceding.symbol.name == lock["preceding_name"]
            and preceding.symbol.storage == "const"
            and preceding.type.display() == "float"
            and preceding.initializer is not None)


def _mutable_storage_holds(declaration: TypedDeclaration,
                           record: _Admitted) -> bool:
    """File-scope `global` storage and a writable symbol.

    Storage, not writability, is what selects this sub-shape: `fragColor` is
    writable too but is an `output`.
    """
    return (declaration.symbol.storage == "global"
            and declaration.symbol.storage == record.storage
            and declaration.symbol.writable is True
            and declaration.symbol.writable == record.writable)


def _uninitialized_holds(declaration: TypedDeclaration) -> bool:
    """No initializer. This is the defining property of the sub-shape and the
    thing that separates it from every existing const admission."""
    return declaration.initializer is None


def _aspect_ratio_contract_holds(field: FrameField,
                                 declaration: TypedDeclaration) -> bool:
    """`aspectRatio` is a plain JS Number -- a DOUBLE, never narrowed to f32.

    `fullResolution[0] / fullResolution[1]` divides two exact-f32 doubles in
    double precision and stores the double. Typing this field `float` because
    GLSL says `float` diverges, discriminably, at any aspect ratio that is not
    exactly f32-representable.
    """
    return (field.name == "aspectRatio"
            and field.glsl_type == "float"
            and declaration.type.display() == "float"
            and field.native_type == "double"
            and field.native_type == _LOCAL_TYPE_CONTRACT.get(field.glsl_type)
            and field.lane_count == 1
            and field.narrowing == "none"
            and field.js_number_kind == "double"
            and field.js_initializer == "0")


def _global_coord_contract_holds(field: FrameField,
                                 declaration: TypedDeclaration) -> bool:
    """`globalCoord` is a `Float32Array` mutated lane by lane -- f32 narrowing.

    `glsl::Vec2` narrows identically (`Vec::operator=` applies
    `noisemaker::f32` per lane). Sharing `aspectRatio`'s contract here would be
    wrong even though the two are declared one line apart.
    """
    return (field.name == "globalCoord"
            and field.glsl_type == "vec2"
            and declaration.type.display() == "vec2"
            and field.native_type == "glsl::Vec2"
            and field.native_type == _LOCAL_TYPE_CONTRACT.get(field.glsl_type)
            and field.lane_count == 2
            and field.narrowing == "per-lane-f32"
            and field.js_number_kind == "float32-array"
            and field.js_initializer == "new Float32Array([0, 0])")


def _declaration_identity_holds(declaration: TypedDeclaration,
                                record: _Admitted) -> bool:
    """Symbol id, name, type, both spans, and both node hashes."""
    return ((declaration.symbol.id, declaration.symbol.name,
             declaration.type.display(), _span(declaration),
             _span(declaration.symbol), _sha(declaration),
             _sha(declaration.symbol))
            == (record.symbol_id, record.name, record.glsl_type,
                record.declaration_span, record.symbol_span,
                record.declaration_sha256, record.symbol_sha256))


def _declaration_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    """All fifteen declarations, order-insensitive: an added or removed global
    anywhere in the program is a hard failure here."""
    return (len(program.declarations) == lock["declaration_count"]
            and _declaration_inventory(program) == lock["declaration_inventory"])


def _initializer_census_holds(program: TypedProgram, lock: dict) -> bool:
    """The two `const float` initializers, node by node.

    A node planted in `PI`'s or `TAU`'s initializer is caught here rather than
    by a refreezable coarse hash -- the gap that three separate modules in the
    previous slice inherited.
    """
    return _initializer_census(program) == lock["initializer_census"]


def _frame_contract_holds(contract: FrameContract,
                          records: tuple[_Admitted, ...]) -> bool:
    """The emitted carrier is a value-initialised `pixel`-scope `Frame` passed
    to helpers by `const` reference.

    `const Frame&` is what turns the single-writer-is-`main` lock into a
    compiler-level enforcement: if that lock were ever wrong the build would
    fail rather than silently diverge.
    """
    return (contract.struct_name == _FRAME_STRUCT_NAME
            and contract.instance_name == _FRAME_INSTANCE_NAME
            and contract.instance_scope == _FRAME_INSTANCE_SCOPE
            and contract.value_initialized is True
            and contract.helper_parameter == _FRAME_PARAMETER
            and contract.helper_parameter_qualifier == _FRAME_PARAMETER_QUALIFIER
            and contract.helper_parameter_ordinal == _FRAME_PARAMETER_ORDINAL
            and contract.writer_function == _FRAME_WRITER
            and contract.fields == tuple(item.field for item in records))


def _node_census_holds(total: int, assigns: int, lock: dict) -> bool:
    return total == lock["total_nodes"] and assigns == lock["total_assigns"]


def _write_cardinality_holds(writes: list[_WriteSite], lock: dict) -> bool:
    return len(writes) == len(lock["writes"])


def _single_writer_holds(writes: list[_WriteSite], lock: dict) -> bool:
    """Every write is owned by `main`. No helper writes either symbol."""
    owner_id, owner_name = lock["main"][0], lock["main"][1]
    return all(item.owner_id == owner_id and item.owner_name == owner_name
               for item in writes)


def _no_indirect_write_holds(program: TypedProgram, writes: list[_WriteSite],
                             symbols: dict[int, str]) -> bool:
    """No compound assignment, no `++`/`--`, no partial write.

    Walks every mutation-shaped node in the program -- global initializers
    included -- and requires that the only ones whose target *base* is an
    admitted global are the two authenticated whole-symbol assignments.

    The IR spells prefix and postfix increment as **two different kinds**:
    `unary` with operator `++`/`--` (`body_semantic.py:200-209`) and `post`
    (`body_semantic.py:210-212`). Both are mutations of a writable lvalue and
    both must be caught here -- testing only `unary` lets `aspectRatio++`
    through this lock. Compound assignment (`*=`, `+=`, ...) is kind `assign`
    with a non-`=` operator, so it needs no operator entry of its own.

    Today the read census would also notice such a node, because a reference
    that is not a whole-symbol assignment target lands in the read bucket and
    trips the cardinality lock. This lock exists so the failure names the
    right thing, and because §11's array form makes a *helper* the writer and
    relaxes `const Frame&` to `Frame&` -- exactly where an increment becomes
    plausible and the read-census fallback may not have this shape.
    """
    authenticated = {id(item.node) for item in writes}
    for _, _, node, _, _, _ in _program_nodes(program):
        if node.kind not in _MUTATION_KINDS or not node.children:
            continue
        if node.kind != "assign" and node.operator not in _INCREMENT_OPERATORS:
            continue
        target = node.children[0]
        if _base_symbol(target).symbol_id not in symbols:
            continue
        if (node.kind != "assign" or node.operator != "="
                or target.kind != "id" or id(node) not in authenticated):
            return False
    return True


def _write_position_holds(writes: list[_WriteSite], main: TypedFunction,
                          lock: dict) -> bool:
    """Both writes are unconditional top-level statements of `main`.

    `main.body[1]` and `main.body[3]`, each the sole expression of its own
    `expr` statement, nested inside no block, `if` or loop -- the program has
    no loops at all. This is premise 1 of the dominance proof.
    """
    if len(writes) != len(lock["writes"]):
        return False
    for site, expected in zip(writes, lock["writes"]):
        index = expected.statement_index
        if index < 0 or index >= len(main.body):
            return False
        statement = main.body[index]
        if (len(site.chain) != 1 or site.chain[0] is not statement
                or statement.kind != "expr"
                or len(statement.expressions) != 1
                or statement.expressions[0] is not site.node
                or site.record.statement_index != index):
            return False
    return True


def _write_identity_holds(writes: list[_WriteSite], lock: dict) -> bool:
    return tuple(item.record for item in writes) == lock["writes"]


def _read_cardinality_holds(reads: list[_ReadSite], lock: dict) -> bool:
    return len(reads) == len(lock["reads"])


def _read_identity_holds(reads: list[_ReadSite], lock: dict) -> bool:
    return tuple(item.record for item in reads) == lock["reads"]


def _dominance_holds(main: TypedFunction, writes: list[_WriteSite],
                     reads: list[_ReadSite], lock: dict,
                     symbols: dict[int, str]) -> bool:
    """No read can precede its write on any reachable path.

    Premise 2: **no `call` node occurs anywhere in `main.body[0..3]`**, so no
    helper -- and therefore no helper read -- can execute before both writes
    complete. Premise 3: the only read inside `main` follows its own write.
    Premise 4: every other read is inside a helper, and every helper is reached
    only through a call at a statement index at or after the call-free prefix.
    """
    prefix = lock["call_free_prefix"]
    kinds = tuple(_statement_node_kinds(main.body[index], index)
                  for index in range(min(prefix, len(main.body))))
    if kinds != lock["main_prefix_kinds"]:
        return False
    if any("call" in item for item in kinds):
        return False
    calls = _call_statement_indices(main)
    if calls != lock["main_call_statement_indices"]:
        return False
    if calls and min(calls) < prefix:
        return False
    written_at = {}
    for site in writes:
        if site.symbol_id in written_at:
            return False
        written_at[site.symbol_id] = site.statement_index
    if set(written_at) != set(symbols):
        return False
    for site in reads:
        if site.owner_id == lock["main"][0]:
            if site.statement_index <= written_at[site.symbol_id]:
                return False
        elif site.owner_id < 0:
            # A read in a global declaration initializer runs before `main`.
            return False
    return True


def _main_body_holds(main: TypedFunction, lock: dict) -> bool:
    identifier, name, length, span = lock["main"]
    return (main.id == identifier and main.name == name
            and len(main.body) == length and _span(main) == span
            and tuple((item.kind, _span(item)) for item in main.body)
            == lock["main_body"])


# --- frozen per-key records --------------------------------------------------

_ASPECT_FIELD = FrameField(
    14, "aspectRatio", "float", "double", 1, "none", "0", "double")
_COORD_FIELD = FrameField(
    15, "globalCoord", "vec2", "glsl::Vec2", 2, "per-lane-f32",
    "new Float32Array([0, 0])", "float32-array")

_LOCKS = {
    SHAPE_KEY: {
        "profile": SHAPE_PROFILE,
        # Provenance only -- NO predicate reads `source_path`, because a
        # TypedProgram carries no path to check it against. The authority is
        # `raw_bytes`/`raw_sha256` below, which ARE locked; the path is here so
        # a reader can find the file, and the focused test asserts the file at
        # this path hashes to the frozen value.
        "source_path": "synth/shape/shape.glsl",
        "raw_bytes": 15986,
        "raw_sha256":
            "d917d2027c873f05bc4183277a2b1dffe158c13cfd1281461580a31e0cd7d67f",
        "normalized_bytes": 14805,
        "normalized_sha256":
            "83bf41728f8e10ed08ec04a9899f35d60b476700703d4db851f57289cf6f1b00",
        "functions_sha256":
            "9aea716238e075a431961c875f674c34b97ed44a5071be54de2a21f3cf94d7d3",
        "whole_sha256":
            "60d87d93ec58d1f4c1e25a70d011a83c65b1988bf337bfbbf28e0e8c99a7e1ea",
        "interface_sha256":
            "06d49ba68a175bf4f313fab9533e889b049fe6593af34b0d49b62da28d23f2fd",
        "defines": (("LOOP_A_OFFSET", "int", "40"),
                    ("LOOP_B_OFFSET", "int", "30")),
        "declaration_count": 15,
        "function_count": 28,
        # Ten uniforms, no samplers, one output, no texture reads, no
        # derivatives, no loops. `resolution` is never read; it stays required.
        "resources": (("resolution", "tileOffset", "fullResolution", "time",
                       "seed", "wrap", "loopAScale", "loopBScale", "speedA",
                       "speedB"), (), ("fragColor",), False, False),
        "counted_loop_proof": (0, 0, 0, 0, 0, True),
        "call_edge_count": 40,
        "call_graph_sha256":
            "78ba0116b860e7da00b9cf1abe6ca2dbe73dc25453fc052af26a47a784ea9dea",
        "reachable": tuple(range(95, 123)),
        "unreachable": (),
        "declaration_inventory": (
            (1, "resolution", "vec2", "uniform", False, False, "15:1-15:25"),
            (2, "tileOffset", "vec2", "uniform", False, False, "16:1-16:25"),
            (3, "fullResolution", "vec2", "uniform", False, False,
             "17:1-17:29"),
            (4, "time", "float", "uniform", False, False, "18:1-18:20"),
            (5, "seed", "int", "uniform", False, False, "19:1-19:18"),
            (6, "wrap", "bool", "uniform", False, False, "20:1-20:19"),
            (7, "loopAScale", "float", "uniform", False, False, "21:1-21:26"),
            (8, "loopBScale", "float", "uniform", False, False, "22:1-22:26"),
            (9, "speedA", "float", "uniform", False, False, "23:1-23:22"),
            (10, "speedB", "float", "uniform", False, False, "24:1-24:22"),
            (11, "fragColor", "vec4", "output", True, False, "26:1-26:16"),
            (12, "PI", "float", "const", False, True, "28:1-28:32"),
            (13, "TAU", "float", "const", False, True, "29:1-29:33"),
            (14, "aspectRatio", "float", "global", True, False, "31:1-31:19"),
            (15, "globalCoord", "vec2", "global", True, False, "32:1-32:18"),
        ),
        "initializer_census": (
            (12, "PI", (("literal", "28:18-28:31", "3.14159265359",
                         "3.14159265359", "float"),)),
            (13, "TAU", (("literal", "29:19-29:32", "6.28318530718",
                          "6.28318530718", "float"),)),
        ),
        "preceding": (12, 13),
        "preceding_name": "TAU",
        "total_nodes": 2007,
        "total_assigns": 41,
        "admitted": (
            _Admitted(
                13, 14, "aspectRatio", "float", "global", True,
                "31:1-31:19", "31:1-31:19",
                "427aaa8106c1e52c45070286b71c8c89a21837a48895e5b18281f083c648c545",
                "20b2f3af0563bbbf662f933f3f98a88bd42fc06909b42f2d5c7e4aadffd6d015",
                _ASPECT_FIELD),
            _Admitted(
                14, 15, "globalCoord", "vec2", "global", True,
                "32:1-32:18", "32:1-32:18",
                "2a2a978ebdd106d15ac1b5c066675cb89bf06d2e515839298a5ed6799e8a593a",
                "ea78b90b61d51c4ea8dee49e0f38961467d7c183f806c74509e102a9a1cb074a",
                _COORD_FIELD),
        ),
        "frame": FrameContract(
            _FRAME_STRUCT_NAME, _FRAME_INSTANCE_NAME, _FRAME_INSTANCE_SCOPE,
            True, _FRAME_PARAMETER, _FRAME_PARAMETER_QUALIFIER,
            _FRAME_PARAMETER_ORDINAL, _FRAME_WRITER,
            (_ASPECT_FIELD, _COORD_FIELD)),
        "main": (105, "main", 19, "457:1-496:2"),
        "main_body": (
            ("decl", "458:5-458:43"), ("expr", "459:5-459:48"),
            ("decl", "460:5-460:46"), ("expr", "461:5-461:55"),
            ("decl", "463:5-463:55"), ("if", "464:5-466:6"),
            ("decl", "467:5-467:57"), ("decl", "468:5-468:20"),
            ("if", "469:5-473:6"), ("decl", "475:5-475:55"),
            ("if", "476:5-478:6"), ("decl", "479:5-479:57"),
            ("decl", "480:5-480:20"), ("if", "481:5-485:6"),
            ("decl", "487:5-487:43"), ("decl", "488:5-488:43"),
            ("decl", "490:5-490:34"), ("expr", "493:5-493:25"),
            ("expr", "495:5-495:23"),
        ),
        # `main.body[0..3]` is the dominance premise: not one `call` node.
        "call_free_prefix": 4,
        "main_prefix_kinds": (
            ("declaration", "construct", "literal", "literal", "literal",
             "literal"),
            ("assign", "id", "binary", "swizzle", "id", "id"),
            ("declaration", "binary", "id", "swizzle", "id"),
            ("assign", "id", "binary", "swizzle", "id", "swizzle", "id"),
        ),
        "main_call_statement_indices": (4, 6, 8, 9, 11, 13, 14, 15),
        "writes": (
            _WriteRecord(
                15, "globalCoord", 105, "main", "=", "459:5-459:47", "vec2",
                "d09df4a87633a9972dcf9234079b5de2dba56d2b3c9ba75a4221a256253642d7",
                "459:5-459:16",
                "52f3f707504acda8e8a0cb4d790ae3bee88885ee519fbda7ffc91d026cf3c2dc",
                1, "expr", "459:5-459:48"),
            _WriteRecord(
                14, "aspectRatio", 105, "main", "=", "461:5-461:54", "float",
                "ec47f65794acc80ada1ff623edaeb159e81c3bc233eb5f21f351e4049dd65889",
                "461:5-461:16",
                "cc7446e140483e5d7f0ecb2f45ceda8cba9cbfebcd844b590368f3f3710b8cb1",
                3, "expr", "461:5-461:55"),
        ),
        "reads": (
            _ReadRecord(
                14, "aspectRatio", 102, "circles", "407:41-407:52", "float",
                "efe078451f3cae103b0335e7ddccd340e229ace24d6a0e4f98e9b7ce555ad374",
                ("binary", "*", None, "407:35-407:52"), 0,
                (0, "e0", 0, 0, 1, 0, 1), (("decl", "407:5-407:60"),)),
            _ReadRecord(
                15, "globalCoord", 104, "diamonds", "417:20-417:31", "vec2",
                "dfe3b07bf01c04278b2d8799f24ce7bc5c45bb0a8adfdf6a3d96d0148d005d0d",
                ("binary", "/", None, "417:20-417:50"), 0, (0, "e0", 0, 0),
                (("decl", "417:5-417:51"),)),
            _ReadRecord(
                14, "aspectRatio", 104, "diamonds", "418:27-418:38", "float",
                "d4c2bcd82a3edaa2724d1a56795dd37b13fda00a01eec3db91681d0dba3ab914",
                ("binary", "*", None, "418:21-418:38"), 1, (1, "e0", 1, 0, 1),
                (("expr", "418:5-418:45"),)),
            _ReadRecord(
                15, "globalCoord", 105, "main", "460:15-460:26", "vec2",
                "0d29603c69746a0b544fa793b4bd40d94c31281d6527929b02abfd379975d5ef",
                ("binary", "/", None, "460:15-460:45"), 2, (2, "e0", 0, 0),
                (("decl", "460:5-460:46"),)),
            _ReadRecord(
                14, "aspectRatio", 109, "offset", "439:34-439:45", "float",
                "f721a36f8eb63109a3b227a00ca32ac6426e5c5882a1b2b53b3f8d792f897297",
                ("binary", "*", None, "439:28-439:45"), 0,
                (0, "s1", "s1", "s1", "s0", "s0", "e0", 0, 0, 0, 0, 1, 1),
                (("if", "431:5-453:6"), ("if", "433:12-453:6"),
                 ("if", "435:12-453:6"), ("if", "438:12-453:6"),
                 ("block", "438:34-440:6"), ("return", "439:9-439:79"))),
            _ReadRecord(
                14, "aspectRatio", 118, "rings", "412:41-412:52", "float",
                "5b7a22df353dcc560065d4b426237b8737560a2c2666c6716324a850b3f76fb4",
                ("binary", "*", None, "412:35-412:52"), 0,
                (0, "e0", 0, 0, 1, 0, 1), (("decl", "412:5-412:60"),)),
            _ReadRecord(
                14, "aspectRatio", 119, "shape", "424:26-424:37", "float",
                "74417ce0f4307862c002e820d92cfd4dee398a3249711be68e7d7bd4ba2aeba3",
                ("construct", None, None, "424:21-424:43"), 0,
                (0, "e0", 1, 1, 0), (("expr", "424:5-424:44"),)),
        ),
    },
}

def _admitted_symbols(lock: dict) -> dict[int, str]:
    """The `{symbol id: name}` map of one key's admitted globals.

    Derived per call from the selected key's own record rather than bound to
    `SHAPE_KEY` at import. The shared-module shape exists so
    `synth/noise:noise` can later add `mutable-global-frame-noise-v1` with no
    edit to Shape's row; an import-time global would run Shape's symbol ids
    against noise's tree and block that extension behind a message naming the
    wrong declaration.
    """
    return {item.symbol_id: item.name for item in lock["admitted"]}


def frame_contract(key: str) -> FrameContract:
    """The frozen emission contract both authorities must honour for ``key``."""
    lock = _LOCKS.get(key)
    if lock is None:
        raise _fail(f"{key} is not an admitted mutable-global frame carrier")
    return lock["frame"]


def allowed_row_fields(key: str) -> frozenset[str]:
    """The complete set of slice-row fields permitted for ``key``.

    Exhaustive by construction: the validator's allowed-field arm compares
    `set(item) != expected`, so requiring equality with this set is what
    discharges "every other profile absent".
    """
    fields = ALLOWED_ROW_FIELDS.get(key)
    if fields is None:
        raise _fail(f"{key} is not an admitted mutable-global frame carrier")
    return fields


def authenticate_mutable_global_frame(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedDeclaration, ...]:
    """Return the exact frozen mutable-global declarations of ``program.key``.

    Returns an empty tuple when ``program.key`` is not a carrier, so callers
    can treat the result as a membership set unconditionally; supplying a
    profile for a non-carrier key is a hard failure.

    Both declarations are returned. The validator's rejection names only the
    first (`31:1 float aspectRatio;`); admitting only that one leaves
    `32:1 vec2 globalCoord;` to fail at the second, unconditional post-loop
    gate.
    """
    from .noise_runtime_define_profile import is_dynamic_program, authenticate_frame
    if is_dynamic_program(program):
        return authenticate_frame(program, source_hash, profile)
    if program.key == NOISE_KEY:
        return _authenticate_noise_mutable_global_frame(
            program, source_hash, profile)
    if program.key not in MUTABLE_GLOBAL_FRAME_KEYS:
        if profile is not None:
            raise _fail(
                "program key is not an admitted mutable-global frame carrier; "
                f"{SHAPE_KEY} 31:1 float aspectRatio and 32:1 vec2 "
                "globalCoord are the sole admitted declarations")
        return ()
    lock = _LOCKS[program.key]
    if profile != lock["profile"]:
        raise _fail("exact profile carrier required")

    if not _caller_source_hash_holds(source_hash, lock):
        raise _fail("exact caller source hash required")
    if not _defines_hold(program, lock):
        raise _fail("exact preprocessor define lock mismatch")
    if not _raw_source_holds(program, lock):
        raise _fail("raw source drift")
    if not _normalized_source_holds(program, lock):
        raise _fail("normalized source drift")
    if not _functions_fingerprint_holds(program, lock):
        raise _fail("typed function fingerprint drift")
    if not _whole_program_fingerprint_holds(program, lock):
        raise _fail("whole-program fingerprint drift")
    if not _interface_fingerprint_holds(program, lock):
        raise _fail("interface fingerprint drift")
    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if not _function_cardinality_holds(program, lock):
        raise _fail("function cardinality or inventory mismatch")
    if not _resources_hold(program, lock):
        raise _fail("resource profile mismatch")
    if not _call_graph_holds(program, lock):
        raise _fail("call graph or reachability profile mismatch")

    # Locate the admitted declarations by SYMBOL IDENTITY, never by ordinal, so
    # the ordinal lock below is the only thing that can see a reordering.
    located: list[tuple[int, TypedDeclaration]] = []
    for record in lock["admitted"]:
        matches = [(index, item)
                   for index, item in enumerate(program.declarations)
                   if item.symbol.id == record.symbol_id]
        if len(matches) != 1:
            raise _fail("admitted global declaration identity mismatch")
        located.append(matches[0])
    ordinals = tuple(index for index, _ in located)
    if not _ordinal_adjacency_holds(program, ordinals, lock):
        raise _fail("admitted global declaration ordinal or adjacency mismatch")

    # Value-level locks run AHEAD of node identity: `Symbol` embeds its own
    # declaration span, so a storage, mutability or initializer mutation also
    # shifts the enclosing node hash, and a coarser ordering would let the hash
    # absorb the change and make each of these vacuous.
    for record, (_, declaration) in zip(lock["admitted"], located):
        if not _mutable_storage_holds(declaration, record):
            raise _fail("admitted global storage or mutability mismatch")
        if not _uninitialized_holds(declaration):
            raise _fail("admitted global declaration carries an initializer")
        if record.name == "aspectRatio":
            contract_holds = _aspect_ratio_contract_holds(record.field,
                                                          declaration)
        elif record.name == "globalCoord":
            contract_holds = _global_coord_contract_holds(record.field,
                                                          declaration)
        else:
            raise _fail("unknown admitted global field")
        if not contract_holds:
            raise _fail(f"{record.name} numeric contract mismatch")
        if not _declaration_identity_holds(declaration, record):
            raise _fail("admitted global declaration identity mismatch")

    if not _declaration_inventory_holds(program, lock):
        raise _fail("global declaration inventory mismatch")
    if not _initializer_census_holds(program, lock):
        raise _fail("global declaration initializer census mismatch")
    if not _frame_contract_holds(lock["frame"], lock["admitted"]):
        raise _fail("frame emission contract mismatch")

    total, assigns = _node_census(program)
    if not _node_census_holds(total, assigns, lock):
        raise _fail("whole-program node census mismatch")

    entries = [item for item in program.functions
               if item.id == lock["main"][0] and item.name == lock["main"][1]]
    if len(entries) != 1:
        raise _fail("main body shape mismatch")
    main = entries[0]

    symbols = _admitted_symbols(lock)
    writes, reads = _reference_census(program, symbols)
    if not _write_cardinality_holds(writes, lock):
        raise _fail("mutable global write census cardinality mismatch: "
                    f"{len(writes)}")
    if not _single_writer_holds(writes, lock):
        raise _fail("mutable global single-writer proof mismatch")
    if not _no_indirect_write_holds(program, writes, symbols):
        raise _fail("mutable global indirect or partial write present")
    if not _write_position_holds(writes, main, lock):
        raise _fail("mutable global write position mismatch")
    if not _write_identity_holds(writes, lock):
        raise _fail("mutable global write identity mismatch")
    if not _read_cardinality_holds(reads, lock):
        raise _fail("mutable global read census cardinality mismatch: "
                    f"{len(reads)}")
    if not _read_identity_holds(reads, lock):
        raise _fail("mutable global read identity mismatch")
    if not _dominance_holds(main, writes, reads, lock, symbols):
        raise _fail("mutable global write-before-read dominance mismatch")
    if not _main_body_holds(main, lock):
        raise _fail("main body shape mismatch")

    admitted = tuple(declaration for _, declaration in located)
    _check_ledger(
        [*admitted, *(item.symbol for item in admitted), main,
         *(item.node for item in writes), *(item.target for item in writes),
         *(item.node for item in reads)],
        _CONSUMED_LEDGER, "mutable-global-frame")
    return admitted


def apply_mutable_global_frame(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_mutable_global_frame(program, source_hash, profile)
    return program


# --- second live key: synth/noise --------------------------------------------
#
# `mutable-global-frame-noise-v1` is the key this module's header designed for
# `synth/noise:noise`.  It is frozen and mutation-closed against the program
# state the real build order produces: `generate_typed_slice` applies
# `runtime_loop_bound` FIRST, so this record freezes the post-attachment tree
# -- functions digest, whole-program
# digest (which embeds `counted_loop_proof`) and the `(1, 0, 1, 8, 8, True)`
# summary all include the eight-trip `multires` proof.
#
# The JS authority (measured against the pinned snapshot this session):
# `canonicalFactory265` (`canonical-kernels.js:31929`, registered `:36445`),
# `Function.prototype.toString` SHA-256
# `392c3be9936855debc0956bc41e4b658896ccdd673674a2ad983101aac521e14`
# (23,299 bytes; byte-identical to the file slice modulo one trailing
# newline).  The materialization is Shape's `globalCoord` contract verbatim:
#
#     var globalCoord = new Float32Array([0, 0]);          // :31959
#     (globalCoord[0] = gl_FragCoord[0] + tileOffset[0],   // main, :32388
#      globalCoord[1] = gl_FragCoord[1] + tileOffset[1], globalCoord);
#     var st = new $runtime.PooledFloat32Array(            // main, :32390
#         [globalCoord[0] / fullResolution[1], globalCoord[1] / fullResolution[1]]);
#     (st[0] = globalCoord[0] / fullResolution[1], ...     // diamonds, :32265
#
# i.e. a factory-scope plain `Float32Array` (never reset by `beginPixel`),
# per-lane f32 narrowing, initial `[0, 0]`.  The GLSL write is `main`'s FIRST
# statement (normalized `279:5`), so write-before-read holds trivially -- the
# dominance argument is stronger than Shape's, not weaker.  Read census is
# exactly two: `main 281:15` and `diamonds 220:10`; `diamonds` is
# conservative-call-graph UNREACHABLE at the frozen defines (its read is the
# §17 dead-code class -- structural locks, not pixel tests).

_NOISE_COORD_FIELD = FrameField(
    15, "globalCoord", "vec2", "glsl::Vec2", 2, "per-lane-f32",
    "new Float32Array([0, 0])", "float32-array")

_NOISE_LOCKS = {
    NOISE_KEY: {
        "profile": NOISE_PROFILE,
        "source_path": "synth/noise/noise.glsl",
        "raw_bytes": 18131,
        "raw_sha256":
            "410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274",
        "normalized_bytes": 8516,
        "normalized_sha256":
            "5a9c937c83b48e85335f1d69b7a364124a3bcd3e1ece1df85b0d6f7dee929205",
        "functions_sha256":
            "6391eaf2da0f033f5fb5f2b04211bd6e13788b31388dd974eee25ec15e7098f7",
        "whole_sha256":
            "7e7ff4474ef6bde8ab1a1f46bfb55bf7e5ba212dba79a31600c0e2a075e2b5b9",
        "interface_sha256":
            "8327df301a143416b03bdb757d3d287700b89bbf543e16294ec8d94f667bb69f",
        "defines": (("LOOP_OFFSET", "int", "300"),
                    ("NOISE_TYPE", "int", "10")),
        "declaration_count": 15,
        "function_count": 30,
        # Thirteen uniforms, no samplers, one output, no texture, no
        # derivatives.  `resolution` is never read; it stays a required ABI
        # binding exactly as Shape's does.
        "resources": (("time", "seed", "resolution", "tileOffset",
                       "fullResolution", "scaleX", "scaleY", "octaves",
                       "ridges", "loopScale", "speed", "colorMode", "wrap"),
                      (), ("fragColor",), False, False),
        "counted_loop_proof": (1, 0, 1, 8, 8, True),
        # 23 distinct caller->callee edges; the program holds 31 call NODES
        # (the counted-for design's "edges 31" counted nodes -- both frozen
        # here in prose so the landing lane cannot confuse them).
        "call_edge_count": 23,
        "call_graph_sha256":
            "959268602fa47616d2c08c8a42ede441df00f21bcea3e0f1956c00ffbfd6e6e8",
        "reachable": (115, 117, 118, 119, 120, 121, 122, 124, 125, 132, 133),
        "unreachable": (104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
                        114, 116, 123, 126, 127, 128, 129, 130, 131),
        "declaration_inventory": (
            (1, "time", "float", "uniform", False, False, "15:1-15:20"),
            (2, "seed", "int", "uniform", False, False, "16:1-16:18"),
            (3, "resolution", "vec2", "uniform", False, False, "17:1-17:25"),
            (4, "tileOffset", "vec2", "uniform", False, False, "18:1-18:25"),
            (5, "fullResolution", "vec2", "uniform", False, False,
             "19:1-19:29"),
            (6, "scaleX", "float", "uniform", False, False, "20:1-20:22"),
            (7, "scaleY", "float", "uniform", False, False, "21:1-21:22"),
            (8, "octaves", "int", "uniform", False, False, "22:1-22:21"),
            (9, "ridges", "bool", "uniform", False, False, "23:1-23:21"),
            (10, "loopScale", "float", "uniform", False, False, "24:1-24:25"),
            (11, "speed", "float", "uniform", False, False, "25:1-25:21"),
            (12, "colorMode", "int", "uniform", False, False, "26:1-26:23"),
            (13, "wrap", "bool", "uniform", False, False, "27:1-27:19"),
            (14, "fragColor", "vec4", "output", True, False, "28:1-28:16"),
            (15, "globalCoord", "vec2", "global", True, False, "31:1-31:18"),
        ),
        # No global initializers at all: PI/TAU/aspectRatio are #defines in
        # this source, stripped by preprocessing before the typed IR exists.
        "initializer_census": (),
        # The pair lock, noise-shaped: `globalCoord` sits at declarations[14],
        # immediately after the `fragColor` OUTPUT (Shape's adjacency locked a
        # `const float`; this key's preceding declaration is not const and
        # carries no initializer, and the live Noise lock below says so).
        "preceding": (13, 14),
        "preceding_name": "fragColor",
        "preceding_storage": "output",
        "preceding_type": "vec4",
        "preceding_initialized": False,
        "total_nodes": 1139,
        "total_assigns": 45,
        "admitted": (
            _Admitted(
                14, 15, "globalCoord", "vec2", "global", True,
                "31:1-31:18", "31:1-31:18",
                "4b93f176f961f0c5f3e864e7af131cf432d325206a9acc3825857c8cce2de8e8",
                "4c4038035daa8c1cf2e7dd892b1297d9d599e4a1666884715403d683bf8fdd4a",
                _NOISE_COORD_FIELD),
        ),
        "frame": FrameContract(
            _FRAME_STRUCT_NAME, _FRAME_INSTANCE_NAME, _FRAME_INSTANCE_SCOPE,
            True, _FRAME_PARAMETER, _FRAME_PARAMETER_QUALIFIER,
            _FRAME_PARAMETER_ORDINAL, _FRAME_WRITER,
            (_NOISE_COORD_FIELD,)),
        "main": (117, "main", 16, "278:1-308:2"),
        "main_body": (
            ("expr", "279:5-279:48"), ("decl", "280:5-280:43"),
            ("decl", "281:5-281:46"), ("decl", "282:5-282:79"),
            ("decl", "284:5-284:27"), ("decl", "285:5-285:25"),
            ("expr", "287:5-287:48"), ("expr", "288:5-288:48"),
            ("expr", "289:5-289:53"), ("decl", "291:5-291:50"),
            ("block", "292:5-295:6"), ("decl", "298:5-298:19"),
            ("if", "299:5-303:6"), ("decl", "304:5-304:59"),
            ("expr", "306:5-306:71"), ("expr", "307:5-307:23"),
        ),
        # The write IS `main.body[0]`, so the call-free prefix is one
        # statement long -- the strongest form of Shape's dominance premise.
        "call_free_prefix": 1,
        "main_prefix_kinds": (
            ("assign", "id", "binary", "swizzle", "id", "id"),
        ),
        "main_call_statement_indices": (6, 7, 8, 9, 12, 13, 14),
        "writes": (
            _WriteRecord(
                15, "globalCoord", 117, "main", "=", "279:5-279:47", "vec2",
                "6bdf23ef1870a8c47a21287eae99b4552d622653394a9e2e7881bb0f1c49f151",
                "279:5-279:16",
                "ffe327fc3b859926f8d58076f8a88676348ac2a6ce0832a4ef7e9944cbfd88d3",
                0, "expr", "279:5-279:48"),
        ),
        "reads": (
            _ReadRecord(
                15, "globalCoord", 114, "diamonds", "220:10-220:21", "vec2",
                "6cbe686d8f2eff6065e0515630adaaba2dd5eb301d0f283d2d327cd12b6c5e3c",
                ("binary", "/", None, "220:10-220:40"), 0,
                (0, "e0", 1, 0), (("expr", "220:5-220:41"),)),
            _ReadRecord(
                15, "globalCoord", 117, "main", "281:15-281:26", "vec2",
                "9f2d6d2a94ffd54dd8ebfa8dfb9e3d7b2fb3f46a4d973ee29ccd0c31c3cd340d",
                ("binary", "/", None, "281:15-281:45"), 2, (2, "e0", 0, 0),
                (("decl", "281:5-281:46"),)),
        ),
        # One declaration, one symbol, `main`, the assignment node, its
        # target, and the two reads: seven distinct consumed objects.
        "consumed_ledger": 7,
    },
}

_LOCKS.update(_NOISE_LOCKS)
PREPARED_LOCKS = {}
PREPARED_MUTABLE_GLOBAL_FRAME_KEYS = frozenset()


def _noise_fail(message: str) -> ValueError:
    """Fail with the noise key's own profile name, never Shape's.

    The module's `_fail` is prefixed `mutable-global-frame-shape-v1`; a noise
    rejection wearing it is exactly the misattribution `_admitted_symbols`'
    docstring warns about.
    """
    return ValueError(f"{NOISE_PROFILE}: {message}")


def _noise_ordinal_adjacency_holds(program: TypedProgram,
                                   ordinals: tuple[int, ...],
                                   lock: dict) -> bool:
    """`globalCoord` sits at declarations[14], right after the `fragColor`
    output -- the noise-shaped pair lock (the preceding declaration is an
    uninitialized OUTPUT here, not Shape's `const float TAU`)."""
    if ordinals != tuple(item.ordinal for item in lock["admitted"]):
        return False
    index, symbol_id = lock["preceding"]
    if index >= len(program.declarations):
        return False
    preceding = program.declarations[index]
    return (preceding.symbol.id == symbol_id
            and preceding.symbol.name == lock["preceding_name"]
            and preceding.symbol.storage == lock["preceding_storage"]
            and preceding.type.display() == lock["preceding_type"]
            and (preceding.initializer is not None)
            == lock["preceding_initialized"])


def prepared_frame_contract(key: str) -> FrameContract:
    """The frozen emission contract for a prepared frame carrier key."""
    lock = PREPARED_LOCKS.get(key)
    if lock is None:
        raise _fail(f"{key} is not a prepared mutable-global frame carrier")
    return lock["frame"]


def _authenticate_noise_mutable_global_frame(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedDeclaration, ...]:
    """Return Noise's exact frozen mutable-global declaration.

    The lock ladder mirrors the landed Shape authenticator predicate for
    predicate (and reuses its generic helpers), with two noise-specific
    generalizations: the ordinal-adjacency lock names the preceding
    declaration's storage/type/initializer from the record instead of
    Shape's hardcoded `const float`, and the single admitted field is
    dispatched by the reusable `globalCoord` contract lock alone.
    """
    if program.key != NOISE_KEY:
        if profile is not None:
            raise _noise_fail(
                "program key is not an admitted mutable-global frame carrier; "
                f"{NOISE_KEY} 31:1 vec2 globalCoord is the sole Noise "
                "declaration")
        return ()
    lock = _LOCKS[program.key]
    if profile != lock["profile"]:
        raise _noise_fail("exact profile carrier required")

    if not _caller_source_hash_holds(source_hash, lock):
        raise _noise_fail("exact caller source hash required")
    if not _defines_hold(program, lock):
        raise _noise_fail("exact preprocessor define lock mismatch")
    if not _raw_source_holds(program, lock):
        raise _noise_fail("raw source drift")
    if not _normalized_source_holds(program, lock):
        raise _noise_fail("normalized source drift")
    if not _functions_fingerprint_holds(program, lock):
        raise _noise_fail("typed function fingerprint drift")
    if not _whole_program_fingerprint_holds(program, lock):
        raise _noise_fail("whole-program fingerprint drift")
    if not _interface_fingerprint_holds(program, lock):
        raise _noise_fail("interface fingerprint drift")
    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _noise_fail("unrelated proof carrier is not absent")
    if not _function_cardinality_holds(program, lock):
        raise _noise_fail("function cardinality or inventory mismatch")
    if not _resources_hold(program, lock):
        raise _noise_fail("resource profile mismatch")
    if not _call_graph_holds(program, lock):
        raise _noise_fail("call graph or reachability profile mismatch")

    located: list[tuple[int, TypedDeclaration]] = []
    for record in lock["admitted"]:
        matches = [(index, item)
                   for index, item in enumerate(program.declarations)
                   if item.symbol.id == record.symbol_id]
        if len(matches) != 1:
            raise _noise_fail("admitted global declaration identity mismatch")
        located.append(matches[0])
    ordinals = tuple(index for index, _ in located)
    if not _noise_ordinal_adjacency_holds(program, ordinals, lock):
        raise _noise_fail("admitted global declaration ordinal or adjacency mismatch")

    for record, (_, declaration) in zip(lock["admitted"], located):
        if not _mutable_storage_holds(declaration, record):
            raise _noise_fail("admitted global storage or mutability mismatch")
        if not _uninitialized_holds(declaration):
            raise _noise_fail("admitted global declaration carries an initializer")
        if record.name != "globalCoord" or not _global_coord_contract_holds(
                record.field, declaration):
            raise _noise_fail(f"{record.name} numeric contract mismatch")
        if not _declaration_identity_holds(declaration, record):
            raise _noise_fail("admitted global declaration identity mismatch")

    if not _declaration_inventory_holds(program, lock):
        raise _noise_fail("global declaration inventory mismatch")
    if not _initializer_census_holds(program, lock):
        raise _noise_fail("global declaration initializer census mismatch")
    if not _frame_contract_holds(lock["frame"], lock["admitted"]):
        raise _noise_fail("frame emission contract mismatch")

    total, assigns = _node_census(program)
    if not _node_census_holds(total, assigns, lock):
        raise _noise_fail("whole-program node census mismatch")

    entries = [item for item in program.functions
               if item.id == lock["main"][0] and item.name == lock["main"][1]]
    if len(entries) != 1:
        raise _noise_fail("main body shape mismatch")
    main = entries[0]

    symbols = _admitted_symbols(lock)
    writes, reads = _reference_census(program, symbols)
    if not _write_cardinality_holds(writes, lock):
        raise _noise_fail("mutable global write census cardinality mismatch: "
                    f"{len(writes)}")
    if not _single_writer_holds(writes, lock):
        raise _noise_fail("mutable global single-writer proof mismatch")
    if not _no_indirect_write_holds(program, writes, symbols):
        raise _noise_fail("mutable global indirect or partial write present")
    if not _write_position_holds(writes, main, lock):
        raise _noise_fail("mutable global write position mismatch")
    if not _write_identity_holds(writes, lock):
        raise _noise_fail("mutable global write identity mismatch")
    if not _read_cardinality_holds(reads, lock):
        raise _noise_fail("mutable global read census cardinality mismatch: "
                    f"{len(reads)}")
    if not _read_identity_holds(reads, lock):
        raise _noise_fail("mutable global read identity mismatch")
    if not _dominance_holds(main, writes, reads, lock, symbols):
        raise _noise_fail("mutable global write-before-read dominance mismatch")
    if not _main_body_holds(main, lock):
        raise _noise_fail("main body shape mismatch")

    admitted = tuple(declaration for _, declaration in located)
    _check_ledger(
        [*admitted, *(item.symbol for item in admitted), main,
         *(item.node for item in writes), *(item.target for item in writes),
         *(item.node for item in reads)],
        lock["consumed_ledger"], "mutable-global-frame-noise")
    return admitted


def apply_prepared_mutable_global_frame(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the prepared identity profile without changing the tree."""
    authenticate_prepared_mutable_global_frame(program, source_hash, profile)
    return program


def authenticate_prepared_mutable_global_frame(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedDeclaration, ...]:
    """Compatibility surface after all prepared frame records have landed."""
    if profile is not None:
        raise _noise_fail("program key is not a prepared mutable-global frame carrier")
    return ()
