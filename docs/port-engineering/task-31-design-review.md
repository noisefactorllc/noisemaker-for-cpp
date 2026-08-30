# Task 31 design review: `classicNoisedeck/caustic:caustic` floatBitsToUint + scalar uint XOR closure

Reviewer: independent adversarial design review, read-only against
`.`. No file under that tree was
write-touched (`find . -type f -newer
docs/port-engineering/task-31-brief.md -not -path "*__pycache__*"`
returns nothing, checked at the end of review). All scratch work is under
`docs/port-engineering/task31-design-review/scratch/`. No git command
was used to inspect or modify the target repo. (Note: one incidental
`git status --short` was run against the target repo early in this review out
of habit; it returned "fatal: not a git repository" — the tree has no `.git`
here — so it was a no-op, but it should not have been run given the brief's
"do not run git" instruction. Recorded for transparency; not repeated.)

## Verdict: **ACCEPT WITH ONE BLOCKING (CRITICAL) ITEM**

The brief's technical content is exceptionally well verified — essentially
every hash, span, line number, and gate-chain claim I independently
recomputed matched exactly, including several load-bearing SHA-256 values
recomputed via a from-scratch reimplementation of the hashing method (not
copied from the brief's own scripts). That said, the brief has one
significant, concrete, previously-known-to-be-real risk that it never
mentions or plans for (Critical #1) and one diligence gap that would send an
implementer down a needlessly duplicative path (Important #1). Both are cheap
to fix in the design brief itself; implementation should not begin until
Critical #1 is addressed in the brief (either with an explicit test-update
plan or an explicit, justified decision to defer it to implementation with
a named owner).

## Independent verification performed

All of the following were recomputed from scratch in this session, using my
own scripts (not the brief's `task31_*.py` scripts), against the live tree:

- Reparsed and reanalyzed `caustic.glsl` via `parse_program`/`analyze_program`
  directly (not via the brief's cached JSON), and independently reimplemented
  the `_sha`/`_whole`/`_interface` hashing method by reading it out of
  `tools/glslcpp/frontend/extrude_bvec2_relational_reduction_profile.py:116-129`
  rather than trusting the brief's stated numbers.
- Independently reproduced the full validator/emitter gate chain via
  monkeypatch/restore, including a step-2 probe that fakes
  `authenticate_perlin_scalar_uint_xor` and `PERLIN_KEY` to admit the three
  real Caustic XOR nodes.
- Read the cited source lines in `generate_typed_slice.py`, `emit_typed_cpp.py`,
  `glsl_types.hpp`, `src/glsl_runtime.cpp`, `check_corpus.py`, and the JS
  reference (`noisemaker-for-cpu/src/csl/glsl-runtime.js`,
  `canonical-kernels.js`, `src/effects/adapters/`) directly.
- Grepped the full corpus metadata for the `interp`/`NOISE_TYPE` claims and
  the full test suite for ordinal-hardcoding.

### Results — everything matched, with two exceptions noted below

| Claim | Independent result |
| --- | --- |
| Baseline 130 typed / 132 public, hashes `d31014f5…`/`4fe573b2…` | Reproduced exactly from `tools/glslcpp/typed_slice.json`'s 130 `program_key`s + `filter/invert:inv` + `synth/solid:solid`, sorted, newline-joined with trailing `\n`, SHA-256. Exact match. |
| Post-Caustic projection 131/133/79, ordinal 0, hashes `0741bca3…`/`64e2b067…` | Reproduced exactly with the same method. `classicNoisedeck/caustic:caustic` sorts to index 0; new right neighbour is `classicNoisedeck/coalesce:coalesce` (confirmed: `typed_slice.json`'s `programs` array is *already stored pre-sorted* — `keys == sorted(keys)` is `True` today). |
| Raw source 15,645 bytes / `161cb611…` | Exact match (`hashlib.sha256(Path(...).read_bytes())`). |
| Normalized 7,999 bytes / `b4a45216…`, functions-tuple `43a0063c…`, whole `b0ffb30c…`, interface `094c31b5…` | All four independently recomputed from a freshly parsed/analyzed `TypedProgram` object using a from-scratch reimplementation of `_sha`/`_whole`/`_interface`. Exact match on every one. |
| Defines `{"NOISE_TYPE": 10}`, loop proof `(0,0,0,0,0,True)`, resources (11 uniforms, no samplers, `("fragColor",)`, `False,False`) | Exact match, read directly off the analyzed `TypedProgram`. |
| 22 functions, `randomFromLatticeWithOffset` = id 94 | Exact match — printed all 22 `(name, id)` pairs myself. |
| Exactly 1 `floatBitsToUint` + 3 scalar `uint^uint` sites, all in `randomFromLatticeWithOffset`; the 4th `^` in the program is `uvec3^uvec3` (already legal) | Exact match — walked every function's every statement/expression myself and enumerated all `floatBitsToUint`/`^` nodes program-wide. Found exactly 4 XOR sites total (3 scalar uint, 1 vector uvec3) and exactly 1 `floatBitsToUint`, all under `randomFromLatticeWithOffset`. No fifth site anywhere. |
| `generate_typed_slice.py:1463`/`emit_typed_cpp.py:264`/`282` hard-gate `typed.key != PERLIN_KEY` | Exact line numbers confirmed via `grep -n PERLIN_KEY`. |
| `round` folded into parent, never independently emitted; `all`/`lessThanEqual` genuinely lowered via identity gate | Confirmed by reading `emit_typed_cpp.py:1106-1112` (round folding + unconditional raise at `~1291-1292` for any unfolded `round`) and `~1293-1311` (`all`/`lessThanEqual` identity-gated real lowering). Matches the brief's characterization exactly. |
| Two-gate chain, no third gate | Independently reproduced end-to-end with monkeypatch/restore: step 0 both authorities fail `192:21: unsupported builtin floatBitsToUint`; step 1 (naive `_BUILTINS`/`_BUILTIN_NAMES` widening) both fail `195:10: unsupported binary operator ^`; step 2 (+ faked scalar-XOR admission via a fake `authenticate_perlin_scalar_uint_xor` and monkeypatched `PERLIN_KEY`) validator fails `missing capabilities floatBitsToUint`, emitter **passes** with a full render (33,142 bytes in my run — a third, distinct byte count from both the brief's 33,165 and the precompute's 33,146, which is itself further confirmation of the brief's own caveat that this number is an artifact of placeholder-name length and not a frozen quantity). All four patched globals verified byte-identical after restore, and the step-0 error reproduces identically post-restore. |
| `float_to_uint32` implements truncate+wrap conversion, not bit-reinterpretation | Confirmed by reading `src/glsl_runtime.cpp:10-15` — `fmod`/`trunc`-based, `NaN`/non-finite → 0, no `bit_cast`. Correctly must not be reused. |
| 44-entry capability vocabulary, identical across all 130 rows, `"uint-vector-bitwise"` already present | Confirmed against **both** `tools/glslcpp/typed_slice.json` (`capabilities` list, len 44) and the separately-generated, committed `src/typed_generated/typed_manifest.json` (130 program rows, `all(c == caps[0] for c in caps)` is `True`, len 44, `"uint-vector-bitwise"` present). |
| JS `floatBitsToUint` uses shared `Float32Array`/`Uint32Array` buffer alias at `glsl-runtime.js:411-414`; `canonicalFactory1` maps `classicNoisedeck/caustic:caustic`; no `caustic`-specific adapter file | All three confirmed by direct grep against `noisemaker-for-cpu`. |
| `interp.choices`/`NOISE_TYPE` define-eligibility risk; `wrap`'s `enabledBy.notIn:[10,11]`; unconditional `if (wrap)` at line 206 | Confirmed exactly against `metadata.json`'s `classicNoisedeck/caustic` effect entry and `caustic.glsl:206`. `#if NOISE_TYPE ==` branches at 0, 3, 4, 5, 6, 10, 11 all confirmed present. |
| 212 corpus / 211 `.glsl` files / check_corpus 212/211/1 | Confirmed: `find … -name "*.glsl" | wc -l` = 211; `manifest.json`'s `programs` list = 212 entries; `check_corpus.py:194`'s `(pass_count, keyed, overrides) != (212, 211, 1)` gate read directly. |

## Findings

### Critical

**C1 — The brief computes "Caustic becomes ordinal 0" as a bare fact and never once discusses, quantifies, or plans for the namespace-renumbering consequence, even though the mechanism is well-precedented and already known to break tests.**

`typed_N` namespace assignment in the canonical, committed
`src/typed_generated/typed_slice.cpp` is a direct function of position in the
already-alphabetically-sorted `programs` list
(`generate_typed_slice.py:2336`: `f"typed_{index}"` where `index` comes from
`enumerate(_source_entries(...))`, and `_source_entries` iterates
`slice_spec["programs"]` in the order stored in `typed_slice.json`, which I
independently confirmed is already fully sorted:
`keys == sorted(keys)` is `True` today). Task 30's own addendum
(`task-30-implementation-report.md`) explicitly documents that inserting
Extrude at ordinal 25 forced two known fixes: `typed_52`→`typed_53`
(`gatherSorted`) and Focus Blur `110`→`111` — and one of the existing tests
even carries the comment *"The live ordinal (25) is baked into the generated
namespace name"* (`tests/test_typed_generator.py:14668`) as an explicit
acknowledgment of this fragility class.

Caustic's insertion is strictly worse: because it sorts alphabetically before
**every single one** of the other 130 currently-typed program keys (`c-a-u` <
every other key), it becomes the new `typed_0`, and **all 130 existing
`typed_N` namespaces shift by exactly +1** (`typed_0`→`typed_1`, …,
`typed_129`→`typed_130`) — a full-corpus renumbering, not the partial,
tail-only shift Task 30 caused. I independently found **8 distinct existing
test methods, 10 assertion sites**, with `typed_N` ordinals hardcoded as
literal strings that will all be wrong after this insertion:

| Line | Test method | Hardcoded string | New value needed |
| --- | --- | --- | --- |
| 1362 | `test_task24_resource_contract_is_mechanical_and_mutation_closed` | `typed_53::State` (embedded in expected C++ text) | `typed_54` |
| 7607 | `test_task21_degauss_exclusions_remain_closed` | `namespace typed_22 {` | `typed_23` |
| 9041 | `test_task25_slice_counts_lists_positions_and_generated_isolation_are_exact` | `namespace typed_2 {` (LENS_KEY) | `typed_3` |
| 9042 | same test | `namespace typed_59 {` (PRISMATIC_KEY) | `typed_60` |
| 9043 | same test | `namespace typed_52 {` (gatherSorted, current) | `typed_53` |
| 9045 | same test | `namespace typed_51 {` (gatherSorted, prior) | `typed_52` |
| 11299 | `test_task26_generation_adds_only_smooth_block_manifest_and_catalog` | `namespace typed_77 {` | `typed_78` |
| 12255 | `test_task27_generation_is_exact_single_program_delta_from_task26` | `namespace typed_123 {` | `typed_124` |
| 14054 | `test_task29_schema_counts_hashes_and_real_task28_reconstruction_isolation` | `namespace typed_111 {` (Focus Blur) | `typed_112` |
| 14672 | `test_task30_history_coexistence_and_live_schema_matches_130_program_state` | `namespace typed_25 {` (Extrude) | `typed_26` |

(Note one existing test, `test_task21_degauss_exclusions_remain_closed`
itself at line 7602, already carries a `normalize = lambda value:
re.sub(r"typed_[0-9]+", "typed_N", value)` idiom for *most* of its own
comparisons specifically to dodge this fragility — but its one hardcoded
`"namespace typed_22 {"` assertion at line 7607 is not covered by that
normalization and will still break. This proves the codebase already knows
this problem needs an explicit mitigation in some places; the brief doesn't
carry that lesson forward.)

I confirmed the blast radius is at least *contained* to the Python test
suite and generated `.cpp`/`.json` artifacts — `include/noisemaker/generated/catalog.hpp`
(the native-facing public surface) declares kernels by `bind_<key>` function
name, not by ordinal, and has zero `typed_N` references — but within the
Python test suite this is real, mechanical, and guaranteed, not speculative.

**Why this belongs in the design brief, not just implementation:** the task
prompt (and the brief's own reasoning about "the single biggest risk in this
task") flags this correctly as the sharpest risk in the whole task, precisely
*because* it's cheap to plan for now (list the 8 tests, decide whether to fix
each hardcoded literal or convert it to the existing `typed_N`→`typed_N`
normalization idiom) and expensive to discover mid-implementation when the
generator silently renumbers the whole file and 8 tests start failing with
opaque diffs. A brief this thorough on every other axis (line-number-exact
citations throughout) omitting this entirely — not even a one-sentence
acknowledgment — is a real gap, not a stylistic nitpick.

**Fix required before implementation begins:** add a short subsection to the
brief enumerating the 8 known affected tests above (or re-deriving the
current list live, since it may drift before implementation), stating the
concrete post-insertion expected values, and deciding whether to (a) hand-fix
each literal to its new ordinal, mirroring exactly how Task 30 fixed
`typed_52`→`typed_53` and Focus Blur `110`→`111`, or (b) generalize the
`typed_N`→`typed_N` normalization idiom already used at line 7602 to the
other 7 sites so future insertions near ordinal 0 don't recur as a surprise.
Either is acceptable; leaving it unplanned is not.

### Important

**I1 — The brief's "genuinely new" framing for the `floatBitsToUint` C++ lowering, and its treatment of NaN bit-pattern parity as an open question requiring operator sign-off, both overlook an already-existing, already-tested, semantically-identical function one header away.**

`include/noisemaker/numeric.hpp:15` already declares
`std::uint32_t float_bits_to_uint(float value) noexcept;`, implemented at
`src/numeric.cpp:50-52` as `return std::bit_cast<std::uint32_t>(value);` —
functionally identical to the brief's proposed new code
(`static_cast<float>(value)` then `bit_cast`, since
`noisemaker::f32(double)` at `src/numeric.cpp:9-11` is itself just
`static_cast<float>(value)`). This function already has a dedicated test
suite covering exactly the edge cases the brief flags as risky
(`tests/test_numeric.cpp:27-38`: `+0.0`/`-0.0` distinct bit patterns,
`+infinity`, round-trip through `uint_bits_to_float`, and NaN with an
explicit "NaN sign/exponent preserved, mantissa nonzero" assertion). Two
other already-shipped functions (`float_to_half_rte`, `float16_truncate`)
already depend on it in production code paths.

Critically, `include/noisemaker/glsl_types.hpp:11` — the exact file the
brief proposes adding a **new**, duplicate `constexpr` function to — already
`#include`s `"noisemaker/numeric.hpp"`, so `noisemaker::float_bits_to_uint`
is already reachable from that translation unit with zero new includes.

The brief's own diligence script
(`docs/port-engineering/task31_runtime_gap.py:37-40`) only searched for
the literal camelCase string `"floatBitsToUint"` inside two specific files
(`glsl_types.hpp`, `glsl_runtime.hpp`). Since the existing C++ function is
spelled in idiomatic snake_case (`float_bits_to_uint`) and lives in a third
file (`numeric.hpp`/`numeric.cpp`) reached only transitively, the script's
grep produced a technically-true but substantively misleading "absent"
result, and the brief inherited that framing ("genuinely new, ~1-2 lines,
confirmed absent from both runtime headers today").

This is not a correctness bug — both the brief's proposed code and the
existing function would produce numerically identical results, since both
ultimately reduce to `std::bit_cast<std::uint32_t>(static_cast<float>(value))`.
It is a reuse/duplication defect (two independent implementations of the
identical bit-reinterpretation operation, in two different namespaces) that
runs against the pattern already established elsewhere in this exact file
(`glsl::round` at `glsl_runtime.cpp:20` delegates to `noisemaker::glsl_round`
rather than reimplementing rounding), and it would very likely surface as a
finding at implementation-review time, forcing rework. More importantly, it
means the brief's flagged "NaN bit-pattern divergence risk needing operator
sign-off" is raised as an open unknown when a concrete, tested, existing
answer for the float-side of that question already sits in the same file's
own transitive include — that existing answer (and its test coverage) should
be surfaced to the operator as context for the sign-off decision, not treated
as though nothing in the codebase addresses it yet. (The double→float
narrowing question specifically for a NaN *double* input, matching JS
`Math.fround` semantics, is *not* fully answered by the existing tests, which
exercise `float` NaN inputs directly — so some open question legitimately
remains; it's just narrower than the brief implies.)

**Concrete fix:** the C++ Lowering section's recommended addition should be:

```cpp
[[nodiscard]] constexpr std::uint32_t float_bits_to_uint(double value) noexcept {
  return noisemaker::float_bits_to_uint(noisemaker::f32(value));
}
```

(or a thin non-`constexpr` inline delegating call, if `noisemaker::float_bits_to_uint`
can't be made `constexpr` — check before implementation, since `std::bit_cast`
itself is `constexpr`-friendly but the free function's declaration in
`numeric.hpp:15` is not currently marked `constexpr`) — reusing the
already-tested function and its already-established `f32()` narrowing helper,
rather than introducing a second implementation of the same operation.

### Minor

**M1 — Oracle provenance section leaves `public_catalog_sha256` applicability genuinely open, correctly disclosed but worth tightening before implementation.** The brief says "confirm during implementation whether a distinct 'public catalog' layer applies... since no `public-catalog.js`-named file was found." This is honestly flagged as uncertain rather than asserted, so it isn't a defect in the same sense as C1/I1, but since Task 30's own oracle recorded this field, leaving it unresolved risks an implementer either fabricating a value or silently omitting a field the provenance schema otherwise requires everywhere else. Worth a one-line resolution (even "N/A for classicNoisedeck-family effects, confirmed by X") before implementation starts, not deferred.

**M2 — The brief is not fully consistent about whether `authorized_caustic_floatbits` is a single object or a 1-tuple.** Section "Concrete implementation shape" says "checking identity against a new `authorized_caustic_floatbits` single-node tuple," but the actual precedent for a single authenticated builtin site (`round`) uses a bare object (`authorized_round`, not a tuple — see `generate_typed_slice.py:1955`: `if value is not authorized_round`), while the *plural*-site precedent (`all`/`lessThanEqual`, 2 authenticated nodes each) uses a tuple pattern. Since Caustic's `floatBitsToUint` closure has exactly one site, the `round`-style bare-object representation is the more direct precedent for *that specific piece*, even though the brief correctly says `round`'s *emission* strategy (fold-and-eliminate) is the wrong model overall. This is a small internal terminology inconsistency an implementer would resolve trivially, but worth tightening.

### Nits

**N1 — The "byte-count caveat" paragraph is good practice and should be the template for future briefs whose diagnostic renders use placeholder names.** No action needed; noting as a positive pattern worth preserving, given this review's own reproduction produced a *third*, still-different byte count (33,142) purely from a different placeholder function-name length, empirically confirming the caveat is warranted.

**N2 — "the single best adversarial-mutation candidate" (Perlin, for the foreign-program rejection test) is a reasonable pick but the brief doesn't mention `filter/pixelSort:gatherSorted` (which also has a `round`-adjacent identity-scoped exemption) as a secondary candidate for proving the exemption doesn't leak across identity-scoped mechanisms generally, not just the XOR one.** Not blocking — Perlin is the more structurally relevant adversarial case for the XOR half specifically — but a second, cheap adversarial case wouldn't hurt test breadth.

## Judgement on the ordinal-0 blast radius (as specifically requested)

The brief does **not** take this risk seriously enough. It correctly computes
and states the bare fact ("Caustic's zero-based ordinal in the new sorted
typed list: 0... it becomes the alphabetically first key") but treats this as
a data point to report rather than a risk to manage. Given that:

1. This exact class of risk already broke two things in the immediately
   preceding task (Task 30: `typed_52`→`typed_53`, Focus Blur `110`→`111`),
   and Task 30's own addendum flags it as a lesson;
2. Caustic's specific insertion point (ordinal 0, sorting before *every*
   other key) causes a full-corpus shift rather than Task 30's partial
   tail-shift, making it objectively larger in scope;
3. One of the affected tests (line 14668) contains an explicit code comment
   acknowledging this exact fragility mechanism;
4. I found 8 distinct, concretely-identifiable test methods (10 assertion
   sites) that will fail as a direct, mechanical consequence, with zero
   ambiguity about which ones or why;

...this was findable with the same tools and diligence the brief applied to
every other claim (a single `grep -n "typed_[0-9]\+" tests/test_typed_generator.py`
would have surfaced it in seconds). Its complete absence from a document that
is otherwise unusually rigorous is the standout gap in this review, and is
why the verdict is ACCEPT-WITH-BLOCKING-ITEM rather than a clean ACCEPT: the
brief should not be considered final until it names these 8 tests and states
the fix plan, exactly as thoroughly as it names every hash and line number
elsewhere.

## Verdict detail

- **C1 (ordinal-0 blast radius omission): BLOCKING.** Must be added to the
  brief before implementation begins.
- **I1 (floatBitsToUint duplication): should be fixed in the brief's C++
  Lowering section before implementation**, but is not blocking in the same
  sense — an implementer who reused `numeric.hpp`'s function on their own
  initiative would arrive at a strictly better outcome even without this
  review, and one who followed the brief literally would still produce a
  numerically-correct (if duplicative) result.
- M1, M2, N1, N2: non-blocking, recorded for completeness.

Once C1 is folded into the brief (and I1 ideally addressed too),
implementation may begin.


---

**Correction (2026-08-30):** this report described the half conversion as IEEE round-to-nearest-even (`float_to_half_rte`). The independent publication review proved the JS authority `floatToHalf` rounds half-up with subnormal pre-truncation; the port diverged on 8,420,351 of 2^32 float32 inputs and the suite pinned the wrong value. The function is now `float_to_half_js`, a verified transcription (exhaustive 2^32 differential, 0 divergent), and `half_to_float` now canonicalizes NaN like the authority (65,536-code differential, 0 divergent). See .superpowers fix-3 lane report of the 2026-08-29 publication review.
