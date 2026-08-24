# Loop-proof cluster oracle-b report

Hermetic JS oracle for the expensive half of the eight-program loop-proof-blocked cluster. Ground truth for the future C++20 port's bit-exact parity tests, once each program's loop-proof gate clears.

Programs covered with a full discriminating oracle: **7**. Programs that could not be covered: **1** (`classicNoisedeck/effects:effects` -- see below).

Total cases across the seven covered programs: **24** (18 closure-exercising + 6 diagnostic). Total mutations: **14**.

## Ground truth per program

| Program | Ground truth | Notes |
| --- | --- | --- |
| nmReindexReduce | canonical factory | clean, no adapter override |
| mandelbrot | canonical factory | clean, no adapter override |
| median | **adapter** (`medianFactory`) | canonical factory (`canonicalFactory80`) CRASHES on a 5x5 render -- see below |
| classicNoisedeck/noise | canonical factory | clean, no adapter override |
| synth/noise | canonical factory | clean, no adapter override |
| testPattern | canonical factory | clean, no adapter override |
| fractal | **adapter** (`fractalFactory`) | NO canonical factory exists at all -- permanent architectural routing, `generatedBytes: 0` |
| effects | n/a -- UNCOVERABLE | dead code at the authorized define, see below |

## Per-program summary

| Program | Cases | Diagnostic | Mutations | All mutations diverge on >=1 reach-eligible case |
| --- | ---: | ---: | ---: | --- |
| nmReindexReduce | 3 | 1 | 2 | true |
| mandelbrot | 3 | 2 | 2 | true |
| median | 3 | 1 | 2 | true |
| classicNoisedeckNoise | 3 | 0 | 2 | true |
| synthNoise | 3 | 0 | 2 | true |
| testPattern | 1 | 1 | 2 | true |
| fractal | 2 | 1 | 2 | true |
| effects | -- | -- | -- | **UNCOVERABLE -- see below** |

## `filter/reindex:nmReindexReduce` (nmReindexReduce)

Defines: `{}`. Ground truth: canonical factory (clean, verified)

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| min-in-last-row-y-axis | 1x1 | false | {"offByOne":true,"swap":true} | `aba4a26bd07150e8...` | `7b2b1ebcff4ad47d...` |
| max-in-last-col-x-axis | 1x1 | false | {"offByOne":true,"swap":true} | `76ff8389e43ed497...` | `b4126f0d1d1f1cec...` |
| small-3x3-grid-multi-tile-drop | 1x1 | false | {"offByOne":false,"swap":true} | `2efa59f25fac42a8...` | `5bcefff1e97b1e17...` |
| single-tile-diagnostic | 1x1 | true | {"offByOne":false,"swap":false} | `10e63f3b52a7d9a5...` | `49c73167083c210a...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| nmReindexReduce-tile-cap-off-by-one | trip_count_off_by_one | 2 | 2 | 2 | 0 |
| nmReindexReduce-tile-cap-swap | trip_count_swap | 3 | 3 | 1 | 0 |

- **nmReindexReduce-tile-cap-off-by-one**: Shrink the shared tile-scan cap from 512 to 4: drops tile row/col index 4 from BOTH nested loops (they share one symbol). Reach-eligible exactly when a case's tileCount.x or tileCount.y exceeds 4.
- **nmReindexReduce-tile-cap-swap**: Shrink the shared tile-scan cap to 1: a materially wrong trip count, visiting only tile (0,0) regardless of true tileCount. Reach-eligible whenever a case's tileCount.x or tileCount.y exceeds 1.

## `synth/mandelbrot:mandelbrot` (mandelbrot)

Defines: `{}`. Ground truth: canonical factory (clean, verified)

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| never-escapes-real-axis-boundary | 1x1 | false | {"offByOne":true,"swap":true} | `7ab8f6c26e4f9862...` | `e3820096cb82366b...` |
| moderate-escape-273-seahorse-tip | 1x1 | false | {"offByOne":false,"swap":true} | `04b6da77619e432e...` | `1325e312c1ed1975...` |
| slow-escape-112-seahorse-alt | 1x1 | false | {"offByOne":false,"swap":true} | `ae1ea09d439ef8dd...` | `7019c7a9cbef5cea...` |
| cardioid-early-out-diagnostic | 1x1 | true | {"offByOne":false,"swap":false} | `7ab8f6c26e4f9862...` | `e3820096cb82366b...` |
| fast-escape-far-outside-diagnostic | 1x1 | true | {"offByOne":false,"swap":false} | `965fab9464705b2c...` | `e3820096cb82366b...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| mandelbrot-max-iter-off-by-one | trip_count_off_by_one | 1 | 1 | 4 | 0 |
| mandelbrot-max-iter-swap | trip_count_swap | 3 | 3 | 2 | 0 |

