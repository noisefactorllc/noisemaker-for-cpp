# Remaining effects: live frontier

**Refreshed 2026-08-22, after the latest live slice landings.** The 2026-08-16
tables below are retained as history; this header is
the current census. Standing rule unchanged: re-run the probe before choosing
work; never carry counts by arithmetic.

## Current state (2026-08-22)

Every figure below was re-derived from the generated artifacts on
2026-08-19, not carried forward: the typed list and absent set from
`tools/glslcpp/typed_slice.json` against the pinned corpus manifest, the
bind count by counting `[[nodiscard]] BoundKernel bind_` in
`include/noisemaker/generated/catalog.hpp`.

| Metric | Value |
| --- | ---: |
| Typed programs | **206** |
| Generated catalog binds | **208** |
| Corpus keys absent from the typed slice | **6** |
| Already ported outside the typed slice | **1** — `filter/wormhole:deposit` |
| Distinct ported/public corpus keys | **207 of 212** |
| Genuinely unported | **5** |
| Typed-list SHA-256 | `8cd74dc103cadab80e96f41b973cd8e388387ce86cc899bd35386383e2a38640` |

The previous 190-row header (`199fbb5e…`, 192 binds, 22 absent, 21 genuinely
unported) is superseded here.

## Census corrections earned by measurement since 2026-08-16 (each re-measured, evidence in the named design)

- **The palette adapters PASS** — `historicPalette` and `palette` are
  portable (side-by-side algorithm quotes + 207,360/207,360 bit-exact
  differential; `struct-parity/struct-design.md` §1). The adapter limbo that
  discounted the struct bucket to 1 program is resolved in the portable
  direction: the bucket is **3**, plus `synth/julia` as a 4th struct family
  behind counted-for.
- **`filter/dither:dither`'s upstream defect no longer reproduces** against
  the pinned snapshot (`errRow` now pre-initialized; `ditherType=7` renders
  deterministically) — portable-in-principle, deep
  (`counted-for-parity/counted-for-design.md`).
- **`fractal`'s "adapter implements a different algorithm" attribution could
  NOT be confirmed** by side-by-side inspection; the operative blocker
  remains the missing canonical factory either way.
- **The counted-for bucket is a ladder, not a wall**: parallax 2 rungs from
  CLEAN at both authorities, lightLeak 3, mandelbrot 4, synth/noise 4;
  classicNoisedeck/noise and testPattern stop on deeper mechanisms; median
  is bespoke-deep (`counted-for-parity/counted-for-design.md`).
- **wobble is PORTED as typed row 189** (wave 1's finale; insertion index
  155 against the live 188-row slice) — varyings never interpolate on the
  CPU path; `v_texCoord` aliases `context.uv` (one mechanism, pure lowering,
  no ABI change; `varying-parity/varying-design.md` + the landed
  `varying_uv_profile.py`, whose record moved from PREPARED into KEYS with
  the row).
- **parallax is PORTED as typed row 190** (insertion index 80, namespace
  `typed_80`) — the counted-for ladder's first landing: the
  `MARCH_STEPS = 32` source-global literal-int seed plus the textureLod
  identity admission (`texture_lod_admission_profile.py`). It landed with
  **structural-only** parity and was **not bit-exact**; the oracle package
  built on 2026-08-19 found it and the emitter was fixed
  (`DEFECTS-FOUND.md` item 6, `counted-for-parity/parallax-acceptance.md`).

## Recommended next

1. **kaleido187 and effects188 oracle packages** — likewise no oracle
   generator and zero native parity tests (`kaleido-acceptance.md` records
   this; `effects-acceptance.md` states the structural boundary but not the
   absence itself). Lower risk than parallax: both acceptance records argue
   the newly-admitted constructs are unreachable at the frozen defines.
2. **`DEFECTS-FOUND.md` item 7 — the cross-lane whole-vector assignment.**
   `synth/gradient` is shipped and divergent: the port matches an unaliased
   mutant on all 120 lanes and disagrees with the authority on 89 of them.
   This is a
   **precondition for landing `synth/mandelbrot`**, which carries the identical
   construct at `mandelbrot.glsl:247-250` and would land wrong against today's
   emitter — parallax's history, repeated.
3. **The binding-sourced pooled-array alias class** (`synth/osc2d`,
   `synth/perlin`) — item 6, measured-but-unresolved.
4. Then the rest of wave 2: lightLeak → **mandelbrot (blocked on item 7)** →
   synth/noise (counted-for ladder) and newton → historicPalette → palette
   (struct bucket).

**parallax190's oracle package is DONE** (2026-08-19), and building it found
that the row was not bit-exact: `DEFECTS-FOUND.md` item 6. The emitter now
models the JavaScript's pooled-array aliasing; see
`counted-for-parity/parallax-acceptance.md`. Note that `typed_slice.cpp` and
`typed_manifest.json` moved with that fix — the table above still holds
because the slice spec, the catalog and the 190-key SHA did not.

The wave-1/wave-2 combined native matrix is **no longer outstanding** — it
was run at the 190-row state on 2026-08-19, first at 268 PASS / 0 FAIL and
then at **271 PASS / 0 FAIL** once parallax's three native parity tests
landed: Debug, Release and ASan+UBSan each green, ctest 1/1, zero warnings,
zero sanitizer diagnostics (no LeakSanitizer claim); x86_64 269/2, both
failures the documented pre-existing arch-NaN fixtures; assembly GO for
`typed_80` on both architectures, re-run after the emitter fix.

