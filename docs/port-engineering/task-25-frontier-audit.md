# Projected post-Task-24 remaining-frontier audit

Date: 2026-08-11  
Scope: read-only corpus, semantic IR, capability validator, typed emitter,
native vector/runtime, canonical-factory, public-dispatch, and adapter
inspection. No repository file or Git state was changed. This is not a Task
25 brief, oracle, design, or implementation authorization.

## Decision

The requested post-Task-24 baseline is:

| State | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Projected exact Task 24 | **123** | **125** | **87** |

The live checkout inspected for this audit is still the accepted Task 23
state, **122 / 124 / 88**, and `filter/pixelSort:gatherSorted` is not yet in
`typed_slice.json` or generated output. Therefore every post-Task-24 number in
this document is an explicit projection: it adds exactly the frozen Task 24
Gather Sorted key, excludes that key from the remaining census, and assumes no
other byte or behavior change. Final Task 24 acceptance must rerun this audit.

The best bounded Task 25 candidate is the two-key literal-`vec3` lane-index
slice:

```text
classicNoisedeck/lensDistortion:lensDistortion
filter/prismaticAberration:prismaticAberration
```

Both programs are direct public/canonical identities with no adapter. Their
only current blockers are eleven literal lane selections over the resolved
main-local `vec3 hsv`: eight in Lens Distortion and three in Prismatic
Aberration. The exact inventory is six direct `=` lvalues and five reads. A
read-only IR projection replacing only those authenticated nodes with the
equivalent fixed `x/y/z` swizzles passes the current validator and emitter for
both keys with no later blocker.

Conditional projection after adding only this two-key slice:

| State | Typed | Public | Publicly unported |
| --- | ---: | ---: | ---: |
| Exact Task 24 | 123 | 125 | 87 |
| Literal-`vec3` Task 25 | **125** | **127** | **85** |

The projected newline-terminated typed/public sorted-list SHA-256 values are
`9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4`
and `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`.

Task 24 does not generically expose scalar `round`: its frozen contract is
Gather-Sorted-key/site/consumer-specific. Posterize therefore remains
production-blocked at its own `round` node. A diagnostic Posterize-specific
round exposure reaches `fwidth(vec3)` immediately; it does not make Posterize
a bounded scalar-numeric follow-on. Derivatives still require a real
fragment-neighborhood/quad execution ABI.

## Inputs and hard gate

Corpus revision is
`a024dc3a960cc44af454abc7aebce50456c194e6`.

The frozen/current Task 24 artifacts inspected here are:

| Artifact | SHA-256 |
| --- | --- |
| `task-24-frontier-audit.md` | `fa4e0481ea50534be05923cf2c673b9f45195315121fbac7cbd05bece4f21220` |
| `task-24-brief.md` | `aa2b61355b8d7ad8cf9fe3cffa20e0a0e38658d8edfe06108dbcff3d19200d51` |
| `task-24-oracle-generator.mjs` | `35d20a4428af390ed437f3c829a250a1974d254b66712c900d684d54a7e682d6` |
| `task-24-oracles.json` | `07dd6f31c3e2b5451cbde8fc0ae6f68ec7c3b06cd6296222ac938cdcee37a72a` |
| `task-24-oracle-report.md` | `b33894f0d69c97de5392d686bc9d5b469d672fc59f522b7b79c15604ae4299f6` |
| `task-24-projection.py` | `a864160c1c92f198003dbb1371d5814f268a18365d2775612f27bcc712d41409` |

`node task-24-oracle-generator.mjs --check` passed during this audit.

