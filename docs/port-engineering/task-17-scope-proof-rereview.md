# Task 17 frozen scope/proof re-review

## Decision

**APPROVED.** The corrected brief resolves the prior P2 and introduces no
remaining P0–P3 design finding.

## Prior P2 resolution

The corrected brief now requires parser-to-typed provenance for both the
original raw source and an immutable canonical runtime-define tuple.  The
tuple is explicitly key-sorted, type-tagged, preserves the distinction among
`bool`, `int`, finite `float`, and `str`, and cannot retain a caller-owned
mutable mapping.  Normalized `TypedProgram.source` remains separate.

That is sufficient and implementable in the current architecture: parse can
return the raw input string plus a tuple built from a copied map, semantic
analysis can carry both values into frozen `TypedProgram` fields, and validator
and emitter can independently compare the retained tuple to empty while
hashing both retained raw and normalized source strings against the two
key-specific constants.  The caller-supplied raw hash is explicitly demoted to
an additional generator gate, not boundary authority.

This closes the demonstrated ambiguity where parsing Sharpen with `{}` and
with `{"UNRELATED": 1}` produced byte-identical normalized source.  The
corrected required regression matrix now includes that same-normalized case,
the changed-normalized `{"GL_ES": 1}` case, and forged raw-source/define
provenance at both validation and emission boundaries.  It also requires
key-order stability and bool/int distinction, preventing ambiguous tuple
serialization.

## Rechecked evidence

- Fresh parse/semantic analysis with `{}` reproduced both source locks:
  Sharpen raw/normalized
  `c9a9b196e61a2904b37ad89c7fc46bee1b40b6bba81293dde3d7cd37527773e7` /
  `1a252d3d5efca1c657dcde87953b12c081c586da01d885e24d3b50395ec5abb0`;
  Sobel raw/normalized
  `ef459738b931929a65422df36f852da4e7cbe4e90387690bea747a34a2e52f84` /
  `d8aad0d49bd0b1badd5231b46bb7bd5a35f9eddadd466afd4ac9f1a0fc0cbf0c`.
- Current accounting was verified: 108 typed, 110 public, and 102 unported
  from 212; adding the exact pair yields 110 typed, 112 public, and 100
  unported.
- The proof remains deliberately source-specific: only size-nine local
  `float`/`vec2` tables, complete literal stores 0–8, then one direct
  `i=0; i<9; i++` read loop with the exact per-key role/read/control profile.
  Its stated tamper matrix rejects declaration/store/read/index/order/control
  changes without granting generic array or indexing support.
- Scalar `double` arrays preserve canonical JavaScript Number storage;
  zero-initialized `glsl::Vec2` arrays preserve Float32 vector lanes.  Direct
  `operator[]`, no `.at()`, no heap/dispatch work in pixels, and separate
  Debug/Release frame evidence remain correctly required.
- `node docs/port-engineering/task-17-oracle-generator.mjs --check`
  returned `ok task-17-oracles.json`.  The four canonical direct-factory
  oracle cases, exact-F32 amount, alpha variants, F32/RGBA8 hashes, probes,
  orientation, and double-render identity are unchanged and adequate.

## Frozen artifact hashes

- Corrected brief: `2306280acb661199c07cb2ad8e6607393129469b09d1d0976ed1bb7428719ba7`
- Risk audit: `17692e3784ad64a4a283f7509b8cabe65521cabe282d5a78d6e6ade17be24937`
- Oracle report: `4f7848798975d6025a138cbb9eb77080987a64188e3867dc7f90bc13d1bdec95`
- Oracle generator: `ab607be447bf86457267e8b76298e24961065407db54039c206d21a6b85dfb9e`
- Oracle JSON: `6a68386e0244a2c5ec0b183e4e5e4e3e59f01c30414f8854a041d871637c907a`

## Scope

This was read-only for the repository.  No Git command or repository write was
performed; this `/tmp` review document is the only file written.
