#!/usr/bin/env python3
"""Targeted adversarial input generator for the specific question: does a
1-3 ULP divergence at double precision ever survive narrowing to float32?

Rather than hoping a generic sweep stumbles onto a case where the true
double-precision result sits exactly on a float32 rounding tie (the only
place a small double-level difference COULD flip the rounded float), this
constructs such cases directly: for many representable float32 values F,
compute the exact halfway point (at double precision) between F and its
float32 successor, then invert the target function to find an x whose
result lands near that halfway point, then emit a dense ULP-stepped cluster
of x around that point. This is the maximally adversarial test for "does
this divergence survive f32 rounding" - far stronger than hoping a broad
sweep happens to hit it.

Writes raw double bit patterns (16 hex digits, one per line) to stdout,
readable by the same probes as inputs.hex.
"""
import math
import struct
import sys

def f64_bits(x):
    return struct.unpack('<Q', struct.pack('<d', x))[0]

def bits_f64(b):
    return struct.unpack('<d', struct.pack('<Q', b))[0]

def f32_of(x):
    # round-trip through float32 (python's struct does correctly-rounded
    # double->float32, same guarantee as static_cast<float> / Math.fround)
    return struct.unpack('<f', struct.pack('<f', x))[0]

def next_f32_up(f):
    # smallest float32 strictly greater than f (f finite, not the max float32)
    bits = struct.unpack('<I', struct.pack('<f', f))[0]
    if f >= 0:
        bits += 1
    else:
        bits -= 1
    return struct.unpack('<f', struct.pack('<I', bits))[0]

seen = set()
out = []

def emit(x):
    if not math.isfinite(x):
        return
    b = f64_bits(x)
    if b in seen:
        return
    seen.add(b)
    out.append('%016x' % b)

def emit_cluster(x0, half_width_ulp=40):
    if not math.isfinite(x0):
        return
    b0 = f64_bits(x0)
    sign = b0 & 0x8000000000000000
    mag = b0 & 0x7fffffffffffffff
    for d in range(-half_width_ulp, half_width_ulp + 1):
        m = mag + d
        if m < 0 or m > 0x7ff0000000000000:
            continue
        emit(bits_f64(m | sign))

def float32_targets_for_range(lo_exp, hi_exp, count, negative_too=True):
    """Generate `count` representable float32 magnitudes with exponents
    spanning [lo_exp, hi_exp] (base-2), one per log-spaced step, each with a
    few different mantissa patterns (0, all-ones-ish, and a couple of
    'random-looking' bit patterns) so we don't just test power-of-two F."""
    targets = []
    mantissa_patterns = [0x000000, 0x7fffff, 0x400000, 0x2a5f31, 0x555555]
    n_exp = max(1, count // len(mantissa_patterns))
    for i in range(n_exp):
        t = i / max(1, n_exp - 1)
        e = lo_exp + t * (hi_exp - lo_exp)
        base = 2.0 ** e
        for mpat in mantissa_patterns:
            # construct a float32 with this exponent and mantissa pattern
            # by bit manipulation directly, to guarantee exact representability.
            fbits = struct.unpack('<I', struct.pack('<f', base))[0]
            fbits = (fbits & 0xff800000) | (mpat & 0x7fffff)
            f = struct.unpack('<f', struct.pack('<I', fbits))[0]
            if math.isfinite(f) and f != 0.0:
                targets.append(f)
                if negative_too:
                    targets.append(-f)
    return targets

N_PER_FUNC = 400

# ---- tanh: range is (-1, 1) ----
for F in float32_targets_for_range(-30, -0.0001, N_PER_FUNC):
    if not (-1.0 < F < 1.0):
        continue
    Fn = next_f32_up(F)
    if not (-1.0 < Fn < 1.0):
        continue
    h = (float(F) + float(Fn)) / 2.0  # exact halfway point at double precision
    if not (-1.0 < h < 1.0):
        continue
    try:
        x0 = math.atanh(h)
    except ValueError:
        continue
    emit_cluster(x0)

# ---- exp: range is (0, ~1.8e308); also test near-zero results (large negative x) ----
for F in float32_targets_for_range(-140, 100, N_PER_FUNC, negative_too=False):
    if F <= 0:
        continue
    Fn = next_f32_up(F)
    if Fn <= 0:
        continue
    h = (float(F) + float(Fn)) / 2.0
    if h <= 0:
        continue
    x0 = math.log(h)
    emit_cluster(x0)

# ---- expm1: range is (-1, ~1.8e308) ----
for F in float32_targets_for_range(-30, 100, N_PER_FUNC, negative_too=True):
    if F <= -1.0:
        continue
    Fn = next_f32_up(F)
    if Fn <= -1.0:
        continue
    h = (float(F) + float(Fn)) / 2.0
    if h <= -1.0:
        continue
    try:
        x0 = math.log1p(h)
    except ValueError:
        continue
    emit_cluster(x0)

# ---- sin: range is [-1, 1], multi-branch (principal + shifted by k*2*pi, and
# the "other half" of each period via pi - x) ----
for F in float32_targets_for_range(-30, -0.0001, N_PER_FUNC):
    if not (-1.0 <= F <= 1.0):
        continue
    Fn = next_f32_up(F)
    if not (-1.0 <= Fn <= 1.0):
        continue
    h = (float(F) + float(Fn)) / 2.0
    if not (-1.0 <= h <= 1.0):
        continue
    try:
        x0 = math.asin(h)
    except ValueError:
        continue
    for k in range(-6, 7):
        emit_cluster(x0 + 2.0 * math.pi * k, half_width_ulp=20)
        emit_cluster((math.pi - x0) + 2.0 * math.pi * k, half_width_ulp=20)

# ---- cos: range is [-1, 1], principal branch [0, pi], plus -x0 and shifts ----
for F in float32_targets_for_range(-30, -0.0001, N_PER_FUNC):
    if not (-1.0 <= F <= 1.0):
        continue
    Fn = next_f32_up(F)
    if not (-1.0 <= Fn <= 1.0):
        continue
    h = (float(F) + float(Fn)) / 2.0
    if not (-1.0 <= h <= 1.0):
        continue
    try:
        x0 = math.acos(h)
    except ValueError:
        continue
    for k in range(-6, 7):
        emit_cluster(x0 + 2.0 * math.pi * k, half_width_ulp=20)
        emit_cluster(-x0 + 2.0 * math.pi * k, half_width_ulp=20)

sys.stderr.write('generated %d unique targeted f32-boundary candidate inputs\n' % len(out))
sys.stdout.write('\n'.join(out) + '\n')
