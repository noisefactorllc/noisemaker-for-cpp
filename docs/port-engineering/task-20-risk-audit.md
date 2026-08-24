# Task 20 implementation-risk audit: fixed affine `vec2[13]` centers

Date: 2026-08-10  
Scope: projected post-Task-19 baseline (113 typed / 115 public), read-only
inspection of the pinned corpus, direct canonical CPU factory, and current
typed frontend/emitter. No repository file was changed and no Git command was
used.

## Recommendation and projected count

Admit at most this one source-identity-locked profile:

```text
fixed-affine-centers13-v1
  synth/sacredGeometry:sacredGeometry
```

This is a source-specific local-table proof, not a generic array or arithmetic
indexing capability. It admits one automatic `vec2[13]` in `fruitMask`, its
three exact initializer regions, and four later direct-index read sites.

| Projection point | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Post-Task-19 baseline supplied for this audit | 113 | 115 | 97 |
| After exactly this Task-20 key | 114 | 116 | 96 |

The corpus manifest remains 212 programs. These are projection counts only;
they do not claim that Task 19 or Task 20 is implemented in the current
checkout.

## Exact source, runtime, and binding contract

| Field | Locked value |
| --- | --- |
| Key/runtime key | `synth/sacredGeometry:sacredGeometry` |
| Source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/sacredGeometry/sacredGeometry.glsl` |
| Raw bytes / SHA-256 | `9710` / `24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de` |
| Normalized bytes / SHA-256 | `8395` / `6b3c4e8492a69969f3d6f78689cfd19de846656fd0c6d5c8dfd5a758427c61d3` |
| Runtime define map | `{}` |
| Canonical factory | `canonicalFactory273`; exact `Function.prototype.toString()` SHA-256 `b4ed8af983d8bda5d48e05d418458c2fc82170f745b021199df7f7095fadb2f2` |
| Canonical generated runtime | `../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js`; SHA-256 `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Resources | none; no samplers, textures, derivatives, varyings, uniform blocks, or structs |
| Source output | `fragColor:vec4@18` |
| Metadata pass route | no inputs; logical pass output `color -> outputTex` |

The exact source declaration order and stable typed symbol identities are:

```text
resolution:vec2@1
tileOffset:vec2@2
fullResolution:vec2@3
aspect:float@4
scale:float@5
rotation:float@6
thickness:float@7
smoothness:float@8
geometry:int@9
rings:int@10
starPoints:int@11
animation:int@12
speed:float@13
pulseDepth:float@14
time:float@15
fgColor:vec3@16
bgColor:vec3@17
fragColor:vec4@18 (output)
```

There is no sampler binding or sampler slot. `resolution`, `tileOffset`,
`fullResolution`, `aspect`, and `time` are render/runtime inputs. The
source-bound metadata defaults are:

```json
{
  "animation": 0,
  "bgColor": [0, 0, 0],
  "fgColor": [1, 1, 1],
  "geometry": 0,
  "pulseDepth": 0.15,
  "rings": 3,
  "rotation": 0,
  "scale": 10,
  "smoothness": 0.02,
  "speed": 1,
  "starPoints": 5,
  "thickness": 0.2
}
```

Metadata describes `speed` as an integer-valued slider, but the shader binding
is exactly `float`; that existing UI/source distinction is not a Task-20
compatibility transform. The source's `PI`, `TAU`, `SQRT3`, animation codes,
and geometry codes are source-local preprocessor macros already authenticated
by the raw and normalized source hashes. They are not runtime defines.

The analyzed program has 18 global interface declarations and 12 functions.
The relevant stable identities are `fruitMask` signature 40,
`p:vec2@31`, `drawLines:bool@32`, and local `centers:vec2[13]@73`.

## Canonical zero-fill and precision semantics

Canonical JavaScript creates `centers` on every `fruitMask` invocation as a
13-element plain array whose elements are 13 distinct, explicitly reset
`PooledFloat32Array([0, 0])` objects. Thus:

- all 26 scalar lanes begin as positive F32 zero, even though subsequent proof
  establishes a complete write before every read;
- a vector assignment stores both result lanes through a Float32Array boundary;
- scalar `float` temporaries such as `angle` remain JavaScript Numbers between
  explicit consumption/storage boundaries; and
- source floating literals first obey the existing `glsl-f32` literal
  contract. In particular, canonical `PI` is
  `3.1415927410125732`, `SQRT3` is `1.7320507764816284`,
  `PI/6` is `0.5235987901687622`, and `2*SQRT3` is
  `3.464101552963257`.

The only narrow native representation is therefore:

```cpp
std::array<glsl::Vec2, 13> centers{};
```

The braces are mandatory: current `glsl::Vec2` contains two zero-initialized
`float` lanes, and its assignment from `glsl::FloatExpr<2>` rounds each lane
through `noisemaker::f32`. The affine center RHS must use the existing scalar
Number-compatible expression lowering (`double angle`, F32 source literals,
`cos`/`sin`, then a `glsl::Vec2` materialization). Lowering `angle` to C++
`float`, retaining the RHS as an unmaterialized expression, using doubles for
stored center lanes, or omitting value initialization can change canonical
bits and is forbidden.

The array's logical payload is 26 F32 lanes, 104 bytes. Native tests should
lock `sizeof(glsl::Vec2) == 8` and `sizeof(std::array<glsl::Vec2,13>) == 104`
on supported builds rather than silently assuming an ABI. This is stack-local
automatic storage; no heap, pointer, span, static storage, or array copy is
needed.

## Complete affine-initialization proof

All coordinates below are normalized typed-source coordinates; the equivalent
raw source lines are 112-120. `fruitMask` body statement indices are part of
the shape lock.

| Role | Typed identity/span | Exact statement and loop proof | Dynamic writes | Proven index set |
| --- | --- | --- | ---: | --- |
| Declaration | body[2], symbol 73, `96:10` | uninitialized source declaration `vec2 centers[13]` | 0 | none yet; native braces still zero-fill |
| Center | body[3], index span `97:5` | `centers[0] = vec2(0.0, 0.0)` | 1 | `{0}` |
| Inner ring | body[4], index span `100:9` | exact `k@74 = 0; k < 6; k++`; body has `angle = float(k)*PI/3.0`, then `centers[1+k] = 2.0*vec2(cos(angle),sin(angle))` | 6 | `{1,2,3,4,5,6}` |
| Outer ring | body[5], index span `104:9` | distinct exact `k@76 = 0; k < 6; k++`; body has `angle = float(k)*PI/3.0 + PI/6.0`, then `centers[7+k] = 2.0*SQRT3*vec2(cos(angle),sin(angle))` | 6 | `{7,8,9,10,11,12}` |

For both affine loops, the induction proof is start 0, strict bound 6,
unit post-increment, six trips, with no `if`, `continue`, `break`, return, or
second indexed write in the loop body. Integer addition is exact over these
ranges. Therefore the three write sets are pairwise disjoint, their union is
exactly `[0,12]`, and there are exactly 13 vector writes before any read. Every
element is assigned exactly once. There is no later write.

The proof must authenticate the RHS as well as the index interval. Merely
showing that `1+k` and `7+k` are in bounds is insufficient: swapped radii,
changed angle phase, changed `PI`/`SQRT3`, a removed `vec2` materialization, or
a reordered/conditional initializer would be source drift even if memory
safety remained true.

## Complete read proof

There are four static array-index read sites after initialization:

| Site | Span | Index proof | Dynamic reads |
| --- | --- | --- | ---: |
| `length(centers[i])` | `114:39` | `i@81 = 0; i < 13; i++` | 13 |
| `length(p - centers[i])` | `120:30` | same `i@81` | 13 |
| line endpoint `centers[i]` | `140:46` | outer `i@88 = 0; i < 13; i++` | 78 on accepted pairs |
| line endpoint `centers[j]` | `140:58` | inner `j@89 = 0; j < 13; j++` | 78 on accepted pairs |

