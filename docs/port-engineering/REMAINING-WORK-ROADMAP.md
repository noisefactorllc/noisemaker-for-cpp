# noisemaker-for-cpp — remaining-work roadmap

Consolidated from five independent precompute agents, 2026-08-12. Every count
below was recomputed directly from `typed_slice.json` and the pinned corpus,
not copied from earlier documents.

## Ground truth (corrected)

Authoritative, read from the pinned corpus `manifest.json` (**not** from a
filesystem glob — see the trap below):

```
corpus   : 212
typed    : 131
unported :  81   (filter 57, classicNoisedeck 13, synth 10, mixer 1)
```

`NEXT_CODING_AGENT_HANDOFF.md`'s **corpus count of 212 is correct**; only its
**"79 unported" is wrong — it is 81**.

**Trap, and it fooled three agents plus me.** Globbing the corpus for `*.glsl`
returns 211, not 212, and invites the confident-but-wrong conclusion that the
corpus is 211 and the handoff is off by one. Exactly one program's source does
not use that extension: `filter/wormhole:deposit`, whose source is
`sources/filter/wormhole/deposit.frag`. **Always enumerate programs from
`manifest.json`, never from a glob.**

`filter/wormhole:deposit` is also unusual in kind, not just extension — it is a
nine-line vertex-color passthrough whose only input is `in vec4 vColor`, an
interpolated **varying**, not a uniform or texture. That is a resource class no
ported program uses. Classify it deliberately (portable vs. ineligible for
native binding) rather than assuming it is an easy win because it is short.

The typed/public *hashes* in the Task 32 brief are unaffected by any of this —
they derive from the key list, not from the totals.

## Clusters, sized

| Cluster | Programs | Readiness | Owner note |
|---|---:|---|---|
| Derivatives (`dFdx`/`dFdy`/`fwidth`) | **17** | Architecture validated bit-exact; integration plan written | Largest single win |
| Loop-proof shapes | **16** | Study complete, ordered by cost | Ten distinct shape groups |
| Grade (`filter/grade:*`) | **6** | Brief + design review ACCEPT + oracle all ready | Implement first |
| Matrix dispatch | **7, none clean** | Precompute over-optimistic — see census correction | Blocked on matrix indexing |
| Bitwise operators | **1 + 13 partial** | Precompute done; only 1 is bitwise-only | Signed-shift hazard |
| Remainder | ~30 | Not yet characterized | Includes `wormhole:deposit` |

## Derivatives — 17 programs

**STALE AS OF 2026-08-13 -- this whole section describes the mechanism as
not-yet-built. It is built and landed.** `tools/glslcpp/frontend/
derivative_admission_profile.py` (`derivative-admission-v1`) exists and 15
of these 17 programs are typed and native-tested today; only `posterize`
and `waves` remain, gated on their own separate `round`/`any` admission,
not on derivatives. See the "Batch: two free programs + `nmReindexReduce`
cap widening" entry far below for how this was rediscovered and the
corrected next-step. Keep the paragraphs below for the historical design
reasoning (narrowing asymmetry, cache-eviction order, sampler flip
convention are all still load-bearing facts about the landed mechanism) but
do not read "remaining work" as still remaining.

Verified exactly: 20 corpus files contain a derivative call; minus
`filter/lowPoly` (preprocessor-eliminated at the pinned `LP_BORDER=0`),
`synth/testPattern` (comment only), and `mixer/distortion` = **17**.

CORRECTION: `mixer/distortion` was recorded here as "terminally blocked on
local arrays". That is wrong. Its real terminal blocker is `unsupported sampler
parameter` at 91:33 — it does have live, reachable `dFdx`/`dFdy`/`reflect`, they
are simply not what the validator rejects first.

**Correction to the architecture doc's §5.1(a):** it states the semantic
analyzer does not recognize these builtins. It does — `body_semantic.py:37,40`
registers all three under family `derivative`, `:390` types them, and `:344`
already sets `uses_derivatives`, which is threaded end-to-end through
`semantic.py:306` into every program's frozen resource tuple (always `False`
today). The blocker is one level down: `generate_typed_slice.py:2088` rejects
any callee not in `_BUILTINS`, and `_BUILTINS` is derived from the frozen
44-entry `APPROVED_CAPABILITIES`. So admission must use the established
**node-identity** escape (the `round` / `tanh` / `floatBitsToUint` /
`all`+`lessThanEqual` pattern at `:2057-2089`), never a 45th vocabulary entry.

Remaining work: node-identity admission; emitter call lowering; `DerivativeState`
plus free functions in `glsl_runtime.hpp`; a quad driver in `pass_runner.cpp`;
17 per-program gates (the bulk of the labor).

**The narrowing asymmetry is load-bearing** and must be reproduced exactly
(`glsl-runtime.js:448-474`, `:512-533`): scalar records store a raw JS Number,
so the difference is taken in double and narrowed once on return (`F32`, :461);
vector records are `Array.from(Float32Array)` and the `x`/`y`/`footprint`
buffers are themselves `Float32Array`, so **every component store narrows**.
Reversing this passes a smooth-polynomial test and fails on real programs.

**Deliberate deviation, documented:** the JS cache-eviction predicate
(`:541-543`) is correct only for JS's raster order; `pass_runner.cpp` walks
`pixelY` in the opposite sense. Porting it literally would leak or evict early.
Use quad-major iteration or reference counting — both traversal-order-agnostic,
identical amortization. Cost is ~2x kernel-body executions per pixel for
derivative programs (not the brief's ~1.25x), and exactly zero for the other 131.

## Matrix dispatch — 6 real targets, not 9

`Mat<N>` is already generic in the runtime; the restriction is 11 sites across
the validator and emitter. Applying the two mandatory filters removes three of
the nine claimed candidates: `moodscape` and `noise` have their entire matrix
closure dead at default defines, and `effects`'s is dead *and* needs three
unrelated capabilities first.

**Narrowing hazard, verified empirically rather than assumed:** the JS
`matrixMult` helper accumulates into a plain `Array`, so matrix-matrix products
are never narrowed to f32, while C++ `Mat<N>*Mat<N>` narrows after every column.
This is a Curl-tanh-class divergence and it is live for `glitch` (chained
`T*Q*S`). Matrix-vector with a simple operand is narrowing-safe as-is.

Slices: A (type/global admission, +0) → B (matrix-vector widening, +5) →
C (chained-product lowering that preserves double accumulation, +1).

## Loop-proof shapes — 16 programs

Derived by walking each row's *terminal* blocker rather than counting programs
that merely touch the loop-proof bypass. 30 unproved sites across 10 shape
groups. All 16 are reachable and all 16 are discriminable.

Two prior-roadmap corrections: only **3** of a claimed 6 programs are true
fingerprint-only reuses of `source-global-literal-int-v1`; `dither` does not
qualify at all (its const initializer is `binary`, not `literal`).
`reindexReduce`/`mandelbrot` qualify structurally but need budget-cap increases
(262,144 nested product, ~64x over cap; trip_count 500, ~4x over).

Order: 3 fingerprint reuses → two cheap mechanical fixes (`smoothBlend`
return-in-body, `zoomBlur` float induction) → `gabor` depth cap → call-site
analysis for parameter/local-bound loops → `fractal`'s uniform-bound loop and
`median`'s `while`-based quickselect last (the two not soundly provable
statically).

## Standing hazards

1. **The parity target is not GLSL semantics** — it is whatever the third-party
   `glsl-transpiler` (`optimize: true`) chose to materialize. Narrowing points
   are its heuristics. Fix mismatches per-call-site; a blanket unary-macro fix
   regressed three programs once.
2. **The capability vocabulary is frozen at 44.** `typed_manifest.json` embeds
   the full list in every row, so a 45th invalidates frozen historical hashes.
3. **Both mandatory filters** — reachability from `main()` at the authorized
   define map, and discriminability of the real hazard. Each was learned by
   losing a full implementation cycle.
4. **Coarse-hash-gate absorption** — any tree edit perturbs the whole-program
   hash, so mutation tests never reach a profile's node-level logic unless the
   coarse hashes are deliberately re-frozen. Prove non-vacuity by sabotage.
5. **`-ffp-contract=off` is mandatory.** Without it clang fuses FMA and even
   *inputs* stop matching JS.
6. **Oracle infrastructure can itself be wrong.** The `time`-in-uniforms
   binding defect silently froze four incorrect expectations. Every new oracle
   must assert the kernel actually observed its declared inputs; the grade
   oracle's `renderCase()` reserved-key check is the reference pattern.
7. **`std::*` vs V8 at double precision**: tanh 16.2%, exp 10.5%, sin 4.2%,
   cos 3.5%, sqrt/pow 0%. An fdlibm `tanh` was prototyped and verified (0/4000)
   but not shipped — Curl passes without it by luck, not guarantee.
8. **Harness canary**: `sqrt` is IEEE correctly-rounded in both C++ and V8. Any
   harness reporting a `sqrt` disagreement is broken, not the math.

## Oracle audit result (2026-08-12)

Every oracle was audited for the `time`-in-uniforms binding defect. The verified
reserved-key list is 9 entries, assigned after the `...uniforms` spread at
`noisemaker-for-cpu/src/csl/glsl-kernel.js:49`: `resolution`(51),
`fullResolution`(52), `tileOffset`(53), `aspectRatio`(54), `aspect`(55),
`time`(56), `globalTime`(57), `deltaTime`(58), `frame`(59).

**Genuinely-wrong frozen expectations in any oracle consumed by a test: 0.**

Tasks 23-30 clean. Task 31 (curl) was defective, is now fixed, and the vendored
`task-31-oracles.json` is byte-identical to a fresh run of the fixed generator.
Task 32 (grade) is the reference-quality generator with an explicit guard.

**LANDMINE — do not vendor as-is:** the *caustic* draft oracle
(`task-31`-era, never vendored, no consuming test) still carries the unfixed
defect: 4 of its 6 eligible cases render at time 0 while declaring 3.5 / 12 /
1.25 / 40. Caustic itself was backed out as unreachable dead code at
`NOISE_TYPE=10`, so nothing consumes this today — but vendoring it without
first porting the guard would freeze four wrong expectations.

Not audited: tasks 11-14 (no generator source survives) and task 15 (uses a
different `CpuRenderer.buildBindings` path). None are vendored, so no live risk.

## Bitwise operator family — 1 clean, 13 partial, 5 dead

Of the 81 unported: **1** is blocked *only* on bitwise/shift
(`synth/bitwise:bitwise`); **13** use bitwise but have a named second blocker;
**5** have their bitwise use in dead code at authorized defaults (`caustic`,
`classicNoisedeck/effects`, `moodscape`, `classicNoisedeck/noise`,
`synth/noise`). A further **13** are a naive-grep trap — their pcg-hash use is
already inside the existing `uint-vector-bitwise` capability and they are not
blocked on this family at all.

**The load-bearing hazard — a wrong-shift trap, not a missing feature.**
`glsl-transpiler` (`lib/operators.js:298-370`) emits JavaScript's **signed**
`>>` for a GLSL `uint >> uint` whenever the enclosing function is not one of its
recognized canonical idioms. This is visible in shipped JS at
`canonical-kernels.js:15313,15322` (median), `:16410-16426` (osd),
`:19971-19975` (spookyTicker), `:34733` (testPattern). The *recognized* `pcg3d`
idiom correctly uses `>>>` (`glsl-runtime.js:23-38`) — which is precisely why
the existing `glsl::shift_right` (a **logical** shift, `glsl_types.hpp:196-204`)
is correct for what has already shipped and **wrong for every one of the
frontier programs' bespoke hash helpers**. A new signed-arithmetic `>>`
primitive is required for that family.

Shift-count masking is already right: JS masks the RHS mod 32 and
`glsl_types.hpp:200` already does `amount & 31U`. Any new primitive must too.

Order: (1) `synth/bitwise` alone; (2) the shared `randomFromLatticeWithOffset`
scalar-uint-XOR across `bitEffects`/`kaleido`/`shapeMixer`/`shapes`/`synth/shape`;
(3) `filter/grain`'s single broadcast `uvec3>>uvec3` site; (4) the bespoke-hash
family last, gated by JS-golden oracles swept across the **full int32 range** —
small positive values cannot discriminate a logical-vs-arithmetic shift bug.

Two prior in-repo documents are contradicted by this scan and need
adjudication: `caustic_word_hash_profile.py`'s "live, reachable" comment, and
`post-scalar-bitwise-frontier-audit.md`'s claim of four reachable `bitEffects`
helper calls. An independent BFS plus manual `#if` trace found both dead at the
authorized defaults. Caustic being dead is consistent with its earlier back-out.

