# Bitwise-operator family: implementation precompute

Read-only analysis. Corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`
(confirmed live in `tools/glslcpp/typed_slice.json` at analysis time:
`revision` field, and `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/`).
State at analysis time: **131 typed / 212 total / 81 unported**
(`tools/glslcpp/typed_slice.json` has 131 `programs` entries;
`tools/glslcpp/corpus/.../manifest.json` has 212 `programs` entries).

All scripts referenced below were written to and run from
`docs/port-engineering/bitops/` and only *read* files under
`.`. No file under
`noisemaker-for-cpp` or `noisemaker-for-cpp/../noisemaker-for-cpu` was
modified, and no `git` command was run in either tree.

Key scripts (kept for reproducibility):
- `docs/port-engineering/bitops/bitops_ast_scan.py` — real
  parse+analyze (`tools/glslcpp/frontend.parse_program` /
  `analyze_program`) over every unported key, with a call-graph BFS from
  `main` for reachability and a walk of the typed AST for bitwise/shift
  sites. Output: `bitops_ast_scan.json`.
- `docs/port-engineering/bitops/bitops_scan.json` — an earlier,
  cruder token-level pass (kept only to show the naive-grep numbers this
  document corrects).

## 0. Baseline: what's already admitted (read before anything else)

Contrary to a naive grep, **scalar/vector bitwise support already exists**
for a narrow shape. `tools/glslcpp/typed_slice.json` capability list (44
entries) includes `uint-vector-bitwise`, and `binary_operators` already
contains `>>`, `^` with `assignment_operators` containing `^=`
(`tools/glslcpp/typed_slice.json`, top-level `capabilities` /
`binary_operators` / `assignment_operators` arrays).

The validator (`tools/glslcpp/generate_typed_slice.py:2013-2174`) admits,
**generically, for any program**, exactly:

| Shape | Validator citation | C++ emission |
|---|---|---|
| `uvecN ^ uvecN` (same uvec type both sides) | `generate_typed_slice.py:2026-2047` | `glsl::bitwise_xor(...)` — `emit_typed_cpp.py:1293-1297` → `include/noisemaker/glsl_types.hpp:206-213` (element-wise `^` on `Vec<N,uint32_t>`) |
| `uvecN >> uint` (vector left, **scalar** uint shift count) | `generate_typed_slice.py:2022-2025` | `glsl::shift_right(...)` — `emit_typed_cpp.py:1267-1271` → `include/noisemaker/glsl_types.hpp:196-204` (logical/zero-fill shift, count masked `& 31U`) |
| `uvecN ^= uvecN` (compound assign, same uvec type) | `generate_typed_slice.py:2169-2174` | same `bitwise_xor` path |

Everything else — scalar `int`/`uint` `&`,`|`,`^`,`<<`,`>>` (except two
narrow **identity-locked, not-in-vocabulary** exceptions below), unary
`~`, `&=`, `|=`, `<<=`, `>>=`, and vector `<<` or vector-vector `>>` — is
rejected today (`APPROVED_BINARY_OPERATORS`/`APPROVED_ASSIGNMENT_OPERATORS`
module constants equal exactly the `typed_slice.json` lists above; no
branch in `generate_typed_slice.py` or `emit_typed_cpp.py` handles `&`,
`|`, `<<`, or unary `~` at all).

Two additional **identity-locked, per-program** exceptions exist and add
nothing to the frozen vocabulary (per the project's established escape
hatch pattern, constraint #1):
- `tools/glslcpp/frontend/perlin_scalar_uint_xor_profile.py` — authenticates
  exactly two scalar `uint ^ uint` sites in `synth/perlin:perlin`
  (already typed), proven **unreachable** dead code at `DIMENSIONS=2`.
- `tools/glslcpp/frontend/caustic_word_hash_profile.py` — authenticates one
  `floatBitsToUint` ingress plus three scalar `uint ^ uint` sites in
  `classicNoisedeck/caustic:caustic`. **`caustic` is still unported** (not
  in the 131) — see §1c, this module's own reachability claim is
  contradicted by independent analysis below.

Runtime coverage (`include/noisemaker/glsl_types.hpp`): only
`shift_right` (logical, uint32, count `& 31U`) and `bitwise_xor` (uint32)
exist. Nothing for `&`, `|`, unary `~`, `<<`, or a **signed/arithmetic**
right shift.

## 1. The frontier: exact program counts

Computed with `bitops_ast_scan.py`: for every one of the 81 unported keys,
parse + semantically analyze with the *exact* metadata default defines
(`tools/glslcpp/check_semantics.py:_metadata_defaults`, the same helper
`tools/glslcpp/check_corpus`/the project's own `task31_frontier_scan.py`
precedent uses), walk the typed AST for `&`,`|`,`^`,`<<`,`>>`,`&=`,`|=`,
`^=`,`<<=`,`>>=`,`~` nodes, and BFS the real call graph from `main` to
mark each site reachable or not.

**32 of the 81 unported programs contain at least one bitwise/shift AST
node.** They split into four groups — the first is a trap a naive grep
would miss:

### Group 0 — NOT actually blocked by bitwise (13 programs, excluded from a/b/c)

All bitwise sites in these programs are the shared `pcg(uvec3 v)` PRNG's
`v ^= v >> uint(16);` idiom (e.g.
`tools/glslcpp/corpus/.../sources/classicNoisedeck/cellNoise/cellNoise.glsl:57`),
which is **already fully inside the admitted `uint-vector-bitwise` shape**
(`^=` on matching uvec types; `>>` with scalar uint count). Naive-grep
census (`bitops_scan.json`) would have miscounted all 13 as "blocked on
bitwise"; the real (per-program) validator first-error is unrelated:

| Program | Real first blocker (`validator_first_error`, `generate_typed_slice.py`) |
|---|---|
| `classicNoisedeck/cellNoise:cellNoise` | unsupported global declaration |
| `classicNoisedeck/cellRefract:cellRefract` | unsupported global declaration |
| `classicNoisedeck/colorLab:colorLab` | unsupported global declaration |
| `classicNoisedeck/glitch:glitch` | unsupported typed type `mat4` |
| `filter/grime:grime` | unsupported varying |
| `filter/lensWarp:lensWarp` | unsupported builtin `dFdx` |
| `filter/lightLeak:lightLeak` | unsupported counted-for program proof |
| `filter/octaveWarp:octaveWarp` | unsupported builtin `dFdx` |
| `filter/scanlineError:scanlineError` | unsupported global declaration |
| `filter/warp:warp` | unsupported builtin `dFdx` |
| `filter/wobble:wobble` | unsupported global declaration |
| `filter/zoomBlur:zoomBlur` | unsupported counted-for program proof |
| `synth/gabor:gabor` | unsupported counted-for safety charge |

None of these belong in a future bitwise-family task.

### Group (c) — bitwise use is unreachable dead code at authorized defaults (5 programs)

Verified via real call-graph BFS from `main`, then **hand-confirmed by
direct #if/#else tracing** on `classicNoisedeck/caustic:caustic` (the
riskiest one, since a *prepared* identity profile in-tree claims the
opposite — see the flag below):

| Program | Dead function(s) | Why unreachable at defaults |
|---|---|---|
| `classicNoisedeck/caustic:caustic` | `pcg`, `randomFromLatticeWithOffset` | `value()` dispatches on `NOISE_TYPE` (`sources/classicNoisedeck/caustic/caustic.glsl:409-438`); metadata default `NOISE_TYPE=10` (`metadata.json`, `classicNoisedeck/caustic` → `interp` param, default `10`) selects the `simplexValue` branch (`caustic.glsl:420-422`), never `constant`/`constantOffset` (only reachable via `NOISE_TYPE` 0 or the `else` branch for 1/2, `caustic.glsl:410-411,427-438`), which are the only callers of `randomFromLatticeWithOffset` (`caustic.glsl:240,246`) |
| `classicNoisedeck/effects:effects` | `pcg` | default `EFFECT=0` (`effects.glsl:19-20`) doesn't reach the `prng`-consuming branch |
| `classicNoisedeck/moodscape:moodscape` | `pcg`, `randomFromLatticeWithOffset` | same lattice-hash dead-branch shape as caustic |
| `classicNoisedeck/noise:noise` | `pcg`, `constantFromLatticeWithOffset` | same shape |
| `synth/noise:noise` | `pcg`, `constantFromLatticeWithOffset` | same shape |

**Flag requiring operator attention before any work on `caustic`:**
`tools/glslcpp/frontend/caustic_word_hash_profile.py:9-12` states in its
module docstring: *"Unlike Perlin's scalar XOR closure (Task 27),
Caustic's XORs are live, reachable, rendered code: their results reach
`fragColor`."* Independent reachability analysis in this document
(cross-checked by direct source reading of
`sources/classicNoisedeck/caustic/caustic.glsl:108-439`, not just the
AST-BFS script) finds the opposite: at the exact metadata-default
`NOISE_TYPE=10`, the host function `randomFromLatticeWithOffset` (and the
`floatBitsToUint`/XOR closure inside it) is **not called from `main`**.
This is exactly the class of mistake constraint #2 warns cost "a full
implementation cycle" previously. **This is UNVERIFIED beyond my own
analysis** — I could not find a second, independent confirmation inside
the repo that resolves the contradiction (e.g. a different intended
define map for this profile). Do not consume
`caustic_word_hash_profile.py` at face value; re-derive reachability
before relying on it.

### Groups (a)/(b) — the genuine frontier: 14 programs

| Category | Count | Programs |
|---|---:|---|
| **(a) blocked ONLY on bitwise/shift** | **1** | `synth/bitwise:bitwise` |
| **(b) blocked on bitwise AND something else (named)** | **13** | see table below |

**(a) `synth/bitwise:bitwise`** — full source is 91 lines
(`sources/synth/bitwise/bitwise.glsl`), a purpose-built demo of runtime
uniform-driven scalar signed-`int` `&`,`|`,`^`,`~` (xor/and/or/nand/xnor
dispatch in `bitOp()`, lines 34-43) plus two more `^` in `main()` (lines
68-69). Confirmed via both the validator's own first-error
(`synth/bitwise:bitwise:34:27: unsupported binary operator ^` —
`generate_typed_slice.py`, the very first thing the AST walk trips on)
**and** a full manual read of the source: no arrays, no loops, no
matrices, no structs/UBOs/varyings/samplers, no global mutable state (only
`const float PI`, already an allowed global-const-float per
`generate_typed_slice.py:1926`). Everything else it uses (`if`/`else`
dispatch, `mix`/`clamp`/`fract`/`abs`/`cos`/`sin`, `int()`/`float()`
constructors) is already in the 44-capability vocabulary. This is the
cleanest possible first target.

**(b) — 13 programs, each with a *named* second blocker.** "First
blocker" is the validator's actual raised error (`validator_first_error`
in `bitops_ast_scan.json`); several report a non-bitwise error first only
because the AST walk reaches that construct earlier in traversal order —
the additional blockers below were confirmed by directly inspecting
`typed.declarations` / loop shape, not inferred from the error text alone:

| Program | Bitwise blocker | Other confirmed blocker(s) |
|---|---|---|
| `classicNoisedeck/bitEffects:bitEffects` | 3× scalar `uint^uint` in `randomFromLatticeWithOffset` (+6 more scalar-int `&`,`\|`,`^`,`<<` sites in `modi`/`and`/`or`/`xor` helper functions, `bitEffects.glsl:173-192`, dead at `MODE=1` default — see caveat below) | (1) global `const int BIT_COUNT`/`mask` not in `SOURCE_GLOBAL_LITERAL_INT_KEYS` whitelist → `unsupported global declaration` at normalized line 129 (`generate_typed_slice.py:1926`); (2) `floatBitsToUint` used twice in `randomFromLatticeWithOffset` (`bitEffects.glsl:121-122`), not admitted outside the `caustic` identity closure |
| `classicNoisedeck/kaleido:kaleido` | 3× scalar `uint^uint` in `randomFromLatticeWithOffset` | (1) same global-const-int gap (`kaleido.glsl` `BIT_COUNT`-style consts, error at normalized line 33); (2) `floatBitsToUint` (`kaleido.glsl:175`); (3) **five global `float[9]` arrays** `emboss`/`sharpen`/`blur`/`edge`/`edge2` (convolution kernels) — a materially different, bigger blocker (global-array family, not scalar-int) |
| `classicNoisedeck/shapeMixer:shapeMixer` | 3× scalar `uint^uint` in `randomFromLatticeWithOffset` | (1) global-const-int gap; (2) `floatBitsToUint` (`shapeMixer.glsl:422`); (3) **four global `const mat3`** (`fwdA`/`fwdB`/`invB`/`invA`) — matrix-global blocker, unrelated family |
| `classicNoisedeck/shapes:shapes` | 3× scalar `uint^uint` in `randomFromLatticeWithOffset` | same three: global-const-int, `floatBitsToUint` (`shapes.glsl:133`), four global `const mat3` |
| `synth/shape:shape` | 3× scalar `uint^uint` in `randomFromLatticeWithOffset` (this variant has **no** `floatBitsToUint` — uses `uint(xi)` directly, `shape.glsl:80-102`) | **mutable (non-const) globals** `aspectRatio: float`, `globalCoord: vec2` — a structurally different, larger blocker (writable global state, not just an unauthenticated constant) |
| `filter/glyphMap:glyphMap` | `int & int`, `int >> int` in `glyphPixel()` (`glyphMap.glsl:287`) | global `const int GLYPH_COUNT` (`glyphMap.glsl:193`) not in the whitelist; usage is pure arithmetic (`% `, clamp), not a loop bound, so this is a cheap in-pattern extension, not a new mechanism |
| `filter/grain:grain` | **vector-vector** `uvec3 >> uvec3` in `pcg3d()` (`grain.glsl:43`, right operand is `uvec3(16u)` — see §2 nuance) + 3× scalar `uint^uint` in `random_from_cell_3d` (`grain.glsl:52-54`) | global `const uint` declarations (`CHANNEL_COUNT`, `INTERPOLATION_*`, `BASE_SEED`, `grain.glsl:12-17`) — the existing whitelist mechanism (`SOURCE_GLOBAL_LITERAL_INT_CAPABILITY`) only covers `type.display()=="int"`; it has **no `uint` variant today** (`generate_typed_slice.py:1910-1915`, `declaration.type.display() == "int"` check) |
| `filter/median:median` | `&`,`\|`,`<<`,`>>` on `uint`/mixed `uint`,`int` operands in `packRecordMajor`/`packRecordBlue`/`unpackRecordRgb` (`median.glsl:15-28`) | (1) `unsupported counted-for program proof` fires first — the sort loop is a data-dependent nested `while` insertion/quickselect, not a provable counted-for; (2) `packHalf2x16`/`unpackHalf2x16` are not in `_BUILTINS` at all (`generate_typed_slice.py:212-219`) — a **third**, independent blocker |
| `filter/osd:osd` | `uint^uint`/`uint>>uint` in a **local, non-canonicalized** scalar `pcg`/`hash2`/`hash3` (`osd.glsl` ~lines 54-63), plus `int&int`/`int>>int` in `sample_glyph` (`osd.glsl:72`) and `main` (`osd.glsl:98`) | global `const int[80] GLYPHS` array (`osd.glsl:24`) plus scalar `const int` GLYPH_W/H/BASE_SCALE/BASE_PADDING — a **global int array**, materially bigger than the existing scalar-only whitelist mechanism |
| `filter/spookyTicker:spookyTicker` | `uint^uint`/`uint>>uint` in local `hash_mix` (`spookyTicker.glsl:48-52`), `int&int`/`int>>int` in `sample_glyph` (`:63`), `uint&uint`/`uint^uint` in `ticker_row_mask` (`:69,78`) | same `const int[80] GLYPHS` global-array pattern as `osd` |
| `filter/texture:texture` | `uint^uint`/`^=` in `fast_hash`/`hash_uint` (`texture.glsl:59-73`) | global `const int Z_LOOP` (`texture.glsl:35`), pure arithmetic use (`%`, not a loop bound) — cheap whitelist extension, same pattern as `glyphMap` |
| `filter/dither:dither` | `int&int` in `getBayer8x8`/`getDitherThreshold` (`dither.glsl:57-58,204,206`) | `unsupported counted-for program proof` fires first — Floyd–Steinberg-style apron/jitter error-diffusion loop with dynamic `FS_APRON_MIN`/`MAX`-derived bounds, not a provable counted-for |
| `synth/testPattern:testPattern` | `int&int`, `int>>int` in `sampleGlyph` (`testPattern.glsl:30`) | `unsupported counted-for program proof` fires first — a plain `for(i=0;i<3;i++)` digit-extraction loop writing into a local `int digits[3]` array; blocked by the array-of-locals shape, not the loop itself per se |

**Caveat on `bitEffects`'s six helper functions** (`modi`, `and`, `or`,
`xor` at `bitEffects.glsl:173-192`): these are defined unconditionally
(no `#if` guard) but my AST-BFS marks them **unreachable** at `MODE=1`
defaults (`bitops_ast_scan.json`, `classicNoisedeck/bitEffects:bitEffects`
→ only 3 sites listed, all inside `randomFromLatticeWithOffset`, none
inside `modi`/`and`/`or`/`xor`). This matches
`post-scalar-bitwise-frontier-audit.md`'s independent claim ("Four
resolved calls remain after preprocessing at the exact defaults:
`and(int,int)`, `or(int,int)`, `xor(int,int)`, and `xor(float,float)`")
**only if** that audit means *called from a reachable path*, not merely
*present in the source* — my BFS finds none of the six helper functions
called from `main` at `MODE=1`. **This is a second contradiction with a
prior in-repo document, flagged UNVERIFIED**: either the audit document
used different assumed defaults, or its "resolved calls" language refers
to something other than true `main`-reachability (e.g. reachability
counting through an as-yet-unauthored `MODE=0` code path, or dead-code
proof intent rather than live-code intent). Re-verify before scoping
`bitEffects` work around those four "resolved calls" — the reachable
scalar-bitwise surface I can confirm for `bitEffects` today is only the
three `uint^uint` sites in `randomFromLatticeWithOffset`.

