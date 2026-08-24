"""Exact identity profile for ``filter/parallax:parallax``'s two ``textureLod`` sites.

``filter/parallax:parallax`` is the counted-for bucket's cheapest program
(``counted-for-design.md`` §2.1 / §5, cost rank 1): measured **two rungs
from CLEAN at both authorities** behind only KNOWN mechanisms --

* **rung 1 (mechanism A, the const-global-literal bound shape):** the march
  loop ``for (int i = 1; i <= MARCH_STEPS; i++)`` (normalized ``59:9-71:10``)
  is bounded by the const global ``const int MARCH_STEPS = 32;`` (symbol 8,
  normalized ``13:1-13:28``). The bound proof rides the EXISTING dict-keyed
  module -- a new key in ``loop_proof.py``'s
  ``_SOURCE_GLOBAL_LITERAL_INT_PROFILES`` (the Task-23 shape, carrier
  auto-supplied from the key, row stays minimal). This module does NOT add
  that key; it freezes the complete dict-entry data as
  ``counted_for_seed_contract`` and re-derives the seed-attached tree itself,
  so this record is the integration slice's one-move landing source (the
  prepared record, the live dict key and the row land together).
* **rung 2 (mechanism B, this module's own mechanism):** ``textureLod`` is
  not in the builtin vocabulary (``APPROVED_CAPABILITIES`` stays 44 /
  ``APPROVED_TYPES`` stays 17 -- zero vocabulary growth, the
  ``reflect``/``ceil`` admission pattern), and the validator rejects the
  first of the program's two sites at normalized ``24:26``. The JavaScript
  authority is a measured pure alias -- ``glsl-runtime.js:400``:
  ``textureLod: (surface, coord) => this.#texture(surface, coord)`` -- the
  lod argument is DROPPED and the call is ``texture`` itself (nearest
  sampling), so the admission is an identity arm over the existing
  ``texture`` path with a frozen lod-``0`` literal check and no mip
  machinery. This module is that arm's frontend home: it hands the
  authorities the two exact live call nodes
  (``getHeight 24:26-24:61`` on ``heightMap`` and ``getInput 30:12-30:46``
  on ``inputTex``).

**The alias evidence, frozen as data at record time** (quote-verified
against the pinned snapshot ``$RUN_ROOT/oracle/noisemaker-for-cpu``):

* ``src/csl/glsl-runtime.js:399-400`` -- ``texture`` and ``textureLod`` are
  byte-identical one-liners over ``this.#texture``; the lod parameter is
  not even in the alias's signature.
* ``canonical-kernels.js:16693`` defines ``canonicalFactory98`` (the
  parallax factory); its only two ``textureLod`` call sites, at lines
  ``16714`` (``getHeight``, ``heightMap``) and ``16720`` (``getInput``,
  ``inputTex``), pass literal ``0`` as the lod -- the transpiler's spelling
  of the source's ``0.0``.
* ``canonical-kernels.js:36278`` is the program's sole registration line.
* ``canonical-kernels.js`` SHA-256
  ``66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe`` --
  byte-identical to the pin the cellRefract/kaleido/effects oracles froze.

**The lowering contract:** ``textureLod(sampler, coord, lod) ==
texture(sampler, coord)`` -- the existing texture path, unchanged; the lod
argument is admitted only as the exact float literal ``0.0`` at the two
frozen sites. A nonzero-lod mutant is INVARIANT on the JS side (the alias
ignores lod), so it is recorded as an invariance witness, not budgeted as
a discriminating oracle case -- the alias IS the contract.

**This module is LANDED** (the ``mutable_global_array`` landed/prepared
split's one-line move): ``KEYS`` carries the parallax key, the row landed as
typed row 190 together with the loop-proof dict key and the two authority
arms in ``generate_typed_slice.py`` / ``emit_typed_cpp.py``.
``allowed_row_fields`` answers from ``ALLOWED_ROW_FIELDS``: the row contract
frozen while PREPARED, enforced now that the row has landed.

Three census conventions were re-derived against the live tree and DIVERGE
from the design's prose (recorded so nobody "fixes" them back):

* the design's "165 nodes" counts function bodies only; the house census
  (global declaration initializers included -- the standing blind-spot
  trap) freezes **167** (the two const-global literal initializers are the
  difference);
* the design's "call edges 4" counts call NODES (``main`` calls
  ``getHeight`` twice); the deduplicated sorted edge SET frozen here has
  **3** edges;
* the design's "read at 58:26" cites the enclosing initializer span; the
  ``MARCH_STEPS`` id node itself is ``58:38-58:49`` (bound read
  ``59:30-59:41``), which is what the ``reads`` lock freezes.

Claim boundary: ``heightMap``'s second-sampler path is fully reachable and
no defines strip code (``defines == ()``), so there are no write-only or
unreachable caveats -- the whole program is oracle-coverable, exactly as
the design's §7 note states.
"""

from __future__ import annotations

import hashlib
import re
from typing import NamedTuple

from .loop_proof import (SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
                         attach_counted_loop_proofs,
                         clear_counted_loop_proofs,
                         summarize_counted_loop_proofs)
from .typed_ir import (TypedExpression, TypedFunction, TypedProgram,
                       TypedStatement)


PARALLAX_KEY = "filter/parallax:parallax"
PARALLAX_PROFILE = "texture-lod-admission-parallax-v1"

