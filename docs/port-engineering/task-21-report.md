# Task 21: Degauss typed CPU port

## Outcome

Task 21 ports `filter/degauss:degauss` into the generated C++ CPU slice with
no generic language, emitter, proof, compatibility, runtime, sampler, Surface,
or CMake change. The typed slice now contains exactly 115 generated programs,
the public catalog contains exactly 117 factories including the two handcrafted
factories, 95 of the 212 pinned corpus programs remain unported, and Degauss is
present exactly once at typed ordinal 19. CRT remains excluded.

The implementation changed exactly the eight approved repository paths. No
Task 22 work, Git operation, branch, worktree, pull request, publish, or deploy
was performed.

## Publication and fidelity contract

- `validate_current_vocabulary_degauss` authenticates the exact corpus entry,
  raw and normalized byte counts/hashes, empty defines, `glsl-f32`, absence of
  a compatibility transform, exact metadata, all 17 function IDs/names/body
  counts/function hashes, function-tuple/whole/interface hashes, declaration
  and resource ABI, zero-loop proof summary, and absence of all four foreign
  proof carriers.
- The exact `TAU` literal is narrowed and checked against F32 word
  `0x40c90fdb`. Canonical factory/runtime identities are retained as provenance
  constants only.
- The current capability, type, operator, compatibility-transform, and numeric
  literal vocabularies are unchanged; their combined fingerprint remains
  `dd4e14138c6ac72bbc37785faf361660edb418c38afabaf115d5b49d79999b4a`.
- `load_slice` enforces the Task 21 closed publication boundary: exactly one
  Degauss key and zero CRT keys, in addition to sorted uniqueness and count 115.
  Same-count missing-Degauss and admitted-CRT substitutions fail closed.
- A semantically valid typed-IR channel mutation is explicitly accepted by the
  generic validator and rejected by the Degauss publication profile, proving
  the profile is the operative source-identity boundary rather than an
  accidental generic-language rejection.

## Generated isolation and code shape

A pre-Task21 114-program specification is rebuilt in memory with the current
generator. All 19 blocks before Degauss are raw-byte identical. Across all 114
prior blocks, normalizing only `typed_[0-9]+` to a sentinel yields byte identity;
there is no other prior-program drift.

The generated Degauss namespace has no generated C++ `main`. Brace-scoped tests
cover `pixel`, `warped_channel_value`, `compute_noise_value`, `simplex_noise`,
`sample_bilinear`, `wrap_float`, and `wrap_index`. They lock:

- one nearest fetch in `pixel`, four bilinear fetches in `sample_bilinear`, and
  exactly one `integer_mod` site in `wrap_index`;
- three `warped_channel_value` calls with exact 0/1/2 channel routing;
- the exact helper edges through mask/frequency, noise/periodic/simplex,
  mod289/permute/taylor, bilinear, and wrap helpers;
- no allocation/deallocation, associative container, variant, string,
  callback, throw, `.at`, VLA, `alloca`, recursion, or indirect dispatch in the
  scoped hot bodies.

Static source accounting is five `texelFetch` AST sites. Runtime accounting is
one fetch on copy or mask-zero paths and at most 13 on the normal path: one
original fetch plus three four-fetch bilinear samples.

## Binding ABI and native parity

The public binder requires exactly nine resources/uniforms: `inputTex`,
`resolution`, `tileOffset`, `fullResolution`, `time`, `displacement`, `speed`,
`seed`, and `direction`. Every missing and wrong-type alternative is rejected;
unrelated extra uniform and sampler bindings are accepted and ignored.

All nine frozen direct-canonical cases from the authenticated
`canonicalFactory45` oracle are transcribed into native tests. Each case renders
twice with fresh input, preserves both input surfaces byte-for-byte, and checks
complete little-endian F32 and RGBA8 hashes, eight asymmetric top-down probes
with all four lane words, every frozen metric, and repeat identity. The cases
cover 4,228 output lanes; every lane is finite. The zero-displacement case is
an exact 1,872-byte F32 copy and preserves all 50 out-of-range-alpha pixels.
Normal-path alpha clamping, mask-zero identity, tiled/untiled, landscape/
portrait/square, positive/negative direction, seed/time/speed, zero full-
resolution fallback, and over-cap direct-binding behavior all match the
canonical oracle exactly.

