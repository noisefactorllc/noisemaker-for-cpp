# Task 30 implementation rereview: Extrude bvec2 relational/reduction closure

Date: 2026-08-12
Author: independent adversarial reviewer (fresh session, no prior Task 30 context other than the documents cited below)

Scope reviewed: `tools/glslcpp/frontend/extrude_bvec2_relational_reduction_profile.py`,
`tools/glslcpp/generate_typed_slice.py`, `tools/glslcpp/emit_typed_cpp.py`,
`tools/glslcpp/typed_slice.json`, `include/noisemaker/glsl_types.hpp`,
`src/typed_generated/*`, `include/noisemaker/generated/catalog.hpp`,
`tests/test_typed_generator.py::Task30ExtrudeBvec2RelationalReductionTests`,
`tests/test_generated_kernels.cpp` (Task30 sections), `tests/test_glsl_types.cpp`.

All commands below were run against the live tree at
`.` (read-only). Native build was
done into a fresh scratch directory, `docs/port-engineering/task30-review/build2`.
No `git` commands were run; no files under `noisemaker-for-cpp` were modified.

## Verdict

**ACCEPT**, with one **Important** non-blocking follow-up required (item I-1
below) before the pattern in this task is reused as a template. No Critical
findings. Every capability-boundary, independence, native-anti-vacuity, and
parity claim in the implementation report and parity evidence was
independently reproduced from the live tree, not merely re-read from the
report. The one significant gap found (I-1) is a test-diagnostic-quality
issue, not a live capability leak or a wrong render — the actual safety
properties it claims to cover were separately confirmed to hold by direct
probing outside the flawed harness.

## Findings summary

| Severity | Count |
|---|---|
| Critical | 0 |
| Important | 1 |
| Minor | 1 |
| Nit | 2 |

- **I-1**: The "47 single-axis structural mutations reject at all three
  authorities" Python test does not exercise the profile's own
  closure-identity verification logic at all — every one of the 47 axes is
  caught by an earlier, generic program-identity/hash gate, not by the
  node-level closure checks the module exists to enforce. This is exactly
  the risk class the accepted brief pre-flagged and asked to be disclosed;
  the implementation report and parity evidence do not disclose it.
- **M-1**: `emit_typed_cpp.py:759` admits `bvec2` type lowering scoped to
  "an Extrude proof is live for this program" rather than to the two exact
  authenticated node identities, unlike every other Extrude admission gate
  in the same files. Currently inert (unreachable given the profile's own
  guarantees), but a real deviation from the brief's stated identity-scoping
  principle.
- **N-1**: GLSL `&&`/`||` do not short-circuit; the emitted C++ does. No
  observable effect here (side-effect-free RHS), but worth a one-line note.
- **N-2**: `filter/edge:edge` is rejected long before it would reach its
  `bvec3`/`greaterThanEqual` code (line 78), at an unrelated "unsupported
  global declaration" gate — a clarification, not a defect.

---

## 1. Capability leak check

**Verified absent from every global table**, by direct interpreter probe
against the live modules (not by reading source only):

```
$ python3 -c "... "
44 ('bool', 'float', ..., 'sampler2D', 'void')   # APPROVED_TYPES, len 16, no bvec2
bvec2 in APPROVED_TYPES -> False
bvec2 in emit_typed_cpp._TYPES -> False
'all'/'lessThanEqual' in emit_typed_cpp._BUILTIN_NAMES -> False, False
```
(`tools/glslcpp/generate_typed_slice.py:188-213`, `tools/glslcpp/emit_typed_cpp.py:80-113`)

**Leak-control programs, re-verified live**, not copied from the report:

```
filter/waves:waves -> REJECTED: filter/waves:waves:41:9: unsupported builtin any
```
Matches the report's claimed message exactly (`tools/glslcpp/corpus/.../filter/waves/waves.glsl:48`,
`74` use `any(notEqual(...))`).

```
filter/edge:edge -> REJECTED: filter/edge:edge:19:1: unsupported global declaration
```
`filter/edge/edge.glsl:78-80` does contain `bvec3 centerOnSide = ... greaterThanEqual(...)`
and `bvec3 crossing = bvec3(...)`, but the validator rejects `edge` at an
earlier, unrelated gate (an unsupported global declaration) before ever
reaching that line. **Correction to my own task framing, not a defect**:
the "edge needs bvec3/greaterThanEqual and is still rejected" claim is true
in outcome (edge is rejected) but the mechanism is unrelated to Task 30's
gates — edge cannot currently be used to test bvec3/greaterThanEqual leakage
specifically, because it never reaches that code path regardless of Extrude.

