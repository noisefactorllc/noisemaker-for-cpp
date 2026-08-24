# Task 22 CRT Final Implementation Review

## Verdict

**APPROVED**

No P0, P1, P2, or P3 finding remains on the final reviewed bytes.

This was an independent final implementation review. No Git command was used,
no branch/worktree/PR was created, and no repository file was modified by the
reviewer.

## Authenticated review inputs

| Artifact | SHA-256 |
| --- | --- |
| `task-22-brief.md` | `f8c5a9fdd18a5ca587dee47d7d297503325b1eea374a867f5e9ad8d196c57e59` |
| `task-22-implementation-design.md` | `1e347e6565ae37aecd5c2edf9db3b9fc851fe3b2591f253c9f57eaf409be63f1` |
| `task-22-oracles.json` | `c927f467418f9ef154a817869228a0918c2fc222ef3bb64f2b0a6bab8a74e889` |
| `task-22-oracle-generator.mjs` | `dc2044ee2bf007f1888f958a09185445caef34c064a6e4b3eea340a09ad49a27` |

The amended brief and design correctly distinguish transform-application
identity from standalone validation: application tests require each retained
raw argument object to be reused in the post-transform tree, while standalone
validator/emitter authentication requires exact fields/hashes and the shared
`turns` DAG identity without claiming it can distinguish an equal-field clone
of a retained argument across independent calls.

## Final owned-file census

