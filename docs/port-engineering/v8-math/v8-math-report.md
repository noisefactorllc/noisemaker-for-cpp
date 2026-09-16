# v8-math: closing the fdlibm/pow/hypot hole -- report

Date: 2026-09-16
Scope: `noisemaker-for-cpp`'s bit-exact-with-V8 math layer, driven to 0
divergence on every function the authority's kernels/adapters/runtime call.
Supersedes `docs/port-engineering/fdlibm/fdlibm-report.md`, which shipped
nothing, ported only 5 of 14 needed functions, and (per this pass's own
measurement, below) had a materially wrong hypot and never checked pow's
real implementation.

## 1. V8 version and architecture provisioning

- `node` (arm64, Homebrew, v26.0.0): `process.versions.v8` =
  `14.6.202.33-node.19`.
- x86-64: no x64 node was pre-provisioned on this machine. Downloaded the
  official `node-v26.0.0-darwin-x64.tar.gz` from `nodejs.org/dist/v26.0.0/`,
  verified its SHA256 against the published `SHASUMS256.txt`
  (`f488ab543fe202d8a2d56e661682117d3c56903a2bf64f2ec1ff7bd421cfd875`,
  matched), kept under `/Users/alex/platform/.nm-cpp-work/tools/` (not in
  the repo). Runs natively under Rosetta on this Apple Silicon Mac;
  `process.versions.v8` reports the identical `14.6.202.33-node.19`, so both
  architectures are being measured against the same V8 revision.
