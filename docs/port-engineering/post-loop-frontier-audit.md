# Post-loop frontier audit: fixed arrays and indexing

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after Task 12 `mod`, Task 13
`texelFetch`, Task 14 source-const lowering, and the recommended Task 15
`counted-for-v1` 44-key slice.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 15 | 115 | 117 | 95 |

The 95 remaining programs comprise 38 loop-bearing programs with an earlier
non-loop blocker, 21 programs deliberately left outside Task 15's 44-key
slice, and 36 programs with no loop AST.  The next useful boundary is **fixed
local arrays with proven indexing**, not general indexing and not matrices.

## Why arrays first

The immediate array/type frontier has these shapes:

| Shape | Programs | Why it is not one feature today |
| --- | ---: | --- |
| Local `float[9]` / `vec2[9]` with literal or counted-loop index | `filter/celShading:celShadingEdges`, `filter/outline:outlineSobel`, `filter/sharpen:sharpen`, `filter/sobel:sobel`, `classicNoisedeck/refract:refract` | Arrays and typed `index` expressions are rejected before their otherwise Task-15-bounded loops can emit. |
| Local `vec2[13]` with affine counted-loop index | `synth/sacredGeometry:sacredGeometry` | The array is the first blocker; all loops fit Task 15's individual and aggregate caps. |
| Static loop-local scalar post-increment | `filter/pixelSort:computeRank` | `brighterCount++` is outside a loop header.  It is the sole next blocker after the Task-15 loop, `continue`, and Task-13 `texelFetch` support. |
| Global mutable arrays / array parameters combined with larger features | `classicNoisedeck/cellRefract:cellRefract`, `classicNoisedeck/effects:effects`, `classicNoisedeck/kaleido:kaleido` | Requires global mutable state; `effects` also needs `mat4` and a float loop, while `kaleido` next needs `floatBitsToUint`. |
| Global const array constructor plus dynamic bound | `synth/testPattern:testPattern` | `const int GLYPH[10]=int[10](...)`, local `int[3]` / `vec3[8]`, a `d<numDigits` loop, then `round`; it is intentionally outside the local-array contract. |

The first row uses only fixed extents (9), while `sacredGeometry` uses one
fixed extent (13).  The raw array/index AST shapes needed by the recommended
slice are:

| Key | Array declarations / index proof |
| --- | --- |
| `filter/celShading:celShadingEdges` | local `float samples[9]`; `idx=0`; nested `ky=-1..1`, `kx=-1..1`; one `samples[idx]` store and `idx++` per inner iteration, proving `idx` is 0..8; later literal reads 0..8 |
| `filter/outline:outlineSobel` | identical local `float samples[9]` and `idx` proof; Task 13 already supplies its `texelFetch` |
| `filter/sharpen:sharpen` | local `float kernel[9]`, `vec2 offsets[9]`; literal stores 0..8; Task-15 `for (int i=0; i<9; i++)` reads both at induction index `i` |
| `filter/sobel:sobel` | local `float sobel_x[9]`, `float sobel_y[9]`, `vec2 offsets[9]`; literal stores 0..8; Task-15 `i=0..<9` reads each at `i` |
| `classicNoisedeck/refract:refract` | local `float[9]` kernel arrays and `vec2 offset[9]`; `convolve(..., float kernel[9], ...)` is an `in` fixed-array parameter; Task-15 `i=0..<9` indexes the parameter and local array |
| `synth/sacredGeometry:sacredGeometry` | local `vec2 centers[13]`; literal store `centers[0]`, then exact affine stores `centers[1+k]` and `centers[7+k]`, `k=0..<6`; subsequent `i,j=0..<13` reads are in range and all elements are definitely initialized |

No proposed array uses a runtime extent, multidimensional array, array return,
`out`/`inout` array parameter, aggregate copy, global mutable array, or array
constructor.  This deliberately does **not** admit vector/matrix component
indexing: `vec3[i]` is a separate frontier.

## Recommended contract: `fixed-local-array-index-v1`

Add the following narrow, fail-closed semantics on top of Task 15:

1. Element types are only `float`, `vec2`, and (for existing scalar-counter
   flow) `int`; rank is exactly one; length is an integer literal in 1..16.
2. Arrays may be declared only in a function body.  A function may accept an
   `in T[N]` parameter only when `T` and `N` satisfy the same contract; reject
   global arrays, uniform arrays, array constructors, `out`/`inout`, returns,
   copies, and array-to-array assignments.
3. Every `a[index]` must have an integral, statically proved interval wholly
   inside `[0,N-1]`.  Admit a literal, a Task-15 induction variable, or the
   two exact monotonic local-counter forms in this slice: `idx=0; ...; idx++`
   and affine `base+k`, where `base` and `k` have checked intervals.  Reject
   arbitrary arithmetic, uniforms, function parameters, texture dimensions,
   and vector/matrix indexing.
4. Require definite assignment before each read.  Emit an uninitialized
   `std::array<T,N>` only after this proof; do not silently value-initialize it
   and change GLSL's uninitialized behavior.
5. Admit `x++` as an expression statement only for a fresh local `int` with
   a proven interval and exactly `+1` monotonic update.  This is separate from
   Task 15's header-only `++`; it must not admit arbitrary postfix expressions.
