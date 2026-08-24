"""Exact identity profiles for **source-declared uv-alias varyings** (the
``in vecN name;`` family at file scope).

``filter/wobble:wobble`` is the first carrier and the only **landed** record;
``filter/grime:grime`` is the second frozen record, **prepared** (below). The
design (``docs/port-engineering/varying-parity/varying-design.md``) measured
that all four real programs of the bucket materialize the varying identically,
and that a record must not be frozen before its program's whole validator
closure is admitted. ``texture`` (scalar-uint ``^``/``^=``/``>>``/``&`` plus
``inversesqrt``) is three mechanisms behind; ``spookyTicker`` is three carrier
slices behind; neither has a record here. ``wormhole:deposit``'s ``vColor`` is
the *caller-supplied* class whose factory is dead code in the reference
renderer -- it is rejected by the alias map and admitted by nothing.

wobble declares exactly one varying, ``in vec2 v_texCoord;`` at raw
``wobble.glsl:14``, reads it exactly once in ``main`` at normalized
``100:24-100:34`` (``vec2 sampleCoord = v_texCoord + offset;``), and never
writes it.

grime's record and why freezing it is legitimate (design 5.2, restated)
-----------------------------------------------------------------------

grime declares exactly one varying, ``in vec2 v_texCoord;`` at raw
``grime.glsl:19:1``, reads it exactly twice in ``main`` -- normalized
``131:24-131:34`` (``vec2 globalCoord = v_texCoord * tileSize +
tileOffset;``) and ``134:41-134:51`` (``texture(inputTex, v_texCoord)``) --
and never writes it. The 5.2 rule says a record must not be frozen before
its program's whole validator closure is admitted, or the frozen
"CLEAN behind the varying" census would be a lie. grime's whole closure
behind the varying is now **identified and carried**: design 3's ladder
measured that with the varying admitted the next (and last) blocker is the
five ``floatBitsToUint`` sites, and with those admitted the validator is
CLEAN; those five sites are frozen in
``grime_float_bits_ingress_profile.py`` (the fifth float-bit
identity-admission carrier after caustic/scanlineError/shapes/shapeMixer),
prepared in the same slice-shape as this record. The JS authority is the
same one-mechanism materialization the wobble record froze --
``canonicalFactory66`` (``canonical-kernels.js:13836``, registered for
``filter/grime:grime`` at ``:36246``): the slot line
``var v_texCoord = new Float32Array([0, 0]);`` and the closure copy
``v_texCoord.set($runtime.varyings["v_texCoord"])`` after ``beginPixel``
(``:13983-13984``); its ``Function.prototype.toString`` SHA-256 is
``c5100a562df7d991381ed1be6e1bb9fd1f8b117f212b267ee23719734d80123f``
(8,413 bytes, byte-equal to the generated-file slice; the pinning method
reproduces the wobble oracle's frozen cellRefract digest
``329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3`` on the
same snapshot and node). The record stays **prepared** -- its row lands in a
later slice together with the ingress carrier's field.

The JavaScript authority, quoted and measured
----------------------------------------------

There is no vertex stage and no interpolation anywhere in the CPU reference.
``glsl-runtime.js:95-99`` hardcodes a three-slot varying map::

    this.varyings = {
      vUv: new Float32Array(2),
      v_texCoord: new Float32Array(2),
      vColor: new Float32Array(4),
    }

and ``beginPixel`` aliases the pixel context's ``uv`` into both uv slots
element by element (``glsl-runtime.js:148-151``)::

    this.varyings.vUv[0] = uv[0]
    this.varyings.vUv[1] = uv[1]
    this.varyings.v_texCoord[0] = uv[0]
    this.varyings.v_texCoord[1] = uv[1]

``vColor`` alone is caller-supplied (``context.varyings?.vColor``, left at
zeros when absent). A declared varying with any other name would make the
generated ``name.set(undefined)`` throw at the first pixel, so the corpus's
five-name census is the **soundness bound** of the runtime's design; the
alias map below (``{vUv, v_texCoord}``) is the port-side mirror of that bound.

The numeric contract, per lane: exactly one rounding --
``F32((x + 0.5) * (1.0 / width))`` and ``F32((height - y - 0.5) *
(1.0 / height))`` -- the product and the reciprocal in binary64, the narrowing
at the ``Float32Array`` store (``pass-runner.js:21,39,45``); every downstream
copy is f32->f32 and idempotent. The existing C++ population
(``make_context``, ``pass_runner.cpp:20-29``) is *float division*, a different
expression whose agreement with the double product is empirical: measured
exhaustively for every size 1..1024 and every pixel, both lanes including the
y-flip, zero mismatches (spot-checked at 2048/4096). The identity is locked by
the test suite over that stated bound, not assumed.

Pure expression lowering -- no ABI change
-----------------------------------------

The C++ port already has the value: ``glsl::PixelContext`` carries
``Vec2 uv{}``. Admission therefore adds **no binding, no State/Frame field,
and no kernel-signature change** -- the emitter lowers every read of the
admitted symbol to ``context.uv`` (a ``glsl::Vec2`` lvalue), the same
``name()`` dispatcher arm shape as ``gl_FragCoord`` -> ``context.frag_coord``.
``kernel_signature_change`` is frozen ``"none"``.

The whole-file span trap (design 1.7)
-------------------------------------

The varying ``Symbol``'s span is the **whole file** (``1:1-107:1`` for
wobble): the analyzer constructs it before declarations are inventoried, and
the preprocessor drops the declaration line from the normalized source
entirely (``preprocess.py:55-61``, *"capture ``in vecN Y;`` varyings (dropped;
codegen maps them to ctx.uv)"*). Consequences locked here as measured facts:

* the varying is **not** in ``typed.declarations`` at all -- it exists only in
  ``typed.interface_symbols`` and as the resolution target of ``id`` nodes
  (``body_globals``). A separate lock freezes that absence, so the emitter's
  ``name()`` arm stays the only consumer path.
* the span lock pins the Symbol's own span **as the whole-file span it is**;
  the raw-source declaration site (``wobble.glsl:14:1``, regex-derived from
  the caller's raw bytes) is carried separately. Do not "fix" the span to the
  declaration site: whole/interface fingerprints include
  ``interface_symbols``.

Landed / prepared (cellRefract 16's kaleido pattern)
----------------------------------------------------

``filter/wobble:wobble`` carries ``varying_profile`` as typed row 189
(insertion index 155): the module landed PREPARED with an empty registry and
the integration slice moved ``WOBBLE_KEY`` into ``KEYS`` together with the
row. ``filter/grime:grime`` is now the second PREPARED record -- its whole
closure behind the varying is identified and carried (the varying plus the
five ``floatBitsToUint`` sites in ``grime_float_bits_ingress_profile.py``),
so freezing no longer asserts an unadmitted CLEAN census (design 5.2,
restated above); its row lands in a later slice, together with the ingress
carrier's field, at which point ``GRIME_KEY`` moves into ``KEYS``.
``texture`` and ``spookyTicker`` keep no record (design 5.2 -- their
closures behind the varying are three mechanisms deep).

Sibling-proof allowlist (cellRefract 13.2 lesson, applied strictly)
-------------------------------------------------------------------

Unlike the cellRefract array carrier, this module allows **no** sibling proof
field: wobble carries none, and every optional ``fixed_*_proof`` field a
``TypedProgram`` can carry is frozen absent -- enumerated from the dataclass,
so a new proof field added elsewhere in the tree turns the test red here
rather than slipping through.

Census discipline
-----------------

Per the standing trap, every walker here descends ``program.declarations``
(global initializers included) as well as ``function.body``. The read census
and the write census are what prove read-only-ness; the write census is
frozen **empty**, so a future parser change cannot silently admit a write.
This module deliberately carries no "writes allowed" switch.
"""

