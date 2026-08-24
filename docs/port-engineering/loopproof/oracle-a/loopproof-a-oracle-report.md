# Loop-proof cluster oracle-a report

Hermetic JS oracle for eight programs blocked on the counted-loop program-proof gate. Ground truth for the future C++20 port's bit-exact parity tests, once each program's loop-proof gate clears.

Programs covered with a full discriminating oracle: **7**. Programs that could not be covered: **1** (`filter/dither:dither` -- see below).

Total cases across the seven covered programs: **32** (29 closure-exercising + 3 diagnostic). Total mutations: **14**.

## Per-program summary

| Program | Cases | Diagnostic | Mutations | All mutations diverge on >=1 reach-eligible case |
| --- | ---: | ---: | ---: | --- |
| blurH | 4 | 1 | 2 | true |
| blurV | 4 | 1 | 2 | true |
| statsFinal | 4 | 0 | 2 | true |
| oilFlatten | 5 | 0 | 2 | true |
| smoothBlend | 2 | 1 | 2 | true |
| zoomBlur | 5 | 0 | 2 | true |
| tetraColorArray | 5 | 0 | 2 | true |
| dither | -- | -- | -- | **UNCOVERABLE -- see below** |

## `filter/blur:blurH` (blurH)

Source: `blurH.glsl` (1120 bytes, `c4283e820b2ade9148358ad4582d350bc7f4a5ccb5fc60f2e1b76bcda58deecc`). Canonical factory `canonicalFactory24`. Public factory is canonical: true. Defines: `{}`.

Loop role: Horizontal Gaussian-blur tap radius: `radius = int(radiusX*renderScale)` drives both the loop bound `[-radius, radius]` and `sigma = radius/3`, so a wrong trip count changes which texels are summed without changing the weighting curve itself.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| radius5-wide | 12x10 | false | {"default":true} | `54e1d3b2b19ca86b...` | `8147355d59597b32...` |
| radius4-tall | 10x12 | false | {"default":true} | `6a161fa0b1a04b5d...` | `62fc60bee3144f31...` |
| radius3-tiled | 16x14 | false | {"default":true} | `20d7ef6de3925ee0...` | `932614901331c872...` |
| radius6-scaled-square | 9x9 | false | {"default":true} | `e8e645cf6fb4bfd9...` | `85fec26224ba241b...` |
| radius0-early-exit-diagnostic | 5x5 | true | {"default":false} | `28b19de7923b14d8...` | `134d13e4a5f76500...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| blurH-tap-radius-off-by-one | trip_count_off_by_one | 4 | 4 | 1 | 0 |
| blurH-tap-radius-swap | trip_count_swap | 4 | 4 | 1 | 0 |

- **blurH-tap-radius-off-by-one**: Drop the `i<=radius` upper bound to `i<radius`: the smallest possible wrong trip count, dropping exactly the `+radius` tap while leaving `-radius..radius-1` and sigma untouched.
- **blurH-tap-radius-swap**: Shrink the upper bound by 2 (`radius-2`): a materially wrong, asymmetric trip count that drops multiple outer taps while sigma (still computed from the true radius) stays fixed.

## `filter/blur:blurV` (blurV)

Source: `blurV.glsl` (1118 bytes, `cc33343032b34e1ede6eed15fbdcb9229ad64484a092b2914065b09fa957fb9b`). Canonical factory `canonicalFactory25`. Public factory is canonical: true. Defines: `{}`.

Loop role: Vertical Gaussian-blur tap radius -- byte-identical shape to blurH, transposed to the Y axis.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| radius5-wide | 12x10 | false | {"default":true} | `0dfd8249fd2ff783...` | `393ae1b8c42562e9...` |
| radius4-tall | 10x12 | false | {"default":true} | `c0d191323ee85023...` | `192bb2b78f47d690...` |
| radius3-tiled | 16x14 | false | {"default":true} | `f361c51e53cf0ca5...` | `3f3016cc42185258...` |
| radius6-scaled-square | 9x9 | false | {"default":true} | `e7851fe465afdfb5...` | `22e733cb8b422bac...` |
| radius0-early-exit-diagnostic | 5x5 | true | {"default":false} | `e082b2bc668de2cb...` | `2662d9a7f2441233...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| blurV-tap-radius-off-by-one | trip_count_off_by_one | 4 | 4 | 1 | 0 |
| blurV-tap-radius-swap | trip_count_swap | 4 | 4 | 1 | 0 |

- **blurV-tap-radius-off-by-one**: Same off-by-one shape as blurH, transposed to Y.
- **blurV-tap-radius-swap**: Same swap shape as blurH, transposed to Y.

