# Task 10: scoped blocks, if/else, and ternary slice

## Outcome

The typed native slice now contains exactly 34 pinned corpus programs and the
public runtime catalog contains exactly 36 unique sorted factories after
retaining the two immutable Task-5 factories. This task added the requested 13
factories and exactly the scoped-block, `if`/`else`, and lazy ternary frontier.
Exactly 178 of the 212 pinned programs remain outside the typed slice.

`filter/highPass:hpCombine` and `filter/plasticWrap:pwSpec` are deliberately
partial factories. They require caller-supplied `blurTex` results from their
unported horizontal/vertical blur stages. This task does not claim either
multi-pass effect is complete.

## Language, semantic, and emitter contracts

- Blocks have lexical scope and retain shadowing. Every `if` arm receives its
  own semantic scope even when the GLSL arm is a single unbraced statement, so
  branch locals cannot leak into a later statement or sibling `else`.
- `if`, nested `else if`, absent `else`, branch returns, short-circuit boolean
  conditions, and scalar/vector ternaries emit from immutable typed IR.
  Ternaries use C++'s lazy `?:`; vector arms materialize at Float32 storage.
- Vector assignments explicitly materialize the right-hand side before
  assignment, preserving the canonical Float32 vector-storage boundary.
- Capability validation and the emitter independently reject unary operators
  other than `+`, `-`, and `!`. Prefix mutation and bitwise complement are
  span-bearing failures rather than implicit frontier expansion.
- Loops, break/continue, arrays, globals, matrices, derivatives, dynamic
  indexing, structs, UBOs, out/inout, varyings, discard, textureLod, and
  texelFetch remain rejected with program/line/column diagnostics.

Reviewer-driven regressions cover unbraced-arm leakage, sibling-else symbol
resolution, outer-variable shadowing, transform matches inside shadowed helper
parameters, unsupported unary mutation, vector assignment materialization, and
framework/local name collision in generated pixel functions.

## Polygon compatibility transform

The schema contains exactly one compatibility transform:

`synth/polygon:shape -> polygon-zero-smoothing-v1`

It matches exactly one `smoothstep(radius, radius - smoothing, d)` in `main`
using stable symbol identities for the `radius` and `smoothing` uniforms and
the intended local `d`. When `smoothing == 0`, it lazily returns `1` for
`d <= radius` and `0` otherwise; nonzero smoothing evaluates the original
smoothstep. Wrong key, reversed edges, altered distance, and same-spelled
shadowed helper parameters all fail closed.

The oracle request supplied `aspect=f32(13/11)`, but the canonical
`createCanonicalBindings` implementation spreads user uniforms and then
unconditionally replaces `aspect` with `f32(width/height)`. The frozen 7x5
oracle therefore uses effective `aspect=f32(7/5)`. Native fixtures bind that
effective value explicitly. A `nonzero -> zero -> nonzero -> zero` sequence
matches both hashes and proves compatibility behavior is deterministic and
order-independent.

## Generator, catalog, and bindings

The schema locks the exact sorted 34-key allowlist, the exact 13 new empty
define maps, the exact capability vocabulary, the exact polygon transform map,
and the existing scatter-only `source-double` literal exception. The generated
manifest records compatibility and numeric-literal contracts without absolute
paths or timestamps. CWD independence, deterministic bytes, ownership
separation, transactional replacement, rollback, path, device, symlink, and
tamper checks remain green.

All 13 distinct new sampler/uniform signatures reject an intentionally wrong
scalar/vector/int/bool alternative at bind time. Dedicated negatives prove the
five secondary samplers are required: high-pass/plastic-wrap `blurTex` and the
three mixer/mask `tex` inputs. Pixel bodies retain typed direct state access and
perform no map/string/variant lookup or heap allocation.

| Generated artifact | SHA-256 |
| --- | --- |
| `src/typed_generated/typed_slice.cpp` | `c44f27040475c1804aef7d6799b2bfd62166c27ea618c0a0e76be896bfff40b3` |
| `src/typed_generated/typed_manifest.json` | `23f40575e118d13b6da1ddb2731e692952cbc83a4be8e34f324fa492bf4f963c` |
| Task-5 `src/generated/synth_solid.cpp` | `4a88533b90ce71268461f2d6fc2ad71025deb830e403c878b424b7b0ef822363` |
| Task-5 `src/generated/filter_invert.cpp` | `06dd8cf0dacb86fb4ae11ebc822fd8103f648bc98d8272bc526c4507b2d4f1b7` |

## External oracle provenance and setup

Oracle revision: `a024dc3a960cc44af454abc7aebce50456c194e6`.
Implementation-time oracle: Node v24.7.0 in the read-only
`../noisemaker-for-cpu` repository, importing
`canonicalKernelFactories`, `bindCanonicalKernel`, `runPass`, and `Surface`.
Every raw GLSL source hash was checked against the pinned manifest before
rendering; canonical factory function-source hashes were independently frozen.
No Node/oracle process is part of the native build or test run.

