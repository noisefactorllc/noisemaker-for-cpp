# Full-Chain Frontier Map — noisemaker-for-cpp typed GLSL→C++ slice

Read-only analysis. Revision probed: `a024dc3a960cc44af454abc7aebce50456c194e6`.
State at probe time: **131 typed / 133 public / 79 unported** (verified —
`tools/glslcpp/typed_slice.json` has exactly 131 `program_key` entries;
`tests/test_typed_generator.py:11154` etc. compute `public = typed ∪
{filter/invert:inv, synth/solid:solid}`, confirmed absent from
`typed_slice.json` by grep; `212 − 133 = 79`).

**This corrects the same mistake twice over.** §10 of the prior roadmap
(`docs/port-engineering/roadmap/remaining-capability-roadmap.md`)
already flagged that `filter/invert:inv`/`synth/solid:solid` must not be
counted as frontier progress. This probe's own harness initially
miscomputed "unported" as `212 − |typed_slice.json|` = 81, silently
re-including those same two programs as if they were unported — caught only
by cross-checking against the task's stated 79. Both are still zero-capability
free wins (pass validator+emitter unmodified) but are **excluded from every
count below**.

## Method

One Python harness (`gate_chain_engine.py`, ~1300 lines) walks the complete
gate chain for all 79 programs: run `validate_capabilities` +
`render_typed_cpp` unpatched, classify the first failing message against a
library of 25 generalization patches (each an exact-text monkeypatch,
restored in `finally`, composed by re-applying every active patch's
substitutions to the **pristine** original source each stage — never to a
previously-patched string, so any subset/order composes safely), apply the
matching patch, repeat, cap at 8 gates. Every patch is a **probe of "what's
next"**, explicitly not a real capability (matching this codebase's own
precedent: every shipped capability is a single-object-identity or exact-SHA
per-program profile, never a name-based allowlist). Extends
`future-precompute/analyze_candidates.py`'s builtin-admission technique and
`future-precompute/task32/probe_gate_chain.py`'s multi-stage composition to
all 79 programs and ~25 gate types instead of 4 programs and 2 gates.

Restoration is proven per stage: 9-field snapshot (function identity + source
SHA-256 for 5 recompilable targets, plus the 5 admission tables) taken before
and after every probe; `gate-chain-all-output.json` records
`restored_all: true` for **all 79 rows**, verified by direct query (zero
`false`).

Two engineering gaps were found and fixed *during* this run, each exactly the
shape the task warned about:

1. **First pass wrongly re-included the 2 free programs as "unported"** (see
   above) — caught by cross-checking the task's own stated 79, not by luck.
2. **`array_global_admission`'s first draft only patched the validator.**
   Running it against `normalMap` produced `PASS` at the validator but a
   *new* emitter failure (`unsupported typed type ivec2[9]` from
   `_Emitter.type()`, which has no array-display fallback at all — a second,
   previously-undocumented gap this engine found, not present in either
   prior roadmap). Fixed by adding an array-display branch to `type()` and a
   matching fallback to `function_parameter_type()`.

The engine also found gates the first-blocker view could not have surfaced by
construction: `filter/grain:grain` needed a **4th** gate
(`uvec3 >> uvec3`, then `uint ^ uint` scalar XOR) beyond the 3 the prior
Task-32 probe stopped at; `filter/normalMap:normalMap` similarly reached 4
gates and now clears mechanically end-to-end (Task 32 stopped at 2 and
declared it blocked). `classicNoisedeck/bitEffects:bitEffects` needed `<<`,
`&`, `^` (int AND uint), and `|` admission across two independent widening
passes before clearing.

## 1. Headline numbers

