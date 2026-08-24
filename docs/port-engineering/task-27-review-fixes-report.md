# Task 27 independent-review fixes

## Scope and review authentication

This test-only repair addresses all three Important findings in
`task-27-implementation-review.md`, SHA-256
`4513c6f396040b665ced08437aebc1355a829946e8e10009766ae34ba94947ca`.
No production, generator, schema, or generated artifact changed.

## I1: executable unsigned-versus-signed discriminator

- `Task27WordCase` now stores the frozen unsigned and canonical signed-JS
  numerator F32 bit patterns.
- All twelve rows transcribe both oracle fields. Python independently parses
  and compares both columns and has literal-tamper witnesses for each.
- Native execution interprets the result word as `std::int32_t` through
  `std::bit_cast`, avoiding an implementation-defined out-of-range unsigned
  cast, compares every signed bit pattern, and requires exactly 8/12
  signed-versus-unsigned discriminating rows.
- RED: the Python transcription test failed because the C++ rows were one
  field short. GREEN: focused Python transcription plus full native suite.

## I2: exhaustive negative closure

- The Task 27 closure now contains 42 named, unequal single-axis candidates.
  Every candidate has a named structural precondition checked before its
  rejection at each of profile, validator, and emitter boundaries.
- Covered axes: key; normalized/raw source; define name/value/kind/count/order;
  analyzer-produced `DIMENSIONS=3`; body status; declaration order/name/count;
  interface/builtin/resource shape; function count/order/id/name/return,
  parameter and body/owner; operator/association/operand order; source path,
  span, category and parent role; signed, mixed, vector/scalar and third XOR;
  call graph; loop count/charge/acyclicity; and unrelated proof injection.
- The mandatory matrix covers exact/absent/foreign/mutated trees, foreign
  programs, and wrong caller hashes. All seven other carrier coordinates are
  tested in combination with the Perlin carrier at validator and emitter.
- A value-equal recursively reconstructed program is admitted under its own
  freshly authenticated objects, but both validator and emitter reject it
  when authorization history is forged to return the original equal-looking
  objects.
- RED: an explicit closure-size assertion failed at 4 candidates. GREEN: all
  candidates, matrices, and independent identity-history checks passed.
- No production rejection gap was exposed.

## I3: exact Task 27 isolation and repaired Task 26 reconstruction

- The Task 26 isolation test now explicitly removes later Perlin first to
  recreate Task 26, then removes Smooth to recreate Task 25.
- The Task 27 isolation test removes only Perlin and regenerates through the
  real pipeline. It authenticates exact Task 26 artifact hashes:
  - C++: `df4aa212f312dcaf12bc348df1b1449a25db52542c97d0bc0350a7a2162b2d38`
  - manifest: `e7f7acd56c96951d5610276cb72ad2df19637f142ae08022b92c2c718a7e7def`
  - catalog header: `557ccdbee5a58ff6129269ad4a4dfdc25486b8a9f8c455da2bf2c8663d55527d`
- It compares all 126 historical blocks after only namespace-ordinal
  canonicalization, all 126 manifest rows after only common output-hash
  exclusion, every historical catalog mapping, and the exact header delta.
  It proves no historical direct scalar XOR or Perlin carrier, exactly one
  Perlin carrier owner/declaration/mapping, 127/126 typed and 129/128 public
  counts, and current/prior ordered-key hashes.
- RED: the stale Task 26 test failed its explicit no-Perlin precondition; the
  new Task 27 isolation test first failed as unimplemented. Both are GREEN.

## Verification

- Focused Task 27 plus repaired Task 26 isolation: 9/9 PASS in 237.336s.
- Full Python: `python3 -m unittest discover -s tests -v` — 172/172 PASS in
  1601.931s.
- Build plus full native executable: 136/136 PASS.
- Fresh AppleClang 16 warnings-as-errors Debug tree
  `/tmp/noisemaker-for-cpp-task27-review-debug.cusrCJ`: configure/build exit 0;
  CTest 1/1 PASS in 2.63s.
- Fresh AppleClang 16 warnings-as-errors Release tree
  `/tmp/noisemaker-for-cpp-task27-review-release.9wSSI3`: configure/build exit 0;
  CTest 1/1 PASS in 0.47s.
- Fresh ASan/UBSan tree
  `/tmp/noisemaker-for-cpp-task27-review-sanitize.M1pa3d`: configure/build exit
  0. The required first run with
  `ASAN_OPTIONS=detect_leaks=1:halt_on_error=1` and
  `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1` preserved the expected
  Apple host result (CTest exit 8, abort in 0.63s):
  `AddressSanitizer: detect_leaks is not supported on this platform.` The
  supported retry with `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1` and the
  same halt-on-error UBSan options exited 0, CTest 1/1 PASS in 7.10s.
- `python3 tools/glslcpp/generate_typed_slice.py --check` — PASS, 127 programs.
- `python3 tools/glslcpp/check_corpus.py --check` — PASS.
- `node docs/port-engineering/task-27-oracle-generator.mjs --check` —
  PASS for the frozen JSON and report.

Production/generated SHA-256 values remain exactly:

- profile `6ef916782a4f76c09fd1eff064f6fe6b589c6371b8687b0b4a99d6e7ea4f671f`
- generator `c9e4d84febaaf6e5e767e3014ba7f26de4e268cbe3b6746d099acf86906f1eca`
- emitter `2d14dda82e55c45117fa911d6d387be5cb4e1f24ddd5dfe6f17574f5bc752f36`
- slice schema `20c39b7a1d91c203e3a5f9c8ba22e9b061d2a73d62c0b710e56aa9fa3c52a213`
- generated C++ `aa15e469d2283ac4f919a3f61edf85f5046f414674ff3cebdb85e5c06d2327c5`
- manifest `f25401d49121ad6dcda189730b6e99ca5946fb0fafd2fbac83c637740ea1cd58`
- catalog header `b82abfa09c224185a4152d487d290d9b6bc475bb15ae744ddc3550c86ded1da5`

Changed test SHA-256 values:

- `tests/test_generated_kernels.cpp`
  `8263f5f3da3ed5cedad6a76e9a53d3f0c2fcfe92faec990125006a325d3c75cc`
- `tests/test_typed_generator.py`
  `5cfbf4c72573887d68a097e3db6fd6cf6a32b74567b6fad2843945e7d92a4f13`

No Git operation was performed.
