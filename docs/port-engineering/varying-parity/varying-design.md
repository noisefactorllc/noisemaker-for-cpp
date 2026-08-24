# Varying admission — `in` interface symbols (the `v_texCoord` family)

Design investigation for the next mechanism after the mutable-global-array
family: admitting source-declared **varyings** (`in vecN name;` at file scope)
into the typed slice. Target bucket, per `REMAINING-EFFECTS.md`: **4 real
programs** — `filter/grime:grime`, `filter/texture:texture`,
`filter/wobble:wobble`, `filter/spookyTicker:spookyTicker` — plus
`filter/wormhole:deposit`, which reports the same first blocker but is already
public through the scatter pass.

Status: **DESIGN — pre-implementation, pre-review.** Every figure below was
measured this session (2026-08-16/17) by probe against the pinned corpus
`a024dc3a960cc44af454abc7aebce50456c194e6`, using the same helpers
`mutable_global_frame_profile.py` exports (never hand-transcribed; re-derive
when amending). Probe state: the live tree's working slice had **186 rows /
44 capabilities** (the uncommitted cellRefract integration); all
first-blocker probes were run against that slice in an `rsync`'d copy.

**Headline findings, in order of decision weight:**

1. **The varying mechanism is ONE mechanism for the four real programs** —
   all four carry the byte-same shape: exactly one varying, `vec2
   v_texCoord`, read-only, every read inside `main`. A corpus-wide sweep
   found **exactly five** programs with varyings; the fifth (`wormhole:
   deposit`) carries a *different* materialization class (`vec4 vColor`,
   caller-supplied) and is already public — it needs nothing.
2. **The JavaScript does not interpolate varyings.** The runtime hardcodes a
   three-slot map (`glsl-runtime.js:95-99`): `vUv`/`v_texCoord` are aliases
   of the pixel context's `uv`, and `vColor` is copied from a caller-supplied
   `context.varyings?.vColor`. For the four programs, `v_texCoord` **is
   `context.uv`** — the pixel center's normalized coordinate, per-lane f32.
   There is no vertex stage anywhere in the CPU reference.
3. **The C++ port already has the value.** `glsl::PixelContext` carries
   `Vec2 uv{}` (`glsl_runtime.hpp:300`), populated by `make_context`
   (`pass_runner.cpp:25`). Admission is **pure expression lowering** — no
   new binding, no State/Frame field, no public-ABI signature change. A
   measured check (§5.4) shows the existing population is bit-identical to
   the JS materialization for every size 1..1024 (and spot checks 2048/4096).
4. **`wobble` is the only program whose entire remaining validator closure is
   the varying gate.** With the gate bypassed in a scratch copy, `wobble`
   (and `wormhole:deposit`) validate CLEAN; `grime` next-blocks on
   `floatBitsToUint`; `texture` on scalar-uint `^`/`>>`/`^=` and finally
   `inversesqrt`; `spookyTicker` is behind at least three further mechanisms.
   Recommended order: **wobble → grime → texture**, spookyTicker deferred
   (§8, §9.2).

---

## 1. Frozen authority — per-program facts

Measured with `_whole`/`_interface`/`_declaration_inventory`/`_node_census`/
`_call_graph`/`_reachability` from `mutable_global_frame_profile.py`, plus a
dedicated varying read-census walker (every `id` node whose `symbol_id` is a
varying symbol). All spans are **normalized-source** coordinates unless
marked raw.

### 1.1 `filter/grime:grime`

| Fact | Value |
| --- | --- |
| Source | `…/sources/filter/grime/grime.glsl` |
| Raw bytes / SHA-256 | 5,776 / `15a88fff0e951bf7fa01f4c982532cf79d835663cb2a81c2076c5fecbd9c351f` |
| Normalized bytes / SHA-256 | 5,279 / `692547b5193d0c03b3cb5fe86c570fff5ea74149affa6a5c88dac8c5b83eeba1` |
| Defines (default, canonical) | `{}` (none) |
| Whole-program SHA-256 | `3d7d6fa34d2842b85624168f1a160a61175cd6951f35bba229846c5e1a3a3512` |
| Interface SHA-256 | `a4493468e515741e459ca8ba83cd165d256bc1c9044e57b60b02f26669afa19d` |
| Node census | 645 nodes / 15 assigns |
| Declarations | 7 (1 sampler, 5 uniforms, 1 output) — **no const globals** |
| Functions | 14 (ids 40-53), all **reachable** |
| Resources | uniforms `(inputTex, resolution, fullResolution, tileOffset, strength, seed)`, samplers `(inputTex,)`, outputs `(fragColor,)`, uses_texture, no derivatives |
| Call graph | 22 edges; `main` → 8 helpers |

**The varying:** symbol id **55**, `v_texCoord`, `vec2`, storage `varying`,
`writable=False`, **2 reads / 0 writes**, both in `main`:

| Site (normalized) | Expression (raw line) |
| --- | --- |
| `131:24-131:34` | `vec2 globalCoord = v_texCoord * tileSize + tileOffset;` (raw `grime.glsl:140`) |
| `134:41-134:51` | `vec4 base_color = texture(inputTex, v_texCoord);` (raw `grime.glsl:143`) |

Raw declaration site: `grime.glsl:19` — `in vec2 v_texCoord;`. Note `resolution`
is declared-but-unread (same class as cellRefract's; it stays a required ABI
binding per the Shapes precedent).

### 1.2 `filter/texture:texture`

| Fact | Value |
| --- | --- |
| Source | `…/sources/filter/texture/texture.glsl` |
| Raw bytes / SHA-256 | 14,344 / `8e95251ef9a7789b1de4e51718ab3bebd9fc6d20db8acd0969191e288ec7454c` |
| Normalized bytes / SHA-256 | 10,411 / `0bc3450da3fd8a9fa6834a750689d085b4c427c9ed2a8906f610ca3855bc5ff9` |
| Defines (default, canonical) | `MODE=3` (`PreprocessorDefine(name='MODE', kind='int', canonical_value='3')`) |
| Whole-program SHA-256 | `be332c46aea5fbce4613e9be631b1585930045767abecd24f035d20427f2df21` |
| Interface SHA-256 | `5678a319d26e55b2035ee9b6df7f64eee996ee9bf4a9e58d05a5033eda6bbe62` |
| Node census | 1,186 nodes / 25 assigns |
| Declarations | 14 (1 sampler, 8 uniforms, 1 output, **4 const scalar globals**: `PI`, `INV_UINT32_MAX` (binary initializer), `Z_LOOP` (`const int`), `SHADE_GAIN`) |
| Functions | 25 (ids 77-101); **9 reachable** at `MODE=3`, 16 unreachable (`material_*` family, `height_canvas/crosshatch/halftone/stucco`, `shape_material`, `s_curve01`, `material_edge_mask`) |
| Resources | uniforms `(inputTex, time, alpha, scale, intensity, contrast, mono, tileOffset, fullResolution)`, samplers `(inputTex,)`, outputs `(fragColor,)`, uses_texture, no derivatives |
| Call graph | 28 edges |

