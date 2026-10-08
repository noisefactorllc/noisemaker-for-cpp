"""Exact identity profiles for **``out`` parameter admission**.

``synth/newton:newton`` is the first ``out``-parameter carrier of the
struct-parity bucket (``docs/port-engineering/struct-parity/
struct-design.md`` §0.5/§3.4/§4.2; every figure re-measured this session
against the pinned corpus with this repo's own
``parse_program``/``analyze_program`` -- measure, never transcribe). The
program carries **two** functions with ``out`` parameters, four parameters
in total::

     98|void df64_cmul(vec2 ar, vec2 ai, vec2 br, vec2 bi,
     99|                out vec2 rr, out vec2 ri)
    107|void transformCoords_df64(vec2 fragCoord, vec2 cX_df, vec2 cY_df,
    108|    float z_zoom, float rot, out vec2 re_df, out vec2 im_df)

(the spans above are the normalized-source locations the frozen records
carry: ``df64_cmul`` 98:1-101:2 with ``rr`` at 98:52-98:63 and ``ri`` at
98:65-98:76; ``transformCoords_df64`` 107:1-119:2 with ``re_df`` at
108:38-108:52 and ``im_df`` at 108:54-108:68).

The validator's first rejecting site for this mechanism is
``98:52 unsupported parameter direction out`` (the design's §4.1 rung 1);
the emitter, independently, has **no direction gate at all** -- an ``out``
parameter that reached it would be emitted **by value with no gate**
(compiles, runs, silently wrong). That silent-pass hazard is why this
module exists as its own carrier with its own direction contract, and why
the contract freezes the emission shape (``glsl::Vec2&`` reference) as
*data the emitter must consume*, alongside the identity census.

Frozen census (all measured):

* **4 out parameters** -- the two above per function, ordinals 4/5 in
  ``df64_cmul`` and 5/6 in ``transformCoords_df64``; every one ``vec2``,
  every one ``out``.
* **Zero ``inout`` parameters** -- newton has none; the frozen empty
  census has no switch to loosen. (``filter/watercolor:wcSimplify``'s
  ``inout vec3`` swap is a different carrier,
  ``inout_vec3_swap_profile``; newton's row must not carry it.)
* **Write-once-in-owner shape** -- each out parameter's *only* reference
  in its owning function is the whole left-hand side of a plain ``=``
  assign that is the sole expression of a top-level ``expr`` statement:
  ``rr`` at 99:5, ``ri`` at 100:5, ``re_df`` at 117:5, ``im_df`` at
  118:5. No reads, no compound operators, no partial targets.
* **3 call sites**, every one in ``main``, every one a **bare void-call
  statement** (the documented wcSimplify class): ``transformCoords_df64``
  at 197:5-198:55 (7 args) and ``df64_cmul`` at 230:13-230:54 and
  237:9-237:52 (6 args each). At every site the out arguments are the
  **last two** arguments and are bare ``id`` nodes naming **plain local
  vec2 variables** (``re_df``/``im_df``; ``tr``/``ti``; ``znr``/``zni``)
  -- exactly the shape that lowers soundly to a C++ reference bound to
  the caller's local.

JavaScript authority (quote-verified this session against the frozen
snapshot's ``canonicalFactory264``): the transpiler keeps the helpers
value-returning and copies results into the caller's arrays --

* body tail: ``df64_sub(df64_mul(ar, br), df64_mul(ai,
  bi)).reduce((res,el,i)=>(res[i] = el, res), rr);`` then
  ``df64_cmul.__out__ = [rr, ri];`` (``transformCoords_df64`` the same
  with ``__out__ = [re_df, im_df]``);
* call site: a comma expression ``(df64_cmul(pwr, pwi, zr_df, zi_df, tr,
  ti), [tr, ti] = df64_cmul.__out__, df64_cmul.__return__)``;
* the out arrays are **pre-allocated fresh at the call site** --
  ``var tr = new $runtime.PooledFloat32Array([0, 0]), ti = ...`` and
  ``var znr = ..., zni = ...`` (and ``re_df``/``im_df`` likewise).

Reference semantics underneath: the port's plain ``glsl::Vec2&``
parameters are the exact analog (the design's §3.2/§3.3). The frozen
``DirectionContract`` below carries the emission shape so the emitter can
never silently pass by value: ``native_abi = "glsl::Vec2&"``,
``pass_mechanism = "reference"``, ``by_value_emission = "forbidden"``,
and ``emitter_direction_gate_required`` is the flag the emitter's own
RED test must consume (delete the emitter's direction check and the
by-value emission must turn a test red -- no generic gate would).

**Landed/prepared split** (the ``mutable_global_array_profile.py``
pattern): ``KEYS`` is empty until newton's row lands; the record is
``PREPARED`` now. The row contract (``PREPARED_ROW_FIELDS``) freezes the
row as carrying both newton struct-lane carriers -- this module and
``struct_declaration_profile`` -- mutually required through
``REQUIRED_COMPANION_PROFILES``.

**No vocabulary growth.** ``out`` never joins ``APPROVED_CAPABILITIES``;
admission is by object identity into the frozen records below only.

---

``filter/lightLeak:lightLeak`` is this module's second key (the
counted-for design's §2.2/§5, cost rank 2 -- measured **three rungs from
CLEAN at both authorities** behind only KNOWN mechanisms; every figure
re-measured this session against the pinned corpus with this repo's own
``parse_program``/``analyze_program``). It lands mechanisms A, C, and D at
their smallest measured size with this phase's registry and freezes the
exact mechanism-A dict entry:

* **mechanism A (the const-global-literal bound shape):** the voronoi loop
  ``for (int i = 0; i < POINT_COUNT; i++)`` (normalized ``65:5-80:6``) is
  bounded by ``const int POINT_COUNT = 6;`` (symbol 2, normalized
  ``5:1-5:27``). The bound proof rides ``loop_proof.py``'s
  ``_SOURCE_GLOBAL_LITERAL_INT_PROFILES`` -- the phase-1 dict key landed with
  this module's row. The complete dict-entry data is frozen as
  ``CountedForSeedContract``
  (``counted_for_seed_contract`` -- the counted-for seed-contract pattern
  parallax's lane froze): its live entry closes rung 1, measured -- the next
  rejection is then
  ``60:50: unsupported parameter direction out``.
* **mechanism C (this module's own):** exactly **2 out parameters on one
  function** -- ``voronoiCell(vec2, float, float, out vec3 cell_color, out
  float cell_dist)`` (ordinals 3/4, spans ``60:50``/``60:71``), both
  written once as the whole LHS of a top-level ``expr`` statement (``83:5``,
  ``84:5``). **Zero inout parameters** (the same fail-closed boundary).
* **mechanism D (the bare-call census):** exactly **2 bare void-call
  statements in the whole program**, both ``voronoiCell`` in ``main``
  (``114:5-114:54`` and ``125:5-125:61``), both top-level (unlike newton,
  whose calls nest inside loops), with the out arguments as the trailing
  pair naming plain locals (``base_cell``/``base_dist`` and
  ``warp_cell``/``warp_dist``). The program-wide ``_bare_call_census``
  proves no third bare call exists anywhere -- the emitter arm's complete
  admission set.

**The lock is frozen over the SEED-ATTACHED tree** (semantic.py's own
sequence: canonical attach, authenticate, re-attach with the seed): the
row, the loop-proof dict key and the authority arms land together, so the
tree this module will authenticate is the closed one -- summary ``(1, 0,
1, 6, 12, True)`` (trips 6, product 6, charge 12, the design's §2.2
figures re-derived). Today's live pre-seed tree dies at the coarse
function fingerprint by design. A ``_counted_rebuild_holds`` lock
re-derives the seed-attached tree from the frozen seed so a tree that
merely claims the closed summary cannot pass.

**JavaScript authority** (quote-verified against the pinned snapshot's
``canonicalFactory77``, definition line 14827, sole registration line
36257; ``canonical-kernels.js`` SHA-256 ``66adc01c…`` byte-identical to
the pin the cellRefract/kaleido/effects/parallax oracles froze; the
factory's ``toString()`` SHA-256 is frozen with the derivation method
cross-validated by reproducing the frozen smoothEdge pin
``732feb5a…``)::

    mix(hash33(s), color, 0.6000000238418579)
      .reduce((res,el,i)=>(res[i] = el, res), cell_color);
    cell_dist = best_dist;
    voronoiCell.__out__ = [cell_color, cell_dist];

    (voronoiCell(uv, seed_f, t, base_cell, base_dist),
     [base_cell, base_dist] = voronoiCell.__out__,
     voronoiCell.__return__)

The lightLeak-specific hazard the mixed ``DirectionContract`` freezes:
the **vec3** out argument is a pre-allocated pooled array
(``var base_cell = new $runtime.PooledFloat32Array([0, 0, 0])``) but the
**float** out argument is a plain scalar (``var base_dist = 0``) -- unlike
newton's all-``Vec2`` shape -- so the per-parameter ABI
(``parameter_abis``: ``glsl::Vec3&`` and ``float&``) is data the emitter
must consume, with by-value emission forbidden for both.

Three census conventions re-derived against the live tree and DIVERGING
from the design's prose (recorded so nobody "fixes" them back; the same
classes as parallax's):

* the design's "574 nodes" counts function bodies only; the house census
  (global declaration initializers included) freezes **576** -- the two
  const-global literal initializers are the difference;
* the design's "edges 8" counts call NODES (``main`` calls ``voronoiCell``
  twice, ``voronoiCell`` calls ``hash33`` twice); the deduplicated sorted
  edge SET frozen here has **6** edges;
* the mechanism census is ``(2 out params, 2 bare calls, 1 bit-op, 0 index
  expressions)`` -- the one ``uvec3 >> uint`` (pcg ``25:10-25:18``) is the
  already-admitted vector form, carried in the census only as the
  program's bit-op boundary.

``hash31`` is the one unreachable function at the frozen (empty) defines;
its ``pcg`` call edge is frozen in the unreachable set, and the out/inout
sites are all in reachable code -- no write-only or unreachable caveats
for the mechanism itself.
"""

from __future__ import annotations

import hashlib
import re
from typing import NamedTuple

from .loop_proof import (SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
                         attach_counted_loop_proofs,
                         summarize_counted_loop_proofs)
from .typed_ir import (TypedExpression, TypedFunction, TypedProgram,
                       TypedStatement, Symbol)


NEWTON_KEY = "synth/newton:newton"
NEWTON_PROFILE = "out-inout-admission-newton-v1"
NEWTON_SOURCE_PATH = "synth/newton/newton.glsl"

LIGHTLEAK_KEY = "filter/lightLeak:lightLeak"
LIGHTLEAK_PROFILE = "out-inout-admission-lightleak-v1"
LIGHTLEAK_SOURCE_PATH = "filter/lightLeak/lightLeak.glsl"

# The counted-for bucket's cost-rank-3 program (counted-for-design.md
# §2.3/§5), extended per-key by the mandelbrot frontend lane. Measured
# (re-deriving the design's §2.3 figures -- two of them wrong): **TEN out
# parameters across THREE functions** -- getPOI ×2 (out vec2 cX_df/cY_df,
# ordinals 1/2), mandelbrot_df64 ×**6** (out float smoothIter/rawIter/
# stripeAcc/trapMin, out vec2 z_final/dz_final, ordinals 3-8), and
# transformCoords_df64 ×2 (out vec2 re_df/im_df, ordinals 5/6) -- the
# design's "across 4 functions / mandelbrot_df64 ×7" mis-decomposed the
# owners while getting the total right; and **FIVE bare void-call
# statements** (the design counted 3, missing main's own
# transformCoords_df64 ``389:9`` and mandelbrot_df64 ``390:9``), matching
# the JS factory's five ``__out__``-destructuring call sites exactly.
# Unlike newton's and lightLeak's write-once owners, mandelbrot's out
# parameters carry a MULTI-STORE census (33 whole-LHS plain ``=``
# stores across nested arms) and exactly TWO non-store references --
# z_final is READ after its tail store in ``dot(z_final, z_final)`` at
# ``272:22``/``272:31`` (the JS reads it back identically) -- so the
# frozen read census replaces the write-once-empty invariant for this key.
# Mechanism A (the MAX_ITER=2048 seed contract) is owned by mandelbrot's
# OTHER carrier (``log_admission_profile``, which also owns mechanism E's
# three ``log`` sites): this lock carries no ``seed`` key, so the
# seed-contract accessor stays single-sourced there; this module's coarse
# fields freeze the SEED-ATTACHED tree the authorities will hold once the
# row, the dict key and both carriers land together.
MANDELBROT_KEY = "synth/mandelbrot:mandelbrot"
MANDELBROT_PROFILE = "out-inout-admission-mandelbrot-v1"
MANDELBROT_SOURCE_PATH = "synth/mandelbrot/mandelbrot.glsl"
JULIA_KEY = "synth/julia:julia"
JULIA_PROFILE = "out-inout-admission-julia-v1"
JULIA_SOURCE_PATH = "synth/julia/julia.glsl"

# The landed carrier registry. Newton's row and its struct companion land
# together; Mandelbrot's out/inout record lands with its log companion.
KEYS: tuple[str, ...] = (LIGHTLEAK_KEY, JULIA_KEY, MANDELBROT_KEY, NEWTON_KEY)
PROFILES: dict[str, str] = {
    JULIA_KEY: JULIA_PROFILE,
    LIGHTLEAK_KEY: LIGHTLEAK_PROFILE,
    NEWTON_KEY: NEWTON_PROFILE,
    MANDELBROT_KEY: MANDELBROT_PROFILE,
}
OUT_INOUT_ADMISSION_KEYS = frozenset(PROFILES)

# No prepared out/inout records remain after the Mandelbrot frontend landing.
PREPARED_KEYS: tuple[str, ...] = ()

# The complete allowed field set for the future slice row -- an ALLOWLIST.
# The frozen newton row carries both newton struct-lane carriers: this
# module and the struct-declaration companion (mutually required below).
# The frozen lightLeak row is minimal: the loop-proof dict key needs no row
# field (carrier auto-supplied from the key) and lightLeak has no companion
# carrier, so the row carries only this module's profile beside the base
# fields. The frozen mandelbrot row carries both mandelbrot carriers:
# this module and the log/seed companion (mutually required below; the
# identical dict also lives in log_admission_profile -- the newton
# two-module pattern).
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
    LIGHTLEAK_KEY: frozenset({
        "defines",
        "program_key",
        "out_inout_admission_profile",
    }),
    MANDELBROT_KEY: frozenset({
        "defines",
        "program_key",
        "log_admission_profile",
        "out_inout_admission_profile",
    }),
}
PREPARED_ROW_FIELDS: dict[str, frozenset[str]] = {}

