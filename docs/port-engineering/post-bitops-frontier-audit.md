# Post-bitops frontier audit: Task 19 constrained intrinsic signatures

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after proposed Tasks 12–18.
Derivative semantics remain excluded pending an explicit neighborhood/quad ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 18 | 128 | 130 | 82 |

## Recommendation: `constrained-intrinsics-v1`

The next coherent fail-closed slice is three exact, independently typed
intrinsic signatures that all lower to local, deterministic CPU computation or
the already-existing base-level sampler.  It intentionally does not become a
general builtin admission.

| Key | Exact default defines | Required signature(s) |
| --- | --- | --- |
| `filter/pixelSort:gatherSorted` | `{}` | `round(float) -> float` |
| `filter/extrude:extrude` | `{ "DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0 }` | `lessThanEqual(vec2,vec2) -> bvec2`; `all(bvec2) -> bool` |
| `filter/parallax:parallax` | `{}` | `textureLod(sampler2D,vec2,0.0) -> vec4` |

The projected prior features cover their remaining needs: `gatherSorted` has
Task-15's C(32) counted loop and Task-13 texel fetch; `extrude` has Task-14
constants and Task-15 bounded loops; `parallax` has `MARCH_STEPS=32` as a
Task-14 source constant and a Task-15-bounded march.  A diagnostic replay of
these exact signatures finds no later frontend rejection in any of the three.

## Narrow runtime/emitter semantics

1. `round(float) -> float` only.  Emit the existing `glsl::round` helper,
   which implements the GLSL-compatible `floor(x + 0.5)` result; retain the
   normal typed float32 conversion at the receiving expression boundary.
   Reject vectors, integer overloads, and `roundEven`.
2. Admit only the pair `lessThanEqual(vec2,vec2) -> bvec2` and
   `all(bvec2) -> bool`.  Materialize both boolean lanes before reducing them
   with logical `&&`; do not introduce `any`, `bvec3`, `bvec4`, boolean
   vectors in uniforms/state/arrays, or other comparison families.
3. Admit `textureLod(sampler2D, vec2, float)` only when the third AST operand
   is the literal floating zero (canonicalized to f32 `0.0`).  Emit the same
   base-level `sample_texture(surface, uv)` path used by `texture`.  Reject
   nonzero, negative, dynamic, or computed lod values and all sampler kinds
   other than `sampler2D`; no mip storage or filtering policy is introduced.
4. Preserve existing checked IR provenance: every admitted call carries its
   exact overload tag, and every key/define map is a sorted, metadata-verified
   allowlist entry.  Unknown overloads or define mismatch fail before emission.
5. These operations allocate nothing, introduce no state, do not access
   neighboring pixels, and retain `PixelFn` noexcept.  The new `bvec2` value is
   an automatic two-lane temporary only.

Required positives are frozen oracles for all three keys, direct numerical
tests around `round` half boundaries (including negative values), both true and
false lanes for `all(lessThanEqual(...))`, and equivalence of
`textureLod(tex,uv,0.0)` with the base sampler at the same UV.  Required
negatives reject vector `round`, `any`, bvec3/4, `greaterThan`, a computed or
nonzero lod, textureLod on another sampler type, and metadata-define drift.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 19 | **131** | **133** | **79** |

## Ranked residual map

The entries below are independent frontiers, not authorization to bundle them.
Counts are the currently visible direct slice size; later blockers can overlap.

| Rank | Frontier | Direct scale / examples | Reason it remains separate |
| ---: | --- | --- | --- |
| 1 | Range-proved general `vec3[i]` | six grading passes: `creative`, `hslSecondary`, `lut`, `primary`, `vignette`, `wheels` | Needs a broader lvalue/rvalue vector-index proof than Task 17's matrix-specific use. |
| 2 | Dynamic-loop range contracts | six visible cases: blur H/V, `normalize:statsFinal`, `tetraColorArray`, `nmReindexReduce`, `zoomBlur` | Bounds depend on render scale, texture dimensions, metadata enforcement, a 512² charge, or float induction. |
| 3 | Derivative ABI | four otherwise-close passes: halftone, octaveWarp, stamp threshold, stipple | Cannot be correct without pixel-neighborhood/quad semantics. |
| 4 | Vector math completion | `synth/curl:curl` needs `tanh(vec3)` plus `mod(vec3,float)` and `mod(vec4,float)` | This expands Task 12's deliberately narrow mod overload set, so it is not folded into Task 19. |
| 5 | Scalar/signed bitwise | `classicNoisedeck/bitEffects:bitEffects` | Needs signed `int` `&`, `|`, `^`, and `<<`, with explicit two's-complement/wrap policy beyond Task 18's unsigned XOR. |
| 6 | Other isolated builtins | `ceil` in `oilFlatten`, `reflect` in lighting/shapeMixer, `tanh`/vector-mod above | Distinct overload and numeric contracts; `oilFlatten` also has an unbounded ceil-derived loop. |
| 7 | Matrices and global arrays | five residual mat3-first programs; `classicNoisedeck/effects:effects` mat4 | Need alternate constructors, float-bit/builtin work, dynamic loops, mat4 algebra, or mutable globals. |
| 8 | Interfaces / ABI | `out`/`inout` helpers, structs (`julia`, `newton`), UBO (`synth/remap`), varyings (`grime`, `texture`) | Changes function calling, buffer layout, or stage inputs rather than local generated expression semantics. |
| 9 | General sampling | nonzero/dynamic LOD, other sampler types | Requires mip-chain ownership and a pinned level/filtering policy. |

`synth/curl:curl` is specifically deferred despite its visible `tanh`: it also
uses `mod(vec3,float)` and `mod(vec4,float)`, which Task 12 intentionally did
not admit.  `filter/oilPaint:oilFlatten` is deferred despite `ceil` because
its `sampleLimit=ceil(fr)` drives an unproved nested loop.  This avoids
smuggling dynamic-loop or broad vector-math semantics into a small intrinsic
slice.
