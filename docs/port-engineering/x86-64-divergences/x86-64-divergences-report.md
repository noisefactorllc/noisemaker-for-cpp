# x86_64-only native test divergences — root-cause report (Lane G)

Investigation of the two PRE-EXISTING x86_64-only failures surfaced by the
cellRefract186 gate matrix. Both reproduce at commit `8edff08` (HEAD of the
185-row stop line) **without** the uncommitted cellRefract slice, so they are
not caused by it and must not be repaired inside it. The repo was not
modified by this investigation; all instrumented work lives under
`$RUN_ROOT/workers/G` (see §7).

**Verdict in one line:** both failures are the same mechanism — the hardware
NaN produced by raw double `0.0/0.0` (SSE2 `divsd` "QNaN indefinite"
`0xFFF8000000000000` on x86_64 vs ARM64 `fdiv` default NaN
`0x7FF8000000000000`), narrowed sign-preservingly to float32
(`0xffc00000` vs `0x7fc00000`) — and the **JavaScript authority itself
produces the same arch-dependent bits** (measured with the identical
node v24.7.0 / V8 `13.6.233.10-node.26` on both architectures), so each
failure is **classification (iii): an inherent cross-arch materialization
question, not a fixture transcription error and not a port bug**. The C++
port is byte-identical to same-architecture JS at every measurement point
of these two fixtures.

## 1. Reproduction

Binaries used (already-built x86_64 Release trees from the gate matrix, run
under Rosetta 2 on this Apple-Silicon Mac; `divsd`/`cvtsd2ss` NaN semantics
are architectural per the Intel SDM, so genuine Intel hardware behaves
identically):

| Binary | Result |
| --- | --- |
| `$RUN_ROOT/verification/head-x86/build/noisemaker-cpu-tests` (HEAD, no slice) | 254 PASS, **2 FAIL** (the two under investigation) |
| `$RUN_ROOT/verification/x86_64/noisemaker-cpu-tests` (HEAD + cellRefract slice) | 260 PASS, **2 FAIL** (same two; failing REQUIRE moves `test_generated_kernels.cpp:10973` → `:10986` from the added rows, `test_typed_slice.cpp:2663` unchanged) |

Failure output (identical text on both binaries modulo the line shift):

```
FAIL typed_task35_bitwise_scalar_int_ops_oracle_cases_are_bit_exact:
  tests/test_generated_kernels.cpp:10973 (HEAD) / :10986 (with slice):
  requirement failed: task23_hex(task23_sha256(float_bytes)) == fixture.f32_sha256
FAIL typed_task16_compute_rank_width_one_preserves_canonical_quiet_nan:
  tests/test_typed_slice.cpp:2663:
  requirement failed: hex(sha256(little_endian_float_bytes(first))) ==
  "24f56616adaf6242697f97e5d9420c4bafa1529c99e8e053b9dc0cb6bc87341c"
```

A scratch harness (`$RUN_ROOT/workers/G/harness.cpp`, linked against
pristine-HEAD `libnoisemaker-cpu.a` built fresh for each arch from
`git archive 8edff08`) rendered both fixtures on both architectures and
dumped every float word. Results:

**Failure 1 — task16 width-one** (`filter/pixelSort:computeRank`, 1x1
flat lumTex `[0.5, 0.25, 0.75, 1.0]`):

| | lane R | lane G | lane B | lane A | f32 sha256 | rgba8 sha256 |
| --- | --- | --- | --- | --- | --- | --- |
| pinned fixture | `00000000` | `3f000000` | **`7fc00000`** | `3f800000` | `24f56616adaf…bc87341c` | `1f71b62d981b…1b67b135e` |
| C++ arm64 (actual) | `00000000` | `3f000000` | `7fc00000` | `3f800000` | `24f56616adaf…bc87341c` (**matches pin**) | `1f71b62d…` (matches) |
| C++ x86_64 (actual) | `00000000` | `3f000000` | **`ffc00000`** | `3f800000` | **`79d1c1af5c1c16157179b44c4a5c04320924e03c6748cbb0eeb40ae4cb8a5582`** | `1f71b62d…` (**matches pin**) |

