# Task 22 CRT scope and proof brief

> **Status:** read-only pre-design, pre-implementation contract. Stop before
> design and implementation. This brief authorizes no repository edit and no
> Git operation. Implementation may begin only after independent scope/proof
> review and an accepted Task 21 baseline.

**Goal:** Add exactly `filter/crt:crt` while matching the public CPU CRT
adapter's float32 reduced-turn sine semantics at six exact scalar sites.

**Architecture:** Apply one key/source/function/span-locked typed-tree
compatibility transform, `crt-metal-sine-v1`, before validation and emission.
The transform expands each of the six source `sin` calls into an inline tree
made only from the already-supported `float` constructor, `floor`, arithmetic,
and `sin`; it adds no runtime helper, language capability, proof object, type,
operator, builtin, or resource ABI. Validator and emitter independently
authenticate the exact post-transform tree.

**Tech stack:** Python 3 typed frontend and immutable typed IR, C++20 typed
emitter, existing GLSL runtime and sampler, the pinned public Noisemaker CPU
adapter oracle, CMake/CTest, ASan/UBSan, and compiler `.su` stack output.

## Global constraints

- Scope is exactly `filter/crt:crt`; no adjacent or otherwise unported key is
  admitted.
- Add exactly one compatibility name: `crt-metal-sine-v1`.
- Add no GLSL capability, proof kind/record/field, type, operator, builtin,
  numeric-literal mode, loop rule, resource/stage ABI, or runtime helper.
- Preserve `glsl-f32` literals, existing Number-compatible scalar temporaries,
  exact F32 vector/storage/builtin boundaries, and `-ffp-contract=off`.
- Do not change global `glsl::sin`, `cos`, sampler behavior, Surface, CMake,
  corpus source, or another factory's output.
- Full F32 and RGBA8 oracle comparison are both mandatory; RGBA8-only
  acceptance is forbidden.
- Do not use Git, create a branch/worktree, commit, push, or open a pull
  request.

---

## Hard baseline gate and count projection

Task 22 must not be implemented on the currently inspected Task 20 state or
on an in-flight Task 21 tree. First require Task 21 final acceptance with:

- exact 115 typed / 117 public / 95 publicly unported / 212 corpus counts;
- exact Degauss source, function, whole-program, interface, factory, numeric,
  binding, nine-oracle, and 13-mutation identities;
- clean Debug, Release, ASan/UBSan, stack, generated-isolation, full Python,
  CTest, prior-oracle, and generator gates;
- exact final Task 21 owned/generated file hashes recorded in its acceptance
  report;
- Task 21 brief SHA-256
  `bf6a223b076b0c3cac93b2a05d3c428b4ba39ab2fe88fe6bc712c3a0a76e6418`.

At Task 22 preflight, record accepted Task 21 hashes for every Task 22-owned
file and generated output. `tools/glslcpp/emit_typed_cpp.py` must still have
SHA-256 `f8c9c21a8bc0590e2af78b892dc7504a55aafd8987a41e367a73f66a8de4ea11`,
because Task 21 authorizes no emitter change. If any accepted Task 21
interface, hash, catalog, output, command, or count differs from this
projection, stop and revise/review Task 22; do not stack onto moving state.

Conditional on that gate:

| State | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Accepted Task 21 | 115 | 117 | 95 |
| Task 22 CRT result | **116** | **118** | **94** |

The sorted insertion is exactly:

```text
filter/craquelure:craquelure
filter/crt:crt
filter/degauss:degauss
filter/deriv:deriv
```

For an exact newline-terminated sorted key list, the projected 116-key typed
catalog SHA-256 is
`76c81945ef992ed258900815335a23ae4f36d8756b7763ebd5e03d8562fde8e3`;
after adding only the separately maintained `filter/invert:inv` and
`synth/solid:solid`, the projected 118-key public list SHA-256 is
`019a80df52192e3c898af58a5e3a2a9da654896eadde78097ce4a818579328f9`.
Tests must also compare the explicit list, not rely on the digest alone.

## Frozen review and oracle artifacts

| Artifact | SHA-256 |
| --- | --- |
| `task-22-frontier-audit.md` | `c3d006f354f6ca9bb65c42b8e6f8bbdac194ddf1a6486ccbf890bfe818f16160` |
| `task-22-oracle-generator.mjs` | `dc2044ee2bf007f1888f958a09185445caef34c064a6e4b3eea340a09ad49a27` |
| `task-22-oracles.json` | `c927f467418f9ef154a817869228a0918c2fc222ef3bb64f2b0a6bab8a74e889` |
| `task-22-oracle-report.md` | `36ac4f8b85a0fefc47c403eef47bd11ceb40e9774fa709125f01bc4e2ea075aa` |

The generator's `--check` must reproduce the JSON before implementation and
at every review gate. `../noisemaker-for-cpu` is oracle
provenance only and must not become a native build, test-runtime, installed
library, or generator dependency.

## Exact identity, provenance, and numeric contract

