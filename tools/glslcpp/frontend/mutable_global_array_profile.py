"""Exact identity profiles for **mutable, uninitialised, file-scope arrays**.

`classicNoisedeck/cellRefract:cellRefract` is the first carrier, and the
first program of this sub-shape. It declares five of them, one line apart,
at the frozen defines ``KERNEL=0`` / ``SHAPE=1``::

    32|float emboss[9];
    33|float sharpen[9];
    34|float blur[9];
    35|float edge[9];
    36|float edge2[9];

``classicNoisedeck/kaleido:kaleido`` is the second carrier (normalized lines
33-37, symbols 13-17, at its own frozen defines ``DIRECTION=2`` /
``KERNEL=0`` / ``LOOP_OFFSET=10`` / ``METRIC=0``); its record was measured
against the pinned corpus by these same helpers -- see
``docs/port-engineering/kaleido-parity/kaleido-design.md``. **Measured
verdict that corrects the cellRefract design's expectation: kaleido's arrays
are WRITE-ONLY at its frozen defines too.** The cellRefract design §3A said
kaleido's "reads live in reachable code"; they do not -- ``KERNEL=0``
strips kaleido's ``convolutionKernel`` branches and its ``main``
``#if KERNEL != 0`` block exactly as it stripped cellRefract's readers, and
the whole-program census is 45 store bases, zero reads, zero whole-array
bases. No read-side lock machinery was needed; the write-only census is
frozen per key, and this module still carries no "reads allowed" switch.
kaleido is also the mechanism's first **two-profile row**: the program
first-blocks on its already-frozen ``scalar-uint-xor-v1`` carrier (verified
against the live slice), so ``allowed_row_fields`` for that key alone
includes ``scalar_uint_xor_profile`` as a REQUIRED companion. Wiring that
companion into the validator's collision list and ``load_slice`` is the
integration slice's work, not this module's.

The validator's "unsupported global declaration" names only the first
array's line. That is the first rejecting site, not the bill of materials:
**all five** must be admitted, by object identity, in one set separate from
the const ``admitted_globals``.

This module follows the **per-key-profile-name, shared-module** shape of
``mutable_global_frame_profile.py`` (which was built dict-keyed for precisely
this follow-on). ``effects`` (row 188) carries the byte-identical
``float emboss[9];`` declaration under its own record
(``mutable-global-nine-array-effects-v1``) with no edit to the two earlier
records' contents -- and, per the designs, **a later record must not be able
to lean on these**: the write-only censuses and the
single-writer-``loadKernels`` dominance frozen below are properties of each
program's frozen defines.
This module deliberately carries no "reads allowed" switch to loosen.

**No vocabulary growth.** Nothing here touches ``APPROVED_CAPABILITIES`` (44)
or ``APPROVED_TYPES`` (17). ``float[9]`` is the already-approved ``float`` in
array clothing -- it is the *storage class*, not the type, that is being
admitted -- so the caller must skip ``used.add(...)`` entirely for a
declaration admitted through this module, symmetric with the
``mutable_global_frame`` precedent.

The crux: a state proof, not a syntax check
-------------------------------------------

Admitting a mutable global array is safe only if nothing reads it before it
is written. At the frozen defines both carriers make that trivially true and
each freezes it as a **write-only census**: the five globals' only readers
(the ``#if KERNEL`` branches of ``convolutionKernel``) were stripped by
normalization, so the whole program contains exactly **45 ``id`` references
to the five array symbols** -- every function body AND every declaration
initializer (there are no initializers, and the census is what proves that)
-- and every one of the 45 is the base of the index target of a plain ``=``
store inside ``loadKernels``. Zero reads, zero whole-array bases, zero
compound/unary/post writes. A read appearing anywhere means the defines
drifted or the mechanism is being reused beyond its proof, and must fail.
(The 45 triples are byte-identical between the two programs -- the same
kernel tables under each program's own symbol ids.)

The writer is proved the same way the frame module proved ``main``:

* **exactly one writer function** ``loadKernels`` (``void``, no parameters;
  id 70 for cellRefract, id 126 for kaleido), whose body is exactly 45
  sole-expression ``expr`` statements;
* the **exact 45 (base, index, value) triples** are frozen -- they are the
  program's kernel tables. 19 of the 45 values are ``unary(-)`` nodes
  wrapping a float literal (GLSL negative constants parse that way), so
  values are extracted as literal-or-unary-minus-of-literal exactly as
  ``_number()`` in ``fixed_array_in_parameter_proof.py`` does -- a lock that
  demanded bare ``literal`` nodes is unsatisfiable by the real program;
* **call dominance**: ``main`` calls ``loadKernels()`` exactly once, as a
  bare no-argument void-context ``expr`` statement at a frozen top-level
  index, before every frozen consumer statement (cellRefract: the
  ``cells``/``map`` calls, the only consumers of state that could observably
  order against the writer; kaleido: nothing reads the arrays, so the frozen
  set is every ``main`` statement bearing a user call -- ``map``, ``offset``,
  ``periodicFunction``, ``kaleidoscope``), and no other function calls the
  writer at all.

One numeric contract, five times over
-------------------------------------

The parity target is the transpiler's materialization: in BOTH carriers the
five globals are factory-scope plain JS arrays of **doubles** (``var emboss =
[0,0,0,0,0,0,0,0,0];``), never narrowed on read or write, immune to the
``beginPixel`` scratch-aliasing hazard because they are not
``PooledFloat32Array``. All 45 constants are small integers exactly
representable in binary32, so the double contract is structurally locked but
not pixel-discriminable -- locked anyway, and said so. The emitted carrier is
``Kernel9`` (``std::array<double, 9>``), the alias the refract shape already
emits, and the frame contract relaxes ``const Frame&`` to ``Frame&`` on the
writer alone.

Sibling-proof allowlist (Amendment 13.2)
----------------------------------------

Unlike the frame template, this module **allows**
``fixed_array_in_parameter_proof`` on the program: the generator auto-attaches
it before validation (``generate_typed_slice.py:5018``), and the cellRefract
record vouches the ``convolve`` parameter and the eight caller tables. The
frozen-absent set is therefore every OTHER ``fixed_*_proof`` field a
``TypedProgram`` can carry -- enumerated from the dataclass, an allowlist by
construction, stronger than the template's four-name list.

Census discipline
-----------------

Per the standing trap, every walker here descends ``program.declarations`` as
well as ``function.body``: the write-only census, the mutation-shape walk and
the node census all count global declaration initializers, so a reference
planted in one cannot hide behind a coarse hash. On this program the frozen
initializer census is empty, and that emptiness is itself a lock.
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from .typed_ir import (TypedDeclaration, TypedExpression, TypedFunction,
                       TypedProgram, TypedStatement)


CELLREFRACT_KEY = "classicNoisedeck/cellRefract:cellRefract"
CELLREFRACT_PROFILE = "mutable-global-nine-array-cellrefract-v1"
KALEIDO_KEY = "classicNoisedeck/kaleido:kaleido"
KALEIDO_PROFILE = "mutable-global-nine-array-kaleido-v1"
EFFECTS_KEY = "classicNoisedeck/effects:effects"
EFFECTS_PROFILE = "mutable-global-nine-array-effects-v1"

# The LANDED carrier registry. `load_slice` enforces that the slice's rows
# carrying `mutable_global_array_profile` equal exactly this key census
# (generate_typed_slice.py:1391-1396, "typed slice mutable-global array
# profile drift"), so a key MUST NOT be registered here before its row lands.
# kaleido's record was landed PREPARED first (held one step short of
# registration against the cellRefract-era slice) and moved here together
# with its row by the integration slice -- the one-line move the
# landed/prepared split exists to make safe. effects (row 188) landed
# registered directly in the same slice as its record: its row, its fixed
# array fourth key and both companion modules' carves landed together.
KEYS = (CELLREFRACT_KEY, KALEIDO_KEY, EFFECTS_KEY)
PROFILES = {CELLREFRACT_KEY: CELLREFRACT_PROFILE,
            KALEIDO_KEY: KALEIDO_PROFILE,
            EFFECTS_KEY: EFFECTS_PROFILE}
MUTABLE_GLOBAL_ARRAY_KEYS = frozenset(PROFILES)

# Records frozen and authenticatable NOW whose rows land in a later slice.
# Empty after kaleido's and effects' integrations; kept for the next
# prepared key.
PREPARED_KEYS: tuple[str, ...] = ()

# The complete allowed field set for the slice row -- an ALLOWLIST, not a
# denylist, exhaustive by construction against the validator's
# `set(item) != expected` comparison. The fixed-array parameter proof is a
# TypedProgram field auto-attached before validation, not a slice-row field,
# so it does not appear here. kaleido's entry is the mechanism's one
# legitimate two-profile row: the program first-blocks on its already-frozen
# `scalar-uint-xor-v1` carrier (measured against the live slice), so that
# companion field is REQUIRED rather than forbidden for that key alone.
# effects (row 188) is the family's first THREE-carrier row: its mat4
# bicubic chain (the glitch module's per-key second record) and its ceil
# admission sites are REQUIRED companions, not merely allowed.
ALLOWED_ROW_FIELDS = {
    CELLREFRACT_KEY: frozenset({
        "defines",
        "program_key",
        "mutable_global_array_profile",
    }),
    KALEIDO_KEY: frozenset({
        "defines",
        "program_key",
        "mutable_global_array_profile",
        "scalar_uint_xor_profile",
    }),
    EFFECTS_KEY: frozenset({
        "defines",
        "program_key",
        "mutable_global_array_profile",
        "glitch_mat4_chain_profile",
        "ceil_admission_profile",
    }),
}
PREPARED_ROW_FIELDS: dict[str, frozenset[str]] = {}

# The required companion carriers, read by BOTH authorities' collision lists
# (the normalMap REQUIRED_COMPANION_PROFILES pattern): present and exact for
# the mapped key, and an unmapped key resolves to no companions and keeps
# the strict absent set -- fail-closed for unmapped fields. effects carries
# TWO companions, both measured as required (the mat4 chain first-blocks at
# `395:10` behind the array gate; the reachable `main` ceil sites at
# `574:13`/`575:13` behind the index arms) -- the first three-carrier row.
REQUIRED_COMPANION_PROFILES = {
    KALEIDO_KEY: (("scalar_uint_xor_profile", "scalar-uint-xor-v1"),),
    EFFECTS_KEY: (("glitch_mat4_chain_profile",
                   "mat4-bicubic-chain-effects-v1"),
                  ("ceil_admission_profile", "ceil-admission-v1")),
}

# The emitted element alias, asserted rather than inherited so a rename of
# `Kernel9` in the emitter turns a test red.
_ARRAY_NATIVE_TYPE = "Kernel9"
_ARRAY_ELEMENT_TYPE = "float"
_ARRAY_EXTENT = 9
# The shipped JavaScript materializes each element as a plain Number.
_ELEMENT_NUMBER_KIND = {"float": "double"}

_FRAME_STRUCT_NAME = "Frame"
_FRAME_INSTANCE_NAME = "frame"
_FRAME_INSTANCE_SCOPE = "pixel"
_FRAME_WRITER = "loadKernels"
_HELPER_PARAMETER = "const Frame& frame"
_HELPER_PARAMETER_ORDINAL = 2
_WRITER_PARAMETER = "Frame& frame"

# Every IR shape that mutates a writable lvalue. `post` is a distinct kind from
# `unary`, not an operator variant of it -- see `_no_indirect_write_holds`.
_MUTATION_KINDS = ("assign", "unary", "post")
_INCREMENT_OPERATORS = ("++", "--")

# Every optional `fixed_*_proof` field a TypedProgram carries EXCEPT the one
# the generator auto-attaches before validation (Amendment 13.2). The test
# suite re-derives this set from the dataclass, so a new proof field added
# elsewhere in the tree turns red here rather than slipping through.
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_affine_centers13_proof",
)

# The cellRefract-era visitation ledger: five declarations, five symbols,
# the writer, `main`, the 45 stores' assign, target, base and value nodes,
# and the one writer call -- 193 distinct objects, each consumed exactly
# once. Kept as the module constant (the landed sabotage tests freeze its
# load-bearing role for BOTH five-array keys); the per-key expectation is
# derived from it and the record's own censuses by `_consumed_ledger` below,
# so effects' seven declarations and 63 stores answer 269 without a second
# bare number, and sabotaging the constant still reddens every key.
_CONSUMED_LEDGER = 193

__all__ = (
    "KEYS", "PROFILES", "MUTABLE_GLOBAL_ARRAY_KEYS", "PREPARED_KEYS",
    "CELLREFRACT_KEY",
    "CELLREFRACT_PROFILE", "KALEIDO_KEY", "KALEIDO_PROFILE",
    "EFFECTS_KEY", "EFFECTS_PROFILE",
    "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS",
    "REQUIRED_COMPANION_PROFILES", "allowed_row_fields",
    "ArrayFrameField", "ArrayFrameContract", "frame_contract",
    "store_census",
    "authenticate_mutable_global_array", "apply_mutable_global_array",
)


class ArrayFrameField(NamedTuple):
    """One admitted array's complete element numeric contract.

    All five carriers of this program share the contract -- plain JS doubles,
    never narrowed -- but it is recorded per declaration so a future key
    whose materialization differs cannot silently inherit this one.
    """

    symbol_id: int
    name: str
    glsl_type: str
    native_type: str
    element_type: str
    extent: int
    narrowing: str
    js_initializer: str
    js_number_kind: str


class ArrayFrameContract(NamedTuple):
    """The frozen emission shape both authorities must honour.

    Every helper takes ``const Frame& frame`` at parameter ordinal 2; the
    writer alone takes ``Frame& frame`` -- the compiler-level enforcement of
    the single-writer lock, relaxed exactly where the 45 stores live.
    """

    struct_name: str
    instance_name: str
    instance_scope: str
    value_initialized: bool
    helper_parameter: str
    helper_parameter_ordinal: int
    writer_parameter: str
    writer_function: str
    fields: tuple[ArrayFrameField, ...]


class _Admitted(NamedTuple):
    """One admitted declaration's identity, position, and contract."""

    ordinal: int
    symbol_id: int
    name: str
    glsl_type: str
    element_type: str
    extent: int
    storage: str
    writable: bool
    declaration_span: str
    symbol_span: str
    declaration_sha256: str
    symbol_sha256: str
    field: ArrayFrameField


class _StoreRecord(NamedTuple):
    """One element store's complete identity: the (base, index, value) triple,
    the operator, the owner, and the assign/target/index/value node hashes."""

    base_id: int
    base_name: str
    index: int | None
    value: float | None
    operator: str
    owner_id: int
    owner_name: str
    assign_span: str
    assign_sha256: str
    target_span: str
    target_sha256: str
    index_span: str
    index_sha256: str
    value_span: str
    value_sha256: str
    statement_index: int
    statement_kind: str
    statement_span: str


class _ReferenceRecord(NamedTuple):
    """Every non-store reference to an admitted array. Frozen empty: the
    write-only census. A read, a whole-array argument, or a whole-symbol
    assignment target all land here and all fail."""

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


class _StoreSite(NamedTuple):
    record: _StoreRecord
    node: TypedExpression
    target: TypedExpression
    base: TypedExpression
    value: TypedExpression
    chain: tuple[TypedStatement, ...]

    @property
    def base_id(self) -> int:
        return self.record.base_id

    @property
    def index(self) -> int | None:
        return self.record.index

    @property
    def value_number(self) -> float | None:
        return self.record.value

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
    def statement_index(self) -> int:
        return self.record.statement_index


class _ReferenceSite(NamedTuple):
    record: _ReferenceRecord
    node: TypedExpression
    chain: tuple[TypedStatement, ...]


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


def _profile_fail(profile: str, message: str) -> ValueError:
    """Prefix every failure with the **per-key** profile name.

    The frame template's module-global prefix is the Amendment 2 hazard: in a
    shared module a failure on one key would name another key's profile. The
    profile is therefore always an argument, never a default.
    """
    return ValueError(f"{profile}: {message}")


def _check_ledger(entries: list, expected: int, label: str,
                  profile: str = CELLREFRACT_PROFILE) -> None:
    """Require ``entries`` to hold exactly ``expected`` distinct objects.

    The profile is the failing key's own name (per-key ``_profile_fail``
    discipline); the default keeps direct helper calls naming the module's
    first key exactly as before."""
    identities = [id(item) for item in entries]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _profile_fail(profile,
                            f"{label} visitation ledger mismatch")


# --- walkers ----------------------------------------------------------------
#
# Every walker here descends `program.declarations` as well as
# `program.functions`. A "whole-program" census that only walks `function.body`
# leaves global declaration initializers in a coarse-hash-only blind spot, and
# for this mechanism the globals are the subject matter.

def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None,
                     grandparent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    """Yield ``(node, parent, grandparent, path)`` for every expression node.

    The grandparent is what lets the census recognize an element store -- the
    base ``id`` under an ``index`` under an ``assign`` -- without re-walking.
    """
    yield value, parent, grandparent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, parent, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, grandparent, item_path in _walk_expression(
                expression, None, None, (*path, f"e{index}")):
            yield item, parent, grandparent, item_path, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _program_nodes(program: TypedProgram):
    """Every expression node in the program, global initializers included."""
    for declaration in program.declarations:
        if declaration.initializer is None:
            continue
        for item, parent, grandparent, path in _walk_expression(
                declaration.initializer):
            yield None, declaration, item, parent, grandparent, path, ()
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, grandparent, path, chain in _walk_statement(
                    statement, (index,)):
                yield function, None, item, parent, grandparent, path, chain


def _statement_node_kinds(statement: TypedStatement, index: int) -> tuple:
    return tuple(item.kind
                 for item, _, _, _, _ in _walk_statement(statement, (index,)))


def _call_statement_indices(function: TypedFunction) -> tuple[int, ...]:
    found = set()
    for index, statement in enumerate(function.body):
        for item, _, _, path, _ in _walk_statement(statement, (index,)):
            if item.kind == "call":
                found.add(path[0])
    return tuple(sorted(found))


def _node_census(program: TypedProgram) -> tuple[int, int]:
    total = 0
    assigns = 0
    for _, _, item, _, _, _, _ in _program_nodes(program):
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


def _function_inventory(program: TypedProgram) -> tuple:
    """All functions in program order: id, name, return type, parameters."""
    return tuple(
        (item.id, item.name, item.return_type.display(),
         tuple((parameter.id, parameter.name, parameter.type.display())
               for parameter in item.parameters))
        for item in program.functions)


