# Projected post-Task-25 remaining-frontier audit

Date: 2026-08-11  
Scope: read-only corpus, typed IR, capability validator, typed emitter, native
runtime/execution ABI, public CPU catalog, canonical factories, and adapters.
No repository file or Git state was changed. This is not a Task 26 brief,
oracle, design, or implementation authorization.

## Decision

The requested starting point is the exact projected Task 25 state:

| State | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Projected exact Task 25 | **125** | **127** | **85** |

The live checkout remains the accepted Task 23 state, **122 / 124 / 88**.
Gather Sorted, Lens Distortion, and Prismatic Aberration are not yet in the
live typed slice. Therefore this audit projects Task 24's one Gather key and
Task 25's exact two literal-`vec3` lane keys, then excludes exactly those three
from the remaining corpus. Final Task 24 and Task 25 acceptance must rerun this
audit; any source, profile, generated-order, count, or public-factory drift
invalidates it.

The best bounded Task 26 slice is one exact immutable source vector constant:

```text
filter/smooth:smoothEdge
```

Its only current blocker is the one top-level declaration
`const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114)`. The resolved symbol is
read at exactly one static site, as the second argument of `dot` in helper
`luminance`; it has no write or escape. A fresh read-only projection moving
only that exact declaration to an automatic helper-local value passes the
current validator, emitter, and C++20 warnings-as-errors syntax check. There is
no later blocker and no runtime, vector-index, derivative, loop, sampler-helper,
or public-adapter change.

Conditional projection after adding only Smooth Edge:

| State | Typed | Public | Publicly unported |
| --- | ---: | ---: | ---: |
| Exact Task 25 | 125 | 127 | 85 |
| Exact Smooth Edge Task 26 | **126** | **128** | **84** |

The projected newline-terminated sorted typed/public list SHA-256 values are
`01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76`
and `d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3`.
Smooth Edge is at zero-based typed position 77 between `filter/skew:skew` and
`filter/smoothstep:smoothstep`.

## Projection inputs and hard gates

Corpus revision is
`a024dc3a960cc44af454abc7aebce50456c194e6`.

The exact Task 25 projection is 125/127/85 with typed/public list hashes
`9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4`
and `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`.
The supporting Task 25 frontier audit is
`task-25-frontier-audit.md`, SHA-256
`e754d9e02e3d98069297dda9f2c8071d25ba2347ddd812af0c41dc74b82e7d27`.

During this audit the temporary Task 24 brief was narrowed to the selected
round-under-int emission decision. Its new SHA-256 is
`a5184121126d75b32372440aae13ef9cde06006c5f4189607327e323e7d16e53`.
The brief now requires exact site/parent lowering as
`glsl::detail::float_to_int32(glsl::round(...))`, without changing generic
`int(float)` emission. Task 24 typed identity and public oracle data are
unchanged. `node task-24-oracle-generator.mjs --check` passed, and the
generator/JSON/report hashes remain respectively
`35d20a4428af390ed437f3c829a250a1974d254b66712c900d684d54a7e682d6`,
`07dd6f31c3e2b5451cbde8fc0ae6f68ec7c3b06cd6296222ac938cdcee37a72a`,
and `b33894f0d69c97de5392d686bc9d5b469d672fc59f522b7b79c15604ae4299f6`.

The live 122/124 lists still hash to
`9db3013a6b0f78d0b95fcb6713c54ace95e82d1545e796e7a380add23c009f0b`
and `2b84fff4d6f35aec1ac6bcc35188d9893e3194c90b9c428775a7308ce1f6281a`.
No projected count is evidence of implemented or accepted live state.

## Recomputed first-blocker census for the 85

After excluding exactly Gather Sorted, Lens Distortion, and Prismatic
Aberration, the first validator/emitter results are:

| First result | Count |
| --- | ---: |
| Unsupported top-level global declaration | 31 |
| Unproved counted-loop program | 19 |
| `dFdx` derivative | 11 |
| `fwidth` derivative | 5 |
| Counted loop exceeds an existing safety cap | 3 |
| Scalar XOR outside current overloads | 2 |
| Varying/stage interface | 2 |
| Dynamic/induction `vec3[i]` | 1 |
| Scalar `round` outside Gather's exact profile | 1 |
| Sampler helper parameter reaches emitter type gap | 1 |
| `all` builtin | 1 |
| `any` builtin | 1 |
| `floatBitsToUint` builtin | 1 |
| `reflect` builtin | 1 |
| `tanh` builtin | 1 |
| Matrix return ABI | 1 |
| `inout` parameter ABI | 1 |
| `mat4` type | 1 |
| Uniform block/resource ABI | 1 |
| **Total** | **85** |

