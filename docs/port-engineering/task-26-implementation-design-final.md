# Task 26 Smooth Edge LUMA_WEIGHTS Implementation Design

## Status and frozen-package authority

This is the bounded implementation design for adding only `filter/smooth:smoothEdge` to the typed C++ slice. **Implementation is READY.** This design does not itself authorize Git operations, publication, or deployment.

The frozen package was repaired and independently validated in `docs/port-engineering/task-26-artifact-repair-report.md`, SHA-256 `6334ea50c9b9b7ed6d272bafd2309e9b3e865667cf89c8d26228e6476c461545`. The repair changed the oracle metadata to the exact source/tree contract: **six static `texelFetch` call sites**, one pass-through call at normalized source line 25 and five edge-path calls at lines 31–35. Runtime path counts remain one fetch for `smoothType == 0` and five fetches otherwise. Recursive oracle comparison proved that this static-site metadata field was the only semantic oracle payload change; all eight cases, eleven mutation/control definitions, and 88 mutation-case results were preserved.

The repaired frozen authorities are:

- `task-26-frontier-audit.md`: `f0971b7cc06b9758975f6d856950c9a5067a2fd9ea71e4c68e46edc699bdf6f6`;
- `task-26-brief.md`: `5df8328d28859ced1b0782008087902fbd9bb6bc23bbdcfe28e71c72d1c1e975`;
- `task-26-oracle-generator.mjs`: `43300fee88354bcce9d1294071858fce432e2297ce1dd3dcccfed524ba2268f9`;
- `task-26-oracles.json`: `7975cbe59733df0178956b7f145e03c2e872e269327d9f8dd1126c3bb9c3ccf9`;
- `task-26-oracle-report.md`: `b3e4a175ea95fe4bdd3319a11996451551ab9a3281412d10aa856f906515f816`.

The corrected oracle generator passes `--check`. No preflight blocker remains.

## Scope and non-goals

The implementation owns exactly this program and feature:

- Program key: `filter/smooth:smoothEdge`
- GLSL source: `sources/filter/smooth/smoothEdge.glsl`
- New behavior: authorize its one exact source-level `const vec3 LUMA_WEIGHTS`, preserve it as an automatic const helper-local C++ value, and add the program to the generated typed catalog.

It must not:

- add generic global-vector, generic global-constant, or generic constant-folding support;
- change parser, typed IR, runtime, CMake, corpus, GLSL types, compatibility transforms, numeric profiles, existing custom comparer support, existing literal-Vec3 lane transforms, or Gather identity handling;
- materialize `LUMA_WEIGHTS` as a namespace/global/static/thread-local value or as kernel state;
- alter any existing typed program's generated behavior, ordering, binding ABI, or manifest semantics;
- touch any file outside the owned-file list at the end of this document;
- perform any Git operation.

## Refreshed Task 25 baseline gate

Implementation must begin from this exact current baseline. These values supersede the projected hashes in the older Task 25 comparer report where the later dimension-hardening review changed `tests/test_generated_kernels.cpp`.

Current counts:

- Typed programs: 125
- Public catalog programs: 127
- Corpus programs: 212
- Unported programs: 85
- Zero-based positions: Lens 2, Gather Sorted 52, Prismatic 59
- Typed ordered-key SHA-256: `9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4`
- Public ordered-key SHA-256: `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`

The refreshed preflight passed:

```text
python3 tools/glslcpp/check_corpus.py --check
check_corpus: ok

python3 tools/glslcpp/generate_typed_slice.py --check
typed slice ok (125 programs)

fresh Debug build + ctest
1/1 test passed
```

Task 26 projected counts and order, computed by adding only Smooth:

- Typed programs: 126
- Public catalog programs: 128
- Corpus programs: 212
- Unported programs: 84
- Smooth zero-based position: 77
- Immediate ordered neighbors: Skew 76, Smooth 77, Smoothstep 78
- Lens, Gather Sorted, and Prismatic remain at 2, 52, and 59
- Projected typed ordered-key SHA-256: `01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76`
- Projected public ordered-key SHA-256: `d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3`

At implementation start, repeat the current count, order, hash, generator-check, and fresh Debug CTest gates. Stop if any value differs; do not reinterpret the design against a drifted tree.

