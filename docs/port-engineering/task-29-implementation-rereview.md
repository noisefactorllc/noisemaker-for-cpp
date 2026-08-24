# Task 29 implementation re-review: Focus Blur borrowed-sampler ABI

Date: 2026-08-12
Reviewer: independent, adversarial re-review agent (no prior involvement in Task 29)

## Verdict

**ACCEPT.** No Critical or Important findings. Every claim in
`task-29-implementation-report.md` that was checked against hard evidence
reproduced exactly. Two Minor findings and one Nit are recorded below; none
block acceptance and none touch production code, the ABI, or test coverage.

Findings by severity: **Critical: 0, Important: 0, Minor: 2, Nit: 1.**

## Method

All findings below are backed by commands I ran myself in this session,
against the untouched working tree at `.`
(read-only; no edits made). No git was used (the tree has no `.git`, per
constraint). Fresh builds were done in `/tmp/nm-cpp-review-build` (Release,
`-Wall -Wextra -Wpedantic -Werror`) and `/tmp/nm-cpp-review-asan` (Debug,
`-fsanitize=address,undefined`).

---

## 1. ABI narrowness — CONFIRMED, cannot leak

`tools/glslcpp/emit_typed_cpp.py:78-84` (`_TYPES`) has no `sampler2D` entry.
`function_type()` (line 736-737) routes through `self.type()` → `_TYPES`, so
any generic sampler use still raises `unsupported typed type sampler2D`
(`emit_typed_cpp.py:723-728`). The only sampler-to-`Surface&` path is
`function_parameter_type()` (`emit_typed_cpp.py:739-766`), gated by
**object identity** (`is`) against `focus.sampler_parameters`, plus an
independent re-check of `function is not focus.helper`, `ordinal not in
(0, 1)`, and `parameter.type.display() != "sampler2D"` (lines 741-750).
`focus` itself is populated only when
`self.focus_blur_borrowed_sampler_profile is not None` **and**
`self.program.key == FOCUS_BLUR_KEY` (`emit_typed_cpp.py:193-215`); any other
program hitting `FOCUS_BLUR_KEY`'s branch with the profile absent raises
`"exact Focus Blur borrowed sampler profile carrier required"` before
emission starts.

Counterexample reproduced live (not read from the census file):

```
$ python3 -c "... render_typed_cpp(program, key, entry['raw_sha256']) ..."
  # key = 'mixer/distortion:distortion'
emit failed as expected: TypedEmissionError mixer/distortion:distortion:1:1: unsupported typed type sampler2D
```

and, feeding the real Focus Blur profile string to the foreign
`mixer/distortion:distortion` program:

```
rejected as expected: TypedEmissionError mixer/distortion:distortion:1:1: Focus Blur borrowed sampler profile metadata mismatch
```

`typed_slice.json` has exactly one entry carrying
`focus_blur_borrowed_sampler_profile`
(`{"program_key": "mixer/focusBlur:focusBlur", ...}`), confirmed by direct
`json.load`. `generate_typed_slice.py:694-707` hash-pins the ordered program
key list and the schema-shape check at lines 657-673 rejects any program that
carries the `focus_blur_borrowed_sampler_profile` key without also being
`FOCUS_BLUR_KEY` (`expected` set is keyed off `key == FOCUS_BLUR_KEY`).

I additionally rendered the real Focus Blur program standalone and counted
`const Surface&` occurrences in the output: 7 total, of which 3 are
pre-existing boilerplate (`sample_texture`, `fetch_texel`, `texture_size`
helpers, lines 16/20/24 of the emitted block) and exactly 4 are the two
sampler parameters × {declaration, definition} of `applyFocusBlur` — matching
the design's "exactly two … in the declaration and two … in the definition."

**Conclusion: the ABI genuinely cannot leak to any other program.** `_TYPES`
was not widened; `function_type()` (the generic path) was not touched.

## 2. Validator/emitter independence — CONFIRMED

