# Task 30 Extrude exact bvec2 relational/reduction closure brief

## Goal and hard gate

Add exactly `filter/extrude:extrude` under identity profile
`extrude-bvec2-relational-reduction-v1`, admitting only the four-node closure
of two immediate `all(lessThanEqual(vec2, vec2))` trees in `main`. Start only
from the CURRENT accepted state (post-Task29, live-verified 2026-08-12):
**212 corpus / 129 typed / 131 public / 81 publicly unported**, typed/public
ordered-key hashes `c2561c5937ba5f11f5d2e86d729ff90b617aff738cb4de53dbf3cd8b76dbbff9`
and `2325f8d06d182800af90cd1b0b67efe9d3058d3682f0ceb4d3f5168ff4af5e16`.

**Correction to the frozen precompute:** `task30-precompute-report.md` and
`analysis.json` state the projected-after-Extrude counts as "129 / 131 / 81"
with ordinal 25. Those three numbers are stale — they describe the CURRENT
state (129/131/81, reached when Focus Blur landed after the precompute was
written), not the state after ALSO adding Extrude. Re-deriving fresh from the
live 129-typed tree (`tools/glslcpp/typed_slice.json`, corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, unchanged from the precompute)
gives the corrected projection:

**130 typed / 132 public / 80 unported**, typed ordinal **25** (unchanged —
Focus Blur sorts under `mixer/`, after Extrude's `filter/` position, so its
insertion does not shift Extrude's ordinal), neighbours unchanged
(`filter/directionalBlur:directionalBlur`, `filter/extrude:extrude`,
`filter/fibers:fibersBlend`), with corrected hashes:

- typed: `d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904`
- public: `4fe573b21a782a784b7fcacacaa276a03a395a1b8c92e83149971b8a19831056`

Both figures were independently cross-checked two ways: (1) a standalone
scratch script computed them directly from `typed_slice.json` +
`manifest.json`; (2) re-running `analyze_task30.py` unmodified against the
live tree reproduces the identical `baseline` (129/131/81, matching current
state) and `projected_extrude` (130/132/80, matching the hashes above)
figures. All other precompute values — target identity, four-node closure,
gate messages, oracle divergence counts — were independently re-verified and
found accurate (see Verification section).

## Frozen target identity

| Field | Frozen value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Source | `sources/filter/extrude/extrude.glsl` |
| Raw bytes / SHA-256 | 16,945 / `3be128643867dc78184bd209306cbe524538fd8d6d53a21817fb87f746100e29` |
| Normalized bytes / SHA-256 | 5,020 / `823698d954e1f2f890414a22e6792ca0ca87484ee21d9043cd3c1a347fd7a4ac` |
| Exact defines | `{"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0}` |
| Numeric contract | `glsl-f32` |
| Function count / tuple SHA-256 | 9 / `cb662c33d7dda0b59a63de9d9ff5e5672e18e137ad43f18f2aa1855cf29e4bb0` |
| Whole-program SHA-256 | `1e02d72c7b5c61d49462310fbbcd9f1816d0440f8716bdaaace7c2396ceb36e3` |
| Interface SHA-256 | `0e8079c94619fc0e8ad85b401a1bd51211f504c933fa963dbf9c7cdbfaec9fe7` |
| Canonical/public factory | `canonicalFactory51`, no adapter (hermetically confirmed, see below) |
| Factory text SHA-256 | `7d5cdd050eaa13282060557e7d6a097ef8300c1b71f31c13d782680eb58d91ef` |

The ordered runtime interface is `inputTex:sampler2D@1`, `resolution:vec2@2`,
`tileOffset:vec2@3`, `fullResolution:vec2@4`, `size:float@5`, `depth:float@6`,
`solidFront:bool@7`, `fragColor:vec4@8/out`. Loop proof is unchanged by this
task: effective depth 3, lexical product 9, entrypoint charge 90, acyclic
call graph — all three counted loops are already admitted; this profile adds
no loop or resource capability.

## Exact four-node closure

The only new semantic family is two immediate `all(lessThanEqual(vec2,vec2))`
trees in `main` (function ID 36), in the normalized source:

```cpp
bool topHit = all(lessThanEqual(abs(P - faceCenter), faceHalf));            // line 159
bool sideHit = (!topHit) && all(lessThanEqual(abs(P - cellC), halfCell));   // line 160
```

| Site | Path | Span | Type | SHA-256 |
| --- | --- | --- | --- | --- |
| top `all` | `(12,'s1','s8','e0',0,0)` | `159:23-159:72` | `bvec2 -> bool` | `38eea107e78da89e0f6dd529d77520ccbea907e980df5e0bbc1f01099e8c4efb` |
| top `lessThanEqual` | `(12,'s1','s8','e0',0,0,0)` | `159:27-159:71` | `vec2,vec2 -> bvec2` | `3048bc23943a393e84d677ebdf15bfc97a942a43635bb8dd95227a594a1ad9e1` |
| side `all` | `(12,'s1','s9','e0',0,0,1)` | `160:37-160:81` | `bvec2 -> bool` | `51877b40b69819a50d527eef19e642e612a9027fcdb58698e707c0818825b2bf` |
| side `lessThanEqual` | `(12,'s1','s9','e0',0,0,1,0)` | `160:41-160:80` | `vec2,vec2 -> bvec2` | `546f5c52a1a44cc20b6dda2b3fd66a38e8b6bc2f68adc2287fcfc8843d771e04` |

All four sites, spans, types, and SHA-256 values were independently
recomputed against the live corpus and match exactly. Each `all` node has
exactly one child (verified structurally, not just by inspection), and that
child is exactly the `lessThanEqual` bvec2 node at the paired path —
confirmed by walking the live typed AST and asserting `len(all.children) ==
1` and `all.children[0] is` the paired `lessThanEqual` node. `topHit` and
`sideHit` are declared `bool` (confirmed by reading normalized source lines
159-160 directly); the `bvec2` intermediate never appears as a declaration,
parameter, return type, subscript target, or stored/escaped value anywhere
else in the program (confirmed: the corpus census records exactly these two
`bvec2`-typed nodes in the whole program, both immediate `all` operands).

## Capability boundary

**Admitted — exactly these four authenticated AST nodes, nothing else:**
- the top `all(bvec2) -> bool` node at `159:23-159:72`, consuming exactly
  its one child;
- the top `lessThanEqual(vec2,vec2) -> bvec2` node at `159:27-159:71`;
- the side `all(bvec2) -> bool` node at `160:37-160:81`, consuming exactly
  its one child;
- the side `lessThanEqual(vec2,vec2) -> bvec2` node at `160:41-160:80`.

**Explicitly BANNED — must be structurally impossible to satisfy, not just
untested:**
- a generic `bvec2`, relational, or reduction capability admitted for any
  other program or any other site in this program;
- `any` (the sibling reduction builtin — confirmed absent from
  `_BUILTIN_NAMES`/`APPROVED_CAPABILITIES` today, and must stay absent
  except as a rejected oracle mutation target);
- any other comparison operator/builtin (`lessThan`, `greaterThan`,
  `greaterThanEqual`, `equal`, `notEqual`);
- `bvec3`/`bvec4` or any non-2-lane boolean vector width;
- scalar/vector mixing in the relational call (e.g. `lessThanEqual(vec2,
  float)`);
- any `bvec2` value that is declared as a local, used as a parameter or
  return type, subscripted, stored in a struct/array, or otherwise escapes
  its immediate consuming `all` call;
- widening `APPROVED_TYPES` (module-level in `generate_typed_slice.py`)
  generically to include `bvec2`. `bvec2` is not in `APPROVED_TYPES` today
  (confirmed) and must not become globally admitted — `reject_type()`
  already carries scoped exceptions for other narrow capabilities (e.g. the
  `array`-kind carve-outs keyed on `proved_array_declarations` /
  `proved_array_parameters` / `proved_array_arguments`); Extrude's `bvec2`
  exception must be added the same way, keyed on the four authenticated
  node identities from this profile, not on the type name alone.

## Independent authentication requirement

Validator and emitter must each independently re-authenticate the exact
four-node closure from the raw source, following the established per-task
profile pattern (`tools/glslcpp/frontend/<name>_profile.py`, e.g.
`focus_blur_borrowed_sampler_profile.py`, `lens_distortion_comparer_profile.py`,
`smooth_edge_luma_weights_profile.py`): an `authenticate_...` function that
reparses/reanalyzes the program from `source_hash` and proves the two `all`
nodes, their spans, their single-child relationship, and the two
`lessThanEqual` children match frozen spans/hashes/types exactly, returning a
proof object; and an `apply_...` function consumed by validator and emitter
each on their own authority. Neither side may trust the other's
authentication or a cached/forged proof — reconstructing an equal tree from
scratch must independently re-authenticate; a foreign or mutated tree
(different span, different callee, extra/missing child, wrong result type,
wrong owning function) must independently fail at both authorities.

Live-verified today (both re-confirmed by direct probe against the current
tree, not copied from the precompute):
- validator first rejects `filter/extrude:extrude:159:23: unsupported
  builtin all` (the earliest closure node it reaches);
- emitter first rejects `filter/extrude:extrude:159:27: unsupported builtin
  lessThanEqual`.

A widened-capability probe (monkeypatching `gen.APPROVED_CAPABILITIES`,
`gen._BUILTINS`, `emit._BUILTIN_NAMES`, and `emit._TYPES` inside a
`try/finally` so state is restored regardless of outcome — the same
technique as `future-precompute/analyze_candidates.py`) proves the two
authorities are independent gates:
- widening only the emitter's name/type maps still leaves the *unwidened*
  validator failing at 159:23 (`unsupported builtin all`) — the earliest
  node, confirming the emitter's admission has no effect on validator
  behavior;
- widening *both* the validator's builtin/capability set AND the emitter's
  maps to admit `all`, `lessThanEqual`, and `bvec2` as builtin/callable
  names makes the emitter render the full 14,330-byte program (SHA-256
  `27e05cfa714eeba2d0e15429792f53d490a2a8283e76bb73a2484135c5b29c08`,
  reproduced exactly), but the validator *still* independently rejects at
  `159:27: unsupported typed type bvec2` — because `reject_type()` checks
  `typ.display() not in APPROVED_TYPES` as a wholly separate gate from the
  builtin/capability list, and `bvec2` was never added to `APPROVED_TYPES`
  by that probe. This is hard proof (not inference) that builtin admission
  and type admission are two independent authorities in the validator, and
  the implementation needs an identity-scoped *type* visit (a `reject_type`
  carve-out, as described above) in addition to builtin admission — exactly
  the precompute's claim, now independently reproduced.

Both monkeypatch probes were run with explicit pre/post snapshots of all
four patched globals (`APPROVED_CAPABILITIES`, `_BUILTINS`,
`_BUILTIN_NAMES`, `_TYPES`) proving byte-identical restoration after the
`try/finally` in every case.

## C++ lowering design

`glsl::BVec2` (and `BVec3`/`BVec4`) **already exist** —
`include/noisemaker/glsl_types.hpp:240`: `using BVec2=Vec<2,bool>;` — as an
instantiation of the existing `Vec<N,T>` template also used for `IVec2` etc.
No new vector storage type is required. What does **not** exist yet and must
be added:

1. `emit._TYPES["bvec2"] = "glsl::BVec2"` (confirmed absent from
   `_BUILTIN_NAMES`/`_TYPES` today) — but only reachable via the
   identity-scoped `reject_type` carve-out above, not a bare `APPROVED_TYPES`
   addition.
2. Two free functions in `include/noisemaker/glsl_types.hpp`, following the
   existing style of `bitwise_xor`/`shift_right`/etc. (template over `N`,
   `constexpr`, lane-wise, `[[nodiscard]]`):
   - `lessThanEqual(const Vec<N,float>&, const Vec<N,float>&) ->
     Vec<N,bool>` — lane-wise `<=`. Only the `N=2` (`vec2,vec2 -> bvec2`)
     instantiation is authorized by this profile; do not add a generic
     multi-width relational family.
   - `all(const Vec<N,bool>&) -> bool` — logical AND-reduction across lanes.
     Only `N=2` (`bvec2 -> bool`) is authorized.
3. `emit._BUILTIN_NAMES["lessThanEqual"] = "lessThanEqual"` and
   `emit._BUILTIN_NAMES["all"] = "all"` (both confirmed absent today),
   admitted only inside the identity-scoped profile module, mirroring how
   `focus_blur_borrowed_sampler_profile.py` scopes its ABI admission to
   `function_parameter_type` for exact function/parameter objects rather
   than widening `_TYPES`/`function_type` generally. `all`/`lessThanEqual`
   here must similarly be admitted only for the four authenticated call
   sites (by owning-function-id + path/span match), not globally added to
   `_BUILTIN_NAMES` unconditionally for every program.
4. Do **not** add `any`, `lessThan`, or wider-lane overloads to either the
   runtime or the emitter tables as part of this task; the four
   discriminating oracle mutations below exist specifically to prove these
   are rejected.

## Test plan

### Python (structural / mutation / history)

Follow the `Task29FocusBlurBorrowedSamplerTests`-style class
(`tests/test_typed_generator.py:13251`) pattern: a
`Task30ExtrudeBvec2RelationalReductionTests(unittest.TestCase)` that:

- authenticates the exact frozen four-node closure from raw source and
  proves `authenticate_...`/`apply_...` returns the same object for an
  independently reconstructed equal tree;
- exhaustively rejects one-axis structural mutations at all three
  authorities (profile, validator, emitter), each candidate asserting its
  own structural precondition before rejection is checked — per the Task 26
  post-mortem below, candidates must be genuinely single-axis and correctly
  named, not compound or mislabeled;
- parses the *executable* C++ tables (not only an embedded JSON copy) for
  the native test's mode enum, case table, and mutation-result table, and
  runs independent tamper-sensitivity subtests against each;
- covers history/coexistence: this profile must coexist with every prior
  task's profile/capability without collision (module import + fresh
  `APPROVED_CAPABILITIES`/`APPROVED_TYPES` tuple check at
  `generate_typed_slice.py:634`).