## Exact source lock

The new profile must authenticate the source and typed tree rather than merely recognize a declaration name. The frozen identity is:

| Property | Required value |
|---|---|
| Program key | `filter/smooth:smoothEdge` |
| Source | `sources/filter/smooth/smoothEdge.glsl` |
| Raw bytes | 1554 |
| Raw SHA-256 | `b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265` |
| Normalized bytes | 1235 |
| Normalized SHA-256 | `42f61c507d633c07415bc816b6ba61f8a862642429943be1c0c1208c97b90f7c` |
| Defines | exact empty tuple/map |
| Functions SHA-256 | `8a7f2ac058a23e438f31787c55d235235271429fb79fc1d085c4dd1ba08cd4fc` |
| Whole-program SHA-256 | `5586658ce1f621887647e5fb77990606e8637b7d759d2c9f1096f26b7385cd89` |
| Interface SHA-256 | `9149a7b19b47edea7179f8460443ee67c4a314bcb3ed2a83b7a68d91550f4930` |
| Declaration SHA-256 | `be8644a44ad3d2710e4dfaa87045257a5bd7c0e7e0a363c12893ea77c3d2ee27` |
| Loop proof | zero loops; acyclic call graph |

The resource/interface declarations are exactly the six existing interface declarations in their current order. Declaration 7 is the only source constant:

- name `LUMA_WEIGHTS`;
- storage `const`;
- type `vec3`;
- not writable;
- declaration span `12:1-12:53`;
- initializer is a three-lane construct at `12:27-12:52`;
- initializer SHA-256 `57ee749ccff2d5029ccbd10b7ce01320fdeb694bf2d02d5835a0e6ccd5836104`;
- lane 0 spelling `0.299`, span `12:32-12:37`, F32 bits `0x3e991687`;
- lane 1 spelling `0.587`, span `12:39-12:44`, F32 bits `0x3f1645a2`;
- lane 2 spelling `0.114`, span `12:46-12:51`, F32 bits `0x3de978d5`.

The exact functions are declaration 9 `luminance` with body size 1 and hash `454e07a023decf6855ebb1b00e4e34013a0926b9b2ce43c08d6dd257f4538b8a`, and declaration 10 `main` with body size 13 and hash `91808a5a46522dc3c72f54733faea98e29621f9ac305a88ef5c7e5c2709e16aa`.

There is exactly one resolved read of declaration 7:

- owner `9:luminance`;
- path `(0, 'e0', 0, 1)`;
- span `15:21-15:33`;
- read SHA-256 `df251d3d8461278afd63b36f1f3cef0d48777196908b8571a11d65dc54b83880`;
- readonly lvalue;
- parent is the exact dot-expression signature at `15:12-15:34`, hash `0f4d0fe02d9ee23557db69dfaca7ffa5c2542295d385c0d075f5b7e374fa43ae`, with the declaration read in child role 1;
- first-argument hash `0c947970257b7042745712013dccbc9cbe816a36827840e4e403bd36c3e06ef3`.

The source has exactly five static calls to helper `luminance` from `main`, six static `texelFetch` syntactic sites in total, one `textureSize` syntactic site, and dynamic fetch counts 1/5 on pass-through/edge paths.

## Narrow profile authority

Add one module:

`tools/glslcpp/frontend/smooth_edge_luma_weights_profile.py`

Its public surface is exactly:

```python
PROFILE = "smooth-edge-luma-weights-v1"
SMOOTH_EDGE_KEY = "filter/smooth:smoothEdge"

def authenticate_smooth_edge_luma_weights(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> tuple[TypedDeclaration, TypedExpression]:
    ...

def apply_smooth_edge_luma_weights(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> TypedProgram:
    authenticate_smooth_edge_luma_weights(program, source_hash, profile)
    return program
```

The profile tuple and every exact identity listed above form the authorization boundary. The profile's own frozen tuple SHA-256 is `fbb3808e4392e3b3fa56a48965a36a47ce1a438626c9acdc6d33613fd3f57b80`.

