# Task 23 literal source-global integer scope and proof brief

> **Status:** frozen read-only scope/proof contract. Stop before design and
> implementation. This file authorizes no repository edit and no Git operation.

**Goal:** admit exactly six direct-public-canonical CPU factories whose only
remaining shared frontend gap is one top-level literal `const int` used as an
already-supported counted-loop bound:

```text
filter/bloom:ntapGather
filter/directionalBlur:directionalBlur
filter/spinBlur:spinBlur
filter/strokes:stkSmear
filter/vaseline:upsample
filter/wind:wind
```

The exact key spellings above are normative. In particular, the source paths
are `filter/strokes` and `filter/vaseline`; abbreviated `strokes/...` or
`vaseline/...` keys are invalid.

**Authorized language delta:** exactly one capability,
`source-global-literal-int-v1`. It admits one positive decimal `int` literal as
the initializer of one immutable top-level `const int`, materializes that value
as an ordinary automatic immutable `std::int32_t` in each referencing generated
function, and seeds the existing counted-loop proof under bound kind
`source-global-const-literal`. It adds no other global form, type, operator,
builtin, expression, statement, loop shape, proof metric, runtime helper,
resource ABI, compatibility transform, or numeric-literal mode.

## Hard Task 22 gate

Do not implement Task 23 against the currently inspected 115-key Task 21 tree
or an in-flight Task 22 tree. First require final, independently accepted Task
22 evidence for all of the following:

- exactly **116 typed / 118 public / 94 publicly unported / 212 corpus**;
- exact CRT public-adapter parity, all frozen function/whole/interface/site and
  native oracle hashes, four-mode transform matrix, generated isolation,
  Debug/Release/ASan/UBSan, stack, disassembly, and full Python/CTest gates;
- final before/after hashes for every Task 22-owned file and generated output;
- accepted amended Task 22 brief SHA-256
  `f8c5a9fdd18a5ca587dee47d7d297503325b1eea374a867f5e9ad8d196c57e59`;
- accepted Task 22 implementation-design SHA-256
  `1e347e6565ae37aecd5c2edf9db3b9fc851fe3b2591f253c9f57eaf409be63f1`,
  final report SHA-256
  `69bcc357de8a8e6df73b8b80ec0e8b5d3e2ca71f12edee25750e21f95c68a7d9`,
  and final independent review SHA-256
  `102a56ab642c1884319a827530639d0dc9943441393e03ea497274812912e5af`;
- exact accepted Task 22 full Python discovery evidence: **122/122 passed**
  on the final reviewed bytes;
- frozen Task 22 frontier/generator/JSON/report hashes
  `c3d006f354f6ca9bb65c42b8e6f8bbdac194ddf1a6486ccbf890bfe818f16160`,
  `dc2044ee2bf007f1888f958a09185445caef34c064a6e4b3eea340a09ad49a27`,
  `c927f467418f9ef154a817869228a0918c2fc222ef3bb64f2b0a6bab8a74e889`,
  and `36ac4f8b85a0fefc47c403eef47bd11ceb40e9774fa709125f01bc4e2ea075aa`.

At Task 23 preflight, record accepted Task 22 hashes for every Task 23-owned
file and generated output. If any accepted count, key list, interface, hash,
command, generated block, or proof contract differs, stop and revise/review
this brief. A Task 22 brief or local green test without final acceptance is not
the gate.

Conditional on that accepted baseline:

| State | Typed | Public | Publicly unported |
| --- | ---: | ---: | ---: |
| Accepted Task 22 | 116 | 118 | 94 |
| Task 23 exact result | **122** | **124** | **88** |

The projected newline-terminated sorted 122-key typed list has SHA-256
`9db3013a6b0f78d0b95fcb6713c54ace95e82d1545e796e7a380add23c009f0b`.
After adding only the separately maintained `filter/invert:inv` and
`synth/solid:solid`, the 124-key public list has SHA-256
`2b84fff4d6f35aec1ac6bcc35188d9893e3194c90b9c428775a7308ce1f6281a`.
Tests must compare the explicit lists as well as the digests.

