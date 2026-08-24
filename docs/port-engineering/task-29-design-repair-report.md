# Task 29 design-review repair report

Date: 2026-08-12

## Verdict

Both Important findings in design review SHA-256
`03df2d76c6a9aa99315ff3070d3f89180b797d47d7d7cc4749cadb011ae08ef6`
are repaired. The package is ready for bounded re-review. No repository or Git
state changed.

## I1: direct ABI oracle

- Retained eight modes, but mode 6 is now explicitly the wrong mapping for
  `depthSource==0/then`; it is no longer a duplicate of valid else mode 1.
- Every mode owns an explicit no-default switch arm. Declared, handled, switch,
  and observed ID sets are exactly `[0,1,2,3,4,5,6,7]`; invalid ID 8 rejects.
- Observed branch/ABI/resource/alias/copy/null/write/read facts and counters are
  derived from executed objects. By-value allocates, owns, and reads two
  independent Surface copies (96 F32 lanes) and aliases neither original.
- Eight semantic structural signatures are pairwise unique while excluding
  IDs, names, acceptance, and numeric result. Dispatch, mix, copy, and witness
  source hashes are frozen for switch/witness tamper detection.

## I2: conditional ancestry

- Recomputation now traverses and retains complete expression and statement
  ancestry for each call, generically locates the unique enclosing `if`, and
  authenticates direct branch-child ownership by object identity.
- It freezes predicate path/kind/type/span/hash/operator/child relations,
  then/else objects and slots, branch cardinality, owned call hashes, one call
  per branch, all calls under the same conditional, mutual exclusivity, and
  exact one-call dynamic min/max.
- Frozen mutation controls cover predicate change/equal reconstruction,
  branch swap, call movement, copying into either/always-executed paths,
  both-executed behavior, and call-slot swap.

## Validation

- `task-29-recompute.py --check`: pass.
- `task-29-oracle-generator.mjs --check`: pass (6 public, 8 direct).
- JSON assertions for `[1,1]` branch cardinality, exact-one dynamic call,
  declared/handled/observed equality, eight unique signatures, invalid enum,
  and real copy ownership/non-aliasing: pass.
- All changed Task29 SHA-256 sidecars authenticate.

Key hashes: recompute script `096dbced...`, recomputed JSON `03ffff1b...`,
oracle generator `01b208c8...`, oracle JSON `b16c120e...`, brief `88e98423...`,
implementation design `01d48009...`.
