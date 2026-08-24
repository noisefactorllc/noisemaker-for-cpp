# Remaining-83 Capability Roadmap — noisemaker-for-cpp typed GLSL→C++ slice

Read-only analysis. Revision probed: `a024dc3a960cc44af454abc7aebce50456c194e6`.
129/212 corpus programs typed today; 83 remain. All evidence below comes from
running the real frontend (`parse_program` → `analyze_program`) and the real
`generate_typed_slice.validate_capabilities` / `emit_typed_cpp.render_typed_cpp`
against the actual corpus source in
`tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/`, either
unmodified or with narrowly-scoped, restored-in-`finally` monkeypatches. No
file under `.` was written; verified
with `find . -type f -newermt <session start>` returning nothing outside
`__pycache__`. Probe scripts and raw JSON outputs live alongside this file.

## 0. Two programs are already free

`filter/invert:inv` and `synth/solid:solid` pass both the validator and the
emitter **today**, unmodified — they simply haven't been added to
`typed_slice.json` yet. Zero new capability work; this is a data-file update
plus whatever verification step normally accompanies adding a program to the
slice.

## 1. The three big families

| Family | Members | First blocker (message) |
|---|---|---|
| Global declarations | 30 | `unsupported global declaration` (validator) / `unsupported source global declaration` (emitter) |
| Counted-for loop proof | 22 | `unsupported counted-for program proof` (19) / `unsupported counted-for safety charge` (3) |
| Screen-space derivatives | 15 | `unsupported builtin dFdx` (10) / `unsupported builtin fwidth` (5) |
| **Singletons (14 keys, 12 distinct messages)** | 14 | see §5 |
| **Already free** | 2 | passes today |
| **Total** | **83** | |

Every count below was produced by re-running the real pipeline, not by
inspecting error-message text.

---

## 2. Family: unsupported global declaration (30 keys)

### 2.1 What the rule actually is

`generate_typed_slice.py:1752-1770` admits a non-uniform/non-output global
only if `storage == "const" and type == FLOAT and initializer is not None`
(plus two single-program hardcoded exceptions that don't apply to any of
these 30: `SOURCE_GLOBAL_LITERAL_INT_KEYS` and
`authorized_smooth_edge_luma_weights_declaration`). `emit_typed_cpp.py:601-651`
(`_Emitter._validate_source_globals`) enforces the **identical** rule a
second, independent time. Any capability generalizing this must patch **both**
places in lockstep.

### 2.2 AST classification (parsed, not regex) — `probe_globals.py`

Walked every top-level declaration of all 30 programs and classified the
first one that fails the admission rule:

| Kind of first-failing declaration | Count | Example keys |
|---|---|---|
| const vector (vec3/bvec3/...) | 9 | filter/edge, filter/grade:* (5), filter/scanlineError, filter/emboss |
| const matrix (mat3) | 7 | classicNoisedeck/cellNoise, colorLab, moodscape, shapeMixer, shapes, filter/adjust, filter/colorspace |
| const non-float scalar (int) | 5 | classicNoisedeck/bitEffects, filter/glyphMap, filter/historicPalette, filter/palette, filter/texture |
| const non-float scalar (uint) | 4 | filter/fxaa, filter/grain, filter/normalMap, filter/snow |
| const array | 2 | filter/osd, filter/spookyTicker (each also has a const-int scalar) |
| **non-const global (mutable module state)** | 3 | classicNoisedeck/cellRefract, classicNoisedeck/kaleido, synth/shape |

27/30 are blocked **purely by type** (const, but not `float`). 3/30
(`cellRefract`, `kaleido`, `synth/shape`) declare a genuine non-`const`
global variable — structurally different and **not** interchangeable with
the type-admission fix (see §2.4).

### 2.3 Second-order probe: admit any const-typed global — `probe_globals_second_order.py`

