# Task 31 fresh frontier audit: classicNoisedeck/caustic:caustic

## Result

Select exactly `classicNoisedeck/caustic:caustic`; no known blocker beyond
the two-gate closure this task authenticates. Fresh analysis of the live
post-Task-30 tree (corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`,
unchanged) found **212 corpus / 130 typed / 132 public / 80 publicly
unported** programs — confirmed directly from `tools/glslcpp/typed_slice.json`
(130 entries, includes `filter/extrude:extrude`) and
`tools/glslcpp/corpus/<revision>/manifest.json` (212 entries, via
`check_corpus --check`, exit 0). Typed/public ordered-key SHA-256 values are
`d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904` and
`4fe573b21a782a784b7fcacacaa276a03a395a1b8c92e83149971b8a19831056`, matching
the accepted post-Task-30 state exactly.

Adding Caustic alone projects **131 typed / 133 public / 79 unported**,
typed ordinal **0** (Caustic becomes the new alphabetically-first typed key),
with ordered hashes `0741bca3f0bd8cc577a42824cd9da480fb462f36f6e5f5ed65e92b2ad95c3060`
and `64e2b0677d3e3bc70de1f34d2b389d6fb50ec7a71278676f1f65c53bab1829f5`. This
matches the frozen precompute's projection exactly — no correction needed;
see `task-31-brief.md` for the full independent re-derivation.

## No newly eligible program after Extrude

All 82 corpus keys currently outside the 130-typed slice were freshly
parsed/analyzed against the live validator (`task31_frontier_scan.py`, which
recomputes this from scratch every run, not from any cached list). Only the
two already-public manual programs (`filter/invert:inv`, `synth/solid:solid`)
pass the validator unassisted today — identical to the set Task 30's own
frontier audit found before Extrude landed, and *smaller* than the pre-
Extrude remaining set by exactly one entry (`filter/extrude:extrude` moved
from "remaining" to "typed"; 83 → 82). No other program crossed from
"remaining" to "passing" as a side effect of Extrude landing — expected on
structural grounds, since each corpus program is a self-contained GLSL file
parsed and analyzed independently of every other program, so a change
confined to `extrude.glsl`'s own authentication cannot alter any other
program's validator outcome; confirmed directly rather than merely assumed,
by re-running the validator against all 82 remaining programs this session
and finding exactly the same 2-key passing set Task 30 reported.

## Rejection landscape among the 82 remaining programs

| Blocker category | Count | Notes |
| --- | --- | --- |
| `unsupported global declaration` | 30 | large, systemic (global-state family, likely simulation/multi-pass effects) |
| `unsupported builtin <X>` | 20 | see breakdown below |
| `unsupported counted-for program proof` | 19 | large, systemic (loop-proof family) |
| `unsupported counted-for safety charge` | 3 | loop-proof family |
| `unsupported varying` | 2 | |
| PASS (validator) | 2 | `filter/invert:inv`, `synth/solid:solid` — the two known manual public keys, unchanged |
| `unsupported typed type mat4` | 1 | |
| `unsupported typed expression index` | 1 | |
| `unsupported parameter direction inout` | 1 | |
| `unsupported sampler parameter` | 1 | |
| `unsupported binary operator <X>` | 1 | |
| `unsupported uniform block` | 1 | |

**`unsupported builtin <X>` breakdown (20 programs, 6 distinct builtins):**

| Builtin | Count | Programs |
| --- | --- | --- |
| `dFdx` | 10 | `filter/bulge`, `filter/lens`, `filter/lensWarp`, `filter/octaveWarp`, `filter/pinch`, `filter/polar`, `filter/pondRipples`, `filter/spiral`, `filter/tunnel`, `filter/warp` |
| `fwidth` | 5 | `filter/celShading:celShadingColor`, `filter/halftone`, `filter/stamp:stThreshold`, `filter/step`, `filter/stipple` |
| `floatBitsToUint` | 1 | `classicNoisedeck/caustic:caustic` — **this task's target** |
| `reflect` | 1 | `filter/lighting` (see below — real work, not a Task-31-sized slice) |
| `round` | 1 | `filter/posterize` — a *different* `round` site than the one Gather Sorted already authenticates; not automatically admitted by that profile's identity scoping |
| `any` | 1 | `filter/waves` — confirms Extrude's explicit ban on `any` remains structurally intact; `waves` is still rejected exactly as Task 30's brief required |
| `tanh` | 1 | `synth/curl` — the precompute's runner-up |

**Derivative family (`dFdx`/`fwidth`, 15 of 20 builtin-blocked programs) is
a large, systemic gap — not a single-task-sized candidate.** No derivative
support (`dFdx`, `dFdy`, `fwidth`) exists anywhere in the current typed
pipeline; admitting it would need its own dedicated design (screen-space
derivative semantics have no meaningful single-pixel CPU analog without a
neighborhood/finite-difference model, unlike a single builtin/operator
identity gate). Correctly out of scope for both this task and any other
single-program pick at the current frontier.

**Cross-check against the precompute's 3-way comparison (Curl / Caustic /
Lighting):** live-verified this session, unaffected by Extrude landing:
- `classicNoisedeck/caustic:caustic:192:21: unsupported builtin
  floatBitsToUint` (same site as before);
- `synth/curl:curl:196:12: unsupported builtin tanh` (same site as before);
- `filter/lighting:lighting:93:26: unsupported builtin reflect` (same site
  as before).

All three remain exactly where the precompute found them. The `task-31-
precompute-report.md`'s ranking and "do not batch" analysis (Caustic and
Curl are both genuinely two-gate, single-function/four-function closures
respectively that terminate in a full render with no third gate; Lighting
needs real generalization of `prove_fixed_nine_local_tables()` to search a
named non-`main` function, which is materially bigger work) is unaffected
by Extrude landing and was independently re-derived, not merely re-read,
for Caustic specifically in `task-31-brief.md` (full gate-chain walk with
monkeypatch/restore, live render proof, whole-program closure scan).

## Selection stands: Caustic

Nothing in this session's independent re-scan changes the precompute's
selection. Caustic remains the smallest, cleanest, single-function,
two-gate, no-third-gate closure among the currently-blocked "unsupported
builtin" bucket, with a fully mechanical C++ lowering path for both halves
(one net-new ~1-line bit-cast function; one reused-verbatim native operator,
already proven live in the committed `typed_slice.cpp` via Task 27's Perlin
XOR emission) and no shared-runtime-template risk of the kind Curl's `mod`
relaxation carries (Curl's fix touches a `requires(N==2)` template already
used by every other `mod(vec2,...)` caller in the corpus; Caustic's fix
touches nothing shared with any other already-typed program).

## Artifact inventory (this session)

| Artifact | Purpose |
| --- | --- |
| `task31_identity.py` / `task31-identity-output.json` | Independent target-identity re-derivation |
| `task31_gate_chain.py` / `task31-gate-chain-output.json` | Independent closure enumeration + full gate-chain walk with monkeypatch/restore |
| `task31_runtime_gap.py` / `task31-runtime-gap-output.json` | Independent C++/JS runtime-gap confirmation |
| `task31_frontier_scan.py` / `task31-frontier-scan-output.json` | Independent re-scan of all 82 remaining corpus programs against the live validator |
| `task-31-brief.md` | Frozen design brief |
| `task-31-frontier-audit.md` | This document |

No Git action is authorized by this package.
