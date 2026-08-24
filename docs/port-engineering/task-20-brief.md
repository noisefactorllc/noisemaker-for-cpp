# Task 20 Sacred Geometry Implementation Brief

> **For agentic workers:** Implement only after an independent scope/proof review. Use a test-first execution workflow with a review gate after the compatibility transform, after the affine-table proof, and after native parity. This brief authorizes no implementation and no Git operation.

**Goal:** Add exactly `synth/sacredGeometry:sacredGeometry` as the one
`fixed-affine-centers13-v1` factory while preserving the pinned canonical
JavaScript Number-division behavior at one exact Star Polygon source site.

**Architecture:** Apply one key/source/function/span-locked compatibility
transform to the analyzed typed tree, then independently prove the one local
`vec2[13]` table and its seven index sites. Validator and emitter each clear
and recompute the proof, and the emitter lowers only the registered table and
indices to a zero-initialized stack `std::array<glsl::Vec2, 13>`.

**Tech stack:** Python 3 typed frontend/proof modules, typed-IR C++20 emitter,
`std::array`, the existing GLSL runtime, direct canonical CPU oracles, CMake,
CTest, ASan/UBSan, and compiler `.su` stack-usage output.

## Global constraints

- Scope is exactly `synth/sacredGeometry:sacredGeometry`; no adjacent key is
  admitted.
- Add exactly `fixed-affine-centers13-v1` plus exactly
  `sacred-star-number-division-v1`.
- Do not add generic arrays, generic affine indexing, global array types, or a
  global change to integer division.
- Preserve `glsl-f32` literals, JavaScript Number scalar temporaries, F32
  vector storage boundaries, strict `-ffp-contract=off`, and direct canonical
  output bytes.
- No sampler/resource ABI, derivative, varying, matrix, struct, block, packed
  word, parameter-direction, output-route, heap, or dispatch capability is in
  scope.
- Do not use Git, create a branch/worktree, commit, push, or open a pull
  request.

---

## Status, supersession, and count gate

This brief supersedes the final “no non-array compatibility transform”
conclusion in `task-20-risk-audit.md`. The subsequent ten-case direct
canonical oracle proved that an array-only implementation is not sound:
native truncating integer division would render finite Star Polygon geometry,
whereas the pinned canonical JavaScript factory emits qNaN in every RGB lane.

Conditional on the accepted post-Task-19 baseline, the exact count movement is:

| Projection point | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Post-Task-19 baseline | 113 | 115 | 97 |
| Accepted Task 20 | **114** | **116** | **96** |

The corpus stays at 212 programs. Acceptance must assert all three final
counts, the exact sorted public catalog, and exclusion of neighboring keys.

## File ownership and implementation boundary

Expected implementation surface:

- Create `tools/glslcpp/frontend/sacred_geometry_compatibility.py`: authenticate
  and perform the one five-node Number-semantics typed-tree rewrite.
- Create `tools/glslcpp/frontend/fixed_affine_centers13_proof.py`: define the
  source locks and recompute the entire local-table proof from the transformed
  typed program.
- Modify `tools/glslcpp/frontend/typed_ir.py`: add immutable proof records and
  one optional `fixed_affine_centers13_proof` field. Do not add an ambient
  array capability flag or runtime lookup structure.
- Modify `tools/glslcpp/generate_typed_slice.py`: register the exact capability,
  transform name, source key, proof attachment order, validation census, count
  locks, and generated-output plumbing.
- Modify `tools/glslcpp/emit_typed_cpp.py`: independently validate the
  transformed profile/proof and add exact declaration/index emission for this
  profile only.
- Modify `tools/glslcpp/typed_slice.json`: add the sorted program with `{}`
  defines, the one capability, and the exact compatibility transform mapping.
- Modify `tests/test_typed_generator.py`, `tests/test_typed_slice.cpp`, and
  `tests/test_generated_kernels.cpp`: add positive, negative/tamper, native
  oracle, binding, catalog, count, and code-shape coverage.
- Regenerate only `src/typed_generated/typed_slice.cpp`,
  `src/typed_generated/typed_manifest.json`, and
  `include/noisemaker/generated/catalog.hpp` through the existing generator.

