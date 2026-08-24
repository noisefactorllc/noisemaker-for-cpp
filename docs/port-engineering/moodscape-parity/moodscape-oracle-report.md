# Moodscape pixel-parity oracle

Authenticated canonical CPU oracle for **classicNoisedeck/moodscape:moodscape** with fixed defines NOISE_TYPE=10 and COLOR_MODE=2. The authority is imported only after a recursively traversed, realpath-confined, literal-import closure of 22 hash-pinned files is authenticated. Bare, escaping, missing, symlinked, and nonliteral imports fail before authority import.

The exact ordered ABI contains the two fixed defines followed by the thirteen source uniforms and binds only the fragColor output; there are no samplers or input textures. Each of six cases executes twice in one process. The comparer checks dimensions and counts before lane access, then every raw little-endian Float32 word and every RGBA8 byte. Distinct surfaces and backing stores, typed-array bits, and all controls are snapshotted and verified unchanged.

Five source mutations are authenticated by exact anchor, replacement, factory, cardinality, independence, and positive Float32/RGBA8 witnesses. The package claims no typed-slice or native integration.

## Reproduction

    NOISEMAKER_FOR_CPU=/Users/aayars/platform/noisemaker-for-cpu node docs/port-engineering/moodscape-parity/moodscape_oracle_generator.mjs --check --cpu-root /private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu
    PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_moodscape_native_oracle_include.py --check
