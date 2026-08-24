# Post-large-reduction frontier audit: Task 48 OSD glyph table index

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-47.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 47 | 170 | 172 | 40 |

## Recommendation: `osd-fixed-glyph-array-index-v1`

The next smallest exact slice is OSD's one immutable glyph table and its sole
range-proved dynamic lookup. It reuses scalar integer masks/shifts and does
not establish general array, indexing, or signed-word support.

| Key | Exact defines | Source SHA-256 | Exact aggregate/index form |
| --- | --- | --- | --- |
| `filter/osd:osd` | `{}` | `c45adaf30ecef6fb7f83a4f3995e671df0caaa47bfeceba8bb9bfe2c07427443` | literal `const int GLYPHS[80]`, read only as `GLYPHS[digit * 8 + gy]` |

`GLYPHS` is one direct 80-child literal `int` constructor, with values in
`0..126`. It has one read in `sample_glyph`. At the sole call site,
`digit = int(digit_hash % 10u)` gives `0..9`; source guards prove `gy=0..7`
before the read. The exact index `digit*8 + gy` is therefore `0..79`. The
loaded row is nonnegative and the immediate existing extraction
`(row >> (6 - gx)) & 1` is safe: `gx=0..6` after the paired guard, so its
right shift count is `0..6`. The shifted value is not stored, returned as an
integer, indexed, or used for loop/allocation/resource control.

The remaining source constants are exact literals `GLYPH_W=7`, `GLYPH_H=8`,
`BASE_SCALE=3`, and `BASE_PADDING=25`. They reuse automatic source-constant
lowering in their reader functions. All remaining operations reuse existing
PRNG word forms, scalar `&`, nonnegative signed right-shift behavior,
constructors, `textureSize`, level-zero `texelFetch`, and ordinary local
arithmetic/control flow. The source has no loop, derivative, matrix, struct,
uniform block, varying, parameter direction, sampler array, `textureLod`, or
mutable global state.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/osd:osd` with its metadata-verified empty define map and
   pinned source hash above. Reject another key, a nonempty/absent/additional
   define, source rewrite, macro expansion, compatibility transform, or
   numeric-literal exception.
2. Permit only the exact five source constants named above. Retain stable
   declaration/symbol identities, literal initializer values, ordered 80-row
   constructor, scalar lane count (80 / 320 bytes), reader functions, and
   zero-write proof in immutable typed IR. Reject a second array, a changed
   extent/rank/element type/initializer, global array write/copy/parameter/
   return, mutable/static state, or a general source-aggregate facility.
3. Materialize `GLYPHS` only as one automatic immutable
   `std::array<std::int32_t,80>` in `sample_glyph`; materialize scalar
   dependencies only in their readers. Do not emit namespace/function-static
   storage, heap allocation, pointer/reference escape, bounds-check slow path,
   or dynamic container.
4. Permit exactly one array read with base `GLYPHS` and index tree
   `digit*8 + gy`. Carry the call-site, guard-dominance, modulus, conversion,
   and resulting `[0,79]` range proof in typed IR. Reject another index/base,
   a literal/dynamic arithmetic variation, an unproved caller, index write,
   swizzle/member base, or any array value escape.
5. Reuse scalar `int >> int` and `int & int` only for the immediate
   nonnegative glyph-row extraction `(row >> (6-gx)) & 1`, with row `[0,126]`
   and shift count `[0,6]`. Reject a negative/unknown operand, count outside
   `0..30`, left shift, another signed shift/mask, compound bitwise write, or
   use outside the direct float result of `sample_glyph`. Bind only the
   authored OSD interface and preserve `PixelFn` as `noexcept` and
   allocation-free.

Required positives are frozen OSD oracles for all ten digits, all eight rows
and seven columns, every corner, alpha extremes, time/speed/seed variations,
all glyph counts, non-square dimensions, and tiled output. Direct tests must
lock all 80 ordered literal entries, one and only one array index, index ranges
at 0 and 79, the `gx=0..6` shift truth table, scalar-constant injection,
declared binding behavior, and byte-identical repeated output.

Required negatives reject array/constant/index/guard/range drift, another
global aggregate or array read/write/escape, unknown/negative signed shifts,
extra word operation, loop, derivative, matrix, struct, uniform block,
varying, parameter direction, sampler array, nonzero/computed LOD, or
key/define/hash/macro drift. Compile generated C++ with warnings as errors
and assert zero hot-path allocations and indirect calls.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 48 | **171** | **173** | **39** |

## Ranked residual map after Task 48

This one read-only glyph table does not establish general source aggregates,
arbitrary dynamic indexing, signed-word semantics, large work, or
neighboring-pixel evaluation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Larger aggregate/index/word forms | dither, median, test pattern | Require more arrays, indexing/lifetime, sorting, or broader signed-word contracts. |
| 3 | General work and resource policy | dynamic multi-pixel scans | Need different dimension provenance, output cardinality, or budget rules. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, remaining scalar bitwise paths | Need independent mip/filter or two's-complement rules. |

Task 48 adds one hash-pinned typed factory in this relative projection while
preserving the derivative hold and every broader aggregate, index, word, work,
matrix, stage, numeric, sampling, and macro boundary.
