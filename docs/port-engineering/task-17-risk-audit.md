# Task 17 implementation-risk audit: fixed nine-element local tables

Date: 2026-08-10  
Repository inspected: `.`  
Method: read-only corpus, typed-IR, emitter/runtime, and pinned canonical-CPU
inspection.  No repository file was changed and no Git command was used.

## Recommendation

After the now-present Task 16 `discarded-local-counter-statement-v1`, the
smallest coherent next slice is a two-key, source-identity-locked capability:

```text
fixed-nine-local-literal-init-counted-read-v1
  filter/sharpen:sharpen
  filter/sobel:sobel
```

The two programs are isomorphic in the aspects this capability admits: a
function-local fixed array of exact size nine, declaration without a source
initializer, complete literal-index initialization before any read, and read
only through one existing literal `i=0; i<9; ++i` counted loop.  Sharpen has
`float[9] kernel` plus `vec2[9] offsets`; Sobel has `float[9] sobel_x`,
`float[9] sobel_y`, and `vec2[9] offsets`.  Treating the pair as one narrowly
proof-carrying capability avoids making a general GLSL array/index language.

## Current frontier and counts

The current allowlist contains 108 typed entries, including
`filter/pixelSort:computeRank`; generated public catalog cardinality is 110.
The pinned manifest contains 212 programs.  Replaying semantic analysis and
the current capability validator over all 104 unallowlisted programs found
these direct local-array blockers:

| Key | Current first rejection |
| --- | --- |
| `filter/sharpen:sharpen` | `25:11 unsupported typed type float[9]` |
| `filter/sobel:sobel` | `23:11 unsupported typed type float[9]` |
| `filter/celShading:celShadingEdges` | `41:11 unsupported typed type float[9]` |
| `filter/outline:outlineSobel` | `60:11 unsupported typed type float[9]` |
| `classicNoisedeck/refract:refract` | `26:24 unsupported typed type float[9]` |
| `synth/sacredGeometry:sacredGeometry` | `96:10 unsupported typed type vec2[13]` |

The replay also showed five unallowlisted non-array programs that happen to
use only already-approved constructs.  They are not authorization to broaden
Task 17.  Adding only the two recommended keys changes the catalog exactly:

| Projection | Typed | Public | Publicly unported (`212 - public`) |
| --- | ---: | ---: | ---: |
| Current post-Task-16 tree | 108 | 110 | 102 |
| Task 17 recommended pair | 110 | 112 | 100 |

## Exact source and binding lock

| Key | Raw / normalized source SHA-256 | Defines | Binding signature | Source-bound defaults |
| --- | --- | --- | --- | --- |
| `filter/sharpen:sharpen` | `c9a9b196e61a2904b37ad89c7fc46bee1b40b6bba81293dde3d7cd37527773e7` / `1a252d3d5efca1c657dcde87953b12c081c586da01d885e24d3b50395ec5abb0` | `{}` | `tileOffset:vec2@1, fullResolution:vec2@2, inputTex:sampler2D@3/S1, amount:float@4, renderScale:float@5` | `amount=1`; runtime-owned `renderScale=1` |
| `filter/sobel:sobel` | `ef459738b931929a65422df36f852da4e7cbe4e90387690bea747a34a2e52f84` / `d8aad0d49bd0b1badd5231b46bb7bd5a35f9eddadd466afd4ac9f1a0fc0cbf0c` | `{}` | `tileOffset:vec2@1, fullResolution:vec2@2, inputTex:sampler2D@3/S1, amount:float@4, renderScale:float@5, alpha:float@6` | `amount=1, alpha=1`; runtime-owned `renderScale=1` |

Both are single-pass `inputTex -> outputTex` filters with `fragColor:vec4`.
The metadata pass has no per-pass uniform remapping; effect defaults bind the
source names above.  `tileOffset` and `fullResolution` remain required
runtime bindings, not inferred shader parameters.

## Immutable typed-IR proof needed

The attached/recomputed counted-loop proof already gives one literal loop per
key: `i` starts at 0, comparison is `< 9`, update is `++`, exactly nine trips,
depth one, lexical product nine, entrypoint charge nine.  The new proof must
be recomputed from immutable typed IR after loop proof attachment and again
at emission; source spelling, text scanning, or a passed-in proof is not
authority.

| Key | Stable local symbols in this parse | Arrays and literal stores | Reads |
| --- | --- | --- | --- |
| Sharpen | `kernel` id 15; `offsets` id 16; induction `i` id 18 | `float[9] kernel`: writes 0..8 once; `vec2[9] offsets`: writes 0..8 once | only `offsets[i]`, `kernel[i]` inside the nine-trip loop |
| Sobel | `sobel_x` id 16; `sobel_y` id 17; `offsets` id 18; induction `i` id 21 | each of the three exact `[9]` arrays writes 0..8 once | only `offsets[i]`, `sobel_x[i]`, `sobel_y[i]` inside the nine-trip loop |