## 2. Exact AST shapes needed (Step 2)

Aggregated over the 14 frontier programs' **reachable, not-yet-admitted**
sites (`bitops_ast_scan.json`, counts from a direct tally):

| Shape | Count | Where |
|---|---:|---|
| `uint ^ uint -> uint` | 28 | shared lattice-hash `randomFromLatticeWithOffset`/`random_from_cell_3d` family, local `pcg`/`hash2`/`hash3`/`hash_mix`/`ticker_row_mask`/`fast_hash` hash helpers |
| `uint ^= uint -> uint` | 6 | `filter/texture:texture` `fast_hash`/`hash_uint` |
| `int & int -> int` | 14 | `dither`, `glyphMap`, `osd`, `spookyTicker`, `testPattern` glyph/mask sampling; `synth/bitwise` `bitOp` |
| `uint & uint -> uint` | 3 | `filter/median` pack helpers, `spookyTicker` `ticker_row_mask` |
| `uint >> uint -> uint` | 9 | `filter/osd`, `filter/spookyTicker`, `filter/texture` local hash helpers |
| `int >> int -> int` | 4 | `glyphMap`, `osd`, `spookyTicker`, `testPattern` glyph bit-sampling |
| `uint >> int -> uint` | 2 | `filter/median` pack/unpack (RHS is an `int` literal shift count, e.g. `major.y >> 16`) |
| `uvec3 >> uvec3 -> uvec3` | 1 | `filter/grain:grain` `pcg3d()`, `grain.glsl:43` |
| `int ^ int -> int` | 4 | `synth/bitwise` |
| `int \| int -> int` | 1 | `synth/bitwise` |
| `uint \| uint -> uint` | 2 | `filter/median` pack/unpack |
| `uint << int -> uint` | 2 | `filter/median` pack/unpack |
| `~int -> int` (unary) | 2 | `synth/bitwise` (nand/xnor) |