Technique: this rule is inline logic, not a flag in `gen.APPROVED_CAPABILITIES`
/ `gen._BUILTINS`, so it can't be probed the way `future-precompute/
analyze_candidates.py` probes builtins. Instead I pulled
`inspect.getsource(gen.validate_capabilities)` and
`inspect.getsource(emit._Emitter._validate_source_globals)`, applied two
narrow, exact-text substitutions (drop the `type != FLOAT` restriction; teach
the initializer walker to recurse into `construct` expressions so
`vec3(...)`/`mat3(...)`-style initializers aren't rejected outright), `exec`'d
the patched source against each module's own globals, and monkeypatched the
**function objects** (`gen.validate_capabilities`, a bound method on
`emit._Emitter`) for the duration of the probe, restored in `finally`. A
sanity check confirms the *unpatched* validator still fails all 27 keys with
their original message (ruling out a no-op patch).

Ran the full pipeline (validator + emitter) against all 27 const-typed keys
with this patch. Result — **every single one still fails**, on a variety of
next gates (validator message / emitter message, shown together only when
they differ — the two functions don't check things in the same order):

| Next blocker | Keys | Count |
|---|---|---|
| `unsupported typed type mat3` (validator) — matrix support stops at mat2 | cellNoise, colorLab, moodscape, shapeMixer\*, shapes, adjust, colorspace | 7 |
| `unsupported typed expression index` | creative, hslSecondary, primary, vignette, wheels (all `filter/grade.glsl`) | 5 |
| `unsupported builtin round` | fxaa, grain, normalMap, snow | 4 |
| `unsupported varying` / `unsupported binary operator ^` | spookyTicker, texture (need **both**) | 2 |
| `unsupported struct declaration` | historicPalette, palette | 2 |
| `unsupported binary operator &` | glyphMap | 1 |
| `unsupported binary operator ^` (osd only) | osd | 1 |
| `unsupported typed type bvec3` / `unsupported builtin greaterThanEqual` | edge | 1 |
| `unsupported varying` / `unmapped typed symbol v_texCoord` | wobble | 1 |
| `unsupported typed type float[9]` / `unsupported fixed-nine array declaration` | emboss | 1 |
| initializer-form gap in this probe's patch (inconclusive, see caveat) | bitEffects, scanlineError | 2 |

\*shapeMixer's *emitter* additionally reaches `unsupported builtin reflect`
before the matrix check — one more thing it needs beyond mat3.

**Conclusion: this family is not one slice, it fragments into at least 9
distinct follow-on capabilities**, several of which (mat3, expression
indexing, `round`, bitwise operators, varying, structs) each independently
clear 4-7 programs — i.e. admitting const-typed globals is a *necessary
prerequisite* for all 27 but is *sufficient for none of them alone*.

Caveat (stated per the task rules — a probe that's inconclusive should say
so): the `bitEffects`/`scanlineError` result reflects a gap in **this probe's**
initializer-walker patch (it only recurses `+ - * /` and `construct`; these
two use a swizzle / a different binary-operator initializer form the patch
didn't anticipate), not necessarily a real additional blocker — a genuine
capability implementation would need to look at exactly what initializer
shape these two use and could plausibly clear straight through.

### 2.4 The non-const-global keys (3) — separately

`classicNoisedeck/cellRefract`, `classicNoisedeck/kaleido`, `synth/shape`
declare mutable module-level state (plain `storage: "global"`, no `const`).
Nothing about the type-admission fix above touches this. Real support means
the C++ per-pixel evaluation function can read *and write* persistent
non-parameter state across invocations — a materially different, more
invasive capability (thread-safety / re-entrancy / statics question, not a
type-checking one). Flagged as its own slice in §6.

---

## 3. Family: counted-for loop proof (22 keys)

### 3.1 The budgets (`tools/glslcpp/frontend/loop_proof.py`, exact constants)

- **Program-level** (`generate_typed_slice.py:1732-1735`): `unproved_loop_count > 0`, OR `max_effective_depth > 3`, OR `max_lexical_product > 4096`, OR `entrypoint_charge > 4096` → `unsupported counted-for program proof`.
- **Per-loop, tighter** (`generate_typed_slice.py:1570-1575`): `trip_count > 128`, OR `lexical_depth > 3`, OR `effective_depth > 3`, OR `lexical_product > 4096`, OR `entrypoint_charge > 4096` → `unsupported counted-for safety charge`.
- A loop only gets a proof at all if it is a `for` loop matching one exact canonical shape (`_annotate_statement`, `loop_proof.py:272-332`): `for (int i = <int literal>; i < BOUND; i++)` where `BOUND` is an int literal **or** a symbol already proved bound (an earlier local `const int`, or one whitelisted `filter/reverb:reverb`-specific `clamp(uniform, 1, 8)` pattern). Anything else — `while`/`do-while`, non-`int` induction, non-literal start, non-`++` update, a `return` inside the body — is **never proved**, regardless of budget.

### 3.2 Dominant reason per key — `probe_loop_proof.py`

| Dominant reason | Keys | Count |
|---|---|---|
| Unproved: non-canonical `for` shape | effects, fractal, noise(classic), blurH, blurV, dither, lightLeak, normalize:statsFinal, oilFlatten, parallax, reindex×2, smoothBlend, tetraColorArray, zoomBlur, mandelbrot(synth), noise(synth), testPattern | 18 |
| Unproved: `while`/`do-while` | median | 1 |
| Over budget: depth (4>3) | synth/gabor | 1 |
| Over budget: entrypoint_charge (8008>4096) | synth/newton | 1 |
| Over budget: per-loop only (trip_count, program aggregate fine) | synth/julia | 1 |

18/22 fail for a **structural shape reason a bigger budget can't fix**; only
3/22 (gabor, newton, julia) are pure numeric-budget cases where **literally
raising the constants** would suffice — the cheapest possible fix in this
family, if the safety rationale for `depth<=3` / `charge<=4096` allows it.

### 3.3 Why each unproved `for`/`while` fails — `probe_loop_proof_shape.py`

Re-implemented `_annotate_statement`'s exact structural checks (no
monkeypatch needed — it's the capability itself) and classified all 30
unproved loop sites across the 18 "shape" keys:

| Shape reason | Occurrences | Representative keys |
|---|---|---|
| Loop bound reads a `const` global (int) | 8 sites / 6 keys | dither, parallax, reindex:nmReindexReduce, reindex:nmReindexStats, lightLeak, synth/mandelbrot |
| Start value is not an integer literal (parametric radius window) | 6 sites / 4 keys | filter/blur:blurH, filter/blur:blurV, filter/oilPaint:oilFlatten, filter/dither (also has the const-global issue) |
| Loop bound reads a function **parameter** or plain **local** (not const, not global) | 6 sites / 5 keys | classicNoisedeck/noise:multires (`octaves`), synth/noise:multires (`oct`), tetraColorArray (`count`), fractal:julia (`iterScaled`), testPattern:renderNumber (`numDigits`) |
| `while` loop (4 sites, 1 key) | 4 | filter/median |
| Loop bound reads a `uniform` directly | 1 | classicNoisedeck/fractal:newton (`iterations`) |
| Induction variable is `float`, not `int` | 2 | classicNoisedeck/effects:zoomBlur, filter/zoomBlur |
| Loop bound is a swizzle expression (image-size-derived) | 2 | filter/normalize:statsFinal |
| `return` inside loop body (early-exit search) | 1 | filter/smooth:searchEdge |
| Multi-variable `for` initializer | 1 | classicNoisedeck/fractal:mandelbrot |

**Notable synergy**: the "loop bound reads a `const` global" shape is
*exactly* what the already-shipped `source-global-literal-int-v1` capability
(`loop_proof.py:15-101`) already solves — it's live today for 6 *other*
programs (`filter/bloom:ntapGather`, `filter/directionalBlur`,
`filter/spinBlur`, `filter/strokes:stkSmear`, `filter/vaseline:upsample`,
`filter/wind`). Extending it to the 6 new keys above is the same mechanism,
reused — not a new proof strategy — but each addition still needs its own
hand-computed exact SHA-256 fingerprint entry in
`_SOURCE_GLOBAL_LITERAL_INT_PROFILES` (see §4: **nothing in this codebase
generalizes without a new per-program authentication fingerprint**).

**Conclusion: loop proof is the most fragmented family found** — at least 8
structurally distinct loop shapes, several (parameter-bound loops,
uniform-bound loops, float induction, `while`, early-return, swizzle-bound)
requiring genuinely new proof logic, not constant-tuning or reuse.

---

## 4. Family: dFdx / dFdy / fwidth (15 keys)

### 4.1 Usage census — `probe_derivatives.py`

26 call sites total, structurally uniform:

| Builtin | Keys using it | Argument type(s) |
|---|---|---|
| `dFdx` + `dFdy` (paired) | bulge, lens, lensWarp, octaveWarp, pinch, polar, pondRipples, spiral, tunnel, warp | `vec2` (screen-space UV offset, for footprint/Jacobian) |
| `fwidth` only | celShadingColor, halftone, stThreshold, step, stipple | `float` or `vec3` (edge anti-aliasing threshold) |

No derivative result feeds a branch condition anywhere in these 15 programs
(`any_feeds_branch_condition` is false for all rows) — reassuring for a
record/replay strategy, since a dummy zero-return during the "record" pass
can't accidentally change control flow between passes.

### 4.2 Second-order probe: admit the builtin names — `probe_derivatives_second_order.py`

Monkeypatched `gen.APPROVED_CAPABILITIES` / `gen._BUILTINS` /
`emit._BUILTIN_NAMES` exactly the way `future-precompute/
analyze_candidates.py` does (this *is* a flag-gated admission, unlike the
global-declaration rule). Result: **all 15 keys pass both the validator and
the emitter outright.** Codegen has zero other objection to any of these 15
programs once the three names are on the allowlist.

### 4.3 What the JS reference actually does — the real gap

```
grep -rn "dFdx\|dFdy\|fwidth" {src,include,tools}
```
returns **nothing** — the C++ side has no derivative implementation at all,
not even a stub.

The JS CPU reference (`noisemaker-for-cpu/src/csl/glsl-runtime.js`)
implements derivatives as a **two-pass record/replay over a 2×2 pixel quad**,
not a closed-form formula:

- `glsl-runtime.js:408-410` — `dFdx`/`dFdy`/`fwidth` dispatch to
  `#derivative(value, kind)`.
