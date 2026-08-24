# Per-program characterization of the 17 derivative-blocked programs

Status: **read-only characterization**. Nothing under
`.` or
`../noisemaker-for-cpu` was modified. No `git` command was
run anywhere. All facts below come from either (a) direct, unmodified
importing and invocation of the real `tools.glslcpp` frontend and generator
modules from `noisemaker-for-cpp` (the "VALIDATOR" =
`tools/glslcpp/generate_typed_slice.py`, the "EMITTER" =
`tools/glslcpp/emit_typed_cpp.py`'s sibling entry points), run in-process from
the extraction script in this directory, or (b) direct `Read` of the pinned
corpus source files. Every number in this document is reproducible by running
`extract_facts.py` (below) against the pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`.

This document supplies the per-program facts requested for the 17 programs
named in the task brief. It assumes and does not re-derive
`docs/port-engineering/derivatives/derivatives-architecture.md` (the
architecture prototype doc, §1 and §3 in particular) -- this document narrows,
mechanically verifies, and in two places (§0.3, §0.4) **corrects** claims from
that doc.

---

## 0. Headline findings (read this first)

### 0.1 All 17 programs parse and semantically analyze successfully TODAY

`tools/glslcpp/frontend/body_semantic.py` already carries `dFdx`, `dFdy`, and
`fwidth` in its builtin table (`_BUILTIN_IDS` at line 21-29, `_BUILTIN_FAMILIES`
at line 33-53, both mapping to a `"derivative"` family whose type rule --
same-shape-in-same-shape-out for any `float`-generic argument -- is
implemented at line 390: `if family == "derivative": return types[0] if
len(types) == 1 and float_gen(types[0]) else None`). Recognizing the call sets
`self.uses_derivatives = True` (line 344), which `semantic.py:305-306` already
threads into `TypedProgram.resources.uses_derivatives` exactly like
`uses_texture`. This means **`parse_program` + `analyze_program` -- the
frontend -- need no code change at all** to admit the 17. This refines
architecture-doc §5.1's claim that "the semantic analyzer never sets
`analyzer.uses_derivatives = True` because `dFdx`/`dFdy`/`fwidth` are not yet
in its recognized-builtin table (they're currently unknown identifiers)" --
that claim is **not correct as of this read**; the recognized-builtin table
already contains them. (Whether this is because `body_semantic.py` was written
or extended after the architecture doc's read, or because that doc's author
checked `semantic.py`/`typed_ir.py` but not `body_semantic.py`, is not
determinable from a read-only vantage point and is reported as a correction,
not explained away.)

Verified for all 17 by running `parse_program` then `analyze_program` with
each program's exact `_defaults()`-authorized define map:
`success: 17/17` (§4, `extract_facts.py` output).

### 0.2 What IS still missing: the generator's frozen-vocabulary walk

The frontend succeeding is not the same as the pipeline succeeding. The
**generator** (`generate_typed_slice.py`'s `validate_capabilities`, the
function the task brief calls "the VALIDATOR") walks the same typed IR a
second time and rejects any builtin callee not in the frozen `_BUILTINS`
frozenset (derived from the 44-entry `APPROVED_CAPABILITIES` tuple), at
`generate_typed_slice.py:2088-2089`:
```python
elif value.callee not in _BUILTINS:
    raise GeneratorError(f"{location(value)}: unsupported builtin {value.callee}")
```
`dFdx`/`dFdy`/`fwidth` are not in `_BUILTINS`, so **today**, all 17 fail here
(not in the frontend). This is exactly the gap the architecture doc's §2/§5.2
identify and the reason the task brief specifies node-identity admission
(mirroring the existing `round`/`tanh`/`floatBitsToUint`/`all`+`lessThanEqual`
pattern at `generate_typed_slice.py:2057-2089`) rather than a 45th vocabulary
token: a bare capability-token admission would also have to cross the walk's
final consistency check at line 2324-2325 (`missing = sorted(used -
set(capabilities))`), which is exactly the mechanism the `round`/`tanh`/etc.
identity-gates dodge by **never** calling `used.add(value.callee)` for their
admitted callee (`generate_typed_slice.py:2107-2109`).

### 0.3 Correction to the "17": two of them have a SECOND, unrelated blocker

Running the real `validate_capabilities()` against each of the 17, patched
**only** to admit `dFdx`/`dFdy`/`fwidth` by name (an in-memory,
this-process-only test bypass -- see §4.2 methodology, never written to any
file), isolates whether derivatives are the *only* thing standing between a
program and full validation:

- **15 of 17 are clean**: once derivatives are admitted (by whatever
  mechanism), `validate_capabilities` raises nothing else for them.
- **`filter/posterize:posterize` has a second blocker**: `round(levels_raw)`
  at source line 65 (`posterize.glsl`) is a real, reachable, unconditional
  call to the `round` builtin. `round` is only admitted by node identity for
  one specific already-ported program (`GATHER_SORTED_KEY`, via
  `gather_sorted_round_profile`/`authenticate_gather_sorted_round_to_int`);
  posterize is a different key, so `authorized_round` stays `None` and every
  `round` call in posterize's IR is rejected:
  `filter/posterize:posterize:60:34: unsupported builtin round` (span is in
  `typed.source`, not raw-file, coordinates -- see the per-program section).
  This `round` call is unrelated to and does not interact with posterize's
  `fwidth` call (different statement, no shared guard).
- **`filter/waves:waves` has a second blocker**: `any(notEqual(tileOffset,
  vec2(0.0)))` at source lines 48 and 74 (`waves.glsl`) is a real, reachable
  call to the `any` builtin. Unlike `round`, **`any` has zero admission path
  in the generator at all** -- it is not in `APPROVED_CAPABILITIES`, not in
  `_BUILTINS`, and not named in any of the node-identity exception branches
  (`round`, `tanh`, `floatBitsToUint`, `all`+`lessThanEqual` -- note `all` is
  identity-gated for Extrude but `any` never appears anywhere in
  `generate_typed_slice.py`, confirmed by a direct grep returning zero hits).
  Result: `filter/waves:waves:41:9: unsupported builtin any`. This call is
  also unrelated to and does not share a guard with waves' `dFdx`/`dFdy`
  calls.

**So the true, currently-landable count once derivatives are admitted is 15,
not 17.** `posterize` and `waves` need their own, separate admission work
(`round` node-identity extension for posterize; a *new* `any` admission path
-- via `bool_reduction`-family node identity or a capability token, an actual
design decision outside this task's scope -- for waves) in addition to
derivatives. This is stated as a **BLOCKER**, per the task's instruction to
name blockers explicitly rather than wave programs through.

### 0.4 Correction/refinement to architecture-doc §3.2's halftone entry

The architecture doc counts `halftone` as one of "2 of 17 [that] call
`fwidth` unconditionally inside a plain helper function
(`halftoneCoverage`, `roundDotCoverage`...)", treating both call sites as
live. Reading `halftone.glsl`'s `main()` (and confirming mechanically via a
call-graph walk of the typed IR, §4.3) shows the pinned defines
(`MODE=0, PATTERN=0`) put the *entire* monochrome branch -- including the
one and only call to `halftoneCoverage` -- inside `#else` of `#if MODE == 0`,
which is preprocessor-eliminated before parsing ever sees it. Under the
pinned defines:
- `halftoneCoverage`'s `fwidth` call site (in the typed IR, since the
  function itself is still defined and still type-checked) is **called zero
  times from `main()`** -- confirmed by walking `main()`'s call expressions:
  no `call` node targets `halftoneCoverage` anywhere in `main`. It cannot be
  an ordinal landmine because it never executes.
- `roundDotCoverage`'s `fwidth` call site is the only one that matters. It is
  called **exactly 4 times from `main()`**, unconditionally, at loop depth 0,
  in fixed textual order (cyan, magenta, yellow, black -- source lines
  130-133), each call containing exactly one `fwidth(centerDistance)` call.
  So halftone's real per-pixel derivative-call sequence is **4 scalar
  `fwidth` calls, ordinals 0-3, always in C/M/Y/K order, unconditional**.