`authenticate_smooth_edge_luma_weights` must independently reject any mismatch in key, source hash, normalized tree, defines, interfaces/resources, functions, declarations, initializer, F32 literal bits, reference resolution, owner, path, parent role, read cardinality, mutability, write/escape state, proof state, or carrier value. It returns the exact declaration object and exact sole read expression so downstream checks can use object identity.

`apply_smooth_edge_luma_weights` is intentionally an identity transform. It authenticates and returns the same `TypedProgram` object. It must not rewrite the tree, add a dataclass/IR field, register a generic capability, or expose a global-constant mechanism.

## Schema, loader, manifest, and ordering

Add exactly one sorted program row to `tools/glslcpp/typed_slice.json`:

```json
{
  "defines": {},
  "smooth_edge_luma_weights_profile": "smooth-edge-luma-weights-v1",
  "program_key": "filter/smooth:smoothEdge"
}
```

Extend only the program-row loader schema with optional `smooth_edge_luma_weights_profile`. Its value, if present, must be the exact profile string. Enforce:

- exactly 126 unique, lexically sorted program keys;
- exactly one Smooth carrier in the entire file;
- that carrier occurs only on the exact Smooth key with empty defines;
- no Smooth program without the carrier;
- no carrier on another key;
- no new top-level registry, capability, type, operator, compatibility entry, custom-comparer map, numeric-profile map, or literal-lane map.

The generated manifest adds `"smooth_edge_luma_weights_profile": "smooth-edge-luma-weights-v1"` only to the Smooth row. Historical rows must remain byte-for-byte semantically equal after removing the common monolithic output-hash field whose value necessarily changes. The new Smooth row is inserted at zero-based position 77.

The generated public catalog adds only the Smooth entry/binder. Public catalog count becomes 128 because its two pre-existing manual entries remain. No adapter entry is added.

## Generation pipeline order

For each selected program, keep this exact order:

1. Parse/analyze the exact source.
2. Apply the existing compatibility transform.
3. Run existing Lens pre-authentication.
4. Attach existing fixed-array/affine proofs.
5. Apply existing Gather identity handling.
6. Apply existing literal-Vec3 lane transform.
7. Apply Smooth identity authentication using the per-row carrier.
8. Independently authenticate Smooth in capability validation.
9. Independently authenticate Smooth in the emitter.
10. Render C++.
11. Record manifest metadata.

The Smooth step must be disjoint from Lens, Gather, and literal-lane profiles, and it must return the same program object. Tests must pin the order and prove that changing it cannot silently broaden admission.

## Validator authority

Extend `validate_capabilities` with one keyword-only `smooth_edge_luma_weights_profile` argument. Do not add the profile to a generic approved-capabilities set.

If the argument is present, validation must require:

- exact Smooth key and exact source hash;
- `glsl-f32` numeric mode;
- no compatibility carrier;
- no custom comparer carrier;
- no literal-Vec3 lane carrier;
- no Gather carrier;
- no source-global-int carrier;
- successful independent profile authentication.

Store the exact authenticated declaration object locally. In declaration validation, admit a source global before the generic float/int-global checks only when `declaration is authorized_smooth_edge_luma_weights_declaration`. No equality/name/type-only admission is allowed. Its dependency tuple must be empty.

At completion, require exact carrier/tree agreement. The four mandatory modes are:

| Tree | Carrier | Result |
|---|---|---|
| Exact Smooth tree | absent | reject |
| Exact Smooth tree | exact | accept unchanged |
| Forged/non-Smooth tree | absent | reject |
| Forged/non-Smooth tree | exact | reject |

An exact Smooth tree without a carrier may reach the existing `unsupported global declaration` rejection. A forged tree with no source global must still be rejected as missing/mismatched profile rather than pass because it avoids the declaration check.

## Emitter authority and exact materialization

Extend `render_typed_cpp` and `_Emitter` with the same keyword-only profile argument. `_Emitter` gets one initialization-only field holding the exact authorized declaration object. The emitter must call the profile authenticator independently; validator success is not trusted as emitter authority.

In `_validate_source_globals`, admit only the declaration object returned by that emitter-side authentication, with no dependencies. Reuse the existing `source_global_locals(function.body)` closure mechanism so the constant is emitted only where referenced. The existing local-type and construct-expression emitters are sufficient; do not add general Vec3-global support.