---

## Superseded 2026-08-16 census (history; probes below were run against the 185-row slice)

## Two counts, and why they differ

This document uses two different "remaining" figures, and a review found the
second one asserted nowhere and defined nowhere. Definitions, so they can be
pinned:

- **Corpus keys absent from the typed slice** — computable, and the one the
  generator tests assert. `len(corpus) - len(typed_slice)`.
- **Genuinely unported** — the absent set minus programs that are already public
  by another route. Today that is exactly one program, `filter/wormhole:deposit`,
  which ships through the scatter pass rather than the typed slice. So
  *genuinely unported = absent − 1* for as long as that remains the only such
  program, and a new scatter-style program would change the relationship.

Assert the first; derive and state the second. A design that requires a test to
pin "genuinely unported" without defining it cannot be satisfied.

## Current state

| Metric | Current value |
| --- | ---: |
| Canonical corpus programs | 212 |
| Typed programs | **185** |
| Generated catalog rows | **187** (185 unique typed keys; Invert and Solid are dual-registered) |
| Corpus keys absent from the typed slice | **27** |
| Already ported outside the typed slice | **1** — `filter/wormhole:deposit` through the scatter pass |
| Distinct ported/public corpus keys | **186 of 212** |
| Genuinely unported | **26** |
| Typed-list SHA-256 | `75ea3f3987ece02df2738db474aecaf9ec82b6cfa8a3172f245bdb28d16b6d60` |

Two programs landed since the previous refresh. `synth/shape:shape` is row 184
(`mutable-global-frame-shape-v1` plus the reused `scalar-uint-xor-v1`; see
`shape-parity/shape-acceptance.md`). `filter/normalMap:normalMap` is row 185 —
the first program of the **const file-scope array** mechanism
(`const-global-nine-table-v1`) plus a fourth key on the pre-existing
`as-u32-round-admission-v1` carrier; see
`normalmap-parity/normalmap-acceptance.md`.

Shapes needed **four** carriers, not the three its design projected: the reused
`scalar-uint-xor-v1`, plus `linear-srgb-shapes-lane-index-v1`,
`shapes-float-bits-ingress-v1`, and a late `shapes-rvalue-assign-v1` for a
compound assignment used as an rvalue that only the emitter gapped on. See
`shapes-parity/shapes183-design.md` §§11-13 for the three amendments that came
out of building it.

## The genuine remaining 26, by first live blocker

Probed against the live 185-row slice on 2026-08-16. Twenty-seven keys are
absent from the slice; `filter/wormhole:deposit` is already public via the
scatter pass, which is why the genuine figure is 26.

| First blocker | Count | Programs |
| --- | ---: | --- |
| Counted-for program proof | 9 | `classicNoisedeck/fractal:fractal`, `classicNoisedeck/noise:noise`, `filter/dither:dither`, `filter/lightLeak:lightLeak`, `filter/median:median`, `filter/parallax:parallax`, `synth/mandelbrot:mandelbrot`, `synth/noise:noise`, `synth/testPattern:testPattern` |
| Global declaration | 6 | `classicNoisedeck/cellRefract:cellRefract`, `classicNoisedeck/effects:effects`, `filter/historicPalette:historicPalette`, `filter/osd:osd`, `filter/palette:palette`, `filter/spookyTicker:spookyTicker` |
| Varying admission | 4 | `filter/grime:grime`, `filter/texture:texture`, `filter/wobble:wobble`, `filter/wormhole:deposit` (already public) |
| Exact scalar-uint-XOR carrier required | 2 | `classicNoisedeck/bitEffects:bitEffects`, `classicNoisedeck/kaleido:kaleido` |
| Typed expression index | 2 | `classicNoisedeck/colorLab:colorLab`, `classicNoisedeck/moodscape:moodscape` |
| Counted-for safety charge | 1 | `synth/julia:julia` |
| Sampler parameter | 1 | `mixer/distortion:distortion` |
| Struct declaration | 1 | `synth/newton:newton` |
| Uniform block | 1 | `synth/remap:remap` |

`filter/wormhole:deposit` also reports `unsupported varying`, but it is excluded
from the genuine count because the scatter pass already provides its public
behavior.

These are first barriers only. Do not infer that every row in a bucket shares
the same complete implementation.

### Three corrections to the first-blocker census

The normalMap design probe re-ran the bucket with every global admitted, which
is the only way to see past a first barrier. Three of its rows correct the
census above and are recorded here because they change what each bucket is
worth, independently of which program is built next. The design review
reproduced the nine-row probe table 9/9 from the pinned corpus
(`normalmap-parity/normalmap-design.md` §1); the source facts below were
re-confirmed by reading the corpus GLSL directly.

- **`filter/spookyTicker` is a varying program, not a global-declaration
  program.** It is double-blocked: `spookyTicker.glsl:16` is `in vec2
  v_texCoord;`, the same declaration `grime.glsl:19` carries. The **varying
  bucket's real membership is four** — `grime`, `texture`, `wobble`,
  `spookyTicker` — where the count in the first-blocker table above is four only
  because it still includes the already-public `wormhole:deposit`. Admitting
  varyings is worth four real programs, not three.
- **`historicPalette` and `palette` block on struct declaration**, the same
  mechanism `synth/newton` needs: `historicPalette.glsl:23` declares
  `struct HistoricPalette`, `palette.glsl:28` declares `struct PaletteEntry`.
  **That bucket is three programs, not one** — a fact independent of their
  unresolved adapter eligibility, which is discussed below and does not change.
