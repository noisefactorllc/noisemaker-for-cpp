# Task 17 frozen scope/proof/oracle review

## Decision

**NOT APPROVED — P2 provenance-lock gap.**

The proposed two-key capability is otherwise a suitably narrow next step: the
source profiles, count arithmetic, scalar/vector storage rules, exclusions,
oracle fixtures, and Debug/Release stack-evidence requirement are coherent.
However, the frozen brief explicitly requires an exact empty define map and
validator/emitter rejection of wrong defines.  The current parser and typed IR
cannot carry that fact to either recomputation boundary, so the specified
emitter-side lock is not implementable as written without adding provenance.

## P2 — exact define-map (and independent raw-source) provenance is absent from TypedProgram

`parse_program(source, key, runtime_defines)` normalizes/preprocesses the
source but returns no define metadata.  `TypedProgram` stores normalized
`source` only; its fields are

```text
key, source, declarations, functions, resources, body_status,
local_type_names, structs, uniform_blocks, interface_symbols,
builtin_symbols, counted_loop_proof
```

Consequently, an emitter that receives a `TypedProgram` and a caller-supplied
raw hash cannot independently prove the input define map was exactly `{}`.
This is observable now, before Task 17 implementation:

```text
parse(sharpen, {})                 -> normalized SHA 1a252d3d...5ec5abb0
parse(sharpen, {"UNRELATED": 1}) -> normalized SHA 1a252d3d...5ec5abb0
same normalized source: True
parser result has define metadata: False
```

The harmless extra define does not change this source's preprocessed body,
which is precisely why a normalized-source hash cannot distinguish it.  A
define that affects `#ifdef GL_ES` does change the normalized digest and would
be rejected, but the frozen contract says **every** map must be exact and
requires wrong-define negatives.  The same representation also leaves the
emitter unable to re-hash the actual raw source; it can only compare the
caller-supplied `source_hash` parameter with the expected constant.

### Required correction before implementation

Extend parser-to-typed provenance with the original raw source and a canonical,
immutable representation of the runtime define map (for example, sorted
`(name, value)` tuples).  Validator and emitter must each independently:

1. hash that retained raw source and compare it to the key-specific raw hash;
2. hash the retained normalized source and compare it to the key-specific
   normalized hash; and
3. require the retained define map to be exactly empty for both Task 17 keys.

Keep the existing generator-level manifest/default check as a separate gate;
it is not a substitute for the typed-IR/emitter boundary.  Add both-boundary
tests that parse the canonical raw source with `{"UNRELATED": 1}` (same
normalized bytes) and with `{"GL_ES": 1}` (different normalized bytes), and
assert rejection.  Include a forged provenance-record mutation test alongside
the required tree/proof tamper tests.

## Verified design evidence outside the P2

- **Scope/counts:** current slice is 108 typed programs and the generated
  public catalog is 110; the pinned manifest has 212.  Adding only Sharpen and
  Sobel yields exactly 110 typed / 112 public / 100 public-unported.  Neither
  proposed key is currently in the typed allowlist.
- **Pinned sources and defines:** direct parse/semantic analysis with `{}`
  reproduced the frozen raw/normalized hashes:
  Sharpen `c9a9b196...27773e7` / `1a252d3d...5ec5abb0`, Sobel
  `ef459738...a2e52f84` / `d8aad0d...fc0cbf0c`.  Metadata defaults for both
  keys are `{}`.
- **Proof feasibility/narrowness:** the typed bodies expose exactly the
  proposed local arrays and store/read pattern.  Sharpen has `kernel:float[9]`
  and `offsets:vec2[9]`; Sobel has `sobel_x:float[9]`, `sobel_y:float[9]`, and
  `offsets:vec2[9]`.  Every store is a direct literal index 0–8 before one
  depth-one `i=0; i<9; i++` loop; the only reads are the specified arrays with
  direct induction `i`.  This supports a source-specific proof without
  admitting generic arrays/indexing.
- **Lowering/precision:** `std::array<double, 9>{}` is correct for the
  canonical Number scalar tables; `std::array<glsl::Vec2, 9>{}` preserves the
  Float32 vector-lane boundary and zero fill.  `operator[]` is `noexcept`; the
  design correctly forbids `.at()` in pixel code.  Raw table payload arithmetic
  is 144 bytes (72-byte scalar + 72-byte vector) for Sharpen and 216 bytes
  (two scalar + vector) for Sobel; the brief correctly requires compiler/frame
  evidence separately in fresh Debug and Release builds rather than claiming
  this is a full stack-frame measurement.
- **Exclusions:** the listed cel-shading/outline dynamic nested-loop users,
  refract array-parameter ABI, and sacred-geometry 13-element/nested profile
  are structurally outside the fixed nine-local-literal/read contract.
- **Bindings:** source declarations and frozen signatures agree.  Sharpen has
  `tileOffset`, `fullResolution`, `inputTex`, `amount`, `renderScale`; Sobel
  adds `alpha`.  The design correctly keeps tile/full resolution as required
  runtime bindings rather than defaults.
- **Oracle truth/adequacy:** `node task-17-oracle-generator.mjs --check`
  returned `ok task-17-oracles.json`.  The generator invokes pinned canonical
  factories through `bindCanonicalKernel`, `runPass`, and `Surface`, records
  source/factory provenance, and byte-compares regenerated JSON.  Its
  non-square F32 input, nonzero tile offset/full resolution, three probes,
  repeat renders, default/non-default exact-F32 amount, and Sobel alpha 0/1
  cover orientation, all nine direct reads, precision, saturation-hidden F32
  behavior, and repeatability.  The `2.3` value is correctly frozen as
  `Math.fround(2.3)` / `0x40133333`.

## Frozen artifact hashes

- Risk audit: `17692e3784ad64a4a283f7509b8cabe65521cabe282d5a78d6e6ade17be24937`
- Brief: `9bb81596fe92aea0911712ed5404b1475a6ebf6ecb81a5e516274a6d4b22c53b`
- Oracle report: `4f7848798975d6025a138cbb9eb77080987a64188e3867dc7f90bc13d1bdec95`
- Oracle generator: `ab607be447bf86457267e8b76298e24961065407db54039c206d21a6b85dfb9e`
- Oracle JSON: `6a68386e0244a2c5ec0b183e4e5e4e3e59f01c30414f8854a041d871637c907a`

## Scope

This was read-only for the repository.  No Git command or repository write was
performed; this `/tmp` review document is the only file written.
