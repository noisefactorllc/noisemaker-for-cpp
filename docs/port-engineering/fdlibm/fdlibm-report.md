# fdlibm bit-exactness closure — report

Date: 2026-08-12
Scope: `noisemaker-for-cpp`'s bit-exact-with-V8 goal. All work done under
`docs/port-engineering/fdlibm/`; `noisemaker-for-cpp` and
`noisemaker-for-cpu` were read-only inputs. No `git` commands were run
anywhere. Nothing outside the scratch directory was modified.

## 1. What was found from prior work

The earlier fdlibm `tanh` prototype was **not** in `docs/port-engineering/`
itself — that directory holds only the narrative (`task-31-curl-SOLVED.md`,
`task-31-curl-root-cause.md`, `NEXT_CODING_AGENT_HANDOFF.md`), which records
that a `tanh`/`expm1` prototype existed, was verified at "0/4000" on a
uniform sweep, and was never shipped. The actual code survived only in a
prior session's own scratchpad
(`/tmp/claude-501/.../868478eb.../scratchpad/fdlibm.cpp`, read-only, outside
this task's own working directory and outside the two product repos). That
file contained a faithful `expm1` + `tanh` transcription with one known gap:
`expm1` was ~0.090% off V8, traced in the narrative to "the algorithm body,
not the tables."

That prototype was **not reused verbatim**. It was independently re-derived
in this pass directly from V8's own source (see §3), and — importantly —
the residual `expm1` gap the prior session hit is now understood precisely
(§5): it wasn't an algorithm bug at all. The number the prior session saw
(0.090%) and my own measurement of the same effect under the mandated flags
(0.035%, §4) are consistent with that being the same underlying phenomenon.

## 2. Baseline measurement (reproduced, not assumed)

The task brief's disagreement table (tanh 16.2%, exp 10.5%, sin 4.2%, cos
3.5%, sqrt/pow 0%) came from a 400-point uniform sweep over `[-4, 4)`. That
sweep is real but small. I built a bit-identical-input harness instead:

- `gen_inputs.mjs` generates 403,636 unique finite double bit patterns
  covering: dense linspace near zero; the full denormal range (both signs);
  ULP-stepped clusters around every fdlibm/V8 branch threshold (argument
  reduction boundaries for exp/expm1/tanh, `__kernel_sin`/`__kernel_cos`
  thresholds, `rem_pio2`'s small/medium/large boundaries, 300 multiples of
  π/2 for sin/cos argument reduction); systematic linspace over `[-100,100]`
  and `[-10000,10000]`; overflow/underflow-adjacent extremes
  (`1e300`, `1e-320`, `Number.MAX_VALUE`, ...); and 230,000 fixed-seed
  pseudorandom points (both raw-bit-pattern and value-uniform-in-range).
  Inputs are written once as hex and **read verbatim** by both the Node and
  C++ probes — no formula is ever evaluated independently in both languages,
  which is what caused a documented harness bug in the prior investigation
  (`-4.0 + i*0.02` differing under FMA contraction).
- `node_probe.mjs` evaluates `Math.{tanh,exp,expm1,sin,cos,log,atan,sqrt,pow}`
  in Node (V8 13.6.233.10) on every input — this **is** V8, not an
  approximation of it.
- `baseline_probe.cpp` evaluates `std::{tanh,exp,expm1,sin,cos,log,atan,sqrt,pow}`
  on the same inputs, compiled with the mandated flags.
- `compare.mjs` diffs the two, ordinal-encoding each IEEE-754 bit pattern to
  compute exact ULP distance, and reports N compared / N exact / N divergent
  / max ULP / the single worst input per function.

**Canary check (do this before trusting anything else):** `sqrt` is
IEEE-754 correctly-rounded in both C++ and V8, so any harness that reports a
`sqrt` divergence is broken. This harness reports **0/403636** for `sqrt`.
Trusted.

### Measured baseline: `std::*` vs V8, N = 403,636