| | Count |
|---|---:|
| Corpus programs | 212 |
| Typed (in `typed_slice.json`) | 131 |
| Already-free (public, zero capability work — data-file only) | 2 |
| Public | 133 |
| **Unported (this report's scope)** | **79** |
| — Mechanically clears full chain (validator+emitter PASS) | 35 |
| — — Reachability-disqualified (dead code at default defines) | 1 (`filter/snow:snow`) |
| — — Needs new runtime **architecture** (derivatives) before real | 17 |
| — — **Landable with generator-only work on the EXISTING runtime** | **17** |
| — Terminal blocker this probe's patch library cannot generalize | 44 |

`35 (PASS) + 44 (blocked) = 79`. `17 (landable) + 17 (derivatives) + 1
(disqualified) = 35`.

## 2. Reachability filter (Task-31/32 technique, applied to all 35 PASS programs)

Call graph from `main` via `call`-node `signature_id`, same method as
`analyze_candidates.py`/`task32/probe_reachability.py`
(`reachability_probe.py`, `reachability-output.json`).

- **`filter/snow:snow` disqualified**, exactly as Task 32 found: its only
  `round()` site (`as_u32`) is defined but never called from any function
  reachable from `main` at this program's authorized define map. Confirmed
  independently by this engine's own call-graph walk (not re-quoting Task
  32 — recomputed).
- **New finding, not in either prior roadmap**: `classicNoisedeck/bitEffects`
  passes the full chain, but its `mask` const global (needed for the `<<`/
  `&`/`^`/`|` widenings) is referenced **only** inside 12 dead helper
  functions (`and`, `or`, `xor`, `not2`, `not3`, `modi`, `bitField`,
  `bitValue`, ...) — a bit-logic-gate code path this program's default
  `#define`s never select (18 of its 30 functions are unreachable; the
  boolean-logic family is one of several mutually-exclusive display modes).
  `bitEffects`'s **other** requirement, `floatBitsToUint`, sits in
  `randomFromLatticeWithOffset`, which **is** reachable. Net: bitEffects is
  *not* disqualified outright (a real render exercises `floatBitsToUint`),
  but four of its six gates (`global_admission_shift`, `bitwise_and`,
  `bitwise_or`, one of the two `scalar_uint_xor` sites) are validator/emitter
  admission requirements only — every global must type-check whether or not
  its readers are reachable — not requirements a full-render parity test
  would ever exercise. Flag this explicitly rather than silently crediting
  bitEffects's landing to capabilities a render can't actually validate.

## 3. Runtime-existence audit (the `float_bits_to_uint`/`glsl_round` lesson, applied again)

Full-tree grep (`include/`, `src/`, excluding generated `typed_generated/`),
not narrow two-file greps:

| Symbol the generator would need to emit | Exists already? | Where |
|---|---|---|
| `glsl::round` | **yes** (`floor(x+0.5)`, deliberately not `std::round`) | `numeric.hpp:10`, `glsl_runtime.hpp:20` (confirmed by Task 32, re-verified) |
| `noisemaker::float_bits_to_uint` | **yes** | (confirmed by Task 32, re-verified) |
| `glsl::reflect` | **yes**, already `Vec<N,float>` templated over N | `glsl_runtime.hpp:118-121` |
| `glsl::refract` | **yes**, already templated over N | `glsl_runtime.hpp:122-125` |
| `glsl::tanh` / `tanh_lanewise` | **yes** (curl already uses it) | `glsl_runtime.hpp:49,92-94` |
| `glsl::bitwise_xor`, `glsl::shift_right` | **yes**, `Vec<N,uint32_t>` templated | `glsl_types.hpp:199-215` |
| `glsl::Mat<N>` (matrix type + `*` for matrix·vector, vector·matrix, matrix·matrix) | **yes — already generic over N**, with `Mat2`/`Mat3`/`Mat4` aliases already declared (`glsl_types.hpp:213-247`) | **Not previously documented as already-generic in either prior roadmap** — both described "mat3/general-NxN support" as unscoped/unknown-cost. It is already fully implemented; only `APPROVED_TYPES`/generator dispatch is missing it. |
| `Vec<N,bool>` / `BVec2`/`BVec3`/`BVec4` type aliases | **yes, already declared** | `glsl_types.hpp:250` |
| `glsl::all`, `glsl::lessThanEqual` | **yes**, but deliberately `requires(N==2)`-constrained (by design, to match the single authenticated Extrude site) | `glsl_types.hpp:230-249` |
| `glsl::any`, `glsl::notEqual`, `glsl::greaterThanEqual`, `glsl::lessThan` | **no** | not found anywhere in `include/`/`src/` |
| `dFdx` / `dFdy` / `fwidth` | **no, not even a stub** | confirmed absent (matches prior roadmap's finding, re-verified) |

**Correction to both prior documents**: mat3/mat4 arithmetic needs **zero**
new runtime code. `Mat<N>` was written generic from the start; only the
generator's `APPROVED_TYPES` tuple and its binary-operator/constructor
dispatch (hardcoded to `mat2`/`mat2*vec2` — see §5) are missing the
generalization. This is now a two-part **pure generator-side** slice, not an
"unscoped, could be either kind" one as previously described.

## 4. Corrected capability → programs-fully-unblocked table (top capabilities)

Counting is **fully-unblocked**, i.e. this capability plus everything else the
program's chain needed, all landed, chain reaching `PASS`, minus the
reachability-disqualified `snow`. This is not a first-blocker count.

| Capability | Programs fully unblocked (this capability + its co-requisites) | Kind |
|---|---:|---|
| `global_admission` (const-typed global generalization) | 13 | pure generator (validator + emitter, two independent copies of the same rule) |
| `dFdx`/`dFdy` (paired) | 11 | generator admission is mechanical; **needs new runtime architecture** (quad record/replay) to be real |
| `index_expression_admission` | 9 | generator only, but this count is optimistic — see caveat below |
| `fwidth` | 6 | same as dFdx/dFdy: mechanical admission, needs the same new runtime architecture |
| `bitwise_and_admission` (`&`) | 4 | pure generator (native C++ `&`, no runtime gap) |
| `scalar_uint_xor_admission`/`scalar_int_xor` (widened `^`) | 4 | pure generator (native C++ `^`) |
| `round` builtin | 4 | pure generator; runtime already correct (`glsl_round`) |
| `array_global_admission` | 3 | generator work in **two** places (validator's `reject_type` + emitter's `type()`/`function_parameter_type()`, the gap this engine found); runtime uses plain `std::array`, no new runtime code |
| `uvec_shift_by_vector` (widened `>>`, incl. scalar) | 3 | pure generator |
| `bitwise_or_admission` (`\|`) | 2 | pure generator |
| `floatBitsToUint` builtin | 2 | pure generator; runtime already correct |
| `bvec_type_admission` | 2 | pure generator; runtime type (`Vec<N,bool>`) already generic |

**Caveat on `index_expression_admission`'s 9**: this probe's patch is
maximally permissive (bypasses the array-index proof requirement entirely
for any `id[...]` site) — a real capability needs a per-program authenticated
proof, following this codebase's own pattern (`fixed_nine`/`fixed_grid`/
`task19`/`task20` are each whole-program profiles, not a structural rule).
The 6 `filter/grade.glsl` keys share one physical source file and very
likely one real proof; `normalMap`/`osd`/`remap` each index a *different*
table shape and would each need their own. So "9 programs, 1 slice" is
optimistic; a defensible estimate is closer to "9 programs, 2-4 real proof
efforts" (1 for the grade cluster, up to 3 more for normalMap/osd/remap).

## 5. What's genuinely non-mechanical, and why (44 programs)