All are validator failures except `mixer/focusBlur:focusBlur`, which validates
and then fails emission because `sampler2D` cannot be spelled as a user-helper
parameter type.

The 19 unproved-loop keys are Effects, Fractal, Noise, Blur H/V, Dither, Light
Leak, Median, Normalize Stats Final, Oil Flatten, Parallax, Reindex Reduce,
Reindex Stats, Smooth Blend, Tetra Color Array, Zoom Blur, Mandelbrot, synth
Noise, and Test Pattern. The three safety-cap keys are Gabor, Julia, and
Newton. Those loop families are unchanged by Tasks 24 and 25.

## Task 26 candidate: exact Smooth Edge `const vec3`

### Frozen identity and interface

| Field | Required observed value |
| --- | --- |
| Key | `filter/smooth:smoothEdge` |
| Source | `sources/filter/smooth/smoothEdge.glsl` |
| Raw bytes / SHA-256 | 1554 / `b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265` |
| Normalized bytes / SHA-256 | 1235 / `42f61c507d633c07415bc816b6ba61f8a862642429943be1c0c1208c97b90f7c` |
| Defines | exactly `{}` |
| Function tuple SHA-256 | `8a7f2ac058a23e438f31787c55d235235271429fb79fc1d085c4dd1ba08cd4fc` |
| Whole typed-program SHA-256 | `5586658ce1f621887647e5fb77990606e8637b7d759d2c9f1096f26b7385cd89` |
| Interface SHA-256 | `9149a7b19b47edea7179f8460443ee67c4a314bcb3ed2a83b7a68d91550f4930` |
| Public/canonical factory | exact same `canonicalFactory140` object |
| Factory-text SHA-256 | `732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e` |
| Adapter entry | absent |

Bindings are exactly
`tileOffset:vec2@1`, `fullResolution:vec2@2`,
`inputTex:sampler2D@3/S1`, `smoothType:int@4`, and `threshold:float@5`;
output is `fragColor:vec4@6`. The program uses one sampler, four ordinary
uniforms, one output, texture access, and no derivatives. It has two functions,
`luminance` signature 9 and `main` signature 10, no loop, array, matrix,
struct, UBO, varying, sampler parameter, or non-`in` parameter.

### Exact declaration and use

The sole non-interface declaration is symbol 7, normalized span
`12:1-12:53` (raw source line 19):

```glsl
const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114);
```

It is storage `const`, type `vec3`, non-writable, and has declaration repr
SHA-256 `be8644a44ad3d2710e4dfaa87045257a5bd7c0e7e0a363c12893ea77c3d2ee27`.
The direct three-scalar constructor initializer has repr SHA-256
`57ee749ccff2d5029ccbd10b7ce01320fdeb694bf2d02d5835a0e6ccd5836104`.
The ordered literal/F32-bit pairs are:

```text
0.299 -> 0x3e991687
0.587 -> 0x3f1645a2
0.114 -> 0x3de978d5
```

The complete resolved-symbol census finds exactly one static read,
`luminance` span `15:21-15:33`, as argument two of
`dot(rgb, LUMA_WEIGHTS)`. There is no assignment, compound assignment,
increment/decrement, swizzle/index/member write, parameter passing, return,
alias, or `out`/`inout` escape. `main` calls `luminance` five times on the
center and four clamped cardinal neighbor texels, so the one static read can
execute five times on the non-pass-through path.

### Bounded lowering and proof result

The later brief should extend source-global materialization only for this exact
key/declaration/use closure. Materialize one ordinary automatic
`const glsl::Vec3 LUMA_WEIGHTS` at entry to `luminance`, from the three typed
literal children, using existing vector construction and F32 lane storage.
Emit no namespace/global/static/function-static object and do not store it in
`State`; use no allocation, pointer/reference lookup, map, variant, callback,
virtual call, or dynamic initialization.

A diagnostic source-local projection emitted the equivalent constructor and
direct `glsl::dot`, produced 4,469 bytes of C++ with SHA-256
`5e8bcfa1c5ca5c06b0eb6371eeeaf77444e698187de1040a9674b3fdd269a9e3`,
and passed `c++ -std=c++20 -Wall -Wextra -Werror -fsyntax-only`. This hash is
diagnostic only because the projection moved source text; a later identity
profile must keep the real typed tree unchanged and independently authenticate
the original global at validator and emitter.