The circle loop performs 26 dynamic element reads. The line loops visit the
complete 13 by 13 grid. Their exact scalar guard `if (j <= i) continue`
rejects 91 pairs (the diagonal and lower triangle) and accepts the 78 pairs
with `j > i`, so they perform 156 dynamic element reads and 78
`lineSegmentSDF` calls. The Metatron path therefore performs 182 dynamic
center reads; the Fruit path performs 26.

Only direct induction identifiers are allowed at read sites. There is no
whole-array read, copy, parameter passing, return, closure/capture, address
taking, alias, or escape. `centers` is not visible outside `fruitMask`.
`geometry == 1` calls `fruitMask(p, false)` and executes the circle reads but
not the line reads; `geometry == 3` calls `fruitMask(p, true)` and executes
both. Other geometry branches do not allocate or access this table.

## Counted-loop charge, stack, and hot path

The current independently recomputed whole-program loop proof is:

```text
loop_count=9
unproved_loop_count=0
max_effective_depth=2
max_lexical_product=169
entrypoint_charge=207
call_graph_acyclic=true
```

The nine loops are Flower's 13 by 13 `q/r` grid; the two six-trip center
initializer loops; the 13-trip circle loop; Metatron's 13 by 13 `i/j` grid;
Borromean's three-trip loop; and Star Polygon's 12-trip loop with a scalar
`break`. All existing `continue` and `break` statements stay inside proved
counted loops. The source is within the current limits (trip <= 128, depth <=
3, product <= 4096, entrypoint charge <= 4096); Task 20 adds no loop/control
capability.

For the maximum Metatron path, the exact charge decomposition is
`6 + 6 + 13 + 13 + 169 = 207` loop iterations/visits. It performs 13 center
writes, 13 circle SDF/outline evaluations, 78 line SDF/outline evaluations,
and 182 center reads per output pixel. Fruit skips the line branch and executes
`6 + 6 + 13 = 25` loop iterations, 13 writes, 13 circle evaluations, and 26
reads. This makes Metatron a required performance and parity case, not merely
an extra branch test.

The center array contributes a fixed 104-byte logical payload to the
`fruitMask` frame for each active pixel evaluation. The loops do not grow the
stack, there is no recursion, and calls are synchronous. Nevertheless, total
frame size includes ordinary scalar/vector locals, call ABI effects, inlining,
debug padding, and the 78 serial `lineSegmentSDF` calls; implementation tests
must record compiler stack-usage output in debug and release and run
sanitizers. A source-level 104-byte calculation is not a total-frame
measurement.

## Provenance and proof recomputation

Using the current typed dataclass representation after semantic analysis and
counted-loop attachment:

- SHA-256 of `repr(program.functions)` is
  `261327d6c1700f71cef056020358ba1ea4dd56c1e8d1017f545df805a4f9b1d8`.
- SHA-256 of the current whole-program profile
  `(key, source, raw_source, declarations, functions, resources, body_status,
  local_type_names, structs, uniform_blocks, interface_symbols,
  builtin_symbols, counted_loop_proof, preprocessor_defines)` is
  `2dda5c4f3931965da85ac54fca2b6e4748cb2cb1ca61b03316f750c2f6754388`.

These fingerprints are additional drift alarms, not substitutes for source
hashes and structural proof. They intentionally fail closed if typed-IR schema,
symbol allocation, spans, function bodies, interfaces, resources, or loop
proofs change.

