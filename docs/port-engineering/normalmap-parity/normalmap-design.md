# `filter/normalMap:normalMap` — design

Target: admit `filter/normalMap:normalMap` as typed row 185, taking the port to
**186 of 212**. This is the first program of the **const file-scope array**
mechanism, and the second program of the global-declaration bucket after
`synth/shape`.

Every number below was produced by a read-only probe of the live 184-row slice
on 2026-08-16, not carried forward from the previous census. The probe scripts
and their transcripts are named per claim.

## 1. Why this target, with the frontier evidence

The recommendation standing in `../REMAINING-EFFECTS.md` was to continue the
mutable-uninitialized-global sub-shape with the `float emboss[9];` array form.
Re-probing the bucket at 184 rows says that is the wrong next step, and it says
so for four programs at once. The probe admits a candidate mechanism in an
`rsync`'d copy and reports the program's *next* blocker, which is the only way
to see past a first barrier.

| Program | First blocker at 184 | Blocker once every global is admitted |
| --- | --- | --- |
| `filter/normalMap` | `15:1 unsupported global declaration` | **CLEAN** after array type + index + `round` |
| `filter/osd` | `24:1 unsupported global declaration` | `59:16 unsupported binary operator ^` |
| `classicNoisedeck/cellRefract` | `32:1 unsupported global declaration` | `66:29 unsupported typed type float[9]` (call site) |
| `classicNoisedeck/kaleido` | `33:1` (behind the XOR carrier) | `543:24 unsupported typed type float[9]` (call site) |
| `classicNoisedeck/effects` | `31:1 unsupported global declaration` | `395:10 unsupported typed type mat4` |
| `classicNoisedeck/bitEffects` | XOR carrier required | `141:13 unsupported binary operator &` |
| `filter/historicPalette` | `27:1 unsupported global declaration` | `18:1 unsupported struct declaration` |
| `filter/palette` | `29:1 unsupported global declaration` | `21:1 unsupported struct declaration` |
| `filter/spookyTicker` | `19:1 unsupported global declaration` | `1:1 unsupported varying` |

Three of those rows correct the current census and belong in
`REMAINING-EFFECTS.md` regardless of which program is built next:

- **`filter/spookyTicker` is a varying program**, not a global-declaration
  program. It is double-blocked, and the varying bucket's real membership is
  four (`grime`, `texture`, `wobble`, `spookyTicker`) rather than three.
- **`historicPalette` and `palette` block on struct declaration**, the same
  mechanism `synth/newton` needs. That bucket is three programs, not one — a
  fact independent of their unresolved adapter eligibility.
- **`bitEffects` and `osd` both need JS-Number bitwise semantics**, the
  `bitwise-scalar-int-ops-v2` shape built for `synth/bitwise`. Neither is a
  small global-declaration job. `<<` is not even in the frozen 17-entry binary
  operator vocabulary, so `bitEffects`'s `const int mask = (1 << BIT_COUNT) - 1;`
  cannot be admitted by widening the const grammar alone.

`normalMap` is the only program in the bucket that reaches CLEAN on a mechanism
that does not drag in a second large one. It is also the only one whose second
requirement is a **carrier that already exists**.

## 2. What is genuinely new, and what is wiring

Four things stand between the live generator and a clean `normalMap`. Both
authorities — `generate_typed_slice.py` (validator) and `emit_typed_cpp.py`
(emitter) — must independently agree on the first three. That separation is not
ceremony: Shapes183 passed the validator and gapped in the emitter, and the
emitter here has its own `_validate_source_globals` with its own mirrored
grammar.

| # | Requirement | New or existing | Reached at |
| --- | --- | --- | --- |
| 1 | Const file-scope **array declaration** admission | **new** | validator gate 1 (`admitted_globals` loop); emitter `_validate_source_globals` |
| 2 | Array **type** admission for a `TypedDeclaration` | **new** | validator `reject_type`; emitter `type()` / `_TYPES` |
| 3 | Const file-scope array **counted index read** | **new** | validator `index` arm; emitter expression arm |
| 4 | `round` admission | **existing carrier**, new key | `as-u32-round-admission-v1` |