def _initializer_census(program: TypedProgram) -> tuple:
    return tuple(sorted(
        (item.symbol.id, item.symbol.name,
         tuple((node.kind, _span(node), node.literal,
                repr(node.literal_value), node.type.display())
               for node, _, _, _ in _walk_expression(item.initializer)))
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


def _number(value: TypedExpression) -> float | None:
    """A float literal, or the unary minus of one -- nothing else.

    Copied exactly from ``fixed_array_in_parameter_proof._number``: 19 of the
    45 store values are ``unary(-)`` nodes (design Amendment 14), so a writer
    lock demanding bare ``literal`` nodes is unsatisfiable by the real
    program.
    """
    if (value.kind == "literal" and value.type.display() == "float"
            and isinstance(value.literal_value, float)):
        return value.literal_value
    if (value.kind == "unary" and value.operator == "-"
            and len(value.children) == 1):
        child = value.children[0]
        if (child.kind == "literal" and child.type.display() == "float"
                and isinstance(child.literal_value, float)):
            return -child.literal_value
    return None


def _literal_index(value: TypedExpression) -> int | None:
    if (value.kind == "literal" and value.type.display() == "int"
            and isinstance(value.literal_value, int)):
        return value.literal_value
    return None


def _reference_census(program: TypedProgram, symbols: dict[int, str]
                      ) -> tuple[list[_StoreSite], list[_ReferenceSite]]:
    """Classify every ``id`` reference to the five arrays.

    A reference is a **store base** only when it is the base of the index
    node that is the whole left-hand side of an assignment --
    ``emboss[0] = -2.0``. Everything else lands in ``references``: a read
    (``kernel[i]`` in rvalue position), a whole-array call argument, a
    whole-symbol assignment target, or an index expression. The write-only
    census is the lock that refuses every one of those.
    """
    stores: list[_StoreSite] = []
    references: list[_ReferenceSite] = []
    for function, declaration, node, parent, grandparent, path, chain in (
            _program_nodes(program)):
        if node.kind != "id" or node.symbol_id not in symbols:
            continue
        owner_id = -1 if function is None else function.id
        owner_name = ("<global-initializer>" if function is None
                      else function.name)
        statement_index = -1 if not path else path[0]
        if (parent is not None and parent.kind == "index"
                and parent.children and parent.children[0] is node
                and grandparent is not None and grandparent.kind == "assign"
                and grandparent.children
                and grandparent.children[0] is parent):
            target = parent
            assign = grandparent
            value = assign.children[1] if len(assign.children) > 1 else node
            stores.append(_StoreSite(
                _StoreRecord(
                    node.symbol_id, symbols[node.symbol_id],
                    _literal_index(target.children[1])
                    if len(target.children) > 1 else None,
                    _number(value), assign.operator, owner_id, owner_name,
                    _span(assign), _sha(assign), _span(target), _sha(target),
                    _span(target.children[1])
                    if len(target.children) > 1 else "",
                    _sha(target.children[1])
                    if len(target.children) > 1 else "",
                    _span(value), _sha(value), statement_index,
                    "" if not chain else chain[-1].kind,
                    "" if not chain else _span(chain[-1])),
                assign, target, node, value, chain))
            continue
        references.append(_ReferenceSite(
            _ReferenceRecord(
                node.symbol_id, symbols[node.symbol_id], owner_id, owner_name,
                _span(node), node.type.display(), _sha(node),
                None if parent is None else _parent_record(parent),
                statement_index, path,
                tuple((item.kind, _span(item)) for item in chain)),
            node, chain))
    return stores, references


def _writer_call_sites(function: TypedFunction, lock: dict) -> list[tuple]:
    """Every call to the frozen writer anywhere inside ``function``."""
    identifier, name = lock["writer"][0], lock["writer"][1]
    sites = []
    for index, statement in enumerate(function.body):
        for item, _, _, path, chain in _walk_statement(statement, (index,)):
            if (item.kind == "call" and item.callee == name
                    and item.signature_id == identifier):
                sites.append((index, statement, item, path, chain))
    return sites


# --- individually deletable locks -------------------------------------------
#
# Each predicate below is exactly one lock with exactly one message. A test
# proves a lock load-bearing by re-executing this module into a scratch
# namespace, replacing one of these functions with an always-true stand-in,
# and showing that the lock's message disappears. Keep them small,
# single-purpose and side-effect free.
#
# Ordering matters. `Symbol` embeds its declaration span, so every value-level
# lock (storage, mutability, initialiser-absence, the element contract, the
# store shapes) is evaluated AHEAD of the node-hash identity locks that would
# otherwise absorb them and make them vacuous.

def _caller_source_hash_holds(source_hash: str | None, lock: dict) -> bool:
    """The caller's own view of the source agrees with the frozen record."""
    return source_hash == lock["raw_sha256"]


def _defines_hold(program: TypedProgram, lock: dict) -> bool:
    """Exactly `KERNEL=0`, `SHAPE=1`, in that order."""
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


def _unrelated_proof_absent_holds(program: TypedProgram) -> bool:
    """Every sibling optional proof is absent -- except the fixed-array
    parameter proof, which the generator auto-attaches before validation
    (Amendment 13.2) and which this module therefore allows."""
    return all(getattr(program, field, None) is None
               for field in _OPTIONAL_PROOF_FIELDS)


def _function_cardinality_holds(program: TypedProgram, lock: dict) -> bool:
    return len(program.functions) == lock["function_count"]


def _function_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    """All twenty-two functions by id, name, return type and parameters."""
    return _function_inventory(program) == lock["function_inventory"]


def _resources_hold(program: TypedProgram, lock: dict) -> bool:
    """One sampler, fourteen scalar/vector uniforms, one output, texture
    reads, no derivatives. `resolution` is declared and never read; it stays
    a required ABI binding, and this lock is what stops it being cleaned up.
    """
    resources = program.resources
    return ((resources.uniforms, resources.samplers, resources.outputs,
             resources.uses_texture, resources.uses_derivatives)
            == lock["resources"])


def _call_graph_holds(program: TypedProgram, lock: dict) -> bool:
    """The exact call-graph edge set, its digest, full reachability, and the
    counted-loop profile. Deliberately does **not** count call *nodes**: the
    single-caller and dominance locks own where calls appear, and folding a
    node count in here would let this lock fire first and hide them.
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
    """The five sit at declarations[16..20], contiguous, immediately after
    the `fragColor` output at 15."""
    if ordinals != tuple(item.ordinal for item in lock["admitted"]):
        return False
    index, symbol_id = lock["preceding"]
    if index >= len(program.declarations):
        return False
    preceding = program.declarations[index]
    return (preceding.symbol.id == symbol_id
            and preceding.symbol.name == lock["preceding_name"]
            and preceding.symbol.storage == "output"
            and preceding.type.display() == "vec4")


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
    thing that separates it from every const-table admission."""
    return declaration.initializer is None


def _element_contract_holds(field: ArrayFrameField,
                            declaration: TypedDeclaration) -> bool:
    """Every element is a plain JS Number -- a DOUBLE, never narrowed.

    The five globals are factory-scope plain JS arrays (`var emboss =
    [0,...]`), not `PooledFloat32Array`, so no store or read narrows. All 45
    constants are exactly representable in binary32, which makes the double
    contract structurally locked but not pixel-discriminable; it is locked
    anyway. All five arrays share this contract, and the predicate is applied
    per declaration so a future key cannot inherit it silently.
    """
    return (declaration.type.kind == "array"
            and declaration.type.size == _ARRAY_EXTENT
            and declaration.type.element.display() == _ARRAY_ELEMENT_TYPE
            and declaration.type.display() == field.glsl_type
            and field.glsl_type == "float[9]"
            and field.element_type == _ARRAY_ELEMENT_TYPE
            and field.extent == _ARRAY_EXTENT
            and field.native_type == _ARRAY_NATIVE_TYPE
            and field.narrowing == "none"
            and field.js_initializer == "0"
            and field.js_number_kind == _ELEMENT_NUMBER_KIND.get(
                field.element_type))


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
    """All twenty-one declarations, order-insensitive: an added or removed
    global anywhere in the program is a hard failure here."""
    return (len(program.declarations) == lock["declaration_count"]
            and _declaration_inventory(program) == lock["declaration_inventory"])


def _initializer_census_holds(program: TypedProgram, lock: dict) -> bool:
    """The frozen initializer census is EMPTY. The census walks global
    declaration initializers node by node, so the emptiness is proved, not
    assumed -- the global-initializer census blind spot is structurally n/a
    only because this lock says so."""
    return _initializer_census(program) == lock["initializer_census"]


def _frame_contract_holds(contract: ArrayFrameContract,
                          records: tuple[_Admitted, ...]) -> bool:
    """The emitted carrier is a value-initialised `pixel`-scope `Frame`;
    every helper takes `const Frame&` at ordinal 2 and the writer alone takes
    `Frame&` -- the compiler-level enforcement of the single-writer lock."""
    return (contract.struct_name == _FRAME_STRUCT_NAME
            and contract.instance_name == _FRAME_INSTANCE_NAME
            and contract.instance_scope == _FRAME_INSTANCE_SCOPE
            and contract.value_initialized is True
            and contract.helper_parameter == _HELPER_PARAMETER
            and contract.helper_parameter_ordinal == _HELPER_PARAMETER_ORDINAL
            and contract.writer_parameter == _WRITER_PARAMETER
            and contract.writer_function == _FRAME_WRITER
            and contract.fields == tuple(item.field for item in records))


def _node_census_holds(total: int, assigns: int, lock: dict) -> bool:
    return total == lock["total_nodes"] and assigns == lock["total_assigns"]


def _writer_function_holds(writer: TypedFunction, lock: dict) -> bool:
    """`loadKernels` is void, takes no parameters, and spans 38:1-64:2."""
    identifier, name, returns, parameters, span = lock["writer"]
    return (writer.id == identifier and writer.name == name
            and writer.return_type.display() == returns
            and len(writer.parameters) == parameters
            and _span(writer) == span)


def _writer_body_holds(writer: TypedFunction, lock: dict) -> bool:
    """The writer's body is exactly 45 statements in the frozen (kind, span)
    order -- one store per statement. The nesting of each store inside its
    statement is the position lock's, not this one's, so a mutation that
    preserves kinds and spans cannot hide behind this lock."""
    return (tuple((item.kind, _span(item)) for item in writer.body)
            == lock["writer_body"])


def _write_cardinality_holds(stores: list[_StoreSite], lock: dict) -> bool:
    return len(stores) == len(lock["stores"])


def _write_owner_holds(stores: list[_StoreSite], lock: dict) -> bool:
    """Every store is owned by `loadKernels`. No helper writes them."""
    owner_id, owner_name = lock["writer"][0], lock["writer"][1]
    return all(item.owner_id == owner_id and item.owner_name == owner_name
               for item in stores)


def _store_position_holds(stores: list[_StoreSite], writer: TypedFunction,
                          lock: dict) -> bool:
    """Every store is an unconditional top-level `expr` statement of the
    writer, at its frozen statement index, nested inside nothing."""
    if len(stores) != len(lock["stores"]):
        return False
    for site, expected in zip(stores, lock["stores"]):
        index = expected.statement_index
        if index < 0 or index >= len(writer.body):
            return False
        statement = writer.body[index]
        if (len(site.chain) != 1 or site.chain[0] is not statement
                or statement.kind != "expr"
                or len(statement.expressions) != 1
                or statement.expressions[0] is not site.node
                or site.record.statement_index != index):
            return False
    return True


def _store_shape_holds(stores: list[_StoreSite], lock: dict) -> bool:
    """Every store: plain `=`, an `id` base among the five, an int-literal
    index in 0..8, and a value that is a literal or the unary minus of a
    literal float (Amendment 14); each base written at exactly the nine
    indices 0..8."""
    allowed = {item.symbol_id for item in lock["admitted"]}
    extent = lock["extent"]
    indices: dict[int, list[int]] = {}
    for site in stores:
        node, target = site.node, site.target
        if node.kind != "assign" or node.operator != "=":
            return False
        if target.kind != "index" or len(target.children) != 2:
            return False
        base = target.children[0]
        if base.kind != "id" or base.symbol_id not in allowed:
            return False
        if site.record.index is None or not 0 <= site.record.index < extent:
            return False
        if site.record.value is None:
            return False
        indices.setdefault(base.symbol_id, []).append(site.record.index)
    if set(indices) != allowed:
        return False
    for values in indices.values():
        if (len(values) != extent
                or tuple(sorted(values)) != tuple(range(extent))):
            return False
    return True


def _store_triples_holds(stores: list[_StoreSite], lock: dict) -> bool:
    """The exact 45 (base, index, value) triples -- the kernel tables."""
    return (tuple((item.base_id, item.record.index, item.record.value)
                  for item in stores) == lock["store_triples"])


def _write_identity_holds(stores: list[_StoreSite], lock: dict) -> bool:
    return tuple(item.record for item in stores) == lock["stores"]


def _no_indirect_write_holds(program: TypedProgram, stores: list[_StoreSite],
                             symbols: dict[int, str]) -> bool:
    """No compound assignment, no `++`/`--`, no whole-array write.

    Walks every mutation-shaped node in the program -- global initializers
    included -- and requires that the only ones whose target *base* is an
    admitted array are the 45 authenticated element stores.

    The IR spells prefix and postfix increment as **two different kinds**:
    `unary` with operator `++`/`--` and `post`. Both mutate a writable lvalue
    and both must be caught here -- testing only `unary` lets `emboss[0]++`
    through this lock. Compound assignment (`+=`, ...) is kind `assign` with
    a non-`=` operator; a whole-symbol write is an `assign` whose target is
    the bare `id`, refused by the `target.kind != "index"` arm.
    """
    authenticated = {id(item.node) for item in stores}
    for _, _, node, _, _, _, _ in _program_nodes(program):
        if node.kind not in _MUTATION_KINDS or not node.children:
            continue
        if node.kind != "assign" and node.operator not in _INCREMENT_OPERATORS:
            continue
        target = node.children[0]
        if _base_symbol(target).symbol_id not in symbols:
            continue
        if (node.kind != "assign" or node.operator != "="
                or target.kind != "index" or id(node) not in authenticated):
            return False
    return True


def _write_only_census_holds(references: list[_ReferenceSite],
                             lock: dict) -> bool:
    """Zero reads, zero whole-array bases: the frozen `KERNEL=0` property."""
    return tuple(item.record for item in references) == lock["references"]


def _single_caller_holds(program: TypedProgram, lock: dict) -> bool:
    """The writer is called exactly once in the whole program, by `main`.
    The call-graph edge set already freezes this; the explicit lock exists so
    a failure names the writer call site, not an opaque digest."""
    callers = set()
    count = 0
    for function in program.functions:
        sites = _writer_call_sites(function, lock)
        count += len(sites)
        if sites:
            callers.add((function.id, function.name))
    return (count == lock["writer_call_count"]
            and callers == {(lock["main"][0], lock["main"][1])})


def _writer_call_holds(main: TypedFunction, lock: dict) -> bool:
    """`main` calls the writer exactly once: a bare, no-argument, void-context
    call that is the sole expression of an unnested `expr` statement at the
    frozen top-level index."""
    sites = _writer_call_sites(main, lock)
    if len(sites) != 1:
        return False
    index, statement, node, path, chain = sites[0]
    record = lock["writer_call"]
    return (index == record["statement_index"]
            and len(chain) == 1 and chain[0] is statement
            and statement.kind == "expr"
            and len(statement.expressions) == 1
            and statement.expressions[0] is node
            and node.type.display() == "void"
            and not node.children
            and _span(node) == record["span"]
            and _sha(node) == record["sha256"])


def _writer_call_dominance_holds(main: TypedFunction, lock: dict) -> bool:
    """The call precedes every `main` statement containing a `cells`/`map`
    call -- the only consumers of state that could observably order against
    it -- and the set of such statements is itself frozen."""
    consumers = []
    identifiers = lock["state_consumer_ids"]
    for index, statement in enumerate(main.body):
        callees = tuple(sorted({
            item.callee
            for item, _, _, _, _ in _walk_statement(statement, (index,))
            if item.kind == "call"
            and (item.callee, item.signature_id) in identifiers}))
        if callees:
            consumers.append((index, callees))
    if tuple(consumers) != lock["state_consumers"]:
        return False
    call_index = lock["writer_call"]["statement_index"]
    return all(index > call_index for index, _ in consumers)


def _main_body_holds(main: TypedFunction, lock: dict) -> bool:
    identifier, name, length, span = lock["main"]
    return (main.id == identifier and main.name == name
            and len(main.body) == length and _span(main) == span
            and tuple((item.kind, _span(item)) for item in main.body)
            == lock["main_body"])


# --- frozen per-key records --------------------------------------------------

_FIELDS = (
    ArrayFrameField(17, "emboss", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(18, "sharpen", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(19, "blur", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(20, "edge", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(21, "edge2", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
)

# --- kaleido frozen record (measured; see kaleido-design.md) ------
_KALEIDO_FIELDS = (
    ArrayFrameField(13, "emboss", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(14, "sharpen", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(15, "blur", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(16, "edge", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(17, "edge2", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
)

# --- effects frozen record (measured; see effects-design.md) -------
# The family's first SEVEN-array member: the five shared kernel tables plus
# `edge3` and `sharpenBlur` (effects-design §2 -- `edge3`/`sharpenBlur` are
# new values, every element still exactly representable in binary32, so the
# plain-Number double structural lock carries over unbroken).
_EFFECTS_FIELDS = (
    ArrayFrameField(15, "emboss", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(16, "sharpen", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(17, "blur", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(18, "edge", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(19, "edge2", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(20, "edge3", "float[9]", "Kernel9", "float", 9, "none",
                    "0", "double"),
    ArrayFrameField(21, "sharpenBlur", "float[9]", "Kernel9", "float", 9,
                    "none", "0", "double"),
)


_LOCKS = {
    CELLREFRACT_KEY: {
        "profile": "mutable-global-nine-array-cellrefract-v1",
        "source_path": "classicNoisedeck/cellRefract/cellRefract.glsl",
        "raw_bytes": 13719,
        "raw_sha256": "aa93167faa07ee22ff0be9c653b5602ac88b1b962e405548cafab43b9e867a70",
        "normalized_bytes": 10221,
        "normalized_sha256": "31cce61e01275d44d46556bfc13edeea4383dcfbcfde024fd7c54a624933bd3c",
        "functions_sha256": "e7e3fd532c4fcc8116655ca64d2b73e6c0905d221cc485014315d29b22b27a6b",
        "whole_sha256": "10049e9bc2ce8fc9539ea315335eef85fff59d1cfbe0844a3d781b0d496aec28",
        "interface_sha256": "09c626e4a6923f856dac399e76972de809ccc8efeb3d49c59d5f69eb8ed17352",
        "defines": (("KERNEL", "int", "0"), ("SHAPE", "int", "1")),
        "declaration_count": 21,
        "function_count": 22,
        "function_inventory": (
            (64, "cells", "float", ((57, "st", "vec2"), (58, "freq", "float"), (59, "cellSize", "float"))),
            (65, "convolutionKernel", "vec3", ((44, "color", "vec3"), (45, "localUV", "vec2"))),
            (66, "convolve", "vec3", ((22, "localUV", "vec2"), (23, "kernel", "float[9]"), (24, "divide", "bool"))),
            (67, "derivatives", "vec3", ((35, "color", "vec3"), (36, "localUV", "vec2"), (37, "divide", "bool"))),
            (68, "desaturate", "vec3", ((34, "color", "vec3"),)),
            (69, "hsv2rgb", "vec3", ((32, "hsv", "vec3"),)),
            (70, "loadKernels", "void", ()),
            (71, "main", "void", ()),
            (72, "map", "float", ((25, "value", "float"), (26, "inMin", "float"), (27, "inMax", "float"), (28, "outMin", "float"), (29, "outMax", "float"))),
            (73, "outline", "vec3", ((42, "color", "vec3"), (43, "localUV", "vec2"))),
            (74, "pcg", "uvec3", ((30, "v", "uvec3"),)),
            (75, "periodicFunction", "float", ((46, "p", "float"),)),
            (76, "pixellate", "vec3", ((62, "localUV", "vec2"), (63, "size", "float"))),
            (77, "polarShape", "float", ((47, "st", "vec2"), (48, "sides", "int"))),
            (78, "posterize", "vec3", ((60, "color", "vec3"), (61, "lev", "float"))),
            (79, "prng", "vec3", ((31, "p", "vec3"),)),
            (80, "rgb2hsv", "vec3", ((33, "rgb", "vec3"),)),
            (81, "shadow", "vec3", ((40, "color", "vec3"), (41, "localUV", "vec2"))),
            (82, "shapeDistance", "float", ((49, "st", "vec2"), (50, "offset", "vec2"), (51, "scale", "float"))),
            (83, "smin", "float", ((54, "a", "float"), (55, "b", "float"), (56, "k", "float"))),
            (84, "sobel", "vec3", ((38, "color", "vec3"), (39, "localUV", "vec2"))),
            (85, "wrapEdges", "vec2", ((52, "st", "vec2"), (53, "freq", "float"))),
        ),
        "resources": (("inputTex",
          "time",
          "seed",
          "resolution",
          "tileOffset",
          "fullResolution",
          "scale",
          "cellScale",
          "cellSmooth",
          "variation",
          "speed",
          "refractAmt",
          "direction",
          "wrap",
          "effectWidth"),
         ("inputTex",),
         ("fragColor",),
         True,
         False),
        "counted_loop_proof": (3, 0, 2, 25, 30, True),
        "call_edge_count": 16,
        "call_graph_sha256": "8dc44ad2a0c4e278006e3b7d93ac9e325407897b92f9764317ac95510e706390",
        "reachable": (64, 70, 71, 72, 74, 79, 83),
        "unreachable": (65, 66, 67, 68, 69, 73, 75, 76, 77, 78, 80, 81, 82, 84, 85),
        "declaration_inventory": (
    (1, "inputTex", "sampler2D", "uniform", False, False, "13:1-13:28"),
            (2, "time", "float", "uniform", False, False, "14:1-14:20"),
            (3, "seed", "int", "uniform", False, False, "15:1-15:18"),
            (4, "resolution", "vec2", "uniform", False, False, "16:1-16:25"),
            (5, "tileOffset", "vec2", "uniform", False, False, "17:1-17:25"),
            (6, "fullResolution", "vec2", "uniform", False, False, "18:1-18:29"),
            (7, "scale", "float", "uniform", False, False, "19:1-19:21"),
            (8, "cellScale", "float", "uniform", False, False, "20:1-20:25"),
            (9, "cellSmooth", "float", "uniform", False, False, "21:1-21:26"),
            (10, "variation", "float", "uniform", False, False, "22:1-22:25"),
            (11, "speed", "float", "uniform", False, False, "23:1-23:21"),
            (12, "refractAmt", "float", "uniform", False, False, "24:1-24:26"),
            (13, "direction", "float", "uniform", False, False, "25:1-25:25"),
            (14, "wrap", "int", "uniform", False, False, "26:1-26:18"),
            (15, "effectWidth", "float", "uniform", False, False, "27:1-27:27"),
            (16, "fragColor", "vec4", "output", True, False, "28:1-28:16"),
            (17, "emboss", "float[9]", "global", True, False, "32:1-32:17"),
            (18, "sharpen", "float[9]", "global", True, False, "33:1-33:18"),
            (19, "blur", "float[9]", "global", True, False, "34:1-34:15"),
            (20, "edge", "float[9]", "global", True, False, "35:1-35:15"),
            (21, "edge2", "float[9]", "global", True, False, "36:1-36:16"),
        ),
        "initializer_census": (),
        "preceding": (15, 16),
        "preceding_name": "fragColor",
        "total_nodes": 1670,
        "total_assigns": 173,
        "extent": 9,
        "admitted": (
            _Admitted(16, 17, "emboss", "float[9]", "float", 9, "global", True,
            "32:1-32:17", "32:1-32:17",
            "16eaaaca2115da66fa303059b1413070c6047ff230f1b2418740a5c0c1c6c631",
            "18ea795b9fd4f896749f8f6203bbd0e7c96307b903e09f6f0b710f7e79609091", _FIELDS[0]),
            _Admitted(17, 18, "sharpen", "float[9]", "float", 9, "global", True,
            "33:1-33:18", "33:1-33:18",
            "fa3106a353479dfe5ada9e045904bdd8323cd1545388bde3a736fdb7caad069a",
            "c63e4bedb54a788e58ae18395c8ecc45a69d17b07e10f4d1a4abcebf65a2fbd7", _FIELDS[1]),
            _Admitted(18, 19, "blur", "float[9]", "float", 9, "global", True,
            "34:1-34:15", "34:1-34:15",
            "e963d9a73ae0083863e0bdd350dc9493e20ff534427a2ddbd020a3ffcd813e2f",
            "d66f7476be909c55829e103371c4abb9003a9b48c9618cc29549c8334d6efea7", _FIELDS[2]),
            _Admitted(19, 20, "edge", "float[9]", "float", 9, "global", True,
            "35:1-35:15", "35:1-35:15",
            "aeb9b8449bd82bb2c8e50c2f3298e0e9eebd54889fc8d0bdbce5be8f696590b2",
            "97df327a601b1b6e4e38e4b5b621d43797bd07986d205b2571d60f1b92fdd95e", _FIELDS[3]),
            _Admitted(20, 21, "edge2", "float[9]", "float", 9, "global", True,
            "36:1-36:16", "36:1-36:16",
            "411872c6effb146bfd039c35fccb72ab55040e3b7d0063a16997689d17f6cbd7",
            "766777202381c0394805c14b42fc51a4fb78afd764fc99deb165339f74289623", _FIELDS[4]),
        ),
        "frame": ArrayFrameContract(
            _FRAME_STRUCT_NAME, _FRAME_INSTANCE_NAME, _FRAME_INSTANCE_SCOPE, True,
            _HELPER_PARAMETER, _HELPER_PARAMETER_ORDINAL, _WRITER_PARAMETER, _FRAME_WRITER,
            _FIELDS),
        "writer": (70, "loadKernels", "void", 0, "38:1-64:2"),
        "writer_body": (
    ("expr", "41:2-41:19"),
            ("expr", "41:20-41:37"),
            ("expr", "41:38-41:54"),
            ("expr", "42:2-42:19"),
            ("expr", "42:20-42:36"),
            ("expr", "42:37-42:53"),
            ("expr", "43:2-43:18"),
            ("expr", "43:19-43:35"),
            ("expr", "43:36-43:52"),
            ("expr", "46:2-46:20"),
            ("expr", "46:21-46:38"),
            ("expr", "46:39-46:57"),
            ("expr", "47:2-47:19"),
            ("expr", "47:20-47:37"),
            ("expr", "47:38-47:55"),
            ("expr", "48:2-48:20"),
            ("expr", "48:21-48:38"),
            ("expr", "48:39-48:57"),
            ("expr", "51:2-51:16"),
            ("expr", "51:17-51:31"),
            ("expr", "51:32-51:46"),
            ("expr", "52:2-52:16"),
            ("expr", "52:17-52:31"),
            ("expr", "52:32-52:46"),
            ("expr", "53:2-53:16"),
            ("expr", "53:17-53:31"),
            ("expr", "53:32-53:46"),
            ("expr", "56:2-56:17"),
            ("expr", "56:18-56:33"),
            ("expr", "56:34-56:49"),
            ("expr", "57:2-57:17"),
            ("expr", "57:18-57:32"),
            ("expr", "57:33-57:48"),
            ("expr", "58:2-58:17"),
            ("expr", "58:18-58:33"),
            ("expr", "58:34-58:49"),
            ("expr", "61:2-61:18"),
            ("expr", "61:19-61:34"),
            ("expr", "61:35-61:51"),
            ("expr", "62:2-62:17"),
            ("expr", "62:18-62:33"),
            ("expr", "62:34-62:49"),
            ("expr", "63:2-63:18"),
            ("expr", "63:19-63:34"),
            ("expr", "63:35-63:51"),
        ),
        "writer_call_count": 1,
        "writer_call": {"statement_index": 3,
         "span": "384:5-384:18",
         "sha256": "bdede4b20800959ad7c9a493ce3db7461c9f02ec0ead5e71eeeb2e4c3468a223"},
        "state_consumer_ids": frozenset({("map", 72), ("cells", 64)}),
        "state_consumers": (
    (5, ("map",)),
            (6, ("map",)),
            (7, ("cells",)),
            (8, ("map",)),
        ),
        "main": (71, "main", 16, "378:1-410:2"),
        "main_body": (
    ("decl", "379:5-379:53"),
            ("decl", "380:5-380:43"),
            ("decl", "382:5-382:44"),
            ("expr", "384:5-384:19"),
            ("decl", "385:5-385:23"),
            ("decl", "387:5-387:52"),
            ("decl", "388:5-388:60"),
            ("decl", "389:5-389:90"),
            ("decl", "390:5-390:57"),
            ("decl", "392:5-392:42"),
            ("expr", "393:5-393:47"),
            ("expr", "394:5-394:47"),
            ("if", "396:5-402:6"),
            ("decl", "405:5-405:88"),
            ("expr", "406:5-406:40"),
            ("expr", "409:5-409:23"),
        ),
        "stores": (
    _StoreRecord(base_id=17, base_name="emboss", index=0, value=-2.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="41:2-41:18", assign_sha256="01cc5744500cf34bff739fb0bb3d1b956fda9a0e79ff47037698162340db9373", target_span="41:2-41:11", target_sha256="80850e80ba4bee9a3758b4820df06f4ba13d0a4a9562f1b06da50913993067f8", index_span="41:9-41:10", index_sha256="0de78fa2064bd5a1294b1fd904486016035fcf8e29bca6266d10511bbe2fa72c", value_span="41:14-41:18", value_sha256="c0f799a68dc4b0b980629ac3a6bce63bba4bce857608d9ca6f1a891f8260f43e", statement_index=0, statement_kind="expr", statement_span="41:2-41:19"),
            _StoreRecord(base_id=17, base_name="emboss", index=1, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="41:20-41:36", assign_sha256="299569d9cfe07ad26a41578ecc39d82714fd2014fe86e558dfc113624f18f6aa", target_span="41:20-41:29", target_sha256="c6b7d976392a510017aa2eb4831dcdb86799be7e815fc0536ee0039492cd7d84", index_span="41:27-41:28", index_sha256="4047ba8a587755afb705c8bb9e8bb38b79effd752a703da46b8ecf72b83dd597", value_span="41:32-41:36", value_sha256="41a375571e23f2b46755db313542b643adb16ea87edefa6d1cd17f2752b5c630", statement_index=1, statement_kind="expr", statement_span="41:20-41:37"),
            _StoreRecord(base_id=17, base_name="emboss", index=2, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="41:38-41:53", assign_sha256="e30fe3da7854c14c179d93e20edc07657addbdcca12507f3cec9a9f6ade2a70e", target_span="41:38-41:47", target_sha256="ad41d64148337955f2d10c5345592449c39c678494bf398d9ca86bce8597e2c2", index_span="41:45-41:46", index_sha256="e7873954c976aa37e5dcbf2e66797c24b11eb3c1bf148198529c317306bbebb3", value_span="41:50-41:53", value_sha256="3b8af09cb5585ca03349d0bbbf761cc73c8db24e95936d21de92380092920423", statement_index=2, statement_kind="expr", statement_span="41:38-41:54"),
            _StoreRecord(base_id=17, base_name="emboss", index=3, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="42:2-42:18", assign_sha256="5d540e8abd546f55f6d012ba77936b84bb08643f2f7d66e8d574c657fbb4cdac", target_span="42:2-42:11", target_sha256="bf87c87ebe8c7bfc8e153a154e55a8fd99fe42f42d1861c5adb00a740840ed40", index_span="42:9-42:10", index_sha256="157a665b8459b246cbc0d98abaf4d27c53eed73056d9c057b66f64725a577fab", value_span="42:14-42:18", value_sha256="bddd20846dd4971c3838a073c481d65326885d2297eda4ed66f270f35ec0a1d4", statement_index=3, statement_kind="expr", statement_span="42:2-42:19"),
            _StoreRecord(base_id=17, base_name="emboss", index=4, value=1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="42:20-42:35", assign_sha256="a74bea78b09ea22bd710ff00c939b774978351f7a1dc89e7fa7a6db795f1404f", target_span="42:20-42:29", target_sha256="977d1e4c605ee68973de2f9d68a684ac7cf5617bc4830fde2f3cf4edbadc2238", index_span="42:27-42:28", index_sha256="af321f4aa7c2ee49c4d57c93745ae17334493fe5a537c8f2ef5fcdbfe25c3049", value_span="42:32-42:35", value_sha256="1e419e902e5c6f11f67f7aba156c6da21fd13ba90ec98f330d9175d7f58d2a87", statement_index=4, statement_kind="expr", statement_span="42:20-42:36"),
            _StoreRecord(base_id=17, base_name="emboss", index=5, value=1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="42:37-42:52", assign_sha256="5c79ca18032e861891044023d7df2a3c0373a07274eaa2fc27c46a451397ab53", target_span="42:37-42:46", target_sha256="5839c7793310abab778dc236f9ddb7104085951ae417247e3631d63fb0adc5d9", index_span="42:44-42:45", index_sha256="95f698e2c581bc9bffb2cfee0be7a74cf78d6571f28448e08bd0a18adbfc1fe8", value_span="42:49-42:52", value_sha256="d80a63fe7488e919ad76251e6b25d8d14c4aa219c861658195b92efdf6a6a874", statement_index=5, statement_kind="expr", statement_span="42:37-42:53"),
            _StoreRecord(base_id=17, base_name="emboss", index=6, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="43:2-43:17", assign_sha256="afe3c1b2393d9663997cbbd391a03a523acca7a53fc31b4564b1bd03162d9741", target_span="43:2-43:11", target_sha256="62b627e38ed5d5628168ed14fa7da8774d02bc4416902e0e9d258e443a41cc19", index_span="43:9-43:10", index_sha256="c51483e66b0e78127d6c803a0d8c976323aa6a09abf3c25792d25f6185df6a0d", value_span="43:14-43:17", value_sha256="5600eb583059606d53609603db0aa2c382beb860bc81bfb1c954b8086def96c4", statement_index=6, statement_kind="expr", statement_span="43:2-43:18"),
            _StoreRecord(base_id=17, base_name="emboss", index=7, value=1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="43:19-43:34", assign_sha256="22979b4e52464f358a8c08bbdc658f38d9956936f2e4aed1c3e7d4d5678a2cbf", target_span="43:19-43:28", target_sha256="1f8083cc6db22773bb00b71b5a60db54cc7a5006c9817a2508738c96c5602b35", index_span="43:26-43:27", index_sha256="5b0c0fa20d440420c7d467c31dd0050d10e1b86ba320cd3a514320b02493f143", value_span="43:31-43:34", value_sha256="d267bda080e862175d119979d59bdde27ed7aba320299c600fe189513f9c36ee", statement_index=7, statement_kind="expr", statement_span="43:19-43:35"),
            _StoreRecord(base_id=17, base_name="emboss", index=8, value=2.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="43:36-43:51", assign_sha256="4cd7e6acf94ff6452c115479d9c72a95322cc75c9ddcc595c63afb5679ecee1c", target_span="43:36-43:45", target_sha256="5017802f9530cb932d8d07817e09ddcaddda3e70d858b3e6a1c47a03b9787396", index_span="43:43-43:44", index_sha256="8d1da7ca36b3ed417fbf48aa7963bd9e401bf369374c88f1b100cb90a6f39dd8", value_span="43:48-43:51", value_sha256="ce3338498c592cea6401b9584beda8aa937c6e23e6750487cb986dcafc729c6f", statement_index=8, statement_kind="expr", statement_span="43:36-43:52"),
            _StoreRecord(base_id=18, base_name="sharpen", index=0, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="46:2-46:19", assign_sha256="45b41a117c771553a12e79be3dd02d6996b01a679b8b34df0f784728f142aea7", target_span="46:2-46:12", target_sha256="11304364a9bab833eda06c61dce4a10e91f4047a7b8180ab0bad6b64d1e1fcc9", index_span="46:10-46:11", index_sha256="e1a8acf49fd140840f2351b2dc99e6d97d2e6e97db88a258af50d6a2f0ccb04e", value_span="46:15-46:19", value_sha256="08bc532fc28a83465f01528899b62eb4a1df8ef89c6594ee12278724e54fc8fc", statement_index=9, statement_kind="expr", statement_span="46:2-46:20"),
            _StoreRecord(base_id=18, base_name="sharpen", index=1, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="46:21-46:37", assign_sha256="4f10684125876105afd762f411a800419fa930f64f43d142c0191eff89385921", target_span="46:21-46:31", target_sha256="64805424b34aa38e664182cd4ba3a1299267d8d03a4d7673513fd8111af4e676", index_span="46:29-46:30", index_sha256="719dbf7e7f0b603a22b9e5109a1070fdee4362dfef84ec5f848ce15e72a221ed", value_span="46:34-46:37", value_sha256="3114452f34366770ee3bee833358cac4b65201f330a81a4c6dd6ca31fcd4eec3", statement_index=10, statement_kind="expr", statement_span="46:21-46:38"),
            _StoreRecord(base_id=18, base_name="sharpen", index=2, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="46:39-46:56", assign_sha256="cd80699d9f293bc95dd4f401ab67b78b76cdcac4455e0d07ce3424a3770382d0", target_span="46:39-46:49", target_sha256="428501364d1a3155fbdca0a853e5ba162378d6dece84bb9f8113a475100a77fa", index_span="46:47-46:48", index_sha256="df86d82eec7721ec05caa2fe241f4041fd2ba5ddff69291ddb6b01888543fe2b", value_span="46:52-46:56", value_sha256="867d4455509002d165ea10bd536e226f381ff45ca183c3414a45744f1628c71a", statement_index=11, statement_kind="expr", statement_span="46:39-46:57"),
            _StoreRecord(base_id=18, base_name="sharpen", index=3, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="47:2-47:18", assign_sha256="b194f3279c92145a0e826e818ff1c5463c8011b76115b8cbf785a352a9a1797f", target_span="47:2-47:12", target_sha256="aafbd028e5f0f98b7f39187501488784fe02c9e7d02eb655d34da6f202ecffb4", index_span="47:10-47:11", index_sha256="33d95d4633c04262968c194d7ab5b5601918dd986523fe25c845a9f22a33f78e", value_span="47:15-47:18", value_sha256="7b95413e1fa5d6cf902b00349292c613e664a61a6cffd378f887bf8bfe1a5f19", statement_index=12, statement_kind="expr", statement_span="47:2-47:19"),
            _StoreRecord(base_id=18, base_name="sharpen", index=4, value=5.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="47:20-47:36", assign_sha256="3be880207c537ce453dbf265cf98991b830f64c4d69026e6e6e9a4fafb00be95", target_span="47:20-47:30", target_sha256="dd88b90b08688c1eb47c167532bab32f27e154b90b4dae8825cd23a015520c33", index_span="47:28-47:29", index_sha256="f25bc89aee9a1d8057231e29eb9b4deefb8fe0ed87c3851128609990afe98bc0", value_span="47:33-47:36", value_sha256="fcbf2ee347085d81bc45119a2bcb51d97a1915adb2f158b9d44bb95a11363284", statement_index=13, statement_kind="expr", statement_span="47:20-47:37"),
            _StoreRecord(base_id=18, base_name="sharpen", index=5, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="47:38-47:54", assign_sha256="9ede985d770efcbeadbff93b4b5fa38ae1f7cb4b72029f0ac59029e72f7d24c4", target_span="47:38-47:48", target_sha256="40857c7543bc5d02e12eddc9ade9ce845bfb7f645ce4d4ad4a95a8e61e632619", index_span="47:46-47:47", index_sha256="e178a842a9d3d0be658b934d007b549dd4551be67869d2e464712e132466b15a", value_span="47:51-47:54", value_sha256="6a2a45adfbb195da5219e41ee92f068469836ffa98f4aab5dad9b7f5ab90b38e", statement_index=14, statement_kind="expr", statement_span="47:38-47:55"),
            _StoreRecord(base_id=18, base_name="sharpen", index=6, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="48:2-48:19", assign_sha256="9d58c2ca264c26528777a47613b7a8a5a8517ee2126df1abd17fbf6b2683af1f", target_span="48:2-48:12", target_sha256="c3a052888c64b56ea40cc8151a75c74b146a201807d598ecbeaee6f03244c819", index_span="48:10-48:11", index_sha256="daa43508ee71f1c00c74c36ee9d88820756378a5fc5d47155e71b7dcaceb7d3c", value_span="48:15-48:19", value_sha256="028047fde47c7a572761adceee8dde96ab36d75fac48e6bd46888df060ee2c7c", statement_index=15, statement_kind="expr", statement_span="48:2-48:20"),
            _StoreRecord(base_id=18, base_name="sharpen", index=7, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="48:21-48:37", assign_sha256="13cbce483d5200c25b8dd2ffd31b71ad7b20e6a47ce677b75fa42ea151794faf", target_span="48:21-48:31", target_sha256="907707656fbb4d05dfade71e01fa6c7952cd97829e9a40daa834bcdf4b041390", index_span="48:29-48:30", index_sha256="5c644c35d47eebbf37fbd2d06453373a3876ba7c73a00f572b342a361875537f", value_span="48:34-48:37", value_sha256="6ce209014adafa33a056eac518a35a54da63390052e9ea375db5c0081c72e240", statement_index=16, statement_kind="expr", statement_span="48:21-48:38"),
            _StoreRecord(base_id=18, base_name="sharpen", index=8, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="48:39-48:56", assign_sha256="4d2abba819e5cc40bfeac6577292eed384712184c40891ca7174465add8a98e1", target_span="48:39-48:49", target_sha256="af2a8a55fc2ddd66a5b8a95e180367acc2644d01bec56b07ed3cd3f43f52103a", index_span="48:47-48:48", index_sha256="b98370461abfa29c0291ab7938f5a361ffd218966f562299bd428ec7db246e2b", value_span="48:52-48:56", value_sha256="b10c41307d6f1994fcec150084f21cece4d51c66561a3e3641c304eb8d687280", statement_index=17, statement_kind="expr", statement_span="48:39-48:57"),
            _StoreRecord(base_id=19, base_name="blur", index=0, value=1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="51:2-51:15", assign_sha256="9871d8d38f152efe595802ac885a97dd1e900aebbad67c5167503692d0019210", target_span="51:2-51:9", target_sha256="e98bd55edfccdea2fdadc1712407ccaf9433d6a62e9f26679346e86b4c8318e3", index_span="51:7-51:8", index_sha256="f7c5f86cc154a244dbb6da329f1433ae69c95bbaca18edd61a87087c8d3b77e5", value_span="51:12-51:15", value_sha256="fa130cd1bbfcafbdc1b9f8bca0a85faa59ffd29f98a07c0dc8e5ea3ba72e4e1e", statement_index=18, statement_kind="expr", statement_span="51:2-51:16"),
            _StoreRecord(base_id=19, base_name="blur", index=1, value=2.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="51:17-51:30", assign_sha256="606a128350917fff04a43848ecb80ff7e22846d1cf92c263f4a1c39453c9310f", target_span="51:17-51:24", target_sha256="ac29237212a13a1926026329d9712a5d829722e9239ccb9ac141351a51ebf7b4", index_span="51:22-51:23", index_sha256="8c24cc0ec930146ac6e08cb1ff6da1ce8450ff7f5ba249552ec28d238566c776", value_span="51:27-51:30", value_sha256="a04dbe2fc9b68e35161ce24329b2be9ee2a58071e35c250c04196ad4469e8904", statement_index=19, statement_kind="expr", statement_span="51:17-51:31"),
            _StoreRecord(base_id=19, base_name="blur", index=2, value=1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="51:32-51:45", assign_sha256="a0434ce8fd0cf720748b2e5709d3abb07596842cc2bbd4865ad2b5b32c8002f3", target_span="51:32-51:39", target_sha256="134a8a625c7f41fec23b22dd39e71c4e4394a09207662d7e867e34f72d9fa0cb", index_span="51:37-51:38", index_sha256="204b267d665a3a95ac1d64a5e8e574a0e656dc2cec4814f19dddaa606999e276", value_span="51:42-51:45", value_sha256="fb768c6a3a67b1082fc8d0fa7b527f9b5b9e0b3c48dfd94f599d76bb580e098d", statement_index=20, statement_kind="expr", statement_span="51:32-51:46"),
            _StoreRecord(base_id=19, base_name="blur", index=3, value=2.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="52:2-52:15", assign_sha256="ecd9a934ee9f99c858ddd6033a06675093861805841a79707d637dc6816adaf0", target_span="52:2-52:9", target_sha256="190d15dc30fdc88b2d700e2a3eb551cf8b01dd07f0c55c0236f3f2b0b5ca4dd7", index_span="52:7-52:8", index_sha256="29b69f4891eca1cf6b54d303aa651f99c0cf55f042e6603d30b08b722a6c61d8", value_span="52:12-52:15", value_sha256="fdd61ec734ce4d8451906d9f4f8a20d167652955daa3627ffeca1f8c3e392f5b", statement_index=21, statement_kind="expr", statement_span="52:2-52:16"),
            _StoreRecord(base_id=19, base_name="blur", index=4, value=4.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="52:17-52:30", assign_sha256="ecb8c6a6c80b63b125bcb2313f0c4d8590a4404f0e5a0a732419c7f5f87f7e5e", target_span="52:17-52:24", target_sha256="7a19cdbcf2968e8d8b95921a0c46b4d9818b9c47cd23ca46074ac9dd004a48c8", index_span="52:22-52:23", index_sha256="323b7ffab4b10545e557685f2f0df75d856c8cac5d20cfb2fb02873b1bccda13", value_span="52:27-52:30", value_sha256="684ce790ff238ff2cd3962f8ea888b932e26b9de41137cffbdd05561412df907", statement_index=22, statement_kind="expr", statement_span="52:17-52:31"),
            _StoreRecord(base_id=19, base_name="blur", index=5, value=2.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="52:32-52:45", assign_sha256="fa0bfb53ec9324a304d60cbcd6ff13f1350868bdb7a003a7b06813ecd031c0c7", target_span="52:32-52:39", target_sha256="23eb8e7d7e13d236aa2e29654fbddcc3149f83f186b9291c066cf78eb9ef5a56", index_span="52:37-52:38", index_sha256="ce1be3f152bea4370acb516356430e36173a3bee048f9714cf18e9ce2f176269", value_span="52:42-52:45", value_sha256="2cb605485f19c04a4e8183bfce42381b606c0cd62cd6d356af682f3d88e44756", statement_index=23, statement_kind="expr", statement_span="52:32-52:46"),
            _StoreRecord(base_id=19, base_name="blur", index=6, value=1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="53:2-53:15", assign_sha256="41285b15a91ae114ab67e282584238cb4e80ac9dddaa95b14eee8deef2aa5f4b", target_span="53:2-53:9", target_sha256="2d2fb0409787fef4b8c39097b30c49c4e305431678e39cef0a7d52d4222e2841", index_span="53:7-53:8", index_sha256="b834362cc48b641859dd7b43c7c9298a4a547ea19528e1cd24312de4a7a17a5c", value_span="53:12-53:15", value_sha256="e0209e2dc4a99390f362f26dc6b393aeba73f43c1015647c53f80499dc044ad9", statement_index=24, statement_kind="expr", statement_span="53:2-53:16"),
            _StoreRecord(base_id=19, base_name="blur", index=7, value=2.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="53:17-53:30", assign_sha256="ee811cabebc2703bb3e78c0180411d416d20a98c4bb5dae66301bbbad16e5d83", target_span="53:17-53:24", target_sha256="cf4f73e8338043b2487c5edb3ad2ecf2fe77b3bcaa6bdb00396de54fdccba3a3", index_span="53:22-53:23", index_sha256="0783c058692e85d6f11fbcfafebb2716c24ee31f83553e6afd4e845b7f4e6f08", value_span="53:27-53:30", value_sha256="d3907e06f276acced3d54f7e63a19d3202466b5ad7208d87ece9107f912c4bc8", statement_index=25, statement_kind="expr", statement_span="53:17-53:31"),
            _StoreRecord(base_id=19, base_name="blur", index=8, value=1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="53:32-53:45", assign_sha256="60500ec8857094a5b7677cd281bf7982642398224cf48b16344cee70497e9e4f", target_span="53:32-53:39", target_sha256="6f373cde6f0e486c228769981cfd6c76e2d2b2314a422f08768178bec6caf937", index_span="53:37-53:38", index_sha256="b9c8afd80aa9d77af1d167a9ed9a7abc784004a205edeeade7ac8965521d95c3", value_span="53:42-53:45", value_sha256="42d4472e98b6b76cf0f3e7d8cd3d60e3fc56e0eada16c954f961e334ac91ed98", statement_index=26, statement_kind="expr", statement_span="53:32-53:46"),
            _StoreRecord(base_id=20, base_name="edge", index=0, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="56:2-56:16", assign_sha256="50e5f2ce74a0fcc4622488d8e78d81df4fc4b9df5cc56dfb54c74e72f6460f18", target_span="56:2-56:9", target_sha256="ebaa4fae1cdcdfead1a548fd943005c8c30a2d8aaddfd04a6d1d3a6c8b7d50d2", index_span="56:7-56:8", index_sha256="5aa99f92fc425aadf5259b7162bceda050e7ca2ca529d48d6d64478b0b8d23b6", value_span="56:12-56:16", value_sha256="f13c6d522e90baf58b3bcd46c1faba4214343c94b01b35f8551ab58a3f0d72e7", statement_index=27, statement_kind="expr", statement_span="56:2-56:17"),
            _StoreRecord(base_id=20, base_name="edge", index=1, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="56:18-56:32", assign_sha256="82eb735b20a404302964715be2bc085cfecec91e90c5233f388f09582ed2371b", target_span="56:18-56:25", target_sha256="13b1ea983bd4c0a76eefe60f2bbb7d7291969314660c27f8440fe936ef2362f8", index_span="56:23-56:24", index_sha256="3d51efb7bd62c5dd1f1369130161bdb432b35743ed9c79615a5e76e4791542e1", value_span="56:28-56:32", value_sha256="d44a47af97fabbe01f3a3284056dea3432582b8f1abdef376b298ece09bb7626", statement_index=28, statement_kind="expr", statement_span="56:18-56:33"),
            _StoreRecord(base_id=20, base_name="edge", index=2, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="56:34-56:48", assign_sha256="173b8b48ae3703393c9bda59af7d1223fcdf668cedc3c739736903ca5da5715a", target_span="56:34-56:41", target_sha256="0f408c0a8523dc44657cb4cf9a0dcf125ec2c7b6784169b59c6f64e8790665b9", index_span="56:39-56:40", index_sha256="7cf2e0a9150469a60bbc85f26148618ff9899e1ea6eb0b0ae6078373b96d2c50", value_span="56:44-56:48", value_sha256="15ca90d198daacda4e786795d28721772b2eaa6149ebe9bdba6aeb807165bad1", statement_index=29, statement_kind="expr", statement_span="56:34-56:49"),
            _StoreRecord(base_id=20, base_name="edge", index=3, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="57:2-57:16", assign_sha256="c2f2031cf8e03a85f2c6d93b32e7ae4a370734497462de55b2ef0b7b74d8857b", target_span="57:2-57:9", target_sha256="3d18e51568998056abb7d163588e5411133131e97d9f50d41adce8549e33bd27", index_span="57:7-57:8", index_sha256="20bf8cd130791d74f29e53c4023804d1db13e6d195545c0544ae1504feb233c3", value_span="57:12-57:16", value_sha256="f423ea512855aa005b11d674e69946ccf879eba15f01d27bd15e565c4b58f7ab", statement_index=30, statement_kind="expr", statement_span="57:2-57:17"),
            _StoreRecord(base_id=20, base_name="edge", index=4, value=8.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="57:18-57:31", assign_sha256="e8b617cf9555c721daeeafb07e3231ea9ea2a2580fbf3aa8b1004d0efb2d2ec4", target_span="57:18-57:25", target_sha256="40224777e370b8c6c01f369cedb9f689a236b09024581a856098515f6243c8bb", index_span="57:23-57:24", index_sha256="68eae6c8040891329713e06407bbad8c67c7d950159a002e598f7ef0c275ec8d", value_span="57:28-57:31", value_sha256="1ccc15bd819e848ff3e4215f5b0482bf308ca985be75cc6416f78a2ac834d8c8", statement_index=31, statement_kind="expr", statement_span="57:18-57:32"),
            _StoreRecord(base_id=20, base_name="edge", index=5, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="57:33-57:47", assign_sha256="e7de195e85c4a5c1797d2d7f2ce980de2997152afc2676820fa1d06d56c97155", target_span="57:33-57:40", target_sha256="23c4c64b87f1e7e9a4118875c328525c348c566e07bad81a74fe973eaae2ceda", index_span="57:38-57:39", index_sha256="9772879e9fa9faa90d010fdd67af3d7ca0cbdb5f32eb2b02a966097ec699a093", value_span="57:43-57:47", value_sha256="3b57f685520cdb8a35714b883f11ddb5017576f01887e7bfe4f474570a820d70", statement_index=32, statement_kind="expr", statement_span="57:33-57:48"),
            _StoreRecord(base_id=20, base_name="edge", index=6, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="58:2-58:16", assign_sha256="c1b5bf5569c075d6b879a4612ec09a7502178d9c62d200111bd4ace55063232b", target_span="58:2-58:9", target_sha256="b5ee5cf5840bb851bccde710793973307efa4e0492eb92b8f7e2230a15ee3d43", index_span="58:7-58:8", index_sha256="7f94d0ec2be6d4b55b3f2aae36cb4c009b9522ad814e45a878dd693eb1ac4ed0", value_span="58:12-58:16", value_sha256="1634ebbdc2d73be219e8d28432ad6ec32cdae96883767907755ebb4228fbfbef", statement_index=33, statement_kind="expr", statement_span="58:2-58:17"),
            _StoreRecord(base_id=20, base_name="edge", index=7, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="58:18-58:32", assign_sha256="d475b3ecff6438c8ee9573f75f500d5fdb86c888b2059d6a8ecf95ad0e58d8de", target_span="58:18-58:25", target_sha256="4982d2ffa1f4e8a453a6569c87704c165946e58d17c5f450a63fe819cbc3c84d", index_span="58:23-58:24", index_sha256="c189bd1510c68fcdc22fc7192ae58fd683798dbbbf75a144587ab088e90f8b92", value_span="58:28-58:32", value_sha256="e3e680a680d1aac2239a50def4b59e56d532c0149a686a70bdd24c12c2879eea", statement_index=34, statement_kind="expr", statement_span="58:18-58:33"),
            _StoreRecord(base_id=20, base_name="edge", index=8, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="58:34-58:48", assign_sha256="152040f0607eae863e1efd7be2de80d7b176d0a35491fd5ba8069e65dfc90ed3", target_span="58:34-58:41", target_sha256="6665ce3fa5b1069b81579fe4965c51658734e509aa40b483335d7db81c891938", index_span="58:39-58:40", index_sha256="2fbeaccc0cdd81cb4b430d37fcddfa1d7d6b899b6bd7f1a421f2e010b17d547f", value_span="58:44-58:48", value_sha256="0b0e73bdb500cb2a69c4b0dc2bf51958730b7abaee1336c2a7025a0c2a5dcdf2", statement_index=35, statement_kind="expr", statement_span="58:34-58:49"),
            _StoreRecord(base_id=21, base_name="edge2", index=0, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="61:2-61:17", assign_sha256="4ddb57de98b6c52339157cf20a6462d5f081aaa849eaa274c64f99a5bac9f1c4", target_span="61:2-61:10", target_sha256="1ba899df56b3b77c08fb10f28f94805f173ca956ae6893bc89d36152f2fdf290", index_span="61:8-61:9", index_sha256="488b028ec4c6d25d00b1ce4b576d760841ebb97e55fb3398b65dde0778c68fa7", value_span="61:13-61:17", value_sha256="d2158a1075f48cbecce57f00c13de8d24f8aaf11587adcfc6bf14d0a5e6b63f7", statement_index=36, statement_kind="expr", statement_span="61:2-61:18"),
            _StoreRecord(base_id=21, base_name="edge2", index=1, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="61:19-61:33", assign_sha256="8f6af36bbe5259bf2ff83e91773bcbfc886865c49dc23da5e5f23383240afaf3", target_span="61:19-61:27", target_sha256="8de37f2b48203191e609a09462912c010e2776de6e4755bcf02d07a92ceda34a", index_span="61:25-61:26", index_sha256="7217664125c0a01dabe71563ce838288aec65b4de48b91c083b362bf96ded5b8", value_span="61:30-61:33", value_sha256="01b752cf425ca359a1ab70f382233cd78c7941069939f03ad86c14435668ab5f", statement_index=37, statement_kind="expr", statement_span="61:19-61:34"),
            _StoreRecord(base_id=21, base_name="edge2", index=2, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="61:35-61:50", assign_sha256="67f735413ea649c0a0eeb4d30da411c5e3a9737c8ac12663db3468f960d51b0c", target_span="61:35-61:43", target_sha256="c2d738292efeb3608f83d81010c94a8c12dee0f5cd414cc25e0ba9e05c2f085d", index_span="61:41-61:42", index_sha256="a788b0a9ab76210c0d373e7b936090c5c6aa505f951706c9d945ca28f48316f1", value_span="61:46-61:50", value_sha256="ad28a89421f1129ec355b8bdd176b530c4f1434455c98c17af0b5d2c6d65b4d5", statement_index=38, statement_kind="expr", statement_span="61:35-61:51"),
            _StoreRecord(base_id=21, base_name="edge2", index=3, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="62:2-62:16", assign_sha256="866fc5e528b0010441f96cc7798f2e94c5f1dc9a9ccdfce7074bcfff3b085708", target_span="62:2-62:10", target_sha256="f0c06c0cb85281cfc1d0ad41c460be3759ed9465b1df681d06b6cfb4daec8731", index_span="62:8-62:9", index_sha256="50fb59ee2fca00aa43b57f4d4b2fa3f9a721b23815bf12fdf9254ec584eed055", value_span="62:13-62:16", value_sha256="bccdd1f4999cf1f9a5ce719300e0a05ec07343b574d13ff36cfa095e9ef79c6c", statement_index=39, statement_kind="expr", statement_span="62:2-62:17"),
            _StoreRecord(base_id=21, base_name="edge2", index=4, value=4.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="62:18-62:32", assign_sha256="20eb0d97e185a9f8fb6db8f095734854ec637b33e2e06563fb6bdfa500db97f9", target_span="62:18-62:26", target_sha256="8402f305d37b577918bc3a5ab745d74c68fb9a842ff21cf5f888a1e934f9459f", index_span="62:24-62:25", index_sha256="882eb3c291241def615868ac8c0e67ce073cd253f0ce46fe586781ebe2821ef7", value_span="62:29-62:32", value_sha256="dee12ae6bae033e460e673a8f664181c902829802a5a22f285dddf6c64d5f17a", statement_index=40, statement_kind="expr", statement_span="62:18-62:33"),
            _StoreRecord(base_id=21, base_name="edge2", index=5, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="62:34-62:48", assign_sha256="15a9fc68fc24430a189d73f405439732dd3137255c763f5da98342e0572dee11", target_span="62:34-62:42", target_sha256="713c49ad8ca99a8cc58a03e647c6c91e7c5f0288c7843aefd36942a045e5ca66", index_span="62:40-62:41", index_sha256="b5b5aebd23b673bd41293598a97d64bf8ec01ca7278e29c99b0e17db50e5b95d", value_span="62:45-62:48", value_sha256="83c326e54189f5424cd7556e54d6f621b057381439f472bc92462f1ceb2bd9c5", statement_index=41, statement_kind="expr", statement_span="62:34-62:49"),
            _StoreRecord(base_id=21, base_name="edge2", index=6, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="63:2-63:17", assign_sha256="b27faef6833134ffadc4097bc08fb2e5ef103bd86a6f85763bbf0e7b158d3615", target_span="63:2-63:10", target_sha256="93c2a767eed760592fd381379a029c2f7206b38c6005e0f76b1580b78887aa0b", index_span="63:8-63:9", index_sha256="b5399bec21e9504d48bdf7d8e10b2aeb5a2bd024c29ea183aba7a3e490980f37", value_span="63:13-63:17", value_sha256="9d2562d0b814dedba05bec2e864b049d56a8c36300d82b52df513fbba2041344", statement_index=42, statement_kind="expr", statement_span="63:2-63:18"),
            _StoreRecord(base_id=21, base_name="edge2", index=7, value=0.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="63:19-63:33", assign_sha256="a8fa8d6afee41955efa9a33d7420f3e3db6420eb223dd2be366e5c37b4fa4ffa", target_span="63:19-63:27", target_sha256="f3218e5c6730975438e471466b013d8b949a01984e80070d55b13e5e5e447295", index_span="63:25-63:26", index_sha256="a0902346c725b8b8089b96c96f9571066998f96ccab929b6cbc59bb9e9131217", value_span="63:30-63:33", value_sha256="ecb90e00b18998116aaa6e63242e5518a64aa2e96da7ef90086013eb5d9ae276", statement_index=43, statement_kind="expr", statement_span="63:19-63:34"),
            _StoreRecord(base_id=21, base_name="edge2", index=8, value=-1.0, operator="=", owner_id=70, owner_name="loadKernels", assign_span="63:35-63:50", assign_sha256="a333f87782386c63e345dcb35c47d30517bf38c616cdc7af3da8c086904d360d", target_span="63:35-63:43", target_sha256="9d5dd741113fab99b6381a7551450ad37b7900b9df3f715ee79c46969a4615f7", index_span="63:41-63:42", index_sha256="cd5964815213ae1dc005dcd8b30adffa35949a22c95874c800019f128853e3ed", value_span="63:46-63:50", value_sha256="9822ff952ee91649b10cceb62c75b4924e9d2cef0d7056c2206438911ec17cee", statement_index=44, statement_kind="expr", statement_span="63:35-63:51"),
        ),
        "store_triples": (
    (17, 0, -2.0),
            (17, 1, -1.0),
            (17, 2, 0.0),
            (17, 3, -1.0),
            (17, 4, 1.0),
            (17, 5, 1.0),
            (17, 6, 0.0),
            (17, 7, 1.0),
            (17, 8, 2.0),
            (18, 0, -1.0),
            (18, 1, 0.0),
            (18, 2, -1.0),
            (18, 3, 0.0),
            (18, 4, 5.0),
            (18, 5, 0.0),
            (18, 6, -1.0),
            (18, 7, 0.0),
            (18, 8, -1.0),
            (19, 0, 1.0),
            (19, 1, 2.0),
            (19, 2, 1.0),
            (19, 3, 2.0),
            (19, 4, 4.0),
            (19, 5, 2.0),
            (19, 6, 1.0),
            (19, 7, 2.0),
            (19, 8, 1.0),
            (20, 0, -1.0),
            (20, 1, -1.0),
            (20, 2, -1.0),
            (20, 3, -1.0),
            (20, 4, 8.0),
            (20, 5, -1.0),
            (20, 6, -1.0),
            (20, 7, -1.0),
            (20, 8, -1.0),
            (21, 0, -1.0),
            (21, 1, 0.0),
            (21, 2, -1.0),
            (21, 3, 0.0),
            (21, 4, 4.0),
            (21, 5, 0.0),
            (21, 6, -1.0),
            (21, 7, 0.0),
            (21, 8, -1.0),
        ),
        "references": (),
    },
    KALEIDO_KEY: {
        "profile": "mutable-global-nine-array-kaleido-v1",
        "source_path": "classicNoisedeck/kaleido/kaleido.glsl",
        "raw_bytes": 27567,
        "raw_sha256": "3a155a9bf64f9e700dd66a77c4195df113d9e85228bde56b1cf410944aaeb8b9",
        "normalized_bytes": 21817,
        "normalized_sha256": "d31299ee69dd0c41965209860ef60a4ad2abf762229cc340383dce2646c6cc1d",
        "functions_sha256": "2ffb48e5f118844d675f9741ccbf7e831ce2f7cfe4609b24777ddb5fb67887ff",
        "whole_sha256": "bae48e72088ee01b07a1c8cfcba2398df87e2baf64284eebe750665e2aebc749",
        "interface_sha256": "666586f65044abc1a147a7c3007f376fde3833c275f5f25bce9b6027b7eaa717",
        "defines": (
            ("DIRECTION", "int", "2"),
            ("KERNEL", "int", "0"),
            ("LOOP_OFFSET", "int", "10"),
            ("METRIC", "int", "0"),
        ),
        "declaration_count": 17,
        "function_count": 43,
        "function_inventory": (
            (109, "bicubicValue", "float", ((72, "st", "vec2"), (73, "freq", "float"))),
            (
                110,
                "blendBicubic",
                "float",
                (
                    (52, "p0", "float"),
                    (53, "p1", "float"),
                    (54, "p2", "float"),
                    (55, "p3", "float"),
                    (56, "t", "float"),
                ),
            ),
            (
                111,
                "blendLinearOrCosine",
                "float",
                ((62, "a", "float"), (63, "b", "float"), (64, "amount", "float"), (65, "interp", "int")),
            ),
            (
                112,
                "catmullRom3",
                "float",
                ((44, "p0", "float"), (45, "p1", "float"), (46, "p2", "float"), (47, "t", "float")),
            ),
            (113, "catmullRom3x3Value", "float", ((50, "st", "vec2"), (51, "freq", "float"))),
            (
                114,
                "catmullRom4",
                "float",
                (
                    (57, "p0", "float"),
                    (58, "p1", "float"),
                    (59, "p2", "float"),
                    (60, "p3", "float"),
                    (61, "t", "float"),
                ),
            ),
            (115, "catmullRom4x4Value", "float", ((74, "st", "vec2"), (75, "freq", "float"))),
            (116, "circles", "float", ((18, "st", "vec2"), (19, "freq", "float"))),
            (117, "constant", "float", ((38, "st", "vec2"), (39, "freq", "float"))),
            (118, "convolutionKernel", "vec3", ((94, "color", "vec3"), (95, "uv", "vec2"))),
            (
                119,
                "convolve",
                "vec3",
                ((81, "uv", "vec2"), (82, "kernel", "float[9]"), (83, "divide", "bool")),
            ),
            (
                120,
                "derivatives",
                "vec3",
                ((85, "color", "vec3"), (86, "uv", "vec2"), (87, "divide", "bool")),
            ),
            (121, "desaturate", "vec3", ((84, "color", "vec3"),)),
            (122, "diamonds", "float", ((22, "st", "vec2"), (23, "freq", "float"))),
            (123, "getMetric", "float", ((103, "st", "vec2"),)),
            (124, "hsv2rgb", "vec3", ((79, "hsv", "vec3"),)),
            (
                125,
                "kaleidoscope",
                "vec2",
                ((106, "st", "vec2"), (107, "sides", "float"), (108, "blendy", "float")),
            ),
            (126, "loadKernels", "void", ()),
            (127, "main", "void", ()),
            (
                128,
                "map",
                "float",
                (
                    (27, "value", "float"),
                    (28, "inMin", "float"),
                    (29, "inMax", "float"),
                    (30, "outMin", "float"),
                    (31, "outMax", "float"),
                ),
            ),
            (129, "mod289_2", "vec2", ((67, "x", "vec2"),)),
            (130, "mod289_3", "vec3", ((66, "x", "vec3"),)),
            (131, "offset", "float", ((104, "st", "vec2"), (105, "freq", "float"))),
            (132, "outline", "vec3", ((90, "color", "vec3"), (91, "uv", "vec2"))),
            (133, "pcg", "uvec3", ((24, "v", "uvec3"),)),
            (134, "periodicFunction", "float", ((32, "p", "float"),)),
            (135, "permute3", "vec3", ((68, "x", "vec3"),)),
            (136, "pixellate", "vec3", ((101, "uv", "vec2"), (102, "size", "float"))),
            (137, "positiveModulo", "int", ((33, "value", "int"), (34, "modulus", "int"))),
            (138, "posterize", "vec3", ((99, "color", "vec3"), (100, "lev", "float"))),
            (139, "prng", "vec3", ((25, "p", "vec3"),)),
            (140, "prng2", "float", ((26, "p", "vec2"),)),
            (
                141,
                "quadratic3",
                "float",
                ((40, "p0", "float"), (41, "p1", "float"), (42, "p2", "float"), (43, "t", "float")),
            ),
            (142, "quadratic3x3Value", "float", ((48, "st", "vec2"), (49, "freq", "float"))),
            (
                143,
                "randomFromLatticeWithOffset",
                "vec3",
                ((35, "st", "vec2"), (36, "freq", "float"), (37, "offset", "ivec2")),
            ),
            (144, "rgb2hsv", "vec3", ((80, "rgb", "vec3"),)),
            (145, "rings", "float", ((20, "st", "vec2"), (21, "freq", "float"))),
            (146, "shadow", "vec3", ((92, "color", "vec3"), (93, "uv", "vec2"))),
            (147, "shape", "float", ((96, "st", "vec2"), (97, "sides", "int"), (98, "blend", "float"))),
            (148, "simplexValue", "float", ((69, "v", "vec2"),)),
            (149, "sineNoise", "float", ((70, "st", "vec2"), (71, "freq", "float"))),
            (150, "sobel", "vec3", ((88, "color", "vec3"), (89, "uv", "vec2"))),
            (151, "value", "float", ((76, "st", "vec2"), (77, "freq", "float"), (78, "interp", "int"))),
        ),
        "resources": (
            (
                "inputTex",
                "resolution",
                "tileOffset",
                "fullResolution",
                "time",
                "wrap",
                "seed",
                "speed",
                "loopScale",
                "kaleido",
                "effectWidth",
            ),
            ("inputTex",),
            ("fragColor",),
            True,
            False,
        ),
        "counted_loop_proof": (1, 0, 1, 9, 0, True),
        "call_edge_count": 51,
        "call_graph_sha256": "ded1fd4455f0f95030d330a330624aba6d3d7b507f959f4e149d8b8c5fd265be",
        "reachable": (
            109,
            110,
            111,
            112,
            113,
            114,
            115,
            116,
            117,
            122,
            123,
            125,
            126,
            127,
            128,
            129,
            130,
            131,
            133,
            134,
            135,
            137,
            141,
            142,
            143,
            145,
            147,
            148,
            149,
            151,
        ),
        "unreachable": (118, 119, 120, 121, 124, 132, 136, 138, 139, 140, 144, 146, 150),
        "declaration_inventory": (
            (1, "inputTex", "sampler2D", "uniform", False, False, "18:1-18:28"),
            (2, "resolution", "vec2", "uniform", False, False, "19:1-19:25"),
            (3, "tileOffset", "vec2", "uniform", False, False, "20:1-20:25"),
            (4, "fullResolution", "vec2", "uniform", False, False, "21:1-21:29"),
            (5, "time", "float", "uniform", False, False, "22:1-22:20"),
            (6, "wrap", "bool", "uniform", False, False, "23:1-23:19"),
            (7, "seed", "int", "uniform", False, False, "24:1-24:18"),
            (8, "speed", "float", "uniform", False, False, "25:1-25:21"),
            (9, "loopScale", "float", "uniform", False, False, "26:1-26:25"),
            (10, "kaleido", "float", "uniform", False, False, "27:1-27:23"),
            (11, "effectWidth", "float", "uniform", False, False, "28:1-28:27"),
            (12, "fragColor", "vec4", "output", True, False, "29:1-29:16"),
            (13, "emboss", "float[9]", "global", True, False, "33:1-33:17"),
            (14, "sharpen", "float[9]", "global", True, False, "34:1-34:18"),
            (15, "blur", "float[9]", "global", True, False, "35:1-35:15"),
            (16, "edge", "float[9]", "global", True, False, "36:1-36:15"),
            (17, "edge2", "float[9]", "global", True, False, "37:1-37:16"),
        ),
        "initializer_census": (),
        "preceding": (11, 12),
        "preceding_name": "fragColor",
        "total_nodes": 3178,
        "total_assigns": 179,
        "extent": 9,
        "admitted": (
            _Admitted(12, 13, "emboss", "float[9]", "float", 9, "global", True,
            "33:1-33:17", "33:1-33:17",
            "50c58a4be51abd5ba2a04fe5116aa251b298e2c07166ea529dbdcc98a47f65cb",
            "127d7b2e433c239cb885104c872b21bfa3d4f231aff2b6b5a5f516633fbac243", _KALEIDO_FIELDS[0]),
            _Admitted(13, 14, "sharpen", "float[9]", "float", 9, "global", True,
            "34:1-34:18", "34:1-34:18",
            "192b11ef85ff0aa2ba64ca5bc5a94688217d11aa5cb6f8e4e96eded48cab4512",
            "5e45016ee06aed737904aeaeab9366b3a4ecc361ea2c23b73fc162c42c4dde72", _KALEIDO_FIELDS[1]),
            _Admitted(14, 15, "blur", "float[9]", "float", 9, "global", True,
            "35:1-35:15", "35:1-35:15",
            "2071750907bd7e2f0820dacc4376823b1fc2ee257d17ddc72cb40eddb011f74f",
            "cfe8068d4e6d4aeec55e5ea8c79d761e5ea50dc93d3316257dd13c4330b7a658", _KALEIDO_FIELDS[2]),
            _Admitted(15, 16, "edge", "float[9]", "float", 9, "global", True,
            "36:1-36:15", "36:1-36:15",
            "4a3e1aaa7de6e3d2b5418cc650a955a698b23d0be0965f524d297ce786e6b09c",
            "940257a90e25759ff0d6baaa1f10f03321b36a37e45b61031455a2198b58595d", _KALEIDO_FIELDS[3]),
            _Admitted(16, 17, "edge2", "float[9]", "float", 9, "global", True,
            "37:1-37:16", "37:1-37:16",
            "da133dc5c2117e0cfc5c3b56e6c75cf2c6f66ea8691d9f971f6f674611d1b496",
            "1787b1387c2c810f849d12bfb795870a615507fdc864c0e5dd5ef030a9d5cf44", _KALEIDO_FIELDS[4]),
        ),
        "frame": ArrayFrameContract(
            _FRAME_STRUCT_NAME, _FRAME_INSTANCE_NAME,
            _FRAME_INSTANCE_SCOPE, True, _HELPER_PARAMETER,
            _HELPER_PARAMETER_ORDINAL, _WRITER_PARAMETER, _FRAME_WRITER,
            _KALEIDO_FIELDS),
        "writer": (126, "loadKernels", "void", 0, "39:1-65:2"),
        "writer_body": (
            ("expr", "42:2-42:19"),
            ("expr", "42:20-42:37"),
            ("expr", "42:38-42:54"),
            ("expr", "43:2-43:19"),
            ("expr", "43:20-43:36"),
            ("expr", "43:37-43:53"),
            ("expr", "44:2-44:18"),
            ("expr", "44:19-44:35"),
            ("expr", "44:36-44:52"),
            ("expr", "47:2-47:20"),
            ("expr", "47:21-47:38"),
            ("expr", "47:39-47:57"),
            ("expr", "48:2-48:19"),
            ("expr", "48:20-48:37"),
            ("expr", "48:38-48:55"),
            ("expr", "49:2-49:20"),
            ("expr", "49:21-49:38"),
            ("expr", "49:39-49:57"),
            ("expr", "52:2-52:16"),
            ("expr", "52:17-52:31"),
            ("expr", "52:32-52:46"),
            ("expr", "53:2-53:16"),
            ("expr", "53:17-53:31"),
            ("expr", "53:32-53:46"),
            ("expr", "54:2-54:16"),
            ("expr", "54:17-54:31"),
            ("expr", "54:32-54:46"),
            ("expr", "57:2-57:17"),
            ("expr", "57:18-57:33"),
            ("expr", "57:34-57:49"),
            ("expr", "58:2-58:17"),
            ("expr", "58:18-58:32"),
            ("expr", "58:33-58:48"),
            ("expr", "59:2-59:17"),
            ("expr", "59:18-59:33"),
            ("expr", "59:34-59:49"),
            ("expr", "62:2-62:18"),
            ("expr", "62:19-62:34"),
            ("expr", "62:35-62:51"),
            ("expr", "63:2-63:17"),
            ("expr", "63:18-63:33"),
            ("expr", "63:34-63:49"),
            ("expr", "64:2-64:18"),
            ("expr", "64:19-64:34"),
            ("expr", "64:35-64:51"),
        ),
        "writer_call_count": 1,
        "writer_call": {
            "statement_index": 3,
            "span": "818:5-818:18",
            "sha256": "0ad7a0ba17ae32bc5ccfd5f83deff877de66aff62864ae278a350893ce63c59a",
        },
        "state_consumer_ids": frozenset({("map", 128), ("kaleidoscope", 125), ("periodicFunction", 134), ("offset", 131)}),
        "state_consumers": ((4, ("map",)), (6, ("offset",)), (7, ("map", "periodicFunction")), (8, ("kaleidoscope",))),
        "main": (127, "main", 11, "813:1-833:2"),
        "main_body": (
            ("decl", "814:5-814:53"),
            ("decl", "815:5-815:46"),
            ("decl", "817:2-817:25"),
            ("expr", "818:5-818:19"),
            ("decl", "820:5-820:53"),
            ("if", "821:5-823:6"),
            ("decl", "825:5-825:52"),
            ("decl", "826:2-826:77"),
            ("expr", "828:2-828:41"),
            ("expr", "829:2-829:32"),
            ("expr", "832:2-832:20"),
        ),
        "stores": (
    _StoreRecord(base_id=13, base_name="emboss", index=0, value=-2.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="42:2-42:18", assign_sha256="0e007f6a518f94a0fc62b81683a90af7424371674f6f0db1d7fcc14c94efb13a", target_span="42:2-42:11",
            target_sha256="9fc661aa2a922fef26c6dfde4937976d63c00ef59face64b7d1c808f0485647c", index_span="42:9-42:10", index_sha256="ef28ab08d011ec30dc0d1c404f2912eb1cadaacfccaea7b0a20d979a2b000ff7", value_span="42:14-42:18",
            value_sha256="34d642a63755e2b92d75d78cfe9e2fec04851eb343285a86e2e72d7dd7fd82bf", statement_index=0, statement_kind="expr", statement_span="42:2-42:19"),
    _StoreRecord(base_id=13, base_name="emboss", index=1, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="42:20-42:36", assign_sha256="d9faa53e91dd62b5f865dfe86624df5bd10a4137ef1305738122736af44b1d7f", target_span="42:20-42:29",
            target_sha256="a98416becf304949a6705a98989ad1e5f6c83e33fa99356e4bfbd43496ce30f5", index_span="42:27-42:28", index_sha256="a8780ca91116311c75c8781cf57d2fac4324053effc77f7e149328fab9b52b36", value_span="42:32-42:36",
            value_sha256="44d76c015f292689e0e2bd2951b47f3ca3a607648bedde56cb4b74f5d49aabd5", statement_index=1, statement_kind="expr", statement_span="42:20-42:37"),
    _StoreRecord(base_id=13, base_name="emboss", index=2, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="42:38-42:53", assign_sha256="078480125f90295aaa5c4ee0faa47610fdafd008d8bfc4b1dfccd7567c6886f4", target_span="42:38-42:47",
            target_sha256="54f27bc63f70cdf58fca8fa7822c6b7333959b77d5e93398b8cc109af319dbbd", index_span="42:45-42:46", index_sha256="f0e209806c01c778d36c9b6bb4fc72bdf603bab930985a1009b223a83b990f6c", value_span="42:50-42:53",
            value_sha256="eff3cb3083afda18c07e7223c30d9198b2a9a35ed8d38c59b7792548108503ac", statement_index=2, statement_kind="expr", statement_span="42:38-42:54"),
    _StoreRecord(base_id=13, base_name="emboss", index=3, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="43:2-43:18", assign_sha256="e11e11895060ada6963885b20c3782eb646d7c787a9bb9c594a9070f25a3594f", target_span="43:2-43:11",
            target_sha256="71cd2dc392368f5f440ac3b302282fc004a2dbb2f3720f4f7a019d5b24075ee7", index_span="43:9-43:10", index_sha256="d357abd11962620efeb6a01b98c42c5c162520b981430df1eafa06339ce16f1b", value_span="43:14-43:18",
            value_sha256="415031478ecf2effece8adb8dedaa6a960c76ebb984dace91e176434a2c1502c", statement_index=3, statement_kind="expr", statement_span="43:2-43:19"),
    _StoreRecord(base_id=13, base_name="emboss", index=4, value=1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="43:20-43:35", assign_sha256="280adf1cb0c078fd0a0c326a35ac2700d1a83c8acf5db37c981d32ef881df2f8", target_span="43:20-43:29",
            target_sha256="175acc64e789129538b6a76eae671592626fccbb7728b3518547cc9dc3960d3c", index_span="43:27-43:28", index_sha256="364caa8783b761ebe4f1ba0bc9ef99c16eb4c0b15c85f8e36e89a513d35e51e8", value_span="43:32-43:35",
            value_sha256="7c25352c482b9b222e2f7739668b3e1a178a41b4884f902d19e068931af7f241", statement_index=4, statement_kind="expr", statement_span="43:20-43:36"),
    _StoreRecord(base_id=13, base_name="emboss", index=5, value=1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="43:37-43:52", assign_sha256="62d14bd0bba6370fbd5447736e113892d0e8271724dd62d5d66c3eed5e9dab39", target_span="43:37-43:46",
            target_sha256="42a59fff5346827ffd878549a77232f2de95c38ccb59d4e564cbbe78722c8776", index_span="43:44-43:45", index_sha256="3eda7472bc13884dbf94a8e8bd69b94e0fb099819b454ad5081fd47a36f657ab", value_span="43:49-43:52",
            value_sha256="5f9dceed436437700266283002e8f4a65b18a1e1e9712c32e86409045a63193e", statement_index=5, statement_kind="expr", statement_span="43:37-43:53"),
    _StoreRecord(base_id=13, base_name="emboss", index=6, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="44:2-44:17", assign_sha256="f51499b01545ee7f6b40e5b9bf4617769273cf18e8475ba2e8617de1df1622fd", target_span="44:2-44:11",
            target_sha256="d9b252b25c7eadf18658f7e3f8737cfbb02f067aed1cd7f9d8bbab8cec37840d", index_span="44:9-44:10", index_sha256="0ac1b659681344698b02e2c085fa768b2414914eb488aa416d66767b78d08864", value_span="44:14-44:17",
            value_sha256="386d764af0e66313debc999660f2864e6ad2464f2943c83b3d0c5676ce61c6bb", statement_index=6, statement_kind="expr", statement_span="44:2-44:18"),
    _StoreRecord(base_id=13, base_name="emboss", index=7, value=1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="44:19-44:34", assign_sha256="c0a7c507a0b7cb8fff6c7a8128bfdf1a92772e1284764571e07cfbddda117fed", target_span="44:19-44:28",
            target_sha256="9abff226990eb5e333cc0356cc719588afc8457c081a9fd19ee9d20315bfb622", index_span="44:26-44:27", index_sha256="ac2f07752cbd40d3edffeb65064818926eb14fc8119dd6c9d1107da317e98572", value_span="44:31-44:34",
            value_sha256="5550ebe78e0ab6108e74890d6f2e64dc1eb86eac5668184d89e7a88dffbe7948", statement_index=7, statement_kind="expr", statement_span="44:19-44:35"),
    _StoreRecord(base_id=13, base_name="emboss", index=8, value=2.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="44:36-44:51", assign_sha256="9b154bb76eba9e3086a7e7e05ccd82f9334a2d78a3dde2ad4f048b782daee41e", target_span="44:36-44:45",
            target_sha256="36c8fff10208df5c50f8a4e30d0ab00090683b662833abd5724ca91559d93369", index_span="44:43-44:44", index_sha256="d301e12231707f3f7f7c859167a476d91c4eb0b9827a8e183f383ac954de2143", value_span="44:48-44:51",
            value_sha256="0ab5e8c1bf02fcd5afc2643b50f530c7db4478d5075f6df3bfba93c85eeffd52", statement_index=8, statement_kind="expr", statement_span="44:36-44:52"),
    _StoreRecord(base_id=14, base_name="sharpen", index=0, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="47:2-47:19", assign_sha256="3d760ed8e69c52b96d61639891f097eb85520627ce7a74ad9029779b83f70bbf", target_span="47:2-47:12",
            target_sha256="42ff2795806003bd44184c6146ca6fc8ce3f7b93d3628dd2a14d401bad055779", index_span="47:10-47:11", index_sha256="160ac3cfa558b5fbc666733ce98cf52af4156cd8fae3651a4b2d7279e9f652a9", value_span="47:15-47:19",
            value_sha256="2edd7da0a842ddcb28dfa9710ae7fd3294b597b9cefb2b8e2c4fb6e662d1ef9f", statement_index=9, statement_kind="expr", statement_span="47:2-47:20"),
    _StoreRecord(base_id=14, base_name="sharpen", index=1, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="47:21-47:37", assign_sha256="c0181976828917c8b5dfb68306030bb01252fc126348783393ef22388166cc21", target_span="47:21-47:31",
            target_sha256="20ef0f5474e39c7a29f067b8bf4fa302c9aaef0215e1ca08bfd720c291d4029d", index_span="47:29-47:30", index_sha256="0bfa55837620424eaef0fe591544f5d5e3478b37a79ad17c8cdb1aee60e40b32", value_span="47:34-47:37",
            value_sha256="825db02e0b803a46b03c48f05cf0dbc31db54c20d79a6d4ad7c42d49562b1b34", statement_index=10, statement_kind="expr", statement_span="47:21-47:38"),
    _StoreRecord(base_id=14, base_name="sharpen", index=2, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="47:39-47:56", assign_sha256="c2e88d36ca2c4a37a18936437e7451357ac3a4ab901d20b57629d545b366517f", target_span="47:39-47:49",
            target_sha256="90838412bc0ebe53eb6fb11e90de987513d861dc58eaa4343bd10747c88c87fe", index_span="47:47-47:48", index_sha256="f8d3163a35929214eb637a42a08a781a94eb14b27e6d2067c6d59e32e954ed14", value_span="47:52-47:56",
            value_sha256="ac15f779f79478428f11df396f5f5a36a669efb0331438b56970b4bb00d066eb", statement_index=11, statement_kind="expr", statement_span="47:39-47:57"),
    _StoreRecord(base_id=14, base_name="sharpen", index=3, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="48:2-48:18", assign_sha256="1d22da68433545f5a34707a0f389869208cf2346ec63be22bc822e5e14bdb4bb", target_span="48:2-48:12",
            target_sha256="6475288bcba1e004e7b0361731b35c5687ecde090af4c96e550e2ab0086e138d", index_span="48:10-48:11", index_sha256="4f1a075b8117047a03ffd5ea648d3ab461bb9dc80858401bc6de6d9ed167545b", value_span="48:15-48:18",
            value_sha256="177f8210e5dffcd5afc0e65b52ee0860e61d2dfb68a845c8301285ca54ff4368", statement_index=12, statement_kind="expr", statement_span="48:2-48:19"),
    _StoreRecord(base_id=14, base_name="sharpen", index=4, value=5.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="48:20-48:36", assign_sha256="949ca77b51ef94a506720af4671960037f1e931f77041ce4cff913113bdb8d5f", target_span="48:20-48:30",
            target_sha256="a0852e9e1d4fd342e90c2a3ad4150c920375761162e664076f09e3686271adad", index_span="48:28-48:29", index_sha256="6d28ee7f7c9309294997bf24cbae857f268102419eeb4dcbda8f6c5ebf7a111e", value_span="48:33-48:36",
            value_sha256="f7c46684f4d1f7231eddb2e4b6b91c9162a78a5d5c7236530217fba7b081936a", statement_index=13, statement_kind="expr", statement_span="48:20-48:37"),
    _StoreRecord(base_id=14, base_name="sharpen", index=5, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="48:38-48:54", assign_sha256="1629164891997f48d9f82c6674d5baa9a35b10be6c19323924acb358082a628b", target_span="48:38-48:48",
            target_sha256="853f73c3d02b197bef98efb2b83fd81dd439b91b0024ea0cd825273e8191838b", index_span="48:46-48:47", index_sha256="3b8df032520f24072206191c6b2371cfc80ae871c936b083437f164d06e01231", value_span="48:51-48:54",
            value_sha256="5151fcddef1aafbd99af7efb6e69c2feab1fc02551cd1c7dcecc0529fc675e3d", statement_index=14, statement_kind="expr", statement_span="48:38-48:55"),
    _StoreRecord(base_id=14, base_name="sharpen", index=6, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="49:2-49:19", assign_sha256="eb5b461e71a168afc3eaa36933e4a6020b09cd83fe3adb0ef1a10952f27c8559", target_span="49:2-49:12",
            target_sha256="7335680eec67efd6f97edd594c6d49b0b6d64980dea98532bfc388c8070a4ec7", index_span="49:10-49:11", index_sha256="2e10d4650c1da105679c8974fd952b5ac72ebb22499f89bef8d28f28d1ee7abd", value_span="49:15-49:19",
            value_sha256="d394bf9bb59ee77b1bf6f16cf2a8a58eeb342f428db17f75026c34a01c0aae9a", statement_index=15, statement_kind="expr", statement_span="49:2-49:20"),
    _StoreRecord(base_id=14, base_name="sharpen", index=7, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="49:21-49:37", assign_sha256="bcb85a90a43514739cef2212e41aeb5182fa7ec4005f87aaf02a852beaf7bbea", target_span="49:21-49:31",
            target_sha256="e32ca02c1eda082ba85661662067bd8249b6ac84c213b2f70b0b9fbfaf8027fa", index_span="49:29-49:30", index_sha256="8d1e855ea6b79341d0692d288601fb68e5d4993d0465cd10d695fad5a0968712", value_span="49:34-49:37",
            value_sha256="b95a13a414a27d0838073526d4886e600c7bea95720c33fbb42bcd932689c952", statement_index=16, statement_kind="expr", statement_span="49:21-49:38"),
    _StoreRecord(base_id=14, base_name="sharpen", index=8, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="49:39-49:56", assign_sha256="06c8168cfee10b5b3102b41f7e8a7aaaf8483f17f9c2b219fbd073a94ef6d60d", target_span="49:39-49:49",
            target_sha256="f87c9f723c2927f1343b9af2a601de483221105896ff3f020c17bbb82d4bdb5f", index_span="49:47-49:48", index_sha256="be669a2bee63e0d702c24499d8775344854c95c4699143eae03422bd41b60585", value_span="49:52-49:56",
            value_sha256="56a18a357a3f87b1870f8a46f49e3e792719bc03ea79b0676f29eb10bcdc7544", statement_index=17, statement_kind="expr", statement_span="49:39-49:57"),
    _StoreRecord(base_id=15, base_name="blur", index=0, value=1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="52:2-52:15", assign_sha256="49055dc64da9d8c229970011b4b1496358d5ea648bf5e2c38aa7397c0788ad1a", target_span="52:2-52:9",
            target_sha256="64b0e37cb572b69f8460a518fdeade9b81bc36259b85cbed37eb428967bb347f", index_span="52:7-52:8", index_sha256="a20271f257027ca9b68369c842b41ccc3812bca239769a2788526fcc892d4034", value_span="52:12-52:15",
            value_sha256="30f0b4ff22ee90058fd9cf451e153d8f3acc51bacd9562d8a23793f8be418cb6", statement_index=18, statement_kind="expr", statement_span="52:2-52:16"),
    _StoreRecord(base_id=15, base_name="blur", index=1, value=2.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="52:17-52:30", assign_sha256="61c5e34011499d9edeb98f27464f63fb27671b3ebaafa97c6de6f0b5da60e3c6", target_span="52:17-52:24",
            target_sha256="f70624432e1a72a91861ea9f0e996386028d00d32c913c89a73e748ea3d4809f", index_span="52:22-52:23", index_sha256="ffff03884be6d08168c91393f57a4166f102853ea14a47ae665a84b33f3cc750", value_span="52:27-52:30",
            value_sha256="643e3b732840219e0b6c4004d6d9c5cb25f76132041bb883c8f1fdadfb56019e", statement_index=19, statement_kind="expr", statement_span="52:17-52:31"),
    _StoreRecord(base_id=15, base_name="blur", index=2, value=1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="52:32-52:45", assign_sha256="5be1789e29cb6a3ed892811753e49c0eef99300e970321b85215c816c04b5965", target_span="52:32-52:39",
            target_sha256="6c5077a2286d319a897e6fd8c6107c5867ccd36a501112565ef2c4a8272786e8", index_span="52:37-52:38", index_sha256="70b6ac993fd9144a7ba01fe3bdd6a2352c9348332feedac1715e0b3088e5a0b3", value_span="52:42-52:45",
            value_sha256="204fb1bbcb5e0f76d2574b983505b74e1295f0ae16e5f202163e273584286cd3", statement_index=20, statement_kind="expr", statement_span="52:32-52:46"),
    _StoreRecord(base_id=15, base_name="blur", index=3, value=2.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="53:2-53:15", assign_sha256="ccd1e64f7e5b44cb89c800cf48bcaabf51aa08b3a0e450a54dcb9d3fcfe1263d", target_span="53:2-53:9",
            target_sha256="1cf46f57e7b463b225e74c6a9446432bf50dc48f371650df193a1249f756fe04", index_span="53:7-53:8", index_sha256="5f272dbc5255eab15c518cfb349ceb317505d0709023d445b8b605daaac884dd", value_span="53:12-53:15",
            value_sha256="09c510076f06fc501302d11ed0618a12dbec14c56b10c15c33ffc944e6955c09", statement_index=21, statement_kind="expr", statement_span="53:2-53:16"),
    _StoreRecord(base_id=15, base_name="blur", index=4, value=4.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="53:17-53:30", assign_sha256="3e1b244deafd8421e30e6ec7ab213ca6b23d950dec9aa6130a36c7bddcb0c431", target_span="53:17-53:24",
            target_sha256="3a8300c21660385c1bae6e09799995ffcda0c5bd78140e22a3ee93b6ec2b81b0", index_span="53:22-53:23", index_sha256="6c90ac1f54f8b27b82b9612b27b824f8296afe4fc65f26b7e54acf271f072877", value_span="53:27-53:30",
            value_sha256="97316450dd6c97662a053b254b1d8757e9d0810a7e6b4d864af8f159f286faa0", statement_index=22, statement_kind="expr", statement_span="53:17-53:31"),
    _StoreRecord(base_id=15, base_name="blur", index=5, value=2.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="53:32-53:45", assign_sha256="8253441dc98e30a5c05223d28b195bd2c390b15b218ae0892f70a034242653b1", target_span="53:32-53:39",
            target_sha256="7314bfd531394b6c29f80bcdc962d81cce6ec3fb16c58802e60ba53642c42d90", index_span="53:37-53:38", index_sha256="8bdef04ce74abf1bbf67fb9f3c36afa01e7bff791e473788406ec1593e7710b9", value_span="53:42-53:45",
            value_sha256="6f09694068297b441874a67d2b17c1b5dc87446694129a012a8775a4a35439df", statement_index=23, statement_kind="expr", statement_span="53:32-53:46"),
    _StoreRecord(base_id=15, base_name="blur", index=6, value=1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="54:2-54:15", assign_sha256="943d75f1f5bef945405746b3aeb3f95584d4c0f24dbff02c08afb5e05d111b70", target_span="54:2-54:9",
            target_sha256="9ac2e0126d602673a6bcaaa61fe1ed40f04a46ddea63d9644da56d5b59727edb", index_span="54:7-54:8", index_sha256="baf80dce909b2acedc7a7bd2e558e4eb5e756f5fe39f1933214013e3d8aff286", value_span="54:12-54:15",
            value_sha256="15b4c16eabdce4dc8374fbf16537ad740d02826b5b9cdd69a7e0d4341fc3e368", statement_index=24, statement_kind="expr", statement_span="54:2-54:16"),
    _StoreRecord(base_id=15, base_name="blur", index=7, value=2.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="54:17-54:30", assign_sha256="bb605f1f77980743a5c9b25280f3f187597817d974d535d4431aac977985b1d6", target_span="54:17-54:24",
            target_sha256="04c6a263bcc7c7a0e97314d34e9b5e1f95cbf3fd38abd0e6b6e7ab86e435f066", index_span="54:22-54:23", index_sha256="872e3c42098a876c3d24a15df4ca3affef47eb9c6e97f0c1e937099e6c716c37", value_span="54:27-54:30",
            value_sha256="5fe915a2af400b66ec3047dcdc8e7f70637517dc7cee40559452c6dcd7bc761b", statement_index=25, statement_kind="expr", statement_span="54:17-54:31"),
    _StoreRecord(base_id=15, base_name="blur", index=8, value=1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="54:32-54:45", assign_sha256="94c14c54cf08b5e0d4ed52cf2d088ed64052406a835f3e11fafd0d6e5a47cf69", target_span="54:32-54:39",
            target_sha256="450f30353f674f94612572a13f265c788c9fa5c7123c81ece713f782856516f3", index_span="54:37-54:38", index_sha256="19719132142581d77ef7d9c53f4b4e2895ed35dc4ff6aea6c636e048b214f00f", value_span="54:42-54:45",
            value_sha256="bd86b351e223721b522f7033574c8b7e34f179ba4c07744d5a6b32cdac095975", statement_index=26, statement_kind="expr", statement_span="54:32-54:46"),
    _StoreRecord(base_id=16, base_name="edge", index=0, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="57:2-57:16", assign_sha256="4a597f5d3628fce613299a40b62a362bfa8f1508fefe2f1136c02773e168b3cc", target_span="57:2-57:9",
            target_sha256="e3933e287df363f8d97b328bb84d75a77017fabacdec1214ec0d614ec848c09f", index_span="57:7-57:8", index_sha256="d756cbc4e321a053cf347576214e6f31f0516a924a50266064619b0fa3ba526b", value_span="57:12-57:16",
            value_sha256="73e0ba7e45dac0cf99a7684eccfcd91f5957a1657f27a2e7bbd417263fffd4d3", statement_index=27, statement_kind="expr", statement_span="57:2-57:17"),
    _StoreRecord(base_id=16, base_name="edge", index=1, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="57:18-57:32", assign_sha256="34fb21a4177789ba4e93b7c7365856696f0c3f8a7ef3f3dcdb76cfe48163c1de", target_span="57:18-57:25",
            target_sha256="f360fefc5b058c62fe658f8f43cb437a9d10657159c89f51e5331331fce45093", index_span="57:23-57:24", index_sha256="c220005e2c4901e1932bb46487cbf44a901a8e971ff74bc2d04463045559e709", value_span="57:28-57:32",
            value_sha256="7406b8cba0796279f910826e0faa401de73650404647010e42ea911fb767303e", statement_index=28, statement_kind="expr", statement_span="57:18-57:33"),
    _StoreRecord(base_id=16, base_name="edge", index=2, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="57:34-57:48", assign_sha256="59943a741a3e7d7cbfc7b6a5c51b5187d091a87c514ef28e2d889eb005c84770", target_span="57:34-57:41",
            target_sha256="6be5e059b441f0c561495b03d5db4f8bad5c1c0aeb8d41947a6a44828918a505", index_span="57:39-57:40", index_sha256="8f11429f0fc2075be0036d76184374fb114669dec6ea933841c2850e88d092e5", value_span="57:44-57:48",
            value_sha256="a64f93fcaf3e59b61811f2c35eb410a5a49a76da4a640dc7a62f12709f6d34b2", statement_index=29, statement_kind="expr", statement_span="57:34-57:49"),
    _StoreRecord(base_id=16, base_name="edge", index=3, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="58:2-58:16", assign_sha256="c8960192ea24dfcaf8d428f25b1a8ae0be1ede98878dab389935f6deb57dfb58", target_span="58:2-58:9",
            target_sha256="7c807dd008e24ae4aae01fa4f348feb5006e36b6e2eba0b0fd96e02ec6368499", index_span="58:7-58:8", index_sha256="fe38f9e295727b667f3ffce4f031d235126969b0b17172686b0cfc3b606d317b", value_span="58:12-58:16",
            value_sha256="489cd6640ef274ac3651e94c573d7fdd82ea381a2323b7f63cab4ff682e033cd", statement_index=30, statement_kind="expr", statement_span="58:2-58:17"),
    _StoreRecord(base_id=16, base_name="edge", index=4, value=8.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="58:18-58:31", assign_sha256="09cf66ef4bd611fbf64e3dce03eb0cf1f3ad2c328cbfc95903bbd65719980c3d", target_span="58:18-58:25",
            target_sha256="054e786a27b063b311c1d835a14812073b28c94bfe346edf439319d72899ca43", index_span="58:23-58:24", index_sha256="6e764be6a3356f7c660ad354c7c4f4c6f0ebd00bdf897a0995ec381bf9d04923", value_span="58:28-58:31",
            value_sha256="959cfe62eda5f862365ebe00169cdc0da791899c07a8a9f392c869fde449d1f0", statement_index=31, statement_kind="expr", statement_span="58:18-58:32"),
    _StoreRecord(base_id=16, base_name="edge", index=5, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="58:33-58:47", assign_sha256="0c43e1f70733ee3df89c13cd180f328815e1b97373418dcd472388ee62f2cf68", target_span="58:33-58:40",
            target_sha256="8bcd6eb6b7367cc53875ee129fea15b174d36932b71411be6010e8950f8bf100", index_span="58:38-58:39", index_sha256="99266f295b2e6e2785496faf7685582bbf070d0f714021e8fa709885c76fa16a", value_span="58:43-58:47",
            value_sha256="b24c55e31e6cb8717eaccaabcc8b6db89c6454411c7b2c1a2946ec977acc23d3", statement_index=32, statement_kind="expr", statement_span="58:33-58:48"),
    _StoreRecord(base_id=16, base_name="edge", index=6, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="59:2-59:16", assign_sha256="36d6f1c9e6bfb94e417903901b6743591e03cd2ed0d0c8eb41dce935cd9927f2", target_span="59:2-59:9",
            target_sha256="d759ad57c5cd9ebfd1ae332caaa25428751374171d0010eb7d8855ece5a96ed7", index_span="59:7-59:8", index_sha256="26b9389963477d350045e8f9f96e5f5b273df7e8577365dd3bd51297fbc5969b", value_span="59:12-59:16",
            value_sha256="937cf5f906bbc76ba2c0afdbbc2a24b202636ccee99f790a90c14cabc8ceac37", statement_index=33, statement_kind="expr", statement_span="59:2-59:17"),
    _StoreRecord(base_id=16, base_name="edge", index=7, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="59:18-59:32", assign_sha256="54dde73b4345657707d0a584477136b5da3d9c9bf45d1bf228c1b09fcb5dc189", target_span="59:18-59:25",
            target_sha256="12c640672e33741001935ce7c5c4979b47aa111c3f3c90a0b9c8d2b28fb33d1f", index_span="59:23-59:24", index_sha256="71741b55d597d5da99af7b9abe8eb01d1ecb8b7be6e040328a0a371c99df976c", value_span="59:28-59:32",
            value_sha256="68419b3ff8dd57f1a9bfa79cde2f92bf8416b5b0839e9f54d12d2b21c5920b0e", statement_index=34, statement_kind="expr", statement_span="59:18-59:33"),
    _StoreRecord(base_id=16, base_name="edge", index=8, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="59:34-59:48", assign_sha256="630fab2e0294e71004227ca871e0a15aa2e3f158dcd1346606b5ae135c942c8b", target_span="59:34-59:41",
            target_sha256="a5f41162daa66361d858e21aab27a04704bab4e363313ff4dccafc40396fc363", index_span="59:39-59:40", index_sha256="67724f4fb32cf739a5757c4f20e3256b32afa676596cf83db8a7b9c6a38c9ad8", value_span="59:44-59:48",
            value_sha256="282b12858451c180b88c482f3ab5dea1744fbd3fdce1a0e201f6e0dac6fa33fb", statement_index=35, statement_kind="expr", statement_span="59:34-59:49"),
    _StoreRecord(base_id=17, base_name="edge2", index=0, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="62:2-62:17", assign_sha256="2bbe34f0bd6819ada8aade6037cb2a3b7957c8687e3fbbf7f4b8d6aee9878c19", target_span="62:2-62:10",
            target_sha256="2413147b3e34aec366fcf6e2d974e9f9a2f385d285a2ec59f2485dc615003af1", index_span="62:8-62:9", index_sha256="3c74ef4bccee8f0bf5533d7f60b39b382975ee3e355a03ef7a6a80619d15d7f0", value_span="62:13-62:17",
            value_sha256="af12da05b787b298256d378ba6511215ca0edd9b572da6bea4447e7869b57659", statement_index=36, statement_kind="expr", statement_span="62:2-62:18"),
    _StoreRecord(base_id=17, base_name="edge2", index=1, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="62:19-62:33", assign_sha256="553fe7577127de79b1bc13c114eff531f3194d0418c05a4bd006d5994f11710c", target_span="62:19-62:27",
            target_sha256="de86c99307eb2c0f2b962db379027761913c593fe271e19acdeb7c71498d676d", index_span="62:25-62:26", index_sha256="9115dbb6bc5d4b924136b3c75fb863ae92189a724dc6c9fa599f211a20ad0c02", value_span="62:30-62:33",
            value_sha256="1a018cfb5b1fc155f848c2d5f25f4564b42d03631cb73fdaaff8a5f48166a72e", statement_index=37, statement_kind="expr", statement_span="62:19-62:34"),
    _StoreRecord(base_id=17, base_name="edge2", index=2, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="62:35-62:50", assign_sha256="9203d855d31d40320f486278b7572b63b1e8dc448df102cb78b9d1dccf4c370a", target_span="62:35-62:43",
            target_sha256="d7a5b6b393f79c6c0f33d5b128ef99f301fa3f5bfd7fb5675a6be59f8576db32", index_span="62:41-62:42", index_sha256="321e10015befe992a64a1de723bcbde0b987b111a3c0182c599b10ca9927afb1", value_span="62:46-62:50",
            value_sha256="0b01e7c024826736f263b780b792e8c44795c9df94c0d7f5bc2b2940298fc73d", statement_index=38, statement_kind="expr", statement_span="62:35-62:51"),
    _StoreRecord(base_id=17, base_name="edge2", index=3, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="63:2-63:16", assign_sha256="f151cf42a47c6047e465be14f483fe87826376783fbffb291a73cdd1d3bd13ba", target_span="63:2-63:10",
            target_sha256="02e09b4e7f3138b5d63e50d86698b3f5ca7f2e57441b3cf4ad2d5fe6b813c960", index_span="63:8-63:9", index_sha256="e020024d879a2969166a35a81b0e8872797660d4429e80d280455feda40b1c6a", value_span="63:13-63:16",
            value_sha256="434c0201db81e0c27dd20df64f49448e0e01af1642113e6d9dfec178ef99af20", statement_index=39, statement_kind="expr", statement_span="63:2-63:17"),
    _StoreRecord(base_id=17, base_name="edge2", index=4, value=4.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="63:18-63:32", assign_sha256="4385e1414d28eb3f8a153f869da4a7dbe9f7fdc70f254b0c8556a1cfbed6d0a1", target_span="63:18-63:26",
            target_sha256="d314f153b0d9461e44cb0d7ceea60955c0ba5f603cf0af9d6e8c1277726d756d", index_span="63:24-63:25", index_sha256="21aa2cda761277344b986a669c145f073887f80c3a7d888e4d6afcbfd7fe8ea7", value_span="63:29-63:32",
            value_sha256="f67e171cbafab265e8a0a368bb667ffc83da85ce7afc02d466786f82c8e0c99a", statement_index=40, statement_kind="expr", statement_span="63:18-63:33"),
    _StoreRecord(base_id=17, base_name="edge2", index=5, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="63:34-63:48", assign_sha256="ab6691e7e753a09d098405e9b1665e5fe21b12f34d1f783fed547d29961484ce", target_span="63:34-63:42",
            target_sha256="28d03aba47038ca74edfecb7ade7b6822e7505f23b45bc574cc5ed58544bdfff", index_span="63:40-63:41", index_sha256="30966289b4d850a2907c3e2393af89b5eb5a79fcea7b95ac69e92c44b338e2e5", value_span="63:45-63:48",
            value_sha256="38d72f3b31684c8077a59c1d3e7102f5ab8d755cc0569a3bedcb59610ff4b71c", statement_index=41, statement_kind="expr", statement_span="63:34-63:49"),
    _StoreRecord(base_id=17, base_name="edge2", index=6, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="64:2-64:17", assign_sha256="567e8cdacbf2602d26ae08087b34a84c8d0811e032a3099b6e9febde6280efd7", target_span="64:2-64:10",
            target_sha256="ede0d910ac65d908b228d4988566ee616a29c6ae6f692a84bbe28a591458a938", index_span="64:8-64:9", index_sha256="6d261bbf950e4dd627d6e62535d4a687cd51f603e5126ff0ee949f49e702f423", value_span="64:13-64:17",
            value_sha256="e917788dc7be3259902b0f6b274474b2c40846e3a27cf63e0eaf312b1a28ada0", statement_index=42, statement_kind="expr", statement_span="64:2-64:18"),
    _StoreRecord(base_id=17, base_name="edge2", index=7, value=0.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="64:19-64:33", assign_sha256="b1e4d985e50d948f82d68d6bf46694cd618d5ca7ab18b5925ef1fd3984b99d8f", target_span="64:19-64:27",
            target_sha256="bab2c9aa85bf94bac2e1fddcc4390b7f9727ae7f1f9a663707ace16e5d0b6dc1", index_span="64:25-64:26", index_sha256="03376966081f9c1f250a85a363e681b9a7fb61f8987dc3331b3e9a8efade7a2e", value_span="64:30-64:33",
            value_sha256="e7c486f30df3f56b516172819a6ff574943f1b2821066764070e58c553b5e1e1", statement_index=43, statement_kind="expr", statement_span="64:19-64:34"),
    _StoreRecord(base_id=17, base_name="edge2", index=8, value=-1.0, operator="=", owner_id=126,
            owner_name="loadKernels", assign_span="64:35-64:50", assign_sha256="bad0cefe5516a25df97dbdf945dac17dc697be2b3528c022439946c99bb6abd6", target_span="64:35-64:43",
            target_sha256="c7e0aada6a28b4b8416982cce82e95f7e331fa0d1618f75cd0d9f4e8f5ba2c47", index_span="64:41-64:42", index_sha256="ef12eaf82ab72865e4edce9c11fa3da09f7ba70dce487acb2b6c9f559779f07c", value_span="64:46-64:50",
            value_sha256="7459cafdbaa33b905c57ccbd20623cae74ed016942372cbc1fbda2902274663c", statement_index=44, statement_kind="expr", statement_span="64:35-64:51"),
        ),
        "store_triples": (
            (13, 0, -2.0),
            (13, 1, -1.0),
            (13, 2, 0.0),
            (13, 3, -1.0),
            (13, 4, 1.0),
            (13, 5, 1.0),
            (13, 6, 0.0),
            (13, 7, 1.0),
            (13, 8, 2.0),
            (14, 0, -1.0),
            (14, 1, 0.0),
            (14, 2, -1.0),
            (14, 3, 0.0),
            (14, 4, 5.0),
            (14, 5, 0.0),
            (14, 6, -1.0),
            (14, 7, 0.0),
            (14, 8, -1.0),
            (15, 0, 1.0),
            (15, 1, 2.0),
            (15, 2, 1.0),
            (15, 3, 2.0),
            (15, 4, 4.0),
            (15, 5, 2.0),
            (15, 6, 1.0),
            (15, 7, 2.0),
            (15, 8, 1.0),
            (16, 0, -1.0),
            (16, 1, -1.0),
            (16, 2, -1.0),
            (16, 3, -1.0),
            (16, 4, 8.0),
            (16, 5, -1.0),
            (16, 6, -1.0),
            (16, 7, -1.0),
            (16, 8, -1.0),
            (17, 0, -1.0),
            (17, 1, 0.0),
            (17, 2, -1.0),
            (17, 3, 0.0),
            (17, 4, 4.0),
            (17, 5, 0.0),
            (17, 6, -1.0),
            (17, 7, 0.0),
            (17, 8, -1.0),
        ),
        "references": (),
    },
    # --- effects frozen record (measured; see
    # effects-design.md §§1-2). SEVEN declarations, 63 stores,
    # the first seven-array member; the five shared tables are
    # byte-identical to the family's, `edge3`/`sharpenBlur` new.
    # The frozen `state_consumers` are the POST-writer main
    # statements (measured: the pre-writer UV-warp calls at
    # statements 5/12/13 sit ahead of the writer call at 15 and
    # are outside this lock's frozen set; the write-only census
    # is what actually protects the arrays -- effects-design
    # §2).
    EFFECTS_KEY: {
        "profile": "mutable-global-nine-array-effects-v1",
        "source_path": "classicNoisedeck/effects/effects.glsl",
        "raw_bytes": 21087,
        "raw_sha256": "e3b742be53b6b1b0dd5e089a805ff02a931cd14643d0a0abe376bd8044e8ec6c",
        "normalized_bytes": 15773,
        "normalized_sha256": "cce2f30177586f4cdabab1e1741a99d1470f49db79c60dc20df9ddbcac9bdfda",
        "functions_sha256": "d06fd4218bd7513a5aecd343bc3bb9d83dfb6b8fba011626fd5bb80707d67579",
        "whole_sha256": "db85c4d2cafed8c07bc03d3e203ec83d099575ade15b5b452a9eeb58bb4940d1",
        "interface_sha256": "feeb85a578bad5296e9c345401f7f1a6055da9aa6f5f476c346137f53cdeef52",
        "defines": (("EFFECT", "int", "0"), ("FLIP", "int", "0")),
        "declaration_count": 21,
        "function_count": 28,
        "function_inventory": (
            (65, 'bicubic', 'float', ((57, 'p', 'vec2'),)),
            (66, 'bloom', 'vec3', ((62, 'st', 'vec2'),)),
            (67, "brightnessContrast", 'vec3', ((32, 'color', 'vec3'),)),
            (68, 'cga', 'vec3', ((58, 'color', 'vec4'), (59, 'st', 'vec2'))),
            (69, 'convolutionEffect', 'vec3', ((53, 'color', 'vec3'), (54, 'uv', 'vec2'))),
            (70, 'convolve', 'vec3', ((41, 'uv', 'vec2'), (42, 'kernel', 'float[9]'), (43, 'divide', 'bool'))),
            (71, 'derivatives', 'vec3', ((44, 'color', 'vec3'), (45, 'uv', 'vec2'), (46, 'divide', 'bool'))),
            (72, 'desaturate', 'vec3', ((40, 'color', 'vec3'),)),
            (73, 'f', 'float', ((56, 'st', 'vec2'),)),
            (74, 'hsv2rgb', 'vec3', ((34, 'hsv', 'vec3'),)),
            (75, 'loadKernels', 'void', ()),
            (76, 'main', 'void', ()),
            (77, 'map', 'float', ((25, 'value', 'float'), (26, 'inMin', 'float'), (27, 'inMax', 'float'), (28, 'outMin', 'float'), (29, 'outMax', 'float'))),
            (78, "offsets", 'float', ((64, 'st', 'vec2'),)),
            (79, 'outline', 'vec3', ((49, 'color', 'vec3'), (50, 'uv', 'vec2'))),
            (80, 'pcg', 'uvec3', ((22, 'v', 'uvec3'),)),
            (81, "periodicFunction", 'float', ((55, 'p', 'float'),)),
            (82, 'pixellate', 'vec3', ((38, 'uv', 'vec2'), (39, 'size', 'float'))),
            (83, 'posterize', 'vec3', ((36, 'color', 'vec3'), (37, 'lev', 'float'))),
            (84, 'prng', 'vec3', ((23, 'p', 'vec3'),)),
            (85, 'random', 'float', ((24, 'p', 'vec2'),)),
            (86, 'rgb2hsv', 'vec3', ((35, 'rgb', 'vec3'),)),
            (87, 'rotate2D', 'vec2', ((30, 'st', 'vec2'), (31, 'rot', 'float'))),
            (88, "saturate", 'vec3', ((33, 'color', 'vec3'),)),
            (89, 'shadow', 'vec3', ((51, 'color', 'vec3'), (52, 'uv', 'vec2'))),
            (90, 'sobel', 'vec3', ((47, 'color', 'vec3'), (48, 'uv', 'vec2'))),
            (91, 'subpixel', 'vec3', ((60, 'st', 'vec2'), (61, 'scale', 'float'))),
            (92, 'zoomBlur', 'vec3', ((63, 'st', 'vec2'),)),
        ),
        "resources": (
            ('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'renderScale', 'time', 'effectAmt', 'scaleAmt', 'rotation', 'offsetX', 'offsetY', 'intensity', 'saturation'),
            ('inputTex',),
            ('fragColor',),
            True,
            False,
        ),
        "counted_loop_proof": (4, 0, 2, 48, 0, True),
        "call_edge_count": 30,
        "call_graph_sha256": "cb421a62eb9d14a121e746b6bffea51e7c188db10230a95f77349bbb2ef2c3da",
        "reachable": (67, 75, 76, 77, 78, 81, 87, 88),
        "unreachable": (65, 66, 68, 69, 70, 71, 72, 73, 74, 79, 80, 82, 83, 84, 85, 86, 89, 90, 91, 92),
        "declaration_inventory": (
            (1, 'inputTex', 'sampler2D', 'uniform', False, False, '15:1-15:28'),
            (2, 'resolution', 'vec2', 'uniform', False, False, '16:1-16:25'),
            (3, 'tileOffset', 'vec2', 'uniform', False, False, '17:1-17:25'),
            (4, 'fullResolution', 'vec2', 'uniform', False, False, '18:1-18:29'),
            (5, 'renderScale', 'float', 'uniform', False, False, '19:1-19:27'),
            (6, 'time', 'float', 'uniform', False, False, '20:1-20:20'),
            (7, 'effectAmt', 'float', 'uniform', False, False, '21:1-21:25'),
            (8, 'scaleAmt', 'float', 'uniform', False, False, '22:1-22:24'),
            (9, 'rotation', 'float', 'uniform', False, False, '23:1-23:24'),
            (10, 'offsetX', 'float', 'uniform', False, False, '24:1-24:23'),
            (11, 'offsetY', 'float', 'uniform', False, False, '25:1-25:23'),
            (12, 'intensity', 'float', 'uniform', False, False, '26:1-26:25'),
            (13, 'saturation', 'float', 'uniform', False, False, '27:1-27:26'),
            (14, 'fragColor', 'vec4', 'output', True, False, '28:1-28:16'),
            (15, 'emboss', 'float[9]', 'global', True, False, '31:1-31:17'),
            (16, 'sharpen', 'float[9]', 'global', True, False, '32:1-32:18'),
            (17, 'blur', 'float[9]', 'global', True, False, '33:1-33:15'),
            (18, 'edge', 'float[9]', 'global', True, False, '34:1-34:15'),
            (19, 'edge2', 'float[9]', 'global', True, False, '35:1-35:16'),
            (20, 'edge3', 'float[9]', 'global', True, False, '36:1-36:16'),
            (21, 'sharpenBlur', 'float[9]', 'global', True, False, '37:1-37:22'),
        ),
        "initializer_census": (),
        "preceding": (13, 14),
        "preceding_name": "fragColor",
        "total_nodes": 2638,
        "total_assigns": 235,
        "extent": 9,
        "admitted": (
            _Admitted(14, 15, "emboss", "float[9]", "float", 9, "global", True,
            "31:1-31:17", "31:1-31:17",
            "3283edd8d2d196c3bc484c93f437559e164db7c1afabb024e1aa2ac256914fcd",
            "9274430d60f2993d916a08cf796efade010a25140deb32754504b756cd6f603f", _EFFECTS_FIELDS[0]),
            _Admitted(15, 16, "sharpen", "float[9]", "float", 9, "global", True,
            "32:1-32:18", "32:1-32:18",
            "68ee8b957fd87259a5f18f04de1bfae89c77a026ac0314685bb95625d78d1865",
            "05a090f4cc21195e82e471a9284030368f6aa11fcf45824be6cf20af2d22ab10", _EFFECTS_FIELDS[1]),
            _Admitted(16, 17, "blur", "float[9]", "float", 9, "global", True,
            "33:1-33:15", "33:1-33:15",
            "51e995c52477f37d8ca6742afc2ea41f49772f3d768d634a2c17aa9613f93072",
            "9e4c4134dfaffa445b9ba85a55cbe5703ca2140ddcbf094766376e32c5fd5453", _EFFECTS_FIELDS[2]),
            _Admitted(17, 18, "edge", "float[9]", "float", 9, "global", True,
            "34:1-34:15", "34:1-34:15",
            "afd5ea3102df22bd2abb2d8a3ad413cc0ce76c79ca5dc05d87ac265e53791b87",
            "5f0643d214959ce4d931d366d8e2cfbe5cacd19f31fe7831766b6596b295f2ea", _EFFECTS_FIELDS[3]),
            _Admitted(18, 19, "edge2", "float[9]", "float", 9, "global", True,
            "35:1-35:16", "35:1-35:16",
            "f98f4119a4a26ca2dc7b3acc39a519085ac872d0c3042efe63bb04a11a88c4dd",
            "88e0db0dc797dcaffcf84fe2b582199d2f7af45720e21539030ce48d7af5e005", _EFFECTS_FIELDS[4]),
            _Admitted(19, 20, "edge3", "float[9]", "float", 9, "global", True,
            "36:1-36:16", "36:1-36:16",
            "4c5554eee7fada45516d49e775096a1f1125eb6c347a19471f3876e9eff6ac8e",
            "c86003a8c86d05aa65461dc96ab9d7b4e0c0eb307190ae8df1f9220aa1f784cb", _EFFECTS_FIELDS[5]),
            _Admitted(20, 21, "sharpenBlur", "float[9]", "float", 9, "global", True,
            "37:1-37:22", "37:1-37:22",
            "a298b485bacd6993f1f66020280a31131e92fdb998d3e6ebe1f30eec4c8cab89",
            "fd295343c13390d0e3cf3c27a598713d32870aae13f8a0a52698e1423a31fd50", _EFFECTS_FIELDS[6]),
        ),
        "frame": ArrayFrameContract(
            _FRAME_STRUCT_NAME, _FRAME_INSTANCE_NAME,
            _FRAME_INSTANCE_SCOPE, True, _HELPER_PARAMETER,
            _HELPER_PARAMETER_ORDINAL, _WRITER_PARAMETER, _FRAME_WRITER,
            _EFFECTS_FIELDS),
        "writer": (75, "loadKernels", "void", 0, "41:1-77:2"),
        "writer_body": (
            ("expr", "44:5-44:22"),
            ("expr", "44:23-44:40"),
            ("expr", "44:41-44:57"),
            ("expr", "45:5-45:22"),
            ("expr", "45:23-45:39"),
            ("expr", "45:40-45:56"),
            ("expr", "46:5-46:21"),
            ("expr", "46:22-46:38"),
            ("expr", "46:39-46:55"),
            ("expr", "49:5-49:23"),
            ("expr", "49:24-49:41"),
            ("expr", "49:42-49:60"),
            ("expr", "50:5-50:22"),
            ("expr", "50:23-50:40"),
            ("expr", "50:41-50:58"),
            ("expr", "51:5-51:23"),
            ("expr", "51:24-51:41"),
            ("expr", "51:42-51:60"),
            ("expr", "54:5-54:19"),
            ("expr", "54:20-54:34"),
            ("expr", "54:35-54:49"),
            ("expr", "55:5-55:19"),
            ("expr", "55:20-55:34"),
            ("expr", "55:35-55:49"),
            ("expr", "56:5-56:19"),
            ("expr", "56:20-56:34"),
            ("expr", "56:35-56:49"),
            ("expr", "59:5-59:20"),
            ("expr", "59:21-59:36"),
            ("expr", "59:37-59:52"),
            ("expr", "60:5-60:20"),
            ("expr", "60:21-60:35"),
            ("expr", "60:36-60:51"),
            ("expr", "61:5-61:20"),
            ("expr", "61:21-61:36"),
            ("expr", "61:37-61:52"),
            ("expr", "64:5-64:21"),
            ("expr", "64:22-64:37"),
            ("expr", "64:38-64:54"),
            ("expr", "65:5-65:20"),
            ("expr", "65:21-65:36"),
            ("expr", "65:37-65:52"),
            ("expr", "66:5-66:21"),
            ("expr", "66:22-66:37"),
            ("expr", "66:38-66:54"),
            ("expr", "69:5-69:23"),
            ("expr", "69:24-69:41"),
            ("expr", "69:42-69:60"),
            ("expr", "70:5-70:22"),
            ("expr", "70:23-70:38"),
            ("expr", "70:39-70:56"),
            ("expr", "71:5-71:23"),
            ("expr", "71:24-71:41"),
            ("expr", "71:42-71:60"),
            ("expr", "74:5-74:27"),
            ("expr", "74:28-74:49"),
            ("expr", "74:50-74:72"),
            ("expr", "75:5-75:26"),
            ("expr", "75:27-75:48"),
            ("expr", "75:49-75:70"),
            ("expr", "76:5-76:27"),
            ("expr", "76:28-76:49"),
            ("expr", "76:50-76:72"),
        ),
        "writer_call_count": 1,
        "writer_call": {
            "statement_index": 15,
            "span": "583:5-583:18",
            "sha256": "9e7911aef1440d34b0ffb73781070b22ed96057bd4c9da2f18961e7dd14525f0",
        },
        "state_consumer_ids": frozenset({("brightnessContrast", 67), ("offsets", 78), ("periodicFunction", 81), ("saturate", 88)}),
        "state_consumers": ((16, ("offsets", "periodicFunction")), (20, ("brightnessContrast",)), (21, ("saturate",))),
        "main": (76, "main", 23, "551:1-597:2"),
        "main_body": (
            ("decl", "552:5-552:53"),
            ("decl", "553:5-553:44"),
            ("decl", "555:5-555:28"),
            ("decl", "557:5-557:36"),
            ("if", "559:5-561:6"),
            ("expr", "564:5-564:33"),
            ("expr", "565:5-565:15"),
            ("expr", "566:5-566:17"),
            ("expr", "567:5-567:15"),
            ("decl", "570:5-570:33"),
            ("expr", "574:5-574:100"),
            ("expr", "575:5-575:110"),
            ("expr", "577:5-577:120"),
            ("expr", "578:5-578:120"),
            ("expr", "580:5-580:20"),
            ("expr", "583:5-583:19"),
            ("decl", "585:5-585:57"),
            ("decl", "587:5-587:22"),
            ("decl", "588:5-588:90"),
            ("expr", "589:5-589:23"),
            ("expr", "593:5-593:47"),
            ("expr", "594:5-594:37"),
            ("expr", "596:5-596:23"),
        ),
        "stores": (
    _StoreRecord(base_id=15, base_name='emboss', index=0, value=-2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='44:5-44:21', assign_sha256='5a1b3b97ba371cb2a4f962878161b265910e2d05d49feb382b24499ea28750fe', target_span='44:5-44:14',
            target_sha256='322749d230928cb11a63befe230e73541c505d3cc37b50f324167f0b99094493', index_span='44:12-44:13', index_sha256='5715fcd9211809189a380895e780cdaa641110b3364e516e1f5e0e181f6158dd', value_span='44:17-44:21',
            value_sha256='1e3a0af9e83b84fac20c33f21692e1c605893f27fed3fb879377ae7ec8a3fc85', statement_index=0, statement_kind='expr', statement_span='44:5-44:22'),
    _StoreRecord(base_id=15, base_name='emboss', index=1, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='44:23-44:39', assign_sha256='678520b399be460db316bc1d2a3c8e2d8bcf6675d873b514db92038f22e52ae2', target_span='44:23-44:32',
            target_sha256='79749e8c39c22674ab4dd86b8db0ee312e9148b813ab6f03e6a5419f2b0404ba', index_span='44:30-44:31', index_sha256='5e3d6a4d57f6010c890f465634227971fa87d5de94455778cf535a2b8392ac01', value_span='44:35-44:39',
            value_sha256='a28947fd8fb0a5a5982d2e77dc36ab3650d560950e198f8bfec25655688c3c80', statement_index=1, statement_kind='expr', statement_span='44:23-44:40'),
    _StoreRecord(base_id=15, base_name='emboss', index=2, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='44:41-44:56', assign_sha256='fee1984a36b0ea5aba2ea29296826e3f3b9214a03f83dff4818e94f3320434a8', target_span='44:41-44:50',
            target_sha256='bc8ec824ed91208388e387ae02dfb8e95252042df0809e63b73c38e0be285092', index_span='44:48-44:49', index_sha256='1db69a378cc141c623f1ad4ea0e7f091e12b4c8576f056fb82e3d00b4091de86', value_span='44:53-44:56',
            value_sha256='8eb34e1fbc78171bab16465e5a13028b5f9daa20f9f84f422b0ac47fd6e99c7a', statement_index=2, statement_kind='expr', statement_span='44:41-44:57'),
    _StoreRecord(base_id=15, base_name='emboss', index=3, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='45:5-45:21', assign_sha256='348019097c296e09394686c198d020c69b9db98178c817d5f7a5953faf1f2669', target_span='45:5-45:14',
            target_sha256='f398f128f1ac2184a667fc8ba09d1322ee40bf057e118e5dfcab2b5d172a58ef', index_span='45:12-45:13', index_sha256='cd3a38912a39c7b56328f1c7373cf4232def4059e145fdeb84f8c67db353b84b', value_span='45:17-45:21',
            value_sha256='d874cf32e7f1b6358139b434d30d35fee10d7c4979c51cebab6acbb979967f06', statement_index=3, statement_kind='expr', statement_span='45:5-45:22'),
    _StoreRecord(base_id=15, base_name='emboss', index=4, value=1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='45:23-45:38', assign_sha256='da1228c5f3b9dac566bd5a768b920542ecd2f6b57f96bdfef3357e711be2f356', target_span='45:23-45:32',
            target_sha256='700a66e09149a83369e3c42ee7892b9ddf47df3d802eb86af304fdb3a7a49c01', index_span='45:30-45:31', index_sha256='a064af964f26c908b97ce0deb1c13bf38d16ea1a7108bdf5a9febe93ba991243', value_span='45:35-45:38',
            value_sha256='17446c830ec2159f284886673b6cc691ad8cc41eb8368ccf26a0761f011ad3ed', statement_index=4, statement_kind='expr', statement_span='45:23-45:39'),
    _StoreRecord(base_id=15, base_name='emboss', index=5, value=1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='45:40-45:55', assign_sha256='1c0fb328fbd75ae9f08d0b283139e7c733bf652d3fd16ea25cde70ca5f7b12d2', target_span='45:40-45:49',
            target_sha256='b9098fe4dd5d3a98be1701b6a7dde033bcec088d0cdc4a180d4f2775c9a7292f', index_span='45:47-45:48', index_sha256='ebf92dd1690a95b39ccd4c3499c5b7a315593c9b3065a7fb6ecd5cf596b038c0', value_span='45:52-45:55',
            value_sha256='bdf14fe9f52d98c8971266ed700f047df73e764a29f0900dfa47fa3280c5a92c', statement_index=5, statement_kind='expr', statement_span='45:40-45:56'),
    _StoreRecord(base_id=15, base_name='emboss', index=6, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='46:5-46:20', assign_sha256='c810206637052aa42ed59ee17d8fa01d6a5ce7800b6c664dd80ea7f8231ae3eb', target_span='46:5-46:14',
            target_sha256='8efa8ff0ecec09d4b2a6917dfdee19a6dae680e8ee78b47b264f9de3c304b8aa', index_span='46:12-46:13', index_sha256='3ac3eaa357ad4bfbb508ceb7c59564625d7c2d31b9f0a34f393d0d3e66fd9142', value_span='46:17-46:20',
            value_sha256='bba5a4c1f9e413b42b719afda068bbdc276f58b3b3f970c0397018219ecff52c', statement_index=6, statement_kind='expr', statement_span='46:5-46:21'),
    _StoreRecord(base_id=15, base_name='emboss', index=7, value=1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='46:22-46:37', assign_sha256='6402e4df303fe908be8e1415348c7d2d8f142f913d5809ef23aaec2359f94612', target_span='46:22-46:31',
            target_sha256='898d5e875d7b49dae7771f07094b6544637219a6da108a6f7fbdfaeb0d598051', index_span='46:29-46:30', index_sha256='c883e803cc6735178a5c2bfc72ec79e8bdc143bbc95c0f32a8a5c874443745cc', value_span='46:34-46:37',
            value_sha256='ca7ef6fb4aa45470da28883837f07f83c018f49c60ae0ec59fb875198e81617e', statement_index=7, statement_kind='expr', statement_span='46:22-46:38'),
    _StoreRecord(base_id=15, base_name='emboss', index=8, value=2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='46:39-46:54', assign_sha256='877958d6072f321d52ebf6fe5dad27ac8da1adf9ef91e6f68bdd25f6d8de6b47', target_span='46:39-46:48',
            target_sha256='465c54def8be476ec8d4414cf5a77926242fa62bee3cec95c17397d5e97c3d64', index_span='46:46-46:47', index_sha256='ef771e7c3d1d1763546c852e8ff5b310389617434fa193000a913ba5d2326398', value_span='46:51-46:54',
            value_sha256='dfaf7f1d5ada1b526683beba5767f7256d1e1f8a3a6e2063e6fa5de1928069e0', statement_index=8, statement_kind='expr', statement_span='46:39-46:55'),
    _StoreRecord(base_id=16, base_name='sharpen', index=0, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='49:5-49:22', assign_sha256='8930d25e8144acb3e1024e53a1330444420ace9aba38bf0cb29f7dbde8195a6e', target_span='49:5-49:15',
            target_sha256='820ee86fa7aae1167b37183b750a761ef5c9d3318b6450d83ae40a532deb5c78', index_span='49:13-49:14', index_sha256='104994007b85c045dcc2c3c86e332bc484073b691381040a0afb5dbf34d737ed', value_span='49:18-49:22',
            value_sha256='74e16d4ac3aaa09c4f46d4f4293705a82f1bf4cc42326b975ef10d508e6dc40d', statement_index=9, statement_kind='expr', statement_span='49:5-49:23'),
    _StoreRecord(base_id=16, base_name='sharpen', index=1, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='49:24-49:40', assign_sha256='aaada5acc7125707d83df9a8310aa50f71b048540f9428bff1f8a0efa2268df2', target_span='49:24-49:34',
            target_sha256='de7a553a418546374797299e998ed49fe97db9b512f0b190300591fed9a83134', index_span='49:32-49:33', index_sha256='838fd244f481f893aea18d91316f41358447964cee5ada313e2bba9ca047c54a', value_span='49:37-49:40',
            value_sha256='ce2a6854afce87ee287fccee57277f28e10f2926ef6275f9cbded7a04165204a', statement_index=10, statement_kind='expr', statement_span='49:24-49:41'),
    _StoreRecord(base_id=16, base_name='sharpen', index=2, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='49:42-49:59', assign_sha256='1a6ba74e713c68d37d93b099f289767ec66fcc813110b39c0f0ffb58e4ee0d02', target_span='49:42-49:52',
            target_sha256='4261f453437ca9df15539686b070a2439359eaf5315a130f5aa47e3c712735c5', index_span='49:50-49:51', index_sha256='0f5714a9fb87cf015a97c8c15d801c131c73760e6bb7104df88afe1b413f8ef3', value_span='49:55-49:59',
            value_sha256='6e3d8c1da7dab4740d6475062622b5256312f12a04675bb8aa1da7d308e1dacd', statement_index=11, statement_kind='expr', statement_span='49:42-49:60'),
    _StoreRecord(base_id=16, base_name='sharpen', index=3, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='50:5-50:21', assign_sha256='014eb8c0e92d86f08289efc0b3139cd18f8fdb99ee46c5e88e4d4d00bbccd9e4', target_span='50:5-50:15',
            target_sha256='8d985cb1e41e7edf9d8bd635b4c2a652820118476894ebfa5cdb71aed3046e97', index_span='50:13-50:14', index_sha256='048d481be44e876eeeedb347224ee37e5d06deefdc7b2ed09553dae6a0bf331e', value_span='50:18-50:21',
            value_sha256='58d8c785744e9022a35af68bd1a152bc0fd73e52cd03aa95587780c6c170a689', statement_index=12, statement_kind='expr', statement_span='50:5-50:22'),
    _StoreRecord(base_id=16, base_name='sharpen', index=4, value=5.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='50:23-50:39', assign_sha256='8cfcc62c4e3a3a6dfc96733013fadc0a8447cb725df79c41112c605f10278f66', target_span='50:23-50:33',
            target_sha256='8c8c66729aba2014f6ad8a2397f003d60affd7dc48928862f75d02688c0e97ef', index_span='50:31-50:32', index_sha256='03896bb71a8fcb1dcc5df1eea5ffcd86bb02b1a02dbe76f6a8f08e3d470a1817', value_span='50:36-50:39',
            value_sha256='7d4ec5e4070568dd92ca5e6de475c770719c1bd0458551bb9b7abb4ac5d21b21', statement_index=13, statement_kind='expr', statement_span='50:23-50:40'),
    _StoreRecord(base_id=16, base_name='sharpen', index=5, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='50:41-50:57', assign_sha256='3f08a408240b315751838b4eba5ab80a7eb537cd39178997eee669d64812ac19', target_span='50:41-50:51',
            target_sha256='5e121830d63b38b31780b70743149538fe643a772a9297d4d175e9273e162c6f', index_span='50:49-50:50', index_sha256='7253b77e80f6a09d7bac2733a083248bc524d5b8f4307629f2401052579f6dba', value_span='50:54-50:57',
            value_sha256='dbb271520ea6a5be50eb75a77c27226e3b7ddfead15c218f32d843fd634d4913', statement_index=14, statement_kind='expr', statement_span='50:41-50:58'),
    _StoreRecord(base_id=16, base_name='sharpen', index=6, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='51:5-51:22', assign_sha256='58e3fff2325dfe9ddc715bedb5d594d82f2b19a5d858a3750d6e5ba68b02c6eb', target_span='51:5-51:15',
            target_sha256='62c1dbb627b5c651ab8435775467769475c9f5fa6d61207b77f082461fb94cd3', index_span='51:13-51:14', index_sha256='1ae537bd625c1a953941020f66cc569f3ae3754ba068e3ed2723977703d8e7a6', value_span='51:18-51:22',
            value_sha256='227f2074d4060f6dde1b57a36ac5b60820cbd2786204e8cb0b79a40cbedf452a', statement_index=15, statement_kind='expr', statement_span='51:5-51:23'),
    _StoreRecord(base_id=16, base_name='sharpen', index=7, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='51:24-51:40', assign_sha256='c00143b1783aafd36da0def859588010ea68874d6abefe0c807a14e103553f87', target_span='51:24-51:34',
            target_sha256='46178e19293a1b3b4433a2be7cf501a4563f68dce3471c356d68fcaf7c5a0f59', index_span='51:32-51:33', index_sha256='455f658015b47882ae8999725efa3c4450b1fd448b5acb17ad6823f48392682d', value_span='51:37-51:40',
            value_sha256='439b223d53fd27475b3ae1de96cc803f0415e669cdb423eff66ad29804eebb98', statement_index=16, statement_kind='expr', statement_span='51:24-51:41'),
    _StoreRecord(base_id=16, base_name='sharpen', index=8, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='51:42-51:59', assign_sha256='2d204411478530b60daed284178889c059c2de85fc501c3409d54b392f5c175c', target_span='51:42-51:52',
            target_sha256='ba95b45d04aec84db5d292a78e9ef4c7346e6639ee06ebfe8c30697dae08b771', index_span='51:50-51:51', index_sha256='c1a1b36d5c75cce48029c2de58fa5eb453dbc273dd3318093ea45952817a7856', value_span='51:55-51:59',
            value_sha256='de3a3ff282d72377d5dd5e54966dda2df5cad207292e959ed58cf336b8f0d569', statement_index=17, statement_kind='expr', statement_span='51:42-51:60'),
    _StoreRecord(base_id=17, base_name='blur', index=0, value=1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='54:5-54:18', assign_sha256='6fab995c784c3e4ce0785d9fbb019f28264cdf46f06057553f6660bdef6e6c86', target_span='54:5-54:12',
            target_sha256='c6d81ad3a31b6206490fa1ea3dc7ba92b4bcea60e9e186654c0c24a5326ef293', index_span='54:10-54:11', index_sha256='2350fa72f724ad71c79ed4e86f54089d3ea89767ada1fbedd315ed535263ae99', value_span='54:15-54:18',
            value_sha256='4a83bc9c446ee623fa1bcf76f8b83aa5c32d6ef567f3f57adf90a36daf821dc8', statement_index=18, statement_kind='expr', statement_span='54:5-54:19'),
    _StoreRecord(base_id=17, base_name='blur', index=1, value=2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='54:20-54:33', assign_sha256='f1f0de7cb8ea1bcfd62422af15dcbf8ce0dfb30ea56530ee3708390925931f6e', target_span='54:20-54:27',
            target_sha256='d870c5cf1c082c3bbbd9b5dc59bed13b5bce01b0c0be024497af85e2e0329893', index_span='54:25-54:26', index_sha256='b5896d7d5ad25e4efa0037c97d8e1cfdd19339b160258c6b954bf4d5fc13f0b9', value_span='54:30-54:33',
            value_sha256='364f4ffb22f3ed8e2ffa3526505fc55da514f6a4dc90171fcb6945d12dfad0ed', statement_index=19, statement_kind='expr', statement_span='54:20-54:34'),
    _StoreRecord(base_id=17, base_name='blur', index=2, value=1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='54:35-54:48', assign_sha256='5aea0d8bb5f9089362ddbc367ba4cbfd66319367d2797a5d0f9e9923ce2d865f', target_span='54:35-54:42',
            target_sha256='b956c846b513a3a1948c659c04fcf836aa3ba774ade080160581fa84ba776c83', index_span='54:40-54:41', index_sha256='359856be249cd0e6fff94fdc729186c8db3ce383f5fd8e64d879c26cc106c40a', value_span='54:45-54:48',
            value_sha256='40ea18a31e925cfe1d936578e9839171495cdb65cdb3431dc8a44c55f6a892e6', statement_index=20, statement_kind='expr', statement_span='54:35-54:49'),
    _StoreRecord(base_id=17, base_name='blur', index=3, value=2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='55:5-55:18', assign_sha256='e3293bda98276249b86222f91b37f65f3066cd056683e003c7d1e16c44289d56', target_span='55:5-55:12',
            target_sha256='406628d7e765ae4d758a070f34882a5fc56df6f80dfd90464ceaabf738498143', index_span='55:10-55:11', index_sha256='aa85b6731deea47bb34c8161d56615295523714ea2f8750d53876c1f1d8e876c', value_span='55:15-55:18',
            value_sha256='33a6f3a2fc6b477d1e6176f38eed6a93eb418251281bfe089c547b3a6a23ad6e', statement_index=21, statement_kind='expr', statement_span='55:5-55:19'),
    _StoreRecord(base_id=17, base_name='blur', index=4, value=4.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='55:20-55:33', assign_sha256='fc65100b785b9aebfb0ba2831cca04ea8f5d671907b9518b79a81353da541843', target_span='55:20-55:27',
            target_sha256='7ba459dc6952970892b9a7bb969e5854683eb9112ec4d162f15502f3ec33995c', index_span='55:25-55:26', index_sha256='32f9d429c0bb755a76e7a5f80da5e6a8619b3ad96076bee52c61236201e4af40', value_span='55:30-55:33',
            value_sha256='3cb3a321191eb3b4900aeb0872195670a93e1928025f29de7f2de1bc1971b221', statement_index=22, statement_kind='expr', statement_span='55:20-55:34'),
    _StoreRecord(base_id=17, base_name='blur', index=5, value=2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='55:35-55:48', assign_sha256='1fdb955f064e716c33cb0543bd21c01f70c56e2a7a39fb663bff5beca7ea05d8', target_span='55:35-55:42',
            target_sha256='8d8fdc7a7b0b2e1a6837acebafb89467559e99b4b24c1012baaff9690db48c82', index_span='55:40-55:41', index_sha256='f93aaf625c240a9178808968fa8d51cf25b16aa1d1c5c23d38a47fc7f2d89044', value_span='55:45-55:48',
            value_sha256='a9aa3522b08c9353a1d6ae21edf746142455fd07bd38308fe86c94df0a28758c', statement_index=23, statement_kind='expr', statement_span='55:35-55:49'),
    _StoreRecord(base_id=17, base_name='blur', index=6, value=1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='56:5-56:18', assign_sha256='aa26090b0066e465b1dd6a468b8d8a011453b45f5cdf91b1db22e91c60237294', target_span='56:5-56:12',
            target_sha256='acacc873c55e1c76f97470166253675fea51dc6c9c1f7ebd0b82ac97b65bd7ba', index_span='56:10-56:11', index_sha256='4e78fdedeabe48b1a7467e594cef1aa14fa3e2b9ed35da6202366dbc6da4ecee', value_span='56:15-56:18',
            value_sha256='c700a367366452152d72427b11589e054361348f35c9f634bfb5faeeec0e572f', statement_index=24, statement_kind='expr', statement_span='56:5-56:19'),
    _StoreRecord(base_id=17, base_name='blur', index=7, value=2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='56:20-56:33', assign_sha256='784b393f2e5da059c1c94da76e94a0fae6c1098044f3ebd2691b152bb1cb565f', target_span='56:20-56:27',
            target_sha256='c9e0a271f8fe2be634e8848ac16de317b9196923c68ff448aa085fc9bcd42fdc', index_span='56:25-56:26', index_sha256='632c2d1d406ca3168fab1e6c00c168eaf54b1e6518d13b5257224d71e214c42d', value_span='56:30-56:33',
            value_sha256='fc70edd1cd1428f93a7d10f7f9f8e45a36f26dd8039091d90a2083e326de86ae', statement_index=25, statement_kind='expr', statement_span='56:20-56:34'),
    _StoreRecord(base_id=17, base_name='blur', index=8, value=1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='56:35-56:48', assign_sha256='288c99497b0c95f717908460d86f474dde8e7c5bae5736d7c996f7268b5d5085', target_span='56:35-56:42',
            target_sha256='5b1fb68ef9203f5f7b529ee24dfaafa37955856a14527883624d6dd3efdb2e32', index_span='56:40-56:41', index_sha256='890dfbe6c9ef39d96f4c862cffbfa278f127fd245f87014ebc75c12721379bb1', value_span='56:45-56:48',
            value_sha256='a93741f11666f0739f083c9017e4472ce84e1e161d18c4b7a76c114f00b87623', statement_index=26, statement_kind='expr', statement_span='56:35-56:49'),
    _StoreRecord(base_id=18, base_name='edge', index=0, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='59:5-59:19', assign_sha256='5e22a31a2ddabcfb471a6c37109192d9619bae9e4348382b95a362a5bf52fce9', target_span='59:5-59:12',
            target_sha256='f760ff13291f54ed8ea143e1cf3b192758a0f84428bcc7f5d438c59c57248f6c', index_span='59:10-59:11', index_sha256='1d18c3c1244f7e89359517fc7f663f2c8644fb2f4493b9f259356e9d0128d96f', value_span='59:15-59:19',
            value_sha256='d3c59c866843b013be0467561e8d5ce3c05574ef0d85c68b494407f587835e8c', statement_index=27, statement_kind='expr', statement_span='59:5-59:20'),
    _StoreRecord(base_id=18, base_name='edge', index=1, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='59:21-59:35', assign_sha256='6c0e9684be8bb920f9a871a14fe3ac4d9522c156a7a9984e6b9ce89bfeefd76c', target_span='59:21-59:28',
            target_sha256='69fa71a89c6c00d68f834d5be77a363de33e545323883f95f17c9cb924fd713b', index_span='59:26-59:27', index_sha256='d4650b6b9fc9574ac264884d649b5d6635b34d7fb4371b5647e26b1954206c07', value_span='59:31-59:35',
            value_sha256='7a487c9b861ad781a31c2075f53da63229457a92171e263252b74afeb837e146', statement_index=28, statement_kind='expr', statement_span='59:21-59:36'),
    _StoreRecord(base_id=18, base_name='edge', index=2, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='59:37-59:51', assign_sha256='cd8bf449e9e505cfffbbc03405021a3d7703ce85fb63d7bc04db46e30857681e', target_span='59:37-59:44',
            target_sha256='3a5cfb649f806ea3edf4fbb7fab221cefffede30ff3dbe44f6841db9204f4719', index_span='59:42-59:43', index_sha256='b94198a1498fba1c921f9e5c1b5a69f2f0eb69c2b0d7ea95b218e6470ffbaf08', value_span='59:47-59:51',
            value_sha256='38fcfa9706a1dbb9bb653538718a593ec4af9e35d535077a593eb93f447b8f52', statement_index=29, statement_kind='expr', statement_span='59:37-59:52'),
    _StoreRecord(base_id=18, base_name='edge', index=3, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='60:5-60:19', assign_sha256='a3f51401adb5095944d9edf117e58d8f1168d00c519f8f982d2c0859c1b27d16', target_span='60:5-60:12',
            target_sha256='e4bb2e321a42f1d320a908615c23889b0063f4326eb3d081c8b8b5c1b49daf36', index_span='60:10-60:11', index_sha256='213a279f53176c08c725debc4517f5ca16a9d4dafe9149484f684f5a9dd88262', value_span='60:15-60:19',
            value_sha256='53d9fbc86c16c7e2598d605232130da487a9330af1550b9700d5b34ca7a35045', statement_index=30, statement_kind='expr', statement_span='60:5-60:20'),
    _StoreRecord(base_id=18, base_name='edge', index=4, value=8.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='60:21-60:34', assign_sha256='724bd1c932da438b53de572c2f8d12b7c23b86ffb9c35869cc759d1ad537ae9f', target_span='60:21-60:28',
            target_sha256='e01303e1eca787d83634a8b8f7f8a0704f159255df188930289c244497206e0f', index_span='60:26-60:27', index_sha256='3db1c60ac763500e977170443e9b07dcc19bbe143a92179f4b69bfa58c3d9ee3', value_span='60:31-60:34',
            value_sha256='6edef1974d2cc788d787b4bc9dccd0305402fc4134faee94d40026d7963b5379', statement_index=31, statement_kind='expr', statement_span='60:21-60:35'),
    _StoreRecord(base_id=18, base_name='edge', index=5, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='60:36-60:50', assign_sha256='56847989d593c712fda64468cd5ef463a4cd374a82a3e0f344d56b48ec473289', target_span='60:36-60:43',
            target_sha256='d607ba2a12a01c1929a7c29d940ba4e2d11bf29fab39c361c2380658b97ab23f', index_span='60:41-60:42', index_sha256='f27bb32084cdc8313d15d6075a5017a27733047f62085dbb7254111ea89a746b', value_span='60:46-60:50',
            value_sha256='ae1035a77a592eaffe0fa0a444bf28c5ec69320817ab7f42f8396f30ae63a277', statement_index=32, statement_kind='expr', statement_span='60:36-60:51'),
    _StoreRecord(base_id=18, base_name='edge', index=6, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='61:5-61:19', assign_sha256='2a8305425ea81138c220c1b3216421dd9f6f6557eca63f2baef44453100f6f92', target_span='61:5-61:12',
            target_sha256='c7c4d04bce361f0c3b034fe906d7bac8db05db9dfc1d323698f8f5a457a73041', index_span='61:10-61:11', index_sha256='819e5e9fe9d224b4be2b366a4ab04afc619dc9962cd61e3e04cd1b3c32661d09', value_span='61:15-61:19',
            value_sha256='6342d94bd97e3a91573c41dee1d70673b10891523fd9e2b8ee5a50f477e4a69b', statement_index=33, statement_kind='expr', statement_span='61:5-61:20'),
    _StoreRecord(base_id=18, base_name='edge', index=7, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='61:21-61:35', assign_sha256='ee88d235ea44a77551e3608628971d9c91d99de25658f74ef56433c3fb165f55', target_span='61:21-61:28',
            target_sha256='05b4593457cdde99e8852d6736555d0fb1630ca4ad3780653f935e036c3da74c', index_span='61:26-61:27', index_sha256='8e7f6abb5179fbd51146fe205e9c00346c68e8777843f39b5909e302eb227816', value_span='61:31-61:35',
            value_sha256='e1f74f316f2887d5e911aae48624176bf13b62d8d32ee68013099008558515d2', statement_index=34, statement_kind='expr', statement_span='61:21-61:36'),
    _StoreRecord(base_id=18, base_name='edge', index=8, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='61:37-61:51', assign_sha256='b473e800b9ebab5c75579387ac558a4750205e2c647ddafb134562172191f45f', target_span='61:37-61:44',
            target_sha256='aab9c35c0a43fcd96a26999d72adbd3e24b65554a700115e560307ca9f1d517d', index_span='61:42-61:43', index_sha256='d96b9a126630b0ddaa96cc936254445bac83bf35e1ffa61cf5b374e551de5c89', value_span='61:47-61:51',
            value_sha256='02a34fab8ab33d5db4543d079053f61de7e8a56d79f3c6c09475acfdf226e41d', statement_index=35, statement_kind='expr', statement_span='61:37-61:52'),
    _StoreRecord(base_id=19, base_name='edge2', index=0, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='64:5-64:20', assign_sha256='3d8cf5a52ab5b4849ac75287bd247cb89a1d9025d4575ad154a4032246449eb6', target_span='64:5-64:13',
            target_sha256='3b75b0089b1d3bcefaf9a0a4e4f9cab4891fcaa336e4fc71d7796fc968bc7511', index_span='64:11-64:12', index_sha256='f44ccb39849d7b663011912d81f0ec22499d33673d9f84c77cbddd35324ad875', value_span='64:16-64:20',
            value_sha256='b01bbee2366d0876a71ac1c2a2ba1d259506c82d03f01a5434b6c086cf0b7a68', statement_index=36, statement_kind='expr', statement_span='64:5-64:21'),
    _StoreRecord(base_id=19, base_name='edge2', index=1, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='64:22-64:36', assign_sha256='8b41ffc79653ff1017110b3f433f8ec44610569e747d234f1c7a57cb34caf3b2', target_span='64:22-64:30',
            target_sha256='d4397f03218afc1a086b416044220a23459a168bb15079d3e03a51d10974d2f1', index_span='64:28-64:29', index_sha256='cb24ef3b6f05fbb9feef687c4b1a7b61c4bda5db314839c8faf930685101107d', value_span='64:33-64:36',
            value_sha256='101bb1215ae777cae33db237db2c6931bf67cebb81050f25dad68550e4520509', statement_index=37, statement_kind='expr', statement_span='64:22-64:37'),
    _StoreRecord(base_id=19, base_name='edge2', index=2, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='64:38-64:53', assign_sha256='01f529fbb6a80d98b1590cc441963a4128596289d2e893db6f43f800dc984737', target_span='64:38-64:46',
            target_sha256='b19b77894b4c92beeae2661de0026c8f1d2d08b8c9debaea00ff4c055e906fb1', index_span='64:44-64:45', index_sha256='f5eea1d5636cab32885243398e876b810fa23c8d39425d27f62fd81614cf61f8', value_span='64:49-64:53',
            value_sha256='2cd0d17dea7f59ba8ed6c6715f9aa5bf97c73443834c0946952d1b82745b7a72', statement_index=38, statement_kind='expr', statement_span='64:38-64:54'),
    _StoreRecord(base_id=19, base_name='edge2', index=3, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='65:5-65:19', assign_sha256='d7ea2c4453c71811d2a79b966aa39e8606270cfb59a7ef627902f51b490fae5c', target_span='65:5-65:13',
            target_sha256='0f127fd2e15f44d39262fa177ec7cb4796c66e7c755f52d012a9170efb489ea6', index_span='65:11-65:12', index_sha256='cf075e565d8a2b8fad39855d434be8f00e599ea283007fe9c9788e5922501e6c', value_span='65:16-65:19',
            value_sha256='d5a92b16a20d2ffa3efb83f601f89be7bd5143a66c751441a5b205024545fba8', statement_index=39, statement_kind='expr', statement_span='65:5-65:20'),
    _StoreRecord(base_id=19, base_name='edge2', index=4, value=4.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='65:21-65:35', assign_sha256='23fc792e86a609c88cb9e5e6e845977faa905f5b30bfa84cc3899c1e04d33d24', target_span='65:21-65:29',
            target_sha256='1c955da3d9f644dcf13764b0476aff3bb75307ca73bc067694ef0c2ccdd661b8', index_span='65:27-65:28', index_sha256='0c8ec148070c4e080f1ec90f8e373c7c6e248741c4d608b5cb53ad11f95ab0ea', value_span='65:32-65:35',
            value_sha256='f54019b08b165a01f835f53821a538251b39838cb380ec5ef36385312c1391d3', statement_index=40, statement_kind='expr', statement_span='65:21-65:36'),
    _StoreRecord(base_id=19, base_name='edge2', index=5, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='65:37-65:51', assign_sha256='945cc15a3cfd0751dae49195d568f123bf1b4d2edbcfb9d1199c08481b1d0b01', target_span='65:37-65:45',
            target_sha256='3348f57f351e3db3c5860a4c69d231726a8aa1e77a3969faf2e140f1352f6742', index_span='65:43-65:44', index_sha256='da22db05c635fc3cf113d2a52de0647fd409c46dffb5fbe3eec17aa5a0d25b5b', value_span='65:48-65:51',
            value_sha256='cbc7cbd30b41d26451d006cc0d5e5dfd3ffa2082f299753f5c9d59c28642ed01', statement_index=41, statement_kind='expr', statement_span='65:37-65:52'),
    _StoreRecord(base_id=19, base_name='edge2', index=6, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='66:5-66:20', assign_sha256='f40a68a64beaf2a07557bc9cd2e34f5a28f17e43069d98c39e1c2b4867c5068e', target_span='66:5-66:13',
            target_sha256='22d01f2016593c42d5f7e14c1d78d20c50a10f2c83156e6144030ca0a7c1d371', index_span='66:11-66:12', index_sha256='e4f54b535e3f7ecd44dbf9af1dff4893930bac57006cdb3c0bc0cb611bd0e8d8', value_span='66:16-66:20',
            value_sha256='483e49b3961bb09968a6bbd8df2e0f7af4fa59b162582df7e97b7cfe28dcd498', statement_index=42, statement_kind='expr', statement_span='66:5-66:21'),
    _StoreRecord(base_id=19, base_name='edge2', index=7, value=0.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='66:22-66:36', assign_sha256='00e36629d8ed15daf3f2a4aeef1fe7cb98d449190ec9314738d07865d13da480', target_span='66:22-66:30',
            target_sha256='fecce81537aff4900ddad0772f0301ac04df7193d0f09627d3d22644da306979', index_span='66:28-66:29', index_sha256='597430ffaaef78092e88d25acb5578a61b71cc28ddc8268c464efb60e0a884f4', value_span='66:33-66:36',
            value_sha256='adff9a546223b7b186a7edf4c3351f7858427328791bb4be3541622bc1055140', statement_index=43, statement_kind='expr', statement_span='66:22-66:37'),
    _StoreRecord(base_id=19, base_name='edge2', index=8, value=-1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='66:38-66:53', assign_sha256='71e297f1f8ee9b70002bbb9e186aa33725a088c84ec6c8a44b9faf63685fe6d1', target_span='66:38-66:46',
            target_sha256='087ce23eaaed7e1e56300c01306621ecffcfedeb72b0d498e83f1ef5767d10aa', index_span='66:44-66:45', index_sha256='2aac3126882a3f66551e1e77a1f4a2a9bd74e598004b739a90955f3eeb7dd1ae', value_span='66:49-66:53',
            value_sha256='11323060b67ad03dd66b19be9d39b001ce8b3c49b7d866530b735f657ecc233a', statement_index=44, statement_kind='expr', statement_span='66:38-66:54'),
    _StoreRecord(base_id=20, base_name='edge3', index=0, value=-0.875, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='69:5-69:22', assign_sha256='3926837b6b0e5d507126e860264c965a6e7f06c5e57363adbdcde9351ece4230', target_span='69:5-69:13',
            target_sha256='b3cb6ea1381d18af08bf4f816c42334b3bbbaa36b2a86e656049cf95a8ecb1f4', index_span='69:11-69:12', index_sha256='38cef5ae00dba91c8809a9fee35f98f951aae33031f3a0af00cd416dc2d6e5b3', value_span='69:16-69:22',
            value_sha256='00d8a44fe504e6d7aee53ac2f51d030492da4139f3fbc75de2403f96952a914d', statement_index=45, statement_kind='expr', statement_span='69:5-69:23'),
    _StoreRecord(base_id=20, base_name='edge3', index=1, value=-0.75, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='69:24-69:40', assign_sha256='f7fca97cb623b1e3f941072b76cd441bb661e52c21ecab011a764a988c9c6b49', target_span='69:24-69:32',
            target_sha256='37247b43013995af969f4c3736c979d6bb78b70052014af5615ccb39d7e50119', index_span='69:30-69:31', index_sha256='b035df1d73ab553920315ffd14034d292c3e21a165cf43eb3113e11484cbff26', value_span='69:35-69:40',
            value_sha256='520822c8195c83ca8336c66a85031246d4671f16edc6de7d0968bb5d334031fb', statement_index=46, statement_kind='expr', statement_span='69:24-69:41'),
    _StoreRecord(base_id=20, base_name='edge3', index=2, value=-0.875, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='69:42-69:59', assign_sha256='4dedb32e73c16daf6cd3fc03fbf485c5765cebe869e20ec2b1ce6644bf625587', target_span='69:42-69:50',
            target_sha256='b27e797a6338a2d2d18405bad9417b3908f6e750849fd1f99154a8c44bd90669', index_span='69:48-69:49', index_sha256='7679e7fbde93608970161afbe6fcd1ce6c5e83bb3cb20b5d23e3be39e605ebd7', value_span='69:53-69:59',
            value_sha256='6525b6887e7bd5c1bca77fe248eb6c2849903d2a1a651c29c758a95134b29368', statement_index=47, statement_kind='expr', statement_span='69:42-69:60'),
    _StoreRecord(base_id=20, base_name='edge3', index=3, value=-0.75, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='70:5-70:21', assign_sha256='b04ca22b79312e5b4aa70d815b01e27832d1d0115323813549d51ca0f0559b37', target_span='70:5-70:13',
            target_sha256='4bd4d8f985d595813a49b1ea09bf70558ba381ec72bd7529d5b5d41e5763525e', index_span='70:11-70:12', index_sha256='6e846484fd4910107655b344d552b8aefb5aa70e125dc6b1d382f65b1e6af0c1', value_span='70:16-70:21',
            value_sha256='d3c0e0568f0c6177d0eaf8e6187326324e53748802979e3c977719b86f25915d', statement_index=48, statement_kind='expr', statement_span='70:5-70:22'),
    _StoreRecord(base_id=20, base_name='edge3', index=4, value=5.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='70:23-70:37', assign_sha256='beb5bd8613eb172627354cb84a8f40501efb1d10211d4e75995fac0b216d3bc6', target_span='70:23-70:31',
            target_sha256='5bb8d242d44e5a24bd8992ad812180b2f989134a789730a5fed424afaed195b9', index_span='70:29-70:30', index_sha256='795ee4cafa80e35b2baf241645f0abc4084172b448a8374fd935c1dd0538f8db', value_span='70:34-70:37',
            value_sha256='ade3b1cf7746dbd5aabab8663dcf5ee36e4c4b21f24b887efd914c19234d483b', statement_index=49, statement_kind='expr', statement_span='70:23-70:38'),
    _StoreRecord(base_id=20, base_name='edge3', index=5, value=-0.75, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='70:39-70:55', assign_sha256='26eb68e63245c180d0db8e9fd2e90939ef21e8e756c9c47ae5df7f9fb76625cb', target_span='70:39-70:47',
            target_sha256='d513b73b74df113ece4b811512eb434efd6d4345b917bd08d36834b1baab201a', index_span='70:45-70:46', index_sha256='dfd5b0e2012edb59aad111cefd4bc05f1199b36aff38b44e64313958d5ab7ed7', value_span='70:50-70:55',
            value_sha256='11bd7a9db6c188d2401a65e10b7e54a46f3a0f8c037e9d14d06129ae24a966fb', statement_index=50, statement_kind='expr', statement_span='70:39-70:56'),
    _StoreRecord(base_id=20, base_name='edge3', index=6, value=-0.875, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='71:5-71:22', assign_sha256='b4e999a704985b39b9589c558c9a3c4d4a554ecd7bc0e80a8a7d4c117ee1120f', target_span='71:5-71:13',
            target_sha256='e48759e147afdaec9229d4b06ea240150dda21e30b298a4680534b625db297a6', index_span='71:11-71:12', index_sha256='fdea3a377cd6e151a0403b6ac93cf877c61b4a6a00fb1419c14426d686633ad3', value_span='71:16-71:22',
            value_sha256='3499c90cc555f74e2df3fe5cf7fcea82873f8ba8fc54a3e072071f9a7cfe10f6', statement_index=51, statement_kind='expr', statement_span='71:5-71:23'),
    _StoreRecord(base_id=20, base_name='edge3', index=7, value=-0.75, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='71:24-71:40', assign_sha256='9f148b1b9b91cca438ef9aef99b53de57a11dcd21eeb6eef3ff633b71143f49d', target_span='71:24-71:32',
            target_sha256='6bc93f8cb2c8102b167538beaaa7612d9125589019ff9daed1e33322167e4e01', index_span='71:30-71:31', index_sha256='6012127f71b7fe3241e39c79d5066cfcbaee7e7abc364e94bacc6971589566a3', value_span='71:35-71:40',
            value_sha256='8136b9fb956a942cd60922dd807a11d3eeb98b2229dec8b8c2894b4aa59f8a08', statement_index=52, statement_kind='expr', statement_span='71:24-71:41'),
    _StoreRecord(base_id=20, base_name='edge3', index=8, value=-0.875, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='71:42-71:59', assign_sha256='4e4acbc93c0af5eb596b7348d47cb7356fefec49460c1eef414d767b8c0e0ab6', target_span='71:42-71:50',
            target_sha256='da996aa902e8e609e954fa2c1f1b7681c9442a9e104d2ad2532a5fd8b0944c7b', index_span='71:48-71:49', index_sha256='ef3f079f5fee026a7bf306e7322ceb04f515f333ac716fa50fbd782730f24ea5', value_span='71:53-71:59',
            value_sha256='49a2fc6774ce6530ee39bc83b577fbb35237cc13ffb9ec887ef261d4827a1033', statement_index=53, statement_kind='expr', statement_span='71:42-71:60'),
    _StoreRecord(base_id=21, base_name='sharpenBlur', index=0, value=-2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='74:5-74:26', assign_sha256='b37fa924a189265c16b12fcdf7658dfa5486a8fcd8ecf488735b41cf04f78745', target_span='74:5-74:19',
            target_sha256='aeb658e37c6be74cb2bc29da8f42738c96ab8e4825699152cedca00f419244f5', index_span='74:17-74:18', index_sha256='80f72fb7fe21d8cb9c385fb25f691113a7e895bcde22f7f36b8af34e5d03a063', value_span='74:22-74:26',
            value_sha256='3a3690a828e655eceb44bd16d2c09ecaf9ed3df64b6e7f75258cd720530cd8cf', statement_index=54, statement_kind='expr', statement_span='74:5-74:27'),
    _StoreRecord(base_id=21, base_name='sharpenBlur', index=1, value=2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='74:28-74:48', assign_sha256='fb9db3f57fddbe9a7b749720cecb20e5b1096e30b3eb44b93a6a9ec44d2dd41f', target_span='74:28-74:42',
            target_sha256='d4664ef1b582eac09e9d93c5ec52fef9b72a10bf07e3136f52b94f0acd30ea5e', index_span='74:40-74:41', index_sha256='f120682696b2b7918e2817c628f2c10e177daf3a94307617688b1c39d05e3949', value_span='74:45-74:48',
            value_sha256='26f704fc9ed25bdd26a56ffd3f89360be6fe6260c7f1950ebb295fe74fcf0a39', statement_index=55, statement_kind='expr', statement_span='74:28-74:49'),
    _StoreRecord(base_id=21, base_name='sharpenBlur', index=2, value=-2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='74:50-74:71', assign_sha256='6b95fd174855fb3c98b8014cdccbf0e2f5f026d4f1aad89bff219b0e565cdfc2', target_span='74:50-74:64',
            target_sha256='73f9ab75773db5cbc0016989fcabb9397a1104529023476a9afc83b1ce65e349', index_span='74:62-74:63', index_sha256='a047fc18cd979f4fa0de9fa5fb4603cb624d29aca4fc7e8c06610fc1661f4ffd', value_span='74:67-74:71',
            value_sha256='c2df25920b69e547023b539d431c6fdebae4dad827c2380e8866f02ece72e00f', statement_index=56, statement_kind='expr', statement_span='74:50-74:72'),
    _StoreRecord(base_id=21, base_name='sharpenBlur', index=3, value=2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='75:5-75:25', assign_sha256='68d320240a2ecd7887a492fef966715b20e65ea2b07058e35c1e6ed6f25e1a79', target_span='75:5-75:19',
            target_sha256='5ad087dd8601ed500df66b56ebd0b277bbbfdef3eefa577b74e343bd74af26d8', index_span='75:17-75:18', index_sha256='6ea5f1ce9120f0bb16d247b168e8a74ffcdaa73e8b74616b2c6645500a460629', value_span='75:22-75:25',
            value_sha256='9540becde4ad184e4bc7e901fe2e2f045c6e6ecd3a4bbf7e1daccad991fd9202', statement_index=57, statement_kind='expr', statement_span='75:5-75:26'),
    _StoreRecord(base_id=21, base_name='sharpenBlur', index=4, value=1.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='75:27-75:47', assign_sha256='b1072ac0146b426d7a10ce7cd46d74a00031c3355d414efd701965bb5ebaf63a', target_span='75:27-75:41',
            target_sha256='004b54427d693b2be08e69965b734c07c503bd96eea1938b0e7f515845b3e8f2', index_span='75:39-75:40', index_sha256='b09da2b56030be5a8b2b78facdb1dcd267be5d30a66854c1b3bb777ec4d6b282', value_span='75:44-75:47',
            value_sha256='c54ddf7481d25388293519389869c72c5d79c2f888dbc42945ec56eff915cac6', statement_index=58, statement_kind='expr', statement_span='75:27-75:48'),
    _StoreRecord(base_id=21, base_name='sharpenBlur', index=5, value=2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='75:49-75:69', assign_sha256='2129942dcc22e58b8c9004fa9b2f09dfbcd57718cd7f7d856d62c967300ecf5c', target_span='75:49-75:63',
            target_sha256='8496de351ce67502da8000e0523257237d31650c76bd6f48f0f7a0d6cfd05534', index_span='75:61-75:62', index_sha256='4747e4b89ca4f0afd8b4446d8f294cad85afb93d4cf3a1f53ca5ff29b52a8886', value_span='75:66-75:69',
            value_sha256='6f77e8614c44b4313562adb1240c1a8bdfac610e741631ea7290d65050565570', statement_index=59, statement_kind='expr', statement_span='75:49-75:70'),
    _StoreRecord(base_id=21, base_name='sharpenBlur', index=6, value=-2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='76:5-76:26', assign_sha256='3a4a83735f2cd8696ab477c8ce5218effe9712c748cedebaf607d2d58b0904a2', target_span='76:5-76:19',
            target_sha256='770f6feb5f08cb2556e50af6b2656b763797d3970d6d1d1d8a028451afac1ecb', index_span='76:17-76:18', index_sha256='4ce1005b17f8a5c1327640dbe7e0425773b8a98ba6d262cb52c7d3afa030e8f5', value_span='76:22-76:26',
            value_sha256='5a48a5f5d9cb386a0f0569753a6f84fe862644e3a3a9c44a73e7ea22c693dbab', statement_index=60, statement_kind='expr', statement_span='76:5-76:27'),
    _StoreRecord(base_id=21, base_name='sharpenBlur', index=7, value=2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='76:28-76:48', assign_sha256='e72f17869adb04a4e7b683c611eb5d45979328518c9183bb415edb4d1eafddcd', target_span='76:28-76:42',
            target_sha256='734832ab865d1dec09de966173e7d131a1155252c4032acaf7d4fef2d87a7a59', index_span='76:40-76:41', index_sha256='adbcf073733b9772ac4afff83bb4281b0d28c7431611076a66c47bc43c976e5a', value_span='76:45-76:48',
            value_sha256='ae281668b4a69f7bef55fb7297133a8ae1cb6d85c10e4ae5084bcc96139a5743', statement_index=61, statement_kind='expr', statement_span='76:28-76:49'),
    _StoreRecord(base_id=21, base_name='sharpenBlur', index=8, value=-2.0, operator='=', owner_id=75,
            owner_name='loadKernels', assign_span='76:50-76:71', assign_sha256='2a56719f125f8f51ac34b6997889c1222c245dafe1cca04b2d6c5ec009137e7a', target_span='76:50-76:64',
            target_sha256='41eb982f6af44ce49b418d2dff6d1483e9582c260ef346fb12f2a37b37ad3b65', index_span='76:62-76:63', index_sha256='07b8ad32658c4e2d4aa241d4c1f0421f813b6e9f3b34bf1552435fda098ae58a', value_span='76:67-76:71',
            value_sha256='acdc69739f5de56da2ee0af48b264eef1acf6c4e3453b38294581b5bbd199a22', statement_index=62, statement_kind='expr', statement_span='76:50-76:72'),
        ),
        "store_triples": (
            (15, 0, -2.0),
            (15, 1, -1.0),
            (15, 2, 0.0),
            (15, 3, -1.0),
            (15, 4, 1.0),
            (15, 5, 1.0),
            (15, 6, 0.0),
            (15, 7, 1.0),
            (15, 8, 2.0),
            (16, 0, -1.0),
            (16, 1, 0.0),
            (16, 2, -1.0),
            (16, 3, 0.0),
            (16, 4, 5.0),
            (16, 5, 0.0),
            (16, 6, -1.0),
            (16, 7, 0.0),
            (16, 8, -1.0),
            (17, 0, 1.0),
            (17, 1, 2.0),
            (17, 2, 1.0),
            (17, 3, 2.0),
            (17, 4, 4.0),
            (17, 5, 2.0),
            (17, 6, 1.0),
            (17, 7, 2.0),
            (17, 8, 1.0),
            (18, 0, -1.0),
            (18, 1, -1.0),
            (18, 2, -1.0),
            (18, 3, -1.0),
            (18, 4, 8.0),
            (18, 5, -1.0),
            (18, 6, -1.0),
            (18, 7, -1.0),
            (18, 8, -1.0),
            (19, 0, -1.0),
            (19, 1, 0.0),
            (19, 2, -1.0),
            (19, 3, 0.0),
            (19, 4, 4.0),
            (19, 5, 0.0),
            (19, 6, -1.0),
            (19, 7, 0.0),
            (19, 8, -1.0),
            (20, 0, -0.875),
            (20, 1, -0.75),
            (20, 2, -0.875),
            (20, 3, -0.75),
            (20, 4, 5.0),
            (20, 5, -0.75),
            (20, 6, -0.875),
            (20, 7, -0.75),
            (20, 8, -0.875),
            (21, 0, -2.0),
            (21, 1, 2.0),
            (21, 2, -2.0),
            (21, 3, 2.0),
            (21, 4, 1.0),
            (21, 5, 2.0),
            (21, 6, -2.0),
            (21, 7, 2.0),
            (21, 8, -2.0),
        ),
        "references": (),
    },
}


def _admitted_symbols(lock: dict) -> dict[int, str]:
    """The `{symbol id: name}` map of one key's admitted arrays.

    Derived per call from the selected key's own record rather than bound to
    `CELLREFRACT_KEY` at import, mirroring the frame module: a future key
    added to this shared module must not run cellRefract's symbol ids against
    its tree.
    """
    return {item.symbol_id: item.name for item in lock["admitted"]}


def frame_contract(key: str) -> ArrayFrameContract:
    """The frozen emission contract both authorities must honour for ``key``."""
    lock = _LOCKS.get(key)
    if lock is None:
        raise _profile_fail(
            CELLREFRACT_PROFILE,
            f"{key} is not an admitted mutable-global array carrier")
    return lock["frame"]


def store_census(key: str) -> int:
    """The frozen element-store census of ``key``'s writer.

    Per key since the effects row (design §5's hard-wired `45`s at both
    authorities): 45 for the two five-array keys, 63 for effects' seven.
    Derived from the record's own store tuple, never a bare number.
    """
    lock = _LOCKS.get(key)
    if lock is None:
        raise _profile_fail(
            CELLREFRACT_PROFILE,
            f"{key} is not an admitted mutable-global array carrier")
    return len(lock["stores"])


def _consumed_ledger(lock: dict) -> int:
    """The visitation-ledger expectation for one key's record.

    Two objects per admitted declaration, the writer and ``main``, four
    nodes per store, and the one writer call. Anchored on
    ``_CONSUMED_LEDGER`` (the cellRefract-era census the landed sabotage
    tests freeze as load-bearing) minus that record's own arrays/stores
    plus this record's, so every figure is a record census -- and
    sabotaging the module constant still reddens every key, effects
    included.
    """
    base = _LOCKS[CELLREFRACT_KEY]
    return (_CONSUMED_LEDGER
            - 2 * len(base["admitted"]) - 4 * len(base["stores"])
            + 2 * len(lock["admitted"]) + 4 * len(lock["stores"]))


def allowed_row_fields(key: str) -> frozenset[str]:
    """The complete set of slice-row fields permitted for ``key``.

    Exhaustive by construction: the validator's allowed-field arm compares
    `set(item) != expected`, so requiring equality with this set is what
    discharges "every other profile absent". Prepared keys answer from
    ``PREPARED_ROW_FIELDS`` -- their row contract is frozen now, enforced
    when their row lands.
    """
    fields = ALLOWED_ROW_FIELDS.get(key) or PREPARED_ROW_FIELDS.get(key)
    if fields is None:
        raise _profile_fail(
            CELLREFRACT_PROFILE,
            f"{key} is not an admitted mutable-global array carrier")
    return fields


def authenticate_mutable_global_array(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedDeclaration, ...]:
    """Return the exact frozen mutable-global array declarations of
    ``program.key``.

    Returns an empty tuple when ``program.key`` is not a carrier, so callers
    can treat the result as a membership set unconditionally; supplying a
    profile for a non-carrier key is a hard failure that names the landed and
    the prepared declarations.

    Membership is the **authenticatable** set -- every frozen record,
    ``PREPARED_KEYS`` included -- not the landed registry: the record is the
    thing under test, and the slice-schema census (``KEYS``) is the
    integration gate's concern, not this function's.

    All five declarations are returned, admitted by object identity. The
    validator's rejection names only the first (``32:1 float emboss[9];``);
    admitting only that one leaves the other four to fail at the
    unconditional post-loop gate.
    """
    if program.key not in _LOCKS:
        if profile is not None:
            raise _profile_fail(
                CELLREFRACT_PROFILE,
                "program key is not an admitted mutable-global array carrier; "
                f"{CELLREFRACT_KEY} 32:1 float emboss[9], 33:1 float "
                "sharpen[9], 34:1 float blur[9], 35:1 float edge[9] and "
                "36:1 float edge2[9], "
                f"{KALEIDO_KEY} 33:1 float emboss[9], 34:1 float "
                "sharpen[9], 35:1 float blur[9], 36:1 float edge[9] and "
                "37:1 float edge2[9], and "
                f"{EFFECTS_KEY} 31:1 float emboss[9], 32:1 float "
                "sharpen[9], 33:1 float blur[9], 34:1 float edge[9], "
                "35:1 float edge2[9], 36:1 float edge3[9] and 37:1 float "
                "sharpenBlur[9], are the sole admitted declarations")
        return ()
    lock = _LOCKS[program.key]

    def fail(message: str) -> ValueError:
        return _profile_fail(lock["profile"], message)

    if profile != lock["profile"]:
        raise fail("exact profile carrier required")

    if not _caller_source_hash_holds(source_hash, lock):
        raise fail("exact caller source hash required")
    if not _defines_hold(program, lock):
        raise fail("exact preprocessor define lock mismatch")
    if not _raw_source_holds(program, lock):
        raise fail("raw source drift")
    if not _normalized_source_holds(program, lock):
        raise fail("normalized source drift")
    if not _functions_fingerprint_holds(program, lock):
        raise fail("typed function fingerprint drift")
    if not _whole_program_fingerprint_holds(program, lock):
        raise fail("whole-program fingerprint drift")
    if not _interface_fingerprint_holds(program, lock):
        raise fail("interface fingerprint drift")
    if not _unrelated_proof_absent_holds(program):
        raise fail("unrelated proof carrier is not absent")
    if not _function_cardinality_holds(program, lock):
        raise fail("function cardinality mismatch")
    if not _function_inventory_holds(program, lock):
        raise fail("function inventory mismatch")
    if not _resources_hold(program, lock):
        raise fail("resource profile mismatch")
    if not _call_graph_holds(program, lock):
        raise fail("call graph or reachability profile mismatch")

    # Locate the admitted declarations by SYMBOL IDENTITY, never by ordinal, so
    # the ordinal lock below is the only thing that can see a reordering.
    located: list[tuple[int, TypedDeclaration]] = []
    for record in lock["admitted"]:
        matches = [(index, item)
                   for index, item in enumerate(program.declarations)
                   if item.symbol.id == record.symbol_id]
        if len(matches) != 1:
            raise fail("admitted array declaration identity mismatch")
        located.append(matches[0])
    ordinals = tuple(index for index, _ in located)
    if not _ordinal_adjacency_holds(program, ordinals, lock):
        raise fail("admitted array declaration ordinal or adjacency mismatch")

    # Value-level locks run AHEAD of node identity: `Symbol` embeds its own
    # declaration span, so a storage, mutability or initializer mutation also
    # shifts the enclosing node hash, and a coarser ordering would let the hash
    # absorb the change and make each of these vacuous.
    for record, (_, declaration) in zip(lock["admitted"], located):
        if not _mutable_storage_holds(declaration, record):
            raise fail("admitted array storage or mutability mismatch")
        if not _uninitialized_holds(declaration):
            raise fail("admitted array declaration carries an initializer")
        if not _element_contract_holds(record.field, declaration):
            raise fail(f"{record.name} element numeric contract mismatch")
        if not _declaration_identity_holds(declaration, record):
            raise fail("admitted array declaration identity mismatch")

    if not _declaration_inventory_holds(program, lock):
        raise fail("global declaration inventory mismatch")
    if not _initializer_census_holds(program, lock):
        raise fail("global declaration initializer census mismatch")
    if not _frame_contract_holds(lock["frame"], lock["admitted"]):
        raise fail("frame emission contract mismatch")

    total, assigns = _node_census(program)
    if not _node_census_holds(total, assigns, lock):
        raise fail("whole-program node census mismatch")

    entries = [item for item in program.functions
               if item.id == lock["writer"][0]
               and item.name == lock["writer"][1]]
    if len(entries) != 1:
        raise fail("writer function identity mismatch")
    writer = entries[0]
    if not _writer_function_holds(writer, lock):
        raise fail("writer function shape mismatch")
    if not _writer_body_holds(writer, lock):
        raise fail("writer body shape mismatch")

    symbols = _admitted_symbols(lock)
    stores, references = _reference_census(program, symbols)
    if not _write_cardinality_holds(stores, lock):
        raise fail(f"store census cardinality mismatch: {len(stores)}")
    if not _write_owner_holds(stores, lock):
        raise fail("mutable global array single-writer proof mismatch")
    if not _store_position_holds(stores, writer, lock):
        raise fail("store position mismatch")
    if not _store_shape_holds(stores, lock):
        raise fail("store shape mismatch")
    if not _store_triples_holds(stores, lock):
        raise fail("kernel table payload mismatch")
    if not _no_indirect_write_holds(program, stores, symbols):
        raise fail("mutable global array indirect partial or compound write "
                   "present")
    if not _write_identity_holds(stores, lock):
        raise fail("store identity mismatch")
    if not _write_only_census_holds(references, lock):
        raise fail(f"write-only reference census mismatch: {len(references)}")

    mains = [item for item in program.functions
             if item.id == lock["main"][0] and item.name == lock["main"][1]]
    if len(mains) != 1:
        raise fail("main body shape mismatch")
    main = mains[0]
    if not _single_caller_holds(program, lock):
        raise fail("writer call site census mismatch")
    if not _writer_call_holds(main, lock):
        raise fail("writer call site in main mismatch")
    if not _writer_call_dominance_holds(main, lock):
        raise fail("writer call dominance mismatch")
    if not _main_body_holds(main, lock):
        raise fail("main body shape mismatch")

    admitted = tuple(declaration for _, declaration in located)
    sites = _writer_call_sites(main, lock)
    call = sites[0][2] if sites else None
    _check_ledger(
        [*admitted, *(item.symbol for item in admitted), writer, main,
         *(item.node for item in stores), *(item.target for item in stores),
         *(item.base for item in stores), *(item.value for item in stores),
         call],
        _consumed_ledger(lock), "mutable-global-array", lock["profile"])
    return admitted


def apply_mutable_global_array(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_mutable_global_array(program, source_hash, profile)
    return program
