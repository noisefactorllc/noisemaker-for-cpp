# Post-Task-28 mechanical frontier precompute

Date: 2026-08-11  
Scope: read-only preparation from the accepted post-Task-27 tree. No repository
file or Git state was changed. Task 28 Rotate is intentionally not redesigned
here. All reusable output is confined to this directory.

## Starting state

The captured starting point is exactly **127 typed / 129 public / 83 publicly
unported**, with sorted typed-key SHA-256
`ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72`.
The corpus revision is
`a024dc3a960cc44af454abc7aebce50456c194e6`.

## Ranked recommendation

### 1. Focus Blur borrowed sampler parameters

After Task 28 Rotate, the strongest next one-key mechanical slice is exactly:

```text
mixer/focusBlur:focusBlur
```

The current validator passes it unchanged. The current emitter fails only
because a helper parameter cannot spell `sampler2D`. A diagnostic projection
mapping helper samplers to `const Surface&` renders and compiles as C++20 with
`-Wall -Wextra -Werror`; no later validator or emitter blocker appears.

Exact source and typed identity:

| Field | Value |
| --- | --- |
| Raw bytes / SHA-256 | 2,268 / `dff787c7de67122abe60ac14f0fc8995e8087fc4549626e6fe678d8f86b3d7d1` |
| Normalized bytes / SHA-256 | 1,685 / `8b3cfb07882d0e409f617b2f86b02fa54cd36db213a60881370306306306be9f` |
| Defines | `{}` |
| Whole program SHA-256 | `96468ba160d253f7d064c2caccd9db686d772a2af94d13ee836996dc488e037b` |
| Interface SHA-256 | `3158dcf83a1d13f84a2d8f3d374d464230ff24b1ed812603cc02fbc96e56be96` |
| Function tuple SHA-256 | `95428219c60cd14910f90e572857773e22818bfaf17436f6a249a10b4364c6e3` |
| Public identity | exact `canonicalFactory195`; no adapter |
| Factory text SHA-256 | `fb4c02c763ef42000b13bba3945cf4fd15e177a2ab2827372ce3b96aa3a778ff` |

The sole new signature is normalized function ID 16:

```text
vec4 applyFocusBlur(in sampler2D sceneTex,
                    in sampler2D depthTex,
                    in vec2 uv)
```

Its complete typed-function SHA-256 is
`fd9a2496e322b3b035258d1532ac4dd37c79f778a5c53c55a1231cfad24e00bb`.
`main` owns exactly two calls:

```text
57:17-57:50  applyFocusBlur(tex, inputTex, uv)
59:17-59:50  applyFocusBlur(inputTex, tex, uv)
```

The interface is `inputTex:sampler2D@1`, `tex:sampler2D@2`,
`resolution:vec2@3`, `tileOffset:vec2@4`, `fullResolution:vec2@5`,
`focalDistance:float@6`, `aperture:float@7`, `sampleBias:float@8`,
`depthSource:int@9`, and `fragColor:vec4@10/out`. The two sampler parameters
are read only and never returned, retained, assigned, indexed, or placed in an
aggregate. Both call arguments resolve directly to the two setup-owned
uniform surfaces. The same-surface case is valid aliasing: two const borrows,
not ownership transfer.

Its one counted loop is already proved: 64 trips, depth 1, lexical product 64,
entrypoint charge 64, acyclic graph. The maximum path performs exactly 67
texture reads per pixel: one depth sample, 64 scene samples, then two alpha
samples. It has no derivative, array, matrix, global, UBO, varying, output
parameter, nonempty define, adapter, or second output.

Suggested closed contract: authenticate only the two exact parameters and two
call sites, emit them as `const Surface&`, preserve argument order and aliasing,
and forbid nullable pointers, writable borrows, retention, sampler return,
sampler arrays/aggregates, arbitrary helper sampler signatures, new resource
lookup, or lifetime extension. The generated helper remains `noexcept`; state
continues to own only setup-time pointers supplied by existing bindings.

Reusable oracle material is already frozen: six canonical cases distinguish
both call permutations, metadata extrema, non-square/tiled geometry,
asymmetric alpha, and an exact same-Surface alias case. Every case has repeat
identity plus full F32/RGBA8 hashes and five pixel probes. The depth-source
pair is explicitly output-discriminating.

### 2. Builtin/value candidates: do not batch yet

