// fdlibm.hpp — bit-exact ports of the transcendental functions V8 uses for
// Math.tanh / Math.exp / Math.expm1 / Math.sin / Math.cos.
//
// V8 does NOT call the platform libm for these; it ships its own port of
// Sun Microsystems' fdlibm (src/base/ieee754.cc). Apple's libm / glibm are
// both "accurate" (within ~1 ULP) but are NOT required to be
// correctly-rounded, and in practice disagree with V8's fdlibm in the last
// bit on a large fraction of double inputs — measured (403,636-point
// adversarial sweep, see fdlibm-report.md) at tanh 4.27%, exp 5.81%,
// expm1 3.37%, sin 2.71%, cos 2.64% divergent from V8. Since
// noisemaker-for-cpp targets bit-exact parity with the JS/V8 renderer, this
// header exists to close that gap: reproduce V8's bits exactly, not just
// "close" values.
//
// Every function here is transcribed line-for-line from V8's
// src/base/ieee754.cc (itself adapted from Sun's fdlibm, 1993, freely
// redistributable — see the notice reproduced in fdlibm.cpp), preserving
// operator order, branch structure, and constant tables exactly. The
// argument-reduction order and polynomial evaluation order are what
// determine the exact output bits: reordering "equivalent" arithmetic (e.g.
// combining multiplies) changes rounding and defeats the entire point of
// this file. Do not simplify the arithmetic in fdlibm.cpp.
//
// MANDATORY build flag: -ffp-contract=off. Without it, the compiler may
// fuse consecutive multiply+add into a single FMA instruction, which
// computes the product at full (unrounded) intermediate precision instead
// of V8's two separately-rounded IEEE-754 operations. That changes the
// exact output bits of every polynomial evaluation in this file and will
// silently defeat bit-exact parity even though the source is a faithful
// transcription. See fdlibm-report.md for a case where this cost hours to
// track down.
//
// Scope: this header implements exactly the five functions the C++ runtime
// needs — expm1, exp, tanh, sin, cos — plus the internal argument-reduction
// machinery (__ieee754_rem_pio2 / __kernel_rem_pio2 / __kernel_sin /
// __kernel_cos) that sin/cos require. log and atan are NOT reimplemented
// here (measured but not found to need replacement in this pass — see the
// report for exact figures); sqrt is IEEE-754 correctly-rounded and already
// agrees with V8 exactly; pow is close (measured ~0.04% divergent, small
// enough it was left alone this pass). If a future measurement finds any of
// these diverging enough to matter, the same fdlibm port technique applies.
//
// KNOWN RESIDUAL GAP (read before assuming "0 divergences" is unconditional):
// verified against this repo's actual V8 (Node/macOS-arm64) at 0/403636 for
// all five functions when compiled with -ffp-contract=fast; under the
// mandatory -ffp-contract=off this drops to 99.6%-99.99% exact (worst case
// 3 ULP) — see fdlibm-report.md "Diagnosed root cause of the residual gap"
// for why: it traces to V8's own shipped binary containing FMA-contracted
// arithmetic on FMA-capable hardware, not to a transcription defect. The
// report lays out the tradeoff; this header does not attempt to chase it
// with hand-placed std::fma() calls because the exact fusion points are a
// backend instruction-selection heuristic, not a stable contract — matching
// one V8 build's ISel choices with hand-fma would just trade one
// non-portable coincidence for another.

#ifndef NOISEMAKER_FDLIBM_HPP_
#define NOISEMAKER_FDLIBM_HPP_

namespace fdlibm {

// exp(x) - 1, computed so that it is accurate even when exp(x) is close to
// 1 (i.e. x close to 0), where naively computing exp(x) - 1 loses almost
// all significant digits to cancellation. tanh() below is built on this.
double expm1(double x);

// e^x.
double exp(double x);

// Hyperbolic tangent. Implemented as (1 - 2/(expm1(2|x|)+2)) for x>=1 and
// (-expm1(-2|x|))/(expm1(-2|x|)+2) for 0<=x<1, exactly as V8 does, so it
// depends on expm1() above rather than calling exp() directly.
double tanh(double x);

// Sine / cosine, argument-reduced via the Payne-Hanek-style algorithm
// fdlibm uses (exact for all finite double x, not just small ones).
double sin(double x);
double cos(double x);

}  // namespace fdlibm

#endif  // NOISEMAKER_FDLIBM_HPP_
