# Post-`out`-params frontier audit: Task 45 preflight-bounded Gaussian blur

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-44.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 44 | 166 | 168 | 44 |

## Recommendation: `blur-preflight-radius-bound-v1`

The next smallest coherent slice is the horizontal/vertical Gaussian pair.
Both use the same source shape and require one new runtime-preflight proof for
their local dynamic symmetric loop; neither requires a derivative, aggregate,
or new sampler semantic.

| Key | Exact defines | Source SHA-256 | Axis binding |
| --- | --- | --- | --- |
| `filter/blur:blurH` | `{}` | `c4283e820b2ade9148358ad4582d350bc7f4a5ccb5fc60f2e1b76bcda58deecc` | `radiusX` |
| `filter/blur:blurV` | `{}` | `cc33343032b34e1ede6eed15fbdcb9229ad64484a092b2914065b09fa957fb9b` | `radiusY` |

For the selected axis, metadata supplies `0 <= radiusAxis <= 50`. Before
binding either generated factory, preflight must require finite values,
`radiusAxis` in that interval, nonnegative finite `renderScale`, and the exact
source-equivalent checked conversion
`r = int(f32(radiusAxis) * f32(renderScale))` in `0..63`. A failure rejects
the invocation; it must not clamp, substitute, or silently reduce the radius.
For `r <= 0`, the authored early return bypasses the loop. For `r=1..63`, the
only loop is exactly `for (int i = -r; i <= r; i++)`, with `2r+1` visits and a
hard maximum of 127 per pixel per pass.

Both sources have one literal `const float PI`, but no reads; it remains in
typed IR for source fidelity and produces no emitted local. Otherwise they
reuse direct texture sampling, `textureSize`, `exp`, local arithmetic/control
flow, and ordinary `in` values. They have no derivative, array, matrix,
struct, uniform block, varying, helper parameter, `textureLod`, boolean
vector, or mutable global state.

## Fail-closed typed/emitter/runtime contract

1. Admit only the two sorted blur keys, with their metadata-verified empty
   define maps and pinned source hashes above. Reject another key, a
   nonempty/absent/additional define, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Add a typed binding preflight for exactly `radiusX`/`radiusY` and
   `renderScale`. Preserve Float32 materialization, finite/range checks, and
   checked GLSL float-to-int conversion in immutable binding evidence. Require
   the selected radius to be within metadata's `0..50`, `renderScale >= 0`, and
   resulting `r` in `0..63`; reject NaN, infinity, negative values, overflow,
   a missing proof, or a different cap. Do not mutate/rebind the user value.
3. Permit only the direct local declaration `int r = int(radiusAxis *
   renderScale)` and the paired authored guard `if (r <= 0) return`. Then
   permit exactly one loop `i=-r; i<=r; i++`, with stable local identities,
   contiguous interval proof, no break/continue/return in the loop, and a
   per-pass charge of at most 127. Reject another dynamic bound, arithmetic
   loop header variant, nested/dynamic loop, recurrence, allocation size,
   index proof, or loop-controlled resource selection.
4. Emit the established checked local `std::int32_t r` and direct structured
   C++ loop. Preserve the source's per-iteration direct texture sample and
   Float32 destination boundaries; do not unroll an unbounded count, add a
   bounds-check slow path, use heap storage, or introduce pointer/reference
   escape, callback, virtual dispatch, map, variant, or indirect call.
5. Bind each authored pass exactly: `tileOffset`, `fullResolution`, `inputTex`,
   the selected radius axis, and `renderScale`. The metadata pipeline remains
   two explicit passes (`blurH -> _blurTemp`, then `blurV -> outputTex`); this
   slice exposes individual factories only and must not add an adapter or
   render graph. `PixelFn` remains `noexcept` and allocation-free.

Required positives are frozen horizontal and vertical oracles for radius zero,
sub-integer/threshold values, `r=1`, interior values, and `r=63`; non-square
textures; alpha; and directional impulse/edge patterns. Direct tests must lock
the preflight Float32 conversion, rejection versus early-return distinction,
the exact symmetric coordinate sequence, sample count `2r+1`, 127-visit cap,
PI omission, both binding matrices, and byte-identical repeat rendering.

Required negatives reject source/define/hash drift; a third key; missing,
wrong-typed, NaN, infinite, negative, metadata-out-of-range, or cap-exceeding
axis/scale; clamp/substitution behavior; altered guard/header/update; a second
or nested dynamic loop; loop-derived indexing/allocation; derivative, array,
matrix, aggregate, uniform block, varying, non-`in` parameter, sampler array,
nonzero/computed LOD, or macro expansion. Compile generated C++ with warnings
as errors and assert zero hot-path allocations and indirect calls.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 45 | **168** | **170** | **42** |

## Ranked residual map after Task 45

This pair's preflight proof does not establish arbitrary uniform-driven work,
general render-scale policy, source aggregates, or neighboring-pixel
evaluation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Texture-dimension and larger-work contracts | `normalize:statsFinal`, `nmReindexReduce` | Texture-size or much larger charged-work bounds need independently enforced resource proofs. |
| 3 | Larger aggregate and word/index forms | OSD, dither, median, test pattern | Require larger arrays, general indexing/lifetime, sorting, or broader signed-word contracts. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, remaining scalar bitwise paths | Need independent mip/filter or two's-complement rules. |

Task 45 adds two hash-pinned typed factories in this relative projection while
preserving the derivative hold and every broader dynamic-work, aggregate,
loop, matrix, stage, index, numeric, sampling, and macro boundary.
