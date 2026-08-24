# Task 12 Acceptance Report: GLSL `mod` slice

Date: 2026-08-10  
Repository: `.`  
Pinned upstream revision: `a024dc3a960cc44af454abc7aebce50456c194e6`

## Result

Task 12 is complete. The immutable typed slice contains exactly 57 sorted programs, the public runtime catalog contains exactly 59 sorted unique factories, and exactly 153 of the 212 pinned corpus programs remain without a native public factory. The immutable Task-5 `filter/invert:inv` and `synth/solid:solid` factories remain the only public factories outside the typed slice and were neither duplicated nor regenerated.

All thirteen additions have authoritative default define maps exactly `{}`:

1. `classicNoisedeck/coalesce:coalesce`
2. `classicNoisedeck/composite:composite`
3. `filter/hs:hs`
4. `filter/repeat:repeat`
5. `filter/scale:scale`
6. `filter/scroll:scroll`
7. `filter/translate:translate`
8. `mixer/patternMix:patternMix`
9. `mixer/shapeMask:shapeMask`
10. `mixer/split:split`
11. `mixer/uvRemap:uvRemap`
12. `synth/modPattern:modPattern`
13. `synth/pattern:pattern`

## Runtime, emitter, and fail-closed boundary

The schema adds exactly the `mod` capability and the typed emitter maps only the admitted GLSL `mod` builtin to `glsl::mod`.

- Scalar evaluation is `x - y * floor(x / y)` through `noisemaker::glsl_mod(double,double)`. The public scalar builtin accepts double arguments so arithmetic is not narrowed prematurely, then returns `float` to preserve the canonical JS scalar builtin result boundary. It does not use `%` or `std::fmod`.
- Vector support is constrained to exactly two lanes: `Vec2/Vec2`, `Vec2/double`, `FloatExpr<2>/Vec2`, and `FloatExpr<2>/double`. The two RHS-expression call shapes are explicitly deleted so `FloatExpr<2>` cannot enter the right operand through the otherwise implicit `Vec2` materialization.
- Stored vec2 lanes are consumed at Float32 and each result is stored through the existing `map_float`/`map_float2` boundary.
- Runtime tests cover negative operands, non-integral and negative divisors, scalar/vector forms, signed zero and nonfinite results, the mirror idiom, pending-expression consumption, and exact output lane bits.
- Compile-time concepts reject scalar/vec2, vec3/vec4, `Vec2/FloatExpr<2>`, and `FloatExpr<2>/FloatExpr<2>` calls while proving both permitted left-expression forms.
- Typed-emitter tests require exact `glsl::mod(...)` spelling and reject wrong arity, scalar/vector reversal, integer arguments, vec3/vec4 widths, and adjacent unsupported builtins including `ceil`, `reflect`, `any`, `floatBitsToUint`, derivatives, and `texelFetch`, with located diagnostics.
- No additional loop, array, global, matrix, struct, UBO, varying, parameter-direction, derivative, textureLod, texelFetch, discard, indexing, integer operator, or unrelated builtin frontier was admitted.

## Canonical compatibility seams

The final schema contains four exact, fail-closed compatibility transform names. The two pre-existing transforms remain unchanged in purpose; Task 12 added two transform names covering three parity repairs discovered from first-bit canonical oracle mismatches.

- `classicNoisedeck/coalesce:coalesce` uses `coalesce-uv-alias-v1`. It preserves the canonical typed-array alias chain from `st` through `leftUV` and `rightUV` at exactly the `cloak(vec2)` and `main()` symbol sites. It also preserves four canonical vector-conditional lowering results in blend modes 2, 3, 7, and 15. The transform records and requires the exact unique `(mode, source symbol, constant, false builtin)` tuple set; focused duplicate, missing, wrong-mode, wrong-symbol, scalar-condition, and wrong-builtin cases fail closed.
- `mixer/shapeMask:shapeMask` uses `shape-mask-sequential-lanes-v1`. It preserves canonical JavaScript typed-array sequential lane writes for the exact `sdfTriangle(vec2,float)` assignment and the two exact `sdfStar5(vec2,float)` compound assignments. The second lane reevaluates expressions after the first lane write. Function, symbol, operator, guard, match-count, and emitted-block shape are locked by focused near-miss tests.
- `filter/corrupt:corrupt` retains `corrupt-sample-uv-alias-v1` for its exact `sampleUv` alias call site.
- `synth/polygon:shape` retains `polygon-zero-smoothing-v1` for its exact canonical zero-smoothing call site.

The sole numeric-literal exception remains the pre-existing `filter/scatter:scatterJitter = source-double`; Task 12 adds none.

## Binding and effect-graph truth

All thirteen programs are single-pass. No adapter or render graph was added.

- Coalesce and composite require caller-provided `inputTex` and `tex`; host `mix` maps to shader binding `mixAmt`.
- Pattern mix, shape mask, split, and UV remap require caller-provided `inputTex` and `tex`.
- Hue/saturation, repeat, scale, scroll, and translate require caller-provided `inputTex`.
- Mod pattern and pattern are texture-free.

