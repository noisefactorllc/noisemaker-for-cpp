# Emboss181 exact-parity oracle

Program `filter/emboss:emboss`; corpus revision `0ed489ec46842bffba33ee2ec65a218b6dda51f5`.

## Result

Seventeen canonical STYLE=0 fixtures store complete Float32 words and independently captured RGBA8 bytes. The suite covers both dispatch helpers, all four full-frame equality combinations, fractional scale, rotation/extrema, clamp/alpha, retained-but-dead colorAmount, external context, and asymmetric table witnesses. No C++ render contributes expected data.

## Exact contract

- Dimensions and lane/byte counts are checked before payloads.
- Float32 equality is raw-word equality, including signed zero and NaN payloads.
- RGBA8 is compared separately from independently supplied canonical bytes.
- Every case proves repeat identity, direct/public identity, finite output, input immutability, hashes, and at least five probes.

## Render fixtures

| Case | Size | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- |
| full-frame-default-nonsquare | 9x6 | 404a2059a72ae159c58c6121f861718b522d26c14da5051b6cc000aefbff5169 | 6eebe43e9af4ec3dbfbe173fc4fd60a64b329441f85db349e4da863785d70048 |
| general-angle-only | 9x6 | d5af05b34869e361dc97f42222727304d8c2738e7345409396d946a06a44098d | 557f763622a06da633e32826f7bf5b2d8cdaae38ea48212ca7327fb701a98145 |
| general-height-only | 9x6 | e0dd4d5f0e033010a3414be8f9b131d42a6fb605060cfb6de4850ba634217319 | 7649a5c8f7fb8180303344279f6f87c1cc82a688f84012016777228ef40aa0c4 |
| general-rotation-extreme | 5x5 | ef71580f2f4444af4bf465843e3484b4dadec3936f3a932dc3b2e8112db0ee80 | 5eaea83d78f04258a21a751ad8b8897e34e773d489ae094a69ce19f62c580b86 |
| default-fractional-scale | 8x5 | 2ceef0094981a60f49bd69c8659b518504383a9071315ffa9ec1c7223d1949e9 | e76fd0f9d5562794e84d3e5631fce4df289fda4ce71d761e3411feb9692cbfb2 |
| general-fractional-scale | 2x2 | b0e203dba0a9c14435f2e4ee9f77a70deee31018db5213890affa41ae1ab49de | b9b8a2205fd354bd2e3b1652018a01189823ec36461f22f3743e4ce55ba3b270 |
| fullresolution-x-mismatch-only | 7x5 | 97ecacdf86f9137ed8bbb3b6de92973eed9bfb7c907beaba9bf27e4af9d780d3 | d15d6eb7e3d2e26f8f5914f549cdf807690753a3ef2294b7fe7f8e0454d0e6a2 |
| fullresolution-both-mismatch | 7x5 | 191c1a6fe28163781bbf5cd9a92d31319e5a46400b14540e3a051b4a0749e240 | 8db7a84d158c36c1645ed9af719f29d3d8242e5548892e9156c6b8542b3ff526 |
| tile-x-offset-only | 7x5 | fb58dab3ed5e338478313f58d96419025913957f8cc4a797df2b3c18f874291b | 89679eef24ad071e7da755d9fafce12bb9379d9eab451585260480f1e8d9cb84 |
| both-frame-terms-false | 7x5 | 72ecebc40fbc3a390d069bdb8eab8422886905ad057fc3bd4acc9c3d4da7684f | c362448f3e95843c2e665cc29cacb1c19a6a2a8c2294455a279c431eb419a490 |
| clamp-and-alpha | 7x5 | ddc68578dff17cbc7488b22038c64f77c6dfec3de09b99d9c21fe5a57154bcdc | 1d57f0f95ce4c69d8b5e23fe3f44ae1b69873c58a0eb2fec52d8f62538eeb62f |
| coloramount-control-low | 8x6 | d49e7249a4ff6cbc4c7caea5c6672db66fd057ea8bd93400323fcb6672e0fcbd | c7159ffe619d1837e51b4e5ed438d64de54fff03be7140b22312ec027c8da62c |
| coloramount-control-high | 8x6 | d49e7249a4ff6cbc4c7caea5c6672db66fd057ea8bd93400323fcb6672e0fcbd | c7159ffe619d1837e51b4e5ed438d64de54fff03be7140b22312ec027c8da62c |
| external-context-base | 8x6 | ab7a8240ac3babe1e0ef9f71b71634f34021874c12833c3bc57c92507c8c9717 | 8d473f2418f9082fbae7c14c4f6d77e6584148bbcda112d335162ad835640c97 |
| external-context-extreme | 8x6 | ab7a8240ac3babe1e0ef9f71b71634f34021874c12833c3bc57c92507c8c9717 | 8d473f2418f9082fbae7c14c4f6d77e6584148bbcda112d335162ad835640c97 |
| default-asymmetric-impulse | 5x7 | 5ee1bef54cbab1e8fdc043a35add56440806a6c41428bf31ace03888ea9d0abc | 8589e18d53a05c37f45fb51af44827147c279f3a308c1558b08f419528f3a229 |
| general-asymmetric-impulse | 9x7 | 3bc32cf32cdaeb3daf64a2bb19f04d51a9ccb9760da6be619897bd9e71782dda | c4b6c6bfb33b571d80d1ee9e3b643cb9066d87e89d511946ea8038655fe88164 |

