# Frontier census — every unported program, 2026-08-12

Authoritative census of all 81 unported programs in the noisemaker-for-cpp
C++20 port, produced by **running the real analysis path** (`parse_program` →
`analyze_program` → `validate_capabilities` → `render_typed_cpp`) against
every one, not by reading GLSL. Read-only throughout; nothing under
`noisemaker-for-cpp` or `noisemaker-for-cpu` was modified; `git` was never
invoked.

## Methodology and snapshot discipline

Another agent was actively editing `generate_typed_slice.py`,
`emit_typed_cpp.py`, `typed_slice.json`, and `tests/test_typed_generator.py`
while this census ran. To get a self-consistent answer immune to those
concurrent edits, the entire `tools/glslcpp/` package (parser, semantic
analyzer, generator, emitter, corpus, fixtures — 3.8MB) was snapshotted
read-only at:

```
snapshot time (rsync start):  2026-08-12T22:51:21Z
snapshot complete:             2026-08-12T22:52:35Z
snapshot path: docs/port-engineering/census/snapshot/20260812T225121Z/repo
```

All analysis below ran against that frozen copy, imported via `sys.path`
insertion — the real `noisemaker-for-cpp` tree was only ever *read* to
produce the snapshot. File hashes for the four contended files at snapshot
time are recorded in
`snapshot/20260812T225121Z/{generate_typed_slice.py,emit_typed_cpp.py,typed_slice.json,test_typed_generator.py}.sha256`.

At snapshot time `typed_slice.json` already contained **137 rows = the 131
pre-existing typed programs + all 6 `filter/grade:*` programs**, confirming
the grade cluster had already landed in-tree exactly as the task description
says to treat it. So the corpus math is: **212 total − 137 currently-typed =
75 currently-remaining**, and **75 + 6 grade = 81 unported**, matching the
task's headline number exactly. Manifest enumeration (never a `*.glsl` glob)
confirms **212** programs, with `filter/wormhole:deposit` the sole `.frag`
source.

For each of the 75 non-grade unported programs, the real, unmodified
validator (`generate_typed_slice.validate_capabilities`, called with
`gen._defaults(repo, key)` — the exact authorized define map function named
in the task) was run and its **first raised diagnostic** recorded verbatim,
including file:line:col span. Reachability was computed independently with a
from-scratch BFS over the typed IR's call graph starting at `main`, walking
both user-function (`kind == "call"`) and builtin (`kind == "builtin"`) call
sites — this is a different code path than the generator's own loop-proof
reachability machinery, so it serves as an independent check. For several
large clusters, a further "relaxed probe" technique was used: a scratch copy
of the validator (never the real file) had one specific gate permissively
patched to reveal what blocker sits *behind* it, without claiming that
relaxation is itself a real, shippable mechanism. This is how the "unlock
cost" answers below were obtained empirically rather than by inspection.

All scripts and raw outputs are under `docs/port-engineering/census/`
with `.sha256` sidecars: `run_census.py` (main driver → `raw_census.json`),
`probe_global_decl.py` (→ `global_decl_probe.json`), `probe_relaxed_global.py`
(→ `relaxed_global_probe.json`), `probe_relaxed2_mat3.py` /
`probe_relaxed3_mat3.py` (→ `relaxed2_mat3_probe.json` /
`relaxed3_mat3_probe.json`), `probe_bitwise_sites.py` (→
`bitwise_sites_probe.json`), `probe_relaxed_varying.py`, and `build_final.py`
(→ `frontier-census.json`, the machine-readable per-program deliverable).

## Cluster table

