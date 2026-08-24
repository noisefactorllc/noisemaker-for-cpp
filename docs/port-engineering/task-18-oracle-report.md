# Task 18 frozen external oracle report

The Task 18 external oracle contract is frozen for exactly the proposed
`fixed-grid-counter-store-v1` pair:

- `filter/celShading:celShadingEdges`
- `filter/outline:outlineSobel`

No repository file was changed and no Git command was used. The generator
binds the pinned `noisemaker-for-cpu` `canonicalKernelFactories` directly
through `bindCanonicalKernel`, executes with `runPass`, and writes canonical
`Surface` output. It does not reproduce either Sobel algorithm itself.

Artifacts:

- `task-18-oracle-generator.mjs` — SHA-256 `ef9ec7303f2e610af7384e3c681935be725bce8019498e3f2b49f9e6ec6489c8`
- `task-18-oracles.json` — SHA-256 `6bfefcf7891f55896e1ff5be6cd67db94c21853f90073a851eacc8ff18da9c1b`

The fixture is a top-down, non-square 7x5 `Float32Array` texture with
distinct formula-generated RGBA lanes. It renders a non-square 9x7 output
with `tileOffset=[3,2]` and `fullResolution=[12,10]`. Both programs bind the
explicit F32 `2.299999952316284` / `0x40133333` edge width or thickness; its
canonical integer conversion is two. The output being larger than the input
forces every 3-by-3 grid's negative and positive `wrapCoord` residues rather
than merely sampling interior pixels. Cel uses its RGB luminosity read;
Outline uses its scalar red-lane read.

Every case renders twice with fresh input and destination surfaces. The
generator fails before freezing a hash if either the F32 bytes or RGBA8 bytes
differ across repeats. JSON records raw and normalized source digests,
canonical generated-runtime digest, exact factory `toString()` digest,
empty define map, binding order/types, uniform F32 words, hashes, and three
top-down F32 lane-bit probes.

| Case | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| `cel-width-2.3f-threshold-0.18f` | `d86694f5c5a05c094b1dc9d4302b0b98cbe3044e5ce22587fdf6dd80f77d27a7` | `966ca81461240fb6c35316537f631f3b74b6d0a33a7b538d05ddd12e241347e9` |
| `cel-width-2.3f-threshold-0.6f` | `048acf6f8feb3be40c9be548bc64eaeadc6de78366a61b778c899eb463575ac0` | `8d0418a7e7b046d582cafcfbbe95b1bf2c05478929a57719ab52a345de1091e5` |
| `outline-metric-1-thickness-2.3f` | `2e62cf4918bb2da1def8b146c4e33ef009d6c6ef05f96bf2d0fd2be4e7679a7f` | `a877af8b8229c67295f3c17123cbaa5a540e59e81a3f95af9db601be5b2eca90` |
| `outline-metric-2-thickness-2.3f` | `afac987ef587a22d89ed00f619edb97e29d321fb2cc57667ceea89c0d78744b0` | `e01ac082638be9679283946c758e093c5ea966bc79b8acdf14d8ee1213f084f8` |
| `outline-metric-3-thickness-2.3f` | `33eb93deef5ea41a7f085c4d3e9d8f4d5c3b4353b8490f0b9e0bbd2466c1d1ff` | `8c3a62bd220bf6321d1127ab2cb1823522ffe38e9e07f985af9aceb9e64a253c` |
| `outline-metric-4-thickness-2.3f` | `a4293babe12252aa6e0f4c4b50f6242ef4a1060297a40a1da12a549ea9c77047` | `db8a0a072ec1c5e85d8678100929a1ef5ecf5c6ffc88217536354d06f4a11f74` |

Cel's 0.18f threshold fixture contains zero, interior, and saturated
smoothstep results; 0.6f changes the threshold boundary while retaining the
same nine-store grid. Outline exercises all `int(sobelMetric)` paths: 1 is
the Euclidean default branch, 2 Manhattan, 3 Chebyshev, and 4 Octagram. The
metric-4 frozen factory uses the canonical F32 literal
`1.4140000343322754`, so its distinct full-frame F32 hash is essential even
where a selected probe happens to match metric 3 after `max`/clamp.

## Zero-size early return

The public canonical API cannot safely freeze a zero-size render:
`Surface` and `createCanonicalBindings` both reject non-positive dimensions.
Accordingly, this oracle deliberately does not bypass the public API with a
forged sampler. Native Task 18 testing must inject a zero-width sampler and,
separately, a zero-height sampler while invoking a normal positive output
pixel. Each test must prove the source's `vec4(0.0)` result, no fetch, and no
entry into the `samples`/`idx` initialization grid. This is a required native
control-path test, not an absent source behavior.

## Numeric and boundary notes

- `createCanonicalBindings` spreads explicit uniform values without rounding.
  The generator supplies `Math.fround` values intentionally, so native tests
  must bind the exact recorded F32 words rather than JS double `2.3`, `0.18`,
  or `0.6`.
- The canonical counter-filled tables are zero-filled plain JavaScript Number
  arrays. Texture lanes cross F32 storage boundaries and final output crosses
  F32 storage, but table scalar arithmetic remains Number precision. The
  proposed C++ profile therefore needs zero-initialized `double[9]`-equivalent
  storage, not an accidental float table or uninitialized stack storage.
- The input/output coordinate conventions are intentionally asymmetric:
  `Surface` rows are top-down while `runPass` supplies bottom-left
  `fragCoord`. The probe coordinates, byte layout, and `wrapCoord` cases in
  JSON lock that orientation.
- RGBA8 hashes are supplemental. They round and clamp output, whereas the
  F32 hashes and lane words distinguish smoothstep/metric precision and the
  metric-4 divisor.

Verification performed:

```text
node docs/port-engineering/task-18-oracle-generator.mjs --check
ok task-18-oracles.json
```

`--check` recomputes all six direct canonical cases and byte-compares the
complete existing JSON. It performs no write.
