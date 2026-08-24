# Task 12 implementation brief: GLSL `mod` slice

Date: 2026-08-10  
Repository: `.`  
Pinned corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`

## Outcome

Add exactly thirteen new typed CPU factories whose only current language
frontier is the GLSL floating `mod` builtin. The typed slice must grow from 44
to exactly 57 sorted programs. The public catalog must grow from 46 to exactly
59 sorted unique factories because the immutable Task-5 implementations of
`filter/invert:inv` and `synth/solid:solid` already occupy their public keys and
must not be duplicated or regenerated. Exactly 153 of the 212 corpus programs
must then remain without a native public factory.

No Git, branches, worktrees, commits, pull requests, sibling-tree writes, new
runtime dependencies, placeholder kernels, hand-translated shader bodies, or
per-pixel map/string/variant/allocation/dynamic dispatch are allowed.

## Exact new allowlist

Every authoritative default define map is exactly `{}`:

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

## Language/runtime contract

- Add exactly one schema-locked capability, `mod`, and map only the typed
  builtin `mod` to `glsl::mod`.
- Preserve GLSL semantics `x - y * floor(x / y)`. Do not use `%` or
  `std::fmod`. Retain the existing scalar double path through
  `noisemaker::glsl_mod` so scalar arguments are not prematurely narrowed.
- Admit exactly `mod(float, float)`, `mod(vec2, float)`, and
  `mod(vec2, vec2)`, plus the emitted `FloatExpr<2>` left-operand equivalents
  of the latter two. Do not admit `mod(float, vec2)`, vec3/vec4 forms, or any
  other overload family. Consume stored vec2 lanes as Float32 and store each
  result with `f32`, following the established `map_float`/`map_float2`
  boundary.
- Do not widen integer `%`, array/index support, loops, globals, matrices,
  structs, UBOs, varyings, parameter directions, derivatives, textureLod,
  texelFetch, discard, or unrelated builtins/operators.
- Keep the Task-11 general literal folding, helper-backed vector operand
  materialization, corrupt alias transform, polygon transform, and all prior
  numeric/source-double contracts unchanged.

## RED/GREEN verification requirements

1. Add focused runtime vectors for negative operands, non-integer divisors,
   scalar mod, vec2/vec2 and vec2/scalar forms,
   signed zero/nonfinite cases matching the canonical JS oracle, the mirror
   idiom `abs(mod(v + 1.0, 2.0) - 1.0)`, and per-lane Float32 storage.
2. Add focused typed-emitter tests for exact `glsl::mod(...)` spelling and
   type/arity failures. Capability and emitter negatives must continue to
   reject at least `ceil`, `reflect`, `any`, `floatBitsToUint`, derivatives,
   texelFetch, and malformed mod calls with located diagnostics.
3. Schema tests must lock exactly 57 sorted typed keys, exact `{}` defines for
   all thirteen additions, exact capability vocabulary, and no new
   compatibility or numeric-literal exceptions.
4. Add all thirteen public binder declarations and a native compile/use guard
   that takes each address. Catalog tests must prove exactly 59 sorted unique
   keys and no duplicate legacy solid/invert entries.
5. Every distinct uniform/sampler signature must fail closed for a missing or
   wrong-typed value. Every required `inputTex`/`tex` sampler must be tested.
6. Freeze exact external-oracle fixtures only after the controller records the
   final oracle artifact SHA below. For every variant require exact
   little-endian Float32 SHA-256, exact RGBA8 SHA-256, dimensions/orientation,
   exact float-bit probes, alpha expectations, and byte-identical second
   render. Diagnose mismatches at the first bit and add a focused RED
   regression before semantic changes.

## Oracle acceptance record

The oracle worker must write only
`docs/port-engineering/task-12-oracles.json`, using pinned Node v24.7.0
and the read-only `noisemaker-for-cpu` canonical factory/runtime. The artifact
must record schema/revision/API, exact raw-source hashes, exact UTF-8
`Function.prototype.toString()` factory-hash contract, deterministic fixture
IDs and bytes/formulas, bindings, dimensions, F32/RGBA hashes, probes, and
known authored equivalences. Every variant must be rendered twice identically.

Final accepted oracle SHA-256:
`b0697f49f09ae3565c6e4505e2a09e3ac5e08714e04fab5492c9d5665999cc9a`

The controller independently verified that live artifact hash, exact 13-source
set, exact 120 unique key/variant pairs, pinned revision/API/Node version, and
the explicit UTF-8 `Function.prototype.toString()` factory-hash contract before
authorizing native fixture freeze. The oracle worker independently replayed
all 120 variants twice with identical hashes/probes and no provenance failure.

## Effect-graph truth

All thirteen metadata entries are single-pass; do not introduce adapters or a
render graph.

- `classicNoisedeck/coalesce:coalesce` and
  `classicNoisedeck/composite:composite` require caller-provided `inputTex` and
  `tex`; host `mix` maps to the shader's `mixAmt` binding.
- `mixer/patternMix:patternMix`, `mixer/shapeMask:shapeMask`,
  `mixer/split:split`, and `mixer/uvRemap:uvRemap` require caller-provided
  `inputTex` and `tex`.
- `filter/hs:hs`, `filter/repeat:repeat`, `filter/scale:scale`,
  `filter/scroll:scroll`, and `filter/translate:translate` require
  caller-provided `inputTex`.
- `synth/modPattern:modPattern` and `synth/pattern:pattern` are texture-free.

## Explicit exclusions

Do not admit the ten other programs whose first reported blocker is `mod`:
after provisional mod support they require floatBitsToUint, indexing,
derivatives, or loops. They belong to later coherent frontiers.

## Full acceptance gates and report

- Run the complete Python suite plus corpus, semantics, legacy generator, and
  typed generator checks. Preserve 212 bodies / 622 metadata candidates / 646
  variants.
- Configure and build fresh strict-warning Debug and Release trees; run the
  complete native executable and CTest in each.
- Verify Task-5 solid/invert hashes and Task-11 typed/oracle regressions remain
  exact.
- Write `docs/port-engineering/task-12-report.md` with scope/counts,
  runtime/emitter/fail-closed contracts, bindings/effect truth, oracle
  provenance and branch matrix, artifact hashes, test counts, and exactly 153
  corpus programs still without a native public factory.
- Stop for independent review before starting any later frontier.