Final zero-based typed positions and neighbors are exact:

| Position | Previous | New key | Next |
| ---: | --- | --- | --- |
| 7 | `filter/bloom:composite` | `filter/bloom:ntapGather` | `filter/celShading:celShadingBlend` |
| 23 | `filter/deriv:deriv` | `filter/directionalBlur:directionalBlur` | `filter/fibers:fibersBlend` |
| 77 | `filter/spatter:spatter` | `filter/spinBlur:spinBlur` | `filter/stamp:stBlurH` |
| 82 | `filter/strokes:stkPost` | `filter/strokes:stkSmear` | `filter/tetraCosine:tetraCosine` |
| 92 | `filter/unsharpMask:usmCombine` | `filter/vaseline:upsample` | `filter/vignette:vignette` |
| 96 | `filter/watercolor:wcSeed` | `filter/wind:wind` | `filter/wormhole:blend` |

## Frozen artifacts

| Artifact | SHA-256 |
| --- | --- |
| `task-23-frontier-audit.md` | `cc49663ed312f95fc3d83cde245a95dc8719a1a90059d750ae9f7b9611061666` |
| `task-23-oracle-generator.mjs` | `f91ece9510c092e9c0221fc9b326522840c0b10eb3433b858eea3d786f7f57a2` |
| `task-23-oracles.json` | `a832ea550911634dbe2e98e62b51837d8fa57612243416a88f70af69f626c52d` |
| `task-23-oracle-report.md` | `8a060f2b74fcc4c7d8ed74ca315b8239a28be0475a57067f3f223667bd009303` |

Run the generator's `--check` before implementation and at every review gate.
`../noisemaker-for-cpu` is pinned oracle provenance only;
it must not become a native build, runtime-test, installed, or generator
dependency.

## Exact source, public factory, and typed identities

Corpus revision is exactly `a024dc3a960cc44af454abc7aebce50456c194e6`.
The pinned canonical generated CPU runtime SHA-256 is
`e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`.

| Key | Defines | Raw bytes / SHA-256 | Normalized SHA-256 | Canonical factory / text SHA-256 |
| --- | --- | --- | --- | --- |
| `filter/bloom:ntapGather` | `{}` | 2196 / `f11c983976cb8450d611e8d888bd151a4c2cfdda8d9d772f906608dedb99d237` | `1d20c3bccadf30a1f6c3c6f8903ed805287933fcc1257d3ae6d4b98c5d0b9f81` | `canonicalFactory23` / `a737ac48f663f041f763677680ab5d5282482ab6d10143939de055b980c4207c` |
| `filter/directionalBlur:directionalBlur` | `{}` | 1153 / `1e4a9d6371683b75a1dbefa968e1536e0017e921fe02f80e600e8f1482e8691c` | `587b19df3989bf8bb649a86265f4210561077ccadcec30f0a92077510bcbf668` | `canonicalFactory47` / `a3803238488c9bd2fe786b931a0a2ba81a057d02f984017d8e10073c68873344` |
| `filter/spinBlur:spinBlur` | `{}` | 3077 / `a5ee242e189066b55d4d5c3140e957418bdff582b367d1f6d4cdfee4c333b405` | `b829271f6c58fccde0e5723cd2bc7d7d3f47acfeb4cf1ce157bc996fb04ff1ee` | `canonicalFactory145` / `c6b97d30339acd21fc01d2d2cd31073c62d2ba82dbb80e95d9457b0f59737547` |
| `filter/strokes:stkSmear` | `{"MODE":0}` | 14787 / `dac057232a650f3c9eb56829aa12507b639d8632f6fc132cbd067a28996fa4db` | `796bad6231e640aec7c6f471465f57112f77394d921bff9902833955e1e20f15` | `canonicalFactory155` / `8f82fbdc740e4bf5448e53823c833e22f37db0aacadad01bc4983a4e58e72010` |
| `filter/vaseline:upsample` | `{}` | 2524 / `39055a214903d09a9b2dd8db9ec5b2023a920c22707ec424ae90d5fb90ebf461` | `1785f58af7b191e5a4f1a55223476d12372c97f87c062d34ecefe07550b05c93` | `canonicalFactory170` / `322ba53c3b001878f026c615998086ef7732277b5f2d2401064ea2497cb6113a` |
| `filter/wind:wind` | `{"METHOD":1}` | 3520 / `68eb0f4deca51ab5352307fa06509b153cf19a29cea4820d054adafa42655f22` | `665e842850e766cbf988212669457fb9fd76dff59e52a2f7b2cedd242e490fa4` | `canonicalFactory177` / `163a65997398acd140ec10572d9253914d1659fc240187c1eae5a9de354810dd` |

