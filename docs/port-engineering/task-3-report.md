# Task 3 — Bounded deterministic PNG codec

## Files

- `include/noisemaker/png.hpp`: public PNG limits and encode/decode interface.
- `src/png.cpp`: deterministic RGBA encoder and bounded non-interlaced 8-bit decoder.
- `tests/test_png.cpp`: independent PNG fixture construction, filter, CRC, compression, and codec behavior tests.
- `CMakeLists.txt`: system zlib discovery, PNG source, test source, and `ZLIB::ZLIB` links.

## Focused RED/GREEN groups

1. **Deterministic encoder structure**
   - RED command: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug && cmake --build build --parallel && build/noisemaker-cpu-tests`
   - RED result: link failed with undefined `noisemaker::encode_png(noisemaker::Surface const&)` from `png_encoder_writes_deterministic_valid_rgba_png`.
   - GREEN command: `cmake --build build --parallel && build/noisemaker-cpu-tests`
   - GREEN result: `png_encoder_writes_deterministic_valid_rgba_png` passed, independently checking signature, IHDR, chunk order, CRCs, zlib-inflated literal scanline bytes, and repeated-byte determinism.

2. **Decoder formats, filters, bounds, and structure**
   - RED command: `cmake --build build --parallel && build/noisemaker-cpu-tests`
   - RED result: link failed with undefined `noisemaker::decode_png(std::span<const std::uint8_t>)` from the independent decoder fixture tests.
   - GREEN command: `cmake --build build --parallel && build/noisemaker-cpu-tests`
   - GREEN result: all decoder tests passed: literal RGBA round trip; forward-filtered fixtures for filters 0–4; gray/RGB/indexed/gray-alpha/RGBA conversion with tRNS; malformed chunks/order/CRC/header/palette/filter/scanline rejection; pixel and bounded-inflate limits.

## Final verification

```text
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
-- Configuring done
-- Generating done

cmake --build build --parallel
[100%] Built target noisemaker-cpu-tests

build/noisemaker-cpu-tests
28 PASS lines, including all six PNG cases; zero failures.

ctest --test-dir build --output-on-failure
100% tests passed, 0 tests failed out of 1
```

## Self-review

- Encoder emits PNG signature, one canonical IHDR, one level-9 IDAT, and empty IEND; all integers and CRCs are big-endian.
- Decoder validates signature, bounds, CRCs, required ordering, ancillary-versus-critical chunks, format fields, palette/tRNS cardinality, zlib completion/output bounds, filters, palette indices, and top-down RGBA output.
- Fixtures use test-side chunking/CRC/compression and forward filtering, never `encode_png` to validate decoding.

## Concerns

- None known.

## Fix Round 1

### Root cause and RED/GREEN

- Root cause: decoder validity was gated on `!transparency.empty()` rather than the already-recorded `seen_transparency` chunk-presence state. An empty `tRNS` therefore bypassed cardinality/color-type validation. The PLTE parser also did not reject an already-seen tRNS, and 16-bit tRNS samples for 8-bit gray/RGB did not validate their required zero high byte.
- Test helper change: `make_png` now takes `has_transparency`, so empty `tRNS` is distinct from an omitted chunk while preserving independent test-side CRC/chunk/compression construction.
- RED command: `cmake --build build --parallel && build/noisemaker-cpu-tests`
- RED result: `png_decoder_rejects_present_invalid_transparency_and_nonfirst_header` failed at `tests/test_png.cpp:217`: expected `std::invalid_argument` for an empty gray `tRNS`, but decode returned successfully. Existing cases passed.
- Fix: validate tRNS using `seen_transparency`; reject empty indexed tRNS and invalid lengths/color types; reject nonzero high bytes for gray/RGB 8-bit samples; reject PLTE after tRNS; add explicit `<cstdlib>` and `<string>` headers.
- GREEN command: `cmake --build build --parallel && build/noisemaker-cpu-tests`
- GREEN result: all 29 named tests passed, including empty gray/RGBA tRNS, RGB tRNS followed by PLTE, nonzero high-byte gray/RGB tRNS, and ancillary-before-IHDR fixtures.

### Final output

```text
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
-- Configuring done
-- Generating done

cmake --build build --parallel
[100%] Built target noisemaker-cpu-tests

build/noisemaker-cpu-tests
29 PASS lines; zero failures.

ctest --test-dir build --output-on-failure
100% tests passed, 0 tests failed out of 1
```
