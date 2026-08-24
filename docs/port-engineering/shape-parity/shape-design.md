# Shape184 source-authenticated design and implementation checklist

Target: `synth/shape:shape`, as typed row 184 — and, through it, the **mutable
uninitialized file-scope global** mechanism, the first of the four sub-shapes
hiding behind `unsupported global declaration`.

Status: read-only design. No repository file was created or modified while
preparing this document except this file and its containing directory. No
build, no generator run against the repository, no `git` command. Every probe
ran against an `rsync`'d copy of `tools/` under an external run root; two probes
deliberately patched **that copy** of the validator and emitter, never the live
tree.

Confidence is recorded per section in §12. Read that before trusting anything
here. The Shapes183 design was confidently wrong three times, and the specific
way it was wrong — asserting a control that could not be satisfied, projecting
three closures where four were needed, and reporting a gate as unconditional
when it was conditional — is the failure mode this document tries to avoid by
labelling inference as inference.

---

## 1. Outcome and authority

Port exactly `synth/shape:shape`. All values below were recomputed from the
pinned corpus during this task, not copied from another document.

| Fact | Value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Canonical source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/shape/shape.glsl` |
| Raw authority | 15,986 bytes, SHA-256 `d917d2027c873f05bc4183277a2b1dffe158c13cfd1281461580a31e0cd7d67f` |
| Normalized authority | 14,805 bytes, SHA-256 `83bf41728f8e10ed08ec04a9899f35d60b476700703d4db851f57289cf6f1b00` |
| Typed functions SHA-256 | `9aea716238e075a431961c875f674c34b97ed44a5071be54de2a21f3cf94d7d3` |
| Typed whole-program SHA-256 | `60d87d93ec58d1f4c1e25a70d011a83c65b1988bf337bfbbf28e0e8c99a7e1ea` |
| Typed interface SHA-256 | `06d49ba68a175bf4f313fab9533e889b049fe6593af34b0d49b62da28d23f2fd` |
| Exact default defines | `LOOP_A_OFFSET=40`, `LOOP_B_OFFSET=30` |
| Declarations / functions | 15 / 28 |
| Corpus ordinal (0-based, of 212) | **208** |
| Program / effect / runtime key | `synth/shape:shape` / `synth/shape` / `synth/shape:shape` |

The three typed hashes are **independently reproduced** here — they are already
frozen inside `tools/glslcpp/frontend/scalar_uint_xor_profile.py` under the
`synth/shape:shape` entry, and the recomputation from a fresh parse matched all
three byte-for-byte. That is a real cross-check, not a restatement: the XOR
profile's Shapes-family locks are current.

The corpus source is **byte-identical** to the live upstream checkout at
`~/platform/noisemaker/shaders/effects/synth/shape/glsl/shape.glsl`
(same SHA-256, `diff` exit 0). Unlike Shapes, there is not even a comment-URL
divergence. Do not refresh the pinned corpus during this task.

### 1.1 Resources — the complete ABI

Ten uniforms, no samplers, one output, **no texture reads, no derivatives, no
loops**:

`resolution`, `tileOffset`, `fullResolution` (`vec2`); `time`, `loopAScale`,
`loopBScale`, `speedA`, `speedB` (`float`); `seed` (`int`); `wrap` (`bool`);
output `fragColor` (`vec4`).

`LOOP_A_OFFSET` / `LOOP_B_OFFSET` are **compile-time defines, not bindings**.
Ten runtime bindings, two defines — never report twelve bindings. (Shapes183
§4 made the same distinction with 18 and 2.)

`resolution` is declared and **never read** anywhere in the program. It remains a
required ABI binding. Do not "clean it up".

### 1.2 Ordinal and blast radius

Insertion is by sorted key. `synth/shape:shape` lands at **typed ordinal 181**
(0-based), i.e. emitted namespace `typed_181`:

```
179 synth/polygon:shape
180 synth/sacredGeometry:sacredGeometry
181 synth/shape:shape          <- new
182 synth/solid:solid          (was 181)
183 synth/subdivide:subdivide  (was 182)
```

**Only two existing programs shift ordinal.** Shapes183 shifted 175. The
reconstruction gate is correspondingly cheaper, but not weaker — it must still
prove all 183 surviving emitted blocks are byte-identical after the `typed_N`
sentinel substitution.

### 1.3 Projected counts

| Quantity | Now | After |
| --- | ---: | ---: |
| Typed rows | 183 | **184** |
| Catalog entries (`kCatalog`) | 185 | **186** |
| Corpus keys absent from slice | 29 | 28 |
| Genuinely unported | 28 | **27** |
| Rows with non-empty `defines` | 26 | 27 |
| `scalar_uint_xor_profile` carriers | 3 | **4** |
| `mutable_global_frame_profile` carriers | 0 | **1** |

- Current sorted 183-key SHA-256: `b10e0d7eb918c60dae3fa24d0a09b1a9578a334c39ab5a9561db54176eca539b`
- **Projected sorted 184-key SHA-256: `026637ff3fec7a9282d4dea84af058acd95612a9f86afff59294062f7f639aec`**

Both computed over sorted keys joined by `\n` **with a trailing newline**, per
the standing trap in `../REMAINING-EFFECTS.md`.

### 1.4 Pre-change artifacts to reconstruct exactly

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 22,728 | `8fb3b8bc876c380a0c406fdae8e81b74d4499924cf301ed7a980c450f7ccfe0a` |
| `src/typed_generated/typed_slice.cpp` | 1,819,738 | `b3b53be504f0e84879d443418f6fe17af5d0605c9589c64e4a21d4e19f803cf5` |
| `src/typed_generated/typed_manifest.json` | 292,207 | `5281d964596734fc447c4d0450906bc2c7fbd6ee7b7e1e971b8ee563c62daab0` |
| `include/noisemaker/generated/catalog.hpp` | 16,926 | `44b05685a3bdd263df1bd8834b8f994e6fc63b1a7717b2111b06e74272411be0` |

`typed_slice.json` is the pre-change **input** lock, not a reconstruction
output.

### 1.5 Canonical JavaScript authority

| Fact | Value |
| --- | --- |
| Factory | **`canonicalFactory274`** |
| `Function.prototype.toString` length | 20,489 bytes |
| `Function.prototype.toString` SHA-256 | `870d97a811e5720f827f5616057483a43b27224240ac95c04a8084dd257a6125` |
| `kernelFactories.get(key) === canonicalKernelFactories[key]` | **true** |
| `canonicalAdapterFactories` owns the key | **false** |
| `check_corpus._ADAPTERS` contains the key | **false** |

`check_corpus._ADAPTERS` is exactly
`{classicNoisedeck/fractal:fractal, filter/historicPalette:historicPalette,
filter/palette:palette, synth/julia:julia}` — verified by import, not by reading
a document. **`synth/shape:shape` is not adapter-routed**, so it is not in the
`fractal` eligibility limbo.

Pinned CPU-relative reference files, all six re-hashed during this task and all
six **identical to the values Shapes183 pinned** (the JS reference has not
drifted since row 183 landed):

- `src/effects/generated/canonical-kernels.js`: `66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe`
- `src/effects/catalog.js`: `d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4`
- `src/csl/glsl-kernel.js`: `a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa`
- `src/csl/glsl-runtime.js`: `a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072`
- `src/runtime/pass-runner.js`: `fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa`
- `src/runtime/surface.js`: `0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59`

---

## 2. The blocker, verified

Both rejections in the handoff reproduce **exactly**, against the live 183-row
capability tuple, via per-program `validate_capabilities` (never
`generate_outputs` — see the probe trap in `../REMAINING-EFFECTS.md`):

```
no carriers:            synth/shape:shape: exact scalar uint XOR profile carrier required
scalar_uint_xor_profile='scalar-uint-xor-v1':
                        synth/shape:shape:31:1: unsupported global declaration
