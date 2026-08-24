# Global-constant frontier audit

Date: 2026-08-10  
Repository checked read-only: `.`  
Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`  
Scope: only the 58 programs whose current first typed-generator rejection is a
top-level global declaration, evaluated against the post-Task-12 capability
vocabulary (including `mod`).

## Conclusion

There is a narrow, safe future frontier: source-qualified, initialized,
read-only `const` `int`/`uint`/`float`/`vec3` globals can be lowered to
function-local immutable constants.  This does not create C++ static state and
therefore cannot leak values from one pixel/kernel invocation to another.

Of the 58 global-first programs:

- **52** contain only that general source form (40 scalar-only and 12 also
  containing non-array vectors); all of their present initializers are
  structurally pure constant expressions and no declared global is written.
- **6** must remain outside that contract: two use `mat3`, one uses `mat4` and
  arrays (and writes a purported const), one uses arrays, and two have
  uninitialized mutable globals written during rendering.
- Only **6 programs become fully validator- and typed-emitter-clean** when the
  global gate alone is replaced in memory: `filter/pixelSort:finalize`,
  `filter/pixelSort:prepare`, `filter/skew:skew`,
  `filter/tetraCosine:tetraCosine`, `filter/tile:tile`, and
  `synth/osc2d:osc2d`.  They are the exact unlockable keys for a coherent
  global-constant slice; all other eligible programs immediately meet an
  unrelated later frontier.

The in-memory projection did not edit the repository or claim native compile
success; it replaced only admitted global declarations to expose the next
validator/emitter result.

## Recommended fail-closed contract

Admit a program only if **every** non-interface top-level declaration satisfies
all of the following:

1. It has the source `const` qualifier, has an initializer, and has type
   exactly `int`, `uint`, `float`, or `vec3` (not a bool, other vector width,
   array, matrix, struct, sampler, or opaque type).  Those are the exact types
   needed by this cohort.
2. Its initializer is a typed, side-effect-free constant-expression tree using
   only literals; an earlier admitted constant by stable symbol identity;
   supported scalar/vector construction; unary `+`/`-`; binary `+`, `-`, `/`,
   or a range-checked scalar integer `<<`; and a vector swizzle of an earlier
   admitted constant.  Those are the exact forms present in the 52 candidates.
   No calls/builtins, conditional, indexing, general member access, casts
   outside current emitter rules, or forward references are admitted.
3. The source declaration graph is acyclic and dependency-ordered.  Each
   initializer and its dependency closure must be validated by the same typed
   capability/emitter checks as a function body; declaration initializers must
   not bypass validation.
4. A whole-program symbol-identity scan proves zero writes to each admitted
   constant: direct assignment, compound assignment, increment/decrement, and
   writes through swizzles/indexes/member expressions are all rejection cases.
5. The emitter materializes the required dependency closure as `const` locals
   at the beginning of every generated GLSL function that reads it (including
   helpers), rather than as a namespace/global/static object.  Preserve the
   existing Float32 vector construction/storage boundary and scalar numeric
   contract.  An unused global may be omitted.

This is deliberately a source-const lowering feature, not general GLSL global
state, and not C++ `static` storage.  It excludes all mutable and uninitialized
globals even if an implementation could zero-initialize them.

## Declaration and access classification

The semantic frontend already proves that every *present* top-level initializer
is a structural GLSL constant expression (literal/earlier const reference/
constructor/unary/binary/conditional/swizzle/member/index), so there are no
function or builtin calls in these initializers.  The classifications below add
the required whole-body read/write audit.

### Admissible scalar-only const forms (40)

All are initialized, structurally pure, and read-only.  Names/types are exact;
an empty use would still be harmless but is not treated as mutable state.

- `classicNoisedeck/bitEffects:bitEffects`: `int BIT_COUNT`, `int mask`
  (`mask` depends on `BIT_COUNT` through a constant shift/subtract tree).
- `filter/bloom:ntapGather`: `int MAX_TAPS`, `float GOLDEN_ANGLE`, `float PI`.
- `filter/blur:blurH`, `filter/blur:blurV`: `float PI` each.
- `filter/celShading:celShadingColor`: `float MIN_GAMMA`.
- `filter/clouds:clouds`, `filter/degauss:degauss`, `filter/lowPoly:lowPoly`,
  `filter/octaveWarp:octaveWarp`, `filter/polar:polar`,
  `filter/tetraColorArray:tetraColorArray`, `mixer/cellSplit:cellSplit`:
  `float TAU` each.
- `filter/crt:crt`: `float PI`, `float TAU`, `float INV_THREE`.
- `filter/directionalBlur:directionalBlur`, `filter/spinBlur:spinBlur`:
  `int N` each.
- `filter/extrude:extrude`: `float TOP_SIGN`, `SHADE_TOP`, `SHADE_BOTTOM`,
  `SHADE_LEFT`, `SHADE_RIGHT`, `EPS`.
- `filter/glyphMap:glyphMap`: `int GLYPH_COUNT`.
- `filter/grain:grain`: `float PI`, `TAU`, `UINT32_TO_FLOAT`; `uint
  CHANNEL_COUNT`, `INTERPOLATION_CONSTANT`, `INTERPOLATION_LINEAR`,
  `INTERPOLATION_COSINE`, `INTERPOLATION_BICUBIC`, `BASE_SEED`.
- `filter/halftone:halftone`: `float DOT_AREA_CAP`, `PI`, `MID_DOT_RADIUS`,
  `MAX_DOT_RADIUS`.
- `filter/lens:lens`: `float HALF_FRAME`.
- `filter/lightLeak:lightLeak`: `float TAU`, `int POINT_COUNT`.
- `filter/parallax:parallax`: `int MARCH_STEPS`, `float SHIFT_SCALE`.
- `filter/pixelSort:finalize`, `filter/pixelSort:prepare`, `filter/skew:skew`:
  `float PI` each.
- `filter/posterize:posterize`: `float MIN_LEVELS`, `float MIN_GAMMA`.
- `filter/reindex:nmReindexReduce`: `float F32_MAX`, `F32_MIN`; `int
  TILE_SIZE`, `MAX_TILE_DIM`.
- `filter/reindex:nmReindexStats`: `float F32_MAX`, `F32_MIN`; `int TILE_SIZE`.
- `filter/rotate:rot`: `float TAU`.
- `filter/strokes:stkSmear`: `int MAX_TAPS`.
- `filter/tetraCosine:tetraCosine`: `float TAU`.
- `filter/tile:tile`, `filter/tunnel:tunnel`: `float PI`, `float TAU` each.
- `filter/vaseline:upsample`: `int TAP_COUNT`; `float RADIUS`,
  `GOLDEN_ANGLE`, `BRIGHTNESS_ADJUST`.
- `filter/wind:wind`: `int MAX_STEPS`; `float STEP_PX`, `MAX_REACH`.
- `synth/bitwise:bitwise`: `float PI`.
- `synth/mandelbrot:mandelbrot`: `float PI`, `TAU`, `BAILOUT`, `LOG2`; `int
  MAX_ITER`.
- `synth/osc2d:osc2d`: `float PI`, `float TAU`.
- `synth/perlin:perlin`: `float TAU`, `float Z_PERIOD`.
- `synth/subdivide:subdivide`: `float PHI`.

### Admissible const scalar/vector forms (12)

All are initialized, structurally pure, and read-only.  `vec3` initializers are
literal constructors except `scanlineError`'s time seeds, which are pure
swizzle/arithmetic expressions over earlier const vectors and therefore need
dependency-aware local lowering.

- `filter/edge:edge`, `filter/emboss:emboss`: `vec3 LUMA` each.
- `filter/fxaa:fxaa`: `uint CHANNEL_COUNT`, `float EPSILON`, `vec3
  LUMA_WEIGHTS`.
- `filter/grade:creative`, `filter/grade:primary`, `filter/grade:vignette`,
  `filter/grade:wheels`, `filter/smooth:smoothBlend`, `filter/smooth:smoothEdge`:
  `vec3 LUMA_WEIGHTS` each.
- `filter/grade:hslSecondary`: `vec3 LUMA_WEIGHTS`, `float PI`.
- `filter/scanlineError:scanlineError`: `float TAU`; `vec3 BASE_SEED_LINE`,
  `TIME_SEED_LINE`, `BASE_SEED_SWERVE`, `TIME_SEED_SWERVE`, `BASE_SEED_WHITE`,
  `TIME_SEED_WHITE`.
- `filter/snow:snow`: `uint CHANNEL_COUNT`, `float TAU`; `vec3
  TIME_SEED_OFFSETS`, `STATIC_SEED`, `LIMITER_SEED`.

### Explicitly rejected global forms (6)

| Program | Exact declaration form and purity | Access/leakage result |
|---|---|---|
| `filter/adjust:adjust` | `const float TAU`; `const mat3 fwdA`, `fwdB`, all pure literal constructors. | Read-only, but matrix globals are outside this narrow feature; needs matrix support. |
| `filter/colorspace:colorspace` | Same `const float TAU`, `const mat3 fwdA`, `fwdB` pattern, pure. | Read-only, but matrix globals are outside this feature. |
| `filter/dither:dither` | 19 scalar `const int` selectors; `const mat4 bayer2x2`, `bayer4x4`; eight `const vec3[N]` palettes; five scalar `const int` Floyd--Steinberg constants. Every initializer is structural/pure. | **Reject:** `FS_APRON_MAX` is written in the body despite the source `const`. Lowering it to C++ shared/static state would leak and race; arrays/mat4 also require later frontiers. |
| `filter/normalMap:normalMap` | `const uint CHANNEL_COUNT`, `CHANNEL_CAP`; `const ivec2[9] SOBEL_OFFSETS`; `const float[9] SOBEL_X_KERNEL`, `SOBEL_Y_KERNEL`, all pure constructors. | Read-only but arrays/indexing are excluded. |
| `synth/noise:noise` | uninitialized mutable `vec2 globalCoord`. | Read and assigned per render; C++ global/static lowering would carry per-pixel state. Reject. |
| `synth/shape:shape` | `const float PI`, `TAU`; uninitialized mutable `float aspectRatio`, `vec2 globalCoord`. | Both mutable globals are read and assigned per render; reject despite the two safe scalar constants. |

There are no struct globals in this 58-program cohort (the four struct-first
programs are a separate planning category).

## Exact unlocks and secondary blockers

The six unlocks each have only literal scalar constants and no global writes:

1. `filter/pixelSort:finalize`
2. `filter/pixelSort:prepare`
3. `filter/skew:skew`
4. `filter/tetraCosine:tetraCosine`
5. `filter/tile:tile`
6. `synth/osc2d:osc2d`

For the other 46 otherwise-admissible constant-only programs, the following is
the first remaining rejection after an in-memory-only lowering projection:

- loop (`for`) (23): `filter/bloom:ntapGather`, `filter/blur:blurH`,
  `filter/blur:blurV`, `filter/clouds:clouds`,
  `filter/directionalBlur:directionalBlur`, `filter/extrude:extrude`,
  `filter/grade:creative`, `filter/grade:hslSecondary`, `filter/grade:primary`,
  `filter/grade:vignette`, `filter/grade:wheels`, `filter/halftone:halftone`,
  `filter/lowPoly:lowPoly`, `filter/octaveWarp:octaveWarp`,
  `filter/reindex:nmReindexReduce`, `filter/reindex:nmReindexStats`,
  `filter/spinBlur:spinBlur`, `filter/strokes:stkSmear`,
  `filter/tetraColorArray:tetraColorArray`, `filter/wind:wind`,
  `mixer/cellSplit:cellSplit`, `synth/perlin:perlin`, `synth/subdivide:subdivide`.
- `texelFetch` (6): `filter/crt:crt`, `filter/degauss:degauss`,
  `filter/lightLeak:lightLeak`, `filter/smooth:smoothBlend`,
  `filter/smooth:smoothEdge`, `filter/vaseline:upsample`.
- `round` (4): `filter/fxaa:fxaa`, `filter/grain:grain`,
  `filter/posterize:posterize`, `filter/snow:snow`.
- `dFdx` (3): `filter/lens:lens`, `filter/polar:polar`,
  `filter/tunnel:tunnel`.
- unsigned/integer bitwise operators (3): `classicNoisedeck/bitEffects:bitEffects`
  and `filter/glyphMap:glyphMap` need `&`; `synth/bitwise:bitwise` needs `^`.
- one each: `filter/celShading:celShadingColor` needs `fwidth`;
  `filter/edge:edge` needs `bvec3`; `filter/emboss:emboss` has a local
  `float[9]`; `filter/parallax:parallax` needs `textureLod`;
  `filter/rotate:rot` has a matrix return; `filter/scanlineError:scanlineError`
  needs `floatBitsToUint`; `synth/mandelbrot:mandelbrot` has an `out` parameter.

The six rejected-global programs above have not been reclassified as unlocks:
their matrix/array/mutable-state requirement remains the immediate blocker.

## Verification performed

- Parsed and semantically analyzed all 58 authoritative-default source files.
- Enumerated top-level typed declarations, initializer trees, stable-symbol
  reads, and write targets across every helper and `main` body.
- Re-ran capability validation and typed emission on an in-memory projection
  that bypassed only eligible global declarations to reveal the first later
  blocker.  The six listed unlocks passed both steps.
- No repository files, corpus data, oracle artifacts, or Git state were
  modified.
