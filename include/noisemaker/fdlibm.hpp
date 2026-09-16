// fdlibm.hpp — the single math layer that reproduces V8's Math.* bit-for-bit
// on both arm64 and x86-64.
//
// V8 does NOT call the platform libm for the bulk of Math.*; it ships its
// own port of Sun Microsystems' fdlibm (src/base/ieee754.cc). Apple's libm /
// glibc's libm are both "accurate" (within ~1 ULP) but are NOT required to
// be correctly-rounded, and in practice disagree with V8's fdlibm in the
// last bit on a large fraction of double inputs. Since noisemaker-for-cpp
// targets bit-exact parity with the JS/V8 renderer, this header exists to
// close that gap: reproduce V8's bits exactly, not just "close" values.
//
// PER-FUNCTION PROVENANCE (verified against this exact V8 build; see
// docs/port-engineering/v8-math/v8-math-report.md for the evidence and
// reference source fetches):
//
//   sin, cos          -- base::ieee754::{sin,cos} (src/base/ieee754.cc,
//                         fdlibm). V8 ALSO ships a build-time alternative
//                         (glibc's vendored dbl-64 sin/cos,
//                         V8_USE_LIBM_TRIG_FUNCTIONS) gated by the GN arg
//                         `v8_use_libm_trig_functions = is_clang` and a
//                         runtime flag `use_libm_trig_functions` (default
//                         true when the macro is compiled in). Verified via
//                         `node --v8-options`: this flag does not exist in
//                         EITHER the arm64 or the x64 (Rosetta) build of
//                         this Node, i.e. V8_USE_LIBM_TRIG_FUNCTIONS was NOT
//                         defined when this V8 was built, so the plain
//                         fdlibm path (base::ieee754::sin/cos) is what
//                         actually runs. Ported here.
//   tan, asin, acos,
//   atan, atan2,
//   exp, expm1,
//   log, log2, tanh   -- base::ieee754::<name>, plain fdlibm, no runtime or
//                         build-time alternative exists for any of these
//                         (confirmed: every one of these resolves through
//                         FUNCTION_REFERENCE_WITH_TYPE(ieee754_<name>_function,
//                         base::ieee754::<name>, ...) in
//                         src/codegen/external-reference.cc with no `#if` /
//                         v8_flags branch around it). Ported here.
//   pow               -- NOT base::ieee754::legacy::pow (the old fdlibm
//                         pow, moved into a `legacy` namespace and
//                         documented "should not be used directly"). The
//                         live implementation is `v8::internal::math::pow`
//                         (src/numbers/ieee754.cc), gated by the runtime
//                         flag `use_std_math_pow` (DEFINE_BOOL default true
//                         on every platform except AIX). Confirmed active
//                         on this build both by reading
//                         src/flags/flag-definitions.h (macOS is not AIX)
//                         and empirically: 200,000 random-input checks of
//                         `Math.pow(x,0.5) === Math.sqrt(x)` and
//                         `Math.pow(x,2) === x*x` (bitwise) both showed 0
//                         mismatches, which only happens under the
//                         std-math-pow special-cased path (the legacy
//                         fdlibm pow computes both through its general
//                         log2/exp2 algorithm and would not agree with
//                         sqrt/multiply bit-for-bit). math::pow's fallback
//                         branch is a literal `std::pow(x, y)` call --
//                         since that resolves to the OS's shared libm on
//                         both sides (V8 and this binary link the same
//                         dynamic `pow` symbol on the same machine), no
//                         algorithm needs porting for that branch: calling
//                         std::pow here IS calling what V8 calls. Only the
//                         special-case wrapper (NaN rules, y==2, y==0.5)
//                         needs reproducing, and this header does that.
//   hypot             -- NOT part of ieee754.cc at all (no fdlibm
//                         ancestor). Math.hypot is a Torque builtin
//                         (src/builtins/math.tq, MathHypot/FastMathHypot):
//                         a *different* fast-path formula per argument
//                         count -- 1 arg: |a|; 2 args: scaled sum of
//                         squares with NO Kahan compensation; 3 args: same
//                         but WITH a Kahan compensation term folded in
//                         between the first two squares only; >3 args
//                         (the runtime's variadic "Slow" path): a full
//                         Kahan-compensated running sum. These are ported
//                         as three overloads below, each matching its
//                         argument count's exact operation order -- do not
//                         "unify" them into one generic loop; the 2-arg
//                         and 3-arg cases are bit-sensitive to which
//                         terms get compensated.
//   sqrt              -- IEEE-754 correctly-rounded in both V8 (a bare
//                         Float64Sqrt machine op) and std::sqrt (mandated
//                         by IEEE 754), so it already agrees with V8
//                         exactly. Not reimplemented; callers keep using
//                         std::sqrt.
//   floor/ceil/round/
//   trunc/abs/min/max/
//   sign/imul/fround  -- exact bitwise/hardware operations already
//                         agreeing with V8's JS semantics; not part of this
//                         header.
//
// Every fdlibm-derived function below is transcribed line-for-line from
// V8's src/base/ieee754.cc (checked against a fresh fetch of the exact tag
// this environment's V8 reports, see docs/port-engineering/v8-math/), which
// is itself adapted from Sun Microsystems' fdlibm, 1993, freely
// redistributable (see the notice reproduced in fdlibm.cpp). Preserving
// operator order, branch structure, and constant tables exactly is the
// entire point: the argument-reduction order and polynomial evaluation
// order are what determine the exact output bits. Do not "simplify" the
// arithmetic in fdlibm.cpp.
//
// FMA / -ffp-contract: V8's own shipped binary contains FMA-contracted
// arithmetic in its polynomial evaluations on FMA-capable hardware (this is
// not a defect; it is what happens when *any* C++ compiler compiles this
// same fdlibm source at -O1+ with contraction allowed and the target has a
// fused-multiply-add instruction). This project mandates
// -ffp-contract=off everywhere else for cross-compiler/cross-architecture
// reproducibility, but the math translation unit (fdlibm.cpp) is compiled
// with -ffp-contract=fast specifically -- see the CMakeLists.txt comment at
// its `set_source_files_properties` block, and
// docs/port-engineering/v8-math/v8-math-report.md for the exhaustive
// differential evidence on both arm64 and x86-64 justifying that as safe
// and deterministic (not a "close enough" tradeoff): on arm64 (NEON always
// has FMA) it reproduces V8's own arm64 binary's contraction; on x86-64
// without -mfma (this project's baseline, and this CI's baseline) there is
// no hardware fused-multiply-add instruction for contract=fast to select,
// so it is a byte-for-byte no-op there and reproduces V8's own x86-64
// binary (also built at the ordinary, non--mfma baseline) too.
//
// Scope: every function noisemaker's kernels/adapters call through
// noisemaker::glsl:: or directly: sin, cos, tan, asin, acos, atan, atan2,
// exp, expm1, log, log2, tanh, pow, hypot (1/2/3/N-arg).

