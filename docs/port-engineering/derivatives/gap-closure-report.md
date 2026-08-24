# Derivative prototype — gap closure report

Status: **verification only**. Nothing under `.`
or `../noisemaker-for-cpu` was modified; both were read
and, for the sampler/surface `.cpp` files, **compiled read-only** (linked
into standalone test binaries under `docs/port-engineering/derivatives/`
— no build artifact was written back into either source tree). No `git`
command was run anywhere. All new files live under
`docs/port-engineering/derivatives/`. The original verified artifacts
(`prototype.cpp`, `reference_probe.mjs`, and their outputs) are untouched —
every file in this report is a new, distinctly-named file alongside them.

This report closes the three verification gaps flagged in
`derivatives-architecture.md` section 6: the untested `vec3`/`vec4`
overload, the unstress-tested multi-call-site ordinal mechanism, and the
unverified edge-of-canvas / off-canvas-texture-sample behavior.

Shared infrastructure: `derivative_lib.hpp` generalizes `prototype.cpp`'s
mechanism to vec3/vec4, an arbitrary number of call sites, and
runtime-configurable (non-8x8) canvas dimensions, while preserving the
scalar-vs-vector **narrowing asymmetry** documented in glsl-runtime.js
lines 448-474/512-533 (see the header's top comment for the full
derivation). Every `.cpp` file below includes it and is compiled with
the mandated flags:

```
clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off -O2 ...
```

All builds were clean (zero warnings). `-ffp-contract=off` matters here in
particular because Gap 1's sensitivity case is specifically about how many
times a value gets rounded and in what order — FMA fusion would silently
change which values get rounded together.

---

## Gap 1 — vec3 and vec4 overloads: **PASS**

**Files**: `gap1_vec34.cpp` (C++), `gap1_vec34_probe.mjs` (JS, imports the
real `GlslCpuRuntime`/`bindGlslKernel` from `glsl-runtime.js` read-only).

**What was built**: a kernel computing a scalar `t` and a `vec3 v3`/`vec4
v4` (both with `.x` set to the *identical* value/formula as `t`), then
`dFdx`/`dFdy`/`fwidth` on all three (24 output lanes/pixel), over an 8x8
grid.

**Sensitivity case**: per the task's requirement to design a case sensitive
to the scalar-vs-vector narrowing asymmetry, the quad at `(quadX=0,
quadY=0)` uses four directly-tabulated corner constants (not a smooth
polynomial) found by brute-force search (`/tmp/search_double_round2.mjs`,
not a deliverable) such that the *exact* (double-precision) dFdx/dFdy
differences are not themselves exactly representable in float32:

| corner | value |
|---|---|
| bottomLeft | `0.0000071775784817873500288` |
| bottomRight | `3.7392933194269062369e-8` |
| topLeft | `0.0025053308345377445221` |

At pixel `(row=7, col=0)` this produces, in **both** implementations:

```
fw_t     = 0.0025052933488041162   (scalar path: single final rounding of the raw double sum)
fw_v3.x  = 0.00250529358163476     (vector path: x/y narrowed to float32 immediately, THEN summed and rounded again)
```

