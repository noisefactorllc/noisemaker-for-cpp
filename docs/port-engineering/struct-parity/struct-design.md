# Struct declaration admission — `synth/newton`, `filter/historicPalette`, `filter/palette`

Design investigation for the **struct-declaration bucket**, which
`REMAINING-EFFECTS.md` censuses at 3 programs: `synth/newton:newton`
(first blocker `125:1 unsupported struct declaration`), and the two
double-blocked, adapter-routed members `filter/historicPalette:historicPalette`
(`struct HistoricPalette` at normalized `18:1`) and
`filter/palette:palette` (`struct PaletteEntry` at normalized `21:1`).
Status: **DESIGN — pre-implementation, pre-review.** Nothing lands in this
lane; this document freezes the measured facts, the eligibility verdicts, the
mechanism decomposition and the blocker ladders the implementation slices need.

This document mirrors `cellrefract-parity/cellrefract-design.md` (Amendments
§§11-17), `varying-parity/varying-design.md` and `effects-parity/effects-design.md`
(their 2026-08-17 review sections bind: companion-module absent-set carves;
the `generate_typed_slice.py`-style second consumption sites; measure never
transcribe; mutant satisfiability before budgeting; per-key records, never
shared strings for whole-program freezes). **Every figure below was MEASURED
this session (2026-08-16/17)** against the pinned corpus
`a024dc3a960cc44af454abc7aebce50456c194e6`, the frozen JS authority snapshot at
`$RUN_ROOT/oracle/noisemaker-for-cpu` (the six family CPU-file pins re-verified
unchanged, §1.4), and an `rsync`'d copy of `tools/` under the shared run root
(`workers/struct/copy`; all destructive probes in the copy; the live tree —
which carries the uncommitted cellRefract integration plus parallel
kaleido/effects/wobble lane edits — was only read). None of the figures is
transcribed from any design.

**Probe state:** the working slice had **186 rows / 44 capabilities**
(cellRefract landed, row 186; typed-list SHA-256 at 186 rows
`1f4e8a51182aa8d71954a48f0b810b4732478e6e61ed14241c37446278102c21` over sorted
keys joined by `\n` with trailing newline). First-blocker and ladder probes ran
per-program `analyze_program` + `validate_capabilities` / `render_typed_cpp`
against that slice in the copy — never `generate_outputs` with a one-row slice.
Gate line numbers cited below are from the session copy; the live tree moves
under the parallel lanes, so the **messages and normalized-source locations are
the stable identifiers**.

## 0. Summary of the load-bearing verdicts

1. **Both palette adapters are algorithm-identical to their corpus GLSL, and
   their data is mechanically derived from it — the corpus rows are PORTABLE.
   The bucket's portable size is 3, not 1.** The generator script itself parses
   the struct tables out of the GLSL source (hard cardinality asserts 21 / 55)
   and emits them as the adapters' data module; my independent value-for-value
   diff is exact, and a numeric differential of the actual shipped adapters
   against an independent GLSL-faithful reimplementation is **bit-exact on
   207,360 / 207,360 cases** (§1). This is *not* the fractal class: fractal's
   adapter implements a different algorithm; these adapters are the same
   algorithm in a different representation.
2. **newton needs far more than struct declaration.** Measured validator
   ladder: struct declaration → `out` parameters → struct types in signatures →
   member access → local `vec2[8]` array → indexed stores → `log`/`log2`
   builtins → capability vocabulary → CLEAN (§4.1). Emitter ladder adds the
   bare-void-call statement gap (the documented wcSimplify class) and an
   **out-parameter silent-pass hazard** — the emitter has no `out`-direction
   gate at all (§4.2, §0.5).
3. **The bucket's two struct families are different mechanisms (and a third
   exists outside the bucket).** newton's is *function-scope struct plumbing*
   (declaration, constructor, struct return, struct local, member reads,
   member swizzles); the palette pair's is *const file-scope arrays of
   structs plus dynamic (uniform-derived) indexing* — the colorLab/moodscape
   index class's first concrete admission. A corpus-wide sweep found exactly
   four struct programs (§3.5): these three plus `synth/julia` (behind a
   counted-for first blocker, adapter eligibility unprobed, a third
   sub-shape). Like the global-declaration bucket before it, this bucket
   decomposes, and the const-struct-array family deserves its own slice (§9).
4. **The palette programs' JS authority is the adapter, and its numeric
   contract is load-bearing and unusual: the struct tables are consumed as
   plain binary64 doubles, never f32-narrowed.** Wrongly staging the table as
   `FloatExpr` f32 lanes — exactly what the emitter's generic constructor path
   produces — measurably diverges from the shipped adapter on 951 / 25,920
   palette cases by 1 f32 ulp (§3.3). The emission shape must be a frozen
   double table, not per-pixel struct constructors.
5. **Emitter silent-pass hazard:** `emit_typed_cpp.py`'s parameter ABI path
   handles direction only inside the authenticated `inout`-swap arm
   (`emit_typed_cpp.py:3105,3118` in the session copy). An `out` parameter
   that the validator admitted would be emitted **by value with no gate** —
   compiles, runs, silently wrong. newton's slice must add an
   identity-authenticated out-parameter arm (§3.4).
6. **`log`/`log2` are in no vocabulary and no identity list.** Recommended
   admission shape: the `tanh` precedent (`curl-vector-math-tanh-wide-mod-v1`
   — authenticated nodes only, *never* the capability vocabulary), not
   vocabulary growth (§5, M10).

## 1. Adapter eligibility resolution (done first — it decides the bucket's size)

Method: read the routing and the adapters in the frozen JS snapshot, read the
corpus GLSL, diff the data mechanically, then run a numeric differential of
the **actual shipped adapters** (imported from the snapshot, not transcribed)
against an **independent GLSL-faithful reimplementation**.

### 1.1 The routing facts

- `tools/glslcpp/check_corpus.py:28` — `_ADAPTERS` is exactly
  `{classicNoisedeck/fractal:fractal, filter/historicPalette:historicPalette,
  filter/palette:palette, synth/julia:julia}` (read from source, not the doc).
- `src/effects/catalog.js:14` — `kernelFactories = new Map(Object.entries({
  ...canonicalKernelFactories, ...canonicalAdapterFactories }))`: adapter
  factories **override** canonical ones. Measured by import:
  `kernelFactories.get('filter/historicPalette:historicPalette') ===
  canonicalAdapterFactories['filter/historicPalette:historicPalette']` →
  `true` (same for `filter/palette:palette`), and
  `canonicalKernelFactories` owns **neither** key — grep of the 612-factory
  registration block finds no entry. **There is no canonical factory for
  either program; the adapter is the only shipped authority.**
