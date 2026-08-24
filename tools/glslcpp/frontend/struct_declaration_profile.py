"""Exact identity profiles for **struct declarations** and their
function-scope plumbing.

``synth/newton:newton`` is the first carrier of the struct-declaration
bucket (``docs/port-engineering/struct-parity/struct-design.md``; every
figure below was re-measured this session against the pinned corpus
``a024dc3a960cc44af454abc7aebce50456c194e6`` with this repo's own
``parse_program``/``analyze_program`` -- measure, never transcribe). The
program's single struct is the first-blocker site the validator reports as
``125:1 unsupported struct declaration``::

    125|struct POIData {
    126|    vec4 center;
    127|    float deg;
    128|    float maxZoom;
    129|};

Sub-shape census frozen here (the design's S1/S2/S4/S6/S9/S10 column for
newton, all re-derived):

* **S1 declaration** -- exactly one struct, ``POIData`` (id 1), three fields
  ``center`` vec4 (57) / ``deg`` float (58) / ``maxZoom`` float (59).
* **S2 constructors** -- exactly 7 ``construct`` nodes whose
  ``constructor_type.kind == "struct"``, all in ``getPOI`` statements 0-6
  (``135:26``-``141:12``), every one with children
  ``(vec4, float, float)``. The first six build their ``vec4`` from 4
  literal lanes; the default ``return POIData(vec4(0.0), 3.0, 7.0)`` uses
  the single-lane splat form (lane counts ``(4,1,1)`` x6 then ``(1,1,1)``).
* **S4 struct-typed return** -- ``getPOI`` (id 71, ``131:1-142:2``) returns
  ``POIData`` and takes one ``in int idx`` (60).
* **S6 struct local from a call** -- ``POIData p = getPOI(poiIdx)``,
  symbol 101, declaration node ``175:17-175:35`` inside ``main``.
* **S9 member + swizzle chains** -- ``p.center.xy`` (``176:15-176:26``) and
  ``p.center.zw`` (``177:15-177:26``), both ``swizzle`` over ``member
  center`` over the ``id`` ``p``, both producing ``vec2``.
* **S10 scalar-member reads** -- ``p.deg`` (``178:21-178:26``, consumed by
  an assign) and ``p.maxZoom`` (``179:39-179:48``, consumed by the ``min``
  builtin).

And the named-empty absent-sets: **zero** whole-vec member reads (S8), and
**zero** struct-typed parameters anywhere in the program (S5) -- the
palette family's shapes are a different record lane and must not ride on
this one.

Measured divergences from the design, recorded rather than absorbed:

* The design (§3.5/M6) counts the ``log``/``log2`` sites as "2 sites"
  (``290:29`` log2, ``290:34`` log). The measured census is **three**
  ``builtin`` nodes: ``log2`` at ``290:29-290:69`` and ``log`` at
  ``290:34-290:51`` **and** ``290:54-290:68`` (the ``log(tolerance)``
  denominator of ``log2(log(convergeDist) / log(tolerance))``). The design
  under-counted by the second ``log``. Those nodes are the integration
  lane's M6 carriers, not this module's census; the finding is recorded
  here so the M6 slice budgets three identities, not two.
* Everything else in the design's §2.1/§3.1 newton column re-measured
  **identical**: raw/normalized bytes+SHA, 26 declarations, 13 functions
  (ids 61-73), 804 nodes / 34 assigns, all-13 reachability, counted-loop
  proof ``(4, 0, 2, 4000, 8008)``, resources, and every span above.

JavaScript authority (quote-verified this session against the frozen
snapshot's ``canonicalFactory264``, registered at
``canonical-kernels.js:36444``): the struct materializes as a **plain
object literal with typed members** -- ``center: new
$runtime.PooledFloat32Array([0.25, 0.4330126941204071, 0,
7.771800092370995e-9]), deg: 3, maxZoom: 14`` -- the vec4 member is a
pooled **f32-lane array** (note the GLSL ``7.7718e-9`` spelling becoming
``7.771800092370995e-9``, the double spelling of the narrowed f32), while
the scalar members are plain Numbers (int-valued doubles). The two
``p.center.xy``/``.zw`` swizzles were rewritten by the generator into
``vec2.add([], new $runtime.PooledFloat32Array([p.center[0],
p.center[1]]), ...)`` constructors -- numerically identical lane
reorders; the port may keep the corpus swizzle form (an authority note,
not an obligation). The frozen materialization contract below carries
these decisions so the emitter lane inherits them as data, and the test
suite asserts the frozen strings without re-reading the snapshot (the
oracle lane owns standing snapshot verification).

**Landed/prepared split.** This module follows
``mutable_global_array_profile.py``: ``KEYS`` is the LANDED carrier
registry (empty -- newton's row lands in the integration slice; a key here
before its row exists would redden the live slice-schema census), and
``PREPARED_KEYS`` carries the record frozen and authenticatable now. The
row contract is frozen in ``PREPARED_ROW_FIELDS``: newton's row carries
this module's field plus the ``out_inout_admission_profile`` companion
(newton's out parameters are inseparable from its struct plumbing -- the
design's M3), enforced mutually through ``REQUIRED_COMPANION_PROFILES``.

**No vocabulary growth.** Nothing here touches ``APPROVED_CAPABILITIES``
or ``APPROVED_TYPES``; admission is by object identity into this module's
frozen records only.

Sibling-proof absent-set: every ``fixed_*_proof`` field a ``TypedProgram``
can carry is frozen **absent** for newton (the design §3.5 measured all
auto-attach proofs as None on this program). The tuple below is
hand-frozen and the test re-derives it from the dataclass, so a new proof
field added elsewhere in the tree turns this module red rather than
silently passing.
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from .typed_ir import (TypedExpression, TypedProgram, TypedStatement,
                       TypedFunction)


NEWTON_KEY = "synth/newton:newton"
NEWTON_PROFILE = "struct-declaration-newton-v1"
NEWTON_SOURCE_PATH = "synth/newton/newton.glsl"
JULIA_KEY = "synth/julia:julia"
JULIA_PROFILE = "struct-declaration-julia-v1"
JULIA_SOURCE_PATH = "synth/julia/julia.glsl"

# The LANDED carrier registry -- empty until newton's row lands (the
# integration slice moves the key here together with its row, the one-line
# move the landed/prepared split exists to make safe).
KEYS: tuple[str, ...] = (JULIA_KEY, NEWTON_KEY)
PROFILES: dict[str, str] = {
    JULIA_KEY: JULIA_PROFILE, NEWTON_KEY: NEWTON_PROFILE}
STRUCT_DECLARATION_KEYS = frozenset(PROFILES)

# Records frozen and authenticatable NOW whose row lands in a later slice.
PREPARED_KEYS: tuple[str, ...] = ()

# The complete allowed field set for the future slice row -- an ALLOWLIST,
# not a denylist. Prepared keys answer from PREPARED_ROW_FIELDS; the frozen
# row carries both struct carriers (the design's M3 hazard: newton's out
# parameters must never be admitted without their direction contract, and
# the struct plumbing must never land without the out arms that keep the
# emitter from silently passing by value).
ALLOWED_ROW_FIELDS: dict[str, frozenset[str]] = {
    JULIA_KEY: frozenset({
        "defines", "program_key", "julia_frontend_profile",
        "struct_declaration_profile", "out_inout_admission_profile",
    }),
    NEWTON_KEY: frozenset({
        "defines",
        "program_key",
        "struct_declaration_profile",
        "out_inout_admission_profile",
    }),
}
PREPARED_ROW_FIELDS: dict[str, frozenset[str]] = {}

# The companion carrier this row cannot land without, read by BOTH
# authorities' collision lists (the kaleido/scalar-uint-xor pattern).
REQUIRED_COMPANION_PROFILES = {
    JULIA_KEY: (
        ("julia_frontend_profile", "julia-frontend-admission-v1"),
        ("out_inout_admission_profile", "out-inout-admission-julia-v1"),
    ),
    NEWTON_KEY: (("out_inout_admission_profile",
                  "out-inout-admission-newton-v1"),),
}

# Every `fixed_*_proof` field a TypedProgram carries. ALL are absent for
# newton (measured; the design's §3.5 auto-attach census found None for
# every proof on this program). The test suite re-derives this set from
# the dataclass, so the absent-set is exhaustive by construction.
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

# The struct, its three fields, the seven constructors, the four member
# nodes, the two swizzle nodes, the four member-base `id` nodes, the
# struct-local declaration node, its initializer call, the local's Symbol,
# `getPOI` and `main`: 26 distinct objects, each consumed exactly once.
_CONSUMED_LEDGER = 26

__all__ = (
    "KEYS", "PROFILES", "STRUCT_DECLARATION_KEYS", "PREPARED_KEYS",
    "NEWTON_KEY", "NEWTON_PROFILE", "NEWTON_SOURCE_PATH",
    "JULIA_KEY", "JULIA_PROFILE", "JULIA_SOURCE_PATH",
    "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS",
    "REQUIRED_COMPANION_PROFILES", "allowed_row_fields",
    "StructFieldRecord", "StructDeclarationRecord", "ConstructorRecord",
    "StructReturnFunctionRecord", "StructLocalRecord", "MemberSiteRecord",
    "StructMaterialization", "materialization_contract",
    "JuliaResultMaterialization", "JuliaStructAdmissionRecord",
    "authenticate_struct_declaration", "apply_struct_declaration",
)


class StructFieldRecord(NamedTuple):
    """One struct field's identity: symbol id, name, GLSL type, span."""

    symbol_id: int
    name: str
    glsl_type: str
    span: str
    sha256: str