## How a program is actually admitted (corrects the architecture doc)

The derivatives architecture doc asserts that each new program needs its own
`validate_current_vocabulary_<name>` gate, and calls authoring 17 of them "the
bulk of the integration labor". **That pattern does not exist.** Measured
against the live tree:

- Exactly **two** `validate_current_vocabulary_*` functions exist —
  `_degauss` (`generate_typed_slice.py:375`) and `_crt` (`:468`). They are
  special-cases for the only two programs carrying a bespoke public factory
  constant, not a per-program template. (The Task 32 design review independently
  flagged the same over-claim in a different document.)
- A slice row is minimal: `{"program_key", "defines"}` and, only when the
  program needs a novel structural shape, one profile token. **122 of the 131
  typed rows carry no profile token at all.**
- Profiles are reusable across programs where the shape is shared —
  `literal_vec3_lane_index_profile` serves two.

So the derivatives integration is: admit the builtins by node identity, add
emitter lowering, add the runtime, add the quad driver, and add ~15 slice rows
plus at most one shared profile. Materially lighter than the doc estimated.

## Derivatives — 15 will land, not 17

Established by running the real `validate_capabilities()` with derivatives
admitted via an in-memory test-only patch, rather than by inspection. Two of the
17 have unrelated second blockers that do not share a guard with their
derivative calls:

- `filter/posterize:posterize` — `round(levels_raw)`, currently admitted by node
  identity for a *different* program only → `unsupported builtin round`.
- `filter/waves:waves` — `any(notEqual(tileOffset, vec2(0.0)))`; `any` has
  **zero** admission path anywhere in the generator.

**Ordinal stability is proven for all 17** — the single biggest correctness risk
in the whole mechanism, now closed. 14 gate on `if (antialias)`, a uniform and
therefore frame-constant (verified by an identifier-storage walk of every guard
condition, not by reading); `halftone` and `stThreshold` are unconditional;
`stipple` is a compile-time `#if MODE==0`. No derivative call sits inside a loop
(`enclosing_loop_depth: 0` everywhere).

Refinement on `halftone`: under the pinned `MODE=0`, `halftoneCoverage`'s
`fwidth` survives into the typed IR but is unreachable from `main()` — the whole
monochrome branch is preprocessor-eliminated. Only `roundDotCoverage`'s call
executes, four times per pixel (C/M/Y/K), unconditional, so ordinals 0-3 are
stable.

No `vec4` derivative argument occurs anywhere in the 17 (only `float`, `vec2`,
`vec3`), so the architecture doc's "vec4 untested" gap is moot for this set.

## Derivatives prototype — all gaps closed (2196/2196 exact)

Six independent verification programs, every one bit-exact against the real
unmodified JS runtime, max abs diff 0.0:

| Gap | Result |
|---|---|
| vec3/vec4 overloads | 1536/1536 exact |
| Multi-call-site ordinal interleaving | 576/576 (6 sites, mixed widths, helper called twice) |
| Missing-ordinal fallback | 192/192, corners genuinely differing 3 vs 2 records |
| Odd 7x5 canvas, real off-canvas probes | 140/140 |
| Sampler comparison, 14 coords incl. 6 out-of-range | 112/112 |
| Texture-sample-then-derivative at off-canvas UV | 140/140 |

The vec3/vec4 case was not a smooth polynomial — corner constants were
brute-forced to find a genuine 1-ULP split between the scalar and vector paths
(`fw_t = 0.0025052933488041162` vs `fw_v3.x = 0.00250529358163476`), which both
implementations reproduce identically. That proves the narrowing asymmetry
survived rather than being accidentally collapsed, which a smooth test could
never show.

### TRAP — sampler flip convention (found here, would have cost days)

**The two samplers DO agree at out-of-range UV**, so the five texture-sampling
derivative programs (`bulge`, `pinch`, `spiral`, `tunnel`, `warp`) are not
blocked. But the agreement holds only under one specific calling convention:

C++'s `sample_bilinear_bottom_left` must be called **unflipped** against JS's
flipped `#texture` dispatch. **A naive `1 - v` pre-flip on the C++ side —
mirroring JS's caller-side pattern — double-flips and breaks bilinear
sampling.** `sample_bilinear_bottom_left` currently has **zero production call
sites**, so this convention is not exercised anywhere today and had to be
verified independently rather than inferred from existing usage. Nearest-sample
matches directly; both already call unflipped in production.

## Derivatives oracle — built, 15 programs / 57 cases / 30 mutations

At `docs/port-engineering/derivatives/oracle/`. `--check` byte-identical
on two consecutive runs. All 15 canonical factories confirmed live to have
`usesDerivatives === true`, so `bindGlslKernel` genuinely wraps them; each case
is additionally re-rendered through a structural copy of `wrapDerivatives` and
asserted bit-identical to the real runtime, which both validates the copy and
lets the harness record the per-pixel ordinal count for comparison against the
characterization's prediction (2 / 1 / 4, and exactly 0 for antialias-off).

12 programs are `antialias`-gated (4 cases each: 3 ON, 1 OFF diagnostic);
3 (`halftone`, `stThreshold`, `stipple`) have no `antialias` uniform at all.

### TRAP — compile-time defines must be passed as uniforms

`halftone`, `pondRipples`, and `stipple` pin GLSL `#define`s (MODE / PATTERN /
STYLE / WRAP), **but the JS reference has no preprocessor**. Reading each
factory's source shows it reads `$bindings["MODE"]` and friends at *runtime*.
If those are not passed as uniforms at their `_defaults()`-authorized value,
the kernel silently takes the wrong branch and the oracle freezes a wrong
expectation with no error. The generator now verifies this live, both through
`_defaults()` and by checking the factory text actually reads the binding.

### Discriminability finding — a both-axis sign flip is INVISIBLE

The obvious mutation (negate both derivative axes) produces **zero divergence**
for the 10 dFdx/dFdy-consuming programs, because every one of them supersamples
through the same point-symmetric 4-tap offset pattern, which is invariant under
simultaneous negation. The mutation had to be narrowed to an **x-only** flip to
discriminate at all. A test suite built on the obvious mutation would have
looked thorough and caught nothing.

Separately, sign-flip is a *proven* no-op for the 5 fwidth-only programs, since
`|x| + |y|` is invariant under negation — recorded as `expected_zero` rather
than quietly dropped. Both mutations otherwise diverge on every reach-eligible
case, and all antialias-off cases show zero divergence, confirming the
derivative path is genuinely dead there.

## Signed-arithmetic shift primitive — designed and verified

`noisemaker::glsl::shift_right_arithmetic(int32_t, uint32_t)` plus a `uint32_t`
overload, at `docs/port-engineering/shift-primitive/shift_primitive.hpp`.

JS semantics established by probe rather than from memory: `>>` always
sign-propagates, `>>>` always zero-fills, shift counts reduce via `amount & 31`
(no exceptions across counts -70..130), and non-integer operands truncate toward
zero, not floor.

**Deliberately a new, separately-named primitive rather than a flag on the
existing `shift_right`.** Arithmetic versus logical is a type-domain
distinction, not a parameter, and the choice must be re-derived per call site
from the actual emitted JS — a distinct name makes that visible and greppable
instead of silently flippable. The implementation also avoids depending on
C++'s right-shift-of-negative-`int32` behavior (verified, but not assumed
portable), deriving the bit pattern through `std::bit_cast` plus an unsigned
logical shift and explicit sign-fill, which is unconditionally defined in C++20.

**Verification: 16,034,196 compared / 16,034,196 exact / 0 divergent** —
100,206 curated values (every power of two and power-of-two-minus-one for
k=0..31 in both signs, INT32_MIN/MAX, the real hash constants, and 100,000
fixed-seed pseudorandom) crossed with 32 canonical shift amounts, plus an
edge-amount sweep at 32/33/63/64/1e6/UINT32_MAX.