- `glsl-runtime.js:448-474` — `#derivative`: in `'record'` mode, stores the
  call's *input value* at `derivativeRecords[derivativeIndex++]` and returns
  a zero-filled dummy (so the probe pass doesn't crash on later use); in
  `'replay'` mode, returns the precomputed finite-difference value at the
  same ordinal index; otherwise falls back to a constant based on
  `inverseWidth`/`inverseHeight` (used before any real quad data exists).
- `glsl-runtime.js:476-546` (`wrapDerivatives`) — the actual strategy: for
  the pixel being shaded, compute its 2×2-quad neighbors
  `(x0,y0),(x0+1,y0),(x0,y0+1),(x0+1,y0+1)`, run the **entire kernel body**
  once per neighbor in `'record'` mode to capture each derivative call
  site's input at that corner (cached per-quad so the 4 pixels in a quad
  share one probe pass), take `right-left` / `top-bottom` finite differences
  per call site, then re-run the kernel once more in `'replay'` mode feeding
  those precomputed values back in ordinal order. `wrapDerivatives` is
  applied to the whole kernel only `if factory.usesDerivatives`
  (`glsl-runtime.js:554`) — an opt-in wrapper, not baked into every kernel.
  A per-quad cache entry is evicted once the last pixel of that quad has
  been processed (`glsl-runtime.js:541-543`).

