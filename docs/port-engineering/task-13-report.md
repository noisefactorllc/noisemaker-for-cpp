# Task 13 Acceptance Report: exact level-zero `texelFetch` slice

Date: 2026-08-10  
Repository: `.`  
Pinned upstream revision: `a024dc3a960cc44af454abc7aebce50456c194e6`  
Implementation brief SHA-256: `b34c155042aaa6737c79058d70081ea37e53f8b22aed25bb16946488e1ef2462`

## Result

Task 13 is complete. The immutable typed slice contains exactly 65 sorted programs, the public catalog contains exactly 67 sorted unique factories, and exactly 145 of the 212 pinned corpus programs remain without a native public factory. The immutable legacy `filter/invert:inv` and `synth/solid:solid` factories remain outside typed generation and were neither duplicated nor regenerated.

Every new authoritative default define map is exactly `{}`:

1. `filter/bloom:brightPass`
2. `filter/bloom:composite`
3. `filter/fibers:fibersBlend`
4. `filter/normalize:apply`
5. `filter/pixelSort:luminance`
6. `filter/reindex:nmReindexApply`
7. `filter/scratches:scratchesBlend`
8. `filter/strayHair:strayHairBlend`

## Typed/runtime boundary

The schema adds exactly one capability, `texelFetch`. The validator and emitter admit only:

`texelFetch(sampler2D, ivec2, source literal 0) -> vec4`

The exact source token is required to be the decimal integer literal `0`. Nonzero and negative literals, hexadecimal zero, arithmetic expressions, local variables, uniforms, floating or scalar coordinates, wrong arities/types, other sampler classes, and `textureLod` fail closed with located diagnostics. Loops and indexing remain rejected, so `filter/pixelSort:computeRank` and `filter/pixelSort:gatherSorted` are not admitted.

Typed emission calls the dedicated generated helper `fetch_texel(surface, coord)`. That helper calls the existing `texel_fetch_bottom_left(surface, coord[0], coord[1])`, then constructs `glsl::Vec4` from the four stored Float32 lanes. It does not substitute normalized `texture()` sampling.

The runtime contract retains:

- bottom-left integer shader coordinates over top-down `Surface` storage;
- signed integer coordinates and edge clamping for negative and oversized coordinates;
- exact heterogeneous Float32 lanes and alpha;
- deterministic repeated fetches.

Focused tests cover `(0,0)`, the opposite corner, negative/oversized clamping, alpha, exact stored lanes, and repeatability. The eight admitted source bodies cannot produce negative fetch coordinates; the external-oracle report therefore makes no unreachable negative-coordinate claim.

No compatibility transform or numeric-literal exception was added. All four Task 12 compatibility transforms and the sole pre-existing scatter `source-double` contract remain schema-locked and unchanged. No loop, array, dynamic-index, global, struct, UBO, varying, derivative, parameter-direction, matrix expansion, nonzero mip, textureLod, or unrelated builtin frontier was admitted.

## Bindings and effect-graph truth

The Task 13 binding matrix exhaustively covers all 20 declared uniform positions and all 14 declared sampler positions. Every uniform is tested both missing and with a representative wrong alternative type; every sampler is tested missing. In particular, strayHair retains exact `ivec2` types for `tileOffset` and `fullResolution`, plus float `renderScale`, even though those authored uniforms are behaviorally unused.

Sampler routes are locked exactly as authored: `inputTex`, `bloomTex`, `overlayTex`, and `statsTex`. A compile/use guard takes the address of every new public binder.

These are partial passes, not complete effect graphs:

- Bloom brightPass is pass 1 of 3. Composite is pass 3 and requires caller-provided `bloomTex`; the middle gather pass remains unported.
- Normalize apply is pass 4 and requires caller-provided 1x1 `statsTex`; producer passes remain unported.
- PixelSort luminance is only its luminance pass; the remaining pipeline is unported.
- Reindex apply is pass 3 and requires caller-provided 1x1 `statsTex` plus `uDisplacement`; producer passes remain unported.
- Fibers, scratches, and strayHair blend are individually executable blend passes requiring caller-provided `inputTex`, `overlayTex`, and `alpha`.

No adapter or render graph was added.

## Oracle provenance and branch matrix

Accepted artifact: `docs/port-engineering/task-13-oracles.json`  
SHA-256: `7d98bc24101b967a13156a544484786b3255ca2e07bd4f55d47f0bc62973b829`  
Schema: `noisemaker-task13-canonical-oracles-v1`  
Node: `v24.7.0`  
API: `canonicalKernelFactories+bindCanonicalKernel+runPass+Surface`  
Factory hash contract: SHA-256 over the exact UTF-8 bytes returned by `Function.prototype.toString()`.

The artifact contains exactly 21 unique key/variant rows for the exact eight-source set. Every canonical row was rendered twice byte-identically. Native verification repeats each render and checks exact little-endian Float32 SHA-256, RGBA8 SHA-256, 9x7 top-down dimensions/orientation, alpha, and twelve exact RGBA Float32 bit probes at pixels 0, 31, and 62.

Base values are output 9x7 top-down, time `f32(.375)`, seed `f32(7)`, tile offset `(-7,5)`, and full resolution `(17,13)`. Fixtures include asymmetric 5x3, 4x6, and 7x2 formula surfaces, a heterogeneous literal 3x3 luminance surface, distinct ranged/flat 1x1 stats surfaces, and a nonopaque 4x6 overlay.