**Operand provenance:**
- Scalar-uint-xor sites (`randomFromLatticeWithOffset` family) operate on
  **locally-computed** hash state (`floatBitsToUint(...)`, `uint(int)`
  conversions, integer literals like `0x9E3779B9u`) — never directly on a
  raw uniform.
- `synth/bitwise:bitwise`'s scalar ops operate directly on **runtime
  uniform `int`s** (`operation`, `mask`, `seed`, `colorOffset` —
  `bitwise.glsl:10-18`) — the strongest test of true int32 wraparound
  since these can be any value the UI slider produces, not just
  well-formed hash state.
- Shift-count provenance: always either an integer **literal**
  (`uvec3(16u)` in `grain`, `16` in `median`, `6-gx`/`bitIndex` computed
  locals in `osd`/`spookyTicker`/`testPattern` glyph sampling) — no site
  in the frontier uses a uniform-driven, unbounded shift count.
- No frontier site feeds a bitwise result into `intBitsToFloat`/
  `uintBitsToFloat` (only `floatBitsToUint` appears, as an *input* to the
  xor chain, in `bitEffects`/`kaleido`/`shapeMixer`/`shapes`, and as dead
  code in `caustic`/`moodscape`/`noise`/`synth/noise`).
- Signed vs unsigned: both signed-`int` (`synth/bitwise`,
  `dither`/`glyphMap`/`osd`/`spookyTicker`/`testPattern` glyph-bit
  sampling) and unsigned-`uint` (the lattice-hash family, `median`'s
  half-float packing) families are present in roughly even measure — this
  is not a scalar-int-only or uint-only extension.

