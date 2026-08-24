# Task 25 Lens tint compatibility frontier audit

Date: 2026-08-11  
Scope: read-only audit of `.`, the
frozen Task 25 artifacts, the pinned canonical JavaScript runtime, current
Task 3 output, and the Task 4 RED native evidence. No repository file, frozen
oracle, or Git state was changed.

## Decision and current blocker

The compatibility gap is exact and bounded. The recommended amendment is one
Lens-only compatibility transform:

```text
lens-truthy-vector-equality-tint-noop-v1
```

It must replace exactly the authenticated conditional expression at typed path
`(21,'e0',0,1,1)` with its existing true branch `color.rgb`. The surrounding
`mix(color.rgb, ..., alpha * 0.01)` remains and therefore still performs the
canonical mix computation and F32 result boundary. No equality, conditional,
vector-truthiness, or tint behavior is exposed generically.

Implementation is **blocked under the current frozen brief/design**, not by a
technical uncertainty. The binding brief SHA-256
`193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2`
explicitly forbids a compatibility transform and its owned-file list does not
authorize a Lens compatibility module. The design SHA-256
`9900749a387a30c6f1db0e584d2382288d44c2f3b0d5670f3b1968f1312c357b`
also requires the lane carrier to reject any simultaneous compatibility
carrier. An amended brief/design must authorize the exact transform, one new
source-locked module (recommended), the exact carrier pair, and the derived
test/generated updates below before repository edits begin.

Three design choices were evaluated:

1. **Recommended: replace the exact conditional with its true branch.** This
   matches the canonical pixel semantics, keeps the surrounding `mix` and
   alpha evaluation, reuses the Refract source-locked transform pattern, and
   produces the smallest generated C++.
2. Replace only the false arm, yielding `predicate ? color.rgb : color.rgb`.
   This retains native predicate evaluation but has no pixel-semantic benefit;
   it preserves a scalar-bool computation that is itself the compatibility
   mismatch. Its proposed final main/function/whole hashes would instead be
   `b72b43b56ad0c9f8ccfaf6bb4aae3e8e7d3aec5f134ba623c44f0b068473a496`,
   `21e0b1a23b81551ab26afc723bda3517d17bd2f746bc5e1bd4c21f6292d77a29`,
   and `7e2ac5aa950891b6bef5c7eadf80907ac9913abcfe30a8d7108c9bd18af3e399`.
3. Add generic vector-equality truthiness or conditional lowering. This is
   rejected: it widens semantics beyond one source/key/site and would affect
   unrelated GLSL equality and conditional expressions.

## Binding inputs and live evidence

| Artifact | SHA-256 / result |
| --- | --- |
| `task-25-brief.md` | `193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2` |
| `task-25-implementation-design.md` | `9900749a387a30c6f1db0e584d2382288d44c2f3b0d5670f3b1968f1312c357b` |
| `task-25-oracle-generator.mjs` | `3594cd9f0a82e7a21e662f8897f43eac0c86943b15ca36b2a0d3d0f805b2772c` |
| `task-25-oracles.json` | `09d8d8a9667fe3b3b90cd582e501b7c0a61d2a41e65ea2d175771a105e32e116` |
| `task-25-oracle-report.md` | `f72b69688d9a2f10df1603d1a012f6df8d0834f012438386038637630eb20611` |
| Oracle check | `ok task-25-oracles.json and task-25-oracle-report.md` |
| Current Task 4 report | `356d4b5e5c11ac217400eea590cf2154869a9bb8553dabeda7f90a3a8cf86f05` |

The frozen oracle remains authoritative and unchanged. Task 4 established that
all four Lens cases are RED while both Prismatic cases and both complete ABI
matrices pass. Named/catalog renders and repeat renders are identical and the
input remains immutable, excluding binding, dispatch, repeatability, and input
mutation as causes.

## Exact source and canonical JavaScript semantics

The sole source is:

```text
tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/
  sources/classicNoisedeck/lensDistortion/lensDistortion.glsl
```

Its public source identity remains 8,269 bytes / SHA-256
`f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444`;
normalized identity remains 7,723 bytes / SHA-256
`6586c49b079a3b0f4aa3538c8e735e70db088ff2e5d2ea1037e9e9c5486fdf52`;
defines are exactly `{}`. Raw line 273 is:

```glsl
color.rgb = mix(color.rgb, (color.rgb == vec3(1.0)) ? color.rgb : min(tint * tint / (1.0 - color.rgb), vec3(1.0)), alpha * 0.01);
```