These differ by exactly 1 ULP, and the C++ implementation reproduces
**both** distinct values bit-for-bit matching JS — proving
`derivative_lib.hpp`'s scalar path (double precision, `DerivativeRecord::
scalar_value`/`DerivativeSample::scalar_x/y/width`, narrowed only at
`derivative_scalar`'s return) and vector path (per-component `float`,
narrowed immediately in `compute_sample`) correctly mirror glsl-runtime.js's
asymmetry rather than collapsing it. An implementation that (incorrectly)
narrowed the scalar path early would have produced `0.00250529358163476`
for `fw_t` too, silently passing a smooth-polynomial test while being wrong
for real programs.

**Command and result**:
```
$ clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off -O2 -o gap1_vec34 gap1_vec34.cpp
$ ./gap1_vec34
$ node gap1_vec34_probe.mjs
```
Lane-by-lane comparison (`gap1_vec34_output.f32` vs `gap1_vec34_reference.f32`,
8×8 pixels × 24 lanes):
```
lanes: 1536 exact matches: 1536 max abs diff: 0.0
```
**PASS — 1536/1536 exact, max abs diff 0.0.**

---

## Gap 2 — multi-call-site ordinal interleaving: **PASS**

**Files**: `gap2_multisite.cpp` (C++, two kernels), `gap2_multisite_probe.mjs`
(JS, structurally parallel).

### Kernel A — interleaved, mixed kinds/widths, helper called twice

Six call sites in fixed order: `dFdx` scalar (ordinal 0) → `fwidth` vec3
(ordinal 1) → `dFdy` vec2 (ordinal 2) → `helper_scalar()` containing one
`dFdx` scalar call, invoked once (ordinal 3) → `fwidth` scalar (ordinal 4)
→ `helper_scalar()` invoked a **second** time (ordinal 5) — the same
textual call site landing at two different ordinals, the sharpest version
of "ordinal is a per-invocation counter, not a per-source-line identity."

```
$ clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off -O2 -o gap2_multisite gap2_multisite.cpp
$ ./gap2_multisite
$ node gap2_multisite_probe.mjs
```
`gap2a_interleaved_output.f32` vs `gap2a_interleaved_reference.f32` (8×8 × 9 lanes):
```
lanes: 576 exact matches: 576 max abs diff: 0.0
```
**PASS — 576/576 exact.**

### Kernel B — missing-ordinal fallback (branchy)

Three call sites; the third (`dFdy`, ordinal 2) is gated on `uv.y < 0.6` —
a per-pixel-*varying* condition (deliberately, to stress-test the
mechanism; none of the real 17 programs gate a derivative call on anything
but a frame-constant `uniform`, per `derivatives-architecture.md` §3.2).
This makes different quad corners execute a **different number** of
derivative calls.

**I was able to construct this case.** Diagnostic output (both
implementations independently probe the same quad,
`quadX=0, quadY=2`, and agree exactly):
```
gap2b diagnostic (C++): bottom corner (0,4) record_count=3 top corner (0,5) record_count=2
gap2b diagnostic (C++): bottom ordinal-2 recorded value=0.56640625 (top ordinal-2 MISSING -> falls back to this, NOT to 0)
gap2b diagnostic (C++): correct y (top falls back to bottomValue) = 0; WRONG (top falls back to 0) would have been -0.56640625

gap2b JS diagnostic: bottom corner (0,4) record_count=3 top corner (0,5) record_count=2
gap2b JS diagnostic: bottom ordinal-2 recorded value=0.56640625
```
This exercises `top[i] ?? bottomValue` (glsl-runtime.js line 517) exactly:
the correct fallback (top falls back to *bottomValue*, giving
`y = bottomValue − bottomValue = 0` at pixel `(row=3, col=0)`, whose own
`uv.y = 0.5625 < 0.6` so it genuinely consumes ordinal 2 in replay) is
**algebraically indistinguishable from 0 in the output** — this is
inherent to the `right ?? left` / `top ?? bottom` design (falling back to
one's own pair partner always yields a zero difference), not a weakness of
the test: the diagnostic block computes what the *wrong* answer (`top ??
0`) would have been (`-0.566...`) for contrast, confirming the
implementation is not accidentally correct.

`gap2b_branchy_output.f32` vs `gap2b_branchy_reference.f32` (8×8 × 3 lanes):
```
lanes: 192 exact matches: 192 max abs diff: 0.0
```
**PASS — 192/192 exact**, and the missing-ordinal fallback path is
confirmed genuinely exercised (record counts 3 vs 2 at the same ordinal
across corners), not just present-but-untriggered.

---

## Gap 3 — edge-of-canvas behavior

### 3a. Odd-dimension canvas (7×5): **PASS**

**Files**: `gap3a_odd_canvas.cpp`, `gap3a_odd_canvas_probe.mjs`. Same
kernel shape as the original `prototype.cpp` (scalar `dFdx`/`dFdy` +
vector `fwidth`), run on a 7×5 canvas so the last quad's `x0+1`/`y0+1`
probes land at column 7 / row 5 — genuinely outside `[0,7)×[0,5)`.

```
$ clang++ ... -o gap3a_odd_canvas gap3a_odd_canvas.cpp && ./gap3a_odd_canvas
$ node gap3a_odd_canvas_probe.mjs
```
`gap3a_odd_canvas_output.f32` vs `gap3a_odd_canvas_reference.f32` (7×5 × 4 lanes):
```
lanes: 140 exact matches: 140 max abs diff: 0.0
```
**PASS — 140/140 exact.**

### 3b. Direct sampler-vs-sampler comparison at out-of-range UV

**Files**: `gap3b_sampler_compare.cpp` (links the **real, unmodified**
`sampler.cpp`/`surface.cpp`/`numeric.cpp` from
`src/`, compiled read-only),
`gap3b_sampler_compare_probe.mjs` (imports the **real, unmodified**
`sampler.js`/`surface.js` from `noisemaker-for-cpu/src/runtime/`).

A distinctive 4×4 texture, sampled at 14 `(u,v)` pairs: interior, all four
exact corner boundaries, and 6 clearly out-of-range coordinates (negative,
`>1`, and `far-out` at `(-2.3, 3.7)`).

**NEAREST** (`sample_nearest_bottom_left` vs `sampleNearestBottomLeft`,
both called **unflipped** — the convention already in production use on
both sides: `glsl-runtime.js:199` and every `sample_nearest_bottom_left`
call site in `typed_slice.cpp`/`filter_invert.cpp`/`synth_solid.cpp`):
**bit-exact agreement on all 14×4 = 56 channel values**, including every
out-of-range coordinate. Both clamp (not wrap) `u`/`v` to
`[0, extent-1]` before indexing — same clamp semantics, same order.

**BILINEAR**: this required determining the correct convention first.
`grep -rn sample_bilinear_bottom_left include/ src/` under
`noisemaker-for-cpp` returns **zero call sites** — no production C++ code
invokes it yet, so there's no established "how do we call this" precedent
to defer to. Two comparisons were run:

1. **Naive same-argument**: C++ `sample_bilinear_bottom_left(surface,u,v)`
   vs raw JS `sampleBilinear(surface,u,v)`, both unflipped. **These
   disagree** (22/56 channel comparisons differ, e.g. `interior` (0.125,
   0.125): C++ gives `(0.75,0,0.75,1)`, JS raw gives `(0,0,0,1)`) — because
   JS's raw `sampleBilinear` has **no** internal row-flip (it's a plain
   top-down sampler; `sampleNearestBottomLeft` does the bottom-left flip
   internally, `sampleBilinear` does not — see `sampler.js:39-65` vs
   `25-37`), while C++'s `sample_bilinear_bottom_left` **does** bake the
   flip in (`sampler.cpp:80-83`, `surface.height()-1-y0`). This is
   expected, not a bug: it's comparing two functions under mismatched
   conventions.
2. **Real production convention**: C++ `sample_bilinear_bottom_left(surface,
   u,v)` **unflipped** (the natural extension of the already-established
   `sample_nearest_bottom_left` unflipped convention) vs JS's **actual**
   `#texture` dispatch for `filter==='linear'`
   (`glsl-runtime.js:198`: `sampleBilinear(surface, coord[0], 1 -
   coord[1])` — JS **does** flip `v` before calling the raw sampler).
   **Bit-exact agreement on all 14×4 = 56 channel values**, including
   every out-of-range coordinate (verified via raw `.f32` binary
   comparison, not decimal-string diffing, to rule out `%.9g` truncation
   artifacts).

