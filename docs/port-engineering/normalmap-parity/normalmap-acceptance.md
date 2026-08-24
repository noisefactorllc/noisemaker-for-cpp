# filter/normalMap acceptance record

`filter/normalMap:normalMap` accepted as typed row 185, sorted index 66, on
2026-08-16. **186 of 212 programs ported.** First program of the const
file-scope array mechanism (`const-global-nine-table-v1`), and the second
program of the global-declaration bucket after `synth/shape`.

## Final state

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 23,202 | `69deb0c8b3f9b453c1101263b0de7fb2f0c1915a21ea5f6cbb298cf0508df20d` |
| `src/typed_generated/typed_slice.cpp` | 1,886,817 | `e7b52cd1f8001978912abf69278f7fad093ae40bb8adf121bae297ef16c952eb` |
| `src/typed_generated/typed_manifest.json` | 295,588 | `de2237511727f93d17df05267512267281c75b62ec6966a32da65f4e23d34667` |
| `include/noisemaker/generated/catalog.hpp` | 17,099 | `4c30f680957a9cec5667b501b64e56869e9e1d7d90e562e3014c6ccf8b50fb4f` |

185 typed rows, 187 catalog entries, 27 corpus keys absent from the slice.
Sorted typed-key SHA-256
`75ea3f3987ece02df2738db474aecaf9ec82b6cfa8a3172f245bdb28d16b6d60` — over the
sorted keys joined by `\n` **with a trailing newline**.

**26 genuinely unported, derived rather than asserted.** Per
`../REMAINING-EFFECTS.md`'s "Two counts, and why they differ": corpus keys
absent from the typed slice is the computable figure the generator tests assert
(212 − 185 = 27); genuinely unported is that set minus programs already public
by another route, which today is exactly one — `filter/wormhole:deposit`, which
ships through the scatter pass. So 27 − 1 = **26**, and the relationship holds
only for as long as `deposit` remains the sole such program. The catalog's 187
is likewise derived: 185 unique typed keys plus the two deliberate dual
registrations, `filter/invert:inv` and `synth/solid:solid`.

The slice row carries two carriers, one new and one pre-existing:

```json
{
  "as_u32_round_profile": "as-u32-round-admission-v1",
  "const_global_table_profile": "const-global-nine-table-v1",
  "defines": {},
  "program_key": "filter/normalMap:normalMap"
}
```

The oracle package and its materializer:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `normalmap_oracle_generator.mjs` | 113,197 | `97f04119127194fe52ad1d8237e5bf923504c280a03b0d76de4d19b1dee297fe` |
| `normalmap-oracles.json` | 440,152 | `1c222a5031e1dd58240344bcb2c4806c0bd01d2aceebb98d43e4e00589f2685d` |
| `normalmap-oracle-report.md` | 27,302 | `fde604f61e9e3076a553192dd4bd59da05ddca313218bc374ad4f2a76714026e` |
| `tools/glslcpp/generate_normalmap_native_oracle_include.py` | 106,764 | `1d0efabc93dfdefe486514ad5a503fb554e15318582483295ac76d746fbae3df` |
| `tests/oracles/normalmap_expected.inc` | 83,429 | `72761710d35c86367b5de3928a741ec7551dd4a712d53c76d77d33364e0487f6` |

All five `.sha256` sidecars re-verified at acceptance.

## Gates

| Gate | Result |
| --- | --- |
| `check_corpus --check` | exit 0, `check_corpus: ok` |
| `check_semantics --check` | exit 0, `bodies ok (212 programs)` |
| `generate_kernels --check` | exit 0 (silent) |
| `generate_typed_slice --check` | exit 0, `typed slice ok (185 programs)` |
| `tests.test_typed_generator` | **210 / 0**, 1,650.199 s |
| `tests.test_const_global_table` | **109 / 0** |
| `tests.test_scalar_uint_xor` and `tests.test_runtime_loop_bound` (the two sibling modules covering `as-u32-round-admission-v1`) | **15 / 0** and **25 / 0** |
| Full Python suite, all 19 `tests/test_*.py` modules | **660 tests, 0 failures, 0 errors, 0 skipped**, 2,286.473 s |
| Native Debug | **256 PASS / 0 FAIL**, ctest 1/1, zero warnings |
| Native Release | **256 PASS / 0 FAIL**, ctest 1/1, zero warnings |
| ASan + UBSan | **256 PASS / 0 FAIL**, ctest 1/1, **zero ASan and zero UBSan diagnostics** |
| Assembly, ARM64 + x86_64 | pixel scope clean on both — no jump table, no indirect branch, no fused-FP |
| Historical 185 → 184 reconstruction | **exact**; 184/184 surviving blocks byte-identical |