### 2.1 Requirement 2 cannot reuse `proved_array_declarations`

`reject_type`'s array arm looks up `proved_array_declarations` by
`getattr(value, "symbol_id", None)` and then requires
`getattr(value, "kind", None) == "declaration"`. A `TypedDeclaration` (the
file-scope node) has neither attribute — it carries `symbol`, `type`, `span`,
`initializer` and nothing else. So the existing path is structurally
unreachable for a global, and registering the symbol in
`proved_array_declarations` does nothing. Verified by doing exactly that in the
probe copy and watching `15:1 unsupported typed type ivec2[9]` reproduce
unchanged.

The new arm must therefore key on **declaration node identity**, the same
pattern `mutable_global_frame_profile` uses for its two gates, not on a symbol
id lookup.

### 2.2 `fixed_nine_table_proof` is the structural precedent, not a carrier

`fixed_nine_table_proof.py` (208 lines) proves a **local**, literal-initialised,
counted-read `float[9]` / `vec2[9]` table for `filter/sharpen`, `filter/sobel`,
`filter/lighting`. Its capability is
`fixed-nine-local-literal-init-counted-read-v1` — the word *local* is in the
capability name. It is the right shape to copy: same nine elements, same
literal-only initializer, same `for (int i = 0; i < 9; i++)` counted read,
same three-tables-per-program layout as sobel's.

Two deltas, both real:

- **File scope, not local.** Which changes where admission happens and which
  authority owns the storage decision.
- **`ivec2` offsets, not `vec2`.** Sobel's offsets are `vec2[9]`; normalMap's
  are `ivec2[9]`. The element type is already in the approved 17-entry type
  tuple, so no type-vocabulary growth — only the array wrapper is new.

Do **not** add a key to `fixed_nine_table_proof`. Its capability name would
then be a lie, and its `_HOST_NAME`/`_LOOP_INDEX`/`_BODY_COUNT` locks are all
expressed against a host *function*, which a file-scope declaration has none of.

## 3. The materialization contract — read from the shipped JS

`canonicalFactory86` in
`noisemaker-for-cpu/src/effects/generated/canonical-kernels.js:15664`
(authority commit `4834b0144ee0524588144a482cca0067b15f68ec`):

```js
  var SOBEL_OFFSETS = [cpu_ivec2(-1, -1), cpu_ivec2(0, -1), … ];
  var SOBEL_X_KERNEL = [0.5, 0, -0.5, 1, 0, -1, 0.5, 0, -0.5];
  var SOBEL_Y_KERNEL = [0.5, 1, 0.5, 0, 0, 0, -0.5, -1, -0.5];
```

Three facts follow, and the middle one is the one this project has been burned
by five times:

1. **These are factory-scope `var`s, not re-initialised per pixel.** Same as
   `synth/shape`'s globals. The emitter's `source_global_locals` emits admitted
   globals as `const` locals *inside* the pixel body, so the port re-evaluates
   them per pixel. For these three that is observationally identical because
   every element is a literal (or a `cpu_ivec2` of two literals) with no
   dependency on any binding, uniform, or prior state — but that identity is a
   **proof obligation of this design**, not an assumption. The closure must
   require literal-only initializers precisely so the per-pixel re-evaluation
   is provably a no-op.
2. **`SOBEL_X_KERNEL` and `SOBEL_Y_KERNEL` are plain JS arrays of Numbers —
   doubles, never narrowed to f32.** They are not `Float32Array`. The GLSL type
   is `float[9]`, and reading the GLSL type is exactly how you get this wrong.
   The native element type is `double`, which is what
   `fixed_array_in_parameter_proof`'s existing alias
   (`using … = std::array<double, 9>;`) already does for the local form.
3. **`SOBEL_OFFSETS` elements are runtime `ivec2` objects** built through
   `cpu_ivec2`, an exact-integer constructor. `glsl::IVec2` is the native
   counterpart; no narrowing question arises.

