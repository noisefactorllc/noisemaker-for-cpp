# Loop-Proof Study — the non-canonical loop-shape frontier

Read-only design study. No writes to `noisemaker-for-cpp` or `noisemaker-for-cpu`.
All claims below are backed by a command actually run against the pinned
corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`; scripts and raw
JSON output live alongside this file in
`docs/port-engineering/loopproof/`.

## 0. Method

- `probe_loop_shapes_detail.py` imports the **real** frontend
  (`tools/glslcpp/frontend/parse_program`, `.../semantic.analyze_program`,
  `.../loop_proof.attach_counted_loop_proofs`) exactly as
  `generate_typed_slice.py` does, parses each program's pinned corpus source,
  attaches real counted-loop proofs, and walks every `for`/`while`/`dowhile`
  statement node recording exact structural facts (span, induction
  type/init, bound AST shape, update, `return`/`break`/`continue` in body,
  nesting depth, and — if proved — the exact `trip_count` /
  `lexical_depth`/`effective_depth`/`lexical_product`/`entrypoint_charge`).
  Output: `loop-shapes-detail-output.json`.
- **Important correctness note discovered while building this**: a
  `TypedStatement.span` is a position in `typed.source` (the *normalized*
  source — comments blanked, uniform prelude injected by
  `frontend/preprocess.normalize`), **not** in `typed.raw_source` (the
  pinned corpus file). Line counts differ (e.g. `synth/newton/newton.glsl`:
  332 raw lines vs. 314 normalized lines). The probe slices source text
  against `typed.source`; the line:column pairs reported below are exactly
  what the generator's own diagnostics use (verified: my span `33:5` for
  `filter/blur:blurH` matches `gate-chain-all-output.json`'s message
  `filter/blur:blurH:33:5: unsupported counted-for program proof` verbatim).
- `probe_reachability.py` builds the call graph from `call`-node
  `signature_id`s starting at `main()` (mirrors
  `roadmap2/reachability_probe.py`'s technique, which only covered the 35
  *mechanically-clearing* programs; this run extends it to the still-blocked
  loop-shape programs, which aren't in that file).
- Cross-checked against two prior read-only analyses already on disk:
  `roadmap/remaining-capability-roadmap.md` §3 (first-order shape
  classification) and `roadmap2/full-chain-frontier-map.md` +
  `gate-chain-all-output.json` (full sequential-patch gate-chain walk, which
  is what actually establishes *terminal* blockers, not just first
  blockers). Where my direct re-run disagrees with the older `roadmap/`
  numbers, I say so explicitly rather than silently adopting them — the
  project's own history here (`full-chain-frontier-map.md` §11, "the second
  time full-chain walking has reduced one") is to re-verify, not trust.

## 1. Deriving the 16 — which programs are *terminally* loop-shape-blocked

The task target is "non-canonical loop shapes, ~16 of the 79 remaining
programs." That 16 is **not** the same set as "programs whose gate chain
touches `loop_proof_bypass`" — there are **22** of those. Verified by walking
`gate-chain-all-output.json` (`rows[*].chain[*].classified_gate`):

```
classicNoisedeck/effects:effects        classicNoisedeck/fractal:fractal      classicNoisedeck/noise:noise
filter/blur:blurH                       filter/blur:blurV                     filter/dither:dither
filter/lightLeak:lightLeak              filter/median:median                  filter/normalize:statsFinal
filter/oilPaint:oilFlatten              filter/parallax:parallax              filter/reindex:nmReindexReduce
filter/reindex:nmReindexStats           filter/smooth:smoothBlend             filter/tetraColorArray:tetraColorArray
filter/zoomBlur:zoomBlur                synth/gabor:gabor                     synth/julia:julia
synth/mandelbrot:mandelbrot             synth/newton:newton                   synth/testPattern:testPattern
```

Walking each row's chain to its **terminal** entry (last patch applied,
still `BLOCKED`/`NO_GENERIC_PATCH`) splits this 22 into four groups:

| Subgroup | Count | Programs | Why excluded from "16" |
|---|---:|---|---|
| **Terminal loop-shape** (the target) | **16** | see §2 | terminal blocker really is the `for`/`while` statement itself |
| Budget-only, loop shape is fine | 1 | `synth/gabor` | `PASS`s outright once the per-loop safety-charge check alone is bypassed — no shape problem at all |
| Loop shape provably fine, but over budget *and* struct-blocked | 2 | `synth/newton`, `synth/julia` | after the budget bypass, next blocker is `unsupported struct declaration`/`unsupported typed type {POIData,JuliaResult}` — a different family (§5 of the full-chain map: "Struct member access") |
| Loop-shape-adjacent but a *different* gate is the actual terminal blocker | 3 | `classicNoisedeck/effects`, `classicNoisedeck/noise`, `filter/median` | `effects`/`noise` never get back to their loop — they die on `unsupported matrix constructor` / `unsupported matrix binary expression` first (matrix family); `median` reaches the loop shape (`while`) but the *walk's* terminal is a **further**, deeper blocker, `unsupported typed expression post` (post-increment on an unproven target) |

`22 − 1(gabor) − 2(newton,julia) − 2(effects,noise) − 1(median) = 16`.
Confirmed independently three ways: (a) walking the JSON by hand above, (b)
`probe_loop_shapes_detail.py`'s `TERMINAL_16` list cross-checked against the
same chain data (`terminal_16_count: 16` in the script's own output), and
(c) `full-chain-frontier-map.md` §5's table, row 1: "Non-canonical `for`-loop
shape | 16". This matches `full-chain-frontier-map.md` §7: 79 unported =
35 mechanically-clearing + 44 non-mechanical, and 44 = 16 (loop shape) + 9
(matrix) + 5 (varying) + 4 (struct) + 4 (array/table) + 1 (Caustic) + 5
(singletons).

**The 16:**

```
classicNoisedeck/fractal:fractal        filter/blur:blurH                filter/blur:blurV
filter/dither:dither                    filter/lightLeak:lightLeak       filter/normalize:statsFinal
filter/oilPaint:oilFlatten              filter/parallax:parallax         filter/reindex:nmReindexReduce
filter/reindex:nmReindexStats           filter/smooth:smoothBlend        filter/tetraColorArray:tetraColorArray
filter/zoomBlur:zoomBlur                synth/mandelbrot:mandelbrot      synth/noise:noise
synth/testPattern:testPattern
```

`effects`, `classicNoisedeck/noise`, and `median` are carried through the
rest of this study for context (their loops are genuinely non-canonical
too, and fixing loop-proof logic is a real prerequisite for them even
though it isn't their *current* terminal blocker), but they are **not**
counted in the headline 16.

## 2. The 30 unproved loop sites, grouped by shape

19 keys (16 + `effects`/`noise`/`median`) carry **30** unproved loop sites
total (matches `roadmap/`'s independently-derived count exactly). Every
`for`-loop bucket below was classified by re-implementing `_annotate_statement`'s
*exact* check order (`loop_proof.py:272-332`: induction storage → induction
type → single initializer → start-is-int-literal → condition
operator/shape → update-is-`++` → bound-is-literal-or-proved-symbol →
no-`return`-in-body) and recording the first failing check — i.e. this is
not guesswork, it's the real gate re-run per site.

| Shape (first failing precondition) | Sites | Keys | Programs (✓ = in the 16) |
|---|---:|---:|---|
| Bound reads a `const` **global** int, not proved | 8 | 6 | dither✓, lightLeak✓, parallax✓, reindexReduce✓ (×2), reindexStats✓ (×2), mandelbrot✓ |
| Start value is not an int literal (unary-negated parametric window, e.g. `-radius`) | 6 | 4 | blurH✓, blurV✓, dither✓ (×2), oilFlatten✓ (×2) |
| `while` loop (mechanism never proves non-`for`) | 4 | 1 | median (×4, **not** in the 16 — see §1) |
| Bound reads a function **parameter**, not proved | 3 | 3 | `classicNoisedeck/noise` (not in 16), tetraColorArray✓, `synth/noise`✓ |
| Bound reads a plain **local**, not proved | 2 | 2 | fractal✓ (`julia`), testPattern✓ |
| Induction variable is `float`, not `int` | 2 | 2 | effects (not in 16), zoomBlur✓ |
| Bound is a swizzle/member expression (resolution-derived) | 2 | 1 | statsFinal✓ (×2) |
| Multi-variable / non-declaration `for`-initializer | 1 | 1 | fractal✓ (`mandelbrot`, a *second* internal loop) |
| Bound reads a `uniform` directly | 1 | 1 | fractal✓ (`newton`, a *third* internal loop) |
| Loop body contains `return` (otherwise fully canonical) | 1 | 1 | smoothBlend✓ (`searchEdge`) |
| **Total** | **30** | **19** | |

**Correction to `roadmap/remaining-capability-roadmap.md` §3.3**: that
earlier pass reported "6 sites/5 keys" for the parameter-or-local-bound
bucket. Direct re-run finds **5 sites/5 keys** (3 parameter-bound + 2
local-bound, split above for precision) — one fewer site than previously
claimed. Everything else in the table matches the prior pass's counts
exactly (const-global 8/6, non-literal-start 6/4, while 4/1, float-induction
2/2, swizzle 2/1, multi-var-init 1/1, uniform 1/1, return-in-body 1/1).

`classicNoisedeck/fractal:fractal` is one program with **three** internally
different unproved loops (`julia` — local-bound; `mandelbrot` — multi-var
init; `newton` — uniform-bound) inside one combined fractal-selector shader.
Fixing "the fractal.glsl shape" is really three separate proof-logic
problems bundled in one program key.

Full per-site data (span, induction, bound AST, update, `body_contains`,
raw source text) is in `loop-shapes-detail-output.json`.

## 3. Provability assessment per shape

| Shape | Statically provable at all? | What a sound proof needs |
|---|---|---|
| **Const-global bound** | **Yes**, mechanically — this is exactly what `source-global-literal-int-v1` already proves for 6 *other* programs. | Nothing new in principle; see §4 for per-program caveats (one candidate's const is not a plain literal, two need budget increases too). |
| **Non-literal (unary-negated) start**, e.g. `for (int i = -radius; i <= radius; i++)` | **Yes, if `radius` is itself provably a small non-negative bound** (local const, clamped uniform, or a new "symmetric window" shape rule: bound = 2×proved_radius+1). Not provable if `radius` is an unclamped uniform/parameter with no upper bound. | A new structural rule recognizing `start = -B, bound = B` (or similar) where `B` is independently proved, computing `trip_count = 2B+1`. Checked concretely: `blurH`/`blurV`'s `radius` and `oilFlatten`'s `sampleLimit` are plain `int` **locals** derived from further expressions upstream in `main()` — need to trace whether those locals are themselves clamped before this rule could apply. Not confirmed clamped in this pass; flagged as needing its own upstream-trace probe before implementation. |
| **`while` loop** (median only) | **Not provable by any generic while-loop rule.** `median`'s 4 while loops are a hand-rolled Hoare quickselect over a **compile-time-fixed** array (`REAL_COUNT` = 9/25/49, driven by the `RADIUS` `#define`). A sound bound exists only via a program-specific combinatorial argument (e.g., "outer partition-narrowing loop runs ≤ REAL_COUNT times, inner scans ≤ REAL_COUNT comparisons each, so total work ≤ REAL_COUNT² ≈ 2401 comparisons worst case for RADIUS=3") — the same kind of whole-program authenticated proof as the existing `SHARPEN_KEY`/`SOBEL_KEY` `fixed_nine_table_proof.py`, **not** a shape rule that generalizes to other `while` loops anywhere else in the corpus (elsewhere a `while` could be genuinely unbounded). | A brand-new, `median`-specific whole-program proof carrier, hand-fingerprinted like the existing `fixed_nine`/`fixed_grid_counter`/`fixed_affine_centers13` precedents. Real, non-trivial combinatorics work, not admission-relaxation. |
| **Parameter/local-bound** | **Not provable from the callee alone.** `synth/noise:multires(int oct, ...)`, `filter/tetraColorArray:sampleColorArray(..., int count, ...)`, `classicNoisedeck/fractal:julia`'s `iterScaled` — none of these have a compile-time-visible upper bound at the point of the loop. | **Call-site analysis**: walk every call site of the owning function from `main()`, confirm every actual argument is provably bounded (literal, proved local, or a `clamp(...)`), and take the max as the loop's proved bound — genuinely new interprocedural proof machinery, not present today. If call sites can't all be proven, the only sound fallback is a **runtime-checked hard cap** (`for (int i=0;i<HARD_CAP;i++) { if (i>=count) break; ... }`) — a real semantic/behavior change (silently truncates rendering beyond the cap) that needs explicit operator sign-off, exactly the same shape `newton`/`julia`/`reindexReduce` already use in-source for their own (already-canonical) loops. |
| **Local-bound, `testPattern:renderNumber`'s `numDigits`** | Same as above, **and** it independently also has `return` inside the body (two separate violations stacked — see below). | Same call-site-analysis-or-hard-cap answer; fixing the bound alone would still leave the `return` gap blocking it. |
| **Float induction** (`for (float t=0.0; t<=40.0; t++)`) | **Yes, mechanically**, once the induction-type check is widened from strictly `int` to also accept `float` with an exact-integer literal start/bound and a unit (`++`, i.e. `+1.0`) step. `float t += 1.0` from an exact literal start is bit-exact for the small ranges seen here (`0.0..40.0`), so `trip_count` is computable exactly as `(bound-start)+1` the same as the int case. | Low-risk, narrow, mechanical widening of one type check — the closest thing to "free" among the structural (non-budget) shapes. Fixes **two** programs at once (`filter/zoomBlur` and `classicNoisedeck/effects`'s internal `zoomBlur`, byte-for-byte the same loop header, apparently copy-pasted). |
| **Swizzle/member bound** (`for (int y=0; y<inSize.y; y++)`, `statsFinal`) | **Provable only with a hard cap on supported texture dimensions**, or by proving `inSize` itself comes from a bounded source. `inSize` here is a `sampler2D`'s `textureSize()` result threaded through as a local — genuinely runtime/resolution-dependent, not a compile-time constant under any current allocation guarantee found in this pass. | Either (a) a documented maximum-supported-resolution hard cap baked into the proof (with a runtime `break`/clamp matching it — same trade-off as parameter-bound loops), or (b) treat resolution as an architecturally-bounded platform constant if one is established elsewhere in the codebase (not confirmed in this pass — flagged, not resolved, exactly per the prior roadmap's §9 callout). |
| **Multi-variable / non-declaration initializer** (`for (i = 0.0; i < float(iterations); i++)`, `fractal:mandelbrot`) | The **shape itself** (assignment instead of declaration) is mechanically fixable — widen the initializer-matcher to accept `expr-statement-assigns-existing-local` as well as `decl`. The **bound** (`iterations`, a `uniform`) is the harder, separate problem below. | Two independent fixes needed on the same loop: (1) accept non-declaring initializers structurally, (2) solve the uniform-bound problem next. |
| **Uniform-bound** (`for (int i=0;i<iterations;i++)`, `fractal:newton`, reading a `uniform` directly with no clamp) | **Not soundly provable without a compile-time clamp.** A `uniform` is an arbitrary externally-supplied runtime value — nothing in the GLSL text bounds it. | The codebase already has the answer for this exact situation: the single existing whitelisted `filter/reverb:reverb`-specific pattern in `loop_proof.py:243-254`, `clamp(uniform, 1, 8)` read into a local `const int`. `fractal:newton`'s loop has **no such clamp today** — it reads `iterations` raw. Two sound paths: (a) a source-level fix adding a clamp before the loop (outside this generator's remit), authenticated the same way `reverb` is, or (b) a generator-side runtime-checked hard cap + `break`, which is a real semantic change (silently caps iteration count) requiring explicit operator sign-off, not a transparent proof. **No admission-relaxation makes this sound** — flagged per the task's soundness requirement. |
| **`return` inside an otherwise-canonical loop** (`smoothBlend:searchEdge`, `for (int i=1;i<=32;i++)`) | **Trivially, always provable.** Start/bound/update are already fully canonical (literal `1`, literal `32`, `++`). A `return` inside the body can only ever **shorten** the number of iterations actually executed relative to the proved upper bound — it cannot extend it. The current blanket "any `return` in body ⇒ unproved" rule (`loop_proof.py:322`, `_contains_return`) is strictly more conservative than necessary for this case. | The single cheapest, lowest-risk fix in the entire shape family: drop the `_contains_return` veto specifically for loops whose start/bound/update are already otherwise canonical (the existing `trip_count` computation stays a valid **upper** bound regardless of early `return`). No budget or soundness argument changes at all — `return` inside a bounded loop is unconditionally safe. |

