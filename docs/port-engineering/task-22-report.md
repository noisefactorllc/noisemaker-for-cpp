# Task 22 CRT implementation acceptance report

Status: accepted. Independent implementation review approved the exact final
bytes with no residual P0-P3 finding.

## Scope delivered

- Added exactly `filter/crt:crt` using compatibility transform
  `crt-metal-sine-v1`.
- Preserved the pinned public CPU adapter's reduced-turn float32 sine behavior
  at exactly six authenticated scalar sites.
- Added no capability, proof kind/field, type, operator, builtin, numeric mode,
  runtime helper, sampler behavior, or adjacent program.
- Final counts are 116 typed factories, 118 public factories, 94 publicly
  unported programs, and 212 corpus programs.
- No Git, branch, worktree, commit, push, PR, Task 23 implementation, or
  deployment operation occurred.

## Frozen contract and review artifacts

- Task 22 amended brief:
  `f8c5a9fdd18a5ca587dee47d7d297503325b1eea374a867f5e9ad8d196c57e59`
- Task 22 implementation design:
  `1e347e6565ae37aecd5c2edf9db3b9fc851fe3b2591f253c9f57eaf409be63f1`
- Frontier audit:
  `c3d006f354f6ca9bb65c42b8e6f8bbdac194ddf1a6486ccbf890bfe818f16160`
- Oracle generator:
  `dc2044ee2bf007f1888f958a09185445caef34c064a6e4b3eea340a09ad49a27`
- Frozen oracle JSON:
  `c927f467418f9ef154a817869228a0918c2fc222ef3bb64f2b0a6bab8a74e889`
- Oracle report:
  `36ac4f8b85a0fefc47c403eef47bd11ceb40e9774fa709125f01bc4e2ea075aa`
- Final independent implementation review:
  `102a56ab642c1884319a827530639d0dc9943441393e03ea497274812912e5af`

## Final owned-file hashes

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/crt_compatibility.py` | `703faf71656bf6a36afeb12ad12a4e8aa390b850aac4c9e79f9e527d4ad8c669` |
| `tools/glslcpp/generate_typed_slice.py` | `b8fade4315e3bb510163c18fc51c5ddc8ab3c20af6272dcc6e9a7f78b8412562` |
| `tools/glslcpp/emit_typed_cpp.py` | `9ee63f4aa7f2b15b52d6dc5b83fc9bc7ca6e2dcaa881787a60aa5bc784647bba` |
| `tools/glslcpp/typed_slice.json` | `c6683f5eaf782c53194f90f0ec2c3dd71436fc09b4c84ac12a83b79cfe1e2dd0` |
| `tests/test_typed_generator.py` | `c4c3be1d130611ebe790e7519dfd8067331d6494db99048d43bf0ed6c8f1893d` |
| `tests/test_generated_kernels.cpp` | `16dc18f60f28a94cb43b302e3df5d7bab3acabbcb58c98d447fcf0ce7bff8180` |
| `tests/test_typed_slice.cpp` | `f85ad92eecbd386d549eb85402a17e93a5a17c08c122c37e474fe9ae6d91dd3e` |
| `src/typed_generated/typed_slice.cpp` | `a3f8135d41e9f2abc864fada60532309b56c43f6e6eb138d548a23b57f944c4f` |
| `src/typed_generated/typed_manifest.json` | `8b5ba832204e6f346563e0ff721e4c7bd7cfcd5194df6f428347188eff35f680` |
| `include/noisemaker/generated/catalog.hpp` | `a96420439fbd3f4289335a08d0a6506687a6222e52cb052475bd01442cec0408` |

## Acceptance evidence

- Frozen oracle generator `--check`: passed.
- Corpus check: passed.
- Typed generator `--check`: passed, exactly 116 programs.
- Focused Task 22 Python gate: 5/5 passed on final bytes.
- Full repository Python discovery: 122/122 passed on final bytes in 520.834s.
- Independent typed-generator Python review: 77/77 passed on the same final
  bytes.
- Debug fresh rebuild and CTest: passed, 1/1 executable and 114 internal
  checks.
- Release fresh rebuild and CTest: passed, 1/1 executable and 114 internal
  checks.
- ASan/UBSan fresh rebuild and CTest: passed, 1/1 executable and 114 internal
  checks. macOS does not support LeakSanitizer; the accepted run used
  `ASAN_OPTIONS=detect_leaks=0` while retaining AddressSanitizer and
  UndefinedBehaviorSanitizer.
- All 11 frozen CRT public-adapter cases passed exact full-F32 bytes, RGBA8
  bytes, seven probes per case, metrics, repeatability, input non-mutation,
  alpha preservation, and orientation checks.
- Binding ABI rejects every missing or wrong-typed value across the exact nine
  required bindings and accepts unrelated extras.
- Explicit catalog list, sortedness, uniqueness, counts, and projected list
  hashes passed.
- Generated isolation passed: all 19 pre-CRT blocks are raw-identical; all 115
  prior blocks are identical after namespace-ordinal normalization.
- CRT block is exactly 56,865 bytes with SHA-256
  `c2cad7e88fb817c311abb0041fec98d14c28ae3c3bd731b67944c745b8c295ec`;
  normalized namespace SHA-256 is
  `36410c4f25e2a0d53bba3bdc7164c18f74cc7f06de8f7589186da182b7246922`.
- Release stack usage records CRT `pixel` at 480 bytes, largest CRT helper at
  352 bytes, and binder at 160 bytes.
- The final negative matrix covers raw/post registration modes, all six sine
  sites and tree fields, shared-DAG identity, all 30 unchanged functions,
  interface/body/F32/shadow/output/fetch/loop drift, every metadata leaf,
  slice schema/catalog closure, and mutation-specific manifest drift with an
  authentic control.

## Review conclusion

Independent final implementation review: **APPROVED**. No residual P0-P3
finding and no missing acceptance evidence.