| Field | Required value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Key/runtime key | `filter/crt:crt` |
| Effect/pass | `filter/crt`, pass 0 `main` |
| Source | `sources/filter/crt/crt.glsl` |
| Raw bytes / SHA-256 | 19,560 / `62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c` |
| Normalized bytes / SHA-256 | 18,054 / `acd1c3f05c6d02052592aeb46bbbc49d23e18f4e83530498687903e00b4623fe` |
| Runtime defines | exactly `{}` |
| Numeric literal contract | exactly `glsl-f32` |
| Compatibility transform | exactly `crt-metal-sine-v1` |
| Canonical factory | `canonicalFactory44` |
| Canonical factory-text SHA-256 | `6d65f4984f8749ca7cdfec976e082662d3a7ad614aabb15ce8a168fca7d8e303` |
| Public factory | `crtFactory` |
| Public factory-text SHA-256 | `240972f95f908452bf87fc681e360553759f374fa81613adc415a5a7c5eb4bf7` |
| Public adapter file SHA-256 | `c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc` |
| Canonical generated runtime SHA-256 | `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Pre-transform function tuple SHA-256 | `f6ab50374732b058fa2a5cd33e87bbe35654682b7125593d7451871194b2ba72` |
| Pre-transform whole-program SHA-256 | `f70fc78da6c3579fa3237fbbfa3712229b88f0a93b8d556181f9bad2ed74b6fc` |
| Post-transform function tuple SHA-256 | `1b67fa6d01135e98434bc9e6a4627f0d23565c81fa1e17cbdba10082e23e37a3` |
| Post-transform whole-program SHA-256 | `7aa853a51316b1122750af1155411a5ca8c1e11cf02688a33d9ef6fcace5f6a2` |
| Interface SHA-256, pre and post | `9336d2b596c0efd955af699a27c788938c99d0e1e5c6438f66054e15fc135490` |
| Typed shape, pre and post | 35 functions, zero loops, acyclic call graph |

Hash contracts are exact:

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

The whole tuple deliberately excludes optional Task 17-20 proof fields so its
identity remains stable across accepted IR extensions. Separately require
`fixed_nine_table_proof`, `fixed_grid_counter_store_proof`,
`fixed_array_in_parameter_proof`, and `fixed_affine_centers13_proof` all
`None`; CRT must not acquire or borrow a proof.

`glsl-f32` remains the only numeric-literal mode. Important exact F32 values
are PI `3.1415927410125732` (`0x40490fdb`), TAU
`6.2831854820251465` (`0x40c90fdb`), INV_THREE
`0.3333333432674408` (`0x3eaaaaab`), and compatibility INV_TAU
`0.15915493667125702` (`0x3e22f983`). Keep existing double scalar
temporaries, F32 vector/storage/builtin results, and `-ffp-contract=off`.

## Exact `crt-metal-sine-v1` transform

### Public behavior being preserved

The pinned public `crtFactory` replaces CRT's `sin` with:

```text
turns = f32(value * f32(1 / 6.283185307179586))
phase = turns - floor(turns)
result = f32(sin(phase * f32(6.283185307179586)))
```

Raw `canonicalFactory44` is not the public reference. The oracle proves raw
factory output differs in 316-351 F32 lanes in representative normal cases,
including large-time, speed-zero, time-zero, tiled, fallback, and default
paths. A plain source emission using global `glsl::sin` is therefore wrong.

### Exact tree rewrite

For each authenticated original `TypedExpression` `site` with kind `builtin`,
callee `sin`, signature `-40`, scalar-float type, rvalue category, and exactly
one child `arg`, replace only `site.children` with the following inline typed
tree:

```text
sin(
  (
    float(arg * 0.15915493667125702)
    - floor(float(arg * 0.15915493667125702))
  ) * 6.2831854820251465
)
```

The two literals have typed kind `literal`, type `float`, rvalue category,
literal strings exactly as shown, and matching Python `literal_value` values.
The constructor has kind `construct`, type/constructor type `float`. `floor`
has kind `builtin`, scalar-float type, rvalue category, signature `-17`, and
callee `floor`. The new products/subtraction have kind `binary`, scalar-float
type, rvalue category, and operators `*`, `-`, `*` in that order. Every
injected node uses the original outer `sin` span. The original argument object
is retained unchanged; the same immutable `turns` subtree appears as the
subtraction's left operand and as `floor`'s child. The outer `sin` retains its
original span, type, category, signature, callee, and all other fields.

This creates the adapter's F32 boundary through the existing float constructor
and the adapter's final F32 result through existing `glsl::sin`. It deliberately
duplicates argument evaluation. That is authorized only because five arguments
are direct identifiers and the sixth is the exact pure `z*157.0 + w*113.0`
tree: none contains a call, assignment, update, lvalue write, index, fetch, or
other side effect. A seventh site or a changed/impure argument rejects.

Do not add a helper function, new builtin, runtime mode, global sine switch,
`fract` substitution, modulo, approximate polynomial, `fmod`, source edit,
or special output branch. Do not transform `cos`.

### Six pre/post site locks

Coordinates and paths are in the normalized typed source. Expression hashes
are `SHA256(repr(expression))`; argument and post hashes use the same contract.

| Function ID/name | Statement/expression path | Span | Pre `sin` SHA-256 | Argument SHA-256 | Post expression SHA-256 |
| --- | --- | --- | --- | --- | --- |
| 98 `compute_lens_offsets` | `(11,e0,0,0,0,0,1)` | `257:37-257:47` | `eb792d3743d971b034cad3305939edd164f35d7391b0e956e0ded09f9ab2edca` | `dfad6ec8408b05020688cf666dd8314a0d5e962d18d258ef05e4c7cbf1d17ab4` | `fee8d1478892ff364e1f2222fbe484ec9c2821fde88981ac3411c7f460b0c991` |
| 105 `hash3` | `(2,e0,0,0,0)` | `278:18-278:32` | `ec1ed0047c1fb4fd715375e00874a32e8f9e41ab9f74a3bac5ea23b3f1983150` | `ba9137a74af006428cd1b19f03d169de8b0889ff1d4aa38dd775e9f85f389ad5` | `7b805551b3f93876e1bd5ecf76a76efea15276160a8aa7bad7a570ba5da70457` |
| 111 `normalized_sine` | `(0,e0,0,0,0)` | `61:12-61:22` | `06d6918e656846d23db8b766f298e3158cc09f466cead68bbdb792a95157ffeb` | `f77149906598a9a158df24b332c186f1cb526dacbfe87bad03262af0a6def1ab` | `37e92090742c393c51e58b0e243ed94b7c496d81713c72f50a81965ab65d0906` |
| 114 `random_scalar` | `(0,e0,0,0,0)` | `32:18-32:27` | `42946f9e07f8dbde14695fd889212e33322f6b0b21073f150c104dbdae0207dc` | `1625e24c6a465e2a1aff50c738539bf101926b078a4a14e617d12daa25efd07b` | `ebf5806ccb5844082b4824ae98be478a0ccbbedcc446d11e1f782a05a5259fb7` |
| 118 `simplex_random` | `(2,e0,0,0,0)` | `38:15-38:25` | `528dcb92903e79bdc9b9c3fa9da9d798ff560617e6bfc10d3c0eea8cd3a840fb` | `385a6b97e9699eb5c2a7b2a2dd223de9794d92452b1ab6061f3bf8e53f8662a0` | `d86ca37ad7e92a214a0aa669208b860c8c2691623ef830abe7275b6f83a99034` |
| 118 `simplex_random` | `(3,e0,0,0,0)` | `39:18-39:44` | `ee17c06d50c446e45ea053d72191298f632721fe4daa3a01aad593095bf78367` | `3c38672a718c912c5748397deb0abcf049c36dd979e9ca9a164f7437d5e2a6d9` | `13a34f969f04eca11820a7aadee45a56f11e5ae369dfac59e02cb88e78673746` |

Exactly five functions change. Their complete hashes are:

| ID/function | Pre SHA-256 | Post SHA-256 |
| --- | --- | --- |
| 98 `compute_lens_offsets` | `c589ae1542160f189e9db5a125719da57ed72ae35357f3aad88a3fd452c0b66d` | `47332fcd4c91de0b794ebed756eb93e469c6d418e612e6abea0673ad93c62258` |
| 105 `hash3` | `0d2944ce4196702c0d0e35dc030866446477ae9f71aea71cb628f3d176fe301c` | `498c7c564d712125c5d86a6371fc8033ab07499b579291c7fd04eb10066cadf2` |
| 111 `normalized_sine` | `931ad72e976380fba0139d37370fc61179a088831a4ec18f6080b978e85cd39c` | `c18a96221435819ea0d4de84dd9702765f1439d0e93309146631d83291f6f5a8` |
| 114 `random_scalar` | `ee5cf37c4b4ded3fc55b076b8ad168f21ac240df34ece9e93bfdb9a0b7dda3e8` | `9af506d4fd1b6092bc8e5eb5985333598e3e4cfd6a5133c33cb762d635f0a74d` |
| 118 `simplex_random` | `f501ca9995ca26e7ffc32dec1f3d20c102fce4083bd5b03e4d9fd4d0168a468f` | `eef49ca4ef3414fc4140bd7ecfcca4d487c02a9c5416b410659d0486c3553819` |

The other 30 functions must remain dataclass-equal. `simplex_random` is
currently unreachable, but both of its sites are transformed and locked so a
future reachability change cannot silently expose raw sine semantics.
`clamp_index` is also currently unreachable and remains present unchanged.

The transform must authenticate both frozen pre hashes before rewriting and
both frozen post hashes afterward. Missing, duplicate, partial, already-
transformed, twice-transformed, reordered, span-shifted, wrong-key/source,
wrong-function/path, wrong-signature, wrong-type/category, wrong argument,
wrong literal/tree, extra `sin`, or any non-site change fails closed. Caller-
provided hashes are drift alarms, never authority.

An in-memory current-emitter projection for the exact post tree, namespace
`typed_19`, and factory `bind_filter_crt_crt` is 56,865 bytes with SHA-256
`c2cad7e88fb817c311abb0041fec98d14c28ae3c3bd731b67944c745b8c295ec`.
After normalizing only `typed_[0-9]+` to `typed_SENTINEL`, its SHA-256 is
`36410c4f25e2a0d53bba3bdc7164c18f74cc7f06de8f7589186da182b7246922`.
These are projected code-shape locks conditional on the accepted Task 21
emitter hash above; baseline drift requires brief review rather than updating
them opportunistically.

## Complete typed shape, aliases, and no-capability finding

The 35 exact source-function names, in typed tuple order, are:

```text
adjust_hue adjust_saturation animated_simplex_value apply_vignette as_u32
blend_cosine blend_linear clamp01 clamp_index compute_lens_offsets
compute_singularity fade fade_vec3 freq_for_shape get_scanline_base_values
get_scanline_value_interpolated hash3 hsv_to_rgb lerp main mod289_vec3
mod289_vec4 normalized_sine periodic_value permute random_scalar rgb_to_hsv
sample_scanline_bilinear simplex_noise simplex_random singularity_mask
taylor_inv_sqrt value_noise_3d wrap_float wrap_unit
```

The current Task 20 validator accepts the raw program and accepts the proposed
post tree with the existing capability tuple. The current emitter renders the
post tree without a new emission primitive. CRT uses only existing const-float
globals, scalar/vector functions and constructors, uint/int conversions,
scalar integer remainder, level-zero `texelFetch`, scalar conditions/returns,
assignments, and already-approved builtins.

There is no loop, array, derivative, varying, block, matrix, struct, sampler
parameter, parameter direction other than `in`, vector predicate, texture LOD,
or dynamic dispatch. The counted-loop proof is exactly:

```text
loop_count=0
unproved_loop_count=0
max_effective_depth=0
max_lexical_product=0
entrypoint_charge=0
call_graph_acyclic=true
```

Therefore `APPROVED_CAPABILITIES`, approved types/operators/builtins/limits,
all proof modules and typed-IR records, and numeric-literal contracts remain
byte-identical to accepted Task 21. Only the compatibility-transform map gains
`"filter/crt:crt": "crt-metal-sine-v1"`; the generated manifest must record
that exact value and `numeric_literal_contract: "glsl-f32"`.

The source shadows three uniforms in `main`:

```text
uniform time@8  -> local time@193
uniform speed@9 -> local speed@194
uniform alpha@11 -> local input alpha@205
```

The first two exact copies remain live on lens/scanline paths. The local alpha
is the input pixel alpha and is dead after declaration; uniform `alpha@11`
controls the clamped blend, while output alpha is exactly `base_sample.w`.
Emitter names/qualification must preserve these identities. Do not delete the
dead local or alias a local to the uniform by spelling.

## Exact interface, resources, and fetch bounds

```text
PI:const float@1
TAU:const float@2
INV_THREE:const float@3
inputTex:sampler2D@4 / sampler slot S1
resolution:vec2@5
tileOffset:vec2@6
fullResolution:vec2@7
time:float@8
speed:float@9
seed:int@10
alpha:float@11
renderScale:float@12
fragColor:vec4@88 (output)
```

Resource requirements are exactly:

```text
uniforms=(inputTex,resolution,tileOffset,fullResolution,time,speed,
          seed,alpha,renderScale)
