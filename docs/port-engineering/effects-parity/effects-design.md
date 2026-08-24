# effects — the third mutable uninitialized global `float[9]` program, plus `mat4`

Design for porting `classicNoisedeck/effects:effects` as a typed row (the row
ordinal is computed at insertion; kaleido's integration slice is queued ahead
of it — §13). Status: **DESIGN — pre-implementation, prepared by the effects
lane (2026-08-16/17)**. Nothing lands in this lane; this document freezes the
measured facts and the mechanism decomposition the implementation slice needs.

This document mirrors `cellrefract-parity/cellrefract-design.md` and inherits
its Amendments §§11-17 and `kaleido-parity/kaleido-design.md` as binding
lessons: native-census figures are read from the live assertion, never carried
forward by arithmetic; the emitter is an independent authority with its own
grammar (§12); rvalue vec compound assigns lower through the corrected §17
assign form; literal-or-unary-minus store values (§14); the tile-crop identity
is program-shaped and only the *method* transfers (§15); write-only-ness is
measured per key, never assumed in either direction (§16); every member of
this family carries unreachable-but-emitted code whose grammar must still
close (§17). **Every figure below was MEASURED this session** against the
pinned corpus, the read-only JS authority, and the live tree's frontend
modules (imported read-only; all destructive probes ran in an rsync'd copy
under the shared run root). None is transcribed from any design.

## 0. Summary of the load-bearing verdicts

1. **The arrays: SEVEN, not five.** `effects` declares `emboss`, `sharpen`,
   `blur`, `edge`, `edge2` — byte-identical tables to cellRefract's/kaleido's
   — **plus `edge3` and `sharpenBlur`**, two tables the family has not seen.
   63 stores, all in `loadKernels`.
2. **Read census: WRITE-ONLY at the frozen defines** (§2) — the family norm
   (cellRefract §16), measured here, not inherited: 63 `id` refs to the seven
   symbols program-wide, every one a literal-index store base inside
   `loadKernels`, zero reads, zero whole-array bases, zero initializers.
3. **MAT4 verdict: the carrier does not cover effects; the lowering machinery
   does, verbatim.** The frozen `glitch-mat4-chain-v1` module cannot
   authenticate effects (hard key check, whole-program locks, empty-defines
   lock, glitch-only splat lock), but its 14-node bicubic closure is
   **structurally identical** to effects' (§4), and the emitter's real mat4
   arms — driven this session over effects' own nodes through the genuine
   code path — produced the exact required lowering. What is new is per-key
   authorization at both authorities, not new lowering.
4. **Both blocker ladders terminate at CLEAN.** Validator: 10 measured
   rejection rungs, the last a `45 → 63` store-ledger widening. Emitter: 4
   measured rejection rungs, then CLEAN — no §12/§17-class grammar
   discovery remains: the two `return color *= dist;` sites and the bare
   `loadKernels();` call lower through the already-corrected arms. The
   ladder behind effects is fully enumerated; there is no unknown mechanism
   behind the enumerated ones (§6).
5. **Order: after kaleido's integration, before the varying bucket** (§13).

## 1. Frozen authority

| Fact | Value (measured) |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Source | `…/sources/classicNoisedeck/effects/effects.glsl` |
| Raw bytes / SHA-256 | 21,087 / `e3b742be53b6b1b0dd5e089a805ff02a931cd14643d0a0abe376bd8044e8ec6c` |
| Normalized bytes / SHA-256 | 15,773 / `cce2f30177586f4cdabab1e1741a99d1470f49db79c60dc20df9ddbcac9bdfda` |
| Defines (canonical, via `generate_typed_slice._defaults`) | `EFFECT=0`, `FLIP=0` |
| Whole-program SHA-256 (family helper formula) | `db85c4d2cafed8c07bc03d3e203ec83d099575ade15b5b452a9eeb58bb4940d1` |
| Interface SHA-256 | `feeb85a578bad5296e9c345401f7f1a6055da9aa6f5f476c346137f53cdeef52` |
| Functions SHA-256 | `d06fd4218bd7513a5aecd343bc3bb9d83dfb6b8fba011626fd5bb80707d67579` |
| Declarations SHA-256 | `d70dc9c99d2aa5a1546b8eb5a6f15b7bb8d0db2cc86cc7a51ba37643e3930a2a` |
| Node census | 2,638 nodes / 235 assigns |
| Declarations | 21 (13 uniforms + `out fragColor` + **seven arrays**) |
| Functions | 28, ids 65-92 |
| Resources | uniforms `(inputTex, resolution, tileOffset, fullResolution, renderScale, time, effectAmt, scaleAmt, rotation, offsetX, offsetY, intensity, saturation)`; samplers `(inputTex)`; outputs `(fragColor)`; texture yes; derivatives no |
| Counted loop proof | `(4, 0, 2, 48, 0, True)` — 4 proved loops, 0 unproved, effective depth 2, lexical product 48, entrypoint charge 0 (convolve `0..<9`; bloom's nested `-4..4`/`-3..3`; zoomBlur's float-indexed `0.0..<=40.0` — all counted) |
| Call graph | 30 edges, digest `cb421a62eb9d14a121e746b6bffea51e7c188db10230a95f77349bbb2ef2c3da` |

The whole/interface fingerprints were computed with the family helper
formula (`program.key, source, raw_source, declarations, functions, …`), the
same one `mutable_global_frame_profile.py`, the array module, and the glitch
module all share.