The exact public/canonical JavaScript is
`../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js`
line 4470. Its relevant emitted text is:

```js
mix(
  new $runtime.PooledFloat32Array([color[0], color[1], color[2]]),
  (new $runtime.PooledFloat32Array([
    color[0] == 1, color[1] == 1, color[2] == 1
  ]))
    ? new $runtime.PooledFloat32Array([color[0], color[1], color[2]])
    : min(/* tint alternative */),
  alpha * 0.009999999776482582
)
```

JavaScript objects, including every `Float32Array`, are truthy regardless of
their elements. Evaluation is therefore exact:

1. evaluate/materialize the first `color.rgb` mix operand;
2. evaluate all three lane comparisons and materialize their
   `PooledFloat32Array`;
3. treat that array object as true;
4. evaluate/materialize the true `color.rgb` arm;
5. do **not** evaluate `tint * tint`, `1.0 - color.rgb`, division, `min`, or the
   false arm's `vec3(1.0)`;
6. evaluate `alpha * 0.009999999776482582`;
7. call canonical `mix`, whose ternary vector path computes and F32-rounds
   every lane even though the two vector values are equal.

Replacing only the conditional with its existing true branch preserves steps
1, 4, 6, and 7 in generated C++ and preserves every pixel-visible value. It
elides the predicate's three reads/comparisons and one ephemeral canonical pool
allocation. That allocation is not a shader-visible side effect: `beginPixel`
resets pool indices; allocation is monotonic within the pixel; the ephemeral
array does not escape; and each later `PooledFloat32Array` constructor fully
overwrites its selected storage. Typed IR/C++ models no pool-allocation side
effect. The existing Refract transform likewise removes the predicates of
canonical truthy typed-array conditionals. If allocation-count identity were
made a requirement, it would require a new runtime side-effect contract and
would be outside this task; it is neither needed nor appropriate here.

## Exact typed AST lock

The typed location uses normalized-source coordinates. It is owned by the sole
`main`, signature/ID 38, whose body has 25 statements.

| Node | Typed path / span | Kind, type, category | SHA-256 |
| --- | --- | --- | --- |
| Assignment parent | `(21,'e0',0)` / `265:5-265:133` | `assign =`, `vec3`, rvalue | `fcad293a35aaa5e8d58fb79a67440fd40a6813a4e3cb5f6621967a419aa0c1ab` |
| `mix` parent | `(21,'e0',0,1)` / `265:17-265:133` | builtin `mix`, `vec3`, rvalue | `0821c5cc7a1190eda7fa50f0c6b681297beee3bec14122ef35ef1df8bc496158` |
| Exact site | `(21,'e0',0,1,1)` / `265:33-265:118` | conditional, `vec3`, rvalue | `d0ed1263c4e79948ce8a260a4d46d3ea4fd2f603e741f711048e59fe67ea0daa` |
| Predicate | site child 0 / `265:33-265:55` | binary `==`, typed scalar `bool`, rvalue | `54bdae95beb11464b7552e4625c5da13588b0856fd92158e3202e96a69ee192a` |
| Predicate lhs | child 0 / `265:33-265:42` | `color.rgb`, `vec3`, lvalue | `48cee70a2575caafe9de2730b82198828ab45dc22f26b7728b9348351e6b3d88` |
| Predicate rhs | child 1 / `265:46-265:55` | `construct vec3(1.0)`, `vec3`, rvalue | `7d19f613fdc4eb2dfecf2b5a85b1ab12b46573ea6636ced78712f919814f9c31` |
| True branch / replacement | site child 1 / `265:59-265:68` | `color.rgb`, `vec3`, lvalue | `5c2f390c2f4dea3e0c0288634599181961adc98a3579c2842e3ab18581be2324` |
| False branch | site child 2 / `265:71-265:118` | builtin `min`, `vec3`, rvalue | `12a3174e1007a3d465ed76b1fde3168b4923a59e3d1e2a7454cf80522321e78e` |

The false branch is exactly `min(tint*tint/(1.0-color.rgb),vec3(1.0))`.
Its first division child hashes to
`fbde657bda13bc59b111f810ed2a8db3d8f84b7c3ecc5f3c7f88130c4fc8fd13`.
The surrounding alpha expression remains site sibling 2, span
`265:120-265:132`, hash
`5078bdeff5e3426961135e7133704398f563ba88e4d99ca249b96a35982a8793`.