6. Cap every array at 16 elements, total live scalar lanes at 64 (256 bytes at
   f32 precision), and lexical array nesting at one.  Count `vec2` as two
   lanes.  Reject a function if liveness cannot be proven below the cap.

Use `std::array<T,N>` as automatic function-local storage and lower an allowed
`in T[N]` parameter to `const std::array<T,N>&`.  This creates no heap
allocation and no shared per-pixel mutable state.  The maximum declared local
array footprints in the proposed keys are 36 bytes (`samples`), 108 bytes
(`sharpen`), 144 bytes (`sobel`), approximately 108 bytes along the refract
helper call path, and 104 bytes (`centers`); all are below the 256-byte cap.

The frontend should retain the resolved element type, length, interval proof,
and definite-initialization proof in typed IR.  The C++ emitter must consume
that checked form instead of re-parsing source expressions.  Bounds checks in
the hot pixel path are therefore unnecessary; missing or failed proof rejects
the program before emission.

## Exact newly clean slice

Under the contract above and Task 15's existing loop/control rules, these
seven keys have no remaining frontend capability blocker.  Every define map
is exactly `{}`:

1. `classicNoisedeck/refract:refract`
2. `filter/celShading:celShadingEdges`
3. `filter/outline:outlineSobel`
4. `filter/pixelSort:computeRank`
5. `filter/sharpen:sharpen`
6. `filter/sobel:sobel`
7. `synth/sacredGeometry:sacredGeometry`

The diagnostic replay was intentionally limited to this contract plus the
already-projected prerequisites.  It finds no later type, operator, builtin,
or statement rejection for those keys; actual implementation still needs
emitter and frozen-oracle verification.  Projected catalog counts are:

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After `fixed-local-array-index-v1` | **122** | **124** | **88** |

## Matrix comparison: defer matrix3/4

Seven remaining programs first reject `mat3`:

`classicNoisedeck/cellNoise:cellNoise`, `classicNoisedeck/colorLab:colorLab`,
`classicNoisedeck/fractal:fractal`, `classicNoisedeck/moodscape:moodscape`,
`classicNoisedeck/noise:noise`, `classicNoisedeck/shapeMixer:shapeMixer`, and
`classicNoisedeck/shapes:shapes`.

They share four top-level `const mat3` values, 9-scalar column-major
constructors, `mat3 * vec3`, and dynamic `vec3[i]` read/write inside otherwise
small `i=0..<3` loops.  A safe matrix3 feature therefore requires more than a
type spelling: source-const matrix lowering, precise GLSL column-major layout,
9-float construction, `mat3×vec3`, and separately range-proved vector index
load/store.  Only two are clean after that broader union:

| Predicted matrix3 clean key | Why the other five remain deferred |
| --- | --- |
| `classicNoisedeck/cellNoise:cellNoise` | `fractal` has dynamic integer/float loop forms and another `mat3` constructor form; `moodscape`, `noise`, and `shapes` next need `floatBitsToUint`; `shapeMixer` next needs `reflect`. |
| `classicNoisedeck/colorLab:colorLab` | same set of deferred blockers above. |

`classicNoisedeck/effects:effects` is the only immediate `mat4` case, but it
also has global mutable `float[9]` kernels, general matrix binary operations,
and `for (float t=0.0; t<=40.0; t++)`.  It must not pull `mat4` into the
matrix3 contract.  Even a carefully scoped matrix3/vector-index feature would
therefore add two keys, versus seven for fixed arrays plus the necessary
counter statement; arrays are the larger coherent and lower-risk frontier.

## Remaining loop forms after this slice

The fixed-array slice consumes `sacredGeometry` and the body-postincrement
case `pixelSort:computeRank`.  The remaining intentionally deferred Task-15
loop cases are:

- `filter/blur:blurH` and `filter/blur:blurV`: bound is
  `int(radius[XY]*renderScale)` without a compiler-enforced `renderScale` cap.
- `filter/normalize:statsFinal`: bounds come from `textureSize(...).xy`.
- `filter/tetraColorArray:tetraColorArray`: `colorCount` has metadata max 8,
  but no generated runtime range enforcement yet.
- `filter/reindex:nmReindexReduce`: 512×512 lexical visits exceed the 4,096
  cap.
- `filter/zoomBlur:zoomBlur`: float induction (`t=0.0; t<=40.0; t++`).
- `filter/extrude:extrude` (`all`), `filter/grade:*` (dynamic vector index),
  `filter/halftone:halftone`, `filter/octaveWarp:octaveWarp`,
  `filter/stamp:stThreshold`, and `filter/stipple:stipple` (derivatives),
  `synth/curl:curl` (`tanh`), and `synth/perlin:perlin` (unsupported `^`).

Verification should include negative IR/emitter tests for an out-of-range
index, `a[uniform]`, unknown interval, 17 elements, 65 live lanes, a global
array, array copy/out parameter, uninitialized read, `vec3[i]`, and a
non-counter `x++`.  For the seven positive keys, run frozen oracle cases that
exercise all indices (especially `centers[0..12]`, Sobel 0..8, and refract's
array parameter) as well as the `continue` and local-counter paths.