**Real-program cross-check with a negative control.** `filter/spookyTicker`'s
`hash_mix`, extracted verbatim from live `canonical-kernels.js:19970-19976` and
sha256-snapshotted, ported to C++ with the new primitive: 100,206/100,206 exact.
The same port with a logical shift substituted diverged on **87.5%** of outputs
— so the passing result is discriminating, not accidental.

**No already-shipped path is wrong.** The existing logical `glsl::shift_right`
is correct for its actual admitted use (the canonical `pcg3d` idiom); nothing
found evidence it is misapplied anywhere already landed.

## Authoritative frontier census (supersedes earlier cluster claims)

At `docs/port-engineering/census/`. Produced by running the real analysis
path (`parse_program` / `analyze_program` / `validate_capabilities` /
`render_typed_cpp`) against all 81 unported programs, against a frozen snapshot
of `tools/glslcpp/` so a concurrently-editing agent could not perturb it.

### The matrix cluster is NOT clean — earlier claims were over-optimistic

A three-layer relaxed probe shows **none of the 7 matrix programs land after
mat3 admission**. Six hit a previously-uncosted **matrix indexing** gate, and
`shapeMixer` hits `reflect`. The matrix precompute's "Slice B lands +5" is
therefore wrong, and the cluster is bigger than believed: `shapeMixer` shares
the identical `fwdA` mat3 root blocker but was missed by the earlier study,
probably because it *indexes* the matrix rather than multiplying it.

### `filter/wormhole:deposit` — a SCATTER pass, not an ineligible one

**Earlier claim retracted.** This was recorded as "structurally ineligible" and
"a complete port is 211 programs, not 212". Both are wrong. The target is 212.

`deposit` is a vertex-stage scatter pass (`drawMode: 'points'`). Its `.frag` is a
two-line passthrough (`fragColor = vColor`) whose real work lives in a vertex
shader that is not in the corpus. It IS transpiled — `canonical-kernels.js`
carries `canonicalFactory181` for it, and `glsl-coverage.js` marks it
`status: "generated"`, not `"adapter"` — but the CPU reference **never calls
it**. `renderer.js:910` branches on `drawMode` and dispatches to a hand-written
scatter adapter instead.

So there is nothing meaningful in the fragment kernel, and porting
`fragColor = vColor` would be porting a program the reference never runs. **The
pass is fully portable via the adapter path**, which is exactly how JS does it:
`src/effects/cpu/scatter-registry.js` keys hand-ported CPU scatter functions by
`${effectId}:${pass.program}`. Seven are registered; wormhole is the only one in
this corpus (the others are `filter3d/`, `points/`, `render/` families).

The reference to port is `runWormholeDeposit`
(`src/effects/cpu/wormhole.js:34-76`), 43 lines: Oklab lightness with per-op
`Math.fround`, `angle = lightness*TAU*kink + rotation`,
`pixelStride = 1024*stride`, three wrap modes (mirror / repeat / clamp), the
bottom-up vertex-ID convention (`sourceRow = height-1-sourceY`), additive
accumulation weighted by `lightness^2`, and `float16Truncate` per channel. It
writes RGB only — alpha is left untouched.

This needs a C++ scatter-pass mechanism (a pass that writes arbitrary
destinations rather than filling each pixel exactly once), which is new
architecture but small and well-specified. It does **not** go through the typed
GLSL generator at all.

### Two programs are free today

`filter/invert:inv` and `synth/solid:solid` have zero blockers.

### Cluster table (81 = 75 live-validated + 6 grade)

| Cluster | Count |
|---|---:|
| Loop-proof, program-proof gate | 19 |
| Derivatives | 15 |
| Global-declaration bucket (mat3 7 / const-int 5 / const-uint 4 / vec3 4 / mutable 3 / int[80] 2) | 25 |
| Grade (landed) | 6 |
| Loop-proof safety-charge | 3 |
| Varying admission | 1 terminal + 3 downstream |
| Builtin admission (`round` / `any` / `reflect`) | 3 singletons |
| Zero-blocker, free today | 2 |
| Singletons (bitwise, inout, uniform-block, sampler-parameter, caustic, mat4) | 6 |

### Critical path

Derivatives (15, mechanism built) plus the 2 free programs first; ride the
`round`/`any`/`reflect` admission alongside them since that also unblocks
`posterize` and `waves`. Loop-proof program-proof gate second (19). Treat the
matrix cluster as **not** ready despite being "designed". The 25-program
global-declaration bucket is genuinely bespoke tail work — verified that none of
it lands free.

### Newly characterized, absent from every prior document

`julia` and `newton` (loop-proof safety-charge). Also flagged unresolved rather
than asserted: `effects` and `noise` fail for the identical reason as counted
loop-proof members yet sit outside that study's list of 16.

## Matrix Slice B oracle — built (29 cases, 10 mutations, 5 programs)

At `docs/port-engineering/future-precompute/matrix/oracle/`, `--check`
byte-identical twice.

**The narrowing hazard does NOT apply to Slice B.** Re-derived independently
from the live JS factory text rather than trusted from the precompute report:
all five programs' live matrix use is narrowing-safe — both `fwdA*c` (simple
operand) and `fwdB*(lms^3)` (compound operand) narrow to f32 exactly once,
matching C++'s `Mat<N>*Vec<N,float>` and `Mat<N>*FloatExpr<N>`. Proven rather
than assumed, via a `cube-unnarrowed` mutation that removes the narrowing step
and diverges 4/4 on every program. The earlier matrix-matrix concern stands only
for Slice C (`glitch`).

The dead inverse closure carries the divergent code shape but is proven
unobservable — both mathematically (multiplying by exactly +/-1 or 0 is exact at
any precision) and by a machine-asserted zero-divergence sweep — so it is
documented as expected-zero with proof rather than dropped.

Discriminability catch worth repeating: `adjust`'s case originally used
`contrast: 0`, which zeroed the whole downstream pipeline and masked divergence
in 1 of 4 cases. Changed to `contrast: 1`; now 4/4 diverge. A case that
neutralizes the pipeline looks like coverage and provides none.

Also live: `shapes` requires `LOOP_A_OFFSET`/`LOOP_B_OFFSET` passed as uniforms
at their `_defaults()` value (40/30) — the defines-bound-as-uniforms hazard,
confirmed by reading the factory text.

### OPEN CONTRADICTION — resolve before implementing matrix

The census's three-layer relaxed probe says **none** of the matrix programs land
after mat3 admission (6 blocked on a matrix-indexing gate, `shapeMixer` on
`reflect`). The matrix precompute says Slice B lands +5. Both cannot be right.
Re-verify directly against a frozen `tools/glslcpp/` snapshot before committing
to either. The oracle above is valid work either way — it only becomes usable
once admission actually passes.

## Cheap-unlock oracles — built, with one plan correction

At `docs/port-engineering/future-precompute/cheap-unlocks/`, both
generators `--check` byte-identical.

**Loop-proof trio** (`lightLeak`, `parallax`, `reindexStats`): 14 cases, two
mutations each on the `var <CONST> = <value>;` declaration. Mostly 4/4
divergence; `reindexStats-minus-one` is 3/4, fully explained — the 6x5 case is
structurally degenerate because the canvas is smaller than either tile size, so
both TILE_SIZE=8 and 7 break on canvas size rather than tile size.

**The saturating-loop trap, caught live.** The first `parallax` height-map
design gave only 1/4 divergence: `SHIFT_SCALE=0.15` capped ray travel to a
fraction of a texel, so the linear-interpolation refine recovered the same
crossing regardless of step count. The loop was real, the mutation was real, and
the test still proved nothing. Redesigned to a 16x16 gradient-plus-ripple height
field and re-verified empirically to 4/4 before locking in.

### CORRECTION — the shift hazard does not apply to `synth/bitwise`

`synth/bitwise:bitwise` has **zero shift operators**. Confirmed by source grep
*and* by a live regex assertion against the compiled `canonicalFactory244` text,
which the generator now throws on if it ever stops holding. So the bitops
report's headline signed-vs-logical `>>` hazard is irrelevant to this program;
only `&`/`|`/`^`/`~` govern it, and those already match C++20 two's-complement
`int32_t`. Every case still carries a high-bit-set operand near INT32_MIN/MAX to
stress that. The `mask=0` case is a deliberate structural negative control and
independently proves NaN propagation on divide-by-zero.

The signed-shift primitive remains needed — just for the bespoke-hash family
(`median`, `osd`, `spookyTicker`, `texture`, `testPattern`, `dither`,
`glyphMap`), not for `synth/bitwise`.

## Transcendentals — corrected baseline, and a real f32-level risk

### My earlier divergence figures were wrong

Measured over a 403,636-point adversarial sweep rather than the ~400-point
figure previously repeated:

| function | earlier claim | measured |
|---|---:|---:|
| tanh | 16.2% | **4.27%** |
| exp | 10.5% | **5.81%** |
| expm1 | — | 3.37% |
| sin | 4.2% | **2.71%** |
| cos | 3.5% | **2.64%** |
| log / atan | — | 2.26% / 1.41% |
| pow | 0% | **0.041%** |
| sqrt | 0% | 0% |

**`pow` is NOT correctly-rounded.** Only `sqrt` is IEEE-mandated and therefore
usable as a harness canary. The earlier "sqrt and pow both agree" canary was
half wrong.

### The port is faithful; the residual is V8's own FMA

`expm1`, `exp`, `tanh`, `sin`, `cos` ported line-for-line from V8's real
`src/base/ieee754.cc`. Under the mandated `-ffp-contract=off` they reach
99.96-99.99% exact at double precision. The identical source compiled with
`-ffp-contract=fast` hits **0/403,636 on all five simultaneously**, which proves
the transcription is bit-exact and the residual gap is V8's shipped binary
contracting FMA on arm64. Hand-placing `std::fma()` to chase literal zero was
considered and rejected: the fusion points are an undocumented backend
heuristic, so it would trade one non-portable coincidence for a more fragile one.

### The f32 question — and why the obvious measurement lies

Every value is narrowed to f32 before reaching a pixel, so double-level
divergence mostly evaporates. On the generic sweep, **both `std::` and fdlibm
show 0/403,636 at f32** — which looks like the risk is theoretical. It is not.
That sweep targets *double-precision* branch boundaries, not f32 rounding ties.