For all six, runtime inspection proved
`kernelFactories.get(key) === canonicalKernelFactories[key]` and proved the
absence of `canonicalAdapterFactories[key]`. The public factory is therefore
the pinned canonical factory itself. Strokes and Wind oracle execution must
still bind their resolved profiles `MODE=0` and `METHOD=1`; omitting those
bindings exercises the wrong generated branch and is a failed oracle.

The typed hashes are exact:

| Key | Pre functions | Post functions | Pre whole | Post whole | Interface pre/post |
| --- | --- | --- | --- | --- | --- |
| `filter/bloom:ntapGather` | `a000425b8ae57882a6877bf2c390f3d1fb3ce226d0181f0fa76d8851d7a79163` | `66138a890082a6185afea09a5f9a169114193bf0134b6153737a663b27a86270` | `915a83f7673ec52fd79e8ed7a0a02094f720fbaa575db63318227f14c3aa2f51` | `ff1fa1ba17abb3bdcd8daf7059b517609db49cfc62c10836b86ea86a1d4c696c` | `b1bbe45469447847e91fbb66b6ee1b0cfc5a5a07cdac53cb322a728e295b8fb8` |
| `filter/directionalBlur:directionalBlur` | `8c0e81f16787bce2ab63a414b9774702ce3ceac9be71f7bad46c9bccde14ddfa` | `6e57feabe450d500b7ac2ddf328e855d72e0eb2c764c89b94c6c6f9afa184f96` | `30011a8fd6f15943857b5d978a5383cbf0408becbfcdd2a8e9fd08eddab11153` | `21e4cc0784b7bbffa453e549776e3ed332df1219bf77d1c42bf32d650f8c1f7b` | `3934c143ad58175d44458d78b2641badf31363c0f8438b1b5f656cbf6e269858` |
| `filter/spinBlur:spinBlur` | `f9563d0e1e160ac48d4f6b0becdcb4ced10342039f0ef8c0a09f822e0c8cc8e8` | `974b46a9db569acad639c8fd500c839f48f15b9bd42baac27374e204ca1d9e51` | `5d3e1a5f3907bc1678620013f2a5e6854c386d12af60a1e92bc196c06ee7e6bc` | `af920749f40d2f9eafcfa3bf9d1ffccf3164571475e1b9162053cba5b3e43bff` | `4b4d07b3a0cd718e48c976ef202de9dff5e7c35d422c371f6243ff0fbf9fa723` |
| `filter/strokes:stkSmear` | `5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9` | `0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344` | `b7b6c65e3275843bd141f9b0c1fcf40daad671dcbeebef2db6a4684ec750790c` | `5ac93407e6a52ef895a887b3817c781d58ac9b974afe30415f31c6b4a9e8cbbf` | `8fe812a5bdfa275782969cb6146b0e8005e8dc521af9e5b10926bc49d2b89fef` |
| `filter/vaseline:upsample` | `9f2f11099585a38441157f4e4bb847808c4fd81df1c69cc79d1b651b0fe90374` | `2e86ae95c587a74560e8cdd1d72bdf3f1d5cc9a14183ed136dc1950a590b2389` | `5771c7b74d9e30e47f0b84438bc40e16d4c0da36346325862bef6516c5f0d60d` | `831676d46152cd861a4f658fb6bfe75c06c3a8275d2b9acaae00ae8038cc39a6` | `fc9fd33b3e14a9808c66c17f3b358d79be3b97c11c6fd6ea281ce51118e0de9e` |
| `filter/wind:wind` | `214d03b9c58da73392e8b05200035b6e81244dbec06705302a237da23081ef6d` | `70e4d4612ed144e0beb110e8fbbaf5d02b60e27e23fbf6961a30ac8d43bbb8e4` | `b08edc234c42aa039867a7c549eff408e7c3c51cfa28d0951a437a00043a2dc0` | `6a5cb2724a9dfa61aaf5f7879a65fe9ec3cd353b7e815f20eb0915e4a103f9e0` | `455e2e5350b3a027556adc181e5ce3099ca395f801add229956b750d31acdf85` |

