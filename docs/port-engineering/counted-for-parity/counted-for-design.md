# Counted-for parity — the nine-program bucket

Design investigation for the largest remaining first-blocker bucket: the nine
programs that first-block on `unsupported counted-for program proof`
(`synth/julia:julia` additionally/instead on `counted-for safety charge`).
Bucket membership per `REMAINING-EFFECTS.md` (2026-08-16 census, 185-row
slice): `classicNoisedeck/fractal:fractal`, `classicNoisedeck/noise:noise`,
`filter/dither:dither`, `filter/lightLeak:lightLeak`, `filter/median:median`,
`filter/parallax:parallax`, `synth/mandelbrot:mandelbrot`,
`synth/noise:noise`, `synth/testPattern:testPattern`.

Status: **DESIGN — pre-implementation, prepared by the counted-for lane
(2026-08-17).** Nothing lands in this lane. Every figure below was **measured
this session** against the pinned corpus `a024dc3a960cc44af454abc7aebce50456c194e6`,
the read-only JS authority at `$RUN_ROOT/oracle/noisemaker-for-cpu`, and the
live tree's frontend (imported read-only; every destructive probe ran in an
`rsync`'d copy under `$RUN_ROOT/workers/counted`). The live tree's slice was
**187 rows / 44 capabilities** at measurement time (cellRefract and kaleido
landed; wobble and effects had not).

**Headline findings, in order of decision weight:**

1. **"Counted-for program proof" is not one mechanism — the nine programs
   need four different bound shapes** (const-global-literal ×3,
   uniform-metadata runtime bound ×2, if-chain bounded local ×1, while-loop
   bespoke certificate ×1, plus three non-portable/deep cases). A plan that
   treats the bucket as one unit of work repeats the global-declaration
   bucket's four-sub-shapes error.
2. **Three programs are measured CLEAN at both authorities behind only
   KNOWN mechanisms**: `parallax` (source-global-literal key + a
   `textureLod` identity arm), `lightLeak` (+ out/inout + a bare-void-call
   emitter arm), `mandelbrot` (same as lightLeak at 5× scale + `log`). The
   census's "first blocker only" warning underestimates exactly as it did
   for wobble and effects; the ladder (§4) is the bucket's decisive
   deliverable.
3. **The `loop-proof-study`'s budget objections are obsolete.**
   `mandelbrot`'s 500-trip loop fits the current 512 cap raised for
   `reindex:nmReindexReduce` — measured: trips 500, product 500,
   charge 1500, all inside `COUNTED_FOR1_MAX_*`. It is fingerprint-only
   reuse of `source-global-literal-int-v1` today.
4. **`synth/noise` is the frame module's designed second key**, not an array
   module key (§6). Its whole closure is four carriers, every one a new key
   in an existing dict-keyed module; no new module.
5. **Two standing non-portability claims do not survive re-measurement
   against the pinned snapshot.** `dither`'s error-diffusion defect is FIXED
   in the pinned bytes (the quoted broken `errRow` line is now a
   pre-initialized 18-element array; `ditherType=7` renders, differs from
   Bayer on 398/1024 lanes, and is deterministic). `fractal`'s
   no-canonical-factory fact is confirmed, but the accompanying "adapter
   implements a different algorithm" claim could not be confirmed by
   side-by-side inspection (§2.8). Both corrections are recorded with their
   evidence and attribution.

---

## 1. What the counted-for gate actually demands

The gate machinery, read from the live frontend (all three files
cross-referenced this session):

- `frontend/semantic.py:291-313` — `analyze_program` **always** attaches
  counted-loop proofs canonically and stores the whole-program summary in
  `typed.counted_loop_proof`. A fresh probe program therefore always agrees
  with the rebuild, and only the *summary* gates can fire.
- `frontend/loop_proof.py` — `_annotate_statement` proves a `for` loop iff:
  declaration-style int (or exact-integer float) induction, literal or
  **proved-bounded** start/bound, `<`/`<=` condition on the induction
  variable, unit `++` update. Bounds become provable from three seed
  sources: `source_global_bounds` (the frozen
  `_SOURCE_GLOBAL_LITERAL_INT_PROFILES` dict keys), `runtime_scalar_bounds`
  (the `runtime-loop-bound-v1` contract), and `runtime_lane_bounds`
  (swizzle-lane bounds). `while`/`dowhile` are **never** provable — no arm
  exists. Local bounds are recognized only as const-int literals,
  `int(ceil(clamp-bounded float))`, or the reverb-specific
  `clamp(uniform,1,8)`.
- **Validator** (`generate_typed_slice.py`): per-loop caps at `:3705-3711`
  (`unsupported counted-for safety charge`: trip ≤ 512, depths ≤ 3,
  product ≤ 262144, charge ≤ 262656), then the program gates at
  `:3914-3938` — `malformed` if the submitted summary disagrees with the
  rebuild; `unsupported counted-for program proof` if the call graph is
  cyclic, **or** (`:3920-3938`) if `unproved_loop_count > 0` or any cap is
  exceeded while at least one loop exists. Gate order: the counted-for gates
  run **before** the global-declaration admission loop (`:4111`) — which is
  why `synth/noise` censuses as counted-for even though it also carries the
  `vec2 globalCoord` declaration blocker.
- **Emitter** (`emit_typed_cpp.py`): an independent copy of the same three
  gates (`_validate_counted_loops`, `:2480-2538`), then statement-level
  gates: a `for` without `loop_proof` dies as `malformed counted-for
  statement` (`:4523`), and `while`/`dowhile` are not in the admitted
  statement kinds at all (`:4859`).

So per program, "satisfying the counted-for proof" means one of:

| Shape | Mechanism that satisfies it | Programs |
| --- | --- | --- |
| Bound is a `const int` global with **literal** initializer | new key in `loop_proof.py::_SOURCE_GLOBAL_LITERAL_INT_PROFILES` (auto-supplied carrier; the Task-23 shape) | lightLeak (`POINT_COUNT=6`), parallax (`MARCH_STEPS=32`), mandelbrot (`MAX_ITER=500`) |
| Bound is a **parameter passed a metadata-bounded uniform** at one call site | new per-key record in `runtime_loop_bound_profile.py` (the tetraColorArray shape) | synth/noise, classicNoisedeck/noise (`octaves: i(2,1,8)`) |
| Bound is a **local set by an if-chain** | new bound rule in `_local_bound` (nothing recognizes it today) | testPattern (`numDigits ∈ {1,2,3}`) |
| `while` loops | **no generic proof exists or can exist**; bespoke whole-program combinatorial certificate (the `fixed_nine`-class hand-fingerprinted proof) | median (4 nested whiles) |
| Mixed float-induction-on-uniform / uniform-bound / multi-var init | three separate shapes in one program | fractal (not portable, moot) |
| Const-composed global + non-literal start + pixel-derived bound | outside every existing shape | dither (see §2.9) |
| Proved but trip 1000 > 512 | cap widening with a reindex-class argued maximum | julia (adapter-only; moot) |

## 2. Frozen authority — per-program facts

Measured with the family helper formula (`_whole_program_identity` /
`_interface_identity` from `loop_proof.py` — the same one the frame/array
modules share). Spans in the per-program loop tables are **normalized-source**
coordinates; the `frozen-facts` probe output lives in the lane's run root.

### 2.1 `filter/parallax:parallax`

| Fact | Value (measured) |
| --- | --- |
| Source | `sources/filter/parallax/parallax.glsl` |
| Raw bytes / SHA-256 | 2,430 / `5ce5dce2ec8e8d7ebd3024c6a5bd5dcb068d0cf322bfd105c4fb3546e1b97642` |
| Normalized bytes / SHA-256 | 1,902 / `281c8163d7f5fd47dc2ebd258003b04e1d41f7687c52e3c99e5aa56c911bd5f0` |
| Defines | `()` |
| Whole / interface SHA-256 | `920fe71bb122690f2169d2ee27ab6a4f908a18bf55b6031cb44fe51ba50c5eff` / `9ff15dc1fd4f97bd0d392bd40d1cab39a4c1fcb988c2d79d595f933235d39314` |
| Node census | 165 nodes / 6 assigns |
| Declarations | 9 (2 samplers `inputTex`/`heightMap`, 4 uniforms, 1 output, `const int MARCH_STEPS = 32`, `const float SHIFT_SCALE`) |
| Functions | 4, **all reachable**; call edges 4 |
| Resources | uniforms `(inputTex, heightMap, tileOffset, fullResolution, direction, pivot)`; samplers `(inputTex, heightMap)`; texture yes; derivatives no |
| Loop summary (live) | loops 0, unproved 1 |
| Mechanism census | 0 out/inout params, 0 bare calls, 0 bit-ops, 0 index expressions |

**The one loop**: `main 59:9-71:10`, `for (int i = 1; i <= MARCH_STEPS; i++)`
— const-global-literal bound, depth 1, contains a `break`. With the
`source-global-literal-int` seed attached (§4 method): **trips 32, product
32, charge 32** — trivially inside every cap. `MARCH_STEPS` is declared at
normalized `13:1` and also read at normalized `58:26`
(`float stepSize = 1.0 / float(MARCH_STEPS);`) — both reads freeze in the
per-key `reads` lock.

### 2.2 `filter/lightLeak:lightLeak`

| Fact | Value (measured) |
| --- | --- |
| Raw / normalized SHA-256 | 5,047 B `61bcb2989992c109dcf73ac5b34bb4dfa7f6603b54c111a84e69b6f73a9501bb` / 4,360 B `4568d0dd53883cfc1cb1ba8237a894e9c5740c4f1a045dff377221722f3eef72` |
| Defines | `()` |
| Whole / interface | `9fc72ea8a4105bdfd38e58240bd0a1e4ae448c1f6ff954a31fd7967edfd991ae` / `e8032324cde699ade81d0920220709d5087d576f3dbaee828da74f6152719ec0` |
| Node census | 574 / 19 |
| Declarations | 12 (`const float TAU`, **`const int POINT_COUNT = 6`**, 1 sampler, 7 uniforms, 1 output) |
| Functions | 7; reachable 6, unreachable 1; edges 8 |
| Resources | uniforms `(inputTex, resolution, tileOffset, fullResolution, alpha, color, speed, seed, time)`; sampler `(inputTex)` |
| Mechanism census | **2 out params** on one function — `voronoiCell(vec2, float, float, out vec3 cell_color, out float cell_dist)` (`60:50`); **2 bare void-call statements**, both `voronoiCell` in `main` (`114:5`, `125:5`); 1 `uvec3>>uint` (already-admitted vector form); 0 index expressions |

**The one loop**: `voronoiCell 65:5-80:6`,
`for (int i = 0; i < POINT_COUNT; i++)` — with the seed attached: **trips 6,
product 6, charge 12**.

### 2.3 `synth/mandelbrot:mandelbrot`

| Fact | Value (measured) |
| --- | --- |
| Raw / normalized SHA-256 | 14,855 B `0587dbc29f2dc8c186d7c47ebe6182e89dfe0387fc29a23826cac15499fba615` / 10,414 B `c062ee7852d0bfab69ca1e2ead6ad68d95dfa5fda9cff8232254b38b34c311a9` |
| Defines | `()` |
| Whole / interface | `d6a5840667d7293fa428a88eef00f8bcf4612a733958e738628c876ed210ebd3` / `2f497a1fb59406d16decbd6bb2d0a5e4e7e5536774fa7ec56a34de12de657c43` |
| Node census | 994 / 51 |
| Declarations | 24 (18 uniforms, 1 output, 4 const floats `PI/TAU/BAILOUT/LOG2`, **`const int MAX_ITER = 500`**) |
| Functions | 24, **all reachable**; edges 46 |
| Resources | 18 uniforms, no samplers, no texture, no derivatives |
| Mechanism census | **10 out params** across 4 functions (`getPOI` ×2, `mandelbrot_df64` ×7, `transformCoords_df64` ×2); **3 bare void-call statements** (`computeValueAt_df64` → `transformCoords_df64` `320:5` and `mandelbrot_df64` `324:5`; `main` → `getPOI` `374:5`); `log` builtin in the df64 escape smoothing; 0 index expressions |