samplers=(inputTex)
outputs=(fragColor)
uses_texture=true
uses_derivatives=false
```

Pass routing is `inputTex <- inputTex`, `fragColor -> outputTex`, and identity
aliases `alpha -> alpha`, `speed -> speed`, `seed -> seed`. Metadata defaults
and ranges remain alpha 0.5 / [0,1] / zero 0, speed 1 / [0,5], and seed 1 /
[1,100]. `renderScale` is a runtime binding with canonical default 1, not a
public effect parameter.

Bindings must reject every missing/wrong-typed required value. `inputTex` is a
texture, seed is `int`, the three coordinate/dimension values are Vec2, and
time/speed/alpha/renderScale are numbers. There is no binding for the three
source constants, no second sampler, and no new output. Existing unrelated-
extra-binding behavior remains unchanged.

There are four static source `texelFetch(...,0)` sites, all in `main`. Alpha
clamped to zero executes the first site and returns one exact F32 fetch. The
normal path executes base, red, and blue sites for exactly three dynamic
level-zero fetches per pixel. `sample_scanline_bilinear` is procedural and
performs no resource fetch. Any helper fetch, nonzero LOD, second sampler,
copy-path count other than one, or normal-path count other than three fails.

The red/blue coordinate order is exact:

```text
x = (global_id.x + tileOffset.x) / max(renderScale, 1)
sample_global_x = displaced_sample_x * raw renderScale
sample_local_x = sample_global_x - tileOffset.x
fetch_x = trunc(sample_local_x)
```

Both current runtimes clamp integer fetch coordinates and map bottom-left
shader y to top-down storage. Do not change sampler semantics or use the
clamped `rs` in the raw-renderScale multiplication.

## Frozen public-adapter oracle

The input is the asymmetric top-down F32 formula recorded in the JSON. Runtime
fragment coordinates are bottom-left; frame is 17, delta-time word
`0x3c888889`, and runtime-seed word `0x41e80000`. All Vec2/scalar inputs cross
F32 storage. Every native configuration must match all F32 bytes, RGBA8 bytes,
stored probes, metrics, finite/copy/alpha/orientation facts, input immutability,
fresh-surface repeat, and local-adapter reconstruction evidence.

| Case | Size | tileOffset / fullResolution words | time / alpha / speed / seed / renderScale | Output F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| alpha-zero-exact-copy-tiled | 13x9 | `40e00000,41300000` / `42240000,41e80000` | `3ec00000 / 00000000 / 40000000 / 37 / 40000000` | `daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687` | `5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3` |
| alpha-negative-clamps-zero-copy | 9x7 | `40400000,40a00000` / `41b80000,41980000` | `3f200000 / be800000 / 3f800000 / 19 / 3f800000` | `5036ac34df07a6e89f8ae9cd5ee4fa3250a1962bdbda6bc4e29dc4ce512fb8a8` | `6b56cc6c2f780b54a655f04ba7deae8e61e8330ca84b5d5056e8c352dd16885c` |
| default-landscape-untiled | 13x9 | `00000000,00000000` / `41500000,41100000` | `3ec00000 / 3f000000 / 3f800000 / 1 / 3f800000` | `3134189c0654121a560abf3f8f102873b3395937ae244eaf1d6de7d03e6c8192` | `c9a7375db6ae12c5dc1f0b2fa49669892d405c55ab587cc0a054d75d9d66eeb9` |
| alpha-above-one-clamps-and-preserves-input-alpha | 13x9 | `00000000,00000000` / `41500000,41100000` | `3ee00000 / 3fe00000 / 3f800000 / 11 / 3f800000` | `e6d5a0788f2a23100ee9968186ac1f1a05175ecf6972e8503bd92cd8130a4bfd` | `b971437eec882ffd958b151216992caad58a8a681211f161ec60480820d52fee` |
| landscape-tiled-render-scale-two | 13x9 | `40e00000,41300000` / `423c0000,41b80000` | `3ee00000 / 3f400000 / 3fe00000 / 37 / 40000000` | `7e9a4e738ad67051674ea5d8e7e2333585e943bbe45fcdbdf3c9e59635c359ec` | `2ed1841d5be9df1f576fecf81bab403ad848fb96d4e33055525a1520e905d75c` |
| portrait-tiled-fractional-render-scale | 9x13 | `40a00000,40400000` / `41b80000,42140000` | `3f1ccccd / 3f200000 / 40000000 / 100 / 3fc00000` | `cdc080912dc354a6052447427814040e552d7c38edf4e1c499d8f7c80bd196be` | `ecfb38a778ba9e40d9bacfb5a8f1f62a810cd929d14b83c2bf5d4abc6bc0d079` |
| speed-zero-nonzero-time | 13x9 | `40800000,40c00000` / `41f80000,41c80000` | `3f600000 / 3f600000 / 00000000 / 19 / 3f800000` | `f83304619eda688e29c3ae34b4c913535919c3505c2f59f5100b587ddf52ddd8` | `16727fe42c77a453e47d0dcfcc14b079b39a84d06683ac8d0f689749611ec70e` |
| time-zero-positive-speed | 13x9 | `40400000,40000000` / `41e80000,41a80000` | `00000000 / 3f600000 / 3fc00000 / 53 / 3f800000` | `bc5ed1803bb52ee4d075d4c9ff6e5cc62ca2ba6f60f7d5aed93d1c237ad81b98` | `59a3fef349d5457d514174dba0e328bcd1723f97d0d8fdf82649ed217265f5d0` |
| full-resolution-zero-fallback | 13x9 | `40000000,3f800000` / `00000000,00000000` | `3ea00000 / 3f400000 / 3fa00000 / 11 / 3f800000` | `19b91bedac3685b2c368a1c8da9eb89ae6e57e8deeee513b4151cf12dad3896f` | `fc49c1f7a2ea1c69db968ceabfaa4293ba8b193e13a5634b51ef763d0fea50d6` |
| square-large-time-max-metadata | 11x11 | `40400000,40000000` / `41f80000,41f80000` | `4640e680 / 3f800000 / 40a00000 / 100 / 3fc00000` | `5169bfe5072efd935eafd52f13b413c7b4f5f9834e9991f5a6207a877a6bfc48` | `3a0f86f1aac14e290bbc2d22675f4af5bfa1a08fc68cbfc59c92331f5daf59a5` |
| render-scale-below-one-clamps | 13x9 | `00000000,00000000` / `41500000,41100000` | `3ef00000 / 3f000000 / 3fa00000 / 29 / 3f000000` | `d963390a996552ce28b3f8f5c7b7971072a60566ebad0bf29beb329fa4a24de2` | `65e933fe048522db9d4b8eae08057c6ca56f3d4b53510181fb2e288f25546716` |

The first two outputs are exact F32 copies. All nine normal cases change every
pixel's RGB and preserve every input alpha bit, including values outside
`[0,1]`. Every output lane is finite.

### Exact 18-mutation sensitivity

The JSON's exact replacement strings/counts, required-divergence and required-
identity lists, all per-case hashes/diffs, and maximum differences are
normative. Summary counts are:

| Mutation | F32-changing cases / 11 | RGBA8-changing / 11 | Max changed F32 lanes |
| --- | ---: | ---: | ---: |
| public-metal-sine-disabled | 9 | 9 | 351 |
| uniform-time-local-alias-offset | 8 | 8 | 346 |
| uniform-speed-local-alias-offset | 9 | 9 | 359 |
| output-alpha-uses-uniform-not-shadowed-input | 9 | 9 | 117 |
| uniform-alpha-clamp-disabled | 2 | 2 | 351 |
| render-scale-clamp-disabled | 1 | 1 | 328 |
| full-resolution-fallback-disabled | 1 | 1 | 320 |
| shape-frequency-axes-unswapped | 2 | 2 | 213 |
| scanline-parity-forced-first-value | 9 | 9 | 233 |
| red-tile-local-subtraction-disabled | 6 | 6 | 319 |
| blue-tile-local-subtraction-disabled | 6 | 6 | 340 |
| red-channel-assembly-uses-blue | 9 | 9 | 323 |
| restore-hue-disabled | 9 | 9 | 341 |
| saturation-boost-disabled | 9 | 9 | 344 |
| vignette-alpha-forced-zero | 9 | 9 | 337 |
| contrast-gain-1-25-to-1 | 9 | 9 | 363 |
| local-mean-eager-f32-materialization | 9 | **0** | 37 |
| seed-base-disabled | 9 | 9 | 345 |

The sine-disabled mutation must diverge in default, tiled landscape, and
large-time square cases while both alpha-copy controls remain identical. The
eager-F32 local-mean mutation must diverge in F32 for default and remain
identical in both copy cases, while changing zero RGBA8 bytes across all 11
cases. That is the mandatory proof that RGBA8 cannot substitute for F32.
Branch-specific renderScale and full-resolution mutations must diverge in only
their dedicated case and match the ten exact control cases recorded in JSON.
Every other required control list is consumed directly from the frozen JSON;
tests must not weaken it to aggregate counts.

## Four-mode forgery matrix and negative profile

Every typed-tree mutation must be submitted independently to both
`validate_capabilities(...)` and direct `render_typed_cpp(...)`. Exercise the
two tree states crossed with the two registration states:

| Mode | Tree | `compatibility_transform` carrier | Expected validator/emitter result |
| --- | --- | --- | --- |
| 1 | authentic raw pre-transform CRT | absent / `None` / manifest `none` | reject: CRT is not publishable without public sine compatibility |
| 2 | authentic raw pre-transform CRT | exact `crt-metal-sine-v1` | reject: required post hashes/sites absent |
| 3 | authentic exact post-transform CRT | absent / `None` / manifest `none` | reject: transformed tree has no matching authority |
| 4 | authentic exact post-transform CRT | exact `crt-metal-sine-v1` | accept |

Repeat modes 2 and 4 with every site/tree/interface/resource mutation. Test
both retained authentic caller hash arguments and attacker-recomputed caller
hash arguments; neither may rescue a forged tree. Wrong transform names,
another key carrying the name, duplicate/extra map entries, or schema/manifest/
validator/emitter carrier disagreement reject.

### Identity, transform, and numeric tampering

- wrong corpus revision, key/runtime key, effect/pass, source path/bytes/size,
  raw or normalized hash/text, canonical factory name/text hash, public adapter
  file/factory identity, or canonical runtime hash;
- changed pre/post function, whole, interface, emitted-block, function count,
  function order/ID/signature/body count, source-function census, or loop proof;
- nonempty/changed defines; missing/wrong numeric carrier; `source-double` or
  any value other than `glsl-f32`; missing/wrong/extra transform map entry;
- zero/five/seven sites; missing, duplicate, reordered, partial, already/twice
  transformed site; wrong function/path/span/signature/type/category/argument;
- INV_TAU/TAU literal spelling/value/type/span changed; float constructor or
  floor missing/reordered/retyped; floor signature/callee changed; wrong
  subtraction/multiplication grouping; shared-turn subtree changed; outer sin
  changed; `fract`, modulo, `fmod`, polynomial, helper, runtime switch, global
  `sin`, `cos`, or unrelated builtin changed;
- compound simplex argument made effectful or duplicated outside its exact
  pure arithmetic tree; any non-site node changed, including the 30 functions
  required dataclass-equal.

### Alias, body, ordering, and F32 tampering

- uniform/local time, speed, or alpha ID/name/type/storage/writability changed;
  local copy source changed; local alpha used as blend strength; uniform alpha
  emitted as output alpha; dead-local deletion or spelling-based capture;
- alpha clamp/predicate/early copy altered; output input-alpha preservation,
  base/uniform mix, scanline parity, frequency axes/equality, fallback, rs
  clamp, raw renderScale remap, tile subtraction, truncation, or coordinate
  order changed;
- red/green/blue fetch or assembly order changed; hue application/restoration,
  saturation, vignette, local-mean contrast, seed, simplex, mask, or wrapping
  order/constants changed;
- eager/missing F32 boundary, reassociation, contraction, fast-math, literal
  widening, removed `-ffp-contract=off`, RGBA8-only comparison, nonfinite
  transition, or fresh-render nondeterminism.

### Interface, resource, stack, and closed-world tampering

- any declaration/binding missing, duplicated, reordered, renamed, renumbered,
  retyped, storage-changed, made writable, or routed differently;
- source constants made bindings, changed/added global, wrong sampler slot,
  second sampler/output, wrong resource tuple/texture flag, wrong metadata
  default/range/alias, missing/wrong binding type, or nonzero LOD;
- static fetch count/order other than four; dynamic copy/normal maximum other
  than one/three; helper fetch; sampler orientation/clamp change;
- added loop, recursion, array/table, dynamic stack, allocation, callback,
  exception, indirect/virtual call, derivative, varying, block, matrix, struct,
  parameter direction, or unsupported type/operator/builtin;
- counts other than 116/118/94/212, catalog digest/list/order/uniqueness drift,
  missing/duplicate CRT, any other remaining key admitted, or compatibility
  reused by another key/source/define/pass/factory;
- any Task 17-20 proof or prior compatibility map changed, Degauss changed, any
  prior generated block changed beyond the sole allowed namespace normalization,
  or unrelated source/test/runtime/generated file drift.

Mutation helpers must locate exact typed nodes and assert one intended
replacement. Source-string-only tests and caller-supplied digest authority are
insufficient.

## Owned implementation files

Only after accepted Task 21 and independent Task 22 brief review may an
implementation modify:

- Create `tools/glslcpp/frontend/crt_compatibility.py`: hard-code provenance,
  six pre/post sites, exact inline rewrite, and post authenticator.
- Modify `tools/glslcpp/generate_typed_slice.py`: register/apply only
  `crt-metal-sine-v1`, add the exact CRT source profile and both-boundary
  validation, add the transform map entry, and update accepted count 115 ->
  116.
- Modify `tools/glslcpp/emit_typed_cpp.py`: recognize only the exact CRT
  transform carrier and independently authenticate the exact post tree before
  existing generic emission. Add no new emission primitive.
- Modify `tools/glslcpp/typed_slice.json`: insert exactly the one sorted `{}`
  CRT entry and exact transform map entry; change no other vocabulary/map.
- Modify `tests/test_typed_generator.py`: pre/post/site/hash, four-mode forgery,
  capability-exclusion, transform, deterministic generation, and generated
  isolation/code-shape tests.
- Modify `tests/test_typed_slice.cpp`: all 11 public-adapter native cases,
  full hashes/probes/metrics/repeat/input/finite/alpha/orientation checks.
- Modify `tests/test_generated_kernels.cpp`: exact CRT binding failures,
  declaration/order/route, and exact 118-key catalog/count tests.

Regenerate only through the accepted generator:

- `src/typed_generated/typed_slice.cpp`
- `src/typed_generated/typed_manifest.json`
- `include/noisemaker/generated/catalog.hpp`

Do not modify typed IR/semantic/proof modules, GLSL runtime/header, sampler,
Surface, corpus, CMake, public binding API, Degauss tests/source, or unrelated
generated bodies. No runtime/helper source file is needed. If an owned-file
conflict with accepted Task 21 cannot be isolated, stop for review.

### Implementation seam clarifications

- Compatibility authentication must run at the beginning of both
  `validate_capabilities(...)` and `_Emitter.__post_init__`, keyed on the exact
  CRT key and carrier, before generic current-vocabulary acceptance. Raw CRT
  with no carrier and transformed CRT with no carrier must therefore reject.
  Both boundaries may call the same pure post authenticator, but each invokes
  it independently and trusts no prior validation or mutable token.
- Aggregate `repr` hashes do not prove object sharing. The post authenticator
  and tests must additionally require that the subtraction's left `turns`
  object `is` the floor child's `turns` object, and application tests must
  require the original argument object is retained.
- Raw-to-post argument object identity is an application-time invariant only:
  capture all six authenticated raw sine arguments and require each generated
  scaled child to be the same object. A test-local equal-field clone must
  demonstrate that this invariant detects replacement. Standalone validator
  and emitter post authentication cannot reconstruct raw object provenance;
  they require exact structural/site/hash equivalence and shared-turns DAG
  identity, but must not claim to reject a semantically and codegen-identical
  clone of an argument node. No provenance token or proof field is authorized.
- Apply the compatibility transform before Task 17-20 proof attachment. Reject
  any preexisting foreign proof during application, and independently require
  all four proof fields to remain `None` in the post profile.
- Site-path code must define the brief's expression-root `0` sentinel
  explicitly: statement index, `eN`, root `0`, then child indices. Do not
  silently compare the frozen paths to a walker representation that omits that
  sentinel.
- Each frozen CRT oracle case has exactly seven probes. Native storage is
  therefore 42 `uint32_t` values per case: x, y, and four lane words for each
  probe.
- The frozen MJS generator's `--check` owns all 18 factory-mutation
  sensitivities and local adapter reconstruction. Native C++ consumes only the
  11 canonical case records; neither JSON nor the CPU repository becomes a
  runtime/build dependency.
- `renderScale` is an exact required runtime number binding but intentionally
  is not a public metadata parameter. This is not a metadata contradiction or
  permission to add a public parameter.

## Test-first order and review gates

1. **Preflight:** authenticate the five Task 21 evidence artifacts, four Task
   22 artifacts, accepted Task 21 final hashes/counts/gates, and unchanged
   emitter. Record all accepted Task 21 owned/generated hashes. Stop on drift.
2. **RED transform/profile:** add exact pre/post/site/four-mode and negative
   profile tests. Observe unknown transform / missing CRT and failure to match
   public adapter semantics.
3. **GREEN transform:** implement only `crt_compatibility.py`, generator
   registration/profile, and emitter post authenticator. Run focused tests;
   independently review all six sites, pre/post hashes, unchanged capability/
   proof/numeric vocabulary, and no global sine/runtime change.
4. **Slice/generation:** insert CRT after Craquelure, run `--check` to observe
   only expected three-output drift, then `--write`. Verify exact projected CRT
   block hashes, transform/numeric manifest fields, and 116 typed count.
5. **Generated isolation:** split accepted Task 21 and Task 22 C++ at
   `// Typed IR program:`. Require raw identity for all 19 blocks before CRT;
   across all 115 prior blocks normalize only `typed_[0-9]+` to one sentinel
   and require byte identity. Any other byte changes fail.
