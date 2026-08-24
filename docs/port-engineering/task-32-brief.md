# Task 32 `filter/grade` cluster — frozen design brief

DESIGN ONLY. No implementation performed. All numbers in this document were
independently re-derived against the live tree
(`noisemaker-for-cpp/tools/glslcpp`, corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`) via read-only probe scripts under
`docs/port-engineering/task32b_*.py`, not copied from prior prose.
Current accepted state, confirmed by direct query: **131 typed / 133 public /
79 unported / 212 corpus**, typed-list SHA-256
`ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2` (recomputed
from `typed_slice.json` and matches exactly — see §7).

## Correction to the target-selection brief

`task-32-target-selection.md` states "All six are passes of one GLSL file
(`filter/grade.glsl`)". **This is wrong and must not carry into
implementation.** The corpus manifest (`manifest.json`) shows `filter/grade`
is a **six-file multi-pass effect**: `sources/filter/grade/{primary,
hslSecondary, wheels, vignette, creative, lut}.glsl`, six distinct files with
six distinct raw/normalized byte counts and SHA-256 hashes (no file named
`grade.glsl` exists in the corpus). They share only the `effect_id`
(`"filter/grade"`) and a strong family resemblance (five of the six declare a
byte-identical `srgbToLinear`/`linearToSrgb` pair, confirmed below). This
doesn't change the target selection's validity, but every downstream claim
about "one shared source, one shared proof" needs this correction: what's
shared is a **repeated code pattern across six independent programs**, not
one parse tree with six entry points. This affects the identity-scoped
authentication design in §2/§4 directly — six programs need six independent
profile authentications, not one.

## 1. What `index_expression_admission` really is for this cluster

**Verdict: genuinely one structural shape, reused identically across all six
programs — but it is a *new* capability shape, not a variant of any existing
one, and it does not admit generalizing the existing array-index machinery.**

Every bracket-index (`[...]`) site in all six programs was enumerated by
walking the typed AST directly (`task32b_grade_identity.py`). Result: **74
index sites total** (primary 10, hslSecondary 14, wheels 10, vignette 10,
creative 10, lut 20), and **every single one** has `base.kind == "id"` (a
plain local `vec3` variable — `linear`, `srgb`, `rgb`, `result`) and
`index.kind == "id"` (the `for`-loop induction variable `i`) — **never a
literal integer index, on either the read or the write side.** Confirmed by
direct census, not sampling.

This is structurally distinct from every existing index-admission track in
`generate_typed_slice.py`'s `expression()` (`store_valid`, `read_valid`,
`grid_store_valid`/`grid_read_valid`, `task19_store_valid`/`task19_read_valid`,
`task20_valid`, lines ~2112-2163): **all six existing tracks require a
literal-int index for a *store* (write/lvalue)**; the only track that accepts
an `id`-kind index (`read_valid`) is for *reads* only. None of the six
existing tracks admits an `id`-indexed **write** — but that is exactly what
`linear[i] = srgb[i] / 12.92;` needs (`i` is the loop counter, not a
constant). Confirmed live: the first blocker after `global_admission` is
patched is always `unsupported typed expression index` pointing at the first
**write** site (e.g. `filter/grade:primary:41:13`, the `linear[i] =` line in
`linearToSrgb`), reproduced independently by calling
`gen.validate_capabilities`/`emit.render_typed_cpp` directly (unpatched) —
see `task32b_validate_baseline_output.json`. This is also not an
`array_global_admission`-style capability: these are not fixed-size arrays,
they are **lane-wise subscripting of a plain `vec3` local**, which the
existing `_proved_array`/`proved_array_declarations` machinery (keyed on
`array_type`/`literal_store_indices`) cannot express even in principle —
there is no "array" here at all, just a vector being indexed by a runtime
variable.

**Is it really one shape or several?** Within the grade cluster specifically
— narrower than the wider 9-program figure the full-chain report caveated —
it is genuinely **one shape**: "read and/or write one lane of a local `vec3`
via a `for`-loop induction variable, in both `if` and `else` branches of a
per-lane conditional." Evidence:

- `srgbToLinear`/`linearToSrgb` are **byte-identical text** in all six files
  (verified: `md5` of the extracted function bodies matches across all six),
  and appear in every one of the six programs — 12 of the 74 sites per
  function-pair × 6 programs = wait, precisely: 2 functions × 6 programs = 12
  function instances, 5 or 4 index sites each depending on the function (see
  §4 tables) = 60 of the 74 total sites.
- `lut.glsl`'s `lutHardLight`/`lutSolarize` (10 more sites) use the exact same
  read-compare-write/write shape (a per-lane `if (rgb[i] OP threshold) {
  result[i] = ...} else { result[i] = ...}`), differing only in the
  arithmetic inside each branch and in comparing against a **local variable**
  (`threshold` in `lutSolarize`) rather than a float literal in the two
  common functions — a difference in the *comparison operand*, not in the
  *index expression itself*, so it does not change what needs authenticating
  about the index node.
- `hslSecondary`'s `hslToRgb` (4 sites) is **write-only** — it never reads
  `rgb[i]` — and initially looked like it might additionally consume the loop
  variable via `float(i)` in `t = h + (1.0 - float(i)) / 3.0`. Checked
  directly: `float(i)` is a **`construct` node** (a type-conversion
  constructor call), not an `index` node, and int→float construction is
  already covered by the existing generic `"constructors"` capability (`used
  .add("constructors")`, `generate_typed_slice.py:2005`) — confirmed by the
  gate chain never reporting a second, distinct blocker for this site. So
  `hslToRgb` needs **no additional proof shape** beyond the write-side index
  admission every other function needs; it's the same shape, just write-only
  and 4 sites instead of 4-5.

**Conclusion for the vocabulary/design question**: the grade cluster needs
exactly **one new authentication shape** — "loop-induction-variable-indexed
`vec3` lane access, read and/or write, inside a per-lane conditional" —
instantiated independently 6 times (once per program, since each program has
its own `source_hash`/AST identity per this codebase's established
per-program authentication model; textual identity across files does not
exempt a program from its own authentication). This *confirms* the
target-selection brief's optimistic reading for this cluster specifically
("very likely one real proof"), while the wider 9-program figure (which
folds in `normalMap`/`osd`/`remap`, each indexing differently-shaped tables)
remains "2-4 real proofs" as the full-chain report said — that caveat was
about the *other* three programs, not about grade.

## 2. What `global_admission` must allow for the five programs

**Verdict: exactly one new initializer shape (`const vec3` via a 3-argument
constructor call), for which a near-identical precedent already exists in
the codebase** (`smooth_edge_luma_weights_profile.py`, admitting `filter/
smooth:smoothEdge`'s own `const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587,
0.114);`). Grade's five programs each declare, byte-identically to each
other in content though at different line numbers:

```glsl
const vec3 LUMA_WEIGHTS = vec3(0.2126, 0.7152, 0.0722);
```

This is the **same shape** Smooth Edge already has an accepted profile for
(a `const vec3` with a 3-literal `vec3(...)` constructor initializer) but
**different literal values** (BT.709 weights `0.2126/0.7152/0.0722` vs. Smooth
Edge's BT.601 weights `0.299/0.587/0.114`), so the existing exact-hash-pinned
`smooth_edge_luma_weights_profile.py` **cannot be reused as-is** — its
`_INITIALIZER_SHA256`/`_LANES` tuple is pinned to the different literal
values and to Smooth Edge's own line/column spans. Five new,
identity-scoped profiles are needed (one per program, following the exact
same template), not a generalization of `APPROVED_TYPES`/`global_initializer`
to "any `const vec3`" — that would be a structural rule, which is exactly
what this codebase's precedent (and constraint (a) below) forbids.

`hslSecondary` additionally declares `const float PI = 3.14159265359;` —
**this needs no new admission work at all.** It is a plain `const float`
global whose initializer is a bare literal, which is **already** admitted by
the generic mechanism at `generate_typed_slice.py:1926-1951`
(`storage=="const" and type==FLOAT`, `initializer.kind=="literal"`). Verified
directly: `PI`'s declaration passes `global_initializer()` unmodified — the
gate chain's first (and only, besides index) blocker for `hslSecondary` is at
`LUMA_WEIGHTS`'s line (`21:1`), never at `PI`'s line, confirming `PI` isn't
the thing failing. No unused-global rejection exists in this codebase's
validator (dead consts are allowed to type-check; the "write to source const
global" audit is about *writes*, not about reads), so `PI` being unread does
not raise a blocker either — it's simply irrelevant to this task, present
only for completeness.

**No global in this cluster needs a shape beyond literal/constructor
initializers.** Checked directly against the two known non-trivial precedents
named in the task: `bitEffects`'s shift-initializer (`<<`) and
`scanlineError`'s swizzle-initializer are **not present** in any of the six
grade programs — every one of the six `LUMA_WEIGHTS`/`PI` declarations here
is a plain literal or a 3-literal constructor call, confirmed by reading
`initializer.kind` for all six declarations (all `"literal"` or
`"construct"`, none `"binary"`/`"unary"`/`"swizzle"`/`"member"`).

**`lut.glsl` has zero global constants** (confirmed: no `const` declarations
in the file at all — `luma()` inlines the weight vector as a literal
`vec3(0.2126, 0.7152, 0.0722)` argument to `dot()` rather than naming a
global). This is why `lut` is the one program needing only
`index_expression_admission`, matching the target-selection brief exactly —
independently re-confirmed, not copied.

### Critical finding: `hslSecondary`'s `LUMA_WEIGHTS` is dead code

Grep and AST census both confirm `hslSecondary.glsl` declares `LUMA_WEIGHTS`
(line 28 in raw source) but **never reads it anywhere in the file** — zero
`id`-kind references to that symbol in any of its 7 functions. This is
**exactly the `classicNoisedeck/bitEffects` pattern** flagged in
`full-chain-frontier-map.md` §2: the validator/emitter type-check *every*
global declaration in the program unconditionally (the admission loop at
`generate_typed_slice.py:1916` iterates `typed.declarations`, not reachable
declarations), so `hslSecondary` needs the vec3 carve-out purely for
**admission-completeness of dead code** — a render will never exercise it
under any input. See constraint (c) discriminability verdict in §5.

The other four (`primary`, `wheels`, `vignette`, `creative`) all read
`LUMA_WEIGHTS` from functions reachable from `main` (§5) — `dot(rgb,
LUMA_WEIGHTS)` calls at 4, 2, 1, and 3 sites respectively, tabulated in §4.

## 3. Frozen target identity (all six)

All values recomputed by `task32b_grade_identity.py`, cross-checked byte-for-
byte against `manifest.json`.

| Program key | Source | Raw B / SHA-256 | Normalized B / SHA-256 | Functions | Function-tuple SHA-256 |
|---|---|---|---|---:|---|
| `filter/grade:primary` | `sources/filter/grade/primary.glsl` | 5839 / `008521bf82834ef55383a492adacb259964170831c92d6c9ddc6368acc850cc2` | 4149 / `6ce48b1dfd729e61d6f36a929a361b2597cd2989fde7bce75e488d18332af4f1` | 13 | `75af73aeeef7936694647aa8c2829d19f5974a17f7c6d217096e1d47d7236270` |
| `filter/grade:hslSecondary` | `.../hslSecondary.glsl` | 4975 / `2f2c54a6d977ccc0ba8657c02f1fc2fecfb576ad85f6d03ea16468fc9cbd095a` | 4260 / `e2e2faa0484d7d8bce8d786bee19ef30ae258d9910f3691efd31d7c4f00469d5` | 7 | `98d0c809dabbd39ad4b017e5e2337b1aa93f8c3db0a03aeb5eebfb1533774a93` |
| `filter/grade:wheels` | `.../wheels.glsl` | 3529 / `fa9c411096816263985e8d5ef82ade976667a6cadecf8929ecd185edbc71f479` | 2789 / `cc34a0287290b7084fdb8d5611b7aacb6bdcfec5a229770823b5e2891cb27efc` | 7 | `380fdefa5da3fd725dcb4180440609c719d566dbb0b2e6f6a6c141201443c49a` |
| `filter/grade:vignette` | `.../vignette.glsl` | 4133 / `740ad849a37c99d87962a376c2e618b24248dc4b2799066aaf6364861727c1fa` | 3158 / `da1e995c43c079d01112112d7fcc82db19e0720567637351bb1fa5f777caf82b` | 5 | `74293fa4d562c9e500d6be13015f6775afd1805a4556fcbce11b3fd887dd331d` |
| `filter/grade:creative` | `.../creative.glsl` | 4230 / `b043aa43d17e098ffb736f16e6c81a5ca422ecdd6fc37fef03c39b01cc939bd3` | 3231 / `0a690075dd6e709f41978baecc5106689637648fe4fa7ccad203ccc890f5f48f` | 6 | `753ae2fcd63137d175d9c45e5ff13630926ad7bdcca4d9111e0a9afac13a7512` |
| `filter/grade:lut` | `.../lut.glsl` | 13745 / `0a8a3ae4d2a14142ae7d53373bfac6ac87a0b175dff132d71cd80e6226f9ec40` | 10588 / `c384a8759f681d191d6f6f5560101b2ed62ba3e187f4bdfb0574f608fca84881` | 28 | `f6eba16d49a8a861a5d282d1cd84202c2759e7506257a52952a64826e072e460` |

| Program key | Whole-program SHA-256 | Interface SHA-256 | Loop proof (count/unproved/depth/product/charge/acyclic) |
|---|---|---|---|
| `primary` | `8c86ac4c453be44b558d423b93b172d1f1c0b8310c1574a8c9d79ef17a67dcbc` | `6716f9f839199c7ccaccdf6c0d94f617bf3167014a44b6400b52b6e0f2f963ed` | 2 / 0 / 1 / 3 / 6 / True |
| `hslSecondary` | `fab6e7a4d97ceeb8dae400465b2efc034521c58fd04d1ab229606fe90c908874` | `ad58e18b0a04a1069ad381d78e534541a80ec5c6c70bf97b0ed00818a90a6f08` | 3 / 0 / 1 / 3 / 9 / True |
| `wheels` | `3bdd83a3c201f78d00b04bc8360bd1ea670f046f81fcadde8aa6989f0d3ed7e6` | `52983f7002275735864a8837e14cd67c6ac2621efe2fff644643c0e34845bed9` | 2 / 0 / 1 / 3 / 6 / True |
| `vignette` | `d8265fbf3722040699e064bfc24120d8f33dc42d8699e7055d91c4f3f0dc9a77` | `0439b9b58f6275497cc9967f8187a2c9d729d892fa660ce1d2faf170c94a4a32` | 2 / 0 / 1 / 3 / 6 / True |
| `creative` | `8a5fb6c925dae811442b04f549109f71155db4eb45ced227ac1f7f83bef0ea41` | `d484112887f0a77bedd887b8e7bc5a038497d196bcac8d7924b9937372b87366` | 2 / 0 / 1 / 3 / 6 / True |
| `lut` | `c0f640cb5d166ecbf3d2b30373af46313835f0c59f1c8a3608192991675f4a26` | `c18fe18ba6259647463eef30713c7db0cbbdf0d9ec98795b8447da429bb71e93` | 4 / 0 / 1 / 3 / 9 / True |

`_whole`/`_interface` computed with the identical field tuple used by
`frontend/curl_vector_math_profile.py` and
`frontend/smooth_edge_luma_weights_profile.py` (`key, source, raw_source,
declarations, functions, resources, body_status, local_type_names, structs,
uniform_blocks, interface_symbols, builtin_symbols, counted_loop_proof,
preprocessor_defines` for whole; the same minus `key`/`source`/`raw_source`/
`functions`/`counted_loop_proof` for interface), so these are directly
comparable to every prior task's frozen values.

**Defines**: all six have exact defines `{}` (confirmed: `metadata.json`'s
`effects["filter/grade"]["params"]` maps every parameter to a `"uniform"`
key, none to a `"define"` key — there is no `#ifdef`-driven dispatch anywhere
in this effect; `preset` in `lut.glsl` is a **runtime uniform**, not a
compile-time define, which matters directly for reachability in §5).