The live accepted-Task-23 files relevant to this projection are:

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/parser.py` | `1b2114be2712eba63dcb8651323a9387a9f049420ef024e09c57fe8f101849cc` |
| `tools/glslcpp/frontend/typed_ir.py` | `7e16d088d7ffe90b7b6cc11dfff27d9df413ff4ffcdd13f9648fc4c35c91272c` |
| `tools/glslcpp/frontend/semantic.py` | `77a6c23e9369436b6d5e65a6ce8b95bec2a496266fdb9859e84a461f3f8bbeb6` |
| `tools/glslcpp/frontend/body_semantic.py` | `4a6dc290c22b6a372d0837040596341a142284fccf42a0eaf7d657a78b419f59` |
| `tools/glslcpp/generate_typed_slice.py` | `3a77d1702484e6ffed83c52e20d7b79315536f39150b43daed134b75bae2133d` |
| `tools/glslcpp/emit_typed_cpp.py` | `54bdacfc2912c6a33a1da76820ef4182d9722a2b5f03ea7f08f43d15bd8eb1f3` |
| `tools/glslcpp/typed_slice.json` | `4af84d22d3272f98f8d1698f34874b1fb249ad0ec9deec2c87cb8f9b354d163f` |
| `src/typed_generated/typed_manifest.json` | `d979fe5d968030cfc3ec9d688367b8b4418b9a841a6f612d65eac03ed5bd4184` |

Live checks passed, but correctly reported the pre-Task-24 state:

```text
generate_typed_slice: typed slice ok (122 programs)
check_corpus: ok
typed/public/unported/corpus = 122/124/88/212
typed list SHA-256  = 9db3013a6b0f78d0b95fcb6713c54ace95e82d1545e796e7a380add23c009f0b
public list SHA-256 = 2b84fff4d6f35aec1ac6bcc35188d9893e3194c90b9c428775a7308ce1f6281a
```

The exact Task 24 projection is 123/125/87, typed/public list hashes
`df7750a48a77733e50f0e20072e291c2404e761932f6df8ddbcf8793d58fb6ac`
and `bcf196794ff17ec62c1121347b3fe49a0907baa7ce3c3bd51352ec8a51fbac4e`,
with Gather Sorted at zero-based position 51 between Find Brightest and
Luminance. Any final Task 24 count, key, source/profile identity, or generated
isolation drift invalidates this projection.

## Projected first-blocker census for the 87

Task 24's exact profile admits no other program. Excluding only Gather Sorted,
the remaining projected first results are:

| First result | Count |
| --- | ---: |
| Unsupported top-level global declaration | 31 |
| Unproved counted-loop program | 19 |
| `dFdx` derivative | 11 |
| `fwidth` derivative | 5 |
| Counted loop exceeds an existing safety cap | 3 |
| Vector/component index expression | 3 |
| Scalar XOR outside the current overloads | 2 |
| Varying/stage interface | 2 |
| Scalar `round` (Posterize; not admitted by Task 24's exact profile) | 1 |
| Sampler parameter reaches emitter type gap | 1 |
| `all` builtin | 1 |
| `any` builtin | 1 |
| `floatBitsToUint` builtin | 1 |
| `reflect` builtin | 1 |
| `tanh` builtin | 1 |
| Matrix return ABI | 1 |
| `inout` parameter ABI | 1 |
| `mat4` type | 1 |
| Uniform block/resource ABI | 1 |
| **Total** | **87** |

All are validator failures except `mixer/focusBlur:focusBlur`: it passes the
validator, then the emitter rejects its `sampler2D` helper parameters.

The three index-first keys are exactly:

```text
classicNoisedeck/lensDistortion:lensDistortion
filter/grade:lut
filter/prismaticAberration:prismaticAberration
```

Grade LUT is not part of the proposed slice. It has twenty induction-indexed
read/write `vec3[i]` sites under proved three-trip loops, rather than literal
lanes on the one `hsv` local.

## Candidate: exact main-local literal `vec3` lane selection

### Provenance and public factory identity

| Field | Lens Distortion | Prismatic Aberration |
| --- | --- | --- |
| Key | `classicNoisedeck/lensDistortion:lensDistortion` | `filter/prismaticAberration:prismaticAberration` |
| Source | `sources/classicNoisedeck/lensDistortion/lensDistortion.glsl` | `sources/filter/prismaticAberration/prismaticAberration.glsl` |
| Raw bytes / SHA-256 | 8269 / `f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444` | 4247 / `513eac95fdf7f67a6839ee5d96e5bbfd76b6cfa62d3254df6fed23d8effe380e` |
| Normalized bytes / SHA-256 | 7723 / `6586c49b079a3b0f4aa3538c8e735e70db088ff2e5d2ea1037e9e9c5486fdf52` | 3907 / `1c157e7f3dc7c9c122cc185812cd2988a98a52024055a482265bded7561a0860` |
| Authoritative default defines | `{}` | `{}` |
| Functions / function-tuple SHA-256 | 8 / `263870c469a9dc3b1f4d5f3a2498864c6da4ff4eaf2cc3efaf198376e4d304c1` | 5 / `6949577823e5eccde21335182d379a590db90188f004f3d479503ac33990cf24` |
| Public/canonical factory | exact same `canonicalFactory10` object | exact same `canonicalFactory117` object |
| Factory-text SHA-256 | `151b1e868c7d2f9a446a8778d170260e5003fec540afb2623088bbf34ca8adcf` | `2eab8943387658c1c28f4e089edd9b248bf441b2b77145ea137c7f979c5def02` |
| Adapter entry | absent | absent |
| Diagnostic projected C++ | 27,446 bytes / `6cfa9d58cbc096b7372b00b17b4ed0b146236a4738acef7870cad05593a57fc5` | 13,316 bytes / `8d6c98fed4ab2d2a2130566081386cdfb74d01ae84c11b198a1be08ae187155f` |

The pinned canonical runtime is
`e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`.
Runtime public-dispatch identity, not filename inference, proved both public
factories are the canonical functions and that neither key is in
`canonicalAdapterFactories`.

Lens binds one sampler and twenty ordinary uniforms, and outputs one `vec4`.
Prismatic binds one sampler and ten ordinary uniforms, and outputs one `vec4`.
Both use texture sampling and neither uses derivatives. Neither contains a
loop, source global, array, matrix, struct, UBO, varying, sampler parameter, or
non-`in` helper parameter behind this blocker.

### Exact typed-site inventory

Every selected node has result type `float`, typed category `lvalue`, a direct
base `id` resolving to the named automatic `vec3 hsv`, and an `int` rvalue
literal in `{0,1,2}`. Read-vs-write is determined by the authenticated parent:
only a direct child-zero of plain `=` is a write.

Lens Distortion's `hsv` is symbol 72 in `main`:

| Span | Lane | Exact role |
| --- | ---: | --- |
| `236:9-236:15` | 0 | direct `=` lvalue |
| `236:24-236:30` | 0 | read in RHS arithmetic |
| `236:65-236:71` | 0 | read in RHS arithmetic |
| `237:9-237:15` | 1 | direct `=` lvalue |
| `247:9-247:15` | 0 | direct `=` lvalue |
| `247:26-247:32` | 0 | read in RHS arithmetic |
| `248:9-248:15` | 1 | direct `=` lvalue |
| `260:46-260:52` | 2 | read as the sole `vec3(...)` splat input |

Prismatic Aberration's `hsv` is symbol 55 in `main`:

| Span | Lane | Exact role |
| --- | ---: | --- |
| `131:5-131:11` | 0 | direct `=` lvalue |
| `131:22-131:28` | 0 | read in RHS arithmetic |
| `132:5-132:11` | 1 | direct `=` lvalue |

Thus the complete slice has **11 sites: 6 writes and 5 reads**, with lane
incidence 0/1/2 = 7/3/1. There is no compound assignment, increment/decrement,
dynamic or negative index, alternate base symbol, parameter/global/uniform
base, or nested selection.

The local is definitely initialized as `vec3(1.0)` before either branch and is
reassigned from `rgb2hsv(color.rgb)` before the selected lane operations. In
Lens, the two groups at lines 236-237 and 247-248 are in the mutually exclusive
`mode == 0` and `else` paths. Prismatic contains only the latter path.

The read-only projection maps `0/1/2 -> x/y/z`. Existing emission then produces
`glsl::swizzle<I>(hsv)` for reads and
`glsl::set_swizzle<I>(hsv, rhs)` for writes. The one-lane `set_swizzle` first
converts the RHS through `convert_lane<float>`, retaining the existing F32
storage boundary. No runtime subscript, bounds branch, pointer arithmetic,
allocation, virtual dispatch, callback, map, or variant is required.

### Required fail-closed boundary for a later brief

A Task 25 brief should authenticate, independently at validator and emitter:

1. exactly the two sorted keys, exact source hashes, and exact empty define
   maps above;
2. exactly the 8/3 ordered site inventories, spans, `main` ownership, stable
   base symbols 72/55 named `hsv`, result/base/index types, literal values,
   typed categories, and parent roles;
3. only scalar reads or direct plain-`=` lvalues; no compound assignment,
   increment, alias, escape, `out`/`inout` actual, or delayed indexed lvalue;
4. canonical checked lowering to the existing fixed swizzle read/write paths,
   preserving RHS-before-storage behavior and F32 lane conversion;
5. rejection of Grade LUT, every dynamic/induction/uniform index, lanes outside
   `0..2`, other vector widths, other local/parameter/global/uniform bases,
   arrays, matrices, structs, samplers, nested indexing, and derivatives.

This should be a closed key/source/site profile, not a global
`typed-expression-index` capability. Frozen public-factory output and mutation
oracles are still required before any brief; this audit creates none.

### Count/list projection

With Task 24 and only these two keys, zero-based final typed positions are:

```text
2   classicNoisedeck/lensDistortion:lensDistortion
52  filter/pixelSort:gatherSorted
59  filter/prismaticAberration:prismaticAberration
```

Their final immediate neighbors are:

```text
classicNoisedeck/composite:composite
classicNoisedeck/lensDistortion:lensDistortion
classicNoisedeck/refract:refract

