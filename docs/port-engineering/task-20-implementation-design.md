# Task 20 Sacred Geometry implementation design

> **Implementation status:** design only. This document authorizes no Git
> operation. Implement in the existing checkout, preserve unrelated work, and
> stop at each review gate below. The approved brief remains normative if this
> design accidentally paraphrases a lock imprecisely.

## Outcome and non-negotiable boundary

Add exactly `synth/sacredGeometry:sacredGeometry` to the typed CPU slice. The
implementation consists of two independent, fail-closed exceptions:

1. `sacred-star-number-division-v1` rewrites exactly five typed nodes at the
   one authenticated `starPolygonMask` arithmetic site so the C++ emitter
   preserves JavaScript Number division, multiplication, and subtraction.
2. `fixed-affine-centers13-v1` proves and lowers exactly the local
   `fruitMask` `vec2[13]` table, its three initialization regions, and its four
   read contexts/seven index-expression sites.

Do not generalize either exception. In particular, do not add `vec2[13]` to
the ambient approved-type set, do not add generic arrays or affine indexing,
do not change global integer-division semantics, and do not edit the runtime,
CMake, source corpus, public binding types, or any unrelated generated body.
The external canonical JavaScript checkout is oracle provenance only and must
not become a build dependency.

The accepted final projection is 114 typed factories, 116 sorted unique public
factories, 96 publicly unported factories, and an unchanged 212-program corpus.

## Frozen starting inputs

Before editing, authenticate the approved artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `task-20-brief.md` | `65dcd5a522234a8c024edaafe7b942e678c5c0f2c643a260543547380c545ab5` |
| `task-20-risk-audit.md` | `6798f1459cd6ae512a8bd70ac730684d2b2b2b5389e2d367099d6fad07b85149` |
| `task-20-oracle-generator.mjs` | `4e9bead18c312cbf0aa5b3239bb575cfaec3ddd40cb246f3d47e8f3ccd49f75e` |
| `task-20-oracles.json` | `1f71fc6fb2f91f0c3b660decda30d533ecca20070bb318cc9757242be3499d03` |
| `task-20-oracle-report.md` | `02db6d234953dd23b2bea50b02e1c5d25449aefbdd7117e0959be003395b3f30` |
| `task-20-scope-proof-review.md` | `4c2f2fd8e5eb50bf483538fbc7bb8aa7adae9ef64f891d368e2ba9927a503297` |

Authenticate the repository baseline as a drift alarm before implementation:

| File | Baseline SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/typed_ir.py` | `5182d170c230f273f332d1abe1e333a39d3511016a3d2bbf7d63a886dd38ffdb` |
| `tools/glslcpp/generate_typed_slice.py` | `f571f48592932352c6d3164e496851ad8a8084e50044bc1994c81a4cf6a7f493` |
| `tools/glslcpp/emit_typed_cpp.py` | `05d69d2f43894c57b13040c0db29e4f507f3fa3dae575cee0d263a8f3df95222` |
| `tools/glslcpp/typed_slice.json` | `7c4180c73fc0afd15b4f879115f2ab963605a95b165b065d0dfc28cf7167c800` |
| `tests/test_typed_generator.py` | `a84a807593f8a8d9e424ecb57f5c629497d454482d96ed14f143e36a96f51fa3` |
| `tests/test_typed_slice.cpp` | `9a6a323c12ad652fb056a24c95b007c6ece9336de4a44388448067176d5d725a` |
| `tests/test_generated_kernels.cpp` | `31da5ef4151d2919cf1694db1b125f84df01ed9a9b69d8f809a1d6e14e3228ab` |
| `src/typed_generated/typed_slice.cpp` | `96ff2647e44fe3d13a8c4e49161c3c1b1b55f00005063186d641bec46da8559b` |
| `src/typed_generated/typed_manifest.json` | `2cd0c5b012de594317719b04b8b8337517aad75953d0d5b54d2804eb9467a543` |
| `include/noisemaker/generated/catalog.hpp` | `e2cebba621536551273af01e3d77f400229dad5c7fcafb42da86cef8abb4083b` |

If any approved artifact differs, stop. If a repository file differs, inspect
and preserve the user change; do not overwrite or silently rebase this design
onto it.

## Exact owned files

Create:

- `tools/glslcpp/frontend/sacred_geometry_compatibility.py`
- `tools/glslcpp/frontend/fixed_affine_centers13_proof.py`

Modify:

- `tools/glslcpp/frontend/typed_ir.py`
- `tools/glslcpp/generate_typed_slice.py`
- `tools/glslcpp/emit_typed_cpp.py`
- `tools/glslcpp/typed_slice.json`
- `tests/test_typed_generator.py`
- `tests/test_typed_slice.cpp`
- `tests/test_generated_kernels.cpp`

Regenerate, through `generate_typed_slice.py --write` only:

- `src/typed_generated/typed_slice.cpp`
- `src/typed_generated/typed_manifest.json`
- `include/noisemaker/generated/catalog.hpp`

No other repository file is owned by Task 20. `semantic.py`, `CMakeLists.txt`,
`glsl_types.hpp`, `glsl_runtime.hpp`, numeric helpers, and corpus sources must
remain byte-identical.

## IR additions

In `tools/glslcpp/frontend/typed_ir.py`, add frozen records whose fields carry
facts, not authority. Follow the existing immutable proof-record conventions.

### Compatibility-site record

Add `SacredStarNumberDivisionSiteProof` with fields sufficient for exact
comparison and diagnostics:

- transform name;
- function signature ID 46;
- induction `i@106`, divisor `n@37`, and local `j@107` symbol identities;
- declaration span `260:13-44`;
- division span `260:29-39`;
- multiplication span `260:29-44`;
- subtraction span `260:18-44`;
- consumption span `262:30-31`;
- pre/post function hashes and pre/post whole-program hashes.

### Affine-table records

Add `FixedAffineStoreRegionProof` with role, statement/body index, statement
and loop spans, optional induction symbol, loop start/bound/comparison/update,
trip count, index span/profile, lower/upper written index, write count, and RHS
span/profile.

Add `FixedAffineReadSiteProof` with role, index span/profile, induction symbol,
owning loop/control span, dynamic read count, and enclosing-expression profile.

Add `FixedAffineCenters13Proof` containing:

- proof kind, key, source and numeric profile;
- raw, normalized, canonical-factory, canonical-runtime, interface,
  transformed-function, and transformed-whole-program locks;
- exact defines, resources, bindings, output symbol, and route;
- the compatibility-site proof;
- `fruitMask` and `main` identities and authenticated body/control profiles;
- `centers@73`, `vec2[13]`, extent 13, native alias `Centers13`, declaration
  body index 2 and span `96:10`;
- the center store, inner store region, outer store region, and all four read
  contexts/seven index sites;
- direct call routing and `drawLines` guard facts;
- recursive declaration/reference/index/write/read counts;
- initialization completeness, pairwise disjointness, dominance, no post-read
  writes, no alias/copy/escape/address/return/parameter/capture facts;
- loop census 9 proved/0 unproved/depth 2/product 169/charge 207/acyclic;
- 104-byte table payload and exact dynamic work counts.

Add only `fixed_affine_centers13_proof: FixedAffineCenters13Proof | None` to
`TypedProgram`. Do not add a general feature flag or a reusable array registry.
The frozen recursive census is one array declaration, eight array-typed
expressions total (the declaration plus seven base identifiers), seven base
identifier expressions, seven index expressions, three static store sites / 13
dynamic vector stores, and four static read sites / 182 maximum dynamic reads
(26 circle reads plus 156 accepted-line endpoint reads).

## Source-locked compatibility transform

Create `tools/glslcpp/frontend/sacred_geometry_compatibility.py`. Export the
exact transform name, Sacred key, source identities, pre/post locks, a
whole-program fingerprint helper, and
`apply_sacred_star_number_division(program) -> TypedProgram`.

The function must first reject any wrong key/source/raw bytes/normalized
source/defines/interface/function identity. It must require:

- raw source: 9710 bytes,
  `24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de`;
- normalized source:
  `6b3c4e8492a69969f3d6f78689cfd19de846656fd0c6d5c8dfd5a758427c61d3`;
- pre-function hash:
  `261327d6c1700f71cef056020358ba1ea4dd56c1e8d1017f545df805a4f9b1d8`;
- pre-whole hash:
  `2dda5c4f3931965da85ac54fca2b6e4748cb2cb1ca61b03316f750c2f6754388`.

Before checking either pre hash, require every top-level fixed-array proof
carrier to be `None`: Task 17 `fixed_nine_table_proof`, Task 18
`fixed_grid_counter_store_proof`, Task 19
`fixed_array_in_parameter_proof`, and Task 20
`fixed_affine_centers13_proof`. A foreign, stale, or forged carried proof is a
transform input error even though these fields are intentionally absent from
the frozen transform hashes. Do not clear them inside the transform and then
continue; reject the caller.

Locate by structural walk, never by textual substitution. Require one and only
one complete match in `starPolygonMask` signature 46:

```glsl
int j = (i + 2) - ((i + 2) / n) * n;
```

Use immutable dataclass replacement to change only these typed nodes from
`int` to `float`: division `260:29-39`, multiplication `260:29-44`, root
subtraction `260:18-44`, declaration expression plus attached `j@107` symbol
`260:13-44`, and the sole later identifier expression plus attached `j@107`
symbol at `262:30-31`. Assert every other dataclass field and every other node
is equal before/after. Reject zero, duplicate, already transformed, partially
transformed, or extra matches.

After replacement require:

- post-function hash:
  `fdaf48f945303bfe83c56ee0e2e75ae62d418904c02fc2bc6621fc0da907f7b2`;
- post-whole hash:
  `de499dea91a59d8fc5ec4591be30a9b4350bb6a9e0317259aa97e8d3e3586ee0`.

The output proof record is descriptive. The hard-coded key, source, structure,
and hashes are the authority. The transform must never emit `%`,
`integer_mod`, casts back to integral arithmetic, a `geometry == 7` shortcut,
an `isnan` branch, or a hard-coded NaN.

Also export a nonmutating post-transform authenticator. Validator and emitter
use this authenticator to require the exact post tree and post hashes; they
must not call the pre-to-post transform again on an already transformed tree.

## Independent affine-table proof

Create `tools/glslcpp/frontend/fixed_affine_centers13_proof.py`. Export the
exact capability, key/profile/source/canonical locks,
`source_provenance_error`, `prove_fixed_affine_centers13`, and
`attach_fixed_affine_centers13_proof`.

Proof runs after the compatibility transform. First authenticate empty defines,
no resources, exact 17 uniforms plus `fragColor@18`, route, transformed hashes,
and exact ordered bindings. Use the independently frozen transformed-tree
profiles as drift alarms, including interface fingerprint
`de898c81d54e1aa67052f551b953dca47e46b8b8aca66ca179408948b9ec8770`.

Recompute, recursively, all of the following rather than trusting an attached
proof:

- `fruitMask` signature 40, parameters `p:vec2@31` and
  `drawLines:bool@32`, exactly 12 body statements;
- exactly one array object, local `centers:vec2[13]@73`, declaration body
  index 2 at normalized `96:10`;
- exactly seven array index expressions and no alternate array access form;
- body 3 writes `centers[0]` at `97:5` exactly once with the exact center RHS;
- body 4 is `k@74 = 0; k < 6; k++`, six trips, writing `centers[1+k]`
  at `100:9`, indices 1..6, with the exact inner-ring RHS;
- body 5 is `k@76 = 0; k < 6; k++`, six trips, writing `centers[7+k]`
  at `104:9`, indices 7..12, with the exact outer-ring RHS;
- the three write sets are disjoint, cover 0..12 exactly once, dominate all
  reads, and no later write occurs;
- circle reads at `114:39` and `120:30` use `i@81`, 13 each;
- line reads at `140:46` and `140:58` use `i@88` and `j@89`, 78 each;
- the line grid is 13 by 13, `j <= i` rejects 91 pairs and accepts 78;
- Fruit reads 26 centers, Metatron reads 182 and evaluates 78 lines;
- no array copy, alias, parameter passage, return, address-taking, capture,
  escape, conditional initialization, dynamic extent, or second owner exists;
- all direct callers and the `drawLines` routing are exact;
- counted-loop proof is nine loops, zero unproved, effective depth two,
  lexical product 169, entrypoint charge 207, acyclic call graph.
- the exact static/dynamic census: declaration 1; array-typed expressions 8;
  base identifiers 7; index expressions 7; store sites 3 / dynamic stores 13;
  read sites 4 / maximum Metatron dynamic reads 182, decomposed as 26 circle
  plus 156 line-endpoint reads.

Store the exact RHS and enclosing-expression fingerprints in the proof so a
permutation or mathematically equivalent rewrite is rejected. The proof must
distinguish the 104-byte raw table payload from the total compiled stack frame.

## Generator registration and validation

In `tools/glslcpp/generate_typed_slice.py`:

1. Import both new modules in the absolute and relative import branches.
2. Add exactly `fixed-affine-centers13-v1` to `APPROVED_CAPABILITIES`; exclude
   it from the ordinary built-in capability set so only its dedicated proof
   can authorize it.
3. Register exactly `sacred-star-number-division-v1` in the compatibility
   transform dispatch. For Sacred, catch proof/transform `ValueError` and
   surface `GeneratorError` with the failing lock/site.
4. Add the Sacred program to the slice loader and change only the locked typed
   count and success message from 113 to 114.
5. Extend the validator boundary to carry both schema metadata values
   explicitly:

```python
validate_capabilities(
    typed,
    declared,
    *,
    source_hash: str | None = None,
    compatibility_transform: str | None = None,
    numeric_literal_contract: str = "glsl-f32",
) -> None
```

   For Sacred, require the transform carrier to equal
   `sacred-star-number-division-v1` and the numeric carrier to equal
   `glsl-f32`; missing, `None`, `"none"`, swapped, or foreign values reject.
   For non-Sacred programs preserve the established schema behavior and reject
   a Sacred transform/capability carrier.
6. In output generation, read both carriers from the authenticated slice entry
   before transformation, then execute exactly: analyze; require all Task
   17/18/19/20 top-level proof fields absent; apply the Sacred transform once;
   rebuild Task 17; rebuild Task 18 using the Task 17 result; rebuild Task 19
   using the Task 18 result; attach Task 20 using the Task 19 result; validate;
   emit. Pass `source_hash`, `compatibility_transform`, and
   `numeric_literal_contract` by explicit keyword into both boundaries.
7. In `validate_capabilities`, do not reapply the compatibility transform. It
   receives the post-transform tree and authenticates that exact tree with the
   nonmutating post authenticator and both explicit metadata carriers. For
   proof reconstruction, first reattach counted-loop and discarded-counter
   facts from bodies, clear all four top-level Task 17/18/19/20 proof fields in
   one `dataclasses.replace`, then rebuild and attach Task 17 -> Task 18 -> Task
   19 -> Task 20 in that exact order. Compare each caller-carried proof field
   against its independently rebuilt value and reject a nonapplicable foreign
   proof. Never accept caller hashes or an attached proof alone.
8. Extend declaration, lvalue, rvalue, and recursive-census checks only for the
   one proved `centers@73` declaration and its seven exact index spans. Any
   other `vec2[13]`, extent, symbol, span, affine form, or function is rejected.

In `tools/glslcpp/typed_slice.json`, add one sorted program entry between
`synth/polygon:polygon` and `synth/subdivide:subdivide` with exactly empty
defines, the one capability, and the one compatibility transform. Do not
change any existing entry.

## Emitter authorization and lowering

In `tools/glslcpp/emit_typed_cpp.py`:

1. Import the transform/proof modules in both supported import modes.
2. Add `compatibility_transform: str | None` beside the existing
   `numeric_literal_contract` carrier on `_Emitter`, and extend
   `render_typed_cpp` to accept both as explicit keyword metadata:

```python
render_typed_cpp(
    program,
    program_key,
    source_hash,
    namespace="typed_kernel",
    factory="bind_typed",
    *,
    numeric_literal_contract: str = "glsl-f32",
    compatibility_transform: str | None = None,
) -> str
```

   Update existing source-double positional callers to use the named argument.
   Every generator call passes both values. For Sacred, initialization requires
   exactly `sacred-star-number-division-v1` and `glsl-f32`; direct callers that
   omit, clear, swap, or forge either carrier reject.
3. In emitter initialization, do not reapply the transform. Independently run
   the nonmutating post-transform authenticator, reattach counted-loop and
   discarded-counter facts, clear all Task 17/18/19/20 proof fields, rebuild
   and attach Task 17 -> Task 18 -> Task 19 -> Task 20 in exact order, and
   compare every original proof field with the rebuilt object. Reject every
   nonapplicable/foreign proof. This must be independent of generator
   validation so a direct emitter caller cannot bypass it.
4. Add `_task20_array` and `_task20_index` helpers. They return authorization
   only when key, function, symbol, span, role, and complete proof match.
5. Consult `_task20_index` before generic array rejection in both lvalue and
   rvalue emission. Keep every nonregistered index on the existing rejection
   path.
6. For the one declaration emit:

```cpp
using Centers13 = std::array<glsl::Vec2, 13>;
static_assert(sizeof(glsl::Vec2) == 8U);
static_assert(sizeof(Centers13) == 104U);
Centers13 centers{};
```

   Place the alias/static assertions in the generated Sacred namespace and
   use direct `std::array::operator[]` with an explicit `std::size_t` cast of
   the proved index at the seven sites. Do not add allocation, runtime lookup,
   bounds-policy objects, callbacks, virtual dispatch, exceptions, or dynamic
   stack storage.
7. Rely on existing float lowering for the transformed Star expression:
   `double j`, `static_cast<double>` around the division operands and its
   float-typed parents, and the existing authored `float(j)` F32 narrowing.
   Add no special emitter shortcut for Star output.

Code-shape tests must assert double divide/multiply/subtract with no integral
cast between them, no `%` or `glsl::integer_mod` at the declaration, and
`-ffp-contract=off` remains effective in all native verification builds.

## Test-first execution sequence and review gates

### 1. Compatibility transform

Add failing Python tests first:

- `test_sacred_star_number_division_transform_is_exact_and_source_locked`
- `test_sacred_star_number_division_transform_rejects_partial_duplicate_and_drift`

Implement the transform until those tests pass. Inspect the exact five-node
diff and both post hashes. **Review gate 1:** do not start array lowering until
an independent reviewer confirms the five-node-only transform and emitted
double arithmetic shape.

### 2. Affine proof and IR

Add failing tests:

- `test_sacred_fixed_affine_centers13_proof_is_exact`
- `test_sacred_fixed_affine_centers13_proof_rejects_structural_drift`

Implement records and proof reconstruction. Require exact write regions,
RHS profiles, seven sites, census, dominance, call routing, and work counts.
**Review gate 2:** independently inspect proof completeness and confirm no
ambient type/index permission was introduced.

### 3. Validator and emitter

Add failing direct-validator and direct-emitter tests:

- `test_sacred_fixed_affine_centers13_validates_and_emits_only_proved_sites`
- `test_sacred_task20_tampering_rejects_at_both_boundaries`
- `test_sacred_task20_exclusions_remain_closed`

Wire registration, independent proof reconstruction, declaration lowering,
and exact lvalue/rvalue authorization. Assert generated code shape and that a
cleared, stale, or attacker-replaced proof fails when any structure differs.
For both boundary APIs, run four explicit modes: (1) the authentic transformed
program with exact proof chain and exact metadata carriers accepts; (2) the
same program with any required proof field cleared rejects; (3) a structurally
mutated program retaining the authentic proof chain rejects as stale; and (4)
the mutation with attacker-updated exposed hashes/proof records rejects from
hard-coded provenance and independently recomputed structure. Repeat carrier
omission/forgery in all applicable modes.

### 4. Slice and generated outputs

Add the sorted JSON entry, update exact locks to 114/116/96, run the generator
in check mode to observe the expected drift, then run `--write`. Confirm only
the three owned generated outputs changed. Compare all non-Sacred generated
factory bodies byte-for-byte against their starting versions.

### 5. Native bindings, catalog, and parity

In `tests/test_generated_kernels.cpp`, assert the exact 17-input order/types,
`fragColor@18`, no resources, successful exact binding, and missing/wrong-type
rejection. Update the exact sorted catalog to 116 and assert Sacred occurs once
while adjacent excluded keys remain absent.

In `tests/test_typed_slice.cpp`, add a native Sacred fixture that consumes the
frozen JSON oracle. Run all ten 37x23 cases and compare full top-down F32 words,
RGBA8 bytes, probes, opaque alpha, nonfinite profiles, and fresh-surface repeat
identity. Run `starPoints=5..12` and require every one of 851 pixels to have RGB
`0x7fc00000` and alpha `0x3f800000`. Keep the finite intended-remainder control
as a test-only discriminator. **Review gate 3:** inspect native parity, binding
ABI, generated diff, and code shape before full acceptance.

## Literal negative/tamper matrix

For every mutation below, exercise both generator validation and direct
emitter construction in four modes: authentic unmodified control (accept),
required proof cleared (reject), mutated tree with retained authentic proof
(stale, reject), and mutated tree with attacker-updated exposed hashes/proof
objects (reject). Every mutation row must show both boundaries rejected before
C++ generation or compilation unless it is explicitly a generated-code
inspection case.

### Provenance, registration, and interface

- wrong key, source path, raw byte, normalized source, raw/normalized hash;
- canonical factory identity/text hash drift; canonical generated-runtime hash
  drift; transformed function count, target-function body count, or any other
  authenticated function/body-count drift;
- nonempty defines; added resource/sampler/global/varying/derivative;
- reordered, missing, duplicated, renamed, retyped, or renumbered binding;
- wrong output symbol, location, logical route, or compatibility-transform name;
- missing, duplicate, wrong, or additional capability;
- missing, `None`, `"none"`, wrong, swapped, or Sacred-on-foreign-key
  `compatibility_transform` carrier; missing/wrong/source-double
  `numeric_literal_contract` carrier; manifest/schema value differing from the
  value delivered to validator or emitter;
- stale pre/post function or whole-program profile, including an attacker
  updating only caller-visible hashes.

### Five-node transform

- missing site; duplicated site; second integral division; pre-transformed or
  partially transformed tree; shifted span;
- missing transform, duplicate transform registration, extra transform,
  transform applied to another key, already/twice-transformed input, or Sacred
  combined with any unrelated compatibility transform;
- any pre-transform Task 17/18/19/20 proof field non-`None`, individually and
  in combinations; any attempt to clear a carried proof silently and continue;
- wrong function/signature or `i@106`, `n@37`, `j@107` identity;
- changed operator, literal 2, child order, declaration ancestry, later read,
  constructor, symbol category/storage/writability, or extra typed node;
- transform only `/`, omit a parent, omit declaration symbol, omit later read,
  transform an extra node, use `%`/`integer_mod`, use F32 arithmetic early,
  insert an integral cast, shortcut geometry 7, branch on NaN, or hard-code NaN.

### Declaration and initialization

- another array object, different element type/extent/storage/function/body
  index/span, uninitialized spelling, dynamic allocation, or alias/copy/escape;
- remove/change/reorder/conditionalize any of the three store regions;
- center index not 0; inner/outer loop start, bound, comparator, increment,
  trip count, induction symbol, or region order changed;
- replace either affine index with `2+k`, `6+k`, `8+k`, `k+1`, or `k+7`;
  overlap, gap, duplicate write, incomplete initialization, or a post-read
  write;
- insert `continue`, `break`, `return`, a conditional around a store, or a
  second write in either initializer loop;
- swap rings; change radius/phase/operator/literal/builtin/Vec2 construction;
  exchange equivalent/symmetry-related RHS expressions.
- lower `angle` as float, store double center lanes, remove the Vec2/F32
  materialization boundary, or swap the `cos`/`sin` operands.

### Reads, control, ownership, and work

- missing/additional/reordered index site; different index expression, symbol,
  span, owning loop, enclosing expression, or use count;
- early read before complete initialization; literal, affine, unproved, or
  out-of-range read; a proved index moved to a different use or control region;
- altered circle loop bounds/body; altered 13x13 grid; change/remove/invert
  `j <= i`; move a read across the guard;
- pass, return, capture, take address of, assign, copy, or store a reference to
  `centers`; use it in another function or call;
- introduce pointer/span access, a whole-array expression/copy, or change the
  local automatic object to static, global, or thread-local storage;
- changed direct-call routing or `drawLines` behavior;
- any loop count/depth/product/charge/call-cycle drift.
- census drift in any individual dimension: declaration `1`, array-typed
  expressions `8`, base identifiers `7`, indices `7`, store sites `3`, dynamic
  stores `13`, read sites `4`, circle reads `26`, line reads `156`, or maximum
  Metatron reads `182`; specifically reject a correct static-site census paired
  with an incorrect dynamic count and the converse.

### Proof-chain forgeries

- clear, retain stale, substitute foreign-key, or forge Task 17
  `fixed_nine_table_proof` while Tasks 18-20 appear authentic;
- do the same independently for Task 18 `fixed_grid_counter_store_proof`, Task
  19 `fixed_array_in_parameter_proof`, and Task 20
  `fixed_affine_centers13_proof`;
- attach a later proof to an earlier reconstruction stage, rebuild out of order,
  omit a predecessor, preserve a proof across structural replacement, or make
  only the nested Task 20 copy agree while its top-level predecessor differs;
- attacker updates every exposed proof/hash field after source, interface,
  transform-node, table, control, or use-site mutation; the hard-coded source,
  post-transform, and structural recomputation must still reject.

### Closed-world exclusions and generated shape

- unrelated program requests `fixed-affine-centers13-v1`;
- Sacred variant or neighbor key; other array extent/type; generic affine
  subscript; a second fixed13 declaration; CRT, Degauss, or adjacent synth key;
- multidimensional, nested, or struct-contained array; array parameter or
  return; `out`/`inout` array; pointer/span facade; texture/sampler, block,
  matrix, packed-word, or resource-ABI capability; any unrelated compatibility
  transform;
- generated hot path contains heap allocation/deallocation, `std::function`,
  string/map/variant lookup, virtual/indirect call, callback, exception,
  recursion, VLA/dynamic alloca, `%`, `integer_mod`, geometry/NaN shortcut, or
  an integral cast in the Star Number chain.
- generated Sacred code uses `.at()`, omits either size static assertion,
  produces finite Star output, accepts RGBA8-only parity, publishes the wrong
  catalog/order/counts, or changes any unrelated generated factory body.

Keep the seven canonical factory mutations as rendered sensitivity tests. The
expected detecting-pair F32/RGBA8 lane differences are respectively
`567/863`, `2553/84`, `2553/84`, `955/117`, `330/210`, `1431/1755`, and
`82/110`; the last mutation intentionally has zero RGBA8-byte differences in
its designated control, so full-F32 comparison is mandatory.

## Verification commands

Run from `.`. Use fresh build trees
under `/tmp`; do not invoke Git.

```sh
shasum -a 256 \
  docs/port-engineering/task-20-brief.md \
  docs/port-engineering/task-20-risk-audit.md \
  docs/port-engineering/task-20-oracle-generator.mjs \
  docs/port-engineering/task-20-oracles.json \
  docs/port-engineering/task-20-oracle-report.md \
  docs/port-engineering/task-20-scope-proof-review.md
