# Task 31 (Curl): parity failure and what has been eliminated

Date: 2026-08-12
Author: integration owner

Curl was implemented end-to-end — profile, both authorities, runtime, slice
registration, regeneration — and then **backed out** on a genuine full-render
parity failure. The tree is green at the accepted Task 30 state; generated
outputs are byte-identical (`typed_slice.cpp` `5765f863…`,
`typed_manifest.json` `3a6b5289…`, `catalog.hpp` `16ebd7b1…`), native 150/150,
all generator gates pass.

## The failure

Rendering the generated Curl kernel against the frozen oracle
(`future-precompute/task31-curl/curl-oracles.json`,
`f4a9e1f92111c3ae68b48aa3e180c6c56e847cbcafbca70b3b34f0ef4e6d5f19`):

| Case | Result |
|---|---|
| `default-seed0-time0` (time=0, seed=0) | **MATCH** |
| `seed7-tiled-midtime` | mismatch — *probe bug, see below* |
| `negative-seed-drives-negative-mod-operands` | **MISMATCH** |
| `negative-intensity-flips-tanh-sign` | **MISMATCH** |
| `large-seed-negative-scale-negative-speed` | **MISMATCH** |
| `two-pi-time-near-identity-intensity` | **MISMATCH** |

One mismatch is my own probe's fault and is not evidence of a port defect:
`seed7-tiled-midtime` is the only case with a non-trivial tile
(`tile_offset [3,2]`, `full_resolution [13,11]`), and the probe hardcoded
`tileOffset=(0,0)`, `fullResolution=(width,height)` for every case. Any
re-run must bind per-case tile data. **Four genuine mismatches remain.**

Probe-level comparison on `negative-intensity-flips-tanh-sign` shows all five
probes differing in every RGB lane (alpha is exactly 1.0 in both), with the C++
values consistently smaller in magnitude — a systematic difference, not
scattered last-ulp noise.

## What has been ELIMINATED (all verified first-hand)

These are the obvious suspects, and none of them is the cause:

1. **`tanh` is not the cause.** JS `Math.tanh` and C++ `std::tanh` were
   compared at f32 across twelve values including negatives, tiny, and
   saturating inputs: **bit-identical in every case**.
2. **`mod` is not the cause.** All 8 of the oracle's `direct_mod_rows` —
   deliberately including negative operands, ±0.0 and near-float32 extremes,
   the exact region where a naive `fmod` port breaks — match the new C++
   `mod` **exactly**. All 10 `direct_tanh_rows` match exactly too. A generated
   harness ran both sets and reported `direct mismatches: 0`.
3. **`sin`/`cos` are not the cause.** This was a strong hypothesis, since V8
   ships its own fdlibm port rather than using platform libm, and `time` enters
   Curl *only* through `sin(time * 6.28318)` and `cos(time * 6.28318)`
   (curl.glsl:152-153) — which would neatly explain why the one matching case
   has `time = 0`. Compared at **double** precision for all five case time
   values: **bit-identical**.

4. **Float-literal narrowing is not the cause.** A strong hypothesis: GLSL
   `6.28318` is a float literal, so if JS kept the double `6.28318` while C++
   narrowed to float (or vice versa) the `sin` argument would differ. Checked
   the actual JS canonical kernel: it **pre-narrows** literals, emitting
   `sin(time * 6.283180236816406)` and `* 0.20000000298023224` — exactly
   `float(6.28318)` and `float(0.2)` widened to double. The generated C++ emits
   `static_cast<double>(static_cast<float>(6.28318))` and
   `static_cast<float>(0.2)`. **Identical values.**
5. **Double-narrowing in the finite-difference path is not the cause.** The
   next hypothesis was that `(p + vec3(0,eps,0)) - offset1` narrows twice in
   C++ (once for the inner add, once at the call) where JS narrows once. It
   does not: `FloatExpr<N>` is a lazy double-precision expression type;
   `Vec<N,float>` converts into it implicitly, all arithmetic runs in double,
   and narrowing to float happens only on assignment or construction of a
   `Vec`. That is exactly the JS Number-until-storage semantics, and it is why
   the type exists. Both sides narrow once.
6. **`offset1` construction matches.** JS stores it as a
   `PooledFloat32Array([a, b, 0])`; C++ assigns `FloatExpr<3>(a, b, 0.0f)` into
   a `glsl::Vec3`, which narrows each lane. Same single narrowing, same point.
7. **`a` and `b` are computed identically.** JS:
   `((sin(time * 6.283180236816406)) * (speed) + 1) / (OCTAVES) * 0.20000000298023224`
   in Number, no narrowing. C++: the same expression with `double` intermediates
   stored to `double a`/`double b`, no narrowing. Same operations, same
   constants, same precision.

So the two new primitives this task adds are correct, the literal handling
matches, and the precision pipeline matches. The divergence lies deeper.

