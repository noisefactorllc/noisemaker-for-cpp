# Task 32 `filter/grade` cluster closure oracle report

Six programs, six independent GLSL sources, sharing only `effect_id: "filter/grade"`. Authorized define map for all six: `{}`.

Total cases: **29** (24 closure-exercising + 5 early-exit diagnostic). All cases `eligible_for_native_binding: true` -- see `defines_axis_note`.

## Defines axis

All six grade programs compile with exact defines {} -- confirmed live via tools.glslcpp.generate_typed_slice._defaults(repo, key) for all six keys, and independently by grep: the only preprocessor directive in any of the six sources is the universal `#ifdef GL_ES` guard (no #define/#ifdef of any effect-specific macro exists, unlike synth/curl's OCTAVES/OUTPUT_MODE/RIDGES). Consequently there is no "different define map" axis from which to construct an ineligible-by-define case for this cluster -- every full-render case below is eligible_for_native_binding: true by construction, and this is stated explicitly rather than fabricating a synthetic ineligible case that would not reflect anything real.

## Two capability shapes

**global_admission**: const vec3 LUMA_WEIGHTS = vec3(0.2126, 0.7152, 0.0722) -- present in primary, hslSecondary (dead), wheels, vignette, creative; absent from lut (which inlines the literal as a dot() argument in luma(), confirmed: zero `const` declarations in lut.glsl).

**index_expression_admission**: for-loop-induction-variable-indexed read AND write of a local vec3 lane (e.g. `linear[i] = srgb[i] / 12.92;`) -- 74 sites total across the six programs per the frozen brief; this oracle exercises the shared srgbToLinear/linearToSrgb pair (present in all six) plus the two program-specific extra closures (hslToRgb write-only in hslSecondary; lutHardLight/lutSolarize in lut).

## Per-program summary

| Program | Has global | Global dead | Eligible cases | Diagnostic cases | Mutations |
| --- | --- | --- | ---: | ---: | ---: |
| primary | true | false | 4 | 0 | 3 |
| hslSecondary | true | true | 4 | 1 | 4 |
| wheels | true | false | 4 | 1 | 3 |
| vignette | true | false | 4 | 1 | 3 |
| creative | true | false | 4 | 1 | 3 |
| lut | false | false | 4 | 1 | 4 |

## `filter/grade:primary`

Source: `primary.glsl` (5839 bytes, `008521bf82834ef55383a492adacb259964170831c92d6c9ddc6368acc850cc2`). Canonical factory `canonicalFactory62` (`b8beeb5acc689dcd3bc09c6347c9b6994267f08fec07bf3a19a72e898f009f46`).

Global `LUMA_WEIGHTS`: read by applyContrast, applyTonalRanges, applyCurve, applySaturation.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| cool-shadow-lift | 6x5 | false | {"index":true,"global":true} | `39436668171c1681...` | `5237b575f0c374c9...` |
| warm-highlight-punch | 5x6 | false | {"index":true,"global":true} | `ce8b1ea091132a73...` | `d3d7efda6e9fc338...` |
| extreme-maxima | 7x4 | false | {"index":true,"global":true} | `9e7a6c906be4531c...` | `97c1cbcf7d2ee6a8...` |
| extreme-minima-tiled | 4x7 | false | {"index":true,"global":true} | `362e76d498e77dad...` | `d25d9cb77c3d534d...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| primary-luma-weights-bt601-swap | global | global | 1 | 4 | 4 | 0 | 0 | nonzero |
| primary-srgbToLinear-write-index-transpose | index | index | 2 | 4 | 4 | 0 | 0 | nonzero |
| primary-linearToSrgb-constant-induction | index | index | 5 | 4 | 4 | 0 | 0 | nonzero |

- **primary-luma-weights-bt601-swap**: Swap LUMA_WEIGHTS from BT.709 (0.2126/0.7152/0.0722) to BT.601 (0.299/0.587/0.114) -- a plausible-looking but wrong luma-weight constant, the exact shape of bug the global_admission profile must prevent silently compiling.
- **primary-srgbToLinear-write-index-transpose**: srgbToLinear: transpose the WRITE index from linear[i] to linear[(i+2)%3] while leaving the srgb[i] READ untouched -- a cyclic lane-swap bug the index_expression_admission profile must prevent silently compiling.
- **primary-linearToSrgb-constant-induction**: linearToSrgb: replace every loop-induction-variable subscript [i] with the constant [0] -- both the READ (linear[i]) and WRITE (srgb[i]) collapse onto lane 0, leaving lanes 1/2 at their zero-initialized value. Exactly the "replace the induction variable with a constant" shape the brief calls out.

### Direct rows: `srgb_to_linear_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).

