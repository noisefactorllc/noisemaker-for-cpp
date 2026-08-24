# Task 16 implementation-risk audit

Date: 2026-08-10  
Repository inspected: `.`  
Pinned corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`  
Input audit: `docs/port-engineering/post-loop-frontier-audit.md`  
Input audit SHA-256: `3acadc92578a2bcb3e4e24a7cebc6aca93048410d452a33042d745b90f7a1ba1`

## Conclusion

The proposed seven-key `fixed-local-array-index-v1` is not one bounded
feature. It combines five independently reviewable contracts:

1. a standalone conditional local-integer post-increment with **no array or
   index expression**;
2. literal-initialized fixed local arrays read by one direct induction
   variable;
3. a nested-loop visit counter used as a dynamic array write index;
4. a fixed array passed by `in` parameter across a helper-call boundary; and
5. affine array initialization followed by direct induction reads.

The smallest coherent safe Task 16 is therefore the one-key
`bounded-local-counter-statement-v1` slice:

```text
filter/pixelSort:computeRank
```

It adds one exact statement form, `brighterCount++`, while reusing the already
implemented Task 13 `texelFetch` and Task 15 counted-loop/`continue` contracts.
It adds no type, array, index, storage, alias, parameter, definite-assignment,
or liveness semantics. Conditional on Task 15 being accepted as the baseline,
Task 16 would move the catalog from **107 typed / 109 public / 103 unported**
to **108 typed / 110 public / 102 unported**.

This is a preflight recommendation only. The repository already contains the
107/109 Task 15 implementation, but this audit does not treat Task 15 as
approved and does not authorize Task 16 implementation.

No repository file was changed.

## Corrected baseline and count arithmetic

The checked tree contains exactly 107 entries in `tools/glslcpp/typed_slice.json`
and a generated `std::array<KernelFactory, 109>` public catalog. The pinned
manifest contains 212 programs, so `212 - 109 = 103` remain publicly unported.
All seven candidates are absent from the typed allowlist.

| Projection | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Actual conditional post-Task-15 baseline | 107 | 109 | 103 |
| Recommended Task 16: `computeRank` only | 108 | 110 | 102 |
| Then literal-init/direct-read local arrays (2 keys) | 110 | 112 | 100 |
| Then nested-grid counter arrays (2 keys) | 112 | 114 | 98 |
| Then refract array parameter (1 key) | 113 | 115 | 97 |
| Then sacred-geometry affine array (1 key) | 114 | 116 | 96 |

Adding all seven at once would therefore yield **114 typed / 116 public / 96
unported**, not the input audit's stale 122/124/88 projection.

## Current first blockers: direct validator replay

All programs analyze successfully through immutable typed IR at authoritative
metadata defaults. The current capability validator then fails exactly as
follows:

| Key | Current first rejection |
| --- | --- |
| `classicNoisedeck/refract:refract` | `26:24 unsupported typed type float[9]` (array parameter) |
| `filter/celShading:celShadingEdges` | `41:11 unsupported typed type float[9]` |
| `filter/outline:outlineSobel` | `60:11 unsupported typed type float[9]` |
| `filter/pixelSort:computeRank` | `34:13 unsupported typed expression post` |
| `filter/sharpen:sharpen` | `25:11 unsupported typed type float[9]` |
| `filter/sobel:sobel` | `23:11 unsupported typed type float[9]` |
| `synth/sacredGeometry:sacredGeometry` | `96:10 unsupported typed type vec2[13]` |

`computeRank` is thus mechanically independent of every proposed array rule.

## Recommended Task 16: exact identity and profile

| Field | Exact value |
| --- | --- |
| Program key | `filter/pixelSort:computeRank` |
| Pinned source | `sources/filter/pixelSort/computeRank.glsl` |
| Raw source SHA-256 | `6ce61bb5cb69bb22ac51f48603d5b40755b1e3f700acad1bc685a1e8a4dea6a4` |
| Define map | `{}` |
| Source-bound effect parameters | none for this pass |
| Binding signature | `lumTex:sampler2D@1/S1` |
| Output | `fragColor:vec4` |
| Array/index/liveness requirements | none |

The pass route is exactly `lumTex <- luminance`, producing the pixel-sort
graph's `rank` surface. Task 16 adds only this factory; it does not claim that
the whole six-pass pixel-sort effect is newly ported.

### Exact counter and control proof

The source has the following already-typed facts:

- `const int NUM_SAMPLES = 32` is the exact Task 15 local-const-literal bound.
- `int brighterCount = 0` is a fresh writable function-local `int`.
- The only write after initialization is the exact standalone expression
  statement `brighterCount++` at source line 35.
- That statement is inside an `if` nested in the proved loop
  `for (int s=0; s<NUM_SAMPLES; s++)`, whose immutable proof records 32 trips,
  depth 1, lexical product 32, and entrypoint charge 32.
- The conditional can execute at most once per loop visit. `continue` can only
  reduce executions. The conservative post-loop interval is therefore
  `brighterCount in [0,32]`, far inside signed 32-bit range.
- The postfix result is discarded. Lowering the admitted statement to
  `++brighterCount;` is observationally equivalent and does not admit postfix
  value semantics.
- After the loop the counter is read only by the existing explicit
  `float(brighterCount) / float(NUM_SAMPLES)` conversion. It does not escape,
  alias, index storage, control another loop, or affect an allocation size.

The proof must be retained in immutable typed IR (for example a frozen
`LocalCounterStatementProof` on the containing `TypedStatement`) and
independently recomputed before emission. Source text, indentation, or the
mere presence of a `post` node is not authority.

### Fail-closed Task 16 contract

1. Admit only the pinned key, source digest, empty define map, exact local
   symbol identity, and exact statement location/control graph above.
2. Accept one standalone postfix `++` expression statement whose operand is
   the proved fresh local `std::int32_t brighterCount`. Reject prefix use,
   decrement, compound assignment, expression-valued postfix, another target,
   another statement, another function, and every other key.
3. Require exact initialization to zero, no competing write, at most one
   conditional update per one of the 32 proved visits, and a recomputed
   interval contained in `[0,32]`. Reject an absent/tampered proof before C++
   generation.
4. Keep Task 15 loop-header increment special handling unchanged. Do not add
   generic `post` support to the expression emitter: the statement emitter
   should recognize only this proved, value-discarded form.
5. Preserve `continue`'s native `for` semantics, level-zero integer
   `texelFetch`, integer division for `sampleX`, stable tie-breaking by
   `sampleX < x`, and explicit float conversion for normalized rank.
6. Retain allocation-free/noexcept pixel execution. This feature needs one
   automatic `std::int32_t`; no array, heap allocation, map/string/variant
   lookup, callback, virtual dispatch, or resource-ABI change belongs in it.

### Required Task 16 negative tests

- body `++x`, `x--`, `x += 1`, `y++`, `(x++) + 1`, `call(x++)`, or postfix
  outside the proved loop/conditional;
- a float, uint, const, parameter, uniform, global, loop induction variable,
  member, swizzle, or indexed operand;
- nonzero/dynamic initialization, a second write, a second update per visit,
  a changed loop bound, a nested multiplicity that exceeds the interval, or
  an integer-overflowing upper proof;
- missing, forged, stale, or symbol-ID-mismatched counter proof at validator
  and emitter boundaries;
- wrong key/source digest, non-empty defines, a second admitted key, missing
  `lumTex`, and every wrong exact binding type.

## Frozen-oracle candidates for Task 16

The following two direct canonical cases were rendered read-only from
`noisemaker-for-cpu`'s pinned `canonicalKernelFactories` using
`bindCanonicalKernel`. The canonical-kernels file inspected has SHA-256
`e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`.
They are suitable exact inputs for the Task 16 oracle freeze; an implementation
brief should still record them in a checked artifact and double-render them.

Common contract:

- destination `9x7`, sampler `lumTex` `11x9`;
- output storage lane `(y*9+x)*4`, fragment coordinate `[x+0.5,y+0.5]`;
- context time `0.375`, frame `7`, delta time `1/60`, seed `19`;
- probes at `(0,0)`, `(4,3)`, `(8,6)`;
- exact F32 bytes, `Surface.toRgba8()` bytes, probe bits, and immediate repeat
  identity must all be checked.

| Variant | Exact `lumTex` construction | Coverage | F32 SHA-256 | RGBA8 SHA-256 | Probe RGBA values |
| --- | --- | --- | --- | --- | --- |
| `formula` | Task-15 tag-1 formula: R `((17x+31y+13)%101)/100`, G `((7x+19y+23)%97)/96`, B `((29x+11y+5)%89)/88`, A `0.35+((3x+5y+1)%13)/20`, each stored to F32 | strict `otherLum > myLum`, skips, positive and zero-ish ranks, heterogeneous rows | `76d5d2c34daae149118591a028a80babed535197369d6b5df2216e1eec5bcb47` | `601c05e3052298d0cfc12cf503876e5ada8a0c274bdad24a2fb00e1cfaa90cdf` | `[0.46875,0.589999974,0,1]`; `[0.53125,0.340000004,0.400000006,1]`; `[0.8125,0.0900000036,0.800000012,1]` |
| `flat-tie` | every texel exactly `[0.5,0.25,0.75,1]` in F32 storage | equality/tie-break arm, `sampleX < x`, skips, counter zero at x=0 and positive elsewhere | `37826c52ed556af08540665ec5435fd99188af1aeb525900647b710f0ecf800f` | `472adcee73849262e3cc7ce4a7bcfdfbb2e4191f7c51e6d49ab4e02404e8d753` | `[0,0.5,0,1]`; `[0.375,0.5,0.400000006,1]`; `[0.75,0.5,0.800000012,1]` |

For width 11, `floor(s*11/32)` reaches every sampled x in `0..10`; every
destination x in `0..8` therefore exercises the `continue` path. Across the
two cases, the body increment executes under both the strict-brighter and
equal-luminance tie-break predicates.

## Why the six array keys must remain split after Task 16

The smallest reusable partition is four later contracts, not one generic
array capability:

| Later contract | Exact keys | New proof burden |
| --- | --- | --- |
| `fixed-nine-local-literal-init-counted-read-v1` | `filter/sharpen:sharpen`, `filter/sobel:sobel` | fixed local arrays, literal stores, direct induction reads |
| `fixed-grid-counter-store-v1` | `filter/celShading:celShadingEdges`, `filter/outline:outlineSobel` | dynamic store index derived from nested visit count, standalone body increment, full initialization |
| `fixed-array-in-parameter-v1` | `classicNoisedeck/refract:refract` | const-reference ABI, direct caller ownership, no alias/copy/escape |
| `fixed-affine-centers13-v1` | `synth/sacredGeometry:sacredGeometry` | affine write intervals, disjoint/exhaustive initialization, 13x13 reads |

Bundling the two keys within each of the first two rows is coherent because
their type, index, initialization, and control proofs are isomorphic. A
source-identity-first implementation may split those pairs further without
weakening the language boundary.

### Exact array/index/definite-initialization/liveness census

“Scalar lanes” is the structural cap: a `vec2` element counts as two. “Native
bytes” below follows the current emitter's canonical policy: local GLSL
`float` values are C++ `double`, while `glsl::Vec2` stores two C++ `float`
lanes.

| Key | Exact array and index proof | Definite initialization | Peak array lanes / native bytes |
| --- | --- | --- | ---: |
| `filter/sharpen:sharpen` | `float kernel[9]`, `vec2 offsets[9]`; literal writes `0..8`; sole nine-trip `i=0..<9` reads `offsets[i]`, `kernel[i]` | both arrays fully written before loop; no earlier read | 27 lanes / 144 bytes (`double[9]` + nine `Vec2`) |
| `filter/sobel:sobel` | `float sobel_x[9]`, `float sobel_y[9]`, `vec2 offsets[9]`; literal writes `0..8`; `i=0..<9` reads all three at `i` | all 27 elements fully written before loop | 36 lanes / 216 bytes |
| `filter/celShading:celShadingEdges` | `float samples[9]`; nested `ky=-1..1`, `kx=-1..1`; pre-use `idx` is exactly `0..8`, one store then `idx++`; later literal reads all except index 4 | zero-size texture returns before array path; normal path has exactly nine unconditional stores before reads | 9 lanes / 72 bytes |
| `filter/outline:outlineSobel` | same nine-visit store proof and later literal read set as Cel | same early-return/normal-path proof | 9 lanes / 72 bytes |
| `classicNoisedeck/refract:refract` | caller `deriv_x[9]` or `deriv_y[9]`, callee `vec2 offset[9]`, exact `in float kernel[9]`; literal stores `0..8`; `i=0..<9` reads `offset[i]` once and `kernel[i]` twice | each caller kernel and callee offsets are completely initialized before the direct call/read loop | 27 live lanes / 144 bytes along either caller-callee path; no caller copy |
| `synth/sacredGeometry:sacredGeometry` | `vec2 centers[13]`; writes `{0}`, `1+k` for `k=0..<6`, `7+k` for `k=0..<6`; reads at `i,j=0..<13` | write sets `{0}`, `{1..6}`, `{7..12}` are disjoint and exhaustive before any read | 26 lanes / 104 bytes |

All fit a 64-lane structural cap, but the input audit's byte figures assume
four-byte scalar arrays and are not valid for this emitter. In particular,
Sobel is 216 native array bytes, not 144. A “256 bytes at f32 precision”
claim must not be used as the native stack-size proof.

### Canonical allocation/precision hazard omitted by the input audit

The inspected canonical JS factories allocate scalar arrays as zero-filled
plain JavaScript number arrays (`[0, ...]`) and vector arrays as arrays of
zeroed `PooledFloat32Array` vectors. The input audit instead directs the C++
emitter to leave arrays uninitialized. That direction conflicts with the
actual external oracle and creates unnecessary undefined-behavior risk if a
future proof is defective.

More importantly, the current C++ emitter intentionally lowers function-local
GLSL scalar `float` temporaries to `double` to preserve canonical JavaScript
Number precision. A generic `std::array<float,N>` would introduce a new F32
storage boundary that the canonical scalar arrays do not have. Later array
work must choose and oracle-verify `std::array<double,N>` for scalar arrays (or
document a narrow compatibility transform); it must not infer element storage
from the GLSL spelling alone. `std::array<glsl::Vec2,N>` remains F32-lane
storage and matches the canonical vector-array boundary.

Even though all six selected sources fully initialize their arrays, the
translator should both prove definite initialization and deterministically
zero-initialize emitted storage, matching the canonical allocation. Failed or
partial initialization must reject before emission rather than relying on
zeroes as a semantic fallback.

## Exact identities, define maps, defaults, and bindings for all seven

Every define map is exactly `{}`. Binding order is source declaration order;
sampler ordinals are shown explicitly.

| Key / raw source SHA-256 | Source-bound metadata defaults | Exact binding signature |
| --- | --- | --- |
| `classicNoisedeck/refract:refract` / `d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2` | `amount=50`, `blendMode=10`, `direction=0`, `mix=50 -> mixAmt`, `mode=0`, `wrap=0` | `inputTex:sampler2D@1/S1, resolution:vec2@2, tileOffset:vec2@3, fullResolution:vec2@4, time:float@5, mode:int@6, amount:float@7, direction:float@8, blendMode:int@9, mixAmt:float@10, wrap:int@11` |
| `filter/celShading:celShadingEdges` / `9c2848c92bd0f3e2de76fd065ac8fc55086cb7d209ce09ac4ba6488acda4630e` | pass-relevant `edgeWidth=1`, `edgeThreshold=0.15` | `tileOffset:vec2@1, fullResolution:vec2@2, colorTex:sampler2D@3/S1, edgeWidth:float@4, edgeThreshold:float@5, renderScale:float@6` |
| `filter/outline:outlineSobel` / `cfe848d1605f1ad693fd3ce9e518a4adf4e0f34e3fff6c6ae1ebcaec49949f5d` | `shape=1 -> sobelMetric`, `thickness=1` | `tileOffset:vec2@1, fullResolution:vec2@2, valueTexture:sampler2D@3/S1, sobelMetric:float@4, thickness:float@5, renderScale:float@6` |
| `filter/pixelSort:computeRank` / `6ce61bb5cb69bb22ac51f48603d5b40755b1e3f700acad1bc685a1e8a4dea6a4` | none for this pass | `lumTex:sampler2D@1/S1` |
| `filter/sharpen:sharpen` / `c9a9b196e61a2904b37ad89c7fc46bee1b40b6bba81293dde3d7cd37527773e7` | `amount=1` | `tileOffset:vec2@1, fullResolution:vec2@2, inputTex:sampler2D@3/S1, amount:float@4, renderScale:float@5` |
| `filter/sobel:sobel` / `ef459738b931929a65422df36f852da4e7cbe4e90387690bea747a34a2e52f84` | `amount=1`, `alpha=1` | `tileOffset:vec2@1, fullResolution:vec2@2, inputTex:sampler2D@3/S1, amount:float@4, renderScale:float@5, alpha:float@6` |
| `synth/sacredGeometry:sacredGeometry` / `24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de` | `animation=0`, `bgColor=[0,0,0]`, `fgColor=[1,1,1]`, `geometry=0`, `pulseDepth=0.15`, `rings=3`, `rotation=0`, `scale=10`, `smoothness=0.02`, `speed=1`, `starPoints=5`, `thickness=0.2` | `resolution:vec2@1, tileOffset:vec2@2, fullResolution:vec2@3, aspect:float@4, scale:float@5, rotation:float@6, thickness:float@7, smoothness:float@8, geometry:int@9, rings:int@10, starPoints:int@11, animation:int@12, speed:float@13, pulseDepth:float@14, time:float@15, fgColor:vec3@16, bgColor:vec3@17`; no sampler |

Runtime-owned values such as tile/full resolution, render scale, time, and
aspect are still mandatory exact named bindings even when they are not effect
parameters. Tests must remove and mistype each sampler and uniform by name.

## Oracle matrix for the deferred array contracts

These are implementation-time minimum variants, not pre-frozen hashes:

| Key | Required variants and why |
| --- | --- |
| `filter/sharpen:sharpen` | `defaults`; `amount_zero`; a tiled non-unit-`renderScale` case. The nine reads are unconditional; include asymmetric non-square input, flat input, and corner impulse. |
| `filter/sobel:sobel` | `defaults`; `alpha_zero`; `amount_zero`; tiled non-unit `renderScale`. Require all three indexed reads per trip and original alpha preservation. |
| `filter/celShading:celShadingEdges` | `defaults`; `edgeWidth_3_threshold_0p37`; one-pixel and wrap-sensitive corner cases. Require nine ordered stores, final `idx=9`, opaque alpha, and zero-size early-return unit coverage. |
| `filter/outline:outlineSobel` | exact `sobelMetric` values 1, 2, 3, and 4, plus wrap-sensitive and one-pixel inputs. This covers Euclidean, Manhattan, Chebyshev, and Octagram branches while repeating the nine-store proof. |
| `classicNoisedeck/refract:refract` | `defaults` (mode 0 non-array branch); `mode_1_wrap_0`; `mode_1_wrap_1`; `mode_1_wrap_2`, with contrast-rich and flat inputs. At least one mode-1 case must exercise both `derivX` and `derivY`; retain default blend 10 and add a nondefault blend branch. |
| `synth/sacredGeometry:sacredGeometry` | `geometry_1_fruit` and `geometry_3_metatron` are mandatory; metatron exercises both `centers[i]` and `centers[j]`. Also retain `defaults` (flower) and one ripple/unfold animation case. |

Every later oracle should use exact F32 and RGBA8 hashes, 12 exact F32 lane
probes, dimensions/orientation/alpha assertions, canonical factory/source
hashes, exact bindings/routes, and an immediate byte-identical repeat render.

## Array implementation hazards and required defenses

1. **Type admission must not be string-only.** Array element type, rank,
   extent, storage class, parameter direction, and source identity need frozen
   typed records. Keep vector/matrix component indexing rejected.
2. **Index proof must be attached to each index expression.** Literal,
   induction, nested-visit counter, and affine forms are different proof kinds;
   the emitter must not reconstruct them from source expressions.
3. **Definite assignment is path-sensitive.** Early returns before declaration
   are harmless; conditional bypass of a store is not. Prove exhaustive writes
   before reads and reject duplicate, missing, or post-read initialization.
4. **Array lvalues need separate emission.** The current `lvalue()` and
   assignment emitter know identifiers/swizzles but do not establish checked
   array element mutation. Do not make generic index expressions writable.
5. **Scalar precision is a compatibility boundary.** Use the external oracle
   to decide `double` versus F32 storage. The current canonical behavior favors
   `double` scalar-array elements, not the input audit's `float` assumption.
6. **Parameter ABI is separate.** Refract needs exactly a direct
   `const std::array<double,9>&`-like non-owning call edge after precision is
   verified. No copies, temporary binding, `out`/`inout`, returns, overload
   widening, or escape follow from it.
7. **Liveness must be interprocedural for array references.** Refract's caller
   kernel and callee offsets overlap; count both, not the reference itself.
   Reject recursion/cycles and arithmetic overflow in lane/byte accounting.
8. **Zero initialization is not definite-assignment fallback.** Match canonical
   deterministic allocation, but still reject an unproved read.
9. **Capability labels should name the proof.** One broad
   `fixed-local-array-index-v1` flag would falsely imply that a key admitted for
   literal reads authorizes affine writes or array parameters.
10. **Generated-code checks are necessary.** Assert no heap allocation,
    static/shared array, `.at()` exception path in the pixel body, generic
    pointer arithmetic, callback, map/string/variant lookup, or dynamic
    dispatch.

## Suggested implementation order after Task 15 acceptance

1. Task 16: `bounded-local-counter-statement-v1` — `computeRank` only.
2. Fixed-nine local literal initialization/direct read — sharpen and Sobel.
3. Nested-grid counter stores — Cel edge and Outline Sobel.
4. Refract's direct fixed-array `in` parameter.
5. Sacred Geometry's affine centers table.

Each step must update exact sorted allowlists and counts, add validator and
emitter proof-tamper negatives, freeze its own canonical oracles, preserve all
prior hashes, and leave the next proof class rejected.

## Read-only evidence

- Replayed all seven pinned sources through parse, semantic analysis, counted
  loop proof attachment, and the current capability validator.
- Enumerated every typed array declaration/parameter, index expression,
  postfix expression, loop proof, resource, and declaration-order binding.
- Checked authoritative metadata defaults and confirmed all seven define maps
  are `{}`.
- Inspected current typed emitter scalar/local type policy and C++ vector lane
  storage.
- Inspected all seven canonical JS factories for array allocation, precision
  boundaries, counter behavior, and pass bindings.
- Rendered the two proposed Task 16 canonical cases read-only and recorded
  exact hashes/probes above.
- Searched `~` to depth three for `noisemaker-for-qt`; no checkout
  was present, so no Qt implementation claim is incorporated here.