**Genuinely-impossible-to-soundly-prove-statically flag**: the `while` shape
(median) and the raw-`uniform`-bound shape (`fractal:newton`) are the two
cases in this family where *no* purely-structural static proof exists —
both require either a bespoke whole-program combinatorial argument (median)
or a source-level/generator-level runtime clamp with an explicit,
operator-approved behavior change (newton). Every other shape above has a
concrete, sound (if not yet built) static proof strategy.

## 4. `source-global-literal-int-v1` reuse — verified per program, not assumed

The older roadmap claimed 6 programs "could reuse that exact mechanism with
new fingerprints": `dither`, `parallax`, `reindex:nmReindexReduce`,
`reindex:nmReindexStats`, `lightLeak`, `synth/mandelbrot`. Checked each
against the mechanism's actual requirements
(`authenticate_source_global_literal_int`, `loop_proof.py:133-195`: the
const must have `storage=="const"`, `direction=="in"`, `type=="int"`, and
critically **`initializer.kind == "literal"`** — not a computed
expression):

| Program | Const | `initializer.kind` | Structurally qualifies? | Budget after reuse | Verdict |
|---|---|---|---:|---|---|
| `filter/lightLeak:lightLeak` | `POINT_COUNT = 6` | `literal` | Yes | trip=6, product=6, charge≈unchanged — well inside all caps | **Clean fingerprint-only reuse.** |
| `filter/parallax:parallax` | `MARCH_STEPS = 32` | `literal` | Yes | trip=32 — well inside all caps | **Clean fingerprint-only reuse.** |
| `filter/reindex:nmReindexStats` | `TILE_SIZE = 8` | `literal` | Yes | nested product = 8×8=64 — well inside all caps | **Clean fingerprint-only reuse.** |
| `filter/reindex:nmReindexReduce` | `MAX_TILE_DIM = 512` | `literal` | Yes, structurally | nested product = 512×512 = **262,144**, ~64× over the 4096 `lexical_product` cap | **Qualifies for the mechanism but also needs a budget-cap increase** — not fingerprint-only. See §5. |
| `synth/mandelbrot:mandelbrot` | `MAX_ITER = 500` | `literal` | Yes, structurally | `trip_count = 500`, ~4× over the 128 per-loop cap (`lexical_product`=500 is fine) | **Qualifies for the mechanism but also needs a budget-cap increase** — not fingerprint-only. See §5. |
| `filter/dither:dither` | `FS_ERR_W` | **`binary`** (`= FS_BLOCK + FS_APRON_MAX + FS_RPAD + 1`) | **No.** `authenticate_source_global_literal_int` raises whenever `initializer.kind != "literal"` (`loop_proof.py:171`). Verified directly: `FS_ERR_W`'s parsed initializer node has `kind="binary"`, not `"literal"`. | n/a | **Does not qualify as-is.** The mechanism would need extending to accept const-composed-of-consts initializers (constant-fold `const+const+const+literal` at admission time), which is new logic, not reuse. **And** `dither` has two *other* unproved loop sites in the same function (`errorDiffusion`'s `r`/`c` loops, both non-literal-start-bound, an entirely different shape) — fixing the const-global site alone would not unblock the program. |