Hash serialization is exactly:

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

The post hashes differ only because exact loop proof objects are attached. The
declarations, expression/statement trees, resources, functions apart from
their loop proof fields, interfaces, and define maps remain dataclass-equal.
Caller-provided hashes are drift alarms, never proof authority.

## Exact global and counted-loop proof boundary

| Key | New authenticated integer global | Symbol ID | Loops / caps | Max depth/product | Entrypoint charge |
| --- | --- | ---: | --- | --- | ---: |
| Bloom | `const int MAX_TAPS = 64;` | 8 | 1 / `[64]` | 1 / 64 | 64 |
| Directional Blur | `const int N = 32;` | 6 | 1 / `[32]` | 1 / 32 | 32 |
| Spin Blur | `const int N = 32;` | 9 | 1 / `[32]` | 1 / 32 | 32 |
| Strokes | `const int MAX_TAPS = 24;` | 8 | 3 / `[3,3,24]` | 2 / 24 | 72 |
| Vaseline | `const int TAP_COUNT = 32;` | 8 | 1 / `[32]` | 1 / 32 | 32 |
| Wind | `const int MAX_STEPS = 128;` | 8 | 1 / `[128]` | 1 / 128 | 128 |

Admission requires all of these simultaneously:

1. exact key, source SHA, define map, declaration name, stable symbol ID,
   storage `const`, type `int`, non-writable symbol, and exact positive decimal
   literal/value in the table;
2. exactly one authenticated non-interface source-global `const int` and
   exactly one initializer child for that integer; no sign node, cast,
   constructor, dependency, identifier, expression, suffix, hexadecimal/octal
   form, mutation, alias, address, escape, shadow confusion, or extra integer
   read outside the authenticated functions;
3. every loop retains the existing fresh local `int` induction, literal start,
   `<` or `<=`, unit `++`, exact bound-symbol identity, permitted break/
   continue behavior, no loop return, and existing trip calculation;
4. proof bound kind exactly `source-global-const-literal`; exact trip, lexical
   depth/product, effective depth, acyclic call graph, and entry charge as
   recomputed from the typed tree; existing global limits remain 128 trips,
   depth 3, product 4096, and entry charge 4096;
5. capability/profile exactly `source-global-literal-int-v1` and exactly the
   six-row identity map above. The capability is not a general license for a
   seventh program or declaration.

The selected sources also contain these exact already-supported source-global
`const float` declarations, which remain authorized only by their frozen source
profiles and do not count as the new integer capability:

| Key | Exact existing `const float` globals |
| --- | --- |
| Bloom | `GOLDEN_ANGLE@9 = 2.39996323`, `PI@10 = 3.14159265359` |
| Directional Blur | none |
| Spin Blur | none |
| Strokes | none |
| Vaseline | `RADIUS@9 = 48.0`, `GOLDEN_ANGLE@10 = 2.39996323`, `BRIGHTNESS_ADJUST@11 = 0.15` |
| Wind | `STEP_PX@9 = 1.0`, `MAX_REACH@10 = 128.0` |

No other non-interface global is admitted. The exact float declarations,
initializers, symbols, reads, and automatic-local materialization must remain
dataclass- and generated-shape-identical to accepted Task 22 behavior.

The semantic analyzer, generator validator, and emitter must seed proof
construction from independently authenticated typed declarations. The
generator and emitter must each recompute declarations, symbol identity,
reads/writes, proof attachment, call graph, and metrics. A forged proof or
attacker-updated whole-program/profile hash cannot rescue a changed tree.

