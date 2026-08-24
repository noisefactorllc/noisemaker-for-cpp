# Classic Noise exact-pixel CPU oracle

Authenticated canonicalFactory12 for **classicNoisedeck/noise:noise** from an external immutable CPU snapshot with fixed defines NOISE_TYPE=10, COLOR_MODE=6, REFRACT_MODE=2, LOOP_OFFSET=300, METRIC=0. The package binds all 24 uniforms plus five defines. Dead bindings are checked for acceptance and invariance, never presented as branch coverage.

Comparison is exact raw little-endian Float32 words and complete RGBA8 bytes. Dimensions and counts precede lane access. Eight cases execute twice with independent output storage, unchanged controls, and retained input state. Five independent factory mutations require positive Float32/RGBA8 witnesses.

Reproduction:

    NOISEMAKER_FOR_CPU=/Users/aayars/platform/noisemaker-for-cpu node docs/port-engineering/classic-noise-parity/classic_noise_oracle_generator.mjs --check --cpu-root /private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu
    PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_classic_noise_native_oracle_include.py --check
