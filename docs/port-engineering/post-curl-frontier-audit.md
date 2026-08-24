# Post-curl frontier audit: Task 28 bounded oil-flatten radius loops

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after proposed Tasks 12–27.
Derivative semantics remain unavailable pending a deliberately specified
neighborhood/quad ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 27 | 146 | 148 | 64 |

## Recommendation: `oil-flatten-bounded-radius-v1`

The next coherent non-derivative dynamic-loop slice is the default
oil-flatten pass:

| Key | Exact default defines | Exact new forms |
| --- | --- | --- |
| `filter/oilPaint:oilFlatten` | `{ "MODE": 1 }` | `ceil(float) -> float`; an exactly proved, nested symmetric local-bound loop pair |

After preprocessing at `MODE=1`, the source computes `radius = size`, then
`fr = clamp(radius, 1.0, 12.0)`, then
`sampleLimit = int(ceil(fr))`.  Its only dynamic loops are exactly:

```glsl
for (int y = -sampleLimit; y <= sampleLimit; y++) {
    for (int x = -sampleLimit; x <= sampleLimit; x++) {
```

For every finite `size`, the source-local proof is
`1 <= fr <= 12`, `1 <= sampleLimit <= 12`, and each axis has at most 25
visits.  The charged nested work is therefore at most `25 * 25 = 625` visits.
The pass uses the existing `textureSize`, `texelFetch(sampler2D, ivec2, 0)`,
scalar integer modulo, vector arithmetic, and Task-15 `continue` contracts;
it has no derivative use, array, matrix, UBO, varying, sampler parameter, or
resource-sized loop bound.  The manifest lists only `inputTex` and `size`, and
the metadata default map is exactly `{ "MODE": 1 }`.

This is safer than the remaining blur passes: their bound derives from
`int(radiusX * renderScale)` or `int(radiusY * renderScale)` and has no
source-local upper-bound proof.  It is also smaller than a texture-dimension
contract for normalize or the 512-by-512 reindex reduction.

## Fail-closed typed/emitter/runtime contract

1. Admit only the named key with the exact integer define map `{ "MODE": 1 }`.
   Extend the typed-slice default-define allowlist by this one entry; preserve
   the existing integer-only schema.  Reject `MODE=0`, `MODE=2..5`, a missing
   `MODE`, a string/float/boolean coercion, another define, or metadata-map
   drift.  No oil-post pass and no macro-variant family is included.
2. Add only the scalar builtin signature `ceil(float) -> float`.  Retain its
   resolved signature in immutable typed IR and reject vector `ceil`, integer
   `ceil`, `floor` substitutions, other rounding builtins, or an unlisted
   caller.  The runtime implementation is the same f32 boundary convention as
   `floor`: `glsl::ceil(double value) noexcept` returns
   `f32(std::ceil(value))`.  Do not add vector overloads or a generic rounding
   mapper.
3. Recognize one proof-carrying dynamic-bound data flow, not arbitrary local
   loop bounds: at the selected key and default preprocessed source, a float
   local is the exact `clamp(<finite float expression>, 1.0, 12.0)` result and
   the next integer local is exactly `int(ceil(that_local))`.  Store the
   symbol identities, f32 lower/upper bounds, conversion chain, source spans,
   and maximum value 12 in immutable typed IR.  The proof must be based on the
   source `clamp`, not UI metadata alone.
4. Admit exactly two nested `for` statements using that one proved local:
   fresh `int y` then fresh `int x`, each initialized as `-sampleLimit`, tested
   as `<= sampleLimit`, and updated only by postfix `++`.  Preserve the GLSL
   scan order (y outer, x inner), admit the two existing body `continue`
   statements under Task 15's structured loop-control rule, and reject a
   write/alias of `sampleLimit`, a different bound expression, `<`, a different
   initial value/update, a `break`/`return`, third loop, sibling dynamic loop,
   different nesting order, or any bound use as an array index, LOD, texture
   size, allocation size, or state field.
5. Require `size` to be finite in this factory before state construction.
   All finite values retain source behavior because the selected source itself
   clamps them to `[1,12]`; NaN and either infinity are rejected before the
   C++ float-to-int conversion.  This is a safety precondition, not a new UI
   range clamp or an authorization to validate unrelated uniforms.
6. The validator assigns an exact cap of 25 axis visits and 625 total nested
   visits before emission.  Emit direct C++ `for` loops with automatic
   `std::int32_t` locals; do not unroll, allocate, recurse, use
   `std::variant`/maps, dynamic dispatch, callbacks, or a shared pixel-state
   scratch buffer.  The existing direct `texelFetch` calls remain bounded by
   the pass's own coordinate clamp.  `PixelFn` remains `noexcept` and
   allocation-free.

Required positive coverage is a frozen canonical oracle for `MODE=1` at
`size=1`, default `size=6`, a noninteger ceiling boundary on each side of 6,
and `size=12`, using edge and corner pixels on a nonuniform small source so
coordinate clamping, both `continue` paths, all octant assignments, and the
full 625-visit bound are exercised.  Unit-test f32 `ceil` on positive,
negative, integral, fractional, large finite, and NaN inputs; only the
selected finite values can reach the factory.  Assert the IR has one exact
ceiling-to-limit proof and the y/x nesting charge is 625.

Required negatives reject a vector or integer `ceil`; an unconnected scalar
`ceil`; `int(floor(fr))`; unclamped, reversed, or 13-upper-bound data flow;
an escaped/nonfinite size; an altered loop header; a write to `sampleLimit`;
three dynamic loops; a 626-or-larger charge; a bound used for indexing/LOD;
`MODE` variants; and any derivative call.  Compile emitted C++ with warnings
as errors and assert zero hot-path allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 28 | **147** | **149** | **63** |

## Ranked residual map after Task 28

These remain independent frontiers; none is authorization to generalize
bounded local loops, `ceil`, or oil-paint variants.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Other resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Need a separately validated render-scale bound, texture-dimension/work policy, or a much larger 512-by-512 budget. |
| 3 | Interface adapters | focusBlur sampler parameters; multi-pass/output flow | Requires a pinned sampler-argument or pass-chain ABI, not a loop change. |
| 4 | Remaining numeric and word operations | signed bitEffects, vector `round`, general shifts/masks, perlin `^` | Need independent signed-word, shift-count, and vector numeric contracts. |
| 5 | Aggregate/interface representation | Julia, Mandelbrot, Newton; historicPalette, palette; remap UBO | Multi-output copy-out, structs, and std140 layout each exceed this local scalar proof. |
| 6 | Varying/matrix/array models | texture, grime, spookyTicker, wormhole deposit; mat4 effects; global arrays | Need a pinned stage-input representation, matrix algebra, or global-lifetime/indexing contract. |
| 7 | General sampling and macro variants | computed/nonzero `textureLod`; nondefault oil MODE values | Need owned mip/filter semantics or an independently audited preprocessor configuration family. |

Task 28 is deliberately one source-proven dynamic radius family: it adds a
single default-configuration factory while retaining the derivative hold and
leaving broader loop, builtin, interface, aggregate, and macro frontiers
separately reviewable.