node docs/port-engineering/task-20-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_sacred_star_number_division_transform_is_exact_and_source_locked \
  tests.test_typed_generator.TypedGeneratorTests.test_sacred_fixed_affine_centers13_proof_is_exact \
  tests.test_typed_generator.TypedGeneratorTests.test_sacred_fixed_affine_centers13_validates_and_emits_only_proved_sites \
  tests.test_typed_generator.TypedGeneratorTests.test_sacred_task20_tampering_rejects_at_both_boundaries \
  tests.test_typed_generator.TypedGeneratorTests.test_sacred_task20_exclusions_remain_closed
python3 -m unittest discover -s tests -p 'test_*.py'
```

Also rerun every prior frozen oracle generator/check from Tasks 15 through 19
using its documented command, plus existing semantic and drift checks. Do not
infer their filenames if the repository documentation differs.

Configure fresh native builds; adapt generator only if the host does not
support Ninja:

```sh
cmake -S . -B /tmp/noisemaker-task20-debug -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fstack-usage -fstack-size-section -ffp-contract=off'
cmake --build /tmp/noisemaker-task20-debug
ctest --test-dir /tmp/noisemaker-task20-debug --output-on-failure

cmake -S . -B /tmp/noisemaker-task20-release -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS='-fstack-usage -fstack-size-section -ffp-contract=off'
cmake --build /tmp/noisemaker-task20-release
ctest --test-dir /tmp/noisemaker-task20-release --output-on-failure