## 3. Semantics hazards, with citations (Step 3)

### Hazard #1 (highest severity): JS's `>>` is ALWAYS signed/arithmetic — GLSL `uint`-ness is invisible to the transpiler unless the whole function matches a hand-written canonical idiom

`glsl-transpiler`'s operator table
(`noisemaker-for-cpu/node_modules/glsl-transpiler/lib/operators.js:12-34`)
maps GLSL `<<`/`>>`/`&`/`|`/`^` to names (`lshift`/`rshift`/`bitand`/
`bitor`/`xor`) used only for descriptor bookkeeping; the actual scalar
codegen fallback (`operators.js:298-370`, specifically the generic
`opResult = left + ' ' + operator + ' ' + right` branch at lines 349-362,
reached because none of the special-cased `+`/`-`/`*`/`--`/`++`/`!`/`~`
branches match) emits the **literal GLSL operator text as JS syntax**,
with **zero type-based distinction between GLSL `int` and `uint`**. Since
JS has only one native signed `>>` (sign-propagating/arithmetic) and one
native unsigned `>>>` (zero-fill/logical), and the transpiler never emits
`>>>` from this generic path, **every custom/bespoke `uint`-typed
right-shift that isn't recognized as a whole-function canonical idiom
becomes JS's *signed* `>>` at runtime**, diverging from GLSL-correct
logical shift whenever the shifted value's bit 31 is set (~50% of hash
outputs).