## `filter/normalize:statsFinal` (statsFinal)

Source: `statsFinal.glsl` (959 bytes, `0b8daf6d5a38dc34bbd98800fdd46f9cdfa0b97f00196382023456a0b6eb1dfa`). Canonical factory `canonicalFactory90`. Public factory is canonical: true. Defines: `{}`.

Loop role: Full-image min/max reduction: nested `y<inSize.y`/`x<inSize.x` loops scan every texel of `inputTex`, taking the R-channel running min and G-channel running max. A wrong bound silently drops rows/columns from the reduction with no visible error signal other than a wrong min/max.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| min-in-first-topdown-row | 6x5 | false | {"default":true} | `0a3a3cdb6c98b02d...` | `06708e7706b5d03c...` |
| max-in-last-topdown-col | 9x7 | false | {"default":true} | `bfde549ab5f41942...` | `457aee5b96f94152...` |
| min-and-max-share-first-row | 8x6 | false | {"default":true} | `81744fbabb941db4...` | `fd6a78c6e25b1d01...` |
| square-canvas | 10x10 | false | {"default":true} | `392909983ad844f9...` | `2ef2461707f163eb...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| statsFinal-y-bound-off-by-one | trip_count_off_by_one | 4 | 3 | 0 | 0 |
| statsFinal-x-bound-off-by-one | trip_count_off_by_one | 4 | 3 | 0 | 0 |

- **statsFinal-y-bound-off-by-one**: Drop the LAST y-iteration (shader-y = inSize.y-1). texelFetch flips Y, so this is exactly the FIRST top-down data row -- undershoots the reduction by one full row. _Note: Only 3/4 reach-eligible cases diverged -- the remaining reach-eligible case(s) were engineered for a DIFFERENT mutation in this program (see design note) and are not expected to diverge under this one._
- **statsFinal-x-bound-off-by-one**: Drop the LAST x-iteration (column inSize.x-1, unaffected by the Y flip) -- undershoots the reduction by one full column. _Note: Only 3/4 reach-eligible cases diverged -- the remaining reach-eligible case(s) were engineered for a DIFFERENT mutation in this program (see design note) and are not expected to diverge under this one._

## `filter/oilPaint:oilFlatten` (oilFlatten)

Source: `oilFlatten.glsl` (7321 bytes, `f2f512b35b846d8a15362739a843c162199b7c53d95251918576726b1b094690`). Canonical factory `canonicalFactory92`. Public factory is canonical: true. Defines: `{"MODE":1}`.

Loop role: 8-sector Kuwahara-style oil-paint sample window: `sampleLimit = ceil(clamp(radius,1,12))` drives the nested `[-sampleLimit,sampleLimit]^2` scan that buckets neighbors into 8 octant accumulators; the octant with lowest color variance is chosen as the flattened output. A wrong trip count changes octant membership counts and variances, hence which octant (and mean color) wins.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| radius6-wide | 10x9 | false | {"default":true} | `53742d7a422d46d5...` | `941015713afa712c...` |
| radius8-tall | 9x10 | false | {"default":true} | `727f1e12671c63f6...` | `613ae8b2061a263b...` |
| radius4-square | 12x12 | false | {"default":true} | `4e33ff22aa40044a...` | `fde531022ad1f920...` |
| radius10-tiled | 14x13 | false | {"default":true} | `7c5d2d03c0871f78...` | `c9e720d2b3eedbb3...` |
| small-radius3-tight-window | 11x11 | false | {"default":true} | `a56b5f871e28b479...` | `89ff6872c4eed220...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| oilFlatten-sample-window-off-by-one | trip_count_off_by_one | 5 | 5 | 0 | 0 |
| oilFlatten-sample-window-swap | trip_count_swap | 5 | 5 | 0 | 0 |

- **oilFlatten-sample-window-off-by-one**: Drop the `x<=sampleLimit` upper bound to `x<sampleLimit`: smallest possible wrong trip count, removing the rightmost column of the sample window from every octant tally.
- **oilFlatten-sample-window-swap**: Shrink BOTH loop upper bounds by 2: a materially wrong, asymmetric window that drops a whole outer ring from the bottom-right of the octant scan.

## `filter/smooth:smoothBlend` (smoothBlend)

Source: `smoothBlend.glsl` (6858 bytes, `c317194f9bbdba9d95c5dcae47e2354221cf0cdb05ffcf14e335a94a4ef3729c`). Canonical factory `canonicalFactory139`. Public factory is canonical: true. Defines: `{}`.

