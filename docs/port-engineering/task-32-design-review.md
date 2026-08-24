# Task 32 `filter/grade` cluster — independent adversarial design review

Reviewer: independent design-review agent. Read-only against
`noisemaker-for-cpp` (no file under that tree or under
`noisemaker-for-cpp-for-cpu/` was modified; no `git` command was run; no
Python test suite or cmake build was run — only standalone, in-memory calls
to `parse_program`/`analyze_program`, the same pure frontend functions the
brief itself used for its own probes).

Document under review: `docs/port-engineering/task-32-brief.md`,
sha256 `49202bb8bed668552b90ed1d5a32f3f6e9c29555a70c428bc0e7ac5153eb6892`
(verified matches the value the task named — confirmed via `shasum -a 256`).

Corpus revision confirmed identical to the brief's:
`a024dc3a960cc44af454abc7aebce50456c194e6` (path exists at
`noisemaker-for-cpp/tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6`).

Scratch artifacts (probes run for this review, all read-only):
- `docs/port-engineering/task32-review/probe_index_census.py` +
  `index_census_output.json` — independent AST census of all `index`-kind
  nodes in the six grade programs.
- `docs/port-engineering/task32-review/probe_reachability.py` +
  `reachability_output.json` — independent call-graph BFS from `main` for
  all six programs.

## Verdict: **ACCEPT — implementation may begin**

The core design (capability boundary in §8, the two new authentication
shapes, the vocabulary handling, the ordinal-shift math, reachability, and
discriminability findings) is independently reproduced and correct in every
case tested. However, three **Important** findings show the brief's
supporting narrative contains claims that are demonstrably false even though
they don't change the final capability boundary. Because this project's own
history shows exactly this class of error (a wrong "confirmed independently"
sentence) gets copy-pasted into implementation docstrings/comments and costs
a review cycle to catch later, **these three corrections are mandatory**
before the implementation report or any code comment repeats the brief's
wording verbatim. This mirrors the accepted precedent in
`task-30-implementation-report.md`'s addendum (ACCEPT with Important findings
required to be fixed, not treated as blocking the start of implementation).

---

## Critical

None found.

## Important

### I1 — §1's blanket claim "no existing track admits an id-indexed write" is false; the real reason is array-only base scoping

**Claim under review:** "all six existing tracks require a literal-int index
for a *store* (write/lvalue); the only track that accepts an `id`-kind index
(`read_valid`) is for reads only... None of the six existing tracks admits an
`id`-indexed **write**."

**Evidence it is false:** `generate_typed_slice.py:2131-2135`:

```python
grid_store_valid = (
    context == "lvalue" and index.kind == "id"
    and index.symbol_id is not None
    and (base.symbol_id, index.symbol_id, value.span)
    in proved_grid_dynamic_stores)
```

This is precisely an id-indexed **write** track (`FIXED_GRID_CAPABILITY`,
wired to `frontend/fixed_grid_counter_store_proof.py:12-14`, admitting
`filter/celShading:celShadingEdges` and `filter/outline:outlineSobel`'s
counter-driven 3x3 table stores). It has existed since (at least) the task
that landed those two programs.