**Correction to the "6 programs, same mechanism, just new fingerprints"
framing**: only **3 of 6** (`lightLeak`, `parallax`, `reindexStats`) are
true fingerprint-only reuse. `reindexReduce` and `mandelbrot` need reuse
*plus* a numeric budget increase (§5). `dither` doesn't qualify for this
mechanism at all in its current form, and even if it did, two more,
differently-shaped loop sites in the same program would still block it.

## 5. The three pure-budget cases — verified numbers and safety recommendation

Ran the real proof machinery (`attach_counted_loop_proofs` +
`summarize_counted_loop_proofs`) directly; every loop in all three programs
has `loop_proof is not None` (shape is fully canonical, `unproved_loop_count
== 0`) — these are exclusively over one or more of the four numeric caps.

### `synth/gabor:gabor` — depth only, cheapest case

- Structure (verified from source, `synth/gabor/gabor.glsl`): `main()` has a
  1-deep octave loop (`for(i<5){if(i>=oct) break; ... gaborNoise(...); }`,
  `oct`-controlled early exit). `gaborNoise()` itself has a 3-deep nest
  (`dy` in `[-1,1]`, `dx` in `[-1,1]`, `k<8` with `if(k>=impulses)break`).
- Measured: `max_effective_depth = 4` (violates the `<=3` cap: 1 [call site
  in main] + 3 [nested loops inside `gaborNoise`]) — this is an
  **interprocedural** depth combination, not one function nesting 4 loops
  directly. `entrypoint_charge = 425`, `lexical_product` (within
  `gaborNoise`) `= 72` (3×3×8) — both comfortably inside the `4096` caps.