| Terminal blocker family | Count | Why this probe's admission technique can't clear it |
|---|---:|---|
| Non-canonical `for`-loop shape | 16 | Needs new structural *proof* logic per shape (parameter-bound trip count, non-literal start, `while`, early-`return`, swizzle/resolution-bound), not an admission relaxation — bypassing the enforcement (`loop_proof_bypass`) does not make an unproved loop provably bounded; confirmed by re-running with the bypass active: all 16 hit the SAME `unsupported typed statement for` message immediately, from a structurally different, unrelated check (`value.loop_proof is None`) that the safety-charge bypass doesn't touch. |
| Matrix arithmetic beyond `mat2 * vec2` | 9 | `matrix_type_admission` (adding mat3/mat4 to `APPROVED_TYPES`) is necessary but not sufficient — the generator's binary-operator dispatch and constructor dispatch separately hardcode "must be exactly `mat2`, must be `mat2*vec2`" (`generate_typed_slice.py:2048-2051`, `emit_typed_cpp.py:1300-1302`), independent of type approval. **This is still pure generator work** (§3 confirms `Mat<N>` is already generic) — a follow-on patch generalizing that dispatch was identified but not built/tested in this pass; flagged as the single highest-value next probe. |
| Varying / interface symbol needs an emitter-side name mapping | 5 | Validator-side admission (bypassing `if typed.interface_symbols: raise`) is trivial, but the emitter has no symbol-table entry for e.g. `v_texCoord`/`vColor` at all (`unmapped typed symbol` — a distinct, later gate) — confirms the prior roadmap's "wobble" finding and extends it to `grime`, `wormhole:deposit`, `spookyTicker`, `synth/shape`. |
| Whole-program authenticated array/table proof required | 4 | `cellRefract`/`kaleido`/`emboss`/`lighting` each declare a fixed-size local table (convolution kernel, palette) structurally like the existing `SHARPEN_KEY`/`SOBEL_KEY` `fixed_nine` mechanism, but none is in `SOURCE_LOCKS` — each needs its own SHA-fingerprinted profile, not a shared rule. |
| Struct member access (custom struct types) | 4 | `historicPalette`/`palette`/`julia`/`newton` need a struct-typed local/return (`HistoricPalette`, `PaletteEntry`, `JuliaResult`, `POIData`) — the emitter has **zero** struct-lowering path (no struct type table, no member-access codegen) even after the validator's blanket `if typed.structs: raise` is bypassed. |
| Whole-program authenticated profile required (non-struct) | 1 | `classicNoisedeck/caustic` needs its own word-hash profile carrier (already known-hard from prior work — Task 31 disqualified it on reachability too). |
| `mod` overload shape | 1 | `shapeMixer` needs a `mod` argument-type combination outside the admitted overload set; not resolved by plain builtin-name admission since `mod` already IS admitted — this is a narrower overload-shape gate. |
| Assignment operator gap (`^=` on a new type) | 1 | `filter/texture`. |
| `inout`/by-reference parameter codegen | 1 | `filter/watercolor:wcSimplify` — validator-side direction check is trivially bypassed, but the emitter has no by-reference parameter ABI at all. |
| Non-uniform sampler expression | 1 | `mixer/distortion` needs a general sampler2D function-parameter ABI, distinct from the single-key Focus-Blur borrowed-sampler profile. |
| Post-increment on an unproven target | 1 | `filter/median` (also has a `while`-loop shape issue). |

### Loop-proof family correction (extends prior roadmap §3, confirms 22 total)

All 22 programs whose chain touched `loop_proof_bypass` are accounted for
exactly (matches the prior roadmap's independently-derived 22-count — cross-
check, not blind trust). One correction: the prior roadmap classified
`synth/gabor`, `synth/newton`, `synth/julia` as "pure over-budget, cheapest
fix in the family — just raise the constants." Full-chain walking shows this
is only true for **`gabor`** (`PASS` once `loop_proof_bypass` alone is
applied). `newton` and `julia` hit a **second**, unrelated blocker after the
budget bypass — `unsupported typed type POIData`/`JuliaResult`, i.e. a
struct-return type, not a numeric budget at all. Raising `depth`/
`entrypoint_charge` alone would **not** land `newton`/`julia`; struct
support (§5 above) would still be required.