**The one loop**: `mandelbrot_df64 226:5-261:6`,
`for (int n = 0; n < MAX_ITER; n++)` — with the seed attached: **trips 500,
product 500, charge 1500**. `MAX_ITER` is also read at raw `381`
(`int maxIter = min(iterations, MAX_ITER);`) — both reads freeze in the
record. The `iterations` uniform is **clamped by the source itself** at that
site, so no uniform bound is needed anywhere — the program's only
unproved-loop dependency is the const global.

### 2.4 `synth/noise:noise`

| Fact | Value (measured) |
| --- | --- |
| Raw / normalized SHA-256 | 18,131 B `410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274` / 8,516 B `5a9c937c83b48e85335f1d69b7a364124a3bcd3e1ece1df85b0d6f7dee929205` |
| Defines | `(("LOOP_OFFSET","int","300"),("NOISE_TYPE","int","10"))` |
| Whole / interface | `023d933cf3e6d2efcb0e47843fabaca020b4f493ea941331fd6d20b44c1d79fd` / `8327df301a143416b03bdb757d3d287700b89bbf543e16294ec8d94f667bb69f` |
| Node census | 1,139 / 45 |
| Declarations | 15 (13 uniforms, 1 output, **`vec2 globalCoord` mutable global** at normalized `31:1`, symbol id 15) |
| Functions | 30; reachable 11, unreachable 19; edges 31 |
| Resources | 13 uniforms, no samplers, no texture |
| Mechanism census | 1 `floatBitsToUint` (`97:10` area, the `sFrac` ingress); **3 scalar-uint `^`** — `(fracBits * 374761393u) ^ 0x9E3779B9u` etc. as the three ordered children of one `uvec3` constructor (`96:9-99:30`); 1 `uvec3>>uint` (admitted form); 0 index expressions |

**The one loop**: `multires 250:5-258:6`,
`for (int i = 1; i <= oct; i++)` where `oct` is `multires`'s third
parameter, passed the `octaves` uniform **directly at the single call site**
`main 306:14 multires(centered, freq, octaves, float(seed), blend)` (raw
`524`). The JS metadata (`src/effects/specs.js:32` and the upstream snapshot,
both measured): `octaves: i(2, 1, 8)` — default 2, min 1, **max 8**. With a
tetra-style `RuntimeScalarBoundSeed` on the **parameter** symbol:
**trips 8, product 8, charge 8**, whole-program summary
`(1, 0, 1, 8, 8, True)` — CLEAN.

### 2.5 `classicNoisedeck/noise:noise`

| Fact | Value (measured) |
| --- | --- |
| Raw / normalized SHA-256 | 31,255 B `4cd68543729f94788ef6fa2a484dd47d76154814b027128bef5eb9c8d7461663` / 14,064 B `9f97d19e355f32e3821057ba8859770a87cbec56c57946d14378764deb8da0f0` |
| Defines | `(("COLOR_MODE","int","6"),("LOOP_OFFSET","int","300"),("METRIC","int","0"),("NOISE_TYPE","int","10"),("REFRACT_MODE","int","2"))` |
| Whole / interface | `400c2d5fa6c879b311601abb0e5e52d693b4798bb49cb712430e5268e1549960` / `82b04cb03ee9125c8fc9bfdcae13de8345bd65608bff0bc16a61ae488efcfb58` |
| Node census | 1,718 / 65 |
| Declarations | 29 (24 uniforms, 1 output, 4 const `mat3` palette matrices `fwdA/fwdB/invB/invA` — literal-initialised, already generically admitted) |
| Functions | 40; reachable 15, unreachable 25; edges 41 |
| Mechanism census | same jitter block as synth/noise (1 `floatBitsToUint` + 3 scalar-uint `^` + 1 vector shift); **10 index expressions** — the `linear[i]`/`srgb[i]` vec3-lane indexed accesses inside `linearToSrgb` (`459:5`) and `srgbToLinear` (`471:5`), both **unreachable** at the frozen defines |

**Loops (3)**: `multires 533:5-558:6` (unproved; same tetra shape as
synth/noise, `octaves` uniform `i(2,1,8)` per the upstream snapshot — the
seed proves it: summary `(3, 0, 1, 8, 8, True)`), plus the two 3-trip
literal loops in the unreachable sRGB converters (already proved).

### 2.6 `synth/testPattern:testPattern`

