# Task 25 Literal Vec3 Lane Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.
>
> **Status:** implementation design only. This document authorizes no
> repository edit and no Git operation.

**Goal:** Add exactly Lens Distortion and Prismatic Aberration to the typed
public CPU catalog by replacing eleven authenticated literal `vec3 hsv` lane
indexes with fixed one-lane swizzles.

**Architecture:** A per-entry string carrier authorizes a closed pre-tree
authenticator, one deterministic eleven-site transformation, a transition
identity check while both trees coexist, and independent value-structural
post-tree authentication in the validator and emitter. Existing
`glsl::swizzle<I>` reads and `glsl::set_swizzle<I>` writes perform all native
work; no generic index capability, runtime subscript, registry, proof field,
or runtime helper is introduced.

**Tech Stack:** Python frozen dataclass typed IR and generator, generated C++20
CPU kernels, existing GLSL runtime/swizzle DSL, C++ native tests, Node-derived
canonical oracle package, CMake/CTest, ASan/UBSan, `.su` stack records, and
ARM64 Release disassembly.

## Global Constraints

- Scope is exactly
  `classicNoisedeck/lensDistortion:lensDistortion` and
  `filter/prismaticAberration:prismaticAberration`, exact empty defines, and
  profile `literal-vec3-lane-index-v1`.
- Transform exactly eleven sites: Lens 8, Prismatic 3; six direct plain-`=`
  writes and five reads; lane incidence `0/1/2 = 7/3/1`.
- Do not add `index`, vector indexing, dynamic indexing, or another broad name
  to the capability vocabulary. Do not admit `filter/grade:lut`.
- Add no typed-IR type or field, proof dataclass, parser/semantic rule, loop
  proof, global proof, numeric mode, runtime helper, sampler behavior,
  derivative, compatibility transform, allocation, or CMake dependency.
- Preserve `glsl-f32`, Number-compatible scalar temporaries, F32 storage and
  builtin boundaries, bottom-left sampling, and `-ffp-contract=off`.
- Acceptance is exact full-F32 and RGBA8 equality. Tolerances and RGBA8-only
  acceptance are forbidden.
- No Git, branch, worktree, commit, push, pull request, deployment, or edit
  outside the frozen owned-file list.

---

## 1. Decision and completion target

The final catalog is exactly **125 typed / 127 public / 85 publicly unported /
212 corpus**. Tests compare explicit sorted lists as well as these frozen
newline-terminated digests:

| List | SHA-256 |
| --- | --- |
| 125 typed keys | `9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4` |
| 127 public keys | `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab` |

Zero-based final typed positions are Lens 2, Gather Sorted 52, and Prismatic
59. Their exact neighbor triples are:

```text
classicNoisedeck/composite:composite
classicNoisedeck/lensDistortion:lensDistortion
classicNoisedeck/refract:refract

filter/pixelSort:findBrightest
filter/pixelSort:gatherSorted
filter/pixelSort:luminance

filter/plasticWrap:pwSpec
filter/prismaticAberration:prismaticAberration
filter/reindex:nmReindexApply
```

The implementation does not expose any index expression. It changes the two
authenticated typed values before validation so the ordinary validator and
emitter see only fixed swizzles. Every other indexed program, especially Grade
LUT's twenty induction-indexed sites, remains rejected.

## 2. Immutable preflight and hard stop

Before any repository edit, authenticate these inputs:

| Input | Required SHA-256 |
| --- | --- |
| Amended Task 25 brief | `193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2` |
| Task 25 frontier audit | `e754d9e02e3d98069297dda9f2c8071d25ba2347ddd812af0c41dc74b82e7d27` |
| Task 25 oracle generator | `3594cd9f0a82e7a21e662f8897f43eac0c86943b15ca36b2a0d3d0f805b2772c` |
| Task 25 oracle JSON | `09d8d8a9667fe3b3b90cd582e501b7c0a61d2a41e65ea2d175771a105e32e116` |
| Task 25 oracle report | `f72b69688d9a2f10df1603d1a012f6df8d0834f012438386038637630eb20611` |
| Accepted Task 24 implementation report | `3a9d0086141061ed54a894a42ae4508cc32e483cb531361a212747a345315f0e` |
| Accepted Task 24 final review | `f6e7e6158a5a3f7bf03a2c99bcc6e5baa6e27d9c567c453f4ff7e4a2bdec7d0a` |

Run the Task 25 oracle generator with `--check`. Confirm corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, exact **123/125/87/212**
starting counts, Gather at position 51, and a clean accepted Task 24 suite.
Capture the three accepted generated outputs before editing for isolation.

The Task 25-owned starting inventory is:

| Path | Accepted Task 24 SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/literal_vec3_lane_index_profile.py` | absent; Task 25 creates it |
| `tools/glslcpp/generate_typed_slice.py` | `a227a0119144f4572aa8628748432d43606742ec170651ed1bd493ef19f58d1f` |
| `tools/glslcpp/emit_typed_cpp.py` | `5beff60a0342a054abff3a975641782dcbcb14116dca9c3ba7ca408b3ffa371e` |
| `tools/glslcpp/typed_slice.json` | `e6a0bbe1cc1caef06d726e7040fcb8b1a205593d30885625aad6460e96b4747a` |
| `tests/test_typed_generator.py` | `8d653a85681f519c3e3c950330239019475de9740ca2bc0d836a1a159afc2698` |
| `tests/test_generated_kernels.cpp` | `ae903b176ac6bd38072f41940fb80df53ad957e1c9e1c3713464181450a54f79` |
| `tests/test_typed_slice.cpp` | `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6` |
| `src/typed_generated/typed_slice.cpp` | `8d06f5864fbb6eca1eb205afc4f9690ec8f0ddd90a384e4f84a80fc50a0c3ea6` |
| `src/typed_generated/typed_manifest.json` | `bf7020628f988acd61128c527495e609cba7e74ee41bc44bfec7053bcd1187b5` |
| `include/noisemaker/generated/catalog.hpp` | `1ca4f356117d2067bb766b630d44e6c4075a3da60ac365f5f6b6a48b7d77d105` |

Stop for review on any mismatch. Do not regenerate or fix forward on a
different baseline.

## 3. Exact source, tree, and site authority

The profile module owns this per-key identity table:

| Identity | Lens | Prismatic |
| --- | --- | --- |
| Raw bytes/hash | 8269 / `f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444` | 4247 / `513eac95fdf7f67a6839ee5d96e5bbfd76b6cfa62d3254df6fed23d8effe380e` |
| Normalized bytes/hash | 7723 / `6586c49b079a3b0f4aa3538c8e735e70db088ff2e5d2ea1037e9e9c5486fdf52` | 3907 / `1c157e7f3dc7c9c122cc185812cd2988a98a52024055a482265bded7561a0860` |
| Functions/main ID/body | 8 / 38 / 25 | 5 / 22 / 31 |
| Main pre/post hash | `dc6d4d2a3b5c50598a879dc6679553b3f89d964a19f5d4c79716970a7f2493ee` / `8de6658184c69cb679f0453e37e37f538eebabb0e14f720d1eeea61e715d30ec` | `416ffbaef2ada8e19fb0f161034a964d4fcfd88c8b2e34fe4f66c1b415a70e56` / `f0d3926e68fcb9c4672779fa36c363d9471240395f36e2857146225e5a87187f` |
| Function tuple pre/post | `263870c469a9dc3b1f4d5f3a2498864c6da4ff4eaf2cc3efaf198376e4d304c1` / `c166fa2b38ec68661fb4d73be1bfb3eef4f879da7d82dbfca44deba1b651a756` | `6949577823e5eccde21335182d379a590db90188f004f3d479503ac33990cf24` / `80fb20a869a84f8c23942fab3b033e554e48c5e5dda2097eb8dbd346a1c758fd` |
| Whole pre/post | `f63fb6dba6626791c248501bcfc5ca1c94f073a0593f34dbe846056fe35c81f5` / `e5dbb049717ce77ba79a36c6ea39ddde88e561df1ba06c98fba0ddd179a63d2e` | `fdc004aa9e36925670b4a33446690150a81ed8b13ffba4aed1b944b2d80b997c` / `1a808ce2ca4aae60be185b04ac96078521db41bcb04d5bb0e9cdb7552f6d482c` |
| Interface pre/post | `53e759b54c0710d9cb3375cc2353878abebec06b378aeaaf9d745c6ecfd2b4ca` | `788b0390952c998db1945320c681f114bcbc150fe1f91738894f77a6220df010` |
| Diagnostic C++ | 27,446 / `6cfa9d58cbc096b7372b00b17b4ed0b146236a4738acef7870cad05593a57fc5` | 13,316 / `8d6c98fed4ab2d2a2130566081386cdfb74d01ae84c11b198a1be08ae187155f` |
| Profile tuple hash | `d1235bb6045a5795c4c10c5db8a990f51ee42e5541dcfa7a663c91f3245d10d3` | `25ad8a580a8263b4d2d15b41eb783abeed3433c94b9c8fffbbae2546300fd6b2` |

Use the brief's exact `repr` serialization for function tuple, whole program,
and interface. Caller hashes are drift alarms only; independently hash retained
raw and normalized source.

The ordered site table is exact:

| Key | Path | Span | Lane/role | Pre hash | Post hash |
| --- | --- | --- | --- | --- | --- |
| Lens | `(18,'s0','s3','e0',0,0)` | `236:9-236:15` | 0/write | `8b56c4f52b2113fa843aeb30133f38a488eda92edca236b9260285e426c632a3` | `1d9ee202f7c93a030803d2c61782ef959a8ef56fc8890b39de56bfe6cb2df13b` |
| Lens | `(18,'s0','s3','e0',0,1,0,0,0,0)` | `236:24-236:30` | 0/read | `1cc773177b9c87d54bd4289dd97c6384f43c0619d1c29a1b5cf1a09a2225a9e6` | `c7daed1dbf0ebc39669fa33212fa1d9b3233fbe7112e07c05ebeaa05a9120920` |
| Lens | `(18,'s0','s3','e0',0,1,0,0,1,0,0)` | `236:65-236:71` | 0/read | `27987cf202ec44e367f3edbacf025685a95a579d3bd1766ed007f3a39fba0233` | `689cb485e1d153df4ba2f46f52e10f7843c818cf111cbdf6d79aa26419f9f69a` |
| Lens | `(18,'s0','s4','e0',0,0)` | `237:9-237:15` | 1/write | `e67ab422ce4f28337e56fef80f8bfb4dbd93a1bbe30eb0165c0aa3cc7dc6cb44` | `829b7f013b6ca2c1cbf03eb25079f7a02ec32731eb0bb8d8015dbfa77152e16b` |
| Lens | `(18,'s1','s3','e0',0,0)` | `247:9-247:15` | 0/write | `92be124aed858e61dff4316731b67be8a46a881c527285b56263477b81193f12` | `0ee30fa6b2497642b0b1b2cbb0fe9fee6fc7594191d410f3ff2b20f7ba6c8243` |
| Lens | `(18,'s1','s3','e0',0,1,0,0,0,0,0)` | `247:26-247:32` | 0/read | `af51ced1d6aafe987b1914573554213afb0c123619134749a44fdb603d08b818` | `d3a7a9840bbe6523a9038c402537928e10b5abaca692762a7b8947f821f4add0` |
| Lens | `(18,'s1','s4','e0',0,0)` | `248:9-248:15` | 1/write | `569c4bc0beead7e391d0bddbcfe03fb78b78286f8bb00754eb37bfa5bc1720de` | `2c94a065f64b606da19073ffe0afd554d57c9222714af12c034b37f90a6b192a` |
| Lens | `(20,'s1','s0','s0','e0',0,1,0,0,0,1,0)` | `260:46-260:52` | 2/read | `e2faad5610537f7e86b817e16c093b165a4d4d84bac84799bfc055f3de262fea` | `96a5a6b39df3fba890e8286278615e6518ec77b6c9d440f9e315bdc70d596250` |
| Prism | `(26,'e0',0,0)` | `131:5-131:11` | 0/write | `2637ccd727e74a3b5583230bf07d8ceed92e72dfc4434041075f90515950f23d` | `2c240e9eae37323e092e20ac3d21e7382fcd86b7160b8f041cc3a2eb9cb7bdeb` |
| Prism | `(26,'e0',0,1,0,0,0,0,0)` | `131:22-131:28` | 0/read | `9af4f5115d7b784cac89bd118123e8b0935194c93b970da62f01541590b17ce2` | `94558e9138e38ceb285c1746af1473ca77f5f56ef564626edaad0be6546d6072` |
| Prism | `(27,'e0',0,0)` | `132:5-132:11` | 1/write | `155a0535e006b5b61f14d842415d9bba0633f15d905e7fbf8944ff847f5685f2` | `8e585f401b1450e2f7c58dd3fada71b23f0cb2b4e85f7e75c6371459db863306` |

Lens sites resolve only to automatic writable `vec3 hsv` symbol 72;
Prismatic sites resolve only to symbol 55. A pre site is exactly `index`,
scalar float lvalue, with direct `id` base and scalar int rvalue literal lane.
Only child zero of plain `assign` operator `=` is role `write`; all other sites
are `read`. A complete program walk must find exactly these 8/3 indexes and no
unselected index.

## 4. Profile module and deterministic transition

Create `tools/glslcpp/frontend/literal_vec3_lane_index_profile.py`. Do not add
a dataclass or typed-IR proof field. Its public interface is:

```python
PROFILE = "literal-vec3-lane-index-v1"
LENS_KEY = "classicNoisedeck/lensDistortion:lensDistortion"
PRISMATIC_KEY = "filter/prismaticAberration:prismaticAberration"
KEYS = (LENS_KEY, PRISMATIC_KEY)