All build lanes carry `-std=c++20 -Wall -Wextra -Wpedantic -Werror
-ffp-contract=off`, verified by reading `flags.make` in each build tree rather
than the CMake invocation.

**No LeakSanitizer claim.** `detect_leaks=0` on Apple means LSan did not run;
the sanitizer lane covers ASan and UBSan only.

**`DEFECTS-FOUND.md` item 4** — the `synth/bitwise` signed-overflow UBSan
diagnostic — did not reproduce in this lane either, for the third slice running.
It is **not** claimed fixed and carries no resolution marker.

### Two notes on the gate results

**`tests/` has no `__init__.py`, so `python -m unittest discover -s tests -t .`
refuses with `ImportError: Start directory is not importable`.** The full-suite
figure above comes from a scratch runner that loads every `tests/test_*.py`
under its real `tests.<name>` package path — the same module set, the same
import path the individual modules use — and reports one combined result.
Creating an `__init__.py` would have been a write into the repository. **The
module count is asserted by the runner rather than assumed, and that caught a
mistake**: the suite is **19** modules, not 20. The three figures reconcile
exactly — 660 total = 210 in `test_typed_generator` + 450 across the other 18,
and `test_const_global_table`'s 109 sits inside that 450 rather than beside it.
`test_typed_generator` was additionally run standalone against the same frozen
tree and reported 210 OK there too.

**The assembly gate is conditional, and the condition is different from
Shapes183's.** `shapes183-design.md` §13 records that `typed_8::value` contains a
real jump table that stays out of pixel scope only because its defines are frozen
at 40/30. `filter/normalMap` has **zero preprocessor defines**, so no frozen
define value is holding this result up. What the result *is* conditional on is
the optimization level: pixel scope was computed on the `-O3 -DNDEBUG` listing
after inlining, and it resolves to 4 bodies on x86_64 and 5 on ARM64 (`pixel`,
`oklab_l_component`, a `clamp` instantiation, `___clang_call_terminate`, plus
`value_map_component` out-of-line on ARM64 only). A different optimization level
gives a different inline set and the audit must be re-run.

Two further boundaries on that gate, stated rather than glossed:

- **Fused-FP absence is proven for the whole translation unit**, not merely
  pixel scope: zero `fmadd`/`fmsub`/`fnmadd`/`fnmsub`/`fmla`/`fmls` in 278,410
  lines of ARM64 listing and zero `vfmadd`/`vfmsub` family in 328,937 lines of
  x86_64 listing. That is an independent witness that `-ffp-contract=off` reached
  the compile line.
- **The pixel path leaves this translation unit.** It calls out to
  `noisemaker::f32`, `glsl::round`, `glsl::detail::float_to_uint32`,
  `texel_fetch_bottom_left`, `Surface::width`/`height` and platform `pow`, none
  of which this listing contains. The `pow`/`atan2`-to-libm versus
  `sin`/`cos`-to-fdlibm asymmetry is generator-wide and intended.
- The one `___clang_call_terminate` reference in pixel scope is the known
  systemic condition recorded in `../REMAINING-EFFECTS.md`:
  `glsl::Vec<N,T>::Vec(const FloatExpr<N>&)` is not `noexcept`. Not a defect,
  not this slice's to fix, and named so a future audit does not re-investigate
  it. The only indirect branch anywhere in the 26 emitted `typed_66` bodies is
  the `shared_ptr<State>` destructor's virtual dispatch, on both architectures —
  bind-time and teardown, never pixel scope.

## What this program proves