The only allowed generated materialization is the first statement of helper `luminance`:

```cpp
const glsl::Vec3 LUMA_WEIGHTS = glsl::FloatExpr<3>(
    static_cast<float>(0.299),
    static_cast<float>(0.587),
    static_cast<float>(0.114));
```

Required code-shape assertions:

- exactly one declaration of `LUMA_WEIGHTS` in the Smooth block;
- automatic `const glsl::Vec3`, helper-local in `luminance` only;
- appears before the helper's dot expression;
- no copy in `main` because the sole resolved read belongs to `luminance`;
- no state member, namespace/global/static/thread-local storage, dynamic initialization, heap allocation, or generic constant table;
- kernel state contains only the existing uniforms/resources;
- exact F32 literal materialization and lane order;
- all five helper calls share the same source declaration semantically while each invocation creates the automatic local as ordinary C++ execution requires.

## Exhaustive negative closure

Tests must enumerate and reject, one field at a time and in meaningful combinations:

- wrong/missing/foreign profile carrier;
- wrong program key, source path, raw hash, normalized hash, defines, numeric mode, factory identity, or adapter state;
- changed interface/resource ordering, type, name, binding, or hash;
- changed function identifier, name, signature, owner, body size, body hash, call count, call graph, loop proof, or recursion proof;
- changed declaration identifier, name, storage, type, writability, span, position, initializer kind, constructor arity, literal spelling, literal order, literal F32 bits, initializer hash, or declaration hash;
- a second declaration that looks equal but is not the authorized object;
- missing read, second read, write, compound write, reference escape, main-owned read, different helper-owned read, changed path, changed parent/dot expression, changed child role, or changed first argument;
- moving the automatic constant to `main`, kernel state, namespace scope, static storage, thread-local storage, a lambda capture, or a generic table;
- use of the carrier on any foreign key or with any existing profile/capability carrier;
- any attempt to authorize another const Vec3 by name, type, literal equality, hash prefix, or source-global category.

Profile tests should build a Cartesian carrier/hash matrix around the four mandatory modes. Validator and emitter tests must be separate so neither can inherit the other's authorization.

## TDD sequence and required RED evidence

Implement in these small RED/GREEN steps, recording the exact focused command and failing output before each production change:

1. **Profile RED:** add tests importing the new profile and authenticating exact/mutated Smooth trees. Expected initial failure: missing profile module. Implement only the exact profile and identity apply function.
2. **Schema RED:** add the planned 126th row and loader/census/order tests before loader support. Expected failure: unknown row field, wrong shape, or wrong count. Implement only the narrow row field and census.
3. **Validator/emitter RED:** call each directly with exact Smooth tree/carrier. Expected failure: unexpected keyword or unsupported global declaration. Add independent authentication and exact declaration-object admission.
4. **Generation RED:** exercise generation with the new row and isolation assertions. Expected failure: unsupported source global or missing Smooth block. Wire the ordered pipeline and manifest field.
5. **Native catalog RED:** add the public catalog/binder test before regeneration. Expected compile/test failure: missing `bind_filter_smooth_smoothEdge` or public count 127 instead of 128. Regenerate only after the generator tests are green.

At each step, run the focused negative suite before advancing. Never weaken a failing assertion to make the implementation pass.

## Generated-output isolation

Generation tests must generate both:

- the new 126-program spec; and
- an in-memory prior spec made only by removing the Smooth row/carrier.

Split generated C++ by `// Typed IR program`, normalize only `typed_[0-9]+`, and prove all 125 historical blocks are otherwise identical. Assert:

- exactly one new block at position 77;
- no historical block contains `LUMA_WEIGHTS`;
- the Smooth block contains exactly one helper-local declaration;
- all 125 historical manifest rows are equal after excluding the common monolithic output-hash field;
- only the Smooth manifest row carries the new profile field;
- catalog/header delta is exactly one key and one binder;
- projected typed/public counts, positions, and ordered-key hashes match the values above.

Capture new full generated-file SHA-256 values after implementation; do not predict or hand-author them in tests. `generate_typed_slice.py --check` must reproduce every owned generated file from the checked-in spec.

## Oracle and native validation

The canonical reference remains the pinned noisemaker-for-cpu factory obtained through `kernelFactories.get(key)`:

- canonical-kernels SHA-256 `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`;
- public-catalog SHA-256 `d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4`;
- adapter-index SHA-256 `40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267`;
- exact factory substring: 2660 bytes, SHA-256 `732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e`;
- canonical factory identity true and adapter entry absent.

The hermetic C++ test embeds the corrected frozen eight-case table; it must not read `/tmp` or noisemaker-for-cpu at runtime. A Python transcription test compares every embedded field against the corrected frozen JSON.

| Case | Size | Type | Threshold bits | Expected F32 SHA-256 | Expected RGBA8 SHA-256 |
|---|---:|---:|---|---|---|
| pass-through-modular-tile | 8x5 | 0 | `0x3e6b851f` | `ffaf80acb8db7b255eaf329399e44b5a562a19e82125b19317d436bb07f8fa4b` | `b3fd913a3458127e8f606cdcdd40aa5204835b0219b6feb1e749993a7bd9a8ad` |
| edge-modular-type1 | 9x6 | 1 | `0x3e3851ec` | `af1d4152b362120f0fa863602de3a5a01e4bf59f393f37058e879d8498909469` | `475820bc2a2eaeffb822f1506b7afffcd4aa8cd9eb4a9c442f27f9eab1c9d2b5` |
| edge-modular-type2-same-branch | 9x6 | 2 | `0x3e3851ec` | `af1d4152b362120f0fa863602de3a5a01e4bf59f393f37058e879d8498909469` | `475820bc2a2eaeffb822f1506b7afffcd4aa8cd9eb4a9c442f27f9eab1c9d2b5` |
| threshold-one-ulp-below | 5x5 | 1 | `0x3dfc0d11` | `c70f0d59488dda2bde1da6463690f63f9d85f22a7ee827dd1bba3f93829adb04` | `66517cf5c7e0d30c1671d3f8d13eea7ab9a83748f82ef4780817cf4b0f30f098` |
| threshold-exact | 5x5 | 1 | `0x3dfc0d12` | `c70f0d59488dda2bde1da6463690f63f9d85f22a7ee827dd1bba3f93829adb04` | `66517cf5c7e0d30c1671d3f8d13eea7ab9a83748f82ef4780817cf4b0f30f098` |
| threshold-one-ulp-above | 5x5 | 1 | `0x3dfc0d13` | `2173d5ef284d8e03867fa476c6cdc4c7ca81948e5244655b7f920b9bbbb84f39` | `7efb4ab7603eea21de958ddfbafc97719d99c62e2c1a63ea1153bfea396dc8a1` |
| single-pixel-clamped-neighbors | 1x1 | 1 | `0x38d1b717` | `7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e` | `e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332` |
| asymmetric-cardinal-lanes | 5x5 | 1 | `0x3df5c28f` | `ffc9c67a9151cfb6b03cb934d9ffb3704a29069cc65e9f3ab91f4535d18fd2ee` | `861c828b629ccf0413f0f4e23f345240720a961d7ca093563523178e30856fdb` |

For every case, render twice through the public catalog and once through the direct binder. Assert width and height for all three results, F32 hash, RGBA8 hash, all five probes, finite-lane count, input immutability, and repeat identity. Pass-through must preserve exact RGBA including alpha. Edge-path output alpha is 1.0. Threshold comparison is inclusive at the exact bit boundary. Coordinates are bottom-left in the kernel versus top-down in fixtures, and the 1x1 case proves cardinal clamping.

Binding ABI is exactly `tileOffset`, `fullResolution`, `inputTex`, `smoothType`, `threshold`. For both direct and public paths, missing or wrong-typed required bindings reject and extra bindings are accepted.

The test-only mutation harness covers all eleven frozen controls and compares each candidate's complete expected hash/difference result:

| Mutation | Cases changed | F32 lanes changed / maximum |
|---|---:|---:|
| red value | 1/8 | 6/6 |
| green value | 3/8 | 6/6 |
| blue value | 4/8 | 6/6 |
| red-blue swap | 5/8 | 16/16 |
| vec3 scalar | 7/8 | 50/50 |
| vec4 extra | 0/8 | structural rejection |
| cross-call mutation | 5/8 | 23/23 |
| rgb self-dot | 4/8 | 22/22 |
| helper-local exact F32 | 0/8 | authorized identity |
| helper-local source double | 2/8 | 6/6 |
| main-owned exact F32 | 0/8 | structural rejection |