This does not change the "17" count (halftone was already correctly included)
or its ordinal-safety verdict (still safe -- see §1), but it changes *why*
and *what actually executes*, which matters for authoring an accurate gate
and for sizing the runtime cost (4 probed+replayed derivative ordinals per
pixel for this one program, not 2).

---

## 1. Ordinal-count stability -- verdict for all 17

Per-program detail is in §5; this is the roll-up.

| Guard shape | Programs | Verdict | Reasoning |
|---|---|---|---|
| `if (antialias) { ... }`, `antialias` a directly-referenced `uniform bool` | bulge, celShadingColor, lens, lensWarp, octaveWarp, pinch, polar, pondRipples, posterize, spiral, step, tunnel, warp, waves (14) | **SAFE** | `antialias` is a GLSL `uniform`: identical value for every fragment invocation in one `run_pass` call, and -- critically -- identical across all 4 quad-corner probes and the real replay, because the reference's `probe()` copies every context field except `fragCoord`/`uv` unchanged (`{ ...context, fragCoord, uv }`, `glsl-runtime.js:484`); `antialias` is never touched. So the branch executes on all 5 kernel invocations making up one output pixel, or on none of them -- never a mix. Confirmed mechanically: each guard's condition expression contains only identifiers with `storage == "uniform"` (`_condition_summary`, no non-uniform identifier reachable in any of the 14 conditions). |
| Unconditional (no runtime guard at all) | halftone (4 executed `fwidth` calls in `roundDotCoverage`, called 4x from `main`), stThreshold (1 `fwidth` call directly in `main`) | **SAFE, trivially** | A call with no guard executes on every one of the 5 invocations by construction. Confirmed: `unconditional: true` for both, and (halftone specifically) `main_call_sites` shows the 4 `roundDotCoverage` calls are themselves unconditional and outside any loop (`loop_depth: 0`). |
| `#if MODE == 0` (compile-time) | stipple (1 `fwidth` call, `MODE` pinned to `0` by `_defaults`) | **SAFE, trivially** | Preprocessor branches are resolved once, before parsing, for the whole pinned program variant. They cannot vary between the 4 probe invocations and the replay invocation of a single output pixel, because all 5 invocations run the *same* compiled kernel body. |

