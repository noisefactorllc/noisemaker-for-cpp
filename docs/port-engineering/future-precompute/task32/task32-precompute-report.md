# Task 32 precompute report: "generalized const-global admission + round" for fxaa/grain/normalMap/snow

Read-only precompute. Repo state probed: `noisemaker-for-cpp` working tree,
corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`, live
`tools/glslcpp/typed_slice.json` = 131 typed programs (hash
`ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2`, verified
against the given hash — see `probe_projected_state.py`). Nothing was
implemented; nothing was written under `noisemaker-for-cpp` or
`noisemaker-for-cpu`. All monkeypatches are function-object substitutions
restored in `finally`, with identity+source-hash snapshots proving
restoration (`gate-chain-output.json`: every `stage_N_restored` is `true`).
No `git` command was run. No cmake build or Python test-suite run was
triggered; one ad hoc standalone `c++` translation unit was compiled and run
entirely under `/tmp`, `#include`-ing two real repo files read-only
(`include/noisemaker/numeric.hpp`, `src/numeric.cpp`).

## Headline answer

**"Generalized const-global admission + `round`" is sufficient for exactly
one of the four candidates: `filter/fxaa:fxaa`.** It is insufficient for the
other three, each for a distinct, evidence-backed reason:

| Key | Clears validator+emitter under const-global+round? | Reason if not | Reachability of its round() site | Selectable as a full-render target? |
|---|---|---|---|---|
| `filter/fxaa:fxaa` | **yes** | — | live/reachable (`as_u32`, called from `main`) | yes, mechanically — but round's specific negative-half hazard is **not** full-render discriminable (see below) |
| `filter/grain:grain` | no | needs a **third** capability: `uvec3 >> uvec3` (component-wise right shift by a vector; only `uvecN >> uint` is approved today) | live/reachable | no (blocked) |
| `filter/normalMap:normalMap` | no | needs **const array-of-vector global admission** (`ivec2[9]`), a materially larger scope than "any const scalar/vector/matrix" — array types are rejected by a separate, earlier type-approval gate | live/reachable | no (blocked) |
| `filter/snow:snow` | **yes, mechanically** | — (validator+emitter both pass) | **unreachable** — `as_u32` is defined but never called from `main` at this program's (empty) define map; it is dead code | **no — disqualified by the Task-31 reachability filter**, exactly like Caustic |

Evidence: `gate-chain-output.json` (stage-by-stage validator/emitter results),
`reachability-output.json` (call graph from `main`).

## Task 1 — full gate chain per candidate

Method: `probe_gate_chain.py`, following `future-precompute/
analyze_candidates.py`'s pattern, extended with a second monkeypatch layer.
Patch A reproduces `roadmap/probe_globals_second_order.py`'s exact text
substitutions (drop the float-only restriction in
`generate_typed_slice.validate_capabilities` and
`emit_typed_cpp._Emitter._validate_source_globals`; teach the const-global
initializer walker to recurse into `construct` expressions). Patch B is new
to this task: it deletes the `round`-specific identity gate
(`generate_typed_slice.py:2057-2059`, `emit_typed_cpp.py:1387-1389`) that
today admits `round()` **only** for the single object-identity-authenticated
call site inside `filter/pixelSort:gatherSorted` (`GATHER_SORTED_KEY`,
`authorized_round`, which is `None` for every other program — confirmed by
reading `generate_typed_slice.py:1401,1600-1604`), and instead lets `round`
fall through to the ordinary `elif value.callee not in _BUILTINS: raise`
check, with `"round"` added to `gen.APPROVED_CAPABILITIES` / `gen._BUILTINS`
/ `emit._BUILTIN_NAMES` by name — the same mechanism
`analyze_candidates.py` already uses for e.g. `reflect`/`tanh`. **This is
explicitly a probe of "what's next if round is generalized," not a real
capability** — every other special-cased builtin in this codebase (`tanh`,
`floatBitsToUint`, `all`/`lessThanEqual`) is gated the same way (single
authenticated-node identity, never entering `_BUILTINS`), so a real `round`
fix would need its own authenticated profile per program, following that
precedent, not a name-based allowlist entry.

Chain, per key (full detail in `gate-chain-output.json`):

- **`filter/fxaa:fxaa`**: unpatched → `unsupported global declaration`
  (`9:1`, `LUMA_WEIGHTS`/`CHANNEL_COUNT`/`EPSILON` globals). Patch A only →
  `unsupported builtin round` (`22:21`, inside `as_u32`). Patch A+B →
  **validator pass, emitter pass** (11746 bytes of emitted C++,
  sha256 `22e95e4e13333fb4517ffcba28cfbb801ce8cc9b41111a3961e8d2afe6417c6d`).