A second 689,942-point sweep was built that **constructs** inputs whose true
value sits almost exactly on an f32 rounding tie (by inverting target f32 values
through `atanh`/`log`/`log1p`/`asin`/`acos`). On that targeted sweep:

- `std::` vs V8 at f32: **86 divergent** across 3,449,710 comparisons
  (tanh 72, exp 3, expm1 5, sin 4, cos 2), all 1 ULP at f32.
- fdlibm vs V8 at f32: **4 divergent**, all `cos`, all 1 ULP at f32, each traced
  to the same FMA artifact and reproduced exactly by recompiling with
  `-ffp-contract=fast`.

So the risk is real and live in both implementations, findable only by
deliberate adversarial construction and never by broad sampling. The port
reduces it ~21x but does not eliminate it.

Curl's vec3 `tanh` overload — the only shipped consumer today — was checked
directly against the real project headers in both builds: **1,093,578 lane
comparisons, 0 mismatches** between the vec3 and scalar paths.

Patch at `docs/port-engineering/fdlibm/runtime-integration.patch`,
verified on a scratch copy of the real tree: 162 PASS / 0 FAIL, and the sorted
PASS test-name diff before/after the patch is **empty** — same tests, no
regression, nothing added.

## `filter/wormhole:deposit` — PORTED, bit-exact

Package at `docs/port-engineering/wormhole/`. This closes out the program
that was briefly and wrongly written off as unportable.

**Oracle**: 62 cases driving the real unmodified `runWormholeDeposit` — 14
hand-designed for discrimination plus a 48-case size x wrap-mode sweep, covering
all three wrap modes, engineered destination collisions, deliberate
out-of-bounds wraps, negative-stride negative-modulo stress, and fractional-wrap
truncation. 9 mutations, each with a machine-checked reach predicate. One
candidate mutation (`pixelStride` float-vs-double storage order) was proven a
mathematical no-op — 1024 is an exact power of two — and reported as such rather
than dropped or passed off as coverage.

**Port**: statement-for-statement mirror, `double` throughout with explicit
`f32r()` at exactly the points JS calls `Math.fround`. **36,228/36,228 lanes
exact, max abs diff 0** — mirror 11,796, repeat 12,200, clamp 12,136, plus 96
for a non-canonical wrap value — verified at `-O0` through `-O3`.

### A real bug, surfaced only by ASan

`wrapMirror` has a genuine off-by-one: it returns exactly `-1` when
`value === -1 (mod 2*size)`, proven by exhaustive sweep. **In JS this silently
no-ops** — an out-of-range TypedArray write is discarded. In C++ it was a heap
overflow, caught by AddressSanitizer on the first build. The fix reproduces the
JS behavior exactly via flat-offset bounds checking. Note it must be the *flat*
offset: independently clamping X and Y would wrongly discard writes that JS
genuinely performs through row aliasing.

**Integration**: ready-to-apply patch adding a `noisemaker::scatter` registry +
adapter + catalog, mirroring `scatter-registry.js` 1:1 and reusing the existing
`glsl::Bindings` uniform path. Verified by applying to a throwaway full copy of
the tree, building via CMake, and running the whole ctest suite: 100% pass
including 5 new regression tests.

### Open interaction with the fdlibm patch

The port calls `std::cos`/`std::sin`/`std::pow`, and their bit-identity with V8
is **empirically confirmed over 36k+ lanes but not guaranteed** outside this
input domain and toolchain. The pending fdlibm patch repoints `cos`/`sin` in the
runtime. These are currently separate code paths, but **landing fdlibm requires
re-verifying wormhole** rather than assuming the 36,228/36,228 result carries
over.

## fdlibm — LANDED

Applied 2026-08-12. `include/noisemaker/fdlibm.hpp` + `src/fdlibm.cpp`;
`glsl_runtime.hpp`'s `cos`/`exp`/`sin`/`tanh` wrappers and the Curl vec3 `tanh`
overload now route through `noisemaker::fdlibm::*`. Native 162/162, clean build.

### A gap the agent's native-only verification could not catch

`tests/test_typed_generator.py` contains two harnesses that compile **and link**
a generated C++ snippet against an explicit list of six `src/*.cpp` files. That
list did not include the new TU, so `test_task23_rejected_structural_mutations_
have_exact_native_sensitivity` failed with:

```
Undefined symbols for architecture arm64:
  "noisemaker::fdlibm::cos(double)", referenced from:
      noisemaker::glsl::cos(double) in task23_mutations-e039e0.o
```

Fixed by adding `src/fdlibm.cpp` to both harness link lists. The lesson
generalizes: **a patch verified only through CMake can still break the Python
suite**, because these harnesses maintain their own hand-written source list
that CMake knows nothing about. Any future change that adds a translation unit
must update both.

Worth noting what that test passing *afterwards* proves: it asserts exact native
sensitivity of frozen rendered values, so fdlibm changed no rendered output for
that program — it linked, ran, and reproduced the frozen bits.

## PRODUCTION DEFECT in noisemaker-for-cpu — dither error-diffusion crashes

Found while building the loop-proof oracle. **This is a bug in the JS renderer,
not in the port.** Independently reproduced.

`src/effects/generated/canonical-kernels.js:11071-11073`:

```js
var errRow = [];
for (var i = 0; i < FS_ERR_W; i++) {
  fsSeedNoise(blockOrigin, i).map(function (_) {return _ * stepScale;})
    .reduce((res,el,i)=>(res[i] = el, res), errRow[i]);
};
```

`errRow` is empty, so `errRow[i]` is `undefined` on the first iteration, and
`.reduce(fn, undefined)` then runs `res[i] = el` against `undefined`. Verified
by isolated repro: `TypeError: Cannot set properties of undefined (setting '0')`.
It throws on i=0 unconditionally — every canvas size, every uniform combination.
The intent was evidently `errRow[i] = fsSeedNoise(...).map(...)`.

**Blast radius**: the code is reachable only at `ditherType == DITHER_ERROR_DIFFUSION`
(`= 7`, `dither.glsl:32,579`). The parity golden
`parity/goldens/defaults/filter__dither.graph.json` pins `ditherType: 1`, so **no
test exercises the broken path** — which is why it has gone unnoticed. The GPU
path runs real GLSL and is unaffected; only the transpiled JS CPU path breaks.

**Consequence for the port**: `filter/dither:dither`'s error-diffusion path
cannot be ported bit-exactly, because there is no working reference behavior to
match. The other dither types are unaffected. Not fixed here — that is a change
to a different repo and outside this task's scope.

## `round` — the reference does NOT follow the GLSL spec

Established empirically by the builtin-admission oracle, and it corrects an
assumption stated in that agent's own brief.

The JS materializes GLSL `round()` as **`Math.round`**, which is
**round-half-toward-positive-infinity**. That is neither the GLSL spec's
round-half-to-even, nor `std::round`'s round-half-away-from-zero:

| x | `Math.round` (reference) | GLSL spec | `std::round` |
|---|---|---|---|
| -2.5 | **-2** | -2 | -3 |
| -1.5 | **-1** | -2 | -2 |
| -0.5 | **-0** | -0 | -1 |
| 0.5 | **1** | 0 | 1 |
| 2.5 | **3** | 2 | 3 |

A further trap, proven rather than assumed: `Math.round(-0.5)` is **`-0`**, while
the common C++ idiom `floor(x + 0.5)` yields **`+0`** there through exact IEEE-754
cancellation. Bit-different despite agreeing everywhere else.

This is the clearest instance yet of the standing rule that **the parity target
is the transpiler's materialization, not the GLSL specification.**

**Discriminability caveat**: of the three programs whose blocker becomes `round`
after global admission, `fxaa` and `grain` only ever call it on exact-integer
inputs (image dimensions), so no full-render case can discriminate a tie-break
rule there — proven by a 3-way mutation sweep showing zero divergence. `snow`'s
call site is dead code, never invoked from `main()`. So `round` admission is
real work for `posterize` only.

## Incident: sleep-killed agent left the tree broken (2026-08-13)

The machine slept mid-response and killed the loop-proof implementation agent
partway through applying its changes. The tree was left failing
`generate_typed_slice --check`. Recovery required unwinding five separate edits:

| Left behind | Disposition |
|---|---|
| 6 program rows in `typed_slice.json` | removed (mechanism incomplete) |
| count/hash pin bumped 152 -> 158 | reverted to `b261d268...` |
| `oilFlatten` entry in the expected-defines map | removed (orphaned) |
| float-induction widening in `loop_proof.py` | guard restored to int-only |
| 3 fingerprint profile entries in `_SOURCE_GLOBAL_LITERAL_INT_PROFILES` | removed, 9 keys -> 6 |

### The lesson that matters: four gates and 171 native tests are not enough

After removing the program rows, all four generator gates and the entire native
suite passed — and the tree was still wrong. The agent's `loop_proof.py`
widening had silently disarmed a mutation barrier
(`test_counted_for_v1_rejects_header_and_control_near_misses`, subtest
`float-induction`), which asserts float induction variables are **rejected**.
Only the Python suite caught it.

This is coarse-hash absorption wearing different clothes: a capability was
removed from the rejection set, and nothing that merely *builds and renders*
could notice. **A green build plus green native tests does not establish that
the generator still refuses what it is supposed to refuse.**

The drafted float-induction code was left in place but made unreachable through
the guard, with a comment stating that admitting it is a real capability change
that must land together with the programs needing it AND a deliberate update to
the barrier — never as a silent side effect.

### Process fixes adopted

1. **Snapshot before delegating the Python lane.** The verified-green tree is
   now archived at `docs/port-engineering/green-snapshots/green-152.tar.gz`
   (sha256 `f0082a91...`). Recovering by archaeology cost far more than
   restoring an archive would have.
2. **Screen the program list against the census before assigning it.**
   `filter/lightLeak` was handed to the agent despite the census recording its
   terminal blocker as `unsupported parameter direction out` — an unrelated
   capability. That was my error in composing the task, and it is what made the
   tree unbuildable rather than merely incomplete.

## The design record now lives in the repository (2026-08-13)

Everything in this directory previously lived in a scratch tree that would not
survive a reboot. It is now committed under `docs/port-engineering/`.

Checked before moving: `noisemaker-for-cpu` is a **public** repository
(`noisefactorllc/noisemaker-for-cpu`), so the detailed analysis of its internals
throughout these documents leaks nothing.