**Why the brief's conclusion survives anyway:** every existing track,
including `grid_store_valid`, is gated by `base_valid`
(`generate_typed_slice.py:2118-2123`), which requires `base.symbol_id` to be
a member of `proved_array_declarations` or `proved_array_parameters` — i.e.
a **proved fixed-size array**. Grade's bases (`linear`, `srgb`, `rgb`,
`result`) are plain local `vec3`s with no array proof of any kind, so
`base_valid` is unconditionally `False` for all 74 sites regardless of
`index.kind` or read/write. This is the correct, narrower argument the brief
makes two paragraphs later ("these are not fixed-size arrays... the existing
`_proved_array`/`proved_array_declarations` machinery... cannot express even
in principle") — that argument is right and sufficient on its own.

**Fix:** delete or rewrite the "none of the six existing tracks admits an
id-indexed write" sentence. State the actual reason: existing tracks are
scoped to proved arrays via `base_valid`; grade's bases are plain locals,
which is what makes them inadmissible, independent of index kind.

### I2 — §1's specific first-blocker citation for `primary` is wrong: it names a read as "the write line"

**Claim under review:** "the first blocker after `global_admission` is
patched is always `unsupported typed expression index` pointing at the first
**write** site (e.g. `filter/grade:primary:41:13`, the `linear[i] =` line in
`linearToSrgb`), reproduced independently."

**Independently reproduced normalized source** (via
`tools.glslcpp.frontend.preprocess.normalize`, matching the parser's own
span coordinates):

```
38 vec3 linearToSrgb(vec3 linear) {
39     vec3 srgb;
40     for (int i = 0; i < 3; i++) {
41         if (linear[i] <= 0.0031308) {
42             srgb[i] = linear[i] * 12.92;
43         } else {
44             srgb[i] = 1.055 * pow(linear[i], 1.0 / 2.4) - 0.055;
45         }
46     }
47     return srgb;
48 }
```

Line 41 column 13 is `linear[i]` inside the `if` **condition** — a read, not
`linear[i] =` (there is no assignment on line 41 at all; the nearest
assignment is `srgb[i] = ...` at line 42). The brief's own §4b table gets
this right (`41:13-41:22 linearToSrgb rvalue ...`), directly contradicting
its own §1 prose for the identical span.

**Root cause, confirmed by direct probe:** `typed.functions` is ordered
**alphabetically by name**, not by source position. For `primary`, function
ids run `41 applyContrast, 42 applyCurve, 43 applySaturation,
44 applyTonalRanges, 45 applyWhiteBalance, 46 blacksWeight,
47 highlightWeight, 48 linearToSrgb, 49 main, 50 midtoneWeight,
51 shadowWeight, 52 srgbToLinear, 53 whitesWeight`. The validator's driver
loop is `for function in typed.functions:` at
`generate_typed_slice.py:2232`, so `linearToSrgb` (id 48) is walked before
`srgbToLinear` (id 52) and before `main`. Within `linearToSrgb`'s body, the
`if`-condition read is visited before the `then`-branch's assignment, so the
genuinely first `index`-kind node hit (once `global_admission` no longer
blocks) is the **read** at 41:13, not a write.

**Consequence:** this doesn't change the required capability boundary — §8
correctly requires admitting "id-indexed reads AND writes," and my own
independent AST census (below, confirming claim 2) shows both reads and
writes are equally blocked (by `base_valid`, not by a read/write-specific
gate). But an incorrect "reproduced independently" citation, used to support
the single most safety-critical claim in the document, is exactly the kind
of error this project's own culture flags as costly (see
`task-30-implementation-report.md`'s addendum: "the mutation test never
reached the novel logic," an equally subtle reproducibility gap that needed
a dedicated fix).

**Fix:** replace the citation with an accurate one, e.g. "the first blocker
is `41:13`, a **read** of `linear[i]` in the loop's `if` condition (the
first write, `srgb[i] =`, is at `42:13`) — both fail identically because
`base_valid` requires a proved array, which no grade base has."

### I3 — §9's "unprecedented... every prior task ported exactly one program" is false

**Claim under review:** "Six programs from one task is unprecedented (every
prior task ported exactly one program)."

**Evidence it is false:** Task 25 landed **two** programs in one task.
`tools/glslcpp/frontend/literal_vec3_lane_index_profile.py:12-14`:

```python
LENS_KEY = "classicNoisedeck/lensDistortion:lensDistortion"
PRISMATIC_KEY = "filter/prismaticAberration:prismaticAberration"
KEYS = (LENS_KEY, PRISMATIC_KEY)
```

confirmed by `task-25-brief.md:9-10` naming both keys as the task's targets,
and by the accepted profile module carrying two independent per-program
`_LOCKS` entries (own raw/whole/interface hashes and site tables for each).

