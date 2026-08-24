# Task 24 Gather Sorted round-to-int scope and proof brief

> **Status:** frozen read-only scope/proof contract. Stop before design and
> implementation. This file authorizes no repository edit and no Git operation.

**Goal:** add exactly `filter/pixelSort:gatherSorted` by admitting its one
scalar `round` node only at its exact frozen site, where the result is
immediately consumed by the existing `int` constructor and emitted through
the existing clamped `glsl::detail::float_to_int32(...)` helper.

**Profile:** exactly `gather-sorted-round-to-int-v1`. This is an identity
profile: it authenticates the unchanged typed tree and permits exact emission;
it does not rewrite the tree. It adds no unrestricted `round` capability and no
typed-IR proof field.

## Global constraints

- Scope is exactly `filter/pixelSort:gatherSorted`; no sibling Pixel Sort pass,
  Posterize, or other remaining program is admitted.
- Add exactly one loader/profile carrier,
  `gather-sorted-round-to-int-v1`, on exactly this key.
- Do not add `round` to the global approved-capability vocabulary. A foreign,
  second, vector, differently consumed, or moved `round` site rejects.
- Add no type, operator, proof dataclass/field, numeric-literal mode, source
  global, loop rule, safety-cap change, runtime helper, sampler/resource ABI,
  derivative, or general compatibility transform.
- Do not change generic scalar `int(float)` constructor emission. The exact
  Gather profile owns the one site-specific clamped conversion spelling.
- Preserve the existing `glsl-f32` contract, existing Number-compatible scalar
  temporaries, F32 storage/builtin boundaries, and `-ffp-contract=off`.
- Do not edit `glsl::round`, numeric conversion, sampler, Surface, corpus,
  CMake, or another factory to make an exclusion case pass.
- Full F32 and RGBA8 public-factory equality are mandatory; RGBA8-only or
  tolerance acceptance is forbidden.
- No Git, branch, worktree, commit, push, pull request, or deployment.

## Hard Task 23 gate and count projection

Task 24 must not be implemented on the currently inspected accepted Task 22
checkout or on an in-flight Task 23 tree. First require final independent Task
23 acceptance with:

- exactly **122 typed / 124 public / 88 publicly unported / 212 corpus**;
- exact six-key source-global integer/profile identities, existing const-float
  profiles, loop charges, all 19 public-factory cases and 12 mutations;
- the full semantic/generator/emitter forgery matrix, accepted Task 22 gates,
  Debug/Release/ASan/UBSan, stack/disassembly/fetch, generated isolation, prior
  oracles, full Python discovery, and CTest;
- final before/after hashes for every Task 23-owned file and generated output;
- final Task 23 brief SHA-256
  `8aab4f5a9274879f7061c51595bba30f29f02d9606c4f76cf0e1e7312227915f`;
- Task 23 audit/generator/JSON/report SHA-256 values
  `cc49663ed312f95fc3d83cde245a95dc8719a1a90059d750ae9f7b9611061666`,
  `f91ece9510c092e9c0221fc9b326522840c0b10eb3433b858eea3d786f7f57a2`,
  `a832ea550911634dbe2e98e62b51837d8fa57612243416a88f70af69f626c52d`,
  and `8a060f2b74fcc4c7d8ed74ca315b8239a28be0475a57067f3f223667bd009303`.

At Task 24 preflight, record accepted Task 23 hashes for every Task 24-owned
file and generated output. Reparse and rehash Gather Sorted on those final
bytes. If a count, source/profile identity, typed hash, command, generated
block, or accepted interface differs from this projection, stop for revised
review instead of stacking onto drift.

Conditional on that gate:

| State | Typed | Public | Publicly unported |
| --- | ---: | ---: | ---: |
| Accepted Task 23 | 122 | 124 | 88 |
| Task 24 result | **123** | **125** | **87** |