**Two independent authorities, both identity-scoped by object identity, not
by type name or program key alone**:
- Validator: `generate_typed_slice.py:1605-1613` (`reject_type`) — admits
  `bvec2` only if `any(value is item for item in authorized_extrude_relationals)`.
- Validator builtin gate: `generate_typed_slice.py:1957-1966` — admits
  `all`/`lessThanEqual` only if `value is item` for one of the four
  authenticated nodes; unconditionally raises otherwise.
- Emitter builtin gate: `emit_typed_cpp.py:1297-1307` — same identity check,
  independently re-derived (see §3).

No other corpus program can reach either gate: both checks are scoped to
`program.key == EXTRUDE_KEY` at the point `authorized_extrude_relationals`/
`authorized_extrude_reductions`/`authorized_extrude_proof` are populated
(`generate_typed_slice.py:1413-1437`, `emit_typed_cpp.py:224-249`); for every
other program those collections are empty and the identity checks trivially
fail closed. Confirmed by directly running the validator against `waves`
and `edge` above with no Extrude profile in scope.

## 2. Is the `used.add` skip sound?

**Verified TRUE, and verified necessary, not merely tidy.**

`src/typed_generated/typed_manifest.json` really does carry one identical
44-entry `capabilities` list on every one of its 130 program rows:

```
$ python3 -c "... distinct capability-list values across rows: 1 ... len 44"
```

This is because the per-row `"capabilities"` field is literally
`slice_spec["capabilities"]` — a copy of the whole `APPROVED_CAPABILITIES`
tuple pulled from `typed_slice.json`
(`generate_typed_slice.py:2352`, confirmed by reading the call site), not a
per-program "what did this program actually use" set. So growing the global
vocabulary by one entry would indeed change every row's `output_sha256`
(computed over the whole regenerated file) and thus every frozen historical
reconstruction hash — the report's stated rationale is accurate.

More importantly, the skip is not optional bookkeeping: `used` (the
per-program *actually-used* set, distinct from the manifest field above) is
checked at `generate_typed_slice.py:2180-2181` via
`missing = sorted(used - set(capabilities))`, raising `GeneratorError` if
non-empty. Since `all`/`lessThanEqual` are not in `APPROVED_CAPABILITIES`,
had they NOT been excluded from `used.add` at line 1981
(`if value.callee not in {"round", "all", "lessThanEqual"}: used.add(...)`),
`validate_capabilities` would immediately reject the *correct* Extrude
program with "missing capabilities all, lessThanEqual" — i.e., the skip is
load-bearing for the feature to work at all, not just for manifest-row
identity. Test `test_task30_capability_and_type_vocabulary_are_identity_scoped_not_widened`
(`tests/test_typed_generator.py:14581-14624`) makes this same point
behaviorally and I reran it fresh (passed, see §9).

No accounting hole: the skip only fires for `all`/`lessThanEqual`, and both
are already gated by the identity checks in §1 before the `used.add` line is
ever reached, so nothing un-authenticated can ride along.

## 3. Validator/emitter independence