Confirmed present, with exact citations, in generated JS for **already
emitted, real production code**:
- `noisemaker-for-cpu/src/effects/generated/canonical-kernels.js:15313`
  (`filter/median`, function `packRecordMajor`):
  `var orderedRg = ((packedRg & 65535) << 16) | (packedRg >> 16);` — plain
  `>>`, not `>>>`, on a `uint`-typed `packedRg` from `packHalf2x16`. Same
  file line 15322 (`unpackRecordRgb`): `var packedRg = (major[1] << 16) |
  (major[1] >> 16);`.
- `canonical-kernels.js:16410-16411,16426` (`filter/osd`, local scalar
  `pcg`/`sample_glyph`, **not** the shared canonical `pcg3d`):
  `var word = ((state >> ((state >> 28) + 4)) ^ state) * 277803737;`,
  `return (word >> 22) ^ word;`, `var row = ... ; return cpu_float((row >>
  (6 - gx)) & 1);` — all plain `>>`.
- `canonical-kernels.js:19971,19973,19975` (`filter/spookyTicker`,
  `hash_mix`, inside `canonicalFactory147` which starts at line 19948):
  `v = v ^ (v >> 16);`, `v = v ^ (v >> 15);`, `v = v ^ (v >> 16);` — all
  plain `>>`.
- `canonical-kernels.js:34733` (`synth/testPattern`, `sampleGlyph`):
  `return ((GLYPH[digit] >> bitIndex) & 1) == 1;` — plain `>>`.

Contrast with the **correctly-recognized** idiom, which the C++ port's
existing `glsl::shift_right` already matches (this is why the *admitted*
`uint-vector-bitwise` capability is safe today): when a GLSL function
matches glsl-transpiler's canonical "pcg3d hash" template (recognized
even through superficial spelling variants — `v = v ^ (v >> uvec3(16u))`
in `filter/grain:grain` maps to the same call as `v ^= v >> uint(16)`
elsewhere), it's replaced wholesale with a call to a hand-written stdlib
helper: `canonical-kernels.js:13701` `function pcg3d (value) { return
$runtime.stdlib.pcg3d(value); }`, whose real implementation
(`noisemaker-for-cpu/src/csl/glsl-runtime.js:23-38`) uses `>>>` throughout
(e.g. line 33: `out[0] = (out[0] ^ (out[0] >>> 16)) >>> 0`). **The
dividing line is exact idiom recognition, not GLSL type** — every one of
the 14 frontier programs' bespoke hash/pack helpers (different function
names, slightly different bodies) falls outside that recognized set and
therefore needs the signed/arithmetic interpretation, not the logical one
the existing `glsl::shift_right` implements.

**Required C++ behavior**: a *new*, separate primitive from
`glsl::shift_right` — a signed/arithmetic right shift matching JS
(`static_cast<int32_t>(value) >> (amount & 31)`, sign-extending, count
masked mod 32 to match the existing project convention at
`glsl_types.hpp:200`) — must be used for every frontier `>>` site *unless*
a specific site is proven (by literally re-deriving the emitted JS, the
way this document just did) to route through a recognized canonical
stdlib helper. This determination is per-*call-site*, not per-*program* or
per-*GLSL-type*, and must be re-verified by reading the actual emitted JS
for each new program before choosing which shift semantics to lower it
to — assuming "type is `uint`, so use logical shift" is exactly the trap
constraint #4 warns about (parity target is the transpiler's heuristic,
not GLSL's).

