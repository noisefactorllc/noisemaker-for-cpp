# cellRefract186 — mutable uninitialized global `float[9]` arrays

Design for porting `classicNoisedeck/cellRefract:cellRefract` as typed row 186.
Status: **DESIGN — reviewed GO, pre-implementation** (frozen verdict in
`cellrefract-design-review.md`; its four Important findings are already
folded in as Amendments §§11-14). Sections 1-10 are the reviewed text;
numbered amendments appended during implementation are authoritative over them
where they conflict, per the standing convention in
`NEXT_CODING_AGENT_HANDOFF.md`.

Mechanism family: **mutable-uninitialized-global array**, the sub-shape
`REMAINING-EFFECTS.md` recommends next. `kaleido` and `effects` carry the same
byte-identical `float emboss[9];` declaration and follow once this lands
(`kaleido` additionally wires its already-frozen `scalar-uint-xor-v1`; `effects`
additionally needs `mat4` and must not be planned with them).

## 1. Frozen authority

Every figure below was measured this session against the pinned corpus by the
same helpers `mutable_global_frame_profile.py` uses (never hand-transcribed;
re-derive when amending).

| Fact | Value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Source | `…/sources/classicNoisedeck/cellRefract/cellRefract.glsl` |
| Raw bytes / SHA-256 | 13,719 / `aa93167faa07ee22ff0be9c653b5602ac88b1b962e405548cafab43b9e867a70` |
| Normalized bytes / SHA-256 | 10,221 / `31cce61e01275d44d46556bfc13edeea4383dcfbcfde024fd7c54a624933bd3c` |
| Defines (default, canonical) | `KERNEL=0`, `SHAPE=1` |
| Whole-program SHA-256 | `10049e9bc2ce8fc9539ea315335eef85fff59d1cfbe0844a3d781b0d496aec28` |
| Interface SHA-256 | `09c626e4a6923f856dac399e76972de809ccc8efeb3d49c59d5f69eb8ed17352` |
| Node census | 1,670 nodes / 173 assigns |
| Functions | 22 |
| Declarations | 21 (uniforms + `out` + five arrays) |

Live RED boundary, reproduced by this session's probe against the committed
185-row slice: `32:1 unsupported global declaration` — the `float emboss[9];`
line. The pre-normalized source comments (`cellRefract.glsl:12-22`) document
SHAPE/KERNEL as compile-time injected defines.

### The five admitted declarations

Normalized lines 32-36, contiguous ordinals 16-20, symbol ids 17-21, all
`array` of `float` extent 9, all UNINITIALIZED:

| Ordinal | Symbol id | Name | Span (line:col) |
| ---: | ---: | --- | --- |
| 16 | 17 | `emboss` | 32:1-32:17 |
| 17 | 18 | `sharpen` | 33:1-33:18 |
| 18 | 19 | `blur` | 34:1-34:15 |
| 19 | 20 | `edge` | 35:1-35:15 |
| 20 | 21 | `edge2` | 36:1-36:16 |

### Function inventory (normalized)

22 functions, ids 64-85. Load-bearing ones:

- `loadKernels` — id 70, `void`, **no parameters**, lines 38-64. The writer.
- `convolve` — id 66, lines 66-99, parameter 2 is `kernel` symbol 23,
  `array<float, 9>` at `66:29-66:44`. This is the predicted second blocker
  (`66:29 unsupported typed type float[9]`), confirmed by the normalMap-era
  probe and consistent with gate order.
- `convolutionKernel` — id 65, lines 279-281: **collapsed to `return color;`**
  by the frozen `KERNEL=0`.
- `main` — id 71, lines 378-410: the `#if KERNEL != 0` block is stripped.
- Callers of `convolve` with whole local tables: `derivatives` (67), `outline`
  (73), `shadow` (81), `sobel` (84) — each declares two local `float[9]`
  tables with 9 literal stores (8 caller tables total).

Call graph (16 edges) and reachability, measured:

- **Reachable**: `main`(71), `loadKernels`(70), `cells`(64), `map`(72),
  `pcg`(74), `prng`(79), `smin`(83).
- **Unreachable**: the other 15, including `convolve`, all four local-table
  callers, `convolutionKernel`, `pixellate`, `posterize`, `hsv2rgb`,
  `rgb2hsv`, `desaturate`, `periodicFunction`, `polarShape`, `shapeDistance`,
  `wrapEdges`.

