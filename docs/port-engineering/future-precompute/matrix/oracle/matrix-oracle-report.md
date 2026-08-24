# Matrix-dispatch cluster (Slice B: matrix*vector) closure oracle report

Corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`. 5 programs. Slice B only: mat3*vec3 (N=3) matrix-vector dispatch across 5 programs (adjust, colorspace, cellNoise, colorLab, shapes). glitch (Slice C, mat4 chained matrix*matrix) is deliberately excluded -- different lowering, different oracle.

Total cases: **29** (20 closure-exercising + 9 non-reaching diagnostic).

## Narrowing analysis

**Finding A (live, safe)**: linear_srgb_from_oklab (all 5 programs): fwdA*c (simple operand) is an inlined per-row sum-of-products expression; fwdB*(lms*lms*lms) (compound operand) narrows the cube to f32 (wrapped in new $runtime.PooledFloat32Array([...])) BEFORE the row dot-product. Both compute the full row-sum in double and narrow exactly once, matching C++ operator*(Mat<N>,Vec<N,float>) (glsl_types.hpp:231) and operator*(Mat<N>,FloatExpr<N>) (glsl_types.hpp:233) exactly. Proven by mutation (see each program's "*-cube-unnarrowed" entry): removing the narrowing step measurably diverges the final f32 output for ordinary inputs.

**Finding B (dead, and separately unobservable)**: oklab_from_linear_srgb (cellNoise, colorLab, shapes only): invB*c is narrow-safe by the same shape as fwdA*c; the inverse's compound operand invA*(sign(lms)*pow(abs(lms),vec3(1/3))) transpiles with the divergent shape vec3.multiply([], sign(lms), pow(...)) (plain Array, never narrowed) -- matching the precompute report's Finding B exactly. This function is NEVER called from main() in any of the 3 programs that declare it (confirmed by direct source read), so it cannot be render-validated regardless. Additionally and independently, its specific compound-operand shape is PROVABLY UNOBSERVABLE under a narrowing-removal mutation: sign(x) in {-1,0,1}, both operands already individually f32-narrowed, so their product is an exact multiply by unit magnitude at any precision -- see each affected program's direct_rows_dead_inverse.proof for the closed-form argument and the machine-asserted zero-divergence sweep.

**Slice C (out of scope)**: The report's Finding C (matrix*matrix chained products via matrixMult's un-narrowed Array accumulator, live in glitch's T*Q*S bicubic chain) is a DIFFERENT divergence, in a DIFFERENT program, requiring a DIFFERENT lowering (chained-product, not vector-multiply) -- explicitly out of scope for this Slice B oracle per the task brief.

## Per-program summary

| Program | Key | Has dead inverse | Eligible cases | Diagnostic cases | Mutations | Narrowing verdict |
| --- | --- | --- | ---: | ---: | ---: | --- |
| adjust | `filter/adjust:adjust` | false | 4 | 2 | 2 | narrowing-SAFE, verified by mutation (see cube-unnarrowed); no inverse function exists in this program. |
| colorspace | `filter/colorspace:colorspace` | false | 4 | 1 | 2 | narrowing-SAFE, verified by mutation (see cube-unnarrowed); no inverse function exists in this program. |
| cellNoise | `classicNoisedeck/cellNoise:cellNoise` | true | 4 | 2 | 2 | live half (linear_srgb_from_oklab) narrowing-SAFE, verified by mutation (see cube-unnarrowed); dead half (oklab_from_linear_srgb) carries Finding B's divergent code shape but is unreachable from main() and, independently, provably unobservable for its specific sign*pow operand -- see direct_rows_dead_inverse. |
| colorLab | `classicNoisedeck/colorLab:colorLab` | true | 4 | 2 | 2 | live half (linear_srgb_from_oklab) narrowing-SAFE, verified by mutation (see cube-unnarrowed); dead half (oklab_from_linear_srgb) carries Finding B's divergent code shape but is unreachable from main() and, independently, provably unobservable for its specific sign*pow operand -- see direct_rows_dead_inverse. |
| shapes | `classicNoisedeck/shapes:shapes` | true | 4 | 2 | 2 | live half (linear_srgb_from_oklab) narrowing-SAFE, verified by mutation (see cube-unnarrowed); dead half (oklab_from_linear_srgb) carries Finding B's divergent code shape but is unreachable from main() and, independently, provably unobservable for its specific sign*pow operand -- see direct_rows_dead_inverse. |

## `filter/adjust:adjust`

Source: `filter/adjust/adjust.glsl` (3786 bytes, `dc1d8456ff2bb6d00ecc62af33ef3a730a990b18b7037d29a29a6e3a3b963ce8`). Canonical factory `canonicalFactory19` (`30a22b13bc733bcbf15545734336006d3ed09101cf82bc6d7c589c843c09e3b0`). Defines: `{}`.

Closures exercised by full-render cases: `linear_srgb_from_oklab`.
No dead closures in this program.

Narrowing verdict: narrowing-SAFE, verified by mutation (see cube-unnarrowed); no inverse function exists in this program

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| oklab-mode-varied | 6x5 | false | {"matrix":true} | `09001cb14c56b1b7...` | `be20096bf614a633...` |
| oklch-mode-tiled | 5x6 | false | {"matrix":true} | `3013805193a916b4...` | `3efef533cfcf11ce...` |
| oklab-mode-extreme | 7x4 | false | {"matrix":true} | `a0b746bce8cf7496...` | `4dae5acfb0dd4530...` |
| oklch-mode-negative-tiled | 4x7 | false | {"matrix":true} | `be6d0ea834ca0a40...` | `8d30b1e6092e787e...` |
| hsv-mode-diagnostic | 3x3 | true | {"matrix":false} | `bdc69cf500ec66f2...` | `f61adb6f1cb7895b...` |
| off-mode-diagnostic | 3x3 | true | {"matrix":false} | `5790b91cfb0de1a9...` | `0fb133094b084415...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| adjust-fwdB-column-swap | constant | matrix | 1 | 4 | 4 | 2 | 0 |
| adjust-cube-unnarrowed | narrowing | matrix | 1 | 4 | 4 | 2 | 0 |