```

Normalized `31:1` is:

```glsl
31|float aspectRatio;
32|vec2 globalCoord;
```

### 2.1 It is two declarations, not one

**The reported blocker names only the first of two mutable uninitialized
globals.** `synth/shape` declares:

| Symbol id | Storage | Type | Name | Initializer | Normalized span |
| ---: | --- | --- | --- | --- | --- |
| 14 | `global` | `float` | `aspectRatio` | none | `31:1-31:19` |
| 15 | `global` | `vec2` | `globalCoord` | none | `32:1-32:18` |

`../REMAINING-EFFECTS.md` describes this program's blocking declaration as
`float aspectRatio;`. That is accurate as the *first* rejecting site and
inaccurate as the *bill of materials*. **The mechanism must admit a `vec2` as
well as a `float` on day one**, and the two have materially different
materialization contracts (§4). Anyone who scopes this as "a scalar" will find
the second declaration at implementation time.

### 2.2 There are five such programs in the corpus, not four

A direct AST walk over all 212 corpus programs for declarations whose storage is
neither `uniform`, `output`, nor `const`:

| Program | Mutable uninitialized globals |
| --- | --- |
| `classicNoisedeck/cellRefract` | `float[9]` × 5 (`emboss`, `sharpen`, `blur`, `edge`, `edge2`) |
| `classicNoisedeck/effects` | `float[9]` × 7 (adds `edge3`, `sharpenBlur`) |
| `classicNoisedeck/kaleido` | `float[9]` × 5 |
| **`synth/noise:noise`** | **`vec2 globalCoord`** |
| `synth/shape:shape` | `float aspectRatio`, `vec2 globalCoord` |

`synth/noise:noise` is a fifth member of this sub-shape. It does not appear in
the frontier's global-declaration bucket because its *first* blocker is
`unsupported counted-for program proof` (reproduced here at normalized
`250:5`). Its `vec2 globalCoord` is the same reduced shape this slice builds,
so once its counted-for blocker is resolved it needs **no new global mechanism**
— it needs this one, with one added `_PROFILES` entry. That is a real, verified
correction to the "4 programs" figure and it improves the mechanism's leverage.

### 2.3 What the validator gate actually is

Two sites in `tools/glslcpp/generate_typed_slice.py`, both of which must be
widened, plus their emitter mirrors:

1. The admission loop's fall-through:
   `if storage != "const" or declaration.type != FLOAT or declaration.initializer is None: raise ... unsupported global declaration`.
2. A **second, unconditional** post-loop check over every declaration:
   `if declaration.symbol.storage not in {"uniform", "output", "const"}: raise ... unsupported global declaration`.
   Admitting in (1) alone is not sufficient. This is the same two-site pattern
   the `mat3` widening hit (`global-admission/global-admission-design.md` §2).
3. `tools/glslcpp/emit_typed_cpp.py::_validate_source_globals` is a second,
   structurally duplicated admission loop; its fall-through raises
   `unsupported source global declaration`.

`admitted_globals` in the validator (and `self.source_globals` in the emitter)
is the **const** set, and both carry an `audit_expression` pass that raises
`write to source const global` on any assignment whose base targets a member.
Mutable globals must therefore be admitted into a **separate** set, not into
`admitted_globals` / `source_globals`, or every write in `main` will be rejected
by the const-write audit.

### 2.4 There is no hidden validator closure — verified, not assumed

With the mutable-global admission relaxed **and nothing else changed**, and with
`scalar_uint_xor_profile='scalar-uint-xor-v1'` supplied, `synth/shape:shape`
reaches **VALIDATOR-CLEAN**.

This is the single most useful fact in the document, and it is the direct answer
to the Shapes183 §12 failure mode (a fourth closure that appeared only at
implementation time). It was obtained by patching the *copied* validator's two
gates and re-running `validate_capabilities`. It does **not** prove the emitter
is clean; that is §2.5.

The same relaxation applied to the array-form programs immediately fails with
`unsupported typed type float[9]`, confirming they are a different mechanism
(§11).

### 2.5 The emitter closure is exactly two things — verified

Relaxing the emitter's `_validate_source_globals` fall-through in the copy, the
next and only failure is:

```
synth/shape:shape:407:41: unmapped typed symbol aspectRatio
```

Adding a name mapping for the two symbols (the probe mapped them to
`frame.<name>`) makes the emitter **run to completion**, producing 50,623 bytes
of C++ with no further error. So the complete emitter closure for this program
is:

1. admission in `_validate_source_globals`;
2. a storage decision and name mapping for the two symbols in every function
   body and in `pixel`.

Nothing else. No new expression kind, no new builtin, no new statement form.
The assignment to a global lowers through the existing statement-level `assign`
path (unlike Shapes183 §12, there is **no rvalue assignment anywhere in this
program**).

---

## 3. The state question: who writes, who reads, and can a read precede a write

A mutable global is a state question, not a syntax question. This section is the
crux. Everything in it is a complete census produced by walking the typed IR,
not by reading the GLSL.

### 3.1 Complete write census — two writes, both in `main`, both plain `=`

| Symbol | Owner | Normalized span | Operator |
| --- | --- | --- | --- |
| `globalCoord` | `main` | `459:5-459:47` | `=` |
| `aspectRatio` | `main` | `461:5-461:54` | `=` |

There is **no other write anywhere in the program**: no compound assignment, no
`++`/`--`, no write inside any helper, no write inside any conditional or loop
(the program has no loops at all).

### 3.2 Complete read census — seven reads across five functions

| Symbol | Owner | Normalized span | Live at defines 40/30? |
| --- | --- | --- | --- |
| `globalCoord` | `main` | `460:15-460:26` | **yes** |
| `globalCoord` | `diamonds` | `417:20-417:31` | no — `offset` arm `410` |
| `aspectRatio` | `shape` | `424:26-424:37` | **yes** — `offset` arm `40..120` |
| `aspectRatio` | `offset` | `439:34-439:45` | **yes** — `offset` arm `30` |
| `aspectRatio` | `circles` | `407:41-407:52` | no — arm `10` |
| `aspectRatio` | `rings` | `412:41-412:52` | no — arm `400` |
| `aspectRatio` | `diamonds` | `418:27-418:38` | no — arm `410` |

At `LOOP_A_OFFSET=40` the taken `offset` arm is `loopOffset >= 40 && loopOffset <= 120`
→ `shape(st, 4, freq*0.5)`; at `LOOP_B_OFFSET=30` it is the `loopOffset == 30`
arm, which reads `aspectRatio` inline. Neither reaches `circles`, `rings`,
`diamonds`, or `value`. All 28 functions are nevertheless **reachable in the
conservative call graph** (the XOR profile's frozen `reachable` tuple is
`range(95, 123)`, i.e. all of them, with an empty `unreachable` tuple) — so this
is a *dynamic* dead-branch boundary, exactly like Shapes183 §3.2, not a
call-graph one.

### 3.3 Write-before-read is statically provable

`main`'s first four top-level statements, in order:

```
458  vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
459  globalCoord = gl_FragCoord.xy + tileOffset;     <- write
460  vec2 st = globalCoord / fullResolution.y;       <- read (after its write)
461  aspectRatio = fullResolution.x / fullResolution.y;  <- write
```

The proof obligations, all discharged:

1. Both writes are **unconditional top-level statements of `main`** — not inside
   any `if`, block, or loop. (`main.body` indices 1 and 3.)
2. **No call expression occurs anywhere in `main` before statement index 3.**
   Statements 0–3 contain no `call` node. Therefore no helper — and so no helper
   read — can execute before both writes.
3. The only read before the `aspectRatio` write is the `globalCoord` read at
   `460:15`, which follows the `globalCoord` write at `459:5`.
4. Every remaining read is inside a helper, and every helper is reached only
   through `offset(...)` at `main` statements later than index 3.

**Conclusion: no read can precede its write on any reachable path.** This is
*not* a stop condition. It is, however, a load-bearing structural claim, and §5
requires it to be locked by the profile and proved load-bearing by deleting the
lock.

### 3.4 What this means for emission

Because every write is in `main` and every helper read is read-only, the
carrier can be a **`pixel`-scope object passed to helpers by `const` reference**.
`const`-ness is then a *compiler-level enforcement* of the single-writer lock: if
the lock were ever wrong, the build would fail rather than silently diverge.
That is a stronger position than the array form can occupy (§11).

---

## 4. How the shipped JavaScript materializes it — the parity target

**The parity target is the transpiler's materialization, not GLSL semantics.**
This has bitten the project five times. Read off `canonicalFactory274` in
`../../../../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js`:

```js
function canonicalFactory274($bindings, $runtime) {
  ...
  var fragColor = new Float32Array([0, 0, 0, 0]);
  var PI = 3.1415927410125732;
  var TAU = 6.2831854820251465;
  var aspectRatio = 0;                            // plain Number (double)
  var globalCoord = new Float32Array([0, 0]);     // f32 lanes
  ...
  function main () {
    var color = new $runtime.PooledFloat32Array([0, 0, 0, 1]);
    (globalCoord[0] = gl_FragCoord[0] + tileOffset[0],
     globalCoord[1] = gl_FragCoord[1] + tileOffset[1], globalCoord);
    var st = new $runtime.PooledFloat32Array([globalCoord[0] / fullResolution[1],
                                              globalCoord[1] / fullResolution[1]]);
    aspectRatio = fullResolution[0] / fullResolution[1];
    ...
  }
  return function canonicalKernel(context, out) {
    $runtime.beginPixel(context)
    main()
    $runtime.writeColor(fragColor, out)
  }
}
```

Four findings, all load-bearing:

**(a) They are factory-scope `var`s, created once per factory instantiation, and
they are NOT re-initialised per pixel.** `$runtime.beginPixel(context)`
(`src/csl/glsl-runtime.js:132`) resets only the runtime's index pools, the
derivative index, and `fragCoord`. It does not touch closure variables. So in
the reference, both globals genuinely carry over between pixels.

**(b) That carry-over is unobservable, because of §3.3.** Both are written
before any read within each `main()` call. A C++ port that constructs a fresh
per-pixel carrier is therefore observationally identical — *conditional on the
write-before-read proof holding*. This is why §3.3 is a lock and not a remark.

**(c) `aspectRatio` is a plain JS Number — a DOUBLE — and is never narrowed to
f32.** `fullResolution[0] / fullResolution[1]` divides two exact-f32 doubles in
double precision and stores the double. A port that types this field `float`
because GLSL says `float` **diverges**. The emitter's existing convention
already gets this right: `local_type()` returns `"double"` for `float`
(`emit_typed_cpp.py:2463-2467`, "Canonical scalar temporaries retain JavaScript
Number precision"), and the probe emission produced exactly

```cpp
frame.aspectRatio = (static_cast<double>(glsl::swizzle<0>(state.fullResolution))
                   / static_cast<double>(glsl::swizzle<1>(state.fullResolution)));
