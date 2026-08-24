# Post-struct-table frontier audit: Task 54 cosine palette record table

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-53.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 53 | 176 | 178 | 34 |

## Recommendation: `cosine-palette-const-vec4-record-table-v1`

The next smallest non-derivative slice is `filter/palette:palette`. It extends
Task 53 only for this distinct, hash-pinned immutable schema: one
four-`vec4` record, 55 ordered records, one guard-proved record read, and
named field/swizzle reads. Existing vector/vector `pow`, vector `step`,
ordinary `gl_FragCoord` sampling, and scalar/vector color math cover the rest.
It does not generalize records, global arrays, dynamic indexing, or aggregate
passing.

| Key | Exact defines | Source SHA-256 | Exact aggregate | Exact dynamic read |
| --- | --- | --- | --- | --- |
| `filter/palette:palette` | `{}` | `03ab3914862807288f7d5f6d2cbe8907cfa66fd1bb80b02df509880292967c09` | `PaletteEntry { vec4 amp, freq, offset, phase }`; `PALETTES[55]`; 220 ordered `vec4` / 880 scalar literals | `PALETTES[paletteIndex - 1]`, dominated by `1 <= paletteIndex <= 55` |

The table's comment-stripped constructor stream has SHA-256
`23c672b0332d2c13755c6f0459f3ec030e574ffc161bf5d78021497d587b8864`.
Every record has four ordered source-f32 `vec4` fields. The early passthrough
return proves that reaching the index requires `paletteIndex` in `1..55`, so
the exact index tree `paletteIndex - 1` is `0..54`. The indexed record is
copied once to local `entry`; only `entry.amp.w` and the four `entry.<field>.xyz`
reads are admitted. All table `amp.w` literals are exactly `0.0`, `1.0`, or
`2.0`, so the one `int(entry.amp.w)` conversion is range-proved to modes
RGB/HSV/OKLAB and cannot introduce a general float-to-int rule.

There is no loop, derivative, matrix, uniform block, varying, parameter
direction, sampler array, `textureLod`, mutable global, discard, output
feedback, or neighboring-pixel contract. `gl_FragCoord.xy` continues to map
to `context.frag_coord.xy`. The metadata pass binds inputTex and the authored
alpha/index/offset/repeat/rotation uniforms; its enum choices are exactly
passthrough `0` plus palette values `1..55`.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/palette:palette` with its metadata-verified empty define
   map and pinned source hash above. Reject another key, nonempty/absent/
   additional define, source rewrite, macro expansion, compatibility transform,
   or numeric-literal exception.
2. Admit exactly one typed record named `PaletteEntry` with the four ordered
   `vec4` fields `amp`, `freq`, `offset`, and `phase`, and exactly one
   `const PaletteEntry[55]` named `PALETTES`. Retain the 55x4x4 source-f32
   initializer tree, 880 scalar count, constructor-stream hash, mode-lane set,
   zero-write proof, and stable symbols in immutable IR. Reject another
   record/array/rank/extent/type/order/value, nested aggregate, global mutable
   state, or generic aggregate declaration.
3. Materialize only this table as one internal immutable static C++ data
   object with no dynamic initialization/allocation and one automatic by-value
   `entry` copy. No pointer/span/reference/address-taking/dynamic container or
   static data beyond this table is permitted. The C++ representation has 55
   records with four `Vec4` values each and no padding-dependent serialized
   ABI.
4. Permit exactly one table read with base `PALETTES` and index tree
   `paletteIndex - 1`; carry the return-dominance and `[0,54]` proof in IR.
   Permit only one scalar `entry.amp.w` read, the four named `.xyz` swizzles,
   and the one local `int` conversion with literal-derived `[0,2]` proof.
   Reject another index/base, computed/cast index, array/record/field write,
   record parameter/return, field alias, lvalue swizzle, or aggregate escape.
5. Reuse the established vector `pow`/`step`, named color helpers, ordinary
   scalar control flow, `gl_FragCoord`, texture sampling, and `PixelFn`
   `noexcept`/allocation-free ABI. Bind only the authored sampler/uniforms.
   Reject a new numeric overload, matrix, loop, derivative, uniform block,
   varying, `out`/`inout`, sampler array/LOD variation, persistent mutable
   state, resource feedback, or multi-pixel scheduling behavior.

Required positives are frozen oracles for passthrough index 0; every 1..55
table entry; invalid negative/56+ indices; RGB, HSV (index 12), and OKLAB
(indices 40, 43, 50) mode branches; alpha/offset/repeat/rotation extrema and
interior values; non-square and one-pixel inputs; and repeated/tiled output.
Direct tests must lock the 880 source-f32 literal bits and constructor-stream
hash, field order, sole index at 0/54, early-return dominance, one `.w` mode
read and four `.xyz` reads, `[0,2]` conversion proof, `context.frag_coord`
mapping, and byte-identical repeated output. Compile generated C++ with
warnings as errors and assert zero hot-path allocations and indirect calls.

Required negatives reject table/record/field/literal/hash/index/range/mode-
conversion/copy drift; a second aggregate/index/struct parameter/record
return; field write or alias; pointer/reference/span/dynamic storage; new
vector numeric overload; loop, derivative, matrix, uniform block, varying,
parameter direction, sampler array, nonzero/computed LOD, resource feedback,
or key/define/macro/numeric-contract drift.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 54 | **177** | **179** | **33** |

## Ranked residual map after Task 54

This one fixed cosine-palette schema does not establish general records,
arrays/indexing, float conversion, derivative semantics, or dynamic work.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Larger aggregate/index/bit forms | dither, median, test pattern, scanlineError | Require sorting, pack/unpack, uint-to-float paths, different aggregate lifetime, or broader indexing/word contracts. |
| 3 | Copy-out, matrix, and block interfaces | Julia/Mandelbrot/Newton, remap | Need `out` result semantics, matrices, or std140 binding contracts. |
| 4 | General work and resource policy | dynamic multi-pixel scans | Need distinct dimension provenance, output cardinality, and budget rules. |
| 5 | Broader profile families | texture MODE 0/1/2/4/5..14 | Need separately pinned preprocessing, reachable-stage, and work contracts. |

Task 54 adds one hash-pinned typed factory in this relative projection while
preserving the derivative hold and every broader aggregate, index, conversion,
ABI, work, resource, sampling, numeric, macro, and stage boundary.
