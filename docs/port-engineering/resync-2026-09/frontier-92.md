# Frontier-92: typed-pipeline census of the 92 net-new GLSL program keys

**Scope.** The 92 `status: "missing"` program keys computed from
`src/effects/generated/backend_compatibility.json` (`reference_key_closure`
minus `canonical_programs` minus the one scatter-registered key,
`filter/wormhole:deposit`) at revision `0ed489ec46842bffba33ee2ec65a218b6dda51f5`.
Every program was probed **individually, from raw upstream GLSL, through the
real typed pipeline** (not a manifest-driven corpus row — these keys are not
in `tools/glslcpp/corpus/`, so there was nothing to load them from). No
frontend profile was added or changed; nothing in the repository was edited.

**Bottom line.** The 92-key gap is **not primarily a typed-GLSL-frontier
problem.** Probed in isolation, **49 of the 92 programs (53%) already pass
parse → declaration analysis → body semantic analysis → loop/counted-for
proofs → capability validation → the typed C++ emitter with zero errors**,
using no frontend changes at all. Of those 49, 4 pass only because the
emitter has a **silent correctness bug** for multi-output programs (see
below) — so **45 are genuinely, fully clean**. The other 43 hit a real,
specific construct gap, concentrated in about a dozen classes, several of
which are one shared mechanism away from unblocking multiple programs at
once.

This inverts the naive read of "92 missing programs, must all need frontend
work." Most of the actual admission cost for this batch is downstream of the
typed generator — in the runtime executor's iteration/MRT/scatter machinery
that `docs/port-engineering/` and `.nm-cpp-work/phase2-architecture.md`
already scoped in detail. This report's job is to nail down precisely what
*does* need frontend/typed-generator work, since that part had no
prior program-by-program evidence.

---

## 1. Method

### 1.1 Harness

No existing tool runs one out-of-corpus program through the pipeline in
isolation — `tools/glslcpp/check_corpus.py`/`check_semantics.py` are
manifest-driven over the pinned 212-program corpus, and
`docs/port-engineering/frontier_census.py` (the closest precedent, used for
the now-fully-resolved `FRONTIER-2026-08-13.md` census) is also
manifest-driven, over a *different* revision's corpus of already-admitted
programs. Both were read in full. Neither has a "probe this raw string as if
it were program X" entry point, so this task built one:
`<scratch>/probe92.py`
(rev-alongside `finalize.py`), which imports and calls these exact,
unmodified functions:

| Stage | Function called | What it catches |
|---|---|---|
| 0 (evidence only) | `tools/glslcpp/frontend/preprocess.py:normalize` | preprocessor errors; **also used to record what `normalize()` alone thinks the outputs/varyings are**, since this is where the MRT finding below starts |
| 1 (parse) | `tools/glslcpp/frontend/__init__.py:parse_program` | normalize + tokenize + parse + span-stripping; syntax errors (`FrontendError`) |
| 2 (semantic) | `tools/glslcpp/frontend/semantic.py:analyze_program` | declaration collection, `BodyAnalyzer` body semantic checks, and `attach_counted_loop_proofs`/`authenticate_source_global_literal_int`/`attach_discarded_local_counter_proofs`/`prove_fixed_nine_local_tables` — **all four are called inside this one function**, in that order, so this task classifies which one produced a given failure by its diagnostic *code* (`E_UNKNOWN_TYPE`/`E_DUPLICATE_*` = declaration; `E_UNKNOWN_SYMBOL`/`E_TYPE`/`E_OPERATOR`/`E_NO_OVERLOAD` = body; `"unsupported counted-for..."`/`E_SOURCE_GLOBAL_LITERAL_INT` = loop proof), not by an isolated call — there is no seam to call them separately without editing `semantic.py`, which was out of scope |
| 3 (validator) | `tools/glslcpp/generate_typed_slice.py:validate_capabilities` | called independently even when stage 2 passed, exactly like `frontier_census.py` does — its failure is recorded separately from the emitter's |
| 4 (emitter) | `tools/glslcpp/emit_typed_cpp.py:render_typed_cpp` | called independently, same rationale |

Every call passed **all profile kwargs as `None`** (the default). Per
`FRONTIER-2026-08-13.md`'s own explicit warning ("pass a profile kwarg ONLY
for its actual carriers; non-carriers raise 'not an admitted carrier', which
looks like a blocker but is a probe artifact"), and independently confirmed
by this task (§1.2), none of the 92 foreign keys are the hardcoded carrier of
any existing per-program profile — so passing none is the *only* correct
probe, not a simplification.

