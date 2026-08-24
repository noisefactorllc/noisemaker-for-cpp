# Task30 precompute: exact Extrude bvec2 relational/reduction closure

Date: 2026-08-12  
Scope: read-only analysis of the accepted post-Task28 repository and pinned CPU
oracle. No repository or Git state was changed; this is a reusable handoff,
not implementation authorization.

## Decision

Select exactly:

```text
filter/extrude:extrude
```

under proposed identity profile
`extrude-bvec2-relational-reduction-v1`. Do not batch it with Watercolor,
Curl, Caustic, or another relational program.

The accepted starting point is **128 typed / 130 public / 82 publicly
unported**, with newline-terminated sorted typed/public key hashes
`30f0333cfd995ba1b866fcbd9589507151255204088675bae6575e42d7328c55`
and `102f5436a5416399f2601879c7d5219706111bc64b93989acbb67d973a01b6c5`.
Adding only Extrude projects **129 / 131 / 81** with hashes
`18f59e720d95b663a27c5d18621d05ef4e0655c6f55c2691ea60a57d649adbe6`
and `2e07968c2030d272fee448a3f18f0b9c70320959e8df5fceb2a6ea2e0d1ad370`.
Extrude is zero-based typed ordinal 25, between Directional Blur and Fibers.

A fresh pass over all 84 corpus keys absent from the typed spec finds no newly
exposed public program that passes both current validator and emitter. The only
non-manual validator pass is Focus Blur, whose sampler-parameter emitter gap is
the in-flight Task29 target. Extrude is therefore the best post-Focus-Blur
singleton, not a skipped zero-change port.

## Exact target identity

| Field | Frozen value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Source | `sources/filter/extrude/extrude.glsl` |
| Raw bytes / SHA-256 | 16,945 / `3be128643867dc78184bd209306cbe524538fd8d6d53a21817fb87f746100e29` |
| Normalized bytes / SHA-256 | 5,020 / `823698d954e1f2f890414a22e6792ca0ca87484ee21d9043cd3c1a347fd7a4ac` |
| Exact defines | `{"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0}` |
| Numeric contract | `glsl-f32` |
| Function count / tuple SHA-256 | 9 / `cb662c33d7dda0b59a63de9d9ff5e5672e18e137ad43f18f2aa1855cf29e4bb0` |
| Whole-program SHA-256 | `1e02d72c7b5c61d49462310fbbcd9f1816d0440f8716bdaaace7c2396ceb36e3` |
| Interface SHA-256 | `0e8079c94619fc0e8ad85b401a1bd51211f504c933fa963dbf9c7cdbfaec9fe7` |
| Canonical/public factory | exact same `canonicalFactory51`; no adapter |
| Factory text SHA-256 | `7d5cdd050eaa13282060557e7d6a097ef8300c1b71f31c13d782680eb58d91ef` |

The ordered runtime interface is `inputTex:sampler2D@1`, `resolution:vec2@2`,
`tileOffset:vec2@3`, `fullResolution:vec2@4`, `size:float@5`, `depth:float@6`,
`solidFront:bool@7`, and `fragColor:vec4@8/out`. The normalized default
program has one sampler and output, no derivatives, no non-`in` parameters,
and no arrays, matrices, structs, UBOs, or varyings.

All three counted loops are already proved: effective depth 3, maximum lexical
product 9, entrypoint charge 90, and acyclic call graph. The profile adds no
loop or resource authorization.

## Exact four-node closure

The only new semantic family is two immediate
`all(lessThanEqual(vec2, vec2))` trees in `main` function ID 36:

| Site | Path | Span | Type | SHA-256 |
| --- | --- | --- | --- | --- |
| top `all` | `(12,'s1','s8','e0',0,0)` | `159:23-159:72` | `bvec2 -> bool` | `38eea107e78da89e0f6dd529d77520ccbea907e980df5e0bbc1f01099e8c4efb` |
| top `lessThanEqual` | `(12,'s1','s8','e0',0,0,0)` | `159:27-159:71` | `vec2,vec2 -> bvec2` | `3048bc23943a393e84d677ebdf15bfc97a942a43635bb8dd95227a594a1ad9e1` |
| side `all` | `(12,'s1','s9','e0',0,0,1)` | `160:37-160:81` | `bvec2 -> bool` | `51877b40b69819a50d527eef19e642e612a9027fcdb58698e707c0818825b2bf` |
| side `lessThanEqual` | `(12,'s1','s9','e0',0,0,1,0)` | `160:41-160:80` | `vec2,vec2 -> bvec2` | `546f5c52a1a44cc20b6dda2b3fd66a38e8b6bc2f68adc2287fcfc8843d771e04` |