The only permitted replacement is the already-existing true-branch value.
After replacement, the parent assignment and `mix` hashes become respectively
`95a24f4f227d4e5304e605a9a7bcaa85ed6bcce8b59845fe91389496d19e7fb7`
and `f1fa2c4575bc6a99069ea50732faffa13dc029e5f1fb061973a9ddacedd6dc6b`.

## Canonical-vs-native mismatch and alpha control

Current emitted C++ is exactly:

```cpp
glsl::set_swizzle<0, 1, 2>(color, glsl::mix(glsl::swizzle<0, 1, 2>(color), ((glsl::swizzle<0, 1, 2>(color) == glsl::FloatExpr<3>(static_cast<float>(1.0))) ? glsl::Vec3(glsl::swizzle<0, 1, 2>(color)) : glsl::Vec3(glsl::component_min(((state.tint * state.tint) / (static_cast<float>(1.0) - glsl::swizzle<0, 1, 2>(color))), glsl::FloatExpr<3>(static_cast<float>(1.0))))), (static_cast<double>(state.alpha) * static_cast<double>(static_cast<float>(0.01)))));
```

`glsl::Vec::operator==` is the default C++ equality operator and returns one
scalar `bool`: true only if all three stored lanes compare equal. Thus the
native false arm runs whenever any color lane is not exactly one, unlike the
always-truthy canonical array object.

Task 4's first divergence at top-down pixel `(0,0)` is blue only:

| Result | F32 bits | Value |
| --- | --- | --- |
| Canonical | `0x3e26616e` | `0.16248103976249695` |
| Current native | `0x3e8a0087` | `0.26953527331352234` |

Red, green, and alpha match at that pixel. All four frozen Lens fixtures have
nonzero tint alpha (`23`, `57`, `38`, `69`) and diverge. For the first fixture:

| Render | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| Canonical, alpha 23 | `40ec6e6bcca21c55b0abe81eca5760b2e623aad76678b49b070d350d0fe49948` | `de4b64895586ce7dc92352820b5c64d5660dc1d722bd8c5392e42568385ec4b8` |
| Current native, alpha 23 | `0517689d4d97caf68ab31c6ac79d345ed30dae6043de7fa34e2771a05381852d` | `e6e053c2e814c3cee1247c38efc4fcb9b5156466d60eca4b6c5abb6cc6e39802` |
| Canonical, alpha 0 | same canonical hashes | same canonical hashes |
| Current native, alpha 0 | exact canonical hashes | exact canonical hashes |

Changing only alpha to zero makes the current native tint mix a no-op and
restores the entire frozen output byte-for-byte. Output alpha itself remains
unchanged in that diagnostic because sampled alpha already exceeds 0.23. This
isolates the discrepancy to native evaluation of the tint alternative; it is
not an oracle, sampler, coordinate, storage, alpha-output, or ABI defect.

## Deterministic transform and profile hashes

Hash serialization is UTF-8 `sha256(repr(value))`, using the existing Task 25
whole-program and interface tuples. The recommended compatibility transform
runs on the ordinary analyzed tree **before** the lane profile, matching the
existing generator order for compatibility transforms.

| Stage | `main` | Function tuple | Whole program | Interface |
| --- | --- | --- | --- | --- |
| Analyzed pre-transform | `dc6d4d2a3b5c50598a879dc6679553b3f89d964a19f5d4c79716970a7f2493ee` | `263870c469a9dc3b1f4d5f3a2498864c6da4ff4eaf2cc3efaf198376e4d304c1` | `f63fb6dba6626791c248501bcfc5ca1c94f073a0593f34dbe846056fe35c81f5` | `53e759b54c0710d9cb3375cc2353878abebec06b378aeaaf9d745c6ecfd2b4ca` |
| Compatibility-only post | `69e4e86508e5dfb982dbc9a0b300a0d1f5e492b0d3a58063087806ced540fcd1` | `9fe84d8f168a7e6c50f40a1a889e0c84f160c9c7654a74d5f5ba29da0894997b` | `8e3e44f36d6f483fc2c5381db69b6751b6c2cc46d346fb1214e3d113eddb20f1` | unchanged |
| Compatibility then lane final | `44757dc7f984ecb1f132473f7979a151adddcaf2fbf3f3e680b35663faefb82c` | `f042dae783e4a99e6671dd39a774d170de7568fd3298c3a21b6cc3ed8bffe9ab` | `66f02d5ab614c12fae43d99b792de30da3e37ea58618ac438fe9a9a4c284f0ec` | unchanged |

The proposed compatibility profile tuple is exactly:

```python
(
  'lens-truthy-vector-equality-tint-noop-v1',
  'classicNoisedeck/lensDistortion:lensDistortion',
  'f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444',
  {},
  (((21,'e0',0,1,1), '265:33-265:118',
    'd0ed1263c4e79948ce8a260a4d46d3ea4fd2f603e741f711048e59fe67ea0daa',
    '5c2f390c2f4dea3e0c0288634599181961adc98a3579c2842e3ab18581be2324'),),
  '263870c469a9dc3b1f4d5f3a2498864c6da4ff4eaf2cc3efaf198376e4d304c1',
  '9fe84d8f168a7e6c50f40a1a889e0c84f160c9c7654a74d5f5ba29da0894997b',
  'f63fb6dba6626791c248501bcfc5ca1c94f073a0593f34dbe846056fe35c81f5',
  '8e3e44f36d6f483fc2c5381db69b6751b6c2cc46d346fb1214e3d113eddb20f1',
  '53e759b54c0710d9cb3375cc2353878abebec06b378aeaaf9d745c6ecfd2b4ca',
)
```

Its SHA-256 is
`79264982e650782b57f2d01ac6a5e18da0cd42a7d11fa846cfb908bb705e2cd9`.
This tuple format is a proposed amended-design lock; it adds no typed-IR field.

Because compatibility executes first, the Lens half of
`literal-vec3-lane-index-v1` must authenticate the compatibility-only tree as
its pre state and the combined tree as its post state. Its eight individual
lane site paths/spans/pre/post hashes remain byte-for-byte unchanged. Only its
aggregate locks change:

| Lens lane-profile lock | Amended value |
| --- | --- |
| Pre main | `69e4e86508e5dfb982dbc9a0b300a0d1f5e492b0d3a58063087806ced540fcd1` |
| Post main | `44757dc7f984ecb1f132473f7979a151adddcaf2fbf3f3e680b35663faefb82c` |
| Pre functions | `9fe84d8f168a7e6c50f40a1a889e0c84f160c9c7654a74d5f5ba29da0894997b` |
| Post functions | `f042dae783e4a99e6671dd39a774d170de7568fd3298c3a21b6cc3ed8bffe9ab` |
| Pre whole | `8e3e44f36d6f483fc2c5381db69b6751b6c2cc46d346fb1214e3d113eddb20f1` |
| Post whole | `66f02d5ab614c12fae43d99b792de30da3e37ea58618ac438fe9a9a4c284f0ec` |
| Interface | `53e759b54c0710d9cb3375cc2353878abebec06b378aeaaf9d745c6ecfd2b4ca` |
| Profile tuple | `71ccd2d24fd938f971dd3a8a569487e24a0e6a3d9daf15351986bb582c646b30` |

An in-memory exact-order reconstruction proved that compatibility-then-lane is
dataclass-equal to lane-then-compatibility; the rewrites are disjoint. The
Prismatic lane lock/profile remains exactly
`25ad8a580a8263b4d2d15b41eb783abeed3433c94b9c8fffbbae2546300fd6b2`.

## Refract precedent and minimal reusable architecture

`tools/glslcpp/frontend/refract_compatibility.py` is the nearest exact
precedent. It provides:

- one transform name and one selected key;
- raw/normalized source, pre/post function, pre/post whole-program, and
  interface locks;
- exact enclosing function/signature/body/control-chain authentication;
- exact per-site expression hashes and branch shapes;
- a `dataclasses.replace` rewrite that turns four canonical truthy-vector
  conditionals into source-locked no-ops;
- exact post-hash verification and rejection of wrong source/key, near misses,
  and already-transformed trees.

`generate_typed_slice.py` imports the Refract name/applicator, freezes it in
the exact `compatibility_transforms` map, dispatches it from
`apply_compatibility_transform`, and applies compatibility transforms before
proof/profile passes. `typed_slice.json` carries Refract in the top-level map,
not in a new typed-IR field. The generated manifest records the exact string;
generated C++ contains only the transformed semantics. Tests lock pre/post
hashes, four rewritten line sites, wrong key/raw/normalized/already-transformed
rejection, proof forgery, static code shape, and absence of surviving ternaries
on the rewritten assignments.

The minimal Lens architecture is therefore:

1. Add a dedicated `frontend/lens_distortion_compatibility.py`; do not make
   `refract_compatibility.py` generic and do not put a Lens case into a broad
   equality helper.
2. Authenticate exact key/source/defines/interface/function/main/path/parent/
   predicate/branch/site hashes, replace that one conditional with the exact
   true-branch object, preserve every non-`main` function by identity, and
   verify the exact compatibility-only post hashes.
