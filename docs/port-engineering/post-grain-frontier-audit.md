# Post-grain frontier audit: Task 25 metadata-ranged counted loop

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after proposed Tasks 12–24.
Derivative semantics remain held: the single-pixel CPU ABI has no
fragment-neighborhood or quad model.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 24 | 143 | 145 | 67 |

## Recommendation: `metadata-ranged-counted-loop-v1`

The next coherent non-derivative slice is the one metadata-ranged loop whose
cost is small and fully auditable when the range is enforced once at factory
binding.  It adds neither a general dynamic-loop rule nor a per-pixel range
check.

| Key | Exact default defines | Checked bound / loop |
| --- | --- | --- |
| `filter/tetraColorArray:tetraColorArray` | `{}` | `colorCount` is metadata `int`, min 2, default 6, max 8; `for (int i = 1; i < count; i++)` has at most 7 trips |

The generated helper is called only as
`sampleColorArray(t, colorCount, smoothness)`.  Its `count` parameter is a
direct, by-value propagation of the one uniform with the frozen range
contract; it is never reassigned before the loop.  The helper has no nested
loop, array indexing, derivative, out/inout parameter, struct, UBO, varying,
or additional unsupported builtin.  Thus it is a closed extension of Task
15's counted-loop proof once the binding range becomes an executable
precondition rather than metadata documentation.

## Fail-closed typed/emitter/runtime contract

1. Admit one loop form only: a fresh local `int i` initialized to literal 1,
   condition `i < count`, and `i++`, where `count` is the exact `int` helper
   parameter proven to originate unchanged from the selected program's
   `colorCount` uniform.  Its checked interval must be `[2,8]`, giving
   induction interval `[1,7]` and charged maximum 7.  Reject other function
   parameters, arithmetic/casts/clamps around the parameter, mutation,
   aliases, texture dimensions, metadata-only assertions, `while`, float or
   uint induction, and nested dynamic loops.
2. Store the bound's provenance in immutable typed IR: metadata record hash or
   pinned source identity, uniform symbol ID/name/type, inclusive min/max,
   helper parameter ID, direct call-site ID, loop induction interval, and
   maximum charge.  The emitter must consume this proof, never rediscover it
   from source text.  Any call other than the exact direct propagation is a
   validation failure.
3. In the generated factory, bind `colorCount` once as `std::int32_t` and
   validate `2 <= colorCount && colorCount <= 8` before constructing `State`.
   Missing/wrong-typed/out-of-range binding throws `KernelBindingError`; valid
   value is captured as immutable typed state.  The generated metadata check
   must fail generation if the authoritative `int`/2/6/8 contract drifts.
4. Emit an ordinary direct C++ `for (std::int32_t i = 1; i < count; ++i)` in
   the helper, tagged with the IR charge proof.  There is no runtime cap check
   in the pixel loop because the factory guard establishes it.  The hot path
   has at most seven iterations, automatic locals only, no allocation,
   virtual dispatch, function pointer, variant/map lookup, or neighbor-pixel
   access; `PixelFn` remains `noexcept`.
5. Cap this feature at one ranged uniform, one propagated helper parameter,
   one dynamic loop, depth one, and eight charged visits per program.  Reject
   range-bearing values stored in arrays/structs/state beyond the immutable
   scalar field, returned through a helper, or reused as an index/LOD/other
   loop bound.  This prevents a key-specific bounded loop from becoming a
   general metadata-to-control-flow channel.

Required positives are frozen renders at color counts 2, 6, and 8; color modes
0–3; auto/manual positions; zero/nonzero smoothness including wrap-seam
blending; and alpha endpoints.  Binding tests must reject count 1 and 9 before
the factory returns, as well as missing/wrong type.  Required negatives reject
a changed metadata maximum, a transformed or reassigned `count`, another
helper caller, an extra loop, a texture-size bound, float induction, and an
attempt to rely on the default 6 without a binding guard.  Compile emitted C++
with warnings as errors and prove zero allocations/indirect calls inside the
pixel body.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 25 | **144** | **146** | **66** |

## Ranked residual map after Task 25

The following are independent frontiers, not authority to generalize the
metadata-ranged-loop path.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Other dynamic-loop/resource models | blur H/V, `normalize:statsFinal`, `nmReindexReduce`, zoomBlur, oilFlatten | Need validated render scale, texture-size charge, a 512² work policy, float induction, or a ceil-derived bound—not a small metadata range. |
| 3 | Remaining numeric and word operations | signed bitEffects, curl vector `tanh` plus wider `mod`, vector `round`, general shifts/masks | Need separate two's-complement, shift-count, or vector builtin contracts. |
| 4 | General output/aggregate ABI | Julia, Mandelbrot, Newton; historicPalette, palette | Multi-output copy-out and struct layout/passing are not loop-bound provenance. |
| 5 | UBO/varying stage data | remap UBO; grime, texture, spookyTicker, wobble, wormhole deposit | Requires std140 layout or explicit stage-input ownership in `PixelContext`. |
| 6 | Arrays/matrices | global arrays in cellRefract/kaleido/normalMap and mat4 effects | Local typed storage does not establish global lifetime, arbitrary indexing, or mat4 algebra. |
| 7 | General sampling | nonzero/computed `textureLod`, other sampler types | Requires owned mip storage and pinned filtering policy. |

Task 25 adds one bounded default-configuration factory while retaining the
derivative hold and keeping all broader loop, interface, array, matrix, and
numeric decisions separately reviewable.
