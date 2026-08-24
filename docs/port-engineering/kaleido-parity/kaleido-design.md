# kaleido — the second mutable uninitialized global `float[9]` program

Design for porting `classicNoisedeck/kaleido:kaleido` as a typed row (the
slice after cellRefract's row 186 lands; exact ordinal computed at
insertion). Status: **DESIGN — frontend record landed PREPARED,
pre-integration**. The per-key record `mutable-global-nine-array-kaleido-v1`
is frozen in `tools/glslcpp/frontend/mutable_global_array_profile.py` with
its test classes green, but **no row lands in this lane**; integration is a
later slice with its own full gate cycle.

This document mirrors `cellrefract-parity/cellrefract-design.md` and inherits
its Amendments §§11-15 as binding lessons (native-census figures are read
from the live assertion, never carried forward; the emitter's bare-call
statement arm; the two hard-wired integration sites; literal-or-unary-minus
store values; the tile-crop non-identity — only the *method* transfers, never
the precedent). **Every figure below was MEASURED this session** against the
pinned corpus and the read-only JS authority by the same helpers the module
uses; none is transcribed from any design.

## 0. What this lane landed, and what it deliberately did not

Landed now (frontend only):

- The kaleido per-key record in
  `tools/glslcpp/frontend/mutable_global_array_profile.py` — held **PREPARED**,
  not registered (§5 explains the landed/prepared split and the measured
  `load_slice` coupling that forces it).
- 60 new kaleido tests in `tests/test_mutable_global_array.py` (five new
  classes: Surface 4, Admission 16, LockDeletion 35, Ledger 3, Vocabulary 2
  — the lock-deletion class's 35 methods are 29 `_delete_and_compare` tests
  plus the direct-scratch tests). The 89 cellRefract tests are
  byte-identical and green before and after.
- The frozen third-key *contents* for `fixed_array_in_parameter_proof.py`
  (§3.3), measured and recorded here but **not landed** — two measured
  conflicts make landing it now wrong (§3.4).

Not landed (integration slice): the row, the XOR row wiring, the
companion-carrier exception in the validator, the `load_slice` schema arm,
the fixed-array third key, the XOR module's absent-set carve-out, the
emitter's kaleido awareness, oracle, native, reconstruction.

## 1. Frozen authority

| Fact | Value (measured) |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Source | `…/sources/classicNoisedeck/kaleido/kaleido.glsl` |
| Raw bytes / SHA-256 | 27,567 / `3a155a9bf64f9e700dd66a77c4195df113d9e85228bde56b1cf410944aaeb8b9` |
| Normalized bytes / SHA-256 | 21,817 / `d31299ee69dd0c41965209860ef60a4ad2abf762229cc340383dce2646c6cc1d` |
| Defines (canonical, via `generate_typed_slice._defaults`) | `DIRECTION=2`, `KERNEL=0`, `LOOP_OFFSET=10`, `METRIC=0` — in that order |
| Whole-program SHA-256 | `bae48e72088ee01b07a1c8cfcba2398df87e2baf64284eebe750665e2aebc749` |
| Interface SHA-256 | `666586f65044abc1a147a7c3007f376fde3833c275f5f25bce9b6027b7eaa717` |
| Functions SHA-256 | `2ffb48e5f118844d675f9741ccbf7e831ce2f7cfe4609b24777ddb5fb67887ff` |
| Node census | 3,178 nodes / 179 assigns |
| Declarations | 17 (11 uniforms + `out fragColor` + five arrays) |
| Functions | 43 |
| Resources | uniforms `(inputTex, resolution, tileOffset, fullResolution, time, wrap, seed, speed, loopScale, kaleido, effectWidth)`; samplers `(inputTex)`; outputs `(fragColor)`; texture yes; derivatives no |
| Counted loop proof | `(1, 0, 1, 9, 0, True)` — one proved loop, entrypoint charge 0 |
| Call graph | 51 edges, digest `ded1fd4455f0f95030d330a330624aba6d3d7b507f959f4e149d8b8c5fd265be` |

The whole/interface fingerprints were computed with BOTH the array module's
helpers and `mutable_global_frame_profile.py`'s — they agree exactly (same
field tuples), and they also equal the values already frozen in
`scalar_uint_xor_profile.py`'s kaleido record (§3.1).

Live RED boundary chain, reproduced this session by per-program
`analyze_program` + `validate_capabilities` against the live slice:

| Carriers supplied | First rejection (measured) |
| --- | --- |
| none | `exact scalar uint XOR profile carrier required` |
| `scalar-uint-xor-v1` | `33:1: unsupported global declaration` |
| `scalar-uint-xor-v1` + the kaleido array carrier, kaleido registered (copy probe, §6) | `543:24: unsupported typed type float[9]` |

