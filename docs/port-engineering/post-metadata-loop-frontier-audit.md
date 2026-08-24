# Post-metadata-loop frontier audit: Task 26 exact float-induction lowering

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, assuming proposed Tasks 12–25.
Derivatives remain unavailable without a specified quad/neighborhood ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 25 | 144 | 146 | 66 |

## Recommendation: `fixed-float-induction-41-v1`

The next coherent slice lowers one statically enumerable source float loop to
its exact 41 iteration values.  It is not general float-loop support and does
not introduce a runtime-bound or resource-dependent loop.

| Key | Exact default defines | Proven source loop |
| --- | --- | --- |
| `filter/zoomBlur:zoomBlur` | `{}` | `for (float t = 0.0; t <= 40.0; t++)`, exactly `t = 0.0` through `40.0` |

Every induction value is an exactly representable binary32 integer and the
loop body has no mutation of `t`, no `break`, `continue`, `return`, nesting,
array/index access, derivative, or parameter-direction feature.  Its PRNG
uses only the already-admitted `uvec3 >> uint` and uvec3 XOR forms.  Therefore
the non-integral induction syntax is its sole projected blocker after prior
slices.

## Fail-closed typed/emitter/runtime contract

1. Admit exactly one `for` shape: a fresh `float` induction symbol initialized
   by canonical f32 `0.0`, condition `t <= 40.0`, postfix `t++`, no writes to
   `t` in the body, and no loop control statement.  Prove all 41 values in
   the closed sequence `[0, 1, ..., 40]`; reject `float` comparisons other
   than this exact shape, other starts/stops/steps, `+=`, prefix increment,
   dynamic bounds, nonfinite literals, nested loops, aliases, and all
   `while`/`do` loops.
2. Encode a `fixed_float_induction` proof in immutable typed IR containing the
   source symbol, f32 start/limit/step values, inclusive iteration count 41,
   no-write/control-flow proof, source span, and total work charge 41.  The
   emitter consumes this node rather than recognizing a float loop textually.
3. Emit a bounded integer driver and a source-value local, for example:

   ```cpp
   for (std::int32_t iteration = 0; iteration < 41; ++iteration) {
     const double t = static_cast<double>(iteration);
     // lowered original body
   }
   ```

   The values 0 through 40 are exact in both binary32 and the generated scalar
   representation, so this preserves the source induction sequence without
   relying on host float-increment behavior.  Keep existing f32 consumption
   boundaries for operations receiving `t`; do not unroll by source text,
   use a host `float` progression, or generalize the conversion to other
   source loops.
4. The generated loop has fixed automatic locals and 41 charged visits; it
   creates no allocation, bounds check, state mutation, virtual dispatch,
   function pointer, callback, map/variant lookup, or neighboring-pixel read.
   `PixelFn` remains `noexcept` and allocation-free.
5. Cap this feature at one fixed float loop per program, depth one, 41 visits,
   and one induction symbol.  Reject a loop value used as an index, array
   extent, LOD, state field, or additional loop bound.  A distinct loop form
   must obtain its own range and numeric-sequence proof.

Required positives are frozen zoomBlur renders at zero, midrange, and maximum
strength; non-square input textures; shifted tiles; and output pixels that
exercise all 41 samples.  Add an IR/emitter test that captures the exact
sequence `[0..40]` and the fixed charge.  Required negatives reject `t <
40.0`, `t <= 40.5`, `t += 1.0`, `t += 0.5`, a body write, a break/continue,
nested float loop, dynamic limit, an iteration count of 42, and define-map
drift.  Compile generated C++ with warnings as errors and prove no hot-path
allocation or indirect dispatch.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 26 | **145** | **147** | **65** |

## Ranked residual map after Task 26

These are separate capabilities, not extensions of the exact 41-value loop.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Other resource/dynamic loop models | blur H/V, `normalize:statsFinal`, `nmReindexReduce`, oilFlatten | Need render-scale validation, texture-size charge, a 512² work policy, or a ceil-derived uniform bound. |
| 3 | Remaining numeric and word operations | signed bitEffects, curl vector `tanh` plus wider `mod`, vector `round`, general shifts/masks | Need independent two's-complement, shift-count, or vector builtin contracts. |
| 4 | General output/aggregate ABI | Julia, Mandelbrot, Newton; historicPalette, palette | Multi-output copy-out and struct layout/passing exceed local induction semantics. |
| 5 | UBO/varying stage data | remap UBO; grime, texture, spookyTicker, wobble, wormhole deposit | Requires std140 layout or a pinned stage-input representation in `PixelContext`. |
| 6 | Arrays/matrices | global arrays in cellRefract/kaleido/normalMap and mat4 effects | Needs global lifetime/indexing or mat4 algebra beyond local automatic values. |
| 7 | General sampling | nonzero/computed `textureLod`, other sampler types | Requires owned mip storage and a pinned filtering policy. |

Task 26 adds one fully static default-configuration factory while preserving
the derivative hold and leaving all broader looping, interface, array, matrix,
and numeric frontiers independently reviewable.