# The LANDED carrier registry -- the integration slice (typed row 190) moved
# the prepared key here together with its row, the loop-proof dict key and the
# two authority arms (the mutable_global_array landed/prepared split's
# one-line move; a key must not be registered before its row lands).
KEYS: tuple[str, ...] = (PARALLAX_KEY,)
PROFILES = {PARALLAX_KEY: PARALLAX_PROFILE}
TEXTURE_LOD_ADMISSION_KEYS = frozenset(KEYS)

# Records frozen and authenticatable NOW whose rows land in a later slice.
# Empty after parallax's integration; kept for the next prepared key.
PREPARED_KEYS: tuple[str, ...] = ()

# The complete allowed field set for the slice row -- an ALLOWLIST, not a
# denylist, exhaustive by construction against the validator's
# `set(item) != expected` comparison. The loop-proof dict key needs no row
# field of its own (carrier auto-supplied from the key), so the row carries
# only this module's profile beside the base fields.
ALLOWED_ROW_FIELDS: dict[str, frozenset[str]] = {
    PARALLAX_KEY: frozenset({
        "defines",
        "program_key",
        "texture_lod_admission_profile",
    }),
}
PREPARED_ROW_FIELDS: dict[str, frozenset[str]] = {}

# --- frozen JavaScript provenance (see the module docstring) -----------------

JS_TEXTURE_LOD_ALIAS_LINE = (
    "textureLod: (surface, coord) => this.#texture(surface, coord)")
JS_ALIAS_SITE = "src/csl/glsl-runtime.js:400"
JS_TEXTURE_LINE = "texture: (surface, coord) => this.#texture(surface, coord)"
JS_TEXTURE_SITE = "src/csl/glsl-runtime.js:399"
JS_FACTORY = ("canonicalFactory98", 16693)
JS_LOD_LITERAL_LINES = (16714, 16720)
JS_REGISTRATION_LINE = 36278
JS_CANONICAL_KERNELS_SHA256 = (
    "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe")
# The measured lowering contract both authorities must honour.
LOWERING_CONTRACT = (
    "textureLod(sampler, coord, lod) == texture(sampler, coord)",
)
# The design §7 mutant discipline: the JS alias drops lod, so a nonzero-lod
# mutant is invariant on the JS side -- an invariance witness, never a
# discriminating oracle case.
JS_LOD_INVARIANT_NOTE = (
    "lod is dropped by the alias: a nonzero-lod mutant is JS-invariant "
    "(invariance witness, not a discriminating case)")

# The dict-entry capability the seed contract rides (loop_proof's own).
SEED_CAPABILITY = SOURCE_GLOBAL_LITERAL_INT_CAPABILITY

# Every optional `fixed_*_proof` field a TypedProgram carries. parallax
# carries none, and the frozen-absent set is the whole dataclass enumeration;
# the test suite re-derives it, so a new proof field added elsewhere in the
# tree turns red here rather than slipping through.
_OPTIONAL_PROOF_FIELDS = (
    "fixed_affine_centers13_proof",
    "fixed_array_in_parameter_proof",
    "fixed_grid_counter_store_proof",
    "fixed_nine_table_proof",
)

# The lod literal the alias freezes: exact float value and exact source text.
_LOD_VALUE = 0.0
_LOD_TEXT = "0.0"
_SEED_LITERAL_PATTERN = re.compile(r"[1-9][0-9]*")

# Every IR shape that mutates a writable lvalue. `post` is a distinct kind
# from `unary`, not an operator variant of it.
_MUTATION_KINDS = ("assign", "unary", "post")
_INCREMENT_OPERATORS = ("++", "--")
_BITWISE_OPERATORS = ("&", "|", "^", "<<", ">>")

# The two sites' four live nodes each, the two owner functions, the two
# sampler Symbols and the seed's Symbol: 13 distinct objects, each consumed
# exactly once.
_CONSUMED_LEDGER = 13

__all__ = (
    "KEYS", "PROFILES", "TEXTURE_LOD_ADMISSION_KEYS", "PREPARED_KEYS",
    "PARALLAX_KEY", "PARALLAX_PROFILE", "SEED_CAPABILITY",
    "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS", "allowed_row_fields",
    "CountedForSeedContract", "counted_for_seed_contract",
    "TextureLodSiteProof", "TextureLodAdmissionProof",
    "authenticate_texture_lod_admission", "apply_texture_lod_admission",
    "JS_TEXTURE_LOD_ALIAS_LINE", "JS_ALIAS_SITE", "JS_TEXTURE_LINE",
    "JS_TEXTURE_SITE", "JS_FACTORY", "JS_LOD_LITERAL_LINES",
    "JS_REGISTRATION_LINE", "JS_CANONICAL_KERNELS_SHA256",
    "LOWERING_CONTRACT", "JS_LOD_INVARIANT_NOTE",
)


class CountedForSeedContract(NamedTuple):
    """The complete mechanism-A dict entry for the integration slice.

    Field-for-field a ``_SOURCE_GLOBAL_LITERAL_INT_PROFILES`` entry: patching
    ``_asdict()`` into that dict and passing the capability through
    ``analyze_program`` closes rung 1 (verified against the live tree; the
    next rejection is then ``24:26: unsupported builtin textureLod``).
    """

    raw: str
    source: str
    defines: tuple
    integer: tuple
    globals: tuple
    reads: tuple
    pre_functions: str
    post_functions: str
    pre_whole: str
    post_whole: str
    interface: str


