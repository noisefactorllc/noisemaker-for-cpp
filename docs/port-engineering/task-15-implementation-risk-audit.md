# Task 15 implementation-risk audit

Date: 2026-08-10  
Repository inspected: `.`  
Approved baseline: completed Task 14 tree, 71 typed / 73 public / 139 unported  
Input audit: `docs/port-engineering/loop-frontier-audit.md`  
Input SHA-256: `4501fe47e66cf6cf507759065edde0ccfde9e72013e0d5fe2159e7882f163e3f`

## Conclusion

The audit's 44-key membership arithmetic reconciles, but the 44-key set is not
a loop-only Task 15 against the approved Task 14 tree. Eight keys must be
deferred to keep the next increment confined to the stated bounded-loop
frontier:

- Six require top-level `const int` source-global lowering, which Task 14
  expressly did not admit: `filter/bloom:ntapGather`,
  `filter/directionalBlur:directionalBlur`, `filter/spinBlur:spinBlur`,
  `filter/strokes:stkSmear`, `filter/wind:wind`, and
  `filter/reindex:nmReindexStats`.
- `mixer/focusBlur:focusBlur` requires `sampler2D` user-function parameters,
  which the current typed emitter cannot spell.
- `synth/gabor:gabor` is syntactically depth 3, but `main`'s 5-trip loop calls
  the three-deep `gaborNoise` loop nest. Its effective execution-stack loop
  depth is 4 and effective nested product is 360, violating a depth-3 safety
  interpretation.

The coherent loop-only set is therefore exactly **36 sorted keys**, producing
projected totals of **107 typed**, **109 public**, and **103 unported**. The
input audit's 115/117/95 projection is not implementable without broadening
Task 15 into at least three additional frontiers.

The input audit also incorrectly says every candidate has default defines
`{}`. Eleven of the original 44 have authoritative non-empty metadata maps.
After the eight deferrals, nine of the retained 36 still have non-empty maps.
Using `{}` for them would fail the generator's existing metadata-equality
gate and, if that gate were weakened, select the wrong preprocessor variant.

No repository file was changed and no Task 15 implementation was started.

## Reconciliation of the original 44

The membership calculation is reproducible:

- 65 programs reach `for` after the Task 12-14 prerequisites.
- Remove the 15 recorded later blockers: 50 remain capability-clean under the
  audit's diagnostic loop erasure.
- Remove the six dynamic, metadata-only, float-counter, or over-cap forms:
  44 remain.
- Against the actual Task 14 tree, remove the eight extra-frontier/runtime
  hazards above: 36 remain for a loop-only increment.

`44 - 8 = 36`; the retained list below is sorted and unique.

## Exact retained 36 and authoritative define maps

The map shown is the value returned by the current authoritative metadata
default extraction and therefore the map the slice schema must carry.

| Key(s) | Exact define map |
| --- | --- |
| `filter/morphology:morphA`, `filter/morphology:morphB` | `{"SHAPE": 0}` |
| `filter/relief:rlBlurH`, `filter/relief:rlBlurV`, `filter/scatter:scatterSmooth`, `filter/stamp:stBlurH`, `filter/stamp:stBlurV`, `filter/strokes:stkPost` | relief/scatter/strokes-post: `{"MODE": 0}`; stamp blur passes: `{}` |
| `filter/lowPoly:lowPoly` | `{"LP_BORDER": 0, "LP_LIGHT": 0}` |
| `filter/hatch:hatch` | `{"MODE": 0}` |
| `filter/oilPaint:oilPost` | `{"MODE": 1}` |
| All other retained keys listed below | `{}` |

Expanded exact sorted list:

1. `filter/chrome:chBlurH` — `{}`
2. `filter/chrome:chBlurV` — `{}`
3. `filter/clouds:clouds` — `{}`
4. `filter/craquelure:craquelure` — `{}`
5. `filter/hatch:hatch` — `{"MODE": 0}`
6. `filter/highPass:hpBlurH` — `{}`
7. `filter/highPass:hpBlurV` — `{}`
8. `filter/lowPoly:lowPoly` — `{"LP_BORDER": 0, "LP_LIGHT": 0}`
9. `filter/morphology:morphA` — `{"SHAPE": 0}`
10. `filter/morphology:morphB` — `{"SHAPE": 0}`
11. `filter/normalize:reduce` — `{}`
12. `filter/normalize:reduceMinmax` — `{}`
13. `filter/oilPaint:oilPost` — `{"MODE": 1}`
14. `filter/patchwork:patchwork` — `{}`
15. `filter/photocopy:pcBlurH` — `{}`
16. `filter/photocopy:pcBlurV` — `{}`
17. `filter/pixelSort:findBrightest` — `{}`
18. `filter/plasticWrap:pwBlurH` — `{}`
19. `filter/plasticWrap:pwBlurV` — `{}`
20. `filter/relief:rlBlurH` — `{"MODE": 0}`
21. `filter/relief:rlBlurV` — `{"MODE": 0}`
22. `filter/reverb:reverb` — `{}`
23. `filter/scatter:scatterSmooth` — `{"MODE": 0}`
24. `filter/stamp:stBlurH` — `{}`
25. `filter/stamp:stBlurV` — `{}`
26. `filter/strokes:stkPost` — `{"MODE": 0}`
27. `filter/unsharpMask:usmBlurH` — `{}`
28. `filter/unsharpMask:usmBlurV` — `{}`
29. `filter/wormhole:blend` — `{}`
30. `mixer/cellSplit:cellSplit` — `{}`
31. `mixer/mashup:mashup` — `{}`
32. `mixer/shadow:shadow` — `{}`
33. `synth/cell:cell` — `{}`
34. `synth/gradient:gradient` — `{}`
35. `synth/mandala:mandala` — `{}`
36. `synth/subdivide:subdivide` — `{}`

There are 27 `{}` entries and nine non-empty entries. The generator's locked
`expected_defines` table must be extended exactly; its equality check must not
be removed.

## Loop proof census and charges for the retained 36

The following definitions remove ambiguity from the audit's word “charge”:

- `product` is the maximum innermost body executions for one lexical nest.
- `lexical charge` is the sum, for every loop node in the program, of that
  node's trips multiplied by all lexical ancestor trips, per invocation of
  its containing function.
- `entry charge` recursively includes every reachable user-helper invocation
  from `main`, takes the larger arm at an `if`, and includes one charge for
  each loop body entry. It is a per-pixel maximum before early `break`.

This definition is fail-closed and exposes helper call multiplicity that the
input audit did not record.