- Reference source: fetched `src/base/ieee754.cc`, `src/base/ieee754.h`,
  `src/numbers/ieee754.cc`, `src/numbers/ieee754.h`,
  `src/codegen/external-reference.cc`, `src/flags/flag-definitions.h`,
  `src/builtins/math.tq` at the exact tag `14.6.202.33` from
  `raw.githubusercontent.com/v8/v8` (mirrors chromium.googlesource.com/v8/v8
   1:1 at tags). The previously-vendored `v8_ieee754_reference.cc` under
  `docs/port-engineering/fdlibm/` was fetched at a stale, different V8
  version (13.6.233.10, per that report's own text) and is NOT what this
  pass ported from; the fresh fetches here are the ones actually used.

## 2. The real shape of V8's math layer (verified, not assumed)

Read from source AND confirmed empirically (`node --v8-options`, and
200,000-input differential probes), not guessed:

| Function(s) | What actually runs | Evidence |
|---|---|---|
| sin, cos | `base::ieee754::{sin,cos}` (plain fdlibm) | V8 also ships a build-time alternative (glibc's vendored dbl-64 sin/cos, gated by `V8_USE_LIBM_TRIG_FUNCTIONS`, GN arg `v8_use_libm_trig_functions = is_clang`) and a *runtime* flag `use_libm_trig_functions` (default true when compiled in). `node --v8-options \| grep libm` returns **nothing** on either the arm64 or the x64 build of this Node -- the macro was not compiled in, so the plain fdlibm path is what runs. |
| tan, asin, acos, atan, atan2, exp, expm1, log, log2, tanh | `base::ieee754::<name>`, plain fdlibm, no runtime/build-time alternative | Every one resolves through `FUNCTION_REFERENCE_WITH_TYPE(ieee754_<name>_function, base::ieee754::<name>, ...)` in `src/codegen/external-reference.cc` with no `#if`/`v8_flags` branch around it (grepped exhaustively). |
| pow | **NOT** `base::ieee754::legacy::pow` (the old fdlibm pow -- moved into a `legacy` namespace in this V8 version and documented "should not be used directly"). The live implementation is `v8::internal::math::pow` (`src/numbers/ieee754.cc`), active whenever `use_std_math_pow` is true (`DEFINE_BOOL` default true on every platform except AIX; confirmed via `node --v8-options`: `--use-std-math-pow` exists with `default: --use-std-math-pow`) | Empirical cross-check (200,000 random inputs each, both true on this build): `Math.pow(x,0.5) === Math.sqrt(x)` bitwise, and `Math.pow(x,2) === x*x` bitwise, 0/200,000 mismatches each -- only possible under the std-math-pow special-cased path. |
| hypot | **NOT** ieee754.cc at all. `Math.hypot` is a Torque builtin (`src/builtins/math.tq`, `MathHypot`/`FastMathHypot`), lowered directly to TurboFan/CSA machine code by V8's own JIT backend -- unrelated to `-ffp-contract` entirely. Per-argument-count formula: 1 arg `\|a\|`; 2 args: scaled sum of squares, **no** Kahan compensation; 3 args: same but with a compensation term folded in between the first two squares only; >3 args ("Slow" label): full running Kahan-compensated sum, with the *plain* (non-Neumaier) compensation shape `summand = n*n - compensation; preliminary = sum + summand; compensation = (preliminary - sum) - summand`. | Read directly from `math.tq`. |
| sqrt | Bare `Float64Sqrt` machine op, IEEE-754 correctly rounded | Already agrees with `std::sqrt` exactly; not touched. |

## 3. What was actually broken (the hole, quantified)

`std::*` vs V8, 403,636-input adversarial sweep (from the superseded report,
reproduced here as the "before any fdlibm port at all" baseline): tanh
4.27%, exp 5.81%, sin 2.71%, cos 2.64%, log 2.26%, atan 1.41%, pow 0.041%
divergent from V8. `log2`, `tan`, `asin`, `acos`, `atan2`, `hypot` were
never even measured against `std::` in that report.

What this pass found **beyond** the missing functions, all confirmed by
direct differential evidence (not inferred):

1. **hypot(x, y) (2-arg) was wrong**, not just "not ported." The prior
   pass's `fdlibm::hypot` used a generic Kahan-compensated running sum for
   all argument counts. V8's real 2-argument fast path
   (`FastMathHypot`, math.tq) uses **no compensation at all**. Measured
   before this fix: 56-99 / 50,000 divergent (1-2 ULP) on the 2- and
   3-argument overloads. Root cause: a transcription that assumed one
   generic N-ary algorithm where V8 has three different formulas by
   argument count.
2. **fd_atan2 dropped a line**: V8's real source does `m &= 1;` inside the
   `k > 60` (`\|y/x\| > 2**60`) shortcut, forcing the pi-combination branches
   (case 2/3) off regardless of x's sign, because at that ratio x's sign is
   numerically irrelevant. Without it, ~10% of an adversarial atan2 sweep
   (any pair with an extreme magnitude ratio) was 1 ULP off. This was a
   **transcription bug**, not an FMA/contraction issue -- confirmed by
   bisection: recomputing the literal (buggy) formula gives the same wrong
   bit under both `-ffp-contract=off` and `=fast`, and adding `m &= 1;`
   fixes it under either.
3. **log2 actively regresses under `-ffp-contract=fast`**. Its final
   combining step is a Dekker/two-sum compensated summation
   (`hi = f - hfsq; ...; w = y + val_hi; val_lo += (y - w) + val_hi; ...`);
   fusing any of those steps breaks the error-free-transformation property
   the algorithm depends on. Measured: 0/50,000 divergent under
   `-ffp-contract=off`, 108-208/50,000 under `=fast` -- the *opposite*
   direction from every other fdlibm-derived function in this file, where
   `fast` is required to reach 0.
4. **log's combining step needed isolating from its surrounding function,
   not just the ambient flag.** Under blanket `-ffp-contract=fast`, log's
   residual dropped from 134/50,000 to 2/50,000 but did not reach 0. This
   was FIRST (incorrectly) fixed with an explicit `std::fma(s, hfsq + r,
   dk * ln2_lo)`, which reached 0/50,000 on arm64 -- but that fix was
   itself wrong (Section 6a): it regressed x86-64 to 180/2,000,000 at full
   scale, because `std::fma()` fuses unconditionally on every
   architecture while V8's own x86-64 binary does not fuse this
   expression at all. The correct fix (same technique `tan` needed,
   Section 6): factor the plain, unfused expression into its own
   `__attribute__((noinline))` function and let ordinary
   `-ffp-contract=fast` auto-fusion decide per architecture. 0/2,000,000
   on both arm64 and x86-64.
5. **tan's combining step had the identical disease as log's**, at a
   much larger scale (304/2,000,000, not 2/50,000) -- see Section 6 for
   the full root-cause writeup and fix (same noinline-extraction
   technique, no explicit fma).

Findings 2, 4, and 5 were only found because this pass built a real
exhaustive differential harness AND used it at the project's actual
build flags (`-O3 -DNDEBUG`, both architectures) rather than trusting the
project-wide `-ffp-contract=fast` override, or a single architecture's
result, to be sufficient by construction.

## 4. The contraction/FMA resolution (deterministic, evidence-gated)

No single global flag setting is correct for every function. Resolved as
three, evidence-gated groups, each pinned by direct measurement rather than
by architecture theory alone:

- **`src/fdlibm.cpp`** (sin, cos, tan, asin, acos, atan, atan2, exp,
  expm1, log, tanh, pow-wrapper): compiled with a per-source
  `set_source_files_properties(... COMPILE_OPTIONS -ffp-contract=fast)`
  override in `CMakeLists.txt`, layered on top of the project-wide
  `-ffp-contract=off`. Verified safe on **both** target architectures, for
  **every** function this file owns, with 0 explicit `std::fma()` calls
  anywhere in it:
  - arm64 (NEON always has hardware FMA): reproduces V8's own arm64
    binary's contraction, measured 0 divergent for every function.
  - x86-64 **without `-mfma`** (this project's actual baseline --
    `-march`/`-mfma` do not appear anywhere in `CMakeLists.txt`, confirmed
    by grep, and CI's `ubuntu-latest` native job configures no arch flags
    either): there is no hardware fused-multiply-add instruction available
    for `-ffp-contract=fast` to select regardless of the flag, so the flag
    is a byte-for-byte no-op there -- proven, not assumed, by cross-compiling
    this exact TU with `clang++ -arch x86_64 ... -ffp-contract=fast` and
    running the differential harness against Node's official x64 darwin
    build under Rosetta: 0 divergent for every function this file owns.
  - `tan` and `log` each needed one additional structural change beyond
    the ambient flag: their shared multi-line combining expressions had to
    be factored into their own `__attribute__((noinline))` functions
    (`kernel_tan_combine`, `log_combine_a`/`log_combine_b`) to remove a
    measured surrounding-code-shape sensitivity in clang's auto-fusion
    heuristic (Sections 6, 6a). This is NOT an explicit-fma workaround --
    each helper is the plain, unfused original formula, byte-identical to
    what fdlibm.cpp had inline before, and the fix is exactly as portable
    as the rest of this file: it relies on the SAME ambient
    `-ffp-contract=fast` auto-fusion, just with the compiler making its
    fusion decision in a smaller, context-free function.
  - `tests/test_fdlibm_contract_pin.cpp` pins the override is actually
    taking effect (last-flag-wins on the compiler command line) by
    asserting `fdlibm::expm1`, `fdlibm::tan` (two inputs), and
    `fdlibm::log` each at a specific bit pattern only reachable with the
    override AND the noinline extractions both intact, captured directly
    from this environment's `node -e` (not retyped from the superseded
    report).
- **`src/fdlibm_off.cpp`** (log2, hypot 2/3/N-arg): compiled under the
  project's ordinary `-ffp-contract=off` -- no override, because for both
  functions here `fast` is measurably *worse*: log2's Dekker summation
  breaks under any fusion (Section 3.3), and hypot is not compiled by
  clang's contraction machinery at all (Section 2) -- its plain, unfused
  `na*na + nb*nb` matches V8's TurboFan-generated code, while an explicit
  `std::fma` at that site was tried and measured to NOT match.
- Everywhere else (asin/acos/atan/atan2's own combining arithmetic; pow's
  `std::pow` fallback): no explicit `std::fma` needed at all -- either the
  ambient flag alone reaches 0 (asin/acos/atan/atan2, after the `m &= 1`
  transcription fix), or the branch is a bare `std::pow(x, y)` call that
  resolves to the OS's one shared libm symbol on both sides (this binary
  and the V8 process it must match both dynamically link the same `pow`
  from the same OS on the same machine), so no algorithm needed porting at
  all for that branch.