class TextureLodSiteProof(NamedTuple):
    """One admitted ``textureLod`` call, by live node identity."""

    record: tuple
    node: TypedExpression
    sampler: TypedExpression
    coord: TypedExpression
    lod: TypedExpression
    owner: TypedFunction

    @property
    def owner_id(self) -> int:
        return self.record[0]

    @property
    def owner_name(self) -> str:
        return self.record[1]

    @property
    def span(self) -> str:
        return self.record[2]

    @property
    def sampler_symbol_id(self) -> int | None:
        return self.record[3]


class TextureLodAdmissionProof(NamedTuple):
    """The two exact live call nodes, plus the visitation ledger."""

    sites: tuple[TextureLodSiteProof, ...]
    consumed_objects: tuple[object, ...]


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole_cleared(program: TypedProgram) -> str:
    """The whole-program fingerprint over the proof-cleared tree.

    Mirrors ``loop_proof._whole_program_identity`` with the cleared
    functions and the cleared summary, so attaching the seed never moves a
    coarse field: the coarse gate is deliberately proof-insensitive.
    """
    cleared = clear_counted_loop_proofs(program.functions)
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        cleared, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        summarize_counted_loop_proofs(cleared), program.preprocessor_defines,
    ))


def _interface(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _profile_fail(profile: str, message: str) -> ValueError:
    """Prefix every failure with the per-key profile name."""
    return ValueError(f"{profile}: {message}")


def _check_ledger(entries: list, expected: int, label: str,
                  profile: str) -> None:
    """Require ``entries`` to hold exactly ``expected`` distinct objects."""
    identities = [id(item) for item in entries]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _profile_fail(profile,
                            f"{label} visitation ledger mismatch")


# --- walkers ----------------------------------------------------------------
#
# Every walker here descends `program.declarations` as well as
# `function.body`: a whole-program census that only walks bodies leaves
# global declaration initializers in a coarse-hash-only blind spot, and for
# this program the initializer census is exactly the two const-global
# literal nodes.

def _walk_with_parent(value: TypedExpression,
                      parent: TypedExpression | None):
    yield value, parent
    for child in value.children:
        yield from _walk_with_parent(child, value)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_with_parent(expression, None)
    for child in value.children:
        yield from _walk_statement(child)


def _program_nodes(program: TypedProgram):
    """``(function, node, parent)`` for every expression node in the
    program, global declaration initializers included (``function`` is
    ``None`` there)."""
    for declaration in program.declarations:
        if declaration.initializer is None:
            continue
        for node, parent in _walk_with_parent(declaration.initializer, None):
            yield None, node, parent
    for function in program.functions:
        for statement in function.body:
            for node, parent in _walk_statement(statement):
                yield function, node, parent


def _node_census(program: TypedProgram) -> tuple[int, int]:
    total = 0
    assigns = 0
    for _, node, _ in _program_nodes(program):
        total += 1
        if node.kind == "assign":
            assigns += 1
    return total, assigns


def _call_graph(program: TypedProgram) -> tuple:
    edges = set()
    for function, node, _ in _program_nodes(program):
        if (function is not None and node.kind == "call"
                and node.signature_id is not None):
            edges.add((function.id, function.name, node.signature_id,
                       node.callee))
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


def _owner_record(function: TypedFunction | None) -> tuple[int, str]:
    if function is None:
        return (-1, "<global-initializer>")
    return (function.id, function.name)


def _builtin_census(program: TypedProgram, callee: str) -> tuple:
    found = []
    for function, node, _ in _program_nodes(program):
        if node.kind == "builtin" and node.callee == callee:
            owner_id, owner_name = _owner_record(function)
            found.append((owner_id, owner_name, _span(node),
                          len(node.children)))
    return tuple(found)


def _texture_size_census(program: TypedProgram) -> tuple:
    return _builtin_census(program, "textureSize")


def _plain_texture_and_fetch_census(program: TypedProgram) -> tuple:
    return (tuple(sorted(_builtin_census(program, "texture")
                         + _builtin_census(program, "texelFetch"))))


def _mechanism_census(program: TypedProgram) -> tuple[int, int, int, int]:
    """(out/inout parameters, bare void-call statements, bit-ops, index
    expressions) -- parallax's 'no secondary mechanisms at all' fact."""
    out_parameters = sum(1 for function in program.functions
                         for parameter in function.parameters
                         if parameter.direction != "in")
    bit_operations = 0
    index_expressions = 0
    for _, node, _ in _program_nodes(program):
        if node.kind == "binary" and node.operator in _BITWISE_OPERATORS:
            bit_operations += 1
        if node.kind == "index":
            index_expressions += 1
    bare_void_calls = 0

    def statement_count(value: TypedStatement) -> None:
        nonlocal bare_void_calls
        if (value.kind == "expr" and len(value.expressions) == 1
                and value.expressions[0].kind == "call"
                and value.expressions[0].type.display() == "void"):
            bare_void_calls += 1
        for child in value.children:
            statement_count(child)

    for function in program.functions:
        for item in function.body:
            statement_count(item)
    return (out_parameters, bare_void_calls, bit_operations,
            index_expressions)


def _seed_symbol(program: TypedProgram, lock: dict):
    for declaration in program.declarations:
        if declaration.symbol.id == lock["seed"]["symbol_id"]:
            return declaration.symbol
    return None


def _frozen_seed(program: TypedProgram, lock: dict):
    """The mechanism-A seed tuple exactly as the authorities will attach it:
    the FROZEN bound value with the live symbol object."""
    return ((lock["seed"]["symbol_id"], lock["seed"]["value"],
             "source-global-const-literal", _seed_symbol(program, lock)),)


def _site_proofs(program: TypedProgram) -> list[TextureLodSiteProof]:
    """Every live ``textureLod`` call node in the program, initializers
    included, with its owner, its three children and its full record."""
    sites: list[TextureLodSiteProof] = []
    for function, node, _ in _program_nodes(program):
        if (node.kind != "builtin" or node.callee != "textureLod"
                or len(node.children) != 3):
            continue
        sampler, coord, lod = node.children
        owner_id, owner_name = _owner_record(function)
        record = (owner_id, owner_name, _span(node), sampler.symbol_id,
                  _span(sampler), _span(coord), _span(lod),
                  (_sha(node), _sha(sampler), _sha(coord), _sha(lod)))
        sites.append(TextureLodSiteProof(
            record, node, sampler, coord, lod, function))
    return sites


def _derive_site_records(program: TypedProgram) -> tuple:
    return tuple(site.record for site in _site_proofs(program))


def _resite(program: TypedProgram,
            sampler_remap: dict[int, int]) -> dict[str, tuple]:
    """Re-derive the ``lod_sites`` records' semantic columns from ``program``
    -- the site spans, owners and sampler ids the mutation moved -- while the
    identity hash tuples keep their frozen originals, and remap each
    recorded sampler id through ``sampler_remap``.

    The lock-under-test companion for the site-value mutation tests: it
    refreezes only what the mutation legitimately moved (the SITES), never
    the identity hashes, so the identity lock keeps its teeth while a
    deliberately remapped sampler column guarantees the identity record can
    still catch a mutant whose site columns are re-frozen.
    """
    frozen = _LOCKS[PARALLAX_KEY]["lod_sites"]
    records = []
    for index, record in enumerate(_derive_site_records(program)):
        owner_id, owner_name, span, sampler_id, sampler_span, coord_span, \
            lod_span, _ = record
        records.append((
            owner_id, owner_name, span,
            sampler_remap.get(sampler_id, sampler_id),
            sampler_span, coord_span, lod_span, frozen[index][-1]))
    return {"lod_sites": tuple(records)}


def _number(value: TypedExpression) -> float | None:
    """A float literal, or the unary minus of one -- nothing else (the
    ``fixed_array_in_parameter_proof._number`` extraction)."""
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


def _base_symbol(node: TypedExpression) -> TypedExpression:
    current = node
    while current.kind in ("swizzle", "member", "index") and current.children:
        current = current.children[0]
    return current


def _function_inventory(program: TypedProgram) -> tuple:
    return tuple(
        (item.id, item.name, item.return_type.display(),
         tuple((parameter.id, parameter.name, parameter.type.display())
               for parameter in item.parameters))
        for item in program.functions)


def _binding_table(program: TypedProgram) -> tuple:
    """All declarations, order-insensitive: an added or removed global
    anywhere is a hard failure here. Initializers appear only as a presence
    bool -- their literal VALUES are the globals-census lock's, and their
    SPANS are the coarse whole/interface fingerprints' -- so neither a value
    mutation nor a length-changing literal can hide behind this inventory
    (a shorter literal shifts the declaration span, which must not redden
    this lock before the value lock that names it)."""
    return tuple(sorted(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable,
         item.initializer is not None)
        for item in program.declarations))


