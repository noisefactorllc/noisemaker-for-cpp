# Post-`equal(bvec2)` frontier audit: Task 39 current-vocabulary CRT/degauss pair

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-38.
The derivative ABI remains held: the per-pixel execution model has no
fragment-neighbor, border, or scheduling semantics.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 38 | 159 | 161 | 51 |

## Recommendation: `crt-degauss-current-vocabulary-v1`

The smallest exact next slice is a two-key, empty-define allowlist extension.
It introduces no type, operator, builtin, storage, loop, sampler, or execution
capability.  Both sources already pass the frozen capability vocabulary and
the current typed C++ emitter in a read-only replay; their only omitted state
is allowlist/catalog coverage.

| Key | Exact defines | Source SHA-256 | Source constants |
| --- | --- | --- | --- |
| `filter/crt:crt` | `{}` | `62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c` | `PI`, `TAU`, `INV_THREE` (`const float`, literal initializers) |
| `filter/degauss:degauss` | `{}` | `915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c` | `TAU` (`const float`, literal initializer) |

The existing source-const lowering emits each dependency closure as an
automatic immutable local in every reader; it must not add C++ namespace,
function-static, or mutable shared storage. Both programs use only `in`
scalar/vector/sampler helper parameters and the already-admitted level-zero
`texelFetch(sampler2D, ivec2, 0) -> vec4` form. Neither source has an array,
matrix, struct, uniform block, varying, `out`/`inout` helper parameter,
`textureLod`, `dFdx`, `dFdy`, `fwidth`, `for`, or `while` node.

For CRT, the resolved builtin set is restricted to prior forms: scalar/vector
`abs`, `clamp`, `cos`, `dot`, `floor`, `fract`, `length`, `max`, `min`, `mix`,
`pow`, `sin`, `sqrt`, `step`, and four level-zero texel fetches. Degauss uses
the same existing families except `fract`, with five level-zero fetches. The
read-only validator replay passes both sources with the current frozen
capability vocabulary; the typed emitter also renders both without a new
emission rule.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/crt:crt` and `filter/degauss:degauss`, in sorted order,
   with their metadata-verified empty define maps. Reject a nonempty, absent,
   reordered, substituted, or additional define; another key; source-hash
   drift; a compatibility transform; and a numeric-literal exception.
2. Reuse source-const lowering only for the exact literal `const float`
   declarations listed above. Keep stable declaration identities, literal
   Float32 materialization, reader/dependency proof, and whole-program
   zero-write audit. Reject an initializer dependency not already proved by
   the existing contract, a non-float global, a vector/matrix/array global,
   nonliteral initializer, write, alias, static materialization, or expanded
   global vocabulary.
3. Reuse only the current resolved builtin signatures and level-zero
   `texelFetch` contract. Every fetch must retain its `sampler2D`, `ivec2`,
   literal integer-zero overload identity. Reject new builtins, overloads,
   nonzero/computed levels, other sampler classes, relational/bvec expansion,
   vector indexing, arrays, matrices, aggregates, loop nodes, derivatives,
   UBOs, varyings, and parameter-direction expansion.
4. Bind exactly the authored interfaces. CRT requires `inputTex`,
   `resolution`, `tileOffset`, `fullResolution`, `time`, `speed`, `seed`,
   `alpha`, and `renderScale`; degauss requires `inputTex`, `resolution`,
   `tileOffset`, `fullResolution`, `time`, `displacement`, `speed`, `seed`,
   and `direction`. Missing or wrong-typed bindings fail before invocation.
5. Emit only automatic locals and existing value types/helpers. Preserve the
   typed Float32 boundaries and bottom-left integer-fetch behavior. Do not
   introduce allocation, mutable process state, pointer/reference escape,
   virtual dispatch, callback, map, variant, indirect call, or a render-graph
   adapter; `PixelFn` remains `noexcept` and allocation-free.

Required positives are frozen CRT and degauss default-profile oracles on
non-square inputs, edge and interior integer fetch coordinates, alpha zero and
one, zero/nonzero time and speed, negative/positive direction, and low/high
displacement. Direct tests must prove the exact four-versus-five fetch-node
counts, exact constant reader closures, source-order literals, full binding
matrices, and byte-identical repeat rendering.

Required negatives reject define or source-hash drift, a third key, any added
capability/type/operator/transform/exception, altered global declaration or
initializer, a write to a source constant, nonzero/computed LOD, sampler/type
drift, every derivative builtin, a loop, array, matrix, struct, UBO, varying,
or non-`in` helper parameter. Compile generated C++ with warnings as errors
and assert zero hot-path allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 39 | **161** | **163** | **49** |

## Ranked residual map after Task 39

This pair consumes only already-proved local semantics. It does not relax the
derivative hold or establish a general source-global admission.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` need explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource and dynamic-work contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Render-scale, texture-dimension, or charged-work bounds need independently enforced runtime proofs. |
| 3 | Global arrays and word/index forms | normalMap, OSD, dither, glyph map, test pattern | Require aggregate lifetime, initialization, range, and signed-word contracts beyond immutable scalar constants. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, derivative effects, remaining scalar bitwise paths | Need independent mip/filter, fragment-neighbor, or two's-complement policy. |

Task 39 is therefore a two-factory catalog increment using existing typed
semantics, while retaining every broader derivative, resource, global-array,
matrix, aggregate, stage, indexing, numeric, sampling, loop, and macro
boundary.