from __future__ import annotations

import hashlib
import re
from typing import NamedTuple

# grime's row contract names its companion carrier's field; the ingress
# module owns the name (module name == row field, the scanline/shapes
# convention) and this module freezes the composed set.
from .grime_float_bits_ingress_profile import GRIME_FLOAT_BITS_INGRESS_FIELD
from .typed_ir import TypedProgram


WOBBLE_KEY = "filter/wobble:wobble"
WOBBLE_PROFILE = "varying-uv-admission-v1"
GRIME_KEY = "filter/grime:grime"
# One mechanism, one profile string (design 5.1): grime's record is a second
# KEY of this module, not a second capability.
GRIME_PROFILE = WOBBLE_PROFILE

# The LANDED carrier registry. wobble's row landed as typed row 189
# (insertion index 155), moving WOBBLE_KEY out of the prepared set and into
# KEYS together with the row -- the one-line move the design records. The
# registry and the slice stay in lockstep: `load_slice`'s per-field schema
# census sees a registered key exactly when its row carries the field.
KEYS: tuple[str, ...] = (WOBBLE_KEY, GRIME_KEY)
PROFILES: dict[str, str] = {WOBBLE_KEY: WOBBLE_PROFILE, GRIME_KEY: GRIME_PROFILE}
VARYING_UV_KEYS = frozenset(PROFILES)

# Records frozen and authenticatable whose rows land in a later slice.
# grime moved OUT of this set when its row landed as a typed row, the same
# one-line move wobble made -- the registry and the slice stay in lockstep.
# texture/spookyTicker still have no record at all: their closures behind the
# varying are three mechanisms deep (design 5.2), so the varying being their
# FIRST reported blocker understates what they need.
PREPARED_KEYS: tuple[str, ...] = ()
PREPARED_PROFILES: dict[str, str] = {}

# The complete allowed field set for the slice row -- an ALLOWLIST, not a
# denylist, exhaustive by construction against the validator's
# `set(item) != expected` comparison. wobble's design row (10) is the
# universal two fields plus exactly one profile field: pure expression
# lowering, no ABI change, no companion carrier. grime's landing row carries
# TWO profile fields -- the varying carrier and its float-bit ingress
# companion, the only other mechanism in grime's measured closure (design 3)
# -- and the field name is imported from that module so the two frozen
# contracts cannot drift apart.
ALLOWED_ROW_FIELDS: dict[str, frozenset[str]] = {
    WOBBLE_KEY: frozenset({
        "defines",
        "program_key",
        "varying_profile",
    }),
    GRIME_KEY: frozenset({
        "defines",
        "program_key",
        "varying_profile",
        GRIME_FLOAT_BITS_INGRESS_FIELD,
    }),
}
PREPARED_ROW_FIELDS: dict[str, frozenset[str]] = {}

# The runtime's uv-alias pair (glsl-runtime.js:95-99, 148-151): the only two
# varying names the CPU reference can materialize. `vColor` is the
# caller-supplied class -- dead factory code in the reference renderer -- and
# is rejected here exactly as 5.5 requires.
UV_ALIAS_NAMES = frozenset({"vUv", "v_texCoord"})

# Every optional `fixed_*_proof` field a TypedProgram carries. Unlike the
# cellRefract array carrier, NONE is allowed: wobble carries no sibling proof,
# and the frozen-absent set is the whole dataclass enumeration. The test
# suite re-derives this set, so a new proof field added elsewhere in the tree
# turns red here rather than slipping through.
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

