# Post-array frontier audit: Task 17 matrix3 constants and bounded vec3 indexing

## Projected starting point

This is a read-only projection over pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after Tasks 12–15 and the
proposed Task 16 fixed-local-array/index slice.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 16 | 122 | 124 | 88 |

The recommended next step is a deliberately small **`mat3-const-vec3-index-v1`**
slice.  It is only two programs, but it has correct existing runtime support,
no new pixel-execution model, and a sharply bounded emitter contract.

## Candidate comparison

| Frontier | Immediately clean candidates | Decision |
| --- | ---: | --- |
| `const mat3` + `mat3×vec3` + range-proved `vec3[i]` | 2 | **Recommend.** The C++ runtime already provides column-major `Mat3`, `Mat3×Vec3`, and `Vec::operator[]`; the missing work is controlled typed-IR/emitter admission. |
| Fragment derivatives (`dFdx`, `dFdy`, `fwidth`) | 4 apparent candidates: `filter/halftone:halftone`, `filter/octaveWarp:octaveWarp`, `filter/stamp:stThreshold`, `filter/stipple:stipple` | Defer. The CPU `PixelFn` receives only one `PixelContext`; `run_pass` invokes each pixel independently and does not provide a 2×2 fragment quad or neighboring evaluations. A zero/finite-difference substitution would change GLSL semantics. |
| `mat4` | 0 | Defer. `classicNoisedeck/effects:effects` also needs global mutable arrays, general matrix operations, and a float loop. It must not broaden a `mat3` feature. |
| Miscellaneous builtins/operators | At most one per unrelated primitive | Defer. `all`, `ceil`, `reflect`, `round`, `tanh`, and scalar/other `^` are independent contracts, not a coherent feature. |
| Parameter directions, structs, UBOs, varyings | 0 under a small ABI change | Defer. These alter binding/layout or stage interfaces, rather than merely emitted local computation. |
| Remaining dynamic loops | 0 without a new runtime bound proof | Defer. Texture-size, metadata-only, float, and unbounded uniform-derived forms remain outside Task 15. |

## Exact Task 17 slice

Every key uses the exact default-define map `{}`.

1. `classicNoisedeck/cellNoise:cellNoise`
2. `classicNoisedeck/colorLab:colorLab`

Both have the same narrow source shape:

- Four top-level source-qualified `const mat3` values: `fwdA`, `fwdB`,
  `invB`, and `invA`.
- Each initializer is exactly a direct `mat3` constructor with nine finite
  scalar expressions, in GLSL column-major order.
- Matrix use is only `mat3 * vec3`; no matrix addition, matrix-matrix product,
  matrix indexing, matrix parameter, matrix return, uniform matrix, or matrix
  array occurs in the slice.
- Their vector subscripts are either literals in 0..2 or the already-admitted
  Task-15 induction variable `i` with proof `i=0; i<3; ++i`.  The indexed
  vectors are `vec3` locals, and writes/read-modify-writes remain in 0..2.
- All their loops are Task-15 bounded: `cellNoise` has `i=0..<3` plus a
  `-2..2` neighborhood pair; `colorLab` has two independent `i=0..<3` loops.

The diagnostic replay with this exact type/operator/index union finds no later
frontend rejection for either program.  It does not include the other five
mat3-first programs:

| Deferred mat3-first key | Next blocker after mat3/vector-index admission |
| --- | --- |
| `classicNoisedeck/fractal:fractal` | alternate matrix-constructor form and dynamic integer/float loop forms |
| `classicNoisedeck/moodscape:moodscape` | `floatBitsToUint` |
| `classicNoisedeck/noise:noise` | `floatBitsToUint` and an octave-derived loop bound |
| `classicNoisedeck/shapeMixer:shapeMixer` | `floatBitsToUint` and `reflect` |
| `classicNoisedeck/shapes:shapes` | `floatBitsToUint` |

## Fail-closed contract

### Typed IR

Add a dedicated matrix-constant node/type, not general matrix admission:

1. Only `mat3` is admitted.  The declaration must be source-qualified `const`,
   top-level, initialized once, and never written.
2. The initializer must be exactly `mat3(e0,…,e8)` where every `ei` is a pure,
   finite scalar constant expression accepted by Task 14's source-const
   evaluator.  Reject scalar-diagonal constructors, vector-column constructors,
   matrix conversions, `mat2`, `mat4`, and nonconstant terms.
3. Lower each accepted matrix into a function-local immutable value at the
   entry of every function that references it.  Do not introduce C++ mutable
   globals, `static` state, uniform matrices, or state-object storage.
4. Matrix expressions are exactly `mat3 * vec3` and use a `vec3` result.
   Reject every other matrix binary operator and all matrix indexing.
5. Extend Task 16's interval system only to `vec3[index]` of local variables,
   when index is a literal 0..2 or the exact Task-15 0..<3 induction variable.
   Preserve read/write lvalue semantics; reject `vec2`/`vec4`, array of vectors
   outside Task 16, swizzle-as-index, uniform/parameter index, and unproved
   arithmetic.

### Emitter/runtime semantics

`glsl::Mat3` already stores three `Vec3` columns and implements GLSL-style
column-major `Mat3×Vec3`.  Emit each 9-scalar GLSL constructor as:

```cpp
glsl::Mat3(glsl::Vec3(e0, e1, e2),
           glsl::Vec3(e3, e4, e5),
           glsl::Vec3(e6, e7, e8))
```

This preserves source column order and uses the existing float32 conversion
path.  For a proved vector subscript, emit `value[checked_index]` with the
typed range proof retained in IR; do not use an unchecked source expression,
and do not add a per-pixel exception path.  Because indices are statically
inside 0..2, `operator[]` is safe and keeps `PixelFn` noexcept.

Cap this feature at four `mat3` constants per function (144 bytes of automatic
float storage), depth zero for matrix nesting, and no matrices in arrays or
parameters.  Reject on constant-evaluation overflow/non-finite output, any
unknown index interval, or any attempted mutation.  These rules ensure no
heap allocation, no per-pixel dynamic allocation, and no shared mutable state.

## Counts and verification

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 17 | **124** | **126** | **86** |

Required positive tests:

- both pinned-default oracle programs, including all three vector-component
  loop iterations and both forward/inverse color transforms;
- direct source-order tests distinguishing column-major from row-major
  construction; and
- generated C++ compilation with the existing `glsl::Mat3` runtime overload.

Required negative tests:

- `mat2`, `mat4`, diagonal/vector/matrix conversion constructors;
- non-const or written matrix globals; matrix uniforms, arrays, parameters,
  returns, indexing, addition, and matrix-matrix multiplication;
- `vec3[3]`, negative/dynamic index, unproved affine index, and `vec2`/`vec4`
  dynamic indexing; and
- more than four matrix constants or a non-finite constant expression.

## Why derivatives remain a hard boundary

The current execution ABI is `PixelFn(const KernelState&, const PixelContext&,
Vec4&) noexcept`; the pass runner creates one context and invokes it once per
output pixel.  Fragment derivatives are defined over neighboring invocations
and implementation-dependent helper lanes, not by a pure local expression.
Task 17 must not define `dFdx`, `dFdy`, or `fwidth` as zero, a screen-space
constant, or an ad hoc texture finite difference.  A future derivative task
would need an explicit quad/neighborhood evaluation contract, border policy,
input/output ordering guarantees, and a new oracle strategy before it can
claim GLSL-compatible results.