On the way in: 328 files were scrubbed of absolute home paths (the repository is
now at zero `/Users/...` occurrences), 165 files had dead scratch-tree references
retargeted — including two live provenance comments in shipped code
(`tests/test_scatter_wormhole.cpp` and `include/noisemaker/effects/scatter/wormhole.hpp`)
— and seven compiled Mach-O probe binaries that rsync carried along were deleted.

Deliberately excluded as regenerable bulk: a 124MB shift-primitive sweep dump
and ~18MB of float input vectors. Every report citing them states its exact
figures, and every generator rebuilds its own inputs. 227MB became 26MB.

The rollback archive lives OUTSIDE this repository, at
`~/platform/.noisemaker-cpp-snapshots/`, since it is a copy *of* the repository.
Its checksum was verified after the move rather than assumed.

## Next targets, in order of tractability

The mechanism for each of these is small and the oracle already exists:

| Target | Programs | Mechanism | Oracle |
|---|---:|---|---|
| Fingerprint reuse (`parallax`, `nmReindexStats`) | 2 | `source-global-literal-int-v1`, already one of the 44 | `future-precompute/cheap-unlocks/` |
| `round` admission (`posterize`) | 1 | node identity; **`Math.round` semantics, not GLSL spec** | `builtins/oracle/` |
| `any` admission (`waves`) | 1 | node identity | `builtins/oracle/` |
| `reflect` admission (`lighting`) | 1 | node identity | `builtins/oracle/` |

`filter/lightLeak` is NOT in this list despite being a fingerprint-reuse
candidate: its terminal blocker is `unsupported parameter direction out`, an
unrelated capability. Assigning it to a loop-proof task is what turned an
incomplete change into an unbuildable tree once already — **screen every program
list against `census/frontier-census.json` before assigning it.**

## Loop-proof: what landing two programs actually cost (2026-08-13)

`filter/zoomBlur:zoomBlur` and `filter/reindex:nmReindexStats` landed, taking
the typed slice to **154** (typed-list SHA-256
`611e4bb44c1d5ef45c2ea0c1715c3f879b76f691e9b8a9fea102ff11210c0e77`).

### The cluster is smaller and dearer than the study claims

Of the three programs the loop-proof study called "clean fingerprint-only
reuse, no vocabulary change", **one** was real:

| Program | Reality |
|---|---|
| `filter/reindex:nmReindexStats` | landed |
| `filter/lightLeak:lightLeak` | terminal blocker `unsupported parameter direction out` |
| `filter/parallax:parallax` | terminal blocker `unsupported builtin textureLod` |

And "no vocabulary change" is wrong: `source-global-literal-int-v1`'s **key set
is itself pinned** — a test asserts `SOURCE_GLOBAL_LITERAL_INT_KEYS` equals
exactly the six task23 keys, so a seventh breaks it.

**Batch, never increment.** Landing one program cost ~24 historical-reconstruction
repairs; landing two cost the same ~24. That repair cost is fixed per batch, so
incremental landing multiplies it for no benefit.

### Float induction was widened deliberately, and the barrier re-armed

`zoomBlur` needs a float induction variable, which
`test_counted_for_v1_rejects_header_and_control_near_misses` forbids. The right
move — done here — is to move `float-induction` into the ACCEPTED set naming the
program that justifies it, and add **two new rejections at the new boundary**
(`float-fractional-start`, `float-fractional-bound`) proving only
exact-integer-valued float literals are admitted. An earlier attempt simply
widened the guard; four generator gates and 171 native tests passed while the
barrier sat disarmed, and only the Python suite caught it.

### Do NOT script the exclusion-set repairs

Three scripted attempts failed, each differently: matching line endings can't
tell a set literal from a dict entry; running the chain rewrite before the
element rewrite makes the second match what the first just moved; and a rule
keyed only on punctuation corrupts grade-specific DATA.

Of 25 sites carrying `"filter/grade:wheels"`, **six must never be touched** —
`LUMA_KEYS`, `ALL_KEYS`, the `SOURCE_FILES` map, two count maps, and a
`LUMA_PROFILES[...]` subscript. They are syntactically identical to exclusion
sets and semantically unrelated. Classify by the ENCLOSING TEST, then edit.

### Snapshot restores defeat incremental builds

`tar` restores original mtimes, so after extracting a snapshot the build system
sees sources older than the objects and rebuilds nothing. A stale binary then
reports tests that no longer exist in the source and passes. Always
`touch` the sources (or delete the build dir) after restoring, or you will
validate the code you just discarded.

## Global admission + mat3: the blocker is not what it was labelled

Full analysis in `global-admission/global-admission-design.md`. The census's
verified blocker table reproduced byte-identically against the live 154-program
tree, but the *interpretation* of the largest bucket was wrong.

**The "matrix indexing" gate behind 6 of the 7 mat3 programs has nothing to do
with matrices.** It is a byte-identical shared helper — `vec3 linearToSrgb(vec3
linear)` doing `linear[i]` inside a `for (i < 3)` loop. That is the *same*
vec3-lane-index shape Task 32 already solved for the grade cluster. It was
mislabelled because alphabetical validation order surfaces it before the matrix
error. Confirmed by debug instrumentation proving zero index-nodes are visited
before that first error, including in `shapeMixer`.

**Consequence**: extending the existing grade index-expression profile to these
programs is probably the real unlock, not new matrix work. `glsl::Mat<N>` and
`Mat3` already exist and compile — there is nothing to build in the runtime.

### Honest slice size: 4-5, not 7

| Program | Verdict |
|---|---|
| `classicNoisedeck/cellNoise` | clean |
| `filter/adjust` | clean |
| `filter/colorspace` | clean |
| `classicNoisedeck/colorLab` | same profile, 2 sites — likely +1 |
| `classicNoisedeck/moodscape` | entire matrix+hash closure is DEAD at authorized defines (live BFS from `main()`); needs a dead-code exemption, which is cheaper than real support |
| `classicNoisedeck/shapeMixer` | EXCLUDED — needs `reflect`, `refract`, a `mod(vec3,vec3)` overload, the shared vec3-index gate, and `floatBitsToUint` before mat3 is even binding |
| `classicNoisedeck/shapes` | EXCLUDED — multi-cluster: mat3 + vec3-index + reachable `floatBitsToUint` + probably the bitwise-XOR cluster |

### CORRECTION to this roadmap's matrix-matrix narrowing hazard

An earlier entry here recorded that the JS `matrixMult` helper accumulates into
a plain `Array` and therefore never narrows, making matrix-matrix products a
Curl-tanh-class divergence. Reading the **currently shipped**
`canonical-kernels.js` directly shows `matrixMult()` narrowing per-element in
both branches. Two independent findings now agree that mat3*vec3 is emitted as
unrolled scalar arithmetic narrowing once per component via
`Float32Array`/`Math.fround` — structurally identical to
`glsl::Mat<N>*Vec<N,float>`.

Treat the matrix-matrix hazard as **unconfirmed** rather than established, and
re-derive it from the shipped JS before acting on it for mat4 / `glitch`.

## Singleton triage — the tail is costed (see `singletons/singleton-triage.md`)

All run against the real validator in-process on a byte-identical copy of
`tools/glslcpp`.

| Program | Terminal blocker | Reachable | Cost |
|---|---|---|---|
| `synth/bitwise:bitwise` | `unsupported binary operator ^` | yes | **cheap** — sole blocker |
| `classicNoisedeck/caustic:caustic` | profile-carrier check | **NO — dead, third independent confirmation** | **cheap** — slice-row wiring only |
| `filter/lighting:lighting` | `unsupported builtin reflect` | yes | **cheap-ish** — its 2nd blocker (`float[9]` Sobel kernel) reuses the ALREADY-SHIPPED `filter/sobel` mechanism |
| `classicNoisedeck/glitch:glitch` | `unsupported typed type mat4` | yes | moderate — 3-hop chain, one mechanism family |
| `filter/watercolor:wcSimplify` | `inout` parameter direction | yes | moderate — and see the emitter gap below |
| `synth/remap:remap` | `unsupported uniform block` | yes | **expensive** — 2nd blocker is a 267-entry uniform array with runtime-computed indices; no existing bounded mechanism fits |
| `mixer/distortion:distortion` | `unsupported sampler parameter` | yes | **most expensive** — traced >=4 hops (sampler-param -> sampler-expr -> dFdx -> its own `float[9]`) |

### Previously undocumented emitter gap

Admitting `inout` makes `wcSimplify` pass the **validator**, and then the
**emitter** fails: it has zero support for a bare void-call statement, which
that program needs 19 times. Budget for emitter work, not just admission.

### Multi-program blockers, now counted exactly

- `out` / `inout` parameter direction gates **3** programs: `lightLeak`,
  `watercolor`, and newly-found `mandelbrot`.
- `textureLod` gates exactly **1**: `parallax` (confirmed as its final blocker).

### THE CENSUS IS NOW STALE — re-screen before batching

`loop_proof.py`'s admitted set was widened after the census snapshot, so two
programs' terminal blockers have moved:

- `filter/oilPaint:oilFlatten` -> now `ceil`
- `filter/smooth:smoothBlend` -> now a global-declaration issue

Both were on the planned six-program loop-proof batch. **Re-run the blocker
probe against the live tree before assigning any program list** — this is the
third time a stale or mislabelled blocker has broken a batch.

### Further corrections

- `classicNoisedeck/shapeMixer` needs **`refract`**, not `reflect`.
- `filter/waves` needs **`bvec2`** as well as `any` — `any` alone is insufficient.
- New singletons not previously listed: `filter/grime:grime` (varying admission,
  1 terminal + 3 downstream) and `synth/shape:shape`.

## Loop-proof oracle-b: 7/8 covered, and three structural discoveries

Full report at `loopproof/oracle-b/loopproof-b-oracle-report.md`. 24 cases,
14 mutations, all empirically diverging; `--check` deterministic (3 runs).

### `classicNoisedeck/fractal` has NO canonical factory at all

`generatedBytes: 0` — permanent adapter-only routing, and **the adapter
implements a different julia/newton/mandelbrot algorithm than the corpus GLSL
source**. This is the same class as `wormhole:deposit`: the fragment program is
not what the reference executes. It cannot be ported from its GLSL, because the
GLSL is not the behaviour. The oracle covers the adapter's `julia()` loop only;
`newton()`/`mandelbrot()` are explicitly out of scope, not silently dropped.

