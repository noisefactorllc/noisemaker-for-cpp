# Task 4: typed GLSL value and binding ABI

## Objective

Add the native, strongly typed value/runtime seam that generated C++ kernels will call. Keep `std::variant` and name lookup at the one-time external binding boundary; no variant, maps, allocation, or string lookup belongs in a future per-pixel kernel body.

This task does not add the generator, renderer, pass graph, derivatives, or CLI.

## Workflow and constraints

- Work only in `.`.
- Do not invoke Git or any indirect Git operation. Do not create branches, worktrees, commits, or PRs.
- Follow strict test-first implementation: add one focused failing test, run it and capture the expected failure, add the minimum production code, run it green, then continue.
- Do not create process/spec/report documents in the repository. Append evidence to `docs/port-engineering/task-4-report.md`.
- Use C++20, standard library, and the existing zlib dependency only.
- Do not use fast-math. Add `-ffp-contract=off` for Clang/GNU to the library and test target so future generated kernels inherit deterministic contraction behavior.
- Preserve existing APIs and all existing tests.

## Files

Create:

- `include/noisemaker/glsl_types.hpp`
- `include/noisemaker/glsl_runtime.hpp`
- `src/glsl_runtime.cpp`
- `tests/test_glsl_types.cpp`
- `tests/test_glsl_runtime.cpp`

Modify only `CMakeLists.txt` in addition to those files.

## Public value types

In namespace `noisemaker::glsl`:

```cpp
template <std::size_t N, class T>
class Vec;

using Vec2 = Vec<2, float>;
using Vec3 = Vec<3, float>;
using Vec4 = Vec<4, float>;
using IVec2 = Vec<2, std::int32_t>;
using IVec3 = Vec<3, std::int32_t>;
using IVec4 = Vec<4, std::int32_t>;
using UVec2 = Vec<2, std::uint32_t>;
using UVec3 = Vec<3, std::uint32_t>;
using UVec4 = Vec<4, std::uint32_t>;
using BVec2 = Vec<2, bool>;
using BVec3 = Vec<3, bool>;
using BVec4 = Vec<4, bool>;

template <std::size_t N>
class Mat;
using Mat2 = Mat<2>;
using Mat3 = Mat<3>;
using Mat4 = Mat<4>;
```

### `Vec` contract

- Backed by `std::array<T,N>` with value semantics and bounds-checked `at()` plus unchecked `operator[]`.
- Default construction zero-initializes all lanes.
- Scalar construction splats.
- Exact-lane construction accepts exactly N values.
- Flattening construction supports the combinations required by GLSL constructors, at minimum `Vec4(Vec3, scalar)`, `Vec3(Vec2, scalar)`, and `Vec4(Vec2, Vec2)`. Invalid lane counts must be rejected at compile time.
- Explicit cross-base conversion uses GLSL rules: float to signed/unsigned integer truncates toward zero; integer to float narrows through the destination float. Avoid undefined behavior for non-finite/out-of-range float-to-int conversion: define deterministic helpers in the runtime instead of raw casts.
- Equality compares lanes exactly.
- `swizzle<I...>(v)` returns a new typed vector for 2-4 indices and the scalar lane for one index. Indices are compile-time checked.
- `set_swizzle<I...>(target, value)` writes from a temporary copy first, so overlapping assignments such as `set_swizzle<0,1>(v, swizzle<1,0>(v))` are alias-safe. Repeated destination lanes are rejected at compile time.
- Component-wise arithmetic supports vector-vector and vector-scalar/scalar-vector for `+ - * /`; signed/unsigned integer addition/subtraction/multiplication wrap at 32 bits without UB. Division by zero for integer types returns zero per the sibling CPU runtime. Signed division truncates toward zero. Shift/bitwise helpers may live in `glsl_runtime.hpp` rather than operators.
- **Parity-critical deferred rounding:** `Vec<N,float>` is a GLSL storage value, but chained floating vector arithmetic must not narrow after every operator. Add a double-backed expression value (for example `FloatExpr<N>`) used as the result of floating vector/vector and vector/scalar operators. Operator chains remain double-backed; construction or assignment into `Vec<N,float>`, vector builtins, function-argument consumption, swizzle consumption, and output storage narrow lanes once with `numeric::f32`. The later generator will declare GLSL vector variables as `Vec`, so ordinary declaration/assignment is the storage boundary. This matches the sibling port's proven rule that compound expressions evaluate in float64 and narrow at consumption boundaries. Integer vector operators still return integer `Vec` immediately.
- Floating operations preserve IEEE NaN/Inf. Scalar shader expressions will be modeled as `double` by the generator; do not add a custom scalar wrapper in this task.

### `Mat` contract

- Column-major storage as `std::array<Vec<N,float>,N>`; `operator[](column)` returns a column.
- Default construction is all zero. Scalar construction produces a diagonal matrix.
- Construct from exactly N columns.
- Implement matrix-vector, vector-matrix, and matrix-matrix multiplication with float64 accumulation and one float32 narrowing per output lane.