| Fact | Value (measured) |
| --- | --- |
| Raw / normalized SHA-256 | 5,919 B `f913300a1312c6630d56fa1cc2faf2cb17fe0643d832473fdec7b66dd373cb20` / 4,450 B `1f150d5cfdc5c037a460e081821f44e835095d63b4b20b67352999eadc8115aa` |
| Defines | `()` |
| Whole / interface | `c75f9c139f901d965d051f4c24eb95b02103fc86655641873c31044aa9a567bf` / `cdc5ea07157c144ca39a20a853a6d105f83bcaa49e5e25681737caa4edec5c3a` |
| Node census | 516 / 12 |
| Declarations | 7 (5 uniforms, 1 output, **`const int GLYPH[10]`** literal table at normalized `13:1`) |
| Functions | 11, all reachable; edges 10 |
| Mechanism census | **4 index expressions** (`GLYPH[digit]`, `digits[…]` ×3); **`int >> int` + `& 1`** one site each — structurally the glyphMap two-node carrier shape (`(GLYPH[digit] >> bitIndex) & 1`, `digit ∈ [0,9]`, `bitIndex ∈ [0,14]` guarded by `sampleGlyph`'s range checks); a local `int digits[3]` mutable array |

**Loops (2)**: `renderNumber 55:5-58:6` `for (int i = 0; i < 3; i++)`
(proved, literal) and `renderNumber 61:5-78:6`
`for (int d = 0; d < numDigits; d++)` — **unproved**. `numDigits` is a local
set by an if-chain (`= 1; if (number >= 10) = 2; if (number >= 100) = 3`),
where `number` descends from the `gridSize` uniform through
`checkerboard`'s arithmetic. No existing bound rule recognizes the shape.

### 2.7 `filter/median:median`

| Fact | Value (measured) |
| --- | --- |
| Raw / normalized SHA-256 | 3,846 B `95e869c02fe2645f4a1b5af5a7446b3f2bacb888f2c965bc272ba56b10666e5d` / 3,267 B `4d84a477b2a53afad21f407b92539d35725e04a2d6a70d2c3f692ba6b6eb0a35` |
| Defines | `(("RADIUS","int","3"))` |
| Whole / interface | `8ad185e431d817133168c61106d284a35e108a2e9da80d1427138aa09091142a` / `b86248644c423a68e4c6730d867582076c1c7b92b15d15c75bd97ba8681a3203` |
| Node census | 302 / 11 |
| Declarations | 3 (sampler, `threshold`, output) |
| Functions | 6, all reachable |
| Mechanism census | **4 `while` loops** (a Hoare-style in-place selection: outer `left < right` `63:5`, scan `scanLeft <= scanRight` `68:9`, and the two single-line cursor scans `69:13`/`70:13`); **two mutable local tables** `uvec2 majorRecords[49]` / `uint blueRecords[49]` (`40:11`, `41:5`); **18 index expressions**; scalar-uint `&`×2 `|`×2 `<<`×2 `>>`×2 (with **int** shift counts); `packHalf2x16`/`unpackHalf2x16`; 1 `floatBitsToUint`; post `++`/`--` **statements** (`scanLeft++`, `scanRight--`) — a statement class admitted today only by the computeRank-locked discarded-counter proof and the fixed-grid proof, and the counter proof covers `++` only |

Loops: the `-3..3` fill pair is proved (`trips 7, product 49, charge 56`);
the four whiles are the blocker.

### 2.8 `classicNoisedeck/fractal:fractal` — not portable; the measured evidence

Frozen facts for the record: raw 10,067 B
`a73c8044185be58e3ae1b0f14b954dbaa7bb8852290b821dba44167fee5e037b`,
normalized 9,061 B
`d30bc823bc8beba8b818b13724ddc980e52c3545765a5ea38766fab41cf3aea6`,
17 functions (15 reachable), 1,114 nodes. Three internally different
unproved loops: `julia 261:5` (`i < iterScaled` — local-bound),
`mandelbrot 301:5` (float induction on `float(iterations)`, non-decl
initializer — two shapes stacked), `newton 220:5` (`i < iterations` — raw
uniform, no clamp). Even if portable it would need three separate proof
answers; it is not portable:

- **No canonical factory — confirmed by direct measurement.**
  `src/effects/generated/glsl-coverage.js` records
  `"effectId": "classicNoisedeck/fractal" … "status": "adapter" …
  "generatedBytes": 0`. `canonical-kernels.js` contains **no registration**
  for the key (measured: zero matches across the file; the adapter table
  `src/effects/adapters/index.js:12` routes
  `'classicNoisedeck/fractal:fractal': fractalFactory`). The C++ side
  agrees: `check_corpus.py:28` lists it in `_ADAPTERS`. There is no
  canonical authority for the corpus GLSL to be ported against.
- **The "adapter implements a different algorithm" claim — recorded with
  attribution, not confirmed by this lane.** `DEFECTS-FOUND.md` §3 records
  the divergence as oracle-agent-verified. My own side-by-side of the
  adapter (`src/effects/adapters/fractal.js`) against the corpus GLSL found
  the four paths structurally aligned — same `map` scalings, same
  `iterations * 2` / `cutoff` / escape-`4` julia; same
  center-swap-commented newton; same `z²+c`-via-`mat2` mandelbrot with
  identical escape and returns; same colorization tail. The adapter's own
  header claims "Direct CPU translation of the pinned canonical
  fractal.glsl … not a different algorithm." Structural alignment cannot
  settle **bit-level** agreement (the adapter's `Math.fround` boundaries,
  `Math.hypot`, and scalar staging differ from a straight GLSL lowering),
  which is presumably what the oracle agent measured. The operative fact
  for the port is the missing canonical factory either way; resolving the
  divergence question is upstream work, not port work.

### 2.9 `filter/dither:dither` — measured correction to the standing claim

Frozen facts for the record: raw 19,391 B
`a966f1746213c8206c5cb57a88cafd8033eb8f8cb08b207209eb31479a11abdb`,
normalized 15,250 B
`eb8300add593991110a6c1d38989831a647a91cb3ece27d5487d52fafc8e6395`,
21 functions (20 reachable), 1,281 nodes. Loops: three proved
(`findClosest4/15/16` literal bounds) and three unproved in `errorDiffusion`
— `i < FS_ERR_W` where `FS_ERR_W` is a **const-composed global**
(`FS_BLOCK + FS_APRON_MAX + FS_RPAD + 1`, a `binary` initializer — outside
`source-global-literal-int-v1`'s literal-only rule), `r = -FS_APRON_MAX …
r <= ly` (non-literal start, pixel-derived bound), nested
`c = -FS_APRON_MAX … c < FS_BLOCK + FS_RPAD`. Plus 24 index expressions,
`vec3[16]`/`vec3[15]`/`vec3[4]` const palette tables, two `mat4` const
tables, and JS-Number signed-int `&` ×6. Whatever the counted-for answer,
dither is a multi-mechanism program.

**The standing non-portability claim does not reproduce.** `DEFECTS-FOUND.md`
§1 quotes `canonical-kernels.js:11071-11073` as
`var errRow = []; … .reduce(…, errRow[i])` throwing
`TypeError: Cannot set properties of undefined (setting '0')` on every
error-diffusion render. Measured this session against the pinned snapshot
(`$RUN_ROOT/oracle/noisemaker-for-cpu`; `canonical-kernels.js` SHA-256
`66adc01c…` — byte-identical to the pin the cellRefract/kaleido/effects
oracles froze):

- Line 11071 now reads
  `var errRow = [new $runtime.PooledFloat32Array([0, 0, 0]), … ×18];` —
  pre-initialized with exactly `FS_ERR_W = 4+11+2+1 = 18` elements. The
  quoted broken form is not in the pinned bytes.
- Driving `canonicalFactory48` through the public
  `bindCanonicalKernel`/`runPass` path with `ditherType=7`
  (`DITHER_ERROR_DIFFUSION`): **renders successfully** at 4×4, 8×8, and
  16×16; the error-diffusion arm **differs from the Bayer-4 control on
  398/1024 float lanes** (the path genuinely executes), and two identical
  runs agree on **0/1024 lanes** (deterministic). The `ditherType=1`
  control reproduces the pinned golden arm.

Consequences, stated carefully: the *defect entry* is stale against the
pinned authority, and `REMAINING-EFFECTS.md`'s "no working JS behavior to
match" no longer holds — there is now a working, deterministic reference
behavior. That reclassifies dither from "not portable" to "portable in
principle but deep" (the loop shapes and bit machinery above). `DEFECTS-FOUND.md`
should be corrected by whichever lane next touches it; this document records
the measurement, and dither's port cost should be re-scoped against the
current snapshot rather than planned around the crash.

### 2.10 `synth/julia:julia` — the safety-charge row is adapter-only too

For completeness (julia is censused separately as `counted-for safety
charge`): its two 1000-trip literal loops are fully proved and trip 1000 > 512,
so the per-loop `safety charge` gate fires (`297:5`). But julia has **no
canonical registration** (measured: zero matches in `canonical-kernels.js`)
and is in `check_corpus._ADAPTERS` — the same adapter-only limbo as fractal.
The cap question is moot until the authority question is answered; if it ever
is, the answer is a reindex-class argued cap (1000 is the source's own
hard-coded escape budget), not a round number.

---

## 3. Loop census — the whole bucket, one table

Every `for`/`while` loop per program, with bounds shape and owner
reachability at the frozen defines (normalized spans; `P` = proved today):

| Program | Loop | Span | Shape | Reachable | Mechanism needed |
| --- | --- | --- | --- | --- | --- |
| parallax | main march | `59:9` | `<= MARCH_STEPS` (const-global literal 32) | yes | source-global-literal key |
| lightLeak | voronoiCell | `65:5` | `< POINT_COUNT` (const-global literal 6) | yes | source-global-literal key |
| mandelbrot | mandelbrot_df64 | `226:5` | `< MAX_ITER` (const-global literal 500) | yes | source-global-literal key |
| synth/noise | multires | `250:5` | `<= oct` (param ← uniform, metadata 1..8) | yes | runtime-loop-bound record |
| classicNoisedeck/noise | multires | `533:5` | `<= octaves` (param ← uniform, 1..8) | yes | runtime-loop-bound record |
| classicNoisedeck/noise | linearToSrgb / srgbToLinear | `459:5` / `471:5` | literal 3 (P) | **no** | — |
| testPattern | renderNumber digits | `61:5` | `< numDigits` (if-chain local ∈ 1..3) | yes | new bound rule |
| testPattern | renderNumber extract | `55:5` | literal 3 (P) | yes | — |
| median | fill y / x | `47:5` / `48:9` | literal `<= 3` (P) | yes | — |
| median | selection whiles ×4 | `63:5`, `68:9`, `69:13`, `70:13` | **while** (Hoare partition over 49 records) | yes | bespoke certificate |
| dither | errorDiffusion | `521:5`, `526:5`, `533:9` | const-composed bound; `-const` start; pixel bound | yes | beyond every shape (moot) |
| dither | findClosest ×3 | `372:5`–`408:6` | literal (P) | yes | — |
| fractal | julia / mandelbrot / newton | `261:5`, `301:5`, `220:5` | local / float-uniform / raw-uniform | yes | moot (adapter-only) |
| fractal | linearToSrgb | `119:5` | literal 3 (P) | yes | — |
| julia | iterateSmooth / juliaIterate | `297:5`, `187:5` | literal 1000 (P, over cap) | yes | cap argument (moot) |

## 4. The ladder — both authorities, rung by rung

Method (the varying lane's, applied to this gate family): an `rsync`'d copy
of `tools/glslcpp` under the scratch root with the counted-for family gates
conditioned on `CFC_BYPASS` levels — `proof` (the two program-proof raises),
`charge` (the per-loop caps), `stmt` (statement-level for-without-proof and
while/dowhile admission) — plus rung-by-rung levels for the *known* families
the ladder reached: `builtin:<names>` (named-builtin identity admission),
`outparam` (out/inout parameter directions), `barecall` (bare void-call
statements), `globaldecl` (mutable/const non-float globals), `uintxor`
(scalar-uint `^`), `arraytype` (array-typed declarations). **These bypasses
admit nothing** — they reveal gate order. The emitter's synthetic out-param
and bare-call emissions are placeholders: a CLEAN termination proves *gate
closure*, not that the real lowering (reference ABI, `__out__`
materialization) is designed — that remains each mechanism's implementation
work. No probe drove `generate_outputs` (the one-row-slice trap).

| Program | Rung 0 (live) | +counted-for | Then | Then | Termination |
| --- | --- | --- | --- | --- | --- |
| **parallax** | `59:9 program proof` | `24:26 unsupported builtin textureLod` | — | — | **CLEAN both** (validator + emitter; 91 lines) |
| **lightLeak** | `65:5 program proof` | `60:50 unsupported parameter direction out` | `114:5 only typed assignments are admitted` (emitter; bare call) | — | **CLEAN both** (148 lines) |
| **mandelbrot** | `226:5 program proof` | `116:24 parameter direction out` (validator) / `320:5 only typed assignments` (emitter bare call) | `273:24 unsupported builtin log` (emitter) | — | **CLEAN both** (402 lines) |
| **synth/noise** | `250:5 program proof` | `31:1 unsupported global declaration` | `97:10 unsupported binary operator ^` | `floatBitsToUint` (with `^` bypassed) | **validator CLEAN**; emitter has *no code path* for an uninitialized mutable global (crash at declaration emission — exactly the frame module's missing emission, §6) |
| **classicNoisedeck/noise** | `459:5 program proof` | `121:21 floatBitsToUint` | `124:10 binary ^` | `460:13 unsupported typed expression index` | **stops at typed expression index** — the colorLab/moodscape mechanism, unsolved today; the 10 sites are in *unreachable* code (the §17 family norm: dead code's grammar must still close) |
| **testPattern** | `55:5 program proof` | `13:1 unsupported global declaration` (`const int GLYPH[10]`) | `13:1 unsupported typed type int[10]` | `121:17 unsupported typed expression index` (validator) / `110:10 unsupported fixed-nine array declaration` (emitter: local `int digits[3]`) | **stops at typed expression index**, behind a generalized const-table and a non-nine local array; plus the JS-Number `>>`/`&` pair behind that |
| **median** | `47:5 program proof` | `40:11 unsupported typed type uvec2[49]` (validator) / `24:12 binary operator &` (emitter) | `50:13 typed expression index` (with the array type hypothetically admitted) | — | **stops at uvec2[49]/while**: first genuinely-new mechanisms stacked several deep |
| fractal / dither / julia | program proof / safety charge | — | — | — | not measured past rung 0 (authority/defect questions first; §2.8-2.10) |

Three readings that change the plan:

1. **The three CLEAN terminations are real and cheap.** parallax needs
   exactly two closures (the frozen profile entry + a `textureLod` arm);
   lightLeak adds the out/inout parameter admission and a bare-void-call
   emitter arm; mandelbrot is lightLeak's shape at 5× scale plus `log`.
   Nothing else fires — measured to CLEAN at both authorities.
2. **`textureLod` is a pure alias in the JS.** `glsl-runtime.js:400`:
   `textureLod: (surface, coord) => this.#texture(surface, coord)` — the
   lod argument is **dropped** and the call is `texture` itself (nearest
   sampling). parallax's factory passes literal `0` as the lod
   (`canonical-kernels.js:16714,16720`). The admission is an identity arm
   over the existing texture path with a frozen lod-`0` literal check; no
   mip machinery exists or is needed.
3. **The out/inout materialization is a designed shape, quote-frozen.**
   `canonicalFactory77` (lightLeak) lowers `voronoiCell`'s two out params
   as `voronoiCell.__out__ = [cell_color, cell_dist]` with call sites
   `(voronoiCell(uv, seed_f, t, base_cell, base_dist), [base_cell,
   base_dist] = voronoiCell.__out__, voronoiCell.__return__)` —
   callee-assigned pooled arrays read back by comma-expression
   destructuring. The C++ lowering (reference out-params, call-site
   lvalues) must match the *values*, and the emitter-side ABI design is the
   mechanism's real work; the ladder's CLEAN only proves no *further gate*
   fires behind it.

## 5. Mechanism decomposition, cost ranking, wave-2 order

| # | Mechanism | Status | Programs |
| --- | --- | --- | --- |
| A | `source-global-literal-int` new keys (frozen dict entries in `loop_proof.py`; carrier auto-supplied, row stays minimal) | **paid-for family** — 9 existing keys, identical shape; budget measured inside caps | parallax, lightLeak, mandelbrot |
| B | `textureLod` identity admission (lod-`0` literal → alias of the texture path) | new builtin arm; the JS materialization is a measured alias | parallax |
| C | **out/inout parameter admission** | **the new mechanism** — no out-param carrier exists (`inout_vec3_swap_profile` is a single-program swap shape, the narrowest precedent); JS `__out__` materialization quote-frozen; REMAINING-EFFECTS item 3's known work | lightLeak (2 params/1 fn), mandelbrot (10 params/4 fns), later wcSimplify |
| D | Bare void-call emitter arm (identity-gated, the `loadKernels` §12 pattern) | new arm in a known family; wcSimplify needs it 19×, lightLeak 2×, mandelbrot 3× | lightLeak, mandelbrot, later wcSimplify |
| E | `log` builtin identity admission | one arm; JS stdlib `log` = `Math.log` with result narrowing to check at implementation | mandelbrot |
| F | `runtime-loop-bound` new records (tetra family; module already dict-keyed; the record must generalize tetra's "exactly one loop" census to "the named unproved loop" — classicNoisedeck/noise has two proved loops alongside) | paid-for family; seed shape measured (param symbol, max 8, metadata 1..8) | synth/noise, classicNoisedeck/noise |
| G | `mutable-global-frame` second key | **designed for** (§6) | synth/noise |
| H | `scalar-uint-xor` new keys (3 sites, uvec3-constructor children — byte-shape match to the frozen carrier) | paid-for family, new per-key records | synth/noise, classicNoisedeck/noise |
| I | `floatBitsToUint` identity record (1 site each; grime's fifth-record precedent) | paid-for family | synth/noise, classicNoisedeck/noise |
| J | If-chain bounded-local rule (`numDigits`) | new bound rule in `_local_bound` (reverb-clamp pattern) | testPattern |
| K | Generalized const-literal array (int[10]) + non-nine local arrays | generalization of `const-global-nine-table-v1` (cardinality + element allowlist) | testPattern |
| L | Typed expression index | **unsolved** (colorLab/moodscape) | classicNoisedeck/noise (10 sites), testPattern (4), median (18) |
| M | While-loop bespoke certificate | genuinely new proof class (median-specific combinatorics) | median |
| N | `uvec2[49]`/`uint[49]` mutable local arrays; scalar-uint `&`/`|`/`<<`/`>>` with int shift counts; pack/unpack builtins; post `--` statements | several new carriers | median |

**Distance table and cost rank** (rungs counted from live RED to CLEAN or
first genuinely-new mechanism):

| Program | Rungs to CLEAN | New mechanisms needed | Cost rank |
| --- | --- | --- | --- |
| parallax | **2** (both CLEAN) | A + B | **1** |
| lightLeak | **3** (both CLEAN) | A + C + D | **2** |
| mandelbrot | **4** (both CLEAN) | A + C + D + E | **3** |
| synth/noise | **4** (validator CLEAN; emitter = G's emission) | F + G + H + I — all new keys in existing modules | **4** |
| classicNoisedeck/noise | 4 → **stops** | F + H + I + **L** | blocked on L |
| testPattern | 3+ → **stops** | J + K + **L** (+ glyphMap-shape int `>>`/`&` carrier widening) | blocked on L |
| median | 1 → **stops** | **M** + N (+ L inside) | deepest |
| dither | ≥3 → deep | beyond every loop shape + L-class machinery | re-scope (§2.9) |
| fractal | — | authority first (no canonical factory) | not portable |
| julia | — | authority first (adapter-only) + cap argument | not portable |

**Recommended wave-2 order** (after the in-flight kaleido/effects/wobble
lanes land; re-run the frontier probe first — never subtract):

1. **parallax** — the bucket's wobble: two known closures, both ladders
   measured CLEAN, smallest program (165 nodes), no secondary mechanisms at
   all (0 out-params, 0 bare calls, 0 bit-ops). Sorted neighbors today:
   `filter/outline:outlineValueMap` < parallax < `filter/patchwork:patchwork`
   (re-derive at insertion). Watch: the `test_task23_six_key…` census test
   pins the six-key set and will redden (the auto-attach-census lesson,
   cellRefract §16); the per-key `reads` lock freezes both `MARCH_STEPS`
   reads.
2. **lightLeak** — lands mechanism C+D at their smallest measured size
   (2 out params on one function, 2 bare calls). C is the shared mechanism
   wcSimplify (19 bare calls) and mandelbrot both need; building it here
   sizes it. The JS `__out__` materialization is quote-frozen (§4).
3. **mandelbrot** — rides C+D; adds only E (`log`). Budget measured inside
   caps (500 ≤ 512) — the loop-proof study's "needs budget increase"
   verdict is obsolete and must not be planned against.
4. **synth/noise** — four carriers, all new keys in existing dict-keyed
   modules (§6). No new module. Landing it also banks F+H+I for
   classicNoisedeck/noise, which then needs only L.
5. **Defer**: classicNoisedeck/noise and testPattern (behind L — solve L
   once for colorLab/moodscape and three more programs move);
   **median** (M is a bespoke proof class, then N's carrier pile);
   **dither** (now has a working authority — re-scope its cost against the
   corrected snapshot before planning); **fractal/julia** (upstream
   authority resolution first).

**Same-carrier-family groupings** (what rides one dict-keyed module):

- **A** (`_SOURCE_GLOBAL_LITERAL_INT_PROFILES` in `loop_proof.py`):
  parallax + lightLeak + mandelbrot — one family, three keys, three
  slices.
- **F** (`runtime_loop_bound_profile.py`): synth/noise +
  classicNoisedeck/noise — two records, one module; both records share the
  tetra shape (uniform metadata 1..8, single direct call site, no parameter
  reassignment) but must relax tetra's "exactly one loop in the program"
  census.
- **H** (`scalar_uint_xor_profile.py`) and **I** (floatBitsToUint identity
  lists in the generator/emitter): both noise programs together.
- **G** (`mutable_global_frame_profile.py`): synth/noise alone (§6).
- **C+D** need a **new module** (out/inout + bare-call) — shared by
  lightLeak, mandelbrot, and later wcSimplify; no existing module owns
  parameter directions.

## 6. synth/noise's double-block — frame module, second key

**Ownership verdict: `mutable_global_frame_profile.py`, as its own docstring
designed.** The module's header states `synth/noise:noise` "carries the
identical reduced form (`vec2 globalCoord`) behind a counted-for first
blocker and will want `mutable-global-frame-noise-v1` from this module with
no edit to Shape's row." Measured against the module registries:
`mutable_global_frame_profile.py` has `KEYS = (SHAPE_KEY,)` — **synth/noise
is its second key** (the docstring also anticipated the array programs,
which instead got their own `mutable_global_array_profile.py` — the array
module is `float[9]`-shaped with writer/store-ledger machinery, schema
censuses, and `_MUTABLE_GLOBAL_ARRAY_DEFINES` wiring that do not apply to a
scalar-form global; the REMAINING-EFFECTS table lists synth/noise in the
mutable-global row only because `globalCoord` is the same *sub-shape class*,
not because the array module owns it).

**The record sketch, measured** (`canonicalFactory265`,
`canonical-kernels.js:36445`):

- Materialization: `var globalCoord = new Float32Array([0, 0]);` — a
  factory-scope plain `Float32Array`, **byte-identical to synth/shape's
  globalCoord contract** (f32 lanes, per-lane narrowing, initial `[0, 0]`,
  never reset by `beginPixel`). `_LOCAL_TYPE_CONTRACT` maps `vec2` →
  `glsl::Vec2` unchanged from Shape's record.
- Declaration: normalized `31:1-31:18`, symbol id 15, storage `global`,
  uninitialised — the exact scalar-form shape the module already admits
  (Shape's `float aspectRatio; vec2 globalCoord;` pair, reduced to the
  `vec2` alone).
- **Write census: exactly one** — `main` body statement 0, normalized
  `279:5-279:16` (`globalCoord = gl_FragCoord.xy + tileOffset;`),
  unconditional, before every other statement. Stronger than Shape's
  dominance proof (write at body[1], first call at statement 4): here the
  write is the *first* statement of `main`, so write-before-read holds
  trivially on every path.
- **Read census: exactly two** — `main 281:15-281:26`
  (`vec2 st = globalCoord / fullResolution.y;`) and `diamonds 220:10-220:21`
  (`st = globalCoord / fullResolution.y;`). Freeze the census; note
  `diamonds`' reachability at `NOISE_TYPE=10` (it sits in the 19 unreachable
  functions — verify at implementation; the dominance argument does not
  depend on it).
- Emission: `Frame` with one `glsl::Vec2 globalCoord{}` member,
  value-initialised `[0,0]` (matches the JS factory initial — exact even
  though unobservable after the write); writer is `main` itself, so unlike
  Shape no `Frame&` writer parameter is needed — every helper that reads it
  (`diamonds`) takes `const Frame&`. The emitter crash measured in §4
  (uninitialized global declaration) is precisely the emission this module
  already knows how to produce.
- Slice row: a **three-companion carrier row** —
  `runtime_loop_bound_profile` + `mutable_global_frame_profile` +
  `scalar_uint_xor_profile` — plus the floatBitsToUint identity list, i.e.
  the normalMap `REQUIRED_COMPANION_PROFILES` pattern; every companion
  module's sibling-absent set needs the per-key carve (the ceil/XOR/glitch
  lesson, effects §4.5: *check every companion for its frozen FAP/sibling
  absent-set*).

## 7. Proof composition and oracle sketch (house discipline)

Per-program notes only where they differ from the standing pattern (§6 of
the handoff: RED/GREEN with value-checks-ahead-of-identity, delete-the-check
sweeps, visitation ledgers, foreign-carrier sweeps recording which neighbor
answers first, collision-chain ownership maps, historical reconstruction,
the full native matrix).

- **parallax**: RED boundaries already measured (§4 rung 0/1). Mutant
  satisfiability: `MARCH_STEPS` content is load-bearing (trips 32 → visible
  march steps) — a bound-value mutant (e.g. record frozen at 31) must be
  pixel-discriminable; verify before budgeting (normalMap §11/§12). The
  `textureLod` arm's mutant: swap lod-`0` literal for a nonzero literal at
  the frozen sites — the JS *ignores* lod, so such a mutant is
  **invariant** on the JS side; record as an invariance witness (the
  alias is the contract), do not budget it as discriminating. Claim
  boundary: `heightMap`'s second-sampler path is fully reachable; no
  defines strip code, so no write-only/unreachable caveats — the whole
  program is oracle-coverable.
- **lightLeak / mandelbrot**: the out-param mechanism's RED must include a
  call-site mutant where the caller reads the out value *before* the call
  (the `__out__` read-back is what makes ordering observable) and a mutant
  swapping out-param aliasing (`__out__` destructuring order). The df64
  chain in mandelbrot is straight-line double-float arithmetic — oracle
  cases should sweep `iterations` below/above `MAX_ITER` (the
  `min(iterations, MAX_ITER)` clamp at raw `381` is a real, reachable
  boundary; a mutant dropping the min must differ only on the
  `iterations > 500` arm — check satisfiability against the metadata
  maximum for `iterations` in the JS definition before budgeting).
  `log`'s numeric contract (narrowing points) is measured from the stdlib
  at implementation, not assumed.
- **synth/noise**: the four carriers' RED/GREEN are per-module; the
  program-level oracle should include an `octaves=8` boundary case (the
  runtime guard's rejection arm — `KernelBindingError` naming `octaves`,
  the tetra pattern) and `octaves` sweep 1..8 invariants. The jitter-block
  mutants ride the scalar-uint-xor module's existing patterns (per-key
  spans/hashes; the three XOR nodes are the program's own).
- **Median/typed-index programs**: out of scope until L/M exist.

**Claim boundaries where defines strip code** (write-only/unreachable
classes): classicNoisedeck/noise's typed-index sites are in unreachable
sRGB converters — if L is ever built and that program ported, the index
grammar's protection there is structural (identity locks), not
pixel-tested, exactly cellRefract §17's class; synth/noise's `diamonds`
read is in (verify) unreachable code — same class for the frame record's
read census.

## 8. What this investigation could not determine

- **The emitter-side lowering design for out/inout and bare calls.** The
  ladder proves gate closure with synthetic emissions; the reference ABI
  (C++ out-param references, call-site lvalues, the `__out__` value
  contract) is implementation-lane design work with its own numeric
  contract questions (which pooled-array writes narrow when).
- **Whether mandelbrot's `iterations` metadata maximum exceeds 500** (the
  clamp's discriminating arm depends on it) — read from the JS definition
  at implementation; not measured this session.
- **testPattern's `numDigits` bound rule shape** — enumerated (if-chain
  local) but not designed; whether it is a `_local_bound` widening or a
  per-key certificate is testPattern's own design pass, and it is blocked
  behind L regardless.
- **The bit-level fractal adapter-vs-GLSL question** (§2.8) — structural
  inspection cannot settle it; whoever resolves fractal's authority should
  re-run the oracle agent's comparison against the current snapshot.
- **dither's re-scoped cost** — this lane measured that a working,
  deterministic error-diffusion reference now exists; budgeting dither's
  actual port (const-composed bounds, pixel-derived loop bounds, the
  palette-table pile) is a separate investigation once the DEFECTS-FOUND
  correction is ratified.
- All figures are lane-measured (the effects §6 scope-note discipline): the
  CLEAN terminations, budget numbers, JS reproductions, and censuses were
  produced by this lane's probes against the pinned corpus and snapshot and
  have not been independently re-run by a second lane.