The production profile must structurally reject the wrong controls even where outputs collide. The test-only harness is the only place mutation modes may exist.

## Stack, disassembly, and sanitizer validation

Use fresh `/tmp` Debug, Release, and ASan/UBSan build directories. Preserve floating-point contraction control and collect stack metadata with `-ffp-contract=off -fstack-usage -fstack-size-section` where supported by the selected compiler.

Required evidence:

- `.su` or equivalent records for `typed_77::luminance` and `typed_77::pixel`;
- maximum non-inlined call-chain static stack below 16 KiB, with the calculation shown;
- sanitizer frame inflation identified as instrumentation rather than production static-stack evidence;
- Release disassembly scoped to `typed_77`, proving five helper calls are either inlined or direct;
- the three exact F32 constants feed the dot product;
- no global load or dynamic initialization for `LUMA_WEIGHTS`;
- no heap allocation, indirect branch, exception path, VLA/`alloca`, recursion, or dynamic stack growth in the typed pixel/helper path;
- binder `shared_ptr` mechanics accounted for outside the pixel/helper proof;
- six static fetch sites in generated code, with runtime counts 1/5, and one `textureSize` execution on each path.

If LeakSanitizer is unsupported on the host, preserve the failed diagnostic and rerun ASan/UBSan with leak detection disabled; do not silently omit the sanitizer run.

## Final verification sequence

Run focused tests after each GREEN step, then this full sequence from a clean generated state:

```sh
node docs/port-engineering/task-26-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/check_semantics.py --check
python3 tools/glslcpp/generate_kernels.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m py_compile tools/glslcpp/frontend/smooth_edge_luma_weights_profile.py tools/glslcpp/generate_typed_slice.py tools/glslcpp/emit_typed_cpp.py tests/test_typed_generator.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

Then configure/build/test fresh Debug, Release, and sanitizer trees, run the stack/disassembly checks, rerun all frozen Task 15 through corrected Task 26 oracle generators in check mode, and independently recompute counts, positions, and ordered-key hashes. Record all commands, exit codes, generated-file hashes, native/oracle hashes, stack calculations, and sanitizer results in the implementation report.

## Owned files

Only these repository paths may change:

- `tools/glslcpp/frontend/smooth_edge_luma_weights_profile.py` — new exact profile/authenticator.
- `tools/glslcpp/generate_typed_slice.py` — narrow row schema, census, pipeline wiring, validator argument, manifest propagation.
- `tools/glslcpp/emit_typed_cpp.py` — emitter-side authentication and exact helper-local admission.
- `tools/glslcpp/typed_slice.json` — one sorted Smooth row/carrier.
- `tests/test_typed_generator.py` — profile/schema/validator/emitter/generation/isolation/negative/transcription tests.
- `tests/test_generated_kernels.cpp` — hermetic native oracle, ABI, mutation, dimension, and public/direct tests.
- `tests/test_typed_slice.cpp` — allowed only if a genuinely necessary typed-catalog assertion cannot live in the existing generated-kernel test; expected unchanged.
- `src/typed_generated/typed_slice.cpp` — generator-owned output only.
- `src/typed_generated/typed_manifest.json` — generator-owned output only.
- `include/noisemaker/generated/catalog.hpp` — generator-owned output only.

Every other repository path is forbidden. In particular, do not change `include/noisemaker/glsl_types.hpp`, `tests/test_glsl_types.cpp`, parser/IR/runtime/CMake files, corpus source, or any existing profile module. Generated files must be produced by the generator, never hand-edited.

## Completion condition

Task 26 is complete only when the repaired frozen package remains locked, every RED was observed before its implementation, the exact profile and two independent authorities pass exhaustive negative closure, only Smooth changes generated semantics, the eight native cases and eleven mutations match the corrected frozen oracle, all Debug/Release/sanitizer/stack/disassembly/full-suite gates pass, and the final report records exact evidence. Local or CI success alone does not authorize publication, deployment, or any Git action.