## Where the divergence must be — narrowed by measurement

A census of all 130 typed programs for Curl's helper functions:

| Helper | Already exercised by a typed program? |
|---|---|
| `permute` | **yes** — `filter/clouds`, `filter/crt`, `filter/degauss` (all passing parity) |
| `simplex3D` | **no — Curl is the first** |
| `fbmSimplex3D` | **no — Curl is the first** |
| `taylorInvSqrt` | **no — Curl is the first** |

`permute` is therefore battle-tested at parity and is the least likely culprit,
despite hosting two of the four new closure sites. The divergence is almost
certainly inside `simplex3D` (41 statements — the largest function in the
program and the biggest never-before-exercised lowering surface) or
`taylorInvSqrt`.

**Important counter-constraint — do not over-read this narrowing.** The one
MATCHING case also calls `simplex3D` (with `a = 0.2`, `b = 10.2`, `seed = 0`,
`scale = 10`, so the arguments are non-trivial). If `simplex3D` were simply
wrong, that case should fail too. So any explanation must be **input-dependent**,
not a blanket error. Two shapes fit:

- a path inside `simplex3D` that only activates for certain inputs — e.g.
  `i = mod(i, 289)` at 65:9 is an identity when the lattice index is already
  in range, and only does real work once offsets/seed push it out of range;
- something that only manifests for larger or negative coordinates.

The first is worth checking before anything else, because it is the one place
where a new closure site sits inside a never-before-exercised function. Note
the direct `mod` rows already passed, so if that is the culprit it is about
*which values reach* the call, not the operation itself.

## What is still unexplained

The correlation that remains: the only matching case has `time = 0` **and**
`seed = 0`. One failing case (`two-pi-time-near-identity-intensity`) has
`seed = 0` but `time ≠ 0`, which implicates the `time` path — yet `sin`/`cos`
are proven identical, and `a`/`b` (curl.glsl:152-153) are the only consumers.

Next steps for whoever picks this up:

1. Fix the probe to bind per-case `tile_offset` / `full_resolution`, then
   re-measure; confirm four mismatches, not five.
2. Instrument intermediate values rather than only the final surface. Compare
   `a` and `b` (curl.glsl:152-153) between JS and C++ for a failing case — they
   are scalars and easy to dump on both sides. If they agree, move inward to
   `fbmSimplex3D` and `curlNoise3D`.
3. The finite-difference narrowing lead has been **checked and ruled out**
   (see elimination 5). Focus instead on `simplex3D` — it is the largest
   function (41 statements), Curl is the first typed program to exercise it,
   and it contains the `mod(vec3, float)` site plus permute/taylorInvSqrt
   chains. Dump `Fx_py` (the first `fbmSimplex3D` result) from both engines for
   a failing case; that isolates everything above simplex3D from everything
   inside it in a single comparison.
4. Check `RIDGES` / `OUTPUT_MODE` handling: the JS oracle passes defines **as
   uniforms** while C++ bakes them at generation time. Extrude did the same
   and matched, so this is lower priority, but it has not been directly
   verified for Curl.

## What was RETAINED (green, verified, reusable)

- **The C++ runtime additions stay.** `tanh` at vec3 and `mod` at
  vec3/vec4-by-scalar are in `glsl_runtime.hpp`, each `requires`-constrained to
  exactly the authorized widths. They are proven correct against 18 direct
  oracle rows and are byte-neutral for all 130 typed programs
  (`generate_typed_slice --check` still yields `5765f863…`).
- **The compile-time width policy in `tests/test_glsl_runtime.cpp` was updated
  deliberately, not silently.** That file carried
  `static_assert(!HasGlslMod<Vec4, double>)` pinning the old narrow policy; it
  now asserts the new authorized widths positively and adds negative assertions
  that `Vec3×Vec3`, `Vec4×Vec4`, and `tanh` at vec2/vec4 remain banned. The
  suite catching my change is exactly why that assertion existed.
- **Native test `glsl_tanh_vec3_and_wide_mod_match_glsl_semantics`** pins GLSL
  sign-of-divisor semantics with negative operands (`mod(-1, 289) == 288`).
- **The profile and both wirings are retained but inert** — no slice entry
  references them, so the tree stays green and the work is recoverable.

## Status of the two Task 31 candidates

Both Caustic and Curl are now blocked, for different and both-real reasons:

- **Caustic** — closure is dead code at its authorized defines; no rendering
  evidence can validate it (`task-31-blockers.md`).
- **Curl** — closure is live and its primitives are proven correct, but the
  program does not currently achieve full-render parity for an unrelated,
  undiagnosed reason.

Curl remains the better candidate: the failure is a solvable bug with a
concrete lead, not a structural impossibility. Do not select a third target
before resolving it — the diagnosis is likely to uncover something that
affects other programs too.