The projected newline-terminated sorted 123-key typed list has SHA-256
`df7750a48a77733e50f0e20072e291c2404e761932f6df8ddbcf8793d58fb6ac`.
After adding only the separately maintained `filter/invert:inv` and
`synth/solid:solid`, the 125-key public list has SHA-256
`bcf196794ff17ec62c1121347b3fe49a0907baa7ce3c3bd51352ec8a51fbac4e`.
Tests must compare explicit lists as well as digests. The final zero-based typed
insertion is exactly 51:

```text
filter/pixelSort:findBrightest
filter/pixelSort:gatherSorted
filter/pixelSort:luminance
```

## Frozen audit and oracle artifacts

| Artifact | SHA-256 |
| --- | --- |
| `task-24-frontier-audit.md` | `fa4e0481ea50534be05923cf2c673b9f45195315121fbac7cbd05bece4f21220` |
| `task-24-oracle-generator.mjs` | `35d20a4428af390ed437f3c829a250a1974d254b66712c900d684d54a7e682d6` |
| `task-24-oracles.json` | `07dd6f31c3e2b5451cbde8fc0ae6f68ec7c3b06cd6296222ac938cdcee37a72a` |
| `task-24-oracle-report.md` | `b33894f0d69c97de5392d686bc9d5b469d672fc59f522b7b79c15604ae4299f6` |

Run `node .../task-24-oracle-generator.mjs --check` before implementation and
at every review gate. `../noisemaker-for-cpu` is pinned
oracle provenance only and must not become a native build, runtime-test,
installed, or generator dependency.

## Exact source, factory, interface, and profile identity