Both the validator (`generate_typed_slice.validate_capabilities`,
lines 1364-1386) and the emitter (`_Emitter.__post_init__`, lines 193-215)
call `authenticate_focus_blur_borrowed_sampler_parameters` themselves, from
scratch, on the `TypedProgram` object — neither reads an "authorized" flag
set by the other. `generate_typed_slice.py:2201-2211` also calls
`apply_focus_blur_borrowed_sampler_parameters` (identity function that itself
authenticates) before validation, so there are three independent
authentication calls in the real pipeline for one program.

I independently drove `render_typed_cpp` (the emitter entry point) directly,
bypassing the validator entirely:

- Absent profile on `mixer/focusBlur:focusBlur` itself: rejected —
  `"exact Focus Blur borrowed sampler profile carrier required"`.
- Wrong profile string (`"bogus-profile-v1"`): rejected —
  `"focus-blur-borrowed-sampler-parameters-v1: exact profile carrier
  required"`.
- Correct profile: emission succeeds, exactly 4 `const Surface&` sampler
  parameter sites as described above.

Fail-closed behavior holds with the validator entirely absent from the call
graph, which is the actual test of independence (a shared-trust bug would
only manifest when one side is skipped).

## 3. Historical integrity — CONFIRMED, no hash tampering, no weakened reconstruction

The task brief specifically worried that the prior session's edit to
`tests/test_typed_generator.py` (subtracting Focus Blur from Task 21-28
historical reconstructions) might have narrowed to "subtract only Focus Blur"
in some places, silently corrupting historical baselines by leaving
later-added programs in state.

I grepped every occurrence of `"filter/rotate:rot"` (the Task 28 exclusion
key used before Task 29 existed) in `tests/test_typed_generator.py` and
checked each site by hand (lines 491, 1367, 2220/2224, 4855, 7231, 7437, 8498,
8618, 8854, 9051, 11034, 11143, 12004, 12057, 12084). **Every single site that
excludes `filter/rotate:rot` also excludes `mixer/focusBlur:focusBlur`**,
consistent with a mechanical "the same programs that needed excluding before
Task 29 still need excluding, plus Focus Blur" edit, not selective narrowing.

For the two tests that do **real** historical reconstruction (regenerate
bytes via `generate_typed_slice.generate_outputs` under
`mock.patch.object(..., "load_slice", ...)` and hash-compare against frozen
output hashes, as opposed to just hashing a key list):