REQUIRED_COMPANION_PROFILES = {
    JULIA_KEY: (
        ("julia_frontend_profile", "julia-frontend-admission-v1"),
        ("struct_declaration_profile", "struct-declaration-julia-v1"),
    ),
    NEWTON_KEY: (("struct_declaration_profile",
                  "struct-declaration-newton-v1"),),
    MANDELBROT_KEY: (("log_admission_profile",
                      "log-admission-mandelbrot-v1"),),
}

# --- frozen JavaScript provenance for lightLeak (see the module docstring) ---

# canonical-kernels.js facts, quote-verified against the pinned snapshot.
LIGHTLEAK_JS_FACTORY = ("canonicalFactory77", 14827)
LIGHTLEAK_JS_REGISTRATION_LINE = 36257
LIGHTLEAK_JS_CANONICAL_KERNELS_SHA256 = (
    "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe")
# The factory's toString() SHA-256. The derivation method (hashing
# canonicalKernelFactories[key].toString() in node against the pinned
# snapshot) was cross-validated by first reproducing the frozen smoothEdge
# pin (tests/test_typed_generator.py:13861) exactly.
LIGHTLEAK_JS_FACTORY_TO_STRING_SHA256 = (
    "9cf716594f8d25347737104d2ec0658276ac5a11405eb878706dc8f429c9055f")
SMOOTH_EDGE_FACTORY_TO_STRING_SHA256 = (
    "732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e")
# The quote-verified __out__ materialization (voronoiCell body tail and
# both call sites; see the module docstring for the full context).
LIGHTLEAK_JS_OUT_STASH = "voronoiCell.__out__ = [cell_color, cell_dist]"
LIGHTLEAK_JS_CALL_SHAPE = (
    "(voronoiCell(uv, seed_f, t, base_cell, base_dist), "
    "[base_cell, base_dist] = voronoiCell.__out__, "
    "voronoiCell.__return__)")
LIGHTLEAK_JS_VEC3_STORE = (
    ".reduce((res,el,i)=>(res[i] = el, res), cell_color)")
LIGHTLEAK_JS_FLOAT_STORE = "cell_dist = best_dist"
LIGHTLEAK_JS_OUT_ALLOCATION = (
    "var base_cell = new $runtime.PooledFloat32Array([0, 0, 0]); "
    "var base_dist = 0")
LIGHTLEAK_NATIVE_ABI = "glsl::Vec3&, float&"
LIGHTLEAK_NATIVE_SHAPE = (
    "caller-local glsl::Vec3 and float, uninitialized before the call (JS "
    "pre-allocates PooledFloat32Array [0, 0, 0] for the vec3 and a plain 0 "
    "scalar for the float)")
LIGHTLEAK_JS_BODY_TAIL = (
    "mix(hash33(s), color, 0.6000000238418579)"
    ".reduce((res,el,i)=>(res[i] = el, res), cell_color); "
    "cell_dist = best_dist")

# The dict-entry capability the seed contract rides (loop_proof's own).
LIGHTLEAK_SEED_CAPABILITY = SOURCE_GLOBAL_LITERAL_INT_CAPABILITY

# --- frozen JavaScript provenance for mandelbrot (quote-verified this
# session against the pinned snapshot; the same canonical-kernels.js pin
# as lightLeak's, byte-identical to the cellRefract/kaleido/effects pins).

MANDELBROT_JS_FACTORY = ("canonicalFactory252", 30151)
MANDELBROT_JS_REGISTRATION_LINE = 36432
MANDELBROT_JS_CANONICAL_KERNELS_SHA256 = (
    "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe")
# The factory's toString(): 13,231 bytes, SHA-256 below. The brace-matching
# extraction method was cross-validated by reproducing the frozen
# cellRefract/wobble (canonicalFactory3) and kaleido (canonicalFactory9)
# toString hashes exactly.
MANDELBROT_JS_FACTORY_TOSTRING_BYTES = 13231
MANDELBROT_JS_FACTORY_TO_STRING_SHA256 = (
    "27b87c62a87c73d76e5a1d2d6096cecaa6714aeba3f26f72a03698592918ee29")
# The per-function __out__ stashes. mandelbrot_df64's stash text appears
# TWICE in the factory (line 30335, the cardioid early-return arm, and
# 30385, the tail) -- both arms re-stash after writing the six arrays.
MANDELBROT_JS_OUT_STASH = (
    "mandelbrot_df64.__out__ = "
    "[smoothIter, rawIter, z_final, dz_final, stripeAcc, trapMin]")
MANDELBROT_JS_GETPOI_STASH = "getPOI.__out__ = [cX_df, cY_df]"
MANDELBROT_JS_TRANSFORM_STASH = (
    "transformCoords_df64.__out__ = [re_df, im_df]")
# getPOI's nine arms write the pooled arrays lane-by-lane as comma
# expressions (quote: arm 3, the scepterValley nucleus); the single tail
# stash above closes the function.
MANDELBROT_JS_GETPOI_LANE_WRITE = (
    "(cX_df[0] = -1.7548776865005493, "
    "cX_df[1] = 2.025385725801243e-8, cX_df)")
# main's call site (factory line 30473); computeValueAt_df64 carries two
# more and main two more beside (30427/30431/30463/30472) -- five total.
MANDELBROT_JS_CALL_SHAPE = (
    "(mandelbrot_df64(re_df, im_df, maxIter, smoothI, rawI, z_final, "
    "dz_final, stripeAcc, trapMin), [smoothI, rawI, z_final, dz_final, "
    "stripeAcc, trapMin] = mandelbrot_df64.__out__, "
    "mandelbrot_df64.__return__)")
# The out arguments are pre-allocated fresh at every call site: vec2 as a
# pooled pair, float as a plain Number zero.
MANDELBROT_JS_VEC2_ALLOCATION = (
    "var z_final = new $runtime.PooledFloat32Array([0, 0]), "
    "dz_final = new $runtime.PooledFloat32Array([0, 0])")
MANDELBROT_JS_FLOAT_ALLOCATION = "var smoothI = 0, rawI = 0"

# Every `fixed_*_proof` field a TypedProgram carries; ALL are absent for
# newton (measured). Re-derived from the dataclass by the test suite.
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

# Mechanism-A seed locks: the IR shapes that mutate a writable lvalue
# (`post` is a distinct kind from `unary`), and the positive-int-literal
# pattern loop_proof's own declaration check applies.
_MUTATION_KINDS = ("assign", "unary", "post")
_INCREMENT_OPERATORS = ("++", "--")
_BITWISE_OPERATORS = ("&", "|", "^", "<<", ">>")
_SEED_LITERAL_PATTERN = re.compile(r"[1-9][0-9]*")

# The four out-parameter Symbols, the two owning functions, the four
# whole-LHS store `id` nodes with their four assign nodes, the three call
# nodes, their six out-argument nodes, and the three bare-call statements:
# 26 distinct objects, each consumed exactly once (newton; the module
# default so the sabotage test's patch still bites). lightLeak's count
# rides its lock as "consumed_ledger".
_CONSUMED_LEDGER = 26

__all__ = (
    "KEYS", "PROFILES", "OUT_INOUT_ADMISSION_KEYS", "PREPARED_KEYS",
    "NEWTON_KEY", "NEWTON_PROFILE", "NEWTON_SOURCE_PATH",
    "JULIA_KEY", "JULIA_PROFILE", "JULIA_SOURCE_PATH",
    "LIGHTLEAK_KEY", "LIGHTLEAK_PROFILE", "LIGHTLEAK_SOURCE_PATH",
    "LIGHTLEAK_SEED_CAPABILITY",
    "LIGHTLEAK_JS_FACTORY", "LIGHTLEAK_JS_REGISTRATION_LINE",
    "LIGHTLEAK_JS_CANONICAL_KERNELS_SHA256",
    "LIGHTLEAK_JS_FACTORY_TO_STRING_SHA256",
    "SMOOTH_EDGE_FACTORY_TO_STRING_SHA256",
    "LIGHTLEAK_JS_OUT_STASH", "LIGHTLEAK_JS_CALL_SHAPE",
    "LIGHTLEAK_JS_VEC3_STORE", "LIGHTLEAK_JS_FLOAT_STORE",
    "LIGHTLEAK_JS_OUT_ALLOCATION",
    "MANDELBROT_KEY", "MANDELBROT_PROFILE", "MANDELBROT_SOURCE_PATH",
    "MANDELBROT_JS_FACTORY", "MANDELBROT_JS_REGISTRATION_LINE",
    "MANDELBROT_JS_CANONICAL_KERNELS_SHA256",
    "MANDELBROT_JS_FACTORY_TOSTRING_BYTES",
    "MANDELBROT_JS_FACTORY_TO_STRING_SHA256",
    "MANDELBROT_JS_OUT_STASH", "MANDELBROT_JS_GETPOI_STASH",
    "MANDELBROT_JS_TRANSFORM_STASH", "MANDELBROT_JS_GETPOI_LANE_WRITE",
    "MANDELBROT_JS_CALL_SHAPE", "MANDELBROT_JS_VEC2_ALLOCATION",
    "MANDELBROT_JS_FLOAT_ALLOCATION",
    "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS",
    "REQUIRED_COMPANION_PROFILES", "allowed_row_fields",
    "OutParameterRecord", "OutStoreRecord", "OutCallSiteRecord",
    "OutReadRecord",
    "DirectionContract", "direction_contract",
    "JuliaOutAdmissionRecord",
    "JuliaOutArgumentRecord", "JuliaOutCallRecord",
    "CountedForSeedContract", "counted_for_seed_contract",
    "authenticate_out_inout_admission", "apply_out_inout_admission",
)


class OutParameterRecord(NamedTuple):
    """One out parameter's identity: owner, ordinal, type, direction, and
    the parameter's source span (value tier) and Symbol hash."""

    function_id: int
    function_name: str
    function_span: str
    parameter_id: int
    parameter_name: str
    glsl_type: str
    direction: str
    ordinal: int
    parameter_span: str
    parameter_sha256: str


class OutStoreRecord(NamedTuple):
    """One whole-LHS store through an out parameter: the target `id` node,
    the assign, and its statement position. Newton's and lightLeak's
    owners write each parameter exactly once at top level, so the two
    defaulted fields stay at their defaults there; mandelbrot's owners
    write through nested if/else arms (33 stores), so each record also
    freezes the statement-nesting DEPTH and (its own tier) the statement
    hash."""

    parameter_id: int
    target_span: str
    target_sha256: str
    assign_span: str
    assign_sha256: str
    operator: str
    statement_index: int
    statement_kind: str
    statement_span: str
    statement_sha256: str = ""
    depth: int = 1


class OutReadRecord(NamedTuple):
    """One non-store reference to an out parameter inside its owner.
    Newton and lightLeak carry none (their write-once invariant); the
    record exists for keys whose owners legitimately READ an out
    parameter after storing it -- mandelbrot's z_final feeds
    ``dot(z_final, z_final)`` twice."""

    parameter_id: int
    parameter_name: str
    span: str
    node_sha256: str
    parent_kind: str
    owner_id: int
    owner_name: str
    statement_span: str


class OutCallSiteRecord(NamedTuple):
    """One call to an out-parameter function: identity, arity, the out
    arguments (always the last two), and the bare-call statement shape."""

    owner: str
    callee: str
    signature_id: int
    span: str
    sha256: str
    argument_count: int
    out_ordinals: tuple[int, ...]
    out_arguments: tuple[tuple[int, str, str, str, str], ...]
    statement_kind: str
    statement_span: str
    statement_sha256: str
    call_type: str
    statement_index: int


class DirectionContract(NamedTuple):
    """The frozen emission contract for out parameters.

    This record is *data the emitter must consume*. The design's §0.5
    hazard: the emitter's generic parameter path returns
    ``function_type(parameter.type)`` for any direction -- an admitted out
    parameter would be emitted by value, compile, and run silently wrong.
    ``by_value_emission`` is therefore frozen "forbidden" and
    ``emitter_direction_gate_required`` frozen True; the emitter lane's
    RED test deletes its direction gate and must see red exactly because
    nothing else would fire.

    ``parameter_abis`` (default empty -- newton's frozen record is
    unchanged) carries the per-parameter reference spelling when a key's
    out parameters have MIXED types: lightLeak's ``cell_color`` is a
    ``glsl::Vec3&`` but ``cell_dist`` is a plain ``float&``, because the
    JS authority materializes the vec3 as a pooled array and the float as
    a plain scalar.
    """

    native_abi: str
    pass_mechanism: str
    by_value_emission: str
    emitter_direction_gate_required: bool
    out_argument_native_shape: str
    js_body_tail: str
    js_out_stash: str
    js_call_shape: str
    js_out_allocation: str
    parameter_abis: tuple[tuple[str, str], ...] = ()


class JuliaOutArgumentRecord(NamedTuple):
    ordinal: int
    kind: str
    symbol_id: int | None
    glsl_type: str
    span: str
    direction: str


class JuliaOutCallRecord(NamedTuple):
    identity: tuple[str, str, int, str]
    arguments: tuple[JuliaOutArgumentRecord, ...]


class JuliaOutAdmissionRecord(NamedTuple):
    """Authenticated four-parameter Julia reference/out ABI census."""

    parameters: tuple[tuple[str, str, str, str, str], ...]
    stores: tuple[tuple[str, str, str], ...]
    calls: tuple[tuple[str, str, int, str], ...]
    call_arguments: tuple[JuliaOutCallRecord, ...]
    store_count: int
    call_count: int
    consumed_objects: tuple[object, ...]