- **`bitEffects` and `osd` both need JS-Number bitwise semantics**, the
  `bitwise-scalar-int-ops-v2` shape built for `synth/bitwise`. Neither is a small
  global-declaration job. `bitEffects.glsl:173` is
  `const int mask = (1 << BIT_COUNT) - 1;` and `<<` is not even in the frozen
  17-entry binary operator vocabulary, so it cannot be admitted by widening the
  const grammar alone; `osd.glsl:73` is `float((row >> (6 - gx)) & 1)` on signed
  ints, which is the JS-Number contract exactly.

### Second blockers behind the scalar-XOR bucket

Independently re-probed 2026-08-15 by supplying `scalar-uint-xor-v1` and
re-running `validate_capabilities`. The census above reproduced exactly; this
table is what it does not show.

| Program | Next blocker with the XOR carrier supplied |
| --- | --- |
| `classicNoisedeck/bitEffects:bitEffects` | `130:1 unsupported global declaration` |
| `classicNoisedeck/kaleido:kaleido` | `33:1 unsupported global declaration` |
| ~~`synth/shape:shape`~~ | ~~`31:1 unsupported global declaration`~~ — **PORTED 2026-08-16 as row 184** |
| ~~`classicNoisedeck/shapes:shapes`~~ | ~~`576:13 unsupported typed expression index`~~ — **PORTED 2026-08-16 as row 183** |

Two consequences worth acting on:

1. **Global declaration is really an 8-program bucket, not 6.** Both remaining
   scalar-XOR rows fall straight into it. That makes it the largest single
   unbuilt mechanism in the remaining 26, level with the 9-row counted-for
   bucket once that bucket's two non-portable programs are removed.
2. **`scalar_uint_xor_profile.py` already carries complete frozen locks for all
   six of its keys** — the two above plus `classicNoisedeck/shapeMixer`,
   `filter/grain`, `classicNoisedeck/shapes` and `synth/shape`, the four wired
   into the slice today. For `bitEffects` and `kaleido` the XOR proof is built
   and paid for; those rows need the carrier wired and then only their
   global-declaration blocker resolved.

The Shapes row is the reason the handoff cites `576:13` as its RED boundary:
**that rejection only appears once the XOR carrier is present.** With no
carriers at all Shapes first-blocks on `exact scalar uint XOR profile carrier
required`. Do not read that as a drift from the design.

## Shapes183 — LANDED 2026-08-16 (row 183)

`classicNoisedeck/shapes:shapes` is ported, at typed ordinal 8 between Shape
Mixer and Splat. Its design projected three carriers; it needed **four**:

```json
{
  "defines": {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30},
  "program_key": "classicNoisedeck/shapes:shapes",
  "scalar_uint_xor_profile": "scalar-uint-xor-v1",
  "linear_srgb_lane_index_profile": "linear-srgb-shapes-lane-index-v1",
  "shapes_float_bits_ingress_profile": "shapes-float-bits-ingress-v1",
  "shapes_rvalue_assign_profile": "shapes-rvalue-assign-v1"
}
```

Gates at acceptance: four generator gates exit 0; full Python 441 tests with the
only failure a copy-path artifact verified passing live; native Debug, Release
and ASan+UBSan each 242 PASS / 0 FAIL with zero sanitizer diagnostics; assembly
clean on ARM64 and x86_64; historical 183 → 182 reconstruction exact.

**Three things it taught, all now amendments in `shapes-parity/shapes183-design.md`:**

- **§11** — the design demanded a bound-`seed` control that is *unsatisfiable*.
  At defines 40/30 `seed` reaches nothing live, and the shader says so at
  `shapes.glsl:12-19`. The axis is now recorded and proven invariant instead,
  which is a real parity assertion: a port that wrongly made `seed` live would
  differ from an invariant oracle.
- **§12** — a fourth closure was needed for `float angle = rot *= PI;`, a
  compound assignment used as an rvalue. `assign` was *already* in the frozen
  44-entry vocabulary; the gap was purely a missing `assign` arm in the
  emitter's expression dispatcher. The lowering was settled by reading the
  shipped JS, which keeps the rvalue form **while four sibling factories fold
  it**.
- **§13** — the assembly gate is clean *conditionally*. `typed_8::value`
  contains a real jump table that only stays out of pixel scope because the
  defines are frozen at 40/30.

If you are porting the two remaining scalar-XOR programs, Shapes is the
worked example to read first: same reused carrier, same shape of secondary
closure, and the amendments show what the design got wrong and how it was
corrected rather than worked around.

## Normalmap185 — LANDED 2026-08-16 (row 185)

`filter/normalMap:normalMap` is ported, at typed ordinal 66 between
`filter/mosaicTiles:mosaicTiles` and `filter/normalize:apply`. It is the first
program of the **const file-scope array** mechanism and the second of the
global-declaration bucket after `synth/shape`:

```json
{
  "as_u32_round_profile": "as-u32-round-admission-v1",
  "const_global_table_profile": "const-global-nine-table-v1",
  "defines": {},
  "program_key": "filter/normalMap:normalMap"
}
```

`normalmap-parity/normalmap-acceptance.md` carries the gates and the claim
boundaries. Three of those boundaries are portable lessons rather than
program-specific facts:

- **Element materialization, not literal-ness, is what makes the emitter's
  per-pixel re-evaluation of an admitted const global sound.** A factory-scope
  `PooledFloat32Array` table is aliased and overwritten by the first per-pixel
  scratch allocation; only the *integer* pool is base-index protected. So the
  mechanism must never be extended to `vec2[N]` / `vec3[N]` / `vec4[N]` const
  globals without re-deriving the pool argument from `glsl-runtime.js`, and the
  closure's element-type check is an allowlist for exactly that reason.
- **Two of the three mutants the design specified were bit-identical**, because
  `SOBEL_X_KERNEL` viewed as 3×3 is exactly the transpose of `SOBEL_Y_KERNEL`. A
  third was structurally unsatisfiable. Design-time mutant proposals need a
  satisfiability and a distinguishability check before they are budgeted.
- **A numeric contract can be unfalsifiable by every pixel of its own program.**
  The two kernel tables are `double` in the JavaScript, but every element is
  exactly representable in binary32, so no parity test can distinguish the
  contracts. The claim is structural, and the acceptance record says so.

## The global-declaration bucket is four mechanisms, not one

Scoped 2026-08-16 by parsing each program in the bucket and reading the exact
normalized declaration at its rejecting site, then re-scoped after `synth/shape`
and `normalMap` landed. **"Unsupported global declaration" is a single message
covering four structurally different shapes**, so treating the bucket as one
unit of work would be a planning error.

| Sub-shape | Programs | Blocking declaration |
| --- | ---: | --- |
| **Mutable uninitialized global** | **4** — `cellRefract`, `effects`, `kaleido`, `synth/noise` | `float emboss[9];` (first three, *identical*); `vec2 globalCoord;` (`synth/noise`) |
| **Const literal array** | 2 — `osd`, `spookyTicker` | `const int GLYPHS[80] = int[80](…)` |
| **Const struct array** | 2 — `historicPalette`, `palette` | `const HistoricPalette PALETTES[PALETTE_COUNT] = HistoricPalette[PALETTE_COUNT](…)` |
| **Const scalar from a constant expression** | 1 — `bitEffects` | `const int mask = (1 << BIT_COUNT) - 1;` |

**`synth/shape` (row 184) closed the scalar form of the first row and
`normalMap` (row 185) closed the `ivec2[9]`/`float[9]` form of the second.**
Neither of the two remaining const-literal-array programs is reachable by adding
a key to `const-global-nine-table-v1`: both `osd` and `spookyTicker` are gated
behind JS-Number bitwise semantics, and `osd`'s table is `int[80]` rather than a
nine-element one, so the closure's frozen cardinality would have to be
generalized as well.

One correction to the first row, found by the `synth/shape` design pass and
still worth knowing before planning:

- **`synth/noise:noise` belongs to this sub-shape too**, carrying its own
  `vec2 globalCoord` (`noise.glsl:45`) behind a counted-for first blocker. It is
  counted in the counted-for row of the first-blocker census as well — a program
  can sit in two buckets, and a first-blocker census cannot show that. Fixing
  this mechanism may move it further than its row suggests.

**And it is not one program: every remaining member of this bucket is
double-blocked.** The normalMap design re-probed all nine with globals admitted
(`normalmap-parity/normalmap-design.md` §1, reproduced 9/9 by its review) and
every one of them reports a further mechanism behind the declaration:

| Program | Blocker once the global declaration is admitted |
| --- | --- |
| `cellRefract` | `66:29 unsupported typed type float[9]` — a **call site**, not a declaration |
| `kaleido` | `543:24 unsupported typed type float[9]` — same call-site shape |
| `effects` | `395:10 unsupported typed type mat4` |
| `osd` | `59:16 unsupported binary operator ^` — JS-Number bitwise |
| `bitEffects` | `141:13 unsupported binary operator &` — JS-Number bitwise |
| `historicPalette`, `palette` | `unsupported struct declaration`, shared with `synth/newton` |
| `spookyTicker` | `1:1 unsupported varying` |
| `synth/noise` | its counted-for first blocker, which is why it is censused there |

`normalMap` was the only member that reached CLEAN on one new mechanism plus a
carrier that already existed, which is why it went first.

### Two of the nine are not eligible, and it is the same limbo as `fractal`

`check_corpus.py`'s `_ADAPTERS` is exactly
`{classicNoisedeck/fractal:fractal, filter/historicPalette:historicPalette,
filter/palette:palette, synth/julia:julia}` — confirmed by import, not by
reading the doc. **`historicPalette` and `palette` are adapter-routed**, the same
class as `fractal`, whose adapter is known to implement a different algorithm
than its own corpus GLSL. Their eligibility must be resolved before any
mechanism is built for them, and they additionally need struct-declaration
support they share with `synth/newton`.

**So the portable portion of this bucket is 7, not 9.** Any plan that counts
`historicPalette` and `palette` is counting two programs that may not be
portable at all.

### Where to start, and what precedent does and does not apply

The **mutable-uninitialized-global array** shape is the best next target within
this bucket: 4 programs, three of which carry a byte-identical
`float emboss[9];`. `synth/shape`'s `float aspectRatio;` was the same shape
reduced to a scalar, and it is already built and shipped (row 184) — read
`shape-parity/shape-acceptance.md` before starting the array form.

**Do not assume `fixed_nine_table_proof.py` covers this.** Its capability is
`fixed-nine-local-literal-init-counted-read-v1` and its keys are
`filter/sharpen`, `filter/sobel`, `filter/lighting` — a **local**, **literal-
initialised**, counted-read `float[9]`. The blocked programs have a **global**,
**uninitialised**, mutable one. It is a useful structural precedent to read
first, and its census/loop-proof shape is worth copying, but it is not a carrier
you can simply add a key to. The same warning now applies to
`const_global_table_profile.py`: its capability is
`const-global-nine-table-v1`, its locks are frozen per key against a
**nine-element, literal-initialised, never-written, exactly-three-reads** table,
and its element type is an allowlist that deliberately excludes every `vec*`.

