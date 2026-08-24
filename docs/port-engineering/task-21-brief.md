# Task 21 Degauss scope and proof brief

> **Status:** read-only pre-implementation contract. Stop before implementation.
> This brief authorizes no repository edit and no Git operation. Implementation
> may begin only after independent scope review and accepted Task 20 evidence.

## Goal and exact boundary

Add exactly one already-supported factory:

```text
filter/degauss:degauss
```

This is the `current-vocabulary-degauss-v1` source profile. It adds no
capability, compatibility transform, proof kind, type, operator, builtin,
numeric exception, loop rule, resource ABI, or runtime helper. Degauss must be
published only after its exact source, typed tree, interface, binding route,
canonical factory, and nine direct-canonical surfaces are authenticated.

Do not include `filter/crt:crt`, even though CRT also passes the current
validator and emitter. Do not use Degauss as authority for another key.

## Baseline precondition and current uncertainty

The repository inspected for this brief is the accepted post-Task-19 baseline
while Task 20 is still a projected/in-flight addition. The independent
frontier audit projects:

| State | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Accepted post-Task-19 repository | 113 | 115 | 97 |
| Required accepted post-Task-20 precondition | 114 | 116 | 96 |
| Task 21 Degauss result | **115** | **117** | **95** |

The corpus remains exactly 212 programs. The two separately maintained public
factories remain `filter/invert:inv` and `synth/solid:solid`.

Task 21 must not be implemented on the currently projected state. First require
Task 20's final review, 114/116/96 counts, exact Sacred native parity, exact
generated output, and clean full gates. At that point record SHA-256 values for
the accepted Task 20 versions of every Task 21-owned file and generated output.
If Task 20's accepted interfaces, catalog, counts, or files differ from this
brief's projection, stop and amend/review Task 21; do not silently stack onto a
moving baseline. Consequently, this brief freezes Degauss and oracle identities
but intentionally does not invent post-Task-20 generated-file hashes.

## Frozen review artifacts

| Artifact | SHA-256 |
| --- | --- |
| `task-21-frontier-audit.md` | `2f4665fa7a7d6471291030c02b3e259a797a95d33dd15dabd3b10433749ec7b0` |
| `task-21-oracle-generator.mjs` | `0c1f12904e1c17a39c61055596be9f0d46ecded252a9d5c7cf1339653472c5c9` |
| `task-21-oracles.json` | `bddb1ca8f8b7a8b905412318c48414594736ca4a972c440da7e8c3525b31bb38` |
| `task-21-oracle-report.md` | `4196f7a238c63eadb2e167b3f76528b620cea56fabad999525c8fbc5826f02fc` |

The generator's `--check` mode independently reproduced the frozen JSON at
brief time. The external canonical checkout is oracle provenance only; it must
not become a CMake, generator, test-runtime, or installed-library dependency.

## Exact Degauss identity and numeric contract

| Field | Required value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Key/runtime key | `filter/degauss:degauss` |
| Effect/pass | `filter/degauss`, pass 0 `main` |
| Source | `sources/filter/degauss/degauss.glsl` |
| Raw bytes / SHA-256 | 10,803 / `915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c` |
| Normalized bytes / SHA-256 | 10,512 / `7d413b240236506511f405319025281a92eb1108c6193ef26a6d0d7bcbae7560` |
| Runtime defines | exactly `{}` |
| Numeric literal contract | exactly `glsl-f32` |
| Compatibility transform | exactly none; no map entry, manifest spelling `none` |
| Canonical factory | `canonicalFactory45` |
| Factory-text SHA-256 | `f515a7ac409c98fc420d9fa9a7e460eb37018b34e3be40419191fc7655a29c38` |
| Canonical generated runtime SHA-256 | `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Function tuple SHA-256 | `f68d742e44e341c1332f8c37ac8544aaa8c5bef979e496a27d45ac28ba48f95a` |
| Whole-program SHA-256 | `73e7e3e3b5e0b7ee9b4e1558d51fc14a01e9820c89674a0b5e42e568bec8d13d` |
| Interface SHA-256 | `6ceb3a3a3c7b0263b29d9950790bbe24b186759a4048b593b0a5447b733ae227` |
| Typed shape | 17 functions, zero loops, acyclic call graph |

Hash contracts are exact and must be implemented literally:

```python
sha256(repr(program.functions))

sha256(repr((
    program.key, program.source, program.raw_source, program.declarations,
    program.functions, program.resources, program.body_status,
    program.local_type_names, program.structs, program.uniform_blocks,
    program.interface_symbols, program.builtin_symbols,
    program.counted_loop_proof, program.preprocessor_defines,
)))