The first result is assigned to local `topHit`. The second is the right side
of short-circuit `(!topHit) && ...` and assigned to local `sideHit`. Each
`bvec2` is consumed immediately by its exact parent `all`; there is no bvec
declaration, parameter, return, assignment, subscript, storage, or escape.

The frozen profile tuple in `analysis.json` has SHA-256
`9a55812e72a99cecb514a188a3185ccc0308ab405dd9221ed8489b114ebb4ecb`.
Caller-supplied hashes must remain drift alarms rather than authority.

Current blockers are complementary: validator first rejects `all`; emitter
first rejects `lessThanEqual`. A diagnostic emitter-only projection mapping
exactly `bvec2 -> glsl::BVec2`, `lessThanEqual`, and `all` renders the whole
program successfully (14,330 bytes, SHA-256
`27e05cfa714eeba2d0e15429792f53d490a2a8283e76bb73a2484135c5b29c08`).
The generic validator still rejects `bvec2`, proving implementation needs an
identity-scoped type visit in addition to builtin admission. No later emitter
blocker exists.

Recommended implementation is exact-profile authentication in validator and
emitter independently, plus narrowly spelled lane-wise comparison and
reduction. Do not add generic `bvec2`, relational, or reduction capabilities;
do not authorize `any`, other comparison operators, widths 3/4, scalar/vector
mixing, or stored boolean vectors.

## Hermetic oracle

`extrude_oracle_generator.mjs` pins the CPU runtime/catalog/adapter/source and
exact public/canonical identity, then freezes six repeat-identical immutable
input cases with finite full F32 and RGBA8 hashes and five probes. The exact
default define case alone discriminates all four value mutations; the extra
block/random/pyramid cases are reusable public-source sensitivity evidence,
not authorization for non-default native profiles.

Four mutated public factories replace one exact site at a time: top/side
`all -> any` and top/side `lessThanEqual -> lessThan`. They diverge in 3/6,
2/6, 4/6, and 2/6 cases respectively. Seven direct rows freeze both input
lane bit patterns, two comparison lanes, `all`, `any`, and strict-less
controls. Mixed-lane rows distinguish `all` from `any`; equality rows
distinguish `<=` from `<`.

Native tests should execute the seven direct rows with explicit mode IDs and
names, reject invalid modes, and Python should parse/transcribe every case,
probe, mode, and lane plus tamper each independently. This avoids the vacuous
mutation-harness failure class previously found in Smooth Edge.

## Why no batch

| Candidate | Exact next closure | Reason to keep separate |
| --- | --- | --- |
| Watercolor Simplify | two `inout vec3` parameters, 19 `sort2` calls, copy-in/copy-out | Requires reference/value ABI, aliasing and evaluation-order proof; current emitter also rejects its call statements. |
| Curl | one `tanh(vec3)`, three `mod(vec3/vec4,float)` sites | Distinct transcendental and vector-mod F32 semantics; current first-gate projection still fails on vector `mod`. |
| Caustic | one `floatBitsToUint`, four scalar `uint ^ uint` sites | Requires bit reinterpretation plus live scalar-word semantics across 22 functions; first-gate projection still fails on XOR. |

None shares Extrude's boolean-vector representation or relational/reduction
semantics. Batching would make review, negative closure, and pixel attribution
weaker without reducing a shared runtime change.

## Reusable artifacts and verification

Run from this directory:

```text
python3 analyze_task30.py
node extrude_oracle_generator.mjs --check
```

Both passed against the accepted post-Task28 tree and pinned CPU checkout.
`analysis.json` contains the fresh full 84-key census and exact candidate
trees. `extrude-oracles.json` is the frozen pixel/direct fixture.