class StructDeclarationRecord(NamedTuple):
    """The struct declaration itself, plus its ordered field records."""

    id: int
    name: str
    display: str
    kind: str
    span: str
    sha256: str
    fields: tuple[StructFieldRecord, ...]


class ConstructorRecord(NamedTuple):
    """One struct-constructor node: position, arity, and payload.

    ``values`` is the measured literal payload (nested tuples); the
    default-return splat form carries a one-lane vec4.
    """

    span: str
    sha256: str
    statement_index: int
    child_types: tuple[str, ...]
    lane_counts: tuple[int, ...]
    values: tuple


class StructReturnFunctionRecord(NamedTuple):
    """The struct-returning function: signature (directions included) and
    the (kind, span) shape of its body."""

    id: int
    name: str
    return_type: str
    parameters: tuple[tuple[int, str, str, str], ...]
    span: str
    sha256: str
    body: tuple[tuple[str, str], ...]


class StructLocalRecord(NamedTuple):
    """The struct-typed local (S6): its declaration node, statement,
    enclosing host statement, initializer call, and Symbol."""

    symbol_id: int
    name: str
    glsl_type: str
    declaration_span: str
    declaration_sha256: str
    statement_kind: str
    statement_span: str
    statement_sha256: str
    chain_depth: int
    host_kind: str
    host_span: str
    initializer_kind: str
    initializer_callee: str
    initializer_signature_id: int
    initializer_span: str
    initializer_sha256: str
    symbol_span: str
    symbol_sha256: str


class MemberSiteRecord(NamedTuple):
    """One `member` node: the field read, its base, and (for S9) the
    swizzle chain above it; `consumer` names the parent kind for S10."""

    field: str
    base_symbol_id: int
    base_type: str
    member_type: str
    role: str
    span: str
    sha256: str
    swizzle: str | None
    swizzle_span: str | None
    swizzle_sha256: str | None
    swizzle_type: str | None
    consumer: str


class StructMaterialization(NamedTuple):
    """The frozen JS-side materialization contract (authority notes,
    quote-verified against ``canonicalFactory264`` this session).

    The emitter lane consumes this record as data; the numeric decisions
    (f32-lane vec4 member, double scalar members) are the design's §3.3
    and are what the oracle differential will hold the port to.
    """

    center_member: str
    scalar_members: str
    center_native: str
    scalar_native: str
    center_witness_glsl: float
    center_witness_f32_spelling: float
    scalar_witnesses: tuple[float, ...]
    swizzle_authority_note: str
    factory_registration: str


class JuliaResultMaterialization(NamedTuple):
    """JuliaResult's adapter-specific native storage contract.

    The source declaration uses seven GLSL ``float`` members, but the CPU
    authority has mixed Number/f32 state. The eventual emitter must use a
    custom double-backed carrier and narrow only the listed f32 stores.
    """

    native_kind: str
    f32_narrowed_fields: tuple[str, ...]
    normal_f32_narrowed_fields: tuple[str, ...]
    number_double_fields: tuple[str, ...]
    normal_iteration_store: str
    convergence_iteration: str
    trap_min: str
    constructor_abi: str


class JuliaStructAdmissionRecord(NamedTuple):
    """Authenticated JuliaResult declaration/constructor/member census."""

    struct_name: str
    fields: tuple[str, ...]
    field_types: tuple[str, ...]
    field_ids: tuple[int, ...]
    constructor_count: int
    constructor_spans: tuple[str, ...]
    member_count: int
    member_sites: tuple[tuple[str, str, int], ...]
    consumed_objects: tuple[object, ...]



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
    """Prefix every failure with the **per-key** profile name (Amendment 2:
    in a shared module a failure on one key must name another key's
    profile). The profile is always an argument, never a default."""
    return ValueError(f"{profile}: {message}")


