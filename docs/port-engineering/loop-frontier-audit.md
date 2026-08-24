# Bounded-loop frontier audit

## Scope and model

This is a read-only projection over the pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`.  It models the following state,
without depending on concurrent implementation changes:

| Component | Programs |
| --- | ---: |
| Existing typed slice | 44 |
| Task 12 `mod` slice | 13 |
| Task 13 exact `texelFetch` slice | 8 |
| Task 14 exact source-const lowering | 6 |
| Existing legacy public entries (`invert`, `solid`) | 2 |
| Projected public catalog | **73** |
| Remaining unported corpus programs | **139** |

The Task 12, Task 13, and Task 14 additions are treated as prerequisites, not
as loop features.  In particular, Task 14 remains limited to initialized,
readonly, source-qualified scalar/vector constants lowered into function-local
constants; this audit does not broaden it into arbitrary global state.

## Whole-frontier AST census

The 139 remaining programs contain 103 loop-bearing programs and 190 loop AST
nodes: 186 `for`, 4 `while`, and zero `do…while`.  Their greatest syntactic
nesting depths are 70 programs at depth 1, 31 at depth 2, and 2 at depth 3.
There are no `do…while` cases to admit.  The four `while` cases are all behind
an earlier unsupported feature, so accepting `while` buys no immediately
executable program.

After the provisional prerequisites, 65 programs first reach a `for` loop:

| First blocker after prerequisites | Programs |
| --- | ---: |
| Directly at `for` | 42 |
| First reaches a `for` after Task 14 source-const lowering | 23 |
| Total immediate loop frontier | **65** |
| Loop-bearing programs still blocked earlier by arrays, matrices, globals outside Task 14, derivatives, structs, etc. | 38 |
| Remaining programs without a loop AST | 36 |

No immediate-frontier loop body contains `return`.  `break` is used in 30 of
the 65 programs and `continue` in five (`normalize:reduce`,
`normalize:reduceMinmax`, `pixelSort:computeRank`, `mixer/cellSplit`, and
`sacredGeometry`).  Thus `break` and `continue` are necessary for the useful
slice; `return` need not be added as a loop-control feature.

## Exact immediate-frontier forms

All forms below are parsed AST headers, normalized only for spacing.  `C(n)`
means a source-qualified integer `const` admitted by Task 14; `L(n)` is a
literal bound.  Every listed program has default defines `{}`.

| Form / maximum lexical trip count | Keys | Controls / nesting |
| --- | --- | --- |
| `for (int i=1; i<=32; i++)` — L(32) | `filter/chrome:chBlurH`, `filter/chrome:chBlurV`, `filter/highPass:hpBlurH`, `filter/highPass:hpBlurV`, `filter/morphology:morphA`, `filter/morphology:morphB`, `filter/photocopy:pcBlurH`, `filter/photocopy:pcBlurV`, `filter/plasticWrap:pwBlurH`, `filter/plasticWrap:pwBlurV`, `filter/relief:rlBlurH`, `filter/relief:rlBlurV`, `filter/stamp:stBlurH`, `filter/stamp:stBlurV`, `filter/unsharpMask:usmBlurH`, `filter/unsharpMask:usmBlurV` | each depth 1; each uses guarded `break` |
| `for (int i=0; i<3; i++)` — L(3) | `filter/grade:creative` (2 loops), `filter/grade:hslSecondary` (3), `filter/grade:lut` (4), `filter/grade:primary` (2), `filter/grade:vignette` (2), `filter/grade:wheels` (2) | depth 1; no loop control |
| `for (int v=-1; v<=1; v++)` — L(3), paired nesting — L(9) | `filter/craquelure:craquelure`, `filter/halftone:halftone`, `filter/lowPoly:lowPoly`, `filter/patchwork:patchwork`, `filter/scatter:scatterSmooth`, `filter/strokes:stkPost` | depth 2; no loop control |
| Small literal counters | `filter/clouds:clouds` (`0..<8`, `break`), `filter/hatch:hatch` (`0..<5`), `filter/oilPaint:oilPost` (`0..<5`, plus a nested `-1..1` pair), `filter/stamp:stThreshold` (`0..<5`), `filter/stipple:stipple` (`0..<5`, plus nested `-1..1` pair), `synth/curl:curl` (`0..<1`), `synth/gradient:gradient` (`0..<4`), `synth/mandala:mandala` (`0..<12`, `break`), `synth/subdivide:subdivide` (`0..<6`, `break`) | depth 1 or 2 |
| Literal rectangular scans | `filter/normalize:reduce`, `filter/normalize:reduceMinmax` (`0..<16` × `0..<16`, L(256), `continue`); `filter/wormhole:blend` (`0..<32` × `0..<32`, L(1024)); `mixer/shadow:shadow` (`-5..5` × `-5..5`, L(121)); `synth/cell:cell` (`-2..2` × `-2..2`, L(25)) | depth 2 |
| Other literal counters | `mixer/focusBlur:focusBlur` (`0..<64`); `mixer/mashup:mashup` (`1..<8`, `break`); `mixer/cellSplit:cellSplit` (separate `-1..1` and `-2..2` pairs, L(9)+L(25), `continue`); `synth/gabor:gabor` (nested `-1..1` × `-1..1` × `0..<8`, L(72), plus `0..<5`; `break`); `synth/sacredGeometry:sacredGeometry` (several L(3/6/12/13) forms, nested L(169), `continue` and `break`) | `gabor` is the only executable depth-3 form; `sacredGeometry` is separately blocked by `vec2[13]` |
| Source-constant bound | `filter/bloom:ntapGather` (`0..<MAX_TAPS`, C(64), `break`); `filter/directionalBlur:directionalBlur` and `filter/spinBlur:spinBlur` (`0..<N`, C(32)); `filter/pixelSort:computeRank` and `filter/pixelSort:findBrightest` (`0..<NUM_SAMPLES`, C(32)); `filter/strokes:stkSmear` (`-1..1` pair plus `1..MAX_TAPS`, C(24), `break`); `filter/wind:wind` (`1..MAX_STEPS`, C(128), `break`) | depth 1 or 2 |
| Source-constant rectangular scan | `filter/reindex:nmReindexStats` (`0..<TILE_SIZE` × `0..<TILE_SIZE`, C(8×8)); `filter/reindex:nmReindexReduce` (`0..<MAX_TILE_DIM` × `0..<MAX_TILE_DIM`, C(512×512), `break`) | depth 2; the latter exceeds the recommended cost cap |
| Proven bounded local | `filter/reverb:reverb`: `int iters=clamp(iterations,1,8); for (int i=0; i<iters; i++)` — C(8) | depth 1 |
| Dynamic / metadata-dependent, not syntax-bounded | `filter/blur:blurH`, `filter/blur:blurV`: `-radius..radius`, where `radius=int(radius[XY]*renderScale)`; `filter/normalize:statsFinal`: `0..<textureSize(...).xy`; `filter/tetraColorArray:tetraColorArray`: `1..<colorCount` (metadata gives `colorCount` min 2, default 6, max 8) | depth 1 or 2 |
| Non-integral counter | `filter/zoomBlur:zoomBlur`: `for (float t=0.0; t<=40.0; t++)` — 41 trips | depth 1 |

The remaining Task-14 source-const loop forms are: `filter/blur:blurH`,
`filter/blur:blurV` (dynamic local radius); `filter/extrude:extrude` (a
literal `-1..1` pair and `0..<6`); `filter/grade:*` (the L(3) entries above);
`filter/halftone:halftone`; `filter/octaveWarp:octaveWarp` (`1..10`, guarded
break); `filter/reindex:nmReindex*`; `filter/tetraColorArray:tetraColorArray`;
`filter/wind:wind`; `mixer/cellSplit:cellSplit`; `synth/perlin:perlin`
(`0..<MAX_OCT`, C(8), and `0..<4`); and `synth/subdivide:subdivide`.

## Exact next blockers after loop admission

I replayed the typed capability validator after erasing only the loop wrapper
and its `break`/`continue` nodes for diagnostic ordering (not as a semantic
implementation).  With `mod`, `texelFetch`, and source-const lowering
provisionally present, 50 of the 65 have no later frontend capability blocker.
The remaining 15 are:

| Next blocker | Keys |
| --- | --- |
| dynamic vector indexing | `filter/grade:creative`, `filter/grade:hslSecondary`, `filter/grade:lut`, `filter/grade:primary`, `filter/grade:vignette`, `filter/grade:wheels` |
| derivatives | `filter/halftone:halftone` (`fwidth`), `filter/octaveWarp:octaveWarp` (`dFdx`), `filter/stamp:stThreshold` and `filter/stipple:stipple` (`fwidth`) |
| other builtin | `filter/extrude:extrude` (`all`), `synth/curl:curl` (`tanh`) |
| non-loop increment expression | `filter/pixelSort:computeRank` (a body-level post-increment; loop-only increment support must not accidentally admit this) |
| operator | `synth/perlin:perlin` (`^`) |
| fixed array | `synth/sacredGeometry:sacredGeometry` (`vec2[13]`) |

The capability replay passes for the other 50 before applying the safety
contract below.  That is evidence of a following feature frontier, not a
claim that loop lowering can erase control flow.

## Recommended narrow contract: `counted-for-v1`

Admit only a fail-closed, statically provable subset:

1. `for` only; reject `while` and `do…while`.
2. Loop variable is a fresh function-local `int`, initialized from an integer
   literal (including unary `-` literal).  No `float`, `uint`, aliases, or
   externally declared induction variable.
3. Condition is exactly `i < B` or `i <= B`, with `i` on the left and a
   monotonic `i++` or `++i` update on the same symbol.  Do not admit arbitrary
   `post` / `pre` expressions elsewhere in the program.
4. `B` is one of: an integer literal; an already Task-14-lowered `const int`
   with a compile-time evaluated value; or a local `int` assigned from the
   exact `clamp(uniform, literal-min, literal-max)` form.  Do not use metadata
   defaults alone as a compiler proof, and do not accept `textureSize`, other
   uniforms, arithmetic-derived bounds, or function parameters.
5. Preserve lexical `break` and `continue` only when nested in an admitted
   loop; reject loop-contained `return`.  Lower both with structured control
   state rather than C++ `goto` or unbounded recursion.
6. Recompute the source-level maximum before emission, then enforce:
   - at most 128 trips for every individual loop;
   - nesting depth at most 3;
   - at most 4,096 visits for every lexical nested product; and
   - at most 4,096 total statically charged loop visits per entrypoint.
   Reject on overflow, missing proof, or a cap violation.

This admits **44** coherent typed programs: all of the 50 clean replays except
the two unbounded blur passes, resolution-sized `normalize:statsFinal`,
metadata-only `tetraColorArray`, the float-loop `zoomBlur`, and the
512×512 `nmReindexReduce`.  It includes the exact `filter/reverb:reverb`
`clamp(...,1,8)` form, and includes `nmReindexStats` at 8×8.  The 44 all use
default defines `{}`.  Projected totals are therefore **115 typed**, **117
public**, and **95 unported**.

`tetraColorArray` is a safe optional forty-fifth only if the generated catalog
also enforces the pinned metadata interval `2 <= colorCount <= 8` at runtime
before calling the shader; default metadata by itself is not a fail-closed
bound.  `blurH` / `blurV` should remain deferred until `renderScale` has an
explicit validated cap, and `statsFinal` until input texture dimensions have a
documented allocation cap carried into the compiler contract.

## Implementation/verification guardrails

- Put the accepted shape, resolved numeric bound, nesting product, and total
  charge in typed IR.  The C++ emitter must consume that checked representation
  rather than re-inspecting source strings.
- Keep a per-key, sorted `{}` define table in the slice schema; reject any
  nonempty define map in this loop increment unless separately audited.
- Add negative parser/semantic tests for `while`, `do`, float induction,
  `i+=2`, decrementing forms, swapped comparisons, dynamic bounds, unproved
  source constants, loop `return`, body-level `i++`, a 129-trip loop, a
  512×512 loop, and arithmetic overflow in charge computation.
- Oracle each admitted key at its pinned defaults plus the extrema relevant to
  `reverb` (1 and 8), `wind` (its guarded early-exit path), and control-flow
  cases containing `break` or `continue`.  The loop audit does not authorize
  a corpus-wide source rewrite or any broad global-variable support.
