# Projected post-Task-23 remaining-frontier audit

Date: 2026-08-11  
Scope: read-only parser, typed-IR, proof, validator, emitter, pinned-corpus,
native numeric runtime, canonical-factory, and public-dispatch inspection. No
repository file or Git state was changed. This is not a Task 24 brief, oracle,
design, or implementation authorization.

## Decision

Assuming Task 23 is implemented and accepted exactly as its final frozen
six-key/profile contract, the baseline becomes:

| State | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Accepted Task 22 | 116 | 118 | 94 |
| Projected exact Task 23 | **122** | **124** | **88** |

The smallest high-confidence Task 24 slice is one key:

```text
filter/pixelSort:gatherSorted
```

Its only current blocker is one scalar `round` site. The pinned public factory
is the exact canonical factory, the native runtime already implements the
required `floor(value + 0.5)` value rule, its existing 64-trip local-constant
loop is fully proved, and a process-local diagnostic exposure validates and
emits with no later blocker. The narrow authorization should be an exact
key/source/site/profile for scalar `round` immediately consumed by `int`, not
an unrestricted promise that all future scalar/vector `round` programs are
compatible.

Conditional projection:

| State | Typed | Public | Publicly unported |
| --- | ---: | ---: | ---: |
| Exact Task 23 | 122 | 124 | 88 |
| One-key Gather Sorted Task 24 | **123** | **125** | **87** |

The projected newline-terminated typed/public sorted-list SHA-256 values are
`df7750a48a77733e50f0e20072e291c2404e761932f6df8ddbcf8793d58fb6ac`
and `bcf196794ff17ec62c1121347b3fe49a0907baa7ce3c3bd51352ec8a51fbac4e`.
The exact final insertion is zero-based position 51:

```text
filter/pixelSort:findBrightest
filter/pixelSort:gatherSorted
filter/pixelSort:luminance
```

The two-key literal-Vec3-index slice remains the best higher-throughput
alternative, but it has eleven read/write sites and adds lvalue lane semantics.
Derivatives and aggregate globals remain materially broader. A separate audit
of public dispatch found no hidden adapter on Gather Sorted, either literal-
index candidate, any of the sixteen derivative-first programs, or Smooth Edge.

## Hard boundary and authenticated inputs

Task 24 must hard-gate on final accepted Task 23, not merely this projection.
The Task 23 inputs used here are:

| Artifact | SHA-256 |
| --- | --- |
| Task 23 frontier audit | `cc49663ed312f95fc3d83cde245a95dc8719a1a90059d750ae9f7b9611061666` |
| Task 23 oracle generator | `f91ece9510c092e9c0221fc9b326522840c0b10eb3433b858eea3d786f7f57a2` |
| Task 23 oracle JSON | `a832ea550911634dbe2e98e62b51837d8fa57612243416a88f70af69f626c52d` |
| Task 23 oracle report | `8a060f2b74fcc4c7d8ed74ca315b8239a28be0475a57067f3f223667bd009303` |
| Task 23 amended brief | `8aab4f5a9274879f7061c51595bba30f29f02d9606c4f76cf0e1e7312227915f` |

