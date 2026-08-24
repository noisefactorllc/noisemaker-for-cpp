"""Exact identity profiles for **const, literal-initialised, file-scope array
tables** read exactly once each through a nine-trip counted loop.

`filter/normalMap:normalMap` is the first carrier, and the first program of
this mechanism. It declares three of them::

    15|const ivec2 SOBEL_OFFSETS[9]  = ivec2[](...);
    21|const float SOBEL_X_KERNEL[9] = float[](...);
    27|const float SOBEL_Y_KERNEL[9] = float[](...);

Nothing in the generator admits a file-scope *array* today, and `reject_type`'s
existing array arm cannot be reached for one: it looks the symbol up in
`proved_array_declarations` via `getattr(value, "symbol_id", None)` and then
requires `getattr(value, "kind", None) == "declaration"`, and a
`TypedDeclaration` carries neither attribute. So this closure keys on
**declaration node identity**, the same route `mutable_global_frame_profile`
uses, and both authorities admit the three nodes by object identity without
widening any frozen vocabulary.

This module follows the **dict-keyed, shared-module** shape of
`mutable_global_frame_profile.py` from the first commit. `filter/osd`,
`classicNoisedeck/cellRefract`, `classicNoisedeck/kaleido` and
`classicNoisedeck/effects` all carry a const or mutable file-scope array behind
one or two further mechanisms; each will want its own per-key record here
rather than a later dict migration.

**No vocabulary growth.** Nothing here touches `APPROVED_CAPABILITIES` (44) or
`APPROVED_TYPES` (17). `float` and `ivec2` are already approved element types
-- it is the *array wrapper at file scope*, not the element type, that is being
admitted -- so the caller must skip `used.add(...)` for a declaration admitted
through this module.

The materialization contract, read from the shipped JavaScript
-------------------------------------------------------------

`canonicalFactory86` (`canonical-kernels.js:15684-15686`, authority commit
`4834b0144ee0524588144a482cca0067b15f68ec`)::

    var SOBEL_OFFSETS = [cpu_ivec2(-1, -1), cpu_ivec2(0, -1), ...];
    var SOBEL_X_KERNEL = [0.5, 0, -0.5, 1, 0, -1, 0.5, 0, -0.5];
    var SOBEL_Y_KERNEL = [0.5, 1, 0.5, 0, 0, 0, -0.5, -1, -0.5];

The two kernels are **plain JS arrays of Numbers -- doubles, never narrowed to
f32**. They are not `Float32Array`. Reading the GLSL type (`float[9]`) is
exactly how a port gets this wrong, and `_NATIVE_ELEMENT_TYPE` maps `float` to
`double` for that reason, matching the emitter's own `local_type()`. Every
element of both kernels happens to be exactly representable in binary32, so no
*value* in this program can distinguish the double contract from an f32 one:
the contract is proved structurally by the emitted native type, never by a
green pixel run.

Why per-pixel re-evaluation is a no-op, and why "literal-only" is not the reason
--------------------------------------------------------------------------------

The emitter lowers admitted source globals to `const` locals inside the pixel
body, so the port re-evaluates these three tables once per pixel while the
JavaScript builds them once per factory. That is observationally identical
here, but **not because the initializers are literals**.

`SOBEL_OFFSETS`'s elements are *pooled* `Int32Array`s (`#allocInteger`,
`glsl-runtime.js:430-436`). They survive the render only because
`beginPixel` snapshots `signedBaseIndices` on first call and restores the
integer pool index to that base (`glsl-runtime.js:132-137`). **The float pool
has no such base** -- `beginPixel` does `this.indices.fill(0)` -- so a
factory-scope `PooledFloat32Array` table is aliased and overwritten by the
first per-pixel scratch allocation. Had these offsets been `vec2`, the
JavaScript itself would clobber the table mid-render and the port's per-pixel
re-evaluation would *not* match the authority.

Literal-only initializers are therefore **necessary but not sufficient**. The
operative reason is element materialization, which is why
`_POOL_SAFE_ELEMENT_TYPES` is an explicit **allowlist** of the nine element
types whose JavaScript counterpart is either a plain Number or a
base-index-protected integer pool entry -- never a denylist, and never "any
approved type". A `vec2[N]` const global would satisfy every other predicate
here and silently disagree with the authority.

Census discipline
-----------------

Every walker below descends `program.declarations` as well as
`program.functions`. That is not defensive style here, it is the whole point:
the validator's generic `expression()` walk iterates `program.functions` only,
and so does its write audit, so a probe reaches CLEAN with the `ivec2[9]`
construct node present and never visited. **Nothing but this closure inspects
that initializer.**
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from . import as_u32_round_profile
from .typed_ir import (TypedDeclaration, TypedExpression, TypedProgram,
                       TypedStatement)


PROFILE = "const-global-nine-table-v1"
NORMAL_MAP_KEY = "filter/normalMap:normalMap"

KEYS = (NORMAL_MAP_KEY,)
PROFILES = {NORMAL_MAP_KEY: PROFILE}
CONST_GLOBAL_TABLE_KEYS = frozenset(PROFILES)

# Wiring data for the validator/emitter companion-exactness matrix. normalMap
# additionally requires the already-frozen `round` carrier, which
# `filter/grain`, `filter/snow` and `filter/fxaa` already share.
REQUIRED_COMPANION_PROFILES = {
    NORMAL_MAP_KEY: (("as_u32_round_profile", "as-u32-round-admission-v1"),),
}

# The complete allowed field set for the slice row -- an ALLOWLIST, not a
# denylist. `generate_typed_slice`'s allowed-field arm compares
# `set(item) != expected`, so an allowlist is exhaustive by construction:
# "every other profile absent" follows from set equality and cannot go stale as
# new profile fields are added elsewhere in the tree. The previous slice's
# review replaced a 5-entry denylist against a 25-field universe for exactly
# this reason; the universe is 32 fields today.
ALLOWED_ROW_FIELDS = {
    NORMAL_MAP_KEY: frozenset({
        "as_u32_round_profile",
        "const_global_table_profile",
        "defines",
        "program_key",
    }),
}

# Design amendment S15. The ONLY element types whose JavaScript materialization
# survives `beginPixel`: plain Numbers (`float`, `int`, `uint`) and
# base-index-protected integer pool entries (`ivec*`, `uvec*`). Float VECTOR
# element types are deliberately absent -- `PooledFloat32Array` tables are
# aliased and clobbered by the first per-pixel scratch allocation, and the rest
# of the predicate set would happily admit one.
_POOL_SAFE_ELEMENT_TYPES = frozenset({
    "float", "int", "uint",
    "ivec2", "ivec3", "ivec4",
    "uvec2", "uvec3", "uvec4",
})

# The emitter's own convention, asserted here rather than inherited silently so
# a future change to `emit_typed_cpp.local_type()` / `_TYPES` turns something
# red. `float` maps to `double` because the shipped JS array holds plain
# Numbers, NOT because GLSL says `float`.
_NATIVE_ELEMENT_TYPE = {
    "float": "double",
    "int": "std::int32_t",
    "uint": "std::uint32_t",
    "ivec2": "glsl::IVec2", "ivec3": "glsl::IVec3", "ivec4": "glsl::IVec4",
    "uvec2": "glsl::UVec2", "uvec3": "glsl::UVec3", "uvec4": "glsl::UVec4",
}

# Lane counts for the vector element types on the allowlist, used by the
# literal-only grammar check to require an exact child count per element.
_ELEMENT_LANES = {"float": 1, "int": 1, "uint": 1,
                  "ivec2": 2, "ivec3": 3, "ivec4": 4,
                  "uvec2": 2, "uvec3": 3, "uvec4": 4}

# Every IR shape that mutates a writable lvalue. `post` is a distinct kind from
# `unary`, not an operator variant of it -- see `_no_write_holds`.
_MUTATION_KINDS = ("assign", "unary", "post")
_INCREMENT_OPERATORS = ("++", "--")

_SIGN_OPERATORS = ("+", "-")

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

# Three declarations, three symbols, three initializers, `main`, the loop, and
# per read site the index node, its base `id` and its induction `id`: twenty
# distinct objects, each consumed once.
_CONSUMED_LEDGER = 20

__all__ = (
    "KEYS", "PROFILES", "CONST_GLOBAL_TABLE_KEYS", "PROFILE",
    "NORMAL_MAP_KEY", "REQUIRED_COMPANION_PROFILES", "ALLOWED_ROW_FIELDS",
    "allowed_row_fields", "ConstGlobalTable", "ConstGlobalTableRead",
    "table_contract", "authenticate_const_global_tables",
    "authenticate_const_global_table_reads", "apply_const_global_tables",
)


class ConstGlobalTable(NamedTuple):
    """One admitted table's complete emission contract (design S4.2).

    `native_element_type` is what the emitter must use for the element, and it
    is a JavaScript fact rather than a GLSL one: `float` becomes `double`
    because the shipped array holds plain Numbers.
    """

    symbol_id: int
    name: str
    glsl_type: str
    native_element_type: str
    element_count: int
    native_alias: str
    native_sizeof: int
    declaration_span: str
    element_spans: tuple[str, ...]


class ConstGlobalTableRead(NamedTuple):
    """One authenticated `TABLE[i]` read site, carrying the LIVE nodes.

    `node`, `base` and `index` are the objects out of the caller's own
    `TypedProgram`, never copies: an authority admits them with `is`, the way
    `authorized_grade_index_sites` is admitted, so its decision rests on
    authenticated node identity rather than on re-deriving structure and
    trusting that this census must have run.

    * `node`  -- the `index` node, `SOBEL_X_KERNEL[i]`
    * `base`  -- its bare `id` operand naming the table
    * `index` -- the loop induction `id`, which the emitter needs to spell the
      subscript and which `_loop_binding_holds` has tied to the nine-trip
      counted loop's `induction_symbol_id`
    """

    symbol_id: int
    name: str
    span: str
    node: TypedExpression
    base: TypedExpression
    index: TypedExpression
    table: ConstGlobalTable


class _Admitted(NamedTuple):
    """One admitted declaration's identity, position, and contract."""

    ordinal: int
    symbol_id: int
    name: str
    glsl_type: str
    element_type: str
    storage: str
    writable: bool
    declaration_span: str
    symbol_span: str
    declaration_sha256: str
    symbol_sha256: str
    initializer_kind: str
    initializer_type: str
    initializer_span: str
    initializer_sha256: str
    table: ConstGlobalTable