# --- individually deletable locks -------------------------------------------
#
# Each predicate below is exactly one lock with exactly one message. A test
# proves a lock load-bearing by re-executing this module into a scratch
# namespace, replacing one of these functions with an always-true stand-in,
# and showing that the lock's message disappears. Keep them small,
# single-purpose and side-effect free.
#
# Ordering matters. `Symbol` embeds its declaration span, so every value-level
# lock (the seed declaration's shape and value, the site shapes, the lod
# literal pair) is evaluated AHEAD of the node-hash identity locks that would
# otherwise absorb them and make them vacuous; the coarse gate runs ahead of
# everything semantic; and the program-shape locks (binding table, inventory,
# call graph) run ahead of the mechanism locks so each mutation dies at the
# lock that names it.

def _caller_source_hash_holds(source_hash: str | None, lock: dict) -> bool:
    """The caller's own view of the source agrees with the frozen record."""
    return source_hash == lock["raw_sha256"]


def _defines_hold(program: TypedProgram, lock: dict) -> bool:
    """Exactly no preprocessor defines -- the whole-program contract."""
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
    return _sha(clear_counted_loop_proofs(program.functions)) == \
        lock["functions_sha256"]


def _whole_program_fingerprint_holds(program: TypedProgram,
                                     lock: dict) -> bool:
    return _whole_cleared(program) == lock["whole_sha256"]


def _interface_fingerprint_holds(program: TypedProgram, lock: dict) -> bool:
    return _interface(program) == lock["interface_sha256"]


def _unrelated_proof_absent_holds(program: TypedProgram) -> bool:
    """Every sibling optional proof is absent -- parallax carries none."""
    return all(getattr(program, field, None) is None
               for field in _OPTIONAL_PROOF_FIELDS)