**No program in the 17 gates a derivative call on anything that varies
per-fragment** (no `uv`, `gl_FragCoord`, texture sample, or noise value ever
appears in a guard condition wrapping a derivative call). That would be the
actual landmine (e.g. `if (uv.x > 0.5) { dFdx(...) }` desynchronizing the
four probe corners' ordinal sequences) and it does not occur anywhere in the
17 -- checked exhaustively via the `_condition_summary` identifier-storage
walk over every enclosing `if` for every one of the 20 derivative call sites
found in the typed IR (17 programs, 2 IR-level sites for halftone since
`halftoneCoverage`'s is present-but-dead, 1 site each for the other 16).

**No derivative call site sits inside a loop** in any of the 17 (checked via
explicit loop-depth tracking during the same walk; every site reports
`enclosing_loop_depth: 0`). Programs that do contain loops elsewhere
(halftone's `boxBlur3`, octaveWarp's octave-accumulation loop, stThreshold's
`fbm`, stipple's `voronoiCell`) all keep those loops in a different function
or a different, non-enclosing statement from the derivative call itself.

**No program I could not prove stable.** All 17 (all 20 IR-level call sites)
have a fully mechanically classified guard. There are no "needs manual
trace"/unresolved cases to report.

**Argument widths exercised across the 17**: `float` (halftone x4-executed +
1 dead, stThreshold, stipple), `vec2` (the 11 `dFdx`+`dFdy` pair programs),
`vec3` (celShadingColor, posterize, step -- all via `fwidth`). **No `vec4`
case occurs anywhere in the 17**, which matches and closes out
architecture-doc §6's flagged gap ("`vec4` derivative overload untested") as
*moot for this specific set of 17 programs* (a `vec3`-argument prototype test
is still worth adding before trusting celShadingColor/posterize/step, per
that doc's own note -- `vec4` genuinely does not need to be tested to cover
these 17, since none of them call a derivative on a `vec4`).

---

## 2. "Would it actually land" -- the corrected count

| Metric | Count |
|---|---|
| Programs in the named 17 | 17 |
| Frontend (`parse_program` + `analyze_program`) succeeds today, no change needed | 17 / 17 |
| Ordinal-stability proven safe | 17 / 17 |
| Would land cleanly through the full generator (`validate_capabilities`) once dFdx/dFdy/fwidth are admitted by node identity, with NO other blocker | **15 / 17** |
| Blocked by derivatives AND a second, unrelated, already-identified capability gap | **2 / 17** -- `filter/posterize:posterize` (`round`, unadmitted for this key), `filter/waves:waves` (`any`, unadmitted anywhere in the generator) |

---

## 3. Methodology and provenance

All facts were produced by `extract_facts.py` (verbatim copy in §6 of this
document; the runnable file is alongside this document at
`extract_facts.py`), which:

1. Imports `tools.glslcpp.check_corpus`, `tools.glslcpp.frontend`
   (`parse_program`, `FrontendError`), `tools.glslcpp.frontend.diagnostics`
   (`SemanticError`), `tools.glslcpp.frontend.semantic.analyze_program`, and
   `tools.glslcpp.generate_typed_slice` (`_defaults`, `GeneratorError`,
   `validate_capabilities`, `_BUILTINS`, `APPROVED_CAPABILITIES`) directly
   from the unmodified `.` checkout.
2. For each of the 17 program keys, reads the manifest entry from
   `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/manifest.json`,
   the authorized define map via `generate_typed_slice._defaults(repo, key)`
   (which reads `metadata.json` through
   `check_semantics._metadata_defaults`), and the raw corpus source.
3. Runs `parse_program(raw_source, key, defines)` then
   `analyze_program(parsed, key)` -- the real frontend, no mocking.
4. Walks the resulting `TypedProgram`'s function bodies to find every
   `dFdx`/`dFdy`/`fwidth` call (`kind == "builtin"`, `callee` in that set),
   recording builtin, argument type, enclosing function, `TypedExpression.span`
   (which -- per the task brief's warning, confirmed true -- indexes
   `typed.source`, the *normalized* source, not the raw corpus file), the full
   stack of enclosing `if` guards with each guard's referenced-identifier
   storages, and enclosing loop depth.
5. Separately walks `main()`'s own call expressions (for the one case,
   halftone, where a derivative call lives in a helper function) to establish
   real per-pixel invocation multiplicity and reachability from `main`.
6. Calls the real `generate_typed_slice.validate_capabilities()` against each
   program's typed IR, with `_BUILTINS` and `APPROVED_CAPABILITIES`
   temporarily extended (a Python-process-local, in-memory monkeypatch,
   restored in a `finally` block, never written to any file) to admit
   `dFdx`/`dFdy`/`fwidth` by name -- purely to observe whether any *other*
   `GeneratorError` still fires. This is a test-only bypass of the frozen-44
   rule for observability; it is explicitly **not** a proposal for how
   production admission should work (the task brief's node-identity
   requirement stands; see §0.2).
7. Computes the exact `functions`/`whole`/`interface` sha256 digests the way
   `validate_current_vocabulary_degauss`/`_crt` do
   (`generate_typed_slice.py:400-421`), from the *unmodified* frontend's
   output -- valid today and stable going forward, since the frontend needs
   no change (§0.1).
8. Writes `derivative-program-facts.json`.

Every number in §0-§2 and every per-program fact in §5 is machine-derived
from this script's actual output (`derivative-program-facts.json`), not
hand-transcribed from the GLSL source -- consistent with the task's
instruction to extract facts mechanically rather than reading GLSL by eye.
Manual source reads (quoted inline where used, e.g. §0.4's `halftone.glsl`
excerpt and §0.3's `posterize.glsl`/`waves.glsl` line citations) were used
only to explain *why* the mechanical result is what it is, never as the
source of a count or a pass/fail verdict.

---

## 4. Summary table

| Program key | Defines | Builtin(s) | Arg type(s) | IR sites | Executed ordinals/pixel | Guard | Ordinal-safe | Validator beyond derivatives |
|---|---|---|---|---|---|---|---|---|
| `filter/bulge:bulge` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/celShading:celShadingColor` | `{}` | fwidth | vec3 | 1 | 1 | `antialias` (uniform) | Safe | Clean |
| `filter/halftone:halftone` | `{MODE:0, PATTERN:0}` | fwidth | float | 2 (1 dead) | 4 (roundDotCoverage x4; halftoneCoverage unreachable) | unconditional | Safe | Clean |
| `filter/lens:lens` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/lensWarp:lensWarp` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/octaveWarp:octaveWarp` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/pinch:pinch` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/polar:polar` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/pondRipples:pondRipples` | `{STYLE:2, WRAP:0}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/posterize:posterize` | `{}` | fwidth | vec3 | 1 | 1 | `antialias` (uniform) | Safe | **BLOCKED** (`round`, unrelated) |
| `filter/spiral:spiral` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/stamp:stThreshold` | `{}` | fwidth | float | 1 | 1 | unconditional | Safe | Clean |
| `filter/step:step` | `{}` | fwidth | vec3 | 1 | 1 | `antialias` (uniform) | Safe | Clean |
| `filter/stipple:stipple` | `{MODE:0}` | fwidth | float | 1 | 1 | `#if MODE==0` (compile-time) | Safe | Clean |
| `filter/tunnel:tunnel` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/warp:warp` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | Clean |
| `filter/waves:waves` | `{}` | dFdx, dFdy | vec2 | 2 | 2 | `antialias` (uniform) | Safe | **BLOCKED** (`any`, unrelated) |

15 rows are fully clean end-to-end (once derivatives are node-identity
admitted); 2 rows (posterize, waves) need one additional, unrelated
admission each.

---

## 5. Per-program detail

The tables below are generated verbatim from `derivative-program-facts.json`
by `gen_sections.py` (also alongside this document). Field order in the
"expected resources tuple" block matches
`validate_current_vocabulary_degauss`/`_crt`'s assertion order exactly
(`generate_typed_slice.py:454-460`, `typed.resources.{uniforms, samplers,
outputs, uses_texture, uses_derivatives}`). Declaration tuples, full function
profile tuples (id, name, body-statement-count, sha256 of `repr(function)`),
and the complete guard-condition detail for every site are in
`derivative-program-facts.json` under each program's key -- this section
gives the load-bearing subset plus pointers; nothing here needs re-deriving
before gate authoring, only transcribing into a
`validate_current_vocabulary_<name>` function shaped like the `degauss`/`crt`
examples.

### `filter/bulge:bulge`
- Source: `sources/filter/bulge/bulge.glsl` (2352 raw bytes, sha256 `87f26ffa13ffe946d94d92a00bd45ca3a9787b9ee402dfe04ebc3d4a911eb170`; 1953 normalized bytes, sha256 `3526dd01153e7def1e3eb6f1dff1b39cfdb1ba275aa81b92732c07206d41d060`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'strength', 'aspectLens', 'wrap', 'rotation', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 10 globals; Functions: 2 (`main, rotate2D`)
- `local_type_names`: `['float', 'float', 'vec2', 'vec2', 'float', 'float', 'float', 'vec2', 'vec2', 'vec2', 'vec4']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=9b1c1b27669b99f6ef51a1f7796a570acf7b4be401a67402e9b59da02d7c7154`, `whole_sha256=11cd75f0fc758ad6de796bc1a1448902214f946dba727120bce3603c7e4a3faf`, `interface_sha256=b5e71e3377314023e8738e808a6634b7827f0408447bea21a405e4a9a0aae949`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 74:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 75:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/celShading:celShadingColor`
- Source: `sources/filter/celShading/celShadingColor.glsl` (2780 raw bytes, sha256 `90fa87484d3549bdaa2ddca4836a7ca8602ad4f1f30aa87a72841d4e013521f4`; 2530 normalized bytes, sha256 `52086cb69a9db0eccff5d37d369f94f672a8290a006999f00ca81742ca1e3d4f`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('tileOffset', 'fullResolution', 'inputTex', 'levels', 'gamma', 'antialias', 'lightDirection', 'strength'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 10 globals; Functions: 6 (`linear_to_srgb_component, linear_to_srgb_rgb, main, pow_vec3, srgb_to_linear_component, srgb_to_linear_rgb`)
- `local_type_names`: `['vec2', 'ivec2', 'vec2', 'vec4', 'float', 'vec3', 'float', 'float', 'float', 'vec3', 'float', 'float', 'float', 'float', 'vec3', 'vec3', 'vec3', 'vec3', 'vec3', 'vec3']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=ab51cb78b516454f8be97ab2bb226f31efb2f3daacba4521ab93bc325a0924cd`, `whole_sha256=9012723f042dcc2fc823ffb36ef7e4cdbff48529f8ec074bd89cd00c58b9e53a`, `interface_sha256=337682508a486618d2deb6bc1c0275078132c3e5c24fc16b8e54c4553cb2e684`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `fwidth` | `vec3` | `main` | 84:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/halftone:halftone`
- Source: `sources/filter/halftone/halftone.glsl` (8440 raw bytes, sha256 `063ddb13f5fffc6f957d4be0a60b0408ff706d6111fd4e3ba52582f7507c7ad7`; 3828 normalized bytes, sha256 `f62382b453796c16948943e002b2498021827314793ab80f0fd66473c4fcb307`)
- Authorized define map (`_defaults`): `{"MODE": 0, "PATTERN": 0}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'frequency', 'cyanAngle', 'magentaAngle', 'yellowAngle', 'blackAngle', 'monoAngle', 'sharpness', 'inkColor', 'paperColor'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 18 globals; Functions: 9 (`boxBlur3, cellSampleFromRuv, halftoneCoverage, lum, main, rgbToCmyk, rotate2D, roundDotCoverage, tonemap2`)
- `local_type_names`: `['float', 'float', 'vec3', 'float', 'float', 'float', 'vec3', 'int', 'int', 'vec2', 'vec2', 'vec2', 'vec2', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'vec2', 'vec2', 'vec2', 'float', 'vec2', 'vec2', 'vec2', 'vec2', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'vec3']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=2, unproved_loop_count=0, max_effective_depth=2, max_lexical_product=9, entrypoint_charge=48, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=9d055dcad8dc24cfa85c7a1a4317b0fe849e7202c512affb4c682cab23d3cebd`, `whole_sha256=5ddb9ed688497772657c9d3eda11e90eb703b151b779a580ba234f49f236697e`, `interface_sha256=2f2bdb794aeb2fbb252bf6c80fda24f0d73bb20754b11eed0a051b982cb5722f`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `fwidth` | `float` | `halftoneCoverage` | 87:24-33 | 0 | unconditional |
| 1 | `fwidth` | `float` | `roundDotCoverage` | 109:30-52 | 0 | unconditional |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/lens:lens`
- Source: `sources/filter/lens/lens.glsl` (2909 raw bytes, sha256 `6633d8c7b1ab23600cb25bb87f3f67c5d1d148b0626169f24de520fbce9e64a5`; 2194 normalized bytes, sha256 `72c7169c1f606090fd80c1a9763b757af6aed98ac54543580c480d2a04a95d61`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'tileOffset', 'fullResolution', 'lensDisplacement', 'aspectLens', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 8 globals; Functions: 1 (`main`)
- `local_type_names`: `['vec2', 'ivec2', 'vec2', 'vec2', 'vec2', 'float', 'float', 'vec2', 'vec2', 'float', 'float', 'float', 'float', 'float', 'vec2', 'bool', 'float', 'float', 'vec2', 'vec2', 'vec2', 'vec2', 'vec2', 'vec4']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=4eaba58099b88677cb99c1a603433a77be8638868cf4e3fd6ddedbc57555e249`, `whole_sha256=7ea51ed2362674cb6fddae77b82a0c5b49280021c28d3504033f98e8a99e1fa0`, `interface_sha256=370d530b1fd84b9a3e0ddb8665f189bc10bf6d4da1f84349aac583dc6fd29e7a`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 66:19-34 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 67:19-34 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/lensWarp:lensWarp`
- Source: `sources/filter/lensWarp/lensWarp.glsl` (4033 raw bytes, sha256 `543b53a26b14dfdcf979e2601eaad32d6ec683c41427301b851173334a670480`; 3446 normalized bytes, sha256 `4d2c5e5d33e31c902b0506daa6f8ec0a1c76dfc3355c6c5f5604e752a6ed862d`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'time', 'displacement', 'speed', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 9 globals; Functions: 7 (`grid, main, pcg, perlinNoise, prng, smootherstep, smoothlerp`)
- `local_type_names`: `['float', 'vec2', 'vec2', 'vec2', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'vec2', 'float', 'vec2', 'float', 'float', 'vec2', 'vec2', 'float', 'float', 'vec2', 'float', 'float', 'vec2', 'vec2', 'vec2', 'vec4', 'vec2']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=f8c4e268beaa15b2dc4c4bdaae870d0c14d180c75440c8db57aa831ab4b67286`, `whole_sha256=8dfa839595d6a87429845ed4015cb25ac9ee162631d1b5d491ee0bfeeca2c647`, `interface_sha256=aad79dc32807a531c08566f437e17df28d5d5f54c552626488211aa5de6c11da`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 98:19-27 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 99:19-27 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/octaveWarp:octaveWarp`
- Source: `sources/filter/octaveWarp/octaveWarp.glsl` (4902 raw bytes, sha256 `ced7dca971a24fb3d8a48641c7bb66c4af637a57984d45ddc9e51f0492a59bea`; 4110 normalized bytes, sha256 `f2b635bd9858cc2f9f33d5490844fc331ca3f8d52f10c76b30f52d3492918a4b`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'time', 'frequency', 'octaves', 'displacement', 'speed', 'wrap', 'seed', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 14 globals; Functions: 6 (`hash21, main, noise, pcg, simplexNoise, wrapFloat`)
- `local_type_names`: `['uvec3', 'vec2', 'vec2', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'vec2', 'vec2', 'float', 'float', 'float', 'float', 'vec2', 'vec2', 'vec2', 'int', 'float', 'int', 'float', 'vec2', 'float', 'float', 'vec2', 'float', 'float', 'float', 'vec2', 'vec2', 'vec2', 'vec2', 'vec4']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=1, unproved_loop_count=0, max_effective_depth=1, max_lexical_product=10, entrypoint_charge=10, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=44d5a0bd997f31c441f25ab198858bc7fc902949014c0c350172947e0ef21ea8`, `whole_sha256=8bb2272c78dba6aa780c7b934852617e478bec35dfe47af03fb2aaffc546e492`, `interface_sha256=4b6c99dad1fc3289edd53b8d830722ab7aaec2cb6c442939c80508064de20fb7`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 146:19-32 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 147:19-32 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/pinch:pinch`
- Source: `sources/filter/pinch/pinch.glsl` (2296 raw bytes, sha256 `031405e087822fd10b07d972e53f2f6d2da95f67d9c56605cbc104e0b955d71c`; 1954 normalized bytes, sha256 `2f6e983bdc1a21b043ef40ccdf5f02902a38274fcbac7db5c5f9cd231749427d`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'strength', 'aspectLens', 'wrap', 'rotation', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 10 globals; Functions: 2 (`main, rotate2D`)
- `local_type_names`: `['float', 'float', 'vec2', 'vec2', 'float', 'float', 'float', 'vec2', 'vec2', 'vec2', 'vec4']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=9d5adc1c2e6f6976072522df0066fdf1a3c2dc490246173675fff139e9ffc7cf`, `whole_sha256=c5c15b401c3e8601a4a2ebe97be02840fc3327b3e9ea6a94628db76e1b19f5d1`, `interface_sha256=c502a3f375d985c7c8a74c1bbbbf32f1cc44d78b3a98fb61ef26ee5fcf03d600`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 73:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 74:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/polar:polar`
- Source: `sources/filter/polar/polar.glsl` (2027 raw bytes, sha256 `391b82e45bc2ea9799de1a200afbd735af96ad15627695d46cfc8caa1298a36d`; 1933 normalized bytes, sha256 `c928b6cbc717ec436c915e763a00f23ce67eb4dd338f0bdd365dbd8dfc217785`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'tileOffset', 'fullResolution', 'time', 'polarMode', 'speed', 'rotation', 'scale', 'aspectLens', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 12 globals; Functions: 5 (`main, polarCoords, smod, smod2, vortexCoords`)
- `local_type_names`: `['vec2', 'float', 'ivec2', 'vec2', 'vec2', 'vec2', 'float', 'vec2', 'vec2', 'vec2', 'vec4']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=8d507070121c5ad9020357677186846e9e133b82d6f27421efafdc367699a22d`, `whole_sha256=5486890330682b31c6df1ea2e5fdcb1b4cdb1ca461efcce72007d7e327abfe9a`, `interface_sha256=a812e3ae963a9cf4bc898d90678f536d5e502aa78efec86eb52eb2116f94aa41`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 61:19-30 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 62:19-30 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/pondRipples:pondRipples`
- Source: `sources/filter/pondRipples/pondRipples.glsl` (5187 raw bytes, sha256 `2958de77f0cdf2a21a00d1505ea75f26df5b66dd7f2cb98431e27178d3386c3d`; 2017 normalized bytes, sha256 `4c67016be6c30065f90ac45df03be2c633a3809bfcf992a226d9aec956710f91`)
- Authorized define map (`_defaults`): `{"STYLE": 2, "WRAP": 0}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'amount', 'ridges', 'speed', 'time', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 10 globals; Functions: 1 (`main`)
- `local_type_names`: `['float', 'vec2', 'vec2', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'vec2', 'float', 'float', 'float', 'vec2', 'vec2', 'vec2', 'vec2', 'vec4']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=0a92078091db5118a786f4236ae51102d437f4ff412ff31be4c383d7ee066721`, `whole_sha256=90f998dff32ff548fcf155301f942f78009a6832483ddb3de9207be6c752de1e`, `interface_sha256=b077289afefd2696448b3217df31da05be3f37a746431183656ae4f68094ca7f`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 84:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 85:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/posterize:posterize`
- Source: `sources/filter/posterize/posterize.glsl` (2630 raw bytes, sha256 `460910a8d1103eca5cc0b4df82f39fd91fbc447b9a815250ae7d34dfab8ee5b2`; 2471 normalized bytes, sha256 `4781d189690f57de2b57aebaaa946eba004b1c57272f32a18d1f0ce06ce44393`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('tileOffset', 'fullResolution', 'inputTex', 'levels', 'gamma', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 9 globals; Functions: 7 (`clamp_01, linear_to_srgb_component, linear_to_srgb_rgb, main, pow_vec3, srgb_to_linear_component, srgb_to_linear_rgb`)
- `local_type_names`: `['vec2', 'vec2', 'vec4', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'vec3', 'vec3', 'vec3', 'vec3', 'vec3', 'vec3']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=7bdcf13444da35b93bcae7c4758f92d46c26f0316f1ec4308bd1bc6e1c93e977`, `whole_sha256=74adeb96fe8c6d4a916b0b54b29ce0f9ca2dbce7f7609f3582dcf51d82f4b6e8`, `interface_sha256=e53cc14ee2e987c2682722edd2870f0b617f1c28cae66e56e47aebe82548b81d`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `fwidth` | `vec3` | `main` | 80:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** OTHER BLOCKER: `filter/posterize:posterize:60:34: unsupported builtin round`

---

### `filter/spiral:spiral`
- Source: `sources/filter/spiral/spiral.glsl` (2869 raw bytes, sha256 `3d609c5028c859d82c060af21b0675dd0dd0ec6f720dbc9e3b3b21a65893ef4a`; 2107 normalized bytes, sha256 `6e516a2d27e14fbbe0c6c1b200625efbdad09283e5ee09cc8d69e5c372b3ca34`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'time', 'strength', 'speed', 'aspectLens', 'wrap', 'rotation', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 12 globals; Functions: 2 (`main, rotate2D`)
- `local_type_names`: `['float', 'float', 'vec2', 'vec2', 'float', 'float', 'float', 'vec2', 'vec2', 'vec2', 'vec4']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=96d3129f74aa9f70b713b8b66d99219c4ea9c5359bac7512e007c683b5d30516`, `whole_sha256=694cd7517a81e3aebe8b24a18e529f06fd5b534c541f1475e34f97c6a561874d`, `interface_sha256=076dcb4d51978fa60df5a9186a5a7447df28a3078e1157eafe9e64912d2d97b8`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 85:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 86:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/stamp:stThreshold`
- Source: `sources/filter/stamp/stThreshold.glsl` (3467 raw bytes, sha256 `d93168982b13907e32e1264c021c39f9d434ae122efd7d11898733293ee5da94`; 1565 normalized bytes, sha256 `f6593ec857c845845201652026bd375e8860d4e107e7528a82e4519c9b085bbe`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'blurTex', 'resolution', 'tileOffset', 'balance', 'roughness', 'inkColor', 'paperColor'),
   ('inputTex', 'blurTex'),
   ('fragColor',),
   True, True)
  ```
- Declarations: 9 globals; Functions: 6 (`fbm, hash12, lum, main, tonemap2, vnoise`)
- `local_type_names`: `['vec3', 'vec2', 'vec2', 'vec2', 'float', 'float', 'int', 'vec2', 'vec4', 'vec4', 'vec2', 'float', 'float', 'float', 'float', 'float', 'float', 'vec3']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=1, unproved_loop_count=0, max_effective_depth=1, max_lexical_product=5, entrypoint_charge=5, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=fccb3a9d9cf9b02f1f30087c58827ce3f5de4c659168c843cc283748edbcc9d1`, `whole_sha256=7a5f47aeda690b1bc649e54662dd2b47aed69f68bded0a5fc1e658bd448c456d`, `interface_sha256=ef70990afd3060826ca720c7419901188c453957b62df786272a3f41244905cd`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `fwidth` | `float` | `main` | 60:20-29 | 0 | unconditional |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/step:step`
- Source: `sources/filter/step/step.glsl` (709 raw bytes, sha256 `4f5680a9b25a2c12cecdcef3cc1ba106c2ee7a8390790544a3425890153cb7bf`; 592 normalized bytes, sha256 `d77e236beca61d709a7b0e5320aa76b3a1e068ee0014bd3e41c31bd3fd4b0f6f`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('tileOffset', 'fullResolution', 'inputTex', 'threshold', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 6 globals; Functions: 1 (`main`)
- `local_type_names`: `['vec2', 'ivec2', 'vec2', 'vec4', 'vec3']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=52e93d37d80c993d92ee8910fa4c6804fcd5ebe3933e722c0c385ec70ba3ace8`, `whole_sha256=0aa2574412206287d46dddc3504e9909788870874a2514202270c39b0415bef2`, `interface_sha256=405fbda2028d8696ca0b0e620efeebded0037a5bbd6705b3f59aef6f84b1e08f`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `fwidth` | `vec3` | `main` | 19:19-36 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/stipple:stipple`
- Source: `sources/filter/stipple/stipple.glsl` (8490 raw bytes, sha256 `69d75b6fab4281fe0a0997eaf6b7b81e5ab30f0da5dfec9255c9dbb6e914c609`; 2598 normalized bytes, sha256 `5bf1e7ef4187d31b9b6d7836537eb7a9ba3df04eaf782629a899a47ca6ccc64f`)
- Authorized define map (`_defaults`): `{"MODE": 0}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'cellSize', 'grainSize', 'density', 'paperColor', 'seed'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 9 globals; Functions: 9 (`fbm, hash12, hash22, lum, main, rotate2D, tonemap2, vnoise, voronoiCell`)
- `local_type_names`: `['vec3', 'vec3', 'vec2', 'vec2', 'vec2', 'float', 'float', 'int', 'vec2', 'vec2', 'float', 'vec4', 'int', 'int', 'vec2', 'vec2', 'float', 'float', 'float', 'float', 'vec2', 'vec2', 'float', 'vec3', 'vec2', 'vec4', 'vec2', 'vec2', 'vec3', 'float', 'float', 'float', 'float']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=3, unproved_loop_count=0, max_effective_depth=2, max_lexical_product=9, entrypoint_charge=12, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=7b5f228b32b8a64996ceaa6a54629ea640816469dffb6cc9a3268c954c9c6162`, `whole_sha256=ccb94ec0b07abeea1f047aafe38627c4309f84f80a623c302a5ed4b4f1e7a37b`, `interface_sha256=5a609da7b87f4e672c3bc02c80393f216b9efc7ba03781a927b67a1221e8c89d`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `fwidth` | `float` | `main` | 112:20-29 | 0 | unconditional |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/tunnel:tunnel`
- Source: `sources/filter/tunnel/tunnel.glsl` (3062 raw bytes, sha256 `c0ebe43eead7a1c040dd4a37162d634fe4b1a93ea0b8704bac502fbc5a978193`; 2637 normalized bytes, sha256 `38d97378dc7d3b0e558f08717a40a03d0369ff9776260e42cbed3e7f5ec7033c`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'tileOffset', 'fullResolution', 'time', 'shape', 'speed', 'rotation', 'scale', 'center', 'aspectLens', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 14 globals; Functions: 3 (`main, polygonShape, smod`)
- `local_type_names`: `['float', 'float', 'ivec2', 'vec2', 'vec2', 'vec2', 'vec2', 'float', 'float', 'float', 'vec2', 'vec2', 'vec4', 'vec2', 'vec2', 'float', 'float']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=14de75890dea3ba98f0df57ecadb98a6f06bf4b3d64a6706d1c4138e110bcb5a`, `whole_sha256=a6b7ecb1d5ab1c08a5a476e58f0b34102ff7a7a4566dabc9dd28b8c2c9d5d18a`, `interface_sha256=d8540a43bc855db657b2f93b6910a463eadf77ba85e7cd6c5fb6cd165188baca`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 80:19-37 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 81:19-37 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/warp:warp`
- Source: `sources/filter/warp/warp.glsl` (3095 raw bytes, sha256 `f3034ac02a2926b819ff874d2d1d0d3dacebf2b7a409c983237d6a71865942ee`; 2840 normalized bytes, sha256 `f3b4c97572bf2868710033cb82244c52233434df8c91ebde50d181983ab89e60`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'time', 'strength', 'scale', 'seed', 'speed', 'wrap', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 12 globals; Functions: 7 (`grid, main, pcg, perlinNoise, prng, smootherstep, smoothlerp`)
- `local_type_names`: `['float', 'vec2', 'vec2', 'vec2', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'vec2', 'float', 'vec2', 'vec2', 'vec2', 'float', 'float', 'vec2', 'vec2', 'vec4']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=85a83512222d058b07514fbb35aeaa78d6762434fc945bd3c9bff8e152df08bf`, `whole_sha256=6e2aa3c9af8aadcc4de8bbae83259be59902873db002ed39aca31d54750e3a9b`, `interface_sha256=55bc224d9217f43f4fff711cb897cd48fe5cff0e446305ada90b61d42a35d611`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 94:19-27 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 95:19-27 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** CLEAN -- no other blocker

---

### `filter/waves:waves`
- Source: `sources/filter/waves/waves.glsl` (2622 raw bytes, sha256 `f4cddf1b3a6c9c68aa677b6743af313e1cdb2bf0a857ce9a1c13edc80f54e3aa`; 2167 normalized bytes, sha256 `f823bcdbac0ff15096e92fcded5c07611077fb7eece203d48f9f08256e968621`)
- Authorized define map (`_defaults`): `{}`
- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, uses_texture, uses_derivatives):
  ```python
  (('inputTex', 'resolution', 'tileOffset', 'fullResolution', 'time', 'strength', 'scale', 'speed', 'wrap', 'rotation', 'antialias'),
   ('inputTex',),
   ('fragColor',),
   True, True)
  ```
- Declarations: 12 globals; Functions: 2 (`main, rotate2D`)
- `local_type_names`: `['float', 'float', 'vec2', 'vec2', 'float', 'float', 'vec2', 'vec2', 'vec2', 'vec2', 'vec4']`
- `structs`: `[]` / `uniform_blocks`: `[]` (both empty for all 17)
- `counted_loop_proof`: loop_count=0, unproved_loop_count=0, max_effective_depth=0, max_lexical_product=0, entrypoint_charge=0, call_graph_acyclic=True
- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): all `None` -- {'fixed_affine_centers13_proof': False, 'fixed_array_in_parameter_proof': False, 'fixed_grid_counter_store_proof': False, 'fixed_nine_table_proof': False}
- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable across the future vocabulary-admission fix, see note below): `functions_sha256=0c9efa54e5863e2022d6e4bc8832bfc3f5a9e11c2ffa3114c623a7faf23ec15f`, `whole_sha256=5e6ed7428f47fdc2037d08c76d7b32a24009a76ce9644bc9386922bd9ab5279e`, `interface_sha256=7e683c0e5c6ae52a90cd2481a28f96e2a163a315bc58bba7b3b7ae564605e753`

**Derivative call sites:**

| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |
|---|---------|----------|---------------|----------------------|------------|-------|
| 0 | `dFdx` | `vec2` | `main` | 70:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |
| 1 | `dFdy` | `vec2` | `main` | 71:19-33 | 0 | then-branch of `if` on [antialias(uniform)] -> frame-constant |

**validate_capabilities() beyond derivatives:** OTHER BLOCKER: `filter/waves:waves:41:9: unsupported builtin any`

---



---

## 6. Extraction script

The exact script used to produce every fact above (`extract_facts.py`,
alongside this document):

```python
#!/usr/bin/env python3
"""Read-only fact extraction for the 17 derivative-blocked programs.

Imports the real, unmodified glslcpp frontend from
. (never writes into that repo) and
runs parse_program + analyze_program against each of the 17 programs at their
authorized (_defaults) preprocessor define map. Extracts:

  - corpus manifest entry (source path, sizes, hashes)
  - authorized define map
  - success/failure of parse+analyze (this IS the "would it land" check)
  - the exact resources tuple the gate must assert
  - declarations tuple (gate shape, matching validate_current_vocabulary_degauss)
  - function profile tuple (id, name, body-stmt-count, sha256(repr(function)))
  - every dFdx/dFdy/fwidth call site: builtin, arg type, enclosing function,
    span (typed.source-relative, i.e. TypedExpression.span, NOT raw corpus
    line numbers), and full stack of enclosing if-guards with each guard's
    referenced-identifier storages (to classify frame-constant vs
    per-pixel-varying)
  - any other diagnostic distinguishing "blocked solely by derivatives" from
    "blocked by X as well"

Output: derivative-program-facts.json (machine-readable) written into this
same directory. This script performs no writes into noisemaker-for-cpp and
runs no git command anywhere.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import traceback

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp import check_corpus  # noqa: E402
from tools.glslcpp.frontend import FrontendError, parse_program  # noqa: E402
from tools.glslcpp.frontend.diagnostics import SemanticError  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp import generate_typed_slice as gts  # noqa: E402
from tools.glslcpp.generate_typed_slice import GeneratorError, _defaults  # noqa: E402

CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS_ROOT = REPO / "tools/glslcpp/corpus" / CORPUS_REVISION

# The 17, in the order given in the task brief.
PROGRAM_KEYS = [
    "filter/bulge:bulge",
    "filter/celShading:celShadingColor",
    "filter/halftone:halftone",
    "filter/lens:lens",
    "filter/lensWarp:lensWarp",
    "filter/octaveWarp:octaveWarp",
    "filter/pinch:pinch",
    "filter/polar:polar",
    "filter/pondRipples:pondRipples",
    "filter/posterize:posterize",
    "filter/spiral:spiral",
    "filter/stamp:stThreshold",
    "filter/step:step",
    "filter/stipple:stipple",
    "filter/tunnel:tunnel",
    "filter/warp:warp",
    "filter/waves:waves",
]

DERIVATIVE_BUILTINS = {"dFdx", "dFdy", "fwidth"}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _span_dict(span) -> dict:
    return {
        "start": span.start, "end": span.end,
        "start_line": span.start_line, "start_column": span.start_column,
        "end_line": span.end_line, "end_column": span.end_column,
    }


def _type_display(t) -> str:
    return t.display()


def _declarations_tuple(typed):
    return tuple(
        (declaration.symbol.id, declaration.symbol.name,
         declaration.type.display(), declaration.symbol.storage,
         declaration.symbol.writable, declaration.symbol.direction,
         None if declaration.initializer is None else (
             declaration.initializer.kind, declaration.initializer.literal))
        for declaration in typed.declarations)


def _function_profiles(typed):
    return tuple(
        (function.signature.id, function.signature.name, len(function.body),
         _sha256(repr(function).encode("utf-8")))
        for function in typed.functions)


def _resources_tuple(typed):
    r = typed.resources
    return (r.uniforms, r.samplers, r.outputs, r.uses_texture, r.uses_derivatives)


def _identifier_storages(expr) -> list[tuple[str, str]]:
    """All (name, storage) pairs for every identifier reachable in expr."""
    out: list[tuple[str, str]] = []

    def walk(e):
        if e.kind == "id" and e.symbol is not None:
            out.append((e.symbol.name, e.symbol.storage))
        if e.kind == "swizzle" and e.children and e.children[0].kind == "id" and e.children[0].symbol is not None:
            pass  # already captured via recursion below
        for c in e.children:
            walk(c)
    walk(expr)
    return out


def _condition_summary(expr) -> dict:
    storages = _identifier_storages(expr)
    kinds = {storage for _, storage in storages}
    frame_constant = kinds <= {"uniform", "const"}
    return {
        "text_kind": expr.kind,
        "identifiers": sorted(set(storages)),
        "storage_kinds": sorted(kinds),
        "frame_constant": frame_constant,
    }


def _find_derivative_sites(typed):
    """Walk every function body; report each dFdx/dFdy/fwidth call site with
    its enclosing function, arg type, span, and the stack of enclosing if
    guards (condition expr storage-classified for frame-constant safety)."""
    sites = []

    for function in typed.functions:
        fn_name = function.signature.name

        def walk_stmt(stmt, guard_stack, loop_depth):
            if stmt.kind == "if":
                condition = stmt.expressions[0]
                children = stmt.children
                walk_stmt(children[0], guard_stack + [{"branch": "then", "condition": condition}], loop_depth)
                if len(children) > 1:
                    walk_stmt(children[1], guard_stack + [{"branch": "else", "condition": condition}], loop_depth)
                return
            if stmt.kind in {"for", "while", "dowhile"}:
                for expr in stmt.expressions:
                    walk_expr(expr, guard_stack, loop_depth)
                for child in stmt.children:
                    walk_stmt(child, guard_stack, loop_depth + 1)
                return
            for expr in stmt.expressions:
                walk_expr(expr, guard_stack, loop_depth)
            for child in stmt.children:
                walk_stmt(child, guard_stack, loop_depth)

        def walk_expr(expr, guard_stack, loop_depth):
            if expr.kind == "builtin" and expr.callee in DERIVATIVE_BUILTINS:
                arg = expr.children[0] if expr.children else None
                sites.append({
                    "builtin": expr.callee,
                    "enclosing_function": fn_name,
                    "arg_type": arg.type.display() if arg is not None else None,
                    "return_type": expr.type.display(),
                    "span": _span_dict(expr.span),
                    "guard_stack": [
                        {"branch": g["branch"], **_condition_summary(g["condition"]),
                         "condition_span": _span_dict(g["condition"].span)}
                        for g in guard_stack
                    ],
                    "unconditional": len(guard_stack) == 0,
                    "enclosing_loop_depth": loop_depth,
                })
            for child in expr.children:
                walk_expr(child, guard_stack, loop_depth)

        for stmt in function.body:
            walk_stmt(stmt, [], 0)

    return sites


def run_validator_beyond_derivatives(typed, raw_source: str) -> dict:
    """Call the real validate_capabilities() (the generator's full-vocabulary
    proof), in-memory-patched to ALSO admit dFdx/dFdy/fwidth by name (a
    test-only bypass of the frozen-44 rule, never written to any file), so we
    can see whether GeneratorError still fires for an UNRELATED reason once
    derivatives are out of the way. This is read-only: it mutates the already
    -imported module's globals for the duration of one call in this process
    only; nothing is written to disk and no other process is affected.

    Returns {"clean": True} if validate_capabilities raises nothing once
    derivatives are admitted (i.e. the program is blocked SOLELY by
    derivatives), or {"clean": False, "error": "..."} with the exact
    GeneratorError text if something else also blocks it.
    """
    original_builtins = gts._BUILTINS
    original_capabilities = gts.APPROVED_CAPABILITIES
    patched_builtins = frozenset(original_builtins | {"dFdx", "dFdy", "fwidth"})
    patched_capabilities = tuple(original_capabilities) + ("dFdx", "dFdy", "fwidth")
    source_hash = _sha256(raw_source.encode("utf-8"))
    try:
        gts._BUILTINS = patched_builtins
        gts.APPROVED_CAPABILITIES = patched_capabilities
        try:
            gts.validate_capabilities(
                typed, patched_capabilities,
                source_hash=source_hash,
                compatibility_transform=None,
                custom_comparer_profile=None,
                numeric_literal_contract="glsl-f32",
                source_global_literal_int_profile=None,
                gather_sorted_round_profile=None,
                literal_vec3_lane_index_profile=None,
                smooth_edge_luma_weights_profile=None,
                perlin_scalar_uint_xor_profile=None,
                rotate_mat2_return_profile=None,
                focus_blur_borrowed_sampler_profile=None,
                extrude_bvec2_relational_reduction_profile=None,
                caustic_word_hash_profile=None,
                curl_vector_math_profile=None,
            )
            return {"clean": True, "error": None}
        except GeneratorError as error:
            return {"clean": False, "error": str(error)}
        except Exception as error:  # noqa: BLE001
            return {"clean": False, "error": f"UNEXPECTED {type(error).__name__}: {error}",
                    "traceback": traceback.format_exc()}
    finally:
        gts._BUILTINS = original_builtins
        gts.APPROVED_CAPABILITIES = original_capabilities


def _main_call_sites(typed) -> list[dict]:
    """Every user-function call expression reachable in main()'s own body
    (not transitively into helpers), with guard/loop context -- used to prove
    call-graph reachability and invocation multiplicity for any derivative
    site that lives inside a helper function rather than main() itself
    (only filter/halftone:halftone has this shape among the 17)."""
    main_fn = next((f for f in typed.functions if f.signature.name == "main"), None)
    if main_fn is None:
        return []
    sites: list[dict] = []

    def walk_stmt(stmt, guard_stack, loop_depth):
        if stmt.kind == "if":
            condition = stmt.expressions[0]
            children = stmt.children
            walk_stmt(children[0], guard_stack + [{"branch": "then", "condition": condition}], loop_depth)
            if len(children) > 1:
                walk_stmt(children[1], guard_stack + [{"branch": "else", "condition": condition}], loop_depth)
            return
        if stmt.kind in {"for", "while", "dowhile"}:
            for expr in stmt.expressions:
                walk_expr(expr, guard_stack, loop_depth)
            for child in stmt.children:
                walk_stmt(child, guard_stack, loop_depth + 1)
            return
        for expr in stmt.expressions:
            walk_expr(expr, guard_stack, loop_depth)
        for child in stmt.children:
            walk_stmt(child, guard_stack, loop_depth)

    def walk_expr(expr, guard_stack, loop_depth):
        if expr.kind == "call" and expr.callee:
            sites.append({
                "callee": expr.callee,
                "span": _span_dict(expr.span),
                "loop_depth": loop_depth,
                "guard_stack": [
                    {"branch": g["branch"], **_condition_summary(g["condition"])}
                    for g in guard_stack
                ],
                "unconditional": len(guard_stack) == 0,
            })
        for child in expr.children:
            walk_expr(child, guard_stack, loop_depth)

    for stmt in main_fn.body:
        walk_stmt(stmt, [], 0)
    return sites


def _manifest_entry(key: str) -> dict:
    manifest = check_corpus._load_json(CORPUS_ROOT / "manifest.json", "manifest")
    entries = {item["program_key"]: item for item in check_corpus._validate_manifest(manifest)}
    return entries[key]


def _metadata(repository: pathlib.Path) -> dict:
    root = check_corpus._corpus_root(repository)
    return check_corpus._load_json(root / "metadata.json", "metadata")


def process(key: str) -> dict:
    result: dict = {"program_key": key}
    try:
        entry = _manifest_entry(key)
    except Exception as error:  # noqa: BLE001
        result["manifest_error"] = repr(error)
        return result
    result["manifest_entry"] = {
        k: v for k, v in entry.items()
    }
    source_path = CORPUS_ROOT / entry["source"]
    raw_source = source_path.read_text(encoding="utf-8")
    result["raw_bytes_actual"] = len(raw_source.encode("utf-8"))
    result["raw_sha256_actual"] = _sha256(raw_source.encode("utf-8"))

    defines = _defaults(REPO, key)
    result["authorized_defines"] = defines
    metadata = _metadata(REPO)
    effect_id = key.split(":", 1)[0]
    result["metadata_effect"] = metadata.get("effects", {}).get(effect_id)

    try:
        parsed = parse_program(raw_source, key, defines)
    except FrontendError as error:
        result["stage"] = "parse"
        result["success"] = False
        result["error"] = str(error)
        return result
    except Exception as error:  # noqa: BLE001
        result["stage"] = "parse"
        result["success"] = False
        result["error"] = f"UNEXPECTED {type(error).__name__}: {error}"
        result["traceback"] = traceback.format_exc()
        return result

    result["normalized_bytes_actual"] = len(parsed["source"].encode("utf-8"))
    result["normalized_sha256_actual"] = _sha256(parsed["source"].encode("utf-8"))

    try:
        typed = analyze_program(parsed, key)
    except SemanticError as error:
        result["stage"] = "analyze"
        result["success"] = False
        result["error"] = str(error)
        result["diagnostics"] = [
            {"code": d.code, "message": d.message, "span": _span_dict(d.span)}
            for d in error.diagnostics
        ]
        return result
    except Exception as error:  # noqa: BLE001
        result["stage"] = "analyze"
        result["success"] = False
        result["error"] = f"UNEXPECTED {type(error).__name__}: {error}"
        result["traceback"] = traceback.format_exc()
        return result

    result["stage"] = "complete"
    result["success"] = True
    result["body_status"] = typed.body_status
    result["resources"] = {
        "uniforms": list(typed.resources.uniforms),
        "samplers": list(typed.resources.samplers),
        "outputs": list(typed.resources.outputs),
        "uses_texture": typed.resources.uses_texture,
        "uses_derivatives": typed.resources.uses_derivatives,
    }
    result["resources_tuple_gate_order"] = [
        list(typed.resources.uniforms), list(typed.resources.samplers),
        list(typed.resources.outputs), typed.resources.uses_texture,
        typed.resources.uses_derivatives,
    ]
    result["declarations"] = [
        {
            "id": d[0], "name": d[1], "type": d[2], "storage": d[3],
            "writable": d[4], "direction": d[5], "initializer": d[6],
        }
        for d in _declarations_tuple(typed)
    ]
    result["function_profiles"] = [
        {"id": f[0], "name": f[1], "body_stmt_count": f[2], "sha256": f[3]}
        for f in _function_profiles(typed)
    ]
    result["local_type_names"] = list(typed.local_type_names)
    result["structs"] = [s.name for s in typed.structs]
    result["uniform_blocks"] = [u.block_name for u in typed.uniform_blocks]
    result["interface_symbols"] = [
        {"name": s.name, "type": s.type.display(), "storage": s.storage}
        for s in typed.interface_symbols
    ]
    result["builtin_symbols"] = [
        {"name": s.name, "type": s.type.display(), "storage": s.storage}
        for s in typed.builtin_symbols
    ]
    proof = typed.counted_loop_proof
    result["counted_loop_proof"] = None if proof is None else {
        "loop_count": proof.loop_count,
        "unproved_loop_count": proof.unproved_loop_count,
        "max_effective_depth": proof.max_effective_depth,
        "max_lexical_product": proof.max_lexical_product,
        "entrypoint_charge": proof.entrypoint_charge,
        "call_graph_acyclic": proof.call_graph_acyclic,
    }
    result["preprocessor_defines"] = [
        {"name": p.name, "kind": p.kind, "canonical_value": p.canonical_value}
        for p in typed.preprocessor_defines
    ]
    result["foreign_proofs_present"] = {
        "fixed_nine_table_proof": typed.fixed_nine_table_proof is not None,
        "fixed_grid_counter_store_proof": typed.fixed_grid_counter_store_proof is not None,
        "fixed_array_in_parameter_proof": typed.fixed_array_in_parameter_proof is not None,
        "fixed_affine_centers13_proof": typed.fixed_affine_centers13_proof is not None,
    }
    result["derivative_call_sites"] = _find_derivative_sites(typed)
    result["derivative_call_count"] = len(result["derivative_call_sites"])
    result["main_call_sites"] = _main_call_sites(typed)
    result["validator_beyond_derivatives"] = run_validator_beyond_derivatives(typed, raw_source)

    # Exact whole-program / interface / functions-tuple hashes, computed the
    # same way validate_current_vocabulary_degauss/_crt do (see
    # generate_typed_slice.py:400-421). These are stable NOW: the frontend
    # (parse_program/analyze_program) needs no change to admit these 17 (see
    # body_semantic.py's existing "derivative" builtin family) -- only the
    # generator's frozen-vocabulary walk (validate_capabilities) needs the
    # node-identity admission described in the architecture doc. So these
    # hashes are exactly what a future validate_current_vocabulary_<name>
    # gate would assert.
    functions_sha256 = _sha256(repr(typed.functions).encode("utf-8"))
    whole = (
        typed.key, typed.source, typed.raw_source, typed.declarations,
        typed.functions, typed.resources, typed.body_status,
        typed.local_type_names, typed.structs, typed.uniform_blocks,
        typed.interface_symbols, typed.builtin_symbols,
        typed.counted_loop_proof, typed.preprocessor_defines,
    )
    whole_sha256 = _sha256(repr(whole).encode("utf-8"))
    interface = (
        typed.declarations, typed.resources, typed.local_type_names,
        typed.structs, typed.uniform_blocks, typed.interface_symbols,
        typed.builtin_symbols, typed.preprocessor_defines,
    )
    interface_sha256 = _sha256(repr(interface).encode("utf-8"))
    result["gate_hashes"] = {
        "functions_sha256": functions_sha256,
        "whole_sha256": whole_sha256,
        "interface_sha256": interface_sha256,
    }
    return result


def main() -> int:
    facts = {"corpus_revision": CORPUS_REVISION, "programs": {}}
    for key in PROGRAM_KEYS:
        facts["programs"][key] = process(key)
    out_path = pathlib.Path(__file__).resolve().parent / "derivative-program-facts.json"
    out_path.write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    success = sum(1 for v in facts["programs"].values() if v.get("success"))
    print(f"success: {success}/{len(PROGRAM_KEYS)}")
    for key, v in facts["programs"].items():
        if not v.get("success"):
            print(f"  FAIL {key}: stage={v.get('stage')} error={v.get('error')}")
    clean = sum(1 for v in facts["programs"].values()
                if v.get("success") and v.get("validator_beyond_derivatives", {}).get("clean"))
    print(f"validator-clean-beyond-derivatives: {clean}/{len(PROGRAM_KEYS)}")
    for key, v in facts["programs"].items():
        vbd = v.get("validator_beyond_derivatives")
        if v.get("success") and vbd and not vbd.get("clean"):
            print(f"  OTHER BLOCKER {key}: {vbd.get('error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

The section-generator (`gen_sections.py`, also alongside this document):

```python
#!/usr/bin/env python3
"""Generate the per-program markdown sections from derivative-program-facts.json.
Read-only; writes only into this characterization/ directory."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
facts = json.loads((HERE / "derivative-program-facts.json").read_text())


def fmt_span(s):
    if s["start_line"] == s["end_line"]:
        return f"{s['start_line']}:{s['start_column']}-{s['end_column']}"
    return f"{s['start_line']}:{s['start_column']}-{s['end_line']}:{s['end_column']}"


def guard_text(site):
    if site["unconditional"]:
        return "unconditional"
    parts = []
    for g in site["guard_stack"]:
        ids = ", ".join(f"{n}({s})" for n, s in g["identifiers"])
        safety = "frame-constant" if g["frame_constant"] else "**PER-PIXEL-VARYING (unsafe)**"
        parts.append(f"{g['branch']}-branch of `if` on [{ids}] -> {safety}")
    return "; ".join(parts)


out = []
for key in facts["programs"]:
    v = facts["programs"][key]
    entry = v["manifest_entry"]
    out.append(f"### `{key}`\n")
    out.append(f"- Source: `{entry['source']}` ({entry['raw_bytes']} raw bytes, "
                f"sha256 `{entry['raw_sha256']}`; {entry['normalized_bytes']} normalized bytes, "
                f"sha256 `{entry['normalized_sha256']}`)\n")
    out.append(f"- Authorized define map (`_defaults`): `{json.dumps(v['authorized_defines'])}`\n")
    r = v["resources"]
    out.append("- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, "
                "uses_texture, uses_derivatives):\n")
    out.append("  ```python\n"
                f"  ({tuple(r['uniforms'])!r},\n"
                f"   {tuple(r['samplers'])!r},\n"
                f"   {tuple(r['outputs'])!r},\n"
                f"   {r['uses_texture']!r}, {r['uses_derivatives']!r})\n"
                "  ```\n")
    out.append(f"- Declarations: {len(v['declarations'])} globals; Functions: {len(v['function_profiles'])} "
                f"(`{', '.join(f['name'] for f in v['function_profiles'])}`)\n")
    out.append(f"- `local_type_names`: `{v['local_type_names']}`\n")
    out.append(f"- `structs`: `{v['structs']}` / `uniform_blocks`: `{v['uniform_blocks']}` "
                f"(both empty for all 17)\n")
    proof = v["counted_loop_proof"]
    out.append(f"- `counted_loop_proof`: loop_count={proof['loop_count']}, "
                f"unproved_loop_count={proof['unproved_loop_count']}, "
                f"max_effective_depth={proof['max_effective_depth']}, "
                f"max_lexical_product={proof['max_lexical_product']}, "
                f"entrypoint_charge={proof['entrypoint_charge']}, "
                f"call_graph_acyclic={proof['call_graph_acyclic']}\n")
    out.append(f"- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): "
                f"all `None` -- {v['foreign_proofs_present']}\n")
    gh = v["gate_hashes"]
    out.append(f"- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable "
                f"across the future vocabulary-admission fix, see note below): "
                f"`functions_sha256={gh['functions_sha256']}`, "
                f"`whole_sha256={gh['whole_sha256']}`, `interface_sha256={gh['interface_sha256']}`\n")
    out.append("\n**Derivative call sites:**\n\n")
    out.append("| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |\n")
    out.append("|---|---------|----------|---------------|----------------------|------------|-------|\n")
    for i, s in enumerate(v["derivative_call_sites"]):
        out.append(f"| {i} | `{s['builtin']}` | `{s['arg_type']}` | `{s['enclosing_function']}` | "
                    f"{fmt_span(s['span'])} | {s['enclosing_loop_depth']} | {guard_text(s)} |\n")
    vbd = v["validator_beyond_derivatives"]
    verdict = "CLEAN -- no other blocker" if vbd["clean"] else f"OTHER BLOCKER: `{vbd['error']}`"
    out.append(f"\n**validate_capabilities() beyond derivatives:** {verdict}\n\n")
    out.append("---\n\n")

(HERE / "_sections.md").write_text("".join(out), encoding="utf-8")
print("wrote _sections.md")

```