### Direct rows: `linear_to_srgb_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).


## `filter/grade:hslSecondary`

Source: `hslSecondary.glsl` (4975 bytes, `2f2c54a6d977ccc0ba8657c02f1fc2fecfb576ad85f6d03ea16468fc9cbd095a`). Canonical factory `canonicalFactory60` (`df65c190f706d88e73c63f143636c74e371c860ebe9fbbdcc6978a67134900ce`).

Global `LUMA_WEIGHTS`: **DEAD** -- zero live reads (expected-dead confirmation, not a coverage gap).

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| key-reds-boost-sat | 6x5 | false | {"index":true,"global":false} | `44583aadcab49d93...` | `f35a0aa2d39917a3...` |
| key-greens-desaturate | 5x6 | false | {"index":true,"global":false} | `02c3180f9befcfdc...` | `af65cb8365b5b4c3...` |
| wide-key-max-shift | 7x4 | false | {"index":true,"global":false} | `9d99db5d9e7344ed...` | `a62f238d591be89a...` |
| narrow-key-negative-shift-tiled | 4x7 | false | {"index":true,"global":false} | `5103910775abe5e5...` | `218bdefe9b534c9b...` |
| disabled-early-exit-diagnostic | 3x3 | true | {"index":false,"global":false} | `b9dd327ff132395e...` | `cd1cec902f56b28c...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| hslSecondary-luma-weights-bt601-swap | global | global | 1 | 0 | 0 | 5 | 0 | ZERO (dead code) |
| hslSecondary-srgbToLinear-write-index-transpose | index | index | 2 | 4 | 4 | 1 | 0 | nonzero |
| hslSecondary-linearToSrgb-constant-induction | index | index | 5 | 4 | 4 | 1 | 0 | nonzero |
| hslSecondary-hslToRgb-write-index-transpose | index | index | 4 | 4 | 3 | 1 | 0 | nonzero |

- **hslSecondary-luma-weights-bt601-swap**: Swap LUMA_WEIGHTS from BT.709 (0.2126/0.7152/0.0722) to BT.601 (0.299/0.587/0.114) -- a plausible-looking but wrong luma-weight constant, the exact shape of bug the global_admission profile must prevent silently compiling.
- **hslSecondary-srgbToLinear-write-index-transpose**: srgbToLinear: transpose the WRITE index from linear[i] to linear[(i+2)%3] while leaving the srgb[i] READ untouched -- a cyclic lane-swap bug the index_expression_admission profile must prevent silently compiling.
- **hslSecondary-linearToSrgb-constant-induction**: linearToSrgb: replace every loop-induction-variable subscript [i] with the constant [0] -- both the READ (linear[i]) and WRITE (srgb[i]) collapse onto lane 0, leaving lanes 1/2 at their zero-initialized value. Exactly the "replace the induction variable with a constant" shape the brief calls out.
- **hslSecondary-hslToRgb-write-index-transpose**: hslToRgb: transpose the WRITE index from rgb[i] to rgb[(i+1)%3] on all four per-lane branches. hslToRgb is the one write-only index site in this cluster (it never reads rgb[i]) -- this mutation is the program-specific closure beyond the shared srgbToLinear/linearToSrgb pair. _Note: One reach-eligible case ("narrow-key-negative-shift-tiled", hslSatAdjust=-1) is expected and confirmed to NOT diverge under this mutation: hslToRgb itself has its own internal early return (`if (s < 0.001) return vec3(l,l,l);`) that the coarse hslEnable!=0 reach flag does not model. That case's hslSatAdjust=-1 clamps corrected saturation to exactly 0 for every pixel, so the per-lane indexed loop this mutation targets never executes for that case -- the mutation still needs and gets nonzero divergence overall (3/4), so it remains a genuine discriminator; this is a documented reach-granularity nuance, not a failure to discriminate._

### Direct rows: `srgb_to_linear_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).

