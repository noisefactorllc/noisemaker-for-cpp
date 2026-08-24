"""Exact five-node float-bit ingress profile for ``filter/grime:grime``.

grime reaches ``floatBitsToUint`` exactly five times, all in reachable code
(design ``varying-design.md`` 3): twice in ``hash21`` (normalized
``38:25-38:45`` and ``38:47-38:67`` -- the ``uvec3(floatBitsToUint(p.x),
floatBitsToUint(p.y), 0u)`` constructor, whose third lane is the ``0u``
literal) and three times in ``hash31`` (``43:25-43:45``, ``43:47-43:67``,
``43:69-43:89``). Everything else grime needs is already admitted: its
``pcg`` is the *vector* form (``uvec3 ^= uvec3 >> 16u``) and rides the
existing uint-vector-bitwise capability exactly as wobble's identical
``pcg`` does -- measured, not assumed.

This module does **not** add ``floatBitsToUint`` to the global builtin or
capability vocabulary, exactly like its four paid-for precedents
(``generate_typed_slice.py``'s identity-admission list):
``caustic_word_hash_profile`` (one site), ``scanline_error_float_bits_
ingress_profile`` (three sites), ``shapes_float_bits_ingress_profile`` (one
site) and ``shape_mixer_builtin_profile``. The frozen 44-entry
``APPROVED_CAPABILITIES`` tuple is untouched: the caller must admit these
nodes by object identity and skip ``used.add(...)``.

Why a new dict-keyed module rather than a per-key extension of a precedent
--------------------------------------------------------------------------

Measured, not guessed. ``shapes_float_bits_ingress_profile`` is single-key
(``SHAPES_FLOAT_BITS_INGRESS_KEYS = frozenset({classicNoisedeck/shapes})``)
and its record is welded to shapes-only downstream structure: the
``seedFrac`` positive-zero initializer lock (read off the real sign bit) and
the scalar-XOR ancestry that re-derives its candidate objects from
``scalar_uint_xor_profile``'s authenticator. ``scanline_error_float_bits_
ingress_profile`` is single-key too, and pins its constants through a frozen
``_FROZEN_PROFILE_TUPLE_REPR`` self-hash of the module's own module-level
record -- per-keying it would churn landed frozen code and invalidate that
self-integrity discipline. Neither carrier's *record shape* is per-key;
both are per-program by construction. grime's record is therefore a NEW
module in the ``varying_uv_profile`` shape this tree established for
follow-on keys: per-key ``_LOCKS`` row, landed ``KEYS`` / prepared
``PREPARED_KEYS`` split, and individually deletable lock predicates.

The JavaScript authority, quoted and cross-validated
----------------------------------------------------

``canonicalFactory66`` (``canonical-kernels.js:13836``, registered for
``filter/grime:grime`` at ``:36246``) destructures ``floatBitsToUint`` once
from ``$runtime.stdlib`` (``:13837``) and calls it at exactly the five
sites -- ``:13871`` (hash21) and ``:13876`` (hash31)::

    var v = pcg(cpu_uvec3(floatBitsToUint(p[0]), floatBitsToUint(p[1]), 0));
    var v = pcg(cpu_uvec3_float_float_float(floatBitsToUint(p[0]),
        floatBitsToUint(p[1]), floatBitsToUint(p[2])));

(note the JS third lane of hash21 is ``0`` where the GLSL says ``0u`` -- the
same value; the parent-identity lock pins the GLSL literal as measured).
The runtime's implementation (``glsl-runtime.js:411-414``) is exact bit
reinterpretation through a shared ArrayBuffer view::

    floatBitsToUint: (value) => {
      this.bitsFloat[0] = value
      return this.bitsUint[0]
    },

The factory's ``Function.prototype.toString`` SHA-256 is
``c5100a562df7d991381ed1be6e1bb9fd1f8b117f212b267ee23719734d80123f``
(8,413 bytes, byte-equal to the generated-file slice of the factory), and
the pinning method itself reproduces the wobble oracle's frozen cellRefract
factory digest ``329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3``
on the same snapshot and node (``v24.7.0``) -- measured by the grime
frontend lane probe before anything was frozen here.

Landed / prepared
-----------------

grime's record is **prepared**: no slice row carries
``grime_float_bits_ingress_profile`` yet, so the landed registry is empty
exactly like the varying module's was before the wobble slice -- registering
the key in ``KEYS`` without its row would redden the live schema census.
The row contract is frozen now (the universal two fields plus BOTH profile
fields: this carrier and ``varying_profile`` -- grime's whole closure is
exactly those two mechanisms, design 3) and
``varying_uv_profile.PREPARED_ROW_FIELDS`` composes it from this module's
field name, so the two contracts cannot drift.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedProgram


PROFILE = "grime-float-bits-ingress-v1"
GRIME_KEY = "filter/grime:grime"
GRIME_FLOAT_BITS_INGRESS_FIELD = "grime_float_bits_ingress_profile"

# The LANDED carrier registry: empty until the integration slice wires
# grime's row (the kaleido/varying pattern -- registry and slice stay in
# lockstep, `load_slice`'s per-field schema census sees a registered key
# exactly when its row carries the field).
KEYS: tuple[str, ...] = (GRIME_KEY,)
PROFILES: dict[str, str] = {GRIME_KEY: PROFILE}
GRIME_FLOAT_BITS_INGRESS_KEYS = frozenset(PROFILES)

# grime's record is frozen and authenticatable; its row lands in a later
# slice together with the varying carrier's field (grime's closure is
# exactly those two mechanisms -- see the module docstring and design 3).
PREPARED_KEYS: tuple[str, ...] = ()
PREPARED_PROFILES: dict[str, str] = {}

ALLOWED_ROW_FIELDS: dict[str, frozenset[str]] = {
    GRIME_KEY: frozenset({
        "defines",
        "program_key",
        "varying_profile",
        GRIME_FLOAT_BITS_INGRESS_FIELD,
    }),
}
PREPARED_ROW_FIELDS: dict[str, frozenset[str]] = {}

# The frozen JS evidence: every line cites its source location, and the
# toString/cross-validation digests are the measured values the probe
# recorded -- never re-typed from the design prose.
FACTORY_TO_STRING_SHA256 = (
    "c5100a562df7d991381ed1be6e1bb9fd1f8b117f212b267ee23719734d80123f")
CROSS_VALIDATION_DIGEST = (
    "329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3")
_JS_EVIDENCE = (
    "canonical-kernels.js:13836 function canonicalFactory66"
    "($bindings, $runtime) {  (registered filter/grime:grime at :36246)",
    "canonical-kernels.js:13837 const { ..., floatBitsToUint } = "
    "$runtime.stdlib  (destructured once; exactly five call sites total)",
    "canonical-kernels.js:13871 hash21: var v = pcg(cpu_uvec3("
    "floatBitsToUint(p[0]), floatBitsToUint(p[1]), 0));",
    "canonical-kernels.js:13876 hash31: var v = "
    "pcg(cpu_uvec3_float_float_float(floatBitsToUint(p[0]), "
    "floatBitsToUint(p[1]), floatBitsToUint(p[2])));",
    "glsl-runtime.js:411-414 floatBitsToUint: (value) => { "
    "this.bitsFloat[0] = value; return this.bitsUint[0] }  (exact bit "
    "reinterpretation through a shared ArrayBuffer view)",
    "canonical-kernels.js:13836-13986 canonicalFactory66 "
    "Function.prototype.toString SHA-256 "
    "c5100a562df7d991381ed1be6e1bb9fd1f8b117f212b267ee23719734d80123f "
    "(8,413 bytes, byte-equal to the generated-file slice)",
    "cross-validated: the same method on the same snapshot reproduces the "
    "wobble oracle's frozen cellRefract factory digest "
    "329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3",
)

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

# Both hash owners, the five ingress nodes, the two uvec3 construct parents
# and the two owning statements: eleven distinct objects, each visited and
# consumed exactly once.
_CONSUMED_LEDGER = 11

__all__ = (
    "PROFILE", "GRIME_KEY", "GRIME_FLOAT_BITS_INGRESS_FIELD",
    "KEYS", "PROFILES", "GRIME_FLOAT_BITS_INGRESS_KEYS",
    "PREPARED_KEYS", "PREPARED_PROFILES",
    "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS", "allowed_row_fields",
    "authenticate_grime_float_bits_ingress",
    "apply_grime_float_bits_ingress",
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


# --- walkers ----------------------------------------------------------------
#
# Every walker here descends `program.declarations` (global initializers
# included) as well as `program.functions`: a "whole-program" census that
# only walks function bodies would leave a planted ingress in a global
# initializer in a coarse-hash-only blind spot. grime carries no const
# globals (its initializer census is the empty tuple), but the census walks
# them anyway so a future parser change cannot hide a site there.

def _walk_expression(value, parent=None, path=()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value, path=(), ancestors=()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, item_path in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, item_path, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _program_nodes(program: TypedProgram):
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


def _node_census(program: TypedProgram) -> tuple[int, int]:
    total = 0
    assigns = 0
    for _, _, item, _, _, _ in _program_nodes(program):
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
         tuple((parameter.id, parameter.name, parameter.type.display())
               for parameter in item.parameters))
        for item in program.functions)


def _initializer_census(program: TypedProgram) -> tuple:
    return tuple(sorted(
        (item.symbol.id, item.symbol.name,
         tuple((node.kind, _span(node), node.literal,
                repr(node.literal_value), node.type.display())
               for node, _, _ in _walk_expression(item.initializer)))
        for item in program.declarations if item.initializer is not None))


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


# --- individually deletable locks -------------------------------------------
#
# Each predicate below is exactly one lock with exactly one message, ordered
# coarse-to-fine; value-level locks run ahead of the node-hash identity
# locks that would otherwise absorb them.

def _caller_source_hash_holds(source_hash: str | None, lock: dict) -> bool:
    return source_hash == lock["raw_sha256"]


def _defines_hold(program: TypedProgram, lock: dict) -> bool:
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
    return all(getattr(program, field, None) is None
               for field in _OPTIONAL_PROOF_FIELDS)


def _function_cardinality_holds(program: TypedProgram, lock: dict) -> bool:
    return len(program.functions) == lock["function_count"]


def _function_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    return _function_inventory(program) == lock["function_inventory"]


def _declaration_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    return (len(program.declarations) == lock["declaration_count"]
            and _declaration_inventory(program)
            == lock["declaration_inventory"])


def _initializer_census_holds(program: TypedProgram, lock: dict) -> bool:
    return _initializer_census(program) == lock["initializer_census"]


def _resources_hold(program: TypedProgram, lock: dict) -> bool:
    resources = program.resources
    return ((resources.uniforms, resources.samplers, resources.outputs,
             resources.uses_texture, resources.uses_derivatives)
            == lock["resources"])


def _call_graph_holds(program: TypedProgram, lock: dict) -> bool:
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


def _node_census_holds(program: TypedProgram, lock: dict) -> bool:
    total, assigns = _node_census(program)
    return total == lock["total_nodes"] and assigns == lock["total_assigns"]


def _owner_identity_holds(owners: dict, lock: dict) -> bool:
    """Both hash owners by full identity, each reachable from ``main``."""
    for (owner_id, owner_name, owner_return, owner_parameters,
         owner_body_length, owner_span) in lock["owners"]:
        owner = owners.get(owner_id)
        if owner is None:
            return False
        if ((owner.name, owner.return_type.display(),
             tuple((item.id, item.name, item.type.display(), item.direction)
                   for item in owner.parameters),
             len(owner.body), _span(owner))
                != (owner_name, owner_return, owner_parameters,
                    owner_body_length, owner_span)):
            return False
    return len(owners) == len(lock["owners"])


def _ingress_census_holds(located: list, owner_ids: frozenset) -> bool:
    """Exactly five floatBitsToUint builtins program-wide, every one inside
    a frozen owner (a site planted in any other function, or in a global
    initializer, breaks the census even when the count is refrozen)."""
    return (len(located) == 5
            and all(function is not None and function.id in owner_ids
                    for function, _, _, _, _ in located))


def _site_identity_holds(located: list, lock: dict) -> bool:
    """Per-site node identity -- span, result type, node hash, arity, the
    swizzle operand and its ``p`` base -- compared in walk order against the
    frozen five."""
    sites = lock["sites"]
    if len(located) != len(sites):
        return False
    for (function, node, parent, path, chain), record in zip(located, sites):
        (owner_id, span, type_name, node_sha, operand_record) = record
        if function is None or function.id != owner_id:
            return False
        if ((node.callee, _span(node), node.type.display(), _sha(node),
             node.category)
                != ("floatBitsToUint", span, type_name, node_sha, "rvalue")
                or len(node.children) != 1):
            return False
        operand = node.children[0]
        (operand_kind, operand_span, operand_type, operand_category,
         operand_sha, base_record) = operand_record
        if len(operand.children) != 1:
            return False
        if ((operand.kind, _span(operand), operand.type.display(),
             operand.category, _sha(operand))
                != (operand_kind, operand_span, operand_type,
                    operand_category, operand_sha)):
            return False
        base = operand.children[0]
        (base_kind, base_span, base_type, base_category, base_symbol_id,
         base_symbol_name, base_sha) = base_record
        if ((base.kind, _span(base), base.type.display(), base.category,
             base.symbol_id,
             None if base.symbol is None else base.symbol.name,
             _sha(base))
                != (base_kind, base_span, base_type, base_category,
                    base_symbol_id, base_symbol_name, base_sha)):
            return False
    return True


def _parent_identity_holds(located: list, lock: dict) -> bool:
    """Each owner's sites share exactly one ``uvec3`` construct parent --
    kind, span, type, node hash, the children-span tuple, the ``0u`` third
    lane of hash21's construct, and the sites as its exact children."""
    parents = lock["parents"]
    by_owner: dict[int, list] = {}
    for function, node, parent, path, chain in located:
        by_owner.setdefault(function.id, []).append((node, parent))
    if set(by_owner) != {row[0] for row in parents}:
        return False
    for owner_id, construct_record, child_spans, literal_record in parents:
        entries = by_owner[owner_id]
        references = [parent for _, parent in entries]
        if any(parent is None for parent in references):
            return False
        parent = references[0]
        if any(other is not parent for other in references[1:]):
            return False
        (construct_kind, construct_span, construct_type,
         construct_sha) = construct_record
        if ((parent.kind, _span(parent), parent.type.display(), _sha(parent))
                != (construct_kind, construct_span, construct_type,
                    construct_sha)):
            return False
        if tuple(_span(child) for child in parent.children) != child_spans:
            return False
        for node, _ in entries:
            if not any(child is node for child in parent.children):
                return False
        if literal_record is not None:
            literal = parent.children[len(child_spans) - 1]
            (literal_kind, literal_span, literal_type, literal_category,
             literal_text, literal_sha) = literal_record
            if ((literal.kind, _span(literal), literal.type.display(),
                 literal.category, literal.literal, _sha(literal))
                    != (literal_kind, literal_span, literal_type,
                        literal_category, literal_text, literal_sha)):
                return False
        elif len(child_spans) == 3 and parent.children[2].kind == "literal":
            return False
    return True