Only lane B differs, and only in the NaN sign bit. The rgba8 hash still
matches on x86_64 because `to_rgba8()` maps any NaN to 0 regardless of
sign. (The test's later `REQUIRE(bits == 0x7fc00000)` at
`test_typed_slice.cpp:2669` would also fail on x86_64, but the f32-hash
REQUIRE at `:2663` aborts the test first.)

**Failure 2 — task35 bitwise oracle** (`synth/bitwise:bitwise`): per-case
hashes computed from the harness dumps show **exactly one** of the six
cases diverges on x86_64:

| case (of 6) | x86_64 f32 | x86_64 rgba8 |
| --- | --- | --- |
| xor-mono-seed-negative-one-signbit-mask | OK | OK |
| and-rgb-int32min-offsets-near-max-mask | OK | OK |
| or-hsv-negative-offsets-large-seed | OK | OK |
| nand-mono-int32-extremes-tiled | OK | OK |
| xnor-rgb-high-bit-mixed-signs | OK | OK |
| **mask-zero-divide-by-zero-diagnostic** | **MISMATCH** | OK |

Diagnostic case detail: 3x3 image, 36 float lanes; **27 lanes** (the
`v,v,v` channels of all 9 pixels) are `0xffc00000` on x86_64 vs
`0x7fc00000` on arm64 (the 9 alpha lanes `3f800000` are identical).
x86_64 actual f32 sha256
`72f71c0a368a60c12d9d7cfa112e460e6dccf009df5ecd1754bc43ed86bb6803` vs
pinned `720415a4af3de87c558c06dbc5c970ee576379eb01d0e3af743c30b35a93986c`;
arm64 reproduces the pin exactly; rgba8 pin `d574fbbb…` matches on both
arches (NaN→0 sign-agnostic).

## 2. Root cause — failure 1 (task16 computeRank width-one)

Code path (all line numbers given as HEAD `8edff08`; the with-slice working
tree adds ~476 lines to `typed_slice.cpp`, cited in parentheses where
checked):

- GLSL source `sources/filter/pixelSort/computeRank.glsl:43`:
  `fragColor = vec4(estimatedRank, myLum, float(x) / float(width - 1), 1.0);`
  With the test's 1x1 output (x=0, width=1) the blue lane is `0.0/0.0`.
- Emitted C++ `src/typed_generated/typed_slice.cpp:11738` (with-slice
  `:12214`), namespace `typed_83`:
  `(static_cast<double>(float(x)) / static_cast<double>(float((width - std::int32_t(1)))))`
  — a raw IEEE double division evaluated by the CPU, then narrowed to
  float32 by `glsl::FloatExpr<4>` at the Surface store.
- Test `tests/test_typed_slice.cpp:2663` pins the whole-buffer f32 sha256;
  `:2669` pins lane B == `0x7fc00000`.

Mechanism (measured, `$RUN_ROOT/workers/G` raw probe, identical values from
the harness): on x86_64, `0.0/0.0` in double yields the SSE2
"QNaN floating-point indefinite" `0xFFF8000000000000` — sign bit SET
(Intel SDM: masked `#IA` on `divsd` returns the indefinite QNaN). On arm64,
`fdiv` yields the default NaN `0x7FF8000000000000` — sign bit CLEAR. The
subsequent double→float narrowing (`cvtsd2ss` / `scvtf`) preserves the NaN
sign and quiet bit: `0xffc00000` vs `0x7fc00000`. The port's numeric layer
is bit-preserving by design (`tests/test_numeric.cpp:92-101`,
`numeric_round_trips_the_shapes183_controlled_nan_payload_and_scalar_xor`),
so the manufactured payload survives storage unchanged on both arches —
the divergence is created by the division itself, not by any store,
uninitialized lane, or x87 behavior (x86_64 builds use SSE2; no x87
extended-precision involvement).

Fixture provenance: `docs/port-engineering/task-16-oracles.json`
(generator `task-16-oracle-generator.mjs`, provenance node **v24.7.0**),
produced by running the CPU repo's canonical JS kernel
(`noisemaker-for-cpu/src/effects/generated/canonical-kernels.js`,
`canonicalFactory104` at line 17040; the JS computes the same
`(x) / (cpu_float(width - 1))` at line 17076 and stores into a
Float32Array). I.e. the pin encodes the **arm64-JS** materialization — see
§4 for the measurement that proves this and its consequence.