- **`filter/grain:grain`**: unpatched → `unsupported global declaration`
  (`12:1`). Patch A only → `unsupported builtin round` (`31:21`, inside
  `as_u32`). Patch A+B → `unsupported binary operator >>` (`43:14`, inside
  `pcg3d`: `v = v ^ (v >> uvec3(16u));`). Root cause: `generate_typed_slice.py`
  admits `>>` only for `uvecN >> uint` (`left_type in {uvec2,uvec3,uvec4} and
  right_type == "uint"`); grain's shift is `uvec3 >> uvec3` (`uvec3(16u)` is
  a scalar-broadcast **constructor**, type `uvec3`, not `uint`) — the same
  widening `^` already got (`uvecN ^ uvecN`) but `>>` has not. **Not
  sufficient — needs a third capability.**
- **`filter/normalMap:normalMap`**: unpatched → `unsupported global
  declaration` (`4:1`). Patch A only → validator: `unsupported typed type
  ivec2[9]` (`15:1`, the `const ivec2 SOBEL_OFFSETS[9] = ivec2[](...)`
  global); emitter (different traversal order): `unsupported builtin round`
  (`34:21`). Patch A+B → validator still `unsupported typed type ivec2[9]`;
  emitter now also surfaces the same array-type rejection. Root cause: array
  types are rejected by a **separate, earlier** type-approval gate
  (`reject_type` against `APPROVED_TYPES`, which has no array entry) that
  Patch A's initializer-shape relaxation does not touch — this is a
  genuinely different, larger-scope capability (const array-of-vector/float
  global tables; `normalMap` has three: `SOBEL_OFFSETS[9]:ivec2[9]`,
  `SOBEL_X_KERNEL[9]:float[9]`, `SOBEL_Y_KERNEL[9]:float[9]`) than "any const
  scalar/vector/matrix," which the roadmap's own second-order table (§2.3)
  under-reported by quoting only the emitter's message. **Not sufficient.**
  (Correction to the roadmap: its §2.3 summary table lists normalMap only
  under "unsupported builtin round," which is the *emitter's* first blocker;
  the *validator's* first blocker is the array-type rejection, a materially
  bigger ask. The roadmap's own raw JSON, `globals_second_order_output.json`,
  already contains this — it just wasn't surfaced in the prose summary.)
- **`filter/snow:snow`**: unpatched → `unsupported global declaration`
  (`7:1`). Patch A only → `unsupported builtin round` (`26:21`, inside
  `as_u32`). Patch A+B → **validator pass, emitter pass** (10174 bytes,
  sha256 `74f95f6e954b7e03f1e5a2fb60834296a928b8fa8a52a77c66095914ba0c4a53`).
  Mechanically clears — but see reachability below.

## Task 2 — global-declaration distribution table (all 30 keys)

Method: `probe_global_distribution.py`. Re-derives the roadmap's §2.2
classification independently (walks `typed.declarations` via the real
frontend, same predicate as `generate_typed_slice.py:1926`) and adds
initializer-shape classification, which the roadmap's table didn't carry.
Bucket counts match the roadmap exactly (cross-check, not blind trust):

| Storage / type bucket | Count | Example keys |
|---|---:|---|
| const vector | 9 | edge, grade:\*(5), scanlineError, emboss |
| const matrix | 7 | cellNoise, colorLab, moodscape, shapeMixer, shapes, adjust, colorspace |
| const non-float scalar (int) | 5 | bitEffects, glyphMap, historicPalette, palette, texture |
| const non-float scalar (uint) | 4 | fxaa, grain, normalMap, snow |
| const array | 2 | osd, spookyTicker |
| non-const global (mutable module state) | 3 | cellRefract, kaleido, synth/shape |
| **Total** | **30** | |

Initializer shape of the *first failing declaration* (per today's exact
rule): `literal` × 9, `constructor` × 18, `none` × 3 (the 3 non-const-global
keys, which declare without an initializer). No first-failing declaration
uses `swizzle`/`arithmetic expression` shapes directly — those only appear
deeper in the same programs' later globals (see below), which is why the
roadmap's second-order probe (testing generalized admission, not just
classification) hit them.

