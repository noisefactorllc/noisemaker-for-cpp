# `filter/wormhole:deposit` — bit-exact C++ port, oracle, and integration plan

## What this is

`filter/wormhole:deposit` is a vertex-stage scatter pass (`drawMode: "points"`). Its `.frag`
source (`sources/filter/wormhole/deposit.frag`, corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`) is a two-line passthrough (`fragColor = vColor`) —
it **is** transpiled (`canonicalFactory181` in `canonical-kernels.js`; `glsl-coverage.js` marks
it `status: "generated"`) but the CPU reference **never executes that kernel**. `renderer.js`
branches on `pass.drawMode === 'points' || 'billboards'` and dispatches to a hand-written scatter
adapter registered in `src/effects/cpu/scatter-registry.js`, which forwards to
`runWormholeDeposit` (`src/effects/cpu/wormhole.js:34-76`) — the real ground truth for this port.
This was verified, not re-derived from the task brief: the source files, line ranges, corpus
paths, and JSON param table (`kink` 0–5, `stride` 0–2, `rotation` −180–180, `wrap`
mirror=0/repeat=1/clamp=2) were all read directly from the two repos.

Everything below lives under `docs/port-engineering/wormhole/`. Nothing was written to
`noisemaker-for-cpp` or `noisemaker-for-cpu`; those trees were only read, and — for the
integration patch's build/test verification — compiled into standalone binaries in a **throwaway
copy under `/tmp`**, never in place.

## Part 1 — JS-golden oracle

`oracle/wormhole_oracle_generator.mjs` imports `runWormholeDeposit`, `Surface`, and
`float16Truncate` directly from the real, unmodified `noisemaker-for-cpu` source files (sha256
pinned, re-verified at load time) and drives them — it never reimplements the algorithm for
golden values. It produces `oracle/wormhole-oracles.json` (deterministic; `--check` mode
confirms byte-identical regeneration) plus `oracle/wormhole-oracle-report.md`.

**Cases: 62** — 14 hand-designed for discrimination (all three wrap modes; out-of-bounds
destinations; multi-source collisions; negative-stride negative-modulo stress; fractional
`wrap` values testing `|0` truncation; a large-stride precision-stress diagnostic; a
known-answer solid-white 1×1 case cross-checked against `oklabLightness(1,1,1) = 1.0` computed
independently) + 48 systematic sweep cases (16 canvas sizes — including `1×1`, `1×7`/`5×1`,
odd non-square `9×13`/`17×31`, and power-of-two `8×8`/`16×16`/`33×33` — × all 3 wrap modes).
Every case is rendered twice (byte-identical required) and its input surface is checked
byte-unmutated by the call.

**Text-surgery self-check**: the oracle also reads `wormhole.js`'s own source text, strips the
`import`/`export` wrapper, and re-evaluates it as a standalone function — then asserts this
extracted copy reproduces the real imported function byte-for-byte on every case, *before*
trusting any mutation result built the same way.

**Mutations: 9**, each with a machine-checked reach predicate (computed from an independently
re-implemented, clearly-labelled diagnostic pass — never used as a golden-value source) requiring
nonzero divergence among reaching cases and **zero** divergence among non-reaching cases:

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | ---: | ---: | ---: | ---: |
| wrap-mirror-clamp-swap | 38 | 36 | 24 | 0 |
| wrap-else-becomes-clamp | 22 | 21 | 40 | 0 |
| source-row-flip-removed | 55 | 55 | 7 | 0 |
| destination-row-flip-removed | 55 | 55 | 7 | 0 |
| weight-formula-linear | 62 | 61 | 0 | 0 |
| float16-truncate-skipped | 62 | 61 | 0 | 0 |
| div13-not-frounded | 62 | 1 | 0 | 0 |
| oklab-matrix-not-frounded | 62 | 1 | 0 | 0 |
| alpha-channel-written | 62 | 62 | 0 | 0 |

The single non-divergent case for `weight-formula-linear`/`float16-truncate-skipped` is the
1×1 solid-white known-answer case, where `lightness = 1.0` exactly, making the quadratic and
linear weight formulas coincide and the accumulated value already exactly float16-representable
— explained, not hidden.

**A mutation that turned out to be a no-op — reported, not dropped.** The obvious
"`pixelStride` computed in float32 first vs. double first" storage-order mutation was checked
(`oracle/wormhole-oracles.json`'s `pixel_stride_rounding_proof`, 22 sampled stride values) and
found to be **provably unobservable**: `Math.fround(1024 * stride) === 1024 * Math.fround(stride)`
always, because 1024 is an exact power of two and scaling by an exact power of two commutes with
round-to-float32. This is exactly the "obvious mutation is a no-op" trap the task brief warned
about. It's documented as a checked non-discriminator rather than silently dropped or falsely
claimed as coverage.

Two direct-row tables freeze function-level ground truth using the REAL extracted closures:
`wrap_function_rows` (18 `wrapRepeat` + 18 `wrapMirror` rows, including negative inputs, checked
against an independent floor-division formula — not `wrapRepeat`'s own formula, which would be
circular) and `oklab_lightness_rows` (12 rows spanning clamped-negative/clamped->1/zero/unit
inputs).

## Part 2 — C++ port and verification

`cpp/wormhole_deposit.hpp` is a standalone C++20 port with zero dependency on either repo's
headers. Every intermediate value is a `double`; `f32r()` performs exactly the
"round-trip-through-float32-and-back" that `Math.fround` performs, and `add`/`mul`/`divd` apply
it exactly once, in the same place the JS source does — chained
`add(add(mul(...),mul(...)),mul(...))` expressions are never flattened. `div(1,3)` is F32-rounded
before `pow`. `pixelStride` stays `double`, never pre-narrowed. Vertex rows are bottom-up for
both source and destination. `weight = lightness²`; RGB channels round-trip through a
truncating (not rounding) `float16_truncate` port of `texture-format.js`'s
`float16Truncate`/`decodeFloat16`; alpha is never touched.

**A real bug this process found (not a JS precision quirk, a JS *algorithm* quirk):**
`wrapMirror(value, size)` has a genuine off-by-one for `value ≡ -1 (mod 2·size)` — it returns
exactly `-1` (never `size`, never anything else; proven by an exhaustive sweep over size
1–40 × value −5000–5000, 21,397 hits, always exactly `-1`). In JS this silently no-ops the
destination write: a `Float32Array` write at a negative or `>=length` integer index is a
documented no-op (verified empirically — `a[-1] = 99` on a fresh `Float32Array` leaves it
unchanged), never a throw, never a wraparound. The first C++ build crashed with a heap
out-of-bounds read at exactly this case (`mirror-collision-oob-6x5`, confirmed via
AddressSanitizer). The fix is **not** "clamp X and Y independently" — a lone out-of-range X with
an in-range row can alias into the *previous row's last pixel*, which JS genuinely writes to
(computed from the same unclamped flat-offset arithmetic JS uses). The port instead computes the
flat `destinationOffset` from the raw, unclamped row/column exactly as JS does, and skips the
three-channel write only when that flat offset falls outside `[0, width·height·4)` — reproducing
JS's per-index bounds semantics exactly rather than reasoning about rows/columns.

**Compile flags**: built and tested at `-O0` through `-O3`, all bit-exact, with the mandated
`-std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off` (zero warnings). Also built
*without* `-ffp-contract=off` as a control: still bit-exact for every case, because this port's
per-operation-rounding style (every `add`/`mul` performs an explicit `static_cast<float>` before
returning) already forces a real, observable rounding barrier the compiler cannot fuse across —
FMA contraction has nothing to attach to. `-ffp-contract=off` remains mandatory per the task
brief and is what ships; the control build is reported as evidence, not as license to drop it if
this code is ever refactored into a flatter expression style.

**Transcendental cross-platform risk — checked, not assumed.** V8's `Math.cos`/`sin`/`pow` and
Apple's libm `std::cos`/`sin`/`pow` are different implementations; bit-identical results across
them are not guaranteed by any spec. This is the single largest a-priori risk to "bit-exact." It
was tested empirically, not waved away: all 36,228 compared lanes below are bit-exact, including
angle values densely covering the full `[-2π, 4π]`-ish range the wormhole formula produces (kink
up to 5, rotation across the full ±180° range) and `oklabLightness`'s `pow(x, 1/3)` calls across
12 direct-row inputs plus every pixel of all 62 cases. No divergence was found. This is strong
empirical evidence for this input domain on this toolchain (Apple clang 16 / arm64), but it is
**not a mathematical guarantee for all possible inputs or other libm implementations** — flagged
explicitly per the task's request to report anything not fully nailed down.

### Comparison results (`cpp/verify_wormhole`, oracle JSON as input, mandated flags)

Direct-row tables: **0/18 wrapRepeat mismatches, 0/18 wrapMirror mismatches, 0/12
oklabLightness mismatches.**

Full-pass cases, broken out by resolved wrap mode:

| Wrap mode | Cases | Lanes compared | Lanes exact | Max abs diff |
| --- | ---: | ---: | ---: | ---: |
| 0 (mirror) | 19 | 11,796 | 11,796 | 0 |
| 1 (repeat) | 22 | 12,200 | 12,200 | 0 |
| 2 (clamp) | 20 | 12,136 | 12,136 | 0 |
| 7 (arbitrary "else" value, exercises the repeat branch via a non-canonical `wrap` int) | 1 | 96 | 96 | 0 |
| **Overall** | **62** | **36,228** | **36,228** | **0** |

**Every lane, every case, every wrap mode: bit-exact. Max abs diff 0 throughout — not "close",
literally zero divergence.**

Reproduce: `cd cpp && ./build.sh && ./verify_wormhole ../oracle/wormhole-oracles.json`.

## Part 3 — Integration recommendation

`src/pass_runner.cpp`'s `run_pass` is a per-pixel **gather**: it calls a `BoundKernel`'s pixel
function once per destination pixel and fills every output pixel exactly once
(`include/noisemaker/kernel.hpp`, `include/noisemaker/surface.hpp`). Scatter passes are a
structurally different shape (variable points-per-source, zero-to-many destinations, and now a
confirmed real no-write case), so they need their own dispatch rather than being forced through
`run_pass`.

**Recommendation** (patch below, not applied): add `noisemaker::scatter`, mirroring
`scatter-registry.js` 1:1 —

- `include/noisemaker/effects/scatter/registry.hpp` + `src/effects/scatter/registry.cpp`: a
  `ScatterAdapter = std::size_t(*)(const glsl::Bindings&, Surface&)` function-pointer type and a
  `register_scatter_adapter`/`resolve_scatter_adapter` map, keyed by the **same**
  `"${effectId}:${program}"` string the JS side and the ported manifest already use. Adapters
  read uniforms/textures through `glsl::Bindings` — the *same* binding object an ordinary
  `bind_*` kernel factory receives — so there is one uniform-resolution code path for both pass
  shapes, not two.
- `include/noisemaker/effects/scatter/wormhole.hpp` + `src/effects/scatter/wormhole.cpp`: the
  verified port plus a thin adapter wrapper and an explicit `register_adapter()` (never a global
  static constructor — matches this codebase's existing flat-declaration style in
  `generated/catalog.hpp` and avoids static-init-order hazards).
- `include/noisemaker/effects/scatter/catalog.hpp` + `.../catalog.cpp`: one aggregator,
  `register_builtin_scatter_adapters()` (idempotent via a function-local magic-static, safe to
  call from multiple independent sites), with a one-line comment marking where each of the six
  remaining JS scatter adapters (`dla:depositGrid`, `lenia:deposit`, `physarum:deposit`,
  `render/pointsRender:deposit`, `render/pointsBillboardRender:deposit`, `filter3d/flow3d:deposit`)
  gets its own call when ported — no new machinery required for any of them.
- **Future dispatch site** (no multi-pass driver exists yet in `noisemaker-for-cpp` — only
  direct `BoundKernel`/`run_pass` calls were found): whatever eventually plays `renderer.js`'s
  role of iterating a pass list needs exactly one new branch, mirroring `renderer.js`'s own
  `pass.drawMode === 'points' || 'billboards'` check, calling `resolve_scatter_adapter` instead
  of building a `BoundKernel` when it matches. That branch is the entire integration surface —
  Surface lifetime, uniform binding, and output quantization are already shared with the gather
  path.

**This was verified to actually work, not just designed on paper.** The patch was applied to a
throwaway full copy of `noisemaker-for-cpp` under `/tmp` (never the real tree), built with
`cmake --build` using the project's own unmodified mandated flags, and its `ctest` suite —
including 5 new tests (`tests/test_scatter_wormhole.cpp`, 3 independent regression vectors
captured directly from the real JS plus a registry round-trip and a dimension-mismatch-throws
check) — passed 100%, alongside every pre-existing test. See `integration/patch-verification.txt`
for the transcript.

## What could not be fully nailed down

- **Transcendental bit-identity across libm implementations** is empirically confirmed for every
  input this oracle exercises (36,228+ lanes, dense angle/lightness coverage) but is not a
  mathematical guarantee for inputs outside that domain or on non-Apple-clang/arm64 toolchains.
  If this port is ever built with a different compiler or on x86_64, re-run
  `cpp/verify_wormhole` against the same oracle before trusting bit-exactness there.
- The C++ side currently has **no multi-pass driver** to wire the new dispatch branch into (only
  direct `BoundKernel` calls exist in tests/examples) — the integration patch adds the
  scatter-adapter machinery and the wormhole adapter itself, both verified working, but the
  "one new `if` branch" in the future driver is a recommendation, not a merge, since that driver
  doesn't exist yet to modify.
- Everything else — oracle determinism, mutation discrimination, the `wrapMirror` off-by-one
  and its no-op semantics, `-ffp-contract=off` sensitivity, and full-pass bit-exactness — was
  directly verified with evidence in this directory, not assumed.

## File map

```
oracle/wormhole_oracle_generator.mjs   JS oracle generator (imports the real runWormholeDeposit)
oracle/wormhole-oracles.json           62 cases, 9 mutations, direct-row tables, provenance
oracle/wormhole-oracle-report.md       human-readable oracle summary
cpp/wormhole_deposit.hpp               standalone C++20 port (the reviewed algorithm)
cpp/json_min.hpp                       minimal self-contained JSON reader for the harness
cpp/verify_wormhole.cpp                comparison harness (oracle JSON -> C++ -> bit-exact diff)
cpp/build.sh                           builds verify_wormhole with the mandated flags
cpp/verify_output.txt                  captured run of the final verification
integration/staging/...                the ready-to-apply files, in their real repo-relative paths
integration/wormhole-scatter-integration.patch   the patch itself (unified diff, 8 files)
integration/patch-verification.txt     transcript: patch applied + full project built + tests passed
*.sha256                               sidecar checksums for every deliverable above
```
