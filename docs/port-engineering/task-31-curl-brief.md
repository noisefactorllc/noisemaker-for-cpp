# Task 31 (Curl) frozen design brief: exact tanh/mod scalar-overload closure

Date: 2026-08-12
Author: design agent (this session)
Status: **DESIGN ONLY. No git action authorized. No file under
`noisemaker-for-cpp` was modified to produce this brief.**

Target: `synth/curl:curl`, defines `{"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES":
True}` (source revision `a024dc3a960cc44af454abc7aebce50456c194e6`, unchanged
from the accepted Task 30 baseline). Starting state, independently
reproduced from the live tree (not copied from any prior doc):
**130 typed / 132 public / 80 unported / 212 corpus**, typed-list SHA-256
`d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904`, public-list
SHA-256 `4fe573b21a782a784b7fcacacaa276a03a395a1b8c92e83149971b8a19831056`.

All numbers, hashes, spans, and gate-chain results below were computed by
scripts in this same directory (`task31curl_probe_identity.py`,
`task31curl_probe_closure.py`, `task31curl_probe_gatechain.py`,
`task31curl_probe_gatechain2.py`), run fresh against the live
`noisemaker-for-cpp` tree, read-only, and cross-checked a second way wherever
noted. Nothing here is copied from `task-31-target-reselection.md` /
`task-31-blockers.md` without independent reproduction; those documents are
cited only for the narrative they contain that this brief does not redo (the
Caustic postmortem).

---

## 0. Executive answers to the four flagged constraints

These four points were each missed by a previous brief on this or a
neighbouring task and cost real time. They are answered first, definitively,
with evidence, before the rest of the brief.

### (a) Capability vocabulary and overload-scoping — the central finding

**`tanh` needs the skip pattern; `mod`'s overload widening is NOT a vocabulary
change but IS a leak risk that must be identity-scoped, not tuple-widened.**

- `tanh` is absent from the 44-entry vocabulary (`typed_slice.json`
  `"capabilities"`, `generate_typed_slice.APPROVED_CAPABILITIES`) and from
  both `generate_typed_slice._BUILTINS` and `emit_typed_cpp._BUILTIN_NAMES`
  (confirmed by direct membership test, not grep alone). It follows the
  existing `round`/`floatBitsToUint`/`all`/`lessThanEqual` precedent exactly:
  an identity-scoped `elif value.callee == "tanh":` branch in both authorities
  that checks node identity against the one authorized Curl `tanh` node, and
  `"tanh"` added to the `used.add()` exclusion set
  (`{"round","all","lessThanEqual","floatBitsToUint","tanh"}`) so the
  vocabulary count stays at 44. `tanh` must **never** be added to `_BUILTINS`
  or `_BUILTIN_NAMES` as a bare name — doing so would admit `tanh` for *any*
  future program's *any* overload without review.

