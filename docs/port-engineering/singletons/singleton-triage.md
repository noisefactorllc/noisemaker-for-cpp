# Singleton tail triage — 2026-08-13

Read-only triage of the singleton and near-singleton blockers in the C++20
port. Every claim below was produced by running the REAL
`parse_program` / `analyze_program` / `validate_capabilities` /
`render_typed_cpp` in-process, against a byte-identical `cp -R` copy of the
live `tools/glslcpp` tree (verified via `diff -rq tools/glslcpp
docs/port-engineering/singletons/probe_tree/tools/glslcpp`, no output) —
never by reading GLSL and guessing. Downstream chains were traced by
re-running the same real validator against copies of `generate_typed_slice.py`
with a single, targeted, already-known blocker's raise site provisionally
patched to admit-and-continue (never the real `tools/glslcpp`, never
`src/`, `include/`, `tests/`, or `CMakeLists.txt`). Every patch site is
asserted at build time to match exactly one occurrence of the original text.

Corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`, resolved from its
`manifest.json` (212 programs). Live tree at time of writing: 154/212 typed
(confirmed via `tools/glslcpp/typed_slice.json`, matching
`REMAINING-WORK-ROADMAP.md`'s 137 + 15 derivatives + 2 free = 154).

## Scripts (all under this directory)

| Script | Purpose |
|---|---|
| `build_relaxed_all.py` | Builds the 13-patch mega-relaxed `generate_typed_slice_relaxed_all.py` used for most single-hop downstream lookups. |
| `build_relaxed_variants.py` | Builds `..._relaxed_loopproof_only.py` (loop-proof gates ONLY) and `..._relaxed_no_paramdir.py` (everything EXCEPT parameter-direction), used to isolate individual hops. |
| `build_extra_hop_variants.py` | Builds 3 further-hop variants layered on the mega-relax, for distortion (+derivatives), glitch (+matrix constructor/product), and parallax (+textureLod). |
| `probe_singletons.py` | Runs the real (unmodified) validator for the terminal blocker + reachability BFS, and the mega-relax for one downstream hop, over the 7 named targets + other found singletons + the loop-proof cluster. Checkpoints after every program. |
| `scan_out_texturelod.py` | Corpus-wide (all 58 currently-unported programs) scan answering "how many programs does `out`/`inout` really gate, and how many does `textureLod` really gate." Checkpoints after every program. |
| `assemble_triage.py` | Assembles `singleton-triage.json` from the above outputs. |

Every script and result file has a `.sha256` sidecar. `probe_tree/` is the
byte-identical working copy (verified, see above); it is not itself part of
the deliverable narrative but is kept so the relaxed variants can be
re-run or re-diffed.

## Ranked table

| Program | Terminal blocker | Reachable? | Downstream chain | Mechanism | Cost |
|---|---|---|---|---|---|
| `synth/bitwise:bitwise` | `unsupported binary operator ^` (34:27, in `bitOp`) | Yes | None found (mega-relax unchanged) | New scalar-uint XOR admission (existing `uint-vector-bitwise` only covers uvecN). Zero shift operators present (re-confirmed). | **Cheap** |
| `classicNoisedeck/caustic:caustic` | `exact Caustic word hash profile carrier required` (structural, not a construct) | **No — dead code, 3rd independent confirmation** | n/a (dead) | Profile-carrier already implemented; needs slice-row wiring only | **Cheap** |
| `filter/lighting:lighting` | `unsupported builtin reflect` (93:26, `applyReflection`) | Yes | `unsupported typed type float[9]` (40:11, local Sobel-X kernel in `calculateNormal`) — but this REUSES the exact mechanism already shipped for `filter/sobel:sobel` | (1) reflect node-identity admission; (2) new fixed-nine profile entry, reusing existing, already-shipped machinery | **Cheap-ish** |
| `classicNoisedeck/glitch:glitch` | `unsupported typed type mat4` (76:10, `bicubic`) | Yes | mat4 type → mat4 constructor → mat4 product, then VALIDATOR PASSES clean (3 hops, all one mechanism family); emitter independently needs the same widening | Matrix-cluster Slice C: widen existing mat3-style admission to mat4 in validator + emitter, preserve double-accumulation narrowing | **Moderate** |
| `filter/watercolor:wcSimplify` | `unsupported parameter direction inout` (10:12, `sort2`) | Yes | VALIDATOR passes once `inout` admitted, but the **separate emitter** then fails on `only typed assignments are admitted` (37:5) — a previously undocumented gap: the emitter has no lowering for a bare void-call statement at all, needed 19× for the Devillard opt_med9 network | (1) inout admission, validator+emitter; (2) NEW emitter capability: void-call-as-statement lowering | **Moderate** |
| `synth/remap:remap` | `unsupported uniform block` (5:1) | n/a (global scope; consumed by main's per-pixel zone walk, i.e. live) | `unsupported typed type vec4[267]` (6:5) — a 267-entry uniform array read with runtime-computed (not compile-time-literal) indices | (1) uniform-block admission; (2) a genuinely NEW general dynamically-indexed uniform-array runtime capability — no existing bounded-table mechanism fits | **Expensive** (most architecturally novel of the 7, but stays in the typed-kernel path) |
| `mixer/distortion:distortion` | `unsupported sampler parameter` (91:33, `applyDisplacement`) | Yes | 4+ confirmed hops: sampler-param → sampler-expression → dFdx (16th derivative-admission program) → **NEW** float[9] kernel (31:11, distinct from lighting's/sobel's) → reflect (per census, not independently re-verified past hop 4) | At least 4 previously-separate capability families stacked | **Most expensive of the 7** — corrects the roadmap's "2 known downstream blockers" framing; direct re-probe finds more |

Multi-program adjacent blockers, corpus-wide (all 58 currently-unported
programs scanned):

| Blocker | Gates | Programs |
|---|---:|---|
| `out`/`inout` parameter direction | **3** | `filter/lightLeak:lightLeak` (out, 2nd blocker behind loop-proof), `filter/watercolor:wcSimplify` (inout, terminal), `synth/mandelbrot:mandelbrot` (out, in df64 double-float-emulation helpers; a 3rd blocker, `unsupported builtin log`, sits behind it) |
| `textureLod` | **1** | `filter/parallax:parallax` (2nd and **confirmed final** blocker behind loop-proof — validator fully passes once both are admitted) |

## Other one-off / near-one-off clusters found (not in the operator's named 7)

Enumerated directly from `frontier-census.json`'s `cluster_counts` (every
cluster with ≤ 2 members), cross-checked against the live tree:

- **`filter/grime:grime`** — terminal of a 4-program cluster ("Varying
  admission (v_texCoord): 1 terminal + 3 downstream"). `filter/spookyTicker`,
  `filter/texture`, `filter/wobble` each independently need the same vec2
  varying admission as their own *second* blocker. grime's own second
  blocker (`floatBitsToUint` at 38:25) still needs its own node-identity
  authorization.
- **`synth/shape:shape`** — genuinely unique cluster (mutable global scratch
  float). Two real gaps: admit the mutable global, then a separate
  `write to source const global` guard fires at 459:5. Not deeply costed
  here (outside the named 7); flagged for future triage.
- **`classicNoisedeck/shapeMixer:shapeMixer`** — shares the mat3 `fwdA`
  declaration with the matrix-dispatch cluster, but its own downstream
  blocker is **`refract`, not `reflect`** as `REMAINING-WORK-ROADMAP.md`'s
  matrix-census paragraph states. Direct re-probe on the live tree: `refract`
  at 675:17, inside `blend()`, confirmed reachable (both `blend` and
  `linear_srgb_from_oklab`, the fwdA/invA consumer, are in the
  main()-reachable function set). **This is a correction to the roadmap
  document.** Chain not walked past refract.
- **`classicNoisedeck/moodscape:moodscape`** — matrix cluster's known dead
  exclusion, re-verified **one level deeper**: not only is `fwdA` itself
  unreachable, the second blocker behind it (`unsupported typed expression
  index` at 137:13, inside `rgb2hsv`) is *also* dead — `rgb2hsv` is absent
  from the main()-reachable set (only `hsv2rgb`, the reverse conversion, is
  reachable). Note: GLSL `#if`-driven line renumbering during preprocessing
  makes direct line/column cross-referencing against the raw corpus source
  unreliable for this program — this finding rests on the AST's own
  reachability data, not on reading source at that line.