class _IndexRecord(NamedTuple):
    symbol_id: int
    name: str
    owner_id: int
    owner_name: str
    span: str
    node_type: str
    category: str
    node_sha256: str
    index_kind: str
    index_symbol_id: int | None
    index_type: str
    index_span: str
    index_category: str
    statement_index: int
    chain: tuple[tuple[str, str], ...]


class _ReferenceRecord(NamedTuple):
    symbol_id: int
    name: str
    owner_id: int
    owner_name: str
    span: str
    node_type: str
    category: str
    node_sha256: str
    parent_kind: str


class _IndexSite(NamedTuple):
    record: _IndexRecord
    node: TypedExpression
    base: TypedExpression
    index: TypedExpression
    chain: tuple[TypedStatement, ...]

    @property
    def symbol_id(self) -> int:
        return self.record.symbol_id

    @property
    def name(self) -> str:
        return self.record.name

    @property
    def span(self) -> str:
        return self.record.span

    @property
    def statement_index(self) -> int:
        return self.record.statement_index


class _ReferenceSite(NamedTuple):
    record: _ReferenceRecord
    node: TypedExpression
    parent: TypedExpression | None

    @property
    def symbol_id(self) -> int:
        return self.record.symbol_id

    @property
    def name(self) -> str:
        return self.record.name

    @property
    def span(self) -> str:
        return self.record.span


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


# --- walkers ----------------------------------------------------------------
#
# Every walker here descends `program.declarations` as well as
# `program.functions`. The validator's generic `expression()` walk and its
# write audit both iterate `program.functions` only, so the three initializers
# are visited by NOTHING ELSE in either authority.

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
        yield from ((item, parent, item_path, chain)
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
            for item, parent, path, chain in _walk_statement(
                    statement, (index,)):
                yield function, None, item, parent, path, chain


def _base_symbol(node: TypedExpression) -> TypedExpression:
    current = node
    while current.kind in ("swizzle", "member", "index") and current.children:
        current = current.children[0]
    return current


def _node_census(program: TypedProgram) -> tuple[int, int]:
    total = 0
    assigns = 0
    for _, _, item, _, _, _ in _program_nodes(program):
        total += 1
        if item.kind == "assign":
            assigns += 1
    return total, assigns


def _binding_table(program: TypedProgram) -> tuple:
    """All declarations in declaration order -- the binding table."""
    return tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable,
         item.initializer is not None, _span(item))
        for item in program.declarations)


def _function_inventory(program: TypedProgram) -> tuple:
    return tuple(
        (item.id, item.name, item.return_type.display(), len(item.parameters),
         len(item.body), _span(item))
        for item in sorted(program.functions, key=lambda value: value.id))