```
$ clang++ ... -I.../noisemaker-for-cpp/include -o gap3b_sampler_compare gap3b_sampler_compare.cpp \
    .../src/sampler.cpp .../src/surface.cpp .../src/numeric.cpp
$ ./gap3b_sampler_compare
$ node gap3b_sampler_compare_probe.mjs
```
`gap3b_sampler_compare_output.f32` vs `gap3b_sampler_compare_reference.f32`
(nearest + bilinear-production-convention, 14 coords × 8 floats):
```
lanes: 112 exact matches: 112 max abs diff: 0.0
```
**Do the two samplers agree at out-of-range UV? YES**, under matching
conventions (nearest: identical call; bilinear: C++ unflipped ==
JS flipped, which is JS's real production behavior). **This is a
finding worth carrying into the integration work, not a bug**: since
`sample_bilinear_bottom_left` has no current call sites, whoever wires up
`texture()`-with-`filter==='linear'` for the 17 programs must call it
**unflipped** (`sample_bilinear_bottom_left(surface, u, v)`, matching the
existing nearest-sampler pattern) — NOT with a JS-style `1-v` pre-flip
applied on top, which would double-flip and silently break bilinear
texture sampling. No MAJOR disagreement was found between the samplers
themselves.

### 3c. End-to-end: texture()-sample at a probed off-canvas UV, then derivative: **PASS**

**Files**: `gap3c_texture_edge.cpp` (links the real sampler/surface
sources again), `gap3c_texture_edge_probe.mjs` (uses the real
`runtime.stdlib.texture`, i.e. the actual `#texture` dispatcher, with
`surface.filter = 'linear'`).

Kernel: `float t = texture(surface, ctx.uv).r; gx=dFdx(t); gy=dFdy(t);
fw=fwidth(t);` — mirrors `bulge`/`pinch`/`spiral`/`tunnel`/`warp`'s pattern
of texture-sampling using a UV that flows into derivative-dependent state,
on the same 7×5 odd canvas as 3a, with a matching 7×5 distinctive texture.

Because the quad mechanism only ever probes **one** pixel past the canvas
edge, the off-canvas UV it produces is always **exactly** at the `1.0`
boundary (e.g. `u = (x0+1)/W = W/W = 1.0`), never further out (e.g. `1.3`)
— broader out-of-range coverage (`1.5`, `1.7`, `-0.3`, `-2.3`, etc.) is
what 3b covers directly at the sampler level; 3c's job is confirming that
*this specific, real* off-canvas-probe-driven value flows correctly
end-to-end through `texture()` and into the derivative machinery.

```
$ clang++ ... -o gap3c_texture_edge gap3c_texture_edge.cpp .../sampler.cpp .../surface.cpp .../numeric.cpp
$ ./gap3c_texture_edge
$ node gap3c_texture_edge_probe.mjs
```
`gap3c_texture_edge_output.f32` vs `gap3c_texture_edge_reference.f32` (7×5 × 4 lanes):
```
lanes: 140 exact matches: 140 max abs diff: 0.0
```
**PASS — 140/140 exact.**

---

## Summary

| Gap | Case | Result | Lanes |
|---|---|---|---|
| 1 | vec3/vec4 dFdx/dFdy/fwidth, incl. narrowing-asymmetry sensitivity case | **PASS** | 1536/1536 exact, max abs diff 0.0 |
| 2a | 6-site interleaved, mixed kind/width, helper called twice | **PASS** | 576/576 exact, max abs diff 0.0 |
| 2b | Missing-ordinal fallback (per-corner-varying call count) | **PASS**, fallback confirmed genuinely exercised (record counts 3 vs 2) | 192/192 exact, max abs diff 0.0 |
| 3a | Odd (7×5) canvas, genuine off-canvas quad probes | **PASS** | 140/140 exact, max abs diff 0.0 |
| 3b | Sampler-vs-sampler at out-of-range UV (nearest + bilinear) | **PASS under matching conventions**; naive mismatched-convention comparison intentionally disagrees (documented, not a bug) | 112/112 exact, max abs diff 0.0 |
| 3c | texture()-sample at probed off-canvas UV, then derivative | **PASS** | 140/140 exact, max abs diff 0.0 |

**Total: 2196/2196 exact float32 lanes across all six verification programs, max abs diff 0.0 everywhere.**

**Everything requested was constructible.** No gap was left unclosed or
unverifiable. The one genuine finding worth flagging prominently for the
integration work (not a defect, but a decision point with a wrong-answer
failure mode): `sample_bilinear_bottom_left` has no production call sites
yet, and it must be invoked **unflipped** (matching the established
`sample_nearest_bottom_left` convention) to agree with JS — a `1-v`
pre-flip at the call site (mirroring JS's own caller-side flip) would be
wrong for the C++ function, which already bakes the flip into its own
addressing.

## Files

All under `docs/port-engineering/derivatives/`, each with a
`.sha256` sidecar:

- `derivative_lib.hpp` — shared C++ core (vec2/vec3/vec4 derivative
  overloads, generic quad driver, narrowing-asymmetry-faithful sample
  computation).
- `gap1_vec34.cpp` / `gap1_vec34_probe.mjs` + outputs
  (`gap1_vec34_output.{csv,f32}`, `gap1_vec34_reference.{csv,f32}`).
- `gap2_multisite.cpp` / `gap2_multisite_probe.mjs` + outputs
  (`gap2a_interleaved_output.{csv,f32}`, `gap2a_interleaved_reference.{csv,f32}`,
  `gap2b_branchy_output.{csv,f32}`, `gap2b_branchy_reference.{csv,f32}`).
- `gap3a_odd_canvas.cpp` / `gap3a_odd_canvas_probe.mjs` + outputs
  (`gap3a_odd_canvas_output.{csv,f32}`, `gap3a_odd_canvas_reference.{csv,f32}`).
- `gap3b_sampler_compare.cpp` / `gap3b_sampler_compare_probe.mjs` + outputs
  (`gap3b_sampler_compare_output.{csv,f32}`, `gap3b_sampler_compare_reference.{csv,f32}`).
- `gap3c_texture_edge.cpp` / `gap3c_texture_edge_probe.mjs` + outputs
  (`gap3c_texture_edge_output.{csv,f32}`, `gap3c_texture_edge_reference.{csv,f32}`).

Pre-existing, untouched: `derivatives-architecture.md`, `prototype.cpp`,
`reference_probe.mjs`, `prototype_output.*`, `reference_output.*`,
`runtime-patch.hpp.txt`.