Note also that `bitEffects` and `kaleido` each additionally need their
already-frozen `scalar-uint-xor-v1` carrier wired — that proof exists and is
paid for, so those two are cheaper than their position in this table suggests.

**The array form is not a free extension of the scalar form.** The `synth/shape`
design probed it: going from `float aspectRatio;` to `float emboss[9];` costs
three further mechanisms — global array *type* admission (which `normalMap` has
now built for the **const** case only); a **non-`main` writer**
(`loadKernels()`), which forces a mutable reference and gives up the
compiler-level single-writer enforcement the scalar form gets for free; and
`float[9]` call arguments and parameters, which is the call-site rejection
`cellRefract` and `kaleido` both land on above.
And do **not** plan `effects` alongside `cellRefract`/`kaleido` — it
additionally needs `mat4`.

A materialization finding from that design, which is exactly the class of thing
that has misled this project five times: in the shipped JS these globals are
factory-scope `var`s that are **not** re-initialised per pixel, and
`aspectRatio` is a plain Number — **a double, never narrowed to f32** — while
`globalCoord` is a `Float32Array` with per-lane narrowing. Two globals declared
one line apart have different numeric contracts. Read the materialization per
declaration; do not infer it from the GLSL type.

`normalMap` extended that finding in a direction the `synth/shape` design had
backwards, and the array form must not be planned without it: **element
materialization also decides whether per-pixel re-evaluation is sound at all.**
The emitter emits an admitted source global as a `const` local inside the pixel
body, so the port re-evaluates it once per pixel. That is a no-op only because
`SOBEL_OFFSETS` is a base-index-protected *integer* pool entry and the two
kernels are plain Number arrays. A factory-scope `PooledFloat32Array` table is
aliased and overwritten by the first per-pixel scratch allocation — measured
against the pinned runtime — so had those offsets been `vec2`, the JavaScript
itself would clobber the table mid-render and the port would silently disagree
with the authority. Literal-only initializers are necessary, not sufficient.

## Known special cases

- `classicNoisedeck/fractal:fractal` remains adapter-only and has no canonical
  factory for its corpus GLSL. Its adapter implements a different algorithm.
  Authority must be resolved before treating the GLSL row as portable.
- `filter/dither:dither` still fails in the JavaScript reference's
  error-diffusion path. There is no working behavior to match until the
  upstream defect is resolved.
- `classicNoisedeck/colorLab:colorLab` and
  `classicNoisedeck/moodscape:moodscape` have deeper index/dead-code issues
  behind their first reported barrier.
- `mixer/distortion:distortion` and `synth/remap:remap` remain bespoke,
  multi-mechanism work.

See `DEFECTS-FOUND.md` for the confirmed upstream conflicts.

## Recommended order

1. **Continue global-declaration admission** — but as **four mechanisms, not
   one**, and against **7 portable programs, not 9**. See the decomposition
   section above before planning: `historicPalette` and `palette` are
   adapter-routed and in the same eligibility limbo as `fractal`, and **every**
   remaining member of the bucket is double-blocked, so no further program in it
   lands on a global-declaration mechanism alone.
   Two of the four sub-shapes are now built: the mutable **scalar** form
   (`synth/shape`, row 184) and the const **nine-element literal array** form
   (`normalMap`, row 185). The next one is the **mutable uninitialized array**
   shape — `cellRefract`, `effects`, `kaleido`, `synth/noise`, three of which
   carry a byte-identical `float emboss[9];` — and it costs a non-`main` writer
   plus `float[9]` call arguments and parameters on top of the declaration.
   `bitEffects` and `kaleido` also need their already-frozen
   `scalar-uint-xor-v1` carrier wired, which is cheap and for which Shapes183 is
   the worked example.
2. Then the varying bucket — **4 real programs** (`grime`, `texture`, `wobble`,
   `spookyTicker`); `wormhole:deposit` reports the same blocker but is already
   public. `spookyTicker` joined this bucket by the normalMap probe, and it is
   also behind a `const int GLYPHS[80]` declaration.
3. Then `out`/`inout` parameter admission, which `lightLeak` and `mandelbrot`
   both need. Warning: admitting `inout` gets `wcSimplify` past the validator
   and the **emitter** then fails with no support for a bare void-call
   statement, needed 19 times.
4. Leave the bespoke sampler, struct, uniform-block, and unresolved loop-proof
   tail for last. Note the struct bucket is **3 programs** (`synth/newton`,
   `historicPalette`, `palette`), not one, though two of the three are in
   adapter limbo.
5. Re-run the read-only frontier probe after **every** landed program. Do not
   carry this census forward by arithmetic — Shapes changed three bucket counts,
   normalMap changed three more, and in both cases at least one of them changed
   only in what it means rather than in its size.

## How to re-run this probe

Work in an `rsync`'d copy, never the live tree.

