# Task 27 Perlin Scalar Uint XOR Implementation Report

## Result

**IMPLEMENTED AND VERIFIED; READY FOR INDEPENDENT IMPLEMENTATION REVIEW.**

Task 27 adds exactly `synth/perlin:perlin` under
`perlin-scalar-uint-xor-v1`. The new exact profile authenticates only the two
nested scalar `uint ^ uint` objects in unreachable `hash3`; validator and
emitter authenticate independently and emit the ordinary left-associated
`std::uint32_t` word expression. No generic scalar-bitwise capability, helper,
runtime overload, `DIMENSIONS=3` row, parser/IR/runtime change, or Git operation
was introduced.

## Frozen package

| Artifact | SHA-256 |
| --- | --- |
| `task-27-brief.md` | `cb63edbc129eaab3c963ac333b2079c15db4fee019564427173114dca1806c54` |
| `task-27-oracle-generator.mjs` | `95e9c5da0d0284f33ffcd0579c014ef29a7761785fed30d4047a75a1107dfd1e` |
| `task-27-oracles.json` | `27e12edfdec79a9f1ad9c07d3d076da2553e36f63d8c9a5ac43c1bc1592bcc54` |
| `task-27-oracle-report.md` | `9686b2107312f327ce898d438fe849b7bc7298158885d252210e76a72a3721b2` |
| `task-27-implementation-design-final.md` | `c6abf725ad560cdee02de716df98fa977ab4cefcaafea07860ac7ee5cd8f1218` |
| `task-27-design-preflight-report.md` | `9c3545bdd79d3c6aac0f82403848df4f0e0fb6441d3205287e0f144abf8b870c` |
| `task-27-design-review-final.md` | `b171a64bbf18c21173920e51923703101cbcf497ca54e15465e61767d20a2de9` |

`node task-27-oracle-generator.mjs --check` passed before implementation and
at the final gate. All Task 15 through Task 27 oracle generators passed their
current `--check` command.

## Strict TDD evidence

1. **Profile RED:**
   `python3 -m unittest ...Task27PerlinTests.test_task27_profile...`
   failed with `ModuleNotFoundError: ...perlin_scalar_uint_xor_profile`.
   **GREEN:** exact profile/authenticator and identity apply passed.
2. **Schema RED:** after adding the frozen row, focused loader test failed
   `GeneratorError: typed slice programs are invalid` because the carrier was
   unknown. **GREEN:** narrow row schema, exact one-carrier census, 127 count,
   position, define, and ordered hash passed.
3. **Validator RED:** exact call failed `TypeError: validate_capabilities() got
   an unexpected keyword argument 'perlin_scalar_uint_xor_profile'`.
   **GREEN:** independent object-identity admission, mandatory carrier, exact
   twice-visited completion check, and foreign/other scalar rejection passed.
4. **Emitter RED:** exact call failed `TypeError: render_typed_cpp() got an
   unexpected keyword argument 'perlin_scalar_uint_xor_profile'`.
   **GREEN:** independent authentication and direct left-nested spelling
   passed; no scalar `glsl::bitwise_xor` lowering exists.
5. **Generation RED:** Perlin was absent because the new identity carrier was
   not wired through apply/validator/emitter/manifest. **GREEN:** 127 blocks,
   one Perlin block, binder, manifest field, and public declaration passed.
6. **Native/catalog/word RED:** warnings-as-errors compilation failed three
   times on missing `bind_synth_perlin_perlin`. **GREEN:** canonical
   regeneration compiled and the full native executable passed.
7. **Status-count RED:** canonical write exposed the stale hardcoded message
   `typed slice ok (126 programs)` despite independently proved 127 spec rows,
   127 manifest rows, and 127 blocks. The status now derives from
   `len(load_slice()["programs"])`; `--check` reports exactly 127.

The first full Python discovery found 11 stale retrospective Task 21-26
census/list/isolation assertions. They were test-only phase reconstruction
issues: current-tree checks were advanced to 127/129/83 and frozen historical
phase checks now explicitly remove Perlin. All 11 focused gates then passed in
606.531 seconds before the clean full rerun.

## Implementation and negative closure

The profile independently locks raw/normalized bytes and hashes, exact
`DIMENSIONS=2`, whole program/interface/function fingerprints, exact `hash3`
owner/body, return/constructor parent, both site spans/hashes/categories/types,
three ordered `q` swizzles, exactly two scalar XORs, proof-carrier absence,
2/0/1/8/28 loop proof, reachable/unreachable partition, and exactly three
`grad3 -> hash3` calls with no reachable call.

Validator and emitter each require the exact exclusive carrier, retain the two
authenticated object identities, admit/emit each once, and reject missing,
wrong, foreign, combined, reconstructed, operator-mutated, reassociated, or
operand-swapped trees. Focused profile/validator/emitter/generation/table tests
passed 7/7 in 38.355 seconds.

The native word harness has six explicit enum/switch arms: exact left XOR,
outer OR, inner OR, outer AND, inner AND, and right-associated XOR. Every arm
records mode, intermediate word, result, and association; the default path
throws. All 12 frozen triples authenticate inner/result words, numerator F32
bits, ratio F64 bits, all five mutation words, OR/AND divergence, and
right-associated value identity with a distinct witness. Python parses the C++
case/word/enum/switch tables one-to-one against frozen JSON and proves case,
word, and mode tampering changes the authenticated table.

## Catalog and generation isolation

| Measure | Final |
| --- | ---: |
| Corpus | 212 |
| Typed | 127 |
| Public | 129 |
| Unported | 83 |
| Perlin typed ordinal | 123 |
| Typed ordered SHA-256 | `ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72` |
| Public ordered SHA-256 | `37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883` |