6. **Bindings/catalog:** add exact success plus every missing/wrong type,
   unrelated-extra control, declaration/route checks, exact catalog list/
   digests/count/sortedness/uniqueness, and all remaining-key exclusions.
7. **Native oracle:** add all 11 exact cases and compare full F32/RGBA8 bytes,
   probes, metrics, copy/alpha/orientation/input/repeat facts in Debug and
   Release. Independently compare every native result to frozen public-adapter
   JSON before broader gates.
8. **Full acceptance:** run ASan/UBSan, `.su` stack measurement, Release
   disassembly, scoped allocation/dispatch/fetch/code-shape inspection, all
   Python/CTest/prior-oracle/generator gates, and final owned/unrelated hashes.

Stop after each numbered review gate on any mismatch. Do not fix parity by
broadening the compatibility transform, changing a runtime function, adding a
capability, or changing the oracle.

## Generated, native, stack, and drift gates

Run from `.` with fresh `/tmp` build
directories and no Git command:

Use Ninja only when `command -v ninja` succeeds. If Ninja is absent, as it was
in the accepted Task 21 environment, substitute `-G 'Unix Makefiles'` for
`-G Ninja` in each of the three fresh configure commands below while preserving
the exact build directories, build types, compiler/linker flags, build, and
CTest commands. Record which generator was selected. Do not reuse a directory
configured with the other generator.