def _statement_ancestry_holds(located: list, lock: dict) -> bool:
    """Each site's expression path, statement chain and statement identity:
    the site sits in the owner's frozen statement, at the frozen index."""
    for (function, node, parent, path, chain), record in zip(
            located, lock["statement_paths"]):
        owner_id, statement_index, expected_path, statement_chain = record
        if function is None or function.id != owner_id:
            return False
        if (path != expected_path
                or tuple((item.kind, _span(item)) for item in chain)
                != statement_chain
                or len(chain) != 1
                or function.body[statement_index] is not chain[0]):
            return False
    return True


def _js_evidence_holds(lock: dict) -> bool:
    """The frozen JS evidence tuple: the quoted authority lines and both
    measured digests (the factory toString SHA and the cross-validation
    digest), never re-typed from prose."""
    return (lock["js_evidence"] == _JS_EVIDENCE
            and FACTORY_TO_STRING_SHA256 in "\n".join(lock["js_evidence"])
            and CROSS_VALIDATION_DIGEST in "\n".join(lock["js_evidence"]))


# --- frozen per-key record ---------------------------------------------------

_LOCKS = {
    GRIME_KEY: {
        "profile": PROFILE,
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
        # The two hash owners: id, name, return, parameters (with
        # direction), body length, span. Both reachable from main.
        "owners": (
            (45, "hash21", "float", ((13, "p", "vec2", "in"),), 2,
             "37:1-40:2"),
            (46, "hash31", "float", ((14, "p", "vec3", "in"),), 2,
             "42:1-45:2"),
        ),
        # The five sites in walk order (hash21's two, then hash31's three):
        # owner id, span, result type, node hash, and the operand record
        # (kind, span, type, category, hash, base record) -- the base is the
        # owner's ``p`` parameter by symbol identity.
        "sites": (
            (45, "38:25-38:45", "uint",
             "08f529d461a1c525343a8b27a1876b4195976f96d11c76d470f012adec2cd624",
             ("swizzle", "38:41-38:44", "float", "lvalue",
              "2d507c119afc29c36136b2c52c4ca3f10a408a0cc283efb9d87366acc627eee9",
              ("id", "38:41-38:42", "vec2", "lvalue", 13, "p",
               "58b7b6450cb446abd86f63eab5d20ef16de2827f37c1faada6559948f9a1fc82"))),
            (45, "38:47-38:67", "uint",
             "d67a70c22e6cf104a55fadb6ef7defeea859560c2afd354e3d013fd168e78300",
             ("swizzle", "38:63-38:66", "float", "lvalue",
              "03a1532a12a304e31c44b558d42bef5307901aa368105c63804991be7ba305ff",
              ("id", "38:63-38:64", "vec2", "lvalue", 13, "p",
               "d355c64e8dd18de1742ae757454f202c2498733eeb473b474064eaf0d1ad086a"))),
            (46, "43:25-43:45", "uint",
             "2a9094029495034b30cf3b07a597530c3619459f8c76ea04e83314758f6c0659",
             ("swizzle", "43:41-43:44", "float", "lvalue",
              "ce44619ee3151473535714cd8a32cfa3190ba1937f1decd39ba9df41e1f6bc21",
              ("id", "43:41-43:42", "vec3", "lvalue", 14, "p",
               "530a7d00dceb51e07ea31de846fe1b28dbd09157d8e6cad6200d4a968be15f70"))),
            (46, "43:47-43:67", "uint",
             "7e36820f81fc3e2660c3365642296b3e45254259cfb36c03f2097f895e713ea0",
             ("swizzle", "43:63-43:66", "float", "lvalue",
              "9fbd757669ee2cb4d66323e86069291e5e2e5274e4fa83f9e4be435bf3f33bff",
              ("id", "43:63-43:64", "vec3", "lvalue", 14, "p",
               "407ebc5ed1caf247f228a5314855dd02ae715fb943a1b387acb0cb3cda0c631b"))),
            (46, "43:69-43:89", "uint",
             "41a61bbd583317867619a3daaf1218ff170577e9af6046a0decc20594b646d19",
             ("swizzle", "43:85-43:88", "float", "lvalue",
              "384b565c660f285f241ddc3677ba5fbd20faccf466be929ee61e92da743168d2",
              ("id", "43:85-43:86", "vec3", "lvalue", 14, "p",
               "34c0d9fb5bdc34c2dd7bd56c704b4caceecca3d5660234f073200eaaf4bc777a"))),
        ),
        # Each owner's shared uvec3 construct parent: kind, span, type, node
        # hash; the children-span tuple; and (hash21 only) the frozen ``0u``
        # third-lane literal record -- kind, span, type, category, literal
        # text, node hash. hash31's parent has no literal lane, so its
        # literal record is None.
        "parents": (
            (45, ("construct", "38:19-38:72", "uvec3",
                  "36a8fde73885e77ae69a0ea81d94c920d4f6f5003611c79608df6ef2a9c5b010"),
             ("38:25-38:45", "38:47-38:67", "38:69-38:71"),
             ("literal", "38:69-38:71", "uint", "rvalue", "0u",
              "a29d75047c9781514c9ef57dbc5ec7a96964cc3c73f88101d9d22da882aef34e")),
            (46, ("construct", "43:19-43:90", "uvec3",
                  "12fcea23cf0ed236acba6d78612645d987c14bd7cb29e62416f4dda25a9d3c3c"),
             ("43:25-43:45", "43:47-43:67", "43:69-43:89"),
             None),
        ),
        # Per-site statement ancestry: owner id, statement index, expression
        # path, statement chain (kind, span).
        "statement_paths": (
            (45, 0, (0, "e0", 0, 0, 0), (("decl", "38:5-38:74"),)),
            (45, 0, (0, "e0", 0, 0, 1), (("decl", "38:5-38:74"),)),
            (46, 0, (0, "e0", 0, 0, 0), (("decl", "43:5-43:92"),)),
            (46, 0, (0, "e0", 0, 0, 1), (("decl", "43:5-43:92"),)),
            (46, 0, (0, "e0", 0, 0, 2), (("decl", "43:5-43:92"),)),
        ),
        "js_evidence": _JS_EVIDENCE,
        # Both owners, five sites, both constructs, both statements: each a
        # distinct object consumed exactly once.
        "consumed_ledger": _CONSUMED_LEDGER,
    },
}