def _check_ledger(entries: list, expected: int, label: str,
                  profile: str = NEWTON_PROFILE) -> None:
    """Require ``entries`` to hold exactly ``expected`` distinct objects."""
    identities = [id(item) for item in entries]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _profile_fail(profile, f"{label} visitation ledger mismatch")


# --- walkers ----------------------------------------------------------------
#
# Census discipline: every walker descends `program.declarations` as well as
# `program.functions` -- global declaration initializers are the classic
# whole-program-census blind spot (the design §8 names struct table
# initializers as exactly such a blind spot for the palette family; here the
# three const-float initializers are walked and the member census over them
# is frozen empty, which is what proves no member site hides there).

def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, item_path in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, item_path, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _program_nodes(program: TypedProgram):
    """Every expression node in the program, global initializers included."""
    for declaration in program.declarations:
        if declaration.initializer is None:
            continue
        for item, parent, path in _walk_expression(declaration.initializer):
            yield None, item, parent, path, ()
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement,
                                                             (index,)):
                yield function, item, parent, path, chain


def _node_census(program: TypedProgram) -> tuple[int, int]:
    total = 0
    assigns = 0
    for _, item, _, _, _ in _program_nodes(program):
        total += 1
        if item.kind == "assign":
            assigns += 1
    return total, assigns


def _declaration_inventory(program: TypedProgram) -> tuple:
    return tuple(sorted(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable,
         item.initializer is not None, _span(item))
        for item in program.declarations))


def _function_inventory(program: TypedProgram) -> tuple:
    return tuple(
        (item.id, item.name, item.return_type.display(),
         tuple((parameter.id, parameter.name, parameter.type.display(),
                parameter.direction)
               for parameter in item.parameters), _span(item))
        for item in program.functions)


def _call_graph(program: TypedProgram) -> tuple:
    edges = set()
    for function, item, _, path, _ in _program_nodes(program):
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


def _constructor_values(node: TypedExpression):
    """The literal payload of a constructor node: literals (or the unary
    minus of one) reduced to numbers, constructs to nested tuples."""
    if node.kind == "literal":
        return node.literal_value
    if node.kind == "unary" and len(node.children) == 1:
        return -_constructor_values(node.children[0])
    if node.children:
        return tuple(_constructor_values(child) for child in node.children)
    return None


def _struct_constructor_census(program: TypedProgram):
    """Every `construct` node whose constructor_type is the frozen struct,
    with its owning function, top-level statement index, and payload."""
    for function, item, parent, path, chain in _program_nodes(program):
        if (item.kind != "construct" or item.constructor_type is None
                or item.constructor_type.kind != "struct"):
            continue
        yield function, item, path[0], chain


def _member_site_census(program: TypedProgram):
    """Every `member` node with its parent (the swizzle consumer for S9,
    the direct consumer for S10) and its base `id` node, classified by
    role. ``parent`` is the swizzle node for swizzled sites and the direct
    consumer (assign / builtin) for scalar reads."""
    for function, item, parent, path, chain in _program_nodes(program):
        if item.kind != "member" or not item.children:
            continue
        base = item.children[0]
        if parent is not None and parent.kind == "swizzle":
            yield item, parent, base, "swizzled"
        else:
            yield item, parent, base, "scalar-read"


def _lane_counts(node: TypedExpression) -> tuple[int, ...]:
    return tuple((len(child.children) if child.kind == "construct" else 1)
                 for child in node.children)


# --- individually deletable locks -------------------------------------------
#
# Each predicate below is exactly one lock with exactly one message. The
# delete-the-check sweep (scratch copy) neutralizes one at a time and every
# removal must redden a named test. Keep them small, single-purpose and
# side-effect free.
#
# Ordering: value checks run AHEAD of node identity. `Symbol` and every
# TypedExpression embed their spans, so a value-level mutation also shifts
# the enclosing hashes -- a coarser ordering would let the identity locks
# absorb value drift and make the value locks vacuous.

def _caller_source_hash_holds(source_hash: str | None, lock: dict) -> bool:
    """The caller's own view of the source agrees with the frozen record."""
    return source_hash == lock["raw_sha256"]


def _defines_hold(program: TypedProgram, lock: dict) -> bool:
    """newton has no preprocessor defines: the canonical empty tuple."""
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
    """Every auto-attachable proof field is absent on newton (measured;
    the design §3.5 census: none of them attaches to this program)."""
    return all(getattr(program, field, None) is None
               for field in _OPTIONAL_PROOF_FIELDS)


def _function_cardinality_holds(program: TypedProgram, lock: dict) -> bool:
    return len(program.functions) == lock["function_count"]


def _function_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    """All thirteen functions by id, name, return type, parameters WITH
    DIRECTIONS, and span. The directions are frozen here so this module
    agrees with the out/inout module's independent inventory."""
    return _function_inventory(program) == lock["function_inventory"]


def _resources_hold(program: TypedProgram, lock: dict) -> bool:
    """22 uniforms (3 vec2 + 19 float), no samplers, one output, no
    texture, no derivatives. `resolution` is declared and never read; it
    stays a required ABI binding (the invariance witness of §7)."""
    resources = program.resources
    return ((resources.uniforms, resources.samplers, resources.outputs,
             resources.uses_texture, resources.uses_derivatives)
            == lock["resources"])


def _call_graph_holds(program: TypedProgram, lock: dict) -> bool:
    """22 edges, full reachability (all 13 functions), the counted-loop
    proof (4/0/2/4000/8008 -- loops are the expected drop-path, M10)."""
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


def _declaration_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    """All 26 declarations, order-insensitive: an added or removed global
    anywhere is a hard failure here."""
    return (len(program.declarations) == lock["declaration_count"]
            and _declaration_inventory(program)
            == lock["declaration_inventory"])


def _node_census_holds(total: int, assigns: int, lock: dict) -> bool:
    return total == lock["total_nodes"] and assigns == lock["total_assigns"]


def _struct_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    """Exactly one struct, its name is a local type name, and there is no
    second struct hiding anywhere in the tree."""
    record = lock["struct"]
    return (len(program.structs) == 1
            and program.structs[0].id == record.id
            and program.structs[0].name == record.name
            and record.name in program.local_type_names)


