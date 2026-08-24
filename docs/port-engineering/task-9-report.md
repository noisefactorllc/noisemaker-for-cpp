# Task 9: straight-line scalar/vector math expansion

## Outcome

The typed native slice now contains exactly 21 pinned corpus programs and the
runtime catalog contains exactly 23 sorted factories after retaining the two
Task-5 proof factories. This task added the requested 16 program factories;
it does not advertise any partial multi-pass effect as end-to-end complete.

The four compile-time variants are explicitly default-define-only in the
generated manifest: lens flare `LENS_TYPE=0`, mosaic `MODE=0`, relief `MODE=0`,
and scatter `MODE=0`. No runtime mode binding implies unsupported variants.
Scatter also has an explicit `source-double` numeric-literal contract because
the canonical compiler intentionally skips float-literal lowering for that
effect; the other 20 typed programs retain the normal `glsl-f32` contract.

## Red/green evidence and fidelity repairs

- RED: the allowlist/catalog tests initially found only the five Task-8 typed
  programs and seven total factories.
- RED: synthetic emission stopped at the first unimplemented math builtin, and
  the runtime helper test did not compile before the new overload table existed.
- RED: the 16-key external oracle advanced through precise parity failures in
  mosaic, ridge, and scatter. These exposed three real consumption boundaries:
  canonical hash12/hash22 precision fences (with scatter excluded), vector
  arithmetic rooted in a vector-valued builtin, and scatter's source-double
  literals. Each received a focused positive/negative regression test.
- GREEN: all 16 factories match the frozen canonical F32 and RGBA8 hashes on
  two actual renders. All 16 also fail closed on empty bindings.

The hash handling is deliberately structural: only the canonical hash12 and
hash22 expression shapes receive the source precision fence, ordinary `fract`
does not, and `filter/scatter` is explicitly excluded. Vector scalar splats and
all-scalar vector constructors defer until a real vector consumption/storage
boundary, while arithmetic descended from a vector-valued builtin materializes
at the canonical Float32Array boundary.

## Capability and boundary truth

The typed emitter/runtime now covers the used scalar/vector overloads for
`abs`, `atan` (one and two argument), `clamp`, `cos`, `distance`, `dot`, `exp`,
`floor`, `fract`, `length`, `max`, `min`, `mix`, `normalize`, `pow`, `radians`,
`sign`, `sin`, `smoothstep`, `sqrt`, `step`, `texture`, and `textureSize`.
Focused tests cover scalar/vector forms, zero normalization, NaN and signed-zero
min/max behavior, and chained rounding sentinels. `exp` is included because the
pinned default lens-flare program uses it.

Still excluded: blocks and control flow (`if`/ternary), loops, arrays, globals,
matrices, derivatives, dynamic indexing, structs, UBOs, out/inout, varyings,
textureLod, texelFetch, adapters, render graphs, CLI integration, and stateful
or point-draw execution. The next slice should add blocks/if/ternary before
loops. The typed slice consumes 21 of 212 pinned programs, so exactly 191 corpus
programs remain outside it.

Capability validation explicitly rejects helper parameters declared `out` or
`inout` before emission, with program/line/column diagnostics; synthetic tests
cover both directions so the by-value C++ helper ABI cannot silently admit them.

## Generator and generated artifacts

The schema locks the exact sorted 21-key allowlist, exact default defines, exact
scatter literal exception, and capability vocabulary. The manifest records each
program's define and literal contracts. Generator output remains CWD-independent,
transactional, revision/source-hash locked, timestamp/absolute-path free, and
owned separately from Task 5. Adversarial rollback, tamper, traversal, reserved
name, symlink, device/unexpected-entry, and injected swap tests pass.

| File | SHA-256 |
| --- | --- |
| `src/typed_generated/typed_slice.cpp` | `e71dbd94ab5d1bd5a501f21369ea1d14fcfd231d71cd1137cfa442cda7eb7059` |
| `src/typed_generated/typed_manifest.json` | `c4131995272906f1a274c0704b235ab7f56d695fa45f2b864fbbd81d68cbb36e` |
| Task-5 `src/generated/synth_solid.cpp` | `4a88533b90ce71268461f2d6fc2ad71025deb830e403c878b424b7b0ef822363` |
| Task-5 `src/generated/filter_invert.cpp` | `06dd8cf0dacb86fb4ae11ebc822fd8103f648bc98d8272bc526c4507b2d4f1b7` |

## Oracle provenance and inputs

