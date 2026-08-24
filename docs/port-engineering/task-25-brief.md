# Task 25 exact main-local literal vec3 lane-index scope and proof brief

> **Status:** frozen read-only scope/proof contract. Stop before design and
> implementation. This file authorizes no repository edit and no Git operation.

**Goal:** add exactly these two direct public/canonical programs:

```text
classicNoisedeck/lensDistortion:lensDistortion
filter/prismaticAberration:prismaticAberration
```

by applying exactly `literal-vec3-lane-index-v1`: replace eleven authenticated
literal selections of the one `main`-local `vec3 hsv` with equivalent fixed
one-lane swizzles. The closed slice is six direct plain-`=` lvalues and five
reads. This is not generic vector indexing and authorizes no dynamic index,
other vector/base/site, or runtime subscript.

## Global constraints and hard Task 24 gate

- Scope is exactly the two sorted keys above, exact 8/3 site inventories, and
  exact empty define maps.
- Add exactly one profile/loader carrier,
  `literal-vec3-lane-index-v1`, on exactly both keys.
- Do not add `index`, vector indexing, dynamic indexing, or another broad name
  to the approved-capability vocabulary. A foreign, second, moved, changed, or
  non-profile index rejects.
- Do not admit `filter/grade:lut`; its twenty induction-indexed read/write
  `vec3[i]` sites are outside this profile.
- Add no type, operator, proof dataclass/field, numeric-literal mode, loop rule,
  safety-cap change, source global, array, matrix, runtime helper, sampler ABI,
  derivative, or generic compatibility transform.
- Preserve `glsl-f32`, Number-compatible scalar temporaries, F32 storage and
  builtin boundaries, existing sampler coordinate behavior, and
  `-ffp-contract=off`.
- Full F32 and RGBA8 public-factory equality are mandatory; RGBA8-only or
  tolerance acceptance is forbidden.
- No Git, branch, worktree, commit, push, pull request, or deployment.

Task 25 must start only after independent final Task 24 acceptance. The gate is
exactly **123 typed / 125 public / 87 publicly unported / 212 corpus**, with
Gather Sorted at typed position 51 and all Task 24 public/native, profile,
forgery, stack, fetch, generated-isolation, Debug/Release/ASan/UBSan, Python,
CTest, and prior-oracle gates accepted. Recheck the amended Task 24 brief and
frozen artifacts:

| Task 24 artifact | SHA-256 |
| --- | --- |
| `task-24-frontier-audit.md` | `fa4e0481ea50534be05923cf2c673b9f45195315121fbac7cbd05bece4f21220` |
| `task-24-brief.md` | `a5184121126d75b32372440aae13ef9cde06006c5f4189607327e323e7d16e53` |
| `task-24-oracle-generator.mjs` | `35d20a4428af390ed437f3c829a250a1974d254b66712c900d684d54a7e682d6` |
| `task-24-oracles.json` | `07dd6f31c3e2b5451cbde8fc0ae6f68ec7c3b06cd6296222ac938cdcee37a72a` |
| `task-24-oracle-report.md` | `b33894f0d69c97de5392d686bc9d5b469d672fc59f522b7b79c15604ae4299f6` |
| `task-24-projection.py` | `a864160c1c92f198003dbb1371d5814f268a18365d2775612f27bcc712d41409` |

At Task 25 preflight, record the independently accepted final Task 24 hashes
for every Task 25-owned file and generated output. Reparse and rehash both keys
on those exact final bytes. No accepted Task 24 report, or any count, key,
source/profile, typed hash, generated block, or interface drift, is a hard
stop; do not stack onto an in-flight or merely locally green Task 24 tree.

Conditional on that hard gate:

| State | Typed | Public | Publicly unported |
| --- | ---: | ---: | ---: |
| Accepted Task 24 | 123 | 125 | 87 |
| Exact two-key Task 25 | **125** | **127** | **85** |

The projected newline-terminated sorted 125-key typed-list SHA-256 is
`9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4`.
After adding only the separately maintained `filter/invert:inv` and
`synth/solid:solid`, the 127-key public-list SHA-256 is
`9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`.
Tests must compare explicit lists as well as digests. Final zero-based typed
positions are Lens 2, Gather Sorted 52, and Prismatic 59.

