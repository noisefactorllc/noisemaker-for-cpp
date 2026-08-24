# Task 25 Task 4 custom comparer report

Date: 2026-08-11  
Repository: `.`  
Status: COMPLETE

## Outcome

The approved Lens-only canonical-JavaScript vector-equality-result truthiness
comparer is implemented. The generated Lens tint predicate at raw corpus line
273 is the sole generated call site. Its surrounding
`mix(color.rgb, ..., alpha * 0.01)` and both conditional arms remain present.
Ordinary `Vec::operator==`, Prism, general equality/conditional lowering, and
all other generated programs remain unchanged in behavior.

All four frozen Lens cases and both frozen Prismatic cases pass their exact
full-F32 and RGBA8 SHA-256 hashes and five probes, along with repeatability,
input immutability, dimensions, finiteness, named/catalog binder identity, and
binding ABI checks. No tolerance-based acceptance was used.

No Git command, branch, worktree, commit, push, PR, workflow, publication, or
repository creation was performed. Canonical corpus GLSL and frozen Task 25
oracle artifacts were not edited.

## Files changed

Non-generated implementation/configuration:

- `include/noisemaker/glsl_types.hpp`
- `tools/glslcpp/frontend/lens_distortion_comparer_profile.py` (new)
- `tools/glslcpp/generate_typed_slice.py`
- `tools/glslcpp/emit_typed_cpp.py`
- `tools/glslcpp/typed_slice.json`

Tests:

- `tests/test_glsl_types.cpp`
- `tests/test_typed_generator.py`
- `tests/test_generated_kernels.cpp`

Canonical generated outputs:

- `src/typed_generated/typed_slice.cpp`
- `src/typed_generated/typed_manifest.json`

`include/noisemaker/generated/catalog.hpp` was regenerated/check-verified but
remains byte-identical at
`cb0a5785163273723e85c77b868b70beb92f5775f113117c4d246c6467f2b80f`.

## Strict TDD evidence

### RED 1: named C++ comparer did not exist

The first production change that the test was designed to catch was removal
or absence of the named compatibility comparer, while separately proving that
ordinary vector equality remains mathematical.

Command:

```text
/usr/bin/time -p cmake --build /tmp/noisemaker-for-cpp-task25-task4-debug --target noisemaker-cpu-tests --parallel
```

Expected RED result (exit 2, real 0.85s):

```text
tests/test_glsl_types.cpp:44:11: error: use of undeclared identifier
'canonical_js_vector_equality_result_is_truthy'
tests/test_glsl_types.cpp:45:11: error: use of undeclared identifier
'canonical_js_vector_equality_result_is_truthy'
2 errors generated.
```

Minimal implementation added the constrained `Vec<N, T>` comparer. Focused
GREEN evidence:

```text
PASS glsl_canonical_js_vector_equality_result_truthiness_is_not_mathematical_equality
```

The test proves the named comparer is true for equal and unequal `Vec3`
operands, while ordinary `equal_left == equal_right` is true and ordinary
`equal_left == unequal` is false. Build real time was 6.51s; the test binary
real time was 2.12s. The same binary still exposed the expected pre-fix Lens
oracle RED and the previously documented stale 125-key catalog assertion.

### RED 2: custom comparer carrier schema was absent

Command:

```text
/usr/bin/time -p python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_task25_lens_custom_comparer_profile_is_admitted_with_lane_profile
```

Expected RED result (1 failure, real 0.23s):

```text
AssertionError: exact Lens custom comparer profile was rejected:
unsupported typed slice schema
```

After adding only the exact Lens map and schema lock, the same command was
GREEN (`Ran 1 test in 0.059s`, real 0.13s).

### RED 3: canonical generation did not route the predicate

Command:

```text
/usr/bin/time -p python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_task25_lens_custom_comparer_routes_only_the_tint_predicate
```

Expected RED result (1 failure, real 40.50s):

```text
AssertionError: 1 != 0
```

The generated program contained zero calls to the required named comparer.
After the authenticated profile and emitter route were implemented, the same
test was GREEN (`Ran 1 test in 65.632s`, real 65.75s). It now freezes exactly
one comparer call in the Lens block, exactly one in the complete generated C++
file, the complete surrounding emitted statement, and absence of the former
ordinary scalar vector-equality spelling at that site.

## Implementation design

### Named comparer

