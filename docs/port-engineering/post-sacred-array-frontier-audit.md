# Post-sacred-array frontier audit: Task 61 Test Pattern closed table profile

This is a read-only long-range projection relative to prepared Tasks 12–60.  The active Task-15 correction remains separate and is not merged into any count, contract, or completion claim here.  The derivative ABI hold remains preserved; the source's grid-line path explicitly uses direct resolution math and contains no fragment-derivative builtin.

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| after Task 60 | 183 | 185 | 27 |

## Recommendation: `test-pattern-closed-small-table-profile-v1`

Admit exactly one factory, `synth/testPattern:testPattern`, as a closed source profile.  Do not turn this into general global arrays, array constructors, dynamic indexing, vector rounding, or scalar-shift support.

| field | exact value |
| --- | --- |
| key | `synth/testPattern:testPattern` |
| source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/testPattern/testPattern.glsl` |
| source SHA-256 | `f913300a1312c6630d56fa1cc2faf2cb17fe0643d832473fdec7b66dd373cb20` |
| source-bound metadata defaults | `{ "gridSize": 4, "pattern": 0 }` |
| define map | `{}` |

The source has three independent, tightly bounded table shapes:

1. immutable `const int GLYPH[10] = int[10](...)`, with ten positive literal bitmaps and only `GLYPH[digit]` read in `sampleGlyph` after `digit` is proved `0..9`;
2. automatic `int digits[3]`, with the exact `i=0..<3` writes and the only dynamic read `digits[numDigits - 1 - d]`; and
3. automatic `vec3 colors[8] = vec3[8](...)`, initialized by the eight literal bars and read only as `colors[bar]` after `bar=clamp(int(uv.x*8.0),0,7)`.

The remaining exact forms are also closed to this source: `GLYPH[digit] >> bitIndex` uses a positive glyph record and proved `bitIndex=0..14`; and `round(vec2)` appears only in `dotGrid` as `round(scaled)`.  A binding preflight proves `1 <= gridSize <= 16`; it makes the checkerboard cell number `0..255`, so `numDigits` is `1..3` and the `digits` read is `0..2`.

## Exact admission contract

1. Accept only the pinned key/digest, empty define map, and metadata profile above.  At factory binding, reject `gridSize` outside `1..16` and `pattern` outside `0..6`; metadata defaults alone are not a runtime proof.
2. Permit exactly the immutable ten-element `GLYPH` source table, lowered as an immutable `std::array<std::int32_t,10>` with the pinned positive literal sequence.  It is read-only, non-address-taken, non-escaping, and has no mutable static or global state.  Permit only `GLYPH[digit]` after the source guard proves `digit=0..9`.
3. Permit exactly two automatic function-local arrays: `std::array<std::int32_t,3> digits` in `renderNumber`, and `std::array<Vec3,8> colors` in `colorBars`.  `digits` gets exactly three writes from `i=0..<3`, then only read at `numDigits-1-d` when `d=0..<numDigits` and `numDigits=1..3`; `colors` gets exactly its eight literal Vec3 initializer entries and is read only at clamped `bar=0..7`.  Reject every other array declaration, constructor, index, copy, parameter, return, alias, or escape.
4. Permit only the source's proven nonnegative signed shift: `GLYPH[digit] >> bitIndex`, followed by existing `& 1`, where the glyph value is nonnegative and `bitIndex=0..14`.  Emit an ordinary nonnegative `std::int32_t` right shift; reject negative values/counts, a count outside `0..14`, left shifts, other `&`/`|`/`^` forms, or any other key.
5. Permit only `round(Vec2) -> Vec2` at `round(scaled)` in `dotGrid`, materializing each lane at the established Float32 boundary.  Reject scalar widening, Vec3/Vec4, roundEven, matrix/array operands, or another call site.  Preserve all existing checkerboard, color-bar, gradient, UV, grid, hue, and dot-grid branches; do not add derivatives, texture/image operations, matrices, packed-half operations, or a resource/stage ABI feature.

## Required tests and oracles

- Acceptance/preflight tests lock key/source/defaults/empty defines and reject grid size below 1 or above 16, pattern outside `0..6`, and every source/profile mismatch.
- Structural tests prove the three table shapes and exact element counts; all `digits` write/read intervals; `colors` initializer order and clamped read; glyph value/count intervals; and the one permitted Vec2 round AST site.
- Runtime tests compare a direct reference over all seven pattern values, grid sizes `1`, `4`, and `16`, non-square dimensions, corner/boundary coordinates, all glyph digits, 1/2/3-digit cell labels, each color-bar index, and dot-grid half/integer boundary cases.  Verify glyph row/column bit ordering, positive-shift behavior, opaque alpha, direct-resolution grid-line width, and repeated-render determinism.
- Negative tests reject mutable or nonliteral global tables, an array outside the three names/types/extents, partial or duplicate `digits` writes, an unproved dynamic index, a shift with a negative/unproved operand/count, a vector round of any other arity/site, derivatives, sampler/LOD/image operations, and every source key other than the allowlisted one.

## Residual frontier after this slice

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| relative after Task 61 | 184 | 186 | 26 |

The remaining frontier is now dominated by genuinely broader work: derivatives remain held; median/sorting and larger mutable aggregate cases; wider packed-word forms; matrix/copy-out; and resource/stage ABI changes.  This test-pattern exception implies none of them.

## Boundary statement

This audit is planning evidence only.  It makes no repository change, does not alter or count active Task 15, and does not claim an implementation is merged.  The derivative ABI hold is preserved.
