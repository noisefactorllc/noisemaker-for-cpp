#pragma once

// shift_primitive.hpp
//
// Standalone, self-contained proposal for the noisemaker-for-cpp C++20
// port's missing SIGNED/ARITHMETIC right-shift primitive, plus four small
// companion scalar bitwise operators from the same frontier task family
// (Task N+3 in docs/port-engineering/bitops/bitops-precompute.md).
//
// This file is a DESIGN PROPOSAL living under
// docs/port-engineering/shift-primitive/. It does not modify, and is
// not wired into, the real
// include/noisemaker/glsl_types.hpp
// (read-only in this task). Its naming, `noexcept`, `[[nodiscard]]`, and
// masking convention deliberately match that file's existing
// `glsl::shift_right` (glsl_types.hpp:196-204) / `glsl::bitwise_xor`
// (glsl_types.hpp:206-213) house style, so it can be pasted into that
// namespace with minimal changes when a future task actually wires it up.
//
// See shift-primitive-report.md for:
//   - the empirically-verified JS semantics table this header implements
//   - why this is a NEW, separately-named primitive rather than a
//     parameter added to the existing (and must-stay-unchanged)
//     glsl::shift_right
//   - the full sweep verification results (N compared/exact/divergent)
//   - the real-program (spookyTicker hash_mix) cross-check

#include <bit>
#include <cstdint>

