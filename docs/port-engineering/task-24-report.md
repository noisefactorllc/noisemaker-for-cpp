# Task 24 implementation report

Date: 2026-08-11

## Outcome

`filter/pixelSort:gatherSorted` is admitted as the sole Task 24 typed CPU
kernel.  The typed/public/unported/corpus counts are now exactly
`123 / 125 / 87 / 212`.  The implementation does not add `round` to the
global capability or builtin vocabulary and does not change a generic cast,
runtime conversion, loop proof, or compatibility transform.

The only new semantic carrier is the per-record
`gather-sorted-round-to-int-v1` identity profile.  It authenticates the frozen
source, complete typed program/tree, exact round child, exact int-constructor
parent, declaration site, loop/resource/interface state, and caller hash.
Validator and emitter authenticate independently.  The emitter owns the exact
nested route:

```cpp
glsl::detail::float_to_int32(glsl::round(/* authenticated argument */))
```

Both emitter authorization fields initialize unconditionally to `None` before
optional authentication.  The Task 23 mutation harness, which deliberately
constructs `_Emitter` via `object.__new__`, also explicitly initializes both
fields; the fresh isolated Task 23 mutation test passes.

## Closed-domain and forgery evidence

The loader covers absent, wrong, duplicate, foreign, extra-field,
compatibility-carrier, and global-capability mutations.  Direct validator and
emitter tests execute a literal Cartesian of every forged tree with
absent/wrong/exact carriers and exact/missing/wrong/attacker-recomputed caller
hashes.  The exact-tree control runs the same 3-by-4 matrix and accepts only
the exact carrier with the exact (or equivalently recomputed) source hash.
Tree forgeries cover the round node and its observable uses,
parent/declaration/site ownership, complete interface/resources, loop
statement/proof/program proof, caller hash, route spelling/nesting, and driver
analyzer laundering.

The non-GLSL construct gates use real fixtures rather than comment labels:

- recursion parses and types a real self-call, proves an acyclic control and
  `call_graph_acyclic == false` for the target, then validator rejection;
- allocation (`new float`), a function-pointer callback, and `throw` each have
  an accepted helper-call control and fail the total parser with
  `FrontendError`;
- a fixed `[2]` stack-array control parses and types, while a parsed
  `float values[n]` target fails semantic validation with `E_ARRAY_SIZE`.

The focused Task 24 suite passed all 10 tests in 112.561 seconds.  The Task 24
structural/native mutation harness proves production rejection before
test-only rendering and compiles/runs the rejected `floor`, `ceil`, 8-trip,
and `std::round` variants with exact native sensitivity.

## Resources, stack, and machine route

Typed resources are exactly the three sampler uniforms `preparedTex`,
`rankTex`, and `brightestTex`, plus output `fragColor`; texture use is true and
derivatives are false.  Mechanical generated-block assertions prove:

- `State` has exactly those three stored sampler pointers and the binder uses
  exactly those three roles;
- one `texture_size(*state.preparedTex)` call;
- one brightest static fetch before the loop, one rank fetch inside the loop,
  and one prepared-result fetch after it;
- one authenticated 64-trip loop and no `break`, `continue`, or return from
  that loop;
- 66 dynamic fetches derived as `1 + loop_proof.trip_count + 1`, not asserted
  as an unexplained constant.

Missing/extra State pointers, wrong fetch role, missing/extra fetch, and
texture-size/fetch LOD mutations all fail the same mechanical audit.

Generated-source extraction reports one `glsl::round`, one exact outer
`float_to_int32`, one texture-size call, three exact role fetches, one 64-trip
loop, and zero generated `main`, early-exit, direct cast, `std::round`,
`lround`, `nearbyint`, allocator, container, string, callback, exception, or
`alloca` route in `pixel`.