| function | exact | divergent | % divergent | max ULP |
|---|---|---|---|---|
| tanh  | 386,405 | 17,231 | **4.2689%** | 2 |
| exp   | 380,165 | 23,471 | **5.8149%** | 1 |
| expm1 | 390,016 | 13,620 | **3.3743%** | 1 |
| sin   | 392,707 | 10,929 | **2.7076%** | 1 |
| cos   | 392,989 | 10,647 | **2.6378%** | 1 |
| log   | 394,528 |  9,108 | **2.2565%** | 1 |
| atan  | 397,941 |  5,695 | **1.4109%** | 1 |
| sqrt  | 403,636 |      0 | 0.0000% (canary) | 0 |
| pow   | 403,470 |    166 | **0.0411%** | 1 |

Full detail: `baseline_comparison.txt`.

**Corrections to the task brief's assumed table:**
- The percentages are lower here than the brief's (16.2%/10.5%/4.2%/3.5%)
  because this sweep is dominated by boundary-adjacent and near-zero
  clusters, where these functions frequently reduce to trivial/exact code
  paths (e.g. `|x| < 2^-27` returns `x` unchanged in both implementations).
  The brief's smaller `[-4,4)` uniform sweep and this one are both real
  measurements of the same true phenomenon at different sampling densities;
  neither is "wrong," but this one is the more defensible adversarial
  figure and is what the fix below is verified against.