### Hazard #2: `&`, `|`, `^`, `~`, `<<` are safe to implement as plain C++20 `int32_t`/`uint32_t` operators — but only because of a specific, citable C++20 rule change

JS's `&`,`|`,`^`,`<<`,`~` all coerce their operand(s) via ToInt32 first
and produce a 32-bit two's-complement result (ECMAScript spec, general
knowledge — **not independently re-verified against the spec text in this
session, flagged UNVERIFIED-by-citation** though it is standard and
well-established). C++20 mandates two's-complement representation for
signed integers (P0907R4, folded into `[basic.fundamental]`) and — this
is the load-bearing, less commonly known part — **also made left-shift of
a negative signed operand well-defined** (`[expr.shift]`: "the value of
`E1 << E2` is the unique value congruent to `E1 × 2^E2` modulo `2^N`",
independent of sign; this was undefined behavior pre-C++20). Net effect:
for these five operators, plain `int32_t`/`uint32_t` C++ operators already
reproduce JS's bit pattern exactly, with no special-casing needed beyond
using the right *width* (32-bit) type — this is a **general-knowledge
claim about the C++20 standard, not verified against the standard text in
this session**; it is, however, indirectly corroborated by this
codebase's own existing `bitwise_xor` (`glsl_types.hpp:206-213`), which
already relies on exactly this (plain `^` on `uint32_t`) and is proven
correct against the JS goldens for 131 shipped programs.

### Hazard #3: shift-count masking convention must match JS's automatic `& 0x1F`, and the existing project convention already does this — reuse it, don't reinvent

JS's shift operators implicitly reduce the RHS mod 32
(`ToUint32(rhs) & 0x1F`, ECMAScript spec — same UNVERIFIED-by-citation
caveat as Hazard #2, but this claim is directly corroborated in-repo: the
existing `glsl::shift_right` already does `const std::uint32_t masked =
amount & 31U;` at `glsl_types.hpp:200`). Any new shift primitive (signed
`>>`, or a future `<<`) must copy this masking convention rather than
leaving out-of-range shift counts as C++ UB.

### Hazard #4 (secondary, checked and found low-risk): unsigned comparison

The task brief calls out unsigned comparison as a classic divergence
point. Spot-checked in `filter/median`'s `lessRecord`
(`canonical-kernels.js:15298-15308`): comparisons (`a[0] < b[0]`) operate
on values already normalized to true non-negative JS-number magnitudes by
upstream `packHalf2x16`/masking (`& 65535` at
`canonical-kernels.js:15318`), not on raw ToInt32-reinterpreted values —
JS's plain `<`/`>` on such already-unsigned-magnitude numbers is
numerically identical to C++ `uint32_t` comparison. **No frontier program
was found where a signed-reinterpreted bitwise result is directly
compared with `<`/`>` before being re-normalized.** This is a lower-
priority risk than Hazard #1 but should still be re-checked per-site
during implementation, not assumed clear from this survey alone.

## 4. Existing runtime/validator/emitter coverage (Step 4)

Already covered (see §0): `uvecN ^ uvecN`, `uvecN >> uint` (logical),
`uvecN ^= uvecN`, all via `glsl::bitwise_xor`/`glsl::shift_right`
(`glsl_types.hpp:196-213`).