def _initializer_census(program: TypedProgram) -> tuple:
    """Every global initializer, node by node, sorted by symbol id."""
    return tuple(sorted(
        (item.symbol.id, item.symbol.name,
         tuple((node.kind, _span(node), node.literal, repr(node.literal_value),
                node.type.display())
               for node, _, _ in _walk_expression(item.initializer)))
        for item in program.declarations if item.initializer is not None))


def _initializer_census_shape(program: TypedProgram) -> tuple:
    """Per-declaration `(id, name, node count, digest)` -- localises a hit."""
    return tuple((symbol_id, name, len(nodes), _sha(nodes))
                 for symbol_id, name, nodes in _initializer_census(program))


def _call_graph(program: TypedProgram) -> tuple:
    edges = set()
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, _, _, _ in _walk_statement(statement, (index,)):
                if item.kind == "call":
                    edges.add((function.id, function.name, item.signature_id,
                               item.callee))
    return tuple(sorted(edges))


def _reachability(program: TypedProgram) -> tuple[tuple[int, ...],
                                                  tuple[int, ...]]:
    adjacency: dict[int, set[int]] = {}
    for caller, _, callee, _ in _call_graph(program):
        adjacency.setdefault(caller, set()).add(callee)
    seen: set[int] = set()
    stack = [item.id for item in program.functions if item.name == "main"]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(adjacency.get(current, ()))
    identifiers = {item.id for item in program.functions}
    return (tuple(sorted(seen & identifiers)),
            tuple(sorted(identifiers - seen)))


def _reference_census(program: TypedProgram, symbols: dict[int, str]
                      ) -> tuple[list[_IndexSite], list[_ReferenceSite]]:
    """Every `TABLE[i]` site and every bare `id` reference, program-wide.

    The two censuses are deliberately independent rather than derived from one
    another: predicate 7 exists to prove that the bare references are *exactly*
    the bases of the index sites, and a bare census computed from the index
    census could not fail that way.
    """
    sites: list[_IndexSite] = []
    references: list[_ReferenceSite] = []
    for function, _declaration, node, parent, path, chain in _program_nodes(
            program):
        owner_id = -1 if function is None else function.id
        owner_name = ("<global-initializer>" if function is None
                      else function.name)
        # `-1` for a global-initializer node: there is no enclosing statement,
        # and `path[0]` there is an expression CHILD index, which would record
        # a meaningless `0` for a node at depth one.
        statement_index = -1 if function is None or not path else path[0]
        if (node.kind == "index" and len(node.children) == 2
                and node.children[0].symbol_id in symbols):
            base, index = node.children
            sites.append(_IndexSite(
                _IndexRecord(
                    base.symbol_id, symbols[base.symbol_id], owner_id,
                    owner_name, _span(node), node.type.display(),
                    node.category, _sha(node), index.kind, index.symbol_id,
                    index.type.display(), _span(index), index.category,
                    statement_index,
                    tuple((item.kind, _span(item)) for item in chain)),
                node, base, index, chain))
        if node.kind == "id" and node.symbol_id in symbols:
            references.append(_ReferenceSite(
                _ReferenceRecord(
                    node.symbol_id, symbols[node.symbol_id], owner_id,
                    owner_name, _span(node), node.type.display(),
                    node.category, _sha(node),
                    "" if parent is None else parent.kind),
                node, parent))
    return sites, references


# --- individually deletable locks -------------------------------------------
#
# Each predicate below is exactly one lock with exactly one message. A test
# proves a lock load-bearing by re-executing this module into a scratch
# namespace, replacing one of these functions with an always-true stand-in, and
# showing that the lock's message disappears. Keep them small, single-purpose
# and side-effect free.
#
# Ordering matters. `Symbol` embeds its declaration span and `TypedDeclaration`
# embeds its whole initializer, so every value-level lock (storage, element
# type, native contract, initializer shape, literal-only grammar) is evaluated
# AHEAD of the node-hash identity lock that would otherwise absorb it and make
# it vacuous.

def _caller_source_hash_holds(source_hash: str | None, lock: dict) -> bool:
    """The caller's own view of the source agrees with the frozen record."""
    return source_hash == lock["raw_sha256"]


def _defines_hold(program: TypedProgram, lock: dict) -> bool:
    """Exactly `()` for normalMap -- locked PER KEY, never hardcoded.

    `linear_srgb_lane_index_profile` carried a hardcoded
    `program.preprocessor_defines != ()` that had to become a per-key exact
    lock when Shapes was added. This module does not repeat that.
    """
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


def _function_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    """The full ordered function inventory, by id."""
    return _function_inventory(program) == lock["function_inventory"]


def _resources_hold(program: TypedProgram, lock: dict) -> bool:
    """Five uniforms, one sampler, one output, texture reads, no derivatives."""
    resources = program.resources
    return ((resources.uniforms, resources.samplers, resources.outputs,
             resources.uses_texture, resources.uses_derivatives)
            == lock["resources"])


def _call_graph_holds(program: TypedProgram, lock: dict) -> bool:
    """The exact call-graph edge set, its digest, and full reachability."""
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


def _companion_carrier_holds(key: str, lock: dict) -> bool:
    """Design S4.3.9 -- the `round` companion carrier is present and exact.

    Checked against the live `as_u32_round_profile` module rather than against
    a string in the slice row, so a reverted or renamed carrier turns this red
    here instead of surfacing as a generic row-shape failure two layers up.
    """
    companions = REQUIRED_COMPANION_PROFILES.get(key)
    if companions != lock["companions"]:
        return False
    for module_name, profile_name in companions:
        if module_name != "as_u32_round_profile":
            return False
        if profile_name != as_u32_round_profile.PROFILE:
            return False
        if key not in as_u32_round_profile.AS_U32_ROUND_KEYS:
            return False
    return "as_u32_round_profile" in ALLOWED_ROW_FIELDS[key]


def _table_ordinal_order_holds(program: TypedProgram,
                               ordinals: tuple[int, ...], lock: dict) -> bool:
    """The three tables are declarations[8..10], contiguous, in frozen order,
    and are the ONLY array-typed declarations in the program."""
    if ordinals != tuple(item.ordinal for item in lock["admitted"]):
        return False
    if tuple(sorted(ordinals)) != ordinals:
        return False
    arrays = tuple(index for index, item in enumerate(program.declarations)
                   if item.type.kind == "array")
    return arrays == ordinals