# The emitted lowering target, asserted rather than inherited so a rename of
# `PixelContext::uv` in the runtime headers turns a test red.
_LOWERING_TARGET = "context.uv"
_NATIVE_TYPE = "glsl::Vec2"
_KERNEL_SIGNATURE_CHANGE = "none"
_NUMERIC_CONTRACT = "per-lane f32, single narrowing, double product"
_LANE_EXPRESSIONS = (
    "F32((x + 0.5) * (1.0 / width))",
    "F32((height - y - 0.5) * (1.0 / height))",
)
_JS_ALIAS_EVIDENCE = (
    "glsl-runtime.js:95-99 this.varyings = { vUv: new Float32Array(2), "
    "v_texCoord: new Float32Array(2), vColor: new Float32Array(4) }",
    "glsl-runtime.js:148-151 this.varyings.vUv[0] = uv[0]; "
    "this.varyings.vUv[1] = uv[1]; this.varyings.v_texCoord[0] = uv[0]; "
    "this.varyings.v_texCoord[1] = uv[1]  (beginPixel: const uv = context.uv)",
    "pass-runner.js:21,39,45 uv[0] = (x + 0.5) * (1 / width); "
    "uv[1] = (height - y - 0.5) * (1 / height)  (binary64 product and "
    "reciprocal, narrowing at the Float32Array store)",
)

# The raw-source declaration recognizer, anchored to its measured raw line
# (design 5.2's regex). The normalized source has no such line to match --
# the preprocessor drops it -- so the caller's raw bytes are the only place
# the declaration site exists at all.
_RAW_DECLARATION_PATTERN = re.compile(
    r"^[ \t]*(?:flat[ \t]+)?in[ \t]+(vec2)[ \t]+(v_texCoord)[ \t]*;[ \t]*$",
    re.MULTILINE)

# Every IR shape that mutates a writable lvalue. `post` is a distinct kind
# from `unary`, not an operator variant of it.
_MUTATION_KINDS = ("assign", "unary", "post")
_INCREMENT_OPERATORS = ("++", "--")

# The admitted varying Symbol and the one authenticated read node: 2 distinct
# objects, each consumed exactly once -- wobble's count, kept as the module
# default. grime's record carries its own per-key count (symbol + two read
# nodes = 3) in ``lock["consumed_ledger"]``; a key without the field answers
# this default, so the landed wobble sabotage tests keep patching the module
# constant exactly as before.
_CONSUMED_LEDGER = 2

__all__ = (
    "KEYS", "PROFILES", "VARYING_UV_KEYS", "PREPARED_KEYS", "PREPARED_PROFILES",
    "WOBBLE_KEY", "WOBBLE_PROFILE", "GRIME_KEY", "GRIME_PROFILE",
    "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS", "allowed_row_fields",
    "UV_ALIAS_NAMES", "VaryingUvContract", "VaryingReadRecord",
    "VaryingWriteRecord", "varying_uv_contract",
    "authenticate_varying_uv", "apply_varying_uv",
)


class VaryingUvContract(NamedTuple):
    """The frozen emission contract both authorities must honour.

    The parity target is the runtime's aliasing, not any interpolation: the
    admitted symbol lowers to ``context.uv`` (a ``glsl::Vec2`` lvalue) by
    pure expression replacement, with no kernel-signature change and the
    per-lane f32 numeric contract the pixel loop already computes.
    """

    symbol_id: int
    name: str
    glsl_type: str
    native_type: str
    alias_of: str
    lowering_target: str
    kernel_signature_change: str
    numeric_contract: str
    lane_expressions: tuple[str, str]
    js_alias_evidence: tuple[str, ...]
    raw_declaration_site: str


class VaryingReadRecord(NamedTuple):
    """One read site's complete identity: owner, span, node hash, the parent
    expression that consumes it, and the owning statement's position."""

    symbol_id: int
    symbol_name: str
    owner_id: int
    owner_name: str
    span: str
    node_type: str
    node_sha256: str
    parent_kind: str
    parent_operator: str | None
    parent_span: str
    statement_index: int
    statement_kind: str
    statement_span: str


class VaryingWriteRecord(NamedTuple):
    """Every mutation of the varying. Frozen EMPTY: all four carrier programs
    are read-only, and the empty census is what keeps a future parser change
    from silently admitting a write."""

    symbol_id: int
    symbol_name: str
    owner_id: int
    owner_name: str
    kind: str
    operator: str | None
    span: str
    node_sha256: str


class _ReadSite(NamedTuple):
    record: VaryingReadRecord
    node: object


