# Post-round frontier audit: Task 24 fixed-splat `uvec3` shift

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after proposed Tasks 12–23.
Derivatives remain held pending an explicit fragment-neighborhood/quad ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 23 | 142 | 144 | 68 |

## Recommendation: `uvec3-shift-splat16-v1`

The next coherent slice is one exact lane-wise unsigned shift form that
unlocks the grain pass.  It does not admit a general vector shift amount or
any signed shift/bitwise operation.

| Key | Exact default defines | Admitted expression |
| --- | --- | --- |
| `filter/grain:grain` | `{}` | `uvec3_value >> uvec3(16u)` as the right operand of existing `uvec3 ^ uvec3` |

`grain`'s `pcg3d` helper contains one precise form:

```glsl
v = v ^ (v >> uvec3(16u));
```

Task 23 supplies its scalar `round` call; Task 14 covers its read-only source
constants; Task 13 covers its level-zero `texelFetch`; and the existing
unsigned-vector arithmetic/XOR machinery covers the rest.  The prior vector
shift contract accepts `uvec3 >> uint` but rejects `uvec3 >> uvec3`; this
fixed splat is the sole remaining projected blocker.  A corpus-wide shift
census finds no other vector-right-hand-side shift form.

## Fail-closed typed/emitter/runtime contract

1. Admit only binary `uvec3 >> uvec3 -> uvec3` when the RHS is exactly the
   typed constructor `uvec3(16u)`: one canonical uint literal argument, no
   unary/binary expression, no symbol, no swizzle, no cast, and no alternate
   constructor spelling.  The left operand must be a `uvec3` rvalue.  Reject
   `uvec2`, `uvec4`, scalar/signed shifts, other counts, computed lane counts,
   variable shift vectors, `<<`, `&`, `|`, and every compound shift assignment.
2. Preserve an immutable IR proof recording the left type, RHS constructor
   shape, all-lane literal value 16, result type, and source span.  Validation
   binds this exact form to `filter/grain:grain` and the metadata-verified
   empty define map.  An ordinary `uvec3 >> uvec3` node without that proof is
   rejected before emission.
3. Emit the already-existing direct helper with its scalar shift overload:

   ```cpp
   glsl::shift_right(value, std::uint32_t{16})
   ```

   It shifts each of the three unsigned lanes by the known in-range count and
   returns an automatic `UVec3`.  This is semantically identical to the
   admitted splat vector and avoids a generic vector-count helper.  Keep the
   existing `uint-vector-bitwise` XOR lowering for the outer operation.
4. Do not add state, heap storage, `std::variant`, virtual dispatch, callbacks,
   pointer arithmetic, or a per-pixel bounds/dispatch branch.  The helper is
   fixed work on three words, is `noexcept`, and preserves the allocation-free
   `PixelFn` path.
5. Cap the extension at one fixed-splat shift per helper and two per program;
   the selected `pcg3d` helper has one.  Reject nested shift amounts, any
   result used as an index/loop bound/ABI field, or another right-hand-side
   vector width/count.  This cap prevents the exact lowering from becoming a
   general vector-bitwise facility.

Required positives are frozen grain renders across alpha-zero/active,
pause/time, non-square texture dimensions, and render-scale inputs, alongside
direct lane tests with distinct high-bit words.  Verify each lane equals its
own logical right shift by 16 and that the following XOR is lane-local.
Required negatives reject `uvec3(15u)`, `uvec3(17u)`, `uvec3(n)`, a three-lane
constructor, `uvec2`/`uvec4`, signed vectors, `<<`, and a wrong define map.
Compile the generated C++ with warnings as errors and assert no hot-path
allocation or indirect dispatch.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 24 | **143** | **145** | **67** |

## Ranked residual map after Task 24

These frontiers remain independent and are not authorized by a fixed unsigned
word operation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Dynamic-loop/resource contracts | blur H/V, `normalize:statsFinal`, `tetraColorArray`, `nmReindexReduce`, `zoomBlur`, `oilFlatten` | Needs exact render-scale, texture-size, metadata-range, work-charge, or non-integral-loop proof. |
| 2 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require neighborhood, border, and execution-order semantics. |
| 3 | Other numeric/bit overloads | signed `bitEffects`; curl vector `tanh` plus wider `mod`; vector `round`; scalar/general shift/mask forms | Each requires separate GLSL integer-wrap, shift-count, or vector numeric rules. |
| 4 | General output/aggregate ABI | Julia, Mandelbrot, Newton; historicPalette, palette | Multi-output copy-out and struct layout/passing are outside a local word expression. |
| 5 | UBO/varying stage data | remap UBO; grime, texture, spookyTicker, wobble, wormhole deposit | Requires std140 layout or a pinned stage-input representation in `PixelContext`. |
| 6 | Arrays/matrices | global arrays in cellRefract/kaleido/normalMap and mat4 effects | Local stack arrays/vector lanes do not establish global lifetime, arbitrary indexing, or mat4 algebra. |
| 7 | General sampling | nonzero/computed `textureLod`, other sampler types | Requires owned mip storage and a pinned filtering policy. |

Task 24 adds one fully specified default-configuration factory while retaining
the derivative hold and keeping general bitwise, interface, array, matrix, and
dynamic-loop work separately reviewable.