def _const_storage_holds(declaration: TypedDeclaration,
                         record: _Admitted) -> bool:
    """File-scope `const` storage and a non-writable symbol (design S4.3.2)."""
    return (declaration.symbol.storage == "const"
            and declaration.symbol.storage == record.storage
            and declaration.symbol.writable is False
            and declaration.symbol.writable == record.writable)


def _element_type_allowlisted_holds(declaration: TypedDeclaration,
                                    record: _Admitted) -> bool:
    """Design amendment S15 -- an ALLOWLIST, never a denylist.

    `SOBEL_OFFSETS`'s elements are pooled `Int32Array`s that survive the render
    only because `beginPixel` restores the integer pool to a snapshotted base
    index. The float pool has no such base (`this.indices.fill(0)`), so a
    factory-scope `PooledFloat32Array` table is aliased and overwritten by the
    first per-pixel scratch allocation. A `vec2[9]` table would satisfy every
    other predicate in this module and silently disagree with the authority.
    """
    array_type = declaration.type
    if array_type.kind != "array" or array_type.element is None:
        return False
    element = array_type.element.display()
    return (element == record.element_type
            and element in _POOL_SAFE_ELEMENT_TYPES
            and element in _NATIVE_ELEMENT_TYPE
            and element in _ELEMENT_LANES)


def _table_contract_holds(declaration: TypedDeclaration,
                          record: _Admitted) -> bool:
    """The emitted native contract: alias, element type, extent, sizeof.

    `float` maps to `double` because the shipped JS array holds plain Numbers.
    `native_sizeof` is asserted as the product so a future element type cannot
    inherit a stale 72.
    """
    table = record.table
    array_type = declaration.type
    if array_type.kind != "array" or array_type.element is None:
        return False
    element = array_type.element.display()
    lanes = _ELEMENT_LANES.get(element)
    native = _NATIVE_ELEMENT_TYPE.get(element)
    if lanes is None or native is None:
        # Reached only if the allowlist lock above has been deleted. Fail
        # closed rather than raising `KeyError` out of a predicate.
        return False
    width = 8 if element == "float" else 4 * lanes
    return (table.symbol_id == record.symbol_id
            and table.name == record.name
            and table.glsl_type == record.glsl_type
            and table.glsl_type == array_type.display()
            and table.element_count == array_type.size
            and table.element_count == 9
            and table.native_element_type == native
            and table.native_sizeof == width * table.element_count
            and table.native_alias.isidentifier()
            and table.declaration_span == _span(declaration)
            and len(table.element_spans) == table.element_count)


def _initializer_construct_holds(declaration: TypedDeclaration,
                                 record: _Admitted) -> bool:
    """Design S4.3.3 -- a `construct` of the declared array type, nine children.

    Also pins the element spans, so an initializer rebuilt from different
    source positions is a hard failure here rather than a coarse-hash one.
    """
    initializer = declaration.initializer
    if initializer is None:
        return False
    return (initializer.kind == "construct"
            and initializer.kind == record.initializer_kind
            and initializer.type.display() == declaration.type.display()
            and initializer.type.display() == record.initializer_type
            and len(initializer.children) == record.table.element_count
            and _span(initializer) == record.initializer_span
            and tuple(_span(child) for child in initializer.children)
            == record.table.element_spans)


def _literal_atom_holds(node: TypedExpression) -> bool:
    """A literal, or a unary `+`/`-` of a literal. Nothing else."""
    if node.kind == "literal":
        return not node.children
    if node.kind == "unary":
        return (node.operator in _SIGN_OPERATORS
                and len(node.children) == 1
                and node.children[0].kind == "literal"
                and not node.children[0].children)
    return False


def _literal_only_initializer_holds(declaration: TypedDeclaration,
                                    record: _Admitted) -> bool:
    """Design S4.3.4 -- literal-only, at every depth.

    No `id` references, no binary arithmetic, no call, no dependency on an
    earlier admitted global. The const-float global grammar elsewhere in the
    generator permits an initializer that reads a previously declared const;
    this mechanism does not, because the emitter re-evaluates these tables once
    per pixel and a reference to anything with per-pixel state would make that
    re-evaluation observable.

    Necessary but NOT sufficient for per-pixel equivalence -- see
    `_element_type_allowlisted_holds` and the module docstring for the
    operative pooling reason.
    """
    initializer = declaration.initializer
    if initializer is None:
        return False
    lanes = _ELEMENT_LANES.get(record.element_type)
    if lanes is None:
        return False
    for element in initializer.children:
        if lanes == 1:
            if not _literal_atom_holds(element):
                return False
            continue
        if (element.kind != "construct"
                or element.type.display() != record.element_type
                or len(element.children) != lanes
                or not all(_literal_atom_holds(item)
                           for item in element.children)):
            return False
    return True


def _declaration_identity_holds(declaration: TypedDeclaration,
                                record: _Admitted) -> bool:
    """Symbol id, name, type, both spans, and three node hashes."""
    initializer = declaration.initializer
    if initializer is None:
        return False
    return ((declaration.symbol.id, declaration.symbol.name,
             declaration.type.display(), _span(declaration),
             _span(declaration.symbol), _sha(declaration),
             _sha(declaration.symbol), _sha(initializer))
            == (record.symbol_id, record.name, record.glsl_type,
                record.declaration_span, record.symbol_span,
                record.declaration_sha256, record.symbol_sha256,
                record.initializer_sha256))


def _binding_table_holds(program: TypedProgram, lock: dict) -> bool:
    """All eleven declarations, in order: an added, removed or retyped global
    anywhere in the program is a hard failure here."""
    return (len(program.declarations) == lock["declaration_count"]
            and _binding_table(program) == lock["bindings"])


def _initializer_census_holds(program: TypedProgram, lock: dict) -> bool:
    """Design S4.3.8 -- every global initializer, node by node.

    This is the ONLY walk in either authority that visits the three
    initializers: the validator's generic `expression()` walk and its write
    audit both iterate `program.functions` only, and a probe reached CLEAN with
    the `ivec2[9]` construct node present and never visited.
    """
    return (_sha(_initializer_census(program))
            == lock["initializer_census_sha256"]
            and _initializer_census_shape(program)
            == lock["initializer_census_shape"])


def _node_census_holds(total: int, assigns: int, lock: dict) -> bool:
    return total == lock["total_nodes"] and assigns == lock["total_assigns"]


def _main_body_holds(main, lock: dict) -> bool:
    identifier, name, length, span = lock["main"]
    return (main.id == identifier and main.name == name
            and len(main.body) == length and _span(main) == span
            and tuple((item.kind, _span(item)) for item in main.body)
            == lock["main_body"])


