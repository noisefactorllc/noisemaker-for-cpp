# Task 9: straight-line scalar/vector math expansion

## Objective

After Task 8 approval, expand the typed native catalog by exactly these 16
additional pinned generated programs (catalog total: 23):

- `filter/celShading:celShadingBlend`
- `filter/chroma:chroma`
- `filter/chrome:chMap`
- `filter/colorReplace:colorReplace`
- `filter/deriv:deriv`
- `filter/lensFlare:lensFlare`
- `filter/mosaicTiles:mosaicTiles`
- `filter/photocopy:pcCombine`
- `filter/relief:rlShade`
- `filter/ridge:ridge`
- `filter/scatter:scatterJitter`
- `filter/simpleAberration:chromaticAberration`
- `filter/text:text`
- `filter/unsharpMask:usmCombine`
- `filter/watercolor:wcComposite`
- `filter/watercolor:wcSeed`

This is a program-factory slice, not a claim that any partial multi-pass effect
is end-to-end supported.

## Hard constraints

- Work only in `.`; never invoke Git,
  branch, worktree, commit, or PR.
- TDD and `apply_patch`; preserve unrelated work and all approved Task 1-8
  artifacts/contracts.
- C++20 + stdlib + zlib runtime only. Generator remains Python-stdlib-only and
  consumes the pinned local corpus plus approved immutable typed IR.
- No raw AST guessing or fallback. No map/string/variant lookup, virtual call,
  `std::function`, or heap allocation in a per-pixel path.
- Preserve double-backed scalar/vector expression evaluation and f32 storage,
  function/builtin, and output boundaries. Keep `-ffp-contract=off`, no
  fast-math, and strict AppleClang/Clang/GNU warnings.
- Do not broaden the two source-specific warning exceptions on the immutable
  Task-5 solid TU.
- Report to `docs/port-engineering/task-9-report.md`, not the repository.

## Capability frontier

Admit only straight-line typed bodies: declarations, assignments, returns,
constructors, swizzles, helper calls, texture/textureSize, and ordinary
scalar/vector math. Do not add blocks/control flow, ternary, loops, globals,
arrays, matrices, derivatives, dynamic indexing, structs, UBOs, out/inout,
varyings, textureLod, or texelFetch in this slice.

Add table-driven typed emitter/runtime support only for overloads actually used
by the 16 programs:

`abs`, `atan`, `clamp`, `cos`, `distance`, `floor`, `fract`, `length`, `max`,
`min`, `mix`, `normalize`, `pow`, `radians`, `sign`, `sin`, `sqrt`, `step`, plus
the already admitted `dot`, `smoothstep`, `texture`, and `textureSize`.

Implement GLSL-compatible scalar/vector overload direction and exact f32
consumption semantics. Expose typed `min`/`max` emission deliberately over the
runtime's component helpers. Every new helper needs focused scalar/vector tests;
include NaN and signed-zero cases where the reference contract distinguishes
them, zero normalization, two-argument `atan(y,x)`, and chained scalar rounding
sentinels.

## Define variants

This slice contains compile-time define variants:

- `filter/lensFlare:lensFlare`: `LENS_TYPE` (4 values)
- `filter/mosaicTiles:mosaicTiles`: `MODE` (2 values)
- `filter/relief:rlShade`: `MODE` (3 values)
- `filter/scatter:scatterJitter`: `MODE` (5 values)

Do not silently compile only the metadata default while presenting the factory
as variant-complete. Either generate all named variants with deterministic
binding-time selection driven by authoritative metadata, or explicitly mark
the generated manifest/factory contract as default-define-only and prevent a
runtime mode parameter from implying unsupported compile-time behavior. Test
every admitted variant through semantic analysis and emission.

## Generator/catalog

- Evolve the typed slice schema deterministically; exact sorted allowlist and
  catalog of 23 unique keys.
- Keep generated output CWD-independent, byte-stable, revision/source-hash
  locked, and free of absolute paths/timestamps.
- Before expansion, repair/verify the typed generator's own path hardening and
  transactional write tests: reject symlink/device/unexpected owned targets,
  invalid/reserved names, and injected failures at each backup/stage swap;
  leave both owned outputs and unrelated generated files byte-identical on any
  failure. Do not replace or validate ownership of immutable Task-5 files as
  though the typed generator owns them.
- Preserve Task-5 files byte-for-byte and Task-8 behavior/hash gates.
- Pixel bodies remain statically typed; factory binding performs all name/type
  lookup once.

## Oracle/parity

Use the pinned `noisemaker-for-cpu` canonical factory for the exact program key
as a read-only implementation-time oracle. Verify its factory source matches
the pinned GLSL before accepting hashes. Bind declared float uniforms through
the explicit f32 boundary; use top-down `Surface.fromRgba8`, nearest bottom-left
sampling, non-square/heterogeneous textures, and nontrivial parameters.

For all 16 keys freeze deterministic small-output F32 and RGBA8 hashes, selected
float-bit probes, dimensions/orientation/alpha expectations, and actual second
render identity. If the JS factory cannot reliably represent the pinned source,
use an independent scalar reference and label it honestly. Record exact oracle
API, inputs, revision, source hashes, and results in the temporary report.

Add negative bind tests for every distinct sampler/uniform signature. External
`textTex` remains a required sampler for `filter/text:text`; no asset loader is
implied.

## Acceptance gates

1. Pinned corpus remains exact and semantic analysis remains 212/212 with all
   622 metadata candidates / 646 pass-variant checks green.
2. Typed generator focused synthetic tests cover every new expression/builtin
   form and fail closed with program/span diagnostics.
3. Typed write/check path has deterministic, CWD, tamper, traversal, reserved
   device, symlink, unexpected-entry, and injected rollback tests.
4. Catalog is exactly 23 sorted factories; no duplicate, adapter, deposit, or
   unrequested key.
5. All 16 native programs compile and match frozen F32/RGBA8 or independent
   references twice; no partial effect is advertised complete.
6. Full Python suites/checkers and native Debug/Release test + CTest gates pass
   under strict warnings.

## Remaining boundary after Task 9

Document exact remaining generated-program count and feature families. The next
slice should add blocks/if/ternary before loops; do not opportunistically cross
that boundary in this task.