The mechanism exists because three **const** file-scope arrays must be admitted,
materialized with the JavaScript's own element type, and read exactly three
times inside one nine-iteration loop:

| name | id | GLSL type | native |
| --- | ---: | --- | --- |
| `SOBEL_OFFSETS` | 9 | `ivec2[9]` | `std::array<glsl::IVec2, 9>`, 72 bytes |
| `SOBEL_X_KERNEL` | 10 | `float[9]` | `std::array<double, 9>`, 72 bytes |
| `SOBEL_Y_KERNEL` | 11 | `float[9]` | `std::array<double, 9>`, 72 bytes |

It is proven four independent ways:

1. **Structurally** — a new closure, `const-global-nine-table-v1`, whose every
   predicate was shown load-bearing by deleting the predicate. 28 of 28
   whole-predicate deletions go red, re-run after the accessor refactor and
   still 28/28, and reproduced independently by the reviewer.
2. **By two authorities that do not share a code path** — the validator
   (`generate_typed_slice.py`) and the emitter (`emit_typed_cpp.py`) each admit
   the three declarations and the three reads **by node identity**, through a
   single private `_authenticate` that both public accessors are structurally
   required to be the sole call into. `grep -c Sobel` returns **0** in both
   authorities, so every alias fact flows from the closure's `table_contract()`
   rather than from a hardcoded name.
3. **By oracle** — eight rendered cases from the unmodified `canonicalFactory86`
   in an immutable snapshot, compared word-for-word and byte-for-byte, with two
   ledger mutants whose witness sets are **disjoint and engineered to be so**:
   every kernel-witness case has uniformly opaque input, and the single
   varying-alpha case has a constant value map so both gradients are exactly
   `+0`.
4. **Natively, by derivation rather than transcription** — swapping the two
   kernel tables exchanges `dx` and `dy`, so the swap mutant's image is exactly
   the canonical image with its R and G lanes exchanged. All **eight** cells of
   that mutant's ledger row are re-derived in
   `typed_normalmap185_mutant_ledger_is_disjoint_and_natively_derived` from the
   stored canonical words, with no floating-point arithmetic and no
   reimplementation of the kernel, and every one matches.

The per-pixel equivalence proof — the crux, because the emitter emits admitted
source globals as `const` locals *inside* the pixel body — is **measured, not
argued**: a mutant that shadows all three tables with identical declarations at
the top of `main()`, exactly the rewrite `source_global_locals` performs, renders
bit-identically on every case (0 changed lanes).

Design §6's "no static storage" requirement is discharged by a symbol dump of the
Release object file rather than by inspection: `nm | c++filt` on
`typed_slice.cpp.o` finds **no `SOBEL_*` symbol of any kind** — the only two
symbols matching "Sobel" are the unrelated `bind_filter_sobel_sobel` and
`bind_filter_outline_outlineSobel` — and the only static-duration `typed_66`
symbols are six RTTI/vtable entries for `State` and its `shared_ptr` control
block, which is the standard polymorphic-`KernelState` machinery. The bound of
that claim: it rules out a named static-duration object for the tables, not the
compiler's own unnamed read-only constant pool, which is a codegen choice
identical for any local `const` array.

## What this program does NOT prove

Every item here is a place where a green run would otherwise be read as evidence
it is not.

1. **The oracle package proves nothing whatsoever about the round contract.**
   Amendment §12: `Math.round` and round-half-away-from-zero differ **only** on
   negative half-integers, and the `max(…, 0)` clamp in
   `uint as_u32(float value) { return uint(max(round(value), 0.0)); }` collapses
   every negative result. Measured over 40,022 samples — half-integers,
   quarter-integers, ties, signed zero, NaN, both infinities, ±2²³ and the int32
   bounds — **7,505 values where the two rounders disagree and 0 `as_u32`
   divergences**, with the `normalmap-round-half-away` mutant rendering 0 changed
   lanes on all eight cases. The axis is proven **invariant**, not exercised. The
   discriminating domain is provably empty because of the clamp, not because the
   binding set happens to miss it. (The design review's own independent scan used
   a slightly different sample set — 40,021 samples, 5,006 disagreements, quoted
   in Amendment §12 — and reached the same zero. The shipped package's numbers
   are the ones the `.inc` asserts and the ones above.)