`noisemaker::glsl::canonical_js_vector_equality_result_is_truthy` is a
constrained C++ vector comparer that always returns true. Its adjacent comment
states the compatibility reason: canonical JavaScript creates an allocated
typed-array comparison result, and the object is truthy whether its lanes are
true or false. It explicitly states that the function is not mathematical
vector equality.

The global `Vec::operator==` declaration is unchanged. The new comparer is
available as a narrow reusable primitive for separately authenticated future
sites, but this Task 25 generation profile authorizes exactly one call.

### Profile and deterministic order

The checked-in slice carries one top-level custom comparer map:

```json
{
  "classicNoisedeck/lensDistortion:lensDistortion":
    "canonical-js-vector-equality-result-truthiness-v1"
}
```

Generation order is explicit and deterministic:

1. Parse/analyze the exact Lens source.
2. Authenticate the custom comparer profile against the untouched pre-lane
   typed program. This step is identity-only and does not rewrite the tree.
3. Apply and transition-check the existing
   `literal-vec3-lane-index-v1` profile.
4. Validate the combined final tree with both exact carriers.
5. Re-authenticate the final tree in the emitter and retain object authority
   for the one predicate.
6. Emit the named comparer only when visiting that exact predicate object.

Prismatic continues to carry only `literal-vec3-lane-index-v1`. Missing or
wrong Lens comparer carriers, comparer carriers on Prismatic/foreign keys,
missing or wrong lane carriers, wrong numeric contracts, and wrong caller
hashes are rejected independently at loader, validator, and emitter
boundaries.

### Preserved emitted evaluation

The final generated line retains the original first `color.rgb` mix operand,
the complete conditional with both true and tint arms, and
`alpha * 0.01`. Only the conditional predicate call changes from ordinary
native vector equality to:

```cpp
glsl::canonical_js_vector_equality_result_is_truthy(
    glsl::Vec3(glsl::swizzle<0, 1, 2>(color)),
    glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(1.0))))
```

The complete generated C++ contains one occurrence. No allocation, callback,
runtime dispatch, generic conditional change, or `Vec::operator==` change was
introduced.

## Source and tree locks

Profile identity:

| Lock | Value |
| --- | --- |
| Program key | `classicNoisedeck/lensDistortion:lensDistortion` |
| Profile | `canonical-js-vector-equality-result-truthiness-v1` |
| Profile tuple SHA-256 | `8dece8742d7539614d36045515985712aa7c05addc705490aa0ec3b6d4d07916` |
| Raw source | 8,269 bytes / `f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444` |
| Normalized source | 7,723 bytes / `6586c49b079a3b0f4aa3538c8e735e70db088ff2e5d2ea1037e9e9c5486fdf52` |
| Defines | `{}` |
| Interface SHA-256 | `53e759b54c0710d9cb3375cc2353878abebec06b378aeaaf9d745c6ecfd2b4ca` |
| Raw/normalized line | 273 / 265 |
| Exact typed path | `(21, 'e0', 0, 1, 1)` |

Aggregate tree locks:

| Stage | Main | Functions | Whole program |
| --- | --- | --- | --- |
| Pre-lane | `dc6d4d2a3b5c50598a879dc6679553b3f89d964a19f5d4c79716970a7f2493ee` | `263870c469a9dc3b1f4d5f3a2498864c6da4ff4eaf2cc3efaf198376e4d304c1` | `f63fb6dba6626791c248501bcfc5ca1c94f073a0593f34dbe846056fe35c81f5` |
| Final after lane profile | `8de6658184c69cb679f0453e37e37f538eebabb0e14f720d1eeea61e715d30ec` | `c166fa2b38ec68661fb4d73be1bfb3eef4f879da7d82dbfca44deba1b651a756` | `e5dbb049717ce77ba79a36c6ea39ddde88e561df1ba06c98fba0ddd179a63d2e` |

Exact target locks:

| Node | Span | SHA-256 |
| --- | --- | --- |
| Assignment parent | `265:5-265:133` | `fcad293a35aaa5e8d58fb79a67440fd40a6813a4e3cb5f6621967a419aa0c1ab` |
| `mix` parent | `265:17-265:133` | `0821c5cc7a1190eda7fa50f0c6b681297beee3bec14122ef35ef1df8bc496158` |
| Conditional site | `265:33-265:118` | `d0ed1263c4e79948ce8a260a4d46d3ea4fd2f603e741f711048e59fe67ea0daa` |
| Predicate | `265:33-265:55` | `54bdae95beb11464b7552e4625c5da13588b0856fd92158e3202e96a69ee192a` |
| Predicate lhs | locked by hash | `48cee70a2575caafe9de2730b82198828ab45dc22f26b7728b9348351e6b3d88` |
| Predicate rhs | locked by hash | `7d19f613fdc4eb2dfecf2b5a85b1ab12b46573ea6636ced78712f919814f9c31` |
| True arm | locked by hash | `5c2f390c2f4dea3e0c0288634599181961adc98a3579c2842e3ab18581be2324` |
| False arm | locked by hash | `12a3174e1007a3d465ed76b1fde3168b4923a59e3d1e2a7454cf80522321e78e` |
| Alpha sibling | locked by hash | `5078bdeff5e3426961135e7133704398f563ba88e4d99ca249b96a35982a8793` |

Authentication additionally requires exactly eight functions, sole `main`
ID 38 with 25 statements, analyzed body status, empty optional proof carriers,
the zero-loop/acyclic call profile, exact node kinds/types/categories/operators,
exact ancestry, and a complete whole-program census containing exactly this
one vector-equality conditional site.

Negative tests reject wrong key/carrier/caller hash; raw or normalized source;
wrong pre/final stage; main-body drift; assignment/mix/site/predicate/operand/
true-arm/false-arm drift; span drift; missing/extra sites; and internal profile
tuple drift. Loader and direct validator/emitter tests also reject missing,
wrong, Prismatic, and foreign comparer carriers.

## Generated projections and counts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 10,462 | `b4f2dd88fcd316886ba4e7834ad9a35296fd19085bac82d692d1438f43735867` |
| `src/typed_generated/typed_slice.cpp` | 1,025,444 | `6a76407f7d812b248d4072b324b8ec42ecc561437fd8fb229169bbd94c03d372` |
| `src/typed_generated/typed_manifest.json` | 197,002 | `f595d92d1d0abdda365725c7a6152982a295d4e88c908def2c3f30e42b50a098` |
| `include/noisemaker/generated/catalog.hpp` | 11,826 | `cb0a5785163273723e85c77b868b70beb92f5775f113117c4d246c6467f2b80f` |
| Ordinal-normalized Lens block | 27,519 | `a516c15ef5eee1c0e16766f4104e4397b01293fc2a39df75154a029f3c312dc6` |

Counts remain 125 typed programs, 127 public factories, 85 corpus programs
not publicly ported, and 212 corpus programs. Lens remains typed ordinal 2;
Gather Sorted ordinal 52; Prismatic ordinal 59. The manifest contains one
`custom_comparer_profile` row, for Lens only. Generated C++ contains one
named-comparer call. The Prismatic normalized projection remains 13,316 bytes /
`8d6c98fed4ab2d2a2130566081386cdfb74d01ae84c11b198a1be08ae187155f`.
Task 25 generated-isolation tests prove every pre-Task-25 program block is
ordinal-normalized byte-identical.

Frozen oracle artifacts remain exactly:

| Artifact | SHA-256 |
| --- | --- |
| `docs/port-engineering/task-25-oracles.json` | `09d8d8a9667fe3b3b90cd582e501b7c0a61d2a41e65ea2d175771a105e32e116` |
| `docs/port-engineering/task-25-oracle-report.md` | `f72b69688d9a2f10df1603d1a012f6df8d0834f012438386038637630eb20611` |

## Exact six-case native parity

The native test traverses all six rows, renders twice through the public
catalog and once through the named binder, requires byte identity among all
three results, re-hashes the complete F32 and RGBA8 outputs, verifies five
probes when the hashes are exact, checks untouched input bytes, dimensions,
and every finite/nonfinite lane count, then requires one final `all_exact`.
Its final result is PASS.