def _no_write_holds(program: TypedProgram, symbols: dict[int, str]) -> bool:
    """Design S4.3.5 -- no write to any admitted table, at any depth.

    Walks every mutation-shaped node in the program -- global initializers
    included -- and requires that NONE of them has an admitted table at the
    base of its target. These tables are `const`, so unlike the mutable-global
    mechanism there is no authenticated write to allow through.

    The IR spells prefix and postfix increment as **two different kinds**:
    `unary` with operator `++`/`--` (`body_semantic.py:200-209`) and `post`
    (`body_semantic.py:210-212`). Both mutate a writable lvalue and both must
    be caught here -- testing only `unary` lets `SOBEL_X_KERNEL[0]++` through,
    which is exactly the miss the `synth/shape` closure shipped on its first
    draft. Compound assignment (`*=`, `+=`, ...) is kind `assign` with a
    non-`=` operator, so it needs no operator entry of its own.
    """
    for _, _, node, _, _, _ in _program_nodes(program):
        if node.kind not in _MUTATION_KINDS or not node.children:
            continue
        if node.kind != "assign" and node.operator not in _INCREMENT_OPERATORS:
            continue
        if _base_symbol(node.children[0]).symbol_id in symbols:
            return False
    return True


def _index_site_census_holds(sites: list[_IndexSite], lock: dict) -> bool:
    """Design S4.3.6 -- exactly three index sites, one per table.

    The category literal is `"readonly lvalue"`, NOT `"readonly"`
    (`body_semantic.py:156,178`). A predicate written `== "readonly"` fails
    closed but with the wrong message.

    This category check is also what covers `out`/`inout` call arguments --
    `shape-design.md` Amendment 2's carried instruction. `body_semantic.py:325`
    requires `argument.category == "lvalue"` for an `out`/`inout` parameter, so
    a table passed that way could not carry `"readonly lvalue"` here.
    """
    if len(sites) != len(lock["index_sites"]):
        return False
    if tuple(item.record for item in sites) != lock["index_sites"]:
        return False
    if len({item.symbol_id for item in sites}) != len(sites):
        return False
    return all(item.record.category == "readonly lvalue" for item in sites)


def _loop_binding_holds(sites: list[_IndexSite], main, lock: dict) -> bool:
    """Design amendment S13 -- bind the reads to the nine-trip counted loop.

    S4.3.6 pins the index *symbol* and the site spans but never the trip
    count. `std::array::operator[]` is unchecked and the JavaScript returns
    `undefined` -> NaN, so a program satisfying every other predicate with a
    trip count of 12 reads out of bounds natively. This is
    `fixed_nine_table_proof.py:163-168` and `:188` transplanted to file scope.
    """
    index = lock["loop_statement_index"]
    if index < 0 or index >= len(main.body):
        return False
    loop = main.body[index]
    proof = loop.loop_proof
    if (loop.kind != "for" or proof is None
            or proof.start_value != 0 or proof.bound_value != 9
            or proof.comparison != "<" or proof.update != "++"
            or proof.trip_count != 9 or len(loop.children) != 2
            or loop.children[1].kind != "block"):
        return False
    if (_span(loop) != lock["loop_span"]
            or (proof.induction_symbol_id, proof.start_value,
                proof.bound_value, proof.comparison, proof.update,
                proof.bound_kind, proof.trip_count, proof.lexical_depth,
                proof.effective_depth, proof.lexical_product)
            != lock["loop_proof"]
            or tuple(item.kind for item in loop.children)
            != lock["loop_child_kinds"]
            or len(loop.children[1].children) != lock["loop_body_count"]):
        return False
    for site in sites:
        if not site.chain or site.chain[0] is not loop:
            return False
        if (site.index.kind != "id"
                or site.index.symbol_id != proof.induction_symbol_id):
            return False
    return True


def _bare_reference_census_holds(references: list[_ReferenceSite],
                                 sites: list[_IndexSite], lock: dict) -> bool:
    """Design S4.3.7 -- exactly three bare `id` references, program-wide.

    Each must be the base of its own index site. A fourth would mean the array
    escapes as a whole value -- a call argument, a return -- which this
    mechanism does not admit.
    """
    if len(references) != len(lock["bare_references"]):
        return False
    if tuple(item.record for item in references) != lock["bare_references"]:
        return False
    bases = [id(item.base) for item in sites]
    if len(set(bases)) != len(bases):
        return False
    return sorted(id(item.node) for item in references) == sorted(bases)


# --- frozen per-key records --------------------------------------------------
#
# Every value below was computed from the real typed IR by
# `compute_const_global_table_profile.py` (see the slice's task-2 report), never
# hand-transcribed.

_TABLES = (
    ConstGlobalTable(
        symbol_id=9, name='SOBEL_OFFSETS',
        glsl_type='ivec2[9]',
        native_element_type='glsl::IVec2',
        element_count=9, native_alias='SobelOffsets9',
        native_sizeof=72, declaration_span='15:1-19:3',
        element_spans=(
            '16:5-16:18',
            '16:20-16:32',
            '16:34-16:46',
            '17:5-17:18',
            '17:20-17:32',
            '17:34-17:46',
            '18:5-18:18',
            '18:20-18:32',
            '18:34-18:46',
        )),
    ConstGlobalTable(
        symbol_id=10, name='SOBEL_X_KERNEL',
        glsl_type='float[9]',
        native_element_type='double',
        element_count=9, native_alias='SobelXKernel9',
        native_sizeof=72, declaration_span='21:1-25:3',
        element_spans=(
            '22:5-22:8',
            '22:10-22:13',
            '22:15-22:19',
            '23:5-23:8',
            '23:10-23:13',
            '23:15-23:19',
            '24:5-24:8',
            '24:10-24:13',
            '24:15-24:19',
        )),
    ConstGlobalTable(
        symbol_id=11, name='SOBEL_Y_KERNEL',
        glsl_type='float[9]',
        native_element_type='double',
        element_count=9, native_alias='SobelYKernel9',
        native_sizeof=72, declaration_span='27:1-31:3',
        element_spans=(
            '28:5-28:8',
            '28:10-28:13',
            '28:15-28:18',
            '29:5-29:8',
            '29:10-29:13',
            '29:15-29:18',
            '30:4-30:8',
            '30:10-30:14',
            '30:16-30:20',
        )),
)