2. **The `double` kernel contract is proven structurally, never numerically.**
   Every element of both tables is `0.5`, `0`, `1` or a negation — exactly
   representable in binary32 *and* binary64 — so **no pixel test in this program
   can distinguish `std::array<double, 9>` from `std::array<float, 9>`**. The
   f32-narrowing mutant was compiled and rendered anyway, to demonstrate the
   impossibility: 0 changed lanes on every case, recorded
   `cannot-diverge-do-not-ship`. The claim rests on the emitted native type and
   on the JavaScript being a plain `Array`, not a `Float32Array`. The one half of
   the numeric story that *is* discriminable is the accumulator: `dx += value *
   SOBEL_X_KERNEL[i]` accumulates in double with no per-step `F32`, and an
   accumulator-narrowing mutant moves **48 and 46** lanes on the two oklab cases
   and 0 lanes everywhere else. Its witnesses are a subset of the retained
   ledger mutant's, so it ships as evidence, never as attribution. (The `43` in
   this record's first draft was transcribed from report prose; the shipped
   document records `46`, the emitted oracle report says `46`, and the Task 4
   review's independently constructed mutant measured `46`. Third instance of a
   hand-transcribed figure disagreeing with the artifact — quote measured values
   from the JSON, never retype them.)
3. **`filter/normalMap` has no params**, so `createCanonicalBindings` leaves
   `size` as the **zero vec4** on every shipped render. channelCount is therefore
   always 1, the entire `oklab_l_component` / `srgb_to_linear` / `cbrt_safe`
   subtree is dynamically dead, `size.w` is never read, and `main()`'s early
   return is unreachable. **Four of the eight oracle cases bind a non-zero `size`
   and are labelled `synthetic-size`.** They are ABI coverage — a port that gets
   them wrong is wrong — but they **must not be cited as production evidence**.
   The materializer re-derives each case's route label from its stored `size`
   words, so the label cannot drift from the binding, and it throws if the effect
   ever grows a param.
4. **Amendment §15's hazard, as a boundary future work must respect.** This
   mechanism **must never be extended to `vec2[N]` / `vec3[N]` / `vec4[N]` const
   globals without re-deriving the JS pool argument from `glsl-runtime.js`.**
   `SOBEL_OFFSETS`'s elements are pooled `Int32Array`s that survive the render
   only because `beginPixel` snapshots `signedBaseIndices` on first call and
   resets the integer index to that base; the float pool has no such base —
   `beginPixel` does `this.indices.fill(0)` — so a factory-scope
   `PooledFloat32Array` table is aliased and **overwritten by the first
   per-pixel scratch allocation.** Executed against the pinned runtime: the float
   table reads back clobbered, the integer table reads back intact. Literal-only
   initializers are **necessary but not sufficient**; the operative reason
   per-pixel re-evaluation is a no-op here is element materialization. The
   closure encodes this as an **allowlist** — `{float, int, uint, ivec2, ivec3,
   ivec4, uvec2, uvec3, uvec4}` — never a denylist and never "any approved type",
   and the materializer rejects the document if any `vec*` entry appears.
5. **The f32-narrowing load-bearing measurement is a scratch script, not a
   committed test.** Stated in those words. Re-measured against the final 23-test
   integration class it reddens three named tests rather than two; nothing in
   `tests/` performs that measurement on its own.