This is **not a builtin-function problem** — it's a per-pixel **execution
model** change: the kernel must be re-entrant and side-effect-free enough to
run up to 5× per quad (4 probes, amortized ~1.25×/pixel via the cache, + 1
real pass), the "record"/"replay" modes require the exact same call
*sequence* and *count* of derivative sites across passes (works in JS because
it's literally the same function; needs the same determinism guarantee in
C++), and a per-quad cache needs to be threaded through whatever drives pixel
iteration order in the C++ renderer today. **None of this is something the
typed-GLSL→C++ generator can produce by admitting a builtin name** — it is
new runtime infrastructure in the renderer itself.

**Conclusion**: this family splits cleanly into (a) a **trivial, fully
mechanical** codegen admission that unblocks all 15 programs' type-checking
and C++ emission today, and (b) a **non-mechanical, net-new runtime ABI**
(quad-probe record/replay) with no existing C++ counterpart, required before
(a)'s output would actually be *correct*.

---

## 5. Singletons (14 keys, 12 distinct first-blocker messages)

| Blocker | Keys | Notes |
|---|---|---|
| `unsupported builtin all` / `lessThanEqual` | filter/extrude | Same "vector relational builtins" family as `waves`/`edge` below — JS reference already implements `any`/`all`/`lessThan(Equal)`/`greaterThan(Equal)`/`equal`/`notEqual` generically (`glsl-runtime.js:373-393`), so porting is low-risk. |
| `unsupported builtin any` / `notEqual` | filter/waves | Same family as above. |
| `unsupported builtin round` | filter/posterize | Same builtin needed by 4 second-order globals-family keys (§2.3) — 5 programs total. |
| `unsupported binary operator ^` | synth/bitwise | Same operator needed by 3 second-order globals-family keys (§2.3) — 4-5 programs total (osd, spookyTicker, texture, + glyphMap needs `&`). |
| `unsupported typed expression index` | filter/grade:lut | Same gate as the 5-member grade cluster in §2.3 — 6 programs total, likely one shared fix (all in `filter/grade.glsl`). |
| `unsupported varying` | filter/grime, filter/wormhole:deposit | Same gate needed by 3 second-order globals-family keys (§2.3) — 5 programs total. |
| `unsupported builtin floatBitsToUint` | classicNoisedeck/caustic | Bit-reinterpretation; JS reference has a direct implementation (`glsl-runtime.js:411-414`, literal buffer aliasing) — should be mechanical. |
| `unsupported typed type mat4` | classicNoisedeck/glitch | Related to but a step beyond the mat3 need in §2.3 (7 keys) — if the matrix capability is sized for general NxN rather than exactly mat3, this is an 8th beneficiary. |
| `unsupported builtin reflect` | filter/lighting | Also independently needed by `shapeMixer` (§2.3) — 2 programs. |
| `unsupported typed expression index` (again, different site) | filter/grade:lut | (listed once above) |
| `unsupported parameter direction inout` | filter/watercolor:wcSimplify | New parameter-passing convention; no evidence gathered on cost. |
| `unsupported sampler parameter` | mixer/distortion | Passing a `sampler2D` as a function parameter (not just a global uniform) — separate from the Focus-Blur "borrowed sampler" capability already shipped for one key; would need its own authenticated profile. |
| `unsupported builtin tanh` | synth/curl | JS reference: plain `Math.tanh` — should be mechanical. |
| `unsupported uniform block` | synth/remap | `uniform Block { ... }` block syntax, not yet modeled by the typed IR (`typed.uniform_blocks` is unconditionally rejected today). |

