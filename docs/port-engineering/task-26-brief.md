# Task 26 Smooth Edge exact LUMA_WEIGHTS scope and proof brief

> **Status:** frozen read-only scope/proof contract. Stop before design and
> implementation. This file authorizes no repository edit and no Git operation.

**Goal:** add exactly `filter/smooth:smoothEdge` under the identity profile
`smooth-edge-luma-weights-v1`. The profile authenticates the unchanged typed
tree containing its sole source-global declaration
`const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114)` and permits only the
emitter to materialize that exact value as one automatic helper-local
`const glsl::Vec3` in `luminance`.

This is not a general source-global, aggregate-constant, or `const vec3`
capability. It authorizes one declaration, one resolved static read, one owner,
and one materialization site on one key.

## Global constraints and hard Task 25 gate

- Scope is exactly `filter/smooth:smoothEdge`, exact empty defines, symbol 7,
  the one `luminance` read, and the exact three-literal constructor.
- Add exactly one profile/loader carrier,
  `smooth-edge-luma-weights-v1`, on exactly this key.
- Do not add globals, vector constants, aggregate constants, source locals, or
  another broad name to the approved-capability vocabulary.
- Do not admit another constant/global program, including Grade, matrix/table,
  palette, glyph, mutable-array, or uninitialized-global families.
- Add no type, operator, proof dataclass/field, registry, numeric-literal mode,
  loop rule, safety-cap change, array/matrix/struct representation, runtime
  helper, sampler ABI, derivative, or generic compatibility transform.
- Preserve `glsl-f32`, Number-compatible scalar temporaries, F32 constructor/
  storage/builtin boundaries, existing `dot` and sampler behavior, and
  `-ffp-contract=off`.
- Full F32 and RGBA8 public-factory equality are mandatory; RGBA8-only or
  tolerance acceptance is forbidden.
- No Git, branch, worktree, commit, push, pull request, or deployment.

Task 26 must start only after independent final Task 25 acceptance. The gate is
exactly **125 typed / 127 public / 85 publicly unported / 212 corpus**, with
Lens at typed position 2, Gather Sorted at 52, and Prismatic at 59. All Task 25
profile, public/native, eleven-site mutation, forgery, stack, fetch,
generated-isolation, Debug/Release/ASan/UBSan, Python, CTest, and prior-oracle
gates must be accepted. Recheck the frozen Task 25 artifacts:

| Task 25 artifact | SHA-256 |
| --- | --- |
| `task-25-frontier-audit.md` | `e754d9e02e3d98069297dda9f2c8071d25ba2347ddd812af0c41dc74b82e7d27` |
| `task-25-brief.md` | `193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2` |
| `task-25-oracle-generator.mjs` | `3594cd9f0a82e7a21e662f8897f43eac0c86943b15ca36b2a0d3d0f805b2772c` |
| `task-25-oracles.json` | `09d8d8a9667fe3b3b90cd582e501b7c0a61d2a41e65ea2d175771a105e32e116` |
| `task-25-oracle-report.md` | `f72b69688d9a2f10df1603d1a012f6df8d0834f012438386038637630eb20611` |

At Task 26 preflight, record independently accepted final Task 25 hashes for
every Task 26-owned file and generated output. Reparse and rehash Smooth Edge
on those exact final bytes. No accepted Task 25 report, or any count, key,
source/profile, typed hash, generated block, or interface drift, is a hard
stop; do not stack onto an in-flight or merely locally green Task 25 tree.

Conditional on that hard gate:

| State | Typed | Public | Publicly unported |
| --- | ---: | ---: | ---: |
| Accepted Task 25 | 125 | 127 | 85 |
| Exact Smooth Edge Task 26 | **126** | **128** | **84** |

The projected newline-terminated sorted 126-key typed-list SHA-256 is
`01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76`.
After adding only the separately maintained `filter/invert:inv` and
`synth/solid:solid`, the 128-key public-list SHA-256 is
`d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3`.
Tests must compare explicit lists as well as digests. Smooth Edge's final
zero-based typed position is 77:

```text
filter/skew:skew
filter/smooth:smoothEdge
filter/smoothstep:smoothstep
```

## Frozen audit and public-factory oracle artifacts