6. **`DEFECTS-FOUND.md` item 5 is a known boundary of this slice, recorded and
   not fixed.** An early `return;` in `main()` writes **black** where JavaScript
   writes the *previous pixel's colour*, because the port does not model
   JavaScript's persistent factory-scope `fragColor`:
   `src/pass_runner.cpp:96,169` declare `glsl::Vec4 output;` inside the per-pixel
   loop, and the emitted `pixel()` assigns it only on paths reaching a
   `fragColor` write. Four shipped programs already carry it — `filter/crt`,
   `filter/degauss`, `filter/fxaa`, `filter/grain` — and normalMap is the fifth
   (`typed_66`; 31 bare `return;` statements in the emitted output, five not
   preceded by an `output =` assignment).

   **Correction to this record's first draft, and to `DEFECTS-FOUND.md`'s.**
   Both originally called this **undefined behaviour**, reasoning from
   `constexpr Vec() = default;` at `glsl_types.hpp:105` that `output` is left
   indeterminate. That is wrong. `glsl_types.hpp:133` declares
   `std::array<T, N> lanes_{};` — a default member initializer — so the
   defaulted constructor value-initialises. Verified by compiling a probe
   against the real header, mirroring `pass_runner.cpp:96` exactly, under
   `-std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off`: three
   consecutive iterations each print `0 0 0 0`, with
   `static_assert(!std::is_trivially_default_constructible_v<glsl::Vec4>)`
   compiling clean. **There is no uninitialised read.** The parity divergence is
   real and unchanged; only its severity is different, and the earlier claim
   that "MSan would catch it" is withdrawn — **no sanitizer can**, because
   nothing here is memory-unsafe. Only a parity test driving a resolution
   smaller than the surface would find it.

   The configuration is unreachable through the shipped binding set, and the
   native suite proves that rather than asserting it: for all eight cases the
   width and height `main()` resolves cover every rendered fragment. The
   oracle's `fragcolor_persistence_witness` arrays are quarantined behind
   `kFragColorPersistenceNativelyExpressible = false` and **no parity test reads
   them**.

Two smaller boundaries inherited from the project rather than introduced here:

- **Collision chains are mostly unreachable.** Roughly twenty of the thirty-odd
  clauses in every foreign-carrier chain are individually unreachable, because an
  earlier mechanism's guard claims the row first. Sweeping siblings and seeing
  this module's own message is therefore not proof that the sweep was meaningful.
- **Sub-clause vacuity is not exhaustively excluded.** The Task 2 re-review swept
  roughly 35 further sub-clauses beyond the 28 whole predicates; about 30 delete
  green individually, and every one was then shown still independently pinned by
  a static hardcoded-literal comparison elsewhere in the test file. None
  reproduces the original severity — a frozen table proved by nothing, anywhere —
  but the sweep is not a proof of completeness.

## The design was wrong six times, and each correction is recorded

The design review reproduced §1's nine-row frontier table 9/9 from the pinned
corpus and independently confirmed §2.1, all three of §3's materialization facts,
§4.2's frozen table and §5's round contract against real code. Those parts stand.
Six Important findings were accepted and landed as Amendments §§11-16 rather than
argued down.

| Amendment | What §§1-10 got wrong |
| --- | --- |
| **§11** | Two of the three specified mutants are **bit-identical**. `SOBEL_X_KERNEL` viewed as 3×3 is exactly the transpose of `SOBEL_Y_KERNEL`, so transposing the offsets and swapping the kernels produce the same image everywhere. Two mutants that cannot be told apart cannot attribute a divergence. |
| **§12** | `normalmap-round-half-away` is **structurally unsatisfiable**, and `as_u32` has three call sites, not one. The design framed satisfiability as contingent on the binding set; it is not. |
| **§13** | Predicate 6 never bounds the loop. `std::array::operator[]` is unchecked and the JS returns `undefined` → NaN, so a program satisfying all nine predicates with a trip count of 12 reads out of bounds. Predicate 10 binds the reads to the enclosing `loop_proof`. |
| **§14** | Two requirements were missing: the array constructor needs **brace-init** (the generic `construct` fallback emits parenthesized call syntax, which does not compile for `std::array`), and the new row-field arm must be inserted **ahead of** the `AS_U32_ROUND_KEYS` arm, which would otherwise claim the row. |
| **§15** | §3.1's stated reason for per-pixel equivalence is not the operative one, and §2.2 had the `ivec2`-versus-`vec2` delta **backwards** — it called it a non-event about type vocabulary when it is the whole difference between a pool-protected table and a self-clobbering one. |
| **§16** | Seven minor corrections, including the IR category string being `"readonly lvalue"` rather than `"readonly"`, §4.4's universal claim about guard-message locking being refuted by two existing modules, and §3 stopping short of the double accumulator. |