- Worst-case per-pixel work: ≤5 (octave) × 3 × 3 × ≤8 (impulses) = **≤360**
  Gabor-kernel evaluations per pixel, each a handful of `prng`/trig calls.
  Already reflected in the measured `entrypoint_charge=425`, which is
  **9.6× under** the 4096 cap.
- **Safety recommendation: low risk, approve.** Raise `effective_depth`'s
  cap from 3 to 4 only (not further). The `lexical_product` and
  `entrypoint_charge` caps stay untouched and already bound the real
  per-pixel cost independently of the depth cap — the depth cap here is a
  structural/proof-complexity guard, not the thing actually limiting
  worst-case work for this program. Verified: `gabor` `PASS`es outright the
  instant the per-loop safety-charge bypass is applied (`gate-chain-all-output.json`
  row, depth 1 = `PASS`) — no other blocker.

### `synth/newton:newton` — the riskiest of the three

- Structure: literal-capped iteration with a runtime `break` —
  `for (int n=0; n<500; n++) { if (n >= maxIter) break; ... }` — containing
  a nested `for (int j=0; j<7; j++) { if (j>=intDeg-1) break; ... }` (df64
  complex-power expansion), plus a separate un-nested roots loop
  `for (int k=0;k<8;k++)`.
- Measured, per loop (4 loops total in `main`):

  | Loop | trip_count | lexical_product | entrypoint_charge |
  |---|---:|---:|---:|
  | `k<8` (roots) | 8 | 8 | 8008 |
  | `n<500` (Newton iterate) | **500** | 4000 | 8008 |
  | `j<7` (nested, complex power) | 7 | 3500 | 8008 |
  | `k<8` (second, normal-map pass) | 8 | 4000 | 8008 |