Live RED boundary, reproduced this session by per-program `analyze_program` +
`validate_capabilities` against the live slice: `31:1: unsupported global
declaration` — the `float emboss[9];` line, exactly the census
`REMAINING-EFFECTS.md` records. The pre-normalized source documents EFFECT and
FLIP as compile-time injected defines (`effects.glsl:12-24`, "definition.js
`globals.effect.define` / `globals.flip.define`").

### The seven admitted declarations

Normalized lines 31-37, contiguous declaration indices 14-20, symbol ids
15-21, all `array` of `float` extent 9, all UNINITIALIZED, immediately after
the `fragColor` output at index 13:

| Index | Symbol id | Name | Span |
| ---: | ---: | --- | --- |
| 14 | 15 | `emboss` | 31:1-31:17 |
| 15 | 16 | `sharpen` | 32:1-32:18 |
| 16 | 17 | `blur` | 33:1-33:15 |
| 17 | 18 | `edge` | 34:1-34:15 |
| 18 | 19 | `edge2` | 35:1-35:16 |
| 19 | 20 | `edge3` | 36:1-36:16 |
| 20 | 21 | `sharpenBlur` | 37:1-37:22 |

Declaration/symbol node SHA-256s are frozen in the module record at
implementation (generated by the module's `_sha`/`_span` helpers; not
transcribed here — re-derive when amending).

### Function inventory (load-bearing subset of the 28)

- `loadKernels` — id 75, `void`, **no parameters**, span 41:1-77:2, body
  exactly 63 sole-expression `expr` statements. The writer.
- `convolve` — id 70, span 234:1-267:2, 16 statements; parameters
  `(41 uv vec2, 42 kernel float[9], 43 divide bool)` — parameter 2's type
  site is the `234:24` third rung (§6), the same call-site family as
  cellRefract's `66:29` and kaleido's `543:24`.
- `convolutionEffect` — id 69, span 360:1-362:2: **collapsed to
  `return color;`** by the frozen `EFFECT=0`. This one collapse is what makes
  all seven arrays write-only (§2) and removes every whole-array reader.
- `bicubic` — id 65, span 372:1-404:2, 31 statements: **the mat4 host**
  (§4), and structurally **unreachable** (no caller anywhere in the
  normalized program — `f` is called only by `bicubic` itself).
- `main` — id 76, span 551:1-597:2, 23 statements; `loadKernels();` is the
  sole expression of top-level statement **15** (span 583:5-583:19, call
  node 583:5-583:18); the `#if EFFECT != 0` and `#if FLIP == N` blocks are
  stripped.
- Callers of `convolve` with whole local tables: `derivatives` (71; deriv_x
  157 @1, deriv_y 158 @11; args 283:15/284:15), `sobel` (90; 210/211 @1/@11),
  `outline` (79; 179/180 @1/@11), `shadow` (89; sobel_x 202 @**0**, sobel_y
  203 @**10**) — 8 caller tables total. **`shadow`'s tables sit at statements
  0 and 10**, kaleido's exact quirk; the generic declaration-searching
  caller-table helper handles it, a frozen-index helper copied from the other
  three would not.
- The two §17 sites: `derivatives` and `sobel` end with `return color *=
  dist;` (raw 300/320; normalized return spans inside 269:1-287:2 and
  289:1-307:2) — exactly the two rvalue compound assigns the corrected §17
  arm lowers.

### Call graph and reachability (measured)

- **Reachable (8)**: `main`, `loadKernels`, `map`, `offsets`,
  `periodicFunction`, `rotate2D`, `brightnessContrast`, `saturate`.
- **Unreachable (20)**: `bicubic`, `bloom`, `cga`, `convolutionEffect`,
  `convolve`, `derivatives`, `desaturate`, `f`, `hsv2rgb`, `outline`, `pcg`,
  `pixellate`, `posterize`, `prng`, `random`, `rgb2hsv`, `shadow`, `sobel`,
  `subpixel`, `zoomBlur`.

The runtime-live pixel path at the frozen defines is exactly the reachable
eight (there are no retained constant-guard dispatch chains of kaleido's
`LOOP_OFFSET` kind here — the normalizer strips the `#if`/`#elif` trees
outright). Everything mat4, everything convolution, and all four
effect-leaf families (`pixellate`/`cga`/`subpixel`/`bloom`/`zoomBlur`) are
emitted-but-dead. The `ceil` calls in `main` (statements 10/11) are the one
new *reachable* grammar element this program adds to the family.

## 2. The read/write census verdict (measured)

**effects' seven arrays are WRITE-ONLY at its frozen defines** — the third
consecutive member of the family to measure so (cellRefract §1, kaleido §2).
Method: the module's own walkers over every function body AND every
declaration initializer.

- The whole program contains exactly **63 `id` references to symbols 15-21**;
  **zero** occur in any global initializer (the initializer census is empty
  and walked — the global-initializer blind spot is structurally n/a).
- All 63 are the base of the index target of a plain `=` store inside
  `loadKernels` (statement indices 0-62, one store per statement; body shape
  census `('expr', 1, 0)` × 63).
- Operators all `=`; indices per base exactly `0..8`, all int literals;
  values all literal-or-unary-minus-of-float-literal (§14 applies; **31** of
  the 63 are `unary(-)` nodes). The 63 `(base, index, value)` triples:
  - `emboss`, `sharpen`, `blur`, `edge`, `edge2` — **byte-identical to
    cellRefract's frozen 45 triples** (verified value-for-value this session).
  - `edge3` = `(-0.875, -0.75, -0.875, -0.75, 5.0, -0.75, -0.875, -0.75,
    -0.875)` and `sharpenBlur` = `(-2, 2, -2, 2, 1, 2, -2, 2, -2)` — new;
    every value is still exactly representable in binary32 (`0.875 = 7·2⁻³`,
    `0.75 = 3·2⁻²`), so the plain-Number-double structural-lock argument
    carries over unbroken.
- **Zero reads, zero whole-array bases, zero non-`=` writes** anywhere.

Why the readers are gone: the only whole-array readers of the seven globals
are `convolutionEffect`'s `#if EFFECT == N` branches (`convolve(uv, blur,
…)`, `edge2`, `emboss`, `sharpen`, `edge3` at 301, `sharpenBlur` at 300) —
all stripped at `EFFECT=0`, leaving the collapsed `return color;`. `edge`
is the family's first table with **no reader in any branch of the raw
source** (a truly dead kernel). Consequence, same as the family: **no read
census, no read-position/dominance-of-reads locks, no table mutant is
pixel-discriminable** (§11); the write-only census is frozen per key with
`references: ()`, and the module still carries no "reads allowed" switch.
A future effects row at some `EFFECT != 0` — where readers DO live and,
unlike kaleido, are *reachable through main's runtime `effectAmt` gate* —
needs its own record with its own read census.

## 3. JavaScript materialization (the authority)

Measured against the sibling `noisemaker-for-cpu` checkout (read-only),
factory `canonicalFactory7` in
`src/effects/generated/canonical-kernels.js:2448`, registered at line 36187
as `"classicNoisedeck/effects:effects": canonicalFactory7`. The three
CPU-file pins re-verified unchanged this session (`canonical-kernels.js`
1,713,290 bytes `66adc01c…`, `catalog.js` 733 bytes `d8cf3122…`,
`glsl-runtime.js` 21,331 bytes `a20421c5…` — the cellrefract/kaleido oracle
pins), so the authority has not drifted. `canonicalAdapterFactories` does
not own the key (imported and checked, not read from a doc).

1. **The seven globals are factory-scope plain JS arrays of doubles** —
   `canonical-kernels.js:2474-2480`, `var emboss = [0, 0, 0, 0, 0, 0, 0, 0,
   0];` … `var sharpenBlur = […]`. **Not** `PooledFloat32Array`; allocated
   once per factory invocation, captured by closure, shared across pixels;
   immune to the `beginPixel` scratch-aliasing hazard. Same per-declaration
   materialization as cellRefract/kaleido — re-measured, not inherited.
2. **Numeric contract**: elements are doubles, never narrowed on read or
   write. All 63 constants are exactly representable in binary32, so the
   double contract is structurally locked but not pixel-discriminable
   (normalMap §12's "unfalsifiable contract" — lock structurally, say so).
3. **`loadKernels` is a real closure function** (`:2481-2547`) called once
   per pixel from `main` (`:3156`, `loadKernels();`), re-writing all 63
   elements before any possible read. Rewrite idempotent; factory-scope
   persistence unobservable; the port may value-initialize per pixel.
4. **`convolve`'s `kernel` parameter is by-reference, no `$runtime.copy`**
   (`:2685`); `kernel[i]` reads are un-narrowed doubles; `conv` accumulates
   in a `PooledFloat32Array` with per-store f32 rounding; `kernelWeight` a
   bare double; the `offset` table a plain JS array of nine pooled `vec2`s;
   the four whole-array call sites inside `convolutionEffect`'s runtime
   dispatch pass the globals directly. The caller tables are plain arrays
   with literal stores — the family shape, third instance.
5. **Defines are runtime bindings** (`:2457-2458`): the JS retains the full
   `FLIP == N` chain, the `EFFECT != 0` / `effectAmt != 0` gates and every
   `EFFECT == N` branch, dispatched at runtime. The corpus row pins
   `EFFECT=0, FLIP=0`; the port's obligation is the normalized corpus
   semantics at those defines, with the JS oracle run at matching binding
   values — the authority question Shapes/cellRefract/kaleido resolved, with
   an invariance control recording the axis (§11).
6. **Factory text pin**: `Function.prototype.toString` of `canonicalFactory7`
   is 28,789 bytes, SHA-256
   `ebf43ff45f4a3568854da02b41baf6b1a25efd2bc5bbf2d8cf78f0a11e3dd81a`.
   Method cross-validated this session by reproducing cellRefract's frozen
   `329d54732a…` (canonicalFactory3) and kaleido's frozen `4ab626fd…`
   (canonicalFactory9) exactly.
7. **mat4 materialization** — see §4.2; it is *pooled*, not plain Number,
   the family's first non-plain-array global-shaped materialization (though
   these are function locals, not globals).

## 4. The MAT4 decomposition (the core)

### 4.1 Every mat4 use site in the normalized program

Measured with the glitch collector's own predicate (mat4-typed node OR
`vec4`-typed `*` binary whose children are `("vec4","mat4")`), over every
function: **14 nodes, every one inside `bicubic` (id 65)** — statement paths
22-25 and 30:

| # | Path | Span | Kind | Type | Op | Symbol | Role |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | (22, e0) | 395:10-395:114 | declaration | mat4 | — | 116 `Q` | data matrix |
| 2 | (22, e0, 0) | 395:14-395:114 | construct | mat4 | — | — | **16 `id` children** (f11, f21, f11x, … f22xy) |
| 3 | (23, e0) | 396:10-396:86 | declaration | mat4 | — | 117 `S` | literal matrix |
| 4 | (23, e0, 0) | 396:14-396:86 | construct | mat4 | — | — | 16 literal/unary children |
| 5 | (24, e0) | 397:10-397:86 | declaration | mat4 | — | 118 `T` | literal matrix |
| 6 | (24, e0, 0) | 397:14-397:86 | construct | mat4 | — | — | 16 literal/unary children |
| 7 | (25, e0) | 398:10-398:23 | declaration | mat4 | — | 119 `A` | product |
| 8 | (25, e0, 0) | 398:14-398:23 | binary | mat4 | `*` | — | outer `(T*Q)*S` |
| 9 | (25, e0, 0, 0) | 398:14-398:19 | binary | mat4 | `*` | — | inner `T*Q` |
| 10 | (25, e0, 0, 0, 0) | 398:14-398:15 | id | mat4 | — | 118 `T` | |
| 11 | (25, e0, 0, 0, 1) | 398:18-398:19 | id | mat4 | — | 116 `Q` | |
| 12 | (25, e0, 0, 1) | 398:22-398:23 | id | mat4 | — | 117 `S` | |
| 13 | (30, e0, 0) | 403:16-403:22 | binary | vec4 | `*` | — | `tv * A` |
| 14 | (30, e0, 0, 1) | 403:21-403:22 | id | mat4 | — | 119 `A` | |

Plus the consuming context, measured: node 13's parent is the builtin `dot`
(403:12-403:27, second argument the `id uv`), itself the sole expression of
`bicubic`'s `return` (statement 30). **No mat4 appears anywhere else in the
program**: no mat4 parameters, no mat4 return types, no mat4 members, no
mat4 in any declaration initializer, and the only other matrix is the
**mat2** constructor + `mat2*vec2` product in `rotate2D` (117:10-117:68) —
reachable, and already generically admitted (the emitter's matrix-binary arm
admits `("mat2","vec2")` without any carrier).

The recorded frontier rung `395:10 unsupported typed type mat4` is node 1 —
a LOCAL declaration inside a dead function, emitted anyway.

### 4.2 What the JS does for each site (the authority)

`canonical-kernels.js:2892-2925` (factory7's `bicubic`):

- `Q`, `S`, `T`, `A` are **16-element `$runtime.PooledFloat32Array`s** —
  per-element **f32 narrowing at construction** (column-major flat), *not*
  plain Number arrays. `A = matrixMult(matrixMult(T, Q), S)`.
- `matrixMult` (`src/csl/glsl-runtime.js:276-303`): both-16 branch is
  column-major `out[col*4+row] = F32(sum)` with **double accumulation** over
  `left[inner*4+row] * right[col*4+inner]` — per-element f32 rounding, inner
  product computed left-associated `(T*Q)*S` exactly as the source.
- `tv`/`uv` are 4-element pooled arrays built from `1, t, t*t, (t*t)*t` in
  Number precision, narrowed per lane at construction.
- `dot(tv * A, uv)` is **scalarized by the transpiler** into
  `dot(PooledFloat32Array([dot(tv, A[0..3]), dot(tv, A[4..7]), dot(tv,
  A[8..11]), dot(tv, A[12..15])]), uv)` — a vec4*mat4 product lowers to four
  column dots, each `dot` (`glsl-runtime.js:253-257`) double-accumulating
  with one final `F32`.

So the JS numeric contract for the whole chain is: f32 at every matrix/array
element store, double accumulation inside each product/dot, left-associated
matrix product — **exactly the contract `glsl::Mat<4>` already implements**
(`include/noisemaker/glsl_types.hpp:238-253`: `Mat*Mat` delegates per column
to `Mat*Vec`, which double-accumulates and `f32`s each element;
`Vec*Mat` column-transforms with the same rounding; `dot` is the existing
builtin). This equivalence was *proven for glitch's landing* over the
identical chain; §4.4 re-verifies it for effects end-to-end at the emitter.

### 4.3 Does the frozen glitch carrier cover this? **No — and its lowering does**

The carrier `tools/glslcpp/frontend/glitch_mat4_chain_profile.py`
(`glitch-mat4-chain-v1`) is a **single-key, whole-program freeze**. Measured
against its source this session, effects fails it at, in order:

1. `authenticate_glitch_mat4_chain` line 226:
   `program.key != GLITCH_KEY or source_hash != _RAW_SHA256` → "selected key
   and exact caller source hash required". Hard key check; effects' raw
   SHA is `e3b742be…`, glitch's frozen `13d6350e…`.
2. Line 242: `program.preprocessor_defines != ()` → "source, function,
   declaration, program, or interface mismatch". Glitch is frozen with
   **empty defines**; effects carries `(EFFECT 0, FLIP 0)`. Effects can
   never pass this lock as written.
3. `_FUNCTIONS` (ids 33-43, 11 functions incl. `scanlines`/`snow`),
   `_CALL_GRAPH` (11 entries), `_RESOURCES` (15 uniforms), `_LOOP_PROOF`
   `(0,0,0,0,0,True)`, `len(program.declarations) != 16` — effects has 28
   functions, 13 uniforms, 21 declarations, loop proof `(4,0,2,48,0,True)`.
4. `_MATRIX_NODES` — the identity-hash record of glitch's 14 nodes at
   glitch's spans (76:10-84:27, symbol ids 67-70); effects' nodes have
   different spans (395-403), ids (116-119), and node hashes.
5. `_ORDERED_FREQ_SPLAT` — a `vec2 *= periodicFunction(...)` splat in
   glitch's `glitch` function (symbol 75), which effects does not contain at
   all; and `_OPTIONAL_PROOF_FIELDS` requiring all four sibling proofs
   absent, which an effects row violates by design (it carries the
   auto-attached fixed-array proof, as cellRefract's Amendment 13.2 already
   forced the array module to allow).
6. `_PROFILE_SHA256` self-hash over the whole tuple — any widening edit
   must re-freeze it.

**But the structural closure is the same program text.** Compare glitch's
`_MATRIX_NODES` tuple to §4.1's table: 4 declarations named `Q`,`S`,`T`,`A`;
3 constructors (Q's with 16 non-literal float `id` children, S/T literal);
2 mat4 products left-associated `(T*Q)*S`; 4 mat4 ids; 1 `vec4*mat4`
product `tv * A` whose parent is `dot(..., uv)` as a `return`'s sole
expression; **even the host function's name is `bicubic` in both programs**
(the carrier's own `matrix closure escaped bicubic` check reads naturally on
effects too). The upstream author copied the bicubic implementation between
the two effects; the port inherits a proven closure shape.

And the **emitter side is per-proof-object identity-driven, not
glitch-text-driven**: `emit_typed_cpp.py`'s mat4 type name (`:3063`,
`authorized_glitch_proof is not None` → `glsl::Mat4`), constructor lowering
(`:3631-3648`, identity over `proof.constructors`, 16 float children,
emitting `glsl::Mat4(col0, …, col3)`), and matrix binary arm (`:3895-3910`,
identity over `matrix_products` + `vector_products`, operator/type-shape
check) all consult whatever proof object the carrier block authenticated.
The validator's three mat4 gates (`reject_type` `:3674-3680` over
`consumed_objects`; constructor `:4346-4364`; matrix binary `:4450-4468`)
likewise. **Verdict: existing carrier does not cover effects; existing
lowering covers effects verbatim once a per-key proof object exists.**

### 4.4 The coverage proof (this session's emitter run)

Driving `render_typed_cpp` in the rsync'd copy with a synthetic effects
proof object (14 nodes of §4.1) fed through the *genuine* authentication and
lowering arms — the real constructor/binary/type-lowering code paths, no
probe bypasses inside them — emitted, verbatim from the run:

```cpp
[[maybe_unused]] glsl::Mat4 Q = glsl::Mat4(glsl::Vec4(f11, f21, f11x, f21x), … );
[[maybe_unused]] glsl::Mat4 S = glsl::Mat4(glsl::Vec4(static_cast<float>(1.), …), …);
[[maybe_unused]] glsl::Mat4 T = glsl::Mat4(…);
[[maybe_unused]] glsl::Mat4 A = ((T * Q) * S);
…
[[maybe_unused]] glsl::Vec4 tv = glsl::FloatExpr<4>(static_cast<float>(1.), t, …);
return glsl::dot((tv * A), uv);
```

Every boundary matches §4.2's JS: constructor lanes narrow per lane through
`glsl::Vec4` (the JS pooled-array construction); `((T * Q) * S)` is the
left-associated per-element-f32 product; `tv * A` binds to
`operator*(FloatExpr<4>, Mat4)` → `Vec4(float) * Mat4` (the JS four column
dots, each double-accumulated and f32'd); the outer `glsl::dot`
double-accumulates with one final f32. Numeric parity for the chain is
structure-identical to glitch's proven slice. Note `bicubic` is dead at the
frozen defines — this protection is structural (identity locks), the §17
claim-boundary class; no oracle case exercises it (§11).

### 4.5 What a `mat4` admission for effects needs, per authority

**Carrier side** (the module, dict-keyed after the array module's pattern —
`KEYS`/`PROFILES` + per-key records; glitch's record and row stay
byte-identical, the kaleido landed/prepared precedent):

- An `EFFECTS_KEY` record freezing: key/profile string (recommend a
  per-key string `mat4-bicubic-chain-effects-v1` alongside glitch's frozen
  `glitch-mat4-chain-v1`, per the array module's per-key-string precedent —
  NOT the ceil/XOR shared-string form, because this module's identity is a
  single program's whole-program freeze and a shared string would read as a
  family capability it is not); raw/normalized bytes+SHA; whole/interface/
  functions/declarations fingerprints (§1); **defines
  `((EFFECT,int,0),(FLIP,int,0))`** — the lock glitch freezes empty must
  become per-key data; functions tuple (28, ids 65-92); call graph digest +
  reachability pair (8/20); resources; loop proof tuple; 21-declaration
  census; sibling-proof absent-set **allowing** the auto-attached
  `fixed_array_in_parameter_proof` (Amendment 13.2's exact carve, already
  required for the array module) and naming the row companions that ARE
  present; the 14 `_MATRIX_NODES`-shaped rows with effects' spans/ids/hashes
  (§4.1); the host lock (`bicubic`, id 65, statement paths 22-25/30); the
  `dot`/`return` route locks (403:12-403:27, statement 30); **no
  freq-splat** — the splat fields become per-key optional (glitch's record
  keeps its three; effects' omits them, and the dataclass/proof accessors
  follow the per-key record).
- The module's `_PROFILE_SHA256` self-hash re-frozen; its `_fail` prefix
  becomes per-key (the shape module's Amendment-2 hazard, already the array
  module's pattern).
- **A third module carve the ladder could not see (review finding,
  2026-08-17)**: `ceil_admission_profile.py` names
  `fixed_array_in_parameter_proof` in its `_OPTIONAL_PROOF_FIELDS`
  (`:42-46`, checked at `:155-157`) and will reject effects' row —
  `ceil-admission-v1: unrelated proof carrier is not absent` — until it
  gets the same per-key carve as the glitch module's sibling-proof
  absent-set above. The §6 ladder bypassed the module authenticator (it fed
  the gates synthetic proof objects), so the lane never saw this rejection.
  **Generic family lesson, stated once**: every companion module freezes
  its own FAP-absent set — check each new companion for the carve (XOR for
  kaleido; glitch AND ceil for effects).

**Validator side** (`generate_typed_slice.py`):

- The `mat4` `reject_type` arm, constructor arm, and matrix-binary arm
  consult `authorized_glitch_proof.consumed_objects/constructors/products`
  — extend to the union of authenticated proofs (or a per-key proof
  attribute); the arms' shape checks (`16 float children`, `*`, the
  `("mat4","mat4","mat4")`/`("vec4","mat4","vec4")` type triples) are
  already generic and unchanged.
- The carrier wiring blocks — the validator's array collision list (its
  `or glitch_mat4_chain_profile is not None` entry at `:3164`) and the
  mat4/ceil blocks' own lists — must move to the normalMap
  `REQUIRED_COMPANION_PROFILES` pattern: effects' row carries **three**
  carriers (array + mat4 + ceil), the first three-companion row; each
  companion is REQUIRED, not merely allowed.
- The schema censuses: `glitch_profiles != [(GLITCH_KEY, …)]` at
  `:1322-1323` gains the effects entry; the ceil census
  (`ceil_profiles`, `:1420-1427`) is key-driven and extends automatically
  with the module record; the array census (`:1391-1396`) extends with
  registration; `_MUTABLE_GLOBAL_ARRAY_DEFINES` (`:611`, still a single
  hardcoded `{"KERNEL": 0, "SHAPE": 1}`) must be per-key — effects adds
  `{"EFFECT": 0, "FLIP": 0}` (kaleido §4.5.2 already censused this site).
  The defines dict has a **second** consumption site: `load_slice`'s
  `expected_defines` entry `MUTABLE_GLOBAL_ARRAY_CELLREFRACT_KEY:
  _MUTABLE_GLOBAL_ARRAY_DEFINES` at `generate_typed_slice.py:1456` (inside
  `load_slice`) — it also becomes per-key, and missing it fails closed with
  a schema-drift error.

**Emitter side** (`emit_typed_cpp.py`): the mat4 carrier block's key gate
(`self.program.key != GLITCH_KEY`, `:1111-1116`) and its hardcoded
re-verification tail (glitch symbol ids 75, the splat fields, `:1136-1174`)
become per-key; the collision list carve-outs as above; **the type-name,
constructor, and product arms need no change** — they are identity-driven
over the proof object (§4.4 proved it).

## 5. Mechanism decomposition

| # | Mechanism | Status |
| --- | --- | --- |
| A | Mutable uninitialized global `float[9]` admission (**×7**, first seven-array member) | **extension** — third record in `mutable_global_array_profile.py`; the 45→63 cardinalities below are the only structural deltas |
| B | Non-`main` writer (`loadKernels`, 63 literal stores) | **covered** — same writer name, same `Frame&` emission shape, same §12 bare-call arm (new frozen node: stmt 15, span 583:5-583:18) |
| C | `float[9]` parameter + local literal tables + whole-array call args | **fourth key** at `fixed_array_in_parameter_proof.py`; the cellRefract §13.1 arm pattern, third copy (or the tuple-of-keys refactor) |
| D | **mat4 closure admission** (14 nodes, `bicubic`) | **the new mechanism** — second key in the glitch module per §4.5; no new lowering |
| E | `ceil` admission in reachable `main` code | **third key** in `ceil_admission_profile.py` (dict-keyed since birth, per-key record shape at its `:47-77`); sites `main 574:13-574:99` and `main 575:13-575:109` (node SHAs `5405bd10…`, `0f65b650…`; first-child SHAs `2a885db6…`, `5105faf6…`) |
| F | The two rvalue `color *= dist` sites | **covered** — the corrected §17 arm, vector dispatch, verified emitted this session |
| G | Loop admission | **expected drop-path** — `(4, 0, 2, 48, 0, True)`, all four loops proved, 48 ≪ 262144 lexical-product cap (`loop_proof.py:38-40`); no carrier (confirm by RED probe, the cellRefract §3D/kaleido §4 E pattern) |

### The hard-wired sites the ladder measured (the §13 class, all four)

1. `generate_typed_slice.py:3196` — `len(authorized_mutable_global_arrays)
   != 5` (validator cardinality; fires FIRST after authentication).
2. `generate_typed_slice.py:4954` — `len(visited_mutable_global_array_stores)
   != 45` (the walk-side store ledger; fires LAST before CLEAN).
3. `emit_typed_cpp.py:5443` — `len(emitter.emitted_array_frame_stores) != 45`
   (the emission-side ledger; fires at the final audit).
4. `emit_typed_cpp.py:1954` — the emitter's array cardinality is already
   contract-driven (`!= len(contract.fields)`), so it needs **no** edit: the
   effects record's 7-field contract satisfies it. (Recorded as the
   non-site, so an implementer does not "fix" it.)

Each `45`/`5` becomes per-key (the contract's field count / the record's
store census — the same never-a-bare-number rule `_MUTABLE_GLOBAL_ARRAY_DEFINES`'s comment at `:612-616` states).

### The fixed-array fourth key: contents, measured

The convolve family is structurally identical to cellRefract's/kaleido's.
Record facts: `convolve` id 70, body 16 statements; parameter `(42,
"kernel", "float[9]", "in")`, native ABI `const Kernel9&`; exactly 2
induction-indexed reads per iteration at `255:32-255:33`/`258:32-258:33`,
induction symbol 154; loop at body[13], proof `(154, 0, 9, "<", "++",
"literal", 9, 1, 1, 9, 0)`; `vec2 offset[9]` table symbol 151 at body[1]
with stores body[2..10]; the 8 caller tables of §1 with their whole-array
argument spans. Whole-program nine-number census over 17 array ids
`{15,…,21, 42, 151, 157, 158, 179, 180, 202, 203, 210, 211}` (the module's
own `_array_census` helper, run this session):
**(1, 9, 164, 155, 144, 3, 147, 8, 8)** — parameters, declarations,
expressions, identifiers, literal stores (63 + 72 + 9 = 144), induction
reads, index expressions, whole-array arguments, array calls. Note 144
literal stores and 17 array ids differ from both landed keys' numbers —
frozen per key, never shared. Binding signature (13 uniforms):
`inputTex:sampler2D, resolution:vec2, tileOffset:vec2, fullResolution:vec2,
renderScale:float, time:float, effectAmt:float, scaleAmt:float,
rotation:float, offsetX:float, offsetY:float, intensity:float,
saturation:float`. FAP-shaped fingerprints for the record: interface
`feeb85a5…` (§1, same formula), functions `d06fd421…`, whole `db85c4d2…`,
canonical factory `ebf43ff4…` (§3.6).

## 6. The blocker ladder (both authorities, measured rung by rung)

Method: per-program `validate_capabilities` / `render_typed_cpp` in the
rsync'd copy, admitting each mechanism *hypothetically* (patched gate or
synthetic proof object) and recording the next rejection — the normalMap
method. No probe drove `generate_outputs` (the one-row-slice trap).

**Validator ladder:**

| Rung | Carriers/gates admitted hypothetically | Next rejection (measured) |
| ---: | --- | --- |
| 0 | none (live) | `31:1: unsupported global declaration` |
| 1 | array carrier (7 decls) | `mutable-global array carrier cardinality mismatch` (the `!= 5` site) |
| 2 | + cardinality 7 | `395:10: unsupported typed type mat4` (node 1 of §4.1 — matches `REMAINING-EFFECTS.md`'s recorded second blocker) |
| 3 | + mat4 type arm | `395:14: unsupported matrix constructor` |
| 4 | + constructor arm | matrix-binary arm (patched in the same pass; its rejection is `unsupported matrix binary expression`) |
| 5 | + matrix binary arm | `234:24: unsupported typed type float[9]` — the convolve parameter (fixed-array fourth key) |
| 6 | + float[9] types | `236:10: unsupported typed type vec2[9]` — the offset table |
| 7 | + vec2[9] types | `237:5: unsupported typed expression index` — the indexed-store/read family (`proved_task19_*` sets) |
| 8 | + index arms | `574:13: unsupported builtin ceil` — **reachable** main code |
| 9 | + ceil | `authenticated mutable-global array store visitation mismatch` (the `!= 45` ledger) |
| 10 | + ledger 63 | **CLEAN** |

**Emitter ladder** (independent authority; synthetic array contract +
effects mat4 proof + ceil sites, real lowering arms):

| Rung | Admitted | Next rejection (measured) |
| ---: | --- | --- |
| 0 | none | (carrier blocks: `mutable-global array profile metadata mismatch` — the collision list rejects the mat4/ceil companions) |
| 1 | + collision carve, array carrier, 7-field contract | `234:24: unsupported typed type float[9]` (`function_parameter_type`) |
| 2 | + array param ABI | `236:10: unsupported fixed-nine array declaration` (local table emission) |
| 3 | + local tables | `237:5: unsupported typed expression index` |
| 4 | + index grammar | the final audit's `authenticated mutable-global array frame reference mismatch` (`!= 45` store ledger) |
| 5 | + ledger 63 | **CLEAN — 651 lines emitted**; §4.4's fragments verbatim; both §17 sites (`return (color = glsl::Vec3(color * dist));`), the §12 writer call (`loadKernels(state, context, frame);`), and `glsl::ceil` at both main sites all lowered through existing arms |

**Consequence: the ladder terminates.** No unprobed validator or emitter
mechanism remains behind the enumerated ones — the §9 anticipated-discovery
class of cellRefract/kaleido is, for effects, closed by measurement. The
implementation's remaining unknowns are per-key record contents and the
named widenings, not grammar.

**Scope note (2026-08-17 review):** the CLEAN terminations and the 651-line
emission figure are **lane-measured**; the independent review confirmed them
only through validator rungs 0-2, emitter rungs 0-2, and the §4.4 fragments
(no contradiction found; termination not independently re-run).

## 7. Emission contract

Namespace `typed_N` (N = the generated ordinal at insertion) gains, in order:

1. The fixed-array alias block (from the fourth key, as cellRefract's):
   `using Kernel9 = std::array<double, 9>;`,
   `using Offsets9 = std::array<glsl::Vec2, 9>;` + the two
   `static_assert(sizeof(...) == 72U)` — per-namespace, no collision.
2. `struct Frame final { Kernel9 emboss{}; Kernel9 sharpen{}; Kernel9
   blur{}; Kernel9 edge{}; Kernel9 edge2{}; Kernel9 edge3{}; Kernel9
   sharpenBlur{}; };` — member order = declaration ordinals 14-20;
   value-initialization reproduces the JS factory-scope zeros (unobservable,
   but exact). The probe's emitted struct (with the probe's
   `std::array<double, 9>` spelling) is §4.4's sibling; the real slice
   spells the members `Kernel9` via the alias cross-check at
   `emit_typed_cpp.py:1965-1969`.
3. `loadKernels([[maybe_unused]] const State& state, [[maybe_unused]] const
   glsl::PixelContext& context, Frame& frame) noexcept` — the only non-const
   frame parameter; body the 63 stores `frame.emboss[0] =
   static_cast<float>(-2.0);` etc. (literal form per refract's store
   lowering).
4. Every other helper gains `[[maybe_unused]] const Frame& frame` at
   ordinal 2. `convolve` (`const Kernel9& kernel`), the eight caller
   tables, `Kernel9 deriv_x{}` locals, and whole-array arguments compile
   unchanged from the refract/cellRefract shape. **`bicubic` too** — the
   mat4 locals need no frame member; the chain is pure locals
   (`glsl::Mat4 Q/S/T/A`, `glsl::Vec4 tv/uv`), all stack, verified in the
   emitted run.
5. `pixel` declares `Frame frame{};` after the state preamble and lowers
   `loadKernels();` (statement 15) to `loadKernels(state, context, frame);`
   via the §12 identity-gated arm — the arm's frozen node list gains
   effects' call node (span `583:5-583:18`). Symbol mapping `15..21 →
   frame.<name>`.
6. Final audit: one Frame type/instance, one non-const frame parameter,
   writer called once, both §17 sites emitted through the vector dispatch,
   all seven symbols written, 63-store ledger — the audit's counts move
   per-key (§5's site 3).

`aspectRatio` is a `#define` macro over `fullResolution.x /
fullResolution.y` and stays expression-level (no trace of it in the emitted
output — measured); it is not a mutable global. The `uv.x -= ceil(…)` /
`uv.y += ceil(…)` compound swizzle assigns in main lower through the
existing `set_swizzle` + `glsl::ceil` path (emitted lines verified).

## 8. Slice row and projected censuses

```json
{
  "ceil_admission_profile": "ceil-admission-v1",
  "defines": {"EFFECT": 0, "FLIP": 0},
  "glitch_mat4_chain_profile": "mat4-bicubic-chain-effects-v1",
  "mutable_global_array_profile": "mutable-global-nine-array-effects-v1",
  "program_key": "classicNoisedeck/effects:effects"
}
```

— the family's first **three-carrier** row (normalMap carried two via
`REQUIRED_COMPANION_PROFILES`; kaleido's carries two; the companions are
REQUIRED, and the negative REDs are rows missing any one of them).

Sorted neighbors (measured against the live 186-row slice): insertion index
5, `classicNoisedeck/composite:composite` < **effects** <
`classicNoisedeck/glitch:glitch` — effects sorts *adjacent to glitch*, the
program whose carrier it shares. Projected censuses (typed rows, catalog
entries, absent keys, typed-list SHA-256, the four artifact hashes, the
native `factories.size()` assertion — live value read this session:
`REQUIRE(factories.size() == 188U)` at `tests/test_generated_kernels.cpp:261`)
are **computed from the live generator at integration**, never projected by
hand (§11 lesson; re-read the assertion — its line number has already moved
once). The auto-attach census test (`test_typed_generator.py`, currently
exactly {refract, cellRefract}) moves with whichever key lands first:
kaleido makes it three, effects four.

## 9. Proof composition (RED/GREEN sketch)

Both authorities independently authenticate and admit **by object
identity**; the seven declarations join the mutable set separate from const
`admitted_globals`; consumed nodes ledger exactly once. RED sequence
(watch each fail for the intended reason):

1. Row absent: `31:1 unsupported global declaration` (live boundary).
2. Row present, carriers absent: `exact mutable-global array profile
   carrier required` at both authorities; then each companion's twin.
3. Foreign carriers: sweep every sibling profile string at both
   authorities; record which neighbour answers first (collision-chain
   trap); claim only rows tested.
4. Per-lock mutations for the array record: wrong raw/normalized hash,
   defines drift (`EFFECT=1` re-normalizes — record what changes; the
   collapsed `convolutionEffect` re-expands and the read census flips),
   inventory ±1, each of the seven renamed/retyped/initialized/moved, 62/64
   stores, non-literal index, non-(literal|unary-literal) value (§14),
   compound write, second `loadKernels` caller, call moved after statement
   16, a read inserted (must fail the write-only census AND the §6 rung-2
   walk), `Frame&` relaxation, non-value-initialized Frame.
5. Mat4 record mutations: each of the 14 nodes altered/removed/reparented
   (constructor arity 15/17, a non-float child, `+` instead of `*`,
   right-association `(Q*S)` — the topology lock, the dot's second argument
   renamed, the chain escaping `bicubic`, a 15th mat4 node appearing);
   defines/values re-frozen to the mutant with coarse messages asserted
   absent.
6. Ceil record mutations: site spans/shashes, a third ceil, ceil outside
   main, callee renamed; the shared-string census for oilPaint/smoothBlend
   stays green.
7. The four §5 hard-wired sites: their per-key replacements RED under
   5-array/45-store mutants of the *cellRefract* record (proving the
   widening did not loosen the landed key) and under 6-array/62-store
   effects mutants.
8. Three-companion negatives: a row missing mat4, missing ceil, missing
   array — each fails closed; the collision lists' carve-outs are per-key
   (a kaleido row carrying a mat4 carrier still rejects).
9. Delete-the-check sweep over every NEW predicate, one at a time, sub-clause
   pairs where `or`-chains are added; tabulate.
10. Sabotage tests for the visitation ledgers (both authorities).

## 10. Verification gates

The standing matrix: four generator gates; focused then full Python; native
Debug/Release/ASan+UBSan (zero warnings, `-ffp-contract=off`, no LSan claim
on Apple); ctest; assembly audit ARM64+x86_64 with demangled symbols;
historical reconstruction (remove only effects from a deep-copied live spec,
regenerate in memory, recover the four pre-effects artifact hashes;
sanity-check the splitter on the unchanged pair first); storage
manifest/cleanup with one owned run root.

Assembly notes: the executed pixel scope at the frozen defines is the
reachable eight (`pixel` + inlined `rotate2D/map/brightnessContrast/
saturate/periodicFunction/offsets/loadKernels`); `convolve`, the
caller-table helpers, `bicubic` (and its `Mat4` arithmetic) and the five
effect-leaf families are out of executed scope — record their instruction
counts, scope the no-indirect-branch/no-fused-FP/no-allocation claims to
executed scope, prove fused-FP absence TU-wide. `Frame` is stack-only (7 ×
72 = 504 bytes — note the frame grew; confirm no stack-depth surprise in
the sanitizers). The 63 stores inline into `pixel`.

## 11. Oracle design (sketch; the oracle lane owns the real design)

`effects_oracle_generator.mjs` in this directory, in the family pattern:
`--cpu-root` required and realpath'd; refuse the live checkout, containment
either way, inside-C++-repo roots; per-file SHA-256 import closure; the
pinned CPU-file hashes (§3); factory identity
`kernelFactories.get(key) === canonicalKernelFactories[key]`; factory name
exactly `canonicalFactory7`; `Function.prototype.toString` SHA-256 frozen
at `ebf43ff4…`; both adapter tables censused (`canonicalAdapterFactories`
must not own the key); GLSL bytes/SHA pinned; stable path placeholder,
absolute-path rejection.

Cases (each full float32-word + RGBA8 arrays, one materializer include):

- `rotation`/`scaleAmt` sweeps driving the reachable `rotate2D` (mat2!) and
  the `uv` re-centering with `ceil` — the two axes that exercise the new
  reachable grammar (`glsl::ceil` and the compound swizzle assigns).
- `offsetX`/`offsetY` arms for the map-driven translation lanes.
- `intensity`/`saturation` negative and positive arms — `brightnessContrast`
  has both `intensity < 0` and `>= 0` contrast maps; `saturate` the `-1..1`
  sat map (both reachable).
- `time`-driven `blendy` (`periodicFunction`, `offsets`) — `blendy` is
  computed but UNUSED at EFFECT=0; use it as the liveness witness that the
  computation is present and identical, not as a discriminating axis.
- `EFFECT=0`/`FLIP=0` invariance controls: both bindings are runtime in the
  JS; run one case each at the frozen values and record the axes with a
  liveness census (the port has neither binding — assert the *absence* of
  the divergence channels, the Shapes §11 pattern; a `FLIP=1` mutant of the
  JS must be invariant against the port).
- No tile-crop case: cellRefract §15 measured the crop identity
  program-shaped; effects samples `inputTex` through a scale/rotate/fract
  warp — budget nothing until probed, cite nothing.

**Mutants — satisfiability checked before budgeting**: the seven tables are
write-only at the frozen defines, so **no table mutant is
pixel-discriminable** (their protection is the frozen 63 triples; the
acceptance record says so plainly). The whole `bicubic` chain, `convolve`,
and the five leaf families are unreachable — mat4 mutants, convolve
mutants, and leaf mutants are **invariant everywhere**; record one
representative invariance witness each rather than budgeting them.
Discriminating candidates (verify, don't assume): `ceil`-dropped (reachable
main), `map`-arms swapped, `rotate2D` angle map perturbed,
`saturate`/`brightnessContrast` coefficient perturbed, `aspect-ratio`
inverted (affects `rotate2D` scaling — `fract(uv)` feeds the texture
sample, so discrimination is plausible but must be measured).

ABI: 13 bindings — `inputTex` texture; `resolution`/`tileOffset`/
`fullResolution` `Vec2`; `renderScale`, `time`, `effectAmt`, `scaleAmt`,
`rotation`, `offsetX`, `offsetY`, `intensity`, `saturation` via
`get_number`. `EFFECT`/`FLIP` are define-style knobs, not ABI bindings (the
port has no such binding; cellRefract's KERNEL/SHAPE precedent). Omit-each
and wrong-variant-each with `KernelBindingError` naming the binding;
unrelated extras ignored; caller immutability; exact alpha; determinism;
independent output storage.

## 12. Risks and expected discoveries

- **The ladder is closed by measurement (§6), so the standing
  "deeper gates are unprobed" risk is retired for this program** — but the
  ladder was climbed with *hypothetical* admissions; the real records'
  internal locks (write-census walkers, dominance, ledgers) are new code
  with their own mutation surface, and the delete-the-check sweep is where
  their vacuity would surface. Budget the sweep, not ladder re-probing.
- **The mat4 module edit touches a frozen, self-hashed single-key
  module.** The dict-key refactor must keep glitch's record, messages, and
  `_PROFILE_SHA256` re-freeze honest; glitch's tests
  (`tests/test_glitch_mat4_chain.py` — currently modified in the live tree
  by another lane) must stay green byte-identically.
- **Three-companion rows are new**: every collision list that today assumes
  "array carrier implies no other carrier" (validator `:3145-3185`, emitter
  `:1895-1949`, and the mat4/ceil blocks' own lists) needs the
  required-companion treatment; a missed one is a fail-closed rejection
  discovered late, not a silent pass — but sweep them all in §9.8 rather
  than discovering them gate-by-gate.
- **`shadow`'s caller tables at statements 0/10** (kaleido's quirk, here
  measured) — the generic declaration-search helper is the reuse; a
  frozen-index helper copied from derivatives/sobel/outline fails only on
  shadow.
- **`edge3`/`sharpenBlur` are new table values** — the byte-identity test
  against cellRefract's 45 triples covers only five of seven tables; freeze
  all 63 and test the two new tables' values explicitly (a transcribed
  `-0.875` typo is exactly the §11 transcription trap).
- `Symbol` span self-absorption, value-checks-ahead-of-identity, refreeze
  only coarse hashes, the collision-chain unreachability trap — the landed
  test classes embed the countermeasures; follow them.
- The JS `main` computes `blendy` ununused at EFFECT=0 — a live-but-dead
  lane the port emits too; do not "clean it up" (the emitter emits
  unreachable code by design; reachability is not the proof's concern).

## 13. Order recommendation (measured basis)

**effects is dearer than kaleido's integration, cheaper than the varying
bucket's unknown; land it after kaleido's integration and before (or in
parallel with, resource permitting) the varying bucket.**

- **After kaleido.** kaleido's integration is wiring plus two carve-outs on
  fully-frozen contents (`kaleido-design.md` §0: record landed PREPARED,
  third-key contents measured, both conflicts with named resolutions);
  effects shares every integration surface kaleido touches — the array
  module registry, `load_slice`'s array census, `_MUTABLE_GLOBAL_ARRAY_DEFINES`,
  the validator/emitter array blocks, the auto-attach census, the
  fixed-array module — plus four surfaces kaleido does not touch (the
  glitch module, the ceil module, the glitch/ceil schema censuses, the
  45→63 sites). Landing effects first would double-widen every shared site
  under kaleido's feet and force kaleido's integration to re-derive its
  two-conflict analysis against a three-carrier world. kaleido first keeps
  each diff one-key-shaped.
- **Before the varying bucket.** effects' risk is now bounded by
  measurement: both ladders terminate at CLEAN (§6), the one new mechanism
  (mat4 per-key) reuses lowering proven end-to-end this session (§4.4), and
  every remaining edit is a named per-key record or a named widening with a
  RED test. The varying bucket (`wobble`/`grime`/`texture`,
  `1:1 unsupported varying`) has an unprobed ladder — its second blockers
  are unmapped, and `spookyTicker`'s membership shows the bucket bleeds
  into the const-array tail. Completing the mutable-global-array family
  while its machinery, test patterns, and the family's three designs are
  fresh is cheaper than context-switching back later. If the varying lanes
  are already resourced, effects can proceed in parallel: its file overlap
  with varying work is the generator/emitter hot core every slice touches,
  nothing mechanism-specific.

## 14. Ownership for the implementation slice

- **Record lane**: `tools/glslcpp/frontend/mutable_global_array_profile.py`
  (effects record, prepared-then-registered per the landed/prepared split),
  `glitch_mat4_chain_profile.py` (dict-key refactor + effects record),
  `ceil_admission_profile.py` (third key), their tests.
- **Integration lane**: `generate_typed_slice.py`, `emit_typed_cpp.py`,
  `fixed_array_in_parameter_proof.py` + tests, `typed_slice.json`,
  generated artifacts, the schema censuses, the four §5 sites.
- **Oracle/native lane**: `effects_oracle_generator.mjs`, oracles JSON,
  include + materializer + sidecars, `tests/test_generated_kernels.cpp`
  census (read the live assertion at implementation time — it moved from
  :249 to :261 since cellRefract §11), the historical reconstruction.
- **Binding constraint**: no row lands before kaleido's integration slice
  reports; the effects row lands with its own full gate cycle.

### Independent review (2026-08-17)

Independent design review (frozen record:
`docs/port-engineering/prepared-designs-review-kaleido-varying-effects.md`)
returned verdict **GO-WITH-CORRECTIONS**. The corrections were applied in
place above:

1. **Important — §1's node census was wrong.** Measured 2,638 nodes / 235
   assigns; this doc said 3,117/235 — a digit transposition of kaleido's
   3,178. Fixed.
2. **Important — §1's call-graph digest was wrong.** Measured
   `cb421a62eb9d14a121e746b6bffea51e7c188db10230a95f77349bbb2ef2c3da`
   (the edge count 30 was right); this doc had `382ce57b…041e`. Fixed.
3. **Important — a third module carve the §6 ladder could not see (§4.5).**
   `ceil_admission_profile.py` names `fixed_array_in_parameter_proof` in
   `_OPTIONAL_PROOF_FIELDS` (`:42-46`, checked `:155-157`) and will reject
   effects' row (`ceil-admission-v1: unrelated proof carrier is not
   absent`) until it gets the same per-key carve as the glitch module; the
   §6 ladder bypassed the module authenticator, so the lane never saw it.
   Added to §4.5's carrier-side list with the generic family lesson: every
   companion module freezes its own FAP-absent set — check each new
   companion for the carve (XOR for kaleido; glitch AND ceil for effects).
4. **Minor — three §3/§5 figures.** `canonical-kernels.js` is 1,713,290
   bytes (not 171,329; the SHA is correct); the emitter contract-driven
   cardinality site is `emit_typed_cpp.py:1954` (not `:1955`); Factory7's
   `loadKernels` is `:2481-2547` (not `:2480-2546`). All fixed.
5. **Minor/scope — §6's termination claims are lane-measured.** "Both
   ladders terminate CLEAN" / "651 lines" marked as lane-measured; the
   review confirmed only validator rungs 0-2, emitter rungs 0-2, and the
   §4.4 fragments (no contradiction found; termination not independently
   re-run).
6. **The `generate_typed_slice.py:1456` `expected_defines`
   second-consumption-site note (same as kaleido's)** added to §4.5's
   validator-side list.
