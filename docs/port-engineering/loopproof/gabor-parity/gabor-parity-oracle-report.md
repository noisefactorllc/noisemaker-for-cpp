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

- Upstream snapshot revision: `117a236679d1db3ab8f0e278230ece277b57564c`
- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`
- GLSL source: 3870 bytes, SHA-256 `91665da2d584d6d88b38e8ba314dfc0b546dd49d29aa161f5d66aecf6bf67bf5`
- Canonical factory: `canonicalFactory249`, 4405 bytes, SHA-256 `1a761bd2b1ab87e781ca4d7a1fc622ed450035b9695115a84e59fb36e6718c57`
- Public catalog identity is exactly the canonical factory; no adapter override exists.
- The canonical define map is exactly empty. The pass has no samplers and writes only `fragColor`.

## Render cases

| Case | Size | Density | Octaves | Speed | Time | Seed | Tile offset | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| default-landscape | 5x4 | 3 | 1 | 1 | 0 | 1 | 0,0 | `e3dab43a27e8d586867a8a60b17db94e886ec04a02e250fefad05562a765f955` | `ad5a765ae88df34f85415ccd5f478adfe1d746a68b1019f86ae909233810f14e` |
| max-depth-density-octaves | 4x3 | 8 | 5 | 5 | 0.125 | 100 | 0,0 | `fec494791b3b11e2b49c3b72221cb5384949421b58adf30a7eb2cefeaf369e4f` | `54c377ff0fab8e0478ea10876628e146a7f88944037794d6807df9b1a035fe71` |
| minimum-work-speed-zero-time-a | 3x5 | 1 | 1 | 0 | 0 | 37 | 0,0 | `f0db9762f51e63299a476a509a2c01e672588d6f64f00f877f4c9bccfb1eb40e` | `ff07db1d76a8b532315c6eb4461059471a5477df3386d7270958be848143ef6d` |
| minimum-work-speed-zero-time-b | 3x5 | 1 | 1 | 0 | 0.987500011920929 | 37 | 0,0 | `f0db9762f51e63299a476a509a2c01e672588d6f64f00f877f4c9bccfb1eb40e` | `ff07db1d76a8b532315c6eb4461059471a5477df3386d7270958be848143ef6d` |
| intermediate-anisotropic | 6x2 | 5 | 3 | 2 | 0.375 | 17 | 0,0 | `41b341a40bb1f22bcbfe6ce72d01e8fe5b360da7a1d1e7edac848bfa06ac7803` | `6d598eb2147ac6bb562018b9e611abdd4c86c6ef2b3dbe693414a78cea431222` |
| opposite-angle-random-orientation | 2x6 | 6 | 4 | 3 | 0.0625 | 63 | 0,0 | `73263d9bf846184b0324a958c8adad4e4fc207921cdd86317a463ef70bb8cc8a` | `9ea610c1737fa332cbe4d15f8737a619a92829dd90d1e2533caf8c7f2d60120c` |
| tile-full-reference | 7x5 | 7 | 4 | 4 | 0.21875 | 29 | 0,0 | `fa8780a091028aabdfcec7980a99485050e8729d91688ae9bde43ba508cda659` | `9d82032633c1043c30f27b2e7c71392738684ed536f11ea57643d1efbc18fdd0` |
| tile-3x2-bottom-offset-2x1 | 3x2 | 7 | 4 | 4 | 0.21875 | 29 | 2,1 | `d2db62258d55dc4e5ebe517d6b4cd87c8fec4a5f80590a1a04c68e69da02df33` | `a13a3979f466a34c0e3e4d9c6cd5ca81f4f41073f9575c93266be5fca0f95456` |

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
| inner-sum-premature-f32 | max-depth-density-octaves | default-landscape, max-depth-density-octaves, minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference |
| octave-sum-premature-f32 | max-depth-density-octaves | default-landscape, max-depth-density-octaves, minimum-work-speed-zero-time-a, minimum-work-speed-zero-time-b, intermediate-anisotropic, opposite-angle-random-orientation, tile-full-reference, tile-3x2-bottom-offset-2x1 |
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