Every element of both float tables is exactly representable in binary32 and in
binary64 (`0.5`, `0`, `1`, and their negations), so no *value* in this program
distinguishes the double contract from an f32 one. That makes the contract
**unfalsifiable by these literals alone** and it must not be claimed as proven
by a passing pixel test. It is proven structurally — by the emitted native type
— and recorded as a claim boundary in §9.

## 4. The closure: `const-global-nine-table-v1`

A new module, `tools/glslcpp/frontend/const_global_table_profile.py`, dict-keyed
from the first commit (the XOR profile's generalization to dict-keyed was its own
task; do not repeat that migration later).

```
PROFILE = "const-global-nine-table-v1"
NORMAL_MAP_KEY = "filter/normalMap:normalMap"
KEYS / PROFILES / CONST_GLOBAL_TABLE_KEYS
REQUIRED_COMPANION_PROFILES = {NORMAL_MAP_KEY: (("as_u32_round_profile",
                                                "as-u32-round-admission-v1"),)}
ALLOWED_ROW_FIELDS  — exhaustive-by-construction allowlist, per key
authenticate_const_global_tables(program, source_hash, profile)
    -> tuple[ConstGlobalTable, ...]
apply_const_global_tables(program, source_hash, profile) -> TypedProgram
```

`ALLOWED_ROW_FIELDS` is an **allowlist**, not a denylist. The `synth/shape`
review replaced a 5-entry `FORBIDDEN_COMPANION_FIELDS` against a 25-field
universe for exactly this reason; do not reintroduce the inverted form.

### 4.1 Frozen identity, per key

Following `mutable_global_frame_profile`'s field set: raw and normalized source
bytes + sha256, functions sha256, whole-program sha256, interface sha256, the
full ordered function inventory, the binding table, the resource tuple, and the
exact defines tuple (`()` for normalMap — it has no preprocessor defines).
Locking the defines per key is required: `linear_srgb_lane_index_profile`
carried a hardcoded `program.preprocessor_defines != ()` that had to become a
per-key exact lock when Shapes was added.

### 4.2 The table contract

```
class ConstGlobalTable(NamedTuple):
    symbol_id: int; name: str; glsl_type: str; native_element_type: str
    element_count: int; native_alias: str; native_sizeof: int
    declaration_span: str; element_spans: tuple[str, ...]
```

For normalMap, exactly three, in declaration order:

| name | id | GLSL type | span | native |
| --- | ---: | --- | --- | --- |
| `SOBEL_OFFSETS` | 9 | `ivec2[9]` | `15:1` | `std::array<glsl::IVec2, 9>`, 72 bytes |
| `SOBEL_X_KERNEL` | 10 | `float[9]` | `21:1` | `std::array<double, 9>`, 72 bytes |
| `SOBEL_Y_KERNEL` | 11 | `float[9]` | `27:1` | `std::array<double, 9>`, 72 bytes |

The `static_assert(sizeof(...) == 72U)` form is already emitted for the
fixed-array-in-parameter aliases; emit the same guard for these.

### 4.3 Predicates the closure must hold

Each is a separate, independently deletable check. The project standard is to
prove a check load-bearing by **deleting the check**, never by mutating the
input — a tree edit perturbs the whole-program hashes and the coarse gate
absorbs the mutation, so a mutation test can pass with the node-level logic
never running. Expect to record a taxonomy of which deletions fail where.

1. Exactly three array declarations, in the frozen order, at the frozen spans,
   with the frozen symbol ids.
2. Every one is `storage == "const"`.
3. Every one has an initializer whose kind is `construct` of the declared array
   type with exactly nine children.
4. Every child is a literal, a unary `+`/`-` of a literal, or — for the ivec2
   table — a `construct` of `ivec2` whose two children are each a literal or a
   unary `+`/`-` of a literal. **Nothing else.** No `id` references, no binary
   arithmetic, no dependency on an earlier admitted global. This is what makes
   per-pixel re-evaluation provably a no-op (§3.1).
5. No write anywhere in the program targets any of the three, at any depth,
   through any of `assign`, prefix `unary` `++`/`--`, or postfix `post`
   `++`/`--`. The `synth/shape` closure missed `post` on its first draft
   because the IR kind is `"post"`, not `"unary"`; reproduce that miss before
   fixing it.