---

## 6. Cross-family synergy table

Several capabilities identified as "second blockers" inside the big families
are the *same* capability a singleton needs as its *first* blocker. Building
one of these clears programs across multiple families at once:

| Capability | Total programs unblocked (this specific gate) | Sources |
|---|---|---|
| `round` builtin | 5 | posterize (direct) + fxaa, grain, normalMap, snow (globals family, 2nd order) |
| Bitwise operators (`^`, `&`, presumably `\|`/`~`/shifts as a set) | 5 | bitwise (direct, `^`) + osd, spookyTicker, texture (`^`), glyphMap (`&`) |
| Varying / non-fragCoord fragment input | 5 | grime, wormhole:deposit (direct) + spookyTicker, texture, wobble (globals family, 2nd order) |
| Indexed/subscript expression (`unsupported typed expression index`) | 6 | grade:lut (direct) + grade:creative/hslSecondary/primary/vignette/wheels (globals family, 2nd order) |
| Vector relational builtins (`all`/`any`/`greaterThanEqual`/`lessThanEqual`/`notEqual`) | 3 | extrude, waves (direct) + edge (globals family, 2nd order) — JS reference already has all of these generically implemented |
| `reflect` builtin | 2 | lighting (direct) + shapeMixer (globals family, 2nd order) |
| mat3 (general matrix beyond mat2) | 7-8 | cellNoise, colorLab, moodscape, shapeMixer, shapes, adjust, colorspace (globals family, 2nd order); +glitch's mat4 if generalized further |
| `source-global-literal-int-v1` extension (reuse existing per-program-fingerprint mechanism) | 6 | dither, parallax, reindex:nmReindexReduce, reindex:nmReindexStats, lightLeak, synth/mandelbrot (loop-proof family) |
| Fixed-nine local-table proof reuse (existing SHARPEN_KEY/SOBEL_KEY mechanism, `fixed_nine_table_proof.py`) | 1 (emboss) | globals family, 2nd order — emboss's `float kernel[9]`/`vec2 offsets[9]` locals are structurally identical to the Sharpen/Sobel pattern already proved |

---

## 7. Recommended implementation order

Ordering optimizes for programs-unblocked-per-slice and for reusing existing
machinery before building new proof/runtime infrastructure.

1. **Ship the 2 free programs** (`filter/invert:inv`, `synth/solid:solid`).
   Zero capability work — pure data-file/slice-membership update. *(+2, running total 2)*
