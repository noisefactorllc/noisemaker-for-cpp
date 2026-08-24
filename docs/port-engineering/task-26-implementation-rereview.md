# Task 26 Implementation Rereview

Date: 2026-08-11  
Repository: `.`  
Mode: read-only repository review; no Git command or repository edit

## Verdict

- **Spec compliance: PASS.** All three original Important findings are addressed.
- **Code quality: PASS with one nonblocking Minor.** The original loader diagnostic issue remains intentionally out of repair scope.
- **Finding counts:** Critical 0, Important 0, Minor 1.
- **Acceptance blockers:** none.

The repair report SHA-256 was authenticated as `4b5f324f826d18ef87c02968011d7aeaae59a1e1f53daf7824e96de4121fe3f1` before review.

## Original finding disposition

### I-1 — Addressed: distinct mutation execution paths and fail-closed dispatch

`task26_mutation_render_with_witness` now has an explicit switch arm for each of the eleven enum values and an invalid-value `default` that throws before the pass-through return (`tests/test_generated_kernels.cpp:7531-7610`). The dedicated identity-control paths are materially distinct:

- `vec4_extra` constructs a `Weight4` with the frozen fourth lane (`tests/test_generated_kernels.cpp:7575-7581`) and passes that four-lane-typed value through its dedicated luminance routine (`tests/test_generated_kernels.cpp:7630-7635`, `tests/test_generated_kernels.cpp:7652-7653`). It intentionally consumes the three RGB-overlap lanes, matching the frozen type/arity-observably-inert oracle.
- `helper_local_exact_f32` constructs the exact three F32 words inside each luminance invocation and records each helper materialization (`tests/test_generated_kernels.cpp:7654-7660`).
- `main_owned_exact_f32` constructs the exact weight vector once in render ownership and passes it as an explicit helper argument (`tests/test_generated_kernels.cpp:7599-7605`, `tests/test_generated_kernels.cpp:7636-7639`, `tests/test_generated_kernels.cpp:7661-7662`). The helper closure captures the dot implementation, not the owner weight; the weight itself crosses the explicit argument boundary.

The native witness test independently checks all eleven path identities and the vec4/helper-local/main-owned ownership, arity, materialization, call-count, and explicit-argument contracts (`tests/test_generated_kernels.cpp:7721-7778`). A separate native test proves an out-of-range mode throws (`tests/test_generated_kernels.cpp:7713-7718`), and the existing exhaustive loop still compares all 88 frozen output/difference/hash rows (`tests/test_generated_kernels.cpp:7849-7883`).

### I-2 — Addressed: coherent single-axis typed-tree negative closure

Source path and declaration span are now separate candidates (`tests/test_typed_generator.py:11039-11042`, `tests/test_typed_generator.py:11181-11190`) with preconditions proving the non-target coordinate remains unchanged (`tests/test_typed_generator.py:11338-11345`). The former parameter-owner mislabel is now accurately `parameter-name`; function ownership is separately represented by changing the helper signature owner and resolving all five calls to it (`tests/test_typed_generator.py:11001-11022`, `tests/test_typed_generator.py:11051-11061`, `tests/test_typed_generator.py:11368-11380`).

The write and reference-escape candidates are now based on analyzer-produced assignment/call shapes. The write targets the declaration-backed symbol with the typed initializer (`tests/test_typed_generator.py:11063-11076`); the escape adds a resolvable `inout vec3` helper and passes the declaration-backed read (`tests/test_typed_generator.py:11078-11108`). Their structural witnesses validate the exact intended shape before any rejection assertion (`tests/test_typed_generator.py:11392-11407`). Every candidate must satisfy its named precondition before profile, validator, and emitter rejection are checked independently (`tests/test_typed_generator.py:11412-11433`).

### I-3 — Addressed: executable table authentication and tamper sensitivity

The new parser extracts the executable initializers for the eight native cases, eleven mutation names, and 88 mutation-result rows, plus the mutation enum and explicit switch arms (`tests/test_typed_generator.py:21-77`). The test reconstructs every expected field from the authenticated frozen JSON (`tests/test_typed_generator.py:11567-11626`) and compares every executable table, enum name, and dispatch name one-to-one (`tests/test_typed_generator.py:11628-11638`). Independent single-field tamper cases for the executable case, name, and result tables must all fail while the embedded JSON remains unchanged (`tests/test_typed_generator.py:11640-11663`).

## Remaining finding

### Minor M-1 — unchanged: imprecise combined loader diagnostic

`tools/glslcpp/generate_typed_slice.py:654-661` still reports `typed slice literal vec3 lane profile drift` for combined census/key, literal-Vec3, or Smooth-carrier failure. This is diagnostic imprecision only and is not an acceptance blocker. Split those invariants into separately named errors in a future narrow cleanup.

## Independent verification

- Focused current tests passed: `test_task26_exhaustive_profile_validator_and_emitter_negative_closure` and `test_task26_cpp_native_oracle_table_is_exact_frozen_transcription` — 2 tests, `OK`, 0.268 seconds.
- Fresh native `LastTest.log` files postdate the repair and report passing runs: Debug 1.85 seconds, Release 0.43 seconds, ASan/UBSan 5.99 seconds.
- Production/profile inputs retain their reviewed hashes: profile `6b25894b…`, generator `04914609…`, emitter `11fc8432…`, typed-slice carrier `a717f8d0…`, and unchanged `tests/test_typed_slice.cpp` `55fee138…`.
- Generated outputs retain their reviewed hashes exactly: `typed_slice.cpp` `df4aa212…`, manifest `e7f7acd5…`, and catalog header `557ccdbe…`.
- Frozen oracle JSON remains `7975cbe5…`.
- The repair-window file scan found only `tests/test_generated_kernels.cpp` and `tests/test_typed_generator.py`; their full hashes match the authenticated fix report (`cc86c7d7…` and `fa87e65b…`).

No broad suite was rerun during rereview. The focused current gates and post-repair Debug/Release/sanitizer logs are credible for the bounded test-only repair.