- **adjust-fwdB-column-swap**: Swap fwdB column 0 and column 1 -- a plausible transposition/copy-paste bug in the emitted mat3 constructor. fwdB is asymmetric (no row/column is a scalar multiple of another), so this changes the live-half output structurally.
- **adjust-cube-unnarrowed**: Remove the f32-narrowing wrap around the lms*lms*lms cube before it feeds fwdB's row dot-product -- simulates an emitter that lowers matN*vecN for a COMPOUND operand by accumulating in double without narrowing first (Finding B's divergence class, verified live on this SAFE-by-construction site). Proves the narrow-once contract (glsl_types.hpp:231/233) is load-bearing, not incidental.

### Direct rows: `linear_srgb_from_oklab` (live)

6 rows, real closure invoked directly. Zero-vector control row shows zero divergence under both mutations (proven exact no-op); at least one non-zero row diverges under each (machine-asserted).


## `filter/colorspace:colorspace`

Source: `filter/colorspace/colorspace.glsl` (2711 bytes, `602f1a2ce0abd59e8e17753c8ec9b49d01fbe0f169d60ad290d294904e02f705`). Canonical factory `canonicalFactory38` (`5c4ede05fe48ee05b9c0e1198450ea28f6018f6038848dfe295a06381f8df883`). Defines: `{}`.

Closures exercised by full-render cases: `linear_srgb_from_oklab`.
No dead closures in this program.

