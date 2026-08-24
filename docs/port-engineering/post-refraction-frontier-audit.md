# Post-refraction frontier audit: Task 22 direct-local `inout vec3`

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, assuming proposed Tasks 12–21.
Derivatives remain excluded: one `PixelContext` invocation cannot define GLSL
fragment-neighborhood semantics.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 21 | 139 | 141 | 71 |

## Recommendation: `direct-local-inout-vec3-v1`

The exact next coherent slice is one non-aliasing `inout vec3` compare-exchange
helper.  It ports a complete watercolor simplification pass without adding
general output parameters, structs, buffers, stage inputs, loops, arrays, or
new mathematical operations.

| Key | Exact default defines | Admitted helper and calls |
| --- | --- | --- |
| `filter/watercolor:wcSimplify` | `{}` | `void sort2(inout vec3 a, inout vec3 b)` called 19 times with two distinct local `vec3` identifiers |

`sort2` constructs `lo=min(a,b)` and `hi=max(a,b)`, then assigns them back to
the two formal parameters.  Every actual is one of the initialized local
`p0`…`p8` values; every call supplies distinct stable symbols.  The pass has
only ordinary texture sampling, scalar/vector arithmetic, constructors,
min/max, clamp, mix, swizzles, and direct calls already covered by previous
slices.  Its sole remaining projected frontend blocker is parameter direction.

This is intentionally not an `out` feature and not a general `inout` ABI:
there are no scalar/vector-width variants, arrays, struct fields, swizzles,
index expressions, uniforms, global variables, returned references, or
aliasing actual arguments in scope.

## Fail-closed typed/emitter/runtime contract

1. Permit an `inout` parameter only in an exactly matched helper signature
   `void(inout vec3, inout vec3)`.  The helper must have a `void` result,
   exactly two parameters, no overload family, no recursion, no function
   pointers, and no other non-`in` parameters.  Keep all `out` parameters
   rejected.
2. A call to that helper must pass exactly two direct identifier lvalues that
   resolve to distinct function-local `vec3` symbols.  Both locals must be
   definitely initialized on every incoming path.  Reject the same symbol in
   both positions; global/uniform/output/interface symbols; parameters;
   swizzles; indexed values; fields; constructors; temporaries; conditional
   expressions; and calls nested in an argument.  This proves no observable
   aliasing or argument-evaluation ambiguity.
3. Retain the direction, parameter/actual stable symbol IDs, direct-local
   proof, non-alias proof, and definite-initialization proof in typed IR.
   Validation must occur before emission and be allowlisted to the one key and
   metadata-verified `{}` define map; a syntactically similar `inout` program
   remains rejected.
4. Emit only this direction as `glsl::Vec3&` in both the generated declaration
   and definition, and pass the direct local values by reference at the direct
   static C++ call site.  Since actual symbols are distinct, this is equivalent
   to the admitted GLSL copy-in/copy-out behavior for this helper.  Do not use
   pointer arithmetic, heap boxes, `std::reference_wrapper`, a variant, a
   lambda, or a function pointer.  Existing `Vec3` automatic values and
   ordinary assignment preserve the established f32 lane boundary.
5. Enforce at most two admitted `inout vec3` parameters per helper, one such
   helper per program, call depth one, and 20 admitted calls per entrypoint.
   `wcSimplify` has exactly one helper and 19 compare-exchange calls.  Reject
   an escaping reference, a call from an admitted helper, or any attempt to
   store a reference in state.  `PixelFn` stays `noexcept`, allocation-free,
   and without per-pixel dynamic dispatch.

Required positives are a frozen default-key oracle over low/mid/high `detail`
values and nonuniform 3×3 texture neighborhoods that force every one of the
19 compare-exchanges, including different median lane orderings.  Add a direct
helper test showing each input local is updated independently and the output
alpha remains `s4.a`.  Required negatives reject `out`, one or three
parameters, `inout float`/`vec2`/`vec4`, duplicate actuals, a swizzle or array
element actual, an uninitialized local, a non-local actual, recursive/helper
calls, an escaping reference, and default-define drift.  Compile generated
C++ with warnings as errors and verify zero hot-path allocations and indirect
calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 22 | **140** | **142** | **70** |

## Ranked residual map after Task 22

The categories below are separate capability decisions, not permission to
broaden the direct-local reference contract.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Dynamic-loop runtime contracts | blur H/V, `normalize:statsFinal`, `tetraColorArray`, `nmReindexReduce`, `zoomBlur`, `oilFlatten` | Each requires a distinct resource/bound proof: validated render scale, texture dimensions, metadata range enforcement, work-charge budget, or non-integral induction. |
| 2 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, mixer distortion | `dFdx`/`dFdy`/`fwidth` require specified quad/neighborhood, border, and scheduling semantics. |
| 3 | Other builtin/operator families | `synth/curl` vector `tanh` plus wider `mod`; signed bitwise `bitEffects`; nonzero LOD sampling | Their numeric, bit, or mip contracts are unrelated to parameter mutation. |
| 4 | General `out`/`inout` ABI | Julia, Mandelbrot, and Newton multi-output helpers | Need copy-out ordering, multi-result representation, scalar/vec2 support, and call-site alias policy beyond two direct local vec3s. |
| 5 | Structs | historicPalette, palette, Julia, Newton | Needs aggregate initialization, field access, passing, and lifetime rules. |
| 6 | UBO/varying stage data | remap UBO; grime, texture, spookyTicker, wobble, wormhole deposit varyings | Requires std140 layout or explicit stage-input ownership and binding validation. |
| 7 | General arrays/matrices | global arrays in cellRefract/kaleido and mat4 effects | Fixed local arrays and one direct-reference helper do not establish global lifetime, arbitrary indexing, mat4 algebra, or mutable-state isolation. |

Task 22 adds one default-configuration factory while preserving the derivative
hold and leaving general function, aggregate, data-interface, and loop ABIs
independently reviewable.