## Frozen audit and public-factory oracle artifacts

| Artifact | SHA-256 |
| --- | --- |
| `task-25-frontier-audit.md` | `e754d9e02e3d98069297dda9f2c8071d25ba2347ddd812af0c41dc74b82e7d27` |
| `task-25-oracle-generator.mjs` | `3594cd9f0a82e7a21e662f8897f43eac0c86943b15ca36b2a0d3d0f805b2772c` |
| `task-25-oracles.json` | `09d8d8a9667fe3b3b90cd582e501b7c0a61d2a41e65ea2d175771a105e32e116` |
| `task-25-oracle-report.md` | `f72b69688d9a2f10df1603d1a012f6df8d0834f012438386038637630eb20611` |

Run `node docs/port-engineering/task-25-oracle-generator.mjs --check`
before implementation and at every review gate. The pinned
`../noisemaker-for-cpu` checkout is oracle provenance only;
it must not become a native build, runtime-test, installed, or generator
dependency.

## Exact source, public identity, and typed-program locks

| Field | Lens Distortion | Prismatic Aberration |
| --- | --- | --- |
| Source | `sources/classicNoisedeck/lensDistortion/lensDistortion.glsl` | `sources/filter/prismaticAberration/prismaticAberration.glsl` |
| Raw bytes / SHA-256 | 8269 / `f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444` | 4247 / `513eac95fdf7f67a6839ee5d96e5bbfd76b6cfa62d3254df6fed23d8effe380e` |
| Normalized bytes / SHA-256 | 7723 / `6586c49b079a3b0f4aa3538c8e735e70db088ff2e5d2ea1037e9e9c5486fdf52` | 3907 / `1c157e7f3dc7c9c122cc185812cd2988a98a52024055a482265bded7561a0860` |
| Defines | exactly `{}` | exactly `{}` |
| Canonical/public factory | exact same `canonicalFactory10` object | exact same `canonicalFactory117` object |
| Factory-text SHA-256 | `151b1e868c7d2f9a446a8778d170260e5003fec540afb2623088bbf34ca8adcf` | `2eab8943387658c1c28f4e089edd9b248bf441b2b77145ea137c7f979c5def02` |
| Adapter entry | absent | absent |
| Functions | 8 | 5 |
| `main` ID / body statements | 38 / 25 | 22 / 31 |
| `main` hash pre | `dc6d4d2a3b5c50598a879dc6679553b3f89d964a19f5d4c79716970a7f2493ee` | `416ffbaef2ada8e19fb0f161034a964d4fcfd88c8b2e34fe4f66c1b415a70e56` |
| `main` hash post | `8de6658184c69cb679f0453e37e37f538eebabb0e14f720d1eeea61e715d30ec` | `f0d3926e68fcb9c4672779fa36c363d9471240395f36e2857146225e5a87187f` |
| Function tuple pre | `263870c469a9dc3b1f4d5f3a2498864c6da4ff4eaf2cc3efaf198376e4d304c1` | `6949577823e5eccde21335182d379a590db90188f004f3d479503ac33990cf24` |
| Function tuple post | `c166fa2b38ec68661fb4d73be1bfb3eef4f879da7d82dbfca44deba1b651a756` | `80fb20a869a84f8c23942fab3b033e554e48c5e5dda2097eb8dbd346a1c758fd` |
| Whole program pre | `f63fb6dba6626791c248501bcfc5ca1c94f073a0593f34dbe846056fe35c81f5` | `fdc004aa9e36925670b4a33446690150a81ed8b13ffba4aed1b944b2d80b997c` |
| Whole program post | `e5dbb049717ce77ba79a36c6ea39ddde88e561df1ba06c98fba0ddd179a63d2e` | `1a808ce2ca4aae60be185b04ac96078521db41bcb04d5bb0e9cdb7552f6d482c` |
| Interface pre and post | `53e759b54c0710d9cb3375cc2353878abebec06b378aeaaf9d745c6ecfd2b4ca` | `788b0390952c998db1945320c681f114bcbc150fe1f91738894f77a6220df010` |
| Diagnostic projected C++ | 27,446 bytes / `6cfa9d58cbc096b7372b00b17b4ed0b146236a4738acef7870cad05593a57fc5` | 13,316 bytes / `8d6c98fed4ab2d2a2130566081386cdfb74d01ae84c11b198a1be08ae187155f` |
| Profile-tuple SHA-256 | `d1235bb6045a5795c4c10c5db8a990f51ee42e5541dcfa7a663c91f3245d10d3` | `25ad8a580a8263b4d2d15b41eb783abeed3433c94b9c8fffbbae2546300fd6b2` |