## Core runtime contract

In `glsl_runtime.hpp/.cpp`, add focused typed helpers needed by generated kernels:

```cpp
double mod(double x, double y);       // x - y * floor(x/y)
double fract(double x);
double round(double x);               // GLSL/JS contract: floor(x + 0.5)

template <std::size_t N> float dot(const Vec<N,float>& a, const Vec<N,float>& b);
template <std::size_t N> float length(const Vec<N,float>& v);
template <std::size_t N> Vec<N,float> normalize(const Vec<N,float>& v);
Vec3 cross(const Vec3& a, const Vec3& b);
template <std::size_t N> Vec<N,float> reflect(const Vec<N,float>& incident, const Vec<N,float>& normal);
template <std::size_t N> Vec<N,float> refract(const Vec<N,float>& incident, const Vec<N,float>& normal, double eta);

template <class T> T component_min(T a, T b);
template <class T> T component_max(T a, T b);
template <class T> T clamp(T x, T low, T high);
template <class T> T mix(T x, T y, T amount);
template <class T> T step(T edge, T x);
template <class T> T smoothstep(T edge0, T edge1, T x);
```

Provide vector overloads for the component-wise helpers with scalar splat arguments where useful. Each returned floating vector is float32-backed. Transcendental families can wait for the next runtime-completion task; do not expand scope merely to add every GLSL builtin.

Reuse existing `numeric.hpp` for `f32`, bit/half/PCG authority. Do not duplicate those implementations.

## Typed external bindings

```cpp
using UniformValue = std::variant<
  float, std::int32_t, std::uint32_t, bool,
  Vec2, Vec3, Vec4,
  IVec2, IVec3, IVec4,
  UVec2, UVec3, UVec4,
  BVec2, BVec3, BVec4,
  Mat2, Mat3, Mat4>;

class KernelBindingError : public std::runtime_error { ... };

class Bindings {
 public:
  void set_uniform(std::string name, UniformValue value);
  void set_texture(std::string name, const noisemaker::Surface& surface);

  template <class T>
  T get_or(std::string_view name, const T& fallback) const;

  const noisemaker::Surface& texture(std::string_view name) const;
};

struct PixelContext {
  Vec2 uv{};
  Vec4 frag_coord{};
  Vec2 resolution{};
  float time{};
  float seed{};
  std::uint32_t frame{};
  float delta_time{};
};
```

- A missing scalar/vector/matrix uniform returns the supplied generated fallback.
- A present uniform with the wrong exact variant alternative throws `KernelBindingError`; no numeric coercion at this boundary.
- A missing required sampler throws `KernelBindingError`.
- `set_texture` stores a non-owning pointer/reference; document that the `Surface` must outlive the binding and kernel using it.
- Empty names are rejected by both setters with `KernelBindingError`.
- Error messages include the binding name and whether it is a uniform or sampler; do not expose implementation-specific mangled type names.
- A generated factory will later call `get_or<T>`/`texture()` exactly once and capture typed values. This task need not define a kernel base class.

## Required tests

Add direct named tests for at least:

1. zero, splat, exact-lane, and flattening vector construction;
2. compile-time properties (`static_assert` constructibility/non-constructibility where relevant);
3. cross-base conversions including truncation and deterministic non-finite/out-of-range behavior;
4. deferred float-vector expression rounding, final storage narrowing, and IEEE NaN/Inf propagation. Include the exact sentinel `a=30570110.0f`, `b=35727780.0f`, `c=0.9301421642303467f`: a chained vector expression stored once must produce float32 bits `1283254281`, while per-operation narrowing would incorrectly produce `1283254280`;
5. wrapping signed/unsigned arithmetic and zero integer division;
6. scalar/vector arithmetic in both operand orders;
7. swizzle reads and alias-safe overlapping swizzle writes;
8. column-major matrix indexing and all three multiplication directions using non-symmetric fixtures;
9. `mod(-1,3)==2`, `fract(-1.25)==0.75`, round tie/negative behavior;
10. dot/length/normalize zero and nonzero vectors, cross, reflect, total-internal-reflection refract;
11. min/max/clamp/mix/step/smoothstep scalar and representative vector behavior;
12. uniform found, missing fallback, exact-type mismatch, empty-name rejection;
13. texture found by reference identity, missing failure, empty-name rejection;
14. `PixelContext` zero defaults.

Use bit-pattern assertions where rounding is the behavior under test. Tests must not merely reimplement the production formula as their oracle.

## Verification

Run and record:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
build/noisemaker-cpu-tests
ctest --test-dir build --output-on-failure
```

## Report

Write `docs/port-engineering/task-4-report.md` with:

- exact test-first red/green commands and concise observed failures/successes;
- files changed;
- API/semantic decisions made within this brief;
- final test counts;
- any remaining concern, especially any behavior that cannot honestly be claimed as original red-before-production evidence.