`fixed-affine-centers13-v1` should have its own proof type/module rather than
loosening `fixed-nine-local-literal-init-counted-read-v1`. Both validator and
emitter must independently recompute the proof from a program with any
attached affine proof cleared, after recomputing counted-loop proofs. The
recomputed object must bind the source/factory/define/binding identities,
function/body identities, all seven static index spans, induction symbol IDs,
exact affine ASTs and RHSs, complete/disjoint initialization, no read before
initialization, no write after initialization, no escape, array/reference
counts, 104-byte payload, typed-function fingerprint, and whole-program
fingerprint. A missing, stale, forged, foreign-key, or source-mismatched proof
must fail at validation and again at emission.

## Current frontend/emitter gap and exact implementation boundary

Current semantic parsing is already sufficient: it produces `vec2[13]`,
stable array/induction identities, affine index ASTs, and all nine counted-loop
proofs. Current validation stops at exactly:

```text
synth/sacredGeometry:sacredGeometry:96:10:
unsupported typed type vec2[13]
```

The existing validator admits array declarations and index expressions only
through the source-locked fixed-nine proof. Its store map recognizes literal
indices and its read map recognizes one proof-wide induction identity. That
cannot soundly express two affine store inductions plus three later read
identities. The new validator path must admit the array-typed base only when it
is the registered base of one of the seven exact index expressions; it must
not add `vec2[13]` to the global approved-type vocabulary or accept arbitrary
binary indices.

The emitter likewise has no array entry in `_TYPES`; `_proved_array`,
`_proved_index`, and local declaration emission are coupled to the fixed-nine
profile, and declaration output hard-codes extent 9. Task 20 should emit extent
13 and the two exact binary store indices only from the new proof role/span.
All other array types and index shapes must continue to throw. The count-loop
emitter, direct `std::array::operator[]`, vector assignment, and ordinary
scalar/vector expression paths can be reused unchanged.

As a diagnostic only, the source was transformed in memory to replace the
array with one ordinary `vec2`, keep both initializer loops/RHS expressions,
and replace all later table reads with that scalar vector. Under a non-locked
audit key, the resulting program passed the current capability validator and
rendered 24,816 bytes of C++. This is evidence that the surrounding non-array
vocabulary is already accepted; it is not an array proof and is not a parity
oracle.

## Non-array semantic compatibility audit

No additional semantic blocker or compatibility transform was found.

- Every condition in the canonical factory is a scalar Boolean. There is no
  vector-equality typed-array truthiness hazard of the kind requiring the
  Task-19 Refract compatibility rule.
- The sole source conditional expression is the scalar Boolean
  `drawLines ? 0.6 : 1.0`; it has ordinary native semantics.
- Vector parameters (`p`, and `p/a/b` in `lineSegmentSDF`) are copied by the
  canonical runtime and already lower by value in the typed emitter.
- `st = rotate2D(st, ...)`, vector compound assignments, scalar `break` and
  `continue`, reversed-edge `smoothstep` in `outlineEdge`, source constants,
  and the used scalar/vector builtins are all in the current admitted
  vocabulary. Reversed-edge `smoothstep` remains the existing canonical
  runtime contract; it is not a new source rewrite.
- There is no sampler/resource ABI, derivative mode, matrix, packed word,
  array parameter/return, or output-route rewrite to add.

Accordingly the typed-slice compatibility-transform entry for this key should
be absent/`none`. If a future oracle disagrees after the exact array lowering,
stop and diagnose it; do not add a speculative transform to this profile.

## Required tests, negative cases, and exclusions

Positive structural tests must prove all locked provenance above, the one
`vec2[13]@73` declaration in `fruitMask`, explicit zero-fill lowering, the
three write sets `{0}`, `{1..6}`, `{7..12}`, exactly 13 vector stores, their
exact RHSs, all four direct read sites, the 26/156/182 dynamic-read counts,
the 78 accepted unordered pairs, and no other array reference. They must
recompute the loop and whole-program proofs instead of trusting serialized
proof fields.

Negative tests must reject at least:

- another key, raw/normalized/factory hash, nonempty runtime defines, changed
  bindings/default profile, forged proof, or any whole-program fingerprint
  drift;