The corpus revision is
`a024dc3a960cc44af454abc7aebce50456c194e6`. The canonical runtime, public
catalog, and adapter-index SHA-256 values are respectively
`e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`,
`d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4`,
and `40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267`.

Hash serialization is exactly:

```python
sha256(repr(program.functions))

sha256(repr((
    program.key, program.source, program.raw_source, program.declarations,
    program.functions, program.resources, program.body_status,
    program.local_type_names, program.structs, program.uniform_blocks,
    program.interface_symbols, program.builtin_symbols,
    program.counted_loop_proof, program.preprocessor_defines,
)))

sha256(repr((
    program.declarations, program.resources, program.local_type_names,
    program.structs, program.uniform_blocks, program.interface_symbols,
    program.builtin_symbols, program.preprocessor_defines,
)))
```

Only `main` changes. Every other full function must remain dataclass-equal and
preferably object-identical. Declarations, resources, source, interfaces,
defines, loop summary, and all existing optional proofs remain byte-identical.
Caller-supplied hashes are drift alarms, never proof authority.

## Exact eleven-site typed inventory

Path grammar: the first integer selects `function.body[index]`; `sN` descends
to `TypedStatement.children[N]`; `eN` selects
`TypedStatement.expressions[N]`; the following `0` is the expression-root
sentinel; remaining integers select successive `TypedExpression.children`.
Every path is owned by `main`.

Each pre site is kind `index`, result `float`, category `lvalue`, with exactly
two children. Child zero is a direct `id` of the one automatic writable
`vec3 hsv`; child one is an `int` rvalue literal in `{0,1,2}`. Only an index
that is child zero of a plain `assign` with operator `=` has role `write`;
all others have role `read` even though their typed category remains lvalue.

### Lens Distortion: main ID 38, hsv symbol 72

| Path | Span | Lane / role | Pre index SHA-256 | Post swizzle SHA-256 |
| --- | --- | --- | --- | --- |
| `(18,'s0','s3','e0',0,0)` | `236:9-236:15` | 0 / write | `8b56c4f52b2113fa843aeb30133f38a488eda92edca236b9260285e426c632a3` | `1d9ee202f7c93a030803d2c61782ef959a8ef56fc8890b39de56bfe6cb2df13b` |
| `(18,'s0','s3','e0',0,1,0,0,0,0)` | `236:24-236:30` | 0 / read | `1cc773177b9c87d54bd4289dd97c6384f43c0619d1c29a1b5cf1a09a2225a9e6` | `c7daed1dbf0ebc39669fa33212fa1d9b3233fbe7112e07c05ebeaa05a9120920` |
| `(18,'s0','s3','e0',0,1,0,0,1,0,0)` | `236:65-236:71` | 0 / read | `27987cf202ec44e367f3edbacf025685a95a579d3bd1766ed007f3a39fba0233` | `689cb485e1d153df4ba2f46f52e10f7843c818cf111cbdf6d79aa26419f9f69a` |
| `(18,'s0','s4','e0',0,0)` | `237:9-237:15` | 1 / write | `e67ab422ce4f28337e56fef80f8bfb4dbd93a1bbe30eb0165c0aa3cc7dc6cb44` | `829b7f013b6ca2c1cbf03eb25079f7a02ec32731eb0bb8d8015dbfa77152e16b` |
| `(18,'s1','s3','e0',0,0)` | `247:9-247:15` | 0 / write | `92be124aed858e61dff4316731b67be8a46a881c527285b56263477b81193f12` | `0ee30fa6b2497642b0b1b2cbb0fe9fee6fc7594191d410f3ff2b20f7ba6c8243` |
| `(18,'s1','s3','e0',0,1,0,0,0,0,0)` | `247:26-247:32` | 0 / read | `af51ced1d6aafe987b1914573554213afb0c123619134749a44fdb603d08b818` | `d3a7a9840bbe6523a9038c402537928e10b5abaca692762a7b8947f821f4add0` |
| `(18,'s1','s4','e0',0,0)` | `248:9-248:15` | 1 / write | `569c4bc0beead7e391d0bddbcfe03fb78b78286f8bb00754eb37bfa5bc1720de` | `2c94a065f64b606da19073ffe0afd554d57c9222714af12c034b37f90a6b192a` |
| `(20,'s1','s0','s0','e0',0,1,0,0,0,1,0)` | `260:46-260:52` | 2 / read, sole `vec3` splat input | `e2faad5610537f7e86b817e16c093b165a4d4d84bac84799bfc055f3de262fea` | `96a5a6b39df3fba890e8286278615e6518ec77b6c9d440f9e315bdc70d596250` |