def _struct_declaration_identity_holds(program: TypedProgram,
                                       lock: dict) -> bool:
    """The struct's id, name, display, kind, span, and node hash."""
    record = lock["struct"]
    declaration = program.structs[0]
    return ((declaration.id, declaration.name,
             declaration.type.display(), declaration.type.kind,
             _span(declaration), _sha(declaration))
            == (record.id, record.name, record.display, record.kind,
                record.span, record.sha256))


def _struct_fields_hold(program: TypedProgram, lock: dict) -> bool:
    """The three fields by id, name, type, and span (value-level; runs
    ahead of the field node hashes, which absorb span drift)."""
    declaration = program.structs[0]
    measured = tuple((field.id, field.name, field.type.display(),
                      _span(field))
                     for field in declaration.fields)
    expected = tuple((record.symbol_id, record.name, record.glsl_type,
                      record.span)
                     for record in lock["struct"].fields)
    return measured == expected


def _struct_field_identity_holds(program: TypedProgram, lock: dict) -> bool:
    """The three field node hashes (the identity tier of the field lock)."""
    declaration = program.structs[0]
    return (tuple(_sha(field) for field in declaration.fields)
            == tuple(record.sha256 for record in lock["struct"].fields))


def _getpoi_signature_holds(function: TypedFunction, lock: dict) -> bool:
    """The struct-typed return (S4): `POIData getPOI(int idx)` -- id 71,
    return display POIData, one `in int` parameter, span 131:1-142:2."""
    record = lock["getpoi"]
    parameters = tuple((parameter.id, parameter.name,
                        parameter.type.display(), parameter.direction)
                       for parameter in function.parameters)
    return (function.id == record.id and function.name == record.name
            and function.return_type.display() == record.return_type
            and parameters == record.parameters
            and _span(function) == record.span)


def _getpoi_body_holds(function: TypedFunction, lock: dict) -> bool:
    """Six `if` returns plus the default `return`: the (kind, span) shape."""
    record = lock["getpoi"]
    return (tuple((statement.kind, _span(statement))
                  for statement in function.body) == record.body)


def _constructor_census_holds(census: list, lock: dict) -> bool:
    """Exactly 7 struct constructors, all owned by `getPOI`, at statements
    0-6, each with children (vec4, float, float) and the frozen lane
    counts (the default return's vec4 splat has ONE lane). Value-level:
    runs ahead of the constructor node hashes."""
    records = lock["constructors"]
    if len(census) != len(records):
        return False
    for (function, node, statement_index, _), record in zip(census, records):
        if (function is None or function.id != lock["getpoi"].id
                or statement_index != record.statement_index
                or len(node.children) != len(record.child_types)
                or tuple(child.type.display() for child in node.children)
                != record.child_types
                or _lane_counts(node) != record.lane_counts):
            return False
    return True


def _constructor_values_hold(census: list, lock: dict) -> bool:
    """The seven literal payloads, value for value (the POI table)."""
    return (tuple(_constructor_values(node) for _, node, _, _ in census)
            == tuple(record.values for record in lock["constructors"]))


def _constructor_identity_holds(census: list, lock: dict) -> bool:
    """The seven constructor spans and node hashes (the identity tier)."""
    return (tuple((_span(node), _sha(node)) for _, node, _, _ in census)
            == tuple((record.span, record.sha256)
                     for record in lock["constructors"]))


def _struct_local_shape_holds(site: tuple | None, lock: dict) -> bool:
    """The struct local (S6): a `POIData` local whose initializer is a call
    to `getPOI` (signature 71). Value-level: type name and initializer
    callee run ahead of the node hashes."""
    if site is None:
        return False
    node, statement, chain, function = site
    record = lock["struct_local"]
    if (node.symbol is None or function is None
            or function.id != lock["main"][0]
            or node.symbol.id != record.symbol_id
            or node.symbol.name != record.name
            or node.symbol.type.display() != record.glsl_type
            or node.symbol.storage != "local"
            or not node.children):
        return False
    initializer = node.children[0]
    return (initializer.kind == record.initializer_kind
            and initializer.callee == record.initializer_callee
            and initializer.signature_id == record.initializer_signature_id)


def _struct_local_identity_holds(site: tuple | None, lock: dict) -> bool:
    """The struct local's spans and hashes (the identity tier): declaration
    node, statement (nested two levels under the `if` host), initializer
    call, and Symbol."""
    if site is None:
        return False
    node, statement, chain, function = site
    record = lock["struct_local"]
    initializer = node.children[0]
    host = chain[-2] if len(chain) > 1 else None
    return ((len(chain), statement.kind, _span(statement), _sha(statement),
             "" if host is None else host.kind,
             "" if host is None else _span(host),
             _span(node), _sha(node), _span(initializer), _sha(initializer),
             _span(node.symbol), _sha(node.symbol))
            == (record.chain_depth, record.statement_kind,
                record.statement_span, record.statement_sha256,
                record.host_kind, record.host_span,
                record.declaration_span, record.declaration_sha256,
                record.initializer_span, record.initializer_sha256,
                record.symbol_span, record.symbol_sha256))


def _member_census_holds(census: list, lock: dict) -> bool:
    """Exactly 4 member nodes program-wide (global initializers included):
    2 swizzled + 2 scalar reads, every base the `p` local of type POIData,
    every site consumed by the frozen parent kind, and ZERO whole-vec
    member reads (S8 absent). Value-level."""
    records = lock["members"]
    if len(census) != len(records):
        return False
    for (node, parent, base, role), record in zip(census, records):
        if (role != record.role
                or node.member != record.field
                or base.kind != "id"
                or base.symbol_id != record.base_symbol_id
                or base.type.display() != record.base_type
                or node.type.display() != record.member_type
                or parent is None
                or parent.kind != record.consumer):
            return False
    roles = tuple(record.role for record in records)
    if roles.count("swizzled") != 2 or roles.count("scalar-read") != 2:
        return False
    # S8 absent-set: no vec-typed member consumed without a swizzle.
    return all(record.member_type == "float"
               for record in records if record.role == "scalar-read")


def _member_swizzle_holds(census: list, lock: dict) -> bool:
    """The two swizzle chains: `xy` and `zw` over `center`, both producing
    vec2 (S9). The letters live in the swizzle node's `member` field."""
    for (node, parent, base, role), record in zip(census, lock["members"]):
        if record.role != "swizzled":
            continue
        if (parent is None or parent.kind != "swizzle"
                or parent.member != record.swizzle
                or parent.type.display() != record.swizzle_type
                or parent.children[0] is not node):
            return False
    return True


