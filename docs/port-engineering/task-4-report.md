# Task 4 report: typed GLSL value and binding ABI

## Test-first evidence

1. Added `glsl_vec_default_and_splat_construction` and wired its translation unit, then ran:

   ```sh
   cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
   cmake --build build --parallel
   ```

   Red result: compilation failed as expected because `noisemaker/glsl_types.hpp` did not exist.

2. Added the minimal typed header/runtime/CMake wiring. The first green build exposed an ill-formed lane-count trait for scalar constructor constraints; corrected that trait, then the foundation test and all pre-existing tests passed.

3. Added direct vector tests for construction, compile-time lane constraints, conversions, deferred float expressions, integer wrap/division, scalar operands, swizzles, and matrices. The red build exposed missing `Vec`/`FloatExpr` mixed operators. Added the mixed operands, then the suite passed. During this slice, the initial sentinel expression was mistakenly written as `a + b * c`; the task owner supplied the brief correction to the required `a + b + c` expression before it was accepted. The matrix-product test oracle was also corrected to the independently calculated column-major product.

4. Added runtime/binding tests. The direct expression-to-`dot` test failed to compile because template deduction cannot materialize `FloatExpr` implicitly. Added explicit expression-consumption overloads for `dot`, `length`, and `normalize`; this then passed.

5. Added the corresponding direct `reflect(FloatExpr, Vec)` test. It failed to compile as expected, then added materializing overloads for `cross`, `reflect`, and `refract` so all geometric vector builtins share the same consumption boundary.

## Files changed

- `CMakeLists.txt`
- `include/noisemaker/glsl_types.hpp`
- `include/noisemaker/glsl_runtime.hpp`
- `src/glsl_runtime.cpp`
- `tests/test_glsl_types.cpp`
- `tests/test_glsl_runtime.cpp`

## Decisions within scope

- `Vec<float>` is float32 storage; float operators produce `FloatExpr<N>` with double lanes and narrow only when consumed into a `Vec` or a typed vector builtin.
- Signed 32-bit add/subtract/multiply use unsigned bit-pattern arithmetic; integer division by zero returns zero and `INT32_MIN / -1` wraps to `INT32_MIN`.
- Float-to-int conversions are deterministic: NaN maps to zero and finite/infinite out-of-range values saturate to the target range.
- Matrices use column-major `Vec` columns and float64 accumulation with one float32 store per result lane.
- Binding maps are an external one-time boundary; samplers are explicitly non-owning.
- Clang/GNU library and test targets receive `-ffp-contract=off`.

## Final verification

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
build/noisemaker-cpu-tests
ctest --test-dir build --output-on-failure
```

Result: 43 named test cases passed; CTest 1/1 passed.

## Remaining concern

The first minimal-header red/green cycle and each later focused failure are recorded above. The broad test batches were then refined while compiling, so the full final test inventory should not be represented as every assertion having existed before every corresponding line of production code. No runtime behavior remains known to fail this task's contract.

## Fix round 1: independent review findings

1. Added direct tests for `Vec3(FloatExpr<Vec2>, scalar)`, both matrix/expression multiplication directions, unary float/int/uint negation, component-helper expression inputs, JS NaN/signed-zero min/max behavior, and the normalize rounding sentinel. Red command:

   ```sh
   cmake --build build --parallel
   ```

   Red result: the compiler rejected `FloatExpr` as a flattening lane part, lacked matrix/expression operators and unary negation, and could not resolve expression inputs for component helpers.

2. Added `FloatExpr` lane-part recognition/materialization, both matrix directions, double-backed unary negation for floats, wrap-safe integer unary negation, and expression-boundary overloads for every vector component helper. The first green attempt exposed a constraint-template deduction defect in the generic expression/vector helper overloads; replaced it with deducible typed overloads and lane-count constrained generic vector overloads.

3. Reworked `component_min`/`component_max` to match JavaScript `Math.min`/`Math.max` for a NaN in either operand and signed-zero ties, which also flows through `clamp` and `smoothstep`.

4. Reworked `length` to use float32 `dot` and `normalize` to divide by that float32 length. The specified `Vec2(-5968.8544921875f, 15943.099609375f)` normalization now produces x bits `3199435837`, including through a `FloatExpr` consumption boundary.

Final fix-round verification reran the required configure/build/test/CTest commands. Result: 45 named test cases passed; CTest 1/1 passed.

## Fix round 2: double scalar generator arguments

1. Added direct runtime assertions with unsuffixed `double` literals for `clamp`, `mix`, `step`, and `smoothstep`, plus `mix(FloatExpr, FloatExpr, 0.5)`. Red command:

   ```sh
   cmake --build build --parallel
   ```

   Red result: all requested calls failed overload resolution because the original vector helpers deduced their scalar parameter as `float`, while generated scalar expressions are `double`.

2. Added float-vector and `FloatExpr` overloads for component min/max, clamp, mix, step, and smoothstep with `double` scalar forms. Each computes with double scalar terms and calls `f32` once while writing the returned vector lane. Existing vector-bound forms still materialize `FloatExpr` exactly once at the helper boundary.

Final fix-round verification reran the required configure/build/test/CTest commands. Result: 45 named test cases passed; CTest 1/1 passed.
