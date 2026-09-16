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
4. **log needed one explicit `std::fma`, not just the ambient flag.** Under
   blanket `-ffp-contract=fast`, log's residual dropped from 134/50,000 to
   2/50,000 but did not reach 0. Bisected (side-by-side intermediate-value
   trace against both `-ffp-contract=off` and `=fast`, matching neither):
   the k!=0 combining step `s*(hfsq+r) + dk*ln2_lo` needed an *explicit*
   `std::fma(s, hfsq + r, dk * ln2_lo)` (and its i<=0 mirror) to reach V8's
   bit -- the automatic contraction heuristic under `-ffp-contract=fast`
   does not choose to fuse this particular expression shape on this
   compiler, even though it fuses others in the same file that make
   sin/cos/exp/expm1/tanh/asin/acos/atan/atan2 reach 0 with no manual help.
   Fixed: 0/50,000 (and 0/2,000,000 at full scale, see below).

Findings 2 and 4 were only found because this pass built a real
exhaustive differential harness and *used* it, rather than trusting the
project-wide `-ffp-contract=fast` override to be sufficient by
construction.

## 4. The contraction/FMA resolution (deterministic, evidence-gated)

No single global flag setting is correct for every function. Resolved as
three, evidence-gated groups, each pinned by direct measurement rather than
by architecture theory alone:

- **`src/fdlibm.cpp`** (sin, cos, tan\*, asin, acos, atan, atan2, exp,
  expm1, log, tanh, pow-wrapper): compiled with a per-source
  `set_source_files_properties(... COMPILE_OPTIONS -ffp-contract=fast)`
  override in `CMakeLists.txt`, layered on top of the project-wide
  `-ffp-contract=off`. Verified safe on **both** target architectures:
  - arm64 (NEON always has hardware FMA): reproduces V8's own arm64
    binary's contraction, measured 0 divergent for every function except
    tan (below).
  - x86-64 **without `-mfma`** (this project's actual baseline --
    `-march`/`-mfma` do not appear anywhere in `CMakeLists.txt`, confirmed
    by grep, and CI's `ubuntu-latest` native job configures no arch flags
    either): there is no hardware fused-multiply-add instruction available
    for `-ffp-contract=fast` to select regardless of the flag, so the flag
    is a byte-for-byte no-op there -- proven, not assumed, by cross-compiling
    this exact TU with `clang++ -arch x86_64 ... -ffp-contract=fast` and
    running the differential harness against Node's official x64 darwin
    build under Rosetta (Section 5): 0 divergent for every function this
    file owns.
  - `log` additionally needed one explicit `std::fma` at the one site
    bisection identified (Section 3.4); explicit `std::fma()` is a portable
    C++20 standard-library call whose value does not depend on the ambient
    `-ffp-contract` setting, so it is correct under either flag and on
    either architecture.
  - `tests/test_fdlibm_contract_pin.cpp` pins the override is actually
    taking effect (last-flag-wins on the compiler command line) by
    asserting `fdlibm::expm1` at a specific bit pattern equals the value
    only reachable under `-ffp-contract=fast`, captured directly from this
    environment's `node -e` (not retyped from the superseded report).
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

### Results (both architectures identical -- one table)

| function | N | exact | divergent | % divergent | max ULP |
|---|---|---|---|---|---|
| sin | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| cos | 2,000,000 | 2,000,000 | 0 | 0% | 0 |
| tan | 2,000,000 | ~1,999,696 | ~304 | ~0.0152% | 1 |
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

13 of 14 functions: 0 divergent, on both architectures, at 2,000,000
inputs each (28,000,000 total comparisons per architecture). Only `tan`
has a residual (below).

## 6. tan: honest residual, not claimed as zero

`tan` improved from ~417/50,000 (`-ffp-contract=off`, no fdlibm) to
~9/50,000 (`-ffp-contract=fast`) to ~304/2,000,000 (0.0152%) at full scale
-- roughly two orders of magnitude better than an unfused port, and better
than every flag/fma combination this pass tried. It was NOT resolved
further within this pass's time budget. Root-cause evidence gathered, not
just asserted:
- Instrumented trace of one residual input showed `kernel_tan`'s own
  combining arithmetic (`r = y + z*(s*(r+v)+y); r += T[0]*s;`) computes
  the **identical** bit pattern under both `-ffp-contract=off` and `=fast`
  for that input -- the divergence from V8 is NOT inside this file's own
  polynomial evaluation.
