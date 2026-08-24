# parallax190 — the pooled-array alias divergence, and how to reproduce it

Companion to `DEFECTS-FOUND.md` item 6. That entry states the defect; this
one is the recipe, so the next agent can put the failure on screen in a few
minutes instead of re-deriving it.

Found 2026-08-19 during the review of commit `04ea735` (rows 186-190). Row
190 had landed at "focused level" — structural admission proven at both
authorities, but no oracle package and no native parity test. The structural
work is sound. The pixels are not.

## What is wrong, in one paragraph

`parallax.glsl`'s ray-march refines between the two straddling samples with
`vec2 prevUV = rayUV; ... rayUV = mix(rayUV, prevUV, w);`. In the shipped
JavaScript, `var prevUV = rayUV` binds a **reference** to the same
`PooledFloat32Array` and the loop updates `rayUV` **in place**, so `prevUV`
follows it, `mix(x, x, w) == x`, and the refinement does nothing. The emitter
writes `glsl::Vec2 prevUV = rayUV;` — a value copy — and performs the
interpolation. The port is running code the authority does not.

## Reproduce

Three ingredients. None of them may live in this repository — build them
under a run root.

**1. An immutable snapshot of the JS authority.** `rsync -a` the sibling
`noisemaker-for-cpu` checkout (including `.git`) somewhere outside both
repositories. Verify the six pinned authority files still hash as
`varying-parity/wobble_oracle_generator.mjs` pins them; they did at
`4834b014`.

**2. A JS driver.** Bind through `createCanonicalBindings` /
`bindCanonicalKernel` / `runPass`, exactly as the wobble and cellRefract
oracle generators do. Destination 4x5, input and height maps 11x9,
`direction = (-0.8, 0.4, 0.2)`, `pivot = 0`, full route.

> **The trap that will cost you an hour.** `createCanonicalBindings` spreads
> `...uniforms` **first** and then sets `resolution`, `fullResolution`,
> `tileOffset`, `aspectRatio`, `aspect`, `time`, `globalTime`, `deltaTime`
> and `frame` itself. Passing any of those inside `uniforms` silently loses
> them. `tileOffset` and `fullResolution` go at the **options** level. Getting
> this wrong makes the JS render a full route against the port's tile route
> and manufactures a large, entirely fake divergence — it did here first.

**3. A C++ driver.** Bind the same values through
`noisemaker::generated::bind_filter_parallax_parallax` and
`noisemaker::run_pass`. Build against a Release tree with the project's
standard flags; `-ffp-contract=off` is not optional.

Compare the float32 words. Two of twenty pixels differ outright.

## The decisive trace

A whole-pixel colour diff does not tell you *where* the two sides part. This
does, and it is worth redoing after any candidate fix:

- In the snapshot, wrap the runtime's `textureLod` so it records
  `(surface.width, surface.height, coord[0], coord[1])`, and push a `PIXEL`
  sentinel from `beginPixel` so the stream segments per pixel.
- On the C++ side, extract the emitted `typed_80` namespace **verbatim** into
  a scratch translation unit, add the same recording to its `sample_texture`,
  and confirm the copy reproduces the shipped kernel's output byte-for-byte
  before trusting anything it says. It did here.

The result that pins the mechanism:

| | textureLod calls | pixels where the final `getInput` coord equals the last `getHeight` coord |
| --- | ---: | ---: |
| JavaScript | 309 | **20 / 20** |
| `typed_80` | 309 | **0 / 20** |

Identical call counts mean the march itself — every `t`, every `f`, every
break decision — agrees exactly. All 309 march coordinates are bit-identical.
Only the post-refinement coordinate differs. The refinement is measurably a
no-op in the authority; the aliasing is the explanation for a fact that stands
on its own.

## Why no existing gate caught it

- No oracle package and no `typed_parallax190_*` native test exist, so no
  pixel of this program has ever been compared with the authority.
- The four generator gates, the assembly gate and the sanitizer lanes are all
  green and always would be: nothing here is unsafe, unadmitted, or
  structurally wrong. The emitted code is a faithful rendering of the GLSL.
  That is precisely the problem.
- The divergence is **parameter-dependent**. At an unrelated binding set used
  for a nine-program differential sweep, parallax came out bit-identical. A
  thin oracle case list would have shipped a green record over this defect.
  Whatever case list the eventual package carries must include a case whose
  march straddles and refines.

## Scope for the fix

`DEFECTS-FOUND.md` item 6 carries the measured blast radius: nine typed rows
contain the alias-then-mutate shape, of which only parallax is confirmed
divergent and none of the other eight is cleared. Read that section before
scoping an emitter change — a fix that models the alias will need the
admission re-derived for every one of them.

Also open, and deliberately **not** attributed to this mechanism: an
unexplained near-ULP differential on `synth/gradient:gradient`, which has no
oracle coverage at all.