_ADMITTED = (
    _Admitted(
        ordinal=8, symbol_id=9, name='SOBEL_OFFSETS',
        glsl_type='ivec2[9]', element_type='ivec2',
        storage='const', writable=False,
        declaration_span='15:1-19:3',
        symbol_span='15:1-19:3',
        declaration_sha256=
            '4ffd1d5fb61afbb00c426c967980618e2f2520bfb1a56e04d113cdd0002c6c44',
        symbol_sha256=
            '0fc5633a871e4026ed231d2f9b6d5f94bf89a6fb7eebaa6d082dce35738b88ac',
        initializer_kind='construct', initializer_type='ivec2[9]',
        initializer_span='15:32-19:2',
        initializer_sha256=
            '642fb6f18ecf3aa6b4951f74a18e3f67876ab3af94ac834bf5032c965ff881bd',
        table=_TABLES[0]),
    _Admitted(
        ordinal=9, symbol_id=10, name='SOBEL_X_KERNEL',
        glsl_type='float[9]', element_type='float',
        storage='const', writable=False,
        declaration_span='21:1-25:3',
        symbol_span='21:1-25:3',
        declaration_sha256=
            '7caa49a7f17acf789761c638f9cfb3e4f7e836685b078275791d8f8f2e4de45f',
        symbol_sha256=
            '3bc6a5bfe30d5770211d383969cb274ba059c44375b715010bf7f7936f165ee1',
        initializer_kind='construct', initializer_type='float[9]',
        initializer_span='21:33-25:2',
        initializer_sha256=
            'd08a6b8c4711ad8f670f5ad1335d8c4636a4176b25d59f4a5127c4cd1f7c832b',
        table=_TABLES[1]),
    _Admitted(
        ordinal=10, symbol_id=11, name='SOBEL_Y_KERNEL',
        glsl_type='float[9]', element_type='float',
        storage='const', writable=False,
        declaration_span='27:1-31:3',
        symbol_span='27:1-31:3',
        declaration_sha256=
            '8e0feb909c18af0f74f88c61cb830b7fa498544bc1fcf0f65f88c4eec3c306d3',
        symbol_sha256=
            'f76f34758b46e3738bd7c330b2e0aa8b6ad0ad937052305e948052b082690658',
        initializer_kind='construct', initializer_type='float[9]',
        initializer_span='27:33-31:2',
        initializer_sha256=
            'bc03bf64e418cc374dd85233905b6be360bac118eed957337eb038a2c17eeb0b',
        table=_TABLES[2]),
)

_INDEX_SITES = (
    _IndexRecord(
        symbol_id=9, name='SOBEL_OFFSETS',
        owner_id=28, owner_name='main',
        span='138:24-138:40', node_type='ivec2',
        category='readonly lvalue',
        node_sha256=
            '9ac9347ce128d05f3e56252389166f20b2d46962d79055fffd55498f5f8554fe',
        index_kind='id', index_symbol_id=47,
        index_type='int', index_span='138:38-138:39',
        index_category='lvalue',
        statement_index=13,
        chain=(('for', '137:5-146:6'), ('block', '137:33-146:6'),
               ('decl', '138:9-138:41'))),
    _IndexRecord(
        symbol_id=10, name='SOBEL_X_KERNEL',
        owner_id=28, owner_name='main',
        span='144:23-144:40', node_type='float',
        category='readonly lvalue',
        node_sha256=
            'cb608bd6f227935d3c05a9be8855ebcaec59596128b38a5f8d5297e4e286f612',
        index_kind='id', index_symbol_id=47,
        index_type='int', index_span='144:38-144:39',
        index_category='lvalue',
        statement_index=13,
        chain=(('for', '137:5-146:6'), ('block', '137:33-146:6'),
               ('expr', '144:9-144:41'))),
    _IndexRecord(
        symbol_id=11, name='SOBEL_Y_KERNEL',
        owner_id=28, owner_name='main',
        span='145:23-145:40', node_type='float',
        category='readonly lvalue',
        node_sha256=
            '8ce0fbd0342403c12c2c2aa2629ef1f2dbf3a12f090de445c89c47f467e15a69',
        index_kind='id', index_symbol_id=47,
        index_type='int', index_span='145:38-145:39',
        index_category='lvalue',
        statement_index=13,
        chain=(('for', '137:5-146:6'), ('block', '137:33-146:6'),
               ('expr', '145:9-145:41'))),
)

_BARE_REFERENCES = (
    _ReferenceRecord(
        symbol_id=9, name='SOBEL_OFFSETS',
        owner_id=28, owner_name='main',
        span='138:24-138:37', node_type='ivec2[9]',
        category='readonly lvalue',
        node_sha256=
            '6307d25f1cd32c2e6ce9a79e08f9ec5b5db3348a3b67b3fe11b4305dfb4130b3',
        parent_kind='index'),
    _ReferenceRecord(
        symbol_id=10, name='SOBEL_X_KERNEL',
        owner_id=28, owner_name='main',
        span='144:23-144:37', node_type='float[9]',
        category='readonly lvalue',
        node_sha256=
            '865fdf46f0723b7f0f267b052d2c6ddcd5a2c65dace94eb76da5830765475c58',
        parent_kind='index'),
    _ReferenceRecord(
        symbol_id=11, name='SOBEL_Y_KERNEL',
        owner_id=28, owner_name='main',
        span='145:23-145:37', node_type='float[9]',
        category='readonly lvalue',
        node_sha256=
            '83c7b877343ad61030071925579264b75e1140294ba00e5c86f0663c9e124c47',
        parent_kind='index'),
)