```

which matches the JS line term-for-term. **This is discriminable by oracle** —
see §4.1.

**(d) `globalCoord` is a `Float32Array` mutated lane-by-lane, so each lane write
narrows to f32.** `glsl::Vec2` narrows identically (`Vec::operator=(const
FloatExpr<2>&)` applies `noisemaker::f32` per lane). The probe emitted
`frame.globalCoord = glsl::Vec2((glsl::swizzle<0,1>(context.frag_coord) + state.tileOffset));`
— correct. Note the *initial* values also match a value-initialised aggregate:
`0` and `[0, 0]`.

Also worth recording, because it looks like a divergence and is not: the JS
materializes the two compile-time defines as **bindings**
(`var LOOP_A_OFFSET = $bindings["LOOP_A_OFFSET"]`) and turns
`#if LOOP_A_OFFSET >= 200 && LOOP_A_OFFSET < 300` into a runtime `if`. The C++
preprocesses it away at 40/30. Identical behaviour at frozen defines; the oracle
must still pass both defines in `$bindings`, as Shapes183's generator does.

### 4.1 Measured discriminability of the materialization

Executed the unmodified public factory through the pinned
`bindCanonicalKernel` / `runPass` / `Surface` path, and against two source-level
mutants built by patching the factory text and recompiling with `new Function`.
**These are measurements, not predictions.**

Mutant **`shape-aspect-f32-narrowed`** — `aspectRatio = Math.fround(fullResolution[0] / fullResolution[1])`:

| Case | Discriminates? | Why |
| --- | --- | --- |
| 64×36, speeds 50/50 | **yes** | 64/36 is not exactly f32-representable |
| 1280×720 full, 40×24 tile at (100,60) | **yes** | same ratio |
| 64×36, 32×20 tile at (16,8) | **yes** | |
| 64×36, 16×16 tile at (8,4) | **no** | same ratio — the sampled pixels happen not to differ |
| 36×64 (portrait) | **no** | 0.5625 is exactly f32 |
| 60×40 | **no** | 1.5 is exactly f32 |
| 48×48 (square) | **no** | 1.0 is exactly f32 |
| speeds 0/0 | **no** | `offset()` never called; `aspectRatio` written but never read |

Two consequences the fixture design must respect: a discriminating case needs an
aspect ratio that is **not** exactly f32-representable *and* at least one
non-zero speed; and **two cases with the same aspect ratio can differ in whether
they discriminate**, so per-case discrimination must be *generated and recorded*,
never asserted from the ratio alone.

Mutant **`shape-globalcoord-unnarrowed`** — `var globalCoord = [0, 0]` (double
lanes instead of `Float32Array`):

| Case | Discriminates? |
| --- | --- |
| tileOffset `[0,0]`, `[8.25,4.5]`, `[1048576.5,0]` | no |
| tileOffset `[16777216,0]` | **yes** |
| tileOffset `[131072.1,0.3]` | **yes** |

So the `globalCoord` f32-lane contract **is** oracle-discriminable, but only at
extreme tile offsets where `gl_FragCoord.xy + tileOffset` leaves the exactly-
representable range. A fixture with only ordinary tile offsets would leave this
half of the mechanism unwitnessed. §6 therefore requires an
`extreme-tile-offset` case.

### 4.2 Axis liveness, measured

| Axis | Result | Note |
| --- | --- | --- |
| External `runPass` time/seed | **invariant** | the factory reads `$bindings` only — the Shapes183 control holds here too |
| Bound `time` | **live** | 0.5 → 10.0 changes output |
| Bound `seed` | **invariant at 40/30** | measured across four settings (speeds ±, wrap on/off, loopAScale 37 and 99) |
| Bound `wrap` | **live only when `lf` is non-integral** | invariant at `loopAScale=1` (`map`→6.0, `floor(6.0)`→6.0); live at `loopAScale=37, loopBScale=61` |
| `speedA`/`speedB` sign and zero | **live**, all seven combinations produce distinct outputs |
| Output alpha | uniformly `0x3f800000` | |
| Top-down crop translation | **0 mismatches** with `tileOffset.y = full_height − crop_y − tile_height` | Shapes183 §4.2 rule applies unchanged |

**Learn the Shapes183 §11 lesson up front: do not demand a bound-`seed` control
that differs.** `seed` is dead at 40/30 for the same reason as in Shapes — it is
consumed only inside `randomFromLatticeWithOffset` (`seedInt` at normalized 76,
`seedBits` at 93) and inside `value()`'s `interp == 10 / 11` arms, all of which
are behind `offset`'s `300..380` arm. Record it as **proven invariant**, with a
`seed_liveness_census`, and keep it a required `int32` ABI binding. Do the same
for `wrap` at any case where `lf` is integral, or choose loop scales that make
it live.

---

## 5. Chosen mechanism

Two carriers on the one new row. **Zero growth of the frozen 44-entry capability
vocabulary and the frozen type tuple.**

### 5.1 Reuse `scalar-uint-xor-v1` unchanged

`scalar_uint_xor_profile.py` already contains a complete, frozen
`synth/shape:shape` lock: source/normalized/functions/whole-program/interface
hashes, define tuple, declaration and function counts, function-inventory and
bindings digests, resource tuple, loop tuple, owner
(`randomFromLatticeWithOffset`, id 117, span `71:1-110:2`), parent, three sites
(`97:10-97:46`, `98:10-98:46`, `99:10-99:47`), scalar census digest, call-graph
digest and full reachability. All the coarse hashes were re-derived here and
match.

**Do not edit that lock and do not add a Shape-specific XOR helper.** Wiring is:
add `"scalar_uint_xor_profile": "scalar-uint-xor-v1"` to the row, add the
allowed-field arm (§5.4). The XOR block's own metadata guard is permissive
enough that a new companion carrier does not require editing it — verify that
during implementation rather than assuming it.

Claim boundary, inherited: those three XOR sites and the whole
`randomFromLatticeWithOffset` body are **dynamically dead at 40/30**. Structural
authentication and `tests/test_numeric.cpp` carry their proof. Never claim a
full-surface render executed them.

### 5.2 New: `mutable-global-frame-shape-v1`

