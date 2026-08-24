# Task 12 preflight: `mod` frontier

Date: 2026-08-10  
Repository checked read-only: `.`  
Pinned corpus: `a024dc3a960cc44af454abc7aebce50456c194e6`

## Verdict

The implementation brief has the correct **13-program** scope and is safe to
use for oracle freeze and implementation once one overload wording correction
below is made.  The older planning document's "15 programs" recommendation is
superseded: its two additional keys, `filter/invert:inv` and
`synth/solid:solid`, are the immutable Task-5 public factories, not new typed
programs.

## Scope/count audit

- Current `tools/glslcpp/typed_slice.json` and typed manifest contain exactly
  44 programs; neither legacy key is in that typed slice.
- Current generated catalog has exactly 46 sorted entries and contains each
  legacy key once.
- Adding the brief's sorted 13 keys yields 57 typed programs and 59 public
  catalog factories.  This is the correct distinction: `212 - 57 = 155`
  programs are outside typed generation, while `212 - 59 = 153` have no native
  public factory.
- Each proposed key has metadata default defines `{}`, exactly one pass, and
  parses/types successfully.  Across the 13, the only newly needed builtin is
  `mod`; their other builtins are already in the approved vocabulary.
- The sampler/effect-graph statements in the brief match the pinned metadata
  and typed resources: two samplers for coalesce/composite and the four mixer
  effects; `inputTex` only for the five filters; no samplers for the two synths.
  All 13 are single-pass, so no adapter/render graph is warranted.

## Required correction: exact admitted `mod` forms

Replace the potentially broad wording at brief lines 46--48 and the
"scalar-vector" implication at line 61 with this exact contract:

> Admit `mod(float, float)`, `mod(vec2, float)`, and `mod(vec2, vec2)`, plus
> the emitted `FloatExpr<2>` left-operand equivalents of the latter two.
> Do not admit `mod(float, vec2)`, vec3/vec4 forms, integer `%` changes, or any
> other overload family.

The actual provisional emitter spellings establish why the FloatExpr forms are
required: mirror filters emit `mod((localUV + 1.0), 2.0)` and patterned effects
emit both `mod(p, s)` and `mod((p + h), s)`.  Thus the necessary native shapes
are Vec2/FloatExpr2 with a scalar divisor, Vec2/FloatExpr2 with a Vec2 divisor,
and the existing scalar-double route.  No source emits scalar-vector `mod`.
Vector overloads must consume `Vec2` lanes as Float32 and store each mapped
lane through `f32`; the existing scalar `glsl::mod(double, double)` already
delegates to `noisemaker::glsl_mod(x - y * floor(x / y))` and must remain so.

## Binding and branch obligations

All 13 uniform signatures are distinct, so the fail-closed missing/wrong-type
binding tests must cover each binder, not a representative subset.  In
particular, test every required sampler (`inputTex` and, where listed, `tex`)
in addition to ordinary scalar/vector uniforms.  Preserve the coalesce and
composite host `mix -> mixAmt` mapping.

The oracle branch matrix should deliberately cover these authored decisions:

- coalesce: negative/non-negative `mixAmt`, normal modes, HSV modes
  `1000..1005`, and the `factor` less/equal/greater-than 0.5 paths;
  composite: each blend mode family and its in/out-of-range color tests.
- hs: zero/nonzero chroma and all six hue sectors; repeat/scale/scroll/
  translate: wrap 0 mirror, wrap 1 repeat, and fallback clamp behavior.
- patternMix and pattern: every pattern family (including their triangle
  branch) plus inversion/animation modes; shapeMask: all shape families,
  speed, and inversion; split: speed, flip-cycle parity, and inversion;
  uvRemap: wrap, channel, and source selection.
- modPattern: each shape band, animation mode, and all blend bands.

Exact Float32/RGBA/hash/probe fixtures remain prohibited until the controller
fills the oracle SHA in the brief.

## Fail-closed boundary verified

The 10 excluded `mod`-first candidates still contain the stated later frontier:
`floatBitsToUint` (caustic), indexing (lensDistortion and
prismaticAberration), `dFdx` (bulge, lensWarp, pinch, pondRipples, spiral,
warp), and a `for` loop (reverb).  Do not broaden this task to admit any of
them.  Preserve all Task-11 literal/vector materialization and compatibility
contracts unchanged.

## Evidence performed

- Read the brief and planning document, corpus manifest/metadata/sources, the
  current typed allowlist/catalog, frontend semantic `mod` family, emitter,
  and runtime implementation.
- Parsed and semantically analyzed all 13 at authoritative defaults; recorded
  their resource signatures and builtin sets.
- Performed an in-memory-only provisional emitter mapping to inspect every
  `glsl::mod(...)` call shape; no repository files were changed.