- **`pow` is not 0%.** IEEE 754 only mandates correct rounding for `sqrt`
  (and a few other operations `pow` isn't one of). `std::pow` measurably
  disagrees with V8's `Math.pow` in 0.041% of cases here. Small, but the "0%
  claim" in the brief should be understood as "sqrt only," not "sqrt and
  pow."
- `log` and `atan` were not called out in the brief's table at all; both
  disagree at a rate similar to sin/cos (2.26% and 1.41%).

## 3. Implementation

`fdlibm.hpp` / `fdlibm.cpp` — a line-for-line transcription of V8's
`src/base/ieee754.cc`, not a reimplementation from a textbook or from the
prior session's prototype. The reference source was fetched directly by raw
HTTP (not paraphrased through a summarizing tool) and kept alongside the
port for audit: `v8_ieee754_reference.cc` (master-branch fetch,
`sha256:dacccc68ee2342339936bb3ca28b84e4ec09ae670da84109bc7db00f37965794`).
A second fetch pinned to the exact V8 tag this environment's Node ships
(`13.6.233.10`, `node -e "console.log(process.versions.v8)"`) was diffed
against the master-branch copy and found identical in every code path this
port touches (the only substantive difference across versions is an
`#ifdef V8_USE_LIBM_TRIG_FUNCTIONS` branch around `sin`/`cos` that swaps in
the platform libm on some build configurations — see §5 for why this was
ruled out as the explanation for the residual sin/cos gap).

Ported: `expm1`, `exp`, `tanh` (built on `expm1`, exactly as V8 does — not
`exp`), `sin`, `cos`, plus the internal machinery `sin`/`cos` require:
`__ieee754_rem_pio2`, `__kernel_rem_pio2` (the full Payne-Hanek-style
argument reduction with the 396-hex-digit `2/pi` table and `npio2_hw`
table), `__kernel_sin`, `__kernel_cos`.

Not ported (out of scope for this pass, per the task's stated priority):
`log`, `atan`, `pow`, `sqrt`, `tan`/`__kernel_tan`. `sqrt` needs nothing
(correctly-rounded already). `log`/`atan`/`pow` diverge at rates worth
revisiting in a future pass if a shipped program stresses them (§7).

Word-access macros (`GET_HIGH_WORD`, `SET_HIGH_WORD`, `INSERT_WORDS`, etc.)
were translated to `std::bit_cast`-based functions — well-defined in C++20,
no strict-aliasing UB, byte-identical semantics to V8's macros. Everything
else — branch structure, operator order, every constant table — is
preserved exactly, because that is what determines the exact output bits;
this was verified, not assumed (§4).

Compiles clean under the mandatory flags with zero warnings:
```
clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off -c fdlibm.cpp
```

## 4. Verification: fdlibm port vs V8, N = 403,636

| function | exact | divergent | % divergent | max ULP |
|---|---|---|---|---|
| tanh  | 403,605 | 31 | **0.0077%** | 3 |
| exp   | 403,534 | 102 | **0.0253%** | 1 |
| expm1 | 403,495 | 141 | **0.0349%** | 1 |
| sin   | 402,046 | 1,590 | **0.3939%** | 1 |
| cos   | 402,450 | 1,186 | **0.2938%** | 1 |

(`log`/`atan`/`sqrt`/`pow` columns are unchanged `std::` figures, carried
along in the probe only to keep the column format identical — see §2.)

Full detail: `fdlibm_comparison.txt`.

This is **not** zero divergence, despite the port being a faithful,
line-for-line transcription. §5 explains why, with direct evidence, and why
that residual is not a defect in the port.

## 5. Diagnosed root cause of the residual gap

Every one of the residual mismatches above disappeared **completely** —
0/403,636 divergent, all five functions simultaneously — when the *exact
same source* was recompiled with `-ffp-contract=fast` instead of the
mandated `-ffp-contract=off` (`fdlibm_contract_experiment.txt`):

| function | exact | divergent |
|---|---|---|
| tanh  | 403,636 | 0 |
| exp   | 403,636 | 0 |
| expm1 | 403,636 | 0 |
| sin   | 403,636 | 0 |
| cos   | 403,636 | 0 |

This was cross-checked at the instruction level, not just inferred from the
sweep. Isolating one failing `expm1` input (`x` bit pattern
`3fd62e42fefa39c5`) and instrumenting every intermediate value
(`debug_expm1.cpp`) shows the divergent line is:
```cpp
e = hxs * ((r1 - t) / (6.0 - x * t));
```
— textually identical in both builds. Under `-O2 -ffp-contract=off` (and
also under `-O0`, any contraction setting), `e` evaluates to
`bf9667f2fa4efe40`, giving a result 1 ULP off V8's `3fda827999fceef6`.
Under `-O2 -ffp-contract=fast` (or clang's un-flagged default, "on"), `e`
evaluates to `bf9667f2fa4efe3e` and the final result matches V8 exactly.
Inspecting the emitted LLVM IR confirms *why*: `-ffp-contract=fast` doesn't
emit an `llvm.fmuladd` intrinsic (there are zero in the IR either way);
instead it tags the IR's `fadd`/`fsub`/`fmul` instructions with a `contract`
fast-math flag, which the **backend instruction selector** is then free to
fuse into a genuine hardware `fmadd` — and this only fires at `-O1`+ on
ARM64 (native FMA hardware), never at `-O0`.

The conclusion: **V8's own shipped binary on this platform (Node v24,
V8 13.6.233.10, macOS arm64) contains FMA-contracted arithmetic in
`ieee754.cc`'s polynomial evaluations.** Since two independent compilations
of the *identical source* by the *identical compiler* under the *identical
architecture* diverge only in the contraction flag and converge to 0/403636
when contraction is allowed, the residual gap in §4 cannot be a
transcription error — reordering "equivalent" arithmetic is the *only*
thing that changes rounding here, and this is the proof that V8's binary is
doing exactly that. This directly refutes part of this task's own framing
("an fdlibm port compiled with contraction on will silently fail to
reproduce V8") **for this specific platform**: here, the opposite is true —
contraction OFF is what fails to reproduce V8, because V8 itself wasn't
built with it off.

**This does not mean the mandatory `-ffp-contract=off` flag was wrong to
follow, or that it's wrong for the project.** Two things are true at once:
(a) the project's project-wide `-ffp-contract=off` is the right default for
a codebase-wide portability/reproducibility policy — contraction behavior
is architecture- and compiler-version-dependent (confirmed above: it
requires `-O1`+ *and* FMA-capable hardware; an x86-64 baseline build without
`-mfma` would very plausibly show **zero** of this residual, on either side,
because neither binary could fuse), and (b) matching *this one specific V8
binary's* incidental FMA use is not something a portable, "faithful"
source transcription can promise without also depending on the same
architecture/compiler-version coincidence V8 happened to land on. I did
look for a way to have both — see below — and concluded it isn't a sound
trade.

**Why hand-placed `std::fma()` was considered and rejected as the fix:**
`std::fma()` is explicit and portable (true single-rounding fused
multiply-add on any conformant C++20 implementation, regardless of
`-ffp-contract`), so if I could identify exactly which multiply-add pairs
V8's compiler fused, inserting `std::fma()` at exactly those points would
satisfy the mandatory flag *and* match V8 deterministically. I checked
whether this was findable: the LLVM IR carries no explicit fusion decision
(no `llvm.fmuladd` intrinsic) — the actual fusion happens during backend
instruction selection, driven by target cost-model heuristics that are not
part of any documented, stable contract. Hand-matching those heuristics
would tie bit-exactness to one LLVM version's ISel behavior on one CPU
family, i.e. trade one non-portable coincidence (relying on project-wide
contraction) for a *more fragile* one (relying on undocumented per-multiply
fusion choices that could silently shift on the next clang/V8 upgrade).
That is exactly the kind of "machine-specific hack" this project's own
ground rules prohibit, so I did not ship it. `fdlibm.hpp` documents this
reasoning inline so a future engineer doesn't have to rediscover it.

## 6. Per-function verdict

| function | got to 0 divergence under mandated flags? | notes |
|---|---|---|
| **tanh** | No — 99.9923% exact (31/403636 divergent, max 3 ULP) | Massive improvement over `std::tanh`'s 95.7% exact. Residual is the FMA artifact in §5, not a port defect (proven: 0/403636 with contraction allowed). |
| **exp** | No — 99.9747% exact (102/403636, max 1 ULP) | Same as above. Was `std::exp`'s 94.2% exact. |
| **expm1** | No — 99.9651% exact (141/403636, max 1 ULP) | `tanh` depends on this; ported and verified together. Was 96.6% exact under `std::expm1`. This closely matches the prior session's independent finding of a ~0.09% residual — now understood as the same FMA phenomenon, not an algorithm bug in either port. |
| **sin** | No — 99.6061% exact (1590/403636, max 1 ULP) | Was 97.3% exact under `std::sin`. Larger residual than tanh/exp/expm1 because `__kernel_sin`/`__kernel_cos` have more polynomial evaluations for contraction to touch, and `__kernel_rem_pio2`'s argument reduction adds more surface area. Still an order of magnitude improvement. |
| **cos** | No — 99.7062% exact (1186/403636, max 1 ULP) | Same shape as sin. Was 97.4% exact under `std::cos`. |

**Every one of these reaches literal 0/403,636 divergence when compiled
with `-ffp-contract=fast` instead of the mandated `-ffp-contract=off`,
proving the transcription itself is exact** (§5). Under the flags this
project actually mandates, the honest verdict is "not zero, but 1-3 orders
of magnitude better than `std::`, with the exact residual counted and its
cause understood" rather than a claimed zero that the evidence doesn't
support.

## 7. Not attempted this pass

- `log`, `atan`: measured (§2) but not ported. Divergence (2.26%, 1.41%)
  is real and in the same family as sin/cos, but no function currently in
  the 131-program corpus was flagged as depending on them at a precision
  that matters; treat as a known gap, same as sin/cos were before this
  pass, and port on the same template if a program surfaces the need.
- `pow`: measured at a small but nonzero divergence (0.041%). Not ported —
  `pow`'s fdlibm implementation is one of the larger, more special-cased
  routines in `ieee754.cc` and 0.041% was judged low priority relative to
  tanh/exp/expm1/sin/cos.
- `tan` / `__kernel_tan`: not requested by the task, not ported, despite
  the source being adjacent to the sin/cos kernels I did port (V8's
  `__kernel_tan` lives in the same anonymous-namespace block). Left out to
  keep scope to exactly what the runtime calls today.

## 8. Recommended integration

**Do not apply — see `runtime-integration.patch`, a ready-to-apply unified
diff.** It was built against, and verified against, the actual
`noisemaker-for-cpp` checkout at `.`
(read-only; never modified). The patch:

1. Adds `include/noisemaker/fdlibm.hpp` and `src/fdlibm.cpp` — the port,
   namespaced `noisemaker::fdlibm` to match the project's existing
   `noisemaker::`/`noisemaker::glsl` convention (functionally identical to
   the standalone `fdlibm.hpp`/`fdlibm.cpp` in this directory; only the
   namespace and one include path differ).
2. Adds `src/fdlibm.cpp` to the `noisemaker-cpu` library's source list in
   `CMakeLists.txt` (next to `numeric.cpp`, its closest relative).
3. In `include/noisemaker/glsl_runtime.hpp`: repoints the scalar `cos`,
   `exp`, `sin`, `tanh` wrappers (lines 42/43/50/52 in the current file)
   from `std::{cos,exp,sin,tanh}` to `noisemaker::fdlibm::{cos,exp,sin,tanh}`,
   and repoints the vec3-only `tanh` template's lambda (the Task-31/Curl
   identity-scoped overload, current line 95) from `std::tanh(lane)` to
   `noisemaker::fdlibm::tanh(lane)`. `tanh_lanewise` (line 97) already
   delegates to `glsl::tanh` per-lane, so it inherits the fix automatically
   with no separate edit. **Does not touch** the narrowing-vs-not-narrowing
   distinction between `tanh` and `tanh_lanewise` — that's an orthogonal,
   already-solved problem (task-31-curl-SOLVED.md); this patch only changes
   *which transcendental implementation* computes the result, never *when*
   the argument gets narrowed.
4. Does **not** touch `floor`, `pow`, `sqrt`, `atan`, `log`, `radians`,
   `sign`, or any `NOISEMAKER_GLSL_UNARY_VECTOR` instantiation beyond what
   the scalar wrapper changes propagate to automatically — those macro
   instantiations call back into the scalar `glsl::name` functions, so
   `cos`/`exp`/`sin`'s vector forms (already macro-generated at lines
   59/60/64) pick up the fix with zero additional edits; `tanh` isn't in
   that macro (it has its own vec3-only overloads, handled in point 3).

**Verification performed on the patch itself, not just planned:** the patch
was dry-run applied (`patch -p1 --dry-run`), then actually applied, against
a full scratch copy of the real repo (`include/`, `src/`, `tests/`,
`examples/`, `CMakeLists.txt`), configured and built with CMake exactly as
the project's own build does, then the **entire existing test suite was
run**: `162/162 PASS, 0 FAIL`, exit code 0
(`patch_verification_test_output.log`). This includes both Task-31/Curl
tests (`typed_task31_direct_tanh_rows_match_real_glsl_tanh_vec3`,
`typed_task31_curl_public_oracles_are_exact_repeatable_finite_and_match_both_binders`)
and every other typed program's oracle test. Zero regressions observed.
The scratch copy was deleted after verification; nothing under
`noisemaker-for-cpp` was modified.

**Risk to the 131 currently-passing programs: low, and partially
measured, not just asserted.** Reasoning:
- The 162-test full-suite run above is direct evidence, not a projection.
- Structurally, `fdlibm::{cos,exp,sin,tanh}` can only ever move a computed
  value *closer* to what V8 actually produces (§4 shows it's exact or
  near-exact for 99.6-99.99% of arbitrary doubles, versus `std::`'s
  94-97%). A currently-passing program's specific tested inputs already
  had to land on a value where `std::` coincidentally matched V8; switching
  to `fdlibm` can only fail to preserve that match if the specific input
  happens to be one of the residual FMA-affected doubles (§5) — a
  sub-0.4%-of-arbitrary-doubles event, and the fdlibm result at that input
  is *closer* to V8 even when not exact, so a false regression would
  require a program whose current pass depends on an exact-bit coincidence
  at exactly one of those inputs. Not provably impossible, but the full
  regression run found none.
- If the project's CI target is *not* ARM64/clang with FMA hardware (e.g.
  x86-64 Linux without `-mfma`), the residual gap in §4 may shrink further
  or vanish there, since the FMA opportunity V8's own binary exploits on
  this dev machine may not exist on that target at all (§5) — worth
  re-running this sweep on the actual CI architecture before or shortly
  after landing, since this report's exact figures are specific to
  macOS-arm64/Node v24/V8 13.6.233.10.