def allowed_row_fields(key: str) -> frozenset[str]:
    """The complete set of slice-row fields permitted for ``key``.

    Exhaustive by construction (the validator's allowed-field arm compares
    ``set(item) != expected``): grime's landing row is the universal two
    fields plus BOTH profile fields -- this carrier and ``varying_profile``
    (``varying_uv_profile.PREPARED_ROW_FIELDS`` composes the same set from
    this module's field name). No key is landed yet, so every answer comes
    from ``PREPARED_ROW_FIELDS`` -- the row contract is frozen now, enforced
    when the row lands."""
    fields = ALLOWED_ROW_FIELDS.get(key) or PREPARED_ROW_FIELDS.get(key)
    if fields is None:
        raise _fail(
            f"{key} is not an admitted grime float-bit ingress carrier")
    return fields


def authenticate_grime_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple:
    """Return grime's five exact ``floatBitsToUint`` nodes, by identity.

    Returns an empty tuple when ``program.key`` is not the carrier, so
    callers can treat the result as a membership set unconditionally;
    supplying a profile for a non-carrier key is a hard failure that names
    the prepared record. Membership is the authenticatable set (the frozen
    ``_LOCKS`` row), not the landed registry: the record is the thing under
    test, and the slice-schema census is the integration gate's concern.
    """
    if program.key not in _LOCKS:
        if profile is not None:
            raise _fail("program key is not an admitted grime float-bit "
                        "ingress carrier")
        return ()
    lock = _LOCKS[program.key]

    def fail(message: str) -> ValueError:
        return _fail(message)

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
    if not _node_census_holds(program, lock):
        raise fail("whole-program node census mismatch")
    if not _declaration_inventory_holds(program, lock):
        raise fail("global declaration inventory mismatch")
    if not _initializer_census_holds(program, lock):
        raise fail("global declaration initializer census mismatch")

    # The whole-program site census -- function bodies AND global
    # declaration initializers (a site planted in an initializer carries
    # ``function=None`` and fails the census even at a refrozen count).
    located: list[tuple] = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for node, parent, path, chain in _walk_statement(
                    statement, (index,)):
                if (node.kind == "builtin"
                        and node.callee == "floatBitsToUint"):
                    located.append((function, node, parent, path, chain))
    for declaration in program.declarations:
        if declaration.initializer is None:
            continue
        for node, _, _ in _walk_expression(declaration.initializer):
            if node.kind == "builtin" and node.callee == "floatBitsToUint":
                located.append((None, node, None, (), ()))

    owner_ids = frozenset(row[0] for row in lock["owners"])
    owners = {function.id: function for function in program.functions
              if function.id in owner_ids}
    if not _owner_identity_holds(owners, lock):
        raise fail("ingress owner identity mismatch")
    for row in lock["owners"]:
        if not _owner_is_reachable(program, row[0]):
            raise fail("ingress owner is not reachable from main")
    if not _ingress_census_holds(located, owner_ids):
        raise fail(f"float-bit ingress census mismatch: {len(located)}")
    if not _site_identity_holds(located, lock):
        raise fail("ingress site identity mismatch")
    if not _parent_identity_holds(located, lock):
        raise fail("ingress construct parent mismatch")
    if not _statement_ancestry_holds(located, lock):
        raise fail("ingress statement ancestry mismatch")
    if not _js_evidence_holds(lock):
        raise fail("ingress JS evidence mismatch")

    # The visitation ledger: both owners, the five sites, each owner's one
    # construct parent and one owning statement -- eleven distinct objects,
    # each consumed exactly once.
    parents: list = []
    statements: list = []
    for owner_id, _, _, _ in lock["parents"]:
        for function, node, parent, path, chain in located:
            if function is not None and function.id == owner_id:
                if not any(parent is item for item in parents):
                    parents.append(parent)
                break
    for record in lock["statement_paths"]:
        owner_id, statement_index, _, _ = record
        owner = owners[owner_id]
        statement = owner.body[statement_index]
        if not any(statement is item for item in statements):
            statements.append(statement)
    _check_ledger(
        [*(owners[row[0]] for row in lock["owners"]),
         *(entry[1] for entry in located),
         *parents, *statements],
        lock.get("consumed_ledger", _CONSUMED_LEDGER),
        "float-bit ingress")
    return tuple(entry[1] for entry in located)


def apply_grime_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_grime_float_bits_ingress(program, source_hash, profile)
    return program