sha256(repr((
    program.declarations, program.resources, program.local_type_names,
    program.structs, program.uniform_blocks, program.interface_symbols,
    program.builtin_symbols, program.preprocessor_defines,
)))
```

The whole-profile tuple deliberately excludes optional Task 17-20 proof fields
so the Degauss identity is stable across the accepted Task 20 IR extension.
Separately require `fixed_nine_table_proof`,
`fixed_grid_counter_store_proof`, `fixed_array_in_parameter_proof`, and
`fixed_affine_centers13_proof` all to be `None`; any carried foreign proof is a
profile failure.

The canonical factory-text hash can only be reauthenticated by the external
oracle generator. Store its constant in the profile/report as provenance, but
do not pretend the C++ repository can re-hash JavaScript factory text without
adding a forbidden dependency.

`glsl-f32` means every authored GLSL float literal crosses an F32 boundary
before participating in the existing Number-compatible scalar evaluation.
The source `TAU` literal is `6.28318530717958647692`; its required F32 value is
`6.2831854820251465`, word `0x40c90fdb`. Retain existing double scalar
temporaries, F32 vector/storage/builtin boundaries, and `-ffp-contract=off`.
Do not add a `source-double` map entry or any Degauss-specific arithmetic
rewrite.

## Typed functions and body locks

The function tuple hash is authority for the complete tree. The following
per-function identities are additional drift diagnostics:

| ID | Function | Top-level body statements | `SHA256(repr(function))` |
| ---: | --- | ---: | --- |
| 52 | `as_u32` | 1 | `5b794fbe001df4116421749d5d0378b6088169d370876fc27757e01ba234b387` |
| 53 | `clamp01` | 1 | `4c77ec274b621bf6b9621b72dff5cf2653f468fd08610b13d16d2d4e301c5114` |
| 54 | `compute_noise_value` | 14 | `76e9489c1e667d2906e040ed25e707f5cea3bd15c27eade92078c466fd6b8fdf` |
| 55 | `freq_for_shape` | 5 | `7c20f25c092dbdd8b75891e74a498022a3a68a74dd8c9aa93a1f8f95ce71cdd9` |
| 56 | `main` | 27 | `e7a5c14a35384ba7174f8af83b428fa412b855678b9d626a7b79a9c5779b04d5` |
| 57 | `mod289_vec3` | 1 | `6a515431e7e453f7106fbb56e352302de98d21ff1578db537ea9b24e53aafbb6` |
| 58 | `mod289_vec4` | 1 | `26e443d7caf37c61b0e1b51fd96ce8f7a0a777e5cbf533487c3c13bc996196c9` |
| 59 | `normalized_sine` | 1 | `4056ee25e08f248238b5308b0a724c80885a04df8b3708e2af2c9b8411efe328` |
| 60 | `periodic_value` | 1 | `717462992b550c078e3bcbcfa4693f7cf48716eca4b8bae02549f3a4bc2aa1a5` |
| 61 | `permute` | 1 | `107a98b3f0a23f2129f707ed9092be4cd36e397984b606b0d37ea2db315d174c` |
| 62 | `sample_bilinear` | 21 | `79c10ddc45c358c67f353150276631ba56e4bdcab0d3760d84afe952c3859f9e` |
| 63 | `simplex_noise` | 46 | `79091353afa3432b82c5aece16c4e4e11cf08de40368e05e544c8509b315fc32` |
| 64 | `singularity_mask` | 9 | `8a9cd929ba8eae78b11714183c7afc78c5e2c6c31abf72ba51cd50ed6bf03de8` |
| 65 | `taylor_inv_sqrt` | 1 | `e4fa063d2b026b8ba09a7b0ef42a05ec3564913f1750b997848821faa9412536` |
| 66 | `warped_channel_value` | 14 | `e730903759accd745d885164f16cde91477a91a2c7589685b8017d573030dabb` |
| 67 | `wrap_float` | 4 | `f0915a8e46372c29b4cd2dbbf74f1771242d1ba0496f1f4ef4434cf61c4abe74` |
| 68 | `wrap_index` | 4 | `7c96a9fda62b2c97b48d061a9c90305f6b5799235ebc663045e774e836de29db` |

The counted-loop proof must remain exactly `loop_count=0`,
`unproved_loop_count=0`, `max_effective_depth=0`,
`max_lexical_product=0`, `entrypoint_charge=0`, and
`call_graph_acyclic=true`.

## Exact interface, resources, and metadata

```text
TAU:const float@1 (source global; never a runtime binding)
inputTex:sampler2D@2 / sampler slot S1
resolution:vec2@3
tileOffset:vec2@4
fullResolution:vec2@5
time:float@6
displacement:float@7
speed:float@8
seed:int@9
direction:float@10
fragColor:vec4@11 (output)
```

Resource requirements are exact:

```text
uniforms=(inputTex,resolution,tileOffset,fullResolution,time,
          displacement,speed,seed,direction)