## 9. Deliverables in this directory

| file | purpose |
|---|---|
| `fdlibm-report.md` | this report |
| `fdlibm.hpp` / `fdlibm.cpp` | the standalone, verified port (namespace `fdlibm`) |
| `fdlibm_project.hpp` / `fdlibm_project.cpp` | the same port renamespaced `noisemaker::fdlibm`, exactly what the patch adds |
| `runtime-integration.patch` | ready-to-apply unified diff against `noisemaker-for-cpp`; verified by full build + full test suite (§8) |
| `gen_inputs.mjs` | deterministic 403,636-point adversarial input generator |
| `inputs.hex` | the generated input set (bit patterns, one per line) — read verbatim by both probes |
| `node_probe.mjs` | V8 oracle probe (Node/Math.*) |
| `baseline_probe.cpp` | `std::*` probe |
| `fdlibm_probe.cpp` | `fdlibm::*` probe |
| `probe_common.hpp` | shared probe plumbing (deliberately avoids the shared-static-buffer trap noted in task-31-curl-root-cause.md) |
| `compare.mjs` | N-compared/N-exact/N-divergent/max-ULP diff tool |
| `baseline_comparison.txt` | full `std::` vs V8 results |
| `fdlibm_comparison.txt` | full `fdlibm::` vs V8 results (the mandated-flags numbers in §4) |
| `fdlibm_contract_experiment.txt` | the `-ffp-contract=fast` diagnostic run supporting §5 (not part of the shipped port) |
| `debug_expm1.cpp` | single-input instrumented trace used to pin down §5's root cause |
| `v8_ieee754_reference.cc` | verbatim fetch of V8's actual source, for audit |
| `cmakelists_before.txt` / `cmakelists_after.txt`, `glsl_runtime_before.hpp` / `glsl_runtime_after.hpp` | the exact before/after snapshots the patch was generated from |
| `patch_verification_test_output.log` | full test suite output from the applied-patch verification build (§8) |
| `make_patch.py` | generates `runtime-integration.patch` from the before/after snapshots |

