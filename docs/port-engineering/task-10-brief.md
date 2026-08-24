# Task 10: scoped blocks, if/else, and ternary slice

## Objective

After independent Task-9 approval, add the first structured-control-flow
frontier and exactly these 13 pinned generated program factories:

- `filter/channel:channel`
- `filter/chromaticAberration:chromaticAberration`
- `filter/glowingEdge:glowingEdge`
- `filter/highPass:hpCombine`
- `filter/pixels:pixels`
- `filter/plasticWrap:pwSpec`
- `filter/seamless:seamless`
- `filter/sine:sine`
- `filter/vignette:vignette`
- `mixer/alphaMask:alphaMask`
- `mixer/applyMode:applyMode`
- `mixer/thresholdMix:thresholdMix`
- `synth/polygon:shape`

The typed slice becomes exactly 34 programs and the public catalog exactly 36
sorted factories after retaining the two immutable Task-5 factories. This is a
program-factory slice, not a claim that partial multi-pass effects are complete.

## Hard constraints

- Work only in `.`; never invoke Git,
  branch, worktree, commit, or PR.
- TDD and `apply_patch`; preserve unrelated work and all approved Task 1-9
  artifacts and exact external parity gates.
- C++20 + stdlib + zlib runtime only. Generator remains Python-stdlib-only and
  consumes the pinned corpus plus immutable typed IR.
- No raw AST guessing or generic fallback. No map/string/variant lookup,
  virtual call, `std::function`, or heap allocation in a per-pixel path.
- Keep `-ffp-contract=off`, no fast-math, strict AppleClang/Clang/GNU warnings,
  and the established JS-double / Float32 storage-consumption contracts.
- Do not broaden Task-5 warning exceptions or change Task-5 files.
- Report to `docs/port-engineering/task-10-report.md`, never the repo.

## Exact language frontier

Admit only:

- lexical blocks with C++-equivalent scope and shadowing;
- `if`, `if/else`, and nested `else if` represented by the immutable typed
  statement tree;
- lazy scalar-bool ternary expressions with exactly one selected arm evaluated;
- existing declarations, assignments, returns, constructors, swizzles, helper
  calls, texture/textureSize, and Task-9 scalar/vector math.

Do not admit loops, break/continue, arrays, globals, matrices, derivatives,
dynamic indexing, structs, UBOs, out/inout, varyings, discard, textureLod,
texelFetch, or new builtin families. Capability validation must be fail-closed
and span-bearing for every excluded statement/expression form.

Emitter tests must cover nested blocks and shadowing, braced and single-statement
branches, an absent `else`, nested else-if, return inside a branch, short-circuit
boolean conditions, lazy ternary arms, scalar-double ternary preservation, and
vector ternary storage. Generated C++ must not hoist branch-local declarations
or evaluate both ternary arms.

## Program and compatibility contracts

- All 13 programs have authoritative `defines = {}`. Schema-lock that fact.
- The existing Task-9 scatter `source-double` literal exception and structural
  hash fences must remain exact and unchanged.
- The pinned JS compiler applies one source-specific semantic repair to
  `synth/polygon:shape`: `smoothstep(radius, radius - smoothing, d)` becomes a
  zero-smoothing-safe conditional, returning `1` when `d <= radius` and `0`
  otherwise when `smoothing == 0`, and using smoothstep otherwise. Reproduce
  this as an explicit, schema-locked typed compatibility transform; do not
  patch generated C++ by source text or advertise a generic smoothstep change.
  Add positive zero/nonzero tests and negative structural-near-miss tests.

No new builtins are expected. The union required by this slice is already
admitted: `abs`, `atan`, `clamp`, `cos`, `dot`, `floor`, `fract`, `length`,
`max`, `min`, `mix`, `normalize`, `pow`, `sin`, `smoothstep`, `sqrt`, `step`,
`texture`, and `textureSize`.

## Partial-pass truth

Eleven selected factories are single-pass. These two are deliberately partial
and must be labeled as such in the report and any public capability metadata:

- `filter/highPass:hpCombine` requires `blurTex` produced by `hpBlurH` then
  `hpBlurV`.
- `filter/plasticWrap:pwSpec` requires `blurTex` produced by `pwBlurH` then
  `pwBlurV`.

Do not add their missing graph stages in this task.

## Generator, catalog, and binding gates

- Evolve the typed schema deterministically with an exact sorted 34-key
  allowlist, exact capability vocabulary, exact compatibility-transform map,
  and an exact 36-key unique sorted catalog.
- Preserve CWD independence, byte stability, revision/source hashes, no
  timestamps/absolute paths, transactional whole-directory writes, ownership
  separation, rollback/path/device/symlink/tamper hardening, and Task-5 hashes.
- Binding remains a one-time factory operation. Pixel bodies remain typed and
  allocation-free.
- Add negative binding coverage for every new distinct sampler/uniform factory
  signature. In particular, prove required secondary samplers (`blurTex`, mask
  or mixer textures) fail at bind time and wrong scalar/vector/int alternatives
  fail without entering a pixel.

## Oracle/parity

Use pinned `noisemaker-for-cpu` canonical factories read-only. Verify the exact
factory source and pinned GLSL SHA before accepting each fixture. Use top-down
`Surface.fromRgba8`, nearest bottom-left sampling, heterogeneous non-square
textures, nontrivial f32/int parameters, tile offsets, and dimensions chosen to
exercise both sides of every admitted runtime branch across the output.

For all 13 keys freeze deterministic small-output F32 and RGBA8 hashes,
selected float-bit probes, dimensions/orientation/alpha expectations, and
actual second-render identity. For ternary programs, ensure both arms occur in
the fixture. For polygon, freeze separate `smoothing == 0` and nonzero cases so
the compatibility transform is observable. Record exact Node API, inputs,
revision, source hashes, branch coverage, and results in the temporary report.

## Acceptance gates

1. Corpus and semantic checks remain 212 bodies / 622 metadata candidates /
   646 variants.
2. Focused typed tests prove every new control-flow form and fail closed on all
   still-excluded forms with program/span diagnostics.
3. Generator transaction, ownership, determinism, and path-hardening gates stay
   green.
4. Typed allowlist is exactly 34 and catalog exactly 36 sorted unique factories.
5. All 13 factories match frozen external F32/RGBA8 references twice; polygon
   also matches its separate zero-smoothing reference.
6. Task-5 files and all Task-8/9 external hashes remain unchanged.
7. Full Python suites/checkers and native Debug/Release tests plus CTest pass
   under strict warnings.

## Remaining boundary after Task 10

Exactly 178 of 212 pinned generated programs remain outside the typed slice.
The next control-flow-only batch may take the ten deferred branch-heavy
candidates, but loops/arrays/indexing remain a separate later frontier.