| Cluster | Count | Mechanism status | Yield per unit of mechanism work |
|---|---:|---|---|
| Loop-proof — program-proof gate | 19 | 16 already designed (shape-by-shape) by the loop-proof study; **3 more (`effects`, `noise`, `median`) hit the identical failure signature but are outside that study's scope** — see contradictions | 16 land mechanically once their per-shape fixes ship; `effects`/`noise` likely piggyback for free (same shapes as already-costed members); `median` has no known mechanism |
| Derivatives (dFdx/dFdy/fwidth) | 15 | Fully designed and prototype-verified (2196/2196 exact); 15-program integration already planned | All 15 land in one mechanism landing — the single largest yield in the corpus |
| Grade | 6 | Landed (already in `typed_slice.json` at snapshot time) | 0 further work |
| Global decl — matrix (`fwdA` mat3) | 7 (5 "6-real-target" + moodscape dead + **shapeMixer, a new 8th member the prior study missed**) | Matrix-dispatch cluster's mechanism (`Mat<N>` generalization, 11 sites) is designed but **does not fully unlock these on its own** — see the 3-layer probe below | 5-6 land per matrix-admission landing, but need an *additional*, uncosted "matrix indexing" (`mat[i][j]`) fix first |
| Global decl — const scalar table (int) | 5 | Partial: `SOURCE_GLOBAL_LITERAL_INT` mechanism exists but is a closed per-key allowlist; extending it is cheap but each program still has its own downstream blocker (verified — see below) | Registration-cheap per program, but none land free |
| Global decl — const scalar table (uint) | 4 | No mechanism (existing const-int mechanism is `int`-only, `uint` excluded by an explicit type check) | New but narrow (int, add uint); all 4 additionally need `round` admission downstream |
| Global decl — const vector table (vec3) | 4 | No mechanism | Each is bespoke; one (`wobble`) reveals a *second, emitter-only* gate distinct from the validator gate |
| Loop-proof — safety-charge (per-loop budget) gate | 3 | `gabor` has a named plan ("depth cap"); **`julia` and `newton` are newly characterized here — absent from every prior document** | Budget-cap increase or per-program bound proof; independent of the 19-member program-proof gate above |
| Global decl — non-const mutable global scratch | 3 (`cellRefract`, `kaleido`, `synth/shape`) | No mechanism; qualitatively harder — a genuinely mutable global, not a const table, no analog in any typed program | Bespoke, likely the most invasive of the global-decl sub-families |
| Global decl — const/array table (int[80]) | 2 (`osd`, `spookyTicker`) | No mechanism (array-typed const global) | Bespoke; `spookyTicker` additionally needs varying admission |
| Zero-blocker (administrative only) | 2 | N/A — already pass parse+validate+emit | **Free.** `filter/invert:inv` and `synth/solid:solid` need only a `typed_slice.json` row |
| Varying admission (v_texCoord) | 1 terminal (+3 downstream via global-decl) | No mechanism at all (`interface_symbols` unconditionally rejected; **zero** of the 212 programs currently uses one) | New, narrow, real: unlocks `grime` down to a next blocker (`floatBitsToUint`), and is a prerequisite (but not sufficient) for `spookyTicker`/`texture`/`wobble` |
| Structurally ineligible | 1 (`wormhole:deposit`) | N/A | Not a mechanism gap — see finding below |
| Builtin admission: round / any / reflect | 3 singletons (`posterize`, `waves`, `lighting`) | No admission path for any of the three; same node-identity pattern used for `round`/`tanh`/`floatBitsToUint`/`all` is available but unbuilt | Each unlocks exactly 1 program directly, but `posterize`/`waves` also need derivatives; `reflect` additionally reappears 3 gates deep inside `shapeMixer` |
| Matrix (mat4, `glitch`) | 1 | Slice C of the matrix-dispatch plan (chained `T*Q*S` product) | 1 program, already costed by the matrix study |
| Caustic word-hash profile | 1 | Mechanism (`authenticate_caustic_word_hash`) already implemented in `frontend/caustic_word_hash_profile.py`, just never wired to a slice row | Cheap to land structurally, but the bitwise use it guards is dead code at the authorized default (`NOISE_TYPE`) — confirmed independently, see below |
| Sampler-as-parameter (`distortion`) | 1 | No mechanism (sampler2D passed as a function argument, not referenced as a bound uniform) | Singleton; also needs derivatives + reflect downstream |
| Bitwise (clean) | 1 (`synth/bitwise`) | Needs the signed-arithmetic `>>` primitive plus `^` admission | Sole program blocked *only* on bitwise |
| inout parameter direction | 1 (`watercolor:wcSimplify`) | No mechanism | Singleton |
| Uniform block | 1 (`synth/remap`) | No mechanism | Singleton |

Cluster counts sum to 81 (75 live-validated + 6 grade). Full machine-readable
breakdown: `frontier-census.json`.

## The critical path

Ranked by programs unlocked per unit of distinct mechanism work, using only
what this census actually verified (not inspection-based estimates):

1. **Derivatives (15 programs, one mechanism, already fully designed).** This
   is the correct first move — architecture validated, prototype gaps closed
   (2196/2196 exact against the real JS runtime), and it is provably a *pure
   win*: 15 programs land with no other blocker in the chain, verified here
   independently via BFS reachability on every dFdx/dFdy/fwidth call site.
2. **The 2 zero-blocker programs (`invert`, `solid`) cost nothing** and
   should be landed alongside step 1 as pure bookkeeping — they already pass
   the full pipeline today.