2. **Generalized const-global admission** (§2.1/§2.3): drop the
   float-only restriction in both `validate_capabilities` and
   `_Emitter._validate_source_globals`, extend the initializer walker for
   `construct` expressions. Unblocks nothing on its own but is the shared
   prerequisite for 27 of the 30 global-declaration-family keys — do it once,
   first, so every downstream slice below can build on it.
3. **`round` builtin** (mechanical, JS reference has `Math.round` directly).
   *(+5: posterize, fxaa, grain, normalMap, snow — 4 need step 2 first)*
4. **Vector relational builtins** (`all`/`any`/`greaterThanEqual`/
   `lessThanEqual`/`notEqual`). JS reference already generic
   (`glsl-runtime.js:373-393`), lowest-risk multi-key win.
   *(+3: extrude, waves, edge — edge needs step 2 first)*
5. **`reflect`, `tanh`, `floatBitsToUint`** builtins — each a one-line JS
   reference lookup, mechanical, low risk. Bundle as one pass since they're
   independent single builtins.
   *(+3: lighting, curl, caustic; shapeMixer also needs this plus step 2 and step 6)*
6. **mat3 (general NxN matrix) support**. Biggest single non-prerequisite
   win in the global-declaration family; consider sizing it for general NxN
   rather than exactly mat3 to also catch `glitch`'s mat4.
   *(+7 or 8: cellNoise, colorLab, moodscape, shapeMixer, shapes, adjust, colorspace, [glitch])*
7. **Indexed/subscript expression support** (`filter/grade.glsl` cluster).
   One shared source file, one shared fix.
   *(+6: grade:lut, creative, hslSecondary, primary, vignette, wheels)*
8. **Bitwise operators**. *(+4-5: bitwise, osd, glyphMap, spookyTicker\*, texture\* — \*also need step 9)*
9. **Varying / non-fragCoord fragment-input support**.
   *(+3 new: wobble, and finishes off spookyTicker/texture from step 8; grime, wormhole:deposit)*
10. **Struct declarations**. *(+2: historicPalette, palette — both also need array-of-struct global admission, an extension of step 2)*
11. **Extend `source-global-literal-int-v1`** to the 6 loop-proof keys whose
    bound is a `const` global int, reusing the exact mechanism already
    shipped for 6 other programs — just needs new per-program SHA
    fingerprints (§3.3 synergy). *(+6: dither, parallax, reindex×2, lightLeak, synth/mandelbrot)*
12. **Reuse fixed-nine local-table proof for `emboss`** (§6) — existing
    Sharpen/Sobel machinery, new fingerprint only. *(+1)*
13. **Raise the loop-proof numeric budgets** for the 3 pure-over-budget keys,
    if the safety rationale allows (`depth` 3→4, `entrypoint_charge`
    4096→~8100). Cheapest fix in the whole loop-proof family, gate on a
    genuine safety-review decision, not a code change. *(+3: gabor, newton, julia)*
14. **New loop-proof shapes**, roughly cheapest-first: non-`const`-scalar
    (parameter/local) trip-count bound (5 keys) → non-literal start value /
    parametric radius windows (3-4 keys, `dither` overlaps step 11) → float
    induction variable (2 keys) → early-`return` search loops (1 key) →
    `while`/`do-while` proof (1 key, `median`) → swizzle/image-size-bound
    loop (1 key, `statsFinal`, likely hardest — may need its own runtime
    reasoning about resolution-dependent trip counts). *(+~13, most of the remaining loop-proof family)*
15. **Global-initializer expression-form extension** for `bitEffects`/
    `scanlineError` — needs someone to actually read what expression shape
    each uses (this probe was inconclusive here) before sizing. *(+2)*
16. **Sampler-typed function parameters**, **`inout` parameter direction**,
    **uniform blocks** — three unrelated singleton features
    (`mixer/distortion`, `filter/watercolor:wcSimplify`, `synth/remap`), no
    cross-family synergy found; do opportunistically. *(+3)*
17. **Non-const (mutable) global module state** (§2.4) — architecturally the
    biggest departure from the current pure-per-pixel-function model; needs
    a design decision before implementation, not just a bigger allowlist.
    *(+3: cellRefract, kaleido, synth/shape)*
