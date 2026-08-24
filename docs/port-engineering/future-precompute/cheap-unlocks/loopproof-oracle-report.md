# Cheap-unlocks cluster 1 -- loop-proof fingerprint reuse (3 programs) oracle report

Hermetic JS oracle for the three programs that are true fingerprint-only reuses of the existing `source-global-literal-int-v1` loop-proof capability: `filter/lightLeak:lightLeak`, `filter/parallax:parallax`, `filter/reindex:nmReindexStats`. Ground truth for the future C++20 port's bit-exact parity tests.

Total cases: **14** (12 closure-exercising + 2 early-exit diagnostic).

## Defines axis

All three programs authorize the empty define map {} -- confirmed live via tools.glslcpp.generate_typed_slice._defaults(repo, key) for all three keys in this session (filter/lightLeak:lightLeak -> {}, filter/parallax:parallax -> {}, filter/reindex:nmReindexStats -> {}), and independently by reading every source file: lightLeak.glsl/parallax.glsl each contain exactly one #ifdef GL_ES guard (universal, not effect-specific), and nmReindexStats.glsl has no preprocessor directive at all. Consequently the "defines must be passed as uniforms, not preprocessed" hazard from the grade/derivative clusters cannot arise for this cluster -- stated explicitly rather than silently assumed inapplicable.

## Adapter override finding

filter/reindex:nmReindexStats's public factory (kernelFactories.get(key)) is NOT its canonical factory -- canonicalAdapterFactories overrides it with a hand-written, performance-optimized reindexStatsFactory (noisemaker-for-cpu/src/effects/adapters/f32-color.js:56-79) that hard-codes tile size 8 directly rather than reading a TILE_SIZE variable (confirmed live in loadProgram()). This generator renders exclusively through canonicalKernelFactories['filter/reindex:nmReindexStats'] (canonicalFactory120, the literal transpilation of the pinned corpus GLSL source) -- the actual porting ground truth -- never through the adapter. The adapter's independent, hand-written commitment to exactly 8 is corroborating (not authoritative) evidence that TILE_SIZE=8 is the intended value, consistent with (not a substitute for) this oracle's own proof that the canonical factory's compiled TILE_SIZE constant genuinely drives output.

## Trip-count discriminability (per program)

Per program, both mutations (an off-by-one trip count and a materially different "swap" trip count) are required to produce nonzero byte-divergence on every reach-eligible case set, and zero divergence on every non-reach-eligible (diagnostic) case -- machine-asserted at generation time, not assumed. See report for the per-mutation divergence tables.

**lightLeak**: POINT_COUNT drives how many Voronoi seed points voronoiCell() scans for its nearest-point search; a wrong count changes which point is nearest for most pixels, and hence the leak color/wormhole distortion at those pixels. Confirmed non-idempotent: both -1 and swap mutations diverge on every non-diagnostic case.

**parallax**: MARCH_STEPS drives both the ray-march loop bound and the per-step increment (stepSize = 1/MARCH_STEPS) of a root-finding search over the height field. A FIRST DESIGN (a small, same-resolution-as-canvas patterned height map) was tried and empirically REJECTED: it made the mutation a near-total no-op (only 1-2/4 cases diverged for a step-count -1 perturbation), because SHIFT_SCALE=0.15 caps the ray's total UV traversal to a fraction of one texel at that scale, so the height-vs-t curve is close to affine and the loop's own linear-interpolation refine step recovers nearly the same crossing regardless of step count -- exactly the "idempotent/saturating" trap the task warns about, caught here by verifying divergence rather than assuming it. The height map was redesigned (16x16, diagonal gradient plus ripple, full 0.05..0.95 dynamic range, see parallaxHeightMap()) to spread crossings across the whole t range and force real texel-cell boundary crossings; re-verified empirically to diverge on all 4 non-diagnostic cases for BOTH the -1 and the swap mutation before being locked in.

**reindexStats**: TILE_SIZE drives both which pixels are treated as tile anchors (fragCoord % TILE_SIZE == 0, the only pixels producing nonzero output at all) and the nested reduction loop bound; a wrong value changes the anchor grid itself, not just the aggregated min/max, so divergence is essentially guaranteed for any canvas larger than 1x1 -- confirmed for all four case sizes, including the single-tile case where TILE_SIZE still governs whether the reduction runs past the canvas edge.

## Per-program summary

| Program | Const | Original | Eligible cases | Diagnostic cases | Mutations |
| --- | --- | ---: | ---: | ---: | ---: |
| lightLeak | POINT_COUNT | 6 | 4 | 1 | 2 |
| parallax | MARCH_STEPS | 32 | 4 | 1 | 2 |
| reindexStats | TILE_SIZE | 8 | 4 | 0 | 2 |

## `filter/lightLeak:lightLeak` (lightLeak)

Source: `lightLeak/lightLeak.glsl` (5047 bytes, `61bcb2989992c109dcf73ac5b34bb4dfa7f6603b54c111a84e69b6f73a9501bb`). Canonical factory `canonicalFactory77`. Public factory is canonical: true.

Loop role: Voronoi seed count -- how many candidate cell centers voronoiCell() scans for the nearest-point search that drives the wormhole distortion, bloom, and screen-blend leak color.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| warm-leak-low-alpha | 6x5 | false | true | `07a6e971fd44737e...` | `3b3224abcbfbe60e...` |
| cool-leak-tiled-drift | 5x6 | false | true | `f53a9f96aa3e5955...` | `6693938d8f8ac3cc...` |
| high-alpha-fast-drift-negative-seed | 7x4 | false | true | `849cd7ce4848751c...` | `975838d6200949f5...` |
| boundary-tiny-alpha | 4x7 | false | true | `cee2f856e5c17316...` | `081702a559f42d17...` |
| zero-alpha-early-exit-diagnostic | 3x3 | true | false | `34abdd615a2caf19...` | `7b8ac5837c9067c1...` |