| Keys | Normalized header(s) and bound proof | Max lexical depth / products | Lexical charge | `main` entry charge |
| --- | --- | ---: | ---: | ---: |
| The 16 blur passes: chrome H/V, highPass H/V, morphology A/B, photocopy H/V, plasticWrap H/V, relief H/V, stamp H/V, unsharpMask H/V | `int i=1; i<=32; i++`; literal 32, 32 trips | 1 / 32 | 32 | 32 each |
| `filter/craquelure:craquelure` | `y=-1..1` containing `x=-1..1`; literals | 2 / 9 | 12 | 60 (the helper is reached five times) |
| `filter/lowPoly:lowPoly` | `dy=-1..1` containing `dx=-1..1`; literals | 2 / 9 | 12 | 12 |
| `filter/patchwork:patchwork` | `j=-1..1` containing `i=-1..1`; literals | 2 / 9 | 12 | 24 (the helper is reached twice) |
| `filter/scatter:scatterSmooth` | `y=-1..1` containing `x=-1..1`; literals | 2 / 9 | 12 | 12 |
| `filter/strokes:stkPost` | `dy=-1..1` containing `dx=-1..1`; literals | 2 / 9 | 12 | 12 |
| `filter/clouds:clouds` | `int i=0; i<8; i++`; literal 8 | 1 / 8 | 8 | 16 (`cloudNoise` is reached twice) |
| `filter/hatch:hatch` | `int i=0; i<5; i++`; literal 5, in `fbm` | 1 / 5 | 5 | 0 at authoritative `MODE=0`; the unused helper is still emitted and must compile |
| `filter/oilPaint:oilPost` | separate `fbm` `0..<5` and `tent3x3` `dy=-1..1` × `dx=-1..1` | 2 / 5 and 9 | 17 across helper definitions | 12 at authoritative `MODE=1`; `fbm` is unreachable |
| `synth/gradient:gradient` | `int i=0; i<4; i++`; literal 4 | 1 / 4 | 4 | 4 |
| `synth/mandala:mandala` | `int i=0; i<12; i++`; literal 12 | 1 / 12 | 12 | 12 |
| `synth/subdivide:subdivide` | `int level=0; level<6; level++`; literal 6 | 1 / 6 | 6 | 6 |
| `filter/normalize:reduce`, `filter/normalize:reduceMinmax` | `dy=0..<16` containing `dx=0..<16`; literals | 2 / 256 | 272 | 272 each |
| `filter/wormhole:blend` | `gy=0..<32` containing `gx=0..<32`; literals | 2 / 1024 | 1056 | 1056 |
| `mixer/shadow:shadow` | `x=-5..5` containing `y=-5..5`; literals | 2 / 121 | 132 | 132 |
| `synth/cell:cell` | `y=-2..2` containing `x=-2..2`; literals | 2 / 25 | 30 | 30 |
| `mixer/mashup:mashup` | `int k=1; k<8; k++`; preprocessed literal 8, exactly 7 trips | 1 / 7 | 7 | 7 |
| `mixer/cellSplit:cellSplit` | separate `-1..1` pair and `-2..2` pair | 2 / 9 and 25 | 42 | 42 |
| `filter/pixelSort:findBrightest` | `int s=0; s<NUM_SAMPLES; s++`; function-local `const int NUM_SAMPLES=32` | 1 / 32 | 32 | 32 |
| `filter/reverb:reverb` | `int iters=clamp(iterations,1,8); int i=0; i<iters; i++`; exact local clamp proof | 1 / 8 | 8 | 8 |

All retained individual trip counts are at most 32 except the 32×32 wormhole
scan; its individual loop count remains 32. Max lexical depth is 2. Max
lexical product is 1024 and max entry charge is 1056, both below 4096.

## Exact binder signatures and sampler declaration positions

Bindings are name-keyed at the public API. “Position” below is the source
uniform declaration / generated `State` constructor slot; `S1`, `S2`, etc.
are sampler ordinals. Tests must still remove every sampler name independently
rather than treating the binder as positional.