Fresh `.su` records give Gather `pixel` frames of 336 bytes static in Debug and
96 bytes static in Release, both far below 16 KiB.  ASan/UBSan reports a
1024-byte dynamic instrumentation frame; the non-sanitized builds establish
the production static bound.  Release ARM64 disassembly loads loop counter
`w26` with `0x40`, decrements it, and branches back on nonzero.  Relocations at
the authenticated conversion site call `noisemaker::glsl::round(double)` and
immediately then `noisemaker::glsl::detail::float_to_int32(double)`.  The
scoped pixel disassembly has no `blr`/`br` indirect branch, allocator,
deallocator, exception, or `alloca` target.

## Public native oracle evidence

Four normative public-factory cases cover positive zero, negative-zero
sign-erasure, half boundaries/endpoints, and width 67.  They freeze all three
input hashes/probes, complete F32/RGBA8 output hashes/probes, finiteness,
double-render identity, and input immutability.  Exact binding tests cover
missing/wrong/exact samplers and unrelated extras.

The signed-zero exclusion remains byte-identical to the positive-zero control.
The out-of-range clamp exclusion recomputes against its frozen canonical
reference and asserts both exact candidate/reference hashes, unequal flags,
218 differing F32 bytes, 64 differing F32 lanes, 61 differing RGBA8 bytes, and
maximum absolute difference `1.5454545319080353`.

## Verification

- Task 24 oracle generator `--check`: pass.
- Corpus check: pass.
- Semantic check: 212 bodies pass.
- Kernel generator `--check`: pass.
- Typed generator `--check`: 123 programs pass.
- Task 24 focused Python: 10 tests, pass.
- Task 23 rejected-structural-mutation harness: pass after explicit test-local
  emitter authorization initialization.
- Fresh Debug full CTest: pass.
- Fresh Release full CTest: pass.
- Fresh ASan+UBSan full CTest with `detect_leaks=0` and
  `halt_on_error=1`: pass.  Retrying `detect_leaks=1` aborts before tests with
  the expected macOS runtime diagnostic, `detect_leaks is not supported on
  this platform`.
- Final full Python discovery from current bytes: 141 tests in 514.093 seconds,
  pass.

No Git, branch, worktree, commit, push, or pull-request operation was used.
The stale Task 23 `gatherSorted`-unported assertion was removed from
`tests/test_typed_slice.cpp`; this is the minimal required admission cleanup,
and the remainder of that file is unchanged.

## Owned-file SHA-256 inventory

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/gather_sorted_round_profile.py` | `c96bc5a6abaa15fb0ca121eec9c7749396467ab3151ec7dbfead0fb9de89df69` |
| `tools/glslcpp/generate_typed_slice.py` | `a227a0119144f4572aa8628748432d43606742ec170651ed1bd493ef19f58d1f` |
| `tools/glslcpp/emit_typed_cpp.py` | `5beff60a0342a054abff3a975641782dcbcb14116dca9c3ba7ca408b3ffa371e` |
| `tools/glslcpp/typed_slice.json` | `e6a0bbe1cc1caef06d726e7040fcb8b1a205593d30885625aad6460e96b4747a` |
| `src/typed_generated/typed_slice.cpp` | `8d06f5864fbb6eca1eb205afc4f9690ec8f0ddd90a384e4f84a80fc50a0c3ea6` |
| `src/typed_generated/typed_manifest.json` | `bf7020628f988acd61128c527495e609cba7e74ee41bc44bfec7053bcd1187b5` |
| `include/noisemaker/generated/catalog.hpp` | `1ca4f356117d2067bb766b630d44e6c4075a3da60ac365f5f6b6a48b7d77d105` |
| `tests/test_typed_generator.py` | `8d653a85681f519c3e3c950330239019475de9740ca2bc0d836a1a159afc2698` |
| `tests/test_generated_kernels.cpp` | `ae903b176ac6bd38072f41940fb80df53ad957e1c9e1c3713464181450a54f79` |
| `tests/test_typed_slice.cpp` | `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6` |

Frozen inputs remain exact: brief `a5184121...`, design `8a93fe78...`, frontier
audit `fa4e0481...`, oracle generator `35d20a44...`, oracle JSON `07dd6f31...`,
and oracle report `b33894f0...`.