- `mod` is **already** in the 44-entry vocabulary and already passes the
  name-membership gate for every program (it is one of the most common
  builtins in the corpus). So on the vocabulary-*count* question the answer
  is unambiguous: **no growth, 44 stays 44, regardless of how the overload
  widening is implemented.**

  But there is a second, independent gate, and this is the part a naive
  brief gets wrong. Both `generate_typed_slice.py` (~line 2029) and
  `emit_typed_cpp.py` (~line 1330) carry the **identical inline literal**:

  ```python
  if value.callee == "mod":
      argument_types = tuple(child.type.display() for child in value.children)
      if argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2")}:
          raise GeneratorError(f"{location(value)}: unsupported builtin mod overload")
  ```

  This check is **not identity-scoped** — it is a blanket type-signature
  gate applied to every `mod` call in every program, with no per-node
  narrowing. If the tuple is naively widened to add `("vec3","float")` and
  `("vec4","float")`, that widening applies to **every program in the
  corpus, typed today or ported in the future** — not just Curl. No
  currently-typed program is affected today (if one called `mod(vec3,
  float)` it would already be failing, and the tree is green), so this is
  not an immediate regression. But it is a structural leak: any future
  program with a `mod(vec3,float)`/`mod(vec4,float)` call would sail through
  this gate without its own review, capability, or profile — exactly the
  class of unreviewed widening the whole profile system exists to prevent.

  **Required fix, precise and non-leaking:** add an identity-scoped
  carve-out *inside* the existing check, keyed on object identity against
  the profile's three authorized mod nodes, mirroring the `all`/
  `lessThanEqual` pattern:

  ```python
  if value.callee == "mod":
      argument_types = tuple(child.type.display() for child in value.children)
      if (argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2")}
              and not any(value is item for item in authorized_curl_mod_nodes)):
          raise GeneratorError(f"{location(value)}: unsupported builtin mod overload")
  ```

  Do the identical edit in `emit_typed_cpp.py`. This keeps the shared tuple
  untouched (so every other program's rejection behavior is unchanged) and
  admits exactly Curl's three authenticated `mod` nodes by identity — not by
  type shape. This is the definitive, evidence-backed resolution of
  constraint (a): the vocabulary does not grow; the overload gate must be
  identity-scoped, not widened.

### (b) Reachability — reproduced independently, matches the reselection doc exactly

Built the real call graph from `program.functions`' `call` nodes'
`signature_id` (not name-matching — verified `signature_id` correctly
resolves `permute`'s two overloads, e.g. all three nested calls inside
`simplex3D` resolve to function id 20, the `vec4` overload, never id 19).
Reachable set from `main` (id 18): `{16 curlNoise3D, 17 fbmSimplex3D, 18
main, 20 permute(vec4), 21 simplex3D, 22 taylorInvSqrt}`. Unreachable:
`{19 permute(vec3)}`.

| Closure site | Owning function | Span | Reachable |
|---|---|---|---|
| `tanh(vec3) -> vec3` | `main` (id 18) | 196:12-196:34 | **yes** |
| `mod(vec4, float) -> vec4` | `permute` (id 20) | 35:12-35:47 | **yes** |
| `mod(vec3, float) -> vec3` | `simplex3D` (id 21) | 65:9-65:22 | **yes** |
| `mod(vec3, float) -> vec3` | `permute` (id 19) | 32:12-32:47 | **no** |

Matches the reselection doc's table exactly (spans differ only by including
end-column, which the doc omitted). **The implementation report for Task 31
must state plainly that the fourth site (`permute(vec3)`'s `mod`) is
validated structurally — parsed, type-checked, authenticated, emitted, and
compiled — but is dead code at the authorized define map, and no rendering
evidence can or does discriminate its correctness.** Unlike Caustic, this
does not disqualify Curl: three of the four sites remain live and
reachable, so full-surface pixel parity is a meaningful gate for the
capability as a whole, with this one caveat stated honestly rather than
glossed over.

### (c) Coarse hash gate absorbs mutation tests — required countermeasure

`ExtrudeBvec2RelationalReductionProof`'s authenticator rejects on ANY tree
edit at the coarse level (`_whole`/`_interface`/`_FUNCTIONS_SHA256` mismatch)
before node-level logic ever runs — Task 30's rereview proved 46 of 47
"single-axis" mutations never reached the profile's real logic. Curl's
profile has the same shape (whole-program SHA-256, interface SHA-256,
functions-tuple SHA-256, all computed below) and will have the identical
failure mode unless guarded against explicitly.

**Required test, modeled exactly on
`test_task30_node_level_closure_logic_rejects_past_the_coarse_hash_gate`:**
a test that uses `mock.patch.multiple` to re-freeze `_WHOLE_SHA256`,
`_INTERFACE_SHA256`, and `_FUNCTIONS_SHA256` (the Curl profile's equivalents)
to match each mutated tree's actual coarse hashes, auto-restored, so that
each single-axis mutation is forced past the coarse gate and must be
rejected by a **specific node-level message** (e.g. "closure site
cardinality mismatch", "closure node identity mismatch", "tanh argument type
mismatch", "mod overload argument mismatch"), with an explicit assertion
that the **coarse message did not fire**. Candidate mutations to drive
through this harness (each single-axis, each must assert its own structural
precondition before checking rejection):

- `tanh` callee renamed to a different unary builtin (e.g. `sin`) at the one
  authorized site — expect a specific node-identity/callee mismatch, not the
  coarse hash message.
- one of the three `mod` nodes' argument-type tuple perturbed (e.g. the
  `vec3` argument retyped to `vec2` in the frozen node record) — expect a
  specific type mismatch, not the coarse message.
- the `tanh` node's single child swapped for an unrelated node of the same
  type — expect a node-identity mismatch.
- one `mod` node's owning-function id perturbed (e.g. claim the
  `simplex3D` mod site actually belongs to `permute`) — expect an
  ownership/ancestry mismatch.
- the reachability classification for the fourth (dead) site flipped in the
  frozen record — expect the authenticator to still authenticate all four
  sites uniformly (reachability is a *reporting* fact for the parity
  section, not a structural admission gate — the emitter must lower the
  unreachable site exactly like the other three, since it is still present
  in the compiled binary).

The test must, like Task 30's, prove itself non-vacuous by sabotaging the
node-identity check and confirming specific subtests then fail, and must
restore the real profile module state at the end so later tests do not
inherit a mis-frozen module.

### (d) Native mutation modes must be pairwise structurally distinct

Curl's native closure is smaller than Extrude's (4 authenticated call sites
across 4 functions, vs. Extrude's 4 nodes in one function), so there is less
surface for accidental mode-sharing, but the requirement is unconditional
regardless of surface size: **every named native mutation mode's payload
must derive only from observed runtime behavior (e.g., reduced/produced
values, per-lane results, call counters) — excluding mode id, mode name, and
any one-hot dispatch array — and pairwise semantic-signature uniqueness
must be asserted across all named modes, proving N distinct code paths, not
N labels sharing fewer paths.** An unhandled enum value must fail closed
(`default` throws), never silently falls through to baseline. This directly
targets the Task 26 defect class (3 of 11 modes silently sharing the
baseline path, 24 of 88 result rows meaningless) and its explicit repair
protocol in Task 30's addendum.

---

## 1. Projection: post-Curl counts, ordinal, hashes, and ordinal blast radius

### 1.1 Projected counts and hashes

Computed by inserting `synth/curl:curl` into the live, alphabetically-sorted
`typed_slice.json` "programs" key list (confirmed the live list is already
alphabetically ordered — `keys == sorted(keys)` is `True` today) and
recomputing exactly as `test_task29_schema_counts_hashes_and_real_task28_reconstruction_isolation`
does (`typed = tuple(program_key for programs)`, `public = sorted(typed +
("filter/invert:inv", "synth/solid:solid"))`, `unported = sorted(corpus_keys
- public)`):

| Quantity | Before | After |
|---|---:|---:|
| Typed programs | 130 | **131** |
| Public programs | 132 | **133** |
| Publicly unported | 80 | **79** |
| Corpus programs | 212 | 212 |

- new typed-list SHA-256: `ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2`
- new public-list SHA-256: `29da87160abcee096a3c5f1c27e1b39381664ad3a7b71342c62a4b2c5e434f8c`
- Curl zero-based typed ordinal **120**, neighbours `synth/cell:cell`
  (ordinal 119, unchanged) and `synth/gradient:gradient` (ordinal 120→121).

### 1.2 Ordinal blast radius — smaller than the mechanical-site class suggests, but a different class dominates

**Class 1 — live hardcoded ordinal/namespace assertions (the class the prior
Caustic-era `task-31-ordinal-blast-radius.md` catalogued): ZERO sites need
updating for Curl.** Verified by re-deriving all nine `"namespace typed_NN
{"` string assertions, the one embedded `make_shared<typed_53::State>`
binder string, and the three explicit `typed.index(KEY)` assertions
(`SMOOTH_EDGE_KEY`→77, `FOCUS_BLUR_KEY`→111, `EXTRUDE_KEY`→25) in the live
`tests/test_typed_generator.py`. Every live-tree numeric value in that class
is < 120 (Curl's insertion ordinal), so none shift. (One of the nine,
`typed_123` for Perlin at line 12255, additionally turned out to be a
**historical reconstruction snapshot** — frozen at the moment Perlin was
added when the tree had 127 total programs — and is immune to *any* future
insertion regardless of ordinal, confirmed by reading its enclosing test:
it explicitly excludes `{"filter/rotate:rot", "mixer/focusBlur:focusBlur",
"filter/extrude:extrude"}` from a freshly-loaded `spec` before reconstructing,
which is exactly Class 2 below.) This differs materially from Caustic,
whose ordinal-0 insertion would have shifted all thirteen of these sites;
Curl sorts alphabetically very late (`synth/curl`), which happens to protect
this whole class.

**Class 2 — historical-reconstruction chronological-boundary exclusion sets
(NOT catalogued by the prior ordinal-blast-radius doc; this is the actual
dominant risk for Curl, and for any future addition regardless of its
ordinal).** Many tests in `tests/test_typed_generator.py` reconstruct an
*earlier* historical state by loading the **live** `spec =
generate_typed_slice.load_slice(REPOSITORY)` and then filtering out a
hardcoded set of "everything added after task N" program keys, e.g.:

```python
spec["programs"] = [item for item in spec["programs"]
                     if item["program_key"] not in {
                         "filter/rotate:rot", "mixer/focusBlur:focusBlur",
                         "filter/extrude:extrude"}]
```

Because these exclusion sets are hardcoded lists (not "everything after
timestamp T" computed dynamically), and because `filter/extrude:extrude` is
today's most-recently-landed program, **every one of these sets currently
ends at Extrude and will silently admit `synth/curl:curl` into the
reconstructed "historical" spec once Curl lands**, corrupting each test's
hardcoded program count and SHA-256 (and, for the one true historical-hash
comparison at line ~12213, the frozen Task 26 artifact hashes it checks
against `prior_with_header`). This is independent of Curl's ordinal — it
would apply to *any* newly landed program, because the risk is chronological
membership in these lists, not alphabetical position.

Grep recipe to reproduce the current inventory (line numbers **will move**
by the time of implementation — re-run this exact command, do not trust the
numbers below without re-deriving):

```text
grep -n '"filter/extrude:extrude"' tests/test_typed_generator.py
```

As of this brief (live tree, `test_typed_generator.py` current revision),
16 occurrences, falling into three edit shapes:

1. **Chronological-boundary exclusion sets requiring `"synth/curl:curl"`
   appended** (14 of the 16): lines 577, 1454, 2308, 7323, 7537, 8602, 8724,
   8960, 9159, 11145, 11255, 12116, 12171, 12199, 13204 (some line numbers
   are the closing `}]`/`})` of a multi-line set; the set itself starts a
   few lines above — re-read each in context). Each of these must gain
   `"synth/curl:curl"` in its literal exclusion set/frozenset, or the
   reconstruction becomes a 1-too-many count.
2. **An authorized-defines completeness table requiring a NEW row, not an
   exclusion edit** (line ~6538, inside
   `test_committed_manifest_has_one_hundred_twenty_nine_typed_outputs_without_absolute_paths`):
   this test reads the **committed** `typed_manifest.json` directly (no
   exclusion filtering) and asserts a hardcoded dict of every program with
   non-empty defines. Once Curl is generated, this dict comprehension will
   include it automatically, and the expected literal must gain:
   `"synth/curl:curl": ("default-only", {"OCTAVES": 1, "OUTPUT_MODE": 3,
   "RIDGES": True})` (confirmed the JSON define_contract vocabulary is
   `"default-only"` for every other single-define-map program in that same
   table; `numeric_literal_contracts` in `typed_slice.json` today is exactly
   `{"filter/scatter:scatterJitter": "source-double"}`, confirming Curl uses
   the ordinary default `"glsl-f32"` contract and needs no entry there).
3. **A full chronological ordered-list membership assertion** (line ~4938-4944):
   `self.assertEqual(sorted([*existing, *task15, ..., "filter/extrude:extrude"]),
   [entry["program_key"] for entry in slice_spec["programs"]])`, where
   `slice_spec = generate_typed_slice.load_slice(REPOSITORY)` (confirmed at
   line 4809 — the live, **unfiltered** spec, not a historical
   reconstruction). This compares the sorted union of every named historical
   batch against the live ordered key list directly, so it will break the
   instant `synth/curl:curl` appears in the live spec unless
   `"synth/curl:curl"` is added to the `sorted([...])` argument list.
   **Confirmed needed, not inconclusive.**

**This class-2 finding is a correction to, and extension of, the
methodology used by the Caustic-era `task-31-ordinal-blast-radius.md`.**
That doc's "13 mechanical sites" enumeration is a real and useful pattern
for Class 1, but it is not a complete blast-radius inventory for any target,
including the one it was written for. The actual safety net for Class 2 is
unavoidably running the full Python test discovery (already mandatory per
the standing protocol) and treating every failure as a real signal — the
grep inventory above exists to make the *first* implementation pass
efficient, not to substitute for that run.

**Native tests:** re-verified `rg -c 'typed_[0-9]+' tests/test_generated_kernels.cpp
tests/test_typed_slice.cpp` finds no hardcoded `typed_NN` occurrences in
either file (native tests bind by public key and factory name), so the
native suite needs no ordinal work — consistent with the prior finding for
Caustic.

---

## 2. Frozen target identity

| Field | Frozen value |
|---|---|
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` (unchanged) |
| Source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/curl/curl.glsl` |
| Raw bytes / SHA-256 | 7,290 / `33d1f2bd0215d6439b51a0aa8d50b5c3637abc0b5cade8f3e451b8d258d0afce` |
| Normalized bytes / SHA-256 | 4,673 / `405774c12a29bff814b92ffbe2cc5f3b267367aa40832befc59b509573be91e9` |
| Exact defines | `{"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}` → canonical `(("OCTAVES","int","1"), ("OUTPUT_MODE","int","3"), ("RIDGES","bool","true"))` |
| Numeric contract | `glsl-f32` (default; `typed_slice.json` `numeric_literal_contracts` today lists only `filter/scatter:scatterJitter`, confirming no exception is needed for Curl) |
| Function count / tuple SHA-256 | 7 / `06632686b2a2a1938389722409a109a71b6fb66fb2e1afd9b459e4fedb8b16fe` |
| Whole-program SHA-256 | `a7c44947e08fdf478857d1f9c400cd5072df99a14ae4d63aebcbd6d1fc1d9374` |
| Interface SHA-256 | `0ff5180a4e2bbbf81e9a2705e99a155d9e9c378fbcbe5729eaa43a941c0227ae` |
| Loop proof tuple | `(1, 0, 1, 1, 12, True)` — matches the reselection doc; not loop-nested with any closure node (the one counted loop is `fbmSimplex3D`'s `for`, unrelated to any of the four authenticated sites) |
| Canonical/public factory | `canonicalFactory248`, no adapter — confirmed two independent ways: (1) `grep '"synth/curl:curl"'` across all of `noisemaker-for-cpu/src/effects/generated/*.js` finds exactly one hit, in `canonical-kernels.js`, no separate public/adapter registry entry; (2) `future-precompute/public-identities.json`'s row for `synth/curl:curl` independently states `adapter_factory_name: null`, `public_is_exact_canonical_object: true` |
| Factory text SHA-256 | `a5faaca15e28732b3ca3f802c03dc1f906a90134d9ac855eba6bcc4f85596349` (10,993 bytes) — reproduced by directly `require()`-ing `canonical-kernels.js` in Node and hashing `canonicalKernelFactories["synth/curl:curl"].toString()`; matches `future-precompute/public-identities.json`'s independently-recorded value exactly |

`_whole`/`_interface` helper definitions (copied verbatim from
`extrude_bvec2_relational_reduction_profile.py`, unmodified, for the future
Curl profile module to reuse):

```python
def _whole(program):
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))

def _interface(program):
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))
```

### 2.1 Function identities (all 7; the profile must authenticate the 4 whose
bodies carry an authenticated node, and must still verify total function
cardinality = 7)

| id | name | return | params | body stmts | span | owns a closure node |
|---:|---|---|---:|---:|---|---|
| 16 | `curlNoise3D` | vec3 | 1 | 25 | 137:1-181:2 | no |
| 17 | `fbmSimplex3D` | float | 1 | 6 | 114:1-130:2 | no |
| **18** | `main` | void | 0 | 11 | 183:1-208:2 | **yes — 1 tanh** |
| **19** | `permute` (vec3 overload) | vec3 | 1 | 1 | 31:1-33:2 | **yes — 1 mod, UNREACHABLE** |
| **20** | `permute` (vec4 overload) | vec4 | 1 | 1 | 34:1-36:2 | **yes — 1 mod** |
| **21** | `simplex3D` | float | 1 | 41 | 43:1-110:2 | **yes — 1 mod** |
| 22 | `taylorInvSqrt` | vec4 | 1 | 1 | 38:1-40:2 | no |

### 2.2 Resources tuple

```text
uniforms: ('resolution', 'tileOffset', 'fullResolution', 'time', 'scale', 'seed', 'speed', 'intensity')
samplers: ()
outputs: ('fragColor',)
uses_texture: False
uses_derivatives: False
structs: ()
uniform_blocks: ()
body_status: 'analyzed'
```

---

## 3. Frozen closure: exactly 4 nodes must be newly authenticated

Every `tanh` call and every `mod` call in the whole program was enumerated
(walking every function's body, not just the reachable subset — an
unauthorized fifth site anywhere else in the program must be a hard
failure, per the Extrude precedent). Total `tanh`+`mod` sites in the whole
program: **4**. All 4 require new authentication — **zero** are covered by
the existing admitted `mod` overload set (`("float","float")`,
`("vec2","float")`, `("vec2","vec2")` — none of Curl's three `mod` calls
match any of these, since all three are vec3-or-vec4-by-scalar).

| # | Callee | Owning fn (id) | Reachable | Span | Result | Parent kind | Child types | Node SHA-256 |
|---|---|---|---|---|---|---|---|---|
| 1 | `tanh` | `main` (18) | yes | 196:12-196:34 | vec3 | `binary` (196:12-196:40) | (`vec3`,) | `bc83ca6fd3369ed6ac8321eb38db83a78569233a404563f491eb95736c27c09a` |
| 2 | `mod` | `permute` (19) | **no** | 32:12-32:47 | vec3 | none (is the `return` expression) | (`vec3`,`float`) | `9e296505e841a30c1211828e3bc255acf00250f53572c992fc948c4a953eb208` |
| 3 | `mod` | `permute` (20) | yes | 35:12-35:47 | vec4 | none (is the `return` expression) | (`vec4`,`float`) | `e0063fe65cbef6674dbb68fe752ddb24dfa7f419c15816227d24d24c8b3de39d` |
| 4 | `mod` | `simplex3D` (21) | yes | 65:9-65:22 | vec3 | `assign` (65:5-65:22) | (`vec3`,`float`) | `5e8842bf171ffb0d63398609deaad1e1c6171bafed84b10e83f5967b337bc466` |

Ancestor statement chains (single-element in every case — none of the four
sites is nested inside the one counted loop, unlike Extrude's two sites
both nested inside the same `for`):

| # | Ancestor kinds | Ancestor spans |
|---|---|---|
| 1 | (`expr`,) | (`196:5-196:47`,) |
| 2 | (`return`,) | (`32:5-32:48`,) |
| 3 | (`return`,) | (`35:5-35:48`,) |
| 4 | (`expr`,) | (`65:5-65:23`,) |

Child node SHA-256 values (for a future profile's node-identity check,
mirroring `_NODES` in the Extrude profile):

- site 1 (`tanh`) child: `f4e778bb127f3924bc93fd0b7beea12879fbf17dfb3fb557d25bc097f848c7be`
- site 2 (`mod` vec3 unreachable) children: `0e3bf42a81dd8ac63534ced244edbc02e3910e8a8f34c70530951adbf61e0b5c`, `428f06112f27901a71a78a75eea7ce4163e0bb3d60bf377232af739c2b084fe3`
- site 3 (`mod` vec4) children: `1754c609d6ec486f066d9cc518c08ce3e870ed7bd4a38ce67285b51a2f52b75c`, `a37a9afeb11211283c1314b5d163604986bf55f197f0dba043f40f7a201d73bb`
- site 4 (`mod` vec3 reachable) children: `c2725ce361f7540980fe47e0e05f5703bb2353263f26e478a6a9ba1c6380730a`, `45961f58255d5a42e2f1264ee759fc43cd4ee3fa4241262452e8f96c16dccd2f`

**Exactly 4 nodes must be authenticated by the profile.** Unlike Extrude
(one owning function, two paired reduction/relational trees, a "no escape"
proof needed because the intermediate `bvec2` type could otherwise leak),
Curl's closure spans **four different owning functions** and has **no
shared intermediate type to police** — `tanh`'s argument/result and `mod`'s
arguments/results are all already-approved types (`vec3`, `vec4`, `float`).
The profile is structurally simpler on that axis, but must still verify:
function cardinality = 7; each of the 4 owning functions' identity (name,
return type, param count, body length, span, from §2.1); the whole-program
and interface hashes; the exact 4-node closure by span+type+SHA+parent-kind
+child-types+child-SHA, with the total `tanh`+`mod` census over the *whole*
program (not just the reachable subgraph) equal to exactly 4, so a fifth
site introduced anywhere is a hard failure.

---

## 4. Gate chain — confirmed live, walked in full, with monkeypatch/restore proof

All four probes below were run against the live `noisemaker-for-cpp` tree,
read-only; the last two explicitly snapshot and restore the patched module
globals and assert equality after restoration.

**Stage 0 — baseline, no widening at all.**

- `generate_typed_slice.validate_capabilities(curl_program, ...)` →
  `REJECT: synth/curl:curl:196:12: unsupported builtin tanh`
- `emit_typed_cpp.render_typed_cpp(curl_program, ...)` (called directly,
  bypassing the validator entirely) → `REJECT: synth/curl:curl:32:12:
  unsupported builtin mod overload`

The two authorities reject at **different** nodes at baseline. This is not
an inconsistency — it reflects that the validator walks `program.functions`
in its stored tuple order (`main` at index 2, before `permute` at indices
3-4), while the emitter's rendering evidently visits `permute` before
`main` (consistent with call-dependency-ordered emission rather than
declaration-tuple order). Each authority independently fails closed at its
own first unsupported construct without needing to agree on traversal
order with the other — itself a form of gate independence evidence.

**Stage 1 — widen only the validator's `_BUILTINS` (add `"tanh"` by bare
name; this is a probe technique, not the recommended implementation shape —
see §0(a), tanh must NOT actually be added to this table).**

- validator → `REJECT: synth/curl:curl:32:12: unsupported builtin mod
  overload` (moved past `tanh`, now blocked by the mod-overload gate — a
  **different, independent** gate).
- `gen._BUILTINS` confirmed restored to byte-identical original after the
  `try/finally`.

**Stage 2 — validator left unmodified; emitter called directly again.**

- emitter → `REJECT: synth/curl:curl:32:12: unsupported builtin mod
  overload` (unchanged from Stage 0 — confirms the emitter's rejection does
  not depend on the validator ever having run, i.e. no shared mutable state
  between the two authorities).

**Stage 3 (second script) — widen `tanh` admission by bare name in BOTH the
validator's `_BUILTINS` and the emitter's `_BUILTIN_NAMES` simultaneously
(again, a probe technique only).**

- validator → `REJECT: synth/curl:curl:32:12: unsupported builtin mod
  overload`
- emitter → `REJECT: synth/curl:curl:32:12: unsupported builtin mod
  overload`
- Both authorities now converge on the **same** remaining rejection. This
  proves there is **no third hidden gate** for the `tanh` half of this
  closure: once its name is admitted, both authorities' only remaining
  objection is the `mod`-overload gate.
- Full restoration confirmed by value-equality snapshot of both
  `gen._BUILTINS` and `emit_mod._BUILTIN_NAMES` before/after (dict object
  identity intentionally differs — the probe replaces the dict rather than
  mutating in place — but content equality holds exactly).

**Why the chain cannot be walked all the way to a full render by
monkeypatching alone:** the `mod`-overload check is an inline literal tuple
inside a function body in both files, not a module-level table — it cannot
be widened by patching a global. This is itself a load-bearing finding for
the brief (see §0(a)): reaching a full render requires an actual,
identity-scoped source edit, not a widen-a-global probe. That edit is
scoped to implementation, not this design brief.

**Full ordered gate list for this closure, as confirmed:**

1. Validator: builtin-name membership (`value.callee not in _BUILTINS`) —
   blocks `tanh` today; must gain an identity-scoped `tanh` branch (never a
   bare `_BUILTINS` addition).
2. Validator: `mod`-overload argument-shape literal — blocks all 3 `mod`
   sites today; must gain an identity-scoped carve-out (never a widened
   literal tuple).
3. Emitter: same two gates, independently coded, independently must be
   fixed the same way for its own authority.
4. No further gate exists beyond these two per authority, for this specific
   closure (proven by Stage 3: once gate 1 (tanh) is cleared in both
   authorities, only gate 2 (mod) remains in both, and nothing else surfaces).

It renders in full **only once both authorities' two gates are each given
their identity-scoped carve-out** — not demonstrated by this read-only
brief (would require an actual source edit), and explicitly left as the
implementation's job.

---

## 5. C++ lowering — what exists, what's missing, verified against the whole include tree

Searched the **entire** `include/` tree case-insensitively for `tanh` (not
just `glsl_types.hpp`/`glsl_runtime.hpp`), per the explicit warning from the
Caustic postmortem (`float_bits_to_uint` was missed because only two files
were checked for a camelCase spelling, and it existed under a snake_case
name in a third file). Result: **`tanh` does not exist anywhere in
`include/`, `src/`, or `tests/`, under any spelling** (`grep -rli tanh`
across all three trees returns nothing).

`mod` exists in `include/noisemaker/glsl_runtime.hpp` but **only at
`N == 2`** (all four overload shapes — `Vec,Vec`; `Vec,double`;
`FloatExpr,Vec`; `FloatExpr,double`; plus two explicitly `= delete`d
ambiguous shapes — are gated `requires(N == 2)`). A scalar `glsl::mod(double,
double)` also exists and is width-independent (used inside every vector
overload via `detail::map_float`/`map_float2`); it needs no change.

### 5.1 Exactly which C++ overloads Curl's 4 nodes actually invoke

All float-vector `+`/`-`/`*`/`/` in this codebase are **lazy**: `Vec<N,float>
op Vec<N,float>` (and vec-op-scalar) always yields `FloatExpr<N>`, never an
eager `Vec<N,float>` (`NOISEMAKER_GLSL_FLOAT_BINARY` macro,
`glsl_types.hpp:165-178`); a concrete `Vec<N,float>` only exists again once
explicitly materialized (a declaration/assignment target, or a function
whose result is eagerly computed like `floor`/`abs`/etc via
`detail::map_float`). Tracing each of the 4 sites through this rule:

- **site 1, `tanh(curl * intensity)`**: `curl` is a concrete `Vec3` local
  (`vec3 curl = curlNoise3D(p);`); `curl * intensity` (scalar `double`)
  yields `FloatExpr<3>`. **Needs `tanh(const FloatExpr<3>&)`.**
- **site 2, `permute(vec3)`'s `mod(((x*34.0)+10.0)*x, 289.0)`** (dead code,
  must still compile): `x` is the concrete `Vec3` parameter; the whole
  numerator is a chain of lazy ops, ending in `FloatExpr<3>`. **Needs
  `mod(const FloatExpr<3>&, double)`.**