| Field | Required value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Key/runtime key | `filter/pixelSort:gatherSorted` |
| Source | `sources/filter/pixelSort/gatherSorted.glsl` |
| Raw bytes / SHA-256 | 1896 / `a45eb039bae3e7b0a5f804de68c441092b6b7826b594c4aa5221c22a6c7b1386` |
| Normalized bytes / SHA-256 | 1185 / `28e7ad80ef7db266559deb4b822f52251ab899af61feb9f915e32c0ecce079a9` |
| Defines | exactly `{}` |
| Numeric contract | exactly `glsl-f32` |
| Identity profile | exactly `gather-sorted-round-to-int-v1` |
| Canonical/public factory | exact same `canonicalFactory107` function object |
| Canonical/public factory-text SHA-256 | `6f4021f01bc289554506215c3f01d716b4fcbf2b458527d02f1a0888d7eecb7c` |
| Public adapter entry | absent |
| Canonical generated runtime SHA-256 | `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Functions | exactly one, `main` |
| Individual `main` SHA-256 | `89ca9cc42483c88f4351e39338079ab5f742300493815982dff04ece432fba7e` |
| Function-tuple SHA-256, pre and post | `6378f26aa15c43dda1ceba1d098d5b7f7fd76174618bbc5428e6659622cf8218` |
| Whole-program SHA-256, pre and post | `23120c79e838032a4ac54abeac0929d1dc2c7c89c895b083b68e6188b6f36fe3` |
| Interface SHA-256, pre and post | `f18371bad7d92151cd361663a4b56266fffa2228b7b6379ad16518d9af8a8ed6` |

Pre and post hashes are deliberately equal: applying the identity profile must
return the exact same immutable `TypedProgram` object without changing a node,
proof, declaration, resource, interface, or define. Standalone validator and
emitter calls cannot rely on prior object identity; they authenticate the exact
fields and hashes independently.

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

The exact profile tuple is:

```python
(
  'gather-sorted-round-to-int-v1',
  'filter/pixelSort:gatherSorted',
  'a45eb039bae3e7b0a5f804de68c441092b6b7826b594c4aa5221c22a6c7b1386',
  {},
  ('main', (0, 6, 'e0', 0, 0), '24:26-24:66', -38,
   'a5f412a1949fdfae93b759bf1c01a22afb44f9a48e71710f2c54cdcdf312c625'),
  ('int-parent', (0, 6, 'e0', 0), '24:22-24:67',
   'b16eb98c5a1cef7a40f78c65448f5f127c5feaa7cfa64dfdda0e167283aaba3c'),
  ('decl-statement', (0, 6), '24:5-24:68',
   '3c98243330c489b4216d526ba594bac28177a8c3c1f1eb3799528ddbad358ea5'),
  '6378f26aa15c43dda1ceba1d098d5b7f7fd76174618bbc5428e6659622cf8218',
  '23120c79e838032a4ac54abeac0929d1dc2c7c89c895b083b68e6188b6f36fe3',
  'f18371bad7d92151cd361663a4b56266fffa2228b7b6379ad16518d9af8a8ed6',
)
```

Its `SHA256(repr(profile_tuple))` is
`a100420798a4964c67ec4b2e98a09c62e5ca5b3b0d7f2fe1eb7a8ff8180e43fa`.
Caller-supplied hashes are drift alarms, never proof authority.

## Exact round-to-int site

The only admitted expression is `main` path `(0,6,e0,0,0)`, normalized span
`24:26-24:66`:

```text
int(round(brightestXNorm * float(width - 1)))
```

The `round` node is kind `builtin`, scalar `float`, rvalue, callee `round`,
signature `-38`, exactly one scalar-float child, and repr SHA-256
`a5f412a1949fdfae93b759bf1c01a22afb44f9a48e71710f2c54cdcdf312c625`.
Its argument repr SHA-256 is
`a3797427a6fd439f07e4b1a5d33f7f13edcff528e71bee77a80489ae1697761d`.

The immediate parent at `(0,6,e0,0)`, span `24:22-24:67`, is the existing
scalar `int` constructor with exactly the round node as its only child; repr
SHA-256 `b16eb98c5a1cef7a40f78c65448f5f127c5feaa7cfa64dfdda0e167283aaba3c`.
The containing declaration statement path `(0,6)`, span `24:5-24:68`, declares
local writable `int brightestX` symbol 13 and has SHA-256
`3c98243330c489b4216d526ba594bac28177a8c3c1f1eb3799528ddbad358ea5`.

Exactly one round node, exact parent/consumer, and exact declaration are
required. Missing, duplicate, second, vector, reordered, moved, span-shifted,
different-signature/type/category/callee/argument, non-int parent, stored-float,
returned, compared, passed, or foreign-key round rejects. Do not transform to
`floor`, `ceil`, `std::round`, `lround`, `nearbyint`, or a source rewrite.

After authenticating both the `round` node and its immediate `int` parent, the
emitter must spell that exact combined expression as:

```cpp
glsl::detail::float_to_int32(glsl::round(/* authenticated argument */))
```

The outer helper is mandatory. A direct `std::int32_t(...)`, C-style cast,
`static_cast<std::int32_t>(...)`, `convert_lane`, `lround`, or any other outer
conversion spelling rejects. Emission must consume the authenticated parent as
one unit so the child cannot also be emitted independently or accepted through
the generic constructor path. Exact positive and negative code-shape tests must
lock the helper name, nesting, argument count, and absence of a generic cast
change.

The identity-profile application authenticates the complete pre tree and
returns it unchanged. Validator and emitter independently recount all builtins
and authenticate the site, parent, declaration, source/key/defines,
functions/whole/interface, loop proof, and profile carrier.

## Numeric and domain boundary

The pinned public canonical factory executes:

```text
round(brightestXNorm * float(width - 1)) | 0
```

Its runtime `round` is JavaScript `Math.round`: ties go toward positive
infinity and negative results in `[-0.5, 0)` retain negative zero before
integer conversion. The existing native implementation is
`glsl::round(x) -> glsl_round(x) -> floor(x + 0.5)`. Native file hashes are
`src/numeric.cpp`
`a45e878748db2c359511e63d9d1e116995f15ca19e623f234203056e1047b045`
and `src/glsl_runtime.cpp`
`9acbaacc5f7aa0cac10f8ee2c662122aaac11564e82d3ced6d88bb9feaab51f1`.

The authorized observable domain is exact:

- finite `brightestTex.r` in `[0,1]`, including positive and negative zero;
- prepared/output width at least 2 and all dimensions/coordinates within
  signed-int32 bounds;
- therefore round input is finite and in `[0,width-1]`;
- the round result is immediately converted to `int` and never observed as a
  float, so negative-zero sign is erased before use.

Within that domain JavaScript `Math.round(... )|0` and native
`glsl::detail::float_to_int32(glsl::round(...))` have the same observable
integer. The helper's clamp is inactive throughout the normative domain;
`glsl::round` supplies the existing `floor(x + 0.5)` tie rule and the helper
performs the immediate integer conversion. Existing positive and negative
half-value native tests remain unchanged. A Task 24 native oracle must include
exact half boundaries, both signed zeros, endpoints, and width above the
64-sample loop count.

The profile explicitly does **not** claim generic compatibility for NaN,
infinity, negative finite values other than sign-erasure controls, values above
one, dimensions outside int32, or round values outside int32. JavaScript `|0`
wraps large integers modulo 2^32 while the native float-to-int32 helper clamps;
generic negative-zero and out-of-range behavior therefore remains excluded.
Do not alter native conversion/runtime to force the exclusion oracle to match.

## Loop, bindings, resources, fetch, and stack

The existing loop proof is unchanged:

| Field | Exact value |
| --- | --- |
| Loop span | `38:5-48:6` |
| Induction | local `int s`, symbol 19 |
| Start / comparison / update | `0`, `<`, `++` |
| Bound | local `const int NUM_SAMPLES = 64` |
| Bound kind / trips | `local-const-literal` / 64 |
| Lexical/effective depth | 1 / 1 |
| Lexical product / entry charge | 64 / 64 |
| Loop-proof SHA-256 | `c9df47f651e3ee7232826b3bf13ac40e29889e3d69a2d7a2f6dedecba5c579d4` |
| Program proof | 1 loop, 0 unproved, depth 1, product 64, charge 64, acyclic |
| Program-proof SHA-256 | `dd9dc4392ed9350b896854ad13cee5a242281bbe2b791f19b28cd2bd361251ca` |

Task 24 adds no loop/global proof and must not change any proof byte or safety
limit.

Bindings are exactly:

```text
preparedTex:sampler2D@1/S1
rankTex:sampler2D@2/S2
brightestTex:sampler2D@3/S3
fragColor:vec4@4
```

There are no ordinary uniforms, define bindings, source globals, varying,
uniform block, derivative, or helper-function parameters. Prepared and rank
textures match output dimensions; brightest has width at least one and matches
output height. Binding tests must reject each missing/wrong sampler and accept
the exact three plus unrelated extras under the existing binding policy.

Resource accounting is exact: one `textureSize(preparedTex,0)`, three static
`texelFetch` sites, and 66 dynamic fetches per pixel: one brightest fetch, 64
rank-loop fetches, and one prepared-result fetch. There are no conditional
fetch exits. Any other static/dynamic count or texture-sampling route fails.

The source call graph contains only `main`; there are no user helpers,
recursion, indirect/virtual calls, callbacks, exceptions, dynamic allocation,
VLA, or `alloca` in the pixel namespace. Preserve Debug/Release/sanitizer `.su`
records for `pixel`; report its static frame or resolve inlining with Release
disassembly. The frame must be static and below the existing 16 KiB warning
threshold. Release disassembly must show the exact bounded loop and native
`glsl::round` followed by `glsl::detail::float_to_int32`, with no direct
floating-to-int cast, allocator, or indirect route. Binder State allocation and
external Surface storage are not per-pixel stack.

## Frozen public-factory oracles

The normative JSON contains four public-factory cases:

1. normalized positive zero, 9x4;
2. normalized negative-zero sign-erasure control, 9x4, byte-identical to the
   positive-zero output;
3. 9x5 values below, exactly at, and above a half boundary plus normalized
   endpoint controls;
4. width 67 with endpoints and fractional positions, exercising the full
   64-sample sparse search when width exceeds its loop count.

Every case freezes all three F32 input hashes/probes, row values and bits,
full-F32/RGBA8 output hashes/probes, finite lanes, three-input immutability, and
fresh double-render byte identity. Normative output hashes are:

| Case | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| positive zero | `566cc3c05492199a3daf8bdcfffe9f610703f74e74defd5583b7e99f768f4390` | `cf0f9c006514afc91c0d06aa64053f5bab69a226385d6e15afe05f11786e4bf7` |
| negative zero | `566cc3c05492199a3daf8bdcfffe9f610703f74e74defd5583b7e99f768f4390` | `cf0f9c006514afc91c0d06aa64053f5bab69a226385d6e15afe05f11786e4bf7` |
| half boundaries | `66e27bbf10a8708b0fa12a5b3a37b98433cb27409e1b19d75477f026a9074381` | `e0e4181ebf3958dda73bc3f2d1e653d11a86cdcf457029d99875a10a07303f11` |
| width 67 | `156bb977e833e4b09b51a83b2a357dec5baef1608224512c2920b78cd5dfbd43` | `67367ef5cae19cfb7c03d76d63f59e1b26a019531d23f15979c39629a6b57d3c` |

Four normative mutations are frozen:

- `round` replaced by `floor`, required to diverge on half-boundary and wide
  cases;
- `round` replaced by `ceil`, required to diverge below the half boundary;
- the sample loop changed from 64 to 8, required to diverge at width 67;
- native `floor(x+0.5)` plus signed-int32 clamp, required to be byte-identical
  on every normative case.

Two non-normative exclusion cases and three controls freeze the boundary:

- negative half is outside the normalized domain; canonical Math.round and
  native floor-plus-half are identical after immediate int, while a
  `std::round`-away-from-zero model must diverge;
- a huge positive normalized-coordinate violation proves canonical `|0` wrap
  diverges from native signed-int32 clamp.

Exclusion outputs are evidence for closed scope, not native parity acceptance.
A native implementation must not be rejected for the expected out-of-range
divergence or changed to make it match.

## Four-mode, loader, and forgery matrix

The exact tree/profile matrix is mandatory in loader, validator, and emitter:

| Typed tree | Profile carrier | Result |
| --- | --- | --- |
| exact frozen Gather tree | absent | reject unsupported `round` |
| exact frozen Gather tree | exact profile | accept without mutation |
| forged/moved/additional round tree | absent | reject |
| forged/moved/additional round tree | exact profile | reject structural drift |

Wrong profile spelling, profile on a foreign key, Gather with another
compatibility carrier, duplicate loader entry, or caller-updated hashes reject.
The loader application must prove exact source/key/defines/tree/profile and
return the same immutable program object. Reapplication is idempotent only in
the sense of returning the same exact object; it must not add state or a node.

The negative matrix must independently cover:

- source/raw/normalized/key/define/profile/function/whole/interface drift;
- missing/duplicate/extra/vector `round`, changed callee/signature/type/
  category/span/argument, moved site, wrong parent, stored or otherwise
  observable float result, wrong declaration symbol/name/type/storage;
- `floor`, `ceil`, `std::round`, another round spelling, or a direct/generic
  integer-cast spelling substituted for the exact nested helper route;
- altered loop induction/bound/proof/charge, return/break/call-cycle insertion;
- added global, varying, uniform block, derivative, sampler, fetch, output,
  function, array, recursion, allocation, callback, exception, or dynamic stack;
- a capability list containing unrestricted `round` even if the profile is
  also present;
- all exact/forged tree crossed with absent/wrong/exact carrier and attacker-
  recomputed caller hashes.

The generator validator and emitter must each recompute authority from the
typed tree and frozen profile. One accepting layer cannot launder a forged tree
into the next.

## Exclusions

Exactly 87 publicly unported programs remain. Explicitly exclude
`filter/posterize:posterize`: its one scalar round does not qualify because,
after round exposure, it remains blocked by `fwidth` at `80:19`. Also exclude
every other round site, vector round, stored/returned float round, broad builtin
capability, Reindex adapter, literal Vec3 indexing candidates, source-global
aggregate work, derivative family, loop-cap changes, and all other frontier
families.

Do not add runtime signed-zero emulation or JavaScript ToInt32 wrapping. Those
would be separate generic numeric changes requiring broader oracles. Do not
bundle Pixel Sort sibling passes merely because their public API is related.

## Owned files and generated isolation

After accepted Task 23, implementation may touch only:

```text
tools/glslcpp/frontend/gather_sorted_round_profile.py   # new exact profile helper
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

