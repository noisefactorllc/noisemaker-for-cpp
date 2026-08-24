# Task 15 canonical oracle report

## Result

The strict Task 15 oracle covers **36** retained counted-loop programs and
**38** render variants.  It projects **107 typed / 109 public / 103 unported**.
The previous 44-key count is not a valid v1 contract: six rows need source
global `const int` lowering, one needs a sampler helper parameter, and one has
effective loop depth four.

## Provenance

- CPU corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`
- Node: `v24.7.0`
- Canonical implementation: `src/effects/generated/canonical-kernels.js`
- Canonical binder: `src/csl/glsl-kernel.js:bindCanonicalKernel`
- Reproducible generator:
  `docs/port-engineering/task-15-oracle-generator.mjs`
- Fixture: 9x7 output, time 0.375, frame 7, delta 1/60, seed 19,
  tile offset [2,1], full resolution [13,11].

Each sampler named by a pass's `inputs` table receives a distinct deterministic
11x9 F32 formula surface.  Each vector is rendered twice by direct canonical
factory binding; F32 output bytes and `Surface.toRgba8()` bytes must match
between the runs.  The JSON records SHA-256 digests and probes at [0,0], [4,3],
and [8,6].

The oracle JSON's `fixture.contract` is normative: it gives the sampler-route
ordering, the 1-based route tag, each top-down 11x9 RGBA formula, storage lane
indices, Float32Array conversion points, fragment inputs, output lane layout,
and double-render check.  Run the generator with `--check` to rebuild all 38
variants and require byte-identical serialized oracle output; use `--write` to
freeze a verified rebuild.

## Boundary coverage

- `filter/reverb:reverb`: defaults plus exact clamp endpoints `iterations=1`
  and `iterations=8` (the latter also enables `ridges`).
- `normalize:reduce`, `normalize:reduceMinmax`, and `cellSplit`: `continue`
  coverage.
- The guarded-break family, `clouds`, `mandala`, `subdivide`, and `mashup`:
  `break` coverage.
- `craquelure`, `lowPoly`, `patchwork`, `scatterSmooth`, `stkPost`, and
  `oilPost`: nested-depth-two coverage.
- Every sampler route is explicitly listed in its vector; multi-sampler passes
  are never silently bound to a shared placeholder.
- `filter/pixelSort:findBrightest`: its retained `NUM_SAMPLES=32` bound is a
  function-local, read-only `const int` initialized directly from an integer
  literal.  It is not one of the deferred source-global const-int cases.

## Deferred keys

`bloom:ntapGather`, `directionalBlur:directionalBlur`, `spinBlur:spinBlur`,
`strokes:stkSmear`, `wind:wind`, and `reindex:nmReindexStats` remain behind
source-global `const int` lowering.  `focusBlur` remains behind sampler helper
parameters.  `gabor` remains above the effective depth cap.  None is present
in the oracle or counted in the projected totals; this does not include
`pixelSort:findBrightest`, whose local constant is covered by the narrow
function-local proof rule above.