**Canonical/public factory identity**: mechanically, each program's factory
function name is `"bind_" + key.replace("/", "_").replace(":", "_")`
(confirmed at `generate_typed_slice.py:2538`, the general case used for the
overwhelming majority of typed programs) — e.g. `bind_filter_grade_primary`,
`bind_filter_grade_hslSecondary`, etc. **Inconclusive**: whether any of the
six additionally needs a bespoke `canonicalFactoryNN`-style identity constant
(as Extrude/Smooth Edge/degauss/CRT have) could not be determined from the
artifacts read — those four constants are hardcoded per-program in
`generate_typed_slice.py` for reasons specific to their own profile
verification (e.g. Extrude's "no adapter" check), and Smooth Edge — which
has the closest-analogous global-admission carve-out — does **not** have one
(confirmed: its `typed_slice.json` entry carries no factory override, only
`smooth_edge_luma_weights_profile`). No evidence found that global/index
admission alone requires this pattern; treat grade the same as Smooth Edge
(standard `bind_...` name, no bespoke factory constant) unless
implementation-time inspection of the adapter-check machinery says otherwise.

## 4. Frozen closures — every node needing new authentication

### 4a. Global declarations (5 programs)

| Program | Symbol | Span | Type | Declaration SHA-256 | Initializer SHA-256 | Dead? | Total reads | Reachable reads |
|---|---|---|---|---|---|---|---:|---:|
| `primary` | `LUMA_WEIGHTS` (id 7) | `22:1-22:56` | `vec3` | `105d7ec786df6db38cf0ad98d31250d818361d33a169cb059966af66bb13a8ac` | `4461b1da004c8387277bac6daa4ddc978cd6a2099d504876cd172cfae9671e18` | No | 4 | 4 |
| `hslSecondary` | `LUMA_WEIGHTS` (id 7) | `21:1-21:56` | `vec3` | `c854652ded68a20becb5e62d6192bd8e3653681b57e2410de8caff6e5ee3ab23` | `a21804beed7e2680203cdafddefe7ed9bfb5f40b039e3a171c1fe2e48d8e7215` | **Yes** | 0 | 0 |
| `wheels` | `LUMA_WEIGHTS` (id 7) | `14:1-14:56` | `vec3` | `04adf0103445aa05df16e6855f6e425da475be6ba9f7c0c1cdf8207bf5883ddd` | `f69bedc6100c29cfe8a607427b43217bcdac3fbb1517ffb1cdb5f4b387e41f8e` | No | 2 | 2 |
| `vignette` | `LUMA_WEIGHTS` (id 7) | `15:1-15:56` | `vec3` | `77a43c66e6bf41c5a8976abece1b50c5612191c0c89b5ac5d32fdef8c7514098` | `29dcba44cb4c504bd9b1088d6e90a756d8907576dd839a3a64c37524bccce385` | No | 1 | 1 |
| `creative` | `LUMA_WEIGHTS` (id 7) | `15:1-15:56` | `vec3` | `570658142d8113df455df8f84dd0c60d767e2564a0b1c78a605e5b9204dbbe14` | `0552b0c3bd0a249fe18c5d17c3d1221d6889c433e8e3fc8c3901348ec58c6750` | No | 3 | 3 |

Read sites (function id, name, span):
- `primary`: `(41, applyContrast, 119:27-119:39)`, `(42, applyCurve,
  136:27-136:39)`, `(43, applySaturation, 158:27-158:39)`, `(44,
  applyTonalRanges, 92:27-92:39)`.
- `wheels`: `(23, applyWheels, 73:27-73:39)`, `(23, applyWheels,
  96:33-96:45)`.
- `vignette`: `(22, applyVignette, 81:31-81:43)`.
- `creative`: `(21, applyFadedFilm, 81:30-81:42)`, `(22, applySplitTone,
  102:27-102:39)`, `(23, applyVibrance, 47:27-47:39)`.
- `hslSecondary`: none.

Each initializer is `kind=="construct"`, `constructor_type.display()==
"vec3"`, 3 children, each child `kind=="literal"`, `type=="float"`, lexemes
`0.2126`/`0.7152`/`0.0722`. `PI` in `hslSecondary` needs no profile (see §2).

### 4b. Index-expression sites (74 total across six programs)

All 74 sites have `base.kind=="id"`, `index.kind=="id"` (the `for`-loop
counter), `type=="float"`. Full span/SHA-256/context table (rvalue = read;
lvalue = write target of an `assign` node):

**`primary`** (10 sites — `srgbToLinear` fn 12, `linearToSrgb` fn 13):
```
28:13-28:20 srgbToLinear rvalue a4e50cbd301e83037492d2cfb515616d57a32a6f5ad8731301a6a5b660017dfb
29:13-29:22 srgbToLinear lvalue 174c9ea3c148376a8c5a47d8751e834a6e6304fb462249b507fa42a205ffdeaa
29:25-29:32 srgbToLinear rvalue 6d10567e16ae294d2558cd19c72ced3f780652050096ece6d5927c1b67b7c69e
31:13-31:22 srgbToLinear lvalue 138bfedfef4bd444de1abde5a27adebd27090c017ff5695ce4972915a46b895e
31:30-31:37 srgbToLinear rvalue 3abe01841a9c4c3241a935c05bbcbab44036ab527134caa584af46ab93a42754
41:13-41:22 linearToSrgb rvalue 2613d8077777ee0a5dba5e750f2d6cedb5f02599f3db4900d870e2e5a6f5bb17
42:13-42:20 linearToSrgb lvalue 375abb89e1c7f8c130879c6d8845188bf99817d4f97d55dce086a7122ae4ee42
42:23-42:32 linearToSrgb rvalue c46ac1519d9567fc0c0a4625b44178501eff14f7e04821a4f1d9ea9edaccca22
44:13-44:20 linearToSrgb lvalue a84fa2d243936e2ca8c8dedfdce5bde0fb2226523b8da2a15291712104d96b1a
44:35-44:44 linearToSrgb rvalue 50f7440b3ccf3bd4594cc99edb0a64d9d745507af367eb0b5aed58a6ebc04278
```

**`hslSecondary`** (14 sites — `srgbToLinear`, `linearToSrgb` identical shape
plus `hslToRgb` write-only):
```
28:13-28:20 srgbToLinear rvalue 2475038fd0df20649b4de127140a48956452aa70df8dc6fb8f74734f012feb16
29:13-29:22 srgbToLinear lvalue 81a3e4e0e848ad174957e3314603f3d67533e23b75c070a99c339f4474e9091f
29:25-29:32 srgbToLinear rvalue 041181c63f834d620c2cf49d65942b3901642df7852c8357c66852f7457e0fee
31:13-31:22 srgbToLinear lvalue 53bfe161a725565d4d2ca912718a85bb8326ae0c6599efebde0d9682d652797f
31:30-31:37 srgbToLinear rvalue e1e1db3f37c00f93bbc85535b05b52ba865353984ebf6685c8b6c17665129ee2
41:13-41:22 linearToSrgb rvalue 6445c0a729cc78ccdb6385385f0666ad5b5607e5b743092a8fc2a1b74c7d7a80
42:13-42:20 linearToSrgb lvalue 26eca14dce4d68ce90863c59b2675f327dbeb9ab154825d65ca6db45386f01ce
42:23-42:32 linearToSrgb rvalue 4b656cff779e5f986abd4f8e15bf968b5e6d1facdfe4e021a814a07bc446982b
44:13-44:20 linearToSrgb lvalue 890242a06dbc8cf34364c613cd5f0c4b6452f099952de0b8ee0ca3c25c69d5f2
44:35-44:44 linearToSrgb rvalue f8682fa317e82b84e0db7c7e1f6fd1b03f9cbb8d7253398a3e9cd4d7c3e2cf44
96:13-96:19  hslToRgb    lvalue 3d062c91ea636f82f84c6a385596b21adbe3a089059e148e127df22df456f85f
98:13-98:19  hslToRgb    lvalue 112929cc70c09231139c9f1679350c12a581c5392b7e74e9d199e0a07e781965
100:13-100:19 hslToRgb   lvalue 3c475ede0dd8545da27aa8a60359e33c9cffdae2f38b6e1cb50b911a9c36dc5d
102:13-102:19 hslToRgb   lvalue 2aee1523e8ca6b404dfb4b8eaa6a5a7d80257ef9b2c03fe297f000e96aa4a6c9
```

**`wheels`** (10 sites, same pair shape):
```
20:13-20:20 srgbToLinear rvalue e6191cc9185cc6a8bb6123266f72688941e6cf9f553c7761054cd0db2ce794fb
21:13-21:22 srgbToLinear lvalue 8f39e8edd7e58c29a5cae396d6f7e562724ddf8949ba64c93e825b23614fcb75
21:25-21:32 srgbToLinear rvalue 050c16188d6dab7cbf12eef218697e842cfceaadfbd386ab43718d3905c9b043
23:13-23:22 srgbToLinear lvalue a4ee2afeaa06ea9b3ae6475f03b6e96a2b238f5c6866b3ce48d4e13d6273edd3
23:30-23:37 srgbToLinear rvalue 9908da897785232617fa6cb3155a56e710fc08bce8ac7ba35b2c3eb12a5a8973
33:13-33:22 linearToSrgb rvalue 75d5b9502043b1214a84f1eb93373c5ce2cc3cc2c66d9ceaefc874e621a3de0b
34:13-34:20 linearToSrgb lvalue 981f9dd559e29fbf0c655dc207bbc3ab8fc4146149109c3edc89c350f067d351
34:23-34:32 linearToSrgb rvalue 751be25cea912a5c96441d535f81846baf81813cf782898f5bb7ae6a43e6f459
36:13-36:20 linearToSrgb lvalue 46e7b3e749e22056e71a85fc2abf23bb7a64ea8acbb68d586269fcc2edb284b6
36:35-36:44 linearToSrgb rvalue 365b5584a18115b15edb689648d28193319e9107b4c5c34999758a23dd7e5747
```

**`vignette`** (10 sites, same pair shape):
```
21:13-21:20 srgbToLinear rvalue 55be133cbb2b6c92cf809e2199ceeb64611b6118a047e3fbfbc8fcd589ef90c7
22:13-22:22 srgbToLinear lvalue d74603f48294c778f400ad287e2f68e6d2caad9ef2c13ad966938ef6d151288c
22:25-22:32 srgbToLinear rvalue cbb5f1e07415d79026c07611021e8b263caa320af56bf1058dc8f9def24c1d2e
24:13-24:22 srgbToLinear lvalue 79884f969663341ca3f5ca75c6c69c31a10e46588f3a41f8103da7892b613d73
24:30-24:37 srgbToLinear rvalue c6871c2779154adcca8fd574b7d7c635c12511e4e65e820413f25ef1f9f4bd10
34:13-34:22 linearToSrgb rvalue d090fda6678f83e47bb21081349fc11db400d0a79b061a64e5080bff3dc2192f
35:13-35:20 linearToSrgb lvalue 8390e03013779382d075b13565499301da682bd8ee3be9c721da8c782315793a
35:23-35:32 linearToSrgb rvalue a0fd97451bafa249bd4438a02adfe66f3c87078295b66a3d19b51b28f0d1b8ae
37:13-37:20 linearToSrgb lvalue 056e7b29799ef15429a57ce31fb9d2341582a9ed8914073cd3807eaf6e24b661
37:35-37:44 linearToSrgb rvalue a69bbc97c42d2d4c5a35ccc961bdc8ce68d7d1f475233f085366277b5229cbf6
```

**`creative`** (10 sites, same pair shape):
```
21:13-21:20 srgbToLinear rvalue 52dae6afd41d07d9f83e629340c9475b4f093ff82000e5965ea9b708cf6cbd7c
22:13-22:22 srgbToLinear lvalue 0eb094e98f3a3de14122e3ecc01fd66bc963ca37e80c7f3ce8cfe7a87273288c
22:25-22:32 srgbToLinear rvalue 64ae05599265f74a81b0a6e066a6456d7d1ad58629758a75742ff17a92eb2b16
24:13-24:22 srgbToLinear lvalue de6cc2deb9f0f226c875eb09d694672b8832e8a51187b456931d6c54b1beab1b
24:30-24:37 srgbToLinear rvalue 08167753b42cc145d5d36f48be9b88e8524c8372edf27cb9f3663e6581134b42
34:13-34:22 linearToSrgb rvalue 1aec2abcebae25f02c2a9858c9941254240f7a6ef2f1f78c0da3cd0166e9f245
35:13-35:20 linearToSrgb lvalue 7a5e79c9550bb07c250c75a27678486e424c5988b2696d71a98ac8a1dfb843c9
35:23-35:32 linearToSrgb rvalue fa396683ec9ac64d8f2474713bcdf1a761bebc896862011e68c308df6508fc9a
37:13-37:20 linearToSrgb lvalue 6855aeafda4085ceadf739b3c4b01755918f8126f5900f3e89663a6a6b66c6eb
37:35-37:44 linearToSrgb rvalue 49ee9c053bb89d52b0dcaeebcba0210f8fbd2c07c0d11dd79eed6c3ffd07f5d4
```

**`lut`** (20 sites — `srgbToLinear`/`linearToSrgb` pair plus `lutHardLight`,
`lutSolarize`):
```
16:13-16:20 srgbToLinear rvalue ee70860e5caf712e2ba1c01db1239003f11806925a1965dd6c7250968f6659cb
17:13-17:22 srgbToLinear lvalue f04b84ea8e4fef8ecaa548b13b3e91025439327b6e91226d47888415b5d26ee7
17:25-17:32 srgbToLinear rvalue 29372ac4ade2fecc313b91860b2f9789333481662f506f8b7f10476ea82478b8
19:13-19:22 srgbToLinear lvalue c50f19f5e80f2460085d21764cb18ba5e23a411de2b28bacdbd249ee3bce3b24
19:30-19:37 srgbToLinear rvalue 704d380022dce824cb932cfb00d24f608cb3e3748f59d312bd92090c23b3795c
29:13-29:22 linearToSrgb rvalue 3bec4e1df0ec3c3fde3d9a7e6d89043c19626865f37df0475f2d09e6976cee4d
30:13-30:20 linearToSrgb lvalue 64d152bc1943aa873514051a0c8650a9c3ee92f42966d26a6b67f6fd43092933
30:23-30:32 linearToSrgb rvalue 6014ccbe1c50e836725b360b700e824c42bcf7ce0132e715bc543ee972619cd6
32:13-32:20 linearToSrgb lvalue 0d7704e58b35b63527d55654764e95a284a4b57f7db4696c9dae8b62ef7938e3
32:35-32:44 linearToSrgb rvalue c05c780cc6469e5a3db7f99c844987da03a8ed92a9ad1aee49ef99cabf91d135
392:13-392:19 lutHardLight rvalue bf8ce1dfe993e1280befbb28df50b3c652bc4d2add7e32364918a6a3d4e3df84
393:13-393:22 lutHardLight lvalue 05ea5df9e619ac221c7f34a8267303b4d7e56e4ab73f3d32091bc9508bb6c8d7
393:31-393:37 lutHardLight rvalue b695fb48c173808e5d7896cc351f272f069206d3ae7a726a437c2b894429e008
395:13-395:22 lutHardLight lvalue 6909028c076e4fcac2362ddeddfde7225e9e7ef747dde8b21305ddeaa277ef27
395:44-395:50 lutHardLight rvalue 75e7edcb9cf3fe1c8afecae09635bd59fa829fc525d859b97f8a7363d2284083
447:13-447:19 lutSolarize rvalue da8bd7811250566525e26d2399f4e9ccd6bd676a0ca3c5edc062a2e792e02870
448:13-448:22 lutSolarize lvalue 2bc453c67c449c1bd749b93a24caaa380e1cab784aed3f0ac12d8cb64a77dc7e
448:38-448:44 lutSolarize rvalue 4fff72d9f176704a58ae4408a3dcb0d2b563700b443d24795bb32ab60c9c048b
450:13-450:22 lutSolarize lvalue 0ea66bd3750f5941b909d5357ad9e17ca4d5cbabfde0b32c67e4a3874c4450fb
450:31-450:37 lutSolarize rvalue cac89aacc6d3c444fe5a1c02ea7aefbf4b27b4de3d6fc71c8efdd1132e6336c6
```

## 5. Gate chains, reachability, discriminability (constraints b/c)

### Gate chains confirmed live, independently

Re-run directly (unpatched `gen.validate_capabilities`/`emit.render_typed_cpp`
against all six, `task32b_validate_baseline.py`), reproducing
`roadmap2/gate-chain-all-output.json`'s depth-0 rows exactly:

| Program | Validator first blocker | Emitter first blocker |
|---|---|---|
| `primary` | `22:1: unsupported global declaration` | `22:1: unsupported source global declaration` |
| `hslSecondary` | `21:1: unsupported global declaration` | `21:1: unsupported source global declaration` |
| `wheels` | `14:1: unsupported global declaration` | `14:1: unsupported source global declaration` |
| `vignette` | `15:1: unsupported global declaration` | `15:1: unsupported source global declaration` |
| `creative` | `15:1: unsupported global declaration` | `15:1: unsupported source global declaration` |
| `lut` | `29:13: unsupported typed expression index` | `29:13: unsupported typed expression index` |

For the five with `global_admission` first: after that gate is (probe-)
patched, the **second and final** blocker for all five is
`unsupported typed expression index` at the first write site in
`srgbToLinear`/`linearToSrgb` (`41:13`/`96:13`/`33:13`/`34:13`/`34:13`
respectively) — matching `gate-chain-all-output.json` exactly. After both
gates, all six reach `PASS` (validator + emitter both clean, `cpp_bytes`
9534-37958 depending on program size). No third gate exists for any of the
six — confirmed by the recorded chains terminating at depth 2 (five
programs) / depth 1 (`lut`), all `restored_all: true`.

Independently confirmed: the 44-entry `APPROVED_CAPABILITIES` tuple is
unmutated after these probes (`assert len(gen.APPROVED_CAPABILITIES) == 44`
passes; identity-checked against a pre-call snapshot).

### Reachability (constraint b)

Call graph built from `call`-node `signature_id`, BFS from `main`, per
program, independently computed (`task32b_grade_identity.py`).

**Result: every function in all six programs is reachable from `main`.**
`primary` 13/13, `hslSecondary` 7/7, `wheels` 7/7, `vignette` 5/5, `creative`
6/6, `lut` 28/28 — **zero unreachable functions**, unlike `filter/snow` and
`classicNoisedeck/caustic`. This holds even for `lut`'s 22-way `if
(preset==N) ... else if (preset==N+1) ...` dispatch in `main`, because
`preset` is a **uniform** (a runtime value), not a `#define` — confirmed:
`metadata.json`'s `filter/grade` params map every field to `"uniform"`, none
to `"define"`, so there is no preprocessor expansion collapsing any branch;
every `call` node for every `lutXxx` function is present in the parsed AST
regardless of what value `preset` takes at runtime, including
`lutHardLight`/`lutSolarize` (`preset==20`/`22`), which is where the two
extra index sites in `lut` live. This is exactly the distinction the prior
Task 31/32 work established for `#ifdef`-gated dead code (`snow`,
`bitEffects`'s bit-logic family) versus ordinary runtime branches: only the
former removes a `call` node from the AST at a given define set, and grade
has no `#ifdef`-driven dispatch to begin with.

**No program in this cluster is reachability-disqualified.** All six should
be validated structurally *and* the six new node closures are exercised by a
real call graph, not merely admitted-but-dead code, **except** for the one
declaration flagged below.

### Discriminability (constraint c)

| Site | Render-discriminable? | Evidence |
|---|---|---|
| `primary` `LUMA_WEIGHTS` | **Yes** | 4 reads, all in functions called unconditionally from `main` (`applyContrast`, `applyCurve`, `applySaturation`, `applyTonalRanges`); feeds `dot(rgb, LUMA_WEIGHTS)` which directly sets per-pixel luma used in every tonal computation. |
| `wheels` `LUMA_WEIGHTS` | **Yes** | 2 reads inside `applyWheels`, called unconditionally from `main`; feeds luma used to weight the three-way color-wheel blend. |
| `vignette` `LUMA_WEIGHTS` | **Yes, conditionally** | 1 read inside `applyVignette`'s `if (highlightProtect > 0.0)` branch — call-graph-reachable (site exists), but a test case needs `vigHiProtect > 0` to actually execute the read at runtime; a default-uniform render would not exercise it. Flag for the oracle test plan: must include a `vigHiProtect>0` case. |
| `creative` `LUMA_WEIGHTS` | **Yes** | 3 reads across `applyVibrance`/`applyFadedFilm`/`applySplitTone`, all called unconditionally from `main`. |
| `hslSecondary` `LUMA_WEIGHTS` | **No — structurally dead** | Zero reads anywhere in the program (confirmed by full census, not `#ifdef`-gated — this is a genuinely unused declaration in the source). Must be flagged exactly as `bitEffects` was: admitted for validator/emitter type-check completeness only; **no oracle test can discriminate it**, because there is no code path, live or dead-branch, that ever loads it. The implementation report must say this explicitly rather than implying a render proved it correct. |
| All 74 index-expression sites | **Yes** | Every site sits in the sRGB↔linear transfer function or a LUT branch that directly determines output RGB channel values; a wrong lane mapping (e.g. writing lane 0 into lane 1) or a wrong per-lane conditional would change rendered pixels for any non-gray input. `lutHardLight`/`lutSolarize` are reachable only when `preset` is 20/22 respectively — the oracle test plan needs explicit cases selecting those two preset values (`preset` is a uniform, not a define, so this is a normal test-input concern, not a reachability concern). |

## 6. C++ lowering design — zero new runtime code required

Confirmed by direct inspection of `include/noisemaker/glsl_types.hpp` and
`emit_typed_cpp.py`, not assumed:

- **Global emission**: Smooth Edge's accepted output already shows the exact
  target shape for a `const vec3` global from a 3-literal constructor —
  `src/typed_generated/typed_slice.cpp:7469`: `const glsl::Vec3 LUMA_WEIGHTS
  = glsl::FloatExpr<3>(static_cast<float>(0.299), ...);`. Grade's five
  programs would emit the same pattern with their own literal values. No new
  emission code path — the existing `construct`-kind handling in
  `emit_typed_cpp.py:1204-1222` (the `vec3` 3-arg-all-float branch) already
  covers this exactly; only the admission gate (`_validate_source_globals`)
  needs a new identity-scoped carve-out per program, mirroring
  `authorized_smooth_edge_luma_weights_declaration` (`emit_typed_cpp.py:
  721-725`).
- **Index emission**: `emit_typed_cpp.py:1244`, the fallback for a *proved*
  index node, is `f"{base}[{index}]"` — plain native C++ subscript syntax,
  already fully generic over what kind of expression the index is. `Vec<N,
  T>::operator[]` already exists for both mutable and const access
  (`include/noisemaker/glsl_types.hpp:119-120`), already used by every
  existing FIXED_NINE/GRID/TASK19/TASK20 index capability. **The only
  missing piece is that `_proved_index` (`emit_typed_cpp.py:1129-1146`)
  currently only recognizes array-backed bases** (`self._proved_array(...)`)
  — a plain local `vec3` being lane-indexed by a loop variable has no
  "array" proof object to look up. A new `_proved_...` predicate (mirroring
  the shape of `_proved_index` but keyed to a new per-program frozen node-set
  rather than an array declaration) is needed on **both** sides (generator's
  `expression()` index branch and emitter's `_proved_index`), each
  independently re-authenticating from `source_hash` per this codebase's
  established two-independent-authorities pattern (Task 30's Extrude
  precedent). No matrix, vector, or arithmetic runtime symbol is missing —
  this is 100% generator/emitter Python work.

### Constraint (a): capability vocabulary must not grow

Two separate mechanisms, checked independently by direct code read:

- **`global_admission` never touches `used`/`APPROVED_CAPABILITIES` at
  all.** The admission loop building `admitted_globals`
  (`generate_typed_slice.py:1909-1954`) and its emitter mirror
  (`_validate_source_globals`) are **entirely separate code paths** from the
  `expression()`/`statement()` walker that populates `used` — confirmed by
  reading both functions top to bottom; neither calls `used.add(...)`
  anywhere. **Zero vocabulary risk for the five global carve-outs** — this
  mechanism is already vocabulary-free, exactly like Smooth Edge's precedent
  (which shipped without adding anything to the 44-entry tuple).
- **`index_expression_admission` DOES flow through `used.add(...)`.** Every
  existing index-admission track (`store_valid`/`grid_*`/`task19_*`/
  `task20_valid`) ends by calling `used.add(FIXED_NINE_CAPABILITY)` /
  `FIXED_GRID_CAPABILITY` / `FIXED_ARRAY_PARAMETER_CAPABILITY` /
  `FIXED_AFFINE_CENTERS13_CAPABILITY` — all four of which are **already**
  among the 44. Since grade's shape is structurally new (§1: id-indexed
  *write*, not covered by any of the four), adding a fifth distinct token
  would be a 45th vocabulary entry — **explicitly forbidden**. The required
  design, following the precedent already in the same function
  (`generate_typed_slice.py:2107-2109`: `round`/`all`/`lessThanEqual`/
  `floatBitsToUint`/`tanh` are exempted from `used.add(value.callee)`
  entirely, because they're validated by per-node identity instead of a
  generic vocabulary flag): the new `index`-kind branch for grade's proof
  track must gate admission purely on **node-identity membership in the
  frozen per-program proof set** and must **not call `used.add(...)` at
  all** for those matched sites — an explicit skip, symmetric with the
  existing callee skip-list, not a reused unrelated token (reusing e.g.
  `FIXED_NINE_CAPABILITY` for a structurally different shape would make the
  manifest's capability flag lie about what was actually admitted).

## 7. Projection

Recomputed independently from the live `typed_slice.json` (`hashlib.sha256`
of `"\n".join(sorted(keys)) + "\n"`, the exact formula asserted at
`generate_typed_slice.py:726-729`; reproduces the frozen
`ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2` for the
current 131-key list, confirming the formula before trusting the projection).

| | Current | Projected (+6) |
|---|---|---|
| Typed count | 131 | **137** |
| Typed-list SHA-256 | `ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2` | `dfb7c7c43d7fd118c4a1b9a266d6957a90b189ec63ac6b0d49538bd853a360d7` |
| Public count (typed + `filter/invert:inv` + `synth/solid:solid`) | 133 | **139** |
| Public-list SHA-256 | `29da87160abcee096a3c5f1c27e1b39381664ad3a7b71342c62a4b2c5e434f8c` | `a873c537d3d8ffb872859389812ae7c1e68954c9fcd381334eca4998195f319f` |
| Unported | 79 | **73** |

Matches the target-selection brief's "137 typed / 139 public / 73 unported"
exactly — independently reproduced, not copied.

**Typed ordinals (0-based, alphabetical) after insertion**:

| Program | New ordinal | Neighbours (prev, next) |
|---|---:|---|
| `filter/grade:creative` | 29 | `filter/glowingEdge:glowingEdge`, `filter/grade:hslSecondary` |
| `filter/grade:hslSecondary` | 30 | `filter/grade:creative`, `filter/grade:lut` |
| `filter/grade:lut` | 31 | `filter/grade:hslSecondary`, `filter/grade:primary` |
| `filter/grade:primary` | 32 | `filter/grade:lut`, `filter/grade:vignette` |
| `filter/grade:vignette` | 33 | `filter/grade:primary`, `filter/grade:wheels` |
| `filter/grade:wheels` | 34 | `filter/grade:vignette`, `filter/hatch:hatch` |

### Ordinal blast radius (per `task-31-ordinal-blast-radius.md`'s method)

**This is the largest ordinal shift of any task so far.** The insertion
point (`filter/grade:*` sorts alphabetically right after
`filter/glowingEdge:glowingEdge`) falls at position 29 of the current
131-key sorted list. Every currently-typed program whose key sorts at or
after that position — **102 of the 131 currently-typed programs** — shifts
its `typed_NN` ordinal by **+6** (computed by `bisect_left` against the live
sorted key list, not estimated). Concretely: `filter/hatch:hatch` moves
29→35, `filter/smooth:smoothEdge` moves 79→85, and every alphabetically-later
program through `synth/subdivide:subdivide` (130→136) shifts likewise.
`filter/extrude:extrude` (ordinal 25, sorts before `grade`) is **unaffected**
— confirmed by direct computation, not assumed from Task 30's smaller
example.

This dwarfs both Task 30 (shifted only programs after ordinal 25 — a late
alphabetical insertion) and Task 31 (shifted all 130, but only by +1, since
Caustic inserted at ordinal 0). A +6 shift across 102 programs means every
hardcoded `typed_NN`/ordinal-index assertion in `tests/test_typed_generator.py`
for those 102 programs needs updating — this is **mechanical but large**, not
conceptually hard; `task-31-ordinal-blast-radius.md`'s own caution applies
doubly here: exact line numbers must be re-derived fresh at implementation
time (they will have moved again since that census), and the assertions must
stay exact (not loosened to regex-normalized ordinals), per that document's
explicit reasoning. This blast radius is direct, load-bearing input to §9's
one-task-vs-split recommendation.

## 8. Capability boundary and test plan

### Capability boundary (explicit, per program)

**Admitted — exactly this, nothing else:**
- Five identity-scoped global profiles (`grade-primary-luma-weights-v1`,
  `grade-hslsecondary-luma-weights-v1`, `grade-wheels-luma-weights-v1`,
  `grade-vignette-luma-weights-v1`, `grade-creative-luma-weights-v1` or
  equivalent per-program names), each authenticating exactly one `const vec3`
  declaration by exact span/hash/lane-literal values, following
  `smooth_edge_luma_weights_profile.py`'s template exactly (own
  `_RAW_SHA256`/`_WHOLE_SHA256`/`_INTERFACE_SHA256`/`_DECLARATION_SHA256`/
  `_INITIALIZER_SHA256`/lane hashes per §4a).
- Six identity-scoped index profiles, one per program, each authenticating
  the exact node set frozen in §4b (10, 14, 10, 10, 10, 20 sites
  respectively) by span+SHA-256, admitting id-indexed reads AND writes of a
  local `vec3` inside a `for`-loop, nothing else.

**Explicitly BANNED — must be structurally impossible, not just untested:**
- Widening `APPROVED_TYPES`/`global_initializer`/`_validate_source_globals`
  generically to admit any `const vec3` with a constructor initializer for
  any program — must stay scoped to the five frozen declaration identities.
- Widening the index-admission machinery to admit *any* `id`-indexed write
  for any program — must stay scoped to the 74 frozen node identities
  (spans + SHA-256) across these six programs.
- Reusing `FIXED_NINE_CAPABILITY`/`FIXED_GRID_CAPABILITY`/
  `FIXED_ARRAY_PARAMETER_CAPABILITY`/`FIXED_AFFINE_CENTERS13_CAPABILITY` as
  the `used.add(...)` token for grade's index sites (mislabels the manifest;
  see §6 constraint (a) — the site must add nothing to `used`).
- Adding a 45th string to `APPROVED_CAPABILITIES`.
- Treating `hslSecondary`'s `LUMA_WEIGHTS` admission as render-validated —
  the implementation report must state it is validated structurally only
  (§5).

### Test plan — Python

Six per-program classes (or one parameterized suite iterating the six),
`Task32Grade{Primary,HslSecondary,Wheels,Vignette,Creative,Lut}Tests`,
each:
- authenticates its frozen global (where applicable) and index closures from
  raw source, proving `authenticate_...`/`apply_...` return the same objects
  for an independently reconstructed equal tree;
- exhaustively rejects single-axis structural mutations at all three
  authorities (profile, validator, emitter) — literal-index substitution,
  wrong lane count, extra/missing branch, foreign symbol id, wrong owning
  function — each candidate asserting its own structural precondition before
  checking rejection, per the Task 26 post-mortem's explicit warning (cited
  in Task 30's brief) against vacuous/mislabeled mutations;
- covers history/coexistence: fresh `APPROVED_CAPABILITIES`/`APPROVED_TYPES`
  tuple check, no collision with any prior task's profile;
- **constraint (d) — coarse-hash-gate bypass, modeled exactly on
  `test_task31_node_level_closure_logic_rejects_past_the_coarse_hash_gate`**
  (`tests/test_typed_generator.py:15422`): for each profile, re-freeze
  `_FUNCTIONS_SHA256`/`_WHOLE_SHA256`/`_INTERFACE_SHA256` via
  `mock.patch.multiple` to match a *mutated* tree (so the coarse "source,
  define, function, whole-program, or interface mismatch" gate cannot
  short-circuit the check), assert the mutation genuinely changed
  `_sha(functions)` first (non-vacuity check), then assert rejection fires
  with a **specific node-level message** (e.g. "closure site cardinality
  mismatch" / "closure node identity mismatch" / "index kind mismatch" —
  exact wording TBD at implementation) and assert the **coarse message did
  not fire**. Required for every mutation axis in every one of the six
  profiles — 6 programs × several axes each, all individually gated this
  way, not just one representative case.
- ordinal blast-radius test: assert removing all six grade keys from the
  live typed list regenerates the frozen Task 31 (131-count) outputs
  byte-for-byte, per the reconstruction-test pattern already used for
  Tasks 28→29→30→31.

### Test plan — Native

- Direct fixture rows per program covering: a value that takes the `if`
  branch and one that takes the `else` branch of each per-lane conditional
  (`<=0.04045` / `>0.04045` etc.), a `vigHiProtect>0` case for `vignette`
  (§5 discriminability), and `preset==20`/`preset==22` cases for `lut`
  (reaching `lutHardLight`/`lutSolarize`).
- Discriminating mutations per constraint (c): swap a write's target lane
  (e.g. write `linear[i]` results into `linear[(i+1)%3]`) and confirm
  divergence against the oracle for a non-gray input; swap the per-lane
  conditional operator and confirm divergence at a boundary input
  (`srgb[i]==0.04045` exactly, `rgb[i]==threshold` exactly for
  `lutSolarize`). Report exact divergence fraction per mutation, per the
  Extrude-precedent table format (§ Task 30's brief), not a pass/fail-only
  claim.
- Explicit non-discriminability disclosure for `hslSecondary`'s
  `LUMA_WEIGHTS`: no oracle mutation is claimed for it; the native suite
  should include a comment/assertion documenting that this global has zero
  live consumers, so a future maintainer doesn't waste time hunting for a
  render-based test that cannot exist.
- Full pixel/parity gates per the standing pattern: Debug/Release
  warnings-as-errors + CTest, ASan/UBSan, all Task15-31 oracles unchanged,
  independent implementation review with zero Critical/Important.

### Constraint (e): narrowing-point check — does NOT apply to this cluster

Checked directly against the actual arithmetic in all six programs, not
assumed. The FloatExpr-narrowing hazard (Curl/lensFlare/tetraCosine/degauss)
is specific to the `NOISEMAKER_GLSL_UNARY_VECTOR` macro's `FloatExpr<N>`
overload, which only fires when a **vector-valued** expression is passed to
a unary function and the JS side scalarizes it. None of the 74 new index
sites or the 5 new globals route through that macro:
- Every index-expression site resolves `base[index]` to a **scalar `float`**
  (a single lane of a `vec3`, via `Vec<N,T>::operator[]`, which returns a
  concrete `float`/`float&`, never a lazy `FloatExpr`). The arithmetic
  around each site (`/`, `+`, `*`, and `pow(scalar, scalar)` in the `pow`
  branches of `srgbToLinear`/`linearToSrgb`) all operates on already-scalar
  operands — `pow`'s two-argument scalar overload is a different code path
  from the single-argument `NOISEMAKER_GLSL_UNARY_VECTOR` family entirely.
- The new globals feed `dot(rgb, LUMA_WEIGHTS)` — a two-vector reduction to
  scalar, not a unary applied to a vector.
No new unary-vector-macro call site is introduced by this cluster's two
capabilities. This does not exempt the cluster from full oracle parity
testing (the authoritative gate), but there is no structural reason to
expect the Curl-class hazard here, and no `_lanewise`-style split is needed
for this task.

## 9. One task or split?

**Recommendation: land as ONE task, but structure the implementation and
review as six explicitly-enumerated sub-units within it, not as one
undifferentiated commit.**

Arguments for one task (not six):
- All six share the exact same two capability shapes (§1, §2) — splitting
  would mean re-deriving and re-reviewing the same admission logic six
  times, with no shape-level learning carried between sub-tasks the way
  there was between, say, Task 30 (bvec2 relational) and prior unrelated
  tasks.
- Five of the six share byte-identical `srgbToLinear`/`linearToSrgb` bodies
  (§1) — a single index-admission code change in the generator/emitter
  benefits all six simultaneously; splitting would not reduce the size of
  that shared code change, only the number of per-program profile files
  touched per commit.
- The projection (§7) and the ordinal blast radius (§7) are properties of
  the *insertion*, not of any one program — landing them separately would
  mean paying the 102-program ordinal-shift cost (and its accompanying test
  file diff) once per sub-task instead of once total, multiplying reviewer
  burden on a mechanical concern for no benefit.

Arguments for splitting (acknowledged, why they don't win):
- Six programs from one task is unprecedented (every prior task ported
  exactly one program). This is a real precedent-setting concern, but the
  novelty is about *scale*, not *risk*: unlike, e.g., bundling Curl's `tanh`
  fix with unrelated programs (explicitly rejected in `task-31-curl-SOLVED
  .md` as a blanket change that regressed three programs), these six don't
  interact with each other's runtime state, don't share any C++ code beyond
  what's independently re-authenticated per program, and one program failing
  its own profile can't silently pass another's (each authenticates from its
  own `source_hash`).
- `hslSecondary`'s dead global (§5) is qualitatively different from the
  other four's live one — but this is a **discriminability property to
  document**, not a **reason to isolate the program**; the profile/proof
  work is identical regardless of whether the global is later read.

**Concrete structuring**: land one task whose implementation commit
introduces (a) the shared index-expression proof-track machinery in
`generate_typed_slice.py`/`emit_typed_cpp.py` once, (b) five global profiles
+ one shared index-profile-per-program (six modules under
`frontend/grade_*_profile.py` or a single parameterized module — implementer's
choice, not load-bearing), and (c) the ordinal/test-suite mechanical updates
once. The test plan (§8) should still enumerate all six programs' fixtures
and discriminability findings **individually and explicitly** in the
implementation report — not folded into one aggregate "6/6 pass" claim — so
`hslSecondary`'s non-discriminable global and `vignette`'s conditional-only
reachability don't get lost in an averaged success statement.

## Artifacts

- `docs/port-engineering/task32b_grade_identity.py` +
  `task32b_grade_identity_output.json` — full per-program identity, global,
  and index-node census (source of §3, §4, most of §5).
- `docs/port-engineering/task32b_validate_baseline.py` +
  `task32b_validate_baseline_output.json` — independent unpatched
  validator/emitter re-run, 44-entry vocabulary assertion (source of §5, §6
  constraint (a)).
- No file under `noisemaker-for-cpp/` or `noisemaker-for-cpp-for-cpu/` was
  modified. No git command was run. No monkeypatch was left applied (both
  probe scripts either apply no patches or verify identity-restoration
  before exiting).