**bitEffects and scanlineError resolved** (both previously inconclusive in
the roadmap's second-order probe):

- `classicNoisedeck/bitEffects:bitEffects`: first failing declaration is
  `BIT_COUNT` (`const int`, literal `8`, span `129:1` in the *normalized*
  source — preprocessor-expanded, so line numbers differ from the raw
  corpus file). It admits cleanly under Patch A. The **next** global,
  `mask` (`const int mask = (1 << BIT_COUNT) - 1;`, span `130:1`), has a
  `binary` initializer using `<<` (left shift) — not one of the four
  operators (`+ - * /`) the const-global initializer walker admits, even
  under Patch A's generalization. Confirmed by direct probe:
  `classicNoisedeck/bitEffects:bitEffects:130:19: unsupported global
  initializer expression binary`. Real requirement: extend the initializer
  walker to admit `<<` (and likely the rest of the bitwise/shift family) —
  not covered by "any const scalar/vector/matrix," a fourth distinct
  extension beyond what Patch A tests.
- `filter/scanlineError:scanlineError`: `TAU` (`const float`, literal) is
  already admitted today. First failing declaration is `BASE_SEED_LINE`
  (`const vec3 = vec3(37.0, 91.0, 53.0)`, span `197:1`) — a plain
  `constructor`, admits cleanly under Patch A. The **next** global,
  `TIME_SEED_LINE = vec3(BASE_SEED_LINE.x + 97.0, BASE_SEED_LINE.y + 59.0,
  BASE_SEED_LINE.z + 131.0)` (span `199:5`), has each constructor argument
  as a `binary +` whose left operand is `BASE_SEED_LINE.x` — a **swizzle**
  (component-select) of an earlier admitted const global, not a plain `id`
  reference. The walker only recognizes direct `id` dependencies. Confirmed:
  `filter/scanlineError:scanlineError:199:5: unsupported global initializer
  expression swizzle`. Real requirement: teach the initializer walker to
  admit swizzles of earlier-admitted global dependencies — this is exactly
  the "swizzle" initializer shape the task asked about, now confirmed with
  a concrete example.

Both are genuinely resolved, not artifacts of the probe's own gaps: the
roadmap was right to flag them inconclusive (its patch didn't handle `<<` or
swizzle-of-dependency), and both turn out to need real additional scope
beyond simple type-restriction relaxation.

## Task 3 — reachability and discriminability

### Reachability (method: `probe_reachability.py`, call graph from `main`
following `call`-node `signature_id`, same technique as
`analyze_candidates.py` / `task-31-target-reselection.md`)

| Key | round() owner function | Reachable from main? |
|---|---|---|
| fxaa | `as_u32` (called via `max(as_u32(resolution.x), 1u)` etc.) | **yes** |
| fxaa | `sanitized_channelCount` (defined, never called — `main` hardcodes `channelCount = 4u`) | no (dead, but irrelevant since fxaa's live round site is `as_u32`) |
| grain | `as_u32` | **yes** |
| normalMap | `as_u32` (called directly and via `sanitize_channelCount`) | **yes** |
| snow | `as_u32` | **no — `as_u32` is defined but never called anywhere in `snow.glsl`'s reachable call graph** |

Snow's disqualification is definitive, not a heuristic: `as_u32`'s
`signature_id` never appears as a `call` target from any function reachable
from `main` (confirmed both by call-graph BFS and independently by grep — no
call site of `as_u32(` exists anywhere in `snow.glsl`). This is structurally
identical to what disqualified `classicNoisedeck/caustic:caustic` in Task 31
(`task-31-target-reselection.md`): a closure that type-checks and emits but
is dead code cannot be validated by full-render parity, because mutating it
never changes rendered output. **Snow must not be selected as a full-render
target on the strength of this gate combination**, even though it "passes."

### Discriminability (method: `probe_round_semantics.py`, real C++ compile
of `noisemaker::glsl_round` against `std::round`)

The C++ runtime's `noisemaker::glsl_round` is **already correct**:
`glsl_round(x) == floor(x + 0.5)` exactly (round-half-up), which is
`round()`'s actual GLSL semantics — bit-identical to `std::round` (round-
half-away-from-zero) for every non-negative input, and diverging **only** at
negative half-integers (measured sweep: 4/20 divergences, all at
`x ∈ {-3.5,-2.5,-1.5,-0.5}`; 0/20 divergences for `x ≥ 0`, including at
`x = -0.4999999`/`-0.5000001` boundary values). Example:
`glsl_round(-0.5) = 0.0`, `std::round(-0.5) = -1.0`.