No semantic analyzer, parser, typed-IR, loop-proof, runtime, numeric, sampler,
Surface, CMake, corpus, or unrelated test edit is authorized. If the exact
profile cannot be implemented within this list, stop for scope review.

Generated isolation requires:

- raw-byte identity for accepted Task 23 program blocks 0 through 50, before
  the Gather insertion;
- all 122 accepted Task 23 blocks byte-identical after replacing only
  `typed_[0-9]+` namespace ordinals with one fixed sentinel;
- exactly one new Gather block at position 51 and exactly one new catalog/
  manifest/header entry;
- no normalization of whitespace, comments, literals, factory names, code,
  keys, manifests, headers, or any token besides namespace ordinals;
- exact
  `glsl::detail::float_to_int32(glsl::round(/* authenticated argument */))`
  at the one authenticated parent/site, the unchanged 64-trip loop, three
  fetch sites, and no direct float-to-int cast, allocation, dispatch,
  recursion, or dynamic-stack construct in the namespace;
- only owned files and three generated outputs differ from accepted Task 23.

## Required verification and completion evidence

Run from `.` with no Git command:

```sh
shasum -a 256 \
  docs/port-engineering/task-24-frontier-audit.md \
  docs/port-engineering/task-24-oracle-generator.mjs \
  docs/port-engineering/task-24-oracles.json \
  docs/port-engineering/task-24-oracle-report.md
node docs/port-engineering/task-24-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
```