samplers=(inputTex)
outputs=(fragColor)
uses_texture=true
uses_derivatives=false
```

Pass routing is `inputTex <- inputTex` and `fragColor -> outputTex`.
`direction`, `displacement`, `seed`, and `speed` use identity aliases.
Metadata defaults are direction 0, displacement 0.0625 (`0x3d800000`),
seed 1, and speed 1 (`0x3f800000`). Metadata ranges remain direction
[-180,180], displacement [0,0.25], seed [1,100], and speed [0,2]. Runtime
owns resolution, tile/full resolution, and time. The over-cap oracle's direct
displacement 1.75 is intentionally outside metadata and must not broaden it.

Bindings must reject each missing or wrong-typed required value. `inputTex`
must be a texture; `seed` must be `int`; coordinate uniforms must be Vec2; all
other runtime uniforms are numbers. An unrelated extra binding remains ignored
as existing binder behavior. There is no binding for `TAU` and no second
sampler.

## Why no transform or capability is allowed

The current validator and typed emitter accept the unmodified analyzed program.
An independent in-memory check reproduced the source/function/whole/interface
locks, passed current capability validation, and emitted native C++ without a
new rule. Degauss uses only the accepted const-float source-global profile,
scalar/vector functions, constructors, F32 materialization, uint and integer
vector conversions, scalar integer `%`, level-zero `texelFetch`, existing
builtins, scalar conditions/returns, and assignments.

There is no loop, array, derivative, varying, block, matrix, struct, sampler
function parameter, non-`in` helper parameter, vector predicate, or dynamic
dispatch. The only `%` is typed `int % int` in `wrap_index`; current emission
must remain exactly one `glsl::integer_mod` site. On live bilinear paths its
next-neighbor inputs are nonnegative and dimensions are positive. JavaScript
`%` and the current truncating signed remainder agree; no Sacred-style
untruncated division exists. All predicates are scalar, so no Refract-style
typed-array truthiness issue exists.

Therefore Task 21 must make all of these assertions:

- `APPROVED_CAPABILITIES`, the typed-slice capability list, approved types,
  operators, builtins, limits, and proof modules are byte-identical to accepted
  Task 20;
- `compatibility_transforms` has no Degauss entry and no other change;
- `numeric_literal_contracts` has no Degauss entry and no other change;
- the generated manifest derives `compatibility_transform: "none"` and
  `numeric_literal_contract: "glsl-f32"`;
- all Task 17-20 proof fields remain `None` for Degauss;
- no emitter, typed-IR, semantic, runtime, sampler, CMake, or public binding API
  change is needed.

If native parity fails, stop and reclassify the mismatch. Do not add a
compatibility transform or capability under this brief.

## Fixed work and resource bound

The exact-copy and mask-zero paths execute one level-zero input fetch. The
normal path executes one original fetch plus three calls to
`warped_channel_value`; each performs one four-fetch bilinear sample. The
maximum is therefore exactly 13 dynamic level-zero fetches per pixel. There are
five static `texelFetch(...,0)` AST sites: one in `main`, four in
`sample_bilinear`.

With nonzero time and speed, each channel evaluates base and time simplex
noise. Work remains fixed: zero source loops, no recursion, no allocation,
no callback, and no indirect/virtual call in the pixel namespace. The existing
binder may allocate State once before rendering; that bind-time allocation is
outside the hot path.

Acceptance must preserve Debug and Release `.su` files and report static versus
dynamic stack bytes for the pixel lambda and the complete maximum chain:

```text
pixel [contains the emitted source-main body] -> warped_channel_value
  -> compute_noise_value -> simplex_noise -> permute/mod289/taylor helpers
  -> sample_bilinear -> wrap_float/wrap_index/fetch_texel