- **`filter/waves:waves`** (`any` admission cluster) — refinement to the
  roadmap: `any` admission alone is **not sufficient**. Once admitted, waves
  hits a second blocker, `unsupported typed type bvec2` (41:13, the
  `notEqual(...)` intermediate), which today is admitted only for one
  unrelated authenticated node elsewhere.
- **`filter/posterize:posterize`** (`round` admission cluster) — unaffected
  by this pass (round deliberately not relaxed); already thoroughly
  characterized by `REMAINING-WORK-ROADMAP.md`'s Math.round-semantics
  finding, not re-derived here.
- **`filter/invert:inv`, `synth/solid:solid`** — confirmed free (VALIDATOR
  PASS with zero relaxation).
- **`filter/wormhole:deposit`** — confirmed **already resolved**, outside
  the typed-kernel path entirely. `include/noisemaker/effects/scatter/
  wormhole.hpp` and `tests/test_scatter_wormhole.cpp` both exist in the live
  tree. Not part of the open singleton tail any more.

## A correction to the loop-proof cluster's current state

Two of the census's 20 remaining loop-proof-cluster programs do **not**
actually terminate on the loop-proof gate on the current live tree — verified
directly against the real top-level `tools/glslcpp` (not the probe copy):

- `filter/oilPaint:oilFlatten` → real terminal blocker is `unsupported
  builtin ceil` (19:27), never reaching the loop.
