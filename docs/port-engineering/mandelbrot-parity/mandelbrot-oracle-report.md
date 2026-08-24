# Mandelbrot exact-pixel oracle

This package authenticates the public `synth/mandelbrot:mandelbrot` canonical factory `canonicalFactory252` from an immutable CPU snapshot. It records raw Float32 words and independently captured RGBA8 bytes with zero tolerance.

- Cases: 7; mutation anchors: 21, each with exact source cardinality and an independent witness set.
- Controls: repeat identity, input bit immutability, independent output storage, public/direct factory identity, and adapter-own-key rejection.
- Authority closure: 22 literal-import files, realpath-confined and hash pinned; nonliteral dynamic imports, live checkout roots, and absolute-looking serialization fail closed.
- Run: `node docs/port-engineering/mandelbrot-parity/mandelbrot_oracle_generator.mjs --check --cpu-root "$NOISEMAKER_CPU_ROOT"`; materialize with `python3 tools/glslcpp/generate_mandelbrot_native_oracle_include.py --check`.

JSON SHA-256: e898287f47f0ea2f2676baec9d96fe8f3c1d0f1e124ba61cc7e099840271e574.
