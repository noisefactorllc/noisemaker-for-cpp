# Task 29 independent design re-review

Date: 2026-08-12

## Verdict

- **SPEC CONSISTENT: YES**
- **IMPLEMENTATION READY: YES**
- **Original Important findings addressed: 2/2**
- **New Critical findings: 0**
- **New Important findings: 0**
- **New Minor findings: 0**
- **Blockers: none**

The repair report authenticates as
`aabfe681dba6959aea0fc587a3ecf22acf66487b79a305800eb557b3e9501613`.
Every current Task 29 SHA-256 sidecar authenticates. Fresh execution of
`task-29-recompute.py --check` and `task-29-oracle-generator.mjs --check`
passes, and an independent JSON reconstruction/assertion pass reports
`INDEPENDENT_TASK29_REPAIR_ASSERTIONS_OK`.

## Original finding dispositions

### I1 — vacuous/contradictory direct ABI oracle: ADDRESSED

The eight semantic structural signatures independently recompute to eight
unique SHA-256 values. Their payloads exclude ID, name, expected acceptance,
and numeric result. The former duplicate is now unambiguous: mode 1 is the
canonical `depthSource!=0/else` mapping while mode 6 is the reversed mapping in
the `depthSource==0/then` context. Their branch witnesses differ, and mode 6
also numerically diverges from canonical then-mode 0.

Mode 3 now constructs two independent `Surface` objects from independent
`Float32Array` storage and passes those objects to the tracked mix. Observed
identity proves neither copy aliases either original; both are in the owned
set; the owned count is two. Execution observes two allocations, 96 copied F32
lanes, two scene reads, two depth reads, and one mix call. Source names are
provenance labels only and no longer masquerade as object identity.

All declaration, handled, observed, and parsed switch-case ID lists are exactly
`[0,1,2,3,4,5,6,7]`. Each arm increments its own dispatch witness exactly once;
invalid ID 8 reaches the post-switch rejection. The oracle freezes separate
hashes for declarations, the complete no-default dispatch switch, tracked mix,
record/witness construction, and copy implementation. Exact counters and
declared-versus-observed branch/ABI/resource fields are frozen in JSON. The
implementation contract additionally requires token-wise authentication of
the generated C++ table, switch, and witness while oracle JSON remains
unchanged, so a label-only or fabricated-witness implementation cannot satisfy
the design.

### I2 — missing enclosing conditional/branch authentication: ADDRESSED

The recomputation walker now retains expression and statement ancestry for
every helper call. Each call has exactly one enclosing `if`; both resolve by
object identity to the same conditional. The next ancestry object is the exact
direct branch child at its authenticated ordinal, not merely an opaque path or
whole-program hash.

The frozen proof records the conditional object/path/span/hash, the complete
predicate object and child relations (`depthSource#9 == 0`), both branch
objects and then/else slots, statement/expression cardinalities, complete
parent chains, branch-owned call hashes, and exact argument IDs. Independent
checks reproduce branch call cardinality `[1,1]`, dynamic minimum/maximum
`1/1`, mutual exclusivity, and complete conditional ownership. The profile
tuple includes these coordinates rather than relying on the whole-program
digest alone.

The repaired brief, adversarial audit, and implementation design explicitly
require candidate-owned objects and one-axis rejection for predicate change,
equal reconstruction with forged old objects, branch swap, call movement,
copy into either or always-executed paths, both-executed behavior, removal,
and call-slot swap. Validator and emitter must independently count the exact
objects returned by their own authentication.

## Remaining design assessment

The narrow `const Surface&` ABI remains correct. It grants a synchronous,
non-null, non-owning, immutable borrow only for the exact two Focus helper
parameters. State remains two setup-owned `const Surface*` fields; surfaces
must stay alive, stable-addressed, and externally unmodified through kernel
use; same-object aliasing is valid; destroying `Bindings` after binding is
safe while surfaces remain alive; and `run_pass` provides fresh output.

Fresh source/IR evidence still proves canonical `in,writable=True` sampler
parameters 13/14 with zero writes/escapes, exactly two allowed uses each,
four static texture and four static textureSize sites, one selected helper call,
and one 64-trip loop. The maximum pixel path is exactly 67 texture reads plus,
separately, 67 textureSize evaluations. No generic `sampler2D` spelling,
runtime/parser/IR/CMake widening, ownership, nullable/mutable helper ABI, or
second program is authorized.

The remaining implementation gates are appropriately strict: exact profile
and consumed-object counts; exhaustive protected-coordinate mutations; real
accepted Task 28 reconstruction; generated code-shape checks; six public pixel
fixtures; eight direct modes; lifetime-after-`Bindings` destruction under
ASan/UBSan; semantic branch/read/loop/alpha mutations; full switch/witness
tamper; all bindings; Debug/Release warnings-as-errors; stack and AArch64
disassembly; all prior oracles; and independent implementation review with no
Critical or Important finding.

No repository file or Git state was changed by this re-review.
