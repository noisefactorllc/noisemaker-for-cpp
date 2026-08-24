# SpookyTicker pixel oracle

This package freezes the canonical `filter/spookyTicker:spookyTicker` factory. It covers uv/varying aliasing, ticker rows and negative-cell scrolling, glyph indexing and signed/unsigned hashes, renderScale, full-res storage dimensions, time, speed, seed, alpha, repeated tile scans, exact Float32 words, and RGBA8 bytes.

- Schema: `noisemaker-for-cpp.spooky-ticker.pixel-parity.v1`
- Cases: 7; behavioral mutations: 10.
- Every case checks immutable sampler input, retained lifetime, canonical/public identity, and distinct output/input storage.
- Run with: `NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node spooky_ticker_oracle_generator.mjs --check --cpu-root <immutable-cpu-snapshot-root>`