def _member_identity_holds(census: list, lock: dict) -> bool:
    """The member (and swizzle) spans and node hashes (the identity tier)."""
    for (node, parent, base, role), record in zip(census, lock["members"]):
        if (_span(node), _sha(node)) != (record.span, record.sha256):
            return False
        if record.role == "swizzled":
            if (_span(parent), _sha(parent)) != (record.swizzle_span,
                                                 record.swizzle_sha256):
                return False
    return True


def _no_struct_parameters_holds(program: TypedProgram) -> bool:
    """S5 absent-set: no parameter of struct type anywhere. historicPalette
    is the struct-parameter program; newton is not, and must not grow one."""
    return not any(parameter.type.kind == "struct"
                   for function in program.functions
                   for parameter in function.parameters)


def _materialization_contract_holds(contract: StructMaterialization,
                                    lock: dict) -> bool:
    """The frozen JS materialization contract, validated against the
    predicate's own constants (never ``contract == lock[...]`` -- that
    would compare the record with itself and hold vacuously under record
    tampering): pooled-f32-array vec4 member, plain-double scalar members,
    the f32-spelling witness, and the swizzle authority note."""
    return (contract.center_member == "pooled-f32-array"
            and contract.scalar_members == "number-double"
            and contract.center_native == "glsl::Vec4"
            and contract.scalar_native == "double"
            and contract.center_witness_glsl == 7.7718e-09
            and contract.center_witness_f32_spelling == 7.771800092370995e-09
            and contract.scalar_witnesses == (3.0, 14.0)
            and "vec2 constructors" in contract.swizzle_authority_note
            and contract.factory_registration
            == '"synth/newton:newton": canonicalFactory264')


# --- frozen per-key records (all measured this session) ----------------------

_STRUCT_FIELDS = (
    StructFieldRecord(57, "center", "vec4", "126:5-126:16",
                      "1613b941fbb51802fee43f697d0191907b3673ede400671eb4827394c31f2a66"),
    StructFieldRecord(58, "deg", "float", "127:5-127:14",
                      "15377f7f892138e1a4e7179f380baad45a5f22d527deedee8a6f7b6db8272796"),
    StructFieldRecord(59, "maxZoom", "float", "128:5-128:18",
                      "692dec66dff69d1c568635959ee2008f33d402ace09988e656e00b4d11d56692"),
)

_CONSTRUCTORS = (
    ConstructorRecord(
        "135:26-135:69",
        "7c8ea921f1ac02dbe74355da06a5ee6d40eb3c9beb18a4abcf93bab35b9ec71a",
        0, ("vec4", "float", "float"), (4, 1, 1),
        ((0.0, 0.0, 0.0, 0.0), 3.0, 7.0)),
    ConstructorRecord(
        "136:26-136:92",
        "b9316ad04e53a885c2501818c3fed58f39250b05eb9e5d68270af4a70fee5316",
        1, ("vec4", "float", "float"), (4, 1, 1),
        ((0.25, 0.4330126941204071, 0.0, 7.7718e-09), 3.0, 14.0)),
    ConstructorRecord(
        "137:26-137:69",
        "3cf013d6d1a1baad3b5f5da6b96a52cc5e0a7e60815218d0882f779ee98ed197",
        2, ("vec4", "float", "float"), (4, 1, 1),
        ((0.0, 0.0, 0.0, 0.0), 5.0, 7.0)),
    ConstructorRecord(
        "138:26-138:113",
        "d9cd14afcf23020a4508c8935de5f3cda25e4b8990f4653cc1a72860c7028994",
        3, ("vec4", "float", "float"), (4, 1, 1),
        ((0.6545084714889526, 0.4755282700061798, 2.5699e-08, -1.1859e-08),
         5.0, 14.0)),
    ConstructorRecord(
        "139:26-139:69",
        "810006f3ceb2dde192f36e5a8f031c5611143b5da6a39582e42b4120a863308f",
        4, ("vec4", "float", "float"), (4, 1, 1),
        ((0.0, 0.0, 0.0, 0.0), 6.0, 7.0)),
    ConstructorRecord(
        "140:26-140:69",
        "cc10dca8dfee54e25a30d2a4faabaf9040ce394643cc6dd8a57f1aa848f012be",
        5, ("vec4", "float", "float"), (4, 1, 1),
        ((0.0, 0.0, 0.0, 0.0), 8.0, 7.0)),
    ConstructorRecord(
        "141:12-141:40",
        "f88828533aba894bca50da580f91fc4f06f11124a315d66c06b1acf9b4ba97da",
        6, ("vec4", "float", "float"), (1, 1, 1),
        ((0.0,), 3.0, 7.0)),
)

_MEMBERS = (
    MemberSiteRecord(
        "center", 101, "POIData", "vec4", "swizzled",
        "176:15-176:23", "a9b16d3959cd35562800cd1fe4c5aa1595a19f2f6aacb6993ad3d8763c21c64b",
        "xy", "176:15-176:26",
        "94711a009ac5a2dedefa3bdb85b78cb47bf04b65924f40f2994913cce4bb5c6a",
        "vec2", "swizzle"),
    MemberSiteRecord(
        "center", 101, "POIData", "vec4", "swizzled",
        "177:15-177:23", "2267e0e27006c623c1993d3511ad6ef529c4b9031f3bf430243da6ecdcd1133f",
        "zw", "177:15-177:26",
        "3ca3221677043241c886526fac90a92f035e4f6ad0876d3f61bd470c82fb236c",
        "vec2", "swizzle"),
    MemberSiteRecord(
        "deg", 101, "POIData", "float", "scalar-read",
        "178:21-178:26", "01b82f1276a05c2783bc3aa93737a99faddd9fbae324a4d039d4aee0b86978df",
        None, None, None, None, "assign"),
    MemberSiteRecord(
        "maxZoom", 101, "POIData", "float", "scalar-read",
        "179:39-179:48", "7b194d58c3b76185b8ca4ef05115c3ece8f404b23657d7e166b101104780926d",
        None, None, None, None, "builtin"),
)

# The `consumer` field names the parent kind at every site: the swizzle
# for the S9 chains, the assign and the `min` builtin for the S10 reads.
_MATERIALIZATION = StructMaterialization(
    center_member="pooled-f32-array",
    scalar_members="number-double",
    center_native="glsl::Vec4",
    scalar_native="double",
    center_witness_glsl=7.7718e-09,
    center_witness_f32_spelling=7.771800092370995e-09,
    scalar_witnesses=(3.0, 14.0),
    swizzle_authority_note=(
        "generator rewrote p.center.xy/.zw into vec2 constructors over "
        "[p.center[0], p.center[1]] / [p.center[2], p.center[3]] "
        "(compile-glsl.js:423-428); numerically identical lane reorder; "
        "the port keeps the corpus swizzle form"),
    factory_registration='"synth/newton:newton": canonicalFactory264',
)

