# Projected post-Task-26 remaining-frontier audit

Date: 2026-08-11  
Scope: read-only corpus, typed semantic IR, capability validator, typed C++
emitter, native value/resource ABI, public CPU catalog, canonical factories,
and adapters. No repository file or Git state was changed. This is not a Task
27 brief, oracle, design, or implementation authorization.

## Decision

The requested starting point is the exact projected Task 26 state:

| State | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Projected exact Task 26 | **126** | **128** | **84** |

This projection starts from the current 123-key typed slice, adds the exact
Task 25 Lens Distortion and Prismatic Aberration keys, and then adds only Task
26 Smooth Edge. The projected newline-terminated sorted typed/public list
SHA-256 values are respectively
`01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76`
and `d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3`.
Final Task 25 and Task 26 acceptance must rerun this audit; any corpus, source,
profile, IR, generated-order, public-factory, or adapter drift invalidates it.

The best bounded Task 27 slice is exactly one default-profile key:

```text
synth/perlin:perlin
```

Its only current blocker is the exact pair of nested scalar `uint ^ uint`
expressions in `hash3`. A read-only typed-tree projection replacing only those
two authenticated operators with a supported binary operator passes the
current validator and emitter with no later blocker. The actual implementation
must preserve `^`, not use that diagnostic replacement: emit the two sites as
ordinary `std::uint32_t ^ std::uint32_t`, with the typed AST's nested
parenthesization and no new runtime helper or general scalar-bitwise grant.

Conditional projection after only this exact key:

| State | Typed | Public | Publicly unported |
| --- | ---: | ---: | ---: |
| Exact Task 26 | 126 | 128 | 84 |
| Exact Perlin Task 27 | **127** | **129** | **83** |

The resulting typed/public sorted-list SHA-256 values are
`ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72`
and `37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883`.
Perlin is at zero-based typed position **123**, between
`synth/pattern:pattern` and `synth/polygon:shape`.

Risk is **medium** for the exact default profile. The code-generation change
is smaller than the runner-up interfaces, but the two admitted sites are dead
from the resolved `DIMENSIONS=2` entrypoint. Public image output therefore
cannot authenticate the new operator semantics. Task 27 needs structural IR,
emitter, compile, and direct unsigned-word tests in addition to ordinary public
output parity.

## Projection inputs and recomputed 84-key census

Corpus revision is
`a024dc3a960cc44af454abc7aebce50456c194e6`.

After excluding exactly Gather Sorted, Lens Distortion, Prismatic Aberration,
and Smooth Edge, the first validator/emitter results are:

| First result | Count |
| --- | ---: |
| Unsupported top-level global declaration | 30 |
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
| **Total** | **84** |

All are validator failures except `mixer/focusBlur:focusBlur`, which passes
the validator and fails emission at its first helper `sampler2D` parameter.
Task 26 removes exactly one global-first key; no other census bucket changes.

## Selected Task 27 identity and exact operator closure

| Field | Required observed value |
| --- | --- |
| Key | `synth/perlin:perlin` |
| Source | `sources/synth/perlin/perlin.glsl` |
| Raw bytes / SHA-256 | 10,882 / `9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318` |
| Normalized bytes / SHA-256 | 4,875 / `88cb30dfb53c75f2d1bf51e9f9b865dca48ffb528e6ff2f77dec224dab309f64` |
| Exact default defines | `{"DIMENSIONS": 2}` |
| Function count / tuple SHA-256 | 13 / `3dbb088e9f6a0ae35d25a3ae197008f62bc7932f3a31697f2ce3fdb05c3e1abc` |
| Whole-program SHA-256 | `a47c9ae9ef983c68c6c867296aaa33401841e5a089dddf9842630c6453e775bc` |
| Interface SHA-256 | `b8ff41d2d2259908c8efa422227f27b89469110330908e8eb34410319e878066` |
| `hash3` signature ID / body SHA-256 | 49 / `3c3253eaa535ee944476a6c5d60bcb8e66212482d3e4b5af44db96d0e1dfcc50` |
| Public/canonical factory | exact same `canonicalFactory268` object |
| Canonical factory text SHA-256 | `55ea0bb422438d8ed6182fc4f587395de5321dc8f8ca0588c0202f23732ca0f4` |
| Public adapter | absent |