**§11 and §12 both shrink the mutant budget**, which is a real loss of oracle
power. It is recorded as a claim boundary above rather than papered over.

Two further corrections came out of building it, neither anticipated by the
design:

- **§11's letter and its spirit conflict on a rich case set.** Its suggested
  replacements were built and measured: `normalmap-sobel-x1-perturbed` witnesses
  8 of 8 cases and `normalmap-sobel-x-negated` 7 of 8 — the same seven as the
  retained mutant. Each witness set is a strict **superset**, so neither can be a
  disjoint second ledger entry on any case set that also covers the program's
  real behaviour. Disjointness was kept (the property §11 argues for), both
  measured mutants ship as `kernel_table_mutant_census` with
  `in_disjoint_ledger: false` and the superset relation machine-checked, and the
  second ledger slot went to `normalmap-alpha-source-transposed` — a different
  contract, a single exclusive witness.
- **`filter/normalMap` declares no params**, which the design's reachability
  picture never mentions, along with the early return and `fragColor`
  persistence. §§1-16 are silent on all three and §8's gate table did not
  anticipate them.

## Reviews

Every piece independently reviewed; every review verified by execution.

| Task | Verdict |
| --- | --- |
| Design | **GO WITH FIXES** — 6 Important (all landed as §§11-16), 7 Minor folded into §16 |
| 1 — `as-u32-round-admission-v1` fourth key | **No separate review, by controller ruling.** The diff is `52 insertions(+), 0 deletions(-)`, so no pre-existing line and therefore no predicate changed, and all 52 added lines are inside the new dict entry. Recorded as a deliberate trade: a data-only addition ships unreviewed behind four green test modules and the generator's own check. |
| 2 — `const-global-nine-table-v1` closure | **APPROVED WITH FIXES**, then two fix rounds, then **FINDINGS ADDRESSED** |
| 3 — both authorities, slice row, artifacts | **APPROVED WITH FIXES**, then two fix rounds, then **COMPLETE** |
| 4 — oracle package | **No independent review verdict is recorded.** `task-4-report.md` self-reports `DONE_WITH_CONCERNS`, and the ledger carries the controller's rulings on its findings (record-don't-fix for `DEFECTS-FOUND` item 5; accept the different-contract second ledger mutant) — but the ledger's own task table still reads *"implemented, review pending"* and no reviewer verdict appears in its log. Stated as it stands rather than rounded up. |
| 5 — native parity, gates, this record | this document |

The Task 4 row is the one exception to the heading above, and it matters because
`../REMAINING-EFFECTS.md` records a process trap from the previous slice:
**a slice is not done until every dispatched review has reported**, and the
previous controller declared acceptance before an integration review arrived that
then produced an Important finding. If a Task 4 review was dispatched, its verdict
belongs in the ledger before this record is treated as final. What the package
*does* have is independent machine verification: `--check` passes from two
differently-shaped snapshot paths and refuses the live checkout, the materializer
`--self-test` proves 77 rejections each with a message assertion, and this task
re-derived all eight cells of the retained mutant's ledger row natively.

### What the reviewers reproduced rather than read

- **The design review** reproduced §1's nine-row frontier table 9/9 from the
  pinned corpus, verified the kernel transpose identity elementwise, and ran a
  143-pixel simulation of the real `main` loop showing both retracted mutants
  give per-channel diff counts `[143, 143, 0]` and compare equal at every pixel.
  It ran the pooled-table probe against the live JS runtime and read back a
  clobbered float table beside an intact integer one.
- **The Task 2 review** independently reproduced the closure's load-bearing table
  — 28 whole-predicate deletions, all 28 red — enumerated the `ALLOWED_ROW_FIELDS`
  allowlist against its own 34-field universe, and found **sub-clause vacuity the
  implementer's whole-predicate methodology structurally could not see**: two
  combined deletions left the suite green, which meant the entire frozen content
  of `_INDEX_SITES` (3 × 15 fields) and `_BARE_REFERENCES` (3 × 9) was proved by
  nothing but cardinality and a category string.
