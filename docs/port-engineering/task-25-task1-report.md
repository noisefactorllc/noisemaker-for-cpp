# Task 25, Task 1 profile report

## Scope

Implemented only the closed literal Vec3 lane profile foundation in:

- `tools/glslcpp/frontend/literal_vec3_lane_index_profile.py`
- `tests/test_typed_generator.py`

No loader, generation driver, validator, emitter, slice, generated, native, or
Git work was performed.

## Frozen input verification

Verified before editing:

```text
193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2  task-25-brief.md
9900749a387a30c6f1db0e584d2382288d44c2f3b0d5670f3b1968f1312c357b  task-25-implementation-design.md
```

The parsed corpus matched the frozen two-key raw/normalized source hashes,
function/whole/interface identities, and site hashes.  The locked census is
Lens 8 and Prismatic 3; aggregate roles are six writes/five reads and lane
incidence is 0/1/2 = 7/3/1.

## RED evidence

After adding the focused test and before creating the module, this command was
run:

```sh
python3 -m unittest tests.test_typed_generator.TypedGeneratorTests.test_task25_literal_vec3_lane_profile_authenticates_and_rewrites_exact_sites
```

It failed as intended:

```text
ModuleNotFoundError: No module named 'tools.glslcpp.frontend.literal_vec3_lane_index_profile'
Ran 1 test in 0.048s
FAILED (errors=1)
```

## GREEN evidence

After the minimal profile implementation, the same command first passed in
1.579 seconds and passed again in the final verification in 1.840 seconds:

```text
Ran 1 test in 1.840s
OK
```

The test asserts the four public functions through real parsed corpus trees;
literal frozen path order and both per-key profile tuple digests; 8/3, 6/5,
and 7/3/1 census totals; one immutable main-only rewrite; retained pre-base
object identity at the transition boundary; preserved non-main object identity;
reapplication rejection; post authentication of a deep dataclass-equal
reconstruction; and transition rejection for that reconstruction because its
bases are no longer object-identical.

## Implementation notes

The profile resolves the brief's literal path grammar directly.  Its `eN`
component is followed by the frozen zero expression-root marker, which is
validated rather than removed or normalized.  Pre/post authenticators each
check the selected key/carrier/source/hash/interface/loop/call-graph/site
authority independently.  Application authenticates pre, performs one main
walk replacing only the eleven authorized nodes, and authenticates the exact
transition and post tree.

## Concerns and deliberate boundary

This Task 1 implementation intentionally has no loader, driver, capability
validator, or emitter plumbing.  Those later boundaries therefore do not yet
consume the profile carrier; Task 2 must add them without broadening the
profile or introducing generic vector indexing.

## Review-fix round 1: proof carriers and whole-program census

### RED evidence

Before the correction, this focused adversarial test was run:

```sh
python3 -m unittest tests.test_typed_generator.TypedGeneratorTests.test_task25_literal_vec3_lane_profile_rejects_proof_injection_and_nonmain_indexes
```

It failed as intended in 0.565 seconds with 13 `ValueError not raised`
failures: each of the four optional proof fields was accepted at the pre,
post, and transition boundaries, and an injected `index` in a non-main
function was accepted after the test rebased only the pre function, whole, and
profile hashes.  This demonstrated that the old main-only census, rather than
an independent whole-program census, was load-bearing.

### GREEN evidence

The profile now requires all four optional proof carriers to be exactly `None`
in standalone pre/post authentication, preserves each carrier by equality and
object identity across transition, and performs its index census across every
function body.  The original and adversarial focused tests passed together:

```sh
python3 -m unittest tests.test_typed_generator.TypedGeneratorTests.test_task25_literal_vec3_lane_profile_authenticates_and_rewrites_exact_sites tests.test_typed_generator.TypedGeneratorTests.test_task25_literal_vec3_lane_profile_rejects_proof_injection_and_nonmain_indexes
```

```text
Ran 2 tests in 0.646s
OK
```