### Direct rows: `linear_to_srgb_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).

### Direct rows: `hsl_to_rgb_rows`

5 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).


## `filter/grade:wheels`

Source: `wheels.glsl` (3529 bytes, `fa9c411096816263985e8d5ef82ade976667a6cadecf8929ecd185edbc71f479`). Canonical factory `canonicalFactory64` (`0ea06a78c7c12757581c8e1776a29da21beccf0ccd461ac07d3c461546e913ef`).

Global `LUMA_WEIGHTS`: read by applyWheels.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| shadow-cool-highlight-warm | 6x5 | false | {"index":true,"global":true} | `943d7872d0867ba6...` | `2d40937432181240...` |
| midtone-push-magenta | 5x6 | false | {"index":true,"global":true} | `bc27a6ed3467b84d...` | `4f342f8e265c1f2f...` |
| extreme-all-wheels | 7x4 | false | {"index":true,"global":true} | `3167b8cd48b3a981...` | `001e3455dde6a8f9...` |
| gentle-all-wheels-negative-balance-tiled | 4x7 | false | {"index":true,"global":true} | `717d6ccad3d7811e...` | `25abd767d861df82...` |
| neutral-wheels-global-skip-diagnostic | 3x3 | true | {"index":true,"global":false} | `ac391099d0d48d38...` | `fcf49e4663340e97...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| wheels-luma-weights-bt601-swap | global | global | 1 | 4 | 4 | 1 | 0 | nonzero |
| wheels-srgbToLinear-write-index-transpose | index | index | 2 | 5 | 5 | 0 | 0 | nonzero |
| wheels-linearToSrgb-constant-induction | index | index | 5 | 5 | 5 | 0 | 0 | nonzero |

- **wheels-luma-weights-bt601-swap**: Swap LUMA_WEIGHTS from BT.709 (0.2126/0.7152/0.0722) to BT.601 (0.299/0.587/0.114) -- a plausible-looking but wrong luma-weight constant, the exact shape of bug the global_admission profile must prevent silently compiling.
- **wheels-srgbToLinear-write-index-transpose**: srgbToLinear: transpose the WRITE index from linear[i] to linear[(i+2)%3] while leaving the srgb[i] READ untouched -- a cyclic lane-swap bug the index_expression_admission profile must prevent silently compiling.
- **wheels-linearToSrgb-constant-induction**: linearToSrgb: replace every loop-induction-variable subscript [i] with the constant [0] -- both the READ (linear[i]) and WRITE (srgb[i]) collapse onto lane 0, leaving lanes 1/2 at their zero-initialized value. Exactly the "replace the induction variable with a constant" shape the brief calls out.

### Direct rows: `srgb_to_linear_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).

### Direct rows: `linear_to_srgb_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).


## `filter/grade:vignette`

Source: `vignette.glsl` (4133 bytes, `740ad849a37c99d87962a376c2e618b24248dc4b2799066aaf6364861727c1fa`). Canonical factory `canonicalFactory63` (`2470f6f7e0c46c41dc199a37862c7ac4de676716695b3237b91f9f15d4a58e9d`).