In **all four** candidates, every `round()` call site has the identical
shape: `uint(max(round(value), 0.0))` inside `as_u32`, called only with a
resolution/size/channel-count uniform component (`resolution.x`, `size.z`,
`res.y`, etc.) — a render-target dimension, architecturally non-negative.
Independently confirmed against the `noisemaker-for-cpu` DSL/parity harness
(`parity/goldens/defaults/filter__fxaa.graph.json`): `resolution`,
`tileOffset`, and `fullResolution` are not user-settable DSL parameters —
they're injected by the renderer from the actual render-target pixel
dimensions, which cannot be negative.

**Plain statement per the task's own framing**: since `glsl_round` and
`std::round` are numerically identical for every non-negative operand, and
these programs never feed `round()` anything else, **full-render parity
cannot discriminate a wrong implementation that used `std::round` instead of
`glsl_round`** for fxaa (or for grain/normalMap if their other blockers were
separately cleared). This hazard is real (the codebase already avoids it
correctly, which is why it's easy to miss) but is not visible to
render-based testing here; direct unit rows exercising `round()` on a
negative operand would be required to actually test it, exactly as Curl's
`mod`-overload hazard needed `direct_mod_rows` in Task 31.

## Task 4 — does `round` already exist in the C++ runtime?

**Yes, with the correct (non-`std::round`) semantics.** Full-tree grep
(`grep -rniE 'round' include/ src/`, both camelCase and snake_case, whole
tree, not just two files — per the `float_bits_to_uint` lesson):

- `include/noisemaker/numeric.hpp:10` / `src/numeric.cpp:17`:
  `double glsl_round(double value) noexcept { return std::floor(value +
  0.5); }`
- `include/noisemaker/glsl_runtime.hpp:18` / `src/glsl_runtime.cpp:20`:
  `double round(double x) noexcept { return noisemaker::glsl_round(x); }` —
  in namespace `noisemaker::glsl`, i.e. callable as `glsl::round(...)`,
  exactly the spelling the emitter's generic builtin path
  (`glsl::{_BUILTIN_NAMES[value.callee]}(...)`) would produce.
- One existing call site: `src/typed_generated/typed_slice.cpp:5738`
  (`glsl::detail::float_to_int32(glsl::round(...))`) — the already-shipped
  `GATHER_SORTED_KEY` profile.
- No other spelling exists anywhere (`roundToInt`, `round_half`,
  `round_away`, etc. — none found).

**Nothing needs to be added to the numeric runtime.** What's missing is
entirely on the generator/emitter admission side (per-program authenticated
profiles, matching this codebase's demonstrated pattern), not the C++
implementation.

## Task 5 — projected post-task state ("if all four land")

Explicitly the hypothetical the task requested. Per the evidence above, only
`fxaa` actually clears the gate chain with a live/reachable, (mechanically)
render-testable site under this exact capability combination; `grain` and
`normalMap` need additional capabilities the hypothesis doesn't cover, and
`snow`'s round closure is dead code. The counts/hashes below are still
computed exactly as asked, method in `probe_projected_state.py`.

| | typed | public (typed + `filter/invert:inv` + `synth/solid:solid`) | unported | corpus |
|---|---:|---:|---:|---:|
| current | 131 | 133 | 79 | 212 |
| projected (+4) | 135 | 137 | 75 | 212 |

Projected typed-list sha256 (newline-terminated, sorted):
`182be487fa009e3bd4cee6b7847674373b23aeffd1097f24c25bf64e4672dac5`
(current, verified against the given hash: `ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2`).

Ordinals and neighbours in the projected 135-entry sorted list:

| Key | Ordinal | Namespace | Before | After |
|---|---:|---|---|---|
| `filter/fxaa:fxaa` | 28 | `typed_28` | `filter/flipMirror:flipMirror` | `filter/glowingEdge:glowingEdge` |
| `filter/grain:grain` | 30 | `typed_30` | `filter/glowingEdge:glowingEdge` | `filter/hatch:hatch` |
| `filter/normalMap:normalMap` | 41 | `typed_41` | `filter/mosaicTiles:mosaicTiles` | `filter/normalize:apply` |
| `filter/snow:snow` | 84 | `typed_84` | `filter/smoothstep:smoothstep` | `filter/sobel:sobel` |

103 of the 131 existing typed programs' ordinals shift (every key sorting
alphabetically after `filter/fxaa:fxaa`, i.e. ordinal ≥ 28 today); full list
in `projected-state-output.json.existing_keys_with_shifted_ordinal`.

## Task 6 — ordinal blast radius

Method: `probe_ordinal_blast_radius.py`, same approach as
`task-31-ordinal-blast-radius.md` — locate every hardcoded `typed_NN` /
`typed.index(...)` site in `tests/test_typed_generator.py`
(13 occurrences across 8 distinct governing tests), determine each site's
exact filtering view by reading the test source (none of them exclude "the
N most recently added programs" — they always filter by a fixed, named key
list, so future additions are never automatically excluded), and recompute
each key's ordinal in that view today vs. after the 4 hypothetical
insertions (using the real `generate_typed_slice.load_slice()`, not pytest).

| Line(s) | Test | Key | Hardcoded | Live today | Already stale? | Projected (+4) | Shifts? |
|---|---|---|---:|---:|---|---:|---|
| 1362 | task24 resource contract (reads on-disk generated .cpp directly) | gatherSorted | 53 | 53 | no | 56 | **yes (+3)** |
| 7607 | task21 degauss exclusions | degauss | 22 | 22 | no | 22 | no |
| 9041 | lens/prismatic literal-vec3 census (5-key view) | lensDistortion | 2 | 2 | no | 2 | no |
| 9042 | same | prismaticAberration | 59 | 59 | no | 62 | **yes (+3)** |
| 9043 | same, "current" | gatherSorted | 52 | 52 | no | 55 | **yes (+3)** |
| 9045 | same, "prior" (historical, minus Lens+Prismatic too) | gatherSorted | 51 | 51 | no | 54 | **yes (+3)** |
| 11155, 11299 | task26 smooth carrier census (3-key view) | smoothEdge | 77 | 77 | no | 80 | **yes (+3)** |
| 12255 | task27 single-program delta (3-key view) | PERLIN_KEY | 123 | **124** | **yes** (curl, `synth/curl` sorts before `synth/perlin`) | 128 | **yes (+4)** |
| 13976, 14054 | task29 schema/cpp-tables (full live spec) | FOCUS_BLUR_KEY | 111 | 111 | no | 115 | **yes (+4)** |
| 14649, 14672 | task30 history coexistence (full live spec) | EXTRUDE_KEY | 25 | 25 | no | 25 | no |

**13 sites total shift or are already stale; 6 of the 8 governing tests have
at least one line that would need updating.** Shift deltas follow directly
from alphabetic sort: all 4 candidates are `filter/*`, so they only push
ordinals for keys sorting after `filter/fxaa` (28) among the referenced
keys — `filter/degauss`, `filter/extrude`, and
`classicNoisedeck/lensDistortion` sort earlier and are unaffected.

**Independent, pre-existing observation (not caused by this task, not
fixed by this task — read-only mandate):** the overall count/hash tuples in
several of these same tests (e.g. `(130, 132, 80, 212)` at lines 13967 and
14640, `(125, 127, 85, 212)` at line 8993, `(127, 129, 83, 212)` at lines
7513 and 11152) are already short by exactly one program relative to the
live tree — `synth/curl:curl` (Task 31's actual landed addition) is present
in `typed_slice.json` (confirmed: 131 live entries) but these hardcoded
tuples were seemingly not updated when it landed, because these tests filter
by an explicit fixed key-name list rather than "everything added after task
N." This is visible in `ordinal-blast-radius-output.json`'s
`count_tuple_context_per_view` (live 131/128/126 across the three views vs.
what these tests hardcode). It does not affect most of the *ordinal* values
above (curl, in `synth/*`, sorts after nearly everything referenced here —
the one exception is `synth/perlin:perlin`, which is why that single site
shows `already_stale_vs_hardcoded: true`). Flagged as observed context for
whoever picks this up next; nothing was changed.

## Files in this directory

- `probe_gate_chain.py` / `gate-chain-output.json` — Task 1.
- `probe_reachability.py` / `reachability-output.json` — Task 3 (reachability half).
- `probe_round_semantics.py` / `round-semantics-output.json` / `cpp-probe/round_semantics_probe.cpp` — Task 3 (discriminability half) + Task 4.
- `probe_global_distribution.py` / `global-distribution-output.json` — Task 2.
- `probe_projected_state.py` / `projected-state-output.json` — Task 5.
- `probe_ordinal_blast_radius.py` / `ordinal-blast-radius-output.json` — Task 6.
- Every `.py`/`.json`/`.cpp` above has a `.sha256` sidecar.