- a different array name, element type, extent, storage class, function,
  declaration index, initializer order, or an aggregate initializer;
- a missing/duplicate `centers[0]` write, `2+k`, `6+k`, `8+k`, `k+1` if exact
  source shape is required, a changed loop start/bound/comparison/update, a
  conditional/early-exit initializer, overlap, gap, or second write;
- a changed radius/phase/RHS, early read, post-init write, affine read,
  literal read, unproved induction, out-of-range index, whole-array use,
  copy/assignment, parameter pass, return, alias, pointer/span, capture, or
  escape; and
- generic arrays, another extent/element, global/static/heap arrays, nested or
  multidimensional arrays, arrays in structs, array parameters/returns,
  `out`/`inout`, generalized affine indexing, derivatives, samplers/textures,
  matrices, packed words, or another Task's proof profile.

The exact source uses `1 + k` and `7 + k`. Even an algebraically equivalent
spelling such as `k + 1` should be rejected by this source-shape proof unless a
future separately reviewed profile intentionally broadens it.

## Canonical oracle requirements

Freeze direct canonical-factory oracles before implementation using
`canonicalKernelFactories` + `bindCanonicalKernel` + `runPass` + `Surface`.
Do not use a GPU result or a native implementation as the reference. Record
the corpus revision, raw/normalized source hashes, canonical generated-file
hash, factory-to-string hash, exact binding signature, all explicit uniform
values and F32 words, render context, top-down storage/fragment-origin rules,
F32 and RGBA8 byte hashes, representative lane-bit probes, opaque alpha, and
fresh-surface repeat identity.

The minimum array-sensitive matrix is:

1. `geometry=1`, animation off: Fruit executes all initialization and both
   circle read sites but skips line reads.
2. `geometry=3`, animation off: Metatron adds the 13 by 13 grid, triangular
   `continue`, `centers[i]`/`centers[j]`, and all 78 line calls.
3. Fruit or Metatron with `animation=4`: ripple uses center distance and is
   sensitive to center-lane F32 storage.
4. Metatron with `animation=5`: unfold exercises center distance,
   `circleUnfoldRange=0.6f`, and line visibility.
5. `geometry=0` with defaults as a non-array control.

Because this publishes an entire factory, add branch cases for the remaining
metadata choices (`geometry=4,5,6,7,8`) and representative rotate/pulse paths,
including a nondefault `rings` and `starPoints`. Use a non-square output,
nonzero `tileOffset`, distinct larger `fullResolution`, explicit runtime
`aspect`, nondefault F32 `scale`, `rotation`, `thickness`, `smoothness`,
`speed`, `pulseDepth`, and `time`, and nontrivial foreground/background colors.
Choose dimensions and scale after inspecting the reference image/probes so
both inner and outer circles and several connecting lines are sampled; a
mostly background fixture is not an adequate oracle.

Runtime oracles cannot replace the structural proof. Rotating or permuting all
six members of a ring can leave Fruit unchanged, and Metatron draws the
complete unordered graph, so several wrong initializer orders are
observationally symmetric. Removing the explicit zero-center store may also
be masked by required zero initialization. Structural tests must catch those
cases. Separately require oracle-mutant sensitivity for a missing/duplicated
outer center, changed outer radius/phase, `centers[j]` replaced with
`centers[i]`, and a lost accepted line pair; regenerate the fixture if the
chosen hashes/probes do not diverge.

Native parity must compare every frozen F32 byte, not only RGBA8, in debug and
release with sanitizers and stack-usage measurement. RGBA8 can hide F32 lane
rounding, reversed-edge smoothstep, and small geometric differences.

## Boundary statement

This audit authorizes no repository edit. Task 20 should add exactly one
typed/public factory under `fixed-affine-centers13-v1`; it must not generalize
fixed arrays, arithmetic indexing, or any ABI/resource feature, and it needs
no non-array compatibility transform on the evidence available now.
