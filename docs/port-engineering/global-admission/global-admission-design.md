# Global const-declaration admission widening + `mat3` support — design

Status: design only, READ-ONLY investigation. No file under `tools/`, `src/`,
`include/`, `tests/`, or `CMakeLists.txt` was modified. All widened-admission
behavior described here was verified by running *copies* of the real
generator/emitter under this directory
(`docs/port-engineering/global-admission/live_probe/`, rsync'd from the live
`tools/` and never written back), against the live tree at typed-count 154
(not the frozen 2026-08-12 census snapshot at 131). No `git` command was run.

## 0. Executive summary

The 25-program "global declaration" family (`docs/port-engineering/census/relaxed_global_probe.json`)
was re-verified byte-for-byte against the live tree — same 25 keys, same
second-blocker classification, same line:column locations
(`probe_layers123.json`). The published blocker table is correct as a
*first-order* classification. Going one and two levels deeper (which this
task required) surfaces three corrections load-bearing enough to change the
recommended slice:

1. **The "matrix indexing" blocker behind 6 of the 7 `mat3` programs is not
   about matrices at all.** It is a shared, byte-identical helper
   `vec3 linearToSrgb(vec3 linear)` that dynamically indexes a `vec3` by its
   own loop counter (`linear[i]` inside `for (int i=0;i<3;++i)`). This is a
   separate, smaller, highly reusable capability, unrelated to `Mat<N>`.
2. **`moodscape`'s entire matrix+hash closure is dead code** at its
   authorized `_defaults()` — confirmed independently by live BFS from
   `main()`. It needs a dead-code exemption, not real mechanism support.
3. **`shapeMixer` is not a 1-builtin (`reflect`) fix.** Peeling its error
   chain live surfaced at least 5 distinct, mutually unrelated capability
   gaps (`reflect`, `refract`, `mod(vec3,vec3)` overload, the shared vec3-
   index gate, `floatBitsToUint`) before the chain was still not exhausted.
   It should be excluded from this slice.

**Recommended near-term slice lands 3 programs cleanly** (`cellNoise`,
`filter/adjust`, `filter/colorspace`) via global-admission widening + mat3
support + one new shared vec3-index profile, landable with a **moodscape
dead-code exemption** for a 4th at effectively no extra mechanism cost, and
`colorLab` for a 5th needing the same vec3-index profile applied twice. Full
details and evidence in the sections below. `shapes` and `shapeMixer` are
NOT part of this slice (see §7).

## 1. Verified blocker table (re-run against the live tree, 154 typed)

Reproduced in `probe_layers123.json` (layer 1 = "layer1_all25_next_blocker").
Identical to `census/relaxed_global_probe.json`, confirming it is still
accurate:

| Second blocker | Count | Programs |
|---|---:|---|
| `unsupported typed type mat3` | 7 | cellNoise, colorLab, moodscape, shapeMixer, shapes, adjust, colorspace |
| `write to source const global` | 3 | cellRefract, kaleido, synth/shape |
| `unsupported builtin round` | 3 | fxaa, grain, snow |
| `unsupported varying` | 3 | spookyTicker, texture, wobble |
| `unsupported binary operator &` | 2 | bitEffects, glyphMap |
| `unsupported struct declaration` | 2 | historicPalette, palette |
| `unsupported typed type bvec3` | 1 | edge |
| `unsupported typed type float[9]` | 1 | emboss (see §6 — misleading label) |
| `unsupported typed type ivec2[9]` | 1 | normalMap |
| `unsupported typed type int[80]` | 1 | osd |
| `unsupported builtin floatBitsToUint` | 1 | scanlineError |
| **Total** | **25** | |

No program's blocker differed from the published table at layer 1. Layers 2
and 3 (mat3 type admission, then mat3 global-declaration admission) also
reproduced byte-identically, including line:column:

- Layer 2 (`unsupported global matrix declaration`, all 7): unchanged.
- Layer 3 (`unsupported typed expression index` for 6, `unsupported builtin
  reflect` for shapeMixer): unchanged. **But see §3 — the label on this
  layer is wrong.**

## 2. Exact site inventory

### Validator (`tools/glslcpp/generate_typed_slice.py`)

| Site | Line(s) | Role |
|---|---|---|
| `APPROVED_TYPES` tuple | L242-245 | 16-entry type list (separate from the frozen 44-entry `APPROVED_CAPABILITIES`, L220-231, independently re-counted at exactly 44). Add `"mat3"`. |
| Global admission loop | L2078-2126 | `admitted_globals` — currently admits only `const float` (plus 2 identity-authorized luma-weights carriers and per-key literal-int sets). **Never calls `used.add`** — vocabulary-free, confirmed by direct read. This is the mechanism to widen. |
| Unconditional matrix-kind global reject | L2161-2166 (`reject_type` call + explicit `declaration.type.kind == "matrix"` check) | Fires on EVERY declaration regardless of admission-loop outcome. Must add a `mat3` carve-out. |
| Construct validator | L2176-2184 | Matrix construct admits only `mat2(4 floats)`. Needs `mat3(9 floats)`. |
| Binary-expression validator | L2185-2223 (matrix branch L2220-2223) | Matrix binary admits only `mat2 * vec2` (tags `used.add("mat2-vector-multiply")`, the SAME existing capability token — reused, not renamed, since the 44-vocab is frozen). Needs `mat3 * vec3` added the same way. |
| Index validator | L2294-2357 | No matrix path at all (proof-based, only recognizes fixed-nine/fixed-grid/task19/task20 array proofs, or grade's identity list). This is where the *actually* needed new mechanism belongs (see §3), NOT a "matrix indexing" mechanism. |
| Function return-type ban | L2431-2433 | Matrix return type banned except for Rotate's authorized helper. None of the 7 target programs return a matrix — orthogonal to this slice. |
| Function parameter-type ban | L2443-2444 | Matrix parameter banned unconditionally. None of the 7 pass a matrix by parameter — orthogonal. |
| `reflect`/`refract` absent from `_BUILTINS`/`APPROVED_CAPABILITIES` | L220-241 | Needed only for `shapeMixer` (excluded from this slice, §7). |

### Emitter (`tools/glslcpp/emit_typed_cpp.py`)

| Site | Line(s) | Role |
|---|---|---|
| `_TYPES` dict | L93-99 | `"mat2": "glsl::Mat2"` present. Add `"mat3": "glsl::Mat3"`. |
| `_validate_source_globals` | L844-900 | **A second, independent, structurally-identical copy of the validator's admission loop**, used to build the dependency-topology needed for emission ordering. Confirmed by direct read: same `storage != "const" or type != FLOAT or initializer is None` gate, same recursive `initializer()` shape-checker. **Must be widened symmetrically** — verified empirically: `cellNoise`/`adjust`/`colorspace` reach full validator PASS under the relaxed-4 probe and then fail here with `unsupported source global declaration`, proving this is the next real gate, not a probe artifact. |
| `source_global_locals` | L948-970 | Actual C++ declaration emission — globals are re-materialized as **function-local** `const <type> <name> = <init>;` inside every consuming function (not true file-scope C++ globals). Uses `self.local_type()` → `_TYPES["mat3"]` once added. One special case: for `type.display()=="int"` it emits `declaration.initializer.literal` directly (preserves source token spelling) instead of calling `self.expression()` — decide during implementation whether newly-admitted int/uint globals need the same literal-preserving path or whether `self.expression()`'s literal handling (`std::int32_t(...)`/`std::uint32_t(...)`) is sufficient (it should be, since both paths produce the same value for an exact-integer literal; the existing special case is most plausibly about spelling/rounding fidelity for a specific already-shipped program, not a general requirement). |
| Construct emission, `mat2` case | L1342-1370 (mat2 at L1346-1351) | Only `mat2(4 floats)` → `glsl::Mat2(Vec2(a,b), Vec2(c,d))`. Needs `mat3(9 floats)` → `glsl::Mat3(Vec3(a,b,c), Vec3(d,e,f), Vec3(g,h,i))`. |
| Binary emission, matrix case | L1448-1450 | Only `mat2 * vec2`. Needs `mat3 * vec3`. |
| Index emission | L1382-1392 | `_proved_index`/`_proved_grade_index` gate — needs a matching new gate for the vec3-loop-index profile (§3). |
| Rotate's `matrix_return_program` gate | L1296-1325, L1903-1932 | Fires only when some function in the program RETURNS a matrix type. Verified none of the 7 target programs declare a matrix-returning function — this gate is inert for this slice. |

### Runtime (`include/noisemaker/glsl_types.hpp`) — read-only verification, no site work needed

Confirmed exactly as the roadmap claimed: `Mat<N>` is already fully generic.

- L221 `template <std::size_t N> class Mat`
- L264 `using Mat2=Mat<2>; using Mat3=Mat<3>; using Mat4=Mat<4>;`
- L231-232: `Mat<N>*Vec<N,float>` / `Vec<N,float>*Mat<N>` accumulate each
  output component in `double sum`, narrow **once** via `noisemaker::f32(sum)`.
- L235: `Mat<N>*Mat<N>` computes `result[column] = a * b[column]` — i.e. each
  column of the product is itself a `Mat<N>*Vec<N,float>`, narrowing once per
  element using the already-narrowed columns of `a`/`b`.

No runtime change is needed for `mat3*vec3` (Slice B shape); `Mat3` and its
multiply operators already exist and compile today, they are simply
unreachable from generated code because the generator/emitter reject the
type before ever emitting `glsl::Mat3(...)`.

## 3. The real prerequisite behind 6/7 "matrix indexing" blockers: a shared vec3-loop-index gate, not matrix indexing

Traced every reported `unsupported typed expression index` location down to
the actual preprocessed source line (line numbers in error messages are
**not** raw-file line numbers — `#ifdef GL_ES` / `precision highp float;` /
`#endif` lines are physically deleted, not blanked, during preprocessing,
shifting everything after by a few lines; had to fetch
`parse_program(...)["source"]` directly rather than trust `grep -n` on the
raw corpus file).

Every one of the 6 (`cellNoise`, `colorLab`, `moodscape`, `shapes`, `adjust`,
`colorspace`) is the SAME line inside a **byte-identical shared helper**:

```glsl
vec3 linearToSrgb(vec3 linear) {
    vec3 srgb;
    for (int i = 0; i < 3; ++i) {
        if (linear[i] <= 0.0031308) {
            srgb[i] = linear[i] * 12.92;
        } else {
            srgb[i] = 1.055 * pow(linear[i], 1.0 / 2.4) - 0.055;
        }
    }
    return srgb;
}
```

Confirmed byte-identical (sha256 `aa5ce4bbf69fa6b1...` of the extracted
function body) across ALL 7 mat3-family programs **including `shapeMixer`**
— `shapeMixer` has the same latent gate, it simply isn't reached yet because
`typed.functions` is validated in **alphabetical order** and `blend`
(containing `reflect`/`refract`) sorts before `linearToSrgb` (verified by
instrumenting a debug copy of the validator to print every `index` node
visited — zero fired before the `reflect` error, proving the ordering claim
rather than assuming it). `colorLab` additionally has a byte-different
mirror `srgbToLinear` (same shape, one more site — sha256
`a3ebfc6d3153dfaf...`).

**This is not matrix indexing.** `linear`/`srgb` are `vec3` locals, `i` is
the loop's own induction variable. The existing index-admission mechanism
(`generate_typed_slice.py` L2294-2357) is proof-based and only recognizes
fixed-size-array declarations/parameters (`proved_array_declarations`,
`proved_array_parameters`) or grade's identity-authorized sites — none of
which cover a plain `vec3` indexed dynamically. **Design: a new, small,
node-identity-authorized profile** — call it `linear_srgb_lane_index_v1` —
structurally parallel to the existing `literal_vec3_lane_index_profile` /
`grade_index_expression_profile` precedent:

- Authenticate, by exact AST node identity within a per-program frozen proof
  (source-hash-gated, like every other profile here), that the counted-for
  loop is exactly `for (int i=0;i<3;++i)` (loop-proof already proves trip
  count/bounds generically via `counted-for-v1` — this profile only needs to
  additionally authorize the `linear[i]`/`srgb[i]` READ/WRITE sites inside
  it, by identity, the same way `grade_valid` does at L2353 in the
  validator and `_proved_grade_index` does in the emitter).
- **Reusable across all 6-7 programs** since the shape (and even the AST
  structure per source hash) is identical — one profile, multiple
  `program_key` carriers, exactly like `LITERAL_VEC3_LANE_INDEX_KEYS` already
  covers 2 programs from 1 profile.
- **Zero vocabulary growth** — follows the `grade_valid` precedent exactly
  (comment at L2344-2352 is explicit that this shape must never touch
  `used.add`).
- `colorLab` needs it applied to 2 function bodies (`linearToSrgb` and
  `srgbToLinear`), everyone else to 1.

This is materially cheaper than a general "matrix indexing" mechanism would
have been (which nothing in the 7 programs' *reachable* code actually needs
— see §5).

## 4. `mat3` global-admission and type-support design

### 4.1 What must be admitted (validator + emitter, symmetric widening)

From the exhaustive global-declaration inventory (`probe_global_inventory.json`,
direct AST walk, all 25 programs), restricted to what this slice actually
needs:

- **`const mat3`**, initializer `mat3(<9 float literals>)` — the only shape
  present anywhere in the corpus for mat3 globals (`fwdA`/`fwdB`/`invB`/
  `invA`, all 9-literal `mat3(...)` constructs). No mat3 global uses a
  computed/nested initializer (unlike the existing float-global initializer
  grammar which permits `+`/`-`/`*`/`/` and identifier references to earlier
  admitted globals) — **do not build that generality for mat3**; admit
  exactly `mat3(float×9)` with all-literal arguments, mirroring the existing
  mat2-construct check's precision (`display()!="mat2" or len!=4 or
  any(child.type!="float")`) but for 9 args. This keeps the admitted shape
  provably narrow and matches what's actually shipped.

### 4.2 What must stay rejected

- **Non-`const` (mutable) globals** — `cellRefract`/`kaleido`'s non-const
  `float emboss[9]`/`sharpen[9]`/`blur[9]`/`edge[9]`/`edge2[9]` (no
  initializer, populated by scattered assignments inside `main()`) and
  `synth/shape`'s non-const `float aspectRatio`/`vec2 globalCoord` (same
  pattern, scalar). These are genuine **mutable cross-function scratch
  state**, a categorically different and much riskier feature (reentrancy/
  thread-safety assumptions, unclear emission target — the emitter's
  existing `_RESERVED_IDENTIFIERS` set already reserves `state`/`context`
  for something in this direction, suggesting a future "per-invocation
  context struct" mechanism, but that is out of scope here). **The widened
  admission loop must keep `storage == "const"` as an unconditional
  requirement** — this alone correctly continues rejecting all 3 programs
  with zero special-casing.
- **Struct types and struct arrays** — `historicPalette`
  (`const HistoricPalette[21] PALETTES`), `palette`
  (`const PaletteEntry[55] PALETTES`). `typed.structs` is unconditionally
  rejected elsewhere (`generate_typed_slice.py` ~L2155,
  `unsupported struct declaration`) — completely out of scope for a
  const-admission change; needs its own struct-type mechanism first.
  Nothing in this design should touch that check.
- **Global fixed-size non-struct arrays** (`normalMap`'s `ivec2[9]`/
  `float[9]×2`, `osd`/`spookyTicker`'s `int[80]`) — real global array
  consts, genuinely const-with-full-literal-list initializers, but a
  different capability shape from scalar/mat3 widening (needs an
  admission proof generalizing the existing LOCAL `fixed_nine_table_proof`/
  task19 family to GLOBAL scope). **Out of scope for this design** — call
  out as a natural "next slice" using the same profile-carrier pattern, not
  something to fold into the mat3/scalar widening.
- **`filter/emboss`'s real blocker is not a global at all.** Its listed
  global (`const vec3 LUMA`, admitted trivially by the vec3 widening) is a
  red herring; the actual next blocker is a **local** `float kernel[9];`
  inside `colorDefaultEmboss`, gated by the existing
  `fixed_nine_table_proof`'s `SOURCE_LOCKS` (a frozen per-program key set
  this program isn't in). Fix is extending that existing mechanism's locked
  key set, not this design's widening. Flagging this explicitly so nobody
  scopes "admit float[9]" into the const-global-admission task by mistake.

### 4.3 Widening shape, both admission loops (validator L2078-2126, emitter L844-900)

Symmetric change to both (they must stay in lockstep — the emitter's copy
existing at all, structurally duplicated, is itself worth flagging as
existing tech debt, but out of scope to consolidate here):

```
admit declaration if storage == "const" and (
    type == FLOAT and initializer is a well-formed float expression   # existing
    or type == INT and initializer is literal-or-literal-arith-of-int  # new, general
    or type == UINT and initializer is a literal                       # new, general
    or type == "vec3" and initializer is vec3(3 float literals)        # new, general
    or type == "mat3" and initializer is mat3(9 float literals)        # new, this slice
)
```

int/uint/vec3 admission is included here because it is the same mechanism
family and unlocks the other 18 non-mat3 programs' globals cheaply (ints and
uints are exact — no narrowing risk at all; vec3 built from 3 independent
float literals narrows identically in both languages, no accumulated
arithmetic). It is **not required** for the 3-5 program mat3 slice
recommended in §7, but the task asked for the admission-widening design in
general, and building only the mat3 case while 18 other programs have
sibling-shaped scalar/vec3 blockers sitting one line away would be a
false economy — the marginal cost of the scalar/vec3 cases is near zero
(no narrowing analysis needed, no emitter construct work beyond what
already exists for vec3, ints/uints already emit correctly via the
existing literal path). **Recommend landing int/uint/vec3 admission in the
SAME commit as mat3**, since it is the identical mechanism and several of
those programs (`fxaa`, `grain`, `edge`, `normalMap`, etc.) are otherwise
one step closer to landing too (though most still have their own further
downstream blockers — round/array-admission/etc. — not evaluated in depth
here, out of this task's scope).

## 5. Reachability + discriminability, per program (mandatory filters)

| Program | mat3 code reachable from `main()`? | vec3-index gate reachable? | Other reachable prerequisite gaps | Verdict |
|---|---|---|---|---|
| `filter/adjust:adjust` | Yes (`linear_srgb_from_oklab`; only declares fwdA/fwdB, not invA/invB — the inverse direction is never used) | Yes (`linearToSrgb`) | None found | **Clean** — reaches full VALIDATOR-PASS with only mat3 admission + mat3 construct/binary + vec3-index profile |
| `filter/colorspace:colorspace` | Yes (same shape as adjust) | Yes | None found | **Clean**, same as adjust |
| `classicNoisedeck/cellNoise:cellNoise` | Yes (`linear_srgb_from_oklab`) | Yes | `rotate2D` (mat2, unrelated) present but **not** reachable — inert | **Clean** |
| `classicNoisedeck/colorLab:colorLab` | Yes | Yes, **twice** (`linearToSrgb` + mirror `srgbToLinear`) | None found | **Clean but needs the vec3-index profile applied to 2 functions** |
| `classicNoisedeck/moodscape:moodscape` | **No** — verified by live BFS: neither `linear_srgb_from_oklab` nor `oklab_from_linear_srgb` nor the `floatBitsToUint`-bearing `randomFromLatticeWithOffset` call is in `main()`'s reachable set | N/A (unreached) | N/A | **Dead code.** Needs a proof that the whole closure is unreachable, not real support. Cheaper than the other path. |
| `classicNoisedeck/shapes:shapes` | Yes | Yes (same shared profile) | `floatBitsToUint` in `randomFromLatticeWithOffset`, confirmed **reachable** (unlike moodscape) — plus, per the roadmap's independent bitwise-cluster finding, the same helper's scalar-uint-XOR is shared across `bitEffects/kaleido/shapeMixer/shapes/synth/shape`, so `shapes` likely also needs that capability (not independently re-verified layer-by-layer here for time) | **Not clean** — needs mat3 + vec3-index-profile + floatBitsToUint identity-admission (existing mechanism, extend its authorized list) + probably the separate bitwise-XOR capability. Multi-cluster, defer. |
| `classicNoisedeck/shapeMixer:shapeMixer` | Yes | Yes (once reached — confirmed by peeling `reflect`→`refract`→`mod overload` away) | At least `reflect`, `refract`, `mod(vec3,vec3)` overload, `floatBitsToUint` (reachable=True), and almost certainly the bitwise-XOR capability next (chain not exhausted) | **Not clean at all** — 5+ unrelated capability gates before mat3 is even the binding constraint. Exclude. |

Discriminability: not independently oracle-verified in this task (that is a
separate, follow-on artifact per this project's established pattern — see
`docs/port-engineering/future-precompute/matrix/oracle/`). However,
`fwdA`/`fwdB` feed directly into `linear_srgb_from_oklab`, which is called
from the OKLab color-adjustment branch reachable at the program's default
`mode` uniform for `adjust`/`colorspace` (both are dedicated OKLab/color-
space filters — the matrix transform is the filter's core purpose, not a
peripheral branch), and `cellNoise`/`colorLab` similarly use it as a
mainline color-space step. High confidence of discriminability by
inspection; recommend building the small oracle (mirroring
`future-precompute/matrix/oracle/`) before landing, per this project's
established practice of never skipping that step.

## 6. Narrowing analysis — corrects the roadmap's "matrix-matrix never narrows" claim for the shape actually used here

Read the ACTUAL emitted JS for `fwdA * c` (`../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js`,
e.g. lines 933/944, repeated per-factory for every OKLab-using program):

```js
var fwdA = new Float32Array([1, 1, 1, 0.3963377773761749, ...]);
var lms = new $runtime.PooledFloat32Array([
  fwdA[0]*c[0] + fwdA[3]*c[1] + fwdA[6]*c[2],
  fwdA[1]*c[0] + fwdA[4]*c[1] + fwdA[7]*c[2],
  fwdA[2]*c[0] + fwdA[5]*c[1] + fwdA[8]*c[2]]);
```

**The transpiler does not call a `matrixMult()` helper for mat3\*vec3 at
all** — it inlines the dot product as unrolled scalar arithmetic. There are
exactly **2** call sites of `matrixMult(` in the entire compiled
`canonical-kernels.js`, both `matrixMult(matrixMult(T, Q), S)` (a mat4
bicubic-interpolation basis-matrix computation, unrelated to any of the 7
mat3 programs — none of them use `matrixMult()` or mat4 at all).

For the shape actually used here: `fwdA[column]` reads come from a
`Float32Array` (exact f32 values, represented exactly as JS doubles); the
three products and two additions execute in JS's native double precision;
the **sum narrows to f32 exactly once**, on construction of the
`PooledFloat32Array` result (`Float32Array`-backed, so assignment itself
rounds to nearest-f32). This is structurally **identical** to
`glsl::Mat<N>*Vec<N,float>` (`include/noisemaker/glsl_types.hpp` L231:
`double sum=0; sum += ...; result[row]=noisemaker::f32(sum);`), including
matching left-to-right accumulation order (`fwdA[0]*c[0] + fwdA[3]*c[1] +
fwdA[6]*c[2]` term order matches `matrix[column][row]` column-major
iteration order in the C++ operator). **Confirms narrowing-safety for Slice
B independently of, and consistent with, the existing
`future-precompute/matrix/oracle/` (`matrix-oracles.json`) finding** — that
oracle's scope note lists exactly `adjust, colorspace, cellNoise, colorLab,
shapes`, i.e. 5 of my 7 (missing `moodscape` [correctly, it's dead] and
`shapeMixer` [an oversight, per the roadmap's own note, "probably because it
indexes the matrix rather than multiplies it" — actually because it's
buried behind reflect/refract/mod-overload, per §7]).

**Correction offered, not required for this slice:** reading the actual
`matrixMult()` helper (`../noisemaker-for-cpu/src/csl/glsl-runtime.js`
L276-306) shows it too narrows via `Float32Array` + explicit
`Math.fround(sum)` in BOTH its matrix-vector and matrix-matrix branches —
contradicting the roadmap's claim that matrix-matrix products in JS
"accumulate into a plain Array" and "are never narrowed to f32". `alloc()`
(L120-124) returns a pooled `Float32Array`, not a plain `Array`. This may
mean the earlier-reported "Curl-tanh-class divergence... live for glitch"
concern needs re-verification against the current shipped runtime before
Slice C (mat4/`glitch`) work proceeds — but `glitch` is a mat4 singleton,
outside this task's mat3 scope, and this finding is offered as a heads-up
for whoever picks up Slice C, not independently chased further here.

## 7. Recommended slicing

| Slice | Programs | Count | Mechanism | Vocabulary impact |
|---|---|---:|---|---|
| **A — clean core** | `filter/adjust`, `filter/colorspace`, `classicNoisedeck/cellNoise` | **3** | mat3 admission (validator L2078-2126/2161-2166 + emitter L844-900) + mat3 construct/binary (validator L2176-2223 + emitter L1342-1370/1448-1450) + `_TYPES["mat3"]` (emitter L93-99) + new `linear_srgb_lane_index_v1` shared identity profile (1 site each) | Zero — no `used.add` anywhere in this path; new profile follows the `grade_valid`/`literal_vec3_lane_index_profile` precedent exactly |
| **B — +1 via double profile site** | `classicNoisedeck/colorLab` | **+1 (4 total)** | Same as A, `linear_srgb_lane_index_v1` applied to 2 sites (`linearToSrgb` + `srgbToLinear`) in this program | Zero |
| **C — +1 via dead-code exemption** | `classicNoisedeck/moodscape` | **+1 (5 total)** | A NEW, smaller mechanism: prove the whole matrix+hash closure is unreachable from `main()` at `_defaults()` (reuse the same BFS logic already used for verification here) and exempt it from type/index/builtin checks on that basis. **Does not require real mat3/vec3-index/floatBitsToUint support** — cheaper than Slice A/B despite looking like it needs the same admission. | Zero, and arguably simpler than A since no real matrix arithmetic needs emitting |
| **Deferred — multi-cluster** | `classicNoisedeck/shapes` | 0 (not landed by this slice) | Needs mat3 + the shared vec3-index profile (from A) + `floatBitsToUint` identity admission (existing mechanism, extend authorized list) + likely the separate bitwise scalar-uint-XOR capability (roadmap's bitwise cluster). Not a mat3-slice deliverable; land after the bitwise cluster's own work. | N/A here |
| **Deferred — bespoke, unrelated to mat3** | `classicNoisedeck/shapeMixer` | 0 | Chain of 5+ unrelated capability gates (`reflect`, `refract`, `mod(vec3,vec3)` overload, vec3-index profile, `floatBitsToUint`, probably bitwise-XOR) before mat3 is even the binding constraint. Treat as its own multi-mechanism task, not part of "mat3 admission." | N/A here |

**Honest count: this design lands 3 programs cleanly (Slice A), 5 with the
two cheap additions (B, C) folded in, and explicitly does NOT land `shapes`
or `shapeMixer`** — contradicting the original 7-program optimistic framing,
consistent with this project's established pattern that every prior
optimistic cluster estimate here needed correction. If C (moodscape's
dead-code exemption) is judged out of scope for a "global admission + mat3"
task specifically (since it's a different mechanism), the honest floor is
**4 programs** (A + colorLab).

The int/uint/vec3 general-scalar admission widening (§4.3) is recommended to
land in the same commit as mat3 (same mechanism, near-zero marginal cost,
no narrowing risk), but by itself does not land any additional *complete*
program in this 25-family set within the scope investigated here — every
other program in the family has a further, separately-scoped blocker
(round/struct/array/varying/bitwise) not evaluated in depth by this task.

## 8. What could not be verified

- **Discriminability was not independently oracle-verified** for
  `adjust`/`colorspace`/`cellNoise`/`colorLab` — argued from code inspection
  (OKLab transform is the filter's core purpose, not a peripheral branch)
  but not proven with a mutation-sweep oracle the way
  `future-precompute/matrix/oracle/` did for its 5-program Slice B claim.
  Building that oracle (same pattern) is recommended before implementation.
- **`shapes`'s and `shapeMixer`'s full blocker chains were not exhausted.**
  Both were peeled several layers deep (enough to establish they are
  multi-cluster, not mat3-scoped) but neither was walked all the way to
  VALIDATOR-PASS. Do not treat the specific gate lists in §5/§7 as complete
  — treat them as proof of "not a clean mat3 slice member," not as a full
  bill of materials for landing them later.
- **The `matrixMult()` matrix-matrix narrowing re-finding (§6) was not
  chased into the `glitch`/mat4 program itself** — out of scope (mat4
  singleton, not part of the 7-program mat3 family) — flagged as a
  heads-up, not resolved.
- **The emitter's `_validate_source_globals` (L844-900) widening was
  verified only by confirming it is the NEXT blocker after a fully-relaxed
  validator for 3 programs** (`probe_layer4.json`, `layer4_emitter` field)
  — the actual widened emitter code was not written or exercised (would
  require modifying `tools/`, which is banned for this task).
- **Whether `int`-typed globals need the `.literal`-preserving special case
  (emit_typed_cpp.py L964-966) extended to newly-admitted programs, or
  whether the general `self.expression()` literal path suffices**, was
  reasoned about but not empirically tested by generating and diffing
  actual C++ output (banned from writing to `tools/`/generating there).

## 9. Deliverables in this directory

- `global-admission-design.md` — this document.
- `probe_layer0_baseline.json` (+ `.sha256`) — real, unmodified live
  validator run over all 25 target keys, confirming the common starting
  blocker.
- `probe_layers123.json` (+ `.sha256`) — layers 1-3 (global admission →
  mat3 type admission → mat3 global-declaration admission), live tree,
  reproduces the census tables exactly.
- `probe_layer4.json` (+ `.sha256`) — layer 4 (+ matrix/vec3 index bypass,
  reflect/refract/mod-overload admission, mat3 construct/binary/return/
  parameter bypass) with reachability and matrix-touching-function analysis
  per program; this is where the moodscape-dead-code and shapeMixer-chain
  findings come from.
- `probe_global_inventory.json` (+ `.sha256`) — exhaustive per-program
  global-declaration inventory (storage/type/initializer shape) for all 25
  programs, direct AST walk.
- `scripts/` — the 4 probe scripts (`.py` + `.sha256`) plus
  `scripts/relaxed-diffs/` (unified diffs of the 4 relaxed validator copies
  against the real, unmodified `generate_typed_slice.py`, showing exactly
  what was provisionally patched for each probe layer — never applied to
  the real tree).
- `PROGRESS.md` — incremental working notes/checkpoints (raw investigation
  log; this design doc is the synthesized version).
