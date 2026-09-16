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
