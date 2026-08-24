# Task 24 implementation design: Gather Sorted exact round-to-int profile

> **Status:** implementation design only. This document authorizes no
> repository edit and no Git operation.

## 1. Decision and completion target

Implement exactly one new typed/public CPU kernel:

```text
filter/pixelSort:gatherSorted
```

Admit only its existing scalar `round` node at the frozen site where the
existing scalar `int` constructor consumes it immediately, and emit that exact
parent/site as
`glsl::detail::float_to_int32(glsl::round(/* authenticated argument */))`.
The authorization carrier is exactly `gather-sorted-round-to-int-v1`.
Applying that carrier is an identity operation: it must return the same
immutable `TypedProgram` object without changing any node, proof, declaration,
resource, interface, define, or hash.

The result is exactly **123 typed / 125 public / 87 publicly unported / 212
corpus**. The newline-terminated sorted typed-key digest is
`df7750a48a77733e50f0e20072e291c2404e761932f6df8ddbcf8793d58fb6ac`;
the public-key digest, after adding the separately maintained Invert and Solid
factories, is
`bcf196794ff17ec62c1121347b3fe49a0907baa7ce3c3bd51352ec8a51fbac4e`.
Tests compare both explicit lists and digests. The typed insertion is exactly
zero-based position 51:

```text
filter/pixelSort:findBrightest
filter/pixelSort:gatherSorted
filter/pixelSort:luminance
```

No sibling Pixel Sort pass, Posterize, vector `round`, stored/returned `round`,
other frontend feature, or other public factory is part of Task 24.

## 2. Immutable preflight

Implementation must stop if any frozen artifact, accepted baseline byte,
source identity, typed identity, or count differs.

| Input | Required SHA-256 |
| --- | --- |
| Amended Task 24 brief | `a5184121126d75b32372440aae13ef9cde06006c5f4189607327e323e7d16e53` |
| Amended Task 24 brief review | `2adfde8d084e310bcd00089f26d70ad813f94aef713d708f82a08306356261a0` |
| Task 24 frontier audit | `fa4e0481ea50534be05923cf2c673b9f45195315121fbac7cbd05bece4f21220` |
| Task 24 oracle generator | `35d20a4428af390ed437f3c829a250a1974d254b66712c900d684d54a7e682d6` |
| Task 24 oracle JSON | `07dd6f31c3e2b5451cbde8fc0ae6f68ec7c3b06cd6296222ac938cdcee37a72a` |
| Task 24 oracle report | `b33894f0d69c97de5392d686bc9d5b469d672fc59f522b7b79c15604ae4299f6` |
| Accepted Task 23 report | `961292d3b0f75f1b471b2a568f8fd6f8f344fbabb35508d012618d3e0ca6a28f` |

The oracle generator has been rerun read-only on the accepted Task 23 tree and
passes `--check`. The accepted starting census is exactly **122 / 124 / 88 /
212**. The Task 24-owned preflight inventory is:

| Path | Accepted Task 23 SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/gather_sorted_round_profile.py` | absent; Task 24 creates it |
| `tools/glslcpp/generate_typed_slice.py` | `3a77d1702484e6ffed83c52e20d7b79315536f39150b43daed134b75bae2133d` |
| `tools/glslcpp/emit_typed_cpp.py` | `54bdacfc2912c6a33a1da76820ef4182d9722a2b5f03ea7f08f43d15bd8eb1f3` |
| `tools/glslcpp/typed_slice.json` | `4af84d22d3272f98f8d1698f34874b1fb249ad0ec9deec2c87cb8f9b354d163f` |
| `tests/test_typed_generator.py` | `f0809d1c832e3e86857f0452291d765ec76e3631a22fcb9640e18dcd009aeb24` |
| `tests/test_generated_kernels.cpp` | `6dba52360129c0fbd79f513d9e3fb1979e6ed99fe6c684577e7809f2c39bd2ba` |
| `tests/test_typed_slice.cpp` | `f85ad92eecbd386d549eb85402a17e93a5a17c08c122c37e474fe9ae6d91dd3e` |
| `src/typed_generated/typed_slice.cpp` | `c36f84aa5bcf09d932837bb84ba323ce51d44398ca29deb4dfb71151c32442a8` |
| `src/typed_generated/typed_manifest.json` | `d979fe5d968030cfc3ec9d688367b8b4418b9a841a6f612d65eac03ed5bd4184` |
| `include/noisemaker/generated/catalog.hpp` | `0704695854c772e26ca014d001d0573ce8fb87e367ffaf1c5cbc7e581bf675ed` |

Reparse Gather Sorted from corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, using exact defines `{}` and the
existing `glsl-f32` numeric contract. The accepted Task 23 tree has been
recomputed to the following exact values:

| Identity | Required value |
| --- | --- |
| Source | `sources/filter/pixelSort/gatherSorted.glsl` |
| Raw bytes / SHA-256 | 1896 / `a45eb039bae3e7b0a5f804de68c441092b6b7826b594c4aa5221c22a6c7b1386` |
| Normalized bytes / SHA-256 | 1185 / `28e7ad80ef7db266559deb4b822f52251ab899af61feb9f915e32c0ecce079a9` |
| Functions SHA-256 | `6378f26aa15c43dda1ceba1d098d5b7f7fd76174618bbc5428e6659622cf8218` |
| Whole-program SHA-256 | `23120c79e838032a4ac54abeac0929d1dc2c7c89c895b083b68e6188b6f36fe3` |
| Interface SHA-256 | `f18371bad7d92151cd361663a4b56266fffa2228b7b6379ad16518d9af8a8ed6` |
| Program loop-proof SHA-256 | `dd9dc4392ed9350b896854ad13cee5a242281bbe2b791f19b28cd2bd361251ca` |
| Functions | one `main`, signature ID 5, 15 statements |

The current Task 23 validator rejects this exact tree only at
`24:26: unsupported builtin round`. Any other preflight result is drift and
requires review before implementation.

## 3. Chosen architecture

Use a per-entry identity-profile carrier, a small shared pure authenticator,
and object-identity admission of the one authenticated node.

The new `typed_slice.json` record is conceptually:

```json
{
  "defines": {},
  "gather_sorted_round_profile": "gather-sorted-round-to-int-v1",
  "program_key": "filter/pixelSort:gatherSorted"
}
```

Every prior program record retains exactly the existing two fields
`defines` and `program_key`. `load_slice` requires the third field exactly once
and only on Gather; absent, wrong, duplicate, foreign, or extra profile fields
fail closed. This is metadata authorization, not a capability.

Create `tools/glslcpp/frontend/gather_sorted_round_profile.py` with a closed
single-row profile. Its public shape is:

```python
PROFILE = "gather-sorted-round-to-int-v1"
GATHER_SORTED_KEY = "filter/pixelSort:gatherSorted"