```sh
shasum -a 256 \
  docs/port-engineering/task-22-frontier-audit.md \
  docs/port-engineering/task-22-oracle-generator.mjs \
  docs/port-engineering/task-22-oracles.json \
  docs/port-engineering/task-22-oracle-report.md
node docs/port-engineering/task-22-oracle-generator.mjs --check

python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_task22_crt_transform_is_exact \
  tests.test_typed_generator.TypedGeneratorTests.test_task22_crt_four_mode_forgery_matrix \
  tests.test_typed_generator.TypedGeneratorTests.test_task22_crt_profile_rejects_identity_interface_and_tree_drift \
  tests.test_typed_generator.TypedGeneratorTests.test_task22_adds_only_exact_transform_no_capability_proof_or_numeric_mode \
  tests.test_typed_generator.TypedGeneratorTests.test_task22_crt_exclusions_remain_closed
python3 -m unittest discover -s tests -p 'test_*.py'

cmake -S . -B /tmp/noisemaker-task22-debug -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fstack-usage -fstack-size-section -ffp-contract=off'
cmake --build /tmp/noisemaker-task22-debug
ctest --test-dir /tmp/noisemaker-task22-debug --output-on-failure

cmake -S . -B /tmp/noisemaker-task22-release -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS='-fstack-usage -fstack-size-section -ffp-contract=off'
cmake --build /tmp/noisemaker-task22-release
ctest --test-dir /tmp/noisemaker-task22-release --output-on-failure

cmake -S . -B /tmp/noisemaker-task22-sanitize -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fsanitize=address,undefined -fno-omit-frame-pointer -fstack-usage -fstack-size-section -ffp-contract=off' \
  -DCMAKE_EXE_LINKER_FLAGS='-fsanitize=address,undefined'
cmake --build /tmp/noisemaker-task22-sanitize
ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
  ctest --test-dir /tmp/noisemaker-task22-sanitize --output-on-failure
```

