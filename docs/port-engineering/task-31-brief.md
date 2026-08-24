# Task 31 Caustic floatBitsToUint + scalar uint XOR closure brief

DESIGN ONLY. No git actions taken or authorized. No file under
`.` was read-write touched; verified
with `find . -type f -newer
docs/port-engineering/.session-start-marker -not -path
"*__pycache__*"` returning nothing, both mid-session and at the end. Every
number below was recomputed live against the current tree in this session
(scripts `task31_identity.py`, `task31_gate_chain.py`,
`task31_runtime_gap.py`, all under `docs/port-engineering/`, each with
a `.sha256` sidecar) — nothing is copied forward from the precompute report
without independent re-derivation.

## Goal and hard gate

Add exactly `classicNoisedeck/caustic:caustic` under a new identity profile
(name TBD at implementation time, e.g. `caustic-floatbits-scalar-xor-v1`),
admitting only the four-node closure inside `randomFromLatticeWithOffset`
(function id 94): one `floatBitsToUint(float) -> uint` builtin call and three
scalar `uint ^ uint -> uint` binary operators. Start only from the CURRENT
accepted state (post-Task30 Extrude, live-verified 2026-08-12): **212
corpus / 130 typed / 132 public / 80 publicly unported**, typed/public
ordered-key hashes `d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904`
and `4fe573b21a782a784b7fcacacaa276a03a395a1b8c92e83149971b8a19831056`. Both
reproduced independently in this session directly from
`tools/glslcpp/typed_slice.json` (130 program keys) plus the two hardcoded
public-only additions (`filter/invert:inv`, `synth/solid:solid`) — matches
exactly.

`python3 -m tools.glslcpp.check_corpus --check` re-run live: `check_corpus:
ok`, exit 0.

## Projection after adding Caustic — CONFIRMED, not corrected

The precompute claims **131 typed / 133 public / 79 unported**, ordinal
**0**, typed hash `0741bca3f0bd8cc577a42824cd9da480fb462f36f6e5f5ed65e92b2ad95c3060`,
public hash `64e2b0677d3e3bc70de1f34d2b389d6fb50ec7a71278676f1f65c53bab1829f5`.
Independently recomputed in this session (fresh Python: sort current 130
keys, insert `"classicNoisedeck/caustic:caustic"`, re-sort, hash; union with
the two public-only keys, re-sort, hash) reproduces every figure exactly,
with no discrepancy to correct:

| Metric | Before (live, verified) | After Caustic (recomputed here) |
| --- | --- | --- |
| Typed count | 130 | **131** |
| Public count | 132 | **133** |
| Publicly unported (212 − public) | 80 | **79** |
| Sorted typed-key SHA-256 | `d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904` | `0741bca3f0bd8cc577a42824cd9da480fb462f36f6e5f5ed65e92b2ad95c3060` |
| Sorted public-key SHA-256 | `4fe573b21a782a784b7fcacacaa276a03a395a1b8c92e83149971b8a19831056` | `64e2b0677d3e3bc70de1f34d2b389d6fb50ec7a71278676f1f65c53bab1829f5` |

Caustic's zero-based ordinal in the new sorted typed list: **0** (it becomes
the alphabetically first key — `classicNoisedeck/caustic:caustic` sorts
before `classicNoisedeck/coalesce:coalesce`, the current first entry).
Neighbours: **left = none** (new first element), **right =
`classicNoisedeck/coalesce:coalesce`**. Total corpus is 212 (confirmed:
`check_corpus.py` hardcodes and enforces exactly 212 programs; 211 `.glsl`
source files map to 212 program-key entries via one keyed-plus-one-override
split, per `check_corpus.py:194`), so unported = 212 − 133 = 79.

## Frozen target identity

All values in this table were independently recomputed in this session by
parsing `caustic.glsl` through the live pipeline (`parse_program` →
`analyze_program`) exactly as `generate_outputs()` does, then hashing with
the `_whole`/`_interface` field order copied verbatim from
`extrude_bvec2_relational_reduction_profile.py` (see
`task31_identity.py`). All match the precompute's independently-stated
values exactly, with two additions the precompute never computed (functions
tuple SHA-256, and the canonical-JS-factory identity):

| Field | Frozen value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Source | `sources/classicNoisedeck/caustic/caustic.glsl` |
| Raw bytes / SHA-256 | 15,645 / `161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d` (matches manifest `raw_sha256`) |
| Normalized bytes / SHA-256 | 7,999 / `b4a45216e62c5facade77e64925075e736ee3ed0eb7b1798bc777ba1bb714b83` |
| Exact defines | `{"NOISE_TYPE": 10}` |
| Numeric contract | `glsl-f32` |
| Function count / functions-tuple SHA-256 | 22 / `43a0063cf16ebea820084302df1d6c59594485b559267597ad30ac3cddc659a3` (newly derived; not stated by the precompute) |
| Whole-program SHA-256 | `b0ffb30caee0d301f54d42892a6e70619fd4cf1e4c19d5fc3f399b3bfc598624` |
| Interface SHA-256 | `094c31b573c08cfdf9e3c76e766c4b4ca96a2df12d6a1629f18b141624464b50` |
| Loop proof `(count, unproved, max_depth, max_lexical_product, entrypoint_charge, acyclic)` | `(0, 0, 0, 0, 0, True)` — **zero loops** anywhere in the reachable graph |
| Resources `(uniforms, samplers, outputs, uses_texture, uses_derivatives)` | 11 uniforms (`time, seed, wrap, resolution, tileOffset, fullResolution, noiseScale, speed, hueRotation, hueRange, intensity`); `()` samplers; `("fragColor",)` outputs; `False, False` |
| Canonical/public factory | `canonicalFactory1` in `noisemaker-for-cpu/src/effects/generated/canonical-kernels.js`, **no adapter** (hermetically confirmed below) |
| Factory text SHA-256 | `27beaa017be557b5960bd072d74247896e596fa0b71b5c331c7795f5732a7488` (Node v24.7.0, `canonicalKernelFactories["classicNoisedeck/caustic:caustic"].toString()`, 19,435 chars) |