Required negatives should reject any other key/name/type/storage/arity/literal,
scalar splat, computed or dependent initializer, second aggregate global,
different read owner/site/parent, main-level use, write/escape, array, matrix,
struct, sampler, mutable/uninitialized global, derivative, or nonempty define
map. The existing source-global scalar-float and exact literal-int profiles
remain independent and unchanged.

The execution ABI risk is bounded: `PixelFn`, `PixelContext`, `run_pass`,
samplers, `Surface`, and `Bindings` need no change. The helper-local vector is
12 bytes of fixed value state before optimizer folding; require stack and
Release-disassembly evidence that the five calls inline or remain direct,
with no allocation or indirect call. Public output oracles must distinguish
the `smoothType == 0` pass-through and nonzero edge paths, threshold boundaries,
non-square dimensions, all four clamped neighbors, lane order, and F32/RGBA8
results.

## Derivatives: 16 first-blocked, 17 after Posterize round

The eleven `dFdx`-first keys are:

```text
filter/bulge:bulge
filter/lens:lens
filter/lensWarp:lensWarp
filter/octaveWarp:octaveWarp
filter/pinch:pinch
filter/polar:polar
filter/pondRipples:pondRipples
filter/spiral:spiral
filter/tunnel:tunnel
filter/warp:warp
mixer/distortion:distortion
```

The first ten each have one `dFdx(vec2)` and one `dFdy(vec2)` in `main`.
Distortion has three pairs across `applyDisplacement`, `applyRefraction`, and
`applyReflection`. Thus the family contains 13 `dFdx` and 13 `dFdy` sites.

The five `fwidth`-first keys are Cel Shading Color (`vec3`, one site),
Halftone (`float`, two sites), Stamp Threshold (`float`, one), Step (`vec3`,
one), and Stipple (`float`, one): six sites total. Posterize has one later
`fwidth(vec3)` site, so exposing its separate scalar round would create a
seventeenth derivative-blocked key and a seventh `fwidth` site. All 17 public
factories are exact canonical identities and none has an adapter.

This is not a builtin-name or current-pixel finite-difference slice. The public
CPU runtime's normative behavior wraps derivative factories in a record/replay
2x2-quad evaluator:

1. identify the fragment's even-aligned quad;
2. execute the full kernel in record mode at four lane coordinates, including
   coordinates beyond an odd output edge;
3. pair left/right and bottom/top recorded values by derivative-call ordinal;
4. compute lane-wise `dFdx`, `dFdy`, or `abs(dx)+abs(dy)`;
5. replay the full target invocation with those values and cache/evict quad
   records according to traversal.

The current native `PixelFn` is one opaque
`void(const KernelState&, const PixelContext&, Vec4&) noexcept` invocation.
`PixelContext` has only UV, fragment coordinate, resolution, time, seed, frame,
and delta time. `run_pass` invokes pixels independently and exposes no quad,
record/replay state, derivative call ordinal, helper-lane policy, odd-border
probe rule, tile ownership, cache lifetime, or parallel scheduling contract.

Parity therefore requires an execution-ABI design: record/replay-capable
generated kernels or context, fixed scratch ownership, exact control-flow/site
alignment, odd-edge probes, deterministic cache eviction, exception/allocation
policy, and a threading rule. A generic finite difference of output color or
texture samples is not equivalent because derivative operands are arbitrary
intermediate scalar/vector expressions. This remains high risk despite the
large direct unlock.

## Remaining 31 global-first programs

Tasks 24 and 25 do not change the 31-key source-global frontier.

### Sixteen scalar/vector-constant programs

```text
classicNoisedeck/bitEffects:bitEffects
filter/edge:edge
filter/emboss:emboss
filter/fxaa:fxaa
filter/glyphMap:glyphMap
filter/grade:creative
filter/grade:hslSecondary
filter/grade:primary
filter/grade:vignette
filter/grade:wheels
filter/grain:grain
filter/scanlineError:scanlineError
filter/smooth:smoothEdge
filter/snow:snow
filter/texture:texture
filter/wobble:wobble
```

A fresh immutable-IR inline projection over every initialized non-interface
scalar/vector constant found only Smooth Edge validator/emitter-clean. The
other later blockers are exact:

| Later blocker | Keys |
| --- | --- |
| Scalar/word `&` | Bit Effects, Glyph Map |
| `bvec3` | Edge |
| local `float[9]` | Emboss |
| scalar `round` | FXAA, Grain, Snow |
| induction `vec3[i]` | the five Grade programs |
| `floatBitsToUint` | Scanline Error |
| varying/stage input | Texture, Wobble |

### Other global representations

- Seven programs use read-only `const mat3` sets: Cell Noise, Color Lab,
  Moodscape, Shape Mixer, Shapes, Adjust, and Colorspace.
- Cell Refract and Kaleido each use five mutable uninitialized global
  `float[9]` tables.
- Historic Palette and Palette use aggregate struct tables; Normal Map uses
  `ivec2[9]` and two `float[9]` tables; OSD and Spooky Ticker use `int[80]`
  glyph tables.
- `synth/shape:shape` has mutable uninitialized `aspectRatio` and
  `globalCoord` and must never enter a const-global profile.

Those forms require separate matrix, aggregate layout/indexing, mutable-state,
lifetime, isolation, and adapter proofs. Task 26 should not generalize from one
direct literal `vec3`.

## Round/site profiles after Task 25

Gather Sorted's Task 24 authority is exact key/source/site/parent emission and
does not add `round` to the global vocabulary. Remaining round sites are:

| Key | Sites | Type/consumer | Earlier or next blocker |
| --- | ---: | --- | --- |
| Posterize | 1 | scalar stored float | first blocker; exact exposure reaches `fwidth(vec3)` |
| FXAA | 2 | scalar to `uint`, scalar to `int` | hidden by vector global |
| Grain | 1 | scalar to `uint` | hidden by globals |
| Snow | 1 | scalar to `uint` | hidden by globals; public adapter |
| Normal Map | 1 | scalar to `uint` | hidden by aggregate globals |
| Test Pattern | 1 | `vec2` stored value | hidden by unproved loop; vector round runtime absent |

Posterize's exact site is `main` `60:34-60:51`, with a stored scalar float
result; its next site is `fwidth(scaled)` at `80:19-80:33`. The other scalar
rounds have distinct key, source, owners, consumers, and domains. None inherits
Gather's round-under-immediate-int profile or its normalized `[0,1]` proof.

## XOR, remaining vector indexing, varyings, and singletons

### Scalar XOR

Two keys are scalar-XOR-first:

- `synth/perlin:perlin` has exactly two nested `uint ^ uint` rvalues in
  `hash3`, both at normalized line 73. Its existing `uvec3 ^= uvec3` sites are
  already covered by vector-bitwise support. With exact scalar XOR bypassed,
  the program validates and emits with no later blocker. Its default define is
  exactly `{"DIMENSIONS": 2}`, source SHA-256
  `9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318`,
  and public dispatch is direct `canonicalFactory268`, text SHA-256
  `55ea0bb422438d8ed6182fc4f587395de5321dc8f8ca0588c0202f23732ca0f4`.
  The scalar sites are in a function unreachable from resolved 2D `main`, so
  output oracles alone cannot prove their spelling; typed/code-shape and direct
  unsigned-word tests are mandatory.
- `synth/bitwise:bitwise` has four `int ^ int` sites. Removing only XOR exposes
  scalar `&` immediately, followed by `|` and `~`; it is not part of a bounded
  XOR-only slice.

### Remaining vector indexing

`filter/grade:lut` is the sole index-first key. It has exactly twenty
induction-indexed local `vec3[i]` sites under four proved three-trip loops:
eight writes and twelve reads across `srgbToLinear`, `linearToSrgb`,
`lutHardLight`, and `lutSolarize`. This is a dynamic proved-loop lvalue/read
ABI, not Task 25's eleven fixed literal lanes over one `hsv` local. It requires
range/induction authentication and runtime/lvalue lowering and remains
separate.

### Varyings

- `filter/grime:grime` consumes read-only `in vec2 v_texCoord` symbol 55.
- `filter/wormhole:deposit` consumes read-only `in vec4 vColor` symbol 4.

Both public factories are direct canonical identities with no adapter. Native
`PixelContext` supplies neither varying; their producer/interpolation/default
and pass-routing semantics are undefined. Wormhole's value belongs to a vertex
producer rather than a texture pixel, and Grime cannot silently substitute UV
without a public-compatibility proof. This is a stage ABI, not a two-key field
addition.

### Singleton first blockers

