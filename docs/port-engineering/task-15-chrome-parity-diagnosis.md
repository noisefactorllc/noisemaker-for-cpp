# Task 15 Chrome H exact-parity diagnosis

## Finding

`filter/chrome:chBlurH` is not missing an F32 boundary.  The failing native
shape has **one extra F32 materialization**: it rounds the scalar-weighted
tap pair before adding it to `sum`.  The canonical JS factory does not round
that product until the accumulator write.

The narrow fix belongs in typed C++ expression emission, not in `typed_10`,
the sampler, `FloatExpr`, or the loop lowering.

## Reproduction evidence

The Task 15 test's canonical first-pixel probe is:

```text
expected  3f051fe7 3f19975b 3e2928db 3f09457c
failing   3f051fe7 3f199759 3e2928da 3f09457d
```

The generated JS reference is `canonicalFactory33` in
`../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js`.
Its tap update is:

```js
(vec4.add([], texture(...), texture(...)))
  .map(_ => _ * w)
  .reduce((res, el, i) => (res[i] += el, res), sum)
```

`vec4.add([], ...)` writes F32 lane values, but `[]` is an ordinary JavaScript
Array.  Consequently its following `.map` stores `pairF32 * wF32` as a
Number/F64; only the typed-array accumulator write in `reduce` rounds the
result.  The required boundary sequence per channel is therefore:

```text
sample F32 + sample F32 -> pair F32
pair F32 * w F32       -> F64
sum F32 + product F64  -> sum F32
```

I compiled two read-only standalone native expressions against the current
runtime and exact 11x9 fixture.  The expression that preserves the product as
`FloatExpr` gives the canonical bits:

```cpp
sum = glsl::Vec4(sum + (glsl::Vec4(sampleA + sampleB) * w));
// 3f051fe7 3f19975b 3e2928db 3f09457c
```

Forcing the additional product materialization gives exactly the failing bits:

```cpp
sum = glsl::Vec4(sum + glsl::Vec4(glsl::Vec4(sampleA + sampleB) * w));
// 3f051fe7 3f199759 3e2928da 3f09457d
```

This rules out texture coordinates, bottom-left sampling, `exp`, loop trip
count, and final output conversion as the immediate cause.

## Safest systemic correction

Preserve the existing `FloatExpr` delayed-rounding model and adjust only the
typed emitter's canonical-plain-array vector path.  A vector-vector operation
lowered by JS as `vecN.op([], a, b)` must materialize the pair to `VecN` (its
lanes are F32), but an immediately following scalar map must remain a
`FloatExpr` until its typed local or assignment boundary.  In practical C++
emission:

```cpp
// correct: pair boundary, no product boundary, assignment boundary
sum = glsl::Vec4(sum + (glsl::Vec4(sampleA + sampleB) * w));

// reject: adds a boundary JS does not have
sum = glsl::Vec4(sum + glsl::Vec4(glsl::Vec4(sampleA + sampleB) * w));
```

`tools/glslcpp/emit_typed_cpp.py` already has the narrow
`_canonical_plain_array_vector` / `scalar_map_of_plain_array` classification
needed for this rule.  Keep it scoped to vector-vector results that feed a
scalar-only vector arithmetic chain; do not globally remove vector
materialization, which would lose the required F32 pair boundary and regress
other kernels.

The currently visible `typed_10` source has the correct first form.  If an
executed binary still produces the failing second-form bits, its generated
object was compiled before this form was present; rebuild the affected target
and rerun the exact Task 15 oracle rather than editing the generated kernel by
hand.

## Verification required for a fix

1. Regenerate the typed slice from the emitter and assert `typed_10` has the
   correct first expression.
2. Rebuild the test target, then run
   `typed_task15_all_thirty_eight_external_oracles_are_exact_and_repeatable`.
3. Keep the Chrome H bit probe above as a regression check and run all 38
   F32/RGBA oracle hashes; the rule is shared by other weighted vector paths.
