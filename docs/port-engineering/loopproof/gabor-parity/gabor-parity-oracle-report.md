# Gabor loop-depth and pixel-parity oracle

Frozen JavaScript ground truth for `synth/gabor:gabor`. The package authenticates the canonical source/factory/interface, freezes the sole counted-loop admission need, and records exact Float32 and RGBA8 render contracts. The custom comparer provides first-pixel diagnostics without weakening byte equality.

## Admission result

- The live pre-port validator rejects at `54:13` with `unsupported counted-for safety charge`.
- All four loops are proved and the counted-loop call graph is acyclic.
- The helper nest has trip counts 3 x 3 x 8, maximum lexical product 72, and helper charge 84. The five-trip main loop calls that helper, yielding entrypoint charge `5 + 5 x 84 = 425`.
- Maximum effective depth is four: main loop depth one plus the helper's lexical depth three. Maximum lexical depth remains three.
- Both 72 and 425 are below the requested 4096 reference cap. The live 2026-08-14 generic constants have since expanded to 262,144 (product) and 262,656 (charge), so the hard-coded depth-three predicate is still the only failing numeric gate.
- An isolated re-probe that changed only the effective-depth predicate from three to four passed the real validator and the independent emitter gate; emitted output was 12,483 bytes with SHA-256 `8eaf3ab53ae3a162c5ea7b0ff0a125cb14bce0f79d3adbaebc586e1ff97c826f`.
- Required production design: a source-authenticated, program-scoped effective-depth-four profile in both authorities. No global cap and no other numeric limit should move.

## Frozen identities

- Upstream snapshot revision: `6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d`
- Corpus revision: `6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d`
- GLSL source: 3870 bytes, SHA-256 `91665da2d584d6d88b38e8ba314dfc0b546dd49d29aa161f5d66aecf6bf67bf5`
- Canonical factory: `canonicalFactory257`, 4480 bytes, SHA-256 `1b1a5e306c24eeb679d656dc568d768dc9ca45be3635c7f44e9f8873b8477533`
- Public catalog identity is exactly the canonical factory; no adapter override exists.
- The canonical define map is exactly empty. The pass has no samplers and writes only `fragColor`.

## Render cases

| Case | Size | Density | Octaves | Speed | Time | Seed | Tile offset | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| default-landscape | 5x4 | 3 | 1 | 1 | 0 | 1 | 0,0 | `f14e9426f45d5992436727ef36c163f096414f41483cb7f8bf627163ed98aac0` | `ad5a765ae88df34f85415ccd5f478adfe1d746a68b1019f86ae909233810f14e` |
| max-depth-density-octaves | 4x3 | 8 | 5 | 5 | 0.125 | 100 | 0,0 | `bfb3cbdd464e9053b3b56f3831918fbfee929ae8805082b0ad0d247f16b68dc4` | `54c377ff0fab8e0478ea10876628e146a7f88944037794d6807df9b1a035fe71` |
| minimum-work-speed-zero-time-a | 3x5 | 1 | 1 | 0 | 0 | 37 | 0,0 | `cbb7c9ed02e147630e7468a9abf625aaa2aafd96742ae572e565d570a337b6d5` | `ff07db1d76a8b532315c6eb4461059471a5477df3386d7270958be848143ef6d` |
| minimum-work-speed-zero-time-b | 3x5 | 1 | 1 | 0 | 0.987500011920929 | 37 | 0,0 | `cbb7c9ed02e147630e7468a9abf625aaa2aafd96742ae572e565d570a337b6d5` | `ff07db1d76a8b532315c6eb4461059471a5477df3386d7270958be848143ef6d` |
| intermediate-anisotropic | 6x2 | 5 | 3 | 2 | 0.375 | 17 | 0,0 | `41b341a40bb1f22bcbfe6ce72d01e8fe5b360da7a1d1e7edac848bfa06ac7803` | `6d598eb2147ac6bb562018b9e611abdd4c86c6ef2b3dbe693414a78cea431222` |
| opposite-angle-random-orientation | 2x6 | 6 | 4 | 3 | 0.0625 | 63 | 0,0 | `a7f8b2e148adbac178ccebeb8b77a4c38bc188911a8c6c32c5bffd70f8fe3d38` | `9ea610c1737fa332cbe4d15f8737a619a92829dd90d1e2533caf8c7f2d60120c` |
| tile-full-reference | 7x5 | 7 | 4 | 4 | 0.21875 | 29 | 0,0 | `6bb6719f04c248d5ce5365ac57bdcd475b3482015f4527433b61a0f6f6dae307` | `9d82032633c1043c30f27b2e7c71392738684ed536f11ea57643d1efbc18fdd0` |
| tile-3x2-bottom-offset-2x1 | 3x2 | 7 | 4 | 4 | 0.21875 | 29 | 2,1 | `1b6e3fc5742b2f75dfe97612e3f5011a89965274a8287c81f661414992b236d6` | `a13a3979f466a34c0e3e4d9c6cd5ca81f4f41073f9575c93266be5fca0f95456` |