Rerun every exact accepted Task 15-21 oracle/check command and all existing
corpus, semantic, transactional-generation, deterministic-CWD, Python, and
native gates. Use accepted reports rather than guessing filenames.

Extract only the generated CRT namespace before code-shape checks:

```sh
awk '
  $0 == "// Typed IR program: filter/crt:crt" { crt = 1 }
  crt && /^namespace typed_[0-9]+ \{/ { body = 1 }
  body { print }
  body && /^}  \/\/ namespace typed_[0-9]+$/ { exit }
' src/typed_generated/typed_slice.cpp > /tmp/task22-crt-namespace.cpp
test -s /tmp/task22-crt-namespace.cpp
test "$(rg -c '^namespace typed_[0-9]+ \{$' /tmp/task22-crt-namespace.cpp)" = 1
rg -n -C 4 '0\.15915493667125702|6\.2831854820251465|glsl::sin|glsl::floor|fetch_texel|void pixel' /tmp/task22-crt-namespace.cpp
if rg -n 'operator new|operator delete|malloc|free|std::function|std::map|std::unordered_map|std::variant|std::string|throw|alloca|\.at\(' /tmp/task22-crt-namespace.cpp; then
  echo 'forbidden construct in CRT namespace' >&2
  exit 1
fi
find /tmp/noisemaker-task22-debug /tmp/noisemaker-task22-release /tmp/noisemaker-task22-sanitize -name '*.su' -print
rg -n 'crt|pixel|compute_lens_offsets|animated_simplex_value|simplex_noise|permute|mod289|value_noise_3d|hash3' /tmp/noisemaker-task22-{debug,release,sanitize} -g '*.su'
```