3. **Loop-proof program-proof gate, 16-19 programs.** Second-largest
   single-mechanism yield. Recommend re-verifying whether `effects` and
   `noise` (classicNoisedeck) genuinely piggyback on shapes the loop-proof
   study already costed (`effects` matches the "float induction" shape
   already priced for `zoomBlur`; `noise` matches "parameter-bound," already
   priced for `tetraColorArray`/`synth/noise`) before excluding them from the
   plan — see contradiction below.
4. **Builtin admission for `round`, `any`, `reflect`** should ride along with
   derivatives work, since two of the three (`posterize`, `waves`) exist
   purely to unblock a derivatives-cluster program, and the node-identity
   admission pattern is already established and cheap per prior landings
   (`round`/`tanh`/`floatBitsToUint`/`all`+`lessThanEqual`).
5. **Matrix cluster is NOT a clean next step despite being "already
   designed."** This census's 3-layer relaxed-probe chain
   (global-decl → typed-type mat3 → global-matrix-declaration gate) shows
   that admitting `mat3` types does **not** unlock any of the 7 candidate
   programs by itself — 6 of 7 hit a *fourth*, uncosted gate
   ("unsupported typed expression index," i.e. `mat[i][j]` row/column
   indexing) and the 7th (`shapeMixer`) falls through to `reflect`. Treat the
   "11 sites across validator and emitter" note in the matrix precompute
   report as an undercount unless indexing is confirmed to be one of them.
6. **The three "safety-charge" loop programs (`gabor`, `julia`, `newton`)**
   are a distinct, smaller mechanism (per-loop trip-count/depth/product/
   charge caps in `audit_loop_proofs`, not the aggregate proof used by the
   19-member cluster above) and should be scheduled as their own small batch
   once budget-cap policy is decided; only `gabor` had prior coverage.
7. **The global-declaration mega-cluster (25 programs) is the expensive,
   uncharacterized tail** the task asked to surface. It is not one
   mechanism — it is at least five distinct resource shapes (const mat3,
   const int, const uint, const vec3, const/mutable arrays), **none of which
   land free even after admission** (verified for all 25 by direct
   relaxed-probe rerun; every one hits a second, different blocker). This
   should be scheduled program-by-program, not planned as a single
   mechanism landing.
8. **Varying admission (v_texCoord)** is a real, previously-uncharacterized,
   narrow mechanism: zero of the 212 corpus programs (typed or not) uses an
   explicit varying today, so this is greenfield. It benefits `grime`
   (lands to one further blocker, `floatBitsToUint`) and is a *necessary but
   insufficient* prerequisite for `spookyTicker`, `texture`, `wobble` (each
   also needs its own global-declaration fix first).
9. **Singletons last** (`bitwise`, `watercolor`'s `inout`, `remap`'s uniform
   block, `distortion`'s sampler-parameter, `caustic`'s word-hash carrier) —
   one program each, no shared leverage.

## Structurally ineligible: `filter/wormhole:deposit`

This is not merely unported — the evidence indicates it cannot be ported
under the current architecture without an entirely new pass type:

- Its terminal (and only) blocker is `unsupported varying` at `1:1`: the
  validator's interface-symbols check (`generate_typed_slice.py:2097-2098`)
  unconditionally rejects **any** program with a declared varying, with zero
  admission mechanism anywhere in the generator.
- Its sole input is `in vec4 vColor` — a per-vertex interpolated color, not a
  uniform or a sampled texture. Confirmed via manifest: **0 uniforms, 0
  samplers, 1 interface symbol, 1 reachable function (`main` itself, a
  9-line passthrough)**.
- **`filter/wormhole:deposit` is the only program in the entire 212-program
  corpus with `"runtime_key": null`** in `manifest.json`. Its sibling passes
  in the same 3-pass `filter/wormhole` effect — `clear` (pass 0) and `blend`
  (pass 2), both ordinary uniform/texture-driven fragment passes — are
  **already typed and shipped**. The manifest itself already marks `deposit`
  as excluded from the runtime dispatch mechanism that every other program
  (typed or not) carries.
- Structurally, `deposit` implies an upstream vertex/point-rasterization
  stage (a particle or point-sprite splat pass that computes `vColor` per
  vertex and interpolates it across a rasterized primitive) — a categorically
  different rendering technique from the per-pixel, fullscreen-fragment
  kernel model every other program in the corpus (ported or not) uses. The
  CPU port's pass-runner model (per-pixel evaluation as a function of pixel
  coordinate, uniforms, and textures) has no analog for a per-vertex
  interpolated attribute.