Oracle revision: `a024dc3a960cc44af454abc7aebce50456c194e6`.
Implementation-time oracle: Node v24.7.0 in
`../noisemaker-for-cpu`, importing the pinned
`canonicalKernelFactories`, `bindCanonicalKernel`, `runPass`, and `Surface`.
Every selected factory source was checked against the pinned corpus source hash.
The oracle is not called by the C++ build or tests; only the resulting hashes
and probes are frozen.

Inputs use top-down `Surface.fromRgba8` with bytes
`[(31x+17y+13t)%256, (11x+47y+29t)%256, (67x+19y+7t)%256,
(255-23x-37y-5t)&255]`: input `5x3,t=1`, blur `3x5,t=11`, color
`7x2,t=23`, edge `4x6,t=37`, simplified `6x4,t=41`, and text `2x7,t=53`.
All outputs are 7x5, nearest/bottom-left sampled, with resolution `(7,5)`,
tile offset `(3,-2)`, full resolution `(17,13)`, time `.125`, and pass seed `7`.
Declared float uniforms are explicitly f32 at binding.

Per-key values: cel edgeColor `(.17,.63,.91)`, mix `.71`; chroma hue/range/
feather `.37/.19/.07`; chrome detail/distortion `63/27`; colorReplace target
`(.23,.51,.77)`, replacement `(.88,.16,.42)`, sensitivity/smoothing/mix/
replaceAlpha/keepAlpha `.43/.18/.67/.82/.31`; deriv amount/scale `1.7/.75`;
lens brightness/center/tint `137/(.29,.61)/(.83,.94,.71)`; mosaic tile/grout/
relief/maxOffset/gapFill/background/seed `4.7/22/58/31/2/(.12,.34,.56)/7`;
photocopy darkness/ink/paper `68/(.08,.17,.29)/(.93,.84,.61)`; relief detail/
angle/balance/grain/ink/paper `57/123/44/36/(.09,.18,.27)/(.92,.79,.63)`;
ridge level `.42`; scatter radius/seed `2.7/11`; aberration displacement `.037`;
text matte/opacity `(.14,.35,.73)/.38`; unsharp amount/threshold `173/14`;
watercolor composite shadow/paper `61/43`. Watercolor seed has no extra binding.

Float32 hashes are SHA-256 of exact little-endian Float32 bytes; RGBA8 hashes
are SHA-256 of output bytes.

