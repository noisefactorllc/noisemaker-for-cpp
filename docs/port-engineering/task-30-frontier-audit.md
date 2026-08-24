# Task 30 fresh frontier audit: exact Extrude bvec2 relational/reduction closure

## Result

Select exactly `filter/extrude:extrude`; no known blocker. Fresh analysis of
the live post-Task29 tree (corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, unchanged) found **212 corpus /
129 typed / 131 public / 81 publicly unported** programs — confirmed directly
from `tools/glslcpp/typed_slice.json` (129 entries, includes
`mixer/focusBlur:focusBlur`, does not include `filter/extrude:extrude`) and
`tools/glslcpp/corpus/<revision>/manifest.json` (212 entries). Typed/public
ordered-key SHA-256 values are
`c2561c5937ba5f11f5d2e86d729ff90b617aff738cb4de53dbf3cd8b76dbbff9` and
`2325f8d06d182800af90cd1b0b67efe9d3058d3682f0ceb4d3f5168ff4af5e16`, matching
the accepted post-Task29 state exactly.

Adding Extrude alone projects **130 typed / 132 public / 80 unported**, typed
ordinal 25 between `filter/directionalBlur:directionalBlur` and
`filter/fibers:fibersBlend`, with ordered hashes
`d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904` and
`4fe573b21a782a784b7fcacacaa276a03a395a1b8c92e83149971b8a19831056`. See
`task-30-brief.md` for why this corrects the frozen precompute's stale
129/131/81 projection (which was computed against the pre-Focus-Blur
128-typed baseline and never re-based after Focus Blur landed).

## No newly eligible program after Focus Blur

All 83 corpus keys currently absent from the typed slice were freshly
parsed/analyzed against the live validator and emitter (re-running
`analyze_task30.py`'s `remaining` census, which recomputes this from
scratch every time, not from a cached list). Only the two already-public
manual programs (`filter/invert:inv`, `synth/solid:solid`) pass both
authorities today — identical to the precompute's `pass_rows`, and *smaller*
than before by exactly one entry: `mixer/focusBlur:focusBlur` is no longer
in the remaining set because it is now typed. No other program crossed from
"remaining" to "passes both gates" as a side effect of Focus Blur landing;
the validator-rejection histogram for the 83 remaining keys otherwise moved
only by the expected accounting shift (`"pass": 3 -> 2`, i.e. minus
Focus Blur) with every other category (dFdx, fwidth, counted-for proof,
global declaration, etc.) unchanged in count. This was confirmed by diffing
the freshly generated `remaining` block against the frozen precompute's
`remaining` block field-by-field, not by inspection alone.

Extrude (`unsupported builtin all` at validator, `unsupported builtin
lessThanEqual` at emitter) remains the only program blocked purely on a
narrow, well-scoped boolean-vector relational/reduction gap. Its closest
cousin, `filter/waves:waves`, is validator-blocked one builtin later
(`unsupported builtin any` at `41:9`) but additionally requires
`notEqual` at the emitter (`41:13`) — a materially broader builtin surface
than Extrude's `all`+`lessThanEqual` pair — so it is not a smaller or
equally-scoped next step.

## Why no batch (unchanged from precompute, re-confirmed)

| Candidate | Exact next closure | Reason to keep separate |
| --- | --- | --- |
| Watercolor Simplify | two `inout vec3` parameters, 19 `sort2` calls, copy-in/copy-out | Requires reference/value ABI, aliasing and evaluation-order proof; emitter still rejects its call statements (`only typed assignments are admitted`, live-confirmed). |
| Curl | one `tanh(vec3)`, three `mod(vec3/vec4,float)` sites | Distinct transcendental and vector-mod F32 semantics; first-gate projection still fails on vector `mod` (live-confirmed: `unsupported builtin mod overload` after admitting `tanh`). |
| Caustic | one `floatBitsToUint`, four scalar `uint ^ uint` sites | Requires bit reinterpretation plus live scalar-word semantics across many functions; validator still fails on `floatBitsToUint` (live-confirmed, unchanged). |

None shares Extrude's boolean-vector representation or relational/reduction
semantics. Batching would make review, negative closure, and pixel
attribution weaker without reducing a shared runtime change.

## Verification

- `tools/glslcpp/typed_slice.json` read directly: 129 programs, confirmed
  `mixer/focusBlur:focusBlur` present, `filter/extrude:extrude` absent.
- `analyze_task30.py` re-run unmodified against the live tree: exit 0,
  `remaining.pass_rows` == `[filter/invert:inv, synth/solid:solid]` only.
- `node extrude_oracle_generator.mjs --check`: hermetic pass, no drift.

This audit changes no repository/Git state.