| Artifact | SHA-256 |
| --- | --- |
| `task-26-frontier-audit.md` | `f0971b7cc06b9758975f6d856950c9a5067a2fd9ea71e4c68e46edc699bdf6f6` |
| `task-26-oracle-generator.mjs` | `43300fee88354bcce9d1294071858fce432e2297ce1dd3dcccfed524ba2268f9` |
| `task-26-oracles.json` | `7975cbe59733df0178956b7f145e03c2e872e269327d9f8dd1126c3bb9c3ccf9` |
| `task-26-oracle-report.md` | `b3e4a175ea95fe4bdd3319a11996451551ab9a3281412d10aa856f906515f816` |

Run `node docs/port-engineering/task-26-oracle-generator.mjs --check`
before implementation and at every review gate. The pinned
`../noisemaker-for-cpu` checkout is oracle provenance only;
it must not become a native build, runtime-test, installed, or generator
dependency.

## Exact source, public, typed-program, and function identity

| Field | Required value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Key/runtime key | `filter/smooth:smoothEdge` |
| Source | `sources/filter/smooth/smoothEdge.glsl` |
| Raw bytes / SHA-256 | 1554 / `b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265` |
| Normalized bytes / SHA-256 | 1235 / `42f61c507d633c07415bc816b6ba61f8a862642429943be1c0c1208c97b90f7c` |
| Defines | exactly `{}` |
| Numeric contract | exactly `glsl-f32` |
| Identity profile | exactly `smooth-edge-luma-weights-v1` |
| Canonical/public factory | exact same `canonicalFactory140` function object |
| Factory-text SHA-256 | `732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e` |
| Public adapter entry | absent |
| Function tuple SHA-256, pre and post | `8a7f2ac058a23e438f31787c55d235235271429fb79fc1d085c4dd1ba08cd4fc` |
| Whole program SHA-256, pre and post | `5586658ce1f621887647e5fb77990606e8637b7d759d2c9f1096f26b7385cd89` |
| Interface SHA-256, pre and post | `9149a7b19b47edea7179f8460443ee67c4a314bcb3ed2a83b7a68d91550f4930` |
| Profile-tuple SHA-256 | `fbb3808e4392e3b3fa56a48965a36a47ce1a438626c9acdc6d33613fd3f57b80` |

The pinned canonical runtime, public catalog, and adapter-index SHA-256 values
are respectively
`e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`,
`d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4`,
and `40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267`.

There are exactly two functions in this order:

| ID / function | Parameters | Body statements | Full-function SHA-256 |
| --- | --- | ---: | --- |
| 9 `luminance` | symbol 8 `rgb:vec3`, direction `in` | 1 | `454e07a023decf6855ebb1b00e4e34013a0926b9b2ce43c08d6dd257f4538b8a` |
| 10 `main` | none | 13 | `91808a5a46522dc3c72f54733faea98e29621f9ac305a88ef5c7e5c2709e16aa` |

The profile is an identity transform. It authenticates the complete source
tree and returns the same immutable `TypedProgram` object; it adds no node,
proof, declaration, local, or field. Validator and emitter calls may receive a
dataclass-equal reconstructed tree and therefore authenticate exact value
structure and hashes rather than impossible post-only object lineage. Add no
registry, side table, lineage token, proof field, or typed-IR field.

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

Caller-supplied hashes are drift alarms, never proof authority.

## Exact source constant and resolved read closure

The sole non-interface declaration is normalized span `12:1-12:53`, raw line
19:

```glsl
const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114);
```

It is symbol 7 named exactly `LUMA_WEIGHTS`, storage `const`, type `vec3`, and
non-writable. Its full declaration repr SHA-256 is
`be8644a44ad3d2710e4dfaa87045257a5bd7c0e7e0a363c12893ea77c3d2ee27`.
The initializer is a direct `vec3` constructor at `12:27-12:52`, with exactly
three scalar-float literal children and repr SHA-256
`57ee749ccff2d5029ccbd10b7ce01320fdeb694bf2d02d5835a0e6ccd5836104`.

