# Task 29 native Focus Blur test report

Date: 2026-08-12

## Scope

Changed only `tests/test_generated_kernels.cpp`.
No production, generator, Python, build-system, Git, branch, worktree, or PR
operation was performed.

## TDD evidence

RED was observed after adding the selected-path resource-count contract:

- `Task29Counters` had no `texture_reads` member.
- `Task29Counters` had no `texture_size_queries` member.
- `cmake --build build-task29-debug --target noisemaker-cpu-tests -j4`
  failed at the two new assertions with those exact missing-member errors.

The first implementation compile then exposed a missing direct include for the
real sampler API (`noisemaker::sample_nearest_bottom_left`). Adding only
`noisemaker/sampler.hpp` resolved that dependency.

## Implemented native contract

- Preserved all six frozen public Focus Blur fixtures and their literal F32,
  RGBA8, dimensions, finite-lane, and five-probe expectations.
- Exercises delayed binding after inner-scope `Bindings` destruction, direct
  factory binding, public catalog binding, and a repeated direct render.
- Proves input immutability, stable storage addresses, fresh output storage,
  and one real shared `Surface` address for the alias fixture.
- Rejects missing and wrong types for all nine bindings and accepts unrelated
  extra uniform/sampler bindings.
- Replaced the partial direct harness with `Task29DirectMode`, eight explicit
  no-default switch arms, per-arm execution counters, post-switch invalid-ID
  rejection, and exact declared/handled/observed ID equality.
- The alias arm passes the same actual `Surface` object as both input and tex;
  no alias boolean is fabricated.
- The value-copy arm creates two independent `Surface` clones, reads those
  exact clone objects through both the direct mix and selected Focus path, and
  proves 2 allocations / 96 copied F32 lanes / exact copied contents / no
  original-object alias.
- Mutable and nullable negative arms execute an actual write expression and
  actual null checks/dereferences, respectively.
- Scene/depth source roles, aliasing, ownership, null, stable-address, and copy
  witnesses are derived from executed object addresses and bytes.
- Exact counters are asserted for all eight modes. Each non-null mode performs
  one depth sample, 64 scene samples, and two alpha-source samples through the
  real sampler API: 67 texture reads and, independently, 67 size queries.
- All eight semantic structural signatures are pairwise unique. Their payload
  excludes mode ID, name, acceptance, numeric mix result, resource checksum,
  and the one-hot per-mode dispatch array.
- Invalid enum 8 rejects with exact text `invalid direct ABI mode 8`.
- Stable parser markers are `TASK29_NATIVE_ORACLE_TABLE_BEGIN/END`,
  `TASK29_DIRECT_ABI_HARNESS_BEGIN/END`, and
  `TASK29_DIRECT_ABI_SWITCH_BEGIN/END`.

## Verification

Warnings-as-errors build:

```text
cmake --build build-task29-debug --target noisemaker-cpu-tests -j4
[100%] Built target noisemaker-cpu-tests
```

Native executable: exit 0. All tests passed, including:

```text
PASS typed_task29_focus_blur_public_oracles_are_exact_repeatable_finite_nonmutating_and_lifetime_safe
PASS typed_task29_focus_blur_binding_abi_rejects_every_missing_and_wrong_input
PASS typed_task29_direct_borrow_switch_executes_eight_distinct_fail_closed_modes
PASS typed_task29_selected_focus_path_executes_sixty_seven_reads_and_size_queries
```

CTest:

```text
ctest --test-dir build-task29-debug --output-on-failure
1/1 Test #1: noisemaker-cpu-tests ... Passed
100% tests passed, 0 tests failed out of 1
```

Final owned-file SHA-256 at handoff:

```text
6ce02513437826a125e25f5fd7fc4f3b980203c49205184ecff6d9a44ca07967  tests/test_generated_kernels.cpp
```
