# Defects surfaced by the C++ port

Bit-exact porting compares output bit patterns against the real JavaScript
reference, which finds classes of bug that a build, a passing test suite, and
even a sanitizer lane all miss. These are the live ones found so far.

Each entry states **who verified it**, because that matters for how much weight
to put on it.

---

## 1. `filter/dither` error-diffusion path crashes unconditionally

**Repo:** `noisemaker-for-cpu` (public) · **Severity:** live crash, user-reachable
· **Verified:** independently reproduced by the port author

`src/effects/generated/canonical-kernels.js:11071-11073`:

```js
var errRow = [];
for (var i = 0; i < FS_ERR_W; i++) {
  fsSeedNoise(blockOrigin, i).map(function (_) {return _ * stepScale;})
    .reduce((res,el,i)=>(res[i] = el, res), errRow[i]);
};
```

`errRow` is empty, so `errRow[i]` is `undefined` on the first iteration.
`.reduce(fn, undefined)` then runs `res[i] = el` against `undefined`:

```
TypeError: Cannot set properties of undefined (setting '0')
```

Throws on i=0 for **every canvas size and every uniform combination**. The
intent was evidently `errRow[i] = fsSeedNoise(...).map(...)`.

**Reachability:** only at `ditherType == DITHER_ERROR_DIFFUSION` (`= 7`,
`dither.glsl:32,579`). The parity golden
`parity/goldens/defaults/filter__dither.graph.json` pins `ditherType: 1`, so no
test exercises the broken path — which is why it has gone unnoticed.

**Scope:** the GPU path runs real GLSL and is unaffected. Only the transpiled JS
CPU renderer breaks.

**Consequence for the port:** `filter/dither`'s error-diffusion path cannot be
ported bit-exactly, because there is no working reference behaviour to match.

---

## 2. `filter/median`'s canonical factory crashes at 5x5

**Repo:** `noisemaker-for-cpu` (public) · **Severity:** live crash, size-dependent
· **Verified:** by the oracle agent, **not** independently reproduced by the port author

`canonicalFactory80` throws a `TypeError` inside `$runtime.copy` on a plain 5x5
render, while 4x4 and 6x6 render fine. Independent of the loop-proof gate.

The median oracle therefore targets `medianFactory` (the working adapter twin)
instead — the same precedent the wormhole oracle set.

---

## 3. `classicNoisedeck/fractal` — shipped adapter diverges from its own GLSL

**Repo:** `noisemaker-for-cpu` (public) · **Severity:** correctness discrepancy,
not a crash · **Verified:** by the oracle agent

`fractal` has **no canonical factory at all** (`generatedBytes: 0`, permanent
adapter-only routing), and the adapter implements a **different**
julia/newton/mandelbrot algorithm than the corpus GLSL source it nominally
corresponds to.

So the GLSL is not the behaviour. Either the GLSL is stale and should be
retired, or the adapter has drifted from it — worth deciding deliberately,
because right now the repository contains two disagreeing definitions of the
same effect.

Same structural class as `filter/wormhole:deposit`, where the fragment kernel
exists and is transpiled but the renderer never executes it.

---

## 4. Signed overflow in shipped `synth/bitwise` code

**Repo:** `noisemaker-for-cpp` (this port) · **Severity:** undefined behaviour
· **Verified:** by the ASan/UBSan lane, 174/174 otherwise green

The sanitizer lane reports a signed-overflow diagnostic in already-shipped
`synth/bitwise` code. Pre-existing and unrelated to the batch that found it;
documented rather than rushed. **This one is ours to fix.**

---

## 5. Early `return;` in `main()` writes black — the port does not model JS's persistent `fragColor`

**Repo:** `noisemaker-for-cpp` (this port) · **Severity:** silent parity
divergence (**not** undefined behaviour — see the correction below) ·
**Verified:** 2026-08-16, by reading the emitted C++ and the shipped JavaScript
runtime, and by compiling a probe against the real header. **This one is ours to
fix.**

Found while building the `filter/normalMap` oracle package. It is **not**
specific to normalMap.

In the shipped JavaScript, `fragColor` is a **factory-scope `Float32Array`**
that is *not* reset per pixel. A pixel whose `main()` takes an early `return;`
without assigning `fragColor` therefore emits the **previous pixel's colour**.