class _WriteSite(NamedTuple):
    record: VaryingWriteRecord
    node: object


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

    In a shared module a failure on one key must never name another key's
    profile; the profile is therefore always an argument, never a default."""
    return ValueError(f"{profile}: {message}")


def _check_ledger(entries: list, expected: int, label: str,
                  profile: str = WOBBLE_PROFILE) -> None:
    """Require ``entries`` to hold exactly ``expected`` distinct objects.

    The profile is the failing key's own name (per-key ``_profile_fail``
    discipline); the default keeps direct helper calls naming the module's
    first key."""
    identities = [id(item) for item in entries]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _profile_fail(profile,
                            f"{label} visitation ledger mismatch")


# --- walkers ----------------------------------------------------------------
#
# Every walker here descends `program.declarations` as well as
# `program.functions`. A "whole-program" census that only walks `function.body`
# leaves global declaration initializers in a coarse-hash-only blind spot.

def _walk_expression(value, parent=None, grandparent=None, path=()):
    """Yield ``(node, parent, grandparent, path)`` for every expression node."""
    yield value, parent, grandparent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, parent, (*path, index))


def _walk_statement(value, path=(), ancestors=()):
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


def _node_census(program: TypedProgram) -> tuple[int, int]:
    total = 0
    assigns = 0
    for _, _, item, _, _, _, _ in _program_nodes(program):
        total += 1
        if item.kind == "assign":
            assigns += 1
    return total, assigns


def _declaration_inventory(program: TypedProgram) -> tuple:
    """All declarations, order-insensitive."""
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


def _base_symbol_node(node):
    """Strip swizzle/member/index clothing down to the base expression."""
    current = node
    while current.kind in ("swizzle", "member", "index") and current.children:
        current = current.children[0]
    return current


def _mutation_targets(program: TypedProgram, symbols: dict[int, str]) -> dict:
    """Every mutation-shaped node whose target *base* is an admitted varying.

    Compound assignment (``+=``, ...) is kind ``assign`` with a non-``=``
    operator; prefix and postfix increment are the two different kinds
    ``unary`` and ``post`` -- both mutate a writable lvalue and both must be
    caught (testing only ``unary`` lets ``v_texCoord.x++`` through)."""
    targets: dict[int, tuple] = {}
    for function, _, node, _, _, _, _ in _program_nodes(program):
        if node.kind not in _MUTATION_KINDS or not node.children:
            continue
        if node.kind != "assign" and node.operator not in _INCREMENT_OPERATORS:
            continue
        base = _base_symbol_node(node.children[0])
        if base.kind != "id" or base.symbol_id not in symbols:
            continue
        owner_id = -1 if function is None else function.id
        owner_name = ("<global-initializer>" if function is None
                      else function.name)
        targets[id(base)] = (node, base, owner_id, owner_name)
    return targets


def _reference_census(program: TypedProgram, symbols: dict[int, str]
                      ) -> tuple[list, list]:
    """Classify every ``id`` reference to the admitted varyings.

    A reference is a **write base** only when it is the base of a mutation
    node's target (``_mutation_targets``). Everything else is a read --
    including swizzle reads, call arguments and initializer uses. The frozen
    read census is the ordered tuple of read records; the write census is
    frozen empty."""
    targets = _mutation_targets(program, symbols)
    reads: list[_ReadSite] = []
    writes: list[_WriteSite] = []
    for function, _, node, parent, _, path, chain in _program_nodes(program):
        if node.kind != "id" or node.symbol_id not in symbols:
            continue
        owner_id = -1 if function is None else function.id
        owner_name = ("<global-initializer>" if function is None
                      else function.name)
        if id(node) in targets:
            continue
        reads.append(_ReadSite(
            VaryingReadRecord(
                node.symbol_id, symbols[node.symbol_id], owner_id, owner_name,
                _span(node), node.type.display(), _sha(node),
                "" if parent is None else parent.kind,
                None if parent is None else getattr(parent, "operator", None),
                "" if parent is None else _span(parent),
                -1 if not path else path[0],
                "" if not chain else chain[-1].kind,
                "" if not chain else _span(chain[-1])),
            node))
    for mutation, base, owner_id, owner_name in targets.values():
        writes.append(_WriteSite(
            VaryingWriteRecord(
                base.symbol_id, symbols[base.symbol_id], owner_id, owner_name,
                mutation.kind, getattr(mutation, "operator", None),
                _span(mutation), _sha(mutation)),
            mutation))
    return reads, writes


# --- individually deletable locks -------------------------------------------
#
# Each predicate below is exactly one lock with exactly one message. A test
# proves a lock load-bearing by re-executing this module into a scratch
# namespace, replacing one of these functions with an always-true stand-in,
# and showing that the lock's message disappears. Keep them small,
# single-purpose and side-effect free.
#
# Ordering matters. `Symbol` embeds its span, so every value-level lock
# (alias name, storage, mutability, direction, type, both spans, the raw
# declaration site) is evaluated AHEAD of the symbol-hash identity lock that
# would otherwise absorb them and make them vacuous.

def _caller_source_hash_holds(source_hash: str | None, lock: dict) -> bool:
    """The caller's own view of the source agrees with the frozen record."""
    return source_hash == lock["raw_sha256"]


def _defines_hold(program: TypedProgram, lock: dict) -> bool:
    """Exactly the empty define tuple -- wobble carries no defines."""
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
    """Every sibling optional proof is absent -- all of them (the strict
    form of Amendment 13.2: wobble carries no sibling proof at all)."""
    return all(getattr(program, field, None) is None
               for field in _OPTIONAL_PROOF_FIELDS)


def _function_cardinality_holds(program: TypedProgram, lock: dict) -> bool:
    return len(program.functions) == lock["function_count"]


def _function_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    """All six functions by id, name, return type and parameters."""
    return _function_inventory(program) == lock["function_inventory"]


def _declaration_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    """All nine declarations, order-insensitive: an added or removed global
    anywhere in the program is a hard failure here."""
    return (len(program.declarations) == lock["declaration_count"]
            and _declaration_inventory(program)
            == lock["declaration_inventory"])


def _initializer_census_holds(program: TypedProgram, lock: dict) -> bool:
    """The three const globals' initializers, node by node: the census walks
    global declaration initializers, so a varying reference planted in one
    cannot hide behind a coarse hash."""
    return _initializer_census(program) == lock["initializer_census"]


def _resources_hold(program: TypedProgram, lock: dict) -> bool:
    """One sampler, four scalar uniforms, one output, texture reads, no
    derivatives. wobble declares no resolution-class uniform at all."""
    resources = program.resources
    return ((resources.uniforms, resources.samplers, resources.outputs,
             resources.uses_texture, resources.uses_derivatives)
            == lock["resources"])


