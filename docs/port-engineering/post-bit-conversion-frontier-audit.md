# Post-bit-conversion frontier audit: Task 51 grime float-bit ingress

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-50.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 50 | 173 | 175 | 37 |

## Recommendation: `grime-float-bits-to-uint-pcg-v1`

The next smallest exact slice is `filter/grime:grime`. It reuses the sole
Task-49 `v_texCoord -> PixelContext::uv` input, established `uvec3` PCG,
Task-15 fixed integer loop form, ordinary sampling, and existing scalar/vector
numeric operations. Its only new semantic boundary is the five exact scalar
`floatBitsToUint` calls that feed the noise PRNG. This is a bit-pattern
conversion contract, not general numeric casting or bit reinterpretation.

| Key | Exact defines | Source SHA-256 | Exact new builtin sites | Fixed work |
| --- | --- | --- | --- | --- |
| `filter/grime:grime` | `{}` | `15a88fff0e951bf7fa01f4c982532cf79d835663cb2a81c2076c5fecbd9c351f` | `hash21(p.x)`, `hash21(p.y)`, `hash31(p.x)`, `hash31(p.y)`, `hash31(p.z)` | one `i=0; i<8; i++` loop, 120 reachable visits per pixel |

Each admitted builtin first rounds its scalar operand through the established
GLSL binary32 boundary, then returns exactly that IEEE-754 binary32 storage
word as `uint`; it performs no numeric conversion, sign extension, NaN
canonicalization, zero normalization, or host-double bit inspection. The
result has one route: a lane of the immediate `uvec3(...)` argument to `pcg`.
`hash21` fixes its third lane to `0u`; `hash31` applies the three named calls.
No converted word is stored persistently, returned, masked, shifted directly,
indexed, used as a loop/resource/allocation control value, or converted back
to float.

`simple_multires` contains the only loop, with fresh `int i`, literal start
`0`, literal limit `8`, unit increment, no loop control, no index, and no
write to the induction variable. Its direct call graph is fixed: main reaches
`refracted_field` three times and `chebyshev_gradient` once; the latter reaches
`refracted_field` four times. Every `refracted_field` reaches
`simple_multires` three times, for 15 calls and 120 total loop visits. This
stays below the prepared loop charge and introduces neither a dynamic bound
nor neighbor-pixel evaluation: the shader samples only `inputTex` at its
current `v_texCoord`.

The source has no derivative despite its visual gradient name; it has no
array/index, matrix, struct, uniform block, parameter direction, sampler
array, `textureLod`, mutable global, discard, output feedback, or secondary
stage input. Its declared uniforms are `inputTex`, `resolution`,
`fullResolution`, `tileOffset`, `strength`, and `seed`; metadata binds the
input sampler, full-resolution/tile fields, strength (default `0.5`), and
seed (default `1`).

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/grime:grime` with the metadata-verified empty define
   map and pinned source hash above. Reject another key, a nonempty/absent/
   additional define, source rewrite, macro expansion, compatibility transform,
   or numeric-literal exception.
2. Add exactly `floatBitsToUint(float) -> uint` at the five pinned source
   spans and only with direct scalar swizzle operands `p.x`, `p.y`, or `p.z`
   in the two named helpers. Typed IR records builtin spelling, argument/result
   types, lane name, helper identity, and the immediate `uvec3` consumer.
   Reject `uintBitsToFloat`, vectors, arrays, another callee/call site,
   arithmetic/cast/wrapper argument, result copy/return, or any use outside
   that PCG-constructor route.
3. Lower the five calls through one `noexcept` binary32-bit helper equivalent
   to `std::bit_cast<std::uint32_t>(f32(argument))`. The f32 boundary precedes
   the bit cast and no host FP operation follows it before `pcg`; preserve
   `+0`, `-0`, infinities, all NaN payload bits supported by the source
   representation, and every finite bit pattern. Reject `static_cast`, text
   formatting/parsing, union aliasing, double-bit casts, host-endian byte
   assembly, value comparisons, or payload-changing normalization.
4. Reuse exactly the prepared Task-15 literal eight-trip loop and immutable
   120-visit interprocedural charge proof described above. Preserve all helper
   identities/call edges and reject a changed loop header, a second/nested/
   dynamic loop, induction use as index/LOD/resource control, changed helper
   multiplicity, or an effective charge above 120.
5. Reuse Task 49's exact `v_texCoord` lowering, existing `uvec3` PCG
   arithmetic and shifts, and ordinary level-zero texture sampling. Bind only
   the authored uniforms/sampler and retain `PixelFn` as `noexcept` and
   allocation-free. Reject another interface symbol, caller-provided stage
   data, sampler/LOD variation, derivative, matrix, struct, uniform block,
   `out`/`inout`, array/index, mutable/static state, feedback, or multi-pixel
   scheduling behavior.

Required positives are frozen grime oracles across strength/seed extrema and
interior values, full-resolution aspect ratios, tile offsets, one-pixel and
non-square inputs, alpha preservation, and repeated/tiled output. Direct
tests must lock all five typed builtin spans and routes; `+0`, `-0`, finite
sentinels, infinities, representative NaN payloads, and the exact resulting
`uint` words; the exact eight induction values; all 15 helper entries/120
visits; the sole `context.uv` binding; and byte-identical repeated output.
Compile generated C++ with warnings as errors and assert zero hot-path
allocations and indirect calls.

Required negatives reject builtin/argument/lane/f32-boundary/bit-pattern drift;
numeric conversion or uint-to-float reinterpretation; a sixth bit call;
conversion-result escape; loop/call-graph/charge drift; a second varying;
array/index, derivative, matrix, struct, uniform block, parameter direction,
sampler array, nonzero/computed LOD, resource feedback, or key/define/hash/
macro/numeric-contract drift.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 51 | **174** | **176** | **36** |

## Ranked residual map after Task 51

This five-site bit ingress does not establish general bit reinterpretation,
arrays/indexing, broader stage inputs, derivative semantics, or dynamic work.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Larger aggregate/index/bit forms | dither, median, test pattern, scanlineError | Require arrays/indexing/lifetime, sorting, pack/unpack, uint-to-float paths, or wider word contracts. |
| 3 | Matrix, struct, copy-out, and block interfaces | historicPalette/palette, Julia/Mandelbrot/Newton, remap | Need aggregate layout, parameter direction, copy-out, or std140 binding contracts. |
| 4 | Broader stage and texture pathways | texture | Needs its own multi-mode loop/work and resource contract. `wormhole:deposit` remains a canonical point-draw coverage source with no runtime kernel key. |
| 5 | General work and resource policy | dynamic multi-pixel scans | Need distinct dimension provenance, output cardinality, and budget rules. |

Task 51 adds one hash-pinned typed factory in this relative projection while
preserving the derivative hold and every broader interface, bit, aggregate,
index, work, resource, sampling, numeric, and macro boundary.