- **Two independent caps are violated, not one**: `entrypoint_charge = 8008`
  (**1.95×** over the 4096 program-level cap) **and** `trip_count = 500` on
  the `n<500` loop (**3.9×** over the 128 per-loop cap). The
  `lexical_product` cap (4096) is *not* violated (max observed 4000) — this
  is worth noting because raising `trip_count` alone without also raising
  `lexical_product` would leave headroom of only 96 before that cap also
  trips.
- This corrects the framing in `roadmap/`'s §3.2 ("Over budget:
  entrypoint_charge (8008>4096) | synth/newton") — that's true but
  incomplete: even with `entrypoint_charge` raised, the `n<500` loop
  independently fails the *separate* `trip_count<=128` check. **Both caps
  must move for `newton` to clear the budget gate at all.**
- Per-iteration cost: each of the 500 outer iterations does ~15-20 `df64_*`
  (double-float-emulated) complex arithmetic calls, plus the nested 7-trip
  complex-power loop (3500 total `df64_cmul` calls for that alone) — this is
  genuinely per-pixel work, not a single-invocation reduction pass.
- **Even after both budget caps move, `newton` still does not ship** — the
  next blocker in the full chain is `unsupported struct declaration` /
  `unsupported typed type POIData` (needs struct-member support, a wholly
  separate, larger capability — §5 of `full-chain-frontier-map.md`).