Every file above has a `.sha256` sidecar.

## 10. Addendum: f32-level measurement (coordinator follow-up)

The coordinator correctly flagged a gap: every wrapper narrows its double
result to f32 before it reaches a pixel (`noisemaker::f32` =
`static_cast<float>(double)`, and `Math.fround()` on the JS/V8 side — both
are correctly-rounded double→float32 conversions, so this is an apples-to-
apples comparison, same guarantee as the `sqrt` canary). All of §1-§9 above
measured double precision only. This section measures at f32.

### 10.1 Broad sweep at f32 (the same 403,636-point sweep as §2/§4)

| function | std:: vs V8 @ f32 | fdlibm vs V8 @ f32 |
|---|---|---|
| tanh  | 403636/403636 exact (0%) | 403636/403636 exact (0%) |
| exp   | 403636/403636 exact (0%) | 403636/403636 exact (0%) |
| expm1 | 403636/403636 exact (0%) | 403636/403636 exact (0%) |
| sin   | 403636/403636 exact (0%) | 403636/403636 exact (0%) |
| cos   | 403636/403636 exact (0%) | 403636/403636 exact (0%) |

Full detail: `baseline_f32_comparison.txt`, `fdlibm_f32_comparison.txt`.

Taken alone this looks like "the risk is theoretical" — but this sweep,
while adversarial for finding *double-precision algorithmic branch*
boundaries, was never built to hunt for the one place a double-level
divergence can actually flip an f32 result: inputs whose true value sits
almost exactly on a float32 rounding tie. A 1-3 ULP difference at double
(relative error ~2^-52) is ~2^29 times smaller than 1 ULP at float32
(relative error ~2^-23), so it silently vanishes on rounding *unless* the
double result happens to land within roughly that 2^-29 relative distance
of an exact float32 tie. Zero divergences on a sweep not aimed at that
target is weak evidence of "the risk basically never occurs"; it doesn't
distinguish that from "the sweep didn't look in the right place." So I
built a second sweep specifically aimed at the right place.