**Consequence that shapes the whole slice:** at the frozen defines the five
globals are **write-only** — their only readers (`convolutionKernel`'s
branches) were stripped by normalization. Every `kernel[i]` read, every
whole-array call argument, and the `float[9]` parameter lives in
unreachable-but-emitted code. The array machinery must still be admitted and
must still compile, but no oracle case at default defines can discriminate any
mutation of the tables' contents. See §7.

## 2. JavaScript materialization (the authority)

Measured against the sibling `noisemaker-for-cpu` checkout, factory
`canonicalFactory3` in `src/effects/generated/canonical-kernels.js:1144-1645`,
registered at line 36183 as `"classicNoisedeck/cellRefract:cellRefract"`.

1. **The five globals are factory-scope plain JS arrays of doubles** —
   `canonical-kernels.js:1172-1176`, `var emboss = [0,0,0,0,0,0,0,0,0];` etc.
   Allocated once per factory invocation (`bindGlslKernel`,
   `glsl-runtime.js:549-556`), captured by closure, shared across pixels.
   **Not** `PooledFloat32Array` — therefore immune to the `beginPixel`
   scratch-aliasing hazard (`glsl-runtime.js:121-133`) that governs
   `const-global-nine-table-v1`'s element allowlist. The pool-safety argument
   of normalMap §15 does not constrain this mechanism, but its lesson does:
   materialization is decided per declaration, and here it is *plain Number*.
2. **Numeric contract**: elements are doubles, never narrowed on read or
   write. All 45 constants are small integers exactly representable in
   binary32, so the double contract is *structurally* locked but not
   *pixel-discriminable* (the normalMap §12 "unfalsifiable contract" case —
   lock it structurally and say so).
3. **`loadKernels` is a real closure function** (`:1177-1223`) called once per
   pixel from `main` (`:1608`), re-writing all 45 elements before any possible
   read. The rewrite is idempotent (constants), so factory-scope persistence
   is unobservable; per-pixel re-execution is the observable contract.
4. **`convolve`'s `kernel` parameter is by-reference, no copy** (`:1224-1248`)
   — unlike vec parameters, which get `$runtime.copy`. `kernel[i]` reads are
   un-narrowed doubles. `conv` accumulates in a `PooledFloat32Array` with
   per-store f32 rounding; `kernelWeight` is a bare double.