In the port, `src/pass_runner.cpp:96` and `:169` declare `glsl::Vec4 output;`
**inside** the per-pixel loop, and the emitted `pixel()` assigns it only on
paths that reach a `fragColor` write. On an early-return path the pixel is
stored **black** — `(0, 0, 0, 0)` — where JavaScript emits the previous pixel's
colour. Faithful behaviour requires `output` to **persist across pixels within
a pass**, mirroring the factory-scope `Float32Array`.

### Correction to the first draft of this item

This item originally claimed the read was **undefined behaviour**, reasoning
from `constexpr Vec() = default;` at `include/noisemaker/glsl_types.hpp:105`
that block-scope default-initialisation leaves the lanes indeterminate. **That
was wrong**, and it was wrong because the declaration one screen further down
was not read: `glsl_types.hpp:133` declares `std::array<T, N> lanes_{};`, a
default member initializer. The defaulted constructor therefore
value-initialises, and `Vec4` is not trivially default-constructible.

Confirmed by compiling a probe against the real header, mirroring
`pass_runner.cpp:96` exactly, under `-std=c++20 -Wall -Wextra -Wpedantic
-Werror -ffp-contract=off`:

```
i=0 -> 0 0 0 0
i=1 -> 0 0 0 0
i=2 -> 0 0 0 0
```

with `static_assert(!std::is_trivially_default_constructible_v<glsl::Vec4>)`
compiling clean. There is no uninitialised read and no memory-safety bug. The
divergence is real and unchanged; only its severity and its fix are different.
Do not go hunting a sanitizer diagnostic for this — there is none to find.

### Scope, measured rather than estimated

32 of the 212 corpus programs contain a bare `return;` in `main`; 27 of those
are now typed. Most are harmless — the GLSL writes `fragColor` immediately
before returning, and the emitter reproduces that. Scanning the 31 bare
`return;` statements in `src/typed_generated/typed_slice.cpp` for ones **not**
immediately preceded by an `output =` assignment gives exactly five, all in
shipped programs:

| block | program | guard |
| --- | --- | --- |
| `typed_32` | `filter/crt:crt` | `global_id.x >= width \|\| global_id.y >= height` |
| `typed_33` | `filter/degauss:degauss` | same shape |
| `typed_41` | `filter/fxaa:fxaa` | `>= width_u \|\| >= height_u` |
| `typed_50` | `filter/grain:grain` | `>= u_width \|\| >= u_height` |
| `typed_66` | `filter/normalMap:normalMap` | `>= width \|\| >= height` |

Counts refreshed 2026-08-16 after `filter/normalMap:normalMap` landed as typed
row 185; it is the fifth carrier, as predicted when this item was written.

### Why no test has caught it

All five guards compare a `frag_coord`-derived `global_id` against a
resolution-derived bound, and `pass_runner` drives `frag_coord` from the same
raster extent it allocated. The guard is therefore unreachable whenever the
`resolution`/`size` binding agrees with the raster — which is every path the
harness exercises. It becomes reachable the moment a caller binds a resolution
smaller than the surface, which is exactly the tiled/partial case the guard was
written for.

No sanitizer lane can report it: there is nothing memory-unsafe here, only a
value that disagrees with the authority. It is invisible to ASan and UBSan by
construction, and an MSan lane would not find it either. Only a parity test
that drives a resolution smaller than the surface would.

**Recorded, not fixed.** The fix is a runtime change to the output-persistence
model touching `pass_runner.cpp` and every kernel's output contract, which is
far outside the slice that found it.

---

## 6. The port copied vector locals that the JavaScript aliases — `filter/parallax` (row 190) shipped wrong

**Repo:** `noisemaker-for-cpp` (this port) · **Severity:** shipped parity
divergence, user-reachable · **Verified:** 2026-08-19, by a coordinate-level
trace of the JavaScript authority against the emitted kernel ·
**Status: FIXED 2026-08-19 for the local and parameter classes; the
binding-sourced class is still open (below).**

Row 190 landed at "focused level" with structural-only parity — no oracle
package, no native parity test. It was wrong, and the missing oracle is why
nothing caught it.

### The measurement

Rendering `filter/parallax:parallax` at 4x5 over an 11x9 input, `direction =
(-0.8, 0.4, 0.2)`, `pivot = 0`, both sides bound identically:

| | textureLod calls | pixels where the final `getInput` coord equals the last `getHeight` coord |
| --- | ---: | ---: |
| JavaScript authority | 309 | **20 / 20** |
| emitted `typed_80` | 309 | **0 / 20** |

Every one of the 309 march samples is bit-identical. Only the **last** call
of each pixel — `getInput(rayUV)` — differs, on all 20 pixels. Two of the 20
pixels land in a different texel and change colour outright.

### The mechanism

`parallax.glsl:65-72` refines between the two straddling march samples:

```glsl
vec2 prevUV = rayUV;
...
rayUV = uv + shift * (t - pivot);   // in-place in the JS materialization
...
float w = f / (f - prevF);
rayUV = mix(rayUV, prevUV, w);
```

In the shipped JavaScript (`canonicalFactory98`), `var prevUV = rayUV` binds
a **reference to the same `PooledFloat32Array`**, and the update is written
in place as `(rayUV[0] = ..., rayUV[1] = ..., rayUV)`. So `prevUV` tracks
`rayUV`, `mix(rayUV, prevUV, w)` is `mix(x, x, w) == x`, and **the refinement
is a no-op**. `prevF = f` is a Number and IS a real copy, so `w` is computed
from the true previous `f` — it is just multiplied into a zero delta.

The emitter writes `glsl::Vec2 prevUV = rayUV;` — a value copy — so the port
actually performs the interpolation the GLSL describes.

This is the failure mode this project has recorded more often than any other:
**the parity target is the transpiler's materialization, not GLSL semantics.**
The refinement is dead code in the authority and live code in the port.

### Blast radius — the first census was an undercount

The first scan of the shipped canonical factories looked only for sources
declared as `new $runtime.PooledFloat32Array`, and reported nine typed rows.
**That was wrong**, and it was wrong because a vector local can also alias a
function parameter (parameters are `$runtime.copy`-ed at entry, so the
parameter itself is a pooled array) or a `$bindings[...]` read. Re-scanning
with all three source kinds gives **23 alias-then-mutate sites across 18
factories, of which 13 are typed rows**:

| source kind | sites | typed programs |
| --- | ---: | --- |
| pooled local | 13 | `bitEffects`\*, `effects`, `noise3d`\*, `flipMirror`, `lowPoly`, `parallax`, `repeat`, `skew`, `spinBlur`, `gradient`, `subdivide`, `flythrough3d`\* |
| parameter | 8 | `crt`, `grade:hslSecondary`, `feedback`\*, `fractal3d`\* |
| **binding** | 2 | `osc2d`, `perlin` |

\* not a typed row.

The emitter's own IR-level analysis is stricter than that text scan — it also
catches swizzle-target writes such as `st[0] *= aspect` — and it converted
**28 declarations** to references.

### Fixed 2026-08-19, for the local and parameter classes

`emit_typed_cpp.py` now models the alias: a `vec2`/`vec3`/`vec4` declaration
whose initializer is a bare vector identifier emits `TYPE& name = source;`
when a write to either name makes the aliasing observable. Where neither name
is written, a copy and an alias are indistinguishable and the emission is
unchanged, which keeps the artifact churn to the 28 sites that matter. The
analysis is re-derived from the live program on every run, never frozen.

Evidence: `typed_slice.cpp` grew by exactly 28 bytes (the ampersands); the
slice spec and `catalog.hpp` are byte-identical. The whole native suite stays
green, which is the load-bearing check — every program with oracle coverage
still matches the authority. `filter/parallax` is now bit-exact on all nine
differential cases, including `tile-clamped`, which had 42 of 64 lanes wrong.
Row 190 has an oracle package (`counted-for-parity/parallax190_oracle_generator.mjs`)
whose `refinement-copy-restored` mutant reproduces the old emission exactly
and is witnessed by 3 of 6 cases, so a regression cannot land silently again.

### What the fix cost: 42 frozen historical pins were re-derived

Recorded loudly, because these are the project's strongest integrity anchors
and a future reader must be able to tell a legitimate re-derivation from a
weakened one.