**The varying:** symbol id **103**, `v_texCoord`, `vec2`, storage `varying`,
**6 reads / 0 writes** at `MODE=3`, all in `main`:
`287:41-287:51` (`texture(inputTex, v_texCoord)`), and the five
`height_field(v_texCoord …)` gradient taps at `304:35`, `305:35`, `306:35`,
`307:35`, `308:35`. (The `MODE >= 5` branch's three `material_value(…
v_texCoord …)` reads are stripped by normalization at `MODE=3`; the JS
factory retains them behind a runtime `MODE` binding — §4.4.)
Raw declaration site: `texture.glsl:30`.

### 1.3 `filter/wobble:wobble`

| Fact | Value |
| --- | --- |
| Source | `…/sources/filter/wobble/wobble.glsl` |
| Raw bytes / SHA-256 | 3,105 / `1bdd1e3bed9111743dfeb7e3418e14c42aa8d93ed4636167a99d17cb143a38cc` |
| Normalized bytes / SHA-256 | 2,589 / `c767dbef8eaa5c0730c6502053b7edf4af30d051de154425fd19860368e34545` |
| Defines (default, canonical) | `{}` (none) |
| Whole-program SHA-256 | `d3b1a67dbd5176e108376de6c5eb2164356b4fb172038a445f5b9f9fd9f8749f` |
| Interface SHA-256 | `65dad134040138d6596f9a2d07da1eddbce9fd68989624fa3b21a888eb67e888` |
| Node census | 370 nodes / 11 assigns |
| Declarations | 9 (1 sampler, 4 uniforms, 1 output, 3 const globals: `TAU` float, `X_NOISE_SEED`/`Y_NOISE_SEED` `vec3`) |
| Functions | 6 (ids 17-22), **all reachable** |
| Resources | uniforms `(inputTex, time, speed, range, wrap)`, samplers `(inputTex,)`, outputs `(fragColor,)`, uses_texture, no derivatives |
| Call graph | 5 edges |

**The varying:** symbol id **24**, `v_texCoord`, `vec2`, storage `varying`,
**1 read / 0 writes**, in `main` at `100:24-100:34` —
`vec2 sampleCoord = v_texCoord + offset;` (raw `wobble.glsl:102`).
Raw declaration site: `wobble.glsl:14`.

### 1.4 `filter/spookyTicker:spookyTicker` (scoped, deferred)

| Fact | Value |
| --- | --- |
| Source | `…/sources/filter/spookyTicker/spookyTicker.glsl` |
| Raw bytes / SHA-256 | 4,276 / `d50ca880cd6c6c03dd01a7ae683316d42ed93baddaadce9f3b918be1c816d50f` |
| Normalized bytes / SHA-256 | 3,393 / `d63a565fa4a814fa2377cd82a464fb296ee566dbbb0c8a5c0763193a33094830` |
| Defines | `{}` |
| Whole / interface SHA-256 | `4c8ac00d1365967229a412e4f6e6a5180a34842affc99014dd82314e22bea2fd` / `3d84a19370581017b270e9ffd5a4a2794e4976e8047b1427955e38a8f6abf5ce` |
| Node census | 394 nodes / 11 assigns |
| Declarations | 13 (1 sampler, 7 uniforms, 1 output, **`const int GLYPHS[80]` + 4 const int scalars**) |
| Functions | 4 (ids 25-28), all reachable |
| **The varying** | symbol id **30**, `v_texCoord`, `vec2`, **3 reads / 0 writes** in `main`: `92:34` (`texture(inputTex, v_texCoord)`), `101:24` (`px = int(floor(v_texCoord.x * dims.x))`), `102:41` (`pyFromBottom = … (1.0 - v_texCoord.y) …`) |

### 1.5 `filter/wormhole:deposit` (already public; no work)

`deposit.frag` is 117 bytes: one varying `vColor` (**vec4**, symbol id 4,
1 read at `6:17`), one output, `main { fragColor = vColor; }`. Raw bytes/SHA:
117 / `156401729b935381b38732d8e84ebdbbe185734e642972fa45533c5ce51a083d`;
whole/interface SHA `6ff76afdd24d243131cb6115039dc00bcbf65e23ba33f4b0c9d6938dcfd6e349` /
`94fd7d5c465eb37af45f6c9caca3582c7fb9a88c0a3a48e31800e5cbcd2219d3`. See §5.5.

### 1.6 The census: varyings are exactly five programs, one per program

A regex sweep of all 212 corpus sources for `(?:in|varying) <type> <name>;`
at file scope returns **exactly the five programs above** — `vec2
v_texCoord` ×4 and `vec4 vColor` ×1. No program has two varyings; no other
names (`vUv`) or types occur anywhere in the corpus. There is no `flat in`
in the corpus (the preprocessor's regex accepts it; nothing uses it). **The
mechanism's total scope is bounded at four real programs by measurement.**

### 1.7 A structural fact that shapes the locks: the varying Symbol's span is the whole file

`semantic.py:258-268` constructs each varying `Symbol` at the **whole-file
span** (it is created before declarations are inventoried; the preprocessor
drops the declaration line from the normalized source entirely —
`preprocess.py:55-61`, whose comment on the varying-drop `continue` reads
verbatim `# codegen maps varyings to ctx.uv`). Consequences:

- The blocker message reads `1:1 unsupported varying`
  (`generate_typed_slice.py:4173` reports `location(interface_symbols[0])`)
  even though the declaration sits at raw `grime.glsl:19`. This is why the
  census table says `1:1`.
- The varying is **not in `typed.declarations`** at all; it exists only in
  `typed.interface_symbols` and as the resolution target of `id` nodes in
  function bodies (`body_globals`, `semantic.py:266`).
