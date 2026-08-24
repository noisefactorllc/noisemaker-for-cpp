# Task 1: C++20 foundation, Surface, and numeric fidelity primitives

## Context

Create the new sibling project at `.`. It is a native C++ CPU port of `../noisemaker-for-cpu`. This task establishes the standalone build/test foundation and the low-level data/numeric contracts every later generated kernel and renderer task will consume.

## Global constraints

- Read `../AGENTS.md` and `../POSTMORTEM-2026-07-14-NOISEMAKER-FORCE-PUSH.md` before changes.
- Never invoke Git, `gh`, branches, worktrees, commits, pushes, PRs, workflows, or deploys.
- Do not create repository-local agent plans, reports, scratch docs, or other process artifacts.
- Use `apply_patch` for every repository file edit.
- Preserve scope: only create `.`; do not modify sibling repositories.
- Use C++20 and portable standard-library facilities. No Qt dependency. No network-dependent CMake fetches.
- Follow strict TDD: write each behavioral test first, run it and record the expected failure, then implement minimal code, then run the focused test and the full suite.
- Build with warnings enabled and treated as errors for project sources on Clang/GCC.

## Files and responsibilities

- Create `CMakeLists.txt`: project `noisemaker-for-cpp`, C++20, library target `noisemaker-cpu`, test executable `noisemaker-cpu-tests`, CTest registration. Support the default Unix Makefiles generator because Ninja is unavailable locally.
- Create `.gitignore`: only build/editor/cache artifacts; no source or generated bundle exclusions.
- Create `include/noisemaker/surface.hpp` and `src/surface.cpp`: `noisemaker::Surface`.
- Create `include/noisemaker/numeric.hpp` and `src/numeric.cpp`: fidelity primitives.
- Create a tiny dependency-free test harness under `tests/` and focused `test_surface.cpp`, `test_numeric.cpp`. Tests must assert real outputs using literal independently derived expectations.

## Required interfaces

```cpp
namespace noisemaker {

class Surface {
public:
  Surface(std::size_t width, std::size_t height);
  Surface(std::size_t width, std::size_t height, std::vector<float> data);

  static Surface from_rgba8(std::size_t width, std::size_t height,
                            std::span<const std::uint8_t> bytes);
  [[nodiscard]] std::size_t width() const noexcept;
  [[nodiscard]] std::size_t height() const noexcept;
  [[nodiscard]] std::span<float> data() noexcept;
  [[nodiscard]] std::span<const float> data() const noexcept;
  [[nodiscard]] Surface clone() const;
  Surface& clear(const std::array<float, 4>& color = {0, 0, 0, 0});
  [[nodiscard]] std::vector<std::uint8_t> to_rgba8() const;
};

[[nodiscard]] float f32(double value) noexcept;
[[nodiscard]] double glsl_mod(double x, double y) noexcept;
[[nodiscard]] double glsl_round(double value) noexcept; // floor(value + 0.5)
[[nodiscard]] std::uint32_t umul(std::uint32_t a, std::uint32_t b) noexcept;
[[nodiscard]] std::uint32_t hash_uint32(std::uint32_t value) noexcept;
[[nodiscard]] std::array<std::uint32_t, 3>
pcg3d(std::array<std::uint32_t, 3> value) noexcept;
[[nodiscard]] std::uint32_t float_bits_to_uint(float value) noexcept;
[[nodiscard]] float uint_bits_to_float(std::uint32_t value) noexcept;
[[nodiscard]] std::uint16_t float_to_half_rte(float value) noexcept;
[[nodiscard]] float half_to_float(std::uint16_t bits) noexcept;
[[nodiscard]] float float16_truncate(float value) noexcept;

} // namespace noisemaker
```

Use `std::bit_cast` for float/uint bit reinterpretation. Integer overflow must be well-defined unsigned wraparound. Surface constructor dimensions must be positive and `width * height * 4` must be overflow-checked before allocation. A supplied data vector must have exactly that length.

## Required literal test vectors

Surface:

- `Surface(0, 1)`, `Surface(1, 0)`, and overflowing dimensions throw `std::invalid_argument` or `std::overflow_error` as appropriate.
- `from_rgba8(2,1,[255,0,0,255, 0,128,255,64])` yields float data `[1,0,0,1, 0,128/255,1,64/255]` rounded into `float`.
- `clear({0.25f,0.5f,0.75f,1})` fills every pixel; `clone()` does not alias source storage.
- `to_rgba8()` maps `NaN,+Inf,-Inf,-0.1,0,0.5,1,1.1` according to the JS contract: every non-finite to 0, clamp to [0,255], `floor(value*255 + 0.5)` for positive finite interior values. In particular `0.5 -> 128`.

Numeric:

- `glsl_mod(-1,3) == 2`.
- `glsl_round(0.5)==1`, `glsl_round(-0.5)==0`, `glsl_round(-1.5)==-1`.
- `umul(0xffffffffu, 374761393u) == 3920205903u`.
- `hash_uint32(0x1234abcdu) == 737574769u`.
- `pcg3d({1,2,3}) == {4204755366u,1223881804u,1500469937u}`.
- Float bit round trips cover `0`, `-0`, `1`, infinity, and a quiet NaN classification.
- IEEE half conversion covers `0`, `-0`, `1`, max finite `65504`, positive/negative infinity, NaN classification, the smallest subnormal `0x0001`, and a halfway case proving round-to-nearest-even.
- `float16_truncate(1.0009f)` equals the decoded half obtained by discarding lower mantissa bits, not the RTE result; finite overflow clamps to half max finite with sign; infinities stay infinite; NaN stays NaN.

## Verification commands

Configure and build in a disposable repo-local `build/` directory:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The final output must contain zero compiler warnings and all tests passing.

## Report

Write the detailed report to `docs/port-engineering/task-1-report.md` using `apply_patch`. Include: files created, each red command/failure reason, each green command/result, full-suite result, self-review notes, and any concerns. Return only `DONE`, a one-line test summary, and concerns.