New module `tools/glslcpp/frontend/mutable_global_frame_profile.py`, following
the **per-key-profile-name, shared-module** shape of
`linear_srgb_lane_index_profile.py` (`linear-srgb-shapes-lane-index-v1`,
`linear-srgb-adjust-lane-index-v1`, …) rather than the single-name shape of
`scalar-uint-xor-v1`. That is deliberate: `synth/noise:noise` will want
`mutable-global-frame-noise-v1` from the same module with no edit to this row,
and the array-form programs (§11) will want their own names again.

Admission is by **exact AST node identity** against a per-key frozen record,
gated on source and typed hashes, and must **skip `used.add(...)`** — the
`grade_valid` / `literal_vec3_lane_index_profile` precedent. No capability
token. No type-tuple entry (`float` and `vec2` are already approved types; it is
the *storage class*, not the type, that is being admitted).

### 5.3 Proposed slice row

```json
{
  "defines": {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30},
  "mutable_global_frame_profile": "mutable-global-frame-shape-v1",
  "program_key": "synth/shape:shape",
  "scalar_uint_xor_profile": "scalar-uint-xor-v1"
}
```

Fields alphabetical, matching the file's existing convention. Require both
carriers together at both the validator and the emitter boundary; missing,
wrong, foreign, or partially composed combinations fail closed in both
directions.

### 5.4 Wiring sites

Validator (`tools/glslcpp/generate_typed_slice.py`):