**No-adapter confirmation** (newly derived; the precompute never checked
this for Caustic): live-querying `canonicalKernelFactories` in
`noisemaker-for-cpu` under Node v24.7.0 shows exactly one key maps to
`canonicalFactory1` — `classicNoisedeck/caustic:caustic` — and there is no
`caustic`-specific file in `noisemaker-for-cpu/src/effects/adapters/`
(`bit-effects.js, crt.js, f32-color.js, fractal.js, index.js, julia.js,
median.js, palette.js, snow.js` — none reference `caustic`). This is a
genuinely hermetic 1:1 mapping, exactly like Extrude's `canonicalFactory51`,
even though `canonicalFactory1`'s own JS source still reads
`$bindings["NOISE_TYPE"]` at runtime (the same shared multi-variant
`caustic.glsl` source compiles several `#if NOISE_TYPE == N` "classic
noisedeck" interpolation modes into one factory; only the
`NOISE_TYPE == 10` branch is registered as this corpus program's frozen
identity — see the Oracle Requirements section for why this matters for
oracle-case eligibility).

**Byte-count caveat:** unlike the hash fields above, no whole-program *byte
count* of a rendered C++ program is part of the frozen identity in this
brief. Both this session's diagnostic full-render (33,165 bytes,
`76e0d8ab80c63660b2e602a083ff5d255eba482dddecc3b6bc91e7024c5880d9`) and the
precompute's own diagnostic full-render (33,146 bytes) used arbitrary
placeholder runtime-function names for the not-yet-designed `floatBitsToUint`
lowering; the two numbers differ only because the placeholder names differ
in length, not because of any semantic difference in what renders. Neither
number should be treated as a frozen target — only the raw/normalized/
whole/interface source hashes above are.

## Exact four-node closure

All four nodes live inside exactly one function, `randomFromLatticeWithOffset`
(id 94, span `164:1-208:2`), confirmed by an exhaustive whole-program scan of
all 22 functions (`task31_gate_chain.py::collect_closure`) that finds
**exactly** 1 `floatBitsToUint` site and **exactly** 3 scalar `uint ^ uint`
sites anywhere in the program — nothing more, nothing in any other function.
Raw-source excerpt (`caustic.glsl:218-229`, raw numbering — differs from the
in-pipeline spans below purely because of preprocessor normalization, exactly
as the precompute noted, confirmed here by direct re-execution rather than
assumed):

```glsl
uint xBits = uint(xi);
uint yBits = uint(yi);
uint seedBits = uint(seed);
uint fracBits = floatBitsToUint(seedFrac);

uvec3 jitter = uvec3(
    (fracBits * 374761393u) ^ 0x9E3779B9u,
    (fracBits * 668265263u) ^ 0x7F4A7C15u,
    (fracBits * 2246822519u) ^ 0x94D049B4u
);

uvec3 state = uvec3(xBits, yBits, seedBits) ^ jitter;   // already-legal uvec3^uvec3 — NOT in this closure
```

| Node | Span (in-pipeline) | Kind/operator | Result type | Child types | Parent kind | Node SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `floatBitsToUint` | `192:21-192:46` | builtin call | `uint` | `[float]` | `declaration` (of `fracBits`) | `e6b86baf243b38741b4870acfe990ce3b353f18948d38773cc853ab11ce3b6a4` |
| scalar `^` #1 | `195:10-195:46` | binary `^` | `uint` | `[uint, uint]` | `construct` (the `uvec3(...)` building `jitter`) | `0ec45e30c890d1177375332f93564f8d12d8bd47805393740503edd290617445` |
| scalar `^` #2 | `196:10-196:46` | binary `^` | `uint` | `[uint, uint]` | `construct` (same `uvec3(...)`) | `7f98e820b388d74eb98c8296f798d778d63d6bdb8d67e68f9bfae73f74e56e4e` |
| scalar `^` #3 | `197:10-197:47` | binary `^` | `uint` | `[uint, uint]` | `construct` (same `uvec3(...)`) | `791b232712de5fe1a3babde2e00799603fbb523421973f9b20888f12e978b8ee` |

All three scalar-XOR nodes share one ancestry statement — the single `decl`
at `194:5-198:7` (the `uvec3 jitter = uvec3(...)` declaration) — and one
common parent, the `uvec3(...)` constructor call at that declaration. The
`floatBitsToUint` node's sole ancestry statement is the separate `decl` at
`192:5-192:47` (`uint fracBits = floatBitsToUint(seedFrac);`).

**The trailing `uvec3(xBits,yBits,seedBits) ^ jitter` at raw line 229
(in-pipeline `200:19-200:57`) is already legal today** — vector
`uvec3 ^ uvec3` is covered by the existing `uint-vector-bitwise` capability
(already 1 of the 44 entries) and is **not** part of this closure. Confirmed
live: it is the only other `^` site in the whole program, both its operand
types are `uvec3`, and its span/hash were captured separately from the four
closure nodes above.

**No-escape proof for `fracBits`:** its declaring symbol (id 144, type
`uint`) is referenced exactly 3 times anywhere in the function body — each
time as the left operand of a scalar `uint * uint` multiply
(`fracBits * 374761393u` etc.) that is itself the left child of one of the
three closure XOR nodes. It is never returned, stored into an array,
subscripted, passed as a function argument, or otherwise escapes scalar-uint
shape. (The `uint * uint` multiplies feeding the XORs are **not** part of
this closure and need no new gate — scalar `*` between two `uint` operands
does not hit any of the special-cased binary-operator branches in
`generate_typed_slice.py`'s `expression()` walk — `%`, `>>`, `^`, and
matrix-`*` are the only special cases — so it falls through to the generic
`used.add("scalar-vector-arithmetic")` path, already one of the 44 approved
capabilities. Live-confirmed: the gate-chain probe's step 0/1 blockers never
mention the multiplies at all.)

## Capability boundary

**Admitted — exactly these four authenticated AST nodes, nothing else:**
- the `floatBitsToUint(float) -> uint` call at `192:21-192:46`, owned by
  `randomFromLatticeWithOffset`;
- the three scalar `uint ^ uint -> uint` binary nodes at `195:10-195:46`,
  `196:10-196:46`, `197:10-197:47`, same owning function, all three children
  of the same `uvec3(...)` constructor.

