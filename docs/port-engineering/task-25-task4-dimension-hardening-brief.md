# Task 25 Task 4 output-dimension assertion hardening

Repository: `.`

Read first:

- `../POSTMORTEM-2026-07-14-NOISEMAKER-FORCE-PUSH.md`
- `../AGENTS.md`
- `docs/port-engineering/task-25-task4-custom-comparer-brief.md`
- `docs/port-engineering/task-25-task4-custom-comparer-report.md`
- `docs/port-engineering/task-25-task4-custom-comparer-review.md`

Address the review's sole Minor finding only. In the six-case native Lens/Prism public-factory oracle test in `tests/test_generated_kernels.cpp`, add explicit output `width()` and `height()` assertions for every independently rendered surface (`first`, `second`, and `direct`) against the fixture dimensions. Preserve the existing element-count, hash, probe, repeatability, binder identity, input immutability, finiteness, and ABI checks. Do not change production code, frozen oracle values, corpus sources, generated outputs, or any unrelated test.

Run a fresh Debug build if necessary and the focused native Task 25 oracle test/full native executable sufficient to prove the assertion compiles and all six cases remain exact. No Git commands, commits, branches, worktrees, PRs, pushes, publication, or repository creation.

Write `docs/port-engineering/task-25-task4-dimension-hardening-report.md` with the exact lines changed, command/results/timing, final `tests/test_generated_kernels.cpp` SHA-256, and self-review. Return only status, one-line validation, and concerns.