6. Read census: exactly **three** index sites, all in `main`, one per table,
   each `TABLE[i]` where `i` is the same loop-index symbol (id 47), each
   `readonly`, at spans `138:24-138:40`, `144:23-144:40`, `145:23-145:40`.
7. Bare-reference census: exactly **three** `id` references to the three
   symbols program-wide — each one the base of its own index site. A fourth
   would mean the array escapes as a whole value (a call argument, a return),
   which this mechanism does not admit.
8. Every census walks **global initializers as well as `function.body`**.
   Two censuses in the Shapes183 closures walk only `function.body`, inherited
   from the `scanline_error_float_bits_ingress_profile` precedent; that gap is
   recorded as systemic in the acceptance record and must not be inherited
   again here.
9. The companion carrier is present and exact: the slice row must carry
   `as_u32_round_profile: "as-u32-round-admission-v1"`.

### 4.4 Guard messages get tests

The Shapes183 integration review found that **no closure in this codebase locks
its carrier-guard messages** — Scanline Error, Caustic, Linear sRGB and Glyph
Map all have zero test references to their guard strings. This slice does not
inherit that. Every guard string this module raises gets a test asserting that
specific message. It is a small cost here and it is the only thing that turns a
silently-rewritten guard red.

## 5. The `as-u32-round-admission-v1` key

`normalMap`'s `as_u32` is byte-comparable to the three keys already in the
profile:

```glsl
uint as_u32(float value) { return uint(max(round(value), 0.0)); }
```
```js
function as_u32 (value) { return max(round(value), 0)|0; };
```

One `round` site, at `34:21-34:33`, returning `float`, inside `as_u32`. Add
`filter/normalMap:normalMap` to `_PROFILES` in
`tools/glslcpp/frontend/as_u32_round_profile.py`, computed by the existing
`docs/port-engineering/global-admission/impl2/compute_as_u32_round_profile.py`
against the real typed IR. **Never hand-compute the frozen fields** — the
module's own header says so.

Both authorities already consult `authorized_as_u32_round`: the validator at
the `round` builtin arm and the emitter at its own `round` arm
(`noisemaker::f32(glsl::round(...))`, narrowing on return, matching the JS
`Math.round` then f32-on-return contract). So this is a key addition, not a
mechanism.

Note the round result **is** narrowed to f32 on return, unlike the kernel
tables. Two numeric contracts in one program again, and for the second slice
running. Do not let the table contract leak onto the round site or vice versa.

## 6. Emission contract

- **Aliases and storage.** Emit the three `using` aliases plus their
  `static_assert(sizeof(...) == 72U)` in `render_body`, from the closure's own
  frozen contract, alongside the existing `fixed_array_in_parameter_proof` and
  `fixed_affine_centers13_proof` alias blocks.
- **No static storage.** The tables become `const` locals in the pixel body via
  `source_global_locals`, like every other admitted source global. Confirm with
  a symbol dump that no static storage is emitted for the three — the
  `synth/shape` slice proved its `Frame` stack-only the same way.
- **`_TYPES` is not widened.** `_TYPES` is a flat display-name map with no array
  entry; adding `"ivec2[9]"` to it would make the array type generally
  emittable for every program. The array type must be resolved through the
  closure's per-declaration contract, the same node-identity route the
  validator uses.
- **Element emission.** `ivec2(-1, -1)` lowers through the existing `ivec2`
  constructor path; the float elements are plain double literals. Verify the
  emitted literal spellings against the JS array element-for-element, not by
  eye.

## 7. Oracle package

Model on `../shape-parity/shape_oracle_generator.mjs` and its five sidecars, and
inherit the **fix** that slice made rather than the defect it found: the oracle
JSON must carry a **stable placeholder** for the run-root path, derive the live
checkout from `NOISEMAKER_FOR_CPU` or `$HOME`, and reject any absolute-looking
string anywhere in the document. Both existing packages now pass from an
arbitrary fresh snapshot path and still refuse the live checkout; a new package
that records its own temp directory would reintroduce a gate that only passes on
one machine.

