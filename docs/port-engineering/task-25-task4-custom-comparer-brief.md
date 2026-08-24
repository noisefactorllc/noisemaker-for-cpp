# Task 25, Task 4 amendment: Lens custom comparer

## Context

The native Task 25 oracle is frozen in `tests/test_generated_kernels.cpp` and `tests/test_typed_generator.py`. Prism is pixel-exact. All four Lens cases fail only because canonical `noisemaker-for-cpu` lowers `color.rgb == vec3(1.0)` to a `PooledFloat32Array`, and JavaScript treats that object as truthy in the conditional. Native C++ currently uses ordinary `Vec::operator==`, which can be false and selects the tint arm.

Read first:

- `../POSTMORTEM-2026-07-14-NOISEMAKER-FORCE-PUSH.md`
- `../AGENTS.md`
- `docs/port-engineering/task-25-task4-blocker-report.md`
- `docs/port-engineering/task-25-lens-tint-compat-audit.md`

## User decision

Implement a custom comparer function. Do not rewrite the conditional to a constant or weaken/replace the pixel oracle.

## Required behavior

1. Add a clearly named C++ comparer representing canonical JavaScript vector-equality-result truthiness. It must return true for both equal and unequal vector operands, because the canonical comparison result is an allocated typed-array object and all such objects are truthy. The name and comments must make this compatibility behavior explicit; do not misleadingly present it as mathematical vector equality.
2. Route only the authenticated `classicNoisedeck/lensDistortion:lensDistortion` tint predicate at source line 273 through that comparer. Preserve the surrounding `mix(color.rgb, ..., alpha * 0.01)` evaluation exactly.
3. Do not alter global `Vec::operator==`, other programs, other Lens predicates, or general conditional/equality lowering.
4. The routing must fail closed on program key, raw and normalized source hashes, interface/tree shape, exact target/predicate/arms/span, and unexpected extra/missing sites. It must coexist with the existing Lens literal-vec3 lane profile in a deterministic documented order.
5. Generated manifest/projection metadata must explicitly identify the custom comparer compatibility profile. Regenerate checked-in outputs only through the canonical generator.
6. Keep the frozen Task 25 JSON/oracle values unchanged. The four Lens and two Prism native cases must match exact F32 and RGBA8 hashes/probes, repeatability, input immutability, dimensions, and finiteness.
7. Add negative mutation tests for the comparer routing and a direct C++ unit test showing equal and unequal vectors are truthy under this named compatibility comparer while ordinary vector equality remains unchanged.

## TDD and validation

- Start by adding the smallest real test for the missing comparer/routing and run it to demonstrate the expected RED failure before production edits.
- Implement the minimal production change, then rerun the focused test to GREEN.
- Run the full Task 25 Task 1-4 validation, relevant historical compatibility/generator suites, canonical regeneration check, Python compile checks, debug build, and CTest targets affected by the change.
- Do not claim parity from tolerances: all frozen hashes/probes must be exact.

## Scope and safety

- No Git commands, commits, branches, worktrees, PRs, pushes, publication, or repository creation.
- Preserve unrelated work and generated-oracle artifacts.
- Do not edit canonical corpus source GLSL.
- Do not add planning/review artifacts inside the repository.

## Report

Write `docs/port-engineering/task-25-task4-custom-comparer-report.md` containing: files changed, RED command/output, implementation design, source/tree locks, generated hashes/counts, every validation command/result/timing, exact six-case parity result, self-review, and SHA-256 hashes for the report and touched non-generated source/test files. Return only status, one-line validation summary, and concerns.
