# Post-`const int` frontier audit: Task 41 local fixed octave bound

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-40.
Derivative semantics remain held: the execution ABI has no fragment-neighbor,
border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 40 | 162 | 164 | 48 |

## Recommendation: `perlin-local-const-octave-v1`

The next smallest exact slice is one macro-pinned generator. Its only new
proof form is a function-local literal `const int` that caps an already
projected counted loop:

| Key | Exact defines | Source SHA-256 | Exact new declaration |
| --- | --- | --- | --- |
| `synth/perlin:perlin` | `{ "DIMENSIONS": 2 }` | `9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318` | `const int MAX_OCT = 8` in `fbm2D` |

For this exact preprocessed profile, `MAX_OCT` has one read: the bound of
`for (int i = 0; i < MAX_OCT; i++)`. The loop has a fresh `int` induction
symbol, literal zero initializer, strict `<`, post-increment, and an existing
early `break` when `i >= oct`; the uniform-derived `oct` can only shorten the
scan. It therefore has at most eight visits. The same profile has the already
admitted literal `i=0..<4` domain-warp loop, also with an early break. `main`
can invoke the 8-visit FBM helper three times and the 4-visit warp helper once,
so the whole pixel invocation is bounded by 28 charged loop visits with no
recursion and no loop-contained return.

Top-level `const float TAU` and `Z_PERIOD` have literal initializers and reuse
the source-constant lowering contract. The resolved body otherwise reuses
existing capabilities: `mod(float,float)`, scalar `uint ^ uint`, `uvec3 >>
uint`/`uvec3 ^= uvec3`, constructors, scalar/vector arithmetic, ordinary
`in` helpers, and the existing `abs`/`clamp`/`cos`/`dot`/`floor`/`fract`/
`max`/`min`/`mix`/`normalize`/`sin` builtin paths. It has no sampler, array,
matrix, struct, uniform block, varying, `out`/`inout` helper parameter,
`textureLod`, derivative, boolean-vector, or dynamic loop form.

## Fail-closed typed/emitter/runtime contract

1. Admit only `synth/perlin:perlin` with the metadata-verified ordered define
   map `{ "DIMENSIONS": 2 }` and pinned source hash above. Reject an absent,
   non-2, additional, or reordered define; another key; source rewrite; macro
   profile expansion; compatibility transform; or numeric-literal exception.
2. Permit exactly one local constant declaration: `const int MAX_OCT = 8` in
   resolved `fbm2D`. Retain declaration/symbol identity, literal integer
   value, lexical function, zero-write proof, and sole bound read in immutable
   typed IR. Reject a global, a second local const int, a different
   type/value/initializer, a dependency, write/alias/escape, or a local const
   admitted outside this exact source span.
3. Reuse Task-15 loop lowering only for the exact two loop shapes in this
   preprocessed program: `i=0..<MAX_OCT` (eight visits) in `fbm2D`, and
   literal `i=0..<4` in `domainWarp2D`. Retain the break predicates and the
   call-graph charge proof (three FBM calls plus at most one warp call = 28).
   Reject another loop, a changed header/update/control statement, a dynamic
   or arithmetic bound, an increased charge, recursion, or a loop-contained
   return.
4. Reuse source-const lowering only for the exact literal float declarations
   `TAU` and `Z_PERIOD`, as automatic immutable reader locals. Reuse only the
   existing scalar-`uint` XOR and `uvec3` shift/XOR forms at their resolved
   source sites; this task does not establish signed bitwise, scalar shifts,
   vector-bit conversion, general word operations, or a global-constant
   expansion.
5. Bind only the authored generator interface: `resolution`, `tileOffset`,
   `fullResolution`, `aspect`, `time`, `scale`, `seed`, `octaves`,
   `colorMode`, `ridges`, `warpIterations`, `warpScale`, `warpIntensity`, and
   `speed`. Missing or wrong-typed bindings fail before invocation. Emit no
   allocation, static/mutable state, pointer/reference escape, virtual
   dispatch, callback, map, variant, indirect call, sampler route, or
   render-graph adapter; `PixelFn` remains `noexcept` and allocation-free.

Required positives are frozen `DIMENSIONS=2` perlin oracles at `octaves`
below one, one, interior, and above eight; both ridged modes; zero and positive
warp iterations; time/speed seams; seed/color modes; and non-square output.
Direct tests must lock the local declaration span/value, sole `MAX_OCT` use,
eight- and four-visit proofs, uniform-triggered early breaks, 28-visit
call-graph bound, Float32 output repeatability, and the exact unsigned XOR and
shift node signatures.

Required negatives reject `DIMENSIONS=3`, a changed define map/hash, another
key, nonliteral/local/global const drift, a second constant or loop, modified
bound/control/call graph, signed or scalar-shift bitwise forms, a derivative,
array, matrix, aggregate, uniform block, varying, sampler, non-`in`
parameter, nonzero/computed LOD, or unlisted macro configuration. Compile
generated C++ with warnings as errors and assert zero hot-path allocations and
indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 41 | **163** | **165** | **47** |

## Ranked residual map after Task 41

This local constant loop proof does not establish general local constants,
uniform-derived work, source-global state, or neighboring-pixel evaluation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource and dynamic-work contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Render-scale, texture-dimension, or charged-work bounds need independently enforced runtime proofs. |
| 3 | Global arrays, word, and index forms | normalMap, OSD, dither, glyph map, test pattern | Require aggregate lifetime, initialization, range, and signed-word contracts beyond one local literal bound. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, remaining scalar bitwise paths | Need independent mip/filter or two's-complement rules. |

Task 41 adds one hash-pinned typed factory while preserving the derivative
hold and every broader local/global, loop, array, matrix, aggregate, stage,
index, numeric, sampling, and macro boundary.