Mutants must have **disjoint witness sets** where they target different
contracts, so a divergence is attributable. Candidate mutants:

- `normalmap-sobel-x-y-swapped` — swaps the two kernels; must move `x_value`
  and `y_value` and not `z_value`.
- `normalmap-offsets-transposed` — swaps the `.x`/`.y` of each offset.
- `normalmap-round-half-away` — replaces `Math.round` with round-half-away-from-
  zero at the `as_u32` site. **Check whether this is satisfiable before
  shipping it**: `sanitize_channelCount` feeds `as_u32(size.z)`, and if `size.z`
  is never a half-integer in the oracle's binding set the mutant discriminates
  nothing. Shapes183 §11 is the precedent — an unsatisfiable control must be
  recorded and replaced with an invariance proof, not waived.
- A kernel-table f32-narrowing mutant is **not** available, because every
  element is exactly representable (§3). Do not ship a mutant that cannot
  diverge and call it a control.

## 8. Gates

The bar is what `synth/shape` met, and nothing less:

| Gate | Requirement |
| --- | --- |
| `check_corpus` / `check_semantics` (212) / `generate_kernels` / `generate_typed_slice` (185) | exit 0 |
| `tests.test_typed_generator` | green (≈1336 s — exceeds the 600 s subagent watchdog; the controller runs it, not a worker) |
| New `tests/test_const_global_table.py` | green, every predicate load-bearing by source-level deletion |
| Full Python `unittest discover` | green (≈40 min) |
| Native Debug / Release | 0 FAIL, ctest 1/1, zero warnings |
| ASan + UBSan | 0 FAIL, zero diagnostics. **No LeakSanitizer claim** — `detect_leaks=0` on Apple |
| Assembly, ARM64 + x86_64 | clean in pixel scope on both |
| Historical 185 → 184 reconstruction | exact; all 184 surviving blocks byte-identical after `typed_N` normalization |

All build lanes carry `-std=c++20 -Wall -Wextra -Wpedantic -Werror
-ffp-contract=off`, verified by reading `flags.make`, not the CMake invocation.

**Validate on the live tree, not in a copy.** Two different copy artifacts have
now been mistaken for regressions: a missing sibling `noisemaker-for-cpu`, and
an `rsync` that excluded `.git` so the oracle's `git rev-parse HEAD` produced
`JavaScript authority commit drift`. A validation copy must reproduce sibling
layout *and* version-control metadata, or the run must happen live.

## 9. Claim boundaries

- **The double contract on the kernel tables is proven structurally, not
  numerically.** Every literal is exactly representable in binary32, so no
  pixel test in this program can distinguish `std::array<double,9>` from
  `std::array<float,9>`. The claim rests on the emitted native type and on the
  JS being a plain `Array`, not a `Float32Array`. Say that; do not let a green
  parity run be reported as evidence for it.
- **Per-pixel re-evaluation is proven equivalent by the literal-only predicate**
  (§4.3.4), not by observation.
- **Nothing here admits a mutable global array**, a global array as a call
  argument or parameter, or a global array returned from a function.
  `cellRefract` and `kaleido` need all three and stay blocked.
- Roughly twenty clauses in every foreign-carrier collision chain are
  individually unreachable — inherited project-wide, recorded in
  `../REMAINING-EFFECTS.md`. Sweeping siblings and seeing this module's own
  message is therefore not proof that the sweep was meaningful.

## 10. What this unlocks, honestly

One program. `osd` shares the const-array sub-shape but is gated behind
JS-Number bitwise semantics, so this mechanism does not land it. The mechanism's
real value is that it is the **precondition** for the array form of the
mutable-global bucket (`cellRefract`, `kaleido`, `effects`), which is where the
remaining density is — and it buys that precondition on the one program where it
can be proven end-to-end without a second large mechanism in the way.

Re-run the frontier probe after this lands. Do not carry this census forward by
arithmetic: Shapes changed three bucket counts, and this probe changed three
more.

