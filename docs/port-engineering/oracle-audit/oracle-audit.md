# Oracle audit: reserved-canonical-key clobbering defect and related classes

Date: 2026-08-12
Scope: read-only audit of `.` and
`../noisemaker-for-cpu` per operator instruction. No files
were modified in either repo. All artifacts below live under
`docs/port-engineering/oracle-audit/`.

## 1. The verified reserved-key list

Source: `../noisemaker-for-cpu/src/csl/glsl-kernel.js`,
function `createCanonicalBindings`, lines 20-61 (read directly, not
trusted from memory). The binding object is built as:

```
39  return Object.freeze({
40    renderScale: 1,
41    speed: 0,
42    seed: f32(seed),
43    centerLoX: 0,
44    centerLoY: 0,
47    size: new Float32Array(4),
48    motion: new Float32Array(4),
49    ...uniforms,
50    ...textures,
51    resolution,
52    fullResolution: completeResolution,
53    tileOffset: tileOffset ?? new Float32Array(2),
54    aspectRatio: f32(width / height),
55    aspect: f32(width / height),
56    time: f32(time),
57    globalTime: f32(time),
58    deltaTime: f32(deltaTime),
59    frame,
60  })
```

Keys assigned **after** the `...uniforms` spread (line 49) — these silently
clobber any same-named key inside a caller's `uniforms` object:

| # | key | line |
|---|-----|------|
| 1 | `resolution` | 51 |
| 2 | `fullResolution` | 52 |
| 3 | `tileOffset` | 53 |
| 4 | `aspectRatio` | 54 |
| 5 | `aspect` | 55 |
| 6 | `time` | 56 |
| 7 | `globalTime` | 57 |
| 8 | `deltaTime` | 58 |
| 9 | `frame` | 59 |

This is exactly 9 keys and exactly matches (a) the previously-circulated list
in the task brief, (b) `task-31-curl-oracle-defect.md`'s enumeration, and (c)
the live `RESERVED_TOP_LEVEL_KEYS` constant already coded into
`docs/port-engineering/future-precompute/task32-grade/grade_oracle_generator.mjs:115`.
All three sources agree with the source code read directly. **Verified, not
assumed.**

Note: `renderScale`, `speed`, `seed`, `centerLoX`, `centerLoY`, `size`,
`motion` are assigned **before** the spread (lines 40-48), so a same-named key
inside `uniforms` legitimately *overrides* them — that is the intended
mechanism for programs with their own `size`/`speed`/`seed` uniform, not a
defect.

Also note (informational, not itself a defect): `...textures` (line 50) is
spread **after** `...uniforms`, so a texture name that collides with a
uniform name would also silently win over the uniform. No such collision was
observed in any generator audited below.

## 2. Inventory

### 2a. Vendored oracles — `noisemaker-for-cpp/tests/oracles/` (consumed by tests)

| File | Task | Program(s) | Cases | Generator source |
|---|---|---|---|---|
| `task-23-oracles.json` | 23 | bloom, directionalBlur, spinBlur, strokes, vaseline, wind (6 programs) | 19 | `docs/port-engineering/task-23-oracle-generator.mjs` |
| `task-24-oracles.json` | 24 | (single program) | 4 | `task-24-oracle-generator.mjs` |
| `task-25-oracles.json` | 25 | lens (`classicNoisedeck/lensDistortion`), prism (`filter/prismaticAberration`) | 6 (4+2) | `task-25-oracle-generator.mjs` |
| `task-26-oracles.json` | 26 | (single program) | 8 | `task-26-oracle-generator.mjs` |
| `task-27-oracles.json` | 27 | `synth/perlin:perlin` | 8 | `task-27-oracle-generator.mjs` |
| `task-28-oracles.json` | 28 | (single program) | 6 | `task-28-oracle-generator.mjs` |
| `task-29-oracles.json` | 29 | focus/blur (`focalDistance`/`aperture`/`sampleBias`/`depthSource`) | 6 | `task-29-oracle-generator.mjs` |
| `task-30-oracles.json` | 30 | `filter/extrude:extrude` | 6 | `future-precompute/task30/extrude_oracle_generator.mjs` |
| `task-31-oracles.json` | 31 | `synth/curl:curl` | 9 (6 eligible + 3 ineligible) | `future-precompute/task31-curl/curl_oracle_generator.mjs` |

Mapping task-31 → curl (not caustic) was confirmed by comparing
`program.key` inside the vendored JSON (`"synth/curl:curl"`) against both
candidate generators' output, and by byte-diffing the vendored file against a
fresh run of the curl generator (see §3).

