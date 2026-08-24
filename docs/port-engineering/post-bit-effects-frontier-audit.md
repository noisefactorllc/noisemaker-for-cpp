# Post-bit-effects frontier audit: Task 31 direct sampler helper parameters

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12–30.
Derivative semantics remain unavailable pending a deliberately specified
fragment-neighborhood/quad ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 30 | 149 | 151 | 61 |

## Recommendation: `direct-sampler2d-helper-v1`

The next smallest closed frontier is the fixed-cost focus-blur mixer.  Its
64-sample loop is already within Task 15's literal counted-loop contract; the
only missing representation is its direct sampler2D helper parameters.

| Key | Exact default defines | Exact admitted helper |
| --- | --- | --- |
| `mixer/focusBlur:focusBlur` | `{}` | `vec4 applyFocusBlur(in sampler2D sceneTex, in sampler2D depthTex, in vec2 uv)` |

`main` makes the only two sampler-parameter calls, with the direct uniform
samplers in swapped order according to `depthSource`:

```glsl
applyFocusBlur(tex, inputTex, uv)
applyFocusBlur(inputTex, tex, uv)
```

The helper reads `depthTex` once, then performs the exact literal
`for (int i = 0; i < 64; i++)` scene-sampling sequence.  It uses only
existing level-zero `texture`, `textureSize`, `sqrt`, `cos`, `sin`, dot,
clamp, and scalar/vector arithmetic.  The typed resource set is exactly two
samplers (`inputTex`, `tex`) plus normal uniforms; it uses neither derivative
nor texture LOD, array, matrix, UBO, varying, macro, non-`in` parameter, or
resource-derived loop bound.  At most 67 samples occur per pixel: one depth
sample, 64 scene samples in the selected branch, and two alpha reads.

This is smaller than blur H/V or normalize stats because the work charge is
fixed by source syntax rather than render scale or texture dimensions.  It
does not create a multi-pass runner: this one typed factory remains a single
pass whose two input surfaces are supplied by the caller.

## Fail-closed typed/emitter/runtime contract

1. Admit only `mixer/focusBlur:focusBlur` and its metadata-verified empty
   define map.  Reject any define, macro variant, other program key, sampler
   kind, or effect-graph expansion.
2. Permit exactly one helper signature with input directions only:

   ```text
   vec4 applyFocusBlur(sampler2D sceneTex, sampler2D depthTex, vec2 uv)
   ```

   Retain each parameter's type, `in` direction, stable symbol ID, and the
   resolved call signature in immutable typed IR.  There are exactly two
   sampler parameters, one vec2 parameter, one vec4 result, and no overload.
   Reject a sampler return, sampler local/global, sampler constructor, array,
   struct field, function pointer, recursion, `out`/`inout`, a different
   helper name/signature, or a second sampler-taking helper.
3. Each sampler actual must be a direct sampler-uniform identifier resolving
   to `inputTex` or `tex`, passed only at the two recorded call sites.  Permit
   the two inputs to alias the same `Surface`, because this helper is read-only;
   reject an expression, swizzle, array/field element, temporary, nested call,
   local alias, conditional sampler selection, nonuniform sampler, or sampler
   stored in state beyond the existing uniform-binding pointer.
4. Lower the helper-only `sampler2D` parameter type to `const Surface&` in
   generated C++ declarations and definitions.  The factory-owned `State`
   keeps its existing non-owning `const Surface*` fields; the two direct call
   sites dereference those validated binding pointers to form borrowed
   references.  `sample_texture` and `texture_size` consume those references
   directly.  No `Surface` copy, pointer parameter, ownership transfer,
   allocation, registry lookup, or new sampler runtime object is introduced.
5. Bind the existing Task-15 fixed-loop proof to this key: exactly one fresh
   `int i`, literal initial 0, `i < 64`, postfix `i++`, no loop control or
   body write to `i`, and a charged 64 visits.  Cap the helper at one depth
   read, 64 scene reads, and the entrypoint at two extra alpha reads.  Reject
   a dynamic bound, altered trip count, nesting, `break`/`continue`/`return`,
   sampler-dependent control/loop/index/LOD use, or a total charge above 67
   samples.
6. Emission uses automatic locals, direct calls, and existing nearest-sampler
   semantics only.  The per-pixel `PixelFn` remains `noexcept`, allocation
   free, and free of virtual/function-pointer dispatch, callbacks, variants,
   maps, or neighbor-pixel/derivative access.

Required positives are frozen default-key oracles with `depthSource=0` and
`depthSource=1`, equal source-surface aliasing, non-square input dimensions,
edge/corner coordinates, focal-distance/aperture extremes, and sample-bias
values that visibly exercise the golden-angle offsets.  Add emitter tests for
the exact `const Surface& sceneTex`/`depthTex` signatures and both direct
state-pointer dereference call orders; binding tests must reject a missing or
wrong-type `inputTex` or `tex`.  Assert the IR loop charge is 64 and the
per-pixel texture-read cap is 67.

Required negatives reject a single/third sampler parameter, a sampler
parameter in another helper, pointer/reference/return sampler types,
`out`/`inout`, a local sampler alias, non-direct actual, texture LOD, dynamic
loop bound, 65th loop iteration, sampler used as an index/ABI field, an extra
sample call, a nonempty define map, and every derivative builtin.  Compile
generated C++ with warnings as errors and assert zero hot-path allocations and
indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 31 | **150** | **152** | **60** |

## Ranked residual map after Task 31

These remain independent frontiers; a read-only sampler helper does not
authorize general resource, interface, or stage-data support.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Need separately validated render scale, texture-dimension/work policy, or a much larger 512-by-512 budget. |
| 3 | General sampler/interface adapters | arbitrary sampler parameters, pass chaining, sampler arrays | Need ownership, aliasing, and call-ABI rules beyond two direct read-only references. |
| 4 | Aggregate and stage interfaces | Julia, Mandelbrot, Newton; historicPalette, palette; remap UBO; grime/texture varyings | Multi-output copy-out, structs, std140, and stage inputs each need their own representation contract. |
| 5 | Arrays and matrices | global arrays, normalMap, kaleido, mat4 effects | Need global lifetime/indexing or broader matrix algebra beyond automatic locals. |
| 6 | General signed-word and numeric forms | nonconstant signed shifts/masks, vector round | Need their own shift-count or vector numeric contracts. |
| 7 | General sampling and macro variants | computed/nonzero `textureLod`; nondefault oil MODE values | Need owned mip/filter semantics or an independently audited preprocessor configuration family. |

Task 31 adds one all-default, fixed-cost single-pass factory while retaining
the derivative hold and all broader dynamic-loop, sampler, aggregate, stage,
array, matrix, numeric, and macro boundaries.
