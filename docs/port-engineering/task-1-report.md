# Task 1 report: C++20 foundation, Surface, and numeric fidelity primitives

## Scope and files created

Only `.` was created. No sibling repository was modified.

- `CMakeLists.txt` — C++20 project, `noisemaker-cpu` library, dependency-free test executable, CTest registration, and Clang/GCC warning-as-error flags.
- `.gitignore` — build, cache, editor, and swap-file artifacts only.
- `include/noisemaker/surface.hpp` and `src/surface.cpp` — checked RGBA float surface storage and byte conversion.
- `include/noisemaker/numeric.hpp` and `src/numeric.cpp` — float32, GLSL, uint32, bit reinterpretation, IEEE half, and float16 truncation contracts.
- `tests/test_harness.hpp` and `tests/test_main.cpp` — tiny dependency-free registration/assertion harness.
- `tests/test_surface.cpp` — dimensions, RGBA8 import/export, clear, and clone isolation vectors.
- `tests/test_numeric.cpp` — GLSL, uint32, PCG/hash, bit patterns, RTE half, and truncation vectors.

## Red phase

1. Behavioral tests and their CMake test target were written before either production header or source file existed.

   Command:

   ```sh
   cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
   ```

   Expected failure observed: CMake reported `src/surface.cpp` missing and therefore could not create the `noisemaker-cpu` target. This was the intended missing-production-implementation failure; no production source had been written yet.

## Green phase

1. Added the minimal `Surface` and numeric headers/sources necessary for the already-written behavioral API tests.

   First build attempt:

   ```sh
   cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug && cmake --build build --parallel && ctest --test-dir build --output-on-failure
   ```

   Result: project sources compiled warning-free, but the test build stopped at a comma in a `std::array<float, 4>` expression passed directly to the single-argument `REQUIRE` macro. This was a test preprocessor syntax error, not a production assertion failure.

2. Rewrote that expected color as a named local array, then reran the focused executable.

   Command:

   ```sh
   cmake --build build --target noisemaker-cpu-tests --parallel && build/noisemaker-cpu-tests
   ```

   Result: all nine focused behavioral tests passed.

3. Tightened bit/float16 expectations to literal independently derived values, including signed zero and the truncation-vs-RTE distinction, then reran the requested full commands.

   Command:

   ```sh
   cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
   cmake --build build --parallel
   ctest --test-dir build --output-on-failure
   ```

   Result: build completed with zero compiler warnings; CTest reported `1/1` test passing.

4. Final focused executable verification:

   ```sh
   cmake --build build --target noisemaker-cpu-tests --parallel && build/noisemaker-cpu-tests
   ```

   Result: all nine named tests passed.

## Full-suite result

`ctest --test-dir build --output-on-failure` completed successfully: `100% tests passed, 0 tests failed out of 1`.

## Self-review

- Surface dimensions reject zero and overflow before allocation; supplied data and RGBA8 byte spans require the exact checked channel count.
- Byte output explicitly maps all non-finite values to zero, clamps finite endpoints, and uses `floor(value * 255 + 0.5)` in the interior.
- Unsigned arithmetic stays in `std::uint32_t`; float/uint bit conversions use `std::bit_cast`.
- `float_to_half_rte` implements ties-to-even for normal and subnormal paths, while `float16_truncate` deliberately discards excess fraction bits and clamps finite overflow to signed half maximum.
- No `TODO`, `TBD`, or `FIXME` markers were found outside the disposable build directory.

## Concerns

None. The only intermediate failure after implementation was a corrected test-macro parsing issue; final project sources and all behavioral tests build and pass warning-free.

## Fix Round 1: missing-contract coverage and mutation validation

### Added tests and direct include

- `numeric_f32_narrows_double_to_ieee_float32` asserts the independently derived IEEE binary32 bit pattern `0x3dcccccd` for `f32(0.1)`.
- `surface_rejects_mismatched_constructor_data` asserts that a 1-by-1 Surface supplied with three float channels throws `std::invalid_argument`.
- `surface_rejects_mismatched_rgba8_data` asserts that a 1-by-1 RGBA8 import supplied with five bytes throws `std::invalid_argument`.
- `tests/test_harness.hpp` now directly includes `<utility>` for its use of `std::move`.

The production implementation already existed before these tests were added, so the following is mutation-based regression-sensitivity validation. It is not labeled as original red/green TDD and cannot retroactively alter the original sequence.

### Mutation: `f32`

Test: `numeric_f32_narrows_double_to_ieee_float32`.

Temporary mutation: changed `return static_cast<float>(value);` to `return static_cast<float>(value) + 1.0f;` in `src/numeric.cpp`.

Focused command:

```sh
cmake --build build --target noisemaker-cpu-tests --parallel && build/noisemaker-cpu-tests
```

Observed output (failure excerpt):

```text
FAIL numeric_f32_narrows_double_to_ieee_float32: tests/test_numeric.cpp:11: requirement failed: noisemaker::float_bits_to_uint(noisemaker::f32(0.1)) == 0x3dcccccdU
```

All eleven unrelated tests passed in that run. Restored the original `static_cast<float>(value)` implementation and reran the focused command; all twelve tests passed.

### Mutation: vector-constructor length guard

Test: `surface_rejects_mismatched_constructor_data`.

Temporary mutation: changed the constructor guard to additionally allow a three-float data vector:

```cpp
if (data_.size() != channel_count(width, height) && data_.size() != 3U)
```

Focused command:

```sh
cmake --build build --target noisemaker-cpu-tests --parallel && build/noisemaker-cpu-tests
```

Observed output (failure excerpt):

```text
FAIL surface_rejects_mismatched_constructor_data: tests/test_surface.cpp:19: expected exception std::invalid_argument
```

All eleven unrelated tests passed in that run. Restored the exact-length guard and reran the focused command; all twelve tests passed.

### Mutation: `from_rgba8` length guard

Test: `surface_rejects_mismatched_rgba8_data`.

Temporary mutation: changed the import guard to additionally allow a five-byte span for the 1-by-1 test:

```cpp
if (bytes.size() != count && bytes.size() != 5U)
```

Focused command:

```sh
cmake --build build --target noisemaker-cpu-tests --parallel && build/noisemaker-cpu-tests
```

Observed output (failure excerpt):

```text
FAIL surface_rejects_mismatched_rgba8_data: tests/test_surface.cpp:24: expected exception std::invalid_argument
```

All eleven unrelated tests passed in that run. Restored the exact-length guard, then reran the focused executable and CTest.

Focused result: all 12 named tests passed.

Full-suite command:

```sh
ctest --test-dir build --output-on-failure
```

Full-suite result:

```text
100% tests passed, 0 tests failed out of 1
```


---

**Correction (2026-08-30):** this report described the half conversion as IEEE round-to-nearest-even (`float_to_half_rte`). The independent publication review proved the JS authority `floatToHalf` rounds half-up with subnormal pre-truncation; the port diverged on 8,420,351 of 2^32 float32 inputs and the suite pinned the wrong value. The function is now `float_to_half_js`, a verified transcription (exhaustive 2^32 differential, 0 divergent), and `half_to_float` now canonicalizes NaN like the authority (65,536-code differential, 0 divergent). See .superpowers fix-3 lane report of the 2026-08-29 publication review.