Primary outputs are top-down 7x5 `Surface` images using nearest bottom-left
sampling, `time=f32(.125)`, and `seed=f32(7)`. Regular inputs are heterogeneous:
`inputTex=5x3/tag1`, `blurTex=3x5/tag11`, and `tex=7x2/tag23`, with RGBA bytes
`(31x+17y+13t, 11x+47y+29t, 67x+19y+7t,
(255-23x-37y-5t)&255)`. Glowing edge instead uses a low-contrast 6x4 surface
`(45+7x+11y, 73+5x+9y, 22+3x+13y, 255-4x-7y)`. Primary tile/full dimensions
are `(3,-2)/(17,13)`; polygon uses `(3,3)/(13,11)` and effective aspect 7/5.

Tests freeze exact little-endian Float32 SHA-256, RGBA8 SHA-256, and full RGBA
float-bit probes at top-down pixels 0, 17, and 34. Every primary and alternate
fixture renders twice with byte-identical Float32 and RGBA8 output.

| Key | Raw GLSL SHA-256 | Canonical factory SHA-256 | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- |
| `filter/channel:channel` | `b237868c688bcfe51deb56155b0fbfe66a3fcf0db5cba93177ec2198ae48e9e7` | `2dfcf137da0cb5c4206569dacae3a640353d77cd0bf872d219b7cc9f8023755a` | `757bbae80510cd028b6a64b02c19959d9c058b2b64dfc7273870e9fe219e6ebd` | `c584bb267993197294a6fbdf101348d51797a91acac9eec19c5ebd23f5e47bde` |
| `filter/chromaticAberration:chromaticAberration` | `bd8fafacdad36703c280204fb007cb6e260ecb4455fcb754a756ae04d51562b6` | `a97890ce4e3b3860ac872d087f077af63933371bf3fdf0ad452883e70eed85db` | `4ca788af3c142403813627704f6e68c9e961989a11323e2a10ec3bea01206125` | `e25e1fa9f910c3cd439d465ce68a50f000eafaa4ed5d708ed399f0b1a2cea61e` |
| `filter/glowingEdge:glowingEdge` | `e5df47ffdea81d4f7403d4a3133acd42f2955da8870fd62e6052c2dbeef1d3fd` | `032d17e131094ab655a9aebee933a7332ede21fc3c54d4b957f78d37f9509577` | `d4ecd1b91848d86890b86d7611ebaeee5c753d388c9fe7a5e8212f193a313163` | `8fd25b2c5bb1124cb6d1348c74355432625bd247128027ae4c7a7f6b3ce55c87` |
| `filter/highPass:hpCombine` | `1dc649d0010cee700cdd56b0e35f4867bbadee7426cb04cad49a126ad1e95284` | `0f3bfb98a5659e4b22fc7fa0fbd8b8dc047e8acdaad83850afcfa9e88c1a3d49` | `b7d5dab26de4a4fe50a8cdc6439c52133a733625b9651abf31a4dc28bd37e40e` | `37f0995e070ba207c0aac4722cabb5c78617281f23562193509956649577990d` |
| `filter/pixels:pixels` | `06919a5f0cb829fdae9c04ae878aa4d7a12072e176ce3c98fb1ccf2623661e6e` | `b4be78577287d8c88601f53047392841bb8604675125c78da877590ad84a5578` | `feb89b0e6a128d533471c06cac88fe82d78874442cfbd509204de736ad6bbc0d` | `59adf71406e87307e5f915828cfce8b52ec0bb667bd62c853dc7181f413c9641` |
| `filter/plasticWrap:pwSpec` | `a26cbadc9c0aec753494f3e2a95964f35358eb8bf283107c2d7c624055c87767` | `ca13c0983ee0bca8709089f31dac3bb1d9538f229997b6b4ea41b8938823566b` | `f39c59c7f4aa4ba745d0d653b2b24d7bd77b4c5cfd9a74771fd45fd0e23eab3c` | `9d1599d1124a34c34d246cf95de8de038e299917769d139057cd453d05449d3a` |
| `filter/seamless:seamless` | `d54569f8e394430d771ecb51edc9258ecde17483674843fab8a9f6efb733dabf` | `ce4a4a603a3e851530a66bd989a891a7a7e1ef2f3090d64074e4d5b68a7b027f` | `95627615549b377e800f657471499a978d7c445c1a35cfc9ac9915e4bdf73bf0` | `90255d926242b26be8853e926acca831507d557afe72a00016c9e134a772dea2` |
| `filter/sine:sine` | `569f2d820d99a6d9ac2b310b6fd646cd961c70a6d9eec2bcfd5d8f3686553f07` | `72a884808cf7666b2d6f7729c7252e254ee2cef7dc3603283fd5c82f623a9068` | `73b6f26c811b0a8676d475bd8eed36917f3ab0d914f87da8f50da49a0d197014` | `6f09375716db998f9df1655f106383dde3444800b8e1242a5390f01be0b916d9` |
| `filter/vignette:vignette` | `0b7f632bb4c11cd61ff340ab9ef4ca82186a848ea70fe24e69aad5a0dfb63b6d` | `5aaa7b67c2935e4826a96938ae014eb9622eb11f39e5e302439fc391850962f1` | `94a2b6f3415386e718d1d3ba3922cb4126241a5797e426b2159e07385e042e75` | `03f0b8e7644def6fbf6fa486b93646041c870baff6684fb98ff8171f3d56dab7` |
| `mixer/alphaMask:alphaMask` | `10185fc4c654577df38082e8fe16e577c5f096ce7574c6819e15243cbf58ca7d` | `84d5062874acd64b108dcf99d004b42adaa6a08924ced798451560778e69e9a9` | `7d32bb110d9181320c62787b1014acc5dc4b163ce451503889fb796ca4852661` | `bf47b573aca6724cdbcc77923827a042542265ed995f492904a4f3887923f92b` |
| `mixer/applyMode:applyMode` | `636174ce4937e5e3da07b757117caf98c760c70ff85e1eb822049fafe2c45670` | `d02430bb6f959993c2bfa7acd70be74a578fba8dca0941f2c2b5743c1b19cd20` | `7aeee2945e2264b2706af1000de073f87afa3de89fb58b74d7d45c5e489fc462` | `901503d50bab78d19f2bdd7f32efd5a6166653885a965813a1a12b735c9517e5` |
| `mixer/thresholdMix:thresholdMix` | `66a51769ab16f2b2575101d5c347860a19fc0a7618af6dd7d06c561af22d1a87` | `0c07954725dfaec82028e2d40f82d131a22663763630fbaaa700d48a5c96accd` | `f6e338ca581f3243524f124f3db407c3e0a56c42d9563eaba6901f48eb373712` | `9499f26e19394e0bd91fad082d820362851877598640cfbdf87f9719ffa62b7e` |
| `synth/polygon:shape` nonzero | `e43087ee8ade2e59ff1a2098c1e6ceb4357a3eb9ee63755a3f8a3879824115e6e` | `794ce8c54414a89bd6d9b1b3083131a042bd7a8ebb7d191eaef93f4e1459bdb1` | `17c3ee338cf903cacfcf422df124a54bc7d9b8497339fca260fe3b8e435b011f` | `22dc2377820085ffdead0646a681390f2285f1dc2de1fba0283145cec687a69c` |
| `synth/polygon:shape` zero | same | same | `1d15ee530fda3a6edcc2234b7c796461eab1b0156cba3916adec7e610313f850` | `3968f2377d75bb572eebc82b4640e94594775758817197a5dae711f8426fb885` |

