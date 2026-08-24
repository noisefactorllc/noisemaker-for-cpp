# Task 28 fresh remaining-frontier audit: exact `mat2` helper return

## Result

**SELECT `filter/rotate:rot`; no blocker.** The current tree is the accepted
post-Task-27 state: 212 corpus programs, 127 typed programs, 129 public
programs, and 83 publicly unported programs. A fresh parse/analyze/validator/
emitter pass over all 85 corpus keys absent from the typed spec (the 83
unported keys plus the two manual public programs) finds Rotate as the only
new program that reaches the existing emitter successfully. Its only current
validator failure is `filter/rotate:rot:14:1: unsupported matrix return type`.

The emitter also passes manual `filter/invert:inv` and `synth/solid:solid`,
which are already public and are not frontier candidates. The one other
remaining program that passes validation, `mixer/focusBlur:focusBlur`, has a
later emitter blocker: `unsupported typed type sampler2D` for its sampler
parameter. Rotate therefore has both fewer semantic changes and no known
later generation blocker.

The complete recomputation is frozen in `task-28-recompute.py` and
`task-28-recomputed.json`. This audit and those artifacts authorize no
repository edit or Git operation.

## Current and projected catalog

| State | Corpus | Typed | Public | Publicly unported |
| --- | ---: | ---: | ---: | ---: |
| Accepted Task 27 | 212 | 127 | 129 | 83 |
| Add only Rotate | 212 | **128** | **130** | **82** |

The current sorted typed/public list SHA-256 values are
`ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72`
and `37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883`.
Adding only Rotate projects
`30f0333cfd995ba1b866fcbd9589507151255204088675bae6575e42d7328c55`
and `102f5436a5416399f2601879c7d5219706111bc64b93989acbb67d973a01b6c5`.
Rotate is zero-based typed position 67:

```text
filter/ridge:ridge
filter/rotate:rot
filter/scale:scale
```

## Fresh first-blocker distribution

The current validator's first diagnostic for the 85 typed-spec-absent keys is:

| First result | Count |
| --- | ---: |
| unsupported global declaration | 30 |
| unsupported counted-for program proof | 19 |
| unsupported `dFdx` | 11 |
| unsupported `fwidth` | 5 |
| unsupported counted-for safety charge | 3 |
| pass | 3 |
| unsupported varying | 2 |
| each of matrix return, mat4, `all`, `any`, `floatBitsToUint`, `reflect`, `round`, `tanh`, index, scalar XOR, inout parameter, uniform block | 1 each |

Only Rotate among the 83 genuinely unported programs also passes the current
emitter. This is stronger evidence than ranking by the first validator error
alone: a scoped validator admission will not merely reveal a known emitter
gap.

## Exact Rotate identity

| Field | Frozen value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Program/runtime key | `filter/rotate:rot` |
| Source | `sources/filter/rotate/rot.glsl` |
| Raw bytes / SHA-256 | 1,197 / `c23e8462e8240f25a715fa3eb05e567269c8d410d27943ba346ebccdd0de1f8f` |
| Normalized bytes / SHA-256 | 964 / `e0e2b723289b08cbfcd6f1fc0a8481869e674de3cfedc0ec5df6d96f64748bb5` |
| Exact defines | `{}` |
| Numeric contract | `glsl-f32` |
| Function count / tuple SHA-256 | 2 / `f5b9f47764c12f05a55925aaca0cf99027ef0b78f67d0122df657f068ba23d56` |
| Whole-program SHA-256 | `3e4312d4c94a8d8b207aa351f8974f417cb5acd63d45a70b1f4a8e606ed2e1b6` |
| Interface SHA-256 | `bfdeb36f89cb3dd84ec4339564e5d830f0f18c9f011d4b563f3cca45973e28df` |
| Public canonical factory | `canonicalFactory127` |
| Factory text SHA-256 | `4dd2ffadbcf25ec3f88c090b014da6cd3ee7faa3ddea970f21714c873dfcf903` |
| Public adapter | absent; public factory is the same canonical object |