## 6. Recommended implementation order

Ordered for programs-landed-per-slice, generator-only work before runtime
architecture, reusing what already exists in the runtime before assuming
anything is missing.

1. **Ship the 2 free programs** (`filter/invert:inv`, `synth/solid:solid`) as
   a data-file consolidation — zero capability work, zero frontier credit
   (per §10 of the prior roadmap, re-confirmed here).
2. **`global_admission`** (generalize const-typed global declaration,
   validator + emitter in lockstep). Prerequisite for 13 programs; several
   (bitEffects) only need it for admission-completeness of dead code (§2) —
   land it but don't expect all 13 to be render-validated equally.
3. **Bitwise-operator family** (`&`, `|`, `^` widened to int/uint scalar,
   `>>` widened to uvecN/scalar, unary `~`). All pure generator, no runtime
   gap, largely independent single-line dispatch widenings.
   *(+4 net beyond step 2's overlap: bitEffects, glyphMap, osd, grain,
   synth/bitwise — 5 keys, 4 new once bitEffects is already counted)*
4. **`round`, `floatBitsToUint`, `reflect`, `tanh` builtins** — all already
   correct in the runtime (§3), each a single-identity-gate deletion plus
   per-program authenticated profile, mechanical and low-risk.
   *(+4: fxaa, grain*, normalMap*, scanlineError, +shapeMixer partially — *already counted via other gates)*
5. **Vector-relational builtins**: `all`/`lessThanEqual` (already exist,
   `N==2`-constrained by design) plus **new** `any`/`notEqual`/
   `greaterThanEqual`/`lessThan` (need new but trivial runtime templates,
   mirroring the existing `N==2` pattern) and `bvec_type_admission`
   (runtime type already generic). *(+2: edge, waves)*