```

The typed tree retains `main@56`, but the emitter does not generate a separate
C++ `main`: it writes those 27 source statements directly into `pixel`. Native
stack accounting therefore requires a `pixel` frame and reachable helper
frames, never a `main` frame.

Report the maximum non-inlined chain sum or Release inlining/disassembly
evidence. Any dynamic/unbounded stack classification, recursive edge,
allocation, indirect call, or more than 13 fetches is a failure. Do not confuse
external input/output surface storage or bind-time State with per-pixel stack.

## Exact catalog projection

Add Degauss between `filter/craquelure:craquelure` and
`filter/deriv:deriv`. The typed list must contain 115 unique sorted entries;
the public catalog must be exactly these 117 unique sorted keys:

```text
classicNoisedeck/coalesce:coalesce
classicNoisedeck/composite:composite
classicNoisedeck/refract:refract
classicNoisedeck/splat:splat
filter/bc:bc
filter/bloom:brightPass
filter/bloom:composite
filter/celShading:celShadingBlend
filter/celShading:celShadingEdges
filter/channel:channel
filter/chroma:chroma
filter/chromaticAberration:chromaticAberration
filter/chrome:chBlurH
filter/chrome:chBlurV
filter/chrome:chMap
filter/clouds:clouds
filter/colorReplace:colorReplace
filter/corrupt:corrupt
filter/craquelure:craquelure
filter/degauss:degauss
filter/deriv:deriv
filter/fibers:fibersBlend
filter/flipMirror:flipMirror
filter/glowingEdge:glowingEdge
filter/hatch:hatch
filter/highPass:hpBlurH
filter/highPass:hpBlurV
filter/highPass:hpCombine
filter/hs:hs
filter/invert:inv
filter/lensFlare:lensFlare
filter/lowPoly:lowPoly
filter/morphology:morphA
filter/morphology:morphB
filter/mosaicTiles:mosaicTiles
filter/normalize:apply
filter/normalize:reduce
filter/normalize:reduceMinmax
filter/oilPaint:oilPost
filter/outline:outlineBlend
filter/outline:outlineSobel
filter/outline:outlineValueMap
filter/patchwork:patchwork
filter/photocopy:pcBlurH
filter/photocopy:pcBlurV
filter/photocopy:pcCombine
filter/pixelSort:computeRank
filter/pixelSort:finalize
filter/pixelSort:findBrightest
filter/pixelSort:luminance
filter/pixelSort:prepare
filter/pixels:pixels
filter/plasticWrap:pwBlurH
filter/plasticWrap:pwBlurV
filter/plasticWrap:pwSpec
filter/reindex:nmReindexApply
filter/relief:rlBlurH
filter/relief:rlBlurV
filter/relief:rlShade
filter/repeat:repeat
filter/reverb:reverb
filter/ridge:ridge
filter/scale:scale
filter/scatter:scatterJitter
filter/scatter:scatterSmooth
filter/scratches:scratchesBlend
filter/scroll:scroll
filter/seamless:seamless
filter/sharpen:sharpen
filter/simpleAberration:chromaticAberration
filter/sine:sine
filter/skew:skew
filter/smoothstep:smoothstep
filter/sobel:sobel
filter/spatter:spatter
filter/stamp:stBlurH
filter/stamp:stBlurV
filter/strayHair:strayHairBlend
filter/strokes:stkPost
filter/tetraCosine:tetraCosine
filter/text:text
filter/threshold:thresh
filter/tile:tile
filter/tint:colorize
filter/translate:translate
filter/unsharpMask:usmBlurH
filter/unsharpMask:usmBlurV
filter/unsharpMask:usmCombine
filter/vignette:vignette
filter/watercolor:wcComposite
filter/watercolor:wcSeed
filter/wormhole:blend
filter/wormhole:clear
mixer/alphaMask:alphaMask
mixer/applyMode:applyMode
mixer/blendMode:blendMode
mixer/cellSplit:cellSplit
mixer/centerMask:centerMask
mixer/channelCombine:channelCombine
mixer/mashup:mashup
mixer/patternMix:patternMix
mixer/shadow:shadow
mixer/shapeMask:shapeMask
mixer/split:split
mixer/thresholdMix:thresholdMix
mixer/uvRemap:uvRemap
synth/cell:cell
synth/gradient:gradient
synth/mandala:mandala
synth/media:mediaInput
synth/modPattern:modPattern
synth/osc2d:osc2d
synth/pattern:pattern
synth/polygon:shape
synth/sacredGeometry:sacredGeometry
synth/solid:solid
synth/subdivide:subdivide
```

`filter/crt:crt` must remain absent. So must every other remaining key. Assert
typed 115, public 117, publicly unported 95, corpus 212, sortedness,
uniqueness, Degauss occurrence exactly one, and exact equality to this list.

## Frozen direct-canonical oracle

The oracle input at each case size is top-down `Float32Array` storage:

```text
R=((17*x+31*y+13)%101)/100
G=((7*x+19*y+23)%97)/96
B=((29*x+11*y+5)%89)/88
A=(((5*x+7*y+3)%23)-5)/12
```

Every lane crosses F32 storage. Alpha ranges from approximately -0.41666666 to
1.41666663. Runtime fragment coordinates remain bottom-left while Surface
storage is top-down. The runtime context is frame 17, delta time word
`0x3c888889`, and runtime-seed word `0x41e80000`.

All native configurations must match every F32 byte, RGBA8 byte, stored probe
word, metric, orientation rule, and fresh-surface repeat in the frozen JSON:

| Case | Size | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- |
| displacement-zero-exact-copy-tiled | 13x9 | `daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687` | `5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3` |
| default-landscape-untiled-center-mask | 13x9 | `c6bf433ea90b0c82d842724d8f633fefb8cded8e34ad83b9d3480d98a7051c71` | `9e02468af87d81a5d0a558ac965dd9e4f78b07a768b855e157d5769bcbd3ee98` |
| nondefault-landscape-tiled-negative-direction | 13x9 | `08dbc2988787474877268f9661bbeccbdc88dbd9f43bbfc3240e58120cf363f1` | `16267b09be48cdb9b967ad1e4c203cd2170b940639975ee1cbba75309765db2c` |
| nondefault-portrait-tiled-positive-direction | 9x13 | `86b32d32e970fffccc7049bf9c091f5e8b5e9139af7afd6f7bee6d315636a37f` | `d2aca58372b68e20691c89a7ab278aebf97ffe85ffa35eb3d4bb6414016803d7` |
| speed-zero-nonzero-time | 13x9 | `2bd1aa43c71d4eaab6298492b9edafd35978cd439eeae2a270968f6210128f37` | `7788b9151bca2f493a0af156b38cc636e14b5f27d4bbed16ed60c4942513dc22` |
| time-zero-positive-speed | 13x9 | `c2f6253b9491350f176470a5be560068fb634e31432d524360d58ee03ed0586f` | `710ce156f4b71dae2d487ac6a78fee5e58ee044fe400eb24740764c1784039b6` |
| full-resolution-zero-fallback-landscape | 13x9 | `15401d32e6befb161651150f044f35496bf741be49872b3869716689131453ff` | `96cbb763c8daf83c9ef99c2972993148a5c2e5231436ebe9c4d4cb581c473a32` |
| square-frequency-equality | 11x11 | `8c09129cc2a75ca01f8a3d774307128cb1c44721c884821f6b22b7cff67e2948` | `8e456f5906aca7993075834d2f3ad09f358f9acaffbfcc4dbc0f113ed4fd94c6` |
| untiled-over-cap-binding-domain-diagnostic | 13x9 | `c7983e127a9bc4ed938cff5c316d71ed50f2dfb2126b54718901efd80aae705f` | `40d20fde4f5aab0e0e42a0371d373dbfdb66f62644650bef511ff8ffa3592bda` |

Bind these exact per-case context words; all Vec2 values also cross F32 storage:

| Case | tileOffset / fullResolution | time | displacement | speed | seed | direction |
| --- | --- | --- | --- | --- | ---: | --- |
| displacement-zero-exact-copy-tiled | `[7,11]` / `[41,29]` | `0x3ec00000` | `0x00000000` | `0x3f800000` | 1 | `0x00000000` |
| default-landscape-untiled-center-mask | `[0,0]` / `[13,9]` | `0x3ec00000` | `0x3d800000` | `0x3f800000` | 1 | `0x00000000` |
| nondefault-landscape-tiled-negative-direction | `[7,11]` / `[41,29]` | `0x3ee00000` | `0x3e400000` | `0x3fe00000` | 37 | `0xc3094000` |
| nondefault-portrait-tiled-positive-direction | `[5,3]` / `[23,37]` | `0x3f1ccccd` | `0x3e800000` | `0x40000000` | 100 | `0x43340000` |
| speed-zero-nonzero-time | `[4,6]` / `[31,25]` | `0x3f600000` | `0x3dc00000` | `0x00000000` | 19 | `0x42050000` |
| time-zero-positive-speed | `[3,2]` / `[29,21]` | `0x00000000` | `0x3e100000` | `0x3fc00000` | 53 | `0xc2760000` |
| full-resolution-zero-fallback-landscape | `[2,1]` / `[0,0]` | `0x3ea00000` | `0x3e000000` | `0x3fa00000` | 11 | `0x42910000` |
| square-frequency-equality | `[3,2]` / `[31,31]` | `0x3f0ccccd` | `0x3e600000` | `0x3f400000` | 71 | `0xc3340000` |
| untiled-over-cap-binding-domain-diagnostic | `[0,0]` / `[13,9]` | `0x3ef00000` | `0x3fe00000` | `0x3fa00000` | 29 | `0x42b40000` |

The nine cases comprise 4,228 output lanes, all finite. The displacement-zero
case must be bit-identical to its 1,872 input bytes, including all 50
out-of-range alpha pixels. Normal paths clamp original alpha; center-mask zero
returns original. The native test must verify input bytes remain unchanged.
RGBA8-only comparison is forbidden.

### Canonical mutation sensitivity

The external generator applies each replacement to exact canonical factory
text with asserted replacement count. Native parity must cover the same
branches; structural profile tests must reject corresponding source/tree drift.

| Mutation | F32-changing cases | RGBA8-changing cases | Required contract |
| --- | ---: | ---: | --- |
| channel-order-red-zero-to-blue-two | 8/9 | 8/9 | channel selectors/call order; copy identity |
| direction-rotation-disabled | 7/9 | 7/9 | direction radians and rotation; direction-zero identity |
| wrap-index-next-neighbor-clamped | 8/9 | 8/9 | integer next-neighbor `%` wrap |
| wrap-float-coordinate-clamped | 8/9 | 8/9 | periodic floating coordinate wrap |
| bilinear-fx-forced-zero | 8/9 | 8/9 | horizontal interpolation and four fetches |
| bilinear-fy-forced-zero | 8/9 | 8/9 | vertical interpolation and four fetches |
| time-noise-branch-disabled | 6/9 | 6/9 | second simplex evaluation and three short-circuit identities |
| singularity-mask-forced-one | 8/9 | 8/9 | mask and exact center behavior |
| alpha-clamp-disabled | 8/9 | **0/9** | F32-only normal alpha contract |
| displacement-cap-disabled | 1/9 | 1/9 | over-cap diagnostic and eight in-range identities |
| simplex-amplitude-42-to-41 | 8/9 | 8/9 | simplex reduction/helper chain |
| frequency-axes-unswapped | 7/9 | 7/9 | landscape/portrait cross-axis mapping; square identity |
| seed-offset-disabled | 8/9 | 8/9 | integer seed binding/base-seed construction |

The frozen JSON's exact required-divergence and required-identity case lists,
replacement strings/counts, mutated hashes, byte/lane differences, probes, and
nonfinite transitions are normative. The alpha mutation changes 49-53 F32
alpha lanes in every normal case while changing zero RGBA8 bytes.

Every mutation has exactly one textual replacement. Its mandatory branch
controls are:

```text
channel-order-red-zero-to-blue-two
  diverge: nondefault-landscape-tiled-negative-direction, nondefault-portrait-tiled-positive-direction
  identity: displacement-zero-exact-copy-tiled