cmake -S . -B /tmp/noisemaker-task20-sanitize -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fsanitize=address,undefined -fno-omit-frame-pointer -fstack-usage -fstack-size-section -ffp-contract=off' \
  -DCMAKE_EXE_LINKER_FLAGS='-fsanitize=address,undefined'
cmake --build /tmp/noisemaker-task20-sanitize
ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
  ctest --test-dir /tmp/noisemaker-task20-sanitize --output-on-failure
```

The intentional floating `0/0` must remain allowed; do not enable a sanitizer
mode that makes canonical IEEE floating divide-by-zero fatal. Do not suppress
integer, bounds, address, or undefined-behavior findings.

Inspect generated and object code:

```sh
awk '
  $0 == "// Typed IR program: synth/sacredGeometry:sacredGeometry" { sacred = 1 }
  sacred && /^namespace typed_[0-9]+ \{/ { body = 1 }
  body { print }
  body && /^}  \/\/ namespace typed_[0-9]+$/ { exit }
' src/typed_generated/typed_slice.cpp > /tmp/task20-sacred-namespace.cpp
test -s /tmp/task20-sacred-namespace.cpp
test "$(rg -c '^namespace typed_[0-9]+ \{$' /tmp/task20-sacred-namespace.cpp)" = 1
rg -n -C 12 'Centers13|double j|starPolygonMask|fruitMask' /tmp/task20-sacred-namespace.cpp
if rg -n 'operator new|operator delete|malloc|free|std::function|std::map|std::unordered_map|std::variant|std::string|throw|alloca|integer_mod|\.at\(' /tmp/task20-sacred-namespace.cpp; then
  echo 'forbidden construct in Sacred namespace' >&2
  exit 1