Hypothesis check (per task brief): (a) libm — inapplicable, no libm call on
this path (plain division); (b) NaN payload canonicalization — **confirmed,
this is the cause**, and the NaN is manufactured by arithmetic (`0.0/0.0`),
not a literal passthrough; (c) x87/SSE — SSE2 semantics, not a bug;
(d) uninitialized/high-bit lanes — ruled out: lane R/G/A and all 9x7
finite-lane cases are bit-identical across arch, and the diverging bits are
exactly the canonical-vs-indefinite NaN encoding.

## 3. Root cause — failure 2 (task35 synth/bitwise diagnostic case)

Code path:

- GLSL `sources/synth/bitwise/bitwise.glsl:44` (in `bitOp`):
  `r = r & m;  return float(r) / float(m);` — with `mask == 0` every
  operator branch collapses `r` to 0, so the return is `float(0)/float(0)`.
- Emitted C++ `src/typed_generated/typed_slice.cpp:19582` (with-slice
  `:20058`), namespace `typed_170`:
  `return (static_cast<double>(static_cast<double>(r)) / static_cast<double>(static_cast<double>(m)));`
- The JS canonical reference (`canonicalFactory244`, `canonical-kernels.js`
  line 28957) returns `(r) / (m)` — plain JS number division — at line
  29018, stored into the Float32Array fragColor.
- Test `tests/test_generated_kernels.cpp`: fixture row at `:10938`
  (`mask-zero-divide-by-zero-diagnostic`, `mask=0`, colorMode 0), failing
  REQUIRE at `:10973` (HEAD) / `:10986` (with slice). The test's own
  comment block (`:10897-10905`) documents the case as the deliberate
  NaN-propagation diagnostic.

Mechanism: identical to §2 — the colorMode-0 output spreads `v` to RGB, so
27/36 lanes carry the hardware `0.0/0.0` NaN (`0xffc00000` on x86_64).
The five non-diagnostic cases exercise the same int bitwise machinery
(`glsl::detail::js_bitwise_*`) with finite results and are bit-identical
across arch (measured 0/120, 0/120, 0/112, 0/112, 0/144 lane diffs),
which is why this test's premise (ToInt32 ops are arch-independent) holds
everywhere except the manufactured-NaN diagnostic.

Fixture provenance: `tests/oracles/task-35-oracles.json` — byte-identical
vendored copy of
`docs/port-engineering/future-precompute/cheap-unlocks/bitwise-oracles.json`
(generator `bitwise_oracle_generator.mjs`), also node-v24.7.0-derived, i.e.
arm64-JS materialization for the diagnostic case.

Hypothesis check: (a) libm — inapplicable for the diverging case (sin/cos
are fdlibm-vendored anyway and the diagnostic uses `rotation=0`); (b)
NaN payload — **confirmed**; (c)/(d) — ruled out as in §2 (finite cases
match exactly).

## 4. The JS-authority question — measured, not assumed

**Q: does the JS engine's own output differ across arch for these values?**
A: **yes.** Both oracle generators were re-run under node v24.7.0 twice on
this machine — natively (arm64) and under Rosetta 2 with the official
`node-v24.7.0-darwin-x64` build (same V8 `13.6.233.10-node.26` on both;
architecture is the only variable). Scratch inputs/outputs in
`$RUN_ROOT/workers/G/t16-{arm64,x64}.json` and `t35-{arm64,x64}.json`.

**task16 generator** (`docs/port-engineering/task-16-oracle-generator.mjs`,
unmodified, imports resolved against a scratch mirror of the CPU repo):

- arm64 node reproduces **all three** pinned case hashes exactly, including
  width-one `24f56616…` (the only JSON diff vs the frozen
  `task-16-oracles.json` is the whole-file `canonical_kernels_sha256`
  provenance field: new factories have been appended to
  `canonical-kernels.js` since the freeze; the program-level
  `factory_to_string_sha256` is still exactly the pinned
  `77391180a834b322967664440caeba3dbf51f2b1ae024e5ab8a3cc781c151acf` on
  both arches — the kernel code itself is unchanged).
