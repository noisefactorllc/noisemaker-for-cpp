# Task 14 canonical global-constant oracle report

Artifact: `task-14-oracles.json`  
Artifact SHA-256: `3d77b3d357e697d41fdb6842f78dbc403afa3f317f3c76708e94923b2b52a104`  
Pinned corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`  
Canonical runtime: Node `v24.7.0`

The campaign rendered **30 variants** twice each; every second Float32 byte
buffer and RGBA8 byte buffer was byte-identical to its first render.  The
artifact records top-down 9x7 dimensions, exact little-endian Float32 and
RGBA8 SHA-256 values, twelve Float32 bit probes per case, source hashes, and
SHA-256 of exact UTF-8 `Function.prototype.toString()` factory bytes.

| Key | Cases | Unique F32 | Const declarations / initializer form |
|---|---:|---:|---|
| `filter/pixelSort:prepare` | 4 | 4 | `const float PI = literal` |
| `filter/pixelSort:finalize` | 4 | 4 | `const float PI = literal` |
| `filter/skew:skew` | 4 | 4 | `const float PI = literal` |
| `filter/tetraCosine:tetraCosine` | 5 | 5 | `const float TAU = literal` |
| `filter/tile:tile` | 5 | 5 | `const float PI = literal`; `const float TAU = literal` |
| `synth/osc2d:osc2d` | 8 | 8 | `const float PI = literal`; `const float TAU = literal` |

All six authoritative metadata default-define maps are exactly `{}`. Each raw
source SHA was independently compared with the pinned manifest before this
artifact was accepted.

Coverage is intentionally heterogeneous: asymmetric formula RGBA8 surfaces
are stored top-down while shader sampling uses bottom-left coordinates. Pixel
sort locks prepare/finalize separately, all mirror/repeat/clamp and non-enum
fallback paths, both `darkest` values, alpha endpoints/interior, signed angles,
and distinct `inputTex`/`originalTex` routing. Skew covers its three wrap arms,
fallback, signed rotation, negative tile coordinates, and oversized-skew
clamping. TetraCosine covers RGB/HSV/OkLab/OKLCH/fallback, all animation
rotation states/fallback, and alpha 0/interior/1. Tile covers every symmetry,
both aspect booleans, and fallback symmetry. Osc2d covers types 0 through 6,
the final-else fallback, time/speed/seed variation, signed rotation/coordinates,
and its `fullResolution < 1` fallback.

Alpha expectations are recorded per variant: pixel-sort finalize uses
`originalTex` alpha, prepare/skew/tetra retain the sampled input alpha, tile
forces alpha one, and osc2d emits opaque grayscale.

No repository, corpus, or oracle inputs were changed; only the requested Task
14 JSON artifact and this report were written.