Confirmed by reading the control flow, not just the tests: the emitter's
constructor calls `authenticate_extrude_bvec2_relational_reduction` directly
(`emit_typed_cpp.py:240-246`, comment: "Independent re-authentication. The
emitter never trusts the validator's result or a supplied proof object."),
using only its own constructor arguments (`self.program`, `self.source_hash`,
`self.extrude_bvec2_relational_reduction_profile`) — there is no code path
by which a validator-produced proof object reaches the emitter.

I ran `test_task30_validator_and_emitter_authenticate_independently_without_trusting_each_other`
fresh (§9, passed) which directly exercises: no profile carrier, wrong
profile string, and a foreign program carrying the identical closure —
against the emitter with the validator never invoked, and symmetrically
against the validator with the emitter never invoked. It also monkeypatches
`APPROVED_TYPES` to admit `"bvec2"` globally and confirms the *foreign*
program still fails (because admission is identity-scoped, not type-scoped),
restoring the tuple in a `finally` and asserting byte-identical restoration.

One gap versus the brief: the brief's own design-verification section
describes a **dual** widening probe — monkeypatching `APPROVED_CAPABILITIES`,
`_BUILTINS`, `_BUILTIN_NAMES`, **and** `_TYPES` together, and showing the
validator's `reject_type` still independently rejects even when the
emitter's tables are widened. The shipped regression test only monkeypatches
`APPROVED_TYPES`. This is not a defect — I independently reproduced the
stronger form of the probe myself and it holds — but the permanent test
suite carries a narrower regression net than what the design verification
actually established. Not required for acceptance; worth folding in
opportunistically.

## 4. Mutation barriers — vacuity check (Important finding I-1)

The Python test claims 47 single-axis mutations "each asserting its own
precondition before rejection is checked." I ran all 47 axes directly
against `authenticate_extrude_bvec2_relational_reduction` (reproducing the
exact axis table from `tests/test_typed_generator.py:14421-14479`,
scratch script at `docs/port-engineering/task30-review/scratch` — not
committed, per instructions):

```
COARSE (caught by "source, define, function, whole-program, or interface mismatch"): 46
  [normalized-source, raw-source, body-status, define-name, define-order,
   struct-presence, uniform-block-presence, loop-count, loop-depth,
   loop-product, loop-charge, call-graph-cycle, resource-*, function-count,
   function-order, main-*, for-*, block-*, decl8-*, decl9-*,
   top-all-*, top-rel-*, side-all-*, side-rel-*]   (46 of 47 axes)

FINE-GRAINED (closure-identity logic reached): 0

OTHER: 1 axis ("program-key") caught by a SEPARATE, equally coarse,
  earlier check: "selected key and exact caller source hash required"
  (generate_typed_slice.py / profile module, the THIRD check in the
  function, before the giant combined hash check).
```

So **zero of the 47 axes** ever reach the module's own closure-specific
logic — the `located` node walk, the "closure node identity mismatch",
"reduction does not immediately consume its relational", "bvec2 value
escapes its immediate reduction", "relational parent is not its paired
reduction", or "closure ancestry kind/span mismatch" checks
(`extrude_bvec2_relational_reduction_profile.py:222-268`). The reason is
structural: `_whole(program)` hashes nearly every field of `TypedProgram`,
including `program.functions` in full, so *any* mutation anywhere in the
function tree changes the coarse hash and is rejected there first, before
the interesting node-identity logic ever runs. Because the validator and
emitter both call this same profile function as their first step for the
Extrude program, this collapse is not specific to the "profile" layer of
the 3-authority test — it propagates identically to the "validator" and
"emitter" subtests too (same underlying function, same first-hit check).

This is precisely the risk class the accepted brief names explicitly under
"Required: avoid the Task 26 ... vacuous mutation-harness class" and asks to
be assessed with: *"assess whether the test distinguishes node-level
failures from coarse hash failures, and say so plainly."* It is a
**different flavor** from Task 26's defect (Task 26's modes silently shared
a code path and passed by construction — a false-positive on "distinct
behavior"; here, every rejection is real — nothing passes when it shouldn't
— but the claimed per-axis diagnostic distinction, and the actual exercise
of the module's four hand-written closure-identity checks, does not happen).
Neither the implementation report nor the parity evidence discloses this;
both describe the 47 mutations only as proof that each "candidate must
assert its own structural precondition before rejection is checked," which
is true of the *precondition* assertion (`assertNotEqual(exact, candidate)`,
genuinely checked) but silent on the *rejection mechanism* being uniform.

**Practical consequence**: if a future edit weakened or removed any of the
five closure-identity checks in `authenticate_extrude_bvec2_relational_reduction`
(e.g. changed an `is not` identity comparison to a weaker equality, or
dropped the ancestry-span check), no test in this suite — Python or native —
would currently catch the regression, because no test constructs an input
that reaches that code while keeping the coarse whole-program hash intact.
I did not find a way to construct such an input without deliberately
engineering object-identity mismatches with byte-identical `repr()` (e.g., a
hand-forged tree using a distinct-but-content-equal clone spliced into one
child slot); doing so is possible in principle but was out of scope to
build for this review. I flag this as **Important** rather than **Critical**
because I independently confirmed, by means outside this test (direct
`reject_type`/builtin-gate reading in §1, direct emitter probing in §3,
native fixture reproduction in §6, fresh full test/build runs in §9), that
the actual admitted capability surface is correctly narrow today — the gap
is in regression coverage of the *reasoning*, not in present-day behavior.

**Fix recommendation**: add at least one Python test case per fine-grained
check that swaps in a distinct-but-repr-identical clone object at the
specific slot each check guards (e.g., a rebuilt `lessThanEqual` clone with
identical fields substituted into `all.children[0]` while the "official"
located-relational stays the original object), so each of the five
closure-identity checks has at least one negative test that is provably
caused by that specific check and not by the coarse gate. This does not
block acceptance of Task 30 itself but should happen before this profile is
used as a template for a future task (the brief's own stated intent).

## 5. Native anti-vacuity

Read `tests/test_generated_kernels.cpp:9111-9401` in full. Confirmed:

- Five modes (`exact_inclusive_all`, `inclusive_any`, `strict_exclusive_all`,
  `strict_exclusive_any`, `mirrored_inclusive_all`), each its own `switch`
  arm with its own comparison expression and its own reduction loop; no
  arm falls through to another, no `default` (an out-of-range mode value
  throws `std::invalid_argument`, verified live in §9).
- The 28-wide `task30_relational_signature` payload
  (`test_generated_kernels.cpp:9283-9300`) is built only from
  `reduced` (7), `lanes` (14), and six named counters (`le_calls`,
  `all_calls`, `strict_calls`, `ge_calls`, `and_reduce_iterations`,
  `or_reduce_iterations`, `rows_processed` = 7) = 28 fields exactly. It
  excludes `mode`, `name`, and `arm_dispatches` (the one-hot dispatch
  array) — confirmed by reading the struct and the signature builder; none
  of those three fields appear in the signature computation.
- Pairwise-uniqueness assertion (`REQUIRE(signatures[left] != signatures[right])`
  for all 10 pairs) plus explicit per-row divergence assertions
  (`witnesses[4].reduced[2] != witnesses[0].reduced[2]`, etc. at rows 2/3/5)
  are genuine content-based divergence checks, not just distinct dispatch
  IDs.
- Mode 4 ("mirrored") is source-verified to never call `lessThanEqual` in
  its arm body (test strips comments first, then asserts the compacted arm
  text excludes the token — `test_typed_generator.py:14884-14890` — I
  independently reread the arm source at
  `test_generated_kernels.cpp:9243-9265` and confirmed it computes
  `rx <= lx` inline, no call to the shared helper).

I built the project fresh (Debug, `-Wall -Wextra -Wpedantic -Werror`) into a
new directory and ran the full native suite:

```
$ cmake -S noisemaker-for-cpp -B task30-review/build2 -DCMAKE_BUILD_TYPE=Debug
$ cmake --build . -j8   # EXIT=0, no warnings
$ ./noisemaker-cpu-tests | grep -c PASS   # 148
$ ./noisemaker-cpu-tests | grep -v PASS   # (empty)
$ ./noisemaker-cpu-tests | grep -i task30
PASS typed_task30_extrude_public_oracles_are_exact_repeatable_finite_and_nonmutating
PASS typed_task30_extrude_binding_abi_rejects_every_missing_and_wrong_input_and_accepts_extras
PASS typed_task30_direct_relational_switch_executes_five_distinct_fail_closed_modes
PASS typed_task30_lessThanEqual_and_all_direct_lane_and_reduction_truth_tables
```

148/148 pass, matching the report's claimed native count exactly (144→148,
+4).

I also independently confirmed the `requires(N == 2)` constraint is a real
compile-time wall, not merely untested, by compiling a standalone
`lessThanEqual<3>`/`all<3>` instantiation:

```
error: no matching function for call to 'lessThanEqual'
note: candidate template ignored: constraints not satisfied [with N = 3]
note: because '3UL == 2' (3 == 2) evaluated to false
```
(`include/noisemaker/glsl_types.hpp:244-258`)

## 6. Parity — independently re-derived

`future-precompute/task30/extrude-oracles.json` hashes to
`bf8c4c165846eb116d2afb4f78b7c1de78f70f104ac714e09395ceffbe51c758`, matching
every citation in the report/evidence.

**Eligibility claim verified from the raw JSON**, not from prose: the oracle
carries 6 `cases`; exactly 3 have
`defines == {"EXTRUDE_TYPE": 0, "DEPTH_SOURCE": 0}`
(`blocks-default-luminance-solid`, `blocks-depth-zero-window`,
`blocks-max-depth-luminance-window`); the other 3
(`blocks-random-solid-tiled`, `pyramids-luminance-solid`,
`pyramids-random-window-tiled`) use `EXTRUDE_TYPE:1` and/or
`DEPTH_SOURCE:1`. `kTask30NativeCases` in the C++ test
(`test_generated_kernels.cpp:8895-8912`) contains exactly the 3 eligible
cases and I confirmed every field (width/height/phase/size/depth/
solidFront/f32_sha256/rgba8_sha256/finite_lanes/nonfinite_lanes and all 5
probe rows' `at_top_down_xy` + `f32_bits_le`) is a byte-for-byte
transcription of the oracle JSON's corresponding rows — I diffed them
programmatically, not by eye.

**Independent re-derivation, not trust of the baked constants**: I ran the
actual native test that renders through the real public binder
(`bind_filter_extrude_extrude` + `run_pass`) and computes SHA-256 against
these baked constants — `typed_task30_extrude_public_oracles_are_exact_repeatable_finite_and_nonmutating`
passed fresh in a from-scratch Debug build (§5/§9), which is a genuine
independent full-surface F32 SHA-256 re-derivation via C++ execution, cross
checked against the JS-oracle-derived JSON file I read separately in
Python. Both paths (C++ render, JSON oracle) agree.

**Divergence counts, recomputed directly from the oracle JSON**, not copied
from the brief:

```
top-lane-any     all-reduction         3/6
side-lane-any    all-reduction         2/6
top-strict-less  inclusive-relational  4/6
side-strict-less inclusive-relational  2/6
```
Matches the brief's claimed 3/6, 2/6, 4/6, 2/6 exactly.

I did not have access to `node`/the JS oracle generator or the
`noisemaker-for-cpu` JS repo in this session, so I could not rerun
`extrude_oracle_generator.mjs --check` myself; the JSON file's hash citation
is internally consistent across the report, evidence, brief, and the live
test-embedded oracle file, which is the strongest verification available
without that toolchain.

## 7. Historical integrity (highest-risk area)

Cross-checked against pre-Task-30 documents (`task-28-implementation-report.md`,
`task-29-implementation-report.md`), authored before Extrude existed:

- **Prior task-owned production files byte-identical to their frozen
  hashes**, confirmed by direct `shasum`, not by reading claims:
  - `tools/glslcpp/frontend/rotate_mat2_return_profile.py` (Task 28) live
    hash `a0ca34a312a0f610c9acb1f6b009ee534f52fc6e1eb1fe1fa2da707e8beba454`
    == frozen hash in `task-28-implementation-report.md:83`.
  - `tools/glslcpp/frontend/focus_blur_borrowed_sampler_profile.py`
    (Task 29) live hash
    `cc0f9333b3b3064d985276af0199720a2da68fd27d0328cac6d565bbee1076b5` ==
    frozen hash in `task-29-implementation-report.md:186`.
- **Task 29's frozen typed/public ordered-key hashes** (`c2561c5937ba5f11f5d2e86d729ff90b617aff738cb4de53dbf3cd8b76dbbff9`
  / `2325f8d06d182800af90cd1b0b67efe9d3058d3682f0ceb4d3f5168ff4af5e16`) match
  `task-29-implementation-report.md:24-25` exactly, and are reproduced by
  `test_task30_removing_only_extrude_regenerates_task29_outputs_byte_for_byte`
  (`tests/test_typed_generator.py:14719-14757`), which I ran fresh (passed,
  §9). That same test's `expected_task29` file-content hashes
  (`358847db3767...`, `01bfe3c139e8...`, `2d32511c858a...`) match
  `task-29-implementation-report.md:190-192` verbatim — i.e., the
  Task-29-minus-Extrude reconstruction reproduces Task 29's own frozen
  acceptance artifacts byte-for-byte, not a value invented to make the test
  pass.
- The reconstruction correctly subtracts only Extrude (129 keys after
  removal, hash `c2561c59...` — matches), consistent with "programs added
  after Task 29" being just this one task; there is no evidence any later
  program besides Extrude was folded in incorrectly.
- The other place the file references pre-Extrude counts
  (`Task29FocusBlurBorrowedSamplerTests`'s own history test at
  `tests/test_typed_generator.py:13366` area, updated to `(130, 132, 80, 212)`
  with a comment "Live current state (post-Task30)") queries
  `generate_typed_slice.load_slice(REPOSITORY)` — i.e. the *live* tree, not
  a frozen constant — so updating it to track Extrude's landing is correct
  maintenance, not tampering with a frozen historical assertion. I confirmed
  this class of assertion is architecturally different from the *profile
  module's own* frozen identity constants (`_WHOLE_SHA256`,
  `_FUNCTIONS_SHA256`, etc., which are per-profile and untouched, per the
  byte-identical file hashes above).