_LOCKS = {
    NEWTON_KEY: {
        "profile": NEWTON_PROFILE,
        "source_path": NEWTON_SOURCE_PATH,
        "raw_bytes": 10325,
        "raw_sha256": ("603090e299ccb08fd4db4bf54a2aa6668ed81be9"
                       "71a84a8b679c7f560e5c27ac"),
        "normalized_bytes": 7747,
        "normalized_sha256": ("c021c2f8c0e8df9b0fe92b97d24d532a5d3ccf"
                              "e44c0e8a75bba4a11cabcc5af8"),
        "functions_sha256": ("c81810c4b619c47bfbcb12cee741a8996f2827"
                             "1dee6ff7185af445ac921770e0"),
        "whole_sha256": ("c5bbd5f6e8d86e104ec2f19276c238d7455ca92c1"
                         "2447a83665ae1c3aec91932"),
        "interface_sha256": ("8b3eca5d9b6ab9805718d5de7073457480b765"
                             "ca82c3acb09923fcead024f935"),
        "defines": (),
        "declaration_count": 26,
        "declaration_inventory": (
            (2, "resolution", "vec2", "uniform", False, False, "4:1-4:25"),
            (3, "tileOffset", "vec2", "uniform", False, False, "5:1-5:25"),
            (4, "fullResolution", "vec2", "uniform", False, False, "6:1-6:29"),
            (5, "time", "float", "uniform", False, False, "7:1-7:20"),
            (6, "degree", "float", "uniform", False, False, "8:1-8:22"),
            (7, "relaxation", "float", "uniform", False, False, "9:1-9:26"),
            (8, "iterations", "float", "uniform", False, False, "10:1-10:26"),
            (9, "tolerance", "float", "uniform", False, False, "11:1-11:25"),
            (10, "poi", "float", "uniform", False, False, "12:1-12:19"),
            (11, "centerHiX", "float", "uniform", False, False, "13:1-13:25"),
            (12, "centerHiY", "float", "uniform", False, False, "14:1-14:25"),
            (13, "centerLoX", "float", "uniform", False, False, "15:1-15:25"),
            (14, "centerLoY", "float", "uniform", False, False, "16:1-16:25"),
            (15, "zoomSpeed", "float", "uniform", False, False, "17:1-17:25"),
            (16, "zoomDepth", "float", "uniform", False, False, "18:1-18:25"),
            (17, "degreeSpeed", "float", "uniform", False, False, "19:1-19:27"),
            (18, "degreeRange", "float", "uniform", False, False, "20:1-20:27"),
            (19, "relaxSpeed", "float", "uniform", False, False, "21:1-21:26"),
            (20, "relaxRange", "float", "uniform", False, False, "22:1-22:26"),
            (21, "rotation", "float", "uniform", False, False, "23:1-23:24"),
            (22, "outputMode", "float", "uniform", False, False, "24:1-24:26"),
            (23, "invert", "float", "uniform", False, False, "25:1-25:22"),
            (24, "fragColor", "vec4", "output", True, False, "27:1-27:16"),
            (25, "PI", "float", "const", False, True, "29:1-29:32"),
            (26, "TAU", "float", "const", False, True, "30:1-30:33"),
            (27, "PHI", "float", "const", False, True, "31:1-31:32"),
        ),
        "function_count": 13,
        "function_inventory": (
            (61, "df64_add", "vec2",
             ((34, "a", "vec2", "in"), (35, "b", "vec2", "in")),
             "64:1-68:2"),
            (62, "df64_cmul", "void",
             ((44, "ar", "vec2", "in"), (45, "ai", "vec2", "in"),
              (46, "br", "vec2", "in"), (47, "bi", "vec2", "in"),
              (48, "rr", "vec2", "out"), (49, "ri", "vec2", "out")),
             "98:1-101:2"),
            (63, "df64_from", "vec2", ((42, "a", "float", "in"),),
             "86:1-88:2"),
            (64, "df64_mul", "vec2",
             ((38, "a", "vec2", "in"), (39, "b", "vec2", "in")),
             "74:1-78:2"),
            (65, "df64_mul_f", "vec2",
             ((40, "a", "vec2", "in"), (41, "b", "float", "in")),
             "80:1-84:2"),
            (66, "df64_quick_two_sum", "vec2",
             ((28, "a", "float", "in"), (29, "b", "float", "in")),
             "39:1-43:2"),
            (67, "df64_sub", "vec2",
             ((36, "a", "vec2", "in"), (37, "b", "vec2", "in")),
             "70:1-72:2"),
            (68, "df64_to_float", "float", ((43, "a", "vec2", "in"),),
             "90:1-92:2"),
            (69, "df64_two_prod", "vec2",
             ((32, "a", "float", "in"), (33, "b", "float", "in")),
             "52:1-62:2"),
            (70, "df64_two_sum", "vec2",
             ((30, "a", "float", "in"), (31, "b", "float", "in")),
             "45:1-50:2"),
            (71, "getPOI", "POIData", ((60, "idx", "int", "in"),),
             "131:1-142:2"),
            (72, "main", "void", (), "148:1-314:2"),
            (73, "transformCoords_df64", "void",
             ((50, "fragCoord", "vec2", "in"), (51, "cX_df", "vec2", "in"),
              (52, "cY_df", "vec2", "in"), (53, "z_zoom", "float", "in"),
              (54, "rot", "float", "in"), (55, "re_df", "vec2", "out"),
              (56, "im_df", "vec2", "out")),
             "107:1-119:2"),
        ),
        "resources": (
            ("resolution", "tileOffset", "fullResolution", "time", "degree",
             "relaxation", "iterations", "tolerance", "poi", "centerHiX",
             "centerHiY", "centerLoX", "centerLoY", "zoomSpeed", "zoomDepth",
             "degreeSpeed", "degreeRange", "relaxSpeed", "relaxRange",
             "rotation", "outputMode", "invert"),
            (), ("fragColor",), False, False),
        "call_edge_count": 22,
        "call_graph_sha256": ("86f43677708455b85aae302ce62d5e7b1b4b61378"
                              "8e7d06a354fe2ee80594381"),
        "reachable": (61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73),
        "unreachable": (),
        "counted_loop_proof": (4, 0, 2, 4000, 8008, True),
        "total_nodes": 804,
        "total_assigns": 34,
        "struct": StructDeclarationRecord(
            1, "POIData", "POIData", "struct", "125:1-129:3",
            "7d06be8f15f590c49ace8b0ce212b3a2a60c7c374cfc77d543a9ea352693523b",
            _STRUCT_FIELDS),
        "constructors": _CONSTRUCTORS,
        "getpoi": StructReturnFunctionRecord(
            71, "getPOI", "POIData", ((60, "idx", "int", "in"),),
            "131:1-142:2",
            "2e2af8b794794aefd3e993bbe6687094ae5a9dbdee98aee3aec066232aefbcd6",
            (("if", "135:5-135:70"),
             ("if", "136:5-136:93"),
             ("if", "137:5-137:70"),
             ("if", "138:5-138:114"),
             ("if", "139:5-139:70"),
             ("if", "140:5-140:70"),
             ("return", "141:5-141:41"))),
        "struct_local": StructLocalRecord(
            101, "p", "POIData",
            "175:17-175:35",
            "0751a948f2fc6ffa361445252ff8ec45196a938e0aabf3a0e186503968fe60ed",
            "decl", "175:9-175:36",
            "2c297191f4aebcc18e455ee9ccd5262122f503c99969b30d56f029a77e80101a",
            3, "block", "174:21-180:6",
            "call", "getPOI", 71, "175:21-175:35",
            "548fb6c75f3b9321b5702ede805086df007a50c39f1436634cd36c8304a57cc4",
            "175:17-175:35",
            "098f78b22f7ab78cb221b0f90f737dbd03b6d90af84db611fd4fcfca709fbc58"),
        "members": _MEMBERS,
        "materialization": _MATERIALIZATION,
        "main": (72, "main", "148:1-314:2"),
    },
}