def authenticate_gather_sorted_round_to_int(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> tuple[TypedExpression, TypedExpression]:
    """Return the exact (int parent, round child) after full authentication."""

def apply_gather_sorted_round_to_int(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> TypedProgram:
    """Authenticate and return the same immutable program object."""
```

`authenticate_gather_sorted_round_to_int` returns the actual immediate `int`
parent and its actual round child reached through the frozen path. The
validator caches the round object and allows `round` only when the expression
currently being visited is that exact object (`value is authorized_round`).
The emitter caches both objects, admits the round child only by identity, and
emits the parent as one profile-owned unit through the existing clamped helper.
Neither layer adds `round` to a name set or infers authorization from the key.
Because the dataclasses are immutable and complete functions/whole/interface
hashes are locked, no duplicate or moved node can borrow the authorization.

`apply_gather_sorted_round_to_int` invokes the same complete authenticator and
returns `program`, not `dataclasses.replace(program, ...)`. Tests require
`result is program` and that a second application returns the same object
again. The generator driver applies it once as the explicit loader phase;
`validate_capabilities` and `_Emitter.__post_init__` then invoke the
authenticator independently. No layer trusts acceptance by the preceding
layer.

Do not change `APPROVED_CAPABILITIES`, `_BUILTINS`, or `_BUILTIN_NAMES` to
contain `round`. Do not add a typed-IR proof field or carrier field. Do not
change generic scalar `int(float)` emission: only the authenticated Gather
parent receives the existing clamp helper. Do not change semantic analysis:
`body_semantic.py` already represents the node and the ordinary semantic
analyzer already produces the exact proved program. Do not change
`loop_proof.py`, parser, runtime, numeric conversion, sampler, Surface, corpus,
CMake, or any compatibility transform.

Rejected alternatives are:

1. Adding `round` to the shared capability/builtin vocabulary. That would
   authorize Posterize and future scalar/vector sites by spelling rather than
   by this exact observable domain.
2. Rewriting `round(x)` to `floor(x + 0.5)`, changing generic scalar int
   conversion, or editing source. Those would mutate the frozen tree or widen
   the conversion change beyond the one profile-owned parent.
3. A new typed-IR proof record or runtime wrapper. The exact source/tree/site/
   consumer hashes already provide the necessary closed authority, and both
   `glsl::round` and `glsl::detail::float_to_int32` already exist.

## 4. Exact authenticator

The helper owns the frozen production identity table. Caller-supplied
`source_hash` is a drift alarm only; authority comes from independently
rehashing the retained raw and normalized source and the typed tree. The helper
requires all of the following:

- profile exactly `gather-sorted-round-to-int-v1`;
- key exactly `filter/pixelSort:gatherSorted`;
- exact raw length/hash, normalized length/hash, defines `{}`, body status,
  functions/whole/interface hashes, and profile-tuple hash;
- exactly one function, `main`, with the frozen signature/body identity;
- exact declarations, resources, local types, structs, uniform blocks,
  interface symbols, builtin symbols, and counted-loop program proof through
  the whole/interface hashes;
- exact round/argument, immediate int parent, and declaration statement;
- exactly one `round` builtin in the whole program, with no second scalar or
  vector occurrence;
- exact loop proof, binding/resource inventory, and absence of globals,
  ordinary uniforms, varyings, blocks, derivatives, helper calls, arrays, and
  additional functions.

The helper uses the brief's exact serialization:

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

Its `SHA256(repr(...))` is
`a100420798a4964c67ec4b2e98a09c62e5ca5b3b0d7f2fe1eb7a8ff8180e43fa`.

Resolve the exact path rather than searching for the first matching builtin:
function index 0, statement index 6, expression `e0`, int-constructor child 0,
round child 0. Then independently walk the complete tree to prove that this is
the only round node. Require the round node to be scalar `float`, rvalue,
callee `round`, signature `-38`, with one scalar-float child; its repr hash is
`a5f412a1949fdfae93b759bf1c01a22afb44f9a48e71710f2c54cdcdf312c625`
and its argument hash is
`a3797427a6fd439f07e4b1a5d33f7f13edcff528e71bee77a80489ae1697761d`.

Require the immediate parent at `(0,6,e0,0)`, span `24:22-24:67`, to be the
existing scalar `int` constructor with exactly that round object as its one
child and repr hash
`b16eb98c5a1cef7a40f78c65448f5f127c5feaa7cfa64dfdda0e167283aaba3c`.
Require statement `(0,6)`, span `24:5-24:68`, to contain the declaration of
local writable `int brightestX`, symbol 13, with no other expression; require
the statement hash
`3c98243330c489b4216d526ba594bac28177a8c3c1f1eb3799528ddbad358ea5`.

The caller hash must equal both the frozen raw hash and the independently
recomputed hash of `program.raw_source`. A forged raw source accompanied by an
attacker-recomputed caller hash therefore still fails the frozen source and
whole-program locks.

## 5. Loader, validator, and emitter flow

### 5.1 Loader and generation driver

`load_slice` keeps the top-level schema unchanged. For every program other
than Gather it requires exactly `{"defines", "program_key"}`. For Gather it
requires exactly
`{"defines", "gather_sorted_round_profile", "program_key"}` and exact
`{}` defines/profile spelling. The sorted allowlist length becomes 123 and the
existing exact default-define map remains otherwise unchanged.

The generation driver reads the carrier from the individual program record;
it does not derive it from key membership. Its order is:

```text
parse and analyze exact source with existing semantic/loop machinery
  -> apply existing compatibility/proof passes (none changes Gather)
  -> apply_gather_sorted_round_to_int with explicit carrier
  -> assert returned object identity
  -> validate_capabilities with explicit carrier
  -> render_typed_cpp with explicit carrier
```

No carrier is copied into the typed IR. The generated manifest keeps its
existing schema: Task 24 adds exactly one Gather record, with `none`
compatibility, `{}` defines, `glsl-f32`, the canonical source hash, and the
new factory. It does not add a profile/capability field to all prior records.

### 5.2 Generator validator

Extend `validate_capabilities` with only this keyword:

```python
gather_sorted_round_profile: str | None = None
```

If a carrier is present, require Gather key, no compatibility transform,
`glsl-f32`, exact caller/raw hash, and full independent authentication. Unpack
the returned pair and cache its child as `authorized_round`; the helper has
already authenticated the exact parent. If no carrier is present, leave
`authorized_round = None`; do not infer from the Gather key.

In the builtin walker, retain the ordinary `_BUILTINS` behavior for every
existing builtin. Handle `round` in a separate branch: accept only when
`value is authorized_round`; do not add `round` to `used`, `_BUILTINS`, or the
declared capability set. Every other round reaches the existing unsupported
builtin error.

Run the existing counted-loop reconstruction independently after profile
authentication. Submitted functions and `counted_loop_proof` must equal the
ordinary recomputed result. The profile helper's frozen hashes and the generic
loop validator are two independent checks; neither replaces the other.

### 5.3 Emitter

Extend `render_typed_cpp` and `_Emitter` with the same explicit keyword. Add
`authorized_round_parent: TypedExpression | None` and
`authorized_round: TypedExpression | None` non-init fields. During
`_Emitter.__post_init__`, a present carrier must pass exact key, source,
numeric-contract, compatibility, and full authenticator checks and cache the
returned pair; a foreign or wrong carrier fails immediately. An absent carrier
leaves both fields `None`. Then run all existing loop, proof-family,
source-global, binding, and resource validation unchanged.

Keep `_BUILTIN_NAMES` unchanged. In `expression`, before the generic
constructor branch, recognize only `value is self.authorized_round_parent`,
require its sole child to be `self.authorized_round`, and emit the parent and
child as one nested unit:

```python
if value is self.authorized_round_parent:
    round_value = value.children[0]
    if round_value is not self.authorized_round:
        raise _error(self.program, value, "Gather round-to-int parent drift")
    return (
        "glsl::detail::float_to_int32("
        f"glsl::round({self.expression(round_value.children[0])}))"
    )
```

The exact resulting spelling is:

```cpp
glsl::detail::float_to_int32(glsl::round(/* authenticated argument */))
```

If a round child is ever visited outside that parent-owned branch, reject it as
unsupported. Do not emit a direct `std::int32_t(...)`, C-style cast,
`static_cast<std::int32_t>(...)`, `convert_lane`, `floor`, `ceil`,
`std::round`, `lround`, `nearbyint`, or a new helper for this site. The generic
constructor branch remains byte-for-byte unchanged for every other scalar int
conversion. Standalone calls to `render_typed_cpp` must succeed only with the
exact program, caller hash, numeric contract, no transform, and exact carrier.

## 6. Four-mode and forgery matrices

Exercise this same matrix through the loader/generation driver, direct
`validate_capabilities`, and direct `render_typed_cpp`:

| Typed tree | Carrier | Expected result |
| --- | --- | --- |
| exact frozen Gather | absent | reject unsupported `round` |
| exact frozen Gather | exact | accept and preserve object/tree bytes |
| forged/moved/additional round | absent | reject unsupported `round` |
| forged/moved/additional round | exact | reject profile/tree drift |

The loader tests mutate an in-memory slice specification and, where tree state
matters, patch the analyzer result passed through `generate_outputs`; no test
writes generated repository bytes. Cover wrong spelling, foreign key,
duplicate Gather entry, Gather with another compatibility carrier, an unknown
extra field, and reapplication of the exact profile.

At validator and emitter boundaries, cross exact and forged trees with
absent/wrong/exact carriers and with correct, missing, wrong, and
attacker-recomputed caller hashes. Each mutation asserts the intended changed
node count and exact target path before checking rejection. The matrix covers:

- key, raw source, normalized source, defines, profile, function tuple,
  whole-program, and interface drift independently;
- missing, duplicate, additional, vector, moved, or span-shifted round;
- callee, signature, result type, category, argument type/hash, arity, and
  child-order changes;
- `floor`, `ceil`, `std::round`, `lround`, `nearbyint`, or a test spelling in
  place of the exact round; a direct/generic int cast, missing outer helper,
  wrong helper, reversed nesting, wrong helper arity, or separately emitted
  child in place of the exact parent-owned nested route;
- non-int parent, wrong constructor type/arity, stored-float, returned,
  compared, passed, or otherwise observable round result;
- declaration statement/path/span drift and `brightestX` symbol ID, name,
  type, storage, writability, initializer, or ownership drift;
- loop induction, start, comparison, update, bound symbol/value/kind,
  trip count, lexical/effective depth, product, charge, loop/program proof, or
  acyclicity drift; type-correct return/break changes and a call cycle;
- missing/extra/changed declaration, global, varying, uniform block,
  derivative, sampler, fetch, output, function, array, recursion, allocation,
  callback, exception, or dynamic-stack construct;
- capability vocabulary containing `round`, even with the exact carrier;
  unknown, missing, extra, or duplicate capability spelling;
- Posterize or any prior key borrowing the carrier; a prior key without the
  carrier remains accepted under the unchanged Task 23 vocabulary.

Generator and emitter tests call their public boundaries independently. The
test must not accept a forged tree in one layer and reuse that acceptance as
proof at the next.

## 7. Loop, domain, bindings, and resource invariants

### 7.1 Loop proof remains ordinary and unchanged

Task 24 does not modify `loop_proof.py` or add a proof seed. The existing exact
proof is:

| Field | Exact value |
| --- | --- |
| Span | `38:5-48:6` |
| Induction | local `int s`, symbol 19 |
| Start / comparison / update | `0` / `<` / `++` |
| Bound | local `const int NUM_SAMPLES = 64` |
| Bound kind / trips | `local-const-literal` / 64 |
| Lexical/effective depth | 1 / 1 |
| Lexical product / entry charge | 64 / 64 |
| Loop-proof SHA-256 | `c9df47f651e3ee7232826b3bf13ac40e29889e3d69a2d7a2f6dedecba5c579d4` |
| Program proof | 1 loop, 0 unproved, depth 1, product 64, charge 64, acyclic |
| Program-proof SHA-256 | `dd9dc4392ed9350b896854ad13cee5a242281bbe2b791f19b28cd2bd361251ca` |

Assert these values before and after profile application, validator
recomputation, emission, and regeneration. Any `loop_proof.py` byte change is a
scope failure, not an implementation convenience.

### 7.2 Observable numeric domain

Native parity is authorized only for finite `brightestTex.r` in `[0,1]`,
including both signed zeros; width at least 2; and all dimensions/coordinates
within signed-int32 bounds. Therefore the round input is finite in
`[0,width-1]`, the result fits signed int32, and the immediate int conversion
erases negative-zero sign before any observable use.

The production route is
`glsl::detail::float_to_int32(glsl::round(x))`, with `glsl::round(x) ->
glsl_round(x) -> floor(x + 0.5)`. The helper's clamp is inactive in the
admitted domain. This route is equivalent to canonical `Math.round(x) | 0`
only in that domain at this site. The profile makes no promise for NaN,
infinity, negative finite values beyond the signed-zero/negative-half control,
values above one, oversized dimensions, or round results outside int32. Do not
add JavaScript ToInt32 wrapping or signed-zero emulation.

### 7.3 ABI and resource contract

Bindings are exactly three samplers and one output:

```text
preparedTex:sampler2D@1/S1
rankTex:sampler2D@2/S2
brightestTex:sampler2D@3/S3
fragColor:vec4@4
```

There are no ordinary uniforms, define bindings, source globals, varying,
uniform block, derivative, or helper parameters. Binder tests reject each
missing sampler and each sampler supplied as the wrong type, accept the exact
three, and accept unrelated extras under the existing policy.

Resource accounting is exactly one `textureSize(preparedTex, 0)`, three static
`texelFetch` sites, and 66 dynamic fetches per pixel: one brightest fetch, 64
rank-loop fetches, and one prepared-result fetch. There are no conditional
fetch exits. Assert the typed resource inventory, generated spelling, and
native fixture arithmetic independently.

## 8. Oracle and native-test design

Embed Task 24 fixtures in one clearly delimited, machine-parseable C++ table in
`tests/test_generated_kernels.cpp`. A Python test in
`tests/test_typed_generator.py` parses that table and compares every field to
`task-24-oracles.json`: case/control names and order, dimensions, signed F32
row bits, all three input hashes and probes, full F32/RGBA8 output hashes and
probes, finite-lane counts, repeat identity, immutability, mutation hashes, and
changed-byte/lane metrics. The native executable remains hermetic and does not
read the JSON or noisemaker-for-cpu.

### 8.1 Four canonical cases

| Case | Size | Required F32 SHA-256 | Required RGBA8 SHA-256 |
| --- | --- | --- | --- |
| `normalized-positive-zero` | 9x4 | `566cc3c05492199a3daf8bdcfffe9f610703f74e74defd5583b7e99f768f4390` | `cf0f9c006514afc91c0d06aa64053f5bab69a226385d6e15afe05f11786e4bf7` |
| `normalized-negative-zero-control` | 9x4 | `566cc3c05492199a3daf8bdcfffe9f610703f74e74defd5583b7e99f768f4390` | `cf0f9c006514afc91c0d06aa64053f5bab69a226385d6e15afe05f11786e4bf7` |
| `normalized-half-boundaries` | 9x5 | `66e27bbf10a8708b0fa12a5b3a37b98433cb27409e1b19d75477f026a9074381` | `e0e4181ebf3958dda73bc3f2d1e653d11a86cdcf457029d99875a10a07303f11` |
| `normalized-wide-67` | 67x5 | `156bb977e833e4b09b51a83b2a357dec5baef1608224512c2920b78cd5dfbd43` | `67367ef5cae19cfb7c03d76d63f59e1b26a019531d23f15979c39629a6b57d3c` |

Each case creates independent prepared/rank/brightest F32 surfaces, snapshots
all three inputs, binds the exact samplers, renders twice through the public
catalog factory, and requires byte-identical full F32 and RGBA8 output, exact
probes, finite lanes, and unchanged inputs. The positive- and negative-zero
outputs must also compare byte-for-byte equal to each other. Width 67 proves
that the 64-sample loop remains a sparse search rather than silently changing
to output width or eight samples.

### 8.2 Four normative mutations

Use test-local structural replacements and temporary C++ namespaces for the
three divergent mutations; never write a mutation into production generated
files. For each typed-tree mutation, first prove the exact target path/hash,
then prove both production validator and production emitter reject it under the
exact profile. A test-only renderer may bypass admission solely after that
rejection, compile the three alternate variants once in a fresh temporary
directory with `-ffp-contract=off`, and emit deterministic F32/RGBA8 records
for field-for-field JSON comparison. Exercise the fourth, identity row through
the production nested-helper kernel.

| Mutation | Construction and required discrimination |
| --- | --- |
| `round-replaced-by-floor` | replace exactly the authenticated callee/signature; diverges on half-boundary and width-67 cases; maximum 512 F32 lanes / 490 RGBA8 bytes changed |
| `round-replaced-by-ceil` | replace exactly the authenticated callee/signature; diverges below the half boundary; maximum 36 / 36 changed |
| `sample-loop-64-to-8` | replace only `NUM_SAMPLES` literal 64 with 8 and rebuild temporary loop proof/cache; diverges at width 67; maximum 1161 / 1131 changed |
| `native-floor-plus-half-with-int32-clamp` | exercise the exact production nested helper route; byte-identical to the public canonical factory on all four normative cases; maximum 0 / 0 changed |

The temporary renderer must assert the intended alternate spelling occurs
exactly once, the canonical spelling is absent at that site, every namespace
is unique, and no temporary byte reaches the repository, catalog, manifest, or
installed library. Separately assert the production identity row contains the
exact nested helper once and no direct/generic cast at that site.

### 8.3 Two exclusion cases and three controls

Embed both exclusion fixtures, but label them non-normative and never use them
to widen native parity:

| Exclusion | Canonical F32 / RGBA8 SHA-256 | Treatment |
| --- | --- | --- |
| `excluded-negative-half` | `795d16640209e8a06f4e3e8913233aca45bb519e3d457a5da130027c3af8609e` / `54cf47fa165718a20e1c5ad47c03b5e56e40afdfdc2bf80c981ce3fc3b8fca57` | immediate int erases Math.round negative zero; native floor-plus-half control must match |
| `excluded-out-of-range-wrap` | `795d16640209e8a06f4e3e8913233aca45bb519e3d457a5da130027c3af8609e` / `54cf47fa165718a20e1c5ad47c03b5e56e40afdfdc2bf80c981ce3fc3b8fca57` | canonical `|0` wraps while native signed-int32 clamp must diverge; not a production acceptance case |

The three exact controls are:

- `negative-half-native-floor-plus-half-control`: identical, 0 changed F32
  lanes and 0 changed RGBA8 bytes;
- `negative-half-std-round-away-from-zero-control`: divergent, 72 changed F32
  lanes and 72 changed RGBA8 bytes;
- `out-of-range-native-int32-clamp-control`: divergent, 64 changed F32 lanes
  and 61 changed RGBA8 bytes.

Execute both exclusions through the exact production nested helper route. The
negative-half output must equal the canonical exclusion because the immediate
integer conversion erases the sign. The huge out-of-range production output
must equal the frozen clamp-control candidate hashes
`0d14c497753088590f7b45ee48075c7969b8ddc65a486f2fbe79c235c8cf1b64`
and
`94de999d1cc8e125614b07a69e70e80ca5f86efac621bf8d8481fb542a4216d1`,
and must diverge from the canonical wrapping hashes by exactly 64 F32 lanes
and 61 RGBA8 bytes. This is a closed-scope exclusion/code-shape control, not a
claim of out-of-domain parity. Do not edit conversion behavior to make the
native result match JavaScript wrapping.

## 9. Generation, catalog, and isolation gates

After adding the exact slice record, generation must produce one new namespace
at typed position 51, one new manifest program record, one new catalog row, and
one new header declaration:

```cpp
bind_filter_pixelSort_gatherSorted(const glsl::Bindings& bindings)
```

Isolation checks compare accepted Task 23 output captured before generation:

- blocks 0 through 50 are raw-byte identical;
- all 122 prior blocks are byte-identical after replacing only
  `typed_[0-9]+` ordinals with one sentinel;
- Gather is the only new block and occupies position 51;
- the prior manifest program records remain structurally identical except for
  the generator's existing monolithic `output_sha256` update; Gather is the
  only new record;
- catalog/header key/factory lists gain exactly Gather and remain sorted and
  unique;
- no whitespace, comments, literal, key, factory name, code, or metadata is
  otherwise normalized; all prior generic scalar int conversions are
  byte-identical.

Extract only the Gather namespace and mechanically require:

- exactly one `glsl::round`, exactly one outer
  `glsl::detail::float_to_int32`, and their exact nesting as one expression;
- zero direct `std::int32_t(glsl::round(...))`, C-style/static casts,
  `convert_lane`, `lround`, or alternate outer conversion at the site;
- exactly one 64-trip counted loop and no other loop;
- exactly three `fetch_texel` sites and one `texture_size` site;
- exact State fields/binder lookups for the three sampler pointers and no
  numeric uniform;
- no generated C++ `main`, global/static/thread-local storage, vector/string
  container, callback, exception route, recursion, VLA, `alloca`, allocator,
  indirect/virtual call, or dynamic stack construct.

The public catalog contains exactly 125 sorted unique keys and rejects an
unported adjacent key. `filter/posterize:posterize` remains absent and still
fails first on its closed round profile; diagnostic exposure must show its
next blocker remains `fwidth` at `80:19`, but Task 24 must not expose or
implement that derivative.

## 10. Stack, disassembly, and build gates

Build fresh Debug, Release, and combined ASan/UBSan trees under `/tmp`, using
Ninja only when available and otherwise Unix Makefiles. Preserve
`-ffp-contract=off`, `-fstack-usage`, and `-fstack-size-section`. Run full
CTest in all three; request leak checking, and on Apple's unsupported
LeakSanitizer runtime record the failure and rerun with `detect_leaks=0`, ASan
`halt_on_error=1`, and UBSan halt/stacktrace, matching the accepted Task 23
platform procedure.

For the Gather namespace, preserve Debug and Release `.su` records for
`pixel`. The source call graph has only `main`, so no user-helper chain is
added. Require a static frame below 16 KiB; resolve an inlined or missing
record with Release disassembly rather than guessing. Sanitizer dynamic frame
classification is instrumentation evidence, not the static resource proof.

Disassemble the exact Gather namespace and reached runtime symbols. Prove the
64-trip bounded loop and ordered
`glsl::round -> glsl_round -> floor(x+0.5) ->
glsl::detail::float_to_int32` route, with no direct floating-to-int conversion
bypassing the helper. Require zero allocator/deallocator or exception targets,
zero `alloca`, zero recursion, and zero `blr`/`br` indirect branches in the
scoped generated route. Binder `shared_ptr<State>` allocation and external
Surface storage are outside the per-pixel stack calculation.

## 11. Test-first implementation sequence

### Step 0: hard gate

Authenticate the artifact table and accepted Task 23 inventory, rerun the Task
24 oracle `--check`, reparse/re-hash Gather, and confirm 122/124/88/212. Capture
the accepted generated outputs for later isolation. Stop on drift.

### Step 1: RED shared-profile and four-mode tests

In `tests/test_typed_generator.py`, add failing tests for the exact helper
profile, exact path/site/parent/declaration, identity application, reapplication,
caller-hash boundary, all four tree/carrier modes, and the complete mutation
matrix. Directly exercise helper, validator, and emitter independently. Add
loader schema tests proving one carrier only and unchanged global capability/
builtin vocabularies.

Then create `gather_sorted_round_profile.py` and add only explicit carrier
plumbing to generator/emitter. Run the focused module before editing the slice.

### Step 2: RED slice, count, and isolation tests

Add failing explicit-list/digest/position tests for 123 typed and 125 public
keys, one Gather profile record, one manifest/catalog/header entry, and exact
Task 23 block isolation. Add the Gather record, generate once, and immediately
run `generate_typed_slice.py --check`. Inspect the isolated block mechanically.

### Step 3: RED native and oracle-transcription tests

Add the four canonical fixtures, four mutations, two exclusion fixtures, three
controls, exact binding cases, and JSON-to-C++ field-for-field parser. Prove
production rejection before compiling temporary mutations. Run the focused
Python and native tests, including repeat, immutability, finite output, exact
F32/RGBA8, signed-zero equality, wide-loop discrimination, and exclusion
semantics.

`tests/test_typed_slice.cpp` should remain byte-identical unless an existing
native assertion cannot be expressed in the Task 24 block of
`tests/test_generated_kernels.cpp`; no runtime seam or duplicated fixture is
justified.

### Step 4: complete verification and independent review

Run on final bytes, without Git:

```sh
shasum -a 256 \
  docs/port-engineering/task-24-frontier-audit.md \
  docs/port-engineering/task-24-oracle-generator.mjs \
  docs/port-engineering/task-24-oracles.json \
  docs/port-engineering/task-24-oracle-report.md
node docs/port-engineering/task-24-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/check_semantics.py --check
python3 tools/glslcpp/generate_kernels.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
```

Rerun every accepted Task 15-23 oracle/check, full Debug/Release/sanitizer
CTest, exact count/list/source/profile/tree/proof/binding/resource checks,
generated isolation, stack/disassembly/fetch analysis, and the final owned-file
hash inventory. Obtain independent review of the final bytes and completion
report. A green generator or build alone is not completion.

## 12. File-by-file scope

| File | Bounded responsibility |
| --- | --- |
| `tools/glslcpp/frontend/gather_sorted_round_profile.py` | new closed one-row source/tree/site/consumer authenticator and identity application |
| `tools/glslcpp/generate_typed_slice.py` | exact loader field, explicit driver propagation, independent validator authentication, object-identity round admission, counts/lists |
| `tools/glslcpp/emit_typed_cpp.py` | explicit carrier, independent authentication, exact-object `glsl::round` emission only |
| `tools/glslcpp/typed_slice.json` | one sorted Gather record with exact `{}` and exact profile |
| `tests/test_typed_generator.py` | four-mode/forgery/caller/loader matrices, generation/isolation/resource checks, JSON transcription, temporary mutation harness |
| `tests/test_generated_kernels.cpp` | embedded four canonical cases, bindings, repeat/finite/immutable/full-output checks, two exclusions and three controls |
| `tests/test_typed_slice.cpp` | preferably unchanged; only an otherwise inexpressible existing-harness ABI assertion |
| `src/typed_generated/typed_slice.cpp` | deterministic generated output only |
| `src/typed_generated/typed_manifest.json` | deterministic generated output only |
| `include/noisemaker/generated/catalog.hpp` | deterministic generated output only |

Every file outside this table remains byte-identical. In particular,
`semantic.py`, `body_semantic.py`, `loop_proof.py`, parser, typed IR, all prior
proof and compatibility modules, runtime/numeric files, sampler, Surface,
corpus, CMake, and other tests are protected. If the exact kernel cannot be
implemented inside this boundary, stop for revised independent review rather
than broadening `round`, changing conversion, or fixing an exclusion case.