filter/pixelSort:findBrightest
filter/pixelSort:gatherSorted
filter/pixelSort:luminance

filter/plasticWrap:pwSpec
filter/prismaticAberration:prismaticAberration
filter/reindex:nmReindexApply
```

## Posterize after Task 24: round does not solve derivatives

Task 24's exact identity profile authorizes only Gather Sorted's `round` at
`24:26-24:66`, immediately consumed by `int`. It deliberately does not add
`round` to the global capability vocabulary. Posterize therefore still fails
production validation at its independent scalar site:

| Field | Posterize value |
| --- | --- |
| Key | `filter/posterize:posterize` |
| Raw / normalized SHA-256 | `460910a8d1103eca5cc0b4df82f39fd91fbc447b9a815250ae7d34dfab8ee5b2` / `4781d189690f57de2b57aebaaa946eba004b1c57272f32a18d1f0ce06ce44393` |
| Defines | `{}` |
| Public/canonical factory | exact same `canonicalFactory116` object |
| Factory-text SHA-256 | `317e38c428bda5e89258c3bc64cae3fbfb54ffa43e0b02f98b2329f542c546ed` |
| Adapter entry | absent |
| Resources | one sampler, three ordinary uniforms, one output; derivatives yes |
| Round site | `main`, `60:34-60:51`, scalar float rvalue `round(levels_raw)` |
| Next diagnostic blocker | `main`, `80:19-80:33`, `fwidth(scaled)`, `vec3 -> vec3` |

The two round domains also differ. Gather's authenticated value is a
nonnegative normalized coordinate multiplied by `width - 1`, and the result
is immediately converted to `int`. Posterize rounds user-controlled
`levels_raw = max(levels, 0.0)` to a stored float and later uses that float in
quantization arithmetic. Gather's signed-zero/huge-value consumer proof cannot
be borrowed for Posterize.

Posterize's `fwidth` is inside the uniform `if (antialias)` branch, but its
operand is `scaled`, derived from the current sampled texel's nonlinear
sRGB-to-linear, gamma, and level arithmetic. GLSL `fwidth` requires neighbor
invocations (`abs(dFdx) + abs(dFdy)`), not merely the current `Surface` value.
The current CPU `PixelFn`/`run_pass` contract invokes one pixel independently
and defines no quad membership, neighboring invocation values, helper-lane
policy, tile-border ownership, edge derivative, or scheduling rule.

The derivative-first family remains sixteen keys (eleven `dFdx`, five
`fwidth`). A future Posterize-specific round profile would expose a
seventeenth derivative-blocked program. Runtime identity inspection found all
seventeen public factories are direct canonical factories and none has an
adapter, but that removes only compatibility indirection; it does not supply
derivative semantics. Adding builtin names or a current-pixel finite
difference would be incorrect.

## Remaining top-level globals

The 31 global-first programs are unchanged by Task 24's exact Gather profile.
They split into materially different representations:

### Sixteen initialized read-only scalar/vector-constant programs

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

A fresh in-memory inline-constant projection found only
`filter/smooth:smoothEdge` validator/emitter-clean. Exact later blockers for
the other fifteen are:

| Later blocker | Keys |
| --- | --- |
| Scalar/word `&` | Bit Effects, Glyph Map |
| `bvec3` | Edge |
| local `float[9]` | Emboss |
| `round` | FXAA, Grain, Snow |
| induction/dynamic `vec3[i]` | the five Grade programs |
| `floatBitsToUint` | Scanline Error |
| varying/stage interface | Texture, Wobble |

Smooth Edge has exactly one source declaration,
`const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114)`, read once as the second
argument of `dot(rgb, LUMA_WEIGHTS)` in helper `luminance`. It is a valid
one-key runner-up, direct public/canonical `canonicalFactory140`, text SHA-256
`732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e`,
with no adapter. It is separate from local lane selection because it adds
aggregate source-global authentication, dependency closure, and helper-local
lifetime/materialization.

### Seven read-only `const mat3` programs

```text
classicNoisedeck/cellNoise:cellNoise
classicNoisedeck/colorLab:colorLab
classicNoisedeck/moodscape:moodscape
classicNoisedeck/shapeMixer:shapeMixer
classicNoisedeck/shapes:shapes
filter/adjust:adjust
filter/colorspace:colorspace
```

These require separately authenticated matrix constructors, column order,
matrix/vector operations, dependency closure, and automatic-local lifetime.
They are not scalar/vector-global near-matches.

### Mutable arrays and aggregate tables

- Cell Refract and Kaleido each use five mutable, uninitialized global
  `float[9]` tables.
- Historic Palette and Palette use source aggregate tables and public adapter
  factories rather than canonical identities.
- Normal Map uses `ivec2[9]` and two `float[9]` source tables.
- OSD and Spooky Ticker use `int[80]` source tables.
- `synth/shape:shape` has mutable uninitialized `aspectRatio` and
  `globalCoord`; it must never enter a source-constant path.

The exact Task 23 source-global integer profile does not generalize to any of
these declarations. An intentionally broad literal-int diagnostic still makes
`filter/reindex:nmReindexStats` structurally validator/emitter-clean, but it
remains excluded: its public `reindexStatsFactory` is not canonical identity
and its eager-F32/top-down adapter behavior differs from `canonicalFactory120`.

### Public adapter holds

Of the 31 global-first programs, 27 are direct canonical public identities and
four are public-adapter holds:

| Key | Public factory | Public factory-text SHA-256 | Canonical status |
| --- | --- | --- | --- |
| `classicNoisedeck/bitEffects:bitEffects` | `bitEffectsFactory` | `0fc0f91500e454c70b2e08b43815eca3efd9c02e0d60b3e6f28c18fb1041bc06` | differs from `canonicalFactory0` |
| `filter/historicPalette:historicPalette` | `historicPaletteFactory` | `f6ff289a0f93e4ddaa5a2f77b0ec4e3645d52007acbaf1f38c0081965adbf7d5` | no canonical public identity |
| `filter/palette:palette` | `paletteFactory` | `547bb6741b27cc12d6ed488cd1bbe12284ab3b916cdaefe1c747a63125523040` | no canonical public identity |
| `filter/snow:snow` | `snowFactory` | `1bca4cc40a2c6dcb5c11e3a25329a582303cd2c46e8e25ffef379ae3b8bbb587` | differs from `canonicalFactory142` |

The adapter registry SHA-256 is
`40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267`.
Any future slice containing one of these keys needs adapter parity/oracles
before it can be counted public.

## Risk-adjusted next bounded slices

| Rank | Bounded slice | Direct unlock | Risk | Finding |
| ---: | --- | ---: | --- | --- |
| 1 | Exact main-local literal `vec3` lanes for Lens + Prismatic | **2** | Low-medium | Eleven finite literal lanes, direct canonical public factories, existing fixed swizzle/F32 storage paths, no later blockers |
| 2 | Smooth Edge exact literal `const vec3` | **1** | Medium | One helper-only read and otherwise clean/direct canonical, but establishes aggregate source-global closure/lifetime |
| 3 | Perlin exact scalar `uint ^ uint` | **1** | Medium | Two nested sites at line 73, direct canonical `canonicalFactory268`, but requires explicit unsigned-word semantics and exact `DIMENSIONS=2` define lock |
| 4 | Focus Blur exact direct sampler-helper ABI | **1** | Medium-high | Validator-clean/direct canonical and fixed 64-trip work, but changes user-function resource borrowing/call ABI |
| 5 | Derivative execution ABI | 16 first-blocked; 17 after Posterize round | High | Requires quad/neighborhood, border, tile, helper-call, and scheduling semantics; not a builtin-name slice |

Perlin's public factory is exact canonical identity with factory-text SHA-256
`55ea0bb422438d8ed6182fc4f587395de5321dc8f8ca0588c0202f23732ca0f4`.
Focus Blur is exact `canonicalFactory195`, factory-text SHA-256
`fb4c02c763ef42000b13bba3945cf4fd15e177a2ab2827372ce3b96aa3a778ff`,
and fails emission only because helper
`applyFocusBlur(sampler2D sceneTex, sampler2D depthTex, vec2 uv)` cannot yet
spell the sampler parameter type.

No generic global broadening, Grade-LUT dynamic indexing, Posterize/derivative
bundle, loop-cap increase, or adapter-backed Reindex Stats publication is
justified by this audit.

## Verification and stop boundary

Read-only verification performed:

- corpus and typed-slice `--check` on the live accepted Task 23 state;
- exact 87-key post-Task-24 projected validator/emitter first-blocker census;
- fresh semantic AST inventory of every selected index site, stable base
  symbol, literal lane, category, parent role, resource/interface, source hash,
  and function tuple;
- in-process transformation of only the 11 selected index nodes to fixed
  swizzles, followed by successful capability validation and typed emission;
- Posterize-specific diagnostic round exposure proving `fwidth(vec3)` is the
  next blocker;
- fresh inline-constant projection over all 31 global-first programs;
- runtime public/canonical function-object identity and adapter-map audit for
  both selected candidates, Posterize, all derivative candidates, Smooth
  Edge, Perlin, Focus Blur, Reindex Stats, and the global-first cohort;
- Task 24 oracle `--check`.

Recommended next action only after final Task 24 acceptance is a dedicated
two-key public-factory oracle package and then an exact Task 25 scope/proof
brief for the literal-`vec3` lane profile. Freeze branch-distinguishing Lens
and Prismatic renders, F32/RGBA8 output, every selected read/write mutation,
lane-range and parent-role negatives, source/factory/function/interface
identity, generated isolation, and native code shape.

Stop before that oracle, brief, design, implementation, or any repository/Git
change. If final Task 24 bytes alter counts, source identities, capabilities,
emission, or generated ordering, rerun and rerank rather than carrying this
projection forward.
