# Task 22 CRT frontier and risk audit

Date: 2026-08-10  
Scope: read-only inspection of the accepted Task 20 repository state, the
projected post-Degauss 115/117/95 state, the pinned corpus, and the public
Noisemaker CPU implementation. No repository file or Git state was changed.

## Decision

`filter/crt:crt` needs **no new GLSL language capability, proof kind, type,
operator, builtin name, resource ABI, loop rule, or stack-owning array form**.
The current Task 20 validator accepts its typed IR, and the current emitter
renders a 54,665-byte C++ body entirely with the existing vocabulary.

It does, however, need a new key/source-locked **runtime semantic compatibility
contract**. The public CPU dispatch is not `canonicalFactory44`; it is the
hand-written `crtFactory` adapter, whose sole purpose is to replace `sin` with
float32 turn reduction matching Metal fast-math. Calling the raw canonical
factory is observably wrong in every normal-path oracle case. Therefore the
smallest honest Task 22 is one key plus a contract such as:

```text
crt-metal-sine-v1
  filter/crt:crt
```

If Task 22 cannot add that exact compatibility seam, CRT should remain
unported. Treating it as an ordinary no-transform addition would freeze the
wrong reference behavior.

| Projected state | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Accepted Task 20 | 114 | 116 | 96 |
| Projected after Task 21 Degauss | 115 | 117 | 95 |
| Projected after compatible Task 22 CRT | **116** | **118** | **94** |

## Exact provenance and typed shape