### 2b. Draft / not-yet-vendored generators (found under `docs/port-engineering`)

| Generator | Program | Cases | Consumed by any test? |
|---|---|---|---|
| `task-15-oracle-generator.mjs` ... `task-22-oracle-generator.mjs` | various filters | 3–11 each (see `task-NN-oracles.json`) | No — `tests/oracles/` starts at task-23 |
| `task-11` … `task-14` (`*-oracles.json` only, **no generator script found**) | various | large (26k–136k JSON) | No |
| `future-precompute/task31/caustic_oracle_generator.mjs` | `classicNoisedeck/caustic:caustic` | 9 (6 eligible + 3 ineligible) | No (confirmed by grep, see §4) |
| `future-precompute/task32-grade/grade_oracle_generator.mjs` | `filter/grade` cluster (6 programs) | 29 (24 eligible + 5 diagnostic) | No — `filter/grade:lut` hits in `test_typed_generator.py` are unrelated typed-classification tests, not render-oracle consumers |
| `future-precompute/focus_blur_oracle_generator.mjs` | focus/blur | partial/incomplete | No — superseded draft of task-29, confirmed by diff (task-29 is the same program, further along) |

`task31-curl/curl_oracle_generator.mjs.bak` is the pre-fix original of the
vendored task-31 generator (see §3) — kept as historical evidence, not a
separate oracle.

## 3. Task 31 (curl): the documented defect, now FIXED and re-vendored

`task-31-curl-oracle-defect.md` (already in `docs/port-engineering/`,
dated 2026-08-12) is the "already confirmed once" incident named in the task
brief. Re-verified against current state:

- `curl_oracle_generator.mjs.bak` (the broken original) passes `uniforms`
  straight through with no top-level `time`:
  `bindCanonicalKernel(factory, { width, height, uniforms, textures: {}, tileOffset, fullResolution })`
  — `time` lived only inside `uniforms` and was discarded for all 6 eligible
  cases.
- The **current** `curl_oracle_generator.mjs` (non-`.bak`) is already fixed,
  lines 189-199:
  ```js
  const { time: caseTime, ...restUniforms } = uniforms
  const kernel = bindCanonicalKernel(factory, {
    width, height, uniforms: restUniforms, textures: {},
    time: caseTime ?? 0, tileOffset: ..., fullResolution: ...,
  })
  ```
- `diff curl_oracle_generator.mjs.bak curl_oracle_generator.mjs` confirms
  this is the only functional change.
- Running the current (fixed) generator produces
  `future-precompute/task31-curl/curl-oracles.json`, which is **byte-identical**
  to the vendored `noisemaker-for-cpp/tests/oracles/task-31-oracles.json`
  (`diff` → identical, both 51930 bytes, same mtime 2026-08-12 14:16).
- The vendored file's 6 eligible-case F32 hashes exactly match the
  "corrected" column from `task-31-curl-oracle-defect.md`'s proof table
  (e.g. `seed7-tiled-midtime` → `e6f49b49…`, not the broken `a3da792e…`).
- `test_generated_kernels.cpp`'s `kTask31NativeCases` table
  (`TASK31_NATIVE_ORACLE_TABLE_BEGIN`, lines 9492-9558) already carries the
  corrected values: `seed7-tiled-midtime` has `time_bits = 0x40600000`
  (= 3.5f) and `f32_hash = "e6f49b49eb…"`, matching the corrected oracle, not
  the stale broken one.

**Current verdict for task 31 (curl): CLEAN.** It was WRONG-EXPECTATION at
the time the defect memo was written; the generator, the vendored JSON, and
the consuming C++ test table are now mutually consistent and reflect the
fix. (The defect memo separately notes 2 remaining C++-port mismatches
unrelated to this oracle-binding bug — that is a port-correctness question,
out of scope for this audit, and is not re-verified here.)

## 4. Task 31/caustic (draft, not vendored): the SAME defect, UNFIXED

`future-precompute/task31/caustic_oracle_generator.mjs` builds a different
program (`classicNoisedeck/caustic:caustic`) under the same `task31/`
directory. Its `render()` (lines 269-278) has **not** been fixed:

```js
function render(factory, { width, height, uniforms, tileOffset, fullResolution }) {
  const kernel = bindCanonicalKernel(factory, {
    width, height, uniforms, textures: {},   // <-- `uniforms.time` never extracted
    tileOffset: new Float32Array(tileOffset ?? [0, 0]),
    fullResolution: new Float32Array(fullResolution ?? [width, height]),
  })
  ...
}
```