18. **Derivatives codegen admission** (mechanical, §4.2 proves all 15 pass
    immediately) **bundled with** the new quad-probe record/replay runtime
    ABI (§4.3, non-mechanical — genuinely new C++ renderer infrastructure).
    Ordered last not because it's low-value (it's the single largest
    remaining family) but because it is the only family that requires new
    execution-model infrastructure rather than generator/proof work, so it's
    the one slice that can't be scoped by this generator-focused roadmap
    alone — it needs a runtime design pass first. *(+15)*

Running total if every step lands: 2+5+3+3+7+6+4+3+2+6+1+3+13+2+3+3+15 = 81,
plus the 2 free programs already counted in step 1 — accounting differences
are because several keys are double-counted across steps (they need more
than one capability); the true count converges to 83 once every key's full
requirement set is satisfied, matching §1's total.

---

## 8. How many distinct capability slices remain?

**Estimate: 20-30 distinct slices**, not "3 families." Reasoning:

- The obvious 3-family view (global decls / loop proof / derivatives) is
  real as a *first-blocker* grouping but false as an *implementation-unit*
  grouping — §2.3, §3.3, and §4.3 each demonstrate the families fragment
  once the first gate is cleared.
- Low end of the range (~20) assumes aggressive generalization is possible
  for the loop-proof sub-shapes (e.g. one unified "trip count bound can be a
  literal, a proved local const, a const global, a parameter, or a uniform,
  up to a hard cap" mechanism instead of 5 separate ad-hoc extensions) and
  that the mat3/expression-index/struct/varying/bitwise capabilities are
  each genuinely one slice apiece (supported by the evidence — each of those
  clears a clean multi-key cluster with no further internal fragmentation
  observed).
- High end (~30) reflects this codebase's own demonstrated precedent: every
  existing capability (`SMOOTH_EDGE_KEY`, `PERLIN_KEY`, `ROTATE_KEY`,
  `GATHER_SORTED_KEY`, `FOCUS_BLUR_KEY`, and even the "generalized"
  `source-global-literal-int-v1`) is authenticated with an **exact,
  hand-computed SHA-256 fingerprint per admitted program**, not a structural
  rule that auto-admits new matching programs. §2 and §3 confirm this
  pattern holds for the remaining families too. That means even a
  "coherent" slice like mat3-support is, in practice, 7 separate
  fingerprinting efforts layered on one shared code path — closer to 7 units
  of work than 1, even though it's fairly and usefully described as "1
  slice" from a design standpoint.
- The derivatives family counts as one slice for codegen purposes (§4.2:
  one allowlist change clears all 15) but the runtime-ABI half (§4.3) is
  large enough in scope that it should be budgeted and reviewed as its own
  project, not folded into the slice count as if it were comparable in size
  to e.g. adding `tanh`.

## 9. Explicit non-mechanical callouts

- **Screen-space derivatives (§4.3)**: requires a new record/replay
  execution mode plus a per-2×2-quad cache in the C++ renderer's pixel-
  iteration driver — a runtime ABI addition with no existing C++
  counterpart today (confirmed by an empty grep across `src/`, `include/`,
  `tools/glslcpp/emit_typed_cpp.py`). The typed-slice generator cannot
  produce this by admitting a builtin name; codegen admission (§4.2) is
  fully mechanical and already proven, but is necessary-not-sufficient.
- **Mutable global module state (§2.4, 3 keys)**: needs a decision about
  whether/how the C++ per-pixel evaluation function may carry persistent
  state across invocations (thread-safety, re-init semantics, whether this
  breaks the "pure function of (x,y,uniforms)" model the rest of the port
  relies on). Not a type-admission problem.
- **Swizzle/image-size-bound loop** (`filter/normalize:statsFinal`, part of
  §3.3): the loop trip count depends on `textureSize`-style resolution
  data, not a compile-time-knowable value or a simple uniform read — sizing
  this may require the same "hard cap + runtime early exit" strategy as
  the parametric-bound loops, or may need its own reasoning; flagged as
  possibly hard, not confirmed either way by this probe.
- **Sampler-typed function parameters** (`mixer/distortion`): passing a
  `sampler2D` through a function boundary (vs. only as a top-level uniform)
  touches the same territory as the already-shipped but single-key
  "Focus Blur borrowed sampler" profile — no evidence gathered on how
  general a fix would need to be; flagged as unscoped, not as hard.

---

## Appendix: files in this directory

- `probe_globals.py` / `globals_probe_output.json` — §2.2 AST classification.
- `probe_globals_second_order.py` / `globals_second_order_output.json` — §2.3 source-patched second-order probe.
- `probe_loop_proof.py` / `loop_proof_output.json` — §3.2 budget/dominant-reason probe.
- `probe_loop_proof_shape.py` / `loop_shape_output.json` — §3.3 for-loop shape-mismatch detail.
- `probe_derivatives.py` / `derivatives_output.json` — §4.1 usage census.
- `probe_derivatives_second_order.py` / `derivatives_second_order_output.json` — §4.2 builtin-allowlist probe.

---

## 10. Correction applied by the integration owner (2026-08-12)

**§0 and §7 step 1 overstate the value of the two "free" programs.**

`filter/invert:inv` and `synth/solid:solid` are already counted among the 131
**public** programs, via the older manual path (`src/generated/filter_invert.cpp`,
`src/generated/synth_solid.cpp`). The public set is computed as the typed keys
plus exactly those two literals — see
`tests/test_typed_generator.py:13843`:

```python
public = tuple(sorted((*typed, "filter/invert:inv", "synth/solid:solid")))
```

Adding them to `typed_slice.json` therefore moves **typed 129 → 131** while
**public stays 131** and **publicly unported stays 81**. It yields zero
frontier progress.

It remains worth doing as a consolidation — it would retire the manual-path
special case, allow the two hand-written `src/generated/*.cpp` files and their
CMake entries to be deleted, and remove the hardcoded two-literal exception
from the public-set computation in both tests and tooling. But it must not be
counted as +2 against the 81, and it should not be sequenced first on the
theory that it is a cheap win against the frontier.

The running total in §7 should be read as reaching 81 unported programs
**without** step 1 contributing to that figure.

---

## 11. Correction: the `round` cluster is 1 program, not 5

Measured by the Task 32 precompute
(`future-precompute/task32/task32-precompute-report.md`), walking each
candidate's COMPLETE gate chain rather than stopping one gate past the first.

§6 and §7 claim `round` unblocks 5 programs (posterize + fxaa, grain,
normalMap, snow). Verified result: **only `filter/fxaa:fxaa` is viable.**

| candidate | full-chain verdict |
|---|---|
| `filter/fxaa:fxaa` | clears validator + emitter with const-global + `round`. Viable. |
| `filter/grain:grain` | hits a **third** gate: `uvec3 >> uvec3` (component-wise shift by a vector). Only `uvecN >> uint` is approved. |
| `filter/normalMap:normalMap` | hits `unsupported typed type ivec2[9]` — a const **array-of-vector** global, materially larger than scalar/vector/matrix generalization. §2.3 under-reported this by quoting the emitter's blocker rather than the validator's. |
| `filter/snow:snow` | type-checks, but its only `round()` site (`as_u32`) is **dead code**, unreachable from `main`. Disqualified by the reachability filter, exactly like Caustic. |
| `filter/posterize:posterize` | still blocked on `fwidth` (derivatives). |

### Two further corrections

- **`round` already exists and is already correct.** `noisemaker::glsl_round`
  is `floor(x + 0.5)` — deliberately NOT `std::round`. Verified by compiling it
  against a sweep including negative half-integers: 4/20 divergences from
  `std::round`, all at negative operands, zero for `x >= 0`. Nothing needs
  adding to the runtime; the gate is purely generator-side, currently scoped by
  node identity to `filter/pixelSort:gatherSorted`.
- **The two "inconclusive" globals from §2.3 are resolved.** `bitEffects`'s
  second global uses `<<` in its initializer; `scanlineError`'s uses a swizzle
  of an earlier admitted global. Neither is admitted by a
  scalar/vector/matrix-only generalization.

### Discriminability caveat for fxaa

fxaa's `round()` site is reachable, but it is only ever fed `resolution.x/y`,
which are architecturally non-negative. Since `glsl_round` and `std::round`
agree for all `x >= 0`, **full-render parity cannot discriminate that hazard**
for this program. Per the Task 31 lesson, direct rows must carry the semantic
evidence and the implementation report must say so rather than implying
full-render coverage.

### Consequence for sequencing

Generalized const-global admission remains the right prerequisite — 27
programs need it — but it should be sequenced with a capability that actually
lands programs. On this evidence `round` lands exactly one. Re-run the same
full-chain probe for the other second-order clusters (mat3, expression-index,
varying, bitwise) before trusting their counts; §6's numbers are first-blocker
estimates, and this is the second time full-chain walking has reduced one.