namespace noisemaker::glsl {

// ---------------------------------------------------------------------
// shift_right_arithmetic -- THE primitive this task designs.
//
// Distinct from glsl::shift_right (logical/zero-fill, Vec<N,uint32_t>-only,
// glsl_types.hpp:196-204), which is the CORRECT, already-shipped-and-
// verified lowering for the admitted `uvecN >> uint` shape -- i.e. the
// canonical pcg3d hash idiom that glsl-transpiler recognizes as a whole-
// function match and replaces with a hand-written stdlib call using JS's
// `>>>` throughout (glsl-runtime.js:23-38). That existing primitive MUST
// keep working unchanged; nothing here alters it.
//
// shift_right_arithmetic is for the disjoint case documented in
// bitops-precompute.md Hazard #1: glsl-transpiler's GENERIC scalar codegen
// fallback (operators.js:298-370, the `opResult = left + ' ' + operator +
// ' ' + right` branch at 349-362) is reached for every GLSL `>>` site that
// is NOT part of a recognized canonical idiom -- and that fallback emits
// JS's plain `>>`, which is ALWAYS sign-propagating/arithmetic, with zero
// regard for whether the GLSL operand was typed `int` or `uint`. This is
// confirmed live in shipped JS at canonical-kernels.js:15313 (`median`),
// :16410-16426 (`osd`), :19971-19975 (`spookyTicker`), :34733
// (`testPattern`). The determination of which shift semantics to use is
// per CALL SITE (does this specific `>>` route through a recognized
// stdlib idiom, or through the generic fallback?), never inferable from
// the GLSL operand's declared type alone.
//
// Masking convention: matches the existing glsl::shift_right exactly --
// `amount & 31U`, reproducing JS's implicit `ToUint32(amount) & 0x1F`
// shift-count reduction (verified empirically in probe_semantics.mjs
// Section D: v >> s vs v >> (s mod 32) produced ZERO mismatches across
// shift counts -70..130 on five representative int32 values, including
// INT32_MIN and INT32_MAX).
//
// Implementation note -- portability: this deliberately does NOT write
// `value >> masked` on a (possibly negative) std::int32_t `value`. Task
// instructions explicitly called out C++20's right-shift-of-negative-
// operand behavior as something to VERIFY rather than assume; see
// shift-primitive-report.md Sec 2 for why plain `>>` on this exact
// toolchain (Apple clang 16 / arm64) was independently confirmed
// bit-identical to the formula below over the full sweep, and why the
// shipped primitive still avoids depending on that toolchain fact: the
// formula below derives the arithmetic-shift bit pattern using only
// operations that are unconditionally well-defined in C++20 for every
// std::int32_t value -- std::bit_cast to std::uint32_t (two's-complement
// guaranteed, [basic.fundamental]/P0907R4), a logical `>>` on that
// uint32_t (always well-defined), and an explicit sign-fill built with an
// unsigned `<<` (well-defined for every masked count in [0,31]).
[[nodiscard]] constexpr std::int32_t shift_right_arithmetic(
    std::int32_t value, std::uint32_t amount) noexcept {
  const std::uint32_t masked = amount & 31U;
  const std::uint32_t bits = std::bit_cast<std::uint32_t>(value);
  std::uint32_t result = bits >> masked;
  if ((bits & 0x8000'0000U) != 0U && masked != 0U) {
    result |= (~std::uint32_t{0}) << (32U - masked);
  }
  return std::bit_cast<std::int32_t>(result);
}

// Overload for call sites where the GLSL-typed operand is `uint` but the
// call site nonetheless requires arithmetic (not logical) shift semantics
// per Hazard #1 -- e.g. filter/median's packedRg, filter/spookyTicker's
// hash_mix `v`, filter/osd's local `pcg` `state`: all GLSL-`uint`-typed,
// all routed through glsl-transpiler's generic fallback (not the pcg3d
// idiom), all needing sign-propagating shift to match shipped JS. GLSL
// type does not select shift semantics; idiom recognition does (see
// class-level comment above). This overload exists so a `uint`-typed call
// site can call shift_right_arithmetic without an extra explicit cast at
// every use, while still being visibly a DIFFERENT function name than
// glsl::shift_right -- an accidental swap is a compile-time-visible wrong
// name, not a silently-flipped boolean flag (see report Sec "new vs
// parameterized" for the full reasoning).
[[nodiscard]] constexpr std::uint32_t shift_right_arithmetic(
    std::uint32_t value, std::uint32_t amount) noexcept {
  return std::bit_cast<std::uint32_t>(
      shift_right_arithmetic(std::bit_cast<std::int32_t>(value), amount));
}

// ---------------------------------------------------------------------
// Bonus companions: the frontier's other missing scalar operators
// (bitops-precompute.md §2/§4: zero runtime coverage today for scalar
// `&`, `|`, `<<`, unary `~`). Included because Task N+3's programs
// (median, osd, spookyTicker, texture, testPattern, dither, glyphMap) need
// these alongside the new shift, and because Hazard #2's claim --  "plain
// C++20 int32_t/uint32_t operators already reproduce JS bit-for-bit for
// &, |, ^, <<, ~, because C++20 mandates two's complement and gives
// left-shift of negative operands defined behavior" -- is verified
// empirically for these specific operators in probe_semantics.mjs
// (Section A/C) and verify_sweep.cpp, not merely cited from the standard.
// Plain operators are correct here (unlike >>) because none of &, |, ^,
// ~, << have a signed/unsigned or well-defined/implementation-defined
// distinction driven by operand sign in C++20 -- only >> does.
[[nodiscard]] constexpr std::int32_t bitwise_and(std::int32_t a, std::int32_t b) noexcept { return a & b; }
[[nodiscard]] constexpr std::uint32_t bitwise_and(std::uint32_t a, std::uint32_t b) noexcept { return a & b; }
[[nodiscard]] constexpr std::int32_t bitwise_or(std::int32_t a, std::int32_t b) noexcept { return a | b; }
[[nodiscard]] constexpr std::uint32_t bitwise_or(std::uint32_t a, std::uint32_t b) noexcept { return a | b; }
[[nodiscard]] constexpr std::int32_t bitwise_not(std::int32_t a) noexcept { return ~a; }
[[nodiscard]] constexpr std::uint32_t bitwise_not(std::uint32_t a) noexcept { return ~a; }

// shift_left: written in the unsigned domain throughout (rather than
// relying on C++20's now-well-defined-but-less-familiar negative-operand
// `<<`) purely for house-style consistency with shift_right_arithmetic
// above -- both avoid ever left- or right-shifting a *signed* operand
// directly, so neither depends on a reader recalling exactly which shift/
// sign combinations P0907R4 fixed.
[[nodiscard]] constexpr std::int32_t shift_left(std::int32_t value, std::uint32_t amount) noexcept {
  const std::uint32_t masked = amount & 31U;
  return std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(std::bit_cast<std::uint32_t>(value) << masked));
}
[[nodiscard]] constexpr std::uint32_t shift_left(std::uint32_t value, std::uint32_t amount) noexcept {
  const std::uint32_t masked = amount & 31U;
  return static_cast<std::uint32_t>(value << masked);
}

}  // namespace noisemaker::glsl