Every eligible case's uniforms literal embeds `time` (lines 300-305), merged
through `fullUniforms(overrides, 10) = {...DEFAULT_UNIFORMS, ...overrides, NOISE_TYPE: 10}`
(`DEFAULT_UNIFORMS.time = 0`, line 208).

**Blast-radius proof** (script:
`docs/port-engineering/oracle-audit/probe_caustic_time_defect.mjs`,
run against the live `canonicalKernelFactories['classicNoisedeck/caustic:caustic']`):
for each of the 6 eligible cases, full-surface F32 SHA-256 was computed three
ways — (a) "broken": exactly what the generator's real `render()` does, (b)
"corrected": `time` destructured to a top-level option, (c) the value
actually frozen in `future-precompute/task31/caustic-oracles.json`.

| Case | intended `time` | frozen == broken | frozen == corrected | broken == corrected (harmless iff true) |
|---|---:|---|---|---|
| simplex-default-seed44 | 0 | **true** | true | true (latent — intended time is already 0) |
| simplex-seed-zero-nowrap | 3.5 | **true** | false | **false — wrong frozen expectation** |
| simplex-large-seed-tiled | 12 | **true** | false | **false — wrong frozen expectation** |
| simplex-negative-intensity-full-hue | 1.25 | **true** | false | **false — wrong frozen expectation** |
| simplex-min-scale-zero-speed | 0 | **true** | true | true (latent — intended time is already 0) |
| simplex-max-scale-large-canvas | 40 | **true** | false | **false — wrong frozen expectation** |