| Key(s) | Exact declaration-order binding signature |
| --- | --- |
| chrome H/V, relief H/V, scatterSmooth, stamp H/V | `inputTex:sampler2D@1/S1, resolution:vec2@2, smoothness:float@3` |
| highPass H/V, unsharpMask H/V | `inputTex:sampler2D@1/S1, resolution:vec2@2, radius:float@3` |
| photocopy H/V, plasticWrap H/V | `inputTex:sampler2D@1/S1, resolution:vec2@2, detail:float@3` |
| morphology A/B | `inputTex:sampler2D@1/S1, resolution:vec2@2, mode:int@3, radius:float@4` |
| `filter/clouds:clouds` | `inputTex:sampler2D@1/S1, tileOffset:vec2@2, fullResolution:vec2@3, seed:float@4, scale:float@5, speed:int@6, time:float@7` |
| `filter/craquelure:craquelure` | `inputTex:sampler2D@1/S1, resolution:vec2@2, tileOffset:vec2@3, spacing:float@4, depth:float@5, brightness:float@6, seed:int@7` |
| `filter/hatch:hatch` | `inputTex:sampler2D@1/S1, resolution:vec2@2, tileOffset:vec2@3, strokeLength:float@4, direction:int@5, balance:float@6, pressure:float@7, inkColor:vec3@8, paperColor:vec3@9` |
| `filter/lowPoly:lowPoly` | `inputTex:sampler2D@1/S1, tileOffset:vec2@2, fullResolution:vec2@3, scale:float@4, seed:float@5, mode:int@6, edgeStrength:float@7, edgeColor:vec3@8, speed:float@9, time:float@10, alpha:float@11` |
| normalize reduce / reduceMinmax | `tileOffset:vec2@1, fullResolution:vec2@2, inputTex:sampler2D@3/S1` |
| `filter/oilPaint:oilPost` | `inputTex:sampler2D@1/S1, flatTex:sampler2D@2/S2, resolution:vec2@3, tileOffset:vec2@4, size:float@5, detail:float@6, textureAmount:float@7, seed:int@8` |
| `filter/patchwork:patchwork` | `inputTex:sampler2D@1/S1, resolution:vec2@2, tileOffset:vec2@3, fullResolution:vec2@4, squareSize:float@5, relief:float@6, lightAngle:float@7` |
| `filter/pixelSort:findBrightest` | `lumTex:sampler2D@1/S1` |
| `filter/reverb:reverb` | `tileOffset:vec2@1, fullResolution:vec2@2, inputTex:sampler2D@3/S1, iterations:int@4, ridges:bool@5, alpha:float@6, wrap:float@7` |
| `filter/strokes:stkPost` | `inputTex:sampler2D@1/S1, smearTex:sampler2D@2/S2, resolution:vec2@3, sharpness:float@4` |
| `filter/wormhole:blend` | `inputTex:sampler2D@1/S1, accumTex:sampler2D@2/S2, resolution:vec2@3, tileOffset:vec2@4, fullResolution:vec2@5, alpha:float@6` |
| `mixer/cellSplit:cellSplit` | `inputTex:sampler2D@1/S1, tex:sampler2D@2/S2, resolution:vec2@3, tileOffset:vec2@4, fullResolution:vec2@5, mode:int@6, scale:float@7, edgeWidth:float@8, seed:int@9, invert:int@10, time:float@11, speed:float@12` |
| `mixer/mashup:mashup` | `resolution:vec2@1, source:sampler2D@2/S1, layer0_tex..layer7_tex:sampler2D@3..10/S2..S9, layers:int@11, smoothness:float@12, layer0_active..layer7_active:int@13..20` |
| `mixer/shadow:shadow` | `inputTex:sampler2D@1/S1, tex:sampler2D@2/S2, resolution:vec2@3, tileOffset:vec2@4, fullResolution:vec2@5, renderScale:float@6, maskSource:int@7, sourceChannel:int@8, threshold:float@9, color:vec3@10, offsetX:float@11, offsetY:float@12, blur:float@13, spread:float@14, wrap:int@15` |
| `synth/cell:cell` | `time:float@1, seed:int@2, resolution:vec2@3, tileOffset:vec2@4, fullResolution:vec2@5, renderScale:float@6, metric:int@7, scale:float@8, cellScale:float@9, cellSmooth:float@10, variation:float@11, speed:float@12`; no sampler |
| `synth/gradient:gradient` | `resolution:vec2@1, tileOffset:vec2@2, fullResolution:vec2@3, gradientType:int@4, rotation:float@5, repeat:int@6, colorCount:int@7, color1..color4:vec3@8..11, seed:int@12, time:float@13, speed:float@14`; no sampler |
| `synth/mandala:mandala` | `resolution:vec2@1, tileOffset:vec2@2, fullResolution:vec2@3, aspect:float@4, scale:float@5, rotation:float@6, thickness:float@7, smoothness:float@8, symmetry:int@9, layers:int@10, shape:int@11, layerSpacing:float@12, twist:float@13, shapeGrowth:float@14, bindu:bool@15, animation:int@16, speed:float@17, pulseDepth:float@18, time:float@19, fgColor:vec3@20, bgColor:vec3@21`; no sampler |
| `synth/subdivide:subdivide` | `inputTex:sampler2D@1/S1, resolution:vec2@2, tileOffset:vec2@3, fullResolution:vec2@4, renderScale:float@5, mode:float@6, depth:float@7, density:float@8, seed:float@9, fill:float@10, outline:float@11, inputMix:float@12, wrap:float@13, time:float@14, speed:float@15` |

