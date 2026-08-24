# OSD pixel oracle

This package freezes the canonical `filter/osd:osd` factory from the immutable CPU authority. It covers four corner modes, alpha-zero early return, full-resolution fallback with tile offset, renderScale, glyph hash/indexing, integer texture fetch, scanline bitwise masking, and panel geometry.

- Schema: `noisemaker-for-cpp.osd.pixel-parity.v1`
- Cases: 7
- Behavioral mutations: 6; every mutation has an actual float32 and RGBA8 witness.
- Float32 comparison is exact little-endian word equality; RGBA8 comparison is exact byte equality.
- Run with: `node osd_oracle_generator.mjs --check --cpu-root $NOISEMAKER_CPU_ROOT`
- Materialize with: `python3 -B tools/glslcpp/generate_osd_native_oracle_include.py --check`

The input fixture is source-bound by function text hash and frozen independently as Float32 words and RGBA8 bytes. The input Surface is checked for exact bitwise immutability and retained across repeat renders.
