# Post-Task-27 independent frontier check

Date: 2026-08-11  
Repository: `.`  
Scope: read-only recomputation from the current pinned corpus, typed allowlist,
semantic frontend, validator, emitter, and native value/resource types. No
repository file or Git state was changed.

## Decision

The current accepted state is internally consistent:

| Measure | Fresh value |
| --- | ---: |
| Typed factories | **127** |
| Public factories | **129** |
| Publicly unported corpus keys | **83** |
| Typed sorted-list SHA-256 | `ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72` |
| Public sorted-list SHA-256 | `37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883` |

There is **no challenge to selecting Rotate for Task 28**. It is the only
remaining key whose validator gate is narrower than its already-working
emitter/runtime representation. A fresh emitter probe renders the unmodified
typed program successfully; no diagnostic AST rewrite is required.

No multi-key batch is both genuinely uniform and lower-risk than Rotate.
In particular, broadening scalar/vector source constants alone unlocks zero
of the 83 remaining keys. The apparent six-key Grade cohort is not one
frontier in the current state: LUT needs dynamic `vec3[i]`, while the other
five need both that indexing proof and a new vector-global lowering.

## Fresh first-result census

| Current first validator result | Count |
| --- | ---: |
| Unsupported top-level global declaration | 30 |
| Unproved counted-loop program | 19 |
| `dFdx` | 11 |
| `fwidth` | 5 |
| Counted-loop safety cap | 3 |
| Varying/stage input | 2 |
| Validator pass (Focus Blur; emitter fails) | 1 |
| Dynamic `vec3[i]` | 1 |
| Scalar signed XOR | 1 |
| Scalar `round` | 1 |
| `all` | 1 |
| `any` | 1 |
| `floatBitsToUint` | 1 |
| `reflect` | 1 |
| `tanh` | 1 |
| Matrix return ABI | 1 |
| `inout` parameter ABI | 1 |
| `mat4` | 1 |
| Uniform block | 1 |
| **Total** | **83** |

Validator and emitter were called independently on all 83 current typed
programs. Their important divergences are real boundaries, not census noise:
Rotate fails only validator matrix-return policy while emission passes; Focus
Blur passes validation but cannot spell a helper `sampler2D` parameter.

## Ranked next five closed slices

| Rank | Exact slice | Unlock | Risk | Current first blocker and downstream result |
| ---: | --- | ---: | --- | --- |
| **1** | `filter/rotate:rot`: exact `mat2 rotate2D(float)` value return | 1 | Medium | Validator rejects matrix return at normalized `14:1`; current emitter passes and emits the existing four-scalar `glsl::Mat2` constructor, by-value call, and existing `Mat2 * Vec2`. No loop, derivative, aggregate, stage, or resource-call ABI follows. |
| **2** | `filter/extrude:extrude`: exactly two `lessThanEqual(vec2,vec2)->bvec2` plus two enclosing `all(bvec2)->bool` sites | 1 | Medium | Validator first stops at `all`; emitter first stops at `lessThanEqual`. Replacing only the two complete reduction subtrees with diagnostic bool literals makes both validator and emitter pass. This is local automatic value computation, but the large 90-charge renderer requires serious native oracle coverage. |
| **3** | `mixer/focusBlur:focusBlur`: exact two read-only sampler helper parameters and two reversed direct calls | 1 | Medium-high | Validator passes. Emitter rejects helper `sampler2D`; a temporary type-map probe to `const Surface&` renders cleanly, including `*state.tex,*state.inputTex` and the reversed order. No later typed/emitter blocker exists, but aliasing, lifetime, 64-trip/67-read caps, and borrowed-resource ABI must be authenticated. |
| **4** | `filter/watercolor:wcSimplify`: exact `void sort2(inout vec3,inout vec3)` and 19 non-aliasing direct-local calls | 1 | Medium-high | Validator rejects parameter direction. The body is otherwise ordinary min/max/assignment and nine texture reads. A key-locked `Vec3&` lowering is closed, but it establishes mutation/copy-out and argument-alias rules, so it is broader than Rotate or Extrude. |
| **5** | `synth/curl:curl`: exact `tanh(vec3)` plus scalar-divisor vector `mod` closure | 1 | Medium-high | Validator first stops at `tanh`; bypassing only `tanh` exposes `mod(vec3,float)`. Fresh traversal finds **three**, not two, vector-mod calls: two `vec3,float` sites and one `vec4,float` site, plus one `tanh(vec3)`. No derivative/resource/aggregate boundary follows under exact defaults, but numeric overload and f32/NaN/saturation proof is larger than ranks 1-4. |

The top five ranking favors a closed capability with no hidden second gate.
Ranks 2 and 3 are close: Focus Blur is smaller source text, while Extrude is
safer in representation because it adds no borrowing or resource-call ABI.
Neither is lower-risk than Rotate.

## Required special scrutiny

### Rotate matrix return

- Raw source: 1,197 bytes, SHA-256
  `c23e8462e8240f25a715fa3eb05e567269c8d410d27943ba346ebccdd0de1f8f`.