| Case | Dimensions | Exact F32 SHA-256 | Exact RGBA8 SHA-256 |
| --- | --- | --- | --- |
| `lens-chromatic-add-static` | 11x7 | `40ec6e6bcca21c55b0abe81eca5760b2e623aad76678b49b070d350d0fe49948` | `de4b64895586ce7dc92352820b5c64d5660dc1d722bd8c5392e42568385ec4b8` |
| `lens-chromatic-alpha-modulated` | 10x8 | `3c4ff034284a714a545a35106c98e7d93398fb800f7bee2dbccffb08592a5e61` | `18b8e022320da7b278ae2935b8602f50ebcf30cfc1e5eb058e932f8d05666ada` |
| `lens-prismatic-add-static` | 9x9 | `0ed06880cce85cebb134fbc0cb2b5710a4a3e08dc336512e31cbaf2a5ec77688` | `204fe8f73e191091c231f159d147cb10df17b9bc88abc44c6baa75da7684b05e` |
| `lens-prismatic-alpha-modulated` | 12x6 | `7fe6ac9ba3bf66f5f3f747f635b6ce5bd9d7e1d184678a74ba1d69cc14b18b76` | `4b8ffb755c45fa8b37e686ff71fd61f66c120eeaf2644b6d871e01b6a728521b` |
| `prism-static-origin-tile` | 10x7 | `daad9591d01855520a052fd2d89ed2e9ed32da2d93421a041e40d58b5389daff` | `5f73c9a1151a312569107b68abd705555f7d2c5540c8e3ea44abd7891a9a3640` |
| `prism-modulated-offset-tile` | 9x6 | `dbc929af7ba49e768bd39a0188e0f9b9426581ba564c856e6289531304c8b216` | `5f141b94b43d85418de325137173a181d705f50574f4d1ca78e01972a1044447` |

Final native log SHA-256:
`64b1c787ac5c7e1715600fceaf8b934ad6ef136d008de52244fb0a633be1357c`.

## Validation commands, results, and timings

### Focused implementation validation

| Command | Result | Timing |
| --- | --- | ---: |
| Direct comparer RED build shown above | Expected compile RED | real 0.85s |
| Direct comparer build + native focused log | Comparer PASS; known pre-fix Lens/catalog RED remained | build 6.51s; executable 2.12s |
| Exact loader RED shown above | Expected 1 failure | real 0.23s |
| Exact loader GREEN | 1/1 PASS | real 0.13s |
| Generated route RED shown above | Expected 1 failure | real 40.50s |
| Generated route GREEN | 1/1 PASS | real 65.75s |
| Structural comparer mutation test | 1/1 PASS | real 0.67s |
| Four amended Task 25 boundary/projection tests | 4/4 PASS | 85.629s |
| Loader mutation + exact emitted-line tests | 2/2 PASS | 105.512s |
| `python3 -m unittest tests.test_typed_generator -k task25` | 16/16 PASS | 288.722s |

An earlier complete Task 25 run correctly exposed the not-yet-amended direct
carrier expectations (2 failures, 5 errors; 192.103s). Those tests were
updated to require the exact combined Lens carrier and keep Prism lane-only;
the clean 16/16 run above is the final result.

### Canonical generation and frozen oracle

| Command | Result | Timing |
| --- | --- | ---: |
| `python3 tools/glslcpp/generate_typed_slice.py --write` (final write) | `typed slice ok (125 programs)` | real 39.14s |
| `python3 tools/glslcpp/generate_typed_slice.py --check` (final) | `typed slice ok (125 programs)` | real 31.52s |
| `node docs/port-engineering/task-25-oracle-generator.mjs --check` (before native validation) | oracle/report OK | real 0.25s |
| Same oracle check (final) | oracle/report OK | real 0.15s |

All checked-in generated output changes were produced by the canonical
`--write` command. No generated file was edited manually.

### Python compile and historical compatibility/generator suites

Final Python compile command:

```text
python3 -m py_compile \
  tools/glslcpp/generate_typed_slice.py \
  tools/glslcpp/emit_typed_cpp.py \
  tools/glslcpp/frontend/lens_distortion_comparer_profile.py \
  tools/glslcpp/frontend/literal_vec3_lane_index_profile.py \
  tests/test_typed_generator.py
```

Result: exit 0, real 0.16s.

Full suite command:

```text
python3 -m unittest \
  tests.test_typed_generator tests.test_semantic \
  tests.test_generator tests.test_corpus
```

Final result: `Ran 157 tests in 902.588s`, `OK` (real 902.70s).

The first broad run was intentionally retained as evidence: 151/157 passed in
898.234s, and its six failures were stale historical/current fixtures rather
than runtime defects. Two test-only emitters that explicitly bypass
`_Emitter.__post_init__` needed to initialize the new authorization field;
Task 24's current Gather audit needed ordinal 52 after the accepted Lens
insertion; the current allowlist needed the accepted Lens/Prismatic rows; one
test expected an obsolete capability diagnostic; and manifest projection
initially added `none` to every row. The final design limits the new manifest
field to Lens, restoring historical Task 24 manifest bytes. The six focused
repairs passed 6/6 in 77.309s before the clean 157/157 rerun.