**The documented frontier is unchanged by this lane**: with the module as
landed (kaleido prepared, not registered), supplying the array carrier for
kaleido fails closed with `mutable-global array profile metadata mismatch`,
and the no-carrier / xor-only rows above are byte-identical to the
`REMAINING-EFFECTS.md` table.

### The five admitted declarations

Normalized lines 33-37, contiguous declaration indices 12-16, symbol ids
13-17, all `array` of `float` extent 9, all UNINITIALIZED, immediately after
the `fragColor` output at index 11:

| Index | Symbol id | Name | Span |
| ---: | ---: | --- | --- |
| 12 | 13 | `emboss` | 33:1-33:17 |
| 13 | 14 | `sharpen` | 34:1-34:18 |
| 14 | 15 | `blur` | 35:1-35:15 |
| 15 | 16 | `edge` | 36:1-36:15 |
| 16 | 17 | `edge2` | 37:1-37:16 |

Declaration/symbol node SHA-256s are frozen in the module record (generated
by the same `_sha`/`_span` helpers; not transcribed here — re-derive when
amending).

### Function inventory (load-bearing subset of the 43)

- `loadKernels` — id 126, `void`, **no parameters**, span 39:1-65:2, body
  exactly 45 sole-expression `expr` statements. The writer.
- `convolve` — id 119, span 543:1-576:2, 16 statements; parameters
  `(81 uv vec2, 82 kernel float[9], 83 divide bool)` — parameter 2 is
  `kernel`, whose type site is the recorded `543:24` rejection (the `f` of
  `float kernel[9]`; the same call-site family as cellRefract's `66:29`).
- `convolutionKernel` — id 118: **collapsed to `return color;`** by the
  frozen `KERNEL=0` (normalized lines 673-675).
- `main` — id 127, span 813:1-833:2, 11 statements; `loadKernels();` is the
  sole expression of top-level statement index 3 (span 818:5-818:19, call
  node 818:5-818:18); the `#if KERNEL != 0` block is stripped.
- Callers of `convolve` with whole local tables: `derivatives` (120),
  `sobel` (150), `outline` (132), `shadow` (146) — two `float[9]` tables
  each, 8 caller tables total. **`shadow`'s tables sit at statements 0 and
  10**, not 1 and 11 like the other three (and like all four of
  cellRefract's) — the generic declaration-searching caller-table helper
  already handles this; a frozen-index helper would not.

### Call graph and reachability (measured)

- **Reachable (30)**: `main`, `loadKernels`, `map`, `offset`, `circles`,
  `kaleidoscope`, `getMetric`, `periodicFunction`, `value`,
  `randomFromLatticeWithOffset`, `pcg`, `positiveModulo`, `constant`,
  `quadratic3`, `quadratic3x3Value`, `catmullRom3`, `catmullRom3x3Value`,
  `catmullRom4`, `catmullRom4x4Value`, `bicubicValue`, `blendBicubic`,
  `blendLinearOrCosine`, `simplexValue`, `sineNoise`, `rings`, `diamonds`,
  `mod289_2`, `mod289_3`, `permute3`, `shape`.
- **Unreachable (13)**: `convolutionKernel`, `convolve`, `derivatives`,
  `desaturate`, `hsv2rgb`, `outline`, `pixellate`, `posterize`, `prng`,
  `prng2`, `rgb2hsv`, `shadow`, `sobel`.

**A distinction cellRefract did not need, measured here:** the normalizer
substitutes define values into the `#if LOOP_OFFSET == N` chain of `offset`
but KEEPS the chain as constant-guarded `if` statements — normalized
`offset` opens with `if (10 == 10) { return circles(st, freq); } else if
(10 == 20) { … }` (normalized lines 715-722). The 30-function reachable set
above is therefore **structural**: `value`, the interpolation family, the
simplex/sine/rings/diamonds arms are structurally reachable through
never-taken constant guards. The **runtime-live** path at the frozen defines
is much smaller: `main → map, offset → circles`, `kaleidoscope → getMetric`,
`periodicFunction`, `loadKernels`, `texture`. In particular the XOR sites
(158-160, in `randomFromLatticeWithOffset`) are structurally reachable but
runtime-dead at `LOOP_OFFSET=10`. This distinction binds two later sections:
mutant budgeting (§7) and the assembly audit scope (§8), and it is the same
class of fact as Shapes' §13 conditional gate.

## 2. The read/write census verdict (the critical difference, measured)

**kaleido's arrays are WRITE-ONLY at its frozen defines — exactly like
cellRefract's.** The cellRefract design §3A's parenthetical — "(or `kaleido`,
whose reads live in reachable code)" — is **wrong** for the frozen defines,
and this section is the measured correction.

Method (the module's own walkers, over every function body AND every
declaration initializer):

- The whole program contains exactly **45 `id` references to symbols 13-17**.
- All 45 are the base of the index target of a plain `=` store inside
  `loadKernels` (statement indices 0-44, one store per statement).
- **Zero reads, zero whole-array bases, zero initializers** — the
  initializer census is empty, and the walk is what proves no read can hide
  in a global initializer.
- The store owners set is exactly `{(126, "loadKernels")}`; operators all
  `=`; indices per base exactly `0..8`.
- The **45 (base, index, value) triples are byte-identical to cellRefract's
  kernel tables** under the symbol-id shift 17-21 → 13-17 (frozen as a test).
  19 of the 45 values are `unary(-)` nodes wrapping a float literal
  (cellRefract Amendment 14 applies unchanged).

Why the readers are gone: kaleido's only readers of the five globals are the
`#if KERNEL == N` branches of `convolutionKernel` (`convolve(uv, blur, …)`,
`edge2`, `emboss`, `sharpen` as whole-array arguments) and `main`'s
`#if KERNEL != 0` block — both stripped at `KERNEL=0`. `convolve`, its four
callers, and `convolutionKernel` remain emitted-but-unreachable, exactly the
cellRefract shape.

**Consequence:** the record needs **no read census, no read-position or
dominance-of-reads locks, no loop-bound proof per read**. The write-only
census is frozen per key (`references: ()`) exactly as cellRefract froze
write-only-ness, and the module still carries no "reads allowed" switch. A
future kaleido row at `KERNEL != 0` — where the readers DO live — needs its
own record with its own read census; that fact is now measured, not assumed
in either direction.

## 3. JavaScript materialization (the authority)

Measured against the sibling `noisemaker-for-cpu` checkout (read-only),
factory `canonicalFactory9` in `src/effects/generated/canonical-kernels.js:3374`,
registered at line 36189 as `"classicNoisedeck/kaleido:kaleido": canonicalFactory9`.
The three CPU-file pins re-verified unchanged this session
(`canonical-kernels.js` `66adc01c…`, `catalog.js` `d8cf3122…`,
`glsl-runtime.js` `a20421c5…` — the cellrefract oracle generator's pins), so
the authority has not drifted since the cellRefract slice.

1. **The five globals are factory-scope plain JS arrays of doubles** —
   `canonical-kernels.js:3404-3408`, `var emboss = [0, 0, 0, 0, 0, 0, 0, 0, 0];`
   etc. **Not** `PooledFloat32Array`; allocated once per factory invocation,
   captured by closure, shared across pixels; immune to the `beginPixel`
   scratch-aliasing hazard. Same per-declaration materialization as
   cellRefract — and, per the normalMap lesson, decided per declaration,
   which is why it was re-measured rather than inherited.
2. **Numeric contract**: elements are doubles, never narrowed on read or
   write. All 45 constants are small integers exactly representable in
   binary32, so the double contract is structurally locked but not
   pixel-discriminable (the normalMap §12 "unfalsifiable contract" case —
   lock it structurally and say so).
3. **`loadKernels` is a real closure function** (`:3409-3455`) called once
   per pixel from `main` (`:4200`, `loadKernels();`), re-writing all 45
   elements before any possible read. The rewrite is idempotent; per-pixel
   re-execution is the observable contract; factory-scope persistence is
   unobservable; the port may value-initialize per pixel without divergence.
4. **Defines are runtime bindings** (`:3388-3391`): the JS retains
   `if (KERNEL != 0) { if (effectWidth != 0) { … } }` in `main` and the full
   `KERNEL == N` dispatch in `convolutionKernel`, dispatched at runtime. The
   corpus row pins `KERNEL=0`; the port's obligation is the normalized
   corpus semantics at those defines, with the JS oracle run at matching
   binding values — the same authority question Shapes and cellRefract
   resolved, with a `KERNEL=0` invariance control recording the axis (§7).
5. **`convolve`'s `kernel` parameter is by-reference, no `$runtime.copy`**
   (`:3819-3848`; `uv` IS copied, `kernel` is not). `kernel[i]` reads are
   un-narrowed doubles; `conv` accumulates in a `PooledFloat32Array` with
   per-store f32 rounding; `kernelWeight` is a bare double; the `offset`
   table is a plain JS array of nine pooled `vec2`s; whole-array call
   arguments pass the arrays directly (`convolve(uv, deriv_x, divide)`), and
   the four globals are passed the same way inside `convolutionKernel`'s
   runtime dispatch.
6. **Factory text pin**: `Function.prototype.toString` of `canonicalFactory9`
   is 32,701 bytes, SHA-256
   `4ab626fda5e91e7f89b93c9d863cda497b85d79239183499785c03607cce19a3`.
   Method cross-validated this session by reproducing cellRefract's frozen
   hash `329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3`
   from `canonicalFactory3` exactly — the same method B1 validated against
   refract's `b404a801…`.

## 4. Mechanism decomposition

| # | Mechanism | Status |
| --- | --- | --- |
| A | Mutable uninitialized global `float[9]` declaration admission (×5) | **prepared record landed** — `mutable-global-nine-array-kaleido-v1` |
| B | Non-`main` writer (`loadKernels`, 45 literal stores) | **covered by A** — same writer name, same `Frame&` emission shape, no delta from cellRefract |
| C | `float[9]` parameter + local literal tables + whole-array call args | **third key needed at integration; contents frozen in §4.3, not landed** (measured reasons in §4.4) |
| D | Scalar-uint-XOR carrier wiring | **already frozen and paid for** — verified, not rebuilt (§4.1) |
| E | Loop admission | **expected drop-path** — the single counted loop (convolve `0..<9`) carries a complete proof; program tuple `(1, 0, 1, 9, 0, True)`; no `runtime_loop_bound` carrier anticipated (confirm by RED probe at integration, as cellRefract's §3D was) |

### 4.1 The XOR carrier: already frozen, verified this session

`scalar_uint_xor_profile.py:84-114` carries complete kaleido locks — raw
27,567/`3a155a9b…`, normalized 21,817/`d31299ee…`, whole `bae48e72…`,
interface `666586f6…`, functions `2ffb48e5…`, defines
`(DIRECTION 2, KERNEL 0, LOOP_OFFSET 10, METRIC 0)`, owner
`randomFromLatticeWithOffset` (143), parent `157:20-161:6`, three sites
`158:10`/`159:10`/`160:10`, plus a 7-entry `float(uint)` census
(`102:31`, `107:12`, `107:38`, `165:19`, `167:9`, `168:9`, `169:9`).
**Verified by direct authentication this session: CLEAN, three nodes
returned.** Nothing here is rebuilt; the integration slice only wires the
row field.

### 4.2 What the landed cellRefract machinery already covers

The dict-keyed module needed no structural change for a second record — the
per-key `_LOCKS` pattern, per-key `_profile_fail`, value-checks-ahead-of-
identity ordering, literal-or-unary-minus extraction, and the visitation
ledger all carry over with per-key data. The writer emission contract is
unchanged: same `Kernel9`, same `Frame`/`frame`/`pixel`/value-init, same
`const Frame&` at ordinal 2 with `Frame&` on the writer alone, same writer
name `loadKernels`. The `wrap` uniform differs (GLSL `bool` vs cellRefract's
`int`) — an ABI-binding question for the oracle lane, not the array
mechanism.

### 4.3 The fixed-array third key: contents, measured

kaleido's convolve family is structurally identical to cellRefract's — the
nine-number whole-program census is **the same tuple**
`(1, 9, 146, 137, 126, 3, 129, 8, 8)` (array parameters, array declarations,
array expressions, identifier references, literal stores, induction reads,
index expressions, whole-array arguments, array calls), over 15 array ids
`{13,14,15,16,17, 82, 243, 249, 250, 274, 275, 332, 333, 362, 363}`:

- `convolve` id 119, body 16 statements; parameter record `(82, "kernel",
  "float[9]", "in")`, native ABI `const Kernel9&`, exactly 2
  induction-indexed reads per iteration — index-expression spans
  `564:25-564:34` and `567:25-567:34`; the `id` nodes are `564:25-564:31`
  and `567:25-567:31` (same sites; the record should freeze which node) —
  induction symbol 246, loop proof
  `(246, 0, 9, "<", "++", "literal", 9, 1, 1, 9, 0)`, loop at body[13].
- `convolve`'s `vec2 offset[9]` table: symbol 243, declaration at body[1],
  stores at body[2..10], components exactly cellRefract's
  `(-x,-y)…(x,y)` grid, one induction read.
- The 8 caller tables: `derivatives` (120; deriv_x 249 @1, deriv_y 250 @11;
  calls @21/@22), `sobel` (150; 362/363 @1/@11), `outline` (132; 274/275),
  `shadow` (146; sobel_x 332 @**0**, sobel_y 333 @**10**) — values exactly
  cellRefract's deriv/sobel tables.
- Binding signature (11 uniforms): `inputTex:sampler2D, resolution:vec2,
  tileOffset:vec2, fullResolution:vec2, time:float, wrap:bool, seed:int,
  speed:float, loopScale:float, kaleido:float, effectWidth:float`.
- FAP-shaped fingerprints for the future record: interface `666586f6…`
  (equals the array module's — same formula), typed-IR (functions)
  `2ffb48e5…`, FAP whole-program `2590b36ad768dd1217743dac63486619562f0d3f2c90d9aa4cb06c0b2ca68e68`
  (the fixed-array formula includes the two sibling-proof fields), canonical
  factory `4ab626fd…` (§3.6).

### 4.4 Why the third key is NOT landed in this lane (two measured conflicts)

1. **The auto-attach census test is frozen to two keys.**
   `tests/test_typed_generator.py:4999`
   (`test_cellrefract_convolve_auto_attach_census_over_whole_corpus`) walks
   all 212 corpus programs and asserts the attached set is exactly
   `(cellRefract, refract)`. A correct kaleido record attaches a third proof
   and reddens a test in B2's file — which this lane must not touch, and
   which is mid-integration for row 186. The same slice that wires the row
   moves that census to exactly three keys with kaleido as the named
   accepted witness.
2. **The XOR module's frozen absent-set rejects the proof.** Measured this
   session: `authenticate_scalar_uint_xor(kaleido, …, "scalar-uint-xor-v1")`
   is CLEAN with no sibling proof attached, and raises
   `scalar-uint-xor-v1: unrelated proof carrier is not absent` the moment
   `fixed_array_in_parameter_proof` is non-None
   (`scalar_uint_xor_profile.py:269-272` names it in `_OPTIONAL_PROOF_FIELDS`,
   checked at `:408-410`). kaleido is the first program that would carry
   BOTH the XOR carrier and a fixed-array proof — landing the record without
   a per-key carve-out of that absent-set would flip the live frontier probe
   for kaleido from `33:1 unsupported global declaration` to the XOR
   rejection, and break the XOR carrier at validation. The carve-out (kaleido
   alone; the other five XOR keys keep the stricter set) is an edit to a
   frozen shared module and needs RED tests for all six XOR keys —
   integration-slice work, in the same slice as the third key.

### 4.5 What integration must wire (not this lane)

1. **Register the key**: move `KALEIDO_KEY` from `PREPARED_KEYS` into `KEYS`/
   `PROFILES`/`MUTABLE_GLOBAL_ARRAY_KEYS` and merge `PREPARED_ROW_FIELDS`
   into `ALLOWED_ROW_FIELDS` — a one-line, reviewable move the module's
   landed/prepared split exists to make safe (§5).
2. **The companion-carrier exception**: `generate_typed_slice.py:3158`'s
   mutable-array collision list rejects `scalar_uint_xor_profile is not
   None`; kaleido's row carries BOTH. Follow the normalMap
   `REQUIRED_COMPANION_PROFILES` pattern (`:3203-3217`): the closure names
   its required companions, the collision list reads them, fail-closed for
   unmapped fields. The row-schema half in `load_slice` and
   `_MUTABLE_GLOBAL_ARRAY_DEFINES` (`:611`; per-key defines) get the same
   treatment — and the defines dict has a **second** consumption site:
   `load_slice`'s `expected_defines` entry
   `MUTABLE_GLOBAL_ARRAY_CELLREFRACT_KEY: _MUTABLE_GLOBAL_ARRAY_DEFINES` at
   `generate_typed_slice.py:1456` (inside `load_slice`), which also becomes
   per-key; missing it fails closed with a schema-drift error.
3. **The fixed-array third key** (§4.3) + **the XOR absent-set carve-out**
   (§4.4.2) + **the auto-attach census extension** (§4.4.1).
4. **The emitter's bare-call arm**: `main`'s `loadKernels();` is the same
   bare `expr`-wrapped `call` statement shape cellRefract needed (its
   Amendment 12). If B2's identity-gated arm is keyed to the exact frozen
   cellRefract call node, it needs kaleido's node (statement 3, span
   `818:5-818:18`, sha `0ad7a0ba17ae32bc5ccfd5f83deff877de66aff62864ae278a350893ce63c59a`)
   added by identity — no generic void-call admission.
5. Deeper validator gates behind globals admission are probed only to
   `543:24` (§6); expect the fixed-array family rejections there, and census
   anything further as amendments.

## 5. The landed/prepared split, and why it is forced

Measured this session: `load_slice`'s census
(`generate_typed_slice.py:1391-1396`) enforces that the slice's
array-carrier rows equal **exactly** the module's registered key census —
registering kaleido in `KEYS` without its row raises
`typed slice mutable-global array profile drift` and reddens the live schema
tests (observed, then fixed). The module therefore now exposes:

- `KEYS` / `PROFILES` / `MUTABLE_GLOBAL_ARRAY_KEYS` / `ALLOWED_ROW_FIELDS` —
  the **landed** registry (cellRefract only), which `load_slice` enforces;
- `PREPARED_KEYS` / `PREPARED_ROW_FIELDS` — kaleido's complete, frozen,
  authenticatable record and row contract, held one step short of
  registration; `authenticate_mutable_global_array` consults the record set
  (so the kaleido tests exercise the real authentication path), while the
  schema census and the validator's carrier gates stay untouched.

This is why the existing cellRefract tests remain byte-identical (an earlier
draft of this lane registered the key and had to extend two census
assertions; the split made those edits unnecessary and they were reverted).

### Slice row (projected — nothing lands now)

```json
{
  "defines": {"DIRECTION": 2, "KERNEL": 0, "LOOP_OFFSET": 10, "METRIC": 0},
  "mutable_global_array_profile": "mutable-global-nine-array-kaleido-v1",
  "program_key": "classicNoisedeck/kaleido:kaleido",
  "scalar_uint_xor_profile": "scalar-uint-xor-v1"
}
```

Sorted neighbors (measured against the corpus manifest and the live slice):
`classicNoisedeck/glitch:glitch` < **kaleido** < `classicNoisedeck/
lensDistortion:lensDistortion`. Projected censuses (typed rows, catalog
entries, absent keys, genuinely unported, typed-list SHA-256, the four
artifact hashes, the native `factories.size()` assertion) are **computed
from the live generator at integration** — never projected by hand, per the
cellRefract §11 lesson; read the live assertion before moving it.

## 6. Proof composition (RED/GREEN)

What this lane already proved, by measurement:

- The record authenticates the exact pinned program: five declarations by
  object identity at indices 12-16, all 30+ shared locks firing their own
  messages under mutation, delete-the-check sweep tabulated in §9.
- Driving the validator in a copy with the key registered in-process and the
  XOR gate suppressed (the integration edits simulated, never landed): the
  array carrier authenticates **through the real gate sequence** and the
  five globals are admitted; the next rejection is exactly
  `543:24: unsupported typed type float[9]` — the convolve parameter —
  confirming both the record's validator compatibility and the recorded
  next blocker behind globals.

Integration RED sequence (write tests first, watch each fail for the
intended reason): row absent → the §1 chain; row present, carriers absent →
`exact mutable-global array profile carrier required` and the XOR twin;
foreign carriers (every sibling profile string, both authorities — sweep all
and record which neighbours answer first, per the collision-chain trap);
per-lock mutations mirroring the landed kaleido test classes through
`validate_capabilities` and `render_typed_cpp`; the two-carrier collision
RED (supplying the XOR companion on the row must be REQUIRED, not merely
allowed — the negative is a row without it); the XOR absent-set carve-out
RED for all six XOR keys; the auto-attach census moving two→three with
kaleido the named witness; the emitter bare-call arm RED for kaleido's exact
call node; delete-the-check sweep for every NEW predicate the integration
adds.

## 7. Oracle design (sketch; the oracle lane owns the real design)

`kaleido_oracle_generator.mjs` in this directory, in the shape/
normalMap/cellrefract pattern: `--cpu-root` required and realpath'd; refuse
the live checkout, containment either way, inside-C++-repo roots; per-file
SHA-256 import closure; the six pinned CPU-file hashes; factory identity
`kernelFactories.get(key) === canonicalKernelFactories[key]`; factory name
exactly `canonicalFactory9`; `Function.prototype.toString` SHA-256 frozen at
`4ab626fd…`; both adapter tables censused (`check_corpus._ADAPTERS` must not
own the key); GLSL bytes/SHA pinned; stable path placeholder,
absolute-path rejection.

Cases (each full float32-word + RGBA8 arrays, one materializer include):

- wedge sweeps over the `kaleido` (sides) binding — the observable axis of
  `kaleidoscope`'s `mod`/`atan` math, distinct sides values so the wedge
  symmetry actually differs between cases.
- `wrap` bool arms (with/without `lf = floor(lf)`), distinct
  `loopScale`/`speed` so `t`, `blendy` and the sampling warp differ.
- `time`/`speed` axes driving `periodicFunction` and the `map(abs(speed),…)`
  blend.
- **`KERNEL=0` invariance control**: the JS `KERNEL` binding is runtime; run
  one case at `KERNEL=0` and record the axis with a liveness census (the
  port has no `KERNEL` binding at all) — the Shapes §11 / cellRefract §7
  pattern of asserting the *absence* of a divergence channel.
- No tile-crop case: cellRefract §15 measured the crop identity
  program-shaped, not universal — kaleido samples a single input texture
  through a world-aligned warp (like cellRefract's tile route), so any crop
  claim must be re-derived, not cited. Budget nothing here until probed.

**Mutants — satisfiability and distinguishability checked before budgeting**
(normalMap §11/§12 lessons): the five tables are **write-only at the frozen
defines, so no table mutant is pixel-discriminable**; their protection is
structural (the frozen 45 triples) and the acceptance record must say so
plainly. Because `LOOP_OFFSET=10` keeps `offset`'s dispatch as constant
`if (10 == N)` guards (§1), the **runtime-live** pixel path is only
`main → map/offset → circles, kaleidoscope → getMetric, periodicFunction,
loadKernels, texture`: mutants in the structurally-reachable but
runtime-dead family (`value`, `pcg`, the XOR sites, the interpolation arms)
are expected **invariant** — candidates, not budgeted mutants, and their
invariance is itself a witness that the guards folded the same way in JS
and the port. A promising *discriminating* class (verify, don't assume):
flipping a constant guard (`10 == 10` → `10 == 20`) changes the runtime-taken
offset arm and should be pixel-discriminable; `getMetric`'s non-euclidean
arms are `#if`-stripped at `METRIC=0`, so metric-arm mutants are
structurally absent — non-satisfiable, do not budget.

ABI: 11 bindings — `inputTex` texture; `wrap` **bool** (verify the binding
variant against `glsl-runtime.js`; cellRefract's was int32), `seed` int;
`time`, `speed`, `loopScale`, `kaleido`, `effectWidth` via `get_number`;
`resolution`/`tileOffset`/`fullResolution` `Vec2`. Omit-each and
wrong-variant-each with `KernelBindingError` naming the binding; unrelated
extras ignored; caller immutability; exact alpha; determinism; independent
storage.

## 8. Verification gates (integration slice)

The standing matrix unchanged from the handoff: four generator gates; focused
then full Python; native Debug/Release/ASan+UBSan; ctest 1/1; assembly audit
ARM64+x86_64 with demangled symbols; historical reconstruction (remove only
kaleido from a deep-copied live spec, regenerate in memory, recover the four
pre-kaleido artifact hashes; sanity-check the splitter on the unchanged pair
first); storage manifest/cleanup with one owned run root.

Assembly notes specific to this slice: at the frozen defines clang will
constant-fold the `if (10 == N)` guards and DCE the dead arms, so the
**executed** pixel scope is the small runtime-live set of §1 — audit that
set, and record the gate **conditional** on the frozen `LOOP_OFFSET` (the
Shapes §13 trap: a different define value puts jump-table dispatch in the
pixel path). The 30-function structural set is emitted source; record its
instruction counts but scope the no-indirect-branch/no-fused-FP/no-allocation
claims to executed scope, and prove fused-FP absence TU-wide. The `Frame`
is stack-only; `loadKernels`' 45 stores inline into `pixel`. Recognize the
standing `noexcept`/terminate-pad condition rather than investigating it.

## 9. What this lane's own gates were (2026-08-16/17)

- `tests/test_mutable_global_array.py`: **89 cellRefract tests + 56 subtests
  green before and after, byte-identical**; 60 new kaleido tests; file total
  149 passed / 80 subtests.
- TDD: the kaleido classes were written first and confirmed RED (70 failed
  at the first run) before the record was implemented.
- **Delete-the-check sweep** (scratch copy of `tools/` + `tests/`, one
  source-level deletion at a time, restored and re-verified after each):

| Deleted check | Named red test(s) | Result |
| --- | --- | --- |
| `PREPARED_ROW_FIELDS.get(key)` fallback in `allowed_row_fields` | `KaleidoMutableGlobalArraySurfaceTests::test_kaleido_row_field_allowlist_names_the_required_xor_companion` | RED (1) |
| authenticatable membership `_LOCKS` → landed-only `MUTABLE_GLOBAL_ARRAY_KEYS` | every record-consuming kaleido test (admission + deletion classes) | RED (18) |
| per-key `lock["profile"]` ledger prefix → module-global default | `KaleidoMutableGlobalArrayLedgerTests::test_the_kaleido_ledger_failure_names_the_kaleido_profile` | RED (1) |
| `_write_only_census_holds` body → always-True (shared predicate) | kaleido **and** cellRefract `test_write_only_census_lock`; cellRefract's three `test_no_indirect_write_lock_catches_*` (their asserted second-line message vanishes) | RED (5) |
| the kaleido `_LOCKS` record itself | 28 kaleido tests (all that consult the record) | RED |

  The 35 in-suite `_scratch` deletion tests additionally prove every shared
  predicate load-bearing **for the kaleido record's data** at runtime. A
  first attempt at the fourth row appended `return True` *after* the real
  return — a no-op that left the suite green; the sweep's value is exactly
  that it caught the fake deletion, and the corrected replacement-of-body
  reddened as required. No new or-chain sub-clauses were added, so no
  pair-deletion discipline was needed; no deletion left the suite green.
- Copy probes: the §1 boundary chain; the registered+admitted run to
  `543:24`; the XOR-module interaction (§4.4.2). All in
  `$RUN_ROOT/workers/D`, restored after each mutation.

## 10. Risks and expected discoveries

- **Deeper validator gates past `543:24` are unprobed** (the copy probe
  stopped at the fixed-array boundary by design — probing past it would
  have required implementing the third key). Expect the fixed-array family
  rejections (parameter, eight caller tables, whole-array arguments,
  indexed-write audit) and census anything beyond as amendments, per the
  cellRefract §9 rule: each discovery is an amendment unless it demands a
  new capability, then stop and re-review.
- **Two frozen shared modules must change at integration** — the XOR
  absent-set carve-out and the validator collision list — and one frozen
  census test moves two→three. Each is a widening needing a named accepted
  witness and a new rejection at the new boundary; sweep all six XOR keys
  and record the collision-chain ownership map rather than claiming it from
  one sibling probe.
- **Structural reachability ≠ runtime liveness** (§1) — budget mutants and
  assembly scope from the runtime-live set; record the conditional-gate
  precondition.
- `wrap` is a **bool** uniform — the one ABI difference from cellRefract;
  the oracle lane must pin the binding variant against the runtime before
  writing omit-each cases.
- `shadow`'s caller tables sit at statements 0/10, not 1/11 — any
  frozen-index helper copied from the other three callers fails only on
  shadow; the generic declaration-search helper is the correct reuse.
- The `Symbol` span self-absorption trap, the global-initializer census
  blind spot (structurally n/a — the initializer census is empty and
  walked), and the collision-chain unreachability trap all apply; the landed
  test classes embed the countermeasures (value checks ahead of identity;
  refreeze only coarse hashes; per-lock messages asserted absent from
  coarse failures).

## 11. Ownership

- **This lane (D)**: `tools/glslcpp/frontend/mutable_global_array_profile.py`
  (kaleido record, prepared), `tests/test_mutable_global_array.py`
  (kaleido classes), this design document.
- **Integration slice (later)**: `generate_typed_slice.py`, `emit_typed_cpp.py`,
  `typed_slice.json`, the fixed-array third key + its tests, the XOR-module
  carve-out + its tests, `tests/test_typed_generator.py` (row schema,
  collision census, auto-attach census two→three), generated artifacts,
  oracle (`kaleido_oracle_generator.mjs`, oracles JSON, include +
  materializer), native (`tests/test_generated_kernels.cpp` census), the
  historical reconstruction.
- **Binding constraint**: no row lands in this lane; integration is a later
  slice with its own full gate cycle.

### Independent review (2026-08-17)

Independent design review (frozen record:
`docs/port-engineering/prepared-designs-review-kaleido-varying-effects.md`)
returned verdict **GO** with three Minor findings. The corrections were
applied in place above — these tables freeze at implementation, and nothing
had landed from them yet:

1. **Test-count bookkeeping (§0, §9).** The lock-deletion class has 35 test
   methods (29 via `_delete_and_compare` plus the direct-scratch tests), not
   33; §0's "three new admission/surface classes" is five classes — Surface
   4, Admission 16, LockDeletion 35, Ledger 3, Vocabulary 2 (= the 60-test
   total). Counts corrected.
2. **A second `_MUTABLE_GLOBAL_ARRAY_DEFINES` consumption site (§4.5).**
   The `expected_defines` entry `MUTABLE_GLOBAL_ARRAY_CELLREFRACT_KEY:
   _MUTABLE_GLOBAL_ARRAY_DEFINES` at `generate_typed_slice.py:1456` (inside
   `load_slice`) also becomes per-key; missing it fails closed with a
   schema-drift error (the doc already cited the `:1391-1396` census).
   Added to the integration list.
3. **The convolve read spans (§4.3).** `564:25-564:34` / `567:25-567:34`
   are the index-expression spans; the `id` nodes are `564:25-564:31` /
   `567:25-567:31` (same sites; the record should freeze which node).
   Labeled above.