No source corpus file, runtime API, public binding type, or unrelated generated
factory should change.

## Frozen identity, provenance, and bindings

| Field | Required value |
| --- | --- |
| Key/runtime key | `synth/sacredGeometry:sacredGeometry` |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Source | `sources/synth/sacredGeometry/sacredGeometry.glsl` |
| Raw bytes / SHA-256 | `9710` / `24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de` |
| Normalized SHA-256 | `6b3c4e8492a69969f3d6f78689cfd19de846656fd0c6d5c8dfd5a758427c61d3` |
| Runtime defines | exactly `{}` |
| Numeric literal contract | `glsl-f32` |
| Canonical factory | `canonicalFactory273`; factory-text SHA-256 `b4ed8af983d8bda5d48e05d418458c2fc82170f745b021199df7f7095fadb2f2` |
| Canonical generated runtime | SHA-256 `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Resources | none |
| Output | `fragColor:vec4@18`; logical `color -> outputTex` |

The exact declaration/binding order is:

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

There is no sampler or sampler slot. The source-local macros `PI`, `TAU`,
`SQRT3`, animation codes, and geometry codes remain authenticated source text,
not runtime defines. Metadata defaults remain animation 0, black background,
white foreground, geometry 0, pulseDepth 0.15, rings 3, rotation 0, scale 10,
smoothness 0.02, speed 1, starPoints 5, and thickness 0.2. The shader `speed`
binding remains `float` even though the UI slider is integer-valued.

The external canonical factory hash is oracle provenance, not a new build-time
dependency on `../noisemaker-for-cpu`. Native generation
must remain self-contained in this repository.

## Exact Star Number-division compatibility transform

### Cause and required canonical result

Raw line 276 / normalized line 260 in `starPolygonMask` is:

```glsl
int j = (i + 2) - ((i + 2) / n) * n;
```

The exact typed identities are `starPolygonMask` signature 46, induction
`i@106`, parameter `n@37`, and local `j@107`. Canonical JavaScript keeps this
arithmetic as binary64 Number arithmetic. At `i=0` and every metadata
`starPoints` value 5 through 12, `2 - (2/n)*n` rounds to positive zero. The
first line segment is degenerate, `dot(ba,ba)` is zero, the projection performs
floating `0/0`, and qNaN propagates through every output RGB lane.

The native transform name is exactly
`sacred-star-number-division-v1`. It must not use `%`, native integer division,
an injected `geometry == 7` shortcut, an `isnan` branch, a hard-coded NaN
output, or a global arithmetic rule.

### Frozen pre/post typed locks

Before transformation, require:

```text
SHA256(repr(program.functions))
  261327d6c1700f71cef056020358ba1ea4dd56c1e8d1017f545df805a4f9b1d8

SHA256(repr((key, source, raw_source, declarations, functions, resources,
             body_status, local_type_names, structs, uniform_blocks,
             interface_symbols, builtin_symbols, counted_loop_proof,
             preprocessor_defines)))
  2dda5c4f3931965da85ac54fca2b6e4748cb2cb1ca61b03316f750c2f6754388
```

Transform exactly five typed nodes and nothing else:

1. Division `/` at normalized `260:29-39`: type `int -> float`.
2. Its multiplication parent `*` at `260:29-44`: type `int -> float`.
3. Root subtraction `-` at `260:18-44`: type `int -> float`.
4. Declaration expression and attached symbol for `j@107` at `260:13-44`:
   type `int -> float`.
5. The sole later `j@107` identifier read inside `float(j)` at `262:30-31`:
   expression and attached-symbol type `int -> float`.

All spans, categories, symbol IDs/names/storage/writability, operators,
children, literals, statement/control ancestry, the `float(j)` constructor,
and every other function/node remain byte-for-byte dataclass-equal. Under the
existing emitter contract a typed `float` local is a C++ `double`, so this
models the canonical Number temporary while the authored `float(j)` remains
the F32 consumption boundary.

After exactly that rewrite, require:

```text
SHA256(repr(program.functions))
  fdaf48f945303bfe83c56ee0e2e75ae62d418904c02fc2bc6621fc0da907f7b2

