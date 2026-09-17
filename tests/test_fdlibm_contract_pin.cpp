// Pins src/fdlibm.cpp's fused-multiply-add sites, which reproduce V8's
// arm64 binary's genuine hardware FMA usage at specific polynomial and
// argument-reduction expressions. This file's mechanism changed
// 2026-09-17: fdlibm.cpp used to rely on an ambient
// `-ffp-contract=fast` CMakeLists.txt override plus `noinline`
// extraction tricks to coax the OPTIMIZER into fusing the right sites --
// which broke in a Debug (-O0) build, because the LLVM passes that
// perform that contraction do not run at -O0 (confirmed directly: bare
// `a*b+c` under `-ffp-contract=fast` emits one `fmadd` on arm64 at -O2
// but separate `fmul`+`fadd` at -O0). fdlibm.cpp now selects fusion
// EXPLICITLY, per call site, via a file-local `fma_()` helper chosen at
// COMPILE TIME per architecture (aarch64: std::fma(); everywhere else:
// plain `a*b+c`) -- see that helper's comment in src/fdlibm.cpp. This
// does not depend on the optimizer at all, so every test below now
// passes identically in Debug and Release.
//
// These tests do not re-read that comment -- they exercise the ACTUAL
// compiled behavior of the fdlibm translation unit at specific double
// inputs where fused vs. unfused arithmetic is known (and, at each input,
// verified against real V8/Node) to produce two DIFFERENT last-bit
// results. If a future refactor ever breaks the fma_() dispatch --
// dropping a fma_() call, swapping which architecture gets which branch,
// or reintroducing a dependency on ambient contraction -- these tests
// fail loudly with the wrong-by-one-ULP result instead of the bug going
// unnoticed until a pixel-parity regression surfaces far away from its
// cause.
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

// Forward declaration of src/fdlibm.cpp's test-only exposure of its
// internal fma_() dispatch (see that file's comment on `namespace
// testing`). Deliberately not part of the public fdlibm.hpp: it exists
// only so this test file can exercise the real, compiled dispatch
// instead of a second, independently-written copy of the same
// architecture check that could itself drift out of sync.
namespace noisemaker::fdlibm::testing {
double fma_probe(double a, double b, double c) noexcept;
}  // namespace noisemaker::fdlibm::testing

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

// Pins log_combine_a's fused site (src/fdlibm.cpp). This input
// specifically discriminates the correct, architecture-gated fma_() call
// from an EARLIER, rejected design: an unconditional `std::fma()` at this
// site reaches this exact bit on arm64 too, but regresses x86-64
// (measured 180/2,000,000 divergent) because `std::fma()` fuses on every
// architecture regardless of hardware support (calling a software
// correctly-rounded emulation where there is no hardware FMA), while
// V8's own x86-64 binary does not fuse this expression at all (no
// hardware FMA at this project's x86-64 baseline). Only fma_()'s
// architecture gate -- fuse on aarch64, stay plain everywhere else --
// reaches 0/2,000,000 on both arm64 and x86-64; see the report for that
// architecture-split measurement.
TEST(fdlibm_contract_pin_log_matches_v8) {
  const double x = std::bit_cast<double>(std::uint64_t{0x40769487cdb54080ULL});
  const double result = noisemaker::fdlibm::log(x);
  const auto bits = std::bit_cast<std::uint64_t>(result);
  // Math.log(186.58...) captured via `node -e`. Before log_combine_a/b
  // existed, this TU computed 0x40178f038f1e25b3 here on arm64 (1 ULP
  // away) under -ffp-contract=fast.
  REQUIRE(bits == 0x40178f038f1e25b4ULL);
}

// Directly exercises src/fdlibm.cpp's `fma_()` dispatch (via the
// testing::fma_probe forwarder it defines for exactly this purpose) at an
// (a, b, c) triple chosen so fused and unfused arithmetic are NOT just
// off by a rounding hair, but produce two grossly different values --
// a genuinely fused result is a fully-fused single rounding of the exact
// mathematical a*b+c, while separately rounding a*b THEN adding c loses
// nearly all of it to catastrophic cancellation:
//   a = 0x3ff0000000000001 (1 + 2^-52), b = 0x3feffffffffffffe (1 - 2^-52),
//   c = 0xbff0000000000000 (-1.0)
//   fused:   round(a*b + c) = -4.930380657631324e-32 (0xb970000000000000)
//   unfused: round(round(a*b) + c) = 0.0 (0x0) -- a*b rounds to exactly
//     1.0 in double precision (the 2^-104 cross term underflows the
//     mantissa), so the unfused path cancels ENTIRELY against c.
// Verified directly with Python's math.fma (a correctly-rounded fused
// primitive independent of this codebase) against the plain `a*b+c`
// double expression, both ways, before writing this test.
//
// This is not redundant with the three tests above: those pin ONE
// architecture-specific bit pattern per function, so a bug that swapped
// the aarch64/x86-64 branches of fma_() -- or that made BOTH branches
// resolve to the same (wrong, for this architecture) choice -- could,
// in principle, still coincidentally match one of those pinned bits
// (e.g. if the wrong branch happened not to matter at that one specific
// input). This test instead asserts the exact PROPERTY fma_() exists to
// guarantee: whichever result THIS architecture is supposed to produce
// (fused on aarch64, unfused everywhere else) is the one actually
// produced, and asserts the OTHER one is NOT what came out -- so fusing
// when this architecture should stay plain, or staying plain when it
// should fuse, fails loudly here regardless of which specific fdlibm
// function a future change happens to touch.
TEST(fdlibm_contract_pin_fma_dispatch_matches_this_architecture) {
  const double a = std::bit_cast<double>(std::uint64_t{0x3ff0000000000001ULL});
  const double b = std::bit_cast<double>(std::uint64_t{0x3feffffffffffffeULL});
  const double c = std::bit_cast<double>(std::uint64_t{0xbff0000000000000ULL});
  const std::uint64_t fused_bits = 0xb970000000000000ULL;
  const std::uint64_t unfused_bits = 0x0000000000000000ULL;

  const double result = noisemaker::fdlibm::testing::fma_probe(a, b, c);
  const auto bits = std::bit_cast<std::uint64_t>(result);

#if defined(__aarch64__)
  REQUIRE(bits == fused_bits);
  REQUIRE(bits != unfused_bits);
#else
  REQUIRE(bits == unfused_bits);
  REQUIRE(bits != fused_bits);
#endif
}