No safe multi-key uniform builtin batch exists at the captured frontier. Each
candidate reveals an independent later blocker when only its first builtin is
temporarily admitted:

| Candidate | First gate | Next exact gate | Disposition |
| --- | --- | --- | --- |
| `filter/lighting:lighting` | one `reflect(vec3,vec3)->vec3` | local `float[9]` declaration in the normal filter | Good later singleton only after a separately authenticated 9-lane local table; do not call it builtin-only |
| `classicNoisedeck/caustic:caustic` | one `floatBitsToUint(float)->uint` | scalar `uint ^ uint` expressions | Good later word-semantics singleton; not a pure bit-conversion task |
| `filter/extrude:extrude` | two `all(bvec2)->bool` | `bvec2` plus two `lessThanEqual(vec2,vec2)` sites | Viable boolean-vector family, but exact to Extrude |
| `filter/waves:waves` | two `any(bvec2)->bool` | `bvec2` plus two `notEqual(vec2,vec2)` sites, then derivatives | Exclude until derivative ABI; cannot safely batch with Extrude now |
| `synth/curl:curl` | one `tanh(vec3)->vec3` | `mod(vec3,float)` and `mod(vec4,float)` overloads | Treat as one exact Curl vector-math closure, not generic tanh |
| `filter/posterize:posterize` | one scalar `round` | one `fwidth(vec3)` | Exclude until derivative ABI |
| `filter/watercolor:wcSimplify` | two `inout vec3` parameters | 19 call statements need copy-in/copy-out and alias rules | Later value-reference ABI task; materially broader than Focus Blur |

The safest eventual numeric/value work is therefore ranked:

1. Focus Blur exact read-only sampler borrow ABI now.
2. Lighting only after its exact fixed local array is designed together with
   the one reflect site.
3. Caustic only as a combined typed word closure, with exact float-bit ingress
   and scalar XOR semantics.
4. Extrude as a single-key `bvec2` relational/reduction closure.
5. Curl as a single-key vector `mod` plus `tanh` closure.

There is no support for a Reflect + FloatBitsToUint batch: they share neither
types, semantics, runtime helpers, source shape, nor downstream blocker. There
is likewise no honest All + Any batch while Waves still requires derivatives.

## Probe and fixture inventory

| Artifact | Purpose | SHA-256 |
| --- | --- | --- |
| `analyze_candidates.py` | Recomputes exact typed inventory and first/next validator-emitter gates | `08f947e29029b97db0b779e4cf756854f0249ab04f71671cae0e167983651407` |
| `candidate-analysis.json` | Full declarations, functions, hashes, resources, calls, builtins, loop proofs, and probe results for eight candidates | `2689474ab24220e735f2c5d7669274bfa415c1c207ab9dbf215b9a776a64204a` |
| `focus-blur-borrowed-sampler-projection.cpp` | Diagnostic current-emitter projection using `const Surface&`; compile-checked only | `26fe46738b1591c443f6a3f05fea5150b1d2f7e1341fa3ab7d3f3e578caefcca` |
| `focus_blur_oracle_generator.mjs` | Hermetic pinned public/canonical oracle generator with `--check` | `9c1a4acffaa1bef021953aa3df0313b8fbe7fb88aea635237e4131dce4c39897` |
| `focus-blur-oracles.json` | Six reusable canonical parity cases | `44595fc5d8f98f44587c95137136c5d10993d427ba7e7e88e353f2bcffc11f74` |
| `public_identity_fixture.mjs` | Recomputes public/canonical identity for all eight candidates | `1967b35cff6e3d1de75ffa4705da1261b8287499b7f35e594f1942377095e458` |
| `public-identities.json` | Pinned factory names/text hashes and adapter absence | `118d3812ce851e21d9bb60ee4083069fcfe401558c6463d950f7c091a8dbdbc6` |

Verification performed:

```text
python3 analyze_candidates.py                                      PASS
node focus_blur_oracle_generator.mjs --check                      PASS (6 cases)
node public_identity_fixture.mjs --check                          PASS (8 candidates)
clang++ -std=c++20 -Wall -Wextra -Werror -Iinclude -fsyntax-only
  focus-blur-borrowed-sampler-projection.cpp                       PASS
```

The projection and temporary capability mappings are diagnostic only. They
must not be copied into production as generic `_TYPES`/builtin additions; a
real task needs key/profile authentication in both validator and emitter,
strict TDD, native parity, ABI/stack/disassembly gates, and independent review.