### Prismatic Aberration: main ID 22, hsv symbol 55

| Path | Span | Lane / role | Pre index SHA-256 | Post swizzle SHA-256 |
| --- | --- | --- | --- | --- |
| `(26,'e0',0,0)` | `131:5-131:11` | 0 / write | `2637ccd727e74a3b5583230bf07d8ceed92e72dfc4434041075f90515950f23d` | `2c240e9eae37323e092e20ac3d21e7382fcd86b7160b8f041cc3a2eb9cb7bdeb` |
| `(26,'e0',0,1,0,0,0,0,0)` | `131:22-131:28` | 0 / read | `9af4f5115d7b784cac89bd118123e8b0935194c93b970da62f01541590b17ce2` | `94558e9138e38ceb285c1746af1473ca77f5f56ef564626edaad0be6546d6072` |
| `(27,'e0',0,0)` | `132:5-132:11` | 1 / write | `155a0535e006b5b61f14d842415d9bba0633f15d905e7fbf8944ff847f5685f2` | `8e585f401b1450e2f7c58dd3fada71b23f0cb2b4e85f7e75c6371459db863306` |

Thus the complete pre-tree index census is exactly **11 = 8 + 3**, all
selected; the post-tree index census is exactly zero. Roles are six writes and
five reads, and lane incidence 0/1/2 is exactly 7/3/1. There is no compound
assignment, increment/decrement, nested selection, alias, escape,
`out`/`inout` actual, parameter/global/uniform base, alternate local, dynamic or
negative index, or lane outside `0..2`.

For each key, the exact profile tuple is:

```python
(
  'literal-vec3-lane-index-v1', key, raw_source_sha256, {},
  tuple((path, span, pre_sha256, post_sha256, hsv_symbol_id, lane, role)
        for each frozen row in table order),
  pre_function_tuple_sha256, post_function_tuple_sha256,
  pre_whole_program_sha256, post_whole_program_sha256,
  interface_sha256,
)
```

Its SHA-256 of UTF-8 `repr(...)` is the per-key value frozen in the identity
table. Paths are tuples, not lists; roles are exactly `'write'` and `'read'`.

## Exact closed rewrite and emission contract

After authenticating the complete pre tree and ordered census, each selected
site is replaced exactly by:

```python
dataclasses.replace(
    site,
    kind='swizzle',
    children=(site.children[0],),
    member='xyz'[site.children[1].literal_value],
)
```

During the transition, the original base object is retained by Python object
identity. The profile application and transform tests hold the pre and post
trees simultaneously and must assert `replacement.children[0] is
site.children[0]` for every row. Type, normalized span, category, and all other
fields are retained; only `kind`, `children`, and `member` change. No source
rewrite, runtime index, bounds branch, pointer arithmetic, lookup table,
helper, proof annotation, or extra node is allowed. All eleven replacements
happen in one authenticated walk. Rewriting zero, a subset, a duplicate, a
twelfth site, or an already transformed tree rejects.

Python object lineage is deliberately not part of standalone post-tree
authority. Once only a post tree is available, an equal frozen dataclass clone
is indistinguishable from the original object and must not be claimed as
rejectable. Standalone validator/emitter authentication instead requires the
exact observable post structure, fields, rows, and hashes. Add no lineage
registry, side table, token, proof field, or typed-IR field: those would widen
the immutable schema solely to preserve process-local history that the exact
deterministic transition tests already prove.