- A per-key span lock must therefore lock the **raw-source declaration
  span** (regex-derived) and the read-site spans (from the `id` nodes), and
  must lock the Symbol's own span as the whole-file span it is — not as the
  declaration site it visually resembles.

---

## 2. First-blocker confirmation (both authorities, live slice)

Per-program `validate_capabilities` against the live 186-row slice's
capabilities, per the `REMAINING-EFFECTS.md` recipe (analyze →
attach both auto-proofs → validate; **never** `generate_outputs` with a
one-row slice). Validator and emitter probed independently — the emitter
(`render_typed_cpp(prog, key, source_hash)`) has its own gate order and does
**not** consult the validator.

| Program | Validator first blocker | Emitter first blocker |
| --- | --- | --- |
| `filter/grime:grime` | `1:1 unsupported varying` | `38:25 unsupported builtin floatBitsToUint` |
| `filter/texture:texture` | `1:1 unsupported varying` | `68:14 unsupported binary operator ^` |
| `filter/wobble:wobble` | `1:1 unsupported varying` | `100:24 unmapped typed symbol v_texCoord` |
| `filter/spookyTicker:spookyTicker` | `19:1 unsupported global declaration` | `19:1 unsupported source global declaration` |
| `filter/wormhole:deposit` | `1:1 unsupported varying` | `6:17 unmapped typed symbol vColor` |

Readings worth recording:

- The emitter's first blocker differs per program because its gates fire in
  emission order (function bodies sorted by id): grime's `hash31` (38)
  precedes `main`, so `floatBitsToUint` fires before the varying symbol is
  resolved; wobble's `main` (100) is the first construct that touches an
  unadmitted node. The **emitter has no varying-specific gate at all** —
  varyings reach `name()` (`emit_typed_cpp.py:3257-3284`) and die at
  `unmapped typed symbol {name}`. That raise is the emitter-side admission
  point; there is nothing to bypass before it.
- spookyTicker's validator blocker (`19:1`) fires in the **const-global
  admission loop** (`generate_typed_slice.py:4112-4115`), which runs *before*
  the `structs`/`uniform_blocks`/`interface_symbols` gates — i.e. gate order
  is: const-global admission loop → write-audit → structs → uniform blocks →
  **varyings** → declaration storage loop → expression gates → capability
  census. That is why spookyTicker censuses as a global-declaration program
  even though it is also a varying program.

---

## 3. What lies behind the varying — second-blocker ladder

Method: an `rsync`'d copy of `tools/glslcpp` under the scratch root with the
varying gate (`generate_typed_slice.py:4172-4173`) conditioned on an env
flag, plus — rung by rung — flags for the gates the ladder reached
(floatBitsToUint else-arm; uint-scalar `^`/`>>`/`&` rejections; scalar `^=`;
non-vocabulary builtins; const-array admission and array `reject_type`).
Each row below is the next rejection with all earlier rungs bypassed.
**These bypasses admit nothing** — they only reveal gate order; every real
admission must be an identity-authenticated carrier per §5.

| Program | With varying admitted, next blocker | Then | Then | Then |
| --- | --- | --- | --- | --- |
| `wobble` | **CLEAN** | — | — | — |
| `wormhole:deposit` | **CLEAN** | — | — | — |
| `grime` | `38:25 unsupported builtin floatBitsToUint` | **CLEAN** (with the 5 ingress sites admitted) | — | — |
| `texture` | `68:14 unsupported binary operator ^` (uint,uint) | `69:5 unsupported assignment operator ^=` (uint scalar) | `197:23 unsupported builtin inversesqrt`; with that bypassed: `missing capabilities inversesqrt` | (uint-scalar `>>` ×4 and uint-scalar `&` ×1 sit behind the `^`/`^=` rungs in the same walkers) |
| `spookyTicker` | `19:1 unsupported global declaration` (`const int GLYPHS[80]`) | `19:1 unsupported typed type int[80]` | `62:15 unsupported typed expression index` (`GLYPHS[digit * 8 + gy]`) | (behind that: `int >> int` and `int & int` — the JS-Number bitwise contract) |

Measured supporting censuses for the ladder:

- **grime** `floatBitsToUint`: **5 `builtin` nodes** — 2 in `hash21`
  (`38:25-38:45`, `38:47-38:67` — the `uvec3(floatBitsToUint(p.x),
  floatBitsToUint(p.y), 0u)` constructor), 3 in `hash31` (`43:25`, `43:47`,
  `43:69`). All in reachable code. Everything else grime uses is already
  admitted: its `pcg` is the *vector* form (`uvec3 ^= uvec3 >> 16u` — 1 `^=`
  assign, 1 `uvec3>>uint` shift), which rides the existing
  `uint-vector-bitwise` capability exactly as wobble's identical `pcg` does.
- **texture** uint census (whole program; reachable first): `assign ^=`
  ×8 (3 `hash_uint` **reachable**, 3 `fast_hash` **reachable**, 2
  `material_hash` unreachable), `binary ^(uint,uint)` ×5 (`fast_hash` 3,
  `material_hash` 2), `binary >>(uint,uint)` ×4 (`hash_uint` 3 reachable,
  `material_gradient` 1 unreachable), `binary &(uint,uint)` ×1
  (`material_gradient`, unreachable), `inversesqrt` ×1 (`material_gradient`,
  unreachable), `binary %(int,int)` ×4 (already admitted generically as
  `integer-modulo`). **Reachable uint work: 6 `^=` + 3 `^` + 3 `>>`, all
  scalar-uint.** Additionally texture's `MODE` is a runtime binding in the
  JS (§4.4) — the same authority shape cellRefract's `KERNEL=0` resolved.

Three consequences:

1. **No existing carrier covers any of texture's uint rungs.**
   `scalar-uint-xor-v1` is frozen to *"exactly three live scalar XOR nodes,
   ordered children of one uvec3 constructor"* (`scalar_uint_xor_profile.py`
   docstring and `_LOCKS`); texture's sites are compound `^=` assignments in
   a scalar chain — a different shape, so a new per-key record (not a key in
   that module as-is) is required. Scalar-uint `>>` is admitted **nowhere**
   (only `uvecN << uint` broadcast or the glyph-map `int >> int` arm), and
   `inversesqrt` is in no vocabulary and no identity list — texture would be
   its first appearance, which (unlike the identity-admission pattern) grows
   the frozen 44-entry capability vocabulary and disturbs every frozen
   historical hash unless it too is identity-admitted.