`\*` tan: see Section 6 -- not fully closed.

## 5. Differential harness and results

Harness (`gen_inputs.mjs`, `node_probe.mjs`, `cpp_probe.cpp`, `compare.mjs`,
`run_differential.sh`, all under this directory): deterministic
adversarial-plus-random generator producing raw IEEE-754 bit patterns
(read verbatim by both the Node probe and the C++ probe -- no formula is
ever independently re-evaluated in both languages, the documented trap
that broke a prior harness), covering special values (±0, ±Inf, multiple
NaN payloads, subnormals, `Number.MIN_VALUE`/`MAX_VALUE`/`EPSILON`), dense
linspace sweeps, ULP-stepped clusters (radius 24) around every branch
threshold pulled directly from `fdlibm.cpp`'s own hex constants, 800
multiples of pi/2 (sin/cos/tan argument-reduction stress) with their own
ULP clusters, and random draws mixing raw 64-bit patterns with
value-uniform-in-range draws across ~600 orders of magnitude. 2-argument
functions (pow, atan2, hypot2) additionally seed the full cross-product of
special values as pairs; hypot3 seeds special-value-derived triples.

Run at N = 2,000,000 per function, on:
- **arm64**: native `node` (Homebrew) vs. this repo's `fdlibm.cpp` +
  `fdlibm_off.cpp` compiled natively arm64.