| Field | Value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Source | `sources/filter/crt/crt.glsl` |
| Raw source | 19,560 bytes; SHA-256 `62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c` |
| Normalized source | SHA-256 `acd1c3f05c6d02052592aeb46bbbc49d23e18f4e83530498687903e00b4623fe` |
| Canonical generated runtime | SHA-256 `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Canonical factory | `canonicalFactory44`; `toString()` SHA-256 `6d65f4984f8749ca7cdfec976e082662d3a7ad614aabb15ce8a168fca7d8e303` |
| Public adapter file | `src/effects/adapters/crt.js`; SHA-256 `c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc` |
| Adapter factory | `crtFactory`; `toString()` SHA-256 `240972f95f908452bf87fc681e360553759f374fa81613adc415a5a7c5eb4bf7` |
| Function tuple fingerprint | `f6ab50374732b058fa2a5cd33e87bbe35654682b7125593d7451871194b2ba72` |
| Whole-program fingerprint | `f70fc78da6c3579fa3237fbbfa3712229b88f0a93b8d556181f9bad2ed74b6fc` |
| Interface fingerprint | `9336d2b596c0efd955af699a27c788938c99d0e1e5c6438f66054e15fc135490` |

The typed program has 35 functions, no loops, an acyclic call graph, no
arrays, structs, matrices, derivatives, blocks, varyings, parameter directions,
or nonzero LOD. Counted-loop proof is exactly zero loops, zero unproved loops,
zero depth/product/charge, and acyclic. All Task 17 through Task 20 fixed-array
proof fields are absent, as required.

The exact declaration/resource surface is:

```text
PI:const float@1
TAU:const float@2
INV_THREE:const float@3
inputTex:sampler2D@4/S1
resolution:vec2@5
tileOffset:vec2@6
fullResolution:vec2@7
time:float@8
speed:float@9
seed:int@10
alpha:float@11
renderScale:float@12
fragColor:vec4@88
```

The authoritative route is `inputTex <- inputTex`, `fragColor -> outputTex`,
with identity aliases for `alpha`, `speed`, and `seed`. Defaults are alpha
`0.5f`, speed `1.0f`, seed `1`; renderScale is a runtime binding with canonical
default `1.0f`, not a public effect parameter.

## The actual blocker: public CRT sine semantics

The adapter computes:

```text
turns = f32(value * f32(1 / TAU))
phase = turns - floor(turns)
result = f32(sin(phase * f32(TAU)))
```

and installs that operation as CRT's scalar/vector `sin`. The source has six
scalar `sin` sites: one in `random_scalar`, two in the currently unreachable
`simplex_random`, one in `normalized_sine`, one in `compute_lens_offsets`, and
one in `hash3`. The compatibility contract should authenticate all six; it
must not silently become a global `glsl::sin` change or affect `cos`.

The oracle's `public-metal-sine-disabled` mutation calls the raw pinned factory.
It matches the two alpha-clamped exact-copy cases, but differs in every one of
the nine normal cases:

| Case | Different F32 lanes | Different RGBA8 bytes | Max absolute lane difference |
| --- | ---: | ---: | ---: |
| default | 316 | 233 | 0.371674 |
| alpha above one | 335 | 316 | 0.748976 |
| landscape tiled | 341 | 324 | 0.378983 |
| portrait tiled | 342 | 324 | 0.436117 |
| speed zero | 321 | 220 | 0.500073 |
| time zero | 320 | 297 | 0.415866 |
| full-resolution fallback | 334 | 314 | 0.472263 |
| square / large time | 351 | 349 | 0.290496 |
| renderScale below one | 328 | 318 | 0.303180 |

This is not a theoretical ULP concern. The public adapter changes visible
pixels substantially. A Task 22 implementation should either emit a dedicated
CRT-only sine helper for the six authenticated calls, or apply an equivalently
narrow typed compatibility mode. The validator and emitter must independently
recount/re-authenticate the sites and source identity. A general runtime sine
change would alter many accepted programs and is out of scope.

## Alias, ordering, and F32 risks

The source deliberately shadows three bindings in `main`:

| Binding | Local | Meaning |
| --- | --- | --- |
| `time@8` | `time@193` | exact local copy used by lens and scanline paths |
| `speed@9` | `speed@194` | exact local copy used by lens and scanline paths |
| `alpha@11` | `alpha@205` | input pixel alpha; currently dead after declaration |

The generated JS factory renames the three locals to `_local_time_1`,
`_local_speed_1`, and `_local_alpha_1`. The current C++ emitter already keeps
the uniforms in `state` and emits the first two locals as `time_193` and
`speed_194`; the local input alpha does not replace `state.alpha`. This is an
existing symbol-identity behavior, not a new capability. The oracle perturbs
each live local copy and separately writes uniform alpha instead of input alpha.
Those mutations diverge as required.

Ordering must remain source/canonical order for:

- scanline construction and base sample;
- red, green, then blue channel assembly;
- per-channel positive hue adjustment followed by whole-color negative hue
  restoration;
- saturation, vignette, local-mean contrast, then uniform-alpha mix;
- red/blue global-to-local x conversion using raw `renderScale`, while pattern
  dimensions use `rs=max(renderScale,1)`.

Counted mutations cover each chain. An inserted eager F32 boundary at the
local RGB mean changes up to 37 F32 lanes across normal cases while changing
zero RGBA8 bytes. Native acceptance therefore must compare complete F32 bytes,
not only RGBA8 hashes. Literal mode remains `glsl-f32`; there is no
`source-double` exception.

## Resource and coordinate audit

There is one sampler and one output. Alpha clamped to zero performs one
level-zero `texelFetch` and returns an exact F32 copy. The normal path performs
exactly three level-zero fetches per pixel: base, red, and blue. No helper
function fetches a texture. The scanline "bilinear" helper is procedural and
does not sample a resource.

The red/blue coordinates intentionally follow this order:

```text
scaled x = (global_id.x + tileOffset.x) / max(renderScale, 1)
sample global x = displaced scaled x * raw renderScale
sample local x = sample global x - tileOffset.x
integer texelFetch x = trunc(sample local x)
```

Both JS and C++ sampler runtimes clamp integer fetch coordinates and convert
bottom-left shader y to top-down storage. The tiled and fractional-renderScale
cases plus independent red/blue tile-subtraction mutations exercise this
contract. No new sampler ABI or texture resource is justified.

For normal renderer-controlled dimensions, integer coordinates remain in the
existing sampler domain. As with other typed programs, hostile direct bindings
large enough to overflow a C++ `int32_t` conversion are outside the frozen
oracle domain and should not be used to broaden Task 22.

## Stack and call-graph audit

The deepest live source chain is bounded and acyclic (for example
`main -> compute_lens_offsets -> animated_simplex_value -> simplex_noise ->
permute -> mod289_vec4`). There are no loops, recursive calls, local arrays,
tables, dynamic allocation requests, or size-dependent stack objects. Local
state consists only of scalar and `Vec2`/`Vec3`/`Vec4` values. `simplex_random`
and `clamp_index` are source functions but currently unreachable; they should
remain parsed/emitted and fingerprinted rather than deleted specially.

Consequently CRT adds code volume and arithmetic work, but no new stack-safety
proof. The existing acyclic call-graph check is sufficient.

## Required scope boundary for a later brief

A later Task 22 implementation brief may authorize only:

1. the single sorted key `filter/crt:crt` with empty defines;
2. the exact source/factory/interface/function/whole-program identities above;
3. one exact CRT-only reduced-turn-sine compatibility contract covering all
   six scalar source sites;
4. existing `glsl-f32` literals and existing language/resource vocabulary;
5. the 11 public-adapter oracle cases and all 18 mutation controls in the
   frozen JSON;
6. projected counts 116 typed / 118 public / 94 unported.

It should explicitly forbid global sine changes, new numeric-literal modes,
new capabilities/proofs, source cleanup/DCE, sampler changes, unrelated keys,
and treating raw `canonicalFactory44` output as the reference. No Task 22 brief
has been written during this audit.