Typed-tree tests own exact site counts and post hashes. Generated tests must
brace-extract `pixel` and the five transformed functions, prove six outer
`glsl::sin` routes with the exact float/floor reduced-turn subtrees, four
static `fetch_texel` calls in pixel, exact helper routing, no generated C++
`main`, and no untransformed raw sine site. Scope forbidden-pattern scans to
the CRT namespace so binder/catalog State allocation is not misclassified.

The deepest live bounded source chain is:

```text
pixel -> compute_lens_offsets -> animated_simplex_value
      -> simplex_noise -> permute -> mod289_vec4
```

Other relevant chains include `pixel -> get_scanline_base_values ->
value_noise_3d -> fade_vec3 -> fade`. There are no loops, recursive edges,
arrays, size-dependent frames, dynamic allocation, callbacks, exceptions, or
indirect/virtual calls in the pixel namespace. The binder's one-time State
allocation and external surface storage are not per-pixel stack.

Preserve Debug and Release `.su` records for `pixel` and every reachable helper.
Report static frame bytes and the maximum non-inlined chain sum, or Release
inlining/disassembly evidence. Use `llvm-objdump -d` or `otool -tvV` to prove
no allocator/indirect route and the expected reduced-turn calculations. Any
dynamic/unbounded stack result, recursion, allocation route, missing stack
record without disassembly resolution, or fetch count above three is failure.