- x86_64 node produces width-one
  `f32_sha256 = 79d1c1af5c1c16157179b44c4a5c04320924e03c6748cbb0eeb40ae4cb8a5582`
  with probe bits `["0x00000000","0x3f000000","0xffc00000","0x3f800000"]`
  — **byte-identical to the C++ port's x86_64 output** measured in §1. The
  two finite cases (`formula`, `flat-tie`) and all rgba8 hashes are
  arch-independent.

**task35 generator** (`bitwise_oracle_generator.mjs`; in the scratch copy
only its whole-file `canonical-kernels.js` drift pin was updated to the
current file hash — six other runtime pins still enforced and pass, and
`canonical_factory_to_string_sha256` recomputes to the pinned
`a00438c5b07fb3e4cfe58a511453f8856f70cb9449465c9bd8d2f35a3afdd3e2` on
both arches, so the frozen JS reference for this program is unchanged):

- arm64 node reproduces all six pinned case hashes exactly.
- x86_64 node reproduces five; the diagnostic's f32 is
  `72f71c0a368a60c12d9d7cfa112e460e6dccf009df5ecd1754bc43ed86bb6803` —
  again **exactly the C++ port's x86_64 value**. rgba8 identical.

**Why V8 differs by arch** (micro-probe `$RUN_ROOT/workers/G/nanprobe.mjs`):
V8 evaluates runtime-variable double division on the host FPU. On x86_64
that is `divsd` → indefinite QNaN `0xfff8000000000000`; storing into a
`Float32Array` converts via `cvtsd2ss`, preserving the sign → `0xffc00000`.
On arm64, `fdiv` → `0x7ff8…` → `0x7fc00000`. V8 *does* canonicalize to the
positive quiet NaN in some paths (compile-time-constant `0/0`, the
`Float32Array([...])` constructor when the element is a constant-folded
NaN, `Math.fround(NaN)`), but **not** in the runtime-arithmetic paths these
kernels use (probe lines `vars 0/0`, `bitOp (r)/(m)`,
`computeRank x/(w-1)` all show `0xfff8…/0xffc00000` on x86_64 node). This
matches ECMAScript, which deliberately leaves NaN byte sequences in typed
array stores implementation-defined (a canonicalization recommendation,
not a requirement) — the "authority" is only byte-stable per-platform.

**Class breadth** (scratch probe `nanclass.cpp`, both arches): the same
x86_64-negative / arm64-positive split applies to every masked
invalid-arithmetic double result — `0.0/0.0`, `inf-inf`, `0.0*inf`,
`inf/inf` all give `0xfff8000000000000` vs `0x7ff8000000000000` (f32
`0xffc00000` vs `0x7fc00000`). Conversely, NaN paths that pass through the
vendored fdlibm sin/cos or through controlled `uint_bits_to_float` payloads
are arch-stable — e.g. `typed_task20_star_points_five_through_twelve_are_canonical_qnan`
(`tests/test_typed_slice.cpp:3164`, expects `0x7fc00000`) **passes on
x86_64** — and rgba8 conversion is NaN-sign-agnostic. So the divergence
class is precisely: *a hardware-manufactured double NaN flowing unmodified
through narrowing into a pinned f32 byte fixture*.

## 5. Classification (task brief's i/ii/iii)

| failure | classification | evidence |
| --- | --- | --- |
| task16 width-one f32 hash | **(iii) inherent cross-arch materialization question** | Same JS kernel code (factory hash `77391180…` identical pinned/arm64/x64) produces `24f56616…` under arm64 node and `79d1c1af…` under x86_64 node; the C++ port equals the same-arch JS on both arches (§1 vs §4, byte-for-byte). The pin is a faithful arm64-JS capture, not a transcription error (arm64 node regenerates it exactly); the port is not producing "wrong bits for the JS on any platform" — it produces each platform's JS bits. The test premise ("the canonical quiet NaN" is `0x7fc00000`, `tests/test_typed_slice.cpp:2669`, brief `task-16-brief.md:135-136` wording "exact canonical NaN payload") is true on arm64 but not on x86_64, where the canonical JS materialization of `0.0/0.0` is `0xffc00000`. |
| task35 diagnostic f32 hash | **(iii), same mechanism** | Same proof shape with factory hash `a00438c5…`; arm64 node reproduces pin `720415a4…`, x86_64 node produces `72f71c0a…` = the port's x86_64 value. The five finite cases (the actual bitwise-semantics coverage of this oracle) are arch-independent and pass on x86_64. |