## Behavioral mutations

| Mutation | Required witness | Changed lanes at first divergent case | First x,y/channel |
| --- | --- | ---: | --- |
| dispatch-force-default | general-rotation-extreme | 71 | 0,0/g |
| dispatch-drop-angle-half | general-angle-only | 127 | 0,0/r |
| dispatch-drop-height-half | general-height-only | 135 | 0,0/r |
| dispatch-and-to-or | general-angle-only | 127 | 0,0/r |
| default-kernel-0-minus-one | default-asymmetric-impulse | 88 | 0,0/r |
| general-kernel-0-minus-one | general-asymmetric-impulse | 143 | 3,0/r |
| default-loop-eight | default-asymmetric-impulse | 93 | 0,0/r |
| general-loop-eight | general-asymmetric-impulse | 148 | 3,0/r |
| default-offset-0-flip-x | default-asymmetric-impulse | 9 | 2,1/r |
| general-base-offset-0-flip-x | general-asymmetric-impulse | 30 | 1,0/r |
| general-rotation-y-sign | general-rotation-extreme | 42 | 0,1/r |
| rotatedpx-no-f32-array | general-rotation-extreme | 13 | 0,1/r |
| offsetuv-no-f32-array | general-fractional-scale | 5 | 0,0/g |
| default-omit-amount | default-fractional-scale | 118 | 0,0/r |
| general-omit-amount | general-fractional-scale | 10 | 0,0/g |
| default-omit-render-scale | default-fractional-scale | 118 | 0,0/r |
| general-omit-render-scale | general-fractional-scale | 10 | 0,0/g |
| resolution-equal-to-notequal | fullresolution-both-mismatch | 82 | 0,0/b |
| resolution-all-to-any | fullresolution-x-mismatch-only | 64 | 0,0/b |
| fullframe-and-to-or | fullresolution-x-mismatch-only | 64 | 0,0/b |
| true-arm-swizzle | full-frame-default-nonsquare | 77 | 0,0/r |
| false-arm-use-local-size | both-frame-terms-false | 73 | 0,0/g |
| fullframe-force-true | both-frame-terms-false | 73 | 0,0/g |
| sample-numerator-use-local-size | both-frame-terms-false | 77 | 0,0/g |
| sample-denominator-use-full-size | both-frame-terms-false | 79 | 0,0/g |
| remove-final-clamp | clamp-and-alpha | 72 | 0,0/r |
| alpha-force-one | clamp-and-alpha | 35 | 0,0/a |
| style-zero-to-one | coloramount-control-low, coloramount-control-high, default-asymmetric-impulse | 144 | 0,0/r |

Each row is an independent exact one-anchor/one-replacement mutant. Every named witness differs in at least one raw Float32 word.

## Structural-only mutations

| Mutation | Contract |
| --- | --- |
| tile-equal-to-notequal | structurally authenticated rejection; pixel identity is algebraically expected |
| tile-all-to-any | structurally authenticated rejection; pixel identity is algebraically expected |
| true-arm-use-canvas-size | structurally authenticated rejection; pixel identity is algebraically expected |
| fullframe-force-false | structurally authenticated rejection; pixel identity is algebraically expected |
| dispatch-force-general | measured pixel identity: at authority 7f47340 no fixture diverges, because the general kernel at angle 135 and height 1 reproduces the default kernel exactly; exact source authentication rejects it |

These rows are intentionally not assigned false pixel witnesses: their shipped-pixel behavior is unobservable (algebraically, or as measured where the contract says so), while exact source authentication rejects them.

## Regeneration

```sh
node docs/port-engineering/arrays/emboss-parity/emboss_parity_oracle_generator.mjs --write --cpu-root "$NOISEMAKER_CPU_ROOT"
node docs/port-engineering/arrays/emboss-parity/emboss_parity_oracle_generator.mjs --check --cpu-root "$NOISEMAKER_CPU_ROOT"
python3 docs/port-engineering/arrays/emboss-parity/generate_emboss_native_oracle_include.py --write
python3 docs/port-engineering/arrays/emboss-parity/generate_emboss_native_oracle_include.py --check
```

Both generators validate pinned authority, complete arrays, checksums, the fixture census, and the full mutation ledger before accepting checked output.