def _call_graph_holds(program: TypedProgram, lock: dict) -> bool:
    """The exact deduplicated call-graph edge set, its digest, and full
    reachability. Deliberately does NOT fold the counted-loop summary in
    (that is the closure lock's own message) and does not count call NODES
    (`main` calls `getHeight` twice; the deduplicated SET has three edges)."""
    edges = _call_graph(program)
    reachable, unreachable = _reachability(program)
    return (len(edges) == lock["call_edge_count"]
            and _sha(edges) == lock["call_graph_sha256"]
            and reachable == lock["reachable"]
            and unreachable == lock["unreachable"])


def _counted_summary_holds(program: TypedProgram, lock: dict) -> bool:
    """The seed-attached whole-program counted-for summary: one loop, proved,
    depth 1, product 32, charge 32, acyclic. A pre-seed tree dies here."""
    proof = program.counted_loop_proof
    if proof is None:
        return False
    return (proof.loop_count, proof.unproved_loop_count,
            proof.max_effective_depth, proof.max_lexical_product,
            proof.entrypoint_charge, proof.call_graph_acyclic) == \
        lock["counted_loop_proof"]


def _function_cardinality_holds(program: TypedProgram, lock: dict) -> bool:
    return len(program.functions) == lock["function_count"]


def _function_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    """All four functions by id, name, return type and parameters."""
    return _function_inventory(program) == lock["function_inventory"]


def _resources_hold(program: TypedProgram, lock: dict) -> bool:
    """Two samplers, four scalar/vector uniforms, one output, texture reads,
    no derivatives."""
    resources = program.resources
    return ((resources.uniforms, resources.samplers, resources.outputs,
             resources.uses_texture, resources.uses_derivatives)
            == lock["resources"])


def _binding_table_holds(program: TypedProgram, lock: dict) -> bool:
    return (len(program.declarations) == lock["declaration_count"]
            and _binding_table(program) == lock["binding_table"])


def _counted_rebuild_holds(program: TypedProgram, lock: dict) -> bool:
    """The submitted proof tree equals the tree rebuilt from the frozen seed:
    attach the frozen bound onto the submitted proof-cleared functions and
    require the exact submitted functions (and summary) back. A tree that
    merely CLAIMS the closed summary dies here."""
    rebuilt = attach_counted_loop_proofs(
        program.functions, program.key,
        source_global_bounds=_frozen_seed(program, lock))
    return (program.functions == rebuilt
            and program.counted_loop_proof
            == summarize_counted_loop_proofs(rebuilt))


def _seed_declaration_holds(program: TypedProgram, lock: dict) -> bool:
    """The bound global is a bare positive int-literal const named
    MARCH_STEPS with value 32 -- the Task-23 declaration checks, evaluated on
    the live declaration ahead of the identity hashes."""
    expected = lock["seed"]
    declaration = next((item for item in program.declarations
                        if item.symbol.id == expected["symbol_id"]), None)
    if declaration is None:
        return False
    symbol = declaration.symbol
    initializer = declaration.initializer
    return (symbol.name == expected["name"]
            and symbol.storage == "const" and symbol.writable is False
            and symbol.direction == "in"
            and declaration.type.display() == "int"
            and initializer is not None
            and initializer.kind == "literal"
            and initializer.type.display() == "int"
            and initializer.category == "rvalue"
            and not initializer.children
            and initializer.literal == expected["literal"]
            and initializer.literal_value == expected["value"]
            and _SEED_LITERAL_PATTERN.fullmatch(
                initializer.literal if initializer.literal else "") is not None)


def _seed_identity_holds(program: TypedProgram, lock: dict) -> bool:
    """The seed declaration's span and both node hashes."""
    expected = lock["seed"]
    declaration = next((item for item in program.declarations
                        if item.symbol.id == expected["symbol_id"]), None)
    if declaration is None:
        return False
    return (_span(declaration), _sha(declaration), _sha(declaration.symbol)) \
        == (expected["span"], expected["declaration_sha256"],
            expected["symbol_sha256"])


def _globals_census_holds(program: TypedProgram, lock: dict) -> bool:
    """Both source globals with their literal texts -- the same census
    `authenticate_source_global_literal_int` freezes in the dict entry."""
    return tuple(
        (item.symbol.name, item.symbol.id, item.type.display(),
         item.initializer.literal if item.initializer is not None else None)
        for item in program.declarations
        if item.symbol.storage not in {"uniform", "output"}) == \
        lock["globals"]


def _no_seed_write_holds(program: TypedProgram,
                         seed_ids: set[int]) -> bool:
    """The seed const is never a mutation target anywhere, and its id nodes
    never appear outside `main` (both frozen reads live in `main`; global
    declaration initializers are walked too, so a reference planted in one
    is refused here as well)."""
    for function, node, _ in _program_nodes(program):
        if node.kind == "id" and node.symbol_id in seed_ids:
            if function is None or function.name != "main":
                return False
        if node.kind not in _MUTATION_KINDS or not node.children:
            continue
        if node.kind != "assign" and node.operator not in (
                _INCREMENT_OPERATORS):
            continue
        if _base_symbol(node.children[0]).symbol_id in seed_ids:
            return False
    return True