**Zero coverage** for: scalar `int`/`uint` `&`, `|`, `^`(outside the two
identity-locked programs), `<<`; unary `~`; `&=`, `|=`, `<<=`, `>>=`;
vector-vector `>>` (shift count itself a vector, `grain.glsl:43`); signed
arithmetic `>>`; `packHalf2x16`/`unpackHalf2x16` (`filter/median`); a
`uint`-flavored variant of `SOURCE_GLOBAL_LITERAL_INT_CAPABILITY`
(`filter/grain`'s `const uint` globals).

`generate_typed_slice.py` and `emit_typed_cpp.py` operator-token grep
confirms no dead/latent code paths for the missing operators exist in
either file — this is not a "just flip a flag" gap, every one of `&`,
`|`, `<<`, unary `~` requires new validator branches, new emitter
lowering, and (for `>>`) a second lowering path alongside the existing
logical one.

## 5. Proposed task decomposition

Ordered cheapest/lowest-risk → most novel, matching the project's own
established pattern (narrow, identity-proof-driven admission per program,
never widen a shape beyond what's proven necessary).

**Task N — `synth/bitwise:bitwise` (category (a), do first).**
Introduce scalar signed-`int` `&`, `|`, `^`, `~`, and their necessary
combination (`~(a&b)`, `~(a^b)`), admitted **generically** (matching the
project's existing pattern for `%`/`uint-vector-bitwise`: a type-shape
check, not a per-program identity lock — since this program's use is
plain runtime-uniform-driven, an identity-lock buys nothing here). New
runtime primitives in `glsl_types.hpp`: `bitwise_and`/`bitwise_or`
(reuse `bitwise_xor`'s pattern but for scalar `int32_t`) and a unary
`bitwise_not`. No new shift needed (`bitwise.glsl` has no `<<`/`>>`).
- *Discriminating tests* (frozen oracle per the project's
  `*-oracle-generator.mjs`/`oracle_typed_slice.mjs` pattern, run against
  real `canonicalFactory244` JS output):
  1. **Negative-operand XOR/AND/OR**: uniforms `a`,`b` spanning negative
     `int32` values (e.g. `seed = -1`, `mask` near `INT32_MIN`). Catches
     an implementation that assumes non-negative `int` (e.g. one that
     widens to `int64_t` before masking, or uses `uint32_t` throughout
     without a correct two's-complement reinterpretation of negative
     inputs).
  2. **`~(a & b)` / `~(a ^ b)` at `op=3,4`**: catches an implementation
     that computes `~` via `-1 - x` incorrectly interacting with a later
     `& mask` (must reproduce exact two's-complement bit pattern before
     masking, not a decimal-arithmetic approximation).
  3. **`mask` = 0**: `r = r & m; return float(r)/float(m);` divides by
     the same `mask` uniform — catches an implementation that special-
     cases mask=0 differently from what plain C++ float division of `0`
     produces (should match JS's `x/0` → `Infinity`/`NaN` propagation
     through `hsv2rgb`, not a C++ divide-by-zero guard that silently
     substitutes a different value).
  4. **`colorMode=1` chromatic-shift RGB path**: exercises `bitOp` three
     times with different `x`/`y` per channel — catches partial/sequenced
     application bugs (e.g. accidental shared mutable state across the
     three `bitOp` calls).

**Task N+1 — the shared `randomFromLatticeWithOffset` scalar-uint-XOR
family: `bitEffects`, `kaleido`, `shapeMixer`, `shapes`, `synth/shape`
(category (b), bitwise sub-piece only).**
These five share one hash idiom (four of them additionally through
`floatBitsToUint`). Recommend a **single, generic** admission (not five
identity-locked profiles) for scalar `uint ^ uint` and (for four of the
five) `floatBitsToUint`, since the shape is structurally identical to the
already-generic `uint-vector-bitwise` pattern — a per-program identity
lock here would just be five near-duplicate 100-line proofs for no
correctness benefit (contrast with `caustic`, where the surrounding
program-level reachability claim genuinely needs per-program proof).
This task **only unblocks the bitwise+floatBitsToUint piece**; each
program's *other* named blocker (global-int/array/matrix/mutable-global,
§1 table) is separate follow-on work, tracked as its own task, not
bundled here.
- *Discriminating tests*:
  1. **`fracBits`/`seedBits` derived from a negative or fractional
     `time`/`seed` uniform** driving `floatBitsToUint(seedFrac)` — catches
     an implementation that assumes `floatBitsToUint`'s input is always
     `[0,1)` and skips exact IEEE-754 bit reinterpretation.
  2. **Compare `xBits^jitter.x` against a value with bit 31 set** (large
     seed/tile values) — catches an implementation using `int32_t` XOR
     with implicit sign confusion instead of `uint32_t` throughout (XOR
     itself is representation-invariant per Hazard #2, but a mixed-type
     accidental promotion would still be a live bug class here).
  3. **`wrap=true` vs `wrap=false`** (changes `xi`/`yi` via
     `positiveModulo`) feeding into the hash — catches an implementation
     that only tests the no-wrap default path.

**Task N+2 — `filter/grain:grain` vector-vector `uvec3 >> uvec3`
(category (b), bitwise sub-piece).**
The one true vector-shift-count site in the whole frontier
(`grain.glsl:43`, `v >> uvec3(16u)`). Recommend admitting this **narrowly**
as "vector `>>` where the right operand is a `construct` node broadcasting
one literal `uint` value to all lanes" (provable at typed-IR level,
reusable via the *existing* `glsl::shift_right(vec, scalar)` by extracting
the broadcast scalar) rather than a general per-lane-variable vector
shift — there is no evidence anywhere in the frontier of a genuine
per-lane-distinct shift count, and admitting that general shape would be
unverified speculative scope. This program's `random_from_cell_3d` scalar
`uint^uint` sites reuse Task N+1's admission.
- *Discriminating tests*:
  1. **Broadcast-uniformity assertion**: a synthetic AST fixture where the
     three lanes of the shift-count `uvec3` constructor are *not* equal —
     must be *rejected* by the validator, not silently narrowed. Catches
     an implementation that only checks the outer node type
     (`uvec3`) without verifying the broadcast-constant proof, silently
     admitting true per-lane shifts it was never proven correct for.
  2. **Compare against the already-shipped scalar-shift-count
     `pcg`/`uint-vector-bitwise` oracle** for the *same* hash values (this
     `pcg3d` is algorithmically identical to the already-admitted one) —
     byte-identical output is the pass condition, catching any
     accidental semantic drift between the broadcast-vector path and the
     existing scalar-shift path.

**Task N+3 — bespoke local hash-helper family: `filter/median`,
`filter/osd`, `filter/spookyTicker`, `filter/texture`,
`synth/testPattern`, `filter/dither`, `filter/glyphMap` (category (b),
bitwise sub-piece — the Hazard #1 core).**
Introduce the new **signed/arithmetic** `>>` primitive (distinct from
`glsl::shift_right`), plus scalar `int`/`uint` `&`,`|`,`<<`,`^=` where
missing. This is the highest-hazard task: every site here needs the
signed-shift semantics from Hazard #1, verified per-program against the
*actual* generated JS (not assumed from GLSL type), because none of these
local functions match a glsl-transpiler canonical idiom.
- *Discriminating tests* (the single most important gate for this whole
  family):
  1. **A frozen JS-golden pixel oracle generated from the real
     `canonicalFactory*` output** (project's standard pattern, e.g.
     `oracle_typed_slice.mjs`) for each program, seeded so hashed
     intermediate values are forced to have bit 31 set for a meaningful
     fraction of pixels (e.g. sweep `seed`/coordinates across the full
     `int32` range, not just small positive test values) — this is the
     test that actually discriminates "used `glsl::shift_right` (logical)
     by mistake" from "used the new signed-arithmetic shift correctly":
     a logical-shift implementation will diverge from the JS golden on
     exactly the bit-31-set pixels and match trivially elsewhere, so a
     narrow test range would falsely pass a wrong implementation.
  2. **`filter/median`'s `packRecordMajor`/`unpackRecordRgb` round-trip**:
     pack then unpack a color with a component whose `packHalf2x16`
     result has bit 31 set (i.e. the float16 "G" channel has its sign bit
     set) — catches exactly the divergence documented in Hazard #1's
     citation; a wrong (logical-shift) implementation corrupts the
     swapped high/low 16-bit halves for such inputs specifically.
  3. **`glyphPixel`/`sample_glyph`/`sampleGlyph`-style bit-index sampling
     at every bit position 0..7** including the boundary `>>` amounts
     that push the sign bit into the tested range — catches off-by-one
     masking bugs in the shift-count `& 31` convention (Hazard #3) as
     well as sign-extension bugs.
  4. **`filter/median`'s loop-proof and `filter/dither`'s loop-proof are
     separate blockers**, not bitwise-shaped — do not attempt to solve
     them inside this task; track as their own loop-family work (outside
     this document's scope).

**Follow-on, not scoped here (name only, per constraint #3's "propose
gates, don't smuggle scope"):**
- `kaleido`'s five `float[9]` global arrays, `shapeMixer`/`shapes`'s four
  `const mat3` globals, `synth/shape`'s mutable globals, `osd`/
  `spookyTicker`'s `const int[80]` arrays, `filter/grain`'s missing
  `uint`-flavored global-const-literal capability, and `filter/median`'s
  `packHalf2x16`/`unpackHalf2x16` admission are each their own,
  unrelated-to-bitwise task.
- `classicNoisedeck/caustic:caustic` should not be scheduled at all until
  the reachability contradiction flagged in §1c is resolved by re-running
  reachability analysis with the actually-intended define map (if
  different from metadata defaults) — or by confirming this repo's
  `caustic_word_hash_profile.py` is simply stale/wrong and should be
  discarded before any further work references it.

## What I could not verify

- **ECMAScript spec text** for ToInt32/ToUint32 and the `& 0x1F` shift-
  count masking (Hazards #2, #3): stated from well-established general
  knowledge, not fetched/quoted from the spec in this session (no network
  access exercised). Strongly corroborated indirectly by this codebase's
  own already-shipped `glsl::shift_right` masking convention and by the
  generated JS I did read, but the ECMA-262 section numbers themselves
  are not independently re-checked here.
- **C++20 `[expr.shift]`/`[basic.fundamental]` exact wording** (Hazard
  #2): general knowledge of the P0907R4 change, not quoted from the
  standard text in this session.
- **The two contradictions with in-repo prior documents**
  (`caustic_word_hash_profile.py`'s "live, reachable" claim, and
  `post-scalar-bitwise-frontier-audit.md`'s "four resolved calls" for
  `bitEffects`) are reported as found, with my own analysis and its
  method fully cited — but I could not find a third source in the repo to
  break the tie, so both are marked UNVERIFIED rather than resolved.
- **Whether `bitEffects`'s `modi`/`and`/`or`/`xor` helpers are *ever*
  reachable under some *other* metadata-valid define combination**
  (e.g. `MODE=0`) was not checked — only the exact default define map was
  analyzed, per the task's reachability filter. If a future task wants to
  port `bitEffects` at `MODE=0` instead of `MODE=1`, the reachable-site
  set would differ from what's reported here and must be re-derived.
- **Full validator error closure beyond the second blocker** for
  `filter/glyphMap` and `filter/texture:texture`: I confirmed a second
  blocker (global-const-int) by direct declaration inspection, but did
  not exhaustively prove no *third* blocker exists further down their
  AST (the validator stops at first error; I did not patch around it to
  force a full pass, since doing so would have required either
  monkeypatching the live validator's internals or hand-rewriting source
  text, both of which felt like more risk of introducing my own analysis
  bugs than the marginal value justified within this task's scope). Treat
  the "other blocker" column for those two programs as *at least one
  more*, not necessarily *the only one more*.
- **`Math.imul`/`umul` 32-bit-wrapping multiply correctness** in the
  existing C++ port for scalar `int`/`uint` multiplication was noted as
  "presumably already correct" (existing, shipped `scalar-vector-
  arithmetic` capability) but not independently re-derived/tested in this
  session — it is not new work introduced by the bitwise family, so out
  of scope, but flagged in case a future task's oracle failures trace
  back there instead of to the shift/xor work this document scopes.