direction-rotation-disabled
  diverge: nondefault-landscape-tiled-negative-direction, nondefault-portrait-tiled-positive-direction
  identity: displacement-zero-exact-copy-tiled, default-landscape-untiled-center-mask
wrap-index-next-neighbor-clamped
  diverge: untiled-over-cap-binding-domain-diagnostic
  identity: displacement-zero-exact-copy-tiled
wrap-float-coordinate-clamped
  diverge: untiled-over-cap-binding-domain-diagnostic
  identity: displacement-zero-exact-copy-tiled
bilinear-fx-forced-zero
  diverge: nondefault-landscape-tiled-negative-direction, untiled-over-cap-binding-domain-diagnostic
  identity: displacement-zero-exact-copy-tiled
bilinear-fy-forced-zero
  diverge: nondefault-portrait-tiled-positive-direction, untiled-over-cap-binding-domain-diagnostic
  identity: displacement-zero-exact-copy-tiled
time-noise-branch-disabled
  diverge: default-landscape-untiled-center-mask, nondefault-landscape-tiled-negative-direction,
           nondefault-portrait-tiled-positive-direction, full-resolution-zero-fallback-landscape,
           square-frequency-equality, untiled-over-cap-binding-domain-diagnostic
  identity: displacement-zero-exact-copy-tiled, speed-zero-nonzero-time, time-zero-positive-speed
