# Task 11 Acceptance Report: ten additional CPU factories

Date: 2026-08-10  
Repository: `.`  
Pinned upstream revision: `a024dc3a960cc44af454abc7aebce50456c194e6`

## Result

Task 11 is complete. The immutable typed slice contains exactly 44 sorted programs, the public runtime catalog contains exactly 46 sorted unique factories, and 168 of the 212 pinned programs remain outside the typed slice. The ten new factories all have `defines = {}` and public declarations in `include/noisemaker/generated/catalog.hpp`.

Added program keys:

1. `classicNoisedeck/splat:splat`
2. `filter/corrupt:corrupt`
3. `filter/flipMirror:flipMirror`
4. `filter/outline:outlineBlend`
5. `filter/outline:outlineValueMap`
6. `filter/spatter:spatter`
7. `filter/tint:colorize`
8. `mixer/blendMode:blendMode`
9. `mixer/centerMask:centerMask`
10. `synth/media:mediaInput`

## Language and runtime boundary

The schema now locks the exact type vocabulary:

`bool, float, int, uint, vec2, vec3, vec4, ivec2, ivec3, ivec4, uvec2, uvec3, uvec4, mat2, sampler2D, void`

It locks binary operators:

`!=, %, &&, *, +, -, /, <, <=, ==, >, >=, >>, ^, ||`

It locks assignment operators:

`*=, +=, -=, /=, =, ^=`

New admitted shapes are deliberately narrow:

- `uint` and `uvec2/3/4` constructors/conversions required by the pinned PCG source.
- Componentwise unsigned `>>`, `^`, and `^=` only; shift counts are masked to five bits and arithmetic wraps modulo 2^32.
- Scalar signed/unsigned integer `%` with defined zero-divisor and `INT_MIN % -1` behavior.
- Multi-declarator statements emitted as separate source-ordered declarations with stable symbol identities.
- Only scalar `mat2(a,b,c,d)`, stored column-major, and only `mat2 * vec2`.
- Literal-only float trees are folded using JS Number arithmetic, then narrowed once at the canonical GLSL Float32 boundary. The scatter-only `source-double` contract remains distinct.
- Helper-backed vector operations materialize plain arithmetic operands at the same Float32 boundary as the canonical typed-array lowering.

Still rejected fail-closed with program/line/column diagnostics: loops, arrays, non-const globals, structs, UBOs, varyings, derivatives, discard, dynamic indexing, out/inout parameters, `textureLod`, `texelFetch`, general matrices, matrix uniforms/parameters, signed shifts, `<<`, `&`, `|`, float bitwise/remainder, and unsupported compound assignments.

Compatibility transforms remain schema-locked and structural:

- `filter/corrupt:corrupt` uses `corrupt-sample-uv-alias-v1` to preserve the canonical `sampleUv` typed-array alias at the exact symbol-bound call site.
- `synth/polygon:shape` retains `polygon-zero-smoothing-v1`.
- No outline-specific source rewrite exists; the OKLab cube-root parity issue was resolved by the general canonical literal-folding rule.

## Pass truth and caller obligations

- `filter/outline:outlineValueMap` is outline pass 0 / stage 1 only.
- `filter/outline:outlineBlend` is outline pass 2 / stage 3 only and requires caller-provided `edgesTexture` produced by the unported `outlineSobel` stage after ValueMap.
- `synth/media:mediaInput` requires caller-provided `imageTex`.
- The other seven added factories are single-pass.

Binding tests cover nine distinct new uniform signatures with both missing and wrong-type failures and thirteen required-sampler cases, including `inputTex`, `tex`, `edgesTexture`, and `imageTex`. A native compile/use guard takes the address of every new public factory declaration so header drift fails compilation.

## Oracle provenance and fixture contract

Final oracle artifact: `docs/port-engineering/task-11-oracles.json`  
SHA-256: `e5586ffc4a76fbcc61b2e651b97e850d174cf1db99aa949689a3d8a812914583`  
Schema: 1  
Node: `v24.7.0`  
API: `canonicalKernelFactories+bindCanonicalKernel+runPass`  
Factory hash contract: SHA-256 of exact UTF-8 `Function.prototype.toString()` bytes.