3. Add the exact transform string for Lens to the existing top-level
   `compatibility_transforms` map. Keep schema 1 and the existing Lens program
   row's `literal_vec3_lane_index_profile`; add no field/dataclass/proof.
4. Apply compatibility first, then the existing lane profile. Amend only the
   Lens aggregate lane locks/profile hash listed above. Prismatic remains lane
   only.
5. Validator and emitter must accept simultaneous carriers only for the exact
   tuple `(Lens key, lens transform, literal-vec3-lane-index-v1, glsl-f32,
   exact source hash, {})`. They must reject a missing/wrong transform on Lens,
   any compatibility transform on Prismatic, either carrier on a foreign key,
   and all other simultaneous-carrier combinations.

The existing blanket lane check `compatibility_transform is not None` must not
simply be deleted. Replace it with the exact pair predicate above at loader,
validator, and emitter boundaries. Final post-tree authority can remain in the
amended Lens lane profile; the transform module owns the exact pre-to-
compatibility transition.

## Resources, calls, and generated projection

Declarations, resources, interfaces, source, defines, loop proof, bindings,
and all optional proofs are unchanged and object-identical across the proposed
rewrite. Lens remains one sampler, twenty ordinary uniforms, one output,
three static/dynamic texture samples, zero texture-size calls, zero loops, and
zero derivatives. Its direct helper graph remains exactly `map`, `hsv2rgb`,
`rgb2hsv`, `hsv2rgb2`, `rgb2hsv2`, `saturate`, `_distance`, and `main`, with
the same edges. The surrounding `mix` builtin remains. The unreachable false
arm's one `min` builtin and its tint arithmetic disappear from the typed tree;
canonical JavaScript never executes them. No texture/resource/direct-call
site changes.

Projected generated C++ for the source line is exactly:

```cpp
glsl::set_swizzle<0, 1, 2>(color, glsl::mix(glsl::swizzle<0, 1, 2>(color), glsl::swizzle<0, 1, 2>(color), (static_cast<double>(state.alpha) * static_cast<double>(static_cast<float>(0.01)))));
```

Deterministic output projections, assuming only this exact semantic rewrite
and the manifest carrier change, are:

| Artifact/projection | Current | Proposed |
| --- | --- | --- |
| Ordinal-normalized Lens block | 27,446 bytes / `6cfa9d58cbc096b7372b00b17b4ed0b146236a4738acef7870cad05593a57fc5` | 27,183 bytes / `809281c2248ebf0e49a114937caff5b4c65dd4a7d9c1ee3e910a5f7c7345ea38` |
| `src/typed_generated/typed_slice.cpp` | 1,025,371 bytes / `b8fe5a45f3032a86185d0515d512a48c40ac37c689c18db0ecb43bf7108b1cc9` | 1,025,108 bytes / `e82231eec2e91c88b0ba5bef73414ea6132786f89e792a0a5e3e6cd3e2d23df2` |
| `src/typed_generated/typed_manifest.json` | 196,916 bytes / `618081cfc312bae9e219a20c0876a23e2066e8630796f9872ef495f440a63b81` | 196,952 bytes / `0fe78ccfc475bec0993c0ac1f3c920fc3c1ded669c4e9c0aefaa6b3aeb020567` |
| `tools/glslcpp/typed_slice.json`, exact sorted-line formatting | 10,319 bytes / `1534c7a6d807bf58734da59aaa8b37f8dc8342ec5d744b936e2e6e079ad1bb49` | 10,417 bytes / `678a685121b0477d84f75231e599ed940385148cbcb7a1cc229090ce73f9d8a5` |
| `include/noisemaker/generated/catalog.hpp` | `cb0a5785163273723e85c77b868b70beb92f5775f113117c4d246c6467f2b80f` | unchanged |

The manifest's Lens row changes only
`compatibility_transform: "none"` to the exact transform name, plus the
monolithic output hash on every row. Counts, explicit sorted keys, positions,
and list hashes remain `125 typed / 127 public / 85 publicly unported / 212`,
Lens 2 / Gather 52 / Prismatic 59,
`9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4`
typed, and
`9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`
public. All non-Lens generated blocks and the catalog/header inventory remain
byte-identical; only the monolithic output hash changes in prior manifest rows.

Implementation-source/test file hashes cannot be computed before the amended
design chooses and authorizes their exact edits. They must be frozen after
implementation; the semantic and generated projections above are already
deterministic.