_JULIA_CALL_ARGUMENTS = (
    JuliaOutCallRecord(
        ("df64_mul", "df64_split", 86, "113:5-113:30"),
        (JuliaOutArgumentRecord(0, "swizzle", None, "float",
                                "113:16-113:19", "in"),
         JuliaOutArgumentRecord(1, "id", 105, "float",
                                "113:21-113:24", "out"),
         JuliaOutArgumentRecord(2, "id", 106, "float",
                                "113:26-113:29", "out"))),
    JuliaOutCallRecord(
        ("df64_mul", "df64_split", 86, "114:5-114:30"),
        (JuliaOutArgumentRecord(0, "swizzle", None, "float",
                                "114:16-114:19", "in"),
         JuliaOutArgumentRecord(1, "id", 107, "float",
                                "114:21-114:24", "out"),
         JuliaOutArgumentRecord(2, "id", 108, "float",
                                "114:26-114:29", "out"))),
    JuliaOutCallRecord(
        ("df64_mul_f", "df64_split", 86, "123:5-123:30"),
        (JuliaOutArgumentRecord(0, "swizzle", None, "float",
                                "123:16-123:19", "in"),
         JuliaOutArgumentRecord(1, "id", 111, "float",
                                "123:21-123:24", "out"),
         JuliaOutArgumentRecord(2, "id", 112, "float",
                                "123:26-123:29", "out"))),
    JuliaOutCallRecord(
        ("df64_mul_f", "df64_split", 86, "124:5-124:28"),
        (JuliaOutArgumentRecord(0, "id", 46, "float",
                                "124:16-124:17", "in"),
         JuliaOutArgumentRecord(1, "id", 113, "float",
                                "124:19-124:22", "out"),
         JuliaOutArgumentRecord(2, "id", 114, "float",
                                "124:24-124:27", "out"))),
    JuliaOutCallRecord(
        ("iterateSmooth", "transformCoords", 99, "290:5-290:47"),
        (JuliaOutArgumentRecord(0, "id", 72, "vec2",
                                "290:21-290:30", "in"),
         JuliaOutArgumentRecord(1, "id", 75, "float",
                                "290:32-290:34", "in"),
         JuliaOutArgumentRecord(2, "id", 118, "vec2",
                                "290:36-290:40", "out"),
         JuliaOutArgumentRecord(3, "id", 119, "vec2",
                                "290:42-290:46", "out"))),
    JuliaOutCallRecord(
        ("main", "transformCoords", 99, "353:9-353:64"),
        (JuliaOutArgumentRecord(0, "id", 152, "vec2",
                                "353:25-353:36", "in"),
         JuliaOutArgumentRecord(1, "id", 154, "float",
                                "353:38-353:51", "in"),
         JuliaOutArgumentRecord(2, "id", 157, "vec2",
                                "353:53-353:57", "out"),
         JuliaOutArgumentRecord(3, "id", 158, "vec2",
                                "353:59-353:63", "out"))),
)


class CountedForSeedContract(NamedTuple):
    """The complete mechanism-A dict entry for the integration slice.

    Field-for-field a ``loop_proof._SOURCE_GLOBAL_LITERAL_INT_PROFILES``
    entry (the singular ``integer``/``reads`` schema): the live
    ``_asdict()`` entry and capability through ``analyze_program`` close rung
    1 (verified against the live tree; the
    next rejection is then ``60:50: unsupported parameter direction
    out``). The dict key lands with this module's row and the authority
    arms -- never before (the typed row remains a separate integration gate).
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
    return ValueError(f"{profile}: {message}")


def _check_ledger(entries: list, expected: int, label: str,
                  profile: str = NEWTON_PROFILE) -> None:
    identities = [id(item) for item in entries]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _profile_fail(profile, f"{label} visitation ledger mismatch")


# --- walkers (census discipline: global initializers included) ---------------

def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None,
                     grandparent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
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
    for declaration in program.declarations:
        if declaration.initializer is None:
            continue
        for item, parent, grandparent, path in _walk_expression(
                declaration.initializer):
            yield None, None, item, parent, grandparent, path, ()
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
    for function, _, item, _, _, path, _ in _program_nodes(program):
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


def _out_parameter_census(program: TypedProgram):
    """Every parameter with a non-``in`` direction, with its function and
    ordinal, in program order."""
    for function in program.functions:
        for ordinal, parameter in enumerate(function.parameters):
            if parameter.direction != "in":
                yield function, ordinal, parameter


def _out_reference_census(program: TypedProgram):
    """Every reference to an out parameter *inside its owning function*,
    classified: the whole-LHS store target vs. anything else. Derived per
    owner from the owner's own parameter list, so a reference to another
    function's out parameter is not silently co-opted."""
    for function in program.functions:
        function_out = {parameter.id for parameter in function.parameters
                        if parameter.direction != "in"}
        if not function_out:
            continue
        for index, statement in enumerate(function.body):
            for item, parent, grandparent, path, chain in _walk_statement(
                    statement, (index,)):
                if item.kind != "id" or item.symbol_id not in function_out:
                    continue
                is_store = (parent is not None and parent.kind == "assign"
                            and parent.children
                            and parent.children[0] is item)
                yield function, item, parent, chain, index, is_store


def _out_call_census(program: TypedProgram, callees: frozenset[str]):
    """Every call node to an out-parameter function, with its owner, its
    statement, and the out arguments (the frozen trailing ordinals)."""
    for function, _, item, parent, grandparent, path, chain in (
            _program_nodes(program)):
        if item.kind != "call" or item.callee not in callees:
            continue
        yield function, item, chain, path[0]


# --- mechanism-A (counted-for seed) helpers, lightLeak's lock only ----------

def _seed_symbol(program: TypedProgram, lock: dict):
    """The live bound Symbol for the lock's seed declaration."""
    for declaration in program.declarations:
        if declaration.symbol.id == lock["seed"]["symbol_id"]:
            return declaration.symbol
    return None


def _frozen_seed(program: TypedProgram, lock: dict):
    """The mechanism-A seed tuple exactly as semantic.py attaches it: the
    FROZEN bound value with the live symbol object."""
    return ((lock["seed"]["symbol_id"], lock["seed"]["value"],
             "source-global-const-literal", _seed_symbol(program, lock)),)


def _seed_declaration(program: TypedProgram, lock: dict):
    return next((item for item in program.declarations
                 if item.symbol.id == lock["seed"]["symbol_id"]), None)


def _base_symbol(node: TypedExpression) -> TypedExpression:
    """Strip swizzle/member/index chains down to the underlying `id`."""
    current = node
    while current.kind in ("swizzle", "member", "index") and current.children:
        current = current.children[0]
    return current


def _find_for(statements):
    for statement in statements:
        if statement.kind == "for":
            yield statement
        yield from _find_for(statement.children)


def _bare_call_census(program: TypedProgram) -> tuple:
    """Every bare void-call statement in the whole program: the sole
    expression of an ``expr`` statement whose call type is void (the
    wcSimplify/emitter-arm class). Mechanism D's census -- what proves the
    arm's admission set is exactly the out-call sites."""
    found = []

    def walk(value: TypedStatement, owner: TypedFunction) -> None:
        if (value.kind == "expr" and len(value.expressions) == 1
                and value.expressions[0].kind == "call"
                and value.expressions[0].type.display() == "void"):
            found.append((owner.name, _span(value),
                          value.expressions[0].callee))
        for child in value.children:
            walk(child, owner)

    for function in program.functions:
        for statement in function.body:
            walk(statement, function)
    return tuple(found)


def _mechanism_census(program: TypedProgram) -> tuple[int, int, int, int]:
    """(out/inout parameters, bare void-call statements, bit-operations,
    index expressions) -- lightLeak's ``(2, 2, 1, 0)``: the one ``uvec3 >>
    uint`` is the already-admitted vector form, frozen here only as the
    program's bit-op boundary."""
    out_parameters = sum(1 for function in program.functions
                         for parameter in function.parameters
                         if parameter.direction != "in")
    bare_calls = len(_bare_call_census(program))
    bit_operations = 0
    index_expressions = 0
    for _, _, item, _, _, _, _ in _program_nodes(program):
        if item.kind == "binary" and item.operator in _BITWISE_OPERATORS:
            bit_operations += 1
        if item.kind == "index":
            index_expressions += 1
    return (out_parameters, bare_calls, bit_operations, index_expressions)


# --- individually deletable locks -------------------------------------------
#
# One predicate, one message, one test each (the delete-the-check sweep).
# Value tiers run AHEAD of node identity tiers: Symbols and TypedExpression
# nodes embed their spans, so identity hashes would otherwise absorb
# value-level drift and make the value locks vacuous.

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
    """All thirteen functions WITH parameter directions -- the direction
    inventory is this module's subject, so a flipped direction must fail
    here by value, not only inside a fingerprint."""
    return _function_inventory(program) == lock["function_inventory"]


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


def _declaration_inventory_holds(program: TypedProgram, lock: dict) -> bool:
    return (len(program.declarations) == lock["declaration_count"]
            and _declaration_inventory(program)
            == lock["declaration_inventory"])


def _node_census_holds(total: int, assigns: int, lock: dict) -> bool:
    return total == lock["total_nodes"] and assigns == lock["total_assigns"]


def _out_parameter_census_holds(census: list, lock: dict) -> bool:
    """Exactly the four frozen out parameters: owner, ordinal, name, type,
    direction, and span. Value tier -- runs ahead of the Symbol hashes."""
    records = lock["out_parameters"]
    if len(census) != len(records):
        return False
    for (function, ordinal, parameter), record in zip(census, records):
        if (function.id != record.function_id
                or function.name != record.function_name
                or _span(function) != record.function_span
                or parameter.id != record.parameter_id
                or parameter.name != record.parameter_name
                or parameter.type.display() != record.glsl_type
                or parameter.direction != record.direction
                or ordinal != record.ordinal
                or _span(parameter) != record.parameter_span):
            return False
    return all(record.direction == "out" for record in records)


def _out_parameter_identity_holds(census: list, lock: dict) -> bool:
    """The four out-parameter Symbol hashes (the identity tier)."""
    return (tuple(_sha(parameter) for _, _, parameter in census)
            == tuple(record.parameter_sha256
                     for record in lock["out_parameters"]))


def _inout_parameter_census_holds(program: TypedProgram) -> bool:
    """The frozen ``inout`` census is EMPTY and there is no switch to
    loosen: newton carries no inout parameter, and the mechanism must not
    grow one without a new frozen record. (wcSimplify's ``inout vec3``
    swap is ``inout_vec3_swap_profile``'s carrier, not newton's.)"""
    return not any(parameter.direction == "inout"
                   for function in program.functions
                   for parameter in function.parameters)


def _out_write_shape_holds(stores: list, lock: dict) -> bool:
    """Each out-parameter store is the whole LHS of a plain ``=`` assign
    that is the sole expression of an ``expr`` statement in its owner, at
    the frozen statement index and (per record) nesting depth (value
    tier). The census is matched POSITIONALLY in visit order: newton's and
    lightLeak's owners write each parameter once at depth 1 (the
    defaulted fields), while mandelbrot's 33 stores live inside if/else
    arms at depths 1..11 -- a repeated parameter id cannot collapse the
    records the way a per-id dict would."""
    records = lock["out_stores"]
    if len(stores) != len(records):
        return False
    for (function, node, parent, chain, index, _), record in zip(
            stores, records):
        statement = chain[-1]
        if (record.parameter_id != node.symbol_id
                or parent.operator != record.operator
                or _span(parent) != record.assign_span
                or _span(node) != record.target_span
                or index != record.statement_index
                or statement.kind != record.statement_kind
                or _span(statement) != record.statement_span
                or len(statement.expressions) != 1
                or statement.expressions[0] is not parent
                or len(chain) != record.depth
                or (record.statement_sha256
                    and _sha(statement) != record.statement_sha256)):
            return False
    return True


def _out_write_only_holds(others: list, lock: dict) -> bool:
    """The write-only census: beyond the whole-LHS stores there is NOT ONE
    further reference to an out parameter inside its owner EXCEPT the
    frozen read records the lock itself carries. Newton and lightLeak
    freeze none (their write-once invariant, ``not others``); mandelbrot
    freezes exactly two z_final reads, so any third non-store reference
    fails here by name."""
    return len(others) == len(lock.get("out_reads", ()))


def _out_read_shape_holds(reads: list, lock: dict) -> bool:
    """Every frozen non-store reference by value: the parameter, its owner,
    its span, its parent's kind and its enclosing statement span. A read
    planted anywhere else (or a store converted to a compound target,
    which re-classifies it as a non-store reference) fails here."""
    records = lock.get("out_reads", ())
    if len(reads) != len(records):
        return False
    for (function, node, parent, chain, index, _), record in zip(
            reads, records):
        if (function.id != record.owner_id
                or function.name != record.owner_name
                or node.symbol_id != record.parameter_id
                or node.symbol.name != record.parameter_name
                or _span(node) != record.span
                or parent is None
                or parent.kind != record.parent_kind
                or _span(chain[-1]) != record.statement_span):
            return False
    return True


def _out_read_identity_holds(reads: list, lock: dict) -> bool:
    """The frozen reads' node hashes (the identity tier)."""
    return (tuple(_sha(node) for _, node, _, _, _, _ in reads)
            == tuple(record.node_sha256
                     for record in lock.get("out_reads", ())))


def _out_write_identity_holds(stores: list, lock: dict) -> bool:
    """The store target/assign node hashes (the identity tier)."""
    return (tuple((_sha(node), _sha(parent))
                  for _, node, parent, _, _, _ in stores)
            == tuple((record.target_sha256, record.assign_sha256)
                     for record in lock["out_stores"]))


def _out_call_census_holds(census: list, lock: dict) -> bool:
    """Exactly 3 calls to the two out-functions, all in ``main``, with the
    frozen arities and the out arguments at the frozen trailing ordinals
    (value tier)."""
    records = lock["out_calls"]
    if len(census) != len(records):
        return False
    for (function, node, chain, index), record in zip(census, records):
        if (function.name != record.owner
                or node.callee != record.callee
                or node.signature_id != record.signature_id
                or len(node.children) != record.argument_count
                or node.type.display() != record.call_type
                or index != record.statement_index):
            return False
        for ordinal, argument in zip(record.out_ordinals,
                                     record.out_arguments):
            if ordinal >= len(node.children):
                return False
            child = node.children[ordinal]
            if (child.kind != "id" or child.symbol is None
                    or child.symbol_id != argument[0]
                    or child.symbol.name != argument[1]
                    or child.symbol.storage != argument[2]
                    or child.type.display() != argument[3]
                    or _span(child) != argument[4]
                    or child.category != "lvalue"):
                return False
    return True


def _out_call_identity_holds(census: list, lock: dict) -> bool:
    """The three call spans and node hashes (the identity tier)."""
    return (tuple((_span(node), _sha(node)) for _, node, _, _ in census)
            == tuple((record.span, record.sha256)
                     for record in lock["out_calls"]))


def _void_statement_shape_holds(census: list, lock: dict) -> bool:
    """Every out-call is a BARE VOID-CALL statement: the sole expression of
    an ``expr`` statement (the documented wcSimplify class -- the emitter
    gap this census hands to the §12-arm widening, M4). Bare means
    sole-expression: two of the three sites sit inside ``main``'s loops
    (the j-loop and the n-loop), so nesting is legitimate and is frozen
    per-site by the statement spans/hashes instead."""
    for (function, node, chain, index), record in zip(census,
                                                      lock["out_calls"]):
        statement = chain[-1]
        if (statement.kind != record.statement_kind
                or _span(statement) != record.statement_span
                or _sha(statement) != record.statement_sha256
                or len(statement.expressions) != 1
                or statement.expressions[0] is not node):
            return False
    return True