The negative binding matrix covers thirteen distinct representative uniform signatures with both missing and wrong-type failures, plus all seventeen required sampler positions. A native compile/use guard takes the address of every new public binder declaration.

## Oracle provenance and fixture contract

Final oracle artifact: `docs/port-engineering/task-12-oracles.json`  
SHA-256: `b0697f49f09ae3565c6e4505e2a09e3ac5e08714e04fab5492c9d5665999cc9a`  
Schema: `noisemaker-task12-canonical-oracles-v1`  
Node: `v24.7.0`  
API: `canonicalKernelFactories+bindCanonicalKernel+runPass+Surface`  
Factory hash contract: SHA-256 of the exact UTF-8 bytes returned by `Function.prototype.toString()` for the canonical factory.

The ledger contains exactly 120 unique key/variant pairs for the exact thirteen-source set. Every canonical variant was rendered twice byte-identically. Native verification repeats every render and checks the exact little-endian Float32 SHA-256, RGBA8 SHA-256, 9x7 top-down dimensions/orientation contract, and twelve exact RGBA Float32 bit probes at pixels 0, 31, and 62. Alpha behavior is therefore covered both by full RGBA hashes and exact probed alpha lanes.

Base pass values are output 9x7 top-down, tile offset `(-5,3)`, full resolution `(17,13)`, time `f32(.375)`, and seed `f32(7)`; canonical bindings overwrite resolution/aspect with `f32(9,7)` and `f32(9/7)`. Texture fixtures include asymmetric 5x3, 7x2, and 4x6 formula surfaces, two nonopaque constants, and a negative-hue constant that forces the scalar negative-`mod` path.

## Oracle branch matrix

| Program | Variants | Covered cases |
|---|---:|---|
| `classicNoisedeck/coalesce:coalesce` | 29 | blend modes 0-18; HSV modes 1000-1005; cloak path; factor `== .5`; factor `< .5`; negative mix amount |
| `classicNoisedeck/composite:composite` | 20 | blend modes 0-15; mode-0 far threshold; mode-1 far; mode-2 near/far greenscreen arms |
| `filter/hs:hs` | 6 | all six 60-degree HSV sectors with a negative rgb2hsv `mod` input |
| `filter/repeat:repeat` | 3 | mirror, repeat, and clamp/fallback wrapping on negative tiled coordinates |
| `filter/scale:scale` | 3 | mirror, repeat, and clamp/fallback scaling coordinates |
| `filter/scroll:scroll` | 3 | all wrap modes with negative offsets and non-square full coordinates |
| `filter/translate:translate` | 3 | all wrap modes including negative mirror `mod` |
| `mixer/patternMix:patternMix` | 12 | pattern arms 0-8; invert; unknown-pattern fallback; full-resolution fallback |
| `mixer/shapeMask:shapeMask` | 12 | shape arms 0-7; invert; animated pulse; unknown-shape fallback; full-resolution fallback |
| `mixer/split:split` | 5 | static; animated even/odd modulo arms; invert xor; full-resolution fallback |
| `mixer/uvRemap:uvRemap` | 7 | both map sources, channels 0-2, wraps 0-2, and combined fallback arms |
| `synth/modPattern:modPattern` | 4 | blend/shape arms with animation modes 0-2 and fallback RGB branch |
| `synth/pattern:pattern` | 13 | pattern arms 0-11, animation branches, negative tiles, and unknown-pattern fallback |

Known authored/fixture-conditioned equivalences remain separately recorded and tested: coalesce modes 2/3/7/15; four composite equivalence groups; and UV-remap `map1_channel2_wrap2`/`fallbacks`.

## Source provenance

