# Post-varying frontier audit: Task 50 spooky ticker scalar word mask

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-49.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 49 | 172 | 174 | 38 |

## Recommendation: `spooky-ticker-uint-mask-and-glyph-image-v1`

The next smallest exact slice is `filter/spookyTicker:spookyTicker`. It reuses
Task 49's sole `v_texCoord -> PixelContext::uv` interface, the Task 48 glyph
index proof, source integer constants, scalar signed glyph extraction, and the
existing scalar/vector unsigned PRNG forms. Its only new word operation is one
scalar unsigned mask, paired with the two exact signed/unsigned representation
conversions needed to derive scrolling cells. It does not establish general
unsigned bitwise arithmetic, numeric casts, arrays, or stage inputs.

| Key | Exact defines | Source SHA-256 | New word node | Reused aggregate |
| --- | --- | --- | --- | --- |
| `filter/spookyTicker:spookyTicker` | `{}` | `d50ca880cd6c6c03dd01a7ae683316d42ed93baddaadce9f3b918be1c816d50f` | `hash_mix(uint(rowSeed) ^ 17u) & 0xFFFFu` | exact 80-entry `GLYPHS` image, SHA-256 `a991e8fc9c7e27dfb03184422e0288f061982669ecbb064906b0b1c6b8c9b7a2` |

The glyph image is byte-for-byte equal to Task 48's OSD table: 80 ordered
`int` literals in `0..126`, with one guarded read `GLYPHS[digit * 8 + gy]`.
`digit = int(h % 10u)` has range `0..9`; the preceding glyph guard gives
`gy=0..7`, so the index remains `0..79`. Its extraction reuses the established
nonnegative signed shift/mask proof, with `row=0..126` and `6-gx=0..6`.

The new unsigned `&` has exactly one left operand: the result of `hash_mix`
after `uint(rowSeed) ^ 17u`; its right operand is literal `0xFFFFu`. Its value
is therefore in `0..65535` and flows only through `float(...)/65535.0` into
`scrollSpeed`. The source also has exactly these representation conversions:
`uint(cellX)`, `uint(rowSeed)`, and `int(hash_mix(uint(rowIdx)+baseSeed))`.
They need the existing checked 32-bit bit-preserving signed/unsigned conversion
helper, never an implementation-defined C++ cast: signed-to-unsigned is modulo
`2^32`, and the named uint-to-int node reinterprets the resulting 32 bits.
None of the resulting words control an array extent, loop, allocation,
resource selection, or dispatch.

The source contains no loop, derivative, matrix, struct, uniform block,
parameter direction, sampler array, `textureLod`, mutable global, or
neighboring-pixel read. The authored interface is one input sampler, uniform
`renderScale`, runtime time, `speed`, `alpha`, `rows`, `seed`, output
`fragColor`, and the already-admitted `v_texCoord`. Metadata binds inputTex,
speed, alpha, rows, and seed; its declared defaults are `1`, `0.75`, `2`, and
`1` respectively.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/spookyTicker:spookyTicker` with the metadata-verified
   empty define map and pinned source hash above. Reject another key, a
   nonempty/absent/additional define, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Reuse the Task-49 stage declaration only when it is exactly read-only
   `in vec2 v_texCoord` lowering to `context.uv`. Reuse the Task-48 array
   facility only when the literal sequence's pinned image hash matches above,
   its extent/type are exactly `int[80]`, and its sole read has the same
   `digit*8 + gy` range proof. Emit automatic immutable storage only; reject a
   changed image, a second aggregate, general indexing, write/copy/escape,
   static storage, pointer/reference, heap, or dynamic container.
3. Permit exactly one `uint & uint -> uint` typed node at the pinned
   `scrollSpeed` expression, with right literal `0xFFFFu`, result range
   `[0,65535]`, and direct float-normalization consumer. Lower with a dedicated
   32-bit unsigned helper or defined `std::uint32_t` operation. Reject another
   unsigned mask, `|`, `~`, `<<`, compound word assignment, arbitrary
   expression shape, unknown mask/range, or result escape.
4. Permit only the three named `int`/`uint` conversions and preserve their
   typed source spans, operand routes, and 32-bit bit pattern. Lower signed to
   unsigned as modulo `2^32` and the one hash result unsigned to signed as an
   explicit bit reinterpretation; reject float-to-word reuse, a second
   uint-to-int site, range-dependent cast lowering, implicit C++ narrowing, or
   any new conversion pair.
5. Reuse existing `hash_mix` scalar unsigned multiply/XOR/right-shift forms,
   integer modulo, source scalar constants `GLYPH_W=7`, `GLYPH_H=8`,
   `BASE_SCALE=3`, and `BASE_ROW_GAP=4`, ordinary sampling, and local control
   flow. Bind only the authored inputs and retain direct `PixelFn` calls as
   `noexcept` and allocation-free. Reject a changed PRNG expression or word
   site, sampler/LOD variation, loop, derivative, matrix, struct, uniform
   block, `out`/`inout`, discard, multi-pixel dependency, or caller-defined
   stage data.

Required positives are frozen ticker oracles for all ten digits and eight
rows, both low and high-bit `rowSeed` outcomes, negative/positive `cellX`,
time/speed/seed variations, all metadata rows/alpha values, render-scale
rounding boundaries, non-square and one-pixel axes, ticker-region boundaries,
and repeated/tiled output. Direct tests must lock the shared 80-entry image
hash and ordered values, one guarded index at 0 and 79, one unsigned mask,
the three conversion nodes with `0`, `INT32_MAX`, `INT32_MIN`, and all-ones
bit patterns, the `context.uv` stage binding, and byte-identical repeated
output. Compile generated C++ with warnings as errors and assert zero hot-path
allocations and indirect calls.

Required negatives reject interface/table/index/guard/range/hash drift; a
second input varying or caller binding; any other aggregate/index/write/escape;
another unsigned mask or scalar word form; implicit signed/unsigned conversion;
loop, derivative, matrix, struct, uniform block, parameter direction, sampler
array, nonzero/computed LOD, draw/feedback resource behavior, or
key/define/macro/numeric-contract drift.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 50 | **173** | **175** | **37** |

## Ranked residual map after Task 50

This exact scalar mask and duplicate glyph image do not establish a general
word or stage ABI, aggregate model, derivative semantics, or multi-pixel work.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Larger aggregate/index/word forms | dither, median, test pattern | Require additional arrays/indexing/lifetime, sorting, pack/unpack or bit reinterpretation, or broader word rules. |
| 3 | Matrix, struct, copy-out, and block interfaces | historicPalette/palette, Julia/Mandelbrot/Newton, remap | Need aggregate layout, parameter direction, copy-out, or std140 binding contracts. |
| 4 | Broader stage and texture pathways | grime, texture | Need bit reinterpretation, loops, additional stage/resource inputs, or feedback ownership. `wormhole:deposit` remains a canonical point-draw coverage source with no runtime kernel key. |
| 5 | General work and resource policy | dynamic multi-pixel scans | Need distinct dimension provenance, output cardinality, and budget rules. |

Task 50 adds one hash-pinned typed factory in this relative projection while
preserving the derivative hold and every broader interface, word, aggregate,
index, work, resource, sampling, numeric, and macro boundary.