singularity-mask-forced-one
  diverge: default-landscape-untiled-center-mask, nondefault-landscape-tiled-negative-direction
  identity: displacement-zero-exact-copy-tiled
alpha-clamp-disabled
  diverge: all eight nonzero-displacement cases
  identity: displacement-zero-exact-copy-tiled
displacement-cap-disabled
  diverge: untiled-over-cap-binding-domain-diagnostic
  identity: the other eight cases
simplex-amplitude-42-to-41
  diverge: nondefault-landscape-tiled-negative-direction, speed-zero-nonzero-time,
           time-zero-positive-speed
  identity: displacement-zero-exact-copy-tiled
frequency-axes-unswapped
  diverge: nondefault-landscape-tiled-negative-direction, nondefault-portrait-tiled-positive-direction
  identity: displacement-zero-exact-copy-tiled, square-frequency-equality
seed-offset-disabled
  diverge: default-landscape-untiled-center-mask, nondefault-landscape-tiled-negative-direction,
           nondefault-portrait-tiled-positive-direction
  identity: displacement-zero-exact-copy-tiled
```

## Fail-closed profile and negative matrix

Because no capability/proof is added, use a small source-key profile validator
inside `generate_typed_slice.py`, not a new ambient feature or IR record. It
must check Degauss only and authenticate the hard-coded raw, normalized,
function, whole, and interface hashes plus exact source path, key, empty
defines, no transform, `glsl-f32`, resources, declarations, function/body
counts, loop proof, and all foreign-proof fields `None`.

The publication boundary is the generator/profile plus exact slice entry.
The generic validator/emitter may continue to accept other current-vocabulary
synthetic programs in tests; a semantically supported Degauss mutation must
still be unpublishable because the source profile fails. Do not distort the
generic emitter merely to reject a source that the language legitimately
supports.

Tests must locate and replace exactly one typed node/statement; zero or
duplicate mutation targets fail the test helper. Exercise:

### Identity, schema, and metadata

- wrong corpus revision, key/runtime key, effect/pass, source path, raw byte or
  size, raw/normalized digest, normalized text, factory name/text hash, or
  canonical runtime hash;
- nonempty/changed defines; numeric contract missing, `source-double`, or any
  value other than `glsl-f32`; Degauss compatibility-transform entry, manifest
  value other than `none`, or any additional transform;
- missing/duplicate/reordered Degauss entry; inserted anywhere except between
  Craquelure and Deriv; changed accepted Task 20 capability/type/operator/
  builtin/limit/proof/transform maps;
- changed function count, function ID/name/signature/body count, function tuple
  hash, whole hash, interface hash, loop summary, call edge, or recursion;
- any non-`None` Task 17, 18, 19, or 20 proof, individually and combined;
  attacker-updated caller hash fields still reject against hard-coded profile.

### Interface and binding

- missing, duplicated, reordered, renamed, renumbered, retyped, or storage-
  changed `TAU@1`, inputs 2-10, or `fragColor@11`;
- `TAU` made a binding, writable/global mutable/static/thread-local, different
  literal/type, or added second source global;
- missing/wrong sampler slot, sampler type, sampler count, resource tuple,
  texture-use flag, output, pass route, alias, or metadata default/range;
- each missing binding and each wrong type: texture as scalar, scalar as
  texture/vector, Vec2 as number, float as int, or seed as float;
- added sampler, sampler parameter, varying, derivative, uniform block, struct,
  matrix, array, `out`/`inout`, nonzero texelFetch LOD, texture function, or
  resource/stage ABI.

### Source/tree semantics

- any of five static `texelFetch` sites missing/duplicated/reordered, LOD not
  exact literal int zero, coordinate/source changed, main original fetch moved
  after an early return, or dynamic maximum not 1/13 as appropriate;
- `%` removed/duplicated/retyped, changed to float `mod`, altered `limit<=0`,
  `wrapped<0`, `x0/y0` clamps, next-neighbor `+1`, or positive-dimension flow;
- `wrap_float` floor/wrap order or correction changed;
- any of four bilinear footprint coordinates, `fx`, `fy`, mix order, or F32
  materialization changed;
- channel literals/order, one/two/three calls, returned sampled lanes, direction
  TAU/360 conversion, rotation signs, displacement scaling, or resolution axes
  changed;
- `speed!=0 && time!=0`, base/time simplex calls, periodic path, seed/channel
  offsets, frequency cross-axis mapping/square branch, simplex amplitude/helper
  path, mask exponent/center/shape, tiled/fallback resolution choice, 1.01
  threshold, 256-pixel cap, or clamp/min path changed;
- displacement-zero or mask-zero early return changed; copy alpha narrowed/
  clamped; normal alpha not `clamp01(original.w)`; output channel order changed;
- added loop, array, derivative, matrix, stage construct, allocation, callback,
  exception, indirect/virtual call, recursion, dynamic stack, or unsupported
  builtin/operator/type.

### Catalog and closed-world exclusions

- typed/public counts other than 115/117, unported other than 95, corpus other
  than 212, unsorted/duplicate catalog, missing or duplicate Degauss;
- `filter/crt:crt` or any of the other 95 remaining keys becomes typed/public;
- Degauss profile/capability reused by another key, source variant, define
  variant, pass, or factory;
- Task 19 Refract proof/transform or Task 20 Sacred proof/Star transform changes;
- any of the 19 pre-Degauss generated program blocks changes by even one raw
  byte; any of the 114 prior program blocks differs after normalizing only
  `typed_[0-9]+` namespace ordinals to one sentinel; or any non-Degauss
  manifest entry, header declaration, binding, oracle, or test fixture changes
  unexpectedly. No whitespace, literal, comment, factory, or code difference
  is normalized.

## Owned implementation files

After accepted Task 20 and independent Task 21 review, implementation may
modify only:

- `tools/glslcpp/typed_slice.json`: add the one sorted `{}` Degauss entry;
  change no capability/transform/numeric-contract/type/operator list.
- `tools/glslcpp/generate_typed_slice.py`: add the exact Degauss profile locks
  and validation helper; change accepted typed count/success text 114 -> 115.
- `tests/test_typed_generator.py`: profile/hash, positive emission, negative
  matrix, exact slice/count/catalog, deterministic drift tests.
- `tests/test_typed_slice.cpp`: nine native oracle surfaces, inputs, probes,
  repeats, orientation, finite/alpha/copy behavior.
- `tests/test_generated_kernels.cpp`: public declaration, exact binding
  signature/failures, exact 117-key catalog.

Regenerate only through the accepted generator:

- `src/typed_generated/typed_slice.cpp`
- `src/typed_generated/typed_manifest.json`
- `include/noisemaker/generated/catalog.hpp`

No new file is needed. Do not modify `typed_ir.py`, `semantic.py`,
`emit_typed_cpp.py`, any proof/compatibility module, corpus source, runtime,
sampler, numeric helper, Surface, CMake, or unrelated test/generated body. If
an owned-file conflict with Task 20 is inseparable, stop for review.

## Test-first implementation order and review gates

1. **Preflight:** authenticate the four Task 21 artifacts and accepted Task 20
   baseline; record accepted owned-file hashes; rerun corpus/generator/full
   gates. Stop on any mismatch.
2. **RED profile tests:** add exact source/function/whole/interface/metadata and
   exclusion tests. Observe Degauss missing and profile mutations not rejected.
3. **GREEN profile:** implement the one internal Degauss profile helper and
   exact 114 -> 115 count. Do not alter generic language or emitter behavior.
   Review gate: independently compare hashes, profile tuple, maps, and owned
   diff before adding generated/native output.
4. **Slice/generation:** add Degauss after Craquelure, run `--check` to observe
   only expected three-output drift, then `--write`. Split generated C++ at
   `// Typed IR program:` markers. Prove raw byte identity for the 19 program
   blocks before Degauss and, across all 114 prior blocks, normalize only each
   `typed_[0-9]+` namespace ordinal to one sentinel and prove byte identity.
   Any other byte drift fails.
