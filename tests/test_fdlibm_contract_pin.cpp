// Pins the CMakeLists.txt override that compiles src/fdlibm.cpp with
// -ffp-contract=fast (against this project's otherwise project-wide
// -ffp-contract=off). See the CMakeLists.txt comment on that
// set_source_files_properties() call, and
// docs/port-engineering/v8-math/v8-math-report.md, for why this is
// required for bit-exactness with V8 rather than a portability hazard.
//
// This test does not re-read the CMake comment -- it exercises the ACTUAL
// compiled behavior of the fdlibm translation unit at a specific double
// input where contraction on vs. off is known (and, at this input,
// verified against real V8/Node) to produce two DIFFERENT last-bit
// results. If a future refactor ever drops the per-source COMPILE_OPTIONS
// override (e.g. during a CMakeLists.txt reorganization) and this TU
// silently falls back to the project-wide -ffp-contract=off, this test
// fails loudly with the off-by-one-ULP result instead of the flag drift
// going unnoticed until a pixel-parity regression surfaces far away from
// its cause.
//
// Provenance of the pinned value: x = bit pattern 0x3fd62e42fefa39c5.
//   Math.expm1(x) in this environment's V8 (node --v8-options confirms
//   the same fdlibm path is active; see fdlibm.hpp's provenance comment)
//   returns the double whose bits are 0x3fda827999fceef6 -- captured via
//   `node -e` against a DataView-constructed bit pattern, not retyped by
//   hand from an old report.
#include "test_harness.hpp"

#include <bit>
#include <cstdint>

#include "noisemaker/fdlibm.hpp"

TEST(fdlibm_contract_pin_expm1_matches_v8_fma_contracted_result) {
  const double x = std::bit_cast<double>(std::uint64_t{0x3fd62e42fefa39c5ULL});
  const double result = noisemaker::fdlibm::expm1(x);
  const auto bits = std::bit_cast<std::uint64_t>(result);
  // V8 Math.expm1 at this x, captured directly from `node -e` in this
  // environment (see file header). If this TU were compiled with
  // -ffp-contract=off instead of the mandated per-source override, the
  // computed value here is 0x3fda827999fceef7 -- 1 ULP away -- not this.
  REQUIRE(bits == 0x3fda827999fceef6ULL);
}

// Pins kernel_tan_combine's noinline extraction (src/fdlibm.cpp). Both
// inputs below were measured divergent (1 ULP from V8) before that
// extraction existed: the "small" input never touches
// __ieee754_rem_pio2 at all (|x| <= pi/4, kernel_tan's direct iy=1
// return), and the "large" input goes through the full argument
// reduction. Both are needed because the noinline boundary's effect on
// clang's -ffp-contract=fast auto-fusion heuristic was found (by
// differential bisection over 2,000,000 inputs, see
// docs/port-engineering/v8-math/v8-math-report.md) to depend on
// surrounding code shape -- a regression that only reintroduced the
// residual in ONE of kernel_tan's branches would otherwise go unnoticed
// by a single-input pin.
TEST(fdlibm_contract_pin_tan_small_bypass_matches_v8) {
  const double x = std::bit_cast<double>(std::uint64_t{0x3fdca1f6cacd184cULL});
  const double result = noisemaker::fdlibm::tan(x);
  const auto bits = std::bit_cast<std::uint64_t>(result);
  // Math.tan(0.4473855) captured via `node -e` in this environment.
  // Before kernel_tan_combine existed (the two combining lines inlined
  // directly in kernel_tan), this TU computed 0x3fdeb59bfb8f7a09 here --
  // 1 ULP away -- under this project's mandated -ffp-contract=fast.
  REQUIRE(bits == 0x3fdeb59bfb8f7a08ULL);
}

TEST(fdlibm_contract_pin_tan_large_reduction_matches_v8) {
  const double x = std::bit_cast<double>(std::uint64_t{0xc087d64e1c088d03ULL});
  const double result = noisemaker::fdlibm::tan(x);
  const auto bits = std::bit_cast<std::uint64_t>(result);
  // Math.tan(-762.7881394069703) captured via `node -e`. Before
  // kernel_tan_combine, this TU computed 0x3fe6ca721f28ce6a here.
  REQUIRE(bits == 0x3fe6ca721f28ce69ULL);
}

// Pins log_combine_a's noinline extraction (src/fdlibm.cpp). This input
// specifically discriminates the fix from the FIRST (rejected) attempt at
// it: an explicit std::fma() at this site reaches this exact bit on
// arm64 too, but regresses x86-64 (measured 180/2,000,000 divergent)
// because std::fma() fuses unconditionally on every architecture, while
// V8's own x86-64 binary does not fuse this expression at all (no
// hardware FMA at this project's x86-64 baseline). Only the noinline
// extraction (no explicit fma, ambient -ffp-contract=fast auto-fusion
// decides per architecture) reaches 0/2,000,000 on both arm64 and
// x86-64; see the report for that architecture-split measurement.
TEST(fdlibm_contract_pin_log_matches_v8) {
  const double x = std::bit_cast<double>(std::uint64_t{0x40769487cdb54080ULL});
  const double result = noisemaker::fdlibm::log(x);
  const auto bits = std::bit_cast<std::uint64_t>(result);
  // Math.log(186.58...) captured via `node -e`. Before log_combine_a/b
  // existed, this TU computed 0x40178f038f1e25b3 here on arm64 (1 ULP
  // away) under -ffp-contract=fast.
  REQUIRE(bits == 0x40178f038f1e25b4ULL);
}
