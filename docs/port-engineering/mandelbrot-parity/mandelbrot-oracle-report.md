# Mandelbrot exact-pixel oracle

This package authenticates the public `synth/mandelbrot:mandelbrot` canonical factory `canonicalFactory260` from an immutable CPU snapshot. It records raw Float32 words and independently captured RGBA8 bytes with zero tolerance.

- Cases: 7; mutation anchors: 21, each with exact source cardinality and an independent witness set.
- Controls: repeat identity, input bit immutability, independent output storage, public/direct factory identity, and adapter-own-key rejection.
- Authority closure: 27 literal-import files, realpath-confined and hash pinned; nonliteral dynamic imports, live checkout roots, and absolute-looking serialization fail closed.
- Run: `node docs/port-engineering/mandelbrot-parity/mandelbrot_oracle_generator.mjs --check --cpu-root "$NOISEMAKER_CPU_ROOT"`; materialize with `python3 tools/glslcpp/generate_mandelbrot_native_oracle_include.py --check`.

JSON SHA-256: b2d3b291914734d2fb634d1e2e5f4861457a382716d2616e0e9d2ce7c8511086.