Emission is an ordinary automatic local in the reference closure of every
function that reads it, for example `const std::int32_t MAX_TAPS = 64;`.
It must never appear at namespace scope, class/State scope, function-static
scope, thread-local scope, as a captured callback, or in writable storage.
No initializer dependency exists or is newly allowed. Existing automatic-local
reference closure still materializes each exact authenticated float used by a
function alongside the new integer when applicable.

The four-mode matrix is mandatory in semantic, generator, and emitter tests:

| Counted-loop tree | Exact capability/profile | Result |
| --- | --- | --- |
| pre-proof/unproved | absent | reject |
| pre-proof/unproved | present | reject |
| exact post-proof | absent/wrong | reject |
| exact post-proof | exact six-row profile | accept |

For each accepted row, test forged declaration storage/type/literal/name/ID,
extra integer or non-profile float/global, initializer dependency/unary/binary/cast, write/update, wrong
bound ID, literalized loop bound, wrong bound kind/trips/depth/product/charge,
loop return, recursive call edge, key/source/define drift, missing/extra
capability, another program borrowing the profile, and all four caller-hash
combinations. Validator and emitter must both fail closed.

## Numeric, interfaces, resources, fetches, and stack

`glsl-f32` remains the only numeric-literal contract. The new positive integer
literals are exact `std::int32_t` values. Existing scalar/vector arithmetic,
int-to-float conversions, F32 constructor/storage/builtin boundaries, sampler
behavior, coordinate orientation, and `-ffp-contract=off` are unchanged. No
compatibility transform is present.

| Key | Exact bindings plus global | Output | Fetch accounting |
| --- | --- | --- | --- |
| Bloom | `tileOffset:vec2@1`, `fullResolution:vec2@2`, `inputTex:sampler2D@3/S1`, `radius:float@4`, `renderScale:float@5`, `taps:int@6`, `MAX_TAPS:const int@8` | `fragColor:vec4@7` | 1 static site; 1..64 dynamic |
| Directional | `inputTex:sampler2D@1/S1`, `resolution:vec2@2`, `angle:float@3`, `blurDistance:float@4`, `N:const int@6` | `fragColor:vec4@5` | 1 static; exactly 32 dynamic |
| Spin | `inputTex:sampler2D@1/S1`, `resolution:vec2@2`, `tileOffset:vec2@3`, `fullResolution:vec2@4`, `amount:float@5`, `centerX:float@6`, `centerY:float@7`, `N:const int@9` | `fragColor:vec4@8` | 1 static; exactly 32 dynamic |
| Strokes `MODE=0` | `inputTex:sampler2D@1/S1`, `resolution:vec2@2`, `tileOffset:vec2@3`, `strokeLength:float@4`, `balance:float@5`, `intensity:float@6`, `MAX_TAPS:const int@8` | `fragColor:vec4@7` | 2 resolved static sites; 29..119 dynamic for UI `strokeLength` 0..100; 21..119 for arbitrary finite F32 |
| Vaseline | `inputTex:sampler2D@1/S1`, `resolution:vec2@2`, `tileOffset:vec2@3`, `fullResolution:vec2@4`, `renderScale:float@5`, `alpha:float@6`, `TAP_COUNT:const int@8` | `fragColor:vec4@7` | 2 static; copy path 1, normal path 33 |
| Wind `METHOD=1` | `inputTex:sampler2D@1/S1`, `resolution:vec2@2`, `tileOffset:vec2@3`, `direction:int@4`, `strength:float@5`, `threshold:float@6`, `MAX_STEPS:const int@8` | `fragColor:vec4@7` | 2 static; copy path 1, normal 1..129; positive reach below 1 breaks before a candidate fetch |

Every key uses one sampler and one output, uses texture sampling, and uses no
derivatives. Strokes' 119 maximum is one main fetch, two 9-or-10-fetch brush
fields, and two 5-to-49-fetch smears in the UI domain. Its resolved `MODE=0`
`srcSample` is the plain one-fetch branch.

Relevant maximum source call chains are:

```text
Bloom:       pixel
Directional: pixel -> hash12
Spin:        pixel -> hash12 / rotateAround
Strokes:     pixel -> strokeVariation -> valueNoise2 -> hash12
             pixel -> brushStrokeField -> hash12 / hash22 / srcSample
             pixel -> smear -> srcSample
             pixel -> smear -> sprayJitter -> valueNoise2 -> hash12
               (conservative unless Release MODE=0 disassembly proves the
                jitterPx=0 branch and this chain are eliminated)
Vaseline:    pixel -> clamp01 / chebyshev_mask
Wind:        pixel -> lum
```

They are acyclic and contain no recursion, indirect/virtual calls, callbacks,
exceptions, dynamic allocation, variable-size arrays, or `alloca`. Preserve
Debug/Release/sanitizer `.su` records for `pixel` and all reachable helpers;
report each static frame and maximum non-inlined chain sum, or resolve an
inlined/missing record with Release disassembly. Any dynamic/unbounded frame,
new allocation route, recursion, missing unresolved record, or fetch count
above the table is failure. For Strokes, include the conservative
`smear -> sprayJitter -> valueNoise2 -> hash12` chain in the stack sum unless
Release disassembly for the resolved `MODE=0`, `jitterPx=0` program proves the
branch and calls absent; source-level conditional reasoning alone is not
sufficient to remove it. The automatic integer is constant-size and must not
create State or per-pixel heap storage.

## Frozen public-factory behavior

The normative `docs/port-engineering/task-23-oracles.json` contains 19
cases: three for each selected key except four for Wind, with exact dimensions,
tiles/full resolutions, F32-bit
uniform records, input and output full-F32/RGBA8 hashes, probes, metrics, finite
lane checks, input immutability, and fresh double-render identity. The compact
output hashes are in `task-23-oracle-report.md` and are incorporated by its
frozen artifact hash; neither file may be hand-edited.

Representative coverage is exact:

- Bloom: one tap/zero radius, seven tiled taps, maximum 64 taps.
- Directional: zero distance, positive angle, negative wide/portrait path.
- Spin: zero amount centered, positive tiled/off-center, negative portrait.
- Strokes: resolved MODE 0 short/low-balance, maximum-length tiled/high-
  balance, long/low-balance field selection.
- Vaseline: alpha-zero exact copy, tiled fractional render scale, alpha above
  one clamped to full blend.
- Wind: resolved METHOD 1 strength-zero early-return copy, tiny positive
  strength entering the normal path but breaking before its first candidate
  fetch, left medium/tiled, and right full-strength/maximum reach. The tiny
  positive case is byte-exact copy output and is an identity control for both
  Wind mutations.

The 12 exact source-factory mutations are bound 64->8 plus taps forced one;
bound 32->8 plus jitter disabled for Directional; bound 32->8 plus jitter
disabled for Spin; bound 24->8 plus MODE-0 selector forced to 135 degrees;
bound 32->8 plus edge mask forced zero; and bound 128->16 plus direction
forced right. Required divergent and identity cases, changed F32 lanes/RGBA8
bytes, and mutated hashes are normative in the JSON. Each native mutation test
must reproduce the intended discrimination; merely testing that a mutation
compiles is insufficient.

Full F32 equality is mandatory. RGBA8-only acceptance, tolerance comparison,
canonical-source-only comparison without public identity, stale fixture
blessing, or omission of MODE/METHOD bindings is forbidden.

## Exclusions and closed world

`filter/reindex:nmReindexStats` is explicitly excluded despite its structurally
similar two 8-trip loops. Its canonical `canonicalFactory120` text SHA-256 is
`0b59d682d882cc0f01348e950c114aaaeb4249f23094741060e482840c7200b3`,
but the public `reindexStatsFactory` text SHA-256 is
`bf9edac9f940e4f435ef55712245be8821b5893f04d68af11d32a059cd0d060f`.
The public eager-F32 adapter file `src/effects/adapters/f32-color.js` has
SHA-256 `b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046`.
It needs a separate compatibility study and cannot borrow these oracles.