**Consequence:** this doesn't weaken the brief's actual recommendation — a
real 2-program combined-task precedent that shipped safely, sharing one
capability shape across programs with independent per-program identity
scoping, is if anything a *better* argument for landing grade's six as one
task than "this has never been tried." But the specific "unprecedented"
framing is wrong and overstates the risk being accepted, which matters
because §9 uses that overstatement to structure its own risk discussion.

**Fix:** replace with "the largest such task (Task 25 landed two programs
sharing one capability shape; this is 3x that scale, not unprecedented in
kind)."

## Minor

### M1 — §2 "following the exact same template" overstates the fit with Smooth Edge's precedent

`frontend/smooth_edge_luma_weights_profile.py` hardcodes exactly **one**
frozen read path (`_READ_PATH = (0, "e0", 0, 1)`, line 30) for Smooth Edge's
single call site. Grade's five programs have variable read counts confirmed
by independent census: `primary` 4, `wheels` 2, `vignette` 1 (conditional),
`creative` 3, `hslSecondary` 0. Each new profile needs its read-site table
generalized to N paths, not literally copy-pasted from a 1-path template.
Mechanical, not a design flaw — reword to "same identity-scoped shape,
generalized to N read sites" so an implementer doesn't try to force a
single-path table onto e.g. `primary`'s 4 reads.

### M2 — §3's bespoke-factory-constant list wrongly includes Extrude

"as Extrude/Smooth Edge/degauss/CRT have" (a bespoke `canonicalFactoryNN`
identity constant). Confirmed: only `DEGAUSS_CANONICAL_FACTORY =
"canonicalFactory45"` (`generate_typed_slice.py:232`) and
`CRT_CANONICAL_FACTORY = "canonicalFactory44"` (line 291) exist. A full grep
for `canonicalFactory`/`FACTORY` near Extrude's wiring
(`extrude_bvec2_relational_reduction_profile`) found no analogous constant —
Extrude is authenticated by profile string alone, same as Smooth Edge. This
actually **strengthens** the brief's own conclusion ("treat grade like
Smooth Edge, no bespoke factory") since two of the four cited analogues, not
one, lack the pattern — but the example list should drop Extrude.

### M3 — §5's "bitEffects" citation is to an unlanded, analyzed-only precedent, not a landed one