---

# Amendments

Sections 1-10 above are left as written apart from inline retraction markers, so
the design review remains auditable against them. Each amendment records
something §§1-10 asserted that an independent check disproved. **Where an
amendment and §§1-10 conflict, the amendment wins.**

The design review (2026-08-16) reproduced §1's nine-row table 9/9 from the
pinned corpus, and independently confirmed §2.1, all three of §3's
materialization facts, §4.2's frozen table, and §5's round contract against real
code. Those parts stand. What follows is what it broke.

## §11 — Two of §7's three mutants are bit-identical. **RETRACTS §7.**

`SOBEL_X_KERNEL` viewed as 3×3 is **exactly the transpose of `SOBEL_Y_KERNEL`**
— verified elementwise, `X[3r+c] == Y[3c+r]` for all nine. Transposing each
offset permutes the sample list by the involution `σ(3r+c) = 3c+r`, so

```
dx' = Σ X[σ(j)]·v_j = Σ Xᵀ[j]·v_j = Σ Y[j]·v_j = dy
```

`normalmap-sobel-x-y-swapped` and `normalmap-offsets-transposed` therefore
produce **bit-identical output everywhere**. A 143-pixel simulation of the real
`main` loop confirms it: both give per-channel diff counts `[143, 143, 0]`, and
the two mutant images compare equal at every pixel.

§7's stated expectation — "must move `x_value` and `y_value` and not `z_value`"
— is correct, and correct for *both*, identically. That is the failure: two
mutants that cannot be told apart cannot attribute a divergence to a contract,
which is the entire point of requiring disjoint witness sets.

**Keep one.** Replace the other with a mutant no permutation of the offsets can
produce — perturbing a single kernel element (`SOBEL_X_KERNEL[1] = 0.25`), or
negating one kernel (moves `x`, leaves `y` and `z`). Then assert disjointness as
a **checked property of the generated oracle**, not as an intent stated in prose.

## §12 — `normalmap-round-half-away` is structurally unsatisfiable. **RETRACTS §7.**

§7 asked the wrong question. It framed satisfiability as contingent on the
binding set: "if `size.z` is never a half-integer in the oracle's binding set."
Two corrections:

1. **`as_u32` has three call sites, not one.** `as_u32(size[0])` and
   `as_u32(size[1])` are called directly in `main`
   (`canonical-kernels.js:15760-15761`), in addition to `as_u32(raw_value)`
   inside `sanitize_channelCount`. §7's premise was incomplete.
2. **The binding set is irrelevant.** `as_u32(v) = max(round(v), 0)|0`.
   `Math.round` and round-half-away-from-zero differ **only** on negative
   half-integers, and every negative result is collapsed by the `max(…, 0)`
   clamp. A 40,021-sample scan over half-integers, quarter-integers, ties, ±0,
   NaN, ±Infinity and the 2²³ boundary found **5,006 values where the two
   rounders disagree and 0 divergences in `as_u32`**.

The discriminating domain is provably empty, and it is empty because of the
clamp — not because the oracle's bindings happen to miss it. Do not ship the
mutant. Record the axis and prove it **invariant** instead, following Shapes183
§11.

The consequence must be said out loud rather than buried: **this oracle package
can prove nothing whatsoever about the round contract for this program.** That
is a third claim boundary, and §9 is amended to carry it.

## §13 — Predicate 6 does not bound the index. **AMENDS §4.3.**

§2.2 describes the shape as "same `for (int i = 0; i < 9; i++)` counted read",
but **no predicate in §4.3 encodes the loop at all**. Predicate 6 pins the index
*symbol* and the site spans; it never pins the trip count.

`fixed_nine_table_proof.py:163-168` — the precedent §2.2 says this design is
copying — does exactly that:

```python
if (loop.kind != "for" or loop.loop_proof is None
        or loop.loop_proof.start_value != 0 or loop.loop_proof.bound_value != 9
        or loop.loop_proof.comparison != "<" or loop.loop_proof.update != "++"
        or loop.loop_proof.trip_count != 9 or len(loop.children) != 2
```

