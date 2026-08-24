# Task 14 implementation brief: source-const scalar-local lowering slice

Date: 2026-08-10  
Repository: `.`  
Pinned corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`

## Outcome

After Task 13 is independently approved, add exactly these six typed CPU
factories, and no others, by admitting the narrow source-global form required
by this cohort: initialized, read-only `const float` declarations. The only
such declarations in the six accepted sources are literal `PI` and `TAU`
constants.

1. `filter/pixelSort:finalize`
2. `filter/pixelSort:prepare`
3. `filter/skew:skew`
4. `filter/tetraCosine:tetraCosine`
5. `filter/tile:tile`
6. `synth/osc2d:osc2d`

Every authoritative default define map is exactly `{}`. Grow the typed slice
from 65 to exactly **71** sorted programs, and the public catalog from 67 to
exactly **73** sorted unique factories. Exactly `212 - 73 = 139` corpus
programs must remain without a native public factory. The two immutable
Task-5 legacy factories remain outside typed generation and must not be
duplicated or regenerated.

No Git, branches, worktrees, commits, pull requests, sibling-tree writes,
new runtime dependencies, placeholder kernels, hand-translated shader bodies,
render-graph adapters, per-pixel map/string/variant/allocation/dynamic
dispatch, C++ namespace globals, function-static state, or C++ static storage
are allowed.

## Narrow language contract

This task is source-const lowering only; it is not support for general GLSL
global state.

- Admit a non-interface top-level declaration only when it has the source
  `const` qualifier, exact scalar type `float`, and an initializer. For this
  allowlist, the accepted declarations are exactly literal `PI` and/or `TAU`:
  `PI` in pixel-sort finalize/prepare and skew; `TAU` in tetra-cosine; and
  both `PI` and `TAU` in tile and osc2d.
- Preserve the source initializer as typed IR. Validate it before capability
  validation and emit it using the existing numeric-literal contract; it may
  not bypass semantic or emitter validation.
- Build a stable-symbol dependency graph for every admitted global initializer.
  It must be declaration-ordered, acyclic, and refer only to earlier admitted
  globals. For this six-key slice every initializer is a literal, but the
  implementation must retain this proof rather than relying on text names.
  Reject forward references and cycles.
- Perform a whole-program, symbol-identity write audit over every helper and
  `main`. Reject direct and compound assignment, prefix/postfix increment or
  decrement, and writes through swizzles, indexes, or members targeting an
  admitted source const. Do not infer safety from a spelling match.
- At the beginning of each generated GLSL helper or `pixel` function that
  reads an admitted global, emit the transitive dependency closure as ordinary
  C++ `const` function locals in source dependency order. A helper that reads
  `TAU` gets its own local; `pixel` gets a local only if it reads it. Do not
  emit an unused declaration. The generated code must contain neither C++
  static/global state nor an ambient global lookup.
- Preserve Float32 construction/storage behavior and the current scalar
  numeric-literal contract. The feature adds no compatibility transform and
  no numeric-literal exception.

Everything outside the preceding contract remains rejected: mutable globals,
uninitialized globals, non-`const` globals, `bool`, `int`, `uint`, all
vectors, arrays, matrices, structs, samplers/opaque types, interface globals,
global function/builtin/conditional/index/member expressions, casts outside
the existing emitter rules, globals written indirectly, forward references,
and dependency cycles. Keep all current loop, array/indexing, matrix (beyond
already-admitted local `mat2` behavior), struct, UBO, varying, derivative,
parameter-direction, `textureLod`, `texelFetch`, and unrelated builtin
frontiers closed.

The broad audit found 58 programs whose first blocker is a top-level global;
only these six become validator- and typed-emitter-clean after this exact
lowering. Do not pull in any of the other 52 candidates. In particular,
`filter/adjust`, `filter/colorspace`, `filter/dither`,
`filter/normalMap`, `synth/noise`, and `synth/shape` remain excluded for their
matrix/array/mutable-state requirements.

## Implementation units and TDD order

### 1. Semantic representation and proof

Files to inspect/modify:

- `tools/glslcpp/frontend/semantic.py`
- `tools/glslcpp/frontend/body_semantic.py`
- `tools/glslcpp/frontend/typed_ir.py` only if an immutable dependency/use
  record cannot be represented by the existing `TypedDeclaration.initializer`
- `tests/test_typed_generator.py`

Start with failing parser/semantic tests for an accepted literal `const float`
global read by both a helper and `main`. Require the typed declaration to carry
the initializer and stable symbol identity. Add separate failing fixtures for
each rejection class: missing `const`, missing initializer, `bool`, `int`,
`uint`, vector, matrix, array, struct, sampler, global call, forward reference,
two-node cycle, direct write, `+=`, `++`, swizzle write, index write, and
member write. Then implement the smallest declaration-graph and whole-body
write-audit support that makes only the accepted fixture pass.

The semantic assertion must make the six real sources pass this global gate,
while the audit's remaining global-frontier corpus stays rejected at either
this gate or its already-recorded next frontier. Do not make a source change
to corpus GLSL or metadata.

### 2. Typed emitter lowering

Files to inspect/modify:

- `tools/glslcpp/emit_typed_cpp.py`
- `tools/glslcpp/generate_typed_slice.py`
- `tests/test_typed_generator.py`

First add failing exact-output tests. For a helper reading a source const, the
generated helper must begin with a matching C++ `const` local before its first
use; the generated `pixel` function must do the same independently when it
reads the constant. Assert source dependency order, one materialization per
function, and no materialization in an unused function. Assert the generated
translation unit has no namespace/global/static declaration for the source
constant.

Then implement function-local closure injection from immutable typed IR.
Reuse the ordinary typed expression emitter; do not special-case PI/TAU text
or reconstruct values from the parser. Make malformed/unsupported typed
initializer IR fail with a located `TypedEmissionError` instead of silently
emitting an approximation.

### 3. Schema, generation, and public catalog

Files to inspect/modify:

- `tools/glslcpp/generate_typed_slice.py`
- `tools/glslcpp/typed_slice.json`
- `src/typed_generated/typed_slice.cpp` (generated only)
- `src/typed_generated/typed_manifest.json` (generated only)
- `include/noisemaker/generated/catalog.hpp` (generated declaration surface)
- `tests/test_generated_kernels.cpp`
- `tests/test_typed_slice.cpp`

Add only the six keys, sorted, with `{}` defines. Lock the approved capability
and type vocabularies so the only new language form is this exact source-const
scalar lowering contract; do not add a general `globals` capability that could
authorize mutable or aggregate state. Regenerate through the checked
generator; never hand-edit generated shader bodies.

Add these six public bind declarations and include every address in the
compile/use declaration guard:

```cpp
bind_filter_pixelSort_finalize
bind_filter_pixelSort_prepare
bind_filter_skew_skew
bind_filter_tetraCosine_tetraCosine
bind_filter_tile_tile
bind_synth_osc2d_osc2d
```

Catalog tests must lock exactly 73 sorted unique keys and 139 remaining
unported corpus keys. The generated-slice check must reject a 70/72/140 or
72/74/138 drift, a seventh Task-14 key, non-empty defines, a new compatibility
transform, or a new numeric-literal exception.

### 4. Binding, effect, and oracle tests

Files to inspect/modify:

- `tests/test_glsl_runtime.cpp`
- `tests/test_typed_slice.cpp`
- `tests/test_generated_kernels.cpp`

Write the negative binding matrix before the factory additions. Each declared
uniform and sampler is required by the typed binder even if the authored GLSL
body later does not consume it; test absence and a representative wrong type
for every distinct signature, and every sampler position independently.

The exact source signatures are:

| Key | Required sampler(s) | Required scalar/vector uniforms |
|---|---|---|
| `filter/pixelSort:prepare` | `inputTex` | `resolution: vec2`, `angled: float`, `time: float`, `darkest: bool`, `wrap: float` |
| `filter/pixelSort:finalize` | `inputTex`, `originalTex` | `resolution: vec2`, `angled: float`, `darkest: bool`, `wrap: float`, `alpha: float` |
| `filter/skew:skew` | `inputTex` | `skewAmt: float`, `rotation: float`, `wrap: float`, `tileOffset: vec2`, `fullResolution: vec2`, `renderScale: float` |
| `filter/tetraCosine:tetraCosine` | `inputTex` | `tileOffset/fullResolution: vec2`; `colorMode/rotation: int`; `offsetR/G/B`, `ampR/G/B`, `freqR/G/B`, `phaseR/G/B`, `repeat`, `offset`, `alpha`, `time`: float |
| `filter/tile:tile` | `inputTex` | `tileOffset/fullResolution: vec2`, `symmetry: int`, `scale`, `offsetX`, `offsetY`, `angle`, `repeat`: float, `aspectLens: bool` |
| `synth/osc2d:osc2d` | none | `resolution`, `tileOffset`, `fullResolution: vec2`; `aspect`, `time`, `speed`, `rotation: float`; `oscType`, `frequency`, `seed: int` |

No adapter or render graph is authorized. Pixel-sort prepare is pass 1 and
finalize is pass 6 of its pipeline: prepare consumes caller-provided input;
finalize consumes caller-provided sorted `inputTex` and original `originalTex`.
Its luminance, brightest, rank, and gather passes remain unported. Skew,
tetra-cosine, and tile are independently executable one-pass filters with a
caller-provided input texture. Osc2d is an independently executable texture-
free generator.

## Frozen accepted oracle

Artifact: `docs/port-engineering/task-14-oracles.json`  
SHA-256: `3d77b3d357e697d41fdb6842f78dbc403afa3f317f3c76708e94923b2b52a104`

The controller has frozen schema
`noisemaker-task14-canonical-oracles-v1`, pinned revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, Node `v24.7.0`, and API
`canonicalKernelFactories+bindCanonicalKernel+runPass+Surface`. The oracle
contains exactly 30 unique `(key, variant)` rows; every canonical bind/render
was repeated byte-identically. Do not regenerate, reinterpret, or weaken it.

| Program | Cases | Required branch/effect coverage |
|---|---:|---|
| pixel-sort prepare | 4 | wrap mirror/repeat/clamp/else fallback; darkest false/true; signed and boundary angles; asymmetric sampled inputs |
| pixel-sort finalize | 4 | both sampler routes; wrap mirror/repeat/clamp/else fallback; darkest false/true; alpha `0`, interior, and `1` |
| skew | 4 | wrap clamp/mirror/repeat/else fallback; signed rotation; negative tile offsets; oversized positive and negative skew clamp |
| tetra-cosine | 5 | colorMode RGB/HSV/OkLab/OKLCH/fallback; rotation `-1/0/1` and fallback; alpha `0`, interior, and `1` |
| tile | 5 | symmetry mirrorXY/rotate2/rotate4/hex-rotate6/fallback; aspectLens true/false; non-square tile and full-resolution geometry |
| osc2d | 8 | oscillator types `0..6` plus fallback; signed rotation; time/speed/seed; negative coordinates; `fullResolution < 1` fallback |

Embed all 30 cases. For each, require the exact little-endian Float32 SHA-256,
RGBA8 SHA-256, 9x7 top-down dimensions/orientation, twelve exact RGBA
Float32-bit probes at pixel indices 0, 31, and 62, alpha behavior, and a
byte-identical second render. Recreate the frozen formula surfaces exactly:
tags `1` (5x3), `23` (4x6), `37` (7x2), and `53` (3x5), using the artifact's
byte formula and bottom-left shader sampling/top-down `Surface` storage
contract. Preserve its canonical binding rule that overwrites resolution and
aspect; per-case tile offsets, full resolutions, scalar uniforms, time, and
seed come from the artifact.

## Full acceptance and stop boundary

- Run the complete Python suite plus `check_corpus --check`,
  `check_semantics --check`, legacy-generator drift, and typed-generator drift.
  Preserve 212 bodies / 622 metadata candidates / 646 variants.
- Configure and build fresh strict-warning Debug and Release trees. Run the
  direct native executable and CTest in each.
- Preserve exact Task-5 hashes and all prior oracle suites: Task 11's 94,
  Task 12's 120, and Task 13's accepted cases.
- Write `docs/port-engineering/task-14-report.md` with source-const
  proof details, exact scope/counts, no-static evidence, binding/effect truth,
  oracle provenance, generated hashes, test counts, and exactly 139 remaining
  public-unported corpus programs.
- Stop for independent review before any later language frontier or any
  repository change for Task 15.