The inspected repository is the accepted Task 22 state, not an implemented
Task 23 state. Its relevant hashes are:

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/parser.py` | `1b2114be2712eba63dcb8651323a9387a9f049420ef024e09c57fe8f101849cc` |
| `tools/glslcpp/frontend/typed_ir.py` | `7e16d088d7ffe90b7b6cc11dfff27d9df413ff4ffcdd13f9648fc4c35c91272c` |
| `tools/glslcpp/frontend/semantic.py` | `01c772aae5732d048c11c28b93d18d00fce63f6373ecb294324773f5e8817f2b` |
| `tools/glslcpp/frontend/body_semantic.py` | `4a6dc290c22b6a372d0837040596341a142284fccf42a0eaf7d657a78b419f59` |
| `tools/glslcpp/frontend/loop_proof.py` | `830ed013d791eb201dfbac8f1a65996b6427656a0e2c7dc953df62dd8c3cb6c8` |
| `tools/glslcpp/generate_typed_slice.py` | `b8fade4315e3bb510163c18fc51c5ddc8ab3c20af6272dcc6e9a7f78b8412562` |
| `tools/glslcpp/emit_typed_cpp.py` | `9ee63f4aa7f2b15b52d6dc5b83fc9bc7ca6e2dcaa881787a60aa5bc784647bba` |
| `tools/glslcpp/typed_slice.json` | `c6683f5eaf782c53194f90f0ec2c3dd71436fc09b4c84ac12a83b79cfe1e2dd0` |

The read-only diagnostic script is
`docs/port-engineering/task-24-projection.py`, SHA-256
`a864160c1c92f198003dbb1371d5814f268a18365d2775612f27bcc712d41409`.
It performs only in-process typed-tree/name-table projections and writes no
repository file. Final Task 23 can change the relevant frontend/emitter hashes;
therefore a Task 24 brief must rerun the full census and projections on the
accepted final Task 23 bytes rather than bless drift.

## Exact projected first-blocker census for the 88

Task 23 is profile-locked to its exact six keys. It does not generically admit
another program merely because it contains a literal integer global. Under
that closed-world result the 88 remaining first blockers are:

| First result | Count |
| --- | ---: |
| Unsupported top-level global declaration | 31 |
| Unproved counted-loop program | 19 |
| `dFdx` derivative | 11 |
| `fwidth` derivative | 5 |
| Counted loop exceeds an existing safety cap | 3 |
| Vector/component index expression | 3 |
| Scalar XOR form outside current overload | 2 |
| `round` builtin | 2 |
| Varying/stage interface | 2 |
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
| **Total** | **88** |

The loop-first set after removing Task 23's six is exactly:

```text
classicNoisedeck/effects:effects
classicNoisedeck/fractal:fractal
classicNoisedeck/noise:noise
filter/blur:blurH
filter/blur:blurV
filter/dither:dither
filter/lightLeak:lightLeak
filter/median:median
filter/normalize:statsFinal
filter/oilPaint:oilFlatten
filter/parallax:parallax
filter/reindex:nmReindexReduce
filter/reindex:nmReindexStats
filter/smooth:smoothBlend
filter/tetraColorArray:tetraColorArray
filter/zoomBlur:zoomBlur
synth/mandelbrot:mandelbrot
synth/noise:noise
synth/testPattern:testPattern
```

No remaining key becomes actually admissible from Task 23's exact profile.
A deliberately broader diagnostic literal-int macro projection reveals only
one structurally clean extra key, adapter-backed Reindex Stats; it must remain
held. The other literal-int programs expose these exact later blockers:

| Key | Literal integer shape | Next blocker |
| --- | --- | --- |
| `filter/dither:dither` | 22 enum/budget constants | still-unproved loop at `521:5` |
| `filter/lightLeak:lightLeak` | `POINT_COUNT=6` | `out` parameter at `60:50` |
| `filter/parallax:parallax` | `MARCH_STEPS=32` | `textureLod` at `24:26` |
| `filter/reindex:nmReindexReduce` | `TILE_SIZE=8`, `MAX_TILE_DIM=512` | safety charge at `32:5` |
| `filter/reindex:nmReindexStats` | `TILE_SIZE=8` | structurally clean, but public adapter |
| `synth/mandelbrot:mandelbrot` | `MAX_ITER=500` | safety charge at `226:5` |

This confirms there is no safe justification to broaden Task 23's profile or
raise loop limits as part of Task 24.

## Candidate 1: exact Gather Sorted scalar round

| Field | Exact value |
| --- | --- |
| Key | `filter/pixelSort:gatherSorted` |
| Source | `sources/filter/pixelSort/gatherSorted.glsl` |
| Raw bytes / SHA-256 | 1896 / `a45eb039bae3e7b0a5f804de68c441092b6b7826b594c4aa5221c22a6c7b1386` |
| Normalized bytes / SHA-256 | 1185 / `28e7ad80ef7db266559deb4b822f52251ab899af61feb9f915e32c0ecce079a9` |
| Defines | `{}` |
| Public/canonical factory | exact same `canonicalFactory107` object |
| Factory-text SHA-256 | `6f4021f01bc289554506215c3f01d716b4fcbf2b458527d02f1a0888d7eecb7c` |
| Adapter entry | absent |
| Functions / function-tuple SHA-256 | 1 / `6378f26aa15c43dda1ceba1d098d5b7f7fd76174618bbc5428e6659622cf8218` |
| Whole-program SHA-256 | `23120c79e838032a4ac54abeac0929d1dc2c7c89c895b083b68e6188b6f36fe3` |
| Interface SHA-256 | `f18371bad7d92151cd361663a4b56266fffa2228b7b6379ad16518d9af8a8ed6` |
| Loop proof | one local-const-literal 64-trip loop; depth/product/entry charge 1/64/64; acyclic |
| Resources | three sampler uniforms, one output, texture yes, derivatives no |
| Fetch accounting | 3 static `texelFetch` sites; 66 dynamic calls per ordinary pixel |

The sole site is function `main`, span `24:26-24:66`, builtin signature `-38`,
scalar-float rvalue with one scalar-float argument. Its argument repr SHA-256 is
`a3797427a6fd439f07e4b1a5d33f7f13edcff528e71bee77a80489ae1697761d`.
The exact tree is:

```text
int(round(brightestXNorm * float(width - 1)))
```

Bindings are exactly `preparedTex:sampler2D@1/S1`,
`rankTex:sampler2D@2/S2`, `brightestTex:sampler2D@3/S3`, and output
`fragColor:vec4@4`. There are no ordinary scalar/vector uniforms and no source
globals. The closest-rank loop retains `NUM_SAMPLES=64` as an existing local
constant; Task 24 needs no loop/global/proof change.

A process-local exposure adding only scalar `round` to the validator and
mapping it to the already-existing `glsl::round` emitted a 3,413-byte
diagnostic block, SHA-256
`3961e66b3940a929c7adb5788d503327aad7d90b690c1f7723c53f03699d503a`,
with no later validator or emitter blocker. That shape hash is diagnostic on
the accepted Task 22 emitter, not a final post-Task-23 lock.

The C++ implementation is already present:

```text
glsl::round(x) -> glsl_round(x) -> floor(x + 0.5)
```

Relevant hashes are `src/numeric.cpp`
`a45e878748db2c359511e63d9d1e116995f15ca19e623f234203056e1047b045`,
`src/glsl_runtime.cpp`
`9acbaacc5f7aa0cac10f8ee2c662122aaac11564e82d3ced6d88bb9feaab51f1`,
and public CPU `src/csl/glsl-runtime.js`
`a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072`.
Existing native tests cover positive and negative halves.

One subtlety prevents calling unrestricted `round` exposure zero-risk:
JavaScript `Math.round` preserves negative zero for inputs from `-0.5` through
negative zero, while C++ `floor(x+0.5)` yields positive zero there; JavaScript
`|0` also wraps huge results while the current native float-to-int conversion
clamps. Neither difference is observable at this site under its documented
normalized brightest-coordinate input: the result is immediately converted
to `int`, and valid values are nonnegative and surface-width bounded. A Task 24
brief should therefore authenticate the exact source/site/consumer and freeze
public-factory oracles at half-pixel boundaries. It should not claim generic
signed-zero or out-of-range round compatibility without separate runtime work.

This is still the smallest high-confidence slice because no runtime mutation
is needed and the site-specific observable behavior is exact.

## Candidate 2: literal Vec3 lane indexing

```text
classicNoisedeck/lensDistortion:lensDistortion
filter/prismaticAberration:prismaticAberration
```

Both public factories are direct canonical identities with no adapter:

| Key | Raw source SHA-256 | Factory / text SHA-256 | Exact sites |
| --- | --- | --- | ---: |
| Lens Distortion | `f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444` | `canonicalFactory10` / `151b1e868c7d2f9a446a8778d170260e5003fec540afb2623088bbf34ca8adcf` | 8 |
| Prismatic Aberration | `513eac95fdf7f67a6839ee5d96e5bbfd76b6cfa62d3254df6fed23d8effe380e` | `canonicalFactory117` / `2eab8943387658c1c28f4e089edd9b248bf441b2b77145ea137c7f979c5def02` | 3 |

All eleven bases are direct `vec3`, all indices are literal `int` lanes 0, 1,
or 2, all sites are in `main`, and there are six writes plus five reads. Lens
Distortion has four writes/four reads at lines 236, 237, 247, 248, and 260;
Prismatic Aberration has two writes/one read at lines 131-132. Grade LUT's 20
induction-indexed lanes remain excluded.

Replacing only those exact sites in memory with equivalent `x/y/z` swizzles
makes both programs validate and emit with no later blocker. Diagnostic block
hashes are Lens `6cfa9d58cbc096b7372b00b17b4ed0b146236a4738acef7870cad05593a57fc5`
and Prismatic
`8d6c98fed4ab2d2a2130566081386cdfb74d01ae84c11b198a1be08ae187155f`.

This slice is still bounded and low-medium risk, but it must prove read/write
lane range, lvalue storage rounding, compound evaluation order, symbol/base
identity, and no admission of dynamic lanes, arrays, matrices, or Grade LUT.
If selected instead, it projects **124 typed / 126 public / 86 unported** with
typed/public list hashes
`0eccc012fb39dfb42fd51a1e442390cbc41818862212009c60c38f1b101e9ea2`
and `410b3e89f58329817c48552550c63c1cb63f5ad05f2d75db1e4980e809828286`.
It unlocks two keys, but is not smaller than Gather Sorted.

## Round sibling and derivative family

`filter/posterize:posterize` has one scalar round site, but after diagnostic
round exposure it stops at `fwidth` at `80:19`. It uses derivatives and is not
part of the Gather slice.

The current derivative-first family remains 16 keys: eleven `dFdx` programs
and five `fwidth` programs listed in the Task 23 audit. Runtime public-dispatch
inspection proves all sixteen public factories are their exact canonical
factories and none has an adapter, but the C++ runtime/emitter contains no
`dFdx`, `dFdy`, or `fwidth` implementation. The apparent family grows to 17
when Posterize's earlier round blocker is removed.

Derivatives require an execution model: neighbor/quad ownership, helper-call
derivatives, tile-border samples, edges, scheduling, and consistent top-down
surface versus bottom-left fragment coordinates. They cannot be made correct
by adding builtin names. This is a high-risk architecture slice and is not a
Task 24 candidate.

## Remaining globals and newly clean programs

The 31 global-first programs retain the Task 23 audit's structural split:

- sixteen first expose read-only scalar/vector constants beyond admitted
  `const float`; only `filter/smooth:smoothEdge` becomes clean after its exact
  literal `const vec3`;
- seven use `const mat3` color transforms;
- Cell Refract and Kaleido use mutable uninitialized global `float[9]` tables;
- Historic Palette, Normal Map, OSD, Palette, and Spooky Ticker need separate
  aggregate/table lifetime and index proofs;
- `synth/shape:shape` has mutable uninitialized globals.

Task 23's exact integer profile changes none of these. Smooth Edge is a valid
one-key runner-up: raw SHA-256
`b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265`,
public/canonical direct `canonicalFactory140` text SHA-256
`732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e`,
and no adapter. It would establish aggregate automatic-local source-global
materialization and therefore has a wider lifetime/type surface than Gather's
already-implemented scalar builtin.

Public adapter inspection found four global-first holds:
`classicNoisedeck/bitEffects:bitEffects` uses `bitEffectsFactory`, Historic
Palette and Palette are adapter factories, and `filter/snow:snow` uses
`snowFactory`. They require public-adapter parity before any structural
projection can publish them.

The only newly validator/emitter-clean key under an intentionally overbroad
literal-int diagnostic is `filter/reindex:nmReindexStats`. It is not newly
public-safe: public `reindexStatsFactory` text SHA-256
`bf9edac9f940e4f435ef55712245be8821b5893f04d68af11d32a059cd0d060f`
differs from canonical `canonicalFactory120` text SHA-256
`0b59d682d882cc0f01348e950c114aaaeb4249f23094741060e482840c7200b3`.
Its eager-F32 adapter remains the decisive hold.

## Risk-adjusted comparison

| Rank | Slice | Directly unlocked | Risk | Finding |
| ---: | --- | ---: | --- | --- |
| 1 | Exact Gather Sorted scalar-round-to-int site | **1** | Low | Runtime exists; direct canonical public factory; one site; proved loop; exact consumer erases signed zero |
| 2 | Literal Vec3 lane reads/writes | **2** | Low-medium | Eleven exact in-range sites; both direct canonical; needs lvalue lane proof and F32 write checks |
| 3 | Smooth Edge exact literal `const vec3` | **1** | Medium | Structurally clean/direct canonical, but broadens source-global aggregate materialization |
| 4 | Scalar uint XOR for Perlin | **1** | Medium | Direct canonical; requires scalar word-semantics overload audit |
| 5 | Focus Blur sampler parameter ABI | **1** | Medium-high | Direct canonical but changes function/resource calling convention |
| 6 | Derivatives | 16 first-blocked, 17 exposed after round | High | Requires neighborhood execution ABI, not spelling exposure |

Reindex Stats is not ranked because its adapter compatibility remains
unresolved. No loop-cap increase, generic global broadening, derivative name
exposure, or multi-family bundle is justified.

## Stop boundary

Recommended next action, only after final Task 23 acceptance, is a dedicated
Gather Sorted public-factory oracle and exact scope/proof brief. That work must
freeze normalized/source/factory/function/whole/interface identities, the one
round tree and int consumer, normalized-coordinate domain and half-boundary
cases, all three samplers, 64-loop/66-fetch accounting, full-F32 and RGBA8
outputs, mutation sensitivity, stack/code shape, and a negative control showing
Posterize remains held by `fwidth`.

This audit stops before that oracle/brief and before design or implementation.
If accepted Task 23 changes the projected census or if public oracles expose a
signed-zero, conversion, sampler, orientation, or loop discrepancy, stop and
rerank rather than broadening the round/runtime contract.