For generated drift, require:

- raw-byte identity for all 19 accepted Task 21 blocks before CRT;
- across all 115 accepted Task 21 blocks, byte identity after replacing only
  `typed_[0-9]+` namespace ordinals with one fixed sentinel;
- no normalization of whitespace, comments, literals, factories, code, keys,
  manifests, or headers;
- only the six owned existing files, the three generator outputs, and the
  one new compatibility file changed; all unrelated hashes remain exact.

## Completion evidence and hard stop

Task 22 can be declared complete only with:

- accepted Task 21 baseline evidence and before/after SHA-256 for every owned
  file/output;
- all Task 22 artifact, source, canonical/public factory, runtime, pre/post
  function/whole/interface, six-site, numeric, binding, alias, and resource
  locks reproduced;
- both validator and emitter passing the complete four-mode and structural
  forgery matrix with attacker-updated caller hashes unable to rescue drift;
- no capability/proof/type/operator/builtin/numeric-mode/runtime/sampler/ABI
  change and exactly one CRT compatibility-transform entry;
- exact 116 typed / 118 public / 94 unported / 212 corpus counts, exact sorted
  lists/digests, CRT once, and all other remaining keys excluded;
- all 11 native full-F32 and RGBA8 hashes plus probes/metrics/input/finite/
  alpha/copy/orientation/repeat behavior in Debug, Release, ASan, and UBSan;
- all 18 canonical mutation sensitivities, including the 9-case/zero-RGBA8
  eager-F32 discriminator and raw-factory/public-adapter discriminator;
- exact one/three dynamic and four static fetch accounting, scoped generated
  code shape, no allocation/dispatch/recursion, `.su` stack table, maximum
  chain bound, and Release disassembly;
- exact generator `--check`, zero failed full Python/native/prior-oracle gates,
  exact generated isolation, and only owned-file drift.

This brief stops before design and implementation. If Task 21 is not accepted
exactly, any transform/site/hash/oracle cannot be reproduced, or native parity
fails, stop and request a revised independently reviewed scope. Do not fix
forward by changing global sine behavior, adding a capability/proof/runtime
helper, editing the corpus or oracle, or admitting another key.