def _direction_contract_holds(contract: DirectionContract,
                              lock: dict) -> bool:
    """The frozen direction contract, validated against the predicate's
    own constants (never ``contract == lock[...]`` -- that would compare
    the record with itself and hold vacuously under record tampering):
    reference passing, by-value emission forbidden, the emitter direction
    gate required, and the quote-verified JS authority notes -- per key,
    because lightLeak's authority materializes a MIXED out-argument shape
    (pooled vec3, scalar float) that newton's all-Vec2 quotes do not
    name."""
    if lock["profile"] == LIGHTLEAK_PROFILE:
        return (contract.native_abi == LIGHTLEAK_NATIVE_ABI
                and contract.parameter_abis
                == (("cell_color", "glsl::Vec3&"), ("cell_dist", "float&"))
                and contract.pass_mechanism == "reference"
                and contract.by_value_emission == "forbidden"
                and contract.emitter_direction_gate_required is True
                and contract.js_out_stash == LIGHTLEAK_JS_OUT_STASH
                and contract.js_call_shape == LIGHTLEAK_JS_CALL_SHAPE
                and contract.js_body_tail == LIGHTLEAK_JS_BODY_TAIL
                and contract.js_out_allocation == LIGHTLEAK_JS_OUT_ALLOCATION
                and contract.out_argument_native_shape == LIGHTLEAK_NATIVE_SHAPE)
    if lock["profile"] == MANDELBROT_PROFILE:
        # mandelbrot's ten out parameters are a MIXED shape across THREE
        # owners: pooled-vec2 references for getPOI/transformCoords_df64/
        # z_final/dz_final, and binary64 references for all four scalar outs.
        # The JS scalar out stash is plain Number storage: even a value that
        # entered through a Float32 builtin remains binary64 through later
        # `+=`/output arithmetic.
        # The JS authority stashes per function -- mandelbrot_df64's stash
        # text appears at BOTH return arms -- writes getPOI's arms
        # lane-wise, and allocates vec2 args as pooled pairs / float args
        # as plain zeros at every one of the five call sites.
        return (contract.parameter_abis
                == (("cX_df", "glsl::Vec2&"), ("cY_df", "glsl::Vec2&"),
                    ("smoothIter", "double&"), ("rawIter", "double&"),
                    ("z_final", "glsl::Vec2&"), ("dz_final", "glsl::Vec2&"),
                    ("stripeAcc", "double&"), ("trapMin", "double&"),
                    ("re_df", "glsl::Vec2&"), ("im_df", "glsl::Vec2&"))
                and contract.pass_mechanism == "reference"
                and contract.by_value_emission == "forbidden"
                and contract.emitter_direction_gate_required is True
                and contract.js_out_stash == MANDELBROT_JS_OUT_STASH
                and contract.js_call_shape == MANDELBROT_JS_CALL_SHAPE
                and MANDELBROT_JS_GETPOI_LANE_WRITE in contract.js_body_tail
                and MANDELBROT_JS_GETPOI_STASH in contract.js_body_tail
                and MANDELBROT_JS_TRANSFORM_STASH in contract.js_body_tail
                and MANDELBROT_JS_VEC2_ALLOCATION
                in contract.js_out_allocation
                and MANDELBROT_JS_FLOAT_ALLOCATION
                in contract.js_out_allocation
                and "caller-local" in contract.out_argument_native_shape)
    return (contract.native_abi == "glsl::Vec2&"
            and contract.pass_mechanism == "reference"
            and contract.by_value_emission == "forbidden"
            and contract.emitter_direction_gate_required is True
            and ".reduce((res,el,i)=>(res[i] = el, res), rr)"
            in contract.js_body_tail
            and contract.js_out_stash == "df64_cmul.__out__ = [rr, ri]"
            and "[tr, ti] = df64_cmul.__out__" in contract.js_call_shape
            and "PooledFloat32Array([0, 0])" in contract.js_out_allocation
            and "caller-local" in contract.out_argument_native_shape)


# --- lightLeak's mechanism-A locks (evaluated only for locks with a seed) ----

def _counted_rebuild_holds(program: TypedProgram, lock: dict) -> bool:
    """The submitted proof tree equals the tree rebuilt from the frozen
    seed: attach the frozen bound onto the submitted functions (attach
    clears proofs itself) and require the exact submitted functions and
    summary back. A tree that merely CLAIMS the closed summary dies here."""
    rebuilt = attach_counted_loop_proofs(
        program.functions, program.key,
        source_global_bounds=_frozen_seed(program, lock))
    return (program.functions == rebuilt
            and program.counted_loop_proof
            == summarize_counted_loop_proofs(rebuilt))


def _seed_declaration_holds(program: TypedProgram, lock: dict) -> bool:
    """The bound global is a bare positive int-literal const named
    POINT_COUNT with the frozen value -- loop_proof's own declaration
    checks, evaluated on the live declaration ahead of the identity
    hashes. (The seed tuple itself carries the FROZEN value, so a drifted
    declaration literal is invisible to the bound machinery and only this
    lock can catch it.)"""
    expected = lock["seed"]
    declaration = _seed_declaration(program, lock)
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
                initializer.literal if initializer.literal else "")
            is not None)


def _seed_identity_holds(program: TypedProgram, lock: dict) -> bool:
    """The seed declaration's span and node hashes (declaration, Symbol,
    initializer literal)."""
    expected = lock["seed"]
    declaration = _seed_declaration(program, lock)
    if declaration is None or declaration.initializer is None:
        return False
    return (_span(declaration), _sha(declaration),
            _sha(declaration.symbol),
            _sha(declaration.initializer)) == (
        expected["span"], expected["declaration_sha256"],
        expected["symbol_sha256"], expected["initializer_sha256"])


def _globals_census_holds(program: TypedProgram, lock: dict) -> bool:
    """Both source globals with their literal texts -- the same census
    loop_proof's dict entry freezes."""
    return tuple(
        (item.symbol.name, item.symbol.id, item.type.display(),
         item.initializer.literal if item.initializer is not None else None)
        for item in program.declarations
        if item.symbol.storage not in {"uniform", "output"}) == \
        lock["globals"]


def _no_seed_write_holds(program: TypedProgram,
                         seed_ids: set[int]) -> bool:
    """The seed const is never a mutation target anywhere (assign,
    ``++``/``--``), through any swizzle/member/index chain; global
    declaration initializers are walked too, so a reference planted in one
    is refused here as well."""
    for _, _, item, _, _, _, _ in _program_nodes(program):
        if item.kind not in _MUTATION_KINDS or not item.children:
            continue
        if item.kind != "assign" and item.operator not in (
                _INCREMENT_OPERATORS):
            continue
        if _base_symbol(item.children[0]).symbol_id in seed_ids:
            return False
    return True


def _seed_reads_holds(program: TypedProgram, lock: dict) -> bool:
    """Exactly the frozen id-node reads: the loop bound alone
    (``voronoiCell 65:25-65:36`` -- lightLeak's POINT_COUNT has exactly
    ONE read, unlike parallax's two)."""
    identifier = lock["seed"]["symbol_id"]
    reads = []
    for function, _, item, _, _, _, _ in _program_nodes(program):
        if item.kind != "id" or item.symbol_id != identifier:
            continue
        owner = "<global-initializer>" if function is None else function.name
        owner_id = -1 if function is None else function.id
        span = item.span
        reads.append((owner, owner_id,
                      span.start_line, span.start_column,
                      span.end_line, span.end_column))
    return tuple(reads) == lock["reads"]