- `test_task28_schema_generation_and_task27_reconstruction`
  (`tests/test_typed_generator.py:13081`): subtracts Focus Blur to reach the
  accepted Task 28 baseline (128 programs, hash `30f0333c...`, matching the
  design brief's stated Task 28 baseline), then further subtracts
  `filter/rotate:rot` to reconstruct Task 27 and compares 3 output file
  hashes against frozen constants. **I ran this test live: PASS (58.7s).**
- `test_task29_schema_counts_hashes_and_real_task28_reconstruction_isolation`
  (line 13834): subtracts only Focus Blur (129→128) to reconstruct Task 28,
  and separately proves the *only* structural diff between current (129
  blocks) and reconstructed (128 blocks) `typed_slice.cpp` is the Focus Blur
  block itself (`set(current_blocks) - set(task28_blocks) == {FOCUS_BLUR_KEY}`,
  line 13925-13926), with every retained block byte-identical modulo ordinal
  renumbering. **I ran this test live: PASS (60.1s).**

I cross-checked every frozen hash constant these two tests assert against
independent, pre-Task-29 documents in `docs/port-engineering/` (Task 27
and Task 28's own implementation reports/rereviews, authored before Task 29
existed):

- `30f0333c...` / `102f5436...` (Task 28 typed/public) — present in
  `task-28-brief.md` and this session's own frontier audit.
- `aa15e469...` / `f25401d4...` / `b82abfa0...` (Task 27 reconstruction
  outputs) — present in `task-27-implementation-report.md` and
  `task-28-brief.md`.
- `b53e020b...` / `612d3522...` / `372d1f69...` (Task 28 reconstruction
  outputs) — present in `task-28-implementation-report.md` and
  `task-28-implementation-rereview.md`.
- `df4aa212...` / `e7f7acd5...` / `557ccdbe...` (Task 26 reconstruction
  outputs, used by Task 27's own delta test) — present in
  `task-26-implementation-report.md` and `task-27-implementation-report.md`.

None of these values were edited; they match documents this session did not
author. **No evidence of hash tampering to force green tests.**

**Minor finding M1:** `test_task26_loader_admits_only_exact_smooth_carrier_and_census`
(`tests/test_typed_generator.py:11024-11052`) and its siblings
`test_task21_degauss_exclusions_remain_closed` (line 7429) and
`test_task22_crt_exclusions_remain_closed` (line 8488) filter only
`{"filter/rotate:rot", "mixer/focusBlur:focusBlur"}` and **not**
`synth/perlin:perlin`, despite Perlin (Task 27) being added after Task 26,
21, and 22. I confirmed directly (`python3` one-liner against the live
`typed_slice.json`) that Perlin is genuinely present in the resulting 127/122-
program lists these tests hash-pin — the tests are not reconstructing a true
"as-of-Task-N" state despite their names implying it; they reconstruct
"current minus the two most-recently-added generalized-profile programs."
This is **pre-existing test design** (the same narrow two-key exclusion
pattern was already used for `filter/rotate:rot` alone before Focus Blur
existed) — the Task 29 repair correctly and mechanically extended the
existing pattern rather than introducing it. Not a defect introduced by this
implementation, but the test names are misleading for future readers auditing
"historical" state. Recommend (not blocking): rename these three tests to
drop "task21/22/26 exclusions" framing, or add a comment noting the exclusion
set is intentionally narrower than full historical reconstruction.

## 4. Mutation barriers — CONFIRMED genuine, not softened

`test_task29_exhaustive_single_axis_protected_coordinate_negative_closure`
(line 13381) constructs 89 single-axis `dataclasses.replace` mutations,
hash-pins the axis name list (`30f64470...`), asserts all 89 produce distinct
candidates, asserts each mutation leaves every *other* coordinate untouched,
and requires each candidate to be independently rejected by the profile
authenticator, the validator, **and** the emitter (3 layers × 89 axes = 267
assertions). I ran it live: PASS (0.5s).

I independently reproduced two of the 89 mutations **outside** the test
harness, calling `authenticate_focus_blur_borrowed_sampler_parameters`
directly on hand-built `dataclasses.replace` candidates never touched by the
test file:

- Renamed helper (`applyFocusBlur` → `otherFocusBlur`): rejected —
  `"source, define, function, whole-program, or interface mismatch"`.
- Loop count 1 → 2: rejected — same message (the mismatch is caught by the
  aggregate whole-program hash before the more granular checks run).

`test_task29_full_carrier_caller_numeric_defines_and_coexistence_matrix`
(line 13662) covers a 90-combination cross product of
(defines × carrier × caller-hash × numeric-contract), asserting exactly 1 of
90 is accepted, plus an 8-way coexistence matrix against every other profile
carrier in the codebase (CRT compatibility transform, Lens custom comparer,
source-global-literal-int, Gather Sorted, literal-vec3-lane, Smooth Edge,
Perlin, Rotate) — each rejected at both validator and emitter layers. I ran
it live: PASS.

`test_task29_complete_call_ancestry_move_copy_swap_and_predicate_controls_reject`
(line 13563) covers predicate replacement, branch swap, call move/copy, and
call-slot swap per the brief's requirement. Ran live: PASS.

**No evidence of softened assertions.** The mutation coverage is exhaustive
and independently reproducible.

## 5. The counter-test fix — ADEQUATE, correctly disclosed

I independently derived the 67/67 figure by reading the emitted
`mixer/focusBlur:focusBlur` block in `src/typed_generated/typed_slice.cpp`
(namespace `typed_110`) line by line:

- `applyFocusBlur`: one `sample_texture(depthTex, …)` before the loop (line
  34 of the extracted block), paired with one `texture_size(depthTex)`
  (nested in the same expression); a `for (i = 0; i < 64; ++i)` loop (line
  39) whose body executes one `sample_texture(sceneTex, …)` + one
  `texture_size(sceneTex)` per trip (line 43) → 64 of each at runtime.
  Runtime total for the helper: 1 + 64 = 65 of each.
- `pixel`: exactly one of the two mutually-exclusive `applyFocusBlur` calls
  executes (line 65-69, `if (depthSource == 0) … else …`), contributing the
  65 above once; then two unconditional alpha sites (line 70,
  `component_max` over both `*state.inputTex` and `*state.tex` samples), each
  paired with its own `texture_size` — 2 more of each.
- Total: 65 + 2 = **67 texture reads and 67 texture_size queries per pixel**,
  independently confirmed, matching the report's claim exactly.

The renamed test
(`typed_task29_reference_trace_model_matches_derived_sixty_seven_read_profile`,
`tests/test_generated_kernels.cpp:8863`) only asserts the **reference model**
(`task29_trace_selected_focus_path`) self-consistently produces 67/67 by
construction — it does not and cannot instrument the actual generated kernel,
which exposes no interception point. The doc comment directly above the
reference model's definition (lines 8444-8455) discloses this precisely:
states the figure is DERIVED, names the three artifacts that carry the real
evidence (static site counts pinned by
`test_task29_schema_counts_hashes_and_real_task28_reconstruction_isolation`,
the counted-loop proof, and the six pixel fixtures against the independent JS
oracle), and states plainly that semantic parity rests on the pixel fixtures,
not the counters. I consider this an honest, adequate disclosure — a reader
of the test name plus its immediately-adjacent comment cannot come away
believing the generated kernel was dynamically instrumented.

I confirmed the rename did not break any Python assertion: the transcription
test `test_task29_cpp_tables_switch_helpers_and_witnesses_are_exact_frozen_transcription`
(line 13948) pins the `dispatch_suffix` region's *function name*
`task29_trace_selected_focus_path` (asserted at lines 14063-14064), never the
`TEST(...)` macro name. Ran live: PASS, alongside the rest of the 7-test
Task 29 class (7 tests, 78.9s, all green — matches report's 82.3s within
normal machine variance).

**Nit N1:** the reference model's doc comment is good but lives only at the
function definition; the `TEST()` block itself (line 8863) carries no
comment repeating the "this is a self-consistency check on the reference
model, not kernel instrumentation" framing. A reader who jumps straight to
the `TEST()` body without scrolling up 400 lines to the function definition
could still be misled for a few seconds. Cosmetic; not blocking.

## 6. Parity chain — CONFIRMED, not circular

Read `docs/port-engineering/task-29-oracle-generator.mjs` in full. Its
only imports are from `../noisemaker-for-cpu/src/...`
(the JS reference renderer) — `catalog.js`, `glsl-kernel.js`,
`pass-runner.js`, `surface.js`. It reads the shared GLSL corpus source file
only to hash-check it (`sourcePath`, line 15, checked against
`provenance.source_sha256` at line 38) — it never imports, shells out to, or
reads any file under `noisemaker-for-cpp`. **No dependency on the C++
implementation or its outputs.**

I ran it fresh:

```
$ node task-29-oracle-generator.mjs --check
Task29 Focus Blur oracle fixture ok (6 public cases, 8 direct modes)
```

and confirmed `task-29-oracles.json`'s SHA-256
(`b16c120e2331d87b61b98154d63954ad52ff328f149ebeb67b66321b73bde0a3`) matches
exactly what `test_task29_cpp_tables_switch_helpers_and_witnesses_are_exact_frozen_transcription`
pins. The chain (JS oracle → hash-pinned JSON → Python transcription
assertion → native kernel execution against those tables) is real and
one-directional; the generator has no path back into the C++ side.

## 7. Additional independent verification performed

- `python3 -m tools.glslcpp.check_corpus --check` → `check_corpus: ok`
  (fresh run, this session).
- `python3 -m tools.glslcpp.check_semantics --check` → `check_semantics:
  bodies ok (212 programs)` (fresh run).
- `python3 -m tools.glslcpp.generate_typed_slice --check` → `generate_typed_slice:
  typed slice ok (129 programs)` (fresh run).
- Fresh Release build (`-Wall -Wextra -Wpedantic -Werror`, new directory
  `/tmp/nm-cpp-review-build`): 0 warnings, exit 0, all 143 native tests PASS,
  0 FAIL, including all 4 Task 29 tests by name.
- Fresh Debug+ASan/UBSan build (new directory `/tmp/nm-cpp-review-asan`,
  `-fsanitize=address,undefined`), run with `ASAN_OPTIONS=detect_leaks=0`
  (the platform's documented ASan/`detect_leaks` incompatibility): 143/143
  PASS, 0 FAIL, 0 sanitizer diagnostics, exit 0 — including the lifetime test
  that destroys `Bindings` after binding while the `Surface` objects remain
  alive (`tests/test_generated_kernels.cpp:8234-8237`), which is the specific
  scenario the design brief required sanitizer coverage for.
- `python3 task-29-recompute.py --check` (the frozen design-time script) →
  confirmed exit 1 with `StopIteration` at line 464, exactly as the report
  describes, run without a pipe to avoid masking the real exit code. This is
  a standalone `/tmp` artifact, not part of the pytest/unittest discovery the
  build depends on; its documented obsolescence (Focus Blur no longer being
  in the "unsupported" frontier it enumerates) is accurately characterized as
  a known, harmless limitation rather than a live gate failure.

**Minor finding M2:** the report's "Known limitation" section is accurate but
undersold: `task-29-recompute.py --check` doesn't just report a benign
mismatch, it throws an unhandled `StopIteration` traceback (Python 3.7+
turns an escaped `StopIteration` inside generator-adjacent code into a hard
crash rather than a clean message). Anyone running this script cold, without
having read the implementation report first, gets a stack trace with no
"this is expected, Focus Blur is no longer in the unsupported frontier"
context. Recommend (not blocking, out of scope for this task since the
script is explicitly frozen/design-time and the report already discloses the
behavior in prose): a future cleanup pass could catch `StopIteration` and
print a one-line explanation, but per the brief's own instruction ("the
frozen artifact and its sidecar are left unmodified"), leaving it untouched
was the correct call for this task.

## Summary of findings

| # | Severity | Finding | Location |
|---|----------|---------|----------|
| M1 | Minor | Three pre-existing "exclusions remain closed" tests (Task 21/22/26) have names implying full historical reconstruction but only exclude the two most-recently-added generalized-profile programs, leaving intervening programs (e.g. Perlin) present. Pre-existing pattern, correctly and mechanically extended by this session, not introduced by it. | `tests/test_typed_generator.py:7429, 8488, 11024` |
| M2 | Minor | `task-29-recompute.py --check`'s expected failure surfaces as a raw `StopIteration` traceback rather than a clear message; report discloses this in prose but the script itself doesn't. Frozen artifact, correctly left untouched per the design brief. | `docs/port-engineering/task-29-recompute.py:464` |
| N1 | Nit | The reference-model disclosure comment lives only at the function definition, ~400 lines above the `TEST()` block that uses it. | `tests/test_generated_kernels.cpp:8444-8455, 8863` |

No Critical or Important findings were identified against any of the seven
review questions. Every quantitative claim in the implementation report that
I attempted to independently reproduce (test counts, hashes, PASS lines,
warning counts, sanitizer cleanliness, oracle reproducibility, the 67/67
derivation, and the exclusivity of the borrowed-sampler ABI to Focus Blur)
reproduced exactly.

## Verdict

**ACCEPT.** No blocking items.