2. **grime's single second blocker has three paid-for precedents.**
   `floatBitsToUint` is identity-admitted today by four per-key lists:
   `caustic_word_hash_profile`, `scanline_error_float_bits_ingress_profile`,
   `shapes_float_bits_ingress_profile`, `shape_mixer_builtin_profile`
   (`generate_typed_slice.py:4518-4540`). grime needs a fifth record of that
   exact shape (5 sites, dict-keyed).
3. **spookyTicker is at least four mechanisms deep** — varying + const
   `int[80]` array (a *generalization* of `const-global-nine-table-v1`'s
   frozen cardinality/element allowlist) + JS-Number signed-int bitwise +
   typed expression index (the colorLab/moodscape mechanism). It is not a
   varying-slice candidate; see §9.2.

---

## 4. JavaScript materialization — the authority, quoted

This is the design's core question: **how does the shipped JavaScript
materialize a program declaring `in vec2 v_texCoord;`?** Answer, end to end,
with the exact lines.

### 4.1 The canonical generator copies varyings from a runtime map, per pixel

`scripts/upstream/compile-glsl.js` (the generator whose output is
`src/effects/generated/canonical-kernels.js`) emits, for **every** varying a
program declares (`compile-glsl.js:554, 570-573`):

```js
const varyingCopies = normalized.varyings.map(({ name }) => `  ${name}.set($runtime.varyings[${JSON.stringify(name)}])`).join('\n')
...
  return function canonicalKernel(context, out) {
    $runtime.beginPixel(context)
    ${varyingCopies}
    main()
    $runtime.writeColor(fragColor, out)
```

So the factory receives the varying **as a per-pixel copy from
`$runtime.varyings`** — not as a `$bindings` entry, not as a computed
expression. The declared variable is a factory-scope zero-initialised
`Float32Array` (the normalizer rewrites `in vec2 v_texCoord;` to a plain
`vec2 v_texCoord;` global — `glsl-normalize.js:219-222` — which codegen
materializes as `var v_texCoord = new Float32Array([0, 0]);`).

### 4.2 The runtime's varying map is hardcoded, three slots, no interpolation

`src/csl/glsl-runtime.js:95-99` and `:147-152`:

```js
this.varyings = {
  vUv: new Float32Array(2),
  v_texCoord: new Float32Array(2),
  vColor: new Float32Array(4),
}
...
beginPixel(context) {
  ...
  const uv = context.uv
  ...
  this.varyings.vUv[0] = uv[0]
  this.varyings.vUv[1] = uv[1]
  this.varyings.v_texCoord[0] = uv[0]
  this.varyings.v_texCoord[1] = uv[1]
  const color = context.varyings?.vColor
  if (color) this.varyings.vColor.set(color)
}
```

**There is no vertex stage and no interpolation anywhere.** The map has
exactly three names, two behaviors:

- `vUv` and `v_texCoord` — **aliases of `context.uv`**, whatever the program
  intended the varying to mean. (A WebGL build would interpolate a vertex
  output; the CPU reference does not — it *equates* the name with the pixel
  center's uv. The port's obligation is the CPU reference, so this aliasing
  **is** the parity contract.)
- `vColor` — copied from a caller-supplied `context.varyings?.vColor`, and
  left at zeros when the caller supplies none.

A declared varying with any other name would make `varyingCopies` emit
`name.set(undefined)` and throw at the first pixel. The corpus's five-name
census (§1.6) is therefore not just descriptive — it is the **soundness
bound** of the runtime's design, and the port's admission should enforce the
same bound (§5.2, foreign-name rejection).

### 4.3 What `context.uv` is: the pixel loop computes it as a double product, narrowed once per lane

`src/runtime/pass-runner.js:20-45` (the effect-running path; `renderer.js`
has the identical construction):

```js
const inverseWidth = 1 / width
const inverseHeight = 1 / height
const uv = new Float32Array(2)
...
const fy = height - y - 0.5
fragCoord[1] = fy
uv[1] = fy * inverseHeight
...
const fx = x + 0.5
fragCoord[0] = fx
uv[0] = fx * inverseWidth
kernel(context, out)
```

**Numeric contract of `v_texCoord`, per lane:** exactly one rounding —
`F32((x + 0.5) * (1.0 / width))` for lane 0 and
`F32((height − y − 0.5) * (1.0 / height))` for lane 1, with the multiply and
reciprocal in binary64 and the narrowing at the `Float32Array` store. All
downstream copies (`beginPixel`'s per-element stores, the factory's
`.set(...)`) are f32→f32 and idempotent. `v_texCoord == fragCoord.xy /
resolution` *as values*, but the port must match the **double-multiply**
form, not assume float division is the same thing (§5.4 measures that they
agree, which is why the existing C++ population is usable).

### 4.4 The four programs' factories, quoted

All four factories are byte-for-byte the same three-line shape (factory
names/registrations at `canonical-kernels.js:36246, 36327, 36341, 36358`):

- grime `canonicalFactory66` (`:13836`): `var v_texCoord = new
  Float32Array([0, 0]);` (factory line 16); reads at `… v_texCoord[0] *
  tileSize[0] + tileOffset[0] …` and `texture(inputTex, v_texCoord)`;
  closure `v_texCoord.set($runtime.varyings["v_texCoord"])` after
  `beginPixel`.
- spookyTicker `canonicalFactory147`: same slot line; reads
  `texture(inputTex, v_texCoord)`, `floor(v_texCoord[0] * dims[0])|0`,
  `floor((1 - v_texCoord[1]) * dims[1])|0`; same closure copy.
- texture `canonicalFactory161`: same slot line (factory line 25); six
  `v_texCoord` reads (base sample + five gradient taps) in the `MODE < 5`
  path *and* three `material_value(…, v_texCoord, …)` reads in the
  `MODE >= 5` path; same closure copy. **`MODE` is a runtime binding**
  (`var MODE = $bindings["MODE"];`, factory line 15) — the corpus row pins
  `MODE=3`, the port emits the normalized-at-3 semantics, and the oracle
  runs the JS factory with `MODE: 3` bound, exactly the cellRefract
  `KERNEL=0` resolution.
- wobble `canonicalFactory178` (`:22566`): same slot line; the one read
  `var sampleCoord = new $runtime.PooledFloat32Array([v_texCoord[0] +
  offset[0], v_texCoord[1] + offset[1]]);`; closure:

```js
  return function canonicalKernel(context, out) {
    $runtime.beginPixel(context)
  v_texCoord.set($runtime.varyings["v_texCoord"])
    main()
    $runtime.writeColor(fragColor, out)
  }
```

**Verdict on the core question: all four programs materialize the varying
identically — one mechanism.** The fifth program (`wormhole:deposit`,
`canonicalFactory181`) materializes `vColor` from the caller-supplied slot;
that is a second mechanism in the abstract, but it is moot for the port (§5.5).

---

## 5. Mechanism decomposition

### 5.1 One shared shape, per-key records

Because §4 shows a single materialization for the four programs, varying
admission is **one dict-keyed profile module**, not per-program mechanisms
and not a vocabulary capability. Module file
`tools/glslcpp/frontend/varying_uv_profile.py` — the **landed** filename,
authoritative (the module has already landed: 82 tests green, empty
registry; capability string, row field, and kwarg all match this design;
renaming landed code for cosmetics churns the tree) — capability string
`varying-uv-admission-v1`, slice row field `varying_profile`, kwarg
`varying_profile` on both `validate_capabilities` and `render_typed_cpp` —
the `mutable_global_frame_profile` shape (which was built dict-keyed for
exactly this style of follow-on), with the cellRefract §13-lesson applied:
**the module allows no sibling proof field** and freezes the
exactly-which-siblings-absent set.

No capability-vocabulary growth: like the frame/array/table carriers, the
gates get an identity-authenticated arm and the frozen 44-entry
`APPROVED_CAPABILITIES` tuple is untouched (so no historical-hash churn).

### 5.2 Per-key locks (`_LOCKS[key]`)

For each of the four keys (the first slice wires only wobble; the records
for grime/texture are added when their second blockers are built — a record
must not be frozen before its program's whole closure is admitted, or the
frozen "CLEAN behind the varying" census would be a lie):

- Source identity: raw/normalized bytes+SHA-256 (§1), caller `source_hash`,
  defines tuple (wobble/grime/spookyTicker `()`; texture
  `(("MODE","int","3"),)`), whole/interface fingerprints (§1).
- Inventory: declarations (name/ordinal/id/type/storage/span), functions
  (id/name/param tuples/return), resources, call-graph edge tuple,
  reachability pair, node census — all from §1's tables.
- The varying by identity: symbol id, name `v_texCoord`, type `vec2`,
  storage `varying`, `writable=False`, Symbol span **as the whole-file span
  it is** (§1.7), raw-source declaration span (regex `^\s*(?:flat\s+)?in\s+
  (vec2)\s+(v_texCoord)\s*;\s*$` anchored to its measured raw line), and —
  value-before-identity ordering per the `Symbol` self-absorption trap —
  the **materialization contract record**: `alias_of="context.uv"`,
  `numeric_contract="per-lane f32, single narrowing, double product"`.
- **Read census**: the exact (owner-function, span) pairs from §1, frozen as
  an ordered tuple; every `id` node referencing the varying symbol must be
  one of them. **Write census frozen EMPTY** (all four programs are
  read-only; the GLSL `in` storage and `writable=False` make this
  structural, but freeze the census anyway so a future parser change cannot
  silently admit a write).
- **Foreign-name rejection**: the module rejects any varying whose name is
  not in `{vUv, v_texCoord}` (the uv-alias map) — `vColor` belongs to the
  caller-supplied class (§5.5) and to no typed-slice program. This is the
  port-side mirror of the runtime's three-slot soundness bound (§4.2).
- Interface census: `len(program.interface_symbols) == 1` for the key, and
  zero varyings for every other corpus program (a corpus-wide test freezes
  the §1.6 census — the auto-attach proves `None` elsewhere).

### 5.3 The two gates, and the emission contract

**Validator** (`generate_typed_slice.py:4172-4173`): the raise becomes an
arm — if the program's interface symbols are exactly the authenticated
tuple (by object identity, consumed once each, in frozen order — the same
visitiation-ledger discipline as the frame/array/table carriers), admit;
otherwise raise the existing message unchanged. Nothing else in the
validator consults varyings: the `id` nodes referencing the symbol pass the
expression gates because the symbol resolves in `body_globals` (measured:
wobble is CLEAN behind the gate).

**Emitter** (`emit_typed_cpp.py:3257`, `name()`): a new arm before the
`unmapped typed symbol` raise, populated only for a program whose closure
this emitter authenticated itself:

```python
if symbol.id in getattr(self, "varying_fields", {}):
    # `context.uv` — the runtime's vUv/v_texCoord alias (glsl-runtime.js:149-150).
    self.emitted_varying_references.append(expression)
    return "context.uv"
```

Emission is then **pure expression lowering**: `v_texCoord` → `context.uv`
(a `glsl::Vec2` lvalue), swizzles/arithmetics flow through the existing vec
machinery (`glsl::swizzle<0>(context.uv)`, etc.). No `Frame`, no `State`
field, no kernel-signature change: every pixel function already receives
`const glsl::PixelContext& context`, and the generated
`pixel(const KernelState&, const glsl::PixelContext&, glsl::Vec4&)`
signature is untouched. **The public C++ ABI gains no parameters.**

### 5.4 The numeric contract is already met — measured, and to be locked

`make_context` (`pass_runner.cpp:20-29`) populates
`.uv = Vec2(frag_coord[0] / resolution[0], frag_coord[1] / resolution[1])`
— *float division*, whereas the JS is a *double product with a double
reciprocal* (§4.3). These are different expressions; their agreement is not
analytical. **Measured this session** (struct-packed f32 rounding,
exhaustive): for every width/height in 1..1024 and every pixel position,
both lanes, including the y-flip,
`F32((x+0.5)*(1.0/w)) == F32((F32(x)+0.5f)/F32(w))` — zero mismatches; also
zero for the x-lane at 2048 and 4096. Nothing in the tree consumes
`context.uv` today (the `uv[0]` occurrences in generated code are unrelated
locals — verified), so the existing population has never been
parity-exercised.