| Program | Raw source SHA-256 | Canonical factory SHA-256 |
|---|---|---|
| `classicNoisedeck/coalesce:coalesce` | `a0f96df68ce058e5e2154c78880b5a611eaf5ab9adcd64242368978c813b6b58` | `bfdfd1ceb1aa2b75f751198b169a427f00b1af8e0b5594f0e7a6a7f032550a76` |
| `classicNoisedeck/composite:composite` | `ae3f29a129016653a5705647cb61c5c6448504e44ad321539fb4ce2e120d9123` | `526ce6655cb361a420686cecdec82a9b1aef2f88ea15dff8543068dd1f297bdf` |
| `filter/hs:hs` | `5449441668f1ed62da954294285b5fbeae48b7c9feeecbfbe3b56bcc9afae4d7` | `5c213702d23b807786c66be0d616435962571353201c2452c82225564870b585` |
| `filter/repeat:repeat` | `6fe9a919129c3424f66c145aca77b4a4101c7edc46828c2d85bff40d4f67ebbc` | `0583968f42e073da6e6fc0785570c8c90b81b36f64ed69ca874317fbd5987248` |
| `filter/scale:scale` | `a45f000ee12c498d7a11a04ecc56e911c9fc804ad9cde60cc7cea47533a19ce3` | `1b09cf8be5e9ad3fb0562f03d146487d3b37dd3aa2eb194c18ead47a93e61d9a` |
| `filter/scroll:scroll` | `ce2117916b0d9513890942332835c6cfd1753a39d9d773626c66c6107050d457` | `789e28bf42b58d1f37bc792da97dbd95c605f417c2a3043aea354257cce5e1c4` |
| `filter/translate:translate` | `70f5c44a2d8275f3dd51a9c11fa997dbb0ffc829c5b3565d651ebbfa246db987` | `1ddb6a5b87d17b2980429288907c48c8966215acf29904fd0230d7811c233dd1` |
| `mixer/patternMix:patternMix` | `b7fab7bc3646f4936fa2f730a07df9ffb9fd36b21250410fc5d0f4718a06d21d` | `705d7ea1b621e206faafbdbcdda9d80004e903a971dd32ff8fab553a601c2d33` |
| `mixer/shapeMask:shapeMask` | `2503c37ae4bb9f81b5d77931445b69743067b7e43370a50779d5a09d86bf0374` | `efca4bf4386ab77e1f9aeb74cdd29d8055f46841669b60e773a7b36a71f1f3b6` |
| `mixer/split:split` | `5e6aa68831e8e5749d76f8cc9721d2dadca6149f06f79991bdf671106f04c0b8` | `0eafdc490c031452eb335f6871c9e11dca9b976f01fca631ab8cbd14f985c713` |
| `mixer/uvRemap:uvRemap` | `ec2514ab283fa6cd67687c3cbf717d4d8596d3bdc075a7ea3d7c7dab800694e5` | `b22891498e48bf505b58529763b8441ae23c4ab51cd68b47b0b8a9c868e01711` |
| `synth/modPattern:modPattern` | `5bf4fc9ed8fdf68fa58e9c66f79e1f42624234500f89fb1ee63da64839d3dc2e` | `f8d396510b4848adea02993065bf5707b57be91167dc77345d8044bd53013284` |
| `synth/pattern:pattern` | `d3ce98d432c1548553fac6446a040d2dab8f0fbb7f852457aa4fc4f139d44c5c` | `a308ea050c1a34d2777fe353bbb8a779b721363c4262757096de20146e18defd` |

## Generated artifacts and retained proofs

| Artifact | SHA-256 |
|---|---|
| `src/typed_generated/typed_slice.cpp` | `4bcdafc0ad7cbd0b82d1bec82171977d502773d06bd74ae2e188c7869af86cc3` |
| `src/typed_generated/typed_manifest.json` | `2eb6f65cbb2484de11cc289931c2cd8242ecae2833ef15aa582240237312dd08` |
| `tools/glslcpp/typed_slice.json` | `709af25f8272380459b0466b0ab35b700c7b67f03d9dd1586a4613982969d550` |
| `include/noisemaker/generated/catalog.hpp` | `cd92f1983aaac3643030157a8ac5a67a65cf9d3f9ce0a04b2d10a24530101768` |

Task-5 immutable proofs remain byte-identical:

- `src/generated/synth_solid.cpp`: `4a88533b90ce71268461f2d6fc2ad71025deb830e403c878b424b7b0ef822363`
- `src/generated/filter_invert.cpp`: `06dd8cf0dacb86fb4ae11ebc822fd8103f648bc98d8272bc526c4507b2d4f1b7`

The native suite also re-verifies all 94 Task-11 external oracle variants and all prior Task 8-10 oracle hashes.

## Verification record

All commands ran without Git, branches, worktrees, commits, pull requests, sibling-tree writes, or new runtime dependencies.

- Final post-review `python3 -m unittest discover -s tests -p 'test_*.py' -v`: 66 tests passed in 346.153 seconds.
- `python3 -m tools.glslcpp.check_corpus --check`: passed; exact pinned corpus.
- `python3 -m tools.glslcpp.check_semantics --check`: passed; 212 bodies.
- Semantic corpus totals remain 622 metadata candidates and 646 variants, locked by the full Python suite.
- `python3 -m tools.glslcpp.generate_kernels --check`: passed; legacy Task-5 output drift-free.
- `python3 -m tools.glslcpp.generate_typed_slice --check`: passed; exact 57-program typed slice.
- Fresh Debug configure/build in `/tmp/noisemaker-cpp-task12-impl-debug`: passed under AppleClang 16.0.0 with `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`.
- Fresh Debug CTest: 1/1 passed; direct executable: 79 passed, 0 failed.
- Fresh Release configure/build in `/tmp/noisemaker-cpp-task12-impl-release`: passed under the same strict warning and FP-contract flags.
- Fresh Release CTest: 1/1 passed; direct executable: 79 passed, 0 failed.
- Independent root Debug verification also passed CTest 1/1 and the direct 79-test executable.

No known acceptance failure remains. Work stops here before any later language frontier.
