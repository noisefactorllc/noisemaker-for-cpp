# Task 13 canonical texelFetch oracle report

Artifact: `docs/port-engineering/task-13-oracles.json`  
SHA-256: `7d98bc24101b967a13156a544484786b3255ca2e07bd4f55d47f0bc62973b829`  
Revision: `a024dc3a960cc44af454abc7aebce50456c194e6`  
Node: `v24.7.0`

All 21 cases were rendered twice byte-identically. Each stores exact raw corpus and UTF-8 Function.prototype.toString factory hashes, F32/RGBA8 hashes, and 12 Float32 bit probes.

| Key | Cases | Unique F32 |
| --- | ---: | ---: |
| filter/bloom:brightPass | 3 | 3 |
| filter/bloom:composite | 2 | 2 |
| filter/fibers:fibersBlend | 3 | 3 |
| filter/scratches:scratchesBlend | 3 | 3 |
| filter/normalize:apply | 2 | 2 |
| filter/pixelSort:luminance | 2 | 2 |
| filter/reindex:nmReindexApply | 3 | 3 |
| filter/strayHair:strayHairBlend | 3 | 2 |

Fixtures are heterogeneous top-down integer-addressable textures, with 1x1 range/flat stats intermediates. They lock bottom-left rows, high-coordinate edge clamping, alpha, tile/full-resolution option propagation, renderScale binding, and every declared sampler/uniform route. Negative integer fetch positions are unreachable in these eight source programs and are explicitly excluded from this source-level oracle.