5. **Bindings/catalog:** add declaration, every missing/wrong-type case, extra-
   binding control, exact list/count/sortedness/uniqueness and CRT exclusion.
6. **Native oracle:** construct exact F32 input/formula and all nine binding
   records from frozen words; run every full F32/RGBA8/probe/metric/repeat/input-
   immutability check. Review gate: independently compare all native outputs to
   the direct canonical JSON before sanitizers.
7. **Full acceptance:** fresh Debug, Release, ASan/UBSan, stack, disassembly,
   scoped generated-code inspection, full Python/CTest/prior-oracle gates, and
   final owned/unrelated hash census.

## Verification commands

Run from `.`; use fresh `/tmp` build
trees and no Git command.

```sh
shasum -a 256 \
  docs/port-engineering/task-21-frontier-audit.md \
  docs/port-engineering/task-21-oracle-generator.mjs \
  docs/port-engineering/task-21-oracles.json \
  docs/port-engineering/task-21-oracle-report.md
node docs/port-engineering/task-21-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_task21_degauss_profile_is_exact_and_current_vocabulary \
  tests.test_typed_generator.TypedGeneratorTests.test_task21_degauss_profile_rejects_identity_interface_and_tree_drift \
  tests.test_typed_generator.TypedGeneratorTests.test_task21_adds_no_capability_transform_or_numeric_exception \
  tests.test_typed_generator.TypedGeneratorTests.test_task21_degauss_exclusions_remain_closed
python3 -m unittest discover -s tests -p 'test_*.py'
```