```python
import hashlib, json, pathlib, sys
sys.path.insert(0, "tools/glslcpp"); sys.setrecursionlimit(20000)
import generate_typed_slice as G
repo = pathlib.Path(".")
spec = json.loads(pathlib.Path("tools/glslcpp/typed_slice.json").read_text())
caps = tuple(spec["capabilities"])
corpus = pathlib.Path("tools/glslcpp/corpus/<REVISION>")
man = json.loads((corpus / "manifest.json").read_text())
typed = {r["program_key"] for r in spec["programs"]}
for entry in man["programs"]:
    key = entry["program_key"]
    if key in typed: continue
    src = (corpus / entry["source"]).read_text(encoding="utf-8")
    prog = G.analyze_program(G.parse_program(src, key, G._defaults(repo, key)), key)
    prog = G.attach_fixed_array_in_parameter_proof(prog)
    prog = G.attach_fixed_affine_centers13_proof(prog)
    try:
        G.validate_capabilities(prog, caps,
            source_hash=hashlib.sha256(src.encode()).hexdigest())
        print(key, "CLEAN")
    except Exception as exc:
        print(key, type(exc).__name__, exc)
```

To see what a program hits *next*, pass its already-built carrier as a keyword
argument (`scalar_uint_xor_profile="scalar-uint-xor-v1"`). That is how the
second-blocker table above was produced, and it is the difference between a
useful frontier and a misleading one.

Two traps, both paid for:

- **Do not probe by driving `generate_outputs` with a one-row slice.** The slice
  schema carries whole-suite profile censuses, so a one-row spec dies with
  `typed slice literal vec3 lane profile drift` — the generic last-clause
  message of a 14-clause `or` chain — which reads as a profile bug and is not.
  Per-program `validate_capabilities` is both correct and about two orders of
  magnitude faster, because `generate_outputs` re-runs `validate_corpus` and the
  full 212-program semantic report on every call.
- **A killed probe leaves the copy's `typed_slice.json` truncated.** `SIGTERM`
  skips the `finally` restore. If a re-probe suddenly reports typed programs as
  unported, that is the cause; re-copy the slice from the live tree.

The typed-list SHA-256 is taken over the sorted keys joined by `\n` **with a
trailing newline**. At 185 rows that is `75ea3f39…`; a bare `"\n".join(keys)`
over the same 185 keys yields `27f57027…` and will look like slice drift when
there is none.

## Process trap: do not close out a slice while a review is still running

Recorded 2026-08-16 because it happened, and it nearly cost a real finding.

Reviews of a large slice finish at very different times — the integration review
of Shapes183 ran **48 minutes**, long after every other lane had reported. The
controller declared the slice accepted, wrote the acceptance record, and deleted
the owned run root **before that review arrived**. It then came back with an
Important finding (a widened emitter arm with no regression lock) that had to be
fixed after "completion".

Worse, the run root held the reviewer's pre-work snapshot and its logs. It
happened to finish reading them first and said so explicitly. Had it been
mid-verification, the deletion would have destroyed the evidence underneath it
and produced a confusing failure that looked like the reviewer's fault.

Two rules:

1. **A slice is not done until every dispatched review has reported.** Track
   outstanding reviews explicitly; do not infer completion from "the workers are
   all finished." Implementation finishing and verification finishing are
   different events.
2. **Never delete a shared run root while any agent might still be reading it.**
   List live agents first. The storage gate says delete after evidence is
   summarized — "summarized" means *all* evidence, including evidence that has
   not been produced yet.

## Trap: validating in a copy breaks tests that reach outside the repo

The standing advice below — never run the suite against a tree you are editing,
run it in an `rsync`'d copy — has one exception you must know about, or you will
either chase a phantom regression or, far worse, wave a real one away.

Some oracle generators resolve the JavaScript reference as a **sibling of the
repository root**, by a hardcoded relative path. `emboss_parity_oracle_generator.mjs`
imports `'../../../../../noisemaker-for-cpu/src/effects/catalog.js'` and computes
`cpuRoot = path.join(path.resolve(here, '../../../../..'), 'noisemaker-for-cpu')`.
Beside the live checkout that resolves to `~/platform/noisemaker-for-cpu` and
works. Beside a copy at some scratch path it resolves to a sibling that does not
exist, and the test fails with `ERR_MODULE_NOT_FOUND`.

**The same test has now failed twice on a copy, for two entirely different
reasons.** Both times it was an artifact; both times the fix for one exposed the
other:

1. **No sibling.** The copy sat somewhere the hardcoded `../../../../../noisemaker-for-cpu`
   did not resolve → `ERR_MODULE_NOT_FOUND`. Observed at 441 tests, 1 failure.
2. **Sibling present but no `.git`.** Placing the CPU repo as a sibling fixed (1),
   and then the generator's `spawnSync('git', ['rev-parse','HEAD'], {cwd: cpuRoot})`
   failed because the `rsync` had excluded `.git` → `JavaScript authority commit
   drift`, which reads alarmingly like a real provenance failure. Observed at 528
   tests, 1 failure.

Both times the test passes on the live tree in about a second.

So a copy must reproduce **everything the oracle reaches for**: sibling layout
*and* version-control metadata. If you exclude `.git` for size, expect any
oracle that stamps a source revision to fail. Either include `.git` in the copy,
or accept the split and verify the affected tests live.

**The discipline, both halves:**

1. When a copy-run failure names a module-resolution or missing-path error,
   check whether the test reaches outside the repository before treating it as a
   regression.
2. **Never dismiss a copy-run failure as "just the copy thing" without running
   that single test against the live tree.** It takes seconds. Assuming the
   benign explanation is how a real failure gets shipped, and this trap makes
   that assumption feel reasonable.