and at `:188` ties the index node to `loop.loop_proof.induction_symbol_id`.

`std::array::operator[]` is unchecked and the JS returns `undefined` → NaN, so a
program satisfying all nine predicates with a trip count of 12 reads out of
bounds natively and NaN in the oracle. It cannot slip through for *this* key,
because the whole-program hashes catch it — and that is precisely the vacuity
this project's delete-the-check method exists to expose. §4.3's own preamble
commits to each predicate being "a separate, independently deletable check";
delete predicate 6 today and nothing goes red on range safety.

**Add predicate 10**, separately deletable: bind the three read sites to the
enclosing loop's `loop_proof` (start 0, bound 9, `<`, `++`, trip count 9) and
require `index.symbol_id == loop.loop_proof.induction_symbol_id`. Copying the
precedent's structural shape means copying this, not only its census shape.

## §14 — Two requirements are missing from §2. **AMENDS §2, §4, §6.**

§2 asserts exactly four requirements. It is four at the validator and **six**
overall.

### Requirement 5 — array constructor **expression** emission

§2's requirement 2 is scoped to a `TypedDeclaration`. The initializer is a
`TypedExpression`, and it gaps twice:

- `self.type()` on `ivec2[9]` raises `unsupported typed type ivec2[9]` through
  the `_TYPES` `KeyError`.
- Even with the type resolved, the generic `construct` fallback
  (`emit_typed_cpp.py:3214`) emits **parenthesized call syntax**
  `Alias(a, b, …)`, which does not compile for `std::array`. It needs aggregate
  brace-init, `Alias{{ … }}`.

Add a node-identity-keyed array-constructor arm to the emitter's `construct`
dispatcher, emitting brace-init against the closure's frozen `native_alias`,
with its own guard message and its own test.

Two smaller emitter notes: the closure must populate
`self.source_global_dependencies[symbol_id] = ()` or `source_global_locals`
raises `KeyError` on its closure walk; and `source_global_locals` emits
`declaration.symbol.name` raw rather than the `_safe_identifier` it just
computed into `self.locals` — pre-existing, benign for `SOBEL_*`, and not to be
inherited silently.

### Requirement 6 — the slice-row field arm, which is ordering-sensitive

§4 defines `ALLOWED_ROW_FIELDS` but never names its consumption site. The
per-key row-field allowlist chain at `generate_typed_slice.py:1021-1110`
contains

```python
{"defines", "as_u32_round_profile", "program_key"}
if key in AS_U32_ROUND_KEYS else
```

Once `filter/normalMap:normalMap` joins `AS_U32_ROUND_KEYS` — which Task 1 does
— **that arm claims the row** and rejects a `const_global_table_profile` field
with the generic `typed slice programs are invalid`. The new arm must be
inserted **ahead** of it, exactly as `SHAPES_KEY`'s arm is placed ahead of the
shared linear-sRGB arm, with an in-source comment naming the hazard.

Separately, `mutable_global_frame_profiles` and the Shapes carriers each carry a
**named** drift census with their own message (`:1304-1315`) specifically so a
failure is not misreported by a neighbouring clause. Add one for this profile.

## §15 — §3.1's reason for per-pixel equivalence is not the operative one, and §2.2 has the ivec2/vec2 risk backwards. **RETRACTS §3.1 and §2.2.**

This is the finding with the longest reach, and it inverts something §2.2
dismissed.

`SOBEL_OFFSETS` elements are **pooled** `Int32Array`s (`#allocInteger`,
`glsl-runtime.js:430-436`), not fresh objects. They survive the render only
because `beginPixel` snapshots `signedBaseIndices` on first call and resets the
integer index to that base (`:132-137`). **The float pool has no such base** —
`beginPixel` does `this.indices.fill(0)`. Executed against the live runtime:

```
after pixel  ivec: [[-1,-1],[0,-1],[1,-1]]   vec: [[111,222],[333,444]]
aliased? vecTable[0] === scratch1: true      ivecTable[0] === iscratch: false
```

A factory-scope `PooledFloat32Array` table is **aliased and overwritten by the
first per-pixel scratch allocation.**

