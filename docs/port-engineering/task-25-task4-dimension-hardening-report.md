# Task 25 Task 4 output-dimension assertion hardening report

Date: 2026-08-11  
Repository: `.`  
Status: COMPLETE

## Scope and result

Addressed only the review's Minor finding in the six-case native Lens/Prism
public-factory oracle. No production code, generated output, frozen oracle
values, corpus source, or unrelated test was changed.

## File changed

- `tests/test_generated_kernels.cpp`

## Exact changed lines

Inserted immediately after the three independent rendered surfaces are created
in `typed_task25_public_factory_oracles_are_exact_repeatable_finite_and_nonmutating`:

```cpp
REQUIRE(first.width() == fixture.width);
REQUIRE(first.height() == fixture.height);
REQUIRE(second.width() == fixture.width);
REQUIRE(second.height() == fixture.height);
REQUIRE(direct.width() == fixture.width);
REQUIRE(direct.height() == fixture.height);
```

The final source locations are `tests/test_generated_kernels.cpp:4239-4244`.
These assertions retain all existing element-count, F32/RGBA8 hash, probe,
repeatability, direct-vs-public-factory, input-immutability, finiteness,
binder identity, and ABI checks.

## Validation

Fresh Debug rebuild after the test edit:

```text
/usr/bin/time -p cmake --build build-task18-debug --target noisemaker-cpu-tests --parallel
```

Result: exit 0. `tests/test_generated_kernels.cpp` was recompiled and
`noisemaker-cpu-tests` was relinked. Observed wall time: 28.5s.

Full native executable through CTest:

```text
ctest --test-dir build-task18-debug --output-on-failure
```

Result: exit 0; `1/1 Test #1: noisemaker-cpu-tests ... Passed 5.63 sec`;
`100% tests passed, 0 tests failed`; total real time 5.65s. This executable
includes the six-case Task 25 native oracle, so all four Lens and two Prism
cases passed their existing exact F32/RGBA8 hash and probe assertions together
with the new output dimensions.

## Final digest

```text
8fc8674a1029e9161112224ced50c3fb11d2e8b26be0a51070b7191c7bb7f296  tests/test_generated_kernels.cpp
```

## Self-review

Confirmed the six additions assert `width()` and `height()` for every
independently rendered surface (`first`, `second`, and `direct`) against the
fixture dimensions. They are positioned before any output-byte comparisons,
and no existing assertion was removed or altered. No Git command, commit,
branch, worktree, PR, push, publication, or repository creation was
performed.