def _seed_reads_holds(program: TypedProgram, lock: dict) -> bool:
    """Exactly the two frozen id-node reads: `float(MARCH_STEPS)` at
    58:38-58:49 and the loop bound at 59:30-59:41."""
    identifier = lock["seed"]["symbol_id"]
    reads = []
    for function, node, _ in _program_nodes(program):
        if node.kind != "id" or node.symbol_id != identifier:
            continue
        owner_id, owner_name = _owner_record(function)
        span = node.span
        reads.append((owner_name, owner_id,
                      span.start_line, span.start_column,
                      span.end_line, span.end_column))
    return tuple(reads) == lock["reads"]


def _march_loop_holds(program: TypedProgram, lock: dict) -> bool:
    """The one loop's complete proof shape at its frozen span in `main`."""
    expected = lock["march_loop"]
    mains = [item for item in program.functions
             if item.id == expected["owner"][0]
             and item.name == expected["owner"][1]]
    if len(mains) != 1:
        return False

    def find_for(statements):
        for statement in statements:
            if statement.kind == "for":
                yield statement
            yield from find_for(statement.children)

    for statement in find_for(mains[0].body):
        if _span(statement) != expected["span"]:
            continue
        proof = statement.loop_proof
        return (proof is not None
                and proof.induction_symbol_id == expected["induction_symbol_id"]
                and proof.start_value == expected["start"]
                and proof.bound_value == expected["bound"]
                and proof.comparison == expected["comparison"]
                and proof.update == expected["update"]
                and proof.bound_kind == expected["bound_kind"]
                and proof.trip_count == expected["trips"]
                and proof.lexical_depth == expected["depth"]
                and proof.lexical_product == expected["product"]
                and proof.entrypoint_charge == expected["charge"])
    return False


def _texture_lod_census_holds(sites: list, lock: dict) -> bool:
    """Exactly two textureLod call nodes -- walked over global declaration
    initializers too, which is what proves no third site can hide in one.
    Cardinality only: the spans are the shape and identity locks' (a
    length-changing mutation may legitimately move them, and must die at
    the lock that names the moved thing, not here)."""
    return len(sites) == lock["lod_site_count"]


def _lod_shape_holds(sites: list, lock: dict) -> bool:
    """Both sites' structural shape -- owner, span, sampler symbol,
    coord/lod kinds and types -- plus the two lod-literal sub-clauses. The
    sub-clause pair is the discipline: the VALUE clause extracts
    literal-or-unary-minus and the TEXT clause compares the literal string,
    so deleting either one alone leaves the other to catch a nonzero lod."""
    shape = tuple(
        (site.owner_id, site.owner_name, site.sampler_symbol_id,
         site.coord.kind, site.coord.type.display(),
         site.lod.kind, site.lod.type.display(), site.span)
        for site in sites)
    return (shape == lock["lod_shape"]
            and _lod_value_holds(sites, lock)
            and _lod_text_holds(sites, lock))


def _lod_value_holds(sites: list, lock: dict) -> bool:
    return all(_number(site.lod) == _LOD_VALUE for site in sites)


def _lod_text_holds(sites: list, lock: dict) -> bool:
    return all(site.lod.literal == _LOD_TEXT for site in sites)


def _lod_identity_holds(sites: list, lock: dict) -> bool:
    """Both sites' full records: owner, spans, sampler symbol id and the
    four per-site node hashes (call, sampler, coord, lod)."""
    return tuple(site.record for site in sites) == lock["lod_sites"]


def _texture_family_census_holds(program: TypedProgram, lock: dict) -> bool:
    """The alias boundary: zero plain `texture` and zero `texelFetch` sites,
    and exactly the two frozen `textureSize` sites -- the program's only
    sampling sites are the two textureLod nodes the identity arm admits."""
    return (_plain_texture_and_fetch_census(program)
            == lock["plain_texture_and_fetch"]
            and _texture_size_census(program) == lock["texture_size_sites"])


def _mechanism_census_holds(program: TypedProgram, lock: dict) -> bool:
    return _mechanism_census(program) == lock["mechanism_census"]


def _node_census_holds(total: int, assigns: int, lock: dict) -> bool:
    return total == lock["total_nodes"] and assigns == lock["total_assigns"]


def _main_body_holds(main: TypedFunction, lock: dict) -> bool:
    identifier, name, length, span = lock["main"]
    return (main.id == identifier and main.name == name
            and len(main.body) == length and _span(main) == span
            and tuple((item.kind, _span(item)) for item in main.body)
            == lock["main_body"])


# --- frozen per-key record ---------------------------------------------------