The validator and emitter independently authenticate the exact post tree,
profile, source/key/defines, function/whole/interface locks, and exact 11-row
post-site table. Reads emit only existing fixed
`glsl::swizzle<I>(hsv)`. Direct plain-`=` writes emit only existing
`glsl::set_swizzle<I>(hsv, rhs)`. The RHS is evaluated once before lane
storage; existing one-lane `set_swizzle` applies `convert_lane<float>` and
therefore preserves the canonical Float32Array storage boundary. The line-260
source `vec3(hsv[2])` emits the existing scalar-to-vec3 splat around one fixed
`glsl::swizzle<2>(hsv)`; it is one authenticated source read, even though the
public JavaScript factory materializes three `hsv[2]` values.

Any `operator[]`, runtime lane integer, switch, dynamic bounds logic,
allocation, virtual/indirect dispatch, callback, `std::variant`, or pointer
selection in the two generated pixel namespaces fails. Existing runtime and
polymorphic DSL facilities may be reused only insofar as the final code shape
is the fixed compile-time swizzle route above; this profile does not expose a
general subscript API.

## Bindings, resources, fetches, calls, and stack

Lens bindings are exactly:

```text
inputTex:sampler2D@1/S1
resolution:vec2@2
tileOffset:vec2@3
fullResolution:vec2@4
time:float@5
aspectLens:bool@6
shape:int@7
tint:vec3@8
alpha:float@9
vignetteAmt:float@10
distortion:float@11
speed:float@12
loopScale:float@13
aberration:float@14
hueRotation:float@15
hueRange:float@16
mode:int@17
modulate:bool@18
blendMode:int@19
saturation:float@20
passthru:float@21
fragColor:vec4@22
```

Prismatic bindings are exactly:

```text
inputTex:sampler2D@1/S1
resolution:vec2@2
tileOffset:vec2@3
fullResolution:vec2@4
time:float@5
aberrationAmt:float@6
hueRotation:float@7
hueRange:float@8
modulate:bool@9
saturation:float@10
passthru:float@11
fragColor:vec4@12
```

Lens therefore has one sampler, twenty ordinary uniforms, and one output;
Prismatic has one sampler, ten ordinary uniforms, and one output. Both use
texture sampling and neither uses derivatives, varyings, uniform blocks,
source globals, arrays, matrices, structs, sampler parameters, or non-`in`
helper parameters.

Lens has exactly three static `texture` sites and exactly three dynamic texture
samples per pixel; it has no texture-size call. Prismatic has exactly three
static `texture` sites, three dynamic texture samples per pixel, and one
`textureSize(inputTex,0)` call per pixel. Neither program has a loop. Their
call graphs are acyclic and contain only direct generated helpers; no
recursion, indirect/virtual call, callback, exception, per-pixel allocation,
VLA, or `alloca` is allowed.

Preserve Debug/Release/sanitizer `.su` records for `pixel` and every reachable
helper in each namespace. Report each static frame and maximum non-inlined
chain sum, or resolve inlining with Release disassembly. Every frame/chain must
be static and below the existing 16 KiB warning threshold. Release disassembly
must show fixed swizzle/lane code with no runtime lane branch or indirect route.
Binder `State` allocation and external `Surface` storage are not per-pixel
stack.

## Frozen public-factory cases and site sensitivity

The JSON contains six representative public-factory cases. Lens covers every
`mode × blendMode` combination, with both static and modulated time paths,
positive and negative distortion, aspect-lens branches, tint, alpha, passthru,
and both vignette signs. Prismatic covers static origin/full-frame and
modulated nonzero asymmetric tile offset/full resolution, including its
texture-size/local-coordinate path.

