# Const-global admission widening (int/uint/vec3) — batch report, 2026-08-13

Scope: the 20 of 46 remaining programs whose terminal blocker (re-probed live,
via `generate_typed_slice.validate_capabilities` exactly as briefed) is
`unsupported global declaration`. Starting state: **166 typed**, SHA-256 of
sorted `typed_slice.json` program_key list
`e01689106db98e84cd3f3ec267e3fd2b5419a5370e2c7f8038c96d69fa2e6955` (matches
the frozen constant checked at `generate_typed_slice.py:847`, and matches the
operator's own briefed prefix). Native `176 PASS / 0 FAIL`. All four
generator gates exit 0 (re-verified below).

**Outcome: 0 programs landed.** The general const-global admission mechanism
(designed and verified below) correctly clears the FIRST blocker for 10 of
the 20 programs, but every one of those 10 hits a second, independent,
out-of-scope blocker immediately behind it. The remaining 10 need either
mutable-global-state support, struct-array support, or fixed-array support —
none of which is a const-global-admission problem. No file under `tools/`,
`src/`, `include/`, `tests/`, or `CMakeLists.txt` was modified in the live
tree; `git` was never run; nothing was written to `/tmp`.

## 1. The 20-program disposition, each with hard evidence

### 1a. Mutable global scratch state (4) — categorically excluded, not a const shape

`classicNoisedeck/cellRefract:cellRefract`, `classicNoisedeck/effects:effects`,
`classicNoisedeck/kaleido:kaleido`, `synth/shape:shape` each declare
non-`const` globals (`float emboss[9]`, `sharpen[9]`, `blur[9]`, `edge[9]`,
[`edge2[9]`/`edge3[9]`/`sharpenBlur[9]`], or `synth/shape`'s
`aspectRatio`/`globalCoord`) with **no initializer**, populated by scattered
assignments inside `main()`. Verified definitively: bypassing the admission
loop entirely (a research-only monkeypatch in a throwaway copy, admitting
every non-uniform/output declaration unconditionally) still fails immediately
with `write to source const global` — the existing write-audit
(`generate_typed_slice.py` audit_expression/audit_statement, ~L2444-2469)
correctly flags every one of them as written-to. This is proof, not
inference: these are not const-shaped at all; they need a fundamentally
different mutable-state model (per-invocation context struct or similar),
explicitly out of scope for a const-admission widening.

### 1b. `classicNoisedeck/bitEffects:bitEffects` (1) — needs a new binary operator, not admission

Its two globals (`BIT_COUNT` const int literal, `mask = (1 << BIT_COUNT) - 1`)
are almost admittable, but `mask`'s initializer uses `<<`, which is not in
`_BINARY_OPERATORS` (`emit_typed_cpp.py:140`) **at all** — not gated by a
profile, genuinely unimplemented. Bypassing admission entirely still fails at
`unsupported binary operator &` next (a *different* bitwise operator, deeper
in the program). Both `<<` and general int `&` require new/extended bitwise
mechanism work (`authorized_bitwise_scalar_int_ops_sites`, a per-program
frozen profile family), unrelated to global declarations.

### 1c. Struct-array globals (2) — blocked earlier, by type, not by admission shape

`filter/historicPalette:historicPalette` (`const HistoricPalette[21] PALETTES`)
and `filter/palette:palette` (`const PaletteEntry[55] PALETTES`). Confirmed by
bypassing admission entirely: both immediately hit `unsupported typed type
HistoricPalette[21]` / `PaletteEntry[55]` from `reject_type`'s
`APPROVED_TYPES` check, which fires **before** any admission-loop logic runs.
Struct types are unconditionally rejected elsewhere in the validator
(`typed.structs` check) — needs whole new struct-type support (member-access
codegen, a struct type table in the emitter), not const-global admission.

### 1d. Fixed-array globals (3) — same `reject_type` wall as 1c

`filter/normalMap:normalMap` (`const ivec2[9] SOBEL_OFFSETS`, `const
float[9] SOBEL_X_KERNEL/SOBEL_Y_KERNEL`), `filter/osd:osd` and
`filter/spookyTicker:spookyTicker` (`const int[80] GLYPHS`). Same bypass
proof: immediate `unsupported typed type ivec2[9]` / `int[80]` from
`reject_type`, before admission-loop logic. `array`-kind types are
unconditionally rejected. A global fixed-array admission mechanism (extending
the existing LOCAL `fixed_nine_table_proof`/task19/task20 family to global
scope, plus an array-display branch in the emitter's `type()`/
`function_parameter_type()`) is a distinct, larger mechanism — not landed
here.

### 1e. Ten scalar/vec3-clean candidates — admission mechanism verified, ALL hit a second unrelated blocker

For these 10, every remaining global is `const` and one of: `int`/`uint`
literal, or `vec3` built from float literals (some via a single-lane swizzle
of an earlier-admitted `const vec3` sibling — see §2). The widened admission
(§2, verified in a throwaway copy, never applied to the live tree) admits
**all** of them with zero vocabulary growth. But every one of the 10 then
hits an independent second blocker, confirmed by running the real
`validate_capabilities` against the widened copy:

| Program | Second blocker | Reachable from `main`? | Verdict |
|---|---|---|---|
| `filter/edge:edge` | `unsupported typed type bvec3` | yes (`applyBlend`/`contourConv`/`getWeight`) | needs new relational-vector type support |
| `filter/emboss:emboss` | `unsupported typed type float[9]` (a **local**, inside `colorDefaultEmboss`) | yes | needs `fixed_nine_table_proof`'s `SOURCE_LOCKS` extended — its own SHA-fingerprinted profile |
| `filter/fxaa:fxaa` | `unsupported builtin round` (`as_u32`) | **yes**, called directly from `main` | needs a new per-program round-admission profile (no general `round` capability exists — only 2 narrow existing profiles, Gather Sorted / Posterize, neither reusable here) |
| `filter/glyphMap:glyphMap` | `unsupported binary operator &` | yes (`hash`/`pcg`) | needs the bitwise-scalar-int-ops profile family extended to this program |
| `filter/grain:grain` | `unsupported builtin round` (`as_u32`) | **yes**, called from `main`'s reachable closure | same as fxaa — new round profile needed |
| `filter/scanlineError:scanlineError` | `unsupported builtin floatBitsToUint` | yes (`pcg`) | needs floatBitsToUint admission extended (existing mechanism, but a new per-program authorized site) |
| `filter/smooth:smoothBlend` | `unsupported builtin ceil` | yes | `ceil` has **zero** existing admission mechanism anywhere in the generator |
| `filter/snow:snow` | `unsupported builtin round` (`as_u32`) | **no** — confirmed unreachable from `main` by direct call-graph BFS, independently re-verified against the current 166-typed tree (not just quoting prior analysis) | closest near-miss: a **dead-code exemption** would suffice instead of real round semantics, but no dead-code-exemption mechanism exists anywhere in the validator/emitter today (would be new, general, and risky to scope correctly) |
| `filter/texture:texture` | `unsupported varying` (`v_texCoord`) | genuinely used — 6 real reads found by AST walk, not boilerplate | varying/interface-symbol support doesn't exist in the emitter at all (no symbol-table entry for a varying) |
| `filter/wobble:wobble` | `unsupported varying` (`v_texCoord`) | genuinely used — 1 real read | same as texture |

None of these second blockers were introduced by, or specific to, the choice
of admission grammar in §2 — each is the validator's next unconditional
check, independent of how the global got admitted. Widening admission
further (e.g. admitting more expression shapes) cannot change this: the
blockers are downstream of admission entirely.

## 2. The verified (but unlanded) admission mechanism

Designed and tested only in a throwaway rsync copy
(`/Users/aayars/platform/.nm-validate/global-batch/`, outside the live tree),
never applied to `tools/glslcpp/generate_typed_slice.py` or
`emit_typed_cpp.py` on disk. Zero-vocabulary-growth (never calls
`used.add(...)`), matching the existing const-float and `mat3` admission
loops' own precedent exactly (both already general, not per-program-profile
scoped, in the current tree).