**Explicitly BANNED — must be structurally impossible, not merely
untested:**
- a generic `floatBitsToUint` capability admitted for any other program or
  site — it must remain absent from `_BUILTINS`/`APPROVED_CAPABILITIES`
  (`generate_typed_slice.py`) and from `_BUILTIN_NAMES`
  (`emit_typed_cpp.py`), exactly like `all`/`lessThanEqual` stayed absent
  after Task 30 (confirmed: `task-30-implementation-report.md` "Boundary
  verification" table shows the 44-entry vocabulary unchanged post-Extrude);
- `uintBitsToFloat` — confirmed absent from both headers today and must not
  be admitted by this profile (Caustic never calls it; live-confirmed by the
  whole-program scan finding zero sites);
- any generic scalar `uint`-arithmetic-to-bit-pattern reinterpretation
  outside the one authenticated `floatBitsToUint` call;
- widening the *existing* Perlin scalar-XOR mechanism to accept a second
  program key. `authenticate_perlin_scalar_uint_xor` is hard-gated on
  `typed.key != PERLIN_KEY` at two call sites
  (`generate_typed_slice.py:1463`, `emit_typed_cpp.py:264`/`282`) and cannot
  serve two different `typed.key` values without either changing `PERLIN_KEY`
  itself (forbidden — it would silently widen what Perlin's frozen profile
  accepts) or adding a **second, parallel** kwarg/profile module scoped to
  `classicNoisedeck/caustic:caustic` only. Caustic's four nodes must never
  become authorizable through Perlin's `perlin_scalar_uint_xor_profile`
  kwarg;
- any `uint ^ uint` site outside the three authenticated nodes in
  `randomFromLatticeWithOffset` — including the already-legal
  `uvec3 ^ uvec3` at `200:19-200:57`, which must keep going through the
  *general* vector-XOR path (`used.add("uint-vector-bitwise")`), not the
  identity-scoped scalar path, so a foreign vector-XOR site can never
  masquerade as an authenticated scalar site;
- `float_to_uint32`/`glsl::detail::float_to_uint32` must never be used to
  implement `floatBitsToUint` — the two have similar names but incompatible
  semantics (conversion/truncation vs. bit-reinterpretation); see the C++
  Lowering section.

## Design constraint: does this need a capability-vocabulary change?

**No — for either half, if and only if both follow the existing
identity-scoped skip pattern.** `src/typed_generated/typed_manifest.json`
records the full 44-entry global capability vocabulary identically in every
one of the 130 program rows today (confirmed live:
`all(p["capabilities"] == programs[0]["capabilities"] for p in programs)` is
`True`, `len(capabilities) == 44`, and `"uint-vector-bitwise"` is already one
of the 44). Adding a 45th entry would change all 130 rows and invalidate the
frozen historical-reconstruction hashes for Tasks 27/28/29/30 — the exact
mistake the Task 30 postmortem flags.

**Scalar `uint ^ uint` — mechanism already exists, reuse as template only.**
The binary-operator branch at `generate_typed_slice.py:1932-1944` already
special-cases scalar XOR: if the node is one of the caller-supplied
`authorized_perlin_scalar_uint_xors` (checked by object identity), it
validates `(uint, uint, uint)` typing and **does not** call
`used.add("uint-vector-bitwise")` — it is a pure identity gate with zero
vocabulary cost. The parallel emitter branch
(`emit_typed_cpp.py:1191-1200`) emits a bare native `(left ^ right)` — no
`glsl::bitwise_xor()` call. **Live-confirmed reachable-code proof, not
inference:** Task 27's already-shipped, already-committed
`src/typed_generated/typed_slice.cpp` contains this exact emission at the
Perlin `hash3()` function: `((glsl::swizzle<0>(q) ^ glsl::swizzle<1>(q)) ^
glsl::swizzle<2>(q))` — a bare operator on two `std::uint32_t` lane values,
with zero runtime helper call (`task31_runtime_gap.py` locates this line
programmatically and confirms it contains `^` but not `glsl::bitwise_xor`,
while the *vector* XOR two lines earlier in the same function,
`q = glsl::bitwise_xor(q, glsl::shift_right(q, std::uint32_t(16)))`, does
call the helper — proving the two lowerings are genuinely different code
paths, not an artifact of my reading). This is **directly reusable
verbatim** for Caustic's three scalar XOR sites: no new C++ runtime function,
just the native `^` operator.

However — **the exact `perlin_scalar_uint_xor_profile` kwarg cannot be
reused for Caustic**, confirmed by direct execution, not just reading:
monkeypatching `authenticate_perlin_scalar_uint_xor` and driving
`validate_capabilities(..., perlin_scalar_uint_xor_profile=<diagnostic>)`
against the Caustic program still raises `"Perlin scalar uint XOR profile
metadata mismatch"` at the very first check
(`typed.key != PERLIN_KEY`, `generate_typed_slice.py:1463`) *before* the
authenticate function is ever called — patching the authenticate function
alone is not enough, because the guard is a separate, earlier, hardcoded
`typed.key` check. The probe only got past this by ALSO monkeypatching the
module-level `PERLIN_KEY` binding itself to equal Caustic's key — which is
explicitly not a legitimate design (it would silently let Caustic through
Perlin's frozen gate). **Conclusion, precise version of the precompute's
"~100% template / 0% data" claim:** the correct design is a **new, parallel**
kwarg (e.g. `caustic_scalar_uint_xor_profile: str | None = None`) and a new
profile module (`caustic_scalar_uint_xor_profile.py`), built by copying
`perlin_scalar_uint_xor_profile.py`'s structure (same `_whole`/`_interface`
helpers, same `authenticate_.../apply_...` signature shape, same "collect
every site in the whole program and assert count/identity/ancestry"
strategy) but with entirely fresh hashes/spans/function-ids/call-graph data,
wired into `generate_typed_slice.py`/`emit_typed_cpp.py` alongside (not
instead of) Perlin's existing kwarg, following the exact insertion pattern
Extrude used for its own kwarg (new dataclass field, new `if ... is not
None:` block in both `validate_capabilities` and `_Emitter.__init__`, new
entries in `load_slice()`'s per-key expected-shape dispatch and hardcoded
singleton-list checks, new manifest key entry).

**One further difference from Perlin worth flagging:** Perlin's two scalar
XORs are provably **unreachable** dead code — `authenticate_perlin_scalar_uint_xor`'s
own call-graph proof shows `hash3` (function id 49) is outside the reachable
set from the program's actual entry point under `DIMENSIONS=2` (reachable =
`(45,46,48,50,51,52,53,54,55,56)`, excluded = `(47,49,57)`). Caustic's three
scalar XORs are **live, reachable, rendered code** — `randomFromLatticeWithOffset`
is called from `constant()`/`constantOffset()`, which the `#if NOISE_TYPE ==
10` branch of `noise()` calls directly, and the live full-render probe below
executes this path. This means Caustic's native test plan needs actual
value-level parity coverage (fixture rows that exercise the XOR path with
real bit patterns), not just structural/type authentication — Perlin's
profile never needed a native fixture at all, since the code it authenticates
never runs.

