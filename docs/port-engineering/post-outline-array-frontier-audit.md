# Post-outline-array frontier audit: Task 59 Refract direct fixed-array parameter

This is a read-only long-range projection relative to prepared Tasks 12–58.  The active Task-15 correction is deliberately not merged into these counts, contracts, or completion claims.  The fragment-derivative ABI hold remains intact: source helpers named `derivX` and `derivY` perform ordinary sampled convolutions and are not `dFdx`, `dFdy`, or `fwidth`.

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| after Task 58 | 181 | 183 | 29 |

## Recommendation: `refract-direct-nine-array-in-parameter-v1`

Admit exactly one factory, `classicNoisedeck/refract:refract`, under a source-specific fixed-array parameter contract.  Do not admit general array parameters, references, aliasing, or helper-array escape.

| field | exact value |
| --- | --- |
| key | `classicNoisedeck/refract:refract` |
| source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/refract/refract.glsl` |
| source SHA-256 | `d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2` |
| source-bound metadata defaults | `{ "amount": 50, "blendMode": 10, "direction": 0, "mix": 50, "mode": 0, "wrap": 0 }` |
| define map | `{}` |

The only array-parameter shape is `convolve(vec2 uv, float kernel[9], bool divide)`.  `derivX` creates `float deriv_x[9]`; `derivY` creates `float deriv_y[9]`; each writes literal indices `0..8`, then passes that exact local identifier directly to `convolve`.  In the callee, only `vec2 offset[9]` is local; it too receives literal writes `0..8`.  The sole dynamic reads are `offset[i]` and `kernel[i]` in `for (int i = 0; i < 9; i++)`.

At any direct call, the live caller kernel and callee offsets occupy 27 scalar-float lanes (108 bytes); lowering the parameter as a const reference does not copy the kernel.  This is a deliberately closed source graph, not a capability for arbitrary `T[N]` parameters or C++ references.

## Exact admission contract

1. Accept only the pinned key, digest, empty define map, and source-bound metadata defaults above.  Reject any identity/profile mismatch before translation.
2. Permit exactly the direct helper signature `convolve(Vec2, in float[9], bool) -> Vec3`, lowered to `convolve(Vec2, const std::array<float, 9>&, bool)`.  The reference is const, non-null, non-storable, non-returnable, and may only bind to the exact local `deriv_x` or `deriv_y` caller array.  Reject every other array parameter, direction, type, extent, overload, indirect call, array return, array assignment, alias, or escape.
3. Permit only the three automatic arrays named by this source: `std::array<float, 9> deriv_x`, `std::array<float, 9> deriv_y`, and callee-local `std::array<Vec2, 9> offset`.  Require one literal-index assignment at each index `0..8` before any read.  Reject globals/statics, heap allocation, constructors, copies, extra arrays, nonliteral writes, and changed initializer order or values.
4. Prove `convolve`'s only indexed loop starts `i=0`, guards `i < 9`, increments by one, and makes exactly nine trips in interval `0..8`.  Permit exactly one `offset[i]` and two `kernel[i]` reads per trip (the convolution weight and weight total), with no dynamic index or indexed mutation elsewhere.
5. Preserve existing source-constant (`PI`/`TAU`), ordinary texture, `textureSize`, `floor`, `map`, `mod`, vector comparison, and blend lowering.  Retain direct call ownership: `derivX` and `derivY` each call `convolve` once, only within the existing `mode == 1` path.  Do not introduce sampler arrays, LOD/gradient/image operations, fragment derivatives, mutable shared state, a new resource ABI, or a general helper-reference feature.

## Required tests and oracles

- Acceptance tests lock the source/key/defaults/empty defines and reject drift at the factory boundary.
- Structural tests prove the one helper signature, two allowed direct caller arrays, one callee offset array, all 27 literal table writes, direct-only binding, non-escape/non-copy behavior, and the exact nine-trip loop with only the permitted reads.
- Runtime tests compare an independent reference on non-square and one-pixel inputs; contrast-rich and flat inputs; `mode` 0 and 1; all three `wrap` modes; multiple `amount`, `direction`, and `mix` values; and representative blend-mode branches, including the default.  Verify both `derivX` and `derivY` calls, tile-offset/full-resolution mapping, alpha, and repeated-render determinism.
- Negative tests reject an array argument from a parameter/global/conditional expression, a second `convolve` caller, a changed parameter direction/extent, array capture or return, partial/duplicate table writes, an altered loop bound/step, a dynamic write index, sampler arrays, LOD/gradient syntax, fragment derivative syntax, and every other source key.

## Residual frontier after this slice

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| relative after Task 59 | 182 | 184 | 28 |

The residual remains partitioned by independent proof burden: fragment-derivative programs stay held; then different local arrays (notably affine/larger-table shapes); then sorting, packed-word, matrix/copy-out, and resource/stage ABI cases.  This direct fixed-array parameter exception establishes none of those broader capabilities.

## Boundary statement

This is planning evidence only.  It makes no repository change, does not modify or count the active Task-15 correction, and does not claim an implementation is merged.  The derivative ABI hold is preserved.