Sources came from `git -C <noisemaker git> show
0ed489ec46842bffba33ee2ec65a218b6dda51f5:shaders/effects/<id>/glsl/<program>.{glsl,frag,vert}`
(86 single `.glsl` files, 6 `.frag`+`.vert` pairs — see §2.2). Default
`#define` values came from the JS authority's
`src/effects/generated/upstream-snapshot.js` (`effectRecords[].params[].define`/`.default`),
the same shape `check_semantics.py._metadata_defaults` builds for the 212
corpus, just sourced from the authority snapshot instead of the (inapplicable,
these keys aren't in it) corpus `metadata.json`.

### 1.2 Harness validation

1. **Sample of already-admitted programs.** `probe_source()` was run against
   12 randomly-sampled (`seed=42`) programs from the real 212-program corpus,
   using their real corpus metadata defines. 9/12 reached `emitter_pass`
   cleanly. The other 3 (`filter/grade:vignette`, `filter/spinBlur:spinBlur`,
   `filter/wormhole:deposit`) reported "exact ... profile carrier required" —
   this is the documented profile-artifact, not a regression: these three
   *are* hardcoded per-key carriers (of `grade_luma_weights_profile`,
   `source_global_literal_int_profile`, and the scatter-only exclusion,
   respectively) and require their own profile kwarg to pass, exactly as
   `FRONTIER-2026-08-13.md` describes. Confirmed no such "carrier required"
   artifact appears anywhere in the real 92-key census (grepped for
   `carrier`/`profile mismatch` across all 98 fragment+vertex probe results:
   zero hits).
2. **Reproducing `FRONTIER-2026-08-13.md`'s historical blockers.** All 212
   corpus programs are now `status: "compatible"`
   (`backend_compatibility.json`'s own counts: `status_incompatible: 0`), so
   every blocker in that August doc is now resolved — re-probing 7 of its
   named blockers (`filter/edge:edge`, `filter/glyphMap:glyphMap`,
   `filter/grain:grain`, `classicNoisedeck/bitEffects:bitEffects`,
   `filter/scanlineError:scanlineError`) confirms this: each now reports
   "exact `<name>` profile carrier required" (i.e., its fix landed as exactly
   the kind of dict-keyed profile the doc's "Next levers" section
   anticipated) rather than the old raw construct error. `check_semantics.py
   --check` and `check_corpus.py --check` both pass on the checked-out tree
   independently of this harness, confirming the 212/167 baseline this
   census's "already admitted" comparisons rest on.

### 1.3 Per-program static facts

Independent of pipeline outcome, every source was also scanned with plain
regexes for: sampler-uniform count/types, declared `out` count/names
(matching both `out T x;` and `layout(location=N) out T x;`), `for`/`while`
presence, `struct` presence, `texelFetch(`, an `atlas`-named helper,
bitwise/XOR operators, `uint`/`uvecN` usage, `bvecN` *type* usage, `mat3`/`mat4`
usage, `switch`, `discard`, and the three vertex-only builtins. These are the
`vert`/`MRT`/`smp`/`loop`/`atlas`/`struct`/`bit` columns in §4's table and are
independent of whether the pipeline ever got far enough to see them itself.

---

## 2. Headline findings

### 2.1 45 of 92 are typed-pipeline-clean; the real blocker is orchestration, not the frontier

44 programs pass parse/semantic/validator/emitter with **zero** modification,
and one more (`render/pointsBillboardRender:depthKeys`) does too once a
pass-level `#define VIEW_MODE` — computed dynamically by the JS authority's
`definition.js` rather than listed as a static per-effect param default, so
this census's metadata extraction initially missed it — is supplied (any
concrete value works; see the program's `defines_note` in the JSON). That is
**45/92 (49%)** with no construct blocker at any stage this task could probe.

This matches `.nm-cpp-work/phase2-architecture.md`'s own family-level finding
independently: Family B/C's report states "**Zero hand-written C++ adapters
are needed** ... the complexity is 100% in orchestration/scheduling, not
per-pixel kernel logic" (§3.2.3), and this program-by-program census confirms
it empirically at the individual-kernel level, not just as a per-family
estimate. What these 45 actually need is the **iteration/loop-execution
scheduler primitive** that `phase2-architecture.md` §4.1 already identifies
as the single most cross-cutting missing piece in the C++ runtime
(`GraphExecutor::execute()` cannot run a pass list more than once per render
call, confirmed there by grepping `executor.cpp` for
`iterated|loop_role|particle|global_xyz|iteration|loop` — zero matches) —
this is **out of this task's scope** (typed pipeline only) but is the correct
next reference for these 45 programs' actual blocker.

### 2.2 MRT: the typed *generator* is nearly fine; the typed *emitter* has one narrow, silent bug

`.nm-cpp-work/phase2-architecture.md` §4.1(#3) states MRT support is
"genuinely new ground for the GLSL frontend parser too, not just the
executor." Direct measurement **refines this**: the parser and the
declaration/semantic layer already handle `layout(location=N) out vec4 x;`
correctly — `normalize()`'s regex-based output capture (which only matches
plain `out T name;`, not the `layout(...)`-qualified form) *does*
under-detect it, returning `['fragColor']` for every MRT program tested, but
this is silently papered over one layer up: `semantic.py`'s declaration pass
independently derives "is this an output" from `"out" in quals` (line ~165),
which survives the `layout(...)` prefix regardless. Verified directly:
`points/heightGrid:agent` and `points/lenia:agentField` (3-output, `outXYZ`/
`outVel`/`outRGBA`) and `synth3d/cell3d:precompute`/`synth3d/shape3d:precompute`
(2-output, `fragColor`/`geoOut`) all show `outputs_detected` with the full,
correct output list post-semantic-analysis.

The real, narrow gap is one function in the **emitter**:
`tools/glslcpp/emit_typed_cpp.py:5892-5893`

```python
if symbol.id in self.outputs:
    return "output"
```

*Every* symbol with `storage == "output"` — regardless of which of the N
declared outputs it is — resolves to the identical C++ identifier `output`,
because the emitted `pixel()` function signature has exactly one output
parameter (`glsl::Vec4& output`). Generating C++ for `points/heightGrid:agent`
and grepping the result confirms this concretely: the emitted body is

```cpp
void pixel(..., glsl::Vec4& output) noexcept {
  ...
  output = glsl::Vec4(/* outXYZ's expression */);
  output = glsl::Vec4(/* outVel's expression */);
  output = glsl::Vec4(/* outRGBA's expression */);
}
```

three sequential overwrites of the same variable — **only the last write
(`outRGBA`) survives**; `outXYZ` and `outVel`'s independently-computed values
are silently discarded. Neither `validate_capabilities()` nor
`render_typed_cpp()` raises for this — there is no arity check anywhere in
either function — so a naive "did it throw" census would misreport these 4
programs as fully compatible. **24 of the 92 programs declare more than one
output** (`declared_out_count > 1`, cross-checked byte-for-byte against the
JS authority's own `drawBuffers` pass metadata: zero mismatches); only 4
currently *expose* this bug in isolation because the other 20 are blocked
earlier by unrelated issues (loop proofs, XOR, sampler-parameters, etc.) that
would need fixing first to reach the emitter at all.

### 2.3 Vertex/points draw mode: zero support, uniformly, by construction

The 6 `.frag`+`.vert` pairs (`filter3d/flow3d:deposit`, `points/dla:depositGrid`,
`points/lenia:deposit`, `points/physarum:deposit`,
`render/pointsBillboardRender:deposit`, `render/pointsRender:deposit` — all
and only the programs the JS authority's own pass metadata marks
`drawMode: "points"` or `"billboards"`) are the *entire* vertex-shader
surface among the 92; there is no seventh case and no case with vertex
involvement but no separate `.vert` file. All 6 `.vert` files fail identically
in `analyze_program`'s body-semantic sub-stage with `E_UNKNOWN_SYMBOL` on
`gl_VertexID` and `gl_Position` (5 of 6 also reference `gl_PointSize`) —
confirmed directly (not inferred) by checking each exception's full
diagnostic text, not just its first line. This matches the pipeline's own
documented self-description, found verbatim in two places
(`tools/glslcpp/generate_typed_slice.py:5021`,
`tools/glslcpp/frontend/varying_uv_profile.py:53`): *"there is no vertex
stage and no interpolation anywhere in the CPU reference."* On the fragment
side, 5 of the 6 companion `.frag` files additionally fail with `unsupported
varying` (they consume a vertex-interpolated `in` value, e.g. `v_weight`/
`v_color`); the 6th (`points/lenia:deposit`) has a fragment body that happens
not to reference its varying and is otherwise clean — but the pass is still
`drawMode: "points"` and still has no vertex stage to run at all, so it is
equally blocked, just not by anything visible in the fragment kernel alone.

### 2.4 Everything else is a small, mostly-precedented set of construct gaps

See §3 for the ranked table. Two are worth flagging as *already
half-solved*: the scalar/vector XOR pattern (`(a >> b) ^ a) * k` — a
`hash_uint`-style PCG hash, present verbatim or near-verbatim in every
program that fails on it) is the **same shape** as the existing
`perlin_scalar_uint_xor_profile.py`/`scalar_uint_xor_profile.py`, already
admitted for 5 other corpus programs and explicitly flagged in
`FRONTIER-2026-08-13.md` as needing generalization to a dict-keyed profile —
this census's 7 new primary carriers (and up to 15 more masked behind other
blockers — see §3 note) are exactly that generalization's next customers.
Likewise, `sampler2D` passed as a function *parameter* (`vec4 bicubic(sampler2D
tex, ...)`) is the same shape as the existing
`focus_blur_borrowed_sampler_profile.py` ("borrowed sampler"), already solved
once for one corpus program.

---

## 3. Ranked blocker classes

Ranked by **primary-blocker program count** — the number of programs for
which this is literally the first thing that stops them, as directly
measured. Where a class is cross-cutting (more programs contain the
triggering construct than are currently blocked *by* it, because an earlier,
unrelated blocker gets there first), the "latent exposure" column gives the
larger true number from the regex facts in §1.3 — fixing the class alone
does not immediately unblock the latent count, since those programs still
need their earlier blocker resolved too.

| # | Programs (primary) | Latent exposure | Blocker class | Stage | Recommended capability |
|---:|---:|---:|---|---|---|
| 1 | **44** (includes `pointsBillboardRender:depthKeys`, whose only obstacle in this census was a probe-metadata gap, not a real construct — see §2.1) | 44 | *No typed-pipeline blocker at all* — needs the runtime iteration/loop-execution scheduler, not frontend work | n/a (out of typed-pipeline scope) | `phase2-architecture.md` §4.1 primitive #1 (step-scoped persistent resources + outer N-iteration loop driver) |
| 2 | 9 | ~28 programs contain a `for` loop; not all are unproven | `unsupported counted-for program proof` | validator/emitter | Widen the counted-for trip-count proof to cover uniform-derived/texture-size-derived bounds (same class `FRONTIER-2026-08-13.md` called "the single biggest lever" for the old 43; recurring here) |
| 3 | 7 | ~22 (any source containing `^`/`hash_uint`) | `unsupported binary operator ^` (scalar/uint XOR, PCG-style hash) | validator/emitter | Generalize `scalar_uint_xor_profile.py`/`perlin_scalar_uint_xor_profile.py` to a dict-keyed profile admitting these new carriers (mechanism already exists, per §2.4) |
| 4 | 6 (5 direct `unsupported varying` + 1 clean-but-still-blocked) | 6 (exactly; see §2.3) | No vertex/rasterization stage exists in the typed pipeline at all | semantic (`.vert`) / validator (`.frag`) | New pipeline stage: a vertex-shader kernel type (binds `gl_VertexID`→per-point index, computes `gl_Position`/`gl_PointSize`, produces varyings) plus per-vertex interpolation feeding the existing fragment kernel — this is new ground, not a widening of an existing mechanism |
| 5 | 4 | 24 (every MRT program; only 4 expose it today, see §2.2) | MRT output collapse — **silent**, not raised | emitter (passes; wrong) | One targeted fix: give `_Emitter` an output-symbol→physical-slot map instead of the single hardcoded `"output"` name at `emit_typed_cpp.py:5892-5893`, plus an N-output `pixel()` signature. (Declaration/semantic layers already work — §2.2.) *This alone does not unblock any of the 24 by itself; the runtime executor's separate `unsupported_mrt` refusal, already scoped in `phase2-architecture.md` §4.1(#3), also has to land.* |
| 6 | 4 | 4 | `unsupported sampler parameter` (`sampler2D` as a function parameter, e.g. bicubic/bilinear interpolation helpers) | validator/emitter | Generalize the existing `focus_blur_borrowed_sampler_profile.py` ("borrowed sampler") to these 4 new carriers |
| 7 | 3 | 3 (exactly; only `flock:agent`, `life:agent`, `pointsBillboardRender:spriteMeanTiles` use `%` this way among the 92) | `E_OPERATOR: % requires same integral operands` — precisely, `ivec2 % int` (vector-by-scalar broadcast), not literally int-vs-uint | semantic (body) | Admit GLSL's scalar-broadcast form of `%` (`vecN % scalar` in addition to `vecN % vecN`) — a real GLSL-spec-legal form the validator currently rejects |
| 8 | 3 | 3 (exactly; grepped `cross(` across all 92) | `cross()` builtin (3D vector cross product) is not implemented — confirmed via a minimal synthetic repro (`vec3 c = cross(a,b);` fails identically: `E_NO_OVERLOAD: no exact overload for cross`) | semantic (body) | Add `cross(vec3, vec3) -> vec3` to the builtin table — needed by all three volume-camera-basis kernels (`render3d`, `renderLit3d`, `flythrough3d:precompute`) |
| 9 | 2 | 2 | `unsupported typed type vec4[9]` — a fixed-size local array/table, same shape as the existing `FIXED_NINE_CAPABILITY` | validator/emitter | Register these 2 new carriers (`temporalAberration:temporalAberration`, `navierStokes:nsSmooth`) against the existing fixed-nine mechanism |
| 10 | 2 | ≥3 (`heightmap3d:precompute` needs both `any` and `lessThan`; `pointsBillboardRender:deposit` needs `lessThan` behind its varying blocker) | bvec relational-reduction builtins (`any`, `all`, `isnan`, `lessThan`, `greaterThan`, …) — none are in `APPROVED_CAPABILITIES` | semantic (body, `E_NO_OVERLOAD`) / validator | Add the bvec-relational builtin family; `points/attractor:agent`'s blocker is `any(isnan(newPos))` — two builtins from this family stacked |
| 11 | 2 | 2 | `unsupported counted-for safety charge` (a distinct, more conservative sub-case of the loop-bound proof; both `buddhabrot:agent`/`buddhabrot:zWrite`) | validator/emitter | Same family as #2, historically named in `FRONTIER-2026-08-13.md` for `gabor`/`julia`; likely lands together with #2 |
| 12 | 2 | 2 | `floatBitsToUint`/`uintBitsToFloat` (IEEE-754 bit-reinterpretation) not implemented | semantic (body) / validator | Add these two builtins — used by `points/dla:agent` and `points/physarum:agent`'s RNG seeding |
| 13 | 1 | 1 | `unsupported typed expression index` — numeric **vector component access by index** (`hsv[0] = ...`), as both rvalue and lvalue, distinct from `.xyzw` swizzle syntax | validator | Confirmed via minimal synthetic repro (`vec3 hsv; hsv[0] = hsv[0]+0.5;` fails identically). Admit `v[i]` for constant/loop-bound integer `i` on both sides of `=` |
| 14 | 1 | 1 | `unsupported global declaration` — a 55-entry `const PaletteEntry[]` struct-array literal table | validator | Same construct class the existing hand-written `filter/palette` C++ adapter already special-cases (`palette`/`historicPalette`/`fractal`/`julia` are all listed as adapter exceptions in `check_corpus.py` per `FRONTIER-2026-08-13.md`); `filter3d/palette3d` is very likely the same "hand-written adapter, not typed generator" precedent, not a typed-emitter task at all |
| 15 | 1 | 1 | `unsupported typed expression post` — postfix `count++` | validator | Admit postfix increment/decrement (needed by `synth3d/cellularAutomata3d:simulate`'s neighbor counter) |
| 16 | 1 | 1 | `acos()` builtin missing (not in `APPROVED_CAPABILITIES`, unlike `sin`/`cos`/`atan`) | semantic (body, `E_NO_OVERLOAD`) | Add `acos(float) -> float` — needed by `synth3d/fractal3d:precompute` |

Rows 1-16 sum to 44+9+7+6+4+4+3+3+2+2+2+2+1+1+1+1 = **92**, exactly, and match
`frontier-92.json`'s `blocker_class_ranking` (computed from the same
per-program `blocker_class` field, not retyped by hand) one-for-one. Note row
4's "6" is itself 5 programs whose *fragment* half also fails on `unsupported
varying` plus 1 (`points/lenia:deposit`) whose fragment half is independently
clean — both are the same root cause (no vertex stage exists at all) and are
merged in this row; the table in §4 shows them as two distinct
`blocker_class` strings for traceability.

---

## 4. Per-program table

`vert` = drawMode points/billboards with a separate `.vert` (Y/-). `MRT` =
declared output count (ground-truthed against the JS authority's own
`drawBuffers` pass metadata, §1.3 — zero mismatches across all 92). `smp` =
declared `sampler2D` uniform count. `loop` = `for`/`while`/`-` present
anywhere in the source (not necessarily on the path to the reported
blocker). `atlas` = uses the `ivec3`→`ivec2` "3D volume as a 2D atlas
texture" helper pattern with `texelFetch`. `struct` = declares a `struct`.
`bit/uint` = uses a bitwise/XOR operator and/or `uint`/`uvecN`.

Full detail (raw error text, exact source line inside the *normalized*
source, `outputs_detected`, sampler types, domain, etc.) is in
`frontier-92.json`, keyed by program key.

<details>
<summary>92 rows (click to expand)</summary>

| key | file | stage | first blocker (class) | vert | MRT | smp | loop | atlas | struct | bit/uint |
|---|---|---|---|---|---|---|---|---|---|---|
| `classicNoisedeck/noise3d:noise3d` | .glsl | validator | loop-bound proof | - | 1 | 0 | for | - | - | bit+u |
| `classicNoisedeck/shapes3d:shapes3d` | .glsl | validator | loop-bound proof | - | 1 | 1 | for | - | Y | bit+u |
| `filter/convolutionFeedback:cfBlend` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `filter/convolutionFeedback:cfBlur` | .glsl | validator | loop-bound proof | - | 1 | 1 | for | - | - | - |
| `filter/convolutionFeedback:cfSharpen` | .glsl | validator | loop-bound proof | - | 1 | 1 | for | - | - | - |
| `filter/feedback:copy` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `filter/feedback:feedback` | .glsl | validator | vector component access by integer index | - | 1 | 2 | - | - | - | - |
| `filter/motionBlur:copy` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `filter/motionBlur:motionBlur` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `filter/temporalAberration:delayShift` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `filter/temporalAberration:temporalAberration` | .glsl | validator | fixed-size local array/table admission | - | 1 | 9 | - | - | - | - |
| `filter3d/flow3d:agent` | .glsl | validator | scalar/uint XOR admission | - | 3 | 4 | - | Y | - | bit+u |
| `filter3d/flow3d:blend` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `filter3d/flow3d:copy` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `filter3d/flow3d:deposit` | .frag+.vert | validator | vertex/rasterization stage | Y | 1 | 0 | - | - | - | - |
| `filter3d/flow3d:diffuse` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `filter3d/palette3d:palette3d` | .glsl | validator | const struct-array global table | - | 1 | 1 | - | - | Y | - |
| `points/attractor:agent` | .glsl | semantic:body | bvec relational-reduction builtins | - | 3 | 3 | - | - | - | bit+u |
| `points/attractor:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/buddhabrot:agent` | .glsl | validator | loop-bound proof | - | 3 | 3 | for | - | - | bit+u |
| `points/buddhabrot:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/buddhabrot:zWrite` | .glsl | validator | loop-bound proof | - | 1 | 2 | for | - | - | - |
| `points/dla:agent` | .glsl | semantic:body | float/uint bit-reinterpretation builtins | - | 3 | 5 | - | - | - | bit+u |
| `points/dla:copyGrid` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/dla:depositGrid` | .frag+.vert | validator | vertex/rasterization stage | Y | 1 | 0 | - | - | - | - |
| `points/dla:initGrid` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/dla:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `points/flock:agent` | .glsl | semantic:body | integer modulo operand-shape | - | 3 | 3 | for | - | - | bit+u |
| `points/flock:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/flow:agent` | .glsl | validator | scalar/uint XOR admission | - | 3 | 4 | - | - | - | bit+u |
| `points/flow:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/heightGrid:agent` | .glsl | emitter_pass(MRT-silent) | MRT fragment outputs | - | 3 | 4 | - | - | - | - |
| `points/heightGrid:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/hydraulic:agent` | .glsl | validator | scalar/uint XOR admission | - | 3 | 4 | - | - | - | bit+u |
| `points/hydraulic:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/lenia:agentField` | .glsl | emitter_pass(MRT-silent) | MRT fragment outputs | - | 3 | 4 | - | - | - | - |
| `points/lenia:clear` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 0 | - | - | - | - |
| `points/lenia:convolve` | .glsl | validator | loop-bound proof | - | 1 | 1 | for | - | - | - |
| `points/lenia:deposit` | .frag+.vert | emitter_pass(clean) | no blocker in the fragment kernel, but drawMode:points has no vertex stage | Y | 1 | 0 | - | - | - | - |
| `points/lenia:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/life:agent` | .glsl | semantic:body | integer modulo operand-shape | - | 4 | 6 | for | - | - | bit+u |
| `points/life:matrix` | .glsl | validator | scalar/uint XOR admission | - | 1 | 0 | - | - | - | bit+u |
| `points/life:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/physarum:agent` | .glsl | validator | float/uint bit-reinterpretation builtins | - | 3 | 5 | - | - | - | bit+u |
| `points/physarum:deposit` | .frag+.vert | validator | vertex/rasterization stage | Y | 1 | 0 | - | - | - | - |
| `points/physarum:diffuse` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/physarum:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `points/physical:agent` | .glsl | validator | scalar/uint XOR admission | - | 3 | 4 | for | - | - | bit+u |
| `points/physical:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `render/loopBegin:loopBegin` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `render/loopEnd:copy` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `render/pointsBillboardRender:blend` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `render/pointsBillboardRender:clearDefocus` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 0 | - | - | - | - |
| `render/pointsBillboardRender:copy` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `render/pointsBillboardRender:deposit` | .frag+.vert | validator | vertex/rasterization stage | Y | 1 | 2 | for | - | - | - |
| `render/pointsBillboardRender:depthKeys` | .glsl | emitter_pass(clean)* | no frontend/typed-pipeline blocker (*pass-level VIEW_MODE define needed — see §2.1) | - | 1 | 1 | - | - | - | - |
| `render/pointsBillboardRender:depthMerge` | .glsl | validator | loop-bound proof | - | 1 | 1 | for | - | - | - |
| `render/pointsBillboardRender:diffuse` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `render/pointsBillboardRender:spriteMean` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | for | - | - | - |
| `render/pointsBillboardRender:spriteMeanTiles` | .glsl | semantic:body | integer modulo operand-shape | - | 1 | 1 | for | - | - | - |
| `render/pointsEmit:init` | .glsl | validator | scalar/uint XOR admission | - | 3 | 4 | - | - | - | bit+u |
| `render/pointsEmit:passthrough` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `render/pointsRender:blend` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `render/pointsRender:copy` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `render/pointsRender:deposit` | .frag+.vert | validator | vertex/rasterization stage | Y | 1 | 0 | - | - | - | - |
| `render/pointsRender:diffuse` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `render/render3d:render3d` | .glsl | semantic:body | cross() builtin missing | - | 2 | 1 | for | Y | Y | bit |
| `render/renderCubemap3d:renderCubemap3d` | .glsl | validator | loop-bound proof | - | 2 | 1 | for | Y | Y | bit |
| `render/renderCubemapSurface:renderCubemapSurface` | .glsl | validator | loop-bound proof | - | 2 | 1 | for | Y | - | bit |
| `render/renderLandscape3d:landscape` | .glsl | validator | loop-bound proof | - | 2 | 2 | for | - | - | - |
| `render/renderLit3d:renderLit3d` | .glsl | semantic:body | cross() builtin missing | - | 2 | 1 | for | Y | Y | bit |
| `synth/cellularAutomata:ca` | .glsl | validator | sampler2D passed as a function parameter | - | 1 | 2 | - | - | - | - |
| `synth/cellularAutomata:caFb` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | for | - | - | bit |
| `synth/mnca:mnca` | .glsl | validator | sampler2D passed as a function parameter | - | 1 | 2 | - | - | - | - |
| `synth/mnca:mncaFb` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | for | - | - | - |
| `synth/navierStokes:ns` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `synth/navierStokes:nsAdvect` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `synth/navierStokes:nsDivergence` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `synth/navierStokes:nsGradient` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | - | - | - |
| `synth/navierStokes:nsPressure` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 1 | - | - | - | - |
| `synth/navierStokes:nsSmooth` | .glsl | validator | fixed-size local array/table admission | - | 1 | 1 | for | - | - | - |
| `synth/navierStokes:nsSplat` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | for | - | - | - |
| `synth/reactionDiffusion:rd` | .glsl | validator | sampler2D passed as a function parameter | - | 1 | 2 | - | - | - | - |
| `synth/reactionDiffusion:rdFb` | .glsl | validator | sampler2D passed as a function parameter | - | 1 | 2 | - | - | - | - |
| `synth3d/cell3d:precompute` | .glsl | emitter_pass(MRT-silent) | MRT fragment outputs | - | 2 | 0 | for | - | - | bit+u |
| `synth3d/cellularAutomata3d:simulate` | .glsl | validator | postfix increment/decrement operator | - | 1 | 2 | for | Y | - | - |
| `synth3d/flythrough3d:precompute` | .glsl | semantic:body | cross() builtin missing | - | 2 | 0 | for | - | Y | bit |
| `synth3d/fractal3d:precompute` | .glsl | semantic:body | acos() builtin missing | - | 2 | 0 | for | - | - | - |
| `synth3d/heightmap3d:precompute` | .glsl | validator | bvec relational-reduction builtins | - | 2 | 2 | - | - | - | - |
| `synth3d/noise3d:precompute` | .glsl | validator | scalar/uint XOR admission | - | 2 | 0 | for | - | - | bit+u |
| `synth3d/reactionDiffusion3d:simulate` | .glsl | emitter_pass(clean) | no frontend/typed-pipeline blocker | - | 1 | 2 | - | Y | - | - |
| `synth3d/shape3d:precompute` | .glsl | emitter_pass(MRT-silent) | MRT fragment outputs | - | 2 | 0 | - | - | - | bit |

</details>

---

## 5. Recommended general capabilities, ordered by programs unblocked

This orders the **typed-pipeline-side** work only (in scope for this task).
The single largest lever (44-45 programs) is a **runtime executor**
capability, already fully scoped by `phase2-architecture.md` §4.1 — listed
first for completeness since it dominates the count, but it is not frontend
work and this task did not re-derive it.

1. **Runtime iteration/loop-execution scheduler** (44-45 programs; not
   typed-pipeline work — see §2.1 and `phase2-architecture.md` §4.1 primitive #1).
2. **Loop-bound proof widening** (9 direct + 2 "safety charge" variant = 11
   programs; recurring lever, same shape as the old 43-program frontier's
   "single biggest lever").
3. **Scalar/uint XOR admission, generalized** (7 direct; up to 22 latent) —
   mechanism exists, needs new carriers registered.
4. **Vertex/rasterization pipeline stage** (6 programs total: 5 direct +
   1 masked) — new mechanism, not a widening; also the prerequisite for the
   6 corresponding scatter adapters `phase2-architecture.md` §4.1(#5) already
   lists.
5. **MRT emitter fix** (unblocks nothing alone — 24 programs are MRT, but
   all also need the runtime executor's separate MRT primitive,
   `phase2-architecture.md` §4.1(#3) — listed because it is a real, now
   located, silent-correctness bug independent of that runtime work: 4
   programs currently report false "compatible" status).
6. **`sampler2D`-as-parameter admission, generalized** (4 programs) —
   mechanism exists (`focus_blur_borrowed_sampler_profile.py`), needs new
   carriers.
7. **`vecN % scalar` broadcast modulo** (3 programs) — real GLSL-legal form
   currently rejected.
8. **`cross()` builtin** (3 programs, all volume-camera-basis kernels).
9. **Fixed-size local array/table, generalized** (2 programs) — mechanism
   exists (`FIXED_NINE_CAPABILITY`), needs new carriers.
10. **bvec relational-reduction builtins** (`any`/`all`/`isnan`/`lessThan`/
    `greaterThan`) (2 direct primary, ≥3 latent).
11. **`floatBitsToUint`/`uintBitsToFloat`** (2 programs).
12. **Vector component access by index (`v[i]`, rvalue+lvalue)** (1 program,
    confirmed via synthetic repro).
13. **`acos()` builtin** (1 program).
14. **Postfix increment/decrement** (1 program).
15. **Const struct-array global table** (1 program) — likely belongs to the
    hand-written-adapter track (`filter/palette` precedent), not the typed
    generator, pending confirmation.

---

## 6. What is verified vs. not

**Verified directly** (code read + a passing/failing probe against the live
modules, several with an additional minimal synthetic repro isolating the
exact construct): the 92-key set itself (§0, cross-checked two ways against
`backend_compatibility.json`); the MRT declaration-vs-emitter split (§2.2,
including reading the exact emitter source line and generating real C++ for
two MRT programs); the vertex-builtin blocker for all 6 `.vert` files (§2.3,
full diagnostic text inspected, not just first line); `cross()`,
`v[i]`-indexing, and the `vecN % scalar` modulo shape (§2.4/§3, each with a
standalone synthetic-source repro against `parse_program`/`analyze_program`/
`validate_capabilities`); the `sampler2D`-parameter and XOR/`hash_uint`
pattern-matches to existing named profiles (source-read, not just
message-text-matched); the `VIEW_MODE` pass-level-define probe artifact for
`pointsBillboardRender:depthKeys` (§2.1, re-probed with a concrete value from
both possible states, both pass identically).

**Not independently re-verified, taken from `phase2-architecture.md` on that
document's own authority**: the runtime executor findings this report
references for context (`executor.cpp`'s `unsupported_mrt` refusal site line
numbers, the `iterated|loop_role|particle` grep-zero claim, the family-level
effect/pass counts) — these are outside this task's stated scope (the typed
pipeline) and were only spot-checked once each (§2.1's grep, §2.2's
`unsupported_mrt` grep) for internal consistency, not re-derived from
scratch.

**Explicitly flagged as uncertain in the table above**: `filter3d/palette3d`'s
likely hand-written-adapter fate (inferred by construct-class analogy to
`filter/palette`, not confirmed against this specific effect's own
registration); the exact source line GLSL-side attribution for a few
messages where the validator's diagnostic span pointed at an enclosing
statement rather than the literal failing sub-expression (noted per-row in
`frontier-92.json` via `first_blocker_raw`, which preserves the pipeline's
own reported line:col verbatim — this report's prose additionally pins the
real *construct* by locating it in the post-`normalize()` source
independently, since raw-source line numbers do not equal normalized-source
line numbers whenever comments or `#version`/preprocessor lines are
stripped).

Full per-program data — raw error strings, `outputs_detected`,
`normalize_outputs_ground_truth_mismatch`, `defines_applied`/`defines_note`,
sampler types, domain, etc. — is in `<work>/frontier-92.json`.