SHA256(repr(the same whole-program tuple))
  de499dea91a59d8fc5ec4591be30a9b4350bb6a9e0317259aa97e8d3e3586ee0
```

The transform function must fail on a missing, duplicated, pre-transformed,
partially transformed, span-shifted, wrong-key, wrong-source, wrong-function,
wrong-symbol, wrong-operator, wrong-literal, wrong-parent, or extra matching
site. It must verify both frozen pre hashes before rewriting and both frozen
post hashes afterward. The validator and emitter must independently
authenticate retained raw/normalized source, empty defines, the exact post
tree, and the compatibility-transform registration; caller-provided hashes
are additional drift alarms, never authority.

Required emitted shape at the site is semantically equivalent to:

```cpp
double j =
    static_cast<double>(i + std::int32_t(2)) -
    static_cast<double>(
        (static_cast<double>(i + std::int32_t(2)) /
         static_cast<double>(n)) *
        static_cast<double>(n));
```

The existing float constructor must then narrow `j` at `float(j)`. Exact
parentheses may follow the emitter's established spelling, but tests must
prove C++ double division/multiply/subtract, `double j`, no integral cast
between them, and no `%`/`glsl::integer_mod` at this declaration. Both library
and tests already compile with `-ffp-contract=off`; removing that option is a
Task 20 failure because contraction can change the separately rounded Number
operations.

## `fixed-affine-centers13-v1` proof contract

The proof runs only after the Star transform and locks the post-transform
function and whole-program hashes above. It owns exactly `fruitMask` signature
40 (`p:vec2@31`, `drawLines:bool@32`), its 12 body statements, and
`centers:vec2[13]@73` at normalized `96:10` / body statement 2.

### Initialization

Native storage is exactly:

```cpp
using Centers13 = std::array<glsl::Vec2, 13>;
static_assert(sizeof(glsl::Vec2) == 8U);
static_assert(sizeof(Centers13) == 104U);
Centers13 centers{};
```

The braces are mandatory. They create 13 distinct zero-valued Vec2 elements
and 26 positive F32 zero lanes before authored writes. Do not emit uninitialized
storage, double lanes, a pointer/span/vector, static/thread-local storage, an
aggregate source initializer, or an array copy.

The proof must authenticate these three exact, ordered, pairwise-disjoint
write regions before any read:

| Role | Typed site | Exact induction/RHS | Dynamic vector writes | Index set |
| --- | --- | --- | ---: | --- |
| center | body[3], `97:5` | `centers[0] = vec2(0.0,0.0)` | 1 | `{0}` |
| inner ring | body[4], `100:9`, `k@74` | `k=0; k<6; k++`; angle `float(k)*PI/3.0`; `2.0*vec2(cos(angle),sin(angle))`; index exactly `1+k` | 6 | `{1..6}` |
| outer ring | body[5], `104:9`, `k@76` | `k=0; k<6; k++`; angle `float(k)*PI/3.0+PI/6.0`; `2.0*SQRT3*vec2(cos(angle),sin(angle))`; index exactly `7+k` | 6 | `{7..12}` |

There are exactly 13 vector stores, every element is written once, no read
precedes completion, and no later write exists. The proof must lock exact AST
operator order and RHS shapes, not merely prove an interval. `k+1`, changed
radii, swapped rings, a phase change, altered literal, missing Vec2
materialization, conditional initializer, overlap, or gap rejects.

Canonical scalar `angle` temporaries remain C++ `double`. Source literals use
the existing F32 values (`PI=3.1415927410125732`,
`SQRT3=1.7320507764816284`, `PI/6=0.5235987901687622`, and
`2*SQRT3=3.464101552963257`), trigonometry consumes Number-compatible scalar
expressions, and assignment materializes both Vec2 lanes through F32 storage.

### Reads, calls, and non-escape

The four static read sites are:

| Site | Span | Induction proof | Dynamic reads |
| --- | --- | --- | ---: |
| `length(centers[i])` | `114:39` | `i@81=0; i<13; i++` | 13 |
| `length(p-centers[i])` | `120:30` | same `i@81` | 13 |
| `lineSegmentSDF(...,centers[i],...)` | `140:46` | outer `i@88=0; i<13; i++` | 78 accepted pairs |
| `lineSegmentSDF(...,...,centers[j])` | `140:58` | inner `j@89=0; j<13; j++` | 78 accepted pairs |

The circle loop has 26 reads. The exact `if (j <= i) continue` visits the full
13x13 grid, rejects 91 diagonal/lower-triangle pairs, accepts 78 `j>i` pairs,
and performs 156 endpoint reads. Metatron therefore performs 182 center reads;
Fruit performs 26. The proof must recursively census every array declaration,
reference, index, store, read, enclosing control, and use. There is no
whole-array use, assignment/copy, parameter pass, return, pointer/reference,
capture, alias, address taking, or escape.

`geometry == 1` reaches `fruitMask(p,false)`; `geometry == 3` reaches
`fruitMask(p,true)`. Other geometry branches do not allocate or touch the
table. This routing and direct-call identity is part of the whole-program lock.

### Validator and emitter boundary

The validator may admit an array-typed base only when its symbol/type/span is
the one proved declaration or one of the seven registered index expressions.
The two affine stores accept only the exact binary ASTs and exact induction
symbols/spans above. Reads accept only the three exact direct induction IDs at
the four spans. Do not add `vec2[13]` to `APPROVED_TYPES`, do not generalize
the fixed-nine proof/store maps, and do not accept arbitrary binary indices.

The emitter should add profile-specific helpers analogous to
`_task20_array()` and `_task20_index()`. Emit extent 13 only from the proof;
use direct `std::array::operator[]` with an explicit `std::size_t` cast around
the proved index result. Do not use `.at()`, pointer arithmetic, a generic
array type table, templates selected by arbitrary extent, exception paths, or
runtime proof lookup. All unregistered array/index shapes must still throw.

Both validator and emitter must:

1. reattach counted-loop and discarded-counter proofs from the typed bodies;
2. clear every attached fixed-array proof, including the Task 20 proof;
3. reconstruct earlier proof layers in the established order;
4. authenticate the exact transformed Sacred Geometry post profile;
5. recompute `fixed-affine-centers13-v1` independently;
6. compare the entire immutable proof object; and
7. reject missing, stale, forged, foreign-key, source-mismatched, or
   attacker-updated proof metadata.

## Counted-loop, stack, and hot-path evidence

The unchanged whole-program counted-loop lock is:

```text
loop_count=9
unproved_loop_count=0
max_effective_depth=2
max_lexical_product=169
entrypoint_charge=207
call_graph_acyclic=true
```

Maximum Metatron work per pixel is `6+6+13+13+169=207` loop
iterations/visits, 13 center writes, 13 circle evaluations, 78 line
evaluations, and 182 center reads. Fruit executes 25 loop iterations, 13
writes, 13 circle evaluations, and 26 reads. Task 20 adds no loop/control
capability and must not raise current trip/depth/product/charge limits.

The centers payload is exactly 104 stack bytes, but that is not the complete
frame. Acceptance must preserve compiler `.su` files from fresh Debug and
Release builds with `-fstack-usage` and report:

- `fruitMask`, `starPolygonMask`, `lineSegmentSDF`, `main`, the pixel lambda,
  and optimizer-generated/inlined clones;
- static versus dynamic classification and exact reported bytes;
- the maximum non-inlined Metatron call-chain sum, or, when Release inlines,
  the containing frame plus code/disassembly evidence; and
- the 104-byte payload separately from total frame size.

ASan and UBSan builds must show no memory, bounds, integer, lifetime, or
alignment failure. Floating `0/0` at the exact proved Star segment is required
canonical behavior; do not enable `-fsanitize=float-divide-by-zero` as a broad
fatal check for the parity run. Do not disable ASan/UBSan generally. The
generated pixel path must contain no allocation, deallocation, virtual call,
callback, `std::function`, map/string/variant lookup, exception, recursion, or
indirect dispatch. Catalog factory lookup at bind time is outside the pixel
hot loop and remains unchanged.

## Frozen external oracle

Artifacts and identities:

- risk audit SHA-256:
  `6798f1459cd6ae512a8bd70ac730684d2b2b2b5389e2d367099d6fad07b85149`;
- generator SHA-256:
  `4e9bead18c312cbf0aa5b3239bb575cfaec3ddd40cb246f3d47e8f3ccd49f75e`;
- oracle JSON SHA-256:
  `1f71fc6fb2f91f0c3b660decda30d533ecca20070bb318cc9757242be3499d03`;
- oracle report SHA-256:
  `02db6d234953dd23b2bea50b02e1c5d25449aefbdd7117e0959be003395b3f30`.

The fixture is 37x23 top-down F32 output with bottom-left fragment
coordinates, tile offset `[5,7]`, full resolution `[53,41]`, aspect
`1.60869562625885f` (`0x3fcde9bd`), frame 11, delta time
`0.01666666753590107f`, seed 23, ordinary time `0.3375000059604645f`, and
Unfold time `0.4124999940395355f`. The JSON carries every uniform F32 word,
nine lane-bit probes, and repeat identity.

Native Debug, Release, ASan, and UBSan runs must match every F32 byte and every
RGBA8 byte for all ten cases:

| Case | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| geometry-0-flower-default-control | `f21a1640b99f9261e057803162a58a10421ef8215e986ac32a5db139772e5fc7` | `5924cef44fee78454a1b0de3ad2d6ee3f6e58a5781d33d6ada23a0f3ebd94695` |
| geometry-1-fruit-animation-off | `53a248d64b3e0ddd6ec1e3b0cb464f0a34a7537b195b6101ae491ed5237527bd` | `65c56e8163f4771fa4b84f9491683b268f3f690244da038aa159017491446418` |
| geometry-3-metatron-animation-off | `a59f25d73a50ea89aaecef886f6716d0160e1daff66e2c2d0d903db4b78a9768` | `1bcedeeb940061ff65ecd623ed9403bc7cb527f0aeb0aa109280d94377365b56` |
| geometry-1-fruit-ripple | `4860d797929366c4653b781be06b0e1ff71e50536bb8ed520451d36696353b97` | `6008029ea08dd02986f54f779201b757973456d8fe110b60c279e8f25ab2ceaf` |
| geometry-3-metatron-unfold | `b230927f646ca19eec5da4afd377b834bcfba868f6ee4ac2c4c9cd2ca704b6d9` | `a8a85901eb46162d910c494f18d1d55ddd6f6c137fc01184e4502d8e6e6e00bf` |
| geometry-4-seed-rotate | `aefe8af6e96a502a31f955c69d048fb0b3ea6509fcb7cbc812fe3a858c17057a` | `fb99a8983f2d2d8e7068a63741090d35687a42fac360e67c3e76398a311ff4cc` |
| geometry-5-vesica-pulse | `0c64d5b84edde6e6c8ef3fb5a69a96c188cd0aa9a4061e27ace4d346d155ef11` | `3eec9bdd7df95c1027b106df8cddf374f7301379d8c19f1c0093d13873fa96cb` |
| geometry-6-borromean-ripple | `0927349a467756276ad2818fad4726061093fbeada54bb67b5441c184948d368` | `0b04d4b45240d9359b1aa049e791321be93f0512c42858d33f4d8460b2d87599` |
| geometry-7-star-animation-off | `2582e12629310c9fbd4781a158fd7f77512709b7b081bfb5ca00f38efde57879` | `0ca995365b120c89a3dbf0f3def90f25c768c1f6af5556f57d15ef2fda197ebe` |
| geometry-8-triquetra-rotate | `6b3b4a906ffa5238c87f3516f92c26f61d8a4e4b51ae0b33db8535ea2946eeaf` | `dad1ab989e22377d728fee5d982a9f1f9186580e5e4227f6c313db218ce52905` |

The Star case is intentionally nonfinite. For each `starPoints=5..12`, every
one of 851 pixels must be exactly RGB qNaN word `0x7fc00000` and alpha
`0x3f800000`; all eight values share the Star hashes above. The generator's
intended-integer-remainder control is finite and must *not* match native. For
`starPoints=7` that rejected control is F32
`0c8a428114ff71c11358e12f90578b72ddb686609a0165caae15b758d5793a54`
and RGBA8
`32a173d00b4f39b2716bf4ea8deb6f8717e8722bf1cec3f43204c74bb50ea988`.

The seven counted factory mutations lock center zero, both affine store
regions, both circle read roles, the nested `centers[j]` line endpoint, and an
inner-ring permutation symmetry stress. Required F32 lane differences are
567/863, 2553/84, 2553/84, 955/117, 330/210, 1431/1755, and 82/110 for their
respective detecting pairs. All six non-array geometry controls stay
byte-identical for array mutations. The permutation changes F32 but not RGBA8,
so RGBA8-only native tests are forbidden. Structural proof, not rendered
symmetry, must reject reordered affine initialization.

## Positive test matrix

### Compatibility and proof construction

- Exact source analyzes, the Star transform reproduces both frozen post hashes,
  the affine proof attaches, validator accepts, and emitter produces C++.
- The transform changes exactly the five listed nodes and preserves every
  other dataclass field/node.
- The proof record contains exact key/profile, source locks, post hashes,
  function/body/symbol identities, all seven index spans, three induction
  identities, the two affine AST profiles, write/read counts, disjoint/complete
  initialization, no-escape flags, 104-byte payload, and loop summary.
- Validator and emitter both accept only after independently clearing and
  recomputing the proof.
- Generated C++ contains `std::array<glsl::Vec2, 13>`, `{}` initialization,
  the 8/104-byte static assertions, exact affine indices, direct induction
  reads, `double angle`, and the exact `double j` Number-division shape.
- Generated manifest records empty defines, `glsl-f32`, the exact transform,
  and exact capability; public catalog contains exactly 116 sorted unique keys.

### Native behavior

- Bind every required scalar/vector uniform at the exact source type and reject
  missing/wrong types; there are no sampler bindings.
- Run all ten frozen cases with exact F32 uniform words, full hashes, probes,
  opacity/nonfinite profiles, orientation, and fresh-surface repeat identity.
- Run the complete `starPoints=5..12` qNaN matrix and explicitly reject the
  finite remainder-control hashes.
- Exercise Fruit off, Metatron off, Ripple, and Unfold as the array-sensitive
  minimum; the remaining six cases prove whole-factory publication.

## Negative and tamper matrix

Every typed-program mutation must be tested at both capability validation and
direct typed emission. Where a forged attacker can update or clear attached
proof fields, test retained proof, cleared proof, and attacker-replaced proof.

| Category | Mutations that must reject |
| --- | --- |
| identity/provenance | wrong key; raw/normalized digest; nonempty or altered defines; wrong numeric contract; factory/source manifest identity; binding order/type/symbol ID; resource/output/interface drift; function/body count; pre/post function or whole-program hash |
| transform registration | missing transform; wrong name; transform on another key; duplicate/extra transform; untransformed, partially transformed, already transformed, or twice transformed tree |
| Star site | wrong function/signature/body path/span; `i/n/j` ID/name/type drift; `/`, `*`, or `-` changed/reordered; literal 2 changed; a cast inserted/removed; another division rewritten; declaration or `float(j)` read omitted/duplicated; `j` narrowed to int; `%`/integer_mod; geometry-7 shortcut; hard-coded NaN; contracted arithmetic or removed `-ffp-contract=off` |
| declaration/storage | array name, symbol, function, statement index, element, extent, storage class, initializer form/order, or positive-zero initialization drift; missing braces; aggregate source initializer |
| affine stores | missing/duplicate center store; `2+k`, `6+k`, `8+k`, or `k+1`; loop start/bound/comparison/update drift; different induction ID; conditional, continue, break, return, or second write; overlap/gap; reordered store regions |
| RHS/precision | radius, phase, PI/SQRT3/literal/operator drift; float `angle`; double center lanes; removed Vec2/F32 materialization; swapped cos/sin or ring RHS |
| reads/control | early read; post-init write; affine/literal/unproved/out-of-range read; changed span/induction; missing/duplicated circle site; `centers[j] -> centers[i]`; changed nested bounds; changed `j<=i` guard/continue; lost/extra accepted pair; call target/order drift |
| ownership/escape | whole-array read/write/copy; parameter pass; return; address/reference/pointer/span; capture; alias; static/global/thread-local/heap storage; recursion |
| exclusions | any other key, extent, element, array profile, generic binary index, multidimensional/nested/struct array, array parameter/return, `out`/`inout`, sampler/texture, derivative, varying, block, matrix, packed word, resource ABI, or unrelated compatibility transform |
| generated/native | `.at()`, exception path, allocation, virtual/indirect hot-loop call, dynamic stack frame, missing static assertion, finite Star output, RGBA8-only acceptance, wrong catalog/count, or changed unrelated generated body |

Mutation helpers must locate nodes by full structural identity and assert one
exact replacement. Tests that merely change a source string without proving
the intended typed node changed are inadequate.

## Implementation order and review gates

- [ ] Add failing transform tests for all pre/post locks and site tampering;
  implement only the exact five-node rewrite; rerun the focused tests.
- [ ] Add immutable Task 20 proof records and failing positive/negative proof
  tests; implement full recursive proof recomputation; rerun both-boundary
  tamper tests.
- [ ] Add validator census/allowlist plumbing; prove only the exact declaration
  and seven indices pass while all generic-array cases remain rejected.
- [ ] Add emitter proof validation and exact stack/index/Number code shape;
  inspect emitted Sacred Geometry and run code-shape assertions.
- [ ] Add the slice entry/transform/capability and regenerate the three owned
  outputs; assert 114 typed / 116 public / 96 unported.
- [ ] Add all ten native cases and the eight-value Star matrix; run Debug and
  Release parity before any broader suite.
- [ ] Run ASan/UBSan, allocation/dispatch/code-shape inspection, and Debug/
  Release stack measurement; preserve logs and `.su` evidence.
- [ ] Run the complete generator, corpus, Python, CTest, prior-oracle, and Task
  20 oracle gates; independently review scope and proof before declaring Task
  20 accepted.

## Verification commands and acceptance evidence

Use fresh external build directories so repository outputs remain limited to
the three generator-owned files. Exact compiler flags may be expressed through
the environment or CMake cache, but must retain the project's
`-ffp-contract=off`.

```sh
python3 tools/glslcpp/check_corpus.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/glslcpp/generate_typed_slice.py --check
node docs/port-engineering/task-20-oracle-generator.mjs --check

