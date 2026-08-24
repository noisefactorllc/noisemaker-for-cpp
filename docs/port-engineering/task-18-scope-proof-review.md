# Task 18 frozen scope/proof/oracle review

## Decision

**NOT APPROVED — one P1 and one P2 design finding.**

The two-key capability, source-specific table/counter proof, precision rule,
count arithmetic, exclusions, and six canonical oracle cases are otherwise
coherent.  The required native zero-dimension injection cannot be performed
through the current C++ resource interfaces without a new test seam or a
runtime/resource change, and the brief's claimed exact loop spelling disagrees
with both canonical sources.

## P1 — zero-width/zero-height native sampler injection has no legal interface

The brief requires native tests to bind a zero-width sampler and a zero-height
sampler to a positive output pixel, then prove exact zero output, no fetch, and
no table/counter-grid entry, while retaining public `Surface` validation and
making no resource ABI change.  The current interfaces provide no object that
can satisfy those conditions:

- both `Surface` constructors call `channel_count`, which throws
  `std::invalid_argument` when either extent is zero;
- `glsl::Bindings::set_texture` accepts only `const Surface&` and stores a
  `const Surface*`;
- generated kernel state likewise stores `const Surface*`;
- `texture_size`, `texel_fetch_bottom_left`, and all sampler functions consume
  concrete `Surface` references directly; and
- `Surface` is not polymorphic, has private dimensions/storage, and exposes no
  test-only unchecked constructor or sampler abstraction.

There is also no fetch/grid instrumentation hook in the sampler, kernel,
binding, or pass-runner interfaces.  Mutating private object layout through a
cast, placement trick, or `#define private public` would violate C++ object
invariants and cannot serve as acceptance evidence.  A zero-sized destination
cannot help because `run_pass` constructs a `Surface` before invoking any
pixel.

### Required correction

Choose and freeze one realizable contract before implementation:

1. **Recommended:** acknowledge that the branch is unreachable under the
   production resource invariant and replace the native injection requirement
   with both-boundary source-profile/tamper tests plus exact emitted-C++
   assertions proving the `textureSize` predicate, zero assignment, return,
   and dominance over the array declaration/grid.  Keep ordinary positive
   native oracle tests for executable behavior.
2. If dynamic execution is mandatory, explicitly authorize and specify a
   narrow test resource/sampler seam that can represent zero extents and count
   fetches/grid entry.  Its production ABI, hot-path, ownership, and `noexcept`
   consequences must be reviewed as additional scope.  A zero-size `Surface`
   constructor alone would still not prove “no fetch” or “no grid entry.”

As frozen, the acceptance requirement is impossible without stepping outside
the stated scope, so implementation cannot honestly satisfy the brief.

## P2 — “exact lexical” loop update spelling is wrong

The brief says the exact lexical grid is
`ky=-1; ky<=1; ky++` with nested `kx=-1; kx<=1; kx++`.  Both pinned sources
actually use prefix updates:

```glsl
for (int ky = -1; ky <= 1; ++ky) {
    for (int kx = -1; kx <= 1; ++kx) {
```

Fresh typed analysis confirms both header updates are `kind="unary"`,
`operator="++"`; the existing counted-loop summary intentionally collapses
prefix/postfix to `update="++"`.  Because Task 18 demands a source-specific
exact structural profile, relying only on that summary would accept a forged
postfix header with authentic source provenance.

Correct the brief to `++ky` / `++kx`, require the source-specific proof to
check unary-prefix expression kind as well as the counted-loop facts, and add
both-boundary tamper negatives that replace either header with postfix.

## Verified evidence outside the findings

- **Counts:** the current post-Task-17 slice has 110 typed entries; the pinned
  corpus has 212 and the public baseline is 112.  Adding exactly the two Task
  18 keys yields 112 typed / 114 public / 98 public-unported.  Neither key is
  currently in the typed allowlist.
- **Source/provenance:** fresh parse/semantic analysis with empty defines
  reproduced Cel raw/normalized
  `9c2848c92bd0f3e2de76fd065ac8fc55086cb7d209ce09ac4ba6488acda4630e` /
  `c8e56f507bfa71ac7d43dbe7cc8060695a2e0fc1eb2f1b2bc19e2ed17d55411e`
  and Outline raw/normalized
  `cfe848d1605f1ad693fd3ce9e518a4adf4e0f34e3fff6c6ae1ebcaec49949f5d` /
  `fa3eb35ad201e4cbf44a0f3e43060652f2cf099a6b2de1c7c4f906c0d30cca5d`.
  Task 17's retained raw/normalized/type-tagged-define provenance contract is
  correctly inherited.
- **Proof feasibility:** each program has one `float[9] samples`, one direct
  dynamic `samples[idx]` store followed by discarded `idx++` in the three-by-
  three nested grid, counted-loop product 9 and entrypoint charge 12.  The
  literal read census is exactly two Sobel sums over indices
  `{0,1,2,3,5,6,7,8}`; index 4 is not read, while all nine stores remain
  required.  The brief appropriately locks the complete source-specific RHS,
  symbol/index census, store-before-increment order, counter interval, early-
  return dominance, and forged-tree negatives at both boundaries.
- **Precision/emission:** zero-initialized `std::array<double, 9>` matches the
  canonical plain JavaScript Number array and 72-byte raw payload on the
  supported target.  Direct `operator[]` is appropriate only under the
  reconstructed interval proof; `.at()`, generic index/postfix emission,
  allocation, and dynamic dispatch remain excluded.  Debug/Release `.su`
  frame evidence is correctly required separately.
- **Bindings/exclusions:** the declared binding signatures match the source
  interfaces, remain required and exactly typed, and add only these pass
  factories.  Task 17's literal-store profile, Refract's array parameter, and
  Sacred Geometry's `vec2[13]` affine/nested profile remain outside scope.
- **Oracle truth/coverage:** fresh
  `node docs/port-engineering/task-18-oracle-generator.mjs --check`
  returned `ok task-18-oracles.json`.  The generator directly binds pinned
  canonical CPU factories and byte-compares six double-rendered cases.  Its
  non-square F32 input, larger output, nonzero tile/full resolution, exact-F32
  width/thickness/thresholds, Cel boundary contrast, all four Outline metrics,
  F32/RGBA8 hashes, probes, wrap coverage, orientation, and metric-4 divisor
  provide adequate executable positive-path coverage.  It correctly states
  that public canonical APIs cannot supply the zero-size case.

## Frozen artifact hashes

- Risk audit: `45e7efad86d2b390068052bdec914a413bf3540ac8f5af6cf53ed1290a28cbda`
- Brief: `99f8835a0563e03cd529dcdb66847530837d7219ae284d2861603b59dc9d989d`
- Oracle report: `16199e11d4ec8af8c4c5ecf86748d16573c2f53c61ed4e3bd4c79acec8a710f3`
- Oracle generator: `ef9ec7303f2e610af7384e3c681935be725bce8019498e3f2b49f9e6ec6489c8`
- Oracle JSON: `6bfefcf7891f55896e1ff5be6cd67db94c21853f90073a851eacc8ff18da9c1b`

## Scope

This review was read-only for the repository.  No Git command or repository
write was performed; this `/tmp` review document is the only file written.
