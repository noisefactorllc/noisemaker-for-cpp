# Task 25 Task 1 independent review

Date: 2026-08-11

## Verdict

**APPROVED.** The final Task 1 profile implementation and focused tests comply
with the amended brief and approved design. The first review found two exact
gaps—unauthenticated optional proof carriers and a main-only index census—and
the review-fix round closes both with direct RED/GREEN evidence. I found no
remaining material scope, correctness, authority, or test-quality defect on
the final reviewed bytes.

## Reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| amended Task 25 brief | `193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2` |
| approved implementation design | `9900749a387a30c6f1db0e584d2382288d44c2f3b0d5670f3b1968f1312c357b` |
| final Task 1 report | `7d1b4c328d9aab5833271d130d1c3d2e7018b1ce31a1560a2e865c4733aae7b1` |
| profile implementation | `36445e5bed63a06648e2820ae29d76ea438fe33c27756c0db3f0b0c6ad976e4a` |
| current generator test file | `2a41a82cfd83c2daf2c133a04efc062d0919dc47f616a95c3258b583b1a0bcb7` |

Review scope was limited to
`tools/glslcpp/frontend/literal_vec3_lane_index_profile.py` and the two Task 25
profile tests at the end of `tests/test_typed_generator.py`.

## Exact profile and sentinel authority

- `PROFILE`, `LENS_KEY`, `PRISMATIC_KEY`, and `KEYS` are exact.
- The 11 frozen paths are verbatim tuples in brief order: Lens 8 and
  Prismatic 3. Every `eN` component retains and validates its following zero
  expression-root sentinel rather than normalizing it away.
- All raw/normalized byte counts and hashes, main IDs/body counts and
  pre/post hashes, function-tuple hashes, whole-program hashes, unchanged
  interface hashes, base symbol IDs, spans, lane/role labels, pre/post site
  hashes, and profile-tuple hashes match the binding brief.
- The profile tuple uses exact `repr` serialization, tuple paths, `{}`, the
  frozen raw hash, exact row order, and roles spelled `write`/`read`.
- Each pre site is re-proved as a scalar-float lvalue index of the direct
  writable main-local `vec3 hsv` by an int rvalue literal. Write/read role is
  recomputed from the actual parent and child ordinal.

The whole-program pre index census is exactly the resolved ordered 8/3 sites;
standalone post authentication requires zero index nodes across every
function. Aggregate roles are six writes/five reads and lane incidence is
`7/3/1` for lanes `0/1/2`.

## Observable locks and rewrite behavior

Pre and post authentication independently lock the selected key/carrier,
caller hash, retained raw and normalized source, empty defines, analyzed body,
main/function/whole/interface state, declarations/resources/builtins through
the frozen fingerprints, exact zero-loop acyclic proof, exact sites, and exact
profile tuple.

The four optional proof fields omitted by the brief's frozen whole-program
serialization are now explicitly required to be `None` at both standalone
boundaries:

- `fixed_nine_table_proof`
- `fixed_grid_counter_store_proof`
- `fixed_array_in_parameter_proof`
- `fixed_affine_centers13_proof`

Transition authentication additionally requires those fields to remain equal
and object-identical. This closes the initially reproduced proof-injection
acceptance and ensures only the fixed lane rewrite changes.

Application authenticates pre, creates an identity-keyed replacement map, and
walks `main` once. It replaces only the authenticated sites using the exact
`dataclasses.replace` shape, reports exactly 8 or 3 changes, retains each base
object by identity, creates one new main/function tuple/program, and preserves
all non-main functions by identity. Reapplication rejects.

The transition authenticator holds pre and post together and requires retained
base `is` identity plus exact dataclass replacement value. Standalone post
authentication deliberately uses only structural value authority: a deep
dataclass-equal reconstruction is accepted there, while transition rejects it
because process-local base lineage was not retained. This exactly implements
the amended identity split.

## Tests and adversarial verification

The positive focused test exercises real parsed corpus trees and all four
public functions. It freezes literal path order and profile hashes, verifies
8/3 and aggregate role/lane counts, main-only rewrite, non-main identity,
transition base identity, post structural-clone acceptance, transition clone
rejection, and reapplication rejection.

The adversarial focused test independently injects each optional proof at pre,
post, and transition boundaries and requires rejection. It also inserts an
index in a non-main function, then deliberately rebases the internal function,
whole-program, and profile hashes; rejection therefore proves the independent
whole-program census is load-bearing rather than merely shadowed by a frozen
digest.

Fresh independent controller results on both programs:

```text
Ran 2 tests in 0.491s
OK
Lens: 12/12 proof-boundary injections rejected; rebased non-main index rejected
Prismatic: 12/12 proof-boundary injections rejected; rebased non-main index rejected
```

The Task 1 report records the original RED import failure before module
creation and a second review RED with 13 missing rejections before the fix;
the corresponding focused GREEN runs are present. This is adequate TDD
evidence for the scoped foundation.

## Scope

The profile introduces no typed-IR field, proof dataclass, schema field,
registry, side table, runtime helper, vector subscript, dynamic lane route, or
generic indexing capability. Task 1 touched only the authorized new helper and
Task 25 test block. Loader, driver, validator, emitter, slice, generated, and
native work correctly remain later tasks.

No repository file was edited and no Git operation was used during this
review.