- `scripts/upstream/compile-glsl.js:34-45` — the `adapters` set lists both
  keys; `glsl-coverage.js` records `status: "adapter", generatedBytes: 0` for
  both (`historicPalette` at `:660-667`, `palette` at `:899-906`). The
  generator never attempted to transpile them: the transpiler **cannot lower
  a constant array of structs** (its own comment at `compile-glsl.js:437-439`:
  "glsl-transpiler cannot lower a constant array of structs and silently emits
  constant vec4 arrays as empty arrays"), and the one program it did lower
  structurally (`filter3d/palette3d`) needed a bespoke selector-function
  rewrite (`lowerPaletteStructArray`, `compile-glsl.js:304-333`).
- **newton fresh check: NOT adapter-routed.** `synth/newton:newton` is absent
  from `_ADAPTERS`, `glsl-coverage.js:2470-2476` records `status: "generated"`
  (generatedBytes 9,010), and the canonical factory exists:
  `"synth/newton:newton": canonicalFactory264`
  (`canonical-kernels.js:36444`). The generator applies exactly two
  source-level adaptations to newton (`compile-glsl.js:423-428`), both
  swizzle-of-struct-member lowerings (`p.center.xy` →
  `vec2(p.center.x, p.center.y)`, same for `.zw`) — see §3.2.

### 1.2 The data is mechanically derived from the corpus GLSL

`compile-glsl.js` parses the struct tables **out of the same GLSL sources the
corpus pins**, with hard cardinality asserts (`compile-glsl.js:72-87`):

```js
function parsePaletteEntries(source) {
  source = source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '')
  const entries = []
  const entry = /\bPaletteEntry\s*\(\s*(vec4\([^)]*\)\s*,\s*…\s*\)/g
  for (const match of source.matchAll(entry)) entries.push(parseVectorList(match[1], 'vec4', 4))
  if (entries.length !== 55) throw new Error(`Expected 55 canonical cosine palettes, found ${entries.length}`)
  return entries
}
// parseHistoricPaletteEntries is the same shape with vec3 ×5 and length 21.
```

The result is written to `src/effects/generated/canonical-adapter-data.js`
(`compile-glsl.js:635-638`), which the hand-written adapter consumes. **My
diff, value for value** (paren-matching parser over both sides):

- `historicPaletteData`: 21 entries × 15 components — **IDENTICAL** to the 21
  `HistoricPalette(vec3,vec3,vec3,vec3,vec3)` initializers.
- `paletteData`: 55 entries × 16 components — **IDENTICAL** to the 55
  `PaletteEntry(vec4,vec4,vec4,vec4)` initializers (including the `amp.w` mode
  lane: RGB=0, HSV=1, OkLab=2).

Content pins (SHA-256 over the minimal-JSON serialization of the parsed
doubles; re-derive with the same canonical form when amending):

| Table | Shape | Content SHA-256 |
| --- | --- | --- |
| `historicPaletteData` | 21 × 15 doubles | `1bf935623b41d4a2e169ebbebe076631d59205f3eba74e120c0a9716727734f4` |
| `paletteData` | 55 × 16 doubles | `388fb1699962ee64066659f70b0c629e759ba22a405e1638e47f7de5b0fcadab` |

### 1.3 The algorithm is the same — side by side, load-bearing sites

`src/effects/adapters/palette.js` (5,283 bytes, SHA-256
`8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452`) against
the corpus GLSL. Every branch, constant and expression order matches:

| # | Corpus GLSL | Adapter (`palette.js`) |
| --- | --- | --- |
| 1 | `float t = lum * (1.0 - 1e-4) * repeat + offset * 0.01; if (rotation == -1) t += time; else if (rotation == 1) t -= time; t = fract(t);` (`historicPalette.glsl:265-271`) | `let t = lum * (1 - 1e-4) * $bindings.repeat + $bindings.offset * 0.01; if ($bindings.rotation === -1) t += $bindings.time; else if ($bindings.rotation === 1) t -= $bindings.time;` then `sampleHistoric(historicPaletteData[index], fract(t), …)` (`palette.js:126-129`) |
| 2 | `vec3 result = mix(pal.color1, pal.color2, b1); result = mix(result, pal.color3, b2); … result = mix(result, pal.color5, b4);` (cascade, `historicPalette.glsl:226-229`) | `out[0] = entry[0]; … for (colorIndex 1..4) out[c] = mix(out[c], entry[colorIndex*3+c], blends[colorIndex-1])` — same association order (`palette.js:95-104`) |
| 3 | wrap block: `d = (lum > 0.5) ? (lum - 1.0) : lum; wrapFactor = smoothstep(-bw, bw, d); wrapColor = mix(pal.color5, pal.color1, wrapFactor); wrapMask = 1.0 - smoothstep(0.0, bw, abs(d)); result = mix(result, wrapColor, wrapMask);` (`:233-242`) | `distance = lum > 0.5 ? lum - 1 : lum; … wrapColor = mix(entry[12 + channel], entry[channel], wrapFactor); out[channel] = mix(out[channel], wrapColor, wrapMask)` (`palette.js:105-113`) — `entry[12+c]` is `color5`, `entry[c]` is `color1` |
| 4 | `return clamp(offset + amp * cos(TAU * (freq * t + phase)), 0.0, 1.0);` (`palette.glsl:493`) | `color[channel] = clamp(entry[8 + channel] + entry[channel] * Math.cos(TAU * (entry[4 + channel] * t + entry[12 + channel])))` (`palette.js:74`) |
| 5 | `x = c * (1.0 - abs(mod(hp, 2.0) - 1.0));` + the six `hp < N` branches + `return rgb + vec3(m);` (`palette.glsl:427-453`) | `x = c * (1 - Math.abs((hp - 2 * Math.floor(hp / 2)) - 1))` (`mod(hp,2)` expanded exactly) + the same six branches via `out.set([c + m, x + m, m])` etc. (`palette.js:23-34`) |
| 6 | `return mix(high, low, step(linear, vec3(0.0031308)));` with `low = linear * 12.92`, `high = 1.055 * pow(linear, vec3(1.0/2.4)) - 0.055` (`palette.glsl:477-481`) | `return value <= 0.0031308 ? value * 12.92 : 1.055 * Math.pow(value, 1 / 2.4) - 0.055` — the same `step`/`mix` collapsed; boundary case equal (`palette.js:36-38`) |
| 7 | oklab chain `lab.g*-0.509+0.276`, `lab.b*-0.509+0.198`, l₁/m₁/s₁ coefficients, cubes, the 4.0767… matrix, `clamp(…,0,1)` (`palette.glsl:456-489`) | identical constants and order (`palette.js:40-53`) |
| 8 | `if (paletteIndex <= 0 \|\| paletteIndex > PALETTE_COUNT) { fragColor = inputColor; return; }` (passthrough, `palette.glsl:506-509`) | `if (paletteIndex <= 0 \|\| paletteIndex > paletteData.length) { $runtime.writeColor(input, out); return; }` (`palette.js:63-67`) |
| 9 | `uv = gl_FragCoord.xy / texSize; inputColor = texture(inputTex, uv)` (both programs) | `context.fragCoord[0] / $bindings.inputTex.width` … `$runtime.stdlib.texture($bindings.inputTex, […])` (`palette.js:59-62, 120-123`) |
| 10 | index: `int idx = clamp(paletteIndex, 0, PALETTE_COUNT - 1)` / `PALETTES[paletteIndex - 1]` | `Math.min(Math.max($bindings.paletteIndex \| 0, 0), historicPaletteData.length - 1)` / `paletteData[paletteIndex - 1]` (`palette.js:68, 124`) |
| 11 | `blendedColor = mix(inputColor.rgb, paletteColor, alpha); fragColor = vec4(blendedColor, inputColor.a);` | `out[c] = Math.fround(mix(input[c], color[c], alpha)); out[3] = input[3]` per lane (`palette.js:79-83, 130-134`) |

The only GLSL statement with no adapter counterpart is
`vec2 globalCoord = gl_FragCoord.xy + tileOffset;` — **declared and never
read** in both GLSL mains (dead code; `tileOffset`/`fullResolution` are
declared-but-unread uniforms in both programs and stay required ABI bindings
per the Shapes precedent). The adapter's `smoothstep` carries one guard the
GLSL does not — see §1.5.

### 1.4 The numeric differential: bit-exact

Both shipped adapters were imported from the frozen snapshot and run through a
stub runtime (`beginPixel` noop; `stdlib.texture` returning a controlled
`Float32Array(4)` pixel; `inputTex = {width: 16, height: 16}`), against an
independent reimplementation of the corpus GLSL algorithm staged exactly where
the adapter stages (working color in a `Float32Array(3)`; final lanes
`Math.fround`).

- **historicPalette — 181,440 cases bit-exact, 0 differ**: every one of the 21
  palettes × smoothness {0, 0.25, 1} × rotation {−1, 0, 1} × repeat {1, 2.7} ×
  offset {0, 37} × time {0, 12.34} × alpha {0, 0.5, 1} × 40 input pixels
  (black, white, 38 deterministic pseudo-random).
- **palette — 25,920 cases bit-exact, 0 differ**: paletteIndex {0, 1, 12, 16,
  40, 43, 50, 55, 56} (both passthrough arms 0/56, HSV entries 12/16, OkLab
  entries 40/43/50) × the same knob sweep × 40 pixels.
- Method note (the honest staging lesson): a first run in which my
  reimplementation kept the mode-conversion results (`hsv2rgb`/`oklab2rgb`)
  as doubles — instead of narrowing them into the adapter's `Float32Array`
  staging, which is also what GLSL `vec3 finalColor = hsv2rgb(...)` does at
  the vec3 store — differed on **951 / 25,920 cases by exactly 1 f32 ulp**.
  With the staging matched, 100% bit-exact. That 951-case witness is the
  numeric-contract evidence behind §3.3's emission decision.

### 1.5 One defined edge worth pinning: `smoothstep(e, e, x)`

The adapter's helper guards the degenerate edge
(`palette.js:17-21`):
`if (edge0 === edge1) return value < edge0 ? 0 : 1`. The runtime's
transpiled `smoothstep` has **no such guard**
(`glsl-runtime.js:360-363` — `(value - e0)/(e1 - e0)` → NaN at e0 == e1), and
GLSL itself leaves `smoothstep(e, e, x)` undefined. At `smoothness = 0`
(blendWidth = 0 — **the default binding** for historicPalette per the
upstream params) all four cascade blends hit this edge. The shipped behavior
is the adapter's hard step; the port must reproduce **that**, and the oracle
must carry a `smoothness = 0` case (the default-binding arm) or the port's
most common runtime mode is untested. My differential covered smoothness = 0
bit-exactly (both sides hard-step).

### 1.6 Factory provenance pins (method cross-validated)

`Function.prototype.toString` SHA-256s, computed against the frozen snapshot.
The method reproduces the family's frozen cellRefract pin exactly
(`canonicalFactory3` → `329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3`,
matching `cellrefract186-oracles.json:322`). New pins for this bucket:

| Factory | bytes | SHA-256 |
| --- | ---: | --- |
| `canonicalFactory264` (`synth/newton:newton`, canonical) | 10,572 | `7e4e95cfd6afa9f89e24920dbb06cd3af6f90f0c83f4329e302f701b78bba7af` |
| `historicPaletteFactory` (adapter) | 1,039 | `f6ff289a0f93e4ddaa5a2f77b0ec4e3645d52007acbaf1f38c0081965adbf7d5` |
| `paletteFactory` (adapter) | 1,408 | `547bb6741b27cc12d6ed488cd1bbe12284ab3b916cdaefe1c747a63125523040` |

CPU-file pins re-verified unchanged against the snapshot (the six the family
freezes): `canonical-kernels.js` 1,713,290 B `66adc01c…`, `catalog.js` 733 B
`d8cf3122…`, `glsl-kernel.js` 2,217 B `a684b1bc…`, `glsl-runtime.js` 21,331 B
`a20421c5…`, `pass-runner.js` 3,916 B `fbfd5347…`, `surface.js` 2,823 B
`0cd69c92…` (full values in `cellrefract186_oracle_generator.mjs:104-111`).
This bucket additionally freezes two **new** authority files:
`src/effects/adapters/palette.js` (hash above) and
`src/effects/generated/canonical-adapter-data.js` (5,266 B, SHA-256
`ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab`).

### 1.7 Verdict

**Bucket portable size = 3.** historicPalette and palette are portable with
the adapter as oracle authority — a *new oracle-generator check shape* (M11,
§5): the family's `kernelFactories.get(key) === canonicalKernelFactories[key]`
assert inverts for these two keys to
`kernelFactories.get(key) === canonicalAdapterFactories[key]`, plus
`canonicalKernelFactories` must **not** own the key, plus
`check_corpus._ADAPTERS` (parsed from live source) **must** contain it — the
exact inverse of the cellRefract generator's three adapter checks. The
eligibility caveat that motivated this section is resolved by measurement, but
the *conclusion is recorded here, not silently absorbed*: any future upstream
regeneration that changes the adapter or the data module breaks the frozen
pins above and must re-run this differential.

## 2. Frozen authority — per-program facts (all three measured)

Measured with `_whole`/`_interface`/`_node_census`/`_declaration_inventory`/
`_call_graph`/`_reachability` from `mutable_global_frame_profile.py`, against
the pinned corpus. Manifest cross-check: every raw/normalized byte+SHA figure
below equals the manifest's `raw_bytes`/`raw_sha256`/`normalized_*` fields.

### 2.1 `synth/newton:newton`

| Fact | Value (measured) |
| --- | --- |
| Source | `sources/synth/newton/newton.glsl` |
| Raw bytes / SHA-256 | 10,325 / `603090e299ccb08fd4db4bf54a2aa6668ed81be971a84a8b679c7f560e5c27ac` |
| Normalized bytes / SHA-256 | 7,747 / `c021c2f8c0e8df9b0fe92b97d24d532a5d3ccfe44c0e8a75bba4a11cabcc5af8` |
| Defines (via `_defaults`) | `()` — none |
| Whole / interface SHA-256 | `8227557b0a1d006eed470c004d3cd9975fae2036836753f5e7f6c4d52c5c9ef2` / `1c7426e6e2b7dd22b0695ed3610c02071dc4b2acae1878dc965f79eadfe95985` |
| Node census | 804 nodes / 34 assigns |
| Declarations | 26 — 22 uniforms (3 `vec2` + 19 `float`), `out fragColor` (id 24), 3 const floats `PI`/`TAU`/`PHI` (ids 25-27, normalized 29:1-31:1) |
| Functions | 13, ids 61-73 — 10 `df64_*` helpers, `getPOI` (71), `main` (72, normalized 148:1-314:2), `transformCoords_df64` (73) |
| Structs | **1** — `POIData` id 1, normalized span `125:1-129:3` (the first-blocker site); fields `center` vec4 (57, 126:5), `deg` float (58, 127:5), `maxZoom` float (59, 128:5) |
| Call graph / reachability | 22 edges; **all 13 functions reachable**, none unreachable |
| Resources | uniforms `(resolution, tileOffset, fullResolution, time, degree, relaxation, iterations, tolerance, poi, centerHiX, centerHiY, centerLoX, centerLoY, zoomSpeed, zoomDepth, degreeSpeed, degreeRange, relaxSpeed, relaxRange, rotation, outputMode, invert)`; no samplers; outputs `(fragColor)`; no texture; no derivatives |
| Counted loop proof | `(4, 0, 2, 4000, 8008, acyclic)` — 4 proved loops (`205:5`, `221:5`, `227:9`, `270:9`), 0 unproved; all inside `COUNTED_FOR_V1_MAX_*` (trip 512 / product 262,144 / charge 262,656) — **loops are the expected drop-path** |

Load-bearing signature facts: `df64_cmul` (id 62, normalized `98:1`) has
parameters `(44 ar, 45 ai, 46 br, 47 bi` in`, 48 rr, 49 ri` **out**)`;
`transformCoords_df64` (id 73, `107:1`) has `(50…54 in`, `55 re_df, 56 im_df`
**out**`)`; `getPOI` (id 71, `131:1`) **returns `POIData`** and takes one
`int idx` (60). All `df64_*` helpers take and return `vec2` (the df64 hi/lo
pair) by value.

### 2.2 `filter/historicPalette:historicPalette`

| Fact | Value (measured) |
| --- | --- |
| Source | `sources/filter/historicPalette/historicPalette.glsl` |
| Raw bytes / SHA-256 | 12,528 / `cc0feb09e2f90505766a0b8b0d61ca0cf83a1121ec7b104eea5ff806c9ce0c33` |
| Normalized bytes / SHA-256 | 6,963 / `69d0af70c74a07e9f2d72aeeb7c1495aa353a8a9ebcba0331a655dde7ac9f4b0` |
| Defines | `()` — none |
| Whole / interface SHA-256 | `672d66def0c9c097b61112b7269138d9043459a1236fdccd809960c56b9c8e32` / `081b9b3704841a1cde78cb4d90e8a70e946e150c3ac0ce790d7a26d5205c5072` |
| Node census | 643 nodes / 8 assigns |
| Declarations | 13 — 10 uniforms (`tileOffset`, `fullResolution` vec2; `inputTex` sampler2D; `paletteIndex` **int**, `rotation` **int**, `smoothness`, `offset`, `repeat`, `alpha`, `time` float), `out fragColor` (12), `const int PALETTE_COUNT` (18, 26:1), **`const HistoricPalette PALETTES[21]`** (19, `27:1-196:3`, the first-blocker site) |
| Functions | 2 — `main` (23, `241:1-275:2`), `sampleHistoricPalette` (24, `199:1-239:2`) |
| Structs | **1** — `HistoricPalette` id 1, normalized `18:1-24:3`; fields `color1..color5` all vec3 (ids 13-17, `19:5-23:5`) |
| Call graph / reachability | 1 edge (`main → sampleHistoricPalette`); both reachable |
| Resources | samplers `(inputTex)`; outputs `(fragColor)`; texture yes; derivatives no |
| Counted loops | none (proof `(0, 0, …, 0)`) |
| Status | **adapter** (`glsl-coverage.js:660-667`); oracle authority = `historicPaletteFactory` (§1) |

### 2.3 `filter/palette:palette`

| Fact | Value (measured) |
| --- | --- |
| Source | `sources/filter/palette/palette.glsl` |
| Raw bytes / SHA-256 | 15,189 / `03ab3914862807288f7d5f6d2cbe8907cfa66fd1bb80b02df509880292967c09` |
| Normalized bytes / SHA-256 | 12,914 / `5e233dee16d462d5a93b30f95f2fc480ba5165bdab8a01bd6dc87c4285fa8b9f` |
| Defines | `()` — none |
| Whole / interface SHA-256 | `8004434e834b93616bc3bb0ba573fce427fc3f166431412cec5da18bc4241ee1` / `b4f6276de7b670e30c0d7a4b806e3de6fa1943eb7d24cff358592d5769382c79` |
| Node census | 1,521 nodes / 15 assigns |
| Declarations | 16 — 9 uniforms (same shape as historicPalette minus `smoothness`), `out fragColor` (11), `const int MODE_RGB/MODE_HSV/MODE_OKLAB` (12-14, `17:1-19:1`), `const int PALETTE_COUNT` (19, 28:1), **`const PaletteEntry PALETTES[55]`** (20, `29:1-415:3`), `const float TAU` (21, 417:1) |
| Functions | 6 — `cosinePalette` (31, `485:1`), `hsv2rgb` (32, `420:1`), `linear2srgb` (33, `470:1`), `main` (34, `489:1-541:2`), `oklab2linear` (35, `449:1`), `oklab2rgb` (36, `477:1`) |
| Structs | **1** — `PaletteEntry` id 1, normalized `21:1-26:3`; fields `amp`, `freq`, `offset`, `phase` all vec4 (ids 15-18, `22:5-25:5`) |
| Call graph / reachability | 5 edges (`main → cosinePalette/hsv2rgb/oklab2rgb`; `oklab2rgb → linear2srgb/oklab2linear`); all 6 reachable |
| Resources | samplers `(inputTex)`; texture yes; derivatives no |
| Counted loops | none |
| Status | **adapter**; oracle authority = `paletteFactory` (§1) |

Sorted insertion neighbors (measured against the 186-row working slice;
re-check at insertion): `historicPalette` between
`filter/highPass:hpCombine` (57) and `filter/hs:hs`; `palette` between
`filter/outline:outlineValueMap` (77) and `filter/patchwork:patchwork` (78);
`newton` between `synth/modPattern:modPattern` (177) and `synth/osc2d:osc2d`
(178).

## 3. The struct mechanism

### 3.1 Sub-shape decomposition (the census, measured)

"Struct declaration" is one message over **structurally different shapes** —
the same planning error the global-declaration bucket was post-mortemed for.
Measured node census (walker over every function body and every declaration
initializer; `construct` nodes whose `constructor_type.kind == "struct"`,
`member` nodes, `index` nodes with struct-array bases):

| Sub-shape | newton | historicPalette | palette |
| --- | :-: | :-: | :-: |
| S1 struct **declaration** | 1 (`POIData`, 125:1) | 1 (`HistoricPalette`, 18:1) | 1 (`PaletteEntry`, 21:1) |
| S2 struct **constructor** in reachable code | 7 (getPOI stmts 0-6, `135:26`-`141:12`, 3 children) | 0 | 0 |
| S3 struct **constructor in a const table initializer** | 0 | 21 (`29:5`-`189:5`, 5 children each) | 55 (`31:5`-`404:5`, 4 children each) |
| S4 **struct-typed return** | 1 (`getPOI`) | 0 | 0 |
| S5 **struct-typed parameter** (by value) | 0 | 1 (`pal`, `199:28`) | 0 |
| S6 struct **local** from a call | 1 (`POIData p = getPOI(poiIdx)`, sym 101) | 0 | 0 |
| S7 struct local from a **dynamic table index** | 0 | 1 (`HistoricPalette pal = PALETTES[idx]`, sym 33) | 1 (`PaletteEntry entry = PALETTES[paletteIndex-1]`, sym 54) |
| S8 **whole-member read** (vec-typed member, no swizzle) | 0 | 7 (`pal.color1..color5`, `220:23`-`232:42`) | 0 |
| S9 **member + swizzle chain** | 2 (`p.center.xy`/`.zw`, `176:15`/`177:15`) | 0 | 5 (`entry.amp.xyz` ×2, `.w`, `freq/offset/phase.xyz`, `519:20`-`522:91`) |
| S10 **scalar-member read** | 2 (`p.deg` `178:21`, `p.maxZoom` `179:39`) | 0 | 1 (`int(entry.amp.w)` via S9) |
| S11 **dynamic (uniform-derived) index** into the struct array | 0 | 1 (`PALETTES[idx]`, `268:27`, idx = clamp(int-uniform, 0, 20)) | 1 (`PALETTES[paletteIndex - 1]`, `516:26`) |

Two families, exactly as the task suspected:

- **newton = function-scope struct plumbing** (S1, S2, S4, S6, S9, S10) plus
  unrelated companions (out params, void calls, `vec2[8]`, log/log2).
- **the palette pair = const file-scope arrays of structs** (S1, S3, S5/S7,
  S8/S9, S11) — a *different sub-shape* from newton's local structs, and
  itself two sub-shapes (historicPalette's whole-vec3 member reads and
  by-value struct parameter vs palette's member-swizzle chains and
  arithmetic dynamic index).

### 3.2 JavaScript materialization — the authority, quoted

**newton** — `canonicalFactory264`, `canonical-kernels.js:31627-31929`
(toString pin §1.6). The transpiler materializes the struct as a **plain
object literal with typed members**, constructed per return site:

```js
function getPOI (idx) {
  if (idx == 2) {
  return {
  center: new $runtime.PooledFloat32Array([0.25, 0.4330126941204071, 0, 7.771800092370995e-9]),
  deg: 3,
  maxZoom: 14
  };
  };
  …  // 6 further object literals, identical shape
```

- The `vec4` member is a **pooled f32 array** (per-lane f32 at construction —
  note `7.7718e-8` became `7.771800092370995e-9`'s f32 double spelling);
  the **scalar members are plain Numbers** — int-valued doubles (`3`, `14`).
- Member reads are lane/property reads: `p.deg`, `p.maxZoom`,
  `p.center[0..3]`. The two `p.center.xy`/`.zw` swizzles were **rewritten by
  the generator** (`compile-glsl.js:423-428`) into constructors —
  `vec2.add([], new $runtime.PooledFloat32Array([p.center[0], p.center[1]]), …)`
  — numerically identical to a swizzle (lane reorder); the port may keep the
  corpus swizzle form. Record the adaptation as an authority note, not an
  obligation.
- **Out params**: the transpiler copies results into the caller's arrays and
  stashes them — `df64_cmul` body ends
  `df64_sub(df64_mul(ar, br), df64_mul(ai, bi)).reduce((res,el,i)=>(res[i] = el, res), rr); …
  df64_cmul.__out__ = [rr, ri];` and the **call site** is a comma expression
  `(df64_cmul(pwr, pwi, zr_df, zi_df, tr, ti), [tr, ti] = df64_cmul.__out__, df64_cmul.__return__)`
  with the out arrays pre-allocated fresh at the call site
  (`var tr = new $runtime.PooledFloat32Array([0, 0]), ti = …`). This is JS's
  multiple-return workaround; reference semantics underneath — the port's
  plain `Vec2&` parameters are the exact analog.
- **Bare void-call statements**: 3 frozen nodes — `transformCoords_df64(…)` at
  `197:5`, `df64_cmul(…)` at `230:13` (inside the j-loop) and `237:9` (z^n),
  all in `main`. This is the documented wcSimplify class
  (`REMAINING-EFFECTS.md` "Recommended order" item 3: the emitter "fails with
  no support for a bare void-call statement").
- **df64 numeric contract** (the reason this program exists): every `df64_*`
  helper returns `new $runtime.PooledFloat32Array([s, e])` — **hi/lo lanes are
  f32**; all intermediate arithmetic (`a + b`, `4097 * a`, the two-prod
  residual) is plain-double; vec parameters get `$runtime.copy` (by value);
  const float literals are f32-narrowed at factory scope — `var PI =
  3.1415927410125732; var TAU = 6.2831854820251465; var PHI = 1.6180340051651;`
  and `1e-20` became `9.999999682655225e-21` (while `1e10` stayed
  `10000000000`, exactly representable). The house `FloatExpr` per-lane
  double-compute/f32-store machinery is exactly this contract.
- **Local array**: `var roots = [new $runtime.PooledFloat32Array([0, 0]), ×8];`
  with per-lane induction stores `roots[k][0] = cos(angle)`.
- `log`/`log2` route to `Math.log`/`Math.log2` (`glsl-runtime.js:341-342`) —
  V8; see §5 M10 for the C++ routing decision.

**historicPalette / palette** — the **adapters** are the authority (§1); there
is no factory materialization of these GLSL sources. The shipped
materialization of the const struct array is:

```js
import { historicPaletteData, paletteData } from '../generated/canonical-adapter-data.js'
…
export function paletteFactory($bindings, $runtime) {
  const color = new Float32Array(3)   // factory scope, reused per pixel
  return function paletteKernel(context, out) { … }
}
```

- The tables are **module-scope frozen arrays of plain doubles**
  (`Object.freeze([...]).map(Object.freeze)`) — parsed from the GLSL (§1.2),
  **never f32-narrowed**: `0.56851584` is consumed as the binary64 double.
  Arithmetic is plain-double until the explicit staging points: the working
  `color` is a `Float32Array(3)` (per-channel narrowing at each store,
  including the in-place `hsvToRgb`/`oklabToRgb` writes), and the final mix
  lanes get `Math.fround` (`out[c] = Math.fround(mix(input[c], color[c], alpha))`).
- **This is the load-bearing staging decision.** Staging the table as f32
  lanes (what a naive struct-of-`Vec3` emission or the emitter's generic
  `FloatExpr` constructor path produces) diverges from the shipped adapter on
  951 / 25,920 palette cases by 1 f32 ulp (§1.4). The port's obligation is
  the adapter, so the table must be **doubles**.

### 3.3 Emission shape

**newton** — a real C++ struct type, the natural shape (the JS object literal
is its exact analog), per-namespace as the Frame precedent:

```cpp
struct POIData final { glsl::Vec4 center; double deg; double maxZoom; };
[[nodiscard]] POIData getPOI(/*…state, context,*/ std::int32_t idx) noexcept {
  if (idx == 2) return POIData{glsl::Vec4(static_cast<float>(0.25), …), 3.0, 14.0};
  …
}
```

`center` is `glsl::Vec4` (f32 lanes, matching the pooled member); `deg`/
`maxZoom` are `double` (JS Numbers; `deg` feeds the double `effDegree`
pipeline, `maxZoom` the double `min`). Member reads lower as
`p.center`/`p.deg`; the two member swizzles lower through the existing
swizzle machinery (`glsl::swizzle<0,1>(p.center)`), with the JS
constructor-rewrite recorded as an authority note. `out` parameters lower as
`glsl::Vec2&` (new arm, §0.5); the 3 void-call statements lower as ordinary
calls through the §12-arm pattern widened to the frozen 3-node identity list;
`roots` as `std::array<glsl::Vec2, 8> roots{};` with per-lane induction
stores. No `Frame`-style shared state exists here — the struct is
function-scope only — so no frame parameter changes; **the public ABI gains
nothing** (bindings only; §7).

**historicPalette / palette** — **per-field lowering onto a frozen double
table, not a struct-of-Vec3 type.** Recommended shape (namespace scope, the
C++ analog of the adapter's module-scope frozen arrays):

```cpp
// historicPalette (21 × 15), palette (55 × 16) — frozen, content-hashed (§1.2)
static const std::array<std::array<double, 15>, 21> PALETTES{{ /*…*/ }};
```

`PALETTES[idx]` lowers to a row reference; member reads lower to lane
offsets into the row (`pal.color3` → `row[6..8]`), consumed as doubles; the
per-channel working color stages f32 exactly at the adapter's staging points
(the `color` local and the fround'd out mix). This deliberately does **not**
reuse the per-pixel `source_global_locals` re-evaluation path that
`const-global-nine-table-v1` uses: re-emitting 21/55 struct constructors per
pixel is both wasteful and — via the generic `FloatExpr` constructor —
numerically wrong against the adapter (§1.4's 951-case witness). A
namespace-scope static also sidesteps the `beginPixel` scratch-aliasing
question entirely (normalMap §15) and matches the adapter's
allocate-once-at-module-load materialization. The probe run confirmed the
**wrong-by-default** shape concretely: with the gates bypassed, the emitter's
generic path emits `const /*PaletteEntry[55]*/ PALETTES =
/*PaletteEntry*/(glsl::FloatExpr<4>(static_cast<float>(0.76), …), …)` per
pixel — f32 lanes, parenthesized call syntax — which is precisely what the
admission must not do.

Struct-typed parameters and locals (S5/S7) lower as row references/locals of
the table's row type (`const std::array<double, 15>& pal`); a `struct
HistoricPalette` C++ type is optional sugar with no numeric role — **the
numeric contract is the double table plus the staging points**, and the
per-key locks should freeze the contract, not the sugar.

### 3.4 ABI

No public-ABI signature changes for any of the three programs: the generated
`pixel(const KernelState&, const glsl::PixelContext&, glsl::Vec4&)` signature
is untouched; structs, out-params, tables and void calls are all
namespace-internal. Binding surfaces (from the upstream params records,
measured):

- **newton** — 22 bindings: `resolution`/`tileOffset`/`fullResolution` Vec2;
  the other 19 via `get_number` (GLSL declares all as `float`; params
  metadata types `poi`/`iterations`/`degree`/`outputMode` int and `invert`
  boolean are Number-valued at the JS boundary — `invert > 0.5`,
  `iterations|0`; pin the exact generated State variants at implementation,
  never transcribe).
- **historicPalette** — 10: `inputTex` texture; `tileOffset`/
  `fullResolution` Vec2; `paletteIndex`, `rotation`, `smoothness`, `offset`,
  `repeat`, `alpha`, `time` numbers. Note `repeat` is params-int but GLSL
  `uniform float` — a Number either way at the boundary.
- **palette** — 9: same minus `smoothness`.

### 3.5 Per-key locks (the profile module)

One dict-keyed module per family (the `mutable_global_frame_profile.py`
shape), per-key records with individually deletable predicates, value checks
ordered **ahead of** node identity (the `Symbol` self-absorption trap):

- Source identity: raw/normalized bytes+SHA (§2), caller `source_hash`,
  empty defines tuple, whole/interface fingerprints (§2).
- Inventory: declarations (ids/names/types/storage/spans), functions
  (id/name/return/param tuples incl. directions), resources, call-graph edge
  tuple, reachability, node census, counted-loop proof tuple (newton).
- **Struct census by identity** (§3.1's table, frozen per key): the struct
  declaration (id, name, field ids/names/types/spans); every constructor node
  (span, child-count, child kinds); every member node (base type, field
  name, span); member-swizzle chains (the swizzle letters live in the
  swizzle node's `member` field); the index nodes and their **index
  expressions** (newton: loop induction; hp: clamped int; pal:
  `paletteIndex - 1` arithmetic); newton's out-parameter signature tuples and
  the 3 void-call nodes; newton's `vec2[8]` declaration + store/read
  census; the log/log2 node spans (2 sites: `290:29` log2, `290:34` log —
  the smooth-iteration expression).
- **The data tables as content** (palette pair): cardinality (21×15 / 55×16),
  the §1.2 content SHA-256, and spot-value locks on load-bearing entries
  (per-program: e.g. palette #2's `0.56851584` amp lane; the four OkLab
  entries' `amp.w == 2.0`; every entry's `freq.w/offset.w/phase.w == 0.0`
  where the GLSL writes `vec4(…, 0.0)`).
- **Materialization contract records** (value-before-identity): newton —
  `center` = f32-lane member, `deg`/`maxZoom` = double members, factory
  literal f32 spellings (`PI = 3.1415927410125732` etc.); palette pair —
  `table_numeric_contract = "plain binary64 doubles, never narrowed before
  arithmetic"`, `staging = "color Float32Array(3) per channel; fround at out
  mix"`, and the **smoothstep-edge contract** (hard step at e0 == e1,
  §1.5).