| Case | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| Lens chromatic/add/static | `40ec6e6bcca21c55b0abe81eca5760b2e623aad76678b49b070d350d0fe49948` | `de4b64895586ce7dc92352820b5c64d5660dc1d722bd8c5392e42568385ec4b8` |
| Lens chromatic/alpha/modulated | `3c4ff034284a714a545a35106c98e7d93398fb800f7bee2dbccffb08592a5e61` | `18b8e022320da7b278ae2935b8602f50ebcf30cfc1e5eb058e932f8d05666ada` |
| Lens prismatic/add/static | `0ed06880cce85cebb134fbc0cb2b5710a4a3e08dc336512e31cbaf2a5ec77688` | `204fe8f73e191091c231f159d147cb10df17b9bc88abc44c6baa75da7684b05e` |
| Lens prismatic/alpha/modulated | `7fe6ac9ba3bf66f5f3f747f635b6ce5bd9d7e1d184678a74ba1d69cc14b18b76` | `4b8ffb755c45fa8b37e686ff71fd61f66c120eeaf2644b6d871e01b6a728521b` |
| Prismatic static/origin tile | `daad9591d01855520a052fd2d89ed2e9ed32da2d93421a041e40d58b5389daff` | `5f73c9a1151a312569107b68abd705555f7d2c5540c8e3ea44abd7891a9a3640` |
| Prismatic modulated/offset tile | `dbc929af7ba49e768bd39a0188e0f9b9426581ba564c856e6289531304c8b216` | `5f141b94b43d85418de325137173a181d705f50574f4d1ca78e01972a1044447` |

Every case freezes the F32 input hash/probes, full-F32 and RGBA8 output
hashes/probes, finite-lane count, input immutability, and fresh double-render
byte identity. Native tests must reproduce every field exactly in Debug,
Release, and sanitizer builds, including top-down storage, bottom-left fragment
origin, clamped sampling, tile offset, and alpha.

There are exactly eleven one-site wrong-lane mutations, one per frozen source
row. Each write target, RHS read, and lane role is independently sensitive in
at least one active case; in fact each mutation diverges in both active branch
cases. The line-260 splat mutation changes its three expanded public-factory
occurrences together because they represent one source read. Exact mutation
IDs, candidate hashes, lane/byte differences, and maximum differences are
normative in the JSON/report. Native exact output must match the baseline; a
corresponding wrong post swizzle must either be rejected by the profile or,
when deliberately executed only in the negative test harness, diverge where
the frozen mutation does. Mutation outputs are sensitivity evidence, never an
authorization for a different lane.

## Four-mode loader/profile and forgery matrix

The loader application accepts only the exact pre tree plus exact carrier,
authenticates all pre locks, and produces the exact post tree. Direct validator
and emitter calls operate fail-closed on the post tree:

| Mode | Typed tree | Profile carrier | Result |
| --- | --- | --- | --- |
| 1 | authentic pre-index tree | absent/wrong | reject unsupported index |
| 2 | authentic pre-index tree | exact | loader transforms; direct validator/emitter reject because required post sites/hashes are absent |
| 3 | authentic post-swizzle tree | absent/wrong | reject transformed tree without matching authority |
| 4 | authentic exact post-swizzle value tree | exact | validator and emitter accept, including a dataclass-equal reconstruction |

The four modes concern observable tree values and carrier state, not post-only
Python object lineage. Test both retained authentic caller hashes and
attacker-recomputed caller hashes in all four modes. Neither may rescue a
value-forged tree. Wrong spelling,
foreign key, only one of the two loader entries, duplicate entry, carrier on
Grade LUT, simultaneous unrelated compatibility carrier, or schema/manifest/
validator/emitter disagreement rejects.

The negative matrix must independently cover:

- corpus revision, source path/raw/normalized bytes, key/runtime key, defines,
  numeric contract, factory/public identity, adapter presence, function order/
  ID/signature/body count, function/whole/interface/profile hash drift;
- zero, ten, twelve, reordered, moved, duplicate, partial, or already/twice
  transformed sites; wrong path/span/pre/post hash/base/index/parent/role;
- base name/ID/type/storage/writability changed; another local/parameter/
  global/uniform base; vec2/vec4/integer vector, array, matrix, struct, sampler;
- non-int, nonliteral, uniform, induction, negative, out-of-range, or
  effectful index; lane/member mismatch; nested index; delayed indexed lvalue;
- read changed to direct write, write changed to read, compound assignment,
  prefix/postfix update, `out`/`inout` escape, alias, callback, pointer, or
  runtime subscript;
- replacement node kind/children/member/type/category/span changed; transition
  fails to retain the pre base object while both trees are available; non-site
  function or interface changed;
- loop/global/array/derivative/sampler/fetch/output/function insertion,
  recursion, allocation, exception, indirect call, dynamic stack, or
  unrestricted indexing capability.

Semantic profile application, generator validation, and emitter authentication
must recompute value authority independently. Transition-only identity tests
remain separate from post-only value authentication. One accepting layer
cannot launder a value-forged tree into the next.

