# Task 21 Degauss Implementation Design

> **For agentic workers:** REQUIRED SUB-SKILL: use
> `superpowers:test-driven-development`, then
> `superpowers:verification-before-completion`. This plan is executable only
> after an independent read-only review. No Git, branch, worktree, pull request,
> publication, or deployment operation is authorized.

**Goal:** Add exactly `filter/degauss:degauss` to the existing generated C++
CPU slice, reaching exactly 115 typed factories, 117 public factories, 95
publicly unported programs, and 212 corpus programs.

**Architecture:** Keep the accepted generic typed IR, validator, emitter,
runtime, and resource ABI unchanged. Add one hard-coded, source-key-specific
publication profile in `generate_typed_slice.py`; add one sorted slice entry;
regenerate the three existing outputs; and freeze direct-canonical native
parity in the existing test files. The Degauss profile authenticates identity
and structure but grants no new language feature.

**Tech stack:** Python 3 typed-GLSL generator/tests, generated C++20, the
existing native test harness, CMake/CTest, frozen Node oracle artifacts used
only as implementation-time provenance, ASan/UBSan, compiler `.su` stack
records, and `otool` or `llvm-objdump`.

## Global constraints

- Repository: `.`.
- The amended scope brief is
  `docs/port-engineering/task-21-brief.md`, SHA-256
  `bf6a223b076b0c3cac93b2a05d3c428b4ba39ab2fe88fe6bc712c3a0a76e6418`.
- The accepted Task 20 implementation report is
  `docs/port-engineering/task-20-report.md`, SHA-256
  `83d0624bd21f581593d7b011fdff8757191ae466b8b84174b6a1eec5cb7b81f2`.
- The accepted Task 20 final review is
  `docs/port-engineering/task-20-final-acceptance-review.md`, SHA-256
  `b1ee7af7b8ecf7144209a77141448b5b55093f5987d82bbc5dfe37d82f4c750f`.
- Baseline/result counts are exactly `114/116/96/212` and
  `115/117/95/212` for typed/public/unported/corpus.
- Add Degauss only. `filter/crt:crt` remains excluded.
- Add no capability, transform, numeric exception, proof, type, operator,
  builtin, loop rule, resource ABI, runtime helper, dependency, or new file.
- Do not modify `typed_ir.py`, `semantic.py`, `emit_typed_cpp.py`, any proof or
  compatibility module, corpus source, runtime, sampler, Surface, CMake, or
  public binding ABI.
- All repository edits, when separately authorized, must use `apply_patch`;
  only the canonical generator may write generated outputs.
- Native parity failure is a stop/reclassification condition, never authority
  to add a transform or capability.

---

## 1. Authenticated inputs and accepted baseline

The following Task 21 artifacts were recomputed from the current checkout and
match the amended brief:

| Artifact | SHA-256 |
| --- | --- |
| `task-21-frontier-audit.md` | `2f4665fa7a7d6471291030c02b3e259a797a95d33dd15dabd3b10433749ec7b0` |
| `task-21-oracle-generator.mjs` | `0c1f12904e1c17a39c61055596be9f0d46ecded252a9d5c7cf1339653472c5c9` |
| `task-21-oracles.json` | `bddb1ca8f8b7a8b905412318c48414594736ca4a972c440da7e8c3525b31bb38` |
| `task-21-oracle-report.md` | `4196f7a238c63eadb2e167b3f76528b620cea56fabad999525c8fbc5826f02fc` |

`node task-21-oracle-generator.mjs --check`, corpus `--check`, and typed
generation `--check` all pass on the accepted Task 20 baseline.

Independent analysis reproduced Degauss's exact 10,803-byte raw source hash
`915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c`,
10,512-byte normalized hash
`7d413b240236506511f405319025281a92eb1108c6193ef26a6d0d7bcbae7560`,
17-function tuple hash
`f68d742e44e341c1332f8c37ac8544aaa8c5bef979e496a27d45ac28ba48f95a`,
whole-profile hash
`73e7e3e3b5e0b7ee9b4e1558d51fc14a01e9820c89674a0b5e42e568bec8d13d`,
and interface hash
`6ceb3a3a3c7b0263b29d9950790bbe24b186759a4048b593b0a5447b733ae227`.
All 17 function IDs, names, top-level body counts, and hashes match the brief;
the loop proof is exactly zero/zero/zero/zero/zero/acyclic and all four Task
17-20 proof fields are `None`.