- A relaxed-probe specifically admitting `vec2` varyings (to isolate whether
  *any* varying could pass, separate from the vColor question) still rejects
  `wormhole:deposit`'s `vec4` varying, confirming this is not just "the
  varying mechanism doesn't exist yet" but a distinct resource-type problem
  even after that mechanism exists.

**Caveat:** this determination rests on resource-shape evidence (manifest,
validator, reachability) and was not cross-checked against a full read of
`pass_runner.cpp`'s pass-dispatch code, so it does not rule out a
currently-unbuilt point/vertex pass mode existing in the native renderer
outside the typed-program pipeline. Given the manifest's own `runtime_key:
null` marking, that is unlikely, but flagged as not exhaustively verified.

No other program in the 81 shows comparable evidence of ineligibility.
`filter/grime:grime` also hits `unsupported varying`, but its varying is an
ordinary `in vec2 v_texCoord` — the same UV convention every typed program
already re-derives from `gl_FragCoord`/`resolution` — so it is merely
unported, not ineligible (see Varying admission above).

## Singletons (the expensive tail, identified early)

Programs whose terminal blocker's *mechanism* is unique to that program
(no other unported program shares the same missing capability):

| Program | Blocker |
|---|---|
| `synth/bitwise:bitwise` | `unsupported binary operator ^` (bitwise-clean) |
| `filter/watercolor:wcSimplify` | `unsupported parameter direction inout` |
| `synth/remap:remap` | `unsupported uniform block` |
| `mixer/distortion:distortion` | `unsupported sampler parameter` (sampler2D as a function argument) |
| `classicNoisedeck/caustic:caustic` | `exact Caustic word hash profile carrier required` |
| `classicNoisedeck/glitch:glitch` | `unsupported typed type mat4` |
| `filter/lighting:lighting` | `unsupported builtin reflect` (terminal; also reappears buried in `shapeMixer`, so not a pure singleton once downstream chains are counted) |
| `filter/posterize:posterize` | `unsupported builtin round` (terminal; also needed downstream by 4 global-decl-cluster programs, so not a pure singleton either) |
| `filter/waves:waves` | `unsupported builtin any` |

`round` and `reflect` are listed because they are each other program's *sole*
terminal blocker, but are flagged as not fully isolated since both
capabilities are independently required by other programs deeper in their
blocker chains (`round` by `fxaa`/`grain`/`snow` downstream; `reflect` by
`shapeMixer` downstream). True one-off, no-reuse-anywhere singletons:
`bitwise` operator `^`, `inout`, uniform block, sampler-as-parameter, and the
Caustic word-hash carrier.

## Prior documents this census contradicts, with evidence

1. **`REMAINING-WORK-ROADMAP.md`'s derivatives section, re: `mixer/distortion`.**
   Claim: excluded from the 17-member derivative set because it is "genuinely
   calls them but is terminally blocked on local arrays." **Refuted.** The
   real, unmodified validator's first diagnostic for `mixer/distortion:distortion`
   is `mixer/distortion:distortion:91:33: unsupported sampler parameter` — a
   sampler2D passed as a function argument. `distortion` does have live,
   BFS-reachable `dFdx`/`dFdy` **and** `reflect` calls, but they are not what
   the validator rejects first. "Local arrays" may be a real, further-downstream
   issue not yet reached by this census (validation stops at the first
   blocker), but it is not the terminal one.

2. **The task's own framing, independently re-confirmed rather than
   contradicted:** `caustic_word_hash_profile.py`'s in-source "live,
   reachable" comment and `post-scalar-bitwise-frontier-audit.md`'s "four
   reachable `bitEffects` helper calls" claim. This census's independent BFS
   (a different implementation than the generator's own reachability
   machinery) finds `classicNoisedeck/caustic:caustic`'s bitwise sites
   **unreachable** (`any_reachable: False`) from `main` at its authorized
   default, and reproduces the exact 5-member dead list from
   `bitops-precompute.md` byte-for-byte:
   `caustic`, `classicNoisedeck/effects`, `classicNoisedeck/moodscape`,
   `classicNoisedeck/noise`, `synth/noise`. This independently corroborates
   the roadmap's adjudication, not the two contradicted source comments.

3. **The matrix-dispatch precompute report's 9-candidate discovery list is
   missing `classicNoisedeck/shapeMixer:shapeMixer`.** `shapeMixer` declares
   the identical `const mat3 fwdA` global as the other 7 matrix candidates
   (byte-for-byte same declaration shape) and, once that global-declaration
   gate and the `mat3` typed-type gate are both relaxed, chains down to the
   *same* "unsupported typed expression index" family the other 6 candidates
   hit, before finally landing on `unsupported builtin reflect`. The most
   likely explanation: the prior study's candidate discovery scanned for
   `matrix_binary_sites` (matrix arithmetic, e.g. `mat * vec`), and
   `shapeMixer` only **indexes** into `fwdA` (`fwdA[i]`) rather than
   multiplying through it, so it never produced a `matrix_binary_sites` hit
   and was never enumerated as a candidate — even though it shares the exact
   same root blocker as the other 7.

4. **The loop-proof study's `terminal_16` list appears to have three
   unexplained gaps: `classicNoisedeck/effects:effects`,
   `classicNoisedeck/noise:noise`, and `filter/median:median` all hit the
   identical validator diagnostic** (`unsupported counted-for program proof`)
   as the 16 characterized members, and for `effects`/`noise` specifically,
   direct introspection of `rebuild_authenticated_counted_loop_proofs`
   confirms they fail for the **same reason** as counted members — a
   genuinely unproved loop, not a call-graph cycle, not an over-budget
   metric (`call_graph_acyclic: True` for both; `unproved_loop_count: 1` for
   both). `effects` even appears in the study's own `shape_groups` under
   "float induction" (the same shape already priced for the counted member
   `zoomBlur`), and `noise` appears under "parameter-bound" (the same shape
   priced for counted members `tetraColorArray`/`synth/noise`) — yet neither
   made the final 16. `median` is very likely deliberately excluded (its
   `while`-loop quickselect is separately flagged elsewhere as "not soundly
   provable statically," unlike the other two), but no equivalent
   explanation for `effects`/`noise` was found in any prior document. This is
   reported as an unresolved gap, not asserted as a wrong final count — it
   may be that a valid reason exists in a document this census did not
   locate.

## What could not be determined

- **Whether the 25 global-declaration programs' downstream blockers (found
  via the relaxed-probe technique) are themselves each singletons or share
  further sub-mechanisms.** The relaxed probe reveals only the *next* gate,
  one layer at a time; a full recursive chain-walk to each program's true
  final PASS state was not performed for all 25 (only fully chained for the
  7-member matrix sub-family, 3 layers deep). Concretely open: `bitEffects`
  and `glyphMap` both land next on `unsupported binary operator &` — whether
  that is the *same* shared bitwise mechanism as the 13-partial bitops
  cluster, or a coincidence, was not verified.
- **The exact 13-member/13-member split inside the bitwise family's 26
  reachable-non-terminal programs** (roadmap's "13 use bitwise but have a
  named second blocker" vs. "13 are a naive-grep trap already covered by
  uint-vector-bitwise"). This census independently reproduces the
  **aggregate** figures (32 total bitwise-touching, 5 dead, 1 clean, 26
  reachable-with-other-terminal-blocker — all exactly matching prior
  counts), but distinguishing which 13 of the 26 are already covered by the
  existing `uint-vector-bitwise` capability versus which 13 genuinely need
  new bitwise work would require checking each site's specific operand
  shape against `APPROVED_CAPABILITIES`, which was out of budget here.
- **`filter/watercolor:wcSimplify`'s and `synth/remap:remap`'s downstream
  chains** were not relaxed-probed at all (true one-shot terminal-only
  reads) — it is unknown whether a second blocker sits behind `inout` or the
  uniform-block rejection.
- **Whether `wobble`'s emitter-only gate** (`unsupported source global
  declaration`, found only after validator-side relaxation let it pass) has
  siblings among the other 24 global-declaration programs — only `wobble`
  was probed this deep; the other 24 were only relaxed at the validator
  layer, so an emitter-side surprise for any of them cannot be ruled out.
- **Full recursive resolution was not attempted for `glyphMap`,
  `historicPalette`, `palette`, `fxaa`, `grain`, `normalMap`, `snow`, `edge`,
  `emboss`, `scanlineError`, `osd`** beyond their first downstream blocker
  (recorded in `relaxed_global_probe.json`); whether each is 1, 2, or 4 gates
  from PASS is unknown.

## Full per-program table

See `frontier-census.json` for the complete 81-row, machine-readable table
(terminal blocker with span, cluster, downstream blockers, reachability,
unlock-cost note, bitwise cross-reference, and raw source hash for every
program). Summary by cluster, program counts as tabulated above; full key
lists are reproducible by grouping that file on the `cluster` field.
