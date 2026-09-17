# The six remaining scatter adapters — bit-exact C++ ports, oracles, and sweep results

## What this is

`noisemaker-for-cpu`'s `src/effects/cpu/scatter-registry.js` registers seven hand-written CPU
"scatter" adapters for vertex-stage (`drawMode: "points"`/`"billboards"`) passes. Wormhole
(`filter/wormhole:deposit`) was already ported and verified (see `docs/port-engineering/wormhole/`).
This directory ports and verifies the remaining six:

| Registry key | JS source | C++ files |
| --- | --- | --- |
| `points/dla:depositGrid` | `src/effects/cpu/points-deposit.js:176-216` | `dla.hpp`/`.cpp` |
| `points/lenia:deposit` | `src/effects/cpu/points-deposit.js:226-256` | `lenia.hpp`/`.cpp` |
| `points/physarum:deposit` | `src/effects/cpu/points-deposit.js:264-296` | `physarum.hpp`/`.cpp` |
| `render/pointsRender:deposit` | `src/effects/cpu/points-deposit.js:308-343` | `points_render.hpp`/`.cpp` |
| `render/pointsBillboardRender:deposit` | `src/effects/cpu/billboard-deposit.js` | `points_billboard_render.hpp`/`.cpp` |
| `filter3d/flow3d:deposit` | `src/effects/cpu/flow3d-deposit.js` | `flow3d.hpp`/`.cpp` |

Shared JS helpers (`texelFetchAgent`, `scatterPointPixel`, `computeClipCenter`, `fract`,
`GOLDEN_RATIO_CONJUGATE`) are ported ONCE into `points_deposit_support.hpp`/`.cpp`, mirroring
`points-deposit.js`'s own module boundary — every C++ adapter that needs them (all six) calls the
same implementation, never a re-typed copy.

## Adapter contract change

