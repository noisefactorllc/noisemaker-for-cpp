# Builtin admission cluster (`round` / `any` / `reflect`) closure oracle report

Six programs blocked (three today, three after a documented but unlanded const-global-admission widening) on exactly one of three GLSL builtins with zero-or-partial node-identity admission in the C++20 generator. Authorized define map for all six: `{}`.

Total cases: **24** (4 early-exit / dead-code diagnostic).

## Findings

- **snow_public_factory_is_not_canonical**: filter/snow:snow is the one program in this cluster whose PUBLIC kernelFactories entry is NOT canonicalKernelFactories -- src/effects/adapters/snow.js (snowFactory) hand-optimizes the same GLSL program for production rendering. The C++ port targets the CANONICAL (GLSL-transpiled) semantics, exactly as generate_typed_slice.py types the raw source, so this oracle correctly uses canonicalKernelFactories[key] for all six programs including snow -- documented here rather than silently working around it.
- **snow_round_is_dead_code**: as_u32(), the only function in snow.glsl that calls round(), is declared but never invoked from main() -- confirmed by grep against the raw source, the compiled JS factory text, AND a runtime call-log instrumentation (zero round() calls recorded for every snow case built below). round() still gates the C++ generator's frozen-vocabulary walk (the walk visits declared functions, not just reachable ones), so a node-identity admission is still required for snow to type-check, but no case here asserts non-trivial round() BEHAVIOR for snow.
- **fxaa_grain_round_domain_is_integer_only**: round()'s reachable call site in both fxaa and grain (as_u32 applied to resolution.x/y or an equivalent) can never receive a fractional input: width/height are always exact integers (Number.isInteger enforced by createCanonicalBindings). Consequently no full-render case in either program can discriminate ANY rounding tie-break rule -- proven below (zero divergence, not assumed) for both the banker's-rounding and away-from-zero mutations, across every case. Only a general-liveness mutation (round(x) -> round(x)-1, which perturbs every input regardless of tie) is discriminating for these two programs at full-render.
- **posterize_round_domain_is_nonneg_only**: posterize's round() input is levels_raw = max(levels, 0.0) -- always non-negative. round-half-away-from-zero agrees with Math.round on every non-negative real, so that mutation is a PROVABLE (and proven) no-op on every posterize case; only the banker's-rounding mutation (which differs from Math.round at positive ties too, e.g. 0.5 and 2.5) is discriminating at full-render for this program. Both signs of the required .5 boundary are still exhaustively covered via the direct rows below, unconstrained by this program's domain.
- **minus_0p5_sign_of_zero_trap**: Math.round(-0.5) === -0 (verified: Object.is check). The common "obviously correct" C++ idiom `std::floor(x + 0.5f)` matches Math.round's VALUE at every other tested boundary but returns +0 (not -0) at exactly x=-0.5, because -0.5f+0.5f is an exact IEEE754 cancellation that rounds to +0. A C++ round() built on floor(x+0.5) will therefore differ from the JS reference in the SIGN BIT of a zero result at this one input -- proven via a direct row, not assumed.
- **lighting_reflect_defensive_normalize_is_full_render_noop**: The "defensive internal normalize" reflect() mutation is a proven bit-exact no-op for every lighting full-render case: this program always calls normalize() on its normal vector before reflect() ever sees it (calculateNormal -> normalize(vec3(-dx,-dy,1))), so double-normalizing changes nothing. This is a property of THIS PROGRAM, not of reflect() in general -- the hazard is real and independently proven via a direct row using a deliberately non-unit N.

## Per-program summary

| Program | Builtin | Blocked today on | Cases | Diagnostic |
| --- | --- | --- | ---: | ---: |
| posterize | round | (terminal today) | 4 | 1 |
| waves | any | (terminal today) | 4 | 0 |
| lighting | reflect | (terminal today) | 4 | 2 |
| fxaa | round | unsupported global declaration (LUMA_WEIGHTS vec3 const) -- round becomes terminal only after that lands; see relaxed_global_probe.json | 4 | 0 |
| grain | round | unsupported global declaration (const scalar table: PI/TAU/UINT32_TO_FLOAT/INTERPOLATION_*/BASE_SEED) -- round becomes terminal only after that lands | 4 | 0 |
| snow | round | unsupported global declaration (const scalar/vec3 table: CHANNEL_COUNT/TAU/TIME_SEED_OFFSETS/STATIC_SEED/LIMITER_SEED) -- round becomes terminal only after that lands | 4 | 1 |

