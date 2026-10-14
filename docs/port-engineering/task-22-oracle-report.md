# Task 22 public CPU oracle report: CRT

## Conclusion

The frozen CRT oracle is ready for a future one-key Task 22, but it proves that
CRT is **not** a plain no-compatibility addition. Expected output comes from the
pinned public CPU `crtFactory` adapter. Eleven cases cover alpha copy/clamp
behavior, defaults and metadata maxima, time/speed short circuits,
landscape/portrait/square shape branches, full-resolution fallback, tiled and
untiled coordinates, and renderScale below/equal/above one. Eighteen counted
mutations cover the public sine adapter and the remaining alias/order/F32/
resource hazards.

The generator independently reconstructs the adapter around mutated copies of
the exact canonical factory text. Before mutations, that reconstruction must
match the imported public adapter in complete F32 and RGBA8 bytes for every
case. Every canonical case also renders twice from fresh surfaces and must be
byte-identical and finite.

## Frozen provenance

| Field | Frozen value |
| --- | --- |
| Key | `filter/crt:crt` |
| Corpus revision | `a1a3fa2a84223dfc1f5ec2c7a54a6f4269139c15` |
| Raw source | 19,644 bytes; SHA-256 `dfbba2918a68889c5b82ef619bf472387acec116b4d72bf76d62f35a60c9aa7f` |
| Normalized source | SHA-256 `b61e7111d522b13682b351f592d1873b30c1644f5964e34af689117ff8408902` |
| Canonical factory | `canonicalFactory42`; `toString()` SHA-256 `2420fa0eecb9e48c1192c1f029ab7c547888a9f9ca68cf26e145dd6762695cb6` |
| Public adapter | `crtFactory`; file SHA-256 `c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc`; `toString()` SHA-256 `240972f95f908452bf87fc681e360553759f374fa81613adc415a5a7c5eb4bf7` |
| Canonical generated runtime | SHA-256 `80b2e701426a5003d9ef44dce09de1f601f4c8cd1e4bff1f0c4d2b607e95e91c` |
| Typed fingerprints | function tuple `aba032705467be0f9e5f98248b0801549b9aad498ae1dd2910d0a6e6ab9f0fc1`; whole program `a413b66710aeef5c8911da18d1de09cd4f7519060ca104c16b321fbbaa3e1248` |
| Typed shape | 35 source functions, zero loops, acyclic call graph |
| Required compatibility | `crt-metal-sine-v1` (provisional name), public adapter semantics |

The exact bindings, output, pass route, defaults, local shadow symbol IDs, and
three-fetch normal-path resource profile are recorded in the JSON.

## Cases and hashes

The asymmetric top-down F32 input uses:

```text
R=((17*x+31*y+13)%101)/100
G=((7*x+19*y+23)%97)/96
B=((29*x+11*y+5)%89)/88
A=(((5*x+7*y+3)%23)-5)/12
```

Every lane crosses a `Float32Array` boundary. Alpha deliberately ranges outside
the unit interval, which distinguishes uniform alpha strength from preserved
input alpha.