Design decision: **keep `make_context` as-is and freeze the measured
identity as a lock** — a Python probe test re-verifying the equality
exhaustively over a stated bound (say, 1..4096, both lanes), plus a native
test asserting `make_context(...).uv` equals the double-product form for the
oracle resolutions. Rationale: changing `make_context` to the double-product
form would be the *provably* exact form and is a one-line change, but it
touches a shared runtime path mid-integration; the measured identity makes
that unnecessary, and the bound is recorded rather than assumed. If any
future resolution breaks the equality, the one-line change is the amendment.
(This is the "measure the JS materialization per declaration" lesson applied
forward: the measurement, not the type, is the contract.)

### 5.5 The in-repo precedent: `wormhole:deposit` did NOT emit its varying

The scatter pass handled the one `vColor`-class varying by **not porting the
kernel at all**. In the C++ repo, `src/effects/scatter/wormhole.cpp` is a
hand-written adapter (`run_deposit`, registered
`scatter::register_scatter_adapter("filter/wormhole:deposit", &adapter)` at
`wormhole.cpp:173`, inside `register_adapter()`) implementing the deposit
algorithm directly — oklab lightness, angle, stride, wrap modes,
float16-truncate accumulation — with no typed-slice emission. The JS
authority does the same thing:
`src/effects/cpu/wormhole.js` `runWormholeDeposit` is a hand-written adapter
too, and the CPU renderer routes `drawMode: 'points' | 'billboards'` passes
to `resolveScatterAdapter(...)` **without ever calling the canonical
factory** (`renderer.js:947-957`). `canonicalFactory181` is registered but
never executed by the reference renderer.

Lesson for this design, both directions:

1. The caller-supplied varying class (`vColor`) has **no JS-exercised kernel
   semantics to port** — the factory is dead code in the authority — so the
   typed slice must not admit it (the foreign-name rejection of §5.2 is
   what keeps that honest).
2. The precedent says nothing about how to emit a `v_texCoord`-class
   varying — no typed-slice program has ever carried one. The real in-repo
   precedents for the *emission shape* are `context.frag_coord`
   (`emit_typed_cpp.py:3264-3265`: `gl_FragCoord` lowers to
   `context.frag_coord`, a builtin-symbol arm of the same `name()`
   dispatcher) and the frame-field arms — this mechanism is that pattern's
   fourth instance.

---

## 6. Proof composition (RED/GREEN sketch)

Both authorities independently call the authenticator; admission is by
object identity into a set consulted only by the new arms; every
authenticated varying symbol consumed exactly once per authority
(visitation ledger, the three-gate discipline of the frame/array/table
carriers — here two gates per authority: interface census and read census).

RED sequence, written first and watched failing for the intended reason:

1. Row absent: `1:1 unsupported varying` (validator) and, for wobble,
   `100:24 unmapped typed symbol v_texCoord` (emitter) — both live
   boundaries, already reproduced this session (§2).
2. Row present, carrier absent: the new module's
   `exact varying profile carrier required` at both authorities.
3. **Foreign-carrier sweep**: pass every sibling profile string
   (`mutable-global-frame-shape-v1`, `mutable-global-nine-array-
   cellrefract-v1`, `const-global-nine-table-v1`, `scalar-uint-xor-v1`, …)
   as `varying_profile`, and the new `varying-uv-admission-v1` as every
   other row field — assert rejection, and per the collision-chain trap,
   **record which neighbouring guard actually answers first** for each;
   claim only the rows tested. The two authorities will legitimately
   disagree on some messages (guard order differs); scope the same-message
   claim to the rows actually probed.
