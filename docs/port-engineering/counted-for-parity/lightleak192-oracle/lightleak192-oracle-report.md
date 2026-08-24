# LightLeak192 exact-parity oracle

Canonical `filter/lightLeak:lightLeak` from corpus `a024dc3a960cc44af454abc7aebce50456c194e6`; factory `canonicalFactory77`.

The oracle stores complete raw little-endian Float32 words and independently captured RGBA8 bytes for 11 deterministic cases. Each case also stores a source-bound input-texture phase, complete input Float32 words/hash, and complete input RGBA8 bytes/hash; native consumers must use those frozen payloads and never infer phase from case order or reimplement the generator formula. Dimensions, lane counts, signed zero, NaN payloads, repeat identity, input immutability, canonical/public identity, and binding tables are checked exactly.

## Input texture contract

Schema: `noisemaker-for-cpp.lightleak192.input-texture.v1`; source function: `inputSurface`; source-function SHA-256: `31ca4a008de6ab3cfaafc0e0a1ed863153ddf6855d8f43aeb80b76963cc5a990`; coordinate order: x-fastest row-major; component order: r, g, b, a.

## Regeneration

```sh
node docs/port-engineering/counted-for-parity/lightleak192-oracle/lightleak192_oracle_generator.mjs --write --cpu-root "$NOISEMAKER_CPU_ROOT"
node docs/port-engineering/counted-for-parity/lightleak192-oracle/lightleak192_oracle_generator.mjs --check --cpu-root "$NOISEMAKER_CPU_ROOT"
python3 -B tools/glslcpp/generate_lightleak192_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_lightleak192_native_oracle_include.py --check
```

Behavioral mutations: 11; structural-only mutations: 2; frozen CPU import closure files: 22.
