# Task 29 Python test report

## Scope

- Owned file: `tests/test_typed_generator.py`
- No Git operations, branches, worktrees, pull requests, or edits outside the owned test file.
- Added a custom parser/comparer that authenticates the executable C++ oracle table, direct-mode enum/name/ID declarations, switch arms, witness counters, semantic signature, alias/copy implementation, and invalid-mode guard.

## TDD record

The initial Task 29 group failed before the profile and native harness converged: the owned-object census was 17 instead of 25, the protected-coordinate candidate set collapsed to 88 instead of 89, an equal reconstructed parent was incorrectly treated as a negative, one branch-source mutation was a no-op, and the generated sample-count expectation was wrong. The focused closure test was kept red while the candidate construction was repaired. The executable parser then exposed two independent comparer defects during exhaustive mutation: hexadecimal literals ending in `f` were being mistaken for floating-point suffixes, and the authenticated span did not include the complete harness-end marker line. A final focused run caught and corrected the mutable-reference assertion so that `const Surface&` is not classified as mutable.

## Final coverage

- 7 Task 29 Python test methods.
- Exact accepted profile owns 25 unique candidate-derived AST objects, including the helper, both sampler parameters, four helper sampler uses, both calls and parents, the conditional/predicate/branches, complete statement ancestry, four texture sites, and four texture-size sites.
- 89 unique one-coordinate mutations with label-list SHA-256 `30f64470c71e4b2b5a6626e40b3f3a5a329384b9328b6d5dc74719e47ad95499`; all are rejected independently by profile authentication, typed validation, and emission (267 layer-specific rejection checks).
- 9 ancestry/call/predicate move-copy-swap controls rejected at all three layers (27 checks), while a structurally equal independently reconstructed accepted program is accepted and proven to own its own object graph; forged historical proof reuse is rejected.
- Full carrier/caller/numeric/defines matrix: 90 combinations, exactly 1 accepted.
- Coexistence matrix: 8 carriers checked by validation and emission (16 checks).
- Analyzer-produced ABI/code-shape alternatives: 14 distinct source programs rejected at all three layers (42 checks).
- Current frozen corpus authenticated as 129 typed, 131 public, 81 unported, 212 total, with exact typed/public hashes and ordinal/neighbors.
- Real Task 28 reconstruction is regenerated from the current sources after subtracting Task 29, then authenticated by all three accepted artifact hashes, historical 128/130/82 counts, historical typed/public hashes, and normalized equality of all 128 prior typed blocks.
- Executable native authentication covers 6 public oracle cases, 8 direct ABI modes, exact `declared == handled == observed` mode IDs, unique switch arms, true aliasing, actual owning copies, counter vectors, result/branch/ABI/source-role observations, and 31 semantic-signature fields with 8 unique signatures.
- Exhaustive executable-region tamper closure mutates each of 4,499 lexical tokens independently and requires either parser rejection or a changed parsed semantic structure while the frozen repaired JSON remains byte-authenticated.
- Frozen oracle SHA-256: `b16c120e2331d87b61b98154d63954ad52ff328f149ebeb67b66321b73bde0a3`.

## Commands and results

```text
python3 -m unittest tests.test_typed_generator.Task29FocusBlurBorrowedSamplerTests
.......
----------------------------------------------------------------------
Ran 7 tests in 78.206s

OK
```

```text
python3 -m py_compile tests/test_typed_generator.py
exit 0
```

Owned test-file SHA-256: `047f4eef8cfbc47698974fc0e3fffa4adc42499fd4ed185c5b921e3ede6b2b84`.