Narrowing verdict: narrowing-SAFE, verified by mutation (see cube-unnarrowed); no inverse function exists in this program

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| oklab-mode | 6x5 | false | {"matrix":true} | `9392fb282c437de3...` | `ba956f9af3b11001...` |
| oklch-mode-tiled | 5x6 | false | {"matrix":true} | `cd7b0baec4d5e83d...` | `15973873dc038223...` |
| oklab-mode-tiled | 7x4 | false | {"matrix":true} | `01887df22ecc4e08...` | `d3f148721e3e94f3...` |
| oklch-mode-extreme-canvas | 4x7 | false | {"matrix":true} | `d149e53acb157896...` | `2258f3ef30125dd2...` |
| hsv-mode-diagnostic | 3x3 | true | {"matrix":false} | `ca708de84eafdb4b...` | `6609a8c81e574774...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| colorspace-fwdB-column-swap | constant | matrix | 1 | 4 | 4 | 1 | 0 |
| colorspace-cube-unnarrowed | narrowing | matrix | 1 | 4 | 4 | 1 | 0 |

- **colorspace-fwdB-column-swap**: Swap fwdB column 0 and column 1 -- a plausible transposition/copy-paste bug in the emitted mat3 constructor. fwdB is asymmetric (no row/column is a scalar multiple of another), so this changes the live-half output structurally.
- **colorspace-cube-unnarrowed**: Remove the f32-narrowing wrap around the lms*lms*lms cube before it feeds fwdB's row dot-product -- simulates an emitter that lowers matN*vecN for a COMPOUND operand by accumulating in double without narrowing first (Finding B's divergence class, verified live on this SAFE-by-construction site). Proves the narrow-once contract (glsl_types.hpp:231/233) is load-bearing, not incidental.

### Direct rows: `linear_srgb_from_oklab` (live)

6 rows, real closure invoked directly. Zero-vector control row shows zero divergence under both mutations (proven exact no-op); at least one non-zero row diverges under each (machine-asserted).


## `classicNoisedeck/cellNoise:cellNoise`

Source: `classicNoisedeck/cellNoise/cellNoise.glsl` (9643 bytes, `9fd76306b377ef501a5dd340263179f04e3e890cc05d5e82f524f7bdf793d3b8`). Canonical factory `canonicalFactory2` (`c22f3abe9db76b0b926895c55fdf202847f65a78ca9940dc4ac7122f9e9f53b6`). Defines: `{}`.

Closures exercised by full-render cases: `linear_srgb_from_oklab`.
Closures authenticated structurally ONLY (dead, never render-validated): `oklab_from_linear_srgb`.

Narrowing verdict: live half (linear_srgb_from_oklab) narrowing-SAFE, verified by mutation (see cube-unnarrowed); dead half (oklab_from_linear_srgb) carries Finding B's divergent code shape but is unreachable from main() and, independently, provably unobservable for its specific sign*pow operand -- see direct_rows_dead_inverse.proof

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| oklab-palette-worley | 6x5 | false | {"matrix":true} | `b4670ec5f86258e3...` | `22d83f1666185b22...` |
| oklab-palette-tiled | 5x6 | false | {"matrix":true} | `b687e409202c3fa5...` | `b9e638cce90b0186...` |
| oklab-palette-hexagon-tex-influence | 7x4 | false | {"matrix":true} | `e3d97829e4815e94...` | `aedb31a4ec69b347...` |
| oklab-palette-extreme | 4x7 | false | {"matrix":true} | `b7dad68275c5a8d5...` | `26aebeb29c62cfa3...` |
| diagnostic-colorMode-grayscale | 3x3 | true | {"matrix":false} | `a1091a63f611034f...` | `c43ccf0e4ac856e2...` |
| diagnostic-paletteMode-hsv | 3x3 | true | {"matrix":false} | `f3588cfed8f01688...` | `a4144d56eb3693d9...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| cellNoise-fwdB-column-swap | constant | matrix | 1 | 4 | 4 | 2 | 0 |
| cellNoise-cube-unnarrowed | narrowing | matrix | 1 | 4 | 4 | 2 | 0 |

- **cellNoise-fwdB-column-swap**: Swap fwdB column 0 and column 1 -- a plausible transposition/copy-paste bug in the emitted mat3 constructor. fwdB is asymmetric (no row/column is a scalar multiple of another), so this changes the live-half output structurally.
- **cellNoise-cube-unnarrowed**: Remove the f32-narrowing wrap around the lms*lms*lms cube before it feeds fwdB's row dot-product -- simulates an emitter that lowers matN*vecN for a COMPOUND operand by accumulating in double without narrowing first (Finding B's divergence class, verified live on this SAFE-by-construction site). Proves the narrow-once contract (glsl_types.hpp:231/233) is load-bearing, not incidental.

### Direct rows: `linear_srgb_from_oklab` (live)

6 rows, real closure invoked directly. Zero-vector control row shows zero divergence under both mutations (proven exact no-op); at least one non-zero row diverges under each (machine-asserted).

### Direct rows: `oklab_from_linear_srgb` (dead, structural only)

