# Task 13 implementation brief: exact level-zero `texelFetch` slice

Date: 2026-08-10  
Repository: `.`  
Pinned corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`

## Outcome

After Task 12 is independently approved, add exactly eight new typed CPU factories whose only current language frontier is integer-coordinate `texelFetch`. Grow the typed slice from 57 to exactly 65 sorted programs and the public catalog from 59 to exactly 67 sorted unique factories. The immutable legacy `filter/invert:inv` and `synth/solid:solid` entries remain outside typed generation. Exactly 145 of 212 corpus programs must remain without a native public factory.

No Git, branches, worktrees, commits, pull requests, sibling-tree writes, new runtime dependencies, placeholder kernels, hand-translated shader bodies, render-graph adapters, or per-pixel map/string/variant/allocation/dynamic dispatch are allowed.

## Exact allowlist

Every authoritative default define map is exactly `{}`:

1. `filter/bloom:brightPass`
2. `filter/bloom:composite`
3. `filter/fibers:fibersBlend`
4. `filter/normalize:apply`
5. `filter/pixelSort:luminance`
6. `filter/reindex:nmReindexApply`
7. `filter/scratches:scratchesBlend`
8. `filter/strayHair:strayHairBlend`

## Language/runtime contract

- Add exactly one schema-locked capability for `texelFetch` and map only the typed call `texelFetch(sampler2D, ivec2, int-literal-zero) -> vec4`.
- The third argument must be the source literal `0`. Reject nonzero literals, uniforms, variables, arithmetic expressions, other sampler classes, floating coordinates, non-`ivec2` coordinates, wrong arity, `textureLod`, and every unrelated builtin expansion.
- Emit a dedicated typed helper that calls the existing `texel_fetch_bottom_left(surface, x, y)` and materializes its four stored Float32 lanes as `glsl::Vec4`. Preserve bottom-left shader integer coordinates, top-down `Surface` storage conversion, integer edge clamping, alpha, and exact stored bits. Do not substitute normalized `texture()` sampling.
- Preserve signed `ivec2` values end to end. `filter/strayHair:strayHairBlend` declares integer `tileOffset` and `fullResolution` plus float `renderScale`; do not coerce them to the ordinary float system-uniform types. Although those three bindings are unused by the authored body, the public binder must retain the exact declared signature and reject missing or wrong-typed values.
- Keep all Task 12 compatibility transforms and numeric boundaries unchanged. Do not admit loops, arrays/indexing, globals, matrices beyond the existing `mat2`, structs, UBOs, varyings, derivatives, parameter directions, `textureLod`, nonzero mip levels, or adjacent texel-fetch programs.

## RED/GREEN verification

1. Add runtime/helper tests for exact `(0,0)` bottom-left row selection, opposite corner, negative and oversized integer clamping, alpha, heterogeneous Float32 lanes, and repeatability. Negative coordinates are a runtime-helper contract; the eight admitted shader bodies cannot produce them and the source-level oracle must not claim otherwise.
2. Add typed validator/emitter tests for exact helper spelling and result type. Reject every malformed arity/type, nonzero or nonliteral mip, `textureLod`, floating coordinates, other sampler types, loops, and indexing with located diagnostics.
3. Schema tests must lock exactly 65 sorted typed keys, exact `{}` defines for all eight additions, the exact capability vocabulary, and no new compatibility/numeric-literal exceptions.
4. Add all eight public binder declarations plus a compile/use address guard. Catalog tests must prove exactly 67 sorted unique public keys and exactly 145 corpus keys without a public factory.
5. For every distinct uniform/sampler signature, fail closed on every required sampler/uniform being absent and on representative wrong types. Lock all declared sampler routes exactly as authored: `inputTex`, `bloomTex`, `overlayTex`, and `statsTex`.
6. Freeze and embed every one of the 21 accepted external-oracle cases. Require exact little-endian Float32 SHA-256, RGBA8 SHA-256, 12 float-bit probes, dimensions/orientation, alpha, and a byte-identical second render.

## Accepted oracle

Artifact: `docs/port-engineering/task-13-oracles.json`  
SHA-256: `7d98bc24101b967a13156a544484786b3255ca2e07bd4f55d47f0bc62973b829`  
Report: `docs/port-engineering/task-13-oracle-report.md`

The controller independently verified the live artifact hash, pinned revision `a024dc3a960cc44af454abc7aebce50456c194e6`, Node v24.7.0, exact eight-source set, exact 21 unique key/variant rows, raw-source and UTF-8 `Function.prototype.toString()` factory hashes, and double-render identity. Case counts are 3 brightPass, 2 composite, 3 fibersBlend, 2 normalize apply, 2 pixelSort luminance, 3 reindex apply, 3 scratchesBlend, and 3 strayHairBlend.

## Effect-graph truth

These factories are individually executable only when callers provide metadata-declared intermediate surfaces. Do not claim complete multi-pass effects and do not add adapters or a render graph.

- Bloom brightPass is pass 1 of 3; composite is pass 3 and needs caller-supplied `bloomTex`. The middle gather pass remains unported.
- Normalize apply is pass 4 and needs caller-supplied 1x1 `statsTex`; its producers remain unported.
- PixelSort luminance is only its luminance pass; the remaining pipeline is unported.
- Reindex apply is pass 3 and needs caller-supplied 1x1 `statsTex` plus `uDisplacement`; its producers remain unported.
- Fibers, scratches, and strayHair blend are individually executable blend passes needing caller-supplied `inputTex`, `overlayTex`, and `alpha`.

Exclude `filter/pixelSort:computeRank` and `filter/pixelSort:gatherSorted`: after `texelFetch`, both immediately require the later counted-loop frontier.

## Full acceptance and report

- Run the complete Python suite plus corpus, semantics, legacy generator, and typed generator drift checks. Preserve 212 bodies / 622 metadata candidates / 646 variants.
- Configure and build fresh strict-warning Debug and Release trees; run the direct native executable and CTest in each.
- Preserve exact Task 5 hashes, Task 11's 94 cases, and Task 12's 120 cases.
- Write `docs/port-engineering/task-13-report.md` with scope/counts, typed/runtime fail-closed contracts, effect-graph truth, oracle provenance, generated hashes, exact test counts, and exactly 145 remaining public-unported corpus programs.
- Stop for independent review before starting Task 14 repository changes.