4. Per-lock mutations (value checks ordered ahead of node identity;
   surrounding hashes refrozen to the mutant; assert the coarse/identity
   messages did **not** fire): wrong raw/normalized hash; defines drift
   (texture `MODE=4` re-normalizes — record what changes, including the
   read-census delta); ±1 declaration/function in inventory; the varying
   renamed / retyped (`vec3`) / duplicated / made writable; a read inserted
   (a third `v_texCoord` mention in wobble's `main`) — the read census must
   name it; a write inserted — must fail the write census AND the storage
   class; the varying moved to a different function — owner mismatch;
   foreign-name varying (`vUv` actually occurs in no corpus program, so
   synthesize one in a mutation) — the alias-map rejection.
5. **Delete-the-check sweep**: one predicate at a time from the module
   source in the scratch copy; every deletion must turn at least one named
   test red; tabulate. Where a predicate is an `or`-chain, delete
   sub-clauses and test pairs of individually-green deletions together.
6. Sabotage test for the visitation ledger (drop one consumed symbol; the
   ledger count check must fire, not a downstream crash).
7. Auto-attach census: `attach`-equivalent proves `None` for every other
   corpus program (212-key census test, freezing §1.6).
8. The uv-identity locks of §5.4 (Python probe + native `make_context`
   equality).

## 7. Oracle sketch

`wobble_oracle_generator.mjs` in `docs/port-engineering/varying-parity/`, in
the shape/normalMap/cellRefract pattern: `--cpu-root` required and
realpath'd; refuse the live checkout, containment either way, in-repo roots;
per-file SHA-256 import closure; the pinned CPU-file hash set; factory
identity `kernelFactories.get(key) === canonicalKernelFactories[key]`;
factory name exactly `canonicalFactory178`;
`Function.prototype.toString` SHA-256 frozen at generation; adapter tables
censused (`canonicalAdapterFactories` must not own the key;
`check_corpus._ADAPTERS` parsed from live source must not contain it); GLSL
bytes/SHA pinned; stable path placeholder, absolute-path rejection.

Cases (full float32-word + RGBA8 arrays, stored once, materialized via the
Python materializer with field/duplicate/truncation/sidecar checks):

- `wrap-mirror` / `wrap-repeat` / `wrap-clamp` — the three `applyWrap` arms
  at distinct `wrap` bindings; mirror and repeat also exercise the
  folded-coordinate paths where the crop question (below) bites.
- `two-speeds-zero-range` — `speed` drives `simplexRandom`'s noise
  coordinates (the JS comment says speed is folded into the noise input so
  output varies even at `time=0`); `range=0` pins `offset` to zero and the
  case degenerates to a pure pass-through of `texture(inputTex,
  applyWrap(v_texCoord))` — **the cleanest possible discriminator of the
  varying itself**: any materialization error (wrong lane order, y-flip,
  f32 drift) lands exactly here.
- `time-sweep` — two `time` values, offset non-zero: exercises
  `v_texCoord + offset` through every wrap arm.
- ABI: bindings are `inputTex` texture + `time`, `speed`, `range`, `wrap`,
  all four `uniform float` in the GLSL and therefore `get_number` bindings
  (`wrap` is `int mode = int(wrap);` inside `applyWrap` — a float uniform
  narrowed at use, not an int32 binding; `wrap|0` in the JS factory is the
  ToInt32 of the same Number). Omit-each and wrong-variant-each with
  `KernelBindingError` naming the binding; extras ignored; exact alpha
  (`fragColor = sampled` — alpha is the texture's); determinism; independent
  output storage.

**Crop/tile behavior — probe before asserting (the binding §15 lesson).**
wobble's kernel uses *only* `v_texCoord`: no `tileOffset`, no
`fullResolution`, no `gl_FragCoord`. The offset is uniform across pixels, so
same-resolution tile-vs-full should agree wherever `sampleCoord` stays in
`[0,1]` — but under mirror/repeat the folded coordinate reads a *different
absolute texel* on a tile-sized input than on a full-sized input (the same
mechanism cellRefract §15 measured: destination-local uv collapsing through
a wrap into differently-sized textures). Do **not** assert the Shapes crop
identity: run the probe, and record either a measured identity witness with
its per-arm mismatch census or a measured non-identity witness, exactly as
cellRefract §15 did. The `range=0` case is the one arm where an identity is
*plausibly* sound (pure uv pass-through with no wrap crossing at interior
pixels) — probe it separately rather than assuming.

**Mutants — satisfiability/distinguishability caveats first** (normalMap
§11/§12: two of three design mutants were bit-identical and one was
unsatisfiable; budget only after verifying bit-difference on at least one
case):

- `varying-lane-swap` (uv.yx) and `varying-y-unflip` (treat uv as top-down)
  — *should* be the strongest discriminators, and directly pin §4.2's
  aliasing; verify bit-difference on `two-speeds-zero-range` (a pure
  pass-through case makes the y-flip difference maximal).
- `offset-sign-flipped`, `wrap-arm-swapped` (mirror↔repeat), and a
  `noise3d`-lattice perturbation (`hash31` seed encoding) — pin the
  non-varying path so the oracle is not blind to regressions there.
- Candidate mutant to **reject after probing**: a one-ULP uv perturbation —
  cellRefract §15 measured that nearest-sampling absorbs sub-texel
  perturbations (`prng_near_ulp_invariance`); wobble uses the same
  `sampleNearestBottomLeft` path, so a sub-texel uv mutant is *expected
  invariant* on most pixels. Record it as an invariance witness if probed,
  not as a discriminating mutant.

## 8. Recommended order among grime / texture / wobble

**wobble first; grime second; texture third; spookyTicker deferred.**
Evidence, all measured:

| Ranking input | wobble | grime | texture |
| --- | --- | --- | --- |
| Validator closure behind the varying | **CLEAN** | + `floatBitsToUint` ×5 (identity-admission, 4 paid-for precedents) | + scalar-uint `^`×5, `^=`×8, `>>`×4, `&`×1 (no existing carrier covers the shape; `>>`/`&` admitted nowhere), `inversesqrt` (vocabulary or new identity class), `MODE` runtime-binding authority note |
| Emitter work | one `name()` arm (+ shared varying gate) | same + `floatBitsToUint` sites (emitter precedent exists — shapes) | same + uint-scalar operator arms (new emitter surface) |
| Program size | 370 nodes / 6 fns / 2,589 B | 645 / 14 / 5,279 B | 1,186 / 25 / 10,411 B, 16 fns unreachable at `MODE=3` |
| Varying read census | 1 read | 2 reads | 6 reads |
| Oracle discrimination of the varying | `range=0` pass-through case | interleaved with multi-octave noise (harder) | gradient taps amplify uv errors (good) but wrapped in the deepest closure |

wobble is the only program where the mechanism lands **one closure from
done** at both authorities, it is the smallest program in the bucket, and it
has a purpose-built varying discriminator case (`range=0`). grime is one
identity-admission of a well-precedented shape away. texture is a
three-mechanism program that merely *starts* with the varying — exactly the
"first barrier only" warning of the census. (Also: landing wobble first
exercises the shared varying carrier on the smallest read census, so the
grime/texture records extend a proven module rather than debugging it
inside a bigger program.)

## 9. Risks, unknowns, and deferred scope

### 9.1 Risks and expected discoveries for the wobble slice

- **Emitter second gates are unprobed behind `name()`.** The §2 emitter
  probe stopped at the first unadmitted construct per program; once the
  `name()` arm exists, later emitter gates (the compound-assign reducer,
  `mod` overloads, the `?:` chains in `applyWrap`) may surface. wobble's
  validator-CLEAN result makes validator-side surprises unlikely, but the
  emitter is an independent grammar — each discovery is an amendment, and
  the wcSimplify lesson (bare void-call statements) says emitter gaps can
  need their own identity-gated arms.
- **The uv numeric identity is empirical, not proven** (§5.4). Bound it,
  lock it, and name the one-line `make_context` amendment if it ever breaks.
- **The whole-file-span Symbol** (§1.7) will tempt an implementer to "fix"
  the span to the declaration site. Don't: the span is part of frozen
  identity (whole/interface fingerprints include `interface_symbols`); lock
  it as-is and carry the declaration span separately from the raw source.
- Collision-chain staleness (REMAINING-EFFECTS): the foreign-carrier sweep
  will find most sibling rejections answered by neighbouring guards; record
  the ownership map rather than claiming the chain.
- `resolution` is declared-but-unread in grime only; wobble declares no
  resolution-class uniform at all — no Shapes-style unread-binding question
  arises for the first slice.

### 9.2 spookyTicker is explicitly deferred — and why

spookyTicker's closure behind the varying, enumerated by the §3 ladder:

1. **`const int GLYPHS[80]`** — not reachable by a key in
   `const-global-nine-table-v1` (frozen nine-element cardinality, element
   allowlist) and not by the mutable-array carrier (it is const, literal,
   never written). It needs a generalized const-literal-array carrier (int
   element, cardinality 80) — its own slice, with the normalMap §15
   pool-safety question re-derived for an *integer* pool table.
2. **Typed expression index** — `GLYPHS[digit * 8 + gy]` at `62:15`, the
   colorLab/moodscape mechanism, unsolved today.
3. **JS-Number signed-int bitwise** — `float((row >> (6 - gx)) & 1)` at
   raw `spookyTicker.glsl:65`. **Checked against the two existing
   carriers:** `bitwise-scalar-int-ops-v2` (`bitwise_scalar_int_ops_profile.py`)
   is single-key — `KEYS = ("synth/bitwise:bitwise",)` — and its v2
   transform retypes a frozen Number *region* to FLOAT with ToInt32
   boundaries at the operators; spookyTicker's shift/mask sit inside an
   `int`-typed pipeline (`GLYPHS` is `int[80]`, `gx`/`row` are `int`), a
   different pre-transform shape, so it needs its own record after the
   module is dict-keyed. `glyph-map-nonnegative-int-shift-v1`
   (`glyph_map_nonnegative_int_shift_profile.py`) is *also* single-key
   (`filter/glyphMap:glyphMap`) but its two-node shape — nonnegative
   `int >> int` plus `& 1` mask — is **structurally exactly** spookyTicker's
   `(row >> (6 - gx)) & 1` (`row ∈ [0,0x7E]`, `6 - gx ∈ [0,6]`, both
   nonnegative by the `sample_glyph` guard). So the operators need no new
   grammar — `>>` and `&` are already in the frozen 17-entry binary
   vocabulary — but the *carrier* must be widened from one key to two, with
   glyphMap's frozen locks untouched. **spookyTicker is reachable without
   new operator grammar; it is not reachable without three carrier slices.**
4. The varying itself — shared with this design, record frozen when its
   other three mechanisms land.

Deferral rationale: it is the only bucket member whose varying admission
buys nothing until three other mechanisms exist; planning it with them would
violate the one-mechanism-per-slice discipline the global-declaration bucket
post-mortem (four sub-shapes, every member double-blocked) already
established.

### 9.3 What this investigation could not determine

- The **emitter-side** ladder behind `name()` for each program (§9.1): the
  emitter gates fire in emission order and the probe stops at the first;
  only implementing the arm reveals the rest. Expected, not measured.
- Whether the **tile-vs-full crop identity** holds for wobble under
  mirror/repeat (§7): the mechanism is identified (wrapped uv through
  differently-sized textures) but the witness direction requires the oracle
  harness, which is implementation-lane work.
- The **`& 0xffffu` / `>> 16u` uint-scalar admission shape for texture** is
  enumerated but not designed (no existing carrier; whether it is a new
  dict-keyed module or a generalized scalar-uint profile is a decision for
  texture's own design pass).
- `PooledFloat32Array` scratch-aliasing (normalMap §15) is **not** a hazard
  here — the varying slot is a factory-scope `new Float32Array` (not
  pooled), measured in all five factories — but texture's *other* work
  (uint ops) has not been pool-audited; that belongs to its slice.

## 10. Slice row (first landing, wobble)

Insert at sorted index 153, between `filter/wind:wind` and
`filter/wormhole:blend` (measured against the 186-row working slice; re-check
neighbors at insertion time):

```json
{
  "defines": {},
  "program_key": "filter/wobble:wobble",
  "varying_profile": "varying-uv-admission-v1"
}
```

Projected at landing: 187 typed rows; 189 catalog entries (wobble is not
dual-registered); corpus keys absent 26 → 25; genuinely unported 26 → 25.
Read the native census assertion (`tests/test_generated_kernels.cpp`) and
move it by the measured delta — never carry it forward by arithmetic
(cellRefract §11). Compute the new typed-list SHA-256 (sorted keys joined by
`\n` **with trailing newline**) and all artifact hashes from generator
output.

Generated namespace: sorted insertion index 153 becomes `typed_153` at
insertion time — re-derive at landing; existing namespaces at higher indices
shift, and the historical-reconstruction test normalizes exactly those
ordinals (cellRefract minor-corrections precedent).

### Independent review (2026-08-17)

Independent design review (frozen record:
`docs/port-engineering/prepared-designs-review-kaleido-varying-effects.md`)
returned verdict **GO-WITH-CORRECTIONS**. The corrections were applied in
place above:

1. **Important — §1.4's spookyTicker interface SHA-256 carried a
   one-hex-digit transcription error.** The measured value is
   `3d84a19370581017b270e9ffd5a4a2794e4976e8047b1427955e38a8f6abf5ce`; this
   doc had `…55e3888f6abf5ce` (char 57 'a' vs '8'). Figure fixed.
2. **Minor — §5.1's module filename.** The LANDED module is
   `tools/glslcpp/frontend/varying_uv_profile.py` (82 tests green, empty
   registry; capability / row-field / kwarg all match this design), not
   `varying_profile.py`. §5.1 amended to make the landed filename
   authoritative — renaming landed code for cosmetics churns the tree.
3. **Minor — §5.5's scatter-registration citation.**
   `src/effects/scatter/wormhole.cpp:173` (inside `register_adapter()`),
   not `:207`. Fixed.
4. **Minor — §1.7 rendered a paraphrase as a quote.** The actual
   `preprocess.py:60` comment is `# codegen maps varyings to ctx.uv`; §1.7
   now quotes the real comment.

### Implementation amendment (2026-08-18): tile-crop non-identity on BOTH arms; wobble has no tile bindings

Measured by the wobble oracle lane before asserting anything (the cellRefract
§15 lesson applied): tile ≠ top-down crop on **both** arms — live-clamp
74/120 words, and the §7 "plausibly sound" range=0 arm **75/120**. The
mechanism is stronger than cellRefract's: wobble declares no
`tileOffset`/`fullResolution` bindings whatsoever, so `v_texCoord` is purely
destination-local and the two routes sample differently-sized inputs through
the warp with no world alignment to share. Coincidental equalities are exact
f32 matches plus clamp-saturation collapse (probed with instrumented
post-wrap sampleCoord publishers), never alignment. **No crop identity may
be asserted on any wobble arm**; both full-route surfaces are stored beside
the tile case in `wobble-oracles.json`.

Also measured and recorded by the same lane: at shipped defaults
(speed 5, range 0.5, wrap 0) every scalar binding is output-inert (max
offset 0.0275 < the half-texel margin 0.03125 — a structural bound, the
Shapes-§11 pattern); the `range` binding wakes the warp (384 lanes); wrap
ToInt32 truncation controls (unbound → mirror, 0.5 → mirror, 1.5 → repeat);
and the mirror↔clamp edge-texel alias caveat (shallow crossings make that
pair agree despite crossing — "crossing ⟺ wrap switch differs" is not a
theorem; both alternates recorded per case).