Also reject all other 88 publicly unported keys and every form of `const uint`,
bool/float/vector/matrix/array/struct/sampler global newly admitted by this
task, multiple integer globals or any non-profile extra global,
mutable/uninitialized/static globals, signed/nondecimal
or expression initializers, initializer dependencies, runtime/dynamic bounds,
new loop forms or safety-cap changes, derivatives, dynamic vector indexing,
round/XOR/word-semantics work, sampler/function/resource ABI changes,
compatibility transforms, numeric modes, corpus edits, and adapters.

Existing admitted literal/expression `const float` behavior must remain byte-
identical and must not be reclassified under the new capability. Parser,
`body_semantic.py`, typed-IR dataclasses, GLSL runtime, sampler, Surface, CMake,
and corpus sources are outside scope.

## Owned files and generated isolation

After the Task 22 gate, implementation may touch only these existing source
files if required by the exact contract:

```text
tools/glslcpp/frontend/semantic.py
tools/glslcpp/frontend/loop_proof.py
tools/glslcpp/generate_typed_slice.py
tools/glslcpp/emit_typed_cpp.py
tools/glslcpp/typed_slice.json
tests/test_semantic.py
tests/test_typed_generator.py
tests/test_generated_kernels.cpp
tests/test_typed_slice.cpp
src/typed_generated/typed_slice.cpp
src/typed_generated/typed_manifest.json
include/noisemaker/generated/catalog.hpp
```

No new runtime/helper/profile source file, corpus edit, CMake edit, or unrelated
cleanup is authorized. If a required change falls outside this list, stop for
scope review instead of expanding opportunistically.

Generated isolation requires:

- raw-byte identity for accepted Task 22 program blocks 0 through 6, before
  the first new Bloom insertion;
- across all 116 accepted Task 22 blocks, byte identity after replacing only
  `typed_[0-9]+` namespace ordinals with one fixed sentinel;
- exactly the six new blocks at the positions above, with each global emitted
  only as an automatic local in its reference closure;
- no normalization of whitespace, comments, literal text, factory names,
  code, keys, manifests, headers, or any token besides namespace ordinals;
- no allocation/dispatch/recursion/global-storage construct in any new
  namespace, and exact generated binder/catalog ABI;
- only the owned files and three generated outputs differ from the accepted
  Task 22 hash inventory.

## Required verification and completion evidence

Run with fresh `/tmp` Debug, Release, and ASan/UBSan build directories, using
Ninja only if installed and otherwise Unix Makefiles, always with
`-ffp-contract=off` and `-fstack-usage -fstack-size-section`:

```sh
shasum -a 256 docs/port-engineering/task-23-frontier-audit.md \
  docs/port-engineering/task-23-oracle-generator.mjs \
  docs/port-engineering/task-23-oracles.json \
  docs/port-engineering/task-23-oracle-report.md
node docs/port-engineering/task-23-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
```

Then configure/build/CTest Debug and Release, and ASan/UBSan with leak checking
and `halt_on_error=1`; rerun every accepted Task 15-22 oracle/check command.
Extract each of the six generated namespaces and mechanically verify exact
automatic integer declarations, loop bounds, fetch sites, helper routes, and
absence of `static`, `thread_local`, allocator, callback/container, exception,
`alloca`, indirect call, or generated C++ `main`. Preserve `.su` tables and
Release disassembly evidence.

Task 23 is complete only with accepted Task 22 baseline evidence; exact frozen
artifact/source/factory/function/whole/interface/global/proof/resource/list
hashes; the full four-mode and forgery matrices passing independently in
semantic/generator/emitter; exact 122/124/88/212 counts; all 19 full-F32 and
RGBA8 native cases and all 12 mutations matching; deterministic repeat,
immutable input, finite outputs and exact copy paths; Debug/Release/ASan/UBSan
green; bounded stack/disassembly/fetch evidence; generated isolation; all
prior gates green; and an exact owned-file hash inventory.

This brief stops before design and implementation. If any identity, gate,
oracle, or bound cannot be reproduced, stop for revised independent review.
Do not fix forward by broadening globals, proof rules, runtime semantics,
compatibility behavior, corpus sources, key scope, or owned files.