- import + `PROFILE`/`KEYS` re-export (two import blocks, mirroring
  `shapes_rvalue_assign_profile`'s pair at L149 and L319);
- allowed-field-set arm for `synth/shape:shape`:
  `{"defines", "program_key", "scalar_uint_xor_profile", "mutable_global_frame_profile"}`;
- a **dedicated** slice-census check with its **own message**
  (`typed slice mutable-global frame profile drift`) — do not add a clause to
  the 14-clause `or` chain, which reports every failure under
  `typed slice literal vec3 lane profile drift` and points at the wrong
  mechanism;
- `validate_capabilities` keyword parameter, an `if profile is not None:` guard
  block with the companion-exactness and collision matrix, and the symmetric
  `elif typed.key in MUTABLE_GLOBAL_FRAME_KEYS: raise ... exact mutable-global frame profile carrier required`;
- widen **both** validator global gates (§2.3 items 1 and 2), admitting only
  declarations that are members of the authenticated record — by object
  identity, not by storage class;
- register the admitted declarations in a set **separate from
  `admitted_globals`**, so the const-write audit continues to reject writes to
  const globals while permitting the two authenticated writes.

Emitter (`tools/glslcpp/emit_typed_cpp.py`):

- the mirrored keyword parameter and guard (`emit_typed_cpp.py` re-authenticates
  independently; the validator and emitter remain independent authorities);
- widen `_validate_source_globals` symmetrically, into a separate set;
- `_TYPES` needs nothing new;
- emit the frame struct, its `pixel`-scope instance, and the extra helper
  parameter (§5.5);
- reserved-identifier handling (§5.6);
- a visitation ledger: every authenticated node consumed exactly once, with a
  negative test that sabotages the ledger.

Schema/state: `typed_slice.json` row, `tests/test_typed_generator.py` counts and
censuses, the four generated artifacts.

### 5.5 Emitted shape

Inside the program namespace, emitted **only** for a carrier program:

```cpp
struct Frame final {
  double aspectRatio{};        // JS: var aspectRatio = 0        (Number/double)
  glsl::Vec2 globalCoord{};    // JS: new Float32Array([0, 0])   (f32 lanes)
};
```

`pixel` declares `Frame frame{};` before the first emitted statement and writes
into it directly. Every helper of the carrier program gains a third
emitter-bound parameter `[[maybe_unused]] const Frame& frame` after
`const State& state` and `const glsl::PixelContext& context`; reads lower to
`frame.<name>`.

Field types come from the existing `local_type()` convention — `double` for
`float`, `glsl::Vec2` for `vec2` — which is what makes §4(c) correct by
construction rather than by special-casing. The profile must **assert** the
mapping rather than inherit it silently, so that a future change to
`local_type()` turns something red here.

Three properties this shape buys:

1. `const Frame&` in helpers is a **compiler-level enforcement** of the
   single-writer-is-`main` lock from §3.1. If that lock is ever wrong, the build
   fails; it cannot silently diverge.
2. `Frame frame{}` value-initialises to `0.0` / `[0,0]`, which are exactly the
   JS factory-scope initial values, so the "carry-over is unobservable" argument
   never has to be relied on for the first pixel.
3. The struct generalizes to the array form without redesign (§11), by relaxing
   `const Frame&` to `Frame&`.

**Rejected alternative A — thread the values by value through the transitive
read closure.** Smaller signature footprint, but it requires computing and
freezing a per-helper closure, produces non-uniform signatures, and does not
generalize to the array form, whose writer is a helper. Rejected.

**Rejected alternative B — put the fields in `State`.** `State` is `const` at
every use site and is shared across the whole pass; per-pixel mutation of it
would break the const contract and be a thread-safety hazard. Rejected.

**Rejected alternative C — a general "mutable global" capability.** Grows the
frozen vocabulary and admits the construct program-wide. Banned by the
node-identity policy that every mechanism in this project follows.

### 5.6 The `_RESERVED_IDENTIFIERS` hazard — checked

`emit_typed_cpp.py:379` reserves `{state, context, output, kernel_base}`, and
`_safe_identifier` mangles **any** GLSL local or parameter with a reserved name,
**in every program**. Adding `frame` unconditionally would therefore change the
emitted C++ of any already-frozen program that declares a local named `frame`.

Census of the pinned corpus: **no `.glsl` source declares an identifier named
`frame`.** All seven files containing the word have it only inside comments,
which normalization strips. So the addition is a no-op today.

Do not treat that census as sufficient on its own — the 184→183 historical
reconstruction is the test that proves it, and it must be run and must show all
183 surviving blocks byte-identical. If a future corpus refresh introduces a
local named `frame`, the reconstruction is what will catch it.

---

## 6. Oracle, provenance, coordinates, and exact comparer

Mirror the Shapes183 package exactly; it is the current standard and it worked.
One deterministic package, no alternative locations:

- `docs/port-engineering/shape-parity/shape184_oracle_generator.mjs`
- `docs/port-engineering/shape-parity/shape184-oracles.json` (canonical full-array authority)
- `docs/port-engineering/shape-parity/shape184-oracle-report.md`
- `tools/glslcpp/generate_shape_native_oracle_include.py` (sole JSON→C++ materializer)
- `tests/oracles/shape184_expected.inc`

A sibling `<artifact>.sha256` for all five; every generator/checker verifies all
applicable sidecars byte-for-byte. Negative tests on the materializer for
missing/extra fields, duplicate case names, malformed dimensions/counts/hex
words/byte values, wrong hashes/sidecars, truncated/extra arrays.

The JSON locks schema/version, corpus revision, key, exact defines, source
path/bytes/SHA, factory name and text SHA, generator provenance, comparer
self-test ledger, unique case/coverage labels, and exact full arrays. Per case:
dimensions; all **ten** runtime bindings; the two defines recorded **separately**;
external pass time/seed; every float/Vec lane as a hexadecimal f32 word; expected
full-surface f32 words and RGBA8 bytes; finite/non-finite counts; SHA-256 over
each array.

### 6.1 Independent JavaScript authority

Identical discipline to Shapes183 §4.1: `CPU_ROOT` is an **immutable snapshot**
of `~/platform/noisemaker-for-cpu` under the run root; the generator takes a
required `--cpu-root`; every CPU import is resolved by real path and required to
be beneath `CPU_ROOT`; imports or cache hits from the live checkout are a hard
failure. Before execution require
`kernelFactories.get(key) === canonicalKernelFactories[key]`, require the
function to be named `canonicalFactory274` with
`Function.prototype.toString` SHA-256
`870d97a811e5720f827f5616057483a43b27224240ac95c04a8084dd257a6125`, and require
`canonicalAdapterFactories` not to own the key. Pin the six CPU file hashes from
§1.5. Execute the unmodified public factory through
`bindCanonicalKernel` / `runPass`; a locally reimplemented formula is not an
oracle.

### 6.2 Proposed fixture set — eight cases

Each case's coverage claim below is **measured** (§4.1, §4.2), not projected.

| Case | Purpose |
| --- | --- |
| `shape-landscape-64x36` | baseline; non-exact aspect; discriminates `aspect-f32` |
| `shape-crop-1280x720` | tile route at a production-shaped resolution; discriminates `aspect-f32`; carries the crop translation proof |
| `shape-square-48` | **non-reaching control** for `aspect-f32` (ratio exactly 1.0) |
| `shape-portrait-36x64` | **non-reaching control** (ratio 0.5625, exactly f32) with a different shape than square |
| `shape-zero-speeds` | **non-reaching control**: `offset()` never called, `aspectRatio` written and never read |
| `shape-wrap-live-37-61` | the only case where the `wrap` axis is live; non-integral `lf` |
| `shape-negative-speeds` | the `speedA<0` / `speedB<0` arms; discriminates `aspect-f32` |
| `shape-extreme-tile-offset` | the **only** case that discriminates `globalcoord-unnarrowed` (tile offset `[131072.1, 0.3]`, measured) |

Add no case without a proved live branch lacking a witness. The four `speed`
sign/zero combinations that are not top-level cases should be covered as nested
controls on `shape-landscape-64x36`, not as new top-level cases.

### 6.3 Controls, with the Shapes183 §11 mistake pre-corrected

Attach to `shape-landscape-64x36`:

- **External-pass invariance** (measured to hold): render with `runPass` time/seed
  words `(0x00000000, 0x3f800000)` and `(0x4f000000, 0xcf000000)`; require
  identical full arrays.
- **Bound `time` liveness** (measured to hold): `0x3f000000` → `0x41200000` must
  differ.
- **Bound `seed` invariance** (measured): record verbatim and prove invariant.
  Ship a `seed_liveness_census` naming every `seed` consumer and why each is
  unreachable at 40/30. **Do not require it to differ.** `seed` remains a
  required `int32` ABI binding: phase 2 still omits it once and supplies a wrong
  variant once.
- **Bound `wrap`**: invariant on `shape-landscape-64x36` (integral `lf`), live on
  `shape-wrap-live-37-61`. Record both, and record *why* they differ — this pair
  is itself a parity assertion.

### 6.4 Mutation ledger

`shape184_oracle_generator.mjs` independently computes both mutants —
`shape-aspect-f32-narrowed` and `shape-globalcoord-unnarrowed` — records per-case
f32/RGBA8 hashes, and `--check` validates the exact case-by-mutant
discrimination table. The expected table is the measured one in §4.1; a case
that flips is a stop condition, not something to re-baseline. The native
implementation must match only the unmutated oracle. Do not commit hand-mutated
generated C++.

### 6.5 Comparer

Program-specific exact comparer in `tests/test_generated_kernels.cpp`: validate
width and height **before** lane count; require both arrays to hold exactly
`width*height*4` elements; compare every float by exact 32-bit word including
signed zero and NaN payload; compare every RGBA8 byte; report the first mismatch
with top-down x/y, channel, expected/actual words and bytes. Self-tests for
dimension mismatch, ±0, differing NaN payloads, word-only and byte-only
mismatch, short/long arrays. Every alpha word exactly `0x3f800000` and every
RGBA8 alpha byte exactly `255`, in every case and route (measured to hold). No
tolerance, no hash-only, no RGBA8-only substitution.

---

## 7. Test and mutation matrix

### 7.1 Python / frontend, RED then GREEN

1. Freeze a preflight asserting `synth/shape:shape` is absent, is corpus ordinal
   208, has the exact source/defines/resources of §1, rejects first with
   `exact scalar uint XOR profile carrier required`, and with the XOR carrier
   supplied rejects at normalized `31:1` with `unsupported global declaration`.
   **Both rejections, not just the second** — the acceptance record for Shapes
   flagged that no closure in this codebase locks its carrier-guard messages, and
   this slice should stop matching that convention.
2. Failing exact tests for both declarations before any production wiring.
3. Prove the profile authenticates both declarations only with the exact
   source/defines and coexists with the XOR carrier.
4. Missing / wrong / foreign / partial carrier combinations at **both**
   boundaries, each asserting its specific guard message.
5. Assert the capability tuple remains exactly 44 and the type tuple unchanged.
6. For every mutation whose purpose is local structural logic, refreeze **only
   the coarse hash fields** to the mutant, assert the coarse message did **not**
   fire, and assert the intended local message did. Refreezing semantic fields is
   vacuity #2 from the Shapes taxonomy; do not use a wholesale refreeze helper.
7. Order value-level checks **ahead of** node-identity checks, per the `Symbol`
   trap: `Symbol` embeds its declaration span, so a value mutation shifts the
   containing node's hash and self-absorbs.

### 7.2 The mutation matrix, and non-vacuity by deletion

Adopt as standard: **prove a check load-bearing by DELETING THE CHECK**, in a
scratch copy of `tools/` and `tests/` outside the repository, one predicate at a
time, recording which tests go red and with which message. Mutating the input
proves only that the module rejected something; deleting the check proves *which*
check rejected it.

| # | Lock the profile must carry | Deletion test — what must go RED, with that lock's own message |
| --: | --- | --- |
| 1 | source path / raw bytes / raw SHA | source-drift test |
| 2 | normalized bytes / SHA | normalized-drift test |
| 3 | functions / whole-program / interface SHA | each of three coarse-drift tests |
| 4 | exact defines `(LOOP_A_OFFSET,int,40)`, `(LOOP_B_OFFSET,int,30)` | per-define value, name, and order tests |
| 5 | declaration count 15 and full declaration inventory | inventory test (an added or removed global) |
| 6 | resource tuple (10 uniforms, 0 samplers, 1 output, no texture, no derivatives) | resource-drift test |
| 7 | `aspectRatio` identity: id, name, `float`, storage `global`, **initializer is None**, span `31:1-31:19`, node hash | one test per field |
| 8 | `globalCoord` identity: id, name, `vec2`, storage `global`, initializer None, span `32:1-32:18`, node hash | one test per field |
| 9 | **declaration ordinal and adjacency** (the two are `program.declarations[13]`, `[14]`, immediately after `const float TAU`) | reorder test |
| 10 | **write census is exactly two**, owners both `main`, operators both `=`, spans `459:5-459:47` / `461:5-461:54` | a synthetic third write must fail here, not at a coarse hash |
| 11 | **write statement indices in `main.body` are 1 and 3, both top-level, neither nested** | move-the-write-into-an-`if` test |
| 12 | **no `call` node in `main.body[0..3]`** — the dominance premise | insert a helper call before index 3 |
| 13 | **read census is exactly seven**, with owner and span per row (§3.2) | add/remove/move a read |
| 14 | **no helper writes either symbol** | plant a write in `circles` |
| 15 | field type mapping: `aspectRatio` → `double`, `globalCoord` → `glsl::Vec2` | change the mapping |
| 16 | frame instance is value-initialised in `pixel` before the first statement | delete the initialiser |
| 17 | helper parameter is `const Frame&`, not `Frame&` | relax it |
| 18 | call-graph digest and full reachability tuple | a dead/unreachable owner substitution |
| 19 | foreign key rejection | apply the profile to another program |
| 20 | companion-carrier exactness (XOR present and exact; every other profile absent) | drop or swap the XOR carrier |
| 21 | visitation ledger: every authenticated node consumed exactly once, in both authorities | sabotage each visitation check |

Tabulate one row per predicate. A predicate whose deletion leaves the suite
green is decoration. A test that goes red with the *wrong* message is testing a
different lock than its name claims — that was vacuity #3 in the Shapes slice,
and it hid an ancestry lock whose message appeared in no test at all.

### 7.3 The census must walk global declaration initializers

Per the standing trap: modules that advertise a "whole-program" census
(`linear_srgb_lane_index_profile.py`,
`shapes_float_bits_ingress_profile.py`, and the
`scanline_error_float_bits_ingress_profile.py` precedent all three inherit from)
walk `program.functions` → `function.body` only, so a node planted in a global
declaration initializer escapes into coarse-hash-only coverage. Three separate
instances of that gap were found in the last slice.

For this mechanism the answer is **emphatically yes, walk them** — the entire
subject matter is global declarations. Specifically:

- the census must enumerate **all 15 declarations**, not only the two admitted
  ones, so an added global anywhere is a hard failure;
- it must assert `initializer is None` on both admitted declarations, which is
  the *defining* property of the sub-shape and the thing that separates it from
  every existing const admission;
- it must walk any initializer that *is* present on the other 13 (the two
  `const float`s), so a node planted in `PI`'s or `TAU`'s initializer is caught
  by the census rather than by a refreezable coarse hash.

`shapes_rvalue_assign_profile.py` already walks global initializers and does not
inherit the gap; use it, not the ingress modules, as the structural template for
the walker.

### 7.4 What `fixed_nine_table_proof.py` does and does not give you

Read it first as a structural precedent, then discard most of it.

**What it gives:** the shape of a positional structural proof — a per-key
`_PROFILES` table; typed-IR and whole-program fingerprint gates
(`_TYPED_IR_LOCKS`, `_WHOLE_PROGRAM_LOCKS`) checked before anything else; a
named host function per key; exact `body` indices for the declaration and its
stores; a complete reference count (`all_references`) so a stray read anywhere
in the host fails; and the `"double" if element == "float"` element-type mapping,
which independently corroborates §4(c).

**What it does not give:**

- Its capability is `fixed-nine-local-literal-init-counted-read-v1` over
  `filter/sharpen`, `filter/sobel`, `filter/lighting` — a **local**,
  **literal-initialised**, **counted-read** `float[9]`. Every one of those three
  adjectives is false here: the declarations are **global**, **uninitialised**,
  and read by plain reference, not by an induction-indexed read.
- It is **capability-bearing** (it holds a token in the frozen 44). This
  mechanism must not be; it is node-identity admission with no `used.add`.
- It **refuses any program with preprocessor defines** outright
  (`if key not in _PROFILES or defines: return None`). `synth/shape` has two.
- Its proof is anchored on a loop (`loop_proof`, trip count 9, one
  induction-indexed read per table). `synth/shape` has **no loops at all**.
- Its stores are nine consecutive statements at fixed indices; here there are two
  writes at `main.body[1]` and `[3]`, separated by a declaration.

It is a template for *census and positional rigour*, not a carrier you can add a
key to.

### 7.5 Generated artifacts and historical reconstruction

1. Insert only the one sorted row. Update the exact schema/profile censuses and
   expected defines.
2. Generate only through
   `PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_typed_slice.py --write`.
   Never hand-edit generated C++, manifest, or header.
3. Require the projected 184-key SHA
   `026637ff3fec7a9282d4dea84af058acd95612a9f86afff59294062f7f639aec`, the exact
   `polygon / sacredGeometry / shape / solid / subdivide` neighbourhood, 184
   unique rows, 186 catalog entries, 27 genuinely unported, XOR carriers 4,
   frame carriers 1, and 27 rows with non-empty `defines`.
4. Assert the manifest row carries both profile names, exact defines, factory
   `bind_synth_shape_shape`, source hash, and the default-only define contract.
5. Assert catalog size 186 and that `synth/shape` occurs exactly once between
   `synth/sacredGeometry` and `synth/solid`, with the named and catalog binders
   pointing at the same factory.
6. Historical 184 → 183 reconstruction: deep-copy the live spec, remove only the
   new row, generate in memory, require the exact four pre-change hashes of §1.4,
   and compare every surviving emitted block after replacing only `typed_N`
   ordinals with a sentinel. The block-set difference must be exactly
   `synth/shape`. **This is also the test that proves the `frame`
   reserved-identifier addition is a no-op** (§5.6). Classify each older
   milestone assertion; never bulk-rewrite historical data.

### 7.6 Native parity, ABI, immutability

1. Run every oracle case through `generated::bind("synth/shape:shape", bindings)`,
   through `bind_synth_shape_shape(bindings)`, and through a second public repeat
   render from independent bindings.
2. Compare all three to the full exact oracle and to each other; assert
   independent output storage, deterministic repetition, finite-lane counts,
   alpha behaviour, expected RGBA8.
3. No sampler → immutability is executable **binding-state** proof: snapshot all
   ten getter-visible values through their production getter/type (`int32`,
   `bool`, `number`, `Vec2`) and the raw f32 words of each caller-owned `Vec2`
   lane array; compare exactly after all three passes. Do not claim
   input-surface immutability for a generator with no sampler.
4. ABI-test all ten uniforms through both binders: omit each once, supply the
   wrong variant type once, require `KernelBindingError` naming the binding.
   Lock `seed` as `int32`, `wrap` as `bool`,
   `resolution`/`tileOffset`/`fullResolution` as `Vec2`, the rest through
   `get_number`. **Include `resolution`, which the program never reads.** Confirm
   the two compile-time defines are not runtime bindings, and that unrelated
   extra uniform/texture entries are ignored and behaviour-neutral.

---

## 8. Likely owned file scope

Production / profile owner:

- Create `tools/glslcpp/frontend/mutable_global_frame_profile.py`.
- Modify `tools/glslcpp/generate_typed_slice.py`.
- Modify `tools/glslcpp/emit_typed_cpp.py`.
- Modify `tools/glslcpp/typed_slice.json`.
- Generated only: `src/typed_generated/typed_slice.cpp`,
  `src/typed_generated/typed_manifest.json`,
  `include/noisemaker/generated/catalog.hpp`.

Python-test owner:

- New focused `tests/test_mutable_global_frame.py` for the profile proof and the
  §7.2 deletion matrix.
- Modify `tests/test_typed_generator.py` for integration, counts, hashes,
  reconstruction, cross-profile composition, and the emitter-boundary regression
  lock.

Oracle / native owner:

- Sole owner of the five §6 artifacts and their sidecars.
- Modify `tests/test_generated_kernels.cpp` for the comparer, public/direct/repeat
  parity, ABI, binding immutability, alpha, and the mutation ledger.

Do not edit the corpus, runtime math/types, `Surface`/sampler, CMake, README,
unrelated profiles, existing expected fixtures, or generated files by hand.
Expand scope only on a reproduced blocker, and update this design first.

---

## 9. Verification and native-code gates

Run only after §10 is active. Every Python command uses both
`PYTHONDONTWRITEBYTECODE=1` and `python3 -B`.

1. Schema checks assert 184 unique rows, 186 catalog entries, 27 unported,
   carrier counts 4/1, 27 rows with non-empty defines, key-list SHA
   `026637ff3fec7a9282d4dea84af058acd95612a9f86afff59294062f7f639aec`, and the
   exact five-key neighbourhood.
2. `check_corpus.py --check`.
3. `check_semantics.py --check` (212 programs).
4. `node shape184_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"`, then
   `generate_shape_native_oracle_include.py --check`; require imports confined
   beneath the immutable snapshot, all sidecars, public identity, external and
   axis controls, full arrays, alpha, crop translation, and the mutant ledger.
5. `generate_kernels.py --check`.
6. `generate_typed_slice.py --check` (184 programs).
7. Focused profile/oracle/reconstruction tests, then
   `python3 -B -m unittest discover -s tests -p 'test_*.py' -q`.
   **Expect one failure if the suite runs from a relocated copy** —
   `test_emboss_color_style … test_oracle_include_and_frontend_probe_no_write_checks`
   resolves the JS reference as a sibling of the repository root. Verify that
   single test against the live tree before calling it a copy-path artifact, and
   report the split honestly. Never dismiss a copy-run failure without running it
   live.
8. Fresh `$RUN_ROOT/Debug` configure/build, direct binary, CTest 1/1.
9. Fresh `$RUN_ROOT/Release` likewise.
10. Fresh `$RUN_ROOT/sanitizer` ASan+UBSan likewise, with
    `UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1`; on Apple
    `ASAN_OPTIONS=detect_leaks=0`, and therefore **make no LeakSanitizer claim**.
11. Confirm `-Werror` and `-ffp-contract=off` in all three builds by reading
    `flags.make`, not the CMake invocation.

Assembly audit, native ARM64 and x86_64 cross, on the final exact source.
Resolve symbols after generation rather than assuming spelling; inspect at
minimum `typed_181::pixel`, `typed_181::offset`, `typed_181::shape`,
`typed_181::map`, `typed_181::periodicFunction`,
`typed_181::randomFromLatticeWithOffset`, and the binder. Pixel/helper scope: no
indirect `br`/`blr` or indirect `jmp`/`call`, no fused FP, no heap, no
exception/unwind path, no virtual/callback dispatch, no string/container work,
no dynamic stack. Direct helper calls are allowed; binder-only `shared_ptr`
teardown is the permitted carve-out.

**Two things to expect rather than investigate afresh:**

- `typed_181::value` almost certainly compiles to a real jump table, exactly as
  `typed_8::value` does in Shapes (same 9-way `interp` dispatch). It should stay
  out of pixel scope **only because the defines are frozen at 40/30** — `pixel`
  reaches `value` solely through `offset`'s `300..380` arm, which 40/30 does not
  select. **Record the gate result as conditional and name the precondition.**
  Any future work admitting alternate `LOOP_A_OFFSET`/`LOOP_B_OFFSET` values must
  re-run this gate and should expect to need a source-authenticated bounded
  dispatch shape. *(Inference from Shapes183 §13, not measured here — no build
  was run.)*
- `glsl::Vec<N,T>::Vec(const FloatExpr<N>&)` at `glsl_types.hpp:164` is not
  `noexcept`, so functions constructing a `Vec` from a `FloatExpr` carry an LSDA
  and a `___clang_call_terminate` pad. It affects 51 functions in the translation
  unit and is not this slice's to fix. Recognise it; do not investigate it.
- `pow`/`atan2` route to platform libm while `sin`/`cos` route to the
  repository's `fdlibm`. Generator-wide, intended, bit-exact. Do not "fix".

---

## 10. Storage and cleanup gate

Unchanged from Shapes183 §10 in substance; restated with this slice's prefix.

- Exactly one external root:
  `RUN_ROOT="$(mktemp -d /private/tmp/noisemaker-shape184.XXXXXX)"`, immediately
  validated against that exact prefix. Explicit `Debug`, `Release`, `sanitizer`,
  `reconstruction`, `assembly`, `oracle` lane directories.
- Before any Python/Node/build command, export `TMPDIR`/`TMP`/`TEMP`,
  `XDG_CACHE_HOME`, `PYTHONPYCACHEPREFIX` into the root and set
  `PYTHONDONTWRITEBYTECODE=1`; every Python invocation spelled `python3 -B`.
- Define the retained-product allowlist before execution. Write
  `repository-full.before.tsv` (path, kind, size, SHA-256, link target; dotfiles
  and pre-existing artifacts included; bytewise sorted) and
  `repository-transients.before.tsv`. Regenerate both after every lane; require
  byte-for-byte identity outside the allowlist and zero new transients.
- Keep every canonical/control array once, in `shape184-oracles.json`.
- **Do not delete the run root until every dispatched review has reported.** The
  Shapes slice deleted it while an integration review was still running, which
  cost a real finding and nearly destroyed the reviewer's evidence. List live
  agents first. "Evidence summarized" means *all* evidence, including evidence
  not yet produced.

---

## 11. The array form: what would have to change

`float emboss[9];` and its siblings are byte-identical across `cellRefract`,
`effects`, and `kaleido`. The mechanism above is deliberately shaped so the array
form is an extension, but it is **not a free one**. Verified by probe, in order:

1. **Global array *type* admission.** With mutable-global storage admitted, all
   three fail immediately at `unsupported typed type float[9]`. `reject_type`
   admits array types only via `proved_array_declarations` (local declarations
   from `fixed_nine_table_proof`) or `proved_array_parameters`. A global array
   needs its own registration path.
2. **The writer is not `main`.** In `cellRefract` the 45 literal stores live in
   `void loadKernels()`, which `main` calls. So the `const Frame&` helper
   parameter of §5.5 must relax to a non-const `Frame&` **for the array
   carriers**, and with it goes the compiler-level enforcement of the
   single-writer lock. The profile must then carry the dominance proof
   explicitly, and that proof is harder: it must show `loadKernels()` is called
   unconditionally from `main` before any read, rather than reading off
   statement indices in one function.
3. **Passing a global array as an argument.** `convolve(localUV, emboss, false)`
   needs the array to be admitted as a call argument
   (`proved_array_arguments`), and the callee's `float kernel[9]` parameter needs
   `fixed-array-in-parameter-v1`, whose key set is frozen. Probed next blocker
   after global-array type admission, for `cellRefract` and `kaleido`:
   `unsupported typed type float[9] [STORAGE=parameter]` at `66:29` and `543:24`
   respectively.
4. **`effects` is worse than the other two.** Its next blocker after global-array
   type admission is `unsupported typed type mat4` at `395:10` — a type currently
   supported only for `classicNoisedeck/glitch` through
   `glitch_mat4_chain_profile`. Do not plan `effects` alongside `cellRefract` and
   `kaleido`.
5. **Materialization must be re-read, not assumed.** Do not carry §4's findings
   across. Read each array program's `canonicalFactory` and confirm whether the
   nine elements land in a `Float32Array` (f32 lanes) or a plain array
   (doubles) before choosing `std::array<double,9>` versus
   `std::array<float,9>`. `fixed_nine_table_proof` maps `float` elements to
   `double`, which is evidence but not proof for a different program.

The honest summary: `synth/shape` and `synth/noise` share the reduced form and
this mechanism lands both (`noise` after its counted-for blocker). `cellRefract`
and `kaleido` need three further mechanisms on top. `effects` needs four.

---

## 12. Confidence register, and what could not be verified

**High — measured directly during this task, reproducible from the commands in
this document:**

- §1 every hash, byte count, ordinal, count projection, and the 184-key digest.
- §1.5 factory name, `toString` digest, non-adapter status, the six CPU hashes.
- §2 both rejections, both declarations, the five-program corpus census, and
  §2.4/§2.5 — that the validator closure is exactly the two global gates and the
  emitter closure is exactly admission plus symbol mapping.
- §3 the complete write and read censuses and the dominance argument.
- §4 the JS materialization, including that `beginPixel` does not reset closure
  vars, and §4.1/§4.2's discrimination and liveness tables, all measured by
  running the real factory and two source-level mutants.
- §5.6 the corpus census for the identifier `frame`.
- §11 items 1, 3, and 4, each a probed rejection.

**Medium — reasoned from code that was read but not executed:**

- §5.5's emitted shape. The probe emitted `frame.<name>` references and the
  emitter completed, so the *expression* lowering is verified; the `struct Frame`
  declaration, the `pixel`-scope instance, the helper parameter, and the
  `const`-ness were **not** emitted or compiled. No C++ was built during this
  task.
- §5.4's wiring list. Derived by reading the four existing carriers' wiring, not
  by writing it. In particular, whether the `scalar_uint_xor_profile` guard block
  needs editing to tolerate a new companion is *believed* to be no (its collision
  list is short) but was not proved.
- §9's expectation that `typed_181::value` contains a jump table folded away at
  40/30. Inferred from Shapes183 §13 on a structurally identical dispatch; no
  assembly was produced.

**Could not be determined:**

- **Whether `shape-extreme-tile-offset` is expressible end-to-end in the C++
  harness.** The measurement in §4.1 was made in the JS reference. Whether
  `glsl::PixelContext::frag_coord` plus a `tileOffset` of `[131072.1, 0.3]`
  survives the C++ binding path and the comparer without a non-finite lane was
  not tested. If it does not, the `globalCoord` f32-lane contract has **no oracle
  witness** and becomes a structural-authentication-only claim boundary in the
  §4(d) sense — which must then be stated in the oracle JSON's
  `claim_boundaries`, not left implicit.
- **Whether the emitted `const Frame&` parameter perturbs the assembly gate.** It
  should not (a reference is a pointer, calls stay direct), but nothing was
  compiled.
- **The exact per-case f32/RGBA8 arrays.** This document deliberately records
  only discrimination *outcomes*, because the fixture is the oracle owner's
  deliverable and generating arrays here would create a second, unowned copy.
- **Whether `synth/noise:noise` needs anything beyond this mechanism** once its
  counted-for blocker is resolved. Only its first blocker was probed.

**Deliberately not asserted:**

- No claim that a full-surface render executes the three scalar XOR sites, the
  `randomFromLatticeWithOffset` body, or the `circles`/`rings`/`diamonds`
  branches. All are dynamically dead at 40/30.
- No claim about `wrap` liveness in general — it is live only where `lf` is
  non-integral, and §6.2 assigns exactly one case to that axis.

---

## 13. Stop conditions

Stop and redesign rather than widening if any of these occurs:

- the source hashes, defines, ordinal, or the 184-key digest no longer match §1;
- `synth/shape` needs any capability beyond the one new closure plus the existing
  scalar-XOR carrier — in particular, if the emitter demands a new expression
  arm, that contradicts §2.5 and the closure was mis-scoped;
- write-before-read (§3.3) cannot be locked as a structural predicate — a
  mechanism that admits mutable globals without proving dominance is unsafe at
  any size;
- the JS materialization of either global differs from §4 when re-read from the
  pinned snapshot;
- a measured discrimination outcome in §4.1 or an axis result in §4.2 fails to
  reproduce in the oracle generator;
- the oracle factory or source provenance cannot be authenticated, or an import
  resolves outside the immutable CPU snapshot;
- exact f32 parity fails and a tolerance is proposed;
- any profile mutation reaches only a coarse hash, or any deleted predicate in
  §7.2 leaves the suite green;
- the 184 → 183 reconstruction changes any surviving normalized emitted block —
  including as a side effect of adding `frame` to `_RESERVED_IDENTIFIERS`;
- sanitizer or assembly gates reveal a pixel-path allocation, indirect dispatch,
  fused FP, UB, or unbounded/dynamic stack behaviour.

Completion means: the 184-key generated state, exact full-surface parity on all
eight cases plus controls, one new profile closure plus the reused scalar-XOR
carrier, historical reconstruction exact, full Python/Debug/Release/sanitizer
gates green, a native assembly GO recorded **with its define precondition
named**, every dispatched review reported and its Critical/Important findings
addressed, and a clean storage audit — all agreeing.

---

## Amendment 1 — two adapter tables, not one; and the tile-offset question is settled

Added 2026-08-16 by the integration owner from the oracle worker's findings.
Sections above are the originally written design; this overrides them where
stated.

**§1.5 conflates two different adapter tables.** They are not the same and do
not have the same contents:

- `check_corpus._ADAPTERS` has **four** keys —
  `{classicNoisedeck/fractal:fractal, filter/historicPalette:historicPalette,
  filter/palette:palette, synth/julia:julia}`. This is the corpus-level
  eligibility allowlist.
- `canonicalAdapterFactories` in the shipped JS has **eleven** keys. This is the
  runtime routing table.

An oracle must pin **both** by census — confirming the target key is absent from
each — because absence from one implies nothing about the other. The oracle
package now does. Anyone reusing §1.5 as a template should carry both checks.

**The extreme-tile-offset bindability question is RESOLVED: it binds.** §12
listed this as unverified, with the consequence that the `globalCoord` f32-lane
contract might have no oracle witness and become a structural-only claim
boundary. It does not. Probed against the real headers and sources outside the
repository: `tileOffset = [131072.1, 0.3]` round-trips through
`get<glsl::Vec2>` as `0x48000006` / `0x3e99999a` with no clamping, and
`swizzle<0,1>(frag_coord) + tileOffset` produces 384 lane words across all 192
pixels that are **bit-identical** to the JS reference, with zero non-finite
lanes on either side.

Those 384 words are shipped as `globalcoord_native_binding_witness` /
`kGlobalCoordWitnessWords`, so the native phase can prove the binding path
**before the kernel exists** — the contract has a real witness, not a boundary.

**Three deviations from the design's oracle plan, each deliberate and
re-measured rather than inherited:**

1. Three cases are realised at smaller equal-ratio dimensions (64×36 → 16×9,
   48² → 12², 36×64 → 9×16). The control group multiplies the anchor's area by
   five and the design's sizes produced a ~6 MB JSON. Discrimination was
   **re-measured** at the new sizes, never carried over.
2. The crop-translation *proof* moved to `shape-wrap-live-37-61`, because a
   1280×720 full route is 3.7M lanes. `shape-crop-1280x720` keeps its exact
   design configuration and its offset rule is still checked; the gap is
   recorded as `full_route_stored: false` and guarded.
3. The two contracts are required to have **disjoint witness sets**. A shared
   witness could not attribute a divergence to one contract or the other, so
   sharing one is now a hard failure rather than an accident waiting to be
   misread.

---

## Amendment 2 — profile closure accepted; two items that bite the array form

Added 2026-08-16. The `mutable-global-frame-shape-v1` closure is accepted:
75 tests, **29/29 predicates proven load-bearing by source-level deletion**,
capability tuple 44 and type tuple 17 unchanged, and
`generate_typed_slice.py` byte-identical to the `03b035c` baseline.

Two deferred items, both harmless today and both **specifically relevant when
§11's array form lands**, because that form makes a helper the writer and
relaxes `const Frame&` to `Frame&`:

1. **`out`/`inout` call arguments are a mutation path `_MUTATION_KINDS` does not
   model.** The IR shape exists — the repo already has an
   `inout_vec3_swap_profile`. It is not an escape today: such a reference lands
   in the read bucket and trips read cardinality 7→8. But the message would name
   the wrong lock, which is precisely the failure mode
   `_no_indirect_write_holds` was added to prevent. Model it before the array
   form, not after.
2. **`_fail()` prefixes every message with the module-level `SHAPE_PROFILE`.**
   Once `mutable-global-frame-noise-v1` is added for `synth/noise:noise`, that
   program's failures will be labelled with Shape's profile name. This is the
   same multi-key coupling that was removed from the admitted-symbol map,
   surviving in the one place it was not looked for.

Also recorded so a later sweep is not misled: the implementer's deletion table
mixes two harness semantics. Under **source-level deletion** (what the `_scratch`
docstring commits to) the counts are `_write_position_holds` 2,
`_no_indirect_write_holds` 4, `_dominance_holds` **1**; under attribute-rebind,
`_dominance_holds` reads 2 because the stand-in's `(*a, **k)` signature also reds
the symbol-map test. Every row is load-bearing under both semantics — only the
counts differ. **Declare which harness produced a table when you write one.**

---

## Amendment 3 — sanitizer and assembly: GO, and the Frame contract proved at instruction level

Added 2026-08-16 from the independent verifier's report.

**Sanitizer.** 250 PASS / 0 FAIL on the direct binary, CTest 1/1, **zero ASan
and zero UBSan diagnostics**. `-Werror` and `-ffp-contract=off` confirmed on the
actual compile line via `flags.make`. On Apple `detect_leaks=0` means
LeakSanitizer did not run — **no leak claim is made in either direction**.
`DEFECTS-FOUND.md` item 4 did **not** reproduce; nothing appeared, so there was
nothing to confirm as the same diagnostic. It is not claimed fixed and keeps no
resolution marker.

**Assembly, ARM64 and x86_64.** Pixel scope is `{pixel, shape}` on both arches;
`map`, `offset` and `periodicFunction` inline into `pixel` and were audited
there. Both are clean on every axis — zero indirect branches, zero fused FP, no
heap, no exception path or LSDA, no string or container work, no dynamic stack,
no jump table. Fused FP is zero across the **entire translation unit** on both
arches, which is the independent witness that `-ffp-contract=off` took effect.
The binder's indirect calls were authenticated instruction by instruction:
refcount decrement → vptr → vtable slot 16 → `blr x8` / `callq *16(%rax)`,
libc++ `shared_ptr` teardown, binder-only. Unlike the previous program, no LSDA
or `___clang_call_terminate` appears anywhere in this program's pixel scope.

**The Frame contract holds, and the proof is stronger than a parity test could
give.** The struct is stack-only, 16 B at a fixed offset inside `pixel`'s
constant frame, passed by address; no heap, no dynamic stack, and no
static/global storage emitted for either former global. The two fields keep
genuinely different numeric treatment: `aspectRatio` is produced by
`fdiv`/`divsd` in double, stored and read back 64-bit into double arithmetic;
`globalCoord` is rounded per lane and stored as two 32-bit lanes.

Decisively: `pixel` and `shape` contain **zero hardware narrowing
instructions**. All narrowing routes through the enumerable `f32()` helper — 22
calls in `pixel`, 7 in `shape`, identical on both arches — and `aspectRatio`
passes through none of them. There is nothing for the
`shape-aspect-f32-narrowed` mutant to catch, established at the instruction
level rather than inferred from output equality.

**Jump table — present, contained, and CONDITIONAL, exactly as in
`shapes183-design.md` §13.** `typed_181::value` does compile to a real jump
table on both arches. At defines 40/30 clang inlines `offset` into `pixel` and
constant-folds the dispatch away — `pixel` contains no `300..380` range test at
all, a stronger witness than the previous program's. **Containment is a property
of the frozen defines, not of the code.** Any future define variant for this
program must re-run the assembly gate and should expect to need a
source-authenticated bounded dispatch shape.