`noisemaker::scatter::ScatterAdapter` widened from
`(const glsl::Bindings&, Surface&) -> std::size_t` to
`(const glsl::Bindings&, const ScatterPass&, Surface&) -> std::size_t`. `ScatterPass` carries only
the two `pass`-record fields any adapter (old or new) actually reads: `pass.blend`
(`render/pointsBillboardRender:deposit`'s `isPremultipliedBlend`) and `pass.count`
(`filter3d/flow3d:deposit`'s `pass?.count ?? capacity`) — not the scalar `bindings` context
(`time`/`frame`/`seed`/...) or `params`, since no shipped adapter reads either. Wormhole's own
adapter takes and ignores the new parameter; its four pre-existing tests
(`tests/test_scatter_wormhole.cpp`) still pass byte-for-byte against the same embedded JS oracle
vectors after the signature change.

## A real bug the randomized sweep found (not a JS quirk — a porting mistake)

`computeClipCenter`'s `uniforms.fieldOfView` read (only reached under `viewMode === 2`) has **no**
`?? default` in the JS source, unlike `uniforms.posZ ?? 0`. An early version of both
`points_render.cpp` and `points_billboard_render.cpp` defaulted an unbound `fieldOfView` binding to
`0.0`, which sends `focalLength = 1 / Math.tan(0 * 0.00872664626)` to `Infinity` instead of the
correct `NaN` (JS `Math.max(undefined, 10)` coerces `undefined` to `NaN` via `ToNumber`, and
`Math.max`/`Math.min` return the first NaN argument, not a default). The 12,000-case
`render/pointsRender:deposit` sweep caught this immediately (62 divergent cases, values like
`Infinity`/`744.07`/`NaN` where JS had a real finite number or `-0`) before any fix landed in
`points_billboard_render.cpp`, which shares the same bug and was fixed pre-emptively. Fixed by
defaulting the binding to `std::numeric_limits<double>::quiet_NaN()` instead. Both fixed points are
called out in-code (`points_render.cpp`, `points_billboard_render.cpp`,
`points_deposit_support.hpp`'s `ClipCenterUniforms::field_of_view` comment).

## Numeric semantics, verified against a live V8 build, not assumed

- None of the six adapters ever calls `Math.fround` except billboard's `hash()` — grep-verified.
  The only other narrowing is the destination `Surface`'s own float32 store on `+=`, which C++
  `float += double` already reproduces exactly (usual arithmetic conversions: widen to double, add,
  narrow back on assignment).
- **`Math.min`/`Math.max` are NOT `std::min`/`std::max`, and NOT
  `glsl::component_min<double>`/`component_max<double>`.** Empirically verified against this
  session's live Node/V8 build (a custom-payload NaN injected via a `DataView`,
  `0x7ff8000000000123`): `Math.min`/`Math.max` return the FIRST NaN argument scanning left to
  right, with its EXACT bit pattern preserved — never a re-materialized canonical NaN.
  `std::min`/`std::max`'s tie-break is unspecified and empirically disagrees for at least one
  argument order; `glsl::component_min`/`component_max` (this codebase's existing GLSL-facing
  helper) deliberately forces a canonical NaN, which is correct for THAT helper's own contract but
  not for a literal `Math.min`/`Math.max` port. `points_deposit::js_min`/`js_max` implement the
  measured behavior directly (reproduction commands below). `Math.sign` gets the same
  payload-preserving treatment (`js_sign`, local to `points_billboard_render.cpp`), verified the
  same way.
- Transcendentals route through `noisemaker::fdlibm` (`cos`/`sin`/`exp`/`tan`) — never `std::`;
  `sqrt`/`abs`/`floor`/`ceil`/`trunc` use `std::` per this codebase's established convention
  (IEEE-correctly-rounded / exact-agreement functions need no fdlibm shim).
- Billboard's sprite sampling reuses the EXISTING, already-shipped
  `noisemaker::sample_nearest_bottom_left`/`sample_bilinear_bottom_left` DOUBLE overloads (the same
  ones `src/effects/remap.cpp`'s `sample_zone_texture` already uses) — never the FLOAT overload,
  which would narrow `u`/`v` to float32 before sampling and diverge from JS's pure-double
  `sampleSprite` pipeline.
- Caught and fixed during authoring (before any sweep ran): two `!(x > 0)` mistranslations of JS's
  own `x <= 0` in the billboard adapter (`blurRadius`, `aperture`) — `!(NaN > 0)` is `true` but
  `NaN <= 0` is `false`, so these disagreed from JS on a NaN operand. Corrected to the literal
  `<= 0` form JS actually uses.

### V8 empirical verification commands (reproduce the `Math.min`/`Math.max`/`Math.sign` behavior above)

```bash
node -e '
function bits(x){const b=new DataView(new ArrayBuffer(8)); b.setFloat64(0,x); return [...Array(8)].map((_,i)=>b.getUint8(i).toString(16).padStart(2,"0")).join("");}
const buf = new ArrayBuffer(8); const dv = new DataView(buf);
dv.setBigUint64(0, 0x7ff8000000000123n); const nA = dv.getFloat64(0);
dv.setBigUint64(0, 0x7ff8000000000456n); const nB = dv.getFloat64(0);
console.log("min(5, nA)", bits(Math.min(5, nA)));
console.log("min(nA, nB)", bits(Math.min(nA, nB)));
console.log("min(nB, nA)", bits(Math.min(nB, nA)));
console.log("min(3, nA, 5)", bits(Math.min(3, nA, 5)));
console.log("sign(customNaN)", bits(Math.sign(nA)));
'
```

## Oracle generators (`.mjs`, import the REAL authority adapters directly)

Each of `docs/port-engineering/scatter-adapters/oracle/{dla,lenia,physarum,points_render,
points_billboard_render,flow3d}_oracle_generator.mjs` imports the real, unmodified adapter function
from the pinned authority snapshot (`/Users/alex/platform/.nm-cpp-work/authority/61aa869`) and
calls it directly — never reimplements the algorithm. Each produces:

- `<name>-oracles.json` — a curated, human-reviewable case set (hand-designed discrimination cases
  covering dead/alive-boundary agents, off-canvas landings, NaN/Infinity propagation, non-square
  and 1×N textures, destination-vs-agent-texture size mismatches, overlapping-deposit stress, and a
  systematic size × parameter sweep), with the full float32 destination buffer embedded as hex plus
  a SHA-256, and every case rendered twice from byte-identical inputs with a hard determinism
  check.
- `<name>-fuzz.bin` — a large randomized differential-sweep case file (binary format documented in
  `oracle/common.mjs`'s `CaseWriter`), fed to `tools/parity/scatter_fuzz_verify.cpp`.

Domain coverage per the task brief: many sizes (1×1, 1×N/N×1, odd non-square, up to 16×16 in the
curated sets), destination pre-seeded with non-zero content, inputs with random values including
negatives/>1/NaN/Inf/-0, points landing out of range and on edges, overlapping points, every
pass/blend variant (`points_billboard_render`'s additive/premultiplied/garbage-string/absent
`pass.blend`; `flow3d`'s present/fractional/negative/NaN/absent `pass.count`), and every optional
uniform's `?? default` fallback path exercised by actually OMITTING the key (not just setting it to
a default value) — `posZ`, `fieldOfView`, `blurLayer`, `sizeDistance`, `brightnessDistance`,
`aperture`, `focalDistance`.

### Curated case counts

| Adapter | Curated cases |
| --- | ---: |
| `points/dla:depositGrid` | 108 |
| `points/lenia:deposit` | 112 |
| `points/physarum:deposit` | 105 |
| `render/pointsRender:deposit` | 122 |
| `render/pointsBillboardRender:deposit` | 167 |
| `filter3d/flow3d:deposit` | 112 |

## Randomized differential sweep — reproduce and results

Generate (writes both the curated JSON and the `-fuzz.bin` file for that adapter):

```bash
cd docs/port-engineering/scatter-adapters/oracle
node dla_oracle_generator.mjs --fuzz-count=12000
node lenia_oracle_generator.mjs --fuzz-count=12000
node physarum_oracle_generator.mjs --fuzz-count=12000
node points_render_oracle_generator.mjs --fuzz-count=12000
node flow3d_oracle_generator.mjs --fuzz-count=12000
node points_billboard_render_oracle_generator.mjs --fuzz-count=15000
```

Verify (build `scatter-fuzz-verify` via the project's normal CMake build, then):

```bash
cd <build-dir>
./scatter-fuzz-verify "points/dla:depositGrid"                    <repo>/docs/port-engineering/scatter-adapters/oracle/dla-fuzz.bin
./scatter-fuzz-verify "points/lenia:deposit"                       <repo>/docs/port-engineering/scatter-adapters/oracle/lenia-fuzz.bin
./scatter-fuzz-verify "points/physarum:deposit"                    <repo>/docs/port-engineering/scatter-adapters/oracle/physarum-fuzz.bin
./scatter-fuzz-verify "render/pointsRender:deposit"                <repo>/docs/port-engineering/scatter-adapters/oracle/points_render-fuzz.bin
./scatter-fuzz-verify "filter3d/flow3d:deposit"                    <repo>/docs/port-engineering/scatter-adapters/oracle/flow3d-fuzz.bin
./scatter-fuzz-verify "render/pointsBillboardRender:deposit"       <repo>/docs/port-engineering/scatter-adapters/oracle/points_billboard_render-fuzz.bin
```

**Literal results** (this run, after the fieldOfView fix — zero divergence across every adapter):

```
scatter-fuzz-verify key="points/dla:depositGrid" file=".../dla-fuzz.bin" cases=12000 total_lanes=589092 divergent_lanes=0 divergent_cases=0 pixel_count_mismatches=0
scatter-fuzz-verify key="points/lenia:deposit" file=".../lenia-fuzz.bin" cases=12000 total_lanes=588652 divergent_lanes=0 divergent_cases=0 pixel_count_mismatches=0
scatter-fuzz-verify key="points/physarum:deposit" file=".../physarum-fuzz.bin" cases=12000 total_lanes=589972 divergent_lanes=0 divergent_cases=0 pixel_count_mismatches=0
scatter-fuzz-verify key="render/pointsRender:deposit" file=".../points_render-fuzz.bin" cases=12000 total_lanes=583956 divergent_lanes=0 divergent_cases=0 pixel_count_mismatches=0
scatter-fuzz-verify key="filter3d/flow3d:deposit" file=".../flow3d-fuzz.bin" cases=12000 total_lanes=591620 divergent_lanes=0 divergent_cases=0 pixel_count_mismatches=0
scatter-fuzz-verify key="render/pointsBillboardRender:deposit" file=".../points_billboard_render-fuzz.bin" cases=15000 total_lanes=733768 divergent_lanes=0 divergent_cases=0 pixel_count_mismatches=0
```

Every case's destination buffer AND returned pixel count matched the JS-computed expected values
byte-for-byte (raw `memcmp` over float32 bytes — distinguishes -0 from +0 and preserves NaN-payload
differences a numeric `==` would hide). Total: **75,000 randomized cases, 3,677,060 float lanes
compared, 0 divergent lanes, 0 divergent cases, 0 pixel-count mismatches**, well above the
task's 10,000-case-per-adapter minimum.

**Before the fix**, the `render/pointsRender:deposit` sweep reported (same 12,000-case file, same
build otherwise): `divergent_lanes=271 divergent_cases=62 pixel_count_mismatches=62` — this is the
run that surfaced the fieldOfView bug described above; it is not hidden or discarded, only
superseded by the post-fix run above.

`.bin` fuzz files are regenerated by the commands above and are NOT checked into the repository
(tens of MB each); the `.mjs` generators (checked in) plus the fixed seeds embedded in them make
every run exactly reproducible. The curated `-oracles.json` files ARE checked in as the durable,
reviewable oracle artifact.

## Native tests

`tests/test_scatter_{dla,lenia,physarum,points_render,points_billboard_render,flow3d}.cpp` (added
to `CMakeLists.txt`'s `noisemaker-cpu-tests` target), each with a registry-lookup check plus 3-4
embedded regression vectors captured directly from the real JS adapters (dead/boundary-alive agent,
a direct-call case, a via-registry case, and — for billboard — one additive, one premultiplied, one
dead, and one procedural-shapeMode case). Command:

```bash
cd <build-dir>
cmake --build . --target noisemaker-cpu-tests -j4
./noisemaker-cpu-tests | grep -E "scatter_(dla|lenia|physarum|points_render|points_billboard_render|flow3d|wormhole)"
```

All new and pre-existing scatter tests pass (30 `PASS scatter_*` lines, 0 `FAIL scatter_*` lines).
Full-suite run (same binary, no filter): pre-existing, unrelated failures (the base tree is
mid-integration — `palette_override_oracle_*`, two `graph_*`, one `typed_task15_*`, 38 total) are
unchanged before and after this work; PASS count increased from 512 to 531 (19 new scatter test
cases across the six new files, plus the 6 registry-lookup placeholders already counted).

## Sanitizer build

Reconfigured the same build directory with `-fsanitize=address,undefined -fno-sanitize-recover=all`
(`CMAKE_CXX_FLAGS`/`CMAKE_EXE_LINKER_FLAGS`) and rebuilt `noisemaker-cpu-tests` from clean object
files, then ran the full suite:

```bash
cmake -S <repo> -B <build-dir> -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-sanitize-recover=all" -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build <build-dir> --target noisemaker-cpu-tests -j4
<build-dir>/noisemaker-cpu-tests
```

All 30 `scatter_*` tests (wormhole's 5 plus the 25 across the six new adapters) pass under
ASan+UBSan with **zero** sanitizer reports (`grep -iE "ERROR: AddressSanitizer|ERROR:
UndefinedBehaviorSanitizer|runtime error:|SUMMARY: "` over the full run's stdout+stderr: no
matches). The suite's overall PASS/FAIL counts are unchanged from the non-sanitized run (531
PASS / 38 pre-existing FAIL) — the FAILs are ordinary `REQUIRE` failures in unrelated, already-
failing tests, not sanitizer aborts (confirmed by inspecting their text: `graph:binding_type: ...`,
`requirement failed: ...`, no ASan/UBSan stack trace of any kind).

## What could not be fully nailed down

- **No multi-pass driver exists yet** in `noisemaker-for-cpp` to dispatch through
  `resolve_scatter_adapter` at render time (same situation wormhole's own report already recorded)
  — these six adapters are registered and oracle-verified, but wiring the executor's per-pass loop
  to call them is explicitly out of scope for this task (another worker's assignment) and
  `src/graph/executor.cpp` was not touched.
- **Transcendental bit-identity across libm implementations** is empirically confirmed for every
  input these oracles exercise (75,000+ randomized cases plus ~726 curated cases, dense coverage of
  the angle/lightness/rotation domains each adapter's transcendentals see) on this session's Apple
  clang / arm64 toolchain, but is not a mathematical guarantee for inputs outside that domain or on
  a different compiler/architecture — consistent with wormhole's own report's flag on the same
  point.
- Mutation-testing-style discriminator tables (wormhole's report's own extra rigor, e.g. per-
  mutation reach/divergence tables) were not built for these six adapters — out of scope for this
  task's stated verification standard, which asks for the oracle generator, the randomized sweep,
  native tests, and sanitizer builds, not mutation coverage tables. The randomized sweep's 0/3.68M
  divergent lanes result is the evidence of record.