| Lane | Literal lexeme/value | Span | Literal repr SHA-256 | F32 bits |
| ---: | --- | --- | --- | --- |
| 0 | `0.299` / 0.299 | `12:32-12:37` | `06162ef141f3a4066bbb35d0ec773002c341ec99f3c3b19a024bf381d5486c27` | `0x3e991687` |
| 1 | `0.587` / 0.587 | `12:39-12:44` | `6f17e5a19288943b912be887ac5b4390afbab72c3e2c6786d78d64dd068f285f` | `0x3f1645a2` |
| 2 | `0.114` / 0.114 | `12:46-12:51` | `8af04ca08c0c38d7ad1fb93f89ce44698bbb43bd43ca80060a723dd089806e41` | `0x3de978d5` |

There is exactly one resolved-symbol static read. Path grammar uses the first
integer for `function.body[index]`, `eN` for
`TypedStatement.expressions[N]`, the following `0` as expression-root
sentinel, and remaining integers for `TypedExpression.children`.

| Field | Exact value |
| --- | --- |
| Owner | function 9 `luminance` |
| Path | `(0,'e0',0,1)` |
| Read span | `15:21-15:33` |
| Read shape | `id`, symbol 7, `vec3`, category `readonly lvalue` |
| Read repr SHA-256 | `df251d3d8461278afd63b36f1f3cef0d48777196908b8571a11d65dc54b83880` |
| Parent | scalar-float rvalue builtin `dot`, signature -13 |
| Parent span / child role | `15:12-15:34` / child 1 of 2 |
| Parent repr SHA-256 | `0f4d0fe02d9ee23557db69dfaca7ffa5c2542295d385c0d075f5b7e374fa43ae` |
| `rgb` first-argument repr SHA-256 | `0c947970257b7042745712013dccbc9cbe816a36827840e4e403bd36c3e06ef3` |

There is no second read, write, compound assignment, increment/decrement,
swizzle/index/member write, parameter passing, return, alias, main ownership,
or `out`/`inout` escape. `main` calls `luminance` exactly five times on the
nonzero `smoothType` path and zero times on the pass-through path.

The exact profile tuple is:

```python
(
  'smooth-edge-luma-weights-v1',
  'filter/smooth:smoothEdge',
  'b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265',
  {},
  (7, 'LUMA_WEIGHTS', 'const', 'vec3', '12:1-12:53',
   'be8644a44ad3d2710e4dfaa87045257a5bd7c0e7e0a363c12893ea77c3d2ee27',
   '57ee749ccff2d5029ccbd10b7ce01320fdeb694bf2d02d5835a0e6ccd5836104',
   (('0.299', 0.299, '12:32-12:37',
     '06162ef141f3a4066bbb35d0ec773002c341ec99f3c3b19a024bf381d5486c27'),
    ('0.587', 0.587, '12:39-12:44',
     '6f17e5a19288943b912be887ac5b4390afbab72c3e2c6786d78d64dd068f285f'),
    ('0.114', 0.114, '12:46-12:51',
     '8af04ca08c0c38d7ad1fb93f89ce44698bbb43bd43ca80060a723dd089806e41'))),
  (9, 'luminance', (0, 'e0', 0, 1), '15:21-15:33',
   'df251d3d8461278afd63b36f1f3cef0d48777196908b8571a11d65dc54b83880',
   '0f4d0fe02d9ee23557db69dfaca7ffa5c2542295d385c0d075f5b7e374fa43ae', 1),
  '8a7f2ac058a23e438f31787c55d235235271429fb79fc1d085c4dd1ba08cd4fc',
  '5586658ce1f621887647e5fb77990606e8637b7d759d2c9f1096f26b7385cd89',
  '9149a7b19b47edea7179f8460443ee67c4a314bcb3ed2a83b7a68d91550f4930',
)
```

Its SHA-256 is the frozen profile-tuple value above.

## Exact helper-local materialization and emission contract

The typed tree remains unchanged. After independently authenticating the exact
profile, declaration, initializer, read/parent closure, functions, whole
program, and interface, the emitter suppresses only the top-level C++
materialization of symbol 7 and emits exactly this ordinary automatic value as
the first statement in function 9 `luminance`:

```cpp
const glsl::Vec3 LUMA_WEIGHTS = glsl::FloatExpr<3>(
    static_cast<float>(0.299),
    static_cast<float>(0.587),
    static_cast<float>(0.114));
```