def authenticate_literal_vec3_lane_index_pre(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> tuple[TypedExpression, ...]:
    """Return the exact ordered pre-index site objects."""

def authenticate_literal_vec3_lane_index_post(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> tuple[tuple[TypedExpression, int, str], ...]:
    """Return exact ordered (post swizzle, lane, role) value authority."""

def authenticate_literal_vec3_lane_index_transition(
    before: TypedProgram,
    after: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> tuple[tuple[TypedExpression, int, str], ...]:
    """Require the exact value rewrite and retained pre base identities."""

def apply_literal_vec3_lane_index(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> TypedProgram:
    """Authenticate pre, rewrite all sites once, authenticate transition/post."""
```

The pre and post authenticators independently require exact carrier, selected
key, caller/raw/normalized hashes, `{}` defines, `glsl-f32` metadata at their
callers, body status, main ID/count/hash, function/whole/interface hash,
declarations, resources, builtin symbols, no loop, acyclic call graph, exact
site table, and per-key profile tuple hash. Resolve the frozen paths directly,
then perform an independent whole-program census. Searching for the first
matching index or swizzle is forbidden.

`apply_literal_vec3_lane_index` authenticates the entire pre value, then walks
`main` once. It maps each path to one row and replaces only the matching node:

```python
replacement = dataclasses.replace(
    site,
    kind="swizzle",
    children=(site.children[0],),
    member="xyz"[site.children[1].literal_value],
)
```

The walk must report exactly 8 or 3 replacements. It creates one new `main`,
one new function tuple, and one new `TypedProgram`; every non-main function is
both dataclass-equal and object-identical. Source, declarations, resources,
interface, defines, counted-loop summary, and optional proof fields remain
equal and preferably identical. Reapplication and an already transformed tree
fail pre authentication.

The transition authenticator holds both trees and requires, per row,
`post.children[0] is pre.children[0]`. It also checks that only `kind`,
`children`, and `member` changed and that all frozen post hashes match. A test
transition that dataclass-clones one base must fail here.

Standalone post authority deliberately does not claim process-local lineage.
A dataclass-equal reconstructed post tree is accepted by validator/emitter
when all observable values and hashes are exact. Do not add a registry, side
table, token, carrier object, proof field, or IR field to remember lineage.

## 5. Loader and generation-driver plumbing

The two selected `typed_slice.json` entries have exactly these carriers:

```json
[
  {
    "defines": {},
    "literal_vec3_lane_index_profile": "literal-vec3-lane-index-v1",
    "program_key": "classicNoisedeck/lensDistortion:lensDistortion"
  },
  {
    "defines": {},
    "literal_vec3_lane_index_profile": "literal-vec3-lane-index-v1",
    "program_key": "filter/prismaticAberration:prismaticAberration"
  }
]
```

Gather retains its separate `gather_sorted_round_profile`; all other records
retain the existing two fields. `load_slice` requires exactly two lane-profile
records in sorted key order, exact profile spelling, exact `{}` defines, no
duplicate/foreign/Grade-LUT carrier, no simultaneous compatibility carrier,
and exactly 125 sorted unique programs. The global capability, type, operator,
compatibility, numeric-contract, and define maps remain byte-for-byte equal.

The generation order is:

```text
parse/analyze exact source
-> apply existing compatibility and proof passes
-> read only the per-record lane-profile carrier
-> apply_literal_vec3_lane_index(pre, source_hash, carrier)
-> require returned object is not pre and pre/post transition authenticates
-> validate_capabilities(post, ..., literal_vec3_lane_index_profile=carrier)
-> render_typed_cpp(post, ..., literal_vec3_lane_index_profile=carrier)
```

No carrier enters the typed IR or generated manifest. Each new manifest row
uses the existing schema with exact key/source hash, `{}` defines, `glsl-f32`,
`none` compatibility, and its generated factory.

## 6. Independent validator and emitter authority

Extend `validate_capabilities` with only:

```python
literal_vec3_lane_index_profile: str | None = None
```

A present carrier requires a selected key, no compatibility transform, and
`glsl-f32`, then calls the post authenticator independently. A selected key
without the exact carrier must fail at the end even though fixed swizzles are
ordinary approved constructs. Pre trees with absent carriers reach the
existing unsupported-index rejection; pre trees with exact carriers fail post
authentication. Do not add an index capability or special index case.

Extend `_Emitter` and `render_typed_cpp` with the same keyword. Add one
non-init field, explicitly initialized before optional authentication:

```python
authorized_literal_vec3_lane_sites: tuple[
    tuple[TypedExpression, int, str], ...
] = field(init=False, default=())
```

`_Emitter.__post_init__` rejects wrong key/profile/source/numeric/compatibility
metadata and independently calls the post authenticator. A selected key with
no carrier rejects. Existing nonselected emitters keep an empty tuple,
including test-local `_Emitter` instances built with `object.__new__`.

Use identity only to select the already value-authenticated post nodes inside
that one emitter invocation:

```python
def _literal_lane_site(self, value):
    return next((row for row in self.authorized_literal_vec3_lane_sites
                 if row[0] is value), None)
```

Before generic swizzle emission, an authorized read must have role `read` and
emits exactly `glsl::swizzle<I>(hsv)`. In `lvalue`, an authorized write must
have role `write` and returns the existing `(hsv, "I")` result; the unchanged
plain-`=` statement branch emits exactly
`glsl::set_swizzle<I>(hsv, rhs)`. Reject a selected write visited as a read or
a selected read visited as a write. Non-profile swizzles use byte-identical
generic code.

This is site-owned use of existing fixed-swizzle emission, not a new runtime
path. The RHS is evaluated once before `set_swizzle`; existing
`convert_lane<float>` preserves the Float32Array storage boundary. The Lens
line-260 read emits one `glsl::swizzle<2>(hsv)` as the scalar input of the
existing vec3 splat, even though the canonical JavaScript text expands it
three times.

## 7. Four-mode and full forgery matrices

Exercise loader application, direct validator, and direct emitter separately:

| Mode | Tree | Carrier | Required result |
| --- | --- | --- | --- |
| 1 | exact pre-index | absent/wrong | application rejects; direct layers reject unsupported index/profile |
| 2 | exact pre-index | exact | application returns exact post; direct validator/emitter reject missing post authority |
| 3 | exact post-swizzle value | absent/wrong | direct validator/emitter reject missing/wrong authority |
| 4 | exact post-swizzle value | exact | validator/emitter accept, including dataclass-equal reconstruction |

At each boundary use literal Cartesian tests, not representative sampling:

- every forged pre tree × absent/wrong/exact carrier × exact/missing/wrong/
  attacker-recomputed caller hash at the application boundary;
- every forged post value × the same 3 carrier modes × 4 caller-hash modes at
  validator and emitter independently;
- exact pre/post controls across the same matrices with only the documented
  mode accepting.

Every mutation asserts its exact target path/count/precondition before the
expected rejection. Cover independently:

- source revision/path/raw/normalized/key/runtime key/defines/numeric/factory/
  adapter/function order/ID/signature/body/function tuple/whole/interface/
  profile drift;
- zero, ten, twelve, reordered, moved, duplicated, partial, additional, or
  twice-transformed sites and wrong path/span/pre/post hash/base/index/parent/
  lane/role;
- base name/ID/type/storage/writability, alternate local, parameter, global,
  uniform, vec2/vec4/integer vector, array, matrix, struct, or sampler;
- non-int, nonliteral, uniform, induction, negative, lane 3, effectful, nested,
  delayed-lvalue, aliasing, escaping, `out`/`inout`, callback, pointer, and
  runtime-subscript index forms;
- read converted to direct write, write converted to read, compound assign,
  prefix/postfix update, wrong RHS ordering, and line-260 nonsplat use;
- post kind/children/member/type/category/span changes and non-site function,
  declaration, interface, proof, or resource changes;
- loop/global/array/derivative/sampler/fetch/output/function insertion,
  recursion, allocation, exception, indirect call, callback, and dynamic
  stack fixtures with authentic controls at their actual parser/semantic/
  validator boundary;
- capability vocabulary containing any index spelling, missing/extra/
  duplicate/unknown capability, Grade LUT borrowing the carrier, either one of
  the two required loader entries missing, and another compatibility carrier.

The cloned-base negative belongs only to the transition boundary while both
trees exist. Post-only layers accept a dataclass-equal clone by design and
still reject every observable value difference. Never represent a parser- or
semantic-bound construct merely by appending a comment to `raw_source`.

Patch analyzer output inside driver tests to ensure `generate_outputs` rejects
forged pre/post states rather than laundering them through a helper. Snapshot
all repository generated bytes before and after every negative/temp-native
test.

## 8. ABI, resource, call, and code-shape proof

Lens bindings are exactly one sampler, twenty ordinary uniforms, and one
output in the order and IDs frozen in the brief. Prismatic is exactly one
sampler, ten ordinary uniforms, and one output. Tests must compare the complete
explicit binding tuples, not counts alone. For every required entry, omit it
and supply a wrong typed alternative; both reject at bind time. Exact bindings
and exact bindings plus unrelated extras accept under existing policy.

Typed and generated mechanical audits require:

| Property | Lens | Prismatic |
| --- | ---: | ---: |
| Static/dynamic texture samples per pixel | 3 / 3 | 3 / 3 |
| `textureSize(inputTex,0)` calls | 0 | 1 |
| Loops | 0 | 0 |
| Derivatives | 0 | 0 |
| Source globals/arrays/matrices/structs/UBOs/varyings | 0 | 0 |

Derive dynamic texture counts from three straight-line authenticated static
sites and absence of loops/conditional exits. Mutation tests remove/add a
sample, change its sampler role/coordinates, add/change texture-size LOD,
insert an early exit, and alter resources; the mechanical audit must fail.

Extract only the two generated namespaces and require exactly six selected
`set_swizzle<I>` writes and five selected `swizzle<I>` reads in main according
to the site table. Count the line-260 scalar read once. Require zero
`operator[]`, runtime lane integer/switch/bounds code, pointer selection,
lookup table, `std::variant`, allocator/container/string/callback/exception/
`alloca`, indirect/virtual dispatch, recursion, dynamic stack, or generated
C++ `main`.

The source call graphs are acyclic. Lens has `map`, `hsv2rgb`, `rgb2hsv`,
`hsv2rgb2`, `rgb2hsv2`, `saturate`, `_distance`, and main; reachable main
chains include `_distance -> map`, `saturate -> map`, `rgb2hsv`, and
`hsv2rgb`. Prismatic has `map`, `hsv2rgb`, `rgb2hsv`, `saturate`, and main;
reachable chains include `saturate -> map`, `rgb2hsv`, and `hsv2rgb`.

## 9. Canonical native oracle and temporary mutation harness

Run the pinned generator first and treat
`task-25-oracles.json` as the exact field-level source. Embed one delimited,
machine-parseable Task 25 table in `tests/test_generated_kernels.cpp`; a Python
test parses it and compares case/mutation order, keys, dimensions, tile/full
resolution, time, every uniform and F32 bit, input hash/five probes, output
F32/RGBA8 hash/five probes, finite count, repeat/immutability flags, mutation
IDs/roles/lanes/generated-occurrence count, candidate hashes, and every
byte/lane/max-difference metric to the pinned JSON. The native executable is
hermetic and never reads `/tmp` or noisemaker-for-cpu.

The six production cases are:

| Case | Size | Output F32 SHA-256 | Output RGBA8 SHA-256 |
| --- | --- | --- | --- |
| `lens-chromatic-add-static` | 11x7 | `40ec6e6bcca21c55b0abe81eca5760b2e623aad76678b49b070d350d0fe49948` | `de4b64895586ce7dc92352820b5c64d5660dc1d722bd8c5392e42568385ec4b8` |
| `lens-chromatic-alpha-modulated` | 10x8 | `3c4ff034284a714a545a35106c98e7d93398fb800f7bee2dbccffb08592a5e61` | `18b8e022320da7b278ae2935b8602f50ebcf30cfc1e5eb058e932f8d05666ada` |
| `lens-prismatic-add-static` | 9x9 | `0ed06880cce85cebb134fbc0cb2b5710a4a3e08dc336512e31cbaf2a5ec77688` | `204fe8f73e191091c231f159d147cb10df17b9bc88abc44c6baa75da7684b05e` |
| `lens-prismatic-alpha-modulated` | 12x6 | `7fe6ac9ba3bf66f5f3f747f635b6ce5bd9d7e1d184678a74ba1d69cc14b18b76` | `4b8ffb755c45fa8b37e686ff71fd61f66c120eeaf2644b6d871e01b6a728521b` |
| `prism-static-origin-tile` | 10x7 | `daad9591d01855520a052fd2d89ed2e9ed32da2d93421a041e40d58b5389daff` | `5f73c9a1151a312569107b68abd705555f7d2c5540c8e3ea44abd7891a9a3640` |
| `prism-modulated-offset-tile` | 9x6 | `dbc929af7ba49e768bd39a0188e0f9b9426581ba564c856e6289531304c8b216` | `5f141b94b43d85418de325137173a181d705f50574f4d1ca78e01972a1044447` |

Construct the exact deterministic modular F32 input from the oracle generator.
For each case snapshot input, bind through the public catalog factory, render
twice fresh, and require exact full F32/RGBA8 bytes, all probes, finite lanes,
input immutability, top-down storage, bottom-left fragment origin, clamping,
tile/full-resolution behavior, and alpha.

The eleven one-site mutations are, in frozen order:

| ID | Source lane -> wrong | Active cases | Max F32 lanes / RGBA8 bytes |
| --- | --- | --- | ---: |
| `lens-236-write-lane0-to-lane1` | 0 -> 1 | two chromatic | 20 / 20 |
| `lens-236-first-read-lane0-to-lane1` | 0 -> 1 | two chromatic | 24 / 24 |
| `lens-236-second-read-lane0-to-lane2` | 0 -> 2 | two chromatic | 20 / 20 |
| `lens-237-write-lane1-to-lane2` | 1 -> 2 | two chromatic | 231 / 231 |
| `lens-247-write-lane0-to-lane1` | 0 -> 1 | two prismatic Lens | 180 / 179 |
| `lens-247-read-lane0-to-lane1` | 0 -> 1 | two prismatic Lens | 175 / 172 |
| `lens-248-write-lane1-to-lane2` | 1 -> 2 | two prismatic Lens | 216 / 215 |
| `lens-260-read-splat-lane2-to-lane1` | 2 -> 1 | two alpha Lens | 206 / 206 |
| `prism-131-write-lane0-to-lane1` | 0 -> 1 | both Prismatic | 122 / 119 |
| `prism-131-read-lane0-to-lane1` | 0 -> 1 | both Prismatic | 133 / 131 |
| `prism-132-write-lane1-to-lane2` | 1 -> 2 | both Prismatic | 158 / 157 |

For each mutation, first resolve and hash the exact post site, change only its
member to the frozen wrong lane, and prove production validator and emitter
reject under the exact carrier. Only then may a test-only emitter bypass
`__post_init__`; it must initialize every cache, including empty Gather and
lane-profile authorization fields, from the mutated program.

Compile the two canonical post namespaces and all eleven uniquely named wrong
post namespaces once in a fresh temporary directory with `-ffp-contract=off`.
Run every active case and compare candidate F32/RGBA8 hashes and complete
same/different byte/lane/max-absolute metrics field-for-field to each JSON
`case_results` record. Inactive branch cases must remain exact baseline. The
line-260 mutation changes one C++ source swizzle/splat site while matching the
three expanded JavaScript occurrences. Assert repository generated output,
manifest, header, catalog, and installed library bytes are unchanged before
and after the harness.

## 10. Generated isolation and catalog gates

Generation adds exactly two blocks, two manifest rows, two catalog rows, and
two header declarations. Reconstruct the accepted Task 24 123-program spec in
memory and generate both baselines without writing repository bytes.

- All 123 prior blocks are byte-identical after replacing only
  `typed_[0-9]+` namespace ordinals with one sentinel.
- Lens is the only new block at position 2; Prismatic is the only new block at
  position 59; Gather changes ordinal only from 51 to 52.
- Prior manifest records remain structurally identical except the existing
  monolithic output hash; only the two new records appear.
- Header/catalog explicit key/factory lists gain exactly the two sorted rows.
- Each normalized new namespace equals its frozen diagnostic projection:
  27,446 bytes / `6cfa9d58cbc096b7372b00b17b4ed0b146236a4738acef7870cad05593a57fc5`
  for Lens and 13,316 bytes /
  `8d6c98fed4ab2d2a2130566081386cdfb74d01ae84c11b198a1be08ae187155f`
  for Prismatic.
- No prior whitespace, comment, literal, ABI, factory, key, manifest field, or
  code is normalized.

The public catalog test becomes exactly 127 sorted unique keys. Grade LUT and
an adjacent unported key remain absent. General unported and historical Task
15-24 count tests must use current 125/127/85/212 only where they test current
state; historical isolation tests reconstruct their old slice explicitly and
retain their historical digests.

`tests/test_typed_slice.cpp` currently has no Lens/Prismatic exclusion and is
expected to remain byte-identical at its Task 24 hash. Change it only if an
actual stale assertion is proven; do not add duplicate Task 25 fixtures there.

## 11. Stack, disassembly, and complete verification

Use fresh `/tmp` Debug, Release, and ASan/UBSan directories. Preserve
`-ffp-contract=off -fstack-usage -fstack-size-section`. Run full CTest in all
three. Request leak detection; if Apple's runtime reports LeakSanitizer
unsupported, record that exact diagnostic and rerun with `detect_leaks=0`,
ASan halt, and UBSan halt/stacktrace.

Preserve `.su` records for both `pixel` functions and every reachable helper.
Report each static frame and maximum non-inlined call-chain sum; all must be
static and below 16 KiB. Treat sanitizer dynamic frames as instrumentation,
not production static proof. Resolve inlining with Release disassembly.

Scoped Release disassembly must prove fixed lane loads/stores with no runtime
lane switch/bounds branch/subscript, three sample calls per pixel, Prismatic's
one texture-size call, acyclic direct helper calls, and zero `blr`/`br`
indirect branch, allocator/deallocator, exception, `alloca`, VLA, recursion,
or dynamic-stack route. Binder `shared_ptr<State>` allocation and external
Surface storage are outside per-pixel analysis.

Run, without Git:

```sh
shasum -a 256 \
  docs/port-engineering/task-25-frontier-audit.md \
  docs/port-engineering/task-25-oracle-generator.mjs \
  docs/port-engineering/task-25-oracles.json \
  docs/port-engineering/task-25-oracle-report.md
node docs/port-engineering/task-25-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/check_semantics.py --check
python3 tools/glslcpp/generate_kernels.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
```

Also rerun `task-15-oracle-generator.mjs --check` through
`task-25-oracle-generator.mjs --check` for every available accepted package,
all focused Task 15-25 Python/native tests, and final Debug/Release/sanitizer
CTest. Finish with mechanical namespace/resource/stack/disassembly checks, an
exact owned-file before/after SHA-256 inventory, an implementation report,
and independent final review. Generator success alone is not completion.

## 12. Test-first implementation sequence

### Task 1: Hard gate and RED profile tests

**Files:** create the profile module; modify only
`tests/test_typed_generator.py` initially.

**Interfaces:** produce the four profile functions in section 4. Later tasks
consume only those functions and the explicit string carrier.

- [ ] Hash all frozen artifacts and accepted Task 24 owned files; run oracle,
  corpus, semantic, generator, Python, and native baseline checks.
- [ ] Capture accepted generated bytes and reparse both keys; assert exact pre
  source/function/whole/interface/site/profile identities.
- [ ] Add RED pre/post/transition tests, including 8/3 census, 6/5 roles,
  7/3/1 lanes, one-walk replacement, base identity, non-main identity,
  reapplication rejection, and dataclass-equal post reconstruction acceptance.
- [ ] Implement the minimal closed helper and run those focused tests green.

### Task 2: RED loader, driver, validator, and emitter matrices

**Files:** modify `generate_typed_slice.py`, `emit_typed_cpp.py`, and profile
tests; do not edit the slice yet.

**Interfaces:** propagate only `literal_vec3_lane_index_profile: str | None`.

- [ ] Add loader-schema negatives and all four exact modes.
- [ ] Add the literal Cartesian forgery/caller/carrier tests in section 7 at
  application, validator, emitter, and patched-driver boundaries.
- [ ] Add exact emission-route tests for six writes/five reads and explicit
  nonselected-emitter empty-cache regression tests.
- [ ] Implement only explicit carrier plumbing, post authentication, and
  site-owned use of existing fixed-swizzle emission; run focused tests green.

### Task 3: RED slice/count/isolation tests and deterministic generation

**Files:** modify `typed_slice.json`, generator tests, and the three generated
outputs.

- [ ] Add RED explicit 125/127/85/212 list, digest, position, manifest,
  header/catalog, diagnostic-projection, and Task 24 isolation assertions.
- [ ] Add exactly the two sorted profile records and generate once.
- [ ] Run `generate_typed_slice.py --check`; mechanically inspect only the two
  new namespaces and prove all prior normalized blocks unchanged.

### Task 4: RED six-case native oracle and ABI tests

**Files:** modify `tests/test_generated_kernels.cpp` and its exact transcription
test in `tests/test_typed_generator.py`.

- [ ] Add the exact machine-parseable six-case/eleven-mutation table and prove
  field-for-field equality with the pinned JSON.
- [ ] Add complete missing/wrong/exact/extras ABI tests for both bindings.
- [ ] Add six public-factory renders with exact input/output/probes,
  repeatability, finiteness, immutability, tile/origin/alpha checks.
- [ ] Run the focused native executable and transcription test green.

### Task 5: RED eleven-mutation temporary native harness

**Files:** modify only `tests/test_typed_generator.py`; temporary C++ files
live in a fresh temporary directory.

- [ ] Add every one-site wrong-member mutation with exact target proof and
  production validator/emitter rejection.
- [ ] Render/compile all eleven test-only variants once and compare every
  active/inactive result to exact JSON hashes and metrics.
- [ ] Assert no temporary output or repository byte drift; rerun focused Task
  25 Python and native tests.

### Task 6: Full gates and independent review

**Files:** no additional product file; write only the requested `/tmp` report
and review artifacts.

- [ ] Run every command in section 11, every accepted prior oracle, and fresh
  Debug/Release/ASan+UBSan full CTest.
- [ ] Preserve `.su`, call-chain, Release disassembly, resource, fixed-lane,
  and generated-isolation evidence.
- [ ] Hash every owned file, obtain independent review, and stop on any drift
  rather than widening scope.

## 13. File-by-file scope

| File | Bounded responsibility |
| --- | --- |
| `tools/glslcpp/frontend/literal_vec3_lane_index_profile.py` | exact two-key pre/post/transition authentication and one-walk rewrite |
| `tools/glslcpp/generate_typed_slice.py` | exact loader fields, driver application, independent post validation, counts/lists |
| `tools/glslcpp/emit_typed_cpp.py` | explicit carrier, independent post auth, exact selected fixed read/write emission |
| `tools/glslcpp/typed_slice.json` | exactly two sorted `{}` profile records |
| `tests/test_typed_generator.py` | profile/four-mode/forgery/driver/isolation/resource/transcription/temp-native tests |
| `tests/test_generated_kernels.cpp` | six hermetic public cases, exact ABIs, repeat/finite/immutable/full-output checks |
| `tests/test_typed_slice.cpp` | expected unchanged; only remove a proven stale exclusion if necessary |
| `src/typed_generated/typed_slice.cpp` | deterministic generated output only |
| `src/typed_generated/typed_manifest.json` | deterministic two-row manifest addition only |
| `include/noisemaker/generated/catalog.hpp` | deterministic two-declaration/key addition only |

No other file is authorized. If the exact profile cannot be implemented within
this list, stop for scope review.