## Deferred eight: exact reason, loop facts, defines, and bindings

| Key | Why deferred | Loop / charge facts | Defines and exact binding signature |
| --- | --- | --- | --- |
| `filter/bloom:ntapGather` | top-level `const int MAX_TAPS=64` unsupported by Task 14 | `0..<MAX_TAPS`; depth 1, product/entry 64 | `{}`; `tileOffset:vec2@1, fullResolution:vec2@2, inputTex:sampler2D@3/S1, radius:float@4, renderScale:float@5, taps:int@6` |
| `filter/directionalBlur:directionalBlur` | top-level `const int N=32` unsupported | `0..<N`; depth 1, product/entry 32 | `{}`; `inputTex:sampler2D@1/S1, resolution:vec2@2, angle:float@3, blurDistance:float@4` |
| `filter/spinBlur:spinBlur` | top-level `const int N=32` unsupported | `0..<N`; depth 1, product/entry 32 | `{}`; `inputTex:sampler2D@1/S1, resolution:vec2@2, tileOffset:vec2@3, fullResolution:vec2@4, amount:float@5, centerX:float@6, centerY:float@7` |
| `filter/strokes:stkSmear` | top-level `const int MAX_TAPS=24`; additionally exposes a prototype-emission defect | `3x3` plus `1..MAX_TAPS`; lexical depth 2, products 9/24, lexical charge 36, entry charge 72 | `{"MODE":0}`; `inputTex:sampler2D@1/S1, resolution:vec2@2, tileOffset:vec2@3, strokeLength:float@4, balance:float@5, intensity:float@6` |
| `filter/wind:wind` | top-level `const int MAX_STEPS=128` unsupported | `1..MAX_STEPS`; depth 1, product/entry 128 | `{"METHOD":1}`; `inputTex:sampler2D@1/S1, resolution:vec2@2, tileOffset:vec2@3, direction:int@4, strength:float@5, threshold:float@6` |
| `filter/reindex:nmReindexStats` | top-level `const int TILE_SIZE=8` unsupported | `0..<TILE_SIZE` squared; depth 2, product 64, lexical/entry charge 72 | `{}`; `inputTex:sampler2D@1/S1` |
| `mixer/focusBlur:focusBlur` | helper parameters `sampler2D sceneTex, sampler2D depthTex` cannot be emitted by current `function_type` | `0..<64`; depth 1, product/entry 64 | `{}`; `inputTex:sampler2D@1/S1, tex:sampler2D@2/S2, resolution:vec2@3, tileOffset:vec2@4, fullResolution:vec2@5, focalDistance:float@6, aperture:float@7, sampleBias:float@8, depthSource:int@9` |
| `synth/gabor:gabor` | interprocedural effective depth 4 exceeds depth-3 contract | helper `3x3x8`, main `0..<5`; lexical depth 3/products 72 and 5, lexical charge 89; effective product 360 and entry charge 425 | `{}`; `resolution:vec2@1, tileOffset:vec2@2, fullResolution:vec2@3, time:float@4, seed:float@5, scale:float@6, orientation:float@7, bandwidth:float@8, isotropy:float@9, density:float@10, octaves:float@11, speed:float@12`; no sampler |