| File | Final SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/crt_compatibility.py` | `703faf71656bf6a36afeb12ad12a4e8aa390b850aac4c9e79f9e527d4ad8c669` |
| `tools/glslcpp/generate_typed_slice.py` | `b8fade4315e3bb510163c18fc51c5ddc8ab3c20af6272dcc6e9a7f78b8412562` |
| `tools/glslcpp/emit_typed_cpp.py` | `9ee63f4aa7f2b15b52d6dc5b83fc9bc7ca6e2dcaa881787a60aa5bc784647bba` |
| `tools/glslcpp/typed_slice.json` | `c6683f5eaf782c53194f90f0ec2c3dd71436fc09b4c84ac12a83b79cfe1e2dd0` |
| `tests/test_typed_generator.py` | `c4c3be1d130611ebe790e7519dfd8067331d6494db99048d43bf0ed6c8f1893d` |
| `tests/test_typed_slice.cpp` | `f85ad92eecbd386d549eb85402a17e93a5a17c08c122c37e474fe9ae6d91dd3e` |
| `tests/test_generated_kernels.cpp` | `16dc18f60f28a94cb43b302e3df5d7bab3acabbcb58c98d447fcf0ce7bff8180` |
| `src/typed_generated/typed_slice.cpp` | `a3f8135d41e9f2abc864fada60532309b56c43f6e6eb138d548a23b57f944c4f` |
| `src/typed_generated/typed_manifest.json` | `8b5ba832204e6f346563e0ff721e4c7bd7cfcd5194df6f428347188eff35f680` |
| `include/noisemaker/generated/catalog.hpp` | `a96420439fbd3f4289335a08d0a6506687a6222e52cb052475bd01442cec0408` |

The implementation is confined to the six owned source/test files, one new
compatibility module, and three canonical generator outputs. Protected
semantic, typed-IR, proof, runtime, sampler, kernel, and CMake anchors retain
their accepted Task 21 hashes. No generic capability, proof, numeric mode,
sampler, ABI, or runtime feature was introduced.

## Transform and publication lock review

- CRT is admitted exactly once with transform carrier
  `crt-metal-sine-v1`. The transform authenticates exact raw inputs and changes
  exactly six intended `sin` sites into reduced-turn sine expressions. All six
  original argument objects are retained during application, each reduced-turn
  subtraction shares the same `turns` object with its `floor(turns)` child, all
  four `cos` sites remain untouched, and the other 30 functions remain equal.
- Validator and emitter independently authenticate the carrier, exact CRT
  structure, source/interface/function/whole-program hashes, six sites, and
  their typed fields. The complete four-mode matrix covers raw/transformed
  programs with missing, wrong, and exact carriers; caller-recomputed digests
  do not rescue structural drift.
- The final adversarial matrix rejects field drift in the inner and outer
  transform nodes, floor call/signature/order, literals/types/categories/spans,
  argument and local-symbol source changes, duplicate or seventh sine sites,
  shared-DAG clones, function movement/duplication, interface/resource/proof
  drift, loops/recursion/arrays, fetch count/ownership drift, and allocation,
  callback, exception, or dynamic-stack vocabulary.
- The matrix has coherent negative rewrites and positive controls. Its current
  five focused tests passed independently; no residual false positive or
  missing required row remains.
- The slice is sorted and unique at 116 entries. The public catalog is sorted
  and unique at 118 entries. Exactly 94 of the 212 corpus programs remain
  unported. CRT occurs once between Craquelure and Degauss. Exact typed/public
  list hashes are `76c81945ef992ed258900815335a23ae4f36d8756b7763ebd5e03d8562fde8e3`
  and `019a80df52192e3c898af58a5e3a2a9da654896eadde78097ce4a818579328f9`.
- Generated isolation is exact: all 19 blocks before CRT are raw-byte identical
  to Task 21, and all 115 pre-existing blocks are identical after normalizing
  only their required namespace ordinal. The isolated CRT block is 56,865
  bytes with SHA-256
  `c2cad79029847645cf230593c5251d3ebce5a4987d804d534b5227ac6c73cfbe`.

## Generated shape, ABI, and stack review

- The generated CRT namespace contains the six intended reduced-turn sine
  forms and four untouched cosine forms. It has one pixel entry, no generated
  C++ `main`, no loop or recursion, and no hot-path allocation, container,
  string, callback, exception, VLA/`alloca`, virtual, or indirect-dispatch
  route.
- Static fetch sites remain exactly four: one base, one red, one blue, and the
  helper definition. Runtime accounting remains one fetch on the alpha-copy
  path and three on the normal path.
- Binding tests reject every missing and wrong-typed required binding, accept
  the exact binding, and accept unrelated extras. All nine required values and
  the single sampler are covered.
- Fresh Debug and Release `.su` output classifies every CRT function as
  `static`. Representative Debug/Release frames are: `pixel` 2304/480 bytes,
  `compute_lens_offsets` 576/128, `animated_simplex_value` 560/128,
  `value_noise_3d` 1280/272, and `simplex_noise` 5104/352. The maximum reviewed
  CRT frame is 5104 bytes in Debug, below the 16 KiB warning threshold.

## Native oracle transcription and behavior

All 11 native fixtures were mechanically compared field-for-field with the
frozen JSON: names, dimensions, scalar/Vec2/seed words, all four input/output
F32 and RGBA8 hashes per case, 42 probe words per case, and all eight metrics
match. Native coverage authenticates repeat identity, input immutability,
finite output, exact copy on both alpha-zero routes, input-alpha preservation,
orientation/tile/full-resolution behavior, metadata boundaries, shadowed
locals, and the public Metal reduced-turn sine adapter. The 18 canonical
mutation sensitivities retain their required divergence and identity cases.

## Fresh final-byte verification

- `node task-22-oracle-generator.mjs --check`: pass.
- `python3 tools/glslcpp/check_corpus.py --check`: pass.
- `python3 tools/glslcpp/generate_typed_slice.py --check`: pass, 116 programs.
- Five focused Task 22 Python tests: 5/5 pass independently in 168.826 seconds;
  the implementation owner also reran the focused gate successfully.
- Full current Python suite: 77/77 pass independently in 429.284 seconds.
- Current Debug rebuild/CTest: 1/1 executable pass, 114 internal checks,
  2.23 seconds.
- Current Release rebuild/CTest: 1/1 executable pass, 114 internal checks,
  0.14 seconds.
- Current ASan/UBSan rebuild/CTest: 1/1 executable pass, 114 internal checks,
  6.93 seconds, with UBSan halt/stacktrace enabled and the reviewed
  Apple-runtime leak-detector waiver `detect_leaks=0`; no ASan or UBSan
  diagnostic was emitted.
- Final source, test, and generated-output hashes were reread after all test
  runs and match the census above.

## Review audit trail

The initial candidate was not approved. Independent adversarial review found
missing raw-to-post retained-argument identity coverage, incomplete four-mode
and structural matrices, shared-DAG-breaking test walkers, a wrong manifest
test path, incoherent local-source mutations, an ineffective fetch-count
mutation, insufficient fetch-owner/function/duplicate-site rows, and gaps in
literal/type/category/span checks. Each issue was reported before approval,
the implementation was revised, the exact latest bytes were rereviewed, and
both focused and full gates were rerun after the corrections.

No residual P0-P3 issue or missing completion evidence remains.