The exact formatting may follow generator formatting, but code-shape tests
must prove `const glsl::Vec3`, helper-block automatic lifetime, lane order,
literal lexemes, three explicit F32 conversions, existing `FloatExpr<3>`
constructor boundary, and the immediately reachable unchanged
`glsl::dot(rgb, LUMA_WEIGHTS)` use.

There must be no namespace/global, `static`, function-static, thread-local,
`State` field, `main` local, parameter, capture, heap object, lookup, pointer,
reference indirection, array, map, variant, callback, virtual call, dynamic
initializer, or second materialization. The helper value is constructed on
each executed `luminance` call, is never written, and cannot escape.

A diagnostic source-local projection produced 4,469 bytes, SHA-256
`5e8bcfa1c5ca5c06b0eb6371eeeaf77444e698187de1040a9674b3fdd269a9e3`,
and passed C++20 warnings-as-errors syntax. It is not the final generated-block
hash: the generic diagnostic emitter omitted source `const`, while this profile
requires it, and the real identity profile keeps the typed tree unchanged.

## Bindings, resources, fetches, calls, and stack

Bindings and output are exactly:

```text
tileOffset:vec2@1
fullResolution:vec2@2
inputTex:sampler2D@3/S1
smoothType:int@4
threshold:float@5
fragColor:vec4@6
```

There is one sampler, four ordinary uniforms, and one output. The program uses
texture access and no derivatives. It has no loop, array, matrix, struct, UBO,
varying, sampler parameter, non-`in` parameter, recursion, indirect/virtual
call, callback, exception, per-pixel allocation, VLA, or `alloca`. The loop
summary is exactly zero loops, zero unproved, zero depth/product/charge, and an
acyclic call graph.

There are exactly six static `texelFetch` sites and one static
`textureSize(inputTex,0)` site. The `smoothType == 0` path executes texture size
and one fetch, then returns the exact input RGBA. Every nonzero `smoothType`
executes texture size and exactly five fetches: center plus four cardinal
neighbors clamped component-wise to `[0, texSize-1]`. It calls `luminance` five
times. No helper fetch, early exit, other sampler route, or coordinate
orientation is allowed.

The helper-local vector is 12 bytes of fixed value state before optimizer
folding. Preserve Debug/Release/sanitizer `.su` records for `pixel` and
`luminance`; report each static frame and maximum non-inlined chain sum, or
resolve inlining with Release disassembly. Every frame/chain must be static and
below the existing 16 KiB warning threshold. Release disassembly must prove
the five calls inline or remain direct, the three fixed F32 lanes feed `dot`,
and no allocator, dynamic initialization, indirect route, or hidden global
access exists. Binder `State` allocation and external `Surface` storage are not
per-pixel stack.

## Frozen public-factory cases and mutation controls

The JSON contains eight representative public-factory cases:

| Case | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| pass-through modular tiled | `ffaf80acb8db7b255eaf329399e44b5a562a19e82125b19317d436bb07f8fa4b` | `b3fd913a3458127e8f606cdcdd40aa5204835b0219b6feb1e749993a7bd9a8ad` |
| edge modular `smoothType=1` | `af1d4152b362120f0fa863602de3a5a01e4bf59f393f37058e879d8498909469` | `475820bc2a2eaeffb822f1506b7afffcd4aa8cd9eb4a9c442f27f9eab1c9d2b5` |
| edge modular `smoothType=2` | `af1d4152b362120f0fa863602de3a5a01e4bf59f393f37058e879d8498909469` | `475820bc2a2eaeffb822f1506b7afffcd4aa8cd9eb4a9c442f27f9eab1c9d2b5` |
| threshold one ULP below | `c70f0d59488dda2bde1da6463690f63f9d85f22a7ee827dd1bba3f93829adb04` | `66517cf5c7e0d30c1671d3f8d13eea7ab9a83748f82ef4780817cf4b0f30f098` |
| threshold exact | `c70f0d59488dda2bde1da6463690f63f9d85f22a7ee827dd1bba3f93829adb04` | `66517cf5c7e0d30c1671d3f8d13eea7ab9a83748f82ef4780817cf4b0f30f098` |
| threshold one ULP above | `2173d5ef284d8e03867fa476c6cdc4c7ca81948e5244655b7f920b9bbbb84f39` | `7efb4ab7603eea21de958ddfbafc97719d99c62e2c1a63ea1153bfea396dc8a1` |
| single-pixel clamped neighbors | `7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e` | `e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332` |
| asymmetric cardinal lanes | `ffc9c67a9151cfb6b03cb934d9ffb3704a29069cc65e9f3ab91f4535d18fd2ee` | `861c828b629ccf0413f0f4e23f345240720a961d7ca093563523178e30856fdb` |