The historical-reconstruction tests rebuild a past milestone state by
regenerating it **with the live emitter**. Correcting the emitter therefore
changes the bytes of every reconstructed state that contains an aliased
program, and the pinned digests move with it. Re-derived: 12 digests across six milestone states (`scanline177`,
`glyph178`, `edge179`, `glitch180`, `emboss181`, `live182`) shared by four
modules; 27 digests and 8 reconstructed-artifact byte counts inside
`test_typed_generator`; 3 block-concatenation hashes in the task35 module;
and 5 live-artifact pins. Each reconstructed state grew by exactly the number
of ampersands its programs gained, which is why the byte counts moved in
lockstep with the digests.

Why this is a re-derivation and not a weakening:

- **Nothing about the mechanism changed.** Each test still deep-copies the
  live spec, removes rows, regenerates in memory and compares against a
  pinned digest. No check was deleted, no comparison loosened, no tolerance
  introduced.
- **The structural invariants still pass.** Each of those tests also asserts
  the surviving block set and byte-identity after `typed_N` normalization,
  and those assertions were green throughout — only the digests moved.
- **Every state reconstructed to the same new digest from every module that
  reconstructs it.** `edge179` is pinned in three separate modules and all
  three produced the identical new value; `glyph178` in four. Independent
  agreement across modules is the cross-check that the new values are the
  reconstruction's output and not a transcription.

Two tests build an `_Emitter` by hand rather than through `__post_init__`
(`test_task23_rejected_structural_mutations…`,
`test_task24_rejected_round_and_loop_mutations…`). They set the mutation
census manually and so had to be taught the alias census too — the two
`AttributeError`s that surfaced were that gap, not a defect in the emission.

### Still open: the binding-sourced class

`synth/osc2d` and `synth/perlin` both do `var res = fullResolution;` and then
write `res` in place, which in the authority writes **into the binding array**
and persists for the rest of the pass. The port cannot express that through a
`const State&` field, so the emitter deliberately skips this class and the
copy behaviour is unchanged for those two rows. Whether it is observable is
**not yet measured**: the guard fires only when `fullResolution[0] < 1`, which
`createCanonicalBindings` never produces by default, and even then both sides
may agree because every later read of `res` sees 1024 either way. What has NOT
been checked is whether those kernels read `fullResolution` directly elsewhere,
which is where the two would part. Measure that before deciding it is inert.

### The `synth/gradient` signal was real — it is item 7

The near-ULP `synth/gradient` differential recorded here as unconfirmed has
since been diagnosed and is a **separate defect**, not this mechanism: see
item 7. It is not fixed by the alias change, and the "near-ULP" description
was misleading — it is a small-angle algebraic difference, not rounding.

### Still open: the binding-sourced class

`synth/osc2d` and `synth/perlin` both do `var res = fullResolution;` and then
write `res` in place, which in the authority writes **into the binding array**
and persists for the rest of the pass. The port cannot express that through a
`const State&` field, so the emitter deliberately skips this class and the
copy behaviour is unchanged for those two rows. Whether it is observable is
**not yet measured**: the guard fires only when `fullResolution[0] < 1`, which
`createCanonicalBindings` never produces by default, and even then both sides
may agree because every later read of `res` sees 1024 either way. What has NOT
been checked is whether those kernels read `fullResolution` directly elsewhere,
which is where the two would part. Measure that before deciding it is inert.

### Open, unexplained, and NOT part of this mechanism