Global `LUMA_WEIGHTS`: read by applyVignette (inside `if (highlightProtect > 0.0)`).

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| darken-circle-highlight-protect | 6x5 | false | {"index":true,"global":true} | `5fee38f04bfa3d6b...` | `763453eef7385809...` |
| lighten-ellipse-no-protect | 5x6 | false | {"index":true,"global":false} | `6b09ebee75bfef62...` | `b0bda5f5432fe5fc...` |
| extreme-max-tiled-highlight-protect | 7x4 | false | {"index":true,"global":true} | `ba21678d7ac7b41c...` | `f911792a0161a11c...` |
| extreme-minima-highlight-protect | 4x7 | false | {"index":true,"global":true} | `f287bf6cdb419e70...` | `ab54ff9128a21c42...` |
| near-zero-amount-early-exit-diagnostic | 3x3 | true | {"index":false,"global":false} | `577445a717a537f3...` | `bb764dcd195d585c...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| vignette-luma-weights-bt601-swap | global | global | 1 | 3 | 3 | 2 | 0 | nonzero |
| vignette-srgbToLinear-write-index-transpose | index | index | 2 | 4 | 4 | 1 | 0 | nonzero |
| vignette-linearToSrgb-constant-induction | index | index | 5 | 4 | 4 | 1 | 0 | nonzero |

- **vignette-luma-weights-bt601-swap**: Swap LUMA_WEIGHTS from BT.709 (0.2126/0.7152/0.0722) to BT.601 (0.299/0.587/0.114) -- a plausible-looking but wrong luma-weight constant, the exact shape of bug the global_admission profile must prevent silently compiling.
- **vignette-srgbToLinear-write-index-transpose**: srgbToLinear: transpose the WRITE index from linear[i] to linear[(i+2)%3] while leaving the srgb[i] READ untouched -- a cyclic lane-swap bug the index_expression_admission profile must prevent silently compiling.
- **vignette-linearToSrgb-constant-induction**: linearToSrgb: replace every loop-induction-variable subscript [i] with the constant [0] -- both the READ (linear[i]) and WRITE (srgb[i]) collapse onto lane 0, leaving lanes 1/2 at their zero-initialized value. Exactly the "replace the induction variable with a constant" shape the brief calls out.

### Direct rows: `srgb_to_linear_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).

### Direct rows: `linear_to_srgb_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).


## `filter/grade:creative`

Source: `creative.glsl` (4230 bytes, `b043aa43d17e098ffb736f16e6c81a5ca422ecdd6fc37fef03c39b01cc939bd3`). Canonical factory `canonicalFactory59` (`b5b99c6a5951ea7d68dbd6a58d6dc303393c95aa80aaa7f7a3de866e32530779`).

Global `LUMA_WEIGHTS`: read by applyVibrance, applyFadedFilm, applySplitTone.

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| boost-vibrance-lift-blacks-tint | 6x5 | false | {"index":true,"global":true} | `157385988133f03d...` | `741f41d8450d1465...` |
| desaturate-vibrance-heavy-fade | 5x6 | false | {"index":true,"global":true} | `1bd8730580872738...` | `7f4b78db7c299f70...` |
| extreme-maxima | 7x4 | false | {"index":true,"global":true} | `0e2d8edaab78b241...` | `87f6e7c2ac2f3aef...` |
| extreme-minima-tiled | 4x7 | false | {"index":true,"global":true} | `3806cc20ed60e0b7...` | `0135bde68671fcf4...` |
| all-neutral-global-skip-diagnostic | 3x3 | true | {"index":true,"global":false} | `9131b570788890e9...` | `dffb307d9dd359e8...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| creative-luma-weights-bt601-swap | global | global | 1 | 4 | 4 | 1 | 0 | nonzero |
| creative-srgbToLinear-write-index-transpose | index | index | 2 | 5 | 5 | 0 | 0 | nonzero |
| creative-linearToSrgb-constant-induction | index | index | 5 | 5 | 5 | 0 | 0 | nonzero |

- **creative-luma-weights-bt601-swap**: Swap LUMA_WEIGHTS from BT.709 (0.2126/0.7152/0.0722) to BT.601 (0.299/0.587/0.114) -- a plausible-looking but wrong luma-weight constant, the exact shape of bug the global_admission profile must prevent silently compiling.
- **creative-srgbToLinear-write-index-transpose**: srgbToLinear: transpose the WRITE index from linear[i] to linear[(i+2)%3] while leaving the srgb[i] READ untouched -- a cyclic lane-swap bug the index_expression_admission profile must prevent silently compiling.
- **creative-linearToSrgb-constant-induction**: linearToSrgb: replace every loop-induction-variable subscript [i] with the constant [0] -- both the READ (linear[i]) and WRITE (srgb[i]) collapse onto lane 0, leaving lanes 1/2 at their zero-initialized value. Exactly the "replace the induction variable with a constant" shape the brief calls out.

### Direct rows: `srgb_to_linear_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).

### Direct rows: `linear_to_srgb_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).


## `filter/grade:lut`