### Native (fixture / parity)

- Execute the **seven direct relational/reduction rows** frozen in
  `extrude-oracles.json.direct_relational_cases` (equal lanes, mixed lanes,
  negative zero, large exact-integer floats, one asymmetric lane) with
  explicit mode IDs and names; reject an invalid/unhandled mode
  (fail-closed, `default` throws).
- Execute the **four discriminating public-factory mutations**, each
  replacing exactly one authenticated site, and assert their divergence
  counts against the live-verified oracle (re-run independently via
  `node extrude_oracle_generator.mjs --check`, which passed hermetically
  against the pinned CPU oracle with no drift):

  | Mutation | Hazard | Verified divergence (of 6 cases) |
  | --- | --- | --- |
  | top `all -> any` | all-reduction | **3/6** |
  | side `all -> any` | all-reduction | **2/6** |
  | top `lessThanEqual -> lessThan` | inclusive-relational | **4/6** |
  | side `lessThanEqual -> lessThan` | inclusive-relational | **2/6** |

  These match the precompute's claimed 3/6, 2/6, 4/6, 2/6 exactly — verified
  by counting `same_f32_bytes == false` rows per mutation directly from
  `extrude-oracles.json`, independent of the precompute's prose.
- Full pixel/parity gates per the standing pattern: Debug/Release
  warnings-as-errors + CTest, ASan/UBSan, all Task15-29 oracles, independent
  implementation review with zero Critical/Important.

