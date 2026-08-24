# Task 27 independent implementation re-review

## Verdict

- **Production code: PASS**
- **Frozen implementation/test specification: PASS**
- **Original Important findings: 3/3 ADDRESSED**
- **New Critical findings: 0**
- **New Important findings: 0**
- **New Minor findings: 0**
- **Blockers: none**

This re-review was read-only with respect to the repository and Git state. The
fix report independently authenticates as
`f7a2af820025c27196fcd1083bc5d8ff2a083e0a4915ff88966487974bc7f985`.

## Original finding dispositions

### I1. Unsigned-versus-signed-JavaScript discriminator — ADDRESSED

`Task27WordCase` now carries both the source-unsigned and canonical signed-JS
numerator F32 bits at `tests/test_generated_kernels.cpp:7947-7950`; all twelve
frozen rows transcribe both fields at lines 7952-7965. The executable test at
lines 8011-8036:

- evaluates the selected result as unsigned;
- reinterprets its exact word as `std::int32_t` with `std::bit_cast` at line
  8018, avoiding an implementation-defined out-of-range unsigned conversion;
- asserts both frozen numerator bit patterns at lines 8021-8022; and
- requires exactly eight discriminating rows at line 8035.

The frozen oracle independently contains exactly eight such rows. Python
transcribes both fields at `tests/test_typed_generator.py:12023-12036` and has
independent literal-tamper witnesses for the unsigned and signed columns at
lines 12043-12053. The fix is executable, exact, and non-vacuous.

### I2. Exhaustive profile/validator/emitter negative closure — ADDRESSED

`tests/test_typed_generator.py:12055-12429` now defines 43 named unequal
candidates. The candidate/precondition key sets are required to match and the
suite requires at least forty candidates at lines 12313-12314. Every candidate
first satisfies its named structural precondition, then is separately rejected
by profile, validator, and emitter at lines 12316-12333.

The matrix covers source/raw/define drift including analyzer-produced
`DIMENSIONS=3`, interface/resources, declarations, functions/signatures/body
and ownership, exact expression operators/types/operands/path/span/category/
parent role, a third scalar site, call graph, loop proof, and unrelated proof
injection. The mandatory carrier matrix at lines 12335-12369 covers exact,
absent, foreign, mutated, foreign-tree, and wrong-caller-hash states. All seven
other carrier coordinates are combined with Perlin and independently rejected
by validator and emitter at lines 12371-12391.

Finally, the recursively reconstructed value-equal program at lines
12393-12429 is valid only after authenticating its own new objects. Both
validator and emitter reject forged authorization history returning the old
equal-looking objects. This directly tests the identity boundary rather than
merely relying on whole-program hashes.

### I3. Generated isolation and Task 26 reconstruction — ADDRESSED

The Task 27 delta test at `tests/test_typed_generator.py:11851-11988` removes
only Perlin and regenerates through the real pipeline. It authenticates the
three exact accepted Task 26 artifact hashes at lines 11870-11883, compares
all 126 historical blocks after only namespace-ordinal normalization at lines
11898-11910, compares all 126 manifest rows after excluding only the common
monolithic output hash at lines 11923-11947, proves the exact header delta at
lines 11949-11954, and proves the exact 129/128 catalog delta and all historical
mappings at lines 11956-11972. Current/prior typed and public ordered hashes
are authenticated at lines 11974-11988. Direct scalar XOR and Perlin carrier
leakage into historical blocks/rows are explicitly forbidden.

The stale Task 26 reconstruction is repaired at
`tests/test_typed_generator.py:10920-10946`: it first removes later Perlin to
recreate Task 26, asserts that precondition, and only then removes Smooth to
recreate Task 25. Its current Task 26 block count is correctly 126 at line
10963.

## Independent verification

Fresh re-review execution produced:

- Task 27 frozen oracle `--check`: PASS.
- corpus check: PASS.
- canonical generator `--check`: PASS, 127 programs.
- all eight `Task27PerlinTests`: PASS in 154.122 seconds.
- preserved fresh Debug build CTest rerun: 1/1 PASS in 2.91 seconds.
- preserved fresh Release build CTest rerun: 1/1 PASS in 0.22 seconds.
- preserved fresh ASan/UBSan build rerun with leak detection disabled only for
  the documented unsupported Apple facility and halt-on-error retained: 1/1
  PASS in 10.90 seconds.

The fix report's full-run evidence is coherent with the inspected tree: 172
Python tests, 136 native tests, fresh Debug/Release builds, and the first
sanitizer run preserving the exact unsupported `detect_leaks` diagnostic
before the supported retry.

## Scope and hashes

Only the two test files changed from the first review:

- `tests/test_generated_kernels.cpp`:
  `8263f5f3da3ed5cedad6a76e9a53d3f0c2fcfe92faec990125006a325d3c75cc`
- `tests/test_typed_generator.py`:
  `5cfbf4c72573887d68a097e3db6fd6cf6a32b74567b6fad2843945e7d92a4f13`

Production, schema, and generated outputs remain byte-identical to the first
review, including profile `6ef91678...`, generator `c9e4d84f...`, emitter
`2d14dda8...`, schema `20c39b7a...`, generated C++ `aa15e469...`, manifest
`f25401d4...`, and catalog header `b82abfa0...`. Frozen runtime, CMake, and
`tests/test_typed_slice.cpp` sentinels also remain unchanged.

No repository edit and no Git operation was performed by this re-review.