### Mutations

| Mutation | Kind | New value | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| lightLeak-point-count-minus-one | trip_count_off_by_one | 5 | 4 | 4 | 1 | 0 |
| lightLeak-point-count-swap | trip_count_swap | 3 | 4 | 4 | 1 | 0 |

- **lightLeak-point-count-minus-one**: POINT_COUNT 6 -> 5: the smallest possible wrong trip count (a classic off-by-one bound error, e.g. `<=` written instead of `<`), narrower than the "swap" mutation below.
- **lightLeak-point-count-swap**: POINT_COUNT 6 -> 3: halves the Voronoi seed count, a materially wrong trip count.

## `filter/parallax:parallax` (parallax)

Source: `parallax/parallax.glsl` (2430 bytes, `5ce5dce2ec8e8d7ebd3024c6a5bd5dcb068d0cf322bfd105c4fb3546e1b97642`). Canonical factory `canonicalFactory98`. Public factory is canonical: true.

Loop role: Ray-march step count for the parallax-occlusion search: each iteration samples the height map at a shrinking `t` and stops (with a linear refine) as soon as the ray crosses the surface. Both the iteration count AND the per-step increment (`stepSize = 1/MARCH_STEPS`) derive from this one constant.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| strong-xy-shift-march | 16x14 | false | true | `927fb6c97477995c...` | `68a5acef4462e998...` |
| reverse-direction-tiled | 16x14 | false | true | `95551eabc0980e8e...` | `8a58245041189f04...` |
| shallow-pivot-wide-shift | 24x20 | false | true | `019abaf1cd9cd4ac...` | `a0cf50d187204533...` |
| steep-pivot-negative-y | 24x20 | false | true | `1d21e6c98d2a6136...` | `4e14c58b2ee48062...` |
| loop-skipped-flat-heightmap-diagnostic | 3x3 | true | false | `34abdd615a2caf19...` | `7b8ac5837c9067c1...` |

### Mutations

| Mutation | Kind | New value | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| parallax-march-steps-minus-one | trip_count_off_by_one | 31 | 4 | 4 | 1 | 0 |
| parallax-march-steps-swap | trip_count_swap | 16 | 4 | 4 | 1 | 0 |

- **parallax-march-steps-minus-one**: MARCH_STEPS 32 -> 31: smallest possible wrong trip count.
- **parallax-march-steps-swap**: MARCH_STEPS 32 -> 16: halves the ray-march resolution, a materially wrong trip count and step size.

## `filter/reindex:nmReindexStats` (reindexStats)

Source: `reindex/nmReindexStats.glsl` (2395 bytes, `06525e054fc4910e7bc53345ad656071d2fcb33fc897f4aa35e8fc59b6f0b951`). Canonical factory `canonicalFactory120`. Public factory is canonical: false.

**Adapter override present**: `reindexStatsFactory`, independently confirmed hard-coded to tile size 8. See adapter override finding above.

Loop role: Per-tile min/max lightness reduction window: TILE_SIZE governs BOTH which pixels are "tile anchors" (`fragCoord % TILE_SIZE == 0`, the only pixels that run the reduction at all) AND the nested loop bound of the reduction itself, so a wrong value changes which pixels carry output at all, not just the aggregated value.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| single-tile-small | 6x5 | false | true | `403f6472864b9120...` | `bace24b546c4739e...` |
| exact-multiple-tiles | 16x8 | false | true | `25cc3cc613481751...` | `d2288cc97b270e81...` |
| partial-edge-tile | 9x9 | false | true | `4f4da78b444e6118...` | `f32f0458ee8edcbf...` |
| multi-tile-tiled-offset | 20x17 | false | true | `23918ad257b39af4...` | `b292785463dda92c...` |

### Mutations

| Mutation | Kind | New value | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| reindexStats-tile-size-minus-one | trip_count_off_by_one | 7 | 4 | 3 | 0 | 0 |
| reindexStats-tile-size-swap | trip_count_swap | 4 | 4 | 4 | 0 | 0 |

- **reindexStats-tile-size-minus-one**: TILE_SIZE 8 -> 7: smallest possible wrong trip count, also shifts which pixels are tile anchors. _Note: Only 3/4 reach-eligible cases diverged -- investigated, see report._
- **reindexStats-tile-size-swap**: TILE_SIZE 8 -> 4: halves the tile window, a materially wrong trip count and a materially different anchor grid.

## Negative closure

- **dither_or_reindexReduce_or_mandelbrot_included**: refused -- dither does not structurally qualify (FS_ERR_W initializer.kind is `binary`, not `literal`); reindexReduce and mandelbrot qualify structurally but additionally need a budget-cap increase, so they are not fingerprint-only reuses and are out of this cluster's scope per the task brief.
- **idempotent_or_saturating_cases_used_as_proof**: refused -- every mutation asserts nonzero divergence among reach-eligible cases at build time; a case set that failed to discriminate would throw, not ship silently. parallax in particular was designed with a non-flat, per-pixel-varying height map specifically because a flat/constant height field would make the ray-march search converge to the same crossing point regardless of step count (verified: the flat-diagnostic case exists precisely to demonstrate this, and is excluded from the discriminating case set).
- **canonicalAdapterFactories_reindexStatsFactory_used_as_ground_truth**: refused -- see adapter_override_note. The oracle renders exclusively through canonicalKernelFactories, never through kernelFactories (which would silently prefer the adapter for this one program).