- **site 3, `permute(vec4)`'s same expression shape at `Vec4`**: identical
  reasoning. **Needs `mod(const FloatExpr<4>&, double)`.**
- **site 4, `simplex3D`'s `i = mod(i, 289.0)`**: `i` was declared as
  `vec3 i = floor(v + dot(v, C.yyy));` — `floor`'s vector overload returns
  an *eager* `Vec<3,float>` (via `detail::map_float`, not the lazy binary
  macro), so `i` is a concrete `Vec3` lvalue at the point of the `mod` call.
  **Needs `mod(const Vec<3,float>&, double)`** (note: `FloatExpr<N>`'s
  converting constructor from `Vec<N,float>` is non-`explicit`, so this call
  would also silently compile against a `FloatExpr<3>`-only overload via
  implicit conversion — but the brief requires providing the concrete-`Vec`
  overload explicitly, mirroring the existing `N==2` quartet's symmetry
  rather than relying on an implicit-conversion loophole).

So exactly two mod overload *shapes* are needed, at two widths each:
`mod(FloatExpr<N>, double)` for `N ∈ {3,4}`, and `mod(Vec<N,float>, double)`
for `N == 3` only (nothing calls the `Vec<4,float>,double` shape). The
brief recommends adding both `N==3` and `N==4` for `Vec<N,float>,double` too
for API symmetry with the `FloatExpr` sibling and because it costs nothing
extra and is no wider a leak than the FloatExpr form — implementer's call,
not load-bearing.

