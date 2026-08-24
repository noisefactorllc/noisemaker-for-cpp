# Task 15 — strict counted `for` v1

## Scope

Add the narrow, fail-closed counted-loop feature to `noisemaker-for-cpp`.
This **does not** broaden the port into general global integer-constant
lowering, arbitrary sampler helper parameters, or interprocedural loop-depth
support.  With those boundaries, the audited increment is **36** typed
programs: **107 typed**, **109 public**, and **103 unported**.

This replaces the earlier, invalid 44-key projection.  Eight apparent loop
frontier keys remain deferred: `filter/bloom:ntapGather`,
`filter/directionalBlur:directionalBlur`, `filter/spinBlur:spinBlur`,
`filter/strokes:stkSmear`, `filter/wind:wind`, and
`filter/reindex:nmReindexStats` require unsupported source-global `const int`
lowering; `mixer/focusBlur:focusBlur` has an unsupported `sampler2D` helper
parameter; and `synth/gabor:gabor` reaches effective loop depth four through a
helper call (the v1 cap is three).

## Accepted grammar and proof

The parser and typed IR may admit only:

```glsl
for (int i = L; i < B; i++) { ... }
for (int i = L; i <= B; ++i) { ... }
```

`i` must be a fresh function-local integer; `L` and `B` must be integer
literals (including unary-negative literals), except for (1) the exact local
`int iters = clamp(iterations, 1, 8)` proof in `filter/reverb:reverb`, and
(2) an exact function-local, read-only `const int NAME = INTEGER_LITERAL;`
declaration followed by a stable `NAME` bound read.  The latter admits
`filter/pixelSort:findBrightest`'s local `const int NUM_SAMPLES = 32` only:
the symbol may have no writes, aliases, arithmetic-derived use as a bound, or
top-level/global declaration.  It does not authorize source-global `const int`
lowering.
The induction variable must be on the left of `<` or `<=`; only `i++` and
`++i` are valid updates.  Preserve `break` and `continue` only inside an
already-admitted loop.  Reject loop `return`, `while`, `do`, floating or
external induction, `i += 2`, decrements, swapped tests, dynamic bounds,
`textureSize`, arithmetic-derived bounds, and increment/decrement expressions
outside an admitted loop.

The checked IR must carry the resolved trip bound, lexical and effective
call-stack depth, lexical product, and entrypoint charge.  Recompute before
emission; reject overflow, individual loops above 128, effective depth above
3, nested products above 4,096, and entrypoint charge above 4,096.  The C++
emitter consumes this proof object and must not re-parse source strings.

## Authoritative define maps

The default compile-time define map is *not* uniformly empty.  Preserve these
exact maps in the slice manifest and reject drift:

| Key(s) | Defines |
| --- | --- |
| `filter/morphology:morphA`, `filter/morphology:morphB` | `{ "SHAPE": 0 }` |
| `filter/relief:rlBlurH`, `filter/relief:rlBlurV`, `filter/scatter:scatterSmooth`, `filter/strokes:stkPost`, `filter/hatch:hatch` | `{ "MODE": 0 }` |
| `filter/lowPoly:lowPoly` | `{ "LP_BORDER": 0, "LP_LIGHT": 0 }` |
| `filter/oilPaint:oilPost` | `{ "MODE": 1 }` |

All other admitted keys use `{}`.  Defines are pinned fixture metadata, not a
runtime fallback or a request to add generic preprocessor support.

## 36-key manifest

```text
filter/chrome:chBlurH              filter/chrome:chBlurV
filter/highPass:hpBlurH            filter/highPass:hpBlurV
filter/morphology:morphA           filter/morphology:morphB
filter/photocopy:pcBlurH           filter/photocopy:pcBlurV
filter/plasticWrap:pwBlurH         filter/plasticWrap:pwBlurV
filter/relief:rlBlurH              filter/relief:rlBlurV
filter/stamp:stBlurH               filter/stamp:stBlurV
filter/unsharpMask:usmBlurH        filter/unsharpMask:usmBlurV
filter/craquelure:craquelure       filter/lowPoly:lowPoly
filter/patchwork:patchwork         filter/scatter:scatterSmooth
filter/strokes:stkPost             filter/clouds:clouds
filter/hatch:hatch                 filter/oilPaint:oilPost
synth/gradient:gradient            synth/mandala:mandala
synth/subdivide:subdivide          filter/normalize:reduce
filter/normalize:reduceMinmax      filter/wormhole:blend
mixer/shadow:shadow                synth/cell:cell
mixer/mashup:mashup                mixer/cellSplit:cellSplit
filter/pixelSort:findBrightest     filter/reverb:reverb
```

## Tests and oracle contract

Add parser/semantic negative fixtures for every rejected form above, plus
129-trip, 512x512, and arithmetic-overflow charges.  Add focused lowering
tests for `break`, `continue`, the 16 horizontal/vertical guarded break
passes, nested scans, and the reverb clamp extrema 1 and 8.  Run the retained
36-key manifest through the canonical fixture with every `pass.inputs` route
bound.  Require exact F32 byte hash, exact RGBA8 hash, three F32 pixel probes,
and an immediate repeat render byte match.  The pinned observations are in
`docs/port-engineering/task-15-oracles.json`; regenerate and verify them
with `node docs/port-engineering/task-15-oracle-generator.mjs --check`.
The generator is part of the oracle contract and records route ordering,
top-down F32 lane construction, and all F32 conversion boundaries.

Do not add the eight deferred programs by weakening any of the checks above.
