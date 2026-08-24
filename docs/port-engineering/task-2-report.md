# Task 2 report: GLSL sampling and texture formats

## Implemented scope

- Added `sampler.hpp/.cpp`: top-down nearest, GLSL bottom-left nearest,
  half-texel bottom-left bilinear, and clamped bottom-left `texelFetch`.
- Added `texture_format.hpp/.cpp`: channel-wise `rgba16f`, finite/clamped and
  rounded `rgba8_unorm`, and explicit bit-preserving `rgba32f` no-op.
- Added literal-fixture tests and registered the new production/test sources in
  CMake.

## Focused red/green evidence

| Behavior group | RED evidence | GREEN result |
| --- | --- | --- |
| Top-down nearest | Linker: `Undefined symbols ... sample_nearest_top_down(...)` from `sampler_nearest_top_down_uses_surface_storage_rows` | Test executable passed the two top-down fixture assertions. |
| Bottom-left nearest | Linker: `Undefined symbols ... sample_nearest_bottom_left(...)` from `sampler_nearest_bottom_left_uses_glsl_row_addressing_and_clamps` | Fixture corners, `v=0.5` regression, and deep out-of-range clamps passed. |
| Bottom-left bilinear | Linker: `Undefined symbols ... sample_bilinear_bottom_left(...)` from `sampler_bilinear_bottom_left_uses_half_texel_centers_and_edge_clamping` | Four exact centers, literal center average, and deep edge clamps passed. |
| Bottom-left integer fetch | Linker: `Undefined symbols ... texel_fetch_bottom_left(...)` from `sampler_texel_fetch_bottom_left_addresses_integer_rows_and_clamps` | Bottom-left/top-right addressing and integer edge clamps passed. |
| `rgba16f` | Linker: `Undefined symbols ... quantize_texture(...)` from `texture_format_rgba16f_truncates_each_channel` | Literal truncated `[0.0999755859375, 0.333251953125, 1.5, -0.25]` passed. |
| `rgba8_unorm` stored bytes | Initial output-only test was rejected because `Surface::to_rgba8()` could mask a no-op. After direct stored-bit assertions, RED was `FAIL texture_format_rgba8_unorm_clamps_and_rounds_to_normalized_bytes ... data[0] == 0x3dd0d0d1U`. | Stored normalized byte float bits and `to_rgba8()` literal `[26,128,255,0]` passed. |
| `rgba8_unorm` nonfinite (mutation-based regression-sensitivity validation) | This is not RED-before-implementation evidence. A mutation check returned `FAIL texture_format_rgba8_unorm_maps_nonfinite_channels_to_zero ... data[0] == 0x00000000U` when nonfinites were deliberately mapped to 255; the correct implementation was immediately restored. | NaN, +infinity, and -infinity all stored exact positive zero; the finite channel stored `64/255`. |
| `rgba32f` bit preservation (mutation-based regression-sensitivity validation) | This is not RED-before-implementation evidence. A mutation check returned `FAIL texture_format_rgba32f_preserves_every_channel_bit_pattern ... data[0] == 0x80000000U` when the explicit no-op case was deliberately changed to overwrite channel zero; the correct implementation was immediately restored. | Signed zero, quiet-NaN payload `0x7fc12345`, negative infinity, and 1.0 all retained their exact bits. |

## Final verification

Command:

```text
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Exact final CTest output:

```text
Test project build
    Start 1: noisemaker-cpu-tests
1/1 Test #1: noisemaker-cpu-tests .............   Passed    0.19 sec

100% tests passed, 0 tests failed out of 1

Total Test time (real) =   0.19 sec
```

The test executable also reported all 20 cases as `PASS`; compilation completed with the configured `-Wall -Wextra -Wpedantic -Werror` flags and no warnings.

## Self-review

- The bottom-left nearest sampler computes the clamped shader row before
  translating it to `height - 1 - shader_y`; it does not use `1-v`.
- Bilinear addressing uses `uv * size - 0.5`, bottom-left integer rows, double
  interpolation intermediates, and one float narrowing assignment per channel.
- Texture expectations use literals / fixed bit patterns rather than values
  computed by the code under test.
- Scope is limited to the six requested source/test files, CMake registration,
  and this required report. No Git or external state-changing operations ran.

## Concerns

None.

## Fix Round 1

### Bilinear nonfinite coordinates

- Added `sampler_bilinear_bottom_left_clamps_infinities_and_propagates_nan` before changing production code. It uses only hand-derived literals: negative/positive infinite `u` with `v=0.5` yield the left/right column blends `[0.25, 0.625, 0.25, 0.625]` and `[0.625, 0.25, 0.625, 0.25]`; negative/positive infinite `v` with `u=0.5` yield the bottom/top row blends `[0.75, 0.5, 0.125, 0.375]` and `[0.125, 0.375, 0.75, 0.5]`. A NaN coordinate must make every output channel NaN.
- RED command: `cmake --build build --target noisemaker-cpu-tests --parallel && build/noisemaker-cpu-tests`
- Exact red behavior: `FAIL sampler_bilinear_bottom_left_clamps_infinities_and_propagates_nan: tests/test_sampler.cpp:23: requirement failed: test::nearly_equal(actual[channel], expected[channel])`. The pre-fix `infinity - infinity` weight was NaN.
- GREEN command: same focused build/executable command. Result: `PASS sampler_bilinear_bottom_left_clamps_infinities_and_propagates_nan` and all then-21 executable cases passed.
- Minimal fix: clamp both half-texel coordinates to `[0, width-1]` / `[0, height-1]` before `floor` and weight calculation. `std::clamp` leaves NaN unchanged, preserving JS NaN propagation.

### Invalid texture enum fallback

- Added `texture_format_invalid_enum_is_a_bit_preserving_no_op` before changing production code. It casts sentinel `999`, asserts the returned reference is the original surface, and checks the exact signed-zero, quiet-NaN payload, negative-infinity, and 1.0 bit patterns.
- Pre-fix focused build/executable invocation produced no executable output. The safely observable focused CTest command, `ctest --test-dir build --output-on-failure`, then reported `1/1 Test #1: noisemaker-cpu-tests .............SIGTRAP***Exception: 0.01 sec` and `0% tests passed, 1 tests failed out of 1`. This is deterministic Debug evidence of the prior fall-through undefined behavior, not an assertion failure.
- GREEN command: `cmake --build build --target noisemaker-cpu-tests --parallel && build/noisemaker-cpu-tests`. Result: `PASS texture_format_invalid_enum_is_a_bit_preserving_no_op` and all then-22 executable cases passed.
- Minimal fix: add `return surface;` after the exhaustive `TextureFormat` switch, preserving data and reference identity for invalid underlying values.

### Fix Round 1 final verification

```text
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

```text
Test project build
    Start 1: noisemaker-cpu-tests
1/1 Test #1: noisemaker-cpu-tests .............   Passed    0.00 sec

100% tests passed, 0 tests failed out of 1

Total Test time (real) =   0.00 sec
```