## Required fail-closed tests and gates

### Transform and carrier

- Exact positive transition: analyzed pre tree -> compatibility-only hashes ->
  amended lane profile -> combined final hashes. Require one replacement and
  non-`main` function identity.
- Reject wrong key/path/source/raw/normalized/defines/main ID/body count,
  moved/reordered/duplicate/zero/two sites, wrong parent/mix/assignment,
  predicate operator/type/children, either branch, span, pre/post/site/profile
  hash, and already/twice transformed input.
- Reject predicate changed to scalar equality, another vector width/base,
  another `vec3(1.0)`, another conditional, another tint expression, or a
  caller-recomputed hash. Caller hashes remain alarms, never authority.
- Loader exact-map tests must require the Lens transform and reject absent,
  wrong, foreign, duplicate-equivalent, Prismatic, Grade-LUT, and generic
  transform entries.
- Direct validator/emitter four-mode coverage becomes two-carrier coverage for
  Lens: raw pre is never accepted directly; compatibility-only is not final;
  lane-only with the old hash is rejected; exact combined post plus both exact
  carriers accepts; missing/wrong either carrier rejects. A dataclass-equal
  final clone accepts post authority, while transition identity remains a
  separate test.

### Generated/code shape

- Freeze the projected normalized Lens block, whole C++, manifest, slice JSON,
  and unchanged header hashes above.
- Require exactly the proposed self-mix line; forbid the Lens tint ternary,
  scalar vector equality, tint division/min alternative, runtime branch,
  allocation, callback, indirect dispatch, or generic truthiness helper.
- Re-run all eleven lane mutation controls unchanged. Their paths and
  sensitivity remain authoritative.
- Preserve exact bindings, three texture calls, zero texture-size calls,
  resource tuple, direct helper graph, stack/disassembly, and no-allocation/
  no-indirect-call gates.

### Native/oracle

- Re-run `node docs/port-engineering/task-25-oracle-generator.mjs --check`
  before and after; frozen artifacts must remain unchanged.
- The existing six-case native fixture must make all four Lens and both
  Prismatic cases full-F32 and RGBA8 GREEN through named and catalog binders,
  with repeatability, finiteness, input immutability, probes, tile/origin, and
  alpha checks unchanged.
- Retain the alpha-23 current-native divergence as a negative sensitivity
  control and alpha-zero exact identity as the no-op control. Disabling or
  mutating the compatibility transform must diverge on the four nonzero-alpha
  Lens cases; it must not affect Prismatic.
- Re-run exact ABI matrices, Debug/Release/ASan/UBSan native gates, Python,
  CTest, generated-isolation, and driver checks. No RGBA8-only or tolerance
  acceptance is allowed.

## Task 3 expectations superseded by an amended design

The following current Task 3 expectations become historical and must change
only in current-Task-25 assertions:

- Lens lane profile hash `d1235bb6045a5795c4c10c5db8a990f51ee42e5541dcfa7a663c91f3245d10d3`
  and its aggregate pre/post main/function/whole locks;
- Lens normalized projection 27,446 bytes /
  `6cfa9d58cbc096b7372b00b17b4ed0b146236a4738acef7870cad05593a57fc5`;
- generated C++ and manifest hashes `b8fe5a45...` and `618081cf...`;
- the expected Lens manifest value `compatibility_transform: "none"`;
- current exact compatibility-map assertions that omit Lens;
- `test_task25_loader_schema_admits_only_the_two_later_lane_carriers`, whose
  current `compatibility` mutation deliberately adds a transform to Lens and
  expects rejection;
- four-mode helpers that call validator/emitter with the lane carrier but no
  Lens compatibility carrier;
- Task 25 generated-isolation expectations that all Task 24 blocks are
  unchanged remain valid, but Lens's new block hash must be the proposed one.

Historical Task 21/22/23/24 reconstruction tests must keep their historical
compatibility maps by explicitly removing the later Lens transform when they
derive old specs. They must not be globally updated to pretend the transform
existed in earlier tasks.

The pre-existing C++ catalog test still expects 125 public factories while the
accepted Task 3 catalog has 127. That stale test must be corrected to the
accepted 127-key list independently; it is not evidence for or against the
Lens transform and must not be hidden by this amendment.

## Approval input

Approve option 1 only: amend Task 25 to authorize one dedicated Lens
compatibility module and the exact transform-first/lane-second carrier pair,
using the hashes and gates above. Options 2 and 3 should remain explicitly
forbidden.
