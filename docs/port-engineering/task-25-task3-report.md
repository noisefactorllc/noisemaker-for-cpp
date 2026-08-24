# Task 25 Task 3 implementation report

Date: 2026-08-11

## Scope

Implemented only Task 3 slice/count/isolation and deterministic generation in
`.`. No Git, branch, worktree, commit,
pull request, deployment, or native-oracle fixture operation was performed.

Hand-edited repository files:

- `tools/glslcpp/generate_typed_slice.py`
- `tools/glslcpp/typed_slice.json`
- `tests/test_typed_generator.py`

Generator-owned outputs updated by exactly one canonical writer invocation:

- `src/typed_generated/typed_slice.cpp`
- `src/typed_generated/typed_manifest.json`
- `include/noisemaker/generated/catalog.hpp`

`tests/test_typed_slice.cpp` remained byte-identical.

## Binding inputs

| Artifact | SHA-256 |
| --- | --- |
| amended Task 25 brief | `193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2` |
| approved implementation design | `9900749a387a30c6f1db0e584d2382288d44c2f3b0d5670f3b1968f1312c357b` |
| approved Task 2 review | `ea1732d4c75f62c7eab3c42a0bfa95d1ae3ca9427e4342fb532bb1784f74d28b` |
| Task 2 report | `77caf4936a6a7180f586acba37321f4b05b989f09010d9cbf234260efcf0a343` |

## RED

Tests were added before production edits. The bounded command was:

```text
python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_task25_slice_counts_lists_positions_and_generated_isolation_are_exact \
  tests.test_typed_generator.TypedGeneratorTests.test_task25_loader_rejects_transitional_task24_no_carrier_slice
```

Observed result:

```text
Ran 2 tests in 0.054s
FAILED (failures=2)
```

The final-state test failed because the live explicit tuple had 123 entries,
lacked Lens at position 2, and therefore did not equal the frozen 125-key
tuple. The transitional regression failed with `GeneratorError not raised`,
proving the exact Task 24 123-program/no-carrier loader branch was still live.

## Minimal implementation and deterministic write

- Removed only the exact transitional 123-program/no-carrier branch from
  `load_slice`; the loader now accepts only the frozen 125-key digest and
  exactly the two selected lane-profile carriers.
- Added exactly two sorted records, both with exact `{}` defines and
  `literal-vec3-lane-index-v1`.
- Updated the success diagnostic from 123 to 125 programs.
- Ran the canonical writer exactly once:

```text
python3 tools/glslcpp/generate_typed_slice.py --write
generate_typed_slice: typed slice ok (125 programs)
```

The command exited 0 and updated only the three generator-owned outputs.

## GREEN and verification

Initial RED-pair GREEN after implementation:

```text
Ran 2 tests in 71.110s
OK
```

All twelve Task 25 Task 1-3 Python methods together:

```text
Ran 12 tests in 202.103s
OK
```

After adding explicit raw ordinal and unchanged Task 24 native-test hash
assertions, the Task 3 pair was rerun:

```text
Ran 2 tests in 106.443s
OK
```

Canonical deterministic check:

```text
python3 tools/glslcpp/generate_typed_slice.py --check
generate_typed_slice: typed slice ok (125 programs)
```

Exit status was 0. Final `python3 -m py_compile` over the generator and test
file also exited 0.

A targeted eight-method compatibility run exposed three stale expectations in
one Task 21 test: the final 125-list digest now rejects missing CRT/Degauss
before the old boundary message, and Lens shifts Degauss's raw namespace from
21 to 22. The other seven methods passed. After correcting those test-only
expectations, the affected method was rerun:

```text
Ran 1 test in 105.903s
OK
```

## Exact mechanical results

- Counts are exactly `125 typed / 127 public / 85 publicly unported / 212 corpus`.
- Newline-terminated typed-list SHA-256 is
  `9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4`.
- Newline-terminated public-list SHA-256 is
  `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`.
- Zero-based positions are Lens 2, Gather Sorted 52, and Prismatic 59, with
  the three exact frozen neighbor triples.
- The slice has exactly two lane-profile records in sorted order, both with
  exact `{}` defines.