- Exact defaults: `{}`; zero loops; one sampler uniform; no derivatives.
- The only helper is `mat2 rotate2D(float)`, with locals `c`, `s`, return
  `mat2(c,-s,s,c)`, and one immediate `rotate2D(...) * uv` use.
- Fresh unmodified emission: 3,798 bytes, SHA-256
  `5adc3594227b95105351b4210a8dcba0becea69593b6f02ba70097abddf9a851`.
- `TAU` is an already-admitted source `const float`; it is not a second global
  blocker. The Task 28 profile should remain one key, one signature, one call,
  exact constructor order, no matrix parameter/storage/index/generalization.

### Focus Blur sampler helper ABI

- Raw source: 2,268 bytes, SHA-256
  `dff787c7de67122abe60ac14f0fc8995e8087fc4549626e6fe678d8f86b3d7d1`.
- Exact helper: `vec4 applyFocusBlur(sampler2D sceneTex, sampler2D depthTex,
  vec2 uv)`; calls are exactly `(tex,inputTex,uv)` and
  `(inputTex,tex,uv)`.
- Counted proof is one 64-trip loop, depth 1, entrypoint charge 64. The maximum
  selected path is one depth read + 64 scene reads + two alpha reads.
- Temporarily adding only emitter spelling `sampler2D -> const Surface&`
  produced a 6,059-byte block, SHA-256
  `4736a114d2d2edac0345468bdb8b3570b3a6d1a9e089a6ea6637ce2e989511b5`,
  with direct dereferenced state pointers in both orders. This is evidence of
  no later emitter blocker, not implementation authorization or compile proof.

### Singleton `all`, `any`, `reflect`, and `tanh`

- **`all`:** Extrude contains exactly two `all(bvec2)` calls, each owning one
  `lessThanEqual(vec2,vec2)`. Diagnostic removal of only those two complete
  trees makes validator and emitter pass. The runtime already represents
  `BVec2`, but has no admitted relational/reduction helper. This is a closed
  exact slice and ranks second.
- **`any`:** Waves contains exactly two `any(bvec2)` calls, each owning one
  `notEqual(vec2,vec2)`. Removing only those trees immediately exposes
  `dFdx` at normalized line 70, and the resource record confirms derivatives.
  It is not a safe standalone builtin slice before a real derivative ABI.
- **`reflect`:** Lighting has exactly one `reflect(vec3,vec3)` and the runtime
  already implements the vector formula. Removing only that call exposes a
  helper-local `float[9]` at normalized `40:11`: the helper owns two
  `float[9]` Sobel tables and one `vec2[9]` offset table, then indexes all
  three in a 9-trip loop. Current fixed-nine proofs are key/owner locked to
  other programs. Therefore reflect alone unlocks nothing; a combined
  reflect + helper-local-table profile is larger than the ranked five.
- **`tanh`:** Curl has one `tanh(vec3)`, but removing it exposes unsupported
  vector `mod`. The exact closure is two `mod(vec3,float)` calls and one
  `mod(vec4,float)` call. It is bounded under defaults
  `{OCTAVES:1,OUTPUT_MODE:3,RIDGES:true}`, but is not a singleton admission.

### Scalar/vector constant globals

The current validator already admits immutable scalar `const float` globals.
Among the 30 global-first keys, exactly 15 otherwise use only read-only
`int`/`uint`/`float`/`vec3` global constants rather than matrix/array/mutable
global forms. An in-memory projection that changes only those declarations to
an already-emittable interface storage class unlocks **zero** keys. The next
results are:

| Next boundary after scalar/vector globals | Keys |
| --- | ---: |
| Dynamic Grade `vec3[i]` | 5 |
| Scalar `round` | 3 |
| Signed scalar `&` | 2 |
| Varying/stage input | 2 |
| `bvec3`/relational contour path | 1 |
| Helper-local fixed arrays | 1 |
| `floatBitsToUint` | 1 |

This excludes `synth/shape:shape`, whose uninitialized mutable globals remain
unsafe, and all matrix/array/struct global cohorts. A broad constant-global
task would be infrastructure-only at this point and is not lower-risk or more
useful than Rotate. The six Grade programs are a plausible later throughput
slice only after separately specifying both vector-global localization and
range-proved dynamic local/parameter `vec3[i]` reads/writes.

## Verification boundary

The independent probe parsed and semantically analyzed every remaining key
using authoritative metadata defaults and corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`. It independently exercised the
current validator and emitter, traversed exact named builtin/call sites,
performed single-boundary diagnostic bypasses for downstream discovery, and
reconstructed typed/public sorted-list hashes. Diagnostic substitutions were
in memory only and are not proposed lowering semantics.

Recommendation: proceed with Rotate alone for Task 28. Do not bundle Focus
Blur, Extrude, parameter directions, globals, relational reductions, Curl
math, derivatives, or any matrix form beyond the exact returned `mat2`.