| Program | Cases | Covered cases |
|---|---:|---|
| `filter/bloom:brightPass` | 3 | soft-knee below/ramp/above, fully below, fully above, high-coordinate clamp |
| `filter/bloom:composite` | 2 | zero intensity/alpha preservation; positive tinted HDR addition and clamp |
| `filter/fibers:fibersBlend` | 3 | alpha 0, 0.53, and 1 with overlay route and base alpha retention |
| `filter/normalize:apply` | 2 | ranged normalization; flat-range divide-by-zero guard |
| `filter/pixelSort:luminance` | 2 | heterogeneous OKLab luminance/normalized x; nonsquare high-coordinate clamp |
| `filter/reindex:nmReindexApply` | 3 | positive range/displacement; flat-range fallback; zero displacement |
| `filter/scratches:scratchesBlend` | 3 | alpha 0, 0.53, and 1 max-blend with base alpha retention |
| `filter/strayHair:strayHairBlend` | 3 | two distinct integer-system bindings proving unused-system equivalence; alpha 1 |

All 21 cases matched the accepted artifact on the first native oracle run; no parity compatibility seam was needed.

## Source provenance

| Program | Raw source SHA-256 | Canonical factory SHA-256 |
|---|---|---|
| `filter/bloom:brightPass` | `db9bb2dbe897ee03435cae86aa88a766b7d8e6bc58e61103fa5e66c3c3dbc880` | `a743462868665c5aeb90776e0d4769292018f4e93ab7b6452e23571c3aee2ac8` |
| `filter/bloom:composite` | `28e480fad84b7254e9392b8d4d85bc398b62a0e57f94dffac94db655132abbef` | `c785331dac99841e1bf32813bd2702036600eb23da7d3a5eff79df633e345260` |
| `filter/fibers:fibersBlend` | `3c541fbfa45fa98cbfd67c2c7c8a91e4167867a3935681163260733c19cb7575` | `ed94b776d7ed02ba469346a2fdd2ffcf7bf764b52e70bff523447f13dac25a57` |
| `filter/normalize:apply` | `c59c0bad843a38c823bd2fc6396d0b9bca1cac7f1fe074aaf5dbc9622522e855` | `4f7886bfdaab15e96025b6ed635324d15d908583127c0ee138e1c9b6d50362d0` |
| `filter/pixelSort:luminance` | `da27454ff4cc3fcc40b296c8ea8bd8913a00165b2c001aef3cd9e6bd05db0298` | `bcd29820617f79fea392ff510b2c924886ad6bc848a5cd6e1b9528628c63f09f` |
| `filter/reindex:nmReindexApply` | `651bb6930d3fe51629fc3a17c88bfa7c7831e78fa18be0ea16d0f3f9d3c5154d` | `70e57b5473d572c270db0453b05c366162f0998289e93d6d6816a8a8ae1abc2e` |
| `filter/scratches:scratchesBlend` | `db76fc1b477acfa7e9a2d22ca532a9d29ed4034ec695d4f4b75ed8741ce63c63` | `0d731cc78adf32ec44389012d5fc9795f024d94885e744b6e0f064ea6c7ea02b` |
| `filter/strayHair:strayHairBlend` | `bacff9ec121ac6e28d377702145eb14cdd8dfa2cbfc4ec9ba89765f658b1345c` | `baeaa10b7fc9b281d5e328c58aa5c50fae338e58a50b69650053b29ebee768dc` |

## Generated artifacts and retained proofs

| Artifact | SHA-256 |
|---|---|
| `src/typed_generated/typed_slice.cpp` | `9a841df6c7fd9c8a9b2b16379a2f3752644cbbc4e7500e113592f4918ad5c6c2` |
| `src/typed_generated/typed_manifest.json` | `664b488dc4a881149af4624509959f10912a24065b74559d106efccd2f2a778c` |
| `tools/glslcpp/typed_slice.json` | `56044b5cc0b8fb7cfee288d45d4ffb57df1bf6d9f723fc654cede392f5ed2ae7` |
| `include/noisemaker/generated/catalog.hpp` | `b60961bc78b8909cae53640df1a5b9c6b39c887d03a48883d43c914ba1d6299d` |

Task-5 immutable proofs remain byte-identical:

- `src/generated/synth_solid.cpp`: `4a88533b90ce71268461f2d6fc2ad71025deb830e403c878b424b7b0ef822363`
- `src/generated/filter_invert.cpp`: `06dd8cf0dacb86fb4ae11ebc822fd8103f648bc98d8272bc526c4507b2d4f1b7`

The native suite also re-verifies all 94 Task-11 cases and all 120 Task-12 cases exactly.

## Verification record

All commands ran without Git, branches, worktrees, commits, pull requests, sibling-tree writes, or new runtime dependencies.

- `python3 -m unittest discover -s tests -p 'test_*.py' -v`: 67 tests passed in 428.785 seconds.
- `python3 -m tools.glslcpp.check_corpus --check`: passed; exact pinned corpus.
- `python3 -m tools.glslcpp.check_semantics --check`: passed; 212 bodies.
- Full-suite schema tests retain exact 622 metadata candidates and 646 variants.
- `python3 -m tools.glslcpp.generate_kernels --check`: passed; legacy Task-5 generation drift-free.
- `python3 -m tools.glslcpp.generate_typed_slice --check`: passed; exact 65-program typed slice.
- Fresh Debug configure/build in `/tmp/noisemaker-cpp-task13-impl-debug`: passed under AppleClang 16.0.0 with `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`.
- Fresh Debug CTest: 1/1 passed; direct executable: exactly 84 passed, 0 failed.
- Fresh Release configure/build in `/tmp/noisemaker-cpp-task13-impl-release`: passed under the same strict warning and FP-contract flags.
- Fresh Release CTest: 1/1 passed; direct executable: exactly 84 passed, 0 failed.

No known Task 13 acceptance failure remains. Work stops here before Task 14 repository changes for independent review.