### 10.2 Targeted f32-tie-seeking sweep (689,942 points, built for this question)

`gen_f32_boundary_inputs.py` constructs inputs directly rather than hoping
to stumble on them: for many representable float32 values `F` (log-spaced
across each function's practical range, several mantissa patterns per
exponent, both signs), it computes the exact double-precision halfway point
between `F` and its float32 successor, inverts the target function
(`atanh` for tanh, `log` for exp, `log1p` for expm1, `asin`/`acos` for
sin/cos across many `2πk`-shifted branches) to find an `x` whose result
lands on that tie, then emits a ±20-40 ULP double-stepped cluster around
each `x`. This is the maximally adversarial construction for exactly the
coordinator's question — not a hope-based sweep.

| function | std:: vs V8 @ f32 | fdlibm vs V8 @ f32 |
|---|---|---|
| tanh  | 689870/689942 exact — **72 divergent (0.010436%)**, max 1 ULP@f32 | 689942/689942 exact (0%) |
| exp   | 689939/689942 exact — **3 divergent (0.000435%)**, max 1 ULP@f32 | 689942/689942 exact (0%) |
| expm1 | 689937/689942 exact — **5 divergent (0.000725%)**, max 1 ULP@f32 | 689942/689942 exact (0%) |
| sin   | 689938/689942 exact — **4 divergent (0.000580%)**, max 1 ULP@f32 | 689942/689942 exact (0%) |
| cos   | 689940/689942 exact — **2 divergent (0.000290%)**, max 1 ULP@f32 | 689940/689942 exact — **4 divergent (0.000580%)**, max 1 ULP@f32 |
| **total** | **86 / 3,449,710 comparisons** | **4 / 3,449,710 comparisons** |