def _voronoi_loop_holds(program: TypedProgram, lock: dict) -> bool:
    """The one loop's complete proof shape at its frozen span in
    ``voronoiCell`` (lightLeak's seed-side loop lock)."""
    expected = lock["voronoi_loop"]
    owners = [item for item in program.functions
              if item.id == expected["owner"][0]
              and item.name == expected["owner"][1]]
    if len(owners) != 1:
        return False
    for statement in _find_for(owners[0].body):
        if _span(statement) != expected["span"]:
            continue
        proof = statement.loop_proof
        return (proof is not None
                and proof.induction_symbol_id
                == expected["induction_symbol_id"]
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


def _mechanism_census_holds(program: TypedProgram, lock: dict) -> bool:
    """(out params, bare calls, bit-ops, index expressions): the
    program-wide mechanism boundary. lightLeak freezes (2, 2, 1, 0) --
    the emitter arm's bare-call admission set is exactly the two
    out-call statements, and the single ``uvec3 >> uint`` is the
    already-admitted vector form; mandelbrot freezes (10, 5, 0, 0) --
    the design's decomposition with the corrected owner split and the
    five-call census. mandelbrot's loop-shape lock lives in
    log_admission_profile (its seed contract's owner); here the
    seed-attached summary rides the call-graph lock's tuple."""
    return _mechanism_census(program) == lock["mechanism_census"]


# --- frozen per-key records (all measured this session) ----------------------

_OUT_PARAMETERS = (
    OutParameterRecord(62, "df64_cmul", "98:1-101:2",
                       48, "rr", "vec2", "out", 4,
                       "98:52-98:63",
                       "2eb649a97a3ce8dc01fa6d53d008096534e7a95baa9ffe71a6c5117f7ebe94f6"),
    OutParameterRecord(62, "df64_cmul", "98:1-101:2",
                       49, "ri", "vec2", "out", 5,
                       "98:65-98:76",
                       "f65105af7c0c2ff6fe40d266bf0ddaead3171a3a2a6cd8de30f895b9d56b8634"),
    OutParameterRecord(73, "transformCoords_df64", "107:1-119:2",
                       55, "re_df", "vec2", "out", 5,
                       "108:38-108:52",
                       "6dba9d714bc3c3561fe5b5c350ef7159b64de4e70e820f285b08935ccc460e89"),
    OutParameterRecord(73, "transformCoords_df64", "107:1-119:2",
                       56, "im_df", "vec2", "out", 6,
                       "108:54-108:68",
                       "4984a38a81750b607634f6815c5fdf90ca2642766f4c013f64069d9e6c747186"),
)

_OUT_STORES = (
    OutStoreRecord(48, "99:5-99:7",
                   "65b07a50ad0883e5a2a8ebce786fbbe140770ecf77b2edb179b89158b01a868c",
                   "99:5-99:54",
                   "ad032a7144eac5581f7eae8f97f8ead5a9d49bb56f0fa35a77621ed2cf2ed8ef",
                   "=", 0, "expr", "99:5-99:55"),
    OutStoreRecord(49, "100:5-100:7",
                   "e7abc259bc24d2872c0858fe2e362443ab258c63aa20177683def444c4a321c9",
                   "100:5-100:54",
                   "4fc889461880c04b6584b73d581ef6225ca682670e0fd084ec0bfb2531aecdba",
                   "=", 1, "expr", "100:5-100:55"),
    OutStoreRecord(55, "117:5-117:10",
                   "d5f4eae190f5028291bf3bad1cc23dd991e691930d081ca468980760ec5b78a2",
                   "117:5-117:38",
                   "e2b946d73995c97fdef80372e68bbdbd959fb7aa5c2984b267062cb07cb9bf85",
                   "=", 8, "expr", "117:5-117:39"),
    OutStoreRecord(56, "118:5-118:10",
                   "206b26d8bf44c10e0ae0a3641fcf13eccb41c3500cc00ce97345a854a73e97ef",
                   "118:5-118:38",
                   "236d26b5e293e4baf3c38680091f73d24a8a7480579b95f8890f16c2113a109c",
                   "=", 9, "expr", "118:5-118:39"),
)

_OUT_CALLS = (
    OutCallSiteRecord(
        "main", "transformCoords_df64", 73, "197:5-198:55",
        "0b9bdcaf64c42b39838deac3163c845907f6dd0b0e3efa9f5b53b2d31fe5cb2a",
        7, (5, 6),
        ((104, "re_df", "local", "vec2", "198:42-198:47"),
         (105, "im_df", "local", "vec2", "198:49-198:54")),
        "expr", "197:5-198:56",
        "792505d1f2d9dec94e2a3c14fbaa09ecd8f2ada41e560ff1aa678c7dc6e57a6e",
        "void", 15),
    OutCallSiteRecord(
        "main", "df64_cmul", 62, "230:13-230:54",
        "4fd77ca7ef31b7347ee540f3e022e357c46e6934d94110aba30e67d5a5f27140",
        6, (4, 5),
        ((121, "tr", "local", "vec2", "230:47-230:49"),
         (122, "ti", "local", "vec2", "230:51-230:53")),
        "expr", "230:13-230:55",
        "5ff3b4343c1055667e0a7ebfd1556fbf968777eba15590ba1eb0b1af0a7bf7fe",
        "void", 26),
    OutCallSiteRecord(
        "main", "df64_cmul", 62, "237:9-237:52",
        "6688cba4637b605c3be7bee80218208eb0d271c6d5ab617a6202588ec3aa2fa6",
        6, (4, 5),
        ((123, "znr", "local", "vec2", "237:43-237:46"),
         (124, "zni", "local", "vec2", "237:48-237:51")),
        "expr", "237:9-237:53",
        "0d2f0ddc43cd75510e3931f5f835773717fe0b5284df1d259345133828eab358",
        "void", 26),
)

_DIRECTION_CONTRACT = DirectionContract(
    native_abi="glsl::Vec2&",
    pass_mechanism="reference",
    by_value_emission="forbidden",
    emitter_direction_gate_required=True,
    out_argument_native_shape="caller-local glsl::Vec2, uninitialized before "
                              "the call (JS pre-allocates PooledFloat32Array "
                              "[0, 0])",
    js_body_tail="df64_sub(df64_mul(ar, br), df64_mul(ai, bi))"
                 ".reduce((res,el,i)=>(res[i] = el, res), rr)",
    js_out_stash="df64_cmul.__out__ = [rr, ri]",
    js_call_shape="(df64_cmul(pwr, pwi, zr_df, zi_df, tr, ti), "
                  "[tr, ti] = df64_cmul.__out__, df64_cmul.__return__)",
    js_out_allocation="var tr = new $runtime.PooledFloat32Array([0, 0]), "
                      "ti = new $runtime.PooledFloat32Array([0, 0])",
)

# --- lightLeak's frozen records (all measured this session) ------------------

_LIGHTLEAK_OUT_PARAMETERS = (
    OutParameterRecord(29, "voronoiCell", "60:1-85:2",
                       20, "cell_color", "vec3", "out", 3,
                       "60:50-60:69",
                       "b7d12aa9c9f773dd8207732234f17ccb2a1dc02ebf02acca"
                       "2cef9de53160b33e"),
    OutParameterRecord(29, "voronoiCell", "60:1-85:2",
                       21, "cell_dist", "float", "out", 4,
                       "60:71-60:90",
                       "3ab1928af21f19450a2318bf1caa838722fa9da9b5e74fcf7"
                       "5d19258b0d3dbf2"),
)

_LIGHTLEAK_OUT_STORES = (
    OutStoreRecord(20, "83:5-83:15",
                   "a052955a46739dce7219c30a0bff777429fe2c944ed4ccd85e9"
                   "0b7c44781098d",
                   "83:5-83:44",
                   "92d8f305210eea7503d78e630f57c27b22d6983a2bcc5b48102"
                   "ef3428a07d938",
                   "=", 5, "expr", "83:5-83:45"),
    OutStoreRecord(21, "84:5-84:14",
                   "0a7ddb4b0cc591ab8299b1818bf106f03df0d3f1f3053bb0bf7"
                   "54a83f766f66c",
                   "84:5-84:26",
                   "10776b063861622335ab15d59c56af51383ab339cbf0f3ed2a2d"
                   "3ce3e0b28486",
                   "=", 6, "expr", "84:5-84:27"),
)

_LIGHTLEAK_OUT_CALLS = (
    OutCallSiteRecord(
        "main", "voronoiCell", 29, "114:5-114:53",
        "f416baee19ffe0411c4d8f2ffc8aa7c341bd333de30a9a2f3e5cc6821e7c7292",
        5, (3, 4),
        ((45, "base_cell", "local", "vec3", "114:32-114:41"),
         (46, "base_dist", "local", "float", "114:43-114:52")),
        "expr", "114:5-114:54",
        "09373f0bea4bd4bd98340fd943369d673737e0a798902e02e739af340e86d902",
        "void", 12),
    OutCallSiteRecord(
        "main", "voronoiCell", 29, "125:5-125:60",
        "80acfba4e667482380bc0bdb90d9591dce1af276fdddee91101b65a567ec5368",
        5, (3, 4),
        ((51, "warp_cell", "local", "vec3", "125:39-125:48"),
         (52, "warp_dist", "local", "float", "125:50-125:59")),
        "expr", "125:5-125:61",
        "4727c99119491cded56b7b9405c42f69c3da56bebc13df279af7aa2ff567b300",
        "void", 19),
)

_LIGHTLEAK_DIRECTION_CONTRACT = DirectionContract(
    native_abi=LIGHTLEAK_NATIVE_ABI,
    pass_mechanism="reference",
    by_value_emission="forbidden",
    emitter_direction_gate_required=True,
    out_argument_native_shape=LIGHTLEAK_NATIVE_SHAPE,
    js_body_tail=LIGHTLEAK_JS_BODY_TAIL,
    js_out_stash=LIGHTLEAK_JS_OUT_STASH,
    js_call_shape=LIGHTLEAK_JS_CALL_SHAPE,
    js_out_allocation=LIGHTLEAK_JS_OUT_ALLOCATION,
    parameter_abis=(("cell_color", "glsl::Vec3&"),
                    ("cell_dist", "float&")),
)

# --- mandelbrot's frozen records (all measured this session, over
# the seed-attached tree) ---------------------------------------------

_MANDELBROT_OUT_PARAMETERS = (
    OutParameterRecord(106, 'getPOI', '117:1-146:2',
                       43, 'cX_df', 'vec2', 'out', 1,
                       '117:24-117:38',
                       '5d75de67d60033282515b3f2e4ae57eddbfaa531cd453af86bcc09370b1eb759'),
    OutParameterRecord(106, 'getPOI', '117:1-146:2',
                       44, 'cY_df', 'vec2', 'out', 2,
                       '117:40-117:54',
                       '57b031c1ff10af15922d6ec399b14a152b86b93704cba7ff09a9afcf10e04be0'),
    OutParameterRecord(111, 'mandelbrot_df64', '203:1-280:2',
                       61, 'smoothIter', 'float', 'out', 3,
                       '204:22-204:42',
                       '9c7a9822a27438bfd81fbf25b6bdbd838601b4f0d76a414c222f0deab695a272'),
    OutParameterRecord(111, 'mandelbrot_df64', '203:1-280:2',
                       62, 'rawIter', 'float', 'out', 4,
                       '204:44-204:61',
                       '58d6524b48ea5054b5cfda78ba50c0849e9d85e563831009d3cacf799b1d9032'),
    OutParameterRecord(111, 'mandelbrot_df64', '203:1-280:2',
                       63, 'z_final', 'vec2', 'out', 5,
                       '205:22-205:38',
                       '45a7e15389301634f3c1b696df2d5e7f729b2eb107d217c74f9ea7040a4e69b6'),
    OutParameterRecord(111, 'mandelbrot_df64', '203:1-280:2',
                       64, 'dz_final', 'vec2', 'out', 6,
                       '205:40-205:57',
                       '08a0c743d67eab480e2687f29bcefd42f3f0356632acfa1bc933ed1ca7db9187'),
    OutParameterRecord(111, 'mandelbrot_df64', '203:1-280:2',
                       65, 'stripeAcc', 'float', 'out', 7,
                       '206:22-206:41',
                       '09ffe3042fd8feaec8c26445d5c35a20a2c942a51fd3c6c09391f969f876eb91'),
    OutParameterRecord(111, 'mandelbrot_df64', '203:1-280:2',
                       66, 'trapMin', 'float', 'out', 8,
                       '206:43-206:60',
                       '7e62ec29dfde9f907d120229003d000d8ac724787687a487097d390d1fe2a293'),
    OutParameterRecord(117, 'transformCoords_df64', '153:1-165:2',
                       50, 're_df', 'vec2', 'out', 5,
                       '154:27-154:41',
                       '140e1c7b10c32bd225e306bbcbc487a1ca9c18123e138fe7d85132b66e09d436'),
    OutParameterRecord(117, 'transformCoords_df64', '153:1-165:2',
                       51, 'im_df', 'vec2', 'out', 6,
                       '154:43-154:57',
                       '4b3d3aa28fb9e93e6df20c5e879c565fe66dc98cf73d093492c2bb1a9f67976e'),
)
_MANDELBROT_OUT_STORES = (
    OutStoreRecord(43, '120:9-120:14',
                   'a5846b30a45acccfec9e7fb5113494896ef98971611c2597140db7905f0c2d65',
                   '120:9-120:60',
                   '7b01d822ab6bd86f0ba4df91fc871882492f51b3820195900773ded0b7ba787e',
                   '=', 0, 'expr', '120:9-120:61',
                   '9c9a86fee309b3c712f2249f19c439fe3ce7203fbe43b0978c9bdd501010da2f', 3),
    OutStoreRecord(44, '121:9-121:14',
                   '47ed9e1563568ad8940a2cf3dbfac089894cdf6f913954f4e494d4dc9ec82aa7',
                   '121:9-121:60',
                   '716a5d710aecd24d5d29b505bc4176ed5122f6892580d66a42064bf402a8e6a0',
                   '=', 0, 'expr', '121:9-121:61',
                   '281a1a5237987d920ac9d13456db974c8a54f7188866298dbaa78ee44742f514', 3),
    OutStoreRecord(43, '123:9-123:14',
                   '495c576106b3d17c7e2411c3397aeb065ba509d0e5db76428b0d5c4d36dae739',
                   '123:9-123:61',
                   'd4091adecd2c37210630764585772db3a4c2107a22be8afad56a5ee6c62b0138',
                   '=', 0, 'expr', '123:9-123:62',
                   'e3f2afd8812fb693b0d4f6c0b5e4451c80c2ef7440ba3a752a62175591e9b5a9', 4),
    OutStoreRecord(44, '124:9-124:14',
                   'edfe7ee9923d3b0a91bfac55e1893f387afbb31eacc89bca9b836724c94a61df',
                   '124:9-124:63',
                   '5fb395fae3131b5c1ca95bcbbe660fa59be726e844afef502deaef655042b2be',
                   '=', 0, 'expr', '124:9-124:64',
                   '62cfd70c1e09079ac59478a487ff78a43e00423198a8be969b576703533f6c50', 4),
    OutStoreRecord(43, '126:9-126:14',
                   '31bdf31e330403b7e89003f07ec24985a5d99e795670b0dde04c90e293cd82b4',
                   '126:9-126:59',
                   '2493d4786e60a6938a48ac7a650696bebc5610dacda4e5d6b7aaef7f8817f0d7',
                   '=', 0, 'expr', '126:9-126:60',
                   '2714503720064edf8a9fe7e86156078b64eac394c643d264ec1788d874448383', 5),
    OutStoreRecord(44, '127:9-127:14',
                   'b86d395e538fc9dcd7f67ebb0bea425a1a9e4fb1c0fe2cc03cc594c9bbb27c03',
                   '127:9-127:32',
                   '44f85da34883eb9e31b505f02a9690ebdf2145cb08c06c8014920b77e649e257',
                   '=', 0, 'expr', '127:9-127:33',
                   '93f968a873f7ef27ab849a68b28ea98bbf03b7addfff30c524d733d58d140546', 5),
    OutStoreRecord(43, '129:9-129:14',
                   '9e335771951068d756dbfd5c3f268b051bc6ee774acc76ccafdefcde5f9db28e',
                   '129:9-129:60',
                   'a0767f1af243009fb43aadc8de0927b83ec24b922e7878ace58aed7962104f78',
                   '=', 0, 'expr', '129:9-129:61',
                   'fdb582165c96099e3e392115d73b362ebfccc9e66666f1ceb1160c4dbffd8bd4', 6),
    OutStoreRecord(44, '130:9-130:14',
                   '36a3ab293b0dfaa76c267747651e4696b506440da2520456974aa01c3fcd87a5',
                   '130:9-130:62',
                   '485bb1f16da2053284324e85f4bcd2dfc7620a64d33ce8e9f5f38e15a85440f3',
                   '=', 0, 'expr', '130:9-130:63',
                   '7d1ee1d4d23fa32616028e537e9f3748fc78a97956ad79a8431de921d8d12f2d', 6),
    OutStoreRecord(43, '132:9-132:14',
                   '4d3202efcb75f258ebf2114b3c01fddc28bc60b3b68c26bb6d0c380d95952df8',
                   '132:9-132:59',
                   '3ab3629a154d678574051781c7e70593e28fe96f4d0a20ad06253a1236a61865',
                   '=', 0, 'expr', '132:9-132:60',
                   'fdbce95b0e57a049ac41606f812fa2fb2f7136f1ba23116ece0f9ddf52c8a4e7', 7),
    OutStoreRecord(44, '133:9-133:14',
                   'db592fa625a9f9cd56368ed9dceaeb2d9ede5315c352a05260847bf564b064f1',
                   '133:9-133:32',
                   '204b81e299cfe382c91eb6ff7459e99e377bf3296cebb7832c226db5a4f3b869',
                   '=', 0, 'expr', '133:9-133:33',
                   'ff6eb17dcc2c7b7d08aba50c052a8539499ad760811168823c408307eb4c06f6', 7),
    OutStoreRecord(43, '135:9-135:14',
                   'a84e4f808d832eb7b4044891bcd388f4291ebcce0daf309dbb229dd7d4e02739',
                   '135:9-135:61',
                   '2dc113d9d0997259d1f9eb6d24e94ef01e639a86c7ad15e525338a29684d0135',
                   '=', 0, 'expr', '135:9-135:62',
                   'd104eb6909bcebfe32a77d071e45a0bf1c4c3ab975da2029f80f7a71c293bdad', 8),
    OutStoreRecord(44, '136:9-136:14',
                   '5fcb2500b4dc70e021db52496c8a7c75cdfda02886792c1ded9ed43558e1e6d8',
                   '136:9-136:61',
                   '9ffb43dd65461035b1c5c7df6b7bdd300a9d3c6acd890e7e342db4d61de32301',
                   '=', 0, 'expr', '136:9-136:62',
                   '997f35ba780df8a4502df9bafa3294edd69af1d0b3ec80ea88a37cb021e9095e', 8),
    OutStoreRecord(43, '138:9-138:14',
                   '227d9b5a1a9f9ca4f39b4ed054a5a66020dcb9d7756e96e511634d0e1e7149a8',
                   '138:9-138:60',
                   'b04941dc10ca0ce504ba46dc108264a6e246d06972b68c453dde9751ad5edf7f',
                   '=', 0, 'expr', '138:9-138:61',
                   'a1157538637160cbccc3ceeb0216d26df1fcbe94d0bd00ced626a8e02ce31431', 9),
    OutStoreRecord(44, '139:9-139:14',
                   '8d78da8866bbc61abc2a0b6892c1d5d714bb81dd98515e927b985f0c589f729a',
                   '139:9-139:62',
                   '23c8a66f579ec620fce3f4bcfd81bd8d6d5be4daac2fe0836747eb4c5d08758b',
                   '=', 0, 'expr', '139:9-139:63',
                   '106191e63f92aea7431880e6478ec77c34d431ae5560a407c860d7f609f80c1e', 9),
    OutStoreRecord(43, '141:9-141:14',
                   '48c0f57dbaf7f4e1017d7b9c4137a206eddaec44e1f5755684fa42b8d715014a',
                   '141:9-141:60',
                   '9bc5f90b931d55a4b142b39788215e05659887e0b20cd6a95a332c85d86a689a',
                   '=', 0, 'expr', '141:9-141:61',
                   '27c719eedd0b96b4f2aa6f2c12a62bcf014e72f95329421a017d397fa758e983', 10),
    OutStoreRecord(44, '142:9-142:14',
                   '536876c843d448613222e24543bf5716bfe8815d8405c673d9ad60ab0976035b',
                   '142:9-142:60',
                   '0e76d429a92df48bae0c7b035b8ac9d56be813b4a74a8706cacf115d060fbdfb',
                   '=', 0, 'expr', '142:9-142:61',
                   '6c38b15c54165f4c7d902d4b835ed3e66fdf30b71b555a6c192e1680e7f6d9d4', 10),
    OutStoreRecord(43, '144:9-144:14',
                   '4c814c8a854cc1a77959277e4e12c8b80e90ad0cbb9be3f28f7a1fb3544b57d7',
                   '144:9-144:43',
                   '19056473dadec684383836944991db75a3f6311c3a918fd90dc5c6ee3a245999',
                   '=', 0, 'expr', '144:9-144:44',
                   '344b9b284745d96f973b7425e5076b3a65021f6648b13325bda187d36edf7a56', 10),
    OutStoreRecord(44, '144:46-144:51',
                   '7dbcc4ff23e5e7c883330c5af0281193cce600c79a5d0292ff0d61c918cbc828',
                   '144:46-144:80',
                   '42008d8b8a54c9553a8637eb0b04d63fb08b6176d9a21a60625bc18584ad4db6',
                   '=', 0, 'expr', '144:46-144:81',
                   '60c7dc8e1447eeb4aeb67aa8f3f7ecf5050b330b67364a6cc989232d7d2610e1', 10),
    OutStoreRecord(61, '211:9-211:19',
                   'f862c44376d895059f13ec78987f23aa75f05851d9e97d0300821708621dff8d',
                   '211:9-211:36',
                   '060c24cbf056d041958385ab04dfcf66974c367df32c03a9d5a8c46703c11e14',
                   '=', 2, 'expr', '211:9-211:37',
                   'e9d74439d3f12f650132910f9fca97f4867b46484e764e62617841825affc03a', 3),
    OutStoreRecord(62, '212:9-212:16',
                   'd25dbdebab5a75a454531093e3a1ab5918ec1aa2ec837cae36a3a9f81fbedf1b',
                   '212:9-212:33',
                   '82e054af4842dec67b0723718b27e1d5aefbae0eb281293825cc5a8345a21180',
                   '=', 2, 'expr', '212:9-212:34',
                   '3dd5e79a4932d4bc05bbbc8544f6fa475b18e12780b2f2c01b651772fe87c53c', 3),
    OutStoreRecord(63, '213:9-213:16',
                   '239b377db150c8ecda1a47ad988453bf7ca283af131a2acdfb5370ae841b7be4',
                   '213:9-213:28',
                   '5a628b07268898b84e41c89f8b5fe14c445c033a8d979d0f8638b8e967adc60c',
                   '=', 2, 'expr', '213:9-213:29',
                   'c2dfe21ab7c2bc3f142aa71c9595f6ffd8ea88969117d122fbe26330a19f1c77', 3),
    OutStoreRecord(64, '214:9-214:17',
                   'c9e79f8b463f5cd072cfcb09eb8217b72d0bb8100b84b837b397b9ba305660be',
                   '214:9-214:29',
                   '36f7d69d0f47fd34747434467e5c57e363d52f795d5190f13a83f2a536268df4',
                   '=', 2, 'expr', '214:9-214:30',
                   '89dfaacd29907c2f09fe01b61faf5a99244a235dd3079b5d5ffac99f970f2353', 3),
    OutStoreRecord(65, '215:9-215:18',
                   '3c2f4862be5ee70c99be67d3e83e0a82e6c1f2c984e53b440ec2baafaf3e0ca9',
                   '215:9-215:24',
                   '65bb48d717833fd1c8f036d58dff02abfa8b79297bfc0c2f6242bfd513631d92',
                   '=', 2, 'expr', '215:9-215:25',
                   '486d29d5a165ec9fc8c04a76218a8d6810b87b7f23b262cb45e0ddd17c0f5b0b', 3),
    OutStoreRecord(66, '216:9-216:16',
                   '11dc41b63064777c6b6a13e5953e17258751c748f4f3f55639f11ed4502ed654',
                   '216:9-216:23',
                   'eebe5a9f475bb5bcff20a8f559bf3e521f6961bb7e20daf12fc155fefee18314',
                   '=', 2, 'expr', '216:9-216:24',
                   'c64bf4296df2586d6393dc6a4989f35f3876965403065735ceaf9f9253700ff0', 3),
    OutStoreRecord(62, '264:5-264:12',
                   '086d1aefcc76879b4dacae652a6b0488fc8bd57ca8f2bfd31c854a7052d5aee7',
                   '264:5-264:16',
                   '42449f69dd6cd4103609b438b52d754ca20fe0b01270614aafc67c1dd4c66292',
                   '=', 10, 'expr', '264:5-264:17',
                   '41861b73ca371a6a75e65c0285fd4c5e9c8bda3be51938e04212ef1fa53139ef', 1),
    OutStoreRecord(63, '267:5-267:12',
                   'c56f33a04a659170eb3a358257d3cd8ba3bf98e47f236e49113bbe44f69b6dfc',
                   '267:5-267:27',
                   '9f9de284c0858f4b81698b3017219a3e01a11a6f005118518e9abb108ee33fdb',
                   '=', 13, 'expr', '267:5-267:28',
                   '9ec41deb63500b7a35468f0622df35f6c2ebacb2c16cc760050fc16345b782e5', 1),
    OutStoreRecord(64, '268:5-268:13',
                   '31f9aa46d4294394d8199fd4b2d90190116dd2b930f8d0c1bf228524ae6944ca',
                   '268:5-268:18',
                   '00bc0bbd3c6112ba7f47c6f3d30fdac9ab4307d63e045e129a774fd9503f1261',
                   '=', 14, 'expr', '268:5-268:19',
                   'd398b9df52105762d36d2e3f3ba3b80e757e340c42c477f9147f2ee92186dfff', 1),
    OutStoreRecord(65, '269:5-269:14',
                   '013491b5927b1c3567e922a4eaf217b862c7b6fc6a00a68c3ba81f75c9fb1323',
                   '269:5-269:23',
                   'da008100a19abcbe9e40eff0ef2247ffb61042190209617a01b43eeff9a30dbb',
                   '=', 15, 'expr', '269:5-269:24',
                   '0ab6bf6ef2eaa400063c802c4e6371d059e63143afd7bae9f5f560fc1e45f823', 1),
    OutStoreRecord(66, '270:5-270:12',
                   '690231d22e8f04d3b388b063d43a58e0ce477e72931cb354079d7ed815f82614',
                   '270:5-270:19',
                   'b621acf75817a397af60e3c40756e6a94297eb5df4900a2eb435e93eae684d6e',
                   '=', 16, 'expr', '270:5-270:20',
                   '1849e014b5f6393f88093555e81649f0fbbd7e3c8fbd6b697606bd70e45afea3', 1),
    OutStoreRecord(61, '276:9-276:19',
                   'e667b7f909db9bc08bfaf0735b97f02a5d3c924065671236af59a1a60eee29d0',
                   '276:9-276:34',
                   '2056b919d5fc26cc557805934254a98d4dd2342463f0c68de0e4be82ba826276',
                   '=', 18, 'expr', '276:9-276:35',
                   'ae1cb8fb42b5dac6dbca2d04790e424832f20abfc289d1d8099063e072e48ab1', 3),
    OutStoreRecord(61, '278:9-278:19',
                   '3d1400fc9fd35671274e8d1d69e8a7d07e7ae7a9f93df5fe0e59227f6e0cd932',
                   '278:9-278:23',
                   '225952976b5e46226ecc861fe23773d1ea55f3ddc540aafde6af5e81d4b1d199',
                   '=', 18, 'expr', '278:9-278:24',
                   'ec003a7895c6b1ab420b8e53e5fbb1b5354a2833a3031d0330acf5c3475c6896', 3),
    OutStoreRecord(50, '163:5-163:10',
                   'e93b26c62c17b18f580dc2c1f7c3d5cac890cb6c17d6f9bf2f4f473f56d1307b',
                   '163:5-163:53',
                   'a9fee8cf3e36088d758b30c021429eaceff186c3501b02056069a366c0ad9771',
                   '=', 6, 'expr', '163:5-163:54',
                   '76d85d3323d76e69e0b9fb84bc382cf6b06e3716299d9715a6da08a0c05a7b77', 1),
    OutStoreRecord(51, '164:5-164:10',
                   '351b38c7c9605a9d79a98f001c9a7616ac0e730359680f622ac6832722de005d',
                   '164:5-164:53',
                   'a30c81164774ffaa1f86724d66f20095022d4118764d1443ccb58a983915866f',
                   '=', 7, 'expr', '164:5-164:54',
                   '099f40c8242f3bfd4e3f5597d852b7ea176fd8e1284b4752490ff2b586675982', 1),
)
_MANDELBROT_OUT_READS = (
    OutReadRecord(63, 'z_final',
                '272:22-272:29', 'fb78672ba4d2c533f288f0eabf7f60b1cafbe2eae226da738605388c060dd622',
                'builtin', 111, 'mandelbrot_df64',
                '272:5-272:40'),
    OutReadRecord(63, 'z_final',
                '272:31-272:38', '4be190c1b8eb9f67ea2b0abb1a7214f182b711017dddfdd6fcd0393b8245a3f6',
                'builtin', 111, 'mandelbrot_df64',
                '272:5-272:40'),
)
_MANDELBROT_OUT_CALLS = (
    OutCallSiteRecord(
        'computeValueAt_df64', 'transformCoords_df64', 117, '321:5-321:77',
        '8445f262964b6aa7a0b33c7dace94f5f56e8e919d296743dbffcbec9c9d9ef9f',
        7, (5, 6),
        ((120, 're_df', 'local', 'vec2', '321:64-321:69'), (121, 'im_df', 'local', 'vec2', '321:71-321:76'),),
        'expr', '321:5-321:78',
        'e169f4f812d884bbbf7eb9498f81ce000344fd21f9226433d0515f5329dfab9c', 'void', 1),
    OutCallSiteRecord(
        'computeValueAt_df64', 'mandelbrot_df64', 111, '325:5-325:68',
        'a36dceb8d022f3034d29625d999d6d92e07fb6468fd8a85ec81a09993b046a62',
        9, (3, 4, 5, 6, 7, 8),
        ((122, 'sI', 'local', 'float', '325:44-325:46'), (123, 'rI', 'local', 'float', '325:48-325:50'), (124, 'zf', 'local', 'vec2', '325:52-325:54'), (125, 'dzf', 'local', 'vec2', '325:56-325:59'), (126, 'sa', 'local', 'float', '325:61-325:63'), (127, 'tm', 'local', 'float', '325:65-325:67'),),
        'expr', '325:5-325:69',
        'd0ce6a74bd885e0e9d00924bdff2056f7931e29583cee0bf8ee8efa51d911ce9', 'void', 5),
    OutCallSiteRecord(
        'main', 'getPOI', 106, '375:5-375:30',
        'f5c108b9e1af65b9d71646e697bdbc6d66d86cda123b1ec1605ad53818d4bded',
        3, (1, 2),
        ((154, 'cX_df', 'local', 'vec2', '375:17-375:22'), (155, 'cY_df', 'local', 'vec2', '375:24-375:29'),),
        'expr', '375:5-375:31',
        '12de3130a09d7559fcbc1817f722e46cf24dcd3eec3b79d4d40b7fe418bc2c3a', 'void', 5),
    OutCallSiteRecord(
        'main', 'transformCoords_df64', 117, '389:9-389:84',
        'aa746df8b21e47726c97c8991ff075383da9f1dcc817e0d632df7eeba3031e9c',
        7, (5, 6),
        ((163, 're_df', 'local', 'vec2', '389:71-389:76'), (164, 'im_df', 'local', 'vec2', '389:78-389:83'),),
        'expr', '389:9-389:85',
        '7d3552e02abd860f0cabd03a33ca37597f4d30c4155bbba421b77d5b09e11204', 'void', 7),
    OutCallSiteRecord(
        'main', 'mandelbrot_df64', 111, '390:9-390:101',
        '12621a3084b50717f4239f690081e4497b1ba23a4549c96d205b85ca1cea057c',
        9, (3, 4, 5, 6, 7, 8),
        ((157, 'smoothI', 'local', 'float', '390:48-390:55'), (158, 'rawI', 'local', 'float', '390:57-390:61'), (159, 'z_final', 'local', 'vec2', '390:63-390:70'), (160, 'dz_final', 'local', 'vec2', '390:72-390:80'), (161, 'stripeAcc', 'local', 'float', '390:82-390:91'), (162, 'trapMin', 'local', 'float', '390:93-390:100'),),
        'expr', '390:9-390:102',
        '1c563a8f3c61529832066ceb765c65418d234707de986da0a864f9caffcecaa6', 'void', 7),
)
_MANDELBROT_DECLARATION_INVENTORY = (
    (1, 'resolution', 'vec2', 'uniform', False, False, '4:1-4:25'),
    (2, 'tileOffset', 'vec2', 'uniform', False, False, '5:1-5:25'),
    (3, 'fullResolution', 'vec2', 'uniform', False, False, '6:1-6:29'),
    (4, 'time', 'float', 'uniform', False, False, '7:1-7:20'),
    (5, 'poi', 'int', 'uniform', False, False, '9:1-9:17'),
    (6, 'outputMode', 'int', 'uniform', False, False, '10:1-10:24'),
    (7, 'iterations', 'int', 'uniform', False, False, '11:1-11:24'),
    (8, 'centerHiX', 'float', 'uniform', False, False, '12:1-12:25'),
    (9, 'centerHiY', 'float', 'uniform', False, False, '13:1-13:25'),
    (10, 'centerLoX', 'float', 'uniform', False, False, '14:1-14:25'),
    (11, 'centerLoY', 'float', 'uniform', False, False, '15:1-15:25'),
    (12, 'zoomSpeed', 'float', 'uniform', False, False, '17:1-17:25'),
    (13, 'zoomDepth', 'float', 'uniform', False, False, '18:1-18:25'),
    (14, 'invert', 'float', 'uniform', False, False, '19:1-19:22'),
    (15, 'stripeFreq', 'float', 'uniform', False, False, '20:1-20:26'),
    (16, 'trapShape', 'int', 'uniform', False, False, '21:1-21:23'),
    (17, 'lightAngle', 'float', 'uniform', False, False, '22:1-22:26'),
    (18, 'rotation', 'float', 'uniform', False, False, '23:1-23:24'),
    (19, 'fragColor', 'vec4', 'output', True, False, '25:1-25:16'),
    (20, 'PI', 'float', 'const', False, True, '27:1-27:32'),
    (21, 'TAU', 'float', 'const', False, True, '28:1-28:33'),
    (22, 'BAILOUT', 'float', 'const', False, True, '29:1-29:29'),
    (23, 'LOG2', 'float', 'const', False, True, '30:1-30:39'),
    (24, 'MAX_ITER', 'int', 'const', False, True, '32:1-32:27'),
)
_MANDELBROT_FUNCTION_INVENTORY = (
    (95, 'computeValueAt_df64', 'float', ((81, 'fragCoord', 'vec2', 'in'), (82, 'cX_df', 'vec2', 'in'), (83, 'cY_df', 'vec2', 'in'), (84, 'z_zoom', 'float', 'in'), (85, 'rot', 'float', 'in'), (86, 'maxIter', 'int', 'in')), '319:1-327:2'),
    (96, 'df64_add', 'vec2', ((31, 'a', 'vec2', 'in'), (32, 'b', 'vec2', 'in')), '70:1-74:2'),
    (97, 'df64_from', 'vec2', ((39, 'a', 'float', 'in'),), '96:1-98:2'),
    (98, 'df64_mul', 'vec2', ((35, 'a', 'vec2', 'in'), (36, 'b', 'vec2', 'in')), '82:1-86:2'),
    (99, 'df64_mul_f', 'vec2', ((37, 'a', 'vec2', 'in'), (38, 'b', 'float', 'in')), '89:1-93:2'),
    (100, 'df64_quick_two_sum', 'vec2', ((25, 'a', 'float', 'in'), (26, 'b', 'float', 'in')), '41:1-45:2'),
    (101, 'df64_sub', 'vec2', ((33, 'a', 'vec2', 'in'), (34, 'b', 'vec2', 'in')), '77:1-79:2'),
    (102, 'df64_to_float', 'float', ((40, 'a', 'vec2', 'in'),), '101:1-103:2'),
    (103, 'df64_two_prod', 'vec2', ((29, 'a', 'float', 'in'), (30, 'b', 'float', 'in')), '57:1-67:2'),
    (104, 'df64_two_sum', 'vec2', ((27, 'a', 'float', 'in'), (28, 'b', 'float', 'in')), '48:1-53:2'),
    (105, 'getEffectiveZoom', 'float', ((94, 'poiIndex', 'int', 'in'),), '351:1-361:2'),
    (106, 'getPOI', 'void', ((42, 'index', 'int', 'in'), (43, 'cX_df', 'vec2', 'out'), (44, 'cY_df', 'vec2', 'out')), '117:1-146:2'),
    (107, 'getPoiMaxZoom', 'float', ((41, 'index', 'int', 'in'),), '111:1-115:2'),
    (108, 'inCardioid', 'bool', ((52, 'x', 'float', 'in'), (53, 'y', 'float', 'in')), '171:1-175:2'),
    (109, 'inPeriod2Bulb', 'bool', ((54, 'x', 'float', 'in'), (55, 'y', 'float', 'in')), '177:1-180:2'),
    (110, 'main', 'void', (), '367:1-411:2'),
    (111, 'mandelbrot_df64', 'void', ((58, 'c_re', 'vec2', 'in'), (59, 'c_im', 'vec2', 'in'), (60, 'maxIter', 'int', 'in'), (61, 'smoothIter', 'float', 'out'), (62, 'rawIter', 'float', 'out'), (63, 'z_final', 'vec2', 'out'), (64, 'dz_final', 'vec2', 'out'), (65, 'stripeAcc', 'float', 'out'), (66, 'trapMin', 'float', 'out')), '203:1-280:2'),
    (112, 'outputDistance', 'float', ((70, 'z', 'vec2', 'in'), (71, 'dz', 'vec2', 'in'), (72, 'rawIter', 'float', 'in'), (73, 'maxIter', 'int', 'in')), '291:1-299:2'),
    (113, 'outputNormalMap', 'float', ((87, 'fragCoord', 'vec2', 'in'), (88, 'cX_df', 'vec2', 'in'), (89, 'cY_df', 'vec2', 'in'), (90, 'z_zoom', 'float', 'in'), (91, 'rot', 'float', 'in'), (92, 'maxIter', 'int', 'in'), (93, 'angle', 'float', 'in')), '329:1-345:2'),
    (114, 'outputOrbitTrap', 'float', ((78, 'trapMin', 'float', 'in'), (79, 'rawIter', 'float', 'in'), (80, 'maxIter', 'int', 'in')), '310:1-313:2'),
    (115, 'outputSmoothIteration', 'float', ((67, 'smoothIter', 'float', 'in'), (68, 'rawIter', 'float', 'in'), (69, 'maxIter', 'int', 'in')), '286:1-289:2'),
    (116, 'outputStripeAverage', 'float', ((74, 'smoothIter', 'float', 'in'), (75, 'rawIter', 'float', 'in'), (76, 'stripeAcc', 'float', 'in'), (77, 'maxIter', 'int', 'in')), '301:1-308:2'),
    (117, 'transformCoords_df64', 'void', ((45, 'fragCoord', 'vec2', 'in'), (46, 'cX_df', 'vec2', 'in'), (47, 'cY_df', 'vec2', 'in'), (48, 'z', 'float', 'in'), (49, 'rot', 'float', 'in'), (50, 're_df', 'vec2', 'out'), (51, 'im_df', 'vec2', 'out')), '153:1-165:2'),
    (118, 'trapDistance', 'float', ((56, 'z', 'vec2', 'in'), (57, 'shape', 'int', 'in')), '186:1-197:2'),
)

_MANDELBROT_DIRECTION_CONTRACT = DirectionContract(
    native_abi="glsl::Vec2& (vec2) and float& (float), per parameter",
    pass_mechanism="reference",
    by_value_emission="forbidden",
    emitter_direction_gate_required=True,
    out_argument_native_shape="caller-local glsl::Vec2 / float lvalues, "
                              "uninitialized before the call (JS "
                              "pre-allocates PooledFloat32Array [0, 0] "
                              "pairs for vec2 and plain Number zeros for "
                              "float)",
    js_body_tail=(MANDELBROT_JS_GETPOI_LANE_WRITE + "; ...; "
                  + MANDELBROT_JS_GETPOI_STASH + "; "
                  + MANDELBROT_JS_TRANSFORM_STASH),
    js_out_stash=MANDELBROT_JS_OUT_STASH,
    js_call_shape=MANDELBROT_JS_CALL_SHAPE,
    js_out_allocation=(MANDELBROT_JS_FLOAT_ALLOCATION + "; "
                       + MANDELBROT_JS_VEC2_ALLOCATION),
    parameter_abis=(
        ("cX_df", "glsl::Vec2&"), ("cY_df", "glsl::Vec2&"),
        ("smoothIter", "double&"), ("rawIter", "double&"),
        ("z_final", "glsl::Vec2&"), ("dz_final", "glsl::Vec2&"),
        ("stripeAcc", "double&"), ("trapMin", "double&"),
        ("re_df", "glsl::Vec2&"), ("im_df", "glsl::Vec2&"),
    ),
)


_JULIA_DIRECTION_CONTRACT = DirectionContract(
    "reference", "native-reference", "forbidden", True,
    "four pinned out parameters preserve source argument order",
    "JuliaResult adapter writes explicit out values",
    "out values are caller-owned references",
    "df64_split(a, hi, lo); transformCoords(fragCoord, zm, reDF, imDF)",
    "float&/glsl::Vec2&",
    (("df64_split.hi", "float&"), ("df64_split.lo", "float&"),
     ("transformCoords.reDF", "glsl::Vec2&"),
     ("transformCoords.imDF", "glsl::Vec2&")),
)


def _julia_walk_expressions(value):
    for expression in value.expressions:
        yield expression
        stack = list(expression.children)
        while stack:
            current = stack.pop()
            yield current
            stack.extend(current.children)
    for child in value.children:
        yield from _julia_walk_expressions(child)


def _authenticate_julia_out(program, source_hash, profile):
    from . import julia_frontend_profile as frontend
    fail = lambda message: _profile_fail(JULIA_PROFILE, message)
    if profile != JULIA_PROFILE:
        raise fail("exact profile carrier required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if raw.count(b"df64_split(a.x, ahi, alo);") != 2:
        raise fail("argument order mutation")
    if (source_hash != frontend.RAW_SHA256
            or len(raw) != frontend.RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != frontend.RAW_SHA256
            or len(normalized) != frontend.NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != frontend.NORMALIZED_SHA256
            or _sha(program.functions) != frontend.FUNCTIONS_SHA256
            or _whole(program) != frontend.WHOLE_SHA256
            or _interface(program) != frontend.INTERFACE_SHA256):
        raise fail("source or typed identity lock mismatch")
    parameters = tuple(
        (function.name, parameter.name, parameter.type.display(),
         parameter.direction, _span(parameter))
        for function in program.functions for parameter in function.parameters
        if parameter.direction != "in")
    expected = (
        ("df64_split", "hi", "float", "out", "104:26-104:38"),
        ("df64_split", "lo", "float", "out", "104:40-104:52"),
        ("transformCoords", "reDF", "vec2", "out", "145:22-145:35"),
        ("transformCoords", "imDF", "vec2", "out", "145:37-145:50"),
    )
    if parameters != expected:
        raise fail("four-out parameter identity mismatch")
    stores = []
    for function in program.functions:
        if function.name not in {"df64_split", "transformCoords"}:
            continue
        out_names = {parameter.name for parameter in function.parameters
                     if parameter.direction == "out"}
        for statement in function.body:
            for expression in _julia_walk_expressions(statement):
                if expression.kind != "assign" or not expression.children:
                    continue
                target = expression.children[0]
                if getattr(target.symbol, "name", None) in out_names:
                    stores.append((function.name, target.symbol.name, _span(expression)))
    expected_stores = (
        ("df64_split", "hi", "106:5-106:21"),
        ("df64_split", "lo", "107:5-107:16"),
        ("transformCoords", "reDF", "153:5-153:76"),
        ("transformCoords", "imDF", "154:5-154:76"),
    )
    if tuple(stores) != expected_stores:
        raise fail("out store identity mismatch")
    calls = []
    for function in program.functions:
        for statement in function.body:
            for expression in _julia_walk_expressions(statement):
                if expression.kind == "call" and expression.callee in {
                        "df64_split", "transformCoords"}:
                    calls.append((function.name, expression.callee,
                                  expression.signature_id, _span(expression)))
    expected_calls = (
        ("df64_mul", "df64_split", 86, "113:5-113:30"),
        ("df64_mul", "df64_split", 86, "114:5-114:30"),
        ("df64_mul_f", "df64_split", 86, "123:5-123:30"),
        ("df64_mul_f", "df64_split", 86, "124:5-124:28"),
        ("iterateSmooth", "transformCoords", 99, "290:5-290:47"),
        ("main", "transformCoords", 99, "353:9-353:64"),
    )
    if tuple(calls) != expected_calls:
        raise fail("out call/argument-order identity mismatch")
    call_arguments = []
    for function in program.functions:
        for statement in function.body:
            for expression in _julia_walk_expressions(statement):
                if expression.kind != "call" or expression.callee not in {
                        "df64_split", "transformCoords"}:
                    continue
                out_start = len(expression.children) - 2
                arguments = tuple(
                    JuliaOutArgumentRecord(
                        ordinal, child.kind,
                        getattr(child.symbol, "id", None),
                        child.type.display(), _span(child),
                        "out" if ordinal >= out_start else "in")
                    for ordinal, child in enumerate(expression.children))
                call_arguments.append(JuliaOutCallRecord(
                    (function.name, expression.callee,
                     expression.signature_id, _span(expression)), arguments))
    if tuple(call_arguments) != _JULIA_CALL_ARGUMENTS:
        raise fail("out call argument order identity/type/span mismatch")
    consumed = []
    for function in program.functions:
        for parameter in function.parameters:
            if parameter.direction != "in":
                consumed.append(parameter)
    for function in program.functions:
        for statement in function.body:
            consumed.extend(expression for expression in _julia_walk_expressions(statement)
                            if expression.kind == "assign"
                            and expression.children
                            and getattr(expression.children[0].symbol, "name", None)
                            in {"hi", "lo", "reDF", "imDF"})
    consumed.extend(
        expression for function in program.functions
        for statement in function.body
        for expression in _julia_walk_expressions(statement)
        if expression.kind == "call"
        and expression.callee in {"df64_split", "transformCoords"})
    if len(consumed) != 14 or len({id(item) for item in consumed}) != 14:
        raise fail("out consumed-object ledger mismatch")
    return JuliaOutAdmissionRecord(
        expected, expected_stores, expected_calls, tuple(call_arguments),
        len(stores), len(calls), tuple(consumed))

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
        "out_parameters": _OUT_PARAMETERS,
        "out_stores": _OUT_STORES,
        "out_calls": _OUT_CALLS,
        "direction_contract": _DIRECTION_CONTRACT,
    },
    LIGHTLEAK_KEY: {
        "profile": LIGHTLEAK_PROFILE,
        "source_path": LIGHTLEAK_SOURCE_PATH,
        "raw_bytes": 5047,
        "raw_sha256": ("61bcb2989992c109dcf73ac5b34bb4dfa7f6603b54c111"
                       "a84e69b6f73a9501bb"),
        "normalized_bytes": 4360,
        "normalized_sha256": ("4568d0dd53883cfc1cb1ba8237a894e9c5740c4f1"
                              "a045dff377221722f3eef72"),
        # Frozen over the SEED-ATTACHED tree (see the module docstring):
        # these are the post-landing figures the dict entry's
        # "post_functions"/"post_whole" carry.
        "functions_sha256": ("72db52007f289ea5cff3ef10cc2b5245a7bac958f1"
                             "067729fdfd75d82515bf0d"),
        "whole_sha256": ("8f78928336444c53847458cb908ae2c3eeda6ae93c0ab0"
                         "090fbf87207846397a"),
        "interface_sha256": ("e8032324cde699ade81d0920220709d5087d576f3db"
                             "aee828da74f6152719ec0"),
        "defines": (),
        "declaration_count": 12,
        "declaration_inventory": (
            (1, "TAU", "float", "const", False, True, "4:1-4:42"),
            (2, "POINT_COUNT", "int", "const", False, True, "5:1-5:27"),
            (3, "inputTex", "sampler2D", "uniform", False, False,
             "7:1-7:28"),
            (4, "resolution", "vec2", "uniform", False, False, "8:1-8:25"),
            (5, "tileOffset", "vec2", "uniform", False, False, "9:1-9:25"),
            (6, "fullResolution", "vec2", "uniform", False, False,
             "10:1-10:29"),
            (7, "alpha", "float", "uniform", False, False, "11:1-11:21"),
            (8, "color", "vec3", "uniform", False, False, "12:1-12:20"),
            (9, "speed", "float", "uniform", False, False, "13:1-13:21"),
            (10, "seed", "int", "uniform", False, False, "14:1-14:18"),
            (11, "time", "float", "uniform", False, False, "15:1-15:20"),
            (12, "fragColor", "vec4", "output", True, False,
             "17:1-17:16"),
        ),
        "function_count": 7,
        "function_inventory": (
            (23, "centerMask", "float",
             ((22, "uv", "vec2", "in"),), "88:1-92:2"),
            (24, "hash31", "float", ((14, "p", "vec3", "in"),),
             "32:1-39:2"),
            (25, "hash33", "vec3", ((15, "p", "vec3", "in"),),
             "41:1-53:2"),
            (26, "luminance", "float", ((16, "c", "vec3", "in"),),
             "55:1-57:2"),
            (27, "main", "void", (), "94:1-158:2"),
            (28, "pcg", "uvec3", ((13, "v", "uvec3", "in"),),
             "20:1-30:2"),
            (29, "voronoiCell", "void",
             ((17, "uv", "vec2", "in"), (18, "seed_f", "float", "in"),
              (19, "t", "float", "in"), (20, "cell_color", "vec3", "out"),
              (21, "cell_dist", "float", "out")),
             "60:1-85:2"),
        ),
        "resources": (
            ("inputTex", "resolution", "tileOffset", "fullResolution",
             "alpha", "color", "speed", "seed", "time"),
            ("inputTex",), ("fragColor",), True, False),
        "call_edge_count": 6,
        "call_graph_sha256": ("ecb5142d3ec27b3aae718e293764c39f5c4b99888"
                              "ba13f972e45bda66d445fd4"),
        "reachable": (23, 25, 26, 27, 28, 29),
        "unreachable": (24,),
        "counted_loop_proof": (1, 0, 1, 6, 12, True),
        "seed": {
            "symbol_id": 2,
            "name": "POINT_COUNT",
            "value": 6,
            "literal": "6",
            "span": "5:1-5:27",
            "declaration_sha256": ("2b94b06ae0dabb88b3aa8536336f3bef5cd083"
                                   "40c50476ce0dc02c191d3e6899"),
            "symbol_sha256": ("5661dc91f9e702daa9a5c2a7811683c8ec5716b99b2"
                              "f260091e7bf60ea777451"),
            "initializer_sha256": ("ccb79f398d39fa9014004c27c865e3e807be"
                                   "32ae04fde257ff1dec6c17b288de"),
        },
        "globals": (("TAU", 1, "float", "6.28318530717958647692"),
                    ("POINT_COUNT", 2, "int", "6")),
        "reads": (("voronoiCell", 29, 65, 25, 65, 36),),
        # The dict entry's pre-attachment figures (loop_proof's own
        # formulas over the canonical pre-proof tree -- see
        # counted_for_seed_contract).
        "seed_pre_functions": ("f7274c863e2c65b6aa80160bb4d42ea06cd26a3a6"
                               "8e8508e4fc13bc1350fb9a3"),
        "seed_pre_whole": ("9fc72ea8a4105bdfd38e58240bd0a1e4ae448c1f6ff95"
                           "4a31fd7967edfd991ae"),
        "voronoi_loop": {
            "owner": (29, "voronoiCell"),
            "span": "65:5-80:6",
            "induction_symbol_id": 70,
            "start": 0,
            "bound": 6,
            "comparison": "<",
            "update": "++",
            "bound_kind": "source-global-const-literal",
            "trips": 6,
            "depth": 1,
            "product": 6,
            "charge": 12,
        },
        "total_nodes": 576,
        "total_assigns": 19,
        "out_parameters": _LIGHTLEAK_OUT_PARAMETERS,
        "out_stores": _LIGHTLEAK_OUT_STORES,
        "out_calls": _LIGHTLEAK_OUT_CALLS,
        "direction_contract": _LIGHTLEAK_DIRECTION_CONTRACT,
        "mechanism_census": (2, 2, 1, 0),
        # 2 out Symbols + 1 owning function + 2 store targets + 2 assigns
        # + 2 calls + 4 out arguments + 2 statements: 15 distinct objects.
        "consumed_ledger": 15,
        "consumed_label": "out-inout-admission-lightleak",
    },

    MANDELBROT_KEY: {
        "profile": MANDELBROT_PROFILE,
        "source_path": "synth/mandelbrot/mandelbrot.glsl",
        "raw_bytes": 14931,
        "raw_sha256": ("6e6f740356f7ced1cbd40b3a991dd0ef654e39ecaeec8"
                       "c52e091a08f68e3b3bd"),
        "normalized_bytes": 10416,
        "normalized_sha256": ("4a28158eff2b0f94d9568c6a06aa61a924e51b49"
                              "01cb59698a8a4498dd782986"),
        # The SEED-ATTACHED tree (the state the authorities hold once the
        # loop-proof dict key and this row land together); the design's
        # interface figure carried a one-character typo (d for c at
        # position 26), corrected here.
        "functions_sha256": ("9df77469d8caf1799a6092f2f581aa2ad1516d715a"
                             "b8737a1fb2f8e33d3bea70"),
        "whole_sha256": ("673a127ed44de1e7fa0ce7ea88db6a575035c58265f9f2"
                         "1323f9edf821a2b44d"),
        "interface_sha256": ("e8c746cd6e89dddbcc041f4498036036b171f9b3f9b"
                             "24e2fd480f631ce92e124"),
        "defines": (),
        "declaration_count": 24,
        "declaration_inventory": _MANDELBROT_DECLARATION_INVENTORY,
        "function_count": 24,
        "function_inventory": _MANDELBROT_FUNCTION_INVENTORY,
        "resources": (
            ("resolution", "tileOffset", "fullResolution", "time", "poi",
             "outputMode", "iterations", "centerHiX", "centerHiY",
             "centerLoX", "centerLoY", "zoomSpeed", "zoomDepth", "invert",
             "stripeFreq", "trapShape", "lightAngle", "rotation"),
            (), ("fragColor",), False, False),
        "call_edge_count": 31,
        "call_graph_sha256": ("652bd56b36e1a005d8203727106fbddd14f7a5b41c"
                              "6192f89369c96e9416b548"),
        "reachable": (95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105,
                      106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
                      116, 117, 118),
        "unreachable": (),
        # The seed-attached closed summary (rides the call-graph lock; the
        # loop-shape lock itself lives in log_admission_profile).
        "counted_loop_proof": (1, 0, 1, 2048, 6144, True),
        "total_nodes": 999,
        "total_assigns": 51,
        "out_parameters": _MANDELBROT_OUT_PARAMETERS,
        "out_stores": _MANDELBROT_OUT_STORES,
        "out_reads": _MANDELBROT_OUT_READS,
        "out_calls": _MANDELBROT_OUT_CALLS,
        "direction_contract": _MANDELBROT_DIRECTION_CONTRACT,
        "mechanism_census": (10, 5, 0, 0),
        # 10 out Symbols + 3 owning functions + 33 store targets + 33
        # assigns + 5 calls + 18 out arguments + 5 statements + 2 read
        # nodes: 109 distinct objects, each consumed exactly once.
        "consumed_ledger": 109,
        "consumed_label": "out-inout-admission-mandelbrot",
    },
}


