# noisemaker-for-cpp Phase 2 architecture map

Sources cited throughout:
- **JS authority** (`noisemaker-for-cpu` pinned at `61aa869`): `<noisemaker-for-cpu@61aa869>`
- **cpp port** (integration checkpoint, NOT the main checkout): `<noisemaker-for-cpp integration tree>`

All file:line citations below are against these two exact trees. Anything not directly
read from source is marked **UNVERIFIED**.

---

## 0. Ground truth: what's actually missing (verified, not estimated)

The task brief's "159 of 205" / "46 missing" framing was verified exactly, not taken on
faith, by diffing the two kits' compiled compatibility lists:

```
<noisemaker-for-cpu@61aa869>/export-kit/compat-effects.json   -> 205 entries
<noisemaker-for-cpp integration tree>/export-kit/compat-effects.json        -> 159 entries
authority - cpp (the real gap)                                                      -> 46 entries, exact set below
cpp - authority                                                                     -> 0 entries (cpp claims nothing extra)
```

Both files are generated, not hand-maintained: `export-kit/generate-compat.mjs` (cpp side,
`<noisemaker-for-cpp integration tree>/export-kit/generate-compat.mjs`) computes
compat-effects.json from `src/effects/generated/backend_compatibility.json` **and** from
`executor.cpp`'s own hard-coded refusal lists (it regex-extracts `kMeasuredParityExclusions`
and `is_worm_overlay_resource`'s effect-id list straight out of the executor source, lines
21-27 of that script) — so the 159-count is a live, self-checking function of the current
source tree, not a stale snapshot. It also **unconditionally deletes `synth/media`** from
the list with the comment "The shipped CLI renders output only; it cannot supply media's
imageTex" (script line ~30) — a CLI-surface exclusion layered on top of backend/executor
compatibility, discussed in §7.

The exact 46-effect gap, confirmed against `backend_compatibility.json`'s 344
`reference_passes` records (`schema: "noisemaker-cpp.backend-compatibility.v1"`,
`<noisemaker-for-cpp integration tree>/src/effects/generated/backend_compatibility.json`),
splits into the five families the task brief proposed. The grouping is **correct as given**;
this document keeps it unchanged and adds two effects the authority ships that are *not yet*
counted in the 46/205 headline number at all (they postdate the 205-effect kit baseline both
kits' `compat-effects.json` were generated from) — `synth3d/heightmap3d` +
`render/renderLandscape3d` (extra members of family D) and `points/heightGrid` (extra member
of family E). Family sizes: A=8, B=8, C=2, D=14(+2 new), E=14(+1 new). 8+8+2+14+14=46.

Per-pass status counts across all 344 backend_compatibility.json records:
`compatible: 210, missing: 132, scatter: 1, incompatible: 1`. Of the 46 gap effects, **every
pass in families B, C, D, and E is `status: "missing"` (`missing_backend_program`)** — i.e.
no GLSL kernel has ever been generated for them. Family A is the outlier: all of its
individual programs are already `"compatible"` except `filter/wormhole:deposit`, which is the
codebase's *only* `"scatter"` record. This one fact reshapes the whole roadmap: family A is
overwhelmingly an **executor/CLI** problem, not a codegen problem, while B/C/D/E are
overwhelmingly a **combined codegen + executor** problem.

---

## 1. Executive summary of the JS runtime primitives (shared across all families)

Read in full: `src/runtime/iteration.js`, `src/runtime/pass-runner.js`, `src/runtime/surface.js`,
`src/runtime/sink.js`, `src/runtime/texture-format.js`, `src/runtime/buffer-pool.js`,
`src/runtime/render-result.js`, `src/runtime/sampler.js`, `src/runtime/cpu-frame-export.js`,
`src/runtime/frame-export.js`, and the first ~950 of 1678 lines of `src/runtime/renderer.js`
(all paths under the authority root).

- **Iteration groups** (`src/runtime/iteration.js:57-105`, `computeIterationGroups`): partitions
  one chain's compiled steps into `{steps, iterated, loop?}` groups. Three group-forming rules,
  evaluated in this order: (1) `read`/`write` steps are always boundaries — they close any open
  group and form their own one-step group (`iteration.js:79-83`); (2) `loopRole === 'begin'`
  opens an `openLoop` region that swallows every subsequent step until `loopRole === 'end'`
  closes it as `{iterated:true, loop:true}` (`iteration.js:84-88,73-76`); nested `begin`, an
  unmatched `begin`/`end`, or a read/write crossing the region all throw synchronously
  (`iteration.js:70-71,84,102`); (3) a step that declares `global_xyz` in its own
  `definition.textures` (only `render/pointsEmit` ever does) closes whatever's open and opens a
  **new, owned** particle group (`iteration.js:90-93`) — even if that means two `pointsEmit()`
  calls in one chain open two independent, non-merged groups. While a particle group is open, a
  later step **joins** it iff any of its own pass inputs/outputs reference a
  `PARTICLE_STATE_PATTERN`-matching name (`^global_(xyz|vel|rgba|life_data)$|^global_.*_trail$`,
  `iteration.js:14`); otherwise it closes the group (`iteration.js:95-99`). A group's `iterated`
  flag is just the opening step's own `definition.iterated`.
- **Iteration schedule** (`renderer.js:852-893` `runIteratedGroupSync`, mirrored async at
  895-936): `N = Number.isFinite(group.steps[0].params.iterationCount) ? that : 60`.
  `N<=0` short-circuits to `zeroIterationGroupOutput` (`renderer.js:595-634`) — clone the input
  bundle with **no pass run at all**, or (chain-starting volume generator) a zeroed
  volume/geometry atlas. Otherwise, for `i` in `[0,N)`: `iterationOptions = {...renderOptions,
  frame: i, deltaTime: 1/600 (`ITERATION_DELTA_TIME`, `iteration.js:21`), time:
  wrap01(renderOptions.time - (N-1-i)/600)}` (`renderer.js:873-878`, `wrap01(x)=((x%1)+1)%1` at
  `iteration.js:23-25`). Every step in the group runs once, in order, via
  `runGroupStepIterationSync` (`renderer.js:943` onward), threading `stepInput` between them;
  **resources persist across iterations** in `state.resources` (allocated once by
  `initializeGroupStepState`, `renderer.js:660-677`) rather than being recreated — this is the
  entire reason a joined chain can accumulate a trail texture or a simulation state across ticks
  instead of re-running from scratch every iteration.
- **`selfTex`/`feedback`** (`renderer.js:60-72,654-676,738,1068-1071`): a reserved input-route
  token, never a declared texture and never a pass output. `initializeGroupStepState` allocates
  one persistent, zeroed surface *per step* the first time any of that step's passes lists
  `selfTex` or `feedback` as an input (`renderer.js:665-674`); it is never stored under its own
  name in `resources` (so `replaceCanonicalResource` can never recycle it mid-run) and is
  updated by an explicit `Float32Array#set` **memcpy** from that iteration's real output at the
  end of each iteration (`renderer.js:1068-1071` and the three sibling occurrences), never a
  reference swap. `filter/convolutionFeedback` is the only shipped effect that reads it
  (`renderer.js:64`). Outside an iterated group, or on iteration 0, it resolves to a permanently
  zeroed placeholder (`renderer.js:402,738`) — matching upstream's first-frame behavior.
- **`global_accum` / loop regions**: `runIteratedGroupSync` allocates one `global_accum` surface
  per loop-region group, sized from the group's input image, stored in the group-shared
  `groupResources` map (`renderer.js:857-865`), and released at the end like every other group
  resource unless retained in the final output (`renderer.js:886, finishGroupResources`
  `832-850`). `groupInputTextures` (`renderer.js:726-743`) special-cases both particle-state
  names *and* `global_accum` to route through `groupResources` instead of the step's own
  resource map; `storeGroupOutput` (`renderer.js:762-765`) does the same on the output side. The
  exact per-iteration accumulate/blend arithmetic and how `loopEnd` converts `global_accum` back
  into `outputTex` were **traced by the family B/C sub-agent** (see §3.2/§3.3 below) rather than
  by this top-level pass, since it requires reading past line 950 of `renderer.js` plus the
  `loopBegin`/`loopEnd` JS effect definitions.
- **Volume/geometry bundle** (`renderer.js:97-124,107-116`): a chain's "current image" becomes a
  `{image, volume, geometry, volumeSize}` bundle the moment any step is a `volume-*` domain
  effect (`isChainBundle`/`chainBundle`). `inheritVolumeSize` (`renderer.js:107-116`) is the
  N×N² rule: an **incoming** volume atlas's `.width` always becomes the effective `volumeSize`
  for a `volume-generator|volume-filter|volume-renderer` step, *overriding* both the param
  default and any explicitly-supplied mismatched value, after asserting
  `volume.height === volumeSize**2`. `bundleOutput` (`renderer.js:118-124`) resolves the
  passthrough names `inputTex`/`inputTex3d`/`inputGeo`. The four near-duplicate dispatch sites
  (`renderer.js:1051-1071, 1185-1205, ~1320-1340, ~1465-1485` — sync/async × canonical/iterated)
  each recompute `volumeSize` the same way: `domain==='volume-generator' ? (params.volumeSize ??
  volume?.width ?? null) : (inputBundle.volumeSize ?? params.volumeSize ?? volume?.width ??
  null)`, then re-validate the `expectedWidth/expectedHeight = volumeSize/volumeSize**2` shape of
  whatever the step actually produced.
- **MRT** (`drawBuffers >= 2`): `runCanonicalMrtPass`/`Async` (`renderer.js:450-533`) run one
  shared pixel loop writing a `4*destinations.length`-float scratch buffer per pixel, scattering
  each 4-float chunk into its own destination `Surface` — i.e. one kernel call produces *all*
  MRT outputs for a pixel atomically. `canonicalMrtDestinations`/`groupMrtDestinations`
  (`renderer.js:542-554,806-814`) allocate one destination per `factory.outputNames` entry and
  **assert** they all share identical width/height (`assertMrtDestinationsShareDimensions`,
  `renderer.js:51-58`) — a hard requirement, not a convention.
- **Pass-level `repeat`/`conditions`/`defines`/`viewport`**
  (`renderer.js:159-177,372-385,184-205`): numeric `pass.repeat` used as-is (default 1); a
  string `repeat` names a uniform holding the count (`resolveRepeatCount`). `conditions.runIf`/
  `skipIf` gate whether a pass runs at all, via `Number(uniforms[x]) === / !== Number(equals)`
  (`passIsActive`). Pass-level `defines` (used for `pointsRender`/`pointsBillboardRender`'s
  per-viewMode variants) are bound as **ordinary runtime uniforms**, not baked shader variants —
  "this port declares each such macro name as an ordinary uniform... and binds its literal value
  at call time" (`renderer.js:372-377`; corroborated by `CSL.md`'s "Canonical GLSL
  compatibility" section). A pass's `viewport.width/height` overrides the destination texture's
  own declared size (`renderer.js:384-385`) — this is exactly how a 6-face cubemap or a
  per-repeat varying-size pass would size its own output differently from the parent effect's
  declared texture spec (see family D's cubemap analysis).
- **Scatter dispatch** (`renderer.js:963-965,1096-1098,1232-1234,1377-1379`, four near-duplicate
  call sites): any pass whose kernel isn't run through the ordinary per-pixel gather is looked up
  by `${effectId}:${pass.program}` in `scatter-registry.js`'s adapter map
  (`src/effects/cpu/scatter-registry.js`, read in full) and invoked with a small scalar
  `bindings` object (`buildScatterBindings`, `renderer.js:819-830`) plus raw `{pass, uniforms,
  inputs, destination, params}` — deliberately NOT the full per-pixel kernel context. 7 total
  adapters exist: `filter/wormhole:deposit` (ported to cpp already), `filter3d/flow3d:deposit`,
  `points/dla:depositGrid`, `points/lenia:deposit`, `points/physarum:deposit`,
  `render/pointsRender:deposit`, `render/pointsBillboardRender:deposit` (last two share one
  registration, dispatched on `pass.blend`).
- **Float precision discipline**: `pass-runner.js:26` and the MRT variants Math.fround both
  `time` and `seed` once at context-build time; per-pixel kernel bodies otherwise operate however
  the generated/adapter code chooses. Every hand-written CPU adapter examined so far
  (`wormhole.js`, `worm-overlay.js`) performs an explicit `Math.fround` after *every* add/mul,
  matching the authority's own float32-register discipline — **this per-operation rounding
  point, not just the final store, is what makes bit-exactness possible**, and is the pattern
  the ported `scatter/wormhole.cpp` reproduces via its own `f32r()` helper on every
  `add`/`mul`/`div`. Any new hand adapter for families A/E must follow the same discipline: round
  after every individual floating op the JS source performs it after, never at the end of a
  fused expression.

## 2. Executive summary of the cpp architecture today

Read in full or in relevant part: `include/noisemaker/graph/{executor.hpp,execution_plan.hpp,
resource.hpp}`, `include/noisemaker/effects/{catalog_types.hpp,catalog.hpp,registry.hpp}`,
`src/graph/executor.cpp` (2101 lines — read ~900 of them across the validation and execution
paths), `src/effects/registry.cpp` (971 lines, admission()/domain-validation sections),
`src/dsl/compiler.cpp` (chain-grammar validation section), `src/effects/scatter/*`,
`export-kit/generate-compat.mjs`, `tools/cli/noisemaker_render.cpp`, and
`src/effects/generated/backend_compatibility.json`'s schema (all paths under the cpp root).

Pipeline: DSL source → `dsl::compile()` (`src/dsl/compiler.cpp`) validates chain grammar
(domain ordering: generator-must-open-chain, volume-filter/renderer-needs-a-volume,
loop-begin/end balancing — **already generic**, see §2.3) and builds an `ExecutionPlan`
(`include/noisemaker/graph/execution_plan.hpp`) whose `PlanEffectSnapshot`s each carry one
`PassAdmission` per pass from `EffectRegistry::admission()` (`src/effects/registry.cpp:926-965`).
`GraphExecutor::execute(plan, inputs)` (`src/graph/executor.cpp:1850-2099`) then runs it.

**2.1 The executor's four blanket refusals** (`executor.cpp`, both in
`validate_plan_before_allocation` at ~763-843/987-1033 and in `validate_pass_controls` at
~1331-1340 — the same four checks appear at both the pre-allocation dry-run and the real
per-pass authentication, so there is no way to get past them by any current code path):

1. `admission.status == AvailabilityStatus::scatter` → `GraphErrorCode::unsupported_scatter`,
   message **"scatter is not enabled in Task 6"** (`executor.cpp:781-787,1012-1014`).
2. `admission.authority_pass.blend || pass.blend->enabled` →
   `GraphErrorCode::unsupported_blend`, **"blend is not enabled in Task 6"**
   (`executor.cpp:1019-1022`).
3. `admission.draw_mode != "fragment"` (or `pass.draw_mode` explicitly non-fragment) →
   `GraphErrorCode::unsupported_draw_mode`, **"draw mode is not fragment"**
   (`executor.cpp:1023-1027,1339`).
4. `pass.draw_buffers` present and not exactly `1.0` → `GraphErrorCode::unsupported_mrt`,
   **"multiple draw buffers are unsupported"** (`executor.cpp:1028-1033,1340`); reinforced by
   `validate_pass_output_abi` (`executor.cpp:634-655`), which independently requires **exactly
   one** fragment output (`kFragmentOutputSymbol = "fragColor"`) per pass.
5. `admission.dimensionality != "image"` → `GraphErrorCode::unsupported_draw_mode`, **"only
   image dimensionality is supported"** (`executor.cpp:1338`) — this is the volume/geometry
   domain's blanket refusal, structurally identical in kind to the other four.
6. `pass.count.has_value() || pass.viewport.has_value()` → `GraphErrorCode::invalid_snapshot`,
   **"ordinary count or viewport is unsupported"** (`validate_ordinary_pass_metadata`,
   `executor.cpp:616-626`) — this blocks per-face cubemap viewport overrides and any
   scatter-style `count` before either subsystem is wired, independent of the scatter-status
   check above.

`GraphExecutor::execute`'s real per-step loop (`executor.cpp:1850-2099`) confirms these aren't
just validation-time checks with a different runtime path: the loop tracks exactly **one**
`GraphResource* current` between steps (the 2D image route) and, per pass, does exactly:
resolve ordered sampler routes → allocate one destination → `bind_factory_route` → `run_pass`
(the fragment gather) → quantize → publish. There is no iteration count, no loop region, no
particle-group bookkeeping, no volume/geometry bundle, and no scatter/MRT dispatch branch
anywhere in this loop. Every one of families B, C, D, and E needs new machinery *added to this
loop*, not merely new data plumbed through existing branches.

**2.2 What already has a name but no algorithm** — `is_worm_overlay_resource`
(`executor.cpp` ~215, used at ~872 and ~1930) recognizes the `overlayTex` texture for
`filter/fibers`/`filter/scratches`/`filter/strayHair` and throws a *specific*
"declared texture requires the canonical CPU worm-overlay adapter" refusal rather than a
generic one — i.e. cpp's authors already reserved the concept, they just haven't ported the
algorithm. Similarly, `kMeasuredParityExclusions` (`executor.cpp:739-751`,
`authenticate_measured_parity` at 753-761) hard-refuses `filter/snow:snow` and
`synth/testPattern:testPattern` even though **both already have a generated, "compatible"
typed kernel** — the generated kernel is *measured* to diverge from the authority (499/748
RGBA8 bytes for snow at 17×11; 2 grid-boundary pixels / 6 bytes for testPattern), so cpp
refuses rather than ship wrong pixels. This is not a "not yet ported" gap in the usual sense;
see family A's report for whether the fix is a hand adapter (matching JS's own approach,
per `CSL.md`'s "10 CPU adapters" list) or a codegen fix.

**2.3 What already has generic schema/grammar support** — two pleasant surprises that change
the roadmap's shape:

- `EffectDefinition.domain` (`catalog_types.hpp:102`) is a plain `std::string`, but
  `registry.cpp:857-858` already validates it against a **fixed allow-list**: `{"image",
  "volume-generator", "volume-filter", "volume-renderer", "loop-begin", "loop-end"}`. The data
  model already has room for every family D/C domain.
- `dsl/compiler.cpp:517-533` already enforces the chain-ordering grammar for all five of those
  domains generically: a `volume-generator` must open a chain (unless `iterated && has_volume`,
  the exact carve-out `synth3d/cellularAutomata3d`/`reactionDiffusion3d` need);
  `volume-filter`/`volume-renderer` require a volume already present; `loop-begin` requires a
  current image and refuses to nest; `loop-end` requires an open loop. **None of this DSL-level
  grammar needs to change for families C or D** — the gap for those two families is purely (a)
  registering the 16+2 EffectDefinitions with real typed GLSL kernels, and (b) teaching
  `GraphExecutor::execute` to actually thread a volume/geometry bundle and run a loop region,
  neither of which the compiler blocks today.
- By contrast, **family E (particle groups) has no compiler-level or schema-level scaffolding
  at all** — `global_xyz`, `particle`, and `pointsEmit` do not appear anywhere in
  `dsl/compiler.cpp` or `executor.cpp`. `EffectDefinition.iterated`
  (`catalog_types.hpp:115`) is read only for the volume-generator chain-position carve-out
  above; there is no equivalent of `computeIterationGroups`' particle-joining logic anywhere in
  cpp. Porting family E therefore requires **new DSL/compiler logic**, not just new
  executor/codegen work — a materially bigger lift than families C/D's "grammar already exists,
  executor doesn't act on it yet" position. (Confirm against the family E deep-dive below.)

**2.4 Scatter-adapter registry: the one piece of family-crossing work already half-done.**
`include/noisemaker/effects/scatter/{registry.hpp,catalog.hpp,wormhole.hpp}` +
`src/effects/scatter/{registry.cpp,catalog.cpp,wormhole.cpp}` mirror JS's
`scatter-registry.js` 1:1: a `ScatterAdapter` function-pointer map keyed by
`"${effectId}:${program}"`, an idempotent `register_builtin_scatter_adapters()` aggregator
(`catalog.cpp`, 24 lines total) whose only registered adapter today is `wormhole::
register_adapter()` — its own source comment names the exact six future call sites:
`dla::register_adapter(); lenia::register_adapter(); physarum::register_adapter();
points_render::register_adapter(); points_billboard_render::register_adapter();
flow3d::register_adapter();`. `wormhole.cpp` (175 lines) is a **complete, independently
verified, bit-exact port** — see `docs/port-engineering/wormhole/wormhole-report.md` for its
JS-golden-oracle-plus-mutation-testing methodology (62 cases, 9 mutations, 36,228 lanes
compared, max abs diff 0) and the real JS-quirk bug it caught (`wrapMirror`'s `value ≡ -1 (mod
2·size)` off-by-one, which JS silently no-ops as an out-of-range `TypedArray` write and C++ must
reproduce via flat-offset bounds-checking, never per-axis clamping). **What's missing is purely
the executor-side dispatch branch**: `GraphExecutor::execute`'s per-pass loop
(`executor.cpp:1980-2089`) always does `bind_factory_route` + `run_pass`; it has no branch that
checks `admission.status == AvailabilityStatus::scatter` and calls `resolve_scatter_adapter()`
instead, and `validate_plan_before_allocation` refuses every scatter-status pass
unconditionally rather than conditionally on whether an adapter is registered for that specific
program key. This is the single smallest, most template-able piece of net-new executor
machinery in the entire 46-effect backlog, and it directly gates 6 of family E's effects plus
`filter3d/flow3d` (also family E) — see §4's landing-order recommendation.

## 3. Per-family deep dives

_This section is populated from four independent research passes, one per family group,
each citing file:line against the same two trees. Family C is folded into family B's report
because both are driven by the same JS iteration-group primitive._

### 3.1 Family A — filter/fibers, filter/scratches, filter/strayHair, filter/snow, synth/testPattern, filter/text, synth/media, filter/wormhole

#### 3.1.1 Exact JS runtime semantics

**fibers/scratches/strayHair (the worm-overlay trio).** All three are `kind: "mixer"` with a
single `blend` pass (inputs `inputTex`+`overlayTex`), and the only declared texture is
`overlayTex` (`width/height:"screen"`, `format:"rgba8"`), which no pass produces
(`upstream-snapshot.js`: fibers 5710-5768, scratches 9774-9832, strayHair 10868-10926). Because
nothing produces it, the authority's declared-but-unproduced-texture path fills it via
`renderCanonicalWormOverlay(effectId,width,height,params)`
(`src/effects/cpu/worm-overlay.js:124-181`) — one seeded-RNG worm-tracing algorithm shared by
all three, parameterized per effect id. Components: `SeededRng` (lines 5-25, a 32-bit PCG-style
hash with `.float()`/`.normal()` via Box-Muller using plain float64 `Math.log`/`Math.sqrt`/
`Math.cos` — **no `Math.fround` guards anywhere in this file**, unlike wormhole.js/snow.js);
`valueNoiseField` (27-52, a small bilinearly-smoothed `Float32Array` lattice); `trace` (89-122,
spawns `count = max(1, floor(maxDimension*density))` worms with per-worm stride/rotation,
steps each `iterations = max(1, floor(sqrt(minDimension)*duration))` times, angle from a
flow-field lookup plus rotation, alpha modulated by a triangular exposure ramp);
`drawSegment` (54-87, capsule-rasterizing line blitter with closest-point projection,
`Math.hypot` distance, "over" alpha compositing). Final quantization rounds the whole surface
to 8-bit once, at the end (line 179), not per draw call. Per-effect parameters differ only in
worm count/density/kink/duration/behavior/color (fibers: 4 chaotic pastel layers; scratches: 4
alternating-behavior white layers; strayHair: 1 sparse near-black layer) — cite
`worm-overlay.js:128-178` for exact constants. Bit-exactness risk: this is a "reproduce V8's
float64 transcendentals" problem (harder than wormhole's float32-rounded case), and no oracle
for this algorithm exists anywhere in the checkout today.

**filter/snow.** Single `main` pass, program `snow` (`upstream-snapshot.js:10287-10340`),
`"status":"compatible"` in `backend_compatibility.json` — the *generated* kernel type-checks
fine. But the authority never runs it: `src/effects/adapters/snow.js`'s `snowFactory` is
registered in `canonicalAdapterFactories['filter/snow:snow']`
(`src/effects/adapters/index.js:9,21`) and **always overrides** the generated kernel. The
adapter (fully `Math.fround`-guarded) computes two independent 3D hash-noise samples via a
`snowHash` dot-product/fract construction, mixes them through a `pow(limiterValue,
(1-density)/density)`-shaped mask (`snow.js:76-83`). `docs/CSL.md:91` confirms snow is one of the
JS authority's fixed 10-CPU-adapter set. This is exactly `kMeasuredParityExclusions`'
`filter/snow:snow` case (`executor.cpp:744-747`): the generated kernel isn't buggy, it's simply
the *wrong ground truth* — JS itself never executes it.

**synth/testPattern.** Single `main` pass, pure generator, no inputs
(`upstream-snapshot.js:24727-24774). Unlike snow, testPattern has **no** entry in
`canonicalAdapterFactories` — confirmed absent from all 12 keys. So here the ordinary generated
kernel *is* the authority's real ground truth, and cpp's own typed-kernel emission has a genuine
boundary-condition bug (divergent at 2 grid-boundary pixels / 6 of 748 RGBA8 bytes at 17×11,
`executor.cpp:748-750`) — a different bug class from snow despite both being caught by the same
guard.

