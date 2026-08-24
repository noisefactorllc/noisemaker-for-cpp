# Newton exact-pixel oracle

- Program: synth/newton:newton
- Authority: unmodified public canonicalFactory264 from an immutable CPU snapshot.
- Cases: 8; exact mutation ledger entries: 16.
- The checked closure has 22 files and is realpath-confined; literal dynamic imports are traversed and nonliteral imports are rejected.
- Controls include repeatability, direct public identity, independent output storage, and exact input Float32-bit immutability.
- Compare with raw Float32 words and independently captured RGBA8 bytes; tolerance is none.

## Reproduction

node docs/port-engineering/newton-parity/newton_oracle_generator.mjs --check --cpu-root "$NOISEMAKER_CPU_ROOT"
python3 -B tools/glslcpp/generate_newton_native_oracle_include.py --check

Absolute checkout paths are intentionally omitted from this report and JSON.
