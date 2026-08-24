# Task 2: GLSL texture sampling and attachment quantization

## Context

Extend `.` with the image-semantics layer required by generated CPU kernels. `Surface` and numeric/half primitives already exist and pass their Task 1 gate.

## Global constraints

- Read `../AGENTS.md` and `../POSTMORTEM-2026-07-14-NOISEMAKER-FORCE-PUSH.md` before changes.
- Never invoke Git, `gh`, branches, worktrees, commits, pushes, PRs, workflows, or deploys.
- Do not create repository-local process artifacts.
- Use `apply_patch` for every repository/report file edit.
- Modify only `.` and `docs/port-engineering/task-2-report.md`.
- C++20, portable standard library, no Qt/network-fetched dependencies, warnings-as-errors.
- Strict TDD: add one focused behavior test at a time, run it before its implementation and record the behavior-specific compile/link/assertion failure, implement minimally, rerun green, then continue. Do not use a single coarse missing-file failure as evidence for all behaviors.
- Expected values must be literals or hand-derived fixtures, not computed with the implementation under test.

## Files

- Create `include/noisemaker/sampler.hpp` and `src/sampler.cpp`.
- Create `include/noisemaker/texture_format.hpp` and `src/texture_format.cpp`.
- Create `tests/test_sampler.cpp` and `tests/test_texture_format.cpp`.
- Modify `CMakeLists.txt` only to add the new production/test sources.

## Interfaces

```cpp
namespace noisemaker {

using Rgba = std::array<float, 4>;

[[nodiscard]] Rgba sample_nearest_top_down(const Surface&, double u, double v) noexcept;
[[nodiscard]] Rgba sample_nearest_bottom_left(const Surface&, double u, double v) noexcept;
[[nodiscard]] Rgba sample_bilinear_bottom_left(const Surface&, double u, double v) noexcept;
[[nodiscard]] Rgba texel_fetch_bottom_left(const Surface&, int x, int y) noexcept;

enum class TextureFormat { rgba16f, rgba8_unorm, rgba32f };
Surface& quantize_texture(Surface&, TextureFormat format) noexcept;

} // namespace noisemaker
```

All samplers clamp to edge. Surface storage is top-down. GLSL nearest and texel-fetch APIs address rows bottom-up by computing the clamped integer shader row first and then `storage_y = height - 1 - shader_y`; do not implement the nearest flip as normalized `1-v`. Bilinear uses half-texel centers, bottom-left integer row addressing, double intermediates, then exactly one `f32` narrowing per output channel.

`rgba16f` uses existing `float16_truncate` channel-by-channel. `rgba8_unorm` maps non-finite to zero, clamps, rounds positive interior with `floor(value*255 + 0.5)`, and stores the normalized float byte value. `rgba32f` is an explicit bit-preserving no-op.

## Literal sampler fixture and tests

Use this 2x2 top-down Surface (four float RGBA texels in storage order):

```text
top-left     = [0,    0.25, 0.5,  1]
top-right    = [0.25, 0.5, 1,    0]
bottom-left  = [0.5,  1,    0,    0.25]
bottom-right = [1,    0,    0.25, 0.5]
```

Tests:

- top-down nearest at `(0.25,0.25)` is top-left; `(0.75,0.75)` is bottom-right.
- bottom-left nearest at `(0.25,0.25)` is bottom-left; `(0.75,0.25)` bottom-right; `(0.25,0.75)` top-left; `(0.75,0.75)` top-right.
- exact boundary regression: bottom-left nearest at `v=0.5` selects the top storage row; this catches the incorrect `sample(..., 1-v)` implementation.
- deep out-of-range coordinates clamp: `(-100,-100)` is bottom-left and `(100,100)` top-right for bottom-left nearest.
- bottom-left bilinear at all four exact half-texel centers returns the respective named texel.
- bottom-left bilinear at `(0.5,0.5)` is literal `[0.4375,0.4375,0.4375,0.4375]` (the hand-derived channel average).
- bilinear deep out-of-range clamps to edge texels.
- `texel_fetch_bottom_left(surface,0,0)` is bottom-left, `(1,1)` is top-right, and out-of-range integer coordinates clamp.

## Literal texture-format tests

- `float16_truncate(0.1f)` is already covered; `quantize_texture` on `[0.1f,0.3333f,1.5f,-0.25f]` with `rgba16f` must yield literal `[0.0999755859375f,0.333251953125f,1.5f,-0.25f]`.
- `rgba8_unorm` on `[0.1f,0.5f,2.0f,-1.0f]` converts back via `to_rgba8()` to `[26,128,255,0]`.
- `rgba8_unorm` maps `NaN`, positive infinity, and negative infinity to zero.
- `rgba32f` preserves the exact `float_bits_to_uint` patterns of all channels, including signed zero and a quiet NaN payload.

## Verification

Run focused red/green commands during implementation. End with:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Zero warnings, all tests pass.

## Report

Write `docs/port-engineering/task-2-report.md` with `apply_patch`. Include exact red failure per behavior group, exact green results, final full-suite output, self-review, and concerns. Return only status, one-line test summary, concerns.