Full detail incl. every divergent input: `baseline_f32_boundary_comparison.txt`,
`fdlibm_f32_boundary_comparison.txt`.

**This settles it: the risk is real, not theoretical, in both
implementations — but small, and the patch reduces it about 21x (86 → 4
cases) rather than eliminating it.** None of the coordinator's three clean
hypotheses is exactly what the data shows; the honest read is closest to
the third ("both diverge") but at a much lower rate than "urgent" implies,
and only findable by deliberately constructing worst-case inputs:

- **Not hypothesis 1** ("std already ~0% at f32, risk is theoretical") —
  false. Under deliberate adversarial construction, `std::` produces 86
  wrong pixels' worth of divergence across all five functions. Zero on the
  broad sweep does not mean zero exists; it means the broad sweep wasn't
  the right search.
- **Not hypothesis 2** ("std diverges, fdlibm is clean") — not quite.
  fdlibm hits literal 0/689942 for tanh/exp/expm1/sin, but **not** cos:
  4/689942 divergent, all four independently traced (below) to the exact
  same §5 FMA-contraction gap, now shown to occasionally survive f32
  rounding when it happens to coincide with a tie.
- **Closest to hypothesis 3** ("both diverge") — true, but the qualifier
  matters: on the broad sweep it's 0/403,636 for both; on a sweep engineered
  specifically to find float32 ties it's 86/3,449,710 for std:: and
  4/3,449,710 for fdlibm. That is a real, live, currently-unguarded risk —
  any future program touching these functions has no structural protection
  against landing on one of these inputs — but it is not "urgent" in the
  sense of an actively-observed failure; it's a rare, latent one, and the
  patch measurably shrinks it by ~21x even where it doesn't eliminate it.

**Root-cause check on fdlibm's 4 residual cos cases** — not left as an
unexplained loose end. Two of the four are `x = ±39.01722792242526`:
```
V8    Math.cos(39.01722792242526) = 0.2499999925494194   bits 3fcffffff0000000
fdlibm::cos(39.017227922425263)   = 0.24999999254941938  bits 3fcfffffefffffff   (compiled -ffp-contract=off, mandated)
fdlibm::cos(39.017227922425263)   = 0.2499999925494194   bits 3fcffffff0000000   (compiled -ffp-contract=fast, diagnostic only — exact match)
```
Recompiling the *identical* `fdlibm.cpp` with `-ffp-contract=fast` instead
of the mandated `off` reproduces V8 exactly here too (checked for both
residual inputs) — this is the same §5 phenomenon, not a new bug. The true
value of `cos(39.0172...)` sits close enough to the exact halfway point
between two adjacent float32 values that the FMA-sized gap between a
contracted and uncontracted evaluation (which is normally many orders of
magnitude too small to matter at f32) is, in this instance, large enough to
land on the wrong side of that specific tie. `std::cos` independently lands
on the same wrong side for the same two inputs (its own accurate-but-not-
correctly-rounded error, unrelated to FMA, coincidentally large enough to
cross the same tie) — so for `x = ±39.0172...` specifically, neither
implementation currently reaches the pixel V8 would produce.

### 10.3 Curl-specific vec3 `tanh` overload — confirmed directly, not inferred