- Generated output has exactly 125 program blocks and manifest rows, 127
  catalog rows, one Lens block/row/declaration, and one Prismatic
  block/row/declaration.
- Raw namespaces are exactly Lens `typed_2`, current Gather `typed_52`, and
  Prismatic `typed_59`; the in-memory Task 24 baseline has Gather `typed_51`.
- All 123 Task 24 blocks are byte-identical after replacing only
  `typed_[0-9]+` with the frozen ordinal sentinel.
- Normalized Lens diagnostic output is exactly 27,446 bytes with SHA-256
  `6cfa9d58cbc096b7372b00b17b4ed0b146236a4738acef7870cad05593a57fc5`.
- Normalized Prismatic diagnostic output is exactly 13,316 bytes with SHA-256
  `8d6c98fed4ab2d2a2130566081386cdfb74d01ae84c11b198a1be08ae187155f`.
- Prior manifest rows remain structurally identical except the monolithic
  output hash; the only new manifest/header/catalog rows are the two selected
  keys.
- `tests/test_typed_slice.cpp` remains at its accepted Task 24 SHA-256
  `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6`.

## Before/after SHA-256 inventory

| File | Before | After |
| --- | --- | --- |
| `tools/glslcpp/generate_typed_slice.py` | `8c453c5526dee235232df1d25ada88294d120e2023632fbfa89da1b425ff7df1` | `4ef4203e80dd8beb78e65168c804234cdeb875436b1828ca9280c31bed138227` |
| `tools/glslcpp/typed_slice.json` | `e6a0bbe1cc1caef06d726e7040fcb8b1a205593d30885625aad6460e96b4747a` | `1534c7a6d807bf58734da59aaa8b37f8dc8342ec5d744b936e2e6e079ad1bb49` |
| `src/typed_generated/typed_slice.cpp` | `8d06f5864fbb6eca1eb205afc4f9690ec8f0ddd90a384e4f84a80fc50a0c3ea6` | `b8fe5a45f3032a86185d0515d512a48c40ac37c689c18db0ecb43bf7108b1cc9` |
| `src/typed_generated/typed_manifest.json` | `bf7020628f988acd61128c527495e609cba7e74ee41bc44bfec7053bcd1187b5` | `618081cfc312bae9e219a20c0876a23e2066e8630796f9872ef495f440a63b81` |
| `include/noisemaker/generated/catalog.hpp` | `1ca4f356117d2067bb766b630d44e6c4075a3da60ac365f5f6b6a48b7d77d105` | `cb0a5785163273723e85c77b868b70beb92f5775f113117c4d246c6467f2b80f` |
| `tests/test_typed_generator.py` | `0e89165df7f7c40652075e6a83d68e3aee7ffa3a4a89844c49fd6e57aeb99bc2` | `8269f5bf31b7b318bdcfad13667747f53f672d71028d0061b0fdfc16e4803825` |
| `tests/test_typed_slice.cpp` | `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6` | `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6` |

Task 2 production authority files remained unchanged:

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/literal_vec3_lane_index_profile.py` | `62920c523ab4a73e4a6c75fe912459bdf7ccde86196871eda2eeab16c69ca216` |
| `tools/glslcpp/emit_typed_cpp.py` | `18659e9b2e76e14d2da69ce198b21ce653d325525a67b290b856ee7af61dbd1c` |

## Stop boundary

Task 3 stops here. Native six-case pixel-level F32/RGBA8 oracle fixtures,
mutation harnesses, full build/sanitizer gates, independent final review, and
publication remain later tasks and were not entered.

## Fix round 1: exact historical Task 22 reconstruction

Fresh independent review artifact
`docs/port-engineering/task-25-task3-fresh-review.md`, SHA-256
`b7e2fd42597f6eb58710db6acf76791230faed49c5ccc601a77ad0c2c5200781`,
identified one Important test-fixture defect: the Task 22 isolation fixture
removed only the two Task 25 keys, leaving the six Task 23 programs, Task 24
Gather Sorted, and Task 23's capability vocabulary addition.

### Fix-round RED

The Task 22 test first received literal historical assertions for exact
`116 typed / 118 public / 94 publicly unported / 212 corpus`, typed-list
SHA-256
`76c81945ef992ed258900815335a23ae4f36d8756b7763ebd5e03d8562fde8e3`,
public-list SHA-256
`019a80df52192e3c898af58a5e3a2a9da654896eadde78097ce4a818579328f9`,
CRT and Degauss positions 19 and 20, absence of
`source-global-literal-int-v1`, and 115 prior pre-CRT blocks.

```text
python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_task22_crt_exclusions_remain_closed