- `filter/smooth:smoothBlend` → real terminal blocker is `unsupported global
  declaration` (17:1), never reaching the loop.

Since the loop-proof audit runs *before* the global-declaration checks in
`validate_capabilities`'s fixed order, this means both programs' loops now
pass the loop-proof audit cleanly on the live tree — unlike
`frontier-census.json`, which (dated 2026-08-12, frozen snapshot
`20260812T225121Z`) records both as loop-proof rejections. The most likely
explanation: `loop_proof.py`'s ACCEPTED set was widened on 2026-08-13 for the
`zoomBlur`/`nmReindexStats` landing (see `REMAINING-WORK-ROADMAP.md`'s "Float
induction was widened deliberately" section), incidentally letting other
programs' loops through too. **`frontier-census.json` is stale for at least
these two programs and should be re-run before being treated as fully
authoritative for the loop-proof cluster again.**

Also newly found in this pass: `ceil` and `log` have **zero** admission path
anywhere in the generator (not in `APPROVED_CAPABILITIES`, no runtime
primitive for `ceil`; `log` has no `glsl::log` in `glsl_runtime.hpp` despite
the transcendentals doc already carrying accuracy figures for it). `ceil`
gates `oilFlatten` and (as a 2nd-hop blocker) `smoothBlend`; `log` gates
`mandelbrot` as a 3rd-hop blocker behind `out`.

## Could not determine

- **`mixer/distortion:distortion`**'s full chain past hop 4 (the float[9]
  kernel at 31:11). The census's own earlier probe records `reflect` as a
  further downstream blocker, but this pass did not independently re-verify
  it as final — could not determine whether a 6th blocker exists.
- **`classicNoisedeck/shapeMixer:shapeMixer`**'s chain past `refract`
  (675:17) — not walked further. Could not determine whether the
  "matrix indexing" gate that blocks 6 other matrix-cluster programs also
  applies to shapeMixer once refract is handled.
- **`synth/shape:shape`**'s exact cost was not deeply estimated (only the
  2-hop chain was confirmed); it sits outside the operator's named 7 and was
  not prioritized for a full mechanism-cost writeup here.
- Whether `synth/remap:remap`'s needed "dynamically-indexed uniform array"
  capability could instead be satisfied by a bounded, staticaly-provable
  variant (à la the existing fixed-nine/fixed-grid proofs) rather than a
  fully general runtime primitive — this would require reading `remap`'s
  full zone-walk loop structure in `main()` in detail, which was not done
  here. Flagged as a design question for whoever scopes the work, not
  answered.
- The exact identity of the AST node at `classicNoisedeck/moodscape:
  moodscape:137:13` in terms of raw source text — preprocessing-driven line
  renumbering made this unverifiable by direct inspection; the reachability
  conclusion (dead) does not depend on it and stands independently.

## What is genuinely cheap vs. needs real architecture

**Cheap** (single new admission, or already-dead): `synth/bitwise:bitwise`,
`classicNoisedeck/caustic:caustic`.

**Cheap-ish** (one new admission + one reuse of existing, already-shipped
machinery): `filter/lighting:lighting`.

**Moderate** (multiple admissions, all within one mechanism family, or one
genuinely new but narrow emitter capability): `classicNoisedeck/glitch:glitch`
(matrix widening, matches the roadmap's existing plan), `filter/watercolor:
wcSimplify` (inout + a new but narrow "call as statement" emitter capability).

**Expensive** (a genuinely new, general runtime capability with no bounded
existing mechanism to reuse): `synth/remap:remap` (dynamically-indexed
uniform array).

**Most expensive / union of several other clusters**: `mixer/distortion:
distortion` (sampler-parameter + sampler-expression + a 16th
derivative-admission grant + its own float[9] table + reflect).

None of the 7 named targets needs a whole new pass architecture the way
`wormhole:deposit` did — all stay inside the typed per-pixel kernel path
(`filter/wormhole:deposit` itself is excluded from this list: it is already
resolved via the scatter-pass adapter, outside the typed generator).
