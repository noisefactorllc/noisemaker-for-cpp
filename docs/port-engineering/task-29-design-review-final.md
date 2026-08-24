# Task 29 independent design review

Date: 2026-08-12

## Verdict

- **SPEC CONSISTENT: NO**
- **IMPLEMENTATION READY: NO**
- **Critical findings: 0**
- **Important findings: 2**
- **Minor findings: 0**
- **Blockers:** repair and re-freeze the direct ABI oracle and the branch-parent
  authentication described below, then repeat this bounded design review.

The production direction is otherwise sound: `const Surface&` is the narrow
non-null, non-owning, read-only synchronous helper ABI; current state remains
two setup-owned `const Surface*`; destroying `Bindings` after bind is safe only
while both stable-address surfaces remain alive and externally unmodified;
same-Surface aliasing is valid; and `run_pass` creates separate output storage.
Fresh source/IR traversal reproduced sampler parameters 13/14 with canonical
`direction=in,writable=True`, exactly two read-only uses each, exact calls
`(tex#2,inputTex#1,uv#33)` / `(inputTex#1,tex#2,uv#33)`, mutually exclusive
branches, four static texture sites, four static textureSize sites, and one
64-trip loop. Thus the selected path is exactly 67 reads and, separately, 67
size queries.

## Important findings

### I1. The frozen eight-mode direct ABI oracle is structurally vacuous and internally contradictory

**Evidence:** `task-29-oracle-generator.mjs:102-110` declares mode 1
`exact-depth-b-const-refs` and mode 6 `wrong-resource-order` with the identical
semantic tuple `const-ref,inputTex,tex,phaseA=0,phaseB=1`. The generated JSON
confirms every structural/result field is identical except the freely assigned
ID, name, and `accepted` label. The uniqueness check at line 151 includes ID and
name, so renaming the same behavior makes it pass. The numeric check at line
150 only compares mode 6 to mode 0; mode 6 is byte-for-byte the same operation
and witness as valid mode 1. No call-site/depthSource context exists to make the
order wrong.

Mode 3 is also not a copy. Although declared as `tex-copy` /
`inputTex-copy`, `directRecord` lines 113-126 resolves those strings back to
the original `tex` and `inputTex` objects and fabricates `owns_copy=true` from
the ABI label. The resulting oracle simultaneously claims ownership copies and
object aliasing with the originals. The writable/nullable facts are likewise
derived from labels rather than an executed or independently authenticated
shape. This contradicts the brief's requirement that every mode have a
distinct structural signature/counter and that ABI negatives never fall
through to a baseline renderer (`task-29-brief.md:68-79`).

**Fix contract:** add explicit call-site/depthSource context to every ordered
mode, so mode 6 is demonstrably the wrong order for a named branch while mode 1
is the right order for the other branch. Actually allocate independent copied
surfaces for the value-copy mode and derive identity/alias/ownership fields
from object behavior, not the requested ABI label. Separate declared metadata
from observed witness fields. Define the semantic structural signature without
ID, name, or expected acceptance and require pairwise uniqueness (or explicitly
classify value-identical but shape-distinct negatives). Re-freeze the oracle,
report, brief/design hashes, and require the eventual C++ switch/table parser
to authenticate the context, actual ABI spelling, actual copy/borrow identity,
and observed counters.

### I2. The package claims exact branch-parent freezing but freezes only assignment parents

**Evidence:** `task-29-brief.md:16-20` says both branch parents are frozen by
`task-29-recomputed.json`, and the adversarial contract requires authentication
of both complete calls, their parent branches, and branch predicate/ownership.
However `task-29-recompute.py:171-173` traverses calls while retaining only the
immediate expression parent. `call_records` at lines 202-212 stores that
parent's kind/hash/child index; both records therefore identify an `assign`,
not the enclosing `if` branch. The profile tuple at lines 227-232 repeats only
that assignment data. Branch side is inferable from an opaque path and the
whole-program digest, but the same audit explicitly says whole-program hashes
are not substitutes for independent object authentication.

**Fix contract:** locate and freeze the exact enclosing conditional statement,
its exact predicate object/hash/symbol relation, then/else child identity,
branch ordinal, branch statement cardinality, and call-to-branch ownership for
both calls. Include those objects/coordinates in the profile tuple and JSON;
require the profile to return objects owned by the authenticated tree and make
validator/emitter count them exactly. Add one-axis tests for predicate change,
branch swap, call movement/outside-branch, duplicated/executed-both branch, and
forged old-branch objects on an equal reconstruction. Re-freeze dependent
artifacts and sidecars.

## Frozen-package and baseline evidence

All current Task 29 and accepted Task 28 SHA-256 sidecars authenticate,
including the adversarial audit at
`ff374db0c0905792b0e138d583518e7dcc634950b9dd2f59442d15e259e31270`.
`task-29-recompute.py --check`, the refreshed Task 29 oracle check, the older
future Focus oracle check, and the public-identity fixture check all pass.
Accepted Task 28 repository bytes match all hashes frozen in
`task-29-recomputed.json`: 212 corpus / 128 typed / 130 public / 82 unported,
projecting Focus alone to 129 / 131 / 81 at ordinal 110 with ordered hashes
`c2561c59...` / `2325f8d0...`. The accepted Task 28 review/fix/rereview package
also authenticates and closes its prior three Important findings.

The source/tree/interface/helper/resource/public identity, exact empty defines,
and projection claims independently recompute. No generic `sampler2D` type
widening is needed: emitter admission belongs only in
`function_parameter_type` for the two exact authenticated parameters, while
validator and emitter must independently reject every foreign sampler-helper
shape. The proposed lifetime test (surfaces outside an inner `Bindings` scope,
kernel used after `Bindings` destruction under ASan/UBSan), pixel fixtures,
real Task 28 reconstruction, warnings-as-errors, stack, disassembly, and prior
oracle gates remain appropriate after the two frozen-package repairs.

No repository file or Git state was changed by this review.