Not (i): a fixture-provenance *error* would mean the JS authority is
arch-independent and the pin captured the wrong bytes; refuted because the
authority itself is byte-divergent per arch. Not (ii): a port bug would
mean C++ ≠ JS on some platform; refuted by the byte-identical C++-vs-node
comparison on each arch. It genuinely is (iii): **the oracle for
NaN-manufacturing expressions is arch-dependent, so a single pinned hash
cannot encode "the JS truth" for both architectures.**

## 6. Recommendation

Cheapest correct repair per the project's rules (exact parity, no
tolerance, fixtures derive from the JS authority, never weaken a frozen
check):

1. **Dual-pin the two NaN-materializing fixtures per architecture** — the
   recommended fix. In each affected test (and in the upstream oracle JSONs,
   which keep a recorded provenance), carry both JS-derived hashes and
   select by architecture macro at compile time, e.g. pin the f32 hash and
   the lane-B word to `0x7fc00000`/`24f56616…`/`720415a4…` on arm64 and to
   `0xffc00000`/`79d1c1af…`/`72f71c0a…` on `__x86_64__` (both sets already
   re-derivable by running the existing generators under the two node
   builds; the x86_64 values are measured in this report and were produced
   by the unmodified generators). This *strengthens* the checks (more
   exact bytes pinned, still zero tolerance) and keeps the fixtures
   derived from the JS authority on each arch. The generators should also
   record `process.arch` in provenance so future freezes are unambiguous.
2. **Do not canonicalize hardware NaNs in the port** (e.g. forcing
   `0x7fc00000` at the FloatExpr narrowing): it would make the port
   arch-independent but byte-**diverge from actual x86_64 JS** for these
   lanes (measured), violating the authority rule. Reject unless the
   project explicitly re-scopes the authority to "arm64 JS output".
3. **Not in the current slice.** Both failures pre-date the cellRefract186
   slice (reproduced at clean `8edff08`, 254/256, with the slice 260/262 —
   identical two). Fixing them inside the slice would couple an unrelated
   policy change to a row-parity task; the repair belongs in a small
   dedicated follow-up that touches only the two tests + the two oracle
   JSONs (and the generator provenance field).
4. **Risk of inaction:** x86_64 consumers can never gate green (2 red
   checks in every full run), masking real regressions behind known noise
   and making the "exact parity" claim formally unverifiable on that arch;
   and every future fixture that pins f32 bytes of a hardware-manufactured
   NaN (any `0/0`, `inf−inf`, `0*inf`, `inf/inf` lane reaching a Surface)
   will re-trip the same ambiguity — cheap to prevent now by recording the
   arch axis in the oracle schema when dual-pinning these two.

## 7. Evidence artifacts (scratch, not the repo)

- `harness.cpp`, `harness-x86{,.out}`, `harness-arm{,.out}` — per-word dumps
  and hashes of both fixtures on both arches (pristine-HEAD libs built at
  `repo-head/build-x86`, `repo-head/build-arm`).
- `compare.py` — pinned-vs-actual comparison incl. per-case task35 table
  and lane-level diffs (reads pins from the test sources directly).
- `nanprobe.mjs` — V8 NaN-materialization probe (arm64 node vs x86_64 node).
- `nanclass.cpp`, `nanclass-{x86,arm}` — invalid-arithmetic NaN class probe.
- `jsrun/` — mirror of `noisemaker-for-cpu` + corpus + the two generators
  used for the dual-arch oracle reruns; outputs `t16-{arm64,x64}.json`,
  `t35-{arm64,x64}.json`; `factoryhash.mjs` (factory-text identity check);
  `node-x64/` (official darwin-x64 node v24.7.0).
- Full-suite logs: `head-x86-full.{out,err}`, `slice-x86-full.{out,err}`.

Repro commands (essentials): build each arch via
`cmake -DCMAKE_OSX_ARCHITECTURES=<arch> -DCMAKE_BUILD_TYPE=Release`, link
the harness against `libnoisemaker-cpu.a`, run; oracle reruns via
`node <generator>` and
`arch-native-vs-$(…)/node-v24.7.0-darwin-x64/bin/node <generator>` from the
`jsrun` layout described above.