The accepted current-vocabulary payload is formed by deterministic sorted-key
JSON over `APPROVED_CAPABILITIES`, `APPROVED_TYPES`, approved binary and
assignment operators, sorted `_BUILTINS`, the corresponding slice lists, and
the transform/numeric maps. Its SHA-256 is
`dd4e14138c6ac72bbc37785faf361660edb418c38afabaf115d5b49d79999b4a`.
Tests must compare the constituent values directly and this stable fingerprint;
the fingerprint alone is not sufficient.

### Exact pre-write hashes of every owned file

| Owned file | Accepted Task 20 SHA-256 | Intended Task 21 change |
| --- | --- | --- |
| `tools/glslcpp/typed_slice.json` | `bf86b4e7e5e26a89a27f23009eb5a7589618ec54b469b79ffa4cad343f66ccb0` | Insert one sorted empty-define Degauss entry only. |
| `tools/glslcpp/generate_typed_slice.py` | `ff9cc618c98255ed71714c0384e5f64b613a09f5540457cca4e38b133ad62594` | Add the private Degauss profile/constants, wire it at publication, and change 114 to 115 in count validation/status text. |
| `tests/test_typed_generator.py` | `ece8739c40e37e7e9ac42054d4c647a1f4cdb2543bbd92ed0c2ec0dec275fb27` | Add profile, mutation, vocabulary, generation-isolation, and exclusion tests; update exact counts. |
| `tests/test_typed_slice.cpp` | `acfe7fe5483188b3936eb3d02b15f1187f185c2474f341996ce4d764f07b31a0` | Add the nine direct-canonical native fixtures and checks. |
| `tests/test_generated_kernels.cpp` | `fba30769e2ac4e66a173a9fc1c61c2ec920483c6b3b347e9377242d5c6b3035d` | Add exact Degauss binding ABI, declaration, 117-key catalog, and CRT-only adjacent exclusion. |
| `src/typed_generated/typed_slice.cpp` | `3b56d4f69b4477c7306ac659ec6a59c64f0a929d72a56921c28eb9961e82eef8` | Canonical generator output only. |
| `src/typed_generated/typed_manifest.json` | `8840aedc26a73c2af8e871cac4a2a41ffb8f107dbaea870902e9b22340614f41` | Canonical generator output only. |
| `include/noisemaker/generated/catalog.hpp` | `292c212ffb77e2bc597749899c7211a8134027f556c6b6f5eb03412a037aef6a` | Canonical generator output only. |

There are exactly eight owned repository files and no created repository file.
Record post-write hashes for these same eight paths. A before/after hash census
must prove that every other repository path is unchanged.

Key protected anchors and their exact accepted hashes are:

| Protected file | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/semantic.py` | `01c772aae5732d048c11c28b93d18d00fce63f6373ecb294324773f5e8817f2b` |
| `tools/glslcpp/frontend/typed_ir.py` | `7e16d088d7ffe90b7b6cc11dfff27d9df413ff4ffcdd13f9648fc4c35c91272c` |
| `tools/glslcpp/emit_typed_cpp.py` | `f8c9c21a8bc0590e2af78b892dc7504a55aafd8987a41e367a73f66a8de4ea11` |
| `tools/glslcpp/frontend/fixed_nine_table_proof.py` | `712a98e5130545f6f3884a965e2e096bc07fa0fe0ed88b1549ff6733ecac85b1` |
| `tools/glslcpp/frontend/fixed_grid_counter_store_proof.py` | `2bada0deacf426f29a85a1d747eba6e62ff5c37b4d428a4a4ab40fc44aa3ffa1` |
| `tools/glslcpp/frontend/fixed_array_in_parameter_proof.py` | `fd27f974b6d34c32cd0837948cdc93b9683afb1d61fe3881ca5841d55b10d468` |
| `tools/glslcpp/frontend/fixed_affine_centers13_proof.py` | `ac82d95f7a79dacb9749a2241d15e92e533299c61bf97fbcf3e2c128226499bd` |
| `tools/glslcpp/frontend/refract_compatibility.py` | `4bb1384ea020f03c91ae28c6d3498f0b5525318fc7ba0a2c4eb926866e1a7050` |
| `tools/glslcpp/frontend/sacred_geometry_compatibility.py` | `96987d7418216113a712ab70e7180cf919e5c2942528cf00264f8777bc1ab0d4` |
| `include/noisemaker/sampler.hpp` | `abec1caeec36504c6f49c2fe9df64b218a2346bb0db2417000517e7f6f9e0fe9` |
| `include/noisemaker/kernel.hpp` | `9869f847eaa78c46d8a1507002ff87bae1d6417b46b06f931d4a7ed31401114f` |
| `CMakeLists.txt` | `bca6b4ab77d26c72449ef8d7a66d5832fdc939ebb35a85211b7684dde62216d5` |

All listed anchors require exact equality after implementation.

## 2. Chosen design and rejected alternatives

### Chosen: a key-specific publication profile

Add one internal `validate_current_vocabulary_degauss` helper to
`generate_typed_slice.py`. It receives the analyzed `TypedProgram`, exact corpus
entry, declared defines, selected compatibility transform, numeric literal
contract, and exact metadata effect record. The helper always authenticates
Degauss; it is called only when the manifest entry key is the hard-coded
`DEGAUSS_KEY`. Mutating either the entry or typed key therefore fails rather
than turning the helper into an ambient feature.

This is the smallest sound boundary. Generic capability validation answers
whether a tree is expressible; the Degauss profile answers whether this exact
frozen tree may be published.

### Rejected: allowlist entry without a profile

This would render today, but any semantically supported source drift would also
publish. Source hash validation alone does not lock typed tree, interface,
metadata route, or foreign proof state.

### Rejected: new capability, proof carrier, transform, or emitter rule

Degauss already validates and emits under the accepted vocabulary. Adding an
ambient rule would broaden authority, touch forbidden boundaries, and conflate
publication identity with language support. A parity mismatch under the chosen
design stops the task.

## 3. Generator/profile contract

### Constants

Keep the constants in `generate_typed_slice.py`; create no module. Define exact
literal constants for:

- key/runtime key, effect, pass index/name, source path, status, raw and
  normalized byte counts/hashes, empty defines, `glsl-f32`, and no transform;
- `canonicalFactory45`, factory-text hash
  `f515a7ac409c98fc420d9fa9a7e460eb37018b34e3be40419191fc7655a29c38`,
  and canonical generated-runtime hash
  `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`
  as provenance constants only;
- complete function tuple, whole, and interface hashes;
- all 17 `(id, name, top_level_body_count, SHA256(repr(function)))` rows from
  the amended brief;
- the exact declaration/resource signature, `TAU` literal and F32 word
  `0x40c90fdb`, zero-loop summary, and the exact metadata effect/pass dictionary.

Do not accept caller-provided expected hashes. The profile recomputes actual
hashes and compares them to module constants.

### Helper interface and checks

Use this exact callable signature:

```python
validate_current_vocabulary_degauss(
    typed,
    entry: dict[str, Any],
    declared_defines: dict[str, int],
    *,
    compatibility_transform: str | None,
    numeric_literal_contract: str,
    metadata_effect: dict[str, Any],
) -> None
```

The helper performs, in order:

1. Exact corpus-entry equality, including revision-owned source identity,
   runtime key, effect/program, pass, status, outputs, varyings, byte counts,
   and hashes.
2. Exact `typed.key`, raw-source bytes/hash, normalized-source bytes/hash,
   empty defines, `compatibility_transform is None`, and `glsl-f32`.
3. Exact 17 function diagnostics, function tuple hash, whole tuple hash using
   the amended brief's field order, and interface tuple hash using its field
   order. The whole tuple intentionally excludes optional Task 17-20 fields.
4. Explicit `None` checks for `fixed_nine_table_proof`,
   `fixed_grid_counter_store_proof`, `fixed_array_in_parameter_proof`, and
   `fixed_affine_centers13_proof`.
5. Exact declaration/interface/resource facts: `TAU@1`, uniforms 2-10,
   `fragColor@11`, sampler S1 meaning, uniforms/samplers/output tuples,
   texture true, derivatives false, no extra source global, and the exact
   zero-loop acyclic proof.
6. Exact metadata effect record: identity aliases for direction/displacement/
   seed/speed; `inputTex <- inputTex`; `fragColor -> outputTex`; defaults
   0/0.0625/1/1; ranges `[-180,180]`, `[0,0.25]`, `[1,100]`, `[0,2]`; no
   define; no texture metadata entry; one pass only.

Error messages name the first failed profile field and the Degauss key. They do
not expose a way to override the frozen value.

### Publication wiring

Load pinned metadata once in `generate_outputs` beside the corpus root. After
analysis, compatibility handling, and existing proof attachment—but before
generic `validate_capabilities` and emission—call the helper only when
`entry["program_key"] == DEGAUSS_KEY`. Pass the exact entry, declared defines,
selected transform, numeric contract, and
`metadata["effects"]["filter/degauss"]`.

Leave `validate_capabilities` and `render_typed_cpp` untouched. Degauss's four
proof fields stay `None`; there is no proof attachment, transform call, or
numeric-map entry.

`load_slice` changes only the exact allowlist count from 114 to 115. The CLI
success text changes from 114 to 115. Every vocabulary/map literal remains
byte-for-byte the accepted Task 20 value.

## 4. Slice, generated output, and catalog isolation

Add exactly:

```json
{"defines": {}, "program_key": "filter/degauss:degauss"}
```

between Craquelure and Deriv. Do not add Degauss to
`compatibility_transforms` or `numeric_literal_contracts`.

Before generation, `generate_typed_slice.py --check` must fail only because the
three generated outputs are stale. Run the canonical writer once, then require
`--check` success. The new manifest entry must state
`compatibility_transform: "none"`, `numeric_literal_contract: "glsl-f32"`,
`define_contract: "none"`, exact source identity, and the new whole-output
hash.

The sorted insertion is at ordinal 19: the 19 preceding program blocks retain
raw byte identity, while the 95 following pre-existing blocks necessarily
change only their generated `typed_N` namespace ordinal. Therefore isolation
is defined precisely as follows:

1. Split accepted Task 20 and Task 21 C++ output at
   `// Typed IR program: <key>` markers.