## `filter/posterize:posterize` (round)

Source: `posterize/posterize.glsl` (2630 bytes, `460910a8d1103eca5cc0b4df82f39fd91fbc447b9a815250ae7d34dfab8ee5b2`). Canonical factory `canonicalFactory116` (`317e38c428bda5e89258c3bc64cae3fbfb54ffa43e0b02f98b2329f542c546ed`). Public factory is canonical identity: true. Adapter override present: false.

**Reachability**: round(levels_raw) at line 65 executes unconditionally, every pixel, before the antialias branch -- always reachable. levels_raw = max(levels, 0.0), so this call site can NEVER receive a negative input: round-half-away-from-zero and Math.round agree on every non-negative real, so the away-from-zero mutation is a PROVABLE (and proven, below) no-op for every posterize case, regardless of whether levels lands on a tie.

### Cases

| Case | Size | Diagnostic | Reach | Call count | F32 SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| half-tie-2.5-discriminates-bankers | 6x5 | false | true | 66 | `de3da045f7e6511c...` |
| half-tie-6.5-discriminates-bankers-antialias-off | 5x6 | false | true | 66 | `c3e167879ca8a8ef...` |
| ordinary-levels-no-tie-sanity | 7x4 | false | true | 60 | `231b58ec967828be...` |
| min-levels-tie-absorbed-diagnostic | 4x7 | true | true | 60 | `eccacf0596e39322...` |

### Mutations

| Mutation | Hazard | Case | Reach | Diverges |
| --- | --- | --- | --- | --- |
| round-minus-one-liveness | general-liveness | half-tie-2.5-discriminates-bankers | true | true |
| round-minus-one-liveness | general-liveness | half-tie-6.5-discriminates-bankers-antialias-off | true | true |
| round-minus-one-liveness | general-liveness | ordinary-levels-no-tie-sanity | true | true |
| round-minus-one-liveness | general-liveness | min-levels-tie-absorbed-diagnostic | true | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | half-tie-2.5-discriminates-bankers | true | true |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | half-tie-6.5-discriminates-bankers-antialias-off | true | true |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | ordinary-levels-no-tie-sanity | true | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | min-levels-tie-absorbed-diagnostic | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | half-tie-2.5-discriminates-bankers | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | half-tie-6.5-discriminates-bankers-antialias-off | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | ordinary-levels-no-tie-sanity | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | min-levels-tie-absorbed-diagnostic | true | false |