- **Safety recommendation: hold for explicit operator sign-off, and do not
  raise ahead of need.** This is the largest, most consequential relaxation
  of the three: it nearly doubles the global `entrypoint_charge` cap
  (propose ≥8192 if approved, with margin) *and* nearly quadruples the
  global per-loop `trip_count` cap (propose ≥512). Both caps are **shared,
  global constants** — raising them doesn't just admit `newton`, it raises
  the ceiling for every current and future per-pixel single loop and
  program-aggregate cost in the corpus. Given `newton` cannot ship from this
  change alone (struct support is still required), there is no immediate
  payoff to justify the relaxation now; sequence it together with struct
  support (§6) so the risk and the benefit land in the same slice.

### `synth/julia:julia` — the "already safe in aggregate" case

- Structure: two independent, un-nested loops (`juliaIterate`,
  `iterateSmooth`), each `for (int n=0; n<1000; n++) { if (n>=maxIter)
  break; ... }` — same literal-cap-plus-runtime-break pattern as `newton`,
  but with **no nesting**.
- Measured: `trip_count = 1000` on **both** loops (**7.8× over** the 128
  per-loop cap — the largest single-loop overshoot of the three cases), but
  `lexical_product = 1000` and `entrypoint_charge = 3000` — **both within**
  the 4096 caps, with real margin (3000 vs 4096, 27% headroom).
- Because there's no nesting, `julia`'s real aggregate cost (already
  reflected in `entrypoint_charge=3000`) is the thing that's actually
  bounded and safe; the per-loop `trip_count<=128` check is the *only*
  binding constraint, and it's more conservative here than the aggregate
  charge cap that already does the real safety job for this program.
- Per-iteration cost: a handful of df64 arithmetic ops (`dz` derivative
  update, `z = z² + c` in df64, bailout check, stripe/orbit-trap
  accumulation) — comparable per-iteration cost to `newton`'s outer loop,
  without the multiplicative nested blowup.
- **Like `newton`, `julia` also does not ship from a budget change alone** —
  next blocker after the budget bypass is `unsupported struct declaration` /
  `unsupported typed type JuliaResult`.
- **Safety recommendation: better-justified than `newton` (aggregate charge
  already safely under cap), but still a large single-cap relaxation
  (128→≥1000, ~8×) that is shared and global.** Given the no-payoff-without-struct-support
  situation is identical to `newton`'s, sequence together with `newton` and
  struct-member work rather than raising the cap speculatively now. If/when
  approved, consider whether the fix should be "raise `trip_count` globally
  to ≥1000" (blunt, large) vs. "loosen the per-loop `trip_count` check
  specifically when `lexical_product`/`entrypoint_charge` for that loop are
  already comfortably within cap" (narrower, safer, more proof-code work) —
  this second option is worth scoping since it would also make `newton`'s
  non-nested loops safer to admit without touching the global `trip_count`
  ceiling as aggressively.

## 6. Reachability and discriminability filters

Per the Task-31/32 lesson (`docs`/prior work: a wrong-output hazard on
unreachable or non-discriminating code doesn't get caught by full-render
parity, so both filters must be checked and stated, not assumed).

### Reachability

Built the call graph from `call`-node `signature_id`s starting at each
program's `main()` (`probe_reachability.py`, mirrors
`roadmap2/reachability_probe.py`'s technique — that file only covers the 35
mechanically-clearing programs, so this is fresh for the still-blocked loop
family). **Verdict: all 16 terminal programs' unproved-loop-containing
functions are reachable from `main()`** under the corpus's default define
map — no candidate is eliminated by reachability. (For contrast:
`classicNoisedeck/effects`'s `zoomBlur` function, which is **not** in the
16, actually **is** unreachable from `effects`'s `main()` — a real
reachability disqualification, but for a program already excluded from the
16 on other grounds.) `classicNoisedeck/fractal`'s three internal unproved
loops (`julia`/`mandelbrot`/`newton` sub-functions) are all statically
reachable too: the dispatch between them is a **runtime** branch on a
uniform (fractal-type selector), not a compile-time `#define`, so the
static call graph includes all three regardless of which one a given frame
actually executes — none can be dead-code-eliminated the way `filter/snow`'s
`round()` call was in the prior corrective pass.

### Discriminability — would a wrong trip count change rendered output?

Checked against each loop's actual role in the source, not assumed:

| Program | Loop's role | Wrong trip count changes output? |
|---|---|---|
| `fractal` (julia/mandelbrot/newton) | Escape-time iteration count directly drives coloring | **Yes, strongly** — classic fractal renderer behavior |
| `blurH`/`blurV` | Box-blur kernel width (`radius`) | **Yes** — visible blur radius changes |
| `dither` | Floyd–Steinberg-style error-diffusion neighborhood | **Yes** — visibly different dither pattern |
| `lightLeak` | Voronoi seed count (`POINT_COUNT`) | **Yes** — visibly different cell pattern |
| `statsFinal` | Full-image min/max reduction | **Yes**, and silently-wrong if undershot (missed pixels understate stats, no visible error signal) |
| `oilFlatten` | Oil-paint sample-window radius | **Yes** — same class as blur |
| `parallax` | Ray-march step count | **Yes** at low counts; diminishing/converging at high counts, but the proved range (32) is on the sensitive side |
| `reindexReduce`/`reindexStats` | Per-tile/whole-image stat aggregation feeding a later reindex pass | **Yes** — undershooting silently drops tiles/pixels from the stats, visible downstream |
| `smoothBlend:searchEdge` | Bounded (1..32) edge search with early `return` | Only matters near the search-radius boundary; return already short-circuits most cases |
| `tetraColorArray` | Blends across `count-1` palette-stop transitions | **Yes** — wrong stop count changes the gradient materially |
| `zoomBlur` | Radial zoom-blur sample count (41 fixed samples) | **Yes** — sample count trades off blur smoothness |
| `synth/noise:multires` | Octave count for fractal noise | **Yes** — visibly changes noise detail/character |
| `testPattern:renderNumber` | Digit count for an on-screen numeric readout | **Yes** — truncated/wrong digits shown |

**Verdict: none of the 16 is a discriminability non-issue.** Unlike the
`filter/fxaa`/`round()` case (where `glsl_round`/`std::round` only diverge
for negative inputs and the call site is architecturally always
non-negative, so full-render parity testing structurally cannot exercise
the hazard), every one of these 16 loops has a trip count that measurably
changes rendered pixels. This is a clean result for validation planning —
render-parity tests against these programs will actually exercise the fix
— but it also means there is **no shortcut**: correctness of whatever bound
is chosen (call-site-derived, hard-cap, or otherwise) has to be right, not
just "close enough to pass a parity threshold."

## 7. Recommended slicing and order

Ordered for programs-landed-per-slice, cheapest/lowest-risk first, generator
work before any new architecture, and explicitly **not** promising a
"landed" program where a downstream blocker (struct support, matrix
dispatch) is still required even after loop-proof work — several of the 16
still need one more capability beyond loop-proof to actually ship.

**(a) Fingerprint-only reuse of `source-global-literal-int-v1`** — zero new
proof logic, each is a hand-computed SHA-256 profile entry exactly like the
six that already exist.
- `filter/lightLeak:lightLeak` (`POINT_COUNT=6`)
- `filter/parallax:parallax` (`MARCH_STEPS=32`)
- `filter/reindex:nmReindexStats` (`TILE_SIZE=8`)

  *(+3 programs, no budget changes, no new soundness question — do first.)*

**(b) Cheap, low-risk new shape logic** (mechanical or nearly so, bounded
scope, no operator sign-off needed beyond normal review):
1. **Drop `_contains_return` for otherwise-fully-canonical loops**
   (`filter/smooth:smoothBlend`). The narrowest, safest fix in the entire
   family — a `return` inside a bounded loop can only shorten it.
   *(+1: smoothBlend)*
2. **Widen induction-type check to accept `float` with integer literal
   start/bound and unit step** (`filter/zoomBlur`, and
   `classicNoisedeck/effects`'s copy of the same loop — though `effects`
   still needs the unrelated matrix-constructor gate cleared first to ship).
   *(+1 confirmed landable now: zoomBlur; +1 contingent on matrix-family work: effects)*