2. Require the key sets to differ by Degauss only.
3. Require raw byte equality for all 19 keys before Degauss.
4. For all 114 pre-existing keys, replace only `typed_[0-9]+` with a fixed
   sentinel in both blocks and require byte equality.
5. Fail on any other difference. Do not normalize whitespace, literals,
   comments, factory names, or code.

This implements the amended brief's exact generated-isolation contract without
pretending that index-derived namespace renumbering can remain raw-identical.
Changing the generator/emitter namespace scheme is forbidden.

The public catalog and header must contain Degauss exactly once between
Craquelure and Deriv, equal the brief's exact 117-key list, remain sorted and
unique, retain Invert and Solid once, and exclude CRT and all other 95
remaining corpus keys.

## 5. Test-first implementation sequence

### Gate A: immutable preflight

1. Hash the amended brief, four Task 21 artifacts, accepted Task 20 report and
   review, eight owned files, and protected anchors.
2. Run Task 21 oracle `--check`, corpus/semantics/kernel/typed checks, full
   Python discovery, current native CTest, and every accepted Task 15-20 oracle
   check.
3. Assert live counts are exactly 114/116/96/212 and Sacred's accepted native
   tests remain present.
4. Stop on any mismatch; do not edit.

### RED 1: profile does not exist

Add these exact tests to `TypedGeneratorTests`:

- `test_task21_degauss_profile_is_exact_and_current_vocabulary`
- `test_task21_degauss_profile_rejects_identity_interface_and_tree_drift`
- `test_task21_adds_no_capability_transform_or_numeric_exception`
- `test_task21_degauss_exclusions_remain_closed`

The first run must fail because
`validate_current_vocabulary_degauss`/profile constants do not exist and the
slice lacks Degauss. Preserve the RED output.