def _call_graph_holds(program: TypedProgram, lock: dict) -> bool:
    """The exact call-graph edge set, its digest, and full reachability --
    all six functions are reachable from ``main``."""
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


def _node_census_holds(total: int, assigns: int, lock: dict) -> bool:
    return total == lock["total_nodes"] and assigns == lock["total_assigns"]


def _interface_cardinality_holds(program: TypedProgram, lock: dict) -> bool:
    """Exactly one interface symbol -- no second varying, and no builtin in
    the interface list."""
    return len(program.interface_symbols) == lock["interface_cardinality"]


def _uv_alias_name_holds(symbol, lock: dict) -> bool:
    """The name is one the runtime can materialize as ``context.uv``. This is
    the port-side mirror of the three-slot soundness bound: `vColor` and any
    other name are rejected here, ahead of identity."""
    return symbol.name in UV_ALIAS_NAMES


def _varying_storage_holds(symbol, lock: dict) -> bool:
    """``varying`` storage, not writable, direction ``in`` -- the read-only
    storage class, checked before the symbol hash that would absorb it."""
    return (symbol.storage == lock["varying"][3]
            and symbol.storage == "varying"
            and symbol.writable is False
            and symbol.direction == "in")


def _varying_type_holds(symbol, lock: dict) -> bool:
    """``vec2`` -- a float vector of width 2, the shape ``context.uv``
    carries; a ``vec3``/``vec4`` varying has no aliasing semantics."""
    return (symbol.type.display() == lock["varying"][2]
            and symbol.type.kind == "vector"
            and symbol.type.base == "float"
            and symbol.type.width == 2
            and symbol.type.display() == "vec2")


def _symbol_span_holds(symbol, lock: dict) -> bool:
    """The Symbol's span is the WHOLE-FILE span it is (design 1.7) -- locked
    as measured, never "fixed" to the declaration site it resembles. The
    raw-source declaration site is a separate lock."""
    return _span(symbol) == lock["symbol_span"]


def _raw_declaration_holds(program: TypedProgram, lock: dict) -> bool:
    """The raw bytes carry exactly one ``in vec2 v_texCoord;`` declaration,
    on the frozen raw line and column. The normalized source cannot be
    consulted: the preprocessor drops the line entirely."""
    source_path, text, line = lock["raw_declaration"]
    raw = program.raw_source
    matches = list(_RAW_DECLARATION_PATTERN.finditer(raw))
    if len(matches) != 1:
        return False
    match = matches[0]
    line_no = raw.count("\n", 0, match.start()) + 1
    column = len(raw[:match.start()].rsplit("\n", 1)[-1]) + 1
    if match.group(0) != text:
        return False
    return (line_no == line
            and column == 1
            and f"{source_path}:{line}:{column}"
            == lock["contract"].raw_declaration_site)


def _varying_identity_holds(symbol, lock: dict) -> bool:
    """Symbol id, name, type, the whole-file span, and the node hash."""
    identifier, name, type_name, _, _, span, sha = lock["varying"]
    return ((symbol.id, symbol.name, symbol.type.display(), _span(symbol),
             _sha(symbol)) == (identifier, name, type_name, span, sha))


def _no_declaration_inventory_entry_holds(program: TypedProgram,
                                          lock: dict) -> bool:
    """The varying exists only in ``interface_symbols`` (design 1.7); a
    ``typed.declarations`` entry carrying the symbol would give the
    declaration-storage walker a second consumer path."""
    identifier = lock["varying"][0]
    return all(item.symbol.id != identifier
               for item in program.declarations)


def _read_census_holds(reads: list, lock: dict) -> bool:
    """The exact ordered read census: one read in ``main`` at the frozen
    site, consumed by the frozen parent expression in the frozen statement.
    Every ``id`` node referencing the varying must be exactly it."""
    return (len(reads) == len(lock["reads"])
            and tuple(item.record for item in reads) == lock["reads"])


def _write_census_holds(writes: list, lock: dict) -> bool:
    """The write census is frozen EMPTY. All four carrier programs are
    read-only; the GLSL ``in`` storage and ``writable=False`` make it
    structural, but the census is frozen anyway so a future parser change
    cannot silently admit a write."""
    return (len(writes) == len(lock["writes"])
            and tuple(item.record for item in writes) == lock["writes"])


def _varying_contract_holds(contract: VaryingUvContract, lock: dict) -> bool:
    """The emission contract: alias-of/lowering-to ``context.uv`` as a
    ``glsl::Vec2`` lvalue, no kernel-signature change, the per-lane f32
    double-product numeric contract, and the measured JS evidence strings."""
    return (contract == lock["contract"]
            and contract.alias_of == _LOWERING_TARGET
            and contract.lowering_target == _LOWERING_TARGET
            and contract.native_type == _NATIVE_TYPE
            and contract.kernel_signature_change == _KERNEL_SIGNATURE_CHANGE
            and contract.numeric_contract == _NUMERIC_CONTRACT
            and contract.lane_expressions == _LANE_EXPRESSIONS
            and contract.js_alias_evidence == _JS_ALIAS_EVIDENCE)


# --- frozen per-key records --------------------------------------------------