### SECOND PRODUCTION DEFECT — `filter/median`'s canonical factory crashes

`canonicalFactory80` throws a `TypeError` inside `$runtime.copy` on a plain 5x5
render, while 4x4 and 6x6 render fine. Size-dependent, previously undocumented,
and independent of the loop-proof gate. The oracle targets `medianFactory` (the
working adapter twin) instead — the same precedent the wormhole oracle set.

This is the second live defect this port has surfaced in the JS renderer, after
the dither error-diffusion crash.

### A genuine infinite loop in median's Hoare partition

Mutating the inner boundary (`scanLeft <= scanRight` -> `<`) hangs forever —
verified live, ran past a 120-second watchdog and had to be killed. Avoided as a
mutation site; both median mutations instead cap the *outer* convergence loop
with a provably terminating counter. Worth knowing before anyone fuzzes this
program.

### `classicNoisedeck/effects` is uncoverable at its authorized define

Every loop in the file sits behind `if (EFFECT != 0)`, and the authorized define
is `EFFECT=0`. Proven rather than asserted: the same loop mutation shows **0/4
divergence at the authorized default and diverges at an unauthorized
`EFFECT=1` control**, so the loop and the mutation are both real — the code is
simply dead at the only define value the reachability rule permits.

## `synth/bitwise:bitwise` — LANDED, and a real narrowing bug found+fixed (2026-08-13)

Typed count **156** (typed-list SHA-256
`faed9f083ae6ef4cdece48e1cba52f7c6308ac0cae2bd311e4b648d64d65aacc`). Native
**172 PASS / 0 FAIL**. All four generator gates green
(`check_corpus --check`, `check_semantics --check`,
`generate_typed_slice --check`, `generate_kernels --check`).

### Mechanism: scalar-int `&`/`|`/`^`/`~`, node-identity, zero vocab growth

New module `tools/glslcpp/frontend/bitwise_scalar_int_ops_profile.py`
(`bitwise-scalar-int-ops-v1`), same shape as the Perlin/caustic scalar-uint-XOR
precedent. `APPROVED_BINARY_OPERATORS` gained `&`/`|` (an AST-level operator
allow-list, NOT the frozen 44-entry capability vocabulary — that stayed at 44).
`&`/`|`/`^`/`~` on scalar `int` are admitted only for the 10 exact,
source-hash-gated node identities in `bitOp()` and `main()`; every other
program's use of these operators (none exist yet) would still be rejected.
Confirmed live: **zero shift operators** anywhere in the program (re-verified
both by source grep and a regex assertion against the compiled
`canonicalFactory244` text), so the signed-vs-logical shift hazard
(`glsl::shift_right_arithmetic`) does not apply here — only `&`/`|`/`^`/`~`,
which are exact two's-complement bit-for-bit matches between JS ToInt32
semantics and C++20 `int32_t` (representation is mandated; no shift, no
sign-extension ambiguity).

### NEW hazard found, not in any prior document: `float(int)` premature narrowing

`bitOp`'s `return float(r) / float(m);` looks like a harmless GLSL-spec cast,
but the compiled JS (`canonicalFactory244`) materializes both `float()` calls
as **identity no-ops** — `return (r) / (m);`, full double precision, narrowed
to float32 exactly once at the `Float32Array` store. The C++ emitter's general
`float(intExpr)` constructor rule narrows immediately instead. Invisible for
every other `float(int)` site in the corpus because those operands never
exceed float32's exact-integer range (`2**24`); `bitOp`'s AND/XOR/OR/NAND/XNOR
results can be arbitrarily large in magnitude, so the extra narrowing step is
observable — caught by the vendored oracle (`and-rgb-int32min-offsets-near-
max-mask`, pixel (0,0): premature-narrow gives `0x3d420420`, real runtime
gives `0x3d420421`, a 1-ULP miss that a byte-quantized RGBA8 comparison alone
would have hidden — the RGBA8 hash matched even with the bug present).

**Fixed by node identity, not a blanket rule change** — the roadmap's own
standing hazard #1 warns a blanket unary-macro fix regressed three programs
once. `authenticate_bitwise_int_to_float_narrowing_skip` (same module)
authenticates the exact two `construct` nodes in `bitOp`'s return statement;
the emitter emits `static_cast<double>(...)` for those two nodes only and the
untouched general `float(intExpr)` rule still governs every other program.

### Oracle: vendored, and it directly caught the bug

`tests/oracles/task-35-oracles.json` (byte-identical copy of
`docs/port-engineering/future-precompute/cheap-unlocks/bitwise-oracles.json`,
sha256 `10b01899cbc1e125594f0d8094c98188bc88778a72248b565865b36994727687`
— re-frozen 2026-08-30 as a dual-architecture package; the copy was
`df6f50adbd60ffc7ca30720bf8f09f47cfc339be6d10203f5238be6008b3bf9b` while it
carried only the arm64 capture).
Unlike the grade cluster (texture input, unreproducible synthetic image) and
unlike zoomBlur/reindexStats (oracle vendored but never wired to a consuming
test), `synth/bitwise:bitwise` has **no texture input at all** — a pure
fragCoord generator — so its oracle hashes are directly, byte-exactly
reproducible in the native suite. New test
`typed_task35_bitwise_scalar_int_ops_oracle_cases_are_bit_exact` in
`tests/test_generated_kernels.cpp` renders all 6 cases (5 real + 1 mask=0
divide-by-zero diagnostic asserting NaN in every channel) through both the
direct binder and the catalog dispatch, and compares full-buffer f32 and RGBA8
SHA-256 against the oracle. All 6 pass after the narrowing fix; case 2
(`and-rgb-...`) is the one that caught the bug — traced against the real
`canonicalFactory244` JS via a throwaway instrumented copy (never the real
`noisemaker-for-cpu` checkout) to find the root cause rather than guessing.

**A second bug in my own harness, also worth recording**: the oracle's
per-case `time` field is not always 0 (`0.75` and `2.3` for two of the six
cases) — GLSL `uniform float time`, bound via `Bindings`, independent of
`run_pass`'s own `time` parameter (unused by this program). Missing this
produced a *different* wrong hash and cost a full trace-and-diff cycle to
isolate from the real narrowing bug.

### Historical-reconstruction repair count for this batch: ~24, matching precedent

Every `spec["programs"] = [item for item in ... if key not in {...}]` /
`!= "key"`-chain historical reconstruction in `tests/test_typed_generator.py`
needed `"synth/bitwise:bitwise"` added — **to the exclusion set** if the test
mocks `load_slice` and hash-compares `generate_outputs()` byte-for-byte
against a frozen historical artifact (ordinal numbers are position-dependent,
so a present-but-uncounted-for new program shifts every later `typed_N`
namespace); **left present, with counts/hashes recomputed**, only for the
tests explicitly marked "NOT a historical reconstruction; see the note on
`test_task21_degauss_exclusions_remain_closed`" (narrow denylist tests that
deliberately let later-added programs ride along). Classified by reading each
enclosing test, never by pattern-matching the exclusion-set text — several
near-identical-looking blocks needed opposite treatment. Every recomputed
value was produced by running the real `load_slice()`/`generate_outputs()`
against the live tree with the candidate change applied, never by hand
arithmetic. Live-state pins updated in matched pairs (native catalog test
renamed `..._one_hundred_fifty_seven_...` -> `..._one_hundred_fifty_eight_...`,
size `157U`->`158U`, catalog array gained the new key at its sorted position;
Python-side `155`/`156`/`157`/`158` counts and their SHA-256 hashes updated
together, never one without the other).

### Full validation

`generate_typed_slice.py --write` then `--check`: clean. Native
`noisemaker-cpu-tests`: 172/172. Python suite: kicked off in a fresh full-tree
copy (`.nm-validate/nm2-final/`) after all fixes landed; two earlier partial
runs against stale pre-fix copies showed exactly the expected, already-
diagnosed failures (confirming the fix set was correctly targeted) and are not
evidence of anything wrong with the live tree.

## `filter/lighting:lighting` — LANDED, and Batch A (colorLab/moodscape) re-screened OFF the queue

Typed count **160** (typed-list SHA-256
`5e3124aea60e4e4f745d8c580e295bd68ab77661f0953a0152898476cec0f215`). Native
**174/174** (172 pre-existing + 2 new). All four generator gates green
(`generate_typed_slice --check`, `check_corpus --check`, `check_semantics
--check`, `generate_kernels --check`).

### Batch A re-screen: `colorLab` and `moodscape` are NOT the cheap wins the design doc promised

Re-screening `classicNoisedeck/colorLab` against the live tree with the
`linear_srgb_lane_index_v1` profile extended (locally, in-memory only) shows a
**3rd blocker the design doc's §5 table missed**: `main()` has 3 additional
`index` nodes outside the `linearToSrgb`/`srgbToLinear` closures — one indexes
a **function-call result** (`base.kind == "call"`), which the validator's
index handler rejects unconditionally before any profile check even runs
(`if len(value.children) != 2 or value.children[0].kind != "id": raise`); the
other two are literal-int indexes into a plain local `vec3` (a shape the
existing `literal_vec3_lane_index_profile` handles only for its own two
locked keys, not generically). `colorLab` needs a new admission mechanism for
"index a call-result / arbitrary local vec3 by literal int", not just the
existing profile applied twice.

`moodscape`'s whole matrix+hash closure being dead is confirmed correct (BFS
from `main` at `COLOR_MODE=2, NOISE_TYPE=10` excludes it), but landing it
needs a genuinely new mechanism — whole-**function** dead-code exemption
(skip validation AND emission for functions proven unreachable), not a
node-identity exemption like Perlin's/Caustic's (those are dead **nodes**
inside otherwise-live functions; moodscape's dead set is 15 whole functions
of assorted shapes, so exempting them node-by-node would mean rediscovering
and re-authenticating a different construct in each one). Neither program was
landed this session — re-screening cost was worth it; forcing either through
without the missing mechanism would have risked an unverified or broken
landing.

### `filter/lighting:lighting` — landed instead, via two narrow, precedented mechanisms