_JULIA_RESULT_MATERIALIZATION = JuliaResultMaterialization(
    "custom-double-backed-mixed-precision",
    ("zMag2", "dzMag2", "stripeSum", "stripeCount", "stripeLast"),
    ("iter", "zMag2", "dzMag2", "stripeSum", "stripeCount", "stripeLast"),
    ("iter", "trapMin"),
    "iter = F32(iteration + 1) before double-backed store",
    "convergence iteration remains Number double",
    "trapMin remains unfrounded Number double",
    "JuliaResult local with seven source fields; custom native carrier",
)
_JULIA_MEMBER_SITES = (
    ("iter", "238:5-238:11"), ("zMag2", "239:5-239:12"),
    ("dzMag2", "240:5-240:13"), ("stripeSum", "241:5-241:16"),
    ("stripeCount", "242:5-242:18"), ("stripeLast", "243:5-243:17"),
    ("trapMin", "244:5-244:14"), ("iter", "253:9-253:15"),
    ("zMag2", "254:24-254:31"), ("iter", "256:19-256:25"),
    ("iter", "260:9-260:15"), ("zMag2", "261:23-261:30"),
    ("dzMag2", "262:24-262:32"),
    ("iter", "269:9-269:15"), ("stripeCount", "270:9-270:22"),
    ("stripeSum", "271:17-271:28"), ("stripeCount", "271:31-271:44"),
    ("stripeCount", "272:22-272:35"), ("stripeSum", "272:46-272:57"),
    ("stripeLast", "272:60-272:72"), ("stripeCount", "272:77-272:90"),
    ("zMag2", "273:24-273:31"),
    ("iter", "280:9-280:15"), ("trapMin", "281:24-281:33"),
)


def _julia_walk_statements(value):
    yield value
    for child in value.children:
        yield from _julia_walk_statements(child)


def _julia_member_census(program):
    result = []
    for function in program.functions:
        for statement in function.body:
            for node in _julia_walk_statements(statement):
                for expression in node.expressions:
                    stack = [expression]
                    while stack:
                        current = stack.pop()
                        if (current.kind == "member"
                                and current.children
                                and current.children[0].type.display() == "JuliaResult"):
                            result.append(current)
                        stack.extend(current.children)
    return sorted(result, key=lambda item: item.span.start)


def _authenticate_julia_struct_declaration(program, source_hash, profile):
    from . import julia_frontend_profile as frontend
    fail = lambda message: _profile_fail(JULIA_PROFILE, message)
    if profile != JULIA_PROFILE:
        raise fail("exact profile carrier required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (raw.count(b"        i += 1.0;") != 2
            or raw.splitlines()[219].strip() != b"i += 1.0;"):
        raise fail("normal iteration f32 store mutation")
    if (source_hash != frontend.RAW_SHA256
            or len(raw) != frontend.RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != frontend.RAW_SHA256
            or len(normalized) != frontend.NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != frontend.NORMALIZED_SHA256
            or _sha(program.functions) != frontend.FUNCTIONS_SHA256
            or _whole(program) != frontend.WHOLE_SHA256
            or _interface(program) != frontend.INTERFACE_SHA256):
        raise fail("source or typed identity lock mismatch")
    if (len(program.structs) != 1
            or program.structs[0].name != "JuliaResult"
            or _span(program.structs[0]) != "161:1-169:3"):
        raise fail("JuliaResult declaration identity mismatch")
    declaration = program.structs[0]
    fields = tuple(field.name for field in declaration.fields)
    types = tuple(field.type.display() for field in declaration.fields)
    ids = tuple(field.id for field in declaration.fields)
    if (fields != frontend.STRUCT_FIELD_NAMES
            or types != ("float",) * 7
            or ids != (51, 52, 53, 54, 55, 56, 57)):
        raise fail("JuliaResult seven-field declaration mismatch")
    julia = next((item for item in program.functions
                  if item.id == 91 and item.name == "juliaIterate"), None)
    if julia is None or julia.return_type.display() != "JuliaResult":
        raise fail("JuliaResult constructor owner mismatch")
    constructors = [item for item in julia.body[0].expressions
                    if item.kind == "declaration" and item.type.display() == "JuliaResult"
                    and item.symbol is not None and item.symbol.name == "r"]
    if len(constructors) != 1:
        raise fail("JuliaResult constructor/local census mismatch")
    members = _julia_member_census(program)
    actual_sites = tuple((item.member, _span(item), item.children[0].symbol.id)
                         for item in members)
    expected_sites = tuple((name, span, symbol)
                           for (name, span), symbol in zip(
                               _JULIA_MEMBER_SITES,
                               (132,) * 7 + (64,) * 3 + (66,) * 3
                               + (68,) * 9 + (70,) * 2))
    if actual_sites != expected_sites:
        raise fail("JuliaResult member-node identity mismatch")
    consumed = (declaration, *declaration.fields, constructors[0], *members)
    if len(consumed) != 33 or len({id(item) for item in consumed}) != len(consumed):
        raise fail("JuliaResult consumed-object ledger mismatch")
    return JuliaStructAdmissionRecord(
        "JuliaResult", fields, types, ids, 1,
        (_span(constructors[0]),), len(members), actual_sites, consumed)