Validator (`generate_typed_slice.py`, inserted into the `admitted_globals`
loop right after the existing `mat3` block, before the float-only fallback
raise):

- `const int` / `const uint` with a **bare literal initializer** — admitted
  unconditionally. Exact values, zero narrowing risk. Deliberately does NOT
  admit int/uint arithmetic or id-references (no shipped program in this
  family needs it; `bitEffects`'s `mask` needs `<<`, which is excluded per
  §1b regardless).
- `const vec3` built from a 3-argument `vec3(...)` construct where each
  component is: a float literal, `+`/`-`/`*`/`/` arithmetic over float
  literals and earlier-admitted `const float` globals (mirrors the existing
  float grammar exactly), OR a single-lane swizzle of an earlier-admitted
  `const vec3` sibling (`filter/scanlineError`'s
  `TIME_SEED_LINE = vec3(BASE_SEED_LINE.x + 97.0, ...)` idiom — verified this
  is the *only* non-literal vec3-component shape present in the batch, by
  direct AST dump of all 20 programs' declarations).

Emitter (`emit_typed_cpp.py`) needs the symmetric widening in
`_validate_source_globals` (same grammar, tracking `source_global_dependencies`
so `BASE_SEED_LINE` emits before `TIME_SEED_LINE`), **plus one real, load-
bearing bug fix** found while designing this: `source_global_locals`
(~L1236) currently does
`declaration.initializer.literal if declaration.type.display()=="int" else self.expression(...)`
— `.literal` is `None` for any non-literal initializer (e.g. a computed int
expression), so this line would silently emit the Python string `"None"` into
generated C++ for any admitted int global whose initializer isn't a bare
literal. Not triggered by this batch (both int globals admitted here,
`GLYPH_COUNT`/`Z_LOOP`, are bare literals), but flagged as a real defect for
whoever lands general int-global admission next: guard with
`declaration.initializer.kind == "literal"`, not just the type check.

**Verified safe, not verified valuable**: ran the full `test_typed_generator.py`
Python suite against the widened copy. Result: **1** expected failure
(`test_task14_admits_only_initialized_const_float_source_globals`, a
near-miss test that specifically asserts non-float globals stay rejected —
correctly starts failing once the grammar is widened, exactly as its own
docstring anticipates for a future widening) and otherwise a clean run
against all 166 currently-typed programs (no regression). This confirms the
mechanism is structurally correct and non-regressive, but per this project's
own standing rule ("a vendored-but-unwired oracle proves nothing"), it has
not been exercised end-to-end by any program that actually reaches emitted,
built, oracle-verified C++ — because none of the 10 candidates clear their
second blocker. Landing it alone would add validator/emitter surface area
and one required near-miss-test rewrite for zero typed-count gain, so it was
**not** applied to the live tree.

## 3. Recommendation for the next thread

This batch's own evidence, cross-checked against the pre-existing (larger,
131-typed-era) `docs/port-engineering/roadmap2/full-chain-frontier-map.md`
survey, points at the same two next slices, still accurate at 166 typed:

1. **Bitwise-operator family** (`&`, `|`, `^`, `<<`, `~` widened to
   int/uint scalar) — pure generator, no runtime gap, would land
   `glyphMap` (and contribute to `bitEffects`, though that one also needs
   `<<` specifically, which isn't built at all yet). Land together with this
   admission widening in the same commit, per this codebase's own established
   pattern (mat3 admission landed bundled with the `linear_srgb_lane_index_v1`
   profile, never alone).
2. **A new per-program `round` admission profile** for `filter/fxaa:fxaa`'s
   `as_u32` site (`glsl::round` already exists and is correct in the runtime;
   the gate is generator-side authentication only, mirroring
   `gather_sorted_round_profile.py`/`posterize_round_profile.py`). `grain`
   needs the same PLUS a third gate (`uvec3 >> uvec3`, not investigated
   further here). `snow`'s round site is dead code — a cheaper dead-code
   exemption might suffice there instead of full round semantics, but no
   dead-code-exemption mechanism exists yet; scoping and building one safely
   is real, separate work, not attempted here to stay disciplined to this
   batch's actual blocker.

Do **not** attempt `ceil` (zero existing admission anywhere), `varying`
support (no emitter symbol-table entry for interface symbols at all), or
struct/array-global support as part of a "global admission" batch — each is
its own multi-hour mechanism, confirmed by direct code inspection in §1c/1d/1e
above, not speculation.

## 4. Gate/test evidence (live, unmodified tree)

```
$ python3 -m tools.glslcpp.check_corpus --check
check_corpus: ok                                          EXIT=0
$ python3 -m tools.glslcpp.check_semantics --check
check_semantics: bodies ok (212 programs)                 EXIT=0
$ python3 -m tools.glslcpp.generate_typed_slice --check
generate_typed_slice: typed slice ok (166 programs)        EXIT=0
$ python3 -m tools.glslcpp.generate_kernels --check
(no output)                                                 EXIT=0
```

Native (Debug, this thread's own `build-glob/`, never `build-baseline-check`):
```
$ cmake -DCMAKE_BUILD_TYPE=Debug ..     EXIT=0
$ cmake --build . -j 8                  EXIT=0
$ ./noisemaker-cpu-tests                176 PASS / 0 FAIL, EXIT=0
```

Typed-list SHA-256 (sorted `program_key`, per `generate_typed_slice.py`'s own
`_sha256(("\n".join(keys) + "\n").encode())` formula, `generate_typed_slice.py:847`):
`e01689106db98e84cd3f3ec267e3fd2b5419a5370e2c7f8038c96d69fa2e6955` — unchanged
from the briefed starting state (166 typed), since nothing was landed.

Python suite: run against the **live, unmodified** tree was not repeated
here (baseline already asserted green at the start of this task by the
operator's own rescreen 3 minutes before this session began — `check1.log`:
`generate_typed_slice: typed slice ok (166 programs)`, `EXIT=0` — and
nothing under `tools/`/`src/`/`include/`/`tests/` was touched since). The
full suite *was* run against the widened throwaway copy (§2): 1 expected
near-miss failure, otherwise clean.