6. **`array_global_admission`** (validator `reject_type` + emitter `type()`/
   `function_parameter_type()` — this engine's own two-part fix). Plain
   `std::array`, no runtime gap. *(+3: normalMap, osd, remap; each still
   needs its own array-shape review, not a blanket rule — see §4 caveat)*
7. **`index_expression_admission`**, scoped as a real per-program proof
   (grade cluster first — one shared source file, likely one shared proof).
   *(+6 grade keys firm; +3 normalMap/osd/remap already counted above,
   contingent on their own array proofs landing too)*
8. **Generalized matrix binary-op/constructor dispatch + `mat3`/`mat4` type
   admission.** Identified as pure generator work in this pass (§3, §5) but
   the dispatch-generalization patch itself was not built/tested here —
   highest-value next probe, since the runtime needs nothing new.
   *(+9 candidates, unconfirmed pending that follow-on probe: cellNoise,
   colorLab, effects, glitch, moodscape, noise(classic), shapes, adjust,
   colorspace)*
9. **Derivatives (`dFdx`/`dFdy`/`fwidth`) codegen admission**, bundled with
   the **new quad-record/replay runtime architecture** it depends on to be
   real (unchanged from the prior roadmap's finding, re-confirmed: grep for
   `dFdx`/`dFdy`/`fwidth` across `include/`/`src/` is still empty). Largest
   single remaining family by program count (17) but the only one requiring
   net-new runtime execution-model infrastructure, not generator/proof work.
10. **Varying/interface-symbol emitter mapping.** *(+5: grime, wormhole:deposit, spookyTicker, wobble, synth/shape — spookyTicker/wobble/shape also need other gates from steps above)*
11. **Struct member-type support** (new: struct type table + member-access
    codegen in the emitter, beyond the validator's already-trivial bypass).
    *(+4: historicPalette, palette, julia, newton)*
12. **Whole-program authenticated array/table proofs**, one per program,
    following the `SHARPEN_KEY`/`SOBEL_KEY` `fixed_nine` precedent.
    *(+4: cellRefract, kaleido, emboss, lighting)*
13. **Non-canonical loop-proof shapes**, new structural proof logic per shape
    (unchanged from the prior roadmap's §3.3 breakdown — not re-derived in
    finer grain here beyond confirming the 22-program total and the
    newton/julia correction above). *(+16, minus gabor already landed at
    step 2-tier budget bypass, minus newton/julia which need step 11 too)*
14. **Singleton/architectural items**: `mod` overload widening (shapeMixer),
    `inout`/by-reference parameter ABI (watercolor:wcSimplify), general
    sampler2D function-parameter ABI (mixer/distortion), `^=` on new types
    (texture), post-increment on unproven targets (median), Caustic's
    whole-program word-hash profile. No cross-program synergy found for any
    of these six; do opportunistically. *(+6)*

## 7. Honest total

- **79 unported programs** in scope (corrected from an internal
  miscomputation of 81 — see header).
- **35 mechanically clear** the full validator+emitter chain today under
  this probe's generalization patches; **34** are legitimate targets
  (1, `snow`, is dead-code-disqualified).
  - **17 landable now** with generator-only work against the *existing*
    runtime (no new C++ function, no new architecture) — see §4.
  - **17 need the derivatives runtime architecture** (quad record/replay) in
    addition to mechanical codegen admission — real work, not a data-file
    update, exactly as the prior roadmap sized it, re-confirmed.
- **44 programs** are blocked by something this probe's admission-relaxation
  technique cannot generalize — each needs either new structural proof logic
  (loop shapes, 16), a second generator-side dispatch gap beyond type
  admission (matrix arithmetic, 9), new emitter-side lowering that doesn't
  exist at all (varying-symbol mapping 5, struct member access 4), a new
  per-program whole-program authenticated profile (array/table proofs 4,
  Caustic 1), or a narrower shape gap within an already-admitted capability
  (mod overload, `^=`, post-increment, `inout` ABI, sampler-parameter ABI —
  5 singletons).
- **Distinct capability slices remaining, revised estimate: ~18-24** (down
  from the prior roadmap's 20-30 estimate, now that mat3/mat4/bvec/all-
  family runtime existence is confirmed rather than assumed unknown, and now
  that grain/normalMap/bitEffects/osd/synth-bitwise are confirmed to
  collapse into 2 bitwise-family slices rather than needing per-program
  bespoke work). This count still follows the codebase's own demonstrated
  precedent — every admitted builtin/matrix/array capability still needs a
  **per-program** authenticated SHA/identity profile on top of the shared
  code-path generalization, so "slice" here means "shared code-path
  capability," not "one commit unblocks everything using it."
- **Programs I believe cannot reach bit-exact parity at all, or only with
  very large new investment**: none newly disqualified beyond what prior
  work already found (`classicNoisedeck/caustic`, `filter/snow` on
  reachability grounds — re-confirmed, not new). No program in this pass hit
  a blocker suggesting fundamental impossibility; every NO_GENERIC_PATCH
  terminal is "needs new but buildable proof/lowering/ABI work," not "cannot
  be represented in this IR."

## Appendix: files in this directory

- `gate_chain_engine.py` (+ `.sha256`) — the harness: 25 registered gate
  patches (some generated dynamically per-builtin-name), classifier,
  escalation logic (`global_admission` → `mutable_global_admission` when the
  same message re-triggers after the first patch — two structurally
  different capabilities sharing one error message), full restoration proof.
- `gate-chain-all-output.json` (+ `.sha256`) — per-program chain, every
  stage's blocker message, patches applied, restoration proof, for all 79
  programs.
- `reachability_probe.py` (+ `.sha256`) — call-graph-from-`main` reachability
  for all 35 PASS programs.
- `reachability-output.json` (+ `.sha256`) — per-program builtin-site/global
  reachability detail (source of the snow/bitEffects findings in §2).
- `sanity-*.json` — intermediate validation runs kept for audit trail (each
  is a subset re-run used to catch and fix the two engineering gaps in the
  Method section above).