The frozen `caustic-oracles.json` matches the broken (time-forced-to-0)
rendering in all 6 cases, and diverges from the intended-time rendering in
4 of 6 — i.e. the caustic program genuinely reads `time` (speed is nonzero
in the affected cases; `simplex-min-scale-zero-speed` has `speed: 0`
explicitly, which is why it's harmless independent of its `time: 0`).

**Verdict: WRONG-EXPECTATION, 4 of 6 eligible cases** (2 of 6 LATENT —
intended time happened to be 0). **Consuming test: none.** Confirmed by
`grep -rn caustic tests/*.cpp tests/*.py` in `noisemaker-for-cpp` → zero
hits. This file is not referenced by `tests/oracles/task-31-oracles.json`
(that's curl) or by any `.cpp`/`.py` test. It is a landmine only if/when it
gets vendored as a future task's oracle — flagging so it does not ship as-is.

## 5. Per-task verdict table

| Task | File(s) | Cases | Reserved key in `uniforms`? | Blast radius | Verdict |
|---|---|---:|---|---|---|
| 23 | task-23-oracles.json | 19 | none | n/a | **CLEAN** |
| 24 | task-24-oracles.json | 4 | none | n/a | **CLEAN** |
| 25 | task-25-oracles.json | 6 | none | n/a | **CLEAN** |
| 26 | task-26-oracles.json | 8 | none | n/a | **CLEAN** |
| 27 | task-27-oracles.json | 8 | none (see §6a re: `DIMENSIONS`) | n/a | **CLEAN** |
| 28 | task-28-oracles.json | 6 | none | n/a | **CLEAN** |
| 29 | task-29-oracles.json | 6 | none (no `time` use at all) | n/a | **CLEAN** |
| 30 | task-30-oracles.json | 6 | none (no `time` use at all) | n/a | **CLEAN** |
| 31 (curl) | task-31-oracles.json | 9 | **yes, historically** (`.bak`) | 4/6 eligible cases wrong (per defect memo) | **FIXED** — now CLEAN, re-vendored, consuming C++ table updated |
| 31/caustic (draft) | future-precompute/task31/caustic-oracles.json | 9 | **yes, currently, unfixed** | 4/6 eligible cases wrong (proven above) | **WRONG-EXPECTATION** — not vendored, 0 consuming tests |
| 32/grade (draft) | future-precompute/task32-grade/grade-oracles.json | 29 | none — has explicit guard (`assertNoReservedKeysInUniforms`) | n/a | **CLEAN** (reference-quality) |
| 15–22 (drafts) | root `/tmp` `task-NN-oracles.json` | 3–11 each | none found (literal-scan + manual top-level-siblings check) | n/a | **CLEAN**, not vendored |
| 11–14 (drafts) | root `/tmp` `task-NN-oracles.json` | large | **UNVERIFIED — no generator script exists to audit** | unknown | not vendored, no live risk |
| focus_blur (draft) | future-precompute/focus-blur-oracles.json | partial | none found | n/a | superseded by task-29, moot |

## 6. Step 5 — broader sweep

### 6a. Uniform names the program does not declare

Mechanical cross-check
(`docs/port-engineering/oracle-audit/scan_undeclared_uniforms.mjs`):
extracted every literal `uniforms: { key: ... }` key across 19 generators and
compared against each generator's own `'name:type@N'`-style binding-signature
documentation strings. One candidate surfaced: task 27's `DIMENSIONS` key is
absent from its hand-written `binding_signature` doc string.

Verified directly against the **live compiled factory**
(`canonicalKernelFactories['synth/perlin:perlin'].toString()`):

```
var DIMENSIONS = $bindings["DIMENSIONS"];
```

`DIMENSIONS` **is** genuinely read by the shader closure — it is a real,
bindable name in this CPU transpiler (see §6b for why), just omitted from the
generator's own documentation string. Not a defect: the doc-string list is
cosmetic only and consumed by nothing. **No genuinely undeclared/silently-
ignored uniform name was found** across the 19 generators scanned.

### 6b. Declared `defines` vs. what actually compiles

This CPU transpiler does **not** fold `#define`-style GLSL macros into
separate JS closures per define combination — every generated factory reads
them the same way it reads ordinary uniforms, e.g. in
`canonicalKernelFactories['synth/curl:curl']`:

```
var OCTAVES = $bindings["OCTAVES"];
var RIDGES = $bindings["RIDGES"];
var OUTPUT_MODE = $bindings["OUTPUT_MODE"];
```

Spot-checked against curl's 3 "ineligible" cases
(`octaves-2-diverges-loop-unroll`, `output-mode-0-flowx-channel`,
`ridges-false-no-fold`, which merge `def.defines` into `uniforms` and render
through the single pinned `canonical` factory rather than a per-define
recompile): their frozen F32 hashes are all distinct from each other and from
the matching eligible case, confirming the declared defines genuinely reach
and affect the render — not a silent no-op. (Initial suspicion, before
reading the factory text, was that this must be a bug; reading
`glsl-kernel.js`'s sibling factory output disproved it — the `$bindings[...]`
mechanism is generic for both uniforms and defines in this system.)

Every generator audited independently pins `canonical_factory_to_string_sha256`
/ `factorySha256` (or equivalent) against the live factory's `.toString()`
before use, and throws on drift — this is a real, load-bearing self-check
(confirmed present in task-27, task-31-curl, task-32-grade; consistent
pattern elsewhere). This gives generation-time assurance that the declared
`defines` metadata matches what was pinned when the generator was authored,
for the representative files inspected. **Not exhaustively re-verified for
every one of the 19+ generators** — mark the broader claim as spot-checked,
not exhaustively proven; tracing `canonical-kernels.js`'s own generation
pipeline against the `tools/glslcpp` corpus compile step would be needed for
full proof and was judged out of scope for a JS-level oracle audit.

## 7. Scripts used (all under this directory)

- `probe_caustic_time_defect.mjs` — renders the 6 eligible caustic cases
  broken/corrected/vs-frozen, per §4.
- `scan_uniforms_literals.mjs` — bracket-matches every `uniforms: { ... }`
  literal in 21 generator files and flags reserved-key hits (found only in
  curl `.bak`, curl current [inert — stripped before binding], and caustic).
- `scan_undeclared_uniforms.mjs` — cross-checks literal uniform keys against
  each generator's own binding-signature documentation strings (§6a).

## 8. Summary

- Reserved key list: **9 keys**, verified line-by-line against
  `glsl-kernel.js:20-61` — `resolution`, `fullResolution`, `tileOffset`,
  `aspectRatio`, `aspect`, `time`, `globalTime`, `deltaTime`, `frame`.
- **0** vendored/consumed oracles currently contain a wrong frozen
  expectation from this defect class. Task 31 (curl) had it and has been
  fixed and re-vendored, with the consuming C++ test table already updated.
- **1** draft, not-yet-vendored oracle (`task31/caustic`) currently has the
  unfixed defect, 4 of 6 eligible cases genuinely wrong — 0 consuming tests
  today, flagged so it isn't vendored as-is later.
- Step 5 sweep: no genuinely undeclared/silently-ignored uniform names found;
  no defines-vs-compiled mismatch found (spot-checked, not exhaustive).
- Unverified: tasks 11-14 (no generator script exists to audit); task 15
  (uses a different `CpuRenderer.buildBindings`/`passUniforms` code path, not
  `createCanonicalBindings` directly — not traced). Neither is vendored, so
  neither carries live risk today.
