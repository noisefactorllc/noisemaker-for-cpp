# Task 25 Task 4 native oracle and ABI report

Date: 2026-08-11

## Status

BLOCKED on a confirmed Lens-only canonical compatibility-semantic gap. The
frozen oracle was not changed and production/generated files were not edited.
Task 4 cannot be reported DONE because the focused native oracle is correctly
RED for all four Lens cases under the current brief/design and allowed-file
boundary. Both Prismatic cases and both complete ABI matrices pass.

## Frozen preflight

- Brief SHA-256: `193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2`
- Design SHA-256: `9900749a387a30c6f1db0e584d2382288d44c2f3b0d5670f3b1968f1312c357b`
- Oracle generator SHA-256: `3594cd9f0a82e7a21e662f8897f43eac0c86943b15ca36b2a0d3d0f805b2772c`
- Oracle JSON SHA-256: `09d8d8a9667fe3b3b90cd582e501b7c0a61d2a41e65ea2d175771a105e32e116`
- Task 3 rereview SHA-256: `43827a0117cf1663dfa5bb8048d4c92993c634c3e7582e62d47f6dedf765f9f5`
- `node docs/port-engineering/task-25-oracle-generator.mjs --check`:
  `ok task-25-oracles.json and task-25-oracle-report.md`

## Strict TDD evidence

The first repository edit added only
`test_task25_cpp_native_oracle_table_is_exact_frozen_transcription`.

RED command:

```text
python3 -m unittest tests.test_typed_generator.TypedGeneratorTests.test_task25_cpp_native_oracle_table_is_exact_frozen_transcription
```

Exact RED reason:

```text
AssertionError: 1 != 0
```

at the assertion requiring exactly one
`TASK25_NATIVE_ORACLE_TABLE_BEGIN`; the current C++ file had zero.

After adding the exact embedded table, the focused transcription test is
GREEN:

```text
Ran 1 test in 0.005s

OK
```

The test compares the complete 61,946-byte JSON artifact, both exact ABI
tuples/resources, six case records, and eleven mutation records. It also
extracts both generated pixel namespaces and requires three samples each,
Lens zero and Prismatic one texture-size call, exact direct helper sets, and
absence of loop/index/operator/allocation/callback/exception/indirect forms.

## Native fixture and ABI evidence

The C++ native fixture independently consumes six constexpr case rows rather
than treating the embedded JSON as executable evidence. It reconstructs the
modular F32 input, validates its hash and five top-down probes, renders through
both public catalog dispatch and the two named public binders, and checks
fresh-render identity, input immutability, full F32/RGBA8 hashes and probes,
finite lane counts, dimensions, tile/full-resolution sentinels, and positive/
negative distortion coverage.

The complete binding matrices pass:

```text
PASS typed_task25_native_table_freezes_six_cases_eleven_mutations_and_resources
PASS typed_task25_lens_and_prismatic_binding_abis_reject_every_missing_or_wrong_input
```

The ABI test covers every one of 21 required Lens inputs and 11 required
Prismatic inputs, missing and wrong-typed, through named and catalog binders.
Exact and exact-plus-extra uniform/texture bindings accept. A binding
round-trip proves texture identity and every common/program value type and F32
bit pattern before binding.

Fresh Debug configure/build:

```text
cmake -S . -B /tmp/noisemaker-for-cpp-task25-task4-debug -DCMAKE_BUILD_TYPE=Debug
cmake --build /tmp/noisemaker-for-cpp-task25-task4-debug --parallel
[100%] Built target noisemaker-cpu-tests
```

## Native oracle failure and root cause

The input boundary is exact for the first Lens case. Named and catalog binder
outputs are byte-identical, repeat renders are byte-identical, and the input
remains immutable. The first output divergence is top-down pixel `(0,0)`, blue
lane:

| | F32 bits | value |
| --- | --- | --- |
| frozen canonical | `0x3e26616e` | `0.16248103976249695` |
| generated C++ | `0x3e8a0087` | `0.26953527331352234` |

The red, green, and alpha lanes at that pixel match exactly. Both Prismatic
cases match their complete frozen F32/RGBA8 hashes; all four Lens cases
diverge.

The root cause is canonical JavaScript line 4470 in `canonical-kernels.js`.
Its tint conditional tests a newly constructed `PooledFloat32Array` of three
lane comparisons. JavaScript typed arrays are always truthy, so the first
branch always returns the existing color and the tint alternative is
unreachable. Generated C++ evaluates the vector equality as a scalar boolean
and applies the tint alternative when the vector is not all ones.

A one-variable diagnostic confirms this precisely for the first case:

| render | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| frozen JS, alpha 23 | `40ec6e6bcca21c55b0abe81eca5760b2e623aad76678b49b070d350d0fe49948` | `de4b64895586ce7dc92352820b5c64d5660dc1d722bd8c5392e42568385ec4b8` |
| frozen JS, alpha 0 | same | same |
| generated C++, alpha 23 | `0517689d4d97caf68ab31c6ac79d345ed30dae6043de7fa34e2771a05381852d` | `e6e053c2e814c3cee1247c38efc4fcb9b5156466d60eca4b6c5abb6cc6e39802` |
| generated C++, alpha 0 | exact frozen hashes | exact frozen hashes |

Changing only alpha to zero makes the native tint mix a no-op and restores
the frozen full output byte-for-byte. It does not alter alpha output in this
case because sampled alpha already exceeds 0.23.

This is not an oracle defect and must not be repaired by weakening expected
hashes. It needs an amended brief/design authorizing an exact Lens-only,
structurally authenticated compatibility transform/carrier for this one
canonical truthiness site. A generic conditional or vector-truthiness widening
would violate the current closed scope.

## Generated byte isolation

The generated C++/manifest/header bytes were snapshotted before native testing
and re-hashed after diagnosis. They are unchanged:

| File | Before and after SHA-256 |
| --- | --- |
| `src/typed_generated/typed_slice.cpp` | `b8fe5a45f3032a86185d0515d512a48c40ac37c689c18db0ecb43bf7108b1cc9` |
| `src/typed_generated/typed_manifest.json` | `618081cfc312bae9e219a20c0876a23e2066e8630796f9872ef495f440a63b81` |
| `include/noisemaker/generated/catalog.hpp` | `cb0a5785163273723e85c77b868b70beb92f5775f113117c4d246c6467f2b80f` |

The pre-existing catalog test still expects 125 public factories and fails
after accepted Task 3 generated the intended 127-key catalog. That stale test
is separate from the Task 4 oracle mismatch and is outside the two exact Task
4 assertions reported above.