This final ledger is the root-controller-authorized replacement for the initial
93-variant artifact SHA-256
`f61a22328edb365bdd3f8c93916750ce5ef6d081038c04b2e146dd9a23accdb6`.
The initial ledger was rejected before acceptance because its corrupt,
center-mask, media, and outline fixtures were less discriminating and its
factory-hash byte contract was not explicit. The replacement adds corrupt
`mixedLowBits`, strengthens those fixtures, states the exact hash contract, and
was independently checked for all ten factory hashes, every raw source hash,
and two byte-identical renders of all 94 variants. The dated acceptance
amendment is recorded in `task-11-brief.md`.

Base output is 7x5 top-down, sampled nearest with bottom-left shader coordinates. Base pass values are tile offset `(3,2)`, full resolution `(13,11)`, time `f32(.125)`, seed `f32(7)`, with runtime resolution canonically overwritten to `(7,5)`. Formula fixtures use deterministic asymmetric RGBA8 bytes; tint additionally uses a literal gray/chromatic hybrid, outline uses grayscale and an exact-red edge override, and media uses 17x13 asymmetric and transparent fixtures so placement, tiling, flipping, bounds, and alpha paths are observable.

Each of 94 variants was rendered twice byte-identically. Native verification requires, for every variant, the exact little-endian Float32 SHA-256, exact RGBA8 SHA-256, dimensions, orientation, alpha behavior, and twelve exact float-bit probes from pixels 0, 17, and 34.

Branch matrix:

| Program | Variants | Covered cases |
|---|---:|---|
| `classicNoisedeck/splat:splat` | 8 | primary, disabled/no-specks, splat modes 0/1/3, speck modes 0/1/2 |
| `filter/corrupt:corrupt` | 4 | clean, full, mid bits, mixed low bits |
| `filter/flipMirror:flipMirror` | 12 | modes 0/1/2/3/11/12/13/14/15/16/17/18 |
| `filter/outline:outlineBlend` | 2 | black and white outline |
| `filter/outline:outlineValueMap` | 2 | OKLab color and grayscale |
| `filter/spatter:spatter` | 2 | primary and fallback resolution |
| `filter/tint:colorize` | 3 | modes 0/1/2 |
| `mixer/blendMode:blendMode` | 16 | every mode 0 through 15 |
| `mixer/centerMask:centerMask` | 19 | shapes 0/1/2/-1 and blend modes 0 through 13 plus 15 |
| `synth/media:mediaInput` | 26 | positions 0-8; tiling 1-3; flips 1/2/3/11-18; out-of-bounds; transparent; zero-scale guard |

The media zero-scale guard is intentionally equivalent to centered position 4 at scale 100; the other 25 media variants have 25 distinct Float32 hashes.

## Source provenance