- **Sibling-proof absent-sets** (the review's generic lesson): freeze exactly
  which companion carriers are absent per key; check every companion module
  this bucket's rows sit beside for the absent-set carve (the effects review
  found `ceil_admission_profile.py`'s the hard way). All three programs carry
  **no** auto-attached proofs today (`fixed_array_in_parameter_proof` /
`fixed_affine_centers13_proof` attach as None — measured), so the initial
  absent-sets are empty; the locks must still *name* them empty.
- Corpus-wide auto-attach census, **measured over all 212 programs**: exactly
  **four** programs carry structs — this bucket's three, plus
  `synth/julia:julia` (`struct JuliaResult`, normalized `161:1`, 7 scalar
  float fields `iter/zMag2/dzMag2/stripeSum/stripeCount/stripeLast/trapMin`;
  a struct **return** (`juliaIterate`, `185:1`), a struct local, and **four
  struct-typed parameters** (`outputSmoothIteration`/`outputDistanceEstimation`/
  `outputStripeAverage`/`outputOrbitTrap`, each `JuliaResult r`)). julia
  censuses behind a *counted-for safety charge* first blocker (`297:5`,
  re-confirmed live this session), not behind struct declaration, so it is
  not a member of this bucket — but it is a **future consumer of M1/M2 and a
  third struct sub-shape** (scalar-field-heavy, struct-return, struct-params;
  the newton family without tables and the palette family without arrays).
  Its adapter eligibility (`juliaFactory`) was **not probed here** — out of
  this bucket's first-blocker scope — and must be resolved by the same §1
  method before any julia slice. Every other corpus key proves None.

## 4. Blocker ladders (bypass method, both authorities)

Method: the `rsync`'d copy with each rejecting raise conditioned on an env
flag (or a placeholder return for type/name gates), rung by rung, per
program. **These bypasses admit nothing** — they reveal gate order only.
Emitter "CLEAN" terminations are with placeholder lowering (not compilable
C++); the effects-lane scope note applies: real arms may surface further
gaps. Gate line numbers are session-copy values.

### 4.1 Validator (`validate_capabilities`)

| Rung | newton | historicPalette | palette |
| --: | --- | --- | --- |
| 0 | `125:1 unsupported struct declaration` | `27:1 unsupported global declaration` | `29:1 unsupported global declaration` |
| 1 | `98:52 unsupported parameter direction out` | `27:49 unsupported global initializer type HistoricPalette[21]` | `29:46 unsupported global initializer type PaletteEntry[55]` |
| 2 | `131:1 unsupported typed type POIData` | `27:49 unsupported global initializer expression construct` | `29:46 unsupported global initializer expression construct` |
| 3 | `176:15 unsupported typed expression member` | `18:1 unsupported struct declaration` | `21:1 unsupported struct declaration` |
| 4 | `204:10 unsupported typed type vec2[8]` | `27:1 unsupported typed type HistoricPalette[21]` (array-kind arm) | `29:1 unsupported typed type PaletteEntry[55]` (array-kind arm) |
| 5 | `208:9 unsupported typed expression index` | `27:1 unsupported typed type HistoricPalette[21]` (final type-vocabulary arm) | `29:1 unsupported typed type PaletteEntry[55]` (final arm) |
| 6 | `290:29 unsupported builtin log2` | `268:27 unsupported typed expression index` | `516:26 unsupported typed expression index` |
| 7 | `missing capabilities log, log2` | `220:23 unsupported typed expression member` | `519:20 unsupported typed expression member` |
| 8 | **CLEAN** (with log/log2 admitted) | **CLEAN** | **CLEAN** |

Readings worth recording:

- The palette programs' const-int globals (`PALETTE_COUNT`, `MODE_*`) and
  const-float `TAU` pass rung 0 through the existing
  `source-global-literal-int` / const-float arms — only the struct-array
  declaration rejects. newton's `PI`/`TAU`/`PHI` pass unchanged.
- The capability rung is the frozen 44-entry `APPROVED_CAPABILITIES` equality
  (both `unknown capability` and `missing capabilities` fire); the ladder
  modeled coherent vocabulary growth. `log`/`log2` are in **no** vocabulary
  and **no** identity list — newton would be their first appearance (§5 M10).
- Everything else the three programs use is already admitted: `mat2`
  constructor and `mat2*vec2` (newton's `transformCoords_df64`), `pow` on
  vec3, `step`, `mod`, `smoothstep`, `textureSize`, `clamp` on ints, int
  casts, `sin`/`cos`/`sqrt`/`floor`/`min`/`mix`/`fract`/`abs`.

### 4.2 Emitter (`render_typed_cpp`) — independent authority

| Rung | newton | historicPalette | palette |
| --: | --- | --- | --- |
| 0 | `1:1 unsupported typed type POIData` (signature return-type resolution; span-less node) | `27:1 unsupported source global declaration` | `29:1 unsupported source global declaration` |
| 1 | `176:15 unsupported typed expression member` | `1:1 unsupported typed type HistoricPalette` (struct parameter type) | **KeyError 20** (`source_global_locals` dependency walk — see below) |
| 2 | `197:5 only typed assignments are admitted` (**bare void call**, the wcSimplify class) | `220:23 unsupported typed expression member` | `516:26 unsupported typed expression index` |
| 3 | `204:10 unsupported fixed-nine array declaration` (`vec2 roots[8]` local) | **KeyError 19** (same dependency-walk site) | **CLEAN** (146 lines, placeholders) |
| 4 | `208:9 unsupported typed expression index` (induction store) | `268:27 unsupported typed expression index` | — |
| 5 | `290:34 unsupported builtin log` | **CLEAN** (88 lines, placeholders) | — |
| 6 | **CLEAN** (301 lines, placeholders) | — | — |

Two emitter-specific discoveries beyond the validator's list:

1. **`source_global_locals` is a second consumption site the const-global
   admission must feed** (the `generate_typed_slice.py:1456`-class lesson,
   emitter-side): the per-pixel const-global re-emission walk consults
   `source_global_dependencies[symbol]` for every referenced source global
   (`emit_typed_cpp.py:3028-3035` session copy). With the declaration
   hypothetically admitted, the walk **KeyErrors on the table symbol**
   (19 / 20) — an unhandled crash, not a gate. A real admission must record
   the table's (empty) dependency closure there — or, per §3.3, route the
   table to a namespace-scope static and leave this walk untouched, which is
   the recommended shape and removes the site entirely.
2. **The out-parameter silent-pass hazard** (§0.5): no rung fires for
   direction at the emitter — the generic parameter path returns
   `self.function_type(parameter.type)` for any direction. The validator
   rejects `out` today, so nothing reaches it; the moment a carrier admits
   newton's out params, the emitter would emit them **by value** — compiles,
   runs, silently wrong. The emitter needs its own identity-authenticated
   out-parameter arm (`glsl::Vec2&`) with its own RED test, per the
   independent-authorities rule.

Also measured: the emitter's generic `construct` arm lowers a struct
constructor as `Type(child, …)` once `type()` resolves a name (works through
the placeholder), and dynamic `PALETTES[paletteIndex - 1]` lowers to a plain
subscript `(state.paletteIndex - std::int32_t(1))` once the index gate is
admitted — the shape composes; the numeric content is what §3.3 fixes.

### 4.3 What was not probed

- Compilable emission (the ladders stop at gate closure with placeholders;
  real arms' lowering — swizzle-over-member, struct returns, out-param
  references — may surface further grammar or C++-compile gaps, the §17
  class).
- The `used`-capability census internals for an identity-admission shape of
  log/log2 (the `tanh`/`floatBitsToUint` precedent arms were located at
  `generate_typed_slice.py:4518-4545` session copy but the census wiring was
  not read end-to-end).
- Historical-reconstruction churn under either log/log2 admission option
  (identity: none expected; vocabulary: every frozen capability-tuple record
  moves — not measured).
- The tile-vs-full crop identity for the palette pair (the cellRefract §15
  lesson: program-shaped, probe at oracle time; both programs sample through
  `fragCoord/texSize` with `tileOffset` unread — budget nothing until
  probed).
- `log`/`log2` V8-vs-libm bit-exactness (the `pow`/`atan2` precedent
  resolved the same question by oracle measurement; §8).

## 5. Mechanism decomposition, cost ranking, recommended order

| # | Mechanism | Programs | Status |
| --- | --- | --- | --- |
| M1 | Struct declaration admission (the `structs` gate + declaration-side type arms) | all 3 | **new** |
| M2 | Struct plumbing grammar: struct types in signatures (return `getPOI`; param `pal`), struct constructors (S2), struct locals (S6/S7), member nodes (S8/S9/S10) | all 3 | **new** |
| M3 | Out parameters (`df64_cmul` ×2, `transformCoords_df64` ×2 — all `out vec2`) | newton | **the lightLeak/mandelbrot mechanism** — first landing here or there |
| M4 | Bare void-call statements (3 frozen nodes) | newton | **§12-arm widening** (identity-gated node list, cellRefract precedent) |
| M5 | Local `vec2[8]` array + induction-indexed stores/reads | newton | **new** (local-array write side; the fixed-nine/FAP precedents cover literal stores and parameter reads, not induction writes into a plain local array) |
| M6 | `log`/`log2` builtins (2 sites) + capability admission | newton | **new**; recommend the `tanh` identity-admission shape (no vocabulary growth) |
| M7 | Const file-scope **array of structs**: declaration, table initializer (21/55 struct constructors), element type admission | hp, palette | **new** — the `const-global-nine-table-v1` family's struct generalization, with a different materialization (§3.3: namespace-scope double table, **not** per-pixel re-eval) |
| M8 | Dynamic (uniform-derived) index into the const struct array | hp, palette | **new** — the colorLab/moodscape index class's first concrete admission |
| M9 | Adapter-side oracle authority (inverted factory checks, two new pinned authority files) | hp, palette | **new oracle-generator shape** |
| M10 | Loop admission | newton | **expected drop-path** — `(4, 0, 2, 4000, 8008)` all proved, inside caps; confirm by RED probe |

**Cost ranking (measured basis).** newton carries M1-M6 (five companions);
historicPalette carries M1+M2(param/whole-member forms)+M7+M8+M9 (four);
palette carries the same as historicPalette plus member-swizzle chains and a
55×16 table (four, marginally dearer). But cost is not program count:

- M3+M4 are **shared investments** — `lightLeak` and `mandelbrot` both need
  `out`/`inout`, and the wcSimplify void-call gap is documented as "needed 19
  times" for that bucket. newton's slice pays for machinery that unlocks two
  more programs in the 9-row counted-for bucket.
- M6 via identity admission is cheap and churn-free; via vocabulary growth it
  disturbs every frozen capability-tuple record — take the identity path.
- M7+M8 have no precedent carriers to extend (normalMap's table carrier is
  frozen to nine-element literal scalar arrays with exactly-three-reads
  locks; the dynamic index is admitted nowhere). They are a genuine
  two-mechanism design of their own — which is exactly why §9 recommends the
  const-struct-array family as its own slice, not as newton's tail.

**Recommended order:**

1. **newton first** (`newton-struct-v1`-class carriers; row after
   `synth/modPattern`, insertion index 178). It is the only member whose
   authority is the standard canonical-factory oracle shape (no M9), its
   struct family is the smaller mechanism set (M1+M2 pure grammar — no
   tables, no dynamic indexes), its ladder is fully enumerated at both
   authorities (§4), and its companions M3/M4 are the counted-for bucket's
   next mechanisms anyway. The §0.5 out-param emitter arm is a
   correctness-critical discovery best landed with its first consumer.
2. **historicPalette second** (introduces M7+M8+M9 on the smaller table
   21×15, the simpler member shape (S8 whole-member reads, no swizzle
   chains), and the clamped index form).
3. **palette third** (extends the same carriers: 55×16 table, S9
   member-swizzle chains, arithmetic index, hsv/oklab branches — all
   admitted grammar except the carriers it shares with historicPalette).

**Explicitly deferred (§9): the const-struct-array family (M7/M8/M9) as its
own design pass** if resourcing forces a split — newton's slice must not
reach for it, and the palette pair must not be bundled with newton's
out/void/local-array work. One mechanism family per slice, the
global-declaration post-mortem's rule.

## 6. Proof composition sketch (RED/GREEN)

Both authorities independently call the authenticators; admission **by object
identity** into per-mechanism consumed sets; visitation ledgers (the
three-gate discipline); every authenticated node consumed exactly once per
authority.

1. Row absent: the live boundaries of §4 rung 0 at both authorities
   (newton: validator `125:1` / emitter `1:1`; hp: `27:1`/`27:1`; pal:
   `29:1`/`29:1`) — already reproduced this session.
2. Row present, carrier absent: each module's `exact … profile carrier
   required` at both authorities.
3. **Foreign-carrier sweep**: every sibling profile string × every row field
   at both authorities; record which neighbouring guard answers first (the
   collision-chain trap); claim only rows tested. newton's row carries its
   struct carrier alone (plus the M4 node list and M6 identities inside the
   same module); the palette rows carry the struct-array carrier — check
   every const-global/mutable-array/frame companion's absent-set for the
   carve (the effects-review lesson; at minimum
   `const_global_table_profile.py`, `mutable_global_frame_profile.py`,
   `mutable_global_array_profile.py`, `ceil_admission_profile.py`,
   `scalar_uint_xor_profile.py`).
4. Per-lock mutations (value checks before identity; refreeze surrounding
   hashes; assert the coarse/identity messages did **not** fire): wrong
   raw/normalized hash; ±1 declaration/function/struct/field; the struct
   renamed/field-reordered/field-retyped; each constructor child altered
   (arity ±1, non-vec child, literal value perturbed — table spot locks);
   each member site renamed/retargeted; the index expression altered (clamp
   bounds, off-by-one `paletteIndex`, newton's loop bound); newton: an out
   param flipped to `in`, a 4th void call inserted, `roots` widened to 9,
   a log site changed to `exp`; palette: a table entry's mode lane flipped
   (RGB→OkLab — changes the conversion arm), one vec3 lane perturbed.
5. **Delete-the-check sweep**: one predicate at a time from each module
   source in the scratch copy; every deletion reddens a named test;
   sub-clause pairs for `or`-chains; tabulate.
6. Sabotage tests for every visitation ledger, both authorities — including
   the emitter's out-param arm (delete the direction check → the RED test
   that catches by-value emission must fire, since no generic gate would).
7. Auto-attach census: structs prove present for exactly the four §3.5 keys
   and None for the other 208 corpus programs.
8. newton loop drop-path: confirm no loop carrier fires (M10's RED probe).

## 7. Oracle sketch

Per family, in the shape/normalMap/cellRefract pattern: `--cpu-root` required
and realpath'd; refuse the live checkout, containment either way,
inside-C++-repo roots; per-file SHA-256 import closure; the pinned CPU-file
hash set (§1.6 — the palette oracles add `adapters/palette.js` and
`canonical-adapter-data.js`); GLSL bytes/SHA pinned; stable path placeholder,
absolute-path rejection.

**newton** (`canonicalFactory264`): factory identity
`kernelFactories.get(key) === canonicalKernelFactories[key]`; factory name
and toString SHA (§1.6); `canonicalAdapterFactories` must not own the key;
`check_corpus._ADAPTERS` must not contain it (the family checks, unchanged).

- Cases: `poi` 0-6 (manual + all six POIs — each selects a different table
  row and zoom cap; `pentaSpiral5` exercises the df64 low words);
  `outputMode` 0/1/2 × `invert` (all three value maps + inversion);
  `degree` 3-8 sweep (root count 3-8 — drives the inner-loop trip counts and
  the `roots` writes/reads); `iterations` at bounds 10/500 (loop charge);
  `tolerance` sweep (convergence + the smooth-iteration `log2(log/log)`
  expression — the M6 sites are reachable only when a root converges);
  `zoomSpeed` on/off; `relaxation` 0.5/2; `rotation` ±180 (the mat2 path);
  center offsets including df64-scale magnitudes (zoomDepth ≥ 7 where the
  low words matter).
- **Mutants — satisfiability/distinguishability verified before budgeting**
  (normalMap §11/§12): candidates (verify bit-difference on ≥1 case before
  budgeting): `df64_two_prod` split constant perturbed (4097 → 4093 —
  perturbs every hi/lo split; verify discrimination at high zoom where df64
  precision is observable), `smoothIter` formula dropped (the log2/log
  expression), `getPOI` table entry perturbed (one POI's center lane),
  `convergedRoot` index off-by-one, `bailout` constant perturbed,
  `transformCoords` angle sign flipped. Expected-invariant control to
  *record, not budget*: a perturbation of the unused `resolution` uniform
  (declared-but-unread — the port must not read it; its invariance is the
  witness).
- ABI: 22 bindings (§3.4); omit-each / wrong-variant-each with
  `KernelBindingError` naming the binding; extras ignored; exact alpha
  (`fragColor = vec4(vec3(value), 1.0)` — alpha constant 1); determinism;
  independent output storage.

**historicPalette / palette** — the adapter-side authority (M9):
`kernelFactories.get(key) === canonicalAdapterFactories[key]` **inverted**
checks — `canonicalKernelFactories` must not own the key;
`check_corpus._ADAPTERS` parsed from live source **must** contain it (the
inverse of the family's census); adapter factory name + toString SHA (§1.6);
the adapter-data module hash and the §1.2 table content pins re-derived at
generation.

- historicPalette cases: `paletteIndex` 0 (clamp low arm) and every 1-21
  (each row is a distinct case — cheap, exhaustive, and each isolates one
  table row); `smoothness` **0 (the default — the §1.5 edge)**, 0.25, 1;
  `rotation` −1/0/1; `repeat` 1/10; `offset` extremes; `time` sweep (drives
  `fract(t)` across the wrap seam — the wrap block is reachable only with
  `smoothness > 0` and `t` straddling 0/1); `alpha` 0/0.5/1.
- palette cases: `paletteIndex` 0 and 56 (both passthrough arms) plus every
  1-55; one HSV entry (12 `darkSatin`, 16 `ghostly`), three OkLab entries
  (40/43/50), several RGB entries with non-trivial lanes (2 `fiveG`, 17
  `grayscale` freq=2, 39 `sherbetDouble`); `rotation`/`offset`/`repeat`/
  `alpha` sweeps as above.
- Mutants (verify before budgeting): single table-lane perturbations (each
  discriminates exactly its palette case — satisfiability near-guaranteed,
  but verify per normalMap's bit-identical-mutant lesson; e.g. a
  `freq.w`-lane perturbation should be invariant everywhere since `freq.w`
  is never read — record as invariance witness, do not budget);
  `smoothstep`-edge guard removed (NaN vs hard step at smoothness 0 —
  discriminates on most pixels); cascade order swapped (`b2` before `b1`);
  wrap block dropped; `mode` dispatch arm swapped (HSV↔OkLab — discriminates
  only on the 5 conversion entries); `1e-4` guard dropped (aliases bright
  pixels — the GLSL comment's own stated hazard); f32-staged table variant
  (the §1.4 wrong staging — expected to differ on ~3.7% of palette-program
  cases; a strong lock for the double-table contract).
- Crop/tile: probe before asserting anything (§4.3).

## 8. Risks and expected discoveries

- **Emitter-side grammar behind the placeholders** (§4.3): the real arms for
  struct returns, member swizzles, out-param references and induction
  stores may gap like §12/§17 did — each discovery is an amendment; the
  standing lesson is that the emitter is an independent grammar.
- **The out-param silent pass** (§0.5) is the single most dangerous finding:
  it fails *open* at the emitter. The RED test for the emitter arm must
  delete the arm's direction check and see a test fail — the generic suite
  would stay green without it.
- **`log`/`log2` numeric routing**: V8's `Math.log`/`Math.log2` vs the C++
  side. House precedent (`pow`/`atan2` → platform libm, bit-exact against
  oracles; `sin`/`cos`/`exp`/`tanh` → the fdlibm port because V8 differs
  there) says: route `glsl::log`/`glsl::log2` to `f32(std::log/…)` and let
  the oracle measure; if any case differs, the fdlibm-kernel amendment is
  the fix (fdlibm.hpp explicitly does *not* reimplement log today).
- **`log2` of the smooth-iteration expression only fires when a root
  converges** — case design must ensure convergence (small `tolerance`,
  low-degree roots), or M6's second site is untested.
- **newton's `int(iterations)` uniform bound**: the counted-loop proofs
  cover it (M10 drop-path), but a define or binding that made `maxIter`
  exceed 500 would change nothing (loop caps at 500) — worth one invariance
  case, not a lock.
- **Parallel lanes**: the live tree's `generate_typed_slice.py`/
  `emit_typed_cpp.py`/`typed_slice.json` are being modified by the
  kaleido/effects/wobble lanes while this design is frozen against the
  186-row copy. Every integration site cited here must be re-located at
  implementation; the **messages and normalized locations are the stable
  identifiers**.
- `Symbol` span self-absorption, whole-program-census blind spots in global
  initializers (struct table initializers are exactly such initializers —
  the walker-extension warning applies to the new censuses), and the
  collision-chain unreachability trap all apply; §3.5/§6 embed the
  countermeasures.

## 9. Deliberately deferred

1. **`synth/julia`'s struct** — a fourth struct program exists (§3.5) behind
   a counted-for first blocker in another bucket. Deferred because (a) its
   first blocker is not struct declaration, (b) its adapter eligibility is
   unprobed, and (c) its sub-shape (7 scalar fields, struct return, 4 struct
   params) is a *third* family that should extend the M1/M2 carriers with its
   own per-key records, not ride along on either landed family.
2. **The const-struct-array family (M7/M8/M9) as its own slice** —
   recommended structure, not merely permission: it is two precedent-free
   mechanisms plus a new oracle authority shape, none of which newton needs;
   bundling them with newton's out/void/local-array work would repeat the
   global-declaration bucket's one-unit-of-work planning error.
3. **`filter3d/palette3d`** — outside this corpus/bucket (a 3d program), but
   noted: upstream already solved its struct-array lowering with selector
   functions; if the C++ port ever needs a dynamic-index fallback shape, that
   is the upstream precedent, *not* the adapter's flat table (which is what
   the two 2d programs' authority actually does).
4. **The tile-vs-full crop identity probes** for all three programs —
   oracle-lane work (§4.3), with cellRefract §15 binding: probe, measure,
   record identity or non-identity; cite no precedent.
5. **newton at non-default bindings beyond the sweep** (e.g. `zoomDepth` 14
   with POI maxZoom 7 clamping interactions) — case-design work for the
   oracle lane, enumerated axes in §7 but not probed here.

## 10. Explicit answers to the two framing questions

**Does newton need anything besides struct declaration?** Yes — six further
mechanisms, all enumerated by measurement (§4.1): (1) `out` parameters
(validator rung 1; plus the emitter's missing gate, §0.5); (2) struct types
in signatures — `getPOI`'s `POIData` return (rung 2); (3) member-access
grammar (rung 3); (4) the local `vec2 roots[8]` array declaration (rung 4);
(5) induction-indexed stores/reads on it (rung 5); (6) `log`/`log2` builtins
plus their capability admission (rungs 6-7) — plus the emitter-only bare
void-call statement gap (3 nodes) behind the struct work. Loops need nothing
(proved, within caps). What is at `125:1`: the normalized `struct POIData
{…}` declaration line (raw `newton.glsl:143-147`); what follows it in the
normalized source is `getPOI` at `131:1` — the struct return — then, in gate
order, everything in §4.1's table.

**The bucket's portable size: 3.** Both adapter-routed members pass
eligibility with the strongest evidence class available — mechanical data
provenance from their own GLSL plus a 207,360-case bit-exact differential
against the shipped adapters (§1) — with the adapter (not any canonical
factory) as their oracle authority, one new oracle-generator check shape
(M9), and one load-bearing numeric contract the emission design must honor
(§3.3: frozen double tables, never f32 lanes).

## 11. Ownership for the implementation slices

- **newton slice**: record lane (`tools/glslcpp/frontend/struct_plumbing_profile.py`
  or the family's naming convention — new module, dict-keyed from birth);
  integration lane (`generate_typed_slice.py` struct gate + type arms +
  out-param gate + log/log2 identity arms; `emit_typed_cpp.py` member arm +
  out-param arm + §12-arm widening + local-array arm; `typed_slice.json`);
  oracle/native lane (`newton_oracle_generator.mjs`, oracles JSON, include +
  materializer, `tests/test_generated_kernels.cpp` census — read the live
  assertion at implementation, never carry it forward).
- **palette-family slice** (separate): record lane (struct-array carrier
  module); integration lane (const-global admission arms ×3 sites, the
  `source_global_locals` decision per §3.3, dynamic-index arms, both
  authorities); oracle lane (adapter-side generator checks M9, two new
  pinned authority files, the smoothness-0 default case).
- Serialization: the newton slice lands first; the palette-family design pass
  (extending this document's §§3.3, 5 M7-M9 into a full cellrefract-style
  design with its own review) starts only after newton's gates exist; the
  shared run root and pre/post manifests per the standing storage rules.