## Exclusions and generated isolation

Exactly 85 publicly unported programs remain. Exclude Grade LUT and every
dynamic/induction/uniform index; every other base/vector width/lane/site; all
remaining global, loop, derivative, builtin, ABI, matrix, array, struct, UBO,
and varying families; and every capability expansion not enumerated here.

After accepted Task 24, implementation may touch only:

```text
tools/glslcpp/frontend/literal_vec3_lane_index_profile.py  # new exact profile helper
tools/glslcpp/generate_typed_slice.py
tools/glslcpp/emit_typed_cpp.py
tools/glslcpp/typed_slice.json
tests/test_typed_generator.py
tests/test_generated_kernels.cpp
tests/test_typed_slice.cpp
src/typed_generated/typed_slice.cpp
src/typed_generated/typed_manifest.json
include/noisemaker/generated/catalog.hpp
```

No parser, semantic analyzer, typed-IR dataclass, loop/proof module, runtime,
numeric, swizzle helper, sampler, Surface, corpus, CMake, or unrelated test edit
is authorized. If the exact closed profile cannot be implemented within this
list, stop for scope review.

Generated isolation requires:

- all 123 accepted Task 24 blocks byte-identical after replacing only
  `typed_[0-9]+` namespace ordinals with one fixed sentinel;
- exactly two new blocks: Lens at position 2 and Prismatic at position 59;
  Gather Sorted moves only ordinal position from 51 to 52;
- exactly two new catalog/manifest/header entries, with final explicit
  typed/public lists and their frozen digests;
- no whitespace, comment, literal, factory, ABI, key, manifest, header, or code
  normalization outside necessary namespace ordinal changes;
- each new namespace matches its exact diagnostic projection after the same
  deterministic namespace/factory normalization;
- exactly the six authenticated main writes through fixed
  `glsl::set_swizzle<I>`, five authenticated main reads through fixed
  `glsl::swizzle<I>`, and no runtime `operator[]`/lane selection route;
- exact bindings, three static texture calls per key, Prismatic's one
  texture-size call, no derivative/loop/allocation/dispatch/recursion/dynamic
  stack, and only owned-file drift.

## Required verification and completion evidence

Run from `.` with no Git command:

```sh
shasum -a 256 \
  docs/port-engineering/task-25-frontier-audit.md \
  docs/port-engineering/task-25-oracle-generator.mjs \
  docs/port-engineering/task-25-oracles.json \
  docs/port-engineering/task-25-oracle-report.md
node docs/port-engineering/task-25-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
```

Use fresh `/tmp` Debug, Release, and ASan/UBSan build directories, selecting
Ninja only when installed and otherwise Unix Makefiles. Preserve
`-ffp-contract=off`, `-fstack-usage`, and `-fstack-size-section`; enable leak
checking and UBSan `halt_on_error=1`. Build and run full CTest in all three.
Rerun every accepted Task 15-24 oracle/check command.

Mechanically extract only the two new namespaces. Prove exact fixed-swizzle
code shape and absence of runtime indexing; exact binding/State ABI; exact
fetch and texture-size accounting; no generated C++ `main`; and no forbidden
allocator/container/string/callback/exception/`alloca`/indirect route. Preserve
Debug and Release `.su` files and Release disassembly evidence.

Task 25 is complete only with accepted final Task 24 baseline evidence; all
frozen artifact/source/factory/public/site/profile/function/whole/interface/
binding/resource/list identities; the full four-mode loader/validator/emitter
and forgery matrices; exact **125/127/85/212** counts; all six native
full-F32/RGBA8 cases and all eleven site mutations accounted; deterministic
repeat, immutable input, finite output, tile/origin/alpha behavior; clean
Debug/Release/ASan/UBSan/Python/CTest/prior oracles; bounded stack/disassembly/
fetch proof; exact generated isolation; and an owned-file before/after hash
inventory.

This brief stops before design and implementation. If Task 24 acceptance,
profile authentication, public oracle parity, generated isolation, or any
exact site cannot be reproduced, stop for revised independent review. Do not
fix forward by exposing generic vector indexing, admitting Grade LUT, changing
the runtime/swizzle DSL, or broadening the owned-file set.