#ifndef NOISEMAKER_FDLIBM_HPP_
#define NOISEMAKER_FDLIBM_HPP_

namespace noisemaker::fdlibm {

// exp(x) - 1, computed so that it is accurate even when exp(x) is close to
// 1 (i.e. x close to 0), where naively computing exp(x) - 1 loses almost
// all significant digits to cancellation. tanh() below is built on this.
double expm1(double x) noexcept;

// e^x.
double exp(double x) noexcept;

// Hyperbolic tangent. Implemented as (1 - 2/(expm1(2|x|)+2)) for x>=1 and
// (-expm1(-2|x|))/(expm1(-2|x|)+2) for 0<=x<1, exactly as V8 does, so it
// depends on expm1() above rather than calling exp() directly.
double tanh(double x) noexcept;

// Sine / cosine / tangent, argument-reduced via the Payne-Hanek-style
// algorithm fdlibm uses (exact for all finite double x, not just small
// ones).
double sin(double x) noexcept;
double cos(double x) noexcept;
double tan(double x) noexcept;

// Inverse trig.
double asin(double x) noexcept;
double acos(double x) noexcept;
double atan(double x) noexcept;
double atan2(double y, double x) noexcept;

// Natural / base-2 logarithm. fd_log: classic argument-reduction + degree-7
// Remez polynomial (see fdlibm.cpp for the method comment). log2 reduces to
// the same k_log1p() kernel V8's own log2 uses, then rescales by 1/ln2 in
// extra precision -- NOT `log(x) / M_LN2`, which would round differently.
double log(double x) noexcept;
double log2(double x) noexcept;

// x**y, matching V8's live Math.pow (v8::internal::math::pow,
// src/numbers/ieee754.cc under the default `use_std_math_pow=true`),
// NOT V8's retired fdlibm-based pow (base::ieee754::legacy::pow). See the
// provenance comment above.
double pow(double x, double y) noexcept;

// Euclidean norm, matching V8's Math.hypot (src/builtins/math.tq) exactly
// per argument count -- see the provenance comment above for why these are
// three distinct overloads rather than one generic N-ary loop.
double hypot(double x, double y) noexcept;
double hypot(double x, double y, double z) noexcept;
double hypot_n(const double* values, int count) noexcept;

}  // namespace noisemaker::fdlibm

#endif  // NOISEMAKER_FDLIBM_HPP_