| Program | Raw source SHA-256 | Canonical factory SHA-256 |
|---|---|---|
| `classicNoisedeck/splat:splat` | `cfdcc4edcc5097043ad72602feb62a40622c14ba1bee66fb1ac2e414d1b3cced` | `a4238c0fa17c69e89910c708d7a46f6eff49043a11f8851b67384f2e05a2451a` |
| `filter/corrupt:corrupt` | `b81642d2e63294f9f51656eb2441cdaf479c495c5e4acb0d3a4907a13b070d02` | `7c8e4652a1e8787dfd8b226e76cbfbd4d3a330ad8c17a7730d161a72f58fe25f` |
| `filter/flipMirror:flipMirror` | `696263e373913b7ab71430189fb7626ca966780ff645384b89509cf9d1a3fa7e` | `0d29e4d562a208ffb4b5911b186539f452880ea8a058af07b2df8fcf1cddc113` |
| `filter/outline:outlineBlend` | `5cf1613b00702bda4ccd5a03c1beee0aa779c1a947dc77d2adb78c854dad1a0d` | `082079151de99925485a7ab66362752d0b64f236d312bdfd924acba37d3b546e` |
| `filter/outline:outlineValueMap` | `8d6504a8464a44cb4d1e86d2596c0d7a60d4924d18bd2114dc1f5ce5d49434cb` | `7d03750cc4e3c8225840e70340dab1edbab225ef63026650c41bf46b118a4a8a` |
| `filter/spatter:spatter` | `9d8cb56f43761cdb52a36935a7c3b66d758189d82db0c52ad93b5090206579af` | `9430e004fda86cbb8dca735314b0b8da8a9c18130440a5a74db3b53beeb4f52d` |
| `filter/tint:colorize` | `2af8eca3f8e54ddde3decc2d6bc03723833b50239ade32de04b968d3b88359a6` | `c4308bccb7126fd7e45a280bf397742193cd79a4b72994b81966da040ea189b9` |
| `mixer/blendMode:blendMode` | `a33eb805a9ee8fe2ee5b807db1141a5570afa84af92a5c65db7a2f828a6d9e66` | `2252c783080476c75eaa349acf7c0e82b0d3813c54ca2f84b08e93b1b82bbbe5` |
| `mixer/centerMask:centerMask` | `55d708d50af0c0d0a6caf8a32ca3621f8137ff0d489aeb8d5f579e20984599e2` | `95d1869309242dc9f61acfc21af7ec342b4244188cadd9f845cbae5cb5d96490` |
| `synth/media:mediaInput` | `2e984ec5f95008b83fdccd3bc3e266a4c68b58488096d9de343ff16f0199313e` | `347dd57642761747ab4be2eae33483364440e3b54f5fe2a05eb785081236bd9a` |

## Generated artifacts and retained proofs

| Artifact | SHA-256 |
|---|---|
| `src/typed_generated/typed_slice.cpp` | `0a7a38f30524e8eff499b3e00c12343aa36561f90b95e94ec47aa55a2bc8d0e8` |
| `src/typed_generated/typed_manifest.json` | `c8fa7afd316e8c7be42818363f8d031d87044823f662f9d928f06d4577c60488` |
| `tools/glslcpp/typed_slice.json` | `d1c31e90eb99b524f3d890383672f4b97927f13c494966a81967a2b364f1790b` |
| `include/noisemaker/generated/catalog.hpp` | `10912e175d07b4c2e815c2c53de5d2e6511ab41fd70d342d218deed705ec6018` |

Task 5 immutable generated proofs remain byte-identical:

- `src/generated/synth_solid.cpp`: `4a88533b90ce71268461f2d6fc2ad71025deb830e403c878b424b7b0ef822363`
- `src/generated/filter_invert.cpp`: `06dd8cf0dacb86fb4ae11ebc822fd8103f648bc98d8272bc526c4507b2d4f1b7`

The native suite also re-verifies all 34 prior Task 8-10 oracle hashes exactly.

## Verification record

All commands ran without Git, branches, worktrees, commits, pull requests, network access, or sibling-tree mutation.

- `python3 -m unittest discover -s tests -p 'test_*.py' -v`: 62 tests passed in 242.151 seconds.
- `python3 -m tools.glslcpp.check_corpus --check`: passed; exact 212-source corpus.
- `python3 -m tools.glslcpp.check_semantics --check`: passed; 212 bodies, 622 metadata candidates, 646 variants.
- `python3 -m tools.glslcpp.generate_kernels --check`: passed; legacy Task 5 output drift-free.
- `python3 -m tools.glslcpp.generate_typed_slice --check`: passed; exact 44-program typed slice.
- Fresh Debug configure/build in `build-task11-debug`: passed under AppleClang 16.0.0 with `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`.
- Fresh Debug CTest: 1/1 passed; direct executable: 76 passed, 0 failed.
- Fresh Release configure/build in `build-task11-release`: passed under the same strict warning and FP contract flags.
- Fresh Release CTest: 1/1 passed; direct executable: 76 passed, 0 failed.
- Placeholder/abandoned-implementation scan found no Task11 placeholder, outline exponent rewrite, or experimental JS-math runtime.

No known acceptance failure remains.