No evidence of an altered frozen hash anywhere I checked.

## 8. Other checks

- **`consumed_objects` cardinality (11)**: meaningful, not arbitrary. Traced
  the dedup logic (`extrude_bvec2_relational_reduction_profile.py:110-134`):
  main(1) + reductions(2) + relationals(2) + reduction_parents(2) + 4 unique
  statements out of 6 raw chain entries (the `for` and `block` ancestors are
  shared between the two closures; only the two `decl` ancestors differ) =
  11. The test additionally asserts `len({id(item) for item in
  proof.consumed_objects}) == 11`, i.e. genuine object-identity uniqueness,
  not just tuple length.
- **`requires(N==2)` enforcement**: genuinely enforced — see §5, reproduced
  independently.
- **Emitted C++ vs. GLSL semantics**: `topHit`/`sideHit` lowering
  (`src/typed_generated/typed_slice.cpp:3565-3566`) is a verbatim structural
  match to the source
  (`sources/filter/extrude/extrude.glsl:316-317`). One semantic nuance
  (N-1 below): GLSL `&&`/`||` are specified as evaluating both operands
  (no short-circuit), while C++ `&&` short-circuits; `sideHit`'s
  right-hand side (`all(lessThanEqual(abs(P - cellC), halfCell))`) has no
  side effects, so this produces no observable divergence in this program,
  but it is a latent hazard if this exact `(cond) && all(lessThanEqual(...))`
  lowering pattern is ever reused for an RHS with a side effect (e.g. a
  future profile that mixes counters into a relational branch).