- **The Task 2 re-review** did its own source surgery in its own scratch copy and
  verified all six isolating clauses fail **exactly one** test each, including
  independent reproduction of the controller's two spot-checks. It rebuilt the
  guard-coverage census from scratch by AST — 33 message fragments, all 33
  asserted as call arguments — and added a decoy proving prose no longer
  satisfies the check. It then swept ~35 further sub-clauses and showed every
  green one still pinned by a static literal elsewhere.
- **The Task 3 review** re-derived every artifact number, re-ran the
  reconstruction, mutation-tested every guard and ledger, proved the §14 arm
  ordering load-bearing by swapping the arms, and confirmed `grep -c Sobel` = 0 in
  both authorities. It **demonstrated the central cost instead of asserting it**:
  swapping the double-element emission for the generic literal path emits
  `static_cast<float>(0.5)` into a `std::array<double, 9>` — the exact
  float-narrowing the whole materialization analysis exists to prevent — and only
  the committed-artifact drift check catches it.
- **The controller** recomputed all four artifact digests, the sorted-key hash and
  every census constant rather than reading them; located each of the three index
  nodes by its own walk of `main`, with no reference to the closure's census, to
  verify the node-identity claim; and spot-checked two of the reviewer's
  combined-deletion clauses in scratch copies, each failing exactly one test and
  it being the isolating one.
- **This task** re-ran the frontier probe on the live 185-row slice rather than
  deriving the new census by arithmetic, re-derived all eight cells of the
  kernel-swap mutant ledger natively from the stored canonical words, and
  re-confirmed the three census corrections by reading the corpus GLSL directly
  (`spookyTicker.glsl:16` `in vec2 v_texCoord;`; `historicPalette.glsl:23` and
  `palette.glsl:28` struct declarations; `bitEffects.glsl:173`
  `const int mask = (1 << BIT_COUNT) - 1;` and `osd.glsl:73`
  `float((row >> (6 - gx)) & 1)`).

### Three method corrections worth carrying forward

1. **"Delete the check" must neutralize behaviour, not delete text.** Textually
   removing a clause also strips its literal from the module source, which trips
   a *second, unrelated* test that does a raw-text search of the module — so the
   clause looks better-guarded than it is. Any project mixing source-text
   assertions with delete-the-check vacuity testing must neutralize
   (`... or True`) rather than delete.
2. **Guard-coverage auditing must use an AST walk, and must render
   `FormattedValue` as `{}`.** Source-text search fails in *both* directions: it
   over-reports by matching docstrings, and under-reports because implicit string
   concatenation means the assertion text never appears contiguously. Dropping
   f-string interpolations while joining `JoinedStr` chunks fabricates guards that
   do not exist — that error produced a false "17 guards, two malformed" census
   which the implementer corrected to 16, all asserted, and turned into a
   regression lock. Coverage must be measured against test literals that are
   **arguments to a call**.
3. **Sanity-check a block splitter on an unchanged pair before trusting a
   mismatch.** The Task 3 reviewer's first splitter glued the trailing `kCatalog`
   block onto the last program and produced a false 183/184 — the same failure
   the previous slice's reviewer hit. The same class of error appeared in this
   task's assembly audit: treating every label as a function boundary truncated
   `pixel` at its first basic block and made an empty pixel scope look clean.
   Both were caught by checking the tool against a case whose answer was already
   known.

## A defect this slice found beyond its own scope

`DEFECTS-FOUND.md` item 5, above. The finding was **widened by measurement before
being recorded**: the oracle task framed it as a normalMap concern, and the
controller measured instead that 32 of 212 corpus programs have a bare `return;`
in `main`, 26 already typed, and that of the 30 emitted bare returns **four are
not preceded by an `output =` assignment**, all in shipped programs. Fixing the
UB alone is not enough — value-initialising `output` removes the undefined
behaviour but still disagrees with JavaScript, which emits the previous pixel's
colour. Faithful behaviour needs output persistence across pixels within a pass,
which is a runtime change to `pass_runner.cpp` and every kernel's output
contract. Ruled record-not-fix: far outside a slice whose job is to admit const
file-scope arrays.

