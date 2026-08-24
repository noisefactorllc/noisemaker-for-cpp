# Post-intrinsics frontier audit: Task 20 range-proved `vec3` indexing

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, assuming proposed Tasks 12–19.
Derivative semantics remain explicitly deferred: `PixelFn` receives one
`PixelContext`, not a quad or neighbor-access ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 19 | 131 | 133 | 79 |

## Recommendation: `local-vec3-index-v1`

The next coherent fail-closed slice is range-proved lvalue and rvalue indexing
of a `vec3`, attached only to the already-admitted counted-loop induction
symbol.  It is the highest-value frontier which does not add a new shader
interface, sampler policy, dynamic bound, or derivative model.

| Key | Exact default defines | Proven index form |
| --- | --- | --- |
| `filter/grade:creative` | `{}` | `i` in `for (int i = 0; i < 3; i++)` |
| `filter/grade:hslSecondary` | `{}` | `i` in `for (int i = 0; i < 3; i++)` |
| `filter/grade:lut` | `{}` | `i` in `for (int i = 0; i < 3; i++)` |
| `filter/grade:primary` | `{}` | `i` in `for (int i = 0; i < 3; i++)` |
| `filter/grade:vignette` | `{}` | `i` in `for (int i = 0; i < 3; i++)` |
| `filter/grade:wheels` | `{}` | `i` in `for (int i = 0; i < 3; i++)` |

All six sources use that exact lexical counted-loop shape.  They read input
parameters such as `srgb[i]` or `linear[i]`, and write locals such as
`linear[i]`, `srgb[i]`, `rgb[i]`, or `result[i]`.  `lut` is the largest member,
with four such loops; it still uses only the same `0..2` lane proof.  Task 14
source constants and Task 15 counted loops cover the remaining features in
this set.  This deliberately generalizes neither Task 17's matrix-specific
case nor any array indexing.

## Fail-closed IR, emitter, and runtime contract

1. Add a distinct typed expression, for example `vec3_index`, rather than
   accepting generic `index`.  Its base must be exactly `vec3`; its index must
   be either a literal integer in `[0, 2]` or the symbol of a lexically
   dominating Task-15 counted loop proven to have interval `[0, 2]` at the
   access point.  The symbol may not be reassigned, passed by reference, or
   used after the admitting loop's scope.
2. Admit both rvalues and assignment targets, including function `in vec3`
   parameters and local `vec3` values.  Do not admit `out`/`inout` parameters,
   arrays, matrices, `vec2`/`vec4`, swizzles with a dynamic selector, nested
   indexing, global mutable storage, or a computed/converted index.
3. Retain a per-function definite-lane-initialization proof for local vectors:
   all three lanes must be written along every path before the whole local
   vector is read, returned, or passed.  Parameters start initialized.  This
   makes the generated C++ independent of zero-initialization as an accidental
   substitute for GLSL's lane data flow.
4. Emit a direct automatic-storage lane reference/value, e.g.
   `value[static_cast<std::size_t>(i)]`, only after the IR proof establishes
   `0 <= i && i < 3`.  The existing `glsl::Vec<N,T>::operator[]` is `noexcept`;
   no bounds check, allocation, virtual call, function-pointer dispatch, or
   pixel-state allocation is introduced.  Preserve the existing typed f32
   conversion boundary on vector assignments and compound assignments.
5. Cap admission at 32 dynamic `vec3` index sites per program, eight per
   function, and one dynamic-index expression per access chain.  Reject any
   construct outside those exact proof and size limits before emission.
   Keep capability provenance explicit (`local-vec3-index-v1`) and bind every
   key to its sorted, metadata-verified empty define map.

Required positive oracles are the six frozen default-key renders plus
per-lane tests for reads and writes at indices 0, 1, and 2, branch coverage of
each grade conversion, and a `lut` rendering comparison.  Required negatives
must reject `i < 4`, `i += 2`, a reassigned or shadowed induction variable,
`v[j + 1]`, `vec4[i]`, `mat3[i]`, `array[i]`, `v[i][j]`, a dynamic swizzle,
an `out`/`inout` indexed parameter, an uninitialized local vector read, and
metadata/default-define drift.  Compile the generated slice with warnings as
errors and assert that its hot `PixelFn` allocation counter and dispatch count
remain zero.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 20 | **137** | **139** | **73** |

## Ranked residual map after Task 20

These remain separate frontiers; their presence is not authorization to merge
them into the index slice.

| Rank | Frontier | Visible examples | Why it stays separate |
| ---: | --- | --- | --- |
| 1 | Dynamic-loop contracts | blur H/V, `normalize:statsFinal`, `tetraColorArray`, `nmReindexReduce`, `zoomBlur`, `oilFlatten` | Bounds depend on render scale, texture dimensions, a float/`ceil` result, or a larger work charge. |
| 2 | Derivative ABI | halftone, octave warp, stamp threshold, stipple | Correct `dFdx`/`dFdy` needs neighboring-pixel or quad semantics, still excluded. |
| 3 | Vector-math completion | `synth/curl:curl` | Needs `tanh(vec3)` plus deliberately excluded `mod(vec3,float)` and `mod(vec4,float)`. |
| 4 | Signed scalar bitwise | `classicNoisedeck/bitEffects:bitEffects` | `int` `&`, `|`, `^`, and `<<` require a pinned two's-complement and shift policy. |
| 5 | Other intrinsic/sampling signatures | nonzero or computed `textureLod`, other sampler kinds, `reflect` | Requires a separately specified mip-chain/filter policy or numeric overload contract. |
| 6 | Arrays and general indexing | `cellRefract`, kaleido, test-pattern-style arrays | Array storage, initialization, lifetime, and arbitrary subscript proofs are not vector-lane semantics. |
| 7 | Matrix completion | `classicNoisedeck/effects:effects` (`mat4`) and remaining mat3 programs | Needs matrix constructors/algebra and often overlapping builtin or loop work. |
| 8 | Function/interface ABI | `synth/julia`, `synth/mandelbrot`, `synth/newton` `out` helpers; `watercolor` `inout` | Needs C++ reference/result lowering and alias/evaluation-order rules, not a local expression feature. |
| 9 | Data/stage ABI | `synth/remap:remap` UBO; `filter/grime:grime` and `filter/texture:texture` varyings | Needs std140 layout or pinned stage-input ownership in `PixelContext`. |

The Task 20 boundary therefore consumes the six all-default grade passes while
preserving the derivative hold and leaving each ABI, dynamic-loop, array, and
matrix decision independently reviewable.