- **M-1** (emitter `type()` scoping): see summary above;
  `emit_typed_cpp.py:759` checks `self.authorized_extrude_proof is not None`
  rather than `value is item for item in proof.relationals`, unlike the
  validator's equivalent gate (`generate_typed_slice.py:1611`), the
  emitter's own builtin-call gate (`emit_typed_cpp.py:1305`), and the
  emitter's post-emission completeness check
  (`emit_typed_cpp.py:1786`). Currently unreachable with a bvec2-typed value
  in practice: I traced every call site of `self.type(...)` in
  `emit_typed_cpp.py` and none of them can carry a `bvec2`-typed operand for
  this program, because the only two bvec2-valued expressions are consumed
  inline by the special-cased `all`/`lessThanEqual` string synthesis path
  (`emit_typed_cpp.py:1297-1315`), which never calls `self.type()` on the
  bvec2 operand itself — and the profile's own authentication guarantees no
  *other* bvec2 node can exist in an admitted tree (the "bvec2 value
  escapes its immediate reduction" check in §4). Recommend tightening for
  consistency and to remove the landmine, not blocking.

## 9. Fresh verification run (this session)

```
$ cmake -S noisemaker-for-cpp -B docs/port-engineering/task30-review/build2 -DCMAKE_BUILD_TYPE=Debug
$ cmake --build . -j8                                    EXIT=0, zero warnings (-Werror)
$ ./noisemaker-cpu-tests | grep -c PASS                  148
$ ./noisemaker-cpu-tests | grep -v PASS                  (none)
$ python3 tools/glslcpp/generate_typed_slice.py --check  "typed slice ok (130 programs)"  EXIT=0
$ python3 tools/glslcpp/check_corpus.py --check          "check_corpus: ok"               EXIT=0
$ python3 tools/glslcpp/check_semantics.py --check       "bodies ok (212 programs)"       EXIT=0
$ python3 tools/glslcpp/generate_kernels.py --check                                        EXIT=0
$ python3 -m unittest tests.test_typed_generator.Task30ExtrudeBvec2RelationalReductionTests -v
  ... 7 tests, OK, 111.352s
```

Did not rerun the full 34-minute Python discovery (per instructions); the
targeted Task 30 class (7/7) and the 4 Task 30 native tests plus the full
native suite (148/148) were run fresh instead, and a static count of
`def test_` across all four `tests/test_*.py` files totals exactly 193,
matching the report's "Ran 193 tests" claim without requiring the full run.

## File hash cross-checks performed (all matched frozen/report values)

- `future-precompute/task30/extrude-oracles.json` → `bf8c4c16...` (matches report/brief citation)
- `tools/glslcpp/frontend/rotate_mat2_return_profile.py` → `a0ca34a3...` (matches Task 28 frozen)
- `tools/glslcpp/frontend/focus_blur_borrowed_sampler_profile.py` → `cc0f9333...` (matches Task 29 frozen)

No hash mismatches found anywhere in this review.