_LOCKS = {
    NORMAL_MAP_KEY: {
        "profile": PROFILE,
        # Provenance only -- NO predicate reads `source_path`, because a
        # TypedProgram carries no path to check it against. The authority is
        # `raw_bytes`/`raw_sha256` below, which ARE locked; the path is here so
        # a reader can find the file, and the focused test asserts the file at
        # this path hashes to the frozen value.
        'source_path': 'sources/filter/normalMap/normalMap.glsl',
        'raw_bytes': 4017,
        'raw_sha256':
            '384312e50972f75dbebd4080cd76d1c2554a439eb36746f2e351d63a03a271cb',
        'normalized_bytes': 4001,
        'normalized_sha256':
            '65a598d7765460203cf38a91883de40bedcb7e135dbbdac2cd90663353567025',
        'functions_sha256':
            '793a4e48595b07c795e6f7c70e5b40e2618d7eac3af52aa26b3cde569b60a48b',
        'whole_sha256':
            'f73f464481e6fd42cca04a70301c55a6650637a229f232fb9cb5100d90a68777',
        'interface_sha256':
            '8fd3e2fea274678d41892ce91bab3bea20732755282ba50a421cc2b252303fc5',
        # Exactly `()`. Locked per key, never hardcoded module-wide.
        'defines': (),
        'declaration_count': 11,
        'function_count': 10,
        'resources': (('tileOffset', 'fullResolution', 'inputTex', 'size',
                       'motion'), ('inputTex',), ('fragColor',), True, False),
        'counted_loop_proof': (1, 0, 1, 9, 9, True),
        'call_edge_count': 10,
        'call_graph_sha256':
            'bd874a7d895cf64206e6b60b51831c143567ca78937003f93cf605428d3b89d4',
        'reachable': (24, 25, 26, 27, 28, 29, 30, 31, 32, 33),
        'unreachable': (),
        'bindings': (
            (1, 'CHANNEL_COUNT', 'uint', 'const', False, True, '4:1-4:31'),
            (2, 'CHANNEL_CAP', 'uint', 'const', False, True, '5:1-5:29'),
            (3, 'tileOffset', 'vec2', 'uniform', False, False, '7:1-7:25'),
            (4, 'fullResolution', 'vec2', 'uniform', False, False, '8:1-8:29'),
            (5, 'inputTex', 'sampler2D', 'uniform', False, False, '9:1-9:28'),
            (6, 'size', 'vec4', 'uniform', False, False, '10:1-10:19'),
            (7, 'motion', 'vec4', 'uniform', False, False, '11:1-11:21'),
            (8, 'fragColor', 'vec4', 'output', True, False, '13:1-13:41'),
            (9, 'SOBEL_OFFSETS', 'ivec2[9]', 'const', False, True,
             '15:1-19:3'),
            (10, 'SOBEL_X_KERNEL', 'float[9]', 'const', False, True,
             '21:1-25:3'),
            (11, 'SOBEL_Y_KERNEL', 'float[9]', 'const', False, True,
             '27:1-31:3'),
        ),
        'function_inventory': (
            (24, 'as_u32', 'uint', 1, 1, '33:1-35:2'),
            (25, 'cbrt_safe', 'float', 1, 3, '70:1-76:2'),
            (26, 'clamp01', 'float', 1, 1, '37:1-39:2'),
            (27, 'compute_reference_value', 'float', 2, 2, '108:1-111:2'),
            (28, 'main', 'void', 0, 19, '113:1-154:2'),
            (29, 'oklab_l_component', 'float', 1, 10, '78:1-92:2'),
            (30, 'sanitize_channelCount', 'uint', 1, 4, '41:1-50:2'),
            (31, 'srgb_to_linear', 'float', 1, 2, '63:1-68:2'),
            (32, 'value_map_component', 'float', 2, 5, '94:1-106:2'),
            (33, 'wrap_coord', 'int', 2, 4, '52:1-61:2'),
        ),
        'initializer_census_sha256':
            '1743a4c7dd80b5ae48b98263d92da0288fdd55338c82a406ae4508b429ad5037',
        'initializer_census_shape': (
            (1, 'CHANNEL_COUNT', 1,
             '2ac13aecc261bc2945d1fda7dfc40f184af6da13a9f73ae0231a3d77bd639513'),
            (2, 'CHANNEL_CAP', 1,
             '796ac735abe16ea264f343ab52a37f5c4cdbff6579b395cf9b33c193dd970349'),
            (9, 'SOBEL_OFFSETS', 34,
             'ab61c82bfbd2972a49fa085937c2dbd11a46c33e560ab569823ac49b98322f9c'),
            (10, 'SOBEL_X_KERNEL', 13,
             'e3cea1d32e00af3932fb9a209388033d02dac68f886325d7dc00bf8100bc36e0'),
            (11, 'SOBEL_Y_KERNEL', 13,
             '689828ff2db6c34f52b8adcebf952291f43e01e70151b185df63460b0255da74'),
        ),
        'total_nodes': 401,
        'total_assigns': 6,
        'main': (28, 'main', 19, '113:1-154:2'),
        'main_body': (
            ('decl', '114:5-114:53'), ('decl', '115:5-115:77'),
            ('decl', '117:5-117:33'), ('decl', '118:5-118:34'),
            ('decl', '119:5-119:43'), ('if', '120:5-122:6'),
            ('if', '123:5-125:6'), ('if', '126:5-128:6'),
            ('decl', '130:5-130:55'), ('decl', '131:5-131:30'),
            ('decl', '132:5-132:32'), ('decl', '134:5-134:20'),
            ('decl', '135:5-135:20'), ('for', '137:5-146:6'),
            ('decl', '148:5-148:53'), ('decl', '149:5-149:53'),
            ('decl', '150:5-150:70'), ('decl', '152:5-152:63'),
            ('expr', '153:5-153:58'),
        ),
        'loop_statement_index': 13,
        'loop_span': '137:5-146:6',
        'loop_proof': (47, 0, 9, '<', '++', 'literal', 9, 1, 1, 9),
        'loop_child_kinds': ('decl', 'block'),
        'loop_body_count': 5,
        "admitted": _ADMITTED,
        "index_sites": _INDEX_SITES,
        "bare_references": _BARE_REFERENCES,
        "companions": REQUIRED_COMPANION_PROFILES[NORMAL_MAP_KEY],
    },
}


def _admitted_symbols(lock: dict) -> dict[int, str]:
    """The `{symbol id: name}` map of one key's admitted tables.

    Derived per call from the selected key's own record rather than bound to
    `NORMAL_MAP_KEY` at import: an import-time global would run normalMap's
    symbol ids 9/10/11 against the next carrier's tree and block that extension
    behind a message naming the wrong declaration.
    """
    return {item.symbol_id: item.name for item in lock["admitted"]}


def table_contract(key: str) -> tuple[ConstGlobalTable, ...]:
    """The frozen emission contract both authorities must honour for ``key``."""
    lock = _LOCKS.get(key)
    if lock is None:
        raise _fail(f"{key} is not an admitted const-global nine-table carrier")
    return tuple(item.table for item in lock["admitted"])


def allowed_row_fields(key: str) -> frozenset[str]:
    """The complete set of slice-row fields permitted for ``key``.

    Exhaustive by construction: the validator's allowed-field arm compares
    `set(item) != expected`, so requiring equality with this set is what
    discharges "every other profile absent".
    """
    fields = ALLOWED_ROW_FIELDS.get(key)
    if fields is None:
        raise _fail(f"{key} is not an admitted const-global nine-table carrier")
    return fields