A **near-ULP** divergence on `synth/gradient:gradient` (89 of 120 lanes, e.g.
`0.739394` vs `0.739476`), which the alias fix does not change. Localized:
it needs **both** `rotation != 0` and `repeat != 0`, and is independent of
seed, time, speed and gradientType — so it lives in the rotation math
(`angle`, the `mat2(c,-s,s,c)` build, or `rotate2D`), not in the aliasing.
`synth/gradient` has no oracle coverage of any kind. Still an **unconfirmed
signal**: the same harness produced one false positive earlier (uniforms named
`tileOffset`/`fullResolution` are silently overwritten by
`createCanonicalBindings`, which spreads `...uniforms` first and then sets
those names itself — passing them at the wrong level made the JS render a full
route against the port's tile route).

---

## 7. `synth/gradient` is NOT bit-exact — a whole-vector assignment whose RHS reads a lane the JavaScript has already clobbered

**Repo:** `noisemaker-for-cpp` (this port) · **Severity:** shipped parity
divergence, user-reachable · **Verified:** 2026-08-19, by a mutant that
isolates the mechanism. **This one is ours to fix.** Distinct from item 6 —
the alias fix does not change it.

Item 6's fix made the *declaration* an alias. This is the other half: what
happens when you **write through** one.

### The mechanism

`gradient.glsl:127` is an ordinary whole-vector assignment:

```glsl
rotatedCentered = mat2(c, -s, s, c) * centered;
```

The JavaScript materializes it as sequential in-place component writes, into
an array that **is** `centered` (`var rotatedCentered = centered;`):

```js
(rotatedCentered[0] = c * centered[0] + s * centered[1],
 rotatedCentered[1] = -s * centered[0] + c * centered[1], rotatedCentered);
```

Lane 0's write **clobbers `centered[0]` before lane 1 reads it**, so lane 1
actually computes `-s * (c*centered[0] + s*centered[1]) + c*centered[1]`.

The emitter renders the assignment as `glsl::Mat2(...) * centered` — one
expression evaluated into a temporary and then assigned — which is the
*unclobbered* result GLSL specifies.

### The proof

A mutant that reads the source lanes into temporaries first (making the JS
compute the unclobbered result — exactly what the port emits) was rendered
alongside the canonical factory and compared with the shipped kernel at
6x5, `gradientType=1`, `rotation=0.4`, `repeat=2`:

| comparison | lanes differing (of 120) |
| --- | ---: |
| canonical authority vs the port | **89** |
| **unaliased mutant vs the port** | **0** |
| canonical authority vs unaliased mutant | 89 |

The port reproduces the mutant exactly and the authority not at all. That is
the mechanism, not an inference from it.

It also explains the shape of the divergence: it needs **both**
`rotation != 0` (or `s == 0` and the clobber is inert) and `repeat != 0`
(or `t * repeat` collapses and hides it), and it is independent of seed,
time, speed and gradientType. The perturbation is `-s * s * centered[1]`,
which is small for small angles — it looked near-ULP, but it is not a
rounding artifact at all.

### Blast radius, measured — and narrower than it first looks

Scanning every shipped canonical factory for an in-place component-write
tuple where a later lane's expression reads an already-written lane finds
**four sites**:

| program | typed? | verdict |
| --- | --- | --- |
| `synth/gradient:gradient` | yes | **DIVERGENT** (above) |
| `mixer/shapeMask:shapeMask` | yes | **not divergent** — verified 0/168 lanes across all 8 `shape` values |
| `synth/mandelbrot:mandelbrot` | **no — unported** | same shape as gradient; **will land wrong** |
| `classicNoisedeck/noise3d:noise3d` | no | not in the pinned corpus |

`shapeMask` is the instructive one. Its GLSL writes the two components as
**separate statements** (`p.x = …; p.y = …;`), which the emitter already
lowers to two sequential `set_swizzle` calls — matching the materialization
exactly. Gradient's GLSL is a **single whole-vector assignment**, which the
emitter lowers to one temporary. So the defect is not "in-place tuples" in
general; it is precisely:

> a **whole-vector assignment** whose right-hand side reads a lane of its own
> destination (or of an alias of it) that an earlier component write has
> already overwritten.

### `synth/mandelbrot` must be fixed BEFORE it lands

`mandelbrot.glsl:247-250` is the same construct:

```glsl
dz = vec2(2.0 * (zx * dz.x - zy * dz.y) + 1.0,
          2.0 * (zx * dz.y + zy * dz.x));
```

Lane 1 reads `dz.x`. `synth/mandelbrot` is on the wave-2 landing list. Landing
it against the current emitter reproduces parallax's history exactly: a row
that passes every structural gate and renders the wrong pixels.

### The fix, and why it is not in this change

The emitter must lower a whole-vector assignment to **sequential component
writes in source order** whenever the destination is read cross-lane by the
right-hand side. That is a second emitter change of the same weight as item
6's — and item 6's cost 42 re-derived frozen historical pins across four
verification waves. Doing both in one session would put two independent
emitter corrections behind a single re-derivation, which is exactly the state
in which a real regression hides. **Recorded, not fixed.**

---

## Not a defect, but do not fuzz it

Mutating `filter/median`'s inner Hoare-partition boundary
(`scanLeft <= scanRight` -> `<`) produces a **genuine infinite loop** — verified
live, ran past a 120-second watchdog and had to be killed. The shipped code is
correct; the neighbouring mutation is not survivable. Both median mutations in
the oracle therefore cap the *outer* convergence loop with a provably
terminating counter instead.