Use fresh `/tmp` Debug, Release, and ASan/UBSan build directories, selecting
Ninja only when installed and otherwise Unix Makefiles. Preserve
`-ffp-contract=off`, `-fstack-usage`, and `-fstack-size-section`; enable leak
checking and UBSan `halt_on_error=1`. Build and run full CTest in all three.
Rerun every accepted Task 15-23 oracle/check command.

Extract only the Gather namespace. Mechanically prove one `glsl::round`, one
outer `glsl::detail::float_to_int32`, their exact nesting with no direct or
generic floating-to-int cast, one 64-trip loop, three static fetch sites, one
texture-size call, exact State/binder ABI, no generated C++ `main`, and no
forbidden allocator/container/string/callback/exception/`alloca`/indirect
route. Preserve `.su` and Release disassembly evidence.

Task 24 is complete only with accepted Task 23 baseline evidence; all frozen
artifact/source/factory/public/site/profile/function/whole/interface/loop/
binding/resource/list identities; the full four-mode loader/validator/emitter
forgery matrix; unchanged capability vocabulary without `round`; exact
123/125/87/212 counts; all four full-F32/RGBA8 native cases and four normative
mutations; correct treatment of signed-zero and out-of-range exclusion
controls; deterministic repeat, immutable three inputs, finite output; clean
Debug/Release/ASan/UBSan/Python/CTest/prior oracles; bounded stack/disassembly/
fetch evidence; exact generated isolation; and an owned-file hash inventory.

This brief stops before design and implementation. If final Task 23 drift,
public oracle parity, domain assumptions, or exact profile authentication fail,
stop for revised independent review. Do not fix forward by exposing generic
round, altering numeric conversion, expanding domains, adding derivatives, or
admitting another key.