### GREEN 1: exact profile, no publication yet

Implement only the constants/helper and direct profile tests. Analyze the
pinned source with empty defines and call the helper explicitly. Require every
identity, function, whole, interface, declaration, resource, metadata, loop,
and foreign-proof check above. Generic validation and in-memory emission must
continue to succeed with the unchanged Task 20 capability tuple.

Review Gate 1 independently compares the hard-coded identities to the amended
brief/oracle, confirms no forbidden file changed, and rejects any new
capability/transform/proof/emitter/runtime rule.

### RED 2: publication/count/catalog absent

Update exact allowlist/catalog expectations to 115/117/95/212 and add
generation-isolation assertions. Observe failure because Degauss is not in the
slice/catalog and generated outputs are still Task 20.

### GREEN 2: slice activation and canonical regeneration

Insert the one sorted JSON entry, wire the helper, change the two count strings,
observe expected generated drift, and run the canonical writer once. Require:

- one Degauss typed/manifest/header/factory/catalog occurrence;
- exact `none`/`glsl-f32` manifest carriers;
- Degauss at typed ordinal 19;
- 114 prior blocks isolated by the strict ordinal-only comparison;
- no CRT declaration, factory, or catalog entry;
- repeated generation and alternate-CWD generation are byte-identical.

### RED 3: binding/native parity absent

Add the Degauss header-reference, exact binding matrix, and nine frozen native
fixtures. The build must fail before regenerated declaration/output is present
or native hashes must fail before fixture completion. Do not weaken expected
values to match native output.

### GREEN 3: generated binding and direct-canonical parity

The existing emitter supplies the generated code; there is no hand-written
runtime fix. Add only test data/assertions until all nine cases match. If they
do not match, stop and reclassify.

Review Gate 2 independently compares every C++ fixture field to
`task-21-oracles.json`, checks both full hashes and probes/metrics, and confirms
the input remains immutable.

### Gate D: final acceptance

Run all checks in Section 9 from fresh build trees. Perform stack, generated
shape, fetch, and disassembly audits before claiming completion. Rehash the
eight owned files and full protected census. Independent final review must
return no P0-P3 finding.

## 6. Negative and current-vocabulary regression design

### Test helpers

Inside `tests/test_typed_generator.py`, use test-only helpers that:

- load the exact corpus entry/source/metadata and analyze with `{}`;
- reconstruct the three profile tuples in the exact frozen field order;
- replace one typed dataclass node within a named function ID and assert the
  locator matched exactly once; zero or duplicate matches fail the test itself;
- rebuild a temporary slice/repository without mutating the real checkout;
- split generated C++ by program marker and normalize only namespace ordinals.

Do not add a production mutation API or proof carrier.

### Identity, schema, metadata, and foreign-proof matrix

Each subcase must fail the Degauss profile or slice loader independently:

- wrong revision, key/runtime key, effect/program/pass, status, source path,
  byte size/hash, normalized text/hash, factory name/text/runtime provenance;
- nonempty defines; missing/wrong numeric contract; any Degauss transform;
  any additional transform or numeric exception;
- missing, duplicate, reordered, or misplaced slice entry; counts other than
  115/117/95/212;
- changed function count, any one function ID/name/signature/body count/hash,
  function tuple, whole tuple, interface tuple, loop summary, edge, or
  recursion;
- Task 17, 18, 19, or 20 proof non-`None`, each alone and all together;
- attacker-mutated typed tree plus attacker-recomputed local digest still
  rejects because the expected digest is module-owned;
- every declaration/resource mutation from the brief: TAU binding/mutability/
  type/literal/global count, IDs/order/storage/types, sampler slot/count,
  output/route/aliases/defaults/ranges, texture/derivative flags, and forbidden
  varying/block/struct/matrix/array/sampler-parameter/stage ABI.

### Thirteen semantics-sensitive tree mutations

Use one exact function-scoped locator per canonical mutation and require the
hard-coded profile to reject it:

| Canonical mutation | Typed function ID |
| --- | ---: |
| red channel selector `0 -> 2` | `main@56` |
| direction rotation disabled | `warped_channel_value@66` |
| integer next-neighbor wrap changed | `wrap_index@68` |
| floating coordinate wrap changed | `wrap_float@67` |
| bilinear `fx` forced zero | `sample_bilinear@62` |
| bilinear `fy` forced zero | `sample_bilinear@62` |
| time-noise branch disabled | `compute_noise_value@54` |
| singularity mask forced one | `singularity_mask@64` |
| normal alpha clamp disabled | `main@56` |
| displacement cap disabled | `main@56` |
| simplex amplitude `42 -> 41` | `simplex_noise@63` |
| frequency axes unswapped | `compute_noise_value@54` |
| seed offset disabled | `compute_noise_value@54` |

Also cover five static level-zero `texelFetch` AST sites, exactly one typed `%`
site, bilinear footprint/order, channel call count/order, displacement/mask/
early-return branches, full-resolution fallback, 256-pixel cap, 1.01
threshold, F32 materialization, and no loop/recursion/allocation/dynamic ABI.

The external oracle generator remains the authority for each mutation's exact
one textual replacement and required divergence/identity case lists. Rerun its
`--check`; do not call Node from CMake or native/Python test runtime.

### Closed-world/current-vocabulary controls

- Reconstruct the stable vocabulary payload and require direct equality plus
  SHA `dd4e14138c6ac72bbc37785faf361660edb418c38afabaf115d5b49d79999b4a`.
- Require Degauss absent from transform/numeric maps and all four proofs `None`.
- Require the unchanged generic validator and emitter to accept exact Degauss
  in memory before publication.
- Require a semantically valid Degauss mutation to pass generic validation yet
  fail the key-specific publication profile. This proves the boundary is
  identity, not a disguised language restriction.
- Require profile use with a foreign key/source/pass/define to fail.
- Re-run Task 19 Refract and Task 20 Sacred transform/proof tests unchanged.

## 7. Exact binding and catalog tests

In `tests/test_generated_kernels.cpp`, add
`typed_task21_degauss_binding_abi_is_exact`. Its binding constructor supplies:

- texture: `inputTex` only;
- Vec2: `resolution`, `tileOffset`, `fullResolution`;
- number: `time`, `displacement`, `speed`, `direction`;
- int: `seed`.

For each of the nine names, omit it once and substitute the wrong alternative
once: texture as scalar, Vec2 as scalar, numbers as int, and seed as float.
Every case throws `KernelBindingError`. A fully correct binding returns a
non-null pixel function. Add an unrelated extra binding and require success.
There is no `TAU` binding or second sampler.

Rename/update the exact catalog test to 117 entries, insert Degauss between
Craquelure and Deriv, and compare every key against the amended brief's exact
117-key list. Count Degauss/Invert/Solid exactly once, assert strict sortedness,
and require `generated::bind("filter/crt:crt", empty)` plus representative
remaining keys to throw `std::invalid_argument`.

## 8. Native oracle design

### Fixture representation

Add `Task21Case` and `render_task21` in `tests/test_typed_slice.cpp`. Store each
float/Vec2 value as its exact F32 word, seed as `std::int32_t`, dimensions,
full F32/RGBA8 hashes, eight four-lane probe words, and every metric from the
frozen JSON. Mechanically transcribe all nine records and independently compare
the C++ record names/hashes/words/metrics to the JSON before running tests.
The JSON is not a runtime dependency.

Construct a fresh top-down `Surface` for each render with:

```text
R=((17*x+31*y+13)%101)/100
G=((7*x+19*y+23)%97)/96
B=((29*x+11*y+5)%89)/88
A=(((5*x+7*y+3)%23)-5)/12
```

Cast every lane to `float` at assignment. Bind the case's exact words and call
`run_pass` with its width/height/time, runtime seed word `0x41e80000`, frame 17,
and delta-time word `0x3c888889`.

### Exact nine cases

Use the nine names, dimensions, binding words, and hashes in the amended brief.
The F32/RGBA8 hash pairs are:

| Case | F32 / RGBA8 SHA-256 |
| --- | --- |
| displacement-zero-exact-copy-tiled | `daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687` / `5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3` |
| default-landscape-untiled-center-mask | `c6bf433ea90b0c82d842724d8f633fefb8cded8e34ad83b9d3480d98a7051c71` / `9e02468af87d81a5d0a558ac965dd9e4f78b07a768b855e157d5769bcbd3ee98` |
| nondefault-landscape-tiled-negative-direction | `08dbc2988787474877268f9661bbeccbdc88dbd9f43bbfc3240e58120cf363f1` / `16267b09be48cdb9b967ad1e4c203cd2170b940639975ee1cbba75309765db2c` |
| nondefault-portrait-tiled-positive-direction | `86b32d32e970fffccc7049bf9c091f5e8b5e9139af7afd6f7bee6d315636a37f` / `d2aca58372b68e20691c89a7ab278aebf97ffe85ffa35eb3d4bb6414016803d7` |
| speed-zero-nonzero-time | `2bd1aa43c71d4eaab6298492b9edafd35978cd439eeae2a270968f6210128f37` / `7788b9151bca2f493a0af156b38cc636e14b5f27d4bbed16ed60c4942513dc22` |
| time-zero-positive-speed | `c2f6253b9491350f176470a5be560068fb634e31432d524360d58ee03ed0586f` / `710ce156f4b71dae2d487ac6a78fee5e58ee044fe400eb24740764c1784039b6` |
| full-resolution-zero-fallback-landscape | `15401d32e6befb161651150f044f35496bf741be49872b3869716689131453ff` / `96cbb763c8daf83c9ef99c2972993148a5c2e5231436ebe9c4d4cb581c473a32` |
| square-frequency-equality | `8c09129cc2a75ca01f8a3d774307128cb1c44721c884821f6b22b7cff67e2948` / `8e456f5906aca7993075834d2f3ad09f358f9acaffbfcc4dbc0f113ed4fd94c6` |
| untiled-over-cap-binding-domain-diagnostic | `c7983e127a9bc4ed938cff5c316d71ed50f2dfb2126b54718901efd80aae705f` / `40d20fde4f5aab0e0e42a0371d373dbfdb66f62644650bef511ff8ffa3592bda` |

For every case:

1. Render twice with fresh input and destination surfaces.
2. Require input F32 bytes unchanged after each render and outputs byte-equal.
3. Require complete little-endian F32 hash and complete RGBA8 hash.
4. Require all eight top-down probe coordinates and all four lane words.
5. Require exact metrics: 4,228 total lanes across cases, every lane finite,
   changed lanes/pixels, exact-input pixels, alpha preservation/clamping,
   out-of-range alpha count, and min/max words/values.
6. Require orientation through asymmetric corner/interior probes.

The zero-displacement case must be exactly equal to all 1,872 input bytes and
preserve all 50 out-of-range-alpha pixels. Normal paths require
`clamp01(original.w)`; the exact center mask-zero pixel returns original data.
The over-cap case is a direct-binding diagnostic and must not change metadata
ranges.

## 9. Generated shape, resource, and full verification gates

### Scoped generated-code assertions

Extract only the Degauss namespace. Brace-extract `pixel`,
`warped_channel_value`, `compute_noise_value`, `simplex_noise`,
`sample_bilinear`, `wrap_float`, and `wrap_index`.

Require:

- one `fetch_texel` call in `pixel`, four in `sample_bilinear`, all LOD zero;
- exactly one `integer_mod` in `wrap_index` and no second remainder site;
- exactly three `warped_channel_value` calls and correct 0/1/2 lane routing;
- correct helper call graph and no generated C++ `main` definition or frame;
- `TAU` materialized through the normal `glsl-f32` boundary;
- no allocation/deallocation, `std::function`, associative container, variant,
  string, throw, `.at`, VLA, `alloca`, callback, indirect/virtual dispatch, or
  recursion in the scoped hot bodies.

Static source accounting is five `texelFetch` AST sites. Runtime accounting is
one fetch on copy/mask-zero paths and at most 13 on the normal path: one
original fetch plus three four-fetch bilinear samples. More than 13 is failure.

### Stack and disassembly

