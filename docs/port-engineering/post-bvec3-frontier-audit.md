# Post-`bvec3` frontier audit: Task 37 fixed-scan scalar `ceil`

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-36.
Derivative semantics remain unavailable because the current per-pixel ABI has
no fragment-neighborhood, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 36 | 157 | 159 | 53 |

## Recommendation: `smooth-blend-fixed-scan-ceil-v1`

The next smallest exact slice is one all-default pass that reuses the
projected Task-34 literal `vec3` const, Task-15 counted loops, Task-13
level-zero `texelFetch`, and Task-28 scalar `ceil` numeric path:

| Key | Exact default defines | Exact new allowlist expansion |
| --- | --- | --- |
| `filter/smooth:smoothBlend` | `{}` | one `ceil(float radius) -> float`, converted once to local `int r` |

The only ceiling call is `int r = int(ceil(radius));` in `edgeBlur`. `r` is
used solely by the two guard predicates `abs(dx) > r` and `abs(dy) > r` inside
the statically bounded `-4..4` pair; it never supplies a loop initializer,
condition, update, allocation size, texture coordinate extent, or recursion
depth. The blur scan therefore remains exactly 81 charged visits, regardless
of runtime `radius`.

The program's remaining bounded loops are exactly `i=0..<8` (MSAA sampling)
and `i=1..32` (edge search), each with existing structured early break; its
two sampler uniforms are read directly by helpers. The sole source global is
the already-projected literal `const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587,
0.114)`, read only by `luminance`. A read-only replay that exposes only this
const form, the counted loops/control flow, and the one scalar `ceil` call
passes every later current capability gate. The source has no derivative,
array, matrix, struct, UBO, varying, sampler parameter, non-`in` parameter,
or nonempty metadata define.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/smooth:smoothBlend` with its metadata-verified empty
   define map. Reject every other key, nonempty define map, source rewrite,
   macro configuration, or `ceil` caller.
2. Reuse the Task-34 source-local vector contract only for the exact literal
   `LUMA_WEIGHTS` declaration and its helper-only `dot` use. Materialize one
   automatic `const glsl::Vec3` in `luminance`; reject other vector globals,
   computed/dependent initializers, writes, aliases, main-level reads, and
   static/global storage.
3. Permit exactly one resolved scalar builtin node:

   ```text
   ceil(float radius) -> float
   ```

   It must be the direct child of the source `int(...)` conversion that
   initializes fresh local `r` in `edgeBlur`. Preserve its source span,
   overload, result type, conversion, target symbol, and downstream-use proof
   in immutable typed IR. Reject vector/signed/unsigned overloads, a second
   call, a call in another function, arithmetic-wrapped operands, and a result
   passed, returned, stored in state, or used as a loop bound.
4. Prove `r` is read only by the two scalar guard comparisons in the exact
   `dy=-4..4`, `dx=-4..4` nested loops. Reuse the existing fixed-loop proof:
   9 visits per dimension, 81 combined visits, `continue` only, and no
   loop-contained return. Keep the separate 8- and 32-visit loops under their
   existing caps; a runtime `samples` or `searchSteps` value can select an
   existing early break but cannot enlarge a lexical loop.
5. Emit the established scalar ceiling helper with the existing GLSL
   Float32 boundary, then the existing checked float-to-int conversion and
   ordinary local `std::int32_t r`. Do not add an allocation, dynamic loop,
   bounds-check slow path, pointer/reference escape, virtual dispatch,
   callback, map, or variant. `PixelFn` stays `noexcept` and allocation-free.

Required positives are frozen smooth-blend oracles for all three `smoothType`
branches (MSAA, SMAA, blur), radius values below an integer, at an integer,
and above it including negative radius, sample/search early exits, asymmetric
edge textures, and non-square dimensions. Direct tests must lock one ceiling
node, the conversion/local target, the two guard uses, 8/32/81 loop charges,
helper-local LUMA injection, and level-zero fetches from both samplers.

Required negatives reject a second/vector/different `ceil`, a ceiling result
used as a loop bound/allocation/index, a changed scan range, dynamic induction,
new loop nesting, vector-global drift, sampler parameters/arrays, nonempty
defines, another key, and every derivative builtin. Compile generated C++
with warnings as errors and assert zero hot-path allocations and indirect
calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 37 | **158** | **160** | **52** |

## Ranked residual map after Task 37

This guard-only scalar ceiling does not define uniform-derived loop bounds or
any neighboring-pixel execution behavior.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Need independently validated render scale, texture-dimension/work policy, or a much larger work budget. |
| 3 | General `ceil` and numeric flows | uniform-driven bounds, vector ceil, other integer conversions | Need independent overload, overflow, and bound-provenance rules. |
| 4 | General boolean/global/indexing forms | bvec reductions, computed vector globals, global arrays, dynamic vector/matrix indexing | Need broader type, initialization, range, lifetime, and aliasing rules. |
| 5 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need different layout, copy-out, binding, and stage ownership contracts. |
| 6 | Sampling and macro extensions | computed/nonzero `textureLod`, sampler arrays, nondefault oil `MODE` | Need explicit mip/filter, call-ABI, or preprocessor contracts. |

Task 37 adds one all-default typed factory while preserving the derivative
hold and every broader loop, numeric, global, boolean, matrix, aggregate,
stage, sampling, and macro boundary.