cmake -S . -B /tmp/noisemaker-task20-debug -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fstack-usage'
cmake --build /tmp/noisemaker-task20-debug --parallel
ctest --test-dir /tmp/noisemaker-task20-debug --output-on-failure

cmake -S . -B /tmp/noisemaker-task20-release -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS='-fstack-usage'
cmake --build /tmp/noisemaker-task20-release --parallel
ctest --test-dir /tmp/noisemaker-task20-release --output-on-failure

cmake -S . -B /tmp/noisemaker-task20-sanitize -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fsanitize=address,undefined -fno-omit-frame-pointer -fstack-usage' \
  -DCMAKE_EXE_LINKER_FLAGS='-fsanitize=address,undefined'
cmake --build /tmp/noisemaker-task20-sanitize --parallel
ctest --test-dir /tmp/noisemaker-task20-sanitize --output-on-failure
```

Acceptance evidence must include fresh command output, zero failed tests, exact
generator `--check`, direct native Debug/Release F32 and RGBA8 hashes, the
Star qNaN words for all `starPoints=5..12`, sanitizer output, `.su` frame
records, generated code-shape excerpts, allocation/dispatch inspection,
catalog/count assertions, and confirmation that unrelated generated factory
bodies are unchanged. Workflow success without these runtime and structural
artifacts is not Task 20 completion.

## Explicit exclusions

Task 20 does not establish generic local arrays, generic affine arithmetic,
generic Number semantics for GLSL integer locals, general integer-division
rewriting, NaN injection, array ABI, array parameters/returns, aliasing,
dynamic storage, or any resource/stage capability. It does not authorize CRT,
Degauss, another Sacred Geometry source variant, another fixed extent, or
another compatibility transform. If either frozen post hash or any canonical
F32 hash cannot be reproduced, stop and diagnose; do not broaden this profile.

This document is a frozen implementation contract only. It contains no
implementation authorization.