6 rows, real closure invoked directly. ALL rows show zero divergence under the narrowing-removal mutation, machine-asserted -- proof: sign(x) in {-1, 0, 1} for all real x (IEEE754 sign, ignoring NaN), and both `sign(lms)` and `pow(abs(lms), vec3(1/3))` are already individually f32-narrowed before the multiply (sign/pow are #unary/#binary stdlib calls in glsl-runtime.js, which narrow every element to f32 on write). Multiplying an f32 value by exactly -1, 0, or 1 is EXACT at any precision -- it can only flip a sign bit or zero the result, never round. Therefore narrowing the PRODUCT before vs. after feeding it into the invA row dot-product cannot change the bit pattern, and this is a mathematically provable, not merely empirically observed, zero-divergence result.


## `classicNoisedeck/colorLab:colorLab`

Source: `classicNoisedeck/colorLab/colorLab.glsl` (9273 bytes, `8a2615887cde9ad2f6adead3a6f69a9f21ac015f762e6add80f23aa293bd530a`). Canonical factory `canonicalFactory5` (`14a7f15dcc865abb6780304e3e4f8d427a47255f638da38a78c075680ec932dd`). Defines: `{}`.

Closures exercised by full-render cases: `linear_srgb_from_oklab`.
Closures authenticated structurally ONLY (dead, never render-validated): `oklab_from_linear_srgb`.

Narrowing verdict: live half (linear_srgb_from_oklab) narrowing-SAFE, verified by mutation (see cube-unnarrowed); dead half (oklab_from_linear_srgb) carries Finding B's divergent code shape but is unreachable from main() and, independently, provably unobservable for its specific sign*pow operand -- see direct_rows_dead_inverse.proof

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| oklab-direct | 6x5 | false | {"matrix":true} | `266480b426cbed88...` | `fb8139ccf9d6d3a2...` |
| oklab-direct-tiled-inverted | 5x6 | false | {"matrix":true} | `2d2e70a65f785fbb...` | `d0c3caf8af03cdb3...` |
| palette-oklab-tiled | 7x4 | false | {"matrix":true} | `ff867f4d2cc4bf4e...` | `203afd765ac3a19d...` |
| palette-oklab-cycle-negative | 4x7 | false | {"matrix":true} | `57e152003fc7ebe3...` | `dadbed3bb9dc4a8a...` |
| diagnostic-colorMode-grayscale | 3x3 | true | {"matrix":false} | `fa7e11ec1218ba40...` | `275921d2a35e46a8...` |
| diagnostic-palette-hsv | 3x3 | true | {"matrix":false} | `8ce6dded42416ddb...` | `9412431063a26d0e...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| colorLab-fwdB-column-swap | constant | matrix | 1 | 4 | 4 | 2 | 0 |
| colorLab-cube-unnarrowed | narrowing | matrix | 1 | 4 | 4 | 2 | 0 |

- **colorLab-fwdB-column-swap**: Swap fwdB column 0 and column 1 -- a plausible transposition/copy-paste bug in the emitted mat3 constructor. fwdB is asymmetric (no row/column is a scalar multiple of another), so this changes the live-half output structurally.
- **colorLab-cube-unnarrowed**: Remove the f32-narrowing wrap around the lms*lms*lms cube before it feeds fwdB's row dot-product -- simulates an emitter that lowers matN*vecN for a COMPOUND operand by accumulating in double without narrowing first (Finding B's divergence class, verified live on this SAFE-by-construction site). Proves the narrow-once contract (glsl_types.hpp:231/233) is load-bearing, not incidental.

### Direct rows: `linear_srgb_from_oklab` (live)

6 rows, real closure invoked directly. Zero-vector control row shows zero divergence under both mutations (proven exact no-op); at least one non-zero row diverges under each (machine-asserted).

### Direct rows: `oklab_from_linear_srgb` (dead, structural only)

6 rows, real closure invoked directly. ALL rows show zero divergence under the narrowing-removal mutation, machine-asserted -- proof: sign(x) in {-1, 0, 1} for all real x (IEEE754 sign, ignoring NaN), and both `sign(lms)` and `pow(abs(lms), vec3(1/3))` are already individually f32-narrowed before the multiply (sign/pow are #unary/#binary stdlib calls in glsl-runtime.js, which narrow every element to f32 on write). Multiplying an f32 value by exactly -1, 0, or 1 is EXACT at any precision -- it can only flip a sign bit or zero the result, never round. Therefore narrowing the PRODUCT before vs. after feeding it into the invA row dot-product cannot change the bit pattern, and this is a mathematically provable, not merely empirically observed, zero-divergence result.


## `classicNoisedeck/shapes:shapes`

Source: `classicNoisedeck/shapes/shapes.glsl` (21289 bytes, `60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0`). Canonical factory `canonicalFactory16` (`a4e1aeaf8cbc3d748517369e054b7ec4a2fd5f70962cbafef61d5e473527c2c3`). Defines: `{"LOOP_A_OFFSET":40,"LOOP_B_OFFSET":30}`.

Closures exercised by full-render cases: `linear_srgb_from_oklab`.
Closures authenticated structurally ONLY (dead, never render-validated): `oklab_from_linear_srgb`.

Narrowing verdict: live half (linear_srgb_from_oklab) narrowing-SAFE, verified by mutation (see cube-unnarrowed); dead half (oklab_from_linear_srgb) carries Finding B's divergent code shape but is unreachable from main() and, independently, provably unobservable for its specific sign*pow operand -- see direct_rows_dead_inverse.proof

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| oklab-palette-a | 6x5 | false | {"matrix":true} | `24fc890fc3fb8ea6...` | `87edb17f5f25afd5...` |
| oklab-palette-tiled | 5x6 | false | {"matrix":true} | `6120a8e580b9c733...` | `021e26fe02abb0b0...` |
| oklab-palette-extreme | 7x4 | false | {"matrix":true} | `045349cadbfb30b1...` | `29cabb807ee830bb...` |
| oklab-palette-negative-speed | 4x7 | false | {"matrix":true} | `598859af2a3400cd...` | `0eafb55f928b32a6...` |
| diagnostic-palette-hsv | 3x3 | true | {"matrix":false} | `8882e69e7f73ea6b...` | `74ca2b357fad7f2c...` |
| diagnostic-palette-rgb | 3x3 | true | {"matrix":false} | `89aefd704b2ca693...` | `ca589fefbb8dc01d...` |

### Mutations

| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| shapes-fwdB-column-swap | constant | matrix | 1 | 4 | 4 | 2 | 0 |
| shapes-cube-unnarrowed | narrowing | matrix | 1 | 4 | 4 | 2 | 0 |

- **shapes-fwdB-column-swap**: Swap fwdB column 0 and column 1 -- a plausible transposition/copy-paste bug in the emitted mat3 constructor. fwdB is asymmetric (no row/column is a scalar multiple of another), so this changes the live-half output structurally.
- **shapes-cube-unnarrowed**: Remove the f32-narrowing wrap around the lms*lms*lms cube before it feeds fwdB's row dot-product -- simulates an emitter that lowers matN*vecN for a COMPOUND operand by accumulating in double without narrowing first (Finding B's divergence class, verified live on this SAFE-by-construction site). Proves the narrow-once contract (glsl_types.hpp:231/233) is load-bearing, not incidental.

### Direct rows: `linear_srgb_from_oklab` (live)

6 rows, real closure invoked directly. Zero-vector control row shows zero divergence under both mutations (proven exact no-op); at least one non-zero row diverges under each (machine-asserted).

### Direct rows: `oklab_from_linear_srgb` (dead, structural only)

6 rows, real closure invoked directly. ALL rows show zero divergence under the narrowing-removal mutation, machine-asserted -- proof: sign(x) in {-1, 0, 1} for all real x (IEEE754 sign, ignoring NaN), and both `sign(lms)` and `pow(abs(lms), vec3(1/3))` are already individually f32-narrowed before the multiply (sign/pow are #unary/#binary stdlib calls in glsl-runtime.js, which narrow every element to f32 on write). Multiplying an f32 value by exactly -1, 0, or 1 is EXACT at any precision -- it can only flip a sign bit or zero the result, never round. Therefore narrowing the PRODUCT before vs. after feeding it into the invA row dot-product cannot change the bit pattern, and this is a mathematically provable, not merely empirically observed, zero-divergence result.


## Negative closure

- **slice_c_glitch**: excluded -- mat4 chained matrix*matrix, different lowering, see narrowing_analysis.slice_c_out_of_scope
- **moodscape_noise_effects**: excluded -- entire matrix closure dead at authorized defines in all three (per the precompute report's reachability probe; not independently re-verified here since this oracle only targets the 5 live-or-half-live Slice B programs)
- **dead_inverse_treated_as_render_validated**: forbidden -- oklab_from_linear_srgb is validated structurally only (direct closure invocation + narrowing proof), never through a full-render case, because it has zero live callers in all 3 programs that declare it
- **generic_mat3_vec3_capability**: forbidden -- this oracle is scoped to the 5 named program_keys and their exact fwdA/fwdB/invA/invB constant identities, not "any mat3*vec3 site"