_LOCKS = {
    WOBBLE_KEY: {
        "profile": WOBBLE_PROFILE,
        "source_path": "filter/wobble/wobble.glsl",
        "raw_bytes": 3105,
        "raw_sha256": "1bdd1e3bed9111743dfeb7e3418e14c42aa8d93ed4636167a99d17cb143a38cc",
        "normalized_bytes": 2589,
        "normalized_sha256": "c767dbef8eaa5c0730c6502053b7edf4af30d051de154425fd19860368e34545",
        "functions_sha256": "82c6f49e48c9177993b949d7879970dca135284d8b914c04c585048e78997298",
        "whole_sha256": "d3b1a67dbd5176e108376de6c5eb2164356b4fb172038a445f5b9f9fd9f8749f",
        "interface_sha256": "65dad134040138d6596f9a2d07da1eddbce9fd68989624fa3b21a888eb67e888",
        "defines": (),
        "function_count": 6,
        "declaration_count": 9,
        "function_inventory": (
            (17, "applyWrap", "vec2", ((16, "uv", "vec2"),)),
            (18, "hash31", "float", ((11, "p", "vec3"),)),
            (19, "main", "void", ()),
            (20, "noise3d", "float", ((12, "p", "vec3"),)),
            (21, "pcg", "uvec3", ((10, "v", "uvec3"),)),
            (22, "simplexRandom", "float", ((13, "t", "float"),
                                             (14, "spd", "float"),
                                             (15, "seed", "vec3"))),
        ),
        "declaration_inventory": (
            (1, "inputTex", "sampler2D", "uniform", False, False, "7:1-7:28"),
            (2, "time", "float", "uniform", False, False, "8:1-8:20"),
            (3, "speed", "float", "uniform", False, False, "9:1-9:21"),
            (4, "range", "float", "uniform", False, False, "10:1-10:21"),
            (5, "wrap", "float", "uniform", False, False, "11:1-11:20"),
            (6, "fragColor", "vec4", "output", True, False, "13:1-13:16"),
            (7, "TAU", "float", "const", False, True, "15:1-15:36"),
            (8, "X_NOISE_SEED", "vec3", "const", False, True, "16:1-16:50"),
            (9, "Y_NOISE_SEED", "vec3", "const", False, True, "17:1-17:49"),
        ),
        "initializer_census": (
            (7, "TAU", (
                ("literal", "15:19-15:35", "6.28318530717959",
                 "6.28318530717959", "float"),)),
            (8, "X_NOISE_SEED", (
                ("construct", "16:27-16:49", None, "None", "vec3"),
                ("literal", "16:32-16:36", "17.0", "17.0", "float"),
                ("literal", "16:38-16:42", "29.0", "29.0", "float"),
                ("literal", "16:44-16:48", "11.0", "11.0", "float"))),
            (9, "Y_NOISE_SEED", (
                ("construct", "17:27-17:48", None, "None", "vec3"),
                ("literal", "17:32-17:36", "41.0", "41.0", "float"),
                ("literal", "17:38-17:42", "23.0", "23.0", "float"),
                ("literal", "17:44-17:47", "7.0", "7.0", "float"))),
        ),
        "resources": (("inputTex", "time", "speed", "range", "wrap"),
                      ("inputTex",), ("fragColor",), True, False),
        "counted_loop_proof": (0, 0, 0, 0, 0, True),
        "call_edge_count": 5,
        "call_graph_sha256": "aff1e20f7afbb4a3ead812457bcfdfeb9d413cfe5fe3859c9cab92d52f5da0ee",
        "reachable": (17, 18, 19, 20, 21, 22),
        "unreachable": (),
        "total_nodes": 370,
        "total_assigns": 11,
        "interface_cardinality": 1,
        # symbol id, name, type, storage, writable, THE REAL whole-file span,
        # symbol node hash. The span is the whole file because the analyzer
        # constructs the Symbol before declarations are inventoried and the
        # preprocessor drops the declaration line (design 1.7).
        "varying": (24, "v_texCoord", "vec2", "varying", False,
                    "1:1-107:1",
                    "64c07c4b70c09e69521c7f56fd4afb1ec20e6aab4469e4db8fe36cb54415ca12"),
        "symbol_span": "1:1-107:1",
        # The raw-source declaration site, regex-derived from the caller's
        # raw bytes: file, exact line text, 1-based line number (column 1).
        "raw_declaration": ("filter/wobble/wobble.glsl",
                            "in vec2 v_texCoord;", 14),
        "reads": (
            VaryingReadRecord(
                symbol_id=24, symbol_name="v_texCoord",
                owner_id=19, owner_name="main",
                span="100:24-100:34", node_type="vec2",
                node_sha256="c1c81c4cc993ca1f4330a4d649b7ca1f217f9771f949a26b9cc68ddfa1f875a9",
                parent_kind="binary", parent_operator="+",
                parent_span="100:24-100:43",
                statement_index=6, statement_kind="decl",
                statement_span="100:5-100:44"),
        ),
        "writes": (),
        "contract": VaryingUvContract(
            symbol_id=24, name="v_texCoord", glsl_type="vec2",
            native_type=_NATIVE_TYPE,
            alias_of=_LOWERING_TARGET, lowering_target=_LOWERING_TARGET,
            kernel_signature_change=_KERNEL_SIGNATURE_CHANGE,
            numeric_contract=_NUMERIC_CONTRACT,
            lane_expressions=_LANE_EXPRESSIONS,
            js_alias_evidence=_JS_ALIAS_EVIDENCE,
            raw_declaration_site="filter/wobble/wobble.glsl:14:1"),
    },
    # grime's PREPARED record -- every figure re-derived from the pinned
    # corpus with the mutable_global_frame_profile helpers (never
    # hand-transcribed from the design): raw 5,776 B / 15a88fff...;
    # normalized 5,279 B / 692547b5...; whole / interface / functions
    # fingerprints as frozen below; 645 nodes / 15 assigns; 7 declarations
    # (1 sampler, 5 uniforms, 1 output -- NO const globals, so the
    # initializer census is the empty tuple); 14 functions (ids 40-53), all
    # reachable; 22 call edges. `resolution` is declared-but-unread (the
    # cellRefract class) and stays a required ABI binding. The varying:
    # symbol id 55, whole-file span 1:1-169:2 (the normalized source is 169
    # lines -- design 1.7), raw declaration at grime.glsl:19:1, two reads /
    # no writes, both in main. The per-key ledger counts the symbol plus
    # both read nodes.
    GRIME_KEY: {
        "profile": GRIME_PROFILE,
        "source_path": "filter/grime/grime.glsl",
        "raw_bytes": 5776,
        "raw_sha256": "15a88fff0e951bf7fa01f4c982532cf79d835663cb2a81c2076c5fecbd9c351f",
        "normalized_bytes": 5279,
        "normalized_sha256": "692547b5193d0c03b3cb5fe86c570fff5ea74149affa6a5c88dac8c5b83eeba1",
        "functions_sha256": "aa22ddb7420446590f002a6ab591b295a8ad1d8e53e3d9b05f636a2a9910f257",
        "whole_sha256": "3d7d6fa34d2842b85624168f1a160a61175cd6951f35bba229846c5e1a3a3512",
        "interface_sha256": "a4493468e515741e459ca8ba83cd165d256bc1c9044e57b60b02f26669afa19d",
        "defines": (),
        "function_count": 14,
        "declaration_count": 7,
        "function_inventory": (
            (40, "chebyshev_gradient", "float",
             ((27, "uv", "vec2"), (28, "base_freq", "vec2"),
              (29, "px", "vec2"), (30, "disp", "float"),
              (31, "s", "float"))),
            (41, "clamp01", "float", ((8, "v", "float"),)),
            (42, "exponential_noise", "float",
             ((32, "uv", "vec2"), (33, "freq", "vec2"), (34, "s", "float"))),
            (43, "fade", "float", ((15, "t", "float"),)),
            (44, "freq_for_shape", "vec2",
             ((9, "freq", "float"), (10, "w", "float"), (11, "h", "float"))),
            (45, "hash21", "float", ((13, "p", "vec2"),)),
            (46, "hash31", "float", ((14, "p", "vec3"),)),
            (47, "main", "void", ()),
            (48, "pcg", "uvec3", ((12, "v", "uvec3"),)),
            (49, "refracted_exponential", "float",
             ((35, "uv", "vec2"), (36, "freq", "vec2"), (37, "px", "vec2"),
              (38, "disp", "float"), (39, "s", "float"))),
            (50, "refracted_field", "float",
             ((22, "uv", "vec2"), (23, "base_freq", "vec2"),
              (24, "px", "vec2"), (25, "disp", "float"),
              (26, "s", "float"))),
            (51, "seed_offset", "vec2", ((18, "s", "float"),)),
            (52, "simple_multires", "float",
             ((19, "uv", "vec2"), (20, "base_freq", "vec2"),
              (21, "s", "float"))),
            (53, "value_noise", "float",
             ((16, "coord", "vec2"), (17, "s", "float"))),
        ),
        "declaration_inventory": (
            (1, "inputTex", "sampler2D", "uniform", False, False, "4:1-4:28"),
            (2, "resolution", "vec2", "uniform", False, False, "5:1-5:25"),
            (3, "fullResolution", "vec2", "uniform", False, False,
             "6:1-6:29"),
            (4, "tileOffset", "vec2", "uniform", False, False, "7:1-7:25"),
            (5, "strength", "float", "uniform", False, False, "8:1-8:24"),
            (6, "seed", "float", "uniform", False, False, "9:1-9:20"),
            (7, "fragColor", "vec4", "output", True, False, "11:1-11:16"),
        ),
        "initializer_census": (),
        "resources": (("inputTex", "resolution", "fullResolution",
                       "tileOffset", "strength", "seed"),
                      ("inputTex",), ("fragColor",), True, False),
        "counted_loop_proof": (1, 0, 1, 8, 120, True),
        "call_edge_count": 22,
        "call_graph_sha256": "b8a0f826c336c9230a1965f8f090571c263eea6f6b9f56dfae6d9f2db108cd2f",
        "reachable": (40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53),
        "unreachable": (),
        "total_nodes": 645,
        "total_assigns": 15,
        "interface_cardinality": 1,
        # symbol id, name, type, storage, writable, THE REAL whole-file span
        # (the normalized source is 169 lines), symbol node hash.
        "varying": (55, "v_texCoord", "vec2", "varying", False,
                    "1:1-169:2",
                    "cba74007ce9c04f6185e65d92420f5c8f807e7ccca08254ab73cf63faadd28ff"),
        "symbol_span": "1:1-169:2",
        # The raw-source declaration site, regex-derived from the caller's
        # raw bytes: file, exact line text, 1-based line number (column 1).
        "raw_declaration": ("filter/grime/grime.glsl",
                            "in vec2 v_texCoord;", 19),
        "reads": (
            VaryingReadRecord(
                symbol_id=55, symbol_name="v_texCoord",
                owner_id=47, owner_name="main",
                span="131:24-131:34", node_type="vec2",
                node_sha256="127c65585965fd72eaf7d9f2b4dbfadefaf396a08fd04d6975b05060f761c342",
                parent_kind="binary", parent_operator="*",
                parent_span="131:24-131:45",
                statement_index=1, statement_kind="decl",
                statement_span="131:5-131:59"),
            VaryingReadRecord(
                symbol_id=55, symbol_name="v_texCoord",
                owner_id=47, owner_name="main",
                span="134:41-134:51", node_type="vec2",
                node_sha256="86e645490e4e492a7baaed51ec143f6312ce1ec50f329969de6a28b1547eb18b",
                parent_kind="builtin", parent_operator=None,
                parent_span="134:23-134:52",
                statement_index=4, statement_kind="decl",
                statement_span="134:5-134:53"),
        ),
        "writes": (),
        "contract": VaryingUvContract(
            symbol_id=55, name="v_texCoord", glsl_type="vec2",
            native_type=_NATIVE_TYPE,
            alias_of=_LOWERING_TARGET, lowering_target=_LOWERING_TARGET,
            kernel_signature_change=_KERNEL_SIGNATURE_CHANGE,
            numeric_contract=_NUMERIC_CONTRACT,
            lane_expressions=_LANE_EXPRESSIONS,
            js_alias_evidence=_JS_ALIAS_EVIDENCE,
            raw_declaration_site="filter/grime/grime.glsl:19:1"),
        # The symbol plus both authenticated read nodes: 3 distinct objects,
        # each consumed exactly once (wobble's default of 2 does not apply).
        "consumed_ledger": 3,
    },
}