fi
find /tmp/noisemaker-task20-debug /tmp/noisemaker-task20-release /tmp/noisemaker-task20-sanitize -name '*.su' -print
rg -n 'fruitMask|starPolygonMask|lineSegmentSDF|sacredGeometry|operator\(\)' /tmp/noisemaker-task20-{debug,release,sanitize} -g '*.su'
```

The first `awk` command must produce exactly one Sacred namespace and no binder
or neighboring factory. Code-shape tests should use brace-balanced extraction
for the exact `fruitMask`, `starPolygonMask`, `lineSegmentSDF`, `main`, and
`pixel` definitions and run hot-loop forbidden-pattern assertions only on
those extracted bodies. Do not scan the whole generated translation unit for
Task 20 forbidden patterns: other authenticated factories and bind-time code
are outside this profile. Verify unrelated body drift separately by comparing
each non-Sacred generated factory body with its frozen baseline.

Use `llvm-objdump -d` or `otool -tvV` on the produced object/executable to
confirm Release inlining/call shape and the absence of allocator/indirect-call
paths in the Sacred pixel loop. Record compiler-reported static frame sizes for
`fruitMask`, `starPolygonMask`, `lineSegmentSDF`, `main`, the pixel lambda, and
optimizer clones. Bound the maximum non-inlined chain from reported frames, or
document Release inlining with disassembly. The 104-byte `Centers13` payload is
not the total frame-size bound. Any dynamic/unbounded stack classification is
a failure.

## Completion evidence

Task 20 is complete only when all review gates and commands pass and the final
report records:

- approved artifact and final owned-file SHA-256 values;
- exact five-node transform diff and frozen pre/post hashes;
- complete proof-reconstruction/tamper matrix results at validator and emitter;
- 114/116/96/212 counts and exact sorted catalog/binding evidence;
- ten native F32/RGBA8 oracle results, all Star 5..12 qNaN words, probes,
  orientation, alpha/nonfinite profiles, and repeat identity;
- Debug, Release, ASan, and UBSan commands/results;
- `.su` frame table, maximum call-chain reasoning, and Release disassembly;
- generated-code forbidden-pattern inspection;
- proof that only the owned source/test files and three generated outputs
  changed, with unrelated generated factory bodies unchanged.

Do not claim parity from hashes alone, generator success alone, or one build
configuration. No branch, worktree, commit, push, or pull request is part of
this implementation design.