## Oracle independence, re-verified rather than assumed

The property that both previous slices broke — a `--check` gate that only passes
from the exact machine-specific temp directory that produced it — was fixed at
the root, and it was re-verified here on a **fresh snapshot at a path this slice
had never used** (`cp -a` including `.git`, from the live checkout at
`4834b0144ee0524588144a482cca0067b15f68ec` with a clean worktree):

| Package | `--check` from a fresh snapshot | `--check` against the live checkout |
| --- | --- | --- |
| `normalmap_oracle_generator.mjs` | exit 0 | exit 1, "`--cpu-root` must be an immutable snapshot, never the live noisemaker-for-cpu checkout" |
| `shape_oracle_generator.mjs` | exit 0 | exit 1, same refusal |
| `shapes183_oracle_generator.mjs` | exit 0 | exit 1, same refusal |

`generate_normalmap_native_oracle_include.py --check` exits 0 and `--self-test`
reports **ok (77 checks)**, each with a message assertion. The materializer
re-derives, rather than trusts, every surface and texture digest, every binding's
word-versus-value agreement, each case's route label, every control's verdict,
ledger disjointness twice — once from the document and once from its own frozen
table — the transpose identity by digest equality, the kernel-census superset
relation, and the round, narrowing and re-evaluation invariance totals.

## Deferred, with reasons

- **A stale native census was red on arrival.** Task 3 added the row and left
  `typed_slice_catalog_is_exactly_one_hundred_eighty_six_sorted_keys_…` asserting
  186 catalog entries against a catalog that now has 187, so the native binary
  failed before this task touched anything. Repaired here, since the native tests
  are this task's file: renamed to `…_one_hundred_eighty_seven_…`, count bumped,
  and `filter/normalMap:normalMap` inserted in sorted position between
  `filter/mosaicTiles:mosaicTiles` and `filter/normalize:apply`. Recorded because
  the lesson generalizes: **a slice that adds a typed row must budget for the
  native catalog census, not only the Python ones.**
- **Two byte counts in `task-4-report.md` are stale** — it lists the oracle JSON
  at 434,479 bytes and the report at 23,881, where the shipped files are 440,152
  and 27,302. The sidecars and `--check` agree with what is on disk, so the
  package is self-consistent; only the report's table is wrong. This record uses
  the measured values.
- **`DEFECTS-FOUND.md` item 5 is now one slice stale in its wording.** It reads
  "`filter/normalMap:normalMap` will be the fifth when it lands" and counts "the
  30 bare `return;` statements in `src/typed_generated/typed_slice.cpp`". It has
  landed, and the count is now **31** in the working tree against 30 at HEAD;
  `typed_66::pixel` carries the guard with no preceding `output =`, exactly as
  predicted. Not corrected here because that document belongs to the task that
  wrote it, and rewriting another task's finding is not this one's call.
- **The `statement_index` `function is None` branch** has a positive test that
  plants a read inside `CHANNEL_CAP`'s initializer, added in Task 2 fix round 2;
  the branch is no longer correct-by-inspection-only.
- **The mechanism unlocks one program.** `osd` shares the const-array sub-shape
  but is gated behind JS-Number bitwise semantics and carries an `int[80]` table
  rather than a nine-element one, so this closure cannot reach it by adding a
  key. The mechanism's value is as the **precondition** for the array form of the
  mutable-global bucket (`cellRefract`, `kaleido`, `effects`), which is where the
  remaining density is.
- **The publication-gate scope item stands.** Re-measured at acceptance:
  `docs/port-engineering/` holds **1,891 tracked files and 39 MB of a 71 MB
  working tree**, of which **115** are tracked `.log` / `.err` / `.orig` files;
  repo-wide the figure is **117**, the extra two being `CMakeLists.txt.orig` and
  `screen.err` at the root. (The pre-flight ledger records 117 under
  `docs/port-engineering/` specifically — that split is the only discrepancy.)
  These are per-task scratch that was committed rather than retained product.
  Recorded, not acted on; narrowing or widening the requested scope is not this
  task's call, and it belongs to the final review and publication task.