_LOCKS = {
    PARALLAX_KEY: {
        "profile": PARALLAX_PROFILE,
        "source_path": "sources/filter/parallax/parallax.glsl",
        "raw_bytes": 2430,
        "raw_sha256":
            "5ce5dce2ec8e8d7ebd3024c6a5bd5dcb068d0cf322bfd105c4fb3546e1b97642",
        "normalized_bytes": 1902,
        "normalized_sha256":
            "281c8163d7f5fd47dc2ebd258003b04e1d41f7687c52e3c99e5aa56c911bd5f0",
        "functions_sha256":
            "39bfbb083f4383209661da6248eecff353f3f1ff7257c828bc1ce62bcf821808",
        "whole_sha256":
            "920fe71bb122690f2169d2ee27ab6a4f908a18bf55b6031cb44fe51ba50c5eff",
        "interface_sha256":
            "9ff15dc1fd4f97bd0d392bd40d1cab39a4c1fcb988c2d79d595f933235d39314",
        "defines": (),
        "function_count": 4,
        "function_inventory": (
            (13, "getHeight", "float", ((11, "uv", "vec2"),)),
            (14, "getInput", "vec4", ((12, "uv", "vec2"),)),
            (15, "getLuminosity", "float", ((10, "color", "vec3"),)),
            (16, "main", "void", ()),
        ),
        "resources": (
            ("inputTex", "heightMap", "tileOffset", "fullResolution",
             "direction", "pivot"),
            ("inputTex", "heightMap"),
            ("fragColor",),
            True,
            False,
        ),
        "call_edge_count": 3,
        "call_graph_sha256":
            "f75576e0e8e157b0f48f3a22da5f6a525e841eedf68600a53ccb08b8322d66b7",
        "reachable": (13, 14, 15, 16),
        "unreachable": (),
        "counted_loop_proof": (1, 0, 1, 32, 32, True),
        # The seed contract's post-attachment figures (loop_proof's own
        # formulas over the seed-attached tree -- see
        # counted_for_seed_contract).
        "seed_post_functions":
            "7b13f5ae2cd5f75f179c601d57d5ea818919841a700c3400d3ccb40f8ab4b9d0",
        "seed_post_whole":
            "30e996fec218dfd0c92f0f706d1cde5b0da84b25421fedf6d9f08479421d8a16",
        "declaration_count": 9,
        "binding_table": (
            (1, "inputTex", "sampler2D", "uniform", False, False),
            (2, "heightMap", "sampler2D", "uniform", False, False),
            (3, "tileOffset", "vec2", "uniform", False, False),
            (4, "fullResolution", "vec2", "uniform", False, False),
            (5, "direction", "vec3", "uniform", False, False),
            (6, "pivot", "float", "uniform", False, False),
            (7, "fragColor", "vec4", "output", True, False),
            (8, "MARCH_STEPS", "int", "const", False, True),
            (9, "SHIFT_SCALE", "float", "const", False, True),
        ),
        "seed": {
            "symbol_id": 8,
            "name": "MARCH_STEPS",
            "value": 32,
            "literal": "32",
            "span": "13:1-13:28",
            "declaration_sha256":
                "eba95160978f03b429b85136e04f59079f3650a9484c57afd088e9d776e422d4",
            "symbol_sha256":
                "ee344bcaa77cb0c1b9056f1c0be04fb7addc6725fccaa3978cdfedc59ef97f61",
        },
        "globals": (("MARCH_STEPS", 8, "int", "32"),
                    ("SHIFT_SCALE", 9, "float", "0.15")),
        "reads": (("main", 16, 58, 38, 58, 49),
                  ("main", 16, 59, 30, 59, 41)),
        "march_loop": {
            "owner": (16, "main"),
            "span": "59:9-71:10",
            "induction_symbol_id": 33,
            "start": 1,
            "bound": 32,
            "comparison": "<=",
            "update": "++",
            "bound_kind": "source-global-const-literal",
            "trips": 32,
            "depth": 1,
            "product": 32,
            "charge": 32,
        },
        "lod_site_count": 2,
        "lod_shape": (
            (13, "getHeight", 2, "id", "vec2", "literal", "float",
             "24:26-24:61"),
            (14, "getInput", 1, "id", "vec2", "literal", "float",
             "30:12-30:46"),
        ),
        "lod_sites": (
            (13, "getHeight", "24:26-24:61", 2, "24:37-24:46",
             "24:48-24:55", "24:57-24:60",
             ("0f0caec7d7133119df6d4d6542569d4d4effcdd3f83162528c8374e498bfcecc",
              "a0c8bd0b22c7837c79658c7c385fbdbbb2e1d82cd00d856f093622c391fa2901",
              "38c6517e532ba65c4672106544d739860f221c6a657bc13d64e86eaf8fc8259d",
              "e09fb37fe5fc236e3e2121376b34c483689479ac6b182bc9528f85a0eb61a105")),
            (14, "getInput", "30:12-30:46", 1, "30:23-30:31",
             "30:33-30:40", "30:42-30:45",
             ("4837c637f01130eff654d12caa027538c19a35901235d6b56a31f50f939fb706",
              "53fe8cf58b89ec4d55f268b92dcc109417f1139eefd1547dccd3babbbe9520da",
              "7bcd7dbd6b2a11ffbc62299d1b5bbe50b655f160fd1e20fe2cac5fa0664c693b",
              "ce6b37b218c0f73d4e1c8f98644de683b9d090595d85ee291a197439efc759b4")),
        ),
        "texture_size_sites": (
            (13, "getHeight", "22:25-22:50", 2),
            (14, "getInput", "28:25-28:49", 2),
        ),
        "plain_texture_and_fetch": (),
        "mechanism_census": (0, 0, 0, 0),
        "main": (16, "main", 11, "33:1-75:2"),
        "main_body": (
            ("decl", "34:5-34:53"),
            ("decl", "35:5-35:44"),
            ("decl", "37:5-37:83"),
            ("decl", "38:5-38:37"),
            ("decl", "43:5-43:53"),
            ("if", "44:5-50:6"),
            ("decl", "53:5-53:19"),
            ("decl", "54:5-54:45"),
            ("decl", "55:5-55:36"),
            ("if", "57:5-72:6"),
            ("expr", "74:5-74:33"),
        ),
        "total_nodes": 167,
        "total_assigns": 6,
    },
}