**filter/text.** `kind:"mixer"`, one pass named `"overlay"` (unrelated to worm-overlay — just a
composite-text-over-input naming convention), inputs `inputTex`+`textTex`,
`externalTexture:"textTex"` (`upstream-snapshot.js:11683-11701`). JS's own CLI states the intent:
"the image is also bound as imageTex/textTex for filters that sample the host texture
(filter/text, synth/media)" (`bin/noisemaker-cpu.js:229-232`); `--input` binds the *same* decoded
PNG to both names (`loadExternalTextures`, lines 203-219, specifically 207-209).

**synth/media.** `kind:"generator"`, one `main` pass, `externalTexture:"imageTex"`
(`upstream-snapshot.js:19838-19967`). Pure "host must supply an external texture" — no JS-side
generation at all beyond the generated `mediaInput` kernel's own placement math
(`bgColor`/`position`/`tiling`/`flip`/`scaleAmt`/`rotation`), which is already `"compatible"`.

**filter/wormhole.** Three passes (`upstream-snapshot.js:12691-12733`): `clear` (zeroes
`wormhole_accum`, a real `rgba16f` half-float atlas, not 8-bit), `deposit` (`drawMode:"points"`,
`count:"input"`, `blend:true` — the scatter pass, ground truth `runWormholeDeposit` at
`src/effects/cpu/wormhole.js:34-76`), `blend` (composites `wormhole_accum` back over `inputTex`).
The deposit algorithm is **already ported and bit-exact-verified in cpp**
(`src/effects/scatter/wormhole.cpp:100-171`) per `docs/port-engineering/wormhole/
wormhole-report.md` — every op through `Math.fround`/`f32r()` exactly once in JS's own position;
Oklab-luminance weighting; bottom-up vertex row addressing; a genuine JS algorithm quirk
(`wrapMirror` returns exactly `-1` for `value ≡ -1 mod 2·size`, which JS's `Float32Array` write
silently no-ops, reproduced in C++ via flat-offset bounds-checking, not per-axis clamping,
`wormhole.cpp:156-161`); and an explicitly-flagged, not fully closable, transcendental
cross-platform risk (V8 vs. Apple libm `cos`/`sin`/`pow` have no bit-identity guarantee; verified
empirically bit-exact for 36,228 lanes on Apple clang/arm64 only).

#### 3.1.2 What cpp currently does, and the precise gap