Either place the copy so the expected sibling resolves, or run the affected
tests live and report the split honestly — "440 passed on the copy; the 1
failure is a copy-path artifact, verified passing live" — rather than rounding
to a clean number.

## Traps when scanning emitted assembly

Three ways an assembly audit produces a confident wrong answer. All three were
hit or nearly hit in real scans.

**Mangled-name prefix collision.** `8typed_1814…` is `typed_18`, **not**
`typed_181` — the digit run after the length prefix is the length, and the name
runs into whatever follows. A substring match on `typed_181` will happily select
`typed_18`'s functions and audit the wrong program. Resolve symbols by
demangling, not by grepping the mangled form.

**ARM64 spells things differently from x86_64, and a shared regex lies about
it.** The jump-table label is lowercase `lJTI` on ARM64 and uppercase `LJTI` on
x86_64, so a case-sensitive `LJTI` grep reports "no jump table on ARM64" — a
false architecture difference. ARM64 also allocates its frame with a pre-index
`stp …, [sp, #-N]!` rather than `sub sp, …`, so a `sub sp` frame-size regex
reports a false 0-byte frame. Write per-architecture patterns, or demangle and
parse rather than grep.

**Inlined helpers move the audit boundary.** When `map`, `offset` and
`periodicFunction` inline into `pixel`, auditing `pixel` alone is auditing four
functions' worth of code, and auditing the named helpers separately finds
out-of-line copies that the pixel path never calls. Establish the real pixel
scope first — which functions actually execute per pixel after inlining — then
audit that set, and say which bodies you audited inside which.

One positive pattern worth reusing: **fused-FP absence is best proven across the
entire translation unit**, not just pixel scope. Zero fused-FP instructions in
~600k lines of listing is an independent witness that `-ffp-contract=off`
reached the compile line; a clean pixel scope alone could be luck.

## Trap: a clean assembly gate can depend on a frozen input, not on the code

Found 2026-08-16 in the Shapes assembly audit, and it generalizes to every
program whose defines select among dispatch arms.

`typed_8::value` compiles to a real jump table (`LJTI196_0` → `jmpq *%rax`;
`br x10` on ARM64). The assembly gate still passed, because at the frozen
defines `40/30` the only path from `pixel` to `value` runs through an `offset`
arm those defines do not select — so clang inlines `offset` and constant-folds
the dispatch away. Pixel scope is genuinely free of indirect branches.

The gate result is therefore **conditional on an input**, and a green result
does not mean the code contains no jump table. Admit one alternate define value
for that program and the jump table lands in the pixel path.

Two consequences:

- When a program's defines select among arms, **record the gate result as
  conditional** and name the precondition. Do not let a later reader infer that
  the code is structurally free of indirect dispatch.
- Any work admitting alternate define variants for an already-gated program must
  **re-run the assembly gate**, and should expect to need a source-authenticated
  bounded dispatch shape.

The flip side is a genuine bonus: where a dead branch is folded away, the
assembly is an *independent, compiler-level witness* for a dead-code claim
boundary that no oracle case can discriminate. Worth citing when you have it.

## Known systemic condition: missing `noexcept` puts terminate pads in pixel scope

`glsl::Vec<N,T>::Vec(const FloatExpr<N>&)` at `glsl_types.hpp:164` is not
`noexcept`, so functions constructing a `Vec` from a `FloatExpr` carry an LSDA
and a `___clang_call_terminate` landing pad. It is unreachable on normal flow
and harmless, but it appears inside pixel closures and currently affects **51
functions** in the translation unit, including several programs' `pixel`.

Not a defect and not any one slice's to fix — but it is the standing reason an
assembly audit will report an exception path in pixel scope, and it would be a
cheap, broadly beneficial cleanup: adding `noexcept` there should clear all 51
at once. Anyone auditing assembly should recognise it rather than investigate it
afresh.

While you are in that area: `pow`/`atan2` route to platform libm while
`sin`/`cos` route to the repository's `fdlibm` (`glsl_runtime.hpp:42,61`). That
asymmetry is generator-wide, intended, and bit-exact against the oracles — do
not "fix" it into consistency.

## Trap: most of a foreign-carrier collision chain is unreachable

Found 2026-08-16 by sweeping **all 32 sibling profiles** against a new
mechanism's collision list, at both authorities. The result is uncomfortable and
applies to **every mechanism in the file**, not one:

- 32/32 foreign carriers are rejected — the fail-closed property is real.
- But the new mechanism's **own** message answers only **12 of 32** at the
  validator and **6 of 32** at the emitter. The other twenty are caught first by
  a neighbouring mechanism's guard (`Edge bvec3 contour…`, `Glitch mat4 chain…`,
  `Curl vector math…`, and so on), because the guard blocks run in a fixed order
  and an earlier one claims the row.

By this project's own standard — *a predicate whose deletion leaves the suite
green is decoration* — roughly twenty of the thirty-odd clauses in each chain are
individually unreachable. Delete any one and everything stays green.

**Why this matters, concretely.** A slice probes one sibling profile, sees its
own message, and writes "this proves the collision list is evidence rather than
decoration." That sentence is true only for the witness it picked. The next slice
copies the reasoning, and ships a chain in which the clause guarding *its* actual
collision partner is one of the unreachable ones.

**What to do.** Do not claim a collision chain is proven by one sibling probe.
Either record which siblings your chain actually owns — sweep all of them and
list the reachable subset — or add a test that records the ownership map so a
reordering that silently transfers a clause shows up. The staleness is inherited
and is nobody's single slice to fix, but the *claim* is cheap to make honest.