**`floatBitsToUint` — no existing skip mechanism; must be added, following
Extrude's `all`/`lessThanEqual` shape, not Perlin's or `round`'s.** There is
no existing single-builtin identity-scoped exemption analogous to what
Caustic needs, other than the three names already special-cased at
`generate_typed_slice.py:1954-1966` (`round`, `all`, `lessThanEqual`) and
`emit_typed_cpp.py:1291-1311`. Of those:
- `round` is the **wrong template**. Its emitter handling
  (`emit_typed_cpp.py:1106-1112`) never emits `round` as a builtin call at
  all — it is folded into its authorized *parent* node
  (`int(round(x))` → `glsl::detail::float_to_int32(glsl::round(x))`) at the
  point where the parent is visited, and the ordinary
  `value.callee == "round"` branch inside the builtin dispatch
  unconditionally raises (`emit_typed_cpp.py:1291-1292`) — meaning any
  `round()` node that reaches that dispatch directly (i.e., was **not**
  consumed by its authorized parent) fails loud. `round` is eliminated by
  folding, never independently lowered.
- `all`/`lessThanEqual` (Task 30's own pattern) **is the right template**:
  each is admitted by identity inside the ordinary `value.kind == "builtin"`
  dispatch (`generate_typed_slice.py:1957-1966`,
  `emit_typed_cpp.py:1293-1311`) and then genuinely lowered to a real
  runtime call (`glsl::all(...)`, `glsl::lessThanEqual(...)`) — exactly the
  shape `floatBitsToUint(seedFrac) -> glsl::float_bits_to_uint(seedFrac)`
  needs, since there is no elimination-by-folding transform available for a
  bit-reinterpret operation.

**Live proof that the naive path (generically widening `_BUILTINS`) breaks
the vocabulary invariant, exactly as the constraint warns.** This session's
`task31_gate_chain.py` monkeypatched `gen._BUILTINS |= {"floatBitsToUint"}`
(the crude, wrong-by-design admission an implementer might reach for by
analogy with an ordinary builtin) and reran `validate_capabilities` with
`APPROVED_CAPABILITIES` deliberately left unwidened. Result: the validator
gets past the `195:10: unsupported binary operator ^` gate (once scalar XOR
is also admitted) but then fails at the very last check in the function —
`missing = used - set(capabilities); if missing: raise ...`
(`generate_typed_slice.py:2181`) — with **`missing capabilities
floatBitsToUint`**. This is hard, reproduced evidence (not a hypothesis)
that naively widening `_BUILTINS`/`_BUILTIN_NAMES` is insufficient/unsafe:
it silently adds `"floatBitsToUint"` to `used` (via the fallthrough at
`generate_typed_slice.py:1981-1982`, `if value.callee not in {"round", "all",
"lessThanEqual"}: used.add(value.callee)`), and the validator correctly
refuses to ship a program whose declared capability list doesn't match. The
**only** clean fix is to extend that same exempt tuple to include
`"floatBitsToUint"` (guarded, like `all`/`lessThanEqual`, by an identity
check against the one authenticated node) — at which point
`floatBitsToUint` never enters `used`, and no capability-vocabulary change
is needed at all, exactly like the scalar-XOR half. Interestingly, the
matching naive widening of the **emitter's** `_BUILTIN_NAMES` produces no
equivalent failure (the emitter has no "declared vocabulary" bookkeeping),
which is itself worth noting: the 44-entry-vocabulary invariant is enforced
*only* by the validator's final `missing = used - set(capabilities)` check,
so the identity-scoped-admission design is what makes both authorities agree
independently — an emitter that silently accepts a naively-widened builtin
while the validator (correctly) rejects it would otherwise be a divergent-
authority bug of exactly the kind this codebase's "one report once, fail
loud" discipline forbids.

**Concrete implementation shape (design only — nothing here is code to
apply):**
- `generate_typed_slice.py`: add `elif value.callee == "floatBitsToUint":`
  immediately alongside the existing `elif value.callee in {"all",
  "lessThanEqual"}:` block (`~line 1957`), checking identity against a new
  `authorized_caustic_floatbits` single-node tuple; extend the exempt set at
  `~line 1981` to `{"round", "all", "lessThanEqual", "floatBitsToUint"}` (or
  equivalent, scoped so only the identity-authorized node is exempt — the
  `all`/`lessThanEqual` branch already demonstrates the pattern: check
  identity, and only exempt from `used.add` if authorized, else still raise).
- `emit_typed_cpp.py`: add a parallel `elif value.callee == "floatBitsToUint":`
  branch beside the existing `elif value.callee in {"all",
  "lessThanEqual"}:` (`~line 1293`), checking identity against the same
  authenticated node and returning `f"glsl::float_bits_to_uint({arguments[0]})"`.
  `floatBitsToUint` must stay absent from `_BUILTIN_NAMES`.
- `load_slice()`'s hardcoded per-key expected-field-set dispatch
  (`generate_typed_slice.py:665-684`) and hardcoded singleton-list checks
  (`~lines 710-727`) need a new `caustic_..._profile`-shaped branch, exactly
  mirroring Extrude's own insertion in Task 30, plus the `len(keys) != 130`
  / `d31014f5...` literals bumped to 131 / `0741bca3...`.

## Independent authentication at both authorities

Following the established per-task pattern (`authenticate_...`/`apply_...`
pair, each authority re-authenticating from `source_hash` rather than
trusting a cached proof — see `extrude_bvec2_relational_reduction_profile.py`
and `perlin_scalar_uint_xor_profile.py`), the new
`caustic_floatbits_scalar_xor_profile.py` (or two separate modules — one per
half, since they are structurally distinct: one builtin-identity node, three
binary-operator-identity nodes) must:
- reparse/reanalyze the program from `source_hash`, proving raw/normalized
  bytes+hash, exact defines (`{"NOISE_TYPE": 10}`), function count (22),
  whole/interface hashes, and loop proof `(0,0,0,0,0,True)` match exactly;
- locate the one `floatBitsToUint` node and the three scalar `^` nodes by
  walking the **whole program**, asserting cardinality exactly 4, span,
  type, parent kind, and per-node SHA-256 for each, and that no additional
  site of either kind exists anywhere;
- return only candidate-owned exact objects (never a boolean or a
  reconstructed-but-unequal tree) so validator and emitter each independently
  re-derive and compare by object identity, per this codebase's established
  non-negotiable pattern.

Live-verified today (both re-confirmed by direct probe against the current
tree in this session, not copied from the precompute):
- validator's first rejection: `classicNoisedeck/caustic:caustic:192:21:
  unsupported builtin floatBitsToUint`;
- emitter's first rejection: `classicNoisedeck/caustic:caustic:192:21:
  unsupported builtin floatBitsToUint` (validator and emitter **agree** on
  the first blocker here — unlike Curl/Lighting in the precompute's
  three-candidate comparison, where validator/emitter disagreed).

## Gate-chain confirmation

Full second-order chain, re-walked live with monkeypatch/restore
(`task31_gate_chain.py`), pre/post snapshots of every patched global
(`gen._BUILTINS`, `gen.APPROVED_CAPABILITIES`, `emit._BUILTIN_NAMES`,
`gen.PERLIN_KEY`, `emit.PERLIN_KEY`) proving byte-identical restoration in
every case (`monkeypatch_restoration_verified: true`, plus the
step-0 blocker reproduced identically after restore):

| Step | Patch applied | Validator | Emitter |
| --- | --- | --- | --- |
| 0 | none | `192:21: unsupported builtin floatBitsToUint` | `192:21: unsupported builtin floatBitsToUint` |
| 1 | admit `floatBitsToUint` (diagnostic, naive `_BUILTINS` widening — NOT the recommended design) | `195:10: unsupported binary operator ^` | `195:10: unsupported binary operator ^` |
| 2 | + admit scalar `^` (diagnostic, generalizing the real `authenticate_perlin_scalar_uint_xor` mechanism to the 3 real Caustic nodes) | `missing capabilities floatBitsToUint` (see Design Constraint section — an artifact of step 1's naive admission, not a genuine third gate) | **PASS** (33,165-byte full render) |

**No third gate exists.** The emitter reaches a complete, successful render
after exactly the same two admissions the precompute claimed
(`floatBitsToUint`, then scalar `^`), and the validator's step-2 failure is
fully explained and load-bearing evidence for the Design Constraint section
above (naive `_BUILTINS` widening breaks the capability-vocabulary
invariant), not evidence of additional program complexity. A validator that
instead followed the identity-scoped skip pattern for `floatBitsToUint`
(exactly like it already does for `all`/`lessThanEqual`) would not have hit
this failure, but reproducing that cleanly requires editing the hardcoded
exempt-tuple literals in the source file, which this read-only design brief
cannot and must not do.

## C++ lowering design

**`floatBitsToUint` — genuinely new, ~1-2 lines, confirmed absent from both
runtime headers today** (`task31_runtime_gap.py`: absent from
`include/noisemaker/glsl_types.hpp` and `include/noisemaker/glsl_runtime.hpp`).
The JS canonical reference (`noisemaker-for-cpu/src/csl/glsl-runtime.js:411-414`)
reinterprets bits via a shared `Float32Array`/`Uint32Array` buffer alias:
`this.bitsFloat[0] = value; return this.bitsUint[0]`, live-confirmed
(`js_floatBitsToUint_uses_shared_typed_array_alias: true`,
`js_bitsFloat_is_Float32Array: true`, `js_bitsUint_is_Uint32Array: true`).
Because that JS path assigns into a **Float32Array** slot first — rounding
the JS double to float32 before the uint32 bits are read — the C++ lowering
must **narrow to `float` before bit-casting**, not bit-cast the raw `double`
storage directly (sizes wouldn't even match — `std::bit_cast` requires equal
object sizes). Recommended addition to `include/noisemaker/glsl_types.hpp`,
matching the header-only `constexpr` free-function style already used for
`bitwise_xor`/`shift_right`/`integer_mod`:

```cpp
[[nodiscard]] constexpr std::uint32_t float_bits_to_uint(double value) noexcept {
  return std::bit_cast<std::uint32_t>(static_cast<float>(value));
}
```

**Do not confuse this with the already-existing `float_to_uint32`.**
`glsl::detail::float_to_uint32(double)` (declared `glsl_types.hpp:17`,
implemented `src/glsl_runtime.cpp:10-15`) already exists and is used
extensively (7 call sites in the committed `typed_slice.cpp`) — but it
implements GLSL's `uint(floatValue)` **conversion** semantics (truncate
toward zero, wrap modulo 2^32, `NaN`/non-finite → 0), confirmed by reading
its body live (`fmod`/`trunc`-based, no `bit_cast` anywhere in it). It must
**not** be reused for `floatBitsToUint`, which is a bit-pattern
reinterpretation with completely different results for the same input (e.g.
`floatBitsToUint(1.5)` reinterprets the IEEE-754 bit pattern of `1.5f`
— `0x3FC00000` — while `float_to_uint32(1.5)` converts to the integer value
`1`).

**Scalar `uint ^ uint` — zero new runtime code, reuse verbatim.** As shown
above, Task 27's committed `typed_slice.cpp` already proves the emission
shape: a bare native `^` on two `std::uint32_t` values, no helper function.
Caustic's three sites lower identically:
`(fracBits_expr * 374761393u) ^ 0x9E3779B9u` etc. emit as ordinary C++
`(left ^ right)`, with `fracBits`'s multiply-by-constant expressions
themselves already covered by the generic `scalar-vector-arithmetic`
capability (no special handling needed there either).

## Test plan

### Python (structural / mutation / history)

A `Task31CausticFloatBitsScalarXorTests(unittest.TestCase)` class following
the `Task30ExtrudeBvec2RelationalReductionTests`
(`tests/test_typed_generator.py:14231`) /
`Task27PerlinTests` (`tests/test_typed_generator.py:12072`) pattern:

- authenticate the exact frozen four-node closure from raw source; prove
  `authenticate_.../apply_...` returns the same objects for an independently
  reconstructed equal tree, and rejects a foreign program
  (e.g. `synth/perlin:perlin`, which also has scalar XOR nodes — the
  single best adversarial-mutation candidate, since it's structurally
  similar but a different program) at both authorities;
- exhaustive single-axis structural mutations at all three authorities
  (profile, validator, emitter): `floatBitsToUint` → some other builtin;
  scalar `^` → `|`/`&`/`>>`; operand-type drift (`float`→`double`-labelled,
  `uint`→`int`); wrong owning function; wrong parent (a scalar XOR moved
  outside the `uvec3(...)` constructor); each candidate must assert its own
  single-field precondition before checking rejection (per the Task 26
  post-mortem requirement below — **not optional** here);
- coexistence: this profile must coexist with all 130+1 prior profiles
  without collision — module import plus a fresh
  `APPROVED_CAPABILITIES`/`APPROVED_TYPES` tuple check
  (`generate_typed_slice.py:634`-adjacent) proving the 44-entry vocabulary is
  unchanged after this task lands (a hard assertion, not a spot check);
- byte-for-byte reconstruction of the prior state (Task 30's 130-typed tree)
  from history, matching the established regression-proof pattern.

### Required: avoid the Task 26 (Smooth Edge) vacuous mutation-harness class

Per the operator's explicit instruction, this MUST be carried forward
verbatim as a hard requirement, not a suggestion. Task 26 shipped native
mutation modes that silently shared the baseline code path — the enum/switch
case existed and was "tested," but no branch actually constructed the
claimed divergent value, so a fraction of the claimed mutation-result rows
passed by construction, proving nothing. **Concrete requirement for Task
31:** every named native mutation mode (there will likely be at minimum:
`floatBitsToUint` swapped for an unrelated builtin; each of the 3 scalar XOR
sites individually swapped for `|`/`&`; a foreign-program probe) must take an
explicit, structurally distinct code path — never share a fallthrough with
the baseline or with another named mode, proven the same way Task 30 proved
it: a semantic signature payload derived only from **observed behavior**
(computed `jitter`/`state`/`prngState` values, call counters), explicitly
**excluding** mode id, mode name, and any one-hot dispatch array, so pairwise
uniqueness is genuine evidence of distinct code paths rather than aliasing.
An unhandled enum value must fail closed (no `default` arm silently
succeeding).

### Required: avoid the Task 30 coarse-hash-absorption gap

Per the operator's explicit instruction, this MUST also be carried forward
as a hard requirement. Task 30's mutation test was absorbed entirely by the
coarse whole-program hash gate — the novel node-level authentication logic
(the four-node identity checks) went completely unexercised, because any
tampering was already caught by the much blunter whole-program SHA-256 check
firing first, so the test suite never actually proved the node-level checks
do anything. **Concrete requirement for Task 31:** the test suite must
**re-freeze the coarse hashes first** (raw/normalized/whole/interface,
functions-tuple) as fixed, separately-asserted constants, and then run the
node-level mutation battery **on a tree that already matches every coarse
hash** (i.e., the mutation must alter only in-memory node identity/kind/
type/parent — not source bytes — so the coarse SHA-256 gates cannot possibly
fire first). Each node-level rejection test must assert the exact
node-level error message (e.g. `"scalar XOR site mismatch"`,
`"floatBitsToUint owning function mismatch"` — real messages TBD at
implementation time, but must be program-specific, not the generic
`"source, define, function, whole-program, or interface mismatch"` message
that the coarse gate raises) — asserting the coarse message where a
node-level message is expected is itself a test bug this suite must not
repeat.

### Native (fixture / parity)

Unlike Perlin's scalar XOR (dead code — never needed a native fixture at
all, since `hash3()` is unreachable under `DIMENSIONS=2`), **Caustic's
closure is live, reachable, rendered code** — `randomFromLatticeWithOffset`
executes on every pixel of the default `NOISE_TYPE=10` render. This is the
single biggest structural difference from the Perlin precedent and drives a
materially different test-plan weight:

- direct fixture rows exercising `randomFromLatticeWithOffset` (or the
  smallest wrapping public call, `constant()`/`constantOffset()`) across a
  range of `seed`/`s` (the float feeding `seedFrac`/`fracBits`) values
  chosen to exercise interesting `floatBitsToUint` bit patterns: `0.0`,
  negative zero, a value with a simple bit pattern, a value near a float32
  rounding boundary (since the JS reference rounds to float32 before
  reinterpreting — an oracle case at a value that rounds differently to
  float32 than the naive double bit pattern would catch a lowering bug that
  skips the `float` narrowing step);
  and exact expected `jitter`/`state`/`prngState` bit-level outputs;
- explicit truth-table coverage for the new `float_bits_to_uint` free
  function in isolation (not just through the full kernel): known IEEE-754
  bit patterns, `+0.0`/`-0.0` (which have different bit patterns despite
  comparing equal), `NaN` (multiple valid bit patterns — pin exactly which
  one the reference/implementation produce, or explicitly document
  divergence risk if `Math.fround`/JS `NaN` canonicalization differs from
  C++ `static_cast<float>` on a `NaN` double — flag this as a design risk
  needing operator sign-off rather than silently assuming parity, since GLSL
  `NaN` bit-pattern behavior is implementation-defined and the JS/C++ paths
  may legitimately diverge here);
- discriminating mutations (mirroring Extrude's four-row divergence table):
  swap `floatBitsToUint` for a differently-shaped conversion; swap one
  scalar XOR's operand order; corrupt one magic constant — each verified
  against the live-verified oracle's own divergence count (not assumed);
- full pixel/parity gates per the standing pattern: Debug/Release
  warnings-as-errors + CTest, ASan/UBSan (worth calling out specifically for
  `std::bit_cast` correctness, though `bit_cast` is UB-free by design when
  used correctly — the risk is in the `static_cast<double> -> float`
  narrowing path elsewhere in the kernel, already exercised by every other
  task), all Task15-30 oracles, independent implementation review with zero
  Critical/Important findings.

## Oracle requirements

Following the Task 30 lesson explicitly: **the JS oracle generator must not
assume every generated case is native-bindable.** Caustic's authorized
define map, frozen by this profile, is exactly `{"NOISE_TYPE": 10}` — a
single value, not a range. This is a genuinely sharper eligibility risk than
Extrude's (which had two 2-valued defines, `DEPTH_SOURCE`/`EXTRUDE_TYPE`,
still only one pinned combo): Caustic's `metadata.json` entry
(`classicNoisedeck/caustic`) exposes a UI-facing `interp` parameter whose
`"choices"` (`constant=0, linear=1, hermite=2, catmullRom3x3=3,
catmullRom4x4=4, bSpline3x3=5, bSpline4x4=6, simplex=10, sine=11`) map
**directly onto the same `NOISE_TYPE` compile-time `#define`** that this
profile's typed slice pins at `10`. The raw `caustic.glsl` source literally
contains `#if NOISE_TYPE == 0`, `== 3`, `== 4`, `== 5`, `== 6`, `== 10`,
`== 11` branches (confirmed live via direct grep) — meaning at *runtime*, a
user (or a naively-written oracle generator that cycles through `interp`
choices for broader "coverage") can select a different `NOISE_TYPE`, and the
JS canonical factory (`canonicalFactory1`) will compile and execute a
**completely different `#if` branch** than the one this profile
authenticates. **Any oracle case whose effective `NOISE_TYPE` define is not
exactly `10` must be marked explicitly ineligible for native binding** —
its C++-side comparison target simply doesn't exist, since the typed/emitted
program only ever lowers the `NOISE_TYPE == 10` branch. `wrap`, `seed`, and
all other `classicNoisedeck/caustic` parameters are ordinary runtime
uniforms (not compile-time defines) and may vary freely across oracle cases
without an eligibility concern — including `wrap`, which the metadata UI
hides for `interp ∈ {10, 11}` but the shader itself still reads
unconditionally at `caustic.glsl:206` (`if (wrap) { ... }`), so oracle cases
should still vary it for coverage even though the UI wouldn't normally
expose it at `NOISE_TYPE=10`.

The oracle JSON (`tests/oracles/task-31-oracles.json`, not produced by this
design-only brief — it is an implementation artifact, generated by a
one-off `*_oracle_generator.mjs` script the implementer writes, following
the pattern of the (now-absent, evidently ephemeral) `extrude_oracle_generator.mjs`
referenced by Task 30) must freeze, per the established provenance shape
(`tests/oracles/task-30-oracles.json`'s `provenance` block):
- `canonical_kernels_sha256`, `public_catalog_sha256` (if applicable —
  Extrude's oracle recorded one; confirm during implementation whether a
  distinct "public catalog" layer applies to `classicNoisedeck` family
  effects or whether `canonicalKernelFactories` is itself the public
  surface for this key, since no `public-catalog.js`-named file was found
  in this session's search of `noisemaker-for-cpu/src/effects/generated/`);
- `adapter_index_sha256` / `adapter_absent: true` — confirmed true this
  session (no `caustic`-specific adapter file exists);
- `source_sha256` = `161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d`;
- `canonical_factory_name` = `"canonicalFactory1"`;
- `canonical_factory_to_string_sha256` — **must be recomputed live at
  implementation time**, not copied from this brief's
  `27beaa017be557b5960bd072d74247896e596fa0b71b5c331c7795f5732a7488`, since
  the source-of-truth is whatever `noisemaker-for-cpu` contains at the exact
  commit the implementation pins (this brief's value is only a same-session
  spot-check, not a durable pin — `noisemaker-for-cpu` is a separate repo
  outside this design brief's frozen scope);
- `node` version used to run the generator;
- `public_identity: true` (given `adapter_absent: true` above);
- exact closure counts (`floatBitsToUint_sites: 1`, `scalar_uint_xor_sites: 3`);
- explicit `defines: {"NOISE_TYPE": 10}` per case, and an explicit
  `eligible_for_native: bool` (or equivalent) field per case so a future
  implementer cannot accidentally bind an ineligible case, mirroring the
  "3 of 6 eligible" split Task 30 shipped.

## Verification summary

- `check_corpus --check`: `check_corpus: ok`, exit 0 (live, this session).
- Post-Task-30 baseline (130/132/80, hashes `d31014f5...`/`4fe573b2...`)
  reproduced live directly from `tools/glslcpp/typed_slice.json` — matches
  the manifest's own hardcoded `load_slice()` literal exactly.
  Post-Caustic projection (131/133/79, hashes `0741bca3...`/`64e2b067...`,
  ordinal 0, neighbours none/`classicNoisedeck/coalesce:coalesce`)
  independently recomputed and matches the precompute exactly — no
  correction needed anywhere in the projection.
- Target identity (raw/normalized bytes+hash, defines, function count,
  whole/interface hashes, loop proof, resources) independently recomputed
  from the live pipeline and matches the precompute's stated values exactly,
  plus two new values the precompute never stated (functions-tuple SHA-256;
  canonical-JS-factory identity, hermetic no-adapter confirmation, and
  factory-text SHA-256).
- Exact four-node closure (1 `floatBitsToUint` + 3 scalar `^`) independently
  recomputed via a whole-program AST scan (not just the two illustrative
  sites the precompute quoted) — cardinality, spans, types, parent kinds,
  SHA-256 all match; no fifth site exists anywhere.
- Gate chain independently re-walked with monkeypatch/restore: step 0 and
  step 1 blockers match the precompute exactly; step 2 achieves a full
  33,165-byte render at the emitter (precompute: 33,146 bytes — both
  diagnostic-only, neither a frozen quantity, difference fully explained by
  differing placeholder names). **No third gate — confirmed independently,
  not merely re-asserted.**
- New, precompute-independent finding: the naive `_BUILTINS`-widening
  admission path for `floatBitsToUint` is live-proven to break the
  capability-vocabulary invariant (`missing capabilities floatBitsToUint`),
  which is the concrete evidence for why the identity-scoped skip pattern
  (mirroring `all`/`lessThanEqual`, not `round`) is structurally mandatory,
  not merely recommended, for this task.
- New, precompute-independent finding: `perlin_scalar_uint_xor_profile`'s
  kwarg is hard-locked to `PERLIN_KEY` at two call sites and cannot be
  reused directly for Caustic — a new, parallel kwarg/module is required,
  sharpening the precompute's "0% reusable as data" claim into a precise
  code-level reason.
- New, precompute-independent finding: `floatBitsToUint`'s correct
  structural template is Extrude's `all`/`lessThanEqual` pattern (real
  lowering), not `round`'s (elimination-by-folding) — the precompute did not
  address this distinction.
- New, precompute-independent finding: `float_to_uint32` already exists but
  implements incompatible (conversion, not bit-reinterpretation) semantics
  and must not be reused.
- New, precompute-independent finding: Caustic's shared multi-variant
  `caustic.glsl` source creates a `NOISE_TYPE`/`interp` define-eligibility
  risk for oracle generation, directly analogous to (and sharper than)
  Extrude's `DEPTH_SOURCE`/`EXTRUDE_TYPE` eligibility split from the Task 30
  postmortem.
- New, precompute-independent finding: Caustic's scalar-XOR closure is live,
  reachable, rendered code (unlike Perlin's, which is dead code) — this
  changes the native test plan's weight materially, requiring real
  value-level fixture parity rather than structural authentication alone.

No Git action is authorized by this package.

---

## Addendum: design-review repairs (integration owner, 2026-08-12)

The independent design review
(`task-31-design-review.md`) returned **ACCEPT with one blocking item**. Both
substantive findings are resolved below; implementation may begin.

### CRITICAL (resolved) — ordinal-0 blast radius

The brief stated "Caustic → ordinal 0" as a bare fact without planning for its
consequence: Caustic sorts before every other typed key, so all 130 existing
`typed_N` namespaces shift by +1. This is a full-corpus renumbering, strictly
larger than Task 30's tail-only shift.

A complete, measured plan now exists:
**`task-31-ordinal-blast-radius.md`**
(`522e3b5d4094c4b5979a66bc8751677b4893985fd58a51ed2c5cf0185c66a659`).

Key conclusions:

- **Frozen historical hashes are SAFE.** Reconstruction removes Caustic first,
  restoring ordinals 0..129 exactly as today, so the frozen Task 28/29/30
  outputs still reproduce byte-for-byte. This must be asserted explicitly with
  a "removing only Caustic regenerates the accepted Task 30 outputs
  byte-for-byte" test, matching the 28→29 and 29→30 precedents.
- **13 live assertion sites must be updated**, all mechanical: 3 explicit
  ordinal index assertions (`77`→78 smooth, `111`→112 focus, `25`→26 extrude),
  9 `namespace typed_NN` string assertions, and 1 embedded binder source
  string (`typed_53::State` → `typed_54`). The blast-radius document lists each
  with its current line and new value.
- **Native tests need no ordinal work** — no hardcoded `typed_NN` exists in
  `tests/test_generated_kernels.cpp` or `tests/test_typed_slice.cpp`; native
  binding is by public key and factory name, both ordinal-independent.
- **Do not loosen these assertions to regex-normalized ordinals.** They are
  deliberately exact and pin which namespace each program occupies.
  Normalization is correct only in the reconstruction tests, which already do
  it at `tests/test_typed_generator.py:1504-1508`.

### IMPORTANT (resolved) — `floatBitsToUint` needs NO new runtime code

The brief called the C++ lowering "genuinely new" and flagged NaN bit-pattern
parity as an open risk requiring operator sign-off. Both are unnecessary.

`noisemaker::float_bits_to_uint(float)` **already exists** and has exactly the
required bit-reinterpretation semantics:

```cpp
// src/numeric.cpp:50-52
std::uint32_t float_bits_to_uint(float value) noexcept {
  return std::bit_cast<std::uint32_t>(value);
}
```

- declared at `include/noisemaker/numeric.hpp:15`;
- already reachable from the emitted code — `glsl_types.hpp:11` includes
  `noisemaker/numeric.hpp`;
- already covered by dedicated tests at `tests/test_numeric.cpp:28-35`,
  including `+0.0`, `-0.0` (`0x80000000`), `1.0`, infinity, and round-trips
  through `uint_bits_to_float`.

The NaN-parity concern is therefore closed: `std::bit_cast` preserves the exact
payload, and the round-trip tests already pin it.

**Delegate to the existing function. Do not add a new one.** Both the
precompute and this brief missed it by grepping the camelCase GLSL spelling
(`floatBitsToUint`) in `glsl_types.hpp`/`glsl_runtime.hpp` only, rather than
the snake_case C++ spelling across the whole include tree.

**Net effect: Task 31 requires no new C++ runtime code at all.** Scalar
`uint ^ uint` already emits a bare native `^` (verified in Task 27's committed
output), and `floatBitsToUint` delegates to an existing, tested function. The
entire task is generator wiring plus tests.

### The `float_to_uint32` trap still stands

`float_to_uint32` (`src/glsl_runtime.cpp:10-16`) implements GLSL **numeric
conversion** — truncate, then wrap mod 2^32 — and must never be used for
`floatBitsToUint`. Measured divergence:

| value | `float_to_uint32` | `float_bits_to_uint` |
|---:|---:|---:|
| 1.5 | 1 | 1069547520 |
| 0.25 | 0 | 1048576000 |
| 123.456 | 123 | 1123477881 |
| -2.0 | 4294967294 | 3221225472 |

Confusing them compiles, runs, and silently produces wrong pixels.

### Minor / Nit — no action

Oracle `public_catalog_sha256` applicability is self-disclosed and low
severity; the `round`-versus-tuple terminology inconsistency in the
implementation-shape section does not affect the contract.