Every case freezes its input hash/probes, threshold value/F32 bits, full-F32
and RGBA8 output hashes/probes, finite lanes, input immutability, and fresh
double-render byte identity. The pass-through F32 output equals its complete
input byte-for-byte, including alpha. `smoothType=1` and `2` are byte-identical
on the same fixture. The boundary center probe is edge-on for one ULP below and
exact threshold, and edge-off for one ULP above, locking inclusive `step`.

Native tests must reproduce every field exactly in Debug, Release, and
sanitizer builds, including top-down storage, bottom-left fragment coordinates,
clamped neighbors, tile bindings, edge channel order, forced edge alpha one,
and pass-through alpha.

The eleven frozen mutations/controls cover value, type/arity, lane order,
storage/write/lifetime, resolved read/parent, ownership, and F32
materialization:

| Mutation/control | Required result |
| --- | --- |
| each of the three lane values changed independently | diverges |
| red/blue lane order swapped | diverges |
| `vec3` replaced by scalar | diverges |
| observable vec4 extra-lane control | byte-identical, but structurally rejected |
| cross-call mutable write | diverges |
| resolved read replaced by `dot(rgb,rgb)` | diverges |
| exact helper-local F32 materialization | byte-identical and authorized lowering |
| helper-local source-double ordinary array | diverges at frozen boundary cases |
| exact F32 vector owned by `main` and passed to helper | byte-identical, but structurally rejected |

Exact IDs, candidate hashes, changed lanes/bytes, and maximum differences are
normative in the JSON/report. The two observably inert negative controls prove
public output cannot substitute for structural type/arity/owner proof. The
authorized helper-local identity control proves the exact ownership lowering.
Mutation outputs do not authorize any changed value or structure.

## Four-mode loader/profile and forgery matrix

The exact tree/profile matrix is mandatory in loader, validator, and emitter:

| Typed tree | Profile carrier | Result |
| --- | --- | --- |
| exact frozen Smooth Edge tree | absent | reject unsupported top-level global |
| exact frozen Smooth Edge tree | exact profile | accept unchanged; emitter performs exact helper-local materialization |
| forged declaration/read/function/interface tree | absent | reject |
| forged declaration/read/function/interface tree | exact profile | reject structural drift |

Profile application must authenticate exact source/key/defines/tree/profile and
return the same immutable object. Dataclass-equal reconstruction is acceptable
to standalone validator/emitter value authentication; no object-lineage claim
or registry is allowed. Wrong spelling, foreign key, duplicate loader entry,
another source-global/compatibility carrier, or caller-updated hashes reject.

The negative matrix must independently cover:

- corpus revision, source path/raw/normalized bytes, key/runtime key, defines,
  numeric contract, factory/public identity, adapter presence, function order/
  ID/signature/body count, function/whole/interface/profile hash drift;
- missing/duplicate/second global; wrong symbol ID/name/type/storage/
  writability/span; mutable, uninitialized, dependent, computed, scalar-splat,
  wrong-arity, array, matrix, struct, sampler, or nonliteral initializer;
- any literal lexeme/value/type/span/F32 bits changed, lane reordered, lane
  omitted/duplicated/added, constructor kind/type/arity changed;
- missing/duplicate/extra/moved read; wrong owner/path/span/category/symbol;
  wrong `dot` signature/type/parent/argument position or changed `rgb` child;
- assignment, compound assignment, increment/decrement, swizzle/index/member
  write, parameter/return/alias/capture, `out`/`inout` escape, main use, or
  second helper use;
- missing/duplicate/nonconst materialization; namespace/global/static/thread-
  local/State/main/parameter ownership; source-double or non-F32 construction;
  heap/pointer/reference/map/variant/callback/virtual/dynamic initialization;
