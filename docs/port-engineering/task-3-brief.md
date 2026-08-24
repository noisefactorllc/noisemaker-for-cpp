# Task 3: Bounded deterministic PNG codec

## Context

Add the in-memory PNG file-format boundary to `.`. `Surface`, byte conversion, sampling, and attachment quantization are approved. This codec must faithfully mirror `../noisemaker-for-cpu/src/node/png.js` for non-interlaced 8-bit PNGs.

## Global constraints

- Read workspace instructions and the force-push postmortem before edits.
- Never invoke Git or indirect Git operations; no branches/worktrees/commits/pushes/PRs/workflows/deploys.
- Use `apply_patch` for every repository/report edit. No repo-local process artifacts.
- Modify only the C++ port and `docs/port-engineering/task-3-report.md`.
- C++20, warnings-as-errors, no Qt or network fetches. System zlib through CMake `find_package(ZLIB REQUIRED)` is the only added dependency.
- Strict TDD per behavior group: focused test first; run and record its specific failure before implementation; minimal implementation; green. Do not call post-implementation mutations original RED evidence.
- Tests construct PNG fixtures independently from the decoder using test-only helpers plus zlib CRC/compress calls; never use `encode_png` to generate a decoder-validation fixture.

## Files and interfaces

- Create `include/noisemaker/png.hpp`, `src/png.cpp`, `tests/test_png.cpp`.
- Modify `CMakeLists.txt` only for the new source/test and `ZLIB::ZLIB` link.

```cpp
namespace noisemaker {

inline constexpr std::size_t max_png_pixels = 16'777'216;
inline constexpr std::size_t max_png_encoded_bytes = 256U * 1024U * 1024U;
inline constexpr std::size_t max_png_decoded_bytes = 96U * 1024U * 1024U;

[[nodiscard]] std::vector<std::uint8_t> encode_png(const Surface& surface);
[[nodiscard]] Surface decode_png(std::span<const std::uint8_t> png);

} // namespace noisemaker
```

Throw `std::invalid_argument` for malformed/unsupported content, `std::overflow_error` for configured size bounds, and `std::runtime_error` for zlib failures that are not caused by an exceeded output bound. Error messages must name the violated PNG structure (signature, chunk type/CRC/order, bit depth, color type, interlace, scanline length/filter, palette, tRNS, or size limit).

## Encoder contract

- Input is a validated positive `Surface`, capped at `max_png_pixels`.
- Output is deterministic within the same zlib build: signature, one 13-byte `IHDR` (8-bit RGBA color type 6, compression/filter/interlace methods 0), one `IDAT`, one empty `IEND`.
- Scanlines are top-down and each begins with filter byte 0.
- Use zlib level 9. CRC covers type+data. Big-endian chunk lengths/CRC and IHDR dimensions.
- Test literal Surface bytes: `2x1 [255,0,0,255, 0,128,255,64]`. Parse output independently; assert signature bytes, chunk type sequence, dimensions/header fields, CRCs, and independently inflate IDAT to literal `[0,255,0,0,255,0,128,255,64]`. Two encodes must be byte-identical.

## Decoder contract

- Reject encoded input above 256 MiB before parsing.
- Require exact PNG signature; exactly one first `IHDR`; valid chunk bounds and CRC; consecutive `IDAT` after IHDR; empty `IEND` after IDAT; no trailing bytes.
- Ignore ancillary chunks only; reject unknown critical chunks. Enforce legal PLTE/tRNS ordering and cardinality.
- Dimensions positive and at most 16,777,216 pixels with overflow-safe arithmetic.
- Only bit depth 8, compression/filter method 0, interlace 0.
- Accept color types 0 gray, 2 RGB, 3 indexed, 4 gray-alpha, 6 RGBA. Validate palettes, indices, and tRNS lengths/rules.
- Bounded zlib inflate: exact expected `(stride+1)*height`, maximum 96 MiB, fail if stream expands beyond expected or has invalid/trailing compressed structure.
- Decode all PNG row filters 0 None, 1 Sub, 2 Up, 3 Average, 4 Paeth with unsigned-byte wrapping.
- Output is top-down RGBA `Surface` via `Surface::from_rgba8`.

## Required decoder tests

1. Round-trip a literal 3x2 RGBA surface through encode/decode and compare dimensions/RGBA8.
2. Independent hand-built 2x2 RGBA PNG fixtures for each filter 0..4 decode to the same literal 16 RGBA bytes. Test helper must apply forward filtering itself.
3. Independent 1x1 fixtures cover:
   - gray value 7 -> `[7,7,7,255]`; gray+tRNS sample 7 -> alpha 0;
   - RGB `[1,2,3]` -> alpha 255; RGB+tRNS `[1,2,3]` -> alpha 0;
   - indexed palette entry `[10,20,30]` with tRNS alpha 40;
   - gray-alpha `[7,9]` -> `[7,7,7,9]`;
   - RGBA `[1,2,3,4]` unchanged.
4. Structural rejection fixtures: wrong signature; truncated chunk; corrupt IHDR CRC; duplicate/not-first IHDR; nonconsecutive IDAT; nonempty or missing IEND; trailing data; unknown critical chunk; invalid bit depth; interlace; unsupported color type; invalid palette; out-of-range palette index; illegal tRNS.
5. Bounds: independently build an IHDR with width 16,777,217 and assert pixel-limit overflow; independently build a 1x1 RGBA header whose IDAT inflates to 1 MiB and assert bounded-inflate failure.
6. Invalid scanline filter 5 and wrong decompressed scanline length are rejected.

## Verification

End with fresh:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
build/noisemaker-cpu-tests
ctest --test-dir build --output-on-failure
```

All named cases pass; zero warnings.

## Report

Write `docs/port-engineering/task-3-report.md`. Include files, each focused RED/GREEN group, exact commands/failure reason/results, final output, self-review, concerns. Return only status, one-line test summary, concerns.