**A related claim that also does not generalize:** the two authorities do NOT
answer with the same message in every case. Outside a small matrix they
routinely diagnose different faults, because their guard blocks are ordered
differently — one sibling gives `mutable-global frame profile metadata mismatch`
at the validator and `Gather Sorted round profile metadata mismatch` at the
emitter. Both remain fail-closed; only the diagnosis differs. Treating a benign
ordering difference as a bug, and reordering guard blocks to "fix" it, would
disturb frozen messages across unrelated mechanisms. Scope any same-message
claim to the rows you actually tested.

## Method: prove a check is load-bearing by DELETING THE CHECK

Adopt this as standard for every new profile module. It found **three separate
vacuities in the Shapes slice alone** — two caught by the implementer using it on
itself, one caught by a reviewer using it on the implementer. None of the three
would have shown up in any suite.

The technique: copy `tools/` and `tests/` to a scratch directory outside the
repository, delete **one predicate at a time from the module source** (not from
the test, and not by mutating the input), and record which tests go red. Then
restore and diff clean. Tabulate the result — one row per predicate.

| Predicate deleted | Expected |
|---|---|
| each lock in turn | at least one test RED, with a message naming *that* lock |
| any lock | never GREEN |

A predicate whose deletion leaves the suite green is decoration, however
carefully written. A test that goes red with the wrong message is testing a
different lock than its name claims.

The three vacuities this caught, as a taxonomy of how they hide:

1. **The coarse gate absorbed it.** A `-0.0` mutant appeared caught, but the
   node hash was firing, not the sign lock — see the `Symbol` trap below.
   *Cure:* order value checks ahead of node identity.
2. **The refreeze helper handed the mutation to the lock under test.** A helper
   refroze semantic fields wholesale, so with the lock deleted the module raised
   nothing at all. *Cure:* refreeze only hash fields, never semantic ones.
3. **An earlier lock fired first.** A test named for an ancestry lock was
   actually being caught by an owner-body-shape lock; the ancestry lock's
   message appeared in no test in the suite. *Cure:* mutate the thing that lock
   uniquely owns, and assert its specific message.

Mutating the input tells you the module rejected something. Deleting the check
tells you *which check* did the rejecting. Only the second is proof.

## Trap: `Symbol` embeds its declaration span, so value mutations self-absorb

Found 2026-08-15 while building the Shapes float-bit ingress lock, and it
generalizes to **every value-level lock in the project**.

The typed IR's `Symbol` carries its declaration span. So changing a literal's
*value* — `0.0` → `-0.0`, a magnitude, a type suffix — also shifts the hash of
the node containing it. A mutation test written the obvious way (mutate the
source, assert it raises) therefore passes whether or not the check you meant to
prove ever executed. The node-identity hash absorbs it, exactly the way the
coarse whole-program hash absorbs structural mutations.

This bit the `seedFrac` positive-zero lock: the `-0.0` mutant was being caught by
the ingress operand's node hash, not by the sign check. It was self-caught before
landing; it would not have shown up in any suite.

Two defenses, both required:

1. **Order the value check ahead of node identity**, so the value lock is the
   first thing that can fire.
2. **Test the lock by deleting the lock, not by mutating the source.** Remove or
   weaken the check in a scratch copy and confirm a test goes red. Then, in the
   real mutation test, refreeze every surrounding span and hash record to the
   mutant so only the intended arm can fire, and assert the coarse and identity
   messages did *not* fire.

The general rule this is an instance of: **a mutation test proves nothing until
you have shown it fails for the reason you intended.** Sabotage the check, not
the input.

## Trap: "whole-program" node censuses walk only `function.body`

Found 2026-08-15 during the Shapes profile review. Affects at least
`linear_srgb_lane_index_profile.py`, `shapes_float_bits_ingress_profile.py`,
and the `scanline_error_float_bits_ingress_profile.py` precedent all three
inherit from — so treat it as the shared shape, not a one-module bug.

These modules advertise a **whole-program** census: the set of admitted nodes
must match the frozen set exactly, and an extra node anywhere is a hard failure.
That claim is slightly wider than the code. The walkers iterate
`program.functions` and descend `function.body`, so a node planted in a **global
declaration initializer** is outside the census. It would still be caught, but
only by the declarations-bearing coarse hashes — which means a mutation that
refreezes those coarse hashes could hide a node there.

Nothing exploits this today and it is not a regression. It matters because the
whole point of these censuses is to be the thing that still holds when the
coarse gate is refrozen; a census with a coarse-hash-only blind spot is exactly
the vacuity the modules exist to prevent, just relocated.

Fixing it means extending the walkers to global declaration initializers across
all the modules that share the pattern, which is a dedicated pass rather than
something to bolt onto a single program's slice. Until then: when you write a
new census, walk declarations too, and do not describe a census as
"whole-program" if it only covers function bodies.

## Durable execution rules

- Insert slice rows in exact sorted order.
- Validator and emitter remain independent authorities.
- Every widening needs a named accepted witness and a new rejection at the new
  boundary.
- Repair historical reconstruction tests by classifying each assertion; never
  bulk-rewrite milestone data.
- Match the shipped JavaScript materialization, including its float32 staging,
  rather than assumed GLSL semantics.
- Validate from one task-owned immutable snapshot and build root outside the
  repository. Route Python bytecode, caches, temporary files, builds, assembly,
  and logs into that root; compare full pre/post repository manifests and
  delete only the exact owned root.