Ran 1 test in 31.820s
FAILED (failures=1)
```

The exact observed tuple was `(123, 125, 87, 212)` instead of
`(116, 118, 94, 212)`, directly proving the seven retained Task 23/24 keys.

### Minimal test-fixture repair

The in-memory Task 22 fixture now removes exactly:

- the six frozen `SOURCE_GLOBAL_LITERAL_INT_KEYS` introduced by Task 23;
- Task 24 `filter/pixelSort:gatherSorted`;
- the two Task 25 lane-profile keys;
- the single Task 23 `source-global-literal-int-v1` capability.

The test asserts that its literal six-key tuple equals the production frozen
`SOURCE_GLOBAL_LITERAL_INT_KEYS` set before removal. Because the current
validator correctly requires the current vocabulary, the historical
generation calls use a test-local validation adapter that validates every
remaining typed program against the current approved vocabulary while the
reconstructed spec itself retains and proves the exact historical Task 22
vocabulary. No production code or generated byte changed.

The repaired test additionally locks the complete generated C++ identities:

- Task 21 pre-CRT SHA-256
  `986d6d3116497282e468440a6786be5728ee53f0558ea8c5a553831e353aa5ba`;
- Task 22 post-CRT SHA-256
  `a3f8135d41e9f2abc864fada60532309b56c43f6e6eb138d548a23b57f944c4f`;
- ordinal-dependent Task 22 `typed_19` CRT block SHA-256
  `c2cad7e88fb817c311abb0041fec98d14c28ae3c3bd731b67944c745b8c295ec`;
- ordinal-normalized CRT block SHA-256 remains
  `36410c4f25e2a0d53bba3bdc7164c18f74cc7f06de8f7589186da182b7246922`.

Two intermediate diagnostic runs exposed and then closed current-vocabulary
and stale raw-ordinal test assumptions. The final focused result was:

```text
Ran 1 test in 98.697s
OK
```

The requested cross-era regression command covering the Task 3 pair, Task 23
isolation, both Task 24 historical checks, and current committed
generation/manifest checks completed:

```text
Ran 7 tests in 394.752s
OK
```

Final deterministic and syntax gates after the repair:

```text
python3 tools/glslcpp/generate_typed_slice.py --check
generate_typed_slice: typed slice ok (125 programs)

python3 -m py_compile tests/test_typed_generator.py
```

Both exited 0.

### Fix-round final SHA-256 inventory

Only `tests/test_typed_generator.py` changed in the repository during this
fix round:

| File | Pre-fix | Final |
| --- | --- | --- |
| `tests/test_typed_generator.py` | `8269f5bf31b7b318bdcfad13667747f53f672d71028d0061b0fdfc16e4803825` | `c13af462519be2ff879542d7b5fc0f682ba037abd411a62d49477d7f55468818` |

The Task 3 production and generated hashes remain unchanged:

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/generate_typed_slice.py` | `4ef4203e80dd8beb78e65168c804234cdeb875436b1828ca9280c31bed138227` |
| `tools/glslcpp/typed_slice.json` | `1534c7a6d807bf58734da59aaa8b37f8dc8342ec5d744b936e2e6e079ad1bb49` |
| `src/typed_generated/typed_slice.cpp` | `b8fe5a45f3032a86185d0515d512a48c40ac37c689c18db0ecb43bf7108b1cc9` |
| `src/typed_generated/typed_manifest.json` | `618081cfc312bae9e219a20c0876a23e2066e8630796f9872ef495f440a63b81` |
| `include/noisemaker/generated/catalog.hpp` | `cb0a5785163273723e85c77b868b70beb92f5775f113117c4d246c6467f2b80f` |
| `tests/test_typed_slice.cpp` | `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6` |

No Git operation was performed.