| Case | Output F32 SHA-256 | Output RGBA8 SHA-256 |
| --- | --- | --- |
| alpha-zero-exact-copy-tiled | `daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687` | `5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3` |
| alpha-negative-clamps-zero-copy | `5036ac34df07a6e89f8ae9cd5ee4fa3250a1962bdbda6bc4e29dc4ce512fb8a8` | `6b56cc6c2f780b54a655f04ba7deae8e61e8330ca84b5d5056e8c352dd16885c` |
| default-landscape-untiled | `8d79ffbb89906ab3ac639254ad939a80b700609c11b3052da69d7d1b308a1ead` | `b119d07a2c71836c7ae0ae8fb26deb0942ba5254c50b8f10e1a57983e4abc80d` |
| alpha-above-one-clamps-and-preserves-input-alpha | `db6a4c4b1828da7def9818c90a04156914cc1fb57dd4fd6e8fc471e625a67203` | `b971437eec882ffd958b151216992caad58a8a681211f161ec60480820d52fee` |
| landscape-tiled-render-scale-two | `d93238b6ab384881dc5bfb5d6e51e33db46b6f8430068d62bd30d5cd7e7b10af` | `8b01630d856e5de5c694addc6bb8f3aecdfe561d18d777cbb773b99e983d113c` |
| portrait-tiled-fractional-render-scale | `df4de8296c90676f60025d0fff1869d001d5835343fba8e59f0ac2edc49fdbf9` | `8c55dd1ea14b3cf06413cc902253ee1d7c674ff33776ca2c937c9992b22f56a9` |
| speed-zero-nonzero-time | `50e355ebf7f615c611b33ba28a0ea4ba39ea15ef7f1abcfc7e1bc57e43d3bd84` | `7fc20e14302c8dd5b1abd2561fc5f0749e1e7b014b5feb583f5cc734bc6e2e19` |
| time-zero-positive-speed | `e8c211553f7fb1a7398cc4ce4f1dd9c1ff5c14b02fe24c4e097f9de8d418fa16` | `9c9a2e5f1c63dde9de72bebded827b52339bad6d06fcb035da5c7f2286aad86d` |
| full-resolution-zero-fallback | `70e7b389149a2d86cb8771d9c2cbf6324a3d4132433946157674b82a7703f69a` | `6503af699c4bbefc4dda800dfdb455b397b05165486e6866de4ebc0f474b5377` |
| square-large-time-max-metadata | `b358b073881dd9e560052bf8204bb9b4fb2baf36d6914a67560252f4bf8682d5` | `3123832208dc84924af2cae7b1f93e7cf959f72f4df0087f909f7697daca57cd` |
| render-scale-below-one-clamps | `4af92d87e04669063f3cdad9601ad08a57b5d64e9aa0bd4c5da4270ea0ee0381` | `442879a307d31f079e3279360b68cf9fb95fd949f47e6ad266caf939386d3ed3` |

Both alpha-clamped-zero cases are exact F32 copies. Every normal case changes
all pixels' RGB and preserves every input alpha bit, including out-of-range
values. All output lanes are finite.

## Mutation sensitivity

All factory mutations use exact text and asserted occurrence counts; shape
drift fails generation. The first mutation bypasses the public adapter and is
the decisive compatibility proof.

| Mutation | F32-changing cases / 11 | RGBA8-changing cases / 11 | Maximum changed F32 lanes in one case |
| --- | ---: | ---: | ---: |
| public-metal-sine-disabled | 9 | 9 | 350 |
| uniform-time-local-alias-offset | 8 | 8 | 334 |
| uniform-speed-local-alias-offset | 9 | 9 | 355 |
| output-alpha-uses-uniform-not-shadowed-input | 9 | 9 | 117 |
| uniform-alpha-clamp-disabled | 2 | 2 | 351 |
| render-scale-clamp-disabled | 1 | 1 | 322 |
| full-resolution-fallback-disabled | 1 | 1 | 320 |
| shape-frequency-axes-unswapped | 2 | 2 | 196 |
| scanline-parity-forced-first-value | 9 | 9 | 223 |
| red-tile-local-subtraction-disabled | 6 | 6 | 317 |
| blue-tile-local-subtraction-disabled | 6 | 6 | 328 |
| red-channel-assembly-uses-blue | 9 | 9 | 304 |
| restore-hue-disabled | 9 | 9 | 326 |
| saturation-boost-disabled | 9 | 9 | 320 |
| vignette-alpha-forced-zero | 8 | 8 | 297 |
| contrast-gain-1-25-to-1 | 9 | 9 | 346 |
| effect-color-8bit-quantization-disabled | 9 | 7 | 337 |
| seed-base-disabled | 9 | 9 | 338 |

Disabling the source's effect-color 8-bit quantization changes F32 output in
all nine normal cases and RGBA8 output in seven. The two exact-copy cases remain
identity controls for all mutations that occur after the early return. The
renderScale and full-resolution mutations each diverge only in their dedicated
branch case and match all cases where their altered predicate/value is
equivalent.

## Reproduction

Run from the repository root with an authenticated CPU root and matching ledger:

```sh
node docs/port-engineering/task-22-oracle-generator.mjs --cpu-root "$CPU_ROOT" --ledger "$CPU_LEDGER" --check
```

`--check` revalidates pinned source, canonical runtime, canonical factory,
adapter file/factory, public dispatch identity, all source-function shapes,
double-render determinism, local adapter reconstruction, and every mutation;
then it requires exact JSON identity. `--write` is the only mode that rewrites
the frozen JSON. No repository output is used as an expected image.