Build fresh Debug and Release trees with `-fstack-usage
-fstack-size-section -ffp-contract=off`. Report static/dynamic frame values for
`pixel` and every reachable helper. Calculate the maximum non-inlined chain:

```text
pixel -> warped_channel_value
      -> compute_noise_value -> simplex_noise -> permute/mod289/taylor helpers
      -> sample_bilinear -> wrap_float/wrap_index/fetch_texel
```

If Release inlines helpers, prove the fixed `pixel` prologue and reachable
direct calls from scoped disassembly/relocations. Any non-sanitized dynamic
frame, unbounded stack, recursive edge, allocator target, or `blr`/indirect
route fails. Sanitizer `.su` instrumentation classifications are reported
separately and never substituted for Debug/Release evidence.

### Commands

Run, in order, from the repository root:

```sh
node docs/port-engineering/task-21-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/check_semantics.py --check
python3 tools/glslcpp/generate_kernels.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_task21_degauss_profile_is_exact_and_current_vocabulary \
  tests.test_typed_generator.TypedGeneratorTests.test_task21_degauss_profile_rejects_identity_interface_and_tree_drift \
  tests.test_typed_generator.TypedGeneratorTests.test_task21_adds_no_capability_transform_or_numeric_exception \
  tests.test_typed_generator.TypedGeneratorTests.test_task21_degauss_exclusions_remain_closed
python3 -m unittest discover -s tests -p 'test_*.py'
```

Rerun every Task 15-20 oracle generator with its accepted `--check` command.
Use fresh `/tmp/noisemaker-task21-{debug,release,sanitize}` trees for configure,
build, and `ctest --output-on-failure`, with the amended brief's flags. Do not
reuse Task 20 build trees.

On Apple, first attempt the brief's `ASAN_OPTIONS=detect_leaks=1`. If the ASan
runtime rejects leak detection as unsupported before tests—as it did for the
accepted Task 20 build—record that exact platform failure and rerun the same
binary with `detect_leaks=0`; keep ASan and
`UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1` enabled. A sanitizer finding
is still a failure; only the unsupported leak-detector option may be waived.

Finally rerun deterministic alternate-CWD, transactional rollback/tamper,
symlink/traversal/unexpected-entry, and generated-owned-tree tests already in
the Python suite.

## 10. Exact final inventory and hard stops

The final repository inventory is exactly:

```text
tools/glslcpp/typed_slice.json
tools/glslcpp/generate_typed_slice.py
tests/test_typed_generator.py
tests/test_typed_slice.cpp
tests/test_generated_kernels.cpp
src/typed_generated/typed_slice.cpp
src/typed_generated/typed_manifest.json
include/noisemaker/generated/catalog.hpp
```

Stop and request revised scope if:

- any authenticated brief/baseline/source/profile/oracle identity differs;
- Degauss needs a capability, transform, proof, numeric exception, emitter,
  runtime, sampler, Surface, CMake, or ABI change;
- generic validation/emission of the exact source fails;
- any native F32 byte, RGBA8 byte, probe, metric, repeat, orientation, or input
  immutability check differs;
- CRT or another remaining key becomes public;
- any non-Degauss block differs beyond its index-derived namespace ordinal;
- resource accounting exceeds 13 fetches or reveals dynamic stack,
  recursion, allocation, or indirect dispatch;
- any path outside the exact eight-file inventory changes.

Completion evidence must include the eight before/after hashes, protected
anchor census, exact 115/117/95/212 counts, full test/check outputs, nine-case
oracle comparison, 13-mutation sensitivity check, generated isolation proof,
stack table/call-chain bound, disassembly/relocation proof, and independent
final review.

## Self-review

- Placeholder scan: no unresolved marker, deferred implementation, or
  unspecified production interface remains.
- Scope check: one source-key profile, one slice entry, three generated outputs,
  and existing tests only.
- Type/interface check: Degauss has one sampler, three Vec2 uniforms, four
  numeric uniforms, one int uniform, one output, and no TAU binding.
- Consistency check: the design distinguishes source `main@56` from generated
  `pixel`, uses `check_corpus.py --check`, preserves Task 20's 114/116/96
  baseline, and normalizes only unavoidable generated namespace ordinals.
