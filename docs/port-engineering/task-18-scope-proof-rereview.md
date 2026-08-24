# Task 18 frozen scope/proof re-review

## Decision

**APPROVED.** The corrected brief resolves the prior P1 and P2 without
introducing a remaining P0–P3 design finding.

## P1 resolution — unreachable zero-dimension branch

The brief now explicitly recognizes the production invariant: canonical and
native public APIs reject zero-sized surfaces, native bindings retain concrete
positive `Surface*` values, and no zero-dimension injection or test/runtime/
resource seam is authorized.

Acceptance evidence is correspondingly realizable and appropriately scoped.
Both validator and emitter must reconstruct the exact `textureSize` predicate,
zero assignment, return, and dominance over every array declaration, fetch,
grid loop, store, and counter update.  Emitted-code order assertions provide a
second boundary, and forged trees that remove, move, weaken, or bypass the
branch must reject.  This preserves the authored branch without invalid
`Surface` construction, object-layout tricks, or an ABI/hot-path change.

## P2 resolution — exact loop update form

The brief now identifies the exact loops as
`ky=-1; ky<=1; ++ky` and nested `kx=-1; kx<=1; ++kx`, requires their update
expressions to be typed `unary` prefix nodes, and explicitly rejects postfix
replacements.  Fresh semantic inspection confirmed both canonical sources
produce exactly two `unary` `++` loop headers.  This supplements the generic
counted-loop summary, which intentionally records only `update="++"` and does
not distinguish prefix from postfix.

## Rechecked design evidence

- Scope/counts remain exactly 112 typed / 114 public / 98 public-unported from
  the accepted 110 / 112 / 100 Task 17 baseline.
- Raw/normalized source locks, empty immutable define provenance, exact binding
  signatures, and source-specific RHS/read/control census are unchanged.
- The nested-grid proof still establishes three trips per loop, lexical product
  nine, entrypoint charge 12, direct `samples[idx]` store immediately followed
  by discarded `idx++`, store interval 0–8, final counter 9, and only the exact
  later literal reads.
- Zero-initialized `std::array<double, 9>`, proved direct indexing, `noexcept`,
  allocation-free hot-path requirements, exclusions, and Debug/Release stack
  evidence remain correctly bounded.
- Fresh `node docs/port-engineering/task-18-oracle-generator.mjs --check`
  returned `ok task-18-oracles.json`; the six positive-path canonical cases
  are unchanged.

## Frozen artifact hashes

- Corrected brief: `8ea81afc0f9488c533bafc372ea92565f2237ee0e473ebef313503b940d8719b`
- Risk audit: `45e7efad86d2b390068052bdec914a413bf3540ac8f5af6cf53ed1290a28cbda`
- Oracle report: `16199e11d4ec8af8c4c5ecf86748d16573c2f53c61ed4e3bd4c79acec8a710f3`
- Oracle generator: `ef9ec7303f2e610af7384e3c681935be725bce8019498e3f2b49f9e6ec6489c8`
- Oracle JSON: `6bfefcf7891f55896e1ff5be6cd67db94c21853f90073a851eacc8ff18da9c1b`

## Scope

This was read-only for the repository.  No Git command or repository write was
performed; this `/tmp` review document is the only file written.
