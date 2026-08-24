# Post-test-pattern frontier audit: Task 62 Median fixed-record selection

This is a read-only long-range projection relative to prepared Tasks 12–61.  The active Task-15 correction is explicitly separate and is not merged into counts, contracts, or completion claims.  The derivative ABI hold remains preserved.

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| after Task 61 | 184 | 186 | 26 |

## Recommendation: `median-radius3-fixed-record-selection-v1`

Admit exactly one factory profile, `filter/median:median` at `RADIUS=3`.  This is a closed 49-record selection specialization, not general mutable arrays, `while`, preprocessor branches, half packing, or scalar unsigned bit operations.

| field | exact value |
| --- | --- |
| key | `filter/median:median` |
| source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/median/median.glsl` |
| source SHA-256 | `95e869c02fe2645f4a1b5af5a7446b3f2bacb888f2c965bc272ba56b10666e5d` |
| source-bound metadata defaults | `{ "radius": 3, "threshold": 0 }` |
| define map | `{ "RADIUS": 3 }` |
| preprocessed fixed values | `REAL_COUNT=49`, `medianIndex=24` |

The profile has exactly two mutable automatic tables: `uvec2 majorRecords[49]` and `uint blueRecords[49]` (147 32-bit lanes, 588 bytes).  The literal `y=-3..3`, `x=-3..3` scan fills each entry once at `index=0..48`.  The source's in-place Hoare-style selection then reads, compares, and swaps only matched record positions until rank 24 is selected.

This is intentionally not merged with Task 15: the nested selection `while` statements require their own termination certificate.  For the pinned 49-element graph, every partition round advances `left` or decreases `right`; each scan cursor is monotone inside `[0,48]`; and the pivot is itself a live record, giving the two scan predicates an in-range stopping witness.  The proof therefore bounds selection at 49 partition rounds, with each round containing at most 49 left-cursor advances, 49 right-cursor advances, and 49 paired swaps.  No generic `while` acceptance follows.

## Exact admission contract

1. Accept only the pinned key/source digest, source-bound defaults, and define map above.  Reject `RADIUS` values 1 or 2, every other define, source drift, and threshold/profile mismatch before translation.  The `#if` chain is resolved only to `REAL_COUNT=49`.
2. Permit exactly `std::array<UVec2,49> majorRecords` and `std::array<std::uint32_t,49> blueRecords` as automatic entry-local storage.  They may be mutated only by the 49 fill writes and the matched three-assignment swap pair from the source.  Reject global/static/heap storage, arrays in parameters/returns, aliases, copies outside the exact swap temporaries, another extent/type, or an additional array.
3. Prove the fill grid exactly `y=-3..3` and `x=-3..3`, yielding index values `0..48` once each in row-major order.  Require the one `majorRecords[index]` and one `blueRecords[index]` write on each visit, with all records definitely initialized before any selection read.  Preserve clamped bottom-left `texelFetch` for the 49 reads and center-alpha capture at `x==0 && y==0`.
4. Admit only the pinned selection state graph: outer `left < right`; pivot reads at literal rank 24; inner cursor guard `scanLeft <= scanRight`; the two ordered-record scan predicates; matched temporary swap of both tables; and the two source updates of `left`/`right`.  Carry checked intervals for every index and a termination certificate as described above; reject an unproved cursor update, changed comparison, additional `while`, `break`, `continue`, recursion, or a source whose certificate cannot be rebuilt.
5. Admit only the source's packed-record routes: `packHalf2x16(Vec2) -> uint`, `unpackHalf2x16(uint) -> Vec2`, scalar `floatBitsToUint(float)`, and the exact uint masks/shifts/OR used to swap RG halfword order plus the `& 0xffffu` blue extraction.  Materialize Float32 before float bits and use the established IEEE binary16 pack/unpack authority.  Reject other widths, signed bitwise operations, vector bit reinterpretation, arbitrary shift counts, other packing routes, texture LOD/gradient/image operations, derivatives, or a resource/stage ABI feature.

## Required tests and oracles

- Acceptance tests lock the identity/defaults/`{RADIUS:3}` profile and reject all other radius defines, source drift, and threshold binding mismatch.
- Structural tests prove exactly two 49-element arrays, 49 paired fill writes, full initialization, all selection index intervals, matched record swaps, the certified bounded selection graph, and absence of an uncapped/general `while` lowering.
- Runtime tests compare a reference that uses the exact source record ordering: brightness Float32 bits, RG half packing with the halfword swap, and blue half word.  Include non-square and one-pixel images, clamped edges/corners, repeated colors, brightness ties, half-rounding boundaries, threshold `0` and positive thresholds around the replacement boundary, opaque and non-opaque center alpha, and repeated-render determinism.
- Negative tests reject `RADIUS=1/2`, a table extent other than 49, an altered fill/selection bound, a dynamic array escape, an unmatched record swap, a noncertified cursor update, a changed packed-word operator/count, a different pack/unpack overload, a general `while`, derivatives, sampler arrays, LOD/gradient/image syntax, and every other source key.

## Residual frontier after this slice

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| relative after Task 62 | 185 | 187 | 25 |

The remaining work is deliberately broader: fragment derivatives remain held; dither-style mutable/work-budgeted aggregates; other packed-word or scalar integer contracts; matrices/copy-out; and resource/stage ABI changes.  This one radius-3 selection exception establishes none of those features.

## Boundary statement

This audit is planning evidence only.  It makes no repository change, does not alter or count active Task 15, and does not claim implementation or merge completion.  The derivative ABI hold is preserved.