**Critically: `mod(Vec<N,float>, Vec<N,float>)` and `mod(FloatExpr<N>,
Vec<N,float>)` (the two-vector forms) must remain `requires(N == 2)`
unchanged.** Curl's closure never calls two-vector `mod` at width 3 or 4;
widening those forms too would be exactly the kind of unauthenticated,
untested generalization Task 30's boundary section explicitly bans for its
own capability, and the same principle applies here.

### 5.2 Required additions, by file

**`include/noisemaker/glsl_runtime.hpp`** (near the existing `mod`
overloads at lines 66-71, and near `sin`/`cos`/etc. at lines 39-61):

```cpp
[[nodiscard]] inline float tanh(double value) { return noisemaker::f32(std::tanh(value)); }

// Deliberately constrained to N == 3. Only the exact vec3 site authenticated
// by <curl-profile-name> is authorized to lower to these; wider use is a
// compile error, mirroring the lessThanEqual/all precedent in glsl_types.hpp.
template <std::size_t N> requires(N == 3)
[[nodiscard]] inline Vec<N,float> tanh(const Vec<N,float>& value) {
  return detail::map_float(value, [](double lane) { return glsl::tanh(lane); });
}
template <std::size_t N> requires(N == 3)
[[nodiscard]] inline Vec<N,float> tanh(const FloatExpr<N>& value) {
  return glsl::tanh(Vec<N,float>(value));
}
```