- **mandelbrot-max-iter-off-by-one**: Drop the static cap from 500 to 499 -- the smallest possible wrong trip count. Only the never-escapes case (true rawIter=500) reaches a cap this close to the real bound.
- **mandelbrot-max-iter-swap**: Shrink the static cap to 80 -- a materially wrong trip count. Reach-eligible for all three non-diagnostic cases (true iteration counts 500/273/112, all exceeding 80).

## `filter/median:median` (median)

Defines: `{"RADIUS":3}`. Ground truth: adapter (medianFactory) -- see module header / report for why

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| high-variance-8x8 | 8x8 | false | {"cap1":true,"cap5":true} | `5b58355225d6766d...` | `3fe5bb629ed8575e...` |
| high-variance-6x5 | 6x5 | false | {"cap1":true,"cap5":true} | `1c5819a2ef40e2e0...` | `a8bb162ff881e795...` |
| high-variance-7x7 | 7x7 | false | {"cap1":true,"cap5":true} | `c37307cb6f8f02e4...` | `5f8a8a5e0e82807d...` |
| uniform-color-diagnostic | 6x6 | true | {"cap1":false,"cap5":false} | `a102ef145e8a24af...` | `6c8276aa9be792c9...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| median-outer-convergence-cap-1 | trip_count_swap | 3 | 3 | 1 | 0 |
| median-outer-convergence-cap-5 | trip_count_off_by_one | 3 | 3 | 1 | 0 |

- **median-outer-convergence-cap-1**: Cap the outer quickselect convergence loop at 1 pass -- severe, provably-terminating (bounded by a counter, not data) trip-count reduction. Reach-eligible on all three high-variance cases (true convergence depth >10); the uniform-color diagnostic already converges within 1 pass and is expected-zero.
- **median-outer-convergence-cap-5**: Cap the outer quickselect convergence loop at 5 passes -- milder than cap-1 but still well under the true convergence depth (>10) for all three high-variance cases; the uniform-color diagnostic is unaffected (converges in 1 pass).

### Canonical-factory defect (median)

The GLSL-transpiled `canonicalFactory80` crashes on certain input sizes; the adapter (used as this oracle's ground truth) does not.

| Size | Threw | Message |
| --- | --- | --- |
| 4x4 | false | -- |
| 5x5 | true | Cannot read properties of undefined (reading 'length') |
| 6x6 | false | -- |

canonicalFactory80 crashes on this exact 5x5 patterned input; 4x4 and 6x6 render fine with the identical algorithm shape and identical uniform contract -- data-dependent, not a hermeticity mistake in this generator.

### Avoided mutation site (median)

Anchor: `while (scanLeft <= scanRight) {`. Attempted mutation: `while (scanLeft < scanRight) {`.

**Outcome:** INFINITE LOOP -- verified live, killed after exceeding a 120s wall-clock watchdog on an 8x8 patterned render; a synchronous JS while-loop blocks the event loop so no in-process timer can preempt it

**Root cause:** dropping the `<=` boundary loses the guarantee that scanLeft/scanRight cross by the end of the middle loop; when they instead land exactly on medianIndex, neither outer-loop narrowing branch fires and left/right are unchanged forever

**Disposition:** AVOIDED as a mutation site entirely. Both mutations below instead cap the OUTER `while (left < right)` convergence loop with an explicit counter, which provably terminates by construction regardless of data, sidestepping this hazard rather than working around it case-by-case.

## `classicNoisedeck/noise:noise` (classicNoisedeckNoise)

Defines: `{"COLOR_MODE":6,"LOOP_OFFSET":300,"METRIC":0,"REFRACT_MODE":2,"NOISE_TYPE":10}`. Ground truth: canonical factory (clean, verified)

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| three-octaves | 6x5 | false | {"default":true} | `e593f6ae405fd541...` | `a8885b365df22505...` |
| four-octaves | 6x5 | false | {"default":true} | `8d8765e1320ea796...` | `410a34652af4558a...` |
| six-octaves-saturation-check | 6x5 | false | {"default":true} | `63552decceb85dfe...` | `100f62dbde162160...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| classicNoisedeckNoise-octave-off-by-one | trip_count_off_by_one | 3 | 3 | 0 | 0 |
| classicNoisedeckNoise-octave-swap | trip_count_swap | 3 | 3 | 0 | 0 |

- **classicNoisedeckNoise-octave-off-by-one**: Drop the last octave (i<octaves instead of i<=octaves): smallest possible wrong trip count. Verified live to diverge at octaves=3, 4, and 6 -- the geometric weight decay (1/2^i) has not saturated the mutated last octave into float32 invisibility at any of these counts.
- **classicNoisedeckNoise-octave-swap**: Drop the last two octaves: a materially wrong trip count, verified live to diverge at octaves=3, 4, and 6.

## `synth/noise:noise` (synthNoise)

Defines: `{"LOOP_OFFSET":300,"NOISE_TYPE":10}`. Ground truth: canonical factory (clean, verified)

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| three-octaves | 6x5 | false | {"default":true} | `118b29ffb7adcfa1...` | `777b9a1e2d2b53a1...` |
| four-octaves | 6x5 | false | {"default":true} | `3a1b04cf5c4ef49c...` | `6586a8b0d1602215...` |
| six-octaves-saturation-check | 6x5 | false | {"default":true} | `39cde4f5e8ede7b8...` | `84e04443fe73e691...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| synthNoise-octave-off-by-one | trip_count_off_by_one | 3 | 3 | 0 | 0 |
| synthNoise-octave-swap | trip_count_swap | 3 | 3 | 0 | 0 |

- **synthNoise-octave-off-by-one**: Drop the last octave. Verified live to diverge at octaves=3, 4, and 6.
- **synthNoise-octave-swap**: Drop the last two octaves. Verified live to diverge at octaves=3, 4, and 6.

## `synth/testPattern:testPattern` (testPattern)

Defines: `{}`. Ground truth: canonical factory (clean, verified)

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| hundreds-digit-glyph-hit | 1x1 | false | {"default":true} | `f6bb1294da2f78cd...` | `ad95131bc0b799c0...` |
| single-digit-diagnostic | 1x1 | true | {"default":false} | `7ab8f6c26e4f9862...` | `e3820096cb82366b...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| testPattern-digit-extraction-off-by-one | trip_count_off_by_one | 1 | 1 | 1 | 0 |
| testPattern-digit-extraction-swap | trip_count_swap | 1 | 1 | 1 | 0 |

- **testPattern-digit-extraction-off-by-one**: Drop the hundreds-digit extraction (i<2 instead of i<3): digits[2] stays at its zero-initialized value. Verified live to flip the hundreds-digit-glyph-hit pixel from background to glyph-black.
- **testPattern-digit-extraction-swap**: Drop both the tens- and hundreds-digit extraction (i<1): a materially wrong trip count. Verified live to diverge identically to the off-by-one mutation at this probe point (both leave digits[2]=0).

## `classicNoisedeck/fractal:fractal` (fractal)

Defines: `{}`. Ground truth: adapter (fractalFactory) -- see module header / report for why

### Cases

| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| julia-never-escapes-z0a | 1x1 | false | {"default":true} | `b73ab93e458d122f...` | `61efa6ca5470d637...` |
| julia-never-escapes-z0b | 1x1 | false | {"default":true} | `b73ab93e458d122f...` | `61efa6ca5470d637...` |
| julia-fast-escape-diagnostic | 1x1 | true | {"default":false} | `7ab8f6c26e4f9862...` | `e3820096cb82366b...` |

### Mutations -- empirical divergence figures

| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| fractal-julia-count-off-by-one | trip_count_off_by_one | 2 | 2 | 1 | 0 |
| fractal-julia-count-swap | trip_count_swap | 2 | 2 | 1 | 0 |

- **fractal-julia-count-off-by-one**: Drop the last julia() iteration (count-1 instead of count, count=iterations*2=100). Reach-eligible on both never-escapes cases (true escape >> 100, verified via a double-precision calibration probe restricted to this generator's case-design step -- the actual proof renders through the real fractalFactory).
- **fractal-julia-count-swap**: Drop the last 40 julia() iterations (count-40=60): a materially wrong trip count. Same reach-eligibility as the off-by-one mutation.

## `classicNoisedeck/effects:effects` -- UNCOVERABLE

UNRENDERABLE-AS-DISCRIMINATING, not merely non-discriminating -- verified live, not assumed. `EFFECT` genuinely IS bound as a runtime uniform (`var EFFECT = $bindings["EFFECT"];`, matching the defines-bound-as-uniforms lesson -- it is NOT preprocessor-eliminated, unlike a first, wrong hypothesis this generator formed and then disproved by grepping the compiled JS text for `function convolve`/`function bloom`/`function zoomBlur`, all of which ARE present). Every loop in this program (convolve()'s 3x3 kernel-tap loop, bloom()'s -4..4 nested loop, zoomBlur()'s 0..40 loop) lives exclusively inside functions reachable ONLY through `main()`'s `if (EFFECT != 0) { if (effectAmt != 0) { ... } }` gate -- and `generate_typed_slice._defaults()` authorizes EFFECT=0 for this program (confirmed live, not assumed). At EFFECT=0 that whole block is skipped at RUNTIME on every invocation, so none of its loops ever execute. Verified live, not merely inferred from reading the source: a textual off-by-one mutation on convolve()'s tap loop (`for (var i = 0; i < 9; i++)` -> `for (var i = 0; i < 0; i++)`) produces ZERO divergence across four different `effectAmt` values (0, 5, 10, 20) at the authorized EFFECT=0 -- and the IDENTICAL mutation produces NONZERO divergence at an UNAUTHORIZED EFFECT=1, proving the loop and the mutation are both real and working, just genuinely unreachable at the one define value this task's reachability rule (only build cases reachable from main() at the authorized defines) permits. No case can be built for this program without violating that rule.

### Live evidence captured by this generator

- `EFFECT` confirmed bound as a runtime uniform: **true** (`var EFFECT = $bindings["EFFECT"];`)
- Authorized defines: `{"EFFECT":0,"FLIP":0}`
- Mutation: `convolve() 3x3 tap loop: i<9 -> i<0 (never executes)` (anchor `for (var i = 0; i < 9; i++) {`)
- At the authorized default (EFFECT=0), across effectAmt in {0,5,10,20}: **0/4 diverged**

  | effectAmt | EFFECT | Diverges |
  | ---: | ---: | --- |
  | 0 | 0 | false |
  | 5 | 0 | false |
  | 10 | 0 | false |
  | 20 | 0 | false |

- At an UNAUTHORIZED control value (EFFECT=1, effectAmt=10): **diverges=true** -- proves the loop and mutation are real, just unreachable at the authorized default.