The normalized IR contains exactly two scalar unsigned XOR nodes, both owned
by `hash3` signature 49:

| Site | Span | Expression SHA-256 | Left SHA-256 | Right SHA-256 | Parent |
| --- | --- | --- | --- | --- | --- |
| Outer | `73:18-73:33` | `31049e8d38c4a6d26d051659ccd435fb7715906fb861440b7904429f3514495c` | `f51b3a1264df7050a8528a5094da6d16c464978d1cb5c8b680461c9173d195cc` | `5387f564b5e3d096fd99fe10781613d0adab40bc86ebb50a00b79725118f7f08` | child 0 of the `float` constructor at `73:12-73:34`, SHA `98f5cc12b9b7d44fefc28337f7d4a2d605eb455d2b36f39f3e80296114e57e2b` |
| Inner | `73:18-73:27` | `f51b3a1264df7050a8528a5094da6d16c464978d1cb5c8b680461c9173d195cc` | `7a2954d83ebe2be4dfd2ca31558438ff5423668aa4bb593b349b489b7fc92023` | `d15d2568d9165294874cd3c76406e368a48b31c6834d2949d91f7ac4845a81cc` | child 0 of the outer XOR |

Both operands and both results are resolved `uint`. These are the source tree
for `float(q.x ^ q.y ^ q.z)`; associativity is the authenticated nested tree,
not a text substitution. The existing `uvec3 ^= uvec3` and `uvec3 >> uint`
sites remain covered by the current vector-bitwise implementation and do not
belong to the new scalar profile.

The exact interface is fourteen uniforms and one output, with no samplers or
derivatives:

```text
resolution:vec2@1
tileOffset:vec2@2
fullResolution:vec2@3
aspect:float@4
time:float@5
scale:float@6
seed:int@7
octaves:int@8
colorMode:int@9
ridges:int@10
warpIterations:int@11
warpScale:float@12
warpIntensity:float@13
speed:float@14
fragColor:vec4@15/out
```

Its two loops are already proved, effective depth one, maximum lexical product
8, entrypoint charge 28, and acyclic call graph. No loop, derivative, sampler,
array-index, varying, matrix, output-count, or execution ABI is exposed after
the XOR profile.

## Semantic boundary: source `uint` versus canonical JavaScript bitwise

The resolved default entrypoint reaches function IDs
`45, 46, 48, 50, 51, 52, 53, 54, 55, 56`; it does **not** reach `hash3` 49 or
`grad3` 47. `DIMENSIONS=2` selects the 2D `pcg`/`prng` path. Consequently:

- every public default-profile render is insensitive to both scalar XOR sites;
- a mutation of either site can remain output-identical and is not proof of
  correctness;
- Task 27 must authenticate the dead helper definitions because the emitter
  still emits them, while not pretending that an image oracle exercised them.

There is also a real future-profile distinction. The canonical JavaScript
helper spells the return as
`cpu_float((q[0] ^ q[1]) ^ q[2]) / 4294967296`; JavaScript scalar bitwise
operators produce a signed 32-bit result. The typed GLSL operands are
unambiguously `uint`, and direct C++ `std::uint32_t ^ std::uint32_t` preserves
the source's unsigned word. Task 27 should use the source-typed unsigned
meaning for these dead default-profile definitions. It must not claim tested
behavioral parity for `hash3`, and it must not authorize `DIMENSIONS=3`.
Adding a 3D profile later requires a separate public-compatibility decision
and oracle; it cannot inherit Task 27 merely because the helper text is
present.

The current C++ runtime contains only vector `glsl::bitwise_xor`; that helper
should remain unchanged. The exact scalar form is already a defined C++20
operation on `std::uint32_t`, so adding a generic scalar overload would widen
the surface without benefit. The validator and emitter should each recognize
only the authenticated key/profile/sites and emit direct nested scalar XOR.

## Closest alternatives

### Rotate: narrow value ABI, but still a function-signature frontier

`filter/rotate:rot` is the next-smallest candidate after Perlin:

- raw 1,197 bytes, SHA-256
  `c23e8462e8240f25a715fa3eb05e567269c8d410d27943ba346ebccdd0de1f8f`;
- normalized 964 bytes, SHA-256
  `e0e2b723289b08cbfcd6f1fc0a8481869e674de3cfedc0ec5df6d96f64748bb5`;
- exact empty define map;
- one helper, signature ID 10, `mat2 rotate2D(float)`, body SHA-256
  `f88f6345a607d84afbe28d4859e3afd70f0c75c0c0e51e4de42cc7f1e2051006`;
- direct public `canonicalFactory127`, text SHA-256
  `4dd2ffadbcf25ec3f88c090b014da6cd3ee7faa3ddea970f21714c873dfcf903`;
- no adapter, loop, derivative, array, varying, or later blocker.

The current validator rejects the matrix return, but the current emitter can
already spell `glsl::Mat2` by value, the four-scalar constructor, and the
existing `Mat2 * Vec2` use. This makes Rotate narrower than Focus Blur after a
fresh audit, but it still establishes a new authenticated function return
category and column-major constructor/value-return proof. It must remain a
separate one-key task.

### Focus Blur: borrowed sampler-helper call ABI

`mixer/focusBlur:focusBlur` is validator-clean but the emitter cannot spell
the two `sampler2D` parameters of helper signature 16:

```text
vec4 applyFocusBlur(sampler2D sceneTex, sampler2D depthTex, vec2 uv)
```

The helper body SHA-256 is
`fd9a2496e322b3b035258d1532ac4dd37c79f778a5c53c55a1231cfad24e00bb`.
`main` calls it exactly twice, first `(tex, inputTex, uv)` at `57:17-57:50`,
then `(inputTex, tex, uv)` at `59:17-59:50`. This requires an explicit
read-only borrowed-surface parameter representation and correct alias/order
preservation, not merely adding `sampler2D` to the ordinary `_TYPES` table.

Its one loop is proved for 64 trips, effective depth one and entrypoint charge
64. The maximum path performs 67 texture reads per pixel: one depth read and
64 scene reads inside the helper, plus two alpha reads in `main`. It is direct
public `canonicalFactory195`, text SHA-256
`fb4c02c763ef42000b13bba3945cf4fd15e177a2ab2827372ce3b96aa3a778ff`,
with no adapter. The fixed workload makes it bounded, but the borrowed
resource/call ABI is broader and riskier than Perlin's exact word expression
or Rotate's existing value representation.

## Other residual frontiers

### Remaining top-level globals

After Smooth Edge, 30 keys remain global-first. Fifteen have scalar/vector
constant declarations: Bit Effects, Edge, Emboss, FXAA, five Grade programs
(`creative`, `hslSecondary`, `primary`, `vignette`, `wheels`), Grain,
Scanline Error, Snow, Texture, and Wobble. They do not form a no-later-blocker
batch: their next blockers include scalar `&`, `bvec3`, local `float[9]`,
scalar `round`, induction `vec3[i]`, `floatBitsToUint`, and varying inputs.

The other fifteen require broader aggregate or state work: seven `const mat3`
sets; mutable global `float[9]` in Cell Refract and Kaleido; aggregate tables
in Historic Palette, Palette, Normal Map, OSD, and Spooky; and mutable synth
Shape globals. Task 26's exact immutable `vec3` constant does not authorize
any of these types, mutation/lifetime models, or downstream blockers.

### Dynamic Grade indexing

`filter/grade:lut` remains the sole index-first key. It has exactly twenty
induction-indexed local `vec3[i]` sites under four proved three-trip loops:
eight writes and twelve reads across `srgbToLinear`, `linearToSrgb`,
`lutHardLight`, and `lutSolarize`. Five other Grade keys reach the same family
only after their globals. This requires a range-authenticated loop-index
lvalue/read contract; it is not Task 25's fixed literal-lane profile.

### Derivatives