| Key | First blocker | Exact-exposure result |
| --- | --- | --- |
| Caustic | `floatBitsToUint` | reaches scalar XOR |
| Glitch | `mat4` | type/runtime matrix frontier |
| Extrude | `all` | reaches `bvec2` |
| Lighting | `reflect` | reaches local `float[9]` |
| Posterize | scalar `round` | reaches `fwidth(vec3)` |
| Rotate | matrix return | function ABI frontier |
| Watercolor Simplify | `inout` | copy-in/copy-out alias ABI |
| Waves | `any` | reaches `bvec2`, then derivatives |
| Focus Blur | sampler helper type | validator-clean; emitter-only gap |
| Curl | `tanh` | reaches unsupported `mod` overload |
| Remap | uniform block | resource/layout ABI |

No singleton above becomes a lower-risk one-feature addition than Smooth Edge.

## Public adapter audit

The pinned public CPU runtime files hash to:

```text
canonical-kernels.js  e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56
catalog.js            d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4
adapters/index.js     40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267
```

Of the projected remaining 85, **77** public factories are direct canonical
identities and **8** are adapter-backed:

```text
classicNoisedeck/bitEffects:bitEffects
classicNoisedeck/fractal:fractal
filter/historicPalette:historicPalette
filter/median:median
filter/palette:palette
filter/reindex:nmReindexStats
filter/snow:snow
synth/julia:julia
```

Any future slice containing one of those eight needs adapter-specific parity
and cannot count raw canonical output as public truth. Smooth Edge, Perlin,
Focus Blur, all 17 derivative-family keys, Grade LUT, both varying keys, and
the non-adapter singletons audited above are direct identities. Direct identity
removes compatibility indirection; it does not remove compiler/runtime ABI
risk.

## Ranked next three bounded slices

| Rank | Exact bounded slice | Unlock | Risk | Reason |
| ---: | --- | ---: | --- | --- |
| **1** | Smooth Edge exact `LUMA_WEIGHTS` literal `const vec3` | **1** | Medium | One immutable constructor, one helper read, existing vector/dot lowering, direct public identity, no later blocker or execution-ABI change |
| **2** | Perlin exact two nested scalar `uint ^ uint` sites under `DIMENSIONS=2` | **1** | Medium | No later blocker and direct public identity, but scalar unsigned-word semantics are new and the sites are unreachable in the default output path, requiring direct structural tests |
| **3** | Focus Blur exact two borrowed sampler-helper parameters | **1** | Medium-high | Validator-clean and fixed 64-trip/direct-public, but establishes a user-function resource borrowing/call ABI with two sampler permutations |

Task 26 should select rank 1 only. A later brief must remain one-key,
source/declaration/use-closed and must not establish general aggregate globals.
Do not bundle Perlin, Focus Blur, derivatives, Grade LUT, other vector globals,
or adapter-backed work.

## Verification and stop boundary

Read-only evidence gathered:

- exact 85-key projected first-validator/emitter census;
- fresh typed declaration/function/resource/interface and stable-symbol use
  inspection for Smooth Edge;
- fresh inline projection over all sixteen scalar/vector-global programs;
- Smooth Edge validator, emitter, and C++20 warnings-as-errors syntax probe;
- exact derivative builtin site/type/owner census for 16 keys plus Posterize;
- native `PixelFn`/`PixelContext`/`run_pass` inspection and public CPU
  record/replay derivative-wrapper inspection;
- round-site census across all projected remaining programs;
- Perlin and Bitwise scalar-XOR site inventory and later-blocker probes;
- exact Grade LUT twenty-site read/write census and loop proof;
- varying symbol/resource inspection;
- singleton exact-exposure probes;
- runtime public/canonical object-identity and adapter-map audit for all 85;
- Task 24 oracle `--check` after the requested brief correction;
- projected count/list recomputation for Tasks 25 and 26.

Recommended next action only after final Tasks 24 and 25 acceptance is a
dedicated one-key Smooth Edge public-factory oracle package, followed by an
exact Task 26 scope/proof brief. Freeze declaration/source/function/interface
identity, lane bits/order, helper-only closure injection, both smooth paths,
threshold and clamped-neighbor behavior, F32/RGBA8 output, writes/escape
negatives, generated isolation, stack, and native code shape.

Stop before that oracle, Task 26 brief, design, implementation, or any
repository/Git change. If final Task 24/25 bytes alter the projected baseline,
rerun and rerank rather than carrying this audit forward.