def allowed_row_fields(key: str) -> frozenset[str]:
    """The complete set of slice-row fields permitted for ``key``.

    An allowlist, not a denylist; prepared keys answer from
    ``PREPARED_ROW_FIELDS`` -- frozen now, enforced when the row lands.
    """
    fields = ALLOWED_ROW_FIELDS.get(key) or PREPARED_ROW_FIELDS.get(key)
    if fields is None:
        raise _profile_fail(
            NEWTON_PROFILE,
            f"{key} is not an admitted out/inout admission carrier")
    return fields


def direction_contract(key: str) -> DirectionContract:
    """The frozen emission contract for ``key``'s out parameters."""
    if key == JULIA_KEY:
        return _JULIA_DIRECTION_CONTRACT
    lock = _LOCKS.get(key)
    if lock is None:
        raise _profile_fail(
            NEWTON_PROFILE,
            f"{key} is not an admitted out/inout admission carrier")
    return lock["direction_contract"]


def counted_for_seed_contract(key: str) -> CountedForSeedContract:
    """The complete mechanism-A dict entry for ``key`` -- field-for-field a
    ``loop_proof._SOURCE_GLOBAL_LITERAL_INT_PROFILES`` entry (the singular
    ``integer``/``reads`` schema), the integration slice's one-move landing
    source for the bound-proof dict key. Un-landed: the dict key lands with
    this module's row and the authority arms, never before."""
    lock = _LOCKS.get(key)
    if lock is None or "seed" not in lock:
        raise _profile_fail(
            LIGHTLEAK_PROFILE,
            f"{key} is not an admitted counted-for seed contract carrier")
    return CountedForSeedContract(
        raw=lock["raw_sha256"],
        source=lock["normalized_sha256"],
        defines=lock["defines"],
        integer=(lock["seed"]["name"], lock["seed"]["symbol_id"],
                 lock["seed"]["literal"], lock["seed"]["value"]),
        globals=lock["globals"],
        reads=lock["reads"],
        pre_functions=lock["seed_pre_functions"],
        post_functions=lock["functions_sha256"],
        pre_whole=lock["seed_pre_whole"],
        post_whole=lock["whole_sha256"],
        interface=lock["interface_sha256"],
    )


