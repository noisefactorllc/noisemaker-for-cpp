"""Exact identity profile for ``synth/mandelbrot``'s three ``log`` sites and
its counted-for seed contract.

``synth/mandelbrot:mandelbrot`` is the counted-for bucket's third-cheapest
program (``counted-for-design.md`` §2.3 / §5, cost rank 3): measured **four
rungs from CLEAN at both authorities** behind only KNOWN mechanisms --

* **rung 1 (mechanism A, the const-global-literal bound shape):** the
  iteration loop ``for (int n = 0; n < MAX_ITER; n++)`` (normalized
  ``226:5-261:6``, owner ``mandelbrot_df64``) is bounded by the const global
  ``const int MAX_ITER = 500;`` (symbol 24, normalized ``31:1-31:26``).
  The bound proof rides the EXISTING dict-keyed module -- a new key in
  ``loop_proof.py``'s ``_SOURCE_GLOBAL_LITERAL_INT_PROFILES`` (the Task-23
  shape, carrier auto-supplied from the key, row stays minimal). This
  module does NOT add that key; it freezes the complete dict-entry data as
  ``counted_for_seed_contract`` (the parallax-lane pattern) and re-derives
  the seed-attached tree itself, so this record is the integration slice's
  one-move landing source. **The loop budget FITS the current caps** --
  measured trips 500, product 500, charge 1500 against
  ``COUNTED_FOR_V1_MAX_TRIP_COUNT/LEXICAL_PRODUCT/ENTRYPOINT_CHARGE`` of
  512/262144/262656: the loop-proof study's "needs budget increase"
  verdict is obsolete and must not be planned against.
* **rungs 2-3 (mechanisms C+D, out/inout + bare void calls):** the
  validator's next rejection after the seed is ``116:24: unsupported
  parameter direction out``; those mechanisms' frontend home is
  ``out_inout_admission_profile`` (newton's module, extended per-key with
  mandelbrot's TEN out parameters across THREE functions and FIVE bare
  void-call statements -- both figures re-measured; see the divergences
  below). This module only freezes their census as context
  (``mechanism_census``) and requires that module as its row companion.
* **rung 4 (mechanism E, this module's own mechanism):** ``log`` is
  analyzer-known (``body_semantic._BUILTIN_FAMILIES`` freezes the
  ``unary_float`` overload) but **absent from both authorities'
  vocabularies** -- the validator's ``APPROVED_CAPABILITIES``/``_BUILTINS``
  (44 frozen entries) and the emitter's builtin arms -- so a ``log`` node
  dies at the validator's ``value.callee not in _BUILTINS`` fall-through
  and at the emitter's generic arm (the design's ladder measured the
  emitter rejection at ``273:24``). **The tanh precedent is frontend-side
  and is exactly this shape**: ``tanh`` too is absent from every table,
  ``curl_vector_math_profile`` authenticates the site, and BOTH
  authorities carry node-identity arms (the validator's
  ``authorized_curl_tanh`` at ``generate_typed_slice.py:4776``, the
  emitter's ``proof.tanh_site`` arm emitting ``glsl::tanh_lanewise``).
  This module therefore freezes the three sites the same way -- as a
  frontend record handing the authorities the exact live nodes -- and BOTH
  authority arms are integration work that lands with the row. That is
  the log-admission verdict, frozen as ``LOG_ADMISSION_VERDICT``.

**The three sites** (all scalar ``float -> float``, arity one, every parent
a ``binary`` node):

* ``mandelbrot_df64 273:24-273:33`` -- ``log(mag2)`` in the df64 escape
  smoothing (``var log_zn = log(mag2) * 0.5`` in the JS factory);
* ``mandelbrot_df64 274:20-274:38`` -- ``log(log_zn / LOG2)``, the nested
  log-of-a-log of the smoothing denominator;
* ``outputDistance 295:30-295:38`` -- ``log(mag)`` in the distance
  estimator (NOT in the escape smoothing -- the design's prose placed only
  two of the three sites there).

**JavaScript authority** (quote-verified this session against the pinned
snapshot ``$RUN_ROOT/oracle/noisemaker-for-cpu``):

* ``canonical-kernels.js`` SHA-256
  ``66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe`` --
  byte-identical to the pin the cellRefract/kaleido/effects/parallax oracles
  froze. ``canonicalFactory252`` (line 30151) is the program's factory,
  registered once at line 36432. Its ``Function.prototype.toString`` is
  13,231 bytes, SHA-256 ``27b87c62...`` -- the extraction method
  cross-validated this session by reproducing the frozen
  ``canonicalFactory3`` (cellRefract/wobble) and ``canonicalFactory9``
  (kaleido) toString hashes exactly (``JS_CROSS_VALIDATION``).
* The factory destructures ``log`` straight from the stdlib (line 30152)
  and calls it at lines 30379 / 30380 / 30404 -- exactly the three sites.
* ``src/csl/glsl-runtime.js:341`` -- ``log: unary(Math.log)``: **JS
  ``Math.log`` is the authority**, applied lanewise but scalar at all
  three sites. The V8-vs-libm routing risk the struct design flagged for
  log/log2 is frozen as ``MATH_LOG_ROUTING_NOTE``: V8's ``Math.log`` is
  V8's own implementation, not the platform libm the C++ side links, so
  bit-level agreement is NOT guaranteed and must be oracle-verified; all
  three sites feed strictly positive magnitudes (no domain-edge cases),
  but the log-of-a-log at site 2 compounds any ULP divergence. The JS
  also narrows the ``LOG2`` const through f32 (``var LOG2 =
  0.6931471824645996``; the GLSL literal is ``0.6931471805599453``) --
  a narrowing point the emitter lane must measure, recorded here as
  ``JS_LOG2_NARROWED``.
* The design's §8 open question -- whether ``iterations``' metadata
  maximum exceeds 500 -- is RESOLVED: ``src/effects/specs.js`` freezes
  ``iterations: i(500, 50, 2000)``, so the source's own
  ``min(iterations, MAX_ITER)`` clamp (JS line 30459) has a reachable
  discriminating arm at iterations in (500, 2000] and an oracle case
  there is budgetable.

**This module is PREPARED, not landed** (the ``mutable_global_array``
landed/prepared split): ``KEYS`` is empty, ``PREPARED_KEYS`` carries the
mandelbrot key, and nothing in ``generate_typed_slice.py`` /
``emit_typed_cpp.py`` references the module yet -- so no live schema census
moves until the integration slice lands the row, the loop-proof dict key,
the out/inout record and the emitter ``log`` arm together.
``allowed_row_fields`` answers from ``PREPARED_ROW_FIELDS``: the row
contract is frozen now, enforced when the row lands, and matches
``out_inout_admission_profile``'s mandelbrot entry exactly (the newton
two-module pattern; mutually required through
``REQUIRED_COMPANION_PROFILES``).

Four census conventions were re-derived against the live tree and DIVERGE
from the design's §2.3 prose (recorded so nobody "fixes" them back):

* the design's "10 out params across 4 functions (getPOI ×2,
  mandelbrot_df64 ×7, transformCoords_df64 ×2)" decomposes wrong:
  mandelbrot_df64 carries **SIX** out parameters and the owners are
  **THREE** functions (the total of ten is right);
* the design's "3 bare void-call statements" missed ``main``'s own
  ``transformCoords_df64`` (``388:9``) and ``mandelbrot_df64`` (``389:9``)
  calls: the true census is **FIVE** (the JS factory has five
  ``__out__``-destructuring call sites);
* the design's "994 nodes" counts function bodies only; the house census
  (global declaration initializers included -- the standing blind-spot
  trap) freezes **999** (the five const initializers are the difference);
  and the design's "call edges 46" counts call NODES -- the deduplicated
  sorted edge SET frozen here has **31**;
* the design's interface SHA ``2f497a1f...ecbd6bb2d0a5...`` carries a
  one-character transcription error: the measured value is
  ``2f497a1f...ecbd6bb2c0a5...`` (the pre-whole fingerprint -- a strict
  superset of the interface tuple -- matches the design exactly, so the
  components agree and the prose string is the typo).

Claim boundary: mandelbrot is NOT the corpus's only ``log`` caller --
newton carries two sites (its own prepared lane's business) and julia
carries eight (adapter-only, ``check_corpus._ADAPTERS``); this module's
authenticatable set is mandelbrot alone, and all 24 of mandelbrot's
functions are reachable at the frozen (empty) defines, so every site is
oracle-coverable.
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


MANDELBROT_KEY = "synth/mandelbrot:mandelbrot"
MANDELBROT_PROFILE = "log-admission-mandelbrot-v1"

# The landed carrier registry.  Mandelbrot's MAX_ITER seed registration,
# out/inout companion, and log identity are promoted together by its slice
# landing; the emitter log arm is a separate downstream lane.
KEYS: tuple[str, ...] = (MANDELBROT_KEY,)
PROFILES = {MANDELBROT_KEY: MANDELBROT_PROFILE}
LOG_ADMISSION_KEYS = frozenset(KEYS)

# No prepared log records remain after the Mandelbrot frontend landing.
PREPARED_KEYS: tuple[str, ...] = ()

# The complete allowed field set for the slice row -- an ALLOWLIST, not a
# denylist, exhaustive by construction against the validator's
# `set(item) != expected` comparison. The row carries BOTH mandelbrot
# carriers: this module and the out/inout companion (mutually required
# below). The loop-proof dict key needs no row field of its own (carrier
# auto-supplied from the key).
ALLOWED_ROW_FIELDS: dict[str, frozenset[str]] = {
    MANDELBROT_KEY: frozenset({
        "defines",
        "program_key",
        "log_admission_profile",
        "out_inout_admission_profile",
    }),
}
PREPARED_ROW_FIELDS: dict[str, frozenset[str]] = {}

REQUIRED_COMPANION_PROFILES = {
    MANDELBROT_KEY: (("out_inout_admission_profile",
                      "out-inout-admission-mandelbrot-v1"),),
}

# --- frozen JavaScript provenance (see the module docstring) -----------------

JS_FACTORY = ("canonicalFactory252", 30151)
JS_REGISTRATION_LINE = 36432
JS_CANONICAL_KERNELS_SHA256 = (
    "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe")
# Function.prototype.toString of the factory, and the two frozen hashes the
# extraction method reproduced exactly (the toString-pin discipline).
JS_FACTORY_TOSTRING = (
    13231,
    "27b87c62a87c73d76e5a1d2d6096cecaa6714aeba3f26f72a03698592918ee29")
JS_CROSS_VALIDATION = (
    ("canonicalFactory3",
     "329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3"),
    ("canonicalFactory9",
     "4ab626fda5e91e7f89b93c9d863cda497b85d79239183499785c03607cce19a3"),
)
# The stdlib destructuring that binds the factory's `log`, and the runtime
# line that routes it: Math.log IS the authority.
JS_STDLIB_DESTRUCTURING = (
    "const { sin, cos, atan, pow, log, sqrt, abs, floor, min, max, "
    "clamp, length, dot, normalize } = $runtime.stdlib")
JS_STDLIB_LINE = 30152
JS_LOG_AUTHORITY_LINE = "log: unary(Math.log)"
JS_LOG_AUTHORITY_SITE = "src/csl/glsl-runtime.js:341"
# The sibling mandelbrot never uses (the routing-risk pair the struct design
# flagged: log AND log2).
JS_LOG2_SIBLING_LINE = "log2: unary(Math.log2)"
JS_LOG2_SIBLING_SITE = "src/csl/glsl-runtime.js:342"
# The three factory call sites, quote-frozen with their line numbers.
JS_LOG_SITES = (
    ("var log_zn = log(mag2) * 0.5;", 30379),
    ("var nu = (log(log_zn / LOG2)) / LOG2;", 30380),
    ("var dist = (2 * mag) * log(mag) / dmag;", 30404),
)
# Numeric-contract notes measured from the pinned snapshot.
JS_LOG2_NARROWED = "var LOG2 = 0.6931471824645996;"
JS_MAX_ITER_LINE = "var MAX_ITER = 500;"
JS_ITERATIONS_CLAMP = "var maxIter = min(iterations, MAX_ITER);"
JS_ITERATIONS_METADATA = (
    "src/effects/specs.js: iterations: i(500, 50, 2000) -- default 500, "
    "min 50, MAX 2000 > MAX_ITER 500, so the clamp's discriminating arm "
    "(iterations in (500, 2000]) is reachable and budgetable")
# The measured lowering contract both authorities must honour.
LOWERING_CONTRACT = (
    "log(float) == Math.log(float), scalar unary at all three sites",)
# The routing risk the struct design flagged for log/log2, frozen as data.
MATH_LOG_ROUTING_NOTE = (
    "Math.log is V8's own implementation, not the platform libm the C++ "
    "side links: bit-level agreement of the two log implementations is "
    "not guaranteed and must be oracle-verified. All three sites feed "
    "strictly positive magnitudes (mag2 > 1, log_zn/LOG2 > 0, mag > 0) so "
    "there are no domain-edge cases, but site 2 takes log of a log and "
    "compounds any ULP divergence; the JS also narrows LOG2 through f32 "
    "(0.6931471824645996), a narrowing point the emitter must reproduce.")
# The admission verdict: the tanh precedent executed as a frontend record.
LOG_ADMISSION_VERDICT = (
    "frontend record (the tanh precedent: curl_vector_math_profile "
    "authenticates the site and both authorities consume node identity). "
    "log is analyzer-known (body_semantic's unary_float overload) but "
    "absent from the validator's APPROVED_CAPABILITIES/_BUILTINS and from "
    "the emitter's builtin arms, exactly like tanh -- so BOTH authority "
    "arms (a validator callee arm consulting this record's nodes, and the "
    "emitter arm emitting the Math.log contract) are integration work "
    "landing with the row; the vocabulary stays at 44 entries.")

# The dict-entry capability the seed contract rides (loop_proof's own).
SEED_CAPABILITY = SOURCE_GLOBAL_LITERAL_INT_CAPABILITY

# Every optional `fixed_*_proof` field a TypedProgram carries. mandelbrot
# carries none, and the frozen-absent set is the whole dataclass enumeration;
# the test suite re-derives it, so a new proof field added elsewhere in the
# tree turns red here rather than slipping through.
_OPTIONAL_PROOF_FIELDS = (
    "fixed_affine_centers13_proof",
    "fixed_array_in_parameter_proof",
    "fixed_grid_counter_store_proof",
    "fixed_nine_table_proof",
)

_LOD_LITERAL_PATTERN = re.compile(r"[1-9][0-9]*")

# Every IR shape that mutates a writable lvalue. `post` is a distinct kind
# from `unary`, not an operator variant of it.
_MUTATION_KINDS = ("assign", "unary", "post")
_INCREMENT_OPERATORS = ("++", "--")
_BITWISE_OPERATORS = ("&", "|", "^", "<<", ">>")

# The transcendental family whose zero census bounds the admission: log is
# the only member mandelbrot uses (log2/exp/exp2/tanh all zero); pow is
# already approved and carries exactly the two getEffectiveZoom sites.
_ZERO_FAMILY = ("log2", "exp", "exp2", "tanh")

# The three sites' two live nodes each (6), the two DISTINCT owner
# functions (mandelbrot_df64 owns two sites and is consumed once), and the
# seed's Symbol: 9 distinct objects, each consumed exactly once.
_CONSUMED_LEDGER = 9

__all__ = (
    "KEYS", "PROFILES", "LOG_ADMISSION_KEYS", "PREPARED_KEYS",
    "MANDELBROT_KEY", "MANDELBROT_PROFILE", "SEED_CAPABILITY",
    "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS", "REQUIRED_COMPANION_PROFILES",
    "allowed_row_fields", "CountedForSeedContract",
    "counted_for_seed_contract", "LogSiteProof", "LogAdmissionProof",
    "authenticate_log_admission", "apply_log_admission",
    "JS_FACTORY", "JS_REGISTRATION_LINE", "JS_CANONICAL_KERNELS_SHA256",
    "JS_FACTORY_TOSTRING", "JS_CROSS_VALIDATION",
    "JS_STDLIB_DESTRUCTURING", "JS_STDLIB_LINE",
    "JS_LOG_AUTHORITY_LINE", "JS_LOG_AUTHORITY_SITE",
    "JS_LOG2_SIBLING_LINE", "JS_LOG2_SIBLING_SITE", "JS_LOG_SITES",
    "JS_LOG2_NARROWED", "JS_MAX_ITER_LINE", "JS_ITERATIONS_CLAMP",
    "JS_ITERATIONS_METADATA", "MATH_LOG_ROUTING_NOTE", "LOWERING_CONTRACT",
    "LOG_ADMISSION_VERDICT",
)


class CountedForSeedContract(NamedTuple):
    """The complete mechanism-A dict entry for the integration slice.

    Field-for-field a ``_SOURCE_GLOBAL_LITERAL_INT_PROFILES`` entry: patching
    ``_asdict()`` into that dict and passing the capability through
    ``analyze_program`` closes rung 1 (verified against the live tree; the
    next rejection is then ``116:24: unsupported parameter direction out``,
    mechanism C's).
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


class LogSiteProof(NamedTuple):
    """One admitted ``log`` call, by live node identity."""

    record: tuple
    node: TypedExpression
    argument: TypedExpression
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


class LogAdmissionProof(NamedTuple):
    """The three exact live log nodes, plus the visitation ledger."""

    sites: tuple[LogSiteProof, ...]
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
# this program the initializer census is exactly the five const-global
# literal nodes (the 994-vs-999 divergence from the design's prose).

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


def _pow_census(program: TypedProgram) -> tuple:
    """The already-approved transcendental sibling: exactly the two
    getEffectiveZoom sites (pow rides the general capability; it is frozen
    here as the family's boundary, the textureSize analog)."""
    return _builtin_census(program, "pow")


def _zero_family_census(program: TypedProgram) -> tuple[int, ...]:
    """log2/exp/exp2/tanh site counts -- all frozen zero. log2 is the
    routing-risk sibling (Math.log2, glsl-runtime.js:342) mandelbrot never
    calls; tanh is curl's carrier and must stay out of every table."""
    return tuple(sum(1 for _, node, _ in _program_nodes(program)
                     if node.kind == "builtin" and node.callee == name)
                 for name in _ZERO_FAMILY)


def _mechanism_census(program: TypedProgram) -> tuple[int, int, int, int]:
    """(out/inout parameters, bare void-call statements, bit-ops, index
    expressions) -- the design's §2.3 decomposition with BOTH corrected
    figures: ten out parameters and FIVE bare void calls (the design's
    '3 across 4 functions / mandelbrot_df64 ×7' undercounted the calls and
    mis-decomposed the owners: it is 10 across 3 functions, ×6 on
    mandelbrot_df64)."""
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


def _site_walk(program: TypedProgram):
    """``(function, node, statement, parent)`` for every ``log`` builtin
    node, in deterministic program order, nested statements included.
    Global declaration initializers cannot carry calls the analyzer types
    as builtins here, so the body walk is exhaustive."""
    for function in program.functions:
        def walk(value: TypedStatement):
            for expression in value.expressions:
                for node, parent in _walk_with_parent(expression, None):
                    if node.kind == "builtin" and node.callee == "log":
                        yield function, node, value, parent
            for child in value.children:
                yield from walk(child)
        for statement in function.body:
            yield from walk(statement)


def _resite(program: TypedProgram) -> dict[str, tuple]:
    """Re-derive the site records' positional columns from ``program`` --
    the owners and the spans the mutation moved -- while the identity hash
    tuples keep their frozen originals.

    The lock-under-test companion for the site-value mutation tests: it
    refreezes only what the mutation legitimately moved (the SITES), never
    the identity hashes, so the identity lock keeps its teeth while a
    deliberately moved span guarantees the identity record can still catch
    a mutant whose site columns are re-frozen. The child-KIND column is a
    value column and is never re-derived here.
    """
    frozen_sites = _LOCKS[MANDELBROT_KEY]["log_sites"]
    frozen_shape = _LOCKS[MANDELBROT_KEY]["log_shape"]
    records = []
    shape = []
    for index, (function, node, statement, parent) in enumerate(
            _site_walk(program)):
        argument = node.children[0]
        owner_id, owner_name = _owner_record(function)
        records.append((
            owner_id, owner_name, _span(node), _span(argument),
            _span(statement), frozen_sites[index][-2],
            frozen_sites[index][-1]))
        shape.append((
            owner_id, owner_name, *frozen_shape[index][2:-1], _span(node)))
    return {"log_sites": tuple(records), "log_shape": tuple(shape)}


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
# namespace, replacing the predicate with an always-true stand-in, and
# showing that the lock's message disappears. Keep them small,
# single-purpose and side-effect free.
#
# Ordering matters. `Symbol` embeds its declaration span, so every value-level
# lock (the seed declaration's shape and value, the site shapes) is evaluated
# AHEAD of the node-hash identity locks that would otherwise absorb them and
# make them vacuous; the coarse gate runs ahead of everything semantic; and
# the program-shape locks (binding table, inventory, call graph) run ahead of
# the mechanism locks so each mutation dies at the lock that names it.

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
    """Every sibling optional proof is absent -- mandelbrot carries none."""
    return all(getattr(program, field, None) is None
               for field in _OPTIONAL_PROOF_FIELDS)


def _call_graph_holds(program: TypedProgram, lock: dict) -> bool:
    """The exact deduplicated call-graph edge set, its digest, and full
    reachability (all 24 functions). Deliberately does NOT fold the
    counted-loop summary in (that is the closure lock's own message) and
    does not count call NODES (the design's '46' counted nodes; the frozen
    SET has 31 edges)."""
    edges = _call_graph(program)
    reachable, unreachable = _reachability(program)
    return (len(edges) == lock["call_edge_count"]
            and _sha(edges) == lock["call_graph_sha256"]
            and reachable == lock["reachable"]
            and unreachable == lock["unreachable"])


def _counted_summary_holds(program: TypedProgram, lock: dict) -> bool:
    """The seed-attached whole-program counted-for summary: one loop, proved,
    depth 1, product 500, charge 1500, acyclic. A pre-seed tree dies here."""
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
    """All 24 functions by id, name, return type and parameters."""
    return _function_inventory(program) == lock["function_inventory"]


def _resources_hold(program: TypedProgram, lock: dict) -> bool:
    """Eighteen uniforms, no samplers, one output, no texture reads, no
    derivatives."""
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
    """The bound global is a bare positive int-literal const named MAX_ITER
    with value 500 -- the Task-23 declaration checks, evaluated on the live
    declaration ahead of the identity hashes."""
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
            and _LOD_LITERAL_PATTERN.fullmatch(
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
    """All five source globals with their literal texts -- the same census
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
    never appear outside the two frozen read owners (`main`'s min() read and
    `mandelbrot_df64`'s loop bound -- unlike parallax, not every read lives
    in main, so the owner set is the frozen reads' own); global declaration
    initializers are walked too, so a reference planted in one is refused
    here as well."""
    owners = {name for name, _, _, _, _, _ in
              _LOCKS[MANDELBROT_KEY]["reads"]}
    for function, node, _ in _program_nodes(program):
        if node.kind == "id" and node.symbol_id in seed_ids:
            if function is None or function.name not in owners:
                return False
        if node.kind not in _MUTATION_KINDS or not node.children:
            continue
        if node.kind != "assign" and node.operator not in (
                _INCREMENT_OPERATORS):
            continue
        if node.children[0].symbol_id in seed_ids:
            return False
    return True


def _seed_reads_holds(program: TypedProgram, lock: dict) -> bool:
    """Exactly the two frozen id-node reads: `min(iterations, MAX_ITER)` in
    main at 368:35-368:43 and the loop bound in mandelbrot_df64 at
    226:25-226:33."""
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


def _iteration_loop_holds(program: TypedProgram, lock: dict) -> bool:
    """The one loop's complete proof shape at its frozen span in
    `mandelbrot_df64` -- induction 173, start 0, bound 500, `<`, `++`,
    trips 500, depth 1, product 500, charge 1500."""
    expected = lock["iteration_loop"]
    owners = [item for item in program.functions
              if item.id == expected["owner"][0]
              and item.name == expected["owner"][1]]
    if len(owners) != 1:
        return False

    def find_for(statements):
        for statement in statements:
            if statement.kind == "for":
                yield statement
            yield from find_for(statement.children)

    for statement in find_for(owners[0].body):
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


def _log_census_holds(sites: list, lock: dict) -> bool:
    """Exactly three log call nodes -- walked over global declaration
    initializers too, which is what proves no fourth site can hide in one.
    Cardinality only: the spans are the shape and identity locks' (a
    length-changing mutation may legitimately move them, and must die at
    the lock that names the moved thing, not here)."""
    return len(sites) == lock["log_site_count"]


def _log_shape_holds(sites: list, lock: dict) -> bool:
    """All three sites' structural shape -- owner, span, argument kind and
    type, result type, parent kind. The argument-kind column is the value
    tier (an id at sites 1/3, the `/LOG2` binary at site 2): a mutation
    that re-nests the argument dies here even when the spans are refrozen
    by ``_resite``."""
    shape = tuple(
        (site.owner_id, site.owner_name, site.argument.kind,
         site.argument.type.display(), site.node.type.display(),
         site.record[5], site.span)
        for site in sites)
    return shape == lock["log_shape"]


def _log_identity_holds(sites: list, lock: dict) -> bool:
    """All three sites' full records: owners, spans and the three per-site
    node hashes (call, argument, statement)."""
    return tuple(site.record for site in sites) == lock["log_sites"]


def _log_family_census_holds(program: TypedProgram, lock: dict) -> bool:
    """The family boundary: log is the only transcendental mandelbrot uses
    (log2/exp/exp2/tanh all zero -- log2 being the routing-risk sibling) and
    pow, already approved, has exactly the two frozen getEffectiveZoom
    sites."""
    return (_zero_family_census(program) == lock["zero_family"]
            and _pow_census(program) == lock["pow_sites"])


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

_FUNCTION_INVENTORY = (
    (95, "computeValueAt_df64", "float",
     ((81, "fragCoord", "vec2"), (82, "cX_df", "vec2"), (83, "cY_df", "vec2"),
      (84, "z_zoom", "float"), (85, "rot", "float"), (86, "maxIter", "int"))),
    (96, "df64_add", "vec2", ((31, "a", "vec2"), (32, "b", "vec2"))),
    (97, "df64_from", "vec2", ((39, "a", "float"),)),
    (98, "df64_mul", "vec2", ((35, "a", "vec2"), (36, "b", "vec2"))),
    (99, "df64_mul_f", "vec2", ((37, "a", "vec2"), (38, "b", "float"))),
    (100, "df64_quick_two_sum", "vec2",
     ((25, "a", "float"), (26, "b", "float"))),
    (101, "df64_sub", "vec2", ((33, "a", "vec2"), (34, "b", "vec2"))),
    (102, "df64_to_float", "float", ((40, "a", "vec2"),)),
    (103, "df64_two_prod", "vec2",
     ((29, "a", "float"), (30, "b", "float"))),
    (104, "df64_two_sum", "vec2", ((27, "a", "float"), (28, "b", "float"))),
    (105, "getEffectiveZoom", "float", ((94, "poiIndex", "int"),)),
    (106, "getPOI", "void",
     ((42, "index", "int"), (43, "cX_df", "vec2"), (44, "cY_df", "vec2"))),
    (107, "getPoiMaxZoom", "float", ((41, "index", "int"),)),
    (108, "inCardioid", "bool", ((52, "x", "float"), (53, "y", "float"))),
    (109, "inPeriod2Bulb", "bool",
     ((54, "x", "float"), (55, "y", "float"))),
    (110, "main", "void", ()),
    (111, "mandelbrot_df64", "void",
     ((58, "c_re", "vec2"), (59, "c_im", "vec2"), (60, "maxIter", "int"),
      (61, "smoothIter", "float"), (62, "rawIter", "float"),
      (63, "z_final", "vec2"), (64, "dz_final", "vec2"),
      (65, "stripeAcc", "float"), (66, "trapMin", "float"))),
    (112, "outputDistance", "float",
     ((70, "z", "vec2"), (71, "dz", "vec2"), (72, "rawIter", "float"),
      (73, "maxIter", "int"))),
    (113, "outputNormalMap", "float",
     ((87, "fragCoord", "vec2"), (88, "cX_df", "vec2"), (89, "cY_df", "vec2"),
      (90, "z_zoom", "float"), (91, "rot", "float"), (92, "maxIter", "int"),
      (93, "angle", "float"))),
    (114, "outputOrbitTrap", "float",
     ((78, "trapMin", "float"), (79, "rawIter", "float"),
      (80, "maxIter", "int"))),
    (115, "outputSmoothIteration", "float",
     ((67, "smoothIter", "float"), (68, "rawIter", "float"),
      (69, "maxIter", "int"))),
    (116, "outputStripeAverage", "float",
     ((74, "smoothIter", "float"), (75, "rawIter", "float"),
      (76, "stripeAcc", "float"), (77, "maxIter", "int"))),
    (117, "transformCoords_df64", "void",
     ((45, "fragCoord", "vec2"), (46, "cX_df", "vec2"), (47, "cY_df", "vec2"),
      (48, "z", "float"), (49, "rot", "float"), (50, "re_df", "vec2"),
      (51, "im_df", "vec2"))),
    (118, "trapDistance", "float", ((56, "z", "vec2"), (57, "shape", "int"))),
)

_BINDING_TABLE = (
    (1, "resolution", "vec2", "uniform", False, False),
    (2, "tileOffset", "vec2", "uniform", False, False),
    (3, "fullResolution", "vec2", "uniform", False, False),
    (4, "time", "float", "uniform", False, False),
    (5, "poi", "int", "uniform", False, False),
    (6, "outputMode", "int", "uniform", False, False),
    (7, "iterations", "int", "uniform", False, False),
    (8, "centerHiX", "float", "uniform", False, False),
    (9, "centerHiY", "float", "uniform", False, False),
    (10, "centerLoX", "float", "uniform", False, False),
    (11, "centerLoY", "float", "uniform", False, False),
    (12, "zoomSpeed", "float", "uniform", False, False),
    (13, "zoomDepth", "float", "uniform", False, False),
    (14, "invert", "float", "uniform", False, False),
    (15, "stripeFreq", "float", "uniform", False, False),
    (16, "trapShape", "int", "uniform", False, False),
    (17, "lightAngle", "float", "uniform", False, False),
    (18, "rotation", "float", "uniform", False, False),
    (19, "fragColor", "vec4", "output", True, False),
    (20, "PI", "float", "const", False, True),
    (21, "TAU", "float", "const", False, True),
    (22, "BAILOUT", "float", "const", False, True),
    (23, "LOG2", "float", "const", False, True),
    (24, "MAX_ITER", "int", "const", False, True),
)

_MAIN_BODY = (
    ("decl", "367:5-367:53"),
    ("decl", "368:5-368:45"),
    ("decl", "369:5-369:43"),
    ("decl", "370:5-370:44"),
    ("decl", "373:5-373:23"),
    ("expr", "374:5-374:31"),
    ("decl", "376:5-376:17"),
    ("if", "378:5-402:6"),
    ("if", "405:5-407:6"),
    ("expr", "409:5-409:40"),
)

_LOCKS = {
    MANDELBROT_KEY: {
        "profile": MANDELBROT_PROFILE,
        "source_path": "sources/synth/mandelbrot/mandelbrot.glsl",
        "raw_bytes": 14855,
        "raw_sha256":
            "0587dbc29f2dc8c186d7c47ebe6182e89dfe0387fc29a23826cac15499fba615",
        "normalized_bytes": 10414,
        "normalized_sha256":
            "c062ee7852d0bfab69ca1e2ead6ad68d95dfa5fda9cff8232254b38b34c311a9",
        "functions_sha256":
            "5b24f4c4818b8ffee46ca02f752e4e19223ac97e677cccce310510af9a274a3d",
        "whole_sha256":
            "d6a5840667d7293fa428a88eef00f8bcf4612a733958e738628c876ed210ebd3",
        # The design's §2.3 figure carried a one-character typo (d for c at
        # position 26); the measured value is frozen here.
        "interface_sha256":
            "2f497a1fb59406d16decbd6bb2c0a5e4e7e5536774fa7ec56a34de12de657c43",
        "defines": (),
        "function_count": 24,
        "function_inventory": _FUNCTION_INVENTORY,
        "resources": (
            ("resolution", "tileOffset", "fullResolution", "time", "poi",
             "outputMode", "iterations", "centerHiX", "centerHiY",
             "centerLoX", "centerLoY", "zoomSpeed", "zoomDepth", "invert",
             "stripeFreq", "trapShape", "lightAngle", "rotation"),
            (), ("fragColor",), False, False),
        "call_edge_count": 31,
        "call_graph_sha256":
            "652bd56b36e1a005d8203727106fbddd14f7a5b41c6192f89369c96e9416b548",
        "reachable": (95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106,
                      107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117,
                      118),
        "unreachable": (),
        "counted_loop_proof": (1, 0, 1, 500, 1500, True),
        # The seed contract's post-attachment figures (loop_proof's own
        # formulas over the seed-attached tree -- see
        # counted_for_seed_contract).
        "seed_post_functions":
            "8240975403a5fe23b71b16799b7617dece132599ccfea69b24e717710f76f39b",
        "seed_post_whole":
            "1ca045076337edb3bfcb5e618e0eb83f9633858eafb91176a2e713b4be28314e",
        "declaration_count": 24,
        "binding_table": _BINDING_TABLE,
        "seed": {
            "symbol_id": 24,
            "name": "MAX_ITER",
            "value": 500,
            "literal": "500",
            "span": "31:1-31:26",
            "declaration_sha256":
                "6621dc55855d3b645e0503d3128fed27ea927063835c31c5c1c68ab9c9f7e967",
            "symbol_sha256":
                "9a337dcb738d55051edb060319fe19c29d37cbb21f1ba7d831c579c51c1da13a",
        },
        "globals": (("PI", 20, "float", "3.14159265359"),
                    ("TAU", 21, "float", "6.28318530718"),
                    ("BAILOUT", 22, "float", "256.0"),
                    ("LOG2", 23, "float", "0.6931471805599453"),
                    ("MAX_ITER", 24, "int", "500")),
        "reads": (("main", 110, 368, 35, 368, 43),
                  ("mandelbrot_df64", 111, 226, 25, 226, 33)),
        "iteration_loop": {
            "owner": (111, "mandelbrot_df64"),
            "span": "226:5-261:6",
            "induction_symbol_id": 173,
            "start": 0,
            "bound": 500,
            "comparison": "<",
            "update": "++",
            "bound_kind": "source-global-const-literal",
            "trips": 500,
            "depth": 1,
            "product": 500,
            "charge": 1500,
        },
        "log_site_count": 3,
        # (owner_id, owner_name, argument kind, argument type, result type,
        #  parent kind, span)
        "log_shape": (
            (111, "mandelbrot_df64", "id", "float", "float", "binary",
             "273:24-273:33"),
            (111, "mandelbrot_df64", "binary", "float", "float", "binary",
             "274:20-274:38"),
            (112, "outputDistance", "id", "float", "float", "binary",
             "295:30-295:38"),
        ),
        # (owner_id, owner_name, span, argument span, statement span,
        #  parent kind, (call sha, argument sha, statement sha))
        "log_sites": (
            (111, "mandelbrot_df64", "273:24-273:33", "273:28-273:32",
             "273:9-273:40", "binary",
             ("886cfc8a9e873cd8d3347936d39c3007692c5bea6cd867ed6454d01ec6732117",
              "e338522f0c2c509fb325b02ac901348c4e7498dcb8bfb9ca1a5132cc15ed7b81",
              "14c67e90ac0423e7a971e1c84df64b7ba1466f4311a0bf670bb0c2a166cdc8a4")),
            (111, "mandelbrot_df64", "274:20-274:38", "274:24-274:37",
             "274:9-274:46", "binary",
             ("5a744b74fc3af8073fd87b0fb3959cf1a6f06d50ea7ae4a9dee4829060a208a9",
              "df5c68b98bea20eed0c55f4821863f5dd8c07d12ccdb48e633770968c76f83df",
              "c9c2f0c98692685cb5a10aa1e02811bd7dfb669fb8aac07aef62a5802123bb0a")),
            (112, "outputDistance", "295:30-295:38", "295:34-295:37",
             "295:5-295:46", "binary",
             ("a908733a3439b43be7d3e400a8b2ce244c093125b99a2c6bdf3aa8d31d89ad38",
              "e7fc3c17394bb7563bdbdc408b4aada8b7d587c3b1df9f7e70cce82f4438c1a5",
              "e93fb634a6fdc87a1fa64e3126c5bf53e1c595ab9edd87cebdfad3501434fcb6")),
        ),
        "pow_sites": (
            (105, "getEffectiveZoom", "357:16-357:47", 2),
            (105, "getEffectiveZoom", "359:12-359:31", 2),
        ),
        "zero_family": (0, 0, 0, 0),
        # (out/inout params, bare void calls, bit-ops, index expressions)
        "mechanism_census": (10, 5, 0, 0),
        "main": (110, "main", 10, "366:1-410:2"),
        "main_body": _MAIN_BODY,
        "total_nodes": 999,
        "total_assigns": 51,
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
            MANDELBROT_PROFILE,
            f"{key} is not an admitted log admission carrier")
    return fields


def counted_for_seed_contract(key: str) -> CountedForSeedContract:
    """The complete mechanism-A dict entry for ``key`` -- field-for-field a
    ``loop_proof._SOURCE_GLOBAL_LITERAL_INT_PROFILES`` entry, the
    integration slice's one-move landing source for the bound-proof key."""
    lock = _LOCKS.get(key)
    if lock is None:
        raise _profile_fail(
            MANDELBROT_PROFILE,
            f"{key} is not an admitted log admission carrier")
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


def _site_proofs(program: TypedProgram) -> list[LogSiteProof]:
    """Every live ``log`` call node in the program with its owner, its
    argument and its full record (owner, spans, the parent kind, and the
    three node hashes)."""
    sites: list[LogSiteProof] = []
    for function, node, statement, parent in _site_walk(program):
        if len(node.children) != 1:
            # A non-unary log cannot match the frozen shape; record it with
            # the children it has so the census/shape locks can name it.
            argument = node.children[0] if node.children else node
        else:
            argument = node.children[0]
        owner_id, owner_name = _owner_record(function)
        record = (owner_id, owner_name, _span(node), _span(argument),
                  _span(statement),
                  parent.kind if parent is not None else None,
                  (_sha(node), _sha(argument), _sha(statement)))
        sites.append(LogSiteProof(record, node, argument, function))
    return sites


def authenticate_log_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> LogAdmissionProof | None:
    """Authenticate the frozen log identity profile and return the three
    exact live call nodes for ``program.key``.

    Returns ``None`` when ``program.key`` is not a carrier and no profile
    was supplied, so callers can treat the result as optional
    unconditionally; supplying a profile for a non-carrier key is a hard
    failure that names the sole admitted sites.
    """
    if program.key not in _LOCKS:
        if profile is not None:
            raise _profile_fail(
                MANDELBROT_PROFILE,
                "program key is not an admitted log admission carrier; "
                f"{MANDELBROT_KEY} 273:24, 274:20 and 295:30 are the sole "
                "admitted log sites")
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
    if not _iteration_loop_holds(program, lock):
        raise fail("counted-for iteration loop profile mismatch")

    sites = _site_proofs(program)

    if not _log_census_holds(sites, lock):
        raise fail("log site census mismatch")
    if not _log_shape_holds(sites, lock):
        raise fail("log site shape mismatch")
    if not _log_identity_holds(sites, lock):
        raise fail("log site identity mismatch")
    if not _log_family_census_holds(program, lock):
        raise fail("log-family census mismatch")
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
    owners = {}
    for site in sites:
        owners.setdefault(site.owner_id, site.owner)
    consumed = [
        *(item for site in sites for item in (site.node, site.argument)),
        *owners.values(),
        seed_symbol,
    ]
    _check_ledger(consumed, _CONSUMED_LEDGER, "log admission",
                  lock["profile"])
    return LogAdmissionProof(tuple(sites), tuple(consumed))


def apply_log_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree:
    the admission IS the identity -- the three ``log`` nodes lower to the
    Math.log contract, so there is nothing to rewrite."""
    authenticate_log_admission(program, source_hash, profile)
    return program