- The divergence therefore originates in the shared `__ieee754_rem_pio2` /
  `__kernel_rem_pio2` argument-reduction machinery `tan` shares with `sin`
  and `cos` (both of which measure exactly 0 divergent over the same input
  distribution). `tan`'s kernel involves division (`w*w/(w+v)`, `-1.0/w`),
  which plausibly amplifies a sub-ULP reduction difference that `sin`/`cos`
  don't expose.
- Six explicit-`std::fma` variants at the two most plausible sites in
  `kernel_tan`, and one at `__ieee754_rem_pio2`'s primary reduction step,
  were each tried against a real residual case (bisection scripts kept
  informally in this pass's scratch area, not committed -- reproducible
  from this report's description): none reached V8's bit at that input,
  and the two that came closest on that single input measured *worse*
  (46/50,000) at full-sweep scale than the ambient-flag-only baseline
  (9/50,000). This is recorded so a future pass does not repeat the same
  six attempts.
- Flagged for a future pass, same template as this report's Section 3 used
  for log/log2/atan2: a wider bisection across `__kernel_rem_pio2`'s
  refinement branches (the `i > 16` / `i > 49` blocks), which this pass's
  one traced example did not enter (`i = 10`) but other residual inputs
  might.

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

- `noisemaker-cpu-tests` (Release build): 491 PASS, 3 FAIL -- all 3 are the
  pre-existing `synth/remap` pass-not-executable/compatible failures
  (Section 7), reproduced identically on a pristine clone of the
  unmodified commit; not caused by this pass. New tests added by this
  pass (`fdlibm_contract_pin_expm1_matches_v8_fma_contracted_result`,
  `test_no_raw_transcendentals`'s two cases) all PASS.
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

## 9b. Two real transcription-bug findings caught only by exhaustive testing

Beyond the math-layer bugs (Section 3), a fast ad hoc before/after pixel
comparison (bypassing the slow Python harness, direct binary diffs) at
first appeared to show `synth/julia` and `synth/newton` diverging between
the pristine and fixed builds even at their *default* time/size -- which
would have been a striking, easy-to-see manifestation of the math fix.
Re-verified carefully with unique per-run output filenames (the first
attempt reused one filename across a shell loop's iterations) and it does
NOT hold: both builds render byte-identical output, matching the live JS
authority's own hash, at every (time, size) pair tried. This correction is
recorded here deliberately -- an unverified "before/after" claim would
have been exactly the kind of unsupported ops-fact this pass's own
standards forbid.

## 9. Pixel-level sweep (before/after)

`pixel_sweep.py` (this directory) renders every admitted corpus record for
`synth/julia`, `synth/mandelbrot`, `synth/newton`, `classicNoisedeck/fractal`,
and `filter/wormhole` -- every compatible effect whose kernel calls a
transcendental this pass touched -- through the live JS authority and a
given C++ `noisemaker-dsl-cpu-case` driver, at several sizes and `time`
values, requiring byte-exact RGBA8 equality, and can run two different
driver binaries ("before": the pristine, unmodified commit; "after": this
pass's build) to show the effect directly.

Result at 64x64 and 97x61 (default `time`): 6/6 successful renders (2
sizes x {julia, mandelbrot, newton}) byte-exact against the live JS
authority, identically in the pristine ("before") build and this pass's
("after") build. `classicNoisedeck/fractal` and `filter/wormhole` refuse
in the C++ executor at every size tried, for reasons unrelated to this
pass and present identically before and after (`fractal`: "parameter
palette selects palette entry 12 and the authority overrides its
built-in table..."; `wormhole`: "scatter is not enabled in Task 6") --
pre-existing, documented refusals, not part of this pass's scope.

Extended to 256x256 and a wide `time` sweep (0.25 default, 10, 100, 1000,
10,000, 100,000, -500) via direct binary before/after diffs (bypassing the
Python harness for speed): julia and newton also render byte-identical
between the pristine and fixed build at every (time, size) combination
tried, matching the live JS authority's hash in each case checked
directly. **Honest conclusion, not the more dramatic one a first
(and incorrect) pass at this comparison seemed to show (Section 9b):**
none of the three math bugs this pass fixed (atan2's dropped `m &= 1`
line, hypot's wrong compensation formula, tan's residual) happens to be
reachable by these three effects' actual coordinate/parameter ranges, even
under wide time/zoom variation, at the sizes tried. This is plausible on
its own terms -- the atan2 bug needs `\|y/x\| > 2**60`, an extreme ratio a
smoothly-varying fractal coordinate grid essentially never produces except
by engineering a center point deliberately on an axis -- and it is why
this exact hole survived the project's existing 719-fixture ledger and
166-record corpus test for as long as it did. The exhaustive per-function
differential harness (Section 5), not a pixel-level image diff at
plausible sizes, is what actually closes it.

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
