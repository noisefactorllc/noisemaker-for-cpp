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
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Raw source | 19,560 bytes; SHA-256 `62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c` |
| Normalized source | SHA-256 `acd1c3f05c6d02052592aeb46bbbc49d23e18f4e83530498687903e00b4623fe` |
| Canonical factory | `canonicalFactory44`; `toString()` SHA-256 `6d65f4984f8749ca7cdfec976e082662d3a7ad614aabb15ce8a168fca7d8e303` |
| Public adapter | `crtFactory`; file SHA-256 `c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc`; `toString()` SHA-256 `240972f95f908452bf87fc681e360553759f374fa81613adc415a5a7c5eb4bf7` |
| Canonical generated runtime | SHA-256 `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Typed fingerprints | function tuple `f6ab50374732b058fa2a5cd33e87bbe35654682b7125593d7451871194b2ba72`; whole program `f70fc78da6c3579fa3237fbbfa3712229b88f0a93b8d556181f9bad2ed74b6fc` |
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
| default-landscape-untiled | `3134189c0654121a560abf3f8f102873b3395937ae244eaf1d6de7d03e6c8192` | `c9a7375db6ae12c5dc1f0b2fa49669892d405c55ab587cc0a054d75d9d66eeb9` |
| alpha-above-one-clamps-and-preserves-input-alpha | `e6d5a0788f2a23100ee9968186ac1f1a05175ecf6972e8503bd92cd8130a4bfd` | `b971437eec882ffd958b151216992caad58a8a681211f161ec60480820d52fee` |
| landscape-tiled-render-scale-two | `7e9a4e738ad67051674ea5d8e7e2333585e943bbe45fcdbdf3c9e59635c359ec` | `2ed1841d5be9df1f576fecf81bab403ad848fb96d4e33055525a1520e905d75c` |
| portrait-tiled-fractional-render-scale | `cdc080912dc354a6052447427814040e552d7c38edf4e1c499d8f7c80bd196be` | `ecfb38a778ba9e40d9bacfb5a8f1f62a810cd929d14b83c2bf5d4abc6bc0d079` |
| speed-zero-nonzero-time | `f83304619eda688e29c3ae34b4c913535919c3505c2f59f5100b587ddf52ddd8` | `16727fe42c77a453e47d0dcfcc14b079b39a84d06683ac8d0f689749611ec70e` |
| time-zero-positive-speed | `bc5ed1803bb52ee4d075d4c9ff6e5cc62ca2ba6f60f7d5aed93d1c237ad81b98` | `59a3fef349d5457d514174dba0e328bcd1723f97d0d8fdf82649ed217265f5d0` |
| full-resolution-zero-fallback | `19b91bedac3685b2c368a1c8da9eb89ae6e57e8deeee513b4151cf12dad3896f` | `fc49c1f7a2ea1c69db968ceabfaa4293ba8b193e13a5634b51ef763d0fea50d6` |
| square-large-time-max-metadata | `5169bfe5072efd935eafd52f13b413c7b4f5f9834e9991f5a6207a877a6bfc48` | `3a0f86f1aac14e290bbc2d22675f4af5bfa1a08fc68cbfc59c92331f5daf59a5` |
| render-scale-below-one-clamps | `d963390a996552ce28b3f8f5c7b7971072a60566ebad0bf29beb329fa4a24de2` | `65e933fe048522db9d4b8eae08057c6ca56f3d4b53510181fb2e288f25546716` |

Both alpha-clamped-zero cases are exact F32 copies. Every normal case changes
all pixels' RGB and preserves every input alpha bit, including out-of-range
values. All output lanes are finite.

## Mutation sensitivity

All factory mutations use exact text and asserted occurrence counts; shape
drift fails generation. The first mutation bypasses the public adapter and is
the decisive compatibility proof.

| Mutation | F32-changing cases / 11 | RGBA8-changing cases / 11 | Maximum changed F32 lanes in one case |
| --- | ---: | ---: | ---: |
| public-metal-sine-disabled | 9 | 9 | 351 |
| uniform-time-local-alias-offset | 8 | 8 | 346 |
| uniform-speed-local-alias-offset | 9 | 9 | 359 |
| output-alpha-uses-uniform-not-shadowed-input | 9 | 9 | 117 |
| uniform-alpha-clamp-disabled | 2 | 2 | 351 |
| render-scale-clamp-disabled | 1 | 1 | 328 |
| full-resolution-fallback-disabled | 1 | 1 | 320 |
| shape-frequency-axes-unswapped | 2 | 2 | 213 |
| scanline-parity-forced-first-value | 9 | 9 | 233 |
| red-tile-local-subtraction-disabled | 6 | 6 | 319 |
| blue-tile-local-subtraction-disabled | 6 | 6 | 340 |
| red-channel-assembly-uses-blue | 9 | 9 | 323 |
| restore-hue-disabled | 9 | 9 | 341 |
| saturation-boost-disabled | 9 | 9 | 344 |
| vignette-alpha-forced-zero | 9 | 9 | 337 |
| contrast-gain-1-25-to-1 | 9 | 9 | 363 |
| local-mean-eager-f32-materialization | 9 | **0** | 37 |
| seed-base-disabled | 9 | 9 | 345 |

The eager-F32 mutation is an explicit full-precision control: it changes F32
output in every normal case but no RGBA8 byte. The two exact-copy cases remain
identity controls for all mutations that occur after the early return. The
renderScale and full-resolution mutations each diverge only in their dedicated
branch case and match all cases where their altered predicate/value is
equivalent.

## Reproduction

Run from any directory:

```sh
node docs/port-engineering/task-22-oracle-generator.mjs --check
```

`--check` revalidates pinned source, canonical runtime, canonical factory,
adapter file/factory, public dispatch identity, all source-function shapes,
double-render determinism, local adapter reconstruction, and every mutation;
then it requires exact JSON identity. `--write` is the only mode that rewrites
the frozen JSON. No repository output is used as an expected image.