def _authenticatable_keys() -> frozenset[str]:
    """Membership is the authenticatable set -- every frozen record,
    ``PREPARED_KEYS`` included -- not the landed registry."""
    return frozenset(_LOCKS)


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
            PARALLAX_PROFILE,
            f"{key} is not an admitted textureLod admission carrier")
    return fields


def counted_for_seed_contract(key: str) -> CountedForSeedContract:
    """The complete mechanism-A dict entry for ``key`` -- field-for-field a
    ``loop_proof._SOURCE_GLOBAL_LITERAL_INT_PROFILES`` entry, the
    integration slice's one-move landing source for the bound-proof key."""
    lock = _LOCKS.get(key)
    if lock is None:
        raise _profile_fail(
            PARALLAX_PROFILE,
            f"{key} is not an admitted textureLod admission carrier")
    return CountedForSeedContract(
        raw=lock["raw_sha256"],
        source=lock["normalized_sha256"],
        defines=lock["defines"],
        integer=(lock["seed"]["name"], lock["seed"]["symbol_id"],
                 lock["seed"]["literal"], lock["seed"]["value"]),
        globals=lock["globals"],
        reads=lock["reads"],
        pre_functions=lock["functions_sha256"],
        post_functions=lock["seed_post_functions"],
        pre_whole=lock["whole_sha256"],
        post_whole=lock["seed_post_whole"],
        interface=lock["interface_sha256"],
    )


def authenticate_texture_lod_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TextureLodAdmissionProof | None:
    """Authenticate the frozen textureLod identity profile and return the
    two exact live call nodes for ``program.key``.

    Returns ``None`` when ``program.key`` is not a carrier and no profile
    was supplied, so callers can treat the result as optional
    unconditionally; supplying a profile for a non-carrier key is a hard
    failure that names the sole admitted sites.
    """
    if program.key not in _LOCKS:
        if profile is not None:
            raise _profile_fail(
                PARALLAX_PROFILE,
                "program key is not an admitted textureLod admission "
                "carrier; "
                f"{PARALLAX_KEY} 24:26 and 30:12 are the sole admitted "
                "textureLod sites")
        return None
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
    if not _call_graph_holds(program, lock):
        raise fail("call graph or reachability profile mismatch")
    if not _counted_summary_holds(program, lock):
        raise fail("counted-for closure summary mismatch")
    if not _function_cardinality_holds(program, lock):
        raise fail("function cardinality mismatch")
    if not _function_inventory_holds(program, lock):
        raise fail("typed function inventory mismatch")
    if not _resources_hold(program, lock):
        raise fail("resource profile mismatch")
    if not _binding_table_holds(program, lock):
        raise fail("binding table mismatch")
    if not _counted_rebuild_holds(program, lock):
        raise fail(
            "counted-for proof tree does not match the seed-derived rebuild")
    if not _seed_declaration_holds(program, lock):
        raise fail("counted-for bound seed declaration value profile mismatch")
    if not _seed_identity_holds(program, lock):
        raise fail("counted-for bound seed declaration identity mismatch")
    if not _globals_census_holds(program, lock):
        raise fail("source global census mismatch")
    seed_ids = {lock["seed"]["symbol_id"]}
    if not _no_seed_write_holds(program, seed_ids):
        raise fail("counted-for bound seed write census mismatch")
    if not _seed_reads_holds(program, lock):
        raise fail("counted-for bound seed read census mismatch")
    if not _march_loop_holds(program, lock):
        raise fail("counted-for march loop profile mismatch")

    sites = _site_proofs(program)

    if not _texture_lod_census_holds(sites, lock):
        raise fail("textureLod site census mismatch")
    if not _lod_shape_holds(sites, lock):
        raise fail("textureLod site shape mismatch")
    if not _lod_identity_holds(sites, lock):
        raise fail("textureLod site identity mismatch")
    if not _texture_family_census_holds(program, lock):
        raise fail("texture-family census mismatch")
    if not _mechanism_census_holds(program, lock):
        raise fail("mechanism census mismatch")
    total, assigns = _node_census(program)
    if not _node_census_holds(total, assigns, lock):
        raise fail("whole-program node census mismatch")
    mains = [item for item in program.functions
             if item.id == lock["main"][0] and item.name == lock["main"][1]]
    if len(mains) != 1:
        raise fail("main body shape mismatch")
    if not _main_body_holds(mains[0], lock):
        raise fail("main body shape mismatch")

    seed_symbol = _seed_symbol(program, lock)
    consumed = [
        *(item for site in sites
          for item in (site.node, site.sampler, site.coord, site.lod)),
        *(site.owner for site in sites),
        *(site.sampler.symbol for site in sites),
        seed_symbol,
    ]
    _check_ledger(consumed, _CONSUMED_LEDGER, "textureLod admission",
                  lock["profile"])
    return TextureLodAdmissionProof(tuple(sites), tuple(consumed))


def apply_texture_lod_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree:
    the admission IS the identity -- ``textureLod(s, uv, 0.0)`` lowers to the
    existing ``texture`` path, so there is nothing to rewrite."""
    authenticate_texture_lod_admission(program, source_hash, profile)
    return program