- altered pass-through, threshold/step, cardinal clamp/direction, fetch,
  texture-size, alpha, output, loop/call graph, allocation, exception,
  recursion, indirect call, or dynamic stack;
- generic source-global/vector-constant capability, another profile key, or
  changes to existing scalar-float/source-global-int profiles.

Loader, validator, and emitter each recompute authority from the exact tree and
frozen profile. One accepting layer cannot launder a forged tree into the next.

## Exclusions, owned files, and generated isolation

Exactly 84 publicly unported programs remain. Exclude every other source
global, scalar/vector/matrix/array/struct constant, mutable or uninitialized
global, Grade induction index, derivative, loop, builtin, ABI, UBO, varying,
sampler-helper, and adapter-backed family. Do not bundle Perlin scalar XOR or
Focus Blur sampler parameters merely because the frontier audit ranks them
next.

After accepted Task 25, implementation may touch only:

```text
tools/glslcpp/frontend/smooth_edge_luma_weights_profile.py  # new exact helper
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
numeric/vector/dot helper, sampler, Surface, corpus, CMake, or unrelated test
edit is authorized. If the exact profile cannot be implemented within this
list, stop for scope review.

Generated isolation requires:

- all 125 accepted Task 25 blocks byte-identical after replacing only
  `typed_[0-9]+` namespace ordinals with one fixed sentinel;
- exactly one new Smooth Edge block at position 77 and exactly one new
  catalog/manifest/header entry;
- no whitespace, comment, literal, factory, ABI, key, manifest, header, or code
  normalization outside necessary namespace ordinal changes;
- exact State/binder ABI with no `LUMA_WEIGHTS` field or binding;
- no namespace/global/static `LUMA_WEIGHTS`; exactly one automatic helper-local
  `const glsl::Vec3` with exact three F32 lanes and one direct `glsl::dot` read;
- exactly six static fetch sites, one texture-size site, exact branch dynamic
  counts, and no derivative/loop/allocation/dispatch/recursion/dynamic stack;
- only owned-file drift and exact final typed/public lists/digests.

## Required verification and completion evidence

Run from `.` with no Git command:

```sh
shasum -a 256 \
  docs/port-engineering/task-26-frontier-audit.md \
  docs/port-engineering/task-26-oracle-generator.mjs \
  docs/port-engineering/task-26-oracles.json \
  docs/port-engineering/task-26-oracle-report.md
node docs/port-engineering/task-26-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
```

Use fresh `/tmp` Debug, Release, and ASan/UBSan build directories, selecting
Ninja only when installed and otherwise Unix Makefiles. Preserve
`-ffp-contract=off`, `-fstack-usage`, and `-fstack-size-section`; enable leak
checking and UBSan `halt_on_error=1`. Build and run full CTest in all three.
Rerun every accepted Task 15-25 oracle/check command.

Mechanically extract only the new namespace. Prove exact helper-local const/F32
code shape, direct `dot`, absence of generated C++ `main`, exact State/binder
ABI, fetch and texture-size counts, and no forbidden global/static/allocator/
container/string/callback/exception/`alloca`/indirect route. Preserve Debug and
Release `.su` files and Release disassembly evidence.

Task 26 is complete only with accepted final Task 25 baseline evidence; all
frozen artifact/source/factory/public/declaration/read/profile/function/whole/
interface/binding/resource/list identities; the full four-mode loader/
validator/emitter and forgery matrices; exact **126/128/84/212** counts; all
eight native full-F32/RGBA8 cases and eleven mutations/controls accounted;
deterministic repeat, immutable input, finite output, threshold/clamp/origin/
alpha behavior; clean Debug/Release/ASan/UBSan/Python/CTest/prior oracles;
bounded stack/disassembly/fetch proof; exact generated isolation; and an
owned-file before/after hash inventory.

This brief stops before design and implementation. If Task 25 acceptance,
profile authentication, public oracle parity, helper-local materialization,
generated isolation, or any exact declaration/read fact cannot be reproduced,
stop for revised independent review. Do not fix forward by exposing generic
source globals/constants, changing the typed IR/runtime/vector DSL, admitting
another key, or broadening the owned-file set.