So §3.1 is wrong about *why* per-pixel re-evaluation is a no-op. Literal-only
initializers are **necessary but not sufficient**. Had these offsets been
`vec2`, the JavaScript itself would clobber the table mid-render, and the port's
per-pixel re-evaluation would *not* match the authority. The operative reason is
the **element materialization**: a plain Number array, or a base-index-protected
integer pool entry.

And §2.2 has it backwards. It calls the ivec2-vs-vec2 delta a non-event —
"the element type is already in the approved 17-entry type tuple, so no
type-vocabulary growth — only the array wrapper is new." Type-vocabulary growth
was never the risk. The delta is the whole difference between a pool-protected
table and a self-clobbering one.

**New claim boundary, and it is a live hazard**, because §10 sells this slice as
the precondition for the array form of the mutable-global bucket:

> **This mechanism must not be extended to a float-vector element type**
> (`vec2[N]`, `vec3[N]`, `vec4[N]` const globals) without re-deriving the pool
> argument from `glsl-runtime.js`. The predicate set in §4.3 would admit such a
> table and the port would silently disagree with the authority.

Encode it: the closure's element-type check must be an **allowlist** of
`{float, int, uint, ivec2, ivec3, ivec4, uvec2, uvec3, uvec4}` — never a
denylist, and never "any approved type".

## §16 — Minor corrections

- **§4.3.6's category string is wrong.** The IR category is `"readonly lvalue"`
  (`frontend/body_semantic.py:156,178`), which is what the three sites carry.
  Sibling profiles compare against that exact literal. A predicate written
  `== "readonly"` fails closed but with the wrong message — the §4.4 failure
  mode this design is otherwise trying to prevent.
- **§4.4's universal claim is false.** "No closure in this codebase locks its
  carrier-guard messages" is refuted by `tests/test_edge_bvec3_contour.py:47,53`
  and `tests/test_gabor_effective_depth.py:93`. Scope the claim to the four
  modules actually checked. The prescription — test every guard string — is
  right and stands.
- **`shape-design.md` Amendment 2's carried instruction is addressed, not
  dropped.** It flagged `out`/`inout` call arguments as an unmodelled mutation
  path that "bites the array form", and this *is* the array form. §4.3.5 lists
  only `assign` / `unary` / `post`; the coverage actually comes from predicate
  6's category check. Say that explicitly rather than leaving the preceding
  slice's deferred item silently unaddressed.
- **§1's table header overstates one cell.** The column reads "Blocker once
  every global is admitted", but the `normalMap` cell reports the state after
  four independent widenings. The true intermediate state, with globals and
  declaration-site array types admitted, is
  `138:24 unsupported typed expression index`. It is the one cell in that column
  not comparable to the other eight.
- **§1's numbers are tree-state dependent.** `normalMap`'s first blocker is
  `15:1 unsupported global declaration` **against committed HEAD** `c846a23`.
  With Task 1's `as_u32_round_profile` change in the working tree it becomes
  `exact as_u32 round admission profile carrier required`. A design claiming
  every number came from "a read-only probe of the live 184-row slice" must say
  which tree state.
- **§3 stops short of the accumulator.** `dx += value * SOBEL_X_KERNEL[i]` is
  raw JavaScript on plain `var`s: **double accumulation with no per-step `F32`**,
  unlike everything routed through `$runtime`. Nine f32-valued terms summed in
  double is not the same as summed in float. This is already satisfied by
  `local_type` mapping GLSL `float` → `double`, so it is not a defect — but a
  section titled "The materialization contract", in a project misled five times
  by exactly this class of thing, must name the accumulator.
- **The closure is the *sole* authority on the initializer at the validator.**
  The validator never type-checks global initializer expressions at all: the
  generic `expression()` walk iterates `program.functions` only, and so does the
  write audit (`audit_statement`, `:3789-3795`). A probe reached CLEAN with the
  `ivec2[9]` construct node present and never visited. §4.3.8's demand that the
  censuses walk global initializers is therefore far more load-bearing than its
  one-line statement suggests.