def _authenticate(
        program: TypedProgram, source_hash: str | None, profile: str | None
) -> tuple[tuple[TypedDeclaration, ...], tuple[ConstGlobalTableRead, ...]]:
    """The single authentication path. Both public accessors project from it.

    Returning declarations AND reads from one function is the point: an
    accessor that ran a subset of the locks would hand an authority nodes the
    other authority never validated, and the two are supposed to be
    independent re-authenticators of the same frozen record, not of different
    ones.
    """
    if program.key not in CONST_GLOBAL_TABLE_KEYS:
        if profile is not None:
            raise _fail(
                "program key is not an admitted const-global nine-table "
                f"carrier; {NORMAL_MAP_KEY} 15:1 SOBEL_OFFSETS, 21:1 "
                "SOBEL_X_KERNEL and 27:1 SOBEL_Y_KERNEL are the sole admitted "
                "declarations")
        return (), ()
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
        raise _fail("function cardinality mismatch")
    if not _function_inventory_holds(program, lock):
        raise _fail("typed function inventory mismatch")
    if not _resources_hold(program, lock):
        raise _fail("resource profile mismatch")
    if not _call_graph_holds(program, lock):
        raise _fail("call graph or reachability profile mismatch")
    if not _companion_carrier_holds(program.key, lock):
        raise _fail("as_u32 round companion carrier mismatch")

    # Locate the admitted declarations by SYMBOL IDENTITY, never by ordinal, so
    # the ordinal lock below is the only thing that can see a reordering.
    located: list[tuple[int, TypedDeclaration]] = []
    for record in lock["admitted"]:
        matches = [(index, item)
                   for index, item in enumerate(program.declarations)
                   if item.symbol.id == record.symbol_id]
        if len(matches) != 1:
            raise _fail("const global table declaration identity mismatch")
        located.append(matches[0])
    ordinals = tuple(index for index, _ in located)
    if not _table_ordinal_order_holds(program, ordinals, lock):
        raise _fail("const global table declaration order or ordinal mismatch")

    # Value-level locks run AHEAD of node identity: `Symbol` embeds its own
    # declaration span and `TypedDeclaration` embeds its whole initializer, so
    # a storage, element-type or initializer mutation also shifts the enclosing
    # node hash, and a coarser ordering would make each of these vacuous.
    for record, (_, declaration) in zip(lock["admitted"], located):
        if not _const_storage_holds(declaration, record):
            raise _fail("const global table storage mismatch")
        if not _element_type_allowlisted_holds(declaration, record):
            raise _fail("const global table element type is not pool-safe")
        if not _table_contract_holds(declaration, record):
            raise _fail("const global table native contract mismatch")
        if not _initializer_construct_holds(declaration, record):
            raise _fail("const global table initializer is not a nine-element "
                        "array construct")
        if not _literal_only_initializer_holds(declaration, record):
            raise _fail("const global table initializer is not literal-only")
        if not _declaration_identity_holds(declaration, record):
            raise _fail("const global table declaration identity mismatch")

    if not _binding_table_holds(program, lock):
        raise _fail("binding table mismatch")
    if not _initializer_census_holds(program, lock):
        raise _fail("global declaration initializer census mismatch")

    total, assigns = _node_census(program)
    if not _node_census_holds(total, assigns, lock):
        raise _fail("whole-program node census mismatch")

    entries = [item for item in program.functions
               if item.id == lock["main"][0] and item.name == lock["main"][1]]
    if len(entries) != 1:
        raise _fail("main body shape mismatch")
    main = entries[0]
    if not _main_body_holds(main, lock):
        raise _fail("main body shape mismatch")

    symbols = _admitted_symbols(lock)
    if not _no_write_holds(program, symbols):
        raise _fail("const global table write present")
    sites, references = _reference_census(program, symbols)
    if not _index_site_census_holds(sites, lock):
        raise _fail("const global table index read census mismatch: "
                    f"{len(sites)}")
    if not _loop_binding_holds(sites, main, lock):
        raise _fail("const global table read is not bound to the nine-trip "
                    "counted loop")
    if not _bare_reference_census_holds(references, sites, lock):
        raise _fail("const global table bare reference census mismatch: "
                    f"{len(references)}")

    admitted = tuple(declaration for _, declaration in located)
    _check_ledger(
        [*admitted, *(item.symbol for item in admitted),
         *(item.initializer for item in admitted), main,
         main.body[lock["loop_statement_index"]],
         *(item.node for item in sites), *(item.base for item in sites),
         *(item.index for item in sites)],
        _CONSUMED_LEDGER, "const-global-nine-table")

    # The read records are built ONLY here, after every lock has passed, and
    # in the frozen record order -- which `_index_site_census_holds` has
    # already proved is the census order, and which is declaration order.
    tables = {item.symbol_id: item.table for item in lock["admitted"]}
    reads = tuple(
        ConstGlobalTableRead(
            site.record.symbol_id, site.record.name, site.record.span,
            site.node, site.base, site.index, tables[site.record.symbol_id])
        for site in sites)
    return admitted, reads


def authenticate_const_global_tables(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedDeclaration, ...]:
    """Return the exact frozen const array declarations of ``program.key``.

    Returns an empty tuple when ``program.key`` is not a carrier, so callers
    can treat the result as a membership set unconditionally; supplying a
    profile for a non-carrier key is a hard failure.

    All three declarations are returned. The validator's rejection names only
    the first (`15:1 const ivec2 SOBEL_OFFSETS[9]`); admitting only that one
    leaves `21:1` and `27:1` to fail at the next iteration of the same loop.
    """
    return _authenticate(program, source_hash, profile)[0]


def authenticate_const_global_table_reads(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[ConstGlobalTableRead, ...]:
    """Return the exact frozen `TABLE[i]` read sites of ``program.key``.

    The three records arrive in frozen declaration order -- `SOBEL_OFFSETS`,
    `SOBEL_X_KERNEL`, `SOBEL_Y_KERNEL` -- and each carries the **live nodes**
    from ``program``: the `index` node, its bare `id` base, and the loop
    induction `id`. Authorities admit them the way `authorized_grade_index_sites`
    and `authorized_linear_srgb_lane_index_sites` are admitted::

        valid = any(value is item.node for item in reads)

    Node identity, not structure. Anchoring the index arm on the authenticated
    *declaration* plus a structural test instead would make that authority's
    admission depend on this census having run, rather than on it consuming
    authenticated nodes -- safe against this one frozen census, not obviously
    safe against the second, third and fourth keys this dict-keyed module
    exists to carry.

    Every lock the declaration accessor runs has already run: both project
    from one `_authenticate` call, so neither can be satisfied by a program the
    other would reject.
    """
    return _authenticate(program, source_hash, profile)[1]


def apply_const_global_tables(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree.

    Returns the SAME object it was given: `generate_typed_slice` asserts
    `profiled is not typed` for every sibling profile and raises
    "identity profile mutated program".
    """
    _authenticate(program, source_hash, profile)
    return program