"Must be flagged exactly as `bitEffects` was" implies an existing
implementation-report precedent to model wording from.
`classicNoisedeck/bitEffects:bitEffects` is confirmed **absent** from the
live `typed_slice.json` (0 matches) — it is analyzed only, in
`roadmap2/full-chain-frontier-map.md` §2, as a *future* candidate with the
same dead-code-global shape ("bitEffects's `mask` const global... referenced
only inside 12 dead helper functions"). The parallel reasoning is sound, but
there is no landed report to actually match wording against; reword to "the
same shape analyzed for the (not-yet-landed) bitEffects candidate."

## Nits

1. §7's ordinal-blast-radius framing ("every hardcoded `typed_NN`/
   ordinal-index assertion in `tests/test_typed_generator.py`... needs
   updating") undersells the diff's real scope. The `typed_NN` ordinal also
   names C++ namespaces directly inside the generated
   `src/typed_generated/typed_slice.cpp` (confirmed: `namespace typed_0`
   through `typed_130`, 524 total occurrences) — inserting at ordinal 29
   renames 102 of those namespaces (`typed_29`→`typed_35`, etc., mechanically
   the same shift already computed). Confirmed **harmless**: zero native
   `tests/*.cpp` files reference `typed_NN::` directly (`bind_<name>` factory
   functions are the only stable public surface), so this adds no risk, but
   the generated-file diff will be far larger than "test assertions" implies
   — worth a one-line heads-up so a reviewer isn't alarmed by the diff size.
2. §3's citation of `smooth_edge_luma_weights_profile.py`'s emitted output at
   `src/typed_generated/typed_slice.cpp:7469` is exactly correct (confirmed
   by `grep -n`), as is the `emit_typed_cpp.py:1244` index-fallback citation
   and the `emit_typed_cpp.py:721-725` `authorized_smooth_edge_luma_
   weights_declaration` citation — called out here only because so much of
   this review is corrections; these three specific line citations should be
   trusted as-is.

---

## Verification detail, by original claim number

**1. Six-files correction.** Confirmed exactly against
`corpus/.../manifest.json`: six `program_key` rows for `effect_id ==
"filter/grade"`, one per file under `sources/filter/grade/`, each with its
own `raw_bytes`/`raw_sha256`/`normalized_bytes`/`normalized_sha256`. All six
hash/byte pairs reproduced **byte-for-byte identical** to the brief's §3
table via direct manifest query. No file named `grade.glsl` exists. Confirmed
correct as stated.

**2. `index_expression_admission` is one structural shape.** Independent AST
census (`probe_index_census.py`, walking every `index`-kind node returned by
`analyze_program` for all six programs): **74 sites total**, per-program
counts `primary 10, hslSecondary 14, wheels 10, vignette 10, creative 10,
lut 20` — exact match to the brief. Every single site has
`(base.kind, index.kind) == ("id", "id")`; zero literal indices found
(`literal_index_count=0` for all six programs); zero non-`id` bases. The
headline shape claim is **exhaustively confirmed, not sampled**. The
structural-novelty argument (existing tracks require a proved array via
`base_valid`, which grade's plain-`vec3`-local bases can never satisfy) is
also confirmed by direct code read of `generate_typed_slice.py:2112-2163`
and `emit_typed_cpp.py:1129-1146` (`_proved_index`, which likewise requires
`self._proved_array(base.symbol_id)` to be non-`None`). See I1/I2 above for
the two narrative inaccuracies found while verifying this claim — neither
changes the headline 74-site, all-`id`/`id` result.

Site-level spot checks that all matched exactly: `hslToRgb`'s 4 write-only
sites (96:13, 98:13, 100:13, 102:13, all `write`, base `rgb`); `float(i)` in
`hslSecondary`'s `hslToRgb` confirmed `kind == "construct"` with a single
`id` child (not an `index` node), at 92:30.

**3. `global_admission` needs one new shape.** Confirmed by direct read of
`generate_typed_slice.py:1909-1954`: the only existing carve-out for a
non-`FLOAT` (i.e. vector) `const` global is the single object-identity check
`if declaration is authorized_smooth_edge_luma_weights_declaration` (line
1923) — every other path requires `declaration.type != FLOAT` to be false,
i.e. rejects anything but scalar float. This means generalizing to "any
`const vec3`" is not merely undesirable but requires structurally different
code than exists today; five new identity-scoped carve-outs (mirroring the
existing one) are the only shape consistent with the current architecture.
`hslSecondary`'s `PI` confirmed to pass through the generic
`storage=="const" and type==FLOAT` path unmodified (no vec3 involved). `lut`
confirmed to have **zero** `const` declarations (`grep` returned no matches).
See M1 for the one overstatement found (variable read-count generalization
needed, not a literal copy of Smooth Edge's one-path template).

**4. Reachability.** Independent call-graph BFS from `main`
(`probe_reachability.py`, built purely from `call`-kind nodes'
`signature_id`) reproduced **exactly**: `primary 13/13, hslSecondary 7/7,
wheels 7/7, vignette 5/5, creative 6/6, lut 28/28`, zero unreachable
functions in any of the six. `metadata.json`'s `filter/grade` effect
confirmed: all 39 params map to `"uniform"`, zero map to `"define"`; the only
`#ifdef` in any of the six source files is the standard `#ifdef GL_ES`
precision guard (not a dispatch define). `preset` confirmed a uniform `int`
with `hardLight: 20` and `solarize: 22` in its `choices` map, matching the
claim that `lutHardLight`/`lutSolarize` are reached via a runtime branch, not
preprocessor exclusion.

**5. Discriminability.** Confirmed by direct symbol-id census:
`hslSecondary`'s `LUMA_WEIGHTS` has **zero** reads across all 7 functions
(confirmed exhaustively, not `#ifdef`-gated). The other four programs' read
counts and call sites reproduced exactly against §4a/§5's tables (`primary`
4 reads in `applyContrast`/`applyCurve`/`applySaturation`/
`applyTonalRanges`; `wheels` 2 in `applyWheels`; `vignette` 1 in
`applyVignette`; `creative` 3 in `applyFadedFilm`/`applySplitTone`/
`applyVibrance`). `vignette`'s conditional-read claim confirmed against
source: `applyVignette(vec3 rgb, float vignetteMask, float amount, float
highlightProtect)` reads `LUMA_WEIGHTS` only inside `if (highlightProtect >
0.0) { ... }` (normalized line 80), and `main` passes the uniform
`vigHiProtect` as that parameter (`rgb = applyVignette(rgb, vignetteMask,
vignetteAmount, vigHiProtect);`) — the test-plan naming (`vigHiProtect>0`)
and the discriminability-table naming (`highlightProtect > 0.0`) are
consistent, just at different call levels. No unused-global rejection exists
in the admission loop (confirmed: `generate_typed_slice.py:1916-1954` checks
only storage/type/initializer shape, never usage) — `PI` and dead
`LUMA_WEIGHTS` both pass admission for that reason, as claimed. On the
"is admitting a never-read global acceptable" question: yes, given the
`bitEffects`-shape precedent (see M3 — real as an *analyzed* pattern, not yet
a landed one) and given the brief's own explicit requirement (§8) that the
implementation report must disclose it as structurally-validated-only, never
implied render-proven. The alternative (excluding it from the closure and
instead rejecting the whole program at that declaration) is not viable —
`hslSecondary`'s LUMA_WEIGHTS genuinely exists in the accepted source and
must type-check for the program to compile at all; the disclosure
requirement is the correct mitigation, not exclusion.

**6. Vocabulary.** Confirmed by direct code read: the `admitted_globals`
loop and `audit_expression` (`generate_typed_slice.py:1909-1975`) never
reference `used` at all — zero `used.add` calls in that span, confirming
`global_admission` is vocabulary-free. The `index`-kind branch
(`generate_typed_slice.py:2112-2163`) **does** call `used.add(...)` on every
matched path (`FIXED_AFFINE_CENTERS13_CAPABILITY`,
`FIXED_ARRAY_PARAMETER_CAPABILITY`, `FIXED_GRID_CAPABILITY`,
`FIXED_NINE_CAPABILITY`, lines 2157-2163), and the existing skip-list
precedent (`round`/`all`/`lessThanEqual`/`floatBitsToUint`/`tanh`, lines
2107-2109) is real and exactly as cited, confirming the required design
(grade's index track must skip `used.add` entirely, mirroring that callee
skip-list, not reuse an existing FIXED_* token). `APPROVED_CAPABILITIES`
confirmed to have exactly **44** entries by direct import and `len()` call.

**7. Zero new C++ runtime.** Confirmed: `Vec<N,T>::operator[]` at
`include/noisemaker/glsl_types.hpp:119-120`, generic over `N`/`T`, returns a
concrete `T&`/`const T&` (never a lazy `FloatExpr`). `emit_typed_cpp.py`'s
index fallback confirmed at **exactly** line 1244:
`f"{self.expression(value.children[0])}[{self.expression(value.children[1])}]"`.
`_proved_index` confirmed at lines 1129-1146, gated on `self._proved_array(
base.symbol_id)` being non-`None` — always `None` for grade's plain-`vec3`
locals, confirming the emitter-side gap is exactly what the brief says (a
new `_proved_...` predicate, not new runtime). Smooth Edge's already-shipped
emission confirmed byte-for-byte at `src/typed_generated/typed_slice.cpp:
7469`: `const glsl::Vec3 LUMA_WEIGHTS = glsl::FloatExpr<3>(static_cast<float>
(0.299), static_cast<float>(0.587), static_cast<float>(0.114));`. Constraint
(e) (no Curl-class narrowing hazard) spot-checked: `pow(double, double)` at
`include/noisemaker/glsl_runtime.hpp:42` is a distinct scalar overload from
the `Vec<N,float>` two-argument overloads at lines 96-100, confirming it
never touches the single-argument `NOISEMAKER_GLSL_UNARY_VECTOR` macro family
that caused Task 31's Curl regression.

**8. Ordinal blast radius.** Independently recomputed from the live
`typed_slice.json`: current typed count **131**, typed-list SHA-256
`ea5c0628...` — matches the brief's frozen value exactly. Projected count
**137**, projected typed-list SHA-256
`dfb7c7c43d7fd118c4a1b9a266d6957a90b189ec63ac6b0d49538bd853a360d7` — matches
exactly. Insertion position (via `bisect_left`) confirmed at ordinal **29**;
count of currently-typed keys sorting at or after the first grade key
confirmed **exactly 102**. The reconstruction argument was independently
tested (not merely trusted): removing the six grade keys from the projected
137-key sorted list reproduces the original 131-key sorted list **and** its
frozen SHA-256 exactly. This corroborates but does not fully discharge the
brief's own framing that this "must be argued explicitly, not assumed" —
what I verified is the sorted-key-list identity; the brief's own §8 test
plan additionally proposes regenerating the full `typed_slice.cpp` byte
output for the reconstructed 131-program case, which this review did not run
(out of scope: no cmake/full-suite execution permitted) and should still be
executed as the brief itself proposes. See Nit 1 for the related
`typed_NN`-namespace-rename scope note (confirmed harmless).

**9. One task or six?** See I3 for the factual correction to the
"unprecedented" framing. With that correction, the brief's substantive
arguments for landing as one task hold: the two capability shapes are shared
in full, verified reachability/discriminability findings are per-program and
already itemized individually (not averaged), and Task 25's 2-program
precedent shows the combined-task pattern is safe when programs don't share
runtime state and each authenticates independently by its own `source_hash`
— which is confirmed true here (each of the six is authenticated from its
own frozen `raw_sha`/`whole`/`interface` hashes per §3/§4). **Recommendation:
land as one task**, per the brief's own §9 structuring (shared
index-admission machinery once, six independent profile modules, ordinal/test
updates once), with the corrected precedent framing from I3.

**10. Other traps.** The three Important findings above are exactly the kind
of "cost a full implementation cycle" trap the task's background docs warn
about (per `task-31-curl-SOLVED.md`'s own harness-error confessions and
`task-30-implementation-report.md`'s addendum about a mutation test that
"never reached the novel logic"). No additional structural traps were found
beyond those three plus the Minor/Nit items above.

---

## Judgement on the dead-code global (`hslSecondary`'s `LUMA_WEIGHTS`)

Admitting it is acceptable, and excluding it from the closure is not a
viable alternative — the declaration exists in the accepted, frozen source
and must type-check for the program to compile at all; there is no
"conditionally admit only if read" mechanism in this codebase and adding one
would itself be new, riskier machinery for a single dead declaration. The
brief's required mitigation (explicit non-discriminability disclosure in the
implementation report and native test suite, never implying a render proved
it) is the correct and sufficient safeguard, consistent with the
(not-yet-landed but analytically established, see M3) `bitEffects` pattern.

## One-task-or-split recommendation

**Land as one task**, six explicitly-enumerated sub-units within it, per the
brief's own §9 structuring — this recommendation is unchanged by this
review's findings, once the "unprecedented" framing in I3 is corrected to
"largest of this kind, following Task 25's 2-program precedent at 3x scale."
