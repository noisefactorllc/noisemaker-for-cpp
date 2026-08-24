# Post-float-bits frontier audit: Task 52 texture default-mode word closure

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-51.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 51 | 174 | 176 | 36 |

## Recommendation: `texture-mode3-word-closure-v1`

The next smallest coherent slice is the metadata-pinned paper profile of
`filter/texture:texture`. It reuses Task 49's only stage input,
Task 50's scalar unsigned mask/conversion representation, Task 51's f32/word
boundary, ordinary sampling, and the prepared fixed-loop form. The profile's
new forms are tightly finite: eight scalar `uint ^= uint` assignments, nine
named `int -> uint` conversions, and one scalar `inversesqrt(float)` helper
call. It does not establish a general preprocessor, word, conversion, or
inverse-root facility.

| Key | Exact defines | Source SHA-256 | New forms | Reachable default work |
| --- | --- | --- | --- | --- |
| `filter/texture:texture` | `{ "MODE": 3 }` | `8e95251ef9a7789b1de4e51718ab3bebd9fc6d20db8acd0969191e288ec7454c` | 8 `^=`, 9 `int -> uint`, 1 `inversesqrt` | five `height_paper` calls, three trips each = 15 visits |

`MODE=3` is authoritative metadata, not a fallback choice. The pinned
preprocess result selects `height_paper` in `height_field`, removes the
`MODE>=5` main path that reads `gl_FragCoord`, and fixes every conditional
branch in `material_value`. All helper definitions still compile, so their
exact source forms remain validated even when unreachable from the selected
pixel path.

The eight compound-XOR sites are the three `hash_uint` updates, three
`fast_hash` updates, and two `material_hash` updates. Each has scalar `uint`
target and scalar `uint` RHS, with the authored RHS shape `value >> literal`
or `uint(ivec lane) * literal`; no scalar word result escapes its local hash
chain. The nine explicit `uint` conversions are the three `fast_hash` ivec3
lanes, two literal loop-salt expressions, two `material_hash` ivec2 lanes,
and `z0`/`z1` in `material_noise`. They reuse the exact modulo-`2^32`
signed-to-unsigned conversion established by Task 50, with their source-span,
operand, and immediate hash/salt consumer identity retained in IR.

`inversesqrt` occurs once, as `inversesqrt(max(dot(gradient, gradient),
0.000001))` in `material_gradient`; both arguments are finite/nonnegative on
that route and the max lower bound is exact. It returns a scalar float only to
multiply the two-lane gradient. It never selects work, resources, an index, or
control flow. The source's loops are immutable literal forms: `0..<3`,
`0..<2`, and the nested `-1..1` pair in the dead `material_sprinkles` helper.
The only default-reachable loop is paper's three-trip loop entered five times.
There is no derivative, array/index, matrix, struct, uniform block, parameter
direction, sampler array, `textureLod`, mutable global, discard, or output
feedback.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/texture:texture` with the complete sorted define map
   `{ "MODE": 3 }`, the pinned source hash above, and exact normalized
   preprocessed profile. Reject a missing/empty/additional/value-changed map,
   source `#ifndef` fallback, other MODE, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Permit exactly the eight named scalar `uint ^= uint` assignments and nine
   named `int -> uint` constructions described above. Carry target/operand
   symbols, operator, source span, literal/cast tree, and local hash-chain
   consumer in typed IR. Lower compound XOR as a defined 32-bit unsigned
   operation, and signed-to-unsigned as modulo `2^32`; reject `&=`, `|=`,
   shifts/compound shifts, another conversion direction, implicit C++
   narrowing, a different expression shape, or any result escape.
3. Permit exactly one `inversesqrt(float) -> float` node with the pinned
   `max(dot(gradient,gradient),0.000001)` argument tree and direct vector
   multiplication parent. Lower through a deterministic `noexcept` scalar
   helper with the established f32 input/output boundaries. Reject another
   overload, vector/matrix argument, a raw host reciprocal-sqrt, zero/negative
   lower bound, control/index/resource use, or a second inverse-root site.
4. Reuse the Task-49 `v_texCoord -> context.uv` binding, Task-50 exact
   `h & 0xffffu` word-mask convention, and Task-51 f32-to-word ingress
   unchanged. Preserve the three fixed loop proofs, with the selected main
   call graph charged at 15 visits and dead helpers compiled but not charged.
   Reject a changed loop header/call edge, a dynamic/nested reachable charge,
   general stage interface, `gl_FragCoord` in the MODE3 preprocessed main,
   or any new array/index capability.
5. Bind only `inputTex`, time, alpha, scale, intensity, contrast, mono,
   tileOffset, and fullResolution; preserve ordinary input sampling and the
   existing `PixelFn` `noexcept`/allocation-free ABI. Reject new samplers,
   LOD/filter changes, derivative, matrix, struct, uniform block, `out`/
   `inout`, persistent state, resource feedback, or multi-pixel scheduling.

Required positives are frozen MODE3 paper oracles over alpha/scale/intensity/
contrast/mono/time extremes and interior values, non-square and one-pixel
axes, tile/full-resolution changes, all five height samples, and repeated/
tiled output. Direct tests must lock preprocessing to MODE3; the eight
compound-XOR and nine conversion spans/routes; `int` values `0`, `-1`,
`INT32_MIN`, and `INT32_MAX`; the single inverse-root input/output around its
lower bound; all fixed loop induction sequences; dead-helper compilation; and
byte-identical repeated output. Compile generated C++ with warnings as errors
and assert zero hot-path allocations and indirect calls.

Required negatives reject any other MODE, fallback define, word assignment or
conversion site, inverse-root overload/argument/use, added stage data,
`gl_FragCoord` MODE3 path, loop/call-graph charge drift, array/index,
derivative, matrix, struct, uniform block, parameter direction, sampler
array, nonzero/computed LOD, resource feedback, or key/hash/macro/numeric-
contract drift.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 52 | **175** | **177** | **35** |

## Ranked residual map after Task 52

This one compile-time paper profile does not establish general macros, scalar
word/conversion facilities, arrays/indexing, derivative semantics, or dynamic
resource work.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Larger aggregate/index/bit forms | dither, median, test pattern, scanlineError | Require arrays/indexing/lifetime, sorting, pack/unpack, uint-to-float paths, or wider word contracts. |
| 3 | Matrix, struct, copy-out, and block interfaces | historicPalette/palette, Julia/Mandelbrot/Newton, remap | Need aggregate layout, parameter direction, copy-out, or std140 binding contracts. |
| 4 | General work and resource policy | dynamic multi-pixel scans | Need distinct dimension provenance, output cardinality, and budget rules. |
| 5 | Broader profile families | texture MODE 0/1/2/4/5..14 | Need separately pinned preprocessing, reachable-stage, and work contracts. |

Task 52 adds one hash-pinned typed factory in this relative projection while
preserving the derivative hold and every broader macro, interface, word,
conversion, aggregate, index, work, resource, sampling, numeric, and stage
boundary.
