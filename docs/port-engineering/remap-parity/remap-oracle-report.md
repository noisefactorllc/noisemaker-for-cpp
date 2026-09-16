# Remap exact-pixel CPU oracle

Authenticated `synth/remap:remap` against an immutable CPU snapshot and the hand-written `remapFactory` adapter (semantic uniforms, not the packed std140 RemapUniforms array -- that array now feeds only the retired generated-kernel path). Exact Float32 words and independently captured RGBA8 bytes are required.

- Cases: 14; source mutants: 7.
- Authority closure: 23 literal-import files.
- JSON SHA-256: dcb49b8e0b18ae3af45c2567d0f62788188cb5af90b2145e041b2c50311f363a.