Widen the existing `mod(Vec<N,float>,double)` and `mod(FloatExpr<N>,double)`
overloads' constraint from `requires(N == 2)` to `requires(N == 2 || N == 3
|| N == 4)` (these two specific overload shapes only — leave
`mod(Vec,Vec)`, `mod(FloatExpr,Vec)`, and the two `=delete`d shapes at
`requires(N == 2)` unchanged):

```cpp
template <std::size_t N> requires(N == 2 || N == 3 || N == 4)
[[nodiscard]] inline Vec<N,float> mod(const Vec<N,float>& a,double b) { return detail::map_float(a,[b](double x){return glsl::mod(x,b);}); }
...
template <std::size_t N> requires(N == 2 || N == 3 || N == 4)
[[nodiscard]] inline Vec<N,float> mod(const FloatExpr<N>& a,double b) { return mod(Vec<N,float>(a),b); }
```

`std::tanh` is available via the existing `<cmath>` include at the top of
`glsl_runtime.hpp`; no new include needed.

No changes needed to `glsl_types.hpp` (that file holds `Vec`/`FloatExpr`/
`Mat`/`BVec` core machinery and the Extrude-specific `lessThanEqual`/`all`;
Curl's additions belong alongside `sin`/`cos`/`mod` in `glsl_runtime.hpp` by
existing precedent, not `glsl_types.hpp`).

### 5.3 Emitter identity-scoped emission (no `_TYPES` change needed)

Unlike Extrude's `bvec2`, `tanh`/`mod`'s arguments and results are all
already-approved type spellings (`vec3`, `vec4`, `float` → `glsl::Vec3`,
`glsl::Vec4`, `double`), so **`emit._TYPES` needs no new entry.** Only the
two identity-scoped builtin-emission branches (mirroring the `all`/
`lessThanEqual` block at `emit_typed_cpp.py:1364-1381`) are needed, emitting
`glsl::tanh(...)` and `glsl::mod(...)` directly rather than going through
`_BUILTIN_NAMES` lookup for the identity-scoped nodes.

---

## 6. Capability boundary

**Admitted — exactly these four authenticated AST nodes, nothing else:**
- the `tanh(vec3) -> vec3` node at `196:12-196:34` in `main`;
- the `mod(vec3, float) -> vec3` node at `32:12-32:47` in `permute` (vec3
  overload, unreachable, structurally authenticated only);
- the `mod(vec4, float) -> vec4` node at `35:12-35:47` in `permute` (vec4
  overload);
- the `mod(vec3, float) -> vec3` node at `65:9-65:22` in `simplex3D`.

**Explicitly BANNED — must be structurally impossible, not just untested:**
- `tanh` admitted by bare name in `_BUILTINS`/`_BUILTIN_NAMES` for any other
  program or site (must stay identity-scoped forever, like `round`/
  `floatBitsToUint`/`all`/`lessThanEqual`);
- `mod`'s overload-shape check widened as a bare tuple/set change rather
  than an identity-scoped carve-out (§0(a) — this is the single most
  important boundary in this brief);
- `tanh`/`mod` at any width other than the exact ones authenticated (`tanh`
  at `N != 3`; `mod(Vec/FloatExpr, double)` at `N` outside `{2,3,4}`;
  `mod(Vec,Vec)`/`mod(FloatExpr,Vec)` widened past `N == 2` at all);
- any other unadmitted builtin reachable from Curl's authorized define map
  (the corpus census in §3 already proves no fifth `tanh`/`mod` site exists
  in the whole program; the validator's "unsupported builtin" fallback
  continues to reject everything else unconditionally);
- treating the unreachable `permute(vec3)` mod site as anything other than
  "authenticated, compiled, never validated by rendering" in any report
  language (§0(b)).

---

## 7. Test plan

### Python (structural / mutation / history)

Follow the `Task30ExtrudeBvec2RelationalReductionTests`-style class shape:

- authenticate the exact frozen 4-node closure from raw source; prove
  `authenticate_...`/`apply_...` returns/accepts an independently
  reconstructed distinct-object tree (via the `dataclasses.replace`
  recursive-rebuild pattern already used at
  `tests/test_typed_generator.py:14330-14346`), sharing no object identity
  with the original's proof;
- the coarse-hash-gate countermeasure from §0(c), non-negotiable given the
  Task 30 rereview's finding;
- exhaustive single-axis structural mutation rejection at all three
  authorities (profile, validator, emitter) for each of the 4 sites — callee
  rename, argument arity change, argument type change, owning-function
  reassignment, span/parent tampering — each asserting its own structural
  precondition before checking rejection (Task 26 post-mortem: candidates
  must be genuinely single-axis and correctly named, not compound or
  mislabeled);
- validator/emitter independence, proven behaviorally (forged-proof
  rejection, emitter called directly bypassing the validator, as in §4);
- identity-scoping proven behaviorally, not by static list inspection: a
  foreign program (any other corpus key) with a structurally similar
  `tanh`/`mod(vecN,float)` call (if the census turns any up — re-run the
  whole-corpus census, not just Curl, before implementation) must be
  rejected at both authorities;
- coexistence matrix: fresh `APPROVED_CAPABILITIES`/`APPROVED_TYPES` tuple
  check with every prior task's profile imported simultaneously
  (`generate_typed_slice.py:634`-area pattern);
- byte-for-byte reconstruction test: "removing only Curl regenerates the
  accepted Task 30 (130-typed) outputs byte-for-byte" — same pattern
  already used for every prior task transition, and the concrete mechanism
  by which the frozen historical hashes stay safe despite Curl's insertion
  (ordinal 120, not ordinal 0, so — unlike the abandoned Caustic ordinal-0
  plan — removing Curl alone reproduces today's 130-program tree without
  any ordinal renumbering of the other 129 at all, since Curl sits after
  all of them that matter to any currently-frozen historical snapshot);
- **the Class-2 exclusion-set updates from §1.2 are a hard prerequisite for
  a green Python suite**, not optional cleanup — every listed test will
  fail with a corrupted count/hash otherwise. Treat the full-suite run as
  the authoritative check that none were missed.

### Native (fixture / parity)

- Execute the oracle's eligible direct rows (once the concurrently-built
  oracle at `future-precompute/task31-curl/` lands — this brief does not
  read or depend on its current draft state) with explicit F32/RGBA8
  hashes; reject an invalid/unhandled mode fail-closed.
- Full pixel/parity gates per the standing pattern: Debug/Release
  warnings-as-errors + CTest, ASan/UBSan (with the known
  `detect_leaks`-unsupported-on-this-platform retry procedure already
  documented for prior tasks), all Task15-30 oracles, independent
  implementation review with zero Critical/Important.
- `static_assert`-based compile-time proof that `tanh<2>`/`tanh<4>` and
  `mod<5>` (or any width outside `{2,3,4}`) are hard errors — keep the width
  dependent via file-scope template variables, per Task 30's own recorded
  gotcha (a `requires`-expression evaluated directly in a non-template
  context is non-dependent and gets diagnosed eagerly by Clang rather than
  substitution-failing as intended).
- Candidate discriminating mutations for the native fixture (semantically
  grounded, **divergence rates not measured in this design pass — mark
  INCONCLUSIVE until run against a real oracle**):
  - `tanh → identity` (no saturation) at the one authorized site — GLSL
    `tanh` saturates to `[-1,1]`; the surrounding expression
    `tanh(curl*intensity)*0.5+0.5` maps that to `[0,1]`, so removing the
    saturation should diverge whenever `|curl*intensity|` exceeds
    roughly 1 in any lane, which is plausible given the source's own
    comment ("tanh saturates gracefully, intensity controls curve") but
    **not independently confirmed by rendering** in this pass.
  - `mod → fmod` (C semantics: sign follows the dividend) vs GLSL `mod`
    semantics (`x - y*floor(x/y)`, always non-negative for positive `y`) at
    each of the 3 authorized sites — a legitimate, semantically-motivated
    single-axis swap in the same spirit as Extrude's `all → any`, expected
    to diverge whenever the dividend goes negative, which happens routinely
    given `permute`'s domain includes negative lattice coordinates — again
    **not independently measured here.**
  - Both candidate families must be checked against the real oracle once
    built, and only mutations with genuine, non-zero, non-trivial
    divergence counts should ship as the native test's discriminating rows
    (per the Task 30 anti-vacuity standard in §0(d)).

---

## 8. Oracle requirements

- **Eligibility rule (Task 30's lesson, restated precisely for Curl):** the
  oracle may carry multiple define-map cases, but only the case(s) whose
  define map equals exactly `{"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES":
  true}` are eligible for native binding/parity comparison. Any other
  `OCTAVES`/`OUTPUT_MODE`/`RIDGES` combination renders a structurally
  different program (different loop-unroll count, different output-mode
  branch, different ridge post-process) and must be marked ineligible for
  native binding — public-source sensitivity evidence only, exactly as
  Extrude's non-default `EXTRUDE_TYPE`/`DEPTH_SOURCE` cases were excluded.
- **What mutations must discriminate:** per §7, both the `tanh`-saturation
  removal and the `mod`→`fmod` semantic swap are candidate discriminators;
  the oracle should carry enough distinct input coordinates/seeds/uniform
  values that at least one authorized site's mutation produces a
  measurable, non-trivial divergence — including specifically exercising
  negative-argument inputs to `permute`, since GLSL `mod` vs C `fmod`
  diverge only when the dividend's sign differs from the divisor's.
- **Direct rows:** given three of the four closure sites are reachable, a
  full-surface pixel-parity row (matching Extrude's precedent of
  whole-surface F32 SHA-256 comparison against the frozen JS reference) is
  the primary evidence; additionally, at least one direct closure-probe row
  isolating each of `tanh` and `mod`'s exact argument/return shapes (mirror
  Extrude's `direct_relational_cases` pattern) would let the C++ runtime's
  new functions be verified independent of the full render, and is
  recommended but not verified as already present in the concurrently-built
  oracle (not inspected in this pass, per the isolation instruction).
- **The unreachable site (`permute(vec3)`'s mod) cannot be given a
  rendering-based direct row that means anything** — any oracle row
  targeting it would necessarily call the dead function directly via some
  test-only hook, which is a legitimate thing to do for a compile/type
  proof but must not be reported as parity evidence for the accepted
  program's rendered behavior (§0(b)).

---

## Summary of hard numbers for quick reference

- Projected: **131 typed / 133 public / 79 unported / 212 corpus**
- Typed-list SHA-256: `ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2`
- Public-list SHA-256: `29da87160abcee096a3c5f1c27e1b39381664ad3a7b71342c62a4b2c5e434f8c`
- Curl ordinal: **120** (neighbours `synth/cell:cell` / `synth/gradient:gradient`)
- Ordinal blast radius Class 1 (live hardcoded ordinal/namespace sites): **0**
- Ordinal blast radius Class 2 (chronological-boundary exclusion sets needing
  `"synth/curl:curl"` added): **~15-16 sites**, grep recipe above, re-derive
  fresh before editing
- Vocabulary growth needed: **0** (44 stays 44)
- `mod` overload widening: **must be identity-scoped**, not a tuple/set
  widen — leak risk otherwise
- `tanh`: absent from vocabulary everywhere; needs the skip pattern, never a
  bare `_BUILTINS`/`_BUILTIN_NAMES` addition
- Closure size: **4 nodes** (1 `tanh`, 3 `mod`), spanning **4 owning
  functions**, **3 of 4 reachable** from `main`
- Gate chain: 2 independent gate-families per authority (builtin-name,
  mod-overload-shape); confirmed no third hidden gate for this closure
- C++ runtime: `tanh` absent everywhere in `include/`; `mod` exists only at
  `N==2`; additions scoped to `glsl_runtime.hpp`, `N∈{3,4}` for the two
  scalar-mod overload shapes actually used, `N==3` only for `tanh`

## Files produced by this brief (read-only against `noisemaker-for-cpp`)

- `docs/port-engineering/task-31-curl-brief.md` (this file)
- `docs/port-engineering/task-31-curl-brief.md.sha256`
- `docs/port-engineering/task31curl_probe_identity.py`
- `docs/port-engineering/task31curl_probe_closure.py`
- `docs/port-engineering/task31curl_probe_gatechain.py`
- `docs/port-engineering/task31curl_probe_gatechain2.py`