def allowed_row_fields(key: str) -> frozenset[str]:
    """The complete set of slice-row fields permitted for ``key``.

    An allowlist, not a denylist: the validator's allowed-field arm compares
    ``set(item) != expected``, so equality with this set discharges "every
    other profile absent" by construction. Prepared keys answer from
    ``PREPARED_ROW_FIELDS`` -- the row contract is frozen now and enforced
    when the row lands.
    """
    fields = ALLOWED_ROW_FIELDS.get(key)
    if fields is None:
        raise _profile_fail(
            NEWTON_PROFILE,
            f"{key} is not an admitted struct-declaration carrier")
    return fields


def materialization_contract(key: str) -> StructMaterialization:
    """The frozen materialization contract for ``key``."""
    if key == JULIA_KEY:
        return _JULIA_RESULT_MATERIALIZATION
    lock = _LOCKS.get(key)
    if lock is None:
        raise _profile_fail(
            NEWTON_PROFILE,
            f"{key} is not an admitted struct-declaration carrier")
    return lock["materialization"]


def _find_struct_local(program: TypedProgram, lock: dict):
    """Locate the frozen struct local by symbol id, anywhere in the tree
    (it is nested inside an ``if``), returning the declaration node, its
    statement, the statement chain, and the owning function."""
    record = lock["struct_local"]
    for function in program.functions:
        for statement in function.body:
            for item, parent, path, chain in _walk_statement(statement):
                if (item.kind == "declaration"
                        and item.symbol is not None
                        and item.symbol.id == record.symbol_id):
                    return item, chain[-1], chain, function
    return None


def authenticate_struct_declaration(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple:
    """Return the frozen struct-plumbing identity of ``program.key``.

    Returns an empty tuple when ``program.key`` is not a carrier, so
    callers can treat the result as a membership set unconditionally;
    supplying a profile for a non-carrier key is a hard failure that names
    the sole (currently prepared) admitted declaration.

    Membership is the **authenticatable** set -- every frozen record,
    ``PREPARED_KEYS`` included -- not the landed registry: the record is
    the thing under test, and the slice-schema census is the integration
    gate's concern, not this function's.
    """
    if program.key == JULIA_KEY:
        return _authenticate_julia_struct_declaration(program, source_hash, profile)
    if program.key not in _LOCKS:
        if profile is not None:
            raise _profile_fail(
                NEWTON_PROFILE,
                "program key is not an admitted struct-declaration carrier; "
                f"{NEWTON_KEY} struct POIData at 125:1-129:3 (fields "
                "center vec4 126:5, deg float 127:5, maxZoom float 128:5) "
                "is the sole admitted declaration")
        return ()
    lock = _LOCKS[program.key]

    def fail(message: str) -> ValueError:
        return _profile_fail(lock["profile"], message)

    if profile != lock["profile"]:
        raise fail("exact profile carrier required")

    # --- coarse gate (in evaluation order) --------------------------------
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
    if not _declaration_inventory_holds(program, lock):
        raise fail("global declaration inventory mismatch")

    total, assigns = _node_census(program)
    if not _node_census_holds(total, assigns, lock):
        raise fail("whole-program node census mismatch")

    # --- the struct census (value tiers ahead of identity tiers) ----------
    # The FIELD value tier runs ahead of the STRUCT identity tier: a
    # field-level mutation also shifts the struct's own hash (fields are
    # embedded in its repr), so evaluating the struct identity first would
    # absorb field-value drift and make the field census vacuous.
    if not _struct_inventory_holds(program, lock):
        raise fail("struct inventory mismatch")
    if not _struct_fields_hold(program, lock):
        raise fail("struct field census mismatch")
    if not _struct_declaration_identity_holds(program, lock):
        raise fail("struct declaration identity mismatch")
    if not _struct_field_identity_holds(program, lock):
        raise fail("struct field identity mismatch")

    # Locate getPOI by id, never by position.
    entries = [item for item in program.functions
               if item.id == lock["getpoi"].id]
    if len(entries) != 1:
        raise fail("struct return function identity mismatch")
    getpoi = entries[0]
    if not _getpoi_signature_holds(getpoi, lock):
        raise fail("struct return signature mismatch")
    if not _getpoi_body_holds(getpoi, lock):
        raise fail("getPOI body shape mismatch")

    census = list(_struct_constructor_census(program))
    if not _constructor_census_holds(census, lock):
        raise fail(f"struct constructor census mismatch: {len(census)}")
    if not _constructor_values_hold(census, lock):
        raise fail("struct constructor payload mismatch")
    if not _constructor_identity_holds(census, lock):
        raise fail("struct constructor identity mismatch")

    site = _find_struct_local(program, lock)
    if not _struct_local_shape_holds(site, lock):
        raise fail("struct local census mismatch")
    if not _struct_local_identity_holds(site, lock):
        raise fail("struct local identity mismatch")

    members = list(_member_site_census(program))
    if not _member_census_holds(members, lock):
        raise fail(f"struct member census mismatch: {len(members)}")
    if not _member_swizzle_holds(members, lock):
        raise fail("member swizzle census mismatch")
    if not _member_identity_holds(members, lock):
        raise fail("struct member identity mismatch")

    if not _no_struct_parameters_holds(program):
        raise fail("struct-typed parameter census mismatch")
    if not _materialization_contract_holds(lock["materialization"], lock):
        raise fail("struct materialization contract mismatch")

    # --- visitation ledger -------------------------------------------------
    # Every authenticated object, consumed exactly once: the struct, its
    # three fields, seven constructors, four members, two swizzles, four
    # member bases, the struct-local declaration node, its initializer
    # call, its Symbol, getPOI and main.
    mains = [item for item in program.functions
             if item.id == lock["main"][0] and item.name == lock["main"][1]]
    if len(mains) != 1:
        raise fail("struct local census mismatch")
    main = mains[0]
    node, statement, chain, function = site
    _check_ledger(
        [program.structs[0], *program.structs[0].fields,
         *(item for _, item, _, _ in census),
         *(item for item, _, _, _ in members),
         *(parent for _, parent, _, role in members
           if role == "swizzled"),
         *(base for _, _, base, _ in members),
         node, node.children[0], node.symbol, getpoi, main],
        _CONSUMED_LEDGER, "struct-declaration-newton", lock["profile"])
    return (program.structs[0],
            tuple(item for _, item, _, _ in census),
            tuple(item for item, _, _, _ in members))


def apply_struct_declaration(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_struct_declaration(program, source_hash, profile)
    return program