Loop role: `searchEdge()`'s SMAA-style edge-distance search (`for(i=1;i<=32;i++){ if(i>searchSteps) break; ...; if(edge<0.5) return i-1; }`) is the ONE loop in this program's blocked set (per loop-proof-study SS2/SS7: start/bound/update are already fully canonical -- the sole violation is the blanket "any return in body" veto, not the bound itself). The hard cap of 32 only matters when `searchSteps>=`(the mutated cap) AND the nearest same-orientation edge is farther than the mutated cap but within 32 -- both engineered explicitly in the cases below (see design note).

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| edge-distance-20-swap-target | 40x6 | false | {"default":true} | `5f074f62d6b2a4c3...` | `70cbc41f57c229f7...` |
| edge-distance-32-off-by-one-target | 40x6 | false | {"default":true} | `625350d2b92272b9...` | `ac9f54f2619d3437...` |
| msaa-mode-diagnostic-non-reaching | 8x7 | true | {"default":false} | `03507b8dc53d7354...` | `ed77293baa2966e9...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| smoothBlend-searchEdge-cap-off-by-one | trip_count_off_by_one | 2 | 1 | 1 | 0 |
| smoothBlend-searchEdge-cap-swap | trip_count_swap | 2 | 2 | 1 | 0 |

- **smoothBlend-searchEdge-cap-off-by-one**: Drop the hard cap from 32 to 31: at search distance exactly 32 (the `edge-distance-32-off-by-one-target` case), the mutated search never reaches the edge and falls through to `return searchSteps`, diverging from the real `return 31`. _Note: Only 1/2 reach-eligible cases diverged -- the remaining reach-eligible case(s) were engineered for a DIFFERENT mutation in this program (see design note) and are not expected to diverge under this one._
- **smoothBlend-searchEdge-cap-swap**: Halve the hard cap to 16: at search distance 20 (the `edge-distance-20-swap-target` case), the mutated search never reaches the edge and falls through to `return searchSteps`, diverging from the real `return 19`.

## `filter/zoomBlur:zoomBlur` (zoomBlur)

Source: `zoomBlur.glsl` (1496 bytes, `3b24e68c6aec2161bbac73f5cac3d21e658531fff6a365ae78a4982179a707bd`). Canonical factory `canonicalFactory182`. Public factory is canonical: true. Defines: `{}`.

Loop role: Radial zoom-blur sample count: `for(t=0;t<=40;t++)` (float induction, the loop-proof-study shape this program is blocked on) drives a 41-tap parabolic-weighted radial sample average. A wrong trip count drops samples asymmetrically across the `percent=(t+offset)/40` parabola, changing both the weighted color sum and the normalizing `total`.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| moderate-strength-wide | 12x10 | false | {"default":true} | `71ba1cdbe602acc7...` | `274ec8ae29b164a8...` |
| strong-strength-tall | 10x12 | false | {"default":true} | `d2fc016eb42e0fce...` | `20e5b4c9c2d43b8a...` |
| weak-strength-tiled | 16x14 | false | {"default":true} | `ebbf972233c25ceb...` | `b717c87ca9cd47df...` |
| large-strength-square | 9x9 | false | {"default":true} | `4cf1885db024c940...` | `4ffbf9c084b70ad8...` |
| zero-strength-uniform-sampling | 5x5 | false | {"default":true} | `7a28fbe1981ea48e...` | `5c2ad9cd988968c2...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| zoomBlur-sample-count-off-by-one | trip_count_off_by_one | 5 | 5 | 0 | 0 |
| zoomBlur-sample-count-swap | trip_count_swap | 5 | 5 | 0 | 0 |