1. **`reflect(vec3,vec3)` admission** — new module
   `tools/glslcpp/frontend/reflect_admission_profile.py`, single node-identity
   exemption for lighting's one call site (`applyReflection`), same
   zero-vocabulary-growth pattern as `round`/`tanh`/`floatBitsToUint`. `glsl::
   reflect` already existed in `glsl_runtime.hpp`, generic over `Vec<N,float>`,
   already implementing `I - 2*dot(N,I)*N` with no defensive normalize — no
   runtime change needed.
2. **The Sobel-shaped normal-map convolution** — `calculateNormal`'s three
   `float sobel_x[9]`/`sobel_y[9]`/`vec2 offsets[9]` tables are byte-identical
   in shape to the already-shipped `filter/sobel` mechanism
   (`fixed_nine_table_proof.py`), with one difference: they live inside a
   **helper function**, not `main()`. Generalized the module's hardcoded
   `"main"` lookup to a per-key `_HOST_NAME` table (`LIGHTING_KEY:
   "calculateNormal"`) — the proof's structural requirements (loop shape, read
   pattern, literal-store shape) are otherwise untouched, and sharpen/sobel's
   own admission was re-verified unaffected by the generalization.

### A real, pre-existing `std::pow`-vs-V8 ULP hazard, found and root-caused, not chased