| Key | Pinned source SHA-256 | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- |
| `filter/celShading:celShadingBlend` | `182d5b48d026e923aa2c412c659c633541859ffc3e9bc03315d5c5e18385f69f` | `3040fca866a32e77c2d5828672a9d983fd8b78c8f19e81030444b7f922cc144a` | `998a939393905a859371711b5c971f0435ed757720ac5b5a9348e59d652a6409` |
| `filter/chroma:chroma` | `520627b0a7461e42baad13d20851ff4c0a2cb1a7d050776f3592ade9f800dcfb` | `efc59e60e7b127541dbb28cf18d5981144fc4a22f02d4f6d710be29ea0ac06fe` | `72ef0585ff112ea147febd8ede9f8d3965215513c44ddf0feb188790f371c637` |
| `filter/chrome:chMap` | `46cfe00d324444f4b2d7b0ed4d708323ef05cd9927fcec3561f1af1da37b6e08` | `5d0c6dd88fe0a39b97b994002b7431214d59760f9133c2ff40d1e3bebd8ec119` | `bc19edaad2c576252a6f9ea3420422d08286039b8cc15f88aa0e7a6734f18bf8` |
| `filter/colorReplace:colorReplace` | `e85d80a109a48d551d60ff6136efedb4a131e0b973ad9637b82df9b46449f5fb` | `f672cb72086923fa32c34cc12915196bccd211ea450d6cac6dee39649b4d3814` | `33c8b3e38c7d93521a58581c2b1bc0e56547d2afc8d5673aeddca4d2bf26d0ff` |
| `filter/deriv:deriv` | `e1283736b0b1aeacf1bb795eda742871f0b6027bdf98659a3c7fa4a68d91f3ce` | `43e591217a059e9a86f3e00e52a91b0539c2cc3783619dd0f45de04c292fd3a2` | `6a3cbb07be0a133257bd1ca518d82c8269c5b47bd4abd975fe1cb530b70c900e` |
| `filter/lensFlare:lensFlare` | `46ba9da4e66a3978f92b18810bcb5db9d0f2f01fb4a80843c2091381f2001244` | `046d8dc804bf93f97533a85f05783b14a6dcedf09afede6a3660e600676d8599` | `42d035c4d765ef017d27b641bb5a2a96f03122ca19032c1e02233b8d7915cbc4` |
| `filter/mosaicTiles:mosaicTiles` | `1495023febe8ffccc57fa8738c6dc027b57d98e77fc88108ae639a8590c2fd47` | `b45240877494b59e366f9d9441bd2e125365bcd87f000ca363839cdc8bd725b0` | `bacfcc449e6470bfa16347c7b00cf9a2807ec433a060282b32358f2b39a273e1` |
| `filter/photocopy:pcCombine` | `67f0d9c44fe0142c326691427ffa6bb819a9e04bd8bd8c7aa0f639c659aeba03` | `5c30639723acd4eed15826649692300488800a81c4c20d0b9a2cdafb4bfb4405` | `76d6b92b4fb7f0c8e4f465da28246117a0ad5ac0c9c45e43085d1280f0877c6f` |
| `filter/relief:rlShade` | `dda1113e9cca57b25fa93c0843cd19fa76880724059fe1b56c5e5735f671ea90` | `1dba0f21095568d3f62d27d313993dfaa6bae04c1fb0fc81156d583ea3a2d1d6` | `f5205caa03ccc976eefc1c41b9f535ea578a23510cf6154642b16634da32abe6` |
| `filter/ridge:ridge` | `0e3cc0289ff2057145afd5bb8ceeef71bfbbee0aee149eb0f609937f0571694c` | `14e083e0d2e604d0b5559ebbdd175316ae313160e5aca89c468678ef3932eff9` | `5d220bfe0488a6b32a233b82932edee6b8b5e094c478b95f54289d6e0edc1b8b` |
| `filter/scatter:scatterJitter` | `e68ff4dc90236e866895d4720d58e81b9151a67d9cc62b43085efbf634fa4e71` | `3894d5739e765cf71a39a082abb8315bfd5fac4a7d6be6c4f8a8cf9b87ae5c8c` | `d3425ff7218c66a0a0711e3ed96f3c343df410227e22cececf9ad51dc48c42be` |
| `filter/simpleAberration:chromaticAberration` | `c6d3f57f92c9cc0e7e1a1a8e1381699cc0ddb95d83b9d8b1c1a3da19d782f245` | `09c9d93ea78ddb0f877dd993f6af3f5b7d7ffd9c10d05fe4dc2f4b505f1af7e6` | `42c44f9ac2cd9b55e1dc92abd18afa3960b6a7982d44e9463db03717b207b760` |
| `filter/text:text` | `be62b513c1fb56f34d23ace109b76a525454f5a5dbac64239949d6faf16e7462` | `a6dba9bbe4b6dfeab15bfc45089f5255e359d292a1a7199ca76ce42da549b134` | `cde2a1348bc93ad9c33a91b3ae4c3c711af183490b365ffd967fd296f9e7e2de` |
| `filter/unsharpMask:usmCombine` | `d5bc1d96fd7f241579d705688045ef2ba4975c382c99e1aec3f1f69bf0b3c03c` | `dcb8cd1ae6f41bba9ab35d807a4d89d158605be5a2fb5b8bd199def2d06970a5` | `c5c85cddd59a4e9c9c6e98e316ad8de4074dffbd4787c841a5cd1b6f80829630` |
| `filter/watercolor:wcComposite` | `b3f03b27f84a4a9629c1eb2808edaaf63a3c696fa385e871d853cacce21dcaa6` | `409c8f37bb8778750cedc218f2ca6d488ad6fffe1c090c786d7e3c582bde5a3b` | `1bdc0c3ae9f57ef445f25fa3e3cac55cbcfbba28745b0a2af58c885a6d514bc4` |
| `filter/watercolor:wcSeed` | `e3158e856ebb45df82222fcf26708c83d5bdba7b9af2f017e18f4fde696633da` | `29f8cb0bcb53dac6c6c0f32405d5ee0670617a236c5b59c2aa9d3536637abe0a` | `b758a60117b29acbcaa0d2e74eaef9487d06f80d1cf5363df30967a981e0df2f` |

## Final verification

- Full Python suites: 49/49 passed (`test_corpus`, `test_semantic`, legacy
  generator, typed generator).
- `check_corpus.py --check`: passed.
- `check_semantics.py --check`: 212/212 bodies passed; the pinned checker also
  covers all 622 metadata candidates and 646 pass variants.
- `generate_kernels.py --check`: passed; Task-5 output hashes unchanged.
- `generate_typed_slice.py --check`: 21 programs, byte-identical.
- Debug configure/build: strict-warning build passed; native tests 66/66;
  CTest 1/1.
- Release configure/build: strict-warning build passed; native tests 66/66;
  CTest 1/1.
