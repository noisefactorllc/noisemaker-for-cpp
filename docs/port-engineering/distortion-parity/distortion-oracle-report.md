# Distortion pixel-parity oracle

Authenticated canonical CPU oracle for **mixer/distortion:distortion**. It covers displacement, refraction, reflection, map-source routing, mirror/repeat/clamp wrapping, chromatic aberration, antialias sampling, tiled coordinates, exact Float32 words, RGBA8 bytes, repeatability, and three independent factory mutation witnesses.

The authority is an unmodified public canonical factory from an immutable CPU snapshot. Its recursively traversed, realpath-confined literal-import closure contains 22 hash-pinned files; bare specifiers, missing/escaping imports, and nonliteral dynamic imports fail before any oracle import executes.

Each canonical run snapshots both `inputTex` and `tex` before `runPass`, then compares exact Float32 words and backing bytes on those same surfaces immediately after the run. The assertion throws on any mutation; each case's `input_immutable: true` flag is emitted only after both checks succeed. The authenticated binding order is `inputTex:Surface/sampler2D`, `tex:Surface/sampler2D`, followed by the ten scalar/vector controls.

The typed landing remains intentionally outside this package. The prepared frontend profile records sampler parameters, six derivative calls, and three mutable local fixed-size arrays as separate blockers.

## Reproduction

node docs/port-engineering/distortion-parity/distortion_oracle_generator.mjs --check --cpu-root \"$NOISEMAKER_CPU_ROOT\"
python3 -B tools/glslcpp/generate_distortion_native_oracle_include.py --check