5. **Defines are runtime bindings in the JS** (`:1154-1155`): the branch tree
   is retained and dispatched at runtime. The *corpus GLSL* is
   preprocessor-conditional and our normalizer strips it at `KERNEL=0` — the
   divergence is the same authority question Shapes resolved: the frozen
   corpus row pins defines `{KERNEL: 0, SHAPE: 1}`, and the port's obligation
   is the normalized corpus semantics at those defines, with the JS oracle run
   at matching binding values (`KERNEL=0` bound at runtime reproduces "block
   skipped").
6. **No re-initialization between pixels**: nothing zeroes the arrays between
   `loadKernels` calls; since `loadKernels` fully overwrites before any read,
   first-pixel zero-init is also unobservable. The port may value-initialize
   per pixel without divergence.

## 3. Mechanism decomposition

Four mechanisms, two new, two extensions of paid-for precedent:

| # | Mechanism | Status |
| --- | --- | --- |
| A | Mutable uninitialized global `float[9]` declaration admission (×5) | **new** — `mutable-global-nine-array-cellrefract-v1` |
| B | Non-`main` writer function (`loadKernels`, 45 literal element stores) | **new** — part of A's state proof; emission-side `Frame&` |
| C | `float[9]` parameter + local literal tables + whole-array call args | **extension** — per-key record in `fixed_array_in_parameter_proof.py` |
| D | Loop admission (`cells`'s nested `-2..<=2`, `convolve`'s `0..<9`) | **anticipated** — likely a new `runtime_loop_bound` key (Shapes precedent); RED probe confirms during implementation |

### A + B: the new profile module

New file `tools/glslcpp/frontend/mutable_global_array_profile.py`, dict-keyed
shared module exactly in the pattern of `mutable_global_frame_profile.py`
(which was built dict-keyed for precisely this follow-on; its Amendment 2
hazards are addressed below). Capability `mutable-global-nine-array-cellrefract-v1`,
row field `mutable_global_array_profile`.

`_LOCKS[key]` freezes (each lock an individually deletable predicate; value
checks ordered **ahead of** node identity per the `Symbol` self-absorption
trap):

- Source identity: raw/normalized bytes+SHA-256, caller `source_hash`, defines
  tuple `(("KERNEL","int","0"),("SHAPE","int","1"))`, whole/interface
  fingerprints.
- Inventory: 21 declarations (names, ordinals, symbol ids), 22 functions
  (id/name/param tuples), resources (1 sampler `inputTex`, 14 scalar/vector
  uniforms, 1 output, texture reads, no derivatives), call graph (16 edges,
  exact edge tuple), reachability pair, counted-loop proofs, node census
  (1670/173).
- The five admitted arrays by symbol identity: ordinal, id, name, span, type
  `array<float,9>`, storage mutable, `initializer is None`, per-name numeric
  contract (`double`, `narrowing="none"`, JS initial `0`), declaration/symbol
  node hashes, ordinal adjacency (16-20 contiguous, immediately after
  `fragColor` at 15).
- **Writer proof**: exactly one writer function `loadKernels` (id 70, void,
  0 params); write census exactly 45 stores, all `assign` with operator `=`,
  all bases `id` in {17..21}, all indices literal `0..8`, all values literal
  floats (freeze the 45 (base, index, value) triples exactly — they are the
  program's kernel tables); no indirect/partial/compound/unary/post writes
  anywhere in the program targeting the five symbols; no reads of the five
  symbols anywhere (write-only at frozen defines — freeze this; a read
  appearing means defines drifted or the mechanism is being reused beyond its
  proof).
- **Call dominance**: `main` calls `loadKernels` exactly once, at a frozen
  top-level statement index, before every statement containing a `cells`/`map`
  call (the only consumers of state that could observably order against it);
  `loadKernels` is called by no other function; the call is the statement
  `loadKernels();` with no arguments and void context.
- **Frame contract** (emission): struct `Frame` with five `Kernel9` members in
  ordinal order; instance `frame`; scope `pixel`; value-initialized;
  `writer_function="loadKernels"` taking `Frame&` at parameter ordinal 2;
  every other helper takes `const Frame&` at ordinal 2 (Shapes' frozen
  contract, minus its `writer_function="main"`).
- Visitation ledger over consumed nodes (declarations, stores, call) with a
  frozen count; every authenticated node consumed exactly once.

**Amendment-2 hazards from the shape slice, both addressed here by design:**
(1) there are no `out`/`inout` parameters in this program — census them and
freeze the census empty, so the unmodeled mutation path cannot sneak in later
without failing a lock; (2) `_fail` prefixes come from a per-key profile name,
not a module-global, so failures name `mutable-global-nine-array-cellrefract-v1`.

**What deliberately does *not* generalize:** the write-only census and the
single-writer-`loadKernels` dominance are properties of `KERNEL=0`. A future
row with `KERNEL != 0` (or `kaleido`, whose reads live in reachable code) needs
its own record with its own read census and read-position proof. The module
must not carry a "reads allowed" switch.

### C: per-key record in `fixed_array_in_parameter_proof.py`

The module currently hard-freezes `refract` (symbol 19, induction 54, census
`(1,3,35,32,27,3,30,2,2)`). Refactor to dict-keyed `PROFILES`/`KEYS` with two
records; **refract's record and dataclass must remain byte-identical in
behavior** (its tests and the historical reconstruction pin it). The
cellRefract record `cellrefract-convolve-v1` freezes:

- `convolve` id 66, parameter symbol 23 (`kernel`, ordinal 1, `float[9]`,
  direction `in`, native ABI `const Kernel9&`), induction symbol = the loop's
  `i`, exactly 2 induction-indexed parameter reads per iteration
  (`kernel[i]` in the product and the weight tally).
- The 8 caller tables (4 functions × 2) with names, symbol ids, 9 literal
  stores each, and their whole-array call arguments; plus `convolve`'s own
  `vec2 offset[9]` table (9 `vec2` stores, induction reads).
- Whole-program censuses recomputed for this program (array declarations,
  identifiers, literal stores, induction reads, index expressions, whole
  arguments, array calls) — the numbers differ from refract's and are frozen
  per key.
- Unreachability recorded, not rejected: the proof vouches grammar, not
  liveness. (Refract's callers are reachable; cellRefract's are not. The
  emitter emits both.)

### D: loop admission

`cells` carries nested `for (int y = -2; y <= 2; y++)` × `for (int x …)` and
`convolve` the `0..<9` loop. Shapes (same family, `synth/shape`) needed
`runtime_loop_bound_profile`; expect a `runtime-loop-bound-cellrefract-v1` key.
The RED probe during implementation confirms the exact requirement and the
exact first rejection once A-C are admitted; if no loop gate fires, drop D and
record why in an amendment.

## 4. Emission contract

Namespace `typed_N` (N = the row's generated ordinal) gains, in order:

1. `using Kernel9 = std::array<double, 9>;` and
   `using Offsets9 = std::array<glsl::Vec2, 9>;` with the existing
   `static_assert(sizeof(...) == 72U)` pair — identical to refract's emitted
   aliases (they are per-namespace; no collision).
2. `struct Frame final { Kernel9 emboss{}; Kernel9 sharpen{}; Kernel9 blur{}; Kernel9 edge{}; Kernel9 edge2{}; };`
   — member order = declaration ordinals 16-20; value-initialization
   reproduces the JS factory-scope zeros (unobservable, but exact).
3. `loadKernels([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, Frame& frame) noexcept`
   — the **only** non-const frame parameter in the namespace; body is the 45
   stores `frame.emboss[0] = static_cast<float>(-2.0);` etc. (literal form
   follows the emitter's existing store lowering for local tables — refract's
   `deriv_x[k] = static_cast<float>(…)`).
4. Every other helper gains `[[maybe_unused]] const Frame& frame` at ordinal
   2 (Shapes' `_emitter_bound_parameters` pattern). `convolve` and the
   local-table helpers compile unchanged from the refract shape: `const
   Kernel9& kernel` param, `Kernel9 deriv_x{}` locals, whole-array arguments.
   In frozen-`KERNEL=0` reality none of them is called from `pixel`.
5. `pixel` declares `Frame frame{};` immediately after the state preamble and
   lowers `loadKernels();` to `loadKernels(state, context, frame);` at its
   frozen statement position. Symbol mapping `17..21 → frame.<name>` in the
   expression emitter.
6. Final audit: exactly one `Frame` type, one instance, one non-const frame
   parameter (on the writer), writer called exactly once from `pixel`, and
   every admitted symbol referenced (here: written) at least once.

`aspectRatio` is a `#define` macro over `fullResolution.x / fullResolution.y`
and stays expression-level lowering — it is **not** one of Shape's mutable
globals; do not widen `mutable-global-frame-shape-v1`.

## 5. Slice row and projected censuses

Insert in sorted position (`classicNoisedeck/cellNoise:cellNoise` <
`classicNoisedeck/cellRefract:cellRefract` < `classicNoisedeck/colorLab` …;
check exact neighbors at insertion time):

```json
{
  "defines": {"KERNEL": 0, "SHAPE": 1},
  "mutable_global_array_profile": "mutable-global-nine-array-cellrefract-v1",
  "program_key": "classicNoisedeck/cellRefract:cellRefract"
}
```

(D adds `"runtime_loop_bound_profile": "runtime-loop-bound-cellrefract-v1"`
if the probe demands it.)

Projected: 186 typed rows; 188 catalog entries; corpus keys absent 26;
genuinely unported 25; mutable-global-array carrier count 1. Compute the new
typed-list SHA-256 and the four artifact hashes from the generator output —
never project them by hand (method-correction rule). Budget for the **native
catalog census** too: `factories.size()` assertions move 186 → 187.

## 6. Proof composition (RED/GREEN)

Both authorities (`generate_typed_slice.py` validator,
`emit_typed_cpp.py` emitter) independently call the authenticator, admit the
five declarations **by object identity** into a set separate from const
`admitted_globals`, and consume the profile nodes exactly once. Admission by
identity, never by re-matching.

RED sequence (write tests first, watch each fail for the intended reason):

1. Row absent: `32:1 unsupported global declaration` (live boundary).
2. Row present, carrier absent: `exact mutable-global array profile carrier
   required` at both authorities.
3. Foreign carrier (`mutable-global-frame-shape-v1`, `const-global-nine-table-v1`,
   every sibling profile field): rejected with the cellRefract message at
   whichever authority owns the row — and per the collision-chain trap, sweep
   **all** sibling profile strings and record which neighbours answer first;
   claim only the rows actually tested.
4. Per-lock mutations (value checks before identity; refreeze surrounding
   hashes to the mutant and assert the coarse/identity messages did *not*
   fire): wrong raw/normalized hash, defines drift (`KERNEL=1` re-normalizes —
   record what changes), inventory ±1 declaration/function, each of the five
   symbols renamed/retyped/initialized/moved, 44/46 stores, a store with
   non-literal index, a store with non-literal value, a compound write, a
   second caller of `loadKernels`, call moved after `cells`, a read of any
   array inserted, `Frame&` relaxation on a non-writer, non-value-initialized
   Frame.
5. Delete-the-check sweep: one predicate at a time from the module source in
   a scratch copy; every deletion must turn at least one named test red;
   tabulate. Sub-clause granularity: where a predicate is an `or`-chain of
   redundant sub-clauses, delete sub-clauses and test **pairs** of
   individually-green deletions together.
6. Sabotage test for the visitation ledger.
7. `fixed_array_in_parameter_proof`: refract record unchanged (its existing
   tests stay green, byte-identical proof object); cellRefract record
   mutations mirror its own lock list; auto-attach proves None for every
   other corpus program (census test over the full corpus).

## 7. Oracle design

`cellrefract_oracle_generator.mjs` in `docs/port-engineering/cellrefract-parity/`,
in the shape/normalMap pattern: `--cpu-root` required and realpath'd; refuse
the live checkout, containment either way, and inside-C++-repo roots; per-file
SHA-256 import closure; the six pinned CPU-file hashes; factory identity
`kernelFactories.get(key) === canonicalKernelFactories[key]`; factory name
exactly `canonicalFactory3`; `Function.prototype.toString` SHA-256 frozen at
generation; both adapter tables censused (`canonicalAdapterFactories` must not
own the key; `check_corpus._ADAPTERS` parsed from live source must not contain
it); GLSL bytes/SHA pinned; stable path placeholder, absolute-path rejection.

Cases (each full float32-word + RGBA8 arrays, stored once, materialized into
`tests/oracles/cellrefract186_expected.inc` via a Python materializer with
field/duplicate/truncation/sidecar checks):

- `cells-wrap-mirror` / `cells-wrap-repeat` — the two `wrap` arms, distinct
  seeds/speeds so `cells`, `smin`, `prng`, and the refraction displacement all
  execute and differ between cases.
- `cells-extreme-variation` — drives `cellSmooth`/`variation` arms including
  the `k == 0.0` smin branch.
- `tile-crop-translation` — full route vs tile route with
  `tileOffset=(crop_x, full_h-crop_y-tile_h)`, compared exactly (Shapes'
  amended crop contract).
- `kernel-zero-invariance` — one-axis control: binding `KERNEL` is a runtime
  JS binding; run one case at `KERNEL=0` (the frozen define) and record the
  axis with a liveness census (the port has no `KERNEL` binding at all; the
  axis asserts the *absence* of a divergence channel, per Shapes §11).

**Mutants — satisfiability and distinguishability checked before budgeting**
(normalMap §11/§12 lessons): the five tables are write-only at frozen defines,
so **no table mutant is pixel-discriminable**; their protection is structural
(§6) and the acceptance record must say so plainly. Discriminating mutants
instead target the reachable path and must be verified bit-differing on at
least one case before being budgeted; candidates (verify, don't assume):
`smin-h-quadratic-dropped` (affects smooth-min cells), `prng-pcg-round-stepped`
(pcg constant perturbed), `aspect-ratio-inverted` (affects `cells` scaling),
`wrap-arm-swapped`. Non-reaching control: a `KERNEL != 0` branch mutant
(reaching only via stripped code) must be **invariant** everywhere — that
invariance is itself a witness that defines stripping matched the JS runtime
skip.

ABI: 15 bindings — `seed` and `wrap` int32, `time`, `scale`, `cellScale`,
`cellSmooth`, `variation`, `speed`, `refractAmt`, `direction`, `effectWidth`
via `get_number`, `resolution`/`tileOffset`/`fullResolution` `Vec2`, `inputTex`
texture. Omit-each and wrong-variant-each with `KernelBindingError` naming the
binding; unrelated extras ignored and behavior-neutral; caller vector/binding
immutability; exact alpha; deterministic repeatability; independent output
storage.

## 8. Verification gates

The standing matrix, unchanged from §6 of the handoff: four generator gates;
focused then full Python (module-count-asserting scratch runner, 19+1 modules);
native Debug/Release/ASan+UBSan (zero warnings with
`-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`; no LSan claim on Apple);
ctest 1/1; assembly audit ARM64+x86_64 with demangled symbol resolution and
per-architecture patterns; historical reconstruction 186 → 185 (remove only
cellRefract from a deep-copied live spec, regenerate in memory, recover the
four pre-cellRefract artifact hashes, surviving blocks byte-identical modulo
`typed_N` ordinals — sanity-check the block splitter on the unchanged
185-pair first); storage manifest/cleanup with one owned run root.

Assembly notes specific to this slice: the pixel path at frozen defines is
`pixel` + inlined `cells`/`prng`/`pcg`/`smin`/`map` + `loadKernels` — audit
that set; `convolve` and the local-table helpers are **out of pixel scope**
(dead code may still be emitted — record instruction counts but scope the
no-indirect-branch/no-fused-FP/no-allocation claims to executed scope, and
prove fused-FP absence TU-wide). `loadKernels`'s 45 stores are the frame
writes — expect them inlined into `pixel`; no heap, no static storage for
`Frame` (stack-only, like Shapes' 16-byte Frame).

## 9. Risks and expected discoveries

- **Deeper validator gates behind array admission are unprobed.** The
  normalMap-era probe stopped at `66:29`. Gate order may surface further
  rejections (indexed-write audit, whole-array-argument grammar, `uvec3`
  componentwise ops in `pcg`, `distance()`, `mod()` on vec2, the `?:`
  chains in `hsv2hsv`-family unreachable code, counted-loop proofs for
  `cells`). Each discovery is an amendment, not a redesign, unless it demands
  a new capability beyond D — then stop and re-review per the standing rule.
- `Symbol` span self-absorption, whole-program-census blind spot in global
  initializers (n/a here — no initializers), and the collision-chain
  unreachability trap all apply; §6 embeds the countermeasures.
- `kaleido`/`effects` reuse: this design freezes write-only/read-census-empty
  locks that those programs will *not* satisfy (their reads are reachable).
  Their records will extend the read side; do not loosen this one to
  accommodate them.

## 10. Ownership for parallel execution

- **Worker A** (profile): `tests/test_mutable_global_array.py`,
  `tools/glslcpp/frontend/mutable_global_array_profile.py`.
- **Worker B** (integration): `tests/test_typed_generator.py`,
  `generate_typed_slice.py`, `emit_typed_cpp.py`,
  `fixed_array_in_parameter_proof.py` + its tests, `typed_slice.json`,
  generated artifacts.
- **Worker C** (oracle/native): `cellrefract_oracle_generator.mjs`,
  `cellrefract-oracles.json`, oracle include + materializer + sidecars,
  `tests/test_generated_kernels.cpp`, `tests/test_numeric.cpp`.
- Serialization: Worker B integrates A's interface only after A's tests are
  stable; the shared run root and pre/post manifests per the standing storage
  rules.

## Amendments

Independent design review (frozen as `cellrefract-design-review.md`, verdict
**GO**) reproduced every §1-§2 fact by re-derivation and found four Important
corrections. Each is authoritative over the section it amends.

### §11 — amends §5: the native census figure was hand-transcribed wrong

The live assertion is `REQUIRE(factories.size() == 187U)` at
`tests/test_generated_kernels.cpp:249`; it moves **187 → 188** (the slice is
185 rows + 2 hardcoded dual-registrations today, so 186 rows → 188 entries).
§5's "186 → 187" copied the *previous* slice's correction out of the handoff
— the exact transcription trap the method-corrections list bans, committed in
the very paragraph citing that rule. Never carry a census forward by
arithmetic; read the assertion.

### §12 — amends §4.5 and §6: the emitter cannot lower `loadKernels();` today

`main`'s call is a bare `expr` statement wrapping a `call` node, and the
emitter's expr-statement grammar admits only assignments plus two special
cases and one identity-gated `inout`-vec3-swap call arm
(`emit_typed_cpp.py:4409-4417`, `only typed assignments are admitted`). The
validator has no such gate, so this surfaces **only on the emitter side**
after A-C are admitted — the documented wcSimplify pattern
(`REMAINING-EFFECTS.md` §"Recommended order" item 3). Implementation adds a
new identity-authenticated bare-call-statement arm for exactly the frozen
`loadKernels();` call node (mirroring the inout-swap arm's identity gating),
with its own RED test. No generic void-call admission.

### §13 — amends §3A/§3C: two hard-wired integration sites must change

1. `generate_typed_slice.py:3652-3686` — the fixed-array proof recomputation
   chain is `if typed.key == REFRACT_KEY: … elif typed.fixed_array_in_parameter_proof
   is not None: raise "malformed fixed-array input-parameter proof key"`. The
   refactored auto-attach will attach a cellRefract proof and the validator
   will raise that error unless a new arm recomputes and registers the
   `proved_array_declarations`/`proved_array_parameters`/`proved_array_arguments`
   sets for cellRefract's tables.
2. `mutable_global_frame_profile.py:158-163` + `:1111-1113` — the template
   module's `_OPTIONAL_PROOF_FIELDS` names `fixed_array_in_parameter_proof`
   and rejects any carrier whose program carries it, and
   `attach_fixed_array_in_parameter_proof` runs unconditionally before
   validation (`generate_typed_slice.py:5018`). A wholesale copy of the
   pattern fails on the authentic program: the new module must **allow** that
   field (and freeze exactly which sibling proofs are absent, which is a
   stronger lock than the template's).

### §14 — amends §3A's writer lock: "all values literal floats" is unsatisfiable

19 of the 45 store values are `unary(-)` nodes wrapping a literal (GLSL
negative constants parse as unary-minus-of-literal), not `literal` nodes. The
(base, index, value) triple freeze must extract values literal-or-unary-minus-
of-literal, exactly as `_number()` in `fixed_array_in_parameter_proof.py:143-153`
already does. §6's mutation "a store with non-literal value" means: a value
node that is neither form.

### Minor corrections (no section renumbered)

- §5's right-hand sorted neighbor is **`classicNoisedeck/coalesce:coalesce`**
  (insertion index 2 in `typed_slice.json`), not `colorLab` — `colorLab` is
  unported and not in the slice at all.
- §3D is almost certainly dead weight: all three loops carry complete counted
  proofs (loop count 3, unproved 0, effective depth 2, lexical product 25 —
  well inside `COUNTED_FOR_V1_MAX_*`, `loop_proof.py:38-40`), and ported
  `cellNoise` has an identical loop profile with no loop carrier. Expect the
  drop-path to fire; budget accordingly.
- Line-citation drift: `beginPixel` starts at `glsl-runtime.js:132` (the
  `indices.fill(0)` is line 133); the factory's closing brace is line 1646.
- Numbering: the landing is typed **row 186**, but the generated namespace is
  **`typed_2`** (sorted insertion index 2; existing namespaces shift +1).
  Keep the two schemes explicitly labeled in tests and the acceptance record;
  the §8 reconstruction normalizes exactly these ordinals.

### §15 — RETRACTS §7's crop case: the Shapes tile-crop identity does NOT hold for cellRefract

Measured by the oracle lane (2026-08-17), mechanism proven by instrumented
probes before recording: with the Shapes crop contract
(`tileOffset=(crop_x, full_h-crop_y-tile_h)`, tile-sized `resolution`,
full-sized `fullResolution`), the tile output is **not** the top-down crop of
the full-route output — `tile-crop-translation` differs in **70/96 float
words and 70/96 RGBA8 bytes** (first mismatch tile `0x3f000000` vs full
`0x3f200000`). The mechanism: the cells distance field `d` **is**
world-aligned (0/96 mismatches on a `d`-only probe), but
`localUV = (st*fullResolution − tileOffset)/textureSize` collapses back to
destination-local coordinates (0/48 localUV lanes equal between routes),
and the two routes sample *different input textures* — tile-sized on the tile
route, full-sized on the full route — through a world-aligned warp. The
Shapes identity held because that program's warp path did not feed a sampled
texture this way; the contract is **program-shaped, not universal**.

Consequences, now binding:

1. The oracle case is recorded as a measured **non-identity** witness
   (`cellrefract186-oracles.json` carries both surfaces and the mismatch
   census); the native include warns against asserting any crop identity.
2. The raw-crop-y trap check is still non-vacuous (47 lanes) and stays.
3. Any future slice reusing "the Shapes crop contract" must re-derive it for
   its own program; citing this slice as precedent for the identity is
   forbidden — only the *method* (probe, measure, record) transfers.

Also measured and recorded by the same lane, in the same spirit: the
`prng` divisor mutant at `4294967295` (one ULP below 2³²−1) is invariant on
every case — nearest-sampling absorbs the sub-texel perturbation — so it is
recorded as `prng_near_ulp_invariance`, not budgeted as a discriminating
mutant; and the four kept ledger mutants (smin-h-quadratic-dropped,
prng-pcg-constant-perturbed, aspect-ratio-inverted, wrap-arm-swapped) pin
different reachable functions, so their witness sets overlap by design —
no disjointness requirement is imposed, unlike shape/normalMap.

### §16 — corrects §3A: kaleido's reads are NOT reachable; the write-only shape is the family norm

§3A asserted "kaleido, whose reads live in reachable code" as the assumed
contrast case for the write-only census. Measured by the kaleido preparation
lane (2026-08-17, `kaleido-parity/kaleido-design.md`): kaleido at its frozen
defines (`DIRECTION=2/KERNEL=0/LOOP_OFFSET=10/METRIC=0`) is **write-only
exactly like cellRefract** — 45 `id` refs to its five array symbols, all
store-bases in its `loadKernels`, zero reads, and the 45 `(base, index,
value)` triples byte-identical to cellRefract's under an id-shift. The
normalizer strips kaleido's readers at `KERNEL=0` the same way. §3A's
"future row needs its own read census" guidance stands as a *requirement to
measure per key*, not as a claim that any known key has reachable reads. Two
kaleido-specific integration facts are already banked in that design §4.3:
`test_typed_generator.py`'s auto-attach census pins exactly {refract,
cellRefract} (a third key reddens it), and `authenticate_scalar_uint_xor`'s
frozen absent-set rejects any program carrying `fixed_array_in_parameter_proof`
— kaleido needs both carriers, so its integration slice must carve the XOR
allowlist per key.

### §17 — implementation discovery (amends §4): two rvalue compound assigns needed a third emitter arm

`derivatives` (`206:9`) and `sobel` (`226:9`) end with `return color *= dist;`
— compound assignments used as rvalues, in code unreachable at the frozen
defines (their only callers are stripped at `KERNEL=0`, exactly like the
caller tables). The emitter's expression grammar rejected them; the
validator had already admitted `*=`. The fix mirrors Shapes' §12 rvalue-assign
widening: a new identity-gated emitter arm resolving exactly those two nodes
at authentication time (2 nodes, `*=`, vec3 id target, frozen structurally).
Like the caller tables, these nodes have no oracle coverage — dynamically
dead at the frozen defines — so their protection is structural (RED/GREEN
identity locks), a recorded claim boundary rather than a pixel-tested one.
This is §9's anticipated discovery class firing a second time; the standing
lesson is that every member of this program family carries
unreachable-but-emitted code whose grammar must still close.

**Corrected 2026-08-17 by the native lane + controller:** the arm's first
lowering reused Shapes' scalar form `(color *= dist)`, which does not
compile — `glsl::Vec` defines no compound-assignment operators, and the
scalar precedent (`rot *= PI`) worked only because its target was a
`double`. The corrected vector lowering is the house assign form
`(color = glsl::Vec3(color * dist))` — double lanes, per-lane f32 narrowing
on store, exactly the JS `color = color * dist`. The arm now dispatches on
the target's type kind (`vector` → assign form; scalar → compound form) and
asserts the frozen `*=` operator. The two generated sites read
`return (color = glsl::Vec3(color * dist));` (`typed_slice.cpp:823,1097`).
`kaleido` (`620,640`) and `effects` (`300,320`) carry the identical source
pattern, so this corrected arm is the reusable form for their slices.

### Review-verified facts worth carrying into implementation

The review additionally established, by re-derivation: the 8 caller-table
symbol ids (107/108, 131/132, 152/153, 162/163) and `convolve`'s `offset`
table symbol 101; the 2 induction reads of `kernel` at `87:25`/`90:25` with
induction symbol 104, trip 9; the exactly-45-reference write-only census
(45 `id` refs to symbols 17-21 program-wide, every one an assign-target base
inside `loadKernels`, zero reads, zero whole-array bases, and no
initializers anywhere — the global-initializer census blind spot is
structurally n/a); that `resolution` is declared-but-unread and stays a
required ABI binding per the Shapes precedent; that `map` as a helper name
already coexists with a `const Frame&` ordinal-2 parameter in emitted
namespaces today (`typed_slice.cpp:21864`); that the `write to source const
global` audit (`generate_typed_slice.py:3958-3964`) covers only the const
`admitted_globals` set, so the separate mutable set is what keeps the 45
stores admissible; and that all six pinned CPU-file hashes still match, so
the JS authority has not drifted since normalMap.