3. **Symmetric-window start/bound rule**: `for (int i=-B;i<=B;i++)` where
   `B` is independently proved (needs an upstream trace of whether
   `radius`/`sampleLimit` are themselves clamped before this can land — not
   yet confirmed in this pass, so scope that trace first).
   *(+3 candidates once traced: blurH, blurV, oilFlatten; dither needs this **and** the const-global-with-arithmetic-initializer fix below, so don't count it here yet)*

**(c) Reuse + budget-constant change, needs an explicit safety
justification per §5**:
- `filter/reindex:nmReindexReduce` (`MAX_TILE_DIM=512`, needs
  `lexical_product` cap raised ~64× to ≥262144) — low *real* per-frame risk
  because the loop is single-pixel-gated (`if (fragCoord != (0,0)) return`
  before the loop), but the cap itself is shared/global and a naive raise
  would also let a genuinely per-pixel program claim the same headroom.
  Recommend scoping the cap increase narrowly (e.g. per-loop opt-in
  authenticated profile, not a blanket constant bump) rather than a global
  `4096→262144` change.
- `synth/mandelbrot:mandelbrot` (`MAX_ITER=500`, needs `trip_count` cap
  raised ~4× to ≥500) — genuinely per-pixel cost, comparable in kind to
  `gabor`'s already-recommended change but larger in magnitude; needs
  explicit sign-off.
- `synth/gabor:gabor` (`effective_depth` cap 3→4 only) — see §5, lowest-risk
  of the three pure-budget cases, **lands immediately with no other blocker**.

  *(+1 confirmed immediately landable: gabor. +2 contingent on operator-approved cap changes: reindexReduce, mandelbrot.)*

**(d) Genuinely new, larger proof/ABI logic** (real design+build work, not
admission relaxation):
- **Call-site analysis for parameter/local-bound loops** (a new
  interprocedural proof, or fall back to a runtime hard cap with sign-off):
  `filter/tetraColorArray`, `synth/noise:multires`,
  `classicNoisedeck/fractal`'s `julia` sub-loop (`iterScaled`),
  `synth/testPattern:renderNumber` (also needs the `return`-in-body fix from
  (b), since it has *two* independent shape violations).
  *(+4, real proof-engineering work, not budget-tuning)*
- **Const-composed-of-consts global initializer support** (extends
  `source-global-literal-int-v1` to fold `const+const+const+literal`, not
  just a bare literal), plus the two *other*, differently-shaped unproved
  loops in the same function: `filter/dither`. Does not ship from any one
  fix alone — needs three separate shape problems solved in the same
  program (const-arithmetic reuse extension, and two symmetric-window
  proofs from (b) once traced).
  *(dither is the single hardest-to-fully-clear program in the 16 because it stacks three distinct shape gaps)*
- **Multi-variable/non-declaration initializer** structural widening:
  `classicNoisedeck/fractal`'s `mandelbrot` sub-loop — mechanical shape fix,
  but its bound (`iterations`, a raw uniform) still needs the uniform-bound
  answer below, so this alone doesn't land the loop.
- **Resolution/swizzle-bound loops**: `filter/normalize:statsFinal` — needs
  either a documented max-resolution hard cap or an established
  architectural resolution bound; not resolved in this pass, flagged as
  open.

**(e) Not soundly provable statically — needs a source-level clamp or an
explicit, operator-approved runtime-checked hard cap (behavior change, not
a transparent proof)**:
- `classicNoisedeck/fractal`'s `newton` sub-loop — reads a `uniform`
  directly with no clamp. The codebase's own precedent
  (`filter/reverb:reverb`'s whitelisted `clamp(uniform,1,8)` pattern) is the
  template: either a source fix adding an equivalent clamp (authenticated
  the same bespoke way), or a generator-side hard cap + `break`.
- `filter/median:median` — `while`-loop quickselect over a compile-time
  small fixed array (9/25/49 elements per `RADIUS` `#define`). No generic
  `while` rule can be sound (elsewhere a `while` could be genuinely
  unbounded); this needs its own whole-program combinatorial proof
  (`fixed_nine_table_proof.py`-style precedent — a program-specific
  worst-case comparison-count argument, roughly `REAL_COUNT²` for this
  algorithm), which is real, non-trivial, per-program work, not a shape
  extension that helps anything else in the corpus.

## Bottom line / order of operations

1. **(a) fingerprint-only reuse** — 3 programs, ship first, zero risk.
2. **(b) cheap shape fixes** — return-in-loop (1), float induction (1
   confirmed + 1 contingent on matrix work), symmetric-window (3 candidates
   pending an upstream-clamp trace).
3. **(c) `gabor`'s depth-cap-only fix** — ships immediately, no other
   blocker, low risk; sequence right after (a)/(b).
4. **(c) `reindexReduce`/`mandelbrot` budget increases** — real but bounded
   risk, needs explicit operator approval, recommend scoping narrowly
   (per-program authenticated profile) rather than a blanket global-constant
   raise.
5. **(d) call-site analysis** for parameter/local-bound loops — real new
   proof engineering, no shortcuts; do after the cheap wins to validate the
   approach on a smaller surface first.
6. **`newton`/`julia` budget increases** — hold; no payoff without struct
   support landing in the same slice, so bundle rather than raise
   speculatively.
7. **(e) uniform-bound and `while`-loop cases** — hardest, most consequential
   (real behavior-change or bespoke-combinatorics work); do last, each on
   its own merits, each needing explicit operator sign-off for `newton`'s
   uniform-clamp and its own review for `median`'s combinatorial proof.

## Appendix — files in this directory

- `probe_loop_shapes_detail.py` / `loop-shapes-detail-output.json` — §1/§2/§4/§5
  per-loop structural and proof data (30 sites, 19 keys, all fields).
- `probe_reachability.py` / `reachability-output.json` — §6 reachability data.
- `shape-groups-summary.json` — compact machine-readable version of §2's table.
- `.sha256` sidecars for every file above and for this document.