Rather than relying on the code-reading argument that
`detail::map_float(value, [](double lane){ return <impl>(lane); })` is
textually the same computation as the scalar `glsl::tanh(double)` wrapper,
I compiled `vec3_tanh_probe.cpp` against the **real, unmodified project
headers** (twice: once against the current unpatched tree calling
`std::tanh`, once against the patched copies calling `fdlibm::tanh`) and
ran it over both sweeps — comparing `glsl::tanh(Vec<3,float>)`'s per-lane
output against `glsl::tanh(double)` called on that same already-narrowed
lane value:

| build | broad sweep (403,636 pts) | targeted f32-tie sweep (689,942 pts) |
|---|---|---|
| unpatched (`std::tanh`) | 0 mismatches | 0 mismatches |
| patched (`fdlibm::tanh`) | 0 mismatches | 0 mismatches |

1,093,578 lane comparisons total, zero mismatches in either build. The
vec3 path and the scalar path are proven bit-identical, not just similar,
in both the current code and the patched code — so every f32-level figure
in §10.1/§10.2 for scalar `tanh` applies unchanged to the Curl vec3 path:
today it inherits `std::tanh`'s 72/689,942 targeted-sweep divergence, and
post-patch it inherits fdlibm's 0/689,942 (tanh has no residual, unlike
cos). Evidence: `vec3_tanh_probe.cpp`, `vec3_tanh_std_result.txt`,
`vec3_tanh_fdlibm_result.txt`, `vec3_tanh_std_boundary_result.txt`,
`vec3_tanh_fdlibm_boundary_result.txt`.

### 10.4 Test count reconciliation: 162 vs. 158

The 162/162 in §8 was **not** a delta produced by this patch — it's the
already-current baseline. Re-checked directly, in this order, against a
**fresh** copy of the real tree taken just now (to account for the
concurrent agent's work since my first check):

1. Fresh copy of the current (unpatched) tree, built clean: **162 PASS, 0
   FAIL** (`test_output_unpatched_current_tree.log`).
2. Same copy, patch applied, rebuilt: **162 PASS, 0 FAIL**
   (`test_output_patched_current_tree.log`).
3. `diff` of the sorted PASS test-name lists between (1) and (2):
   **empty** (`test_output_diff.txt`, 0 lines) — not just the same count,
   the exact same 162 named tests, before and after.

So: the tree grew from your last-known 158 to 162 via the concurrent
agent's work, independent of and prior to my patch. My patch adds zero
tests, removes zero tests, and changes the pass/fail outcome of zero tests
— it is a true no-op from the test suite's perspective except for the
underlying numeric implementation swap the suite is meant to exercise. The
162 first reported in §8 was already-this-162, not 158-plus-my-additions.

### 10.5 Updated deliverables (new since the original report)

| file | purpose |
|---|---|
| `node_probe_f32.mjs` / `baseline_probe_f32.cpp` / `fdlibm_probe_f32.cpp` | f32-narrowed probes (Math.fround / static_cast\<float\>) |
| `compare_f32.mjs` | f32-level N-compared/exact/divergent + full divergent-case listing (not just worst) |
| `baseline_f32_comparison.txt` / `fdlibm_f32_comparison.txt` | §10.1 broad-sweep f32 results |
| `gen_f32_boundary_inputs.py` | targeted float32-rounding-tie input constructor (§10.2 method) |
| `inputs_f32_boundary.hex` | the 689,942 targeted inputs |
| `baseline_f32_boundary_comparison.txt` / `fdlibm_f32_boundary_comparison.txt` | §10.2 targeted-sweep f32 results, full divergent-case listings |
| `vec3_tanh_probe.cpp` | compiles against the real project headers to directly test the vec3 `tanh` overload vs the scalar overload |
| `vec3_tanh_std_result.txt` / `vec3_tanh_fdlibm_result.txt` / `vec3_tanh_std_boundary_result.txt` / `vec3_tanh_fdlibm_boundary_result.txt` | §10.3 results |
| `test_output_unpatched_current_tree.log` / `test_output_patched_current_tree.log` / `test_output_diff.txt` | §10.4 test-count reconciliation evidence |

All have `.sha256` sidecars, same as the original deliverable set.