- **round-minus-one-liveness**: round(x) -> round(x) - 1 for every input, tie or not. Proves the call site genuinely executes and its result is load-bearing -- independent of the tie-break question.
- **round-bankers-spec-tiebreak**: round(x) -> round-half-to-even ("banker's rounding", the GLSL SPEC's tie-break rule). The JS reference materializes round() as Math.round (round-half-towards-+Infinity), NOT the spec's rule -- this mutation catches a spec-faithful-but-wrong C++ implementation.
- **round-away-from-zero-naive-cpp**: round(x) -> round-half-away-from-zero (what std::round actually does). Catches "I called std::round() directly" as a bug.

## `filter/waves:waves` (any)

Source: `waves/waves.glsl` (2622 bytes, `f4cddf1b3a6c9c68aa677b6743af313e1cdb2bf0a857ce9a1c13edc80f54e3aa`). Canonical factory `canonicalFactory176` (`4a289d05076a7588ced250d307eeaf8d8d0b1628bd5fc907ea71481b02ed2ae5`). Public factory is canonical identity: true. Adapter override present: false.

**Reachability**: any(notEqual(tileOffset, vec2(0.0))) is called TWICE per pixel (lines 48 and 74), unconditionally -- always reachable regardless of tileOffset value.

### Cases

| Case | Size | Diagnostic | Reach | Call count | F32 SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| tile-zero-any-false | 6x5 | false | true | 132 | `bd159170280243d8...` |
| tile-x-only-any-true-one-lane | 5x6 | false | true | 132 | `a50e840918f84f71...` |
| tile-y-only-any-true-other-lane | 7x4 | false | true | 120 | `245b6fccb9696557...` |
| tile-both-any-true-full | 4x7 | false | true | 120 | `3b735dc08ed64c95...` |

### Mutations

| Mutation | Hazard | Case | Reach | Diverges |
| --- | --- | --- | --- | --- |
| any-as-all-confusion | any-all-confusion | tile-zero-any-false | true | false |
| any-as-all-confusion | any-all-confusion | tile-x-only-any-true-one-lane | true | true |
| any-as-all-confusion | any-all-confusion | tile-y-only-any-true-other-lane | true | true |
| any-as-all-confusion | any-all-confusion | tile-both-any-true-full | true | false |
| any-reverse-iteration-order | order-dependence-probe | tile-zero-any-false | true | false |
| any-reverse-iteration-order | order-dependence-probe | tile-x-only-any-true-one-lane | true | false |
| any-reverse-iteration-order | order-dependence-probe | tile-y-only-any-true-other-lane | true | false |
| any-reverse-iteration-order | order-dependence-probe | tile-both-any-true-full | true | false |

- **any-as-all-confusion**: any(v) -> all(v) (AND-reduction instead of OR). Diverges exactly when the input vector is neither all-true nor all-false.
- **any-reverse-iteration-order**: Same OR-reduction, iterated last-to-first. Proves the short-circuit ORDER does not leak into observable output (expected zero divergence everywhere, proven not assumed).

## `filter/lighting:lighting` (reflect)

Source: `lighting/lighting.glsl` (6049 bytes, `a0601f7012f385c14c1bdb9f462e5dcb303fe05cfbb4645484d5d1bd629e1a4f`). Canonical factory `canonicalFactory78` (`9c9b70f5738071d64edb39c331ebf39b0075dd215fdae61db23b381a0898f75f`). Public factory is canonical identity: true. Adapter override present: false.

**Reachability**: reflect(incident, normal) is called once inside applyReflection, itself called only when reflection>0.0 || aberration>0.0. `normal` is always normalize()'d (unit length) before it reaches reflect() in THIS program -- so the "defensive normalize" mutation is expected to be a full-render no-op here (proven, not assumed) even though it is a genuine hazard for the C++ port in general (see the direct rows for a non-unit-N discriminating case). When aberration>0 but reflection==0, applyReflection still executes and reflect() still fires (reachable, proven by call log), but its output is immediately multiplied by reflection==0, so BOTH reflect mutations are legitimately-zero-divergence for that case too -- documented with proof, not dropped.

### Cases

| Case | Size | Diagnostic | Reach | Call count | F32 SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| reflection-strong-sign-matters | 6x5 | false | true | 30 | `35b9d0303cdbac02...` |
| reflection-aberration-refraction-mixed-tiled | 5x6 | false | true | 30 | `901928e220c7e741...` |
| aberration-only-zero-offset-diagnostic | 7x4 | true | true | 28 | `5951f12f620b5e0d...` |
| all-off-diagnostic-no-reflect-call | 4x7 | true | false | 0 | `e72ea07339688d23...` |

### Mutations

| Mutation | Hazard | Case | Reach | Diverges |
| --- | --- | --- | --- | --- |
| reflect-sign-flip | wrong-sign-convention | reflection-strong-sign-matters | true | true |
| reflect-sign-flip | wrong-sign-convention | reflection-aberration-refraction-mixed-tiled | true | true |
| reflect-sign-flip | wrong-sign-convention | aberration-only-zero-offset-diagnostic | true | false |
| reflect-sign-flip | wrong-sign-convention | all-off-diagnostic-no-reflect-call | false | false |
| reflect-defensive-normalize | defensive-internal-normalize | reflection-strong-sign-matters | true | false |
| reflect-defensive-normalize | defensive-internal-normalize | reflection-aberration-refraction-mixed-tiled | true | false |
| reflect-defensive-normalize | defensive-internal-normalize | aberration-only-zero-offset-diagnostic | true | false |
| reflect-defensive-normalize | defensive-internal-normalize | all-off-diagnostic-no-reflect-call | false | false |

- **reflect-sign-flip**: reflect(I,N) = I - 2*dot(N,I)*N -> I + 2*dot(N,I)*N. The sign-convention bug the architecture doc calls out.
- **reflect-defensive-normalize**: reflect(I,N) internally normalizes N before applying the formula. GLSL's reflect() must NOT do this (spec requires the CALLER to pass unit N); diverges whenever N is not already unit length.

## `filter/fxaa:fxaa` (round)

Source: `fxaa/fxaa.glsl` (4938 bytes, `088449aa1fd5855489d3ce0c6ed2986b9b128fa93ace5817dbeafeff92a7bdf0`). Canonical factory `canonicalFactory56` (`8c707f68d552fa852fa899d377616a0c772f0ebefce3026137af301f044bb3c0`). Public factory is canonical identity: true. Adapter override present: false.

**Reachability**: as_u32(resolution.x) / as_u32(resolution.y) execute unconditionally at the top of main() -- reachable, and its result (width_u/height_u) genuinely gates an early-return (verified: shrinking it by 1 causes the last column/row to early-return to transparent black). But resolution.x/y are ALWAYS exact integers (Number.isInteger enforced by createCanonicalBindings), so round(integer) == integer under every rounding convention -- no full-render case can ever exercise a genuine tie here. sanitized_channelCount()'s round() (a second call site) is DEAD CODE: grepped, it is declared but never invoked from main().

### Cases

| Case | Size | Diagnostic | Reach | Call count | F32 SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| small-canvas-round-reachable-integer-only | 6x5 | false | true | 60 | `42f5db5fe3503ec3...` |
| tiled-canvas-round-reachable-integer-only | 5x6 | false | true | 60 | `1bbc998d30bfe2bf...` |
| wide-canvas-round-reachable-integer-only | 7x4 | false | true | 56 | `c97c68a00e8affad...` |
| tall-canvas-round-reachable-integer-only | 4x7 | false | true | 56 | `eb168d9bc4a55454...` |

### Mutations

| Mutation | Hazard | Case | Reach | Diverges |
| --- | --- | --- | --- | --- |
| round-minus-one-liveness | general-liveness | small-canvas-round-reachable-integer-only | true | true |
| round-minus-one-liveness | general-liveness | tiled-canvas-round-reachable-integer-only | true | true |
| round-minus-one-liveness | general-liveness | wide-canvas-round-reachable-integer-only | true | true |
| round-minus-one-liveness | general-liveness | tall-canvas-round-reachable-integer-only | true | true |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | small-canvas-round-reachable-integer-only | true | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | tiled-canvas-round-reachable-integer-only | true | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | wide-canvas-round-reachable-integer-only | true | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | tall-canvas-round-reachable-integer-only | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | small-canvas-round-reachable-integer-only | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | tiled-canvas-round-reachable-integer-only | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | wide-canvas-round-reachable-integer-only | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | tall-canvas-round-reachable-integer-only | true | false |

- **round-minus-one-liveness**: round(x) -> round(x) - 1 for every input, tie or not. Proves the call site genuinely executes and its result is load-bearing -- independent of the tie-break question.
- **round-bankers-spec-tiebreak**: round(x) -> round-half-to-even ("banker's rounding", the GLSL SPEC's tie-break rule). The JS reference materializes round() as Math.round (round-half-towards-+Infinity), NOT the spec's rule -- this mutation catches a spec-faithful-but-wrong C++ implementation.
- **round-away-from-zero-naive-cpp**: round(x) -> round-half-away-from-zero (what std::round actually does). Catches "I called std::round() directly" as a bug.

## `filter/grain:grain` (round)

Source: `grain/grain.glsl` (8796 bytes, `6edf8deec35e2fa3a32fc150c2be8cb6d71a9356c1c7a3cff5bd3c6c7df764f0`). Canonical factory `canonicalFactory65` (`36a15bacaf42ebe94dc587fdc77cb56a5c714cae51fd40c7f7a6a187794ef44f`). Public factory is canonical identity: true. Adapter override present: false.

**Reachability**: as_u32(res.x) / as_u32(res.y) execute unconditionally at the top of main() -- reachable, same early-return-gate structure and same always-integer-input constraint as fxaa (both proven below).

### Cases

| Case | Size | Diagnostic | Reach | Call count | F32 SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| basic-grain-round-reachable-integer-only | 6x5 | false | true | 60 | `b6d00c31bdd1a710...` |
| tiled-grain-round-reachable-integer-only | 5x6 | false | true | 60 | `4ac085e24eeff9be...` |
| paused-grain-round-reachable-integer-only | 7x4 | false | true | 56 | `c3d4dd8db65f4396...` |
| scaled-grain-round-reachable-integer-only | 4x7 | false | true | 56 | `09287ba54a6899f6...` |

### Mutations

| Mutation | Hazard | Case | Reach | Diverges |
| --- | --- | --- | --- | --- |
| round-minus-one-liveness | general-liveness | basic-grain-round-reachable-integer-only | true | true |
| round-minus-one-liveness | general-liveness | tiled-grain-round-reachable-integer-only | true | true |
| round-minus-one-liveness | general-liveness | paused-grain-round-reachable-integer-only | true | true |
| round-minus-one-liveness | general-liveness | scaled-grain-round-reachable-integer-only | true | true |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | basic-grain-round-reachable-integer-only | true | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | tiled-grain-round-reachable-integer-only | true | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | paused-grain-round-reachable-integer-only | true | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | scaled-grain-round-reachable-integer-only | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | basic-grain-round-reachable-integer-only | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | tiled-grain-round-reachable-integer-only | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | paused-grain-round-reachable-integer-only | true | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | scaled-grain-round-reachable-integer-only | true | false |

- **round-minus-one-liveness**: round(x) -> round(x) - 1 for every input, tie or not. Proves the call site genuinely executes and its result is load-bearing -- independent of the tie-break question.
- **round-bankers-spec-tiebreak**: round(x) -> round-half-to-even ("banker's rounding", the GLSL SPEC's tie-break rule). The JS reference materializes round() as Math.round (round-half-towards-+Infinity), NOT the spec's rule -- this mutation catches a spec-faithful-but-wrong C++ implementation.
- **round-away-from-zero-naive-cpp**: round(x) -> round-half-away-from-zero (what std::round actually does). Catches "I called std::round() directly" as a bug.

## `filter/snow:snow` (round)

Source: `snow/snow.glsl` (2982 bytes, `ae057787cc101755743c17b4cdf46b51d70ed8b9896fed9535a058c8b252f48a`). Canonical factory `canonicalFactory142` (`769bbb2ed7322417cb3334d9427a1037c8dd40fd55f5e003490cd0129ef109b1`). Public factory is canonical identity: false. Adapter override present: true.

**Reachability**: as_u32() -- the only function in this source that calls round() -- is DECLARED but NEVER CALLED anywhere in main() or any function main() transitively calls. Verified by grep against both the raw GLSL source (zero call sites besides the declaration) and the compiled JS factory text (same), and independently reconfirmed here at runtime: the InstrumentedRuntime call log for round() is empty for every snow case. round() is therefore fully dead code in this program -- the C++ port needs a node-identity admission for the call to type-check, but no case can or should assert non-trivial round() BEHAVIOR for snow; every mutation is expected (and proven) zero-divergence for every case.

### Cases

| Case | Size | Diagnostic | Reach | Call count | F32 SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| basic-snow-round-dead | 6x5 | false | false | 0 | `a7df02d02b40d848...` |
| tiled-snow-round-dead | 5x6 | false | false | 0 | `59f85a2587649bfe...` |
| paused-snow-round-dead | 7x4 | false | false | 0 | `74cb6af761588b7a...` |
| zero-alpha-early-exit-diagnostic | 4x7 | true | false | 0 | `51b836c9060e2395...` |

### Mutations

| Mutation | Hazard | Case | Reach | Diverges |
| --- | --- | --- | --- | --- |
| round-minus-one-liveness | general-liveness | basic-snow-round-dead | false | false |
| round-minus-one-liveness | general-liveness | tiled-snow-round-dead | false | false |
| round-minus-one-liveness | general-liveness | paused-snow-round-dead | false | false |
| round-minus-one-liveness | general-liveness | zero-alpha-early-exit-diagnostic | false | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | basic-snow-round-dead | false | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | tiled-snow-round-dead | false | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | paused-snow-round-dead | false | false |
| round-bankers-spec-tiebreak | wrong-tiebreak-rule-glsl-spec | zero-alpha-early-exit-diagnostic | false | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | basic-snow-round-dead | false | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | tiled-snow-round-dead | false | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | paused-snow-round-dead | false | false |
| round-away-from-zero-naive-cpp | wrong-tiebreak-rule-naive-cpp | zero-alpha-early-exit-diagnostic | false | false |

- **round-minus-one-liveness**: round(x) -> round(x) - 1 for every input, tie or not. Proves the call site genuinely executes and its result is load-bearing -- independent of the tie-break question.
- **round-bankers-spec-tiebreak**: round(x) -> round-half-to-even ("banker's rounding", the GLSL SPEC's tie-break rule). The JS reference materializes round() as Math.round (round-half-towards-+Infinity), NOT the spec's rule -- this mutation catches a spec-faithful-but-wrong C++ implementation.
- **round-away-from-zero-naive-cpp**: round(x) -> round-half-away-from-zero (what std::round actually does). Catches "I called std::round() directly" as a bug.

## `round()` at the six required .5 boundaries (both signs) -- direct rows

The JS reference materializes GLSL `round()` as `unary(Math.round)` (glsl-runtime.js:350) -- i.e. **round-half-towards-positive-infinity**, NOT the GLSL spec's round-half-to-even ("banker's rounding"), and NOT `std::round`'s round-half-away-from-zero. Determined empirically (Math.round semantics probed directly, not assumed from any spec):

| Input | Real (Math.round) | round-half-to-even (spec) | Diverges | round-half-away-from-zero (std::round) | Diverges | floor(x+0.5) | Diverges |
| ---: | ---: | ---: | --- | ---: | --- | ---: | --- |
| -2.5 | -2 | -2 | false | -3 | true | -2 | false |
| -1.5 | -1 | -2 | true | -2 | true | -1 | false |
| -0.5 | -0 | 0 | true | -1 | true | 0 | true |
| 0.5 | 1 | 0 | true | 1 | false | 1 | false |
| 1.5 | 2 | 2 | false | 2 | false | 2 | false |
| 2.5 | 3 | 2 | true | 3 | false | 3 | false |

Non-tie sanity inputs (must show zero divergence against every tie-break mutation -- proven, not assumed):

| Input | Real | Diverges (any mutation) |
| ---: | ---: | --- |
| -3.25 | -3 | false |
| -1 | -1 | false |
| 0 | 0 | false |
| 1 | 1 | false |
| 3.25 | 3 | false |
| 100 | 100 | false |

## `any()` discrimination -- direct rows

| Input | Real (any) | as-all result | Diverges | Reverse-order result | Diverges |
| --- | --- | --- | --- | --- | --- |
| [0,0] | false | false | false | false | false |
| [1,0] | true | false | true | true | false |
| [0,1] | true | false | true | true | false |
| [1,1] | true | true | false | true | false |
| [0,0,0] | false | false | false | false | false |
| [1,0,0] | true | false | true | true | false |
| [0,1,0] | true | false | true | true | false |
| [0,0,1] | true | false | true | true | false |
| [1,1,1] | true | true | false | true | false |
| [0,1,1] | true | false | true | true | false |

## `reflect()` discrimination -- direct rows

| Case | I | N | \|N\| | unit N | Real | Diverges (sign-flip) | Diverges (defensive-normalize) |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| unit-N-positive-dot | [0.5,0.30000001192092896,0.800000011920929] | [0,0,1] | 1.0000 | true | [0.5000,0.3000,-0.8000] | true | false |
| unit-N-negative-dot | [-0.4000000059604645,0.20000000298023224,-0.8999999761581421] | [0,0,1] | 1.0000 | true | [-0.4000,0.2000,0.9000] | true | false |
| unit-N-orthogonal-dot-zero | [1,0,0] | [0,0,1] | 1.0000 | true | [1.0000,0.0000,0.0000] | false | false |
| non-normalized-N-short | [0.6000000238418579,0.20000000298023224,0.699999988079071] | [0.10000000149011612,0,0] | 0.1000 | false | [0.5880,0.2000,0.7000] | true | true |
| non-normalized-N-long | [0.30000001192092896,-0.4000000059604645,0.8999999761581421] | [0,0,50] | 50.0000 | false | [0.3000,-0.4000,-4499.1001] | true | true |
| non-normalized-N-generic | [0.5,0.5,-0.30000001192092896] | [2,-1,4] | 4.5826 | false | [3.3000,-0.9000,5.3000] | true | true |

## Negative closure

- **any_other_define_map**: reject -- not constructible for this cluster, see defines_axis_note
- **generic_round_any_reflect_capability**: forbidden -- this oracle characterizes exactly the three node-identity call sites documented per program, never a general "admit all round/any/reflect calls" capability
- **snow_round_treated_as_render_validated**: forbidden -- validated structurally (call-log-proven unreachable) only; zero live consumers, zero divergence is EXPECTED and confirmed, not a coverage gap