Every valid-domain case requires finite exact-grayscale output with exact alpha one, exact repeated-render identity, and direct-canonical/public-catalog equality. The paired speed-zero cases prove time identity and unused frame/external-seed identity. The tile case must exactly equal the corresponding bottom-left-origin crop from the full render.

## Materialization traps

- Canonical JS converts GLSL `float(0xffffffffu)` to Float32 4294967296. Direct word fixtures freeze that intermediate. Using Number 4294967295 happens to round every frozen normalized result to the same Float32 lane, so this is explicitly structural rather than assigned a false pixel witness.
- Scalar Gabor and octave accumulators stay JavaScript Number values until vector/Surface materialization. Premature Float32 narrowing is rejected separately at each accumulation layer.
- Octave state updates are order-sensitive. Advancing `pOct` before rather than after the current sample is rejected by exact pixels; swapping neighbor traversal is separately rejected by source authentication.
- `fullResolution.y`, bottom-left `gl_FragCoord`, and `tileOffset` jointly define coordinates. The exact tile/full continuity check freezes all three.
- The effect-level `seed` uniform overrides the infrastructure seed option. `frame` is not read by this factory; the identity pair records that instead of inventing a false witness.

## Mutation discrimination

| Mutation | Required exact-bit witnesses | All divergent cases |
| --- | --- | --- |
| octave-loop-five-reduced-to-four | max-depth-density-octaves | max-depth-density-octaves |
| impulse-loop-eight-reduced-to-seven | max-depth-density-octaves | max-depth-density-octaves |
| density-break-removed | default-landscape, minimum-work-speed-zero-time-a | default-landscape, minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| octave-break-removed | default-landscape, intermediate-anisotropic | default-landscape, minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| octave-coordinate-update-before-sample | max-depth-density-octaves | default-landscape, max-depth-density-octaves, minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| inner-sum-premature-f32 | intermediate-anisotropic | default-landscape, minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference |
| octave-sum-premature-f32 | intermediate-anisotropic | default-landscape, minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference |
| octave-coordinate-doubling-removed | max-depth-density-octaves | max-depth-density-octaves, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| octave-amplitude-decay-removed | max-depth-density-octaves | max-depth-density-octaves, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| normalization-removed | max-depth-density-octaves, intermediate-anisotropic | max-depth-density-octaves, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| full-resolution-y-replaced-by-x | default-landscape, tile-full-reference | default-landscape, max-depth-density-octaves, minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| tile-offset-removed | tile-3x2-bottom-offset-2x1 | tile-3x2-bottom-offset-2x1 |
| time-binding-ignored | max-depth-density-octaves, intermediate-anisotropic | max-depth-density-octaves, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| effect-seed-ignored | max-depth-density-octaves, intermediate-anisotropic | max-depth-density-octaves, minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| orientation-ignored | intermediate-anisotropic | minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, tile-full-reference, tile-3x2-bottom-offset-2x1 |
| isotropy-ignored | max-depth-density-octaves, intermediate-anisotropic | max-depth-density-octaves, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |

The nine source/profile negatives separately reject wrong key, define or byte drift, changed bounds/breaks/order, and a global depth-cap widening. Source authentication is required even when a mutation remains numerically below a generic budget.

## Regeneration

From the `noisemaker-for-cpp` repository root:

```sh
node docs/port-engineering/loopproof/gabor-parity/gabor_parity_oracle_generator.mjs
node docs/port-engineering/loopproof/gabor-parity/gabor_parity_oracle_generator.mjs --check
```

