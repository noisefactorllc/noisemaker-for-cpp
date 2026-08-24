# Post-texture-profile frontier audit: Task 53 historic palette record table

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-52.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 52 | 175 | 177 | 35 |

## Recommendation: `historic-palette-const-record-table-v1`

The next smallest non-derivative slice is `filter/historicPalette:historicPalette`.
It reuses existing `gl_FragCoord`, ordinary sampling, source scalar constants,
and `context` bindings. Its one new boundary is a single immutable global
record table: one five-field `HistoricPalette`, exactly 21 ordered records,
and one range-proved record read. It does not establish general structs,
arrays, dynamic indexing, record mutation, or aggregate ABI passing.

| Key | Exact defines | Source SHA-256 | Exact aggregate | Exact dynamic read |
| --- | --- | --- | --- | --- |
| `filter/historicPalette:historicPalette` | `{}` | `cc0feb09e2f90505766a0b8b0d61ca0cf83a1121ec7b104eea5ff806c9ce0c33` | `HistoricPalette { vec3 color1..color5 }`; `PALETTES[21]`; 105 ordered `vec3` / 315 scalar literals | `PALETTES[idx]`, where `idx=clamp(paletteIndex,0,20)` |

The table's comment-stripped constructor stream has SHA-256
`b80e0c46b3be9ff8e48dc6f4c6af95b60f1bb157b55e0f155f3e90084ca4f871`.
Every record has exactly five ordered three-lane source-f32 colors. The only
index is the local `idx`; the exact scalar clamp proves `[0,20]` even if the
caller supplies an arbitrary signed `paletteIndex`. The indexed record is
copied once to local `pal`, passed by value only to `sampleHistoricPalette`,
then read through its five named fields. There is no field/record/array write,
address/reference escape, nested aggregate, array parameter/return, loop,
matrix, derivative, uniform block, varying, sampler array, `textureLod`, or
neighbor-pixel policy.

`gl_FragCoord.xy` retains the existing bottom-left pixel-center mapping to
`context.frag_coord.xy`; it is used to form the current input UV and an unused
global-coordinate local. The metadata pass binds `inputTex` and maps alpha,
index, offset, repeat, rotation, and smoothness to their authored uniforms;
the index default is `4` and the authoritative choice set is exactly `0..20`.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/historicPalette:historicPalette` with the metadata-
   verified empty define map and pinned source hash above. Reject another key,
   nonempty/absent/additional define, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Admit exactly one typed record declaration named `HistoricPalette` with
   five read-only ordered `vec3` fields `color1` through `color5`, and exactly
   one `const HistoricPalette[21]` declaration named `PALETTES`. Retain the
   ordered 21x5x3 source-f32 initializer tree, scalar count, constructor-stream
   hash, zero-write proof, and stable field/symbol identities in immutable IR.
   Reject another struct/array/rank/extent/type/order/value, a nested record,
   global mutable state, aggregate copy other than the named local, or a
   generic record/array facility.
3. Materialize only this table as one internal immutable static C++ data
   object with no dynamic initialization or allocation; materialize `pal` as
   one automatic by-value record. Do not expose a pointer/span/reference,
   permit table address-taking, use a dynamic container, or create a general
   persistent source-global pathway. The object has exactly 21 records, five
   `Vec3` fields each, and no padding-dependent serialized contract.
4. Permit exactly one record index with base `PALETTES` and direct index symbol
   `idx`; carry the `clamp(paletteIndex,0,PALETTE_COUNT-1)` provenance and
   `[0,20]` interval proof in IR. Permit only the subsequent five named
   read-only `pal.colorN` field reads in `sampleHistoricPalette`. Reject another
   base/index expression, unproved/cast arithmetic index, member lvalue,
   array/record write, field alias, swizzle base, or aggregate escape.
5. Permit exactly the named by-value helper parameter
   `sampleHistoricPalette(HistoricPalette pal, float lum, float smoothAmount)`
   and direct call from `main`; lower it as one automatic value copy with no
   pointer/reference ABI. Reuse existing `gl_FragCoord`, texture, `mix`,
   `smoothstep`, and scalar control flow. Bind only the authored uniforms and
   sampler; retain a direct `noexcept`, allocation-free `PixelFn`.

Required positives are frozen oracles for all 21 palette choices; index inputs
below/above range; all rotation modes; offset/repeat/smoothness/alpha extrema
and interior values; every five-color transition and wrap seam; non-square and
one-pixel inputs; and repeated/tiled output. Direct tests must lock the record
layout/order, 315 source-f32 literal bits and constructor-stream hash, the sole
index at 0 and 20, five field reads, by-value copy route, `context.frag_coord`
mapping, and byte-identical repeated output. Compile generated C++ with
warnings as errors and assert zero hot-path allocations and indirect calls.

Required negatives reject table/record/field/literal/hash/index/range/copy
drift; a second aggregate, index, struct parameter, field write, pointer/
reference/span, mutable global or static data beyond this one table, generic
aggregate lifetime,
loop, derivative, matrix, uniform block, varying, parameter direction,
sampler array, nonzero/computed LOD, resource feedback, or key/define/macro/
numeric-contract drift.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 53 | **176** | **178** | **34** |

## Ranked residual map after Task 53

This one immutable five-color record table does not establish general
aggregates, arrays/indexing, copying, derivative semantics, or dynamic work.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Larger aggregate/index/bit forms | palette, dither, median, test pattern, scanlineError | Require larger/different record schemas, sorting, pack/unpack, uint-to-float paths, or broader indexing/word contracts. |
| 3 | Copy-out, matrix, and block interfaces | Julia/Mandelbrot/Newton, remap | Need `out` result semantics, matrices, or std140 binding contracts. |
| 4 | General work and resource policy | dynamic multi-pixel scans | Need distinct dimension provenance, output cardinality, and budget rules. |
| 5 | Broader profile families | texture MODE 0/1/2/4/5..14 | Need separately pinned preprocessing, reachable-stage, and work contracts. |

Task 53 adds one hash-pinned typed factory in this relative projection while
preserving the derivative hold and every broader aggregate, index, copy, ABI,
work, resource, sampling, numeric, macro, and stage boundary.