Source: `lut.glsl` (13745 bytes, `0a8a3ae4d2a14142ae7d53373bfac6ac87a0b175dff132d71cd80e6226f9ec40`). Canonical factory `canonicalFactory61` (`d4e69f82c63b29797a6b5450cb65c291f6e377a2043f10c785d5a5b49b5f8abe`).

No global constant in this program (literal inlined directly into `luma()`'s `dot()` call).

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| hardlight-preset | 6x5 | false | {"index":true,"srgbPair":true,"hardLight":true,"solarize":false} | `0ac4637612f67a6a...` | `268fc2f573e26aa5...` |
| solarize-preset | 5x6 | false | {"index":true,"srgbPair":true,"hardLight":false,"solarize":true} | `b715d384f5e62c31...` | `bc7f14de71f5e10f...` |
| tealorange-preset-full-blend | 7x4 | false | {"index":true,"srgbPair":true,"hardLight":false,"solarize":false} | `5cef05fc15026a52...` | `aaf84441c392d462...` |
| vintage-partial-blend-tiled | 4x7 | false | {"index":true,"srgbPair":true,"hardLight":false,"solarize":false} | `8156e52a6c98b2e1...` | `af28014038101e6e...` |
| no-lut-early-exit-diagnostic | 3x3 | true | {"index":false,"srgbPair":false,"hardLight":false,"solarize":false} | `156041d41f151f13...` | `b5bf47ed4738d670...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| lut-srgbToLinear-write-index-transpose | index | srgbPair | 2 | 4 | 4 | 1 | 0 | nonzero |
| lut-linearToSrgb-constant-induction | index | srgbPair | 5 | 4 | 4 | 1 | 0 | nonzero |
| lut-lutHardLight-write-index-transpose | index | hardLight | 2 | 1 | 1 | 4 | 0 | nonzero |
| lut-lutSolarize-constant-induction | index | solarize | 6 | 1 | 1 | 4 | 0 | nonzero |

- **lut-srgbToLinear-write-index-transpose**: srgbToLinear: transpose the WRITE index from linear[i] to linear[(i+2)%3] while leaving the srgb[i] READ untouched -- a cyclic lane-swap bug the index_expression_admission profile must prevent silently compiling.
- **lut-linearToSrgb-constant-induction**: linearToSrgb: replace every loop-induction-variable subscript [i] with the constant [0] -- both the READ (linear[i]) and WRITE (srgb[i]) collapse onto lane 0, leaving lanes 1/2 at their zero-initialized value. Exactly the "replace the induction variable with a constant" shape the brief calls out.
- **lut-lutHardLight-write-index-transpose**: lutHardLight (reachable only at preset==20): transpose the WRITE index from result[i] to result[(i+2)%3] while leaving rgb[i] READs untouched.
- **lut-lutSolarize-constant-induction**: lutSolarize (reachable only at preset==22): replace every [i] subscript with the constant [0], collapsing both the rgb[i] read and result[i] write onto lane 0.

### Direct rows: `srgb_to_linear_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).

### Direct rows: `linear_to_srgb_rows`

6 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).

### Direct rows: `lut_hard_light_rows`

5 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).

### Direct rows: `lut_solarize_rows`

5 rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).


## Negative closure

- **any_other_define_map**: reject -- not constructible for this cluster, see defines_axis_note
- **generic_const_vec3_global_capability**: forbidden -- must stay scoped to the five frozen per-program LUMA_WEIGHTS declaration identities, never widened to "any const vec3"
- **generic_id_indexed_write_capability**: forbidden -- must stay scoped to the 74 frozen per-program node identities, never widened to "any id-indexed write"
- **hslSecondary_luma_weights_treated_as_render_validated**: forbidden -- validated structurally (type-checks) only; zero live consumers, zero divergence is EXPECTED and confirmed, not a coverage gap
- **reusing_existing_index_capability_tokens**: forbidden -- FIXED_NINE/FIXED_GRID/FIXED_ARRAY_PARAMETER/FIXED_AFFINE_CENTERS13 must not be reused as the used.add(...) token for grade's index sites; this is a JS behavioral oracle only and does not itself assert Python-side vocabulary, but documents the constraint per the frozen brief §6 for the implementer