def authenticate_out_inout_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple:
    """Return the frozen out-parameter identity of ``program.key``.

    Returns an empty tuple for non-carrier keys (unconditional membership
    set); supplying a profile for a non-carrier is a hard failure naming
    the sole (currently prepared) admitted sites.

    Membership is the **authenticatable** set -- every frozen record,
    ``PREPARED_KEYS`` included -- not the landed registry.
    """
    if program.key == JULIA_KEY:
        return _authenticate_julia_out(program, source_hash, profile)
    if program.key not in _LOCKS:
        if profile is not None:
            raise _profile_fail(
                NEWTON_PROFILE,
                "program key is not an admitted out/inout admission carrier; "
                f"{NEWTON_KEY} df64_cmul out vec2 rr at 98:52 and ri at "
                "98:65, and transformCoords_df64 out vec2 re_df at 108:38 "
                "and im_df at 108:54; "
                f"{LIGHTLEAK_KEY} voronoiCell out vec3 cell_color at 60:50 "
                "and out float cell_dist at 60:71; "
                f"{MANDELBROT_KEY} getPOI out vec2 cX_df/cY_df at 117:24/"
                "117:40, transformCoords_df64 out vec2 re_df/im_df at "
                "154:27/154:43, and mandelbrot_df64 out float smoothIter/"
                "rawIter/stripeAcc/trapMin and out vec2 z_final/dz_final at "
                "204:22-206:60, "
                "are the sole admitted parameters")
        return ()
    lock = _LOCKS[program.key]

    def fail(message: str) -> ValueError:
        return _profile_fail(lock["profile"], message)

    if profile != lock["profile"]:
        raise fail("exact profile carrier required")

    # --- coarse gate -------------------------------------------------------
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

    # --- the out/inout census (value tiers ahead of identity tiers) --------
    # The inout gate runs FIRST: it is the fail-closed boundary of the
    # mechanism (an `inout` parameter is never admitted through this
    # module), so a planted inout answers by name before the out census
    # dilutes the message.
    if not _inout_parameter_census_holds(program):
        raise fail("inout parameter census mismatch")

    # --- the counted-for seed side (locks with a "seed" only) ---------------
    # lightLeak's mechanism-A locks, in the parallax order (rebuild first,
    # then the seed's value tier, its identity tier, the globals census,
    # the write census, the read census, the loop profile). They run
    # AHEAD of the out/inout identity tiers because Symbol and node
    # hashes embed absolute source offsets: a length-changing source
    # mutation anywhere upstream would otherwise be absorbed by an
    # identity hash before the seed lock that names it could fire. The
    # program-wide mechanism census runs last (after the out/inout
    # census) so the per-site locks answer first.
    if "seed" in lock:
        if not _counted_rebuild_holds(program, lock):
            raise fail(
                "counted-for proof tree does not match the seed-derived "
                "rebuild")
        if not _seed_declaration_holds(program, lock):
            raise fail(
                "counted-for bound seed declaration value profile mismatch")
        if not _seed_identity_holds(program, lock):
            raise fail(
                "counted-for bound seed declaration identity mismatch")
        if not _globals_census_holds(program, lock):
            raise fail("source global census mismatch")
        seed_ids = {lock["seed"]["symbol_id"]}
        if not _no_seed_write_holds(program, seed_ids):
            raise fail("counted-for bound seed write census mismatch")
        if not _seed_reads_holds(program, lock):
            raise fail("counted-for bound seed read census mismatch")
        if not _voronoi_loop_holds(program, lock):
            raise fail("counted-for voronoi loop profile mismatch")

    census = list(_out_parameter_census(program))
    if not _out_parameter_census_holds(census, lock):
        raise fail(f"out parameter census mismatch: {len(census)}")
    if not _out_parameter_identity_holds(census, lock):
        raise fail("out parameter identity mismatch")

    references = list(_out_reference_census(program))
    stores = [entry for entry in references if entry[-1]]
    others = [entry for entry in references if not entry[-1]]
    if not _out_write_shape_holds(stores, lock):
        raise fail("out parameter store shape mismatch")
    if not _out_write_only_holds(others, lock):
        raise fail(f"out parameter write-once census mismatch: "
                   f"{len(others)} non-store reference(s)")
    # The read tiers are per-key: only a lock that CARRIES frozen reads
    # (mandelbrot's two z_final references) validates them here -- for the
    # write-once carriers the planted-read boundary stays the write-only
    # lock alone, exactly as their tests freeze it.
    if "out_reads" in lock and not _out_read_shape_holds(others, lock):
        raise fail("out parameter read census mismatch")
    if not _out_write_identity_holds(stores, lock):
        raise fail("out parameter store identity mismatch")
    if ("out_reads" in lock
            and not _out_read_identity_holds(others, lock)):
        raise fail("out parameter read identity mismatch")

    callees = frozenset(
        {record.function_name for record in lock["out_parameters"]})
    calls = list(_out_call_census(program, callees))
    if not _out_call_census_holds(calls, lock):
        raise fail(f"out call-site census mismatch: {len(calls)}")
    if not _out_call_identity_holds(calls, lock):
        raise fail("out call-site identity mismatch")
    if not _void_statement_shape_holds(calls, lock):
        raise fail("bare void-call statement shape mismatch")
    if not _direction_contract_holds(lock["direction_contract"], lock):
        raise fail("out direction emission contract mismatch")
    if ("mechanism_census" in lock
            and not _mechanism_census_holds(program, lock)):
        raise fail("mechanism census mismatch")

    # --- visitation ledger -------------------------------------------------
    # The out Symbols, the owning functions, the store targets and their
    # assigns, the calls, their out arguments, the statements, and the
    # frozen read nodes: each consumed exactly once (newton's module
    # default stays 26 so the sabotage test's patch still bites; the other
    # locks ride their own counts). The out-argument slice is per record:
    # newton's and lightLeak's owners take the trailing pair, while
    # mandelbrot_df64's calls take the trailing SIX.
    owners = {}
    for function, _, parameter in census:
        owners.setdefault(function.id, function)
    _check_ledger(
        [*(parameter for _, _, parameter in census),
         *owners.values(),
         *(node for _, node, _, _, _, _ in stores),
         *(parent for _, _, parent, _, _, _ in stores),
         *(node for _, node, _, _ in calls),
         *(child for (_, node, _, _), record in zip(calls,
                                                    lock["out_calls"])
           for child in node.children[len(node.children)
                                      - len(record.out_ordinals):]),
         *(chain[-1] for _, _, chain, _ in calls),
         *([] if "out_reads" not in lock
           else [node for _, node, _, _, _, _ in others])],
        lock.get("consumed_ledger", _CONSUMED_LEDGER),
        lock.get("consumed_label", "out-inout-admission-newton"),
        lock["profile"])
    return (tuple(parameter for _, _, parameter in census),
            tuple(node for _, node, _, _ in calls))


def apply_out_inout_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_out_inout_admission(program, source_hash, profile)
    return program