## Branch coverage and NaN parity

An additional 23 exact external variants cover all fixed runtime branch arms:
channel 0/1/3; chromatic fallback resolution; glowing metrics 0/1/2;
high-pass mono; pixels early return; both plastic-wrap fallback conditions;
seamless linear/sharp/zero-width; sine luminance; vignette fallback dimensions;
alpha-mask early-return/negative amount; apply brightness-negative/saturation;
threshold luminance hard/soft; and polygon non-triangle/zero-alpha. Their exact
bindings, Float32/RGBA8 hashes, and probes are frozen in the native tests; the
read-only oracle dataset was independently validated as
`/tmp/noisemaker-task10-branch-oracles.json` SHA-256
`c4e5a21b7f15ccb5fd56709f220ee5b25ebc639b8aba9fee5733e2edbbda81b9`.

The chromatic false-arm case exposes an intentional source quirk: `uv` divides
by zero before the later fallback ternary. Canonical nearest sampling indexes a
typed array with NaN and produces quiet-NaN RGBA. Native nearest sampling had
previously clamped NaN to texel zero; a focused RED/green sampler regression now
returns quiet-NaN RGBA when either coordinate is NaN, matching canonical F32
and RGBA8 hashes exactly without changing finite or infinite clamping.

## Final verification

- Full Python suites: 54/54 passed; the focused semantic/typed subset passed
  38 tests and 270 subtests.
- `check_corpus.py --check`: `check_corpus: ok`.
- `check_semantics.py --check`: `bodies ok (212 programs)`; metadata coverage
  remains 622 candidates / 646 variants.
- `generate_kernels.py --check`: passed; Task-5 generated hashes unchanged.
- `generate_typed_slice.py --check`: `typed slice ok (34 programs)`.
- Debug strict-warning build: passed; native tests 71/71; CTest 1/1.
- Release strict-warning build: passed; native tests 71/71; CTest 1/1.

All work stayed in `.`; no Git,
branch, worktree, commit, or pull-request operation was used.