Removing only Perlin from the live spec reproduced the exact accepted Task 26
generated artifacts:

| Artifact | Reconstructed Task 26 SHA-256 |
| --- | --- |
| `typed_slice.cpp` | `df4aa212f312dcaf12bc348df1b1449a25db52542c97d0bc0350a7a2162b2d38` |
| `typed_manifest.json` | `e7f7acd56c96951d5610276cb72ad2df19637f142ae08022b92c2c718a7e7def` |
| `catalog.hpp` | `557ccdbee5a58ff6129269ad4a4dfdc25486b8a9f8c455da2bf2c8663d55527d` |

All 126 historical program blocks are byte-identical after normalizing only
the generated namespace ordinal. All 126 historical manifest rows are
semantically identical after excluding the common monolithic output hash.

Final generated `hash3` contains exactly two direct scalar ` ^ ` tokens, one
unchanged vector `glsl::bitwise_xor`, the unchanged float-constructor boundary,
and the exact ordered operands. The Perlin block contains exactly three static
`hash3(state, context, ...)` call sites owned by unreachable `grad3`.

## Native pixel and ABI verification

All eight frozen public cases passed exact full F32 SHA-256, full RGBA8
SHA-256, all five probes, width/height, repeat identity between public catalog
and direct binder, finite-lane census, and alpha behavior. The cases cover
mono/RGB, one/four/six octaves, ridges, zero/one/four warps, nonzero tile
offset, larger full resolution, speed-zero time control, and the 1024 full
resolution fallback.

All fourteen required bindings reject both missing values and wrong variants.
`DIMENSIONS` is compile-time only and is not a runtime binding.

## Full verification

| Gate | Result |
| --- | --- |
| Corpus check | PASS |
| Canonical generator `--check` | PASS, reports 127 programs |
| Full Python discovery | **171/171 PASS in 1231.324s** |
| Fresh Debug warnings-as-errors build / CTest | PASS, 1/1 in 2.10s |
| Fresh Release warnings-as-errors build / CTest | PASS, 1/1 in 0.31s |
| Fresh ASan/UBSan build | PASS |
| ASan first leak attempt | Preserved expected Apple abort: `detect_leaks is not supported on this platform` |
| ASan/UBSan retry, leak detection off, halt-on-error | PASS, 1/1 in 6.10s |
| Task 15-27 oracle checks | PASS |

Final stack usage from a fresh `-fstack-usage` compile:

| Function | Debug | Release | Bound |
| --- | ---: | ---: | ---: |
| `hash3` | 576 B | 64 B | 640 / 96 B |
| `pixel` | 608 B | 96 B | 704 / 128 B |
| maximum Perlin helper | 608 B | 144 B | 640 / 192 B |

The isolated Release AArch64 `hash3` range has the existing three vector-lane
shift-XOR `eor` operations, then exactly two terminal word reductions at
`0x61c70` and `0x61c74`, immediately followed by unsigned `ucvtf` at
`0x61c78`. There is no `scvtf` in that terminal conversion and no indirect
branch. The frame is fixed 64 bytes. No scalar XOR helper call/symbol,
per-pixel heap allocation, VLA, `alloca`, exception path, callback, virtual, or
indirect dispatch was introduced. The existing binder `make_shared<State>` is
setup-time only.

## Final owned-file hashes

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/perlin_scalar_uint_xor_profile.py` | `6ef916782a4f76c09fd1eff064f6fe6b589c6371b8687b0b4a99d6e7ea4f671f` |
| `tools/glslcpp/generate_typed_slice.py` | `c9e4d84febaaf6e5e767e3014ba7f26de4e268cbe3b6746d099acf86906f1eca` |
| `tools/glslcpp/emit_typed_cpp.py` | `2d14dda82e55c45117fa911d6d387be5cb4e1f24ddd5dfe6f17574f5bc752f36` |
| `tools/glslcpp/typed_slice.json` | `20c39b7a1d91c203e3a5f9c8ba22e9b061d2a73d62c0b710e56aa9fa3c52a213` |
| `tests/test_typed_generator.py` | `f172abfddd65db381e2c4db39ac4ecf3f88b8e7cdd4d4a25255f25f6c013e238` |
| `tests/test_generated_kernels.cpp` | `2bb473ca896ff5eee7e1382abe8109f61cb5a9f3fd8f26a403418380a7b42250` |
| `src/typed_generated/typed_slice.cpp` | `aa15e469d2283ac4f919a3f61edf85f5046f414674ff3cebdb85e5c06d2327c5` |
| `src/typed_generated/typed_manifest.json` | `f25401d49121ad6dcda189730b6e99ca5946fb0fafd2fbac83c637740ea1cd58` |
| `include/noisemaker/generated/catalog.hpp` | `b82abfa09c224185a4152d487d290d9b6bc475bb15ae744ddc3550c86ded1da5` |

Frozen sentinels remain unchanged:

- `tests/test_typed_slice.cpp`:
  `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6`
- `include/noisemaker/glsl_types.hpp`:
  `37e71f566d5b8d5e1abf68fee1b27338898e4afacb116764824274dfda6780d8`
- `CMakeLists.txt`:
  `bca6b4ab77d26c72449ef8d7a66d5832fdc939ebb35a85211b7684dde62216d5`

## Concerns and blockers

No implementation blocker is known. `hash3` is deliberately unreachable for
the exact public `DIMENSIONS=2` profile; public image equality proves
reachability only, while the independent executable direct-word harness and
code/disassembly authentication prove the scalar expression. This profile
must not be reused as evidence for public-JavaScript behavior under
`DIMENSIONS=3`.

No Git operation was run.