`stkSmear`'s source has a forward declaration and later definition of
`srcSample`. The semantic IR retains both. The current emitter emits the
prototype as an empty non-void definition, then emits the real definition,
causing both `-Wreturn-type` and redefinition errors. This is separate from
its `const int` blocker.

## Additional semantic, emitter, and runtime hazards

1. **Task 14 scope is misstated in the input audit.** The approved code admits
   only initialized top-level source-`const` values of exact scalar `float`
   type. It does not admit `const int` or source vectors. The Task 15 brief
   must not describe integer constants as “already Task-14-lowered.”

2. **Loop proof must be immutable typed IR.** Current `TypedStatement("for")`
   stores condition/update positionally and contains no resolved bound,
   trip-count, product, charge, induction symbol, or proof kind. Add an exact
   frozen proof record and have both validator and emitter independently
   reject malformed records. Do not reparse source strings in the emitter.

3. **Increment support must remain header-scoped.** `i++` and `++i` are
   ordinary typed `post`/`unary` expressions today, and both validator and
   emitter reject them. Admission must be tied by stable symbol identity to
   the verified loop update. A body-level increment must remain rejected.

4. **Native `for` is the safest structured lowering.** Direct C++ `break` and
   `continue` preserve the lexical target, and C++ `continue` on a `for`
   executes the update expression. A manual `while` or control-state lowering
   can accidentally skip the update on `continue`; tests must cover this.

5. **Charge rules must be explicitly interprocedural.** Lexical-only census
   understates runtime work for clouds, craquelure, patchwork, and especially
   gabor. The formula above should be schema/test locked, with checked integer
   arithmetic and cycle rejection in the user-function call graph.

6. **Unreachable helpers still require emission.** At `hatch`'s authoritative
   `MODE=0`, `fbm` is not called and entry charge is zero, but the helper is
   present and the emitter currently emits all helpers. Loop capability and
   compile tests must therefore cover it even though runtime oracle pixels do
   not execute it.

7. **Public binding is name-based.** Declaration position only controls
   generated state construction. Negative tests must cover every uniform's
   missing/wrong type and every sampler name independently, including all nine
   mashup sampler names.

8. **Per-pixel caps do not cap a whole render.** `wormhole:blend` charges 1056
   loop-body visits per pixel; a large CPU surface multiplies that cost by
   every output pixel. This does not violate the proposed static language cap,
   but production acceptance should include measured CPU budgets or an outer
   render-size/work budget rather than treating 4096-per-pixel as a global
   denial-of-service bound.

9. **Prototype and sampler-parameter support are separate language work.** Do
   not silently fix them as incidental loop implementation. If later admitted,
   prototypes must be emitted only as declarations and sampler parameters must
   map to non-owning `const Surface&`/pointer semantics with stable binding
   lifetime and exact texture helper behavior.

## Read-only probe evidence

- Parsed all 44 candidates at their authoritative metadata defaults and
  extracted loop headers from AST, types/resources from typed IR, and uniform
  declaration order from stable symbols.
- In-memory loop erasure plus in-memory integer-constant substitution was used
  only as a diagnostic probe; it was never written into the repository.
- 43/44 reached the current emitter under that diagnostic transformation;
  focusBlur failed deterministically on unsupported helper `sampler2D` type.
- Strict individual AppleClang compilation of the transformed outputs found
  only `stkSmear`'s prototype double-definition/non-return error among those
  43. All retained 36 transformed outputs compiled independently with
  `-std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off`.
- This compile probe is following-frontier evidence, not an oracle substitute
  and not evidence that loop semantics have been implemented.

## Recommended corrected Task 15 boundary

Freeze the next brief/oracle around exactly the retained 36, their exact
define maps, the loop proofs and interprocedural charges above, and projected
107/109/103 counts. Keep top-level `const int`, sampler user-function
parameters, prototypes, and effective depth-4 gabor explicitly deferred.
Stop again for independent review before any of those frontiers.