### Final Debug/native/CTest gates

| Command | Result | Timing |
| --- | --- | ---: |
| `cmake -S . -B /tmp/noisemaker-for-cpp-task25-task4-debug -DCMAKE_BUILD_TYPE=Debug` | configure/generate exit 0 | real 0.11s |
| `cmake --build /tmp/noisemaker-for-cpp-task25-task4-debug --parallel` | `Built target noisemaker-cpu-tests` | real 5.52s |
| `/tmp/noisemaker-for-cpp-task25-task4-debug/noisemaker-cpu-tests` | all native tests PASS, including direct comparer, 127-key catalog, Task 25 table/ABI/exact parity | real 1.56s |
| `ctest --test-dir /tmp/noisemaker-for-cpp-task25-task4-debug --output-on-failure` | 1/1 PASS, 0 failures | test 1.35s; real 1.37s |

## Self-review

- Scope: changes are limited to the approved comparer primitive, exact Lens
  profile/carrier/emission path, canonical outputs, and required tests. No
  unrelated production feature or corpus source was changed.
- Semantics: the surrounding `mix` and both arms remain byte-visible in the
  generated statement; only predicate evaluation uses the named comparer.
- Isolation: one generated call exists, Lens only. Prism retains its previous
  block hash. Task 25 isolation checks cover all other blocks.
- Fail-closed behavior: raw and normalized sources, caller hash, key, defines,
  interface, tree stage, main/function/whole hashes, exact path including the
  expression-root marker, ancestry, predicate/operands/arms/alpha, and complete
  site census are authenticated.
- Equality behavior: ordinary `Vec::operator==` is untouched and directly
  tested beside equal/unequal compatibility comparer calls.
- Metadata: exactly the Lens manifest row names the custom comparer profile;
  historical rows are unchanged apart from the monolithic output hash required
  on every row.
- Oracle integrity: frozen JSON/report hashes are unchanged and checks pass
  before and after native work.
- Catalog: the prior stale native assertion was corrected to the already
  accepted 127-key catalog and now enumerates Lens and Prismatic explicitly.
- Safety: no Git or publication operation occurred; no paid/generated external
  assets or unrelated working files were removed.

## SHA-256 inventory for touched non-generated source/test files

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `include/noisemaker/glsl_types.hpp` | 16,431 | `37e71f566d5b8d5e1abf68fee1b27338898e4afacb116764824274dfda6780d8` |
| `tools/glslcpp/generate_typed_slice.py` | 122,105 | `8755d89308684fac7d673b21d7cfa51aebee9da773af0b0c9c6c4dc856bcac54` |
| `tools/glslcpp/emit_typed_cpp.py` | 85,287 | `947f01f759c6b6cbe005b6be6505823fc4fbf7a4c124bdb34637a93727e9fead` |
| `tools/glslcpp/frontend/lens_distortion_comparer_profile.py` | 10,601 | `06c6e8a8d5947fb446f1572e3486add5942e37a5c6a42527a85563238ff3dd27` |
| `tools/glslcpp/typed_slice.json` | 10,462 | `b4f2dd88fcd316886ba4e7834ad9a35296fd19085bac82d692d1438f43735867` |
| `tests/test_glsl_types.cpp` | 7,296 | `f4d28da8bbbb80c79037419a8f997d7724eeaf81426ffa9320265cf64cfae818` |
| `tests/test_typed_generator.py` | 591,370 | `3b0f55a1b967399bac4ba3efb50586e36a278cd44fb77d54ebf7f0ef2e3b9778` |
| `tests/test_generated_kernels.cpp` | 213,445 | `630ca223723c93226631951fc242795ab20a283b2c38b1f950d87cee8e08ca76` |

## Report checksum convention

A report cannot contain its own final whole-file SHA-256 without changing the
bytes being hashed. The SHA-256 of this report body, through the byte immediately
before this section, is recorded below after finalization. The actual complete
file SHA-256 is recorded in the adjacent
`task-25-task4-custom-comparer-report.md.sha256` file and in the parent-agent
handoff.

Report-body SHA-256: `9e1334041c617f2cc71214e665141a39f4d8eea6622f8f3c84b81f511392ddf7`