## Stack, call-chain, and disassembly evidence

Fresh non-sanitized `.su` evidence classifies every reachable generated helper
as static:

| Function | Debug bytes | Release bytes |
| --- | ---: | ---: |
| `pixel` | 928 | 224 |
| `warped_channel_value` | 544 | 80 |
| `compute_noise_value` | 688 | 160 |
| `simplex_noise` | 5104 | 352 |
| `sample_bilinear` | 544 | 192 |
| `singularity_mask` | 240 | 64 |
| `freq_for_shape` | 160 | 48 |
| `mod289_vec3` / `mod289_vec4` | 272 / 320 | 64 / 80 |
| `permute` / `taylor_inv_sqrt` | 304 / 192 | 48 / 48 |
| `wrap_float` / `wrap_index` | 80 / 64 | 32 / 0 |
| `periodic_value` / `normalized_sine` | 64 / 48 | 16 / 16 |
| `as_u32` / `clamp01` | 48 / 48 | 16 / 16 |
| `fetch_texel` | 128 | 0 |

The maximum known non-inlined chain is `pixel -> warped_channel_value ->
compute_noise_value -> simplex_noise -> mod289_vec4`, bounded at 7,584 Debug
bytes and 896 Release bytes. Release has fixed prologues for `pixel` (`0xe0`),
`compute_noise_value` (`0xa0`), `simplex_noise` (`0x160`), and
`sample_bilinear` (`0xc0`); remaining hot helpers are fixed register/leaf
frames. Scoped Release relocation/disassembly evidence shows only direct calls,
zero `blr`, and no allocator/deallocator, VLA, or `alloca` target. Sanitizer
`.su` dynamic classifications are instrumentation-only and are not used as
resource proof.

## Red/green and final verification

- Initial profile RED produced the intended missing-helper errors and 114/115
  count failure. The exact identity/interface/tree mutation matrix then passed.
- Slice RED reached only canonical generated-output drift before `--write`;
  the canonical generator now passes `--check` at 115 programs.
- Independent review found a same-count loader substitution bypass. Exact RED
  reproduced both missing-Degauss and admitted-CRT acceptance. The final loader
  boundary and both regression cases are GREEN.
- Final focused Task 21 Python tests: 4/4 passed in 120.383 seconds; independent
  rerun: 4/4 passed in 155.125 seconds.
- Final full Python discovery on exact final bytes: 117/117 passed in 435.179
  seconds; independent rerun: 117/117 passed in 440.483 seconds.
- Task 21 oracle `--check`, corpus `--check`, semantic analysis of all 212
  bodies, handcrafted-kernel generation `--check`, typed generation `--check`,
  and every accepted Task 15-20 oracle `--check` passed.
- The current native suite passed with the Degauss binding and nine-case oracle
  tests. Fresh Debug and Release Unix Makefiles builds passed CTest 1/1; final
  current-byte reruns passed in 3.28 and 0.66 seconds respectively.
- Ninja was unavailable, so the accepted Unix Makefiles fallback was used with
  the exact stack and floating-point flags.
- Fresh ASan+UBSan build succeeded. Apple's ASan runtime rejected
  `detect_leaks=1` as unsupported before execution; the required
  `detect_leaks=0` rerun with ASan and UBSan halt/stacktrace enabled passed
  CTest 1/1, and the final current-byte rerun passed in 8.38 seconds.
- Independent final implementation review is APPROVED with no P0-P3 findings:
  `docs/port-engineering/task-21-final-implementation-review.md`, SHA-256
  `b52ed2c2a3c361fd07d0bfc2c537e0702aa05cefb03443e5ab2516f2615dcbaa`.

## Protected anchor census

All protected anchors retain the accepted Task 20 hashes:

| Protected file | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/semantic.py` | `01c772aae5732d048c11c28b93d18d00fce63f6373ecb294324773f5e8817f2b` |
| `tools/glslcpp/frontend/typed_ir.py` | `7e16d088d7ffe90b7b6cc11dfff27d9df413ff4ffcdd13f9648fc4c35c91272c` |
| `tools/glslcpp/emit_typed_cpp.py` | `f8c9c21a8bc0590e2af78b892dc7504a55aafd8987a41e367a73f66a8de4ea11` |
| `tools/glslcpp/frontend/fixed_nine_table_proof.py` | `712a98e5130545f6f3884a965e2e096bc07fa0fe0ed88b1549ff6733ecac85b1` |
| `tools/glslcpp/frontend/fixed_grid_counter_store_proof.py` | `2bada0deacf426f29a85a1d747eba6e62ff5c37b4d428a4a4ab40fc44aa3ffa1` |
| `tools/glslcpp/frontend/fixed_array_in_parameter_proof.py` | `fd27f974b6d34c32cd0837948cdc93b9683afb1d61fe3881ca5841d55b10d468` |
| `tools/glslcpp/frontend/fixed_affine_centers13_proof.py` | `ac82d95f7a79dacb9749a2241d15e92e533299c61bf97fbcf3e2c128226499bd` |
| `tools/glslcpp/frontend/refract_compatibility.py` | `4bb1384ea020f03c91ae28c6d3498f0b5525318fc7ba0a2c4eb926866e1a7050` |
| `tools/glslcpp/frontend/sacred_geometry_compatibility.py` | `96987d7418216113a712ab70e7180cf919e5c2942528cf00264f8777bc1ab0d4` |
| `include/noisemaker/sampler.hpp` | `abec1caeec36504c6f49c2fe9df64b218a2346bb0db2417000517e7f6f9e0fe9` |
| `include/noisemaker/kernel.hpp` | `9869f847eaa78c46d8a1507002ff87bae1d6417b46b06f931d4a7ed31401114f` |
| `CMakeLists.txt` | `bca6b4ab77d26c72449ef8d7a66d5832fdc939ebb35a85211b7684dde62216d5` |

## Exact Task 21 file inventory

| File | Task 20 SHA-256 | Final Task 21 SHA-256 |
| --- | --- | --- |
| `tools/glslcpp/typed_slice.json` | `bf86b4e7e5e26a89a27f23009eb5a7589618ec54b469b79ffa4cad343f66ccb0` | `e01050bd3e71df32df522da741a7087896fea500548bebe988f181bee4bfb802` |
| `tools/glslcpp/generate_typed_slice.py` | `ff9cc618c98255ed71714c0384e5f64b613a09f5540457cca4e38b133ad62594` | `ea51119950c7e7262282e57a85db895583125cc76d174d7acff51c57cea4dad1` |
| `tests/test_typed_generator.py` | `ece8739c40e37e7e9ac42054d4c647a1f4cdb2543bbd92ed0c2ec0dec275fb27` | `ea1b490eb75285e8fee77d24776725c37937d69db1c38e3bb15b8c3d5b99bb9b` |
| `tests/test_typed_slice.cpp` | `acfe7fe5483188b3936eb3d02b15f1187f185c2474f341996ce4d764f07b31a0` | `150dcd25ff794648299a9dcc83d875e9a29820784f13890aba276435e3640d61` |
| `tests/test_generated_kernels.cpp` | `fba30769e2ac4e66a173a9fc1c61c2ec920483c6b3b347e9377242d5c6b3035d` | `143b9b290ec135e7018af7b53c9fccc4183ec1f4f7fe1848e6f135c557120df5` |
| `src/typed_generated/typed_slice.cpp` | `3b56d4f69b4477c7306ac659ec6a59c64f0a929d72a56921c28eb9961e82eef8` | `986d6d3116497282e468440a6786be5728ee53f0558ea8c5a553831e353aa5ba` |
| `src/typed_generated/typed_manifest.json` | `8840aedc26a73c2af8e871cac4a2a41ffb8f107dbaea870902e9b22340614f41` | `53e8c04374876a26a4ed0cec47587ebe998eccc7ce33b817b8d6ef0a6d73a124` |
| `include/noisemaker/generated/catalog.hpp` | `292c212ffb77e2bc597749899c7211a8134027f556c6b6f5eb03412a037aef6a` | `bb3d7f78ac49eb026ebccb8a14fd2a23d94fb43f200a98245d271168499748d4` |