The exact ordered interface is:

```text
inputTex:sampler2D@1/S1
rotation:float@2
wrap:int@3
speed:int@4
time:float@5
fragColor:vec4@6/out
```

Resources are five uniforms, one sampler, and one output; texture use is true
and derivatives are false. The program has no loop, unproved loop, struct,
uniform block, varying, array, global matrix, matrix parameter, matrix index,
non-`in` parameter, macro, or public adapter. Its counted-loop proof is
0/0/0/0/0/acyclic.

## Exact matrix-return closure

The only matrix-returning function is signature 10:

```glsl
mat2 rotate2D(float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return mat2(c, -s, s, c);
}
```

Its exact properties are:

- signature/body: ID 10, `rotate2D`, one `in float` parameter ID 8, return
  `mat2`, span `14:1-18:2`, three statements, signature SHA-256
  `a04f91d3f994b30e78f97d04ca5b572c1a94425c25150c6af69345ec8119fd8f`,
  body SHA-256
  `f88f6345a607d84afbe28d4859e3afd70f0c75c0c0e51e4de42cc7f1e2051006`;
- fresh local `c` ID 17 initialized only by `cos(angle)` and fresh local `s`
  ID 18 initialized only by `sin(angle)`;
- the return expression is the sole `mat2` constructor, path
  `(2,'e0',0)`, span `17:12-17:29`, SHA-256
  `e663648e5aadc5bbaf20fe171459a9a64e2deb713a46665e63e3a6c08d416796`;
- its four ordered scalar children are exactly `c`, `-s`, `s`, `c`, with
  source spans `17:17-17:18`, `17:20-17:22`, `17:24-17:25`, and
  `17:27-17:28`; the unary child owns the exact ID-18 `s` child;
- there is no returned matrix local, matrix parameter, second matrix-returning
  helper, overload, prototype, recursion, or matrix state.

The only call is in `main`, function ID 9. The call path is
`(8,'e0',0,1,0)`, span `35:10-35:40`, SHA-256
`5328e90c21b68b353d8c9ab9caf2a1f3ba59d9de557d72729978670f851ff1b1`.
It is child 0 of the sole matrix-vector `*` expression at
`(8,'e0',0,1)`, span `35:10-35:45`, SHA-256
`4e166653131410b87db5123dfe23746cd54e3096b4728e7ea22cd908607d766f`.
Its right child is the local `vec2 uv`. The returned matrix is therefore used
immediately and directly as `mat2 * vec2`, exactly once.

There are exactly two matrix-typed expressions in the whole program: that call
and the constructor. The existing emitter already produces:

```cpp
[[nodiscard]] glsl::Mat2 rotate2D(
    [[maybe_unused]] const State& state,
    [[maybe_unused]] const glsl::PixelContext& context,
    [[maybe_unused]] double angle) noexcept {
  [[maybe_unused]] double c = glsl::cos(angle);
  [[maybe_unused]] double s = glsl::sin(angle);
  return glsl::Mat2(glsl::Vec2(c, (-s)), glsl::Vec2(s, c));
}
```

and one direct `rotate2D(...) * uv`. The current runtime already stores
matrices as column vectors and multiplies `Mat2 * Vec2` with double
accumulation followed by one F32 narrowing per output lane. No runtime or
emitter addition is required.

The frozen exact profile tuple SHA-256 is
`2cfd54eca913518997b359a75e179eb45a323bf50c635b8d2d70874a1dfec76c`.
Caller-provided hashes remain drift alarms rather than authority.

## Recommended exact authorization

Add one identity-only `rotate-mat2-return-v1` profile. It authenticates the
entire program plus the exact helper, constructor children, single call, and
direct matrix-vector parent. The validator may bypass its blanket matrix
return rejection only for the exact authenticated function object. It must
still traverse and validate the helper body and every matrix expression under
the existing rules.

