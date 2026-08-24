# Test Pattern pixel-parity oracle

Program: `synth/testPattern:testPattern`. Source: `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/testPattern/testPattern.glsl` (5919 bytes, `f913300a1312c6630d56fa1cc2faf2cb17fe0643d832473fdec7b66dd373cb20`).

Input contract: **source-only**. Test Pattern has no sampler or input texture path; no input lifetime or immutability claim is made.

Cases: **9**. Behavioral mutants: **9**, each has Float32 and RGBA8 witnesses. Structural-only mutants: **2**.

| Case | Size | Pattern | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | ---: | ---: | --- | --- |
| checker-hundreds-digit | 1x1 | 0 | f6bb1294da2f78cd935b01c7656280df5eaa0439e9d97bc03775825a41a508e4 | ad95131bc0b799c0b1af477fb14fcf26a6a9f76079e48bf090acb7e8367bfd0e |
| checker-single-digit | 1x1 | 0 | 7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e | e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332 |
| checker-grid-clamp | 2x2 | 0 | 9628e545ed3ac074e5a6cbf542a642b62482fbfca9b4cb3ea4743a1874256e37 | 5ac6a5945f16500911219129984ba8b387a06f24fe383ce4e81a73294065461b |
| color-bars | 8x1 | 1 | 6db8f03150c8a0c7721300683cc43b5eae30cd2a528113f6bf127769c45f3b03 | 856c5f8dcc3ef73f3bae698cde3c0aa91d26a35638aae001fcc2ee1b08eaf5e0 |
| gradient-nonsquare | 4x3 | 2 | 28d6aa59331d654196bd4696252c3e81370e09a8dcac8a2e836e363adc345798 | b2e526d8f801cf1a080e4a54eaec499dfb9224e94e2d29c5961c9c1b89a414a2 |
| uv-map-tile | 3x2 | 3 | 462ac905c1671ec6cbbf7ff9817d6e57d88e24793d73a96126b8514e4dec0420 | 2b2c6c1decfe3f06f0be5e78e77d88a654933406e9214788d87fba15a3f8fe53 |
| grid-lines | 5x4 | 4 | eb66ad4ac07d220d72032a42d732cf266339da9c8566093c868b8285d4ec033c | 89c7c79931afa67d559f7cf332ab5a65a379ebf5e4fa2d997535c364af2c24a8 |
| color-grid | 4x3 | 5 | a5fe647f7b56090d8fd56ad17be335977cc423f97c6fdba7a60c8d5d300aaf19 | e1396e97656f8095d998762f0c08d1f208067de33bad4d4c91ea8dc974bce0a1 |
| dot-grid | 5x5 | 6 | 45958e7de2b03e705d949058a74871b720c933b6690af3237dc550276121f3ff | eec6872072e956535878ec2c0e3124d23b5ba54a2f7f172e1c2841eeee6b5be4 |