Eleven keys are first-blocked by `dFdx` and contain thirteen `dFdx` plus
thirteen paired `dFdy` sites. Five keys are first-blocked by six `fwidth`
sites; Posterize reaches a seventh `fwidth` only after its distinct scalar
`round`. Supporting these requires a real quad/neighborhood record/replay ABI,
defined borders, scheduling, and sampler interaction. A current-pixel finite
difference or name-only builtin addition is not sufficient.

### Varyings and singleton blockers

Grime consumes `in vec2 v_texCoord`; Wormhole Deposit consumes
`in vec4 vColor`. Texture and Wobble reach varying inputs after their globals.
`PixelContext` has no producer/interpolation/default contract for these stage
values, so none can be treated as ordinary UV or color bindings.

The remaining singleton first blockers stay independent:

| Key | First blocker | Next exposed boundary |
| --- | --- | --- |
| Caustic | `floatBitsToUint` | scalar XOR |
| Glitch | `mat4` | matrix type/runtime |
| Extrude | `all` | `bvec2` |
| Lighting | `reflect` | local `float[9]` |
| Posterize | scalar `round` | `fwidth(vec3)` |
| Rotate | matrix return | no later blocker, but function ABI |
| Watercolor Simplify | `inout` | copy-in/copy-out alias ABI |
| Waves | `any` | `bvec2`, then derivatives |
| Focus Blur | sampler helper type | borrowed resource/call ABI |
| Curl | `tanh` | unsupported `mod` overload |
| Remap | uniform block | layout/resource ABI |

## Public adapter audit

The pinned public CPU files remain:

```text
canonical-kernels.js  e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56
catalog.js            d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4
adapters/index.js     40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267
```

Of the projected remaining 84, **76** public factories are direct canonical
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

Perlin, Rotate, Focus Blur, Grade LUT, all derivative-first keys, and both
varying-first keys are direct identities. Direct identity removes adapter
indirection; it does not prove unreachable helper semantics or authorize a
new native ABI.

## Ranked next three bounded slices

| Rank | Exact bounded slice | Unlock | Risk | Reason |
| ---: | --- | ---: | --- | --- |
| **1** | Perlin exact two nested scalar `uint ^ uint` sites under exact `DIMENSIONS=2` | **1** | **Medium** | One source-typed word expression, no runtime helper or later blocker, direct public identity; dead from default entrypoint, so structural/direct-word proof is mandatory |
| **2** | Rotate exact `mat2 rotate2D(float)` value return | **1** | **Medium** | Emitter and `Mat2` runtime already represent the body/call; requires a closed matrix-return and constructor-layout proof but no resource or execution ABI |
| **3** | Focus Blur exact two borrowed sampler helper parameters and two call permutations | **1** | **Medium-high** | Validator-clean and fixed 64-trip/direct-public, but establishes surface borrowing, alias/order, and texture-resource call semantics |

Task 27 should select rank 1 only. It must not bundle signed bitwise operators,
Bit Effects, `DIMENSIONS=3`, scalar helpers, Rotate, Focus Blur, globals,
derivatives, Grade indexing, varyings, or adapters.

## Verification and stop boundary

This audit was produced from fresh parsing/semantic analysis of Perlin, Focus
Blur, and Rotate; validator and emitter probes; exact function/interface/hash
recomputation; resolved call-graph and operator-site traversal; typed/public
sorted-list reconstruction; and current public/canonical object-identity
checks. The diagnostic Perlin XOR bypass emitted 18,631 bytes of C++ with
SHA-256
`583e3b1b74784a4fb1f8e57350b8da7bc1ae4997a2f1a8fee4c98e686c732b7b`
and exposed no later blocker. That diagnostic hash is not an implementation
target because the temporary tree used `+` solely to query the remaining
frontier.

A later Task 27 brief should freeze the exact source/profile/tree identities,
the two unsigned sites and parent closure, default-path non-reachability,
direct-public identity, generated nested C++ spelling, and negative controls
for foreign keys/sites/types/operators/defines/reachability. It should require
warnings-as-errors compilation, direct high-bit unsigned XOR word tests, and
ordinary default public render parity while explicitly recording that the
render does not exercise `hash3`.

Stop after this audit. No Task 27 brief, oracle, design, implementation,
generated source, runtime change, repository edit, or Git operation is
authorized by this document.