The profile does not authorize a general matrix-return capability. Reject:

- another key, any define, another numeric mode, raw/normalized/source drift,
  or coexistence with any existing per-program profile carrier;
- `mat3`/`mat4`, scalar/vector/array/struct/sampler return, a matrix parameter,
  `out`/`inout`, overload, prototype, recursion, or second matrix return;
- changed local count/type/storage/initializer, a returned matrix local,
  changed constructor kind/type/arity/order/child identity/sign, diagonal or
  composite constructor, matrix indexing/arithmetic inside the helper;
- absent, additional, moved, or changed call; call outside `main`; stored,
  passed, returned, or state-escaped result; vector-matrix or matrix-matrix
  multiplication; non-direct use; dynamic dispatch or indirect call.

Validator and emitter must authenticate independently and require the exact
carrier. The emitter's current generic ability to spell the source is not
authorization. Generated code must return `glsl::Mat2` by value, remain
`noexcept`, and use no heap allocation, static/global matrix, callback,
virtual dispatch, pointer/reference return, or new runtime matrix type.

## Oracle and proof requirements

The hermetic public oracle freezes six non-square quadrant-marked input cases.
They cover wrap values 0, 1, and 2; zero, positive, and negative speed;
stationary and animated time; zero, quarter-turn, negative oblique, and large
accumulated angles. Every case records immutable input hashes/probes,
repeat-identical finite F32 output, exact full F32 and RGBA8 hashes, dimensions,
and five output probes.

Five public-factory mutations cover transposed constructor lanes, different
child identities, a diagonal form, row-major multiply, and a value-equivalent
helper-local return. All four value/layout mutations diverge in at least one
case; the helper-local return is intentionally output-identical but must be
structurally rejected.

The direct matrix harness has six explicit modes:

1. exact direct return with column-major multiply;
2. transposed constructor;
3. row-major multiply;
4. diagonal constructor;
5. wrong sine sign;
6. exact values through a helper-local return.

Each switch arm must execute a genuinely distinct implementation, record both
its numeric mode ID and exact name plus return-shape witness, and have no
fallthrough. The invalid enum path throws. Six angle/vector rows freeze input,
cosine, sine, all four column-major lanes, and output F32 bit patterns for all
six modes. The four incorrect value/layout modes diverge somewhere; exact and
helper-local-return are value-identical but have distinct structural witnesses.

Python must parse the executable C++ public-case and direct-mode tables and
compare every field one-to-one with the frozen JSON. It must tamper each field
independently while the oracle JSON remains unchanged and prove rejection.
This includes case name, dimensions, phase, time, all three uniforms, input
hash/probes, output hashes/probes, mode numeric ID, mode string, return-shape
witness, angle/vector bits, matrix-lane bits, and product bits.

## Ranked residual after Rotate

| Rank | Frontier | Visible examples | Why separate |
| ---: | --- | --- | --- |
| 1 | Exact sampler parameter | `mixer/focusBlur:focusBlur` | Validator passes, but emitter needs a narrow read-only sampler-parameter ABI and call authentication. |
| 2 | Derivative ABI | halftone, stamp, posterize, warp effects | `dFdx`/`dFdy`/`fwidth` require neighborhood, border, and scheduling semantics. |
| 3 | Global/array/matrix aggregates | normal map, kaleido, mat4 programs | Need global lifetime, indexing, dimensions, and broader operator contracts. |
| 4 | Counted resource loops | blur/reduction passes | Need separate work/texture-size budget proofs. |
| 5 | Stage and aggregate interfaces | UBO, varying, struct/copy-out programs | Need representation and binding ABI contracts. |
| 6 | Numeric/sampling extensions | packed bits, vector reductions, round/tanh/reflect | Each needs its own type and F32 semantic proof. |

Task 28 adds one all-default typed factory while leaving every broader matrix,
sampler, derivative, loop, aggregate, stage, global, numeric, and runtime
boundary closed.