`is_worm_overlay_resource(effect_id, texture)` (`executor.cpp:215-220`) is a **closed,
exact 3-effect/1-texture-name allowlist** (`overlayTex` for fibers/scratches/strayHair only),
consulted at two throw sites (`executor.cpp:867-876` in validation, `1916-1934` in `execute()`)
that both fail closed with "declared texture requires the canonical CPU worm-overlay adapter"
rather than guessing a zero-fill. Zero lines of the actual algorithm exist anywhere in the tree.
`authenticate_measured_parity` (`executor.cpp:753-761`) refuses snow/testPattern identically
regardless of their different root causes (called from `executor.cpp:893` and `1528`). Text and
media have no guard at all blocking them — the runtime plumbing (`ExecutionInputs::
external_textures`, already copied into the arena at `executor.cpp:1869`; `decode_png` already
in `png.hpp:32`) is complete end-to-end, but **no code path ever populates it from a file**:
`noisemaker_render.cpp`'s entire flag set (`--help/--list-effects/-o/--width/--height/--time/
--frame/--seed/--raw-rgba8/--metadata`, lines 264-333) has no `--input`/`--texture`. Wormhole's
`deposit` is refused unconditionally by both blanket-scatter throw sites
(`executor.cpp:781-787,1011-1014`, "scatter is not enabled in Task 6") **despite the adapter
already being registered** (`scatter/wormhole.cpp:173`, aggregated by `scatter/catalog.cpp:14`)
and already recorded as `"scatter"`/adapter-known in `backend_compatibility.json`'s own scatter
metadata block (~line 87704-87734). The gap is purely that neither throw site checks whether
`resolve_scatter_adapter(program_key)` actually resolves before refusing.

#### 3.1.3 GLSL programs needing admission vs. hand-written C++

**Zero new GLSL programs need typed-corpus admission** — every Family A program key
(`fibersBlend`, `scratchesBlend`, `strayHairBlend`, `snow:snow`, `testPattern:testPattern`,
`text:text`, `media:mediaInput`, `wormhole:clear`, `wormhole:blend`) is already
`"compatible"`, and `wormhole:deposit` is already `"scatter"` — none is `"missing"`. What needs
hand-written C++: (1) the shared worm-overlay generator algorithm; (2) the executor's
scatter-dispatch branch plus making the two blanket refusals conditional on adapter
availability (wormhole's own adapter is otherwise complete); (3) a ported `snow.js` hand
adapter (matches the JS authority's own approach); (4) a boundary-condition **bug fix** in cpp's
existing typed-kernel emission for testPattern (not a port); (5) CLI-only plumbing for text/media
(no new algorithm). Crucially, `check_corpus.py`'s fixed manifest (`212` programs / `167`
effects / `(212,211,1)` pass/keyed/override triple, lines 119-120,167-168,191-195) **already
permanently encodes `filter/wormhole:deposit` as the corpus's one scatter override** — the
validator explicitly looks up `effects["filter/wormhole"]["passes"][1]` and requires
`program=="deposit", key is None, drawMode=="points"` before accepting `overrides=1`. Landing
all of Family A moves none of these numbers.

#### 3.1.4 Cross-family shared infrastructure

The scatter-dispatch executor branch wormhole needs **is the same infrastructure** Family E's
`points/dla`, `points/lenia`, `points/physarum`, `render/pointsRender`,
`render/pointsBillboardRender`, and `filter3d/flow3d` need — `scatter/catalog.cpp`'s own
comment (lines 15-18) names exactly those six as the remaining call sites, and
`scatter/registry.hpp`'s header states the design goal outright: mirror the JS contract 1:1 so
those six "need no new machinery when they're ported." But Family E's six programs start from a
strictly harder position than wormhole: their agent/deposit kernels are `"missing"`
(no GLSL kernel at all), not merely dispatch-blocked — wormhole is dispatch-only-blocked, with
an already-oracle-verified adapter. **Recommendation: land wormhole's scatter-wiring first.**
It is the smallest possible instance of the shared branch, touches only the two existing
blanket-refusal call sites, and proves the real dispatch branch against the live multi-pass
`execute()` driver before Family E has to extend it under harder conditions (missing kernels,
and per the task brief, MRT for the "agent" passes — this MRT dependency was **not**
independently confirmed by this pass and should be checked against family E's own report).

#### 3.1.5 Risks

Worm-overlay's float64-transcendental dependency (no `Math.fround` guards at all in that file)
is a harder bit-exactness target than wormhole's float32-rounded case, with no existing oracle
to build from. The snow/testPattern guard conflates two different bug classes under one
mechanism — treating them the same (e.g. "fix the generated snow kernel until it matches") would
misdirect effort on snow, where the generated kernel is simply the wrong ground truth. Two
**independent, easy-to-miss kit-visibility gaps**, both of the same shape as the already-known
`synth/media` exclusion in `generate-compat.mjs`: (1) that script's `effects.delete('synth/media')`
(line ~32) is a hardcoded literal, not read from any executor guard, so it will keep excluding
media from the kit until someone edits the generator script itself, even after CLI support
ships; (2) `generate-compat.mjs`'s admission test is a literal `status === 'compatible'` string
check (line ~28) — so even after the scatter-dispatch branch lands and wormhole renders
correctly, `filter/wormhole`'s backend status will still read `"scatter"` (a corpus-classification
label, not an adapter-registration flag) and the effect will *still* be silently omitted from
`compat-effects.json` unless that admission rule is separately revisited to admit a `"scatter"`
status when a resolvable adapter exists. Both should be tracked as explicit follow-ups distinct
from the runtime port itself. Finally, `wormhole-report.md`'s transcendental cross-platform
caveat (Apple-clang/arm64-only empirical verification) becomes more load-bearing once the
adapter runs in a real production dispatch path rather than a standalone harness.



### 3.2 Family B (iterated feedback) + Family C (loop region) — 10 effects

Combined because both ride the same JS iteration-group primitive, and the sub-agent's own
reading proves (§3.2.4) that C and Family E's particle groups are, at the JS-authority level,
literally the same mechanism with a different name-matching predicate.

#### 3.2.1 Exact JS runtime semantics

**Scheduler internals, re-verified independently**: `computeIterationGroups`
(`iteration.js:57-105`) enforces the loop-region invariants (nested `loopBegin`, unmatched
markers, read/write crossing a loop boundary — all throw, lines 70-71,84,102) at *runtime*;
`filter/convolutionFeedback`'s `PARTICLE_STATE_PATTERN` (`global_ca_state`,
`global_mnca_state`, `global_rd_state`, `global_ns_velocity`/`_pressure`/`_smoothed`) does
**not** match the particle regex despite the `global_` prefix — confirmed by direct string
comparison — so these stay ordinary per-step scratch, never routed through `groupResources`.
Only `global_accum` is special-cased by *literal name equality*, not the regex.

**`render/loopBegin`+`render/loopEnd`+`global_accum` traced exactly** (previously
undetermined by the orchestrator, now resolved): `render/loopBegin`
(`upstream-snapshot.js:15960-16013`, `domain:"loop-begin"`, `loopRole:"begin"`,
`iterated:true`, params `alpha`/`intensity`/`iterationCount`) has one pass `accumBlend`
(`inputs:{inputTex:"inputTex", accumTex:"global_accum"}`, program `loopBegin`) and declares
**no textures of its own** — `global_accum` is supplied entirely by the group scheduler.
`render/loopEnd` (`upstream-snapshot.js:16015-16053`, `domain:"loop-end"`, `loopRole:"end"`,
**no `iterated` key at all** — confirmed absent from all 25 `"iterated":true` hits in the
snapshot) has two passes both running program `"copy"` (a trivial `texture(inputTex,uv)`
passthrough, `canonicalFactory233`): `feedback` (`inputTex→global_accum`) and `output`
(`inputTex→outputTex`). The `loopBegin` kernel itself (`canonicalFactory232`, read in full) is
the *entire* accumulation formula — `blended = max(inputColor, accum*intensity/100); result =
mix(inputColor, blended, alpha/100)` — and **there is no arithmetic mean, no divide-by-N, and
no dependence on `iterationCount` inside the kernel at all**; `N` only controls how many times
the cycle runs. Because `storeGroupOutput` (`renderer.js:762-765`) special-cases
`name === 'global_accum'` to *replace* (not add into) the surface stored under that name,
`global_accum` after iteration `i` is literally "the loop body's raw output from iteration
`i`," not a running sum — the effect's own `description` string ("accumulator loop") names the
*pattern* (iterated feedback/relaxation), not a literal running total. Only the **final**
iteration's `loopEnd:output` copy becomes the group's returned output; there is no separate
normalization step anywhere.

**Precision — a compounding-quantization risk not previously flagged**: every pass output,
in both group and non-group paths, is narrowed through `quantizeTexture`
(`texture-format.js:43-57`) immediately after being written — for the default `rgba16f`
format this calls `float16Truncate` **per pixel, per pass, every single iteration**, not once
at the end. Since `loopBegin`/`loopEnd` declare no explicit texture format for `outputTex`/
`global_accum`, they inherit the pool default (`rgba16f`), meaning **half-float rounding
compounds every iteration** of a loop region or Family B feedback effect; the Family B effects
with an explicit `format:"rgba8unorm"` scratch texture (`_selfTex`, `_cfSharpened`/
`_cfBlurred`, `_h1..._h8`) are narrowed even harder, every iteration. Any cpp port that
narrows at a different point in the pipeline, or with different rounding
(`float16Truncate`'s round-toward-zero is a deliberate WebGL-attachment match, not
round-to-nearest), risks a real cumulative divergence, not just a per-pass one.

**Family B, effect by effect** (all read in full from `upstream-snapshot.js`; all declare
`iterated:true` + `iterationCount` default 60 unless noted):

- **`filter/convolutionFeedback`** (4717-4826): 3 passes (`sharpen`→`cfSharpen`,
  `blur`→`cfBlur`, `blend`→`cfBlend`). **This is the only Family B/C effect whose pass-input
  value is the literal reserved string `"selfTex"`** (`inputs:{inputTex:"selfTex"}` on the
  `sharpen` pass) — confirmed by direct grep; every other effect below only *looks* similar.
- **`filter/feedback`** (5544-5708): 2 passes, `main` (`inputs:{inputTex, selfTex:"_selfTex"}`
  — note the **uniform key** is named `selfTex` but the **resource value** is the ordinary name
  `_selfTex`, not the literal token) and `feedback` (`program:"copy"`, `outputTex→_selfTex`).
  **This does NOT trigger the reserved-token mechanism at all** — its persistence is the
  *ordinary* named-scratch-texture idiom (`_selfTex` persists purely because `state.resources`
  is built once and never recreated across iterations). Any cpp implementation that
  special-cases only the literal `"selfTex"`/`"feedback"` token values will silently miss this
  effect's real persistence mechanism.
- **`filter/motionBlur`** (7651-7717): structurally identical `_selfTex`-not-literal-token
  pattern to `filter/feedback`.
- **`filter/temporalAberration`** (11026-11213): **9 literal pass records, not
  `pass.repeat`** — `main` plus 8 `shiftN` passes forming a shift register
  (`_h1..._h8`), and **all 8 shift passes share one program_key**, `delayShift` — confirmed by
  direct grep, resolving the task brief's ambiguity exactly.
- **`synth/cellularAutomata`** (18952-19102): 2 passes, `update` (program `caFb`, reads
  *and* writes `global_ca_state` in the same pass) and `render` (program `ca`). Despite the
  `global_` prefix, `global_ca_state` does **not** match `PARTICLE_STATE_PATTERN` — ordinary
  scratch, zero-seeded once by `ensureGroupScratchResources`'s special case for read-and-write
  in one pass.
- **`synth/mnca`** (19970-20179): near-structural-clone of cellularAutomata (`update`→`mncaFb`,
  `render`→`mnca`, `global_mnca_state`).
- **`synth/navierStokes`** (20326-20544): **7 literal passes**, all distinct program keys
  (`nsSplat`,`nsAdvect`,`nsDivergence`,`nsPressure`,`nsGradient`,`nsSmooth`,`ns`). The
  `pressure` pass alone carries `"repeat":"iterations"` (a *string* naming a uniform, default
  30, range 4-40). **Exact cost arithmetic, verified against the actual param defaults**: one
  outer iteration = 6 fixed passes + 30 `pressure` repeats = 36 pass executions; × `N=60`
  outer iterations = **2,160 total pass executions per frame at every default value** — this
  precisely reproduces EFFECTS.md's cited figure via independent arithmetic on two
  independently-verified numbers, not by trusting the doc's own claim. The `nsPressure` kernel
  itself (`canonicalFactory269`, read in full) is an ordinary 5-point Jacobi stencil — ordinary
  per-pixel math, no cross-pass state beyond what the executor already threads.
- **`synth/reactionDiffusion`** (21218-21434): 2 passes, `simulate` (program `rdFb`,
  **also** carries `"repeat":"iterations"`, default 8, range 1-32) and `render` (program
  `rd`). **A second, previously-unflagged cost trap of the identical shape as navierStokes,
  just smaller**: `(8+1) × 60 = 540` pass executions per frame at defaults — not mentioned by
  name in EFFECTS.md's cost paragraph, but the same repeat-inside-iterationCount
  multiplication applies. `cellularAutomata`/`mnca` have **no** hidden repeat on either pass —
  their cost is a flat `2×iterationCount` (120 passes/frame), not multiplicative.

#### 3.2.2 What cpp currently does, and the precise gap

**Catalog data is fully present and correctly populated — this refutes any assumption that
Family B/C are simply absent from cpp.** `effect_catalog.cpp` already contains complete
`EffectDefinition` records for all ten effects, with the *typed* fields actually set (not
just mirrored in a `.raw` JSON blob): `render/loopBegin`'s `make_effect_164()` sets
`e.loop_role = std::string("begin");` and `e.iterated = true;`; `render/loopEnd`'s
`make_effect_165()` sets `e.loop_role = std::string("end");` and correctly has **no**
`e.iterated = true;` line, matching JS's own omission. All eight Family B effects have
`e.iterated = true;` set. **Exact count match, verified**: `grep -c "e.iterated = true;"
effect_catalog.cpp` → 25; `grep -c '"iterated": true'` on `upstream-snapshot.js` → 25.
`grep -c "e.loop_role"` in cpp → 2, matching JS's two `loopRole` keys. **The generator
pipeline is faithful for these fields across the whole catalog, not just B/C** — this is not
a data-model gap.

**Executor: strictly single-pass-per-step, zero iteration concept** — re-confirmed
independently (`grep -n "iterated\|loop_role\|particle\|global_xyz"` on `executor.cpp`: zero
matches). **`pass_repeat()` (`executor.cpp:362-389`) already exists and already works** —
it resolves numeric or named-uniform `pass.repeat` exactly like JS's `resolveRepeatCount`, and
is exactly the mechanism navierStokes's `pressure`/reactionDiffusion's `simulate` need for
their *inner* repeat — but this is a same-iteration, same-call repeat, orthogonal to the
*outer* `iterationCount`-driven whole-step-graph loop B/C need. No changes to `pass_repeat`
should be necessary; it composes correctly once an outer loop calls each iteration's passes
through the existing per-pass path. `validate_plan_before_allocation` unconditionally requires
`AvailabilityStatus::compatible` for every pass — meaning even once an outer scheduler exists,
every B/C chain still hard-fails today because all 24 unique programs (§3.2.3) are
`missing_backend_program`: **the executor-scheduler gap and the GLSL-corpus gap are
independent blockers that both need closing.**

**DSL compiler: loop grammar already implemented and correct**, independently re-confirmed —
`compiler.cpp`'s chain-compilation loop tracks `open_loop` per chain and enforces
current-image/nesting/unmatched-marker/write-crosses-boundary rules at compile time,
duplicating (compiler-side rather than runtime-side) the exact invariants JS's
`computeIterationGroups` enforces. A `loopBegin()...loopEnd()` chain **compiles cleanly
today** — it only fails later, at `validate_plan_before_allocation`, because nothing backs
the passes. **cpp has two working gates around a hole, not a missing gate.**

#### 3.2.3 GLSL programs needing admission vs. hand-written C++

Querying `backend_compatibility.json` directly for all ten ids gives **32 pass rows, all
`"status":"missing"`, resolving to exactly 24 unique `program_key` values** (not "~27" —
verified exact count): convolutionFeedback 3/3, feedback 2/2, motionBlur 2/2,
temporalAberration 9 rows/**2** keys (8 shifts collapse onto `delayShift`), cellularAutomata
2/2, mnca 2/2, navierStokes 7/7, reactionDiffusion 2/2, loopBegin 1/1, loopEnd 2 rows/**1** key
(both passes collapse onto `copy`). Sampling the actual kernel bodies from
`canonical-kernels.js` (no standalone `.frag`/`.glsl` files exist for these effects in this
checkout — confirmed by exhaustive `find`) shows **all 24 are ordinary, self-contained
per-pixel fragment kernels**: trivial passthroughs (`copy`, `delayShift`), a 5-point Jacobi
pressure stencil (`nsPressure`), a variable-radius (uniform-bounded, not compile-time-constant)
unsharp-mask loop (`cfSharpen` — the same pattern already solved elsewhere in the 212-program
corpus for ordinary blur/median effects, not a new problem class), a fixed 3×3 Gray-Scott
Laplacian (`rdFb`), and a trivial max/mix blend (`loopBegin`). **Zero hand-written C++ adapters
are needed for Family B/C** — the complexity is 100% in orchestration/scheduling, not
per-pixel kernel logic, confirming the task's own hypothesis. None of the ten effects use
`drawMode:"points"`/`"billboards"`; nothing resembles wormhole's scatter case.

`check_corpus.py`'s four size gates are **hardcoded literals**, not manifest-derived —
independently re-confirmed by reading the validator: `len(programs)!=212` (line 119-120),
`len(sources)!=212` (156), `len(effects)!=167` (167-168), `(pass_count,keyed,overrides)!=
(212,211,1)` (194). Landing the 24 new programs + 10 new effects requires manually bumping
all four (to at least 236 programs/sources, 177 effects — the exact new pass_count/keyed
delta needs separate re-derivation, since the manifest's per-pass `"key"` concept is distinct
from `program_key` and was not independently re-derived by this pass — **UNVERIFIED beyond
"it changes and must be hand-updated"**). This is a real landing-order hazard: landing the
programs without updating `check_corpus.py` fails CI with a "gate drift" error that reads like
a corpus-integrity bug, not a stale magic number.

#### 3.2.4 Cross-family shared infrastructure — the central finding

**Nothing in `GraphExecutor::execute()` today can run a step's pass list more than once per
render call.** This requires a genuinely new executor primitive that families D (its iterated
volume generators) and E (particle groups) also need. Reading `storeGroupOutput`
(`renderer.js:762-765`) closely is decisive:
```js
storeGroupOutput(name, surface, state, groupResources, surfaces, owned) {
  if (isParticleStateName(name) || name === 'global_accum') this.replaceCanonicalResource(name, surface, groupResources, surfaces, owned)
  else this.replaceCanonicalResource(name, surface, state.resources, surfaces, owned)
}
```
Family E's particle-state names and Family C's `global_accum` are handled by **the exact same
branch, into the exact same `groupResources` map**, differing only in the name-matching
predicate — at the JS-authority level these are **provably the same primitive**: a named
surface shared across every step in the group for the whole N-iteration run, *replaced* (not
mutated) on each write, read back by name on a later pass/iteration, and released at group end
unless part of the final output — unconditionally, regardless of naming convention (comment,
`renderer.js:836`: "particle state never survives beyond the group run that owns it").

But most of Family B (`feedback`,`motionBlur`,`temporalAberration`'s `_hN`,
`cellularAutomata`'s/`mnca`'s/`reactionDiffusion`'s `global_*_state`) does **not** use this
group-shared primitive at all — none of these names match the particle pattern or
`global_accum`, so `storeGroupOutput` routes them to `state.resources`, the **per-step** (not
per-group) map, persisting purely because `initializeGroupStepState` builds it once and
`runGroupStepIterationSync` never recreates it. This is a materially simpler, different
primitive (scoped to one step, no cross-step sharing, no name predicate). A third, narrowest
idiom exists purely for `convolutionFeedback`: the reserved `selfTex`/`feedback` token
triggers a dedicated surface, allocated once, **never stored under its own name** in the
ordinary route table, updated by **memcpy** (not reference-swap) at the end of every
iteration — a copy-semantics guarantee, not a naming convention, needed by exactly one effect
in the whole catalog.

**Recommendation: cpp needs three layered pieces, not one monolith.** (1) Group-scoped
shared resources (for `global_accum` + particle names) — one map, replace-not-mutate writes,
released at group end unless retained. (2) Step-scoped persistent resources (everything
else) — a per-step map built once, never recreated across iterations; the executor's existing
per-step binding code needs only to stop being rebuilt every iteration, no new logic. (3) The
`selfTex`/`feedback` reserved-token surface — special-cased narrowly, needed by exactly one
effect. Suggested shape: a new `GraphExecutor::run_iteration_group(...)` that resolves `N`
(defensive 60 fallback), short-circuits `N==0` to a clone/zero path, allocates shared+per-step
resource maps once, then loops `i` in `[0,N)` re-running every step's *existing, unmodified*
single-pass execution path (including its already-working `pass_repeat()` calls) with
`frame=i, delta_time=1/600, time=wrap01(...)`, resetting the nominal chain input to the
group's original frozen input at the top of every iteration (mirroring `renderer.js:879`),
and releasing everything not retained in the final output.

**Recommended landing order** (independently derived by this analysis): (1) the step-scoped
persistent-resource piece first — needed by 6 of Family B's 8 effects, no new
`ResourceArena` lifetime category, a strict subset of everything else. (2) the outer
N-iteration loop driver next, wired to the existing single-pass path unchanged — this
unblocks the remaining two selfTex-needing effects (add that narrow special case here) and is
*also* the exact loop Family D's iterated volume generators need, nothing more. (3) the
group-shared resource map last, generically, with `global_accum` and particle-state support
as two thin call sites of one map — land Family C and Family E's particle-group support
essentially together, since the JS authority treats them as one mechanism; Family C is the
cheaper first real exercise (no scatter/points draw mode, no agent-count param, just one blend
kernel + two copies, and only 2 unique GLSL programs vs. Family B's 22) before Family E adds
scatter-adapter complexity on top.

#### 3.2.5 Risks

**navierStokes's cost trap is now exactly quantified** (2,160 passes/frame at every default
value, arithmetic shown above, matching EFFECTS.md verbatim) **and reactionDiffusion has an
identically-shaped, previously-unflagged cost trap at smaller scale** (540 passes/frame).
Recommend excluding both by name (not just by family) from casual smoke-test sweeps, and
considering lower `iterationCount`/`iterations` defaults for automated correctness-only test
runs. **`ResourceArena`'s design assumptions do not currently support what an iteration group
needs, and this is a deliberate design gap, not an incidental one**: `ResourceLifetime` has no
category for "persists across N re-executions of a subgraph, never published to a name any
other step could bind by mistake," and the existing `ScopedPin`/`pin`/`unpin` machinery is
explicitly documented as scoped to *one effect's execution scope* — an iteration group needs
retention spanning the entire outer loop across every step and every iteration, a materially
larger lifetime unit than anything the arena expresses today; retrofitting this by convention
(manual re-pinning) risks exactly the use-after-retire bugs the arena's aggressive
retire-on-zero-reference policy is designed to catch. **This should be scoped as its own small
design task before or alongside the step-scoped-map work**, not discovered mid-implementation.
`selfTex`/`feedback` zero-on-iteration-0 semantics are narrow and effect-specific — only
`convolutionFeedback` uses the literal token; `feedback`/`motionBlur` merely *look* similar
(same pass-pair shape) but use the ordinary step-scoped path — a cpp port that pattern-matches
on "looks like feedback" rather than the literal input value will build the wrong mechanism for
2 of the 3 effects that appear to need it. **The pixel-correctness acceptance bar is
explicitly looser than a GPU golden, and is good news worth stating explicitly**: all 8 Family
B effects are inside the JS authority's own permanent 21-effect `cpu-divergent`-skip set
(EFFECTS.md line 70, confirmed by name-matching all 8 against that list) — cpp's target for
them is "match the JS CPU authority," never "match a GPU golden." `render/loopBegin`/
`render/loopEnd` are looser still: they appear in `scripts/parity/run.js`'s `NEW_CPU_EFFECT_IDS`
set (the JS authority's own "no pinned GPU golden yet, fixtures compile but aren't pixel-diffed"
bucket) — meaning the JS authority itself has **no pinned reference of any kind** for the
loop-region pattern; cpp's own future fixtures for `loopBegin`/`loopEnd` would be the *first*
pinned pixel reference of any kind for this pattern anywhere in the project.



### 3.3 Family D — volumes/3D (16 effects: 14 core + `synth3d/heightmap3d` + `render/renderLandscape3d`)

**Headline correction to the task brief's own framing, established by direct reading, not
assumption**: two of the sixteen named members are *not* volume-domain effects at all, and
eleven of the remaining fourteen are MRT (two-output) passes, not ordinary single-output
fragment passes. This changes the shape of the family substantially from "14+2 uniform volume
effects" to "2 plain-image effects + 14 real volume effects, 11 of which also need MRT that has
**zero precedent anywhere in the current 211/304-program corpus**."

#### 3.3.1 Exact JS runtime semantics

**Two members never touch the bundle at all.** `classicNoisedeck/noise3d`
(`upstream-snapshot.js:2581-2691`) and `classicNoisedeck/shapes3d`
(`upstream-snapshot.js:3314-3343`) both declare `"domain": "image"`, each a single ordinary
fragment pass that does its whole raymarch inside the kernel and never declares `outputTex3d`/
`outputGeo`. They never participate in `inheritVolumeSize`/`bundleOutput`/any of the four
volume-dispatch blocks (which all gate on `domain ∈ {volume-generator,volume-filter,
volume-renderer}`, `renderer.js:110,1047,1181,1316,1462`). Their "Family D" membership is
topical (3D-looking output), not architectural — they need only an admitted kernel, nothing
from the bundle-threading work.

**Bundle threading and N×N² atlas** (the other 14 real volume-domain members):
`isChainBundle`/`chainBundle` (`renderer.js:97-105`) wrap chain values as
`{image,volume,geometry,volumeSize}`. `inheritVolumeSize` (`renderer.js:107-115`) is the exact
N×N² mechanism: an inbound volume atlas's `.width` becomes the effective `volumeSize`
*unconditionally*, overriding both param default and explicit value
(`params.volumeSize === volumeSize ? params : {...params, volumeSize}`), only for the three
volume domains, and validates `volume.height === volumeSize**2` at the boundary. The same
shape assertion repeats at the output boundary in all four near-identical volume-dispatch
blocks (`renderer.js:1040-1075` read in full, duplicated 1174-1208/1310-1345/1456-1491):
`volumeSize = domain==='volume-generator' ? (params.volumeSize ?? volume?.width ?? null) :
(inputBundle.volumeSize ?? params.volumeSize ?? volume?.width ?? null)`; `volume-renderer` is
explicitly exempted both from "must produce a volume" and from the width/height re-check
(only generator/filter get re-validated, since a renderer's `outputTex3d` is a passthrough).

**Geometry-channel preservation, confirmed exactly**: `bundleOutput(name,input,resources)`
(`renderer.js:118-124`) returns `input` unchanged when `name` is falsy or the literal string
`"inputGeo"`, else re-resolves from `resources.get(name)`. Concrete Family D instances:
`filter3d/palette3d` declares `"outputGeo":"inputGeo"` (pure passthrough); every
`volume-generator` in the family declares `"outputGeo":"geoBuffer"` (fresh geometry, since
generators start chains); every `volume-renderer` declares `"outputGeo":"screenGeoBuffer"` — a
**shape change**, not just content: pre-render geometry means a volume atlas (N×N²),
post-render it means an ordinary screen-shaped 2D G-buffer, and nothing in the runtime
enforces or announces this reinterpretation — it must be known by convention.

**Volume-renderer "conversion back to image" — the actual mechanism**: contrary to a literal
reading of EFFECTS.md's "converts the bundle back to the ordinary image channel," the volume
field is **not** cleared by the renderer. All `volume-renderer` members declare
`"outputTex3d":"inputTex3d"` — a passthrough — so the *bundle* a renderer step returns still
literally carries the stale volume forward. The real conversion happens only at the
chain-terminal `write(oN)` call, which has always only ever read `.image` off a bundle
(`renderer.js:1633,1665`) — i.e. "nothing downstream of a renderer's `.write()` ever sees a
volume again" is true in effect, but the mechanism is "the sink only reads `.image`," not "the
renderer nulls the volume field."

**Cubemap face handling — determined, not merely absent**: `render/renderCubemap3d` and
`render/renderCubemapSurface` (`upstream-snapshot.js:18147-18251,18251-18355`, read in full)
have pass records **structurally identical** to non-cubemap `render3d`/`renderLit3d`: one pass,
`drawBuffers:2`, no `repeat:6`, no per-face `viewport` array, no six literal pass records —
just a single `cubeBasis` (`mat3`, default identity) uniform. The six faces are resolved
**entirely inside the GLSL fragment kernel** (almost certainly a screen-space tile/cross
layout deriving face + ray direction from pixel position and `cubeBasis`), executed as one
ordinary MRT pass across the full output resolution. Cubemap support therefore adds **no new
pass-graph or executor concept** beyond what `render3d`/`renderLit3d` already need — the
complexity is confined to the kernel body, a pure typed-kernel-authoring problem, not an
executor one.

**`render3d`/`renderLit3d`/`renderLandscape3d` raymarch shape**: all five `volume-renderer`
members share one pass shape — inputs `volumeCache`→`inputTex3d`, `analyticalGeo`→`inputGeo`,
two outputs (`fragColor`→`outputTex`, `geoOut`→`screenGeoBuffer`), `drawBuffers:2`.
`renderLandscape3d` additionally sets `"type":"compute"` — confirmed **dead metadata**: a
repo-wide grep of `src/runtime|dsl|csl` for `pass.type`/`type === 'compute'` returns nothing;
the CPU runtime never branches on it. It appears on exactly 3 pass records total (Family D's
`renderLandscape3d`+`heightmap3d`, plus non-family `points/heightGrid`) and looks like
forward-looking metadata for a future non-CPU backend, not something the CPU executor needs.

**`synth3d/heightmap3d`'s 2D-to-atlas packing**: it takes two `type:"surface"` parameters
(`heightTex`,`tex`, both `default:"none"`) fed as ordinary pass inputs — **not** through the
volume/geometry bundle at all. `type:"surface"` params are a third, independent
resource-resolution path already in `buildBindings` (`renderer.js:271-280`: null→emptySurface,
`{kind:'input'}`→current image, else a named-surface lookup). Its `"precompute"` pass declares
`"type":"compute"` + `drawBuffers:2` + an explicit `viewport` sized to the N×N² atlas — the
actual height→voxel-column packing is entirely inside that kernel's math, using the *same*
`volumeCache`/`geoBuffer` output shape every other `synth3d` generator uses.

**Palette override applicability — resolved precisely, and it changes which effect is
blocked**: of Family D's two `classicNoisedeck` members, **`shapes3d` does declare a `palette`
parameter whose default is `40`** ("silvermane", not `0`/`none`; choices span `none`..
`vintagePhoto`, `upstream-snapshot.js:3512-3595`) — meaning `authenticate_measured_parity`'s
sibling guard, `authenticate_palette_override`, fires **even at unmodified defaults**, not only
on some rare explicit override. **`noise3d` declares no `palette` parameter at all** (confirmed
by reading its full record; its only palette-adjacent field, `colorMode`, is a plain enum) —
so it is entirely unaffected by the `paletteData` dependency, contrary to a grouping that
would treat both `classicNoisedeck` members as equally palette-relevant.

**Iterated-generator special case, `cellularAutomata3d`/`reactionDiffusion3d`**: both declare
`"iterated": true` and two extra typed parameters no other Family D member has: `source:
{type:"volume", default:"vol0"}` and `geoSource: {type:"geometry", default:"geo0"}`. This is
exactly the explicit typed-volume/geometry-parameter case `seedTypedChainResources`
(`renderer.js:785-804`) handles: resolve from the inbound bundle if present, else lazily
allocate and zero-clear a fresh atlas from the effect's own `outputTex3d`/`outputGeo` spec —
precisely EFFECTS.md's "when used at the start of a chain, they receive zeroed seed/geometry
atlases instead" (`docs/EFFECTS.md:62`). Both ride the *exact same* generic iteration-group
machinery every Family B effect does (`step.definition.iterated === true`,
`iteration.js:92,100`) — no Family-D-specific grouping logic exists anywhere.
`reactionDiffusion3d`'s pass additionally sets `"repeat":"iterations"` (a uniform-named repeat,
`renderer.js:169-172`); `cellularAutomata3d`'s does not (its own `iterationCount` param,
`cpuOnly:true`, governs the render-level count instead).

#### 3.3.2 What cpp currently does, and the precise gap

Domain schema (`registry.cpp:857-858`) and DSL chain grammar (`compiler.cpp:513-533`) both
already accept every Family D domain and ordering rule generically (see §2.3) — confirmed by
independent re-reading. **All 16 ids are already present as full `EffectDefinition` records**
in `effect_catalog.cpp` (verified by grep, e.g. `classicNoisedeck/noise3d` with `domain:
"image"` verbatim) — contradicting any assumption that the catalog itself is a blocker.
`catalog_types.hpp`'s `output_tex3d`/`output_geo`/`iterated` and `PassDefinition::viewport`/
`draw_buffers`/`type` are all real, already-populated `std::optional` fields; parsing 11 MRT
passes, 9 viewport-bearing passes, and 2 `"type":"compute"` passes causes no schema error
today. **The gap is entirely in binding and execution:**

1. **MRT is refused at two independent sites**: `validate_pass_output_abi`
   (`executor.cpp:632-641`, `pass.outputs.size() != 1` → `unsupported_mrt`) and
   `validate_pass_controls` (`executor.cpp:1331-1340`, `draw_buffers->number != 1.0` → the same
   code) — every one of the 11 two-output Family D passes hits both.
2. **Any pass-level `viewport`/`count` is refused outright**
   (`validate_ordinary_pass_metadata`, `executor.cpp:615-624`, "ordinary count or viewport is
   unsupported") — 9 of 16 passes declare an explicit `viewport` sized off `volumeSize`/
   `volumeSize**2` and are structurally refused today (6 of these 9 overlap with the MRT list).
3. `admission.dimensionality != "image"` (`executor.cpp:1338`) is real but **not the governing
   blocker in practice** — since none of the 16 programs exist in the compiled corpus yet, every
   Family D pass hits the plain `status != compatible` refusal first. Once admitted with an
   ordinary `dimensionality:"image"` tag this check should pass trivially; MRT/viewport are the
   checks that need real surgery.
4. **The executor threads exactly one resource** — `GraphResource* current`
   (`executor.cpp:1879`) is the *only* state carried between steps; there is no analog anywhere
   of JS's `{image,volume,geometry,volumeSize}` bundle. All 14 real volume-domain effects need
   this before they can run at all, independent of MRT/viewport.
5. **No runtime typed volume/geometry parameter resolution exists at all** — `registry.cpp`
   already type-checks `parameter.type == "volume"|"geometry"` at the DSL/normalize level
   (~line 622), but a grep of `executor.cpp` for `"volume"`/`"geometry"` returns zero hits; only
   `type=="surface"` parameters have a real execution-time resolution path
   (`surface_parameter_for_route`). `cellularAutomata3d`/`reactionDiffusion3d`'s `source`/
   `geoSource` need an entirely new resolution path mirroring `seedTypedChainResources` — not
   wiring, but a path that doesn't exist in any form yet.
6. **No iteration-scheduler runtime exists in cpp at all** (confirmed independently by this
   family's own grep of `executor.cpp` for `iterated|IterationGroup|iteration_count`: only the
   DSL-grammar reference at `compiler.cpp:518`) — `cellularAutomata3d`/`reactionDiffusion3d`
   need this to exist before they can run, on top of the bundle work. This independently
   corroborates family B/C's finding of the same gap.
7. **`shapes3d` additionally hits `authenticate_palette_override`** (`executor.cpp:707-729`)
   out of the box, since its palette default is `40`, not `0` — this fires with **no**
   user-supplied override at all. `noise3d` is entirely unaffected.

#### 3.3.3 GLSL programs needing admission vs. hand-written C++

All 16 are `"status":"missing"` in `backend_compatibility.json` (one pass each,
`missing_backend_program`), confirmed directly, program keys as given in the task brief. The
brief's implicit assumption that these are ordinary single-output kernels is **wrong for 11 of
16**: `render3d`, `renderCubemap3d`, `renderCubemapSurface`, `renderLit3d`, `renderLandscape3d`,
`cell3d`, `flythrough3d`, `fractal3d`, `heightmap3d`, `synth3d/noise3d`, `shape3d` all declare
`"drawBuffers":2` — real MRT kernels needing two `out`/render-target declarations. **A
repo-wide check of the pinned corpus sources for any existing second fragment output found
zero matches** — MRT has no precedent anywhere in the currently-admitted 211/304 programs, so
this is new ground for the GLSL frontend parser *and* the executor, not just "more kernels in
an established pattern." 5 of 16 (`palette3d`, `cellularAutomata3d:simulate`,
`reactionDiffusion3d:simulate`, `noise3d`, and confirm `shapes3d`) are ordinary single-output
kernels. 2 of 16 (`heightmap3d`, `renderLandscape3d`) carry the inert `"type":"compute"` tag
with no dispatch implications. **No effect in the family declares a non-fragment `draw_mode`
or per-face viewport array** — confirming §1's cubemap conclusion: no hand-written C++
scatter/dispatch adapter is needed for the two cubemap effects beyond what every other MRT
volume-renderer needs. None of Family D's 16 program keys appear in cpp's 4-entry hand-adapter
set (`classicNoisedeck/fractal`, `filter/historicPalette`, `filter/palette`, `synth/julia`,
per `check_corpus.py:27-32`'s `_ADAPTERS`) — an absence check only, but it suggests all 16 are
plain typed-GLSL-emitter routes, not hand-CPU-adapter routes. **Net**: the real new C++
engineering here is entirely inside `GraphExecutor` (MRT output handling, viewport-sized
non-screen pass destinations, bundle threading) — not in kernel-authorship style.

#### 3.3.4 Cross-family shared infrastructure and landing order

Bundle threading is a new, `GraphExecutor`-wide mechanic — generalizing the single `current`
pointer to a small `{image,volume,geometry,volumeSize}` struct, populated/consumed only when a
step's domain is volume-flavored. This is architecturally distinct from family B/C's temporal
iteration scheduler (a replay of one pass graph N times) and family E's particle-group
mechanism (no Family D effect declares a particle-state texture) — but `cellularAutomata3d`/
`reactionDiffusion3d` need the **iteration scheduler** in addition to the bundle, since they
are both `iterated:true`.

**Recommended landing order** (as independently derived by this family's own analysis, and
consistent with the top-level recommendation in §4 below): (1) bundle threading in
`GraphExecutor`, validated first against the 14 non-iterated volume effects (this
simultaneously requires lifting the MRT refusal into a real two-output path for 11 of them and
the viewport refusal into non-screen destination sizing for 9 of them); `noise3d`/`shapes3d`
can land independently and earlier in parallel since they need neither bundle nor MRT/viewport
work, only an admitted kernel each (though `shapes3d` still needs `paletteData`). (2)
`cellularAutomata3d`/`reactionDiffusion3d` only after *both* the bundle work *and* family B/C's
iteration scheduler land — they strictly need both, and landing them earlier would mean
re-deriving bundle semantics in isolation only to redo it once the generic mechanism exists.
(3) The `classicNoisedeck` palette override (`paletteData`, 55×16 table) is orthogonal and
should be ported in parallel — it blocks exactly one Family D effect (`shapes3d`, at default
settings) and is pure data plus a `buildBindings`-style uniform-override rule, with no
volume/MRT/iteration dependency.

#### 3.3.5 Risks

**Atlas memory multiplication under iteration**: the `16N³`-byte-per-atlas cost
(`docs/EFFECTS.md:66`) applies with extra force to `cellularAutomata3d`/`reactionDiffusion3d`
(default `volumeSize:32`, `reactionDiffusion3d` additionally repeats its pass `"iterations"`
times per the render-level `iterationCount` default 60) — "stateful effects can retain several
atlases at once, and cost multiplies by iterationCount" is not hypothetical here; a naive port
that retains every iteration's atlas rather than ping-ponging a fixed buffer pair risks a real
blow-up at the larger `volumeSize` choices (128 is valid for both). **`shapes3d`'s palette
block is default-triggered, not an edge case** — it fires before any volume/MRT work is even
relevant to that specific effect. **MRT and viewport-override support are unproven, not just
unbuilt**: no program in the current corpus uses a second fragment output, so there is no
existing MRT kernel anywhere in cpp to pattern-match against for either the frontend parser or
the executor's destination-allocation logic — genuinely new code, not an adaptation of working
code. **No bit-exactness acceptance bar exists yet for any of the 16**: EFFECTS.md states "All
17 effects added in this coverage pass are separately reported as `newly ported, no GPU
golden` until pinned references exist" (`docs/EFFECTS.md:84`) — Family D's 16 plus
`filter3d/flow3d` account for exactly that 17. Unlike the 21 prior simulation effects
(permanent, explicit `cpu-divergent` skips), Family D's two iterated members are **not**
grandfathered into any skip list — they get the same "no golden yet" treatment as their 14
non-iterated siblings, meaning a pixel-diff acceptance gate has to be *created*, not just
satisfied, as part of landing each effect. Float64/raymarch bit-exactness in the actual
per-voxel/per-ray GLSL math was not inspected (no `.glsl` source path is embedded in the JSON
records) and is marked **UNVERIFIED**, though the absence of any Family D key from cpp's
4-entry hand-adapter set is weak evidence against a hidden float64-CPU-adapter dependency like
`classicNoisedeck/fractal`'s.



### 3.4 Family E — particles/draw ops (14 core + `points/heightGrid`)

#### 3.4.0 Headline corrections to the task brief

**`filter3d/flow3d` does NOT participate in the `pointsEmit` particle group.** Its `agent` pass
reads/writes `global_flow3d_state1/2/3` — none of which match `PARTICLE_STATE_PATTERN`
(`upstream-snapshot.js:12878-12903`); its `deposit`/`blend` passes touch `global_flow3d_trail`
(matching the `_trail` wildcard), but no other step ever references that name, so it never
triggers a join either. `computeIterationGroups` treats a standalone `flow3d()` exactly like
`synth/reactionDiffusion`: a single-step, `iterated:true` group with its own private per-step
scratch (`ensureGroupScratchResources`), never touching `groupResources`. Flow3d is textually
"Family E" (particle/agent simulation with a scatter deposit) but architecturally needs only
the **base iterated-single-step scheduler** shared with families B/C, not the **cross-step
particle-group sharing layer** the 10 `points/*` + 3 `render/points*` effects need.

**`docs/CSL.md:91`'s "5 vertex-stage scatter adapters" is a doc typo, not a design fact** —
the sentence *lists six names* but *says* "5". The code disagrees with the "5":
`scatter-registry.js:61-75` registers 7 keys total (wormhole + 6), backed by 6 distinct
non-wormhole adapter functions (4 in `points-deposit.js`, 1 in `billboard-deposit.js`, 1 in
`flow3d-deposit.js`). `render/pointsRender` and `render/pointsBillboardRender` do **not** share
one registry key with each other — each gets its own; what they share is only the pass-level
program *name* `"deposit"` within their own effect plus the viewMode/blendMode/define
convention. cpp's own docs get this right (`scatter/registry.hpp:10-21`,
`wormhole-report.md:172-175`, `scatter/catalog.cpp:15-18` all say "six").

#### 3.4.1 JS runtime semantics

**Particle-group open/join/close, step-granularity confirmed**: `declaresXyz(step)`
(`iteration.js:27-29`) is true only for `render/pointsEmit`'s own record — confirmed by grep,
every other family-E effect's `textures` is either `{}` or contains only *other* private
textures (`global_zState` for buddhabrot, `global_dla_grid` for dla, `global_lenia_density`/
`global_lenia_field` for lenia, `forceMatrix` for life, `global_physarum_pheromone` for
physarum, several depth/defocus textures for pointsBillboardRender). The join/close decision
is at **step granularity** — once a step joins (any one of its passes references particle
state), its *whole* pass list runs every iteration as part of the group, including passes that
touch no particle name at all (e.g. `life`'s `matrix` pass, which recomputes a fixed 8×8 force
matrix from `inputs:{}` every single iteration purely because `life`'s *other* pass, `agent`,
joined the group).

**Group-scoped resource machinery, re-verified**: `groupOwnerStateSize`
(`renderer.js:41-45`) forces a joining step's `stateSize` to the owner's value unconditionally.
`groupTextureSpec`/`resolveGroupParticleTexture` (`renderer.js:688-720`) find the first
group step declaring a name, or synthesize a `256×256`/format-per-name fallback from the
*referencing* step's params. `storeGroupOutput` (`renderer.js:762-765`) routes any
particle-state name **or `global_accum`** (family C's loop-feedback surface) into the same
`groupResources` map — **confirming §3.2.4's finding independently, from the E side**: this
is one generic "group-shared resource" primitive, not two.

**Per-effect pass-graph shape, grep'd directly, with corrected MRT/scatter counts**: reading
all 15 records in full gives: **13 of 15** effects own an MRT `agent`/`init` pass
(`drawBuffers:3` on 12, `drawBuffers:4` uniquely on `points/life`'s `agent`, at
`upstream-snapshot.js:15645`); `render/pointsRender`/`render/pointsBillboardRender` need
**zero** MRT (they only ever *read* particle state, never write it). `points/buddhabrot`'s
`zWrite` and `points/life`'s `matrix` are confirmed **ordinary single-output fragment
kernels**, not scatter-shaped, despite superficially looking simulation-like — neither
declares `drawMode` or `blend`. `points/heightGrid`'s `agent` pass carries a literal
`"type":"compute"` field also seen on 24 of `pointsBillboardRender`'s ordinary passes; grep of
`renderer.js` for `pass.type` was not exhaustively performed by either sub-agent — flagged
**UNVERIFIED** whether it changes anything at the JS runtime level, likely inert metadata for a
future non-CPU backend (consistent with family D's independent finding that `"type":"compute"`
is dead metadata there too — see §3.3.1).

**The six non-wormhole scatter adapters** (`points-deposit.js`+`billboard-deposit.js`+
`flow3d-deposit.js`, all read in full): shared primitives include a golden-ratio
low-discrepancy density cull (`GOLDEN_RATIO_CONJUGATE=0.618033988749895`), `texelFetchAgent`
(bottom-up-to-top-down row flip, matching `GlslCpuRuntime#texelFetch`), `scatterPointPixel`
(GPU point-raster equivalence with an explicit NaN guard before the bounds check — a NaN
offset would otherwise flow into `data[NaN]+=...`, a silent typed-array no-op rather than an
intentional discard), and `computeClipCenter` (shared verbatim by pointsRender/
pointsBillboardRender: flat/ortho/perspective view modes, sequential not composed-matrix
X→Y→Z rotation). Per-adapter algorithm traps found by direct reading: `dlaDepositGridAdapter`
writes alpha as `energy` alone, *not* `rgba.a*energy` (explicit literal-port trap, comment at
`points-deposit.js:207`); `leniaDepositAdapter` deposits a **constant** color regardless of
agent color (lenia's `deposit.vert` has no `rgbaTex` input at all); `pointsRenderDepositAdapter`
evaluates the density cull **before** the alive check, in upstream's exact order;
`flow3dDepositAdapter` is structurally different — voxel xyz/RGB in `stateTex1`/`stateTex2`
(not the `global_xyz` convention at all, consistent with §3.4.0's finding), three independent
agent-count caps (`capacity`, `maxAgents` from density, `pass.count`); the billboard adapter
(`billboard-deposit.js:282-450`, the largest/most complex adapter in the family) serves *both*
`deposit`/`deposit_alpha` pass records via inspecting `pass.blend` per call, combines a
depth-sort reindex, a golden-ratio cull on the *reindexed* id, a PCG-style hash for per-agent
jitter, and an affine-inverse-pixel-membership quad rasterization test with an explicitly
**closed-boundary, not GPU-half-open-fill-rule** simplification (acknowledged as unobservable
given no GPU golden exists for any of these 21 effects).

**A material precision difference from wormhole, found by direct grep**: none of the six
adapters call `Math.fround` explicitly except a single `Math.fround(n+seed)` inside a PCG hash
helper — wormhole's entire per-operation `f32r()` rounding discipline is **absent** from these
six. They do their index/cull/AABB math in plain double precision, relying on the already-
float32-or-float16-quantized *storage format* for precision at the boundary, not on
per-operation rounding. This means the real GLSL-float32-fidelity work concentrates in the
not-yet-transpiled agent MRT kernels themselves (out of scope for this pass — their `.frag`
sources aren't even in the corpus yet), while the six deposit adapters are comparatively
lower-precision-risk index/geometry code.

**`heightGrid`'s no-fallback behavior, mechanism confirmed exactly**: `needsParticlePipeline`
(`bin/noisemaker-cpu.js:120-129`) iterates an effect's passes in declaration order, testing
each pass's inputs against a `written` set populated only from *earlier* passes' outputs.
heightGrid's one pass reads `global_xyz`/`global_vel` with no earlier pass at all, so the check
trivially fires (matching `EFFECTS.md:31` verbatim). Every *other* `points/*` effect's `agent`
pass reads *and writes* the same particle names in the *same* pass — same-pass read+write never
trips the check (it specifically tests "read before being written by an *earlier* pass") — which
is why they get the 256×256-fallback behavior instead of a hard throw: their own kernel can
manufacture/respawn agent state from nothing, whereas heightGrid's kernel is a pure
rearrangement with no spawn logic (matches its description, "Arrange every particle in a
landscape grid...").

#### 3.4.2 What cpp currently does, and the precise gap

Re-verified independently: a grep of both `executor.cpp` and `compiler.cpp` for
`global_xyz|particle|pointsEmit|points/|render/points` returns **zero matches** in either
file. **More fundamentally than the task brief's framing**: a grep of `executor.cpp` for
`iteration|loop` also returns zero matches — there is no runtime iteration-group concept of
*any* kind, not just no particle-group layer. `compiler.cpp` only validates `loopBegin`/
`loopEnd` *syntax* at compile time; nothing executes a region N times, iterated or not. **This
independently corroborates §3.2's finding from the E side**: families B/C's own base
iteration scheduler doesn't exist either, and both families are blocked on the same,
currently entirely-unbuilt piece of runtime machinery.

Two more blanket refusals, re-confirmed: scatter (`executor.cpp:781-787,1011-1015,1333-1336`,
three call sites now, one more than previously noted) and MRT/non-fragment draw mode
(`executor.cpp:1023-1034,1339-1340`).

**Root cause of family E's `missing` (not `scatter`) classification, resolved precisely —
refining the task brief's own hypothesis.** `EffectRegistry::admission()`
(`registry.cpp:926-969`) returns `AvailabilityStatus::scatter` only if the underlying
`ReferencePassCompatibility` row's own `status == "scatter"`. That row is generated by a
cpp-repo Python tool, `tools/dsl/generate_backend_compatibility.py`, whose status-assignment
logic has exactly three branches: (1) `key == SCATTER_KEY` → `"scatter"`, where `SCATTER_KEY`
is a **single hardcoded literal string, `"filter/wormhole:deposit"`**, not a set or lookup
table; (2) `key in by_key` (the program already has a `.frag` source in the 212-entry
executable-fragment corpus manifest) → whatever the corpus computed; (3) else →
`"missing"`/`missing_backend_program`. A direct check of that manifest found **zero**
family-E keys present at all. So the true state is: **family E's `.frag` sources have not
even been added to the corpus yet, for either ordinary or scatter passes**, and the
`"scatter"` classification is a single hand-baked exception for wormhole with no
generalization mechanism in place for the other six keys. Promoting family E out of
`"missing"` requires two independent, non-interchangeable steps depending on pass shape: (a)
add each ordinary pass's `.frag` source to the corpus/manifest, letting it flow through the
normal typed-generation pipeline; (b) generalize `SCATTER_KEY` from a scalar to a set covering
the six new keys, mirroring the existing scatter-contract-building logic per key. This
confirms the task brief's own closing framing ("simply unclassified/unbuilt, not
known-scatter-but-blocked") with the exact mechanism and file.

The scatter-adapter *registry* is already ported generically and simply unused — re-confirmed:
`registry.hpp`/`registry.cpp`/`catalog.cpp` mirror the JS registry 1:1; `catalog.cpp`'s
`register_builtin_scatter_adapters()` calls only `wormhole::register_adapter()` today and
comments out the exact six future calls. No dispatch site calls any of this yet.

#### 3.4.3 GLSL programs needing admission vs. hand-written adapters, and the MRT question

Cross-checking every pass record against `backend_compatibility.json` (all read `"missing"`,
none read `"scatter"` — confirming §3.4.2's finding empirically for every single record):
**84 total pass records** across the 15 effects, collapsing to **52 distinct program_keys**
needing any work: **15 scatter pass records / 6 distinct adapter keys**; **13 MRT pass
records / 13 distinct keys** (one per effect, all of family E's agent-owning effects except
pointsRender/pointsBillboardRender); **56 ordinary pass records / 33 distinct ordinary
keys** — sharing is real and non-trivial (`points/physarum`'s `copy` and `passthrough` passes
share one key; `pointsBillboardRender`'s 22 `depthMerge0..21` records all share **one** GLSL
program, contributing 22 pass records but only 1 typed-corpus admission). `zWrite`/`matrix`
are confirmed ordinary typed-corpus candidates needing nothing beyond what any of the 294
already-generated programs needed, once their `.frag` sources are added to the corpus.

**MRT is a hard, separate executor capability — and the same one family D's cubemap/renderer
effects need, on structural grounds.** The executor's MRT refusal (`draw_buffers->number !=
1.0` → `unsupported_mrt`) is generic, rejecting any pass with >1 draw buffer regardless of
family. Since 13 of 15 family-E effects need `drawBuffers:3` or `4`, and JS's own MRT pixel
loop (`renderer.js:450-490`) is a single shared implementation used by every MRT-capable
effect regardless of namespace, the natural cpp analog is **one shared multi-output pixel-loop
primitive** in the executor/pass-runner layer, built once and wired into whichever family
lands it first. **This reconciles directly with family D's own, independently-derived finding**
(§3.3, "MRT has no precedent anywhere in the currently-admitted 211/304 programs") — both
families hit the exact same refusal at the exact same two call sites for the exact same
underlying reason, and neither family's own report had visibility into the other's — this
report is the reconciliation point. **Recommendation: land MRT support once, generically,
before either family's MRT-dependent effects, rather than have family D and family E each
build it independently.**

#### 3.4.4 Cross-family shared infrastructure and landing order

**Particle-grouping is genuinely "the base iteration scheduler plus a resource-naming
convention," not separate machinery — but the base scheduler itself doesn't exist in cpp for
either family.** JS has exactly one grouping function and one pair of execution functions
serving *every* iterated effect, single-step (family B/C, plus flow3d) and multi-step particle
groups (family E) alike; the only code that differs is whether `declaresXyz`/
`referencesParticleState` ever fire and whether a resource resolves through the step-private
map or the group-shared map. **Landing the base N-times-execution scheduler (needed by
families B/C and by flow3d) is a strict prerequisite for family E**; once it exists, the
additional particle-group layer is comparatively small — a resource map keyed by texture name
instead of by step, plus the `stateSize`-inheritance override. This matches §3.2.4's
three-layer recommendation exactly, arrived at independently from the E side.

**Scatter-dispatch executor wiring is shared with family A's wormhole; wormhole should land
first** — the registry/catalog/dispatch-branch design is explicitly written for verbatim reuse
by the six remaining adapters, and wormhole's branch is already fully verified. This matches
§3.1.4's recommendation, arrived at independently from the E side — both family A's and family
E's own reports converge on the same landing-order conclusion without having seen each other's
findings.

**Recommended internal landing order for family E's own 15 effects** (biased toward proving
each new mechanism — base scheduler → particle-group sharing → MRT → scatter → depth-sort
complexity — on the smallest surface before compounding them): (1) `points/attractor` first
(simplest MRT3-agent + passthrough shape, proves particle-group-open + MRT3 together
minimally); (2) `points/flock`/`flow`/`hydraulic`/`physical` as a batch (structurally
identical to attractor); (3) `render/pointsEmit` itself, early regardless of ordering since
every other points effect depends on it as group owner; (4) `points/dla` (first scatter
adapter, plus two extra ordinary passes); (5) `points/buddhabrot` (adds an ordinary
private-texture pass, and — per §5 — a cost/perf checkpoint before denser effects); (6)
`points/life` (first and only `drawBuffers:4` effect — proves MRT generalizes past 3 outputs);
(7) `points/lenia`/`physarum` (second/third scatter adapters; physarum is explicitly
cost-flagged in EFFECTS.md); (8) `points/heightGrid` (needs nothing new mechanically, but is
the required regression target for the CLI's auto-`pointsEmit()`-injection path); (9)
`filter3d/flow3d` (per §3.4.0, needs none of the particle-sharing layer — could land as early
as right after the base scheduler + MRT + scatter exist, but its `volume-filter` domain pulls
in family D's volume-bundle concerns, so its exact sequencing relative to family D is an open
question this report resolves in §4 below); (10) `render/pointsRender` (first non-agent-owning
effect, three scatter-pass variants gated by viewMode); (11) `render/pointsBillboardRender`
last (38 pass records, depth-sort, aperture defocus, three view modes compounding every prior
mechanism at once — see §5).

#### 3.4.5 Risks

**Bit-exactness of the six scatter-adapter ports is the dominant risk; repeating wormhole's
oracle-plus-mutation-testing methodology per adapter is not optional.** Every one of the six
family-E adapters has at least one structurally plausible mistranslation trap already visible
in the source (dla's alpha-is-energy-alone convention, lenia's ignore-agent-color-entirely
constant deposit, pointsRender's cull-order-matters density check, pointsBillboardRender's
hash+affine-rasterization+boundary-convention stack) — each is exactly the shape of bug
wormhole's process caught only via AddressSanitizer plus exhaustive mutation testing, not by
inspection. **Cost traps beyond EFFECTS.md's already-documented ~25s physarum chain**:
`points/buddhabrot`'s default `stateSize:512` (double every other effect's 256 default)
combined with `maxIter:200` (range 20-2000) suggests a per-agent escape-time inner loop whose
worst-case cost (`UNVERIFIED`, `.frag` source not yet in corpus) could reach `stateSize² ×
maxIter × iterationCount` ≈ 512²×2000×60, orders of magnitude larger than the "flat" agent
effects' `256²×60`. `filter3d/flow3d`'s agent-state textures are fixed at literal 512×512
(262,144 agents) **regardless of `volumeSize`**, giving ~15.7M agent evaluations per render at
default `iterationCount` — comparable to buddhabrot's worst case. **`render/
pointsBillboardRender` is the single highest-risk effect in the whole 46-effect backlog** —
confirmed on stronger grounds than assumed: beyond raw pass count, it uniquely combines an
unconditionally-present 22-stage depth-sort network (most of which is runtime-gated off but
must still be correctly evaluated-and-skipped), three independently-combined runtime-variation
axes (viewMode × blendMode × defocus-on/off) each selecting among 8 `deposit`-program records
with different `defines`-as-uniforms bindings, a continuous-threshold 5×5 defocus convolution,
and the PCG-hash/affine-rasterization complexity — no other single effect in the family
combines this many independently-variable runtime axes inside one scatter adapter.
**Parity/skip status, confirmed for all 15**: every family-E effect is an explicit "CPU
iteration divergence" skip in EFFECTS.md (the 13 named individually plus heightGrid named as
one of "3 more from this round's landscape/heightfield release") — **zero pixel-parity
fixtures exist for any of these 15 today**, so the JS CPU reference itself is the *only*
ground truth available, reinforcing that wormhole-style oracle+mutation discipline (not
GPU-pixel comparison) is the only available verification path for this entire family.



## 4. Cross-family shared infrastructure and recommended landing order

All four family reports were produced independently (four separate agents, no visibility into
each other's findings) and then reconciled here. Two of them arrived at **identical
conclusions from opposite directions** (families B/C and E both independently concluded that
JS's particle-group and loop-region mechanisms are one primitive; families D and E both
independently hit the exact same MRT refusal for the exact same reason and each flagged it as
an open question for the other) — that convergence is itself strong evidence the shared-infra
map below is the right shape, not an artifact of one report's framing.

### 4.1 The five genuinely-new executor primitives, ranked by how many families need them

1. **A base "run this pass graph N times" iteration scheduler.** Needed directly by: all 8
   Family B effects, both Family C effects (as the "loop region" special case),
   `synth3d/cellularAutomata3d` + `synth3d/reactionDiffusion3d` (Family D's two iterated
   generators), `filter3d/flow3d` (Family E, but per §3.4.0 as a *single-step* iterated
   effect, not a particle group), and — as the substrate the particle-group layer sits on top
   of — every `points/*`/`render/points*` effect in Family E. **This does not exist in cpp in
   any form today** — independently confirmed by three of the four family reports via the
   identical grep (`executor.cpp` has zero matches for `iterated|loop_role|particle|
   global_xyz|iteration|loop`). It is the single most cross-cutting piece of missing
   infrastructure in the entire 46-effect backlog. Recommended internal shape (per §3.2.4,
   independently corroborated by §3.4.4): three layers — (a) a step-scoped persistent resource
   map (reuse the step's existing binding code, just stop rebuilding it every iteration; needed
   by 6 of Family B's 8 effects and is a strict subset of everything else); (b) an outer
   `N`-times loop driver calling each step's *existing, unmodified* single-pass execution path
   with `frame=i, delta_time=1/600, time=wrap01(...)`, resetting the nominal chain input to the
   frozen group input every iteration; (c) a group-shared resource map (below) layered on top.
2. **A group-shared resource map** (`global_accum` + particle-state names). Needed by Family C
   (`global_accum`) and Family E's particle groups. **Proven, at the JS-authority level, to be
   *the same primitive*** — `storeGroupOutput`'s single branch (`renderer.js:762-765`) routes
   both into the identical `groupResources` map, differing only in the name-matching
   predicate — independently re-derived by both the B/C and E sub-agents from opposite
   directions. Recommend implementing once: a map keyed by resource name, shared across every
   step in a group for the group's full `N`-iteration run, entries *replaced* (never mutated
   in place) on write, released at group end unless retained in the final output.
3. **MRT (multi-render-target) execution.** Needed by 11 of Family D's 16 effects and 13 of
   Family E's 15 effects — **24 passes across two families, refused at the identical two
   `executor.cpp` call sites for the identical reason** (`draw_buffers->number != 1.0` →
   `unsupported_mrt`). Neither family's own report had visibility into the other's finding;
   this report is the reconciliation point, and the conclusion is unambiguous: **build one
   shared multi-output pixel-loop primitive** (mirroring JS's single `runCanonicalMrtPass`
   implementation, `renderer.js:450-490`, used by every MRT-capable JS effect regardless of
   namespace) in the executor/pass-runner layer, once, before either family's MRT-dependent
   effects land. **No program in the currently-admitted 211/304-program corpus uses a second
   fragment output** (independently confirmed by Family D's own corpus search) — this is
   genuinely new ground for the GLSL frontend parser too, not just the executor.
4. **Volume/geometry bundle threading**, generalizing `GraphExecutor::execute`'s single
   `GraphResource* current` to a `{image, volume, geometry, volumeSize}` struct. Needed
   directly by Family D's 14 real volume-domain effects (2 of D's 16 are plain `domain:"image"`
   and don't need it at all — a correction to the task brief's framing, see §3.3.1). Possibly
   also relevant to `filter3d/flow3d` (Family E), whose deposit adapter already flattens agent
   Z-slices into a `volumeSize × volumeSize²` atlas using the same N×N² convention, even though
   flow3d doesn't go through the chain-level `{image,volume,geometry}` bundle the way a
   `volume-*`-domain effect does (§4.3 below resolves this).
5. **Scatter dispatch**, wiring the already-complete `noisemaker::scatter` registry into
   `GraphExecutor::execute`'s per-pass loop (one new branch: if `admission.status ==
   AvailabilityStatus::scatter` and an adapter resolves for the program key, call it instead of
   `bind_factory_route`/`run_pass`), and relaxing the two blanket scatter refusals to be
   conditional on adapter availability. Needed by Family A's `filter/wormhole:deposit` (adapter
   already ported and independently oracle-verified bit-exact) and, once ported following the
   same methodology, Family E's six remaining scatter adapters (`dla`, `lenia`, `physarum`,
   `flow3d`, `pointsRender`, `pointsBillboardRender`).

### 4.2 Recommended global landing order

This sequencing is chosen to (a) prove each new primitive on its smallest, already-verified
instance before compounding it with the next, (b) keep the fixed-corpus/generated-artifact
regeneration serialized per §6 rather than colliding across parallel lanes, and (c) unblock
the largest number of downstream effects per step.

1. **Wormhole's scatter-dispatch executor branch (Family A).** Smallest possible instance of
   primitive #5 above — one adapter, already registered, already bit-exact per a 62-case/
   9-mutation oracle (§3.1). Touches exactly two existing refusal sites. Proves the real
   dispatch branch against the live `execute()` driver before anything harder needs to extend
   it. Unblocks `filter/wormhole` (1 of the 46) plus establishes the template
   families A and E's own reports both independently recommend reusing for the other 6
   scatter adapters.
2. **`filter/text`/`synth/media` CLI plumbing (Family A) + the worm-overlay generator
   algorithm (Family A) + the `snow` hand-adapter port (Family A) + the `testPattern` kernel
   bug-fix (Family A), in parallel with step 1** — none of these four depend on or block any
   other family's work; they are pure, independent, small pieces of net-new C++/CLI code
   (§3.1.3). Landing all of Family A first clears 8 of the 46 effects with zero executor
   architecture changes beyond step 1's scatter branch.
3. **The step-scoped persistent-resource layer** (primitive #1a) — the cheapest, most
   broadly-needed piece of the iteration scheduler; needed by 6 of Family B's 8 effects and a
   strict subset of every later step.
4. **The outer N-iteration loop driver** (primitive #1b), wired to the existing single-pass
   path unmodified. This alone (plus step 3) is sufficient to unblock: the 2 remaining Family B
   effects that need the narrow `selfTex`/`feedback` special case (add it here), and — once
   their GLSL kernels are separately admitted (§6) — `synth3d/cellularAutomata3d`/
   `reactionDiffusion3d` (Family D) and `filter3d/flow3d` (Family E, per §3.4.0/§4.3).
5. **MRT execution** (primitive #3), built once, generically. This is the single highest-
   leverage remaining piece: it unblocks 11 of Family D's effects and 13 of Family E's effects
   simultaneously — 24 passes across two families from one piece of new machinery.
6. **Volume/geometry bundle threading** (primitive #4), landed against Family D's
   *non-iterated* volume effects first (12 of 14 real volume-domain effects — the 2 iterated
   ones need step 4 as well, already landed by this point). `classicNoisedeck/noise3d`/
   `shapes3d` can land any time after step 5 (MRT) independently, since neither needs the
   bundle at all — `noise3d` needs nothing further; `shapes3d` additionally needs the
   `paletteData` port (step 8, orthogonal, can run in parallel with this whole sequence).
7. **The group-shared resource map** (primitive #2), generically, with `global_accum`
   (Family C) and particle-state names (Family E) as its two call sites. Land Family C
   first as the cheaper exercise (2 unique GLSL programs, one trivial blend kernel, no scatter,
   no agent-count parameter) before Family E's particle groups add scatter-adapter complexity
   on top of the same primitive.
8. **`paletteData` (the 55×16 table)** — orthogonal to the whole sequence above, can be ported
   in parallel starting any time; it unblocks `classicNoisedeck/shapes3d` (Family D) and any
   other `classicNoisedeck` effect elsewhere in the catalog selecting a non-zero palette.
9. **The six remaining scatter adapters (Family E)**, following wormhole's oracle-plus-
   mutation-testing methodology one at a time, after steps 4-5-7 have landed (each needs the
   particle-group layer, most need MRT for their companion agent pass, all need the scatter
   dispatch branch from step 1). Internal order within this step: Family E's own
   recommendation in §3.4.4 (attractor → the four MRT3-passthrough clones → pointsEmit → dla →
   buddhabrot → life → lenia/physarum → heightGrid → flow3d → pointsRender →
   pointsBillboardRender last).
10. **`render/pointsBillboardRender`** lands last, deliberately — both by Family E's own
    internal ordering and by this report's synthesis: it is, by independent assessment, the
    single highest-risk effect in the entire 46-effect backlog (§5).

### 4.3 Resolving the two families' open cross-questions

Both the Family D and Family E sub-agents flagged questions for "the orchestrator" to resolve
without visibility into each other's work. Resolving them now, from both reports together:

- **"Is family D's cubemap MRT the same mechanism family E's agent passes need?"** (Family E's
  question) / **is there a shared MRT need at all?** (implicit in Family D's report) — **Yes,
  confirmed.** Family D independently found 11 of 16 effects declare `"drawBuffers":2`
  (including both `renderCubemap3d`/`renderCubemapSurface`) and that MRT has zero precedent in
  the current corpus; Family E independently found 13 of 15 effects declare `"drawBuffers":3`
  or `4` and reached the identical "build MRT once, generically" recommendation from the
  refusal-site symmetry alone. Both are describing the same gap. See §4.1 primitive #3.
- **"Does `'type':'compute'` change anything at the JS runtime level?"** — **Resolved:
  no, it's inert metadata.** Family D independently confirmed this by grepping
  `src/runtime|dsl|csl` for `pass.type`/`type === 'compute'` and finding zero branches on it
  anywhere in the CPU runtime, concluding it is forward-looking metadata for a future non-CPU
  backend. Family E flagged the identical field on `heightGrid`'s agent pass and 24 of
  `pointsBillboardRender`'s passes as unverified from its own reading. Family D's confirmed
  finding transfers directly: it's the same field in the same schema, and there is no
  mechanism anywhere in the codebase (checked independently by two separate reports) that
  would treat it differently for Family E's instances. Treat as **confirmed, not just
  UNVERIFIED-and-consistent**: `pass.type` needs no executor support in either family.
- **"Where does `filter3d/flow3d` sequence relative to family D's volume-bundle work?"**
  (Family E's question) — **Recommendation: flow3d does not need Family D's full
  chain-level `{image,volume,geometry}` bundle-threading primitive (#4 above) at all** —
  its `volumeSize`-sized agent-state atlas is a private, per-step concern sized directly by a
  `volumeSize` param and consumed only inside its own deposit adapter's clip-space math
  (§3.4.1's `flow3dDepositAdapter` reading: it flattens Z-slices via `atlasY = state1[1] +
  floor(state1[2]) * volumeSize`, entirely inside the adapter, never touching a chain-level
  volume/geometry route). It needs only the **dimension-resolution convention** Family D's
  bundle work will establish for sizing an `N × N²` atlas texture (`textureDimension`'s
  `{screenDivide}`/`{param}` forms, `renderer.js:129-154`) — not the bundle threading itself.
  Recommend landing flow3d any time after steps 4-5 (base scheduler + MRT) and the scatter
  dispatch branch (step 1) exist, **without** waiting for step 6's full bundle-threading work,
  reusing only its atlas-dimension-sizing helper once that helper exists as a standalone
  utility (which it should be, regardless, since both families need it independently).

## 5. Risks (rolled up across families)

Ranked by a combination of severity and how many effects each risk touches, synthesizing all
four family reports' individual risk sections (§3.1.5, §3.2.5, §3.3.5, §3.4.5) rather than
repeating them.

1. **`render/pointsBillboardRender` (Family E) is the single highest-risk effect in the whole
   46-effect backlog**, independently assessed as such by its own family report on multiple
   compounding grounds (§3.4.5): 38 pass records, an unconditionally-present 22-stage
   depth-sort network that must still be correctly evaluated-and-skipped in the common case,
   three independently-combined runtime-variation axes (viewMode × blendMode × defocus)
   selecting among 8 conditionally-run `deposit`-program records, a continuous-threshold 5×5
   defocus convolution, and a PCG-hash-plus-affine-rasterization core. No other single effect
   in the entire backlog combines this many independently-variable runtime axes. Land it
   strictly last (§4.2 step 9's internal ordering).
2. **`synth/navierStokes` (2,160 passes/frame) and `synth/reactionDiffusion` (540
   passes/frame) are precisely-quantified cost traps**, the second not previously named in
   EFFECTS.md's own cost discussion — both derived by direct arithmetic on verified pass
   counts and default `iterations`/`iterationCount` values, not assumed (§3.2.1). Combined
   with Family E's own newly-identified cost risks — `points/buddhabrot`'s `stateSize:512 ×
   maxIter:200` combination (potentially `stateSize²×maxIter×iterationCount` ≈ 5×10¹⁰ inner
   ops in the worst case, UNVERIFIED pending the actual kernel source) and `filter3d/flow3d`'s
   fixed 512×512/262,144-agent population independent of `volumeSize` (~15.7M agent
   evaluations/render at default settings) — recommend an explicit, named (not just
   family-level) exclusion list for casual smoke-test sweeps, and consider lowering
   `iterationCount`/`iterations` defaults specifically for automated correctness-only test runs
   across all four of these effects.
3. **MRT and volume-atlas execution paths are unproven, not merely unbuilt**, independently
   confirmed by both Family D and Family E: zero programs in the current 211/304-program
   corpus use a second fragment output, so there is no existing MRT kernel anywhere in cpp to
   pattern-match against for either the GLSL frontend parser or the executor's
   destination-allocation logic. This is materially riskier than "write more kernels in an
   established pattern" — treat the MRT primitive (§4.1 #3) as new engineering requiring its
   own design/review pass, not an incremental extension.
4. **`ResourceArena`'s lifetime model does not support what an iteration group needs, and this
   is a design gap that should be scoped explicitly before implementation, not discovered
   mid-port** (§3.2.5, Family B/C's own finding): `ResourceLifetime` has no category for
   "persists across N re-executions of a subgraph, never published to a name any other step
   could bind by mistake," and the existing `ScopedPin` machinery is explicitly documented as
   scoped to one effect's single-pass execution, not a whole iterated group's lifetime.
   Retrofitting this by convention (manual re-pinning every iteration) risks exactly the kind
   of use-after-retire bug the arena's aggressive retire-on-zero-reference policy exists to
   prevent.
5. **Bit-exactness verification burden is large and uneven across families, and Family A's own
   two sub-cases (`snow` vs. `testPattern`) show why "one guard, one fix" reasoning is
   dangerous.** `filter/snow`'s generated kernel is simply the wrong ground truth (the
   authority never executes it — a hand-adapter port is the correct fix); `synth/testPattern`'s
   generated kernel *is* the ground truth and cpp's own emission pipeline has a genuine
   boundary bug (a fix, not a port) — both currently caught by one identical-looking guard
   (`kMeasuredParityExclusions`). The worm-overlay trio (Family A) depends on matching V8's
   *float64* transcendentals with no existing oracle anywhere in the checkout — a harder,
   less-precedented target than wormhole's float32-rounded case. Family E's six scatter
   adapters do their index/geometry math in double precision throughout (only one incidental
   `Math.fround` call across all six files), relying on the storage format for precision at
   the boundary — meaning the real float32-fidelity risk for Family E concentrates in the
   not-yet-transpiled agent MRT kernels, not in the deposit adapters examined here.
   **Recommend a per-effect (not per-family) verification-methodology assignment**: wormhole's
   oracle-plus-mutation-testing discipline is mandatory for every new hand-written C++ adapter
   (worm-overlay, snow, and all six of Family E's remaining scatter adapters); ordinary
   typed-corpus GLSL admissions (the large majority of B/C/D/E's 92 new programs, §6) get the
   standard typed-corpus pipeline's existing exactness gates instead.
6. **The pixel-correctness acceptance bar is explicitly looser than a GPU golden for most of
   this backlog — good news, but state it explicitly rather than assume it.** All 8 Family B
   effects are inside the JS authority's own permanent 21-effect `cpu-divergent`-skip set;
   `render/loopBegin`/`loopEnd` have **no pinned JS-side pixel reference of any kind** yet
   (they're in `NEW_CPU_EFFECT_IDS`, the "fixtures compile but aren't pixel-diffed" bucket);
   all 16 of Family D's effects and all 15 of Family E's effects are `"newly ported, no GPU
   golden"` per EFFECTS.md's own accounting. Practically: the acceptance target for nearly
   this entire 46(+3)-effect backlog is "match the JS CPU authority's own output," not "match a
   GPU golden" — but for `loopBegin`/`loopEnd` specifically, cpp's own future fixtures would be
   the *first* pinned pixel reference of any kind for the loop-region pattern anywhere in the
   project, meaning that reference has to be built as part of landing the feature, not assumed
   to already exist.
7. **Two independent, easy-to-miss kit-visibility gaps of the same shape, both flagged by
   Family A**: `export-kit/generate-compat.mjs` hardcodes `effects.delete('synth/media')`
   unconditionally (not read from any executor guard, so it won't self-clear once the runtime
   port lands) and its admission test is a literal `status === 'compatible'` string check (so
   `filter/wormhole` will keep failing kit admission even after the scatter-dispatch branch
   ships, since its backend status will still read `"scatter"`, a classification label, not an
   adapter-availability flag). Both need a follow-up edit to the generator script itself,
   independent of the runtime work that "should" have fixed them.

## 6. Fixed-corpus gate migration

`tools/glslcpp/check_corpus.py` (`<noisemaker-for-cpp integration tree>`) validates the
**existing** pinned GLSL corpus against hard-coded literal counts, independent of the 46-effect
Phase 2 backlog:

- `len(programs) != 212` → `"manifest: expected exactly 212 programs"` (`check_corpus.py:119-120`)
- `len(sources) != 212` → `"manifest: source count gate drift"` (`check_corpus.py:156-157`)
- `len(effects) != 167` → `"metadata: expected exactly 167 effects"` (`check_corpus.py:167-168`)
- `(pass_count, keyed, overrides) != (212, 211, 1)` (`check_corpus.py:191-194`) — 212 total
  canonical passes, 211 distinct program keys (one pass, `filter/wormhole:deposit`, shares its
  vertex/fragment key with another physical row — the `overrides == 1` is that single
  drawMode-override case, per the surrounding wormhole-specific assertion at line 191), and 167
  distinct effects.

**This 212-program/167-effect corpus is the pre-existing GLSL-typing effort** (the one that
took the port from the low-100s to 159/205 effects — see `docs/port-engineering/
REMAINING-EFFECTS.md`/`REMAINING-WORK-ROADMAP.md` for its own, separate history) — it is
**not** the same thing as the 46-effect Phase 2 backlog this report is about. It already
contains every GLSL program every one of the 159-already-working effects needs, plus every
program family A's 8 effects need (all already `"compatible"`).

Landing families B/C/D/E requires **92 net-new unique GLSL program keys** — verified by two
independent methods that agree exactly: (1) directly querying `backend_compatibility.json`'s
344 `reference_passes` records for `status: "missing"` and counting distinct `program_key`
values across the *entire* file (132 individual pass records → 92 distinct keys); (2) summing
each family's own independently-derived count from its deep-dive report — Family B/C: **24**
(§3.2.3, exact), Family D: **16** (§3.3.3, one pass each, no sharing), Family E: **52**
(§3.4.3, 33 ordinary + 13 MRT + 6 scatter) — `24+16+52 = 92`, matching method (1) exactly.
Family A contributes **0** new program keys (all 9 of its program keys are already
`"compatible"`/`"scatter"`, §3.1.3). This cross-check (one top-down query against the whole
file, four independent bottom-up per-family counts arrived at by separate research passes with
no visibility into each other's numbers) is strong evidence the 92 figure is correct, not an
artifact of one counting method.

The **effect-count gate has a similarly clean cross-check**: `167 → 167+41 = 208`, where 41 is
the sum of Family B (8) + Family C (2) + Family D (16, i.e. 14 core + 2 new) + Family E (15,
i.e. 14 core + 1 new) — **not** 46, because Family A's 8 effects are already counted inside
the existing 167 (their programs are already `"compatible"`, §3.1.3, so they were already part
of the typed-effect corpus before this report's diff was run; only B/C/D/E are entirely absent
from it today, §3.2.2/§3.3.2/§3.4.2 all independently confirm this via the identical `"missing"`
status). **208 is also exactly the JS authority's own current total effect count**
(`docs/EFFECTS.md:5`: "The runtime contains 208 effects") — i.e. landing every effect this
report covers (the 46-effect gap plus the 3 newer additions) brings cpp's typed-effect corpus
to parity with the JS authority's own full current catalog size, a satisfying independent
confirmation that no effect has been missed or double-counted across the five family
groupings.

The `(212,211,1)` pass/keyed/override triple will grow by roughly `212+92=304` passes, and by
however many of Family E's new scatter passes need the same drawMode-override treatment
wormhole's `deposit` already gets — the 6 remaining scatter adapters (`dla`, `lenia`,
`physarum`, `pointsRender`, `pointsBillboardRender`, `flow3d`) each plausibly need one override
row, pushing `overrides` from `1` toward `7`, but the exact new value depends on the corpus
manifest's own per-pass `"key"` concept (distinct from `program_key`) and was **not**
independently re-derived by any family report — flagged as **UNVERIFIED** beyond "it grows and
must be hand-updated," per Family B/C's own explicit caveat (§3.2.3).

Beyond `check_corpus.py`, three more generated artifacts move in lockstep and must be
regenerated in dependency order, per the operating rules recorded in this same cpp tree's own
`docs/port-engineering/NEXT_CODING_AGENT_HANDOFF.md` (top block, "Generated artifacts move only
through their generators, exactly once per change, with the pin cascade propagated in
dependency order: compat → effect catalog → corpus fixture → sidecars"):

1. `src/effects/generated/backend_compatibility.json` (2.5 MB) — regenerated first; every
   family's new program keys flip from `"missing"` to `"compatible"` (or `"scatter"`) here.
2. `src/effects/generated/effect_catalog.cpp` (4.3 MB, generated) + its
   `effect_catalog.provenance.json` sidecar — regenerated from the updated compatibility
   document; this is where each new `EffectDefinition`'s `domain`/`iterated`/`loop_role`
   fields actually get populated for the first time for families B/C/D/E (confirmed absent or
   present per the family reports below).
3. `tools/glslcpp/typed_slice.json` / `src/typed_generated/typed_slice.cpp` (the actual typed
   GLSL kernel bodies) — grows by the 92 new programs.
4. `tests/test_typed_generator.py`'s pinned hashes/counts (per the handoff doc's own repeated
   warning: "Renaming or editing ANY hand-written test file can move a pin... run full discovery
   before pushing such a commit") — every one of these pins must be re-derived, never hand-typed,
   after each landing.

Recommended sequencing for **parallel lanes without collisions**: since all four generated
artifacts are single monolithic files regenerated wholesale by their own generators (not
hand-edited, not diffed line-by-line), the actual collision risk is not "two lanes touch the
same line" but "two lanes both regenerate the same file from a partially-landed source tree and
clobber each other's in-flight work." The mechanical fix used elsewhere in this codebase (see
the wormhole precedent) is: land one family's GLSL-corpus admission + registry/catalog data
completely, regenerate all four artifacts and get them merged, *then* start the next family's
admission — i.e. **serialize the generated-artifact regeneration step across families even if
the executor/runtime work happens in parallel branches**. See §4 for which family should hold
that serialization slot first.

## 7. CLI / export-kit parity: how each engine's kit invokes rendering

### 7.1 JS authority CLI (`bin/noisemaker-cpu.js`, 408 lines)

Commands: `generate EFFECT` (render a catalog effect, `'random'` picks one of `kind:
'generator'`), `apply EFFECT INPUT` (apply a filter to an input PNG), `animate EFFECT`
(sweep `time` over `[0,1)` `frame-count` times into an `.mp4` via `ffmpeg`, or keep PNG
frames with `--save-frames`), `run` (DSL program on stdin), `render PROGRAM` (DSL file, `-`
for stdin), `effect EFFECT` (render one catalog effect with test-shaped default wiring),
`csl SHADER` (render a raw CSL generator file), `effects` (list every catalog id + kind).

Flags relevant to this backlog: **`--input FILE`** binds a decoded PNG as *both*
`imageTex` and `textTex` external textures (`loadExternalTextures`, lines 203-210) — this is
exactly what `filter/text` and `synth/media` need. **`--texture NAME=FILE`** (repeatable)
binds an arbitrary named external texture (lines 211-217). **`--param NAME=VALUE`**
(repeatable) and **`--uniform NAME=VALUE`** (repeatable, CSL-only) inject effect parameters
without hand-writing DSL text.

The CLI does substantial **DSL-program synthesis** on the caller's behalf, all inside
`effectProgram(effect, assignments)` (lines 131-162) — this is the single most
important piece of convenience logic the cpp CLI is missing, and it directly explains why
several of the 46 gap effects "just work" from the JS CLI today with a bare effect name:

- **Particle pipeline auto-injection** (`needsParticlePipeline`, lines 116-129, and its use at
  134-136): detects an effect that reads a particle-state global (`global_xyz`/`vel`/`rgba`/
  `points_trail`) as a pass **input** with no preceding **output** of that same name among its
  own passes — i.e. a `points/*` effect that cannot self-seed. `points/heightGrid` is the
  concrete, named example (EFFECTS.md, `docs/EFFECTS.md:31`; and see family E's report). For
  such an effect the CLI silently prepends `solid().pointsEmit(stateSize: x64).` ahead of the
  requested call.
- **Loop wrapping** (lines 137-141): `render/loopBegin`/`render/loopEnd` each get wrapped with
  the *other* half of the pair (`loopBegin(iterationCount: 1)` or `loopEnd()`) so a bare
  `effect loopBegin` still compiles to a balanced region.
- **Volume-domain wiring** (lines 142-152): a `volume-generator` gets `.render3d().write(o0)`
  appended; a `volume-filter` gets prefixed with `noise3d(volumeSize: N).` and suffixed with
  `.render3d().write(o0)`; a `volume-renderer`'s own effect *is* the render step. `N` is read
  back out of the caller's own `--param volumeSize=...` assignment if present (including a
  dotted enum-choice spelling), else the effect's own declared default, else `16`.
- **Mixer surface auto-wiring** (lines 156-161): for a non-generator/filter effect (i.e. a
  mixer with multiple `type: 'surface'` parameters), the CLI auto-generates up to 6 solid-color
  source surfaces and wires them positionally into the call.

### 7.2 cpp CLI (`tools/cli/noisemaker_render.cpp`, 419 lines)

Single command: `noisemaker-render PROGRAM.dsl [options]`. Flags: `-o/--output`,
`--width`, `--height`, `--time`, `--frame`, `--seed`, `--raw-rgba8`, `--metadata`,
`--list-effects`, `-h/--help`. **No `--input`, no `--texture`, no `--param`, no effect-name
shortcut commands, no `animate`.** The tool's own header comment is explicit about why it's
this thin: "This is the user-facing entry point... renders through the *same* library route
the corpus harness drives... this file owns only its CLI, its help text and its human-readable
refusal formatting" (`noisemaker_render.cpp:1-15`) — i.e. it is deliberately a single-code-path
wrapper around `tools/benchmark/corpus_case.{hpp,cpp}`'s `compile_case`/`execute_case`, not a
feature-complete rewrite of the JS CLI's convenience layer. The caller must already have a
complete, self-contained `.dsl` program file; there is no server-side program synthesis at all.

### 7.3 The actual gap, verified precisely

The runtime plumbing for external textures is **already fully wired end-to-end** in cpp and
needs no executor change:

- `noisemaker::RenderOptions` **is** `graph::ExecutionInputs` by type alias
  (`include/noisemaker/renderer.hpp:11`), which already declares `std::vector<NamedSurface>
  seed_surfaces` and `external_textures` (`include/noisemaker/graph/executor.hpp:74-84`).
  `GraphExecutor::execute` already copies every entry of both vectors into the resource arena
  with `ResourceLifetime::seed`/`ResourceLifetime::external` before running any pass
  (`executor.cpp:1854-1877`), and `validate_plan_before_allocation` already de-duplicates and
  validates their names (`executor.cpp:813-826`).
- `noisemaker::decode_png(std::span<const std::uint8_t>) -> Surface` already exists,
  symmetric to the already-used `encode_png` (`include/noisemaker/png.hpp:32`).

So the CLI-parity gap for family A's `filter/text`/`synth/media` is **shallow and purely
additive**: `noisemaker_render.cpp` needs (1) a `--input FILE` flag that reads the file's
bytes, calls `decode_png`, and pushes the result into `options.render.external_textures` under
whichever route name(s) the DSL program expects (JS uses the fixed names `imageTex`/`textTex`
for `--input`; cpp's DSL-driven model may not need the JS CLI's implicit dual-binding at all,
since a `.dsl` program can name its own external-texture route explicitly — this needs a design
decision, not just a mechanical port); and (2) a repeatable `--texture NAME=FILE` flag doing
the same for an arbitrary named route. Neither needs any change to `GraphExecutor`,
`ExecutionInputs`, or the resource arena.

The **DSL-program-synthesis convenience layer** (particle-pipeline auto-injection, loop
wrapping, volume-domain wiring, mixer auto-wiring, `--param`, effect-name shortcut commands,
`animate`) is a separate, larger, and lower-priority gap: it is pure ergonomics on top of a
`.dsl` program the caller could always write by hand, and none of it blocks kit *correctness* —
only kit *convenience* (e.g. a hand-authored `.dsl` file for `points/heightGrid` that already
opens with `pointsEmit()` works today without any CLI change; only the bare-effect-name
shortcut needs the synthesis logic). Recommended priority: ship `--input`/`--texture` first
(it's small, and it's a hard blocker for `filter/text`/`synth/media` regardless of how family A
lands), and treat the DSL-synthesis convenience layer as a follow-on once the kit's own smoke
tests reveal whether they need it.

### 7.4 The `synth/media` kit-exclusion trap

Even after `synth/media` is fully ported at the runtime level (its single GLSL pass is already
`"compatible"` per backend_compatibility.json — see family A's report), it will **still** be
absent from cpp's `compat-effects.json` unless `export-kit/generate-compat.mjs`'s unconditional
`effects.delete('synth/media')` (script line ~30, justified by "The shipped CLI renders output
only; it cannot supply media's imageTex") is revisited once `--input`/`--texture` ships. This is
a three-way dependency worth tracking explicitly: runtime port → CLI flag → compat-list
generator rule, in that order, or the kit will keep reporting `synth/media` unsupported after
the first two are done.