- **zoomBlur-sample-count-off-by-one**: Drop the `t<=40` upper bound to `t<40`: smallest possible wrong trip count, dropping the t=40 sample (percent=1, the parabola's other zero-weight endpoint -- still touches `total` at float32 precision because `offset` is nonzero).
- **zoomBlur-sample-count-swap**: Halve the sample count to 21 taps (t=0..20): a materially wrong trip count that drops the entire back half of the parabola, including its highest-weight taps near t=20..40.

## `filter/tetraColorArray:tetraColorArray` (tetraColorArray)

Source: `tetraColorArray.glsl` (9754 bytes, `68c7cabce311a0a05ba116ce8d34bd5e70e0c09bfb8eab06c93f4f9e01fa5438`). Canonical factory `canonicalFactory158`. Public factory is canonical: true. Defines: `{}`.

Loop role: `sampleColorArray()`'s `for(i=1;i<count;i++)` blends across `count-1` palette-stop boundaries (`count` = the `colorCount` uniform, a parameter-bound loop per loop-proof-study SS2). A wrong trip count skips the transition into the last color stop(s), changing the gradient color at any luminance `t` past the dropped boundary.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| four-stops-wide | 10x9 | false | {"default":true} | `a7147193169cd6e0...` | `797b7f5bd55e44f2...` |
| six-stops-tall | 9x10 | false | {"default":true} | `f44ec66ea149da29...` | `e126df6c470a88af...` |
| eight-stops-square | 12x8 | false | {"default":true} | `73f53d1142e2f510...` | `3123fec6f3ffe832...` |
| three-stops-small | 8x8 | false | {"default":true} | `dde94fd923a3ca29...` | `3f9bfd65a6f49970...` |
| two-stops-minimal | 6x6 | false | {"default":true} | `48d14e7adde7aeb1...` | `a861244aa15c89d8...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| tetraColorArray-stop-count-off-by-one | trip_count_off_by_one | 5 | 4 | 0 | 0 |
| tetraColorArray-stop-count-swap | trip_count_swap | 5 | 5 | 0 | 0 |

- **tetraColorArray-stop-count-off-by-one**: Drop the last blend iteration (`i<count-1`): smallest possible wrong trip count, skipping the transition into the final color stop. _Note: Only 4/5 reach-eligible cases diverged -- the remaining reach-eligible case(s) were engineered for a DIFFERENT mutation in this program (see design note) and are not expected to diverge under this one._
- **tetraColorArray-stop-count-swap**: Drop the last three blend iterations (`i<count-3`, clamped to 0 iterations in JS whenever count<=3): a materially wrong trip count, verified to diverge from colorCount=2 upward.

## `filter/dither:dither` -- UNCOVERABLE

UNRENDERABLE, not merely non-discriminating -- verified live, not assumed. All three of this program's blocked loop-proof sites (the FS_ERR_W-bound fill loop, and the two "-FS_APRON_MAX" symmetric-window r/c loops -- loop-proof-study SS2/SS4) live exclusively inside errorDiffusion(), reachable only when ditherType==DITHER_ERROR_DIFFUSION(7). The CURRENT PINNED canonical-kernels.js (sha256 e605746c...98815ab56, the same hash independently verified by every other oracle in this audited family) compiles errorDiffusion()'s array-fill loop as `fsSeedNoise(...).reduce((res,el,i)=>(res[i]=el,res), errRow[i])` -- passing the not-yet-assigned `errRow[i]` (undefined, since `errRow` starts as `[]`) as reduce's INITIAL accumulator, which throws `TypeError: Cannot set properties of undefined (setting '0')` on the very first loop iteration (i=0), for EVERY canvas size and EVERY uniform combination -- confirmed with a minimal isolated repro of the exact reduce-into-undefined pattern (see report). This is 100% reproducible, unconditional, and independent of any loop-bound mutation: the reference JS this oracle must treat as ground truth does not produce ANY output for the one branch containing this program's blocked loops, so no render-level trip-count discrimination can be demonstrated -- not because the loops fail to discriminate, but because the reference crashes before either the real or the mutated factory can be compared. This is a genuine, independently-discovered defect in noisemaker-for-cpu (most likely a glsl-transpiler code-generation gap for first-time GLSL fixed-array element writes, distinct from and orthogonal to the C++ loop-proof gate this cluster exists to unblock) -- out of scope to fix here per the task's explicit prohibition on modifying noisemaker-for-cpu. Confirmed the crash is isolated to this one function: `errorDiffusion` occurs exactly once in canonical-kernels.js, and the existing test suite (test/canonical-kernel-smoke.test.js) only ever exercises dither at its DEFAULT (Bayer, non-error-diffusion) dither type, so this defect was never previously exercised or caught.

### Live evidence captured by this generator

- Isolated repro of the exact compiled `.reduce(callback, arr[notYetSet])` pattern threw: **true** (`Cannot set properties of undefined (setting '0')`)
- Full-pipeline render attempts at `ditherType=DITHER_ERROR_DIFFUSION(7)` across 3 unrelated canvas sizes/uniform sets: 3/3 threw, all with the identical message `Cannot set properties of undefined (setting '0')`
- Same factory, `ditherType=DITHER_BAYER_2X2(0)`, renders successfully: finite_lanes=120, nonfinite_lanes=0 -- proves the defect is isolated to `errorDiffusion()`, not a general breakage of this program or a hermeticity mistake in this generator.