Building the native oracle test (4 cases from
`docs/port-engineering/builtins/oracle/builtin-oracles.json`'s `lighting`
entry, texture inputs reproduced via the same `patternedSurface` formula
Task 33's oracle already uses) surfaced 2 of 4 cases with a handful of 1-3 ULP
mismatches. Root-caused against the real unmodified JS reference (both
renders reproduced independently in Node, diffed pixel-for-pixel) rather than
assumed: the divergent lanes are confined to the unconditional
ambient/diffuse/specular Blinn-Phong term's `pow(specAngle, shininess)`, not
to `reflect()` or the Sobel table. Proof it's unrelated to `reflect()`: one of
the two failing cases sets `reflection=0`, so `mix(workingColor,
reflectedColor, reflection/100.0)` returns `workingColor` bit-exactly
regardless of `reflectedColor`'s value (0 times any finite value is exactly
0) — yet it still shows a 1-ULP mismatch, which can only come from the
lighting term every case computes unconditionally. This is the already-
documented, already-accepted `std::pow`-vs-V8 hazard from this roadmap's own
transcendentals section (pow measured at a 0.041% mismatch rate at double
precision; `glsl::pow` intentionally stays on `std::pow`, not fdlibm, per
that section's explicit decision not to chase pow to literal zero). Landed
only the 2 bit-exact cases (`reflection-strong-sign-matters`, live and
reachable; `all-off-diagnostic-no-reflect-call`, proves the reachability
guard) with the other 2 documented in-place rather than silently dropped —
matches this project's standing "root-cause through the real JS rather than
adjusting an expectation" rule.

### A real dangling-pointer bug in the native test itself, found by ASan-style crash triage

The first cut of the native oracle test crashed (`SIGSEGV` in
`sample_nearest_bottom_left`, reproducible) because `Bindings::set_texture`
stores a raw pointer to the `Surface` it's given
(`textures_.insert_or_assign(std::move(name), &surface)` — no copy), and the
test passed `task33_patterned_surface(...)`'s return value as an **inline
temporary** directly into `set_texture(...)`, which is destroyed at the end
of that statement. Fixed by naming both `Surface` locals so they outlive the
`Bindings` and the `run_pass` call that consumes them (matches the existing
Task 33 tests' pattern, which already gets this right).

### Historical-reconstruction repair count: ~24 sites, plus 8 pre-existing failures inherited from the prior batch, folded in

Every `spec["programs"] = [item for item in ... if item["program_key"] not in
{...}]`-style historical reconstruction across `tests/test_typed_generator.py`
needed `"filter/lighting:lighting"` added to its exclusion set (count/hash
recomputed from the real `load_slice()`, never by hand) or, for the "narrow
denylist, let later programs ride along" tests
(`test_task21_degauss_exclusions_remain_closed` and its Task 22 CRT twin),
just the target count bumped. Also found and fixed, independent of this
landing (pre-existing since at least the `synth/bitwise` batch, unrelated to
Slice A): a missing `classicNoisedeck/caustic:caustic` entry in the committed-
manifest defines census, a missing `"mat3"`/`"&"`/`"|"` in the Task 11
frozen-vocabulary assertion, 3 `AttributeError`s in hand-constructed
`object.__new__(_Emitter)` test fixtures that never got every `authorized_*`/
`emitted_*` field added as new profiles landed, and one stale generated-
namespace ordinal (`typed_66` → `typed_71`) in a resource-contract test. The
coordinator's independently-run v159 baseline showed exactly 8 of these
(5 failures + 3 errors); all 8 confirmed fixed by direct single-test reruns,
and the full suite was re-validated end to end in a fresh copy afterward.

## Batch: two free programs + `nmReindexReduce` cap widening (2026-08-13) -- and three re-screened corrections

Typed count **163** (typed-list SHA-256
`fb9466c45bc5b8cd19a69bdcd2948f7dfdf68b8aa1e76d9fc6b35a76ff5496a7`). Native
**174/174** at both `-DCMAKE_BUILD_TYPE=Debug` and `Release`, exit 0 both
times. All four generator gates re-run individually and green: `check_corpus
--check` (`check_corpus: ok`), `check_semantics --check` (`bodies ok (212
programs)`), `generate_typed_slice --check` (`typed slice ok (163
programs)`), `generate_kernels --check` (silent success, exit 0).

### Landed: `filter/invert:inv`, `synth/solid:solid`

Re-screened live (parse -> `validate_capabilities` -> `render_typed_cpp`):
both `validator: pass` / `emitter: pass` with zero blockers, confirming the
census's "two programs are free today" finding still holds. Added as
minimal `{"defines": {}, "program_key": ...}` slice rows -- no profile, no
mechanism work. Both already had a pre-existing, independently-tested
hand-written "adjacent" adapter (`bind_filter_invert`/`bind_synth_solid`)
hardcoded into `render_catalog_header`'s factory list from before either
program was typed; landing the typed counterpart does not retire that
adapter (see below).

### Landed: `filter/reindex:nmReindexReduce` -- deliberate cap widening, not a fingerprint reuse

This is a different kind of landing than every prior `source-global-
literal-int-v1` entry: those were all pure fingerprint reuses at trip/
product/charge well inside the original 128/4096/4096 caps. This program's
`for (ty=0; ty<MAX_TILE_DIM; ++ty) { if (ty>=tileCount.y) break; for (tx=0;
tx<MAX_TILE_DIM; ++tx) { if (tx>=tileCount.x) break; ... } }` genuinely
needs `MAX_TILE_DIM=512` as a proven loop bound (real per-loop trip count
512, nested lexical product 512*512=262144, whole-program entrypoint charge
262656) -- all three exceed the original caps and were raised **exactly** to
these three values, not to a round number, named
`COUNTED_FOR_V1_MAX_TRIP_COUNT`/`_MAX_LEXICAL_PRODUCT`/`_MAX_ENTRYPOINT_
CHARGE` in `tools/glslcpp/frontend/loop_proof.py` and imported by both
`generate_typed_slice.py` and `emit_typed_cpp.py` (previously two
independent literal-`4096`/`128` copies per file; now one shared constant
definition so the validator and emitter checks cannot drift apart). The
source's own `MAX_TILE_DIM` guard is byte-identical to the cap already baked
into the JS transpiled from this same GLSL, so 512 is the true worst case
for bit-exact parity, not a defensive overestimate -- confirmed no runtime
texture-size preflight is needed (unlike the never-landed Task 47 design in
`post-resource-bound-loop-frontier-audit.md`, which assumed one was
required).

**A new near-miss boundary, moved deliberately.** `trip-129` in
`test_counted_for_v1_rejects_header_and_control_near_misses` and
`nested-product`/`entry-charge` in
`test_counted_for_v1_rejects_effective_depth_product_charge_and_call_cycles`
encoded the *old* 128/4096 boundary; left as-is they would have started
passing at the *new* boundary for the wrong reason (looking thorough,
proving nothing). All four (`trip-129`->`trip-513`, `scan-512`->`scan-513`,
`nested-product`, `entry-charge`) were bumped to values that safely exceed
the new caps -- verified by actually running each through
`validate_capabilities` before editing the test, not by hand arithmetic
(kept as the same tests, not new ones, since they test the same mechanism
at its new true edge). `nested-product` needed a third nesting level: at the
new caps, `512*512` sits exactly ON the product boundary (not past it) and
is simultaneously the per-loop trip cap, so a 2-level nesting can no longer
isolate "product exceeds while every individual trip count stays admitted"
the way `65*65` could against the old, unrelated 4096/128 pair.

**Schema generalized: one program can now admit more than one global int.**
Every previous `_SOURCE_GLOBAL_LITERAL_INT_PROFILES` entry admits exactly
one designated global (the "integer"/"reads" singular keys) because that
was always sufficient before. `nmReindexReduce` has two source globals used
as plain `int`s -- `MAX_TILE_DIM` (the loop bound) and `TILE_SIZE` (used
only in ordinary arithmetic, `(statsTexSize.x + TILE_SIZE - 1) / TILE_SIZE`
and `tx * TILE_SIZE` -- never a loop bound). `TILE_SIZE` has no admission
path of its own: the emitter's source-global validator only accepts a
`float`-typed const global generically, or an `int` if its symbol id is in
the returned bound-seed set. Extended `authenticate_source_global_literal_
int` to accept an optional plural `"integers"`/`"reads"` (tuple of 4-tuples
/ tuple of per-integer reads-tuples) schema, authenticating each admitted
integer with the identical checks as the singular path and returning one
seed per integer; the singular six existing profiles are untouched (still
read via `(expected["integer"],)`/`(expected["reads"],)`), so none of their
frozen hashes moved. All downstream consumers
(`attach_counted_loop_proofs`'s `source_global_bounds` parameter, and the
emitter's `admitted_literal_ints` set) were already generic over an
arbitrary-length seed tuple -- only the single authentication function
needed generalizing.

Every hash in the new profile entry (`raw`/`source`/`pre_functions`/
`post_functions`/`pre_whole`/`post_whole`/`interface`, plus both integers'
`reads` lists) was computed by running the real `analyze_program` /
`attach_counted_loop_proofs` / `summarize_counted_loop_proofs` against the
live tree, never by hand.

### CORRECTION -- `render_catalog_header`'s dual registration is a coexistence, not a migration

Landing `filter/invert:inv`/`synth/solid:solid` through the typed slice does
**not** retire their pre-existing hardcoded legacy catalog entries
(`bind_filter_invert`/`bind_synth_solid`, implemented in `src/generated/`
and still exercised directly by name in `test_generated_kernels.cpp`). Both
now coexist under the identical public key, each catalog key appearing
twice adjacently. `bind()` does a linear first-match scan and the untouched
legacy factory sorts first (`"bind_filter_invert" <
"bind_filter_invert_inv"` lexically), so **production dispatch through
`bind()` is completely unchanged** -- the new typed factory is reachable
only by its own name (`bind_filter_invert_inv`/`bind_synth_solid_solid`) or
directly via the typed slice's own tests, existing as an independently
bit-exact-verified shadow implementation rather than a replacement. This
was not obvious going in -- the first attempt at this landing assumed
`filter/invert:inv` had no prior catalog entry at all, and the frozen
catalog test (`typed_slice_catalog_is_exactly_one_hundred_sixty_two_
sorted_unique_keys_and_excludes_adjacent_programs`) failed on the size pin
before this was understood. Renamed to
`typed_slice_catalog_is_exactly_one_hundred_sixty_five_sorted_keys_with_
dual_registered_invert_and_solid`; the strict `<` adjacency check became
`<=` with an explicit assertion that any equal-adjacent pair is one of
exactly these two known keys (so a *third* accidental duplicate would still
fail loud), and `invert_count`/`solid_count` moved from `==1U` to `==2U`.
Recomputed from the real generated `kCatalog` table, never by hand.

### Batch A re-screened again -- still not the clean group the queue described

Re-ran `parse_program` -> `validate_capabilities` for all four "likely
landable" programs against the live 160-then-163-program tree. All four
still fail identically at `unsupported counted-for program proof`, but
**none of the four is the fingerprint-only or cheap-mechanical case the
queue's framing implied**:

- `filter/blur:blurH`/`blurV`: `radius = int(radiusX * renderScale)`, a
  runtime product of two plain `float` **uniforms** with no `clamp()` and no
  const anywhere in the chain. Neither `_local_bound` nor `_start_value` in
  `loop_proof.py` can prove any upper bound on this -- there is no compile-
  time or texture-derived ceiling to appeal to, unlike every case the
  existing mechanisms cover.
- `filter/normalize:statsFinal`: bound is `inSize.y`/`inSize.x` from
  `textureSize(inputTex, 0)` directly, with **no compile-time cap at all**
  (unlike `nmReindexReduce`'s `MAX_TILE_DIM`-capped `tileCount`) -- an
  arbitrarily large input texture is an arbitrarily large proven-unbounded
  trip count.
- `filter/tetraColorArray:tetraColorArray`: `for (i=1; i<count; i++)` where
  `count` is a function **parameter** fed from `colorCount`, a bare
  `uniform int` with no clamp anywhere in the source. This is exactly the
  "call-site analysis for parameter/local-bound loops" bucket the loop-proof
  study named as harder work, and even call-site analysis would only
  forward the same unbounded-uniform problem one level.

All three shapes need a genuinely new mechanism -- a runtime resource-bound
/ preflight admission (matching what the never-landed Task 47 design
sketched for `nmReindexReduce`, which turned out not to be needed there
after all since that program's bound was compile-time-capped) -- not
available anywhere in the generator today. None landed this batch. This is
the fourth time this exact queue entry has been re-screened off after
looking clean on paper; the census and even the oracle report's own "Likely
landable" framing should be treated as unverified until re-run against the
live tree, every time.

### CORRECTION (same session, caught before landing anything wrong) -- derivatives are ALREADY LANDED; my first read of this was wrong

The paragraph originally here claimed the whole 15-17-program derivatives
mechanism (`DerivativeState`, node-identity admission, emitter lowering, the
`pass_runner.cpp` quad driver) was unbuilt, based on a builtin-usage scan
that only proved `fwidth`/`dFdx`/`dFdy` aren't in `_BUILTINS` -- which is
true of every node-identity-admitted builtin (`round`, `tanh`, `reflect`,
...) whether or not its mechanism exists, so it was the wrong test. A native
sanitizer run for unrelated reasons (see below) surfaced PASSing tests named
`typed_task33_..._matches_vendored_oracle_bit_exact` and `typed_task33_all_
fifteen_derivative_kernels_are_registered_and_report_uses_derivatives`,
which prompted a direct check: `tools/glslcpp/frontend/derivative_admission_
profile.py` exists, is 268 lines, and its own docstring says outright --
"`posterize` and `waves` are deliberately excluded: each has a second,
unrelated capability gap (`round`/`any`) that is out of scope for this
admission." `DERIVATIVE_ADMISSION_KEYS` already contains all 15 other
members (`bulge`, `celShadingColor`, `halftone`, `lens`, `lensWarp`,
`octaveWarp`, `pinch`, `polar`, `pondRipples`, `spiral`, `stThreshold`,
`step`, `stipple`, `tunnel`, `warp`), each with its own frozen whole-
program/interface/loop-proof/call-site record inside one shared
`derivative-admission-v1` profile, and all 15 are typed and native-tested
today. **The roadmap's own "Remaining work: node-identity admission;
emitter call lowering; `DerivativeState`... a quad driver in
`pass_runner.cpp`" framing under "Derivatives -- 17 programs" is stale** --
that work is done. Landing posterize and waves is therefore genuinely just
what the "Next targets" table said: `round` admission (posterize) and
`any`+`notEqual`+`bvec2` admission (waves), **plus** adding both keys to
the already-built `DERIVATIVE_ADMISSION_KEYS`/`_FROZEN_PROFILE_TUPLE_REPR`
(each program's own frozen record, computed from the live tree the same
way every other entry there was). Not attempted this session --
discovered too late in this batch to safely add without its own dedicated
verification pass -- but it is real, contained, next-batch work, not the
large undertaking the corrected-then-re-corrected text above implied.
**Re-screen `DERIVATIVE_ADMISSION_KEYS` directly before planning that
batch**, not this paragraph's history.

### Batch B re-screened -- `mandelbrot` needs a second, unrelated mechanism too

Re-confirmed `synth/mandelbrot:mandelbrot`'s terminal blocker is the same
`unsupported counted-for program proof` as `nmReindexReduce` (an unproved
loop -- `for (n=0; n<MAX_ITER; n++)`, likely a source-global bound similar
in shape to the one just landed). But the roadmap's singleton-triage table
already separately recorded mandelbrot under "`out`/`inout` parameter
direction gates exactly 3 programs: `lightLeak`, `watercolor`, and
`mandelbrot`" -- `mandelbrot_df64`'s six `out` parameters
(`out float smoothIter, out float rawIter, out vec2 z_final, ...`). Neither
blocker alone is sufficient: admitting the loop bound (a deliberate cap/
global-bound widening in the same family as this batch's `nmReindexReduce`
work) would only advance the terminal error to the `out`-parameter one, and
`out`/`inout` parameter direction has no admission mechanism anywhere in
the generator yet (a capability gating 3 programs at once, not a one-off).
Not attempted this batch; the roadmap's "deliberate, argued cap change"
framing for mandelbrot undersells the work -- it is at minimum two
independent mechanisms, one of which (parameter direction) is unbuilt.
`filter/median:median` (the other Batch B member) was not re-screened this
session; its terminal blocker is the already-documented JS reference crash
at `canonicalFactory80`, unrelated to either of the above.

### Historical-reconstruction repair for this batch

Two sites, both pin-consistency guards inside `generate_typed_slice.py`
itself (not a test-side historical reconstruction like prior batches): the
`len(keys) != 160` / SHA-256 `5e3124aea6...` combined drift guard (bumped to
163 / `fb9466c45b...`, recomputed from the real written `typed_slice.json`
via `"\n".join(sorted keys) + "\n"`, matching the exact formula at
`generate_typed_slice.py:814`) and the catalog-shape test in
`test_generated_kernels.cpp` described above. No `tests/test_typed_
generator.py` exclusion-set edits were needed for this batch -- none of the
three landed programs are named anywhere in that file's frozen historical-
reconstruction fixtures.

### Sanitizer lane -- one PRE-EXISTING finding, unrelated to this batch

Ran the same `-fsanitize=address,undefined` Debug lane this project's other
batches use. With `halt_on_error=1` it aborted; with `halt_on_error=0` all
174 tests still PASS (exit 0) and the sanitizer reports exactly one
diagnostic, in code this batch never touched:

```
src/typed_generated/typed_slice.cpp:15239:24: runtime error: signed integer
overflow: -2000000000 * 3 cannot be represented in type 'std::int32_t'
  in noisemaker::generated::typed_149::pixel(...)
  reached from typed_task35_bitwise_scalar_int_ops_oracle_cases_are_bit_exact
```

This is `synth/bitwise:bitwise`'s emitted `int32_t * int32_t`, inside a
program whose whole point is exercising near-`INT32_MIN`/`INT32_MAX`
two's-complement operands (see the `synth/bitwise:bitwise` LANDED section
above). The wraparound result is exactly what JS `ToInt32` semantics
require and the native oracle test for it passes bit-exact -- but the C++
multiply that produces it is undefined behavior per the standard even
though the platform's actual (non-sanitized) codegen wraps as needed. Not
introduced by this batch (nothing here touches bitwise's emitter path);
not fixed here (out of scope, and the right fix -- routing through an
unsigned-multiply-then-`bit_cast` primitive, the same shape as the signed-
shift primitive in `docs/port-engineering/shift-primitive/` -- is its own
small, deliberate, argued change, not a silent one). Recording it here
since no prior document mentions it and a sanitizer finding should never go
unrecorded once observed.

### Python suite

Kicked off in a fresh full-tree copy (`.nm-validate/v163/`, log
`.nm-validate/v163.log`) after all fixes landed; **not yet observed
complete on submission of this report** -- do not treat its absence here as
a claim of green. The four generator gates and the native suite (174/174,
Debug + Release + sanitize-with-known-pre-existing-finding) were
independently verified with real exit codes, per the standing rule to
report the Python suite as its own line.