### Required: avoid the Task 26 (Smooth Edge) vacuous mutation-harness class

`task30-precompute-report.md` names this explicitly without detail; the
concrete precedent is `task-26-implementation-review.md` finding I-1/I-2 and
its repair in `task-26-mutation-fix-report.md`. What went wrong: three of
Smooth Edge's eleven named native mutation modes (`vec4_extra`,
`helper_local_exact_f32`, `main_owned_exact_f32`) shared the *same* code path
as the unmutated baseline — the enum/switch case existed and was "tested,"
but no branch actually constructed the claimed four-lane value, the claimed
helper-local materialization, or the claimed main-owned-and-passed value.
24 of the claimed 88 mutation-result rows therefore passed by construction,
proving nothing about type, arity, or ownership. Separately, several
"one-field" negative-closure mutations were actually compound (changed two
fields at once) or mislabeled (a "parameter-owner" case that only renamed a
parameter, not reassigning ownership; "write"/"reference-escape" cases that
merely relabeled an unrelated node instead of constructing a real write or
reference escape).

**Concrete requirement this implies for Task 30:** every named native
mutation mode (`all -> any` top/side, `lessThanEqual -> lessThan` top/side,
and any additional structural/profile mutation candidates in the Python
suite) must take an explicit, structurally distinct code path — never share
a fallthrough with the baseline or with another named mode — and an
unhandled enum value must fail closed rather than silently defaulting. Every
"single-axis" mutation must change exactly the one named field/dimension it
claims to (assert the structural precondition before checking rejection);
compound or misnamed candidates are not acceptable substitutes. The
transcription/tamper tests must authenticate the *executable* C++ tables
(enum order, switch-case order, case/result tables), not only an embedded
JSON mirror, so that source tampering — not just JSON tampering — is
caught.

## Verification summary

- `analyze_task30.py` re-run against the live tree: exit code 0, output
  identical in structure to the frozen file, with `baseline` now correctly
  reporting the current 129/131/81 state and `projected_extrude` correctly
  reporting 130/132/80 (matching this brief's corrected numbers exactly).
- `node extrude_oracle_generator.mjs --check`: `extrude oracle fixture ok (6
  cases)`, exit code 0 — hermetic reproduction from the pinned CPU
  runtime/catalog/adapter, no drift from the frozen `extrude-oracles.json`.
- Four-node closure, gate messages, closure-projection render bytes/hash,
  and all four discriminating mutation divergence counts were independently
  recomputed (not copied) and match the precompute exactly.
- The only material correction found: the precompute's stated
  "projected 129/131/81, ordinal 25" for the state *after* adding Extrude is
  the CURRENT (pre-Extrude) state, made stale by Focus Blur landing first;
  corrected to 130/132/80 with new typed/public hashes above. The ordinal
  (25) and neighbours happen to be unaffected by that staleness.

No Git action is authorized by this package.