Symbol numbers above are diagnostic evidence, not a cross-parse ABI.  The
admission contract needs the source digest, typed symbol identities within
the rebuilt IR, exact declaration/statement positions and control ancestry.
It must prove all of the following:

1. The declaration is a function-local `float[9]` or `vec2[9]` with no
   initializer, no array parameter/return/global/storage qualifier, and no
   alias/copy/escape.
2. Every direct write target is exactly one admitted array plus a literal
   signed-int index in `{0,...,8}`.  Each index occurs once; all writes happen
   before the only reading loop and no later array write exists.
3. The loop subscript is exactly the proved induction symbol, with interval
   `[0,8]`.  It is not an expression, swizzle, parameter, other local, nested
   index, or a second loop.  The read set contains only the stated symbols.
4. No control edge can bypass table completion before a read; no return,
   break, continue, or conditional sits in the initialization region.  The
   existing reading loop may retain its texture builtins, but no array value
   may be passed to a call or escape through one.

That permits direct native `operator[]` only after the proof.  Do not use
`std::array::at`: it introduces a throwing path into `noexcept` pixel code.
Do not add generic dynamic indexing, array expressions, arbitrary sizes,
partially initialized arrays, aggregate initializers, arrays of other types,
or array arguments/returns.

## Canonical precision, zero-fill, and native lowering

Pinned canonical CPU factories use two distinct representations:

- scalar tables are ordinary JavaScript Number arrays created as
  `[0,0,0,0,0,0,0,0,0]`; and
- offset tables are arrays of nine zeroed `PooledFloat32Array([0,0])` vectors.

This matters even though all admitted literal values are exactly representable.
The C++ emitter intentionally keeps GLSL scalar local temporaries as `double`
to model JavaScript Number arithmetic, while `glsl::Vec2` owns F32 lanes.
Required lowering is therefore, with value initialization:

```cpp
std::array<double, 9> kernel{};       // or sobel_x/sobel_y
std::array<glsl::Vec2, 9> offsets{};
```

`std::array<float,9>` would introduce a scalar F32 storage boundary absent
from the canonical Number array.  Leaving either array uninitialized diverges
from canonical zero-fill and risks undefined behavior if future validation is
wrong.  `glsl::Vec2` itself value-initializes its lanes, so `offsets{}` matches
the canonical zeroed vector construction.  This requires no heap allocation,
resource ABI, callback, virtual dispatch, string/map lookup, or exception
path in pixel execution.

Raw table payload is 144 bytes for Sharpen (`double[9]` 72 plus nine Vec2
F32 lanes 72) and 216 bytes for Sobel (two 72-byte scalar tables plus 72-byte
offset table).  These are payload figures, not a portable complete frame-size
claim: vector/temporary alignment and compiler decisions determine the actual
frame.  Require debug and release compiler stack-usage evidence or an
equivalent target-specific frame measurement before imposing a hard stack cap.

## Explicit exclusions

- `filter/celShading:celShadingEdges` and `filter/outline:outlineSobel` use a
  dynamic `samples[idx]` store inside nested `-1..1` loops and a body-level
  `idx++`; their initialization/index proof is different.
- `classicNoisedeck/refract:refract` passes `float[9]` through an `in`
  parameter and therefore needs an array ABI/ownership/alias contract.
- `synth/sacredGeometry:sacredGeometry` uses `vec2[13]` with affine loop
  writes and a nested 13-by-13 read pattern.
- Other index-frontier effects (for example grade/lens-distortion forms) are
  not evidence for local fixed-table admission.

No `noisemaker-for-qt` implementation was used as a runtime authority; its
tree did not supply a relevant sharpen/sobel lowering for this decision.

## Required verification before acceptance

1. Negative IR tests for every rejected size/type/storage/initializer,
   missing/duplicate/nonliteral/out-of-range write, read-before-completion,
   dynamic subscript, wrong induction symbol/bound/update, second write,
   nested loop, call/return/control bypass, key/digest/define/binding drift,
   and stale/forged proof.
2. Emitter tests that verify exactly the two allowed key/source profiles,
   `std::array<double,9>{}` and `std::array<glsl::Vec2,9>{}` lowering,
   direct proved indexing, no `at`, no allocation, and preserved `noexcept`.
3. Canonical differential oracles from the pinned CPU factory for each key:
   non-square top-down F32 input, nonzero tile offset/full resolution, default
   bindings, and at least one non-default amount (plus Sobel alpha 0 and 1).
   Freeze F32 and RGBA8 hashes, bit probes, orientation, and double-render
   identity; use dimensions that make every offset table entry observable.
4. Build and run debug/release native differential tests with the frozen
   inputs.  Confirm typed/public counts 110/112 and that exactly these two
   new factories, not the adjacent array users or whole effects, appear.
5. Measure actual debug and release stack frames under the supported compiler
   configuration; validate the raw 144/216-byte table payload calculation and
   retain the allocation-free pixel contract.