- **x86-64**: Node's official `darwin-x64` build (SHA256-verified, run
  under Rosetta) vs. the same two files cross-compiled
  `clang++ -arch x86_64` (still `-ffp-contract=fast` /
  `-ffp-contract=off` respectively per file) and run under Rosetta.

**Methodology correction made during integrator review**: every run in
this section is compiled with `-O3 -DNDEBUG -Wall -Wextra -Wpedantic
-Werror`, matching `CMakeLists.txt`'s actual `CMAKE_CXX_FLAGS_RELEASE`
byte-for-byte (confirmed via `cmake --system-information` and the literal
`flags.make` this project's own build generates). An earlier pass of this
harness built its probes at `-O2`, which is NOT what ships; that gap is
exactly what let `tan`'s residual go unnoticed until the integrator asked
for a from-scratch comparison against V8's own `-ffp-contract` behavior
per function (Section 6).

### Results (both architectures identical -- one table)

| function | N | exact | divergent | % divergent | max ULP |
|---|---|---|---|---|---|
| sin | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| cos | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| tan | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| asin | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| acos | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| atan | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| exp | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| expm1 | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| log | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| log2 | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| tanh | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| pow | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| atan2 | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| hypot (2-arg) | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| hypot (3-arg) | 2,000,000 | 2,000,000 | 0 | 0% | 0 |

**14 of 14 functions: 0 divergent, on both architectures, at 2,000,000
inputs each (28,000,000 total comparisons per architecture).**

## 6. tan: root-caused and fixed to 0/2,000,000

The integrator correctly rejected the earlier "304/2,000,000, documented
residual" as not good enough. Root cause, found by comparing byte-for-byte
against the vendored V8 source and by per-statement bisection against the
real (not simplified) `kernel_tan`/`tan`/`fd_log`:

1. **`kernel_tan` and `tan()` are byte-for-byte identical to
   `v8_ieee754_reference.cc`** (line-by-line diff performed; no
   transcription error, no missing branch, no `iy`-handling difference
   from sin/cos's dispatch). The `|x| < 2**-28` and `|x| >= 0x3FE59428`
   branches, and the `iy` odd/even dispatch, all match V8 exactly.
2. **Classifying all 304 pre-fix residual inputs** (script: none entered
   the `>= 0x3FE59428` large-angle branch; 10 never reached
   `__ieee754_rem_pio2` at all (`|x| <= pi/4`); the rest split ~evenly
   between `iy=1` and `iy=-1`). This proved the divergence was in the
   *shared* `r/v/s` polynomial combination both paths execute before
   branching, not in the reduction machinery or the reciprocal branch.
3. **The actual mechanism, found by direct A/B compiled-object
   comparison, not inference**: the two-line combination
   (`r = y + z*(s*(r+v)+y); r += T[0]*s;`), compiled *inline* inside
   `kernel_tan` exactly as fdlibm.cpp originally had it, produces
   DIFFERENT machine code under `-ffp-contract=fast` depending on
   `kernel_tan`'s surrounding code shape -- confirmed directly: wrapping
   the identical two lines in an unrelated `switch` statement (even with
   only the original case reachable) changed the compiled result from
   304/2,000,000 divergent to 0/2,000,000, proving the auto-fusion
   heuristic is sensitive to register pressure/scheduling context from
   the rest of the function, not to the two lines' own semantics.
4. **The fix**: factor those two lines into their own
   `__attribute__((noinline))` function, `kernel_tan_combine` (no explicit
   `std::fma`, no algorithm change -- byte-identical formula, just
   isolated). Isolating the expression removes the context-dependence:
   compiled standalone, with no competing live variables, clang's
   `-ffp-contract=fast` heuristic makes one fixed choice, and that choice
   reproduces V8 exactly. Verified against the REAL (not a copy)
   `src/fdlibm.cpp`, at both `-O2` and `-O3`, on both architectures: **0
   divergent out of 2,000,000 in every combination.**
5. **`tests/test_fdlibm_contract_pin.cpp`** pins both the small-bypass
   input (`0x3fdca1f6cacd184c`, never touches `rem_pio2`) and the
   large-reduction input (`0xc087d64e1c088d03`) that were divergent before
   this fix, so a future re-inlining (or a compiler upgrade that changes
   the isolated function's own codegen) fails loudly.

This same "noinline extraction, no explicit fma" technique also replaced
an earlier, INCORRECT fix to `log` -- see Section 3a.

## 6a. A second architecture-split bug, caught only by testing x86-64 at
the correct optimization level

The Section 3 fix for `log`'s residual (originally: explicit
`std::fma(s, hfsq + r, dk * ln2_lo)`) reached 0/2,000,000 on arm64 but,
re-measured at `-O3` on x86-64 (the methodology correction above), showed
**180/2,000,000 divergent, max 1 ULP**. Root cause: `std::fma()` fuses
UNCONDITIONALLY on every architecture (it is defined to always produce a
single, correctly-rounded fused result), but V8's own x86-64 binary does
NOT fuse this expression -- this project's x86-64 baseline has no
hardware fused-multiply-add for `-ffp-contract=fast` to select, so V8's
own `ieee754.cc` build stays unfused there, while arm64's NEON always has
hardware FMA and V8's arm64 binary fuses it. An unconditional
`std::fma()` therefore matched arm64-V8 but forced the WRONG (fused)
behavior on x86-64. Fixed the same way as `tan`: two
`__attribute__((noinline))` helpers (`log_combine_a`, `log_combine_b`),
plain unfused formula, no explicit `std::fma` anywhere -- letting ordinary
`-ffp-contract=fast` auto-fusion decide per architecture, matching V8's
own per-architecture build in both directions. Verified 0/2,000,000 on
arm64 AND x86-64 after the change. `tests/test_fdlibm_contract_pin.cpp`
pins the specific input (`0x40769487cdb54080`) that discriminates this
fix from the rejected explicit-fma version.

## 7. Call sites migrated

- `include/noisemaker/glsl_runtime.hpp`: added `tan`, `asin`, `acos`,
  `log`, `log2`, `exp2` (routes through `pow(2, x)`, matching the
  authority's own `glsl-runtime.js` `exp2: unary((value) => Math.pow(2,
  value))`); fixed `atan`/`atan2`/`pow` to call `noisemaker::fdlibm::*`
  instead of `std::*`. `sqrt`/`inversesqrt` unchanged (already exact).
- `src/effects/scatter/wormhole.cpp`: oklab lightness cube-root exponent,
  half-float decode's `pow(2, k)` scale factors, and the offset
  cos/sin -- all `std::` -> `noisemaker::fdlibm::`.
- `src/graph/executor.cpp`: the `DimensionKind::power` texture-size
  expression's `std::pow` -> `noisemaker::fdlibm::pow`.
- `tools/glslcpp/emit_typed_cpp.py` (the typed-C++ emitter): fixed the
  authorized-Mandelbrot/Newton-log special cases (were emitting
  `noisemaker::f32(std::log(...))` directly, bypassing the `glsl::`
  dispatch layer entirely) to emit `glsl::log`/`glsl::log2`; fixed the
  hardcoded sRGB-gamma helper template (`1.055 * std::pow(...) - 0.055`,
  emitted into two separate generated functions) and the julia/fractal
  block's `atan2`/`hypot` (2- and 3-arg)/`pow(10, ...)` templates.
- **`src/typed_generated/typed_slice.cpp` was hand-patched to the
  byte-identical text the fixed emitter would produce**, because
  `generate_typed_slice --write` currently fails closed on a **pre-existing,
  documented, out-of-scope** issue: `synth/remap:remap`'s
  `remap-std140-frontend-v1` profile is deliberately left permanently
  mismatched (`tools/glslcpp/frontend/remap_profile.py`'s own module
  docstring: "so `generate_typed_slice --check` fails, precisely and only,
  on this one program key... rather than being silently skipped"; fixing
  it needs edits to `generate_typed_slice.py`'s `_factory_route` and
  `generate_backend_compatibility.py`, both stated there as "outside this
  lane's permitted edits"). Verified pre-existing and unrelated to this
  pass by cloning the pristine, unmodified commit to a scratch directory
  and reproducing the identical failure. Every hand-patched line was
  verified against the (unmodified-by-this-patch) typed-program test
  suite (`typed_julia_*`, `typed_mandelbrot_*`, `typed_newton_*`,
  `typed_fractal_*` -- all pass, including their `adversarial`/
  `exact_parity` cases) and the full live corpus-parity run (Section 8).
  A future `--write`, once remap is unblocked, will regenerate
  byte-identical output for every line this pass touched.
- Added `tests/test_no_raw_transcendentals.py`: a grep gate over
  `src/`, `include/`, and the typed-C++ emitter for a bare
  `std::{sin,cos,tan,asin,acos,atan,atan2,exp,expm1,log,log2,pow,hypot,
  tanh}(` outside the math layer's own two files, so a future edit cannot
  reopen this hole one call site at a time.

## 8. Native / oracle / corpus results

- `noisemaker-cpu-tests` (Release build): 494 PASS, 3 FAIL -- all 3 are the
  pre-existing `synth/remap` pass-not-executable/compatible failures
  (Section 7), reproduced identically on a pristine clone of the
  unmodified commit; not caused by this pass. All 5 tests added by this
  pass PASS: `fdlibm_contract_pin_expm1_matches_v8_fma_contracted_result`,
  `fdlibm_contract_pin_tan_small_bypass_matches_v8`,
  `fdlibm_contract_pin_tan_large_reduction_matches_v8`,
  `fdlibm_contract_pin_log_matches_v8`, and
  `test_no_raw_transcendentals`'s two cases.
- `python -m tools.glslcpp.check_corpus --check`,
  `check_semantics --check`, `generate_kernels --check`: all clean (the
  `remap` ABI-mismatch diagnostic line is pre-existing and does not fail
  these three).
- `python3 -B -m unittest tests.test_dsl_corpus_parity -v`: **OK** -- all
  166 admitted corpus records, including `synth/julia`, `synth/mandelbrot`,
  `synth/newton`, `classicNoisedeck/fractal`, and `filter/wormhole` (every
  effect this pass's math changes touch), render byte-exact RGBA8 against
  the live JS authority. This is the strongest single confirmation: every
  effect in the entire admitted corpus, not just the five math-heavy ones,
  is unaffected or fixed, with zero regressions.
- `tests.test_julia_oracle` / `test_mandelbrot_oracle` / `test_newton_oracle`
  / `test_fractal_oracle` and the broader oracle family
  (`python -m unittest discover -s tests -p 'test_*oracle*.py'`, run with
  `NOISEMAKER_CPU_ROOT` set): 164 tests, 133 pass/skip, 31 failures + 1
  error, ALL of the form `CPU import closure mismatch` / `literal import
  graph drift` -- a pinned list of expected authority-JS-file
  paths+hashes each oracle generator self-checks against, drifted from
  what this specific `61aa869` authority checkout actually contains.
  **Confirmed pre-existing and unrelated to this pass**: reproduced the
  identical failure set (same count, same error text) by running the
  identical discovery command against a fresh `git clone` of the
  unmodified commit. Nothing in this pass touches any oracle generator or
  its pinned closure list.

## 9. Pixel-level parity sweep (before/after)

(An earlier, less rigorous pass at this section, using this pass's own
`pixel_sweep.py` on 5 hand-picked effects, briefly produced a false
"julia/newton diverge" result from a shell-scripting bug -- reused output
filenames across a loop's iterations -- that was caught and corrected
before being reported; it is superseded entirely by the integrator's
parity harness results below, which cover those same effects plus 107
more with byte-hash-level before/after proof, not a hand-rolled check.)

Superseded this pass's own earlier `pixel_sweep.py` (5 effects, corpus
defaults + a hand-varied size/time grid) with the integrator-provided
**parameter/geometry sweep harness**, copied into this lane at
`tools/parity/sweep.py` + `tools/parity/dump_catalog.mjs`. Unlike
`pixel_sweep.py`, it varies every declared parameter across its domain
(numeric min/max/interior, every enum, booleans, colors/vectors), not just
size and time, so it is a strictly stronger check.

Ran with `--variants 20 --seed 20260916 --no-chains`, on TWO driver
binaries -- "before" (`/tmp/v8math_pristine`, a fresh clone of this lane's
base commit, i.e. before ANY change in this task) and "after" (this lane's
current `build-lane`, with every fix above) -- against the same JS
authority, same seed, same catalog:

**Named 13 effects** (`filter/clouds`, `filter/scanlineError`,
`filter/texture`, `mixer/patternMix`, `synth/cell`, `synth/curl`,
`synth/gabor`, `synth/modPattern`, `synth/perlin`, `synth/mandala`,
`synth/pattern`, `synth/gradient`, `classicNoisedeck/splat`), 260 cases
(20 variants x 13 effects):

| | before | after |
|---|---|---|
| byte_exact | 172 | 172 |
| cpp_refused_only | 66 | 66 |
| divergent | 22 | 22 |

**All 22 divergent cases produce byte-identical output in "before" and
"after"** (compared by `actualSha256` per case, not just the divergent
count -- every one of the 22 case ids matches exactly, same hash, same
first-mismatch offset/channel/expected/actual, same mismatch count). Zero
cases moved between classifications in either direction: nothing this
pass's fixes broke, nothing this pass's fixes happened to repair either.

**Root-caused to the exact pixel and the exact call path, not just
diffed**, for the simplest of the 22 (`filter__clouds__v16`, 17x11,
reproduced standalone with the exact DSL
`solid(color:#3a7).clouds(seed:1,scale:0.1,speed:0)`, divergent at
output pixel (6,2): expected R=241, actual R=240). Instrumented the
actual `pixel()` function (temporarily, reverted after -- `git diff` was
empty before continuing) to print every value feeding `cloudNoise`/
`simplex2d` at that exact pixel (`context.frag_coord = (6.5, 8.5)` in this
kernel's bottom-up convention). Two independent, direct findings, not
inference:
1. **`animPhase = 0` and `animSpeed = 0`** for this DSL (`speed: 0`), so
   `cloudNoise`'s `timeOffset` term is
   `(cos(animPhase+octavePhase) - cos(octavePhase)) * octaveRadius*animSpeed`
   -- with `animPhase = 0`, `cos(0 + octavePhase)` and `cos(octavePhase)`
   are the SAME argument bit-for-bit, so the subtraction is exactly 0
   *symbolically*, before any rounding question even arises, and the
   whole term is additionally multiplied by `animSpeed = 0`. **`cos` and
   `sin` cannot be the cause at this pixel by construction, independent
   of any measurement.**
2. The only other transcendental on the path is `pow(2, i)` for small
   integer `i` (0-6, the octave loop) inside `freq`/`amp` -- proven exact
   against V8 at 2,000,000 inputs including small-integer exponents
   (Section 5).

That leaves only non-transcendental arithmetic (`floor`, `fract`, `abs`,
`dot`, `mix`, plain multiply/add/divide) in `simplex2d`'s permutation
noise as the possible cause -- consistent with the 1-bit-per-channel
pattern (`maxDelta` 1 in 8 of the 11 named-effect cases with a
diagnostic; two `filter/scanlineError` cases reach `maxDelta` 3 and 222,
still byte-identical before/after) pointing at a float32-narrowing-order
or similar arithmetic-sequencing difference elsewhere in the typed
emitter's generated code (the JS authority narrows to float32 on every
`PooledFloat32Array` store; the C++ emitter's narrowing points in a
multi-term sum may not land in the same places), independent of which
transcendental implementation is called underneath. Combined with the
before/after byte-identity above (proving this pass changed nothing about
it), **this is a real, pre-existing, non-math bug, out of scope for "the
fdlibm/pow/hypot hole" this pass owns, and is reported here
rather than fixed or hidden.**

**Broader effect coverage** (every other effect whose generated kernel
calls a transcendental, grepped from `typed_slice.cpp`: 94 additional
effect ids, 1,880 cases, `--variants 20`, same seed), run on BOTH driver
binaries:

| | before | after |
|---|---|---|
| byte_exact | 1,195 | 1,195 |
| cpp_refused_only | 665 | 665 |
| both_refused | 20 | 20 |
| divergent | 0 | 0 |

Identical classification counts, **0 divergent in both.** (One case
transiently reported `harness_error` in the "after" run because this
run's driver binary was mid-relink from a concurrent rebuild in this same
pass; re-ran it standalone once the binary was stable and it is
`byte_exact`, folded into the 1,195 above.)

Combined with the named-13 sweep above and the pure per-function
differential harness (Section 5), this pass's fixes are verified with
**zero regressions and zero unintended changes** across 107 effects,
4,280 rendered variants (2,140 x 2 builds), and 28,000,000 direct
function-level comparisons on two architectures.

## 10. Files changed

- `include/noisemaker/fdlibm.hpp`, `src/fdlibm.cpp`: extended with tan,
  asin, acos, atan, atan2, pow (V8's live wrapper), hypot (2/3-arg, fixed);
  `hypot`/`log2`/`k_log1p`/`fd_log2` moved out.
- `src/fdlibm_off.cpp` (new): log2 + k_log1p + hypot (2/3/N-arg), compiled
  without the fast override.
- `CMakeLists.txt`: added `src/fdlibm_off.cpp` to the library and
  `tests/test_fdlibm_contract_pin.cpp` to the test binary; added the
  per-source `-ffp-contract=fast` override for `src/fdlibm.cpp` with a
  detailed rationale comment.
- `include/noisemaker/glsl_runtime.hpp`, `src/effects/scatter/wormhole.cpp`,
  `src/graph/executor.cpp`: call-site migration (Section 7).
- `tools/glslcpp/emit_typed_cpp.py`, `src/typed_generated/typed_slice.cpp`:
  emitter fix + hand-patch (Section 7).
- `tests/test_fdlibm_contract_pin.cpp`, `tests/test_no_raw_transcendentals.py`
  (new).
- `docs/port-engineering/v8-math/`: this report, the differential harness
  (`gen_inputs.mjs`, `node_probe.mjs`, `cpp_probe.cpp`, `compare.mjs`,
  `run_differential.sh`), and `pixel_sweep.py`.