Rerun every accepted Task 15-20 oracle/check command and all existing semantic,
drift, transactional-generation, and deterministic-CWD tests. Use the exact
documented commands from accepted reports rather than guessing filenames.

```sh
cmake -S . -B /tmp/noisemaker-task21-debug -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fstack-usage -fstack-size-section -ffp-contract=off'
cmake --build /tmp/noisemaker-task21-debug
ctest --test-dir /tmp/noisemaker-task21-debug --output-on-failure

cmake -S . -B /tmp/noisemaker-task21-release -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS='-fstack-usage -fstack-size-section -ffp-contract=off'
cmake --build /tmp/noisemaker-task21-release
ctest --test-dir /tmp/noisemaker-task21-release --output-on-failure

cmake -S . -B /tmp/noisemaker-task21-sanitize -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fsanitize=address,undefined -fno-omit-frame-pointer -fstack-usage -fstack-size-section -ffp-contract=off' \
  -DCMAKE_EXE_LINKER_FLAGS='-fsanitize=address,undefined'
cmake --build /tmp/noisemaker-task21-sanitize
ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
  ctest --test-dir /tmp/noisemaker-task21-sanitize --output-on-failure
```

Extract only the generated Degauss namespace before code-shape checks; the
binder and other factories are outside the pixel profile:

```sh
awk '
  $0 == "// Typed IR program: filter/degauss:degauss" { degauss = 1 }
  degauss && /^namespace typed_[0-9]+ \{/ { body = 1 }
  body { print }
  body && /^}  \/\/ namespace typed_[0-9]+$/ { exit }
' src/typed_generated/typed_slice.cpp > /tmp/task21-degauss-namespace.cpp
test -s /tmp/task21-degauss-namespace.cpp
test "$(rg -c '^namespace typed_[0-9]+ \{$' /tmp/task21-degauss-namespace.cpp)" = 1
rg -n -C 5 'wrap_index|integer_mod|sample_bilinear|fetch_texel|warped_channel_value|void pixel' /tmp/task21-degauss-namespace.cpp
if rg -n 'operator new|operator delete|malloc|free|std::function|std::map|std::unordered_map|std::variant|std::string|throw|alloca|\.at\(' /tmp/task21-degauss-namespace.cpp; then
  echo 'forbidden construct in Degauss namespace' >&2
  exit 1
fi
find /tmp/noisemaker-task21-debug /tmp/noisemaker-task21-release /tmp/noisemaker-task21-sanitize -name '*.su' -print
rg -n 'degauss|pixel|warped_channel_value|compute_noise_value|simplex_noise|sample_bilinear|wrap_' /tmp/noisemaker-task21-{debug,release,sanitize} -g '*.su'
```

Typed-tree tests must continue to authenticate exact source `main@56`.
Generated-code tests must brace-extract exact `pixel`, `warped_channel_value`,
`compute_noise_value`, `simplex_noise`, `sample_bilinear`, `wrap_float`,
and `wrap_index` bodies. Assert one generated `fetch_texel` call in `pixel` and
four in `sample_bilinear`, exactly one `integer_mod` in `wrap_index`, no
generated C++ `main`, exact helper call routing, and forbidden patterns only
within those bodies. Do not scan the entire generated translation unit and
misclassify bind-time catalog/State behavior. For generated isolation, split
accepted Task 20 and Task 21 C++ at `// Typed IR program:` markers. Require raw
byte identity for all 19 blocks before Degauss. Across all 114 prior blocks,
replace only `typed_[0-9]+` namespace ordinals with one fixed sentinel and
require byte identity; any other byte drift fails. This sole normalization is
required because sorted insertion renumbers Degauss and all later namespaces.

Use `llvm-objdump -d` or `otool -tvV` to verify Release call/inlining and no
allocator/indirect-call route in the Degauss pixel path. Preserve and report
`.su` static frame values and maximum chain reasoning.

## Completion evidence and hard stop

Task 21 can be declared complete only with:

- accepted Task 20 baseline evidence and before/after hashes for every owned
  file;
- all frozen Degauss source/factory/function/whole/interface/numeric/metadata
  locks reproduced;
- no capability, transform, numeric override, proof, runtime, emitter, or
  language-list change;
- exact 115 typed / 117 public / 95 unported / 212 corpus counts and exact
  public catalog above, with CRT excluded;
- all nine native full-F32 and RGBA8 hashes, every probe/metric, input
  immutability, orientation, finite/copy/alpha behavior, and repeat identity in
  Debug, Release, ASan, and UBSan;
- all thirteen canonical mutation sensitivities and the full structural/
  exclusion matrix;
- exact static/dynamic fetch accounting, scoped no-allocation/dispatch checks,
  `.su` stack table, call-chain bound, and Release disassembly;
- zero failed full Python/native/prior-oracle tests; exact generator `--check`;
- only the five owned source/test files and three generator outputs changed;
  all 19 pre-Degauss generated blocks are raw-byte-identical, and all 114 prior
  blocks are byte-identical after normalizing only `typed_[0-9]+` namespace
  ordinals to one sentinel. Any other byte drift is a failure.

This document stops before implementation. If any source/profile/oracle/native
identity fails, or Task 20 is not accepted exactly, stop and request a revised
scope. Do not fix forward by adding CRT, a new capability, or a compatibility
transform.