def allowed_row_fields(key: str) -> frozenset[str]:
    """The complete set of slice-row fields permitted for ``key``.

    Exhaustive by construction: the validator's allowed-field arm compares
    `set(item) != expected`, so requiring equality with this set is what
    discharges "every other profile absent". Landed keys answer from
    ``ALLOWED_ROW_FIELDS``; prepared keys (grime, whose row lands in a later
    slice together with its float-bit ingress companion) answer from
    ``PREPARED_ROW_FIELDS`` -- the row contract is frozen now, enforced when
    the row lands."""
    fields = ALLOWED_ROW_FIELDS.get(key) or PREPARED_ROW_FIELDS.get(key)
    if fields is None:
        raise _profile_fail(
            WOBBLE_PROFILE,
            f"{key} is not an admitted varying-uv carrier")
    return fields


def varying_uv_contract(key: str) -> VaryingUvContract:
    """The frozen emission contract both authorities must honour for ``key``."""
    lock = _LOCKS.get(key)
    if lock is None:
        raise _profile_fail(
            WOBBLE_PROFILE,
            f"{key} is not an admitted varying-uv carrier")
    return lock["contract"]


def authenticate_varying_uv(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple:
    """Return the exact frozen uv-alias varying symbols of ``program.key``.

    Returns an empty tuple when ``program.key`` is not a carrier, so callers
    can treat the result as a membership set unconditionally; supplying a
    profile for a non-carrier key is a hard failure that names the sole
    landed declaration.

    Membership is the **authenticatable** set -- every frozen record,
    ``PREPARED_KEYS`` included -- not the landed registry: the record is the
    thing under test, and the slice-schema census (``KEYS``) is the
    integration gate's concern, not this function's.

    The admitted symbols are returned by object identity, each consumable
    exactly once by the caller's new arm; the visitation ledger at the bottom
    freezes what authentication itself consumed.
    """
    if program.key not in _LOCKS:
        if profile is not None:
            site = _LOCKS[WOBBLE_KEY]["raw_declaration"]
            raise _profile_fail(
                WOBBLE_PROFILE,
                "program key is not an admitted varying-uv carrier; "
                f"{WOBBLE_KEY} {site[0]}:{site[2]} `{site[1]}` is the sole "
                "landed varying declaration")
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
    if not _node_census_holds(*_node_census(program), lock):
        raise fail("whole-program node census mismatch")
    if not _declaration_inventory_holds(program, lock):
        raise fail("global declaration inventory mismatch")
    if not _initializer_census_holds(program, lock):
        raise fail("global declaration initializer census mismatch")

    if not _interface_cardinality_holds(program, lock):
        raise fail("varying interface census mismatch")
    symbol = program.interface_symbols[0]

    # Value-level locks run AHEAD of the symbol-hash identity: `Symbol`
    # embeds its span, so a name, storage, type or span mutation also shifts
    # the node hash, and a coarser ordering would let the hash absorb the
    # change and make each of these vacuous.
    if not _uv_alias_name_holds(symbol, lock):
        raise fail("varying name is not in the runtime uv alias map")
    if not _varying_storage_holds(symbol, lock):
        raise fail("varying storage mutability or direction mismatch")
    if not _varying_type_holds(symbol, lock):
        raise fail("varying type mismatch")
    if not _symbol_span_holds(symbol, lock):
        raise fail("varying symbol span is not the whole-file span")
    if not _raw_declaration_holds(program, lock):
        raise fail("varying raw-source declaration site mismatch")
    if not _varying_identity_holds(symbol, lock):
        raise fail("varying symbol identity mismatch")
    if not _no_declaration_inventory_entry_holds(program, lock):
        raise fail("varying appears in the global declaration inventory")

    if not _varying_contract_holds(lock["contract"], lock):
        raise fail("varying emission contract mismatch")

    symbols = {symbol.id: symbol.name}
    reads, writes = _reference_census(program, symbols)
    if not _read_census_holds(reads, lock):
        raise fail(f"varying read census mismatch: {len(reads)}")
    if not _write_census_holds(writes, lock):
        raise fail(f"varying write census mismatch: {len(writes)}")

    _check_ledger(
        [symbol, *(item.node for item in reads), *(item.node for item in writes)],
        lock.get("consumed_ledger", _CONSUMED_LEDGER),
        "varying-uv", lock["profile"])
    return (symbol,)


def apply_varying_uv(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree.

    Admission is pure expression lowering on the consumer side; nothing about
    the typed IR changes here, which is exactly why there is no ABI row to
    carry -- the emitter consults the admitted symbols by identity."""
    authenticate_varying_uv(program, source_hash, profile)
    return program
